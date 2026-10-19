from __future__ import annotations

import copy
import json
import os
import select
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from ovcaq.cli import main
from ovcaq.config import supervisor_settings
from ovcaq.runtime.registry import (
    FleetEntry,
    FleetRegistry,
    FleetRun,
    ProcessIdentity,
    process_identity,
    process_matches,
    run_lock_held,
)
from ovcaq.runtime.session import SessionMetadata, publish_run_metadata
from ovcaq.state.store import DurabilityBoundary, RevisionConflictError, StateStore
from ovcaq.supervisor_cli import stop_supervisor
from ovcaq.tui.app import AttachResult, RunControlService, StaleSelectionError
from ovcaq.tui.discovery import discover_fleet

_OWNER = """
import sys
from pathlib import Path
from ovcaq.runtime.registry import RunLock
lock = RunLock.acquire(Path(sys.argv[1]))
print('ready', flush=True)
command = sys.stdin.readline().strip()
lock.close()
if command == 'release':
    print('released', flush=True)
    sys.stdin.readline()
"""

_REPLACEMENT = """
import json
import os
import sys
from pathlib import Path
from ovcaq.config import supervisor_settings
from ovcaq.runtime.registry import FleetEntry, FleetRegistry, RunLock, process_identity
from ovcaq.runtime.session import SessionMetadata, publish_run_metadata
from ovcaq.state.store import StateStore
root = Path(sys.argv[1])
paths = supervisor_settings(root).runtime.paths
registry = FleetRegistry(Path(sys.argv[2]))
identity = process_identity(os.getpid())
print('ready', flush=True)
sys.stdin.readline()
lock = RunLock.acquire(paths.run_lock)
print('attempting', flush=True)
entry = FleetEntry(1, root, identity.pid, identity.started,
                   'selected', 'generic', '2026-10-03T12:00:00Z')
registry.publish(entry)
publish_run_metadata(paths, SessionMetadata(1, entry.run_id, 'supervisor',
    entry.agent, entry.pid, entry.process_start, entry.started_at))
print('mutation-complete', flush=True)
print(json.dumps(StateStore(paths.state_file).read()), flush=True)
sys.stdin.readline()
lock.close()
"""


@contextmanager
def _child(code: str, *args: Path | str) -> Iterator[subprocess.Popen[str]]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(os.path.abspath(p) for p in sys.path)
    worker = subprocess.Popen(
        [sys.executable, "-c", code, *map(str, args)],
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


def _line(worker: subprocess.Popen[str]) -> str:
    assert worker.stdout is not None
    deadline = time.monotonic() + 5
    received = bytearray()
    while not received.endswith(b"\n"):
        remaining = deadline - time.monotonic()
        assert remaining > 0, "child did not reach its observable barrier"
        ready, _, _ = select.select([worker.stdout], [], [], remaining)
        assert ready, "child did not reach its observable barrier"
        part = os.read(worker.stdout.fileno(), 1)
        assert part, f"child exited unexpectedly: {worker.poll()}"
        received.extend(part)
    return received.decode().strip()


def _send(worker: subprocess.Popen[str], command: str = "continue") -> None:
    assert worker.stdin is not None
    worker.stdin.write(command + "\n")
    worker.stdin.flush()


def _bytes(path: Path) -> tuple[bytes, bytes | None]:
    backup = path.with_name(path.name + ".bak")
    return path.read_bytes(), backup.read_bytes() if backup.exists() else None


@dataclass
class Owner:
    run: FleetRun
    entry: FleetEntry
    metadata: SessionMetadata
    paths: Any
    process: subprocess.Popen[str]


@dataclass
class Fleet:
    selected: Owner
    other: Owner
    registry: FleetRegistry
    registry_root: Path


def _owner(stack: ExitStack, root: Path, name: str, registry: FleetRegistry) -> Owner:
    root.mkdir()
    assert main(["--root", str(root), "--json", "init"]) == 0
    paths = supervisor_settings(root).runtime.paths
    worker = stack.enter_context(_child(_OWNER, paths.run_lock))
    assert _line(worker) == "ready"
    identity = process_identity(worker.pid)
    assert identity is not None
    agent = "generic" if name == "selected" else "local"
    started_at = (
        "2026-10-03T12:00:00Z" if name == "selected" else "2026-10-03T11:00:00Z"
    )
    entry = FleetEntry(
        1,
        root,
        identity.pid,
        identity.started,
        name,
        agent,
        started_at,
    )
    run = FleetRun(
        name, root, entry.agent, entry.started_at, entry.pid, entry.process_start
    )
    metadata = SessionMetadata(
        1,
        name,
        "supervisor",
        run.agent,
        run.pid,
        run.process_start,
        run.started_at,
    )
    publish_run_metadata(paths, metadata)
    registry.publish(entry)
    StateStore(paths.state_file).transaction(lambda state: None)
    return Owner(run, entry, metadata, paths, worker)


@pytest.fixture
def fleet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    request: pytest.FixtureRequest,
) -> Iterator[Fleet]:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg-state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    default = supervisor_settings(tmp_path).runtime.paths.fleet_root
    registry_root = (
        tmp_path / "private-fleet" if getattr(request, "param", False) else default
    )
    registry = FleetRegistry(registry_root)
    with ExitStack() as stack:
        selected = _owner(stack, tmp_path / "selected", "selected", registry)
        other = _owner(stack, tmp_path / "unrelated", "unrelated", registry)
        capsys.readouterr()
        yield Fleet(selected, other, registry, registry_root)


def _hook(
    monkeypatch: pytest.MonkeyPatch, callback: Callable[[DurabilityBoundary], None]
) -> None:
    original = StateStore.__init__

    def initialize(self: StateStore, path: Path, **kwargs: Any) -> None:
        original(self, path, boundary_hook=callback, **kwargs)

    monkeypatch.setattr(StateStore, "__init__", initialize)


def _assert_other(fleet: Fleet, original: tuple[bytes, bytes | None]) -> None:
    assert _bytes(fleet.other.paths.state_file) == original
    assert fleet.other.entry in fleet.registry.snapshot().live
    assert process_matches(
        ProcessIdentity(fleet.other.run.pid, fleet.other.run.process_start)
    )
    assert fleet.other.process.poll() is None


def _assert_only_control(
    before: Any, after: Any, paused: bool, reason: str | None = "maintenance"
) -> None:
    expected = copy.deepcopy(before)
    expected["revision"] += 1
    expected["control"]["pause_requested"] = paused
    expected["control"]["pause_reason"] = (
        after["control"]["pause_reason"] if paused else None
    )
    assert after == expected
    if paused and reason is not None:
        assert after["control"]["pause_reason"]["site"] == "operator"
        assert after["control"]["pause_reason"]["detail"] == reason
    else:
        assert after["control"]["pause_reason"] is None


@pytest.mark.parametrize("reason", ["maintenance", "inspect queue 42", None])
def test_control_commit_pause_resume_targets_only_selected_identity(
    fleet: Fleet, reason: str | None
) -> None:
    selected = fleet.selected
    controls = RunControlService(fleet.registry)
    store = StateStore(selected.paths.state_file)
    original_other = _bytes(fleet.other.paths.state_file)
    before = store.read()
    controls.pause(selected.run, before["revision"], reason)
    paused = store.read()
    _assert_only_control(before, paused, True, reason)
    original = _bytes(store.path)
    with pytest.raises(RevisionConflictError):
        controls.pause(selected.run, before["revision"], "outdated action")
    assert _bytes(store.path) == original
    with pytest.raises(RevisionConflictError):
        controls.resume(selected.run, before["revision"])
    assert _bytes(store.path) == original
    controls.resume(selected.run, paused["revision"])
    _assert_only_control(paused, store.read(), False)
    original = _bytes(store.path)
    with pytest.raises(StaleSelectionError) as caught:
        controls.pause(
            replace(selected.run, process_start="not-selected"),
            store.read()["revision"],
        )
    assert caught.value.committed is False
    assert _bytes(store.path) == original
    _assert_other(fleet, original_other)


@pytest.mark.parametrize("action", ["pause", "resume"])
@pytest.mark.parametrize(
    "boundary",
    [DurabilityBoundary.BACKUP_REPLACED, DurabilityBoundary.STATE_DIR_FSYNCED],
)
def test_control_commit_owner_exit_rolls_back_before_replacement_reads(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    boundary: DurabilityBoundary,
) -> None:
    selected = fleet.selected
    controls = RunControlService(fleet.registry)
    store = StateStore(selected.paths.state_file)
    if action == "resume":
        controls.pause(selected.run, store.read()["revision"], "maintenance")
    before, original = store.read(), _bytes(store.path)
    original_other = _bytes(fleet.other.paths.state_file)
    reached: list[DurabilityBoundary] = []
    with _child(_REPLACEMENT, selected.run.root, fleet.registry_root) as replacement:
        assert _line(replacement) == "ready"

        def invalidate(observed: DurabilityBoundary) -> None:
            if observed != boundary or reached:
                return
            reached.append(observed)
            _send(selected.process)
            assert selected.process.wait(timeout=5) == 0
            _send(replacement)
            assert _line(replacement) == "attempting"
            assert replacement.stdout is not None
            ready, _, _ = select.select([replacement.stdout], [], [], 0.2)
            assert not ready, "replacement publication overtook the selected action"

        _hook(monkeypatch, invalidate)
        with pytest.raises(StaleSelectionError) as caught:
            getattr(controls, action)(selected.run, before["revision"])
        assert caught.value.committed is False
        assert reached == [boundary]
        assert _line(replacement) == "mutation-complete"
        assert json.loads(_line(replacement)) == before
        assert _bytes(store.path) == original
        assert store.read() == before
        assert any(
            entry.pid == replacement.pid for entry in fleet.registry.snapshot().live
        )
        _assert_other(fleet, original_other)
        _send(replacement)
        assert replacement.wait(timeout=5) == 0


@pytest.mark.parametrize("action", ["pause", "resume"])
def test_control_commit_last_boundary_identity_replacement_rolls_back(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    selected = fleet.selected
    controls = RunControlService(fleet.registry)
    store = StateStore(selected.paths.state_file)
    if action == "resume":
        controls.pause(selected.run, store.read()["revision"], "maintenance")
    before, original = store.read(), _bytes(store.path)
    original_other = _bytes(fleet.other.paths.state_file)
    reached: list[DurabilityBoundary] = []

    def invalidate(boundary: DurabilityBoundary) -> None:
        if boundary == DurabilityBoundary.STATE_DIR_FSYNCED and not reached:
            reached.append(boundary)
            publish_run_metadata(
                selected.paths, replace(selected.metadata, run_id="replacement")
            )

    _hook(monkeypatch, invalidate)
    with pytest.raises(StaleSelectionError) as caught:
        getattr(controls, action)(selected.run, before["revision"])
    assert caught.value.committed is False
    assert reached == [DurabilityBoundary.STATE_DIR_FSYNCED]
    assert _bytes(store.path) == original
    assert store.read() == before
    assert selected.process.poll() is None
    _assert_other(fleet, original_other)


def _terminal_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[list[dict[str, Any]], list[object]]:
    attachments: list[dict[str, Any]] = []
    launches: list[object] = []
    monkeypatch.setattr("ovcaq.cli.sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("ovcaq.cli.sys.stdout.isatty", lambda: True)

    def attach(**kwargs: Any) -> AttachResult:
        attachments.append(kwargs)
        return AttachResult("detached", 0)

    def launch(*args: Any, **kwargs: Any) -> None:
        launches.append((args, kwargs))
        pytest.fail("live resume must not launch a supervisor")

    monkeypatch.setattr("ovcaq.tui.app.attach", attach)
    monkeypatch.setattr("ovcaq.cli.launch_supervisor", launch)
    return attachments, launches


@pytest.mark.parametrize("stale", [False, True])
def test_control_commit_interactive_resume_preserves_exact_live_selection(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stale: bool,
) -> None:
    selected = fleet.selected
    store = StateStore(selected.paths.state_file)
    RunControlService(fleet.registry).pause(
        selected.run, store.read()["revision"], "maintenance"
    )
    before, original = store.read(), _bytes(store.path)
    original_other = _bytes(fleet.other.paths.state_file)
    attachments, launches = _terminal_boundaries(monkeypatch)
    reached: list[DurabilityBoundary] = []

    def invalidate(boundary: DurabilityBoundary) -> None:
        if stale and boundary == DurabilityBoundary.STATE_DIR_FSYNCED and not reached:
            reached.append(boundary)
            publish_run_metadata(
                selected.paths, replace(selected.metadata, run_id="replacement")
            )

    _hook(monkeypatch, invalidate)
    result = main(["--root", str(selected.run.root), "resume"])
    captured = capsys.readouterr()
    assert launches == []
    if stale:
        assert result != 0 and attachments == []
        assert reached == [DurabilityBoundary.STATE_DIR_FSYNCED]
        assert "Traceback" not in captured.err
        assert any(
            word in captured.err.lower() for word in ("stale", "replaced", "changed")
        )
        assert _bytes(store.path) == original and store.read() == before
    else:
        assert result == 0, captured.err
        assert len(attachments) == 1
        assert attachments[0]["root"] == selected.run.root
        assert attachments[0]["run_id"] == selected.run.run_id
        _assert_only_control(before, store.read(), False)
    _assert_other(fleet, original_other)


@pytest.mark.parametrize("fleet", [True], indirect=True)
@pytest.mark.parametrize("caller", ["service", "direct"])
def test_injected_registry_stop_signals_only_exact_selected_owner(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
    caller: str,
) -> None:
    selected = fleet.selected
    assert fleet.registry_root != selected.paths.fleet_root
    original = _bytes(selected.paths.state_file)
    original_other = _bytes(fleet.other.paths.state_file)
    signals: list[tuple[int, int]] = []
    kill = os.kill

    def signal_boundary(pid: int, sig: int) -> None:
        if sig == 0:
            kill(pid, sig)
        else:
            signals.append((pid, sig))

    def stop(run: FleetRun) -> ProcessIdentity:
        if caller == "service":
            return RunControlService(fleet.registry).stop(run)
        return stop_supervisor(run, registry=fleet.registry)

    monkeypatch.setattr(os, "kill", signal_boundary)
    with pytest.raises((ValueError, RuntimeError)):
        stop(replace(selected.run, process_start="not-selected"))
    assert signals == []
    assert stop(selected.run) == ProcessIdentity(
        selected.run.pid, selected.run.process_start
    )
    assert signals == [(selected.run.pid, signal.SIGTERM)]
    assert _bytes(selected.paths.state_file) == original
    _assert_other(fleet, original_other)


def test_shared_run_conversion_and_discovery_preserve_distinct_entries(
    fleet: Fleet, tmp_path: Path
) -> None:
    with ExitStack() as stack:
        third = _owner(stack, tmp_path / "third", "third", fleet.registry)
        stale = _owner(stack, tmp_path / "ended", "ended", fleet.registry)
        stale_path = fleet.registry.publish(stale.entry)
        _send(stale.process)
        assert stale.process.wait(timeout=5) == 0
        malformed_path = fleet.registry.publish(
            replace(fleet.other.entry, run_id="malformed")
        )
        malformed_path.write_bytes(b"invalid JSON\n")
        owners = (fleet.selected, fleet.other, third)
        expected = tuple(owner.run for owner in owners)
        converted = tuple(FleetRun.from_entry(owner.entry) for owner in owners)
        assert converted == expected
        view = discover_fleet(fleet.registry)
        assert len(view.runs) == 3 and set(view.runs) == set(expected)
        assert view.malformed_entries == (malformed_path,)
        assert view.stale_entries == (stale_path,)


@pytest.mark.parametrize("run_id", ["selected", "arbitrary-73"])
@pytest.mark.parametrize("agent", ["edge-a", "independent-worker"])
def test_shared_run_conversion_copies_independent_identity_fields(
    tmp_path: Path, run_id: str, agent: str
) -> None:
    entry = FleetEntry(
        1,
        tmp_path / run_id,
        7319,
        "opaque-process-start",
        run_id,
        agent,
        "2026-09-29T09:17:43Z",
    )
    run = FleetRun.from_entry(entry)
    assert (
        run.run_id,
        run.root,
        run.agent,
        run.started_at,
        run.pid,
        run.process_start,
    ) == (
        entry.run_id,
        entry.root,
        entry.agent,
        entry.started_at,
        entry.pid,
        entry.process_start,
    )


def _capture_signals(monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, int]]:
    signals: list[tuple[int, int]] = []
    kill = os.kill

    def signal_boundary(pid: int, sig: int) -> None:
        if sig == 0:
            kill(pid, sig)
        else:
            signals.append((pid, sig))

    monkeypatch.setattr(os, "kill", signal_boundary)
    return signals


def _release_lock(owner: Owner) -> None:
    _send(owner.process, "release")
    assert _line(owner.process) == "released"
    assert owner.process.poll() is None
    assert process_matches(ProcessIdentity(owner.run.pid, owner.run.process_start))
    assert not run_lock_held(owner.paths.run_lock)


@pytest.mark.parametrize("missing", ["lock", "registry-absent", "registry-replaced"])
def test_control_commit_rejects_missing_ownership_proof_with_live_process(
    fleet: Fleet, monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    selected = fleet.selected
    controls = RunControlService(fleet.registry)
    store = StateStore(selected.paths.state_file)
    controls.pause(selected.run, store.read()["revision"], "maintenance")
    before, original = store.read(), _bytes(store.path)
    original_other = _bytes(fleet.other.paths.state_file)
    metadata = selected.paths.run_metadata.read_bytes()
    signals = _capture_signals(monkeypatch)
    if missing == "lock":
        _release_lock(selected)
        assert selected.entry in fleet.registry.snapshot().live
    elif missing == "registry-absent":
        assert fleet.registry.remove(selected.run.run_id, expected=selected.entry)
    else:
        fleet.registry.publish(replace(selected.entry, root=fleet.other.run.root))
    if missing != "lock":
        assert run_lock_held(selected.paths.run_lock)
        assert selected.entry not in fleet.registry.snapshot().live
    assert process_matches(
        ProcessIdentity(selected.run.pid, selected.run.process_start)
    )
    assert selected.paths.run_metadata.read_bytes() == metadata
    for action in ("pause", "resume"):
        with pytest.raises(StaleSelectionError) as caught:
            getattr(controls, action)(selected.run, before["revision"])
        assert caught.value.committed is False
        assert _bytes(store.path) == original
    with pytest.raises((ValueError, RuntimeError)):
        controls.stop(selected.run)
    assert signals == [] and _bytes(store.path) == original
    assert store.read() == before
    _assert_other(fleet, original_other)


@pytest.mark.parametrize("fleet", [True], indirect=True)
@pytest.mark.parametrize("caller", ["service", "direct"])
@pytest.mark.parametrize(
    "mismatch", ["run-id", "root", "metadata", "empty-registry", "lock"]
)
def test_injected_registry_stop_requires_all_proof_for_live_process(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caller: str,
    mismatch: str,
) -> None:
    selected = fleet.selected
    run, registry = selected.run, fleet.registry
    original = _bytes(selected.paths.state_file)
    original_other = _bytes(fleet.other.paths.state_file)
    signals = _capture_signals(monkeypatch)
    if mismatch == "run-id":
        run = replace(run, run_id="unselected")
    elif mismatch == "root":
        run = replace(run, root=fleet.other.run.root)
    elif mismatch == "metadata":
        publish_run_metadata(
            selected.paths, replace(selected.metadata, run_id="replacement")
        )
    elif mismatch == "empty-registry":
        registry = FleetRegistry(tmp_path / "empty-fleet")
        assert registry.snapshot().live == ()
    else:
        _release_lock(selected)
    assert process_matches(ProcessIdentity(run.pid, run.process_start))
    with pytest.raises((ValueError, RuntimeError)):
        if caller == "service":
            RunControlService(registry).stop(run)
        else:
            stop_supervisor(run, registry=registry)
    assert signals == [] and selected.process.poll() is None
    assert _bytes(selected.paths.state_file) == original
    _assert_other(fleet, original_other)
