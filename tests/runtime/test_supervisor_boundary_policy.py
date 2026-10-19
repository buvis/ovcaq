from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from tests.runtime.test_supervisor import Step, add_capability, drain, harness

from ovcaq.events.model import FailureClass
from ovcaq.runtime.decision import DecisionKind, progress_fingerprint
from ovcaq.state.schema import Notice, State

NOTICE: Notice = {
    "site": "review_cap",
    "detail": "Inspect review",
    "created_at": "2026-10-02T12:00:00Z",
}


@pytest.mark.parametrize(
    "failures",
    [
        [FailureClass.AGENT, FailureClass.CONNECTIVITY, FailureClass.RATE_LIMIT],
        [FailureClass.RATE_LIMIT, FailureClass.AGENT, FailureClass.CONNECTIVITY],
    ],
)
def test_alternating_failure_classes_cannot_extend_the_phase_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failures: list[FailureClass]
) -> None:
    h = harness(tmp_path, monkeypatch)
    repeats: list[int] = []
    h.driver.on_line = lambda _: repeats.append(
        h.store.read()["recovery"]["phase_repeats"]
    )
    h.driver.steps = [Step(failure, reset_seconds=1) for failure in failures]
    outcome = h.supervisor().run()
    assert outcome.sessions_attempted == 3
    assert outcome.decision.kind in {DecisionKind.HALT, DecisionKind.PAUSE}
    assert repeats == [0, 1, 2]
    state = h.store.read()
    assert state["recovery"]["phase_repeats"] == 3
    assert state["recovery"]["phase_fingerprint"] == progress_fingerprint(state)
    assert len(h.driver.requests) == 3


@pytest.mark.parametrize("boundary", ["workflow", "capability", "empty", "complete"])
@pytest.mark.parametrize("site", ["review_cap", "operator-check"])
@pytest.mark.parametrize(
    "control", ["attention", "pause_requested", "phase", "next_phase"]
)
def test_committed_controls_block_every_startup_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    control: str,
    site: str,
) -> None:
    h = harness(tmp_path, monkeypatch)

    def prepare(state: State) -> None:
        if boundary != "workflow":
            drain(state, completed=boundary != "empty")
        if boundary in {"capability", "empty"}:
            add_capability(state)
        if control == "attention":
            state["control"]["attention"] = deepcopy(NOTICE)
            state["control"]["attention"]["site"] = site
        elif control == "pause_requested":
            state["control"].update(pause_requested=True, pause_reason=NOTICE)
        else:
            state["work"][control] = "paused"

    h.store.transaction(prepare)
    before = h.store.read()
    outcome = h.supervisor().run()
    assert outcome.sessions_attempted == 0
    assert outcome.decision.kind == (
        DecisionKind.HALT if control == "attention" else DecisionKind.PAUSE
    )
    assert (outcome.exit_code != 0) == (control == "attention")
    assert h.driver.requests == h.runner.requests == []
    after = h.store.read()
    assert after["control"] == before["control"]
    assert after["work"] == before["work"]
    assert after["batch"]["capabilities"] == before["batch"]["capabilities"]
    assert after["batch"]["status"] != "completed"
