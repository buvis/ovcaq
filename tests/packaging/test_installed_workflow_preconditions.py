from __future__ import annotations

import json
from pathlib import Path

import pytest
from packaging_support import (
    InstalledWheel,
    _installed_workflow_root,
    _run,
    _run_unchecked,
    stall_command,
    workflow_command,
)


def test_installed_fresh_init_rejects_phase_handoff_without_mutation(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    root = tmp_path / "fresh-project"
    root.mkdir()
    prefix = [installed_wheel.console_script, "--root", root, "--json"]
    _run([*prefix, "init"], cwd=root, installed_wheel=installed_wheel)
    state = root / "docs/dev/project-management/ovcaq/state.json"
    before = state.read_bytes()

    result = _run_unchecked(
        [*prefix, "workflow", "phase-complete", "--outcome", "tasks_done"],
        cwd=root,
        installed_wheel=installed_wheel,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    error = json.loads(result.stderr)["error"]
    assert error["code"] == "usage"
    assert "running batch" in error["message"]
    assert state.read_bytes() == before
    assert not state.with_suffix(".json.bak").exists()


@pytest.mark.parametrize("command", ("stall", "park"))
def test_installed_rejected_recovery_remains_retryable(
    installed_wheel: InstalledWheel, tmp_path: Path, command: str
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    prds = root / "docs/dev/project-management/prds"
    prd = "00004-workflow-core-v1.md"
    prds.joinpath("backlog").mkdir(exist_ok=True)
    prds.joinpath("wip", prd).rename(prds / "backlog" / prd)
    state = root / "docs/dev/project-management/ovcaq/state.json"
    before = state.read_bytes()
    backup = state.with_suffix(".json.bak").read_bytes()
    argv = (
        stall_command(installed_wheel, root, site="gate", detail="later")
        if command == "stall"
        else workflow_command(installed_wheel, root, "park")
    )

    result = _run_unchecked(argv, cwd=root, installed_wheel=installed_wheel)

    assert result.returncode == 2
    error = json.loads(result.stderr)["error"]
    assert error["code"] == "state_io"
    assert "not present in wip or hold" in error["message"]
    assert state.read_bytes() == before
    assert state.with_suffix(".json.bak").read_bytes() == backup
    prds.joinpath("backlog", prd).rename(prds / "wip" / prd)
    _run(argv, cwd=root, installed_wheel=installed_wheel)
    assert json.loads(state.read_bytes())["recovery"]["operation"] is None
    assert prds.joinpath("hold", prd).is_file()
    assert not prds.joinpath("wip", prd).exists()


def test_installed_restore_recovers_legacy_unbound_intent(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    state_file = root / "docs/dev/project-management/ovcaq/state.json"
    initial = json.loads(state_file.read_bytes())
    source = root / "docs/dev/project-management/prds/wip/00004-workflow-core-v1.md"
    original = source.read_bytes()
    legacy_writer = """
import sys
from pathlib import Path
from ovcaq.paths import state_path
from ovcaq.state.store import StateStore
root = Path(sys.argv[1])
def stamp(state):
    prd = state["work"]["prd"]
    paths = root / "docs/dev/project-management/prds"
    state["recovery"]["operation"] = {
        "id": "legacy-intent", "kind": "stall", "step": "intent", "prd": prd,
        "site": "gate", "detail": "missing source", "artifact": None,
        "source": str(paths / "wip" / prd), "destination": str(paths / "hold" / prd),
        "created_at": "2026-10-25T00:00:00Z",
    }
StateStore(state_path(root)).transaction(stamp)
"""
    _run(
        [installed_wheel.python, "-c", legacy_writer, root],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    failed_intent = state_file.read_bytes()

    result = _run(
        [
            installed_wheel.console_script,
            "--root",
            root,
            "--json",
            "state",
            "restore",
            "--expected-revision",
            str(initial["revision"] + 1),
        ],
        cwd=root,
        installed_wheel=installed_wheel,
    )

    assert json.loads(result.stdout)["revision"] == initial["revision"] + 2
    assert json.loads(state_file.read_bytes()) == {
        **initial,
        "revision": initial["revision"] + 2,
    }
    assert state_file.with_suffix(".json.bak").read_bytes() == failed_intent
    assert source.read_bytes() == original
