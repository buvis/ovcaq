"""Elapsed duration observes the selected run, independently of session totals."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from tests.integration.test_observer_terminal_cleanup import Selected, selected_run

from ovcaq.config import RuntimeSettings
from ovcaq.paths import ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.registry import (
    FleetEntry,
    FleetRegistry,
    FleetRun,
    RunLock,
    process_identity,
)
from ovcaq.runtime.session import (
    SessionMetadata,
    SessionMetric,
    observe_metrics,
    publish_run_metadata,
)
from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore
from ovcaq.tui import model

START = "2026-10-03T10:00:00Z"


class ObservationClock(datetime):
    current = datetime(2026, 10, 3, 10, 5, tzinfo=UTC)

    @classmethod
    def now(cls, tz: object = None) -> datetime:
        return cls.current if tz is not None else cls.current.replace(tzinfo=None)


@dataclass
class LiveRun:
    run: FleetRun
    settings: RuntimeSettings


@pytest.fixture
def live_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[LiveRun]:
    paths = ensure_runtime_layout(
        resolve_runtime_paths(tmp_path, xdg_state_home=tmp_path / "xdg")
    )
    settings = RuntimeSettings(paths, 0.1, 1024**2, 1024**3, 0)
    identity = process_identity(os.getpid())
    assert identity is not None
    run = FleetRun("run-1", tmp_path, "generic", START, identity.pid, identity.started)
    state = new_state(repo_root=tmp_path)
    state["batch"].update(id="batch-1", status="running", started_at=START)
    StateStore(paths.state_file).initialize(state)
    lock = RunLock.acquire(paths.run_lock)
    registry = FleetRegistry(paths.fleet_root)
    registry.publish(
        FleetEntry(
            1, tmp_path, run.pid, run.process_start, run.run_id, run.agent, START
        )
    )
    publish_run_metadata(
        paths,
        SessionMetadata(
            1, run.run_id, "session-1", run.agent, run.pid, run.process_start, START
        ),
    )
    monkeypatch.setattr(
        ObservationClock, "current", datetime(2026, 10, 3, 10, 5, tzinfo=UTC)
    )
    monkeypatch.setattr(model, "datetime", ObservationClock)
    try:
        yield LiveRun(run, settings)
    finally:
        lock.close()


def metric(kind: str, seconds: float) -> dict[str, object]:
    return asdict(
        SessionMetric(
            schema_version=1,
            kind=kind,
            run_id="run-1",
            session_id=kind,
            batch_id="batch-1",
            prd=None,
            phase_launched="build" if kind == "phase" else None,
            capability="verify" if kind == "capability" else None,
            phase_end="review",
            decision="continue",
            started_at=START,
            finished_at="2026-10-03T10:01:00Z",
            wall_seconds=seconds,
            model="observed-model" if kind == "phase" else None,
            usage=None,
        )
    )


@pytest.mark.parametrize("totals", [(), (2.0, 7.0), (400.0, 800.0)])
def test_active_duration_advances_from_run_start_independently_of_metrics(
    live_run: LiveRun, totals: tuple[float, ...]
) -> None:
    paths = live_run.settings.paths
    if totals:
        paths.metrics.write_text(
            "".join(
                json.dumps(metric(kind, seconds)) + "\n"
                for kind, seconds in zip(("phase", "capability"), totals, strict=True)
            )
        )
        snapshot = observe_metrics(paths, batch_id="batch-1")
        assert tuple(row.wall_seconds for row in snapshot.rows) == totals, snapshot.gaps
    before = paths.state_file.read_bytes()
    observer = model.ProjectObserver(live_run.run, live_run.settings)
    try:
        first = observer.poll()
        ObservationClock.current += timedelta(seconds=37)
        second = observer.poll()
    finally:
        observer.close()
    assert first.status == second.status == "running"
    assert first.run is second.run is live_run.run
    assert first.duration_seconds == pytest.approx(300.0)
    assert second.duration_seconds == pytest.approx(337.0)
    assert first.duration_seconds == 300.0
    assert paths.state_file.read_bytes() == before


@pytest.mark.parametrize(
    "started_at",
    [
        "",
        "not-a-timestamp",
        "2026-10-03T10:00:00",
        "2026-10-03T10:06:00Z",
    ],
)
def test_invalid_or_future_run_start_is_unknown_even_with_finalized_metrics(
    live_run: LiveRun, started_at: str
) -> None:
    live_run.settings.paths.metrics.write_text(json.dumps(metric("phase", 60)) + "\n")
    assert len(observe_metrics(live_run.settings.paths, batch_id="batch-1").rows) == 1
    run = replace(live_run.run, started_at=started_at)
    observer = model.ProjectObserver(run, live_run.settings)
    try:
        view = observer.poll()
    finally:
        observer.close()
    assert view.run is run
    assert view.status == "running" and not view.ended
    assert view.duration_seconds is None


def test_malformed_metrics_do_not_hide_elapsed_time_or_mutate_evidence(
    live_run: LiveRun,
) -> None:
    paths = live_run.settings.paths
    paths.metrics.write_text("{broken metric\n")
    snapshot = observe_metrics(paths, batch_id="batch-1")
    assert snapshot.rows == () and not snapshot.complete
    assert any("malformed" in gap for gap in snapshot.gaps)
    before = [path.read_bytes() for path in (paths.state_file, paths.metrics)]
    observer = model.ProjectObserver(live_run.run, live_run.settings)
    try:
        view = observer.poll()
    finally:
        observer.close()
    assert set(snapshot.gaps).issubset(view.gaps)
    assert [path.read_bytes() for path in (paths.state_file, paths.metrics)] == before
    assert view.duration_seconds == 300.0


def test_final_ended_duration_is_known_and_stable_on_later_polls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state-home"))
    with selected_run(tmp_path, "completed") as selected:
        run = selected.first.run
        started = datetime.fromisoformat(run.started_at)
        state = selected.finish()
        completed = datetime.fromisoformat(state["batch"]["completed_at"])
        monkeypatch.setattr(ObservationClock, "current", completed + timedelta(hours=2))
        monkeypatch.setattr(model, "datetime", ObservationClock)
        assert selected.child.poll() == 0 and process_identity(run.pid) is None
        write_terminal_metrics(selected, state["batch"]["id"], "valid")
        path = selected.settings.runtime.paths.state_file
        before = path.read_bytes()
        ended = selected.observer.poll()
        assert ended.ended and ended.status == "completed"
        assert ended.run is run
        ObservationClock.current += timedelta(hours=1)
        later = selected.observer.poll()
        assert later == ended
        assert path.read_bytes() == before
        assert ended.duration_seconds == pytest.approx(
            (completed - started).total_seconds()
        )


def write_terminal_metrics(selected: Selected, batch_id: str, evidence: str) -> None:
    run = selected.first.run
    started = datetime.fromisoformat(run.started_at)
    rows = []
    if evidence == "valid":
        specifications = [(run.run_id, 30), (run.run_id, 10), ("foreign-run", 90)]
    elif evidence == "missing":
        specifications = [(run.run_id, None), ("foreign-run", 90)]
    else:
        specifications = []
    for index, (run_id, seconds) in enumerate(specifications):
        row = metric("phase", 900 + index)
        row.update(
            run_id=run_id,
            session_id=f"terminal-{index}",
            batch_id=batch_id,
            started_at=run.started_at,
            finished_at=(started + timedelta(seconds=seconds))
            .isoformat()
            .replace("+00:00", "Z")
            if seconds is not None
            else None,
        )
        if seconds is None:
            row.update(phase_end=None, decision=None, wall_seconds=None)
        rows.append(row)
    paths = selected.settings.runtime.paths
    paths.metrics.write_text("".join(json.dumps(row) + "\n" for row in rows))
    snapshot = observe_metrics(paths, batch_id=batch_id)
    assert snapshot.complete and snapshot.gaps == ()
    assert [(row.run_id, row.finished_at) for row in snapshot.rows] == [
        (row["run_id"], row["finished_at"]) for row in rows
    ]


@pytest.mark.parametrize("evidence", ["valid", "missing", "empty"])
def test_ended_pause_uses_only_selected_run_metric_end_or_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, evidence: str
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state-home"))
    with selected_run(tmp_path, "paused") as selected:
        run = selected.first.run
        state = selected.finish()
        assert state["batch"]["completed_at"] is None
        write_terminal_metrics(selected, state["batch"]["id"], evidence)
        monkeypatch.setattr(
            ObservationClock,
            "current",
            datetime.fromisoformat(run.started_at) + timedelta(hours=2),
        )
        monkeypatch.setattr(model, "datetime", ObservationClock)
        paths = selected.settings.runtime.paths
        files = (paths.state_file, paths.metrics)
        before = [path.read_bytes() for path in files]
        ended = selected.observer.poll()
        assert ended.ended and ended.status == "paused"
        assert ended.run is run
        ObservationClock.current += timedelta(hours=1)
        assert selected.observer.poll() == ended
        assert [path.read_bytes() for path in files] == before
        if evidence == "valid":
            assert ended.duration_seconds == 30.0
        else:
            assert ended.duration_seconds is None
