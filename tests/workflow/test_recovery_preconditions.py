from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from saga_support import PRD, _ledger, _run_park, _run_stall, _trip_at

from ovcaq.state.commands import StateMutationConflictError, StateService
from ovcaq.state.schema import ArtifactIdentity, State
from ovcaq.state.store import DurabilityBoundary, StateIOError, StateStore
from ovcaq.workflow.paths import LifecyclePaths


@pytest.mark.parametrize("operation", (_run_stall, _run_park), ids=("stall", "park"))
def test_existing_destination_rejects_intent_without_mutating_state(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    operation: Callable[..., None],
) -> None:
    store, paths, runtime = saga_environment
    StateService(store).set_contract_card("retained contract")
    paths.hold.mkdir()
    paths.hold.joinpath(PRD).write_text("competing work")
    before = store.path.read_bytes()
    backup = store.path.with_suffix(".json.bak").read_bytes()

    with pytest.raises(OSError, match="both wip and hold"):
        operation(store, paths, runtime)

    assert store.path.read_bytes() == before
    assert store.path.with_suffix(".json.bak").read_bytes() == backup
    assert paths.wip.joinpath(PRD).read_text() == "# Workflow core\n"
    assert paths.hold.joinpath(PRD).read_text() == "competing work"
    assert _ledger(runtime) is None


@pytest.mark.parametrize("boundary", tuple(DurabilityBoundary))
def test_source_identity_is_guarded_through_intent_publication(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    boundary: DurabilityBoundary,
) -> None:
    store, paths, runtime = saga_environment
    StateService(store).set_contract_card("retained contract")
    before = store.path.read_bytes()
    backup = store.path.with_suffix(".json.bak").read_bytes()
    source = paths.wip / PRD
    retained = paths.wip / "retained.md"

    def substitute(reached: DurabilityBoundary) -> None:
        if reached == boundary:
            source.rename(retained)
            source.write_text("replacement work")

    with pytest.raises(StateIOError, match="artifact identity changed"):
        _run_stall(StateStore(store.path, boundary_hook=substitute), paths, runtime)

    assert store.path.read_bytes() == before
    assert store.path.with_suffix(".json.bak").read_bytes() == backup
    assert source.read_text() == "replacement work"
    assert retained.read_text() == "# Workflow core\n"
    assert _ledger(runtime) is None


def test_restore_recovers_an_old_unbound_intent_without_touching_prds(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
) -> None:
    store, paths, runtime = saga_environment
    initial = store.read()
    with pytest.raises(RuntimeError, match="after-intent-before-move"):
        _run_stall(
            store, paths, runtime, boundary_hook=_trip_at("after-intent-before-move")
        )
    # Model the old writer's invalid intent while retaining its actual backup.
    pending = store.read()
    pending["recovery"]["operation"]["artifact"] = None
    legacy = StateStore(runtime / "legacy.json")
    legacy.initialize(initial)
    legacy.transaction(lambda _state: pending)
    before_backup = legacy.path.with_suffix(".json.bak").read_bytes()

    result = StateService(legacy).restore(expected_revision=1)

    assert result["revision"] == 2
    assert legacy.read() == {**initial, "revision": 2}
    assert paths.wip.joinpath(PRD).read_text() == "# Workflow core\n"
    assert not paths.hold.joinpath(PRD).exists()
    assert _ledger(runtime) is None
    assert before_backup == store.path.with_suffix(".json.bak").read_bytes()


@pytest.mark.parametrize(
    ("step", "artifact"),
    (
        ("intent", {"device": 1, "inode": 2}),
        ("moved", {"device": 1, "inode": 2}),
        ("recorded", {"device": 1, "inode": 2}),
        ("moved", None),
        ("recorded", None),
    ),
)
def test_restore_keeps_bound_recovery_fenced(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    step: str,
    artifact: ArtifactIdentity | None,
) -> None:
    store, paths, runtime = saga_environment
    with pytest.raises(RuntimeError, match="after-intent-before-move"):
        _run_stall(
            store, paths, runtime, boundary_hook=_trip_at("after-intent-before-move")
        )

    def advance(state: State) -> None:
        state["recovery"]["operation"]["step"] = step
        state["recovery"]["operation"]["artifact"] = artifact

    store.transaction(advance)
    before = store.path.read_bytes()
    backup = store.path.with_suffix(".json.bak").read_bytes()

    with pytest.raises(StateMutationConflictError, match="reconcile it first"):
        StateService(store).restore()

    assert store.path.read_bytes() == before
    assert store.path.with_suffix(".json.bak").read_bytes() == backup
