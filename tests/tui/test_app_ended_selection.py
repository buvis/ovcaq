"""Protocol-only mapping checks; real cleanup is covered by integration tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from ovcaq.runtime.registry import FleetRun
from ovcaq.tui.app import AttachResult, ProjectApp, run_plain
from ovcaq.tui.model import ProjectView


class EndedObserver:
    def __init__(self, root: Path, status: str) -> None:
        self.polls = 0
        self.view = ProjectView(
            run=FleetRun(
                "selected", root, "local", "2026-10-03T12:00:00Z", 12345, "start"
            ),
            status=status,
            phase="build",
            next_phase="build",
            prd="selected.md",
            revision=4,
            tasks_completed=1,
            tasks_total=7,
            review_cycle=0,
            provider="local",
            duration_seconds=None,
            usage=None,
            lanes=(),
            capabilities=(),
            attention=None,
            telemetry="partial",
            gaps=("Selected run ended; final evidence unavailable",),
            ended=True,
        )

    def poll(self) -> ProjectView:
        self.polls += 1
        if self.polls > 1:
            pytest.fail("viewer polled an ended selection again")
        return self.view

    def close(self) -> None:
        pass


class NoControls:
    def pause(self, *args: object, **kwargs: object) -> None:
        pytest.fail("an ended viewer requested pause")

    def resume(self, *args: object, **kwargs: object) -> None:
        pytest.fail("an ended viewer requested resume")

    def stop(self, *args: object, **kwargs: object) -> None:
        pytest.fail("an ended viewer requested stop")


@pytest.mark.parametrize("status", ["state-write-failed", "unknown"])
def test_plain_ended_uncertain_result_fails_visibly_without_repolling(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    status: str,
) -> None:
    observer = EndedObserver(tmp_path, status)
    assert run_plain(observer, poll_interval=0.001) == AttachResult("failed", 1)
    output = capsys.readouterr().out
    assert "selected.md" in output and "final evidence unavailable" in output
    assert observer.polls == 1


@pytest.mark.parametrize("status", ["state-write-failed", "unknown"])
def test_textual_ended_uncertain_result_fails_without_repolling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    observer = EndedObserver(tmp_path, status)
    app = ProjectApp(observer, NoControls(), poll_interval=0.01)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.pause(0.05)
            assert app.return_value == AttachResult("failed", 1)

    asyncio.run(exercise())
    assert observer.polls == 1
