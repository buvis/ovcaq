from __future__ import annotations

import errno
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
from tests.workflow_client.conftest import BUNDLE, process_ended

from ovcaq.workflow_client import (
    JOIN_SECONDS,
    ControllerClient,
    ControllerConfig,
    ControllerTimeoutError,
    _kill_group,
)


def _kill_quietly(pid: int) -> None:
    """Best-effort cleanup of a process a failed assertion may have left."""
    try:
        os.kill(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def _await_pids(path: Path, count: int, within: float = 5.0) -> list[int]:
    """The pids a controller recorded, waited for instead of assumed.

    A controller killed before it writes the file would otherwise surface as
    an unreadable file rather than as a diagnosable failure.
    """
    deadline = time.monotonic() + within
    while True:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        recorded = text.split()
        if len(recorded) == count:
            return [int(pid) for pid in recorded]
        assert time.monotonic() < deadline, (
            f"controller did not record {count} pid(s) in {path} "
            f"within {within}s, got {text!r}"
        )
        time.sleep(0.05)


class _BlockingProcess:
    """A Popen-like object whose .wait() would block indefinitely without a
    bound, used to prove _kill_group() does not simply call process.wait()
    with no timeout after os.killpg fails to deliver the signal."""

    def __init__(self, never_set: threading.Event) -> None:
        self.pid = 4242
        self.waits: list[float | None] = []
        self._never_set = never_set

    def wait(self, timeout: float | None = None) -> int:
        self.waits.append(timeout)
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
    # A denied signal does not excuse skipping the reap: the controller is
    # still waited for, and only with a finite bound.
    assert process.waits == [JOIN_SECONDS]
    assert outcome == [None]


def test_kill_group_reports_a_signal_failure_that_is_not_a_denial(monkeypatch) -> None:
    def invalid_signal(pid: int, sig: int) -> None:
        raise OSError(errno.EINVAL, "invalid argument")

    monkeypatch.setattr(os, "killpg", invalid_signal)
    process = _BlockingProcess(threading.Event())

    with pytest.raises(OSError) as caught:
        _kill_group(process)

    # Only "the group is already gone" and "not permitted" are benign;
    # anything else is a defect the caller must see.
    assert caught.value.errno == errno.EINVAL


# A controller that puts a long-sleeping child of its own in its process
# group and records that child's pid, so a test can tell a killed group from
# a killed direct child.
GROUP_MEMBER_CONTROLLER = """\
import subprocess
import sys
import time
from pathlib import Path

member = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(8)"],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
Path(sys.argv[1]).write_text(str(member.pid), encoding="utf-8")
time.sleep(8)
"""


def test_kill_group_ends_a_grandchild_sharing_the_controller_group(
    tmp_path: Path,
) -> None:
    script = tmp_path / "group_controller.py"
    script.write_text(GROUP_MEMBER_CONTROLLER, encoding="utf-8")
    pid_file = tmp_path / "member.pid"
    process = subprocess.Popen(
        [sys.executable, str(script), str(pid_file)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    member = _await_pids(pid_file, 1)[0]
    try:
        _kill_group(process)

        # The whole group dies, not only the direct child.
        assert process_ended(member)
        # And the controller is reaped rather than left as a zombie.
        assert process.returncode == -signal.SIGKILL
    finally:
        _kill_quietly(member)
        _kill_quietly(process.pid)


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


@pytest.mark.parametrize("timeout_seconds", [1, 3])
def test_capture_completes_within_bounded_time_when_a_pipe_stays_open(
    monkeypatch, tmp_path: Path, timeout_seconds: int
) -> None:
    kills: list[tuple[int, int]] = []
    monkeypatch.setattr(os, "killpg", lambda pid, sig: kills.append((pid, sig)))
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
            timeout_seconds=timeout_seconds,
        )
        client = ControllerClient(config)
        started = time.monotonic()

        with pytest.raises(ControllerTimeoutError):
            client._capture(process)

        elapsed = time.monotonic() - started
        # Reporting the timeout is not enough: the group has to be killed.
        assert kills == [(process.pid, signal.SIGKILL)]
        # The configured bound is what is awaited - neither a fixed shorter
        # deadline nor the stream that never ends.
        assert timeout_seconds <= elapsed < timeout_seconds + 3.0
    finally:
        # The write ends are never closed here, modeling the detached
        # descendant the finding describes; close explicitly for test
        # process hygiene rather than relying on garbage collection.
        os.close(write_out)
        os.close(write_err)
        process.stdout.close()
        process.stderr.close()


# A controller that exits at once, but first spawns a descendant in a session
# of its own that inherits the controller's stdout and stderr and holds them
# open for 8 seconds. The pipes therefore outlive the controller, and the
# descendant is outside the controller's process group, so killing that group
# does not close them. A second child stays inside the group on streams of
# its own, so a test can still see whether the group was killed.
DETACHED_DESCENDANT_CONTROLLER = """\
import subprocess
import sys
from pathlib import Path

descendant = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(8)"],
    stdin=subprocess.DEVNULL,
    start_new_session=True,
)
in_group = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(8)"],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
Path(sys.argv[1]).write_text(
    "%d\\n%d\\n" % (descendant.pid, in_group.pid), encoding="utf-8"
)
sys.exit(0)
"""


def test_run_with_detached_descendant_times_out_within_bound(tmp_path: Path) -> None:
    script = tmp_path / "detached_controller.py"
    script.write_text(DETACHED_DESCENDANT_CONTROLLER, encoding="utf-8")
    pid_file = tmp_path / "descendant.pid"
    config = ControllerConfig(
        argv=(sys.executable, str(script), str(pid_file)),
        contract_bundle=BUNDLE,
        actor_file=None,
        project_root=tmp_path,
        timeout_seconds=1,
    )
    client = ControllerClient(config)
    started = time.monotonic()

    with pytest.raises(ControllerTimeoutError) as caught:
        client._run("contract")

    elapsed = time.monotonic() - started
    descendant, in_group = _await_pids(pid_file, 2)
    try:
        assert elapsed < 3.0
        # The report names the bound that was exceeded.
        assert str(config.timeout_seconds) in str(caught.value)
        # The controller's own group was killed before the report.
        assert process_ended(in_group)
        # The descendant is still alive, so the pipes were still open when the
        # call returned: it returned on its own deadline, not on end of stream.
        assert not process_ended(descendant, within=0.0)
    finally:
        _kill_quietly(descendant)
        _kill_quietly(in_group)
