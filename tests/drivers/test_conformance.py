from __future__ import annotations

import json
import os
import select
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import AgentDriver, LaunchRequest
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import FailureClass, ObservationType, Usage
from ovcaq.events.reducer import reduce_session
from ovcaq.events.tail import NormalizedEventWriter, RawFirstDecoder
from ovcaq.runtime.process import OwnedProcess
from ovcaq.runtime.session import SessionEvidenceWriter

FIXTURES = Path(__file__).parents[1] / "fixtures"
CODEX_PROMPT = """$run-autopilot
Read the committed OVCAQ state to determine the current phase. Use `ovcaq state`
and `ovcaq workflow` commands for all durable mutations. Perform only the
current phase, commit exactly one successful phase handoff through the OVCAQ
workflow command, then exit the session. Never edit state.json directly. Do not
start a second phase in this session. Completion is determined by committed
state, not your final message. Do not install, upgrade, or modify launcher
plugins or marketplace content."""


@pytest.fixture(params=["claude", "codex"])
def adapter(request: pytest.FixtureRequest) -> str:
    return request.param


def driver_for(
    adapter: str, tmp_path: Path, command: tuple[str, ...] = ("fixture",)
) -> AgentDriver:
    settings = AgentSettings(
        name=adapter,
        command=command,
        tiers={"standard": "fixture-model"},
        environment={
            "HOME": str(tmp_path / "home"),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "XDG_STATE_HOME": str(tmp_path / "state"),
        },
        options={"permission_mode": "auto"} if adapter == "claude" else {},
    )
    return (ClaudeDriver if adapter == "claude" else CodexDriver)(
        settings, run_id="shared-run"
    )


def request_for(tmp_path: Path, phase: str = "build") -> LaunchRequest:
    return LaunchRequest(
        tmp_path,
        phase,
        "literal $(never) | prompt\npassword=prompt-secret",
        "standard",
        "high",
        3,
        tmp_path / "session",
    )


def records(
    adapter: str, *, detail: str | None = None, usage: bool = True
) -> list[dict]:
    if adapter == "claude":
        result = {
            "type": "result",
            "session_id": "shared-session",
            "subtype": "success" if detail is None else "error_during_execution",
            "is_error": detail is not None,
            "result": detail or "Complete.",
        }
        if usage:
            result["usage"] = {
                "input_tokens": 20,
                "cache_read_input_tokens": 100,
                "cache_creation_input_tokens": 0,
                "output_tokens": 30,
            }
        return [
            {"type": "system", "subtype": "init", "session_id": "shared-session"},
            result,
        ]
    terminal = (
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 120,
                "cached_input_tokens": 100,
                "cache_write_input_tokens": 0,
                "output_tokens": 30,
                "reasoning_output_tokens": 10,
            },
        }
        if detail is None
        else {"type": "turn.failed", "error": {"message": detail}}
    )
    return [{"type": "thread.started", "thread_id": "shared-session"}, terminal]


def decoded(driver: AgentDriver, inputs: list[dict]):
    return tuple(
        event for record in inputs for event in driver.decode(json.dumps(record))
    )


def launch_suffix(adapter: str, tmp_path: Path, request: LaunchRequest):
    return (
        (
            "-p",
            "--permission-mode",
            "auto",
            "--model",
            "fixture-model",
            "--effort",
            "high",
            "--output-format",
            "stream-json",
            "--verbose",
            request.prompt,
        )
        if adapter == "claude"
        else (
            "--ask-for-approval",
            "never",
            "exec",
            "--json",
            "--sandbox",
            "workspace-write",
            "-C",
            str(tmp_path),
            "-m",
            "fixture-model",
            "-c",
            'model_reasoning_effort="high"',
            "--",
            request.prompt,
        )
    )


@pytest.mark.parametrize("phase", ["build", "review", "done"])
def test_exact_launch_and_default_prompt(
    adapter: str, tmp_path: Path, phase: str
) -> None:
    driver = driver_for(adapter, tmp_path, ("fixture", "literal-wrapper"))
    request = request_for(tmp_path, phase)
    spec = driver.build_launch(request)
    prefix = ("fixture", "literal-wrapper")
    suffix = launch_suffix(adapter, tmp_path, request)
    assert spec.argv == prefix + suffix
    assert spec.cwd == tmp_path
    assert (
        spec.raw_format
        == {"claude": "claude-stream-json-v1", "codex": "codex-exec-json-v1"}[adapter]
    )
    assert dict(spec.env) == (
        {
            "HOME": str(tmp_path / "home"),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "XDG_STATE_HOME": str(tmp_path / "state"),
        }
        | (
            {"CLAUDE_UNATTENDED": "1", "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0"}
            if adapter == "claude"
            else {}
        )
    )
    assert driver.default_prompt(phase) == (
        "/autopilot:run-autopilot" if adapter == "claude" else CODEX_PROMPT
    )


@pytest.mark.parametrize("exit_code", [0, 7])
def test_decode_summary_cache_split_and_nonzero_completion(
    adapter: str, tmp_path: Path, exit_code: int
) -> None:
    driver = driver_for(adapter, tmp_path)
    events = decoded(driver, records(adapter))
    assert events[0].type == ObservationType.SESSION_STARTED
    assert events[-1].type == ObservationType.SESSION_COMPLETED
    assert all(
        event.provider == adapter and event.run_id == "shared-run" for event in events
    )
    assert all(event.protocol_version == 1 for event in events)
    summary = driver.summarize(events, exit_code)
    assert summary == reduce_session(events, exit_code).summary
    assert summary.success is True
    assert summary.session_id == "shared-session"
    assert summary.failure_class is None
    assert summary.usage == Usage(
        input_tokens=20,
        output_tokens=30,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=100,
    )
    # Replaying cumulative telemetry must not double counters.
    assert driver.summarize(events + events, exit_code).usage == summary.usage
    assert driver.summarize((), 0).success is False


@pytest.mark.parametrize(
    ("detail", "failure"),
    [
        ("Unauthorized", FailureClass.AUTHENTICATION),
        ("Permission denied", FailureClass.PERMISSION),
        ("Connection refused", FailureClass.CONNECTIVITY),
        ("Request timed out", FailureClass.TIMEOUT),
        ("Agent failed", FailureClass.AGENT),
        ("Usage limit reached", FailureClass.RATE_LIMIT),
    ],
)
def test_actual_failure_decoding(
    adapter: str, tmp_path: Path, detail: str, failure: FailureClass
) -> None:
    driver = driver_for(adapter, tmp_path)
    events = decoded(driver, records(adapter, detail=detail, usage=False))
    summary = driver.summarize(events, 1)
    assert summary == reduce_session(events, 1).summary
    assert summary.success is False
    assert summary.failure_class == failure
    assert summary.rate_limit_reset_at is None


@pytest.mark.parametrize("has_reset", [False, True])
def test_native_rate_limit_deadline(
    adapter: str, tmp_path: Path, has_reset: bool
) -> None:
    driver = driver_for(adapter, tmp_path)
    # Native relative reset syntax differs; inject only at the adapter edge.
    detail = "Usage limit reached" + ("; retry after 60 seconds." if has_reset else ".")
    inputs = records(adapter, detail=detail, usage=False)
    if adapter == "claude" and has_reset:
        inputs.insert(
            1,
            {
                "type": "rate_limit_event",
                "rate_limit_info": {
                    "status": "rejected",
                    "resetsAt": int(time.time()) + 60,
                    "rateLimitType": "five_hour",
                },
            },
        )
    events = decoded(driver, inputs)
    summary = driver.summarize(events, 1)
    assert summary.failure_class == FailureClass.RATE_LIMIT
    assert (summary.rate_limit_reset_at is not None) is has_reset
    if has_reset:
        assert 0 < (summary.rate_limit_reset_at.timestamp() - time.time()) <= 65


def test_success_prose_and_unknown_records_are_not_completion(
    adapter: str, tmp_path: Path
) -> None:
    driver = driver_for(adapter, tmp_path)
    prose = (
        {
            "type": "assistant",
            "message": {
                "id": "prose",
                "content": [{"type": "text", "text": "All tasks complete."}],
            },
        }
        if adapter == "claude"
        else {
            "type": "item.completed",
            "item": {
                "id": "prose",
                "type": "agent_message",
                "text": "All tasks complete.",
            },
        }
    )
    events = decoded(driver, [records(adapter)[0], prose])
    assert driver.summarize(events, 0).success is False
    unknown = tuple(driver.decode("not-json password=raw-secret"))
    assert unknown[0].type == ObservationType.RAW_UNKNOWN
    assert "raw-secret" not in str(unknown[0].payload)
    assert unknown[0].payload["raw_sha256"]
    assert driver.summarize(unknown, 0).failure_class == FailureClass.UNKNOWN


def test_raw_is_durable_before_decode_and_normalized_is_redacted(
    adapter: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver = driver_for(adapter, tmp_path)
    raw_path, normalized_path = tmp_path / "raw.jsonl", tmp_path / "normalized.jsonl"
    raw = SessionEvidenceWriter(raw_path, max_bytes=100000, min_free_bytes=0)
    normalized = NormalizedEventWriter(
        normalized_path, max_bytes=100000, min_free_bytes=0
    )
    original = driver.decode
    seen = []

    def decode_after_raw(line: str):
        assert line.encode() in raw_path.read_bytes()
        seen.append(line)
        return original(line)

    monkeypatch.setattr(driver, "decode", decode_after_raw)
    decoder = RawFirstDecoder(
        raw=raw, normalized=normalized, driver=driver, run_id="shared-run"
    )
    source = b"not-json password=private-fixture-secret\n" + b"".join(
        json.dumps(record).encode() + b"\n" for record in records(adapter)
    )
    events = ()
    try:
        for index in range(0, len(source), 7):
            events += decoder.feed(source[index : index + 7])
        events += decoder.finish()
    finally:
        normalized.close()
        raw.close()
    assert len(seen) == 3
    assert raw_path.read_bytes() == source
    assert b"private-fixture-secret" in raw_path.read_bytes()
    assert b"private-fixture-secret" not in normalized_path.read_bytes()
    assert b"[REDACTED]" in normalized_path.read_bytes()
    assert stat.S_IMODE(raw_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(normalized_path.stat().st_mode) == 0o600
    assert driver.summarize(events, 0).success is True


def stopped(pid: int) -> bool:
    status = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)],
        capture_output=True,
        timeout=2,
        check=False,
    )
    assert status.returncode in (0, 1)
    return not status.stdout.strip() or status.stdout.strip().startswith(b"Z")


def group_command(adapter: str, scenario: str) -> tuple[str, ...]:
    # Claude's fake executable has no group scenario, so its edge supplies a harmless script.
    child_handler = (
        "signal.SIG_IGN" if scenario == "descendant-kill" else "signal.SIG_DFL"
    )
    child_code = f"import signal,time; signal.signal(signal.SIGTERM,{child_handler}); print('ready',flush=True); time.sleep(60)"
    code = f"""import json,os,signal,subprocess,sys,time
signal.signal(signal.SIGTERM,signal.SIG_IGN)
assert sys.stdin.read() == ''
child=subprocess.Popen([sys.executable,'-c',{child_code!r}],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE)
assert child.stdout.readline().strip()==b'ready'
print(json.dumps({{'type':'fake_descendant','pid':child.pid,'parent_pid':os.getpid(),'pgid':os.getpgrp()}}),flush=True)
"""
    if scenario != "parent-exit":
        code += "child.wait(timeout=60)\n"
        if scenario == "descendant-kill":
            code += "time.sleep(60)\n"
    if adapter == "codex" and scenario != "parent-exit":
        command = (str(FIXTURES / "codex" / "v1" / "fake_codex.py"),)
    else:
        command = (sys.executable, "-c", code)
    return command


def group_sentinel(environment):
    return subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=dict(environment),
    )


def descendant_identity(owned, sentinel):
    child_pid = None
    deadline = time.monotonic() + 5
    pending = bytearray()
    while child_pid is None and time.monotonic() < deadline:
        ready, _, _ = select.select([owned.stdout], [], [], 0.1)
        if ready:
            chunk = os.read(owned.stdout.fileno(), 8192)
            assert chunk, "fake exited before publishing descendant identity"
            pending.extend(chunk)
            while b"\n" in pending:
                line, _, remaining = pending.partition(b"\n")
                pending[:] = remaining
                record = json.loads(line)
                if record.get("type") == "fake_descendant":
                    child_pid = record["pid"]
                    assert record["parent_pid"] == owned.pid
                    assert os.getpgid(child_pid) == record["pgid"]
                    assert os.getpgid(sentinel.pid) != record["pgid"]
                    break
    assert child_pid is not None
    return child_pid


@pytest.mark.parametrize(
    "scenario", ["descendant-term", "descendant-kill", "parent-exit"]
)
def test_real_owned_group_cleanup_and_unrelated_process(
    adapter: str, tmp_path: Path, scenario: str
) -> None:
    command = group_command(adapter, scenario)
    driver = driver_for(adapter, tmp_path, command)
    spec = driver.build_launch(request_for(tmp_path))
    environment = dict(spec.env) | {"OVCAQ_FAKE_SCENARIO": scenario}
    sentinel = group_sentinel(spec.env)
    owned = None
    try:
        owned = OwnedProcess.spawn(spec.argv, cwd=spec.cwd, env=environment)
        child_pid = descendant_identity(owned, sentinel)
        term_sent = kill_sent = False
        if scenario != "parent-exit":
            term_sent = owned.signal_group(signal.SIGTERM)
            assert term_sent is True
            if scenario == "descendant-kill":
                time.sleep(0.05)
                assert owned.poll() is None
                assert not stopped(child_pid)
                kill_sent = owned.signal_group(signal.SIGKILL)
                assert kill_sent is True
        owned.wait(timeout=5)
        result = owned.collect_exit(
            timed_out=False, term_sent=term_sent, kill_sent=kill_sent
        )
        assert result.returncode == (
            -signal.SIGKILL if scenario == "descendant-kill" else 0
        )
        assert result.signal == (
            signal.SIGKILL if scenario == "descendant-kill" else None
        )
        assert result.term_sent is term_sent and result.kill_sent is kill_sent
        assert owned.signal_group(signal.SIGTERM) is False
        deadline = time.monotonic() + 3
        while not stopped(child_pid) and time.monotonic() < deadline:
            time.sleep(0.02)
        assert stopped(child_pid)
        assert sentinel.poll() is None
    finally:
        try:
            if owned is not None:
                owned.signal_group(signal.SIGKILL)
                owned.wait(timeout=5)
                owned.stdout.close()
        finally:
            sentinel.terminate()
            sentinel.wait(timeout=5)
