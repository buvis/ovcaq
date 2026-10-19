"""Requirements-only capability execution and timeout regressions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from tests.runtime.test_capability_lifecycle import _workflow
from tests.runtime.test_supervisor import Harness, add_capability, drain, harness, rows

from ovcaq.config import supervisor_settings
from ovcaq.runtime.capability import (
    CapabilityExecution,
    CapabilityRequest,
    CapabilityService,
)
from ovcaq.runtime.decision import DecisionKind
from ovcaq.runtime.session import reconcile_metrics


@dataclass
class EvidenceRunner:
    h: Harness
    error: Exception | None = None
    detail: str | None = None
    requests: list[CapabilityRequest] = field(default_factory=list)
    aggregates: list[list[dict[str, object]]] = field(default_factory=list)

    def run(self, request: CapabilityRequest) -> CapabilityExecution:
        self.requests.append(request)
        self.aggregates.append(
            rows(self.h.paths.metrics) if self.h.paths.metrics.exists() else []
        )
        current = self.h.store.read()["batch"]["capabilities"][request.name]
        assert current["status"] == "running"
        assert current["attempts"][-1]["id"] == request.attempt_id
        assert current["attempts"][-1]["session_id"] == request.session.root.name
        request.session.raw.write_text('{"event":"runner evidence"}\n')
        if self.error is not None:
            raise self.error
        return CapabilityExecution(True, request.session.root.name, self.detail)


def service(h: Harness, **options: object) -> CapabilityService:
    return CapabilityService(
        h.root,
        store=h.store,
        paths=h.paths,
        run_id="explicit-retry",
        clock=h.clock.now,
        **options,
    )


def ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Harness:
    h = harness(tmp_path, monkeypatch)
    h.store.transaction(add_capability)
    h.store.transaction(drain)
    return h


def failed_attempt(h: Harness, name: str = "audit") -> dict[str, object]:
    lifecycle = service(h, timeout_seconds=17)
    attempt = lifecycle.start(name)
    assert attempt["session_id"] is not None
    lifecycle.finish(
        name,
        attempt["id"],
        CapabilityExecution(False, attempt["session_id"], "seed failure; retry audit"),
    )
    return h.store.read()["batch"]["capabilities"][name]["attempts"][0]


def configure(h: Harness, user: str, project: str) -> None:
    user_path = h.root.parent / "user-config/ovcaq/config.toml"
    user_path.parent.mkdir(parents=True, exist_ok=True)
    user_path.write_text(user)
    (h.root / "ovcaq.toml").write_text(project)
    h.settings = supervisor_settings(h.root, runtime=h.settings.runtime)


@pytest.mark.parametrize("entry", ["pending", "retry"])
@pytest.mark.parametrize("name", ["audit", "archive"])
@pytest.mark.parametrize(
    ("user", "project", "expected"),
    [
        (None, None, 10800),
        (79, None, 79),
        (79, 1, 1),
        (79, 86400, 86400),
        (2, None, 2),
        (42, None, 42),
        (79, 1234, 1234),
        (79, 86399, 86399),
    ],
)
def test_capability_request_uses_bounded_configuration_without_agent_route(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entry: str,
    name: str,
    user: int | None,
    project: int | None,
    expected: int,
) -> None:
    h = ready(tmp_path, monkeypatch)
    if name != "audit":
        h.store.transaction(
            lambda state: state["batch"]["capabilities"].update(
                {name: state["batch"]["capabilities"].pop("audit")}
            )
        )
    if entry == "retry":
        failed_attempt(h, name)
    configure(
        h,
        "" if user is None else f"[capabilities.{name}]\ntimeout_seconds={user}\n",
        "[phases.done]\ntimeout_seconds=5\n"
        + (
            ""
            if project is None
            else f"[capabilities.{name}]\ntimeout_seconds={project}\n"
        ),
    )
    runner = EvidenceRunner(h)
    h.runner = runner
    if entry == "pending":
        assert h.supervisor().run().sessions_attempted == 0
    else:
        service(h).retry(name, runner)
    (request,) = runner.requests
    assert request.timeout_seconds == expected
    assert request.name == name
    assert h.driver.requests == []
    assert h.store.read()["batch"]["capabilities"][name]["status"] == "succeeded"


@pytest.mark.parametrize("override", [1, 2, 42, 1234, 10800, 86399, 86400])
def test_explicit_timeout_overrides_project_and_user_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: int,
) -> None:
    h = ready(tmp_path, monkeypatch)
    failed_attempt(h)
    configure(
        h,
        "[capabilities.audit]\ntimeout_seconds=71\n",
        "[capabilities.audit]\ntimeout_seconds=43\n",
    )
    runner = EvidenceRunner(h)
    service(h, timeout_seconds=override).retry("audit", runner)
    (request,) = runner.requests
    assert request.timeout_seconds == override
    assert h.driver.requests == []


@pytest.mark.parametrize(
    ("user", "project", "override", "expected"),
    [("true", "41", None, 41), ("false", "-1", 59, 59)],
    ids=["project-over-invalid-user", "explicit-over-invalid-project-and-user"],
)
def test_valid_higher_priority_timeout_supersedes_invalid_lower_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    user: str,
    project: str,
    override: int | None,
    expected: int,
) -> None:
    h = ready(tmp_path, monkeypatch)
    failed_attempt(h)
    user_path = h.root.parent / "user-config/ovcaq/config.toml"
    user_path.parent.mkdir(parents=True, exist_ok=True)
    user_path.write_text(f"[capabilities.audit]\ntimeout_seconds={user}\n")
    (h.root / "ovcaq.toml").write_text(
        f"[capabilities.audit]\ntimeout_seconds={project}\n"
    )
    runner = EvidenceRunner(h)
    options = {} if override is None else {"timeout_seconds": override}
    state = service(h, **options).retry("audit", runner)
    (request,) = runner.requests
    assert request.timeout_seconds == expected
    assert state["batch"]["capabilities"]["audit"]["status"] == "succeeded"
    assert h.driver.requests == []


@pytest.mark.parametrize("source", ["user", "project", "explicit"])
@pytest.mark.parametrize(
    "value", [True, False, 0, -1, 86401, 1.5, float("inf"), float("nan"), "79", ""]
)
def test_invalid_timeout_is_rejected_before_runner_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    value: object,
) -> None:
    h = ready(tmp_path, monkeypatch)
    failed_attempt(h)
    runner = EvidenceRunner(h)
    literal = json.dumps(value) if isinstance(value, str) else str(value).lower()
    config = f"[capabilities.audit]\ntimeout_seconds={literal}\n"
    with pytest.raises(ValueError):
        if source == "explicit":
            service(h, timeout_seconds=value).retry("audit", runner)
        else:
            configure(
                h,
                config if source == "user" else "",
                config if source == "project" else "",
            )
            service(h).retry("audit", runner)
    assert runner.requests == []
    assert h.driver.requests == []


class IntegerLikeTimeout:
    def __int__(self) -> int:
        return 79

    def __index__(self) -> int:
        return 79


@pytest.mark.parametrize(
    "value",
    [None, [], {}, IntegerLikeTimeout()],
    ids=["null", "list", "mapping", "integer-like"],
)
def test_explicit_timeout_rejects_noninteger_objects_before_runner_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    value: object,
) -> None:
    h = ready(tmp_path, monkeypatch)
    failed_attempt(h)
    runner = EvidenceRunner(h)
    with pytest.raises(ValueError):
        service(h, timeout_seconds=value).retry("audit", runner)
    assert runner.requests == [] and h.driver.requests == []


@pytest.mark.parametrize("entry", ["pending", "retry"])
@pytest.mark.parametrize(
    "error",
    [
        LookupError("archive backend unavailable"),
        LookupError("another archive destination disappeared"),
        RuntimeError("runner exited unexpectedly"),
        OSError("artifact write failed"),
    ],
    ids=["lookup-original", "lookup-other", "runtime", "os"],
)
def test_runner_exception_retains_identity_pins_results_and_actionable_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entry: str,
    error: Exception,
) -> None:
    h = ready(tmp_path, monkeypatch)
    prior = failed_attempt(h) if entry == "retry" else None
    before = h.store.read()
    runner = EvidenceRunner(h, error=error)
    h.runner = runner
    if entry == "pending":
        outcome = h.supervisor().run()
        assert outcome.sessions_attempted == 0 and outcome.exit_code != 0
        assert outcome.decision.kind == DecisionKind.HALT
    else:
        with pytest.raises(type(error), match=f"^{re.escape(str(error))}$"):
            service(h).retry("audit", runner)
    after = h.store.read()
    (request,) = runner.requests
    capability = after["batch"]["capabilities"]["audit"]
    assert capability["status"] == "failed"
    assert len(capability["attempts"]) == (2 if prior else 1)
    if prior:
        assert capability["attempts"][0] == prior
    attempt = capability["attempts"][-1]
    assert attempt["id"] == request.attempt_id
    assert attempt["session_id"] == request.session.root.name
    assert attempt["status"] == "failed" and attempt["finished_at"] is not None
    assert _workflow(after) == _workflow(before)
    for key in ("required", "launcher", "plugin", "version", "failure"):
        assert capability[key] == before["batch"]["capabilities"]["audit"][key]
    assert_failure_evidence(h, request, attempt, error)


def assert_failure_evidence(
    h: Harness, request: CapabilityRequest, attempt: dict, error: Exception
) -> None:
    attention = h.store.read()["control"]["attention"]
    assert attention is not None
    for detail in (attempt["detail"], attention["detail"]):
        assert type(error).__name__ in detail and str(error) in detail
        assert "retry" in detail.lower() and "audit" in detail.lower()
    raw = rows(request.session.raw)
    assert raw[0] == {"event": "runner evidence"}
    assert raw[-1]["session_id"] == attempt["session_id"]
    assert raw[-1]["success"] is False
    assert raw[-1]["detail"] == attempt["detail"]
    (metric,) = rows(request.session.metrics)
    assert metric["decision"] == "failed"
    assert metric["session_id"] == attempt["session_id"]
    assert metric["finished_at"] == attempt["finished_at"]
    aggregate = rows(h.paths.metrics)
    assert [r for r in aggregate if r["session_id"] == attempt["session_id"]] == [
        metric
    ]
    assert len(reconcile_metrics(h.paths)) == len(aggregate)
    assert rows(h.paths.metrics) == aggregate


@pytest.mark.parametrize("entry", ["pending", "retry"])
def test_running_capability_is_never_published_as_interrupted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entry: str,
) -> None:
    h = ready(tmp_path, monkeypatch)
    if entry == "retry":
        failed_attempt(h)
    runner = EvidenceRunner(h, detail="archived 7 records; checksum verified")
    h.runner = runner
    if entry == "pending":
        h.supervisor().run()
    else:
        service(h).retry("audit", runner)
    (request,) = runner.requests
    (during,) = runner.aggregates
    live = [row for row in during if row["session_id"] == request.session.root.name]
    assert all(row["decision"] is None and row["finished_at"] is None for row in live)
    final = rows(h.paths.metrics)
    current = [row for row in final if row["session_id"] == request.session.root.name]
    assert len(current) == 1 and current[0]["decision"] == "succeeded"
    assert current[0]["finished_at"] is not None
    assert len(reconcile_metrics(h.paths)) == len(final)
    assert rows(h.paths.metrics) == final
    attempt = h.store.read()["batch"]["capabilities"]["audit"]["attempts"][-1]
    assert attempt["detail"] == runner.detail
    assert rows(request.session.raw)[-1] == {
        "success": True,
        "session_id": request.session.root.name,
        "detail": runner.detail,
    }


@pytest.mark.parametrize("paused", ["phase", "next_phase"])
def test_paused_startup_reconciles_stale_owner_without_route_or_workflow_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    paused: str,
) -> None:
    h = ready(tmp_path, monkeypatch)
    lifecycle = service(h)
    original = lifecycle.start("audit")
    metadata = h.paths.sessions / original["session_id"] / "meta.json"
    retained = json.loads(metadata.read_text())
    retained.update(pid=99999999, process_start="absent-process")
    metadata.write_text(json.dumps(retained))
    h.change(**{paused: "paused"})
    configure(h, "", "")
    before = h.store.read()
    outcome = h.supervisor().run()
    state = h.store.read()
    (attempt,) = state["batch"]["capabilities"]["audit"]["attempts"]
    assert attempt["id"] == original["id"] and attempt["status"] == "failed"
    assert attempt["finished_at"] is not None and attempt["detail"]
    assert outcome.sessions_attempted == 0
    assert h.driver.requests == [] and h.runner.requests == []
    assert _workflow(state) == _workflow(before)
    assert len(reconcile_metrics(h.paths)) == 1
    h.supervisor().run()
    assert h.store.read() == state
    assert len(reconcile_metrics(h.paths)) == 1
    runner = EvidenceRunner(h)
    retried = lifecycle.retry("audit", runner)
    old, new = retried["batch"]["capabilities"]["audit"]["attempts"]
    assert old == attempt and new["status"] == "succeeded"
    assert new["id"] != old["id"] and new["session_id"] != old["session_id"]
    assert len(runner.requests) == 1 and len(reconcile_metrics(h.paths)) == 2
    assert _workflow(retried) == _workflow(before)


def test_live_owner_rejects_retry_without_changing_state_or_session_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = ready(tmp_path, monkeypatch)
    lifecycle = service(h)
    attempt = lifecycle.start("audit")
    before = h.store.read()
    evidence = {
        path: path.read_bytes()
        for path in h.paths.sessions.rglob("*")
        if path.is_file()
    }
    runner = EvidenceRunner(h)
    assert lifecycle.reconcile("audit") == before
    with pytest.raises(ValueError):
        lifecycle.retry("audit", runner)
    assert h.store.read() == before
    assert before["batch"]["capabilities"]["audit"]["attempts"] == [attempt]
    assert {path: path.read_bytes() for path in evidence} == evidence
    assert runner.requests == []
