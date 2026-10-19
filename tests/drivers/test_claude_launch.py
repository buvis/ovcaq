from __future__ import annotations

import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import DriverHealth, LaunchRequest
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.events import (
    PROTOCOL_VERSION,
    Observation,
    ObservationType,
    reduce_session,
)


@pytest.fixture
def settings() -> AgentSettings:
    return AgentSettings(
        name="claude",
        command=(sys.executable, "--literal-wrapper-argument"),
        tiers={"standard": "provider-primary", "backup": "provider-backup"},
        environment={"WARDEN_UNATTENDED": "1"},
        options={"permission_mode": "auto"},
    )


@pytest.fixture
def launch_request(tmp_path: Path) -> LaunchRequest:
    return LaunchRequest(
        root=tmp_path,
        phase="build",
        prompt="Keep this literal; $(anything) | anything\nsecond line",
        model="standard",
        effort="high",
        timeout_seconds=37,
        session_dir=tmp_path / "session",
    )


@pytest.mark.parametrize("effort", ("low", "medium", "high"))
@pytest.mark.parametrize(
    ("fallback_model", "fallback_arguments"),
    (
        (None, ()),
        ("standard", ()),
        ("backup", ("--fallback-model", "provider-backup")),
    ),
)
def test_launch_preserves_exact_argv_and_literal_prompt(
    settings: AgentSettings,
    launch_request: LaunchRequest,
    fallback_model: str | None,
    fallback_arguments: tuple[str, ...],
    effort: str,
) -> None:
    launch_request = replace(launch_request, effort=effort)
    options = dict(settings.options)
    if fallback_model is not None:
        options["fallback_model"] = fallback_model
    driver = ClaudeDriver(replace(settings, options=options), run_id="run-6")

    spec = driver.build_launch(launch_request)

    assert driver.name == "claude"
    assert spec.argv == (
        *settings.command,
        "-p",
        "--permission-mode",
        "auto",
        "--model",
        "provider-primary",
        "--effort",
        effort,
        *fallback_arguments,
        "--output-format",
        "stream-json",
        "--verbose",
        launch_request.prompt,
    )
    assert spec.cwd == launch_request.root
    assert spec.raw_format == "claude-stream-json-v1"


@pytest.mark.parametrize("swap_tiers", (False, True))
@pytest.mark.parametrize(
    ("primary_tier", "fallback_tier", "primary_model", "fallback_model"),
    (
        ("standard", "backup", "alternate-primary", "another-provider-model"),
        ("primary", "reserve", "custom-main", "reserved-provider"),
    ),
)
def test_fallback_argv_resolves_configured_models_after_tier_names_and_roles_change(
    settings: AgentSettings,
    launch_request: LaunchRequest,
    primary_tier: str,
    fallback_tier: str,
    primary_model: str,
    fallback_model: str,
    swap_tiers: bool,
) -> None:
    tiers = {primary_tier: primary_model, fallback_tier: fallback_model}
    if swap_tiers:
        primary_tier, fallback_tier = fallback_tier, primary_tier
        primary_model, fallback_model = fallback_model, primary_model
    settings = replace(
        settings,
        tiers=tiers,
        options={"permission_mode": "auto", "fallback_model": fallback_tier},
    )
    request = replace(launch_request, model=primary_tier)

    spec = ClaudeDriver(settings, run_id="run-6").build_launch(request)

    assert spec.argv == (
        *settings.command,
        "-p",
        "--permission-mode",
        "auto",
        "--model",
        primary_model,
        "--effort",
        "high",
        "--fallback-model",
        fallback_model,
        "--output-format",
        "stream-json",
        "--verbose",
        request.prompt,
    )


def test_fallback_with_a_distinct_tier_but_same_model_is_omitted(
    settings: AgentSettings, launch_request: LaunchRequest
) -> None:
    settings = replace(
        settings,
        tiers={"standard": "provider-primary", "alias": "provider-primary"},
        options={"permission_mode": "auto", "fallback_model": "alias"},
    )
    spec = ClaudeDriver(settings, run_id="run-6").build_launch(launch_request)
    assert "--fallback-model" not in spec.argv


@pytest.mark.parametrize("warden_value", ("1", "0", "configured-value"))
def test_launch_environment_contains_only_defaults_and_configured_values(
    settings: AgentSettings,
    launch_request: LaunchRequest,
    monkeypatch: pytest.MonkeyPatch,
    warden_value: str,
) -> None:
    monkeypatch.setenv("HOST_ONLY_MARKER", "must-not-leak")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "host-secret")
    monkeypatch.setenv("CLAUDE_HOST_MARKER", "must-not-leak")
    monkeypatch.setenv("CLAUDE_UNATTENDED", "host-value")
    monkeypatch.setenv("WARDEN_UNATTENDED", "host-value")
    configured = {
        "WARDEN_UNATTENDED": warden_value,
        "CLAUDE_UNATTENDED": "1",
        "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
        "CLAUDE_EXTRA_SETTING": "configured-value",
        "LOCAL_RUN_MODE": "configured-value",
        "PATH": "/configured/tools",
    }
    settings = replace(settings, environment=configured)
    driver = ClaudeDriver(settings, run_id="run-6")

    first = driver.build_launch(launch_request)
    monkeypatch.setenv("CLAUDE_EXTRA_SETTING", "later-host-value")
    second = driver.build_launch(launch_request)

    assert dict(first.env) == configured
    assert dict(second.env) == configured
    assert first.env is not second.env


def test_launch_supplies_unattended_defaults_when_environment_is_empty(
    settings: AgentSettings, launch_request: LaunchRequest
) -> None:
    driver = ClaudeDriver(replace(settings, environment={}), run_id="run-6")
    assert dict(driver.build_launch(launch_request).env) == {
        "CLAUDE_UNATTENDED": "1",
        "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
    }


@pytest.mark.parametrize(
    "environment",
    (
        {"CLAUDE_UNATTENDED": "0"},
        {"CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "1000"},
    ),
)
def test_rejects_changed_fixed_unattended_defaults(
    settings: AgentSettings, environment: dict[str, str]
) -> None:
    settings = replace(settings, environment=environment)
    with pytest.raises(ValueError):
        ClaudeDriver(settings, run_id="run-6")


@pytest.mark.parametrize(
    "options",
    (
        {},
        {"permission_mode": None},
        {"permission_mode": True},
        {"permission_mode": ""},
        {"permission_mode": "default"},
        {"permission_mode": "bypassPermissions"},
        {"permission_mode": "acceptEdits"},
        {"permission_mode": "plan"},
        {"permission_mode": "AUTO"},
        {"permission_mode": "auto", "unknown_option": True},
        {"permission_mode": "auto", "allow_explicit_model": "true"},
        {"permission_mode": "auto", "allow_explicit_model": 1},
        {"permission_mode": "auto", "fallback_tier": True},
        {"permission_mode": "auto", "fallback_tier": ""},
        {"permission_mode": "auto", "fallback_tier": "backup"},
        {"permission_mode": "auto", "fallback_model": None},
        {"permission_mode": "auto", "fallback_model": True},
        {"permission_mode": "auto", "fallback_model": 1},
        {"permission_mode": "auto", "fallback_model": ""},
        {"permission_mode": "auto", "fallback_model": " \t"},
    ),
)
def test_rejects_missing_unsafe_or_mistyped_options(
    settings: AgentSettings, options: dict[str, object]
) -> None:
    settings = replace(settings, options=options)
    with pytest.raises(ValueError):
        ClaudeDriver(settings, run_id="run-6")


@pytest.mark.parametrize("model", (None, "unknown-tier", "provider-primary"))
def test_launch_requires_a_configured_tier_without_explicit_model_opt_in(
    settings: AgentSettings, launch_request: LaunchRequest, model: str | None
) -> None:
    driver = ClaudeDriver(settings, run_id="run-6")
    with pytest.raises(ValueError):
        driver.build_launch(replace(launch_request, model=model))


@pytest.mark.parametrize(
    ("model", "resolved"),
    (("standard", "provider-primary"), ("provider-explicit", "provider-explicit")),
)
def test_explicit_model_opt_in_preserves_tier_resolution(
    settings: AgentSettings,
    launch_request: LaunchRequest,
    model: str,
    resolved: str,
) -> None:
    settings = replace(
        settings, options={"permission_mode": "auto", "allow_explicit_model": True}
    )
    spec = ClaudeDriver(settings, run_id="run-6").build_launch(
        replace(launch_request, model=model)
    )
    assert spec.argv[spec.argv.index("--model") + 1] == resolved


@pytest.mark.parametrize("effort", (None, " ", "\t"))
def test_launch_rejects_missing_or_blank_effort(
    settings: AgentSettings, launch_request: LaunchRequest, effort: str | None
) -> None:
    driver = ClaudeDriver(settings, run_id="run-6")
    with pytest.raises(ValueError):
        driver.build_launch(replace(launch_request, effort=effort))


@pytest.mark.parametrize("allow_explicit_model", (False, True))
@pytest.mark.parametrize("fallback_model", ("unknown-tier", "provider-primary"))
def test_fallback_must_resolve_a_configured_tier_even_with_explicit_models_enabled(
    settings: AgentSettings,
    launch_request: LaunchRequest,
    allow_explicit_model: bool,
    fallback_model: str,
) -> None:
    settings = replace(
        settings,
        options={
            "permission_mode": "auto",
            "allow_explicit_model": allow_explicit_model,
            "fallback_model": fallback_model,
        },
    )
    with pytest.raises(ValueError):
        ClaudeDriver(settings, run_id="run-6").build_launch(launch_request)


@pytest.mark.parametrize("command_kind", ("missing", "nonexecutable", "directory"))
def test_probe_reports_unusable_commands_with_a_visible_reason(
    settings: AgentSettings, tmp_path: Path, command_kind: str
) -> None:
    command = tmp_path / "agent-command"
    if command_kind == "nonexecutable":
        command.write_text("unexecutable command", encoding="utf-8")
        command.chmod(0o600)
    elif command_kind == "directory":
        command.mkdir()
    driver = ClaudeDriver(replace(settings, command=(str(command),)), run_id="run-6")

    health = driver.probe()

    assert isinstance(health, DriverHealth)
    assert health.healthy is False
    assert health.detail.strip()


def test_probe_finds_path_commands_without_running_them(
    settings: AgentSettings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    marker = tmp_path / "command-was-executed"
    command = tmp_path / "test-agent"
    command.write_text(
        f"#!{sys.executable}\n"
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).touch()\n",
        encoding="utf-8",
    )
    command.chmod(0o700)
    monkeypatch.setenv("PATH", str(tmp_path))
    driver = ClaudeDriver(replace(settings, command=(command.name,)), run_id="run-6")

    health = driver.probe()

    assert health.healthy is True
    assert health.detail.strip()
    assert "permission_mode=auto" in health.detail
    assert driver.probe() == health
    assert not marker.exists()


@pytest.mark.parametrize("exit_code", (0, 7))
@pytest.mark.parametrize("completed", (False, True))
def test_summary_matches_the_neutral_reducer_for_single_pass_observations(
    settings: AgentSettings, exit_code: int, completed: bool
) -> None:
    observations = (
        (
            Observation(
                protocol_version=PROTOCOL_VERSION,
                timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                provider="claude",
                run_id="run-6",
                session_id="session-6",
                lane_id=None,
                type=ObservationType.SESSION_COMPLETED,
                payload={},
            ),
        )
        if completed
        else ()
    )
    driver = ClaudeDriver(settings, run_id="run-6")
    driver.decode(
        '{"type":"result","subtype":"error","is_error":true,'
        '"session_id":"prior-session","result":"permission denied"}'
    )
    assert (
        driver.summarize(iter(observations), exit_code)
        == reduce_session(observations, exit_code).summary
    )
