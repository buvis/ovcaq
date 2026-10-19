"""Runtime command observations and retained evidence operations."""

from __future__ import annotations

import argparse
import os
import stat
import sys
import time
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from ovcaq.cli_io import _json_file, _runtime_metadata, _runtime_timestamp
from ovcaq.config import RuntimeSettings, runtime_settings
from ovcaq.errors import CommandError, ErrorCode
from ovcaq.paths import RuntimePaths
from ovcaq.runtime.capability import CapabilityResult
from ovcaq.runtime.registry import FleetRegistry
from ovcaq.runtime.session import (
    ActiveSessionError,
    EmergencyStateFailure,
    EvidenceInventory,
    PurgePlan,
    RunObservation,
    acknowledge_emergency_failure,
    apply_purge,
    inventory_evidence,
    observe_run,
    plan_purge,
)
from ovcaq.state.schema import JSONValue, SchemaError
from ovcaq.state.store import StateError, StateStore


def _purge_payload(plan: PurgePlan, *, applied: bool) -> dict[str, JSONValue]:
    return {
        "schema_version": plan.schema_version,
        "applied": applied,
        "selected": [str(item.path) for item in plan.selected],
        "total_bytes": plan.total_bytes,
        "command": list(plan.command),
    }


def _log_payload(paths: RuntimePaths, args: argparse.Namespace) -> JSONValue:
    inventory = inventory_evidence(paths)
    candidates = []
    for item in inventory.sessions:
        if args.log_session is not None and item.session_id != args.log_session:
            continue
        metadata = _runtime_metadata(item.path / "meta.json")
        if metadata.session_id != item.session_id:
            raise ValueError("session metadata does not match its directory")
        candidates.append((metadata, item))
    if not candidates:
        raise ValueError("no matching retained session")
    metadata, item = max(
        candidates,
        key=lambda pair: (
            _runtime_timestamp(pair[0].started_at),
            pair[0].session_id,
        ),
    )
    kind = args.kind or "raw"
    evidence_path = item.path / f"{kind}.jsonl"
    info = _read_log(evidence_path, follow=args.follow)
    return {
        "schema_version": 1,
        "session_id": metadata.session_id,
        "kind": kind,
        "path": str(evidence_path),
        "size_bytes": info.st_size,
        "active": item.active,
    }


def _read_log(evidence_path: Path, *, follow: bool) -> os.stat_result:
    descriptor = os.open(
        evidence_path,
        os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0),
    )
    with os.fdopen(descriptor, "rb") as evidence:
        info = os.fstat(evidence.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"not a regular evidence file: {evidence_path}")
        if follow:
            while True:
                chunk = evidence.read(64 * 1024)
                if chunk:
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                else:
                    time.sleep(0.1)
    return info


def _dispatch_logs(
    args: argparse.Namespace,
    paths: RuntimePaths,
) -> JSONValue:
    if args.logs_command == "purge" and (
        args.log_session is not None or args.kind is not None or args.follow
    ):
        raise CommandError(
            ErrorCode.USAGE, "log selection and follow options cannot precede purge"
        )
    if args.follow and args.json:
        raise CommandError(ErrorCode.USAGE, "--follow cannot be used with --json")
    try:
        if args.logs_command == "purge":
            plan = plan_purge(paths, session_id=args.session, before=args.before)
            if args.apply:
                apply_purge(plan)
            return _purge_payload(plan, applied=args.apply)
        return _log_payload(paths, args)
    except (ValueError, OSError, ActiveSessionError) as error:
        raise CommandError(ErrorCode.RUNTIME_FORMAT, str(error)) from error


def _state_attention(
    paths: RuntimePaths,
    *,
    acknowledge: bool,
) -> tuple[str, JSONValue, str | None]:
    runtime_store = StateStore(paths.state_file)
    try:
        runtime_store.read()
        state_health = "available"
    except (StateError, SchemaError, OSError, ValueError):
        if acknowledge:
            raise
        state_health = "invalid" if paths.state_file.exists() else "missing"
    acknowledged_archive = None
    if acknowledge:
        try:
            acknowledged_archive = str(
                acknowledge_emergency_failure(paths, state_valid=True)
            )
        except (EmergencyStateFailure, OSError, ValueError, TypeError) as error:
            raise CommandError(ErrorCode.RUNTIME_FORMAT, str(error)) from error
    marker = paths.runtime_root / "state-write-failed.json"
    attention: JSONValue = None
    if marker.exists() or marker.is_symlink():
        try:
            attention = {"path": str(marker), "record": _json_file(marker)}
        except CommandError as error:
            attention = {"path": str(marker), "error": str(error)}
    return state_health, attention, acknowledged_archive


def _run_health(paths: RuntimePaths, run: RunObservation) -> RunObservation:
    if run.status != "idle":
        return run
    try:
        fleet = FleetRegistry(paths.fleet_root).snapshot()
        if any(entry.root == paths.project_root for entry in fleet.live):
            return RunObservation(
                "inconsistent", "fleet registry entry has no authoritative run"
            )
    except (OSError, ValueError) as error:
        return RunObservation("inconsistent", str(error))
    return run


def _evidence_summary(
    settings: RuntimeSettings, run: RunObservation
) -> tuple[dict[str, JSONValue], str, EvidenceInventory | None]:
    paths = settings.paths
    evidence_health = "available"
    evidence_summary: dict[str, JSONValue] = {
        "runtime_root": str(paths.runtime_root),
        "sessions": [],
        "total_bytes": 0,
        "max_retained_bytes": settings.max_retained_bytes,
        "min_free_bytes": settings.min_free_bytes,
    }
    inventory = None
    try:
        inventory = inventory_evidence(paths, run=run)
        evidence_summary["total_bytes"] = inventory.total_bytes
        evidence_summary["sessions"] = [
            cast(JSONValue, {**asdict(item), "path": str(item.path)})
            for item in inventory.sessions
        ]
    except (ValueError, OSError) as error:
        evidence_health = str(error)
    return evidence_summary, evidence_health, inventory


def _directory_health(
    paths: RuntimePaths,
    inventory: EvidenceInventory | None,
) -> dict[str, str]:
    health = {
        "permissions": "available",
        "writability": "available",
    }
    directories = [paths.runtime_root, paths.sessions]
    if inventory is not None:
        directories.extend(item.path for item in inventory.sessions)
    for directory in directories:
        try:
            information = directory.lstat()
            mode = stat.S_IMODE(information.st_mode)
            if not stat.S_ISDIR(information.st_mode) or mode != 0o700:
                health["permissions"] = (
                    f"runtime directory requires mode 0700: {directory}"
                )
            if (
                information.st_uid != os.geteuid()
                or mode & 0o300 != 0o300
                or not os.access(directory, os.W_OK | os.X_OK, effective_ids=True)
            ):
                health["writability"] = (
                    f"runtime directory is not owner-writable: {directory}"
                )
        except OSError as error:
            health["permissions"] = str(error)
            health["writability"] = str(error)
    return health


def _storage_health(
    settings: RuntimeSettings, inventory: EvidenceInventory | None
) -> dict[str, str]:
    health = {"retained_budget": "available", "free_space": "available"}
    if inventory is None:
        health["retained_budget"] = "retained evidence size is unavailable"
    elif inventory.total_bytes > settings.max_retained_bytes:
        health["retained_budget"] = "retained evidence exceeds max_retained_bytes"
    try:
        volume = os.statvfs(settings.paths.runtime_root)
        if volume.f_bavail * volume.f_frsize < settings.min_free_bytes:
            health["free_space"] = "available space is below min_free_bytes"
    except OSError as error:
        health["free_space"] = str(error)
    return health


def _doctor_payload(
    settings: RuntimeSettings,
    purge_preview: JSONValue,
    state_health: str,
    run: RunObservation,
    evidence_health: str,
    inventory: EvidenceInventory | None,
    attention: JSONValue,
    acknowledged_archive: str | None,
    probe: Callable[[], tuple[CapabilityResult, ...]],
) -> JSONValue:
    paths = settings.paths
    capabilities = sorted(probe(), key=lambda result: result.name)
    health = {
        "evidence": evidence_health,
        "run": run.detail,
        "state": state_health,
        **_directory_health(paths, inventory),
        **_storage_health(settings, inventory),
    }
    return {
        "schema_version": 1,
        "ok": (
            all(status == "available" for status in health.values())
            and attention is None
            and all(result.status == "supported" for result in capabilities)
        ),
        "paths": {
            name: str(path)
            for name, path in asdict(paths).items()
            if not name.startswith("_")
        },
        "capabilities": [cast(JSONValue, asdict(result)) for result in capabilities],
        "checks": [
            {"name": name, "status": status} for name, status in sorted(health.items())
        ],
        "purge_preview": purge_preview,
        "attention": attention,
        "acknowledged_emergency_archive": acknowledged_archive,
    }


def _dispatch_runtime(
    args: argparse.Namespace,
    root: Path,
    *,
    probe: Callable[[], tuple[CapabilityResult, ...]],
) -> JSONValue:
    settings = runtime_settings(root)
    paths = settings.paths
    if args.command == "logs":
        return _dispatch_logs(args, paths)
    state_health, attention, acknowledged_archive = _state_attention(
        paths,
        acknowledge=args.command == "doctor" and args.acknowledge_emergency,
    )
    run = _run_health(paths, observe_run(paths))
    evidence_summary, evidence_health, inventory = _evidence_summary(settings, run)
    purge_preview = None
    if inventory is not None:
        plan = plan_purge(paths, before=datetime.now(UTC), inventory=inventory)
        purge_preview = _purge_payload(plan, applied=False)
        purge_preview["command"] = list(plan.command[:-1])
    if args.command == "status":
        if evidence_health != "available":
            raise CommandError(ErrorCode.RUNTIME_FORMAT, evidence_health)
        return {
            "schema_version": 1,
            "state": state_health,
            "run": run.status,
            "evidence": evidence_summary,
            "purge_preview": purge_preview,
            "attention": attention,
        }
    return _doctor_payload(
        settings,
        purge_preview,
        state_health,
        run,
        evidence_health,
        inventory,
        attention,
        acknowledged_archive,
        probe,
    )
