"""Versioned durable state schema."""

from __future__ import annotations

import copy
import json
import math
import re
import types
import typing
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    ForwardRef,
    Literal,
    Never,
    TypeAlias,
    TypedDict,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    is_typeddict,
)

SCHEMA_VERSION: Final[int] = 1
TIMESTAMP_FORMAT: Final[str] = "UTC RFC 3339: YYYY-MM-DDTHH:MM:SS[.ffffff]Z"
MAX_STATE_BYTES: Final[int] = 16 * 1024 * 1024
MAX_COMMAND_PAYLOAD_BYTES: Final[int] = 2 * 1024 * 1024
MAX_STRING_BYTES: Final[int] = 1024 * 1024
MAX_CONTRACT_CARD_BYTES: Final[int] = 64 * 1024
MAX_JSON_DEPTH: Final[int] = 32
MAX_JSON_INTEGER_DIGITS: Final[int] = 640
MAX_TASKS: Final[int] = 512
MAX_ATTEMPTS_PER_TASK: Final[int] = 64
MAX_REVIEW_CYCLES: Final[int] = 32
MAX_REVIEW_ITEMS: Final[int] = 1024
MAX_CAPABILITIES: Final[int] = 64
MAX_OPEN_MAP_ITEMS: Final[int] = 256
_JSON_DECODE_DEPTH_LIMIT: Final[int] = MAX_JSON_DEPTH + 8
_JSON_INTEGER_ABSOLUTE_LIMIT: Final[int] = 10**MAX_JSON_INTEGER_DIGITS

Phase = Literal["build", "review", "done", "paused"]
NextPhase = Literal["build", "review", "done", "paused", ""]
BatchStatus = Literal["idle", "running", "attention", "completed"]
TaskStatus = Literal["pending", "in_progress", "completed"]
AttemptOutcome = Literal[
    "completed", "aborted", "review_flagged", "rework_failed", "escalated"
]
CapabilityStatus = Literal["pending", "running", "failed", "succeeded", "skipped"]
ReviewCategory = Literal["fix", "verify", "known"]
ReviewItemStatus = Literal["pending", "resolved"]
ReviewerStatus = Literal["available", "unavailable", "disabled", "passed", "failed"]
DecisionStatus = Literal["applied", "deferred", "escalated"]
RecoveryKind = Literal["park", "stall"]
RecoveryStep = Literal["intent", "moved", "recorded"]

JSONScalar: TypeAlias = str | int | float | bool | None  # noqa: UP040
if TYPE_CHECKING:
    JSONValue: TypeAlias = (  # noqa: UP040
        JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
    )
else:
    JSONValue: TypeAlias = (  # noqa: UP040
        JSONScalar | list[ForwardRef("JSONValue")] | dict[str, ForwardRef("JSONValue")]
    )


class CatchupCache(TypedDict):
    completed_at: str | None
    head_sha: str | None


class CompletedPrd(TypedDict):
    filename: str
    cycles: int
    autonomous_decisions: int
    escalated_decisions: int
    tasks_completed: int
    tasks_total: int


class CapabilityAttempt(TypedDict):
    id: str
    status: Literal["running", "failed", "succeeded"]
    started_at: str
    finished_at: str | None
    session_id: str | None
    detail: str | None


class CapabilityEntry(TypedDict):
    required: bool
    launcher: str
    plugin: str
    version: str
    failure: Literal["attention"]
    status: CapabilityStatus
    attempts: list[CapabilityAttempt]


class BatchState(TypedDict):
    id: str
    status: BatchStatus
    started_at: str | None
    completed_at: str | None
    completed_prds: list[CompletedPrd]
    parks_consecutive: int
    catchup: CatchupCache
    capabilities: dict[str, CapabilityEntry]


class TaskEstimates(TypedDict):
    input_tokens: int | None
    context_peak: int | None


class EscalationEntry(TypedDict):
    reason: Literal["gate_failure", "review_flag", "rescue"]
    from_tier: str
    diagnosis: Literal["spec_gap", "solid_spec"] | None
    repair_used: bool


class AttemptEntry(TypedDict):
    number: int
    tier: str
    driver: str
    outcome: AttemptOutcome
    review_cycle: int | None
    cause: str | None
    pipeline: Literal["minimal", "lean", "full"] | None
    cleanup_outcome: str | None
    started_at: str
    finished_at: str
    commit_sha: str | None
    escalation: EscalationEntry | None
    metadata: dict[str, JSONValue]


class TaskEntry(TypedDict):
    id: int
    name: str
    description: str
    active_form: str
    status: TaskStatus
    blocked_by: list[int]
    tier: str | None
    files_touched: int | None
    public_contract_edit: bool | None
    estimates: TaskEstimates
    attempts: list[AttemptEntry]
    metadata: dict[str, JSONValue]


class WorkState(TypedDict):
    prd: str | None
    phase: Phase
    next_phase: NextPhase
    completed_phases: list[Literal["review"]]
    work_start_sha: str | None
    repo_root: str
    design_doc: str | None
    contract_card: str | None
    tasks_total: int
    tasks_completed: int
    extensions: dict[str, JSONValue]


class DecisionGate(TypedDict):
    decision: str
    detail: str
    decided_at: str


class TestRun(TypedDict):
    command: list[str]
    exit_code: int
    summary: str


class ReviewCycle(TypedDict):
    cycle: int
    review_file: str
    reviewers: dict[str, ReviewerStatus]
    issues_found: int
    follow_up_tasks: int
    deferred: int
    recurring_issues: list[str]
    decision_gate: DecisionGate | None
    rework_commits: list[str]
    rework_notes: list[str]
    fix_audit: list[str]
    test_run: TestRun | None


class DecisionEntry(TypedDict):
    id: str
    kind: str
    summary: str
    rationale: str
    cycle: int | None
    created_at: str
    status: DecisionStatus


class DoubtEntry(TypedDict):
    id: str
    description: str
    category: ReviewCategory
    justification: str | None
    status: ReviewItemStatus
    source: str | None


class RubricVerdict(TypedDict):
    rule_id: str
    verdict: Literal["pass", "fail"]
    source: str | None


class ReviewState(TypedDict):
    cycle: int
    cap: int
    cycles: list[ReviewCycle]
    decisions: list[DecisionEntry]
    doubts: list[DoubtEntry]
    rubric_verdicts: list[RubricVerdict]
    rework_task_ids: list[int]
    lenses: dict[str, Literal["pending", "running", "completed", "failed"]]
    extensions: dict[str, JSONValue]


class Notice(TypedDict):
    site: str
    detail: str
    created_at: str


class ControlState(TypedDict):
    pause_requested: bool
    pause_reason: Notice | None
    attention: Notice | None


class ArtifactIdentity(TypedDict):
    device: int
    inode: int


class RecoveryOperation(TypedDict):
    id: str
    kind: RecoveryKind
    step: RecoveryStep
    prd: str
    site: str
    detail: str
    source: str
    destination: str
    artifact: ArtifactIdentity | None
    created_at: str


class RecoveryState(TypedDict):
    operation: RecoveryOperation | None
    replan_count: int
    phase_fingerprint: str | None
    phase_repeats: int


class State(TypedDict):
    schema_version: int
    revision: int
    batch: BatchState
    work: WorkState
    tasks: list[TaskEntry]
    review: ReviewState
    control: ControlState
    recovery: RecoveryState


def new_state(*, repo_root: Path) -> State:
    return {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "batch": {
            "id": "",
            "status": "idle",
            "started_at": None,
            "completed_at": None,
            "completed_prds": [],
            "parks_consecutive": 0,
            "catchup": {"completed_at": None, "head_sha": None},
            "capabilities": {},
        },
        "work": {
            "prd": None,
            "phase": "build",
            "next_phase": "build",
            "completed_phases": [],
            "work_start_sha": None,
            "repo_root": str(repo_root.resolve()),
            "design_doc": None,
            "contract_card": None,
            "tasks_total": 0,
            "tasks_completed": 0,
            "extensions": {},
        },
        "tasks": [],
        "review": {
            "cycle": 0,
            "cap": 3,
            "cycles": [],
            "decisions": [],
            "doubts": [],
            "rubric_verdicts": [],
            "rework_task_ids": [],
            "lenses": {},
            "extensions": {},
        },
        "control": {"pause_requested": False, "pause_reason": None, "attention": None},
        "recovery": {
            "operation": None,
            "replan_count": 0,
            "phase_fingerprint": None,
            "phase_repeats": 0,
        },
    }


class SchemaError(ValueError):
    """Raised when a value violates the v1 state schema."""


class ResourceLimitError(SchemaError):
    """Raised when a value exceeds a schema resource limit."""


class DuplicateJSONKeyError(ValueError):
    """Raised before decoding can collapse a duplicate JSON object key."""


_MAX_VALUE_REPR = 200
_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
_EXTENSION_KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9_.-]*$")


def _bounded_repr(value: object) -> str:
    text = repr(value)
    if len(text) <= _MAX_VALUE_REPR:
        return text
    return f"{text[:_MAX_VALUE_REPR]}...({len(text)} chars)"


def _safe_error_text(value: str) -> str:
    return value.encode("utf-8", errors="backslashreplace").decode("utf-8")


def _invalid(path: str, expected: str, value: object) -> Never:
    safe_path = _safe_error_text(path)
    raise SchemaError(f"{safe_path}: expected {expected}, got {_bounded_repr(value)}")


def _fail(path: str, detail: str) -> Never:
    raise SchemaError(f"{_safe_error_text(path)}: {detail}")


def _limit(path: str, detail: str) -> Never:
    raise ResourceLimitError(f"{_safe_error_text(path)}: {detail}")


def _check_json_decode_depth(text: str, *, source: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > _JSON_DECODE_DEPTH_LIMIT:
                _limit(
                    source,
                    "JSON nesting exceeds safe decode limit "
                    f"{_JSON_DECODE_DEPTH_LIMIT}",
                )
        elif character in "]}":
            depth = max(depth - 1, 0)


def _check_decoded_json_depth(value: object, *, source: str) -> None:
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > _JSON_DECODE_DEPTH_LIMIT:
            _limit(
                source,
                f"JSON nesting exceeds safe decode limit {_JSON_DECODE_DEPTH_LIMIT}",
            )
        if isinstance(item, dict):
            pending.extend((nested, depth + 1) for nested in item.values())
        elif isinstance(item, list):
            pending.extend((nested, depth + 1) for nested in item)


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJSONKeyError(
                f"duplicate JSON object key: {_bounded_repr(key)}"
            )
        value[key] = item
    return value


def _decode_json_integer(literal: str, *, source: str) -> int:
    digits = literal.removeprefix("-")
    if len(digits) > MAX_JSON_INTEGER_DIGITS:
        _limit(
            source,
            f"JSON integer literal exceeds {MAX_JSON_INTEGER_DIGITS} digits",
        )
    return int(literal)


def _reject_nonstandard_json_constant(literal: str) -> Never:
    raise ValueError(f"non-standard JSON constant: {literal}")


def decode_json(text: str, *, source: str) -> JSONValue:
    """Decode bounded JSON without collapsing duplicate object keys."""
    _check_json_decode_depth(text, source=source)

    def parse_integer(literal: str) -> int:
        return _decode_json_integer(literal, source=source)

    return cast(
        JSONValue,
        json.loads(
            text,
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_nonstandard_json_constant,
            parse_int=parse_integer,
        ),
    )


def _field_path(path: str, field: object) -> str:
    return f"{path}.{field}" if path else str(field)


def _item_path(path: str, index: int) -> str:
    return f"{path}[{index}]"


def _require_dict(value: object, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _invalid(path or "state", "object", value)
    return cast(dict[str, Any], value)


def _require_list(value: object, path: str) -> list[Any]:
    if not isinstance(value, list):
        _invalid(path, "list", value)
    return value


def _require_string(value: object, path: str, *, limit: int = MAX_STRING_BYTES) -> str:
    if not isinstance(value, str):
        _invalid(path, "string", value)
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise SchemaError(
            f"{_safe_error_text(path)}: string is not valid UTF-8"
        ) from error
    if len(encoded) > limit:
        _limit(path, f"UTF-8 value exceeds {limit} bytes")
    return value


def _require_integer(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _invalid(path, "integer", value)
    if abs(value) >= _JSON_INTEGER_ABSOLUTE_LIMIT:
        _limit(path, f"integer value exceeds {MAX_JSON_INTEGER_DIGITS} digits")
    return value


def _require_bool(value: object, path: str) -> bool:
    if not isinstance(value, bool):
        _invalid(path, "boolean", value)
    return value


_SCALARS = {str: _require_string, int: _require_integer, bool: _require_bool}


def validate_timestamp(value: object, path: str) -> str:
    timestamp = _require_string(value, path)
    if not _TIMESTAMP_PATTERN.fullmatch(timestamp):
        _invalid(path, TIMESTAMP_FORMAT, value)
    try:
        datetime.fromisoformat(f"{timestamp[:-1]}+00:00")
    except ValueError as error:
        raise SchemaError(
            f"{path}: expected {TIMESTAMP_FORMAT}, got {_bounded_repr(value)}"
        ) from error
    return timestamp


def _timestamp_value(value: str) -> datetime:
    return datetime.fromisoformat(f"{value[:-1]}+00:00")


def _validate_json(value: object, path: str, depth: int) -> None:
    if depth > MAX_JSON_DEPTH:
        _limit(path, f"JSON nesting exceeds {MAX_JSON_DEPTH}")
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, str):
            _require_string(value, path)
        elif isinstance(value, int) and not isinstance(value, bool):
            _require_integer(value, path)
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            _fail(path, "JSON number must be finite")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json(item, _item_path(path, index), depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > MAX_OPEN_MAP_ITEMS:
            _limit(path, f"open map exceeds {MAX_OPEN_MAP_ITEMS} items")
        for key, item in value.items():
            if not isinstance(key, str):
                _invalid(path, "JSON object with string keys", value)
            _require_string(key, _field_path(path, key))
            _validate_json(item, _field_path(path, key), depth + 1)
        return
    _invalid(path, "finite JSON value", value)


def validate_json_value(value: object, path: str) -> JSONValue:
    """Validate a generic JSON value before any recursive copy work."""
    _validate_json(value, path, 0)
    return cast(JSONValue, value)


def _validate_open_map(value: object, path: str, *, extensions: bool) -> None:
    mapping = _require_dict(value, path)
    if len(mapping) > MAX_OPEN_MAP_ITEMS:
        _limit(path, f"open map exceeds {MAX_OPEN_MAP_ITEMS} items")
    for key, item in mapping.items():
        if not isinstance(key, str):
            _invalid(path, "object with string keys", value)
        key_path = _field_path(path, key)
        _require_string(key, key_path)
        if extensions and not _EXTENSION_KEY_PATTERN.fullmatch(key):
            _fail(key_path, "invalid extension key")
        _validate_json(item, key_path, 0)


def _validate_annotation(value: object, annotation: object, path: str) -> None:
    if isinstance(annotation, ForwardRef):
        if annotation.__forward_arg__ == "JSONValue":
            _validate_json(value, path, 0)
            return
        _fail(path, f"unresolved annotation {annotation.__forward_arg__}")
    if is_typeddict(annotation):
        _validate_owned(value, annotation, path)
        return
    origin = get_origin(annotation)
    arguments = get_args(annotation)
    if origin is Literal:
        if value not in arguments or not isinstance(value, type(arguments[0])):
            _invalid(path, f"one of {arguments!r}", value)
        if isinstance(value, str):
            _require_string(value, path)
        return
    if origin is list:
        for index, item in enumerate(_require_list(value, path)):
            _validate_annotation(item, arguments[0], _item_path(path, index))
        return
    if origin is dict:
        mapping = _require_dict(value, path)
        key_annotation, value_annotation = arguments
        for key, item in mapping.items():
            key_path = _field_path(path, key)
            _validate_annotation(key, key_annotation, key_path)
            _validate_annotation(item, value_annotation, key_path)
        return
    if origin in {types.UnionType, typing.Union}:
        non_null = tuple(item for item in arguments if item is not type(None))
        if value is None and len(non_null) != len(arguments):
            return
        if len(non_null) == 1:
            _validate_annotation(value, non_null[0], path)
            return
    if (validator := _SCALARS.get(cast(type, annotation))) is not None:
        cast(Any, validator)(value, path)
        return
    if annotation is type(None):
        if value is not None:
            _invalid(path, "null", value)
        return
    _fail(path, f"unsupported schema annotation {annotation!r}")


_MINIMUM_RULES: dict[object, tuple[tuple[str, int], ...]] = {
    State: (("revision", 0),),
    BatchState: (("parks_consecutive", 0),),
    CompletedPrd: (
        ("cycles", 0),
        ("autonomous_decisions", 0),
        ("escalated_decisions", 0),
        ("tasks_completed", 0),
        ("tasks_total", 0),
    ),
    WorkState: (("tasks_total", 0), ("tasks_completed", 0)),
    TaskEntry: (("id", 1),),
    TaskEstimates: (("input_tokens", 0), ("context_peak", 0)),
    AttemptEntry: (("number", 1), ("review_cycle", 1)),
    ReviewState: (("cycle", 0), ("cap", 1)),
    ReviewCycle: (
        ("cycle", 1),
        ("issues_found", 0),
        ("follow_up_tasks", 0),
        ("deferred", 0),
    ),
    DecisionEntry: (("cycle", 1),),
    RecoveryState: (("replan_count", 0), ("phase_repeats", 0)),
}
_TIMESTAMP_FIELDS: dict[object, tuple[str, ...]] = {
    BatchState: ("started_at", "completed_at"),
    CatchupCache: ("completed_at",),
    AttemptEntry: ("started_at", "finished_at"),
    DecisionGate: ("decided_at",),
    DecisionEntry: ("created_at",),
    Notice: ("created_at",),
    RecoveryOperation: ("created_at",),
    CapabilityAttempt: ("started_at", "finished_at"),
}
_COLLECTION_LIMITS: dict[object, tuple[tuple[str, int], ...]] = {
    State: (("tasks", MAX_TASKS),),
    BatchState: (("capabilities", MAX_CAPABILITIES),),
    TaskEntry: (("attempts", MAX_ATTEMPTS_PER_TASK),),
    ReviewState: (
        ("cycles", MAX_REVIEW_CYCLES),
        ("decisions", MAX_REVIEW_ITEMS),
        ("doubts", MAX_REVIEW_ITEMS),
        ("rubric_verdicts", MAX_REVIEW_ITEMS),
        ("rework_task_ids", MAX_REVIEW_ITEMS),
    ),
}


def _validate_common_constraints(
    owner: object, value: dict[str, Any], path: str
) -> None:
    steps = ("time", "min") if owner is BatchState else ("min", "time")
    for step in steps:
        if step == "time":
            for field in _TIMESTAMP_FIELDS.get(owner, ()):
                if value[field] is not None:
                    validate_timestamp(value[field], _field_path(path, field))
        else:
            for field, minimum in _MINIMUM_RULES.get(owner, ()):
                if value[field] is not None and value[field] < minimum:
                    detail = (
                        "must be non-negative"
                        if minimum == 0
                        else f"must be at least {minimum}"
                    )
                    _fail(_field_path(path, field), detail)


def _validate_collection_constraints(
    owner: object, value: dict[str, Any], path: str
) -> None:
    for field, limit in _COLLECTION_LIMITS.get(owner, ()):
        if len(value[field]) > limit:
            _limit(_field_path(path, field), f"exceeds {limit} entries")
        review_cycle = owner is ReviewState and field == "cycles"
        if review_cycle and value["cycle"] > MAX_REVIEW_CYCLES:
            _limit(_field_path(path, "cycle"), f"exceeds {MAX_REVIEW_CYCLES}")


def _validate_content_constraints(
    owner: object, value: dict[str, Any], path: str
) -> None:
    if owner is CompletedPrd and value["tasks_completed"] > value["tasks_total"]:
        _fail(_field_path(path, "tasks_completed"), "exceeds tasks_total")
    elif owner is WorkState:
        if not Path(value["repo_root"]).is_absolute():
            _fail(_field_path(path, "repo_root"), "must be an absolute path")
        if value["contract_card"] is not None:
            contract_path = _field_path(path, "contract_card")
            _require_string(
                value["contract_card"], contract_path, limit=MAX_CONTRACT_CARD_BYTES
            )
    elif owner is TaskEntry:
        if not value["name"]:
            _fail(_field_path(path, "name"), "must not be empty")
        if value["files_touched"] is not None and value["files_touched"] < 0:
            _fail(_field_path(path, "files_touched"), "must be non-negative")
    elif owner is TestRun:
        command = json.dumps(
            value["command"], ensure_ascii=False, separators=(",", ":")
        )
        if len(command.encode("utf-8")) > MAX_COMMAND_PAYLOAD_BYTES:
            command_path = _field_path(path, "command")
            _limit(command_path, f"exceeds {MAX_COMMAND_PAYLOAD_BYTES} bytes")


@cache
def _resolved_type_hints(owner: object) -> dict[str, Any]:
    return get_type_hints(owner, globalns=globals(), localns=globals())


def _validate_owned(value: object, owner: object, path: str) -> dict[str, Any]:
    mapping = _require_dict(value, path)
    hints = _resolved_type_hints(owner)
    for key in mapping:
        if not isinstance(key, str):
            _invalid(path or "state", "object with string keys", value)
    for field in hints:
        if field not in mapping:
            _fail(_field_path(path, field), "required field is missing")
    for field in mapping:
        if field not in hints:
            _fail(_field_path(path, field), "unknown field")
    for field, annotation in hints.items():
        field_path = _field_path(path, field)
        if field in {"metadata", "extensions"}:
            _validate_open_map(
                mapping[field], field_path, extensions=field == "extensions"
            )
        else:
            _validate_annotation(mapping[field], annotation, field_path)
    _validate_common_constraints(owner, mapping, path)
    _validate_content_constraints(owner, mapping, path)
    _validate_collection_constraints(owner, mapping, path)
    return mapping


def _require_unique_ids(
    entries: list[dict[str, Any]], path: str, *, field: str = "id"
) -> None:
    seen: set[object] = set()
    for index, entry in enumerate(entries):
        identifier = entry[field]
        if identifier in seen:
            _fail(_field_path(_item_path(path, index), field), "duplicate identifier")
        seen.add(identifier)


def _validate_task_invariants(state: dict[str, Any]) -> None:
    tasks = state["tasks"]
    _require_unique_ids(tasks, "tasks")
    task_ids = {task["id"] for task in tasks}
    for task_index, task in enumerate(tasks):
        task_path = _item_path("tasks", task_index)
        blockers: set[int] = set()
        for blocker_index, blocker in enumerate(task["blocked_by"]):
            blocker_path = _item_path(
                _field_path(task_path, "blocked_by"), blocker_index
            )
            if blocker == task["id"]:
                _fail(blocker_path, "task cannot block itself")
            if blocker in blockers:
                _fail(blocker_path, "duplicate blocker")
            if blocker not in task_ids:
                _fail(blocker_path, "unknown blocker")
            blockers.add(blocker)
        for attempt_index, attempt in enumerate(task["attempts"]):
            attempt_path = _item_path(_field_path(task_path, "attempts"), attempt_index)
            if attempt["number"] != attempt_index + 1:
                _fail(
                    _field_path(attempt_path, "number"),
                    "attempt numbers must be contiguous",
                )
            if _timestamp_value(attempt["finished_at"]) < _timestamp_value(
                attempt["started_at"]
            ):
                _fail(
                    _field_path(attempt_path, "finished_at"),
                    "precedes started_at",
                )
    work = state["work"]
    if work["tasks_total"] != len(tasks):
        _fail("work.tasks_total", "must equal the number of tasks")
    completed = sum(task["status"] == "completed" for task in tasks)
    if work["tasks_completed"] != completed:
        _fail("work.tasks_completed", "must equal completed task entries")
    for index, task_id in enumerate(state["review"]["rework_task_ids"]):
        if task_id not in task_ids:
            _fail(_item_path("review.rework_task_ids", index), "unknown task")


def _validate_review_invariants(state: dict[str, Any]) -> None:
    review = state["review"]
    _require_unique_ids(review["cycles"], "review.cycles", field="cycle")
    _require_unique_ids(review["decisions"], "review.decisions")
    _require_unique_ids(review["doubts"], "review.doubts")


def _validate_capability_attempts(
    attempts: list[dict[str, Any]], path: str, attempt_ids: set[str]
) -> None:
    previous_finished: datetime | None = None
    for index, attempt in enumerate(attempts):
        attempt_path = _item_path(_field_path(path, "attempts"), index)
        if attempt["id"] in attempt_ids:
            _fail(_field_path(attempt_path, "id"), "duplicate identifier")
        attempt_ids.add(attempt["id"])
        started = _timestamp_value(attempt["started_at"])
        finished = (
            None
            if attempt["finished_at"] is None
            else _timestamp_value(attempt["finished_at"])
        )
        if finished is not None and finished < started:
            _fail(_field_path(attempt_path, "finished_at"), "precedes started_at")
        if previous_finished is not None and started < previous_finished:
            _fail(_field_path(attempt_path, "started_at"), "attempts are out of order")
        if index < len(attempts) - 1 and (
            attempt["status"] not in {"failed", "succeeded"} or finished is None
        ):
            _fail(attempt_path, "prior attempt must be terminal")
        previous_finished = finished


def _validate_latest_capability(capability: dict[str, Any], path: str) -> None:
    status = capability["status"]
    if status not in {"running", "failed", "succeeded"}:
        return
    attempts = capability["attempts"]
    latest = attempts[-1]
    latest_path = _item_path(_field_path(path, "attempts"), len(attempts) - 1)
    if latest["status"] != status:
        _fail(_field_path(latest_path, "status"), "does not match capability")
    if status == "running" and latest["finished_at"] is not None:
        _fail(_field_path(latest_path, "finished_at"), "running attempt is finished")
    if status in {"failed", "succeeded"} and latest["finished_at"] is None:
        _fail(_field_path(latest_path, "finished_at"), "terminal attempt is unfinished")


def _validate_capability_invariants(state: dict[str, Any]) -> None:
    attempt_ids: set[str] = set()
    for name, capability in state["batch"]["capabilities"].items():
        path = _field_path("batch.capabilities", name)
        attempts = capability["attempts"]
        status = capability["status"]
        if status == "pending" and attempts:
            _fail(_field_path(path, "attempts"), "pending capability has attempts")
        if status == "skipped":
            if capability["required"]:
                _fail(_field_path(path, "required"), "required capability cannot skip")
            if attempts:
                _fail(_field_path(path, "attempts"), "skipped capability has attempts")
        if status in {"running", "failed", "succeeded"} and not attempts:
            _fail(
                _field_path(path, "attempts"), f"{status} capability needs an attempt"
            )
        _validate_capability_attempts(attempts, path, attempt_ids)
        _validate_latest_capability(capability, path)


def _validate_batch_invariants(state: dict[str, Any]) -> None:
    batch = state["batch"]
    if batch["status"] != "idle" and not batch["id"]:
        _fail("batch.id", "non-idle batch requires an identifier")
    if batch["status"] == "completed":
        if batch["completed_at"] is None:
            _fail("batch.completed_at", "completed batch requires a timestamp")
        for name, capability in batch["capabilities"].items():
            if capability["required"] and capability["status"] != "succeeded":
                _fail(
                    _field_path(_field_path("batch.capabilities", name), "status"),
                    "required capability must succeed before completion",
                )


def validate_state(value: object) -> State:
    document = _require_dict(value, "state")
    if "schema_version" not in document:
        _fail("schema_version", "required field is missing")
    version = _require_integer(document["schema_version"], "schema_version")
    if version != SCHEMA_VERSION:
        _fail("schema_version", f"must equal {SCHEMA_VERSION}")
    _check_decoded_json_depth(document, source="state")
    try:
        encoded = (
            json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
    except (
        TypeError,
        ValueError,
        OverflowError,
        RecursionError,
        UnicodeEncodeError,
    ) as error:
        try:
            _validate_owned(document, State, "")
        except SchemaError:
            raise
        except RecursionError:
            pass
        raise SchemaError(f"state: not a finite JSON document: {error}") from error
    if len(encoded) > MAX_STATE_BYTES:
        _limit("state", f"canonical document exceeds {MAX_STATE_BYTES} bytes")

    state = _validate_owned(document, State, "")
    _validate_task_invariants(state)
    _validate_review_invariants(state)
    _validate_capability_invariants(state)
    _validate_batch_invariants(state)
    return cast(State, copy.deepcopy(state))
