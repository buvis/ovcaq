from __future__ import annotations

import copy
import errno
import json
import os
import stat
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from test_commands import (
    ERROR_CODES,
    _assert_json_failure,
    _directory_bytes,
    _initialize_cli_root,
    _initialize_running_cli_task,
    _invoke_main,
)

from ovcaq.errors import ErrorCode
from ovcaq.state.commands import (
    MutationResult,
    StateService,
)
from ovcaq.state.schema import (
    State,
    new_state,
    validate_state,
)
from ovcaq.state.store import StateStore


def _seed_restore_cli(
    root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _initialize_cli_root(root, capsys)
    result = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            "--expected-revision",
            "0",
            'work.extensions["tests/restore"]',
            '"current"',
        ],
        capsys,
    )
    assert result[0] == 0
    assert json.loads(result[1]) == {"ok": True, "revision": 1, "result": None}
    assert result[2] == ""


def test_state_restore_cli_routes_through_state_service(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "restore-service-cli"
    _seed_restore_cli(root, capsys)
    restore_calls: list[int | None] = []
    real_restore = StateService.restore

    def recording_restore(
        self: StateService,
        *,
        expected_revision: int | None = None,
    ) -> MutationResult:
        restore_calls.append(expected_revision)
        return real_restore(self, expected_revision=expected_revision)

    monkeypatch.setattr(StateService, "restore", recording_restore)

    result = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "restore",
            "--expected-revision",
            "1",
        ],
        capsys,
    )

    assert result[0] == 0
    assert json.loads(result[1]) == {"ok": True, "revision": 2, "result": None}
    assert result[2] == ""
    assert restore_calls == [1]
    assert (
        "tests/restore"
        not in StateStore(
            root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
        ).read()["work"]["extensions"]
    )


def test_error_code_contains_exactly_the_public_failure_values() -> None:
    assert tuple(error.value for error in ErrorCode) == ERROR_CODES


@pytest.mark.parametrize(
    "argv",
    (
        pytest.param(["state"], id="missing-state-command"),
        pytest.param(["state", "unknown"], id="unknown-state-command"),
        pytest.param(["state", "--json", "show"], id="global-option-after-verb"),
        pytest.param(["state", "get"], id="missing-path"),
        pytest.param(
            ["init", "--expected-revision", "0"],
            id="compare-and-set-on-init",
        ),
        pytest.param(
            ["state", "task", "add", "--unsafe", "task.json"],
            id="unsafe-on-task-command",
        ),
    ),
)
def test_main_normalizes_argparse_mistakes_to_usage_exit_one(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code, _stdout, stderr = _invoke_main(argv, capsys)

    assert exit_code == 1
    assert "usage:" in stderr.lower()
    assert "Traceback" not in stderr


def test_main_accepts_only_declared_top_level_and_subparser_option_spellings(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "option-spelling-root"
    _initialize_cli_root(root, capsys)

    state_path = _assert_show_option_spellings(root, capsys)

    exact_unsafe = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            "--unsafe",
            'work.extensions["tests/declared-option"]',
            '{"exact":true}',
        ],
        capsys,
    )
    assert exact_unsafe[0] == 0
    assert exact_unsafe[2] == ""
    assert StateStore(state_path).read()["work"]["extensions"][
        "tests/declared-option"
    ] == {"exact": True}

    runtime = state_path.parent
    before = _directory_bytes(runtime)
    abbreviated_unsafe = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            "--unsa",
            'work.extensions["tests/declared-option"]',
            '{"abbreviated":true}',
        ],
        capsys,
    )
    _assert_json_failure(abbreviated_unsafe, exit_code=1, error_code="usage")
    assert _directory_bytes(runtime) == before


def _assert_show_option_spellings(
    root: Path,
    capsys: pytest.CaptureFixture[str],
) -> Path:

    exact = _invoke_main(
        ["--root", str(root), "--json", "state", "show"],
        capsys,
    )
    assert exact[0] == 0
    state_path = root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
    assert json.loads(exact[1]) == StateStore(state_path).read()
    assert exact[2] == ""

    abbreviated = _invoke_main(
        ["--root", str(root), "--js", "state", "show"],
        capsys,
    )
    assert abbreviated[0] == 1
    assert abbreviated[1] == ""
    assert "usage:" in abbreviated[2].lower()
    assert "Traceback" not in abbreviated[2]
    return state_path


def test_init_uses_explicit_root_preserves_config_and_ignores_legacy_state(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = (tmp_path / "explicit-root").resolve()
    root.mkdir()
    config = root / "ovcaq.toml"
    config_bytes = b"# existing project configuration\n"
    config.write_bytes(config_bytes)
    config.chmod(0o640)
    os.utime(
        config,
        ns=(1_700_000_000_123_456_789, 1_700_000_100_987_654_321),
    )
    config_before = config.stat()
    legacy_state = root / "dev" / "local" / "autopilot" / "state.json"
    legacy_state.parent.mkdir(parents=True)
    legacy_bytes = b'{"schema_version": 999, "legacy": true}\n'
    legacy_state.write_bytes(legacy_bytes)

    result = _invoke_main(["--root", str(root), "--json", "init"], capsys)

    assert result[0] == 0
    assert json.loads(result[1]) == {"ok": True, "revision": 0, "result": None}
    assert result[2] == ""
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    assert stat.S_IMODE(runtime.stat().st_mode) == 0o700
    config_after = config.stat()
    assert config_after.st_ino == config_before.st_ino
    assert stat.S_IMODE(config_after.st_mode) == stat.S_IMODE(config_before.st_mode)
    assert config_after.st_atime_ns == config_before.st_atime_ns
    assert config_after.st_mtime_ns == config_before.st_mtime_ns
    assert config.read_bytes() == config_bytes
    assert legacy_state.read_bytes() == legacy_bytes
    assert StateStore(runtime / "state.json").read() == new_state(repo_root=root)

    before = _directory_bytes(runtime)
    _assert_json_failure(
        _invoke_main(["--root", str(root), "--json", "init"], capsys),
        exit_code=7,
        error_code="state_exists",
    )
    assert _directory_bytes(runtime) == before


@pytest.mark.parametrize(
    "symlink_component",
    (
        pytest.param("docs", id="docs"),
        pytest.param("dev", id="dev"),
        pytest.param("project-management", id="project-management"),
        pytest.param("ovcaq", id="runtime"),
    ),
)
def test_init_rejects_symlinked_runtime_components_without_touching_target(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    symlink_component: str,
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    victim = tmp_path / "external-runtime"
    victim.mkdir(mode=0o755)
    note = victim / "operator-note"
    note.write_bytes(b"outside bytes must stay exact\n")
    os.utime(note, ns=(1_700_000_000_000_000_000, 1_700_000_100_000_000_000))
    victim_mode = stat.S_IMODE(victim.stat().st_mode)
    note_before = note.stat()

    current = root
    for component in ("docs", "dev", "project-management", "ovcaq"):
        candidate = current / component
        if component == symlink_component:
            candidate.symlink_to(victim, target_is_directory=True)
            break
        candidate.mkdir()
        current = candidate

    result = _invoke_main(["--root", str(root), "--json", "init"], capsys)

    _assert_json_failure(result, exit_code=2, error_code="state_io")
    assert stat.S_IMODE(victim.stat().st_mode) == victim_mode
    assert note.read_bytes() == b"outside bytes must stay exact\n"
    note_after = note.stat()
    assert note_after.st_mode == note_before.st_mode
    assert note_after.st_mtime_ns == note_before.st_mtime_ns
    assert tuple(path.relative_to(victim) for path in victim.rglob("*")) == (
        Path("operator-note"),
    )


def test_init_config_creation_failure_leaves_no_state_and_retry_succeeds(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = (tmp_path / "retryable-config-failure").resolve()
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    runtime.mkdir(parents=True)
    state_path = runtime / "state.json"
    config = root / "ovcaq.toml"
    root_mode = stat.S_IMODE(root.stat().st_mode)
    root.chmod(0o500)

    try:
        failed = _invoke_main(["--root", str(root), "--json", "init"], capsys)
    finally:
        root.chmod(root_mode)

    _assert_json_failure(failed, exit_code=2, error_code="state_io")
    assert not state_path.exists()
    assert not config.exists()

    retried = _invoke_main(["--root", str(root), "--json", "init"], capsys)

    assert retried[0] == 0
    assert json.loads(retried[1]) == {"ok": True, "revision": 0, "result": None}
    assert retried[2] == ""
    assert config.read_bytes() == b""
    assert StateStore(state_path).read() == new_state(repo_root=root)


def _create_config_directory(path: Path) -> None:
    path.mkdir()


def _create_broken_config_symlink(path: Path) -> None:
    path.symlink_to(path.with_name("missing-ovcaq.toml"))


@pytest.mark.parametrize(
    "create_collision",
    (
        pytest.param(_create_config_directory, id="directory"),
        pytest.param(_create_broken_config_symlink, id="broken-symlink"),
    ),
)
def test_init_rejects_project_config_path_collisions_before_state_publication(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    create_collision: Callable[[Path], None],
) -> None:
    root = (tmp_path / "config-collision").resolve()
    root.mkdir()
    config = root / "ovcaq.toml"
    create_collision(config)
    original = config.lstat()
    target = config.readlink() if stat.S_ISLNK(original.st_mode) else None

    result = _invoke_main(["--root", str(root), "--json", "init"], capsys)

    _assert_json_failure(result, exit_code=2, error_code="state_io")
    assert not (
        root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
    ).exists()
    after = config.lstat()
    assert after.st_mode == original.st_mode
    assert os.path.samestat(after, original)
    if target is not None:
        assert config.readlink() == target


@pytest.mark.parametrize("discovery", ("config", "runtime", "git"))
def test_init_discovers_an_absolute_project_root_and_creates_missing_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    discovery: str,
) -> None:
    root = (tmp_path / discovery / "project").resolve()
    nested = root / "nested" / "cwd"
    nested.mkdir(parents=True)
    config = root / "ovcaq.toml"
    if discovery == "config":
        config.write_text("# discovery marker\n", encoding="utf-8")
    elif discovery == "runtime":
        runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
        runtime.mkdir(parents=True)
        runtime.chmod(0o700)
    else:
        subprocess.run(
            ["git", "init", "--quiet", str(root)],
            check=True,
            capture_output=True,
            text=True,
        )
    monkeypatch.chdir(nested)

    result = _invoke_main(["--json", "init"], capsys)

    assert result[0] == 0
    assert json.loads(result[1]) == {"ok": True, "revision": 0, "result": None}
    assert result[2] == ""
    state = StateStore(
        root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
    ).read()
    assert state["work"]["repo_root"] == str(root)
    assert Path(state["work"]["repo_root"]).is_absolute()
    assert config.is_file()
    if discovery == "config":
        assert config.read_text(encoding="utf-8") == "# discovery marker\n"


@pytest.mark.parametrize(
    ("setup", "argv", "exit_code", "error_code"),
    (
        pytest.param("missing", ["unknown"], 1, "usage", id="argparse-usage"),
        pytest.param("missing", ["state", "show"], 2, "state_io", id="missing-state"),
        pytest.param("corrupt", ["state", "show"], 2, "state_io", id="corrupt-state"),
        pytest.param(
            "initialized",
            ["state", "restore"],
            8,
            "invalid_backup",
            id="missing-backup",
        ),
        pytest.param(
            "initialized",
            [
                "state",
                "set",
                "--expected-revision",
                "999",
                'work.extensions["tests/conflict"]',
                "{}",
            ],
            9,
            "revision_conflict",
            id="revision-conflict",
        ),
        pytest.param(
            "initialized",
            ["state", "get", "work["],
            1,
            "invalid_path",
            id="invalid-path",
        ),
        pytest.param(
            "initialized",
            ["state", "set", "work.phase", '"review"'],
            1,
            "protected_path",
            id="protected-path",
        ),
        pytest.param(
            "initialized",
            ["state", "set", 'work.extensions["tests/json"]', "{"],
            1,
            "usage",
            id="malformed-inline-json",
        ),
    ),
)
def test_json_failures_have_stable_codes_exits_and_streams(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    setup: str,
    argv: list[str],
    exit_code: int,
    error_code: str,
) -> None:
    root = tmp_path / "failure-root"
    root.mkdir()
    if setup == "initialized":
        _initialize_cli_root(root, capsys)
    elif setup == "corrupt":
        state_path = (
            root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
        )
        state_path.parent.mkdir(parents=True)
        state_path.write_bytes(b"{not-json")

    result = _invoke_main(
        ["--root", str(root), "--json", *argv],
        capsys,
    )

    _assert_json_failure(result, exit_code=exit_code, error_code=error_code)


@pytest.mark.parametrize("corruption", ("schema-type", "derived-count", "future"))
def test_schema_failures_are_classified_without_tracebacks(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    corruption: str,
) -> None:
    root = tmp_path / "schema-root"
    _initialize_cli_root(root, capsys)
    state_path = root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
    state = json.loads(state_path.read_bytes().decode("utf-8"))
    current_version = new_state(repo_root=root)["schema_version"]
    assert state["schema_version"] == current_version
    if corruption == "schema-type":
        state["schema_version"] = str(current_version)
        exit_code, error_code = 1, "invalid_state"
    elif corruption == "derived-count":
        state["work"]["tasks_total"] = 1
        with pytest.raises(ValueError):
            validate_state(cast(State, copy.deepcopy(state)))
        exit_code, error_code = 1, "invalid_state"
    else:
        state["schema_version"] = current_version + 1
        exit_code, error_code = 6, "future_schema"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "show"],
        capsys,
    )

    _assert_json_failure(result, exit_code=exit_code, error_code=error_code)


def test_invalid_persisted_value_cannot_spoof_resource_limit_classification(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "untrusted-error-text-root"
    _initialize_cli_root(root, capsys)
    state_path = root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["work"]["phase"] = "exceeds 9"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    before = state_path.read_bytes()

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "show"],
        capsys,
    )

    _assert_json_failure(result, exit_code=1, error_code="invalid_state")
    assert state_path.read_bytes() == before


@pytest.mark.parametrize(
    "inline_json",
    (
        pytest.param('{"value":1,"value":2}', id="root-object"),
        pytest.param(
            '{"nested":{"value":1,"value":2}}',
            id="nested-object",
        ),
    ),
)
def test_inline_json_duplicate_keys_are_rejected_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    inline_json: str,
) -> None:
    root = tmp_path / "inline-duplicate-root"
    _initialize_cli_root(root, capsys)
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    before = _directory_bytes(runtime)

    result = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            'work.extensions["tests/duplicate"]',
            inline_json,
        ],
        capsys,
    )

    _assert_json_failure(result, exit_code=1, error_code="usage")
    assert _directory_bytes(runtime) == before


@pytest.mark.parametrize(
    "file_json",
    (
        pytest.param('{"name":"first","name":"last"}', id="root-owned"),
        pytest.param(
            '{"name":"task","metadata":{"value":1,"value":2}}',
            id="nested-open",
        ),
    ),
)
def test_json_file_duplicate_keys_are_rejected_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    file_json: str,
) -> None:
    root = tmp_path / "file-duplicate-root"
    _initialize_cli_root(root, capsys)
    payload = root / "duplicate.json"
    payload.write_text(file_json, encoding="utf-8")
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    before = _directory_bytes(runtime)

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "task", "add", str(payload)],
        capsys,
    )

    _assert_json_failure(result, exit_code=1, error_code="usage")
    assert _directory_bytes(runtime) == before


@pytest.mark.parametrize("duplicate_kind", ("root", "owned", "open"))
def test_persisted_duplicate_keys_have_stable_state_io_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    duplicate_kind: str,
) -> None:
    root = tmp_path / "persisted-duplicate-root"
    _initialize_cli_root(root, capsys)
    state_path = root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
    state = new_state(repo_root=root)
    if duplicate_kind == "open":
        state["work"]["extensions"] = {"tests/duplicate": "last"}
    encoded = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
    if duplicate_kind == "root":
        raw = encoded.replace(
            b'"revision": 0,', b'"revision": 999,\n  "revision": 0,', 1
        )
    elif duplicate_kind == "owned":
        raw = encoded.replace(
            b'"phase": "build",',
            b'"phase": "review",\n    "phase": "build",',
            1,
        )
    else:
        raw = encoded.replace(
            b'"tests/duplicate": "last"',
            b'"tests/duplicate": "first",\n      "tests/duplicate": "last"',
            1,
        )
    assert raw != encoded
    state_path.write_bytes(raw)

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "show"],
        capsys,
    )

    _assert_json_failure(result, exit_code=2, error_code="state_io")
    assert state_path.read_bytes() == raw


def test_duplicate_backup_has_stable_invalid_backup_error_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "duplicate-backup-root"
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
    encoded = backup_path.read_bytes()
    duplicate = encoded.replace(
        b'"revision": 0,', b'"revision": 999,\n  "revision": 0,', 1
    )
    assert duplicate != encoded
    backup_path.write_bytes(duplicate)
    before = _directory_bytes(runtime)

    result = _invoke_main(
        ["--root", str(root), "--json", "state", "restore"],
        capsys,
    )

    _assert_json_failure(result, exit_code=8, error_code="invalid_backup")
    assert _directory_bytes(runtime) == before


@pytest.mark.parametrize(
    "command_argv",
    (
        pytest.param(("state", "task", "add"), id="add"),
        pytest.param(("state", "task", "attempt", "1"), id="attempt"),
        pytest.param(("state", "task", "complete", "1"), id="complete"),
        pytest.param(("state", "task", "set-meta", "1"), id="set-meta"),
    ),
)
@pytest.mark.parametrize(
    "payload_text",
    (
        pytest.param("[]", id="array"),
        pytest.param('"scalar"', id="scalar"),
        pytest.param("null", id="null"),
    ),
)
def test_object_only_task_payloads_reject_every_non_object_json_shape_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    command_argv: tuple[str, ...],
    payload_text: str,
) -> None:
    root = tmp_path / "object-payload-root"
    _initialize_running_cli_task(root, capsys)
    payload_path = root / "non-object.json"
    payload_path.write_text(payload_text, encoding="utf-8")
    runtime = root / "docs" / "dev" / "project-management" / "ovcaq"
    before = _directory_bytes(runtime)

    result = _invoke_main(
        ["--root", str(root), "--json", *command_argv, str(payload_path)],
        capsys,
    )

    _assert_json_failure(result, exit_code=1, error_code="usage")
    assert _directory_bytes(runtime) == before


def test_directory_sync_refusal_reports_unsupported_durability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "durability-root"
    _initialize_cli_root(root, capsys)
    real_fsync = os.fsync

    def refuse_directory_sync(fd: int) -> None:
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError(errno.EINVAL, "directory sync unsupported")
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", refuse_directory_sync)

    result = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            'work.extensions["tests/durability"]',
            "{}",
        ],
        capsys,
    )

    _assert_json_failure(
        result,
        exit_code=10,
        error_code="durability_unsupported",
    )


def test_exception_name_alone_does_not_report_unsupported_durability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "durability-type-root"
    _initialize_cli_root(root, capsys)

    class DurabilityUnsupportedError(OSError):
        pass

    def raise_same_named_untyped_error(
        _store: StateStore,
        _mutator: Any,
        *,
        expected_revision: int | None = None,
        publication_guard: Callable[[], None] | None = None,
    ) -> State:
        del expected_revision, publication_guard
        raise DurabilityUnsupportedError(errno.EIO, "not the state-store error type")

    monkeypatch.setattr(StateStore, "transaction", raise_same_named_untyped_error)

    result = _invoke_main(
        [
            "--root",
            str(root),
            "--json",
            "state",
            "set",
            'work.extensions["tests/durability-type"]',
            "{}",
        ],
        capsys,
    )

    _assert_json_failure(result, exit_code=2, error_code="state_io")
