"""Probe version evidence and failure diagnostics obey the public contract."""

import json
import re
import sys
from pathlib import Path

import pytest

from ovcaq.drivers.base import DriverHealth
from ovcaq.drivers.codex import CodexDriver
from ovcaq.drivers.edge import build_driver
from ovcaq.paths import CONFIG_NAME

SECRET = "sk-" + "proj-fixturecredential12345678901234567890"
PREFIX = "literal prefix ; $(touch must-not-exist)"
LIMIT = 16 * 1024
PROBE_SCRIPT = r"""
import json
import os
import sys

args = sys.argv[1:]
with open(os.environ["PROBE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"args": args, "stdin": sys.stdin.read()}) + "\n")
if args[0:1] != [os.environ["PROBE_PREFIX"]]:
    sys.exit(80)
operation = args[1:]
if operation == ["--version"]:
    print(os.environ["PROBE_VERSION"], flush=True)
    sys.exit(0)
if operation != ["login", "status"]:
    sys.exit(81)
stream = sys.stdout if os.environ["PROBE_STREAM"] == "stdout" else sys.stderr
secret = "sk-" + "proj-fixturecredential12345678901234567890"
print("Not logged in: expired credential; account needs reauthentication", file=stream)
print("Authorization: Bearer " + secret, file=stream, flush=True)
stream.write("é" * int(os.environ["PROBE_PADDING"]))
stream.flush()
sys.exit(int(os.environ["PROBE_EXIT"]))
"""


@pytest.fixture
def probe_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "isolated-config"))
    project = tmp_path / "project"
    project.mkdir()
    (tmp_path / "probe.py").write_text(PROBE_SCRIPT, encoding="utf-8")
    return project


def configured_probe(
    project: Path,
    version: str = "codex-cli 0.160.0",
    stream: str = "stderr",
    padding: int = 0,
    exit_code: int = 23,
) -> CodexDriver:
    argv = (sys.executable, str(project.parent / "probe.py"), PREFIX)
    environment = {
        "PROBE_LOG": str(project.parent / "probe.jsonl"),
        "PROBE_PREFIX": PREFIX,
        "PROBE_VERSION": version,
        "PROBE_STREAM": stream,
        "PROBE_PADDING": str(padding),
        "PROBE_EXIT": str(exit_code),
    }
    configuration = (
        'agent = "codex"\n[agents.codex]\n'
        f"command = {json.dumps(argv)}\n"
        'tiers = { standard = "fixture-model" }\n'
        "environment = { "
        + ", ".join(
            f"{key} = {json.dumps(value)}" for key, value in environment.items()
        )
        + ' }\n[agents.codex.options]\nsandbox = "workspace-write"\n'
        'approval = "never"\n'
    )
    (project / CONFIG_NAME).write_text(configuration, encoding="utf-8")
    driver = build_driver(project, "codex")
    assert isinstance(driver, CodexDriver)
    return driver


@pytest.mark.parametrize(
    "version",
    (
        "prefixnoise codex-cli 0.160.0",
        "codex-cli 0.160.0-rc.1",
        "codex-cli 0.160.0.1",
        "codex-cli 0.160.00",
        "codex-cli 0.160.0+unreviewed",
        "codex-cli 0.160.0 trailing-noise",
        "codex-cli 0.160.01",
        "unreviewed first line\ncodex-cli 0.160.0",
    ),
)
def test_probe_rejects_version_aliases_that_are_not_exact_reviewed_evidence(
    probe_project: Path, version: str
) -> None:
    health = configured_probe(probe_project, version=version, exit_code=0).probe()
    assert isinstance(health, DriverHealth)
    assert health.healthy is False
    assert "0.160.0" in health.detail
    assert health.detail.strip()
    records = (probe_project.parent / "probe.jsonl").read_text().splitlines()
    assert [json.loads(record) for record in records] == [
        {"args": [PREFIX, "--version"], "stdin": ""}
    ]


@pytest.mark.parametrize("stream", ("stdout", "stderr"))
@pytest.mark.parametrize("exit_code", (1, 23))
def test_probe_preserves_actionable_sanitized_authentication_failures(
    probe_project: Path,
    capfd: pytest.CaptureFixture[str],
    stream: str,
    exit_code: int,
) -> None:
    health = configured_probe(probe_project, stream=stream, exit_code=exit_code).probe()
    captured = capfd.readouterr()
    assert health.healthy is False
    assert "expired credential" in health.detail.lower()
    assert "codex login" in health.detail.lower()
    assert re.search(rf"(?<!\d){exit_code}(?!\d)", health.detail)
    assert len(health.detail.encode("utf-8")) <= LIMIT
    disclosed = health.detail + captured.out + captured.err
    assert SECRET not in disclosed
    assert "fixturecredential12345678901234567890" not in disclosed
    records = (probe_project.parent / "probe.jsonl").read_text().splitlines()
    assert [json.loads(record) for record in records] == [
        {"args": [PREFIX, "--version"], "stdin": ""},
        {"args": [PREFIX, "login", "status"], "stdin": ""},
    ]
    assert not (probe_project / "must-not-exist").exists()


@pytest.mark.parametrize("stream", ("stdout", "stderr"))
def test_probe_bounds_authentication_details_and_retains_useful_diagnostics(
    probe_project: Path, capfd: pytest.CaptureFixture[str], stream: str
) -> None:
    health = configured_probe(probe_project, stream=stream, padding=131072).probe()
    captured = capfd.readouterr()
    assert isinstance(health, DriverHealth)
    assert health.healthy is False
    assert "expired credential" in health.detail.lower()
    assert "codex login" in health.detail.lower()
    assert len(health.detail.encode("utf-8")) <= LIMIT
    disclosed = health.detail + captured.out + captured.err
    assert SECRET not in disclosed
    assert "fixturecredential12345678901234567890" not in disclosed
