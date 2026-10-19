from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

import pytest
from saga_support import (
    PRD,
    _ledger,
    _run_park,
    _run_stall,
    _trip_at,
)

from ovcaq.state.store import StateStore
from ovcaq.workflow import _files as files_module
from ovcaq.workflow.paths import LifecyclePaths
from ovcaq.workflow.records import (
    RecoveryConflictError,
    SagaBoundary,
)


@pytest.mark.parametrize("operation", (_run_stall, _run_park), ids=("stall", "park"))
@pytest.mark.parametrize(
    ("boundary", "step"),
    (
        (SagaBoundary.AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC, "moved"),
        (SagaBoundary.AFTER_APPEND_BEFORE_COMMIT, "recorded"),
    ),
)
def test_saga_deferred_directory_replacement_preserves_recovery_until_restored(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    operation: Callable[..., None],
    boundary: SagaBoundary,
    step: str,
) -> None:
    store, paths, runtime_root = saga_environment
    deferred = runtime_root / "deferred"
    relocated = runtime_root / "relocated"

    def replace(reached: SagaBoundary) -> None:
        if reached is boundary:
            deferred.rename(relocated)
            deferred.mkdir()

    with pytest.raises(OSError, match="deferred directory identity changed"):
        operation(store, paths, runtime_root, boundary_hook=replace)

    partial = store.read()
    assert partial["recovery"]["operation"]["step"] == step  # type: ignore[index]
    assert partial["tasks"] != []
    assert partial["batch"]["parks_consecutive"] == 0
    assert list(deferred.iterdir()) == []
    assert paths.hold.joinpath(PRD).is_file()
    deferred.rmdir()
    relocated.rename(deferred)
    operation(store, paths, runtime_root)
    before = store.path.read_bytes()
    operation(store, paths, runtime_root)
    assert store.path.read_bytes() == before
    assert store.read()["recovery"]["operation"] is None
    assert store.read()["tasks"] == []
    assert len(_ledger(runtime_root)["items"]) == 1  # type: ignore[index]


def test_recorded_recovery_requires_ledger_proof_after_restart(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
) -> None:
    store, paths, runtime_root = saga_environment
    with pytest.raises(RuntimeError, match="after-append-before-commit"):
        _run_stall(
            store,
            paths,
            runtime_root,
            boundary_hook=_trip_at("after-append-before-commit"),
        )
    deferred = runtime_root / "deferred"
    relocated = runtime_root / "relocated"
    deferred.rename(relocated)
    before = store.path.read_bytes()

    with pytest.raises(RecoveryConflictError, match="no matching deferred record"):
        _run_stall(store, paths, runtime_root)

    assert store.path.read_bytes() == before
    assert store.read()["tasks"] != []
    deferred.joinpath("20260830-120000-deferred.json.lock").unlink()
    deferred.rmdir()
    relocated.rename(deferred)
    _run_stall(store, paths, runtime_root)
    assert store.read()["recovery"]["operation"] is None
    assert len(_ledger(runtime_root)["items"]) == 1  # type: ignore[index]


def test_replay_after_rename_before_directory_fsync_syncs_both_lifecycle_dirs(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, paths, runtime_root = saga_environment

    with pytest.raises(RuntimeError, match="after-rename-before-directory-fsync"):
        _run_stall(
            store,
            paths,
            runtime_root,
            boundary_hook=_trip_at("after-rename-before-directory-fsync"),
        )

    operation = store.read()["recovery"]["operation"]
    assert operation is not None and operation["step"] == "intent"
    assert not paths.wip.joinpath(PRD).exists()
    assert paths.hold.joinpath(PRD).is_file()
    synced_inodes: list[int] = []
    real_fsync = files_module._fsync_directory_descriptor

    def spy_fsync(descriptor: int) -> None:
        synced_inodes.append(os.fstat(descriptor).st_ino)
        real_fsync(descriptor)

    monkeypatch.setattr(files_module, "_fsync_directory_descriptor", spy_fsync)
    _run_stall(store, paths, runtime_root)

    assert synced_inodes == [
        paths.wip.stat().st_ino,
        paths.hold.stat().st_ino,
        runtime_root.stat().st_ino,
        runtime_root.joinpath("deferred").stat().st_ino,
    ]
    assert store.read()["recovery"]["operation"] is None


@pytest.mark.parametrize("lifecycle_name", ("wip", "hold"))
def test_after_intent_rename_away_of_lifecycle_directory_fails_recoverably(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    lifecycle_name: str,
    tmp_path: Path,
) -> None:
    store, paths, runtime_root = saga_environment
    lifecycle = getattr(paths, lifecycle_name)
    relocated = lifecycle.with_name(f"relocated-{lifecycle_name}")
    external = tmp_path / f"external-after-intent-{lifecycle_name}"
    external.mkdir()
    sentinel = external / "sentinel.txt"
    sentinel.write_text("untouched\n", encoding="utf-8")

    def replace_lifecycle(boundary: SagaBoundary) -> None:
        if boundary is SagaBoundary.AFTER_INTENT_BEFORE_MOVE:
            lifecycle.rename(relocated)
            lifecycle.symlink_to(external, target_is_directory=True)

    with pytest.raises(OSError, match="lifecycle directory identity changed"):
        _run_stall(
            store,
            paths,
            runtime_root,
            boundary_hook=replace_lifecycle,
        )

    partial = store.read()
    operation = partial["recovery"]["operation"]
    assert operation is not None and operation["step"] == "intent"
    assert partial["tasks"] != []
    assert _ledger(runtime_root) is None
    assert sentinel.read_text(encoding="utf-8") == "untouched\n"
    assert not external.joinpath(PRD).exists()
    if lifecycle_name == "wip":
        assert relocated.joinpath(PRD).is_file()
        assert not paths.hold.joinpath(PRD).exists()
    else:
        assert paths.wip.joinpath(PRD).is_file()
        assert not relocated.joinpath(PRD).exists()

    lifecycle.unlink()
    relocated.rename(lifecycle)
    _run_stall(store, paths, runtime_root)

    committed = store.read()
    assert committed["recovery"]["operation"] is None
    assert committed["tasks"] == []
    assert paths.hold.joinpath(PRD).is_file()
    assert sentinel.read_text(encoding="utf-8") == "untouched\n"
    assert not external.joinpath(PRD).exists()


@pytest.mark.parametrize("lifecycle_name", ("wip", "hold"))
@pytest.mark.parametrize(
    ("boundary", "expected_step", "recorded"),
    (
        (SagaBoundary.AFTER_MOVE_BEFORE_APPEND, "moved", False),
        (SagaBoundary.AFTER_APPEND_BEFORE_COMMIT, "recorded", True),
    ),
)
def test_later_boundary_lifecycle_replacement_fails_then_reconciles(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    lifecycle_name: str,
    boundary: SagaBoundary,
    expected_step: str,
    recorded: bool,
    tmp_path: Path,
) -> None:
    store, paths, runtime_root = saga_environment
    lifecycle = getattr(paths, lifecycle_name)
    relocated = lifecycle.with_name(f"relocated-{lifecycle_name}-{boundary.value}")
    external = tmp_path / f"external-{lifecycle_name}-{boundary.value}"
    external.mkdir()
    sentinel = external / "sentinel.txt"
    sentinel.write_text("untouched\n", encoding="utf-8")

    def replace_lifecycle(reached: SagaBoundary) -> None:
        if reached is boundary:
            lifecycle.rename(relocated)
            lifecycle.symlink_to(external, target_is_directory=True)

    with pytest.raises(OSError, match="lifecycle directory identity changed"):
        _run_stall(
            store,
            paths,
            runtime_root,
            boundary_hook=replace_lifecycle,
        )

    partial = store.read()
    operation = partial["recovery"]["operation"]
    assert operation is not None and operation["step"] == expected_step
    assert partial["tasks"] != []
    assert (_ledger(runtime_root) is not None) is recorded
    assert relocated.joinpath(PRD).is_file() is (lifecycle_name == "hold")
    assert sentinel.read_text(encoding="utf-8") == "untouched\n"
    assert not external.joinpath(PRD).exists()

    lifecycle.unlink()
    relocated.rename(lifecycle)
    _run_stall(store, paths, runtime_root)

    committed = store.read()
    assert committed["recovery"]["operation"] is None
    assert committed["tasks"] == []
    assert paths.hold.joinpath(PRD).is_file()
    assert len(_ledger(runtime_root)["items"]) == 1  # type: ignore[index]
    assert sentinel.read_text(encoding="utf-8") == "untouched\n"


def test_after_intent_symlink_swap_cannot_escape_verified_hold_directory(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    tmp_path: Path,
) -> None:
    store, paths, runtime_root = saga_environment
    external = tmp_path / "external-after-intent"
    external.mkdir()
    state_before = store.path.read_bytes()

    def replace_hold(boundary: SagaBoundary) -> None:
        if boundary is SagaBoundary.AFTER_INTENT_BEFORE_MOVE:
            paths.hold.rmdir()
            paths.hold.symlink_to(external, target_is_directory=True)

    with pytest.raises(OSError):
        _run_stall(
            store,
            paths,
            runtime_root,
            boundary_hook=replace_hold,
        )

    assert not external.joinpath(PRD).exists()
    assert paths.wip.joinpath(PRD).is_file()
    assert store.read()["recovery"]["operation"] is not None
    assert store.read()["tasks"] != []
    assert store.path.read_bytes() != state_before
    assert _ledger(runtime_root) is None


@pytest.mark.parametrize("lifecycle_name", ("wip", "hold"))
def test_saga_rejects_symlinked_lifecycle_directories_without_mutation(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    lifecycle_name: str,
    tmp_path: Path,
) -> None:
    store, paths, runtime_root = saga_environment
    lifecycle = getattr(paths, lifecycle_name)
    external = tmp_path / f"external-{lifecycle_name}"
    external.mkdir()
    if lifecycle_name == "wip":
        paths.wip.joinpath(PRD).rename(external / PRD)
        paths.wip.rmdir()
    lifecycle.symlink_to(external, target_is_directory=True)
    state_before = store.path.read_bytes()

    with pytest.raises(OSError, match="lifecycle directory"):
        _run_stall(store, paths, runtime_root)

    assert store.path.read_bytes() == state_before
    assert _ledger(runtime_root) is None
    if lifecycle_name == "hold":
        assert paths.wip.joinpath(PRD).is_file()
        assert not external.joinpath(PRD).exists()
    else:
        assert external.joinpath(PRD).is_file()
