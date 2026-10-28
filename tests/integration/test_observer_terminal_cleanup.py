"""Selected supervisor death between polls must preserve its final observation."""

from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ovcaq.config import PhaseSettings, RuntimeSettings, SupervisorSettings
from ovcaq.drivers.base import LaunchRequest, LaunchSpec
from ovcaq.events.model import (
    FailureClass,
    Observation,
    ObservationType,
    SessionSummary,
    Usage,
)
from ovcaq.paths import ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.capability import CapabilityExecution, CapabilityRequest
from ovcaq.runtime.decision import SupervisorPolicy
from ovcaq.runtime.registry import FleetRegistry, FleetRun, process_identity
from ovcaq.runtime.session import observe_metrics
from ovcaq.runtime.supervisor import Supervisor
from ovcaq.state.schema import State, new_state
from ovcaq.state.store import StateStore
from ovcaq.tui.app import AttachResult
from ovcaq.tui.model import ActivityLane, ProjectObserver, ProjectView, UsageView

STAMP = "2026-10-03T12:00:00Z"
OUTCOMES = [
    ("completed", AttachResult("completed", 0)),
    ("paused", AttachResult("detached", 0)),
    ("stopped", AttachResult("detached", 0)),
    ("halted", AttachResult("failed", 1)),
    ("attention", AttachResult("failed", 1)),
]
SELECTED_USAGE = Usage(137, 29, 11, 17, 3, 0.3125, True)


class Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()

    def wait(self, event: threading.Event, timeout: float) -> bool:
        return event.wait(timeout)


class BoundedObserver(ProjectObserver):
    """Keep a broken viewer from polling forever, while using real observations."""

    polls = 0

    def poll(self) -> ProjectView:
        self.polls += 1
        if self.polls > 60:
            pytest.fail("viewer continued polling an ended selection")
        return super().poll()


def settings_for(base: Path) -> SupervisorSettings:
    paths = ensure_runtime_layout(
        resolve_runtime_paths(
            base / "repo",
            runtime_root=base / "repo/runtime",
            xdg_state_home=base / "state-home",
        )
    )
    return SupervisorSettings(
        RuntimeSettings(paths, 0.05, 1_000_000, 10_000_000, 0),
        SupervisorPolicy(1, 2, 2, 0.01, 1.0, 3),
        {
            phase: PhaseSettings("sonnet", "high", 20)
            for phase in ("build", "review", "done")
        },
    )


def seed(
    root: Path,
    *,
    replacement: bool = False,
    prd: str | None = None,
    total: int | None = None,
) -> State:
    state = new_state(repo_root=root)
    state["batch"].update(
        id="replacement" if replacement else "selected", status="running"
    )
    state["work"].update(
        phase="build",
        next_phase="build",
        prd=prd
        if prd is not None
        else ("replacement.md" if replacement else "selected.md"),
        tasks_completed=81 if replacement else 1,
        tasks_total=total if total is not None else (99 if replacement else 7),
    )
    state["tasks"] = [
        {
            "id": number,
            "name": f"Task {number}",
            "description": "Observe completion",
            "active_form": "Observing completion",
            "status": "pending",
            "blocked_by": [],
            "tier": None,
            "files_touched": None,
            "public_contract_edit": None,
            "estimates": {"input_tokens": None, "context_peak": None},
            "attempts": [],
            "metadata": {},
        }
        for number in range(1, state["work"]["tasks_total"] + 1)
    ]
    update_tasks(state)
    if replacement:
        state["batch"]["capabilities"]["replacement-audit"] = {
            "required": False,
            "launcher": "local",
            "plugin": "other",
            "version": "1",
            "failure": "attention",
            "status": "skipped",
            "attempts": [],
        }
    return state


def update_tasks(state: State) -> None:
    for number, task in enumerate(state["tasks"]):
        task["status"] = (
            "completed" if number < state["work"]["tasks_completed"] else "pending"
        )


@dataclass
class Driver:
    base: Path
    store: StateStore
    outcome: str
    nonce: str
    runtime: RuntimeSettings
    telemetry: bool = False
    name: str = "local"
    requests: list[LaunchRequest] = field(default_factory=list)
    default_tiers: Mapping[str, str] = field(default_factory=dict)

    def default_prompt(self, phase: str) -> str:
        return phase

    def build_launch(self, request: LaunchRequest) -> LaunchSpec:
        self.requests.append(request)
        assert len(self.requests) <= 3, "terminal state must not relaunch forever"
        code = (
            "import os,time\nfrom pathlib import Path\n"
            f"receipt=Path({str(self.base / 'agent-receipt')!r})\n"
            "temporary=receipt.with_suffix('.tmp')\n"
            f"temporary.write_text(str(os.getpid())+':'+{self.nonce!r})\n"
            "temporary.replace(receipt)\n"
            f"if {self.telemetry!r}: print('lane-start', flush=True); print('checkpoint', flush=True)\n"
            f"release=Path({str(self.base / 'release')!r})\n"
            "deadline=time.monotonic()+15\n"
            "while not release.exists() and time.monotonic()<deadline: time.sleep(.01)\n"
            "assert release.exists(), 'test did not release agent'\n"
            "print('selected agent finished', flush=True)\n"
            f"if {self.telemetry!r}: print('lane-finished', flush=True)\n"
        )
        return LaunchSpec(
            (sys.executable, "-c", code), dict(os.environ), request.root, "jsonl"
        )

    def decode(self, raw_line: str) -> tuple[Observation, ...]:
        line = raw_line.strip()
        if line == "checkpoint":
            (self.base / "telemetry-ready").touch()
        if line not in {"lane-start", "lane-finished"}:
            return ()
        metadata = json.loads(self.runtime.paths.run_metadata.read_text())
        kind = (
            ObservationType.LANE_STARTED
            if line == "lane-start"
            else ObservationType.LANE_COMPLETED
        )
        payload = (
            {"label": "Selected verifier"}
            if line == "lane-start"
            else {"detail": "Selected archive verified"}
        )
        return (
            Observation(
                1,
                datetime.now(UTC),
                "selected-provider",
                metadata["run_id"],
                self.requests[-1].session_dir.name,
                "selected-verifier",
                kind,
                payload,
            ),
        )

    def summarize(self, observations: object, exit_code: int) -> SessionSummary:
        assert exit_code == 0
        self.store.transaction(self.finish)
        failed = self.outcome == "halted"
        return SessionSummary(
            not failed,
            self.requests[-1].session_dir.name,
            FailureClass.AGENT if failed else None,
            "selected terminal failure" if failed else None,
            None,
            SELECTED_USAGE if self.telemetry else None,
        )

    def finish(self, state: State) -> None:
        total = state["work"]["tasks_total"]
        state["work"]["tasks_completed"] = total - 1
        state["review"]["cycle"] = 2
        if self.outcome in {"completed", "attention"}:
            state["work"].update(phase="done", next_phase="", tasks_completed=total)
            state["batch"]["completed_prds"] = [
                {
                    "filename": state["work"]["prd"],
                    "cycles": 2,
                    "autonomous_decisions": 0,
                    "escalated_decisions": 0,
                    "tasks_completed": total,
                    "tasks_total": total,
                }
            ]
        if self.outcome in {"paused", "stopped"}:
            state["work"].update(phase="paused", next_phase="paused")
        if self.outcome == "stopped":
            state["control"].update(
                pause_requested=True,
                pause_reason={
                    "site": "operator_stop",
                    "detail": "selected stop",
                    "created_at": STAMP,
                },
            )
        if self.outcome == "attention":
            state["batch"]["capabilities"]["audit"] = {
                "required": True,
                "launcher": "local",
                "plugin": "audit",
                "version": "1",
                "failure": "attention",
                "status": "pending",
                "attempts": [],
            }
        update_tasks(state)


class FailedCapability:
    def run(self, request: CapabilityRequest) -> CapabilityExecution:
        request.session.raw.write_text(
            f"selected capability diagnostic: {request.session.root.name}\n"
        )
        return CapabilityExecution(
            False, request.session.root.name, "selected audit failed"
        )


def worker(base: Path, outcome: str, nonce: str, telemetry: bool) -> None:
    settings = settings_for(base)
    store = StateStore(settings.runtime.paths.state_file)
    supervisor = Supervisor(
        settings.runtime.paths.project_root,
        store=store,
        driver=Driver(base, store, outcome, nonce, settings.runtime, telemetry),
        settings=settings,
        capability_runner=lambda _: FailedCapability(),
        clock=Clock(),
        sleeper=lambda _: None,
    )
    result = supervisor.run()
    (base / "supervisor-receipt").write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "nonce": nonce,
                "exit_code": result.exit_code,
                "state": store.read(),
            }
        )
    )


@dataclass
class Selected:
    base: Path
    settings: SupervisorSettings
    child: subprocess.Popen[str]
    observer: ProjectObserver
    first: ProjectView
    nonce: str

    def finish(self) -> dict[str, object]:
        (self.base / "release").touch()
        stdout, stderr = self.child.communicate(timeout=25)
        assert self.child.returncode == 0, (stdout, stderr)
        receipt = json.loads((self.base / "supervisor-receipt").read_text())
        assert receipt["pid"] == self.child.pid != os.getpid()
        assert receipt["nonce"] == self.nonce
        assert process_identity(self.child.pid) is None
        paths = self.settings.runtime.paths
        assert not paths.run_metadata.exists()
        assert not FleetRegistry(paths.fleet_root).snapshot().live
        return receipt["state"]


def wait_ready(base: Path, child: subprocess.Popen[str], telemetry: bool) -> None:
    deadline = time.monotonic() + 10
    marker = "telemetry-ready" if telemetry else "agent-receipt"
    while not (base / marker).exists():
        if child.poll() is not None:
            pytest.fail(
                f"supervisor exited before agent receipt: {child.communicate()}"
            )
        assert time.monotonic() < deadline, "supervisor never launched its agent"
        time.sleep(0.01)


def prepare(
    base: Path, replacement: bool, prd: str | None, total: int | None
) -> tuple[SupervisorSettings, State]:
    base.mkdir(exist_ok=True)
    root = base / "repo"
    root.mkdir(exist_ok=True)
    (root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner"]\n'
        'tiers = { sonnet = "model-s", opus = "model-o" }\n'
    )
    settings = settings_for(base)
    store = StateStore(settings.runtime.paths.state_file)
    initial = seed(root, replacement=replacement, prd=prd, total=total)
    if replacement:
        store.transaction(lambda _: initial)
    else:
        store.initialize(initial)
    for filename in (
        "release",
        "agent-receipt",
        "supervisor-receipt",
        "telemetry-ready",
    ):
        (base / filename).unlink(missing_ok=True)
    return settings, initial


def launch_worker(
    base: Path, outcome: str, nonce: str, telemetry: bool
) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            str(base),
            outcome,
            nonce,
            str(int(telemetry)),
        ],
        env=dict(os.environ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


@contextmanager
def selected_run(
    base: Path,
    outcome: str,
    *,
    replacement: bool = False,
    prd: str | None = None,
    total: int | None = None,
    telemetry: bool = False,
) -> Iterator[Selected]:
    settings, initial = prepare(base, replacement, prd, total)
    nonce = secrets.token_hex(16)
    child = launch_worker(base, outcome, nonce, telemetry)
    observer = None
    try:
        wait_ready(base, child, telemetry)
        pid_text, received = (base / "agent-receipt").read_text().split(":")
        assert received == nonce and int(pid_text) not in {os.getpid(), child.pid}
        os.kill(int(pid_text), 0)
        (entry,) = FleetRegistry(settings.runtime.paths.fleet_root).snapshot().live
        assert entry.pid == child.pid and process_identity(child.pid) is not None
        run = FleetRun(
            entry.run_id,
            entry.root,
            entry.agent,
            entry.started_at,
            entry.pid,
            entry.process_start,
        )
        observer = BoundedObserver(run, settings.runtime)
        first = observer.poll()
        if telemetry:
            assert first.provider == "selected-provider"
            assert first.lanes == (
                ActivityLane("selected-verifier", "Selected verifier", "running", None),
            )
        assert (
            first.status == "running"
            and first.tasks_completed == initial["work"]["tasks_completed"]
        )
        yield Selected(base, settings, child, observer, first, nonce)
    finally:
        (base / "release").touch()
        if child.poll() is None:
            child.communicate(timeout=25)
        if observer is not None:
            observer.close()


@pytest.fixture
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state-home"))
    return tmp_path


def assert_committed(
    view: ProjectView, state: dict[str, object], selected: Selected
) -> None:
    assert view.ended is True
    assert view.run == selected.first.run
    assert view.revision == state["revision"]
    assert view.tasks_completed == state["work"]["tasks_completed"]
    assert view.tasks_total == state["work"]["tasks_total"]
    assert view.phase == state["work"]["phase"]
    assert view.next_phase == state["work"]["next_phase"]
    assert view.prd == state["work"]["prd"]
    assert view.review_cycle == state["review"]["cycle"]
    assert view.attention == state["control"]["attention"]


def assert_final_telemetry(
    final: ProjectView, selected: Selected, state: dict[str, object]
) -> None:
    assert selected.first.provider == "selected-provider"
    assert final.provider == selected.first.provider
    assert selected.first.lanes == (
        ActivityLane("selected-verifier", "Selected verifier", "running", None),
    )
    assert final.lanes == (
        ActivityLane(
            "selected-verifier",
            "Selected verifier",
            "completed",
            "Selected archive verified",
        ),
    )
    metrics = observe_metrics(
        selected.settings.runtime.paths, batch_id=state["batch"]["id"]
    )
    assert metrics.complete and metrics.gaps == ()
    (metric,) = metrics.rows
    assert metric.run_id == selected.first.run.run_id
    assert metric.finished_at is not None
    assert metric.wall_seconds is not None and metric.wall_seconds >= 0
    started = datetime.fromisoformat(selected.first.run.started_at)
    completed = datetime.fromisoformat(state["batch"]["completed_at"])
    assert final.duration_seconds == (completed - started).total_seconds()
    assert final.duration_seconds >= 0
    assert final.usage == UsageView(137, 29, 11, 17, 3, 0.3125, True, False)
    assert final.telemetry == "complete"
    assert final.gaps == ()


@pytest.mark.parametrize("prd", ["00012-lantern.md", "00187-harbor-ledger.md"])
@pytest.mark.parametrize("outcome,expected", OUTCOMES)
def test_final_commit_survives_supervisor_cleanup_between_polls(
    isolated_config: Path,
    outcome: str,
    expected: AttachResult,
    prd: str,
) -> None:
    with selected_run(
        isolated_config, outcome, prd=prd, telemetry=outcome == "completed"
    ) as selected:
        state = selected.finish()
        path = selected.settings.runtime.paths.state_file
        before = path.read_bytes()
        final = selected.observer.poll()
        assert final.status == outcome
        assert_committed(final, state, selected)
        assert final.prd == prd
        assert final.provider == selected.first.provider
        if outcome == "completed":
            assert_final_telemetry(final, selected, state)
        else:
            assert final.lanes == ()
            assert final.usage is None
        assert final.tasks_completed > selected.first.tasks_completed
        assert selected.observer.poll() == final
        assert selected.observer.poll() == final
        assert path.read_bytes() == before
        assert (
            not FleetRegistry(selected.settings.runtime.paths.fleet_root)
            .snapshot()
            .live
        )


def test_failed_capability_retains_retry_and_session_evidence_after_exit(
    isolated_config: Path,
) -> None:
    with selected_run(isolated_config, "attention") as selected:
        state = selected.finish()
        final = selected.observer.poll()
        assert_committed(final, state, selected)
        (capability,) = final.capabilities
        attempt = state["batch"]["capabilities"]["audit"]["attempts"][-1]
        assert capability.name == "audit" and capability.status == "failed"
        assert capability.required and capability.detail == "selected audit failed"
        assert capability.retry_command == (
            "ovcaq",
            "--root",
            str(selected.first.run.root),
            "capability",
            "retry",
            "audit",
        )
        assert capability.session_id == attempt["session_id"] is not None
        assert (
            capability.evidence_path is not None and capability.evidence_path.exists()
        )
        assert (
            selected.settings.runtime.paths.sessions in capability.evidence_path.parents
        )
        session_root = selected.settings.runtime.paths.sessions / attempt["session_id"]
        capability.evidence_path.relative_to(session_root)
        assert (session_root / "raw.jsonl").read_text().splitlines()[0] == (
            f"selected capability diagnostic: {attempt['session_id']}"
        )


@pytest.mark.parametrize("prd", ["00219-beacon.md", "00301-river-audit.md"])
@pytest.mark.parametrize("cache_final", [False, True])
def test_replacement_never_becomes_the_ended_selection(
    isolated_config: Path,
    cache_final: bool,
    prd: str,
) -> None:
    with selected_run(isolated_config, "paused", prd=prd) as selected:
        selected.finish()
        proven = selected.observer.poll() if cache_final else selected.first
        with selected_run(
            isolated_config,
            "completed",
            replacement=True,
            prd="00477-replacement.md",
        ) as replacement:
            path = selected.settings.runtime.paths.state_file
            before = path.read_bytes()
            final = selected.observer.poll()
            assert final.ended and final.run == selected.first.run
            assert final.prd == prd
            assert (
                final.prd == proven.prd
                and final.tasks_completed == proven.tasks_completed
            )
            assert final.tasks_total == proven.tasks_total
            assert final.capabilities == proven.capabilities
            assert (
                final.run != replacement.first.run
                and final.prd != replacement.first.prd
            )
            assert final.status != "completed"
            if cache_final:
                assert final.status == proven.status
            else:
                assert final.gaps
            assert selected.observer.poll() == final
            assert path.read_bytes() == before
            assert replacement.child.poll() is None


@dataclass
class ReplacementDuringRead:
    selected: Selected
    forward: Callable[..., int]
    caller: int = field(default_factory=threading.get_ident)
    ready: threading.Event = field(default_factory=threading.Event)
    done: threading.Event = field(default_factory=threading.Event)
    replacement: Selected | None = None
    error: BaseException | None = None
    thread: threading.Thread | None = None
    state_bytes: bytes = b""

    def publish(self) -> None:
        try:
            with selected_run(self.selected.base, "completed", replacement=True) as run:
                self.replacement = run
                self.state_bytes = run.settings.runtime.paths.state_file.read_bytes()
                self.ready.set()
                assert self.done.wait(15), "race assertions did not release replacement"
        except BaseException as error:  # noqa: BLE001 - re-raised in the test thread
            self.error = error
        finally:
            self.ready.set()

    def open(
        self, path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> int:
        paths = self.selected.settings.runtime.paths
        names = {paths.runtime_root.name, paths.fleet_root.name, paths.state_file.name}
        if (
            threading.get_ident() == self.caller
            and self.thread is None
            and Path(os.fsdecode(path)).name in names
            and flags & os.O_ACCMODE == os.O_RDONLY
        ):
            self.thread = threading.Thread(target=self.publish)
            self.thread.start()
            # A reader may hold the run lock. Do not require a writer to beat it.
            self.ready.wait(0.5)
        return self.forward(path, flags, mode, dir_fd=dir_fd)

    def await_replacement(self) -> Selected:
        assert self.thread is not None, (
            "final observation did not reach an OS read boundary"
        )
        assert self.ready.wait(10), (
            "replacement did not start after final poll returned"
        )
        if self.error is not None:
            raise self.error
        assert self.replacement is not None
        return self.replacement

    def close(self) -> None:
        self.done.set()
        if self.thread is not None:
            self.thread.join(timeout=25)
            assert not self.thread.is_alive(), "replacement fixture did not finish"
        if self.error is not None:
            raise self.error


def assert_selected_race_evidence(
    final: ProjectView, state: dict[str, object], selected: Selected
) -> None:
    assert final.ended and final.run == selected.first.run
    assert final.lanes == ()
    if final.tasks_completed == state["work"]["tasks_completed"]:
        assert_committed(final, state, selected)
        assert final.status == "attention"
        (capability,) = final.capabilities
        assert (
            capability.name == "audit" and capability.detail == "selected audit failed"
        )
    else:
        prior = selected.first
        assert final.gaps
        assert final.revision == prior.revision
        assert (final.phase, final.next_phase, final.prd) == (
            prior.phase,
            prior.next_phase,
            prior.prd,
        )
        assert (final.tasks_completed, final.tasks_total) == (
            prior.tasks_completed,
            prior.tasks_total,
        )
        assert final.capabilities == prior.capabilities
        assert final.attention == prior.attention
        assert final.status != "completed"


def test_replacement_starting_during_final_observation_cannot_supply_selected_data(
    isolated_config: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with selected_run(isolated_config, "attention") as selected:
        state = selected.finish()
        race = ReplacementDuringRead(selected, os.open)
        try:
            with monkeypatch.context() as boundary:
                boundary.setattr(os, "open", race.open)
                final = selected.observer.poll()
            replacement = race.await_replacement()
            assert replacement.child.poll() is None
            assert process_identity(replacement.child.pid) is not None
            assert final.run != replacement.first.run
            assert final.prd != replacement.first.prd
            assert final.tasks_completed != replacement.first.tasks_completed
            assert final.tasks_total != replacement.first.tasks_total
            assert final.capabilities != replacement.first.capabilities
            assert_selected_race_evidence(final, state, selected)
            assert selected.observer.poll() == final
            assert (
                selected.settings.runtime.paths.state_file.read_bytes()
                == race.state_bytes
            )
            assert replacement.child.poll() is None
        finally:
            race.close()


@pytest.mark.parametrize("damage", ["missing", "symlink"])
def test_unavailable_final_state_is_visible_and_cannot_claim_completion(
    isolated_config: Path,
    damage: str,
) -> None:
    with selected_run(isolated_config, "completed") as selected:
        selected.finish()
        path = selected.settings.runtime.paths.state_file
        saved = path.with_name("unavailable-state.json")
        path.rename(saved)
        if damage == "symlink":
            path.symlink_to(saved)
        final = selected.observer.poll()
        assert final.ended and final.gaps
        assert final.telemetry in {"partial", "unavailable"}
        cause = (
            r"missing|not found|no such file|FileNotFoundError"
            if damage == "missing"
            else r"symlink|symbolic link|too many levels|not a regular file|unsafe state path"
        )
        assert any(
            re.search(r"state|final.{0,20}evidence", gap, re.IGNORECASE)
            and re.search(cause, gap, re.IGNORECASE)
            for gap in final.gaps
        )
        assert final.status != "completed"
        assert final.run == selected.first.run
        assert final.tasks_completed != 7
        assert selected.observer.poll() == final


if __name__ == "__main__":
    worker(Path(sys.argv[1]), sys.argv[2], sys.argv[3], bool(int(sys.argv[4])))
