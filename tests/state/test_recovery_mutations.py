from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from test_commands import (
    _attempt,
    _directory_bytes,
    _state_with_tasks,
    _store_for_state,
    _task,
)

from ovcaq.state.commands import StateMutationConflictError, StateService


@pytest.mark.parametrize(
    "mutation",
    (
        pytest.param(
            lambda service: service.add_task({"name": "blocked"}, expected_revision=0),
            id="task-add",
        ),
        pytest.param(
            lambda service: service.start_task(1, expected_revision=0),
            id="task-start",
        ),
        pytest.param(
            lambda service: service.append_attempt(1, _attempt(1), expected_revision=0),
            id="task-attempt",
        ),
        pytest.param(
            lambda service: service.complete_task(1, _attempt(1), expected_revision=0),
            id="task-complete",
        ),
        pytest.param(
            lambda service: service.set_task_body(1, "blocked", expected_revision=0),
            id="task-body",
        ),
        pytest.param(
            lambda service: service.set_task_meta(
                1, {"metadata": {"blocked": True}}, expected_revision=0
            ),
            id="task-meta",
        ),
        pytest.param(
            lambda service: service.set_task_status(
                1, "completed", expected_revision=0
            ),
            id="task-status",
        ),
        pytest.param(
            lambda service: service.clear_tasks(expected_revision=0),
            id="task-clear",
        ),
        pytest.param(
            lambda service: service.set_contract_card("blocked", expected_revision=0),
            id="contract",
        ),
        pytest.param(
            lambda service: service.set(
                'work.extensions["tests/recovery"].value',
                2,
                expected_revision=0,
            ),
            id="generic-set",
        ),
        pytest.param(
            lambda service: service.append(
                'work.extensions["tests/recovery"].items',
                "blocked",
                expected_revision=0,
            ),
            id="generic-append",
        ),
        pytest.param(
            lambda service: service.delete(
                'work.extensions["tests/recovery"].value',
                expected_revision=0,
            ),
            id="generic-delete",
        ),
        pytest.param(
            lambda service: service.restore(expected_revision=0),
            id="restore",
        ),
    ),
)
def test_every_public_state_mutation_rejects_active_recovery_atomically(
    tmp_path: Path,
    mutation: Callable[[StateService], object],
) -> None:
    initial = _state_with_tasks(tmp_path, [_task(1, "Original")])
    initial["work"]["extensions"]["tests/recovery"] = {
        "value": 1,
        "items": ["original"],
    }
    initial["recovery"]["operation"] = {
        "id": "active-recovery",
        "kind": "stall",
        "step": "intent",
        "prd": "00004-workflow-core-v1.md",
        "site": "design_gate",
        "detail": "approval missing",
        "source": str(tmp_path / "wip/00004-workflow-core-v1.md"),
        "destination": str(tmp_path / "hold/00004-workflow-core-v1.md"),
        "artifact": None,
        "created_at": "2026-08-26T10:00:00Z",
    }
    store = _store_for_state(tmp_path, initial)
    service = StateService(store)
    before = _directory_bytes(tmp_path)

    with pytest.raises(StateMutationConflictError, match="active-recovery"):
        mutation(service)

    assert store.read() == initial
    assert _directory_bytes(tmp_path) == before
