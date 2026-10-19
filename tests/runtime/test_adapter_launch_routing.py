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

from ovcaq.config import supervisor_settings
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
