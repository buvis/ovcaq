from __future__ import annotations

from datetime import timedelta

import pytest
from tests.runtime.test_decision import _NOW, _POLICY, _attempt, _decision, _state

from ovcaq.events.model import FailureClass
from ovcaq.runtime.decision import (
    DecisionKind,
    RetryState,
    progress_fingerprint,
    snapshot,
)


@pytest.mark.parametrize("repeats", [0, 2, 3])
@pytest.mark.parametrize(
    "failure", [FailureClass.PERMISSION, FailureClass.AUTHENTICATION]
)
def test_permission_and_authentication_halt_even_at_the_shared_repeat_limit(
    repeats: int, failure: FailureClass
) -> None:
    state = _state()
    state["recovery"].update(
        phase_fingerprint=progress_fingerprint(state), phase_repeats=repeats
    )
    before = snapshot(state)
    decision = _decision(before, _attempt(before, failure))
    assert decision.kind == DecisionKind.HALT
    assert decision.next_phase_repeats == repeats + 1
    assert decision.wait_seconds is None
    assert decision.capability is None


@pytest.mark.parametrize("repeats", [0, 2, 3])
@pytest.mark.parametrize(
    "failure,prd,retries",
    [
        (
            FailureClass.CONNECTIVITY,
            "00001-feature.md",
            RetryState(connectivity=_POLICY.connectivity_retries),
        ),
        (
            FailureClass.RATE_LIMIT,
            "00001-feature.md",
            RetryState(rate_limit=_POLICY.rate_limit_retries),
        ),
        (FailureClass.AGENT, None, RetryState(died=_POLICY.died_retries)),
    ],
    ids=["connectivity", "rate_limit", "bootstrap_death"],
)
def test_exhausted_class_budgets_keep_their_terminal_halt_at_shared_boundaries(
    repeats: int, failure: FailureClass, prd: str | None, retries: RetryState
) -> None:
    state = _state()
    state["work"]["prd"] = prd
    state["recovery"].update(
        phase_fingerprint=progress_fingerprint(state), phase_repeats=repeats
    )
    before = snapshot(state)
    result = _attempt(before, failure, reset_at=_NOW + timedelta(seconds=1))
    decision = _decision(before, result, retries)
    assert decision.kind == DecisionKind.HALT
    assert decision.next_phase_repeats == repeats + 1
    assert decision.wait_seconds is None
    assert decision.capability is None
