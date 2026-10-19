from __future__ import annotations

import copy
import errno
import fcntl
import json
import os
import signal
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from test_durability import (
    _BOUNDARY_WORKER,
    _stop_worker,
    _wait_for_worker_line,
    _worker_environment,
)
from test_store import (
    _BOUNDARY_REPAIR_WRITER_OPERATION,
    _ORIGINAL_POPEN,
    _assert_child_blocks,
    _assert_child_finishes,
    _canonical_bytes,
    _child_operation,
    _directory_bytes,
    _invalid_state_bytes,
    _sidecar_after_initialize,
)

import ovcaq.state.store as store_module
from ovcaq.state.schema import (
    SchemaError,
    State,
    new_state,
)
from ovcaq.state.store import (
    BackupError,
    DurabilityBoundary,
    FutureSchemaError,
    RevisionConflictError,
    StateIOError,
    StateStore,
)


def test_restore_validates_and_republishes_the_backed_up_state(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    store = StateStore(state_path)
    store.initialize(initial)

    def mutate(candidate: State) -> None:
        candidate["work"]["prd"] = "current.md"

    store.transaction(mutate)
    restored = store.restore(expected_revision=1)

    assert restored["work"] == initial["work"]
    assert store.read() == restored
    restored["work"]["prd"] = "changed-return.md"
    assert store.read()["work"]["prd"] is None


def test_restore_uses_raw_backup_and_rotates_exact_raw_current_bytes(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    initial["work"]["extensions"] = {"tests/raw": "žluťoučký"}
    store = StateStore(state_path)
    store.initialize(initial)

    def mutate(candidate: State) -> None:
        candidate["work"]["prd"] = "raw-current.md"

    current = store.transaction(mutate)
    backup_path = state_path.with_name("state.json.bak")
    raw_backup = json.dumps(initial, ensure_ascii=False).encode("utf-8")
    raw_current = json.dumps(current, ensure_ascii=False).encode("utf-8")
    backup_path.write_bytes(raw_backup)
    state_path.write_bytes(raw_current)
    backup_path.chmod(0o644)
    state_path.chmod(0o644)

    restored = store.restore(expected_revision=1)

    expected = copy.deepcopy(initial)
    expected["revision"] = 2
    assert restored == expected
    assert state_path.read_bytes() == _canonical_bytes(expected)
    assert backup_path.read_bytes() == raw_current
    assert {entry.name for entry in tmp_path.iterdir()} == {
        "state.json",
        "state.json.bak",
        "state.json.lock",
    }
    assert stat.S_IMODE(state_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(backup_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(state_path.with_name("state.json.lock").stat().st_mode) == (
        0o600
    )


def _track_lock_descriptors(
    monkeypatch: pytest.MonkeyPatch,
    lock_path: Path,
) -> tuple[list[int], list[int]]:
    real_open = store_module.os.open
    real_close = store_module.os.close
    opened: list[int] = []
    closed: list[int] = []

    def track_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
    ) -> int:
        descriptor = real_open(path, flags, mode)
        if Path(os.fsdecode(path)) == lock_path:
            opened.append(descriptor)
        return descriptor

    def track_close(descriptor: int) -> None:
        if descriptor in opened:
            closed.append(descriptor)
        real_close(descriptor)

    monkeypatch.setattr(store_module.os, "open", track_open)
    monkeypatch.setattr(store_module.os, "close", track_close)
    return opened, closed


def _inject_lock_failure(
    monkeypatch: pytest.MonkeyPatch,
    opened: list[int],
    failure_stage: str,
) -> None:
    real_fchmod = store_module.os.fchmod
    real_flock = store_module.fcntl.flock
    acquisition_failed = False

    def fail_lock_permissions(descriptor: int, mode: int) -> None:
        if descriptor in opened and failure_stage == "permissions":
            raise OSError(errno.EIO, "injected lock fchmod failure")
        real_fchmod(descriptor, mode)

    def fail_lock_acquisition(descriptor: int, operation: int) -> None:
        nonlocal acquisition_failed
        if (
            descriptor in opened
            and failure_stage == "acquisition"
            and operation != fcntl.LOCK_UN
            and not acquisition_failed
        ):
            acquisition_failed = True
            raise OSError(errno.EIO, "injected lock flock failure")
        real_flock(descriptor, operation)

    monkeypatch.setattr(store_module.os, "fchmod", fail_lock_permissions)
    monkeypatch.setattr(store_module.fcntl, "flock", fail_lock_acquisition)


@pytest.mark.parametrize(
    "invalid_kind",
    (
        "missing",
        "malformed-json",
        "non-object",
        "future-schema",
        "schema-invalid",
    ),
)
def test_restore_rejects_invalid_backup_without_changing_durable_bytes(
    tmp_path: Path,
    invalid_kind: str,
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    store.transaction(lambda _state: None)
    backup_path = state_path.with_name("state.json.bak")
    invalid_raw = _invalid_state_bytes(invalid_kind, tmp_path)
    if invalid_raw is None:
        backup_path.unlink()
    else:
        backup_path.write_bytes(invalid_raw)
    before = _directory_bytes(tmp_path)

    with pytest.raises(BackupError):
        store.restore(expected_revision=1)

    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize(
    ("invalid_kind", "error_type"),
    (
        pytest.param("missing", StateIOError, id="missing"),
        pytest.param("malformed-json", StateIOError, id="malformed-json"),
        pytest.param("non-object", SchemaError, id="non-object"),
        pytest.param("future-schema", FutureSchemaError, id="future-schema"),
        pytest.param("schema-invalid", SchemaError, id="schema-invalid"),
    ),
)
def test_restore_validates_current_before_parsing_backup_and_preserves_bytes(
    tmp_path: Path,
    invalid_kind: str,
    error_type: type[Exception],
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    store.transaction(lambda _state: None)
    backup_path = state_path.with_name("state.json.bak")
    backup_path.write_bytes(b"backup must not be parsed\n")
    invalid_raw = _invalid_state_bytes(invalid_kind, tmp_path)
    if invalid_raw is None:
        state_path.unlink()
    else:
        state_path.write_bytes(invalid_raw)
    before = _directory_bytes(tmp_path)

    with pytest.raises(error_type):
        store.restore(expected_revision=1)

    assert _directory_bytes(tmp_path) == before


def test_restore_honors_expected_revision_without_changing_durable_bytes(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    store.transaction(lambda _state: None)
    before = _directory_bytes(tmp_path)

    with pytest.raises(RevisionConflictError):
        store.restore(expected_revision=0)

    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize(
    ("setup_transactions", "expected_revision"),
    (
        pytest.param(1, 0, id="stale"),
        pytest.param(1, 2, id="future"),
        pytest.param(0, False, id="boolean-false-equals-zero"),
        pytest.param(1, True, id="boolean-true-equals-one"),
        pytest.param(0, -1, id="negative"),
    ),
)
def test_restore_rejects_conflicting_and_invalid_revisions_before_publication(
    tmp_path: Path,
    setup_transactions: int,
    expected_revision: int,
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    for _ in range(setup_transactions):
        store.transaction(lambda _state: None)
    before = _directory_bytes(tmp_path)

    with pytest.raises(RevisionConflictError):
        store.restore(expected_revision=expected_revision)

    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize(
    "failure_stage",
    (
        pytest.param("permissions", id="fchmod"),
        pytest.param("acquisition", id="flock"),
    ),
)
def test_lock_setup_failures_close_the_opened_descriptor_once_without_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
) -> None:
    state_path = tmp_path / "state.json"
    lock_path = tmp_path / "state.json.lock"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    store.transaction(lambda _state: None)
    before = _directory_bytes(tmp_path)
    opened_lock_descriptors, closed_lock_descriptors = _track_lock_descriptors(
        monkeypatch, lock_path
    )
    _inject_lock_failure(monkeypatch, opened_lock_descriptors, failure_stage)
    mutator_calls = 0

    def mutate(_state: State) -> None:
        nonlocal mutator_calls
        mutator_calls += 1

    with pytest.raises(StateIOError):
        store.transaction(mutate, expected_revision=1)

    assert len(opened_lock_descriptors) == 1
    assert closed_lock_descriptors == opened_lock_descriptors
    assert mutator_calls == 0
    assert _directory_bytes(tmp_path) == before


def test_read_uses_the_shared_sidecar_and_transaction_uses_it_exclusively(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    sidecar = _sidecar_after_initialize(state_path)
    marker = tmp_path / "mutator-called"

    with sidecar.open("rb") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH)
        try:
            with _child_operation(
                state_path, "read", cwd=tmp_path, marker=marker
            ) as reader:
                _assert_child_finishes(reader)
            with _child_operation(
                state_path, "transaction", cwd=tmp_path, marker=marker
            ) as writer:
                _assert_child_blocks(writer)
                assert not marker.exists()
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                _assert_child_finishes(writer)
                assert marker.read_text(encoding="utf-8") == "called\n"
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    with sidecar.open("rb") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            with _child_operation(
                state_path, "read", cwd=tmp_path, marker=marker
            ) as reader:
                _assert_child_blocks(reader)
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                _assert_child_finishes(reader)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _seed_counter_state(tmp_path: Path) -> tuple[Path, State]:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    initial["work"]["extensions"] = {"tests/counter": 0}
    store = StateStore(state_path)
    store.initialize(initial)

    def increment(state: State) -> None:
        state["work"]["extensions"]["tests/counter"] += 1

    return state_path, store.transaction(increment)


def _start_boundary_writer(
    tmp_path: Path,
    state_path: Path,
    boundary: DurabilityBoundary,
    operation: str,
    *,
    interactive: bool = False,
) -> subprocess.Popen[str]:
    return _ORIGINAL_POPEN(
        [sys.executable, "-c", operation, os.fspath(state_path), boundary.name],
        cwd=tmp_path,
        env=_worker_environment(),
        stdin=subprocess.PIPE if interactive else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def test_reader_waits_until_a_boundary_blocked_writer_is_sigkilled(
    tmp_path: Path,
) -> None:
    state_path, seeded = _seed_counter_state(tmp_path)
    assert seeded["revision"] == 1
    boundary = DurabilityBoundary.STATE_TEMP_FSYNCED
    writer = _start_boundary_writer(tmp_path, state_path, boundary, _BOUNDARY_WORKER)

    try:
        _wait_for_worker_line(writer, f"{boundary.name}\n")
        with _child_operation(
            state_path,
            "read",
            cwd=tmp_path,
            marker=tmp_path / "unused-reader-marker",
        ) as reader:
            _assert_child_blocks(reader)
            os.kill(writer.pid, signal.SIGKILL)
            stdout, stderr = writer.communicate(timeout=5)
            assert writer.returncode == -signal.SIGKILL, (stdout, stderr)
            _assert_child_finishes(reader)
    finally:
        _stop_worker(writer)

    observed = StateStore(state_path).read()
    assert observed["revision"] == 1
    assert observed["work"]["extensions"]["tests/counter"] == 1

    cleaned = StateStore(state_path).transaction(
        lambda _state: None,
        expected_revision=observed["revision"],
    )
    assert cleaned["revision"] == 2
    assert cleaned["work"]["extensions"]["tests/counter"] == 1
    assert not tuple(tmp_path.glob(".state.json.ovcaq-*.tmp"))


def test_reader_waits_until_boundary_failure_repair_releases_the_writer_lock(
    tmp_path: Path,
) -> None:
    state_path, seeded = _seed_counter_state(tmp_path)
    before = _directory_bytes(tmp_path)
    boundary = DurabilityBoundary.STATE_REPLACED
    writer = _start_boundary_writer(
        tmp_path,
        state_path,
        boundary,
        _BOUNDARY_REPAIR_WRITER_OPERATION,
        interactive=True,
    )

    try:
        _wait_for_worker_line(writer, f"{boundary.name}\n")
        with _child_operation(
            state_path,
            "read",
            cwd=tmp_path,
            marker=tmp_path / "unused-repair-reader-marker",
        ) as reader:
            _assert_child_blocks(reader)
            assert writer.stdin is not None
            writer.stdin.write("fail\n")
            writer.stdin.flush()
            _wait_for_worker_line(writer, "repaired\n")
            stdout, stderr = writer.communicate(timeout=5)
            assert writer.returncode == 0, (stdout, stderr)
            _assert_child_finishes(reader)
    finally:
        _stop_worker(writer)

    assert StateStore(state_path).read() == seeded
    assert _directory_bytes(tmp_path) == before
