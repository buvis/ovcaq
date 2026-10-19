from __future__ import annotations

import pytest

from ovcaq.workflow.policy import (
    LOOP_TASK_CEILING,
    InvalidPlan,
    plan_over_ceiling,
    validate_plan_shape,
)


def _tasks(count: int) -> list[dict[str, object]]:
    return [
        {"id": index, "status": "pending", "blocked_by": []}
        for index in range(1, count + 1)
    ]


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        pytest.param(14, False, id="under"),
        pytest.param(15, False, id="at"),
        pytest.param(16, True, id="over"),
    ],
)
def test_plan_ceiling_rows(count: int, expected: bool) -> None:
    assert plan_over_ceiling({"tasks": _tasks(count)}) == (expected, count)


def test_plan_ceiling_is_fifteen_and_can_be_overridden() -> None:
    assert LOOP_TASK_CEILING == 15
    assert plan_over_ceiling({"tasks": _tasks(16)}, ceiling=20) == (False, 16)


@pytest.mark.parametrize("state", [{}, {"tasks": "not-a-list"}])
def test_tolerant_characterized_counting_treats_missing_or_non_list_as_zero(
    state: dict[str, object],
) -> None:
    assert plan_over_ceiling(state) == (False, 0)


def test_validate_plan_shape_accepts_an_acyclic_dependency_graph() -> None:
    tasks = _tasks(3)
    tasks[1]["blocked_by"] = [1]
    tasks[2]["blocked_by"] = [1, 2]

    assert validate_plan_shape({"tasks": tasks}) == 3


@pytest.mark.parametrize(
    "tasks",
    [
        pytest.param("not-a-list", id="not-list"),
        pytest.param(["not-an-object"], id="entry-not-object"),
        pytest.param(
            [{"id": 1, "status": "pending", "blocked_by": [2]}],
            id="unknown-blocker",
        ),
        pytest.param(
            [{"id": 1, "status": "pending", "blocked_by": [1]}],
            id="self-cycle",
        ),
        pytest.param(
            [
                {"id": 1, "status": "pending", "blocked_by": [2]},
                {"id": 2, "status": "pending", "blocked_by": [1]},
            ],
            id="dependency-cycle",
        ),
    ],
)
def test_validate_plan_shape_rejects_invalid_rows(tasks: object) -> None:
    with pytest.raises(InvalidPlan):
        validate_plan_shape({"tasks": tasks})
