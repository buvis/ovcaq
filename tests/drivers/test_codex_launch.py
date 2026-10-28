"""Codex launch arguments remain literal and configuration-driven."""

import json
import logging
import subprocess
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import AgentDriver, LaunchRequest
from ovcaq.drivers.codex import CodexDriver
from ovcaq.drivers.edge import build_driver


def toml_value(value: object) -> str:
    if isinstance(value, Mapping):
        return (
            "{ "
            + ", ".join(
                f"{json.dumps(key)} = {toml_value(item)}" for key, item in value.items()
            )
            + " }"
        )
    return json.dumps(value)


def configure_driver(
    settings: AgentSettings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AgentDriver:
    root = tmp_path / "configured-project"
    root.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "provider-home"))
    (root / "ovcaq.toml").write_text(
        'agent = "codex"\n[agents.codex]\n'
        f"command = {toml_value(settings.command)}\n"
        f"tiers = {toml_value(dict(settings.tiers))}\n"
        f"environment = {toml_value(dict(settings.environment))}\n"
        f"options = {toml_value(dict(settings.options))}\n"
    )
    return build_driver(root, "codex")


@pytest.fixture
def settings() -> AgentSettings:
    return AgentSettings(
        name="codex",
        command=("fixture-wrapper", "--literal-prefix", "fixture-launcher"),
        tiers={"standard": "fixture-model", "premium": "fixture-large"},
        environment={"TASK_MODE": "fixture", "TASK_LABEL": "two words"},
        options={},
    )


@pytest.fixture
def launch_request(tmp_path: Path) -> LaunchRequest:
    return LaunchRequest(
        root=tmp_path / "project with spaces",
        phase="build",
        prompt="--literal prompt\nsecond line",
        model=None,
        effort=None,
        timeout_seconds=123,
        session_dir=tmp_path / "session",
    )


@pytest.mark.parametrize(
    ("model", "resolved"),
    ((None, None), ("standard", "fixture-model"), ("fixture-model", "fixture-model")),
)
@pytest.mark.parametrize("effort", (None, "low", "medium", "high", "xhigh"))
@pytest.mark.parametrize("use_factory", (False, True), ids=("direct", "configured"))
def test_launch_has_exact_order_and_omits_unconfigured_flags(
    settings: AgentSettings,
    launch_request: LaunchRequest,
    model: str | None,
    resolved: str | None,
    effort: str | None,
    use_factory: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = (
        configure_driver(settings, tmp_path, monkeypatch)
        if use_factory
        else CodexDriver(settings, run_id="launch-contract")
    )
    requested = replace(launch_request, model=model, effort=effort)
    spec = driver.build_launch(requested)
    expected = (
        *settings.command,
        "--ask-for-approval",
        "never",
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
        "-C",
        str(launch_request.root),
        *(("-m", resolved) if resolved is not None else ()),
        *(("-c", f'model_reasoning_effort="{effort}"') if effort is not None else ()),
        "--",
        launch_request.prompt,
    )
    assert driver.name == "codex"
    assert spec.argv == expected
    assert spec.cwd == launch_request.root
    assert spec.raw_format == "codex-exec-json-v1"
    assert dict(spec.env) == dict(settings.environment)
    assert spec.env is not settings.environment


@pytest.mark.parametrize(
    "options",
    (
        {"sandbox": "workspace-write"},
        {"approval": "never"},
        {"allow_explicit_model": False},
        {"allow_explicit_model": True},
        {
            "sandbox": "workspace-write",
            "approval": "never",
            "allow_explicit_model": False,
        },
    ),
)
def test_accepted_options_keep_the_safe_launch_defaults(
    settings: AgentSettings, launch_request: LaunchRequest, options: dict[str, object]
) -> None:
    baseline = CodexDriver(settings, run_id="baseline").build_launch(launch_request)
    selected = CodexDriver(replace(settings, options=options), run_id="selected")
    assert selected.build_launch(launch_request) == baseline


@pytest.mark.parametrize(
    "options",
    (
        *(
            {"sandbox": value}
            for value in ("read-only", "danger-full-access", "", None, True, 1, {})
        ),
        *(
            {"approval": value}
            for value in (
                "on-request",
                "untrusted",
                "on-failure",
                "",
                None,
                False,
                0,
                [],
            )
        ),
        *(
            {"allow_explicit_model": value}
            for value in (None, 0, 1, "false", "true", [], {})
        ),
        {"unknown": True},
    ),
)
def test_constructor_rejects_unknown_or_invalid_options(
    settings: AgentSettings, options: dict[str, object]
) -> None:
    with pytest.raises(ValueError) as raised:
        CodexDriver(replace(settings, options=options), run_id="invalid-options")
    assert raised.type is ValueError


@pytest.mark.parametrize(
    ("tiers", "requested", "resolved"),
    (
        (
            {"standard": "premium", "premium": "fixture-large"},
            "premium",
            "fixture-large",
        ),
        ({"default": "o3", "o3": "o3-pro"}, "o3", "o3-pro"),
    ),
)
def test_tier_key_resolves_before_a_matching_configured_model_value(
    settings: AgentSettings,
    launch_request: LaunchRequest,
    tiers: dict[str, str],
    requested: str,
    resolved: str,
) -> None:
    settings = replace(settings, tiers=tiers)
    driver = CodexDriver(settings, run_id="tier-precedence")
    argv = driver.build_launch(replace(launch_request, model=requested)).argv
    assert argv[-4:] == ("-m", resolved, "--", launch_request.prompt)


@pytest.mark.parametrize(
    ("tier", "configured_model"),
    (("standard", "fixture-standard-model"), ("deep", "default-fixture-model")),
)
def test_codex_default_tier_omits_model_segment(
    settings: AgentSettings,
    launch_request: LaunchRequest,
    tier: str,
    configured_model: str,
) -> None:
    request = replace(launch_request, model=tier)
    defaulted = CodexDriver(
        replace(settings, tiers={}), run_id="default-tiers"
    ).build_launch(request)
    configured = CodexDriver(
        replace(settings, tiers={tier: configured_model}), run_id="configured-tiers"
    ).build_launch(request)
    reserved = CodexDriver(
        replace(settings, tiers={}, options={"allow_explicit_model": False}),
        run_id="reserved-tier",
    ).build_launch(replace(launch_request, model="default"))

    assert "-m" not in defaulted.argv
    assert defaulted.argv[-2:] == ("--", launch_request.prompt)
    assert configured.argv[-4:] == ("-m", configured_model, "--", launch_request.prompt)
    assert "-m" not in reserved.argv
    assert reserved.argv[-2:] == ("--", launch_request.prompt)
    assert defaulted.cwd == launch_request.root
    assert dict(defaulted.env) == dict(settings.environment)


@pytest.mark.parametrize("allow", (None, False, True))
@pytest.mark.parametrize("use_factory", (False, True), ids=("direct", "configured"))
def test_arbitrary_explicit_models_require_the_opt_in(
    settings: AgentSettings,
    launch_request: LaunchRequest,
    allow: bool | None,
    use_factory: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = {} if allow is None else {"allow_explicit_model": allow}
    selected = replace(settings, options=options)
    driver = (
        configure_driver(selected, tmp_path, monkeypatch)
        if use_factory
        else CodexDriver(selected, run_id="explicit-model")
    )
    requested = replace(launch_request, model="unconfigured-model")
    if allow:
        assert driver.build_launch(requested).argv[-4:] == (
            "-m",
            "unconfigured-model",
            "--",
            launch_request.prompt,
        )
    else:
        with pytest.raises(ValueError):
            driver.build_launch(requested)


@pytest.mark.parametrize("effort", ("maximum", "HIGH", " high "))
def test_unmapped_effort_warns_once_and_omits_the_override(
    settings: AgentSettings,
    launch_request: LaunchRequest,
    effort: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    driver = CodexDriver(settings, run_id="effort-warning")
    baseline = driver.build_launch(launch_request)
    with caplog.at_level(logging.WARNING, logger="ovcaq.drivers.codex"):
        spec = driver.build_launch(replace(launch_request, effort=effort))
    assert spec == baseline
    assert len(caplog.records) == 1
    assert caplog.records[0].name == "ovcaq.drivers.codex"
    assert caplog.records[0].levelno == logging.WARNING
    assert effort in caplog.records[0].getMessage()


@pytest.mark.parametrize("effort", (" ", "\t", "\n"))
def test_blank_effort_is_rejected(
    settings: AgentSettings, launch_request: LaunchRequest, effort: str
) -> None:
    driver = CodexDriver(settings, run_id="blank-effort")
    with pytest.raises(ValueError):
        driver.build_launch(replace(launch_request, effort=effort))


def test_building_a_launch_does_not_spawn_or_evaluate_literal_inputs(
    settings: AgentSettings,
    launch_request: LaunchRequest,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_spawn(*args: object, **kwargs: object) -> None:
        pytest.fail("constructor and build_launch must not spawn a process")

    monkeypatch.setattr(subprocess, "Popen", unexpected_spawn)
    monkeypatch.setattr(subprocess, "run", unexpected_spawn)
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "unread-provider-home"))
    monkeypatch.setenv("OPENAI_API_KEY", "sanitized-host-only-value")
    marker = tmp_path / "shell-marker"
    prefix = f"$(touch '{marker}')"
    prompt = f"--help; touch '{marker}'\n`touch '{marker}'`"
    selected = replace(settings, command=("fixture-launcher", prefix))
    driver = CodexDriver(selected, run_id="literal-launch")
    spec = driver.build_launch(replace(launch_request, prompt=prompt))
    assert spec.argv[:2] == selected.command
    assert spec.argv[-2:] == ("--", prompt)
    assert dict(spec.env) == dict(settings.environment)
    assert not marker.exists()
    assert not launch_request.root.exists()
    assert not launch_request.session_dir.exists()
