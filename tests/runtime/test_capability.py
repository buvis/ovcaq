from __future__ import annotations

import errno
import fcntl
import os
import select
import signal
import stat
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from ovcaq.runtime.capability import (
    CapabilityResult,
    probe_platform,
    require_process_capabilities,
)

_NAMES = (
    "platform",
    "advisory_lock",
    "process_group",
    "group_signal",
    "directory_fsync",
)
_DARWIN_ONLY = pytest.mark.skipif(
    sys.platform != "darwin", reason="personal-cutover integration requires macOS"
)
_WORKER = """
import os
import signal
import sys

signal.signal(signal.SIGUSR1, lambda *_: print("signalled", flush=True))
print(f"ready {os.getpid()} {os.getpgrp()}", flush=True)
for line in sys.stdin:
    if line.strip() == "ping":
        print("alive", flush=True)
"""


def _line(worker: subprocess.Popen[str]) -> str:
    assert worker.stdout is not None
    ready, _, _ = select.select([worker.stdout], [], [], 5)
    assert ready, "worker did not respond within five seconds"
    line = worker.stdout.readline()
    assert line, "worker closed its output before responding"
    return line.rstrip("\n")


@contextmanager
def _isolated_worker() -> Iterator[subprocess.Popen[str]]:
    worker = subprocess.Popen(
        [sys.executable, "-c", _WORKER],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        start_new_session=True,
    )
    try:
        assert _line(worker) == f"ready {worker.pid} {worker.pid}"
        yield worker
    finally:
        if worker.poll() is None:
            worker.kill()
        worker.communicate(timeout=5)


@pytest.fixture
def supported_darwin() -> tuple[CapabilityResult, ...]:
    if sys.platform != "darwin":
        pytest.skip("supported personal-cutover baseline requires macOS")
    results = probe_platform(platform_name="darwin")
    assert tuple(result.name for result in results) == _NAMES
    assert all(result.status == "supported" for result in results), results
    return results


@pytest.mark.parametrize("status", ["supported", "unsupported", "degraded"])
@pytest.mark.parametrize("field", ["name", "status", "detail"])
def test_capability_facts_preserve_their_values_and_cannot_be_mutated(
    status: str,
    field: str,
) -> None:
    result = CapabilityResult(name="platform", status=status, detail="probe evidence")
    assert (result.name, result.status, result.detail) == (
        "platform",
        status,
        "probe evidence",
    )
    with pytest.raises(FrozenInstanceError):
        setattr(result, field, "changed")


def test_platform_probe_returns_exactly_five_facts_in_a_stable_order() -> None:
    first = probe_platform()
    second = probe_platform()
    assert isinstance(first, tuple)
    assert isinstance(second, tuple)
    assert tuple(result.name for result in first) == _NAMES
    assert tuple(result.name for result in second) == _NAMES
    for result in (*first, *second):
        assert isinstance(result, CapabilityResult)
        assert result.status in {"supported", "unsupported", "degraded"}
        assert isinstance(result.detail, str)


@pytest.mark.parametrize("platform_name", ["linux", "win32", "freebsd", ""])
def test_other_platforms_cannot_pass_personal_cutover(platform_name: str) -> None:
    results = probe_platform(platform_name=platform_name)
    assert tuple(result.name for result in results) == _NAMES
    assert all(result.status in {"unsupported", "degraded"} for result in results)
    with pytest.raises(RuntimeError):
        require_process_capabilities(results)


def _ineffective_lock(descriptor: int, operation: int) -> None:
    # Successful return does not exclude another opener of the same inode.
    return None


@_DARWIN_ONLY
@pytest.mark.parametrize("fact", ["advisory_lock", "process_group", "group_signal"])
def test_probes_reject_successful_os_calls_that_do_not_provide_the_capability(
    monkeypatch: pytest.MonkeyPatch,
    fact: str,
) -> None:
    real_popen = subprocess.Popen
    real_killpg = os.killpg
    parent_group = os.getpgrp()
    workers: list[subprocess.Popen[str]] = []

    def spawn(*args: object, **kwargs: object) -> subprocess.Popen[str]:
        if fact == "process_group":
            kwargs["start_new_session"] = False
            kwargs["process_group"] = None
            kwargs["preexec_fn"] = None
        worker = real_popen(*args, **kwargs)
        workers.append(worker)
        return worker

    def deliver_signal(group: int, number: int) -> None:
        if fact == "group_signal" and number != 0:
            # Permission/existence checks still succeed, but delivery is broken.
            return
        if group == parent_group and number != 0:
            # A failed isolation probe must never signal the test runner's group.
            raise PermissionError(errno.EPERM, "refusing the unrelated parent group")
        real_killpg(group, number)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(subprocess, "Popen", spawn)
            patch.setattr(os, "killpg", deliver_signal)
            if fact == "advisory_lock":
                patch.setattr(fcntl, "flock", _ineffective_lock)
            results = probe_platform(platform_name="darwin")
    finally:
        # Keep cleanup independent of the deliberately broken group signalling.
        for worker in workers:
            if worker.poll() is None:
                worker.kill()
            worker.wait(timeout=5)

    assert tuple(result.name for result in results) == _NAMES
    observed = {result.name: result.status for result in results}
    assert observed[fact] in {"unsupported", "degraded"}, (
        f"{fact} was reported supported without demonstrating its behavior"
    )
    with pytest.raises(RuntimeError):
        require_process_capabilities(results)


def test_preflight_accepts_a_complete_supported_darwin_probe(
    supported_darwin: tuple[CapabilityResult, ...],
) -> None:
    assert require_process_capabilities(supported_darwin) is None


@pytest.mark.parametrize("name", _NAMES)
@pytest.mark.parametrize("status", ["unsupported", "degraded"])
def test_preflight_rejects_each_required_fact_when_it_is_not_supported(
    supported_darwin: tuple[CapabilityResult, ...],
    name: str,
    status: str,
) -> None:
    results = tuple(
        replace(result, status=status) if result.name == name else result
        for result in supported_darwin
    )
    with pytest.raises(RuntimeError):
        require_process_capabilities(results)


def test_preflight_rejects_an_empty_result_set() -> None:
    with pytest.raises(RuntimeError):
        require_process_capabilities(())


@pytest.mark.parametrize("name", _NAMES)
def test_preflight_rejects_each_missing_required_fact(
    supported_darwin: tuple[CapabilityResult, ...],
    name: str,
) -> None:
    results = tuple(result for result in supported_darwin if result.name != name)
    with pytest.raises(RuntimeError):
        require_process_capabilities(results)


@pytest.mark.parametrize("name", [*_NAMES, "unrecognized"])
def test_preflight_rejects_duplicate_or_unknown_facts(
    supported_darwin: tuple[CapabilityResult, ...],
    name: str,
) -> None:
    extra = CapabilityResult(name=name, status="supported", detail="extra fact")
    with pytest.raises(RuntimeError):
        require_process_capabilities((*supported_darwin, extra))


@_DARWIN_ONLY
@pytest.mark.parametrize(
    ("boundary", "fact"),
    [
        ("lock", "advisory_lock"),
        ("spawn", "process_group"),
        ("signal", "group_signal"),
        ("fsync", "directory_fsync"),
    ],
)
def test_failed_os_probes_do_not_claim_support_or_pass_preflight(
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    fact: str,
) -> None:
    def unavailable(*args: object, **kwargs: object) -> None:
        raise OSError(errno.ENOTSUP, "operation unavailable")

    real_fsync = os.fsync

    def reject_directory_fsync(descriptor: int) -> None:
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise OSError(errno.ENOTSUP, "directory fsync unavailable")
        real_fsync(descriptor)

    with monkeypatch.context() as patch:
        if boundary == "lock":
            patch.setattr(fcntl, "flock", unavailable)
        elif boundary == "spawn":
            patch.setattr(subprocess, "Popen", unavailable)
        elif boundary == "signal":
            patch.setattr(os, "killpg", unavailable)
        else:
            patch.setattr(os, "fsync", reject_directory_fsync)
        results = probe_platform(platform_name="darwin")

    assert tuple(result.name for result in results) == _NAMES
    observed = {result.name: result.status for result in results}
    assert observed[fact] in {"unsupported", "degraded"}
    with pytest.raises(RuntimeError):
        require_process_capabilities(results)


@_DARWIN_ONLY
def test_macos_advisory_lock_excludes_a_real_competing_process(
    tmp_path: Path,
    supported_darwin: tuple[CapabilityResult, ...],
) -> None:
    path = tmp_path / "capability.lock"
    contender = """
import fcntl
import sys

with open(sys.argv[1], "rb") as stream:
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("contended")
    else:
        print("acquired")
"""
    with path.open("w+b") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        blocked = subprocess.run(
            [sys.executable, "-c", contender, str(path)],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        assert blocked.stdout.strip() == "contended"
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        released = subprocess.run(
            [sys.executable, "-c", contender, str(path)],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        assert released.stdout.strip() == "acquired"
    assert require_process_capabilities(supported_darwin) is None


@_DARWIN_ONLY
def test_macos_process_groups_receive_signals_without_harming_an_unrelated_process(
    supported_darwin: tuple[CapabilityResult, ...],
) -> None:
    with _isolated_worker() as target, _isolated_worker() as unrelated:
        assert os.getpgid(target.pid) == target.pid
        assert os.getpgid(unrelated.pid) == unrelated.pid
        assert target.pid != unrelated.pid
        assert target.pid != os.getpgrp()
        os.killpg(target.pid, signal.SIGUSR1)
        assert _line(target) == "signalled"

        results = probe_platform(platform_name="darwin")
        assert require_process_capabilities(results) is None
        assert unrelated.stdin is not None
        unrelated.stdin.write("ping\n")
        unrelated.stdin.flush()
        assert _line(unrelated) == "alive"
        assert unrelated.poll() is None
    assert require_process_capabilities(supported_darwin) is None


@_DARWIN_ONLY
def test_macos_can_fsync_a_real_directory(
    tmp_path: Path,
    supported_darwin: tuple[CapabilityResult, ...],
) -> None:
    descriptor = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        assert stat.S_ISDIR(os.fstat(descriptor).st_mode)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    assert require_process_capabilities(supported_darwin) is None
