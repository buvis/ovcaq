"""Codex-native tool projection, failure classification, and retry deadlines."""

import json
import re
from datetime import UTC, datetime, timedelta

from ovcaq.events.model import (
    FailureClass,
    JSONValue,
    ObservationType,
    Usage,
    sanitize_json,
    sanitize_text,
)


def item_activity(item: object) -> dict[str, JSONValue] | None:
    if not isinstance(item, dict):
        return None
    item_id = item.get("id")
    item_kind = item.get("type")
    if not isinstance(item_id, str) or not item_id:
        return None
    detail = item.get("message" if item_kind == "error" else "text")
    if item_kind in ("agent_message", "reasoning", "error") and isinstance(detail, str):
        return {
            "kind": {
                "agent_message": "text",
                "reasoning": "thinking",
                "error": "error",
            }[item_kind],
            "text": sanitize_text(detail)[:4096],
            "message_id": sanitize_text(item_id)[:4096],
        }
    if item_kind == "todo_list":
        steps = item.get("items")
        if isinstance(steps, list) and all(
            isinstance(step, dict)
            and isinstance(step.get("text"), str)
            and isinstance(step.get("completed"), bool)
            for step in steps
        ):
            return {
                "kind": "plan",
                "message_id": sanitize_text(item_id)[:4096],
                "items": [
                    {
                        "text": sanitize_text(step["text"])[:4096],
                        "completed": step["completed"],
                    }
                    for step in steps
                ],
            }
    return None


def bounded_detail(detail: str) -> str:
    """Redact original and control-reconstructed credentials, then bound detail."""
    controls = r"\x1b\[[0-?]*[ -/]*[@-~]|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
    # A lone ESC must not turn a new [REDACTED] marker into an ANSI sequence.
    protected = re.sub(
        controls,
        lambda match: "\x00" if match[0] == "\x1b" else match[0],
        detail,
    )
    cleaned = re.sub(controls, "", sanitize_text(protected))
    return sanitize_text(cleaned)[:4096]


def turn_usage(native: object) -> tuple[Usage, str | None]:
    """Normalize cumulative counters without inventing a cache partition."""
    if not isinstance(native, dict):
        return Usage(), "Missing or malformed Codex usage"
    names = (
        "input_tokens",
        "cached_input_tokens",
        "cache_write_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    )
    counts: list[int | None] = []
    gap = None
    for name in names:
        value = native.get(name)
        if type(value) is int and value >= 0:
            counts.append(value)
        else:
            counts.append(None)
            if name in native or name in names[:3]:
                gap = "Missing or invalid Codex usage counter"
    if all(value == 0 for value in counts):
        return Usage(), "Default zero Codex usage lacks telemetry"
    inclusive, read, write, output, _reasoning = counts
    uncached = None
    estimated = write is not None and write > 0
    if estimated:
        gap = "; ".join(
            reason
            for reason in (gap, "Codex cache-write input partition is unknown")
            if reason
        )
    elif inclusive is not None and read is not None and write == 0:
        if read <= inclusive:
            uncached = inclusive - read
        else:
            gap = "; ".join(
                reason
                for reason in (gap, "Codex cache reads exceed inclusive input")
                if reason
            )
    return Usage(
        input_tokens=uncached,
        output_tokens=output,
        cache_creation_input_tokens=write,
        cache_read_input_tokens=read,
        estimated=estimated,
    ), gap


def command_detail(item: dict[str, object]) -> str | None:
    command, output, exit_code = (
        item.get("command"),
        item.get("aggregated_output"),
        item.get("exit_code"),
    )
    if not isinstance(command, str) or not isinstance(output, str):
        return None
    if exit_code is not None and type(exit_code) is not int:
        return None
    return sanitize_text(f"{command}\n{output}")[:4096]


def file_detail(item: dict[str, object]) -> str | None:
    changes = item.get("changes")
    if not isinstance(changes, list) or not all(
        isinstance(change, dict)
        and isinstance(change.get("path"), str)
        and change.get("kind") in ("add", "delete", "update")
        for change in changes
    ):
        return None
    return sanitize_text(
        "; ".join(f"{change['kind']}: {change['path']}" for change in changes)
    )[:4096]


def mcp_detail(item: dict[str, object]) -> str | None:
    if not all(isinstance(item.get(key), str) for key in ("server", "tool")):
        return None
    result, error = item.get("result"), item.get("error")
    if result is not None and (
        not isinstance(result, dict) or not isinstance(result.get("content"), list)
    ):
        return None
    if error is not None and (
        not isinstance(error, dict) or not isinstance(error.get("message"), str)
    ):
        return None
    detail = {key: item.get(key) for key in ("server", "tool", "result", "error")}
    return json.dumps(sanitize_json(detail), ensure_ascii=False)[:4096]


def web_detail(item: dict[str, object]) -> str | None:
    action = item.get("action")
    if not isinstance(item.get("query"), str) or not isinstance(action, dict):
        return None
    action_kind = action.get("type")
    if not isinstance(action_kind, str):
        return None
    fields = {
        "search": ("query",),
        "open_page": ("url",),
        "find_in_page": ("url", "pattern"),
    }.get(action_kind, ())
    if any(
        action.get(key) is not None and not isinstance(action[key], str)
        for key in fields
    ):
        return None
    queries = action.get("queries")
    if (
        action_kind == "search"
        and queries is not None
        and (
            not isinstance(queries, list)
            or not all(isinstance(query, str) for query in queries)
        )
    ):
        return None
    if "results" in item and not isinstance(item["results"], list):
        return None
    detail = {key: item.get(key) for key in ("query", "action", "results")}
    return json.dumps(sanitize_json(detail), ensure_ascii=False)[:4096]


def collab_detail(item: dict[str, object]) -> str | None:
    if item.get("tool") not in ("spawn_agent", "send_input", "wait", "close_agent"):
        return None
    if not isinstance(item.get("sender_thread_id"), str):
        return None
    prompt = item.get("prompt")
    if prompt is not None and not isinstance(prompt, str):
        return None
    return sanitize_text(prompt or "")[:4096]


def item_lanes(
    item: object,
    started_lanes: set[str] | None = None,
) -> tuple[list[tuple[str, ObservationType, dict[str, JSONValue]]], bool]:
    if not isinstance(item, dict) or item.get("type") != "collab_tool_call":
        return [], False
    receivers, states = item.get("receiver_thread_ids"), item.get("agents_states")
    if not isinstance(receivers, list) or not receivers or not isinstance(states, dict):
        return [], True
    kinds = {
        "pending_init": ObservationType.LANE_PROGRESS,
        "running": ObservationType.LANE_PROGRESS,
        "completed": ObservationType.LANE_COMPLETED,
        "errored": ObservationType.LANE_FAILED,
    }
    result: list[tuple[str, ObservationType, dict[str, JSONValue]]] = []
    has_unknown = False
    for receiver in receivers:
        if not isinstance(receiver, str) or not receiver:
            has_unknown = True
            continue
        state = states.get(receiver)
        if not isinstance(state, dict):
            has_unknown = True
            continue
        status, message = state.get("status"), state.get("message")
        if (
            status in ("interrupted", "shutdown", "not_found")
            and started_lanes is not None
            and receiver in started_lanes
        ):
            status = "errored"
        if (
            not isinstance(status, str)
            or status not in kinds
            or (message is not None and not isinstance(message, str))
        ):
            has_unknown = True
            continue
        result.append(
            (
                receiver,
                kinds[status],
                {"label": "Receiver", "detail": bounded_detail(message or "")},
            )
        )
    return result, has_unknown


def item_tool(
    item: object,
    event: str,
) -> tuple[ObservationType, dict[str, JSONValue]] | None:
    if not isinstance(item, dict):
        return None
    item_id, item_kind = item.get("id"), item.get("type")
    if not isinstance(item_id, str) or not item_id or not isinstance(item_kind, str):
        return None
    projections = {
        "command_execution": ("command", command_detail),
        "file_change": ("file change", file_detail),
        "mcp_tool_call": ("remote tool", mcp_detail),
        "web_search": ("web search", web_detail),
        "collab_tool_call": ("collaboration", collab_detail),
    }
    projection = projections.get(item_kind)
    if projection is None:
        return None
    name, project = projection
    detail = project(item)
    if detail is None:
        return None
    status = item.get("status")
    if item_kind == "web_search":
        status = "completed" if event == "item.completed" else "in_progress"
    allowed = ("in_progress", "completed", "failed")
    if status not in allowed + (
        ("declined",) if item_kind == "command_execution" else ()
    ):
        return None
    failed = (
        item_kind == "command_execution" and item.get("exit_code") not in (None, 0)
    ) or (item_kind == "mcp_tool_call" and item.get("error") is not None)
    kind = ObservationType.TOOL_STARTED
    if failed or status in ("failed", "declined"):
        kind = ObservationType.TOOL_FAILED
    elif status == "completed":
        kind = ObservationType.TOOL_COMPLETED
    return kind, {"tool_id": item_id, "name": name, "detail": detail}


def classify_failure(detail: str) -> FailureClass:
    """Match native diagnostics in authentication-to-agent precedence order."""
    status = (
        r"(?:http(?:/\d+(?:\.\d+)?| status (?:client|server) error \()?"
        r"|status(?: code)?|error(?: code)?)\s*+[:=]?\s*+"
    )
    for failure, pattern in (
        (
            FailureClass.AUTHENTICATION,
            (
                rf"{status}401|unauthorized|not logged in|"
                r"(?:invalid|expired) credentials?"
            ),
        ),
        (
            FailureClass.PERMISSION,
            rf"{status}403|permission denied|sandbox (?:denied|error)|approval denied",
        ),
        (
            FailureClass.RATE_LIMIT,
            (
                rf"{status}429|rate[- ]limit(?:s|ed|ing)?|quota (?:limits?|exceeded)|"
                r"usage limits?"
            ),
        ),
        (
            FailureClass.CONNECTIVITY,
            (
                rf"{status}(?:502|503)|connection reset|connection refused|"
                r"connection failed|dns|network unreachable|server unavailable|"
                r"stream disconnected|model is at capacity"
            ),
        ),
        (FailureClass.TIMEOUT, r"timeouts?|timed out"),
        (
            FailureClass.AGENT,
            r"agent failed|agent failure|internal error|agent loop died",
        ),
    ):
        if re.search(rf"\b(?:{pattern})\b", detail, re.IGNORECASE):
            return failure
    return FailureClass.UNKNOWN


def failure_reset(detail: str, now: datetime) -> datetime | None:
    """Return only an explicit aware deadline within the next six hours."""
    absolute = re.search(r"\breset at (\S+)", detail, re.IGNORECASE)
    relative = re.search(r"\bretry after (\S+) seconds?\b", detail, re.IGNORECASE)
    try:
        if absolute:
            reset = datetime.fromisoformat(absolute[1].rstrip(".,)"))
            if reset.tzinfo is None:
                return None
        elif relative:
            seconds = float(relative[1])
            if not 0 < seconds <= 21600:
                return None
            reset = now + timedelta(seconds=seconds)
        else:
            return None
        if not timedelta(0) < reset - now <= timedelta(hours=6):
            return None
        return reset.astimezone(UTC)
    except (ValueError, OverflowError):
        return None
