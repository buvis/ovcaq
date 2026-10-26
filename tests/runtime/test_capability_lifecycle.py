from __future__ import annotations

import json
import os
import re
import select
import stat
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from tests.runtime.test_supervisor import Step, harness

from ovcaq.errors import CommandError, ErrorCode
from ovcaq.paths import RuntimePaths, ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.capability import (
    CapabilityExecution,
    CapabilityRequest,
    CapabilityRunner,
    CapabilityService,
)
from ovcaq.runtime.registry import ProcessIdentity, process_identity, process_matches
from ovcaq.runtime.session import (
    SessionPaths,
    parse_session_metadata,
    reconcile_metrics,
)
from ovcaq.state.schema import CapabilityAttempt, State, new_state
from ovcaq.state.store import RevisionConflictError, StateStore

T0 = "2026-09-14T10:00:00Z"
T1 = "2026-09-14T10:01:00Z"


@dataclass
class Harness:
    root: Path
    paths: RuntimePaths
    store: StateStore
    service: CapabilityService
    initial: State
    clock: list[datetime]


def _fixture_state(
    root: Path, *, required: bool, skipped: bool, name: str, batch_id: str
) -> State:
    state = new_state(repo_root=root)
    state["batch"].update(id=batch_id, status="running", started_at=T0)
    state["batch"]["capabilities"] = {
        name: {
            "required": required,
            "launcher": "fake",
            "plugin": f"fake/{name}",
            "version": "1",
            "failure": "attention",
            "status": "skipped" if skipped else "pending",
            "attempts": [],
        }
    }
    state["batch"]["completed_prds"] = [
        {
            "filename": "finished.md",
            "cycles": 2,
            "autonomous_decisions": 1,
            "escalated_decisions": 0,
            "tasks_completed": 1,
            "tasks_total": 1,
        }
    ]
    state["work"].update(next_phase="", tasks_total=1, tasks_completed=1)
    state["work"]["extensions"] = {"test/work": {"preserve": [1, 2]}}
    state["review"]["extensions"] = {"test/review": {"preserve": [3, 4]}}
    state["tasks"] = [
        {
            "id": 1,
            "name": "Finished work",
            "description": "Preserve me",
            "active_form": "",
            "status": "completed",
            "blocked_by": [],
            "tier": None,
            "files_touched": None,
            "public_contract_edit": None,
            "estimates": {"input_tokens": None, "context_peak": None},
            "attempts": [],
            "metadata": {"sentinel": [1, 2]},
        }
    ]
    return state


def _harness(
    tmp_path: Path,
    *,
    required: bool = True,
    skipped: bool = False,
    name: str = "archive",
    batch_id: str = "batch-1",
    declared: bool = True,
) -> Harness:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    paths = ensure_runtime_layout(
        resolve_runtime_paths(
            root, runtime_root=root / "runtime", xdg_state_home=tmp_path / "state-home"
        )
    )
    store = StateStore(paths.state_file)
    state = _fixture_state(
        root, required=required, skipped=skipped, name=name, batch_id=batch_id
    )
    if not declared:
        state["batch"]["capabilities"] = {}
    initial = store.initialize(state)
    clock = [datetime(2026, 9, 14, 10, tzinfo=UTC)]
    service = CapabilityService(
        root,
        store=store,
        paths=paths,
        run_id="run-1",
        clock=lambda: clock[0],
        timeout_seconds=37,
    )
    return Harness(root, paths, store, service, initial, clock)


def _session(harness: Harness, attempt: CapabilityAttempt) -> SessionPaths:
    assert attempt["session_id"] is not None
    root = harness.paths.sessions / attempt["session_id"]
    return SessionPaths(
        root=root,
        raw=root / "raw.jsonl",
        normalized=root / "normalized.jsonl",
        metrics=root / "metrics.jsonl",
        metadata=root / "meta.json",
        summary=root / "summary.json",
    )


def _rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def _workflow(state: State) -> bytes:
    return json.dumps(
        [
            state["work"],
            state["tasks"],
            state["review"],
            state["batch"]["completed_prds"],
        ],
        sort_keys=True,
    ).encode()


def _evidence(harness: Harness) -> dict[str, bytes]:
    return {
        str(path.relative_to(harness.paths.sessions)): path.read_bytes()
        for path in harness.paths.sessions.rglob("*")
        if path.is_file()
    }


def _finish(
    harness: Harness, attempt: CapabilityAttempt, success: bool, elapsed: int = 60
) -> State:
    harness.clock[0] += timedelta(seconds=elapsed)
    assert attempt["session_id"] is not None
    return harness.service.finish(
        "archive",
        attempt["id"],
        CapabilityExecution(
            success,
            attempt["session_id"],
            None if success else "Retry archive: unavailable",
        ),
    )


@dataclass
class FakeRunner:
    harness: Harness
    success: bool
    requests: list[CapabilityRequest] = field(default_factory=list)

    def run(self, request: CapabilityRequest) -> CapabilityExecution:
        self.requests.append(request)
        current = self.harness.store.read()["batch"]["capabilities"][request.name]
        assert current["status"] == "running"
        assert current["attempts"][-1]["id"] == request.attempt_id
        assert _rows(request.session.metrics)[0]["decision"] is None
        metadata = parse_session_metadata(
            json.loads(request.session.metadata.read_text())
        )
        self.harness.clock[0] += timedelta(minutes=1)
        return CapabilityExecution(
            self.success,
            metadata.session_id,
            None if self.success else "Retry archive: runner unavailable",
        )


@contextmanager
def _worker() -> Iterator[subprocess.Popen[str]]:
    worker = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import sys; print('ready', flush=True); sys.stdin.read()",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        assert worker.stdout is not None
        readable, _, _ = select.select([worker.stdout], [], [], 5)
        assert readable and worker.stdout.readline().strip() == "ready"
        yield worker
    finally:
        if worker.poll() is None:
            worker.kill()
        worker.communicate(timeout=5)


@pytest.mark.parametrize("name", ["archive", "publish"])
def test_start_commits_one_running_attempt_with_private_pending_evidence(
    tmp_path: Path,
    name: str,
) -> None:
    harness = _harness(tmp_path, name=name)
    previous_umask = os.umask(0)
    try:
        attempt = harness.service.start(name, expected_revision=0)
    finally:
        os.umask(previous_umask)
    state = harness.store.read()
    assert state["revision"] == 1
    assert state["batch"]["capabilities"][name]["status"] == "running"
    assert state["batch"]["capabilities"][name]["attempts"] == [attempt]
    assert attempt["status"] == "running" and attempt["started_at"] == T0
    assert attempt["finished_at"] is None and attempt["detail"] is None
    session = _session(harness, attempt)
    metadata = parse_session_metadata(json.loads(session.metadata.read_text()))
    assert str(UUID(metadata.session_id)) == attempt["session_id"]
    assert (metadata.run_id, metadata.agent, metadata.started_at) == (
        "run-1",
        f"capability:{name}",
        T0,
    )
    assert process_matches(ProcessIdentity(metadata.pid, metadata.process_start))
    (pending,) = _rows(session.metrics)
    assert (pending["kind"], pending["capability"], pending["batch_id"]) == (
        "capability",
        name,
        "batch-1",
    )
    assert pending["session_id"] == metadata.session_id
    for key in (
        "phase_launched",
        "phase_end",
        "model",
        "decision",
        "finished_at",
        "wall_seconds",
    ):
        assert pending[key] is None
    assert session.raw.is_file()
    for directory in (harness.paths.runtime_root, harness.paths.sessions, session.root):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    for artifact in (session.metadata, session.raw, session.metrics):
        assert stat.S_IMODE(artifact.stat().st_mode) == 0o600
    assert _workflow(state) == _workflow(harness.initial)


def test_start_rejects_conflicting_revision_without_state_or_evidence_writes(
    tmp_path: Path,
) -> None:
    harness = _harness(tmp_path)
    before, evidence = harness.store.read(), _evidence(harness)
    with pytest.raises(RevisionConflictError):
        harness.service.start("archive", expected_revision=before["revision"] + 1)
    assert harness.store.read() == before
    assert _evidence(harness) == evidence


def test_attempt_and_session_identifiers_are_unique_across_independent_roots(
    tmp_path: Path,
) -> None:
    first = _harness(tmp_path / "first").service.start("archive")
    second = _harness(tmp_path / "second").service.start("archive")
    assert first["id"] != second["id"]
    assert first["session_id"] != second["session_id"]


@pytest.mark.parametrize(
    "reason", ["unknown", "optional", "running", "failed", "succeeded"]
)
def test_start_rejects_ineligible_capabilities_without_state_or_evidence_writes(
    tmp_path: Path, reason: str
) -> None:
    harness = _harness(tmp_path, required=reason != "optional")
    if reason in {"running", "failed", "succeeded"}:
        attempt = harness.service.start("archive")
        if reason != "running":
            _finish(harness, attempt, reason == "succeeded")
    before, evidence = harness.store.read(), _evidence(harness)
    with pytest.raises(ValueError):
        harness.service.start("missing" if reason == "unknown" else "archive")
    assert harness.store.read() == before
    assert _evidence(harness) == evidence


@pytest.mark.parametrize("success", [True, False])
@pytest.mark.parametrize(
    ("started", "elapsed"), [(T0, 60), ("2027-02-03T23:59:41Z", 137)]
)
def test_finish_retains_result_evidence_and_one_final_metric_without_reopening_work(
    tmp_path: Path, success: bool, started: str, elapsed: int
) -> None:
    harness = _harness(tmp_path)
    harness.clock[0] = datetime.fromisoformat(started)
    attempt = harness.service.start("archive")
    assert attempt["started_at"] == started
    session = _session(harness, attempt)
    metadata = session.metadata.read_bytes()
    retained = b'{"event": "retained", "text": "\\u00e9"}  \n'
    session.raw.write_bytes(retained)
    state = _finish(harness, attempt, success, elapsed)
    finished = harness.clock[0].isoformat().replace("+00:00", "Z")
    expected = "succeeded" if success else "failed"
    capability = state["batch"]["capabilities"]["archive"]
    assert state == harness.store.read()
    assert capability["status"] == expected
    (final_attempt,) = capability["attempts"]
    assert final_attempt == {
        **attempt,
        "status": expected,
        "finished_at": finished,
        "detail": None if success else "Retry archive: unavailable",
    }
    (final,) = _rows(session.metrics)
    assert final["session_id"] == attempt["session_id"]
    assert final["decision"] == expected and final["finished_at"] == finished
    assert final["started_at"] == started and final["wall_seconds"] == elapsed
    assert final["phase_end"] is None and final["model"] is None
    rows = reconcile_metrics(harness.paths)
    assert len(rows) == 1 and rows[0].decision == expected
    assert len(_rows(harness.paths.metrics)) == 1
    raw = session.raw.read_bytes()
    assert raw.startswith(retained) and raw.endswith(b"\n")
    (raw_line,) = raw[len(retained) :].splitlines()
    assert json.loads(raw_line) == {
        "success": success,
        "session_id": attempt["session_id"],
        "detail": None if success else "Retry archive: unavailable",
    }
    assert session.metadata.read_bytes() == metadata
    assert stat.S_IMODE(session.raw.stat().st_mode) == 0o600
    assert stat.S_IMODE(session.metrics.stat().st_mode) == 0o600
    if not success:
        attention = state["control"]["attention"]
        assert attention is not None
        assert "archive" in attention["site"] + attention["detail"]
        assert "Retry archive: unavailable" in attention["detail"]
    assert _workflow(state) == _workflow(harness.initial)


@pytest.mark.parametrize("mismatch", ["attempt", "session", "revision"])
def test_finish_rejects_conflicting_identity_or_revision_without_finalizing_evidence(
    tmp_path: Path, mismatch: str
) -> None:
    harness = _harness(tmp_path)
    attempt = harness.service.start("archive")
    before, evidence = harness.store.read(), _evidence(harness)
    assert attempt["session_id"] is not None
    execution = CapabilityExecution(
        True, str(uuid4()) if mismatch == "session" else attempt["session_id"], None
    )
    error = RevisionConflictError if mismatch == "revision" else ValueError
    with pytest.raises(error):
        harness.service.finish(
            "archive",
            str(uuid4()) if mismatch == "attempt" else attempt["id"],
            execution,
            expected_revision=0 if mismatch == "revision" else before["revision"],
        )
    assert harness.store.read() == before
    assert _evidence(harness) == evidence


@pytest.mark.parametrize("mismatch", ["attempt", "session"])
def test_finish_rejects_previous_attempt_or_session_without_state_or_evidence_writes(
    tmp_path: Path, mismatch: str
) -> None:
    harness = _harness(tmp_path)
    previous = harness.service.start("archive")
    _finish(harness, previous, False)

    class CheckingRunner(FakeRunner):
        def run(self, request: CapabilityRequest) -> CapabilityExecution:
            before, evidence = harness.store.read(), _evidence(harness)
            current = before["batch"]["capabilities"]["archive"]["attempts"][-1]
            assert current["status"] == "running"
            assert current["id"] != previous["id"]
            assert current["session_id"] != previous["session_id"]
            session_id = (
                previous["session_id"]
                if mismatch == "session"
                else current["session_id"]
            )
            assert session_id is not None
            with pytest.raises(ValueError):
                harness.service.finish(
                    "archive",
                    previous["id"] if mismatch == "attempt" else current["id"],
                    CapabilityExecution(True, session_id, None),
                    expected_revision=before["revision"],
                )
            assert harness.store.read() == before
            assert _evidence(harness) == evidence
            return super().run(request)

    runner = CheckingRunner(harness, True)
    state = harness.service.retry("archive", runner)
    assert len(runner.requests) == 1
    assert state["batch"]["capabilities"]["archive"]["status"] == "succeeded"


def test_live_process_identity_keeps_running_and_refuses_retry_without_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    harness = _harness(tmp_path)
    runner = FakeRunner(harness, True)
    with _worker() as worker:
        identity = process_identity(worker.pid)
        assert identity is not None and process_matches(identity)
        monkeypatch.setattr(
            "ovcaq.runtime.capability.process_identity", lambda _: identity
        )
        harness.service.start("archive")
        before, evidence = harness.store.read(), _evidence(harness)
        assert harness.service.reconcile("archive") == before
        with pytest.raises(ValueError):
            harness.service.retry("archive", runner)
        assert harness.store.read() == before
        assert _evidence(harness) == evidence
        assert runner.requests == []
        assert worker.poll() is None


@pytest.mark.parametrize("stale", ["exited", "wrong-start"])
def test_reconcile_requires_matching_live_process_identity_and_records_stale_attention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stale: str
) -> None:
    harness = _harness(tmp_path)
    with _worker() as worker:
        identity = process_identity(worker.pid)
        assert identity is not None
        retained = (
            identity
            if stale == "exited"
            else ProcessIdentity(identity.pid, identity.started + "-old")
        )
        monkeypatch.setattr(
            "ovcaq.runtime.capability.process_identity", lambda _: retained
        )
        attempt = harness.service.start("archive")
        if stale == "exited":
            worker.kill()
            worker.wait(timeout=5)
        else:
            assert worker.poll() is None and process_matches(identity)
        assert not process_matches(retained)
        harness.clock[0] += timedelta(minutes=1)
        state = harness.service.reconcile("archive")
        capability = state["batch"]["capabilities"]["archive"]
        assert capability["status"] == "failed"
        (final_attempt,) = capability["attempts"]
        assert final_attempt["id"] == attempt["id"]
        assert (
            final_attempt["status"] == "failed" and final_attempt["finished_at"] == T1
        )
        assert final_attempt["detail"]
        attention = state["control"]["attention"]
        assert (
            attention is not None
            and "archive" in attention["site"] + attention["detail"]
        )
        assert "retry" in attention["detail"].lower()
        assert _workflow(state) == _workflow(harness.initial)
        assert harness.service.reconcile("archive") == state == harness.store.read()


@pytest.mark.parametrize("success", [True, False])
@pytest.mark.parametrize("timeout_seconds", [9, 83])
@pytest.mark.parametrize("batch_id", ["batch-1", "batch-retry-42"])
def test_explicit_retry_runs_once_and_preserves_prior_attempt_evidence_and_drained_work(
    tmp_path: Path, success: bool, timeout_seconds: int, batch_id: str
) -> None:
    harness = _harness(tmp_path, batch_id=batch_id)
    original = harness.service.start("archive")
    _finish(harness, original, False)
    original_evidence = _evidence(harness)
    runner = FakeRunner(harness, success)
    supplied: CapabilityRunner = runner
    independent = CapabilityService(
        harness.root,
        store=harness.store,
        paths=harness.paths,
        run_id="retry-run",
        clock=lambda: harness.clock[0],
        timeout_seconds=timeout_seconds,
    )
    state = independent.retry("archive", supplied)
    assert len(runner.requests) == 1
    (request,) = runner.requests
    assert isinstance(request, CapabilityRequest)
    assert (request.name, request.root, request.batch_id, request.timeout_seconds) == (
        "archive",
        harness.root,
        batch_id,
        timeout_seconds,
    )
    attempts = state["batch"]["capabilities"]["archive"]["attempts"]
    assert len(attempts) == 2 and attempts[0]["id"] == original["id"]
    assert attempts[1]["id"] == request.attempt_id != original["id"]
    assert attempts[1]["session_id"] != original["session_id"]
    expected = "succeeded" if success else "failed"
    assert attempts[1]["status"] == expected
    assert state["batch"]["capabilities"]["archive"]["status"] == expected
    assert state == harness.store.read()
    assert _workflow(state) == _workflow(harness.initial)
    assert all(
        _evidence(harness)[path] == data for path, data in original_evidence.items()
    )
    (final,) = _rows(request.session.metrics)
    assert (
        final["decision"] == expected
        and final["session_id"] == attempts[1]["session_id"]
    )
    assert final["run_id"] == "retry-run" and final["batch_id"] == batch_id
    assert _rows(request.session.raw)
    assert len(reconcile_metrics(harness.paths)) == 2
    assert {row["batch_id"] for row in _rows(harness.paths.metrics)} == {batch_id}


@pytest.mark.parametrize("success", [True, False])
def test_repeated_retry_rejects_success_but_allows_a_distinct_request_after_failure(
    tmp_path: Path, success: bool
) -> None:
    harness = _harness(tmp_path)
    original = harness.service.start("archive")
    _finish(harness, original, False)
    runner = FakeRunner(harness, success)
    state = harness.service.retry("archive", runner)
    before_evidence = _evidence(harness)
    if success:
        with pytest.raises(ValueError):
            harness.service.retry("archive", runner)
        assert harness.store.read() == state and _evidence(harness) == before_evidence
        assert len(runner.requests) == 1
    else:
        next_state = harness.service.retry("archive", runner)
        attempts = next_state["batch"]["capabilities"]["archive"]["attempts"]
        assert len(attempts) == 3
        assert len({attempt["id"] for attempt in attempts}) == 3
        assert len({attempt["session_id"] for attempt in attempts}) == 3
        assert len(runner.requests) == 2
        assert _workflow(next_state) == _workflow(harness.initial)
        assert len(reconcile_metrics(harness.paths)) == 3


def test_retry_reconciles_a_dead_owner_and_completes_exactly_one_new_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    harness = _harness(tmp_path)
    with _worker() as worker:
        identity = process_identity(worker.pid)
        assert identity is not None
        with monkeypatch.context() as patch:
            patch.setattr(
                "ovcaq.runtime.capability.process_identity", lambda _: identity
            )
            original = harness.service.start("archive")
        worker.kill()
        worker.wait(timeout=5)
        runner = FakeRunner(harness, True)
        state = harness.service.retry("archive", runner)
    old, new = state["batch"]["capabilities"]["archive"]["attempts"]
    assert old["id"] == original["id"] and old["status"] == "failed"
    assert old["detail"] and old["finished_at"] is not None
    assert new["id"] != old["id"] and new["status"] == "succeeded"
    assert len(runner.requests) == 1
    assert _workflow(state) == _workflow(harness.initial)
    metrics = reconcile_metrics(harness.paths)
    assert len(metrics) == 2
    assert {row.session_id for row in metrics} == {old["session_id"], new["session_id"]}


@pytest.mark.parametrize("reason", ["pending", "optional", "skipped"])
def test_retry_rejects_pending_optional_or_skipped_capabilities_without_invoking_runner(
    tmp_path: Path, reason: str
) -> None:
    harness = _harness(
        tmp_path, required=reason == "pending", skipped=reason == "skipped"
    )
    runner = FakeRunner(harness, True)
    evidence = _evidence(harness)
    with pytest.raises(ValueError):
        harness.service.retry("archive", runner)
    assert harness.store.read() == harness.initial
    assert _evidence(harness) == evidence
    assert runner.requests == []


@pytest.mark.parametrize(
    ("declared", "unknown"),
    [
        (False, "archive"),
        (False, ""),
        (True, "archiv"),
        (True, "archive-old"),
        (True, ""),
    ],
)
def test_retry_rejects_an_unknown_capability_as_a_usage_error_without_writes(
    tmp_path: Path, declared: bool, unknown: str
) -> None:
    harness = _harness(tmp_path, declared=declared)
    if declared:
        _finish(harness, harness.service.start("archive"), False)
    runner = FakeRunner(harness, True)
    before, evidence = harness.store.read(), _evidence(harness)
    state_bytes = harness.paths.state_file.read_bytes()
    message = f"^{re.escape(f'unknown capability: {unknown}')}$"
    with pytest.raises(CommandError, match=message) as caught:
        harness.service.retry(unknown, runner)
    assert caught.value.code is ErrorCode.USAGE
    assert harness.store.read() == before
    assert harness.paths.state_file.read_bytes() == state_bytes
    assert _evidence(harness) == evidence
    assert runner.requests == []
    if declared:
        state = harness.service.retry("archive", runner)
        assert [request.name for request in runner.requests] == ["archive"]
        assert state["batch"]["capabilities"]["archive"]["status"] == "succeeded"
        assert len(state["batch"]["capabilities"]["archive"]["attempts"]) == 2
    else:
        assert before["batch"]["capabilities"] == {}


def test_run_declares_no_required_capability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch)

    def unstarted(state: State) -> None:
        state["batch"] = new_state(repo_root=h.root)["batch"]

    before = h.store.transaction(unstarted)
    assert not before["batch"]["id"].strip() and before["batch"]["capabilities"] == {}
    seen: list[State] = []

    def at_first_session() -> None:
        seen.append(h.store.read())
        h.store.transaction(lambda state: state["control"].update(pause_requested=True))

    h.driver.steps = [Step(effect=at_first_session)]
    outcome = h.supervisor().run()
    assert outcome.exit_code == 0 and len(h.driver.requests) == 1
    (first,) = seen
    assert first["batch"]["id"].strip() and first["batch"]["status"] == "running"
    assert first["batch"]["capabilities"] == {}
    assert h.store.read()["batch"]["capabilities"] == {}
