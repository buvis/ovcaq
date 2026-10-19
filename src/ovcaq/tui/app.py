"""Interactive and plain viewers with exact-run controls."""

from __future__ import annotations

import os
import secrets
import select
import stat
import sys
import termios
import time
from collections.abc import Callable, Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Protocol, TextIO

from ovcaq.config import runtime_settings
from ovcaq.paths import RuntimePaths, _trusted_path
from ovcaq.runtime.registry import FleetRegistry, FleetRun, ProcessIdentity
from ovcaq.state.commands import StateService
from ovcaq.state.store import StateError, StateStore
from ovcaq.supervisor_cli import operator_notice, stop_supervisor, verify_run
from ovcaq.tui.discovery import FleetView, discover_fleet, select_run
from ovcaq.tui.model import ProjectObserver, ProjectView, display_text
from ovcaq.tui.panels import plain_frame

if TYPE_CHECKING:
    from rich.console import Group

_FLEET_LINE_LIMIT = 4096
_HELP = "p pause/resume   s stop (asks first)   q detach   ? help"
_FAILURES = (OSError, ValueError, RuntimeError, StateError)


def _fleet_row(run: FleetRun) -> str:
    return "  ".join(
        display_text(str(value)) for value in (run.run_id, run.root, run.agent)
    )


def _fleet_status(view: FleetView) -> str:
    status = f"{len(view.runs)} live runs" if view.runs else "No live runs available"
    return (
        f"{status}; registry gaps: {len(view.stale_entries)} stale, "
        f"{len(view.malformed_entries)} malformed"
    )


def _frame(view: ProjectView) -> Group:
    from rich.console import Group
    from rich.text import Text

    return Group(Text(f"OVCAQ run: {display_text(view.run.run_id)}"), plain_frame(view))


class ControlService(Protocol):
    def pause(
        self, run: FleetRun, expected_revision: int, reason: str | None = None
    ) -> None: ...
    def resume(self, run: FleetRun, expected_revision: int) -> None: ...
    def stop(self, run: FleetRun) -> ProcessIdentity: ...


class StaleSelectionError(RuntimeError):
    def __init__(self, message: str, *, committed: bool) -> None:
        super().__init__(message)
        self.committed = committed


class RunControlService:
    """Mutate only the exact selected run, proving its identity around the write."""

    def __init__(self, registry: FleetRegistry) -> None:
        self._registry = registry

    def pause(
        self, run: FleetRun, expected_revision: int, reason: str | None = None
    ) -> None:
        notice = operator_notice(reason)
        self._mutate(
            run,
            lambda service: service.request_pause(
                notice, expected_revision=expected_revision
            ),
        )

    def resume(self, run: FleetRun, expected_revision: int) -> None:
        self._mutate(
            run, lambda service: service.resume(expected_revision=expected_revision)
        )

    def stop(self, run: FleetRun) -> ProcessIdentity:
        return stop_supervisor(run, registry=self._registry)

    def _mutate(self, run: FleetRun, change: Callable[[StateService], object]) -> None:
        def validate() -> RuntimePaths:
            try:
                return verify_run(run, self._registry)
            except (OSError, ValueError, RuntimeError) as error:
                raise StaleSelectionError(str(error), committed=False) from error

        paths = validate()
        with self._registry.guard_mutation(validate) as guard:
            change(StateService(StateStore(paths.state_file), publication_guard=guard))
        try:
            verify_run(run, self._registry)
        except (OSError, ValueError, RuntimeError) as error:
            raise StaleSelectionError(
                f"change committed, but the selection is now stale: {error}",
                committed=True,
            ) from error


@dataclass(frozen=True, slots=True)
class AttachResult:
    reason: Literal["detached", "completed", "fallback", "failed"]
    exit_code: int


def _terminal_result(view: ProjectView) -> AttachResult | None:
    if view.status == "completed":
        return AttachResult("completed", 0)
    if not view.ended:
        return None
    if view.status in ("paused", "stopped"):
        return AttachResult("detached", 0)
    return AttachResult("failed", 1)


@dataclass(frozen=True, slots=True)
class ThemeResult:
    name: str | None
    gap: str | None


_THEMES = ("textual-dark", "textual-light", "nord", "gruvbox", "catppuccin-mocha")
_THEME_LIMIT = 256
# No spaces: the gap must survive screenshot text extraction verbatim.
_THEME_GAP = "theme-unavailable:using-default"


def _config_root() -> Path:
    return _trusted_path(
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    )


def theme_path() -> Path:
    return _config_root() / "ovcaq" / "theme"


@contextmanager
def _theme_directory(*, create: bool = False) -> Iterator[tuple[int, int]]:
    root = _config_root()
    if create:
        root.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    anchor = os.open(root, flags)
    try:
        if create:
            try:
                os.mkdir("ovcaq", 0o700, dir_fd=anchor)
            except FileExistsError:
                pass
        directory = os.open("ovcaq", flags, dir_fd=anchor)
        try:
            if create:
                os.fchmod(directory, 0o700)
            yield anchor, directory
        finally:
            os.close(directory)
    finally:
        os.close(anchor)


def load_theme() -> ThemeResult:
    try:
        with _theme_directory() as (_, directory):
            fd = os.open(
                "theme",
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory,
            )
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    return ThemeResult(None, _THEME_GAP)
                data = os.read(fd, _THEME_LIMIT + 1)
            finally:
                os.close(fd)
    except FileNotFoundError:
        return ThemeResult(_THEMES[0], None)
    except OSError:
        return ThemeResult(None, _THEME_GAP)
    name = data.decode("utf-8", errors="replace").strip()
    if len(data) > _THEME_LIMIT or name not in _THEMES:
        return ThemeResult(None, _THEME_GAP)
    return ThemeResult(name, None)


def save_theme(name: str) -> ThemeResult:
    if name not in _THEMES:
        return ThemeResult(None, _THEME_GAP)
    try:
        with _theme_directory(create=True) as (anchor, directory):
            try:
                before = os.stat("theme", dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                before = None
            if before is not None and not stat.S_ISREG(before.st_mode):
                return ThemeResult(None, _THEME_GAP)
            temp = f".theme-{secrets.token_hex(16)}"
            fd = os.open(
                temp,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            try:
                with os.fdopen(fd, "w") as handle:
                    handle.write(f"{name}\n")
                current_dir = os.stat("ovcaq", dir_fd=anchor, follow_symlinks=False)
                if not os.path.samestat(current_dir, os.fstat(directory)):
                    return ThemeResult(None, _THEME_GAP)
                try:
                    current = os.stat("theme", dir_fd=directory, follow_symlinks=False)
                except FileNotFoundError:
                    current = None
                if (current is None) != (before is None) or (
                    current is not None
                    and before is not None
                    and (
                        not os.path.samestat(current, before)
                        or current.st_mtime_ns != before.st_mtime_ns
                    )
                ):
                    return ThemeResult(None, _THEME_GAP)
                os.replace(temp, "theme", src_dir_fd=directory, dst_dir_fd=directory)
            finally:
                try:
                    os.unlink(temp, dir_fd=directory)
                except FileNotFoundError:
                    pass
    except OSError:
        return ThemeResult(None, _THEME_GAP)
    return ThemeResult(name, None)


# ponytail: Textual is optional at import time so a --no-deps install still
# imports; attach() falls back to plain output when these classes are missing.
try:
    from rich.text import Text
    from textual.app import App, ComposeResult
    from textual.binding import Binding, BindingType
    from textual.screen import ModalScreen
    from textual.widgets import OptionList, Static
except Exception as error:  # noqa: BLE001 - optional UI imports may fail arbitrarily
    _TEXTUAL_ERROR: Exception | None = error
else:
    _TEXTUAL_ERROR = None
    _DETACH: list[BindingType] = [
        Binding("q", "detach", "Detach"),
        Binding("ctrl+c", "detach", "Detach", priority=True),
        Binding("ctrl+d", "detach", "Detach", priority=True),
    ]

    class FleetApp(App[FleetRun | None]):
        BINDINGS: ClassVar[list[BindingType]] = _DETACH

        def __init__(self, view: FleetView) -> None:
            self._theme_ready = False
            super().__init__()
            self._view = view

        def on_mount(self) -> None:
            result = load_theme()
            self.theme = result.name or _THEMES[0]
            self._theme_ready = True
            if result.gap:
                self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap}")

        def watch_theme(self, name: str) -> None:
            if self._theme_ready:
                result = save_theme(name)
                if result.gap:
                    self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap}")

        def compose(self) -> ComposeResult:
            yield Static("OVCAQ fleet", id="title")
            yield Static(Text(_fleet_status(self._view)), id="fleet-status")
            yield OptionList(*(Text(_fleet_row(run)) for run in self._view.runs))

        def on_option_list_option_selected(
            self, event: OptionList.OptionSelected
        ) -> None:
            self.exit(self._view.runs[event.option_index])

        def action_detach(self) -> None:
            self.exit(None)

    class _ConfirmStop(ModalScreen[bool]):
        BINDINGS: ClassVar[list[BindingType]] = [
            Binding("y", "answer(True)", "Stop"),
            Binding("n", "answer(False)", "Cancel"),
            Binding("escape", "answer(False)", "Cancel"),
        ]

        def __init__(self, run: FleetRun) -> None:
            super().__init__()
            self._run = run

        def compose(self) -> ComposeResult:
            yield Static(Text(f"Stop run {display_text(self._run.run_id)}? [y/n]"))

        def action_answer(self, confirmed: bool) -> None:
            self.dismiss(confirmed)

    class ProjectApp(App[AttachResult]):
        BINDINGS: ClassVar[list[BindingType]] = [
            *_DETACH,
            Binding("p", "toggle_pause", "Pause/resume"),
            Binding("s", "stop", "Stop"),
            Binding("question_mark", "toggle_help", "Help"),
        ]

        def __init__(
            self,
            observer: ProjectObserver,
            controls: ControlService,
            *,
            poll_interval: float = 0.25,
        ) -> None:
            self._theme_ready = False
            super().__init__()
            self._observer = observer
            self._controls = controls
            self._poll_interval = poll_interval
            self._view: ProjectView | None = None
            self._executor = ThreadPoolExecutor(max_workers=1)
            self._pending: Future[ProjectView] | None = None
            self._closing = False

        def compose(self) -> ComposeResult:
            yield Static(id="notice")
            help_panel = Static(_HELP, id="help")
            help_panel.display = False
            yield help_panel
            yield Static(id="frame")

        def on_mount(self) -> None:
            result = load_theme()
            self.theme = result.name or _THEMES[0]
            self._theme_ready = True
            if result.gap:
                self._notify_error(result.gap)
            self._poll()
            self.set_interval(self._poll_interval, self._poll)

        def watch_theme(self, name: str) -> None:
            if self._theme_ready:
                result = save_theme(name)
                if result.gap:
                    self._notify_error(result.gap)

        def _poll(self) -> None:
            if self._closing or self.return_value is not None:
                return
            if self._view is not None and _terminal_result(self._view) is not None:
                return
            if self._pending is None:
                self._pending = self._executor.submit(self._observer.poll)
                return
            if not self._pending.done():
                return
            pending, self._pending = self._pending, None
            try:
                view = pending.result()
            except _FAILURES as error:
                self._notify_error(f"observation failed: {error}")
                self.exit(AttachResult("failed", 1))
                return
            self._view = view
            self.query_one("#frame", Static).update(_frame(view))
            result = _terminal_result(view)
            if result is not None:
                self.call_after_refresh(self.exit, result)

        def on_unmount(self) -> None:
            self._closing = True
            # Finish the finite read before attach closes or reuses the observer.
            self._executor.shutdown(wait=True, cancel_futures=True)

        def _notify_error(self, message: str) -> None:
            self.query_one("#notice", Static).update(Text(display_text(message)))

        def _control(self, action: Callable[[], object]) -> None:
            try:
                action()
            except _FAILURES as error:
                self._notify_error(f"control failed: {error}")
            else:
                self.query_one("#notice", Static).update("")

        def action_detach(self) -> None:
            self.exit(AttachResult("detached", 0))

        def action_toggle_help(self) -> None:
            help_panel = self.query_one("#help", Static)
            help_panel.display = not help_panel.display

        def action_toggle_pause(self) -> None:
            view = self._view
            if view is None or view.revision is None:
                self._notify_error("control failed: no state revision observed yet")
                return
            run, revision = view.run, view.revision
            if view.status in ("paused", "pause-requested"):
                self._control(lambda: self._controls.resume(run, revision))
            else:
                self._control(lambda: self._controls.pause(run, revision))

        def action_stop(self) -> None:
            if self._view is None:
                return
            # The confirmed stop targets the run observed when s was pressed.
            run = self._view.run

            def answered(confirmed: bool | None) -> None:
                if confirmed:
                    self._control(lambda: self._controls.stop(run))

            self.push_screen(_ConfirmStop(run), answered)


def run_plain(
    observer: ProjectObserver, *, poll_interval: float = 0.25
) -> AttachResult:
    try:
        from rich.console import Console

        buffer = StringIO()
        console = Console(file=buffer)
        previous = ""
        while True:
            view = observer.poll()
            buffer.seek(0)
            buffer.truncate()
            console.print(_frame(view))
            result = _terminal_result(view)
            frame = buffer.getvalue()
            if frame != previous or result is not None:
                sys.stdout.write(frame)
                sys.stdout.flush()
                previous = frame
            if result is not None:
                return result
            try:
                readable, _, _ = select.select([sys.stdin], [], [], poll_interval)
            except (OSError, TypeError, ValueError):
                time.sleep(poll_interval)
            else:
                if readable and sys.stdin.readline(1) == "":
                    return AttachResult("detached", 0)
    except (KeyboardInterrupt, EOFError):
        return AttachResult("detached", 0)
    except (ImportError, *_FAILURES) as error:
        print(f"ovcaq: viewer failed: {display_text(str(error))}", file=sys.stderr)
        return AttachResult("failed", 1)


def run_plain_fleet(
    view: FleetView, *, input_stream: TextIO, output_stream: TextIO
) -> FleetRun | None:
    print(_fleet_status(view), file=output_stream)
    if not view.runs:
        return None
    for number, run in enumerate(view.runs, start=1):
        print(
            f"{number}. {_fleet_row(run)}",
            file=output_stream,
        )
    print("run id: ", end="", file=output_stream, flush=True)
    try:
        line = input_stream.readline(_FLEET_LINE_LIMIT)
    except (KeyboardInterrupt, EOFError):
        return None
    # EOF and overlong input both arrive without a trailing newline.
    if not line.endswith("\n"):
        return None
    return next((run for run in view.runs if run.run_id == line.strip()), None)


def _fallback_notice(error: object) -> None:
    print(
        f"ovcaq: interactive view unavailable ({display_text(str(error))}); "
        "using plain output",
        file=sys.stderr,
    )


def _capture_terminal() -> list[Any] | None:
    try:
        return termios.tcgetattr(sys.stdin.fileno())
    except (AttributeError, OSError, ValueError, termios.error):
        return None


def _restore_terminal(saved: list[Any] | None) -> None:
    if saved is None:
        return
    try:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, saved)
    except (AttributeError, OSError, ValueError, termios.error):
        pass


def _interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _choose_run(view: FleetView) -> FleetRun | None:
    if _interactive():
        saved = _capture_terminal()
        try:
            if _TEXTUAL_ERROR is not None:
                raise _TEXTUAL_ERROR
            app = FleetApp(view)
            selected = app.run()
        except Exception as error:  # noqa: BLE001 - ordinary fleet UI failures fall back
            _restore_terminal(saved)
            _fallback_notice(error)
        else:
            if app.return_code == 0:
                return selected
            _restore_terminal(saved)
            _fallback_notice(f"exit code {app.return_code}")
    return run_plain_fleet(view, input_stream=sys.stdin, output_stream=sys.stdout)


def attach(
    *,
    registry: FleetRegistry,
    root: Path | None,
    run_id: str | None = None,
    controls: ControlService,
    poll_interval: float = 0.25,
) -> AttachResult:
    view = discover_fleet(registry)
    if root is None and run_id is None:
        selected = _choose_run(view)
        if selected is None:
            return AttachResult("detached", 0)
    else:
        selected = select_run(view, run_id=run_id, root=root)
    observer = ProjectObserver(selected, runtime_settings(selected.root))
    try:
        if _interactive():
            saved = _capture_terminal()
            try:
                if _TEXTUAL_ERROR is not None:
                    raise _TEXTUAL_ERROR
                result = ProjectApp(
                    observer, controls, poll_interval=poll_interval
                ).run()
            except Exception as error:  # noqa: BLE001 - ordinary project UI failures fall back
                _restore_terminal(saved)
                _fallback_notice(error)
            else:
                if result is not None:
                    return result
                _restore_terminal(saved)
                _fallback_notice("viewer exited without a result")
        return run_plain(observer, poll_interval=poll_interval)
    finally:
        observer.close()
