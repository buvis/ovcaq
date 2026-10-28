from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterable, Mapping
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
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import Observation, SessionSummary
from ovcaq.paths import RuntimePaths, ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.decision import DecisionKind, SupervisorPolicy
from ovcaq.runtime.registry import (
    DuplicateRunError,
    FleetRegistry,
    ProcessIdentity,
    RunLock,
    process_identity,
    process_matches,
)
from ovcaq.runtime.session import reconcile_metrics
from ovcaq.runtime.supervisor import Supervisor
from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore


@dataclass
class Step:
    code: str


@dataclass
class ProcessDriver:
    name: str = "claude"
    environment: dict[str, str] = field(default_factory=dict)
    adapter: ClaudeDriver | CodexDriver | None = None
    steps: list[Step] = field(default_factory=list)
    requests: list[LaunchRequest] = field(default_factory=list)
    on_line: Callable[[str], None] | None = None
    default_tiers: Mapping[str, str] = field(default_factory=dict)

    def default_prompt(self, phase: str) -> str:
        assert self.adapter is not None
        return self.adapter.default_prompt(phase)

    def probe(self) -> object:
        raise AssertionError("a configured process fixture needs no network probe")

    def build_launch(self, request: LaunchRequest) -> LaunchSpec:
        assert len(self.requests) < len(self.steps), "unexpected extra launch"
        code = self.steps[len(self.requests)].code
        self.requests.append(request)
        driver_type = ClaudeDriver if self.name == "claude" else CodexDriver
        self.adapter = driver_type(
            AgentSettings(
                name=self.name,
                command=(sys.executable, "-c", code),
                tiers={
                    "sonnet": "model-s",
                    "opus": "model-o",
                    "model-s": "model-s",
                    "model-o": "model-o",
                },
                environment=self.environment,
                options={"permission_mode": "auto"} if self.name == "claude" else {},
            ),
            run_id="process-conformance",
        )
        return self.adapter.build_launch(request)

    def decode(self, raw_line: str) -> Iterable[Observation]:
        if self.on_line is not None:
            self.on_line(raw_line)
        assert self.adapter is not None
        return self.adapter.decode(raw_line)

    def summarize(
        self, observations: Iterable[Observation], exit_code: int
    ) -> SessionSummary:
        assert self.adapter is not None
        return self.adapter.summarize(observations, exit_code)


class ProcessClock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()

    def wait(self, event: threading.Event, timeout: float) -> bool:
        return event.wait(timeout)


@dataclass
class Harness:
    root: Path
    paths: RuntimePaths
    store: StateStore
    driver: ProcessDriver
    settings: SupervisorSettings

    def supervisor(self) -> Supervisor:
        def unexpected_capability(entry: object) -> object:
            raise AssertionError("process fixture has no capabilities")

        return Supervisor(
            self.root,
            store=self.store,
            driver=self.driver,
            settings=self.settings,
            capability_runner=unexpected_capability,
            clock=ProcessClock(),
            sleeper=time.sleep,
        )


def process_driver(tmp_path: Path, adapter: str) -> ProcessDriver:
    return ProcessDriver(
        name=adapter,
        environment={
            "HOME": str(tmp_path / "home"),
            "XDG_CONFIG_HOME": str(tmp_path / "user-config"),
            "XDG_STATE_HOME": str(tmp_path / "state-home"),
        },
        adapter=(ClaudeDriver if adapter == "claude" else CodexDriver)(
            AgentSettings(
                name=adapter,
                command=(sys.executable,),
                tiers={},
                environment={},
                options={"permission_mode": "auto"} if adapter == "claude" else {},
            ),
            run_id="process-conformance",
        ),
    )


def harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, adapter: str) -> Harness:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
    root = tmp_path / "repo"
    root.mkdir()
    (root / "ovcaq.toml").write_text(
        f'agent = "{adapter}"\n[agents.{adapter}]\ncommand = ["runner"]\n'
        'tiers = { sonnet = "model-s", opus = "model-o" }\n'
        "[phases.build]\ntimeout_seconds = 3\n"
    )
    paths = ensure_runtime_layout(
        resolve_runtime_paths(
            root, runtime_root=root / "runtime", xdg_state_home=tmp_path / "state-home"
        )
    )
    store = StateStore(paths.state_file)
    state = new_state(repo_root=root)
    state["batch"].update(id="batch-1", status="running")
    state["work"].update(phase="build", next_phase="build")
    store.initialize(state)
    settings = SupervisorSettings(
        RuntimeSettings(paths, 0.05, 1_000_000, 10_000_000, 0),
        SupervisorPolicy(1, 2, 2, 0.25, 5.0, 3),
        {
            phase: PhaseSettings(tier, "high", 3)
            for phase, tier in (
                ("build", "sonnet"),
                ("review", "opus"),
                ("done", "sonnet"),
            )
        },
    )
    return Harness(
        root,
        paths,
        store,
        process_driver(tmp_path, adapter),
        settings,
    )


@pytest.fixture(params=["claude", "codex"])
def adapter(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(autouse=True)
def unrelated_process(tmp_path: Path):
    sentinel = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env={"HOME": str(tmp_path / "sentinel-home")},
    )
    try:
        yield sentinel
        assert sentinel.poll() is None
    finally:
        sentinel.terminate()
        sentinel.wait(timeout=5)


def rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


GROUP_CODE = """
import json, os, signal, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
child = os.fork()
if child == 0:
    time.sleep(15)
    os._exit(0)
print(json.dumps({'parent': os.getpid(), 'child': child}), flush=True)
time.sleep(15)
"""


def stopped(pid: int) -> bool:
    return process_identity(pid) is None


def assert_stopped(identities: list[ProcessIdentity]) -> None:
    assert len(identities) == 2
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if all(stopped(identity.pid) for identity in identities):
            return
        time.sleep(0.02)
    assert all(stopped(identity.pid) for identity in identities)


def clean_survivors(identities: list[ProcessIdentity]) -> None:
    for identity in identities:
        if process_matches(identity):
            try:
                os.kill(identity.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def capture_ownership(h: Harness, identities: list[ProcessIdentity], line: str) -> None:
    for pid in json.loads(line).values():
        identity = process_identity(pid)
        assert identity is not None
        identities.append(identity)
    assert h.paths.run_metadata.is_file()
    registry = FleetRegistry(h.paths.fleet_root).snapshot()
    assert len(registry.live) == 1
    assert not registry.malformed and not registry.stale


def assert_fleet_empty(h: Harness) -> None:
    registry = FleetRegistry(h.paths.fleet_root).snapshot()
    assert not registry.live
    assert not registry.malformed
    assert not registry.stale


def test_watchdog_times_out_and_kills_the_whole_owned_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    adapter: str,
) -> None:
    h = harness(tmp_path, monkeypatch, adapter)
    h.driver.steps = [Step(code=GROUP_CODE), Step(code=GROUP_CODE)]
    identities: list[ProcessIdentity] = []
    h.driver.on_line = lambda line: capture_ownership(h, identities, line)
    started = time.monotonic()
    try:
        outcome = h.supervisor().run()
        assert outcome.exit_code == 1 and outcome.decision.kind == DecisionKind.HALT
        assert time.monotonic() - started < 12
        assert_stopped(identities[:2])
        if len(identities) == 4:
            assert_stopped(identities[2:])
        assert 1 <= outcome.sessions_attempted <= 2
        for request in h.driver.requests:
            summary = json.loads((request.session_dir / "summary.json").read_text())
            assert summary["timed_out"] is True
            assert summary["signal"] == signal.SIGKILL
            assert summary["returncode"] == -signal.SIGKILL
            assert summary["detail"] == "session timed out"
        assert len(reconcile_metrics(h.paths)) == outcome.sessions_attempted
        assert not h.paths.run_metadata.exists()
        assert_fleet_empty(h)
    finally:
        clean_survivors(identities)


@pytest.mark.parametrize("number", [signal.SIGINT, signal.SIGTERM, signal.SIGHUP])
def test_signal_returns_shell_exit_and_finalizes_evidence_after_group_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    adapter: str,
    number: signal.Signals,
) -> None:
    h = harness(tmp_path, monkeypatch, adapter)
    h.driver.steps = [Step(code=GROUP_CODE)]
    identities: list[ProcessIdentity] = []
    timers: list[threading.Timer] = []

    def observed(line: str) -> None:
        capture_ownership(h, identities, line)
        timer = threading.Timer(0.05, os.kill, args=(os.getpid(), number))
        timers.append(timer)
        timer.start()

    h.driver.on_line = observed
    try:
        outcome = h.supervisor().run()
        assert outcome.exit_code == 128 + number and outcome.sessions_attempted == 1
        assert_stopped(identities)
        (request,) = h.driver.requests
        assert rows(request.session_dir / "raw.jsonl")
        summary = json.loads((request.session_dir / "summary.json").read_text())
        assert summary["timed_out"] is False
        assert summary["signal"] == signal.SIGKILL
        assert summary["returncode"] == -signal.SIGKILL
        assert summary["detail"] == "supervisor signal"
        (metric,) = reconcile_metrics(h.paths)
        assert metric.finished_at is not None and metric.decision is not None
        assert not h.paths.run_metadata.exists()
        assert_fleet_empty(h)
    finally:
        for timer in timers:
            timer.cancel()
            timer.join(timeout=1)
        clean_survivors(identities)


def test_duplicate_run_ownership_is_refused_without_launch_or_owner_removal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    adapter: str,
) -> None:
    h = harness(tmp_path, monkeypatch, adapter)
    with RunLock.acquire(h.paths.run_lock):
        with pytest.raises(DuplicateRunError):
            h.supervisor().run()
        assert h.driver.requests == []
        assert not h.paths.run_metadata.exists()
        assert_fleet_empty(h)
        with pytest.raises(DuplicateRunError), RunLock.acquire(h.paths.run_lock):
            pytest.fail("duplicate run released another owner's lock")
    with RunLock.acquire(h.paths.run_lock):
        assert h.driver.requests == []
