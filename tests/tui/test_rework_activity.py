from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from ovcaq.config import AgentSettings
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import Observation, ObservationType
from ovcaq.events.tail import TailBatch
from ovcaq.tui.panels import activity_panel

from . import test_model
from .model_support import Projection

projection = test_model.projection
FIXTURES = Path(__file__).parents[1] / "fixtures"


def _decoder(provider: str) -> ClaudeDriver | CodexDriver:
    settings = AgentSettings(
        name=provider,
        command=("unused",),
        tiers={"standard": "fixture-model"},
        environment={},
        options={"permission_mode": "auto"} if provider == "claude" else {},
    )
    driver = ClaudeDriver if provider == "claude" else CodexDriver
    return driver(settings, run_id="run-1")


def _decoded_tools(
    decoder: ClaudeDriver | CodexDriver, frame: dict[str, object]
) -> tuple[Observation, ...]:
    return tuple(
        replace(event, session_id="session-1", lane_id=None)
        for event in decoder.decode(json.dumps(frame))
        if event.type.value.startswith("tool.")
    )


def _event(
    provider: str,
    kind: str,
    payload: dict[str, object],
    *,
    session: str = "session-1",
    lane: str | None = None,
) -> Observation:
    return Observation(
        protocol_version=1,
        timestamp=datetime(2026, 10, 3, 10, tzinfo=UTC),
        provider=provider,
        run_id="run-1",
        session_id=session,
        lane_id=lane,
        type=ObservationType(kind),
        payload=payload,
    )


def _render(projection: Projection, *events: Observation) -> str:
    projection.batches.append(TailBatch(events, (), False, False, True))
    stream = StringIO()
    Console(file=stream, width=240, color_system=None, force_terminal=False).print(
        activity_panel(projection.poll())
    )
    return stream.getvalue()


@pytest.mark.parametrize(
    "started_line,terminal_line",
    [(2, 3), (2, 4), (6, 7), (6, 8), (9, 10), (9, 11), (12, 13)],
    ids=[
        "command-completed",
        "command-failed",
        "file-completed",
        "file-failed",
        "remote-completed",
        "remote-failed",
        "web-completed",
    ],
)
def test_activity_displays_decoded_codex_tools_without_lanes(
    projection: Projection, started_line: int, terminal_line: int
) -> None:
    lines = (FIXTURES / "codex" / "v1" / "tool-active.jsonl").read_text().splitlines()
    start_frame = json.loads(lines[started_line])
    start_frame["type"] = "item.started"
    terminal_frame = json.loads(lines[terminal_line])
    terminal_frame["item"]["id"] = start_frame["item"]["id"]
    decoder = _decoder("codex")
    (started,) = _decoded_tools(decoder, start_frame)
    rendered = _render(projection, started)
    assert str(started.payload["name"]) in rendered
    assert started.type == ObservationType.TOOL_STARTED
    assert projection.poll().activity[0].status == "started"
    assert "started" in rendered
    if started_line == 2:
        assert projection.poll().activity[0].detail == "printf example"
        assert "printf example" in rendered
        assert "\n" not in projection.poll().activity[0].detail
    else:
        assert projection.poll().activity[0].detail == started.payload["detail"]
        assert str(started.payload["detail"]) in rendered
    (terminal,) = _decoded_tools(decoder, terminal_frame)

    rendered = _render(projection, terminal)

    assert str(started.payload["name"]) in rendered
    assert terminal.type.value.removeprefix("tool.") in rendered
    assert len(projection.poll().activity) == 1
    detail = projection.poll().activity[0].detail
    if started_line == 2:
        assert detail == "printf exampleexample"
        assert "printf exampleexample" in rendered
        assert "\n" not in detail
    else:
        assert detail == terminal.payload["detail"]
    for line in str(terminal.payload["detail"]).splitlines():
        assert line in rendered


def test_decoded_terminal_tool_name_replaces_previous_name_for_same_id(
    projection: Projection,
) -> None:
    lines = (FIXTURES / "codex" / "v1" / "tool-active.jsonl").read_text().splitlines()
    start_frame = json.loads(lines[2])
    terminal_frame = json.loads(lines[13])
    terminal_frame["item"]["id"] = start_frame["item"]["id"]
    decoder = _decoder("codex")
    (started,) = _decoded_tools(decoder, start_frame)
    (terminal,) = _decoded_tools(decoder, terminal_frame)
    assert started.payload["name"] != terminal.payload["name"]
    _render(projection, started)

    rendered = _render(projection, terminal)

    activity = projection.poll().activity
    assert len(activity) == 1
    assert activity[0].label == terminal.payload["name"]
    assert activity[0].status == "completed"
    assert str(terminal.payload["name"]) in rendered


@pytest.mark.parametrize("is_error", [False, True])
def test_activity_displays_decoded_claude_tools_without_inventing_input(
    projection: Projection, is_error: bool
) -> None:
    lines = (FIXTURES / "claude" / "v1" / "healthy.jsonl").read_text().splitlines()
    decoder = _decoder("claude")
    (started,) = _decoded_tools(decoder, json.loads(lines[1]))

    rendered = _render(projection, started)

    assert "Read" in rendered
    assert projection.poll().activity[0].status == "started"
    assert "started" in rendered
    assert "/sanitized/example" not in rendered
    assert projection.poll().activity[0].detail is None
    terminal_frame = json.loads(lines[2])
    terminal_frame["message"]["content"][0]["is_error"] = is_error
    (terminal,) = _decoded_tools(decoder, terminal_frame)

    rendered = _render(projection, terminal)

    assert "Read" in rendered
    assert "Fixture tool completed." in rendered
    assert ("failed" if is_error else "completed") in rendered
    assert len(projection.poll().activity) == 1


@pytest.mark.parametrize(
    "provider,line,kind",
    [
        ("claude", 1, "text"),
        ("claude", 1, "thinking"),
        ("codex", 5, "text"),
        ("codex", 2, "thinking"),
        ("codex", 4, "error"),
    ],
)
def test_activity_displays_decoded_literal_messages_without_lanes(
    projection: Projection, provider: str, line: int, kind: str
) -> None:
    text = f"{kind} [bold]literal fixture[/bold]"
    lines = (FIXTURES / provider / "v1" / "healthy.jsonl").read_text().splitlines()
    frame = json.loads(lines[line])
    if provider == "claude":
        block = next(b for b in frame["message"]["content"] if b["type"] == kind)
        block["thinking" if kind == "thinking" else "text"] = text
    else:
        frame["item"]["message" if kind == "error" else "text"] = text
    (event,) = (
        replace(event, session_id="session-1", lane_id=None)
        for event in _decoder(provider).decode(json.dumps(frame))
        if event.type == ObservationType.ACTIVITY_MESSAGE
        and event.payload["kind"] == kind
    )

    rendered = _render(projection, event)

    assert text in rendered
    assert projection.poll().activity[0].label == kind


def test_activity_displays_decoded_codex_plan_updates_without_lanes(
    projection: Projection,
) -> None:
    lines = (FIXTURES / "codex" / "v1" / "tool-active.jsonl").read_text().splitlines()
    decoder = _decoder("codex")
    pending_frame = json.loads(lines[20])
    completed_frame = json.loads(lines[21])
    pending_frame["item"]["items"].extend(
        [
            {"text": "Verify additional fixture", "completed": False},
            {"text": "Finish final fixture", "completed": False},
        ]
    )
    completed_frame["item"]["items"].extend(
        [
            {"text": "Verify additional fixture", "completed": True},
            {"text": "Finish final fixture", "completed": False},
        ]
    )
    pending = tuple(
        replace(event, session_id="session-1")
        for event in decoder.decode(json.dumps(pending_frame))
    )
    completed = tuple(
        replace(event, session_id="session-1")
        for event in decoder.decode(json.dumps(completed_frame))
    )

    assert "pending: Inspect example" in _render(projection, *pending)
    rendered = _render(projection, *completed)
    expected = "done: Inspect example / done: Verify additional fixture / pending: Finish final fixture"
    assert expected in rendered
    assert projection.poll().activity[0].detail == expected
    assert projection.poll().activity[0].label == "plan"
    assert len(projection.poll().activity) == 1


def test_activity_displays_decoded_literal_plan_steps_without_lanes(
    projection: Projection,
) -> None:
    lines = (FIXTURES / "codex" / "v1" / "tool-active.jsonl").read_text().splitlines()
    frame = json.loads(lines[21])
    frame["item"]["items"] = [
        {"text": "Inspect [bold]literal[/bold] fixture", "completed": True},
        {"text": "Verify remaining fixture", "completed": False},
    ]
    (event,) = (
        replace(event, session_id="session-1", lane_id=None)
        for event in _decoder("codex").decode(json.dumps(frame))
    )

    rendered = _render(projection, event)

    assert "Inspect [bold]literal[/bold] fixture" in rendered
    assert "Verify remaining fixture" in rendered
    assert projection.poll().activity[0].label == "plan"


@pytest.mark.parametrize("provider", ["codex", "claude"])
def test_activity_keeps_lanes_and_excludes_other_session_activity(
    projection: Projection, provider: str
) -> None:
    lane = _event(
        provider,
        "lane.started",
        {"label": "Receiver", "detail": "checking"},
        lane="child-1",
    )
    selected = _event(
        provider,
        "activity.message",
        {"kind": "text", "text": "selected fixture", "message_id": "selected"},
    )
    other = _event(
        provider,
        "activity.message",
        {"kind": "text", "text": "unselected fixture", "message_id": "other"},
        session="session-2",
    )

    rendered = _render(projection, lane, selected, other)

    assert "Receiver: running" in rendered
    assert "checking" in rendered
    assert "selected fixture" in rendered
    assert "unselected fixture" not in rendered


@pytest.mark.parametrize("provider", ["codex", "claude"])
def test_activity_bounds_large_literal_message_details(
    projection: Projection, provider: str
) -> None:
    text = "[bold]literal fixture[/bold] " + "x" * 200_000
    event = _event(
        provider,
        "activity.message",
        {"kind": "text", "text": text, "message_id": "large"},
    )

    rendered = _render(projection, event)

    assert "[bold]literal fixture[/bold]" in rendered
    assert len(rendered) < len(text)
