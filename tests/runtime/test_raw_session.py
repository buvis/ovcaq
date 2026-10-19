from __future__ import annotations

import errno
import os
import stat
from collections.abc import Callable
from pathlib import Path

import pytest

from ovcaq.runtime import session
from ovcaq.runtime.session import (
    EvidenceLimitError,
    SessionEvidenceWriter,
)


def _reject(expected: type[BaseException], operation: Callable[[], object]) -> None:
    with pytest.raises(expected):
        operation()


def test_writes_private_regular_evidence_without_interpreting_bytes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "raw.jsonl"
    previous_umask = os.umask(0)
    try:
        writer = SessionEvidenceWriter(path, max_bytes=1024, min_free_bytes=0)
    finally:
        os.umask(previous_umask)
    try:
        information = path.lstat()
        assert stat.S_ISREG(information.st_mode)
        assert stat.S_IMODE(information.st_mode) == 0o600
        assert path.read_bytes() == b""
        expected = b""
        for chunk in (b"", b'\xff{"token":"secret', b'"}\r', b"\n\x00\xc3", b"\xa9"):
            assert writer.write(chunk) == len(chunk)
            expected += chunk
            assert path.read_bytes() == expected
    finally:
        writer.close()
    assert path.read_bytes() == expected


@pytest.mark.parametrize("chunk", [None, "text", bytearray(b"x"), memoryview(b"x"), 3])
def test_rejects_nonbytes_without_changing_evidence(
    tmp_path: Path, chunk: object
) -> None:
    path = tmp_path / "raw.jsonl"
    writer = SessionEvidenceWriter(path, max_bytes=6, min_free_bytes=0)
    try:
        assert writer.write(b"abc") == 3
        _reject(TypeError, lambda: writer.write(chunk))
        assert path.read_bytes() == b"abc"
        assert writer.write(b"def") == 3
        assert path.read_bytes() == b"abcdef"
    finally:
        writer.close()


@pytest.mark.parametrize("field", ["max_bytes", "min_free_bytes"])
@pytest.mark.parametrize("value", [-1, True, False, 1.0, "1", None])
def test_rejects_invalid_limits(tmp_path: Path, field: str, value: object) -> None:
    limits = {"max_bytes": 1024, "min_free_bytes": 0, field: value}
    _reject(ValueError, lambda: SessionEvidenceWriter(tmp_path / "raw.jsonl", **limits))


@pytest.mark.parametrize("limit", [0, 7])
def test_checks_ceiling_before_each_chunk_and_empty_writes_consume_no_budget(
    tmp_path: Path, limit: int
) -> None:
    path = tmp_path / "raw.jsonl"
    writer = SessionEvidenceWriter(path, max_bytes=limit, min_free_bytes=0)
    try:
        assert writer.write(b"") == 0
        prefix = b"abc" if limit else b""
        assert writer.write(prefix) == len(prefix)
        with pytest.raises(EvidenceLimitError):
            writer.write(b"x" * (limit - len(prefix) + 1))
        assert path.read_bytes() == prefix
        remainder = b"z" * (limit - len(prefix))
        assert writer.write(remainder) == len(remainder)
        assert writer.write(b"") == 0
        with pytest.raises(EvidenceLimitError):
            writer.write(b"!")
        assert path.read_bytes() == prefix + remainder
    finally:
        writer.close()


@pytest.mark.parametrize("min_free_bytes", [4, 12, 28, 252])
def test_checks_available_space_before_each_chunk_and_allows_exact_floor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    min_free_bytes: int,
) -> None:
    available_blocks = 1024

    def filesystem_space(_location: object) -> os.statvfs_result:
        return os.statvfs_result(
            (4096, 4, 100000, 100000, available_blocks, 1000, 1000, 1000, 0, 255)
        )

    monkeypatch.setattr(os, "statvfs", filesystem_space)
    monkeypatch.setattr(os, "fstatvfs", filesystem_space)
    path = tmp_path / "raw.jsonl"
    writer = SessionEvidenceWriter(path, max_bytes=1024, min_free_bytes=min_free_bytes)
    try:
        available_blocks = min_free_bytes // 4 + 1
        assert writer.write(b"abc") == 3
        available_blocks = min_free_bytes // 4
        with pytest.raises(EvidenceLimitError):
            writer.write(b"d")
        assert path.read_bytes() == b"abc"
        available_blocks = min_free_bytes // 4 + 1
        assert writer.write(b"defg") == 4
        available_blocks = min_free_bytes // 4 - 1
        with pytest.raises(EvidenceLimitError):
            writer.write(b"h")
        assert path.read_bytes() == b"abcdefg"
    finally:
        writer.close()


def test_completes_partial_and_interrupted_writes_without_loss_or_duplication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "raw.jsonl"
    prefix = b"old"
    chunks = (bytes(range(256)), b"\xffnew\x00\r\n\xc3\xa9", b"last unterminated row")
    expected = prefix + b"".join(chunks)
    writer = SessionEvidenceWriter(path, max_bytes=len(expected), min_free_bytes=0)
    real_write = os.write
    calls = 0

    def interrupted_write(descriptor: int, payload: bytes) -> int:
        nonlocal calls
        calls += 1
        if calls % 5 in (1, 2):
            raise InterruptedError(errno.EINTR, "interrupted")
        return real_write(descriptor, payload[: calls % 7 + 1])

    try:
        assert writer.write(prefix) == len(prefix)
        retained = prefix
        with monkeypatch.context() as patch:
            patch.setattr(os, "write", interrupted_write)
            for chunk in chunks:
                assert writer.write(chunk) == len(chunk)
                retained += chunk
                assert path.read_bytes() == retained
        assert path.read_bytes() == expected
        with pytest.raises(EvidenceLimitError):
            writer.write(b"!")
        assert path.read_bytes() == expected
    finally:
        writer.close()
    assert path.read_bytes() == expected


@pytest.mark.parametrize("failure", [errno.ENOSPC, errno.EIO])
@pytest.mark.parametrize("accepted_prefix", [0, 2])
def test_write_failure_preserves_prior_evidence_and_partial_new_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: int,
    accepted_prefix: int,
) -> None:
    path = tmp_path / "raw.jsonl"
    writer = SessionEvidenceWriter(path, max_bytes=1024, min_free_bytes=0)
    real_write = os.write
    accepted = False

    def failing_write(descriptor: int, payload: bytes) -> int:
        nonlocal accepted
        if accepted_prefix and not accepted:
            accepted = True
            return real_write(descriptor, payload[:accepted_prefix])
        raise OSError(failure, "injected write failure")

    try:
        assert writer.write(b"prior\n") == 6
        information = path.stat()
        with monkeypatch.context() as patch:
            patch.setattr(os, "write", failing_write)
            _reject(OSError, lambda: writer.write(b"next\xff\n"))
        assert os.path.samestat(information, path.stat())
        assert path.read_bytes() == b"prior\n" + b"next\xff\n"[:accepted_prefix]
    finally:
        writer.close()
    assert path.read_bytes() == b"prior\n" + b"next\xff\n"[:accepted_prefix]


@pytest.mark.parametrize(
    "obstacle", ["file", "symlink", "dangling", "directory", "fifo"]
)
def test_rejects_existing_or_nonregular_paths_without_overwriting_evidence(
    tmp_path: Path, obstacle: str
) -> None:
    path = tmp_path / "raw.jsonl"
    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(b"preserve")
    if obstacle == "file":
        path.write_bytes(b"original evidence")
        path.chmod(0o600)
    elif obstacle == "symlink":
        path.symlink_to(sentinel)
    elif obstacle == "dangling":
        path.symlink_to(tmp_path / "missing")
    elif obstacle == "directory":
        path.mkdir()
    else:
        os.mkfifo(path)
    before = path.lstat()
    _reject(
        OSError, lambda: SessionEvidenceWriter(path, max_bytes=1024, min_free_bytes=0)
    )
    after = path.lstat()
    assert (after.st_ino, after.st_mode) == (before.st_ino, before.st_mode)
    assert sentinel.read_bytes() == b"preserve"
    assert not (tmp_path / "missing").exists()
    if obstacle == "file":
        assert path.read_bytes() == b"original evidence"


@pytest.mark.parametrize("obstacle", ["symlink", "world-writable"])
def test_rejects_unsafe_parent_without_creating_evidence(
    tmp_path: Path, obstacle: str
) -> None:
    parent = tmp_path / "session"
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    sentinel = target / "sentinel"
    sentinel.write_bytes(b"preserve")
    if obstacle == "symlink":
        parent.symlink_to(target, target_is_directory=True)
    else:
        parent.mkdir(mode=0o700)
        parent.chmod(0o777)
    _reject(
        ValueError,
        lambda: SessionEvidenceWriter(
            parent / "raw.jsonl", max_bytes=1024, min_free_bytes=0
        ),
    )
    assert not (parent / "raw.jsonl").exists()
    assert list(target.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"preserve"


def test_parent_replacement_during_creation_fails_without_following_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = tmp_path / "session"
    parent.mkdir(mode=0o700)
    moved = tmp_path / "original-session"
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    sentinel = target / "sentinel"
    sentinel.write_bytes(b"preserve")
    real_open = os.open
    replaced = False

    def replace_parent(
        path: str | Path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal replaced
        if flags & os.O_CREAT and not replaced:
            replaced = True
            parent.rename(moved)
            parent.symlink_to(target, target_is_directory=True)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", replace_parent)
    _reject(
        ValueError,
        lambda: SessionEvidenceWriter(
            parent / "raw.jsonl", max_bytes=1024, min_free_bytes=0
        ),
    )
    assert parent.is_symlink()
    assert list(target.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"preserve"


def test_flush_syncs_bytes_and_close_syncs_then_closes_only_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "raw.jsonl"
    writer = SessionEvidenceWriter(path, max_bytes=1024, min_free_bytes=0)
    information = path.stat()
    real_fsync, real_close = os.fsync, os.close
    events: list[tuple[str, bytes]] = []

    def sync(descriptor: int) -> None:
        is_evidence = os.path.samestat(information, os.fstat(descriptor))
        real_fsync(descriptor)
        if is_evidence:
            events.append(("sync", path.read_bytes()))

    def close(descriptor: int) -> None:
        is_evidence = os.path.samestat(information, os.fstat(descriptor))
        real_close(descriptor)
        if is_evidence:
            events.append(("close", path.read_bytes()))

    monkeypatch.setattr(os, "fsync", sync)
    monkeypatch.setattr(os, "close", close)
    try:
        assert writer.write(b"first") == 5
        writer.flush()
        assert ("sync", b"first") in events
        assert writer.write(b" second") == 7
        events.clear()
        writer.close()
        assert events == [("sync", b"first second"), ("close", b"first second")]
        writer.close()
        assert events == [("sync", b"first second"), ("close", b"first second")]
        _reject(ValueError, lambda: writer.write(b"late"))
        _reject(ValueError, lambda: writer.write(b""))
        _reject(ValueError, writer.flush)
        assert path.read_bytes() == b"first second"
    finally:
        writer.close()


def test_close_releases_descriptor_once_even_when_sync_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "raw.jsonl"
    writer = SessionEvidenceWriter(path, max_bytes=1024, min_free_bytes=0)
    assert writer.write(b"preserved evidence") == 18
    real_close = os.close
    synced: list[int] = []
    closed: list[int] = []

    def failing_sync(descriptor: int) -> None:
        synced.append(descriptor)
        raise OSError(errno.EIO, "injected sync failure")

    def close(descriptor: int) -> None:
        real_close(descriptor)
        closed.append(descriptor)

    with monkeypatch.context() as patch:
        patch.setattr(os, "fsync", failing_sync)
        patch.setattr(os, "close", close)
        try:
            with pytest.raises(OSError) as failure:
                writer.close()
            assert failure.value.errno == errno.EIO
            assert len(synced) == 1
            descriptor = synced[0]
            assert closed == [descriptor]
            with pytest.raises(OSError) as invalid:
                os.fstat(descriptor)
            assert invalid.value.errno == errno.EBADF
            writer.close()
            assert synced == closed == [descriptor]
            assert path.read_bytes() == b"preserved evidence"
        finally:
            for descriptor in synced:
                if descriptor not in closed:
                    real_close(descriptor)


def test_evidence_writer_has_no_obsolete_raw_writer_alias() -> None:
    assert not hasattr(session, "RawSessionWriter")
