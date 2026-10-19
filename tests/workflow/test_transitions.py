from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ovcaq.state.schema import State, validate_state
from ovcaq.state.store import StateStore
from ovcaq.workflow import records, transitions

TRANSITION_ROWS = [
    pytest.param("build", "tasks_done", "review", "review", id="build-review"),
    pytest.param("review", "rework", "review", "review", id="review-rework"),
    pytest.param("review", "converged", "done", "done", id="review-done"),
    pytest.param("done", "more_prds", "build", "build", id="done-next"),
    pytest.param("done", "drained", "done", "", id="done-drained"),
    pytest.param("build", "drained", "done", "", id="empty-drained"),
]


@pytest.mark.parametrize("outcome", (*transitions.OUTCOMES, "unknown"))
def test_drained_state_rejects_every_transition_without_mutation(
    workflow_state: State, tmp_path: Path, outcome: str
) -> None:
    drained = transitions.apply(workflow_state, "drained")
    store = StateStore(tmp_path / "state.json")
    store.initialize(drained)
    before = store.path.read_bytes()

    with pytest.raises(transitions.UnknownTransition):
        transitions.apply(drained, outcome)
    with pytest.raises(transitions.UnknownTransition):
        transitions.phase_complete(store, outcome)

    assert store.path.read_bytes() == before
    assert drained["work"]["phase"] == "done"
    assert drained["work"]["next_phase"] == ""


@pytest.mark.parametrize(
    ("phase", "outcome", "expected_phase", "expected_next"),
    TRANSITION_ROWS,
)
def test_every_transition_row_lands_with_valid_full_effects(
    workflow_state: State,
    phase: str,
    outcome: str,
    expected_phase: str,
    expected_next: str,
) -> None:
    workflow_state["work"]["phase"] = phase  # type: ignore[typeddict-item]
    workflow_state["work"]["next_phase"] = phase  # type: ignore[typeddict-item]
    if phase == "review":
        workflow_state["review"]["cycle"] = 1

    result = transitions.apply(workflow_state, outcome)

    assert result["work"]["phase"] == expected_phase
    assert result["work"]["next_phase"] == expected_next
    validate_state(result)


def test_build_to_review_starts_first_cycle_and_preserves_tasks(
    workflow_state: State,
) -> None:
    tasks = workflow_state["tasks"]
    result = transitions.apply(workflow_state, "tasks_done")

    assert result["review"]["cycle"] == 1
    assert result["work"]["completed_phases"] == []
    assert result["tasks"] == tasks


def _populate_review_history(workflow_state: State) -> None:
    workflow_state["work"]["phase"] = "review"
    workflow_state["work"]["next_phase"] = "review"
    workflow_state["review"]["cycle"] = 2
    workflow_state["review"]["cycles"] = [
        {
            "cycle": 2,
            "review_file": "review-02.md",
            "reviewers": {"alice": "passed"},
            "issues_found": 1,
            "follow_up_tasks": 1,
            "deferred": 0,
            "recurring_issues": [],
            "decision_gate": None,
            "rework_commits": [],
            "rework_notes": [],
            "fix_audit": [],
            "test_run": None,
        }
    ]
    workflow_state["review"]["decisions"] = [
        {
            "id": "decision-1",
            "kind": "scope",
            "summary": "keep scope",
            "rationale": "durable review history",
            "cycle": 2,
            "created_at": "2026-09-01T10:00:00Z",
            "status": "applied",
        }
    ]


def _populate_cycle_work(workflow_state: State) -> None:
    workflow_state["review"]["doubts"] = [
        {
            "id": "doubt-1",
            "description": "cycle-local doubt",
            "category": "fix",
            "justification": None,
            "status": "pending",
            "source": "bob",
        }
    ]
    workflow_state["review"]["rubric_verdicts"] = [
        {"rule_id": "R1", "verdict": "fail", "source": "bob"}
    ]
    workflow_state["tasks"] = [
        {
            "id": 1,
            "name": "rework",
            "description": "fix review findings",
            "active_form": "fixing review findings",
            "status": "pending",
            "blocked_by": [],
            "tier": None,
            "files_touched": None,
            "public_contract_edit": None,
            "estimates": {"input_tokens": None, "context_peak": None},
            "attempts": [],
            "metadata": {},
        }
    ]
    workflow_state["work"]["tasks_total"] = 1
    workflow_state["review"]["rework_task_ids"] = [1]
    workflow_state["review"]["lenses"] = {
        "alice": "completed",
        "blake": "failed",
    }
    workflow_state["review"]["extensions"] = {"workflow/review": True}


def test_rework_increments_cycle_and_clears_all_cycle_local_review_state(
    workflow_state: State,
) -> None:
    _populate_review_history(workflow_state)
    _populate_cycle_work(workflow_state)
    cycles = copy.deepcopy(workflow_state["review"]["cycles"])
    decisions = copy.deepcopy(workflow_state["review"]["decisions"])
    extensions = copy.deepcopy(workflow_state["review"]["extensions"])
    batch = copy.deepcopy(workflow_state["batch"])

    result = transitions.apply(workflow_state, "rework")

    assert result["review"]["cycle"] == 3
    assert result["review"]["cycles"] == cycles
    assert result["review"]["decisions"] == decisions
    assert result["review"]["doubts"] == []
    assert result["review"]["rubric_verdicts"] == []
    assert result["review"]["rework_task_ids"] == []
    assert result["review"]["lenses"] == {}
    assert result["review"]["extensions"] == extensions
    assert result["batch"] == batch
    assert result["work"]["completed_phases"] == []
    validate_state(result)


def test_convergence_adds_review_marker_idempotently(workflow_state: State) -> None:
    workflow_state["work"]["phase"] = "review"
    workflow_state["work"]["next_phase"] = "review"
    workflow_state["review"]["cycle"] = 1

    once = transitions.apply(workflow_state, "converged")
    once["work"]["phase"] = "review"
    twice = transitions.apply(once, "converged")

    assert twice["work"]["completed_phases"] == ["review"]


def test_more_prds_delegates_to_authoritative_reset(workflow_state: State) -> None:
    workflow_state["work"]["phase"] = "done"
    workflow_state["work"]["next_phase"] = "done"

    assert transitions.apply(workflow_state, "more_prds") == records.reset_prd_fields(
        workflow_state
    )


REJECTED_TRANSITION_ROWS = [
    pytest.param("build", "converged", id="build-converged"),
    pytest.param("build", "more_prds", id="build-more-prds"),
    pytest.param("build", "rework", id="build-rework"),
    pytest.param("review", "drained", id="review-drained"),
    pytest.param("review", "more_prds", id="review-more-prds"),
    pytest.param("review", "tasks_done", id="review-tasks-done"),
    pytest.param("done", "converged", id="done-converged"),
    pytest.param("done", "rework", id="done-rework"),
    pytest.param("done", "tasks_done", id="done-tasks-done"),
    pytest.param("paused", "converged", id="paused-converged"),
    pytest.param("paused", "drained", id="paused-drained"),
    pytest.param("paused", "more_prds", id="paused-more-prds"),
    pytest.param("paused", "rework", id="paused-rework"),
    pytest.param("paused", "tasks_done", id="paused-tasks-done"),
    pytest.param("unknown", "tasks_done", id="unknown-phase"),
    pytest.param("review", "sideways", id="unknown-outcome"),
]


@pytest.mark.parametrize(("phase", "outcome"), REJECTED_TRANSITION_ROWS)
def test_unknown_transition_rows_fail_closed(
    workflow_state: State,
    phase: str,
    outcome: str,
) -> None:
    workflow_state["work"]["phase"] = phase  # type: ignore[typeddict-item]

    with pytest.raises(transitions.UnknownTransition, match=phase):
        transitions.apply(workflow_state, outcome)

    with pytest.raises(transitions.UnknownTransition, match=phase):
        transitions.next_phase(phase, outcome)


def test_every_transition_is_pure(workflow_state: State) -> None:
    for phase, outcome in transitions.TRANSITIONS:
        candidate = copy.deepcopy(workflow_state)
        candidate["work"]["phase"] = phase
        if phase == "review":
            candidate["review"]["cycle"] = 1
        before = copy.deepcopy(candidate)

        transitions.apply(candidate, outcome)

        assert candidate == before


def test_next_phase_agrees_with_applied_full_effect(
    workflow_state: State,
) -> None:
    for phase, outcome in transitions.TRANSITIONS:
        candidate = copy.deepcopy(workflow_state)
        candidate["work"]["phase"] = phase
        candidate["work"]["next_phase"] = phase
        if phase == "review":
            candidate["review"]["cycle"] = 1

        applied = transitions.apply(candidate, outcome)

        assert transitions.next_phase(phase, outcome) == applied["work"]["next_phase"]
