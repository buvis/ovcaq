from __future__ import annotations

from pathlib import Path

import pytest

from ovcaq.state.schema import State
from ovcaq.state.store import RevisionConflictError, StateStore
from ovcaq.workflow.frontmatter import apply_to_store
from ovcaq.workflow.records import (
    RecoveryConflictError,
    complete_prd_in_store,
    defer_record,
)
from ovcaq.workflow.transitions import phase_complete


@pytest.fixture
def workflow_store(tmp_path: Path, workflow_state: State) -> StateStore:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    store = StateStore(runtime / "state.json")
    store.initialize(workflow_state)
    return store


def test_frontmatter_application_maps_effective_values_in_one_cas_commit(
    workflow_store: StateStore,
) -> None:
    text = (
        "---\n"
        "catchup: skip\n"
        "design: skip\n"
        "rework_cap: 4\n"
        "pause_on_ambiguity: true\n"
        "default_model: full\n"
        "---\n"
    )

    result = apply_to_store(
        workflow_store,
        text,
        prd="00004-workflow-core-v1.md",
        available_tiers={"full"},
        expected_revision=0,
    )

    assert result.state["revision"] == 1
    assert result.state["review"]["cap"] == 4
    assert result.state["work"]["extensions"] == {
        "workflow/tier-floor": "full",
    }
    assert result.state["review"]["extensions"] == {
        "workflow/frontmatter-rework-cap-owned": True,
    }
    assert result.fields == {
        "catchup_mode": "skip",
        "design_mode": "skip",
        "pause_on_ambiguity": True,
        "rework_cap": 4,
        "tier": "full",
    }
    assert result.warnings == ()


def test_frontmatter_application_reports_overwrites_and_cas_is_fail_closed(
    workflow_store: StateStore,
) -> None:
    workflow_store.transaction(
        lambda state: state["work"]["extensions"].update(
            {"workflow/catchup-mode": "force"}
        )
    )
    before = workflow_store.path.read_bytes()

    with pytest.raises(RevisionConflictError):
        apply_to_store(
            workflow_store,
            "---\ncatchup: skip\n---\n",
            prd="00004-workflow-core-v1.md",
            expected_revision=0,
        )

    assert workflow_store.path.read_bytes() == before
    result = apply_to_store(
        workflow_store,
        "---\ncatchup: skip\n---\n",
        prd="00004-workflow-core-v1.md",
        expected_revision=1,
    )
    assert result.warnings == (
        "ovcaq: PRD frontmatter reset catchup_mode force -> skip",
    )


def test_frontmatter_application_rejects_wrong_prd_without_mutation(
    workflow_store: StateStore,
) -> None:
    before = workflow_store.path.read_bytes()

    with pytest.raises(ValueError, match="does not match active PRD"):
        apply_to_store(
            workflow_store,
            "---\nrework_cap: 5\n---\n",
            prd="00005-runtime.md",
            expected_revision=0,
        )

    assert workflow_store.path.read_bytes() == before
    assert workflow_store.read()["revision"] == 0


def test_explicit_default_cap_remains_owned_for_later_overwrite_warning(
    workflow_store: StateStore,
) -> None:
    first = apply_to_store(
        workflow_store,
        "---\nrework_cap: 3\n---\n",
        prd="00004-workflow-core-v1.md",
        expected_revision=0,
    )
    second = apply_to_store(
        workflow_store,
        "---\nrework_cap: 2\n---\n",
        prd="00004-workflow-core-v1.md",
        expected_revision=1,
    )

    assert first.warnings == ()
    assert second.warnings == ("ovcaq: PRD frontmatter reset rework_cap 3 -> 2",)


def test_phase_complete_is_one_state_store_cas_transaction(
    workflow_store: StateStore,
) -> None:
    committed = phase_complete(
        workflow_store,
        "tasks_done",
        expected_revision=0,
    )

    assert committed["revision"] == 1
    assert committed["work"]["phase"] == "review"
    assert committed["work"]["next_phase"] == "review"
    assert committed["review"]["cycle"] == 1
    with pytest.raises(RevisionConflictError):
        phase_complete(
            workflow_store,
            "rework",
            expected_revision=0,
        )


def test_recovery_intent_fences_every_competing_workflow_mutation(
    workflow_store: StateStore,
    tmp_path: Path,
) -> None:
    def stamp(state: State) -> None:
        state["recovery"]["operation"] = {
            "id": "active-operation",
            "kind": "stall",
            "step": "intent",
            "prd": "00004-workflow-core-v1.md",
            "site": "design_gate",
            "detail": "approval missing",
            "source": str(tmp_path / "wip/00004-workflow-core-v1.md"),
            "destination": str(tmp_path / "hold/00004-workflow-core-v1.md"),
            "artifact": None,
            "created_at": "2026-09-02T10:00:00Z",
        }

    workflow_store.transaction(stamp)
    before = workflow_store.path.read_bytes()
    revision = workflow_store.read()["revision"]

    operations = (
        lambda: apply_to_store(
            workflow_store,
            "---\nrework_cap: 2\n---\n",
            prd="00004-workflow-core-v1.md",
        ),
        lambda: phase_complete(workflow_store, "tasks_done"),
        lambda: complete_prd_in_store(
            workflow_store,
            "00004-workflow-core-v1.md",
        ),
        lambda: defer_record(
            workflow_store,
            tmp_path / "runtime-records",
            "00004-workflow-core-v1.md",
            {"op_id": "competing-defer"},
        ),
    )
    for operation in operations:
        with pytest.raises(RecoveryConflictError, match="active-operation"):
            operation()
        assert workflow_store.path.read_bytes() == before
        assert workflow_store.read()["revision"] == revision
    assert not (tmp_path / "runtime-records").exists()


def test_complete_prd_is_idempotent_through_state_store(
    workflow_store: StateStore,
) -> None:
    def converge(state: State) -> None:
        state["work"]["phase"] = "done"
        state["work"]["next_phase"] = "done"
        state["work"]["completed_phases"] = ["review"]

    workflow_store.transaction(converge)
    once = complete_prd_in_store(
        workflow_store,
        "00004-workflow-core-v1.md",
        expected_revision=1,
    )
    twice = complete_prd_in_store(
        workflow_store,
        "00004-workflow-core-v1.md",
        expected_revision=2,
    )

    assert once["revision"] == 2
    assert twice["revision"] == 3
    assert len(twice["batch"]["completed_prds"]) == 1


@pytest.mark.parametrize("phase", ("build", "review"))
def test_complete_prd_store_rejection_preserves_bytes_and_revision(
    workflow_store: StateStore,
    phase: str,
) -> None:
    if phase == "review":
        workflow_store.transaction(
            lambda state: state["work"].update(
                {"phase": "review", "next_phase": "review"}
            )
        )
    before = workflow_store.path.read_bytes()
    revision = workflow_store.read()["revision"]

    with pytest.raises(ValueError, match="terminal converged state"):
        complete_prd_in_store(
            workflow_store,
            "00004-workflow-core-v1.md",
            expected_revision=revision,
        )

    assert workflow_store.path.read_bytes() == before
    assert workflow_store.read()["revision"] == revision


def test_defer_public_boundary_uses_committed_batch_and_active_prd(
    workflow_store: StateStore,
    tmp_path: Path,
) -> None:
    record = {
        "op_id": "defer-boundary-1",
        "type": "decision",
        "detail": "safe follow-up",
    }

    path = defer_record(
        workflow_store,
        tmp_path / "runtime-records",
        "00004-workflow-core-v1.md",
        record,
    )
    first = path.read_bytes()
    defer_record(
        workflow_store,
        tmp_path / "runtime-records",
        "00004-workflow-core-v1.md",
        record,
    )

    assert path.name == "20260830-120000-deferred.json"
    assert path.read_bytes() == first
    with pytest.raises(ValueError, match="conflicting deferred record"):
        defer_record(
            workflow_store,
            tmp_path / "runtime-records",
            "00004-workflow-core-v1.md",
            {**record, "detail": "different follow-up"},
        )
    assert path.read_bytes() == first
    with pytest.raises(ValueError, match="active PRD"):
        defer_record(
            workflow_store,
            tmp_path / "runtime-records",
            "00005-runtime.md",
            {"op_id": "defer-boundary-2"},
        )
