from __future__ import annotations

import copy
import os
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest
from tests.runtime.test_supervisor import Harness, Step, add_capability, harness

from ovcaq.config import ConfigurationError, PhaseSettings, resolve_phase_route
from ovcaq.errors import EXIT_CODES, CommandError, ErrorCode
from ovcaq.runtime.decision import DecisionKind
from ovcaq.runtime.registry import FleetEntry, FleetRegistry, process_identity
from ovcaq.runtime.session import require_no_emergency_failure
from ovcaq.state.schema import State, new_state

HEALTHY_TIERS = {"build": "sonnet", "review": "opus", "done": "sonnet"}


def unstarted(h: Harness) -> State:
    """Commit a batch that has no identity yet and one pending capability."""

    def prepare(state: State) -> None:
        state["batch"] = new_state(repo_root=h.root)["batch"]
        add_capability(state)

    before = h.store.transaction(prepare)
    assert not before["batch"]["id"].strip()
    assert before["batch"]["capabilities"]["audit"]["status"] == "pending"
    return before


def assert_no_state_change(h: Harness, before: State) -> None:
    after = h.store.read()
    assert after["revision"] == before["revision"]
    assert after["batch"]["status"] == before["batch"]["status"]
    assert after["batch"]["id"] == before["batch"]["id"]
    assert not after["batch"]["id"].strip()
    assert after["batch"]["capabilities"]["audit"] == {
        **before["batch"]["capabilities"]["audit"],
        "status": "pending",
        "attempts": [],
    }
    assert after == before
    assert h.driver.requests == [] and h.runner.requests == []
    assert_no_runtime_write(h)


def assert_no_runtime_write(h: Harness) -> None:
    """The rejection precedes ownership publication and metric reconciliation."""
    assert not h.paths.run_metadata.exists()
    assert not h.paths.metrics.exists()
    assert list(h.paths.sessions.iterdir()) == []


def break_routes(h: Harness, *phases: str) -> None:
    h.settings = replace(
        h.settings,
        phases={
            phase: PhaseSettings(
                f"missing-{phase}" if phase in phases else tier, "high", 3
            )
            for phase, tier in HEALTHY_TIERS.items()
        },
    )


def patch_probe(monkeypatch: pytest.MonkeyPatch, outcome: object) -> list[int]:
    """Replace the kernel identity probe and record the pid it was asked for."""
    calls: list[int] = []

    def probe(pid: int) -> object:
        calls.append(pid)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    monkeypatch.setattr("ovcaq.runtime.registry.process_identity", probe)
    monkeypatch.setattr(
        "ovcaq.runtime.supervisor.process_identity", probe, raising=False
    )
    return calls


@pytest.mark.parametrize("tier", ["sonnet-x", "opusine"])
def test_preflight_rejects_unknown_tier_without_state_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tier: str
) -> None:
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    h.settings = replace(
        h.settings,
        phases={**h.settings.phases, "build": PhaseSettings(tier, "high", 3)},
    )

    with pytest.raises(CommandError) as direct:
        h.supervisor().preflight()
    assert direct.value.code is ErrorCode.USAGE
    assert str(direct.value) == f"Unknown agent tier: {tier}"

    with pytest.raises(CommandError) as caught:
        h.supervisor().run()

    error = caught.value
    assert error.code is ErrorCode.USAGE
    assert error.exit_code == EXIT_CODES[ErrorCode.USAGE] == 1
    assert str(error) == f"Unknown agent tier: {tier}"
    assert_no_state_change(h, before)


def test_preflight_rejects_missing_process_identity_without_state_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    probed = patch_probe(monkeypatch, None)

    with pytest.raises(CommandError) as direct:
        h.supervisor().preflight()
    assert direct.value.code is ErrorCode.USAGE
    assert str(direct.value) == "process identity is unavailable for this process"
    assert probed == [os.getpid()]
    probed.clear()

    with pytest.raises(CommandError) as caught:
        h.supervisor().run()

    error = caught.value
    assert error.code is ErrorCode.USAGE
    assert error.exit_code == EXIT_CODES[ErrorCode.USAGE] == 1
    assert str(error) == "process identity is unavailable for this process"
    assert probed == [os.getpid()]
    assert_no_state_change(h, before)


@pytest.mark.parametrize("detail", ["kernel probe refused", "no such process"])
def test_preflight_propagates_the_probe_error_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, detail: str
) -> None:
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    raised = CommandError(ErrorCode.PROCESS_PROBE, detail)
    probed = patch_probe(monkeypatch, raised)

    with pytest.raises(CommandError) as caught:
        h.supervisor().run()

    error = caught.value
    assert error is raised
    assert error.code is ErrorCode.PROCESS_PROBE
    assert error.exit_code == EXIT_CODES[ErrorCode.PROCESS_PROBE] == 12
    assert str(error) == detail
    assert probed == [os.getpid()]
    assert_no_state_change(h, before)


@pytest.mark.parametrize("broken", ["build", "review", "done"])
def test_preflight_rejects_a_route_broken_in_any_single_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, broken: str
) -> None:
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    break_routes(h, broken)

    with pytest.raises(CommandError) as caught:
        h.supervisor().run()

    error = caught.value
    assert error.code is ErrorCode.USAGE and error.exit_code == 1
    assert str(error) == f"Unknown agent tier: missing-{broken}"
    assert_no_state_change(h, before)


def test_preflight_reports_the_first_broken_phase_in_route_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)

    break_routes(h, "build", "review", "done")
    with pytest.raises(CommandError) as all_broken:
        h.supervisor().run()
    assert str(all_broken.value) == "Unknown agent tier: missing-build"

    break_routes(h, "review", "done")
    with pytest.raises(CommandError) as tail_broken:
        h.supervisor().run()
    assert str(tail_broken.value) == "Unknown agent tier: missing-review"

    assert_no_state_change(h, before)


def test_preflight_resolves_routes_for_the_driver_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    config = h.root / "ovcaq.toml"
    config.write_text(
        config.read_text() + '[agents.remote]\ncommand = ["remote-runner"]\n'
        'tiers = { haiku = "model-h" }\n'
    )
    before = unstarted(h)
    h.driver.name = "remote"

    with pytest.raises(CommandError) as caught:
        h.supervisor().run()

    error = caught.value
    assert error.code is ErrorCode.USAGE and error.exit_code == 1
    assert str(error) == "Unknown agent tier: sonnet"
    assert_no_state_change(h, before)


def test_preflight_accepts_a_tier_only_the_agent_override_supplies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    (h.root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner"]\n'
        'tiers = { sonnet = "model-s", opus = "model-o", custom = "model-c" }\n'
        '[agents.local.phases.review]\ntier = "custom"\n'
    )
    before = unstarted(h)
    h.settings = replace(
        h.settings,
        phases={**h.settings.phases, "review": PhaseSettings("bespoke", "high", 3)},
    )

    assert h.supervisor().preflight() is None
    assert_no_state_change(h, before)


def test_preflight_reports_the_override_tier_not_the_neutral_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    config = h.root / "ovcaq.toml"
    config.write_text(
        config.read_text() + '[agents.local.phases.done]\ntier = "ghost"\n'
    )
    before = unstarted(h)
    assert h.settings.phases["done"].tier == "sonnet"

    with pytest.raises(CommandError) as caught:
        h.supervisor().preflight()

    assert caught.value.code is ErrorCode.USAGE
    assert str(caught.value) == "Unknown agent tier: ghost"
    assert_no_state_change(h, before)


def test_preflight_converts_a_configuration_fault_that_names_no_tier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    config = h.root / "ovcaq.toml"
    config.write_text(
        config.read_text() + "[agents.local.phases.build]\ntimeout_seconds = 5\n"
    )
    before = unstarted(h)

    with pytest.raises(CommandError) as direct:
        h.supervisor().preflight()
    assert str(direct.value) == "unknown fields for phase build"

    with pytest.raises(CommandError) as caught:
        h.supervisor().run()

    error = caught.value
    assert error.code is ErrorCode.USAGE
    assert error.exit_code == EXIT_CODES[ErrorCode.USAGE] == 1
    assert str(error) == "unknown fields for phase build"
    assert_no_state_change(h, before)


def test_preflight_probes_process_identity_before_resolving_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    break_routes(h, "build", "review", "done")
    probed = patch_probe(monkeypatch, None)

    with pytest.raises(CommandError) as caught:
        h.supervisor().preflight()

    assert caught.value.code is ErrorCode.USAGE
    assert str(caught.value) == "process identity is unavailable for this process"
    assert probed == [os.getpid()]
    assert_no_state_change(h, before)


def test_preflight_rejects_a_broken_route_for_an_already_started_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    before = h.store.read()
    assert before["batch"]["id"] == "batch-1"
    assert before["batch"]["status"] == "running"
    break_routes(h, "review")

    with pytest.raises(CommandError) as caught:
        h.supervisor().run()

    error = caught.value
    assert error.code is ErrorCode.USAGE
    assert error.exit_code == EXIT_CODES[ErrorCode.USAGE] == 1
    assert str(error) == "Unknown agent tier: missing-review"
    assert h.store.read() == before
    assert h.driver.requests == [] and h.runner.requests == []
    assert_no_runtime_write(h)


def test_preflight_revalidates_routes_after_an_earlier_healthy_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    assert h.supervisor().preflight() is None
    h.driver.steps = [
        Step(
            effect=lambda: h.store.transaction(
                lambda state: state["control"].update(pause_requested=True)
            )
        )
    ]
    assert h.supervisor().run().exit_code == 0
    settled = h.store.read()

    break_routes(h, "build")
    with pytest.raises(CommandError) as caught:
        h.supervisor().run()

    assert caught.value.code is ErrorCode.USAGE
    assert str(caught.value) == "Unknown agent tier: missing-build"
    assert h.store.read() == settled
    assert len(h.driver.requests) == 1


def test_preflight_passes_on_a_healthy_host_and_the_run_mints_a_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    h.driver.steps = [
        Step(
            effect=lambda: h.store.transaction(
                lambda state: state["control"].update(pause_requested=True)
            )
        )
    ]
    supervisor = h.supervisor()
    settings = supervisor._settings
    project_entries = sorted(path.name for path in h.root.iterdir())

    assert supervisor.preflight() is None

    assert supervisor._settings is settings and h.settings is settings
    assert sorted(path.name for path in h.root.iterdir()) == project_entries
    assert_no_runtime_write(h)

    outcome = supervisor.run()
    after = h.store.read()
    assert outcome.exit_code == 0 and outcome.sessions_attempted == 1
    assert [request.phase for request in h.driver.requests] == ["build"]
    assert [
        (request.model, request.effort, request.timeout_seconds)
        for request in h.driver.requests
    ] == [("model-s", "high", 3)]
    assert after["batch"]["id"].strip() and after["batch"]["status"] == "running"
    assert after["revision"] > before["revision"]


def fail_fleet_publish(monkeypatch: pytest.MonkeyPatch, error: BaseException) -> None:
    """Break ownership publication after the run metadata is already on disk."""

    def publish(self: object, entry: object) -> Path:
        raise error

    monkeypatch.setattr("ovcaq.runtime.registry.FleetRegistry.publish", publish)


def fleet_contents(h: Harness) -> dict[str, bytes | None]:
    return {
        path.name: path.read_bytes() if path.is_file() else None
        for path in h.paths.fleet_root.iterdir()
    }


def seed_foreign_fleet_entry(h: Harness) -> dict[str, bytes | None]:
    """Publish a live entry owned by another project; a failed start must keep it."""
    identity = process_identity(os.getpid())
    assert identity is not None
    run_id = uuid4().hex
    foreign = FleetEntry(
        1,
        h.root.parent / "other-project",
        identity.pid,
        identity.started,
        run_id,
        "local",
        "2026-10-01T09:00:00Z",
    )
    FleetRegistry(h.paths.fleet_root).publish(foreign)
    seeded = fleet_contents(h)
    assert seeded[f"{run_id}.json"]
    return seeded


def assert_no_ownership_records(h: Harness, foreign: dict[str, bytes | None]) -> None:
    assert not h.paths.run_metadata.exists()
    assert fleet_contents(h) == foreign
    assert list(h.paths.sessions.iterdir()) == []
    assert h.driver.requests == [] and h.runner.requests == []


@pytest.mark.parametrize(
    "error",
    [OSError("synthetic fleet publish failure"), RuntimeError("registry unavailable")],
    ids=["oserror", "runtimeerror"],
)
def test_early_failure_returns_fresh_batch_to_idle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    foreign = seed_foreign_fleet_entry(h)
    fail_fleet_publish(monkeypatch, error)

    outcome = h.supervisor().run()

    after = h.store.read()
    assert outcome.exit_code == 1 and outcome.sessions_attempted == 0
    assert outcome.decision.kind is DecisionKind.HALT
    assert outcome.decision.reason.strip()
    assert after["batch"]["id"] == ""
    assert after["batch"]["started_at"] is None
    assert after["batch"]["status"] == "idle"
    assert after["control"]["attention"] is None
    assert after["revision"] > before["revision"]
    assert not (h.paths.runtime_root / "state-write-failed.json").exists()
    require_no_emergency_failure(h.paths)
    assert_no_ownership_records(h, foreign)


@pytest.mark.parametrize(
    ("batch_id", "started_at"),
    [
        ("batch-resumed", "2026-10-02T11:00:00Z"),
        ("batch-9", "2026-09-30T08:15:00Z"),
        (uuid4().hex, "2026-10-20T07:45:00Z"),
    ],
    ids=["named", "short", "minted-shape"],
)
def test_early_failure_on_resumed_batch_records_attention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, batch_id: str, started_at: str
) -> None:
    h = harness(tmp_path, monkeypatch)

    def resume(state: State) -> None:
        state["batch"].update(id=batch_id, status="running", started_at=started_at)

    before = h.store.transaction(resume)
    foreign = seed_foreign_fleet_entry(h)
    fail_fleet_publish(monkeypatch, OSError("synthetic fleet publish failure"))

    outcome = h.supervisor().run()

    after = h.store.read()
    assert outcome.exit_code == 1 and outcome.sessions_attempted == 0
    attention = after["control"]["attention"]
    assert attention is not None and attention["site"] == "startup"
    assert attention["detail"].strip()
    assert after["batch"]["id"] == batch_id
    assert after["batch"]["status"] == "running"
    assert after["batch"]["started_at"] == started_at
    assert after["revision"] > before["revision"]
    expected = copy.deepcopy(before)
    expected["revision"] = after["revision"]
    expected["control"]["attention"] = attention
    assert after == expected
    assert_no_ownership_records(h, foreign)


def test_early_failure_falls_back_to_attention_when_the_revert_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    unstarted(h)
    before = h.store.transaction(
        lambda state: state["work"].update(prd="00007-feature.md")
    )
    foreign = seed_foreign_fleet_entry(h)
    fail_fleet_publish(monkeypatch, OSError("synthetic fleet publish failure"))

    outcome = h.supervisor().run()

    after = h.store.read()
    assert outcome.exit_code == 1 and outcome.sessions_attempted == 0
    attention = after["control"]["attention"]
    assert attention is not None and attention["site"] == "startup"
    assert after["batch"]["id"].strip()
    assert after["batch"]["status"] == "running"
    assert after["batch"]["started_at"] is not None
    assert after["work"]["prd"] == "00007-feature.md"
    expected = copy.deepcopy(before)
    expected["revision"] = after["revision"]
    expected["control"]["attention"] = attention
    expected["batch"].update(
        id=after["batch"]["id"],
        status="running",
        started_at=after["batch"]["started_at"],
    )
    assert after == expected
    assert_no_ownership_records(h, foreign)


def test_early_failure_lets_an_interrupt_propagate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    unstarted(h)
    interrupt = KeyboardInterrupt()
    fail_fleet_publish(monkeypatch, interrupt)

    with pytest.raises(KeyboardInterrupt) as caught:
        h.supervisor().run()

    assert caught.value is interrupt


def fail_route_on_the_nth_call(
    monkeypatch: pytest.MonkeyPatch, *, fail_at_call: int, error: Exception
) -> list[int]:
    """Let preflight's own route checks pass; break only a later call (the
    one `_attempt` makes for the current phase, after preflight passed)."""
    calls: list[int] = []

    def route(
        root: Path, phase: str, *, agent: str, phase_settings: PhaseSettings
    ) -> object:
        calls.append(len(calls) + 1)
        if len(calls) == fail_at_call:
            raise error
        return resolve_phase_route(
            root, phase, agent=agent, phase_settings=phase_settings
        )

    monkeypatch.setattr("ovcaq.runtime.supervisor.resolve_phase_route", route)
    return calls


def test_attempt_failure_before_a_session_opens_reverts_a_fresh_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ConfigurationError raised by `_attempt`'s own route lookup - after
    preflight's three checks already passed - must not leave batch.status
    running with no supervisor (the exact defect this fix addresses)."""
    h = harness(tmp_path, monkeypatch)
    before = unstarted(h)
    calls = fail_route_on_the_nth_call(
        monkeypatch,
        fail_at_call=4,
        error=ConfigurationError("synthetic broken route for the build phase"),
    )

    outcome = h.supervisor().run()

    after = h.store.read()
    assert len(calls) == 4
    assert outcome.exit_code == 1 and outcome.sessions_attempted == 1
    assert outcome.decision.kind is DecisionKind.HALT
    assert after["batch"]["id"] == ""
    assert after["batch"]["started_at"] is None
    assert after["batch"]["status"] == "idle"
    assert after["control"]["attention"] is None
    assert after["revision"] > before["revision"]
    assert h.driver.requests == []


def test_attempt_failure_on_a_resumed_batch_records_attention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same failure on a batch this run did not freshly start (no
    `started` to revert) falls back to an attention notice, not a silent
    running-with-no-supervisor state."""
    h = harness(tmp_path, monkeypatch)

    def resume(state: State) -> None:
        state["batch"].update(
            id="batch-resumed", status="running", started_at="2026-10-02T11:00:00Z"
        )

    before = h.store.transaction(resume)
    fail_route_on_the_nth_call(
        monkeypatch,
        fail_at_call=4,
        error=ConfigurationError("synthetic broken route for the build phase"),
    )

    outcome = h.supervisor().run()

    after = h.store.read()
    attention = after["control"]["attention"]
    assert outcome.exit_code == 1
    assert outcome.decision.kind is DecisionKind.HALT
    assert attention is not None and attention["site"] == "startup"
    assert after["batch"]["id"] == "batch-resumed"
    assert after["batch"]["status"] == "running"
    assert after["batch"]["started_at"] == "2026-10-02T11:00:00Z"
    assert after["revision"] > before["revision"]
    assert h.driver.requests == []


def fail_run_metadata_after_writing(
    monkeypatch: pytest.MonkeyPatch, error: BaseException
) -> None:
    """Let `publish_run_metadata` write its file, then raise, as a crashed
    fsync or a disk-full error on the following write might."""
    import ovcaq.runtime.supervisor as supervisor_module

    real_publish = supervisor_module.publish_run_metadata

    def publish(paths: object, metadata: object) -> None:
        real_publish(paths, metadata)
        raise error

    monkeypatch.setattr(supervisor_module, "publish_run_metadata", publish)


def test_run_metadata_write_then_raise_leaves_no_orphan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A tracking write before the call (not after it returns) is what lets
    cleanup find a file that was written just before the publisher raised."""
    h = harness(tmp_path, monkeypatch)
    unstarted(h)
    foreign = seed_foreign_fleet_entry(h)
    error = OSError("synthetic fsync failure after run metadata was written")
    fail_run_metadata_after_writing(monkeypatch, error)

    outcome = h.supervisor().run()

    after = h.store.read()
    assert outcome.exit_code == 1 and outcome.sessions_attempted == 0
    assert outcome.decision.kind is DecisionKind.HALT
    assert after["batch"]["id"] == ""
    assert after["batch"]["status"] == "idle"
    assert_no_ownership_records(h, foreign)
