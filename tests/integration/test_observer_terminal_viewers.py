"""Production viewers retain and render the exact selected terminal frame."""

from __future__ import annotations

import asyncio
import re
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from tests.integration.test_observer_terminal_cleanup import (
    OUTCOMES,
    STAMP,
    assert_committed,
    selected_run,
)
from tests.integration.test_observer_terminal_cleanup import (
    isolated_config as isolated_config,  # noqa: PLC0414 - pytest fixture re-export
)

from ovcaq.runtime.registry import FleetRegistry
from ovcaq.state.schema import State
from ovcaq.state.store import StateStore
from ovcaq.tui.app import AttachResult, ProjectApp, RunControlService, run_plain


def assert_frame_values(text: str, state: dict[str, object]) -> None:
    work = state["work"]
    assert re.search(rf"(?<![\w.-]){re.escape(work['prd'])}(?![\w.-])", text)
    assert re.search(
        rf"(?<!\d){work['tasks_completed']}\s*/\s*{work['tasks_total']}(?!\d)",
        text,
    )


@pytest.mark.parametrize("outcome,expected", OUTCOMES)
def test_plain_renders_final_selected_frame_and_returns_without_further_polls(
    isolated_config: Path,
    capsys: pytest.CaptureFixture[str],
    outcome: str,
    expected: AttachResult,
) -> None:
    with selected_run(
        isolated_config, outcome, prd=f"{outcome}-harbor-ledger.md", total=37
    ) as selected:
        state = selected.finish()
        before = selected.settings.runtime.paths.state_file.read_bytes()
        polls = selected.observer.polls
        try:
            result = run_plain(selected.observer, poll_interval=0.001)
        finally:
            output = capsys.readouterr().out
        assert result == expected
        assert selected.observer.polls == polls + 1
        assert outcome in output.lower()
        assert_frame_values(output, state)
        assert selected.settings.runtime.paths.state_file.read_bytes() == before


@pytest.mark.parametrize("outcome,expected", OUTCOMES)
def test_textual_returns_terminal_result_after_real_supervisor_exit(
    isolated_config: Path,
    outcome: str,
    expected: AttachResult,
) -> None:
    with selected_run(
        isolated_config, outcome, prd=f"{outcome}-lantern-audit.md", total=143
    ) as selected:
        registry = FleetRegistry(selected.settings.runtime.paths.fleet_root)
        app = ProjectApp(
            selected.observer, RunControlService(registry), poll_interval=0.02
        )

        async def exercise() -> None:
            async with app.run_test(size=(120, 40)) as pilot:
                state = selected.finish()
                before = selected.settings.runtime.paths.state_file.read_bytes()
                for _ in range(30):
                    await pilot.pause(0.02)
                    if app.return_value is not None:
                        break
                assert app.return_value == expected
                polls = selected.observer.polls
                await pilot.pause(0.05)
                assert selected.observer.polls == polls
                assert_committed(selected.observer.poll(), state, selected)
                screenshot = ET.fromstring(app.export_screenshot())
                text = " ".join(
                    "".join(node.itertext())
                    for node in screenshot.iter("{http://www.w3.org/2000/svg}text")
                )
                assert outcome in text.lower()
                assert_frame_values(text, state)
                assert selected.settings.runtime.paths.state_file.read_bytes() == before

        asyncio.run(exercise())


@pytest.mark.parametrize("status", ["paused", "attention"])
def test_live_pause_or_attention_does_not_end_textual_selection(
    isolated_config: Path, status: str
) -> None:
    with selected_run(isolated_config, "completed") as selected:
        store = StateStore(selected.settings.runtime.paths.state_file)

        def change(state: State) -> None:
            if status == "paused":
                state["work"].update(phase="paused", next_phase="paused")
            else:
                state["control"]["attention"] = {
                    "site": "review",
                    "detail": "live issue",
                    "created_at": STAMP,
                }

        store.transaction(change)
        view = selected.observer.poll()
        assert view.status == status and view.ended is False
        app = ProjectApp(
            selected.observer,
            RunControlService(
                FleetRegistry(selected.settings.runtime.paths.fleet_root)
            ),
            poll_interval=0.02,
        )

        async def exercise() -> None:
            async with app.run_test() as pilot:
                await pilot.pause(0.08)
                assert app.return_value is None and selected.child.poll() is None
                await pilot.press("q")

        asyncio.run(exercise())
        assert app.return_value == AttachResult("detached", 0)
        assert selected.child.poll() is None


def set_live_status(state: State, status: str | None) -> None:
    state["work"].update(
        phase="paused" if status == "paused" else "build", next_phase="build"
    )
    state["control"]["attention"] = (
        {"site": "review", "detail": "live issue", "created_at": STAMP}
        if status == "attention"
        else None
    )


@pytest.mark.parametrize("status", ["paused", "attention"])
def test_plain_keeps_live_pause_or_attention_until_the_selected_run_ends(
    isolated_config: Path,
    capsys: pytest.CaptureFixture[str],
    status: str,
) -> None:
    with selected_run(isolated_config, "completed") as selected:
        store = StateStore(selected.settings.runtime.paths.state_file)
        store.transaction(lambda state: set_live_status(state, status))

        def release() -> None:
            time.sleep(0.1)
            store.transaction(lambda state: set_live_status(state, None))
            (selected.base / "release").touch()

        thread = threading.Thread(target=release)
        thread.start()
        try:
            result = run_plain(selected.observer, poll_interval=0.01)
        finally:
            output = capsys.readouterr().out
            thread.join(timeout=5)
        assert not thread.is_alive()
        assert result == AttachResult("completed", 0)
        assert status in output.lower() and "completed" in output.lower()
        assert "selected.md" in output
        selected.finish()
