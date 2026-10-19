from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from ovcaq.state.schema import State
from ovcaq.state.store import StateStore
from ovcaq.workflow.paths import LifecyclePaths, resolve_lifecycle_paths
from ovcaq.workflow.records import (
    SagaBoundary,
    park,
    stall,
)

PRD = "00004-workflow-core-v1.md"
NOW = "2026-08-30T12:30:00Z"
OPERATION_ID = "operation-04b"


@pytest.fixture
def saga_environment(
    tmp_path: Path,
    workflow_state: State,
) -> tuple[StateStore, LifecyclePaths, Path]:
    paths = resolve_lifecycle_paths(tmp_path, Path("docs/dev/project-management/prds"))
    paths.wip.mkdir(parents=True)
    paths.wip.joinpath(PRD).write_text("# Workflow core\n", encoding="utf-8")
    runtime_root = tmp_path / "docs" / "dev" / "project-management" / "ovcaq"
    runtime_root.mkdir(parents=True)
    store = StateStore(runtime_root / "state.json")
    workflow_state["tasks"] = [
        {
            "id": 1,
            "name": "saga",
            "description": "exercise recovery",
            "active_form": "Exercising recovery",
            "status": "in_progress",
            "blocked_by": [],
            "tier": None,
            "files_touched": None,
            "public_contract_edit": None,
            "estimates": {"input_tokens": None, "context_peak": None},
            "attempts": [],
            "metadata": {},
        }
    ]
    workflow_state["work"]["tasks_total"] = 1
    store.initialize(workflow_state)
    return store, paths, runtime_root


def _trip_at(name: str) -> Callable[[SagaBoundary], None]:
    def trip(boundary: SagaBoundary) -> None:
        if boundary.value == name:
            raise RuntimeError(f"failpoint: {name}")

    return trip


def _ledger(runtime_root: Path) -> dict[str, object] | None:
    path = runtime_root / "deferred" / "20260830-120000-deferred.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _run_stall(
    store: StateStore,
    paths: LifecyclePaths,
    runtime_root: Path,
    *,
    boundary_hook: Callable[[SagaBoundary], None] | None = None,
) -> None:
    stall(
        store,
        paths=paths,
        runtime_root=runtime_root,
        prd=PRD,
        site="design_gate",
        detail="design approval is missing",
        boundary_hook=boundary_hook,
        operation_id_factory=lambda: OPERATION_ID,
        now=lambda: NOW,
    )


def _run_park(
    store: StateStore,
    paths: LifecyclePaths,
    runtime_root: Path,
    *,
    boundary_hook: Callable[[SagaBoundary], None] | None = None,
) -> None:
    park(
        store,
        paths=paths,
        runtime_root=runtime_root,
        detail="session ended before handoff",
        boundary_hook=boundary_hook,
        operation_id_factory=lambda: OPERATION_ID,
        now=lambda: NOW,
    )
