"""Pure task-plan validation and size policy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

LOOP_TASK_CEILING: Final[int] = 15


class InvalidPlan(ValueError):
    """Raised when a task snapshot is not a valid dependency plan."""


def plan_over_ceiling(
    state: Mapping[str, object],
    ceiling: int = LOOP_TASK_CEILING,
) -> tuple[bool, int]:
    """Return the characterized tolerant plan-size decision."""
    tasks = state.get("tasks")
    count = len(tasks) if isinstance(tasks, list) else 0
    return count > ceiling, count


def _task_id(task: Mapping[str, object], index: int) -> int:
    task_id = task.get("id")
    if type(task_id) is not int or task_id < 1:
        raise InvalidPlan(f"tasks[{index}].id must be a positive integer")
    return task_id


def validate_plan_shape(state: Mapping[str, object]) -> int:
    """Validate task objects, references, and dependency acyclicity."""
    raw_tasks = state.get("tasks", [])
    if not isinstance(raw_tasks, list):
        raise InvalidPlan("tasks must be a list")

    dependencies: dict[int, tuple[int, ...]] = {}
    for index, raw_task in enumerate(raw_tasks):
        if not isinstance(raw_task, dict):
            raise InvalidPlan(f"tasks[{index}] must be an object")
        task = cast(dict[str, object], raw_task)
        task_id = _task_id(task, index)
        if task_id in dependencies:
            raise InvalidPlan(f"duplicate task id: {task_id}")
        raw_blockers = task.get("blocked_by", [])
        if not isinstance(raw_blockers, list):
            raise InvalidPlan(f"tasks[{index}].blocked_by must be a list")
        blockers: list[int] = []
        for blocker in raw_blockers:
            if type(blocker) is not int or blocker < 1:
                raise InvalidPlan(
                    f"tasks[{index}].blocked_by entries must be positive integers"
                )
            blockers.append(blocker)
        dependencies[task_id] = tuple(blockers)

    known_ids = set(dependencies)
    for task_id, dependency_ids in dependencies.items():
        unknown = [blocker for blocker in dependency_ids if blocker not in known_ids]
        if unknown:
            raise InvalidPlan(f"task {task_id} references unknown blockers: {unknown}")

    visiting: set[int] = set()
    visited: set[int] = set()

    def visit(task_id: int) -> None:
        if task_id in visiting:
            raise InvalidPlan(f"task dependency cycle includes {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for blocker in dependencies[task_id]:
            visit(blocker)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in dependencies:
        visit(task_id)
    return len(raw_tasks)
