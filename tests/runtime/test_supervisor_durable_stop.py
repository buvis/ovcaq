from __future__ import annotations

import os
import signal
import threading
from datetime import datetime
from pathlib import Path

import pytest
from tests.runtime.test_supervisor import Step, add_capability, drain, harness

from ovcaq.runtime.decision import DecisionKind, SupervisorDecision
from ovcaq.runtime.session import (
    EmergencyStateFailure,
    acknowledge_emergency_failure,
    record_state_failure,
    require_no_emergency_failure,
)
from ovcaq.state.commands import StateService
from ovcaq.state.schema import State

SECRET = "SYNTHETIC-SENSITIVE-STATE-FAILURE-11"
CLOCK_DATES = ("2026-10-02T12:00:00Z", "2028-03-17T04:15:36Z")


def seed_history(state: State) -> None:
    state["tasks"] = [
        {
            "id": 1,
            "name": "Finished work",
            "description": "Retain completed task evidence",
            "active_form": "",
            "status": "completed",
            "blocked_by": [],
            "tier": None,
            "files_touched": None,
            "public_contract_edit": None,
            "estimates": {"input_tokens": None, "context_peak": None},
            "attempts": [],
            "metadata": {"sentinel": [1, 2]},
        }
    ]
    state["work"].update(tasks_total=1, tasks_completed=1)
    state["review"]["extensions"] = {"test/review": {"retained": [3, 4]}}


def seed_failure_intent(state: State) -> None:
    seed_history(state)
    state["control"]["pause_reason"] = {
        "site": "review_cap",
        "detail": "Retain prior routing reason",
        "created_at": "2026-10-01T12:00:00Z",
    }


def fail_writes(monkeypatch: pytest.MonkeyPatch, target: Path) -> None:
    replace = os.replace

    def unavailable(
        source: object, destination: object, *args: object, **kwargs: object
    ) -> None:
        if Path(destination) == target:
            raise OSError(SECRET)
        replace(source, destination, *args, **kwargs)

    monkeypatch.setattr(os, "replace", unavailable)


def assert_sanitized(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            assert SECRET.encode() not in path.read_bytes(), path


def test_state_write_failure_halts_and_blocks_restart_until_acknowledged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    original = h.store.read()
    with monkeypatch.context() as faults:
        fail_writes(faults, h.paths.state_file)
        outcome = h.supervisor().run()
    assert outcome.exit_code == 1 and outcome.decision.kind == DecisionKind.HALT
    assert h.driver.requests == []
    assert h.store.read() == original
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(h.paths)
    with pytest.raises(EmergencyStateFailure):
        h.supervisor().run()
    assert h.store.read() == original and h.driver.requests == []
    assert_sanitized(h.paths.state_file.parent)
    acknowledge_emergency_failure(h.paths, state_valid=True)
    require_no_emergency_failure(h.paths)
    h.driver.steps = [Step(effect=lambda: h.change(next_phase="paused"))]
    assert h.supervisor().run().sessions_attempted == 1


@pytest.mark.parametrize("run_loop", [False, True])
def test_real_post_session_read_failure_leaves_emergency_restart_barrier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, run_loop: bool
) -> None:
    h = harness(tmp_path, monkeypatch)
    original = h.paths.state_file.read_bytes()
    h.driver.steps = [Step(effect=lambda: h.paths.state_file.write_text("{broken"))]
    supervisor = h.supervisor()
    if run_loop:
        assert supervisor.run().decision.kind == DecisionKind.HALT
    else:
        assert supervisor.run_once().state_error
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(h.paths)
    h.paths.state_file.write_bytes(original)
    with pytest.raises(EmergencyStateFailure):
        h.supervisor().run()
    assert len(h.driver.requests) == 1
    acknowledge_emergency_failure(h.paths, state_valid=True)
    require_no_emergency_failure(h.paths)


def test_transient_state_read_failure_records_sanitized_durable_notice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(seed_failure_intent)
    before = h.store.read()
    open_file = os.open
    failed = False

    def unavailable(path: object, *args: object, **kwargs: object) -> int:
        nonlocal failed
        if Path(path) == h.paths.state_file and not failed:
            failed = True
            raise OSError(SECRET)
        return open_file(path, *args, **kwargs)

    with monkeypatch.context() as faults:
        faults.setattr(os, "open", unavailable)
        outcome = h.supervisor().run()
    assert failed and outcome.decision.kind == DecisionKind.HALT
    state = h.store.read()
    notice = state["control"]["attention"]
    assert notice is not None
    assert notice["site"].strip() and notice["detail"].strip()
    for section in ("work", "batch", "tasks", "review", "recovery"):
        assert state[section] == before[section]
    for key in ("pause_requested", "pause_reason"):
        assert state["control"][key] == before["control"][key]
    require_no_emergency_failure(h.paths)
    assert_sanitized(h.paths.state_file.parent)
    restarted = h.supervisor().run()
    assert restarted.decision.kind == DecisionKind.HALT
    assert restarted.exit_code != 0 and restarted.sessions_attempted == 0
    assert h.driver.requests == []


def test_emergency_barrier_precedes_capability_reconciliation_and_all_state_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(add_capability)
    StateService(h.store).start_capability(
        "audit",
        {
            "id": "orphan",
            "status": "running",
            "started_at": "2026-10-02T12:00:00Z",
            "finished_at": None,
            "session_id": "orphan-session",
            "detail": None,
        },
    )

    def unavailable(site: str, detail: str) -> None:
        raise OSError("unavailable")

    record_state_failure(
        h.paths, site="test", detail="failure", write_state_notice=unavailable
    )
    before = h.paths.state_file.read_bytes()
    with pytest.raises(EmergencyStateFailure):
        h.supervisor().run()
    assert h.paths.state_file.read_bytes() == before
    assert h.driver.requests == [] and h.runner.requests == []


def preserve_intent(state: State) -> None:
    drain(state)
    state["work"].update(phase="paused", next_phase="paused")
    state["control"]["pause_reason"] = {
        "site": "review_cap",
        "detail": "Review limit",
        "created_at": "2026-10-01T12:00:00Z",
    }
    state["control"]["attention"] = {
        "site": "test",
        "detail": "Keep attention",
        "created_at": "2026-10-01T12:00:00Z",
    }
    state["recovery"]["operation"] = {
        "id": "recovery-1",
        "kind": "park",
        "step": "intent",
        "prd": "example.md",
        "site": "supervisor",
        "detail": "Moving PRD",
        "source": "backlog/example.md",
        "destination": "parked/example.md",
        "artifact": None,
        "created_at": "2026-10-01T12:00:00Z",
    }


@pytest.mark.parametrize("preserve", [False, True])
@pytest.mark.parametrize("number", [signal.SIGINT, signal.SIGTERM])
@pytest.mark.parametrize("clock_date", CLOCK_DATES)
def test_signal_persists_stop_with_injected_clock_and_preserves_existing_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    preserve: bool,
    number: signal.Signals,
    clock_date: str,
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.clock.current = datetime.fromisoformat(clock_date)
    h.store.transaction(seed_history)
    h.driver.steps = [
        Step(code="print('ready', flush=True); import time; time.sleep(10)")
    ]
    before: list[State] = []

    def stop(line: str) -> None:
        if preserve:
            h.store.transaction(preserve_intent)
        before.append(h.store.read())
        threading.Timer(0.05, os.kill, args=(os.getpid(), number)).start()

    h.driver.on_line = stop
    assert h.supervisor().run().exit_code == 128 + number
    state = h.store.read()
    assert state["control"]["pause_requested"] is True
    if preserve:
        assert state["control"]["pause_reason"] == before[0]["control"]["pause_reason"]
    else:
        notice = state["control"]["pause_reason"]
        assert notice is not None and notice["site"] == "operator_stop"
        assert str(int(number)) in notice["detail"]
        assert datetime.fromisoformat(notice["created_at"]) == h.clock.now()
    for section in ("work", "recovery", "batch", "tasks", "review"):
        assert state[section] == before[0][section]
    assert state["control"]["attention"] == before[0]["control"]["attention"]


def test_stop_publication_failure_uses_sanitized_emergency_restart_barrier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.driver.steps = [
        Step(code="print('ready', flush=True); import time; time.sleep(10)")
    ]

    def stop(line: str) -> None:
        fail_writes(monkeypatch, h.paths.state_file)
        threading.Timer(0.05, os.kill, args=(os.getpid(), signal.SIGTERM)).start()

    h.driver.on_line = stop
    assert h.supervisor().run().exit_code == 143
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(h.paths)
    assert_sanitized(h.paths.state_file.parent)
    with pytest.raises(EmergencyStateFailure):
        h.supervisor().run()
    assert len(h.driver.requests) == 1


def test_apply_completion_failure_leaves_durable_sanitized_restart_barrier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(drain)
    with monkeypatch.context() as faults:
        fail_writes(faults, h.paths.state_file)
        assert (
            h.supervisor().apply(SupervisorDecision(DecisionKind.COMPLETE, "drained"))
            is False
        )
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(h.paths)
    assert_sanitized(h.paths.state_file.parent)
    with pytest.raises(EmergencyStateFailure):
        h.supervisor().run()
    assert h.driver.requests == []


def test_post_session_progress_write_failure_halts_and_blocks_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(seed_history)
    before: list[State] = []

    def fail_progress_write() -> None:
        before.append(h.store.read())
        fail_writes(monkeypatch, h.paths.state_file)

    h.driver.steps = [Step(effect=fail_progress_write)]
    outcome = h.supervisor().run()
    assert outcome.sessions_attempted == 1
    assert outcome.exit_code != 0 and outcome.decision.kind == DecisionKind.HALT
    assert len(h.driver.requests) == 1
    assert h.store.read() == before[0]
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(h.paths)
    assert_sanitized(h.paths.state_file.parent)
    with pytest.raises(EmergencyStateFailure):
        h.supervisor().run()
    assert len(h.driver.requests) == 1
    assert h.store.read() == before[0]


def test_started_drained_run_completion_write_failure_halts_and_blocks_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(seed_history)
    StateService(h.store).start_batch("batch-1", "2026-10-02T12:00:00Z")
    h.store.transaction(drain)
    before = h.store.read()
    assert before["batch"]["started_at"] is not None
    with monkeypatch.context() as faults:
        fail_writes(faults, h.paths.state_file)
        outcome = h.supervisor().run()
    assert outcome.exit_code != 0 and outcome.decision.kind == DecisionKind.HALT
    assert outcome.sessions_attempted == 0
    assert h.store.read() == before
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(h.paths)
    assert_sanitized(h.paths.state_file.parent)
    with pytest.raises(EmergencyStateFailure):
        h.supervisor().run()
    assert h.driver.requests == []
    assert h.store.read() == before


def test_transient_state_read_failure_preserves_unacknowledged_attention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    attention = {
        "site": "operator_review",
        "detail": "Inspect the retained review evidence before continuing.",
        "created_at": "2026-09-14T08:17:31Z",
    }
    h.store.transaction(lambda state: state["control"].update(attention=attention))
    assert h.store.read()["control"]["attention"] == attention
    open_file = os.open
    failed = False

    def unavailable(path: object, *args: object, **kwargs: object) -> int:
        nonlocal failed
        if Path(path) == h.paths.state_file and not failed:
            failed = True
            raise OSError(SECRET)
        return open_file(path, *args, **kwargs)

    with monkeypatch.context() as faults:
        faults.setattr(os, "open", unavailable)
        outcome = h.supervisor().run()
    assert failed
    assert outcome.exit_code != 0 and outcome.decision.kind == DecisionKind.HALT
    assert outcome.sessions_attempted == 0
    assert h.store.read()["control"]["attention"] == attention
    assert_sanitized(h.paths.state_file.parent)
    restarted = h.supervisor().run()
    assert restarted.exit_code != 0 and restarted.decision.kind == DecisionKind.HALT
    assert restarted.sessions_attempted == 0
    assert h.driver.requests == []
    assert h.store.read()["control"]["attention"] == attention
