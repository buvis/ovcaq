from __future__ import annotations

import copy
from pathlib import Path

import pytest
from tests.runtime.test_supervisor import Harness, Step, harness
from tests.runtime.test_supervisor_preflight import (
    assert_no_ownership_records,
    fail_fleet_publish,
    fail_route_on_the_nth_call,
    fleet_contents,
    seed_foreign_fleet_entry,
    unstarted,
)

from ovcaq.errors import CommandError, ErrorCode
from ovcaq.runtime.decision import DecisionKind
from ovcaq.runtime.registry import FleetEntry, FleetRegistry, process_identity
from ovcaq.runtime.session import require_no_emergency_failure
from ovcaq.state.schema import State


def fail_fleet_remove(
    monkeypatch: pytest.MonkeyPatch, error: BaseException
) -> list[tuple[str, object]]:
    """Break the best-effort removal of an ownership record and keep what it
    was asked to remove; the registry rejects a run id with `ValueError`, not
    only with `OSError`."""
    removals: list[tuple[str, object]] = []

    def remove(self: object, run_id: str, *, expected: object = None) -> bool:
        removals.append((run_id, expected))
        raise error

    monkeypatch.setattr("ovcaq.runtime.registry.FleetRegistry.remove", remove)
    return removals


def fail_fleet_publish_keeping_the_entry(
    monkeypatch: pytest.MonkeyPatch, error: BaseException
) -> list[object]:
    """Break ownership publication before anything reaches the fleet root,
    keeping the entry the supervisor asked to publish so a later removal can
    be matched against it."""
    published: list[object] = []

    def publish(self: object, entry: object) -> Path:
        published.append(entry)
        raise error

    monkeypatch.setattr("ovcaq.runtime.registry.FleetRegistry.publish", publish)
    return published


def test_cleanup_failure_never_blocks_the_revert(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Removing a record is best effort: a `ValueError` from the removal must
    neither strand the batch this run freshly started in `running` nor cost
    the cleanup of the records that did reach disk."""
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    foreign = seed_foreign_fleet_entry(h)
    published = fail_fleet_publish_keeping_the_entry(
        monkeypatch, ValueError("synthetic fleet publish rejection")
    )
    removals = fail_fleet_remove(
        monkeypatch, ValueError("synthetic fleet removal rejection")
    )

    outcome = h.supervisor().run()

    after = h.store.read()
    assert outcome.exit_code == 1 and outcome.sessions_attempted == 0
    assert outcome.decision.kind is DecisionKind.HALT
    assert len(published) == 1 and len(removals) == 1
    run_id, expected_entry = removals[0]
    assert run_id and run_id in repr(published[0])
    assert expected_entry == published[0]
    assert after["batch"]["status"] == "idle"
    assert after["batch"]["id"] == ""
    assert after["batch"]["started_at"] is None
    assert after["control"]["attention"] is None
    assert after["revision"] > before["revision"]
    assert not (h.paths.runtime_root / "state-write-failed.json").exists()
    require_no_emergency_failure(h.paths)
    assert_no_ownership_records(h, foreign)
    expected = copy.deepcopy(before)
    expected["revision"] = after["revision"]
    assert after == expected


def test_cleanup_failure_on_a_resumed_batch_keeps_its_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The recovery is identity-guarded: a failed cleanup must not force a
    batch this run did not start to `idle`. It keeps its id, its start time
    and its `running` status, and gets an attention notice instead."""
    h = harness(tmp_path, monkeypatch)

    def resume(state: State) -> None:
        state["batch"].update(
            id="batch-resumed", status="running", started_at="2026-10-02T11:00:00Z"
        )

    before = h.store.transaction(resume)
    foreign = seed_foreign_fleet_entry(h)
    fail_fleet_publish(monkeypatch, ValueError("synthetic fleet publish rejection"))
    removals = fail_fleet_remove(
        monkeypatch, ValueError("synthetic fleet removal rejection")
    )

    outcome = h.supervisor().run()

    after = h.store.read()
    attention = after["control"]["attention"]
    assert outcome.exit_code == 1 and outcome.sessions_attempted == 0
    assert len(removals) == 1
    assert attention is not None and attention["site"] == "startup"
    assert attention["detail"].strip()
    assert after["batch"]["id"] == "batch-resumed"
    assert after["batch"]["status"] == "running"
    assert after["batch"]["started_at"] == "2026-10-02T11:00:00Z"
    expected = copy.deepcopy(before)
    expected["revision"] = after["revision"]
    expected["control"]["attention"] = attention
    assert after == expected
    assert_no_ownership_records(h, foreign)


def test_same_failure_before_a_session_opens_reverts_a_fresh_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The sibling of the session-opened case: the very same `CommandError`,
    on the same attempt path, raised before the supervisor opened a session
    returns the freshly started batch to `idle`. Only whether a session
    opened may separate the two, never the class of the failure."""
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    h.driver.steps = [Step()]
    calls = fail_route_on_the_nth_call(
        monkeypatch,
        fail_at_call=4,
        error=CommandError(ErrorCode.PROCESS_PROBE, "kernel probe refused"),
    )

    outcome = h.supervisor().run()

    after = h.store.read()
    assert len(calls) == 4
    assert outcome.exit_code == 1 and outcome.sessions_attempted == 1
    assert outcome.decision.kind is DecisionKind.HALT
    assert after["batch"]["status"] == "idle"
    assert after["batch"]["id"] == ""
    assert after["batch"]["started_at"] is None
    assert after["control"]["attention"] is None
    assert after["revision"] > before["revision"]
    assert h.driver.requests == []


def fail_the_first_spawn_probe(
    h: Harness, monkeypatch: pytest.MonkeyPatch, error: CommandError
) -> tuple[list[int], list[State]]:
    """Break the kernel identity probe `OwnedProcess.spawn` makes for the
    process it starts, for the first launched session only. Preflight's own
    probe keeps working, so the failure lands after the session opened. Keep
    the committed state as it stood at the moment of the raise."""
    import ovcaq.runtime.process as process_module
    import ovcaq.runtime.registry as registry_module

    real_spawn = process_module.OwnedProcess.spawn
    real_probe = registry_module.process_identity
    spawns: list[int] = []
    inside_first: list[int] = []
    opened: list[State] = []

    def probe(pid: int) -> object:
        if inside_first:
            opened.append(h.store.read())
            raise error
        return real_probe(pid)

    def spawn(argv: object, **kwargs: object) -> object:
        spawns.append(len(spawns) + 1)
        if len(spawns) > 1:
            return real_spawn(argv, **kwargs)
        inside_first.append(1)
        try:
            return real_spawn(argv, **kwargs)
        finally:
            inside_first.clear()

    monkeypatch.setattr(registry_module, "process_identity", probe)
    monkeypatch.setattr(process_module, "process_identity", probe, raising=False)
    monkeypatch.setattr(process_module.OwnedProcess, "spawn", staticmethod(spawn))
    return spawns, opened


def test_failure_after_session_opened_never_reverts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The revert is only for a failure that precedes the first session. Once
    a session has opened, the batch keeps exactly the identity the run minted
    and gets an attention notice - the session counter moved in the reverting
    cases too, so only the session that actually opened may decide this."""
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    h.driver.steps = [Step()]
    spawns, opened = fail_the_first_spawn_probe(
        h, monkeypatch, CommandError(ErrorCode.PROCESS_PROBE, "kernel probe refused")
    )

    outcome = h.supervisor().run()

    after = h.store.read()
    attention = after["control"]["attention"]
    assert spawns == [1] and len(opened) == 1
    minted = opened[0]
    assert [request.phase for request in h.driver.requests] == ["build"]
    assert outcome.exit_code == 1 and outcome.sessions_attempted == 1
    assert after["batch"]["status"] == "running"
    assert minted["batch"]["id"].strip() and not before["batch"]["id"].strip()
    assert after["batch"]["id"] == minted["batch"]["id"]
    assert minted["batch"]["started_at"] is not None
    assert after["batch"]["started_at"] == minted["batch"]["started_at"]
    assert attention is not None and attention["site"] == "startup"
    assert attention["detail"] == "attempt failed: kernel probe refused"
    assert after["revision"] > before["revision"]
    expected = copy.deepcopy(minted)
    expected["revision"] = after["revision"]
    expected["control"]["attention"] = attention
    assert after == expected


def test_create_session_os_error_before_session_opens_reverts_a_fresh_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An `OSError` from `create_session`, inside the first `_open_session`
    before `_session_opened` is ever set, must revert the freshly started
    batch exactly like the `CommandError` sibling above - the loop's own
    `_STATE_ERRORS` catch must not strand it `running` with no supervisor."""
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    h.driver.steps = [Step()]

    def fail_create_session(*args: object, **kwargs: object) -> object:
        raise OSError("synthetic session directory creation failure")

    monkeypatch.setattr("ovcaq.runtime.supervisor.create_session", fail_create_session)

    outcome = h.supervisor().run()

    after = h.store.read()
    assert outcome.exit_code == 1 and outcome.sessions_attempted == 1
    assert outcome.decision.kind is DecisionKind.HALT
    assert after["batch"]["status"] == "idle"
    assert after["batch"]["id"] == ""
    assert after["batch"]["started_at"] is None
    assert after["control"]["attention"] is None
    assert after["revision"] > before["revision"]
    assert h.driver.requests == []


def test_open_session_assertion_error_before_session_opens_reverts_a_fresh_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bare `AssertionError` from `_open_session`'s `assert identity is not
    None` - preflight's own probe must keep working, only the attempt probe
    fails - escapes `_STATE_ERRORS` and `_PUBLISH_ERRORS` alike; it must still
    revert the fresh batch rather than leave it `running`."""
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    h.driver.steps = [Step()]
    calls: list[int] = []

    def probe(pid: int) -> object:
        calls.append(pid)
        if len(calls) <= 2:
            return process_identity(pid)
        return None

    monkeypatch.setattr("ovcaq.runtime.supervisor.process_identity", probe)

    outcome = h.supervisor().run()

    after = h.store.read()
    assert len(calls) == 3
    assert outcome.exit_code == 1 and outcome.sessions_attempted == 1
    assert outcome.decision.kind is DecisionKind.HALT
    assert after["batch"]["status"] == "idle"
    assert after["batch"]["id"] == ""
    assert after["batch"]["started_at"] is None
    assert after["control"]["attention"] is None
    assert after["revision"] > before["revision"]
    assert h.driver.requests == []


def seed_earlier_run_evidence(h: Harness) -> dict[Path, bytes]:
    """Write the session transcript an earlier run left behind; cleaning up
    this run's ownership records must not scrub another run's evidence."""
    session = h.paths.sessions / "session-earlier"
    session.mkdir()
    (session / "raw.jsonl").write_bytes(b'{"from": "an earlier run"}\n')
    return {path: path.read_bytes() for path in session.iterdir()}


def fail_fleet_publish_after_writing(
    h: Harness, monkeypatch: pytest.MonkeyPatch, error: BaseException
) -> list[tuple[dict[str, bytes | None], bytes | None]]:
    """Let the real `FleetRegistry.publish` put this run's entry on disk, then
    raise, as a crashed fsync on a following write might. Record the fleet
    root and the run metadata as they stood when the publisher raised."""
    real_publish = FleetRegistry.publish
    observed: list[tuple[dict[str, bytes | None], bytes | None]] = []

    def publish(self: FleetRegistry, entry: FleetEntry) -> Path:
        real_publish(self, entry)
        metadata = (
            h.paths.run_metadata.read_bytes()
            if h.paths.run_metadata.is_file()
            else None
        )
        observed.append((fleet_contents(h), metadata))
        raise error

    monkeypatch.setattr("ovcaq.runtime.registry.FleetRegistry.publish", publish)
    return observed


def test_fleet_entry_written_then_raise_is_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An entry that reached disk before the publisher raised must be removed
    together with the run metadata written just before it, while another run's
    entry and an earlier run's session evidence keep their exact bytes."""
    h = harness(tmp_path, monkeypatch)
    unstarted(h)
    foreign = seed_foreign_fleet_entry(h)
    earlier = seed_earlier_run_evidence(h)
    observed = fail_fleet_publish_after_writing(
        h, monkeypatch, OSError("synthetic fsync failure after the entry was written")
    )

    outcome = h.supervisor().run()

    assert len(observed) == 1
    fleet_at_raise, metadata_at_raise = observed[0]
    mine = {name: body for name, body in fleet_at_raise.items() if name not in foreign}
    assert len(mine) == 1 and all(mine.values())
    assert metadata_at_raise
    assert outcome.exit_code == 1
    assert not h.paths.run_metadata.exists()
    assert fleet_contents(h) == foreign
    assert {path: path.read_bytes() for path in earlier} == earlier
    assert h.driver.requests == [] and h.runner.requests == []
