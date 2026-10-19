"""The driver edge selects configured providers without launching them."""

from pathlib import Path

import pytest

from ovcaq.drivers.base import DRIVER_API_VERSION, LaunchRequest
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.drivers.codex import CodexDriver
from ovcaq.drivers.edge import build_driver
from ovcaq.errors import CommandError, ErrorCode
from ovcaq.paths import CONFIG_NAME


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "isolated-config"))
    project = tmp_path / "project"
    project.mkdir()
    (project / CONFIG_NAME).write_text(
        'agent = "codex"\n'
        "[agents.codex]\n"
        'command = ["fixture-wrapper", "--codex-prefix", "fixture-codex"]\n'
        'tiers = { standard = "fixture-codex-model" }\n'
        'environment = { TASK_MODE = "codex-fixture" }\n'
        "[agents.codex.options]\n"
        'sandbox = "workspace-write"\n'
        'approval = "never"\n'
        "[agents.claude]\n"
        'command = ["fixture-claude"]\n'
        'tiers = { sonnet = "fixture-claude-model" }\n'
        'environment = { TASK_MODE = "claude-fixture" }\n'
        "[agents.claude.options]\n"
        'permission_mode = "auto"\n'
        "[agents.unsupported]\n"
        'command = ["fixture-unsupported"]\n',
        encoding="utf-8",
    )
    return project


@pytest.mark.parametrize("name", (None, "codex"))
def test_edge_selects_codex_and_preserves_the_configured_launch(
    root: Path, name: str | None
) -> None:
    driver = build_driver(root, name)
    request = LaunchRequest(
        root=root,
        phase="build",
        prompt="--literal configured prompt",
        model="standard",
        effort="high",
        timeout_seconds=123,
        session_dir=root / "session",
    )
    spec = driver.build_launch(request)
    assert isinstance(driver, CodexDriver)
    assert driver.name == "codex"
    assert DRIVER_API_VERSION == 2
    assert spec.argv == (
        "fixture-wrapper",
        "--codex-prefix",
        "fixture-codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
        "-C",
        str(root),
        "-m",
        "fixture-codex-model",
        "-c",
        'model_reasoning_effort="high"',
        "--",
        request.prompt,
    )
    assert dict(spec.env) == {"TASK_MODE": "codex-fixture"}
    assert spec.cwd == root
    assert spec.raw_format == "codex-exec-json-v1"


def test_name_override_preserves_the_claude_resolved_model_bridge(root: Path) -> None:
    driver = build_driver(root, "claude")
    request = LaunchRequest(
        root=root,
        phase="build",
        prompt="literal Claude prompt",
        model="fixture-claude-model",
        effort="high",
        timeout_seconds=123,
        session_dir=root / "session",
    )
    spec = driver.build_launch(request)
    assert isinstance(driver, ClaudeDriver)
    assert driver.name == "claude"
    assert spec.argv[0] == "fixture-claude"
    assert spec.argv.count("fixture-claude-model") == 1
    assert "sonnet" not in spec.argv
    assert spec.env["TASK_MODE"] == "claude-fixture"
    assert spec.cwd == root


def test_unsupported_agent_keeps_the_runtime_format_error(root: Path) -> None:
    with pytest.raises(CommandError) as caught:
        build_driver(root, "unsupported")
    assert caught.value.code is ErrorCode.RUNTIME_FORMAT
    assert caught.value.exit_code == 1
