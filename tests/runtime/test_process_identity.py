from __future__ import annotations

import ctypes
import ctypes.util
import errno
import os
import random
import re
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
from tests.runtime.fleet_registry_helpers import _dead_pid, _entry

from ovcaq.errors import EXIT_CODES, CommandError, ErrorCode
from ovcaq.runtime.registry import (
    PBI_PID_OFFSET,
    PBI_START_TVSEC_OFFSET,
    PBI_START_TVUSEC_OFFSET,
    PBI_STATUS_OFFSET,
    PROC_BSDINFO_SIZE,
    PROC_PIDTBSDINFO,
    SZOMB,
    FleetRegistry,
    ProcessIdentity,
    RegistrySnapshot,
    process_identity,
    process_matches,
)

# Darwin's <sys/proc_info.h>, spelled out so the tests below never borrow the
# module's own idea of the layout: struct proc_bsdinfo is 136 bytes, pbi_status
# sits at 4 (pbi_xstatus at 8), pbi_pid at 12, pbi_start_tvsec at 120 and
# pbi_start_tvusec at 128; PROC_PIDTBSDINFO is flavor 3 and SZOMB is 5.
_FLAVOR = 3
_RECORD_SIZE = 136
_STATUS_OFFSET = 4
_PID_OFFSET = 12
_TVSEC_OFFSET = 120
_TVUSEC_OFFSET = 128
_SRUN = 2
_SZOMB = 5


def test_process_identity_requires_alive_pid_and_matching_start() -> None:
    identity = process_identity(os.getpid())
    assert isinstance(identity, ProcessIdentity)
    assert identity.pid == os.getpid()
    assert isinstance(identity.started, str)
    assert identity.started
    assert process_matches(identity) is True
    assert (
        process_matches(replace(identity, started=identity.started + "-recycled"))
        is False
    )
    dead_pid = _dead_pid()
    assert process_identity(dead_pid) is None
    assert (
        process_matches(ProcessIdentity(pid=dead_pid, started=identity.started))
        is False
    )


def test_child_identity_stays_live_until_process_exit(tmp_path: Path) -> None:
    parent = process_identity(os.getpid())
    assert parent is not None
    # Separate process starts even on platforms with second-resolution tokens.
    time.sleep(1.1)
    with subprocess.Popen(
        [sys.executable, "-c", "import sys; sys.stdin.read()"],
        stdin=subprocess.PIPE,
    ) as child:
        try:
            identity = process_identity(child.pid)
            assert isinstance(identity, ProcessIdentity)
            assert identity.pid == child.pid
            assert isinstance(identity.started, str)
            assert identity.started
            assert identity.started != parent.started
            assert process_identity(child.pid) == identity
            assert process_matches(identity) is True

            registry = FleetRegistry(tmp_path)
            entry = replace(
                _entry(tmp_path),
                pid=identity.pid,
                process_start=identity.started,
            )
            path = registry.publish(entry)
            expected = RegistrySnapshot(live=(entry,), malformed=(), stale=())
            assert registry.snapshot() == expected
            registry.prune()
            assert path.exists()
            assert registry.snapshot() == expected
            assert process_identity(child.pid) == identity
            assert child.poll() is None
        finally:
            child.kill()
            child.wait(timeout=5)

    assert process_identity(identity.pid) is None
    assert process_matches(identity) is False
    assert registry.snapshot() == RegistrySnapshot(live=(), malformed=(), stale=(path,))
    registry.prune()
    assert not path.exists()
    assert registry.snapshot() == RegistrySnapshot(live=(), malformed=(), stale=())


def _bsdinfo(
    pid: int, *, status: int = _SRUN, tvsec: int = 1700000000, tvusec: int = 0
) -> bytes:
    """Build the kernel's process-info record at the offsets Darwin defines."""
    payload = bytearray(_RECORD_SIZE)
    for offset, width, value in (
        (_STATUS_OFFSET, 4, status),
        (_PID_OFFSET, 4, pid),
        (_TVSEC_OFFSET, 8, tvsec),
        (_TVUSEC_OFFSET, 8, tvusec),
    ):
        payload[offset : offset + width] = value.to_bytes(width, sys.byteorder)
    return bytes(payload)


def _kernel_answers(
    monkeypatch: pytest.MonkeyPatch,
    payload: bytes,
    written: int,
    errno_value: int = 0,
) -> list[tuple[int, int, int, int]]:
    """Make the kernel probe answer with `written` bytes of `payload` and `errno_value`."""
    calls: list[tuple[int, int, int, int]] = []

    class _Library:
        def proc_pidinfo(
            self, pid: int, flavor: int, argument: int, buffer: object, size: int
        ) -> int:
            calls.append((pid, flavor, argument, size))
            ctypes.memmove(buffer, payload, min(len(payload), size))
            ctypes.set_errno(errno_value)
            return written

    monkeypatch.setattr("ovcaq.runtime.registry._libproc", lambda: _Library())
    return calls


def _probe_failure(call: Callable[[], object]) -> CommandError:
    """Assert `call` fails with the typed probe error and hand the error back."""
    with pytest.raises(CommandError) as raised:
        call()

    error = raised.value
    assert error.code is ErrorCode.PROCESS_PROBE
    assert error.code.value == "process_probe"
    assert error.exit_code == EXIT_CODES[ErrorCode.PROCESS_PROBE] == 12
    return error


def test_probe_reads_the_darwin_proc_bsdinfo_layout() -> None:
    """The probe must read pbi_status, not the pbi_xstatus field beside it."""
    assert PROC_PIDTBSDINFO == _FLAVOR
    assert PROC_BSDINFO_SIZE == _RECORD_SIZE
    assert PBI_STATUS_OFFSET == _STATUS_OFFSET
    assert PBI_PID_OFFSET == _PID_OFFSET
    assert PBI_START_TVSEC_OFFSET == _TVSEC_OFFSET
    assert PBI_START_TVUSEC_OFFSET == _TVUSEC_OFFSET
    assert SZOMB == _SZOMB


def test_process_probe_unavailable_is_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    assert process_identity(os.getpid()) is not None
    monkeypatch.setattr(sys, "platform", "freebsd13")
    monkeypatch.setattr(ctypes.util, "find_library", lambda name: None)
    error = _probe_failure(lambda: process_identity(os.getpid()))
    assert "ovcaq doctor" in str(error)
    assert "freebsd13" in str(error).lower()


def test_unloadable_probe_library_is_typed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A library path that resolves but refuses to load is a typed failure, not a crash."""
    missing = tmp_path / "libproc.dylib"
    monkeypatch.setattr(ctypes.util, "find_library", lambda name: str(missing))
    error = _probe_failure(lambda: process_identity(os.getpid()))
    assert "ovcaq doctor" in str(error)
    assert sys.platform.lower() in str(error).lower()


@pytest.mark.parametrize("pid", [0, -1, -2, -os.getpid(), -(2**31)])
def test_non_positive_pid_is_gone_without_touching_the_kernel(
    monkeypatch: pytest.MonkeyPatch, pid: int
) -> None:
    def refuse() -> object:
        raise AssertionError(f"the kernel library was loaded for pid {pid}")

    monkeypatch.setattr("ovcaq.runtime.registry._libproc", refuse)
    assert process_identity(pid) is None
    assert (
        process_matches(ProcessIdentity(pid=pid, started="1700000000.000000")) is False
    )


@pytest.mark.parametrize(
    "errno_value",
    [errno.EPERM, errno.EACCES, errno.EINVAL, errno.ENOMEM, errno.EFAULT, 0, errno.ESRCH],
)
def test_absent_pid_is_simply_gone_whatever_errno_the_kernel_leaves(
    monkeypatch: pytest.MonkeyPatch, errno_value: int
) -> None:
    """A zero-byte answer means gone, regardless of errno (spec: size 0 or 136)."""
    pid = os.getpid()
    record = _bsdinfo(pid)
    calls = _kernel_answers(monkeypatch, record, written=0, errno_value=errno_value)
    assert process_identity(pid) is None
    assert calls == [(pid, _FLAVOR, 0, _RECORD_SIZE)]


_SHORT_WRITES = tuple(
    sorted(
        (
            {1, 2, 7, 64, 100, _RECORD_SIZE - 1, _RECORD_SIZE + 1, 2 * _RECORD_SIZE}
            | set(random.sample(range(1, 4 * _RECORD_SIZE), 8))
        )
        - {_RECORD_SIZE}
    )
)


@pytest.mark.parametrize("written", _SHORT_WRITES)
def test_incomplete_kernel_record_is_typed_failure(
    monkeypatch: pytest.MonkeyPatch, written: int
) -> None:
    """Any byte count other than a whole record is a failure, not a parsed identity."""
    pid = os.getpid()
    _kernel_answers(monkeypatch, _bsdinfo(pid), written=written)
    _probe_failure(lambda: process_identity(pid))


@pytest.mark.parametrize(
    "record_pid",
    [
        1,
        2,
        os.getpid() - 1,
        os.getpid() + 1,
        os.getpid() + 7,
        os.getpid() + 4242,
    ],
)
def test_identity_belonging_to_another_pid_is_typed_failure(
    monkeypatch: pytest.MonkeyPatch, record_pid: int
) -> None:
    pid = os.getpid()
    assert record_pid != pid
    _kernel_answers(monkeypatch, _bsdinfo(record_pid), written=_RECORD_SIZE)
    _probe_failure(lambda: process_identity(pid))


@pytest.mark.parametrize(
    "tvsec,tvusec",
    [
        (1700000000, 42),
        (7, 987654),
        (1, 0),
        (1700000001, 1),
        (999, 999999),
        (1700000002, 100000),
        (random.randrange(1, 2**31), random.randrange(0, 1000000)),
    ],
)
def test_start_token_pads_microseconds_to_six_digits(
    monkeypatch: pytest.MonkeyPatch, tvsec: int, tvusec: int
) -> None:
    pid = os.getpid()
    record = _bsdinfo(pid, tvsec=tvsec, tvusec=tvusec)
    _kernel_answers(monkeypatch, record, written=_RECORD_SIZE)
    identity = process_identity(pid)
    assert isinstance(identity, ProcessIdentity)
    assert identity.pid == pid

    token = identity.started
    assert re.fullmatch(r"\d+\.\d{6}", token)
    seconds, _, micros = token.partition(".")
    assert int(seconds) == tvsec
    assert int(micros) == tvusec
    assert float(token) == pytest.approx(tvsec + tvusec / 1e6, abs=1e-5)
    assert process_matches(ProcessIdentity(pid=pid, started=token)) is True
    assert process_matches(ProcessIdentity(pid=pid, started=f"{token}0")) is False


def test_kernel_zombie_status_has_no_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    pid = os.getpid()
    _kernel_answers(monkeypatch, _bsdinfo(pid, status=_SZOMB), written=_RECORD_SIZE)
    assert process_identity(pid) is None
    assert (
        process_matches(ProcessIdentity(pid=pid, started="1700000000.000000")) is False
    )


def test_probe_failure_never_answers_that_a_process_is_gone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """process_matches must raise on a genuinely broken probe; False would kill a live run."""
    identity = ProcessIdentity(pid=os.getpid(), started="1700000000.000042")
    _kernel_answers(monkeypatch, _bsdinfo(identity.pid), written=7)
    _probe_failure(lambda: process_matches(identity))

    _kernel_answers(monkeypatch, _bsdinfo(identity.pid + 1), written=_RECORD_SIZE)
    _probe_failure(lambda: process_matches(identity))


_SIGNAL_SPY = """
import signal, sys
path = sys.argv[1]
def mark(number, frame):
    with open(path, "a") as stream:
        stream.write(f"{number}\\n")
for number in (signal.SIGCONT, signal.SIGUSR1, signal.SIGUSR2):
    signal.signal(number, mark)
sys.stdout.write("ready\\n")
sys.stdout.flush()
sys.stdin.read()
"""


def test_probe_does_not_signal_the_process_it_inspects(tmp_path: Path) -> None:
    marker = tmp_path / "signals"
    with subprocess.Popen(
        [sys.executable, "-c", _SIGNAL_SPY, str(marker)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    ) as child:
        assert child.stdin is not None
        assert child.stdout is not None
        try:
            assert child.stdout.readline() == "ready\n"
            identity = process_identity(child.pid)
            assert isinstance(identity, ProcessIdentity)
            for _ in range(5):
                assert process_identity(child.pid) == identity
                assert process_matches(identity) is True
            assert not marker.exists()

            # Control: a real signal does reach the child and lands in the marker.
            os.kill(child.pid, signal.SIGUSR1)
            deadline = time.monotonic() + 5
            recorded: list[str] = []
            while time.monotonic() < deadline and not recorded:
                recorded = marker.read_text().split() if marker.exists() else []
                time.sleep(0.01)
            assert recorded == [str(int(signal.SIGUSR1))]
        finally:
            child.stdin.close()
            child.wait(timeout=5)


def test_zombie_process_has_no_identity() -> None:
    parent = process_identity(os.getpid())
    assert isinstance(parent, ProcessIdentity)
    child = subprocess.Popen(
        [sys.executable, "-c", "import sys; sys.stdin.read()"], stdin=subprocess.PIPE
    )
    assert child.stdin is not None
    try:
        live = process_identity(child.pid)
        assert isinstance(live, ProcessIdentity)
        assert live.pid == child.pid
        assert re.fullmatch(r"\d+\.\d{6}", live.started)
        assert re.fullmatch(r"\d+\.\d{6}", parent.started)
        assert live.started != parent.started
        assert process_matches(live) is True
        assert process_matches(replace(live, started=live.started[:-1])) is False
        assert process_matches(replace(live, pid=parent.pid)) is False

        child.stdin.close()
        # Wait for exit without reaping, so the child is observed as a zombie.
        os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOWAIT)
        assert process_identity(child.pid) is None
        assert process_matches(live) is False
        assert process_matches(parent) is True
    finally:
        child.stdin.close()
        assert child.wait(timeout=5) == 0
    assert process_identity(child.pid) is None
