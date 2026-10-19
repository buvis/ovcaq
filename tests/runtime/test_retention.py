from __future__ import annotations

import builtins
import errno
import fcntl
import io
import json
import os
import select
import stat
import subprocess
import sys
import warnings
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Self

import pytest

from ovcaq.paths import RuntimePaths, ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.registry import process_identity, process_matches
from ovcaq.runtime.session import (
    ActiveSessionError,
    EvidenceInventory,
    EvidenceItem,
    PurgePlan,
    apply_purge,
    inventory_evidence,
    plan_purge,
)
from ovcaq.state.schema import MAX_STATE_BYTES


def _reject(expected: type[BaseException], operation: Callable[[], object]) -> None:
    with pytest.raises(expected):
        operation()


def _layout(tmp_path: Path) -> tuple[RuntimePaths, Path, Path]:
    project = tmp_path / "project with spaces"
    project.mkdir()
    paths = resolve_runtime_paths(project, xdg_state_home=tmp_path / "state")
    ensure_runtime_layout(paths)
    return paths, project, inventory_evidence(paths).runtime_root


def _session(root: Path, name: str, payload: bytes = b"retained") -> Path:
    directory = root / "sessions" / name
    directory.mkdir(parents=True, mode=0o700)
    (directory / "raw.jsonl").write_bytes(payload)
    return directory


def _snapshot(root: Path) -> dict[Path, tuple[int, int, int, bytes | str | None]]:
    result = {}
    for path in [root, *sorted(root.rglob("*"))]:
        info = path.lstat()
        content = None
        if stat.S_ISREG(info.st_mode):
            content = path.read_bytes()
        elif stat.S_ISLNK(info.st_mode):
            content = os.readlink(path)
        result[path] = (info.st_ino, info.st_mode, info.st_mtime_ns, content)
    return result


def _row(session_id: str, payload: object = None) -> bytes:
    return (
        json.dumps(
            {"schema_version": 1, "session_id": session_id, "payload": payload}
        ).encode()
        + b"\n"
    )


@contextmanager
def _held_lock(path: Path) -> Iterator[int]:
    code = """
import fcntl, os, sys
with open(sys.argv[1], "ab") as handle:
    fcntl.flock(handle, fcntl.LOCK_EX)
    print(os.getpid(), flush=True)
    sys.stdin.buffer.read(1)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", code, str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout is not None
        assert select.select([process.stdout], [], [], 5)[0], "lock holder timed out"
        yield int(process.stdout.readline())
    finally:
        if process.poll() is None:
            process.communicate("x", timeout=5)
        else:
            process.communicate(timeout=5)
        assert process.returncode == 0


def _assert_inventory_item(item: EvidenceItem, directory: Path, timestamp: int) -> None:
    assert isinstance(item, EvidenceItem)
    assert item.path == directory
    assert (item.device, item.inode) == (
        directory.stat().st_dev,
        directory.stat().st_ino,
    )
    assert datetime.fromisoformat(item.modified_at) == datetime.fromtimestamp(
        timestamp, UTC
    )
    assert datetime.fromisoformat(item.modified_at).utcoffset() == timedelta(0)
    assert item.active is False


def test_inventory_counts_regular_files_without_following_links_or_expiring_old_data(
    tmp_path: Path,
) -> None:
    paths, _, root = _layout(tmp_path)
    later = _session(root, "z-last", b"abc")
    earlier = _session(root, "a-first", b"\xffmalformed\n")
    nested = earlier / "nested"
    nested.mkdir()
    (nested / "extra").write_bytes(b"12345")
    empty = root / "sessions" / "empty"
    empty.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel").write_bytes(b"never count or delete this")
    (earlier / "link").symlink_to(outside, target_is_directory=True)
    (earlier / "dangling").symlink_to(tmp_path / "absent")
    os.mkfifo(earlier / "fifo")
    (root / "sessions" / "linked-session").symlink_to(outside)
    (root / "sessions" / "loose-file").write_bytes(b"not a session")
    os.mkfifo(root / "sessions" / "loose-fifo")
    (root / "events.jsonl").write_bytes(b"events\n")
    (root / "metrics.jsonl").write_bytes(b"metrics\n")
    for file, timestamp in (
        (earlier / "raw.jsonl", 100),
        (nested / "extra", 200),
        (later / "raw.jsonl", 300),
        (empty, 400),
        (earlier, 999),
    ):
        os.utime(file, (timestamp, timestamp))
    before = _snapshot(root)

    inventory = inventory_evidence(paths)

    assert isinstance(inventory, EvidenceInventory)
    assert tuple(item.session_id for item in inventory.sessions) == (
        "a-first",
        "empty",
        "z-last",
    )
    assert tuple(item.size_bytes for item in inventory.sessions) == (16, 0, 3)
    assert inventory.total_bytes == 16 + 3 + len(b"events\nmetrics\n")
    for item, directory, timestamp in zip(
        inventory.sessions, (earlier, empty, later), (200, 400, 300), strict=True
    ):
        _assert_inventory_item(item, directory, timestamp)
    assert inventory_evidence(paths) == inventory
    assert _snapshot(root) == before
    assert (outside / "sentinel").read_bytes() == b"never count or delete this"


@pytest.mark.parametrize("obstacle", ["symlink", "fifo", "directory"])
def test_inventory_excludes_nonregular_root_aggregates(
    tmp_path: Path, obstacle: str
) -> None:
    paths, _, root = _layout(tmp_path)
    _session(root, "kept", b"abc")
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    for name in ("events.jsonl", "metrics.jsonl"):
        path = root / name
        if obstacle == "symlink":
            path.symlink_to(outside)
        elif obstacle == "fifo":
            os.mkfifo(path)
        else:
            path.mkdir()
    before = _snapshot(root)
    assert inventory_evidence(paths).total_bytes == 3
    assert _snapshot(root) == before
    assert outside.read_bytes() == b"outside"


def test_inventory_tolerates_a_file_vanishing_after_directory_enumeration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _, root = _layout(tmp_path)
    directory = _session(root, "kept", b"abc")
    vanished = directory / "vanishing"
    vanished.write_bytes(b"gone")
    real_scandir = os.scandir
    real_listdir = os.listdir

    def vanishing_listdir(path: object) -> list[str]:
        entries = real_listdir(path)
        if "vanishing" in entries:
            vanished.unlink(missing_ok=True)
        return entries

    class VanishingScan:
        def __init__(self, path: object) -> None:
            with real_scandir(path) as entries:
                self.entries = list(entries)
            if any(entry.name == "vanishing" for entry in self.entries):
                vanished.unlink(missing_ok=True)
            self.iterator = iter(self.entries)

        def __iter__(self) -> VanishingScan:
            return self

        def __next__(self) -> os.DirEntry[str]:
            return next(self.iterator)

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

        def close(self) -> None:
            self.entries.clear()

    with monkeypatch.context() as patch:
        patch.setattr(os, "scandir", VanishingScan)
        patch.setattr(os, "listdir", vanishing_listdir)
        inventory = inventory_evidence(paths)
    assert not vanished.exists()
    assert tuple(item.session_id for item in inventory.sessions) == ("kept",)
    assert inventory.sessions[0].size_bytes == inventory.total_bytes == 3
    assert (directory / "raw.jsonl").read_bytes() == b"abc"


def test_plans_are_immutable_pure_identity_bearing_and_render_exact_selectors(
    tmp_path: Path,
) -> None:
    paths, project, root = _layout(tmp_path)
    for name, timestamp in (
        ("z-old", 99),
        ("a-old", 98),
        ("boundary", 100),
        ("newer", 200),
    ):
        directory = _session(root, name, name.encode())
        os.utime(directory / "raw.jsonl", (timestamp, timestamp))
    before = _snapshot(root)
    inventory = inventory_evidence(paths)
    cutoff = datetime.fromtimestamp(100, UTC)
    plan = plan_purge(paths, before=cutoff)
    assert isinstance(plan, PurgePlan)
    assert plan.schema_version == 1
    assert plan.runtime_root == root
    assert plan.selected == tuple(
        item for item in inventory.sessions if item.session_id in {"a-old", "z-old"}
    )
    assert plan.total_bytes == len(b"z-olda-old")
    assert plan.command == (
        "ovcaq",
        "--root",
        str(project),
        "logs",
        "purge",
        "--before",
        "1970-01-01T00:01:40Z",
        "--apply",
    )
    _assert_alternate_plan_selectors(paths, project, inventory, cutoff, plan)
    for value, field in (
        (inventory, "total_bytes"),
        (inventory.sessions[0], "size_bytes"),
        (plan, "total_bytes"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(value, field, 999)
    assert _snapshot(root) == before


def _assert_alternate_plan_selectors(
    paths: RuntimePaths,
    project: Path,
    inventory: EvidenceInventory,
    cutoff: datetime,
    plan: PurgePlan,
) -> None:
    offset_cutoff = datetime.fromisoformat("1970-01-01T01:01:40+01:00")
    offset_plan = plan_purge(paths, before=offset_cutoff)
    assert offset_plan.selected == plan.selected
    assert offset_plan.total_bytes == plan.total_bytes
    assert offset_plan.command == plan.command
    assert all(
        item.session_id != "newer"
        for selected_plan in (plan, offset_plan)
        for item in selected_plan.selected
    )
    by_id = plan_purge(paths, session_id="boundary")
    assert by_id.selected == (inventory.sessions[1],)
    assert by_id.total_bytes == len(b"boundary")
    assert by_id.command == (
        "ovcaq",
        "--root",
        str(project),
        "logs",
        "purge",
        "--session",
        "boundary",
        "--apply",
    )
    fractional = cutoff.replace(microsecond=123456)
    assert plan_purge(paths, before=fractional).command[-2:] == (
        "1970-01-01T00:01:40.123456Z",
        "--apply",
    )


@pytest.mark.parametrize(
    "selectors",
    [
        {},
        {"session_id": "kept", "before": datetime(2026, 1, 1, tzinfo=UTC)},
        {"session_id": ""},
        {"session_id": "."},
        {"session_id": ".."},
        {"session_id": "../kept"},
        {"session_id": "/kept"},
        {"session_id": "a/b"},
        {"session_id": "a\x00b"},
        {"session_id": 1},
        {"before": datetime(2026, 1, 1)},  # noqa: DTZ001 - reject naive cutoffs
        {"before": "2026-01-01T00:00:00Z"},
        {"before": True},
    ],
)
def test_invalid_selectors_fail_without_mutating_evidence(
    tmp_path: Path, selectors: dict[str, object]
) -> None:
    paths, _, root = _layout(tmp_path)
    _session(root, "kept")
    before = _snapshot(root)
    _reject(ValueError, lambda: plan_purge(paths, **selectors))
    assert _snapshot(root) == before


@pytest.mark.parametrize("selector", ["session", "before"])
def test_no_match_preview_and_apply_preserve_all_evidence(
    tmp_path: Path, selector: str
) -> None:
    paths, _, root = _layout(tmp_path)
    directory = _session(root, "kept")
    aggregate = root / "events.jsonl"
    aggregate.write_bytes(_row("kept", 1))
    before = _snapshot(root)
    plan = (
        plan_purge(paths, session_id="missing")
        if selector == "session"
        else plan_purge(paths, before=datetime(1970, 1, 1, tzinfo=UTC))
    )
    assert plan.selected == ()
    assert plan.total_bytes == 0
    assert _snapshot(root) == before
    assert apply_purge(plan) == ()
    assert (directory / "raw.jsonl").read_bytes() == b"retained"
    assert aggregate.read_bytes() == _row("kept", 1)
    assert tuple(item.session_id for item in inventory_evidence(paths).sessions) == (
        "kept",
    )


@pytest.mark.parametrize(
    "metadata", ["matching", "other", "stale", "missing", "malformed", "future"]
)
def test_activity_requires_matching_valid_metadata_but_any_live_lock_blocks_apply(
    tmp_path: Path, metadata: str
) -> None:
    paths, _, root = _layout(tmp_path)
    _session(root, "selected")
    _session(root, "other")
    plan = plan_purge(paths, session_id="selected")
    with _held_lock(root / "run.lock") as pid:
        identity = process_identity(pid)
        assert identity is not None
        assert process_matches(identity)
        stale = replace(identity, started="stale-process-start-token")
        assert not process_matches(stale)
        record = {
            "schema_version": 2 if metadata == "future" else 1,
            "run_id": "run-1",
            "session_id": "other" if metadata == "other" else "selected",
            "agent": "command",
            "pid": pid,
            "process_start": stale.started if metadata == "stale" else identity.started,
            "started_at": "2026-01-01T00:00:00Z",
        }
        run = root / "run.json"
        if metadata != "missing":
            run.write_text("{" if metadata == "malformed" else json.dumps(record))
        before = _snapshot(root)
        inventory = inventory_evidence(paths)
        assert {item.session_id for item in inventory.sessions if item.active} == (
            {"selected"}
            if metadata == "matching"
            else {"other"}
            if metadata == "other"
            else set()
        )
        cutoff = plan_purge(paths, before=datetime(9999, 1, 1, tzinfo=UTC))
        assert all(not item.active for item in cutoff.selected)
        assert len(cutoff.selected) == (1 if metadata in {"matching", "other"} else 2)
        with pytest.raises(ActiveSessionError):
            apply_purge(plan)
        assert _snapshot(root) == before
    assert all(not item.active for item in inventory_evidence(paths).sessions)
    assert not process_matches(identity)


def _assert_lock_held(path: Path) -> None:
    with path.open("rb") as handle, pytest.raises(BlockingIOError):
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)


def test_runtime_root_swap_cannot_bypass_the_original_live_run_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _, root = _layout(tmp_path)
    selected = _session(root, "selected", b"active raw evidence\x00\xff")
    aggregate = root / "events.jsonl"
    aggregate.write_bytes(_row("selected", "active aggregate evidence"))
    original_bytes = (selected / "raw.jsonl").read_bytes()
    aggregate_bytes = aggregate.read_bytes()
    plan = plan_purge(paths, session_id="selected")
    original = tmp_path / "original-runtime"
    real_open = os.open
    swapped = False

    def swap_root_before_lock_open(
        path: str | Path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal swapped
        if Path(path).name == "run.lock" and not swapped:
            swapped = True
            root.rename(original)
            root.mkdir(mode=0o700)
            _session(root, "selected", b"replacement session evidence")
            (root / "run.lock").touch(mode=0o600)
            aggregate.write_bytes(_row("selected", "replacement aggregate evidence"))
        return real_open(path, flags, mode, dir_fd=dir_fd)

    with _held_lock(root / "run.lock"):
        original_lock = (root / "run.lock").stat()
        with monkeypatch.context() as patch:
            patch.setattr(os, "open", swap_root_before_lock_open)
            _reject(ActiveSessionError, lambda: apply_purge(plan))
        assert original.is_dir()
        assert os.path.samestat(original_lock, (original / "run.lock").stat())
        _assert_lock_held(original / "run.lock")
        assert (original / "sessions" / "selected" / "raw.jsonl").read_bytes() == (
            original_bytes
        )
        assert (original / "events.jsonl").read_bytes() == aggregate_bytes
        assert (selected / "raw.jsonl").read_bytes() == b"replacement session evidence"
        assert aggregate.read_bytes() == _row(
            "selected", "replacement aggregate evidence"
        )


@pytest.mark.parametrize("replacement", ["directory", "symlink", "missing"])
def test_every_selected_identity_is_revalidated_before_any_evidence_is_deleted(
    tmp_path: Path, replacement: str
) -> None:
    paths, _, root = _layout(tmp_path)
    first = _session(root, "a-first")
    last = _session(root, "z-last")
    aggregate = root / "events.jsonl"
    aggregate.write_bytes(_row("a-first") + _row("z-last"))
    plan = plan_purge(paths, before=datetime(9999, 1, 1, tzinfo=UTC))
    moved = tmp_path / "original"
    last.rename(moved)
    if replacement == "directory":
        _session(root, "z-last", b"replacement")
    elif replacement == "symlink":
        last.symlink_to(moved, target_is_directory=True)
    before = aggregate.read_bytes()
    _reject(ValueError, lambda: apply_purge(plan))
    assert (first / "raw.jsonl").read_bytes() == b"retained"
    assert (moved / "raw.jsonl").read_bytes() == b"retained"
    assert aggregate.read_bytes() == before
    if replacement == "directory":
        assert (last / "raw.jsonl").read_bytes() == b"replacement"
    elif replacement == "symlink":
        assert last.is_symlink()
    else:
        assert not last.exists()


def test_apply_removes_only_selected_sessions_and_valid_matching_aggregate_rows(
    tmp_path: Path,
) -> None:
    paths, _, root = _layout(tmp_path)
    selected = _session(root, "selected")
    kept = _session(root, "kept", b"keep me")
    malformed = [
        b"{broken\n",
        b"\xff\n",
        b'{"schema_version":1,"session_id":"selected","payload":0,"payload":1}\n',
        b'{"schema_version":2,"session_id":"selected","payload":null}\n',
        b'{"schema_version":true,"session_id":"selected","payload":null}\n',
        b'{"schema_version":1,"session_id":"selected","payload":null,"extra":1}\n',
        b'{"schema_version":1,"session_id":"selected"}\n',
        b'{"schema_version":1,"session_id":"../selected","payload":null}\n',
        b"[]\n",
        _row("selected", "x" * MAX_STATE_BYTES),
    ]
    unrelated = b' {"payload": {"session_id":"selected"}, "session_id":"kept", "schema_version":1}\r\n'
    final = _row("kept", "no final newline").rstrip(b"\n")
    retained = unrelated + b"".join(malformed) + final
    for name in ("events.jsonl", "metrics.jsonl"):
        (root / name).write_bytes(_row("selected", {"value": 1}) + retained)
    plan = plan_purge(paths, session_id="selected")
    with warnings.catch_warnings(record=True) as reports:
        warnings.simplefilter("always")
        assert apply_purge(plan) == (selected,)
    assert len([report for report in reports if report.category is RuntimeWarning]) == (
        2 * len(malformed)
    )
    assert not selected.exists()
    assert (kept / "raw.jsonl").read_bytes() == b"keep me"
    for name in ("events.jsonl", "metrics.jsonl"):
        assert (root / name).read_bytes() == retained
    assert (root / "retention.lock").is_file()


class _BoundedReader:
    def __init__(self, handle: BinaryIO) -> None:
        self.handle = handle

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.handle.close()

    def __getattr__(self, name: str) -> object:
        return getattr(self.handle, name)

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> bytes:
        row = self.readline()
        if not row:
            raise StopIteration
        return row

    def read(self, size: int = -1) -> bytes:
        assert 0 <= size <= MAX_STATE_BYTES + 1, (
            "aggregate evidence read must be bounded by MAX_STATE_BYTES + 1"
        )
        return self.handle.read(size)

    def readline(self, size: int = -1) -> bytes:
        assert 0 <= size <= MAX_STATE_BYTES + 1, (
            "aggregate evidence line read must be bounded by MAX_STATE_BYTES + 1"
        )
        return self.handle.readline(size)

    def readlines(self, hint: int = -1) -> list[bytes]:
        raise AssertionError("readlines can read an unbounded evidence row")


@pytest.mark.parametrize("aggregate_name", ["events.jsonl", "metrics.jsonl"])
def test_purge_retains_oversized_newline_free_evidence_using_bounded_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, aggregate_name: str
) -> None:
    paths, _, root = _layout(tmp_path)
    selected = _session(root, "selected")
    kept = _session(root, "kept", b"keep this session")
    aggregate = root / aggregate_name
    malformed = b"\xff" + b"x" * (2 * MAX_STATE_BYTES + 257)
    aggregate.write_bytes(_row("selected") + malformed)
    original = aggregate.stat()
    plan = plan_purge(paths, session_id="selected")
    real_builtin_open, real_io_open = builtins.open, io.open

    def guard(handle: BinaryIO) -> BinaryIO | _BoundedReader:
        if os.path.samestat(original, os.fstat(handle.fileno())) and handle.readable():
            return _BoundedReader(handle)
        return handle

    def bounded_builtin_open(*args: object, **kwargs: object) -> object:
        return guard(real_builtin_open(*args, **kwargs))

    def bounded_io_open(*args: object, **kwargs: object) -> object:
        return guard(real_io_open(*args, **kwargs))

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", bounded_builtin_open)
        patch.setattr(io, "open", bounded_io_open)
        with warnings.catch_warnings(record=True) as reports:
            warnings.simplefilter("always")
            assert apply_purge(plan) == (selected,)
    assert any(report.category is RuntimeWarning for report in reports)
    assert not selected.exists()
    assert (kept / "raw.jsonl").read_bytes() == b"keep this session"
    assert aggregate.stat().st_size == len(malformed)
    with aggregate.open("rb") as handle:
        for offset in range(0, len(malformed), 65536):
            assert handle.read(65536) == malformed[offset : offset + 65536]
        assert handle.read(1) == b""


def test_replacement_during_apply_fails_without_following_the_new_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _, root = _layout(tmp_path)
    selected = _session(root, "selected")
    moved = tmp_path / "original"
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_bytes(b"outside evidence")
    aggregate = root / "events.jsonl"
    aggregate.write_bytes(_row("selected"))
    plan = plan_purge(paths, session_id="selected")
    real_open = os.open

    def replace_directory(
        path: str | Path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        if Path(path).name == "selected" and not moved.exists():
            selected.rename(moved)
            selected.symlink_to(outside, target_is_directory=True)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    with monkeypatch.context() as patch:
        patch.setattr(os, "open", replace_directory)
        _reject(OSError, lambda: apply_purge(plan))
    assert selected.is_symlink()
    assert (moved / "raw.jsonl").read_bytes() == b"retained"
    assert sentinel.read_bytes() == b"outside evidence"
    assert aggregate.read_bytes() == _row("selected")


def test_cutoff_apply_returns_deleted_paths_in_session_order_and_keeps_newer_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _, root = _layout(tmp_path)
    last = _session(root, "z-last")
    first = _session(root, "a-first")
    kept = _session(root, "new")
    for directory in (first, last):
        os.utime(directory / "raw.jsonl", (1, 1))
    plan = plan_purge(paths, before=datetime.fromtimestamp(2, UTC))
    real_fsync = os.fsync
    synced_after_deletion = []

    def sync(descriptor: int) -> None:
        real_fsync(descriptor)
        info = os.fstat(descriptor)
        if stat.S_ISDIR(info.st_mode) and not first.exists() and not last.exists():
            with (
                (root / "retention.lock").open("rb") as handle,
                pytest.raises(BlockingIOError),
            ):
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            synced_after_deletion.append((info.st_dev, info.st_ino))

    monkeypatch.setattr(os, "fsync", sync)
    assert apply_purge(plan) == (first, last)
    assert not first.exists()
    assert not last.exists()
    assert (kept / "raw.jsonl").read_bytes() == b"retained"
    assert synced_after_deletion


@pytest.mark.parametrize("failure", [errno.EIO, errno.ENOSPC])
def test_durability_failure_preserves_session_and_aggregate_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: int
) -> None:
    paths, _, root = _layout(tmp_path)
    selected = _session(root, "selected")
    aggregate = root / "events.jsonl"
    content = _row("selected") + _row("kept")
    aggregate.write_bytes(content)
    plan = plan_purge(paths, session_id="selected")

    def fail_sync(_descriptor: int) -> None:
        raise OSError(failure, "injected durability failure")

    with monkeypatch.context() as patch:
        patch.setattr(os, "fsync", fail_sync)
        _reject(OSError, lambda: apply_purge(plan))
    assert (selected / "raw.jsonl").read_bytes() == b"retained"
    assert aggregate.read_bytes() == content


def test_retention_lock_serializes_apply_and_remains_after_release(
    tmp_path: Path,
) -> None:
    paths, project, root = _layout(tmp_path)
    selected = _session(root, "selected")
    lock = root / "retention.lock"
    code = """import pathlib, sys
from ovcaq.paths import resolve_runtime_paths
from ovcaq.runtime.registry import DuplicateRunError
from ovcaq.runtime.session import plan_purge, apply_purge
paths = resolve_runtime_paths(pathlib.Path(sys.argv[1]), xdg_state_home=pathlib.Path(sys.argv[2]))
plan = plan_purge(paths, session_id="selected")
print("ready", flush=True)
try:
    apply_purge(plan)
except DuplicateRunError:
    sys.exit(3)
"""
    with _held_lock(lock):
        identity = lock.stat()
        process = subprocess.Popen(
            [sys.executable, "-c", code, str(project), str(tmp_path / "state")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            assert process.stdout is not None
            assert select.select([process.stdout], [], [], 5)[0]
            assert process.stdout.readline() == "ready\n"
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                pass
            assert (selected / "raw.jsonl").read_bytes() == b"retained"
        except BaseException:
            process.kill()
            process.communicate(timeout=5)
            raise
    _, stderr = process.communicate(timeout=5)
    assert process.returncode in (0, 3), stderr
    if process.returncode == 3:
        assert (selected / "raw.jsonl").read_bytes() == b"retained"
        assert apply_purge(plan_purge(paths, session_id="selected")) == (selected,)
    assert not selected.exists()
    assert os.path.samestat(identity, lock.stat())
    with lock.open("rb") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(handle, fcntl.LOCK_UN)
