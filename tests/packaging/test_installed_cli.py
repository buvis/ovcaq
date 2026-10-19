from __future__ import annotations

import json
from pathlib import Path

import pytest
from packaging_support import (
    DECLARED_MODULES,
    PROJECT_ROOT,
    BuiltArtifacts,
    InstalledWheel,
    _hostile_cwd,
    _installed_workflow_root,
    _run,
    _run_unchecked,
    command_text,
)


@pytest.mark.parametrize(
    "arguments",
    (
        ["phase-complete", "--outcome", "tasks_done"],
        ["phase-complete", "--outcome", "rework"],
        ["phase-complete", "--outcome", "converged"],
        ["phase-complete", "--outcome", "more_prds"],
        ["phase-complete", "--outcome", "drained"],
        ["park"],
        [
            "stall",
            "--prd",
            "00004-workflow-core-v1.md",
            "--site",
            "gate",
            "--detail",
            "late",
        ],
    ),
    ids=("tasks-done", "rework", "converged", "more-prds", "drained", "park", "stall"),
)
def test_installed_drained_workflow_stays_terminal(
    installed_wheel: InstalledWheel, tmp_path: Path, arguments: list[str]
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    prefix = [installed_wheel.console_script, "--root", root, "--json", "workflow"]
    _run(
        [*prefix, "phase-complete", "--outcome", "drained"],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    state = root / "docs/dev/project-management/ovcaq/state.json"
    before = state.read_bytes()

    result = _run_unchecked(
        [*prefix, *arguments], cwd=root, installed_wheel=installed_wheel
    )

    assert result.returncode == 1
    assert "drained" in json.loads(result.stderr)["error"]["message"]
    assert state.read_bytes() == before
    assert root.joinpath(
        "docs/dev/project-management/prds/wip/00004-workflow-core-v1.md"
    ).is_file()
    assert not root.joinpath("docs/dev/project-management/prds/hold").exists()
    assert not root.joinpath("docs/dev/project-management/ovcaq/deferred").exists()


def test_installed_entry_points_print_help_from_hostile_cwd(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    cwd = _hostile_cwd(tmp_path)
    commands = (
        [installed_wheel.console_script, "--help"],
        [installed_wheel.python, "-m", "ovcaq", "--help"],
    )
    for command in commands:
        result = _run(command, cwd=cwd, installed_wheel=installed_wheel)
        output = result.stdout + result.stderr
        assert "usage:" in output.lower(), (
            f"installed help missing usage: {command_text(command)}\n{output}"
        )
        assert "ovcaq" in output.lower(), (
            f"installed help missing product name: {command_text(command)}\n{output}"
        )
        assert str(PROJECT_ROOT) not in output, (
            f"installed help exposed checkout path: {command_text(command)}\n{output}"
        )


_RUNTIME_SESSION_SCRIPT = """
import os
import sys
from pathlib import Path
from ovcaq.paths import ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.registry import process_identity
from ovcaq.runtime.session import SessionMetadata, create_session
root = Path(sys.argv[1])
paths = resolve_runtime_paths(root)
ensure_runtime_layout(paths)
identity = process_identity(os.getpid())
metadata = SessionMetadata(
    schema_version=1, run_id="installed-run", session_id="installed-session",
    agent="command", pid=os.getpid(), process_start=identity.started,
    started_at="2026-01-01T00:00:00Z",
)
session = create_session(paths, metadata)
session.raw.write_bytes(b"installed retained output\\n")
session.normalized.write_bytes(b'{}\\n')
print(session.raw)
"""


def _seed_installed_runtime(
    installed_wheel: InstalledWheel,
    root: Path,
    cwd: Path,
) -> str:
    prefix = [installed_wheel.console_script, "--root", root, "--json"]
    _run([*prefix, "init"], cwd=cwd, installed_wheel=installed_wheel)
    seeded = _run(
        [installed_wheel.python, "-I", "-c", _RUNTIME_SESSION_SCRIPT, root],
        cwd=cwd,
        installed_wheel=installed_wheel,
    )
    return seeded.stdout.strip()


def test_installed_runtime_commands_work_outside_checkout(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    cwd = _hostile_cwd(tmp_path)
    root = tmp_path / "runtime-project"
    root.mkdir()
    prefix = [installed_wheel.console_script, "--root", root, "--json"]
    evidence_path = _seed_installed_runtime(installed_wheel, root, cwd)
    status = _run([*prefix, "status"], cwd=cwd, installed_wheel=installed_wheel)
    status_data = json.loads(status.stdout)
    assert set(status_data) == {
        "schema_version",
        "state",
        "run",
        "evidence",
        "purge_preview",
        "attention",
    }
    assert status_data["state"] == "available"
    assert status_data["run"] == "idle"
    assert status_data["evidence"]["total_bytes"] >= len(b"installed retained output\n")
    preview = status_data["purge_preview"]
    assert preview["applied"] is False
    assert preview["selected"] == [str(Path(evidence_path).parent)]
    assert preview["total_bytes"] == status_data["evidence"]["total_bytes"]
    assert status.stderr == ""
    doctor = _run([*prefix, "doctor"], cwd=cwd, installed_wheel=installed_wheel)
    assert set(json.loads(doctor.stdout)) == {
        "schema_version",
        "ok",
        "paths",
        "capabilities",
        "checks",
        "purge_preview",
        "attention",
        "acknowledged_emergency_archive",
    }
    assert doctor.stderr == ""
    assert json.loads(doctor.stdout)["acknowledged_emergency_archive"] is None
    logs_command = [*prefix, "logs", "--session", "installed-session"]
    logs = _run(logs_command, cwd=cwd, installed_wheel=installed_wheel)
    assert json.loads(logs.stdout) == {
        "schema_version": 1,
        "session_id": "installed-session",
        "kind": "raw",
        "path": evidence_path,
        "size_bytes": len(b"installed retained output\n"),
        "active": False,
    }
    assert logs.stderr == ""


def test_installed_workflow_help_exposes_the_complete_command_family(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    cwd = _hostile_cwd(tmp_path)
    result = _run(
        [installed_wheel.console_script, "workflow", "--help"],
        cwd=cwd,
        installed_wheel=installed_wheel,
    )

    for command in (
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
    ):
        assert command in result.stdout


def test_installed_frontmatter_binds_active_prd_and_tracks_explicit_cap_three(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    prds = root / "docs/dev/project-management/prds/wip"
    wrong = prds / "00005-runtime-v1.md"
    wrong.write_text("---\nrework_cap: 5\n---\n", encoding="utf-8")
    state = root / "docs/dev/project-management/ovcaq/state.json"
    before = state.read_bytes()
    prefix = [installed_wheel.console_script, "--root", root, "workflow", "frontmatter"]

    rejected = _run_unchecked(
        [*prefix, "--prd", wrong, "--expected-revision", "1"],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    assert rejected.returncode == 1
    assert "does not match active PRD" in rejected.stderr
    assert state.read_bytes() == before

    active = prds / "00004-workflow-core-v1.md"
    active.write_text("---\nrework_cap: 3\n---\n", encoding="utf-8")
    _run(
        [*prefix, "--prd", active, "--expected-revision", "1"],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    active.write_text("---\nrework_cap: 2\n---\n", encoding="utf-8")
    changed = _run(
        [*prefix, "--prd", active, "--expected-revision", "2"],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    assert "reset rework_cap 3 -> 2" in changed.stderr


def test_installed_version_and_every_declared_module_come_from_wheel(
    built_artifacts: BuiltArtifacts,
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    cwd = _hostile_cwd(tmp_path)
    script = """
import importlib
import json
import sys
from importlib import metadata

names = json.loads(sys.argv[1])
modules = {name: importlib.import_module(name).__file__ for name in names}
ovcaq = importlib.import_module("ovcaq")
print("OVCAQ_INSTALL_AUDIT=" + json.dumps({
    "metadata_version": metadata.version("ovcaq"),
    "package_version": ovcaq.__version__,
    "modules": modules,
    "sys_path": sys.path,
}))
"""
    command = [
        installed_wheel.python,
        "-c",
        script,
        json.dumps(DECLARED_MODULES),
    ]
    result = _run(command, cwd=cwd, installed_wheel=installed_wheel)
    audit_lines = [
        line.removeprefix("OVCAQ_INSTALL_AUDIT=")
        for line in result.stdout.splitlines()
        if line.startswith("OVCAQ_INSTALL_AUDIT=")
    ]
    assert len(audit_lines) == 1, (
        f"installed import audit produced unexpected output: {command_text(command)}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    audit = json.loads(audit_lines[0])
    assert audit["metadata_version"] == built_artifacts.version, (
        f"installed metadata version {audit['metadata_version']!r} != wheel "
        f"version {built_artifacts.version!r}"
    )
    assert audit["package_version"] == built_artifacts.version, (
        f"installed package version {audit['package_version']!r} != wheel "
        f"version {built_artifacts.version!r}"
    )

    missing = sorted(set(DECLARED_MODULES) - set(audit["modules"]))
    assert not missing, f"installed wheel did not import declared modules: {missing!r}"
    outside_venv = {
        name: module_path
        for name, module_path in audit["modules"].items()
        if not Path(module_path)
        .resolve()
        .is_relative_to(installed_wheel.root.resolve())
    }
    assert not outside_venv, (
        f"imports did not come from installed wheel: {outside_venv!r}"
    )
    checkout_entries = [
        entry for entry in audit["sys_path"] if str(PROJECT_ROOT) in entry
    ]
    assert not checkout_entries, (
        f"installed interpreter inherited checkout paths: {checkout_entries!r}"
    )
