from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from tests.runtime.test_decision import (
    _NOTICE,
    _NOW,
    _POLICY,
    _attempt,
    _decision,
    _state,
)

from ovcaq.events.model import FailureClass
from ovcaq.runtime.decision import (
    CapabilitySnapshot,
    DecisionKind,
    progress_fingerprint,
    snapshot,
)


@pytest.mark.parametrize(
    "failure",
    [None, FailureClass.AGENT, FailureClass.CONNECTIVITY, FailureClass.RATE_LIMIT],
)
@pytest.mark.parametrize(
    "limit,repeats",
    [
        (3, 0),
        (3, 1),
        (3, 2),
        (1, 0),
        (2, 0),
        (2, 1),
        (4, 2),
        (4, 3),
        (7, 5),
        (7, 6),
        (3, 99),
    ],
)
def test_unchanged_attempts_share_the_persisted_phase_limit(
    failure: FailureClass | None, limit: int, repeats: int
) -> None:
    state = _state()
    state["recovery"].update(
        phase_fingerprint=progress_fingerprint(state), phase_repeats=repeats
    )
    before = snapshot(state)
    after = replace(before, revision=before.revision + 7)
    result = _attempt(after, failure, reset_at=_NOW + timedelta(seconds=1))
    decision = _decision(
        before, result, policy=replace(_POLICY, phase_repeat_limit=limit)
    )
    assert decision.next_phase_repeats == repeats + 1
    if repeats + 1 >= limit:
        assert decision.kind in {DecisionKind.PARK, DecisionKind.HALT}
        assert decision.wait_seconds is None
    else:
        expected = (
            DecisionKind.WAIT
            if failure in {FailureClass.CONNECTIVITY, FailureClass.RATE_LIMIT}
            else DecisionKind.RETRY
        )
        assert decision.kind == expected


@pytest.mark.parametrize(
    "failure",
    [None, FailureClass.AGENT, FailureClass.CONNECTIVITY, FailureClass.RATE_LIMIT],
)
@pytest.mark.parametrize("repeats", [99, 1, 2, 3])
def test_stale_fingerprint_does_not_charge_old_repeats_to_current_work(
    failure: FailureClass | None,
    repeats: int,
) -> None:
    state = _state()
    stale = progress_fingerprint(state)
    state["work"]["next_phase"] = "review"
    state["recovery"].update(phase_fingerprint=stale, phase_repeats=repeats)
    before = snapshot(state)
    result = _attempt(before, failure, reset_at=_NOW + timedelta(seconds=1))
    decision = _decision(before, result)
    assert decision.kind in {DecisionKind.RETRY, DecisionKind.WAIT}
    assert decision.next_phase_repeats == 1


@pytest.mark.parametrize("completed_prds,pending", [(0, True), (1, True), (1, False)])
@pytest.mark.parametrize("site", ["review_cap", "operator-check"])
def test_post_session_attention_blocks_capabilities_and_terminal_drain(
    completed_prds: int, pending: bool, site: str
) -> None:
    before = snapshot(_state())
    after = replace(
        before,
        next_phase="",
        drained=True,
        completed_prds=completed_prds,
        attention={**_NOTICE, "site": site},
        capabilities={"audit": CapabilitySnapshot(True, "pending", None, None)}
        if pending
        else {},
    )
    decision = _decision(before, _attempt(after))
    assert decision.kind == DecisionKind.HALT
    assert decision.capability is None
    assert decision.wait_seconds is None
