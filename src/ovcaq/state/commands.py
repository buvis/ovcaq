import copy
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Final, Literal, NotRequired, TypedDict, cast

from ovcaq.state.paths import (
    PathToken,
    append_path,
    delete_path,
    get_path,
    parse_path,
    set_path,
)
from ovcaq.state.schema import (
    AttemptEntry,
    CapabilityAttempt,
    CapabilityEntry,
    JSONValue,
    Notice,
    State,
    TaskEntry,
    TaskEstimates,
    TaskStatus,
    validate_json_value,
    validate_timestamp,
)
from ovcaq.state.store import StateStore


class TaskCreate(TypedDict):
    id: NotRequired[int]
    name: str
    description: NotRequired[str]
    active_form: NotRequired[str]
    blocked_by: NotRequired[list[int]]
    tier: NotRequired[str | None]
    files_touched: NotRequired[int | None]
    public_contract_edit: NotRequired[bool | None]
    estimates: NotRequired[TaskEstimates]
    metadata: NotRequired[dict[str, JSONValue]]


class TaskMetaPatch(TypedDict, total=False):
    tier: str | None
    files_touched: int | None
    public_contract_edit: bool | None
    estimates: TaskEstimates
    metadata: dict[str, JSONValue]


class MutationResult(TypedDict):
    revision: int
    task_id: int | None


class StateMutationConflictError(ValueError):
    """Raised when a public mutation conflicts with durable recovery."""


type ServiceMutator = Callable[[State], State | None]


_TASK_CREATE_FIELDS = frozenset(TaskCreate.__annotations__)
_TASK_META_FIELDS = frozenset(TaskMetaPatch.__annotations__)
_TASK_STATUSES: frozenset[str] = frozenset({"pending", "in_progress", "completed"})
GENERIC_WRITABLE_PREFIXES: Final[tuple[tuple[PathToken, ...], ...]] = (
    ("work", "extensions"),
    ("review", "extensions"),
)


def _require_task_id(value: object) -> int:
    if type(value) is not int:
        raise ValueError(f"task id must be an integer: {value!r}")
    return value


def _preflight_task_create_ids(payload: TaskCreate) -> None:
    if "id" in payload:
        _require_task_id(payload["id"])
    blocked_by = payload.get("blocked_by")
    if isinstance(blocked_by, list):
        for task_id in blocked_by:
            _require_task_id(task_id)


def _task_by_id(state: State, task_id: int) -> TaskEntry:
    task_id = _require_task_id(task_id)
    for task in state["tasks"]:
        if task["id"] == task_id:
            return task
    raise ValueError(f"unknown task id: {task_id}")


def _refresh_task_counts(state: State) -> None:
    state["work"]["tasks_total"] = len(state["tasks"])
    state["work"]["tasks_completed"] = sum(
        task["status"] == "completed" for task in state["tasks"]
    )


def _result(state: State, task_id: int | None) -> MutationResult:
    return {"revision": state["revision"], "task_id": task_id}


def _require_recovery_idle(state: State) -> None:
    operation = state["recovery"]["operation"]
    if operation is not None:
        raise StateMutationConflictError(
            f"recovery operation {operation['id']!r} is active; reconcile it first"
        )


def _capability_by_name(state: State, name: str) -> CapabilityEntry:
    capability = state["batch"]["capabilities"].get(name)
    if capability is None:
        raise ValueError(f"unknown capability: {name!r}")
    return capability


def _require_restorable_recovery(state: State) -> None:
    operation = state["recovery"]["operation"]
    # Earlier writers could publish an intent without a source artifact. Such
    # an operation cannot pass the move's identity check and cannot reconcile.
    # Explicit backup restoration is safe only before any bound recovery work.
    if (
        operation is not None
        and operation["step"] == "intent"
        and operation["artifact"] is None
    ):
        return
    _require_recovery_idle(state)


def _require_detail(detail: object) -> str | None:
    if detail is not None and not isinstance(detail, str):
        raise ValueError(f"capability detail must be a string or null: {detail!r}")
    return detail


def _generic_path(path: str, *, unsafe: bool) -> tuple[PathToken, ...]:
    tokens = parse_path(path)
    if not unsafe and not any(
        len(tokens) > len(prefix) and tokens[: len(prefix)] == prefix
        for prefix in GENERIC_WRITABLE_PREFIXES
    ):
        raise ValueError(f"generic mutation path is protected: {path!r}")
    return tokens


class StateService:
    def __init__(
        self,
        store: StateStore,
        *,
        publication_guard: Callable[[], None] | None = None,
    ) -> None:
        """Use an optional publication guard that must not acquire/read this store."""
        self._store = store
        self._publication_guard = publication_guard

    def show(self) -> State:
        return self._store.read()

    def validate(self) -> State:
        return self.show()

    def get(self, path: str) -> JSONValue:
        state = cast(JSONValue, self._store.read())
        return get_path(state, parse_path(path))

    def _transaction(
        self,
        mutator: ServiceMutator,
        *,
        expected_revision: int | None,
    ) -> State:
        def guarded(state: State) -> State | None:
            _require_recovery_idle(state)
            return mutator(state)

        return self._store.transaction(
            guarded,
            expected_revision=expected_revision,
            publication_guard=self._publication_guard,
        )

    def add_task(
        self,
        payload: TaskCreate,
        *,
        expected_revision: int | None = None,
    ) -> MutationResult:
        _preflight_task_create_ids(payload)
        task_id: int | None = None

        def mutate(state: State) -> None:
            nonlocal task_id
            unknown_fields = set(payload) - _TASK_CREATE_FIELDS
            if unknown_fields:
                raise ValueError(f"unknown task fields: {sorted(unknown_fields)!r}")
            name = payload.get("name")
            if not isinstance(name, str) or not name:
                raise ValueError("task name must be a nonempty string")

            assigned_id = (
                payload["id"]
                if "id" in payload
                else max((task["id"] for task in state["tasks"]), default=0) + 1
            )
            task_id = assigned_id
            estimates = cast(
                TaskEstimates,
                payload.get("estimates", {"input_tokens": None, "context_peak": None}),
            )
            task: TaskEntry = {
                "id": assigned_id,
                "name": name,
                "description": payload.get("description", ""),
                "active_form": payload.get("active_form", ""),
                "status": "pending",
                "blocked_by": payload.get("blocked_by", []),
                "tier": payload.get("tier"),
                "files_touched": payload.get("files_touched"),
                "public_contract_edit": payload.get("public_contract_edit"),
                "estimates": estimates,
                "attempts": [],
                "metadata": payload.get("metadata", {}),
            }
            state["tasks"].append(task)
            _refresh_task_counts(state)

        committed = self._transaction(mutate, expected_revision=expected_revision)
        return _result(committed, task_id)

    def start_task(
        self,
        task_id: int,
        *,
        expected_revision: int | None = None,
    ) -> MutationResult:
        task_id = _require_task_id(task_id)

        def mutate(state: State) -> None:
            _task_by_id(state, task_id)["status"] = "in_progress"
            _refresh_task_counts(state)

        committed = self._transaction(
            mutate,
            expected_revision=expected_revision,
        )
        return _result(committed, task_id)

    def append_attempt(
        self,
        task_id: int,
        attempt: AttemptEntry,
        *,
        expected_revision: int | None = None,
    ) -> MutationResult:
        task_id = _require_task_id(task_id)

        def mutate(state: State) -> None:
            task = _task_by_id(state, task_id)
            expected_number = len(task["attempts"]) + 1
            if attempt.get("number") != expected_number:
                raise ValueError(f"attempt number must be {expected_number}")
            task["attempts"].append(attempt)
            _refresh_task_counts(state)

        committed = self._transaction(
            mutate,
            expected_revision=expected_revision,
        )
        return _result(committed, task_id)

    def complete_task(
        self,
        task_id: int,
        attempt: AttemptEntry,
        *,
        expected_revision: int | None = None,
    ) -> MutationResult:
        task_id = _require_task_id(task_id)

        def mutate(state: State) -> None:
            task = _task_by_id(state, task_id)
            expected_number = len(task["attempts"]) + 1
            if attempt.get("number") != expected_number:
                raise ValueError(f"attempt number must be {expected_number}")
            task["attempts"].append(attempt)
            task["status"] = "completed"
            _refresh_task_counts(state)

        committed = self._transaction(
            mutate,
            expected_revision=expected_revision,
        )
        return _result(committed, task_id)

    def set_task_body(
        self,
        task_id: int,
        body: str,
        *,
        expected_revision: int | None = None,
    ) -> MutationResult:
        task_id = _require_task_id(task_id)

        def mutate(state: State) -> None:
            _task_by_id(state, task_id)["description"] = body
            _refresh_task_counts(state)

        committed = self._transaction(
            mutate,
            expected_revision=expected_revision,
        )
        return _result(committed, task_id)

    def set_task_meta(
        self,
        task_id: int,
        patch: TaskMetaPatch,
        *,
        expected_revision: int | None = None,
    ) -> MutationResult:
        task_id = _require_task_id(task_id)

        def mutate(state: State) -> None:
            unknown_fields = set(patch) - _TASK_META_FIELDS
            if unknown_fields:
                raise ValueError(f"unknown task metadata: {sorted(unknown_fields)!r}")
            task = _task_by_id(state, task_id)
            if "tier" in patch:
                task["tier"] = patch["tier"]
            if "files_touched" in patch:
                task["files_touched"] = patch["files_touched"]
            if "public_contract_edit" in patch:
                task["public_contract_edit"] = patch["public_contract_edit"]
            if "estimates" in patch:
                task["estimates"] = patch["estimates"]
            if "metadata" in patch:
                task["metadata"] = patch["metadata"]
            _refresh_task_counts(state)

        committed = self._transaction(
            mutate,
            expected_revision=expected_revision,
        )
        return _result(committed, task_id)

    def set_task_status(
        self,
        task_id: int,
        status: TaskStatus,
        *,
        expected_revision: int | None = None,
    ) -> MutationResult:
        task_id = _require_task_id(task_id)

        def mutate(state: State) -> None:
            task = _task_by_id(state, task_id)
            if status not in _TASK_STATUSES:
                raise ValueError(f"invalid task status: {status!r}")
            task["status"] = status
            _refresh_task_counts(state)

        committed = self._transaction(
            mutate,
            expected_revision=expected_revision,
        )
        return _result(committed, task_id)

    def clear_tasks(
        self,
        *,
        expected_revision: int | None = None,
    ) -> MutationResult:
        def mutate(state: State) -> None:
            state["tasks"].clear()
            state["review"]["rework_task_ids"].clear()
            _refresh_task_counts(state)

        committed = self._transaction(
            mutate,
            expected_revision=expected_revision,
        )
        return _result(committed, None)

    def set_contract_card(
        self,
        text: str,
        *,
        expected_revision: int | None = None,
    ) -> MutationResult:
        def mutate(state: State) -> None:
            state["work"]["contract_card"] = text.rstrip("\n")

        committed = self._transaction(
            mutate,
            expected_revision=expected_revision,
        )
        return _result(committed, None)

    def set(
        self,
        path: str,
        value: JSONValue,
        *,
        unsafe: bool = False,
        expected_revision: int | None = None,
    ) -> State:
        tokens = _generic_path(path, unsafe=unsafe)
        stored_value = copy.deepcopy(validate_json_value(value, "state value"))

        def mutate(state: State) -> None:
            set_path(state, tokens, stored_value)

        return self._transaction(
            mutate,
            expected_revision=expected_revision,
        )

    def append(
        self,
        path: str,
        value: JSONValue,
        *,
        unsafe: bool = False,
        expected_revision: int | None = None,
    ) -> State:
        tokens = _generic_path(path, unsafe=unsafe)
        stored_value = copy.deepcopy(validate_json_value(value, "state value"))

        def mutate(state: State) -> None:
            append_path(state, tokens, stored_value)

        return self._transaction(
            mutate,
            expected_revision=expected_revision,
        )

    def delete(
        self,
        path: str,
        *,
        unsafe: bool = False,
        expected_revision: int | None = None,
    ) -> State:
        tokens = _generic_path(path, unsafe=unsafe)

        def mutate(state: State) -> None:
            delete_path(state, tokens)

        return self._transaction(
            mutate,
            expected_revision=expected_revision,
        )

    def request_pause(
        self,
        reason: Notice | None,
        *,
        expected_revision: int | None = None,
    ) -> State:
        stored_reason = copy.deepcopy(reason)

        def mutate(state: State) -> None:
            state["control"]["pause_requested"] = True
            state["control"]["pause_reason"] = stored_reason

        return self._transaction(mutate, expected_revision=expected_revision)

    def resume(self, *, expected_revision: int | None = None) -> State:
        def mutate(state: State) -> None:
            state["control"]["pause_requested"] = False
            if "paused" not in (state["work"]["phase"], state["work"]["next_phase"]):
                state["control"]["pause_reason"] = None

        return self._transaction(mutate, expected_revision=expected_revision)

    def record_progress(
        self,
        fingerprint: str,
        repeats: int,
        *,
        expected_revision: int | None = None,
    ) -> State:
        if not isinstance(fingerprint, str) or not fingerprint.strip():
            raise ValueError("phase fingerprint must be a nonblank string")
        if type(repeats) is not int or repeats < 0:
            raise ValueError(
                f"phase repeats must be a nonnegative integer: {repeats!r}"
            )

        def mutate(state: State) -> None:
            state["recovery"]["phase_fingerprint"] = fingerprint
            state["recovery"]["phase_repeats"] = repeats

        return self._transaction(mutate, expected_revision=expected_revision)

    def start_batch(
        self, batch_id: str, started_at: str, *, expected_revision: int | None = None
    ) -> State:
        validate_timestamp(started_at, "started_at")

        def mutate(state: State) -> None:
            batch = state["batch"]
            batch["id"] = batch["id"] or batch_id
            batch["started_at"] = batch["started_at"] or started_at
            if batch["status"] == "idle":
                batch["status"] = "running"

        return self._transaction(mutate, expected_revision=expected_revision)

    def revert_batch_start(
        self, batch_id: str, *, expected_revision: int | None = None
    ) -> State:
        """Return a batch this run started, and never served, to its defaults."""

        def mutate(state: State) -> None:
            batch = state["batch"]
            if (
                batch["status"] != "running"
                or batch["id"] != batch_id
                or state["work"]["prd"] is not None
                or batch["completed_prds"] != []
            ):
                raise ValueError("batch is not a fresh started batch")
            batch["id"] = ""
            batch["started_at"] = None
            batch["status"] = "idle"

        return self._transaction(mutate, expected_revision=expected_revision)

    def complete_batch(
        self, completed_at: str, *, expected_revision: int | None = None
    ) -> State:
        validate_timestamp(completed_at, "completed_at")

        def mutate(state: State) -> None:
            batch = state["batch"]
            if state["work"]["next_phase"] or any(
                entry["required"] and entry["status"] != "succeeded"
                for entry in batch["capabilities"].values()
            ):
                raise ValueError("batch is not complete")
            batch["status"] = "completed"
            batch["completed_at"] = completed_at

        return self._transaction(mutate, expected_revision=expected_revision)

    def start_capability(
        self,
        name: str,
        attempt: CapabilityAttempt,
        *,
        expected_revision: int | None = None,
    ) -> State:
        return self._begin_capability(name, attempt, "pending", expected_revision)

    def retry_capability(
        self,
        name: str,
        attempt: CapabilityAttempt,
        *,
        expected_revision: int | None = None,
    ) -> State:
        return self._begin_capability(name, attempt, "failed", expected_revision)

    def _begin_capability(
        self,
        name: str,
        attempt: CapabilityAttempt,
        eligible: Literal["pending", "failed"],
        expected_revision: int | None,
    ) -> State:
        validate_timestamp(attempt["started_at"], "attempt.started_at")
        if attempt["status"] != "running" or attempt["finished_at"] is not None:
            raise ValueError("a new capability attempt must be running and unfinished")
        _require_detail(attempt["detail"])
        stored_attempt = copy.deepcopy(attempt)

        def mutate(state: State) -> None:
            capability = _capability_by_name(state, name)
            if not capability["required"]:
                raise ValueError(f"capability {name!r} is optional")
            if capability["status"] != eligible:
                raise ValueError(f"capability {name!r} is {capability['status']}")
            if any(
                other["status"] == "running"
                for other in state["batch"]["capabilities"].values()
            ):
                raise ValueError("another capability is already running")
            capability["status"] = "running"
            capability["attempts"].append(stored_attempt)

        return self._transaction(mutate, expected_revision=expected_revision)

    def finish_capability(
        self,
        name: str,
        attempt_id: str,
        *,
        succeeded: bool,
        detail: str | None,
        finished_at: str,
        expected_revision: int | None = None,
    ) -> State:
        validate_timestamp(finished_at, "finished_at")
        _require_detail(detail)

        def mutate(state: State) -> None:
            capability = _capability_by_name(state, name)
            if capability["status"] != "running":
                raise ValueError(f"capability {name!r} is {capability['status']}")
            attempt = capability["attempts"][-1]
            if attempt["id"] != attempt_id:
                raise ValueError(f"attempt {attempt_id!r} is not the running attempt")
            if datetime.fromisoformat(finished_at) < datetime.fromisoformat(
                attempt["started_at"]
            ):
                raise ValueError("finished_at precedes the attempt start")
            status: Literal["failed", "succeeded"] = (
                "succeeded" if succeeded else "failed"
            )
            attempt |= {"status": status, "finished_at": finished_at, "detail": detail}
            capability["status"] = status
            batch = state["batch"]
            attention = state["control"]["attention"]
            if succeeded and attention and attention["site"] == f"capability:{name}":
                state["control"]["attention"] = None
            if not succeeded:
                batch.update({"status": "attention", "completed_at": None})
                state["control"]["attention"] = {
                    "site": f"capability:{name}",
                    "detail": f"capability {name!r} failed: {detail or 'no detail'}",
                    "created_at": finished_at,
                }
            elif all(
                entry["status"] == "succeeded"
                for entry in batch["capabilities"].values()
                if entry["required"]
            ):
                batch["status"] = "completed"
                batch["completed_at"] = finished_at

        return self._transaction(mutate, expected_revision=expected_revision)

    def reconcile_capability(
        self,
        name: str,
        attempt_id: str,
        *,
        detail: str,
        finished_at: str,
        expected_revision: int | None = None,
    ) -> State:
        return self.finish_capability(
            name,
            attempt_id,
            succeeded=False,
            detail=detail,
            finished_at=finished_at,
            expected_revision=expected_revision,
        )

    def skip_empty_drain_capabilities(
        self, *, completed_at: str | None = None, expected_revision: int | None = None
    ) -> State:
        completed_at = completed_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        validate_timestamp(completed_at, "completed_at")

        def mutate(state: State) -> None:
            batch = state["batch"]
            if state["work"]["next_phase"] or batch["completed_prds"]:
                raise ValueError("batch is not an empty drain")
            capabilities = batch["capabilities"]
            if any(entry["status"] != "pending" for entry in capabilities.values()):
                raise ValueError("only pending capabilities can be skipped")
            for entry in capabilities.values():
                entry["required"] = False
                entry["status"] = "skipped"
            batch["status"] = "completed"
            batch["completed_at"] = completed_at

        return self._transaction(mutate, expected_revision=expected_revision)

    def restore(
        self,
        *,
        expected_revision: int | None = None,
    ) -> MutationResult:
        committed = self._store.restore(
            expected_revision=expected_revision,
            precondition=_require_restorable_recovery,
        )
        return _result(committed, None)
