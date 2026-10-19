from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ovcaq.events.model import FailureClass, SessionSummary
from ovcaq.runtime.decision import (
    AttemptResult,
    CapabilitySnapshot,
    DecisionKind,
    ProgressSnapshot,
    RetryState,
    SupervisorDecision,
    SupervisorPolicy,
    decide,
    progress_fingerprint,
    snapshot,
)
from ovcaq.state.schema import (
    CapabilityEntry,
    CapabilityStatus,
    NextPhase,
    Notice,
    State,
    new_state,
)

_NOW = datetime(2026, 10, 2, 12, tzinfo=UTC)
_NOTICE: Notice = {
    "site": "review",
    "detail": "operator intervention",
    "created_at": "2026-10-02T12:00:00Z",
}
_POLICY = SupervisorPolicy(
    died_retries=2,
    connectivity_retries=3,
    rate_limit_retries=2,
    connectivity_wait_seconds=7.5,
    rate_limit_wait_seconds=120.0,
    phase_repeat_limit=3,
)
_NO_RETRIES = RetryState()


def _state() -> State:
    state = new_state(repo_root=Path("/tmp/decision-contract"))
    state["batch"]["id"] = "batch-1"
    state["batch"]["status"] = "running"
    state["work"]["prd"] = "00001-feature.md"
    return state


def _capability(
    status: CapabilityStatus = "pending", *, required: bool = True
) -> CapabilityEntry:
    return {
        "required": required,
        "launcher": "test-driver",
        "plugin": "completion-check",
        "version": "1",
        "failure": "attention",
        "status": status,
        "attempts": [],
    }


def _attempt(
    after: ProgressSnapshot | None,
    failure: FailureClass | None = None,
    *,
    reset_at: datetime | None = None,
    state_error: str | None = None,
) -> AttemptResult:
    return AttemptResult(
        summary=SessionSummary(
            success=failure is None,
            session_id="session-1",
            failure_class=failure,
            failure_detail="normalized failure" if failure else None,
            rate_limit_reset_at=reset_at,
            usage=None,
        ),
        started_at=_NOW - timedelta(seconds=10),
        finished_at=_NOW,
        state_after=after,
        state_error=state_error,
    )


def _decision(
    before: ProgressSnapshot,
    result: AttemptResult,
    retries: RetryState = _NO_RETRIES,
    policy: SupervisorPolicy = _POLICY,
) -> SupervisorDecision:
    return decide(before, result, retries, policy, now=_NOW)


@pytest.mark.parametrize("next_phase", ["build", "review", "done", "paused", ""])
def test_snapshot_reads_committed_fields_and_only_empty_next_phase_is_drained(
    next_phase: NextPhase,
) -> None:
    state = _state()
    state["revision"] = 17
    state["work"].update(phase="done", next_phase=next_phase, tasks_completed=2)
    state["review"]["cycle"] = 4
    state["control"].update(pause_requested=True, pause_reason=_NOTICE)
    state["recovery"].update(phase_fingerprint="saved", phase_repeats=2)
    state["batch"]["capabilities"]["audit"] = _capability()
    original = deepcopy(state)
    actual = snapshot(state)
    assert actual == ProgressSnapshot(
        revision=17,
        batch_id="batch-1",
        batch_status="running",
        prd="00001-feature.md",
        phase="done",
        next_phase=next_phase,
        pause_requested=True,
        pause_reason=_NOTICE,
        attention=None,
        recovery_operation=None,
        tasks_completed=2,
        review_cycle=4,
        completed_prds=0,
        drained=next_phase == "",
        capabilities={"audit": CapabilitySnapshot(True, "pending", None, None)},
        phase_fingerprint="saved",
        phase_repeats=2,
    )
    assert state == original
    with pytest.raises(FrozenInstanceError):
        actual.revision = 99  # type: ignore[misc]


def test_snapshot_preserves_latest_capability_attempt_and_completed_prd_count() -> None:
    state = _state()
    capability = _capability("running")
    for number in (1, 2):
        capability["attempts"].append(
            {
                "id": f"attempt-{number}",
                "status": "running",
                "started_at": "2026-10-02T12:00:00Z",
                "finished_at": None,
                "session_id": f"session-{number}",
                "detail": None,
            }
        )
    state["batch"]["capabilities"]["audit"] = capability
    state["batch"]["completed_prds"].append(
        {
            "filename": "00000-previous.md",
            "cycles": 1,
            "autonomous_decisions": 0,
            "escalated_decisions": 0,
            "tasks_completed": 2,
            "tasks_total": 2,
        }
    )
    actual = snapshot(state)
    assert actual.completed_prds == 1
    assert actual.capabilities["audit"] == CapabilitySnapshot(
        True, "running", "attempt-2", "session-2"
    )


@pytest.mark.parametrize(
    "field",
    [
        "prd",
        "phase",
        "next_phase",
        "tasks_completed",
        "review_cycle",
        "completed_prds",
        "capability_status",
        "attempt_id",
        "session_id",
    ],
)
def test_fingerprint_changes_for_each_workflow_progress_component(field: str) -> None:
    state = _state()
    capability = _capability("running")
    capability["attempts"] = [
        {
            "id": "attempt-1",
            "status": "running",
            "started_at": "2026-10-02T12:00:00Z",
            "finished_at": None,
            "session_id": "session-1",
            "detail": None,
        }
    ]
    state["batch"]["capabilities"]["audit"] = capability
    original = progress_fingerprint(state)
    if field == "prd":
        state["work"]["prd"] = "00002-other.md"
    elif field == "phase":
        state["work"]["phase"] = "review"
    elif field == "next_phase":
        state["work"]["next_phase"] = "review"
    elif field == "tasks_completed":
        state["work"]["tasks_completed"] = 1
    elif field == "review_cycle":
        state["review"]["cycle"] = 1
    elif field == "completed_prds":
        state["batch"]["completed_prds"].append(
            {
                "filename": "previous.md",
                "cycles": 0,
                "autonomous_decisions": 0,
                "escalated_decisions": 0,
                "tasks_completed": 0,
                "tasks_total": 0,
            }
        )
    elif field == "capability_status":
        capability["status"] = "failed"
    elif field == "attempt_id":
        capability["attempts"][-1]["id"] = "attempt-2"
    else:
        capability["attempts"][-1]["session_id"] = "session-2"
    assert progress_fingerprint(state) != original
    assert progress_fingerprint(deepcopy(state)) == progress_fingerprint(state)


def test_fingerprint_ignores_bookkeeping_notices_and_capability_mapping_order() -> None:
    state = _state()
    state["batch"]["capabilities"] = {"z": _capability(), "a": _capability()}
    original = progress_fingerprint(state)
    state["revision"] += 1
    state["recovery"].update(
        phase_fingerprint="stale", phase_repeats=99, replan_count=4
    )
    state["control"].update(
        pause_requested=True, pause_reason=_NOTICE, attention=_NOTICE
    )
    state["batch"]["parks_consecutive"] = 9
    state["batch"]["capabilities"] = dict(
        reversed(state["batch"]["capabilities"].items())
    )
    assert progress_fingerprint(state) == original


@pytest.mark.parametrize("state_error", [None, "state cannot be decoded"])
def test_missing_post_state_halts_before_pause_or_provider_failure(
    state_error: str | None,
) -> None:
    before = replace(snapshot(_state()), pause_requested=True)
    actual = _decision(
        before, _attempt(None, FailureClass.CONNECTIVITY, state_error=state_error)
    )
    assert actual.kind == DecisionKind.HALT
    assert actual.wait_seconds is None


def test_unreadable_post_state_halts_even_when_a_snapshot_is_available() -> None:
    before = snapshot(_state())
    after = replace(before, pause_requested=True)
    actual = _decision(before, _attempt(after, state_error="post-state read failed"))
    assert actual.kind == DecisionKind.HALT


@pytest.mark.parametrize("pause_form", ["request", "phase", "next_phase"])
def test_durable_pause_precedes_empty_drain_capabilities_and_failure(
    pause_form: str,
) -> None:
    before = snapshot(_state())
    after = replace(
        before,
        drained=True,
        next_phase="",
        capabilities={
            "audit": CapabilitySnapshot(True, "pending", None, None),
        },
    )
    if pause_form == "request":
        after = replace(after, pause_requested=True, pause_reason=_NOTICE)
    elif pause_form == "phase":
        after = replace(after, phase="paused")
    else:
        after = replace(after, next_phase="paused", drained=False)
    actual = _decision(before, _attempt(after, FailureClass.CONNECTIVITY))
    assert actual.kind == DecisionKind.PAUSE
    assert actual.capability is None
    assert actual.wait_seconds is None


@pytest.mark.parametrize("completed_prds", [0, 1])
def test_empty_drain_skips_but_nonempty_drain_runs_sorted_required_capabilities(
    completed_prds: int,
) -> None:
    before = snapshot(_state())
    after = replace(
        before,
        drained=True,
        next_phase="",
        completed_prds=completed_prds,
        capabilities={
            "z-required": CapabilitySnapshot(True, "pending", None, None),
            "a-running": CapabilitySnapshot(True, "running", "attempt-1", "live-1"),
            "b-required": CapabilitySnapshot(True, "pending", None, None),
            "a-optional": CapabilitySnapshot(False, "pending", None, None),
            "failed": CapabilitySnapshot(True, "failed", "attempt-2", "failed-1"),
        },
    )
    actual = _decision(before, _attempt(after, FailureClass.RATE_LIMIT))
    assert actual.kind == (
        DecisionKind.SKIP_CAPABILITIES
        if completed_prds == 0
        else DecisionKind.RUN_CAPABILITY
    )
    if completed_prds:
        assert actual.capability == "b-required"


@pytest.mark.parametrize("failed_required", [False, True])
def test_required_capability_failure_or_attention_halts_before_completion(
    failed_required: bool,
) -> None:
    before = snapshot(_state())
    after = replace(
        before,
        drained=True,
        next_phase="",
        completed_prds=1,
        attention=None if failed_required else _NOTICE,
        capabilities={
            "audit": CapabilitySnapshot(
                True, "failed" if failed_required else "succeeded", "a1", "s1"
            ),
        },
    )
    actual = _decision(before, _attempt(after, FailureClass.CONNECTIVITY))
    assert actual.kind == DecisionKind.HALT


def test_completed_capabilities_finish_despite_optional_failure_and_session_death() -> (
    None
):
    before = snapshot(_state())
    after = replace(
        before,
        drained=True,
        next_phase="",
        completed_prds=1,
        capabilities={
            "required": CapabilitySnapshot(True, "succeeded", "a1", "s1"),
            "optional": CapabilitySnapshot(False, "failed", "a2", "s2"),
        },
    )
    assert (
        _decision(before, _attempt(after, FailureClass.AGENT)).kind
        == DecisionKind.COMPLETE
    )


def test_running_capability_is_neither_relaunched_nor_reported_complete() -> None:
    before = snapshot(_state())
    after = replace(
        before,
        drained=True,
        next_phase="",
        completed_prds=1,
        capabilities={
            "required": CapabilitySnapshot(True, "running", "a1", "live-session"),
        },
    )
    actual = _decision(before, _attempt(after))
    assert actual.kind == DecisionKind.HALT
    assert actual.capability is None


@pytest.mark.parametrize("status", [None, "pending", "failed", "succeeded"])
@pytest.mark.parametrize("failure", list(FailureClass))
@pytest.mark.parametrize(
    "progress",
    [
        {"next_phase": "review"},
        {"tasks_completed": 1},
        {"review_cycle": 1},
        {"prd": "00002-other.md"},
        {"completed_prds": 1},
    ],
    ids=["next_phase", "tasks_completed", "review_cycle", "prd", "completed_prds"],
)
def test_committed_progress_continues_before_session_failure_without_drain(
    status: CapabilityStatus | None,
    failure: FailureClass,
    progress: dict[str, object],
) -> None:
    before = replace(snapshot(_state()), phase_repeats=99)
    capabilities = (
        {}
        if status is None
        else {"audit": CapabilitySnapshot(True, status, None, None)}
    )
    after = replace(before, capabilities=capabilities, **progress)
    actual = _decision(before, _attempt(after, failure), RetryState(99, 99, 99))
    assert actual.kind == DecisionKind.CONTINUE
    assert actual.next_phase_repeats == 0
    assert actual.wait_seconds is None


def test_attention_halts_before_committed_phase_progress() -> None:
    before = snapshot(_state())
    after = replace(before, next_phase="review", attention=_NOTICE)
    assert _decision(before, _attempt(after)).kind == DecisionKind.HALT


@pytest.mark.parametrize(
    ("delay", "used", "expected"),
    [
        (None, 0, DecisionKind.HALT),
        (-1, 0, DecisionKind.HALT),
        (0, 0, DecisionKind.HALT),
        (0.001, 0, DecisionKind.WAIT),
        (120, 1, DecisionKind.WAIT),
        (120.001, 0, DecisionKind.HALT),
        (1, 2, DecisionKind.HALT),
        (1, 3, DecisionKind.HALT),
    ],
)
def test_rate_limit_wait_requires_a_future_bounded_reset_and_remaining_budget(
    delay: float | None,
    used: int,
    expected: DecisionKind,
) -> None:
    before = snapshot(_state())
    reset = None if delay is None else _NOW + timedelta(seconds=delay)
    result = _attempt(before, FailureClass.RATE_LIMIT, reset_at=reset)
    actual = _decision(
        before, result, RetryState(died=99, connectivity=99, rate_limit=used)
    )
    assert actual.kind == expected
    assert actual.wait_seconds == (delay if expected == DecisionKind.WAIT else None)


@pytest.mark.parametrize("used", [0, 2, 3, 4])
def test_connectivity_waits_exact_policy_delay_until_its_own_budget_is_exhausted(
    used: int,
) -> None:
    before = snapshot(_state())
    result = _attempt(before, FailureClass.CONNECTIVITY)
    actual = _decision(
        before, result, RetryState(died=99, connectivity=used, rate_limit=99)
    )
    assert actual.kind == (DecisionKind.WAIT if used < 3 else DecisionKind.HALT)
    assert actual.wait_seconds == (7.5 if used < 3 else None)


@pytest.mark.parametrize("prd", [None, "00001-feature.md"])
@pytest.mark.parametrize("used", [0, 1, 2, 3])
@pytest.mark.parametrize(
    "failure", [FailureClass.AGENT, FailureClass.UNKNOWN, FailureClass.TIMEOUT]
)
def test_untouched_death_retries_then_parks_active_work_or_halts_bootstrap(
    prd: str | None,
    used: int,
    failure: FailureClass,
) -> None:
    before = replace(snapshot(_state()), prd=prd)
    actual = _decision(before, _attempt(before, failure), RetryState(used, 99, 99))
    expected = (
        DecisionKind.RETRY
        if used < 2
        else (DecisionKind.PARK if prd else DecisionKind.HALT)
    )
    assert actual.kind == expected
    assert actual.wait_seconds is None


@pytest.mark.parametrize("prd", [None, "00001-feature.md"])
@pytest.mark.parametrize("repeats", [0, 1, 2, 3])
def test_success_without_workflow_progress_retries_then_parks_or_pauses(
    prd: str | None,
    repeats: int,
) -> None:
    state = _state()
    state["work"]["prd"] = prd
    state["recovery"].update(
        phase_fingerprint=progress_fingerprint(state), phase_repeats=repeats
    )
    before = snapshot(state)
    after = replace(
        before, revision=before.revision + 1, phase_fingerprint="bookkeeping"
    )
    actual = _decision(before, _attempt(after))
    expected = (
        DecisionKind.RETRY
        if repeats + 1 < 3
        else (DecisionKind.PARK if prd else DecisionKind.PAUSE)
    )
    assert actual.kind == expected
    assert actual.next_phase_repeats == repeats + 1


def test_decisions_are_repeatable_and_leave_inputs_unchanged() -> None:
    before = snapshot(_state())
    result = _attempt(before, FailureClass.CONNECTIVITY)
    retries = RetryState(died=1, connectivity=1, rate_limit=1)
    original = repr((before, result, retries, _POLICY))
    first = _decision(before, result, retries)
    second = _decision(before, result, retries)
    assert first == second
    assert first.kind == DecisionKind.WAIT
    assert first.wait_seconds == 7.5
    assert repr((before, result, retries, _POLICY)) == original
    with pytest.raises(FrozenInstanceError):
        first.kind = DecisionKind.HALT  # type: ignore[misc]


def test_committed_build_review_done_sequence_drains_without_process_execution() -> (
    None
):
    current = snapshot(_state())
    phases: tuple[NextPhase, ...] = ("review", "done", "")
    decisions = []
    for next_phase in phases:
        after = replace(
            current,
            next_phase=next_phase,
            drained=next_phase == "",
            completed_prds=1 if next_phase == "" else 0,
        )
        decisions.append(_decision(current, _attempt(after)).kind)
        current = after
    assert decisions == [
        DecisionKind.CONTINUE,
        DecisionKind.CONTINUE,
        DecisionKind.COMPLETE,
    ]
