from __future__ import annotations

import asyncio
import io
import os
import pty
import sys
import termios
import xml.etree.ElementTree as ET
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any

import pytest

from ovcaq.runtime.registry import (
    FleetEntry,
    FleetRun,
    ProcessIdentity,
    RegistrySnapshot,
)
from ovcaq.tui import app as app_module
from ovcaq.tui.app import (
    AttachResult,
    ControlService,
    FleetApp,
    ProjectApp,
    ThemeResult,
    attach,
    load_theme,
    run_plain,
    run_plain_fleet,
    save_theme,
    theme_path,
)
from ovcaq.tui.discovery import FleetView
from ovcaq.tui.model import ProjectView


def _run(root: Path, name: str = "selected") -> FleetRun:
    return FleetRun(name, root, "generic", "2026-10-03T12:00:00Z", 12345, "start")


def _view(run: FleetRun) -> ProjectView:
    return ProjectView(
        run=run,
        status="running",
        phase=None,
        next_phase=None,
        prd="00008",
        revision=17,
        tasks_completed=1,
        tasks_total=3,
        review_cycle=0,
        provider="generic",
        duration_seconds=None,
        usage=None,
        lanes=(),
        capabilities=(),
        attention=None,
        telemetry="complete",
        gaps=(),
    )


THEMES = (
    "textual-dark",
    "textual-light",
    "nord",
    "gruvbox",
    "catppuccin-mocha",
)


def _screen_text(app: FleetApp | ProjectApp) -> str:
    screenshot = ET.fromstring(app.export_screenshot())
    return " ".join(
        "".join(element.itertext())
        for element in screenshot.iter("{http://www.w3.org/2000/svg}text")
    )


class Observer:
    def __init__(self, view: ProjectView) -> None:
        self.current = view
        self.polls = 0
        self.closed = False
        self.followups: list[ProjectView | BaseException] = []

    def poll(self) -> ProjectView:
        self.polls += 1
        if self.followups:
            next_view = self.followups.pop(0)
            if isinstance(next_view, BaseException):
                raise next_view
            self.current = next_view
        return self.current

    def close(self) -> None:
        self.closed = True


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


class Registry:
    def __init__(self, runs: tuple[FleetRun, ...]) -> None:
        self.runs = runs
        self.snapshots = 0

    def snapshot(self) -> RegistrySnapshot:
        self.snapshots += 1
        return RegistrySnapshot(
            tuple(
                FleetEntry(
                    1,
                    run.root,
                    run.pid,
                    run.process_start,
                    run.run_id,
                    run.agent,
                    run.started_at,
                )
                for run in self.runs
            ),
            (),
            (),
        )


class Terminal(io.StringIO):
    def isatty(self) -> bool:
        return True


class InterruptingInput(io.StringIO):
    def readline(self, size: int = -1) -> str:
        raise KeyboardInterrupt


@pytest.fixture(autouse=True)
def isolated_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg-state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))


def test_fleet_navigation_returns_the_exact_highlighted_run(tmp_path: Path) -> None:
    first, second = _run(tmp_path / "a", "first"), _run(tmp_path / "b", "second")
    app = FleetApp(FleetView((first, second), (), ()))

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.press("down", "up", "down", "enter")

    asyncio.run(exercise())
    assert app.return_value is second


@pytest.mark.parametrize("key", ["q", "ctrl+c", "ctrl+d"])
def test_fleet_detaches_without_selecting_a_run(tmp_path: Path, key: str) -> None:
    app = FleetApp(FleetView((_run(tmp_path),), (), ()))

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.press(key)
            await pilot.pause()
            assert not app.is_running

    asyncio.run(exercise())
    assert app.return_value is None


@pytest.mark.parametrize("key", ["q", "ctrl+c", "ctrl+d"])
def test_project_detaches_without_stopping_its_run(tmp_path: Path, key: str) -> None:
    observer, controls = Observer(_view(_run(tmp_path))), Controls()
    app = ProjectApp(observer, controls, poll_interval=0.01)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.press(key)

    asyncio.run(exercise())
    assert app.return_value == AttachResult("detached", 0)
    assert controls.calls == []


def test_project_polls_and_controls_only_the_last_observed_run(tmp_path: Path) -> None:
    run = _run(tmp_path)
    observer, controls = Observer(_view(run)), Controls()
    observer.current = replace(
        observer.current, tasks_completed=137, tasks_total=251, telemetry="raw-only"
    )
    service: ControlService = controls
    app = ProjectApp(observer, service, poll_interval=0.01)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            initial = _screen_text(app)
            for value in (run.run_id, "running", "137", "251", "raw-only"):
                assert value in initial
            await pilot.press("p")
            assert controls.calls == [("pause", run, 17, None)]
            observer.current = replace(
                observer.current,
                status="paused",
                revision=24,
                tasks_completed=149,
                telemetry="partial",
            )
            await pilot.pause(0.05)
            updated = _screen_text(app)
            for value in (run.run_id, "paused", "149", "251", "partial"):
                assert value in updated
            assert "137" not in updated and "raw-only" not in updated
            await pilot.press("p")
            assert controls.calls == [("pause", run, 17, None), ("resume", run, 24)]
            assert all(call[1] is run for call in controls.calls)
            await pilot.press("q")

    asyncio.run(exercise())
    assert observer.polls > 1
    assert app.return_value == AttachResult("detached", 0)


@pytest.mark.parametrize("cancel", ["n", "escape"])
def test_stop_requires_confirmation_and_cancellation_never_stops(
    tmp_path: Path, cancel: str
) -> None:
    run = _run(tmp_path)
    observer, controls = Observer(_view(run)), Controls()
    app = ProjectApp(observer, controls, poll_interval=0.01)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.press("s")
            assert controls.calls == []
            await pilot.press(cancel)
            assert controls.calls == []
            await pilot.press("s")
            replacement = _run(tmp_path / "replacement", "replacement")
            observer.current = replace(observer.current, run=replacement, revision=99)
            await pilot.pause(0.05)
            await pilot.press("y")
            assert controls.calls == [("stop", run)]
            assert controls.calls[0][1] is run
            await pilot.press("q")

    asyncio.run(exercise())
    assert controls.calls == [("stop", run)]


def test_question_mark_toggles_visible_help_without_controls(tmp_path: Path) -> None:
    controls = Controls()
    app = ProjectApp(Observer(_view(_run(tmp_path))), controls, poll_interval=60)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            before = app.export_screenshot()
            await pilot.press("?")
            opened = app.export_screenshot()
            assert opened != before
            assert "pause" in opened.lower() and "stop" in opened.lower()
            await pilot.press("?")
            assert app.export_screenshot() != opened
            await pilot.press("q")

    asyncio.run(exercise())
    assert controls.calls == []


def test_project_completion_exits_without_stopping(tmp_path: Path) -> None:
    observer, controls = Observer(_view(_run(tmp_path))), Controls()
    app = ProjectApp(observer, controls, poll_interval=0.01)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            observer.current = replace(
                observer.current, status="completed", revision=18
            )
            await pilot.pause(0.05)

    asyncio.run(exercise())
    assert app.return_value == AttachResult("completed", 0)
    assert controls.calls == []


@pytest.mark.parametrize("text", ["second\nfirst\n", "second\n"])
def test_plain_fleet_reads_one_line_and_returns_exact_selection(
    tmp_path: Path, text: str
) -> None:
    first, second = _run(tmp_path / "a", "first"), _run(tmp_path / "b", "second")
    source, output = io.StringIO(text), io.StringIO()
    result = run_plain_fleet(
        FleetView((first, second), (), ()), input_stream=source, output_stream=output
    )
    assert result is second
    assert source.read() == ("first\n" if text.endswith("first\n") else "")
    assert "first" in output.getvalue() and "second" in output.getvalue()


@pytest.mark.parametrize("text", ["", "\n", "missing\n", "x" * 4097 + "\nselected\n"])
def test_plain_fleet_invalid_or_eof_input_never_selects_a_run(
    tmp_path: Path, text: str
) -> None:
    source = io.StringIO(text)
    result = run_plain_fleet(
        FleetView((_run(tmp_path),), (), ()),
        input_stream=source,
        output_stream=io.StringIO(),
    )
    assert result is None
    assert source.tell() <= 4096


def test_plain_fleet_interrupt_never_selects_a_run(tmp_path: Path) -> None:
    result = run_plain_fleet(
        FleetView((_run(tmp_path),), (), ()),
        input_stream=InterruptingInput(),
        output_stream=io.StringIO(),
    )
    assert result is None


def test_plain_project_polls_until_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    observer = Observer(_view(_run(tmp_path)))
    observer.followups = [
        observer.current,
        replace(observer.current, status="completed"),
    ]
    monkeypatch.setattr(sys, "stdin", Terminal())
    assert run_plain(observer, poll_interval=0) == AttachResult("completed", 0)
    assert observer.polls == 2
    output = capsys.readouterr().out
    assert "running" in output and "completed" in output
    assert output.index("running") < output.index("completed")
    assert output.count(observer.current.run.run_id) >= 2


@pytest.mark.parametrize("error", [KeyboardInterrupt(), EOFError()])
def test_plain_project_interrupt_or_eof_is_detach(
    tmp_path: Path, error: BaseException
) -> None:
    observer = Observer(_view(_run(tmp_path)))
    observer.followups = [error]
    assert run_plain(observer, poll_interval=0) == AttachResult("detached", 0)


def test_plain_project_observation_failure_returns_nonzero(tmp_path: Path) -> None:
    observer = Observer(_view(_run(tmp_path)))
    observer.followups = [RuntimeError("viewer failed")]
    result = run_plain(observer, poll_interval=0)
    assert result.reason == "failed"
    assert result.exit_code != 0


@pytest.mark.parametrize("selector", ["root", "run", "both"])
@pytest.mark.parametrize("failure", [ImportError, RuntimeError])
def test_attach_ui_failure_falls_back_with_same_selection_and_observer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selector: str,
    failure: type[Exception],
) -> None:
    run, other = _run(tmp_path / "selected"), _run(tmp_path / "other", "other")
    observer, controls = Observer(_view(run)), Controls()
    constructed: list[FleetRun] = []

    def observe(selected: FleetRun, settings: object) -> Observer:
        constructed.append(selected)
        return observer

    def fail_viewer(self: object, *args: object, **kwargs: object) -> None:
        assert constructed == [run]
        observer.poll()
        observer.followups = [replace(observer.current, status="completed")]
        raise failure("terminal unavailable")

    monkeypatch.setattr(app_module, "ProjectObserver", observe)
    monkeypatch.setattr(ProjectApp, "run", fail_viewer)
    monkeypatch.setattr(sys, "stdin", Terminal())
    monkeypatch.setattr(sys, "stdout", Terminal())
    result = attach(
        registry=Registry((other, run)),
        root=run.root if selector != "run" else None,
        run_id=run.run_id if selector != "root" else None,
        controls=controls,
        poll_interval=0,
    )
    assert result == AttachResult("completed", 0)
    assert constructed == [run]
    assert observer.polls >= 2
    assert observer.closed
    assert controls.calls == []


def test_fleet_ui_failure_selects_one_line_then_views_that_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second = _run(tmp_path / "a", "first"), _run(tmp_path / "b", "second")
    controls, constructed = Controls(), []
    observer = Observer(replace(_view(second), status="completed"))

    def observe(run: FleetRun, settings: object) -> Observer:
        constructed.append(run)
        return observer

    def fail_viewer(self: object, *args: object, **kwargs: object) -> None:
        raise RuntimeError("terminal unavailable")

    source = Terminal("second\nfirst\n")
    monkeypatch.setattr(app_module, "ProjectObserver", observe)
    monkeypatch.setattr(FleetApp, "run", fail_viewer)
    monkeypatch.setattr(sys, "stdin", source)
    monkeypatch.setattr(sys, "stdout", Terminal())
    registry = Registry((first, second))
    result = attach(registry=registry, root=None, controls=controls)
    assert result.exit_code == 0
    assert constructed == [second]
    assert registry.snapshots == 1
    assert source.read() == "first\n"
    assert controls.calls == []


def test_post_mount_failure_restores_terminal_before_plain_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, controls = _run(tmp_path), Controls()
    observer = Observer(_view(run))
    master_fd, slave_fd = pty.openpty()
    tty_input = os.fdopen(os.dup(slave_fd), "r")
    original = termios.tcgetattr(tty_input.fileno())
    output, error, events = Terminal(), io.StringIO(), []

    def crash_after_mount(self: object, *args: object, **kwargs: object) -> None:
        raw = termios.tcgetattr(tty_input.fileno())
        raw[3] &= ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(tty_input.fileno(), termios.TCSANOW, raw)
        events.append("mounted")
        raise RuntimeError("render loop crashed")

    def plain(selected: Observer, *, poll_interval: float = 0.25) -> AttachResult:
        assert selected is observer
        assert termios.tcgetattr(tty_input.fileno())[3] == original[3]
        events.append("plain")
        return AttachResult("fallback", 7)

    monkeypatch.setattr(app_module, "ProjectObserver", lambda run, settings: observer)
    monkeypatch.setattr(ProjectApp, "run", crash_after_mount)
    monkeypatch.setattr(app_module, "run_plain", plain)
    monkeypatch.setattr(sys, "stdin", tty_input)
    monkeypatch.setattr(sys, "stdout", output)
    monkeypatch.setattr(sys, "stderr", error)
    try:
        result = attach(registry=Registry((run,)), root=run.root, controls=controls)
    finally:
        termios.tcsetattr(tty_input.fileno(), termios.TCSANOW, original)
        tty_input.close()
        os.close(master_fd)
        os.close(slave_fd)
    assert result == AttachResult("fallback", 7)
    assert events == ["mounted", "plain"]
    notices = [
        line for line in (output.getvalue() + error.getvalue()).splitlines() if line
    ]
    assert len(notices) == 1 and "plain" in notices[0].lower()
    assert observer.closed and controls.calls == []


def test_control_error_remains_visible_without_retargeting(tmp_path: Path) -> None:
    run = _run(tmp_path)

    class RejectingControls(Controls):
        def pause(
            self, run: FleetRun, expected_revision: int, reason: str | None = None
        ) -> None:
            super().pause(run, expected_revision, reason)
            raise RuntimeError("selected run became stale")

    controls = RejectingControls()
    app = ProjectApp(Observer(_view(run)), controls, poll_interval=0.01)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            for _ in range(100):
                if "00008" in _screen_text(app):
                    break
                await pilot.pause(0.01)
            assert "00008" in _screen_text(app)
            await pilot.press("p")
            await pilot.pause(0.05)
            assert "stale" in app.export_screenshot().lower()
            assert controls.calls == [("pause", run, 17, None)]
            await pilot.press("q")

    asyncio.run(exercise())
    assert app.return_value == AttachResult("detached", 0)
    assert controls.calls[0][1] is run


def test_attach_viewer_failure_returns_nonzero_without_stopping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, controls = _run(tmp_path), Controls()
    observer = Observer(_view(run))
    observer.followups = [RuntimeError("viewer failed")]

    def fail_viewer(self: object, *args: object, **kwargs: object) -> None:
        raise RuntimeError("terminal unavailable")

    monkeypatch.setattr(app_module, "ProjectObserver", lambda run, settings: observer)
    monkeypatch.setattr(ProjectApp, "run", fail_viewer)
    monkeypatch.setattr(sys, "stdin", Terminal())
    monkeypatch.setattr(sys, "stdout", Terminal())
    result = attach(registry=Registry((run,)), root=run.root, controls=controls)
    assert result.reason == "failed"
    assert result.exit_code != 0
    assert controls.calls == []
    assert observer.closed


def test_attach_normal_detach_closes_the_selected_observer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, controls = _run(tmp_path), Controls()
    observer = Observer(_view(run))
    monkeypatch.setattr(app_module, "ProjectObserver", lambda run, settings: observer)
    monkeypatch.setattr(
        ProjectApp, "run", lambda *args, **kwargs: AttachResult("detached", 0)
    )
    monkeypatch.setattr(sys, "stdin", Terminal())
    monkeypatch.setattr(sys, "stdout", Terminal())
    result = attach(registry=Registry((run,)), root=run.root, controls=controls)
    assert result == AttachResult("detached", 0)
    assert observer.closed
    assert controls.calls == []


def test_theme_result_is_a_frozen_slotted_value() -> None:
    result = ThemeResult("nord", None)

    assert result == ThemeResult(name="nord", gap=None)
    assert not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        result.name = "gruvbox"


def test_relative_config_root_resolves_against_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative-config")

    assert theme_path() == (tmp_path / "relative-config/ovcaq/theme").resolve()


def test_missing_theme_uses_an_allowlisted_default_without_a_gap() -> None:
    result = load_theme()

    assert result.name in THEMES
    assert result.gap is None
    assert not theme_path().exists()


@pytest.mark.parametrize("name", THEMES)
def test_allowlisted_theme_round_trips_with_private_permissions(name: str) -> None:
    result = save_theme(name)
    path = theme_path()

    assert result == ThemeResult(name, None)
    assert load_theme() == ThemeResult(name, None)
    assert path.is_file() and not path.is_symlink()
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize("name", ["", "nord\n", "NORD", "dracula", "../nord"])
def test_invalid_theme_name_does_not_mutate_existing_content(name: str) -> None:
    assert save_theme("gruvbox") == ThemeResult("gruvbox", None)
    path = theme_path()
    original = path.read_bytes()

    result = save_theme(name)

    assert result.name is None
    assert result.gap
    assert path.read_bytes() == original
    assert load_theme() == ThemeResult("gruvbox", None)


@pytest.mark.parametrize(
    "content",
    ["secret-invalid-theme\n", "x" * 257],
    ids=["invalid", "oversized"],
)
def test_invalid_or_oversized_theme_returns_a_sanitized_gap(content: str) -> None:
    path = theme_path()
    path.parent.mkdir(parents=True)
    path.write_text(content)

    result = load_theme()

    assert result.name is None
    assert result.gap
    assert content.strip() not in result.gap


def test_symlinked_theme_file_is_rejected_without_reading_target(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside-theme"
    outside.write_text("nord\n")
    path = theme_path()
    path.parent.mkdir(parents=True)
    path.symlink_to(outside)

    result = load_theme()

    assert result.name is None
    assert result.gap
    assert outside.read_text() == "nord\n"


def test_trusted_xdg_config_alias_loads_intended_theme(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    actual = tmp_path / "actual-config"
    (actual / "ovcaq").mkdir(parents=True)
    (actual / "ovcaq/theme").write_text("nord\n")
    linked = tmp_path / "linked-config"
    linked.symlink_to(actual, target_is_directory=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(linked))

    result = load_theme()

    assert result == ThemeResult("nord", None)


def test_non_regular_theme_file_returns_a_visible_gap() -> None:
    path = theme_path()
    path.mkdir(parents=True)

    result = load_theme()

    assert result.name is None
    assert result.gap


def test_unavailable_theme_file_returns_a_visible_gap() -> None:
    path = theme_path()
    path.parent.mkdir(parents=True)
    path.write_text("nord\n")
    path.chmod(0)
    try:
        result = load_theme()
    finally:
        path.chmod(0o600)

    assert result.name is None
    assert result.gap


def test_theme_save_atomically_replaces_the_file_without_temp_artifacts() -> None:
    assert save_theme("textual-dark") == ThemeResult("textual-dark", None)
    path = theme_path()
    original_inode = path.stat().st_ino

    assert save_theme("catppuccin-mocha") == ThemeResult("catppuccin-mocha", None)

    assert path.stat().st_ino != original_inode
    assert set(path.parent.iterdir()) == {path}
    assert load_theme() == ThemeResult("catppuccin-mocha", None)


def test_theme_save_rejects_an_existing_symlink_without_following_it(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside-theme"
    outside.write_text("sentinel")
    path = theme_path()
    path.parent.mkdir(parents=True)
    path.symlink_to(outside)

    result = save_theme("nord")

    assert result.name is None
    assert result.gap
    assert path.is_symlink()
    assert outside.read_text() == "sentinel"


def test_invalid_theme_gap_is_visible_without_blocking_project_ui() -> None:
    path = theme_path()
    path.parent.mkdir(parents=True)
    path.write_text("private-invalid-value")
    expected = load_theme()
    app = ProjectApp(Observer(_view(_run(path.parent))), Controls(), poll_interval=60)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            screen = _screen_text(app)
            assert expected.gap is not None and expected.gap in screen
            assert "private-invalid-value" not in screen
            await pilot.press("q")

    asyncio.run(exercise())
    assert app.return_value == AttachResult("detached", 0)


def test_invalid_theme_does_not_block_attach_or_plain_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = theme_path()
    path.parent.mkdir(parents=True)
    path.write_text("invalid")
    run, controls = _run(tmp_path), Controls()
    observer = Observer(_view(run))
    observer.followups = [replace(observer.current, status="completed")]

    monkeypatch.setattr(app_module, "ProjectObserver", lambda run, settings: observer)
    monkeypatch.setattr(
        ProjectApp,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("no ui")),
    )
    monkeypatch.setattr(sys, "stdin", Terminal())
    monkeypatch.setattr(sys, "stdout", Terminal())

    assert attach(registry=Registry((run,)), root=run.root, controls=controls) == (
        AttachResult("completed", 0)
    )
    assert observer.closed
    assert controls.calls == []


def test_rendered_and_source_ui_text_is_ovcaq_and_provider_neutral(
    tmp_path: Path,
) -> None:
    project = ProjectApp(Observer(_view(_run(tmp_path))), Controls(), poll_interval=60)
    fleet = FleetApp(FleetView((_run(tmp_path),), (), ()))

    async def render() -> str:
        async with project.run_test() as pilot:
            project_text = _screen_text(project)
            await pilot.press("q")
        async with fleet.run_test() as pilot:
            fleet_text = _screen_text(fleet)
            await pilot.press("q")
        return f"{project_text} {fleet_text}"

    rendered = asyncio.run(render())
    assert "ovcaq" in rendered.lower()
    assert app_module.__file__ is not None
    source = Path(app_module.__file__).read_text()
    forbidden = (
        "tracon",
        "autoclaude",
        "claude",
        "anthropic",
        "codex",
        "pbcopy",
        "clipboard",
    )
    assert not any(term in rendered.lower() for term in forbidden)
    assert not any(term in source.lower() for term in forbidden)
