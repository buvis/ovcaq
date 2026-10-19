"""Render project views as literal, bounded Rich renderables."""

from __future__ import annotations

import shlex
from typing import TYPE_CHECKING

from ovcaq.tui.discovery import FleetView
from ovcaq.tui.model import ProjectView, UsageView, display_text

ACTIVITY_WINDOW = 20

# Rich loads lazily so the module imports without its runtime dependencies.
if TYPE_CHECKING:
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table


def _known(value: object) -> str:
    return "unknown" if value is None else display_text(str(value))


def _panel(title: str, lines: list[str]) -> Panel:
    from rich.panel import Panel
    from rich.text import Text

    # Text keeps dynamic values literal; Rich markup is never parsed.
    return Panel(Text("\n".join(lines)), title=title)


def _usage(usage: UsageView | None) -> str:
    if usage is None:
        return "unknown"
    text = (
        f"in {_known(usage.input_tokens)}, out {_known(usage.output_tokens)}, "
        f"cache write {_known(usage.cache_creation_input_tokens)}, "
        f"cache read {_known(usage.cache_read_input_tokens)}, "
        f"tools {_known(usage.tool_uses)}, cost {_known(usage.cost_usd)}"
    )
    return (
        text
        + (" (estimated)" if usage.estimated else "")
        + (" (partial)" if usage.partial else "")
    )


def fleet_table(view: FleetView) -> Table:
    from rich.table import Table
    from rich.text import Text

    table = Table(title="Fleet")
    for column in ("run", "agent", "root", "started", "pid"):
        table.add_column(column)
    for run in view.runs:
        values = (run.run_id, run.agent, str(run.root), run.started_at, str(run.pid))
        table.add_row(*(Text(display_text(value)) for value in values))
    return table


def workflow_panel(view: ProjectView) -> Panel:
    duration = view.duration_seconds
    return _panel(
        "Workflow",
        [
            f"status: {display_text(view.status)}",
            f"phase: {_known(view.phase)} -> {_known(view.next_phase)}",
            f"prd: {_known(view.prd)}",
            f"revision: {_known(view.revision)}",
            f"agent: {display_text(view.run.agent)}",
            f"provider: {display_text(view.provider)}",
            f"duration: {'unknown' if duration is None else f'{duration:.0f}s'}",
            f"usage: {_usage(view.usage)}",
            f"telemetry: {display_text(view.telemetry)}",
        ],
    )


def tasks_panel(view: ProjectView) -> Panel:
    completed, total = _known(view.tasks_completed), _known(view.tasks_total)
    return _panel("Tasks", [f"{completed} / {total} completed"])


def review_panel(view: ProjectView) -> Panel:
    return _panel("Review", [f"cycle: {_known(view.review_cycle)}"])


def activity_panel(view: ProjectView) -> Panel:
    lines = [
        display_text(item.label)
        + ("" if item.status is None else f": {display_text(item.status)}")
        + ("" if item.detail is None else f" - {display_text(item.detail)}")
        for item in reversed(view.activity[-ACTIVITY_WINDOW:])
    ]
    lines.extend(
        [
            f"{display_text(lane.label)}: {display_text(lane.status)}"
            + ("" if lane.detail is None else f" - {display_text(lane.detail)}")
            for lane in view.lanes[:ACTIVITY_WINDOW]
        ]
        or ["no lanes observed"]
    )
    if len(view.activity) > ACTIVITY_WINDOW:
        lines.append(f"{len(view.activity) - ACTIVITY_WINDOW} activity entries omitted")
    if len(view.lanes) > ACTIVITY_WINDOW:
        lines.append(f"{len(view.lanes) - ACTIVITY_WINDOW} lanes omitted")
    return _panel("Activity", lines)


def capability_panel(view: ProjectView) -> Panel:
    lines = []
    for capability in view.capabilities:
        need = "required" if capability.required else "optional"
        lines.append(
            f"{display_text(capability.name)}: {capability.status}, {need}"
            + (
                ""
                if capability.detail is None
                else f" - {display_text(capability.detail)}"
            )
        )
        if capability.evidence_path is not None:
            lines.append(f"  evidence: {display_text(str(capability.evidence_path))}")
        if capability.retry_command is not None:
            command = shlex.join(
                display_text(part) for part in capability.retry_command
            )
            lines.append(f"  retry: {command}")
    return _panel("Capabilities", lines or ["none"])


def plain_frame(view: ProjectView) -> Group:
    from rich.console import Group
    from rich.text import Text

    header = [f"status: {display_text(view.status)}"]
    if view.attention is not None:
        site = display_text(view.attention["site"])
        header.append(f"attention: {site}: {display_text(view.attention['detail'])}")
    header.extend(f"gap: {display_text(gap)}" for gap in view.gaps)
    return Group(
        Text("\n".join(header)),
        workflow_panel(view),
        tasks_panel(view),
        review_panel(view),
        activity_panel(view),
        capability_panel(view),
    )
