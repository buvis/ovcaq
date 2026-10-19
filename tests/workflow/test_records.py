from __future__ import annotations

import copy

import pytest

from ovcaq.state.schema import State, validate_state
from ovcaq.workflow.records import (
    CompletionError,
    complete_prd,
    completed_prd_summary,
    reset_prd_fields,
)


def _decision(identifier: str, status: str) -> dict[str, object]:
    return {
        "id": identifier,
        "kind": "test",
        "summary": identifier,
        "rationale": "characterized row",
        "cycle": 1,
        "created_at": "2026-08-30T12:04:00Z",
        "status": status,
    }


def _converge(state: State) -> None:
    state["work"]["phase"] = "done"
    state["work"]["next_phase"] = "done"
    state["work"]["completed_phases"] = ["review"]


def _populate_reset_owners(workflow_state: State) -> None:
    workflow_state["work"].update(
        {
            "phase": "done",
            "next_phase": "done",
            "completed_phases": ["review"],
            "work_start_sha": "abc123",
            "design_doc": "docs/dev/project-management/designs/example.md",
            "contract_card": "contract",
            "tasks_total": 2,
            "tasks_completed": 2,
            "extensions": {"workflow/hint": True},
        }
    )
    workflow_state["review"].update(
        {
            "cycle": 2,
            "decisions": [_decision("applied", "applied")],
            "rework_task_ids": [],
            "lenses": {"consensus": "completed"},
            "extensions": {"workflow/review": True},
        }
    )  # type: ignore[typeddict-item]
    workflow_state["control"]["attention"] = {
        "site": "review",
        "detail": "needs work",
        "created_at": "2026-08-30T12:05:00Z",
    }
    workflow_state["control"]["pause_requested"] = True
    workflow_state["recovery"]["replan_count"] = 2
    workflow_state["recovery"]["phase_fingerprint"] = "fingerprint"
    workflow_state["recovery"]["phase_repeats"] = 3


def test_reset_clears_exact_per_prd_owners_and_preserves_batch(
    workflow_state: State,
) -> None:
    _populate_reset_owners(workflow_state)
    batch_before = copy.deepcopy(workflow_state["batch"])
    root_before = workflow_state["work"]["repo_root"]
    prd_before = workflow_state["work"]["prd"]
    cap_before = workflow_state["review"]["cap"]

    result = reset_prd_fields(workflow_state)

    assert result["batch"] == batch_before
    assert result["work"] == {
        "prd": prd_before,
        "phase": "build",
        "next_phase": "build",
        "completed_phases": [],
        "work_start_sha": None,
        "repo_root": root_before,
        "design_doc": None,
        "contract_card": None,
        "tasks_total": 0,
        "tasks_completed": 0,
        "extensions": {},
    }
    assert result["tasks"] == []
    assert result["review"] == {
        "cycle": 0,
        "cap": cap_before,
        "cycles": [],
        "decisions": [],
        "doubts": [],
        "rubric_verdicts": [],
        "rework_task_ids": [],
        "lenses": {},
        "extensions": {},
    }
    assert result["control"] == {
        "pause_requested": True,
        "pause_reason": None,
        "attention": None,
    }
    assert result["recovery"] == {
        "operation": None,
        "replan_count": 0,
        "phase_fingerprint": None,
        "phase_repeats": 0,
    }
    validate_state(result)


def test_reset_is_pure(workflow_state: State) -> None:
    before = copy.deepcopy(workflow_state)
    reset_prd_fields(workflow_state)
    assert workflow_state == before


def test_completed_prd_summary_uses_v1_decision_statuses(workflow_state: State) -> None:
    workflow_state["review"]["cycle"] = 2
    workflow_state["review"]["decisions"] = [
        _decision("a", "applied"),
        _decision("b", "applied"),
        _decision("d", "deferred"),
        _decision("e", "escalated"),
    ]  # type: ignore[typeddict-item]
    workflow_state["work"]["tasks_completed"] = 5
    workflow_state["work"]["tasks_total"] = 7

    assert completed_prd_summary(workflow_state) == {
        "filename": "00004-workflow-core-v1.md",
        "cycles": 2,
        "autonomous_decisions": 2,
        "escalated_decisions": 1,
        "tasks_completed": 5,
        "tasks_total": 7,
    }


def test_completed_prd_summary_defaults_zero_cycle_to_first_cycle(
    workflow_state: State,
) -> None:
    assert completed_prd_summary(workflow_state)["cycles"] == 1


def test_complete_prd_appends_summary_and_resets_park_counter(
    workflow_state: State,
) -> None:
    _converge(workflow_state)
    workflow_state["batch"]["parks_consecutive"] = 2

    result = complete_prd(workflow_state, "00004-workflow-core-v1.md")

    assert result["batch"]["completed_prds"] == [completed_prd_summary(workflow_state)]
    assert result["batch"]["parks_consecutive"] == 0
    validate_state(result)


def test_complete_prd_is_idempotent_for_the_same_summary(workflow_state: State) -> None:
    _converge(workflow_state)
    once = complete_prd(workflow_state, "00004-workflow-core-v1.md")
    twice = complete_prd(once, "00004-workflow-core-v1.md")

    assert twice["batch"]["completed_prds"] == once["batch"]["completed_prds"]


def test_complete_prd_rejects_mismatched_active_prd(workflow_state: State) -> None:
    _converge(workflow_state)
    with pytest.raises(CompletionError, match="does not match"):
        complete_prd(workflow_state, "00005-runtime.md")


@pytest.mark.parametrize("phase", ("build", "review"))
def test_complete_prd_rejects_nonterminal_workflow_state(
    workflow_state: State,
    phase: str,
) -> None:
    workflow_state["work"]["phase"] = phase  # type: ignore[typeddict-item]
    before = copy.deepcopy(workflow_state)

    with pytest.raises(CompletionError, match="terminal converged state"):
        complete_prd(workflow_state, "00004-workflow-core-v1.md")

    assert workflow_state == before


def test_complete_prd_rejects_done_without_convergence_marker(
    workflow_state: State,
) -> None:
    workflow_state["work"]["phase"] = "done"
    workflow_state["work"]["next_phase"] = ""

    with pytest.raises(CompletionError, match="terminal converged state"):
        complete_prd(workflow_state, "00004-workflow-core-v1.md")


def test_complete_prd_rejects_conflicting_existing_summary(
    workflow_state: State,
) -> None:
    _converge(workflow_state)
    workflow_state["batch"]["completed_prds"].append(
        {
            **completed_prd_summary(workflow_state),
            "tasks_total": 99,
        }
    )

    with pytest.raises(CompletionError, match="conflicting"):
        complete_prd(workflow_state, "00004-workflow-core-v1.md")


def test_complete_prd_is_pure(workflow_state: State) -> None:
    _converge(workflow_state)
    before = copy.deepcopy(workflow_state)
    complete_prd(workflow_state, "00004-workflow-core-v1.md")
    assert workflow_state == before
