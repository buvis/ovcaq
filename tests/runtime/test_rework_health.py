from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ovcaq.cli import main


def _configured_agent(
    root: Path, monkeypatch: pytest.MonkeyPatch, version: str, authenticated: bool
) -> Path:
    for variable, directory in (
        ("HOME", "home"),
        ("XDG_STATE_HOME", "xdg-state"),
        ("XDG_CONFIG_HOME", "xdg-config"),
    ):
        monkeypatch.setenv(variable, str(root / directory))
    marker = root / "agent-executed"
    script = root / "fake_agent.py"
    script.write_text(
        "import json, pathlib, sys\n"
        "args = sys.argv[1:]\n"
        f"with pathlib.Path({str(root / 'agent-calls')!r}).open('a') as calls:\n"
        "    calls.write(json.dumps(args) + '\\n')\n"
        f"version = {version!r}\n"
        "if args == ['--version']:\n"
        "    print('codex-cli ' + version)\n"
        "    raise SystemExit(0)\n"
        "if args == ['login', 'status']:\n"
        f"    print({'Logged in' if authenticated else 'Not logged in'!r})\n"
        f"    raise SystemExit({0 if authenticated else 1})\n"
        f"pathlib.Path({str(marker)!r}).write_text('executed')\n"
        "print(json.dumps({'type': 'error', 'message': 'fixture stopped'}))\n"
        "raise SystemExit(1)\n"
    )
    (root / "ovcaq.toml").write_text(
        'agent = "codex"\n[agents.codex]\n'
        f"command = {json.dumps([sys.executable, str(script)])}\n"
        'tiers = { standard = "model-s", deep = "model-o" }\n'
        "[supervisor]\ndied_retries = 0\n"
        "[phases.build]\ntimeout_seconds = 3\n"
    )
    return marker


def _initialize(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--root", str(root), "--json", "init"]) == 0
    capsys.readouterr()
    backlog = root / "docs/dev/project-management/prds/backlog"
    backlog.mkdir(parents=True, exist_ok=True)
    (backlog / "00001-test.md").write_text("# Fixture PRD\n")


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ovcaq",
            "--root",
            str(root),
            "--json",
            "run",
            "--no-tui",
            "--agent",
            "codex",
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


@pytest.mark.parametrize(
    ("version", "authenticated", "expected_terms"),
    [
        ("0.161.0", True, ("0.160.0", "0.161.0")),
        ("0.160.0", False, ("login",)),
    ],
)
def test_run_rejects_unhealthy_adapter_before_agent_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    version: str,
    authenticated: bool,
    expected_terms: tuple[str, ...],
) -> None:
    marker = _configured_agent(tmp_path, monkeypatch, version, authenticated)
    _initialize(tmp_path, capsys)

    result = _run(tmp_path)

    assert result.returncode != 0
    assert not marker.exists()
    assert "Traceback" not in result.stderr
    assert result.stdout == ""
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    message = payload["error"]["message"].lower()
    assert all(term in message for term in expected_terms)


def test_run_executes_adapter_after_healthy_version_and_auth_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    marker = _configured_agent(tmp_path, monkeypatch, "0.160.0", True)
    _initialize(tmp_path, capsys)

    result = _run(tmp_path)

    assert marker.read_text() == "executed"
    calls = [
        json.loads(line) for line in (tmp_path / "agent-calls").read_text().splitlines()
    ]
    assert calls[:2] == [["--version"], ["login", "status"]]
    assert len(calls) >= 3
    assert "Traceback" not in result.stderr
