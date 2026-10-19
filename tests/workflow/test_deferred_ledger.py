from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from saga_support import (
    PRD,
)

from ovcaq.workflow import _files as files_module
from ovcaq.workflow.records import (
    DeferBoundary,
    record_defer,
)


@pytest.mark.parametrize("boundary", tuple(DeferBoundary))
@pytest.mark.parametrize("replacement", ("directory", "symlink"))
def test_defer_directory_replacement_fails_then_replays_once(
    tmp_path: Path, boundary: DeferBoundary, replacement: str
) -> None:
    deferred = tmp_path / "deferred"
    relocated = tmp_path / "relocated"
    external = tmp_path / "external"
    external.mkdir()
    sentinel = external / "sentinel"
    sentinel.write_text("untouched", encoding="utf-8")
    first = {"op_id": "first", "detail": "retained"}
    second = {"op_id": "second", "detail": "new"}
    path = record_defer(tmp_path, PRD, "batch-1", first)

    def replace(reached: DeferBoundary) -> None:
        if reached is boundary:
            deferred.rename(relocated)
            if replacement == "directory":
                deferred.mkdir()
            else:
                deferred.symlink_to(external, target_is_directory=True)

    with pytest.raises(OSError, match="deferred directory identity changed"):
        record_defer(tmp_path, PRD, "batch-1", second, boundary_hook=replace)

    assert not path.exists()
    assert sorted(item.name for item in external.iterdir()) == ["sentinel"]
    assert sentinel.read_text(encoding="utf-8") == "untouched"
    assert not list(relocated.glob("*.tmp"))
    if replacement == "directory":
        deferred.rmdir()
    else:
        deferred.unlink()
    relocated.rename(deferred)
    record_defer(tmp_path, PRD, "batch-1", second)
    before = path.read_bytes()
    record_defer(tmp_path, PRD, "batch-1", second)
    assert path.read_bytes() == before
    assert [item["op_id"] for item in json.loads(before)["items"]] == [
        "first",
        "second",
    ]


def _directory_replacement_io(
    deferred: Path, relocated: Path, boundary: str, original_inode: int
) -> tuple[object, object, object]:
    actual_open = os.open
    actual_fsync = os.fsync
    swapped = False

    def replace_directory() -> None:
        nonlocal swapped
        deferred.rename(relocated)
        deferred.mkdir()
        swapped = True

    def open_at(
        name: str | os.PathLike[str],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        if (
            boundary == "temporary-create"
            and str(name).endswith(".tmp")
            and not swapped
        ):
            replace_directory()
        return actual_open(name, flags, mode, dir_fd=dir_fd)

    def fsync_at(descriptor: int) -> None:
        if (
            boundary == "directory-fsync"
            and os.fstat(descriptor).st_ino == original_inode
            and not swapped
        ):
            replace_directory()
        actual_fsync(descriptor)

    return open_at, fsync_at, lambda: swapped


@pytest.mark.parametrize("boundary", ("temporary-create", "directory-fsync"))
def test_defer_io_stays_bound_to_opened_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    deferred = tmp_path / "deferred"
    relocated = tmp_path / "relocated"
    record = {"op_id": "first", "detail": "retained"}
    path = record_defer(tmp_path, PRD, "batch-1", record)
    original_inode = deferred.stat().st_ino
    open_at, fsync_at, was_swapped = _directory_replacement_io(
        deferred, relocated, boundary, original_inode
    )

    with monkeypatch.context() as patches:
        patches.setattr(os, "open", open_at)
        patches.setattr(os, "fsync", fsync_at)
        with pytest.raises(OSError, match="deferred directory identity changed"):
            record_defer(tmp_path, PRD, "batch-1", {"op_id": "second"})

    assert was_swapped()
    assert list(deferred.iterdir()) == []
    assert not list(relocated.glob("*.tmp"))
    deferred.rmdir()
    relocated.rename(deferred)
    record_defer(tmp_path, PRD, "batch-1", {"op_id": "second"})
    assert [item["op_id"] for item in json.loads(path.read_bytes())["items"]] == [
        "first",
        "second",
    ]


def test_creating_deferred_fsyncs_its_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    synced_inodes: list[int] = []
    real_fsync = files_module._fsync_directory_descriptor

    def spy_fsync(descriptor: int) -> None:
        synced_inodes.append(os.fstat(descriptor).st_ino)
        real_fsync(descriptor)

    monkeypatch.setattr(files_module, "_fsync_directory_descriptor", spy_fsync)
    record_defer(
        tmp_path,
        PRD,
        "batch-1",
        {"op_id": "defer-1", "type": "decision", "detail": "later"},
    )

    assert tmp_path.stat().st_ino in synced_inodes


def test_record_defer_requires_and_deduplicates_operation_ids(tmp_path: Path) -> None:
    record = {"op_id": "defer-1", "type": "decision", "detail": "later"}

    path = record_defer(tmp_path, PRD, "batch-1", record)
    first = path.read_bytes()
    assert record == {"op_id": "defer-1", "type": "decision", "detail": "later"}
    assert json.loads(first) == {
        "batch_id": "batch-1",
        "items": [
            {
                "detail": "later",
                "op_id": "defer-1",
                "prd": PRD,
                "type": "decision",
            }
        ],
    }

    assert record_defer(tmp_path, PRD, "batch-1", record) == path
    assert path.read_bytes() == first


def test_record_defer_rejects_conflicting_operation_id_without_byte_changes(
    tmp_path: Path,
) -> None:
    original = {"op_id": "defer-1", "type": "decision", "detail": "later"}
    path = record_defer(tmp_path, PRD, "batch-1", original)
    before = path.read_bytes()

    with pytest.raises(ValueError, match="conflicting deferred record"):
        record_defer(
            tmp_path,
            PRD,
            "batch-1",
            {**original, "detail": "different"},
        )

    assert path.read_bytes() == before


def test_record_defer_retry_before_atomic_publish_preserves_existing_bytes(
    tmp_path: Path,
) -> None:
    first = {"op_id": "defer-1", "type": "decision", "detail": "first"}
    second = {"op_id": "defer-2", "type": "decision", "detail": "second"}
    path = record_defer(tmp_path, PRD, "batch-1", first)
    before = path.read_bytes()

    def interrupt(boundary: DeferBoundary) -> None:
        if boundary is DeferBoundary.BEFORE_PUBLISH:
            raise RuntimeError("before publish")

    with pytest.raises(RuntimeError, match="before publish"):
        record_defer(tmp_path, PRD, "batch-1", second, boundary_hook=interrupt)

    assert path.read_bytes() == before
    record_defer(tmp_path, PRD, "batch-1", second)
    assert [item["op_id"] for item in json.loads(path.read_bytes())["items"]] == [
        "defer-1",
        "defer-2",
    ]


def test_record_defer_retry_after_atomic_publish_is_byte_exact_noop(
    tmp_path: Path,
) -> None:
    record = {"op_id": "defer-1", "type": "decision", "detail": "later"}

    def interrupt(boundary: DeferBoundary) -> None:
        if boundary is DeferBoundary.AFTER_PUBLISH:
            raise RuntimeError("after publish")

    with pytest.raises(RuntimeError, match="after publish"):
        record_defer(
            tmp_path,
            PRD,
            "batch-1",
            record,
            boundary_hook=interrupt,
        )

    path = tmp_path / "deferred" / "batch-1-deferred.json"
    published = path.read_bytes()
    assert len(json.loads(published)["items"]) == 1
    assert record_defer(tmp_path, PRD, "batch-1", record) == path
    assert path.read_bytes() == published
    assert len(json.loads(path.read_bytes())["items"]) == 1


@pytest.mark.parametrize(
    ("prd", "batch_id", "record"),
    (
        ("../escape.md", "batch-1", {"op_id": "defer-1"}),
        ("00004-safe\nunsafe.md", "batch-1", {"op_id": "defer-1"}),
        (PRD, "../batch", {"op_id": "defer-1"}),
        (PRD, "batch\nunsafe", {"op_id": "defer-1"}),
        (PRD, "batch-1", {}),
        (PRD, "batch-1", {"op_id": ""}),
    ),
)
def test_record_defer_rejects_invalid_boundaries_without_writing(
    tmp_path: Path,
    prd: str,
    batch_id: str,
    record: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        record_defer(tmp_path, prd, batch_id, record)

    assert not (tmp_path / "deferred").exists()
