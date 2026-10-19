from __future__ import annotations

import json
import os
import stat
from collections.abc import Callable
from dataclasses import FrozenInstanceError, asdict, fields, replace
from pathlib import Path

import pytest
from tests.runtime.session_metadata_helpers import (
    _decode,
    _metadata,
    _publication_path,
    _summary,
)

from ovcaq.paths import resolve_runtime_paths
from ovcaq.runtime.session import (
    SessionMetadata,
    SessionPaths,
    create_session,
    publish_run_metadata,
    publish_session_summary,
)
from ovcaq.state.schema import MAX_STATE_BYTES, MAX_STRING_BYTES


def _reject(expected: type[BaseException], operation: Callable[[], object]) -> None:
    with pytest.raises(expected):
        operation()


@pytest.fixture
def synced(monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, int, bool]]:
    observations: list[tuple[int, int, bool]] = []
    real_fsync = os.fsync

    def observe_fsync(descriptor: int) -> None:
        information = os.fstat(descriptor)
        real_fsync(descriptor)
        observations.append(
            (information.st_dev, information.st_ino, stat.S_ISDIR(information.st_mode))
        )

    monkeypatch.setattr(os, "fsync", observe_fsync)
    return observations


def test_session_records_expose_exact_fields_and_metadata_is_frozen() -> None:
    assert {field.name for field in fields(SessionPaths)} == {
        "root",
        "raw",
        "normalized",
        "metrics",
        "metadata",
        "summary",
    }
    assert {field.name for field in fields(SessionMetadata)} == {
        "schema_version",
        "run_id",
        "session_id",
        "agent",
        "pid",
        "process_start",
        "started_at",
    }
    metadata = _metadata()
    with pytest.raises(FrozenInstanceError):
        metadata.agent = "changed"


def test_create_session_returns_exact_private_paths_and_durable_metadata(
    tmp_path: Path, synced: list[tuple[int, int, bool]]
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    paths.runtime_root.parent.mkdir(mode=0o751, parents=True, exist_ok=True)
    ancestors = (tmp_path, paths.runtime_root.parent.parent, paths.runtime_root.parent)
    ancestor_identity = {
        ancestor: (information.st_dev, information.st_ino, information.st_mode)
        for ancestor in ancestors
        for information in (ancestor.stat(),)
    }
    metadata = _metadata()
    previous_umask = os.umask(0)
    try:
        session = create_session(paths, metadata)
    finally:
        os.umask(previous_umask)
    root = paths.sessions / metadata.session_id
    assert session == SessionPaths(
        root=root,
        raw=root / "raw.jsonl",
        normalized=root / "normalized.jsonl",
        metrics=root / "metrics.jsonl",
        metadata=root / "meta.json",
        summary=root / "summary.json",
    )
    assert _decode(session.metadata) == asdict(metadata)
    for directory in (paths.runtime_root, paths.sessions, session.root):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert {
        ancestor: (information.st_dev, information.st_ino, information.st_mode)
        for ancestor in ancestors
        for information in (ancestor.stat(),)
    } == ancestor_identity
    for artifact in session.root.iterdir():
        assert stat.S_IMODE(artifact.stat().st_mode) == 0o600
    information = session.metadata.stat()
    metadata_sync = (information.st_dev, information.st_ino, False)
    assert metadata_sync in synced
    information = root.stat()
    assert (information.st_dev, information.st_ino, True) in synced[
        synced.index(metadata_sync) + 1 :
    ]
    assert not session.summary.exists()


@pytest.mark.parametrize(
    "metadata,summary",
    [
        pytest.param(
            SessionMetadata(
                schema_version=1,
                run_id="batch-orion-73",
                session_id="attempt-cobalt-19",
                agent="worker-orion",
                pid=4721,
                process_start="boot-orion:92841",
                started_at="2025-02-03T04:05:06Z",
            ),
            {
                "schema_version": 1,
                "session_id": "attempt-cobalt-19",
                "finished_at": "2025-02-03T04:08:17Z",
                "returncode": 7,
                "signal": None,
                "timed_out": False,
                "detail": "Worker reported an incomplete step.",
            },
            id="independent-failed-session",
        ),
        pytest.param(
            SessionMetadata(
                schema_version=1,
                run_id="batch-lyra-86",
                session_id="attempt-amber-42",
                agent="worker-lyra",
                pid=8362,
                process_start="boot-lyra:61357",
                started_at="2024-11-21T18:19:20Z",
            ),
            {
                "schema_version": 1,
                "session_id": "attempt-amber-42",
                "finished_at": "2024-11-21T18:23:41Z",
                "returncode": -9,
                "signal": 9,
                "timed_out": True,
                "detail": "Worker exceeded its deadline.",
            },
            id="independent-timed-out-session",
        ),
    ],
)
def test_publication_preserves_independent_session_paths_and_values(
    tmp_path: Path, metadata: SessionMetadata, summary: dict[str, object]
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    session = create_session(paths, metadata)
    root = paths.sessions / metadata.session_id
    assert session == SessionPaths(
        root=root,
        raw=root / "raw.jsonl",
        normalized=root / "normalized.jsonl",
        metrics=root / "metrics.jsonl",
        metadata=root / "meta.json",
        summary=root / "summary.json",
    )
    assert _decode(root / "meta.json") == asdict(metadata)
    publish_run_metadata(paths, metadata)
    publish_session_summary(session, summary)
    assert paths.run_metadata == paths.runtime_root / "run.json"
    assert _decode(paths.run_metadata) == asdict(metadata)
    assert _decode(root / "meta.json") == asdict(metadata)
    assert _decode(root / "summary.json") == summary
    assert set(paths.sessions.iterdir()) == {root}
    for artifact in (paths.run_metadata, session.metadata, session.summary):
        assert stat.S_IMODE(artifact.stat().st_mode) == 0o600


@pytest.mark.parametrize("publication", ["run", "summary"])
def test_publication_replaces_synced_private_json_atomically_then_syncs_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    publication: str,
    synced: list[tuple[int, int, bool]],
) -> None:
    paths, metadata = resolve_runtime_paths(tmp_path), _metadata()
    session = create_session(paths, metadata)
    if publication == "run":
        publish_run_metadata(paths, metadata)
        destination = paths.run_metadata
        expected = asdict(replace(metadata, agent="other"))
        assert destination == paths.runtime_root / "run.json"
    else:
        publish_session_summary(session, _summary())
        destination = session.summary
        expected = _summary() | {"detail": "complete"}
    previous = destination.read_bytes()
    synced.clear()
    replacement_sync_offsets: list[int] = []
    real_replace = os.replace

    def track_replace(source: str | Path, target: str | Path, **kwargs: object) -> None:
        parent = destination.parent
        source_path = _publication_path(source, kwargs.get("src_dir_fd"), parent)
        target_path = _publication_path(target, kwargs.get("dst_dir_fd"), parent)
        if target_path == destination:
            assert source_path.parent == destination.parent
            assert source_path != destination
            information = source_path.stat()
            assert stat.S_IMODE(information.st_mode) == 0o600
            assert (information.st_dev, information.st_ino, False) in synced
            assert _decode(source_path) == expected
            assert destination.read_bytes() == previous
            replacement_sync_offsets.append(len(synced))
        real_replace(source, target, **kwargs)

    monkeypatch.setattr(os, "replace", track_replace)
    if publication == "run":
        publish_run_metadata(paths, replace(metadata, agent="other"))
    else:
        publish_session_summary(session, expected)
    assert len(replacement_sync_offsets) == 1
    information = destination.parent.stat()
    assert (information.st_dev, information.st_ino, True) in synced[
        replacement_sync_offsets[0] :
    ]
    assert _decode(destination) == expected
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600


@pytest.mark.parametrize("field", ["run_id", "session_id"])
@pytest.mark.parametrize(
    "value", ["", ".", "..", "../escaped", "/escaped", "nested/id", "bad\x00id"]
)
def test_invalid_ids_fail_without_replacing_evidence_or_escaping_runtime(
    tmp_path: Path, field: str, value: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    metadata = _metadata()
    session = create_session(paths, metadata)
    publish_run_metadata(paths, metadata)
    before = session.metadata.read_bytes(), paths.run_metadata.read_bytes()
    sentinel = tmp_path / "escaped"
    sentinel.write_bytes(b"preserve")
    for operation in (create_session, publish_run_metadata):
        _reject(
            ValueError,
            lambda operation=operation: operation(
                paths, replace(metadata, **{field: value})
            ),
        )
    assert (session.metadata.read_bytes(), paths.run_metadata.read_bytes()) == before
    assert sentinel.read_bytes() == b"preserve"
    assert set(paths.sessions.iterdir()) == {session.root}


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", 2),
        ("schema_version", True),
        ("schema_version", 1.0),
        ("pid", 0),
        ("pid", -1),
        ("pid", True),
        ("pid", 1.5),
        ("started_at", "2026-99-99T99:99:99Z"),
        ("started_at", "2026-09-14T10:00:00"),
        ("started_at", "2026-09-14T10:00:00+02:00"),
        ("started_at", None),
        ("agent", ""),
        ("agent", None),
        ("process_start", ""),
        ("process_start", None),
        pytest.param("agent", "x" * MAX_STATE_BYTES, id="oversized-agent"),
    ],
)
def test_invalid_metadata_cannot_replace_run_or_create_session(
    tmp_path: Path, field: str, value: object
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    metadata = _metadata()
    publish_run_metadata(paths, metadata)
    before = paths.run_metadata.read_bytes()
    for operation in (create_session, publish_run_metadata):
        _reject(
            ValueError,
            lambda operation=operation: operation(
                paths, replace(metadata, **{field: value})
            ),
        )
    assert paths.run_metadata.read_bytes() == before
    assert not (paths.sessions / metadata.session_id / "meta.json").exists()


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "unknown",
        "future",
        "bool-version",
        "bad-id",
        "bad-time",
        "local-time",
        "offset-time",
        "bool-returncode",
        "null-returncode",
        "float-signal",
        "int-timeout",
        "object-detail",
        "oversized-detail",
    ],
)
def test_invalid_summary_preserves_previously_committed_summary(
    tmp_path: Path, damage: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    session = create_session(paths, _metadata())
    publish_session_summary(session, _summary())
    previous = session.summary.read_bytes()
    summary = _summary()
    if damage == "missing":
        del summary["detail"]
    elif damage == "unknown":
        summary["extra"] = None
    else:
        field, value = {
            "future": ("schema_version", 2),
            "bool-version": ("schema_version", True),
            "bad-id": ("session_id", "../escaped"),
            "bad-time": ("finished_at", "invalid"),
            "local-time": ("finished_at", "2026-09-14T10:01:00"),
            "offset-time": ("finished_at", "2026-09-14T10:01:00+02:00"),
            "bool-returncode": ("returncode", True),
            "null-returncode": ("returncode", None),
            "float-signal": ("signal", 1.5),
            "int-timeout": ("timed_out", 1),
            "object-detail": ("detail", {}),
            "oversized-detail": ("detail", "x" * (MAX_STRING_BYTES + 1)),
        }[damage]
        summary[field] = value
    _reject(ValueError, lambda: publish_session_summary(session, summary))
    assert session.summary.read_bytes() == previous


@pytest.mark.parametrize(
    "detail", [None, "", pytest.param("é" * (MAX_STRING_BYTES // 2), id="utf8-limit")]
)
def test_summary_retains_completion_values_and_accepts_bounded_detail(
    tmp_path: Path, detail: str | None
) -> None:
    session = create_session(resolve_runtime_paths(tmp_path), _metadata())
    summary = _summary() | {
        "returncode": -15,
        "signal": 15,
        "timed_out": True,
        "detail": detail,
    }
    publish_session_summary(session, summary)
    assert _decode(session.summary) == summary
    assert _decode(session.metadata) == asdict(_metadata())


@pytest.mark.parametrize("mismatch", ["summary", "metadata", "directory"])
def test_summary_must_match_both_containing_directory_and_metadata(
    tmp_path: Path, mismatch: str
) -> None:
    session = create_session(resolve_runtime_paths(tmp_path), _metadata())
    publish_session_summary(session, _summary())
    previous = session.summary.read_bytes()
    summary = _summary()
    if mismatch == "summary":
        summary["session_id"] = "another-session"
    else:
        record = asdict(_metadata("another-session"))
        session.metadata.write_text(json.dumps(record), encoding="utf-8")
        if mismatch == "directory":
            summary["session_id"] = "another-session"
    metadata_before = session.metadata.read_bytes()

    _reject(ValueError, lambda: publish_session_summary(session, summary))

    assert session.summary.read_bytes() == previous
    assert session.metadata.read_bytes() == metadata_before


class _ParentReplacement:
    def __init__(self, destination: Path, tmp_path: Path, boundary: str) -> None:
        self.destination, self.parent, self.boundary = (
            destination,
            destination.parent,
            boundary,
        )
        self.outside = tmp_path / "outside"
        self.outside.mkdir()
        information = self.outside.stat()
        self.outside_identity = information.st_dev, information.st_ino
        sentinel = self.outside / "sentinel"
        sentinel.write_bytes(b"preserve")
        self.outside_before = {sentinel.name: sentinel.read_bytes()}
        self.relocated = tmp_path / "original-directory"
        self.replaced = False
        self.committed = False
        self.original_identity: tuple[int, int] | None = None
        self.synced_directories: list[tuple[int, int]] = []
        self.real_open, self.real_replace, self.real_fsync = (
            os.open,
            os.replace,
            os.fsync,
        )

    def belongs_to_parent(self, path: str | Path, descriptor: object = None) -> bool:
        candidate = Path(path)
        if descriptor is not None and not candidate.is_absolute():
            return self.parent.exists() and os.path.samestat(
                os.fstat(descriptor), self.parent.stat()
            )
        return candidate.parent == self.parent

    def replace_parent(self) -> None:
        information = self.parent.stat()
        self.original_identity = information.st_dev, information.st_ino
        self.parent.rename(self.relocated)
        self.parent.symlink_to(self.outside, target_is_directory=True)
        self.replaced = True

    def race_open(
        self, path: str | Path, flags: int, *args: object, **kwargs: object
    ) -> int:
        if (
            self.boundary == "create"
            and not self.replaced
            and flags & os.O_CREAT
            and self.belongs_to_parent(path, kwargs.get("dir_fd"))
        ):
            self.replace_parent()
        return self.real_open(path, flags, *args, **kwargs)

    def race_replace(
        self, source: str | Path, target: str | Path, **kwargs: object
    ) -> None:
        publishing = Path(target).name == self.destination.name and (
            self.replaced or self.belongs_to_parent(target, kwargs.get("dst_dir_fd"))
        )
        if self.boundary == "replace" and not self.replaced and publishing:
            self.replace_parent()
            planted = self.outside / Path(source).name
            planted.write_bytes(b"unrelated external temporary file")
            self.outside_before[planted.name] = planted.read_bytes()
        self.real_replace(source, target, **kwargs)
        if publishing:
            self.committed = True
            if self.boundary == "directory-fsync" and not self.replaced:
                self.replace_parent()

    def observe_fsync(self, descriptor: int) -> None:
        information = os.fstat(descriptor)
        if self.replaced and stat.S_ISDIR(information.st_mode):
            self.synced_directories.append((information.st_dev, information.st_ino))
        self.real_fsync(descriptor)


@pytest.mark.parametrize("publication", ["run", "summary", "metadata"])
@pytest.mark.parametrize("boundary", ["create", "replace", "directory-fsync"])
def test_parent_replacement_cannot_redirect_publication_or_directory_sync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    publication: str,
    boundary: str,
) -> None:
    paths, metadata = resolve_runtime_paths(tmp_path), _metadata()
    if publication == "metadata":
        destination = paths.sessions / metadata.session_id / "meta.json"
        expected = asdict(metadata)
        operation = lambda: create_session(paths, metadata)
    else:
        session = create_session(paths, metadata)
        if publication == "run":
            destination, expected = paths.run_metadata, asdict(metadata)
            operation = lambda: publish_run_metadata(paths, metadata)
        else:
            destination, expected = session.summary, _summary()
            operation = lambda: publish_session_summary(session, expected)
    race = _ParentReplacement(destination, tmp_path, boundary)
    monkeypatch.setattr(os, "open", race.race_open)
    monkeypatch.setattr(os, "replace", race.race_replace)
    monkeypatch.setattr(os, "fsync", race.observe_fsync)
    error: Exception | None = None
    try:
        operation()
    except Exception as exc:  # noqa: BLE001 - safe rejection is permitted
        error = exc

    assert race.replaced, f"the {boundary} race was not exercised"
    assert {
        path.name: path.read_bytes() for path in race.outside.iterdir()
    } == race.outside_before
    assert race.outside_identity not in race.synced_directories
    if race.committed:
        assert race.original_identity in race.synced_directories
    if error is None:
        assert _decode(race.relocated / destination.name) == expected
        assert stat.S_IMODE((race.relocated / destination.name).stat().st_mode) == 0o600
        assert race.committed


def test_session_directory_creation_cannot_follow_replaced_sessions_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_bytes(b"preserve")
    relocated = tmp_path / "original-sessions"
    replaced = False
    real_mkdir = os.mkdir

    def race_mkdir(path: str | Path, *args: object, **kwargs: object) -> None:
        nonlocal replaced
        if Path(path).name == "session-1" and not replaced:
            paths.sessions.rename(relocated)
            paths.sessions.symlink_to(outside, target_is_directory=True)
            replaced = True
        real_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(os, "mkdir", race_mkdir)
    error: Exception | None = None
    try:
        create_session(paths, _metadata())
    except Exception as exc:  # noqa: BLE001 - safe rejection is permitted
        error = exc

    assert replaced, "the session directory creation race was not exercised"
    assert set(outside.iterdir()) == {sentinel}
    assert sentinel.read_bytes() == b"preserve"
    if error is None:
        root = relocated / "session-1"
        assert _decode(root / "meta.json") == asdict(_metadata())
        assert stat.S_IMODE(root.stat().st_mode) == 0o700


@pytest.mark.parametrize("component", ["runtime", "sessions", "session"])
def test_create_session_rejects_symlinked_directories_without_touching_targets(
    tmp_path: Path, component: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_bytes(b"preserve")
    location = {
        "runtime": paths.runtime_root,
        "sessions": paths.sessions,
        "session": paths.sessions / "session-1",
    }[component]
    location.parent.mkdir(parents=True, exist_ok=True)
    location.symlink_to(outside, target_is_directory=True)
    expected = OSError if component == "session" else ValueError
    _reject(expected, lambda: create_session(paths, _metadata()))
    assert location.is_symlink()
    assert list(outside.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"preserve"


@pytest.mark.parametrize("publication", ["run", "summary", "metadata"])
@pytest.mark.parametrize("obstacle", ["symlink", "directory", "fifo"])
def test_publication_rejects_nonregular_destinations_without_changing_them(
    tmp_path: Path, publication: str, obstacle: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    metadata = _metadata()
    session = create_session(paths, metadata)
    if publication == "metadata":
        destination = paths.sessions / "session-2" / "meta.json"
        destination.parent.mkdir(mode=0o700)
    else:
        destination = paths.run_metadata if publication == "run" else session.summary
    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(b"preserve")
    if obstacle == "symlink":
        destination.symlink_to(sentinel)
    elif obstacle == "directory":
        destination.mkdir()
    else:
        os.mkfifo(destination)
    before = destination.lstat()
    if publication == "metadata":
        _reject(OSError, lambda: create_session(paths, _metadata("session-2")))
    elif publication == "run":
        _reject(ValueError, lambda: publish_run_metadata(paths, metadata))
    else:
        _reject(ValueError, lambda: publish_session_summary(session, _summary()))
    after = destination.lstat()
    assert (after.st_ino, after.st_mode) == (before.st_ino, before.st_mode)
    assert sentinel.read_bytes() == b"preserve"


def test_completion_and_new_session_preserve_existing_session_evidence(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    metadata = _metadata()
    session = create_session(paths, metadata)
    for artifact in (session.raw, session.normalized, session.metrics):
        artifact.write_bytes(b'{"evidence":"retain"}\n')
    unrelated = session.root / "operator-note.txt"
    unrelated.write_bytes(b"retain operator note")
    publish_session_summary(session, _summary())
    before = {path: path.read_bytes() for path in session.root.iterdir()}
    _reject(OSError, lambda: create_session(paths, replace(metadata, agent="changed")))
    second = create_session(paths, _metadata("session-2"))
    publish_run_metadata(paths, _metadata("session-2"))
    assert {path: path.read_bytes() for path in session.root.iterdir()} == before
    assert _decode(second.metadata) == asdict(_metadata("session-2"))
    assert not second.summary.exists()
    assert _decode(session.summary) == _summary()


def test_incomplete_session_metadata_remains_readable_after_fresh_path_resolution(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    session = create_session(paths, _metadata())
    session.raw.write_bytes(b'{"unfinished":')
    fresh_paths = resolve_runtime_paths(tmp_path)
    assert _decode(fresh_paths.sessions / "session-1" / "meta.json") == asdict(
        _metadata()
    )
    assert session.raw.read_bytes() == b'{"unfinished":'
    assert not session.summary.exists()
