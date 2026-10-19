from __future__ import annotations

import json
import shlex
from pathlib import Path

import pytest
from test_commands import (
    _assert_json_failure,
    _initialize_cli_root,
    _invoke_main,
    _parser_command_inventory,
)

import ovcaq.cli_io as cli_module
import ovcaq.state.store as store_module
from ovcaq.cli import build_parser, render_state_protocol_command_inventory
from ovcaq.state.schema import MAX_CONTRACT_CARD_BYTES, MAX_STATE_BYTES, new_state


def _deep_json_array(depth: int) -> str:
    return "[" * depth + "null" + "]" * depth


def _state_bytes_with_deep_json(root: Path) -> bytes:
    marker = "deep-json-placeholder"
    state = new_state(repo_root=root)
    state["work"]["extensions"] = {"tests/deep": marker}
    encoded = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
    replaced = encoded.replace(
        json.dumps(marker).encode(),
        _deep_json_array(2_000).encode(),
    )
    assert replaced != encoded
    assert len(replaced) < MAX_STATE_BYTES
    return replaced


def _state_bytes_with_oversized_integer(root: Path) -> bytes:
    state = new_state(repo_root=root)
    encoded = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
    replaced = encoded.replace(
        b'"revision": 0,',
        b'"revision": ' + b"9" * 5_000 + b",",
        1,
    )
    assert replaced != encoded
    assert len(replaced) < MAX_STATE_BYTES
    return replaced


def _state_bytes_with_nonstandard_constant(root: Path, constant: str) -> bytes:
    marker = "non-standard-number-placeholder"
    state = new_state(repo_root=root)
    state["work"]["extensions"] = {"tests/non-standard-number": marker}
    encoded = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
    replaced = encoded.replace(json.dumps(marker).encode(), constant.encode())
    assert replaced != encoded
    return replaced


def _assert_nonstandard_constant_message(result: tuple[int, str, str]) -> None:
    error = json.loads(result[2])["error"]
    assert "non-standard JSON constant" in error["message"]


@pytest.mark.parametrize("constant", ("NaN", "Infinity", "-Infinity"))
def test_nonstandard_inline_json_is_usage_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    constant: str,
) -> None:
    root = tmp_path / "constant-inline-root"
    _initialize_cli_root(root, capsys)
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    before = {path.name: path.read_bytes() for path in runtime.iterdir()}

    result = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            'work.extensions["tests/non-standard-number"]',
            f'{{"value":{constant}}}',
        ],
        capsys,
    )

    _assert_json_failure(result, exit_code=1, error_code="usage")
    _assert_nonstandard_constant_message(result)
    assert {path.name: path.read_bytes() for path in runtime.iterdir()} == before


@pytest.mark.parametrize("constant", ("NaN", "Infinity", "-Infinity"))
def test_nonstandard_json_file_is_usage_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    constant: str,
) -> None:
    root = tmp_path / "constant-file-root"
    _initialize_cli_root(root, capsys)
    payload = root / "non-standard-number.json"
    payload.write_text(
        '{"name":"number","metadata":{"value":' + constant + "}}",
        encoding="utf-8",
    )
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    before = {path.name: path.read_bytes() for path in runtime.iterdir()}

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "task", "add", str(payload)],
        capsys,
    )

    _assert_json_failure(result, exit_code=1, error_code="usage")
    _assert_nonstandard_constant_message(result)
    assert {path.name: path.read_bytes() for path in runtime.iterdir()} == before


@pytest.mark.parametrize("constant", ("NaN", "Infinity", "-Infinity"))
def test_nonstandard_persisted_json_has_stable_state_io_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    constant: str,
) -> None:
    root = tmp_path / "constant-state-root"
    _initialize_cli_root(root, capsys)
    state_path = root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
    raw = _state_bytes_with_nonstandard_constant(root, constant)
    state_path.write_bytes(raw)

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "show"],
        capsys,
    )

    _assert_json_failure(result, exit_code=2, error_code="state_io")
    _assert_nonstandard_constant_message(result)
    assert state_path.read_bytes() == raw


@pytest.mark.parametrize("constant", ("NaN", "Infinity", "-Infinity"))
def test_nonstandard_backup_json_has_stable_invalid_backup_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    constant: str,
) -> None:
    root = tmp_path / "constant-backup-root"
    _initialize_cli_root(root, capsys)
    mutated = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            'work.extensions["tests/current"]',
            "true",
        ],
        capsys,
    )
    assert mutated[0] == 0
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    backup_path = runtime / "state.json.bak"
    backup_path.write_bytes(_state_bytes_with_nonstandard_constant(root, constant))
    before = {path.name: path.read_bytes() for path in runtime.iterdir()}

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "restore"],
        capsys,
    )

    _assert_json_failure(result, exit_code=8, error_code="invalid_backup")
    _assert_nonstandard_constant_message(result)
    assert {path.name: path.read_bytes() for path in runtime.iterdir()} == before


@pytest.mark.parametrize("operation", ("set", "append"))
def test_oversized_inline_json_is_rejected_before_json_parsing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    operation: str,
) -> None:
    root = tmp_path / operation
    _initialize_cli_root(root, capsys)
    assert cli_module.MAX_COMMAND_PAYLOAD_BYTES == 2 * 1024 * 1024
    test_limit = 64
    monkeypatch.setattr(cli_module, "MAX_COMMAND_PAYLOAD_BYTES", test_limit)
    malformed_oversized_json = "{" + "x" * test_limit

    result = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            operation,
            'work.extensions["tests/oversized"]',
            malformed_oversized_json,
        ],
        capsys,
    )

    _assert_json_failure(result, exit_code=11, error_code="resource_limit")


def test_deep_inline_json_is_rejected_without_mutation_or_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "deep-inline-root"
    _initialize_cli_root(root, capsys)
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    before = {path.name: path.read_bytes() for path in runtime.iterdir()}

    result = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            'work.extensions["tests/deep"]',
            _deep_json_array(2_000),
        ],
        capsys,
    )

    _assert_json_failure(result, exit_code=11, error_code="resource_limit")
    assert {path.name: path.read_bytes() for path in runtime.iterdir()} == before


def test_deep_json_file_is_rejected_without_mutation_or_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "deep-file-root"
    _initialize_cli_root(root, capsys)
    payload = root / "deep-task.json"
    payload.write_text(
        '{"name":"deep","metadata":{"nested":' + _deep_json_array(2_000) + "}}",
        encoding="utf-8",
    )
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    before = {path.name: path.read_bytes() for path in runtime.iterdir()}

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "task", "add", str(payload)],
        capsys,
    )

    _assert_json_failure(result, exit_code=11, error_code="resource_limit")
    assert {path.name: path.read_bytes() for path in runtime.iterdir()} == before


def test_deep_persisted_state_has_stable_resource_limit_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "deep-state-root"
    _initialize_cli_root(root, capsys)
    state_path = root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
    raw = _state_bytes_with_deep_json(root)
    state_path.write_bytes(raw)

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "show"],
        capsys,
    )

    _assert_json_failure(result, exit_code=11, error_code="resource_limit")
    assert state_path.read_bytes() == raw


def test_deep_backup_has_stable_invalid_backup_error_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "deep-backup-root"
    _initialize_cli_root(root, capsys)
    mutated = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            'work.extensions["tests/current"]',
            "true",
        ],
        capsys,
    )
    assert mutated[0] == 0
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    backup_path = runtime / "state.json.bak"
    backup_path.write_bytes(_state_bytes_with_deep_json(root))
    before = {path.name: path.read_bytes() for path in runtime.iterdir()}

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "restore"],
        capsys,
    )

    _assert_json_failure(result, exit_code=8, error_code="invalid_backup")
    assert {path.name: path.read_bytes() for path in runtime.iterdir()} == before


def test_oversized_inline_json_integer_is_a_resource_limit_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "integer-inline-root"
    _initialize_cli_root(root, capsys)
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    before = {path.name: path.read_bytes() for path in runtime.iterdir()}

    result = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            'work.extensions["tests/integer"]',
            "9" * 5_000,
        ],
        capsys,
    )

    _assert_json_failure(result, exit_code=11, error_code="resource_limit")
    assert {path.name: path.read_bytes() for path in runtime.iterdir()} == before


def test_oversized_json_file_integer_is_a_resource_limit_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "integer-file-root"
    _initialize_cli_root(root, capsys)
    payload = root / "integer-task.json"
    payload.write_text(
        '{"id":' + "9" * 5_000 + ',"name":"Oversized integer"}',
        encoding="utf-8",
    )
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    before = {path.name: path.read_bytes() for path in runtime.iterdir()}

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "task", "add", str(payload)],
        capsys,
    )

    _assert_json_failure(result, exit_code=11, error_code="resource_limit")
    assert {path.name: path.read_bytes() for path in runtime.iterdir()} == before


def test_oversized_persisted_integer_has_stable_resource_limit_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "integer-state-root"
    _initialize_cli_root(root, capsys)
    state_path = root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
    raw = _state_bytes_with_oversized_integer(root)
    state_path.write_bytes(raw)

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "show"],
        capsys,
    )

    _assert_json_failure(result, exit_code=11, error_code="resource_limit")
    assert state_path.read_bytes() == raw


def test_oversized_backup_integer_has_stable_invalid_backup_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "integer-backup-root"
    _initialize_cli_root(root, capsys)
    mutated = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            'work.extensions["tests/current"]',
            "true",
        ],
        capsys,
    )
    assert mutated[0] == 0
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    backup_path = runtime / "state.json.bak"
    backup_path.write_bytes(_state_bytes_with_oversized_integer(root))
    before = {path.name: path.read_bytes() for path in runtime.iterdir()}

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "restore"],
        capsys,
    )

    _assert_json_failure(result, exit_code=8, error_code="invalid_backup")
    assert {path.name: path.read_bytes() for path in runtime.iterdir()} == before


@pytest.mark.parametrize(
    "argv",
    (
        pytest.param(["state", "task", "add"], id="task-add"),
        pytest.param(["state", "task", "attempt", "1"], id="task-attempt"),
        pytest.param(["state", "task", "complete", "1"], id="task-complete"),
        pytest.param(["state", "task", "set-body", "1"], id="task-body"),
        pytest.param(["state", "task", "set-meta", "1"], id="task-meta"),
        pytest.param(["state", "contract", "set"], id="contract"),
    ),
)
def test_every_oversized_file_payload_is_rejected_before_utf8_or_json_decoding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    root = tmp_path / "file-limit-root"
    _initialize_cli_root(root, capsys)
    if argv[2:3] != ["add"] and argv[1:2] == ["task"]:
        task_payload = tmp_path / "valid-task.json"
        task_payload.write_text('{"name":"Payload target"}', encoding="utf-8")
        add_result = _invoke_main(
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
        assert add_result[0] == 0
    assert cli_module.MAX_COMMAND_PAYLOAD_BYTES == 2 * 1024 * 1024
    test_limit = 64
    monkeypatch.setattr(cli_module, "MAX_COMMAND_PAYLOAD_BYTES", test_limit)
    payload = tmp_path / "oversized-invalid-utf8.bin"
    payload.write_bytes(b"\xff" * (test_limit + 1))

    result = _invoke_main(
        ["--root", str(root), "--json", *argv, str(payload)],
        capsys,
    )

    _assert_json_failure(result, exit_code=11, error_code="resource_limit")


def test_state_reads_follow_the_exported_size_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "state-limit-root"
    _initialize_cli_root(root, capsys)
    assert store_module.MAX_STATE_BYTES > 1
    monkeypatch.setattr(store_module, "MAX_STATE_BYTES", 1)

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "show"],
        capsys,
    )

    _assert_json_failure(result, exit_code=11, error_code="resource_limit")


def test_typed_schema_resource_limit_has_stable_cli_classification(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "typed-schema-limit-root"
    _initialize_cli_root(root, capsys)
    state_path = root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
    state = new_state(repo_root=root)
    state["work"]["contract_card"] = "x" * (MAX_CONTRACT_CARD_BYTES + 1)
    encoded = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
    assert len(encoded) < MAX_STATE_BYTES
    state_path.write_bytes(encoded)

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "show"],
        capsys,
    )

    _assert_json_failure(result, exit_code=11, error_code="resource_limit")


def test_state_protocol_inventory_and_examples_follow_the_live_parser() -> None:
    parser = build_parser()
    document_path = Path(__file__).resolve().parents[2] / "docs" / "state-protocol.md"
    document = document_path.read_bytes().decode("utf-8")
    inventory = document.partition("## Command inventory")[2].partition(
        "## Command examples"
    )[0]
    documented_commands = tuple(
        line.strip() for line in inventory.splitlines() if line.startswith("ovcaq ")
    )

    assert documented_commands == _parser_command_inventory(parser)
    assert render_state_protocol_command_inventory(parser) in inventory
    examples = [
        line.strip().removeprefix("$ ")
        for line in document.partition("## Command examples")[2].splitlines()
        if line.strip().startswith("$ ovcaq ")
    ]
    assert examples
    for example in examples:
        parser.parse_args(shlex.split(example)[1:])
