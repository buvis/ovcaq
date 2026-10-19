"""Closed deterministic workflow transition table."""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass

from ovcaq.state.schema import State
from ovcaq.state.store import StateStore
from ovcaq.workflow.records import require_recovery_idle, reset_prd_fields

type TransitionEffect = Callable[[State], State]
type TransitionKey = tuple[str, str]


@dataclass(frozen=True)
class TransitionRow:
    effect: TransitionEffect
    next_phase: str


class UnknownTransition(ValueError):
    """Raised when no transition row matches a phase and outcome."""


def _copy(state: State) -> State:
    return copy.deepcopy(state)


def _to_review(state: State) -> State:
    result = _copy(state)
    result["work"]["phase"] = "review"
    result["work"]["next_phase"] = "review"
    if result["review"]["cycle"] == 0:
        result["review"]["cycle"] = 1
    return result


def _rework(state: State) -> State:
    result = _copy(state)
    result["work"]["phase"] = "review"
    result["work"]["next_phase"] = "review"
    result["review"]["cycle"] += 1
    result["review"]["doubts"] = []
    result["review"]["rubric_verdicts"] = []
    result["review"]["rework_task_ids"] = []
    result["review"]["lenses"] = {}
    return result


def _converged(state: State) -> State:
    result = _copy(state)
    result["work"]["phase"] = "done"
    result["work"]["next_phase"] = "done"
    if "review" not in result["work"]["completed_phases"]:
        result["work"]["completed_phases"].append("review")
    return result


def _drained(state: State) -> State:
    result = _copy(state)
    result["work"]["phase"] = "done"
    result["work"]["next_phase"] = ""
    return result


TRANSITIONS: dict[TransitionKey, TransitionRow] = {
    ("build", "tasks_done"): TransitionRow(_to_review, "review"),
    ("review", "rework"): TransitionRow(_rework, "review"),
    ("review", "converged"): TransitionRow(_converged, "done"),
    ("done", "more_prds"): TransitionRow(reset_prd_fields, "build"),
    ("done", "drained"): TransitionRow(_drained, ""),
    ("build", "drained"): TransitionRow(_drained, ""),
}

OUTCOMES = tuple(sorted({outcome for _phase, outcome in TRANSITIONS}))


def apply(state: State, outcome: str) -> State:
    """Apply the sole effect set for ``(state.work.phase, outcome)``."""
    require_recovery_idle(state)
    phase = state["work"]["phase"]
    if phase == "done" and state["work"]["next_phase"] == "":
        raise UnknownTransition(
            f"no transition from drained state on outcome {outcome!r}"
        )
    row = TRANSITIONS.get((phase, outcome))
    if row is None:
        raise UnknownTransition(
            f"no transition from phase {phase!r} on outcome {outcome!r}"
        )
    return row.effect(state)


def next_phase(phase: str, outcome: str) -> str:
    """Return the target ``work.next_phase`` for a transition row."""
    try:
        return TRANSITIONS[(phase, outcome)].next_phase
    except KeyError as error:
        raise UnknownTransition(
            f"no transition from phase {phase!r} on outcome {outcome!r}"
        ) from error


def phase_complete(
    store: StateStore,
    outcome: str,
    *,
    expected_revision: int | None = None,
) -> State:
    """Apply one closed transition in one compare-and-set transaction."""
    return store.transaction(
        lambda state: apply(state, outcome),
        expected_revision=expected_revision,
    )
