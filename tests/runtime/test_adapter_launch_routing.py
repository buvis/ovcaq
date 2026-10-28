"""Configured supervisor routes preserve the selected model at launch."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from tests.runtime.test_supervisor import Harness, rows
from tests.runtime.test_supervisor_adapters import (
    adapter_harness,
    prepare_workflow,
    write_workflow_fixture,
)

from ovcaq.config import AgentSettings, resolve_phase_route, supervisor_settings
from ovcaq.drivers.base import LaunchRequest
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.drivers.codex import CodexDriver
from ovcaq.drivers.edge import build_driver
from ovcaq.runtime.decision import DecisionKind
from ovcaq.runtime.session import reconcile_metrics
from ovcaq.runtime.supervisor import Supervisor


def configure_workflow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tiers: dict[str, str],
    routes: tuple[tuple[str, str, str], ...],
    provider: str,
) -> Harness:
    h = adapter_harness(tmp_path, monkeypatch)
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "provider-home"))
    fake = write_workflow_fixture(tmp_path, provider)
    command = [sys.executable, "-u", str(fake)]
    cli = str(Path(sys.executable).with_name("ovcaq"))
    (h.root / "ovcaq.toml").write_text(
        f"agent = {json.dumps(provider)}\n[agents.{provider}]\n"
        f"command = {json.dumps(command)}\n"
        "tiers = { "
        + ", ".join(
            f"{json.dumps(key)} = {json.dumps(value)}" for key, value in tiers.items()
        )
        + " }\n"
        + ('options = { permission_mode = "auto" }\n' if provider == "claude" else "")
        + 'environment = { OVCAQ_FAKE_SCENARIO = "workflow", '
        'OVCAQ_FAKE_MARKER = "ordinary value with spaces", '
        f"OVCAQ_FAKE_CLI = {json.dumps(cli)} }}\n"
        "[workflow]\nruntime_root = 'runtime'\n"
        f"state_file = {json.dumps(str(h.paths.state_file))}\n"
        + "".join(
            f"[phases.{phase}]\ntier = {json.dumps(tier)}\n"
            f"effort = {json.dumps(effort)}\n"
            "timeout_seconds = 3\n"
            for phase, tier, effort in routes
        )
    )
    prepare_workflow(h)
    return h


def write_agent_config(root: Path, provider: str, tiers: str) -> Path:
    root.mkdir()
    (root / "ovcaq.toml").write_text(
        f"agent = {json.dumps(provider)}\n[agents.{provider}]\n"
        'command = ["fixture-runner"]\n' + tiers
    )
    return root


@pytest.mark.parametrize("provider", ["codex", "claude"])
@pytest.mark.parametrize(
    ("tiers", "routes"),
    (
        (
            {"default": "o3", "o3": "o3-pro", "cleanup": "fixture-last"},
            (
                ("build", "default", "low"),
                ("review", "o3", "xhigh"),
                ("done", "cleanup", "medium"),
            ),
        ),
        (
            {
                "default": "fixture-fast",
                "fixture-fast": "fixture-careful",
                "cleanup": "fixture-final",
            },
            (
                ("build", "fixture-fast", "medium"),
                ("review", "default", "low"),
                ("done", "cleanup", "xhigh"),
            ),
        ),
        (
            {
                "default": "fixture-plain",
                "reviewer": "fixture-review",
                "cleanup": "fixture-finish",
            },
            (
                ("build", "default", "xhigh"),
                ("review", "reviewer", "medium"),
                ("done", "cleanup", "low"),
            ),
        ),
    ),
    ids=("named-collision", "different-collision", "distinct-models"),
)
def test_configured_supervisor_launches_each_selected_literal_model_and_effort(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tiers: dict[str, str],
    routes: tuple[tuple[str, str, str], ...],
    provider: str,
) -> None:
    h = configure_workflow(tmp_path, monkeypatch, tiers, routes, provider)
    settings = supervisor_settings(
        h.root, runtime=h.settings.runtime, policy=h.settings.policy
    )
    supervisor = Supervisor(
        h.root,
        store=h.store,
        driver=build_driver(h.root, provider),
        settings=settings,
        capability_runner=lambda _: h.runner,
        clock=h.clock,
        sleeper=h.waits.append,
    )
    outcome = supervisor.run()
    assert outcome.exit_code == 0 and outcome.decision.kind == DecisionKind.COMPLETE
    assert outcome.sessions_attempted == 3
    metrics = [
        metric for metric in reconcile_metrics(h.paths) if metric.kind == "phase"
    ]
    assert [metric.phase_launched for metric in metrics] == ["build", "review", "done"]
    for metric, (_, tier, effort) in zip(metrics, routes, strict=True):
        raw = rows(h.paths.sessions / metric.session_id / "raw.jsonl")
        (invocation,) = [row for row in raw if row.get("type") == "fake_invocation"]
        argv = invocation["argv"]
        model_flag = "--model" if provider == "claude" else "-m"
        assert argv.count(model_flag) == 1
        assert argv[argv.index(model_flag) + 1] == tiers[tier]
        if provider == "claude":
            assert argv.count("--effort") == 1
            assert argv[argv.index("--effort") + 1] == effort
        else:
            assert argv.count("-c") == 1
            assert argv[argv.index("-c") + 1] == f'model_reasoning_effort="{effort}"'
        assert (
            invocation["environment"]["OVCAQ_FAKE_MARKER"]
            == "ordinary value with spaces"
        )


def launch_argv_for_tier(
    driver_class: type[ClaudeDriver | CodexDriver],
    provider: str,
    root: Path,
    tier: str,
) -> tuple[str, ...]:
    settings = AgentSettings(
        name=provider,
        command=("fixture-runner",),
        tiers={},
        environment={},
        options={"permission_mode": "auto"} if provider == "claude" else {},
    )
    request = LaunchRequest(
        root=root,
        phase="build",
        prompt="fixture routed prompt",
        model=tier,
        effort="high",
        timeout_seconds=3,
        session_dir=root / "session",
    )
    driver = driver_class(settings, run_id="default-tier-route")
    argv: tuple[str, ...] = driver.build_launch(request).argv
    return argv


@pytest.mark.parametrize(
    ("provider", "driver_class", "expected_defaults"),
    (
        ("claude", ClaudeDriver, {"standard": "sonnet", "deep": "opus"}),
        ("codex", CodexDriver, {"standard": "default", "deep": "default"}),
    ),
)
def test_unconfigured_project_routes_through_driver_default_tiers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    driver_class: type[ClaudeDriver | CodexDriver],
    expected_defaults: dict[str, str],
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
    unconfigured = write_agent_config(tmp_path / "unconfigured", provider, "")
    configured = write_agent_config(
        tmp_path / "configured",
        provider,
        'tiers = { standard = "fixture-configured-standard" }\n',
    )
    defaults = driver_class.default_tiers
    sentinel = {"standard": "sentinel-standard", "deep": "sentinel-deep"}
    phases = ("build", "review", "done")
    expected_tiers = ("standard", "deep", "standard")

    routes = [
        resolve_phase_route(unconfigured, phase, default_tiers=defaults)
        for phase in phases
    ]
    sentinels = [
        resolve_phase_route(unconfigured, phase, default_tiers=sentinel)
        for phase in phases
    ]

    assert dict(defaults) == expected_defaults
    assert [route.agent for route in routes] == [provider] * 3
    assert [route.tier for route in routes] == list(expected_tiers)
    assert [route.model for route in routes] == [
        expected_defaults[tier] for tier in expected_tiers
    ]
    assert [route.model for route in sentinels] == [
        sentinel[tier] for tier in expected_tiers
    ]
    for route in routes:
        argv = launch_argv_for_tier(driver_class, provider, unconfigured, route.tier)
        if provider == "claude":
            assert argv.count("--model") == 1
            assert argv[argv.index("--model") + 1] == route.model
        else:
            assert "-m" not in argv
    for table in (defaults, sentinel):
        route = resolve_phase_route(configured, "build", default_tiers=table)
        assert route.model == "fixture-configured-standard"
