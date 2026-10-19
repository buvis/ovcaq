"""Per-PRD reset, completion, deferred records, and recovery sagas."""

from __future__ import annotations

import copy
import stat
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import cast

from ovcaq.state.schema import (
    ArtifactIdentity,
    CompletedPrd,
    DecisionEntry,
    JSONValue,
    RecoveryKind,
    RecoveryOperation,
    RecoveryStep,
    State,
    validate_state,
)
from ovcaq.state.store import StateStore
from ovcaq.workflow import _files
from ovcaq.workflow._files import (
    DeferBoundary,
    DeferredRecordConflictError,
    _artifact_identity,
    _artifact_stat,
    _require_artifact_identity,
    _validate_prd_artifact,
    load_deferred_records,
    record_defer,
)
from ovcaq.workflow._rename import rename_exclusive
from ovcaq.workflow.paths import LifecyclePaths

__all__ = [
    "CompletionError",
    "DeferBoundary",
    "DeferredRecordConflictError",
    "RecoveryConflictError",
    "SagaBoundary",
    "SagaResult",
    "complete_prd",
    "complete_prd_in_store",
    "completed_prd_summary",
    "defer_record",
    "load_deferred_records",
    "park",
    "record_defer",
    "require_recovery_idle",
    "reset_prd_fields",
    "stall",
]


class CompletionError(ValueError):
    """Raised when completion would misattribute or conflict with a PRD."""


class RecoveryConflictError(ValueError):
    """Raised when a requested operation conflicts with durable recovery."""


def require_recovery_idle(state: State) -> None:
    """Reject a competing workflow mutation while recovery owns the PRD."""
    operation = state["recovery"]["operation"]
    if operation is not None:
        raise RecoveryConflictError(
            f"recovery operation {operation['id']!r} is active; reconcile it first"
        )


class SagaBoundary(StrEnum):
    """Characterized interruption points in the workflow filesystem saga."""

    AFTER_MKDIR_BEFORE_INTENT = "after-mkdir-before-intent"
    AFTER_INTENT_BEFORE_MOVE = "after-intent-before-move"
    AFTER_RENAME_BEFORE_DIRECTORY_FSYNC = "after-rename-before-directory-fsync"
    AFTER_MOVE_BEFORE_APPEND = "after-move-before-append"
    AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC = "after-replace-before-directory-fsync"
    AFTER_APPEND_BEFORE_COMMIT = "after-append-before-commit"
    AFTER_COMMIT_BEFORE_MARKER_DELETE = "after-commit-before-marker-delete"


type BoundaryHook = Callable[[SagaBoundary], None]
type OperationIdFactory = Callable[[], str]
type TimestampFactory = Callable[[], str]


@dataclass(frozen=True)
class SagaResult:
    """The committed result of a stall or park operation."""

    operation_id: str | None
    kind: RecoveryKind
    replayed: bool
    systemic_halt: bool


def reset_prd_fields(state: State) -> State:
    """Reset v1 per-PRD owners while preserving batch and repository identity."""
    result = copy.deepcopy(state)

    work = result["work"]
    work["phase"] = "build"
    work["next_phase"] = "build"
    work["completed_phases"] = []
    work["work_start_sha"] = None
    work["design_doc"] = None
    work["contract_card"] = None
    work["tasks_total"] = 0
    work["tasks_completed"] = 0
    work["extensions"] = {}
    result["tasks"] = []

    review = result["review"]
    review["cycle"] = 0
    review["cycles"] = []
    review["decisions"] = []
    review["doubts"] = []
    review["rubric_verdicts"] = []
    review["rework_task_ids"] = []
    review["lenses"] = {}
    review["extensions"] = {}

    result["control"]["pause_reason"] = None
    result["control"]["attention"] = None
    result["recovery"] = {
        "operation": None,
        "replan_count": 0,
        "phase_fingerprint": None,
        "phase_repeats": 0,
    }
    return result


def decision_has_content(decision: DecisionEntry) -> bool:
    """Ignore status/timestamp metadata when recognizing a substantive decision."""
    return any(
        value is not None and (not isinstance(value, str) or bool(value.strip()))
        for value in (
            decision["id"],
            decision["kind"],
            decision["summary"],
            decision["rationale"],
            decision["cycle"],
        )
    )


def completed_prd_summary(state: State) -> CompletedPrd:
    """Derive the stable batch summary for the active PRD."""
    filename = state["work"]["prd"]
    if filename is None:
        raise CompletionError("cannot complete a state without an active PRD")
    decisions = [
        item for item in state["review"]["decisions"] if decision_has_content(item)
    ]
    return {
        "filename": filename,
        "cycles": max(1, state["review"]["cycle"]),
        "autonomous_decisions": sum(
            decision["status"] == "applied" for decision in decisions
        ),
        "escalated_decisions": sum(
            decision["status"] == "escalated" for decision in decisions
        ),
        "tasks_completed": state["work"]["tasks_completed"],
        "tasks_total": state["work"]["tasks_total"],
    }


def complete_prd(state: State, prd_filename: str) -> State:
    """Idempotently append the active PRD summary and reset the park breaker."""
    require_recovery_idle(state)
    if (
        state["work"]["phase"] != "done"
        or "review" not in state["work"]["completed_phases"]
    ):
        raise CompletionError(
            "cannot complete a PRD outside the terminal converged state"
        )
    summary = completed_prd_summary(state)
    if summary["filename"] != prd_filename:
        raise CompletionError(
            f"complete PRD {prd_filename!r} does not match active PRD "
            f"{summary['filename']!r}"
        )

    result = copy.deepcopy(state)
    existing = [
        record
        for record in result["batch"]["completed_prds"]
        if record["filename"] == prd_filename
    ]
    if existing:
        if any(record != summary for record in existing):
            raise CompletionError(
                f"conflicting completed PRD summary already exists for {prd_filename!r}"
            )
    else:
        result["batch"]["completed_prds"].append(summary)
    result["batch"]["parks_consecutive"] = 0
    return result


def complete_prd_in_store(
    store: StateStore,
    prd_filename: str,
    *,
    expected_revision: int | None = None,
) -> State:
    """Commit one idempotent completed-PRD summary with revision CAS."""
    return store.transaction(
        lambda state: complete_prd(state, prd_filename),
        expected_revision=expected_revision,
    )


def defer_record(
    store: StateStore,
    runtime_root: Path,
    prd: str,
    record: dict[str, object],
) -> Path:
    """Write a deferred record bound to the committed active batch and PRD."""
    state = store.read()
    require_recovery_idle(state)
    if state["work"]["prd"] != prd:
        raise ValueError(
            f"deferred PRD {prd!r} does not match active PRD {state['work']['prd']!r}"
        )
    batch_id = state["batch"]["id"]
    if not batch_id:
        raise ValueError("cannot defer without an active batch")
    return record_defer(runtime_root, prd, batch_id, record)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _new_operation_id() -> str:
    return uuid.uuid4().hex


def _trip(hook: BoundaryHook | None, boundary: SagaBoundary) -> None:
    if hook is not None:
        hook(boundary)


def _operation_paths(
    paths: LifecyclePaths,
    operation: RecoveryOperation,
) -> tuple[Path, Path]:
    expected_source = paths.wip / operation["prd"]
    expected_destination = paths.hold / operation["prd"]
    source = Path(operation["source"])
    destination = Path(operation["destination"])
    if source != expected_source or destination != expected_destination:
        raise RecoveryConflictError(
            f"recovery operation {operation['id']} has unexpected lifecycle paths"
        )
    return source, destination


def _verify_move(
    source: Path,
    destination: Path,
    *,
    source_directory: int,
    destination_directory: int,
    boundary_hook: BoundaryHook | None,
    identity: ArtifactIdentity | None,
) -> None:
    _files._verify_lifecycle_directory_identity(source.parent, source_directory)
    _files._verify_lifecycle_directory_identity(
        destination.parent, destination_directory
    )
    source_stat = _artifact_stat(source_directory, source.name)
    destination_stat = _artifact_stat(destination_directory, destination.name)
    if source_stat is not None and destination_stat is not None:
        raise OSError(f"PRD exists in both wip and hold: {source.name}")
    if source_stat is not None:
        if not stat.S_ISREG(source_stat.st_mode):
            raise OSError(f"PRD source is not a regular file: {source}")
        _require_artifact_identity(source_directory, source, identity)
        rename_exclusive(
            source.name,
            destination.name,
            src_dir_fd=source_directory,
            dst_dir_fd=destination_directory,
        )
        _trip(boundary_hook, SagaBoundary.AFTER_RENAME_BEFORE_DIRECTORY_FSYNC)
        _files._verify_lifecycle_directory_identity(source.parent, source_directory)
        _files._verify_lifecycle_directory_identity(
            destination.parent,
            destination_directory,
        )
    source_stat = _artifact_stat(source_directory, source.name)
    destination_stat = _artifact_stat(destination_directory, destination.name)
    if source_stat is not None or destination_stat is None:
        raise OSError(f"PRD is not present in wip or hold: {source.name}")
    if not stat.S_ISREG(destination_stat.st_mode):
        raise OSError(f"PRD destination is not a regular file: {destination}")
    _require_artifact_identity(destination_directory, destination, identity)
    _files._verify_lifecycle_directory_identity(source.parent, source_directory)
    _files._verify_lifecycle_directory_identity(
        destination.parent, destination_directory
    )
    _files._fsync_directory_descriptor(source_directory)
    _files._fsync_directory_descriptor(destination_directory)
    _files._verify_lifecycle_directory_identity(source.parent, source_directory)
    _files._verify_lifecycle_directory_identity(
        destination.parent, destination_directory
    )


def _verify_moved_artifact(
    source: Path,
    destination: Path,
    *,
    source_directory: int,
    destination_directory: int,
) -> None:
    """Require the configured lifecycle names and completed move to remain valid."""
    _files._verify_lifecycle_directory_identity(source.parent, source_directory)
    _files._verify_lifecycle_directory_identity(
        destination.parent, destination_directory
    )
    source_stat = _artifact_stat(source_directory, source.name)
    destination_stat = _artifact_stat(destination_directory, destination.name)
    if source_stat is not None or destination_stat is None:
        raise OSError(f"PRD is not present only in configured hold: {source.name}")
    if not stat.S_ISREG(destination_stat.st_mode):
        raise OSError(f"PRD destination is not a regular file: {destination}")
    _files._verify_lifecycle_directory_identity(source.parent, source_directory)
    _files._verify_lifecycle_directory_identity(
        destination.parent, destination_directory
    )


def _state_proves_reset(state: State) -> bool:
    work = state["work"]
    review = state["review"]
    return (
        not state["tasks"]
        and work["tasks_total"] == 0
        and work["tasks_completed"] == 0
        and work["phase"] in {"build", "paused"}
        and work["next_phase"] == work["phase"]
        and review["cycle"] == 0
        and not review["doubts"]
        and not review["rubric_verdicts"]
        and not review["rework_task_ids"]
        and not review["lenses"]
    )


def _completed_operation_id(
    state: State,
    runtime_root: Path,
    *,
    kind: RecoveryKind,
    prd: str,
    site: str,
    detail: str,
) -> str | None:
    if not _state_proves_reset(state) or not state["batch"]["id"]:
        return None
    records = load_deferred_records(runtime_root, state["batch"]["id"])
    for item in reversed(records):
        if (
            item.get("type") == "stall"
            and item.get("prd") == prd
            and item.get("site") == site
            and item.get("detail") == detail
            and item.get("kind") == kind
            and isinstance(item.get("op_id"), str)
        ):
            return cast(str, item["op_id"])
    return None


def _advance_operation(
    store: StateStore,
    operation_id: str,
    expected_step: RecoveryStep,
    next_step: RecoveryStep,
    *,
    verify: Callable[[], None] | None = None,
) -> State:
    def advance(state: State) -> None:
        if verify is not None:
            verify()
        current = state["recovery"]["operation"]
        if (
            current is None
            or current["id"] != operation_id
            or current["step"] != expected_step
        ):
            raise RecoveryConflictError(
                f"recovery operation {operation_id} changed before {next_step}"
            )
        current["step"] = next_step

    return store.transaction(advance, publication_guard=verify)


def _stamp_intent(
    store: StateStore, operation: RecoveryOperation, expected_revision: int
) -> None:
    def stamp(state: State) -> None:
        if state["recovery"]["operation"] is not None:
            raise RecoveryConflictError("another recovery operation is already active")
        state["recovery"]["operation"] = operation

    store.transaction(stamp, expected_revision=expected_revision)


def _commit_operation(
    store: StateStore, operation: RecoveryOperation, *, verify: Callable[[], None]
) -> State:
    def commit(state: State) -> State:
        verify()
        current = state["recovery"]["operation"]
        if (
            current is None
            or current["id"] != operation["id"]
            or current["step"] != "recorded"
        ):
            raise RecoveryConflictError(
                f"recovery operation {operation['id']} changed before commit"
            )
        result = reset_prd_fields(state)
        if operation["kind"] == "park":
            parks = result["batch"]["parks_consecutive"] + 1
            result["batch"]["parks_consecutive"] = parks
            if parks >= 2:
                result["work"]["phase"] = "paused"
                result["work"]["next_phase"] = "paused"
                result["control"]["pause_reason"] = {
                    "site": "systemic_park",
                    "detail": (
                        f"{parks} consecutive PRDs parked via wrapper_died; "
                        "batch halted"
                    ),
                    "created_at": operation["created_at"],
                }
        else:
            result["batch"]["parks_consecutive"] = 0
        return result

    return store.transaction(commit, publication_guard=verify)


@dataclass(frozen=True)
class _Request:
    kind: RecoveryKind
    prd: str
    site: str
    detail: str
    reconcile_any: bool = False


def _validate_request(state: State, request: _Request) -> None:
    _files._require_basename(request.prd, "prd")
    _files._require_basename(state["batch"]["id"], "batch_id")
    if state["work"]["phase"] == "done" and state["work"]["next_phase"] == "":
        raise RecoveryConflictError("cannot park or stall a drained workflow")
    pending = state["recovery"]["operation"]
    if pending is None:
        if state["work"]["prd"] != request.prd:
            raise RecoveryConflictError(
                f"requested PRD {request.prd!r} does not match active PRD {state['work']['prd']!r}"
            )
    elif not request.reconcile_any and (
        pending["prd"],
        pending["kind"],
        pending["site"],
        pending["detail"],
    ) != (request.prd, request.kind, request.site, request.detail):
        raise RecoveryConflictError(
            f"recovery operation {pending['id']} for {pending['prd']} "
            f"conflicts with requested {request.kind} intent for {request.prd}"
        )


def _prepare_operation(
    state: State,
    paths: LifecyclePaths,
    request: _Request,
    operation_id_factory: OperationIdFactory,
    now: TimestampFactory,
) -> RecoveryOperation:
    _validate_request(state, request)
    pending = state["recovery"]["operation"]
    if pending is not None:
        _operation_paths(paths, pending)
        return pending
    operation: RecoveryOperation = {
        "id": _files._require_operation_id(operation_id_factory()),
        "kind": request.kind,
        "step": "intent",
        "prd": request.prd,
        "site": request.site,
        "detail": request.detail,
        "source": str(paths.wip / request.prd),
        "destination": str(paths.hold / request.prd),
        "artifact": None,
        "created_at": now(),
    }
    candidate = copy.deepcopy(state)
    candidate["recovery"]["operation"] = operation
    validate_state(candidate)
    return operation


def _begin_operation(
    store: StateStore,
    state: State,
    operation: RecoveryOperation,
    runtime_root: Path,
    wip_directory: int,
    hold_directory: int,
    boundary_hook: BoundaryHook | None,
) -> SagaResult | None:
    source, destination = Path(operation["source"]), Path(operation["destination"])
    prd = operation["prd"]
    _validate_prd_artifact(wip_directory, source, "source")
    _validate_prd_artifact(hold_directory, destination, "destination")
    if (
        _artifact_stat(wip_directory, prd) is None
        and _artifact_stat(hold_directory, prd) is not None
    ):
        completed_id = _completed_operation_id(
            state,
            runtime_root,
            kind=operation["kind"],
            prd=prd,
            site=operation["site"],
            detail=operation["detail"],
        )
        if completed_id is None:
            raise RecoveryConflictError(
                f"held PRD {prd!r} has no durable recovery proof"
            )
        return SagaResult(
            completed_id,
            operation["kind"],
            True,
            operation["kind"] == "park" and state["work"]["phase"] == "paused",
        )
    operation["artifact"] = _artifact_identity(_artifact_stat(wip_directory, prd))
    _trip(boundary_hook, SagaBoundary.AFTER_MKDIR_BEFORE_INTENT)
    _stamp_intent(store, operation, state["revision"])
    return None


def _move_operation(
    store: StateStore,
    operation: RecoveryOperation,
    wip_directory: int,
    hold_directory: int,
    boundary_hook: BoundaryHook | None,
) -> Callable[[], None]:
    source, destination = Path(operation["source"]), Path(operation["destination"])
    if operation["step"] == "intent":
        _trip(boundary_hook, SagaBoundary.AFTER_INTENT_BEFORE_MOVE)
        _verify_move(
            source,
            destination,
            source_directory=wip_directory,
            destination_directory=hold_directory,
            boundary_hook=boundary_hook,
            identity=operation["artifact"],
        )

    def verify() -> None:
        _verify_moved_artifact(
            source,
            destination,
            source_directory=wip_directory,
            destination_directory=hold_directory,
        )
        _require_artifact_identity(hold_directory, destination, operation["artifact"])

    verify()
    if operation["step"] == "intent":
        _advance_operation(store, operation["id"], "intent", "moved", verify=verify)
        operation["step"] = "moved"
    return verify


def _append_operation_record(
    store: StateStore,
    operation: RecoveryOperation,
    ledger: Path,
    directory: int,
    batch_id: str,
    item: dict[str, JSONValue],
    verify_move: Callable[[], None],
    verify_recorded: Callable[[], None],
    verify_lock: Callable[[], None],
    boundary_hook: BoundaryHook | None,
) -> None:
    def trip_record_boundary(boundary: DeferBoundary) -> None:
        if boundary is DeferBoundary.AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC:
            _trip(boundary_hook, SagaBoundary.AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC)

    _trip(boundary_hook, SagaBoundary.AFTER_MOVE_BEFORE_APPEND)
    verify_move()
    _files._append_deferred_record(
        ledger, directory, batch_id, item, trip_record_boundary, verify_lock
    )
    verify_recorded()
    _advance_operation(
        store, operation["id"], "moved", "recorded", verify=verify_recorded
    )
    operation["step"] = "recorded"


def _operation_record(operation: RecoveryOperation) -> dict[str, JSONValue]:
    return _files._deferred_item(
        operation["prd"],
        {
            "type": "stall",
            "kind": operation["kind"],
            "site": operation["site"],
            "detail": operation["detail"],
            "op_id": operation["id"],
        },
    )


def _record_and_commit(
    store: StateStore,
    operation: RecoveryOperation,
    runtime_root: Path,
    batch_id: str,
    verify_move: Callable[[], None],
    boundary_hook: BoundaryHook | None,
) -> State:
    item = _operation_record(operation)
    with _files._open_deferred_ledger(runtime_root, batch_id) as (
        ledger,
        directory,
        verify_lock,
    ):

        def verify_recorded() -> None:
            verify_move()
            verify_lock()
            content = _files._read_record_file(ledger, batch_id, directory)
            if item not in cast(list[dict[str, JSONValue]], content["items"]):
                raise RecoveryConflictError(
                    f"recovery operation {item['op_id']} has no matching deferred record"
                )

        if operation["step"] == "moved":
            _append_operation_record(
                store,
                operation,
                ledger,
                directory,
                batch_id,
                item,
                verify_move,
                verify_recorded,
                verify_lock,
                boundary_hook,
            )
        else:
            verify_recorded()
            _files._sync_deferred_directory(ledger.parent, directory)
        _trip(boundary_hook, SagaBoundary.AFTER_APPEND_BEFORE_COMMIT)
        verify_recorded()
        return _commit_operation(store, operation, verify=verify_recorded)


def _execute_operation(
    store: StateStore,
    *,
    paths: LifecyclePaths,
    runtime_root: Path,
    request: _Request,
    boundary_hook: BoundaryHook | None,
    operation_id_factory: OperationIdFactory,
    now: TimestampFactory,
) -> SagaResult:
    state = store.read()
    operation = _prepare_operation(state, paths, request, operation_id_factory, now)
    replayed = state["recovery"]["operation"] is not None
    with (
        _files._open_lifecycle_directory(paths.wip) as wip_directory,
        _files._open_lifecycle_directory(paths.hold, create=True) as hold_directory,
    ):
        if not replayed:
            completed = _begin_operation(
                store,
                state,
                operation,
                runtime_root,
                wip_directory,
                hold_directory,
                boundary_hook,
            )
            if completed is not None:
                return completed
        verify_move = _move_operation(
            store, operation, wip_directory, hold_directory, boundary_hook
        )
        committed = _record_and_commit(
            store,
            operation,
            runtime_root,
            state["batch"]["id"],
            verify_move,
            boundary_hook,
        )
    _trip(boundary_hook, SagaBoundary.AFTER_COMMIT_BEFORE_MARKER_DELETE)
    return SagaResult(
        operation["id"],
        operation["kind"],
        replayed,
        operation["kind"] == "park" and committed["work"]["phase"] == "paused",
    )


def stall(
    store: StateStore,
    *,
    paths: LifecyclePaths,
    runtime_root: Path,
    prd: str,
    site: str,
    detail: str,
    boundary_hook: BoundaryHook | None = None,
    operation_id_factory: OperationIdFactory = _new_operation_id,
    now: TimestampFactory = _utc_now,
) -> SagaResult:
    """Run or reconcile the durable stall saga for ``prd``."""
    return _execute_operation(
        store,
        paths=paths,
        runtime_root=runtime_root,
        request=_Request("stall", prd, site, detail),
        boundary_hook=boundary_hook,
        operation_id_factory=operation_id_factory,
        now=now,
    )


def park(
    store: StateStore,
    *,
    paths: LifecyclePaths,
    runtime_root: Path,
    detail: str = "session ended without a committed transition",
    boundary_hook: BoundaryHook | None = None,
    operation_id_factory: OperationIdFactory = _new_operation_id,
    now: TimestampFactory = _utc_now,
) -> SagaResult:
    """Park the active PRD, or first reconcile any durable recovery intent."""
    state = store.read()
    operation = state["recovery"]["operation"]
    prd = operation["prd"] if operation is not None else state["work"]["prd"]
    if prd is None:
        raise ValueError("cannot park without an active PRD")
    return _execute_operation(
        store,
        paths=paths,
        runtime_root=runtime_root,
        request=_Request("park", prd, "wrapper_died", detail, operation is not None),
        boundary_hook=boundary_hook,
        operation_id_factory=operation_id_factory,
        now=now,
    )
