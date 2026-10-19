"""Joinable timeout escalation for an owned process group."""

from __future__ import annotations

import math
import signal
import threading
import time
from dataclasses import dataclass
from typing import Protocol

from ovcaq.runtime.process import OwnedProcess, ProcessOwnershipError


class Clock(Protocol):
    def monotonic(self) -> float: ...

    def wait(self, event: threading.Event, timeout: float) -> bool: ...


class _SystemClock:
    def monotonic(self) -> float:
        return time.monotonic()

    def wait(self, event: threading.Event, timeout: float) -> bool:
        return event.wait(timeout)


@dataclass(frozen=True)
class WatchdogResult:
    fired: bool
    term_sent: bool
    kill_sent: bool


class Watchdog:
    def __init__(
        self,
        process: OwnedProcess,
        *,
        timeout_seconds: float,
        grace_seconds: float,
        clock: Clock | None = None,
    ) -> None:
        for duration in (timeout_seconds, grace_seconds):
            if (
                isinstance(duration, bool)
                or not math.isfinite(duration)
                or duration < 0
            ):
                raise ValueError("watchdog durations must be finite and nonnegative")
        self._process = process
        self._timeout = timeout_seconds
        self._grace = grace_seconds
        self._clock = clock if clock is not None else _SystemClock()
        self._cancelled = threading.Event()
        self._result = WatchdogResult(False, False, False)
        self._error: ProcessOwnershipError | None = None
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._started = False

    def start(self) -> None:
        if self._started:
            raise RuntimeError("watchdog has already started")
        self._started = True
        self._worker.start()

    def cancel(self) -> WatchdogResult:
        self._cancelled.set()
        return self.join()

    def join(self, timeout: float | None = None) -> WatchdogResult:
        self._worker.join(timeout)
        if self._worker.is_alive():
            raise TimeoutError("Watchdog has not finished")
        if self._error is not None:
            raise self._error
        return self._result

    def _wait_until(self, deadline: float) -> bool:
        while not self._cancelled.is_set():
            remaining = deadline - self._clock.monotonic()
            if remaining <= 0:
                return False
            if self._clock.wait(self._cancelled, remaining):
                return True
        return True

    def _run(self) -> None:
        try:
            deadline = self._clock.monotonic() + self._timeout
            if self._process.poll() is not None or self._wait_until(deadline):
                return
            if self._process.poll() is not None or self._cancelled.is_set():
                return
            self._result = WatchdogResult(True, False, False)
            term_sent = self._process.signal_group(signal.SIGTERM)
            self._result = WatchdogResult(True, term_sent, False)
            if not term_sent:
                return
            if self._wait_until(self._clock.monotonic() + self._grace):
                return
            # The leader may have exited while owned descendants remain alive.
            kill_sent = self._process.signal_group(signal.SIGKILL)
            self._result = WatchdogResult(True, term_sent, kill_sent)
        except ProcessOwnershipError as error:
            self._error = error
