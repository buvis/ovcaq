"""Bounded writes of private, uninterpreted session evidence."""

from __future__ import annotations

import os
import stat
from pathlib import Path


class EvidenceLimitError(RuntimeError):
    """A chunk would exceed the evidence ceiling or free-space floor."""


class SessionEvidenceWriter:
    """Persist uninterpreted session bytes in a new private evidence file."""

    def __init__(self, path: Path, *, max_bytes: int, min_free_bytes: int) -> None:
        for value in (max_bytes, min_free_bytes):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("evidence limits must be nonnegative integers")
        self._max_bytes = max_bytes
        self._min_free_bytes = min_free_bytes
        self._written = 0
        self._descriptor: int | None = None
        information = path.parent.lstat()
        if not stat.S_ISDIR(information.st_mode) or information.st_mode & 0o022:
            raise ValueError("evidence requires a safe parent directory")
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            if not os.path.samestat(information, os.fstat(directory)):
                raise ValueError("evidence parent changed while opening")
            descriptor = os.open(
                path.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            try:
                if not os.path.samestat(information, path.parent.lstat()):
                    raise ValueError("evidence parent changed during creation")
                os.fchmod(descriptor, 0o600)
            except BaseException:
                os.close(descriptor)
                raise
            self._descriptor = descriptor
        finally:
            os.close(directory)

    def write(self, chunk: bytes) -> int:
        """Write the complete chunk, retaining every byte accepted before failure."""
        if self._descriptor is None:
            raise ValueError("evidence writer is closed")
        if not isinstance(chunk, bytes):
            raise TypeError("raw evidence must be bytes")
        if not chunk:
            return 0
        if self._written + len(chunk) > self._max_bytes:
            raise EvidenceLimitError("session evidence byte ceiling exceeded")
        space = os.fstatvfs(self._descriptor)
        if space.f_bavail * space.f_frsize - len(chunk) < self._min_free_bytes:
            raise EvidenceLimitError("session evidence free-space floor exceeded")
        view = memoryview(chunk)
        offset = 0
        while offset < len(chunk):
            try:
                accepted = os.write(self._descriptor, view[offset:])
            except InterruptedError:
                continue
            if accepted == 0:
                raise OSError("evidence write made no progress")
            offset += accepted
            self._written += accepted
        return offset

    def flush(self) -> None:
        """Sync all accepted bytes to durable storage."""
        if self._descriptor is None:
            raise ValueError("evidence writer is closed")
        os.fsync(self._descriptor)

    def close(self) -> None:
        """Sync and close once, even when syncing fails."""
        descriptor = self._descriptor
        if descriptor is None:
            return
        self._descriptor = None
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
