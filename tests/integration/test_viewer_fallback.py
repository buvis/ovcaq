"""Fallback viewing survives UI failures and real terminal detach signals."""

from __future__ import annotations

import asyncio
import io
import json
import os
import pty
import subprocess
import sys
import tempfile
import termios
import threading
import time
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from tests.integration.test_observer_terminal_cleanup import (
    isolated_config as isolated_config,  # noqa: PLC0414 - pytest fixture re-export
)
from tests.integration.test_observer_terminal_cleanup import selected_run

from ovcaq.runtime.registry import (
    FleetEntry,
    FleetRun,
    ProcessIdentity,
    RegistrySnapshot,
)
from ovcaq.tui import app as app_module
from ovcaq.tui.app import AttachResult, FleetApp, ProjectApp, attach, run_plain
from ovcaq.tui.model import ActivityLane, ProjectView

SUPPORT = Path(__file__).with_name("viewer_fallback_support.py")


class Controls:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    def pause(
        self, run: FleetRun, expected_revision: int, reason: str | None = None
    ) -> None:
        self.calls.append(("pause", run, expected_revision, reason))

    def resume(self, run: FleetRun, expected_revision: int) -> None:
        self.calls.append(("resume", run, expected_revision))

    def stop(self, run: FleetRun) -> ProcessIdentity:
        self.calls.append(("stop", run))
        return ProcessIdentity(run.pid, run.process_start)


class Terminal(io.StringIO):
    def isatty(self) -> bool:
        return True


class Registry:
    def __init__(self, runs: tuple[FleetRun, ...]) -> None:
        self.runs = runs

    def snapshot(self) -> RegistrySnapshot:
        return RegistrySnapshot(
            tuple(
                FleetEntry(
                    1, r.root, r.pid, r.process_start, r.run_id, r.agent, r.started_at
                )
                for r in self.runs
            ),
            (),
            (),
        )


class Observer:
    def __init__(self, views: list[ProjectView]) -> None:
        self.views = views
        self.polls = 0
        self.closed = False

    def poll(self) -> ProjectView:
        self.polls += 1
        return self.views.pop(0) if len(self.views) > 1 else self.views[0]

    def close(self) -> None:
        self.closed = True


def view(run: FleetRun, **changes: object) -> ProjectView:
    initial = ProjectView(
        run,
        "running",
        "build",
        "build",
        "selected.md",
        1,
        1,
        3,
        0,
        "generic",
        120.0,
        None,
        (),
        (),
        None,
        "complete",
        (),
        False,
    )
    return replace(initial, **changes)


def identities_alive(selected: object) -> None:
    assert selected.child.poll() is None
    agent_pid, nonce = (selected.base / "agent-receipt").read_text().split(":")
    assert nonce == selected.nonce
    os.kill(int(agent_pid), 0)


class Helper:
    def __init__(
        self, process: subprocess.Popen[bytes], output: Any, error: Any
    ) -> None:
        self.process, self.output, self.error = process, output, error


def start_helper(selected: object, mode: str, stdin: object) -> Helper:
    (selected.base / "viewer-result").unlink(missing_ok=True)
    (selected.base / "viewer-ready").unlink(missing_ok=True)
    with ExitStack() as stack:
        output = stack.enter_context(tempfile.TemporaryFile())
        error = stack.enter_context(tempfile.TemporaryFile())
        process = subprocess.Popen(
            [sys.executable, str(SUPPORT), mode, str(selected.base)],
            stdin=stdin,
            stdout=output,
            stderr=error,
            env=dict(os.environ),
            start_new_session=True,
        )
        stack.pop_all()
    return Helper(process, output, error)


def wait_helper_ready(helper: Helper, selected: object) -> None:
    deadline = time.monotonic() + 10
    while not (selected.base / "viewer-ready").exists():
        assert helper.process.poll() is None, "viewer exited before becoming ready"
        assert time.monotonic() < deadline, "viewer did not become ready"
        time.sleep(0.01)


def finish_helper(helper: Helper, selected: object) -> tuple[dict[str, object], str]:
    helper.process.wait(timeout=10)
    helper.output.seek(0)
    helper.error.seek(0)
    output = helper.output.read().decode() + helper.error.read().decode()
    assert helper.process.returncode == 0, output
    return json.loads((selected.base / "viewer-result").read_text()), output


def cleanup_helper(helper: Helper) -> None:
    process = helper.process
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if process.stdin is not None and not process.stdin.closed:
        process.stdin.close()
    helper.output.close()
    helper.error.close()


def test_pipe_eof_detaches_live_plain_viewer_and_preserves_processes(
    isolated_config: Path,
) -> None:
    with selected_run(isolated_config, "completed") as selected:
        helper = start_helper(selected, "plain", subprocess.PIPE)
        try:
            wait_helper_ready(helper, selected)
            assert helper.process.stdin is not None
            helper.process.stdin.close()
            helper.process.stdin = None
            result, _ = finish_helper(helper, selected)
            identities_alive(selected)
            assert result == {"reason": "detached", "exit_code": 0}
        finally:
            cleanup_helper(helper)


def test_pty_ctrl_d_detaches_live_plain_viewer_and_preserves_processes(
    isolated_config: Path,
) -> None:
    with selected_run(isolated_config, "completed") as selected:
        master, slave = pty.openpty()
        helper = None
        try:
            helper = start_helper(selected, "plain", slave)
            os.close(slave)
            slave = -1
            wait_helper_ready(helper, selected)
            os.write(master, b"\x04")
            result, _ = finish_helper(helper, selected)
            identities_alive(selected)
        finally:
            os.close(master)
            if slave >= 0:
                os.close(slave)
            if helper is not None:
                cleanup_helper(helper)
        assert result == {"reason": "detached", "exit_code": 0}


def test_open_stdin_does_not_block_observation_of_completion(
    isolated_config: Path,
) -> None:
    with selected_run(isolated_config, "completed") as selected:
        helper = start_helper(selected, "plain", subprocess.PIPE)
        try:
            wait_helper_ready(helper, selected)
            assert helper.process.stdin is not None and not helper.process.stdin.closed
            identities_alive(selected)
            (selected.base / "release").touch()
            result, _ = finish_helper(helper, selected)
            assert helper.process.stdin is not None and not helper.process.stdin.closed
        finally:
            cleanup_helper(helper)
        assert result == {"reason": "completed", "exit_code": 0}


@pytest.mark.parametrize("exception_name", ["OSError", "ValueError"])
def test_isolated_textual_import_failure_falls_back_and_preserves_processes(
    isolated_config: Path, exception_name: str
) -> None:
    with selected_run(isolated_config, "completed") as selected:
        helper = start_helper(selected, f"import-{exception_name}", subprocess.PIPE)
        try:
            wait_helper_ready(helper, selected)
            assert helper.process.stdin is not None
            helper.process.stdin.close()
            helper.process.stdin = None
            result, output = finish_helper(helper, selected)
            identities_alive(selected)
            notices = [line for line in output.splitlines() if "plain" in line.lower()]
            assert result == {"reason": "detached", "exit_code": 0}
            assert len(notices) == 1
        finally:
            cleanup_helper(helper)


class PollProbe:
    def __init__(self, observer: object, *, block_first: bool = False) -> None:
        self.observer = observer
        self.original_poll = observer.poll
        self.original_close = observer.close
        self.entered, self.release = threading.Event(), threading.Event()
        self.lock = threading.Lock()
        self.polls = self.active = self.maximum = 0
        self.block_first = block_first
        self.violations: list[str] = []
        self.events: list[str] = []

    def poll(self) -> ProjectView:
        with self.lock:
            self.polls += 1
            number = self.polls
            self.active += 1
            self.maximum = max(self.maximum, self.active)
        try:
            if self.block_first and number == 1:
                self.entered.set()
                assert self.release.wait(5), "blocked observation was not released"
            return self.original_poll()
        finally:
            with self.lock:
                self.active -= 1
                self.events.append("poll complete")

    def close(self) -> None:
        with self.lock:
            if self.active:
                self.violations.append("close raced observation")
            self.events.append("close")
        self.original_close()


def failing_app_type(
    boundary: str, entries: list[object], probe: PollProbe
) -> type[ProjectApp]:
    class FailingApp(ProjectApp):
        def __init__(self, current: object, *args: object, **kwargs: object) -> None:
            entries.append(current)
            if boundary == "construction":
                raise ValueError("construction failed")
            super().__init__(current, *args, **kwargs)

        def run(self) -> None:
            if boundary != "runtime":
                raise LookupError("start failed")

            async def crash() -> None:
                async with self.run_test():
                    assert probe.entered.wait(2)
                    attributes = termios.tcgetattr(sys.stdin.fileno())
                    attributes[3] ^= termios.ECHO
                    termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, attributes)
                    await asyncio.sleep(0.2)
                    probe.release.set()
                    raise LookupError("runtime I/O failed")

            asyncio.run(crash())

    return FailingApp


def assert_project_failure(
    result: AttachResult,
    entries: list[object],
    observer: object,
    streams: tuple[io.StringIO, io.StringIO],
    probe: PollProbe,
    controls: Controls,
    boundary: str,
) -> None:
    output, error = streams
    notices = [
        line
        for line in (output.getvalue() + error.getvalue()).splitlines()
        if "plain" in line.lower()
    ]
    assert result == AttachResult("completed", 0) and entries == [observer]
    assert len(notices) == 1 and "close" in probe.events and controls.calls == []
    assert probe.events.index("plain") < probe.events.index("close")
    assert probe.maximum <= 1 and probe.active == 0
    if boundary == "runtime":
        assert (
            probe.events.index("poll complete")
            < probe.events.index("plain")
            < probe.events.index("close")
        )


def exercise_project_failure(
    selected: object, monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    observer, controls, entries = selected.observer, Controls(), []
    probe = PollProbe(observer, block_first=boundary == "runtime")
    monkeypatch.setattr(observer, "close", probe.close)
    if boundary == "runtime":
        monkeypatch.setattr(observer, "poll", probe.poll)
    master, slave = pty.openpty()
    tty_input = os.fdopen(os.dup(slave), "r")
    output, error = Terminal(), io.StringIO()
    original = termios.tcgetattr(tty_input.fileno())

    def plain(current: object, *, poll_interval: float) -> AttachResult:
        assert current is observer and probe.active == 0
        probe.events.append("plain")
        assert termios.tcgetattr(tty_input.fileno())[3] == original[3]
        identities_alive(selected)
        (selected.base / "release").touch()
        return run_plain(current, poll_interval=poll_interval)

    monkeypatch.setattr(app_module, "ProjectObserver", lambda run, settings: observer)
    monkeypatch.setattr(
        app_module, "ProjectApp", failing_app_type(boundary, entries, probe)
    )
    monkeypatch.setattr(app_module, "run_plain", plain)
    monkeypatch.setattr(sys, "stdin", tty_input)
    monkeypatch.setattr(sys, "stdout", output)
    monkeypatch.setattr(sys, "stderr", error)
    try:
        result = attach(
            registry=Registry((selected.first.run,)),
            root=selected.first.run.root,
            controls=controls,
            poll_interval=0.01,
        )
    finally:
        probe.release.set()
        termios.tcsetattr(tty_input.fileno(), termios.TCSANOW, original)
        tty_input.close()
        os.close(master)
        os.close(slave)
    assert_project_failure(
        result, entries, observer, (output, error), probe, controls, boundary
    )


@pytest.mark.parametrize("boundary", ["construction", "start", "runtime"])
def test_ordinary_project_ui_failure_restores_pty_and_reuses_observer(
    isolated_config: Path, monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    with selected_run(isolated_config, "completed") as selected:
        exercise_project_failure(selected, monkeypatch, boundary)


@pytest.mark.parametrize("error", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("fleet", [False, True])
def test_ui_process_control_exceptions_do_not_enter_plain_fallback(
    isolated_config: Path,
    monkeypatch: pytest.MonkeyPatch,
    error: type[BaseException],
    fleet: bool,
) -> None:
    with selected_run(isolated_config, "completed") as selected:
        controls, plain_calls = Controls(), []
        app_type = FleetApp if fleet else ProjectApp
        monkeypatch.setattr(
            app_type, "run", lambda self: (_ for _ in ()).throw(error())
        )
        monkeypatch.setattr(
            app_module, "ProjectObserver", lambda run, settings: selected.observer
        )
        monkeypatch.setattr(
            app_module, "run_plain", lambda *args, **kwargs: plain_calls.append(args)
        )
        monkeypatch.setattr(sys, "stdin", Terminal(selected.first.run.run_id + "\n"))
        monkeypatch.setattr(sys, "stdout", Terminal())
        with pytest.raises(error):
            attach(
                registry=Registry((selected.first.run,)),
                root=None if fleet else selected.first.run.root,
                controls=controls,
            )
        identities_alive(selected)
        assert plain_calls == [] and controls.calls == []


def test_ordinary_fleet_ui_failure_uses_one_bounded_selection(
    isolated_config: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with selected_run(isolated_config, "completed") as selected:
        chosen, observer = selected.first.run, selected.observer
        probe = PollProbe(observer)
        other = replace(chosen, run_id="other", root=chosen.root / "other")
        source = Terminal(f"{chosen.run_id}\nother\n")
        output, error, constructed = Terminal(), io.StringIO(), []

        class CompletingApp:
            def __init__(
                self, current: object, *args: object, **kwargs: object
            ) -> None:
                constructed.append(current)
                self.return_value = None

            def run(self) -> AttachResult:
                identities_alive(selected)
                (selected.base / "release").touch()
                self.return_value = run_plain(observer, poll_interval=0)
                return self.return_value

        monkeypatch.setattr(
            FleetApp,
            "run",
            lambda self: (_ for _ in ()).throw(ValueError("fleet failed")),
        )
        monkeypatch.setattr(app_module, "ProjectApp", CompletingApp)
        monkeypatch.setattr(
            app_module, "ProjectObserver", lambda run, settings: observer
        )
        monkeypatch.setattr(observer, "close", probe.close)
        monkeypatch.setattr(sys, "stdin", source)
        monkeypatch.setattr(sys, "stdout", output)
        monkeypatch.setattr(sys, "stderr", error)
        result = attach(
            registry=Registry((other, chosen)),
            root=None,
            controls=Controls(),
            poll_interval=0,
        )
        notices = [
            line
            for line in (output.getvalue() + error.getvalue()).splitlines()
            if "plain" in line.lower()
        ]
        assert result == AttachResult("completed", 0) and constructed == [observer]
        assert source.read() == "other\n" and "close" in probe.events
        assert len(notices) == 1


def test_plain_prints_only_distinct_frames_and_always_prints_terminal_frame(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = FleetRun("selected", tmp_path, "generic", "stamp", 123, "start")
    lane = ActivityLane("audit", "Visible audit", "running", "checking")
    observer = Observer(
        [
            view(run),
            replace(view(run), duration_seconds=120.0001),
            replace(view(run), tasks_completed=2),
            replace(view(run), tasks_completed=2, lanes=(lane,)),
            replace(view(run), status="completed", ended=True, tasks_completed=3),
        ]
    )
    read_fd, write_fd = os.pipe()
    source, output = os.fdopen(read_fd, "r"), io.StringIO()
    monkeypatch.setattr(sys, "stdin", source)
    monkeypatch.setattr(sys, "stdout", output)
    try:
        result = run_plain(observer, poll_interval=0)
    finally:
        os.close(write_fd)
        source.close()
    text = output.getvalue()
    assert result == AttachResult("completed", 0) and observer.polls == 5
    assert text.count("selected.md") == 4
    assert "2 / 3" in text and "Visible audit" in text and "completed" in text.lower()
