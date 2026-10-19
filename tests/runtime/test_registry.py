from __future__ import annotations

import fcntl
import os
import select
import stat
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from ovcaq.runtime.registry import DuplicateRunError, RunLock

_WORKER = """
import fcntl
import os
import sys
from pathlib import Path

from ovcaq.runtime.registry import DuplicateRunError, RunLock

path = Path(sys.argv[1])
operation = sys.argv[2]

if operation == "wait":
    with path.open("rb") as stream:
        print("opened", flush=True)
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        print("owned", flush=True)
        sys.stdin.readline()
elif operation == "raw":
    with path.open("rb") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("duplicate", flush=True)
        else:
            print("owned", flush=True)
elif operation == "reject":
    try:
        lock = RunLock.acquire(path)
    except OSError:
        print("rejected", flush=True)
    else:
        lock.close()
        print("accepted", flush=True)
else:
    if operation == "isolated":
        def forbid_other_files(event, args):
            if event == "open" and not isinstance(args[0], int):
                if os.fsdecode(args[0]) != str(path):
                    raise AssertionError("lock consulted another file")
            if event in {"os.listdir", "os.scandir"}:
                raise AssertionError("lock enumerated other files")
        sys.addaudithook(forbid_other_files)
    try:
        lock = RunLock.acquire(path)
    except DuplicateRunError:
        print("duplicate", flush=True)
    else:
        lock.close()
        print("owned", flush=True)
"""


def _worker_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        os.path.abspath(entry) for entry in sys.path
    )
    return environment


def _probe(path: Path, operation: str = "try") -> str:
    result = subprocess.run(
        [sys.executable, "-c", _WORKER, str(path), operation],
        env=_worker_environment(),
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    return result.stdout.strip()


@contextmanager
def _waiter(path: Path) -> Iterator[subprocess.Popen[str]]:
    worker = subprocess.Popen(
        [sys.executable, "-c", _WORKER, str(path), "wait"],
        env=_worker_environment(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        yield worker
    finally:
        if worker.poll() is None:
            worker.kill()
        worker.communicate(timeout=5)


def _expect_line(worker: subprocess.Popen[str], expected: str) -> None:
    assert worker.stdout is not None
    ready, _, _ = select.select([worker.stdout], [], [], 5)
    assert ready, f"worker did not report {expected!r}"
    assert worker.stdout.readline() == expected + "\n"


def _identity(path: Path) -> tuple[int, int]:
    information = path.stat()
    return information.st_dev, information.st_ino


def _acquisition_rejection(path: Path) -> OSError:
    try:
        lock = RunLock.acquire(path)
    except OSError as error:
        return error
    lock.close()
    raise AssertionError("acquisition accepted a substituted lock inode")


def test_acquisition_creates_private_inode_and_close_preserves_it(
    tmp_path: Path,
) -> None:
    path = tmp_path / "run.lock"
    assert not path.exists()

    lock = RunLock.acquire(path)
    try:
        identity = _identity(path)
        assert stat.S_ISREG(path.stat().st_mode)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert _probe(path, "raw") == "duplicate"
        assert _probe(path) == "duplicate"
    finally:
        lock.close()

    assert _identity(path) == identity
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert _probe(path) == "owned"
    lock.close()
    assert _identity(path) == identity
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert _probe(path, "raw") == "owned"
    assert _identity(path) == identity


def test_caller_chosen_basename_holds_lock_and_preserves_inode_after_close(
    tmp_path: Path,
) -> None:
    path = tmp_path / "supervisor.guard"
    lock = RunLock.acquire(path)
    try:
        identity = _identity(path)
        assert _probe(path, "raw") == "duplicate"
        assert _probe(path) == "duplicate"
    finally:
        lock.close()

    assert _identity(path) == identity
    assert _probe(path) == "owned"
    assert _probe(path, "raw") == "owned"
    assert _identity(path) == identity


def test_acquisition_and_close_preserve_existing_inode_with_private_permissions(
    tmp_path: Path,
) -> None:
    path = tmp_path / "run.lock"
    path.write_bytes(b"persistent lock\n")
    path.chmod(0o644)
    identity = _identity(path)

    lock = RunLock.acquire(path)
    try:
        assert _identity(path) == identity
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert _probe(path, "raw") == "duplicate"
        assert _probe(path) == "duplicate"
    finally:
        lock.close()

    assert _identity(path) == identity
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert _probe(path) == "owned"
    lock.close()
    assert _identity(path) == identity
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert _probe(path, "raw") == "owned"
    assert _identity(path) == identity


def test_contention_depends_on_lock_without_reading_other_files(
    tmp_path: Path,
) -> None:
    path = tmp_path / "run.lock"
    with RunLock.acquire(path):
        assert _probe(path, "isolated") == "duplicate"
        with pytest.raises(DuplicateRunError):
            RunLock.acquire(path)
    assert _probe(path, "isolated") == "owned"


@pytest.mark.parametrize("exception_exit", [False, True])
def test_context_exit_releases_lock_and_preserves_inode_and_permissions(
    tmp_path: Path, exception_exit: bool
) -> None:
    path = tmp_path / "run.lock"
    lock = RunLock.acquire(path)
    identity = _identity(path)
    sentinel = ValueError("leave the lock context")

    def leave_context() -> None:
        with lock as entered:
            assert entered is lock
            assert _probe(path) == "duplicate"
            if exception_exit:
                raise sentinel

    try:
        if exception_exit:
            with pytest.raises(ValueError) as caught:
                leave_context()
            assert caught.value is sentinel
        else:
            leave_context()
        assert _identity(path) == identity
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert _probe(path) == "owned"
    finally:
        lock.close()


def test_blocked_waiter_and_new_contender_share_one_persistent_inode(
    tmp_path: Path,
) -> None:
    path = tmp_path / "run.lock"
    lock = RunLock.acquire(path)
    identity = _identity(path)
    try:
        with _waiter(path) as waiter:
            _expect_line(waiter, "opened")
            assert waiter.stdout is not None
            ready, _, _ = select.select([waiter.stdout], [], [], 0.15)
            assert not ready, "waiter acquired the inode while the owner held it"
            lock.close()
            _expect_line(waiter, "owned")
            assert _identity(path) == identity
            assert _probe(path) == "duplicate"
            assert waiter.stdin is not None
            waiter.stdin.write("release\n")
            waiter.stdin.flush()
            stdout, stderr = waiter.communicate(timeout=5)
            assert waiter.returncode == 0, (stdout, stderr)
            assert _probe(path) == "owned"
            assert _identity(path) == identity
    finally:
        lock.close()


@pytest.mark.parametrize("kind", ["symlink", "dangling-symlink", "directory", "fifo"])
def test_unsafe_lock_paths_fail_closed_without_owning_target(
    tmp_path: Path, kind: str
) -> None:
    path = tmp_path / "run.lock"
    target = tmp_path / "target"
    if kind == "symlink":
        target.write_bytes(b"untouched\n")
        target.chmod(0o644)
        path.symlink_to(target)
    elif kind == "dangling-symlink":
        path.symlink_to(target)
    elif kind == "directory":
        path.mkdir()
    else:
        os.mkfifo(path)
    original = path.lstat()

    assert _probe(path, "reject") == "rejected"

    observed = path.lstat()
    assert (observed.st_dev, observed.st_ino, observed.st_mode) == (
        original.st_dev,
        original.st_ino,
        original.st_mode,
    )
    if kind == "symlink":
        assert target.read_bytes() == b"untouched\n"
        assert stat.S_IMODE(target.stat().st_mode) == 0o644
        assert _probe(target, "raw") == "owned"
    elif kind == "dangling-symlink":
        assert not target.exists()


def test_inode_substitution_during_acquisition_fails_and_releases_old_inode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "run.lock"
    displaced = tmp_path / "displaced.lock"
    path.write_bytes(b"")
    original_identity = _identity(path)
    real_flock = fcntl.flock
    substituted = False

    def substitute_after_lock(descriptor: int, operation: int) -> None:
        nonlocal substituted
        real_flock(descriptor, operation)
        information = os.fstat(descriptor)
        if (
            operation & fcntl.LOCK_EX
            and (information.st_dev, information.st_ino) == original_identity
            and not substituted
        ):
            substituted = True
            path.rename(displaced)
            path.write_bytes(b"replacement\n")

    with monkeypatch.context() as patch:
        patch.setattr(fcntl, "flock", substitute_after_lock)
        rejection = _acquisition_rejection(path)

    assert isinstance(rejection, OSError)
    assert substituted, "the filesystem race was not exercised"
    assert _identity(displaced) == original_identity
    assert _identity(path) != original_identity
    assert _probe(displaced, "raw") == "owned"
    assert _probe(path, "raw") == "owned"
