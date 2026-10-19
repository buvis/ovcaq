from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from ovcaq.state.schema import State, TaskEntry, new_state
from ovcaq.workflow.resume import resume_target

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "claude"


def _v1_from_legacy_fixture(path: Path, repo_root: Path) -> State:
    legacy = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    state = new_state(repo_root=repo_root)
    batch = cast(dict[str, object], legacy["batch"])
    state["batch"].update(
        {
            "id": cast(str, batch["id"]),
            "status": "running",
            "started_at": "2026-08-30T12:00:00Z",
        }
    )
    state["work"].update(
        {
            "prd": cast(str, legacy["prd"]),
            "phase": cast(str, legacy["phase"]),
            "next_phase": cast(str, legacy["next_phase"]),
            "completed_phases": cast(list[str], legacy["phases_completed"]),
            "tasks_total": cast(int, legacy["tasks_total"]),
            "tasks_completed": cast(int, legacy["tasks_completed"]),
        }
    )  # type: ignore[typeddict-item]
    state["review"]["cycle"] = cast(int, legacy["cycle"])
    state["review"]["cap"] = cast(int, legacy["rework_cap"])
    legacy_tasks = cast(list[dict[str, object]], legacy["tasks"])
    state["tasks"] = [
        cast(
            TaskEntry,
            {
                "id": index,
                "name": task["name"],
                "description": "",
                "active_form": "working",
                "status": task["status"],
                "blocked_by": [],
                "tier": None,
                "files_touched": None,
                "public_contract_edit": None,
                "estimates": {"input_tokens": None, "context_peak": None},
                "attempts": [],
                "metadata": {},
            },
        )
        for index, task in enumerate(legacy_tasks, start=1)
    ]
    return state


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        pytest.param(
            "legacy-state-build.json",
            "continue build at first non-completed task 2",
            id="build-pending",
        ),
        pytest.param(
            "legacy-state-review.json",
            "run review loop at cycle 2",
            id="review-cycle-two",
        ),
        pytest.param(
            "legacy-state-converged.json",
            "skip review -> done",
            id="review-converged",
        ),
    ],
)
def test_characterized_lifecycle_fixture_resume_outcomes_match_under_v1(
    tmp_path: Path,
    fixture: str,
    expected: str,
) -> None:
    state = _v1_from_legacy_fixture(FIXTURES / fixture, tmp_path)
    assert resume_target(state) == expected
