"""Deterministic reduction of normalized observations into a session summary."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields
from datetime import datetime

from ovcaq.events.model import (
    PROTOCOL_VERSION,
    FailureClass,
    Observation,
    ObservationType,
    SessionSummary,
    Usage,
    _parse_utc,
)


@dataclass(frozen=True, slots=True)
class Reduction:
    observations: tuple[Observation, ...]
    summary: SessionSummary


@dataclass(slots=True)
class _SessionState:
    session_id: str | None = None
    source_session_id: str | None = None
    conflicting_identity: bool = False
    completed: bool = False
    failure_class: FailureClass | None = None
    failure_detail: str | None = None
    live_limit: Observation | None = None


def reduce_session(observations: Iterable[Observation], exit_code: int) -> Reduction:
    """Retain every observation and reduce terminal state and usage snapshots."""
    retained = tuple(observations)
    state = _SessionState()
    snapshots: list[Usage] = []
    for observation in retained:
        kind = observation.type
        payload = observation.payload
        if kind == ObservationType.SESSION_STARTED:
            source_session_id = payload.get("source_session_id")
            if isinstance(source_session_id, str):
                if state.source_session_id is None:
                    state.source_session_id = source_session_id
                elif source_session_id != state.source_session_id:
                    state.conflicting_identity = True
        if state.session_id is None and kind in (
            ObservationType.SESSION_STARTED,
            ObservationType.SESSION_COMPLETED,
            ObservationType.SESSION_FAILED,
        ):
            state.session_id = observation.session_id
        if (
            state.session_id is not None
            and observation.session_id is not None
            and observation.session_id != state.session_id
        ):
            state.conflicting_identity = True
        if kind == ObservationType.SESSION_COMPLETED:
            state.completed = True
        elif kind == ObservationType.SESSION_FAILED:
            state.failure_class = FailureClass(str(payload["failure_class"]))
            state.failure_detail = str(payload["detail"])
        elif kind == ObservationType.RATE_LIMIT_STARTED:
            state.live_limit = observation
        elif kind == ObservationType.RATE_LIMIT_CLEARED:
            state.live_limit = None
        if (
            kind
            in (
                ObservationType.USAGE_UPDATED,
                ObservationType.SESSION_COMPLETED,
            )
            and "usage" in payload
        ):
            serialized = payload["usage"]
            assert isinstance(serialized, Mapping)
            snapshots.append(Usage(**dict(serialized)))  # type: ignore[arg-type]
    return Reduction(retained, _session_summary(state, _usage(snapshots), exit_code))


def _usage(snapshots: list[Usage]) -> Usage | None:
    if not snapshots:
        return None
    values: dict[str, int | float | None] = {}
    estimated = False
    for field in fields(Usage):
        if field.name == "estimated":
            continue
        supplied = [
            getattr(snapshot, field.name)
            for snapshot in snapshots
            if getattr(snapshot, field.name) is not None
        ]
        winner = max(supplied) if supplied else None
        values[field.name] = winner
        if winner is not None and not any(
            not snapshot.estimated and getattr(snapshot, field.name) == winner
            for snapshot in snapshots
        ):
            estimated = True
    return Usage(**values, estimated=estimated)  # type: ignore[arg-type]


def _session_summary(
    state: _SessionState, usage: Usage | None, exit_code: int
) -> SessionSummary:
    failure_class = state.failure_class
    failure_detail = state.failure_detail
    success = state.completed and failure_class is None
    if not success and failure_class is None:
        failure_class = FailureClass.AGENT if exit_code else FailureClass.UNKNOWN
    reset_at = None
    if state.live_limit is not None:
        reset = state.live_limit.payload["reset_at"]
        reset_at = _parse_utc(reset) if reset is not None else None
        if not success and failure_class in (FailureClass.UNKNOWN, FailureClass.AGENT):
            failure_class = FailureClass.RATE_LIMIT
            failure_detail = str(state.live_limit.payload["detail"])
    if state.conflicting_identity:
        success = False
        failure_class = FailureClass.UNKNOWN
        failure_detail = None
        reset_at = None
    return SessionSummary(
        success=success,
        session_id=state.session_id,
        failure_class=failure_class,
        failure_detail=failure_detail,
        rate_limit_reset_at=reset_at,
        usage=usage,
    )


def session_failure_observation(
    *,
    timestamp: datetime,
    provider: str,
    run_id: str,
    session_id: str | None,
    failure_class: FailureClass,
    detail: str,
) -> Observation:
    """Build a validated, sanitized failure observation for a session."""
    return Observation(
        protocol_version=PROTOCOL_VERSION,
        timestamp=timestamp,
        provider=provider,
        run_id=run_id,
        session_id=session_id,
        lane_id=None,
        type=ObservationType.SESSION_FAILED,
        payload={"failure_class": failure_class.value, "detail": detail},
    )
