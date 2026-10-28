from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from tests.runtime.test_supervisor import Harness, add_capability, harness, rows

from ovcaq.config import AgentSettings
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.drivers.codex import CodexDriver
from ovcaq.paths import state_path
from ovcaq.runtime.decision import DecisionKind
from ovcaq.runtime.session import reconcile_metrics
from ovcaq.runtime.supervisor import Supervisor
from ovcaq.state.schema import State
from ovcaq.state.store import StateStore


def adapter_harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Harness:
    h = harness(tmp_path, monkeypatch)
    monkeypatch.setattr(h.clock, "now", lambda: datetime.now(UTC))
    committed = h.store.read()
    canonical = state_path(h.root)
    canonical.parent.mkdir(parents=True, exist_ok=True)
    h.store = StateStore(canonical)
    h.store.initialize(committed)
    h.paths = replace(h.paths, state_file=canonical)
    h.settings = replace(h.settings, runtime=replace(h.settings.runtime, paths=h.paths))
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state-home"))
    return h


def write_workflow_fixture(tmp_path: Path, provider: str) -> Path:
    fixtures = Path(__file__).parents[1] / "fixtures"
    fake = fixtures / "codex/v1/fake_codex.py"
    if provider == "claude":
        fake = tmp_path / "fake_claude_workflow.py"
        fake.write_text(
            "import runpy, sys\n"
            f"edge = runpy.run_path({str(fixtures / 'codex/v1/fake_codex.py')!r})\n"
            f"edge['workflow'].__globals__['__file__'] = {str(fixtures / 'claude/v1/fake_claude.py')!r}\n"
            "edge['emit_invocation'](sys.argv[1:])\n"
            "raise SystemExit(edge['workflow']())\n"
        )
    return fake


def workflow_agent(h: Harness, tmp_path: Path, provider: str) -> AgentSettings:
    fake = write_workflow_fixture(tmp_path, provider)
    command = [sys.executable, str(fake)]
    environment = {
        "OVCAQ_FAKE_SCENARIO": "workflow",
        "OVCAQ_FAKE_CLI": str(Path(sys.executable).with_name("ovcaq")),
    }
    (h.root / "ovcaq.toml").write_text(
        f"agent = {json.dumps(provider)}\n"
        f"[agents.{provider}]\ncommand = {json.dumps(command)}\n"
        'tiers = { standard = "model-s", deep = "model-o" }\n'
        "[workflow]\nruntime_root = 'runtime'\n"
        f"state_file = {json.dumps(str(h.paths.state_file))}\n"
    )
    options: dict[str, object] = {"allow_explicit_model": True}
    if provider == "claude":
        options["permission_mode"] = "auto"
    return AgentSettings(
        provider,
        tuple(command),
        {"standard": "model-s", "deep": "model-o"},
        environment,
        options,
    )


def prepare_workflow(h: Harness) -> tuple[str, dict[str, object], State]:
    backlog = h.root / "docs/dev/project-management/prds/backlog"
    backlog.mkdir(parents=True)
    name = "00001-fixture.md"
    (backlog / name).write_text("# Fixture PRD\n")
    historical = {
        "filename": "00000-prior.md",
        "cycles": 1,
        "autonomous_decisions": 0,
        "escalated_decisions": 0,
        "tasks_completed": 1,
        "tasks_total": 1,
    }

    def prepare(state: State) -> None:
        state["work"]["prd"] = name
        state["batch"]["completed_prds"].append(historical.copy())
        add_capability(state)

    initial = h.store.transaction(prepare)
    return name, historical, initial


def assert_handoff(
    session: Path, phase: str, target: str, historical: dict[str, object], name: str
) -> int:
    raw = rows(session / "raw.jsonl")
    commands = [row for row in raw if row.get("type") == "fake_workflow_command"]
    handoffs = [row for row in raw if row.get("type") == "fake_workflow_handoff"]
    assert len(handoffs) == 1 and handoffs[0]["phase"] == phase
    assert handoffs[0]["result"] == {"phase": target or "done", "next_phase": target}
    verbs = [row["argv"][4:6] for row in commands]
    assert (
        verbs
        == {
            "build": [
                ["state", "show"],
                ["workflow", "select"],
                ["state", "show"],
                ["workflow", "phase-complete"],
            ],
            "review": [["state", "show"], ["workflow", "phase-complete"]],
            "done": [
                ["state", "show"],
                ["workflow", "complete-prd"],
                ["state", "show"],
                ["workflow", "phase-complete"],
            ],
        }[phase]
    )
    # Only the launched phase runs: the sole handoff is the last CLI call.
    before_handoff = commands[-2]["result"]
    assert before_handoff["work"]["phase"] == phase
    assert commands[-1]["argv"][-1] == str(before_handoff["revision"])
    assert handoffs[0]["revision"] == before_handoff["revision"] + 1
    if phase == "done":
        assert commands[0]["result"]["batch"]["completed_prds"] == [historical]
        assert commands[1]["result"]["result"]["filename"] == name
        assert before_handoff["revision"] == commands[0]["result"]["revision"] + 1
        assert [
            item["filename"] for item in before_handoff["batch"]["completed_prds"]
        ] == [historical["filename"], name]
    return handoffs[0]["revision"]


def assert_retained_evidence(
    session: Path, phase: str, target: str, provider: str
) -> None:
    assert rows(session / "normalized.jsonl")
    summary = json.loads((session / "summary.json").read_text())
    assert summary["returncode"] == 0 and summary["timed_out"] is False
    (retained_metric,) = rows(session / "metrics.jsonl")
    assert retained_metric["phase_launched"] == phase
    assert retained_metric["phase_end"] == (target or "done")
    assert retained_metric["finished_at"] is not None
    assert json.loads((session / "meta.json").read_text())["agent"] == provider


def assert_completed_results(final: dict, historical: dict, name: str) -> None:
    assert final["work"]["phase"] == "done" and final["work"]["next_phase"] == ""
    assert final["batch"]["completed_prds"][0] == historical
    assert [item["filename"] for item in final["batch"]["completed_prds"]] == [
        historical["filename"],
        name,
    ]
    assert final["batch"]["capabilities"]["audit"]["status"] == "succeeded"


@pytest.mark.parametrize("provider", ["claude", "codex"])
def test_builtin_fake_command_handoffs_drain_and_retain_completed_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
) -> None:
    h = adapter_harness(tmp_path, monkeypatch)
    agent = workflow_agent(h, tmp_path, provider)
    name, historical, initial = prepare_workflow(h)
    driver = (
        ClaudeDriver(agent, run_id="fake-drain")
        if provider == "claude"
        else CodexDriver(agent, run_id="fake-drain")
    )
    supervisor = Supervisor(
        h.root,
        store=h.store,
        driver=driver,
        settings=h.settings,
        capability_runner=lambda _: h.runner,
        clock=h.clock,
        sleeper=h.waits.append,
    )
    outcome = supervisor.run()
    assert outcome.exit_code == 0 and outcome.decision.kind == DecisionKind.COMPLETE
    assert outcome.sessions_attempted == 3 and len(h.runner.requests) == 1
    metrics = reconcile_metrics(h.paths)
    assert [metric.kind for metric in metrics] == ["phase"] * 3 + ["capability"]
    assert [metric.phase_launched for metric in metrics[:3]] == [
        "build",
        "review",
        "done",
    ]
    assert len({metric.session_id for metric in metrics}) == 4
    assert all(metric.finished_at is not None for metric in metrics)
    revisions = []
    for metric, phase, target in zip(
        metrics[:3],
        ("build", "review", "done"),
        ("review", "done", ""),
        strict=True,
    ):
        session = h.paths.sessions / metric.session_id
        revisions.append(assert_handoff(session, phase, target, historical, name))
        assert_retained_evidence(session, phase, target, provider)
    assert initial["revision"] < revisions[0] < revisions[1] < revisions[2]
    final = h.store.read()
    assert_completed_results(final, historical, name)
    assert (
        json.loads((h.paths.reports / "batch-1-state-final.json").read_text()) == final
    )
