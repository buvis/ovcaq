"""Immutable, sanitized version-one observations and session summaries."""

import math
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from types import MappingProxyType

PROTOCOL_VERSION = 1
type JSONValue = (
    str
    | int
    | float
    | bool
    | None
    | list["JSONValue"]
    | tuple["JSONValue", ...]
    | Mapping[str, "JSONValue"]
)
_SENSITIVE = r"token|secret|password|authorization|api[_-]?key|cookie|credential"
_SENSITIVE_KEY = re.compile(_SENSITIVE, re.IGNORECASE)
# A key is a whole `[\w-]` run, entered only at a run start, so each run is
# scanned a constant number of times: linear on long unbroken words, and any
# key length is matched.
_CREDENTIAL = re.compile(
    rf"(?P<prefix>(?<![\w-])(?=[\w-]*?(?:{_SENSITIVE}))[\w-]+"
    r"[\"']?\s*[:=]\s*(?:bearer\s+)?)"
    r"""(?:"[^"]*"|'[^']*'|[^\s,;]+)""",
    re.IGNORECASE,
)
_LIKELY_SECRET = re.compile(
    r"(?P<bearer>\bBearer\s+)(?=[A-Za-z0-9_.-]{20,}\b)[A-Za-z0-9_.-]+"
    r"|(?P<sk>\bsk-[A-Za-z0-9_-]{20,}\b)",
    re.IGNORECASE,
)
_UTC_TEXT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)")
_INVALID_UNICODE_SCALAR = re.compile(r"[\ud800-\udfff]")


class ObservationType(StrEnum):
    SESSION_STARTED = "session.started"
    ACTIVITY_MESSAGE = "activity.message"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    LANE_STARTED = "lane.started"
    LANE_PROGRESS = "lane.progress"
    LANE_COMPLETED = "lane.completed"
    LANE_FAILED = "lane.failed"
    USAGE_UPDATED = "usage.updated"
    RATE_LIMIT_STARTED = "rate_limit.started"
    RATE_LIMIT_CLEARED = "rate_limit.cleared"
    SESSION_COMPLETED = "session.completed"
    SESSION_FAILED = "session.failed"
    RAW_UNKNOWN = "raw.unknown"


class FailureClass(StrEnum):
    RATE_LIMIT = "rate_limit"
    CONNECTIVITY = "connectivity"
    PERMISSION = "permission"
    AUTHENTICATION = "authentication"
    TIMEOUT = "timeout"
    AGENT = "agent"
    UNKNOWN = "unknown"


def sanitize_text(text: str) -> str:
    """Redact credential assignments while retaining ordinary prose."""
    sanitized = _CREDENTIAL.sub(lambda match: match["prefix"] + "[REDACTED]", text)
    return _LIKELY_SECRET.sub(
        lambda match: (match["bearer"] or "") + "[REDACTED]", sanitized
    )


def has_invalid_unicode_scalar(value: object) -> bool:
    """Inspect JSON-like text without changing or redacting its contents."""
    pending: list[object] = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, str):
            if _INVALID_UNICODE_SCALAR.search(current):
                return True
        elif isinstance(current, Mapping):
            for key, child in current.items():
                pending.extend((key, child))
        elif isinstance(current, (list, tuple)):
            pending.extend(current)
    return False


def sanitize_json(value: object) -> JSONValue:
    """Copy scalar-safe JSON values, redacting sensitive data."""
    if has_invalid_unicode_scalar(value):
        raise ValueError("Strings must contain only Unicode scalar values")
    return _sanitize_json(value)


def _sanitize_json(value: object) -> JSONValue:
    if isinstance(value, str):
        return sanitize_text(str(value))
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return float(value)
    if isinstance(value, Mapping):
        result: dict[str, JSONValue] = {}
        for key, child in value.items():
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            result[str(key)] = (
                "[REDACTED]" if _SENSITIVE_KEY.search(key) else _sanitize_json(child)
            )
        return result
    if isinstance(value, (list, tuple)):
        return [_sanitize_json(child) for child in value]
    raise TypeError("Expected a JSON value")


def _freeze(value: JSONValue) -> JSONValue:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(child) for child in value)
    return value


def _identifier(value: object, *, optional: bool = False) -> None:
    if value is None and optional:
        return
    if not isinstance(value, str) or not value:
        raise ValueError("Identifiers must be nonempty strings")
    if has_invalid_unicode_scalar(value):
        raise ValueError("Strings must contain only Unicode scalar values")


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError("Expected an aware UTC datetime")
    return value


def _parse_utc(value: object) -> datetime:
    if not isinstance(value, str) or not _UTC_TEXT.fullmatch(value):
        raise ValueError("Expected an RFC 3339 UTC timestamp")
    return _utc(datetime.fromisoformat(value))


def _timestamp(value: datetime) -> str:
    return _utc(value).astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    tool_uses: int | None = None
    cost_usd: float | None = None
    estimated: bool = False

    def __post_init__(self) -> None:
        for name in (
            "input_tokens",
            "output_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
            "tool_uses",
        ):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("Usage counters must be nonnegative integers or null")
        if self.cost_usd is not None and (
            type(self.cost_usd) is not float
            or not math.isfinite(self.cost_usd)
            or self.cost_usd < 0
        ):
            raise ValueError("Cost must be a finite nonnegative float or null")
        if type(self.estimated) is not bool:
            raise TypeError("estimated must be a boolean")


def _usage_payload(
    kind: ObservationType, payload: Mapping[str, JSONValue]
) -> dict[str, JSONValue]:
    usage = payload["usage"]
    if not isinstance(usage, Mapping) or set(usage) != {f.name for f in fields(Usage)}:
        raise ValueError("Expected complete serialized Usage")
    validated = Usage(**dict(usage))  # type: ignore[arg-type]
    if kind == ObservationType.SESSION_COMPLETED:
        sanitized = sanitize_json(
            {key: value for key, value in payload.items() if key != "usage"}
        )
        assert isinstance(sanitized, dict)
        sanitized["usage"] = asdict(validated)
        return sanitized
    identity = payload["identity"]
    if identity is not None and not isinstance(identity, str):
        raise TypeError("Usage identity must be a string or null")
    # Token counters are schema fields, not credential-bearing keys.
    return {"usage": asdict(validated), "identity": sanitize_json(identity)}


def _check_rate_limit(payload: Mapping[str, JSONValue]) -> None:
    if payload["reset_at"] is not None:
        _parse_utc(payload["reset_at"])
    if payload["window"] is not None and not isinstance(payload["window"], str):
        raise TypeError("Rate-limit window must be text or null")
    if not isinstance(payload["detail"], str):
        raise TypeError("Rate-limit detail must be text")


def _payload(
    kind: ObservationType, payload: Mapping[str, JSONValue]
) -> dict[str, JSONValue]:
    if not isinstance(payload, Mapping):
        raise TypeError("Payload must be a mapping")
    if has_invalid_unicode_scalar(payload):
        raise ValueError("Strings must contain only Unicode scalar values")
    shapes = {
        ObservationType.USAGE_UPDATED: {"usage", "identity"},
        ObservationType.SESSION_FAILED: {"failure_class", "detail"},
        ObservationType.RATE_LIMIT_STARTED: {"reset_at", "window", "detail"},
        ObservationType.RAW_UNKNOWN: {"reason", "raw_sha256", "preview"},
    }
    if kind in shapes and set(payload) != shapes[kind]:
        raise ValueError("Invalid payload keys")
    if kind == ObservationType.USAGE_UPDATED or (
        kind == ObservationType.SESSION_COMPLETED and "usage" in payload
    ):
        return _usage_payload(kind, payload)
    if kind == ObservationType.SESSION_FAILED:
        failure_class = payload["failure_class"]
        if not isinstance(failure_class, str):
            raise TypeError("Failure class must be text")
        FailureClass(failure_class)
        if not isinstance(payload["detail"], str):
            raise TypeError("Failure detail must be text")
    if kind == ObservationType.RATE_LIMIT_STARTED:
        _check_rate_limit(payload)
    if kind == ObservationType.RAW_UNKNOWN:
        if not all(isinstance(payload[key], str) for key in shapes[kind]):
            raise TypeError("Unknown observation fields must be strings")
        if not re.fullmatch(r"[0-9a-f]{64}", str(payload["raw_sha256"])):
            raise ValueError("Expected lowercase SHA-256 digest")
    sanitized = sanitize_json(payload)
    assert isinstance(sanitized, dict)
    if kind in (
        ObservationType.LANE_STARTED,
        ObservationType.LANE_PROGRESS,
        ObservationType.LANE_COMPLETED,
        ObservationType.LANE_FAILED,
    ):
        # This schema counter is not a credential-bearing key.
        total_tokens = payload.get("total_tokens")
        if type(total_tokens) is int and total_tokens >= 0:
            sanitized["total_tokens"] = total_tokens
    if kind == ObservationType.RAW_UNKNOWN:
        sanitized["preview"] = str(sanitized["preview"])[:512]
    return sanitized


@dataclass(frozen=True, slots=True)
class Observation:
    protocol_version: int
    timestamp: datetime
    provider: str
    run_id: str
    session_id: str | None
    lane_id: str | None
    type: ObservationType
    payload: Mapping[str, JSONValue]

    def __post_init__(self) -> None:
        if (
            type(self.protocol_version) is not int
            or self.protocol_version != PROTOCOL_VERSION
        ):
            raise ValueError("Unsupported observation protocol version")
        _utc(self.timestamp)
        _identifier(self.provider)
        _identifier(self.run_id)
        _identifier(self.session_id, optional=True)
        _identifier(self.lane_id, optional=True)
        kind = ObservationType(self.type)
        object.__setattr__(self, "type", kind)
        object.__setattr__(self, "payload", _freeze(_payload(kind, self.payload)))


@dataclass(frozen=True, slots=True)
class SessionSummary:
    success: bool
    session_id: str | None
    failure_class: FailureClass | None
    failure_detail: str | None
    rate_limit_reset_at: datetime | None
    usage: Usage | None

    def __post_init__(self) -> None:
        if type(self.success) is not bool:
            raise TypeError("success must be a boolean")
        _identifier(self.session_id, optional=True)
        if self.failure_class is not None:
            object.__setattr__(self, "failure_class", FailureClass(self.failure_class))
        if self.failure_detail is not None:
            if not isinstance(self.failure_detail, str):
                raise TypeError("Failure detail must be text or null")
            if has_invalid_unicode_scalar(self.failure_detail):
                raise ValueError("Strings must contain only Unicode scalar values")
            object.__setattr__(
                self, "failure_detail", sanitize_text(self.failure_detail)[:4096]
            )
        if self.rate_limit_reset_at is not None:
            _utc(self.rate_limit_reset_at)
        if self.usage is not None and not isinstance(self.usage, Usage):
            raise TypeError("usage must be Usage or null")


def observation_record(observation: Observation) -> dict[str, JSONValue]:
    """Return a fresh, sanitized JSON record."""
    return {
        "protocol_version": observation.protocol_version,
        "timestamp": _timestamp(observation.timestamp),
        "provider": observation.provider,
        "run_id": observation.run_id,
        "session_id": observation.session_id,
        "lane_id": observation.lane_id,
        "type": observation.type.value,
        "payload": _payload(observation.type, observation.payload),
    }


def observation_from_record(record: Mapping[str, JSONValue]) -> Observation:
    """Validate and reconstruct a serialized version-one observation."""
    values = dict(record)
    timestamp = _parse_utc(values.pop("timestamp"))
    return Observation(timestamp=timestamp, **values)  # type: ignore[arg-type]


def summary_record(summary: SessionSummary) -> dict[str, JSONValue]:
    """Return the complete session summary as ordinary JSON containers."""
    return {
        "success": summary.success,
        "session_id": summary.session_id,
        "failure_class": summary.failure_class.value
        if summary.failure_class is not None
        else None,
        "failure_detail": (
            sanitize_text(summary.failure_detail)[:4096]
            if summary.failure_detail is not None
            else None
        ),
        "rate_limit_reset_at": (
            _timestamp(summary.rate_limit_reset_at)
            if summary.rate_limit_reset_at is not None
            else None
        ),
        "usage": asdict(summary.usage) if summary.usage is not None else None,
    }
