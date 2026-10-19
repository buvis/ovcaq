"""Private retained-evidence inventory and purge implementation."""

from __future__ import annotations

import fcntl
import os
import stat
import warnings
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from ovcaq.paths import RuntimePaths
from ovcaq.runtime.registry import DuplicateRunError, RunLock
from ovcaq.runtime.session import (
    ActiveSessionError,
    EvidenceInventory,
    EvidenceItem,
    PurgePlan,
    RunObservation,
    _validate_identifier,
    observe_run,
)
from ovcaq.state.schema import MAX_STATE_BYTES, decode_json, validate_json_value


def _retained_stats(directory: int) -> tuple[int, float | None]:
    size = 0
    newest: float | None = None
    for name in os.listdir(directory):
        try:
            info = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if stat.S_ISREG(info.st_mode):
                size += info.st_size
                newest = (
                    max(newest, info.st_mtime) if newest is not None else info.st_mtime
                )
            elif stat.S_ISDIR(info.st_mode):
                child = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
                )
                try:
                    if not os.path.samestat(info, os.fstat(child)):
                        raise ValueError("evidence directory changed while opening")
                    child_size, child_newest = _retained_stats(child)
                    size += child_size
                    if child_newest is not None:
                        newest = (
                            max(newest, child_newest)
                            if newest is not None
                            else child_newest
                        )
                finally:
                    os.close(child)
        except FileNotFoundError:
            continue
    return size, newest


def _session_inventory(
    root: Path, sessions: int, active_id: str | None
) -> tuple[EvidenceItem, ...]:
    items: list[EvidenceItem] = []
    for name in sorted(os.listdir(sessions)):
        try:
            info = os.stat(name, dir_fd=sessions, follow_symlinks=False)
            if not stat.S_ISDIR(info.st_mode):
                continue
            child = os.open(
                name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=sessions
            )
            try:
                if not os.path.samestat(info, os.fstat(child)):
                    raise ValueError("session changed while opening")
                size, newest = _retained_stats(child)
            finally:
                os.close(child)
        except FileNotFoundError:
            continue
        modified = datetime.fromtimestamp(
            info.st_mtime if newest is None else newest, UTC
        ).isoformat()
        items.append(
            EvidenceItem(
                name,
                root / "sessions" / name,
                size,
                modified,
                name == active_id,
                info.st_dev,
                info.st_ino,
            )
        )
    return tuple(items)


def _inventory(
    root: Path, directory: int, *, active_id: str | None = None
) -> EvidenceInventory:
    total = 0
    for name in ("events.jsonl", "metrics.jsonl"):
        try:
            info = os.stat(name, dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            continue
        if stat.S_ISREG(info.st_mode):
            total += info.st_size
    try:
        sessions = os.open(
            "sessions", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
        )
    except FileNotFoundError:
        return EvidenceInventory(root, total, ())
    try:
        items = _session_inventory(root, sessions, active_id)
    finally:
        os.close(sessions)
    return EvidenceInventory(
        root, total + sum(item.size_bytes for item in items), items
    )


def inventory_evidence(paths: RuntimePaths, run: RunObservation) -> EvidenceInventory:
    try:
        directory = os.open(
            paths.runtime_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
    except FileNotFoundError:
        return EvidenceInventory(paths.runtime_root, 0, ())
    try:
        return _inventory(
            paths.runtime_root, directory, active_id=run.active_session_id
        )
    finally:
        os.close(directory)


def _purge_selector(
    session_id: str | None, before: datetime | None
) -> tuple[tuple[str, str], datetime | None]:
    if (session_id is None) == (before is None):
        raise ValueError("provide exactly one purge selector")
    if session_id is not None:
        _validate_identifier(session_id)
        return ("--session", session_id), before
    if not isinstance(before, datetime) or before.utcoffset() is None:
        raise ValueError("before must be a timezone-aware datetime")
    before = before.astimezone(UTC)
    return ("--before", before.isoformat().replace("+00:00", "Z")), before


def plan_purge(
    paths: RuntimePaths,
    *,
    session_id: str | None = None,
    before: datetime | None = None,
    inventory: EvidenceInventory | None = None,
) -> PurgePlan:
    selector, before = _purge_selector(session_id, before)
    if inventory is None:
        inventory = inventory_evidence(paths, observe_run(paths))
    selected = tuple(
        item
        for item in inventory.sessions
        if not item.active
        and (
            item.session_id == session_id
            if session_id is not None
            else before is not None
            and datetime.fromisoformat(item.modified_at) < before
        )
    )
    return PurgePlan(
        1,
        inventory.runtime_root,
        selected,
        sum(item.size_bytes for item in selected),
        (
            "ovcaq",
            "--root",
            str(paths.project_root),
            "logs",
            "purge",
            *selector,
            "--apply",
        ),
    )


def _remove_contents(directory: int) -> None:
    for name in os.listdir(directory):
        info = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            child = os.open(
                name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
            )
            try:
                if not os.path.samestat(info, os.fstat(child)):
                    raise ValueError("evidence directory changed before deletion")
                _remove_contents(child)
                if not os.path.samestat(
                    info, os.stat(name, dir_fd=directory, follow_symlinks=False)
                ):
                    raise ValueError("evidence directory changed during deletion")
                os.rmdir(name, dir_fd=directory)
            finally:
                os.close(child)
        else:
            os.unlink(name, dir_fd=directory)


def _open_purge_sessions(
    plan: PurgePlan, directory: int, stack: ExitStack
) -> tuple[int, list[tuple[EvidenceItem, int]]] | None:
    inventory = _inventory(plan.runtime_root, directory)
    current = {item.session_id: item for item in inventory.sessions}
    for item in plan.selected:
        _validate_identifier(item.session_id)
        observed = current.get(item.session_id)
        if (
            observed is None
            or item.path != plan.runtime_root / "sessions" / item.session_id
            or (item.device, item.inode) != (observed.device, observed.inode)
        ):
            raise ValueError("selected session identity changed")
    if not plan.selected:
        return None
    sessions = os.open(
        "sessions", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
    )
    stack.callback(os.close, sessions)
    opened: list[tuple[EvidenceItem, int]] = []
    for item in plan.selected:
        descriptor = os.open(
            item.session_id,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=sessions,
        )
        stack.callback(os.close, descriptor)
        info = os.fstat(descriptor)
        if (info.st_dev, info.st_ino) != (item.device, item.inode):
            raise ValueError("selected session changed while opening")
        opened.append((item, descriptor))
    return sessions, opened


def _remove_aggregate_row(row: bytes, name: str, selected_ids: set[str]) -> bool:
    try:
        if len(row) > MAX_STATE_BYTES:
            raise ValueError("aggregate row exceeds size limit")
        record = decode_json(row.decode("utf-8"), source=name)
        if not isinstance(record, dict) or set(record) != {
            "schema_version",
            "session_id",
            "payload",
        }:
            raise ValueError("invalid aggregate fields")
        if type(record["schema_version"]) is not int or record["schema_version"] != 1:
            raise ValueError("invalid aggregate version")
        _validate_identifier(record["session_id"])
        validate_json_value(record["payload"], "payload")
        return cast(str, record["session_id"]) in selected_ids
    except (ValueError, TypeError):
        warnings.warn(
            f"Preserving invalid aggregate row in {name}",
            RuntimeWarning,
            stacklevel=4,
        )
        return False


def _stage_aggregates(
    directory: int, selected_ids: set[str], temporary_names: list[str]
) -> list[tuple[str, str, os.stat_result]]:
    staged: list[tuple[str, str, os.stat_result]] = []
    for name in ("events.jsonl", "metrics.jsonl"):
        try:
            info = os.stat(name, dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(info.st_mode):
            continue
        source_fd = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
        )
        with os.fdopen(source_fd, "rb") as source:
            if not os.path.samestat(info, os.fstat(source.fileno())):
                raise ValueError("aggregate changed while opening")
            temporary = f".{name}.{uuid4().hex}"
            target_fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            temporary_names.append(temporary)
            with os.fdopen(target_fd, "wb") as target:
                while row := source.readline(MAX_STATE_BYTES + 1):
                    if not _remove_aggregate_row(row, name, selected_ids):
                        target.write(row)
                    if len(row) > MAX_STATE_BYTES:
                        while not row.endswith(b"\n"):
                            row = source.readline(MAX_STATE_BYTES + 1)
                            if not row:
                                break
                            target.write(row)
                target.flush()
                os.fsync(target.fileno())
        staged.append((name, temporary, info))
    return staged


def _commit_purge(
    directory: int,
    sessions: int,
    opened: list[tuple[EvidenceItem, int]],
    staged: list[tuple[str, str, os.stat_result]],
) -> None:
    os.fsync(directory)
    os.fsync(sessions)
    for name, _, info in staged:
        aggregate_info = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if not os.path.samestat(info, aggregate_info) or (
            info.st_size,
            info.st_mtime_ns,
        ) != (aggregate_info.st_size, aggregate_info.st_mtime_ns):
            raise ValueError("aggregate changed before replacement")
    for item, _ in opened:
        info = os.stat(item.session_id, dir_fd=sessions, follow_symlinks=False)
        if (info.st_dev, info.st_ino) != (item.device, item.inode):
            raise ValueError("session changed before deletion")
    for name, temporary, _ in staged:
        os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
    for item, descriptor in opened:
        _remove_contents(descriptor)
        os.rmdir(item.session_id, dir_fd=sessions)
    os.fsync(sessions)
    os.fsync(directory)


def _acquire_purge_locks(directory: int, stack: ExitStack) -> list[tuple[str, int]]:
    locks: list[tuple[str, int]] = []
    for name in ("run.lock", "retention.lock"):
        descriptor = os.open(
            name,
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            0o600,
            dir_fd=directory,
        )
        stack.enter_context(RunLock(descriptor))
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(f"Purge lock is not a regular file: {name}")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            if name == "run.lock":
                raise ActiveSessionError(
                    "cannot purge while a run is active"
                ) from error
            raise DuplicateRunError("retention lock is already held") from error
        if not os.path.samestat(
            info, os.stat(name, dir_fd=directory, follow_symlinks=False)
        ):
            raise OSError("purge lock changed during acquisition")
        os.fchmod(descriptor, 0o600)
        locks.append((name, descriptor))
    return locks


def _verify_purge_ancestry(
    root: Path,
    root_info: os.stat_result,
    directory: int,
    sessions: int,
    locks: list[tuple[str, int]],
) -> None:
    if not os.path.samestat(root_info, root.lstat()) or not os.path.samestat(
        os.fstat(sessions),
        os.stat("sessions", dir_fd=directory, follow_symlinks=False),
    ):
        raise ValueError("purge ancestry changed before deletion")
    for name, descriptor in locks:
        if not os.path.samestat(
            os.fstat(descriptor),
            os.stat(name, dir_fd=directory, follow_symlinks=False),
        ):
            raise OSError("purge lock changed before deletion")


def apply_purge(plan: PurgePlan) -> tuple[Path, ...]:
    root = plan.runtime_root
    with ExitStack() as stack:
        root_info = root.lstat()
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, directory)
        if not os.path.samestat(root_info, os.fstat(directory)):
            raise ValueError("runtime root changed while opening")
        locks = _acquire_purge_locks(directory, stack)
        if not os.path.samestat(root_info, root.lstat()):
            raise ValueError("runtime root changed during lock acquisition")
        selected = _open_purge_sessions(plan, directory, stack)
        if selected is None:
            return ()
        sessions, opened = selected
        temporary_names: list[str] = []
        try:
            staged = _stage_aggregates(
                directory, {item.session_id for item in plan.selected}, temporary_names
            )
            _verify_purge_ancestry(root, root_info, directory, sessions, locks)
            _commit_purge(directory, sessions, opened, staged)
        finally:
            for temporary in temporary_names:
                try:
                    os.unlink(temporary, dir_fd=directory)
                except FileNotFoundError:
                    pass
        return tuple(item.path for item in plan.selected)
