"""Isolated-process driver for plain-viewer terminal behavior."""

from __future__ import annotations

import importlib
import importlib.abc
import json
import sys
from io import TextIOBase
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tests.integration.test_observer_terminal_cleanup import settings_for

from ovcaq.runtime.registry import FleetRegistry, FleetRun
from ovcaq.tui.model import ProjectObserver


class TextualFailure(importlib.abc.MetaPathFinder):
    def __init__(self, exception_type: type[Exception]) -> None:
        self.exception_type = exception_type

    def find_spec(
        self,
        fullname: str,
        path: object = None,
        target: object = None,
    ) -> object:
        if fullname == "textual" or fullname.startswith("textual."):
            raise self.exception_type("isolated Textual import failure")
        return None


class TtyStream(TextIOBase):
    """Expose an inherited real stream as an interactive terminal."""

    def __init__(self, stream: TextIOBase) -> None:
        self.stream = stream

    def fileno(self) -> int:
        return self.stream.fileno()

    def isatty(self) -> bool:
        return True

    def readline(self, size: int = -1) -> str:
        return self.stream.readline(size)

    def write(self, text: str) -> int:
        return self.stream.write(text)

    def flush(self) -> None:
        self.stream.flush()


def selected(base: Path) -> tuple[object, FleetRun]:
    settings = settings_for(base)
    (entry,) = FleetRegistry(settings.runtime.paths.fleet_root).snapshot().live
    return settings, FleetRun.from_entry(entry)


def write_result(base: Path, reason: str, exit_code: int) -> None:
    (base / "viewer-result").write_text(
        json.dumps({"reason": reason, "exit_code": exit_code})
    )


def plain(base: Path) -> None:
    from ovcaq.tui.app import run_plain

    settings, run = selected(base)
    observer = ProjectObserver(run, settings.runtime)
    try:
        (base / "viewer-ready").touch()
        result = run_plain(observer, poll_interval=0.01)
        write_result(base, result.reason, result.exit_code)
    finally:
        observer.close()


def failed_import(base: Path, exception_type: type[Exception]) -> None:
    settings, run = selected(base)
    for name in tuple(sys.modules):
        if name == "ovcaq.tui.app" or name == "textual" or name.startswith("textual."):
            sys.modules.pop(name, None)
    sys.meta_path.insert(0, TextualFailure(exception_type))
    sys.stdin = TtyStream(sys.__stdin__)
    sys.stdout = TtyStream(sys.__stdout__)
    (base / "viewer-ready").touch()
    app = importlib.import_module("ovcaq.tui.app")
    observer = ProjectObserver(run, settings.runtime)
    app.ProjectObserver = lambda selected_run, runtime: observer
    try:
        result = app.attach(
            registry=FleetRegistry(settings.runtime.paths.fleet_root),
            root=run.root,
            controls=app.RunControlService(
                FleetRegistry(settings.runtime.paths.fleet_root)
            ),
            poll_interval=0.01,
        )
        write_result(base, result.reason, result.exit_code)
    finally:
        observer.close()


if __name__ == "__main__":
    base_path = Path(sys.argv[2])
    mode = sys.argv[1]
    if mode == "plain":
        plain(base_path)
    else:
        failed_import(
            base_path,
            {"import-OSError": OSError, "import-ValueError": ValueError}[mode],
        )
