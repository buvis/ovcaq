"""Installed and in-process workflow CLI contract tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from ovcaq.cli import (
    build_parser,
    main,
    render_command_reference,
    render_state_protocol_command_inventory,
)
from ovcaq.paths import state_path
from ovcaq.state.schema import State
from ovcaq.state.store import StateStore


def _invoke(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str]:
    exit_code = main(argv)
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def _workflow(
    root: Path,
    capsys: pytest.CaptureFixture[str],
    *args: str,
    json_output: bool = True,
    revision: int | None = None,
) -> tuple[int, str, str]:
    prefix = ["--root", str(root)]
    if json_output:
        prefix.append("--json")
    suffix = [] if revision is None else ["--expected-revision", str(revision)]
    return _invoke([*prefix, "workflow", *args, *suffix], capsys)


def _workflow_choices() -> tuple[str, ...]:
    parser = build_parser()
    top = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    workflow = top.choices["workflow"]
    commands = next(
        action
        for action in workflow._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    return tuple(commands.choices)


def _initialize_running_root(
    root: Path,
    capsys: pytest.CaptureFixture[str],
) -> StateStore:
    root.mkdir()
    result = _invoke(["--root", str(root), "--json", "init"], capsys)
    assert result[0] == 0
    store = StateStore(state_path(root))

    def start(state: State) -> None:
        state["batch"]["id"] = "batch-cli"
        state["batch"]["status"] = "running"
        state["batch"]["started_at"] = "2026-08-30T12:00:00Z"
        state["work"]["prd"] = "00004-workflow-core-v1.md"

    store.transaction(start)
    return store


def test_parser_registers_the_complete_workflow_family() -> None:
    assert _workflow_choices() == (
        "select",
        "frontmatter",
        "phase-complete",
        "resume-target",
        "check-plan",
        "stall",
        "park",
        "defer",
        "complete-prd",
        "render",
    )


def _enter_review(
    root: Path, store: StateStore, capsys: pytest.CaptureFixture[str]
) -> None:
    prd = root / "docs/dev/project-management/prds/wip/00004-workflow-core-v1.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("---\ncatchup: skip\nrework_cap: 4\n---\n", encoding="utf-8")
    frontmatter = _workflow(root, capsys, "frontmatter", "--prd", str(prd), revision=1)
    assert frontmatter[0] == 0
    assert json.loads(frontmatter[1])["revision"] == 2
    assert store.read()["review"]["cap"] == 4
    _assert_completion_refused(root, store, capsys, revision=2)
    phase = _workflow(
        root, capsys, "phase-complete", "--outcome", "tasks_done", revision=2
    )
    assert phase[0] == 0
    assert json.loads(phase[1]) == {
        "ok": True,
        "result": {"next_phase": "review", "phase": "review"},
        "revision": 3,
    }


def _assert_completion_refused(
    root: Path, store: StateStore, capsys: pytest.CaptureFixture[str], *, revision: int
) -> None:
    before = store.path.read_bytes()
    complete = _workflow(
        root,
        capsys,
        "complete-prd",
        "--prd",
        "00004-workflow-core-v1.md",
        revision=revision,
    )
    assert complete[0] == 1
    assert json.loads(complete[2])["error"]["code"] == "usage"
    assert store.path.read_bytes() == before


def test_workflow_public_application_commands_use_state_store_and_cas(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "public-boundaries"
    store = _initialize_running_root(root, capsys)
    _enter_review(root, store, capsys)
    conflict = _workflow(
        root, capsys, "phase-complete", "--outcome", "rework", revision=2
    )
    assert conflict[0] == 9
    assert json.loads(conflict[2])["error"]["code"] == "revision_conflict"
    _assert_completion_refused(root, store, capsys, revision=3)
    converged = _workflow(
        root, capsys, "phase-complete", "--outcome", "converged", revision=3
    )
    assert converged[0] == 0
    assert json.loads(converged[1])["revision"] == 4
    complete = _workflow(
        root, capsys, "complete-prd", "--prd", "00004-workflow-core-v1.md", revision=4
    )
    assert complete[0] == 0
    assert json.loads(complete[1])["revision"] == 5
    assert len(store.read()["batch"]["completed_prds"]) == 1


def test_frontmatter_command_rejects_wrong_prd_and_warns_after_explicit_cap_three(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "frontmatter-authority"
    store = _initialize_running_root(root, capsys)
    prd_dir = root / "docs/dev/project-management/prds/wip"
    prd_dir.mkdir(parents=True)
    wrong = prd_dir / "00005-runtime-v1.md"
    wrong.write_text("---\nrework_cap: 5\n---\n", encoding="utf-8")
    before = store.path.read_bytes()

    rejected = _workflow(root, capsys, "frontmatter", "--prd", str(wrong), revision=1)

    assert rejected[0] == 1
    assert "does not match active PRD" in rejected[2]
    assert store.path.read_bytes() == before

    active = prd_dir / "00004-workflow-core-v1.md"
    active.write_text("---\nrework_cap: 3\n---\n", encoding="utf-8")
    assert (
        _workflow(
            root,
            capsys,
            "frontmatter",
            "--prd",
            str(active),
            json_output=False,
            revision=1,
        )[0]
        == 0
    )
    active.write_text("---\nrework_cap: 2\n---\n", encoding="utf-8")
    changed = _workflow(
        root, capsys, "frontmatter", "--prd", str(active), json_output=False, revision=2
    )
    assert changed[0] == 0
    assert "reset rework_cap 3 -> 2" in changed[2]


def test_selection_resume_and_plan_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "public-reads"
    store = _initialize_running_root(root, capsys)
    prd = root / "docs/dev/project-management/prds/wip/00004-workflow-core-v1.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("# Workflow\n", encoding="utf-8")

    selected = _workflow(root, capsys, "select", json_output=False)
    assert selected == (
        0,
        '{"prd": "00004-workflow-core-v1.md", "source": "wip"}\n',
        "",
    )

    resume = _workflow(root, capsys, "resume-target", json_output=False)
    assert resume == (0, "build: catchup then planning\n", "")
    checked = _workflow(root, capsys, "check-plan")
    assert json.loads(checked[1]) == {"over_ceiling": False, "task_count": 0}
    oversized = _workflow(root, capsys, "check-plan", "--ceiling", "-1")
    assert oversized[0] == 3
    assert oversized[1] == ""
    oversized_error = json.loads(oversized[2])["error"]
    assert oversized_error["code"] == "oversized_plan"
    assert "0 tasks" in oversized_error["message"]
    assert "-1-task" in oversized_error["message"]

    assert store.read()["revision"] == 1


def _assert_defer_replay(
    root: Path, capsys: pytest.CaptureFixture[str], record: Path
) -> tuple[Path, bytes]:
    deferred = _workflow(
        root,
        capsys,
        "defer",
        "--prd",
        "00004-workflow-core-v1.md",
        "--record",
        str(record),
    )
    assert deferred[0] == 0
    deferred_payload = json.loads(deferred[1])
    assert deferred_payload["path"].endswith("batch-cli-deferred.json")
    deferred_path = Path(deferred_payload["path"])
    deferred_bytes = deferred_path.read_bytes()

    exact_replay = _workflow(
        root,
        capsys,
        "defer",
        "--prd",
        "00004-workflow-core-v1.md",
        "--record",
        str(record),
    )
    assert exact_replay[0] == 0
    assert deferred_path.read_bytes() == deferred_bytes

    return deferred_path, deferred_bytes


def test_defer_exact_and_conflicting_replay(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "public-reads"
    store = _initialize_running_root(root, capsys)
    prd = root / "docs/dev/project-management/prds/wip/00004-workflow-core-v1.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("# Workflow\n", encoding="utf-8")

    record = root / "record.json"
    record.write_text(
        json.dumps({"op_id": "cli-defer-1", "type": "decision", "detail": "later"}),
        encoding="utf-8",
    )
    deferred_path, deferred_bytes = _assert_defer_replay(root, capsys, record)

    record.write_text(
        json.dumps({"op_id": "cli-defer-1", "type": "decision", "detail": "different"}),
        encoding="utf-8",
    )
    conflicting_replay = _workflow(
        root,
        capsys,
        "defer",
        "--prd",
        "00004-workflow-core-v1.md",
        "--record",
        str(record),
    )
    assert conflicting_replay[0] == 1
    error = json.loads(conflicting_replay[2])["error"]
    assert error["code"] == "usage"
    assert "conflicting deferred record" in error["message"]
    assert deferred_path.read_bytes() == deferred_bytes

    assert store.read()["revision"] == 1


@pytest.mark.parametrize("surface", ("audit", "report", "metrics"))
def test_render_command_surfaces(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], surface: str
) -> None:
    root = tmp_path / "public-reads"
    store = _initialize_running_root(root, capsys)
    prd = root / "docs/dev/project-management/prds/wip/00004-workflow-core-v1.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("# Workflow\n", encoding="utf-8")

    rendered = _workflow(root, capsys, "render", surface)
    assert rendered[0] == 0
    payload = json.loads(rendered[1])
    assert payload["surface"] == surface
    assert payload["text"].startswith("# Workflow")
    assert store.read()["revision"] == 1


def test_render_report_command_archives_terminal_state_without_removing_live_state(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "terminal-report"
    store = _initialize_running_root(root, capsys)

    def drain(state: State) -> None:
        state["work"]["phase"] = "done"
        state["work"]["next_phase"] = ""

    store.transaction(drain)
    state_before = store.path.read_bytes()

    rendered = _workflow(root, capsys, "render", "report")

    assert rendered[0] == 0
    archive = (
        root / "docs/dev/project-management/ovcaq/reports/batch-cli-state-final.json"
    )
    assert json.loads(archive.read_bytes()) == store.read()
    assert store.path.read_bytes() == state_before


def test_stall_and_park_are_public_and_reconcile_without_marker_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "public-sagas"
    store = _initialize_running_root(root, capsys)
    prd = root / "docs/dev/project-management/prds/wip/00004-workflow-core-v1.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("# Workflow\n", encoding="utf-8")

    stalled = _workflow(
        root,
        capsys,
        "stall",
        "--prd",
        "00004-workflow-core-v1.md",
        "--site",
        "design_gate",
        "--detail",
        "approval missing",
    )
    assert stalled[0] == 0
    assert json.loads(stalled[1])["result"]["kind"] == "stall"
    assert store.read()["recovery"]["operation"] is None

    parked = _workflow(root, capsys, "park")
    assert parked[0] == 1
    assert "durable recovery proof" in parked[2]
    assert not (root / "docs/dev/project-management/ovcaq/park-requested").exists()


def test_workflow_docs_are_generated_from_the_live_parser() -> None:
    generated = render_command_reference(build_parser())
    documented = Path("docs/operations.md").read_text(encoding="utf-8")

    assert documented == generated
    for command in _workflow_choices():
        assert f"ovcaq [--root PATH] [--json] workflow {command}" in documented

    protocol = Path("docs/state-protocol.md").read_text(encoding="utf-8")
    assert "[parser-generated command reference](operations.md)" in protocol
    inventory = protocol.partition("## Command inventory")[2].partition(
        "## Command examples"
    )[0]
    generated = render_state_protocol_command_inventory(build_parser())
    assert generated in inventory
