from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from pathlib import Path

import pytest
from tests.workflow_client.conftest import BUNDLE

from ovcaq.workflow_client import (
    ControllerClient,
    ControllerConfig,
    ControllerTimeoutError,
    _kill_group,
)


class _BlockingProcess:
    """A Popen-like object whose .wait() would block indefinitely without a
    bound, used to prove _kill_group() does not simply call process.wait()
    with no timeout after os.killpg fails to deliver the signal."""

    def __init__(self, never_set: threading.Event) -> None:
        self.pid = 4242
        self._never_set = never_set

    def wait(self, timeout: float | None = None) -> int:
        if timeout is None:
            self._never_set.wait()
            return 0
        if self._never_set.wait(timeout):
            return 0
        raise subprocess.TimeoutExpired(cmd="controller", timeout=timeout)


def test_kill_group_completes_within_bounded_time_when_signal_is_denied(
    monkeypatch,
) -> None:
    never_set = threading.Event()
    calls: list[tuple[int, int]] = []

    def deny_signal(pid: int, sig: int) -> None:
        calls.append((pid, sig))
        raise PermissionError("not permitted")

    monkeypatch.setattr(os, "killpg", deny_signal)
    process = _BlockingProcess(never_set)
    # A raise inside the thread leaves outcome empty (pytest reports the
    # unhandled thread exception), so the final assertion catches it without
    # a blind except.
    outcome: list[None] = []

    def run() -> None:
        outcome.append(_kill_group(process))

    runner = threading.Thread(target=run, daemon=True)
    started = time.monotonic()
    runner.start()
    runner.join(timeout=5.0)
    elapsed = time.monotonic() - started

    assert not runner.is_alive()
    assert elapsed < 5.0
    assert calls == [(process.pid, signal.SIGKILL)]
    assert outcome == [None]


class _OpenPipeProcess:
    """A Popen-like object whose stdout/stderr are real pipes a detached
    descendant could keep open indefinitely, used to prove the reader
    threads _capture starts are joined with a bound rather than awaited
    forever when such a descendant never closes its end."""

    def __init__(self, read_ends: tuple[object, object]) -> None:
        self.pid = 4343
        self.stdout, self.stderr = read_ends

    def wait(self, timeout: float | None = None) -> int:
        raise subprocess.TimeoutExpired(cmd="controller", timeout=timeout or 0)


def test_capture_completes_within_bounded_time_when_a_pipe_stays_open(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(os, "killpg", lambda pid, sig: None)
    read_out, write_out = os.pipe()
    read_err, write_err = os.pipe()
    try:
        process = _OpenPipeProcess(
            (os.fdopen(read_out, "rb"), os.fdopen(read_err, "rb"))
        )
        config = ControllerConfig(
            argv=("controller",),
            contract_bundle=BUNDLE,
            actor_file=None,
            project_root=tmp_path,
            timeout_seconds=1,
        )
        client = ControllerClient(config)
        started = time.monotonic()

        with pytest.raises(ControllerTimeoutError):
            client._capture(process)

        elapsed = time.monotonic() - started
        # Bounded by _kill_group's JOIN_SECONDS wait plus two reader joins,
        # each capped at JOIN_SECONDS - well under this loose ceiling.
        assert elapsed < 5.0
    finally:
        # The write ends are never closed here, modeling the detached
        # descendant the finding describes; close explicitly for test
        # process hygiene rather than relying on garbage collection.
        os.close(write_out)
        os.close(write_err)
        process.stdout.close()
        process.stderr.close()
