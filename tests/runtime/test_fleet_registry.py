from __future__ import annotations

import fcntl
import json
import os
import stat
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest
from tests.runtime.fleet_registry_helpers import (
    _assert_file_preserved,
    _assert_mutation_lock_held,
    _dead_pid,
    _document,
    _entry,
    _reject,
    _resolve_path,
    _write_entry_file,
    _write_file,
)

from ovcaq.runtime.registry import (
    DuplicateRunError,
    FleetRegistry,
    ProcessIdentity,
    RegistrySnapshot,
    RunLock,
)
from ovcaq.state.schema import MAX_JSON_DEPTH, MAX_STATE_BYTES


def test_public_records_are_frozen(tmp_path: Path) -> None:
    entry = _entry(tmp_path)
    snapshot = RegistrySnapshot(live=(entry,), malformed=(), stale=())
    identity = ProcessIdentity(pid=entry.pid, started=entry.process_start)
    for record, field, value in (
        (entry, "agent", "other"),
        (snapshot, "live", ()),
        (identity, "pid", entry.pid + 1),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(record, field, value)


def test_publish_replaces_private_same_directory_file_after_fsync_then_syncs_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "fleet"
    root.mkdir()
    entry = _entry(tmp_path)
    destination = root / "run-1.json"
    previous = b"previous committed bytes\n"
    destination.write_bytes(previous)
    real_fsync, real_replace = os.fsync, os.replace
    events: list[str] = []
    synced_files: set[tuple[int, int]] = set()

    def observe_fsync(descriptor: int) -> None:
        information = os.fstat(descriptor)
        real_fsync(descriptor)
        if stat.S_ISDIR(information.st_mode):
            if os.path.samestat(information, root.stat()):
                events.append("directory-fsync")
        else:
            synced_files.add((information.st_dev, information.st_ino))

    def observe_replace(
        source: str | Path, target: str | Path, **kwargs: object
    ) -> None:
        source_path = _resolve_path(root, source, kwargs.get("src_dir_fd"))
        target_path = _resolve_path(root, target, kwargs.get("dst_dir_fd"))
        if target_path == destination:
            _assert_mutation_lock_held(root)
            assert source_path.parent == root
            assert source_path != destination
            information = source_path.stat()
            assert stat.S_IMODE(information.st_mode) == 0o600
            assert (information.st_dev, information.st_ino) in synced_files
            assert json.loads(source_path.read_text()) == _document(entry)
            assert destination.read_bytes() == previous
            events.append("replace")
        real_replace(source, target, **kwargs)

    monkeypatch.setattr(os, "fsync", observe_fsync)
    monkeypatch.setattr(os, "replace", observe_replace)
    registry = FleetRegistry(root)
    assert registry.publish(entry) == destination
    assert events.count("replace") == 1
    assert "directory-fsync" in events[events.index("replace") + 1 :]
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert json.loads(destination.read_text()) == _document(entry)
    snapshot = registry.snapshot()
    assert snapshot == RegistrySnapshot(live=(entry,), malformed=(), stale=())
    assert {path.name for path in root.iterdir()} == {"run-1.json", "fleet.lock"}


def test_snapshot_classifies_without_mutation_or_locking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = FleetRegistry(tmp_path)
    live = _entry(tmp_path, "live")
    recycled = replace(_entry(tmp_path, "recycled"), process_start="recycled-identity")
    dead = replace(_entry(tmp_path, "dead"), pid=_dead_pid())
    for entry in (live, recycled, dead):
        registry.publish(entry)
    malformed = tmp_path / "broken.json"
    malformed.write_bytes(b"not json")

    def evidence() -> dict[str, tuple[bytes, int, int, int]]:
        return {
            path.name: (
                path.read_bytes(),
                path.stat().st_ino,
                path.stat().st_mtime_ns,
                path.stat().st_mode,
            )
            for path in tmp_path.iterdir()
        }

    before = evidence()

    def forbid_lock(*args: object, **kwargs: object) -> None:
        raise AssertionError("snapshot attempted to take a lock")

    monkeypatch.setattr(fcntl, "flock", forbid_lock)
    snapshot = registry.snapshot()
    assert snapshot.live == (live,)
    assert snapshot.malformed == (malformed,)
    assert isinstance(snapshot.stale, tuple)
    assert set(snapshot.stale) == {tmp_path / "dead.json", tmp_path / "recycled.json"}
    assert evidence() == before


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "unknown",
        "duplicate",
        "future",
        "null",
        "empty",
        "syntax",
        "pid-zero",
        "pid-negative",
        "pid-bool",
        "pid-float",
        "root-null",
        "timestamp-invalid",
        "timestamp-without-zone",
        "id-escape",
        "deep",
        "oversized",
    ],
)
def test_snapshot_rejects_invalid_documents_without_changing_them(
    tmp_path: Path, damage: str
) -> None:
    document = _document(_entry(tmp_path))
    if damage == "missing":
        del document["agent"]
    elif damage == "unknown":
        document["extra"] = "not allowed"
    elif damage == "future":
        document["schema_version"] = 2
    elif damage.startswith("pid-"):
        document["pid"] = {
            "pid-zero": 0,
            "pid-negative": -1,
            "pid-bool": True,
            "pid-float": 1.5,
        }[damage]
    elif damage == "root-null":
        document["root"] = None
    elif damage == "timestamp-invalid":
        document["started_at"] = "2026-99-99T99:99:99Z"
    elif damage == "timestamp-without-zone":
        document["started_at"] = "2026-09-14T10:00:00"
    elif damage == "id-escape":
        document["run_id"] = "../escaped"
    elif damage == "oversized":
        document["agent"] = "x" * MAX_STATE_BYTES
    encoded = json.dumps(document).encode()
    if damage == "duplicate":
        encoded = encoded[:-1] + b', "pid": 1}'
    elif damage == "null":
        encoded = b"null"
    elif damage == "empty":
        encoded = b""
    elif damage == "syntax":
        encoded = b"{"
    elif damage == "deep":
        encoded = b"[" * (MAX_JSON_DEPTH + 1) + b"0" + b"]" * (MAX_JSON_DEPTH + 1)
    path = tmp_path / "run-1.json"
    path.write_bytes(encoded)
    before = path.stat()
    snapshot = FleetRegistry(tmp_path).snapshot()
    assert snapshot == RegistrySnapshot(live=(), malformed=(path,), stale=())
    assert path.read_bytes() == encoded
    assert path.stat().st_ino == before.st_ino
    assert path.stat().st_mtime_ns == before.st_mtime_ns
    assert set(tmp_path.iterdir()) == {path}


@pytest.mark.parametrize(
    "run_id", ["", ".", "..", "../escaped", "nested/run", "/escaped"]
)
def test_invalid_ids_fail_without_escaping_fleet_root(
    tmp_path: Path, run_id: str
) -> None:
    root = tmp_path / "fleet"
    root.mkdir()
    sentinel = tmp_path / "escaped.json"
    sentinel.write_bytes(b"preserve me")
    registry = FleetRegistry(root)
    _reject(
        ValueError, lambda: registry.publish(replace(_entry(tmp_path), run_id=run_id))
    )
    _reject(ValueError, lambda: registry.remove(run_id))
    assert sentinel.read_bytes() == b"preserve me"
    assert not tuple(root.glob("*.json"))
    assert not (root / "nested").exists()


@pytest.mark.parametrize(
    "field,value", [("schema_version", 2), ("pid", 0), ("started_at", "bad")]
)
def test_invalid_publish_preserves_existing_entry(
    tmp_path: Path, field: str, value: object
) -> None:
    registry = FleetRegistry(tmp_path)
    entry = _entry(tmp_path)
    path = registry.publish(entry)
    before = path.read_bytes()
    _reject(ValueError, lambda: registry.publish(replace(entry, **{field: value})))
    assert path.read_bytes() == before
    assert registry.snapshot().live == (entry,)


def test_prune_removes_dead_recycled_and_malformed_entries_preserving_live(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = FleetRegistry(tmp_path)
    live = _entry(tmp_path, "live")
    registry.publish(live)
    registry.publish(replace(_entry(tmp_path, "dead"), pid=_dead_pid()))
    registry.publish(replace(_entry(tmp_path, "recycled"), process_start="wrong-start"))
    (tmp_path / "broken.json").write_bytes(b"{")
    lock_inode = (tmp_path / "fleet.lock").stat().st_ino
    real_unlink = os.unlink

    def observe_unlink(path: str | Path, **kwargs: object) -> None:
        _assert_mutation_lock_held(tmp_path)
        real_unlink(path, **kwargs)

    monkeypatch.setattr(os, "unlink", observe_unlink)
    result = registry.prune()
    assert isinstance(result, RegistrySnapshot)
    assert registry.snapshot() == RegistrySnapshot(live=(live,), malformed=(), stale=())
    assert {path.name for path in tmp_path.iterdir()} == {"fleet.lock", "live.json"}
    assert (tmp_path / "fleet.lock").stat().st_ino == lock_inode


def test_prune_removes_entry_that_remains_unreadable(tmp_path: Path) -> None:
    registry = FleetRegistry(tmp_path)
    path = registry.publish(_entry(tmp_path))
    path.chmod(0)
    try:
        if os.access(path, os.R_OK):
            pytest.skip("current credentials can read files with mode 000")
        snapshot = registry.snapshot()
        assert snapshot == RegistrySnapshot(live=(), malformed=(path,), stale=())
        registry.prune()
        assert not path.exists()
        assert registry.snapshot() == RegistrySnapshot(live=(), malformed=(), stale=())
    finally:
        if path.exists():
            path.chmod(0o600)


@pytest.mark.parametrize("operation", ["prune-stale", "prune-malformed", "remove"])
def test_replacement_before_mutation_lock_survives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    registry = FleetRegistry(tmp_path)
    old = replace(_entry(tmp_path), process_start="recycled-identity")
    path = registry.publish(old)
    if operation == "prune-malformed":
        path.write_bytes(b"{")
    replacement = _entry(tmp_path)
    lock_path = tmp_path / "fleet.lock"
    lock_identity = (lock_path.stat().st_dev, lock_path.stat().st_ino)
    real_flock = fcntl.flock
    replaced = False

    def replace_before_lock(descriptor: int, mode: int) -> None:
        nonlocal replaced
        information = os.fstat(descriptor)
        if mode & fcntl.LOCK_EX and not replaced:
            assert (information.st_dev, information.st_ino) == lock_identity
            temporary = tmp_path / "replacement.tmp"
            temporary.write_text(json.dumps(_document(replacement)))
            temporary.replace(path)
            replaced = True
        real_flock(descriptor, mode)

    monkeypatch.setattr(fcntl, "flock", replace_before_lock)
    if operation == "remove":
        assert registry.remove(old.run_id, expected=old) is False
    else:
        registry.prune()
    assert replaced, "the concurrent replacement did not run"
    assert registry.snapshot() == RegistrySnapshot(
        live=(replacement,), malformed=(), stale=()
    )
    assert (lock_path.stat().st_dev, lock_path.stat().st_ino) == lock_identity


@pytest.mark.parametrize(
    "changed_field", ["root", "pid", "process_start", "run_id", "agent", "started_at"]
)
def test_remove_requires_complete_expected_entry_match(
    tmp_path: Path, changed_field: str
) -> None:
    registry = FleetRegistry(tmp_path)
    entry = _entry(tmp_path)
    path = registry.publish(entry)
    alternatives = {
        "root": tmp_path / "another-project",
        "pid": _dead_pid(),
        "process_start": "other-start",
        "run_id": "other-run",
        "agent": "other-agent",
        "started_at": "2026-09-14T10:00:01Z",
    }
    expected = replace(entry, **{changed_field: alternatives[changed_field]})
    assert registry.remove(entry.run_id, expected=expected) is False
    assert json.loads(path.read_text()) == _document(entry)


def test_remove_matching_entry_syncs_directory_and_preserves_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = FleetRegistry(tmp_path)
    entry = _entry(tmp_path)
    path = registry.publish(entry)
    lock_path = tmp_path / "fleet.lock"
    lock_inode = lock_path.stat().st_ino
    real_fsync = os.fsync
    real_unlink = os.unlink
    observed_removal_sync: list[bool] = []

    def observe_fsync(descriptor: int) -> None:
        information = os.fstat(descriptor)
        if (
            stat.S_ISDIR(information.st_mode)
            and information.st_ino == tmp_path.stat().st_ino
        ):
            observed_removal_sync.append(not path.exists())
        real_fsync(descriptor)

    def observe_unlink(target: str | Path, **kwargs: object) -> None:
        _assert_mutation_lock_held(tmp_path)
        real_unlink(target, **kwargs)

    monkeypatch.setattr(os, "fsync", observe_fsync)
    monkeypatch.setattr(os, "unlink", observe_unlink)
    assert registry.remove(entry.run_id, expected=entry) is True
    assert not path.exists()
    assert True in observed_removal_sync
    assert registry.remove(entry.run_id, expected=entry) is False
    assert lock_path.stat().st_ino == lock_inode
    assert registry.snapshot() == RegistrySnapshot(live=(), malformed=(), stale=())


def test_created_fleet_artifacts_stay_private_and_keep_one_mutation_lock(
    tmp_path: Path,
) -> None:
    root = tmp_path / "fleet"
    registry = FleetRegistry(root)
    entry = _entry(tmp_path)
    previous_umask = os.umask(0)
    try:
        path = registry.publish(entry)
    finally:
        os.umask(previous_umask)
    lock_path = root / "fleet.lock"
    lock_identity = lock_path.stat()

    def assert_private_artifacts() -> None:
        assert stat.S_ISDIR(root.lstat().st_mode)
        assert stat.S_IMODE(root.lstat().st_mode) == 0o700
        assert stat.S_ISREG(lock_path.lstat().st_mode)
        assert stat.S_IMODE(lock_path.lstat().st_mode) == 0o600
        assert os.path.samestat(lock_path.stat(), lock_identity)

    assert_private_artifacts()
    assert stat.S_ISREG(path.lstat().st_mode)
    assert stat.S_IMODE(path.lstat().st_mode) == 0o600
    assert registry.snapshot() == RegistrySnapshot(
        live=(entry,), malformed=(), stale=()
    )
    registry.prune()
    assert_private_artifacts()
    assert path.exists()
    assert registry.remove(entry.run_id, expected=entry) is True
    assert_private_artifacts()
    assert set(root.iterdir()) == {lock_path}


@pytest.mark.parametrize("substitution", ["initial-symlink", "symlink", "directory"])
def test_snapshot_rejects_symlinked_or_replaced_fleet_root(
    tmp_path: Path, substitution: str
) -> None:
    root = tmp_path / "fleet"
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o755)
    outside_entry = outside / "run-1.json"
    encoded, original = _write_entry_file(outside_entry, _entry(tmp_path))

    if substitution == "initial-symlink":
        root.symlink_to(outside, target_is_directory=True)
        with pytest.raises(ValueError):
            FleetRegistry(root).snapshot()
    else:
        registry = FleetRegistry(root)
        registry.publish(_entry(tmp_path))
        root.rename(tmp_path / "displaced-fleet")
        if substitution == "symlink":
            root.symlink_to(outside, target_is_directory=True)
        else:
            outside.rename(root)
            outside_entry = root / outside_entry.name
        with pytest.raises(ValueError):
            registry.snapshot()

    _assert_file_preserved(outside_entry, encoded, original)
    assert set(outside_entry.parent.iterdir()) == {outside_entry}


@pytest.mark.parametrize("substitute_during_read", [False, True])
def test_snapshot_classifies_entry_symlink_without_reading_or_pruning_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, substitute_during_read: bool
) -> None:
    root = tmp_path / "fleet"
    registry = FleetRegistry(root)
    stale = replace(_entry(tmp_path), process_start="recycled-identity")
    path = registry.publish(stale)
    target = tmp_path / "outside.json"
    encoded, original = _write_entry_file(target, _entry(tmp_path))
    substituted = False
    real_open, real_path_open = os.open, Path.open

    def substitute() -> None:
        nonlocal substituted
        if not substituted:
            path.rename(tmp_path / "displaced-entry.json")
            path.symlink_to(target)
            substituted = True

    def substitute_before_open(
        file: str | Path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        if Path(file).name == path.name:
            substitute()
        return real_open(file, flags, mode, dir_fd=dir_fd)

    def substitute_before_path_open(
        file: Path, *args: object, **kwargs: object
    ) -> object:
        if file == path:
            substitute()
        return real_path_open(file, *args, **kwargs)

    if not substitute_during_read:
        substitute()
    with monkeypatch.context() as patch:
        if substitute_during_read:
            patch.setattr(os, "open", substitute_before_open)
            patch.setattr(Path, "open", substitute_before_path_open)
        snapshot = registry.snapshot()

    assert substituted, "the entry substitution was not exercised"
    assert snapshot == RegistrySnapshot(live=(), malformed=(path,), stale=())
    registry.prune()
    _assert_file_preserved(target, encoded, original)
    assert registry.snapshot().live == ()


@pytest.mark.parametrize("operation", ["publish", "prune", "remove"])
def test_mutation_rejects_symlinked_fleet_lock_without_touching_target(
    tmp_path: Path, operation: str
) -> None:
    root = tmp_path / "fleet"
    registry = FleetRegistry(root)
    entry = replace(_entry(tmp_path), process_start="recycled-identity")
    path = registry.publish(entry)
    encoded = path.read_bytes()
    lock_path = root / "fleet.lock"
    lock_path.rename(tmp_path / "original.lock")
    target = tmp_path / "outside.lock"
    target.write_bytes(b"outside lock must stay unchanged\n")
    target.chmod(0o644)
    original = target.stat()
    lock_path.symlink_to(target)

    if operation == "publish":
        _reject(OSError, lambda: registry.publish(replace(entry, agent="replacement")))
    elif operation == "prune":
        _reject(OSError, registry.prune)
    else:
        _reject(OSError, lambda: registry.remove(entry.run_id, expected=entry))

    assert path.read_bytes() == encoded
    assert lock_path.is_symlink()
    assert target.read_bytes() == b"outside lock must stay unchanged\n"
    assert os.path.samestat(target.stat(), original)
    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    with target.open("rb") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.parametrize("operation", ["publish", "prune", "remove"])
def test_mutation_rejects_fleet_lock_replacement_after_acquisition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    root = tmp_path / "fleet"
    registry = FleetRegistry(root)
    entry = replace(_entry(tmp_path), process_start="recycled-identity")
    path = registry.publish(entry)
    encoded = path.read_bytes()
    lock_path = root / "fleet.lock"
    original = lock_path.stat()
    displaced = tmp_path / "displaced.lock"
    replacement = tmp_path / "replacement.lock"
    replacement.write_bytes(b"another mutation owner\n")
    real_flock = fcntl.flock
    substituted = False

    def substitute_after_lock(descriptor: int, mode: int) -> None:
        nonlocal substituted
        real_flock(descriptor, mode)
        if (
            mode & fcntl.LOCK_EX
            and not substituted
            and os.path.samestat(os.fstat(descriptor), original)
        ):
            lock_path.rename(displaced)
            replacement.rename(lock_path)
            substituted = True

    with replacement.open("rb") as replacement_owner:
        real_flock(replacement_owner.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with monkeypatch.context() as patch:
            patch.setattr(fcntl, "flock", substitute_after_lock)
            with pytest.raises(ValueError):
                if operation == "publish":
                    registry.publish(replace(entry, agent="replacement"))
                elif operation == "prune":
                    registry.prune()
                else:
                    registry.remove(entry.run_id, expected=entry)
        assert substituted, "the fleet lock substitution was not exercised"
        _assert_mutation_lock_held(root)
        with displaced.open("rb") as stream:
            real_flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    assert path.read_bytes() == encoded
    assert os.path.samestat(displaced.stat(), original)
    assert not os.path.samestat(lock_path.stat(), original)
    assert lock_path.read_bytes() == b"another mutation owner\n"


@pytest.mark.parametrize("operation", ["publish", "prune", "remove"])
def test_mutation_rejects_root_substitution_after_lock_without_touching_outside_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    root = tmp_path / "fleet"
    registry = FleetRegistry(root)
    entry = replace(_entry(tmp_path), process_start="recycled-identity")
    path = registry.publish(entry)
    encoded = path.read_bytes()
    lock_identity = (root / "fleet.lock").stat()
    displaced = tmp_path / "displaced-fleet"
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o755)
    outside_entry = outside / path.name
    outside_identity = _write_file(outside_entry, encoded)
    outside_lock = outside / "fleet.lock"
    _write_file(outside_lock, b"outside mutation lock\n")
    real_flock = fcntl.flock
    substituted = False

    def substitute_after_lock(descriptor: int, mode: int) -> None:
        nonlocal substituted
        real_flock(descriptor, mode)
        if (
            mode & fcntl.LOCK_EX
            and not substituted
            and os.path.samestat(os.fstat(descriptor), lock_identity)
        ):
            root.rename(displaced)
            root.symlink_to(outside, target_is_directory=True)
            substituted = True

    with monkeypatch.context() as patch:
        patch.setattr(fcntl, "flock", substitute_after_lock)
        with pytest.raises(ValueError):
            if operation == "publish":
                registry.publish(replace(entry, agent="replacement"))
            elif operation == "prune":
                registry.prune()
            else:
                registry.remove(entry.run_id, expected=entry)

    assert substituted, "the fleet root substitution was not exercised"
    assert root.is_symlink()
    _assert_file_preserved(outside_entry, encoded, outside_identity)
    assert outside_lock.read_bytes() == b"outside mutation lock\n"
    assert stat.S_IMODE(outside_lock.stat().st_mode) == 0o644
    assert set(outside.iterdir()) == {outside_entry, outside_lock}
    assert (displaced / path.name).read_bytes() == encoded
    with (displaced / "fleet.lock").open("rb") as stream:
        real_flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.parametrize("malformed", [False, True])
def test_prune_preserves_byte_identical_replacement_after_candidate_identity_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, malformed: bool
) -> None:
    registry = FleetRegistry(tmp_path)
    stale = replace(_entry(tmp_path), process_start="recycled-identity")
    path = registry.publish(stale)
    if malformed:
        path.write_bytes(b"{")
    encoded = path.read_bytes()
    original = path.stat()
    lock_identity = (tmp_path / "fleet.lock").stat()
    replacement = tmp_path / "replacement.tmp"
    replacement.write_bytes(encoded)
    replacement.chmod(0o600)
    replacement_identity = replacement.stat()
    real_flock = fcntl.flock
    substituted = False

    def substitute_after_lock(descriptor: int, mode: int) -> None:
        nonlocal substituted
        real_flock(descriptor, mode)
        if (
            mode & fcntl.LOCK_EX
            and not substituted
            and os.path.samestat(os.fstat(descriptor), lock_identity)
        ):
            _assert_mutation_lock_held(tmp_path)
            replacement.replace(path)
            substituted = True

    with monkeypatch.context() as patch:
        patch.setattr(fcntl, "flock", substitute_after_lock)
        registry.prune()

    assert substituted, "the stale entry substitution was not exercised"
    assert path.read_bytes() == encoded
    assert os.path.samestat(path.stat(), replacement_identity)
    assert not os.path.samestat(path.stat(), original)
    assert registry.snapshot() == RegistrySnapshot(
        live=(),
        malformed=(path,) if malformed else (),
        stale=() if malformed else (path,),
    )


def test_fleet_operations_preserve_authoritative_project_run_lock(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    run_path = project / "run.lock"
    registry = FleetRegistry(tmp_path / "fleet")
    entry = _entry(project)

    with RunLock.acquire(run_path):
        original = run_path.stat()

        def assert_run_owned() -> None:
            assert os.path.samestat(run_path.stat(), original)
            with run_path.open("rb") as stream, pytest.raises(BlockingIOError):
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with pytest.raises(DuplicateRunError):
                RunLock.acquire(run_path)

        assert_run_owned()
        registry.publish(entry)
        assert registry.snapshot().live == (entry,)
        assert_run_owned()
        registry.publish(replace(entry, process_start="recycled-identity"))
        registry.prune()
        assert registry.snapshot() == RegistrySnapshot(live=(), malformed=(), stale=())
        assert_run_owned()
        registry.publish(entry)
        assert registry.remove(entry.run_id, expected=entry) is True
        assert_run_owned()

    assert os.path.samestat(run_path.stat(), original)
    with RunLock.acquire(run_path):
        assert os.path.samestat(run_path.stat(), original)
