from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from saga_support import PRD, _run_park, _run_stall, _trip_at

from ovcaq.state.commands import StateService
from ovcaq.state.store import DurabilityBoundary, StateIOError, StateStore
from ovcaq.workflow import records
from ovcaq.workflow.paths import LifecyclePaths


@pytest.mark.parametrize("operation", (_run_stall, _run_park), ids=("stall", "park"))
def test_move_refuses_competing_destination_at_syscall(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    monkeypatch: pytest.MonkeyPatch,
    operation: Callable[..., None],
) -> None:
    store, paths, runtime = saga_environment
    source = paths.wip / PRD
    held = paths.hold / PRD
    original = source.read_bytes()
    rename = records.rename_exclusive

    def compete(*args: object, **kwargs: object) -> None:
        held.write_bytes(b"concurrent held work")
        rename(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(records, "rename_exclusive", compete)
        with pytest.raises(OSError):
            operation(store, paths, runtime)

    assert held.read_bytes() == b"concurrent held work"
    assert source.read_bytes() == original
    assert store.read()["recovery"]["operation"]["step"] == "intent"
    assert len(store.read()["tasks"]) == 1
    held.rename(held.with_suffix(".retained"))
    operation(store, paths, runtime)
    assert held.read_bytes() == original
    assert store.read()["recovery"]["operation"] is None


@pytest.mark.parametrize("operation", (_run_stall, _run_park), ids=("stall", "park"))
@pytest.mark.parametrize("target", ("wip", "hold", "deferred"))
@pytest.mark.parametrize("boundary", tuple(DurabilityBoundary))
def test_saga_evidence_survives_state_publication(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    operation: Callable[..., None],
    target: str,
    boundary: DurabilityBoundary,
) -> None:
    store, paths, runtime = saga_environment
    with pytest.raises(RuntimeError, match="after-append-before-commit"):
        operation(
            store, paths, runtime, boundary_hook=_trip_at("after-append-before-commit")
        )
    before = store.path.read_bytes()
    backup = store.path.with_suffix(".json.bak")
    backup_before = backup.read_bytes()
    directory = runtime / target if target == "deferred" else getattr(paths, target)
    relocated = directory.with_name(f"{target}-relocated")

    def replace(reached: DurabilityBoundary) -> None:
        if reached == boundary:
            directory.rename(relocated)
            directory.mkdir()

    guarded_store = StateStore(store.path, boundary_hook=replace)
    with pytest.raises(StateIOError, match="directory identity changed"):
        operation(guarded_store, paths, runtime)

    assert store.path.read_bytes() == before
    assert backup.read_bytes() == backup_before
    assert list(directory.iterdir()) == []
    assert not list(runtime.glob(".state.json.ovcaq-*.tmp"))
    directory.rmdir()
    relocated.rename(directory)
    operation(store, paths, runtime)
    committed = store.path.read_bytes()
    operation(store, paths, runtime)
    assert store.path.read_bytes() == committed
    assert store.read()["recovery"]["operation"] is None
    assert store.read()["tasks"] == []
    ledger = runtime / "deferred/20260830-120000-deferred.json"
    assert len(json.loads(ledger.read_bytes())["items"]) == 1


@pytest.mark.parametrize("operation", (_run_stall, _run_park), ids=("stall", "park"))
@pytest.mark.parametrize(
    "batch_id", ("", "../escape", "bad\nidentity", "bad\\identity")
)
def test_batch_preflight_has_no_filesystem_or_state_effects(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    operation: Callable[..., None],
    batch_id: str,
) -> None:
    store, paths, runtime = saga_environment
    service = StateService(store)
    service.set("batch.status", "idle", unsafe=True)
    service.set("batch.id", batch_id, unsafe=True)
    before = store.path.read_bytes()
    backup = store.path.with_suffix(".json.bak")
    backup_before = backup.read_bytes()
    source = paths.wip / PRD
    prd_before = source.read_bytes()

    with pytest.raises(ValueError, match="batch"):
        operation(store, paths, runtime)

    assert store.path.read_bytes() == before
    assert backup.read_bytes() == backup_before
    assert source.read_bytes() == prd_before
    assert not paths.hold.exists()
    assert not (runtime / "deferred").exists()
    service.set("batch.id", "20260830-120000", unsafe=True)
    operation(store, paths, runtime)
    assert store.read()["recovery"]["operation"] is None


@pytest.mark.parametrize("operation", (_run_stall, _run_park), ids=("stall", "park"))
def test_held_file_identity_remains_bound_through_commit(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    operation: Callable[..., None],
) -> None:
    store, paths, runtime = saga_environment
    with pytest.raises(RuntimeError):
        operation(
            store, paths, runtime, boundary_hook=_trip_at("after-append-before-commit")
        )
    before = store.path.read_bytes()
    held = paths.hold / PRD
    relocated = held.with_suffix(".retained")

    def replace(boundary: DurabilityBoundary) -> None:
        if boundary == DurabilityBoundary.STATE_TEMP_FSYNCED:
            held.rename(relocated)
            held.write_text("concurrent replacement")

    with pytest.raises(StateIOError, match="artifact identity changed"):
        operation(StateStore(store.path, boundary_hook=replace), paths, runtime)
    assert store.path.read_bytes() == before
    assert held.read_text() == "concurrent replacement"
    held.rename(held.with_suffix(".concurrent"))
    relocated.rename(held)
    operation(store, paths, runtime)
    assert store.read()["recovery"]["operation"] is None
