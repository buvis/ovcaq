from __future__ import annotations

import json
import os
import secrets
import sys
import threading
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ovcaq.config import PhaseSettings, RuntimeSettings, SupervisorSettings
from ovcaq.drivers.base import LaunchRequest, LaunchSpec
from ovcaq.events.model import Observation, ObservationType, SessionSummary, Usage
from ovcaq.paths import ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.decision import SupervisorPolicy
from ovcaq.runtime.registry import FleetRegistry, FleetRun
from ovcaq.runtime.session import observe_session_evidence
from ovcaq.runtime.supervisor import Supervisor
from ovcaq.state.schema import State, new_state
from ovcaq.state.store import StateStore
from ovcaq.tui.model import ActivityLane, ProjectObserver, ProjectView


class Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()

    def wait(self, event: threading.Event, timeout: float) -> bool:
        return event.wait(timeout)


@dataclass
class LiveDriver:
    store: StateStore
    settings: RuntimeSettings
    cost: float
    raw_only: bool = False
    name: str = "local"
    requests: list[LaunchRequest] = field(default_factory=list)
    views: list[ProjectView] = field(default_factory=list)
    pending: list[dict[str, object]] = field(default_factory=list)
    metadata: list[dict[str, object]] = field(default_factory=list)
    normalized_sizes: list[int] = field(default_factory=list)
    nonces: list[str] = field(default_factory=list)
    receipts: list[tuple[int, str]] = field(default_factory=list)
    observer: ProjectObserver | None = None

    def default_prompt(self, phase: str) -> str:
        return f"observe {phase}"

    def build_launch(self, request: LaunchRequest) -> LaunchSpec:
        self.requests.append(request)
        release = request.session_dir / "release"
        nonce = secrets.token_hex(16)
        self.nonces.append(nonce)
        receipt = request.session_dir / "child-receipt"
        lines = (
            ["opaque provider bytes", "checkpoint"]
            if self.raw_only
            else ["lane", "usage-first", "usage-latest", "checkpoint"]
        )
        code = (
            "import os, time\nfrom pathlib import Path\n"
            f"Path({str(receipt)!r}).write_text(str(os.getpid()) + ':' + {nonce!r})\n"
            f"for line in {lines!r}: print(line, flush=True)\n"
            f"release = Path({str(release)!r})\n"
            "deadline = time.monotonic() + 8\n"
            "while not release.exists() and time.monotonic() < deadline:\n"
            "    time.sleep(0.01)\n"
            "assert release.exists(), 'observer never released the session'\n"
        )
        return LaunchSpec(
            (sys.executable, "-c", code), dict(os.environ), request.root, "jsonl"
        )

    def decode(self, raw_line: str) -> Iterable[Observation]:
        request = self.requests[-1]
        metadata = json.loads(self.settings.paths.run_metadata.read_text())
        if raw_line.strip() == "checkpoint":
            try:
                self.capture(metadata)
            finally:
                (request.session_dir / "release").touch()
            return ()
        if self.raw_only:
            return ()
        index = len(self.requests)
        kind, payload = ObservationType.LANE_STARTED, {"label": f"Worker {index}"}
        if raw_line.strip().startswith("usage-"):
            kind = ObservationType.USAGE_UPDATED
            amount = 10 if raw_line.strip() == "usage-first" else 20
            usage = Usage(
                amount * index, index, 3 * index, 5 * index, index, self.cost, False
            )
            payload = {"usage": asdict(usage), "identity": f"request-{index}"}
        return (
            Observation(
                1,
                datetime.now(UTC),
                f"provider-{index}",
                metadata["run_id"],
                request.session_dir.name,
                f"lane-{index}",
                kind,
                payload,
            ),
        )

    def capture(self, metadata: dict[str, object]) -> None:
        request = self.requests[-1]
        pid_text, nonce = (request.session_dir / "child-receipt").read_text().split(":")
        pid = int(pid_text)
        assert pid != os.getpid() and nonce == self.nonces[-1]
        assert not (request.session_dir / "release").exists()
        os.kill(pid, 0)
        if self.observer is None:
            (entry,) = FleetRegistry(self.settings.paths.fleet_root).snapshot().live
            run = FleetRun(
                entry.run_id,
                entry.root,
                entry.agent,
                entry.started_at,
                entry.pid,
                entry.process_start,
            )
            self.observer = ProjectObserver(run, self.settings)
        self.pending.append(
            json.loads((request.session_dir / "metrics.jsonl").read_text())
        )
        self.metadata.append(metadata)
        self.normalized_sizes.append(
            (request.session_dir / "normalized.jsonl").stat().st_size
        )
        self.views.append(self.observer.poll())
        os.kill(pid, 0)
        self.receipts.append((pid, nonce))

    def summarize(
        self, observations: Iterable[Observation], exit_code: int
    ) -> SessionSummary:
        assert exit_code == 0
        index = len(self.requests)
        self.store.transaction(self.advance)
        usage = (
            None
            if self.raw_only
            else Usage(20 * index, index, 3 * index, 5 * index, index, self.cost)
        )
        return SessionSummary(
            True, self.requests[-1].session_dir.name, None, None, None, usage
        )

    def advance(self, state: State) -> None:
        if len(self.requests) == 1 and not self.raw_only:
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
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[StateStore, SupervisorSettings]:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    root = tmp_path / "repo"
    root.mkdir()
    (root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner"]\n'
        'tiers = { sonnet = "model-s", opus = "model-o" }\n'
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


def run_live(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cost: float,
    *,
    raw_only: bool = False,
) -> LiveDriver:
    store, settings = live_settings(tmp_path, monkeypatch)
    driver = LiveDriver(store, settings.runtime, cost, raw_only)
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


def assert_child_receipts(driver: LiveDriver) -> None:
    assert len(driver.receipts) == len(driver.requests)
    assert len(set(driver.nonces)) == len(driver.requests)
    for request, nonce, (pid, captured_nonce) in zip(
        driver.requests, driver.nonces, driver.receipts, strict=True
    ):
        assert pid != os.getpid() and captured_nonce == nonce
        assert (request.session_dir / "child-receipt").read_text() == f"{pid}:{nonce}"


def assert_session_identities(driver: LiveDriver) -> None:
    first, second = driver.views
    assert driver.pending[0]["finished_at"] is driver.pending[1]["finished_at"] is None
    assert first.run.run_id == second.run.run_id == driver.metadata[0]["run_id"]
    assert driver.metadata[1]["run_id"] == first.run.run_id
    assert driver.pending[0]["session_id"] != driver.pending[1]["session_id"]
    for request, pending in zip(driver.requests, driver.pending, strict=True):
        assert pending["session_id"] == request.session_dir.name
        records = [
            json.loads(line)
            for line in (request.session_dir / "normalized.jsonl")
            .read_text()
            .splitlines()
        ]
        assert records and {row["run_id"] for row in records} == {first.run.run_id}
        assert {row["session_id"] for row in records} == {request.session_dir.name}


def test_real_supervisor_streams_live_cumulative_usage_and_follows_session_rollover(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cost = 0.125
    driver = run_live(tmp_path, monkeypatch, cost)
    assert_child_receipts(driver)
    assert_session_identities(driver)
    first, second = driver.views
    assert (first.phase, first.next_phase) == ("build", "build")
    assert (second.phase, second.next_phase) == ("review", "review")
    assert first.provider == "provider-1"
    assert second.provider == "provider-2"
    assert first.lanes == (ActivityLane("lane-1", "Worker 1", "running", None),)
    assert second.lanes == (ActivityLane("lane-2", "Worker 2", "running", None),)
    assert first.usage is not None and first.usage.input_tokens == 20
    assert first.usage.output_tokens == first.usage.tool_uses == 1
    assert second.usage is not None and second.usage.input_tokens == 60
    assert second.usage.output_tokens == second.usage.tool_uses == 3
    assert first.usage.cost_usd == cost
    assert second.usage.cost_usd == 2 * cost
    assert first.usage.partial and second.usage.partial
    assert first.usage.cache_creation_input_tokens == 3
    assert first.usage.cache_read_input_tokens == 5
    assert second.usage.cache_creation_input_tokens == 9
    assert second.usage.cache_read_input_tokens == 15
    assert first.usage.estimated is second.usage.estimated is False


def test_real_supervisor_preserves_raw_bytes_when_precreated_normalization_is_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    driver = run_live(tmp_path, monkeypatch, 0.0, raw_only=True)
    assert_child_receipts(driver)
    (view,) = driver.views
    (request,) = driver.requests
    assert view.telemetry == "raw-only"
    assert view.provider == "unknown" and view.lanes == () and view.usage is None
    assert driver.pending[0]["finished_at"] is None
    assert driver.normalized_sizes == [0]
    evidence = observe_session_evidence(driver.settings.paths, request.session_dir.name)
    assert evidence.raw
    assert (
        request.session_dir / "raw.jsonl"
    ).read_bytes() == b"opaque provider bytes\ncheckpoint\n"
