from __future__ import annotations

import copy
import errno
import fcntl
import json
import os
import select
import signal
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from functools import wraps
from pathlib import Path
from types import TracebackType
from typing import BinaryIO, Self, cast

import pytest

import ovcaq.state.store as store_module
from ovcaq.state.schema import State, new_state
from ovcaq.state.store import (
    DurabilityBoundary,
    DurabilityUnsupportedError,
    StateIOError,
    StateStore,
)

type Event = tuple[object, ...]


_BOUNDARY_WORKER = """
import signal
import sys
from pathlib import Path

from ovcaq.state.store import DurabilityBoundary, StateStore

state_path = Path(sys.argv[1])
target = DurabilityBoundary[sys.argv[2]]

def pause_at_boundary(boundary):
    if boundary is target:
        print(boundary.name, flush=True)
        signal.pause()

def increment(state):
    extensions = state["work"]["extensions"]
    extensions["tests/counter"] += 1

StateStore(state_path, boundary_hook=pause_at_boundary).transaction(increment)
raise AssertionError("worker passed the requested durability boundary")
"""


def _worker_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        os.fspath(Path(entry or os.curdir).resolve()) for entry in sys.path
    )
    return environment


def _stop_worker(process: subprocess.Popen[str]) -> tuple[str, str]:
    if process.poll() is None:
        process.kill()
    try:
        return process.communicate(timeout=5)
    except subprocess.TimeoutExpired as error:
        raise AssertionError(
            f"worker did not stop; stdout={error.output!r}, stderr={error.stderr!r}"
        ) from error


def _wait_for_worker_line(process: subprocess.Popen[str], expected: str) -> None:
    assert process.stdout is not None
    readable, _, _ = select.select((process.stdout,), (), (), 5)
    if not readable:
        stdout, stderr = _stop_worker(process)
        raise AssertionError(
            f"worker protocol timed out; stdout={stdout!r}, stderr={stderr!r}"
        )
    actual = process.stdout.readline()
    if actual != expected:
        stdout, stderr = _stop_worker(process)
        raise AssertionError(
            "worker protocol mismatch; "
            f"expected={expected!r}, stdout={actual + stdout!r}, stderr={stderr!r}"
        )


@pytest.fixture
def neutral_state_root() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="ovcaq-neutral-durability-") as directory:
        root = Path(directory)
        assert "pytest-of-" not in os.fspath(root)
        yield root


class _SpiedBinaryStream:
    def __init__(
        self,
        stream: BinaryIO,
        descriptor: int,
        temp_descriptors: dict[int, Path],
        events: list[Event],
    ) -> None:
        self._stream = stream
        self._descriptor = descriptor
        self._temp_descriptors = temp_descriptors
        self._events = events

    def __enter__(self) -> Self:
        self._stream.__enter__()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        try:
            return self._stream.__exit__(exception_type, exception, traceback)
        finally:
            self._temp_descriptors.pop(self._descriptor, None)

    def write(self, data: bytes) -> int:
        self._events.append(("write",))
        return self._stream.write(data)

    def flush(self) -> None:
        self._stream.flush()

    def fileno(self) -> int:
        return self._stream.fileno()


class _PublicationSpy:
    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        state_path: Path,
    ) -> None:
        self.events: list[Event] = []
        self.created_temps: list[Path] = []
        self.mkstemp_calls: list[tuple[Path, str, str]] = []
        self.directory_descriptors: dict[int, Path] = {}
        self.closed_directories: list[Path] = []
        self._temp_descriptors: dict[int, Path] = {}
        self._state_path = state_path
        self._install_temp_spies(monkeypatch)
        self._install_directory_spies(monkeypatch)
        self._install_publication_spies(monkeypatch)

    def _install_temp_spies(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_mkstemp = store_module.tempfile.mkstemp
        real_fdopen = store_module.os.fdopen

        def spy_mkstemp(*, dir: Path, prefix: str, suffix: str) -> tuple[int, str]:
            descriptor, name = real_mkstemp(dir=dir, prefix=prefix, suffix=suffix)
            temp_path = Path(name)
            self.created_temps.append(temp_path)
            self.mkstemp_calls.append((Path(dir), prefix, suffix))
            self._temp_descriptors[descriptor] = temp_path
            return descriptor, name

        def spy_fdopen(
            descriptor: int,
            mode: str,
            *,
            closefd: bool,
        ) -> _SpiedBinaryStream:
            stream = cast(
                BinaryIO,
                real_fdopen(descriptor, mode, closefd=closefd),
            )
            return _SpiedBinaryStream(
                stream,
                descriptor,
                self._temp_descriptors,
                self.events,
            )

        monkeypatch.setattr(store_module.tempfile, "mkstemp", spy_mkstemp)
        monkeypatch.setattr(store_module.os, "fdopen", spy_fdopen)

    def _install_directory_spies(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_open = store_module.os.open
        real_fsync = store_module.os.fsync
        real_close = store_module.os.close

        def spy_open(
            path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
            flags: int,
            mode: int = 0o777,
        ) -> int:
            descriptor = real_open(path, flags, mode)
            if Path(os.fsdecode(path)) == self._state_path.parent:
                self.events.append(("directory_open", flags))
                self.directory_descriptors[descriptor] = self._state_path.parent
            return descriptor

        @wraps(real_fsync)
        def spy_fsync(descriptor: int) -> None:
            if descriptor in self._temp_descriptors:
                self.events.append(("file_fsync",))
            elif descriptor in self.directory_descriptors:
                self.events.append(("directory_fsync",))
            real_fsync(descriptor)

        def spy_close(descriptor: int) -> None:
            directory = self.directory_descriptors.pop(descriptor, None)
            if directory is not None:
                self.events.append(("directory_close",))
                self.closed_directories.append(directory)
            real_close(descriptor)

        monkeypatch.setattr(store_module.os, "open", spy_open)
        monkeypatch.setattr(store_module.os, "fsync", spy_fsync)
        monkeypatch.setattr(store_module.os, "close", spy_close)

    def _install_publication_spies(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_link = store_module.os.link
        real_replace = store_module.os.replace

        def spy_link(source: Path, target: Path) -> None:
            real_link(source, target)
            self.events.append(("publish", target.name))

        def spy_replace(source: Path, target: Path) -> None:
            real_replace(source, target)
            self.events.append(("replace", target.name))

        monkeypatch.setattr(store_module.os, "link", spy_link)
        monkeypatch.setattr(store_module.os, "replace", spy_replace)

    def observe_boundary(self, boundary: DurabilityBoundary) -> None:
        self.events.append(("boundary", boundary))


def _assert_store_temp_names(spy: _PublicationSpy, count: int) -> None:
    expected_call = (
        spy.created_temps[0].parent,
        ".state.json.ovcaq-",
        ".tmp",
    )
    assert spy.mkstemp_calls == [expected_call] * count
    assert len(spy.created_temps) == count
    assert all(
        temp.parent == expected_call[0]
        and temp.name.startswith(expected_call[1])
        and temp.name.endswith(expected_call[2])
        for temp in spy.created_temps
    )


def test_initialize_fsyncs_file_then_publishes_then_fsyncs_directory(
    neutral_state_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = neutral_state_root / "state.json"
    spy = _PublicationSpy(monkeypatch, state_path)
    store = StateStore(state_path, boundary_hook=spy.observe_boundary)

    store.initialize(new_state(repo_root=neutral_state_root))

    assert spy.events == [
        ("write",),
        ("file_fsync",),
        ("boundary", DurabilityBoundary.STATE_TEMP_FSYNCED),
        ("publish", "state.json"),
        ("boundary", DurabilityBoundary.STATE_REPLACED),
        ("directory_open", os.O_RDONLY),
        ("directory_fsync",),
        ("directory_close",),
        ("boundary", DurabilityBoundary.STATE_DIR_FSYNCED),
    ]
    assert spy.closed_directories == [neutral_state_root]
    _assert_store_temp_names(spy, 1)


@pytest.mark.parametrize("operation", ("transaction", "restore"))
def test_locked_mutation_fsyncs_backup_and_state_in_deterministic_order(
    neutral_state_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    state_path = neutral_state_root / "state.json"
    setup_store = StateStore(state_path)
    setup_store.initialize(new_state(repo_root=neutral_state_root))
    if operation == "restore":
        setup_store.transaction(lambda _state: None)

    spy = _PublicationSpy(monkeypatch, state_path)
    store = StateStore(state_path, boundary_hook=spy.observe_boundary)

    if operation == "transaction":
        store.transaction(lambda _state: None)
    else:
        store.restore()

    assert spy.events == [
        ("write",),
        ("file_fsync",),
        ("boundary", DurabilityBoundary.BACKUP_TEMP_FSYNCED),
        ("replace", "state.json.bak"),
        ("boundary", DurabilityBoundary.BACKUP_REPLACED),
        ("directory_open", os.O_RDONLY),
        ("directory_fsync",),
        ("directory_close",),
        ("boundary", DurabilityBoundary.BACKUP_DIR_FSYNCED),
        ("write",),
        ("file_fsync",),
        ("boundary", DurabilityBoundary.STATE_TEMP_FSYNCED),
        ("replace", "state.json"),
        ("boundary", DurabilityBoundary.STATE_REPLACED),
        ("directory_open", os.O_RDONLY),
        ("directory_fsync",),
        ("directory_close",),
        ("boundary", DurabilityBoundary.STATE_DIR_FSYNCED),
    ]
    assert spy.closed_directories == [neutral_state_root, neutral_state_root]
    _assert_store_temp_names(spy, 2)


def _seed_counter_store(neutral_state_root: Path) -> tuple[StateStore, State]:
    store = StateStore(neutral_state_root / "state.json")
    initial = new_state(repo_root=neutral_state_root)
    initial["work"]["extensions"] = {"tests/counter": 0}
    store.initialize(initial)

    def increment(state: State) -> None:
        extensions = state["work"]["extensions"]
        extensions["tests/counter"] += 1

    seeded = store.transaction(increment)
    assert seeded["revision"] == 1
    assert seeded["work"]["extensions"]["tests/counter"] == 1
    return store, seeded


def _kill_worker_at_boundary(
    neutral_state_root: Path,
    state_path: Path,
    boundary: DurabilityBoundary,
) -> None:
    command = [
        sys.executable,
        "-c",
        _BOUNDARY_WORKER,
        os.fspath(state_path),
        boundary.name,
    ]
    process = subprocess.Popen(
        command,
        cwd=neutral_state_root,
        env=_worker_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        _wait_for_worker_line(process, f"{boundary.name}\n")
        os.kill(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == -signal.SIGKILL, (stdout, stderr)
    finally:
        _stop_worker(process)


def _interrupt_worker_at_boundary(
    neutral_state_root: Path,
    state_path: Path,
    boundary: DurabilityBoundary,
) -> tuple[int, str]:
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            _BOUNDARY_WORKER,
            os.fspath(state_path),
            boundary.name,
        ],
        cwd=neutral_state_root,
        env=_worker_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        _wait_for_worker_line(process, f"{boundary.name}\n")
        os.kill(process.pid, signal.SIGINT)
        _stdout, stderr = process.communicate(timeout=5)
        assert process.returncode is not None
        return process.returncode, stderr
    finally:
        _stop_worker(process)


def _assert_recoverable_state(
    neutral_state_root: Path,
    seeded: State,
) -> None:
    state_path = neutral_state_root / "state.json"
    paths = (
        state_path,
        state_path.with_suffix(".json.bak"),
        state_path.with_suffix(".json.lock"),
    )
    fresh_store = StateStore(state_path)
    observed = fresh_store.read()
    expected_new = copy.deepcopy(seeded)
    expected_new["revision"] = 2
    expected_new["work"]["extensions"]["tests/counter"] = 2
    assert observed in (seeded, expected_new)
    assert observed == json.loads(state_path.read_bytes())
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in paths)

    restored = fresh_store.restore(expected_revision=observed["revision"])
    assert restored["revision"] == observed["revision"] + 1
    assert fresh_store.read() == restored
    assert not tuple(neutral_state_root.glob(".state.json.ovcaq-*.tmp"))
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in paths)


@pytest.mark.parametrize("boundary", tuple(DurabilityBoundary))
def test_sigkill_at_each_locked_mutation_boundary_preserves_recoverable_state(
    neutral_state_root: Path,
    boundary: DurabilityBoundary,
) -> None:
    state_path = neutral_state_root / "state.json"
    _store, seeded = _seed_counter_store(neutral_state_root)
    _kill_worker_at_boundary(neutral_state_root, state_path, boundary)
    _assert_recoverable_state(neutral_state_root, seeded)


def test_real_sigint_repairs_replaced_backup_before_interrupt_exit(
    neutral_state_root: Path,
) -> None:
    state_path = neutral_state_root / "state.json"
    _seed_counter_store(neutral_state_root)
    before = {
        entry.name: entry.read_bytes()
        for entry in neutral_state_root.iterdir()
        if entry.is_file()
    }

    returncode, stderr = _interrupt_worker_at_boundary(
        neutral_state_root,
        state_path,
        DurabilityBoundary.BACKUP_REPLACED,
    )

    assert returncode != 0
    assert "KeyboardInterrupt" in stderr
    assert {
        entry.name: entry.read_bytes()
        for entry in neutral_state_root.iterdir()
        if entry.is_file()
    } == before
    assert not tuple(neutral_state_root.glob(".state.json.ovcaq-*.tmp"))


@pytest.mark.parametrize(
    ("error_number", "expected_type"),
    (
        pytest.param(errno.EINVAL, DurabilityUnsupportedError, id="einval"),
        pytest.param(errno.ENOTSUP, DurabilityUnsupportedError, id="enotsup"),
        pytest.param(errno.EIO, StateIOError, id="eio"),
    ),
)
def test_directory_fsync_failures_are_translated_and_never_swallowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_number: int,
    expected_type: type[StateIOError],
) -> None:
    state_path = tmp_path / "state.json"
    real_open = store_module.os.open
    real_fsync = store_module.os.fsync
    real_close = store_module.os.close
    directory_descriptors: set[int] = set()
    closed_descriptors: set[int] = set()

    def failing_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
    ) -> int:
        descriptor = real_open(path, flags, mode)
        if Path(os.fsdecode(path)) == state_path.parent:
            assert flags == os.O_RDONLY
            directory_descriptors.add(descriptor)
        return descriptor

    @wraps(real_fsync)
    def failing_fsync(descriptor: int) -> None:
        if descriptor in directory_descriptors:
            raise OSError(error_number, os.strerror(error_number))
        real_fsync(descriptor)

    def observing_close(descriptor: int) -> None:
        if descriptor in directory_descriptors:
            closed_descriptors.add(descriptor)
        real_close(descriptor)

    monkeypatch.setattr(store_module.os, "open", failing_open)
    monkeypatch.setattr(store_module.os, "fsync", failing_fsync)
    monkeypatch.setattr(store_module.os, "close", observing_close)

    with pytest.raises(StateIOError) as raised:
        StateStore(state_path).initialize(new_state(repo_root=tmp_path))

    assert raised.type is expected_type
    assert len(directory_descriptors) == 1
    assert closed_descriptors == directory_descriptors


def _seed_cleanup_candidates(
    tmp_path: Path,
) -> tuple[Path, tuple[Path, ...], Path]:
    stale_temp = tmp_path / ".state.json.ovcaq-stale.tmp"
    stale_temp.write_bytes(b"stale")
    unrelated_files = (
        tmp_path / ".state.json.ovcaq-stale.tmp.keep",
        tmp_path / ".state.json.ovcaq-stale",
        tmp_path / "state.json.ovcaq-stale.tmp",
        tmp_path / ".other.json.ovcaq-stale.tmp",
    )
    for path in unrelated_files:
        path.write_bytes(b"unrelated")
    unrelated_directory = tmp_path / ".state.json.ovcaq-directory.tmp"
    unrelated_directory.mkdir()
    return stale_temp, unrelated_files, unrelated_directory


def test_transaction_fsync_cleanup_removes_only_store_temps_under_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    stale_temp, unrelated_files, unrelated_directory = _seed_cleanup_candidates(
        tmp_path
    )

    real_flock = store_module.fcntl.flock
    real_unlink = store_module.Path.unlink
    exclusive_lock_held = False
    stale_unlinked_under_lock = False

    def observing_flock(descriptor: int, operation: int) -> None:
        nonlocal exclusive_lock_held
        real_flock(descriptor, operation)
        if operation == fcntl.LOCK_EX:
            exclusive_lock_held = True
        elif operation == fcntl.LOCK_UN:
            exclusive_lock_held = False

    def observing_unlink(
        path: Path,
        missing_ok: bool = False,
    ) -> None:
        nonlocal stale_unlinked_under_lock
        if path == stale_temp:
            stale_unlinked_under_lock = exclusive_lock_held
        real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(store_module.fcntl, "flock", observing_flock)
    monkeypatch.setattr(store_module.Path, "unlink", observing_unlink)

    store.transaction(lambda _state: None)

    assert stale_unlinked_under_lock
    assert not stale_temp.exists()
    assert all(path.read_bytes() == b"unrelated" for path in unrelated_files)
    assert unrelated_directory.is_dir()
