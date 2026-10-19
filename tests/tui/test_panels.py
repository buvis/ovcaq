from __future__ import annotations

import os
import shlex
import subprocess
import unicodedata
from collections.abc import Callable
from dataclasses import replace
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table

from ovcaq.runtime.registry import FleetRun
from ovcaq.tui.discovery import FleetView
from ovcaq.tui.model import ActivityLane, CapabilityView, ProjectView, UsageView
from ovcaq.tui.panels import (
    activity_panel,
    capability_panel,
    fleet_table,
    plain_frame,
    review_panel,
    tasks_panel,
    workflow_panel,
)


def _render(renderable: object) -> str:
    stream = StringIO()
    console = Console(file=stream, width=240, color_system=None, force_terminal=False)
    console.print(renderable)
    return stream.getvalue()


@pytest.fixture
def view(tmp_path: Path) -> ProjectView:
    return ProjectView(
        run=FleetRun(
            "run-1",
            tmp_path,
            "configured-launcher",
            "2026-10-03T10:00:00Z",
            123,
            "start",
        ),
        status="running",
        phase="review",
        next_phase="build",
        prd="00008-tui.md",
        revision=17,
        tasks_completed=5,
        tasks_total=8,
        review_cycle=3,
        provider="observed-provider",
        duration_seconds=60.0,
        usage=UsageView(101, 19, 13, 7, 3, 0.125, False, False),
        lanes=(ActivityLane("lane-1", "Reviewer", "running", "checking contracts"),),
        capabilities=(
            CapabilityView(
                "post-drain",
                "failed",
                True,
                "plugin failed",
                ("ovcaq", "--root", str(tmp_path), "capability", "retry", "post-drain"),
            ),
        ),
        attention=None,
        telemetry="complete",
        gaps=(),
    )


@pytest.mark.parametrize(
    "panel,expected",
    [
        (
            workflow_panel,
            ("review", "00008-tui.md", "observed-provider", "configured-launcher"),
        ),
        (tasks_panel, ("5", "8")),
        (review_panel, ("3",)),
        (activity_panel, ("Reviewer", "running", "checking contracts")),
        (capability_panel, ("post-drain", "failed", "plugin failed", "retry")),
    ],
)
def test_core_panels_render_project_values_deterministically(
    view: ProjectView, panel: Callable[[ProjectView], Panel], expected: tuple[str, ...]
) -> None:
    rendered = panel(view)
    first = _render(rendered)

    assert isinstance(rendered, Panel)
    assert first == _render(panel(view))
    for text in expected:
        assert text in first


@pytest.mark.parametrize("completed,total", [(5, 8), (2, 11), (0, 4)])
def test_tasks_panel_tracks_changed_counts(
    view: ProjectView, completed: int, total: int
) -> None:
    changed = replace(view, tasks_completed=completed, tasks_total=total)

    text = _render(tasks_panel(changed))

    assert str(completed) in text and str(total) in text
    assert "unknown" not in text.lower()
    assert text == _render(tasks_panel(changed))
    if (completed, total) != (5, 8):
        assert "5" not in text and "8" not in text


@pytest.mark.parametrize("cycle", [3, 7, 0])
def test_review_panel_tracks_changed_cycle(view: ProjectView, cycle: int) -> None:
    changed = replace(view, review_cycle=cycle)

    text = _render(review_panel(changed))

    assert str(cycle) in text
    assert "unknown" not in text.lower()
    assert text == _render(review_panel(changed))
    if cycle != 3:
        assert "3" not in text


@pytest.mark.parametrize("retry_available", [True, False])
def test_capability_panel_renders_supplied_retry_command_only_when_available(
    view: ProjectView, retry_available: bool
) -> None:
    root = Path("/tmp/selected-project")
    argv = ("ovcaq", "--root", str(root), "capability", "retry", "post-check")
    capability = CapabilityView(
        "post-check", "failed", True, "plugin failed", argv if retry_available else None
    )
    changed = replace(
        view, run=replace(view.run, root=root), capabilities=(capability,)
    )

    text = _render(capability_panel(changed))

    assert "post-check" in text and "plugin failed" in text
    assert text == _render(capability_panel(changed))
    if retry_available:
        assert " ".join(argv) in text
    else:
        assert "retry" not in text.lower()
        assert "ovcaq" not in text and "--root" not in text


@pytest.mark.parametrize(
    "status", ["pending", "running", "failed", "succeeded", "skipped"]
)
def test_capability_panel_renders_every_lifecycle_status_with_retained_evidence(
    view: ProjectView, status: str
) -> None:
    capability = CapabilityView(
        f"{status}-capability", status, True, f"{status} evidence", None
    )
    changed = replace(view, capabilities=(capability,))

    panel_text = _render(capability_panel(changed))
    frame_text = _render(plain_frame(changed))

    assert f"{status}-capability" in panel_text
    assert f"{status}-capability" in frame_text
    assert status in panel_text and status in frame_text
    assert f"{status} evidence" in panel_text
    assert f"{status} evidence" in frame_text
    assert panel_text == _render(capability_panel(changed))
    assert frame_text == _render(plain_frame(changed))


def test_capability_panel_distinguishes_required_and_optional_capabilities(
    view: ProjectView,
) -> None:
    changed = replace(
        view,
        capabilities=(
            CapabilityView("required-check", "failed", True, "required evidence", None),
            CapabilityView(
                "optional-check", "failed", False, "optional evidence", None
            ),
        ),
    )

    panel_text = _render(capability_panel(changed)).lower()
    frame_text = _render(plain_frame(changed)).lower()

    assert "required-check" in panel_text and "required" in panel_text
    assert "optional-check" in panel_text and "optional" in panel_text
    assert "required evidence" in panel_text and "optional evidence" in panel_text
    assert "required-check" in frame_text and "required" in frame_text
    assert "optional-check" in frame_text and "optional" in frame_text


def test_capability_renderers_shell_quote_exact_retry_argv_without_executing_it(
    view: ProjectView, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("renderer executed retry guidance")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(os, "system", forbidden)
    argv = (
        "ovcaq",
        "--root",
        "/tmp/project with spaces",
        "capability",
        "retry",
        "post-drain; do-not-run",
    )
    capability = CapabilityView("post-drain", "failed", True, "retry evidence", argv)
    changed = replace(view, capabilities=(capability,))

    panel_text = _render(capability_panel(changed))
    frame_text = _render(plain_frame(changed))

    assert shlex.join(argv) in panel_text and shlex.join(argv) in frame_text
    assert " ".join(argv) not in panel_text and " ".join(argv) not in frame_text
    assert capability.retry_command == argv
    assert panel_text == _render(capability_panel(changed))
    assert frame_text == _render(plain_frame(changed))


@pytest.mark.parametrize("panel", [workflow_panel, tasks_panel, review_panel])
def test_missing_numbers_and_phase_render_as_unknown(
    view: ProjectView, panel: Callable[[ProjectView], Panel]
) -> None:
    unknown = replace(
        view,
        phase=None,
        next_phase=None,
        prd=None,
        revision=None,
        tasks_completed=None,
        tasks_total=None,
        review_cycle=None,
        provider="unknown",
        duration_seconds=None,
        usage=None,
    )

    result = _render(panel(unknown)).lower()

    assert "unknown" in result
    assert "healthy" not in result
    assert "0/0" not in result and "0 / 0" not in result


@pytest.mark.parametrize(
    "status", ["attention", "parking", "stopping", "halted", "state-write-failed"]
)
def test_plain_frame_keeps_critical_status_attention_gaps_and_failed_capabilities_visible(
    view: ProjectView, status: str
) -> None:
    changed = replace(
        view,
        status=status,
        telemetry="partial",
        gaps=("telemetry interrupted",),
        attention={
            "site": "review",
            "detail": "operator decision needed",
            "created_at": "2026-10-03T10:00:00Z",
        },
    )
    frame = plain_frame(changed)

    text = _render(frame)

    assert isinstance(frame, Group)
    assert status in text
    assert "operator decision needed" in text
    assert "telemetry interrupted" in text
    assert "post-drain" in text and "plugin failed" in text
    assert "configured-launcher" in text and "observed-provider" in text


def test_plain_frame_renders_unknown_provider_without_inference(
    view: ProjectView,
) -> None:
    unknown = replace(view, provider="unknown")

    text = _render(plain_frame(unknown)).lower()

    assert "unknown" in text
    assert "observed-provider" not in text
    assert "healthy" not in text


def test_fleet_rows_show_configured_agent_identity_and_exact_run_selection_identity(
    view: ProjectView,
) -> None:
    other = replace(
        view.run, run_id="run-2", agent="second-launcher", root=view.run.root / "second"
    )
    fleet = FleetView((view.run, other), (), ())

    table = fleet_table(fleet)
    text = _render(table)

    assert isinstance(table, Table)
    assert "configured-launcher" in text and "second-launcher" in text
    assert "run-1" in text and "run-2" in text
    assert str(view.run.root) in text and str(other.root) in text
    assert "observed-provider" not in text
    assert _render(fleet_table(fleet)) == text


@pytest.mark.parametrize(
    "panel,field",
    [
        (workflow_panel, "prd"),
        (workflow_panel, "provider"),
        (activity_panel, "lane"),
        (capability_panel, "capability"),
        (plain_frame, "attention"),
        (plain_frame, "gap"),
    ],
)
def test_dynamic_text_is_literal_and_cannot_inject_terminal_or_rich_controls(
    view: ProjectView, panel: Callable[[ProjectView], object], field: str
) -> None:
    hostile = (
        "PREFIX[blink]LITERAL[/blink]\x1b]52;c;payload\x07\r\x85\u202e\u2066SUFFIX"
    )
    changes = {
        "prd": {"prd": hostile},
        "provider": {"provider": hostile},
        "lane": {"lanes": (ActivityLane("lane", hostile, "running", hostile),)},
        "capability": {
            "capabilities": (CapabilityView(hostile, "failed", True, hostile, None),)
        },
        "attention": {
            "attention": {
                "site": hostile,
                "detail": hostile,
                "created_at": "2026-10-03T10:00:00Z",
            }
        },
        "gap": {"gaps": (hostile,)},
    }

    text = _render(panel(replace(view, **changes[field])))

    assert "[blink]LITERAL[/blink]" in text
    assert "PREFIX" in text and "SUFFIX" in text
    assert all(
        character == "\n" or unicodedata.category(character) not in {"Cc", "Cf"}
        for character in text
    )


def test_fleet_table_sanitizes_agent_run_and_path_text(view: ProjectView) -> None:
    hostile = "[blink]LITERAL[/blink]\x1b\x07\u202e"
    run = replace(view.run, run_id=hostile, agent=hostile, root=Path("/tmp") / hostile)

    text = _render(fleet_table(FleetView((run,), (), ())))

    assert "[blink]LITERAL[/blink]" in text
    assert all(
        character == "\n" or unicodedata.category(character) not in {"Cc", "Cf"}
        for character in text
    )


def test_plain_frame_caps_dynamic_strings_before_rendering(view: ProjectView) -> None:
    long_text = "x" * 100_000
    changed = replace(view, prd=long_text, provider=long_text, gaps=(long_text,))

    rendered = _render(plain_frame(changed))

    assert rendered.count("x") <= 3 * 512
    assert "x" * 32 in rendered


def test_panels_perform_no_filesystem_process_or_control_work(
    view: ProjectView, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("panel attempted external observation or control")

    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(os, "kill", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)

    text = _render(plain_frame(view))
    fleet = _render(fleet_table(FleetView((view.run,), (), ())))

    assert "00008-tui.md" in text
    assert "configured-launcher" in fleet
