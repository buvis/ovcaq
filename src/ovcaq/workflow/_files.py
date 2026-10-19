"""Descriptor-bound lifecycle directories and serialized deferred ledgers."""

from __future__ import annotations

import fcntl
import json
import os
import stat
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from enum import StrEnum
from pathlib import Path
from typing import cast

from ovcaq.state.schema import (
    ArtifactIdentity,
    JSONValue,
    ResourceLimitError,
    decode_json,
    validate_json_value,
)
from ovcaq.workflow.paths import require_safe_identifier

_O_SEARCH: int | None = getattr(os, "O_SEARCH", getattr(os, "O_EXEC", None))


class DeferredRecordConflictError(ValueError):
    """Raised when an operation ID is reused for a different deferred record."""


class DeferBoundary(StrEnum):
    """Deterministic interruption points around deferred record publication."""

    BEFORE_PUBLISH = "before-publish"
    AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC = "after-replace-before-directory-fsync"
    AFTER_PUBLISH = "after-publish"


type DeferBoundaryHook = Callable[[DeferBoundary], None]


def _require_basename(value: object, label: str) -> str:
    return require_safe_identifier(value, label)


def _require_operation_id(value: object) -> str:
    return require_safe_identifier(value, "op_id")


def _canonical_record_bytes(value: dict[str, JSONValue]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory_descriptor(descriptor: int) -> None:
    os.fsync(descriptor)


@contextmanager
def _serialize_deferred_publication(path: Path, directory: int) -> Iterator[None]:
    # The opened directory inode survives sidecar renames. Keep reads out of the
    # check/replace interval too, so a rival cannot prepare a stale snapshot.
    # Do not wait: a replacement-sidecar caller can be nested inside this writer.
    try:
        fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        raise OSError(f"publication busy; retry: {path}") from error
    try:
        yield
    finally:
        fcntl.flock(directory, fcntl.LOCK_UN)


def _validate_record_encoding(path: Path, content: dict[str, JSONValue]) -> bytes:
    encoded = _canonical_record_bytes(content)
    # The same bounded reader used to load this ledger must be able to replay
    # it; reject a prospective write here, before anything touches disk, so a
    # rejected ledger leaves prior bytes intact. Apply the same bounded
    # JSON-value validation the reader applies after decoding, not just the
    # decode-time depth check.
    decoded = decode_json(encoded.decode("utf-8"), source=f"deferred record {path}")
    validate_json_value(decoded, "deferred")
    return encoded


def _write_record_file(
    path: Path,
    directory: int,
    content: dict[str, JSONValue],
    *,
    previous: dict[str, JSONValue],
    verify_lock: Callable[[], None],
    boundary_hook: DeferBoundaryHook | None = None,
) -> None:
    descriptor = -1
    temporary: str | None = None
    encoded = _validate_record_encoding(path, content)
    try:
        _verify_lifecycle_directory_identity(path.parent, directory, label="deferred")
        temporary = f".{path.name}.ovcaq-{uuid.uuid4().hex}.tmp"
        descriptor = os.open(
            temporary,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=directory,
        )
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        _finish_record_publication(
            path, directory, temporary, previous, verify_lock, boundary_hook
        )
        temporary = None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass


def _finish_record_publication(
    path: Path,
    directory: int,
    temporary: str,
    previous: dict[str, JSONValue],
    verify_lock: Callable[[], None],
    boundary_hook: DeferBoundaryHook | None,
) -> None:
    if boundary_hook is not None:
        boundary_hook(DeferBoundary.BEFORE_PUBLISH)
    _publish_record_file(path, directory, temporary, previous, verify_lock)
    if boundary_hook is not None:
        boundary_hook(DeferBoundary.AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC)
    _sync_deferred_directory(path.parent, directory)
    if boundary_hook is not None:
        boundary_hook(DeferBoundary.AFTER_PUBLISH)
    _verify_lifecycle_directory_identity(path.parent, directory, label="deferred")
    verify_lock()


def _publish_record_file(
    path: Path,
    directory: int,
    temporary: str,
    previous: dict[str, JSONValue],
    verify_lock: Callable[[], None],
) -> None:
    with _serialize_deferred_publication(path, directory):
        verify_lock()
        # A displaced sidecar can also be restored while this snapshot is being
        # prepared. Compare under the same inode lock as the native replacement.
        current = _read_record_content(
            path, cast(str, previous["batch_id"]), directory, verify_lock
        )
        if current != previous:
            raise OSError(f"deferred record changed during publication; retry: {path}")
        os.replace(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory)


def _read_record_file(
    path: Path,
    batch_id: str,
    directory: int,
    verify: Callable[[], None] | None = None,
) -> dict[str, JSONValue]:
    with _serialize_deferred_publication(path, directory):
        return _read_record_content(path, batch_id, directory, verify)


def _read_record_content(
    path: Path,
    batch_id: str,
    directory: int,
    verify: Callable[[], None] | None = None,
) -> dict[str, JSONValue]:
    _verify_lifecycle_directory_identity(path.parent, directory, label="deferred")
    try:
        descriptor = os.open(
            path.name,
            os.O_RDONLY
            | os.O_NONBLOCK
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=directory,
        )
    except FileNotFoundError:
        if verify is not None:
            verify()
        return {"batch_id": batch_id, "items": []}
    with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise ValueError(
                f"deferred record is not a single-linked regular file: {path}"
            )
        try:
            value = decode_json(stream.read(), source=f"deferred record {path}")
        except ResourceLimitError:
            raise
        except ValueError as error:
            raise ValueError(f"corrupt deferred record {path}: {error}") from error
    if verify is not None:
        verify()
    else:
        _verify_lifecycle_directory_identity(path.parent, directory, label="deferred")
    if (
        not isinstance(value, dict)
        or set(value) != {"batch_id", "items"}
        or value.get("batch_id") != batch_id
        or not isinstance(value["items"], list)
        or not all(isinstance(item, dict) for item in value["items"])
    ):
        raise ValueError(f"corrupt deferred record {path}")
    validate_json_value(value, "deferred")
    return value


def record_defer(
    runtime_root: Path,
    prd: str,
    batch_id: str,
    record: dict[str, object],
    *,
    boundary_hook: DeferBoundaryHook | None = None,
) -> Path:
    """Durably append one operation-ID-deduplicated deferred record."""
    batch_id = _require_basename(batch_id, "batch_id")
    item = _deferred_item(prd, record)
    with _open_deferred_ledger(runtime_root, batch_id) as (path, directory, verify):
        _append_deferred_record(path, directory, batch_id, item, boundary_hook, verify)
        return path


def _deferred_item(prd: str, record: dict[str, object]) -> dict[str, JSONValue]:
    item = dict(record)
    item["op_id"] = _require_operation_id(record.get("op_id"))
    item["prd"] = _require_basename(prd, "prd")
    validate_json_value(item, "deferred.items[]")
    return cast(dict[str, JSONValue], item)


def _sync_deferred_directory(path: Path, directory: int) -> None:
    _verify_lifecycle_directory_identity(path, directory, label="deferred")
    _fsync_directory_descriptor(directory)
    _verify_lifecycle_directory_identity(path, directory, label="deferred")


def _verify_directory_chain(ancestry: dict[Path, tuple[int, int]]) -> None:
    for ancestor, identity in ancestry.items():
        try:
            linked = os.stat(ancestor, follow_symlinks=False)
        except OSError as error:
            raise OSError(
                f"runtime directory identity changed; retry: {ancestor}"
            ) from error
        if not stat.S_ISDIR(linked.st_mode) or identity != (
            linked.st_dev,
            linked.st_ino,
        ):
            raise OSError(f"runtime directory identity changed; retry: {ancestor}")


@contextmanager
def _ensure_directory_chain(
    path: Path,
) -> Iterator[tuple[int, Callable[[], None]]]:
    """Confirm every ancestor, including levels left by interrupted creators."""
    path = path.resolve()
    levels = (*reversed(path.parents), path)
    confirmed: tuple[int, int] | None = None
    ancestry: dict[Path, tuple[int, int]] = {}

    def verify_ancestry() -> None:
        _verify_directory_chain(ancestry)

    for level in levels[1:]:
        with _open_lifecycle_directory(
            level.parent, label="runtime", search_only=True
        ) as parent:
            parent_stat = os.fstat(parent)
            if confirmed is not None and confirmed != (
                parent_stat.st_dev,
                parent_stat.st_ino,
            ):
                raise OSError(
                    f"runtime directory identity changed; retry: {level.parent}"
                )
            if not level.exists():
                level.mkdir(exist_ok=True)
            with _open_lifecycle_directory(
                level, label="runtime", search_only=True
            ) as directory:
                os.fsync(parent)
                _verify_lifecycle_directory_identity(
                    level.parent, parent, label="runtime"
                )
                _verify_lifecycle_directory_identity(level, directory, label="runtime")
                level_stat = os.fstat(directory)
                confirmed = (level_stat.st_dev, level_stat.st_ino)
                ancestry[level] = confirmed
                if level == path:
                    yield directory, verify_ancestry
                    return


@contextmanager
def _open_deferred_ledger(
    runtime_root: Path, batch_id: str
) -> Iterator[tuple[Path, int, Callable[[], None]]]:
    """Hold the configured directory and ledger lock through publication/commit."""
    batch_id = _require_basename(batch_id, "batch_id")
    deferred = runtime_root / "deferred"
    directory_error = f"deferred directory is not a real directory: {deferred}"
    with _ensure_directory_chain(runtime_root) as (runtime, verify_runtime):
        flags = (
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            directory = os.open(deferred.name, flags, dir_fd=runtime)
        except FileNotFoundError:
            try:
                os.mkdir(deferred.name, mode=0o700, dir_fd=runtime)
            except FileExistsError:
                pass
            except OSError as error:
                raise OSError(
                    f"deferred directory could not be created: {deferred}"
                ) from error
            verify_runtime()
            try:
                directory = os.open(deferred.name, flags, dir_fd=runtime)
            except OSError as error:
                raise OSError(directory_error) from error
        except OSError as error:
            raise OSError(directory_error) from error
        try:
            _fsync_directory_descriptor(runtime)
            verify_runtime()
            path = deferred / f"{batch_id}-deferred.json"
            with _lock_deferred_ledger(path, directory) as verify_lock:

                def verify() -> None:
                    verify_runtime()
                    verify_lock()

                verify()
                yield path, directory, verify
                verify()
        finally:
            os.close(directory)


@contextmanager
def _lock_deferred_ledger(path: Path, directory: int) -> Iterator[Callable[[], None]]:
    lock_name = f"{path.name}.lock"
    _verify_lifecycle_directory_identity(path.parent, directory, label="deferred")
    descriptor = os.open(
        lock_name,
        os.O_RDWR
        | os.O_CREAT
        | os.O_NONBLOCK
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
        0o600,
        dir_fd=directory,
    )
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise ValueError(f"deferred lock is not a regular file: {lock_name}")
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)

        def verify() -> None:
            _verify_lifecycle_directory_identity(
                path.parent, directory, label="deferred"
            )
            try:
                linked = os.stat(lock_name, dir_fd=directory, follow_symlinks=False)
            except OSError as error:
                raise OSError(f"deferred lock identity changed: {lock_name}") from error
            if (opened.st_dev, opened.st_ino) != (
                linked.st_dev,
                linked.st_ino,
            ) or linked.st_nlink != 1:
                raise OSError(f"deferred lock identity changed: {lock_name}")

        verify()
        yield verify
        verify()
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _append_deferred_record(
    path: Path,
    directory: int,
    batch_id: str,
    item: dict[str, JSONValue],
    boundary_hook: DeferBoundaryHook | None,
    verify_lock: Callable[[], None],
) -> None:
    verify_lock()
    content = _read_record_file(path, batch_id, directory, verify_lock)
    items = cast(list[dict[str, JSONValue]], content["items"])
    existing = next((row for row in items if row.get("op_id") == item["op_id"]), None)
    if existing is not None:
        if existing != item:
            raise DeferredRecordConflictError(
                f"conflicting deferred record for op_id {item['op_id']!r}"
            )
        _sync_deferred_directory(path.parent, directory)
        verify_lock()
        return
    _write_record_file(
        path,
        directory,
        {**content, "items": [*items, item]},
        previous=content,
        boundary_hook=boundary_hook,
        verify_lock=verify_lock,
    )


def load_deferred_records(
    runtime_root: Path,
    batch_id: str,
) -> tuple[dict[str, JSONValue], ...]:
    """Load and validate the current batch's deferred records."""
    batch_id = _require_basename(batch_id, "batch_id")
    path = runtime_root / "deferred" / f"{batch_id}-deferred.json"
    if not path.parent.exists():
        return ()
    with _open_lifecycle_directory(path.parent, label="deferred") as directory:
        content = _read_record_file(path, batch_id, directory)
    return tuple(cast(list[dict[str, JSONValue]], content["items"]))


@contextmanager
def _open_lifecycle_directory(
    directory: Path,
    *,
    create: bool = False,
    label: str = "lifecycle",
    search_only: bool = False,
) -> Iterator[int]:
    """Open a verified lifecycle directory without following its final link."""
    if create:
        directory.mkdir(exist_ok=True)
        _fsync_directory(directory.parent)
    access = _O_SEARCH if search_only and _O_SEARCH is not None else os.O_RDONLY
    flags = (
        access
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(directory, flags)
    except OSError as error:
        if search_only and _O_SEARCH is None and isinstance(error, PermissionError):
            raise PermissionError(
                error.errno,
                f"{label} directory requires read access for durable ancestry "
                "confirmation on this platform",
                str(directory),
            ) from error
        raise OSError(
            f"{label} directory is not a real directory: {directory}"
        ) from error
    try:
        _verify_lifecycle_directory_identity(directory, descriptor, label=label)
        yield descriptor
    finally:
        os.close(descriptor)


def _verify_lifecycle_directory_identity(
    directory: Path, descriptor: int, *, label: str = "lifecycle"
) -> None:
    """Require ``directory`` to still name the directory open on ``descriptor``."""
    try:
        opened = os.fstat(descriptor)
        linked = os.stat(directory, follow_symlinks=False)
    except OSError as error:
        raise OSError(f"{label} directory identity changed: {directory}") from error
    if (
        not stat.S_ISDIR(opened.st_mode)
        or not stat.S_ISDIR(linked.st_mode)
        or (opened.st_dev, opened.st_ino) != (linked.st_dev, linked.st_ino)
    ):
        raise OSError(f"{label} directory identity changed: {directory}")


def _artifact_stat(directory: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return None


def _validate_prd_artifact(directory: int, path: Path, label: str) -> None:
    artifact = _artifact_stat(directory, path.name)
    if artifact is not None and not stat.S_ISREG(artifact.st_mode):
        raise OSError(f"PRD {label} is not a regular non-symlink file: {path}")


def _artifact_identity(artifact: os.stat_result | None) -> ArtifactIdentity | None:
    if artifact is None:
        return None
    return {"device": artifact.st_dev, "inode": artifact.st_ino}


def _require_artifact_identity(
    directory: int, path: Path, identity: ArtifactIdentity | None
) -> None:
    artifact = _artifact_stat(directory, path.name)
    if identity is None or artifact is None or _artifact_identity(artifact) != identity:
        raise OSError(f"PRD artifact identity changed: {path}")
