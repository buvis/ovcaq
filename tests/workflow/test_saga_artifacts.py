from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from saga_support import PRD, _ledger, _run_park, _run_stall, _trip_at

from ovcaq.state.store import StateStore
from ovcaq.workflow import records
from ovcaq.workflow.paths import LifecyclePaths


def _replace(path: Path, retained: Path) -> None:
    path.rename(retained)
    path.write_text("different concurrent PRD\n")


def _restore_and_reconcile(
    environment: tuple[StateStore, LifecyclePaths, Path],
    operation: Callable[..., None],
    retained: Path,
) -> None:
    store, paths, runtime = environment
    held = paths.hold / PRD
    held.rename(held.with_suffix(".replacement"))
    retained.rename(held)
    operation(store, paths, runtime)
    before = store.path.read_bytes()
    operation(store, paths, runtime)
    assert store.path.read_bytes() == before
    assert store.read()["recovery"]["operation"] is None
    assert store.read()["tasks"] == []
    assert len(_ledger(runtime)["items"]) == 1
    assert held.read_text() == "# Workflow core\n"


@pytest.mark.parametrize("operation", (_run_stall, _run_park), ids=("stall", "park"))
@pytest.mark.parametrize("replacement", ("before-rename", "after-rename"))
def test_substituted_prd_never_resets_unfinished_work(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    operation: Callable[..., None],
    replacement: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, paths, runtime = saga_environment
    retained = runtime / "original.md"
    before_tasks = store.read()["tasks"]
    native_rename = records.rename_exclusive

    def rename(*args: object, **kwargs: object) -> None:
        if replacement == "before-rename":
            _replace(paths.wip / PRD, retained)
        native_rename(*args, **kwargs)

    def boundary(reached: records.SagaBoundary) -> None:
        if (
            replacement == "after-rename"
            and reached is records.SagaBoundary.AFTER_RENAME_BEFORE_DIRECTORY_FSYNC
        ):
            _replace(paths.hold / PRD, retained)

    with monkeypatch.context() as patches:
        patches.setattr(records, "rename_exclusive", rename)
        with pytest.raises(OSError, match="PRD artifact identity changed"):
            operation(store, paths, runtime, boundary_hook=boundary)

    assert store.read()["tasks"] == before_tasks
    assert store.read()["recovery"]["operation"]["step"] == "intent"
    assert _ledger(runtime) is None
    assert retained.read_text() == "# Workflow core\n"
    _restore_and_reconcile(saga_environment, operation, retained)


@pytest.mark.parametrize("operation", (_run_stall, _run_park), ids=("stall", "park"))
@pytest.mark.parametrize(
    "boundary",
    (
        "after-rename-before-directory-fsync",
        "after-move-before-append",
        "after-append-before-commit",
    ),
)
def test_restarted_saga_requires_original_held_artifact(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    operation: Callable[..., None],
    boundary: str,
) -> None:
    store, paths, runtime = saga_environment
    with pytest.raises(RuntimeError, match=boundary):
        operation(store, paths, runtime, boundary_hook=_trip_at(boundary))
    retained = runtime / "original.md"
    _replace(paths.hold / PRD, retained)
    before = store.path.read_bytes()
    ledger_before = _ledger(runtime)

    with pytest.raises(OSError, match="PRD artifact identity changed"):
        operation(StateStore(store.path), paths, runtime)

    assert store.path.read_bytes() == before
    assert store.read()["tasks"] != []
    assert _ledger(runtime) == ledger_before
    assert retained.read_text() == "# Workflow core\n"
    _restore_and_reconcile(saga_environment, operation, retained)
