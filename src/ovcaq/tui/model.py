"""Project shared run observations into immutable, display-safe views."""

from __future__ import annotations

import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from ovcaq.config import RuntimeSettings
from ovcaq.events.model import Observation, ObservationType, observation_from_record
from ovcaq.events.tail import JsonlFollower
from ovcaq.runtime.registry import FleetRun, ProcessIdentity
from ovcaq.runtime.session import (
    EmergencyFailureObservation,
    MetricsSnapshot,
    RunObservation,
    SelectedRunObservation,
    SessionMetric,
    observe_emergency_failure,
    observe_metrics,
    observe_selected_run,
    observe_session_evidence,
)
from ovcaq.state.schema import (
    CapabilityStatus,
    NextPhase,
    Notice,
    Phase,
    State,
)

TelemetryLevel = Literal["complete", "partial", "raw-only", "unavailable"]
RunStatus = Literal[
    "running",
    "pause-requested",
    "paused",
    "parking",
    "stopping",
    "stopped",
    "state-write-failed",
    "attention",
    "halted",
    "completed",
    "inconsistent",
    "unknown",
]
LaneStatus = Literal["running", "completed", "failed", "unknown"]

MAX_LANES = 256
MAX_ACTIVITY = 256
MAX_GAPS = 128
MAX_USAGE_SESSIONS = 256
GAPS_OMITTED = "additional telemetry gaps omitted"
_HIDDEN_CATEGORIES = {"Cc", "Cf", "Cs", "Zl", "Zp"}
_LANE_STATUS: dict[ObservationType, LaneStatus] = {
    ObservationType.LANE_STARTED: "running",
    ObservationType.LANE_PROGRESS: "running",
    ObservationType.LANE_COMPLETED: "completed",
    ObservationType.LANE_FAILED: "failed",
}
_USAGE_COUNTERS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "tool_uses",
    "cost_usd",
)
_OBSERVATION_ERRORS = (OSError, ValueError)


@dataclass(frozen=True, slots=True)
class ActivityLane:
    lane_id: str
    label: str
    status: LaneStatus
    detail: str | None


@dataclass(frozen=True, slots=True)
class ActivityItem:
    label: str
    status: str | None
    detail: str | None


@dataclass(frozen=True, slots=True)
class UsageView:
    input_tokens: int | None
    output_tokens: int | None
    cache_creation_input_tokens: int | None
    cache_read_input_tokens: int | None
    tool_uses: int | None
    cost_usd: float | None
    estimated: bool
    partial: bool


@dataclass(frozen=True, slots=True)
class CapabilityView:
    name: str
    status: CapabilityStatus
    required: bool
    detail: str | None
    retry_command: tuple[str, ...] | None
    session_id: str | None = None
    evidence_path: Path | None = None


@dataclass(frozen=True, slots=True)
class ProjectView:
    run: FleetRun
    status: RunStatus
    phase: Phase | None
    next_phase: NextPhase | None
    prd: str | None
    revision: int | None
    tasks_completed: int | None
    tasks_total: int | None
    review_cycle: int | None
    provider: str
    duration_seconds: float | None
    usage: UsageView | None
    lanes: tuple[ActivityLane, ...]
    capabilities: tuple[CapabilityView, ...]
    attention: Notice | None
    telemetry: TelemetryLevel
    gaps: tuple[str, ...]
    ended: bool = False
    activity: tuple[ActivityItem, ...] = ()


def display_text(value: str, *, limit: int = 512) -> str:
    """Drop terminal/format controls and cap length; markup stays literal."""
    text = "".join(
        character
        for character in value
        if unicodedata.category(character) not in _HIDDEN_CATEGORIES
    )
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _guard[T](
    gaps: list[str], label: str, read: Callable[..., T], *args: object, **kwargs: object
) -> T | None:
    try:
        return read(*args, **kwargs)
    except _OBSERVATION_ERRORS as error:
        gaps.append(f"{label} unavailable: {type(error).__name__}")
        return None


def _payload_text(event: Observation, key: str, gaps: list[str]) -> str | None:
    value = event.payload.get(key)
    if value is None or isinstance(value, str):
        return None if value is None else display_text(value)
    gaps.append(f"lane {display_text(str(event.lane_id))} has malformed {key}")
    return None


def _emergency_current(
    emergency: EmergencyFailureObservation | None, run: FleetRun
) -> bool:
    """Old well-formed evidence predates this run; malformed evidence stays current."""
    if emergency is None or not emergency.present:
        return False
    if emergency.malformed or emergency.created_at is None:
        return True
    try:
        created = datetime.fromisoformat(emergency.created_at)
        started = datetime.fromisoformat(run.started_at)
    except ValueError:
        return True
    return created >= started


def _status(
    state: State | None,
    observation: RunObservation | None,
    emergency: EmergencyFailureObservation | None,
    rows: tuple[SessionMetric, ...],
    *,
    ended: bool = False,
) -> RunStatus:
    if emergency is not None:
        return "state-write-failed"
    if observation is not None and observation.status == "inconsistent":
        return "inconsistent"
    if state is None:
        return "unknown"
    control, batch = state["control"], state["batch"]
    reason = control["pause_reason"]
    if control["pause_requested"] and reason and reason["site"] == "operator_stop":
        return "stopping"
    if state["recovery"]["operation"] is not None:
        return "parking"
    if control["pause_requested"]:
        return "pause-requested"
    if (
        control["attention"] is not None
        or batch["status"] == "attention"
        or any(
            entry["required"] and entry["status"] == "failed"
            for entry in batch["capabilities"].values()
        )
    ):
        return (
            "halted"
            if ended and rows and rows[-1].decision in ("halt", "park")
            else "attention"
        )
    if state["work"]["phase"] == "paused":
        return "paused"
    if rows and rows[-1].decision == "halt":
        return "halted"
    if batch["status"] == "completed":
        return "completed"
    if (
        batch["status"] == "running"
        and observation is not None
        and observation.status == "active"
    ):
        return "running"
    return "unknown"


def _usage_view(
    sources: list[Mapping[str, object]], missing: bool, complete: bool
) -> UsageView | None:
    if not sources:
        return None

    def total(name: str) -> int | None:
        known = [value for s in sources if isinstance(value := s.get(name), int)]
        return sum(known) if known else None

    costs = [
        value for s in sources if isinstance(value := s.get("cost_usd"), (int, float))
    ]
    return UsageView(
        total("input_tokens"),
        total("output_tokens"),
        total("cache_creation_input_tokens"),
        total("cache_read_input_tokens"),
        total("tool_uses"),
        sum(costs) if costs else None,
        any(source.get("estimated") is True for source in sources),
        not complete
        or missing
        or any(s.get(name) is None for s in sources for name in _USAGE_COUNTERS),
    )


def _capabilities(
    run: FleetRun, state: State, sessions: Path
) -> tuple[CapabilityView, ...]:
    views = []
    for name, entry in sorted(state["batch"]["capabilities"].items()):
        attempts = entry["attempts"]
        detail = attempts[-1]["detail"] if attempts else None
        session_id = attempts[-1]["session_id"] if attempts else None
        retry = (
            ("ovcaq", "--root", str(run.root), "capability", "retry", name)
            if entry["status"] == "failed"
            else None
        )
        views.append(
            CapabilityView(
                display_text(name),
                entry["status"],
                entry["required"],
                None if detail is None else display_text(detail),
                retry,
                session_id,
                sessions / session_id if session_id is not None else None,
            )
        )
    return tuple(views)


def _bounded_gaps(gaps: list[str]) -> tuple[str, ...]:
    unique = tuple(dict.fromkeys(display_text(gap) for gap in gaps))
    if len(unique) <= MAX_GAPS:
        return unique
    return (*unique[: MAX_GAPS - 1], GAPS_OMITTED)


class ProjectObserver:
    """Poll one selected run's shared observations into a ProjectView."""

    def __init__(self, run: FleetRun, settings: RuntimeSettings) -> None:
        self._run = run
        self._paths = settings.paths
        self._batch_id: str | None = None
        self._view: ProjectView | None = None
        self._ended = False
        self._follower = JsonlFollower(
            settings.paths.events,
            # The tail and event modules declare equal but distinct JSON aliases.
            cast(
                Callable[[Mapping[str, object]], Observation], observation_from_record
            ),
        )
        self._session_id: str | None = None
        self._gaps: tuple[str, ...] = ()
        self._clear()

    def _clear(self) -> None:
        self._lanes: dict[str, ActivityLane] = {}
        self._activity: dict[tuple[str, str], ActivityItem] = {}
        self._activity_sequence = 0
        self._usage: dict[str | None, Mapping[str, object]] = {}
        self._provider = "unknown"
        self._normalized = False
        self._raw = False

    def close(self) -> None:
        self._follower.close()

    def poll(self) -> ProjectView:
        if self._view is not None and self._view.ended:
            return self._view
        gaps: list[str] = []
        state, observation, emergency, metrics, raw_evidence = self._observe(gaps)
        rows = metrics.rows if metrics is not None else ()
        for row in rows:
            if row.finished_at is not None:
                self._usage.pop(row.session_id, None)
        live_usage = list(self._usage.values())
        usage = _usage_view(
            [*(row.usage for row in rows if row.usage is not None), *live_usage],
            any(row.usage is None for row in rows),
            (metrics is None or metrics.complete) and not live_usage,
        )
        status = _status(
            state,
            observation,
            emergency if _emergency_current(emergency, self._run) else None,
            rows,
            ended=self._ended,
        )
        if state is None and self._view is not None:
            self._view = replace(
                self._view,
                status="unknown",
                ended=self._ended,
                duration_seconds=None if self._ended else self._view.duration_seconds,
                telemetry="partial",
                gaps=_bounded_gaps([*self._view.gaps, *gaps]),
            )
        else:
            self._view = self._project(
                state,
                status,
                usage,
                raw_evidence,
                rows,
                gaps,
            )
        if self._view.ended:
            self.close()
        return self._view

    def _duration(
        self, state: State | None, rows: tuple[SessionMetric, ...]
    ) -> float | None:
        try:
            started = datetime.fromisoformat(self._run.started_at)
            end = datetime.now(UTC)
            if self._ended:
                completed = state["batch"]["completed_at"] if state else None
                end = (
                    datetime.fromisoformat(completed)
                    if completed is not None
                    else max(
                        datetime.fromisoformat(row.finished_at)
                        for row in rows
                        if row.run_id == self._run.run_id
                        and row.finished_at is not None
                    )
                )
            elapsed = (end - started).total_seconds()
            return elapsed if elapsed >= 0 else None
        except (ValueError, TypeError):
            return None

    def _project(
        self,
        state: State | None,
        status: RunStatus,
        usage: UsageView | None,
        raw_evidence: bool,
        rows: tuple[SessionMetric, ...],
        gaps: list[str],
    ) -> ProjectView:
        bounded = _bounded_gaps(gaps)
        duration_seconds = self._duration(state, rows)
        work = state["work"] if state is not None else None
        notice = state["control"]["attention"] if state is not None else None
        return ProjectView(
            run=self._run,
            status="stopped" if self._ended and status == "stopping" else status,
            phase=work["phase"] if work else None,
            next_phase=work["next_phase"] if work else None,
            prd=display_text(work["prd"]) if work and work["prd"] else None,
            revision=state["revision"] if state is not None else None,
            tasks_completed=work["tasks_completed"] if work else None,
            tasks_total=work["tasks_total"] if work else None,
            review_cycle=state["review"]["cycle"] if state is not None else None,
            provider=self._provider,
            duration_seconds=duration_seconds,
            usage=usage,
            lanes=tuple(self._lanes.values()),
            capabilities=(
                _capabilities(self._run, state, self._paths.sessions) if state else ()
            ),
            attention=None
            if notice is None
            else Notice(
                site=display_text(notice["site"]),
                detail=display_text(notice["detail"]),
                created_at=notice["created_at"],
            ),
            telemetry=self._telemetry(bounded, raw_evidence, bool(rows)),
            gaps=bounded,
            ended=self._ended,
            activity=tuple(self._activity.values()),
        )

    def _telemetry(
        self, gaps: tuple[str, ...], raw_evidence: bool, has_rows: bool
    ) -> TelemetryLevel:
        if gaps:
            return "partial"
        if not self._normalized and (self._raw or raw_evidence):
            return "raw-only"
        if not self._normalized and not has_rows:
            return "unavailable"
        return "complete"

    def _observe(
        self, gaps: list[str]
    ) -> tuple[
        State | None,
        RunObservation | None,
        EmergencyFailureObservation | None,
        MetricsSnapshot | None,
        bool,
    ]:
        try:
            with observe_selected_run(
                self._paths, self._run, batch_id=self._batch_id
            ) as selected:
                evidence = self._evidence(selected, gaps)
        except _OBSERVATION_ERRORS as error:
            selected = SelectedRunObservation(
                None,
                RunObservation("inconsistent"),
                self._ended,
                (f"selected run unavailable: {type(error).__name__}",),
            )
        if selected.state is None:
            # Preserve only this selection's live session across an invalidated
            # sample, so a later attested terminal frame can consume final events.
            if selected.ended or (
                selected.observation.run_id,
                selected.observation.process,
            ) != (
                self._run.run_id,
                ProcessIdentity(self._run.pid, self._run.process_start),
            ):
                self.close()
                self._clear()
                self._session_id, self._gaps = None, ()
            self._ended = selected.ended
            gaps.extend(selected.gaps)
            return None, selected.observation, None, None, False
        self._batch_id = selected.state["batch"]["id"]
        return evidence

    def _evidence(
        self, selected: SelectedRunObservation, gaps: list[str]
    ) -> tuple[
        State | None,
        RunObservation,
        EmergencyFailureObservation | None,
        MetricsSnapshot | None,
        bool,
    ]:
        state, observation = selected.state, selected.observation
        self._ended = selected.ended
        gaps.extend(selected.gaps)
        emergency = metrics = evidence = None
        if state is not None:
            emergency = _guard(
                gaps, "emergency marker", observe_emergency_failure, self._paths
            )
            metrics = _guard(
                gaps,
                "metrics",
                observe_metrics,
                self._paths,
                batch_id=state["batch"]["id"],
            )
            session_id = (
                self._session_id if self._ended else observation.active_session_id
            )
            if session_id is not None:
                evidence = _guard(
                    gaps,
                    "session evidence",
                    observe_session_evidence,
                    self._paths,
                    session_id,
                )
                self._apply(session_id, gaps)
        if emergency is not None and emergency.malformed:
            gaps.append("emergency failure marker is malformed")
        if metrics is not None:
            gaps.extend(
                metrics.gaps or (() if metrics.complete else ("metrics incomplete",))
            )
        raw_evidence = evidence is not None and evidence.raw_only
        return state, observation, emergency, metrics, raw_evidence

    def _apply(self, session_id: str, gaps: list[str]) -> None:
        if session_id != self._session_id:
            self.close()
            self._follower = JsonlFollower(
                self._paths.sessions / session_id / "normalized.jsonl",
                cast(
                    Callable[[Mapping[str, object]], Observation],
                    observation_from_record,
                ),
            )
            self._session_id, self._gaps = session_id, ()
            self._clear()
        batch = _guard(gaps, "events", self._follower.read)
        if batch is None:
            return
        if batch.reset:
            self._clear()
        persistent = list(self._gaps)
        persistent.extend(f"events {g.kind}: {g.detail}" for g in batch.gaps)
        if not batch.complete_history and not batch.backlog:
            persistent.append("event history incomplete")
        self._gaps = _bounded_gaps(persistent)
        gaps.extend(self._gaps)
        if batch.backlog:
            gaps.append("event backlog pending")
        for event in batch.records:
            if (event.run_id, event.session_id) != (self._run.run_id, session_id):
                continue
            self._provider = display_text(event.provider)
            if event.type is ObservationType.RAW_UNKNOWN:
                self._raw = True
                continue
            self._normalized = True
            if event.type is ObservationType.USAGE_UPDATED:
                usage = event.payload["usage"]
                assert isinstance(usage, Mapping)
                # Latest identity per session wins; re-insert to mark it newest.
                self._usage.pop(event.session_id, None)
                self._usage[event.session_id] = usage
                if len(self._usage) > MAX_USAGE_SESSIONS:
                    del self._usage[next(iter(self._usage))]
            elif event.type in _LANE_STATUS and event.lane_id is not None:
                self._observe_lane(event, event.lane_id, gaps)
            elif event.type in (
                ObservationType.TOOL_STARTED,
                ObservationType.TOOL_COMPLETED,
                ObservationType.TOOL_FAILED,
                ObservationType.ACTIVITY_MESSAGE,
            ):
                self._observe_activity(event)

    def _observe_activity(self, event: Observation) -> None:
        payload = event.payload
        if event.type is ObservationType.ACTIVITY_MESSAGE:
            message_id = payload.get("message_id")
            if isinstance(message_id, str) and message_id.strip():
                key = ("message", message_id)
            else:
                self._activity_sequence += 1
                key = ("anonymous", str(self._activity_sequence))
            label = display_text(str(payload.get("kind", "message")))
            detail = payload.get("text")
            if detail is None:
                detail = payload.get("detail")
            if label == "plan":
                items = payload.get("items", ())
                if isinstance(items, (tuple, list)):
                    detail = " / ".join(
                        ("done: " if item.get("completed") is True else "pending: ")
                        + display_text(str(item.get("text", "")))
                        for item in items[:MAX_ACTIVITY]
                        if isinstance(item, Mapping)
                    )
            status = None
        else:
            key = ("tool", display_text(str(payload.get("tool_id", ""))))
            previous = self._activity.get(key)
            label = display_text(
                str(payload.get("name", previous.label if previous else "tool"))
            )
            detail = payload.get("detail")
            status = event.type.value.removeprefix("tool.")
        self._activity.pop(key, None)
        self._activity[key] = ActivityItem(
            label, status, None if detail is None else display_text(str(detail))
        )
        if len(self._activity) > MAX_ACTIVITY:
            del self._activity[next(iter(self._activity))]

    def _observe_lane(self, event: Observation, lane_id: str, gaps: list[str]) -> None:
        previous = self._lanes.get(lane_id)
        label = _payload_text(event, "label", gaps)
        if label is None:
            label = _payload_text(event, "description", gaps)
        detail = _payload_text(event, "detail", gaps)
        status = _LANE_STATUS[event.type]
        if event.type is not ObservationType.LANE_STARTED and (
            previous is None or previous.status == "unknown"
        ):
            status = "unknown"
            gaps.append(
                f"lane {display_text(lane_id)} seen without its start; "
                "history incomplete"
            )
        self._lanes[lane_id] = ActivityLane(
            display_text(lane_id),
            label or (previous.label if previous else display_text(lane_id)),
            status,
            detail if detail is not None else (previous.detail if previous else None),
        )
        if len(self._lanes) > MAX_LANES:
            # ponytail: linear scan, fine at 256 lanes.
            victim = next(
                (
                    key
                    for key, lane in self._lanes.items()
                    if lane.status in ("completed", "failed")
                ),
                next(iter(self._lanes)),
            )
            del self._lanes[victim]
