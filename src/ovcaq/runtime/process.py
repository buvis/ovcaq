"""Own an agent and its descendants through a persistent group leader."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import FrameType
from typing import BinaryIO, Self, cast

from ovcaq.runtime.registry import ProcessIdentity, process_identity, process_matches


@dataclass(frozen=True)
class ProcessExit:
    returncode: int
    signal: int | None
    timed_out: bool
    term_sent: bool
    kill_sent: bool


class ProcessOwnershipError(RuntimeError):
    """The recorded group leader no longer proves ownership."""


class SupervisorSignal(Exception):
    """A supervisor signal whose cleanup belongs to the caller."""

    def __init__(self, signal_number: int) -> None:
        self.signal_number = signal_number
        super().__init__(f"Supervisor received signal {signal_number}")


def supervisor_exit_code(error: BaseException) -> int:
    """Preserve the shell exit status of a supervisor termination signal."""
    if isinstance(error, SupervisorSignal):
        return 128 + error.signal_number
    if isinstance(error, KeyboardInterrupt):
        return 130
    raise TypeError("Expected a supervisor signal or keyboard interrupt")


@contextmanager
def supervisor_signal_scope() -> Iterator[None]:
    """Temporarily translate termination signals into a cleanup exception."""
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("Supervisor signal scope requires the main thread")

    def received(number: int, frame: FrameType | None) -> None:
        raise SupervisorSignal(number)

    previous = {}
    try:
        for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            previous[number] = signal.getsignal(number)
            signal.signal(number, received)
        yield
    finally:
        for number, handler in reversed(previous.items()):
            signal.signal(number, handler)


class OwnedProcess:
    def __init__(
        self,
        agent: subprocess.Popen[bytes],
        anchor: subprocess.Popen[bytes],
        identity: ProcessIdentity,
    ) -> None:
        self._agent = agent
        self._anchor = anchor
        self._identity = identity
        self._ownership_lock = threading.RLock()
        self._group_killed = False
        self._released = False

    @classmethod
    def spawn(
        cls,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str] | None = None,
    ) -> Self:
        if (
            not isinstance(argv, (list, tuple))
            or not argv
            or any(not isinstance(argument, str) or not argument for argument in argv)
        ):
            raise ValueError(
                "argv must be a nonempty list or tuple of nonempty strings"
            )
        anchor = subprocess.Popen(
            [sys.executable, "-m", "ovcaq.runtime._group_anchor"],
            shell=False,
            process_group=0,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        assert anchor.stdin is not None
        assert anchor.stdout is not None
        try:
            ready = anchor.stdout.read(1)
            anchor.stdout.close()
            if ready != b"1":
                raise ProcessOwnershipError("Group anchor did not become ready")
            identity = process_identity(anchor.pid)
            if identity is None:
                raise ProcessOwnershipError("Cannot identify group anchor")
            agent = subprocess.Popen(
                argv,
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                process_group=anchor.pid,
                cwd=cwd,
                env=env,
            )
        except BaseException:
            anchor.stdout.close()
            anchor.stdin.close()
            anchor.wait()
            raise
        return cls(agent, anchor, identity)

    @property
    def pid(self) -> int:
        return self._agent.pid

    @property
    def stdout(self) -> BinaryIO:
        assert self._agent.stdout is not None
        return cast(BinaryIO, self._agent.stdout)

    def poll(self) -> int | None:
        return self._agent.poll()

    def wait(self, timeout: float | None = None) -> int:
        returncode = self._agent.wait(timeout=timeout)
        with self._ownership_lock:
            if self._released:
                return returncode
            # Retain ownership until every group member has received SIGKILL.
            # Reaping the anchor first could make its group number reusable.
            self.signal_group(signal.SIGKILL)
            assert self._anchor.stdin is not None
            self._anchor.stdin.close()
            self._anchor.wait(timeout=timeout)
            self._released = True
        return returncode

    def signal_group(self, signal_number: int) -> bool:
        with self._ownership_lock:
            if self._released or self._group_killed:
                return False
            if self._anchor.poll() is not None:
                try:
                    os.killpg(self._anchor.pid, 0)
                except ProcessLookupError:
                    return False
                raise ProcessOwnershipError("Group remains without its owned anchor")
            if not process_matches(self._identity):
                raise ProcessOwnershipError("Group anchor identity changed")
            try:
                if os.getpgid(self._anchor.pid) != self._anchor.pid:
                    raise ProcessOwnershipError("Group anchor moved to another group")
                os.killpg(self._anchor.pid, signal_number)
            except ProcessLookupError:
                try:
                    os.killpg(self._anchor.pid, 0)
                except ProcessLookupError:
                    return False
                raise ProcessOwnershipError("Group anchor disappeared") from None
            if signal_number == signal.SIGKILL:
                self._group_killed = True
            return True

    def collect_exit(
        self, *, timed_out: bool, term_sent: bool, kill_sent: bool
    ) -> ProcessExit:
        returncode = self.wait()
        return ProcessExit(
            returncode,
            -returncode if returncode < 0 else None,
            timed_out,
            term_sent,
            kill_sent,
        )
