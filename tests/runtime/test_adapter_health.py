from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from ovcaq.cli import main
from ovcaq.config import AgentSettings, supervisor_settings
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.drivers.codex import CodexDriver
from ovcaq.paths import state_path
from ovcaq.runtime.registry import FleetRegistry
from ovcaq.state.schema import State
from ovcaq.state.store import StateStore


@pytest.fixture(autouse=True)
def isolated_homes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in ("HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME"):
        home = tmp_path / variable.lower()
        home.mkdir()
        monkeypatch.setenv(variable, str(home))


def fake_executable(
    directory: Path,
    log: Path,
    marker: Path,
) -> Path:
    directory.mkdir()
    executable = directory / "fixture-agent-health"
    executable.write_text(
        f"#!{sys.executable}\n"
        "import json\nimport sys\nfrom pathlib import Path\n"
        "arguments = sys.argv[1:]\n"
        f"with Path({str(log)!r}).open('a', encoding='utf-8') as stream:\n"
        "    stream.write(json.dumps(arguments) + '\\n')\n"
        "if arguments == ['--version']:\n"
        "    print('codex-cli 0.160.0')\n"
        "elif arguments == ['login', 'status']:\n"
        "    print('Logged in with fixture authentication')\n"
        "else:\n"
        f"    Path({str(marker)!r}).touch()\n"
        "    raise SystemExit(77)\n",
        encoding="utf-8",
    )
    executable.chmod(0o700)
    return executable


def driver_for(
    provider: str, command: str, environment: dict[str, str]
) -> ClaudeDriver | CodexDriver:
    options: dict[str, object] = (
        {"permission_mode": "auto"} if provider == "claude" else {}
    )
    settings = AgentSettings(
        provider,
        (command,),
        {"standard": "fixture-model", "deep": "fixture-model"},
        environment,
        options,
    )
    if provider == "claude":
        return ClaudeDriver(settings, run_id="health-fixture")
    return CodexDriver(settings, run_id="health-fixture")


def assert_probe_evidence(
    provider: str, log: Path, marker: Path, healthy: bool
) -> None:
    records = (
        [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        if log.exists()
        else []
    )
    expected = (
        [["--version"], ["login", "status"]] if provider == "codex" and healthy else []
    )
    assert records == expected
    assert not marker.exists()


@pytest.mark.parametrize("provider", ("claude", "codex"))
def test_probe_finds_executable_available_only_on_overlay_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
) -> None:
    log, marker = tmp_path / "probe.jsonl", tmp_path / "phase-exec"
    executable = fake_executable(tmp_path / "overlay", log, marker)
    host = tmp_path / "host"
    host.mkdir()
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(host))

    health = driver_for(
        provider,
        executable.name,
        {"PATH": os.pathsep.join((str(empty), str(executable.parent)))},
    ).probe()

    assert health.healthy is True
    assert health.detail.strip()
    assert_probe_evidence(provider, log, marker, healthy=True)


@pytest.mark.parametrize("provider", ("claude", "codex"))
@pytest.mark.parametrize("command_kind", ("missing-file", "directory"))
def test_probe_rejects_absolute_command_that_is_not_an_executable_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    command_kind: str,
) -> None:
    log, marker = tmp_path / "probe.jsonl", tmp_path / "phase-exec"
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    command = tmp_path / command_kind
    if command_kind == "directory":
        command.mkdir()
    monkeypatch.setenv("PATH", str(overlay))

    health = driver_for(provider, str(command), {"PATH": str(overlay)}).probe()

    assert health.healthy is False
    assert health.detail.strip()
    assert_probe_evidence(provider, log, marker, healthy=False)


@pytest.mark.parametrize("provider", ("claude", "codex"))
@pytest.mark.parametrize("command_kind", ("name", "absolute"))
def test_probe_rejects_file_without_execute_permission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    command_kind: str,
) -> None:
    log, marker = tmp_path / "probe.jsonl", tmp_path / "phase-exec"
    executable = fake_executable(tmp_path / "overlay", log, marker)
    executable.chmod(0o600)
    host = tmp_path / "host"
    host.mkdir()
    monkeypatch.setenv("PATH", str(host))
    command = executable.name if command_kind == "name" else str(executable)

    health = driver_for(provider, command, {"PATH": str(executable.parent)}).probe()

    assert health.healthy is False
    assert health.detail.strip()
    assert_probe_evidence(provider, log, marker, healthy=False)


@pytest.mark.parametrize("provider", ("claude", "codex"))
def test_probe_finds_executable_symlink_on_overlay_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, provider: str
) -> None:
    log, marker = tmp_path / "probe.jsonl", tmp_path / "phase-exec"
    executable = fake_executable(tmp_path / "target", log, marker)
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    link = overlay / executable.name
    link.symlink_to(executable)
    host = tmp_path / "host"
    host.mkdir()
    monkeypatch.setenv("PATH", str(host))

    health = driver_for(provider, link.name, {"PATH": str(overlay)}).probe()

    assert health.healthy is True
    assert health.detail.strip()
    assert_probe_evidence(provider, log, marker, healthy=True)


@pytest.mark.parametrize("provider", ("claude", "codex"))
def test_probe_finds_executable_on_inherited_host_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, provider: str
) -> None:
    log, marker = tmp_path / "probe.jsonl", tmp_path / "phase-exec"
    executable = fake_executable(tmp_path / "host", log, marker)
    monkeypatch.setenv("PATH", str(executable.parent))

    health = driver_for(provider, executable.name, {}).probe()

    assert health.healthy is True
    assert health.detail.strip()
    assert_probe_evidence(provider, log, marker, healthy=True)


@pytest.mark.parametrize("provider", ("claude", "codex"))
def test_probe_rejects_host_executable_hidden_by_overlay_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, provider: str
) -> None:
    log, marker = tmp_path / "probe.jsonl", tmp_path / "phase-exec"
    executable = fake_executable(tmp_path / "host", log, marker)
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    monkeypatch.setenv("PATH", str(executable.parent))

    health = driver_for(provider, executable.name, {"PATH": str(overlay)}).probe()

    assert health.healthy is False
    assert health.detail.strip()
    assert_probe_evidence(provider, log, marker, healthy=False)


@pytest.mark.parametrize("provider", ("claude", "codex"))
def test_probe_preserves_absolute_executable_with_unrelated_overlay_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, provider: str
) -> None:
    log, marker = tmp_path / "probe.jsonl", tmp_path / "phase-exec"
    executable = fake_executable(tmp_path / "bin", log, marker)
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    monkeypatch.setenv("PATH", str(unrelated))

    health = driver_for(provider, str(executable), {"PATH": str(unrelated)}).probe()

    assert health.healthy is True
    assert health.detail.strip()
    assert_probe_evidence(provider, log, marker, healthy=True)


@pytest.mark.parametrize("provider", ("claude", "codex"))
def test_probe_uses_default_search_path_when_host_path_is_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
) -> None:
    log, marker = tmp_path / "probe.jsonl", tmp_path / "phase-exec"
    executable = fake_executable(tmp_path / "default-bin", log, marker)
    monkeypatch.setattr(os, "defpath", str(executable.parent))
    monkeypatch.delenv("PATH", raising=False)
    assert shutil.which(executable.name) is None

    health = driver_for(provider, executable.name, {}).probe()

    assert health.healthy is True
    assert health.detail.strip()
    assert_probe_evidence(provider, log, marker, healthy=True)


@pytest.mark.parametrize("command_kind", ("fixture", "default-path"))
def test_claude_probe_keeps_empty_host_path_unhealthy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command_kind: str
) -> None:
    log, marker = tmp_path / "probe.jsonl", tmp_path / "phase-exec"
    executable = fake_executable(tmp_path / "bin", log, marker)
    monkeypatch.chdir(executable.parent)
    monkeypatch.setenv("PATH", "")
    command = executable.name if command_kind == "fixture" else "sh"
    if command_kind == "default-path":
        assert shutil.which(command, path=os.defpath) is not None

    health = driver_for("claude", command, {}).probe()

    assert health.healthy is False
    assert health.detail.strip()
    assert_probe_evidence("claude", log, marker, healthy=False)


def initialize_running_project(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root.mkdir()
    assert main(["--root", str(root), "--json", "init"]) == 0
    capsys.readouterr()

    def start(state: State) -> None:
        state["batch"]["id"] = "batch-cli"
        state["batch"]["status"] = "running"
        state["batch"]["started_at"] = "2026-08-30T12:00:00Z"
        state["work"]["prd"] = "00004-workflow-core-v1.md"

    StateStore(state_path(root)).transaction(start)


def configure_project(root: Path, provider: str, command: str, overlay: Path) -> None:
    options = (
        '[agents.claude.options]\npermission_mode = "auto"\n'
        if provider == "claude"
        else ""
    )
    (root / "ovcaq.toml").write_text(
        f"agent = {json.dumps(provider)}\n[agents.{provider}]\n"
        f"command = {json.dumps([command])}\n"
        'tiers = { standard = "fixture-model", deep = "fixture-model" }\n'
        f"environment = {{ PATH = {json.dumps(str(overlay))} }}\n"
        f"{options}[workflow]\nruntime_root = 'runtime'\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("provider", ("claude", "codex"))
def test_unhealthy_overlay_blocks_supervised_phase_exec_and_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    provider: str,
) -> None:
    log, marker = tmp_path / "probe.jsonl", tmp_path / "phase-exec"
    executable = fake_executable(tmp_path / "host", log, marker)
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    root = tmp_path / "project"
    initialize_running_project(root, capsys)
    configure_project(root, provider, executable.name, overlay)
    monkeypatch.setenv("PATH", str(executable.parent))
    paths = supervisor_settings(root).runtime.paths

    code = main(["--root", str(root), "--json", "run", "--no-tui"])
    captured = capsys.readouterr()

    assert code != 0
    assert captured.out == ""
    error = json.loads(captured.err)
    assert error["ok"] is False
    assert "agent is unhealthy" in error["error"]["message"]
    assert_probe_evidence(provider, log, marker, healthy=False)
    assert tuple(paths.sessions.glob("*")) == ()
    assert not FleetRegistry(paths.fleet_root).snapshot().live
