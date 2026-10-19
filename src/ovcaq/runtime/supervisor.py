"""Supervisor loop: launch workflow sessions and apply state-derived decisions."""

from __future__ import annotations

import os
import signal
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from ovcaq.config import SupervisorSettings, resolve_phase_route, workflow_settings
from ovcaq.drivers.base import AgentDriver, LaunchRequest, LaunchSpec
from ovcaq.events import (
    FailureClass,
    Observation,
    SessionSummary,
    session_failure_observation,
)
from ovcaq.events.tail import NormalizedEventWriter, RawFirstDecoder
from ovcaq.runtime._run_observation import publish_terminal_evidence
from ovcaq.runtime.capability import (
    CapabilityRunner,
    CapabilityService,
)
from ovcaq.runtime.decision import (
    AttemptResult,
    DecisionKind,
    ProgressSnapshot,
    RetryState,
    SupervisorDecision,
    boundary_decision,
    decide,
    progress_fingerprint,
    snapshot,
)
from ovcaq.runtime.process import (
    OwnedProcess,
    ProcessExit,
    SupervisorSignal,
    supervisor_exit_code,
    supervisor_signal_scope,
)
from ovcaq.runtime.registry import (
    FleetEntry,
    FleetRegistry,
    ProcessIdentity,
    RunLock,
    process_identity,
)
from ovcaq.runtime.session import (
    SessionEvidenceWriter,
    SessionMetadata,
    SessionMetric,
    SessionPaths,
    cleanup_run_records,
    create_session,
    publish_run_metadata,
    publish_session_metric,
    publish_session_summary,
    reconcile_metrics,
    record_state_failure,
    require_no_emergency_failure,
)
from ovcaq.runtime.watchdog import Clock as WatchdogClock
from ovcaq.runtime.watchdog import Watchdog
from ovcaq.state.commands import StateService
from ovcaq.state.schema import CapabilityEntry, Phase, SchemaError, State
from ovcaq.state.store import StateError, StateStore
from ovcaq.workflow.paths import resolve_lifecycle_paths
from ovcaq.workflow.records import park
from ovcaq.workflow.reports import archive_final_state

_CONTINUING = frozenset(
    {
        DecisionKind.CONTINUE,
        DecisionKind.RETRY,
        DecisionKind.WAIT,
        DecisionKind.PARK,
        DecisionKind.RUN_CAPABILITY,
        DecisionKind.SKIP_CAPABILITIES,
    }
)
_READ_CHUNK = 65536
_STATE_ERRORS = (StateError, SchemaError, OSError)


class Clock(WatchdogClock, Protocol):
    def now(self) -> datetime: ...


class CapabilityRunnerResolver(Protocol):
    def __call__(self, capability: CapabilityEntry) -> CapabilityRunner: ...


@dataclass(frozen=True, slots=True)
class SupervisorOutcome:
    exit_code: int
    decision: SupervisorDecision
    sessions_attempted: int


def _timestamp(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


class Supervisor:
    def __init__(
        self,
        root: Path,
        *,
        store: StateStore,
        driver: AgentDriver,
        settings: SupervisorSettings,
        capability_runner: CapabilityRunnerResolver,
        clock: Clock,
        sleeper: Callable[[float], None],
    ) -> None:
        self._root = root
        self._store = store
        self._driver = driver
        self._settings = settings
        self._paths = settings.runtime.paths
        self._capability_runner = capability_runner
        self._clock = clock
        self._sleeper = sleeper
        self._run_id: str | None = None
        self._metadata: SessionMetadata | None = None
        self._retries = RetryState()
        self._last_failure: FailureClass | None = None
        self._sessions = 0
        self._state_halt: SupervisorDecision | None = None

    def run(self) -> SupervisorOutcome:
        self._sessions = 0
        self._state_halt = None
        with RunLock.acquire(self._paths.run_lock):
            publish_terminal_evidence(self._paths)
            require_no_emergency_failure(self._paths)
            reconcile_metrics(self._paths)
            try:
                self._reconcile_capabilities()
                state = self._store.read()
                batch = state["batch"]
                if (
                    not batch["id"]
                    or not batch["started_at"]
                    or batch["status"] == "idle"
                ):
                    StateService(self._store).start_batch(
                        uuid4().hex,
                        _timestamp(self._clock.now()),
                        expected_revision=state["revision"],
                    )
            except _STATE_ERRORS:
                return SupervisorOutcome(1, self._state_failure("startup"), 0)
            metadata, entry = self._publish_ownership()
            try:
                with supervisor_signal_scope():
                    decision = self._loop()
            except SupervisorSignal as error:
                self._record_stop(supervisor_exit_code(error) - 128)
                return SupervisorOutcome(
                    supervisor_exit_code(error),
                    SupervisorDecision(DecisionKind.HALT, "supervisor signal"),
                    self._sessions,
                )
            finally:
                self._run_id = None
                try:
                    publish_terminal_evidence(
                        self._paths,
                        run_id=entry.run_id,
                        process=ProcessIdentity(entry.pid, entry.process_start),
                        state=self._store.read(),
                    )
                except _STATE_ERRORS:
                    pass
                finally:
                    cleanup_run_records(self._paths, self._metadata or metadata, entry)
        terminal_ok = decision.kind in (DecisionKind.PAUSE, DecisionKind.COMPLETE)
        return SupervisorOutcome(0 if terminal_ok else 1, decision, self._sessions)

    def _state_failure(self, site: str) -> SupervisorDecision:
        detail = "Supervisor state operation failed; inspect state before restarting."

        def write_notice(site: str, detail: str) -> None:
            def mutate(state: State) -> None:
                if state["control"]["attention"] is None:
                    state["control"]["attention"] = {
                        "site": site,
                        "detail": detail,
                        "created_at": _timestamp(self._clock.now()),
                    }

            self._store.transaction(mutate)

        record_state_failure(
            self._paths, site=site, detail=detail, write_state_notice=write_notice
        )
        self._state_halt = SupervisorDecision(DecisionKind.HALT, detail)
        return self._state_halt

    def _record_stop(self, number: int) -> None:
        def mutate(state: State) -> None:
            state["control"]["pause_requested"] = True
            if state["control"]["pause_reason"] is None:
                state["control"]["pause_reason"] = {
                    "site": "operator_stop",
                    "detail": f"Supervisor received signal {number}.",
                    "created_at": _timestamp(self._clock.now()),
                }

        try:
            self._store.transaction(mutate)
        except _STATE_ERRORS:
            self._state_failure("operator_stop")

    def _publish_ownership(self) -> tuple[SessionMetadata, FleetEntry]:
        run_id = uuid4().hex
        identity = process_identity(os.getpid())
        assert identity is not None
        started_at = _timestamp(self._clock.now())
        metadata = SessionMetadata(
            1,
            run_id,
            run_id,
            self._driver.name,
            identity.pid,
            identity.started,
            started_at,
        )
        entry = FleetEntry(
            1,
            self._paths.project_root,
            identity.pid,
            identity.started,
            run_id,
            self._driver.name,
            started_at,
        )
        publish_run_metadata(self._paths, metadata)
        FleetRegistry(self._paths.fleet_root).publish(entry)
        self._run_id = run_id
        self._metadata = metadata
        return metadata, entry

    def _loop(self) -> SupervisorDecision:
        while True:
            try:
                before = snapshot(self._store.read())
                decision = boundary_decision(before)
                if decision is None:
                    self._sessions += 1
                    _, decision = self._attempt()
                if not self.apply(decision):
                    return self._state_halt or decision
            except _STATE_ERRORS:
                return self._state_failure("supervisor.loop")

    def run_once(self) -> AttemptResult:
        require_no_emergency_failure(self._paths)
        result, _ = self._attempt()
        return result

    def apply(self, decision: SupervisorDecision) -> bool:
        kind = decision.kind
        if kind == DecisionKind.WAIT:
            self._sleeper(decision.wait_seconds or 0.0)
        elif kind == DecisionKind.COMPLETE:
            try:
                self._archive()
            except _STATE_ERRORS:
                self._state_failure("batch.complete")
                return False
        elif kind == DecisionKind.SKIP_CAPABILITIES:
            revision = self._store.read()["revision"]
            StateService(self._store).skip_empty_drain_capabilities(
                completed_at=_timestamp(self._clock.now()), expected_revision=revision
            )
        elif kind == DecisionKind.RUN_CAPABILITY:
            assert decision.capability is not None
            self._run_capability(decision.capability)
        elif kind == DecisionKind.PARK:
            result = park(
                self._store,
                paths=resolve_lifecycle_paths(
                    self._root, workflow_settings(self._root).prd_root
                ),
                runtime_root=self._paths.runtime_root,
                detail=decision.reason,
            )
            return not result.systemic_halt
        return kind in _CONTINUING

    def _archive(self) -> None:
        state = self._store.read()
        if state["batch"]["status"] != "completed":
            state = StateService(self._store).complete_batch(
                _timestamp(self._clock.now()), expected_revision=state["revision"]
            )
        archive_final_state(self._paths.runtime_root, state)

    def _capability_service(self, run_id: str) -> CapabilityService:
        return CapabilityService(
            self._root,
            store=self._store,
            paths=self._paths,
            run_id=run_id,
            clock=self._clock.now,
        )

    def _reconcile_capabilities(self) -> None:
        capabilities = self._store.read()["batch"]["capabilities"]
        running = [n for n, c in capabilities.items() if c["status"] == "running"]
        if running:
            service = self._capability_service(uuid4().hex)
            for name in running:
                service.reconcile(name)

    def _run_capability(self, name: str) -> None:
        service = self._capability_service(self._run_id or uuid4().hex)
        capability = self._store.read()["batch"]["capabilities"][name]
        runner = self._capability_runner(capability)
        try:
            service.run(name, runner)
        except Exception:
            if self._store.read()["batch"]["capabilities"][name]["status"] != "failed":
                raise
            # The service retained the runner failure; the next boundary halts.

    def _attempt(self) -> tuple[AttemptResult, SupervisorDecision]:
        state = self._store.read()
        before = snapshot(state)
        phase = state["work"]["next_phase"] or state["work"]["phase"]
        driver = self._driver
        route = resolve_phase_route(
            self._root,
            phase,
            agent=driver.name,
            phase_settings=self._settings.phases[phase],
        )
        prompt = (
            route.prompt if route.prompt is not None else driver.default_prompt(phase)
        )
        run_id = self._run_id or uuid4().hex
        started_at = self._clock.now()
        session, metric = self._open_session(
            state, phase, route.model, run_id, started_at
        )
        halt: Exception | None
        try:
            spec = driver.build_launch(
                LaunchRequest(
                    self._root,
                    phase,
                    prompt,
                    route.model,
                    route.effort,
                    route.timeout_seconds,
                    session.root,
                )
            )
            summary, exit_status, halt = self._collect(
                spec, route.timeout_seconds, session, run_id, metric.session_id
            )
        except Exception as error:
            summary = SessionSummary(
                False, metric.session_id, FailureClass.UNKNOWN, str(error), None, None
            )
            # ponytail: -1 marks "no child exit observed" (spawn failed or lost).
            exit_status = ProcessExit(-1, None, False, False, False)
            self._conclude(
                before, metric, session, summary, exit_status, error, started_at
            )
            raise
        return self._conclude(
            before, metric, session, summary, exit_status, halt, started_at
        )

    def _open_session(
        self,
        state: State,
        phase: Phase,
        model: str,
        run_id: str,
        started_at: datetime,
    ) -> tuple[SessionPaths, SessionMetric]:
        session_id = uuid4().hex
        identity = process_identity(os.getpid())
        assert identity is not None
        session = create_session(
            self._paths,
            SessionMetadata(
                1,
                run_id,
                session_id,
                self._driver.name,
                identity.pid,
                identity.started,
                _timestamp(started_at),
            ),
        )
        metric = SessionMetric(
            1,
            "phase",
            run_id,
            session_id,
            state["batch"]["id"],
            state["work"]["prd"],
            phase,
            None,
            None,
            None,
            _timestamp(started_at),
            None,
            None,
            model,
            None,
        )
        publish_session_metric(self._paths, session, metric)
        if self._metadata is not None:
            metadata = replace(self._metadata, session_id=session_id)
            publish_run_metadata(self._paths, metadata)
            self._metadata = metadata
        return session, metric

    def _collect(
        self,
        spec: LaunchSpec,
        timeout_seconds: int,
        session: SessionPaths,
        run_id: str,
        session_id: str,
    ) -> tuple[SessionSummary, ProcessExit, SupervisorSignal | None]:
        driver = self._driver
        runtime = self._settings.runtime
        raw = SessionEvidenceWriter(
            session.raw,
            max_bytes=runtime.max_session_bytes,
            min_free_bytes=runtime.min_free_bytes,
        )
        normalized = NormalizedEventWriter(
            session.normalized,
            max_bytes=runtime.max_session_bytes,
            min_free_bytes=runtime.min_free_bytes,
        )
        decoder = RawFirstDecoder(
            raw=raw,
            normalized=normalized,
            driver=driver,
            run_id=run_id,
            session_id=session_id,
        )
        try:
            observations, exit_status, interrupted = self._stream(
                spec, timeout_seconds, decoder
            )
            if exit_status.timed_out:
                self._record_timeout(normalized, observations, run_id, session_id)
            summary = driver.summarize(observations, exit_status.returncode)
            if exit_status.timed_out:
                summary = SessionSummary(
                    False,
                    session_id,
                    FailureClass.TIMEOUT,
                    "session timed out",
                    None,
                    summary.usage,
                )
            return summary, exit_status, interrupted
        finally:
            try:
                raw.close()
            finally:
                normalized.close()

    def _record_timeout(
        self,
        normalized: NormalizedEventWriter,
        observations: list[Observation],
        run_id: str,
        session_id: str,
    ) -> None:
        timeout = session_failure_observation(
            timestamp=self._clock.now(),
            provider=self._driver.name,
            run_id=run_id,
            session_id=session_id,
            failure_class=FailureClass.TIMEOUT,
            detail="session timed out",
        )
        normalized.write(timeout)
        observations.append(timeout)

    def _stream(
        self, spec: LaunchSpec, timeout_seconds: int, decoder: RawFirstDecoder
    ) -> tuple[list[Observation], ProcessExit, SupervisorSignal | None]:
        observations: list[Observation] = []
        interrupted: SupervisorSignal | None = None
        process = OwnedProcess.spawn(
            spec.argv, cwd=spec.cwd, env=os.environ | dict(spec.env)
        )
        watchdog = Watchdog(
            process,
            timeout_seconds=timeout_seconds,
            grace_seconds=self._settings.runtime.term_grace_seconds,
            clock=self._clock,
        )
        eof = False
        try:
            watchdog.start()
            while chunk := os.read(process.stdout.fileno(), _READ_CHUNK):
                observations.extend(decoder.feed(chunk))
            eof = True
        except SupervisorSignal as error:
            interrupted = error
        finally:
            if not eof:
                process.signal_group(signal.SIGKILL)
            watchdog.cancel()
            fired = watchdog.join()
            exit_status = process.collect_exit(
                timed_out=fired.fired,
                term_sent=fired.term_sent,
                kill_sent=fired.kill_sent,
            )
        observations.extend(decoder.finish())
        return observations, exit_status, interrupted

    def _publish_summary(
        self,
        session: SessionPaths,
        session_id: str,
        summary: SessionSummary,
        exit_status: ProcessExit,
        finished_at: datetime,
        halt: Exception | None,
    ) -> None:
        detail = summary.failure_detail
        if isinstance(halt, SupervisorSignal):
            detail = "supervisor signal"
        publish_session_summary(
            session,
            {
                "schema_version": 1,
                "session_id": session_id,
                "finished_at": _timestamp(finished_at),
                "returncode": exit_status.returncode,
                "signal": exit_status.signal,
                "timed_out": exit_status.timed_out,
                "detail": detail,
            },
        )

    def _conclude(
        self,
        before: ProgressSnapshot,
        metric: SessionMetric,
        session: SessionPaths,
        summary: SessionSummary,
        exit_status: ProcessExit,
        halt: Exception | None,
        started_at: datetime,
    ) -> tuple[AttemptResult, SupervisorDecision]:
        finished_at = self._clock.now()
        self._publish_summary(
            session, metric.session_id, summary, exit_status, finished_at, halt
        )
        state_after: State | None = None
        state_error: str | None = None
        try:
            state_after = self._store.read()
        except _STATE_ERRORS:
            state_error = self._state_failure("session.finish").reason
        result = AttemptResult(
            summary,
            started_at,
            finished_at,
            None if state_after is None else snapshot(state_after),
            state_error,
        )
        if isinstance(halt, SupervisorSignal):
            decision = SupervisorDecision(DecisionKind.HALT, "supervisor signal")
        elif halt is not None:
            decision = SupervisorDecision(DecisionKind.HALT, f"session failed: {halt}")
        else:
            decision = self._decide(before, result, state_after)
        metric = replace(
            metric,
            phase_end=metric.phase_launched
            if state_after is None
            else state_after["work"]["phase"],
            decision=decision.kind.value,
            finished_at=_timestamp(finished_at),
            wall_seconds=max(0.0, (finished_at - started_at).total_seconds()),
            usage=None if summary.usage is None else asdict(summary.usage),
        )
        publish_session_metric(self._paths, session, metric)
        reconcile_metrics(self._paths)
        if isinstance(halt, SupervisorSignal):
            raise halt
        return result, decision

    def _decide(
        self, before: ProgressSnapshot, result: AttemptResult, after: State | None
    ) -> SupervisorDecision:
        failure = result.summary.failure_class
        if failure != self._last_failure:
            self._retries = RetryState()
        self._last_failure = failure
        decision = decide(
            before, result, self._retries, self._settings.policy, now=self._clock.now()
        )
        if decision.kind == DecisionKind.CONTINUE:
            self._retries = RetryState()
        elif decision.kind == DecisionKind.RETRY:
            self._retries = replace(self._retries, died=self._retries.died + 1)
        elif decision.kind == DecisionKind.WAIT:
            if failure == FailureClass.CONNECTIVITY:
                self._retries = replace(
                    self._retries, connectivity=self._retries.connectivity + 1
                )
            elif failure == FailureClass.RATE_LIMIT:
                self._retries = replace(
                    self._retries, rate_limit=self._retries.rate_limit + 1
                )
        if after is not None and decision.next_phase_repeats is not None:
            try:
                StateService(self._store).record_progress(
                    progress_fingerprint(after),
                    decision.next_phase_repeats,
                    expected_revision=after["revision"],
                )
            except _STATE_ERRORS:
                return self._state_failure("session.progress")
        return decision
