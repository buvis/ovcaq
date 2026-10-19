from __future__ import annotations

import errno
import os
from pathlib import Path

import pytest

from ovcaq.workflow.records import record_defer

PRD = "00004-workflow-core-v1.md"
BATCH_ID = "batch-16"
RECORD = {"op_id": "diagnostic-16", "detail": "test"}


def _is_deferred_path(
    path: str | os.PathLike[str], dir_fd: int | None, runtime_root: Path
) -> bool:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate == runtime_root / "deferred"
    if dir_fd is None or candidate != Path("deferred"):
        return False
    directory = os.fstat(dir_fd)
    root = runtime_root.stat()
    return (directory.st_dev, directory.st_ino) == (root.st_dev, root.st_ino)


def test_record_defer_refuses_regular_file_at_deferred_path(tmp_path: Path) -> None:
    runtime_root = tmp_path.resolve()
    deferred = runtime_root / "deferred"
    published = deferred / f"{BATCH_ID}-deferred.json"
    deferred.write_bytes(b"obstruction")
    inode = deferred.stat().st_ino

    with pytest.raises(OSError) as raised:
        record_defer(runtime_root, PRD, BATCH_ID, RECORD)

    assert (
        str(raised.value) == f"deferred directory is not a real directory: {deferred}"
    )
    assert isinstance(raised.value.__cause__, OSError)
    assert raised.value.__cause__.errno == errno.ENOTDIR
    assert deferred.stat().st_ino == inode
    assert deferred.read_bytes() == b"obstruction"
    assert not published.exists()


def test_record_defer_refuses_symlink_at_deferred_path(tmp_path: Path) -> None:
    runtime_root = tmp_path.resolve()
    deferred = runtime_root / "deferred"
    target = runtime_root / "target"
    target.mkdir()
    sentinel = target / "sentinel"
    sentinel.write_bytes(b"untouched")
    sentinel_inode = sentinel.stat().st_ino
    deferred.symlink_to(target, target_is_directory=True)
    link_inode = deferred.lstat().st_ino

    with pytest.raises(OSError) as raised:
        record_defer(runtime_root, PRD, BATCH_ID, RECORD)

    assert (
        str(raised.value) == f"deferred directory is not a real directory: {deferred}"
    )
    assert isinstance(raised.value.__cause__, OSError)
    assert raised.value.__cause__.errno in {errno.ELOOP, errno.ENOTDIR}
    assert deferred.is_symlink()
    assert deferred.lstat().st_ino == link_inode
    assert sentinel.stat().st_ino == sentinel_inode
    assert sentinel.read_bytes() == b"untouched"
    assert sorted(item.name for item in target.iterdir()) == ["sentinel"]


def test_record_defer_reports_directory_vanishing_before_second_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_root = tmp_path.resolve()
    deferred = runtime_root / "deferred"
    published = deferred / f"{BATCH_ID}-deferred.json"
    actual_open = os.open
    deferred_opens = 0

    def vanish_on_second_open(
        path: str | os.PathLike[str],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal deferred_opens
        if _is_deferred_path(path, dir_fd, runtime_root):
            deferred_opens += 1
            if deferred_opens == 2:
                deferred.rmdir()
        return actual_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", vanish_on_second_open)
    with pytest.raises(OSError) as raised:
        record_defer(runtime_root, PRD, BATCH_ID, RECORD)

    assert deferred_opens == 2
    assert (
        str(raised.value) == f"deferred directory is not a real directory: {deferred}"
    )
    assert isinstance(raised.value.__cause__, OSError)
    assert raised.value.__cause__.errno == errno.ENOENT
    assert not deferred.exists()
    assert not published.exists()


@pytest.mark.parametrize("error_number", (errno.EACCES, errno.ENOSPC, errno.EBADF))
def test_record_defer_reports_directory_creation_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error_number: int
) -> None:
    runtime_root = tmp_path.resolve()
    deferred = runtime_root / "deferred"
    published = deferred / f"{BATCH_ID}-deferred.json"
    actual_mkdir = os.mkdir
    failure = OSError(error_number, os.strerror(error_number), deferred)

    def fail_deferred_mkdir(
        path: str | os.PathLike[str],
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> None:
        if _is_deferred_path(path, dir_fd, runtime_root):
            raise failure
        actual_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "mkdir", fail_deferred_mkdir)
    with pytest.raises(OSError) as raised:
        record_defer(runtime_root, PRD, BATCH_ID, RECORD)

    assert str(raised.value) == f"deferred directory could not be created: {deferred}"
    assert raised.value.__cause__ is failure
    assert raised.value.__cause__.errno == error_number
    assert not deferred.exists()
    assert not published.exists()
