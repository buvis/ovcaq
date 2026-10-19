from __future__ import annotations

import json
import signal
from pathlib import Path

import pytest
from packaging_support import InstalledWheel
from tests.packaging.test_installed_supervisor_cli import (
    _assert_process_stopped,
    _project,
    _run,
    _running,
    _state,
    _success,
    _workflow,
)


@pytest.mark.parametrize("stop", ["SIGINT", "SIGTERM", "command"])
def test_installed_stop_requires_resume_before_a_fresh_process_can_launch(
    installed_wheel: InstalledWheel, tmp_path: Path, stop: str
) -> None:
    root, cwd, environment = _project(installed_wheel, tmp_path)
    before = _state(root)
    number = signal.SIGINT if stop == "SIGINT" else signal.SIGTERM
    with _running(installed_wheel, environment, root, cwd) as (process, driver_pid):
        if stop == "command":
            assert _success(_run(installed_wheel, environment, cwd, "stop")) == {
                "pid": process.pid,
                "signal": 15,
            }
        else:
            process.send_signal(number)
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 128 + number, stdout + stderr
        _assert_process_stopped(driver_pid)
        marker = root / "invocations.jsonl"
        row = json.loads(marker.read_text().splitlines()[0])
        assert row["grandchild"] is not None
        _assert_process_stopped(row["grandchild"])
    state = _state(root)
    assert state["control"]["pause_requested"] is True
    notice = state["control"]["pause_reason"]
    assert notice["site"] == "operator_stop" and str(int(number)) in notice["detail"]
    assert _workflow(state) == _workflow(before)
    invocations = marker.read_bytes()
    _success(_run(installed_wheel, environment, cwd, "run", "--no-tui"))
    assert marker.read_bytes() == invocations
    assert _state(root)["control"]["pause_requested"] is True
    _success(_run(installed_wheel, environment, cwd, "resume"))
    _success(_run(installed_wheel, environment, cwd, "run", "--no-tui"))
    assert len(marker.read_text().splitlines()) == 4
    assert _state(root)["batch"]["status"] == "completed"
