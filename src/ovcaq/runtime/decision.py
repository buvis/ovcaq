"""Pure post-session decisions derived from committed workflow progress."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from ovcaq.events.model import FailureClass, SessionSummary
from ovcaq.state.schema import (
    BatchStatus,
    CapabilityStatus,
    NextPhase,
    Notice,
    Phase,
    RecoveryOperation,
    State,
)


class DecisionKind(StrEnum):
    PAUSE = "pause"
    RUN_CAPABILITY = "run_capability"
    SKIP_CAPABILITIES = "skip_capabilities"
    COMPLETE = "complete"
    CONTINUE = "continue"
    WAIT = "wait"
    RETRY = "retry"
    PARK = "park"
    HALT = "halt"


@dataclass(frozen=True, slots=True)
class SupervisorPolicy:
    died_retries: int
    connectivity_retries: int
    rate_limit_retries: int
    connectivity_wait_seconds: float
    rate_limit_wait_seconds: float
    phase_repeat_limit: int


@dataclass(frozen=True, slots=True)
class CapabilitySnapshot:
    required: bool
    status: CapabilityStatus
    latest_attempt_id: str | None
    latest_session_id: str | None


@dataclass(frozen=True, slots=True)
class ProgressSnapshot:
    revision: int
    batch_id: str
    batch_status: BatchStatus
    prd: str | None
    phase: Phase
    next_phase: NextPhase
    pause_requested: bool
    pause_reason: Notice | None
    attention: Notice | None
    recovery_operation: RecoveryOperation | None
    tasks_completed: int
    review_cycle: int
    completed_prds: int
    drained: bool
    capabilities: Mapping[str, CapabilitySnapshot]
    phase_fingerprint: str | None
    phase_repeats: int


@dataclass(frozen=True, slots=True)
class AttemptResult:
    summary: SessionSummary
    started_at: datetime
    finished_at: datetime
    state_after: ProgressSnapshot | None
    state_error: str | None


@dataclass(frozen=True, slots=True)
class RetryState:
    died: int = 0
    connectivity: int = 0
    rate_limit: int = 0


@dataclass(frozen=True, slots=True)
class SupervisorDecision:
    kind: DecisionKind
    reason: str
    wait_seconds: float | None = None
    capability: str | None = None
    next_phase_repeats: int | None = None


def snapshot(state: State) -> ProgressSnapshot:
    """Capture committed fields without retaining mutable state references."""
    capabilities = {}
    for name, capability in state["batch"]["capabilities"].items():
        latest = capability["attempts"][-1] if capability["attempts"] else None
        capabilities[name] = CapabilitySnapshot(
            required=capability["required"],
            status=capability["status"],
            latest_attempt_id=latest["id"] if latest else None,
            latest_session_id=latest["session_id"] if latest else None,
        )
    return ProgressSnapshot(
        revision=state["revision"],
        batch_id=state["batch"]["id"],
        batch_status=state["batch"]["status"],
        prd=state["work"]["prd"],
        phase=state["work"]["phase"],
        next_phase=state["work"]["next_phase"],
        pause_requested=state["control"]["pause_requested"],
        pause_reason=deepcopy(state["control"]["pause_reason"]),
        attention=deepcopy(state["control"]["attention"]),
        recovery_operation=deepcopy(state["recovery"]["operation"]),
        tasks_completed=state["work"]["tasks_completed"],
        review_cycle=state["review"]["cycle"],
        completed_prds=len(state["batch"]["completed_prds"]),
        drained=state["work"]["next_phase"] == "",
        capabilities=capabilities,
        phase_fingerprint=state["recovery"]["phase_fingerprint"],
        phase_repeats=state["recovery"]["phase_repeats"],
    )


def _fingerprint(progress: ProgressSnapshot) -> str:
    return json.dumps(
        {
            "prd": progress.prd,
            "phase": progress.phase,
            "next_phase": progress.next_phase,
            "tasks_completed": progress.tasks_completed,
            "review_cycle": progress.review_cycle,
            "completed_prds": progress.completed_prds,
            "capabilities": {
                name: [
                    capability.status,
                    capability.latest_attempt_id,
                    capability.latest_session_id,
                ]
                for name, capability in progress.capabilities.items()
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def progress_fingerprint(state: State) -> str:
    """Serialize workflow progress canonically, excluding bookkeeping."""
    return _fingerprint(snapshot(state))


def _capability_decision(after: ProgressSnapshot) -> SupervisorDecision | None:
    pending = sorted(
        name
        for name, capability in after.capabilities.items()
        if capability.required and capability.status == "pending"
    )
    if pending:
        if after.completed_prds == 0:
            return SupervisorDecision(
                DecisionKind.SKIP_CAPABILITIES,
                "No completed work needs capabilities",
            )
        return SupervisorDecision(
            DecisionKind.RUN_CAPABILITY,
            "Required capability is pending",
            capability=pending[0],
        )
    if any(
        capability.required and capability.status == "failed"
        for capability in after.capabilities.values()
    ):
        return SupervisorDecision(DecisionKind.HALT, "Required capability failed")
    if any(
        capability.status == "running" for capability in after.capabilities.values()
    ):
        return SupervisorDecision(DecisionKind.HALT, "Capability is still running")
    return None


def _failure_decision(
    result: AttemptResult,
    retries: RetryState,
    policy: SupervisorPolicy,
    now: datetime,
    prd: str | None,
) -> SupervisorDecision | None:
    failure = result.summary.failure_class
    if failure == FailureClass.RATE_LIMIT:
        reset = result.summary.rate_limit_reset_at
        if (
            retries.rate_limit < policy.rate_limit_retries
            and reset is not None
            and reset.utcoffset() is not None
        ):
            delay = (reset - now).total_seconds()
            if 0 < delay <= policy.rate_limit_wait_seconds:
                return SupervisorDecision(
                    DecisionKind.WAIT,
                    "Waiting for rate-limit reset",
                    wait_seconds=delay,
                )
        return SupervisorDecision(
            DecisionKind.HALT, "No bounded rate-limit retry remains"
        )
    if failure == FailureClass.CONNECTIVITY:
        if retries.connectivity < policy.connectivity_retries:
            return SupervisorDecision(
                DecisionKind.WAIT,
                "Waiting to retry connectivity",
                wait_seconds=policy.connectivity_wait_seconds,
            )
        return SupervisorDecision(DecisionKind.HALT, "Connectivity retries exhausted")
    if failure in {FailureClass.PERMISSION, FailureClass.AUTHENTICATION}:
        return SupervisorDecision(DecisionKind.HALT, "Session requires operator access")
    if not result.summary.success:
        if retries.died < policy.died_retries:
            return SupervisorDecision(
                DecisionKind.RETRY, "Retrying unsuccessful session"
            )
        return SupervisorDecision(
            DecisionKind.PARK if prd else DecisionKind.HALT,
            "Unsuccessful session retries exhausted",
        )
    return None


def boundary_decision(after: ProgressSnapshot) -> SupervisorDecision | None:
    """Apply committed controls before launching work or completing a drain."""
    if after.pause_requested or after.phase == "paused" or after.next_phase == "paused":
        return SupervisorDecision(DecisionKind.PAUSE, "Workflow is paused")
    if after.attention is not None:
        return SupervisorDecision(DecisionKind.HALT, "Workflow needs attention")
    if after.drained:
        return _capability_decision(after) or SupervisorDecision(
            DecisionKind.COMPLETE, "Workflow and capabilities ended"
        )
    return None


def decide(
    before: ProgressSnapshot,
    result: AttemptResult,
    retries: RetryState,
    policy: SupervisorPolicy,
    *,
    now: datetime,
) -> SupervisorDecision:
    """Choose one action in precedence order without performing side effects."""
    after = result.state_after
    if after is None or result.state_error is not None:
        return SupervisorDecision(DecisionKind.HALT, "Post-session state is unreadable")
    boundary = boundary_decision(after)
    if boundary is not None:
        return boundary

    if _fingerprint(before) != _fingerprint(after):
        return SupervisorDecision(
            DecisionKind.CONTINUE,
            "Committed workflow progress",
            next_phase_repeats=0,
        )
    repeats = (
        before.phase_repeats if before.phase_fingerprint == _fingerprint(before) else 0
    ) + 1
    failure_decision = _failure_decision(result, retries, policy, now, after.prd)
    if failure_decision is not None and (
        failure_decision.kind == DecisionKind.HALT
        or repeats < policy.phase_repeat_limit
    ):
        return replace(failure_decision, next_phase_repeats=repeats)
    if repeats < policy.phase_repeat_limit:
        kind = DecisionKind.RETRY
    else:
        kind = (
            DecisionKind.PARK
            if after.prd
            else (DecisionKind.PAUSE if result.summary.success else DecisionKind.HALT)
        )
    return SupervisorDecision(
        kind, "Session made no workflow progress", next_phase_repeats=repeats
    )
