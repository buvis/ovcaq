from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from ovcaq.config import RuntimeSettings
from ovcaq.events.model import Observation
from ovcaq.events.tail import TailBatch
from ovcaq.runtime.registry import FleetEntry, FleetRegistry, FleetRun, ProcessIdentity
from ovcaq.runtime.session import (
    EmergencyFailureObservation,
    MetricsSnapshot,
    RunObservation,
    SessionEvidenceStatus,
)
from ovcaq.state.schema import State
from ovcaq.tui import model


class FixedClock(datetime):
    @classmethod
    def now(cls, tz: object = None) -> datetime:
        current = datetime(2026, 10, 3, 10, 5, tzinfo=UTC)
        return current if tz is not None else current.replace(tzinfo=None)


@dataclass
class Projection:
    run: FleetRun
    settings: RuntimeSettings
    state: State
    registry: FleetRegistry
    entry: FleetEntry
    observation: RunObservation = field(
        default_factory=lambda: RunObservation("active", active_session_id="session-1")
    )
    metrics: MetricsSnapshot = field(
        default_factory=lambda: MetricsSnapshot((), True, ())
    )
    evidence: SessionEvidenceStatus = field(
        default_factory=lambda: SessionEvidenceStatus(True, True, False)
    )
    emergency: EmergencyFailureObservation = field(
        default_factory=lambda: EmergencyFailureObservation(False, None, False)
    )
    batches: deque[TailBatch[Observation]] = field(default_factory=deque)
    observer: model.ProjectObserver | None = None

    def owned_observation(self, paths: object) -> RunObservation:
        return replace(
            self.observation,
            run_id=self.observation.run_id or self.run.run_id,
            process=self.observation.process
            or ProcessIdentity(self.run.pid, self.run.process_start),
        )

    def poll(self) -> model.ProjectView:
        assert self.observer is not None
        return self.observer.poll()
