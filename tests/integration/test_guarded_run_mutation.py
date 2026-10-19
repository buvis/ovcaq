from __future__ import annotations

import json
import os
import select
import stat
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from test_guarded_service import NOTICE, RejectedOwner, durable_bytes, invoke, seed

from ovcaq.runtime.registry import (
    FleetEntry,
    FleetRegistry,
    ProcessIdentity,
    process_identity,
    process_matches,
)
from ovcaq.state.commands import StateService
from ovcaq.state.store import DurabilityBoundary, StateStore

_OWNER = """
import sys
from pathlib import Path
from ovcaq.runtime.registry import RunLock
lock = RunLock.acquire(Path(sys.argv[1]))
print('owned', flush=True)
sys.stdin.readline()
lock.close()
"""

_PUBLISHER = """
import json
import os
import sys
from pathlib import Path
from ovcaq.runtime.registry import FleetEntry, FleetRegistry, RunLock, process_identity
from ovcaq.state.store import StateStore
registry = FleetRegistry(Path(sys.argv[1]))
identity = process_identity(os.getpid())
entry = FleetEntry(1, Path(sys.argv[3]), identity.pid, identity.started,
                   'selected', 'local', '2026-08-26T10:00:00Z')
print('ready', flush=True)
sys.stdin.readline()
lock = RunLock.acquire(Path(sys.argv[2]))
print('attempting', flush=True)
if sys.argv[5] == 'remove':
    registry.remove('selected')
else:
    registry.publish(entry)
print('mutation-complete', flush=True)
print(json.dumps(StateStore(Path(sys.argv[4])).read()), flush=True)
sys.stdin.readline()
lock.close()
"""


@contextmanager
def child(code: str, *arguments: Path | str) -> Iterator[subprocess.Popen[str]]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(os.path.abspath(p) for p in sys.path)
    worker = subprocess.Popen(
        [sys.executable, "-c", code, *map(str, arguments)],
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        yield worker
    finally:
        if worker.poll() is None:
            worker.kill()
        worker.communicate(timeout=5)


def line(worker: subprocess.Popen[str]) -> str:
    assert worker.stdout is not None
    deadline = time.monotonic() + 5
    received = bytearray()
    while not received.endswith(b"\n"):
        remaining = deadline - time.monotonic()
        assert remaining > 0, "child failed to reach its observable barrier"
        ready, _, _ = select.select([worker.stdout], [], [], remaining)
        assert ready, "child failed to reach its observable barrier"
        part = os.read(worker.stdout.fileno(), 1)
        assert part, f"child exited unexpectedly: {worker.poll()}"
        received.extend(part)
    return received.decode().strip()


def send(worker: subprocess.Popen[str]) -> None:
    assert worker.stdin is not None
    worker.stdin.write("continue\n")
    worker.stdin.flush()


def entry_for(owner: subprocess.Popen[str], root: Path) -> FleetEntry:
    identity = process_identity(owner.pid)
    assert identity is not None
    return FleetEntry(
        1,
        root,
        identity.pid,
        identity.started,
        "selected",
        "local",
        NOTICE["created_at"],
    )


def validate_owner(registry: FleetRegistry, selected: FleetEntry) -> None:
    identity = ProcessIdentity(selected.pid, selected.process_start)
    if not process_matches(identity) or selected not in registry.snapshot().live:
        raise RejectedOwner("selected owner no longer owns this run")


def assert_blocked(worker: subprocess.Popen[str]) -> None:
    assert worker.stdout is not None
    ready, _, _ = select.select([worker.stdout], [], [], 0.2)
    assert not ready, "ownership publication overtook the guarded mutation"
    assert worker.poll() is None


def exit_owner(owner: subprocess.Popen[str], selected: FleetEntry) -> None:
    send(owner)
    assert owner.wait(timeout=5) == 0
    assert not process_matches(ProcessIdentity(selected.pid, selected.process_start))


def assert_replacement(registry: FleetRegistry, pid: int, selected: FleetEntry) -> None:
    (replacement_entry,) = registry.snapshot().live
    assert replacement_entry.pid == pid
    assert replacement_entry != selected


@pytest.mark.parametrize("operation", ("request_pause", "resume"))
@pytest.mark.parametrize("boundary", tuple(DurabilityBoundary))
def test_owner_exit_during_publication_rolls_back_before_replacement_reads(
    tmp_path: Path, operation: str, boundary: DurabilityBoundary
) -> None:
    store, before = seed(tmp_path / "state.json", operation)
    original = durable_bytes(store.path)
    registry = FleetRegistry(tmp_path / "fleet")
    with child(_OWNER, tmp_path / "run.lock") as owner:
        assert line(owner) == "owned"
        selected = entry_for(owner, tmp_path)
        registry.publish(selected)
        with child(
            _PUBLISHER,
            tmp_path / "fleet",
            tmp_path / "run.lock",
            tmp_path,
            store.path,
            "publish",
        ) as replacement:
            assert line(replacement) == "ready"
            reached = []

            def invalidate(observed: DurabilityBoundary) -> None:
                if observed == boundary:
                    reached.append(observed)
                    exit_owner(owner, selected)
                    send(replacement)
                    assert line(replacement) == "attempting"
                    assert_blocked(replacement)

            guarded_store = StateStore(store.path, boundary_hook=invalidate)
            with (
                pytest.raises(RejectedOwner, match="selected owner"),
                registry.guard_mutation(
                    lambda: validate_owner(registry, selected)
                ) as guard,
            ):
                invoke(
                    StateService(guarded_store, publication_guard=guard),
                    operation,
                    before["revision"],
                )
            assert reached == [boundary]
            assert line(replacement) == "mutation-complete"
            assert json.loads(line(replacement)) == before
            assert durable_bytes(store.path) == original
            assert store.read() == before
            assert_replacement(registry, replacement.pid, selected)
            send(replacement)
            assert replacement.wait(timeout=5) == 0


@pytest.mark.parametrize("operation", ("request_pause", "resume"))
def test_live_selected_owner_commits_control_once(
    tmp_path: Path, operation: str
) -> None:
    store, before = seed(tmp_path / "state.json", operation)
    registry = FleetRegistry(tmp_path / "fleet")
    with child(_OWNER, tmp_path / "run.lock") as owner:
        assert line(owner) == "owned"
        selected = entry_for(owner, tmp_path)
        registry.publish(selected)
        with registry.guard_mutation(
            lambda: validate_owner(registry, selected)
        ) as guard:
            result = invoke(
                StateService(store, publication_guard=guard),
                operation,
                before["revision"],
            )
        assert result == store.read()
        assert result["revision"] == before["revision"] + 1
        assert result["control"]["pause_requested"] is (operation == "request_pause")
        for key in before.keys() - {"control", "revision"}:
            assert result[key] == before[key]
        assert registry.snapshot().live == (selected,)


@pytest.mark.parametrize("mutation", ("publish", "remove"))
@pytest.mark.parametrize("failure", (False, True))
def test_ownership_mutation_waits_and_is_released_on_context_exit(
    tmp_path: Path, mutation: str, failure: bool
) -> None:
    store, before = seed(tmp_path / "state.json", "request_pause")
    registry = FleetRegistry(tmp_path / "fleet")
    with child(_OWNER, tmp_path / "run.lock") as owner:
        assert line(owner) == "owned"
        selected = entry_for(owner, tmp_path)
        registry.publish(selected)
        with child(
            _PUBLISHER,
            tmp_path / "fleet",
            tmp_path / "other.lock",
            tmp_path,
            store.path,
            mutation,
        ) as replacement:
            assert line(replacement) == "ready"
            try:
                with registry.guard_mutation(
                    lambda: validate_owner(registry, selected)
                ):
                    send(replacement)
                    assert line(replacement) == "attempting"
                    assert_blocked(replacement)
                    if failure:
                        raise RejectedOwner("context failed")
            except RejectedOwner as error:
                assert failure and str(error) == "context failed"
            assert line(replacement) == "mutation-complete"
            assert json.loads(line(replacement)) == before
            live = registry.snapshot().live
            assert not live if mutation == "remove" else live[0].pid == replacement.pid
            send(replacement)
            assert replacement.wait(timeout=5) == 0


@pytest.mark.parametrize("operation", ("request_pause", "resume"))
def test_stale_selection_cannot_change_replacement_state(
    tmp_path: Path, operation: str
) -> None:
    store, before = seed(tmp_path / "state.json", operation)
    original = durable_bytes(store.path)
    registry = FleetRegistry(tmp_path / "fleet")
    with child(_OWNER, tmp_path / "run.lock") as owner:
        assert line(owner) == "owned"
        selected = entry_for(owner, tmp_path)
        registry.publish(selected)
        send(owner)
        assert owner.wait(timeout=5) == 0
        with child(
            _PUBLISHER,
            tmp_path / "fleet",
            tmp_path / "run.lock",
            tmp_path,
            store.path,
            "publish",
        ) as replacement:
            assert line(replacement) == "ready"
            send(replacement)
            assert line(replacement) == "attempting"
            assert line(replacement) == "mutation-complete"
            assert json.loads(line(replacement)) == before
            with (
                pytest.raises(RejectedOwner, match="selected owner"),
                registry.guard_mutation(
                    lambda: validate_owner(registry, selected)
                ) as guard,
            ):
                invoke(
                    StateService(store, publication_guard=guard),
                    operation,
                    before["revision"],
                )
            assert durable_bytes(store.path) == original
            assert registry.snapshot().live[0].pid == replacement.pid


def test_guard_rejects_symlinked_registry_lock_without_touching_target(
    tmp_path: Path,
) -> None:
    registry = FleetRegistry(tmp_path / "fleet")
    with child(_OWNER, tmp_path / "run.lock") as owner:
        assert line(owner) == "owned"
        selected = entry_for(owner, tmp_path)
        record = registry.publish(selected)
        encoded = record.read_bytes()
        lock_path = tmp_path / "fleet" / "fleet.lock"
        lock_path.rename(tmp_path / "original.lock")
        target = tmp_path / "outside.lock"
        target.write_bytes(b"outside bytes\n")
        target.chmod(0o644)
        original = target.stat()
        lock_path.symlink_to(target)
        with (
            pytest.raises(OSError),
            registry.guard_mutation(lambda: validate_owner(registry, selected)),
        ):
            pytest.fail("guard accepted an untrusted registry lock")
        assert record.read_bytes() == encoded
        assert lock_path.is_symlink()
        assert target.read_bytes() == b"outside bytes\n"
        assert os.path.samestat(target.stat(), original)
        assert stat.S_IMODE(target.stat().st_mode) == 0o644


def test_guard_rejects_replaced_lock_at_last_boundary_and_rolls_back(
    tmp_path: Path,
) -> None:
    registry = FleetRegistry(tmp_path / "fleet")
    store, before = seed(tmp_path / "state.json", "request_pause")
    original = durable_bytes(store.path)
    with child(_OWNER, tmp_path / "run.lock") as owner:
        assert line(owner) == "owned"
        selected = entry_for(owner, tmp_path)
        record = registry.publish(selected)
        encoded = record.read_bytes()
        lock_path = tmp_path / "fleet" / "fleet.lock"
        reached = []

        def substitute(boundary: DurabilityBoundary) -> None:
            if boundary == DurabilityBoundary.STATE_DIR_FSYNCED:
                reached.append(boundary)
                lock_path.rename(tmp_path / "original.lock")
                lock_path.write_bytes(b"replacement lock\n")

        guarded = StateStore(store.path, boundary_hook=substitute)
        with (
            pytest.raises(ValueError),
            registry.guard_mutation(
                lambda: validate_owner(registry, selected)
            ) as guard,
        ):
            invoke(
                StateService(guarded, publication_guard=guard),
                "request_pause",
                before["revision"],
            )
        assert reached == [DurabilityBoundary.STATE_DIR_FSYNCED]
        assert durable_bytes(store.path) == original
        assert record.read_bytes() == encoded
        assert lock_path.read_bytes() == b"replacement lock\n"
