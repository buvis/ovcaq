from __future__ import annotations

import json
from pathlib import Path

import pytest

from ovcaq.state.commands import StateService
from ovcaq.state.schema import Notice, State, new_state
from ovcaq.state.store import DurabilityBoundary, RevisionConflictError, StateStore

NOTICE: Notice = {
    "site": "supervisor",
    "detail": "Selected owner pause",
    "created_at": "2026-08-26T10:00:00Z",
}
OTHER_NOTICE: Notice = {
    "site": "operator",
    "detail": "Pause for a separate inspection",
    "created_at": "2026-08-27T11:30:00Z",
}


class RejectedOwner(RuntimeError):
    pass


def seed(
    path: Path, operation: str, *, backup_exists: bool = True
) -> tuple[StateStore, State]:
    state = new_state(repo_root=path.parent)
    state["batch"].update(
        id="batch-1", status="running", started_at=NOTICE["created_at"]
    )
    state["work"]["extensions"] = {"test/keep": [1, 2]}
    state["review"]["extensions"] = {"test/keep": [3, 4]}
    state["control"]["pause_requested"] = operation == "resume"
    state["control"]["pause_reason"] = NOTICE if operation == "resume" else None
    store = StateStore(path)
    current = store.initialize(state)
    if backup_exists:
        current = store.transaction(lambda candidate: None)
        path.with_name(path.name + ".bak").write_bytes(b"opaque previous backup\x00\n")
    path.write_text(json.dumps(current, indent=3) + "\n")
    return store, current


def invoke(
    service: StateService,
    operation: str,
    revision: int | None = None,
    reason: Notice | None = NOTICE,
) -> State:
    kwargs = {} if revision is None else {"expected_revision": revision}
    if operation == "request_pause":
        return service.request_pause(reason, **kwargs)
    return service.resume(**kwargs)


def durable_bytes(path: Path) -> tuple[bytes, bytes | None]:
    backup = path.with_name(path.name + ".bak")
    return path.read_bytes(), backup.read_bytes() if backup.exists() else None


@pytest.mark.parametrize(
    ("operation", "reason"),
    (
        ("request_pause", None),
        ("request_pause", NOTICE),
        ("request_pause", OTHER_NOTICE),
        ("resume", NOTICE),
    ),
)
@pytest.mark.parametrize("guarded", (False, True))
def test_control_change_commits_once_and_preserves_unrelated_state(
    tmp_path: Path, operation: str, reason: Notice | None, guarded: bool
) -> None:
    store, before = seed(tmp_path / "state.json", operation)
    old_bytes = store.path.read_bytes()
    calls = []
    kwargs = {"publication_guard": lambda: calls.append("validated")} if guarded else {}
    after = invoke(StateService(store, **kwargs), operation, before["revision"], reason)
    assert after == store.read()
    assert after["revision"] == before["revision"] + 1
    assert after["control"]["pause_requested"] is (operation == "request_pause")
    if operation == "request_pause":
        assert after["control"]["pause_reason"] == reason
    else:
        assert after["control"]["pause_reason"] is None
    for key in before.keys() - {"revision", "control"}:
        assert after[key] == before[key]
    assert store.path.with_name("state.json.bak").read_bytes() == old_bytes
    assert bool(calls) is guarded


@pytest.mark.parametrize("operation", ("request_pause", "resume"))
@pytest.mark.parametrize("boundary", tuple(DurabilityBoundary))
@pytest.mark.parametrize(
    ("failure", "backup_exists"),
    (
        (RejectedOwner, True),
        (KeyboardInterrupt, True),
        (SystemExit, True),
        (RejectedOwner, False),
    ),
)
def test_guard_rejection_at_every_durable_boundary_restores_exact_bytes(
    tmp_path: Path,
    operation: str,
    boundary: DurabilityBoundary,
    failure: type[BaseException],
    backup_exists: bool,
) -> None:
    store, before = seed(
        tmp_path / "state.json", operation, backup_exists=backup_exists
    )
    original = durable_bytes(store.path)
    assert (original[1] is not None) is backup_exists
    reached = []

    def invalidate(observed: DurabilityBoundary) -> None:
        if observed == boundary:
            reached.append(observed)

    def guard() -> None:
        if reached:
            raise failure("owner changed")

    guarded = StateStore(store.path, boundary_hook=invalidate)
    with pytest.raises(failure, match="owner changed"):
        invoke(
            StateService(guarded, publication_guard=guard),
            operation,
            before["revision"],
        )
    assert reached == [boundary]
    assert durable_bytes(store.path) == original
    assert store.read() == before
    assert not tuple(tmp_path.glob(".state.json.ovcaq-*.tmp"))
    after = invoke(StateService(store), operation, before["revision"])
    assert after["revision"] == before["revision"] + 1


@pytest.mark.parametrize("operation", ("request_pause", "resume"))
def test_revision_conflict_preserves_bytes_and_allows_later_guarded_commit(
    tmp_path: Path, operation: str
) -> None:
    store, before = seed(tmp_path / "state.json", operation)
    original = durable_bytes(store.path)
    valid = True

    def guard() -> None:
        if not valid:
            raise RejectedOwner("owner changed after first commit")

    service = StateService(store, publication_guard=guard)
    with pytest.raises(RevisionConflictError):
        invoke(service, operation, before["revision"] - 1)
    assert durable_bytes(store.path) == original
    assert store.read() == before
    assert (
        invoke(service, operation, before["revision"])["revision"]
        == before["revision"] + 1
    )
    committed = store.read()
    committed_bytes = durable_bytes(store.path)
    valid = False
    second_operation = "resume" if operation == "request_pause" else "request_pause"
    with pytest.raises(RejectedOwner, match="owner changed after first commit"):
        invoke(service, second_operation, committed["revision"])
    assert durable_bytes(store.path) == committed_bytes
    assert store.read() == committed


@pytest.mark.parametrize("operation", ("request_pause", "resume"))
@pytest.mark.parametrize("idle", (False, True))
def test_rejecting_guard_prevents_mutation_without_cas_or_on_idle_batch(
    tmp_path: Path, operation: str, idle: bool
) -> None:
    if idle:
        initial = new_state(repo_root=tmp_path)
        initial["control"]["pause_requested"] = operation == "resume"
        initial["control"]["pause_reason"] = NOTICE if operation == "resume" else None
        store = StateStore(tmp_path / "state.json")
        before = store.initialize(initial)
        assert before["batch"]["status"] != "running"
    else:
        store, before = seed(tmp_path / "state.json", operation)
    original = durable_bytes(store.path)

    def reject() -> None:
        raise RejectedOwner("selected owner rejected")

    service = StateService(store, publication_guard=reject)
    with pytest.raises(RejectedOwner, match="selected owner rejected"):
        invoke(service, operation, before["revision"] if idle else None)
    assert durable_bytes(store.path) == original
    assert store.read() == before


@pytest.mark.parametrize("operation", ("request_pause", "resume"))
def test_guarded_control_result_matches_ordinary_service(
    tmp_path: Path, operation: str
) -> None:
    store, initial = seed(tmp_path / "guarded.json", operation)
    ordinary, _ = seed(tmp_path / "ordinary.json", operation)
    expected = invoke(StateService(ordinary), operation, initial["revision"])
    actual = invoke(
        StateService(store, publication_guard=lambda: None),
        operation,
        initial["revision"],
    )
    assert actual == expected
