from __future__ import annotations

from pathlib import Path

import pytest

from ovcaq.state.schema import State, new_state
from ovcaq.state.store import StateStore
from ovcaq.workflow import transitions


@pytest.mark.parametrize("status", ("idle", "attention", "completed"))
@pytest.mark.parametrize(("phase", "outcome"), tuple(transitions.TRANSITIONS))
def test_nonrunning_batch_cannot_transition(
    workflow_state: State, tmp_path: Path, status: str, phase: str, outcome: str
) -> None:
    workflow_state["batch"]["status"] = status
    workflow_state["work"]["phase"] = phase
    workflow_state["work"]["next_phase"] = phase
    if status == "completed":
        workflow_state["batch"]["completed_at"] = "2026-08-30T13:00:00Z"
    store = StateStore(tmp_path / "state.json")
    store.initialize(workflow_state)
    before = store.path.read_bytes()

    with pytest.raises(transitions.UnknownTransition, match="running batch"):
        transitions.phase_complete(store, outcome)

    assert store.path.read_bytes() == before
    assert not store.path.with_suffix(".json.bak").exists()


@pytest.mark.parametrize(
    ("phase", "outcome"),
    (
        ("build", "tasks_done"),
        ("review", "rework"),
        ("review", "converged"),
        ("done", "more_prds"),
        ("done", "drained"),
    ),
)
def test_prd_transition_requires_an_active_prd(
    workflow_state: State, tmp_path: Path, phase: str, outcome: str
) -> None:
    workflow_state["work"]["prd"] = None
    workflow_state["work"]["phase"] = phase
    workflow_state["work"]["next_phase"] = phase
    store = StateStore(tmp_path / "state.json")
    store.initialize(workflow_state)
    before = store.path.read_bytes()

    with pytest.raises(transitions.UnknownTransition, match="active PRD"):
        transitions.phase_complete(store, outcome)

    assert store.path.read_bytes() == before
    assert not store.path.with_suffix(".json.bak").exists()


def test_empty_running_batch_can_drain_without_a_prd(workflow_state: State) -> None:
    workflow_state["work"]["prd"] = None

    result = transitions.apply(workflow_state, "drained")

    assert result["work"]["phase"] == "done"
    assert result["work"]["next_phase"] == ""
    assert result["batch"]["status"] == "running"


def test_fresh_state_cannot_skip_into_review(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.json")
    store.initialize(new_state(repo_root=tmp_path))
    before = store.path.read_bytes()

    with pytest.raises(transitions.UnknownTransition, match="running batch"):
        transitions.phase_complete(store, "tasks_done")

    assert store.path.read_bytes() == before
