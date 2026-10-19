"""Private session evidence and durable run and completion records."""

from __future__ import annotations

import json
import math
import os
import stat
import sys
from collections.abc import Callable, Mapping
from contextlib import ExitStack
from dataclasses import asdict, dataclass, fields, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast, get_args
from uuid import uuid4

from ovcaq.events import sanitize_text
from ovcaq.paths import RuntimePaths
from ovcaq.runtime._run_observation import (
    RunObservation as RunObservation,  # noqa: PLC0414 - public re-export
)
from ovcaq.runtime._run_observation import (
    SelectedRunObservation as SelectedRunObservation,  # noqa: PLC0414 - public re-export
)
from ovcaq.runtime._run_observation import (
    observe_run as observe_run,  # noqa: PLC0414 - public re-export
)
from ovcaq.runtime._run_observation import (
    observe_selected_run as observe_selected_run,  # noqa: PLC0414 - public re-export
)
from ovcaq.runtime._session_evidence import (
    EvidenceLimitError as EvidenceLimitError,  # noqa: PLC0414 - public re-export
)
from ovcaq.runtime._session_evidence import (
    SessionEvidenceWriter as SessionEvidenceWriter,  # noqa: PLC0414 - public re-export
)
from ovcaq.runtime._session_io import (
    _encode_record,
    _private_directory,
    _publish,
)
from ovcaq.runtime.registry import FleetEntry, FleetRegistry
from ovcaq.state.schema import (
    MAX_STATE_BYTES,
    JSONValue,
    NextPhase,
    Phase,
    decode_json,
    validate_json_value,
    validate_timestamp,
)


@dataclass(frozen=True)
class SessionPaths:
    root: Path
    raw: Path
    normalized: Path
    metrics: Path
    metadata: Path
    summary: Path


@dataclass(frozen=True)
class SessionMetadata:
    schema_version: int
    run_id: str
    session_id: str
    agent: str
    pid: int
    process_start: str
    started_at: str


@dataclass(frozen=True, slots=True)
class SessionMetric:
    schema_version: Literal[1]
    kind: Literal["phase", "capability"]
    run_id: str
    session_id: str
    batch_id: str
    prd: str | None
    phase_launched: Phase | None
    capability: str | None
    phase_end: NextPhase | None
    decision: str | None
    started_at: str
    finished_at: str | None
    wall_seconds: float | None
    model: str | None
    usage: Mapping[str, int | float | bool | None] | None


def _validate_metric_completion_and_usage(metric: SessionMetric) -> None:
    final_fields: tuple[object, ...] = (
        metric.decision,
        metric.finished_at,
        metric.wall_seconds,
    )
    if metric.kind == "phase":
        final_fields += (metric.phase_end,)
    if any(value is None for value in final_fields) and any(
        value is not None for value in final_fields
    ):
        raise ValueError("metric completion fields must be all null or all non-null")
    if metric.usage is not None and (
        not isinstance(metric.usage, Mapping)
        or set(metric.usage)
        != {
            "input_tokens",
            "output_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
            "tool_uses",
            "cost_usd",
            "estimated",
        }
    ):
        raise ValueError("metric usage must contain exactly the normalized fields")
    for key, value in (metric.usage or {}).items():
        if key == "estimated":
            valid = isinstance(value, bool)
        elif value is None:
            valid = True
        elif key == "cost_usd":
            valid = (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
                and value >= 0
            )
        else:
            valid = type(value) is int and value >= 0
        if not valid:
            raise ValueError(f"invalid metric usage {key}")


def _metric_payload(metric: SessionMetric) -> bytes:
    for identifier in (metric.run_id, metric.session_id, metric.batch_id):
        _validate_identifier(identifier)
    if metric.phase_launched is not None and metric.phase_launched not in get_args(
        Phase
    ):
        raise ValueError("invalid metric phase_launched")
    if metric.phase_end is not None and metric.phase_end not in get_args(NextPhase):
        raise ValueError("invalid metric phase_end")
    if metric.kind == "phase":
        if (
            not metric.phase_launched
            or not metric.model
            or metric.capability is not None
        ):
            raise ValueError(
                "phase metrics require phase and model, without capability"
            )
    elif metric.kind == "capability":
        if (
            not metric.capability
            or metric.phase_launched is not None
            or metric.model is not None
        ):
            raise ValueError(
                "capability metrics require capability, without phase or model"
            )
    else:
        raise ValueError("invalid metric kind")
    _validate_metric_completion_and_usage(metric)
    validate_timestamp(metric.started_at, "metric.started_at")
    if metric.finished_at is not None:
        validate_timestamp(metric.finished_at, "metric.finished_at")
        if datetime.fromisoformat(metric.finished_at) < datetime.fromisoformat(
            metric.started_at
        ):
            raise ValueError("metric finished before it started")
    if metric.wall_seconds is not None and (
        isinstance(metric.wall_seconds, bool)
        or not isinstance(metric.wall_seconds, (int, float))
        or not math.isfinite(metric.wall_seconds)
        or metric.wall_seconds < 0
    ):
        raise ValueError("metric wall_seconds must be finite and nonnegative")
    return _encode_record(asdict(metric))


def metric_from_record(record: Mapping[str, JSONValue]) -> SessionMetric:
    """Validate one metric row against the same contract publishers enforce."""
    if not isinstance(record, dict) or set(record) != {
        field.name for field in fields(SessionMetric)
    }:
        raise ValueError("invalid session metric fields")
    metric = SessionMetric(**cast(Any, record))
    _metric_payload(metric)
    return metric


def _read_metric(path: Path) -> SessionMetric:
    lines = path.read_text().splitlines()
    if len(lines) != 1:
        raise ValueError("session metrics must contain exactly one row")
    return metric_from_record(
        cast(Mapping[str, JSONValue], decode_json(lines[0], source=str(path)))
    )


def publish_session_metric(
    paths: RuntimePaths, session: SessionPaths, metric: SessionMetric
) -> None:
    """Atomically publish pending evidence or finalize it once."""
    payload = _metric_payload(metric)
    metadata = parse_session_metadata(
        decode_json(session.metadata.read_text(), source=str(session.metadata))
    )
    if (metric.run_id, metric.session_id) != (metadata.run_id, metadata.session_id):
        raise ValueError("metric does not match session metadata")
    if session.metrics.exists():
        previous = _read_metric(session.metrics)
        if previous.decision is not None:
            raise ValueError("session metric is already final")
        if (previous.run_id, previous.session_id) != (metric.run_id, metric.session_id):
            raise ValueError("metric does not match pending identity")
    _publish(session.metrics, payload, identities=paths._identities)


def reconcile_metrics(paths: RuntimePaths) -> tuple[SessionMetric, ...]:
    """Rebuild the aggregate from retained canonical session evidence."""
    unique: dict[str, SessionMetric] = {}
    for path in sorted(paths.sessions.glob("*/metrics.jsonl")):
        metric = _read_metric(path)
        previous = unique.get(metric.session_id)
        if previous is None or previous.decision is None or metric.decision is not None:
            unique[metric.session_id] = metric
    rows = tuple(
        replace(metric, decision="interrupted") if metric.decision is None else metric
        for metric in sorted(
            unique.values(), key=lambda row: (row.started_at, row.session_id)
        )
    )
    _publish(
        paths.metrics,
        b"".join(_encode_record(asdict(row)) for row in rows),
        identities=paths._identities,
    )
    return rows


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    rows: tuple[SessionMetric, ...]
    complete: bool
    gaps: tuple[str, ...]


def observe_metrics(
    paths: RuntimePaths,
    *,
    batch_id: str,
    max_bytes: int = 16 * 1024 * 1024,
    max_records: int = 4096,
) -> MetricsSnapshot:
    """Read the aggregate within budgets, keeping each session's last batch row."""
    from ovcaq.events.tail import JsonlFollower

    follower = JsonlFollower(
        paths.metrics,
        metric_from_record,
        # Always start at byte zero; max_read_bytes caps the work instead.
        replay_bytes=sys.maxsize,
        max_records=max_records,
        max_read_bytes=max_bytes,
        max_record_bytes=MAX_STATE_BYTES,
    )
    try:
        batch = follower.read()
    finally:
        follower.close()
    latest: dict[str, SessionMetric] = {}
    for row in batch.records:
        if row.batch_id == batch_id:
            # Rows are cumulative updates; the last one in file order wins.
            latest.pop(row.session_id, None)
            latest[row.session_id] = row
    gaps = tuple(f"{gap.kind}: {gap.detail}" for gap in batch.gaps)
    if batch.backlog:
        gaps += ("backlog: aggregate exceeds the read budget",)
    return MetricsSnapshot(
        tuple(latest.values()), batch.complete_history and not gaps, gaps
    )


@dataclass(frozen=True, slots=True)
class SessionEvidenceStatus:
    raw: bool
    normalized: bool
    summary: bool
    raw_only: bool = False


def observe_session_evidence(
    paths: RuntimePaths, session_id: str
) -> SessionEvidenceStatus:
    """Report regular-file presence and raw-only content without following links."""
    _validate_identifier(session_id)
    root = paths.sessions / session_id
    present: list[bool] = []
    nonempty: list[bool] = []
    for name in ("raw.jsonl", "normalized.jsonl", "summary.json"):
        try:
            information = (root / name).lstat()
        except OSError:
            present.append(False)
            nonempty.append(False)
        else:
            present.append(stat.S_ISREG(information.st_mode))
            nonempty.append(present[-1] and information.st_size > 0)
    return SessionEvidenceStatus(
        raw=present[0],
        normalized=present[1],
        summary=present[2],
        raw_only=nonempty[0] and not nonempty[1],
    )


@dataclass(frozen=True, slots=True)
class EmergencyFailureObservation:
    present: bool
    detail: str | None
    malformed: bool
    created_at: str | None = None


def observe_emergency_failure(paths: RuntimePaths) -> EmergencyFailureObservation:
    """Observe the emergency marker read-only; unreadable evidence stays present."""
    try:
        evidence = _read_emergency(paths.runtime_root / "state-write-failed.json")
    except (OSError, ValueError, TypeError) as error:
        detail = f"unreadable emergency evidence ({type(error).__name__})"
        return EmergencyFailureObservation(True, detail, True)
    if evidence is None:
        return EmergencyFailureObservation(False, None, False)
    record = json.loads(evidence[0])
    detail = sanitize_text(f"{record['site']}: {record['detail']}")
    return EmergencyFailureObservation(True, detail, False, record["created_at"])


class EmergencyStateFailure(RuntimeError):
    """Unacknowledged emergency evidence prevents launching another session."""


@dataclass(frozen=True)
class FailureDisposition:
    state_recorded: bool
    emergency_path: Path | None
    block_launch: bool


def _validate_identifier(value: object) -> None:
    if (
        not isinstance(value, str)
        or value in {"", ".", ".."}
        or "/" in value
        or "\x00" in value
    ):
        raise ValueError("record identifier must be a single path component")


def _metadata_payload(metadata: SessionMetadata) -> bytes:
    record = asdict(metadata)
    _validate_identifier(metadata.run_id)
    _validate_identifier(metadata.session_id)
    if type(metadata.pid) is not int or metadata.pid <= 0:
        raise ValueError("metadata pid must be a positive integer")
    for field in ("agent", "process_start"):
        if not isinstance(record[field], str) or not record[field]:
            raise ValueError(f"metadata {field} must be a non-empty string")
    validate_timestamp(metadata.started_at, "metadata.started_at")
    return _encode_record(record)


def parse_session_metadata(record: object) -> SessionMetadata:
    """Validate the same closed metadata contract for readers and publishers."""
    if not isinstance(record, dict) or set(record) != {
        field.name for field in fields(SessionMetadata)
    }:
        raise ValueError("invalid session metadata fields")
    metadata = SessionMetadata(**cast(Any, record))
    _metadata_payload(metadata)
    return metadata


def create_session(paths: RuntimePaths, metadata: SessionMetadata) -> SessionPaths:
    """Create a new private evidence directory with committed metadata."""
    payload = _metadata_payload(metadata)
    root = paths.sessions / metadata.session_id
    session = SessionPaths(
        root=root,
        raw=root / "raw.jsonl",
        normalized=root / "normalized.jsonl",
        metrics=root / "metrics.jsonl",
        metadata=root / "meta.json",
        summary=root / "summary.json",
    )
    with ExitStack() as stack:
        sessions = _private_directory(
            paths.sessions,
            stack,
            identities=paths._identities,
            private=(paths.runtime_root,),
        )
        os.mkdir(metadata.session_id, mode=0o700, dir_fd=sessions)
        information = os.stat(
            metadata.session_id, dir_fd=sessions, follow_symlinks=False
        )
        directory = os.open(
            metadata.session_id,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=sessions,
        )
        stack.callback(os.close, directory)
        if not os.path.samestat(information, os.fstat(directory)):
            raise ValueError("session directory changed while opening")
        os.fchmod(directory, 0o700)
        _publish(session.metadata, payload, directory=directory)
    return session


def publish_run_metadata(paths: RuntimePaths, metadata: SessionMetadata) -> None:
    """Atomically publish the current run's session metadata."""
    _publish(
        paths.run_metadata, _metadata_payload(metadata), identities=paths._identities
    )


def cleanup_run_records(
    paths: RuntimePaths, metadata: SessionMetadata, entry: FleetEntry
) -> bool:
    """Durably remove matching owner records while retaining session evidence."""
    owner = asdict(metadata)
    del owner["session_id"]
    if entry != FleetEntry(root=paths.project_root, **owner):
        return False
    record = paths.run_metadata
    try:
        with ExitStack() as stack:
            directory = _private_directory(
                record.parent, stack, identities=paths._identities, create=False
            )
            _private_directory(
                paths.fleet_root, stack, identities=paths._identities, create=False
            )
            descriptor = os.open(
                record.name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory,
            )
            stream = stack.enter_context(os.fdopen(descriptor, "rb"))
            information = os.fstat(stream.fileno())
            if not stat.S_ISREG(information.st_mode):
                return False
            payload = stream.read(MAX_STATE_BYTES + 1)
            if len(payload) > MAX_STATE_BYTES:
                return False
            observed = parse_session_metadata(
                decode_json(payload.decode("utf-8"), source=str(record))
            )
            if observed != metadata or not os.path.samestat(
                information,
                os.stat(record.name, dir_fd=directory, follow_symlinks=False),
            ):
                return False
            if not FleetRegistry(paths.fleet_root).remove(entry.run_id, expected=entry):
                return False
            if not os.path.samestat(
                information,
                os.stat(record.name, dir_fd=directory, follow_symlinks=False),
            ):
                return False
            os.unlink(record.name, dir_fd=directory)
            os.fsync(directory)
    except (OSError, ValueError, TypeError):
        return False
    return True


def publish_session_summary(session: SessionPaths, summary: dict[str, object]) -> None:
    """Publish a validated completion record without altering raw evidence."""
    expected = {
        "schema_version",
        "session_id",
        "finished_at",
        "returncode",
        "signal",
        "timed_out",
        "detail",
    }
    if set(summary) != expected:
        raise ValueError("summary must contain exactly the completion record fields")
    _validate_identifier(summary["session_id"])
    validate_timestamp(summary["finished_at"], "summary.finished_at")
    if type(summary["returncode"]) is not int:
        raise ValueError("summary returncode must be an integer")
    if summary["signal"] is not None and type(summary["signal"]) is not int:
        raise ValueError("summary signal must be an integer or null")
    if type(summary["timed_out"]) is not bool:
        raise ValueError("summary timed_out must be a boolean")
    if summary["detail"] is not None and not isinstance(summary["detail"], str):
        raise ValueError("summary detail must be a string or null")
    payload = _encode_record(summary)
    if summary["session_id"] != session.root.name:
        raise ValueError("summary does not match the containing session directory")
    with ExitStack() as stack:
        directory = _private_directory(session.root, stack)
        descriptor = os.open(
            session.metadata.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=directory,
        )
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError("session metadata must be a regular file")
            metadata_payload = stream.read(MAX_STATE_BYTES + 1)
        if len(metadata_payload) > MAX_STATE_BYTES:
            raise ValueError("session metadata exceeds maximum document size")
        metadata = parse_session_metadata(
            decode_json(metadata_payload.decode("utf-8"), source=str(session.metadata))
        )
        if metadata.session_id != summary["session_id"]:
            raise ValueError("summary does not match session metadata")
        _publish(session.summary, payload, directory=directory)


def _emergency_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    record: dict[str, object] = {}
    for key, value in pairs:
        if key in record:
            raise ValueError("duplicate emergency record field")
        record[key] = value
    return record


def _read_emergency(marker: Path) -> tuple[bytes, os.stat_result] | None:
    try:
        information = marker.lstat()
    except FileNotFoundError:
        return None
    if (
        not stat.S_ISREG(information.st_mode)
        or stat.S_IMODE(information.st_mode) != 0o600
    ):
        raise ValueError("emergency evidence must be a private regular file")
    descriptor = os.open(marker, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not os.path.samestat(information, opened):
            raise ValueError("emergency evidence changed while opening")
        payload = stream.read(MAX_STATE_BYTES + 1)
    if len(payload) > MAX_STATE_BYTES:
        raise ValueError("emergency evidence exceeds maximum document size")
    try:
        record = json.loads(payload, object_pairs_hook=_emergency_fields)
    except RecursionError as error:
        raise ValueError("emergency evidence exceeds maximum nesting") from error
    if not isinstance(record, dict) or set(record) != {
        "schema_version",
        "site",
        "detail",
        "created_at",
    }:
        raise ValueError("invalid emergency record fields")
    for field in ("site", "detail"):
        if not isinstance(record[field], str):
            raise TypeError(f"emergency {field} must be a string")
    validate_timestamp(record["created_at"], "emergency.created_at")
    _encode_record(record)
    if not os.path.samestat(information, marker.lstat()):
        raise ValueError("emergency evidence changed while reading")
    return payload, information


def record_state_failure(
    paths: RuntimePaths,
    *,
    site: str,
    detail: str,
    write_state_notice: Callable[[str, str], None],
) -> FailureDisposition:
    """Stop the caller; persist emergency evidence if the state writer fails.

    Callers must supply diagnostics that contain no environment values. Callback
    exception text is deliberately excluded from the emergency record.
    """
    for field, value in (("site", site), ("detail", detail)):
        if not isinstance(value, str):
            raise TypeError(f"emergency {field} must be a string")
        validate_json_value(value, f"emergency.{field}")
    try:
        write_state_notice(site, detail)
    except Exception:  # noqa: BLE001, S110 - never log callback diagnostics
        pass
    else:
        return FailureDisposition(True, None, True)

    marker = paths.runtime_root / "state-write-failed.json"
    if _read_emergency(marker) is None:
        _publish(
            marker,
            _encode_record(
                {
                    "schema_version": 1,
                    "site": site,
                    "detail": detail,
                    "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                }
            ),
        )
    return FailureDisposition(False, marker, True)


def require_no_emergency_failure(paths: RuntimePaths) -> None:
    """Fail closed whenever emergency evidence exists or cannot be read."""
    try:
        evidence = _read_emergency(paths.runtime_root / "state-write-failed.json")
    except (OSError, ValueError, TypeError):
        raise EmergencyStateFailure("Emergency state evidence is unreadable") from None
    if evidence is not None:
        raise EmergencyStateFailure("Emergency state failure requires acknowledgement")


def _archive_emergency_evidence(
    paths: RuntimePaths, marker: Path, payload: bytes, information: os.stat_result
) -> Path:
    reports = paths.reports
    try:
        directory = reports.lstat()
    except FileNotFoundError:
        reports.mkdir(mode=0o700)
    else:
        if (
            not stat.S_ISDIR(directory.st_mode)
            or stat.S_IMODE(directory.st_mode) != 0o700
        ):
            raise ValueError("Emergency reports require a private directory")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    archive = reports / f"emergency-{stamp}.json"
    if not os.path.samestat(information, marker.lstat()):
        raise ValueError("Emergency evidence changed before acknowledgement")
    _publish(archive, payload)
    current = _read_emergency(marker)
    if (
        current is None
        or current[0] != payload
        or not os.path.samestat(information, current[1])
    ):
        raise ValueError("Emergency evidence changed before acknowledgement")
    return archive


def acknowledge_emergency_failure(paths: RuntimePaths, *, state_valid: bool) -> Path:
    """Durably archive validated evidence before removing the launch gate."""
    if state_valid is not True:
        raise ValueError("Validated state is required to acknowledge a failure")
    marker = paths.runtime_root / "state-write-failed.json"
    evidence = _read_emergency(marker)
    if evidence is None:
        raise ValueError("No emergency state failure to acknowledge")
    payload, information = evidence
    archive = _archive_emergency_evidence(paths, marker, payload, information)
    reports = archive.parent
    # Keep the retired inode reachable: a writer may already have it open, or a
    # replacement may arrive between verification and the rename.
    retired = reports / f"{archive.stem}-{uuid4().hex}.json"
    with ExitStack() as stack:
        report_fd = os.open(reports, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, report_fd)
        directory_fd = os.open(
            paths.runtime_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
        stack.callback(os.close, directory_fd)
        try:
            os.rename(marker, retired)
            os.fsync(report_fd)
            os.fsync(directory_fd)
            current = _read_emergency(retired)
            if (
                current is None
                or current[0] != payload
                or not os.path.samestat(information, current[1])
                or marker.exists()
                or marker.is_symlink()
            ):
                raise ValueError("Emergency evidence changed during acknowledgement")
            archive.unlink()
            os.fsync(report_fd)
        except (OSError, ValueError, TypeError):
            # A create-only link restores the gate without replacing evidence
            # published by another writer. Both archives remain available.
            try:
                os.link(retired, marker, follow_symlinks=False)
            except (FileExistsError, FileNotFoundError):
                pass
            os.fsync(directory_fd)
            raise
    return retired


@dataclass(frozen=True)
class EvidenceItem:
    session_id: str
    path: Path
    size_bytes: int
    modified_at: str
    active: bool
    device: int
    inode: int


@dataclass(frozen=True)
class EvidenceInventory:
    runtime_root: Path
    total_bytes: int
    sessions: tuple[EvidenceItem, ...]


@dataclass(frozen=True)
class PurgePlan:
    schema_version: Literal[1]
    runtime_root: Path
    selected: tuple[EvidenceItem, ...]
    total_bytes: int
    command: tuple[str, ...]


class ActiveSessionError(RuntimeError):
    """A running supervisor prevents evidence removal."""


def inventory_evidence(
    paths: RuntimePaths, *, run: RunObservation | None = None
) -> EvidenceInventory:
    """Observe retained regular evidence without following links or changing it."""
    from ovcaq.runtime._retention import inventory_evidence as inventory

    return inventory(paths, observe_run(paths) if run is None else run)


def plan_purge(
    paths: RuntimePaths,
    *,
    session_id: str | None = None,
    before: datetime | None = None,
    inventory: EvidenceInventory | None = None,
) -> PurgePlan:
    """Preview whole inactive sessions selected by identifier or strict cutoff."""
    from ovcaq.runtime._retention import plan_purge as plan

    return plan(paths, session_id=session_id, before=before, inventory=inventory)


def apply_purge(plan: PurgePlan) -> tuple[Path, ...]:
    """Remove reviewed evidence while excluding supervisors and other purges."""
    from ovcaq.runtime._retention import apply_purge as apply

    return apply(plan)
