from __future__ import annotations

import json
import os
import sys
import threading
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ovcaq.config import (
    AgentSettings,
    PhaseSettings,
    RuntimeSettings,
    SupervisorSettings,
)
from ovcaq.drivers.base import LaunchRequest, LaunchSpec
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.events.model import Observation, SessionSummary
from ovcaq.paths import ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.decision import SupervisorPolicy
from ovcaq.runtime.registry import FleetRegistry, FleetRun
from ovcaq.runtime.session import observe_session_evidence
from ovcaq.runtime.supervisor import Supervisor
from ovcaq.state.schema import State, new_state
from ovcaq.state.store import StateStore
from ovcaq.tui.model import ProjectObserver, ProjectView


class Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()

    def wait(self, event: threading.Event, timeout: float) -> bool:
        return event.wait(timeout)


@dataclass
class LiveCapture:
    request: LaunchRequest
    metadata: dict[str, object]
    metric: dict[str, object]
    records: list[dict[str, object]]
    raw: bytes
    view: ProjectView


def native_usage(index: int) -> dict[str, int]:
    return {
        "input_tokens": 10 * index,
        "output_tokens": 4 * index,
        "cache_creation_input_tokens": 2 * index,
        "cache_read_input_tokens": 3 * index,
    }


def native_lifecycle_rows(index: int, session_id: str) -> list[dict[str, object]]:
    return [
        {
            "type": "system",
            "subtype": "init",
            "session_id": session_id,
            "model": f"native-model-{index}",
        },
        {
            "type": "system",
            "subtype": "task_started",
            "session_id": session_id,
            "task_id": f"native-lane-{index}",
            "description": f"Native worker {index}",
            "task_type": "local_agent",
        },
        {
            "type": "system",
            "subtype": "task_progress",
            "session_id": session_id,
            "task_id": f"native-lane-{index}",
            "description": f"Native worker {index}",
            "last_tool_name": "Read",
            "usage": {
                "tool_uses": index,
                "total_tokens": 14 * index,
                "duration_ms": 40,
            },
        },
    ]


def native_activity_row(index: int, session_id: str) -> dict[str, object]:
    return {
        "type": "assistant",
        "session_id": session_id,
        "parent_tool_use_id": f"native-lane-{index}",
        "message": {
            "id": f"message-{index}",
            "content": [
                {"type": "text", "text": "working"},
                {
                    "type": "tool_use",
                    "id": f"tool-{index}",
                    "name": "Read",
                    "input": {"file_path": "/sanitized/example"},
                },
            ],
            "usage": native_usage(index),
        },
    }


def native_result_row(index: int, session_id: str) -> dict[str, object]:
    return {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "session_id": session_id,
        "result": "done",
        "total_cost_usd": 0.25 * index,
        "usage": native_usage(index),
    }


def native_session_payload(index: int) -> bytes:
    session_id = f"native-session-{index}"
    rows = [
        *native_lifecycle_rows(index, session_id),
        native_activity_row(index, session_id),
        native_result_row(index, session_id),
        {"type": "test_checkpoint"},
    ]
    return b"".join(
        json.dumps(row, separators=(",", ":")).encode() + b"\n" for row in rows
    )


def child_code(payload: bytes, release: Path) -> str:
    return (
        "import sys, time\nfrom pathlib import Path\n"
        f"sys.stdout.buffer.write({payload!r}); sys.stdout.buffer.flush()\n"
        f"release = Path({str(release)!r})\n"
        "deadline = time.monotonic() + 8\n"
        "while not release.exists() and time.monotonic() < deadline:\n"
        "    time.sleep(0.01)\n"
        "assert release.exists(), 'observer never released the session'\n"
    )


@dataclass(init=False)
class LiveClaudeDriver(ClaudeDriver):
    store: StateStore
    runtime: RuntimeSettings
    requests: list[LaunchRequest] = field(default_factory=list)
    payloads: list[bytes] = field(default_factory=list)
    captures: list[LiveCapture] = field(default_factory=list)
    observer: ProjectObserver | None = None

    def __init__(self, store: StateStore, runtime: RuntimeSettings) -> None:
        settings = AgentSettings(
            "claude",
            (sys.executable,),
            {"sonnet": "fixture-model"},
            {},
            {"permission_mode": "auto"},
        )
        super().__init__(settings, run_id="adapter-owned-run")
        self.store = store
        self.runtime = runtime
        self.requests = []
        self.payloads = []
        self.captures = []
        self.observer = None

    def build_launch(self, request: LaunchRequest) -> LaunchSpec:
        self.requests.append(request)
        index = len(self.requests)
        payload = native_session_payload(index)
        self.payloads.append(payload)
        release = request.session_dir / "release"
        return LaunchSpec(
            (sys.executable, "-c", child_code(payload, release)),
            dict(os.environ),
            request.root,
            "jsonl",
        )

    def decode(self, raw_line: str) -> tuple[Observation, ...]:
        if json.loads(raw_line).get("type") == "test_checkpoint":
            try:
                self.capture()
            finally:
                (self.requests[-1].session_dir / "release").touch()
            return ()
        return super().decode(raw_line)

    def capture(self) -> None:
        request = self.requests[-1]
        metadata = json.loads(self.runtime.paths.run_metadata.read_text())
        if self.observer is None:
            (entry,) = FleetRegistry(self.runtime.paths.fleet_root).snapshot().live
            run = FleetRun(
                entry.run_id,
                entry.root,
                entry.agent,
                entry.started_at,
                entry.pid,
                entry.process_start,
            )
            self.observer = ProjectObserver(run, self.runtime)
        normalized = request.session_dir / "normalized.jsonl"
        records = [json.loads(line) for line in normalized.read_text().splitlines()]
        baseline = self.observer.poll()
        lane = next(row for row in records if row["type"] == "lane.started")
        foreign_rows = []
        for index, changes in enumerate(
            (
                {"run_id": "foreign-run"},
                {"session_id": "foreign-session"},
                {"run_id": "foreign-run", "session_id": "foreign-session"},
            ),
            1,
        ):
            foreign = dict(
                lane, provider=f"foreign-{index}", lane_id=f"foreign-{index}"
            )
            foreign.update(changes)
            foreign_rows.append(json.dumps(foreign, separators=(",", ":")))
        with normalized.open("a") as stream:
            stream.write("\n".join(foreign_rows) + "\n")
        filtered = self.observer.poll()
        assert filtered.provider == baseline.provider
        assert filtered.lanes == baseline.lanes
        self.captures.append(
            LiveCapture(
                request,
                metadata,
                json.loads((request.session_dir / "metrics.jsonl").read_text()),
                records,
                (request.session_dir / "raw.jsonl").read_bytes(),
                filtered,
            )
        )

    def summarize(
        self, observations: Iterable[Observation], exit_code: int
    ) -> SessionSummary:
        summary = super().summarize(observations, exit_code)
        assert summary.usage is not None
        self.store.transaction(self.advance)
        return summary

    def advance(self, state: State) -> None:
        if len(self.requests) == 1:
            state["work"].update(phase="review", next_phase="review")
        else:
            state["work"].update(phase="done", next_phase="")
            state["batch"]["completed_prds"].append(
                {
                    "filename": "finished.md",
                    "cycles": 1,
                    "autonomous_decisions": 0,
                    "escalated_decisions": 0,
                    "tasks_completed": 1,
                    "tasks_total": 1,
                }
            )


def live_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[StateStore, SupervisorSettings]:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    root = tmp_path / "repo"
    root.mkdir()
    (root / "ovcaq.toml").write_text(
        'agent = "claude"\n[agents.claude]\ncommand = ["runner"]\n'
        'tiers = { sonnet = "fixture-model" }\n'
    )
    paths = ensure_runtime_layout(
        resolve_runtime_paths(
            root,
            runtime_root=root / "custom-runtime",
            xdg_state_home=tmp_path / "state-home",
        )
    )
    store = StateStore(paths.state_file)
    state = new_state(repo_root=root)
    state["batch"].update(id="batch-1", status="running")
    state["work"].update(phase="build", next_phase="build")
    store.initialize(state)
    runtime = RuntimeSettings(paths, 0.05, 1_000_000, 10_000_000, 0)
    settings = SupervisorSettings(
        runtime,
        SupervisorPolicy(1, 2, 2, 0.25, 5.0, 3),
        {
            phase: PhaseSettings("sonnet", "high", 10)
            for phase in ("build", "review", "done")
        },
    )
    return store, settings


def run_live_claude(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> LiveClaudeDriver:
    store, settings = live_settings(tmp_path, monkeypatch)
    driver = LiveClaudeDriver(store, settings.runtime)
    supervisor = Supervisor(
        settings.runtime.paths.project_root,
        store=store,
        driver=driver,
        settings=settings,
        capability_runner=lambda _: None,
        clock=Clock(),
        sleeper=lambda _: None,
    )
    try:
        outcome = supervisor.run()
        assert outcome.exit_code == 0
    finally:
        if driver.observer is not None:
            driver.observer.close()
    return driver


def test_real_claude_telemetry_binds_native_ids_to_owning_supervisor_sessions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = run_live_claude(tmp_path, monkeypatch)
    assert len(driver.captures) == len(driver.requests) == 2
    run_ids = {capture.metadata["run_id"] for capture in driver.captures}
    assert len(run_ids) == 1 and "adapter-owned-run" not in run_ids
    for index, capture in enumerate(driver.captures, 1):
        supervisor_session = capture.request.session_dir.name
        assert capture.metric["session_id"] == supervisor_session
        assert capture.metric["model"] == "fixture-model"
        final_metric = json.loads(
            (capture.request.session_dir / "metrics.jsonl").read_text()
        )
        assert final_metric["model"] == "fixture-model"
        assert {row["run_id"] for row in capture.records} == run_ids
        assert {row["session_id"] for row in capture.records} == {supervisor_session}
        assert capture.raw == driver.payloads[index - 1]
        assert f'"session_id":"native-session-{index}"'.encode() in capture.raw
        assert capture.view.provider == "claude"
        assert len(capture.view.lanes) == 1
        (lane,) = capture.view.lanes
        assert (lane.lane_id, lane.label, lane.status) == (
            f"native-lane-{index}",
            f"Native worker {index}",
            "running",
        )
        assert capture.view.usage is not None
        assert capture.view.usage.input_tokens >= 10 * index
        assert capture.view.usage.output_tokens >= 4 * index
        normalized = capture.request.session_dir / "normalized.jsonl"
        text = normalized.read_text()
        assert "foreign-run" in text and "foreign-session" in text
        assert all("foreign" not in lane.lane_id for lane in capture.view.lanes)


@pytest.mark.parametrize(
    ("raw", "normalized", "expected"),
    [
        (None, None, (False, False, False, False)),
        (b"", None, (True, False, False, False)),
        (b"native\n", None, (True, False, False, True)),
        (b"native\n", b"", (True, True, False, True)),
        (b"native\n", b"{}\n", (True, True, False, False)),
    ],
    ids=["absent", "empty-raw", "raw-only", "empty-normalized", "normalized"],
)
def test_evidence_presence_distinguishes_empty_normalized_from_raw_only_content(
    tmp_path: Path,
    raw: bytes | None,
    normalized: bytes | None,
    expected: tuple[bool, bool, bool, bool],
) -> None:
    paths = ensure_runtime_layout(
        resolve_runtime_paths(tmp_path, runtime_root=tmp_path / "runtime")
    )
    session = paths.sessions / "session-1"
    session.mkdir()
    if raw is not None:
        (session / "raw.jsonl").write_bytes(raw)
    if normalized is not None:
        (session / "normalized.jsonl").write_bytes(normalized)
    evidence = observe_session_evidence(paths, session.name)
    assert (evidence.raw, evidence.normalized, evidence.summary, evidence.raw_only) == (
        expected
    )
