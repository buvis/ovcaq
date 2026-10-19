from __future__ import annotations

import json
import os
import stat
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from tests.runtime.session_metadata_helpers import (
    _decode,
    _metadata,
    _publication_path,
    _summary,
)

from ovcaq.paths import RuntimePaths, resolve_runtime_paths
from ovcaq.runtime.registry import FleetEntry, FleetRegistry
from ovcaq.runtime.session import (
    SessionMetadata,
    cleanup_run_records,
    create_session,
    publish_run_metadata,
    publish_session_summary,
)


def _cleanup_records(
    tmp_path: Path,
) -> tuple[RuntimePaths, SessionMetadata, FleetEntry, Path]:
    paths = resolve_runtime_paths(tmp_path, xdg_state_home=tmp_path / "xdg")
    metadata = _metadata()
    entry = FleetEntry(
        schema_version=metadata.schema_version,
        root=paths.project_root,
        pid=metadata.pid,
        process_start=metadata.process_start,
        run_id=metadata.run_id,
        agent=metadata.agent,
        started_at=metadata.started_at,
    )
    publish_run_metadata(paths, metadata)
    fleet_path = FleetRegistry(paths.fleet_root).publish(entry)
    return paths, metadata, entry, fleet_path


def _file_snapshot(root: Path, *, excluded: set[Path]) -> dict[Path, tuple[int, bytes]]:
    return {
        path: (path.stat().st_ino, path.read_bytes())
        for path in root.rglob("*")
        if path.is_file() and path not in excluded
    }


def _directory_snapshot(root: Path) -> dict[Path, int]:
    return {path: path.stat().st_ino for path in root.rglob("*") if path.is_dir()}


def _assert_retained_record(
    path: Path, identity: os.stat_result | None, contents: bytes | None, damage: str
) -> None:
    if identity is None:
        assert not path.exists()
    else:
        after = path.lstat()
        assert (after.st_ino, after.st_mode) == (identity.st_ino, identity.st_mode)
        if contents is not None:
            assert path.read_bytes() == contents
        if damage == "directory":
            assert (path / "keep").read_bytes() == b"retained"


def test_cleanup_durably_removes_only_owner_records_and_preserves_evidence_and_locks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, metadata, entry, fleet_path = _cleanup_records(tmp_path)
    for session_id in (metadata.session_id, "older-session"):
        session = create_session(paths, _metadata(session_id))
        for artifact in (session.raw, session.normalized, session.metrics):
            artifact.write_bytes(b'{"evidence":"retain"}\n')
        publish_session_summary(session, _summary(session_id))
    for artifact in (
        paths.run_lock,
        paths.fleet_lock,
        paths.retention_lock,
        paths.state_file,
        paths.events,
        paths.metrics,
        paths.reports / "completed.json",
    ):
        artifact.parent.mkdir(parents=True, exist_ok=True)
        if not artifact.exists():
            artifact.write_bytes(b"retained evidence")
    records = {paths.run_metadata, fleet_path}
    retained = _file_snapshot(tmp_path, excluded=records)
    directories = _directory_snapshot(tmp_path)
    durable: set[Path] = set()
    real_fsync = os.fsync

    def observe_fsync(descriptor: int) -> None:
        information = os.fstat(descriptor)
        real_fsync(descriptor)
        if stat.S_ISDIR(information.st_mode):
            for record in records:
                if not record.exists() and os.path.samestat(
                    information, record.parent.stat()
                ):
                    durable.add(record)

    monkeypatch.setattr(os, "fsync", observe_fsync)

    assert cleanup_run_records(paths, metadata, entry) is True

    assert all(not path.exists() for path in records)
    assert durable == records
    assert _file_snapshot(tmp_path, excluded=set()) == retained
    assert _directory_snapshot(tmp_path) == directories
    assert cleanup_run_records(paths, metadata, entry) is False


@pytest.mark.parametrize("record", ["run", "fleet"])
def test_cleanup_cannot_report_success_when_deleted_record_cannot_be_synced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, record: str
) -> None:
    paths, metadata, entry, fleet_path = _cleanup_records(tmp_path)
    destination = paths.run_metadata if record == "run" else fleet_path
    real_fsync = os.fsync
    sync_failed = False

    def fail_deleted_record_sync(descriptor: int) -> None:
        nonlocal sync_failed
        information = os.fstat(descriptor)
        if (
            stat.S_ISDIR(information.st_mode)
            and not destination.exists()
            and os.path.samestat(information, destination.parent.stat())
        ):
            sync_failed = True
            raise OSError("directory synchronization failed")
        real_fsync(descriptor)

    monkeypatch.setattr(os, "fsync", fail_deleted_record_sync)
    try:
        result = cleanup_run_records(paths, metadata, entry)
    except Exception:  # noqa: BLE001 - failure may be raised or returned
        result = False

    assert sync_failed, "the post-deletion directory synchronization was not exercised"
    assert result is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", 2),
        ("root", Path("another-project")),
        ("pid", 4721),
        ("process_start", "different-start-token"),
        ("run_id", "different-run"),
        ("agent", "different-agent"),
        ("started_at", "2026-09-14T09:00:00Z"),
    ],
)
def test_cleanup_rejects_unrelated_supplied_fleet_owner_without_removing_records(
    tmp_path: Path, field: str, value: object
) -> None:
    paths, metadata, entry, fleet_path = _cleanup_records(tmp_path)
    if field == "root":
        value = tmp_path / "another-project"
        value.mkdir()
    elif field == "pid":
        value = metadata.pid + 1
    unrelated = replace(entry, **{field: value})
    owner_paths = {paths.run_metadata, fleet_path}
    if field != "schema_version":
        fleet_path = FleetRegistry(paths.fleet_root).publish(unrelated)
        owner_paths.add(fleet_path)
    before = {path: path.read_bytes() for path in owner_paths}

    assert cleanup_run_records(paths, metadata, unrelated) is False

    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "malformed",
        "null",
        "duplicate-key",
        "missing-field",
        "schema_version",
        "run_id",
        "session_id",
        "agent",
        "pid",
        "process_start",
        "started_at",
        "symlink",
        "directory",
        "fifo",
    ],
)
def test_cleanup_rejects_invalid_run_metadata_without_removing_either_record(
    tmp_path: Path, damage: str
) -> None:
    paths, metadata, entry, fleet_path = _cleanup_records(tmp_path)
    run = paths.run_metadata
    sentinel = tmp_path / "sentinel.json"
    sentinel.write_bytes(run.read_bytes())
    if damage in {"missing", "symlink", "directory", "fifo"}:
        run.unlink()
        if damage == "symlink":
            run.symlink_to(sentinel)
        elif damage == "directory":
            run.mkdir()
            (run / "keep").write_bytes(b"retained")
        elif damage == "fifo":
            os.mkfifo(run)
    elif damage == "malformed":
        run.write_bytes(b'{"unfinished":')
    elif damage == "null":
        run.write_bytes(b"null")
    elif damage == "duplicate-key":
        run.write_text(
            json.dumps(asdict(metadata))[:-1] + ', "run_id": "run-1"}',
            encoding="utf-8",
        )
    else:
        document = asdict(metadata)
        if damage == "missing-field":
            del document["process_start"]
        else:
            document[damage] = {
                "schema_version": 2,
                "run_id": "other-run",
                "session_id": "other-session",
                "agent": "other-agent",
                "pid": metadata.pid + 1,
                "process_start": "other-start",
                "started_at": "2026-09-14T09:00:00Z",
            }[damage]
        run.write_text(json.dumps(document), encoding="utf-8")
    fleet_before, sentinel_before = fleet_path.read_bytes(), sentinel.read_bytes()
    identity = run.lstat() if damage != "missing" else None
    contents = run.read_bytes() if identity and stat.S_ISREG(identity.st_mode) else None

    assert cleanup_run_records(paths, metadata, entry) is False

    assert fleet_path.read_bytes() == fleet_before
    assert sentinel.read_bytes() == sentinel_before
    _assert_retained_record(run, identity, contents, damage)


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "schema_version",
        "root",
        "pid",
        "process_start",
        "run_id",
        "agent",
        "started_at",
        "malformed",
        "symlink",
        "directory",
        "fifo",
    ],
)
def test_cleanup_preserves_run_metadata_when_fleet_record_cannot_be_removed(
    tmp_path: Path, damage: str
) -> None:
    paths, metadata, entry, fleet_path = _cleanup_records(tmp_path)
    sentinel = tmp_path / "fleet-sentinel.json"
    sentinel.write_bytes(fleet_path.read_bytes())
    substitutions = {
        "schema_version": 2,
        "root": str(tmp_path / "another-project"),
        "pid": entry.pid + 1,
        "process_start": "new-owner-start",
        "run_id": "new-run",
        "agent": "new-agent",
        "started_at": "2026-09-14T09:00:00Z",
    }
    if damage in substitutions:
        document = _decode(fleet_path)
        document[damage] = substitutions[damage]
        fleet_path.write_text(json.dumps(document), encoding="utf-8")
    elif damage == "malformed":
        fleet_path.write_bytes(b'{"unfinished":')
    else:
        fleet_path.unlink()
        if damage == "symlink":
            fleet_path.symlink_to(sentinel)
        elif damage == "directory":
            fleet_path.mkdir()
            (fleet_path / "keep").write_bytes(b"retained")
        elif damage == "fifo":
            os.mkfifo(fleet_path)
    run_before = paths.run_metadata.read_bytes()
    sentinel_before = sentinel.read_bytes()
    identity = fleet_path.lstat() if damage != "missing" else None
    contents = (
        fleet_path.read_bytes() if identity and stat.S_ISREG(identity.st_mode) else None
    )

    assert cleanup_run_records(paths, metadata, entry) is False

    assert paths.run_metadata.read_bytes() == run_before
    assert sentinel.read_bytes() == sentinel_before
    _assert_retained_record(fleet_path, identity, contents, damage)


@pytest.mark.parametrize("replacement", ["different-owner", "identical-content"])
def test_cleanup_never_unlinks_run_metadata_replaced_after_fleet_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replacement: str
) -> None:
    paths, metadata, entry, fleet_path = _cleanup_records(tmp_path)
    incoming = tmp_path / "replacement.json"
    contents = paths.run_metadata.read_bytes()
    if replacement == "different-owner":
        contents = json.dumps(asdict(replace(metadata, run_id="new-run"))).encode()
    incoming.write_bytes(contents)
    replacement_identity = incoming.stat().st_ino
    replaced = False
    real_unlink = os.unlink

    def replace_after_fleet_unlink(path: str | Path, **kwargs: object) -> None:
        nonlocal replaced
        candidate = Path(path)
        if candidate.name == fleet_path.name:
            candidate = _publication_path(path, kwargs.get("dir_fd"), fleet_path.parent)
        real_unlink(path, **kwargs)
        if candidate == fleet_path:
            assert paths.run_metadata.exists()
            incoming.replace(paths.run_metadata)
            replaced = True

    monkeypatch.setattr(os, "unlink", replace_after_fleet_unlink)
    monkeypatch.setattr(os, "remove", replace_after_fleet_unlink)

    assert cleanup_run_records(paths, metadata, entry) is False

    assert replaced, "the replacement race was not exercised"
    assert not fleet_path.exists()
    assert paths.run_metadata.stat().st_ino == replacement_identity
    assert paths.run_metadata.read_bytes() == contents
