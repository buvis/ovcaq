"""Behavioral checks for the process supervisor's platform requirements."""

from __future__ import annotations

import fcntl
import json
import os
import select
import signal
import struct
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol
from uuid import uuid4

from ovcaq.config import supervisor_settings, validate_capability_timeout
from ovcaq.errors import CommandError, ErrorCode
from ovcaq.paths import RuntimePaths
from ovcaq.runtime.registry import ProcessIdentity, process_identity, process_matches
from ovcaq.runtime.session import (
    SessionMetadata,
    SessionMetric,
    SessionPaths,
    create_session,
    parse_session_metadata,
    publish_session_metric,
    reconcile_metrics,
)
from ovcaq.state.commands import StateService
from ovcaq.state.schema import CapabilityAttempt, State
from ovcaq.state.store import StateStore

_NAMES = (
    "platform",
    "advisory_lock",
    "process_group",
    "group_signal",
    "directory_fsync",
    "process_identity",
)
_DEFAULT_TIMEOUT = object()
_LOCK_CONTENDER = """
import fcntl
import sys

with open(sys.argv[1], "rb") as stream:
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("contended")
    else:
        print("acquired")
"""
_SIGNAL_WORKER = """
import os
import signal
import sys

signal.signal(signal.SIGUSR1, lambda *_: os.write(1, b"signalled\\n"))
os.write(1, b"ready\\n")
sys.stdin.read()
"""


@dataclass(frozen=True)
class CapabilityResult:
    name: str
    status: str
    detail: str


def probe_platform(*, platform_name: str | None = None) -> tuple[CapabilityResult, ...]:
    """Exercise locking, isolation, delivery, and directory durability on macOS."""
    platform_name = sys.platform if platform_name is None else platform_name
    if platform_name != "darwin" or sys.platform != "darwin":
        return tuple(
            CapabilityResult(name, "unsupported", "Personal cutover requires macOS")
            for name in _NAMES
        )

    results = [CapabilityResult("platform", "supported", "Running on macOS")]
    results.append(_probe_advisory_lock())
    results.extend(_probe_process_group())
    results.append(_probe_directory_fsync())
    results.append(_probe_process_identity())
    return tuple(results)


def _probe_advisory_lock() -> CapabilityResult:
    try:
        with TemporaryDirectory(prefix="ovcaq-lock-probe-") as directory:
            path = Path(directory) / "probe.lock"
            with path.open("w+b") as stream:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                blocked = subprocess.run(
                    [sys.executable, "-c", _LOCK_CONTENDER, str(path)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=True,
                )
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                released = subprocess.run(
                    [sys.executable, "-c", _LOCK_CONTENDER, str(path)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=True,
                )
                if (blocked.stdout.strip(), released.stdout.strip()) != (
                    "contended",
                    "acquired",
                ):
                    raise RuntimeError(
                        "Competing process did not observe lock exclusion"
                    )
        return CapabilityResult("advisory_lock", "supported", "Exclusion verified")
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        return CapabilityResult("advisory_lock", "degraded", str(error))


def _probe_process_group() -> tuple[CapabilityResult, CapabilityResult]:
    process_group = CapabilityResult(
        "process_group", "degraded", "Isolation not verified"
    )
    worker: subprocess.Popen[bytes] | None = None
    try:
        worker = subprocess.Popen(
            [sys.executable, "-c", _SIGNAL_WORKER],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        assert worker.stdout is not None
        if not select.select([worker.stdout], [], [], 5)[0]:
            raise RuntimeError("Worker did not become ready")
        if os.read(worker.stdout.fileno(), 64) != b"ready\n":
            raise RuntimeError("Worker closed output before becoming ready")
        if os.getpgid(worker.pid) != worker.pid or worker.pid == os.getpgrp():
            raise RuntimeError("Worker process group is not isolated")
        process_group = CapabilityResult(
            "process_group", "supported", "Isolation verified"
        )
        os.killpg(worker.pid, signal.SIGUSR1)
        if not select.select([worker.stdout], [], [], 1)[0]:
            raise RuntimeError("Worker did not acknowledge the group signal")
        if os.read(worker.stdout.fileno(), 64) != b"signalled\n":
            raise RuntimeError("Worker did not confirm signal delivery")
        group_signal = CapabilityResult(
            "group_signal", "supported", "Delivery verified"
        )
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        if process_group.status != "supported":
            process_group = CapabilityResult("process_group", "degraded", str(error))
        group_signal = CapabilityResult("group_signal", "degraded", str(error))
    finally:
        if worker is not None:
            if worker.poll() is None:
                worker.kill()
            worker.communicate(timeout=5)
    return process_group, group_signal


def _probe_directory_fsync() -> CapabilityResult:
    try:
        with TemporaryDirectory(prefix="ovcaq-fsync-probe-") as directory:
            descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        return CapabilityResult("directory_fsync", "supported", "Directory synced")
    except OSError as error:
        return CapabilityResult("directory_fsync", "degraded", str(error))


def _probe_process_identity() -> CapabilityResult:
    """Report whether the kernel identity probe resolves this process."""
    try:
        identity = process_identity(os.getpid())
    except (CommandError, OSError, ValueError, struct.error) as error:
        # A refused or unreadable probe is evidence, not a doctor crash.
        return CapabilityResult("process_identity", "degraded", str(error))
    if identity is None:
        return CapabilityResult(
            "process_identity", "degraded", "probe returned no identity"
        )
    return CapabilityResult("process_identity", "supported", identity.started)


def require_process_capabilities(results: tuple[CapabilityResult, ...]) -> None:
    """Reject missing, duplicated, unknown, or unsatisfied capability facts."""
    if len(results) != len(_NAMES) or {result.name for result in results} != set(
        _NAMES
    ):
        raise RuntimeError("Preflight requires exactly one fact for each capability")
    failures = [result for result in results if result.status != "supported"]
    if failures:
        raise RuntimeError(
            "; ".join(f"{fact.name}: {fact.detail}" for fact in failures)
        )


@dataclass(frozen=True)
class CapabilityRequest:
    name: str
    root: Path
    batch_id: str
    attempt_id: str
    session: SessionPaths
    timeout_seconds: int


@dataclass(frozen=True)
class CapabilityExecution:
    success: bool
    session_id: str
    detail: str | None


class CapabilityRunner(Protocol):
    def run(self, request: CapabilityRequest) -> CapabilityExecution: ...


def _timestamp(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def _session_paths(paths: RuntimePaths, session_id: str) -> SessionPaths:
    root = paths.sessions / session_id
    return SessionPaths(
        root=root,
        raw=root / "raw.jsonl",
        normalized=root / "normalized.jsonl",
        metrics=root / "metrics.jsonl",
        metadata=root / "meta.json",
        summary=root / "summary.json",
    )


class CapabilityService:
    """Run required batch capabilities as durable, evidence-backed attempts."""

    def __init__(
        self,
        root: Path,
        *,
        store: StateStore,
        paths: RuntimePaths,
        run_id: str,
        clock: Callable[[], datetime],
        timeout_seconds: object = _DEFAULT_TIMEOUT,
    ) -> None:
        self._root = root
        self._store = store
        self._state = StateService(store)
        self._paths = paths
        self._run_id = run_id
        self._clock = clock
        self._timeout_seconds = timeout_seconds
        if timeout_seconds is not _DEFAULT_TIMEOUT:
            validate_capability_timeout(timeout_seconds)

    def start(
        self, name: str, *, expected_revision: int | None = None
    ) -> CapabilityAttempt:
        """Commit a pending capability as running, then create its evidence."""
        attempt, _ = self._begin(name, self._state.start_capability, expected_revision)
        return attempt

    def finish(
        self,
        name: str,
        attempt_id: str,
        execution: CapabilityExecution,
        *,
        expected_revision: int | None = None,
    ) -> State:
        """Commit the current attempt's result, then finalize its evidence."""
        current = self._store.read()
        attempt = current["batch"]["capabilities"][name]["attempts"][-1:]
        if (
            attempt
            and attempt[0]["id"] == attempt_id
            and attempt[0]["session_id"] != execution.session_id
        ):
            raise ValueError("execution does not match the running session")
        # Pinning the observed revision keeps the session check atomic.
        state = self._state.finish_capability(
            name,
            attempt_id,
            succeeded=execution.success,
            detail=execution.detail,
            finished_at=_timestamp(self._clock()),
            expected_revision=(
                current["revision"] if expected_revision is None else expected_revision
            ),
        )
        session = _session_paths(self._paths, execution.session_id)
        descriptor = os.open(session.raw, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "ab") as stream:
            stream.write((json.dumps(asdict(execution)) + "\n").encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        self._finalize(state, name, session)
        return state

    def reconcile(self, name: str) -> State:
        """Fail a running attempt whose recorded owner process is gone."""
        state = self._store.read()
        capability = state["batch"]["capabilities"][name]
        if capability["status"] != "running":
            return state
        attempt = capability["attempts"][-1]
        assert attempt["session_id"] is not None
        session = _session_paths(self._paths, attempt["session_id"])
        try:
            metadata = parse_session_metadata(json.loads(session.metadata.read_text()))
            if process_matches(ProcessIdentity(metadata.pid, metadata.process_start)):
                return state
        except (OSError, ValueError):
            pass  # Unreadable ownership evidence cannot prove a live owner.
        state = self._state.reconcile_capability(
            name,
            attempt["id"],
            detail=f"owner process exited; retry {name} explicitly",
            finished_at=_timestamp(self._clock()),
            expected_revision=state["revision"],
        )
        self._finalize(state, name, session)
        return state

    def retry(self, name: str, runner: CapabilityRunner) -> State:
        """Run exactly one new attempt for a failed or stale capability."""
        if name not in self._store.read()["batch"]["capabilities"]:
            raise CommandError(ErrorCode.USAGE, f"unknown capability: {name}")
        if self.reconcile(name)["batch"]["capabilities"][name]["status"] == "running":
            raise ValueError(f"capability {name!r} is still running")
        return self._execute(name, runner, self._state.retry_capability)

    def run(self, name: str, runner: CapabilityRunner) -> State:
        """Run exactly one pending capability through the shared lifecycle."""
        return self._execute(name, runner, self._state.start_capability)

    def _execute(
        self, name: str, runner: CapabilityRunner, commit: Callable[..., State]
    ) -> State:
        timeout = (
            supervisor_settings(self._root).capability_timeouts.get(name, 10800)
            if self._timeout_seconds is _DEFAULT_TIMEOUT
            else validate_capability_timeout(self._timeout_seconds)
        )
        attempt, session = self._begin(name, commit, None)
        try:
            execution = runner.run(
                CapabilityRequest(
                    name=name,
                    root=self._root,
                    batch_id=self._store.read()["batch"]["id"],
                    attempt_id=attempt["id"],
                    session=session,
                    timeout_seconds=timeout,
                )
            )
        except Exception as error:
            assert attempt["session_id"] is not None
            self.finish(
                name,
                attempt["id"],
                CapabilityExecution(
                    success=False,
                    session_id=attempt["session_id"],
                    detail=f"runner raised {type(error).__name__}: {error}; "
                    f"retry {name} explicitly",
                ),
            )
            raise
        return self.finish(name, attempt["id"], execution)

    def _begin(
        self,
        name: str,
        commit: Callable[..., State],
        expected_revision: int | None,
    ) -> tuple[CapabilityAttempt, SessionPaths]:
        identity = process_identity(os.getpid())
        if identity is None:
            raise RuntimeError("cannot observe the current process identity")
        started_at = _timestamp(self._clock())
        attempt: CapabilityAttempt = {
            "id": str(uuid4()),
            "status": "running",
            "started_at": started_at,
            "finished_at": None,
            "session_id": str(uuid4()),
            "detail": None,
        }
        state = commit(name, attempt, expected_revision=expected_revision)
        assert attempt["session_id"] is not None
        session = self._create_session(
            name, attempt["session_id"], identity, started_at
        )
        publish_session_metric(
            self._paths,
            session,
            SessionMetric(
                schema_version=1,
                kind="capability",
                run_id=self._run_id,
                session_id=attempt["session_id"],
                batch_id=state["batch"]["id"],
                prd=None,
                phase_launched=None,
                capability=name,
                phase_end=None,
                decision=None,
                started_at=started_at,
                finished_at=None,
                wall_seconds=None,
                model=None,
                usage=None,
            ),
        )
        return attempt, session

    def _create_session(
        self,
        name: str,
        session_id: str,
        identity: ProcessIdentity,
        started_at: str,
    ) -> SessionPaths:
        session = create_session(
            self._paths,
            SessionMetadata(
                schema_version=1,
                run_id=self._run_id,
                session_id=session_id,
                agent=f"capability:{name}",
                pid=identity.pid,
                process_start=identity.started,
                started_at=started_at,
            ),
        )
        os.close(
            os.open(
                session.raw, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
            )
        )
        return session

    def _finalize(self, state: State, name: str, session: SessionPaths) -> None:
        attempt = state["batch"]["capabilities"][name]["attempts"][-1]
        assert attempt["finished_at"] is not None
        try:
            metadata = parse_session_metadata(json.loads(session.metadata.read_text()))
        except (OSError, ValueError):
            if session.root.exists():
                return  # ponytail: partial evidence stays as-is; state records it.
            # The owner died before creating evidence; record the failure here.
            identity = process_identity(os.getpid())
            if identity is None:
                raise RuntimeError("cannot observe the current process identity")
            self._create_session(
                name, session.root.name, identity, attempt["started_at"]
            )
            metadata = parse_session_metadata(json.loads(session.metadata.read_text()))
        publish_session_metric(
            self._paths,
            session,
            SessionMetric(
                schema_version=1,
                kind="capability",
                run_id=metadata.run_id,
                session_id=metadata.session_id,
                batch_id=state["batch"]["id"],
                prd=None,
                phase_launched=None,
                capability=name,
                phase_end=None,
                decision=attempt["status"],
                started_at=attempt["started_at"],
                finished_at=attempt["finished_at"],
                wall_seconds=(
                    datetime.fromisoformat(attempt["finished_at"])
                    - datetime.fromisoformat(attempt["started_at"])
                ).total_seconds(),
                model=None,
                usage=None,
            ),
        )
        reconcile_metrics(self._paths)
