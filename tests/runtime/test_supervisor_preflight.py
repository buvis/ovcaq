from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

import pytest
from tests.runtime.test_supervisor import Harness, Step, add_capability, harness

from ovcaq.config import PhaseSettings
from ovcaq.errors import EXIT_CODES, CommandError, ErrorCode
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

    assert supervisor.preflight() is None

    outcome = supervisor.run()
    after = h.store.read()
    assert outcome.exit_code == 0 and outcome.sessions_attempted == 1
    assert [request.phase for request in h.driver.requests] == ["build"]
    assert after["batch"]["id"].strip() and after["batch"]["status"] == "running"
    assert after["revision"] > before["revision"]
