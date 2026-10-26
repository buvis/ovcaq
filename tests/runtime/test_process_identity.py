from __future__ import annotations

import ctypes
import ctypes.util
import errno
import os
import re
import subprocess
import sys
import time
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
    pid: int, *, status: int = 2, tvsec: int = 1700000000, tvusec: int = 0
) -> bytes:
    """Build the kernel's process-info record the probe reads its fields from."""
    payload = bytearray(PROC_BSDINFO_SIZE)
    for offset, width, value in (
        (PBI_STATUS_OFFSET, 4, status),
        (PBI_PID_OFFSET, 4, pid),
        (PBI_START_TVSEC_OFFSET, 8, tvsec),
        (PBI_START_TVUSEC_OFFSET, 8, tvusec),
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


def test_process_probe_unavailable_is_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    assert process_identity(os.getpid()) is not None
    monkeypatch.setattr(ctypes.util, "find_library", lambda name: None)
    with pytest.raises(CommandError) as raised:
        process_identity(os.getpid())

    error = raised.value
    assert error.code is ErrorCode.PROCESS_PROBE
    assert error.code.value == "process_probe"
    assert error.exit_code == EXIT_CODES[ErrorCode.PROCESS_PROBE] == 12
    assert "ovcaq doctor" in str(error)
    assert sys.platform.lower() in str(error).lower()
    # The non-positive guard answers before any library load, broken or not.
    assert process_identity(0) is None
    assert process_identity(-1) is None


def test_denied_probe_is_typed_failure_while_absent_pid_is_simply_gone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = os.getpid()
    record = _bsdinfo(pid)
    for denial in (errno.EPERM, errno.EACCES):
        calls = _kernel_answers(monkeypatch, record, written=0, errno_value=denial)
        with pytest.raises(CommandError) as raised:
            process_identity(pid)
        assert raised.value.code is ErrorCode.PROCESS_PROBE
        assert raised.value.exit_code == 12
        assert calls == [(pid, PROC_PIDTBSDINFO, 0, PROC_BSDINFO_SIZE)]

    calls = _kernel_answers(monkeypatch, record, written=0, errno_value=errno.ESRCH)
    assert process_identity(pid) is None
    assert calls == [(pid, PROC_PIDTBSDINFO, 0, PROC_BSDINFO_SIZE)]


@pytest.mark.parametrize(
    "written",
    [1, 64, PROC_BSDINFO_SIZE - 1, PROC_BSDINFO_SIZE + 1, 2 * PROC_BSDINFO_SIZE],
)
def test_incomplete_kernel_record_is_typed_failure(
    monkeypatch: pytest.MonkeyPatch, written: int
) -> None:
    pid = os.getpid()
    _kernel_answers(monkeypatch, _bsdinfo(pid), written=written)
    with pytest.raises(CommandError) as raised:
        process_identity(pid)
    assert raised.value.code is ErrorCode.PROCESS_PROBE
    assert raised.value.exit_code == 12


def test_identity_belonging_to_another_pid_is_typed_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = os.getpid()
    _kernel_answers(monkeypatch, _bsdinfo(pid + 1), written=PROC_BSDINFO_SIZE)
    with pytest.raises(CommandError) as raised:
        process_identity(pid)
    assert raised.value.code is ErrorCode.PROCESS_PROBE
    assert raised.value.exit_code == 12


@pytest.mark.parametrize(
    "tvsec,tvusec,expected",
    [(1700000000, 42, "1700000000.000042"), (7, 987654, "7.987654")],
)
def test_start_token_pads_microseconds_to_six_digits(
    monkeypatch: pytest.MonkeyPatch, tvsec: int, tvusec: int, expected: str
) -> None:
    pid = os.getpid()
    record = _bsdinfo(pid, tvsec=tvsec, tvusec=tvusec)
    _kernel_answers(monkeypatch, record, written=PROC_BSDINFO_SIZE)
    assert process_identity(pid) == ProcessIdentity(pid=pid, started=expected)
    assert re.fullmatch(r"\d+\.\d{6}", expected)
    assert process_matches(ProcessIdentity(pid=pid, started=expected)) is True
    assert process_matches(ProcessIdentity(pid=pid, started=f"{expected}0")) is False


def test_kernel_zombie_status_has_no_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    pid = os.getpid()
    _kernel_answers(monkeypatch, _bsdinfo(pid, status=SZOMB), written=PROC_BSDINFO_SIZE)
    assert process_identity(pid) is None
    assert (
        process_matches(ProcessIdentity(pid=pid, started="1700000000.000000")) is False
    )


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
