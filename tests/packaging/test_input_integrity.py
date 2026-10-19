from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from packaging_support import InstalledWheel, _installed_workflow_root, _run_unchecked

PRD = "00004-workflow-core-v1.md"


@pytest.mark.parametrize("action", ("defer", "report"))
@pytest.mark.parametrize("malformation", ("duplicate", "deep"))
def test_installed_commands_reject_corrupt_ledger_without_mutation(
    installed_wheel: InstalledWheel, tmp_path: Path, action: str, malformation: str
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    runtime = root / "docs/dev/project-management/ovcaq"
    ledger = runtime / "deferred/installed-batch-deferred.json"
    ledger.parent.mkdir()
    payload = (
        '{"batch_id":"installed-batch","items":[{"op_id":"keep-me"}],"items":[]}'
        if malformation == "duplicate"
        else '{"batch_id":"installed-batch","items":[{"data":'
        + "[" * 10000
        + "0"
        + "]" * 10000
        + "}]}"
    )
    ledger.write_text(payload)
    record = root / "record.json"
    record.write_text('{"op_id":"new"}')
    args = (
        ["defer", "--prd", PRD, "--record", record]
        if action == "defer"
        else ["render", "report"]
    )
    before = (runtime / "state.json").read_bytes()
    result = _run_unchecked(
        [installed_wheel.console_script, "--root", root, "--json", "workflow", *args],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    assert result.returncode == (1 if malformation == "duplicate" else 11)
    assert result.stdout == ""
    error = json.loads(result.stderr)["error"]
    assert error["code"] == (
        "usage" if malformation == "duplicate" else "resource_limit"
    )
    assert "deferred" in error["message"]
    assert ledger.read_text() == payload
    assert (runtime / "state.json").read_bytes() == before
    assert not (runtime / "reports").exists()


@pytest.mark.parametrize(
    "action", ("frontmatter", "defer", "project-config", "user-config")
)
def test_installed_named_fifo_input_refuses_without_waiting_for_writer(
    installed_wheel: InstalledWheel, tmp_path: Path, action: str
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    fifo = root / "input"
    if action == "project-config":
        fifo = root / "ovcaq.toml"
        fifo.unlink()
    elif action == "user-config":
        fifo = (
            Path(installed_wheel.environment["XDG_CONFIG_HOME"]) / "ovcaq/config.toml"
        )
        fifo.parent.mkdir(parents=True, exist_ok=True)
    os.mkfifo(fifo)
    args = {
        "frontmatter": ["frontmatter", "--prd", fifo],
        "defer": ["defer", "--prd", PRD, "--record", fifo],
        "project-config": ["select"],
        "user-config": ["select"],
    }[action]
    state = root / "docs/dev/project-management/ovcaq/state.json"
    before = state.read_bytes()
    try:
        result = subprocess.run(
            [
                str(part)
                for part in [
                    installed_wheel.console_script,
                    "--root",
                    root,
                    "--json",
                    "workflow",
                    *args,
                ]
            ],
            cwd=root,
            env=installed_wheel.environment,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    finally:
        fifo.unlink()
    assert result.returncode == 1
    assert result.stdout == ""
    assert json.loads(result.stderr)["error"]["code"] == "usage"
    assert "regular file" in json.loads(result.stderr)["error"]["message"]
    assert state.read_bytes() == before


@pytest.mark.parametrize("scope", ("project", "user"))
@pytest.mark.parametrize("key", ("prd_root", "ignored"))
def test_installed_deep_toml_refuses_contextually_without_mutation(
    installed_wheel: InstalledWheel, tmp_path: Path, scope: str, key: str
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    config = root / "ovcaq.toml"
    if scope == "user":
        config = (
            Path(installed_wheel.environment["XDG_CONFIG_HOME"]) / "ovcaq/config.toml"
        )
    config.parent.mkdir(parents=True, exist_ok=True)
    original = config.read_bytes() if config.exists() else None
    payload = f"[workflow]\n{key} = " + "[" * 2000 + '"prds"' + "]" * 2000 + "\n"
    config.write_text(payload)
    state = root / "docs/dev/project-management/ovcaq/state.json"
    before = state.read_bytes()
    try:
        result = _run_unchecked(
            [
                installed_wheel.console_script,
                "--root",
                root,
                "--json",
                "workflow",
                "select",
            ],
            cwd=root,
            installed_wheel=installed_wheel,
        )
        assert result.returncode == 1
        assert result.stdout == ""
        assert "Traceback" not in result.stderr
        error = json.loads(result.stderr)["error"]
        assert error["code"] == "usage"
        assert (
            f"configuration nesting exceeds safe decode limit: {config}"
            in error["message"]
        )
        assert config.read_text() == payload
        assert state.read_bytes() == before
    finally:
        if original is None:
            config.unlink()
        else:
            config.write_bytes(original)
