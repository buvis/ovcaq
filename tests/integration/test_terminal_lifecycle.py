"""Real-subprocess and PTY lifecycle tests for the interactive run/attach paths."""

from __future__ import annotations

import fcntl
import json
import os
import pty
import select
import signal
import struct
import subprocess
import sys
import termios
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ovcaq.paths import resolve_runtime_paths
from ovcaq.runtime.registry import FleetEntry, FleetRegistry, process_identity
from ovcaq.state.store import StateStore

COMPLETED = {
    "filename": "finished.md",
    "cycles": 1,
    "autonomous_decisions": 0,
    "escalated_decisions": 0,
    "tasks_completed": 0,
    "tasks_total": 0,
}
ALT_SCREEN_ON = b"\x1b[?1049h"
ALT_SCREEN_OFF = b"\x1b[?1049l"
COOKED = termios.ICANON | termios.ECHO | termios.ISIG
SHIMMED_LAUNCHERS = ("bash", "sh", "zsh", "autoclaude", "autopilot", "tracon")
KEYS = [b"q", b"\x03", b"\x04"]
KEY_IDS = ["q", "ctrl-c", "ctrl-d"]

# Blocks each phase until the test creates go-<phase>, then advances the state.
FAKE_AGENT = r"""
import json, os, sys, time
from pathlib import Path
from ovcaq.paths import resolve_runtime_paths
from ovcaq.state.store import StateStore
root = Path.cwd()
store = StateStore(resolve_runtime_paths(root).state_file)
phase = store.read()["work"]["phase"]
with (root / "invocations.jsonl").open("a") as stream:
    stream.write(json.dumps({"phase": phase, "pid": os.getpid()}) + "\n")
print(json.dumps({"type": "system", "subtype": "init",
                  "session_id": "fake-" + phase}), flush=True)
gate = root / ("go-" + phase)
deadline = time.monotonic() + 90
while not gate.exists():
    if time.monotonic() > deadline:
        raise SystemExit(3)
    time.sleep(0.05)

def advance(state):
    if phase == "build":
        state["work"].update(phase="review", next_phase="review")
    elif phase == "review":
        state["work"].update(phase="done", next_phase="done")
        state["work"]["completed_phases"].append("review")
    elif phase == "done":
        state["work"].update(phase="done", next_phase="")
        state["batch"]["completed_prds"].append(
            json.loads((root / "completed.json").read_text()))

store.transaction(advance)
print(json.dumps({"type": "result", "subtype": "success", "is_error": False,
                  "session_id": "fake-" + phase, "result": "ok"}), flush=True)
"""

# Takes the pty as its controlling tty (real SIGINT; macOS revokes it when the
# session leader exits, so only this test needs it), then fails the Textual app
# after putting the terminal in raw mode.
FALLBACK_WRAPPER = """
import fcntl, sys, termios, tty
fcntl.ioctl(0, termios.TIOCSCTTY, 0)
from ovcaq.tui import app
def fail(self):
    tty.setraw(sys.stdin.fileno())
    raise RuntimeError("synthetic textual startup failure")
app.ProjectApp.run = fail
from ovcaq.cli import main
raise SystemExit(main(sys.argv[1:]))
"""


def wait_until(
    predicate: Callable[[], object], what: str, timeout: float = 20.0
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    pytest.fail(f"timed out after {timeout}s waiting for {what}")


def ps_field(name: str, pid: int) -> str:
    result = subprocess.run(
        ["ps", "-ww", "-o", f"{name}=", "-p", str(pid)],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    return result.stdout.strip()


def gone(pid: int) -> bool:
    return process_identity(pid) is None


def invocations(root: Path) -> list[dict[str, Any]]:
    path = root / "invocations.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def pause_requested(root: Path) -> bool:
    try:
        state = json.loads(
            (root / "docs/dev/project-management/ovcaq/state.json").read_text()
        )
        return bool(state["control"]["pause_requested"])
    except (OSError, ValueError, KeyError):
        return False


@dataclass
class Term:
    proc: subprocess.Popen[bytes]
    master: int
    slave: int
    output: bytearray = field(default_factory=bytearray)

    def pump(self, wait: float = 0.05) -> None:
        if select.select([self.master], [], [], wait)[0]:
            with suppress(OSError):
                self.output.extend(os.read(self.master, 65536))

    def wait_for(
        self, predicate: Callable[[], object], what: str, timeout: float = 20.0
    ) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.pump()
            if predicate():
                return
        tail = bytes(self.output[-300:])
        pytest.fail(f"timed out after {timeout}s waiting for {what}; tail={tail!r}")

    def expect(self, text: str) -> None:
        self.wait_for(lambda: text.encode() in self.output, repr(text))

    def send(self, data: bytes) -> None:
        os.write(self.master, data)

    def exit_code(self, timeout: float = 15.0) -> int:
        self.wait_for(lambda: self.proc.poll() is not None, "exit", timeout)
        assert self.proc.returncode is not None
        return self.proc.returncode

    def send_until_exit(self, key: bytes, timeout: float = 15.0) -> int:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                return self.exit_code()
            self.send(key)
            self.pump(0.3)
        pytest.fail(f"{key!r} did not end the viewer within {timeout}s")

    def is_cooked(self) -> bool:
        return termios.tcgetattr(self.slave)[3] & COOKED == COOKED

    def close(self) -> None:
        if self.proc.poll() is None:
            with suppress(ProcessLookupError):
                os.killpg(self.proc.pid, signal.SIGKILL)
        self.proc.wait(timeout=5)
        for descriptor in (self.master, self.slave):
            with suppress(OSError):
                os.close(descriptor)


class World:
    """Isolated state, config, home, project roots and PATH for one test."""

    def __init__(self, base: Path) -> None:
        self.base = base
        self.state_home = base / "xdg-state"
        self.fleet_root = self.state_home / "ovcaq/runs"
        self.marker = base / "launcher-calls"
        shims = base / "shims"
        shims.mkdir()
        for name in SHIMMED_LAUNCHERS:
            shim = shims / name
            shim.write_text(f'#!/bin/sh\necho "$0 $*" >> {self.marker}\nexit 127\n')
            shim.chmod(0o700)
        (base / "home").mkdir()
        self.env = {
            "PATH": f"{shims}:/usr/bin:/bin",
            "HOME": str(base / "home"),
            "XDG_STATE_HOME": str(self.state_home),
            "XDG_CONFIG_HOME": str(base / "xdg-config"),
            "XDG_CACHE_HOME": str(base / "xdg-cache"),
            "TERM": "xterm-256color",
            "LC_ALL": "en_US.UTF-8",
            "PYTHONNOUSERSITE": "1",
        }
        self.terms: list[Term] = []
        self.pipes: list[subprocess.Popen[str]] = []
        self.projects: list[Path] = []

    def project(self, name: str = "project") -> Path:
        root = self.base / name
        root.mkdir()
        agent = root / "fake-agent"
        agent.write_text(f"#!{sys.executable}\n{FAKE_AGENT}", encoding="utf-8")
        agent.chmod(0o700)
        (root / "completed.json").write_text(json.dumps(COMPLETED))
        phases = "".join(
            f"[phases.{phase}]\ntimeout_seconds = 120\n"
            for phase in ("build", "review", "done")
        )
        (root / "ovcaq.toml").write_text(
            f'agent = "claude"\n[agents.claude]\ncommand = [{json.dumps(str(agent))}]\n'
            'tiers = { standard = "model-s", deep = "model-o" }\n'
            f'[agents.claude.options]\npermission_mode = "auto"\n{phases}',
            encoding="utf-8",
        )
        self.projects.append(root)
        init = subprocess.run(
            [sys.executable, "-m", "ovcaq", "--root", str(root), "--json", "init"],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert init.returncode == 0, init.stderr
        paths = resolve_runtime_paths(root, xdg_state_home=self.state_home)

        def seed(state: Any) -> None:
            state["batch"].update(id="terminal-lifecycle", status="running")
            state["work"].update(phase="build", next_phase="build")

        StateStore(paths.state_file).transaction(seed)
        return root

    def ovcaq(self, *args: str) -> list[str]:
        return [sys.executable, "-m", "ovcaq", *args]

    def spawn(self, *args: str) -> Term:
        return self.spawn_argv(self.ovcaq(*args))

    def spawn_argv(self, argv: list[str]) -> Term:
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))
        proc = subprocess.Popen(
            argv,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            cwd=self.base,
            env=self.env,
            start_new_session=True,
            close_fds=True,
            shell=False,
        )
        term = Term(proc, master, slave)
        self.terms.append(term)
        return term

    def pipe(self, *args: str) -> subprocess.Popen[str]:
        proc = subprocess.Popen(
            self.ovcaq(*args),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.base,
            env=self.env,
            start_new_session=True,
            shell=False,
        )
        self.pipes.append(proc)
        return proc

    def live(self, root: Path | None = None) -> list[FleetEntry]:
        if not self.fleet_root.exists():
            return []
        entries = FleetRegistry(self.fleet_root).snapshot().live
        return [entry for entry in entries if root is None or entry.root == root]

    def wait_live(self, root: Path, count: int = 1) -> list[FleetEntry]:
        found: list[FleetEntry] = []

        def ready() -> bool:
            found[:] = self.live(root)
            return len(found) == count

        wait_until(ready, f"{count} live run(s) for {root.name}")
        return found

    def launcher_calls(self) -> str:
        return self.marker.read_text() if self.marker.exists() else ""

    def close(self) -> None:
        for term in self.terms:
            term.close()
        for proc in self.pipes:
            if proc.poll() is None:
                with suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate(timeout=5)
        supervisors = {entry.pid for entry in self.live()}
        drivers: set[int] = set()
        for root in self.projects:
            drivers.update(row["pid"] for row in invocations(root))
            with suppress(OSError, ValueError, KeyError):
                record = json.loads(
                    (root / "docs/dev/project-management/ovcaq/run.json").read_text()
                )
                supervisors.add(int(record["pid"]))
        self._reap(supervisors, "ovcaq", signal.SIGTERM)
        self._reap(supervisors, "ovcaq", signal.SIGKILL)
        self._reap(drivers, "fake-agent", signal.SIGKILL)

    @staticmethod
    def _reap(pids: set[int], marker: str, number: signal.Signals) -> None:
        for pid in pids:
            if not gone(pid) and marker in ps_field("command", pid):
                with suppress(ProcessLookupError):
                    os.kill(pid, number)
        if number == signal.SIGTERM:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and not all(map(gone, pids)):
                time.sleep(0.05)


@pytest.fixture
def world(tmp_path: Path) -> Any:
    sandbox = World(tmp_path.resolve())
    try:
        yield sandbox
    finally:
        sandbox.close()
    assert sandbox.launcher_calls() == "", "a Bash/legacy launcher was invoked"


def running(
    world: World, *extra: str, name: str = "project"
) -> tuple[Path, FleetEntry, Term]:
    root = world.project(name)
    term = world.spawn("--root", str(root), "run", *extra)
    [entry] = world.wait_live(root)
    term.expect(entry.run_id)
    wait_until(lambda: len(invocations(root)) == 1, "the agent to start")
    return root, entry, term


def detach(term: Term, key: bytes = b"q") -> None:
    term.send(key)
    assert term.exit_code() == 0
    assert term.is_cooked()
    assert ALT_SCREEN_ON in term.output and ALT_SCREEN_OFF in term.output


def assert_survives(world: World, root: Path, entry: FleetEntry, launches: int) -> None:
    assert world.live(root) == [entry]
    assert not gone(entry.pid)
    assert len(invocations(root)) == launches


@pytest.mark.parametrize("key", KEYS, ids=KEY_IDS)
def test_interactive_run_detach_key_leaves_the_supervisor_alive(
    world: World, key: bytes
) -> None:
    root, entry, term = running(world)
    assert entry.pid != term.proc.pid
    detach(term, key)
    assert_survives(world, root, entry, launches=1)


@pytest.mark.parametrize("agent", [(), ("--agent", "claude")], ids=["default", "named"])
def test_run_omits_agent_from_the_supervisor_argv_unless_requested(
    world: World, agent: tuple[str, ...]
) -> None:
    root, entry, term = running(world, *agent)
    command = ps_field("command", entry.pid).split()
    assert command[0] == sys.executable and command[1:3] == ["-m", "ovcaq"]
    assert command[3:6] == ["--root", str(root), "run"] and "--no-tui" in command
    assert ("--agent" in command) is bool(agent)
    assert entry.agent == "claude"
    detach(term)
    assert_survives(world, root, entry, launches=1)


def test_detached_supervisor_can_be_reattached_repeatedly(world: World) -> None:
    root, entry, first = running(world)
    detach(first)
    for key, extra in zip(KEYS, ((), ("--run-id", entry.run_id), ()), strict=True):
        view = world.spawn("--root", str(root), "attach", *extra)
        view.expect(entry.run_id)
        detach(view, key)
        assert_survives(world, root, entry, launches=1)


def test_attach_without_root_displays_fleet_selection_in_the_terminal(
    world: World,
) -> None:
    root, entry, first = running(world)
    detach(first)
    view = world.spawn("attach")
    view.expect("OVCAQ fleet")
    view.expect(entry.run_id)
    detach(view)
    assert_survives(world, root, entry, launches=1)


def test_plain_fleet_selection_lists_runs_and_detaches_on_eof(world: World) -> None:
    root, entry, first = running(world)
    detach(first)
    result = world.pipe("attach")
    stdout, stderr = result.communicate(timeout=20)
    assert result.returncode == 0, stderr
    assert entry.run_id in stdout and "run id:" in stdout
    assert ALT_SCREEN_ON.decode() not in stdout
    assert_survives(world, root, entry, launches=1)


def test_attach_never_launches_a_supervisor(world: World) -> None:
    root = world.project()
    result = world.pipe("--root", str(root), "attach")
    _stdout, stderr = result.communicate(timeout=20)
    assert result.returncode != 0 and "No matching run selection" in stderr
    assert world.live() == [] and invocations(root) == []
    assert not list((root / "docs/dev/project-management/ovcaq").glob("launch-*"))


def test_json_attach_is_rejected_without_viewer_or_launch(world: World) -> None:
    root = world.project()
    result = world.pipe("--root", str(root), "--json", "attach")
    stdout, stderr = result.communicate(timeout=20)
    assert result.returncode != 0 and stdout == ""
    assert json.loads(stderr)["error"]["code"] == "usage"
    assert world.live() == [] and invocations(root) == []


def test_p_requests_a_boundary_pause_and_the_run_stops_at_the_boundary(
    world: World,
) -> None:
    root, entry, term = running(world)
    term.send(b"p")
    wait_until(lambda: pause_requested(root), "the pause request")
    assert_survives(world, root, entry, launches=1)
    (root / "go-build").write_text("")
    wait_until(lambda: world.live(root) == [], "the supervisor to exit")
    wait_until(lambda: gone(entry.pid), "the supervisor process to end")
    assert [row["phase"] for row in invocations(root)] == ["build"]
    assert pause_requested(root)
    detach(term)


def test_resume_reattaches_the_same_live_run(world: World) -> None:
    root, entry, term = running(world)
    term.send(b"p")
    wait_until(lambda: pause_requested(root), "the pause request")
    detach(term)
    view = world.spawn("--root", str(root), "resume")
    view.expect(entry.run_id)
    wait_until(lambda: not pause_requested(root), "the pause to clear")
    assert_survives(world, root, entry, launches=1)
    detach(view)
    assert_survives(world, root, entry, launches=1)


def test_resume_after_boundary_pause_launches_once_and_attaches_the_new_run(
    world: World,
) -> None:
    root, entry, term = running(world)
    term.send(b"p")
    wait_until(lambda: pause_requested(root), "the pause request")
    (root / "go-build").write_text("")
    wait_until(lambda: world.live(root) == [], "the supervisor to exit")
    detach(term)
    view = world.spawn("--root", str(root), "resume")
    [fresh] = world.wait_live(root)
    assert fresh.run_id != entry.run_id and fresh.pid != entry.pid
    view.expect(fresh.run_id)
    wait_until(lambda: len(invocations(root)) == 2, "the restarted agent")
    assert not pause_requested(root)
    detach(view)
    assert_survives(world, root, fresh, launches=2)


def test_cancelled_stop_leaves_the_run_alive(world: World) -> None:
    root, entry, first = running(world)
    detach(first)
    view = world.spawn("--root", str(root), "attach")
    view.expect(entry.run_id)
    view.send(b"s")
    view.expect("Stop run")
    view.send(b"n")
    assert view.send_until_exit(b"q") == 0
    assert_survives(world, root, entry, launches=1)


def test_confirmed_stop_targets_exactly_the_selected_run(world: World) -> None:
    first_root, first, term = running(world, name="first")
    detach(term)
    second_root, second, term = running(world, name="second")
    detach(term)
    view = world.spawn("--root", str(first_root), "attach")
    view.expect(first.run_id)
    view.send(b"s")
    view.expect("Stop run")
    view.send(b"y")
    wait_until(lambda: world.live(first_root) == [], "the selected run to stop")
    wait_until(lambda: gone(first.pid), "the selected supervisor to end")
    assert view.send_until_exit(b"q") == 0
    assert_survives(world, second_root, second, launches=1)
    assert [entry.run_id for entry in world.live()] == [second.run_id]


def test_textual_failure_restores_the_terminal_and_falls_back_to_plain(
    world: World,
) -> None:
    root = world.project()
    term = world.spawn_argv(
        [sys.executable, "-c", FALLBACK_WRAPPER, "--root", str(root), "run"]
    )
    [entry] = world.wait_live(root)
    term.expect("synthetic textual startup failure")
    term.expect("using plain output")
    term.expect(f"OVCAQ run: {entry.run_id}")
    assert term.is_cooked() and ALT_SCREEN_ON not in term.output
    wait_until(lambda: len(invocations(root)) == 1, "the agent to start")
    term.send(b"\x03")
    assert term.exit_code() == 0
    assert_survives(world, root, entry, launches=1)


@pytest.mark.parametrize(
    "arguments,tty",
    [
        (("run", "--no-tui"), True),
        (("--json", "run", "--no-tui"), True),
        (("run",), False),
        (("run", "--no-tui"), False),
    ],
    ids=["tty-no-tui", "tty-json", "pipe-default", "pipe-no-tui"],
)
def test_noninteractive_runs_supervise_in_the_foreground_process(
    world: World, arguments: tuple[str, ...], tty: bool
) -> None:
    root = world.project()
    args = ("--root", str(root), *arguments)
    term = world.spawn(*args) if tty else None
    pipe = None if tty else world.pipe(*args)
    process = term.proc if term else pipe
    assert process is not None
    [entry] = world.wait_live(root)
    assert entry.pid == process.pid
    for phase in ("build", "review", "done"):
        wait_until(
            lambda p=phase: [r["phase"] for r in invocations(root)][-1:] == [p],
            f"the {phase} agent",
        )
        (root / f"go-{phase}").write_text("")
    if term:
        assert term.exit_code(30) == 0
        assert ALT_SCREEN_ON not in term.output and b"complete" in term.output
    else:
        stdout, _ = pipe.communicate(timeout=30)
        assert pipe.returncode == 0 and "complete" in stdout
    assert world.live(root) == []
    assert not list((root / "docs/dev/project-management/ovcaq").glob("launch-*"))


def test_no_bash_launcher_is_invoked_or_required(world: World) -> None:
    _root, entry, term = running(world)
    argv = ps_field("command", entry.pid).split()
    assert argv[:3] == [sys.executable, "-m", "ovcaq"]
    assert not {Path(token).name for token in argv} & set(SHIMMED_LAUNCHERS)
    assert "-c" not in argv
    assert world.launcher_calls() == ""
    detach(term)
    assert world.launcher_calls() == ""
