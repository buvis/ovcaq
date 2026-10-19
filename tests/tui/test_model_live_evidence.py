from __future__ import annotations

import os
import shlex
from collections.abc import Iterator
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from ovcaq.config import RuntimeSettings
from ovcaq.events.model import Observation, ObservationType, Usage
from ovcaq.events.tail import JsonlFollower, NormalizedEventWriter
from ovcaq.paths import RuntimePaths, ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.registry import (
    FleetEntry,
    FleetRegistry,
    FleetRun,
    RunLock,
    process_identity,
)
from ovcaq.runtime.session import (
    SessionMetadata,
    SessionMetric,
    SessionPaths,
    create_session,
    publish_run_metadata,
    publish_session_metric,
    reconcile_metrics,
)
from ovcaq.state.schema import State, new_state
from ovcaq.state.store import StateStore
from ovcaq.tui.model import ActivityLane, CapabilityView, ProjectObserver
from ovcaq.tui.panels import capability_panel

STAMP = "2026-10-03T10:00:00Z"


@dataclass
class Evidence:
    paths: RuntimePaths
    session: SessionPaths
    store: StateStore
    observer: ProjectObserver
    writer: NormalizedEventWriter
    metric: SessionMetric

    def event(self, *, lane: str = "worker", **changes: object) -> Observation:
        return replace(
            Observation(
                1,
                datetime(2026, 10, 3, 10, tzinfo=UTC),
                "observed-provider",
                "run-1",
                "session-1",
                lane,
                ObservationType.LANE_STARTED,
                {"label": lane},
            ),
            **changes,
        )

    def write(self, *events: Observation) -> None:
        for event in events:
            self.writer.write(event)
        self.writer.flush()


def pending_metric() -> SessionMetric:
    return SessionMetric(
        schema_version=1,
        kind="phase",
        run_id="run-1",
        session_id="session-1",
        batch_id="batch-1",
        prd=None,
        phase_launched="build",
        capability=None,
        phase_end=None,
        decision=None,
        started_at=STAMP,
        finished_at=None,
        wall_seconds=None,
        model="local-model",
        usage=None,
    )


@pytest.fixture
def evidence(tmp_path: Path) -> Iterator[Evidence]:
    paths = ensure_runtime_layout(
        resolve_runtime_paths(
            tmp_path,
            runtime_root=tmp_path / "configured-runtime",
            xdg_state_home=tmp_path / "xdg",
        )
    )
    identity = process_identity(os.getpid())
    assert identity is not None
    metadata = SessionMetadata(
        1, "run-1", "session-1", "local", identity.pid, identity.started, STAMP
    )
    entry = FleetEntry(
        1, tmp_path, identity.pid, identity.started, "run-1", "local", STAMP
    )
    registry = FleetRegistry(paths.fleet_root)
    registry.publish(entry)
    lock = RunLock.acquire(paths.run_lock)
    session = create_session(paths, metadata)
    publish_run_metadata(paths, metadata)
    metric = pending_metric()
    publish_session_metric(paths, session, metric)
    store = StateStore(paths.state_file)
    state = new_state(repo_root=tmp_path)
    state["batch"].update(id="batch-1", status="running", started_at=STAMP)
    state["work"].update(phase="build", next_phase="build")
    store.initialize(state)
    run = FleetRun("run-1", tmp_path, "local", STAMP, identity.pid, identity.started)
    observer = ProjectObserver(
        run, RuntimeSettings(paths, 0.1, 32 * 1024**2, 64 * 1024**2, 0)
    )
    writer = NormalizedEventWriter(
        session.normalized, max_bytes=32 * 1024**2, min_free_bytes=0
    )
    try:
        yield Evidence(paths, session, store, observer, writer, metric)
    finally:
        observer.close()
        writer.close()
        lock.close()
        registry.remove(entry.run_id, expected=entry)


@pytest.mark.parametrize(
    "foreign",
    [
        {"run_id": "other-run"},
        {"session_id": "other-session"},
        {"run_id": "other-run", "session_id": "other-session"},
    ],
    ids=["wrong-run", "wrong-session", "both-wrong"],
)
def test_observer_filters_live_events_by_exact_run_and_session_identity(
    evidence: Evidence,
    foreign: dict[str, str],
) -> None:
    evidence.write(evidence.event())
    before = evidence.observer.poll()
    evidence.write(
        evidence.event(lane="foreign", provider="foreign-provider", **foreign)
    )
    after = evidence.observer.poll()
    assert before.lanes == (ActivityLane("worker", "worker", "running", None),)
    assert after.lanes == before.lanes
    assert after.provider == before.provider == "observed-provider"
    assert after.run.run_id == "run-1"
    assert "foreign-provider" in evidence.session.normalized.read_text()


def damage_stream(evidence: Evidence, damage: str) -> None:
    if damage == "malformed":
        with evidence.session.normalized.open("ab") as stream:
            stream.write(b"{malformed json}\n")
    elif damage == "oversized":
        with evidence.session.normalized.open("ab") as stream:
            for _ in range(17):
                stream.write(b"x" * 1024**2)
            stream.write(b"\n")
    elif damage == "replaced":
        replacement = evidence.session.root / "replacement.jsonl"
        replacement.write_text("")
        replacement.replace(evidence.session.normalized)
    else:
        evidence.session.normalized.write_text("")


@pytest.mark.parametrize("damage", ["malformed", "oversized", "replaced", "truncated"])
def test_one_shot_stream_gaps_survive_later_refreshes(
    evidence: Evidence, damage: str
) -> None:
    evidence.write(evidence.event())
    evidence.observer.poll()
    damage_stream(evidence, damage)
    found = None
    for _ in range(32):
        view = evidence.observer.poll()
        matches = tuple(gap for gap in view.gaps if damage in gap.lower())
        if matches:
            found = matches
    assert found, f"{damage} was never diagnosed"
    refreshed = evidence.observer.poll()
    assert set(found) <= set(refreshed.gaps)
    assert len(refreshed.gaps) <= 128
    assert len(refreshed.gaps) == len(set(refreshed.gaps))
    assert refreshed.telemetry == "partial"


def test_bounded_backlog_has_one_diagnostic_without_claiming_truncation(
    evidence: Evidence,
) -> None:
    baseline = evidence.observer.poll()
    event = evidence.event(
        type=ObservationType.ACTIVITY_MESSAGE, lane_id=None, payload={"text": "working"}
    )
    evidence.write(*([event] * 1100))
    queued = evidence.observer.poll()
    new_gaps = set(queued.gaps) - set(baseline.gaps)
    assert len(new_gaps) == 1
    assert "backlog" in next(iter(new_gaps)).lower()
    assert not any("truncat" in gap.lower() for gap in queued.gaps)
    assert queued.telemetry == "partial"
    drained = evidence.observer.poll()
    assert not any("backlog" in gap.lower() for gap in drained.gaps)


def test_follower_backlog_does_not_report_a_truncation_gap(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_bytes(b'{"n":1}\n{"n":2}\n')
    follower = JsonlFollower(path, dict, max_records=1)
    try:
        queued = follower.read()
        drained = follower.read()
        assert queued.records == ({"n": 1},) and queued.backlog
        assert len(queued.gaps) <= 1
        assert not any(gap.kind == "truncated" for gap in queued.gaps)
        assert drained.records == ({"n": 2},) and not drained.backlog
        assert drained.complete_history and drained.gaps == ()
        path.write_bytes(b"")
        truncated = follower.read()
        assert {gap.kind for gap in truncated.gaps} == {"truncated"}
        assert truncated.reset and not truncated.backlog
    finally:
        follower.close()


def add_failed_capability(state: State, session_id: str | None, required: bool) -> None:
    state["batch"]["capabilities"]["post-check"] = {
        "required": required,
        "launcher": "local",
        "plugin": "audit",
        "version": "1",
        "failure": "attention",
        "status": "failed",
        "attempts": [
            {
                "id": "attempt-old",
                "status": "failed",
                "started_at": STAMP,
                "finished_at": STAMP,
                "session_id": "old-session",
                "detail": "old failure",
            },
            {
                "id": "attempt-last",
                "status": "failed",
                "started_at": STAMP,
                "finished_at": STAMP,
                "session_id": session_id,
                "detail": "last failure",
            },
        ],
    }


@pytest.mark.parametrize("session_id", ["last-attempt-session", None])
@pytest.mark.parametrize("required", [True, False])
def test_capability_exposes_last_attempt_evidence_under_configured_runtime_root(
    evidence: Evidence,
    session_id: str | None,
    required: bool,
) -> None:
    if session_id is not None:
        create_session(
            evidence.paths,
            SessionMetadata(
                1, "run-1", session_id, "local", os.getpid(), "retained-process", STAMP
            ),
        )
    evidence.store.transaction(
        lambda state: add_failed_capability(state, session_id, required)
    )
    view = evidence.observer.poll()
    (capability,) = view.capabilities
    expected = None if session_id is None else evidence.paths.sessions / session_id
    argv = (
        "ovcaq",
        "--root",
        str(evidence.paths.project_root),
        "capability",
        "retry",
        "post-check",
    )
    assert capability.session_id == session_id
    assert capability.evidence_path == expected
    assert capability.detail == "last failure"
    assert capability.retry_command == argv
    assert capability.name == "post-check"
    assert capability.status == "failed"
    assert capability.required is required
    stream = StringIO()
    Console(file=stream, width=1000, color_system=None, force_terminal=False).print(
        capability_panel(view)
    )
    rendered = stream.getvalue()
    assert shlex.join(argv) in rendered
    assert "failed" in rendered
    assert "post-check" in rendered.replace(shlex.join(argv), "")
    assert "old-session" not in rendered
    if expected is not None:
        assert isinstance(capability.evidence_path, Path)
        assert capability.evidence_path.is_dir()
        assert str(expected) in rendered


def test_capability_evidence_defaults_preserve_existing_constructor() -> None:
    capability = CapabilityView("audit", "pending", True, None, None)
    assert capability.session_id is None
    assert capability.evidence_path is None


@pytest.mark.parametrize(
    "cost,estimated",
    [
        (0, False),
        (2, False),
        (0.125, False),
        (0.25, True),
    ],
    ids=["zero", "integer", "float", "estimated"],
)
def test_published_integer_and_float_costs_remain_known(
    evidence: Evidence,
    cost: float,
    estimated: bool,
) -> None:
    usage = asdict(Usage(3, 2, 0, 0, 1, float(cost), estimated))
    usage["cost_usd"] = cost
    final = replace(
        evidence.metric,
        phase_end="review",
        decision="continue",
        finished_at="2026-10-03T10:01:00Z",
        wall_seconds=60.0,
        usage=usage,
    )
    publish_session_metric(evidence.paths, evidence.session, final)
    assert reconcile_metrics(evidence.paths) == (final,)
    view = evidence.observer.poll()
    assert view.usage is not None
    assert view.usage.input_tokens == 3
    assert view.usage.output_tokens == 2 and view.usage.tool_uses == 1
    assert view.usage.cache_creation_input_tokens == 0
    assert view.usage.cache_read_input_tokens == 0
    assert view.usage.cost_usd == cost
    assert view.usage.estimated is estimated
    assert view.usage.partial is False
