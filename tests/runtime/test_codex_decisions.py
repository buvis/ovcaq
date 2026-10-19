from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import AgentDriver
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import FailureClass, SessionSummary
from ovcaq.runtime.decision import (
    AttemptResult,
    CapabilitySnapshot,
    DecisionKind,
    ProgressSnapshot,
    RetryState,
    SupervisorPolicy,
    boundary_decision,
    decide,
    progress_fingerprint,
    snapshot,
)
from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore

_FIXTURES = Path(__file__).parents[1] / "fixtures"
_POLICY = SupervisorPolicy(2, 3, 2, 7.5, 120.0, 3)
_DEFAULT_RETRIES = RetryState()


@pytest.fixture(params=["claude", "codex"])
def driver(request: pytest.FixtureRequest) -> AgentDriver:
    name = request.param
    settings = AgentSettings(
        name=name,
        command=("unused-test-executable",),
        tiers={},
        environment={},
        options={"permission_mode": "auto"} if name == "claude" else {},
    )
    cls = ClaudeDriver if name == "claude" else CodexDriver
    return cls(settings, run_id="decision-matrix")


@pytest.fixture
def store(tmp_path: Path) -> StateStore:
    initial = new_state(repo_root=tmp_path)
    initial["batch"].update(id="matrix-batch", status="running")
    initial["work"]["prd"] = "00001-feature.md"
    store = StateStore(tmp_path / "state.json")
    store.initialize(initial)
    return store


def _prose_lines(driver: AgentDriver) -> list[str]:
    record = (
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "All phases complete!"}]},
        }
        if driver.name == "claude"
        else {
            "type": "item.completed",
            "item": {
                "id": "prose",
                "type": "agent_message",
                "text": "All phases complete!",
            },
        }
    )
    return [json.dumps(record)]


def _reset_lines(driver: AgentDriver, reset: datetime) -> list[str]:
    if driver.name == "claude":
        return [
            json.dumps(
                {
                    "type": "rate_limit_event",
                    "rate_limit_info": {
                        "status": "rejected",
                        "resetsAt": reset.timestamp(),
                    },
                }
            )
        ]
    return [
        json.dumps(
            {
                "type": "turn.failed",
                "error": {
                    "message": f"Rate limit reached; reset at {reset.isoformat()}"
                },
            }
        )
    ]


def _claude_failure_lines(failure: FailureClass) -> list[str]:
    indices = {
        FailureClass.CONNECTIVITY: 0,
        FailureClass.AUTHENTICATION: 1,
        FailureClass.PERMISSION: 2,
        FailureClass.TIMEOUT: 3,
        FailureClass.AGENT: 4,
        FailureClass.RATE_LIMIT: 5,
    }
    return (
        [
            (_FIXTURES / "claude/v1/failures.jsonl")
            .read_text()
            .splitlines()[indices[failure]]
        ]
        if failure in indices
        else [
            json.dumps(
                {
                    "type": "result",
                    "subtype": "error",
                    "is_error": True,
                    "result": None,
                }
            )
        ]
    )


def _codex_failure_lines(failure: FailureClass) -> list[str]:
    fixtures = {
        FailureClass.AUTHENTICATION: "authentication-failed",
        FailureClass.PERMISSION: "permission-failed",
    }
    details = {
        FailureClass.CONNECTIVITY: "connection refused by example endpoint",
        FailureClass.RATE_LIMIT: "Rate limit reached",
        FailureClass.TIMEOUT: "request timed out",
        FailureClass.AGENT: "agent failed",
        FailureClass.UNKNOWN: "unclassified terminal failure",
    }
    return (
        (_FIXTURES / "codex/v1" / f"{fixtures[failure]}.jsonl").read_text().splitlines()
        if failure in fixtures
        else [
            json.dumps({"type": "turn.failed", "error": {"message": details[failure]}})
        ]
    )


def _summary(
    driver: AgentDriver,
    failure: FailureClass | None = None,
    *,
    exit_code: int = 0,
    reset: datetime | None = None,
    prose_only: bool = False,
) -> SessionSummary:
    """Inject native records at the edge; never manufacture normalized summaries."""
    if prose_only:
        lines = _prose_lines(driver)
    elif failure is None:
        lines = (
            (_FIXTURES / driver.name / "v1" / "healthy.jsonl").read_text().splitlines()
        )
        # Unknown native noise cannot override a committed handoff.
        lines.append("not-json: noisy session output")
    elif reset is not None:
        lines = _reset_lines(driver, reset)
    elif driver.name == "claude":
        lines = _claude_failure_lines(failure)
    else:
        lines = _codex_failure_lines(failure)
    observations = tuple(
        observation for line in lines for observation in driver.decode(line)
    )
    summary = driver.summarize(observations, exit_code)
    if failure is not None:
        assert not summary.success
        assert summary.failure_class == failure
    return summary


def _decision(
    before: ProgressSnapshot,
    after: ProgressSnapshot | None,
    summary: SessionSummary,
    retries: RetryState = _DEFAULT_RETRIES,
    *,
    now: datetime | None = None,
    state_error: str | None = None,
):
    now = now or datetime.now(UTC)
    return decide(
        before,
        AttemptResult(summary, now, now, after, state_error),
        retries,
        _POLICY,
        now=now,
    )


@pytest.mark.parametrize("failure", [None, *FailureClass])
@pytest.mark.parametrize("exit_code", [0, 17])
def test_committed_handoff_outweighs_native_noise_and_exit(
    driver: AgentDriver, store: StateStore, failure: FailureClass | None, exit_code: int
) -> None:
    before = snapshot(store.read())
    summary = _summary(driver, failure, exit_code=exit_code)
    store.transaction(lambda state: state["work"].update(next_phase="review"))
    after = snapshot(store.read())
    assert after.revision == before.revision + 1
    actual = _decision(before, after, summary, RetryState(99, 99, 99))
    assert actual.kind == DecisionKind.CONTINUE
    assert actual.next_phase_repeats == 0
    assert actual.wait_seconds is None


@pytest.mark.parametrize("failure", list(FailureClass))
@pytest.mark.parametrize("exhausted", [False, True])
@pytest.mark.parametrize("active_prd", [False, True])
def test_native_failures_use_only_their_own_retry_budget(
    driver: AgentDriver,
    store: StateStore,
    failure: FailureClass,
    exhausted: bool,
    active_prd: bool,
) -> None:
    before = replace(
        snapshot(store.read()), prd="00001-feature.md" if active_prd else None
    )
    summary = _summary(driver, failure)
    used = 99 if exhausted else 0
    retries = RetryState(used, 99, 99)
    if failure == FailureClass.CONNECTIVITY:
        retries = RetryState(99, used, 99)
        expected = DecisionKind.HALT if exhausted else DecisionKind.WAIT
    elif failure in {
        FailureClass.RATE_LIMIT,
        FailureClass.PERMISSION,
        FailureClass.AUTHENTICATION,
    }:
        expected = DecisionKind.HALT
    else:
        expected = (
            (DecisionKind.PARK if active_prd else DecisionKind.HALT)
            if exhausted
            else DecisionKind.RETRY
        )
    actual = _decision(before, before, summary, retries)
    assert actual.kind == expected
    assert actual.wait_seconds == (7.5 if expected == DecisionKind.WAIT else None)
    assert actual.next_phase_repeats == 1


@pytest.mark.parametrize("delay", [60, 120, 121])
@pytest.mark.parametrize("used", [0, 1, 2, 3])
def test_native_reset_is_bounded_and_rate_retry_budget_is_independent(
    driver: AgentDriver, store: StateStore, delay: int, used: int
) -> None:
    now = datetime.now(UTC)
    reset = now + timedelta(seconds=delay)
    summary = _summary(driver, FailureClass.RATE_LIMIT, reset=reset)
    assert summary.rate_limit_reset_at == reset
    before = snapshot(store.read())
    actual = _decision(before, before, summary, RetryState(99, 99, used), now=now)
    expected = DecisionKind.WAIT if delay <= 120 and used < 2 else DecisionKind.HALT
    assert actual.kind == expected
    assert actual.wait_seconds == (delay if expected == DecisionKind.WAIT else None)


def test_expired_native_reset_cannot_schedule_a_wait(
    driver: AgentDriver, store: StateStore
) -> None:
    now = datetime.now(UTC)
    reset = now + timedelta(seconds=60)
    summary = _summary(driver, FailureClass.RATE_LIMIT, reset=reset)
    before = snapshot(store.read())
    actual = _decision(before, before, summary, now=reset + timedelta(seconds=1))
    assert actual.kind == DecisionKind.HALT
    assert actual.wait_seconds is None


@pytest.mark.parametrize("prose_only", [False, True])
@pytest.mark.parametrize("repeats", [0, 1, 2, 3])
@pytest.mark.parametrize("active_prd", [False, True])
def test_success_prose_and_bookkeeping_never_complete_unchanged_work(
    driver: AgentDriver,
    store: StateStore,
    prose_only: bool,
    repeats: int,
    active_prd: bool,
) -> None:
    def bookkeeping(state):
        state["work"]["prd"] = "00001-feature.md" if active_prd else None
        state["recovery"].update(
            phase_fingerprint=progress_fingerprint(state), phase_repeats=repeats
        )

    store.transaction(bookkeeping)
    before = snapshot(store.read())
    summary = _summary(driver, prose_only=prose_only)
    assert summary.success is (not prose_only)
    store.transaction(lambda state: state["recovery"].update(replan_count=1))
    after = snapshot(store.read())
    assert after.revision == before.revision + 1
    actual = _decision(before, after, summary)
    expected = (
        DecisionKind.RETRY
        if repeats + 1 < 3
        else (
            DecisionKind.PARK
            if active_prd
            else (DecisionKind.HALT if prose_only else DecisionKind.PAUSE)
        )
    )
    assert actual.kind == expected
    assert actual.next_phase_repeats == repeats + 1


@pytest.mark.parametrize("matching", [False, True])
def test_phase_fingerprint_limits_repeated_native_failure(
    driver: AgentDriver, store: StateStore, matching: bool
) -> None:
    store.transaction(
        lambda state: state["recovery"].update(
            phase_fingerprint=progress_fingerprint(state)
            if matching
            else "previous-phase",
            phase_repeats=2,
        )
    )
    before = snapshot(store.read())
    actual = _decision(before, before, _summary(driver, FailureClass.CONNECTIVITY))
    assert actual.kind == (DecisionKind.PARK if matching else DecisionKind.WAIT)
    assert actual.next_phase_repeats == (3 if matching else 1)


@pytest.mark.parametrize(
    "control",
    ["pause-request", "paused-phase", "paused-next", "attention", "drained"],
)
def test_committed_controls_precede_native_failure_and_progress(
    driver: AgentDriver, store: StateStore, control: str
) -> None:
    before = snapshot(store.read())

    def commit(state):
        state["work"]["next_phase"] = ""
        if control == "pause-request":
            state["control"]["pause_requested"] = True
        elif control == "paused-phase":
            state["work"]["phase"] = "paused"
        elif control == "paused-next":
            state["work"]["next_phase"] = "paused"
        elif control == "attention":
            state["control"]["attention"] = {
                "site": "review",
                "detail": "operator intervention",
                "created_at": "2026-10-02T12:00:00Z",
            }

    store.transaction(commit)
    after = snapshot(store.read())
    expected = (
        DecisionKind.COMPLETE
        if control == "drained"
        else (DecisionKind.HALT if control == "attention" else DecisionKind.PAUSE)
    )
    boundary = boundary_decision(after)
    assert boundary is not None
    assert boundary.kind == expected
    actual = _decision(before, after, _summary(driver, FailureClass.AUTHENTICATION))
    assert actual == boundary


@pytest.mark.parametrize("unreadable", ["missing", "error"])
def test_unreadable_state_halts_even_with_native_success(
    driver: AgentDriver, store: StateStore, unreadable: str
) -> None:
    before = snapshot(store.read())
    actual = _decision(
        before,
        None if unreadable == "missing" else before,
        _summary(driver),
        state_error="read failed" if unreadable == "error" else None,
    )
    assert actual.kind == DecisionKind.HALT


def test_repeated_decision_is_pure_and_does_not_claim_process_ownership(
    driver: AgentDriver, store: StateStore
) -> None:
    before = snapshot(store.read())
    summary = _summary(driver, FailureClass.CONNECTIVITY)
    original = repr((before, summary))
    now = datetime.now(UTC)
    first = _decision(before, before, summary, now=now)
    assert _decision(before, before, summary, now=now) == first
    assert first.kind == DecisionKind.WAIT
    assert repr((before, summary)) == original
    assert snapshot(store.read()) == before


def test_drained_required_capability_authority_is_shared(
    driver: AgentDriver, store: StateStore
) -> None:
    before = snapshot(store.read())
    after = replace(
        before,
        drained=True,
        next_phase="",
        completed_prds=1,
        capabilities={"audit": CapabilitySnapshot(True, "pending", None, None)},
    )
    actual = _decision(before, after, _summary(driver, FailureClass.PERMISSION))
    assert actual.kind == DecisionKind.RUN_CAPABILITY
    assert actual.capability == "audit"
    empty = _decision(
        before,
        replace(after, completed_prds=0),
        _summary(driver, FailureClass.PERMISSION),
    )
    assert empty.kind == DecisionKind.SKIP_CAPABILITIES
