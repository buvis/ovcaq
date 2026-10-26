from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, cast

import pytest

from ovcaq.state.commands import StateMutationConflictError, StateService
from ovcaq.state.schema import (
    CapabilityAttempt,
    CapabilityEntry,
    Notice,
    State,
    new_state,
    validate_state,
)
from ovcaq.state.store import RevisionConflictError, StateStore

T0 = "2026-08-26T10:00:00Z"
T1 = "2026-08-26T10:01:00Z"
NOTICE: Notice = {"site": "supervisor", "detail": "Inspect failure", "created_at": T0}
OPERATIONS = (
    "request_pause",
    "resume",
    "record_progress",
    "start_capability",
    "finish_capability",
    "reconcile_capability",
    "skip_empty_drain_capabilities",
)


def _attempt(identifier: str = "attempt-1") -> CapabilityAttempt:
    return {
        "id": identifier,
        "status": "running",
        "started_at": T0,
        "finished_at": None,
        "session_id": "session-1",
        "detail": None,
    }


def _capability() -> CapabilityEntry:
    return {
        "required": True,
        "launcher": "fake",
        "plugin": "fake/archive",
        "version": "1",
        "failure": "attention",
        "status": "pending",
        "attempts": [],
    }


def _state(tmp_path: Path, *, empty: bool = False) -> State:
    state = new_state(repo_root=tmp_path)
    state["batch"].update(id="batch-1", status="running", started_at=T0)
    state["batch"]["capabilities"] = {"archive": _capability(), "notify": _capability()}
    state["work"]["next_phase"] = ""
    state["work"]["extensions"] = {"test/work": {"keep": [1, 2]}}
    state["review"]["extensions"] = {"test/review": {"keep": [3, 4]}}
    if not empty:
        state["batch"]["completed_prds"] = [
            {
                "filename": "example.md",
                "cycles": 1,
                "autonomous_decisions": 1,
                "escalated_decisions": 0,
                "tasks_completed": 1,
                "tasks_total": 1,
            }
        ]
        state["tasks"] = [
            {
                "id": 1,
                "name": "Finished work",
                "description": "Preserve me",
                "active_form": "",
                "status": "completed",
                "blocked_by": [],
                "tier": None,
                "files_touched": None,
                "public_contract_edit": None,
                "estimates": {"input_tokens": None, "context_peak": None},
                "attempts": [],
                "metadata": {"sentinel": [1, 2]},
            }
        ]
        state["work"].update(tasks_total=1, tasks_completed=1)
    return state


def _completed(filename: str) -> dict[str, Any]:
    return {
        "filename": filename,
        "cycles": 1,
        "autonomous_decisions": 1,
        "escalated_decisions": 0,
        "tasks_completed": 1,
        "tasks_total": 1,
    }


def _fresh_batch(tmp_path: Path, *, batch_id: str, started_at: str) -> State:
    """A batch this run started and never served: no PRD, no completed work."""
    state = new_state(repo_root=tmp_path)
    state["batch"].update(id=batch_id, status="running", started_at=started_at)
    state["batch"]["capabilities"] = {"archive": _capability()}
    return state


def _service(tmp_path: Path, state: State) -> tuple[StateService, StateStore]:
    store = StateStore(tmp_path / "state.json")
    store.initialize(state)
    return StateService(store), store


def _bytes(tmp_path: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}


def _unchanged_work(before: State, after: State) -> None:
    for key in ("work", "tasks", "review"):
        assert before[key] == after[key]
    assert before["batch"]["completed_prds"] == after["batch"]["completed_prds"]


def _running(state: State, name: str = "archive") -> None:
    capability = state["batch"]["capabilities"][name]
    capability["status"] = "running"
    capability["attempts"] = [_attempt()]


def _invoke(service: StateService, operation: str, revision: int) -> State:
    kwargs: dict[str, Any] = {"expected_revision": revision}
    if operation == "request_pause":
        return service.request_pause(NOTICE, **kwargs)
    if operation == "record_progress":
        return service.record_progress("phase-1", 2, **kwargs)
    if operation == "start_capability":
        return service.start_capability("archive", _attempt(), **kwargs)
    if operation == "finish_capability":
        return service.finish_capability(
            "archive",
            "attempt-1",
            succeeded=True,
            detail=None,
            finished_at=T1,
            **kwargs,
        )
    if operation == "reconcile_capability":
        return service.reconcile_capability(
            "archive",
            "attempt-1",
            detail="Session lost; retry",
            finished_at=T1,
            **kwargs,
        )
    return cast(State, getattr(service, operation)(**kwargs))


@pytest.mark.parametrize("reason", [None, NOTICE])
def test_pause_and_resume_change_only_pause_fields(
    tmp_path: Path, reason: Notice | None
) -> None:
    initial = _state(tmp_path)
    _running(initial)
    capability = initial["batch"]["capabilities"]["archive"]
    capability["status"] = "failed"
    capability["attempts"][0].update(status="failed", finished_at=T1, detail="Retry")
    initial["control"]["attention"] = copy.deepcopy(NOTICE)
    initial["recovery"].update(phase_fingerprint="old", phase_repeats=3)
    service, store = _service(tmp_path, initial)
    paused = service.request_pause(reason, expected_revision=0)
    expected = copy.deepcopy(initial)
    expected["revision"] = 1
    expected["control"].update(pause_requested=True, pause_reason=reason)
    assert paused == expected == store.read()
    resumed = service.resume(expected_revision=1)
    expected["revision"] = 2
    expected["control"].update(pause_requested=False, pause_reason=None)
    assert resumed == expected == store.read()


@pytest.mark.parametrize("repeats", [0, 4])
def test_progress_changes_only_fingerprint_and_repeats(
    tmp_path: Path, repeats: int
) -> None:
    initial = _state(tmp_path)
    initial["recovery"]["replan_count"] = 2
    service, store = _service(tmp_path, initial)
    result = service.record_progress("phase:review", repeats, expected_revision=0)
    expected = copy.deepcopy(initial)
    expected["revision"] = 1
    expected["recovery"].update(phase_fingerprint="phase:review", phase_repeats=repeats)
    assert result == expected == store.read()


def test_capabilities_complete_batch_only_after_every_required_success(
    tmp_path: Path,
) -> None:
    initial = _state(tmp_path)
    initial["recovery"]["replan_count"] = 3
    initial["control"].update(pause_requested=True, pause_reason=copy.deepcopy(NOTICE))
    initial["batch"]["catchup"] = {"completed_at": T0, "head_sha": "abc123"}
    optional = _capability()
    optional["required"] = False
    initial["batch"]["capabilities"]["optional"] = optional
    service, store = _service(tmp_path, initial)
    for index, name in enumerate(("archive", "notify")):
        attempt = _attempt(f"attempt-{index}")
        started = service.start_capability(name, attempt, expected_revision=2 * index)
        assert started == store.read()
        assert started["revision"] == 2 * index + 1
        assert started["batch"]["capabilities"][name]["attempts"] == [attempt]
        assert started["batch"]["capabilities"][name]["status"] == "running"
        assert started["batch"]["status"] != "completed"
        result = service.finish_capability(
            name,
            attempt["id"],
            succeeded=True,
            detail=None,
            finished_at=T1,
            expected_revision=2 * index + 1,
        )
        assert result == store.read()
        assert result["revision"] == 2 * index + 2
        expected_attempt = {**attempt, "status": "succeeded", "finished_at": T1}
        assert result["batch"]["capabilities"][name]["attempts"] == [expected_attempt]
        assert result["batch"]["capabilities"][name]["status"] == "succeeded"
        assert (result["batch"]["status"] == "completed") == (index == 1)
        _unchanged_work(initial, started)
        _unchanged_work(initial, result)
        for state in (started, result):
            assert state["recovery"] == initial["recovery"]
            assert state["control"] == initial["control"]
            for key in ("id", "started_at", "catchup"):
                assert state["batch"][key] == initial["batch"][key]
    assert result["batch"]["completed_at"] == T1
    assert result["batch"]["capabilities"]["optional"] == optional
    assert validate_state(result) == result


@pytest.mark.parametrize("reconcile", [False, True])
@pytest.mark.parametrize(
    ("name", "detail"),
    [
        ("archive", "Session lost; retry archive"),
        ("notify", "Worker exited: delivery missing"),
    ],
    ids=["archive", "notify"],
)
def test_capability_failure_preserves_work_and_records_actionable_attention(
    tmp_path: Path, reconcile: bool, name: str, detail: str
) -> None:
    initial = _state(tmp_path)
    _running(initial, name)
    service, store = _service(tmp_path, initial)
    kwargs: dict[str, Any] = {
        "detail": detail,
        "finished_at": T1,
        "expected_revision": 0,
    }
    if reconcile:
        result = service.reconcile_capability(name, "attempt-1", **kwargs)
    else:
        result = service.finish_capability(name, "attempt-1", succeeded=False, **kwargs)
    assert result == store.read()
    assert result["revision"] == 1
    capability = result["batch"]["capabilities"][name]
    assert capability["status"] == "failed"
    assert capability["attempts"] == [
        {
            **_attempt(),
            "status": "failed",
            "finished_at": T1,
            "detail": detail,
        }
    ]
    attention = result["control"]["attention"]
    assert attention is not None
    assert attention["site"].strip()
    assert name in attention["site"] + attention["detail"]
    assert kwargs["detail"] in attention["detail"]
    assert result["batch"]["status"] == "attention"
    assert result["batch"]["completed_at"] is None
    other = "notify" if name == "archive" else "archive"
    assert (
        result["batch"]["capabilities"][other]
        == initial["batch"]["capabilities"][other]
    )
    _unchanged_work(initial, result)
    assert validate_state(result) == result


def test_empty_drain_skips_capabilities_without_attempts_and_completes(
    tmp_path: Path,
) -> None:
    initial = _state(tmp_path, empty=True)
    initial["control"]["attention"] = copy.deepcopy(NOTICE)
    service, store = _service(tmp_path, initial)
    result = service.skip_empty_drain_capabilities(expected_revision=0)
    assert result == store.read()
    assert result["revision"] == 1
    assert result["batch"]["status"] == "completed"
    assert result["batch"]["completed_at"] is not None
    assert result["batch"]["id"] == initial["batch"]["id"]
    assert result["control"] == initial["control"]
    for name, capability in result["batch"]["capabilities"].items():
        assert capability == {
            **initial["batch"]["capabilities"][name],
            "required": False,
            "status": "skipped",
        }
    _unchanged_work(initial, result)
    assert validate_state(result) == result


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("guard", ["revision", "recovery"])
def test_every_transition_rejects_conflicts_and_active_recovery_without_writes(
    tmp_path: Path, operation: str, guard: str
) -> None:
    initial = _state(tmp_path, empty=operation == "skip_empty_drain_capabilities")
    if operation in {"finish_capability", "reconcile_capability"}:
        _running(initial)
    if guard == "recovery":
        initial["recovery"]["operation"] = {
            "id": "recovery-1",
            "kind": "park",
            "step": "intent",
            "prd": "example.md",
            "site": "supervisor",
            "detail": "Moving PRD",
            "source": "backlog/example.md",
            "destination": "parked/example.md",
            "artifact": None,
            "created_at": T0,
        }
    service, store = _service(tmp_path, initial)
    store.transaction(lambda _state: None)
    before, data = store.read(), _bytes(tmp_path)
    with pytest.raises(RevisionConflictError if guard == "revision" else ValueError):
        _invoke(service, operation, 0 if guard == "revision" else 1)
    assert store.read() == before
    assert _bytes(tmp_path) == data


@pytest.mark.parametrize("unrelated_attention", [False, True])
@pytest.mark.parametrize(
    ("session_id", "detail", "finished_at"),
    [
        (None, None, "2026-08-26T10:02:00Z"),
        ("retry-session-alternate", "Archived all records", "2026-08-27T11:03:00Z"),
    ],
    ids=["no-session", "alternate-session-next-day"],
)
def test_successful_retry_completes_batch_and_clears_only_its_attention(
    tmp_path: Path,
    unrelated_attention: bool,
    session_id: str | None,
    detail: str | None,
    finished_at: str,
) -> None:
    initial = _state(tmp_path)
    initial["batch"]["capabilities"].pop("notify")
    _running(initial)
    service, store = _service(tmp_path, initial)
    failed = service.finish_capability(
        "archive",
        "attempt-1",
        succeeded=False,
        detail="Retry archive",
        finished_at=T1,
        expected_revision=0,
    )
    if unrelated_attention:
        store.transaction(lambda state: state["control"].update(attention=NOTICE))
    retry = _attempt("attempt-2")
    retry.update(started_at=T1, session_id=session_id)
    started = service.retry_capability(
        "archive", retry, expected_revision=store.read()["revision"]
    )
    result = service.finish_capability(
        "archive",
        "attempt-2",
        succeeded=True,
        detail=detail,
        finished_at=finished_at,
        expected_revision=started["revision"],
    )
    assert result == store.read()
    assert result["revision"] == started["revision"] + 1
    capability = result["batch"]["capabilities"]["archive"]
    assert capability["status"] == "succeeded"
    completed = dict(retry, status="succeeded", finished_at=finished_at, detail=detail)
    assert capability["attempts"] == [
        failed["batch"]["capabilities"]["archive"]["attempts"][0],
        completed,
    ]
    assert result["control"]["attention"] == (NOTICE if unrelated_attention else None)
    assert result["batch"]["status"] == "completed"
    assert result["batch"]["completed_at"] == finished_at
    _unchanged_work(initial, started)
    _unchanged_work(initial, result)


def test_retry_rejects_stale_revision_without_state_or_backup_writes(
    tmp_path: Path,
) -> None:
    initial = _state(tmp_path)
    _running(initial)
    service, store = _service(tmp_path, initial)
    service.finish_capability(
        "archive",
        "attempt-1",
        succeeded=False,
        detail="Retry archive",
        finished_at=T1,
        expected_revision=0,
    )
    before, data = store.read(), _bytes(tmp_path)
    retry = _attempt("retry-after-failure")
    retry.update(started_at=T1, session_id=None)
    with pytest.raises(RevisionConflictError):
        service.retry_capability("archive", retry, expected_revision=0)
    assert store.read() == before
    assert _bytes(tmp_path) == data


@pytest.mark.parametrize("other_status", ["pending", "running", "failed"])
def test_success_cannot_complete_batch_with_another_unfinished_required_capability(
    tmp_path: Path, other_status: str
) -> None:
    initial = _state(tmp_path)
    _running(initial)
    other = initial["batch"]["capabilities"]["notify"]
    other["status"] = cast(Any, other_status)
    if other_status != "pending":
        attempt = _attempt("notify-attempt")
        attempt.update(status=cast(Any, other_status), session_id="notify-session")
        if other_status == "failed":
            attempt.update(finished_at=T1, detail="Notify failed")
        other["attempts"] = [attempt]
    service, store = _service(tmp_path, initial)
    result = service.finish_capability(
        "archive",
        "attempt-1",
        succeeded=True,
        detail=None,
        finished_at=T1,
        expected_revision=0,
    )
    assert result == store.read()
    assert result["batch"]["capabilities"]["archive"]["status"] == "succeeded"
    assert result["batch"]["capabilities"]["notify"] == other
    assert result["batch"]["status"] != "completed"
    assert result["batch"]["completed_at"] is None
    _unchanged_work(initial, result)


@pytest.mark.parametrize(
    ("fingerprint", "repeats"),
    [("", 0), (" \t", 1), (None, 0), ("ok", -1), ("ok", True), ("ok", 1.5)],
)
def test_invalid_progress_preserves_state_and_backup(
    tmp_path: Path, fingerprint: Any, repeats: Any
) -> None:
    service, store = _service(tmp_path, _state(tmp_path))
    store.transaction(lambda _state: None)
    before, data = store.read(), _bytes(tmp_path)
    with pytest.raises(ValueError):
        service.record_progress(fingerprint, repeats, expected_revision=1)
    assert store.read() == before
    assert _bytes(tmp_path) == data


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "optional",
        "running",
        "failed",
        "succeeded",
        "skipped",
        "duplicate",
        "bad-time",
        "finished",
        "bad-status",
        "bad-detail",
    ],
)
def test_invalid_capability_start_preserves_state_and_backup(
    tmp_path: Path, case: str
) -> None:
    initial = _state(tmp_path)
    attempt = _attempt()
    name = "missing" if case == "missing" else "archive"
    capability = initial["batch"]["capabilities"]["archive"]
    if case == "optional":
        capability["required"] = False
    elif case in {"running", "failed", "succeeded"}:
        _running(initial)
        capability["status"] = cast(Any, case)
        capability["attempts"][0]["status"] = cast(Any, case)
        if case != "running":
            capability["attempts"][0]["finished_at"] = T1
    elif case == "skipped":
        capability.update(required=False, status="skipped")
    elif case == "duplicate":
        _running(initial, "notify")
    elif case == "bad-time":
        attempt["started_at"] = "yesterday"
    elif case == "finished":
        attempt["finished_at"] = T1
    elif case == "bad-status":
        attempt.update(status="failed", finished_at=T1)
    elif case == "bad-detail":
        attempt["detail"] = cast(Any, 42)
    service, store = _service(tmp_path, initial)
    store.transaction(lambda _state: None)
    before, data = store.read(), _bytes(tmp_path)
    with pytest.raises(ValueError):
        service.start_capability(name, attempt, expected_revision=1)
    assert store.read() == before
    assert _bytes(tmp_path) == data


@pytest.mark.parametrize("operation", ["finish_capability", "reconcile_capability"])
@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "stale",
        "pending",
        "failed",
        "succeeded",
        "bad-time",
        "backward-time",
        "bad-detail",
    ],
)
def test_invalid_capability_completion_preserves_state_and_backup(
    tmp_path: Path, operation: str, case: str
) -> None:
    initial = _state(tmp_path)
    if case != "pending":
        _running(initial)
    if case in {"failed", "succeeded"}:
        capability = initial["batch"]["capabilities"]["archive"]
        capability["status"] = cast(Any, case)
        capability["attempts"][0].update(status=cast(Any, case), finished_at=T1)
    service, store = _service(tmp_path, initial)
    store.transaction(lambda _state: None)
    before, data = store.read(), _bytes(tmp_path)
    kwargs: dict[str, Any] = {
        "detail": "Retry archive",
        "finished_at": T1,
        "expected_revision": 1,
    }
    if case == "bad-time":
        kwargs["finished_at"] = "tomorrow"
    elif case == "backward-time":
        kwargs["finished_at"] = "2026-08-25T10:00:00Z"
    elif case == "bad-detail":
        kwargs["detail"] = 42
    if operation == "finish_capability":
        kwargs["succeeded"] = False
    with pytest.raises(ValueError):
        getattr(service, operation)(
            "missing" if case == "missing" else "archive",
            "stale" if case == "stale" else "attempt-1",
            **kwargs,
        )
    assert store.read() == before
    assert _bytes(tmp_path) == data


@pytest.mark.parametrize(
    ("batch_id", "started_at"), [("batch-1", T0), ("batch-alternate", T1)]
)
def test_revert_batch_start_returns_a_fresh_running_batch_to_defaults(
    tmp_path: Path, batch_id: str, started_at: str
) -> None:
    initial = _fresh_batch(tmp_path, batch_id=batch_id, started_at=started_at)
    service, store = _service(tmp_path, initial)
    result = service.revert_batch_start(batch_id, expected_revision=0)
    expected = copy.deepcopy(initial)
    expected["revision"] = 1
    expected["batch"].update(id="", status="idle", started_at=None)
    assert result == expected == store.read()
    assert result["revision"] > initial["revision"]
    defaults = new_state(repo_root=tmp_path)["batch"]
    assert result["batch"]["id"] == defaults["id"] == ""
    assert result["batch"]["status"] == defaults["status"] == "idle"
    assert result["batch"]["started_at"] == defaults["started_at"] is None
    assert result["batch"]["capabilities"] == initial["batch"]["capabilities"]
    _unchanged_work(initial, result)
    assert validate_state(result) == result


@pytest.mark.parametrize(
    ("case", "requested"),
    [
        ("idle", "batch-1"),
        ("attention", "batch-1"),
        ("completed", "batch-1"),
        ("longer-id", "batch-12"),
        ("shorter-id", "batch"),
        ("same-length-id", "batch-2"),
        ("work-prd", "batch-1"),
        ("one-completed-prd", "batch-1"),
        ("two-completed-prds", "batch-1"),
    ],
    ids=[
        "idle",
        "attention",
        "completed",
        "longer-id",
        "shorter-id",
        "same-length-id",
        "work-prd",
        "one-completed-prd",
        "two-completed-prds",
    ],
)
def test_revert_batch_start_requires_fresh_running_batch(
    tmp_path: Path, case: str, requested: str
) -> None:
    initial = _fresh_batch(tmp_path, batch_id="batch-1", started_at=T0)
    if case in {"idle", "attention", "completed"}:
        initial["batch"]["status"] = cast(Any, case)
        if case == "completed":
            initial["batch"].update(completed_at=T1, capabilities={})
    elif case == "work-prd":
        initial["work"]["prd"] = "00007-feature.md"
    elif case == "one-completed-prd":
        initial["batch"]["completed_prds"] = [_completed("first.md")]
    elif case == "two-completed-prds":
        initial["batch"]["completed_prds"] = [
            _completed("first.md"),
            _completed("second.md"),
        ]
    service, store = _service(tmp_path, initial)
    store.transaction(lambda _state: None)
    before, data = store.read(), _bytes(tmp_path)
    with pytest.raises(ValueError) as caught:
        service.revert_batch_start(requested, expected_revision=1)
    assert str(caught.value) == "batch is not a fresh started batch"
    assert store.read() == before
    assert _bytes(tmp_path) == data


def test_revert_batch_start_obeys_the_expected_revision(tmp_path: Path) -> None:
    initial = _fresh_batch(tmp_path, batch_id="batch-1", started_at=T0)
    service, store = _service(tmp_path, initial)
    store.transaction(lambda _state: None)
    before, data = store.read(), _bytes(tmp_path)
    with pytest.raises(RevisionConflictError):
        service.revert_batch_start("batch-1", expected_revision=0)
    assert store.read() == before
    assert _bytes(tmp_path) == data
    reverted = service.revert_batch_start("batch-1", expected_revision=1)
    assert reverted == store.read()
    assert reverted["revision"] == 2
    assert reverted["batch"]["id"] == "" and reverted["batch"]["status"] == "idle"
    assert reverted["batch"]["started_at"] is None


def test_revert_batch_start_rejects_an_active_recovery_without_writes(
    tmp_path: Path,
) -> None:
    initial = _fresh_batch(tmp_path, batch_id="batch-1", started_at=T0)
    initial["recovery"]["operation"] = {
        "id": "recovery-1",
        "kind": "park",
        "step": "intent",
        "prd": "example.md",
        "site": "supervisor",
        "detail": "Moving PRD",
        "source": "backlog/example.md",
        "destination": "parked/example.md",
        "artifact": None,
        "created_at": T0,
    }
    service, store = _service(tmp_path, initial)
    store.transaction(lambda _state: None)
    before, data = store.read(), _bytes(tmp_path)
    with pytest.raises(StateMutationConflictError):
        service.revert_batch_start("batch-1", expected_revision=1)
    assert store.read() == before
    assert _bytes(tmp_path) == data


def test_revert_batch_start_honors_the_publication_guard_without_writes(
    tmp_path: Path,
) -> None:
    class GuardRefusal(Exception):
        pass

    calls: list[int] = []

    def refuse() -> None:
        calls.append(1)
        raise GuardRefusal("publication is fenced")

    initial = _fresh_batch(tmp_path, batch_id="batch-1", started_at=T0)
    _, store = _service(tmp_path, initial)
    store.transaction(lambda _state: None)
    before, data = store.read(), _bytes(tmp_path)
    service = StateService(store, publication_guard=refuse)
    with pytest.raises(GuardRefusal):
        service.revert_batch_start("batch-1", expected_revision=1)
    assert calls
    assert store.read() == before
    assert _bytes(tmp_path) == data


@pytest.mark.parametrize(
    "case", ["not-drained", "completed-prds", "running", "failed", "succeeded"]
)
def test_empty_drain_rejects_work_or_started_capabilities_without_writes(
    tmp_path: Path, case: str
) -> None:
    initial = _state(tmp_path, empty=case != "completed-prds")
    if case == "not-drained":
        initial["work"]["next_phase"] = "build"
    elif case in {"running", "failed", "succeeded"}:
        _running(initial)
        capability = initial["batch"]["capabilities"]["archive"]
        capability["status"] = cast(Any, case)
        capability["attempts"][0]["status"] = cast(Any, case)
        if case != "running":
            capability["attempts"][0]["finished_at"] = T1
    service, store = _service(tmp_path, initial)
    store.transaction(lambda _state: None)
    before, data = store.read(), _bytes(tmp_path)
    with pytest.raises(ValueError):
        service.skip_empty_drain_capabilities(expected_revision=1)
    assert store.read() == before
    assert _bytes(tmp_path) == data
