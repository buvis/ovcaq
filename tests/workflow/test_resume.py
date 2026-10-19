from __future__ import annotations

import copy

import pytest

from ovcaq.state.schema import State
from ovcaq.workflow.resume import resume_target


def test_recovery_operation_outranks_every_phase_branch(workflow_state: State) -> None:
    workflow_state["work"]["phase"] = "review"
    workflow_state["recovery"]["operation"] = {
        "id": "op-77af3",
        "kind": "stall",
        "step": "intent",
        "prd": "00004-workflow-core-v1.md",
        "site": "design_gate",
        "detail": "hook failed",
        "source": "docs/dev/project-management/prds/wip/00004-workflow-core-v1.md",
        "destination": "docs/dev/project-management/prds/hold/00004-workflow-core-v1.md",
        "artifact": None,
        "created_at": "2026-08-30T12:01:00Z",
    }

    assert (
        resume_target(workflow_state)
        == "reconcile stall op-77af3 for 00004-workflow-core-v1.md"
    )


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        pytest.param(
            ["completed", "pending"],
            "continue build at first non-completed task 2",
            id="first-pending",
        ),
        pytest.param(
            ["completed", "in_progress", "pending"],
            "continue build at first non-completed task 2",
            id="in-progress",
        ),
        pytest.param(
            ["completed", "completed"],
            "all tasks done -> review gate",
            id="all-done",
        ),
    ],
)
def test_build_resume_rows(
    workflow_state: State,
    statuses: list[str],
    expected: str,
) -> None:
    workflow_state["tasks"] = [
        {
            "id": index,
            "name": f"task {index}",
            "description": "",
            "active_form": "working",
            "status": status,
            "blocked_by": [],
            "tier": None,
            "files_touched": None,
            "public_contract_edit": None,
            "estimates": {"input_tokens": None, "context_peak": None},
            "attempts": [],
            "metadata": {},
        }
        for index, status in enumerate(statuses, start=1)
    ]  # type: ignore[typeddict-item]

    assert resume_target(workflow_state) == expected


def test_empty_build_uses_committed_catchup_artifact(workflow_state: State) -> None:
    assert resume_target(workflow_state) == "build: catchup then planning"

    workflow_state["batch"]["catchup"] = {
        "completed_at": "2026-08-30T12:02:00Z",
        "head_sha": "abc123",
    }
    assert resume_target(workflow_state) == "skip catchup -> planning"


@pytest.mark.parametrize(
    ("completed", "cycle", "expected"),
    [
        pytest.param([], 0, "run review loop at cycle 1", id="first-cycle"),
        pytest.param([], 2, "run review loop at cycle 2", id="later-cycle"),
        pytest.param(["review"], 2, "skip review -> done", id="converged"),
    ],
)
def test_review_resume_rows(
    workflow_state: State,
    completed: list[str],
    cycle: int,
    expected: str,
) -> None:
    workflow_state["work"]["phase"] = "review"
    workflow_state["work"]["completed_phases"] = completed  # type: ignore[typeddict-item]
    workflow_state["review"]["cycle"] = cycle

    assert resume_target(workflow_state) == expected


@pytest.mark.parametrize(
    ("pause_site", "expected"),
    [
        pytest.param(
            "review_cap",
            "cap-pause resume handler: present unresolved findings, branch resume/abandon",
            id="review-cap",
        ),
        pytest.param("operator", "paused: await user", id="operator"),
        pytest.param(None, "paused: await user", id="no-reason"),
    ],
)
def test_paused_resume_rows(
    workflow_state: State,
    pause_site: str | None,
    expected: str,
) -> None:
    workflow_state["work"]["phase"] = "paused"
    if pause_site is not None:
        workflow_state["control"]["pause_reason"] = {
            "site": pause_site,
            "detail": "paused",
            "created_at": "2026-08-30T12:03:00Z",
        }

    assert resume_target(workflow_state) == expected


def test_done_resume_is_terminal_for_the_prd(workflow_state: State) -> None:
    workflow_state["work"]["phase"] = "done"
    assert resume_target(workflow_state) == "done"


def test_resume_target_is_pure(workflow_state: State) -> None:
    before = copy.deepcopy(workflow_state)
    resume_target(workflow_state)
    assert workflow_state == before
