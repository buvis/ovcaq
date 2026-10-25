from __future__ import annotations

import os
import signal
import subprocess
import threading
import time

from ovcaq.workflow_client import _kill_group


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
    outcome: list[BaseException] = []

    def run() -> None:
        try:
            _kill_group(process)
        except BaseException as error:
            outcome.append(error)

    runner = threading.Thread(target=run, daemon=True)
    started = time.monotonic()
    runner.start()
    runner.join(timeout=5.0)
    elapsed = time.monotonic() - started

    assert not runner.is_alive()
    assert elapsed < 5.0
    assert calls == [(process.pid, signal.SIGKILL)]
    assert outcome == []
