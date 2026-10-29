"""Project adapter and fixture-supervisor evidence through the shared TUI."""

from __future__ import annotations

import json
import sys
import threading
import time
from dataclasses import replace
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from ovcaq.config import (
    AgentSettings,
    PhaseSettings,
    RuntimeSettings,
    SupervisorSettings,
)
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import ObservationType, observation_from_record
from ovcaq.events.tail import TailBatch
from ovcaq.paths import ensure_runtime_layout, resolve_runtime_paths, state_path
from ovcaq.runtime.decision import SupervisorPolicy
from ovcaq.runtime.session import MetricsSnapshot, reconcile_metrics
from ovcaq.runtime.supervisor import Supervisor
from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore
from ovcaq.tui import model
from ovcaq.tui.panels import activity_panel, plain_frame, workflow_panel

from . import test_model
from .model_support import Projection

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/codex/v1"
projection = test_model.projection


class Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()

    def wait(self, event: threading.Event, timeout: float) -> bool:
        return event.wait(timeout)


def _render(renderable: object) -> str:
    stream = StringIO()
    Console(file=stream, width=240, color_system=None, force_terminal=False).print(
        renderable
    )
    return stream.getvalue()


def _driver(scenario: str = "healthy") -> CodexDriver:
    return CodexDriver(
        AgentSettings(
            "codex",
            (sys.executable, str(FIXTURES / "fake_codex.py")),
            {"standard": "model-s", "deep": "model-o"},
            {
                "OVCAQ_FAKE_SCENARIO": scenario,
                "OVCAQ_FAKE_CLI": str(Path(sys.executable).with_name("ovcaq")),
            },
            {},
        ),
        run_id="run-1",
    )


def _feed(projection: Projection, records: tuple) -> model.ProjectView:
    session = next(event.session_id for event in records if event.session_id)
    projection.observation = replace(projection.observation, active_session_id=session)
    projection.batches.append(TailBatch(records, (), False, False, True))
    return projection.poll()


def _decode(name: str, *, exact: bool = False) -> tuple:
    driver = _driver()
    observations = []
    for line in (FIXTURES / f"{name}.jsonl").read_text().splitlines():
        record = json.loads(line)
        if exact and record.get("type") == "turn.completed":
            record["usage"]["cache_write_input_tokens"] = 0
        observations.extend(driver.decode(json.dumps(record)))
    return tuple(observations)


@pytest.mark.parametrize("exact", [False, True])
def test_adapter_usage_projection_labels_unknown_cost(
    projection: Projection,
    exact: bool,
) -> None:
    view = _feed(projection, _decode("healthy", exact=exact))
    assert view.provider == "codex"
    assert view.usage is not None
    assert view.usage.input_tokens == (80 if exact else None)
    assert view.usage.output_tokens == 25
    assert view.usage.cache_creation_input_tokens == (0 if exact else 5)
    assert view.usage.cache_read_input_tokens == 20
    assert view.usage.cost_usd is None
    assert view.usage.estimated is not exact
    rendered = _render(workflow_panel(view))
    assert "provider: codex" in rendered and "cost unknown" in rendered
    assert ("(estimated)" in rendered) is not exact
    assert f"in {'80' if exact else 'unknown'}, out 25" in rendered


def test_adapter_matched_receiver_lane_is_visible(projection: Projection) -> None:
    records = _decode("lanes-matched")
    assert any(event.type == ObservationType.LANE_STARTED for event in records)
    view = _feed(projection, records)
    assert view.provider == "codex"
    assert [(lane.lane_id, lane.label, lane.status) for lane in view.lanes] == [
        ("example-child", "Receiver", "running")
    ]
    assert "Receiver: running" in _render(activity_panel(view))
    assert view.usage is not None and view.usage.cost_usd is None


def test_adapter_mismatched_lanes_remain_unknown(projection: Projection) -> None:
    records = _decode("lanes")
    assert any(event.type == ObservationType.RAW_UNKNOWN for event in records)
    assert not any(event.lane_id for event in records)
    view = _feed(projection, records)
    assert view.provider == "codex" and view.lanes == ()
    assert view.usage is not None
    assert view.usage.input_tokens is None and view.usage.output_tokens is None
    rendered = _render(plain_frame(view))
    assert "no lanes observed" in rendered and "cost unknown" in rendered
    assert "in unknown, out unknown" in rendered


def test_unknown_fixture_stream_is_raw_only(projection: Projection) -> None:
    driver = _driver()
    tuple(driver.decode((FIXTURES / "healthy.jsonl").read_text().splitlines()[0]))
    records = tuple(
        event
        for line in (FIXTURES / "malformed.jsonl").read_text().splitlines()
        if '"future.event"' in line or '"future_item"' in line
        for event in driver.decode(line)
    )
    assert records and all(
        event.type == ObservationType.RAW_UNKNOWN for event in records
    )
    view = _feed(projection, records)
    assert view.provider == "codex" and view.telemetry == "raw-only"
    assert view.usage is None and view.lanes == ()
    rendered = _render(plain_frame(view))
    assert "telemetry: raw-only" in rendered and "usage: unknown" in rendered


def _supervisor(root: Path, monkeypatch: pytest.MonkeyPatch, scenario: str):
    for name in ("HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME"):
        monkeypatch.setenv(name, str(root / name.lower()))
    (root / "ovcaq.toml").write_text(
        'agent = "codex"\n[agents.codex]\n'
        f"command = {json.dumps([sys.executable, str(FIXTURES / 'fake_codex.py')])}\n"
        'tiers = { standard = "model-s", deep = "model-o" }\n'
    )
    paths = ensure_runtime_layout(
        resolve_runtime_paths(root, xdg_state_home=root / "xdg")
    )
    assert paths.state_file == state_path(root)
    store = StateStore(paths.state_file)
    state = new_state(repo_root=root)
    state["batch"].update(id="batch-1", status="running")
    state["work"]["prd"] = "00001-fixture.md"
    store.initialize(state)
    backlog = root / "docs/dev/project-management/prds/backlog"
    backlog.mkdir(parents=True, exist_ok=True)
    (backlog / "00001-fixture.md").write_text("# Fixture PRD\n")
    settings = SupervisorSettings(
        RuntimeSettings(paths, 0.05, 1_000_000, 10_000_000, 0),
        SupervisorPolicy(0, 0, 0, 0.01, 0.01, 3),
        {
            phase: PhaseSettings("standard", "medium", 10)
            for phase in ("build", "review", "done")
        },
    )
    supervisor = Supervisor(
        root,
        store=store,
        driver=_driver(scenario),
        settings=settings,
        capability_runner=lambda _: pytest.fail("unexpected capability"),
        clock=Clock(),
        sleeper=lambda _: None,
    )
    return supervisor, store, paths


def _project_bundle(request: pytest.FixtureRequest, state, paths) -> tuple:
    metrics = reconcile_metrics(paths)
    metric = metrics[-1]
    bundle = paths.sessions / metric.session_id
    records = tuple(
        observation_from_record(json.loads(line))
        for line in (bundle / "normalized.jsonl").read_text().splitlines()
    )
    harness = request.getfixturevalue("projection")
    harness.state = state
    harness.metrics = MetricsSnapshot(metrics, True, ())
    harness.registry.remove(harness.run.run_id, expected=harness.entry)
    harness.entry = replace(harness.entry, run_id=metric.run_id, agent="codex")
    harness.registry.publish(harness.entry)
    harness.run = replace(harness.run, run_id=metric.run_id, agent="codex")
    harness.observer.close()
    harness.observer = model.ProjectObserver(harness.run, harness.settings)
    return _feed(harness, records), records, bundle, metrics


@pytest.mark.parametrize(
    "scenario",
    [
        "healthy",
        "noisy-success",
        "tool-active",
        "lanes",
        "lanes-matched",
        "malformed",
    ],
)
def test_fake_supervisor_evidence_drives_panels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
    scenario: str,
) -> None:
    supervisor, store, paths = _supervisor(tmp_path, monkeypatch, scenario)
    result = supervisor.run_once()
    state = store.read()
    view, records, bundle, metrics = _project_bundle(request, state, paths)
    assert view.provider == "codex" and view.run.agent == "codex"
    assert len(metrics) == 1 and metrics[0].usage is not None
    assert metrics[0].usage["cost_usd"] is None
    assert view.usage is not None and view.usage.cost_usd is None
    assert any(event.type == ObservationType.RAW_UNKNOWN for event in records)
    assert "fake_invocation" in (bundle / "raw.jsonl").read_text()
    assert view.revision == state["revision"] and result.state_error is None
    rendered = _render(plain_frame(view))
    assert "provider: codex" in rendered and "cost unknown" in rendered
    if scenario == "tool-active":
        assert any(event.type == ObservationType.TOOL_STARTED for event in records)
        assert view.usage.tool_uses == metrics[0].usage["tool_uses"]
        assert view.usage.output_tokens == 25
    if scenario == "lanes":
        assert view.lanes == () and view.usage.input_tokens is None
        assert "no lanes observed" in rendered
    if scenario == "lanes-matched":
        assert any(event.type == ObservationType.LANE_STARTED for event in records)
        assert [(lane.lane_id, lane.label, lane.status) for lane in view.lanes] == [
            ("example-child", "Receiver", "running")
        ]
        assert "Receiver: running" in rendered
        assert "Receiver: running" in _render(activity_panel(view))
    if scenario == "noisy-success":
        assert result.summary.success and view.usage.input_tokens == 80
        assert not view.usage.estimated and "(estimated)" not in rendered
    if scenario in ("healthy", "tool-active"):
        assert view.usage.estimated and "(estimated)" in rendered


def test_fake_workflow_done_projects_committed_current_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    supervisor, store, paths = _supervisor(tmp_path, monkeypatch, "workflow")
    revisions = []
    for phase in ("build", "review", "done"):
        result = supervisor.run_once()
        assert result.summary.success and result.state_error is None
        committed = store.read()
        revisions.append(committed["revision"])
    assert revisions == sorted(set(revisions))
    assert committed["batch"]["completed_prds"][0]["filename"] == "00001-fixture.md"
    view, records, bundle, metrics = _project_bundle(request, committed, paths)
    assert [metric.phase_launched for metric in metrics] == ["build", "review", "done"]
    assert view.phase == "done" and view.revision == revisions[-1]
    assert view.provider == "codex" and view.usage.cost_usd is None
    raw = (bundle / "raw.jsonl").read_text()
    assert '"complete-prd"' in raw and '"phase":"done"' in raw
    assert any(event.type == ObservationType.SESSION_COMPLETED for event in records)
    assert "provider: codex" in _render(plain_frame(view))
