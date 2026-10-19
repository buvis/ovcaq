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
from sagas_scripts import (
    INTENT_CONFLICT,
    INTERRUPT_STALL,
    REPLACE_DEFERRED,
)

SET_PARK_HISTORY = """
import sys
from pathlib import Path
from ovcaq.paths import state_path
from ovcaq.state.store import StateStore
StateStore(state_path(Path(sys.argv[1]))).transaction(
    lambda state: state["batch"].update({"parks_consecutive": 1})
)
"""


@pytest.mark.parametrize("conflict", ("kind", "site", "detail"))
def test_installed_stall_rejects_conflicting_inflight_intent(
    installed_wheel: InstalledWheel, tmp_path: Path, conflict: str
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    interrupt_script = INTENT_CONFLICT
    _run(
        [installed_wheel.python, "-c", interrupt_script, root, conflict],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    state = root / "docs/dev/project-management/ovcaq/state.json"
    before = state.read_bytes()
    prefix = [installed_wheel.console_script, "--root", root, "--json", "workflow"]
    result = _run_unchecked(
        [
            *prefix,
            "stall",
            "--prd",
            "00004-workflow-core-v1.md",
            "--site",
            "different" if conflict == "site" else "wrapper_died",
            "--detail",
            "different"
            if conflict == "detail"
            else "session ended without a committed transition",
        ],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    assert result.returncode == 1
    assert "conflicts" in json.loads(result.stderr)["error"]["message"]
    assert state.read_bytes() == before
    assert root.joinpath(
        "docs/dev/project-management/prds/wip/00004-workflow-core-v1.md"
    ).is_file()
    assert not root.joinpath("docs/dev/project-management/ovcaq/deferred").exists()

    reconciled = _run([*prefix, "park"], cwd=root, installed_wheel=installed_wheel)
    assert json.loads(reconciled.stdout)["result"]["kind"] == (
        "park" if conflict == "kind" else "stall"
    )


@pytest.mark.parametrize(
    ("command", "boundary", "step"),
    (
        ("defer", "before-publish", None),
        ("defer", "after-replace-before-directory-fsync", None),
        ("defer", "after-publish", None),
        ("stall", "after-replace-before-directory-fsync", "moved"),
        ("stall", "after-append-before-commit", "recorded"),
        ("park", "after-replace-before-directory-fsync", "moved"),
        ("park", "after-append-before-commit", "recorded"),
    ),
)
def test_installed_deferred_directory_replacement_fails_then_reconciles(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    command: str,
    boundary: str,
    step: str | None,
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    record = root / "record.json"
    record.write_text(
        json.dumps({"op_id": "installed-defer", "detail": "later"}), encoding="utf-8"
    )
    script = REPLACE_DEFERRED
    state = root / "docs/dev/project-management/ovcaq/state.json"
    before = state.read_bytes()
    result = _run_unchecked(
        [installed_wheel.python, "-c", script, root, command, boundary],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    assert result.returncode == 2
    error = json.loads(result.stderr)["error"]
    assert error["code"] == "state_io"
    assert "deferred directory identity changed" in error["message"]
    partial = json.loads(state.read_bytes())
    assert partial["tasks"] == json.loads(before)["tasks"]
    assert partial["batch"]["parks_consecutive"] == 0
    pending = partial["recovery"]["operation"]
    assert (pending["step"] if pending else None) == step
    deferred = root / "docs/dev/project-management/ovcaq/deferred"
    assert list(deferred.iterdir()) == []
    relocated = deferred.with_name("relocated")
    assert not list(relocated.glob("*.tmp"))
    deferred.rmdir()
    relocated.rename(deferred)
    prefix = workflow_command(installed_wheel, root, command)
    if command == "defer":
        prefix += ["--prd", "00004-workflow-core-v1.md", "--record", record]
    elif command == "stall":
        prefix = stall_command(installed_wheel, root, site="gate", detail="later")
    _run(prefix, cwd=root, installed_wheel=installed_wheel)
    ledger = deferred / "installed-batch-deferred.json"
    committed = state.read_bytes()
    ledger_bytes = ledger.read_bytes()
    _run(prefix, cwd=root, installed_wheel=installed_wheel)
    assert state.read_bytes() == committed
    assert ledger.read_bytes() == ledger_bytes
    assert len(json.loads(ledger_bytes)["items"]) == 1
    assert json.loads(committed)["recovery"]["operation"] is None


def test_installed_defer_distinguishes_exact_replay_from_conflicting_operation_id(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    record = root / "record.json"
    record.write_text(
        json.dumps({"op_id": "installed-op", "detail": "first"}),
        encoding="utf-8",
    )
    command = [
        installed_wheel.console_script,
        "--root",
        root,
        "--json",
        "workflow",
        "defer",
        "--prd",
        "00004-workflow-core-v1.md",
        "--record",
        record,
    ]
    _run(command, cwd=root, installed_wheel=installed_wheel)
    ledger = (
        root
        / "docs/dev/project-management/ovcaq/deferred/installed-batch-deferred.json"
    )
    first = ledger.read_bytes()

    _run(command, cwd=root, installed_wheel=installed_wheel)
    assert ledger.read_bytes() == first

    record.write_text(
        json.dumps({"op_id": "installed-op", "detail": "conflict"}),
        encoding="utf-8",
    )
    conflict = _run_unchecked(command, cwd=root, installed_wheel=installed_wheel)
    assert conflict.returncode == 1
    error = json.loads(conflict.stderr)["error"]
    assert error["code"] == "usage"
    assert "conflicting deferred record" in error["message"]
    assert ledger.read_bytes() == first


def test_installed_stall_rejects_active_held_prd_without_durable_proof(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    root.joinpath(
        "docs/dev/project-management/prds/wip/00004-workflow-core-v1.md"
    ).unlink()
    held = root / "docs/dev/project-management/prds/hold/00004-workflow-core-v1.md"
    held.parent.mkdir(parents=True)
    held.write_text("# Held\n", encoding="utf-8")
    state = root / "docs/dev/project-management/ovcaq/state.json"
    before = state.read_bytes()

    result = _run_unchecked(
        [
            installed_wheel.console_script,
            "--root",
            root,
            "--json",
            "workflow",
            "stall",
            "--prd",
            "00004-workflow-core-v1.md",
            "--site",
            "design_gate",
            "--detail",
            "approval missing",
        ],
        cwd=root,
        installed_wheel=installed_wheel,
    )

    assert result.returncode == 1
    assert "durable recovery proof" in result.stderr
    assert state.read_bytes() == before
    assert held.read_text(encoding="utf-8") == "# Held\n"


@pytest.mark.parametrize("kind", ("stall", "park"))
def test_installed_stall_and_park_exact_replay_reject_kind_collision(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    kind: str,
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    _run(
        [installed_wheel.python, "-c", SET_PARK_HISTORY, root],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    detail = "session ended without a committed transition"
    prefix = [installed_wheel.console_script, "--root", root, "--json", "workflow"]
    stalled_command = stall_command(
        installed_wheel, root, site="wrapper_died", detail=detail
    )
    park_command = [*prefix, "park"]
    exact_command = stalled_command if kind == "stall" else park_command
    collision_command = park_command if kind == "stall" else stalled_command

    first = _run_unchecked(exact_command, cwd=root, installed_wheel=installed_wheel)
    assert first.returncode == (4 if kind == "park" else 0)
    assert json.loads(first.stdout)["result"]["kind"] == kind
    state = root / "docs/dev/project-management/ovcaq/state.json"
    ledger = (
        root
        / "docs/dev/project-management/ovcaq/deferred/installed-batch-deferred.json"
    )
    state_bytes = state.read_bytes()
    ledger_bytes = ledger.read_bytes()
    durable_record = json.loads(ledger_bytes)["items"][0]
    assert durable_record["kind"] == kind
    committed = json.loads(state_bytes)
    assert committed["batch"]["parks_consecutive"] == (0 if kind == "stall" else 2)
    assert committed["work"]["phase"] == ("build" if kind == "stall" else "paused")

    replay = _run_unchecked(exact_command, cwd=root, installed_wheel=installed_wheel)
    assert replay.returncode == (4 if kind == "park" else 0)
    assert json.loads(replay.stdout)["result"]["kind"] == kind
    assert state.read_bytes() == state_bytes
    assert ledger.read_bytes() == ledger_bytes
    collision = _run_unchecked(
        collision_command,
        cwd=root,
        installed_wheel=installed_wheel,
    )
    assert collision.returncode == 1
    assert "durable recovery proof" in collision.stderr
    assert state.read_bytes() == state_bytes
    assert ledger.read_bytes() == ledger_bytes


def _concurrent_state_command(
    installed_wheel: InstalledWheel, root: Path, mutation: str
) -> list[str | Path]:
    task = root / "task.json"
    task.write_text(json.dumps({"name": "concurrent"}), encoding="utf-8")
    contract = root / "contract.md"
    contract.write_text("concurrent contract\n", encoding="utf-8")
    prefix = [installed_wheel.console_script, "--root", root, "--json", "state"]
    commands = {
        "task": [*prefix, "task", "add", task],
        "contract": [*prefix, "contract", "set", contract],
        "set": [
            *prefix,
            "set",
            'work.extensions["tests/recovery"]',
            '{"concurrent":true}',
        ],
    }
    return commands[mutation]


@pytest.mark.parametrize("mutation", ("task", "contract", "set"))
def test_installed_state_mutations_reject_active_recovery_then_reconcile(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    mutation: str,
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    interrupt_after_intent = INTERRUPT_STALL
    _run(
        [installed_wheel.python, "-c", interrupt_after_intent, root],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    state_path = root / "docs/dev/project-management/ovcaq/state.json"
    state_before = state_path.read_bytes()
    command = _concurrent_state_command(installed_wheel, root, mutation)
    rejected = _run_unchecked(command, cwd=root, installed_wheel=installed_wheel)
    assert rejected.returncode == 1
    error = json.loads(rejected.stderr)["error"]
    assert error["code"] == "usage"
    assert "recovery operation" in error["message"]
    assert state_path.read_bytes() == state_before

    _run(
        stall_command(
            installed_wheel, root, site="design_gate", detail="approval missing"
        ),
        cwd=root,
        installed_wheel=installed_wheel,
    )

    committed = json.loads(state_path.read_bytes())
    assert committed["recovery"]["operation"] is None
    assert committed["tasks"] == []
    assert committed["work"]["contract_card"] is None
    assert committed["work"]["extensions"] == {}
    assert root.joinpath(
        "docs/dev/project-management/prds/hold/00004-workflow-core-v1.md"
    ).is_file()
