from __future__ import annotations

import json
import os
import socket
import subprocess
from pathlib import Path

import pytest
from packaging_support import (
    InstalledWheel,
    _installed_workflow_root,
    _run,
    _run_unchecked,
)

PRD = "00004-workflow-core-v1.md"


@pytest.mark.parametrize("surface", ("metrics", "report"))
@pytest.mark.parametrize("kind", ("fifo", "directory", "socket"))
def test_installed_metrics_input_refuses_nonregular_files_promptly(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    surface: str,
    kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    runtime = root / "docs/dev/project-management/ovcaq"
    state = runtime / "state.json"
    before = state.read_bytes()
    backup = state.with_suffix(".json.bak").read_bytes()
    ledger = runtime / "metrics.jsonl"
    with socket.socket(socket.AF_UNIX) as listener:
        if kind == "fifo":
            os.mkfifo(ledger)
        elif kind == "directory":
            ledger.mkdir()
        else:
            # Keep the Unix socket name within the platform's pathname limit.
            monkeypatch.chdir(runtime)
            listener.bind(ledger.name)
        inode = ledger.stat().st_ino
        result = subprocess.run(
            [
                installed_wheel.console_script,
                "--root",
                root,
                "--json",
                "workflow",
                "render",
                surface,
            ],
            cwd=root,
            env=installed_wheel.environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    assert result.returncode == 1
    assert json.loads(result.stderr)["error"]["code"] == "usage"
    assert "metrics ledger" in json.loads(result.stderr)["error"]["message"]
    assert ledger.stat().st_ino == inode
    assert state.read_bytes() == before
    assert state.with_suffix(".json.bak").read_bytes() == backup
    assert not (runtime / "reports").exists()


@pytest.mark.parametrize("json_output", (True, False))
def test_installed_park_halt_and_exact_replay(
    installed_wheel: InstalledWheel, tmp_path: Path, json_output: bool
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    prefix = [installed_wheel.console_script, "--root", root]
    command = [*prefix, *(["--json"] if json_output else []), "workflow", "park"]
    _run(command, cwd=root, installed_wheel=installed_wheel)
    second = "00005-second.md"
    (root / "docs/dev/project-management/prds/wip" / second).write_text("# Next\n")
    _run(
        [*prefix, "state", "set", "--unsafe", "work.prd", json.dumps(second)],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    result = _run_unchecked(command, cwd=root, installed_wheel=installed_wheel)
    assert result.returncode == 4
    if json_output:
        value = json.loads(result.stdout)
        assert value["ok"] is False
        assert value["status"] == "systemic_park"
        assert value["result"]["systemic_halt"] is True
    else:
        assert "batch halted" in result.stderr
        assert "Inspect" in result.stderr
    state = root / "docs/dev/project-management/ovcaq/state.json"
    before = state.read_bytes()
    replay = _run_unchecked(command, cwd=root, installed_wheel=installed_wheel)
    assert replay.returncode == 4
    assert state.read_bytes() == before
    assert json.loads(before)["batch"]["parks_consecutive"] == 2


def test_installed_workflow_uses_project_paths_and_active_tiers(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    (root / "docs/dev/project-management/prds").rename(root / "custom-prds")
    (root / "docs/dev/project-management/ovcaq").rename(root / "custom-runtime")
    (root / "ovcaq.toml").write_text(
        'agent = "local"\n[workflow]\nprd_root = "custom-prds"\nruntime_root = "custom-runtime"\n'
        '[agents.local.tiers]\ndeep = "opaque-model"\n[agents.other.tiers]\nmissing = "another-model"\n'
    )
    active = root / "custom-prds/wip" / PRD
    active.write_text("---\ndefault_model: deep\n---\n# PRD\n")
    nested = root / "nested"
    nested.mkdir()
    prefix = [installed_wheel.console_script, "--json", "workflow"]
    selected = _run([*prefix, "select"], cwd=nested, installed_wheel=installed_wheel)
    assert json.loads(selected.stdout) == {"prd": PRD, "source": "wip"}
    _run([*prefix, "resume-target"], cwd=nested, installed_wheel=installed_wheel)
    applied = _run(
        [*prefix, "frontmatter", "--prd", active],
        cwd=nested,
        installed_wheel=installed_wheel,
    )
    assert json.loads(applied.stdout)["result"]["fields"]["tier"] == "deep"
    state = root / "custom-runtime/state.json"
    assert (
        json.loads(state.read_bytes())["work"]["extensions"]["workflow/tier-floor"]
        == "deep"
    )
    active.write_text("---\ndefault_model: missing\n---\n")
    missing = _run(
        [*prefix, "frontmatter", "--prd", active],
        cwd=nested,
        installed_wheel=installed_wheel,
    )
    assert "unavailable" in missing.stderr
    assert (
        "workflow/tier-floor"
        not in json.loads(state.read_bytes())["work"]["extensions"]
    )
    _run([*prefix, "park"], cwd=nested, installed_wheel=installed_wheel)
    assert (root / "custom-prds/hold" / PRD).exists()
    assert (root / "custom-runtime/deferred/installed-batch-deferred.json").exists()
    _run([*prefix, "render", "report"], cwd=nested, installed_wheel=installed_wheel)
    assert (root / "custom-runtime/reports/installed-batch-report.md").exists()
    assert not (root / "docs/dev/project-management/ovcaq").exists()


def _workflow_config_environment(
    installed_wheel: InstalledWheel, tmp_path: Path, root: Path, source: str
) -> dict[str, str]:
    selected = (
        '[workflow]\nprd_root = "selected-prds"\nruntime_root = "selected-runtime"\n'
    )
    absent = '[workflow]\nprd_root = "absent-prds"\nruntime_root = "absent-runtime"\n'
    user_config = tmp_path / "user-config/ovcaq/config.toml"
    user_config.parent.mkdir(parents=True)
    user_config.write_text(selected if source == "user" else absent)
    (root / "ovcaq.toml").write_text(
        selected if source == "project" else (absent if source == "flags" else "")
    )
    environment = {
        **installed_wheel.environment,
        "XDG_CONFIG_HOME": str(user_config.parents[1]),
    }
    return environment


@pytest.mark.parametrize("source", ("user", "project", "flags"))
@pytest.mark.parametrize("command", ("stall", "park"))
def test_installed_workflow_path_precedence_and_state_override(
    installed_wheel: InstalledWheel, tmp_path: Path, source: str, command: str
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    (root / "docs/dev/project-management/prds").rename(root / "selected-prds")
    (root / "docs/dev/project-management/ovcaq").rename(root / "selected-runtime")
    environment = _workflow_config_environment(installed_wheel, tmp_path, root, source)
    options = (
        ["--prd", PRD, "--site", "gate", "--detail", "later"]
        if command == "stall"
        else []
    )
    state = root / "selected-runtime/state.json"
    if source == "flags":
        state.rename(root / "selected-state.json")
        state = root / "selected-state.json"
        options += [
            "--prd-root",
            "selected-prds",
            "--runtime-root",
            "selected-runtime",
            "--state",
            "selected-state.json",
        ]
    nested = root / "nested"
    nested.mkdir()
    result = subprocess.run(
        [installed_wheel.console_script, "--json", "workflow", command, *options],
        cwd=nested,
        env=environment,
        capture_output=True,
        text=True,
        timeout=3,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(state.read_bytes())["recovery"]["operation"] is None
    assert (root / "selected-prds/hold" / PRD).is_file()
    assert (root / "selected-runtime/deferred/installed-batch-deferred.json").is_file()
    assert not (root / "absent-prds").exists()
    assert not (root / "absent-runtime").exists()


def test_installed_explicit_available_tiers_override_the_active_map(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    (root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local.tiers]\nfast = "opaque"\n'
    )
    prd = root / "docs/dev/project-management/prds/wip" / PRD
    prd.write_text("---\ndefault_model: bespoke\n---\n")
    command = [
        installed_wheel.console_script,
        "--root",
        root,
        "--json",
        "workflow",
        "frontmatter",
        "--prd",
        prd,
    ]
    applied = _run(
        [*command, "--available-tier", "fast", "--available-tier", "bespoke"],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    assert json.loads(applied.stdout)["result"]["fields"]["tier"] == "bespoke"
    missing = _run(command, cwd=root, installed_wheel=installed_wheel)
    assert "unavailable" in missing.stderr
    assert "tier" not in json.loads(missing.stdout)["result"]["fields"]
