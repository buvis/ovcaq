from __future__ import annotations

from pathlib import Path
from typing import get_type_hints

from test_commands import (
    _service_with_transaction_spy,
    _state_with_tasks,
    _task,
)

from ovcaq.state.commands import (
    MutationResult,
    TaskCreate,
    TaskMetaPatch,
)


def test_command_typed_dicts_expose_only_the_documented_fields() -> None:
    assert set(get_type_hints(TaskCreate)) == {
        "id",
        "name",
        "description",
        "active_form",
        "blocked_by",
        "tier",
        "files_touched",
        "public_contract_edit",
        "estimates",
        "metadata",
    }
    assert TaskCreate.__required_keys__ == frozenset({"name"})
    assert TaskCreate.__optional_keys__ == frozenset(
        {
            "id",
            "description",
            "active_form",
            "blocked_by",
            "tier",
            "files_touched",
            "public_contract_edit",
            "estimates",
            "metadata",
        }
    )
    assert set(get_type_hints(TaskMetaPatch)) == {
        "tier",
        "files_touched",
        "public_contract_edit",
        "estimates",
        "metadata",
    }
    assert TaskMetaPatch.__required_keys__ == frozenset()
    assert TaskMetaPatch.__optional_keys__ == frozenset(
        {
            "tier",
            "files_touched",
            "public_contract_edit",
            "estimates",
            "metadata",
        }
    )
    assert set(get_type_hints(MutationResult)) == {"revision", "task_id"}
    assert MutationResult.__required_keys__ == frozenset({"revision", "task_id"})
    assert MutationResult.__optional_keys__ == frozenset()


def test_show_validate_and_get_read_from_the_backing_state_file(
    tmp_path: Path,
) -> None:
    initial = _state_with_tasks(
        tmp_path,
        [
            _task(
                7,
                "Build commands",
                description="Initial body",
                metadata={"owner.name": "Tess"},
            ),
            _task(12, "Inspect paths", description="Final body", active_form="Last"),
        ],
    )
    initial["work"]["extensions"]["acme/foo.bar"] = {
        "enabled": True,
        "items": ["first", "last"],
    }
    service, _store, recorded_transactions = _service_with_transaction_spy(
        tmp_path, initial
    )

    shown = service.show()

    assert shown == initial
    assert service.validate() == initial
    assert service.get("tasks[0].description") == "Initial body"
    assert service.get("tasks[-1].active_form") == "Last"
    assert service.get('tasks[0].metadata["owner.name"]') == "Tess"
    assert service.get('work.extensions["acme/foo.bar"].items[-1]') == "last"
    assert recorded_transactions() == ()
