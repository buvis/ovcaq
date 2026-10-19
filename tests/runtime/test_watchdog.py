from __future__ import annotations

import os
import selectors
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import BinaryIO

import pytest

from ovcaq.runtime.process import OwnedProcess, ProcessOwnershipError
from ovcaq.runtime.watchdog import Watchdog, WatchdogResult


def _reject(expected: type[BaseException], operation: Callable[[], object]) -> None:
    with pytest.raises(expected):
        operation()


class DeterministicClock:
    def __init__(self, *, park: bool = False) -> None:
        self.now = 0.0
        self.park = park
        self.waiting = threading.Event()
        self.waits: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def wait(self, event: threading.Event, timeout: float) -> bool:
        assert timeout > 0, "zero-duration deadlines must not busy wait"
        self.waits.append(timeout)
        assert len(self.waits) <= 1000, "watchdog failed to make bounded progress"
        self.waiting.set()
        if self.park:
            assert event.wait(5), "cancellation did not wake the worker"
            return True
        if event.is_set():
            return True
        self.now += timeout
        return event.is_set()


class OwnedGroup:
    def __init__(self, clock: DeterministicClock) -> None:
        self.clock = clock
        self.returncode: int | None = None
        self.group_live = True
        self.term_handled = False
        self.leader_exits_on_term = False
        self.error_on: int | None = None
        self.error = ProcessOwnershipError("owned group identity changed")
        self.attempts: list[tuple[int, float]] = []
        self.deliveries: list[int] = []

    def poll(self) -> int | None:
        return self.returncode

    def signal_group(self, signal_number: int) -> bool:
        assert signal_number in (signal.SIGTERM, signal.SIGKILL)
        self.attempts.append((signal_number, self.clock.monotonic()))
        if signal_number == self.error_on:
            raise self.error
        if not self.group_live:
            return False
        self.deliveries.append(signal_number)
        if signal_number == signal.SIGTERM:
            if self.term_handled:
                self.group_live = False
                self.returncode = 0
            elif self.leader_exits_on_term:
                self.returncode = 0
        else:
            self.group_live = False
            self.returncode = -signal.SIGKILL
        return True


@pytest.fixture
def workers(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[threading.Thread]]:
    started: list[threading.Thread] = []
    real_start = threading.Thread.start

    def observe_start(thread: threading.Thread) -> None:
        started.append(thread)
        real_start(thread)

    monkeypatch.setattr(threading.Thread, "start", observe_start)
    yield started
    for thread in started:
        thread.join(timeout=5)
        assert not thread.is_alive(), "watchdog worker leaked after completion"


def _final(watchdog: Watchdog, expected: WatchdogResult) -> None:
    result = watchdog.join(timeout=5)
    assert result == expected
    cancelled = watchdog.cancel()
    assert cancelled == expected
    assert watchdog.join(timeout=0) == expected
    assert watchdog.cancel() == expected
    for final in (result, cancelled):
        for field in ("fired", "term_sent", "kill_sent"):
            with pytest.raises(FrozenInstanceError):
                setattr(final, field, None)


@pytest.mark.parametrize("field", ["timeout_seconds", "grace_seconds"])
@pytest.mark.parametrize(
    "invalid", [True, False, -1, float("inf"), -float("inf"), float("nan")]
)
def test_rejects_invalid_durations_before_starting_a_worker(
    field: str, invalid: object, workers: list[threading.Thread]
) -> None:
    clock = DeterministicClock()
    process = OwnedGroup(clock)
    durations = {"timeout_seconds": 1.0, "grace_seconds": 0.5}
    durations[field] = invalid
    _reject(ValueError, lambda: Watchdog(process, clock=clock, **durations))
    assert workers == []
    assert process.attempts == []


def test_start_launches_one_joinable_worker_and_cancellation_before_deadline_sends_nothing(
    workers: list[threading.Thread],
) -> None:
    clock = DeterministicClock(park=True)
    process = OwnedGroup(clock)
    watchdog = Watchdog(process, timeout_seconds=1, grace_seconds=0.5, clock=clock)
    watchdog.start()
    try:
        assert clock.waiting.wait(5), "worker never reached its deadline wait"
        assert len(workers) == 1
        assert workers[0].is_alive()
        _reject(RuntimeError, watchdog.start)
    finally:
        result = watchdog.cancel()
    assert result == WatchdogResult(False, False, False)
    _final(watchdog, result)
    assert len(workers) == 1
    assert not workers[0].is_alive()
    assert process.attempts == []


def test_fast_process_exit_before_deadline_sends_nothing(
    workers: list[threading.Thread],
) -> None:
    clock = DeterministicClock()
    process = OwnedGroup(clock)
    process.returncode = 0
    process.group_live = False
    watchdog = Watchdog(process, timeout_seconds=1, grace_seconds=0.5, clock=clock)
    watchdog.start()
    _final(watchdog, WatchdogResult(False, False, False))
    assert process.attempts == []
    assert len(workers) == 1


@pytest.mark.parametrize(
    "timeout,grace", [(1.0, 0.5), (0.0, 0.5), (1.0, 0.0), (0.0, 0.0)]
)
def test_term_ignored_escalates_once_at_deadline_and_once_after_grace(
    timeout: float, grace: float, workers: list[threading.Thread]
) -> None:
    clock = DeterministicClock()
    process = OwnedGroup(clock)
    watchdog = Watchdog(
        process, timeout_seconds=timeout, grace_seconds=grace, clock=clock
    )
    watchdog.start()
    _final(watchdog, WatchdogResult(True, True, True))
    assert process.deliveries == [signal.SIGTERM, signal.SIGKILL]
    assert process.attempts == [
        (signal.SIGTERM, pytest.approx(timeout)),
        (signal.SIGKILL, pytest.approx(timeout + grace)),
    ]
    assert len(workers) == 1
    if timeout == grace == 0:
        assert clock.waits == []


def test_default_clock_waits_for_timeout_and_additional_grace_before_signalling(
    workers: list[threading.Thread],
) -> None:
    attempts: list[tuple[int, float]] = []

    class LiveGroup:
        def poll(self) -> None:
            return None

        def signal_group(self, signal_number: int) -> bool:
            attempts.append((signal_number, time.monotonic()))
            return True

    timeout = 0.05
    grace = 0.05
    began = time.monotonic()
    watchdog = Watchdog(LiveGroup(), timeout_seconds=timeout, grace_seconds=grace)
    watchdog.start()
    _final(watchdog, WatchdogResult(True, True, True))
    assert [number for number, _ in attempts] == [signal.SIGTERM, signal.SIGKILL]
    term_at = attempts[0][1]
    kill_at = attempts[1][1]
    assert timeout <= term_at - began < 5
    assert grace <= kill_at - term_at < 5
    assert len(workers) == 1
    assert not workers[0].is_alive()


def test_term_handled_exit_receives_no_kill_delivery(
    workers: list[threading.Thread],
) -> None:
    clock = DeterministicClock()
    process = OwnedGroup(clock)
    process.term_handled = True
    watchdog = Watchdog(process, timeout_seconds=1, grace_seconds=0.5, clock=clock)
    watchdog.start()
    _final(watchdog, WatchdogResult(True, True, False))
    assert process.deliveries == [signal.SIGTERM]
    assert process.attempts == [
        (signal.SIGTERM, pytest.approx(1)),
        (signal.SIGKILL, pytest.approx(1.5)),
    ]


def test_leader_exit_after_term_does_not_prevent_killing_live_owned_descendants(
    workers: list[threading.Thread],
) -> None:
    clock = DeterministicClock()
    process = OwnedGroup(clock)
    process.leader_exits_on_term = True
    watchdog = Watchdog(process, timeout_seconds=1, grace_seconds=0.5, clock=clock)
    watchdog.start()
    _final(watchdog, WatchdogResult(True, True, True))
    assert process.deliveries == [signal.SIGTERM, signal.SIGKILL]
    assert process.attempts == [
        (signal.SIGTERM, pytest.approx(1)),
        (signal.SIGKILL, pytest.approx(1.5)),
    ]


def test_group_disappearing_before_term_reports_timeout_without_sent_signals(
    workers: list[threading.Thread],
) -> None:
    clock = DeterministicClock()
    process = OwnedGroup(clock)
    process.group_live = False
    watchdog = Watchdog(process, timeout_seconds=0, grace_seconds=0, clock=clock)
    watchdog.start()
    _final(watchdog, WatchdogResult(True, False, False))
    assert process.attempts == [(signal.SIGTERM, 0)]
    assert process.deliveries == []


@pytest.mark.parametrize("failed_signal", [signal.SIGTERM, signal.SIGKILL])
def test_ownership_error_is_raised_by_join_after_worker_stops_without_further_signals(
    failed_signal: int, workers: list[threading.Thread]
) -> None:
    clock = DeterministicClock()
    process = OwnedGroup(clock)
    process.error_on = failed_signal
    watchdog = Watchdog(process, timeout_seconds=0, grace_seconds=0, clock=clock)
    watchdog.start()
    with pytest.raises(ProcessOwnershipError) as caught:
        watchdog.join(timeout=5)
    assert caught.value is process.error
    assert len(workers) == 1
    assert not workers[0].is_alive()
    expected = [signal.SIGTERM]
    if failed_signal == signal.SIGKILL:
        expected.append(signal.SIGKILL)
    assert [number for number, _ in process.attempts] == expected


def _line(stream: BinaryIO) -> bytes:
    deadline = time.monotonic() + 5
    result = bytearray()
    with selectors.DefaultSelector() as selector:
        selector.register(stream, selectors.EVENT_READ)
        while not result.endswith(b"\n"):
            remaining = deadline - time.monotonic()
            assert remaining > 0 and selector.select(remaining), (
                "child output timed out"
            )
            chunk = os.read(stream.fileno(), 1)
            assert chunk, f"child output ended early: {result!r}"
            result.extend(chunk)
    return bytes(result)


def _spawn_real_group(
    tmp_path: Path, exit_on_term: bool
) -> tuple[OwnedProcess, subprocess.Popen[bytes]]:
    handler = "lambda *_: sys.exit(0)" if exit_on_term else "signal.SIG_IGN"
    owned = OwnedProcess.spawn(
        [
            sys.executable,
            "-c",
            (
                "import signal, sys, time; "
                f"signal.signal(signal.SIGTERM, {handler}); "
                "signal.alarm(15); print('ready', flush=True); time.sleep(15)"
            ),
        ],
        cwd=tmp_path,
    )
    assert _line(owned.stdout) == b"ready\n"
    sentinel = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import time; print('ready', flush=True); time.sleep(15)",
        ],
        stdout=subprocess.PIPE,
        process_group=0,
    )
    assert sentinel.stdout is not None
    assert _line(sentinel.stdout) == b"ready\n"
    assert os.getpgid(owned.pid) != os.getpgid(sentinel.pid)
    return owned, sentinel


@pytest.fixture
def real_groups(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Callable[[bool], tuple[OwnedProcess, subprocess.Popen[bytes]]]]:
    children: list[tuple[dict[str, object], subprocess.Popen[bytes]]] = []
    real_popen = subprocess.Popen
    real_killpg = os.killpg

    def observe(argv: object, **kwargs: object) -> subprocess.Popen[bytes]:
        child = real_popen(argv, **kwargs)
        children.append((kwargs, child))
        return child

    def spawn(exit_on_term: bool) -> tuple[OwnedProcess, subprocess.Popen[bytes]]:
        return _spawn_real_group(tmp_path, exit_on_term)

    monkeypatch.setattr(subprocess, "Popen", observe)
    yield spawn
    for options, child in children:
        if child.poll() is None:
            try:
                if options.get("process_group") == 0:
                    real_killpg(child.pid, signal.SIGKILL)
                else:
                    child.kill()
            except ProcessLookupError:
                pass
    for _, child in children:
        child.wait(timeout=5)
        for stream in (child.stdin, child.stdout, child.stderr):
            if stream is not None:
                stream.close()


def test_join_times_out_during_pending_signal_and_returns_only_after_last_delivery(
    real_groups: Callable[[bool], tuple[OwnedProcess, subprocess.Popen[bytes]]],
    workers: list[threading.Thread],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owned, sentinel = real_groups(False)
    pgid = os.getpgid(owned.pid)
    pending = threading.Event()
    release = threading.Event()
    joined = False
    deliveries: list[int] = []
    real_killpg = os.killpg

    def signal_group(group: int, number: int) -> None:
        assert group == pgid
        assert sentinel.poll() is None
        if number:
            assert not joined, "watchdog delivered a signal after a successful join"
            if number == signal.SIGTERM:
                pending.set()
                assert release.wait(5), "test did not release the pending signal"
            real_killpg(group, number)
            deliveries.append(number)
        else:
            real_killpg(group, number)

    monkeypatch.setattr(os, "killpg", signal_group)
    watchdog = Watchdog(owned, timeout_seconds=0, grace_seconds=0)
    watchdog.start()
    try:
        assert pending.wait(5)
        with pytest.raises(TimeoutError):
            watchdog.join(timeout=0.01)
        assert deliveries == []
        assert workers[0].is_alive()
        release.set()
        assert watchdog.join(timeout=5) == WatchdogResult(True, True, True)
        joined = True
        assert not workers[0].is_alive()
        assert deliveries == [signal.SIGTERM, signal.SIGKILL]
        assert watchdog.cancel() == WatchdogResult(True, True, True)
        assert watchdog.join(timeout=0) == WatchdogResult(True, True, True)
        assert owned.wait(timeout=5) == -signal.SIGKILL
        assert sentinel.poll() is None
        assert deliveries == [signal.SIGTERM, signal.SIGKILL]
    finally:
        release.set()
        watchdog.cancel()


class GraceClock:
    def __init__(self, *, cancel: bool) -> None:
        self.now = 0.0
        self.cancel = cancel
        self.started = threading.Event()
        self.resume = threading.Event()

    def monotonic(self) -> float:
        return self.now

    def wait(self, event: threading.Event, timeout: float) -> bool:
        self.started.set()
        if self.cancel:
            assert event.wait(5), "cancellation did not wake the grace wait"
            return True
        assert self.resume.wait(5), "test did not resume the grace wait"
        self.now += timeout
        return False


@pytest.mark.parametrize("cancel", [False, True], ids=["wait-finishes", "cancel"])
def test_wait_or_cancellation_finishes_before_watchdog_can_send_another_signal(
    real_groups: Callable[[bool], tuple[OwnedProcess, subprocess.Popen[bytes]]],
    workers: list[threading.Thread],
    monkeypatch: pytest.MonkeyPatch,
    cancel: bool,
) -> None:
    owned, sentinel = real_groups(True)
    pgid = os.getpgid(owned.pid)
    clock = GraceClock(cancel=cancel)
    deliveries: list[int] = []
    finalized = False
    real_killpg = os.killpg

    def signal_group(group: int, number: int) -> None:
        assert group == pgid
        assert sentinel.poll() is None
        if number:
            assert not finalized, "watchdog signaled a finalized or recycled group"
            if threading.current_thread() is workers[0]:
                deliveries.append(number)
        real_killpg(group, number)

    monkeypatch.setattr(os, "killpg", signal_group)
    watchdog = Watchdog(owned, timeout_seconds=0, grace_seconds=1, clock=clock)
    watchdog.start()
    try:
        assert clock.started.wait(5)
        assert deliveries == [signal.SIGTERM]
        if cancel:
            assert watchdog.cancel() == WatchdogResult(True, True, False)
            assert not workers[0].is_alive()
        assert owned.wait(timeout=5) == 0
        finalized = True
        assert sentinel.poll() is None
        clock.resume.set()
        assert watchdog.join(timeout=5) == WatchdogResult(True, True, False)
        assert not workers[0].is_alive()
        assert watchdog.cancel() == WatchdogResult(True, True, False)
        assert watchdog.join(timeout=0) == WatchdogResult(True, True, False)
        assert deliveries == [signal.SIGTERM]
        assert owned.signal_group(signal.SIGTERM) is False
        assert owned.signal_group(signal.SIGKILL) is False
        assert sentinel.poll() is None
    finally:
        clock.resume.set()
        watchdog.cancel()


def _pause_post_term_check(
    patch: pytest.MonkeyPatch,
    pgid: int,
    workers: list[threading.Thread],
    deliveries: list[int],
    checking: threading.Event,
    release: threading.Event,
) -> None:
    real_getpgid = os.getpgid

    def check_group(pid: int) -> int:
        if (
            pid == pgid
            and threading.current_thread() is workers[0]
            and signal.SIGTERM in deliveries
        ):
            checking.set()
            assert release.wait(5), "test did not release the group identity check"
        return real_getpgid(pid)

    patch.setattr(os, "getpgid", check_group)


def _collect_exit(
    owned: OwnedProcess,
    waiting: threading.Event,
    waited: threading.Event,
    outcomes: list[object],
) -> None:
    waiting.set()
    try:
        outcomes.append(owned.wait(timeout=5))
    except Exception as error:  # noqa: BLE001 - report worker failure to the test
        outcomes.append(error)
    finally:
        waited.set()


def test_wait_racing_with_watchdog_group_check_does_not_report_lost_ownership(
    real_groups: Callable[[bool], tuple[OwnedProcess, subprocess.Popen[bytes]]],
    workers: list[threading.Thread],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owned, sentinel = real_groups(True)
    pgid = os.getpgid(owned.pid)
    checking = threading.Event()
    release = threading.Event()
    waiting = threading.Event()
    waited = threading.Event()
    outcomes: list[object] = []
    deliveries: list[int] = []
    real_killpg = os.killpg

    def signal_group(group: int, number: int) -> None:
        assert group == pgid
        assert sentinel.poll() is None
        if number and threading.current_thread() is workers[0]:
            assert not waited.is_set(), "watchdog signaled after ownership was released"
            deliveries.append(number)
        real_killpg(group, number)

    _pause_post_term_check(monkeypatch, pgid, workers, deliveries, checking, release)
    monkeypatch.setattr(os, "killpg", signal_group)
    watchdog = Watchdog(owned, timeout_seconds=0, grace_seconds=0)
    collector = threading.Thread(
        target=_collect_exit, args=(owned, waiting, waited, outcomes), daemon=True
    )
    watchdog.start()
    try:
        assert checking.wait(5), "watchdog never reached the post-TERM group check"
        collector.start()
        assert waiting.wait(5)
        # A serialized owner may keep wait() pending until the signal check resumes.
        waited.wait(0.5)
        release.set()
        result = watchdog.join(timeout=5)
        collector.join(timeout=5)
        assert not collector.is_alive()
        assert outcomes == [0]
        assert result == WatchdogResult(True, True, signal.SIGKILL in deliveries)
        assert not workers[0].is_alive()
        assert watchdog.join(timeout=0) == result
        assert sentinel.poll() is None
    finally:
        release.set()
        if collector.ident is not None:
            collector.join(timeout=5)
        watchdog.cancel()
