from __future__ import annotations

import argparse
import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from ovcaq.cli import main
from ovcaq.state.commands import (
    GENERIC_WRITABLE_PREFIXES,
    MutationResult,
    StateService,
)
from ovcaq.state.schema import (
    AttemptEntry,
    AttemptOutcome,
    ResourceLimitError,
    State,
    TaskEntry,
    TaskStatus,
    new_state,
    validate_state,
)
from ovcaq.state.store import RevisionConflictError, StateStore

T0 = "2026-08-26T10:00:00Z"
T1 = "2026-08-26T10:01:00Z"
T2 = "2026-08-26T10:02:00Z"


def _directory_bytes(directory: Path) -> dict[str, bytes]:
    return {
        entry.name: entry.read_bytes()
        for entry in directory.iterdir()
        if entry.is_file()
    }


def _attempt(
    number: int,
    *,
    outcome: AttemptOutcome = "completed",
    started_at: str = T0,
    finished_at: str = T1,
) -> AttemptEntry:
    return {
        "number": number,
        "tier": "full",
        "driver": "codex",
        "outcome": outcome,
        "review_cycle": None,
        "cause": None,
        "pipeline": "lean",
        "cleanup_outcome": None,
        "started_at": started_at,
        "finished_at": finished_at,
        "commit_sha": None,
        "escalation": None,
        "metadata": {},
    }


def _task(
    task_id: int,
    name: str,
    *,
    status: TaskStatus = "pending",
    description: str = "",
    active_form: str = "",
    blocked_by: list[int] | None = None,
    tier: str | None = None,
    files_touched: int | None = None,
    public_contract_edit: bool | None = None,
    estimates: dict[str, int | None] | None = None,
    attempts: list[AttemptEntry] | None = None,
    metadata: dict[str, object] | None = None,
) -> TaskEntry:
    return {
        "id": task_id,
        "name": name,
        "description": description,
        "active_form": active_form,
        "status": status,
        "blocked_by": [] if blocked_by is None else blocked_by,
        "tier": tier,
        "files_touched": files_touched,
        "public_contract_edit": public_contract_edit,
        "estimates": (
            {"input_tokens": None, "context_peak": None}
            if estimates is None
            else estimates
        ),
        "attempts": [] if attempts is None else attempts,
        "metadata": {} if metadata is None else metadata,
    }


def _state_with_tasks(tmp_path: Path, tasks: list[TaskEntry]) -> State:
    state = new_state(repo_root=tmp_path)
    state["tasks"] = copy.deepcopy(tasks)
    state["work"]["tasks_total"] = len(state["tasks"])
    state["work"]["tasks_completed"] = sum(
        1 for task in state["tasks"] if task["status"] == "completed"
    )
    return state


def _store_for_state(tmp_path: Path, state: State | None = None) -> StateStore:
    store = StateStore(tmp_path / "state.json")
    store.initialize(new_state(repo_root=tmp_path) if state is None else state)
    return store


def _service_for_state(
    tmp_path: Path, state: State | None = None
) -> tuple[StateService, StateStore]:
    store = _store_for_state(tmp_path, state)
    return StateService(store), store


def _record_transactions(store: StateStore) -> Callable[[], tuple[int | None, ...]]:
    revisions: list[int | None] = []
    real_transaction = store.transaction

    def transaction(
        mutator: Any,
        *,
        expected_revision: int | None = None,
        publication_guard: Callable[[], None] | None = None,
    ) -> State:
        revisions.append(expected_revision)
        return real_transaction(
            mutator,
            expected_revision=expected_revision,
            publication_guard=publication_guard,
        )

    store.transaction = transaction
    return lambda: tuple(revisions)


def _service_with_transaction_spy(
    tmp_path: Path, state: State | None = None
) -> tuple[StateService, StateStore, Callable[[], tuple[int | None, ...]]]:
    store = _store_for_state(tmp_path, state)
    recorded_transactions = _record_transactions(store)
    return StateService(store), store, recorded_transactions


def _task_by_id(state: State, task_id: int) -> TaskEntry:
    matches = [task for task in state["tasks"] if task["id"] == task_id]
    assert len(matches) == 1
    return matches[0]


def _assert_result(
    result: MutationResult,
    *,
    revision: int,
    task_id: int | None,
) -> None:
    assert set(result) == {"revision", "task_id"}
    assert result == {"revision": revision, "task_id": task_id}


def test_generic_writable_prefixes_are_only_the_extension_containers() -> None:
    assert GENERIC_WRITABLE_PREFIXES == (
        ("work", "extensions"),
        ("review", "extensions"),
    )


def _service_with_namespaced_extensions(
    tmp_path: Path,
) -> tuple[StateService, StateStore, Callable[[], tuple[int | None, ...]]]:
    initial = new_state(repo_root=tmp_path)
    initial["work"]["extensions"]["acme/legacy"] = {
        "enabled": True,
        "obsolete": "remove me",
    }
    initial["work"]["extensions"]["acme/foo.bar"] = {"baseline": True}
    initial["review"]["extensions"]["vendor/reviewer"] = {"notes": ["first"]}
    return _service_with_transaction_spy(tmp_path, initial)


def test_generic_mutations_accept_namespaced_extension_descendants(
    tmp_path: Path,
) -> None:
    service, store, recorded_transactions = _service_with_namespaced_extensions(
        tmp_path
    )

    set_state = service.set(
        'work.extensions["acme/foo.bar"]["setting.with[brackets]"]',
        {"enabled": False, "samples": [3, 8]},
        expected_revision=0,
    )
    assert recorded_transactions() == (0,)
    assert set_state == store.read()
    assert set_state["work"]["extensions"]["acme/foo.bar"][
        "setting.with[brackets]"
    ] == {
        "enabled": False,
        "samples": [3, 8],
    }

    created_state = service.set(
        'work["extensions"]["acme/foo"].value',
        9,
        expected_revision=1,
    )
    assert recorded_transactions() == (0, 1)
    assert created_state == store.read()
    assert created_state["work"]["extensions"]["acme/foo"] == {"value": 9}

    append_state = service.append(
        'review["extensions"]["vendor/reviewer"].notes',
        "second",
        expected_revision=2,
    )
    assert recorded_transactions() == (0, 1, 2)
    assert append_state == store.read()
    assert append_state["review"]["extensions"]["vendor/reviewer"]["notes"] == [
        "first",
        "second",
    ]

    delete_state = service.delete(
        'work.extensions["acme/legacy"].obsolete',
        expected_revision=3,
    )
    assert recorded_transactions() == (0, 1, 2, 3)
    assert delete_state == store.read()
    assert delete_state["work"]["extensions"]["acme/legacy"] == {"enabled": True}
    assert validate_state(delete_state) == delete_state


@pytest.mark.parametrize("operation", ("set", "append"))
def test_generic_mutations_reject_deep_values_before_copying_or_transacting(
    tmp_path: Path,
    operation: str,
) -> None:
    service, _store, recorded_transactions = _service_with_namespaced_extensions(
        tmp_path
    )
    nested: object = None
    for _ in range(2_000):
        nested = [nested]

    with pytest.raises(ResourceLimitError, match="JSON nesting exceeds"):
        getattr(service, operation)(
            'work.extensions["tests/deep"]',
            nested,
        )

    assert recorded_transactions() == ()


@pytest.mark.parametrize(
    ("operation", "path", "value"),
    (
        pytest.param("set", "", {}, id="root"),
        pytest.param("set", "work", {}, id="work-ancestor"),
        pytest.param("delete", "review", None, id="review-ancestor"),
        pytest.param("set", "work.extensions", {}, id="work-container"),
        pytest.param("delete", "review.extensions", None, id="review-container"),
        pytest.param("set", "tasks[0].description", "changed", id="task-field"),
        pytest.param("set", "batch.id", "replacement", id="batch-identity"),
        pytest.param("append", "batch.capabilities", "extra", id="capabilities"),
        pytest.param("delete", "review.history", None, id="review-history"),
        pytest.param("set", "review.lenses", [], id="review-lenses"),
        pytest.param("set", "control.pause_requested", True, id="control"),
        pytest.param("delete", "recovery.last_error", None, id="recovery"),
        pytest.param(
            "set",
            'work["extensions.extra"]["acme/item"]',
            {},
            id="work-raw-prefix-lookalike",
        ),
        pytest.param(
            "append",
            'review["extensions[0]"]["acme/item"]',
            "entry",
            id="review-raw-prefix-lookalike",
        ),
    ),
)
def test_generic_mutations_protect_every_path_outside_strict_extension_descendants(
    tmp_path: Path,
    operation: str,
    path: str,
    value: object,
) -> None:
    initial = _state_with_tasks(tmp_path, [_task(4, "Protected")])
    store = _store_for_state(tmp_path, initial)
    store.transaction(lambda _state: None)
    service = StateService(store)
    before = _directory_bytes(tmp_path)
    before_state = copy.deepcopy(store.read())

    with pytest.raises(ValueError):
        if operation == "set":
            service.set(path, cast(Any, value), expected_revision=1)
        elif operation == "append":
            service.append(path, cast(Any, value), expected_revision=1)
        else:
            service.delete(path, expected_revision=1)

    assert store.read() == before_state
    assert _directory_bytes(tmp_path) == before


def test_unsafe_generic_mutations_recover_valid_core_fields(
    tmp_path: Path,
) -> None:
    initial = _state_with_tasks(
        tmp_path,
        [
            _task(
                7,
                "Recover core state",
                description="stale",
                metadata={"events": ["created"], "obsolete": True},
            )
        ],
    )
    service, store, recorded_transactions = _service_with_transaction_spy(
        tmp_path, initial
    )

    set_state = service.set(
        "tasks[0].description",
        "recovered",
        unsafe=True,
        expected_revision=0,
    )
    append_state = service.append(
        "tasks[0].metadata.events",
        "replayed",
        unsafe=True,
        expected_revision=1,
    )
    delete_state = service.delete(
        "tasks[0].metadata.obsolete",
        unsafe=True,
        expected_revision=2,
    )

    assert recorded_transactions() == (0, 1, 2)
    assert set_state["tasks"][0]["description"] == "recovered"
    assert append_state["tasks"][0]["metadata"]["events"] == [
        "created",
        "replayed",
    ]
    assert delete_state == store.read()
    assert delete_state["tasks"][0]["metadata"] == {"events": ["created", "replayed"]}
    assert validate_state(delete_state) == delete_state


@pytest.mark.parametrize(
    "operation",
    (
        pytest.param(
            lambda service: service.set(
                'work.extensions["missing-namespace"]',
                {"valid": "json"},
                expected_revision=1,
            ),
            id="invalid-extension-name",
        ),
        pytest.param(
            lambda service: service.set(
                'review.extensions["vendor/invalid"]',
                cast(Any, {1: "non-json-key"}),
                expected_revision=1,
            ),
            id="invalid-extension-data",
        ),
        pytest.param(
            lambda service: service.append(
                'review.extensions["vendor/missing"].items',
                "new",
                expected_revision=1,
            ),
            id="missing-append-target",
        ),
        pytest.param(
            lambda service: service.delete(
                'work.extensions["acme/missing"]',
                expected_revision=1,
            ),
            id="missing-delete-target",
        ),
        pytest.param(
            lambda service: service.set(
                "tasks[0].status",
                "running",
                unsafe=True,
                expected_revision=1,
            ),
            id="unsafe-schema-invalid",
        ),
        pytest.param(
            lambda service: service.set(
                'work.extensions["unterminated]',
                {},
                unsafe=True,
                expected_revision=1,
            ),
            id="unsafe-parse-invalid",
        ),
    ),
)
def test_invalid_generic_mutations_preserve_state_and_backup(
    tmp_path: Path,
    operation: Any,
) -> None:
    initial = _state_with_tasks(tmp_path, [_task(3, "Target")])
    store = _store_for_state(tmp_path, initial)
    store.transaction(lambda _state: None)
    service = StateService(store)
    before = _directory_bytes(tmp_path)
    before_state = copy.deepcopy(store.read())

    with pytest.raises(ValueError):
        operation(service)

    assert store.read() == before_state
    assert _directory_bytes(tmp_path) == before


def test_generic_mutation_revision_conflict_preserves_state_and_backup(
    tmp_path: Path,
) -> None:
    store = _store_for_state(tmp_path)
    store.transaction(lambda _state: None)
    recorded_transactions = _record_transactions(store)
    service = StateService(store)
    before = _directory_bytes(tmp_path)
    before_state = copy.deepcopy(store.read())

    with pytest.raises(RevisionConflictError):
        service.set(
            'work.extensions["acme/conflict"]',
            {"must": "not persist"},
            expected_revision=0,
        )

    assert recorded_transactions() == (0,)
    assert store.read() == before_state
    assert _directory_bytes(tmp_path) == before


ERROR_CODES = (
    "usage",
    "invalid_state",
    "state_io",
    "future_schema",
    "state_exists",
    "invalid_backup",
    "revision_conflict",
    "invalid_path",
    "protected_path",
    "durability_unsupported",
    "resource_limit",
    "oversized_plan",
    "runtime_format",
)


def _leaf_parsers(
    parser: argparse.ArgumentParser,
) -> list[argparse.ArgumentParser]:
    subparser_actions = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    if not subparser_actions:
        return [parser]
    assert len(subparser_actions) == 1
    parents = [parser] if not subparser_actions[0].required else []
    return parents + [
        leaf
        for child in subparser_actions[0].choices.values()
        for leaf in _leaf_parsers(child)
    ]


def _parser_command_inventory(parser: argparse.ArgumentParser) -> tuple[str, ...]:
    root_usage = " ".join(parser.format_usage().split()).removeprefix("usage: ")
    global_prefix = root_usage.partition(" {")[0].replace(" [-h]", "")
    return tuple(
        f"{global_prefix}{usage.removeprefix('ovcaq')}"
        for leaf in _leaf_parsers(parser)
        if (
            usage := " ".join(leaf.format_usage().split())
            .removeprefix("usage: ")
            .replace(" [-h]", "")
        )
    )


def _invoke_main(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str]:
    exit_code = main(argv)
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def _assert_json_failure(
    result: tuple[int, str, str],
    *,
    exit_code: int,
    error_code: str,
) -> None:
    actual_exit, stdout, stderr = result
    assert actual_exit == exit_code
    assert stdout == ""
    assert "Traceback" not in stderr
    payload = json.loads(stderr)
    assert set(payload) == {"ok", "error"}
    assert payload["ok"] is False
    assert set(payload["error"]) == {"code", "message", "path"}
    assert payload["error"]["code"] == error_code
    assert isinstance(payload["error"]["message"], str)
    assert payload["error"]["message"]
    assert payload["error"]["path"] is None


def _initialize_cli_root(
    root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    result = _invoke_main(["--root", str(root), "--json", "init"], capsys)
    assert result[0] == 0
    assert json.loads(result[1]) == {"ok": True, "revision": 0, "result": None}
    assert result[2] == ""


def _initialize_running_cli_task(
    root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _initialize_cli_root(root, capsys)
    task_payload = root / "valid-task.json"
    task_payload.write_text('{"name":"Payload target"}', encoding="utf-8")
    added = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "task",
            "add",
            str(task_payload),
        ],
        capsys,
    )
    assert added[0] == 0
    assert added[2] == ""
    started = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "task",
            "start",
            "1",
        ],
        capsys,
    )
    assert started[0] == 0
    assert started[2] == ""
