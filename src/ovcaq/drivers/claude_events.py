"""Projections from Claude stream records into normalized event payloads."""

import re
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ovcaq.events import ObservationType, sanitize_text
from ovcaq.events.model import JSONValue


def record_timestamp(record: dict[str, Any], now: datetime) -> datetime:
    supplied = record.get("timestamp")
    if isinstance(supplied, str):
        try:
            parsed = datetime.fromisoformat(supplied)
            if parsed.tzinfo is not None:
                return parsed.astimezone(UTC)
        except (ValueError, OverflowError):
            pass
    return now


def init_payload(record: dict[str, Any]) -> dict[str, JSONValue]:
    payload: dict[str, JSONValue] = {}
    for source, target in (
        ("model", "model"),
        ("permissionMode", "permission_mode"),
        ("claude_code_version", "version"),
    ):
        value = record.get(source)
        if isinstance(value, str):
            payload[target] = value
    return payload


def block_payload(
    block: dict[str, Any], metadata: dict[str, JSONValue]
) -> tuple[ObservationType, dict[str, JSONValue]] | None:
    block_type = block.get("type")
    if block_type in ("text", "thinking"):
        value = block.get(block_type)
        if isinstance(value, str):
            return ObservationType.ACTIVITY_MESSAGE, {
                "kind": block_type,
                "text": value,
                **metadata,
            }
    elif block_type == "tool_use":
        tool_id, name = block.get("id"), block.get("name")
        if isinstance(tool_id, str) and isinstance(name, str):
            return ObservationType.TOOL_STARTED, {
                "tool_id": tool_id,
                "name": name,
                **metadata,
            }
    elif block_type == "tool_result":
        tool_id, detail = block.get("tool_use_id"), block.get("content")
        if isinstance(tool_id, str):
            if isinstance(detail, list):
                detail = " ".join(
                    item["text"]
                    for item in detail
                    if isinstance(item, dict)
                    and item.get("type") == "text"
                    and isinstance(item.get("text"), str)
                )
            if not isinstance(detail, str):
                detail = ""
            event = (
                ObservationType.TOOL_FAILED
                if block.get("is_error") is True
                else ObservationType.TOOL_COMPLETED
            )
            return event, {"tool_id": tool_id, "detail": sanitize_text(detail)[:4096]}
    return None


def task_payload(
    task: dict[str, Any], subtype: object
) -> tuple[ObservationType, dict[str, JSONValue], str] | None:
    task_id = task.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        return None
    payload: dict[str, JSONValue] = {"task_id": task_id}
    patch = task.get("patch")
    values = task | patch if isinstance(patch, dict) else task
    for source, target in (
        ("tool_use_id", "tool_id"),
        ("description", "description"),
        ("task_type", "task_type"),
        ("subagent_type", "subagent_type"),
        ("last_tool_name", "last_tool_name"),
        ("status", "status"),
    ):
        value = values.get(source)
        if isinstance(value, str):
            payload[target] = value
    task_usage = values.get("usage")
    if isinstance(task_usage, dict):
        for counter in ("tool_uses", "total_tokens", "duration_ms"):
            value = task_usage.get(counter)
            if type(value) is int and value >= 0:
                payload[counter] = value
    status = payload.get("status")
    if status == "completed":
        event = ObservationType.LANE_COMPLETED
    elif status in ("failed", "stopped", "killed"):
        event = ObservationType.LANE_FAILED
    elif subtype == "task_started":
        event = ObservationType.LANE_STARTED
    else:
        event = ObservationType.LANE_PROGRESS
    return event, payload, task_id


def rate_limit_payload(
    info: dict[str, Any], now: datetime
) -> tuple[ObservationType, dict[str, JSONValue]] | None:
    status = info.get("status")
    if status not in ("rejected", "allowed_warning", "allowed"):
        return None
    limit_type = info.get("rateLimitType")
    window = limit_type if isinstance(limit_type, str) else None
    detail = f"Rate limit {status}" + ("" if window is None else f": {window}")
    payload: dict[str, JSONValue] = {
        "window": window,
        "detail": sanitize_text(detail)[:4096],
    }
    if status == "allowed":
        return ObservationType.RATE_LIMIT_CLEARED, payload
    reset_at = None
    reset = info.get("resetsAt")
    if isinstance(reset, (int, float)) and not isinstance(reset, bool):
        try:
            parsed = datetime.fromtimestamp(reset, UTC)
            if parsed > now:
                reset_at = parsed.isoformat().replace("+00:00", "Z")
        except (ValueError, OverflowError, OSError):
            pass
    if status == "rejected":
        return ObservationType.RATE_LIMIT_STARTED, {"reset_at": reset_at, **payload}
    return ObservationType.ACTIVITY_MESSAGE, {
        "kind": "rate_limit_warning",
        "reset_at": reset_at,
        **payload,
    }


RESET_BANNER = re.compile(
    r"\bresets\s+(?:([a-z]{3})\s+(\d{1,2})\s+)?(?:at\s+)?"
    r"(\d{1,2})(?::(\d{2}))?\s*([ap]m)\s*\(([^)]*)\)",
    re.IGNORECASE,
)
_MONTHS = (
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
)
_RESET_ISO = re.compile(
    r"\bresets\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))\b"
)


def banner_reset(text: str, anchor: datetime, now: datetime) -> str | None:
    """Resolve a limit banner's reset to a future RFC 3339 UTC instant."""
    iso = _RESET_ISO.search(text)
    if iso is not None:
        try:
            reset = datetime.fromisoformat(iso[1]).astimezone(UTC)
        except (ValueError, OverflowError):
            return None
    else:
        match = RESET_BANNER.search(text)
        if match is None:
            return None
        hour, minute = int(match[3]), int(match[4] or 0)
        if not 1 <= hour <= 12 or minute > 59:
            return None
        hour = hour % 12 + (12 if match[5].lower() == "pm" else 0)
        try:
            zone = ZoneInfo(match[6].strip())
        except (ZoneInfoNotFoundError, ValueError, OSError):
            return None
        local = anchor.astimezone(zone)
        if match[1] is not None:
            if match[1].lower() not in _MONTHS:
                return None
            month = _MONTHS.index(match[1].lower()) + 1
            for year in (local.year, local.year + 1):
                try:
                    wall = datetime(
                        year, month, int(match[2]), hour, minute, tzinfo=zone
                    )
                except ValueError:
                    return None
                if wall > local:
                    break
            else:
                return None
        else:
            wall = local.replace(
                hour=hour, minute=minute, second=0, microsecond=0, fold=0
            )
            if wall <= local:
                wall += timedelta(days=1)
        reset = wall.astimezone(UTC)
    if reset <= now:
        return None
    return reset.isoformat().replace("+00:00", "Z")


_FAILURE_MARKERS = (
    ("permission", ("permission denied", "operation not permitted")),
    (
        "authentication",
        (
            "authentication",
            "unauthorized",
            "invalid api key",
            "oauth",
            "token has expired",
            "token expired",
            "expired token",
            "not logged in",
            "http 401",
            "status 401",
        ),
    ),
    (
        "rate_limit",
        (
            "hit your session limit",
            "hit your usage limit",
            "hit your weekly limit",
            "usage limit reached",
            "rate limit",
            "rate-limit",
            "rate_limit",
            "too many requests",
            "http 429",
            "status 429",
        ),
    ),
    (
        "connectivity",
        (
            "enotfound",
            "dns",
            "socket hang up",
            "connection refused",
            "connection reset",
            "api unavailable",
            "econnreset",
            "econnrefused",
            "etimedout",
            "eai_again",
            "getaddrinfo",
        ),
    ),
    ("timeout", ("timed out", "timeout")),
)


def failure_payload(detail: object) -> dict[str, JSONValue]:
    failure_class = "unknown"
    if isinstance(detail, str):
        lowered = detail.lower()
        failure_class = "agent"
        for classification, markers in _FAILURE_MARKERS:
            if any(marker in lowered for marker in markers):
                failure_class = classification
                break
    else:
        detail = "Malformed terminal error evidence"
    return {"failure_class": failure_class, "detail": sanitize_text(detail)[:4096]}
