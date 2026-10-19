from __future__ import annotations

import copy
import json
import multiprocessing
import os
import stat
import subprocess
import sys
from multiprocessing.connection import Connection
from pathlib import Path

import pytest
from test_durability import (
    _stop_worker,
    _wait_for_worker_line,
    _worker_environment,
)
from test_store import (
    _ORIGINAL_POPEN,
    _REVISION_RACE_OPERATION,
    MutatorFailure,
    _canonical_bytes,
    _directory_bytes,
    _file_with_bytes,
    _increment_counter_process,
    _invalid_state_bytes,
    _state_at_canonical_byte_limit,
    _stop_spawned_process,
)

from ovcaq.state.schema import (
    MAX_STATE_BYTES,
    SCHEMA_VERSION,
    SchemaError,
    State,
    new_state,
    validate_state,
)
from ovcaq.state.store import (
    BoundaryHook,
    DurabilityBoundary,
    FutureSchemaError,
    Mutator,
    RevisionConflictError,
    StateExistsError,
    StateIOError,
    StateStore,
)


def test_initialize_writes_canonical_private_state_and_returns_an_isolated_copy(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "runtime" / "state.json"
    state_path.parent.mkdir()
    state_path.parent.chmod(0o750)
    initial = new_state(repo_root=tmp_path)
    initial["work"]["extensions"] = {"tests/greeting": "Příliš žluťoučký"}
    expected_bytes = _canonical_bytes(initial)

    def accept_boundary(_boundary: object) -> None:
        return None

    boundary_hook: BoundaryHook = accept_boundary
    store = StateStore(state_path, boundary_hook=boundary_hook)
    initialized = store.initialize(initial)

    assert store.path == state_path
    assert initialized == initial
    assert initialized is not initial
    assert initialized["work"] is not initial["work"]
    assert state_path.read_bytes() == expected_bytes
    assert "Příliš žluťoučký".encode() in state_path.read_bytes()
    assert stat.S_IMODE(state_path.parent.stat().st_mode) == 0o750
    assert all(
        stat.S_IMODE(entry.stat().st_mode) == 0o600
        for entry in state_path.parent.iterdir()
        if entry.is_file()
    )

    initial["work"]["prd"] = "changed-input.md"
    initialized["work"]["prd"] = "changed-result.md"
    first_read = store.read()
    second_read = store.read()
    assert first_read["work"]["prd"] is None
    assert second_read == first_read
    assert second_read is not first_read
    assert second_read["work"] is not first_read["work"]


def test_initialize_publishes_the_exact_canonical_limit_and_rejects_one_byte_more(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    initial = _state_at_canonical_byte_limit(tmp_path, revision=0)

    assert validate_state(initial) == initial
    assert StateStore(state_path).initialize(initial) == initial
    assert state_path.read_bytes() == _canonical_bytes(initial)

    oversized_path = tmp_path / "oversized.json"
    oversized = _state_at_canonical_byte_limit(
        tmp_path,
        revision=0,
        extra_bytes=1,
    )
    assert len(json.dumps(oversized, ensure_ascii=False).encode("utf-8")) < (
        MAX_STATE_BYTES
    )
    with pytest.raises(SchemaError):
        validate_state(oversized)
    with pytest.raises(SchemaError):
        StateStore(oversized_path).initialize(oversized)
    assert not oversized_path.exists()


@pytest.mark.parametrize(
    "invalid_revision",
    (
        pytest.param(True, id="boolean"),
        pytest.param(-1, id="negative"),
        pytest.param(0.0, id="non-integer"),
    ),
)
def test_initialize_rejects_invalid_revision_without_publishing_it(
    tmp_path: Path,
    invalid_revision: object,
) -> None:
    state_path = tmp_path / "runtime" / "state.json"
    invalid = new_state(repo_root=tmp_path)
    invalid["revision"] = invalid_revision  # type: ignore[typeddict-item]

    with pytest.raises(SchemaError):
        StateStore(state_path).initialize(invalid)

    assert not state_path.exists()


def test_initialize_refuses_to_replace_an_existing_state_file(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    existing_bytes = b"existing bytes must survive\n"
    state_path.write_bytes(existing_bytes)

    with pytest.raises(StateExistsError):
        StateStore(state_path).initialize(new_state(repo_root=tmp_path))

    assert state_path.read_bytes() == existing_bytes


def test_read_rejects_a_semantically_invalid_state(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    invalid = new_state(repo_root=tmp_path)
    invalid["revision"] = True
    state_path.write_bytes(_canonical_bytes(invalid))

    with pytest.raises(SchemaError):
        StateStore(state_path).read()


def test_read_rejects_a_future_schema_version(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    future = new_state(repo_root=tmp_path)
    future["schema_version"] = SCHEMA_VERSION + 1
    state_path.write_bytes(_canonical_bytes(future))

    with pytest.raises(FutureSchemaError):
        StateStore(state_path).read()


def test_read_rejects_oversized_bytes_before_parsing(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    valid = _canonical_bytes(new_state(repo_root=tmp_path))
    state_path.write_bytes(b" " * (MAX_STATE_BYTES + 1) + valid)

    with pytest.raises(StateIOError):
        StateStore(state_path).read()


def test_transaction_calls_an_in_place_mutator_once_and_isolates_every_copy(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    store = StateStore(state_path)
    initialized = store.initialize(initial)
    candidates: list[State] = []

    def mutate(candidate: State) -> None:
        candidates.append(candidate)
        candidate["work"]["prd"] = "00003-store.md"

    mutator: Mutator = mutate
    committed = store.transaction(mutator, expected_revision=0)

    assert len(candidates) == 1
    assert candidates[0] is not initial
    assert candidates[0] is not initialized
    assert candidates[0]["work"] is not initial["work"]
    assert committed["revision"] == 1
    assert committed["work"]["prd"] == "00003-store.md"
    assert state_path.read_bytes() == _canonical_bytes(committed)

    candidates[0]["work"]["prd"] = "mutated-candidate.md"
    committed["work"]["prd"] = "mutated-result.md"
    reread = store.read()
    assert reread["revision"] == 1
    assert reread["work"]["prd"] == "00003-store.md"
    assert initial["revision"] == 0
    assert initial["work"]["prd"] is None


def test_transaction_uses_a_returned_replacement_and_assigns_the_next_revision(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    replacements: list[State] = []

    def replace(candidate: State) -> State:
        candidate["work"]["prd"] = "discarded.md"
        replacement = copy.deepcopy(candidate)
        replacement["revision"] = 99
        replacement["work"]["prd"] = "replacement.md"
        replacements.append(replacement)
        return replacement

    committed = store.transaction(replace)

    assert committed["revision"] == 1
    assert committed["work"]["prd"] == "replacement.md"
    replacements[0]["work"]["prd"] = "changed-after-return.md"
    assert store.read() == committed


@pytest.mark.parametrize(
    "invalid_revision",
    (
        pytest.param(True, id="boolean"),
        pytest.param(-1, id="negative"),
        pytest.param(0.0, id="non-integer"),
    ),
)
@pytest.mark.parametrize(
    "return_replacement",
    (
        pytest.param(False, id="in-place"),
        pytest.param(True, id="replacement"),
    ),
)
def test_transaction_ignores_schema_invalid_mutator_revisions_before_validation(
    tmp_path: Path,
    invalid_revision: object,
    return_replacement: bool,
) -> None:
    state_path = tmp_path / "state.json"
    backup_path = tmp_path / "state.json.bak"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    current = store.transaction(lambda _state: None)
    current_bytes = state_path.read_bytes()

    def propose_invalid_revision(candidate: State) -> State | None:
        candidate["revision"] = invalid_revision  # type: ignore[typeddict-item]
        candidate["work"]["prd"] = "store-owned-revision.md"
        return copy.deepcopy(candidate) if return_replacement else None

    committed = store.transaction(
        propose_invalid_revision,
        expected_revision=current["revision"],
    )

    assert committed["revision"] == current["revision"] + 1
    assert committed["work"]["prd"] == "store-owned-revision.md"
    assert state_path.read_bytes() == _canonical_bytes(committed)
    assert backup_path.read_bytes() == current_bytes
    assert store.read() == committed


def test_transaction_publishes_the_exact_canonical_limit_and_rejects_one_byte_more(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    replacement = _state_at_canonical_byte_limit(tmp_path, revision=1)

    assert validate_state(replacement) == replacement
    committed = store.transaction(lambda _candidate: replacement)

    assert committed == replacement
    assert state_path.read_bytes() == _canonical_bytes(replacement)

    oversized = _state_at_canonical_byte_limit(
        tmp_path,
        revision=2,
        extra_bytes=1,
    )
    with pytest.raises(SchemaError):
        validate_state(oversized)
    before = _directory_bytes(tmp_path)
    with pytest.raises(SchemaError):
        store.transaction(lambda _candidate: oversized, expected_revision=1)
    assert _directory_bytes(tmp_path) == before


def test_successful_transactions_and_restore_each_advance_revision_once(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    initialized = store.initialize(new_state(repo_root=tmp_path))

    def supply_revision(candidate: State, revision: int) -> None:
        candidate["revision"] = revision

    first = store.transaction(lambda candidate: supply_revision(candidate, 99))
    second = store.transaction(
        lambda candidate: supply_revision(candidate, 0),
        expected_revision=1,
    )
    restored = store.restore(expected_revision=2)

    assert initialized["revision"] == 0
    assert first["revision"] == 1
    assert second["revision"] == 2
    assert restored["revision"] == 3
    assert store.read() == restored
    assert _file_with_bytes(state_path, _canonical_bytes(second)).read_bytes() == (
        _canonical_bytes(second)
    )


def test_initialize_transaction_and_restore_support_a_nondefault_state_basename(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "session.json"
    backup_path = tmp_path / "session.json.bak"
    initial = new_state(repo_root=tmp_path)
    raw_initial = json.dumps(initial, ensure_ascii=False).encode("utf-8")
    store = StateStore(state_path)

    assert store.initialize(initial) == initial
    assert state_path.read_bytes() == _canonical_bytes(initial)
    assert store.read() == initial
    state_path.write_bytes(raw_initial)

    def mutate(candidate: State) -> None:
        candidate["work"]["prd"] = "nondefault-basename.md"

    committed = store.transaction(mutate, expected_revision=0)
    assert backup_path.read_bytes() == raw_initial
    assert state_path.read_bytes() == _canonical_bytes(committed)
    assert store.read() == committed

    raw_current = json.dumps(committed, ensure_ascii=False).encode("utf-8")
    state_path.write_bytes(raw_current)
    restored = store.restore(expected_revision=1)
    expected = copy.deepcopy(initial)
    expected["revision"] = 2

    assert restored == expected
    assert state_path.read_bytes() == _canonical_bytes(expected)
    assert store.read() == expected
    assert backup_path.read_bytes() == raw_current


@pytest.mark.parametrize(
    ("failure", "error_type"),
    (
        pytest.param("raises", MutatorFailure, id="mutator-exception"),
        pytest.param("invalid-result", SchemaError, id="invalid-result"),
    ),
)
def test_failed_mutations_leave_state_and_backup_bytes_unchanged(
    tmp_path: Path,
    failure: str,
    error_type: type[Exception],
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    store.transaction(lambda _state: None)
    before = _directory_bytes(tmp_path)
    calls = 0

    def fail(candidate: State) -> State | None:
        nonlocal calls
        calls += 1
        candidate["work"]["prd"] = "must-not-persist.md"
        if failure == "raises":
            raise MutatorFailure("mutator failed")
        candidate["work"]["phase"] = "invalid"  # type: ignore[typeddict-item]
        return candidate

    with pytest.raises(error_type):
        store.transaction(fail, expected_revision=1)

    assert calls == 1
    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize(
    ("invalid_kind", "error_type"),
    (
        pytest.param("missing", StateIOError, id="missing"),
        pytest.param("malformed-json", StateIOError, id="malformed-json"),
        pytest.param("non-object", SchemaError, id="non-object"),
        pytest.param("future-schema", FutureSchemaError, id="future-schema"),
        pytest.param("schema-invalid", SchemaError, id="schema-invalid"),
    ),
)
def test_transaction_validates_current_before_mutator_and_preserves_backup_bytes(
    tmp_path: Path,
    invalid_kind: str,
    error_type: type[Exception],
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    store.transaction(lambda _state: None)
    invalid_raw = _invalid_state_bytes(invalid_kind, tmp_path)
    if invalid_raw is None:
        state_path.unlink()
    else:
        state_path.write_bytes(invalid_raw)
    before = _directory_bytes(tmp_path)
    calls = 0

    def mutate(_candidate: State) -> None:
        nonlocal calls
        calls += 1

    with pytest.raises(error_type):
        store.transaction(mutate)

    assert calls == 0
    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize(
    ("setup_transactions", "expected_revision"),
    (
        pytest.param(1, 0, id="stale"),
        pytest.param(1, 2, id="future"),
        pytest.param(0, False, id="boolean-false-equals-zero"),
        pytest.param(1, True, id="boolean-true-equals-one"),
        pytest.param(0, -1, id="negative"),
    ),
)
def test_transaction_rejects_conflicting_and_invalid_revisions_before_mutation(
    tmp_path: Path,
    setup_transactions: int,
    expected_revision: int,
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    for _ in range(setup_transactions):
        store.transaction(lambda _state: None)
    before = _directory_bytes(tmp_path)
    calls = 0

    def mutate(_candidate: State) -> None:
        nonlocal calls
        calls += 1

    with pytest.raises(RevisionConflictError):
        store.transaction(mutate, expected_revision=expected_revision)

    assert calls == 0
    assert _directory_bytes(tmp_path) == before


def _start_revision_race_workers(
    tmp_path: Path,
    state_path: Path,
    gate: Path,
    labels: tuple[str, ...],
    markers: tuple[Path, ...],
) -> list[subprocess.Popen[str]]:
    return [
        _ORIGINAL_POPEN(
            [
                sys.executable,
                "-c",
                _REVISION_RACE_OPERATION,
                str(state_path),
                str(gate),
                str(marker),
                label,
            ],
            cwd=tmp_path,
            env=_worker_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        for label, marker in zip(labels, markers, strict=True)
    ]


def _collect_revision_race_outcomes(
    processes: list[subprocess.Popen[str]],
    gate: Path,
) -> list[dict[str, object]]:
    try:
        for process in processes:
            _wait_for_worker_line(process, "ready\n")
        gate.touch()
        outcomes = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0, stderr
            outcomes.append(json.loads(stdout))
        return outcomes
    finally:
        for process in processes:
            _stop_worker(process)


def test_concurrent_same_revision_compare_and_set_commits_exactly_once(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    StateStore(state_path).initialize(initial)
    gate = tmp_path / "start-revision-race"
    labels = ("first", "second")
    markers = tuple(tmp_path / f"{label}-mutator-called" for label in labels)
    processes = _start_revision_race_workers(
        tmp_path, state_path, gate, labels, markers
    )
    outcomes = _collect_revision_race_outcomes(processes, gate)

    successes = [outcome for outcome in outcomes if outcome["result"] == "success"]
    conflicts = [outcome for outcome in outcomes if outcome["result"] == "conflict"]
    assert len(successes) == 1
    assert len(conflicts) == 1
    assert sum(marker.exists() for marker in markers) == 1

    committed = successes[0]["state"]
    assert isinstance(committed, dict)
    assert committed["revision"] == 1
    assert StateStore(state_path).read() == committed
    assert committed["work"]["prd"] in {f"{label}.md" for label in labels}
    assert _file_with_bytes(state_path, _canonical_bytes(initial)).read_bytes() == (
        _canonical_bytes(initial)
    )


def _start_counter_workers(
    state_path: Path,
) -> tuple[list[multiprocessing.Process], list[Connection], list[Connection]]:
    context = multiprocessing.get_context("spawn")
    processes: list[multiprocessing.Process] = []
    parent_connections: list[Connection] = []
    child_connections: list[Connection] = []
    for _ in range(2):
        parent, child = context.Pipe(duplex=True)
        parent_connections.append(parent)
        child_connections.append(child)
        process = context.Process(
            target=_increment_counter_process,
            args=(os.fspath(state_path), child),
        )
        process.start()
        processes.append(process)
        child.close()
    return processes, parent_connections, child_connections


def _collect_counter_states(
    processes: list[multiprocessing.Process],
    connections: list[Connection],
) -> list[State]:
    for process, connection in zip(processes, connections, strict=True):
        assert connection.poll(5), f"counter worker stalled: {process.exitcode=}"
        assert connection.recv() == "ready"
    for connection in connections:
        connection.send("start")
    committed_states = []
    for process, connection in zip(processes, connections, strict=True):
        assert connection.poll(10), f"counter worker stalled: {process.exitcode=}"
        status, committed = connection.recv()
        assert status == "done"
        committed_states.append(committed)
        process.join(timeout=5)
        assert not process.is_alive()
        assert process.exitcode == 0
    return committed_states


def _close_counter_workers(
    processes: list[multiprocessing.Process],
    parent_connections: list[Connection],
    child_connections: list[Connection],
) -> None:
    for connection in (*parent_connections, *child_connections):
        connection.close()
    for process in processes:
        _stop_spawned_process(process)


def test_two_concurrent_writers_both_increment_the_extension_counter(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    initial["work"]["extensions"] = {"tests/counter": 0}
    StateStore(state_path).initialize(initial)
    processes, parent_connections, child_connections = _start_counter_workers(
        state_path
    )

    try:
        committed_states = _collect_counter_states(processes, parent_connections)
    finally:
        _close_counter_workers(processes, parent_connections, child_connections)

    final = StateStore(state_path).read()
    assert final["revision"] == 2
    assert final["work"]["extensions"]["tests/counter"] == 2
    assert {state["revision"] for state in committed_states} == {1, 2}
    assert {
        state["work"]["extensions"]["tests/counter"] for state in committed_states
    } == {1, 2}


def test_transaction_preserves_raw_pre_transaction_bytes_as_the_backup(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    store = StateStore(state_path)
    store.initialize(initial)
    raw_current = json.dumps(initial, ensure_ascii=False).encode("utf-8")
    state_path.write_bytes(raw_current)

    committed = store.transaction(lambda _state: None)

    backup_path = state_path.with_name("state.json.bak")
    assert backup_path.read_bytes() == raw_current
    assert state_path.read_bytes() == _canonical_bytes(committed)
    assert all(
        stat.S_IMODE(entry.stat().st_mode) == 0o600
        for entry in state_path.parent.iterdir()
        if entry.is_file()
    )


@pytest.mark.parametrize(
    "failure_boundary",
    (
        DurabilityBoundary.BACKUP_REPLACED,
        DurabilityBoundary.BACKUP_DIR_FSYNCED,
        DurabilityBoundary.STATE_TEMP_FSYNCED,
        DurabilityBoundary.STATE_REPLACED,
        DurabilityBoundary.STATE_DIR_FSYNCED,
    ),
)
@pytest.mark.parametrize(
    "old_backup_exists",
    (
        pytest.param(False, id="old-backup-absent"),
        pytest.param(True, id="old-backup-present"),
    ),
)
def test_transaction_failure_after_backup_publication_repairs_exact_bytes(
    tmp_path: Path,
    failure_boundary: DurabilityBoundary,
    old_backup_exists: bool,
) -> None:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    store = StateStore(state_path)
    store.initialize(initial)
    backup_path = state_path.with_name("state.json.bak")
    current = initial
    if old_backup_exists:
        current = store.transaction(lambda state: state)
        backup_path.write_bytes(b"opaque old backup bytes\x00\n")
    state_path.write_bytes(json.dumps(current, ensure_ascii=False).encode("utf-8"))
    before = _directory_bytes(tmp_path)

    def fail_after_publication(boundary: DurabilityBoundary) -> None:
        if boundary is failure_boundary:
            raise MutatorFailure(f"failed at {boundary.value}")

    failing_store = StateStore(state_path, boundary_hook=fail_after_publication)

    with pytest.raises(MutatorFailure, match=failure_boundary.value):
        failing_store.transaction(
            lambda _state: None,
            expected_revision=current["revision"],
        )

    assert _directory_bytes(tmp_path) == before
    assert not tuple(tmp_path.glob(".state.json.ovcaq-*.tmp"))


@pytest.mark.parametrize(
    "failure_boundary",
    (
        DurabilityBoundary.BACKUP_REPLACED,
        DurabilityBoundary.BACKUP_DIR_FSYNCED,
        DurabilityBoundary.STATE_TEMP_FSYNCED,
        DurabilityBoundary.STATE_REPLACED,
        DurabilityBoundary.STATE_DIR_FSYNCED,
    ),
)
def test_restore_failure_after_backup_publication_repairs_exact_bytes(
    tmp_path: Path,
    failure_boundary: DurabilityBoundary,
) -> None:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    store = StateStore(state_path)
    store.initialize(initial)

    def mutate(candidate: State) -> None:
        candidate["work"]["prd"] = "current.md"

    current = store.transaction(mutate)
    backup_path = state_path.with_name("state.json.bak")
    state_path.write_bytes(json.dumps(current, ensure_ascii=False).encode("utf-8"))
    backup_path.write_bytes(json.dumps(initial, ensure_ascii=False).encode("utf-8"))
    before = _directory_bytes(tmp_path)

    def fail_after_publication(boundary: DurabilityBoundary) -> None:
        if boundary is failure_boundary:
            raise MutatorFailure(f"failed at {boundary.value}")

    failing_store = StateStore(state_path, boundary_hook=fail_after_publication)

    with pytest.raises(MutatorFailure, match=failure_boundary.value):
        failing_store.restore(expected_revision=1)

    assert _directory_bytes(tmp_path) == before
    assert not tuple(tmp_path.glob(".state.json.ovcaq-*.tmp"))


@pytest.mark.parametrize("operation", ("transaction", "restore"))
@pytest.mark.parametrize("failure_boundary", tuple(DurabilityBoundary))
def test_keyboard_interrupt_repairs_locked_publication_before_reraising(
    tmp_path: Path,
    operation: str,
    failure_boundary: DurabilityBoundary,
) -> None:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    store = StateStore(state_path)
    store.initialize(initial)

    def mutate(candidate: State) -> None:
        candidate["work"]["prd"] = "current.md"

    current = store.transaction(mutate)
    backup_path = state_path.with_name("state.json.bak")
    state_path.write_bytes(json.dumps(current, ensure_ascii=False).encode("utf-8"))
    backup_path.write_bytes(json.dumps(initial, ensure_ascii=False).encode("utf-8"))
    before = _directory_bytes(tmp_path)

    def interrupt(boundary: DurabilityBoundary) -> None:
        if boundary is failure_boundary:
            raise KeyboardInterrupt

    interrupted_store = StateStore(state_path, boundary_hook=interrupt)

    with pytest.raises(KeyboardInterrupt):
        if operation == "transaction":
            interrupted_store.transaction(lambda _state: None, expected_revision=1)
        else:
            interrupted_store.restore(expected_revision=1)

    assert _directory_bytes(tmp_path) == before
    assert not tuple(tmp_path.glob(".state.json.ovcaq-*.tmp"))
