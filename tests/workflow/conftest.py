from __future__ import annotations

from pathlib import Path

import pytest

from ovcaq.state.schema import State, new_state


@pytest.fixture
def workflow_state(tmp_path: Path) -> State:
    state = new_state(repo_root=tmp_path)
    state["batch"].update(
        {
            "id": "20260830-120000",
            "status": "running",
            "started_at": "2026-08-30T12:00:00Z",
        }
    )
    state["work"]["prd"] = "00004-workflow-core-v1.md"
    return state


from saga_support import saga_environment  # noqa: F401
