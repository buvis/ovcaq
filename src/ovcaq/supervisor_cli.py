"""Lifecycle command dispatch: run, pause, resume, stop, capability retry."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import stat
import subprocess
import sys
import time
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from ovcaq.config import supervisor_settings
from ovcaq.drivers.edge import build_driver
from ovcaq.errors import CommandError, ErrorCode
from ovcaq.events import sanitize_text
from ovcaq.paths import RuntimePaths, ensure_runtime_layout
from ovcaq.runtime.capability import (
    CapabilityExecution,
    CapabilityRequest,
    CapabilityRunner,
    CapabilityService,
)
from ovcaq.runtime.registry import (
    DuplicateRunError,
    FleetRegistry,
    FleetRun,
    ProcessIdentity,
    process_identity,
    process_matches,
    run_lock_held,
)
from ovcaq.runtime.session import (
    observe_run,
    observe_selected_run,
    parse_session_metadata,
)
from ovcaq.runtime.supervisor import Supervisor
from ovcaq.runtime.watchdog import _SystemClock
from ovcaq.state.commands import StateService
from ovcaq.state.schema import JSONValue, Notice, SchemaError
from ovcaq.state.store import StateError, StateStore

SupervisorResult = tuple[JSONValue, int | None, bool, int]
LAUNCH_REPORT_ENV = "OVCAQ_LAUNCH_REPORT"
LAUNCH_REPORT_FD_ENV = "OVCAQ_LAUNCH_REPORT_FD"
MAX_REPORT_BYTES = 4096
LAUNCH_POLL_SECONDS = 0.05


def _now() -> datetime:
    return datetime.now(UTC)


class _Clock(_SystemClock):
    def now(self) -> datetime:
        return _now()


class _UnavailableRunner:
    def run(self, request: CapabilityRequest) -> CapabilityExecution:
        raise CommandError(
            ErrorCode.RUNTIME_FORMAT,
            f"no capability runner is available for {request.name!r}",
        )


def _bounded(text: str) -> str:
    text = re.sub(r"(?:\x1b|\\x1b)\[[0-?]*[ -/]*[@-~]", "", text)
    text = sanitize_text(text)
    text = "".join(ch for ch in text if ch.isprintable() or ch == "\n")
    # Reserve one byte for the newline added by plain CLI error emission.
    return text.encode("utf-8")[: MAX_REPORT_BYTES - 1].decode("utf-8", "ignore")


def _open_report(report: Path, flags: int) -> int:
    """Open report without following links; reject anything but a regular file."""
    fd = os.open(report, flags | os.O_NOFOLLOW | os.O_NONBLOCK)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise OSError(f"launch report {report} is not a regular file")
    return fd


def _claim_launch_report(runtime_root: Path, value: str | None) -> Path | None:
    """Validate a report destination against the resolved runtime root."""
    if value is None:
        return None
    report = Path(value)
    try:
        valid = (
            report.is_absolute()
            and ".." not in report.parts
            and report.parent == runtime_root
            and stat.S_ISREG(report.lstat().st_mode)
        )
    except OSError:
        valid = False
    if not valid:
        raise CommandError(
            ErrorCode.RUNTIME_FORMAT,
            "launch report must be a regular file inside the runtime root",
            path=value,
        )
    return report


def _write_launch_report(report: Path | int | None, detail: str) -> None:
    if report is None:
        return
    # A report already removed by a successful launcher stays absent.
    with (
        suppress(OSError),
        os.fdopen(
            os.dup(report)
            if isinstance(report, int)
            else _open_report(report, os.O_WRONLY),
            "wb",
        ) as out,
    ):
        os.fchmod(out.fileno(), 0o600)
        out.seek(0)
        out.truncate()
        out.write(_bounded(detail).encode("utf-8"))


def _verify_inherited_report(descriptor: int, report_path: str | None) -> None:
    info = os.fstat(descriptor)
    if report_path is None or not stat.S_ISREG(info.st_mode):
        raise ValueError("invalid inherited launch report")
    target = Path(report_path).lstat()
    if (target.st_dev, target.st_ino) != (info.st_dev, info.st_ino):
        raise ValueError("inherited launch report changed")


def _report_runtime_error(report: Path | int | None, error: Exception) -> Exception:
    if isinstance(error, DuplicateRunError):
        error = CommandError(ErrorCode.RUNTIME_FORMAT, f"{error}; use `ovcaq attach`")
    _write_launch_report(report, f"supervisor runtime: {error}")
    if isinstance(error, CommandError):
        raise CommandError(error.code, _bounded(str(error)), path=error.path) from error
    if isinstance(error, (StateError, SchemaError, OSError, ValueError)):
        return error
    raise CommandError(
        ErrorCode.RUNTIME_FORMAT, _bounded(f"supervisor failed: {error}")
    ) from error


def _run(args: argparse.Namespace, root: Path) -> SupervisorResult:
    report_path = os.environ.pop(LAUNCH_REPORT_ENV, None)
    inherited = os.environ.pop(LAUNCH_REPORT_FD_ENV, None)
    report: Path | int | None = None
    descriptor: int | None = None
    try:
        if inherited is not None:
            descriptor = int(inherited)
            _verify_inherited_report(descriptor, report_path)
            report = descriptor
        settings = supervisor_settings(root)
        claimed = _claim_launch_report(settings.runtime.paths.runtime_root, report_path)
        report = descriptor if descriptor is not None else claimed
        ensure_runtime_layout(settings.runtime.paths)
        driver = build_driver(root, args.agent)
        health = driver.probe()
        if not health.healthy:
            raise CommandError(
                ErrorCode.RUNTIME_FORMAT,
                _bounded(f"agent is unhealthy: {health.detail}"),
            )
        supervisor = Supervisor(
            root,
            store=StateStore(settings.runtime.paths.state_file),
            driver=driver,
            settings=settings,
            capability_runner=lambda _capability: _UnavailableRunner(),
            clock=_Clock(),
            sleeper=time.sleep,
        )
        outcome = supervisor.run()
        if outcome.exit_code != 0:
            _write_launch_report(report, outcome.decision.reason or "supervisor failed")
        elif supervisor._metadata is not None:
            _write_launch_report(report, json.dumps(asdict(supervisor._metadata)))
    except Exception as error:
        _report_runtime_error(report, error)
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
    value: JSONValue = {
        "decision": outcome.decision.kind.value,
        "reason": outcome.decision.reason,
        "sessions_attempted": outcome.sessions_attempted,
    }
    return value, None, False, outcome.exit_code


def operator_notice(reason: str | None) -> Notice | None:
    if reason is None:
        return None
    return {
        "site": "operator",
        "detail": reason,
        "created_at": _now().isoformat().replace("+00:00", "Z"),
    }


def verify_run(run: FleetRun, registry: FleetRegistry | None = None) -> RuntimePaths:
    """Raise unless run metadata, live registry, process, and run lock all name run."""
    paths = supervisor_settings(run.root).runtime.paths
    identity = ProcessIdentity(run.pid, run.process_start)
    metadata = parse_session_metadata(json.loads(paths.run_metadata.read_text()))
    live = (registry or FleetRegistry(paths.fleet_root)).snapshot().live
    trusted = (
        metadata.run_id == run.run_id
        and ProcessIdentity(metadata.pid, metadata.process_start) == identity
        and any(
            entry.run_id == run.run_id
            and entry.root == run.root
            and ProcessIdentity(entry.pid, entry.process_start) == identity
            for entry in live
        )
        and process_matches(identity)
        and run_lock_held(paths.run_lock)
    )
    if not trusted:
        raise RuntimeError(
            f"run {run.run_id!r} is not the live supervisor owning {run.root}"
        )
    return paths


@dataclass(frozen=True, slots=True)
class LaunchedSupervisor:
    run: FleetRun | None


@dataclass(frozen=True, slots=True)
class LaunchFailureEvidence:
    exit_code: int | None
    detail: str
    path: Path


class LaunchError(RuntimeError):
    evidence: LaunchFailureEvidence

    def __init__(self, evidence: LaunchFailureEvidence) -> None:
        self.evidence = evidence
        super().__init__(evidence.detail)


def _read_launch_report(report: Path) -> str:
    try:
        with os.fdopen(_open_report(report, os.O_RDONLY), "rb") as source:
            raw = source.read(MAX_REPORT_BYTES)
    except OSError:
        return ""
    text = raw.decode("utf-8", "replace")
    return _bounded(text).strip()


def completed_run(paths: RuntimePaths, run: FleetRun) -> bool:
    """Accept completion only when final state is attested by this exact owner."""
    with observe_selected_run(paths, run, batch_id=None) as selected:
        pass
    return (
        selected.ended
        and selected.state is not None
        and selected.state["batch"]["status"] == "completed"
    )


def _completed_launch(paths: RuntimePaths, report: Path, pid: int) -> bool:
    try:
        metadata = parse_session_metadata(json.loads(_read_launch_report(report)))
        run = FleetRun(
            metadata.run_id,
            paths.project_root,
            metadata.agent,
            metadata.started_at,
            metadata.pid,
            metadata.process_start,
        )
        return run.pid == pid and completed_run(paths, run)
    except (OSError, ValueError, StateError):
        return False


def _launch_failure(
    report: Path, pid: int, exit_code: int | None, problem: str
) -> LaunchError:
    if exit_code is None:
        detail = (
            f"supervisor pid {pid} {problem}; inspect it with `ovcaq attach` "
            f"or end it with `ovcaq stop`"
        )
    else:
        written = _read_launch_report(report)
        detail = f"supervisor pid {pid} exited with code {exit_code}: " + (
            written or "unhandled crash before publishing a failure report"
        )
    return LaunchError(LaunchFailureEvidence(exit_code, _bounded(detail), report))


def _published_run(
    registry: FleetRegistry,
    paths: RuntimePaths,
    root: Path,
    pid: int,
    report: Path,
) -> LaunchedSupervisor | None:
    owners = [
        entry
        for entry in registry.snapshot().live
        if entry.pid == pid or entry.root == root
    ]
    if not owners:
        return None
    entry = owners[0]
    identity = process_identity(pid)
    if (
        len(owners) != 1
        or entry.pid != pid
        or entry.root != root
        or identity is None
        or identity.started != entry.process_start
    ):
        raise LaunchError(
            LaunchFailureEvidence(
                None,
                _bounded(
                    f"supervisor pid {pid} has ambiguous or unrelated ownership; "
                    "inspect the existing owner with `ovcaq attach`"
                ),
                report,
            )
        )
    status = observe_run(paths).status
    if status == "inconsistent":
        raise _launch_failure(report, pid, None, "has an inconsistent run observation")
    if status != "active":
        return None
    report.unlink()
    return LaunchedSupervisor(FleetRun.from_entry(entry))


def _spawn_supervisor(
    argv: tuple[str, ...], descriptor: int, report: Path
) -> subprocess.Popen[bytes]:
    try:
        return subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
            pass_fds=(descriptor,),
            shell=False,
            env={
                **os.environ,
                LAUNCH_REPORT_ENV: str(report),
                LAUNCH_REPORT_FD_ENV: str(descriptor),
            },
        )
    finally:
        os.close(descriptor)


def launch_supervisor(
    root: Path,
    *,
    agent: str | None,
    argv_prefix: tuple[str, ...] = (sys.executable, "-m", "ovcaq"),
    timeout_seconds: float = 10.0,
) -> LaunchedSupervisor:
    """Spawn a detached foreground supervisor and wait for its exact publication."""
    paths = ensure_runtime_layout(supervisor_settings(root).runtime.paths)
    report = paths.runtime_root / f"launch-{uuid4().hex}.report"
    descriptor = os.open(
        report, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    argv = (*argv_prefix, "--root", str(root), "run", "--no-tui")
    if agent is not None:
        argv += ("--agent", agent)
    child = _spawn_supervisor(argv, descriptor, report)
    registry = FleetRegistry(paths.fleet_root)
    deadline = time.monotonic() + timeout_seconds
    while True:
        exit_code = child.poll()
        if exit_code is not None:
            if exit_code == 0 and _completed_launch(paths, report, child.pid):
                report.unlink()
                return LaunchedSupervisor(None)
            raise _launch_failure(report, child.pid, exit_code, "exited")
        launched = _published_run(registry, paths, root, child.pid, report)
        if launched is not None:
            return launched
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise _launch_failure(
                report,
                child.pid,
                None,
                f"did not publish an active run within {timeout_seconds}s",
            )
        time.sleep(min(LAUNCH_POLL_SECONDS, remaining))


def stop_supervisor(
    run: FleetRun, *, registry: FleetRegistry | None = None
) -> ProcessIdentity:
    verify_run(run, registry)
    identity = ProcessIdentity(run.pid, run.process_start)
    os.kill(identity.pid, signal.SIGTERM)
    return identity


def _stop(root: Path) -> SupervisorResult:
    paths = supervisor_settings(root).runtime.paths
    try:
        metadata = parse_session_metadata(json.loads(paths.run_metadata.read_text()))
        identity = stop_supervisor(
            FleetRun(
                metadata.run_id,
                paths.project_root,
                metadata.agent,
                metadata.started_at,
                metadata.pid,
                metadata.process_start,
            )
        )
    except (OSError, ValueError, RuntimeError) as error:
        raise CommandError(
            ErrorCode.RUNTIME_FORMAT,
            f"cannot stop the running supervisor: {error}",
            path=str(paths.run_metadata),
        ) from error
    return {"pid": identity.pid, "signal": int(signal.SIGTERM)}, None, False, 0


def _retry(
    args: argparse.Namespace, root: Path, runner: CapabilityRunner | None
) -> SupervisorResult:
    paths = supervisor_settings(root).runtime.paths
    service = CapabilityService(
        root,
        store=StateStore(paths.state_file),
        paths=paths,
        run_id=uuid4().hex,
        clock=_now,
    )
    try:
        state = service.retry(args.name, runner or _UnavailableRunner())
    except ValueError as error:
        raise CommandError(ErrorCode.RUNTIME_FORMAT, str(error)) from error
    status = state["batch"]["capabilities"][args.name]["status"]
    return (
        cast(JSONValue, state),
        state["revision"],
        True,
        0 if status == "succeeded" else 1,
    )


def dispatch_supervisor(
    args: argparse.Namespace,
    root: Path,
    *,
    capability_runner: CapabilityRunner | None = None,
) -> SupervisorResult:
    """Dispatch a lifecycle command; never writes output streams."""
    if args.command == "run":
        return _run(args, root)
    if args.command == "stop":
        return _stop(root)
    if args.command == "capability":
        return _retry(args, root, capability_runner)
    paths = supervisor_settings(root).runtime.paths
    service = StateService(StateStore(paths.state_file))
    if args.command == "pause":
        state = service.request_pause(operator_notice(args.reason))
    else:
        state = service.resume()
    return cast(JSONValue, state), state["revision"], True, 0
