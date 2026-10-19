"""Real-child continuity and publication failures at the Unicode gap boundary."""

from __future__ import annotations

import errno
import json
import os
import signal
from pathlib import Path

import pytest
from tests.runtime.test_supervisor_process import Step, harness, stopped

from ovcaq.events import (
    Observation,
    ObservationType,
    observation_from_record,
    summary_record,
)
from ovcaq.events.tail import NormalizedEventWriter
from ovcaq.runtime.process import OwnedProcess


def continuity_wires() -> tuple[bytes, bytes]:
    unsafe_records = (
        {
            "type": "thread.started",
            "thread_id": "poisoned-parent",
            "vendor": {"value": "\ud800"},
        },
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 99,
                "cached_input_tokens": 9,
                "output_tokens": 88,
            },
            "vendor": {"\udc00": "unsafe key"},
        },
        {
            "type": "item.started",
            "item": {
                "id": "collab-1",
                "type": "collab_tool_call",
                "tool": "spawn_agent",
                "sender_thread_id": "poisoned-parent",
                "receiver_thread_ids": ["child-1"],
                "agents_states": {
                    "child-1": {"status": "running", "message": "\ud800"}
                },
                "status": "in_progress",
            },
        },
    )
    healthy_records = (
        {"type": "thread.started", "thread_id": "healthy-parent"},
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 3,
                "cached_input_tokens": 0,
                "cache_write_input_tokens": 0,
                "output_tokens": 2,
            },
        },
    )
    unsafe_wire = b"".join(
        json.dumps(record).encode() + b"\n" for record in unsafe_records
    )
    healthy_wire = b"".join(
        json.dumps(record).encode() + b"\n" for record in healthy_records
    )
    return unsafe_wire, healthy_wire


def assert_continuity_records(session_dir: Path) -> None:
    observations = tuple(
        observation_from_record(json.loads(line))
        for line in (session_dir / "normalized.jsonl").read_bytes().splitlines()
    )
    assert [item.type for item in observations[:3]] == [ObservationType.RAW_UNKNOWN] * 3
    assert {item.type for item in observations[3:]} >= {
        ObservationType.SESSION_STARTED,
        ObservationType.USAGE_UPDATED,
        ObservationType.SESSION_COMPLETED,
    }
    assert all(
        item.type is not ObservationType.RAW_UNKNOWN for item in observations[3:]
    )
    assert all(item.session_id == session_dir.name for item in observations)
    summary = json.loads((session_dir / "summary.json").read_bytes())
    assert summary["returncode"] == 0
    assert summary["signal"] is None
    assert summary["timed_out"] is False
    assert summary["detail"] is None


def test_real_child_completes_after_unsafe_native_unicode_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch, "codex")
    sentinel = tmp_path / "normal-exit"
    pid_file = tmp_path / "child-pid"
    unsafe_wire, healthy_wire = continuity_wires()
    h.driver.steps = [
        Step(
            code=(
                "import os, sys, time\nfrom pathlib import Path\n"
                f"Path({str(pid_file)!r}).write_text(str(os.getpid()))\n"
                f"sys.stdout.buffer.write({unsafe_wire!r})\n"
                "sys.stdout.buffer.flush()\ntime.sleep(0.2)\n"
                f"sys.stdout.buffer.write({healthy_wire!r})\n"
                "sys.stdout.buffer.flush()\n"
                f"Path({str(sentinel)!r}).write_text('normal exit')\n"
            )
        )
    ]
    signals_while_child_alive: list[int] = []
    real_signal_group = OwnedProcess.signal_group

    def signal_group(process: OwnedProcess, signal_number: int) -> bool:
        if not stopped(int(pid_file.read_text())):
            signals_while_child_alive.append(signal_number)
        return real_signal_group(process, signal_number)

    monkeypatch.setattr(OwnedProcess, "signal_group", signal_group)
    result = h.supervisor().run_once()

    assert sentinel.read_text() == "normal exit"
    assert signals_while_child_alive == []
    assert result.summary.success
    assert result.summary.failure_class is None
    assert result.summary.failure_detail is None
    assert result.state_error is None
    (request,) = h.driver.requests
    assert result.summary.session_id == request.session_dir.name
    usage = summary_record(result.summary)["usage"]
    assert usage["input_tokens"] == 3
    assert usage["output_tokens"] == 2
    assert (
        request.session_dir / "raw.jsonl"
    ).read_bytes() == unsafe_wire + healthy_wire
    assert_continuity_records(request.session_dir)


def inject_gap_writer_failure(
    monkeypatch: pytest.MonkeyPatch, pid_file: Path, sentinel: Path, failure: OSError
) -> list[int]:
    live_at_failure: list[int] = []
    real_write = NormalizedEventWriter.write

    def fail_gap_write(writer: NormalizedEventWriter, observation: Observation) -> int:
        if observation.type is ObservationType.RAW_UNKNOWN:
            pid = int(pid_file.read_text())
            os.kill(pid, 0)
            assert not sentinel.exists()
            live_at_failure.append(pid)
            raise failure
        return real_write(writer, observation)

    monkeypatch.setattr(NormalizedEventWriter, "write", fail_gap_write)
    return live_at_failure


def test_normalized_gap_writer_error_propagates_and_cleans_up_live_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = harness(tmp_path, monkeypatch, "codex")
    sentinel = tmp_path / "normal-exit"
    pid_file = tmp_path / "child-pid"
    unsafe_wire = (
        json.dumps(
            {
                "type": "thread.started",
                "thread_id": "poisoned-parent",
                "vendor": "\ud800",
            }
        ).encode()
        + b"\n"
    )
    h.driver.steps = [
        Step(
            code=(
                "import os, sys, time\nfrom pathlib import Path\n"
                f"Path({str(pid_file)!r}).write_text(str(os.getpid()))\n"
                f"sys.stdout.buffer.write({unsafe_wire!r})\n"
                "sys.stdout.buffer.flush()\ntime.sleep(1)\n"
                f"Path({str(sentinel)!r}).write_text('normal exit')\n"
            )
        )
    ]
    failure = OSError(errno.EIO, "injected normalized writer failure")
    live_at_failure = inject_gap_writer_failure(
        monkeypatch, pid_file, sentinel, failure
    )
    try:
        with pytest.raises(
            OSError, match="injected normalized writer failure"
        ) as caught:
            h.supervisor().run_once()
        assert caught.value is failure
        assert live_at_failure == [int(pid_file.read_text())]
        assert stopped(live_at_failure[0])
        assert not sentinel.exists()
        (request,) = h.driver.requests
        assert (request.session_dir / "raw.jsonl").read_bytes() == unsafe_wire
        assert (request.session_dir / "normalized.jsonl").read_bytes() == b""
        summary = json.loads((request.session_dir / "summary.json").read_bytes())
        assert summary["detail"] == str(failure)
        assert summary["timed_out"] is False
    finally:
        if pid_file.exists() and not stopped(int(pid_file.read_text())):
            os.kill(int(pid_file.read_text()), signal.SIGKILL)
