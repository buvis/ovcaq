from __future__ import annotations

import os
from collections.abc import Callable
from functools import partial
from pathlib import Path

import pytest
from saga_support import (
    NOW,
    OPERATION_ID,
    PRD,
    _ledger,
    _run_park,
    _run_stall,
    _trip_at,
)

from ovcaq.state.commands import StateService
from ovcaq.state.schema import State
from ovcaq.state.store import Mutator, StateIOError, StateStore
from ovcaq.workflow import _files as files_module
from ovcaq.workflow.paths import LifecyclePaths
from ovcaq.workflow.records import (
    RecoveryConflictError,
    park,
    stall,
)
from ovcaq.workflow.transitions import phase_complete


@pytest.mark.parametrize("operation", (_run_stall, _run_park), ids=("stall", "park"))
def test_drained_state_rejects_saga_before_filesystem_effects(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    operation: Callable[..., None],
) -> None:
    store, paths, runtime_root = saga_environment
    phase_complete(store, "drained")
    before = store.path.read_bytes()
    prd_before = paths.wip.joinpath(PRD).read_bytes()

    with pytest.raises(RecoveryConflictError, match="drained"):
        operation(store, paths, runtime_root)

    assert store.path.read_bytes() == before
    assert paths.wip.joinpath(PRD).read_bytes() == prd_before
    assert not paths.hold.exists()
    assert not runtime_root.joinpath("deferred").exists()


@pytest.mark.parametrize("conflict", ("kind", "site", "detail"))
def test_inflight_stall_requires_matching_complete_intent(
    saga_environment: tuple[StateStore, LifecyclePaths, Path], conflict: str
) -> None:
    store, paths, runtime_root = saga_environment
    operation = _run_park if conflict == "kind" else _run_stall
    with pytest.raises(RuntimeError, match="after-intent-before-move"):
        operation(
            store,
            paths,
            runtime_root,
            boundary_hook=_trip_at("after-intent-before-move"),
        )
    pending = store.read()["recovery"]["operation"]
    assert pending is not None
    before = store.path.read_bytes()

    with pytest.raises(RecoveryConflictError, match="conflicts"):
        stall(
            store,
            paths=paths,
            runtime_root=runtime_root,
            prd=PRD,
            site="different" if conflict == "site" else pending["site"],
            detail="different" if conflict == "detail" else pending["detail"],
        )

    assert store.path.read_bytes() == before
    assert paths.wip.joinpath(PRD).is_file()
    assert not paths.hold.joinpath(PRD).exists()
    assert _ledger(runtime_root) is None
    _run_park(store, paths, runtime_root)
    assert store.read()["recovery"]["operation"] is None
    assert _ledger(runtime_root)["items"][0]["kind"] == pending["kind"]  # type: ignore[index]


@pytest.mark.parametrize("step", ("moved", "recorded"))
def test_saga_checks_deferred_identity_inside_state_transaction(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    monkeypatch: pytest.MonkeyPatch,
    step: str,
) -> None:
    store, paths, runtime_root = saga_environment
    deferred = runtime_root / "deferred"
    relocated = runtime_root / "relocated"
    transaction = store.transaction

    def swap_before_mutation(
        mutator: Mutator,
        *,
        expected_revision: int | None = None,
        publication_guard: Callable[[], None] | None = None,
    ) -> State:
        pending = store.read()["recovery"]["operation"]
        if pending is not None and pending["step"] == step:
            deferred.rename(relocated)
            deferred.mkdir()
        return transaction(
            mutator,
            expected_revision=expected_revision,
            publication_guard=publication_guard,
        )

    with monkeypatch.context() as patches:
        patches.setattr(store, "transaction", swap_before_mutation)
        with pytest.raises(StateIOError, match="deferred directory identity changed"):
            _run_stall(store, paths, runtime_root)

    partial = store.read()
    assert partial["recovery"]["operation"]["step"] == step  # type: ignore[index]
    assert partial["tasks"] != []
    assert list(deferred.iterdir()) == []
    deferred.rmdir()
    relocated.rename(deferred)
    _run_stall(store, paths, runtime_root)
    assert store.read()["recovery"]["operation"] is None
    assert len(_ledger(runtime_root)["items"]) == 1  # type: ignore[index]


def _assert_boundary_ledger(
    runtime_root: Path, operation: Callable[..., None], recorded: bool
) -> None:
    ledger = _ledger(runtime_root)
    assert (ledger is not None) is recorded
    if ledger is not None:
        assert ledger["items"] == [
            {
                "detail": (
                    "design approval is missing"
                    if operation is _run_stall
                    else "session ended before handoff"
                ),
                "kind": "stall" if operation is _run_stall else "park",
                "op_id": OPERATION_ID,
                "prd": PRD,
                "site": "design_gate" if operation is _run_stall else "wrapper_died",
                "type": "stall",
            }
        ]


@pytest.mark.parametrize("operation", (_run_stall, _run_park), ids=("stall", "park"))
@pytest.mark.parametrize(
    ("boundary", "revision", "step", "in_wip", "recorded"),
    (
        ("after-mkdir-before-intent", 0, None, True, False),
        ("after-intent-before-move", 1, "intent", True, False),
        ("after-move-before-append", 2, "moved", False, False),
        ("after-append-before-commit", 3, "recorded", False, True),
        ("after-commit-before-marker-delete", 4, None, False, True),
    ),
)
def test_every_characterized_durable_boundary_replays_exactly_once(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    operation: Callable[..., None],
    boundary: str,
    revision: int,
    step: str | None,
    in_wip: bool,
    recorded: bool,
) -> None:
    store, paths, runtime_root = saga_environment

    with pytest.raises(RuntimeError, match=f"failpoint: {boundary}"):
        operation(
            store,
            paths,
            runtime_root,
            boundary_hook=_trip_at(boundary),
        )

    partial = store.read()
    assert partial["revision"] == revision
    recovery = partial["recovery"]["operation"]
    assert (None if recovery is None else recovery["step"]) == step
    assert paths.wip.joinpath(PRD).exists() is in_wip
    assert paths.hold.joinpath(PRD).exists() is (not in_wip)
    _assert_boundary_ledger(runtime_root, operation, recorded)

    operation(store, paths, runtime_root)
    committed = store.read()
    assert committed["recovery"]["operation"] is None
    assert committed["tasks"] == []
    assert committed["work"]["phase"] == "build"
    assert committed["work"]["next_phase"] == "build"
    assert len(_ledger(runtime_root)["items"]) == 1  # type: ignore[index]
    assert committed["batch"]["parks_consecutive"] == (
        0 if operation is _run_stall else 1
    )

    state_bytes = store.path.read_bytes()
    ledger_path = runtime_root / "deferred" / "20260830-120000-deferred.json"
    ledger_bytes = ledger_path.read_bytes()
    operation(store, paths, runtime_root)
    assert store.path.read_bytes() == state_bytes
    assert ledger_path.read_bytes() == ledger_bytes


def test_recovery_operation_preserves_raw_failure_evidence(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
) -> None:
    store, paths, runtime_root = saga_environment

    paths.wip.joinpath(PRD).unlink()
    with pytest.raises(OSError, match="not present in wip or hold"):
        _run_stall(store, paths, runtime_root)

    operation = store.read()["recovery"]["operation"]
    assert operation is not None
    assert operation == {
        "id": OPERATION_ID,
        "kind": "stall",
        "step": "intent",
        "prd": PRD,
        "site": "design_gate",
        "detail": "design approval is missing",
        "source": str(paths.wip / PRD),
        "destination": str(paths.hold / PRD),
        "artifact": None,
        "created_at": NOW,
    }
    assert _ledger(runtime_root) is None


def test_conflicting_recovery_refuses_without_filesystem_effects(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
) -> None:
    store, paths, runtime_root = saga_environment
    with pytest.raises(RuntimeError):
        _run_stall(
            store,
            paths,
            runtime_root,
            boundary_hook=_trip_at("after-intent-before-move"),
        )
    before = store.path.read_bytes()

    with pytest.raises(RecoveryConflictError, match=PRD):
        stall(
            store,
            paths=paths,
            runtime_root=runtime_root,
            prd="00005-runtime.md",
            site="other",
            detail="other failure",
        )

    assert store.path.read_bytes() == before
    assert paths.wip.joinpath(PRD).exists()
    assert _ledger(runtime_root) is None


def test_inactive_held_prd_is_not_mistaken_for_a_replay(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
) -> None:
    store, paths, runtime_root = saga_environment
    inactive_prd = "00003-inactive.md"
    paths.hold.mkdir()
    paths.hold.joinpath(inactive_prd).write_text("# Inactive\n", encoding="utf-8")
    state_before = store.path.read_bytes()
    held_before = paths.hold.joinpath(inactive_prd).read_bytes()

    with pytest.raises(RecoveryConflictError, match="does not match active PRD"):
        stall(
            store,
            paths=paths,
            runtime_root=runtime_root,
            prd=inactive_prd,
            site="design_gate",
            detail="unrelated request",
        )

    assert store.path.read_bytes() == state_before
    assert paths.hold.joinpath(inactive_prd).read_bytes() == held_before
    assert paths.wip.joinpath(PRD).is_file()
    assert _ledger(runtime_root) is None


def test_active_held_prd_without_durable_proof_fails_closed(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
) -> None:
    store, paths, runtime_root = saga_environment
    paths.hold.mkdir()
    paths.wip.joinpath(PRD).rename(paths.hold / PRD)
    state_before = store.path.read_bytes()
    held_before = paths.hold.joinpath(PRD).read_bytes()

    with pytest.raises(RecoveryConflictError, match="durable recovery proof"):
        _run_stall(store, paths, runtime_root)

    assert store.path.read_bytes() == state_before
    assert paths.hold.joinpath(PRD).read_bytes() == held_before
    assert len(store.read()["tasks"]) == 1
    assert _ledger(runtime_root) is None


def test_no_intent_replay_requires_matching_ledger_and_committed_reset(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
) -> None:
    store, paths, runtime_root = saga_environment
    _run_stall(store, paths, runtime_root)
    before = store.path.read_bytes()

    result = stall(
        store,
        paths=paths,
        runtime_root=runtime_root,
        prd=PRD,
        site="design_gate",
        detail="design approval is missing",
    )

    assert result.operation_id == OPERATION_ID
    assert result.replayed is True
    assert store.path.read_bytes() == before


@pytest.mark.parametrize("kind", ("stall", "park"))
def test_exact_replay_uses_recorded_kind_and_rejects_kind_collision(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    kind: str,
) -> None:
    store, paths, runtime_root = saga_environment
    detail = "session ended without a committed transition"

    def set_park_history(state: State) -> None:
        state["batch"]["parks_consecutive"] = 1

    store.transaction(set_park_history)

    stall_call = partial(
        stall,
        store,
        paths=paths,
        runtime_root=runtime_root,
        prd=PRD,
        site="wrapper_died",
        detail=detail,
    )
    park_call = partial(
        park, store, paths=paths, runtime_root=runtime_root, detail=detail
    )
    exact = stall_call if kind == "stall" else park_call
    collision = park_call if kind == "stall" else stall_call
    expected_parks = 0 if kind == "stall" else 2
    expected_phase = "build" if kind == "stall" else "paused"
    first = exact(operation_id_factory=lambda: OPERATION_ID, now=lambda: NOW)

    assert first.kind == kind
    committed_bytes = store.path.read_bytes()
    ledger_bytes = (
        runtime_root / "deferred" / "20260830-120000-deferred.json"
    ).read_bytes()
    assert _ledger(runtime_root)["items"][0]["kind"] == kind  # type: ignore[index]
    assert store.read()["batch"]["parks_consecutive"] == expected_parks
    assert store.read()["work"]["phase"] == expected_phase

    assert exact().kind == kind
    assert store.path.read_bytes() == committed_bytes
    assert (
        runtime_root / "deferred" / "20260830-120000-deferred.json"
    ).read_bytes() == ledger_bytes

    with pytest.raises(RecoveryConflictError, match="durable recovery proof"):
        collision()
    assert store.path.read_bytes() == committed_bytes


def test_replay_after_record_replace_syncs_record_dir_before_state_advance(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, paths, runtime_root = saga_environment

    with pytest.raises(RuntimeError, match="after-replace-before-directory-fsync"):
        _run_stall(
            store,
            paths,
            runtime_root,
            boundary_hook=_trip_at("after-replace-before-directory-fsync"),
        )

    operation = store.read()["recovery"]["operation"]
    assert operation is not None and operation["step"] == "moved"
    assert _ledger(runtime_root) is not None
    synced_steps: list[str | None] = []
    deferred = runtime_root / "deferred"
    real_fsync = files_module._fsync_directory_descriptor

    def spy_fsync(directory: int) -> None:
        if os.fstat(directory).st_ino == deferred.stat().st_ino:
            current = store.read()["recovery"]["operation"]
            synced_steps.append(None if current is None else current["step"])
        real_fsync(directory)

    monkeypatch.setattr(files_module, "_fsync_directory_descriptor", spy_fsync)
    _run_stall(store, paths, runtime_root)

    assert synced_steps == ["moved"]
    assert store.read()["recovery"]["operation"] is None


def test_creating_hold_fsyncs_its_parent_before_intent(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, paths, runtime_root = saga_environment
    synced: list[Path] = []
    real_fsync = files_module._fsync_directory

    def spy_fsync(directory: Path) -> None:
        synced.append(directory)
        real_fsync(directory)

    monkeypatch.setattr(files_module, "_fsync_directory", spy_fsync)
    with pytest.raises(RuntimeError, match="after-mkdir-before-intent"):
        _run_stall(
            store,
            paths,
            runtime_root,
            boundary_hook=_trip_at("after-mkdir-before-intent"),
        )

    assert paths.hold.parent in synced
    assert store.read()["recovery"]["operation"] is None


def test_active_recovery_fences_phase_complete_then_reconciles(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
) -> None:
    store, paths, runtime_root = saga_environment
    with pytest.raises(RuntimeError, match="after-intent-before-move"):
        _run_stall(
            store,
            paths,
            runtime_root,
            boundary_hook=_trip_at("after-intent-before-move"),
        )
    state_before = store.path.read_bytes()
    revision_before = store.read()["revision"]

    with pytest.raises(RecoveryConflictError, match="recovery operation"):
        phase_complete(store, "tasks_done")

    assert store.path.read_bytes() == state_before
    assert store.read()["revision"] == revision_before
    _run_stall(store, paths, runtime_root)
    assert store.read()["recovery"]["operation"] is None
    assert store.read()["tasks"] == []


@pytest.mark.parametrize(
    "mutation",
    (
        pytest.param(
            lambda service: service.add_task({"name": "concurrent task"}),
            id="task",
        ),
        pytest.param(
            lambda service: service.set_contract_card("concurrent contract"),
            id="contract",
        ),
        pytest.param(
            lambda service: service.set(
                'work.extensions["tests/recovery"]',
                {"concurrent": True},
            ),
            id="allowed-generic",
        ),
    ),
)
def test_public_state_mutations_reject_active_recovery_then_reconcile(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
    mutation: Callable[[StateService], object],
) -> None:
    store, paths, runtime_root = saga_environment
    with pytest.raises(RuntimeError, match="after-intent-before-move"):
        _run_stall(
            store,
            paths,
            runtime_root,
            boundary_hook=_trip_at("after-intent-before-move"),
        )
    state_before = store.path.read_bytes()
    revision_before = store.read()["revision"]

    with pytest.raises(ValueError, match="recovery operation"):
        mutation(StateService(store))

    assert store.path.read_bytes() == state_before
    assert store.read()["revision"] == revision_before
    _run_stall(store, paths, runtime_root)
    committed = store.read()
    assert committed["recovery"]["operation"] is None
    assert committed["tasks"] == []
    assert committed["work"]["contract_card"] is None
    assert committed["work"]["extensions"] == {}


def test_park_reconciles_pending_stall_without_incrementing_park_breaker(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
) -> None:
    store, paths, runtime_root = saga_environment
    with pytest.raises(RuntimeError):
        _run_stall(
            store,
            paths,
            runtime_root,
            boundary_hook=_trip_at("after-intent-before-move"),
        )

    _run_park(store, paths, runtime_root)

    state = store.read()
    assert state["recovery"]["operation"] is None
    assert state["batch"]["parks_consecutive"] == 0
    assert _ledger(runtime_root)["items"] == [  # type: ignore[index]
        {
            "detail": "design approval is missing",
            "kind": "stall",
            "op_id": OPERATION_ID,
            "prd": PRD,
            "site": "design_gate",
            "type": "stall",
        }
    ]


def test_second_consecutive_park_commits_reset_and_systemic_pause_together(
    saga_environment: tuple[StateStore, LifecyclePaths, Path],
) -> None:
    store, paths, runtime_root = saga_environment
    _run_park(store, paths, runtime_root)
    second_prd = "00005-runtime.md"
    paths.wip.joinpath(second_prd).write_text("# Runtime\n", encoding="utf-8")

    def select_second(state: State) -> None:
        state["work"]["prd"] = second_prd
        state["tasks"] = []
        state["work"]["tasks_total"] = 0

    store.transaction(select_second)
    result = park(
        store,
        paths=paths,
        runtime_root=runtime_root,
        detail="second session ended before handoff",
        operation_id_factory=lambda: "operation-second",
        now=lambda: NOW,
    )

    state = store.read()
    assert result.systemic_halt is True
    assert state["batch"]["parks_consecutive"] == 2
    assert state["work"]["phase"] == "paused"
    assert state["work"]["next_phase"] == "paused"
    assert state["control"]["pause_reason"] == {
        "site": "systemic_park",
        "detail": "2 consecutive PRDs parked via wrapper_died; batch halted",
        "created_at": NOW,
    }
    assert state["recovery"]["operation"] is None
