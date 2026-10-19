from __future__ import annotations

import json
import stat
from collections.abc import Mapping
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import AgentDriver, LaunchRequest
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events import Observation, ObservationType, Usage
from ovcaq.events.tail import NormalizedEventWriter, RawFirstDecoder
from ovcaq.runtime.process import OwnedProcess, ProcessExit
from ovcaq.runtime.session import SessionEvidenceWriter

CLAUDE_FIXTURES = Path(__file__).parents[1] / "fixtures" / "claude" / "v1"
CODEX_FIXTURES = Path(__file__).parents[1] / "fixtures" / "codex" / "v1"


def _assert_process_artifacts(
    process_exit: ProcessExit,
    owned: OwnedProcess,
    raw_path: Path,
    normalized_path: Path,
    captured: bytearray,
) -> None:
    assert process_exit == ProcessExit(0, None, False, False, False)
    assert owned.signal_group(15) is False
    assert raw_path.read_bytes() == bytes(captured)
    assert stat.S_IMODE(raw_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(normalized_path.stat().st_mode) == 0o600


def _assert_invocation(
    captured: bytearray,
    argv: tuple[str, ...],
    cwd: Path,
    prompt: str,
    env: Mapping[str, str],
) -> None:
    invocation = json.loads(captured.splitlines()[0])
    assert invocation == {
        "type": "fake_invocation",
        "argv": list(argv[1:]),
        "cwd": str(cwd),
        "environment": {
            "CLAUDE_UNATTENDED": "1",
            "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
            "WARDEN_UNATTENDED": "1",
            "HOST_ONLY_MARKER": None,
        },
        "password": "raw-fixture-secret",
    }
    assert argv[-1] == prompt
    assert dict(env) == {
        "CLAUDE_UNATTENDED": "1",
        "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
        "WARDEN_UNATTENDED": "1",
    }


def _assert_normalized_evidence(normalized_path: Path) -> None:
    normalized_bytes = normalized_path.read_bytes()
    assert b"raw-fixture-secret" not in normalized_bytes
    assert b"normalized-value" not in normalized_bytes
    assert b"prompt-secret" not in normalized_bytes
    assert b"[REDACTED]" in normalized_bytes


def _assert_observations(observations: tuple[Observation, ...]) -> None:
    assert [observation.type for observation in observations] == [
        ObservationType.RAW_UNKNOWN,
        ObservationType.SESSION_STARTED,
        ObservationType.ACTIVITY_MESSAGE,
        ObservationType.TOOL_STARTED,
        ObservationType.USAGE_UPDATED,
        ObservationType.TOOL_COMPLETED,
        ObservationType.USAGE_UPDATED,
        ObservationType.SESSION_COMPLETED,
    ]


def _assert_summary(
    driver: AgentDriver,
    observations: tuple[Observation, ...],
    process_exit: ProcessExit,
) -> None:
    summary = driver.summarize(observations, process_exit.returncode)
    assert summary.success is True
    assert summary.session_id == (
        "fake-session" if driver.name == "claude" else "example-healthy"
    )
    assert summary.failure_class is None
    if driver.name == "claude":
        assert summary.usage == Usage(input_tokens=5, output_tokens=2, cost_usd=0.125)
    else:
        assert summary.usage == Usage(
            output_tokens=25,
            cache_creation_input_tokens=5,
            cache_read_input_tokens=20,
            estimated=True,
        )


def _launch_inputs(tmp_path: Path, adapter: str) -> tuple[AgentDriver, LaunchRequest]:
    executable = (
        CLAUDE_FIXTURES / "fake_claude.py"
        if adapter == "claude"
        else CODEX_FIXTURES / "fake_codex.py"
    )
    assert stat.S_IMODE(executable.stat().st_mode) == 0o755
    settings = AgentSettings(
        name=adapter,
        command=(
            (str(executable), "--literal-wrapper-argument")
            if adapter == "claude"
            else (str(executable),)
        ),
        tiers={"standard": "fixture-model"},
        environment=(
            {"WARDEN_UNATTENDED": "1"}
            if adapter == "claude"
            else {
                "HOME": str(tmp_path / "home"),
                "XDG_CONFIG_HOME": str(tmp_path / "config"),
                "XDG_STATE_HOME": str(tmp_path / "state"),
                "OVCAQ_FAKE_SCENARIO": "healthy",
            }
        ),
        options={"permission_mode": "auto"} if adapter == "claude" else {},
    )
    request = LaunchRequest(
        root=tmp_path,
        phase="build",
        prompt="literal $(not-executed) | value\npassword=prompt-secret",
        model="standard",
        effort="high",
        timeout_seconds=30,
        session_dir=tmp_path / "session",
    )
    driver = (ClaudeDriver if adapter == "claude" else CodexDriver)(
        settings, run_id="owned-run"
    )
    return driver, request


def _require_raw_first(driver, raw_path, monkeypatch):
    original_decode = driver.decode

    def decode_after_raw(line: str):
        assert line.encode() in raw_path.read_bytes()
        return original_decode(line)

    monkeypatch.setattr(driver, "decode", decode_after_raw)


def _run_scripted_process(driver, request, spec, monkeypatch, tmp_path):
    request.session_dir.mkdir(mode=0o700)
    raw_path = request.session_dir / "raw.jsonl"
    normalized_path = request.session_dir / "normalized.jsonl"
    raw = SessionEvidenceWriter(raw_path, max_bytes=1 << 20, min_free_bytes=0)
    normalized = NormalizedEventWriter(
        normalized_path, max_bytes=1 << 20, min_free_bytes=0
    )
    decoder = RawFirstDecoder(
        raw=raw, normalized=normalized, driver=driver, run_id="owned-run"
    )
    _require_raw_first(driver, raw_path, monkeypatch)
    process_environment = dict(spec.env) | {
        "HOME": str(tmp_path / "home"),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "XDG_STATE_HOME": str(tmp_path / "state"),
    }
    owned = OwnedProcess.spawn(spec.argv, cwd=spec.cwd, env=process_environment)
    collected = False
    captured = bytearray()
    observations: tuple[Observation, ...] = ()
    try:
        while chunk := owned.stdout.read(7):
            captured.extend(chunk)
            observations += decoder.feed(chunk)
        observations += decoder.finish()
        process_exit = owned.collect_exit(
            timed_out=False, term_sent=False, kill_sent=False
        )
        collected = True
    finally:
        normalized.close()
        raw.close()
        if not collected:
            owned.signal_group(9)
            owned.wait(timeout=5)

    return (
        process_exit,
        owned,
        raw_path,
        normalized_path,
        captured,
        observations,
        process_environment,
    )


@pytest.mark.parametrize("adapter", ["claude", "codex"])
def test_scripted_claude_runs_through_launch_and_owned_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, adapter: str
) -> None:
    monkeypatch.setenv("HOST_ONLY_MARKER", "must-not-leak")
    driver, request = _launch_inputs(tmp_path, adapter)
    spec = driver.build_launch(request)
    (
        process_exit,
        owned,
        raw_path,
        normalized_path,
        captured,
        observations,
        process_environment,
    ) = _run_scripted_process(driver, request, spec, monkeypatch, tmp_path)

    _assert_process_artifacts(process_exit, owned, raw_path, normalized_path, captured)
    if adapter == "claude":
        _assert_invocation(captured, spec.argv, spec.cwd, request.prompt, spec.env)
    else:
        invocation = json.loads(captured.splitlines()[0])
        assert invocation == {
            "type": "fake_invocation",
            "argv": list(spec.argv[1:]),
            "cwd": str(spec.cwd),
            "stdin_closed": True,
            "environment": dict(process_environment) | {"OVCAQ_FAKE_MARKER": None},
        }
        assert spec.argv[-1] == request.prompt
    _assert_normalized_evidence(normalized_path)
    if adapter == "claude":
        _assert_observations(observations)
    else:
        assert [observation.type for observation in observations] == [
            ObservationType.RAW_UNKNOWN,
            ObservationType.SESSION_STARTED,
            ObservationType.ACTIVITY_MESSAGE,
            ObservationType.ACTIVITY_MESSAGE,
            ObservationType.ACTIVITY_MESSAGE,
            ObservationType.ACTIVITY_MESSAGE,
            ObservationType.ACTIVITY_MESSAGE,
            ObservationType.USAGE_UPDATED,
            ObservationType.SESSION_COMPLETED,
            ObservationType.RAW_UNKNOWN,
        ]
        assert (
            observations[-1].payload["reason"]
            == "Codex cache-write input partition is unknown"
        )
    _assert_summary(driver, observations, process_exit)
