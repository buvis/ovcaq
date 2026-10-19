from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from test_commands import (
    T1,
    T2,
    _assert_result,
    _attempt,
    _directory_bytes,
    _record_transactions,
    _service_with_transaction_spy,
    _state_with_tasks,
    _store_for_state,
    _task,
    _task_by_id,
)

from ovcaq.state.commands import (
    StateService,
    TaskCreate,
    TaskMetaPatch,
)
from ovcaq.state.schema import (
    AttemptEntry,
    State,
    TaskEntry,
    TaskStatus,
    validate_state,
)
from ovcaq.state.store import BackupError, RevisionConflictError, StateStore


class _TaskIdEqualityAlias:
    def __eq__(self, other: object) -> bool:
        return other == 1

    def __repr__(self) -> str:
        return "task-id-equality-alias"


class _TaskIdSubclass(int):
    pass


@pytest.mark.parametrize(
    ("existing_tasks", "new_name", "expected_task_id"),
    (
        pytest.param(
            [
                _task(9, "Already done", status="completed"),
                _task(3, "Still waiting"),
            ],
            "New task",
            10,
            id="unordered-existing-ids",
        ),
        pytest.param(
            [
                _task(41, "Middle identifier", status="completed"),
                _task(17, "Lowest identifier"),
                _task(29, "Inserted before maximum"),
            ],
            "Contract check",
            42,
            id="maximum-id-is-first",
        ),
    ),
)
def test_add_task_allocates_after_the_maximum_id_and_applies_defaults(
    tmp_path: Path,
    existing_tasks: list[TaskEntry],
    new_name: str,
    expected_task_id: int,
) -> None:
    initial = _state_with_tasks(tmp_path, existing_tasks)
    service, store, recorded_transactions = _service_with_transaction_spy(
        tmp_path, initial
    )

    result = service.add_task({"name": new_name}, expected_revision=0)

    _assert_result(result, revision=1, task_id=expected_task_id)
    assert recorded_transactions() == (0,)
    committed = store.read()
    assert committed["work"]["tasks_total"] == len(existing_tasks) + 1
    assert committed["work"]["tasks_completed"] == sum(
        1 for task in existing_tasks if task["status"] == "completed"
    )
    assert _task_by_id(committed, expected_task_id) == {
        "id": expected_task_id,
        "name": new_name,
        "description": "",
        "active_form": "",
        "status": "pending",
        "blocked_by": [],
        "tier": None,
        "files_touched": None,
        "public_contract_edit": None,
        "estimates": {"input_tokens": None, "context_peak": None},
        "attempts": [],
        "metadata": {},
    }


def test_add_task_persists_supplied_task_fields_without_reusing_positions(
    tmp_path: Path,
) -> None:
    service, store, recorded_transactions = _service_with_transaction_spy(tmp_path)
    payload: TaskCreate = {
        "name": "Full task",
        "description": "Body",
        "active_form": "Working form",
        "blocked_by": [],
        "tier": "lean",
        "files_touched": 2,
        "public_contract_edit": False,
        "estimates": {"input_tokens": 100, "context_peak": 200},
        "metadata": {"owner": "tess", "nested": [1, {"ok": True}]},
    }

    result = service.add_task(payload, expected_revision=0)

    _assert_result(result, revision=1, task_id=1)
    assert recorded_transactions() == (0,)
    task = store.read()["tasks"][0]
    assert task == {
        "id": 1,
        "status": "pending",
        "attempts": [],
        **payload,
    }


def test_add_task_preserves_a_supplied_task_id(tmp_path: Path) -> None:
    service, store, recorded_transactions = _service_with_transaction_spy(tmp_path)
    payload: TaskCreate = {"id": 27, "name": "Recorded repair"}

    result = service.add_task(payload, expected_revision=0)

    _assert_result(result, revision=1, task_id=27)
    assert recorded_transactions() == (0,)
    assert store.read()["tasks"][0]["id"] == 27


def test_add_task_rejects_a_duplicate_supplied_task_id_without_durable_change(
    tmp_path: Path,
) -> None:
    initial = _state_with_tasks(tmp_path, [_task(27, "Existing task")])
    service, store, recorded_transactions = _service_with_transaction_spy(
        tmp_path, initial
    )
    before = _directory_bytes(tmp_path)

    with pytest.raises(ValueError):
        service.add_task({"id": 27, "name": "Duplicate task"}, expected_revision=0)

    assert recorded_transactions() == (0,)
    assert store.read() == initial
    assert _directory_bytes(tmp_path) == before


def _assert_start_and_body_mutations(
    service: StateService,
    store: StateStore,
    recorded_transactions: Callable[[], tuple[int | None, ...]],
    tasks: list[TaskEntry],
    meta_task_id: int,
    target_task_id: int,
    replacement_body: str,
) -> None:
    started = service.start_task(target_task_id, expected_revision=0)
    _assert_result(started, revision=1, task_id=target_task_id)
    assert recorded_transactions() == (0,)
    state = store.read()
    assert [task["id"] for task in state["tasks"]] == [task["id"] for task in tasks]
    assert _task_by_id(state, target_task_id)["status"] == "in_progress"
    assert _task_by_id(state, meta_task_id)["status"] == "completed"
    assert state["work"]["tasks_total"] == 2
    assert state["work"]["tasks_completed"] == 1

    body = service.set_task_body(target_task_id, replacement_body, expected_revision=1)
    _assert_result(body, revision=2, task_id=target_task_id)
    assert recorded_transactions() == (0, 1)
    state = store.read()
    assert _task_by_id(state, target_task_id)["description"] == replacement_body
    assert _task_by_id(state, target_task_id)["active_form"] == ""
    assert state["work"]["tasks_total"] == 2
    assert state["work"]["tasks_completed"] == 1


def _assert_metadata_mutations(
    service: StateService,
    store: StateStore,
    recorded_transactions: Callable[[], tuple[int | None, ...]],
    meta_task_id: int,
    patch: TaskMetaPatch,
    partial_metadata: dict[str, object],
) -> None:
    patched = service.set_task_meta(
        meta_task_id,
        patch,
        expected_revision=2,
    )
    _assert_result(patched, revision=3, task_id=meta_task_id)
    assert recorded_transactions() == (0, 1, 2)
    state = store.read()
    edited = _task_by_id(state, meta_task_id)
    assert edited["tier"] == patch["tier"]
    assert edited["files_touched"] == patch["files_touched"]
    assert edited["public_contract_edit"] == patch["public_contract_edit"]
    assert edited["estimates"] == patch["estimates"]
    assert edited["metadata"] == patch["metadata"]

    partial = service.set_task_meta(
        meta_task_id, {"metadata": partial_metadata}, expected_revision=3
    )
    _assert_result(partial, revision=4, task_id=meta_task_id)
    assert recorded_transactions() == (0, 1, 2, 3)
    state = store.read()
    edited = _task_by_id(state, meta_task_id)
    assert edited["tier"] == patch["tier"]
    assert edited["files_touched"] == patch["files_touched"]
    assert edited["public_contract_edit"] == patch["public_contract_edit"]
    assert edited["estimates"] == patch["estimates"]
    assert edited["metadata"] == partial_metadata


def _assert_status_and_contract_mutations(
    service: StateService,
    store: StateStore,
    recorded_transactions: Callable[[], tuple[int | None, ...]],
    target_task_id: int,
    contract_text: str,
    stored_contract: str,
) -> None:
    status = service.set_task_status(target_task_id, "completed", expected_revision=4)
    _assert_result(status, revision=5, task_id=target_task_id)
    assert recorded_transactions() == (0, 1, 2, 3, 4)
    state = store.read()
    assert _task_by_id(state, target_task_id)["status"] == "completed"
    assert state["work"]["tasks_total"] == 2
    assert state["work"]["tasks_completed"] == 2

    card = service.set_contract_card(contract_text, expected_revision=5)
    _assert_result(card, revision=6, task_id=None)
    assert recorded_transactions() == (0, 1, 2, 3, 4, 5)
    state = store.read()
    assert state["work"]["contract_card"] == stored_contract
    assert state["work"]["tasks_total"] == 2
    assert state["work"]["tasks_completed"] == 2


@pytest.mark.parametrize(
    (
        "tasks",
        "meta_task_id",
        "target_task_id",
        "replacement_body",
        "patch",
        "partial_metadata",
        "contract_text",
        "stored_contract",
    ),
    (
        pytest.param(
            [
                _task(
                    4,
                    "Completed first",
                    status="completed",
                    tier="lean",
                    files_touched=1,
                    public_contract_edit=False,
                    estimates={"input_tokens": 10, "context_peak": 20},
                    metadata={"keep": True},
                ),
                _task(8, "Pending second", blocked_by=[4]),
            ],
            4,
            8,
            "Replacement body\n",
            {
                "tier": "full",
                "files_touched": 3,
                "public_contract_edit": True,
                "estimates": {"input_tokens": 111, "context_peak": None},
                "metadata": {"new": ["value"]},
            },
            {"only": True},
            "keep trailing spaces  \n\n",
            "keep trailing spaces  ",
            id="ascending-target-last",
        ),
        pytest.param(
            [
                _task(31, "Queue review", blocked_by=[12]),
                _task(
                    12,
                    "Closed bootstrap",
                    status="completed",
                    tier="minimal",
                    files_touched=4,
                    public_contract_edit=None,
                    estimates={"input_tokens": 33, "context_peak": 44},
                    metadata={"old": "value"},
                ),
            ],
            12,
            31,
            "Second replacement body\n\n",
            {
                "tier": None,
                "files_touched": 5,
                "public_contract_edit": False,
                "estimates": {"input_tokens": None, "context_peak": 555},
                "metadata": {"reviewer": "tess", "round": 2},
            },
            {"only": "second"},
            "second contract\n",
            "second contract",
            id="target-first-higher-id",
        ),
    ),
)
def test_start_body_meta_status_and_contract_mutations_each_use_one_transaction(
    tmp_path: Path,
    tasks: list[TaskEntry],
    meta_task_id: int,
    target_task_id: int,
    replacement_body: str,
    patch: TaskMetaPatch,
    partial_metadata: dict[str, object],
    contract_text: str,
    stored_contract: str,
) -> None:
    service, store, recorded_transactions = _service_with_transaction_spy(
        tmp_path, _state_with_tasks(tmp_path, tasks)
    )
    _assert_start_and_body_mutations(
        service,
        store,
        recorded_transactions,
        tasks,
        meta_task_id,
        target_task_id,
        replacement_body,
    )
    _assert_metadata_mutations(
        service, store, recorded_transactions, meta_task_id, patch, partial_metadata
    )
    _assert_status_and_contract_mutations(
        service,
        store,
        recorded_transactions,
        target_task_id,
        contract_text,
        stored_contract,
    )


@pytest.mark.parametrize(
    ("tasks", "target_task_id", "append_attempt", "complete_attempt"),
    (
        pytest.param(
            [
                _task(2, "Finished", status="completed"),
                _task(
                    5,
                    "Running",
                    status="in_progress",
                    attempts=[_attempt(1, outcome="aborted")],
                ),
            ],
            5,
            _attempt(2, outcome="review_flagged", started_at=T1, finished_at=T2),
            _attempt(3, outcome="completed", started_at=T2, finished_at=T2),
            id="target-last",
        ),
        pytest.param(
            [
                _task(
                    21,
                    "Retry focused branch",
                    status="in_progress",
                    attempts=[_attempt(1, outcome="escalated")],
                ),
                _task(13, "Earlier completed work", status="completed"),
            ],
            21,
            _attempt(2, outcome="rework_failed", started_at=T1, finished_at=T2),
            _attempt(3, outcome="completed", started_at=T2, finished_at=T2),
            id="target-first",
        ),
    ),
)
def test_append_attempt_keeps_status_and_complete_task_appends_then_completes(
    tmp_path: Path,
    tasks: list[TaskEntry],
    target_task_id: int,
    append_attempt: AttemptEntry,
    complete_attempt: AttemptEntry,
) -> None:
    initial = _state_with_tasks(tmp_path, tasks)
    service, store, recorded_transactions = _service_with_transaction_spy(
        tmp_path, initial
    )

    appended = service.append_attempt(
        target_task_id,
        append_attempt,
        expected_revision=0,
    )

    _assert_result(appended, revision=1, task_id=target_task_id)
    assert recorded_transactions() == (0,)
    state = store.read()
    running = _task_by_id(state, target_task_id)
    assert running["status"] == "in_progress"
    assert [attempt["number"] for attempt in running["attempts"]] == [1, 2]
    assert running["attempts"][1]["outcome"] == append_attempt["outcome"]
    assert state["work"]["tasks_total"] == 2
    assert state["work"]["tasks_completed"] == 1

    completed = service.complete_task(
        target_task_id,
        complete_attempt,
        expected_revision=1,
    )

    _assert_result(completed, revision=2, task_id=target_task_id)
    assert recorded_transactions() == (0, 1)
    state = store.read()
    running = _task_by_id(state, target_task_id)
    assert running["status"] == "completed"
    assert [attempt["number"] for attempt in running["attempts"]] == [1, 2, 3]
    assert running["attempts"][2]["outcome"] == complete_attempt["outcome"]
    assert state["work"]["tasks_total"] == 2
    assert state["work"]["tasks_completed"] == 2


def test_clear_tasks_clears_dependent_rework_ids_and_preserves_valid_state(
    tmp_path: Path,
) -> None:
    initial = _state_with_tasks(
        tmp_path,
        [
            _task(2, "Done", status="completed"),
            _task(5, "Pending", blocked_by=[2]),
        ],
    )
    initial["review"]["rework_task_ids"] = [5]
    service, store, recorded_transactions = _service_with_transaction_spy(
        tmp_path, initial
    )

    result = service.clear_tasks(expected_revision=0)

    _assert_result(result, revision=1, task_id=None)
    assert recorded_transactions() == (0,)
    committed = store.read()
    assert committed["tasks"] == []
    assert committed["work"]["tasks_total"] == 0
    assert committed["work"]["tasks_completed"] == 0
    assert committed["review"]["rework_task_ids"] == []
    assert validate_state(committed) == committed


def test_expected_revision_conflict_leaves_state_and_backup_unchanged(
    tmp_path: Path,
) -> None:
    store = _store_for_state(tmp_path)
    store.transaction(lambda _state: None)
    recorded_transactions = _record_transactions(store)
    service = StateService(store)
    before = _directory_bytes(tmp_path)

    with pytest.raises(RevisionConflictError):
        service.add_task({"name": "Must not persist"}, expected_revision=0)

    assert recorded_transactions() == (0,)
    assert _directory_bytes(tmp_path) == before


def test_restore_delegates_to_store_and_returns_committed_revision(
    tmp_path: Path,
) -> None:
    store = _store_for_state(tmp_path)
    store.transaction(lambda state: state["work"].__setitem__("prd", "current.md"))
    service = StateService(store)
    restore_calls: list[int | None] = []
    real_restore = store.restore

    def recording_restore(
        *,
        expected_revision: int | None = None,
        precondition: Callable[[State], None] | None = None,
    ) -> State:
        restore_calls.append(expected_revision)
        return real_restore(
            expected_revision=expected_revision,
            precondition=precondition,
        )

    store.restore = recording_restore  # type: ignore[method-assign]

    result = service.restore(expected_revision=1)

    assert restore_calls == [1]
    _assert_result(result, revision=2, task_id=None)
    assert store.read()["work"]["prd"] is None


def test_restore_revision_conflict_preserves_public_error_and_durable_bytes(
    tmp_path: Path,
) -> None:
    store = _store_for_state(tmp_path)
    store.transaction(lambda state: state["work"].__setitem__("prd", "current.md"))
    before = _directory_bytes(tmp_path)

    with pytest.raises(RevisionConflictError):
        StateService(store).restore(expected_revision=0)

    assert _directory_bytes(tmp_path) == before


def test_restore_backup_failure_preserves_public_error_and_durable_bytes(
    tmp_path: Path,
) -> None:
    store = _store_for_state(tmp_path)
    before = _directory_bytes(tmp_path)

    with pytest.raises(BackupError):
        StateService(store).restore(expected_revision=0)

    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize(
    "operation",
    (
        pytest.param(
            lambda service: service.start_task(1, expected_revision=1),
            id="start",
        ),
        pytest.param(
            lambda service: service.append_attempt(1, _attempt(1), expected_revision=1),
            id="append-attempt",
        ),
        pytest.param(
            lambda service: service.complete_task(1, _attempt(1), expected_revision=1),
            id="complete",
        ),
        pytest.param(
            lambda service: service.set_task_body(1, "body", expected_revision=1),
            id="body",
        ),
        pytest.param(
            lambda service: service.set_task_meta(
                1, {"metadata": {"changed": True}}, expected_revision=1
            ),
            id="meta",
        ),
        pytest.param(
            lambda service: service.set_task_status(
                1, "completed", expected_revision=1
            ),
            id="status",
        ),
    ),
)
def test_task_mutations_reject_missing_ids_without_position_fallback(
    tmp_path: Path,
    operation: Any,
) -> None:
    initial = _state_with_tasks(tmp_path, [_task(7, "The only task")])
    store = _store_for_state(tmp_path, initial)
    store.transaction(lambda _state: None)
    recorded_transactions = _record_transactions(store)
    service = StateService(store)
    before = _directory_bytes(tmp_path)

    with pytest.raises(ValueError):
        operation(service)

    assert recorded_transactions() == (1,)
    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize(
    "operation",
    (
        pytest.param(
            lambda service, task_id: service.add_task(
                cast(TaskCreate, {"id": task_id, "name": "Aliased task"}),
                expected_revision=1,
            ),
            id="add",
        ),
        pytest.param(
            lambda service, task_id: service.start_task(
                cast(int, task_id), expected_revision=1
            ),
            id="start",
        ),
        pytest.param(
            lambda service, task_id: service.append_attempt(
                cast(int, task_id), _attempt(1), expected_revision=1
            ),
            id="append-attempt",
        ),
        pytest.param(
            lambda service, task_id: service.complete_task(
                cast(int, task_id), _attempt(1), expected_revision=1
            ),
            id="complete",
        ),
        pytest.param(
            lambda service, task_id: service.set_task_body(
                cast(int, task_id), "body", expected_revision=1
            ),
            id="body",
        ),
        pytest.param(
            lambda service, task_id: service.set_task_meta(
                cast(int, task_id),
                {"metadata": {"changed": True}},
                expected_revision=1,
            ),
            id="meta",
        ),
        pytest.param(
            lambda service, task_id: service.set_task_status(
                cast(int, task_id), "completed", expected_revision=1
            ),
            id="status",
        ),
    ),
)
@pytest.mark.parametrize(
    "task_id",
    (
        pytest.param(True, id="boolean"),
        pytest.param(1.0, id="float"),
        pytest.param(_TaskIdSubclass(1), id="integer-subclass"),
        pytest.param(_TaskIdEqualityAlias(), id="equality-alias"),
    ),
)
def test_compound_service_rejects_aliased_task_ids_before_transacting(
    tmp_path: Path,
    operation: Any,
    task_id: object,
) -> None:
    initial = _state_with_tasks(tmp_path, [_task(1, "Target")])
    store = _store_for_state(tmp_path, initial)
    store.transaction(lambda _state: None)
    recorded_transactions = _record_transactions(store)
    service = StateService(store)
    before = _directory_bytes(tmp_path)

    with pytest.raises(ValueError, match="task id must be an integer"):
        operation(service, task_id)

    assert recorded_transactions() == ()
    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize(
    "task_id",
    (
        pytest.param(True, id="boolean"),
        pytest.param(1.0, id="float"),
        pytest.param(_TaskIdSubclass(1), id="integer-subclass"),
        pytest.param(_TaskIdEqualityAlias(), id="equality-alias"),
    ),
)
def test_add_task_rejects_aliased_blocker_ids_before_transacting(
    tmp_path: Path,
    task_id: object,
) -> None:
    initial = _state_with_tasks(tmp_path, [_task(1, "Blocker")])
    store = _store_for_state(tmp_path, initial)
    store.transaction(lambda _state: None)
    recorded_transactions = _record_transactions(store)
    service = StateService(store)
    before = _directory_bytes(tmp_path)
    payload = cast(TaskCreate, {"name": "Blocked", "blocked_by": [task_id]})

    with pytest.raises(ValueError, match="task id must be an integer"):
        service.add_task(payload, expected_revision=1)

    assert recorded_transactions() == ()
    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize(
    "payload",
    (
        pytest.param({}, id="missing-name"),
        pytest.param({"name": ""}, id="empty-name"),
    ),
)
def test_add_task_rejects_missing_or_empty_name_without_durable_change(
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    service, store, recorded_transactions = _service_with_transaction_spy(tmp_path)
    before = _directory_bytes(tmp_path)

    with pytest.raises(ValueError):
        service.add_task(cast(TaskCreate, payload), expected_revision=0)

    assert recorded_transactions() == (0,)
    assert store.read()["tasks"] == []
    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize(
    "operation",
    (
        pytest.param(
            lambda service: service.append_attempt(3, _attempt(2), expected_revision=1),
            id="attempt-number-gap",
        ),
        pytest.param(
            lambda service: service.complete_task(3, _attempt(2), expected_revision=1),
            id="complete-attempt-number-gap",
        ),
        pytest.param(
            lambda service: service.append_attempt(
                3,
                cast(AttemptEntry, {**_attempt(1), "outcome": "running"}),
                expected_revision=1,
            ),
            id="attempt-schema",
        ),
        pytest.param(
            lambda service: service.set_task_status(
                3, cast(TaskStatus, "running"), expected_revision=1
            ),
            id="status",
        ),
        pytest.param(
            lambda service: service.set_task_meta(
                3,
                cast(TaskMetaPatch, {"metadata": {"changed": True}, "name": "bad"}),
                expected_revision=1,
            ),
            id="meta-key",
        ),
    ),
)
def test_invalid_task_mutations_leave_state_and_backup_unchanged(
    tmp_path: Path,
    operation: Any,
) -> None:
    initial = _state_with_tasks(tmp_path, [_task(3, "Target")])
    store = _store_for_state(tmp_path, initial)
    store.transaction(lambda _state: None)
    recorded_transactions = _record_transactions(store)
    service = StateService(store)
    before = _directory_bytes(tmp_path)
    before_state = copy.deepcopy(store.read())

    with pytest.raises(ValueError):
        operation(service)

    assert recorded_transactions() == (1,)
    assert store.read() == before_state
    assert _directory_bytes(tmp_path) == before
