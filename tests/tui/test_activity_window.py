from __future__ import annotations

import json
import unicodedata
from dataclasses import replace
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console
from rich.panel import Panel

from ovcaq.runtime.registry import FleetRun
from ovcaq.tui.model import ActivityItem, ActivityLane, ProjectView
from ovcaq.tui.panels import activity_panel

from . import test_model
from .model_support import Projection
from .test_activity_projection import _poll
from .test_rework_activity import _decoder

projection = test_model.projection


def _render(view: ProjectView) -> str:
    stream = StringIO()
    console = Console(file=stream, width=240, color_system=None, force_terminal=False)
    panel = activity_panel(view)
    assert isinstance(panel, Panel)
    assert str(panel.title) == "Activity"
    console.print(panel)
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
        usage=None,
        lanes=(),
        capabilities=(),
        attention=None,
        telemetry="complete",
        gaps=(),
    )


def test_newest_activity_precedes_older_activity_and_lanes(view: ProjectView) -> None:
    changed = replace(
        view,
        activity=(
            ActivityItem("oldest-message", "completed", "oldest evidence"),
            ActivityItem("middle-tool", "running", "middle evidence"),
            ActivityItem("newest-plan", "failed", "newest evidence"),
        ),
        lanes=(
            ActivityLane("lane-1", "first-lane", "running", "first evidence"),
            ActivityLane("lane-2", "second-lane", "running", "second evidence"),
        ),
    )

    text = _render(changed)

    expected = (
        "newest-plan",
        "middle-tool",
        "oldest-message",
        "first-lane",
        "second-lane",
    )
    assert [text.index(label) for label in expected] == sorted(
        text.index(label) for label in expected
    )
    for label in expected:
        assert text.count(label) == 1
    for detail in ("newest evidence", "middle evidence", "oldest evidence"):
        assert detail in text
    for item in changed.activity:
        row = next(line for line in text.splitlines() if item.label in line)
        assert item.status is not None and item.status in row
    for lane in changed.lanes:
        row = next(line for line in text.splitlines() if lane.label in line)
        assert lane.detail is not None and lane.detail in row
    assert "omitted" not in text


@pytest.mark.parametrize("count", [0, 1, 19, 20, 21, 23, 28, 100, 1000])
def test_activity_window_keeps_exactly_the_newest_twenty_entries(
    view: ProjectView, count: int
) -> None:
    activity = tuple(
        ActivityItem(f"activity-{index:02d}-entry", None, None)
        for index in range(count)
    )
    changed = replace(
        view,
        activity=activity,
        lanes=(ActivityLane("lane", "lane-after-activity", "running", None),),
    )

    text = _render(changed)

    visible = [item.label for item in reversed(activity[-20:])]
    assert text.count("activity-") == min(count, 20)
    assert [text.index(label) for label in visible] == sorted(
        text.index(label) for label in visible
    )
    for item in activity[:-20]:
        assert item.label not in text
    if visible:
        assert text.index(visible[-1]) < text.index("lane-after-activity")
    assert "lane-after-activity" in text
    if count > 20:
        assert text.count(f"{count - 20} activity entries omitted") == 1
    else:
        assert "activity entries omitted" not in text


@pytest.mark.parametrize("count", [0, 1, 19, 20, 21, 24, 28, 100, 1000])
def test_lane_window_keeps_exactly_the_first_twenty_lanes(
    view: ProjectView, count: int
) -> None:
    lanes = tuple(
        ActivityLane(
            str(index),
            f"lane-{index:02d}-entry",
            ("running", "completed", "failed", "unknown")[index % 4],
            None,
        )
        for index in range(count)
    )
    changed = replace(
        view, lanes=lanes, activity=(ActivityItem("activity-before-lanes", None, None),)
    )

    text = _render(changed)

    visible = [lane.label for lane in lanes[:20]]
    assert text.count("lane-") == min(count, 20)
    assert [text.index(label) for label in visible] == sorted(
        text.index(label) for label in visible
    )
    for lane in lanes[20:]:
        assert lane.label not in text
    for lane in lanes[:20]:
        row = next(line for line in text.splitlines() if lane.label in line)
        assert lane.status in row
    if visible:
        assert text.index("activity-before-lanes") < text.index(visible[0])
        assert "no lanes observed" not in text
    else:
        assert "no lanes observed" in text
    if count > 20:
        assert text.count(f"{count - 20} lanes omitted") == 1
    else:
        assert "lanes omitted" not in text


def test_empty_activity_and_lanes_keep_the_empty_lane_message(
    view: ProjectView,
) -> None:
    text = _render(view)

    assert "no lanes observed" in text
    assert "omitted" not in text
    assert text == _render(view)


def test_both_windows_report_separate_omission_counts_without_changing_history(
    view: ProjectView,
) -> None:
    activity = tuple(
        ActivityItem(f"activity-{index:02d}-entry", None, f"message {index}")
        for index in range(25)
    )
    lanes = tuple(
        ActivityLane(str(index), f"lane-{index:02d}-entry", "running", f"lane {index}")
        for index in range(27)
    )
    changed = replace(view, activity=activity, lanes=lanes)
    original = replace(changed)

    text = _render(changed)

    assert text.count("5 activity entries omitted") == 1
    assert text.count("7 lanes omitted") == 1
    assert text.count("activity-") == 20
    assert text.count("lane-") == 20
    visible = [item.label for item in reversed(activity[-20:])]
    assert [text.index(label) for label in visible] == sorted(
        text.index(label) for label in visible
    )
    for item in activity[-20:]:
        row = next(line for line in text.splitlines() if item.label in line)
        assert item.detail is not None and item.detail in row
    for lane in lanes[:20]:
        row = next(line for line in text.splitlines() if lane.label in line)
        assert lane.detail is not None and lane.detail in row
    assert text.index("activity-05-entry") < text.index("lane-00-entry")
    assert text.index("lane-19-entry") < text.index("5 activity entries omitted")
    assert text.index("lane-19-entry") < text.index("7 lanes omitted")
    assert text == _render(changed)
    assert changed == original


def test_decoded_warning_detail_redacts_synthetic_credentials_before_rendering(
    projection: Projection,
) -> None:
    secret = "sk-" + "syntheticcredential1234567890"
    # Synthetic credential injection, decoded through the real warning boundary.
    frame = json.dumps(
        {
            "type": "rate_limit_event",
            "session_id": "session-1",
            "rate_limit_info": {
                "status": "allowed_warning",
                "rateLimitType": f"five_hour api_key={secret}",
            },
        }
    )
    (warning,) = _decoder("claude").decode(frame)
    expected = "Rate limit allowed_warning: five_hour api_key=[REDACTED]"

    assert warning.type.value == "activity.message"
    assert "text" not in warning.payload
    assert warning.payload["detail"] == expected
    assert _poll(projection, warning) == (expected,)
    text = _render(projection.poll())
    assert expected in text
    assert secret not in text


@pytest.mark.parametrize(
    "field",
    [
        "activity_label",
        "activity_status",
        "activity_detail",
        "lane_label",
        "lane_detail",
    ],
)
def test_dynamic_activity_and_lane_text_is_literal_and_terminal_safe(
    view: ProjectView, field: str
) -> None:
    hostile = (
        "PREFIX[blink]LITERAL[/blink] café 漢字 🚀"
        "\x1b]52;c;payload\x07\r\x85\u202e\u2066SUFFIX"
    )
    item = ActivityItem("activity-label", "running", "activity detail")
    lane = ActivityLane("lane", "lane-label", "running", "lane detail")
    if field.startswith("activity_"):
        item = replace(item, **{field.removeprefix("activity_"): hostile})
    else:
        lane = replace(lane, **{field.removeprefix("lane_"): hostile})
    changed = replace(view, activity=(item,), lanes=(lane,))

    text = _render(changed)

    assert "[blink]LITERAL[/blink]" in text
    assert "PREFIX" in text and "SUFFIX" in text
    assert "café 漢字 🚀" in text
    assert all(
        character == "\n" or unicodedata.category(character) not in {"Cc", "Cf"}
        for character in text
    )
