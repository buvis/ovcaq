from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from packaging_support import InstalledWheel, isolated_environment

from ovcaq.runtime.registry import process_identity

COMPLETED = {
    "filename": "finished.md",
    "cycles": 1,
    "autonomous_decisions": 0,
    "escalated_decisions": 0,
    "tasks_completed": 0,
    "tasks_total": 0,
}

FAKE_DRIVER = r"""
import json, os, subprocess, sys, time
from pathlib import Path
from ovcaq.paths import resolve_runtime_paths
from ovcaq.state.store import StateStore
root = Path.cwd()
store = StateStore(resolve_runtime_paths(root).state_file)
phase = store.read()["work"]["phase"]
mode = os.environ.get("OVCAQ_TEST_DRIVER_MODE", "advance")
grandchild = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"]) if mode == "hold" else None
with (root / "invocations.jsonl").open("a") as stream:
    stream.write(json.dumps({"phase": phase, "pid": os.getpid(), "argv": sys.argv,
                            "grandchild": grandchild.pid if grandchild else None}) + "\n")
print(json.dumps({"type": "system", "subtype": "init", "session_id": "fake-" + phase}), flush=True)
if mode == "hold":
    time.sleep(60)
elif mode == "advance":
    def advance(state):
        if phase == "build":
            state["work"].update(phase="review", next_phase="review")
        elif phase == "review":
            state["work"].update(phase="done", next_phase="done")
            state["work"]["completed_phases"].append("review")
        elif phase == "done":
            state["work"].update(phase="done", next_phase="")
            state["batch"]["completed_prds"].append(json.loads((root / "completed.json").read_text()))
    store.transaction(advance)
failed = mode == "fail"
print(json.dumps({"type": "result", "subtype": "error" if failed else "success",
                  "is_error": failed, "session_id": "fake-" + phase,
                  "result": "Synthetic agent failure" if failed else
                            "Everything completed; the batch is drained."}), flush=True)
raise SystemExit(23 if mode == "fail" else 0)
"""

SEED = r"""
import json, sys
from pathlib import Path
from ovcaq.paths import resolve_runtime_paths
from ovcaq.state.store import StateStore
root = Path(sys.argv[1])
def seed(state):
    state["batch"].update(id="installed-supervisor", status="running")
    phase = sys.argv[2] if len(sys.argv) > 2 else "build"
    state["work"].update(phase=phase, next_phase=phase)
    if phase == "done":
        state["work"]["completed_phases"].append("review")
StateStore(resolve_runtime_paths(root).state_file).transaction(seed)
"""

CAPABILITY_SEED = r"""
import copy, json, os, sys
from pathlib import Path
from ovcaq.paths import resolve_runtime_paths
from ovcaq.runtime.registry import process_identity
from ovcaq.runtime.session import SessionMetadata, create_session
from ovcaq.state.store import StateStore
root, live_pid = Path(sys.argv[1]), int(sys.argv[2])
name = sys.argv[3] if len(sys.argv) > 3 else "agoge"
paths = resolve_runtime_paths(root)
attempt = {"id": "attempt-1", "status": "failed",
           "started_at": "2026-10-02T10:00:00Z", "finished_at": "2026-10-02T10:01:00Z",
           "session_id": None, "detail": "failed"}
if live_pid:
    identity = process_identity(live_pid)
    assert identity is not None
    metadata = SessionMetadata(schema_version=1, run_id="live-capability",
        session_id="live-agoge", agent="capability:agoge", pid=identity.pid,
        process_start=identity.started, started_at="2026-10-02T10:00:00Z")
    create_session(paths, metadata)
    attempt.update(status="running", finished_at=None, session_id="live-agoge", detail=None)
def seed(state):
    state["work"].update(phase="done", next_phase="")
    state["batch"]["completed_prds"] = [json.loads((root / "completed.json").read_text())]
    state["batch"]["capabilities"] = {name: {"required": True, "launcher": "fake",
        "plugin": "fake/" + name, "version": "1", "failure": "attention",
        "status": "running" if live_pid else "failed", "attempts": [attempt]}}
    unrelated = copy.deepcopy(state["batch"]["capabilities"][name])
    unrelated.update(plugin="fake/untouched", status="pending", attempts=[])
    state["batch"]["capabilities"]["untouched"] = unrelated
StateStore(paths.state_file).transaction(seed)
"""

CAPABILITY_RETRY = r"""
import json, sys
from pathlib import Path
from ovcaq.cli import build_parser
from ovcaq.runtime.capability import CapabilityExecution
from ovcaq.supervisor_cli import dispatch_supervisor
class Runner:
    def run(self, request):
        (Path(sys.argv[1]) / "runner-called").write_text("entered")
        (Path(sys.argv[1]) / "runner-called").write_text(request.name)
        success = sys.argv[2] == "success"
        return CapabilityExecution(success, request.session.root.name,
                                   None if success else sys.argv[4])
root = Path(sys.argv[1])
args = build_parser().parse_args(["--root", str(root), "--json", "capability", "retry", sys.argv[3]])
value, revision, mutation, code = dispatch_supervisor(args, root, capability_runner=Runner())
if sys.argv[2] == "success":
    assert revision == value["revision"] and mutation is True and code == 0
print(json.dumps(value))
raise SystemExit(code)
"""


def _run(
    installed: InstalledWheel,
    environment: dict[str, str],
    cwd: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(installed.console_script), "--json", *arguments],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _success(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    value = json.loads(result.stdout)
    assert isinstance(value, dict)
    return value


def _failure(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    assert result.returncode != 0
    assert result.stdout == ""
    assert "Traceback" not in result.stderr
    payload = json.loads(result.stderr)
    assert set(payload) == {"ok", "error"}
    assert payload["ok"] is False
    assert set(payload["error"]) == {"code", "message", "path"}
    assert isinstance(payload["error"]["code"], str) and payload["error"]["code"]
    assert isinstance(payload["error"]["message"], str) and payload["error"]["message"]
    assert payload["error"]["path"] is None or isinstance(payload["error"]["path"], str)
    return payload


def _python(
    installed: InstalledWheel,
    environment: dict[str, str],
    root: Path,
    script: str,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(installed.python), "-I", "-c", script, str(root), *arguments],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result


def _retry_result(
    installed: InstalledWheel,
    environment: dict[str, str],
    root: Path,
    outcome: str,
    name: str,
    detail: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(installed.python),
            "-I",
            "-c",
            CAPABILITY_RETRY,
            str(root),
            outcome,
            name,
            detail,
        ],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def _project(
    installed: InstalledWheel,
    tmp_path: Path,
    *,
    seed: bool = True,
) -> tuple[Path, Path, dict[str, str]]:
    root = tmp_path / "project"
    cwd = root / "arbitrary" / "nested"
    cwd.mkdir(parents=True)
    environment = isolated_environment(tmp_path / "isolation")
    environment["PATH"] = os.pathsep.join(
        (str(installed.console_script.parent), environment["PATH"])
    )
    fake = root / "configured runner"
    fake.write_text(f"#!{installed.python}\n{FAKE_DRIVER}", encoding="utf-8")
    fake.chmod(0o700)
    (root / "completed.json").write_text(json.dumps(COMPLETED), encoding="utf-8")
    (root / "ovcaq.toml").write_text(
        'agent = "claude"\n[agents.claude]\n'
        f'command = [{json.dumps(str(fake))}, "literal ; $HOME argument"]\n'
        'tiers = { standard = "model-s", deep = "model-o" }\n'
        '[agents.claude.options]\npermission_mode = "auto"\n'
        + "".join(
            f"[phases.{phase}]\ntimeout_seconds = 5\n"
            for phase in ("build", "review", "done")
        ),
        encoding="utf-8",
    )
    _success(_run(installed, environment, cwd, "init"))
    if seed:
        _python(installed, environment, root, SEED)
    return root, cwd, environment


def _state(root: Path) -> dict[str, Any]:
    return json.loads(
        (root / "docs/dev/project-management/ovcaq/state.json").read_text()
    )


def _workflow(state: dict[str, Any]) -> list[Any]:
    return [
        state["work"],
        state["tasks"],
        state["review"],
        state["batch"]["completed_prds"],
    ]


def _wait_for_driver(root: Path, process: subprocess.Popen[str]) -> int:
    marker = root / "invocations.jsonl"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        assert process.poll() is None, process.communicate()
        if marker.exists() and marker.read_text().strip():
            return int(json.loads(marker.read_text().splitlines()[0])["pid"])
        time.sleep(0.02)
    pytest.fail("installed foreground run did not start its driver")


@contextmanager
def _running(
    installed: InstalledWheel,
    environment: dict[str, str],
    root: Path,
    cwd: Path,
) -> Iterator[tuple[subprocess.Popen[str], int]]:
    environment = environment | {"OVCAQ_TEST_DRIVER_MODE": "hold"}
    process = subprocess.Popen(
        [str(installed.console_script), "--json", "run", "--no-tui"],
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        yield process, _wait_for_driver(root, process)
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.communicate(timeout=10)
        finally:
            marker = root / "invocations.jsonl"
            if marker.exists():
                for line in marker.read_text().splitlines():
                    row = json.loads(line)
                    for pid in (row["pid"], row["grandchild"]):
                        if pid:
                            try:
                                os.kill(pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
            process.communicate(timeout=5)


def _assert_process_stopped(pid: int) -> None:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if process_identity(pid) is None:
            return
        time.sleep(0.02)
    pytest.fail(f"owned driver {pid} survived supervisor termination")


def _assert_evidence(root: Path, phases: list[str]) -> None:
    sessions = list((root / "docs/dev/project-management/ovcaq/sessions").iterdir())
    assert len(sessions) == len(phases)
    observed = []
    for session in sessions:
        metadata = json.loads((session / "meta.json").read_text())
        assert set(metadata) == {
            "schema_version",
            "run_id",
            "session_id",
            "agent",
            "pid",
            "process_start",
            "started_at",
        }
        assert metadata["schema_version"] == 1 and metadata["agent"] == "claude"
        assert metadata["session_id"] == session.name
        assert isinstance(metadata["pid"], int) and metadata["pid"] > 0
        assert metadata["process_start"] and metadata["run_id"]
        datetime.fromisoformat(metadata["started_at"])
        rows = [
            json.loads(line)
            for line in (session / "raw.jsonl").read_text().splitlines()
        ]
        assert rows[0]["type"] == "system" and rows[0]["subtype"] == "init"
        assert rows[-1]["type"] == "result" and rows[-1]["is_error"] is False
        assert rows[-1]["result"] == "Everything completed; the batch is drained."
        observed.append(rows[-1]["session_id"].removeprefix("fake-"))
    assert sorted(observed) == sorted(phases)


def _assert_configured_invocations(root: Path, phases: list[str]) -> None:
    rows = [
        json.loads(line)
        for line in (root / "invocations.jsonl").read_text().splitlines()
    ]
    assert [row["phase"] for row in rows] == phases
    for row in rows:
        model = "model-o" if row["phase"] == "review" else "model-s"
        assert row["argv"] == [
            str(root / "configured runner"),
            "literal ; $HOME argument",
            "-p",
            "--permission-mode",
            "auto",
            "--model",
            model,
            "--effort",
            "high",
            "--output-format",
            "stream-json",
            "--verbose",
            "/autopilot:run-autopilot",
        ]


def _assert_current_attempt(
    root: Path,
    before: dict[str, Any],
    after: dict[str, Any],
    name: str,
    started: datetime,
    detail: str | None,
) -> None:
    old = before["batch"]["capabilities"][name]["attempts"]
    attempts = after["batch"]["capabilities"][name]["attempts"]
    assert len(attempts) == len(old) + 1 and attempts[:-1] == old
    assert len({attempt["id"] for attempt in attempts}) == len(attempts)
    last = attempts[-1]
    assert (
        started - timedelta(seconds=1)
        <= datetime.fromisoformat(last["started_at"])
        <= datetime.fromisoformat(last["finished_at"])
        <= datetime.now(UTC) + timedelta(seconds=1)
    )
    assert last["detail"] == detail
    session = root / "docs/dev/project-management/ovcaq/sessions" / last["session_id"]
    metadata = json.loads((session / "meta.json").read_text())
    assert metadata["session_id"] == last["session_id"]
    assert metadata["agent"] == f"capability:{name}"
    assert (
        after["batch"]["capabilities"]["untouched"]
        == before["batch"]["capabilities"]["untouched"]
    )
    assert (root / "runner-called").read_text() == name


def test_installed_help_and_inventory_share_lifecycle_commands(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    root, cwd, environment = _project(installed_wheel, tmp_path)
    help_result = _run(installed_wheel, environment, cwd, "--help")
    assert help_result.returncode == 0 and help_result.stderr == ""
    for command in ("run", "pause", "resume", "stop", "capability"):
        assert command in help_result.stdout
    script = "from ovcaq.cli import command_inventory, render_command_reference; import json; print(json.dumps([command_inventory(), render_command_reference()]))"
    inventory, reference = json.loads(
        _python(installed_wheel, environment, root, script).stdout
    )
    assert [
        line for line in reference.splitlines() if line.startswith("ovcaq ")
    ] == inventory
    for command in (" run", " pause", " resume", " stop", " capability retry"):
        assert any(command in line for line in inventory)


@pytest.mark.parametrize("agent_option", [(), ("--agent", "claude")])
@pytest.mark.parametrize("phase", ["build", "review", "done"])
def test_installed_foreground_run_drains_committed_build_review_and_done(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    agent_option: tuple[str, ...],
    phase: str,
) -> None:
    root, cwd, environment = _project(installed_wheel, tmp_path)
    _python(installed_wheel, environment, root, SEED, phase)
    payload = _success(
        _run(installed_wheel, environment, cwd, "run", "--no-tui", *agent_option)
    )
    assert set(payload) == {"decision", "reason", "sessions_attempted"}
    assert payload["decision"] == "complete"
    assert isinstance(payload["reason"], str) and payload["reason"]
    phases = ["build", "review", "done"][["build", "review", "done"].index(phase) :]
    assert payload["sessions_attempted"] == len(phases)
    _assert_configured_invocations(root, phases)
    _assert_evidence(root, phases)
    state = _state(root)
    assert state["work"]["phase"] == "done" and state["work"]["next_phase"] == ""
    assert "review" in state["work"]["completed_phases"]
    assert state["batch"]["completed_prds"] == [COMPLETED]
    assert not (root / "docs/dev/project-management/ovcaq/run.json").exists()


def test_installed_init_can_run_without_seeding_batch_identity(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    root, cwd, environment = _project(installed_wheel, tmp_path, seed=False)
    initial = _state(root)
    assert initial["batch"]["started_at"] is None
    fake = root / "configured runner"
    fake.write_text(
        f"#!{installed_wheel.python}\n"
        + FAKE_DRIVER.replace(
            'phase = store.read()["work"]["phase"]',
            'phase = store.read()["work"]["phase"]\n'
            '(root / "first-session-state.json").write_text(json.dumps(store.read()))\n'
            'assert store.read()["batch"]["id"].strip()\n'
            'assert store.read()["batch"]["status"] == "running"',
        ),
        encoding="utf-8",
    )
    environment["OVCAQ_TEST_DRIVER_MODE"] = "uncommitted"
    result = _run(installed_wheel, environment, cwd, "run", "--no-tui")
    assert "Traceback" not in result.stderr
    assert (root / "first-session-state.json").exists(), result.stderr
    observed = json.loads((root / "first-session-state.json").read_text())
    assert observed["batch"]["id"].strip()
    assert observed["batch"]["status"] == "running"
    datetime.fromisoformat(observed["batch"]["started_at"])
    assert _workflow(observed) == _workflow(initial)
    metrics = [
        json.loads(line)
        for line in (root / "docs/dev/project-management/ovcaq/metrics.jsonl")
        .read_text()
        .splitlines()
    ]
    assert metrics and {metric["batch_id"] for metric in metrics} == {
        observed["batch"]["id"]
    }


def test_installed_unknown_agent_is_rejected_without_launching_configured_driver(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    root, cwd, environment = _project(installed_wheel, tmp_path)
    before = _state(root)
    _failure(
        _run(
            installed_wheel,
            environment,
            cwd,
            "run",
            "--no-tui",
            "--agent",
            "unavailable-agent",
        )
    )
    assert not (root / "invocations.jsonl").exists()
    assert _state(root) == before


def test_installed_pause_resume_and_invalid_run_use_json_envelopes_from_nested_cwd(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    root, cwd, environment = _project(installed_wheel, tmp_path)
    before = _state(root)
    paused = _success(
        _run(installed_wheel, environment, cwd, "pause", "--reason", "maintenance")
    )
    assert set(paused) == {"ok", "revision", "result"}
    assert paused["ok"] is True and paused["result"] == _state(root)
    assert paused["revision"] == paused["result"]["revision"] > before["revision"]
    assert paused["result"]["control"]["pause_requested"] is True
    assert paused["result"]["control"]["pause_reason"]["detail"] == "maintenance"
    _run(installed_wheel, environment, cwd, "run", "--no-tui")
    assert not (root / "invocations.jsonl").exists()
    assert _state(root)["control"]["pause_requested"] is True
    resumed = _success(_run(installed_wheel, environment, cwd, "resume"))
    assert set(resumed) == {"ok", "revision", "result"}
    assert resumed["ok"] is True and resumed["result"] == _state(root)
    assert resumed["revision"] == resumed["result"]["revision"] > paused["revision"]
    assert resumed["result"]["control"]["pause_requested"] is False
    assert resumed["result"]["control"]["pause_reason"] is None
    assert resumed["result"]["work"] == before["work"]
    _success(_run(installed_wheel, environment, cwd, "run", "--no-tui"))
    _assert_configured_invocations(root, ["build", "review", "done"])


@pytest.mark.parametrize("mode", ["uncommitted", "fail"])
def test_installed_success_prose_cannot_complete_uncommitted_work(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    mode: str,
) -> None:
    root, cwd, environment = _project(installed_wheel, tmp_path)
    environment["OVCAQ_TEST_DRIVER_MODE"] = mode
    result = _run(installed_wheel, environment, cwd, "run", "--no-tui")
    if mode == "uncommitted":
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["decision"] == "pause"
        assert payload["sessions_attempted"] > 1
    else:
        assert result.returncode != 0
    assert "Traceback" not in result.stdout + result.stderr
    state = _state(root)
    assert state["work"]["phase"] == "build"
    assert state["batch"]["completed_prds"] == []
    rows = [
        json.loads(line)
        for line in (root / "invocations.jsonl").read_text().splitlines()
    ]
    assert rows and {row["phase"] for row in rows} == {"build"}


@pytest.mark.parametrize("number", [signal.SIGINT, signal.SIGTERM, signal.SIGHUP])
def test_installed_foreground_signals_return_shell_status_and_stop_the_driver(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    number: signal.Signals,
) -> None:
    root, cwd, environment = _project(installed_wheel, tmp_path)
    with _running(installed_wheel, environment, root, cwd) as (process, driver_pid):
        process.send_signal(number)
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 128 + number
        assert "Traceback" not in stdout + stderr
        _assert_process_stopped(driver_pid)
        grandchild = json.loads(
            (root / "invocations.jsonl").read_text().splitlines()[0]
        )["grandchild"]
        assert grandchild is not None
        _assert_process_stopped(grandchild)
    assert not (root / "docs/dev/project-management/ovcaq/run.json").exists()


def test_installed_stop_signals_the_verified_foreground_supervisor(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    root, cwd, environment = _project(installed_wheel, tmp_path)
    with _running(installed_wheel, environment, root, cwd) as (process, driver_pid):
        record = json.loads(
            (root / "docs/dev/project-management/ovcaq/run.json").read_text()
        )
        assert set(record) == {
            "schema_version",
            "run_id",
            "session_id",
            "agent",
            "pid",
            "process_start",
            "started_at",
        }
        assert record["pid"] == process.pid
        script = "from ovcaq.runtime.registry import process_identity; import sys; print(process_identity(int(sys.argv[2])).started)"
        assert (
            record["process_start"]
            == _python(
                installed_wheel, environment, root, script, str(process.pid)
            ).stdout.strip()
        )
        payload = _success(_run(installed_wheel, environment, cwd, "stop"))
        assert payload == {"pid": process.pid, "signal": 15}
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 143
        assert "Traceback" not in stdout + stderr
        _assert_process_stopped(driver_pid)


@pytest.mark.parametrize(
    "damage", ["missing", "malformed", "mismatched", "unrelated-pid"]
)
def test_installed_stop_rejects_untrusted_identity_without_signalling_live_processes(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    damage: str,
) -> None:
    root, cwd, environment = _project(installed_wheel, tmp_path)
    with _running(installed_wheel, environment, root, cwd) as (process, driver_pid):
        metadata = root / "docs/dev/project-management/ovcaq/run.json"
        original = metadata.read_bytes()
        unrelated = subprocess.Popen(
            [str(installed_wheel.python), "-c", "import sys; sys.stdin.read()"],
            stdin=subprocess.PIPE,
        )
        try:
            if damage == "missing":
                metadata.unlink()
            elif damage == "malformed":
                metadata.write_text("{malformed")
            else:
                record = json.loads(original)
                record["process_start"] = "another-unrelated-start-token"
                if damage == "unrelated-pid":
                    record["pid"] = unrelated.pid
                    script = "from ovcaq.runtime.registry import process_identity; import sys; print(process_identity(int(sys.argv[2])).started)"
                    record["process_start"] = _python(
                        installed_wheel, environment, root, script, str(unrelated.pid)
                    ).stdout.strip()
                metadata.write_text(json.dumps(record))
            failure = _failure(_run(installed_wheel, environment, cwd, "stop"))
            assert failure["error"]["code"] != "usage"
            assert process.poll() is None
            assert unrelated.poll() is None
            os.kill(driver_pid, 0)
        finally:
            metadata.write_bytes(original)
            if unrelated.poll() is None:
                unrelated.terminate()
            unrelated.communicate(timeout=5)


@pytest.mark.parametrize("name", ["agoge", "archive"])
def test_installed_capability_retry_succeeds_without_reopening_drained_workflow(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    name: str,
) -> None:
    root, _cwd, environment = _project(installed_wheel, tmp_path)
    _python(installed_wheel, environment, root, CAPABILITY_SEED, "0", name)
    before = _state(root)
    started = datetime.now(UTC)
    result = _python(
        installed_wheel, environment, root, CAPABILITY_RETRY, "success", name, ""
    )
    after = _state(root)
    assert json.loads(result.stdout) == after
    assert _workflow(after) == _workflow(before)
    capability = after["batch"]["capabilities"][name]
    assert capability["status"] == "succeeded"
    assert len(capability["attempts"]) == 2
    assert (
        capability["attempts"][0]
        == before["batch"]["capabilities"][name]["attempts"][0]
    )
    assert capability["attempts"][-1]["status"] == "succeeded"
    _assert_current_attempt(root, before, after, name, started, None)


@pytest.mark.parametrize(
    "name,detail", [("agoge", "remote denied Ω"), ("archive", "archive timed out: 17")]
)
def test_installed_fake_capability_failure_returns_nonzero_and_preserves_drain(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    name: str,
    detail: str,
) -> None:
    root, _cwd, environment = _project(installed_wheel, tmp_path)
    _python(installed_wheel, environment, root, CAPABILITY_SEED, "0", name)
    before = _state(root)
    started = datetime.now(UTC)
    result = _retry_result(installed_wheel, environment, root, "failure", name, detail)
    assert result.returncode != 0
    after = _state(root)
    assert _workflow(after) == _workflow(before)
    capability = after["batch"]["capabilities"][name]
    assert capability["status"] == "failed"
    assert len(capability["attempts"]) == 2
    assert capability["attempts"][-1]["status"] == "failed"
    assert capability["attempts"][-1]["detail"] == detail
    _assert_current_attempt(root, before, after, name, started, detail)
    second = _retry_result(installed_wheel, environment, root, "failure", name, detail)
    assert second.returncode != 0
    repeated = _state(root)
    _assert_current_attempt(root, after, repeated, name, started, detail)
    assert _workflow(repeated) == _workflow(before)


def test_installed_live_capability_owner_rejects_an_injected_runner_before_execution(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    root, _cwd, environment = _project(installed_wheel, tmp_path)
    _python(installed_wheel, environment, root, CAPABILITY_SEED, str(os.getpid()))
    before = _state(root)
    result = _retry_result(installed_wheel, environment, root, "success", "agoge", "")
    assert result.returncode != 0
    assert not (root / "runner-called").exists()
    assert _state(root) == before


@pytest.mark.parametrize("live", [False, True])
def test_installed_capability_retry_reports_unavailable_runner_or_live_owner_as_json(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    live: bool,
) -> None:
    root, cwd, environment = _project(installed_wheel, tmp_path)
    _python(
        installed_wheel,
        environment,
        root,
        CAPABILITY_SEED,
        str(os.getpid() if live else 0),
    )
    before = _state(root)
    failure = _failure(
        _run(installed_wheel, environment, cwd, "capability", "retry", "agoge")
    )
    assert failure["error"]["code"] != "usage"
    after = _state(root)
    assert _workflow(after) == _workflow(before)
    if live:
        assert after == before
    else:
        assert after["batch"]["capabilities"]["agoge"]["status"] == "failed"
