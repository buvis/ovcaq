"""Preserve native thread identity when supervised observations are rebound."""

from __future__ import annotations

import json
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ovcaq.config import (
    AgentSettings,
    PhaseSettings,
    RuntimeSettings,
    SupervisorSettings,
)
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import (
    FailureClass,
    ObservationType,
    SessionSummary,
    observation_from_record,
)
from ovcaq.paths import RuntimePaths, ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.decision import SupervisorPolicy
from ovcaq.runtime.supervisor import Supervisor
from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore


class Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()

    def wait(self, event: threading.Event, timeout: float) -> bool:
        return event.wait(timeout)


def _emitter(root: Path, thread: str, exit_code: int) -> tuple[tuple[str, str], bytes]:
    records = [
        {"type": "thread.started", "thread_id": "native-a"},
        {"type": "thread.started", "thread_id": thread},
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 100,
                "cached_input_tokens": 20,
                "output_tokens": 25,
                "cache_write_input_tokens": 0,
            },
        },
    ]
    raw = "".join(json.dumps(record) + "\n" for record in records).encode()
    emitter = root / "emitter.py"
    emitter.write_text(
        f"import json, sys\nfor record in {records!r}:\n"
        f"    print(json.dumps(record), flush=True)\nsys.exit({exit_code})\n"
    )
    command = (sys.executable, str(emitter))
    (root / "ovcaq.toml").write_text(
        'agent = "codex"\n[agents.codex]\n'
        f"command = {json.dumps(command)}\n"
        'tiers = { standard = "model-s", deep = "model-o" }\n'
    )
    return command, raw


def _state_store(root: Path, paths: RuntimePaths) -> StateStore:
    store = StateStore(paths.state_file)
    state = new_state(repo_root=root)
    state["batch"].update(id="batch-1", status="running")
    state["work"]["prd"] = "00001-fixture.md"
    store.initialize(state)
    backlog = root / "docs/dev/project-management/prds/backlog"
    backlog.mkdir(parents=True, exist_ok=True)
    (backlog / "00001-fixture.md").write_text("# Fixture PRD\n")
    return store


def _supervisor(
    root: Path, monkeypatch: pytest.MonkeyPatch, thread: str, exit_code: int
) -> tuple[Supervisor, RuntimePaths, bytes]:
    for name in ("HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME"):
        monkeypatch.setenv(name, str(root / name.lower()))
    command, raw = _emitter(root, thread, exit_code)
    paths = ensure_runtime_layout(
        resolve_runtime_paths(root, xdg_state_home=root / "xdg")
    )
    store = _state_store(root, paths)
    settings = SupervisorSettings(
        RuntimeSettings(paths, 0.05, 1_000_000, 10_000_000, 0),
        SupervisorPolicy(0, 0, 0, 0.01, 0.01, 3),
        {
            phase: PhaseSettings("standard", "medium", 10)
            for phase in ("build", "review", "done")
        },
    )
    return (
        Supervisor(
            root,
            store=store,
            driver=CodexDriver(
                AgentSettings(
                    "codex", command, {"standard": "model-s", "deep": "model-o"}, {}, {}
                ),
                run_id="run-1",
            ),
            settings=settings,
            capability_runner=lambda _: pytest.fail("unexpected capability"),
            clock=Clock(),
            sleeper=lambda _: None,
        ),
        paths,
        raw,
    )


def _assert_retained_evidence(
    summary: SessionSummary, paths: RuntimePaths, raw: bytes
) -> None:
    assert summary.session_id is not None
    bundle = paths.sessions / summary.session_id
    assert (bundle / "raw.jsonl").read_bytes() == raw
    observations = [
        observation_from_record(json.loads(line))
        for line in (bundle / "normalized.jsonl").read_text().splitlines()
    ]
    assert observations
    assert all(event.session_id == summary.session_id for event in observations)
    assert any(event.type == ObservationType.SESSION_STARTED for event in observations)
    assert any(
        event.type
        in (ObservationType.SESSION_COMPLETED, ObservationType.SESSION_FAILED)
        for event in observations
    )


@pytest.mark.parametrize("exit_code", [0, 9])
def test_distinct_native_threads_fail_after_supervised_session_rebinding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exit_code: int
) -> None:
    supervisor, paths, raw = _supervisor(tmp_path, monkeypatch, "native-b", exit_code)
    result = supervisor.run_once()
    assert result.state_error is None
    assert result.summary is not None
    _assert_retained_evidence(result.summary, paths, raw)
    assert result.summary.success is False
    assert result.summary.failure_class == FailureClass.UNKNOWN


def test_repeated_native_thread_succeeds_with_terminal_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    supervisor, paths, raw = _supervisor(tmp_path, monkeypatch, "native-a", 0)
    result = supervisor.run_once()
    assert result.state_error is None
    assert result.summary is not None
    _assert_retained_evidence(result.summary, paths, raw)
    assert result.summary.success is True
    assert result.summary.failure_class is None
