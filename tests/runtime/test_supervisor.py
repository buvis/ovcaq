from __future__ import annotations

import json
import os
import stat
import sys
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ovcaq.config import (
    PhaseSettings,
    RuntimeSettings,
    SupervisorSettings,
    workflow_settings,
)
from ovcaq.drivers.base import LaunchRequest, LaunchSpec
from ovcaq.events.model import (
    FailureClass,
    Observation,
    ObservationType,
    SessionSummary,
)
from ovcaq.paths import RuntimePaths, ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.capability import (
    CapabilityExecution,
    CapabilityRequest,
    CapabilityService,
)
from ovcaq.runtime.decision import DecisionKind, SupervisorDecision, SupervisorPolicy
from ovcaq.runtime.session import (
    EmergencyStateFailure,
    EvidenceLimitError,
    SessionMetadata,
    SessionMetric,
    create_session,
    publish_session_metric,
    reconcile_metrics,
    record_state_failure,
)
from ovcaq.runtime.supervisor import (
    CapabilityRunnerResolver,
    Supervisor,
    SupervisorOutcome,
)
from ovcaq.state.schema import State, new_state
from ovcaq.state.store import StateStore
from ovcaq.workflow.paths import resolve_lifecycle_paths


@dataclass
class TestClock:
    __test__ = False
    current: datetime = datetime(2026, 10, 2, 12, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current

    def monotonic(self) -> float:
        return time.monotonic()

    def wait(self, event: threading.Event, timeout: float) -> bool:
        return event.wait(timeout)


@dataclass
class Step:
    failure: FailureClass | None = None
    effect: Callable[[], None] | None = None
    code: str = "print('All work is complete; launch nothing else.')"
    decode_error: bool = False
    reset_seconds: float | None = None


def rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


@dataclass
class Driver:
    clock: TestClock
    steps: list[Step]
    name: str = "local"
    requests: list[LaunchRequest] = field(default_factory=list)
    reductions: list[tuple[list[Observation], int]] = field(default_factory=list)
    raw_present_before_decode: list[bool] = field(default_factory=list)
    on_line: Callable[[str], None] | None = None
    launch_error: Exception | None = None
    default_tiers: Mapping[str, str] = field(default_factory=dict)

    def default_prompt(self, phase: str) -> str:
        return f"default {phase}"

    def probe(self) -> object:
        raise AssertionError("a configured test driver needs no network probe")

    def build_launch(self, request: LaunchRequest) -> LaunchSpec:
        if self.launch_error is not None:
            raise self.launch_error
        assert len(self.requests) < len(self.steps), "unexpected extra workflow launch"
        self.requests.append(request)
        code = (
            "import json\nfrom pathlib import Path\n"
            f"pending = json.loads(Path({str(request.session_dir / 'metrics.jsonl')!r}).read_text())\n"
            "assert pending['finished_at'] is None and pending['decision'] is None\n"
            f"assert pending['phase_launched'] == {request.phase!r}\n"
            + self.steps[len(self.requests) - 1].code
        )
        return LaunchSpec(
            (sys.executable, "-c", code),
            {key: value for key, value in os.environ.items() if value},
            request.root,
            "jsonl",
        )

    def decode(self, raw_line: str) -> Iterable[Observation]:
        raw = self.requests[-1].session_dir / "raw.jsonl"
        self.raw_present_before_decode.append(raw_line.strip() in raw.read_text())
        if self.on_line is not None:
            self.on_line(raw_line)
        if self.steps[len(self.requests) - 1].decode_error:
            raise ValueError("synthetic decode failure")
        return ()

    def summarize(
        self, observations: Iterable[Observation], exit_code: int
    ) -> SessionSummary:
        self.reductions.append((list(observations), exit_code))
        step = self.steps[len(self.requests) - 1]
        self.clock.current += timedelta(seconds=2)
        if step.effect is not None:
            step.effect()
        reset = (
            None
            if step.reset_seconds is None
            else self.clock.now() + timedelta(seconds=step.reset_seconds)
        )
        return SessionSummary(
            success=step.failure is None,
            session_id=self.requests[-1].session_dir.name,
            failure_class=step.failure,
            failure_detail=None if step.failure is None else "normalized test failure",
            rate_limit_reset_at=reset,
            usage=None,
        )


@dataclass
class Runner:
    success: bool = True
    requests: list[CapabilityRequest] = field(default_factory=list)

    def run(self, request: CapabilityRequest) -> CapabilityExecution:
        self.requests.append(request)
        (pending,) = rows(request.session.metrics)
        assert pending["decision"] is None
        return CapabilityExecution(
            self.success,
            request.session.root.name,
            None if self.success else "synthetic capability failure",
        )


@dataclass
class Harness:
    root: Path
    paths: RuntimePaths
    store: StateStore
    clock: TestClock
    driver: Driver
    runner: Runner
    settings: SupervisorSettings
    waits: list[float] = field(default_factory=list)

    def supervisor(self) -> Supervisor:
        resolver: CapabilityRunnerResolver = lambda _: self.runner
        return Supervisor(
            self.root,
            store=self.store,
            driver=self.driver,
            settings=self.settings,
            capability_runner=resolver,
            clock=self.clock,
            sleeper=self.waits.append,
        )

    def change(self, **fields: object) -> None:
        self.store.transaction(lambda state: state["work"].update(fields))


def harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Harness:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
    root = tmp_path / "repo"
    root.mkdir()
    (root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner"]\n'
        'tiers = { standard = "model-s", deep = "model-o" }\n'
        "[phases.build]\ntimeout_seconds = 3\n"
        "[phases.review]\ntimeout_seconds = 3\n"
        "[phases.done]\ntimeout_seconds = 3\n"
    )
    paths = ensure_runtime_layout(
        resolve_runtime_paths(
            root,
            runtime_root=root / "runtime",
            xdg_state_home=tmp_path / "state-home",
        )
    )
    store = StateStore(paths.state_file)
    state = new_state(repo_root=root)
    state["batch"].update(id="batch-1", status="running")
    state["work"].update(phase="build", next_phase="build")
    store.initialize(state)
    clock = TestClock()
    settings = SupervisorSettings(
        RuntimeSettings(paths, 0.05, 1_000_000, 10_000_000, 0),
        SupervisorPolicy(1, 2, 2, 0.25, 5.0, 3),
        {
            phase: PhaseSettings(tier, "high", 3)
            for phase, tier in (
                ("build", "standard"),
                ("review", "deep"),
                ("done", "standard"),
            )
        },
    )
    return Harness(root, paths, store, clock, Driver(clock, []), Runner(), settings)


def drain(state: State, *, completed: bool = True) -> None:
    state["work"].update(phase="done", next_phase="")
    if completed:
        state["batch"]["completed_prds"].append(
            {
                "filename": "finished.md",
                "cycles": 1,
                "autonomous_decisions": 0,
                "escalated_decisions": 0,
                "tasks_completed": 1,
                "tasks_total": 1,
            }
        )


def add_capability(state: State) -> None:
    state["batch"]["capabilities"]["audit"] = {
        "required": True,
        "launcher": "local",
        "plugin": "audit",
        "version": "1",
        "failure": "attention",
        "status": "pending",
        "attempts": [],
    }


@pytest.mark.parametrize("pause", ["request", "phase", "next_phase"])
def test_boundary_pause_returns_zero_without_launching(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pause: str,
) -> None:
    h = harness(tmp_path, monkeypatch)
    if pause == "request":
        h.store.transaction(lambda state: state["control"].update(pause_requested=True))
    else:
        h.change(**{pause: "paused"})
    outcome = h.supervisor().run()
    assert isinstance(outcome, SupervisorOutcome)
    assert (outcome.exit_code, outcome.decision.kind, outcome.sessions_attempted) == (
        0,
        DecisionKind.PAUSE,
        0,
    )
    assert h.driver.requests == []


def test_productive_state_beats_nonzero_exit_and_routes_a_fresh_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.driver.steps = [
        Step(
            FailureClass.AGENT,
            lambda: h.change(next_phase="review"),
            "raise SystemExit(9)",
        ),
        Step(effect=lambda: h.change(next_phase="paused")),
    ]
    outcome = h.supervisor().run()
    assert outcome.exit_code == 0 and outcome.sessions_attempted == 2
    assert [request.phase for request in h.driver.requests] == ["build", "review"]
    assert [request.model for request in h.driver.requests] == ["model-s", "model-o"]
    assert [request.prompt for request in h.driver.requests] == [
        "default build",
        "default review",
    ]
    assert h.driver.reductions[0][1] == 9
    assert len({request.session_dir for request in h.driver.requests}) == 2
    metrics = reconcile_metrics(h.paths)
    assert len(metrics) == 2 and all(row.finished_at is not None for row in metrics)
    assert metrics[0].decision == "continue" and metrics[1].decision == "pause"


def test_untouched_successful_prose_reaches_repeat_limit_and_pauses_bootstrap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.driver.steps = [Step() for _ in range(3)]
    outcome = h.supervisor().run()
    assert (outcome.exit_code, outcome.decision.kind, outcome.sessions_attempted) == (
        0,
        DecisionKind.PAUSE,
        3,
    )
    state = h.store.read()
    assert state["recovery"]["phase_repeats"] == 3
    assert state["recovery"]["phase_fingerprint"]
    assert h.waits == []
    assert len({request.session_dir for request in h.driver.requests}) == 3


@pytest.mark.parametrize(
    "failure,attempts,waits",
    [
        (FailureClass.AGENT, 2, []),
        (FailureClass.CONNECTIVITY, 3, [0.25, 0.25]),
        (FailureClass.RATE_LIMIT, 3, [1.0, 1.0]),
    ],
)
def test_failures_obey_retry_caps_despite_supervisor_revision_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: FailureClass,
    attempts: int,
    waits: list[float],
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.driver.steps = [Step(failure, reset_seconds=1) for _ in range(attempts)]
    outcome = h.supervisor().run()
    assert outcome.exit_code == 1 and outcome.decision.kind == DecisionKind.HALT
    assert outcome.sessions_attempted == attempts
    assert h.waits == waits
    assert len({request.session_dir for request in h.driver.requests}) == attempts
    assert len(reconcile_metrics(h.paths)) == attempts


@pytest.mark.parametrize("reset", ["progress", "failure_class"])
def test_retry_budget_resets_after_progress_or_a_changed_failure_class(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reset: str,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.settings = replace(
        h.settings, policy=replace(h.settings.policy, phase_repeat_limit=6)
    )
    middle = (
        Step(FailureClass.AGENT, lambda: h.change(next_phase="review"))
        if reset == "progress"
        else Step(FailureClass.CONNECTIVITY)
    )
    h.driver.steps = [
        Step(FailureClass.AGENT),
        middle,
        Step(FailureClass.AGENT),
        Step(effect=lambda: h.change(next_phase="paused")),
    ]
    outcome = h.supervisor().run()
    assert outcome.exit_code == 0 and outcome.sessions_attempted == 4
    assert outcome.decision.kind == DecisionKind.PAUSE
    assert h.waits == ([] if reset == "progress" else [0.25])


def test_run_once_preserves_raw_unknown_decode_and_private_final_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.driver.steps = [Step(decode_error=True)]
    before = h.clock.now()
    result = h.supervisor().run_once()
    assert result.started_at == before and result.finished_at == before + timedelta(
        seconds=2
    )
    assert result.state_error is None and result.state_after is not None
    (request,) = h.driver.requests
    observations, exit_code = h.driver.reductions[0]
    assert exit_code == 0
    assert h.driver.raw_present_before_decode == [True]
    assert any(item.type == ObservationType.RAW_UNKNOWN for item in observations)
    assert "All work is complete" in (request.session_dir / "raw.jsonl").read_text()
    assert rows(request.session_dir / "normalized.jsonl")
    assert json.loads((request.session_dir / "summary.json").read_text())
    (metric,) = rows(request.session_dir / "metrics.jsonl")
    assert (
        metric["finished_at"] is not None
        and metric["session_id"] == request.session_dir.name
    )
    assert stat.S_IMODE(request.session_dir.stat().st_mode) == 0o700
    for artifact in request.session_dir.iterdir():
        assert stat.S_IMODE(artifact.stat().st_mode) == 0o600
    assert len(reconcile_metrics(h.paths)) == 1


@pytest.mark.parametrize("run_loop", [False, True])
def test_post_session_state_read_failure_is_observable_and_prevents_relaunch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    run_loop: bool,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.driver.steps = [Step(effect=lambda: h.paths.state_file.write_text("{broken"))]
    supervisor = h.supervisor()
    if run_loop:
        outcome = supervisor.run()
        assert outcome.exit_code == 1 and outcome.decision.kind == DecisionKind.HALT
        assert outcome.sessions_attempted == 1
    else:
        attempt = supervisor.run_once()
        assert attempt.state_after is None and attempt.state_error
    assert len(h.driver.requests) == 1
    (metric,) = rows(h.driver.requests[0].session_dir / "metrics.jsonl")
    assert metric["finished_at"] is not None


@pytest.mark.parametrize("site", ["launch", "evidence"])
def test_session_setup_failure_finalizes_metric_and_completion_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    site: str,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.driver.steps = [Step(code="print('evidence larger than one byte')")]
    expected: type[Exception]
    if site == "launch":
        h.driver.launch_error = OSError("synthetic launch failure")
        expected = OSError
    else:
        h.settings = replace(
            h.settings,
            runtime=replace(h.settings.runtime, max_session_bytes=1),
        )
        expected = EvidenceLimitError

    with pytest.raises(expected):
        h.supervisor().run_once()

    (metric,) = reconcile_metrics(h.paths)
    assert metric.decision == DecisionKind.HALT.value
    assert metric.finished_at is not None
    (session,) = h.paths.sessions.iterdir()
    summary = json.loads((session / "summary.json").read_text())
    assert summary["returncode"] == -1
    assert summary["detail"]


@pytest.mark.parametrize(
    "kind", [DecisionKind.CONTINUE, DecisionKind.RETRY, DecisionKind.WAIT]
)
def test_apply_continuations_return_true_and_wait_sleeps_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: DecisionKind,
) -> None:
    h = harness(tmp_path, monkeypatch)
    decision = SupervisorDecision(
        kind, "test decision", wait_seconds=0.125 if kind == DecisionKind.WAIT else None
    )
    assert h.supervisor().apply(decision) is True
    assert h.waits == ([0.125] if kind == DecisionKind.WAIT else [])
    assert h.driver.requests == []


@pytest.mark.parametrize("kind", [DecisionKind.PAUSE, DecisionKind.HALT])
def test_apply_terminal_decisions_stop_without_a_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: DecisionKind,
) -> None:
    h = harness(tmp_path, monkeypatch)
    assert h.supervisor().apply(SupervisorDecision(kind, "test terminal")) is False
    assert h.driver.requests == [] and h.waits == []


@pytest.mark.parametrize("success", [False, True])
def test_required_capability_runs_once_and_does_not_count_as_a_workflow_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    success: bool,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(add_capability)
    h.store.transaction(drain)
    h.runner.success = success
    outcome = h.supervisor().run()
    assert outcome.sessions_attempted == 0 and len(h.runner.requests) == 1
    assert outcome.exit_code == (0 if success else 1)
    assert outcome.decision.kind == (
        DecisionKind.COMPLETE if success else DecisionKind.HALT
    )
    capability = h.store.read()["batch"]["capabilities"]["audit"]
    assert capability["status"] == ("succeeded" if success else "failed")
    assert len(capability["attempts"]) == 1
    assert h.driver.requests == []
    (metric,) = reconcile_metrics(h.paths)
    assert metric.kind == "capability" and metric.finished_at is not None


def test_empty_drain_skips_pending_capabilities_without_invoking_them(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(add_capability)
    h.store.transaction(lambda state: drain(state, completed=False))
    outcome = h.supervisor().run()
    assert outcome.exit_code == 0 and outcome.decision.kind == DecisionKind.COMPLETE
    assert outcome.sessions_attempted == 0 and h.runner.requests == []
    capability = h.store.read()["batch"]["capabilities"]["audit"]
    assert capability["status"] == "skipped" and capability["attempts"] == []


def test_configured_prompt_is_literal_and_replaces_driver_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)
    config = h.root / "ovcaq.toml"
    literal = "Run ${HOME} $(touch injected); literal"
    config.write_text(
        config.read_text() + f"[agents.local.prompts]\nbuild = '{literal}'\n"
    )
    h.driver.steps = [Step()]
    h.supervisor().run_once()
    (request,) = h.driver.requests
    assert request.prompt == literal and request.effort == "high"
    assert request.timeout_seconds == 3 and not (h.root / "injected").exists()


def test_supplied_phase_settings_control_each_workflow_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)
    literal = "Run ${HOME} $(touch injected); literal"
    (h.root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner", "--configured"]\n'
        'tiers = { standard = "model-s", deep = "model-o", custom = "model-c" }\n'
        '[agents.local.phases.review]\ntier = "custom"\neffort = "low"\n'
        f"[agents.local.prompts]\nbuild = '{literal} build'\n"
        f"review = '{literal} review'\ndone = '{literal} done'\n"
    )
    original_runtime, original_policy = h.settings.runtime, h.settings.policy
    h.settings = replace(
        h.settings,
        phases={
            "build": PhaseSettings("custom", "medium", 11),
            "review": PhaseSettings("deep", "xhigh", 13),
            "done": PhaseSettings("deep", "low", 17),
        },
    )
    h.driver.steps = [
        Step(effect=lambda: h.change(next_phase="review")),
        Step(effect=lambda: h.change(next_phase="done")),
        Step(effect=lambda: h.change(next_phase="paused")),
    ]

    outcome = h.supervisor().run()

    assert outcome.exit_code == 0 and outcome.sessions_attempted == 3
    assert (
        h.settings.runtime is original_runtime and h.settings.policy is original_policy
    )
    assert [
        (request.phase, request.model, request.effort, request.timeout_seconds)
        for request in h.driver.requests
    ] == [
        ("build", "model-c", "medium", 11),
        ("review", "model-c", "low", 13),
        ("done", "model-o", "low", 17),
    ]
    assert [request.prompt for request in h.driver.requests] == [
        f"{literal} build",
        f"{literal} review",
        f"{literal} done",
    ]
    assert h.driver.name == "local" and not (h.root / "injected").exists()


def test_complete_archives_committed_terminal_state_without_rewriting_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(drain)
    supervisor = h.supervisor()
    outcome = supervisor.run()
    archive = h.paths.reports / "batch-1-state-final.json"
    assert outcome.decision.kind == DecisionKind.COMPLETE and outcome.exit_code == 0
    assert json.loads(archive.read_text()) == h.store.read()
    original = archive.read_bytes(), archive.stat().st_mtime_ns
    assert (
        supervisor.apply(SupervisorDecision(DecisionKind.COMPLETE, "already done"))
        is False
    )
    assert (archive.read_bytes(), archive.stat().st_mtime_ns) == original
    assert outcome.sessions_attempted == 0


def test_startup_reconciles_retained_pending_metric_before_boundary_pause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)
    metadata = SessionMetadata(
        1,
        "old-run",
        "old-session",
        "local",
        99999999,
        "stale-start",
        "2026-10-01T12:00:00Z",
    )
    session = create_session(h.paths, metadata)
    pending = SessionMetric(
        1,
        "phase",
        "old-run",
        "old-session",
        "old-batch",
        None,
        "build",
        None,
        None,
        None,
        metadata.started_at,
        None,
        None,
        "model-s",
        None,
    )
    publish_session_metric(h.paths, session, pending)
    original = session.metrics.read_bytes()
    h.change(next_phase="paused")
    assert h.supervisor().run().exit_code == 0
    (row,) = rows(h.paths.metrics)
    assert row["session_id"] == "old-session" and row["decision"] == "interrupted"
    assert session.metrics.read_bytes() == original


def test_emergency_state_failure_blocks_all_child_launches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)

    def unavailable(site: str, detail: str) -> None:
        raise OSError("synthetic unavailable state store")

    record_state_failure(
        h.paths,
        site="test",
        detail="unacknowledged failure",
        write_state_notice=unavailable,
    )
    with pytest.raises(EmergencyStateFailure):
        h.supervisor().run()
    assert h.driver.requests == [] and not h.paths.run_metadata.exists()


def test_park_moves_active_prd_to_hold_and_continues_with_committed_saga_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)
    paths = resolve_lifecycle_paths(h.root, workflow_settings(h.root).prd_root)
    paths.wip.mkdir(parents=True, exist_ok=True)
    source = paths.wip / "00001-feature.md"
    source.write_text("# Active feature\n\nRetain this PRD during parking.\n")
    original = source.read_bytes()
    h.change(prd=source.name)
    assert (
        h.supervisor().apply(SupervisorDecision(DecisionKind.PARK, "repeat limit"))
        is True
    )
    assert not source.exists() and (paths.hold / source.name).read_bytes() == original
    state = h.store.read()
    assert state["batch"]["parks_consecutive"] == 1
    assert state["recovery"]["operation"] is None
    assert h.driver.requests == []


def test_fake_build_review_done_drain_capability_failure_and_independent_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(add_capability)
    h.runner.success = False
    h.driver.steps = [
        Step(effect=lambda: h.change(next_phase="review")),
        Step(effect=lambda: h.change(next_phase="done")),
        Step(effect=lambda: h.store.transaction(drain)),
    ]
    outcome = h.supervisor().run()
    assert outcome.exit_code == 1 and outcome.decision.kind == DecisionKind.HALT
    assert outcome.sessions_attempted == 3 and len(h.runner.requests) == 1
    assert [request.phase for request in h.driver.requests] == [
        "build",
        "review",
        "done",
    ]
    metrics = reconcile_metrics(h.paths)
    assert [row.kind for row in metrics] == ["phase"] * 3 + ["capability"]
    assert len({row.session_id for row in metrics}) == 4
    assert all(row.finished_at is not None for row in metrics)
    assert [row.decision for row in metrics[:2]] == ["continue", "continue"]
    drained = h.store.read()
    assert drained["control"]["attention"] is not None
    assert drained["batch"]["capabilities"]["audit"]["status"] == "failed"

    def workflow(state: State) -> object:
        return (
            state["work"],
            state["tasks"],
            state["review"],
            state["batch"]["completed_prds"],
        )

    h.runner.success = True
    retried = CapabilityService(
        h.root,
        store=h.store,
        paths=h.paths,
        run_id="retry-run",
        clock=h.clock.now,
        timeout_seconds=3,
    ).retry("audit", h.runner)
    capability = retried["batch"]["capabilities"]["audit"]
    assert capability["status"] == "succeeded" and len(capability["attempts"]) == 2
    assert capability["attempts"][0]["status"] == "failed"
    assert workflow(retried) == workflow(drained)
    assert len(h.runner.requests) == 2 and len(h.driver.requests) == 3
    assert len(reconcile_metrics(h.paths)) == 5


def test_startup_reconciles_stale_capability_owner_without_retrying_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(add_capability)
    h.store.transaction(drain)
    service = CapabilityService(
        h.root,
        store=h.store,
        paths=h.paths,
        run_id="old-run",
        clock=h.clock.now,
        timeout_seconds=3,
    )
    attempt = service.start("audit")
    metadata_path = h.paths.sessions / attempt["session_id"] / "meta.json"
    metadata = json.loads(metadata_path.read_text())
    metadata.update(pid=99999999, process_start="absent-process")
    metadata_path.write_text(json.dumps(metadata))
    outcome = h.supervisor().run()
    assert outcome.exit_code == 1 and outcome.decision.kind == DecisionKind.HALT
    capability = h.store.read()["batch"]["capabilities"]["audit"]
    assert capability["status"] == "failed" and len(capability["attempts"]) == 1
    assert capability["attempts"][0]["finished_at"] is not None
    assert h.runner.requests == [] and outcome.sessions_attempted == 0
