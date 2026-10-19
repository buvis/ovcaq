"""Headless UI contracts at a deliberately blocked observation boundary."""

from __future__ import annotations

import asyncio
import io
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from ovcaq.runtime.registry import FleetEntry, FleetRun, RegistrySnapshot
from ovcaq.tui import app as app_module
from ovcaq.tui.app import AttachResult, ProjectApp, attach
from ovcaq.tui.model import ActivityLane, ProjectView


def view_for(root: Path) -> ProjectView:
    return ProjectView(
        run=FleetRun(
            "selected", root, "generic", "2026-10-03T12:00:00Z", 12345, "start"
        ),
        status="running",
        phase="build",
        next_phase="build",
        prd="selected.md",
        revision=17,
        tasks_completed=1,
        tasks_total=3,
        review_cycle=0,
        provider="generic",
        duration_seconds=120.0,
        usage=None,
        lanes=(ActivityLane("verifier", "Verifier", "running", "Checking output"),),
        capabilities=(),
        attention=None,
        telemetry="partial",
        gaps=(),
    )


class BlockedObserver:
    def __init__(self, root: Path) -> None:
        self.view = view_for(root)
        self.entered = threading.Event()
        self.release = threading.Event()
        self.guard = threading.Lock()
        self.polls = self.active = self.maximum = 0
        self.started = 0.0
        self.closed = False
        self.violations: list[str] = []
        self.complete = False

    def poll(self) -> ProjectView:
        with self.guard:
            self.polls += 1
            number = self.polls
            self.active += 1
            self.maximum = max(self.maximum, self.active)
            if self.closed:
                self.violations.append("poll after close")
        try:
            if number == 1:
                self.started = time.monotonic()
                self.entered.set()
                self.release.wait(5)
            return replace(
                self.view, status="completed" if self.complete else "running"
            )
        finally:
            with self.guard:
                self.active -= 1

    def close(self) -> None:
        with self.guard:
            if self.active:
                self.violations.append("close raced observation")
            self.closed = True


class Controls:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def pause(
        self, run: FleetRun, expected_revision: int, reason: str | None = None
    ) -> None:
        self.calls.append(("pause", run, expected_revision, reason))

    def resume(self, run: FleetRun, expected_revision: int) -> None:
        self.calls.append(("resume", run, expected_revision))

    def stop(self, run: FleetRun) -> None:
        self.calls.append(("stop", run))
        pytest.fail("viewing/detaching must not stop a supervisor")


class Registry:
    def __init__(self, run: FleetRun) -> None:
        self.run = run

    def snapshot(self) -> RegistrySnapshot:
        run = self.run
        return RegistrySnapshot(
            (
                FleetEntry(
                    1,
                    run.root,
                    run.pid,
                    run.process_start,
                    run.run_id,
                    run.agent,
                    run.started_at,
                ),
            ),
            (),
            (),
        )


class Terminal(io.StringIO):
    def isatty(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))


async def wait_for(predicate: Callable[[], bool]) -> None:
    async with asyncio.timeout(2):
        while not predicate():
            await asyncio.sleep(0.005)


@pytest.mark.parametrize("key", ["q", "ctrl+c", "ctrl+d"])
def test_help_and_detach_respond_before_blocked_poll_finishes(
    tmp_path: Path,
    key: str,
    record_property: Callable[[str, object], None],
) -> None:
    observer, controls = BlockedObserver(tmp_path), Controls()
    app = ProjectApp(observer, controls, poll_interval=0.01)

    async def exercise() -> None:
        try:
            async with app.run_test() as pilot:
                try:
                    await wait_for(observer.entered.is_set)
                    before = app.export_screenshot()
                    await pilot.press("?")
                    opened = app.export_screenshot()
                    assert opened != before and "pause" in opened.lower()
                    pressed = asyncio.create_task(pilot.press(key))
                    await wait_for(lambda: app.return_value is not None)
                    latency = time.monotonic() - observer.started
                    record_property("blocked_poll_detach_seconds", latency)
                    assert latency < 4.0, f"blocked-poll response took {latency:.3f}s"
                    assert observer.active == 1, (
                        "detach was processed only after observation"
                    )
                finally:
                    observer.release.set()
                await pressed
        finally:
            observer.release.set()

    asyncio.run(exercise())
    assert app.return_value == AttachResult("detached", 0)
    assert controls.calls == []
    assert observer.maximum == 1 and observer.active == 0
    assert observer.violations == []


def test_poll_is_single_flight_and_completed_view_preserves_selected_controls(
    tmp_path: Path,
) -> None:
    observer, controls = BlockedObserver(tmp_path), Controls()
    app = ProjectApp(observer, controls, poll_interval=0.01)
    original = observer.view

    async def exercise() -> None:
        async with app.run_test() as pilot:
            try:
                await wait_for(observer.entered.is_set)
                await asyncio.sleep(0.15)
                assert observer.active == observer.maximum == observer.polls == 1
                observer.view = replace(original, revision=42, tasks_completed=2)
            finally:
                observer.release.set()
            await wait_for(lambda: observer.polls >= 2)
            await pilot.pause()
            assert "selected.md" in app.export_screenshot()
            assert "Verifier" in app.export_screenshot()
            await pilot.press("p")
            assert controls.calls == [("pause", original.run, 42, None)]
            await pilot.press("q")
        stopped_at = observer.polls
        await asyncio.sleep(0.05)
        assert observer.polls == stopped_at

    try:
        asyncio.run(exercise())
    finally:
        observer.release.set()
    assert original.revision == 17 and original.tasks_completed == 1
    assert observer.maximum == 1 and observer.active == 0
    assert app.return_value == AttachResult("detached", 0)


def headless_exit(
    app: ProjectApp, observer: BlockedObserver, failure: bool
) -> AttachResult | None:
    async def exercise() -> None:
        async with app.run_test() as pilot:
            await wait_for(observer.entered.is_set)
            # A finite external read may finish during viewer shutdown.
            release = threading.Timer(0.2, observer.release.set)
            release.start()
            if failure:
                raise RuntimeError("terminal render failed")
            await pilot.press("q")

    asyncio.run(exercise())
    return app.return_value


@pytest.mark.parametrize("failure", [False, True])
def test_attach_detach_or_fallback_finishes_observation_before_close_or_plain_poll(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: bool,
) -> None:
    observer, controls = BlockedObserver(tmp_path), Controls()
    selected = observer.view.run
    original_plain = app_module.run_plain
    plain_entries: list[FleetRun] = []

    def plain(current: BlockedObserver, *, poll_interval: float) -> AttachResult:
        assert current is observer and not current.closed
        assert current.active == 0, "plain fallback raced the previous observer poll"
        plain_entries.append(current.view.run)
        current.complete = True
        return original_plain(current, poll_interval=poll_interval)

    monkeypatch.setattr(app_module, "ProjectObserver", lambda run, settings: observer)
    monkeypatch.setattr(
        ProjectApp, "run", lambda self: headless_exit(self, observer, failure)
    )
    monkeypatch.setattr(app_module, "run_plain", plain)
    monkeypatch.setattr(sys, "stdin", Terminal())
    monkeypatch.setattr(sys, "stdout", Terminal())
    try:
        result = attach(
            registry=Registry(selected),
            root=tmp_path,
            controls=controls,
            poll_interval=0.01,
        )
    finally:
        observer.release.set()
    polls_at_close = observer.polls
    time.sleep(0.05)
    assert result == AttachResult("completed" if failure else "detached", 0)
    assert plain_entries == ([selected] if failure else [])
    assert all(run is selected for run in plain_entries)
    assert observer.closed and observer.active == 0 and observer.maximum == 1
    assert observer.polls == polls_at_close and observer.violations == []
    assert controls.calls == []
