from __future__ import annotations

import json
import os
import unicodedata
from collections.abc import Iterator
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ovcaq.config import RuntimeSettings
from ovcaq.events.model import Observation, ObservationType, Usage, observation_record
from ovcaq.events.tail import JsonlFollower, TailBatch
from ovcaq.paths import ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime import _run_observation
from ovcaq.runtime.registry import (
    FleetEntry,
    FleetRegistry,
    FleetRun,
    ProcessIdentity,
    process_identity,
)
from ovcaq.runtime.session import (
    EmergencyFailureObservation,
    MetricsSnapshot,
    RunObservation,
    SessionEvidenceStatus,
    SessionMetric,
)
from ovcaq.state.schema import SchemaError, State, new_state
from ovcaq.state.store import StateIOError, StateStore
from ovcaq.tui import model

from .model_support import FixedClock, Projection

STAMP = "2026-10-03T10:00:00Z"


def _event(kind: str, lane: str | None = None, **payload: object) -> Observation:
    return Observation(
        protocol_version=1,
        timestamp=datetime(2026, 10, 3, 10, tzinfo=UTC),
        provider="observed-provider",
        run_id="run-1",
        session_id="session-1",
        lane_id=lane,
        type=ObservationType(kind),
        payload=payload,
    )


def _batch(*events: Observation, **changes: bool) -> TailBatch[Observation]:
    return TailBatch(
        records=events,
        gaps=(),
        reset=changes.get("reset", False),
        backlog=changes.get("backlog", False),
        complete_history=changes.get("complete_history", True),
    )


def _metric(session: str = "session-1", **changes: object) -> SessionMetric:
    return replace(
        SessionMetric(
            schema_version=1,
            kind="phase",
            run_id="run-1",
            session_id=session,
            batch_id="batch-1",
            prd="00008-tui.md",
            phase_launched="build",
            capability=None,
            phase_end="review",
            decision="continue",
            started_at=STAMP,
            finished_at="2026-10-03T10:01:00Z",
            wall_seconds=60.0,
            model="observed-model",
            usage=None,
        ),
        **changes,
    )


@pytest.fixture
def projection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Projection]:
    paths = ensure_runtime_layout(
        resolve_runtime_paths(tmp_path, xdg_state_home=tmp_path / "xdg")
    )
    settings = RuntimeSettings(paths, 0.1, 1024**2, 1024**3, 0)
    identity = process_identity(os.getpid())
    assert identity is not None
    entry = FleetEntry(
        1, tmp_path, identity.pid, identity.started, "run-1", "launcher", STAMP
    )
    registry = FleetRegistry(paths.fleet_root)
    registry.publish(entry)
    run = FleetRun("run-1", tmp_path, "launcher", STAMP, identity.pid, identity.started)
    state = new_state(repo_root=tmp_path)
    state["batch"].update(id="batch-1", status="running", started_at=STAMP)
    harness = Projection(run, settings, state, registry, entry)
    monkeypatch.setattr(model, "datetime", FixedClock)
    monkeypatch.setattr(StateStore, "read", lambda self: deepcopy(harness.state))
    monkeypatch.setattr(_run_observation, "observe_run", harness.owned_observation)
    monkeypatch.setattr(model, "observe_metrics", lambda *a, **kw: harness.metrics)
    monkeypatch.setattr(model, "observe_session_evidence", lambda *a: harness.evidence)
    monkeypatch.setattr(
        model, "observe_emergency_failure", lambda paths: harness.emergency
    )
    monkeypatch.setattr(
        JsonlFollower,
        "read",
        lambda self: harness.batches.popleft() if harness.batches else _batch(),
    )
    harness.observer = model.ProjectObserver(run, settings)
    try:
        yield harness
    finally:
        harness.observer.close()


def _recovery(kind: str) -> dict[str, object]:
    return {
        "id": "operation-1",
        "kind": kind,
        "step": "intent",
        "prd": "00008-tui.md",
        "site": "review",
        "detail": "needs recovery",
        "source": "source.md",
        "destination": "parked.md",
        "artifact": None,
        "created_at": STAMP,
    }


@pytest.mark.parametrize(
    "case,expected",
    [
        ("emergency", "state-write-failed"),
        ("inconsistent", "inconsistent"),
        ("park", "parking"),
        ("stall", "parking"),
        ("pause", "pause-requested"),
        ("attention", "attention"),
        ("paused", "paused"),
        ("completed", "completed"),
        ("running", "running"),
        ("idle", "unknown"),
    ],
)
def test_status_respects_durable_precedence_over_active_run(
    projection: Projection, case: str, expected: str
) -> None:
    state = projection.state
    state["batch"]["status"] = "completed"
    if case in {
        "emergency",
        "inconsistent",
        "park",
        "stall",
        "pause",
        "attention",
        "paused",
    }:
        state["work"]["phase"] = "paused"
    if case in {"emergency", "inconsistent", "park", "stall", "pause", "attention"}:
        state["control"]["attention"] = {
            "site": "review",
            "detail": "blocked",
            "created_at": STAMP,
        }
    if case in {"emergency", "inconsistent", "park", "stall", "pause"}:
        state["control"]["pause_requested"] = True
    if case in {"emergency", "inconsistent", "park", "stall"}:
        state["recovery"]["operation"] = _recovery(
            "stall" if case == "stall" else "park"
        )
    if case in {"emergency", "inconsistent"}:
        projection.observation = RunObservation(
            "inconsistent", "lock/identity mismatch"
        )
    if case == "emergency":
        projection.emergency = EmergencyFailureObservation(True, "write failed", False)
    if case in {"running", "idle"}:
        state["batch"]["status"] = "running" if case == "running" else "idle"
    if case == "idle":
        projection.observation = RunObservation("idle")
    before = deepcopy(state)

    view = projection.poll()

    assert view.status == expected
    assert projection.state == before
    assert view.run == projection.run


@pytest.mark.parametrize(
    "created_at,malformed,expected",
    [
        ("2026-10-03T09:59:59.999999Z", False, "running"),
        (STAMP, False, "state-write-failed"),
        ("2026-10-03T10:00:00.000001Z", False, "state-write-failed"),
        (None, True, "state-write-failed"),
    ],
)
def test_emergency_failure_only_applies_to_selected_run(
    projection: Projection,
    created_at: str | None,
    malformed: bool,
    expected: str,
) -> None:
    projection.emergency = EmergencyFailureObservation(
        True, "write failed", malformed, created_at
    )

    assert projection.poll().status == expected


def test_state_projects_counts_phase_review_and_notice_without_mutating_input(
    projection: Projection,
) -> None:
    projection.state["revision"] = 17
    projection.state["work"].update(
        phase="review",
        next_phase="build",
        prd="00008-tui.md",
        tasks_total=8,
        tasks_completed=5,
    )
    projection.state["review"]["cycle"] = 3
    notice = {"site": "review", "detail": "needs a decision", "created_at": STAMP}
    projection.state["control"]["attention"] = notice
    before = deepcopy(projection.state)

    view = projection.poll()

    assert (view.phase, view.next_phase, view.prd, view.revision) == (
        "review",
        "build",
        "00008-tui.md",
        17,
    )
    assert (view.tasks_completed, view.tasks_total, view.review_cycle) == (5, 8, 3)
    assert view.attention == notice
    assert projection.state == before
    projection.state["control"]["attention"]["detail"] = "later mutation"
    assert view.attention["detail"] == "needs a decision"


def test_active_operator_stop_takes_precedence_over_recovery_and_pause(
    projection: Projection,
) -> None:
    projection.state["control"].update(
        pause_requested=True,
        pause_reason={
            "site": "operator_stop",
            "detail": "signal 15",
            "created_at": STAMP,
        },
    )
    projection.state["recovery"]["operation"] = _recovery("park")
    projection.metrics = MetricsSnapshot((_metric(decision="halt"),), True, ())

    view = projection.poll()

    assert view.status == "stopping"


def test_idle_halt_metric_remains_visible_after_agent_exit(
    projection: Projection,
) -> None:
    projection.observation = RunObservation("idle")
    projection.metrics = MetricsSnapshot((_metric(decision="halt"),), True, ())

    view = projection.poll()

    assert view.status == "halted"


def test_lane_labels_and_details_follow_the_normalized_contract(
    projection: Projection,
) -> None:
    projection.batches.append(
        _batch(
            _event(
                "lane.started",
                "worker",
                label="Reviewer [red]literal[/red]",
                detail="checking contracts",
            )
        )
    )

    view = projection.poll()

    assert view.lanes == (
        model.ActivityLane(
            "worker", "Reviewer [red]literal[/red]", "running", "checking contracts"
        ),
    )


@pytest.mark.parametrize("payload", [{"label": 3}, {"detail": ["malformed"]}])
def test_malformed_lane_display_values_become_visible_gaps(
    projection: Projection, payload: dict[str, object]
) -> None:
    projection.batches.append(_batch(_event("lane.started", "worker", **payload)))

    view = projection.poll()

    assert view.gaps
    assert view.telemetry == "partial"


@pytest.mark.parametrize(
    "required,expected", [(True, "attention"), (False, "completed")]
)
def test_failed_capability_remains_visible_after_drain_with_exact_retry_argv(
    projection: Projection, required: bool, expected: str
) -> None:
    projection.state["batch"]["status"] = "completed"
    projection.state["batch"]["capabilities"]["post-drain"] = {
        "required": required,
        "launcher": "launcher",
        "plugin": "external-plugin",
        "version": "1",
        "failure": "attention",
        "status": "failed",
        "attempts": [
            {
                "id": "attempt-1",
                "status": "failed",
                "started_at": STAMP,
                "finished_at": STAMP,
                "session_id": None,
                "detail": "plugin failed",
            }
        ],
    }

    view = projection.poll()

    assert view.status == expected
    assert view.capabilities == (
        model.CapabilityView(
            "post-drain",
            "failed",
            required,
            "plugin failed",
            (
                "ovcaq",
                "--root",
                str(projection.run.root),
                "capability",
                "retry",
                "post-drain",
            ),
        ),
    )


@pytest.mark.parametrize(
    "field,value", [("process_start", "replacement"), ("pid", 987654321)]
)
def test_selected_identity_is_revalidated_before_reading_replacement_state(
    projection: Projection, monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    projection.state["revision"] = 17
    projection.state["work"].update(tasks_completed=5, tasks_total=8)
    first = projection.poll()
    projection.state["revision"] = 18
    projection.state["work"].update(tasks_completed=6, tasks_total=9)
    refreshed = projection.poll()

    assert first.status == refreshed.status == "running"
    assert (first.revision, first.tasks_completed, first.tasks_total) == (17, 5, 8)
    assert (refreshed.revision, refreshed.tasks_completed, refreshed.tasks_total) == (
        18,
        6,
        9,
    )
    replacement = replace(projection.entry, **{field: value})
    projection.registry.publish(replacement)
    projection.observation = replace(
        projection.observation,
        process=ProcessIdentity(replacement.pid, replacement.process_start),
    )

    def forbidden_read(self: StateStore) -> State:
        raise AssertionError("read state after selected run identity disappeared")

    monkeypatch.setattr(StateStore, "read", forbidden_read)
    view = projection.poll()

    assert view.run == projection.run
    assert view.status in {"unknown", "inconsistent"}
    assert view.gaps
    assert view.status != "running"


@pytest.mark.parametrize(
    "failure",
    [StateIOError("cannot read state"), SchemaError("bad schema"), OSError("denied")],
)
def test_observational_read_failure_becomes_gap_and_unknown_numeric_values(
    projection: Projection, monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    def unreadable(self: StateStore) -> State:
        raise failure

    monkeypatch.setattr(StateStore, "read", unreadable)
    view = projection.poll()

    assert view.phase is None
    assert view.tasks_completed is None and view.tasks_total is None
    assert view.revision is None and view.review_cycle is None
    assert view.gaps
    assert view.telemetry in {"partial", "unavailable"}


def test_metrics_supply_known_usage_independently_of_elapsed_duration(
    projection: Projection,
) -> None:
    usage = Usage(101, 19, 13, 7, 3, 0.125, True)
    later_usage = Usage(29, 5, 2, 11, 4, 0.25, False)
    projection.metrics = MetricsSnapshot(
        (
            _metric(usage=asdict(usage)),
            _metric("session-2", wall_seconds=90.0, usage=asdict(later_usage)),
        ),
        True,
        (),
    )

    view = projection.poll()

    assert view.duration_seconds == 300.0
    assert view.usage == model.UsageView(130, 24, 15, 18, 7, 0.375, True, False)
    assert view.provider == "unknown"
    assert view.run.agent == "launcher"


def test_partial_metrics_preserve_unknown_usage_and_diagnostic_gaps(
    projection: Projection,
) -> None:
    usage = Usage(input_tokens=100, estimated=True)
    projection.metrics = MetricsSnapshot(
        (_metric(usage=asdict(usage)),), False, ("metrics incomplete",)
    )

    view = projection.poll()

    assert view.usage == model.UsageView(100, None, None, None, None, None, True, True)
    assert "metrics incomplete" in view.gaps
    assert view.telemetry == "partial"


def test_absent_usage_remains_unknown_with_known_elapsed(
    projection: Projection,
) -> None:
    view = projection.poll()

    assert view.duration_seconds == 300.0
    assert view.usage is None
    assert view.provider == "unknown"
    assert view.telemetry in {"partial", "unavailable"}

    usage = Usage(101, 19, 13, 7, 3, 0.125, False)
    projection.metrics = MetricsSnapshot((_metric(usage=asdict(usage)),), True, ())
    projection.batches.append(_batch(_event("lane.started", "worker")))

    complete = projection.poll()

    assert complete.telemetry == "complete"
    assert complete.gaps == ()
    assert complete.duration_seconds == 300.0
    assert complete.usage == model.UsageView(101, 19, 13, 7, 3, 0.125, False, False)
    assert complete.provider == "observed-provider"


@pytest.mark.parametrize(
    "source,expected_provider",
    [("raw-event", "observed-provider"), ("raw-file", "unknown")],
)
@pytest.mark.parametrize("session_id", ["session-1", "session-alternate"])
def test_raw_only_telemetry_survives_missing_normalization(
    projection: Projection,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    expected_provider: str,
    session_id: str,
) -> None:
    projection.observation = RunObservation("active", active_session_id=session_id)
    evidence_requests: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def evidence(*args: object, **kwargs: object) -> SessionEvidenceStatus:
        evidence_requests.append((args, kwargs))
        return projection.evidence

    monkeypatch.setattr(model, "observe_session_evidence", evidence)
    if source == "raw-event":
        projection.batches.append(
            _batch(
                replace(
                    _event(
                        "raw.unknown",
                        reason="unrecognized",
                        raw_sha256="a" * 64,
                        preview="data",
                    ),
                    session_id=session_id,
                )
            )
        )
    else:
        projection.evidence = SessionEvidenceStatus(
            raw=True, normalized=False, summary=False, raw_only=True
        )

    view = projection.poll()

    assert view.telemetry == "raw-only"
    assert view.usage is None
    assert view.provider == expected_provider
    assert view.lanes == ()
    assert len(evidence_requests) == 1
    args, kwargs = evidence_requests[0]
    assert session_id in (*args, *kwargs.values())


@pytest.mark.parametrize(
    "terminal,status", [("lane.completed", "completed"), ("lane.failed", "failed")]
)
def test_lane_start_progress_and_terminal_records_keep_observed_provider(
    projection: Projection, terminal: str, status: str
) -> None:
    projection.batches.extend(
        [
            _batch(_event("lane.started", "worker-1")),
            _batch(_event("lane.progress", "worker-1")),
            _batch(_event(terminal, "worker-1")),
        ]
    )

    started, progress, completed = (projection.poll() for _ in range(3))

    assert started.lanes[0].lane_id == "worker-1"
    assert started.lanes[0].status == progress.lanes[0].status == "running"
    assert completed.lanes[0].status == status
    assert len(completed.lanes) == 1
    assert completed.provider == "observed-provider"
    assert completed.run.agent == "launcher"


@pytest.mark.parametrize("kind", ["lane.progress", "lane.completed", "lane.failed"])
def test_lane_without_start_reports_unknown_and_partial_history(
    projection: Projection, kind: str
) -> None:
    projection.batches.append(_batch(_event(kind, "orphan"), complete_history=False))

    view = projection.poll()

    assert [(lane.lane_id, lane.status) for lane in view.lanes] == [
        ("orphan", "unknown")
    ]
    assert any("history" in gap.lower() for gap in view.gaps)
    assert view.telemetry == "partial"


def test_lane_retention_evicts_oldest_terminal_before_active_lanes(
    projection: Projection,
) -> None:
    events = [_event("lane.started", "active-oldest")]
    for number in range(257):
        events.extend(
            [
                _event("lane.started", f"done-{number}"),
                _event("lane.completed", f"done-{number}"),
            ]
        )
    projection.batches.append(_batch(*events))

    view = projection.poll()

    assert len(view.lanes) == 256
    ids = {lane.lane_id for lane in view.lanes}
    assert "active-oldest" in ids and "done-256" in ids
    assert "done-0" not in ids and "done-1" not in ids


def test_gap_retention_deduplicates_and_collapses_overflow(
    projection: Projection,
) -> None:
    projection.metrics = MetricsSnapshot(
        (), False, tuple(f"gap-{i}" for i in range(150))
    )
    first = projection.poll()
    second = projection.poll()

    assert len(first.gaps) <= 128
    assert len(set(first.gaps)) == len(first.gaps)
    assert "additional telemetry gaps omitted" in first.gaps
    concrete = set(first.gaps) - {"additional telemetry gaps omitted"}
    assert concrete & set(projection.metrics.gaps)
    assert second.gaps == first.gaps


def test_follower_reset_clears_lanes_and_latest_session_usage(
    projection: Projection,
) -> None:
    projection.batches.extend(
        [
            _batch(
                _event("lane.started", "before"),
                _event(
                    "usage.updated",
                    usage=asdict(Usage(input_tokens=10)),
                    identity="request-1",
                ),
            ),
            _batch(_event("lane.started", "after"), reset=True),
        ]
    )

    before = projection.poll()
    after = projection.poll()

    assert before.usage is not None and before.usage.input_tokens == 10
    assert [lane.lane_id for lane in before.lanes] == ["before"]
    assert [lane.lane_id for lane in after.lanes] == ["after"]
    assert after.usage is None


def test_backlog_stays_visible_until_later_polls_drain_it(
    projection: Projection,
) -> None:
    projection.batches.extend(
        [
            _batch(_event("lane.started", "first"), backlog=True),
            _batch(_event("lane.started", "second")),
        ]
    )

    first = projection.poll()
    second = projection.poll()

    assert [lane.lane_id for lane in first.lanes] == ["first"]
    assert first.telemetry == "partial"
    assert any("backlog" in gap.lower() for gap in first.gaps)
    assert {lane.lane_id for lane in second.lanes} == {"first", "second"}


def test_real_follower_tolerates_malformed_record_and_observes_valid_neighbor(
    projection: Projection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.undo()
    monkeypatch.setattr(_run_observation, "observe_run", projection.owned_observation)
    paths = projection.settings.paths
    StateStore(paths.state_file).initialize(projection.state)
    record = observation_record(_event("lane.started", "survivor"))
    events = paths.sessions / "session-1" / "normalized.jsonl"
    events.parent.mkdir(parents=True)
    events.write_text("{broken json\n" + json.dumps(record) + "\n")

    view = projection.poll()

    assert any(lane.lane_id == "survivor" for lane in view.lanes)
    assert view.gaps
    assert view.telemetry == "partial"
    assert events.read_text().startswith("{broken json\n")


@pytest.mark.parametrize(
    "value,limit", [("", 512), ("safe text", 512), ("x" * 1000, 512), ("abc", 2)]
)
def test_display_text_preserves_plain_content_within_explicit_limit(
    value: str, limit: int
) -> None:
    result = model.display_text(value, limit=limit)

    assert len(result) <= limit
    if len(value) <= limit:
        assert result == value


def test_display_text_removes_terminal_and_unicode_format_controls() -> None:
    hostile = "left\x1b]52;c;payload\x07\r\n\t\x00\x85\u202e\u2066\u200bright[red]literal[/red]"

    result = model.display_text(hostile)

    assert all(
        unicodedata.category(character) not in {"Cc", "Cf"} for character in result
    )
    assert "left" in result and "right" in result
    assert "[red]literal[/red]" in result


@pytest.mark.parametrize(
    "record,attribute,value",
    [
        (model.ActivityLane("lane", "label", "running", None), "status", "failed"),
        (
            model.UsageView(None, None, None, None, None, None, False, True),
            "input_tokens",
            1,
        ),
        (model.CapabilityView("cap", "failed", True, None, None), "required", False),
        (
            EmergencyFailureObservation(False, None, False, STAMP),
            "created_at",
            None,
        ),
    ],
)
def test_projection_records_are_immutable_and_slotted(
    record: object, attribute: str, value: object
) -> None:
    assert not hasattr(record, "__dict__")
    with pytest.raises(FrozenInstanceError):
        setattr(record, attribute, value)


def test_project_view_is_immutable_and_slotted(projection: Projection) -> None:
    view = projection.poll()

    assert not hasattr(view, "__dict__")
    with pytest.raises(FrozenInstanceError):
        view.status = "completed"


@pytest.mark.parametrize(
    "boundary",
    [
        "observe_selected_run",
        "observe_metrics",
        "observe_session_evidence",
        "observe_emergency_failure",
    ],
)
def test_shared_observation_failures_are_reported_as_gaps(
    projection: Projection, monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("unreadable evidence")

    monkeypatch.setattr(model, boundary, fail)

    view = projection.poll()

    assert view.gaps
    assert view.telemetry in {"partial", "unavailable"}


def test_observer_sanitizes_and_bounds_dynamic_values_before_returning_view(
    projection: Projection,
) -> None:
    hostile = "[red]literal[/red]\x1b]52;c;data\x07\r\u202e" + "x" * 1000
    projection.state["work"]["prd"] = hostile
    projection.state["control"]["attention"] = {
        "site": hostile,
        "detail": hostile,
        "created_at": STAMP,
    }
    projection.metrics = MetricsSnapshot((), False, (hostile,))
    projection.batches.append(
        _batch(_event("lane.started", "worker", label=hostile, detail=hostile))
    )

    view = projection.poll()

    assert view.attention is not None and view.prd is not None
    values = (
        view.prd,
        view.attention["site"],
        view.attention["detail"],
        view.lanes[0].label,
        view.lanes[0].detail,
        *view.gaps,
    )
    for value in values:
        assert value is not None and len(value) <= 512
        assert all(
            unicodedata.category(character) not in {"Cc", "Cf"} for character in value
        )
    assert "[red]literal[/red]" in view.lanes[0].label
