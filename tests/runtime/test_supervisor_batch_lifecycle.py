from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from tests.runtime.test_supervisor import Step, add_capability, drain, harness

from ovcaq.runtime.decision import DecisionKind, SupervisorDecision
from ovcaq.runtime.session import reconcile_metrics
from ovcaq.state.schema import State, new_state


@pytest.mark.parametrize("started", [False, True])
def test_run_commits_batch_identity_before_first_metric_and_preserves_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, started: bool
) -> None:
    identifiers = []
    for index in range(2):
        location = tmp_path / str(index)
        location.mkdir()
        h = harness(location, monkeypatch)

        def prepare(state: State, root: Path = h.root) -> None:
            if not started:
                state["batch"] = new_state(repo_root=root)["batch"]
            else:
                state["batch"]["started_at"] = "2026-08-26T10:00:00Z"
            state["work"]["extensions"] = {"test/work": [1, 2]}
            state["review"]["extensions"] = {"test/review": [3, 4]}

        before = h.store.transaction(prepare)
        expected_time = (
            before["batch"]["started_at"] if started else h.clock.now().isoformat()
        )
        snapshot = h.root / "first-metric-state.json"
        h.driver.steps = [
            Step(
                code=f"Path({str(snapshot)!r}).write_text(Path({str(h.store.path)!r}).read_text())",
                effect=lambda h=h: h.store.transaction(
                    lambda state: state["control"].update(pause_requested=True)
                ),
            )
        ]
        outcome = h.supervisor().run()
        assert outcome.exit_code == 0 and outcome.sessions_attempted == 1
        observed = json.loads(snapshot.read_text())
        batch = observed["batch"]
        assert batch["id"].strip() and batch["status"] == "running"
        assert datetime.fromisoformat(batch["started_at"]) == datetime.fromisoformat(
            expected_time
        )
        if started:
            assert batch == before["batch"]
        for key in ("work", "tasks", "review"):
            assert observed[key] == before[key] == h.store.read()[key]
        assert batch["completed_prds"] == before["batch"]["completed_prds"]
        (metric,) = reconcile_metrics(h.paths)
        assert metric.batch_id == batch["id"]
        identifiers.append(batch["id"])
    if not started:
        assert len(set(identifiers)) == 2


@pytest.mark.parametrize("empty_optional", [False, True])
def test_terminal_drain_archives_completed_batch_with_injected_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, empty_optional: bool
) -> None:
    h = harness(tmp_path, monkeypatch)

    def prepare(state: State) -> None:
        drain(state, completed=not empty_optional)
        if empty_optional:
            add_capability(state)
            state["batch"]["capabilities"]["audit"]["required"] = False

    before = h.store.transaction(prepare)
    supervisor = h.supervisor()
    outcome = supervisor.run()
    result = h.store.read()
    assert outcome.exit_code == 0 and outcome.decision.kind == DecisionKind.COMPLETE
    assert outcome.sessions_attempted == 0 and h.runner.requests == []
    assert result["batch"]["status"] == "completed"
    assert datetime.fromisoformat(result["batch"]["completed_at"]) == h.clock.now()
    for key in ("work", "tasks", "review"):
        assert result[key] == before[key]
    assert result["batch"]["completed_prds"] == before["batch"]["completed_prds"]
    archive = h.paths.reports / "batch-1-state-final.json"
    assert json.loads(archive.read_text()) == result
    original = archive.read_bytes(), archive.stat().st_mtime_ns
    assert supervisor.apply(SupervisorDecision(DecisionKind.COMPLETE, "done")) is False
    assert h.store.read() == result
    assert (archive.read_bytes(), archive.stat().st_mtime_ns) == original


def test_empty_drain_skips_required_capability_using_injected_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(add_capability)
    before = h.store.transaction(lambda state: drain(state, completed=False))
    outcome = h.supervisor().run()
    result = h.store.read()
    assert outcome.exit_code == 0 and outcome.sessions_attempted == 0
    assert h.runner.requests == [] and h.driver.requests == []
    assert result["batch"]["capabilities"]["audit"] == {
        **before["batch"]["capabilities"]["audit"],
        "required": False,
        "status": "skipped",
    }
    assert result["batch"]["status"] == "completed"
    assert datetime.fromisoformat(result["batch"]["completed_at"]) == h.clock.now()
    assert (
        json.loads((h.paths.reports / "batch-1-state-final.json").read_text()) == result
    )
