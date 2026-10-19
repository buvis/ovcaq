from __future__ import annotations

import json
import logging
import os
import selectors
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path
from typing import BinaryIO

import pytest

from ovcaq.runtime.process import (
    OwnedProcess,
    ProcessExit,
    ProcessOwnershipError,
    SupervisorSignal,
    supervisor_signal_scope,
)
from ovcaq.runtime.registry import ProcessIdentity, process_identity


def _reject(expected: type[BaseException], operation: Callable[[], object]) -> None:
    with pytest.raises(expected):
        operation()


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


@pytest.fixture
def launched(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[list[tuple[object, dict[str, object], subprocess.Popen[bytes]]]]:
    children: list[tuple[object, dict[str, object], subprocess.Popen[bytes]]] = []
    launches: list[tuple[object, dict[str, object], subprocess.Popen[bytes]]] = []
    real_popen = subprocess.Popen
    real_killpg = os.killpg

    def observe(argv: object, **kwargs: object) -> subprocess.Popen[bytes]:
        child = real_popen(argv, **kwargs)
        children.append((argv, kwargs, child))
        identity_probe = (
            isinstance(argv, (list, tuple))
            and bool(argv)
            and Path(argv[0]).name == "ps"
        )
        if not identity_probe:
            launches.append((argv, kwargs, child))
        return child

    monkeypatch.setattr(subprocess, "Popen", observe)
    yield launches
    for _, kwargs, child in children:
        if child.poll() is None:
            try:
                if kwargs.get("process_group") == 0:
                    real_killpg(child.pid, signal.SIGKILL)
                else:
                    child.kill()
            except ProcessLookupError:
                pass
    for _, _, child in children:
        child.wait(timeout=5)
        for stream in (child.stdin, child.stdout, child.stderr):
            if stream is not None:
                stream.close()


@pytest.mark.parametrize(
    "argv",
    [None, "echo unsafe", b"echo", [], (), [""], ["echo", ""], [1], ["echo", None]],
)
def test_spawn_rejects_invalid_argv_before_starting_any_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    argv: object,
) -> None:
    started: list[object] = []

    def forbid_spawn(*args: object, **kwargs: object) -> None:
        started.append(args)
        raise AssertionError("invalid argv reached process creation")

    monkeypatch.setattr(subprocess, "Popen", forbid_spawn)
    _reject(ValueError, lambda: OwnedProcess.spawn(argv, cwd=tmp_path))
    assert started == []


def _assert_launch_options(
    launched: list[tuple[object, dict[str, object], subprocess.Popen[bytes]]],
    owned: OwnedProcess,
    argv: list[str] | tuple[str, ...],
) -> None:
    assert len(launched) == 2
    anchor_argv, anchor_options, anchor = launched[0]
    agent_argv, agent_options, agent = launched[1]
    assert anchor_argv == [sys.executable, "-m", "ovcaq.runtime._group_anchor"]
    assert anchor_options["shell"] is False
    assert anchor_options["process_group"] == 0
    assert anchor.pid != owned.pid == agent.pid
    assert list(agent_argv) == list(argv)
    assert agent_options["shell"] is False
    assert agent_options["stdin"] == subprocess.DEVNULL
    assert agent_options["stdout"] == subprocess.PIPE
    assert agent_options["stderr"] == subprocess.STDOUT
    assert agent_options["process_group"] == anchor.pid


@pytest.mark.parametrize("container", [list, tuple], ids=["list", "tuple"])
def test_spawn_preserves_literal_argv_eof_merged_bytes_cwd_and_environment(
    tmp_path: Path,
    launched: list[tuple[object, dict[str, object], subprocess.Popen[bytes]]],
    caplog: pytest.LogCaptureFixture,
    container: type,
) -> None:
    caplog.set_level(logging.DEBUG)
    secret = "test-environment-value-must-not-be-logged"
    literals = [
        "; touch injected",
        "$(touch injected)",
        "`touch injected`",
        "$PATH",
        "*",
        "a b",
    ]
    code = (
        "import json, os, sys; "
        "print(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd(), "
        "'env': os.environ['OVCAQ_PROCESS_TEST'], 'stdin': sys.stdin.read(), "
        "'pid': os.getpid(), 'pgid': os.getpgrp()}), flush=True); "
        "os.write(2, b'error\\xff\\n')"
    )
    argv = container([sys.executable, "-c", code, *literals])
    owned = OwnedProcess.spawn(
        argv, cwd=tmp_path, env={**os.environ, "OVCAQ_PROCESS_TEST": secret}
    )
    evidence = json.loads(_line(owned.stdout))
    assert _line(owned.stdout) == b"error\xff\n"
    assert evidence == {
        "argv": literals,
        "cwd": str(tmp_path.resolve()),
        "env": secret,
        "stdin": "",
        "pid": owned.pid,
        "pgid": launched[0][2].pid,
    }
    _assert_launch_options(launched, owned, argv)
    assert owned.wait(timeout=5) == 0
    assert owned.stdout.read() == b""
    assert not (tmp_path / "injected").exists()
    assert secret not in caplog.text


def _spawn_sentinel() -> subprocess.Popen[bytes]:
    sentinel = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import time; print('ready', flush=True); time.sleep(60)",
        ],
        stdout=subprocess.PIPE,
        process_group=0,
    )
    assert sentinel.stdout is not None
    assert _line(sentinel.stdout) == b"ready\n"
    return sentinel


def test_exited_agent_leaves_anchor_and_grandchild_signalable_without_harming_sentinel(
    tmp_path: Path,
    launched: list[tuple[object, dict[str, object], subprocess.Popen[bytes]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    code = (
        "import json, os, signal, time\n"
        "if os.fork():\n    os._exit(23)\n"
        "signal.signal(signal.SIGTERM, lambda *_: os.write(1, b'term\\n'))\n"
        "print(json.dumps({'pid': os.getpid(), 'pgid': os.getpgrp()}), flush=True)\n"
        "deadline = time.monotonic() + 15\n"
        "while time.monotonic() < deadline:\n"
        "    time.sleep(1)\n"
    )
    owned = OwnedProcess.spawn([sys.executable, "-c", code], cwd=tmp_path)
    anchor = launched[0][2]
    descendant = json.loads(_line(owned.stdout))
    sentinel = _spawn_sentinel()
    deadline = time.monotonic() + 5
    while owned.poll() is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert owned.poll() == 23
    assert anchor.poll() is None
    assert descendant["pgid"] == anchor.pid
    assert descendant["pid"] != owned.pid
    assert os.getpgid(descendant["pid"]) == anchor.pid
    assert os.getpgid(sentinel.pid) != anchor.pid
    actual_killpg = os.killpg
    deliveries: list[tuple[int, int]] = []

    def signal_owned_group(pgid: int, number: int) -> None:
        assert pgid == anchor.pid
        actual_killpg(pgid, number)
        if number != 0:
            deliveries.append((pgid, number))

    monkeypatch.setattr(os, "killpg", signal_owned_group)
    assert owned.signal_group(signal.SIGTERM) is True
    assert _line(owned.stdout) == b"term\n"
    assert anchor.poll() is None
    assert sentinel.poll() is None
    assert owned.signal_group(signal.SIGKILL) is True
    monkeypatch.setattr(os, "killpg", actual_killpg)
    assert deliveries == [(anchor.pid, signal.SIGTERM), (anchor.pid, signal.SIGKILL)]
    anchor.wait(timeout=5)
    assert sentinel.poll() is None
    assert owned.wait(timeout=5) == 23
    result = owned.collect_exit(timed_out=True, term_sent=True, kill_sent=True)
    assert result == ProcessExit(23, None, True, True, True)
    assert owned.stdout.read() == b""


def test_live_anchor_pgid_mismatch_refuses_to_signal(
    tmp_path: Path,
    launched: list[tuple[object, dict[str, object], subprocess.Popen[bytes]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owned = OwnedProcess.spawn(
        [
            sys.executable,
            "-c",
            "import time; print('ready', flush=True); time.sleep(60)",
        ],
        cwd=tmp_path,
    )
    assert _line(owned.stdout) == b"ready\n"
    anchor = launched[0][2]
    actual_getpgid = os.getpgid

    def mismatched_group(pid: int) -> int:
        return os.getpgrp() if pid == anchor.pid else actual_getpgid(pid)

    delivered: list[tuple[int, int]] = []
    actual_killpg = os.killpg

    def observe_signal(pgid: int, number: int) -> None:
        delivered.append((pgid, number))
        assert number == 0, "a mismatched anchor must never receive a signal"
        actual_killpg(pgid, number)

    with monkeypatch.context() as patch:
        patch.setattr(os, "getpgid", mismatched_group)
        patch.setattr(os, "killpg", observe_signal)
        with pytest.raises(ProcessOwnershipError):
            owned.signal_group(signal.SIGTERM)
    assert not [number for _, number in delivered if number != 0]
    assert owned.poll() is None
    assert anchor.poll() is None


@dataclass(frozen=True)
class SurvivingGroup:
    owned: OwnedProcess
    anchor: subprocess.Popen[bytes]
    descendant: dict[str, int]
    descendant_identity: ProcessIdentity
    sentinel: subprocess.Popen[bytes]


@pytest.fixture
def surviving_group(
    tmp_path: Path,
    launched: list[tuple[object, dict[str, object], subprocess.Popen[bytes]]],
) -> Iterator[SurvivingGroup]:
    code = (
        "import json, os, signal, time\n"
        "if os.fork():\n    os._exit(0)\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "signal.alarm(15)\n"
        "print(json.dumps({'pid': os.getpid(), 'pgid': os.getpgrp()}), flush=True)\n"
        "time.sleep(15)\n"
    )
    owned = OwnedProcess.spawn([sys.executable, "-c", code], cwd=tmp_path)
    anchor = launched[0][2]
    descendant = json.loads(_line(owned.stdout))
    descendant_identity = process_identity(descendant["pid"])
    assert isinstance(descendant_identity, ProcessIdentity)
    sentinel = _spawn_sentinel()
    real_kill = os.kill
    try:
        deadline = time.monotonic() + 5
        while owned.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        yield SurvivingGroup(owned, anchor, descendant, descendant_identity, sentinel)
    finally:
        if process_identity(descendant["pid"]) == descendant_identity:
            try:
                real_kill(descendant["pid"], signal.SIGKILL)
            except ProcessLookupError:
                pass


def _descendant_stopped(pid: int) -> bool:
    status = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)],
        capture_output=True,
        check=False,
        timeout=2,
    )
    assert status.returncode in (0, 1)
    state = status.stdout.strip()
    return not state or state.startswith(b"Z")


def _observe_cleanup(patch: pytest.MonkeyPatch, group: SurvivingGroup) -> list[int]:
    anchor, sentinel = group.anchor, group.sentinel
    real_killpg = os.killpg
    real_waitpid = os.waitpid
    released: list[int] = []

    def observe_reap(pid: int, options: int) -> tuple[int, int]:
        result = real_waitpid(pid, options)
        if result[0] == anchor.pid:
            assert _descendant_stopped(group.descendant["pid"]), (
                "ownership anchor was reaped while its descendant was still running"
            )
            assert sentinel.poll() is None
            released.append(anchor.pid)
        return result

    def observe_signal(pgid: int, number: int) -> None:
        assert pgid == anchor.pid, "cleanup targeted an unrelated process group"
        assert sentinel.poll() is None
        if number:
            assert not released, "cleanup signaled a released or recycled group"
        # Once released, model the old group number being reassigned to the sentinel.
        real_killpg(sentinel.pid if released else pgid, number)

    patch.setattr(os, "waitpid", observe_reap)
    patch.setattr(os, "killpg", observe_signal)
    return released


def _assert_descendant_output_closed(owned: OwnedProcess) -> None:
    with selectors.DefaultSelector() as selector:
        selector.register(owned.stdout, selectors.EVENT_READ)
        assert selector.select(2), "descendant still holds the output pipe open"
        assert os.read(owned.stdout.fileno(), 1) == b""


@pytest.mark.parametrize("cleanup", ["wait", "collect"])
def test_normal_exit_cleans_surviving_descendant_before_reaping_ownership_anchor(
    surviving_group: SurvivingGroup,
    monkeypatch: pytest.MonkeyPatch,
    cleanup: str,
) -> None:
    owned, anchor = surviving_group.owned, surviving_group.anchor
    descendant, sentinel = surviving_group.descendant, surviving_group.sentinel
    real_getpgid = os.getpgid

    def recycled_group(pid: int) -> int:
        return anchor.pid if pid == anchor.pid else real_getpgid(pid)

    assert owned.poll() == 0
    assert descendant["pgid"] == anchor.pid
    assert os.getpgid(descendant["pid"]) == anchor.pid
    assert not _descendant_stopped(descendant["pid"])
    assert anchor.poll() is None
    assert os.getpgid(sentinel.pid) != anchor.pid
    with monkeypatch.context() as patch:
        released = _observe_cleanup(patch, surviving_group)
        if cleanup == "wait":
            assert owned.wait(timeout=5) == 0
        else:
            assert owned.collect_exit(
                timed_out=False, term_sent=False, kill_sent=False
            ) == ProcessExit(0, None, False, False, False)
        assert _descendant_stopped(descendant["pid"])
        assert released == [anchor.pid]
        patch.setattr(os, "getpgid", recycled_group)
        assert owned.signal_group(signal.SIGTERM) is False
        assert owned.signal_group(signal.SIGKILL) is False
        assert owned.wait(timeout=5) == 0
        assert owned.collect_exit(
            timed_out=False, term_sent=False, kill_sent=False
        ) == ProcessExit(0, None, False, False, False)
    _assert_descendant_output_closed(owned)
    assert sentinel.poll() is None


def _reject_unowned_cleanup_signals(
    patch: pytest.MonkeyPatch,
    group: SurvivingGroup,
    anchor_identity: ProcessIdentity,
    mismatch: str,
) -> list[tuple[str, int, int]]:
    anchor, sentinel = group.anchor, group.sentinel
    real_getpgid = os.getpgid
    real_killpg = os.killpg
    real_kill = os.kill
    attempts: list[tuple[str, int, int]] = []

    def mismatched_identity(identity: ProcessIdentity) -> bool:
        assert identity == anchor_identity
        return False

    def mismatched_group(pid: int) -> int:
        return sentinel.pid if pid == anchor.pid else real_getpgid(pid)

    def reject_group_signal(pgid: int, number: int) -> None:
        attempts.append(("group", pgid, number))
        assert number == 0, "cleanup attempted a signal without valid ownership"
        real_killpg(pgid, number)

    def reject_process_signal(pid: int, number: int) -> None:
        attempts.append(("process", pid, number))
        assert number == 0, "cleanup attempted a signal without valid ownership"
        real_kill(pid, number)

    if mismatch == "identity":
        patch.setattr("ovcaq.runtime.process.process_matches", mismatched_identity)
    else:
        patch.setattr(os, "getpgid", mismatched_group)
    patch.setattr(os, "killpg", reject_group_signal)
    patch.setattr(os, "kill", reject_process_signal)
    return attempts


@pytest.mark.parametrize("cleanup", ["wait", "collect"])
@pytest.mark.parametrize("mismatch", ["identity", "pgid"])
def test_cleanup_refuses_mismatched_ownership_without_signalling_or_releasing_anchor(
    surviving_group: SurvivingGroup,
    monkeypatch: pytest.MonkeyPatch,
    cleanup: str,
    mismatch: str,
) -> None:
    owned, anchor = surviving_group.owned, surviving_group.anchor
    descendant, sentinel = surviving_group.descendant, surviving_group.sentinel
    anchor_identity = process_identity(anchor.pid)
    assert isinstance(anchor_identity, ProcessIdentity)
    real_getpgid = os.getpgid
    assert owned.poll() == 0
    assert anchor.poll() is None
    assert real_getpgid(anchor.pid) == anchor.pid
    assert real_getpgid(descendant["pid"]) == anchor.pid
    assert real_getpgid(sentinel.pid) == sentinel.pid != anchor.pid
    with monkeypatch.context() as patch:
        attempts = _reject_unowned_cleanup_signals(
            patch, surviving_group, anchor_identity, mismatch
        )
        with pytest.raises(ProcessOwnershipError):
            if cleanup == "wait":
                owned.wait(timeout=5)
            else:
                owned.collect_exit(timed_out=False, term_sent=False, kill_sent=False)
        assert [attempt for attempt in attempts if attempt[2] != 0] == []
        assert anchor.poll() is None
        assert real_getpgid(descendant["pid"]) == anchor.pid
        assert sentinel.poll() is None
    # Restored identity must still permit signaling: rejection cannot finalize
    # ownership or close the anchor's lifetime control channel.
    assert owned.signal_group(signal.SIGTERM) is True
    assert anchor.poll() is None
    assert process_identity(anchor.pid) == anchor_identity
    assert process_identity(descendant["pid"]) == surviving_group.descendant_identity
    assert sentinel.poll() is None
    assert owned.wait(timeout=5) == 0
    assert sentinel.poll() is None


@pytest.mark.parametrize("number", [signal.SIGTERM, signal.SIGKILL])
def test_live_anchor_identity_mismatch_refuses_to_signal_even_with_correct_pgid(
    tmp_path: Path,
    launched: list[tuple[object, dict[str, object], subprocess.Popen[bytes]]],
    monkeypatch: pytest.MonkeyPatch,
    number: int,
) -> None:
    owned = OwnedProcess.spawn(
        [
            sys.executable,
            "-c",
            "import time; print('ready', flush=True); time.sleep(60)",
        ],
        cwd=tmp_path,
    )
    assert _line(owned.stdout) == b"ready\n"
    anchor = launched[0][2]
    expected_identity = process_identity(anchor.pid)
    assert isinstance(expected_identity, ProcessIdentity)
    assert os.getpgid(anchor.pid) == anchor.pid
    assert os.getpgid(owned.pid) == anchor.pid
    assert anchor.poll() is None
    delivered: list[tuple[int, int]] = []
    actual_killpg = os.killpg

    def mismatched_identity(identity: ProcessIdentity) -> bool:
        assert identity == expected_identity
        return False

    def observe_signal(pgid: int, signal_number: int) -> None:
        delivered.append((pgid, signal_number))
        assert signal_number == 0, "an identity mismatch must prevent signal delivery"
        actual_killpg(pgid, signal_number)

    with monkeypatch.context() as patch:
        patch.setattr(
            "ovcaq.runtime.process.process_matches", mismatched_identity, raising=False
        )
        patch.setattr(os, "killpg", observe_signal)
        with pytest.raises(ProcessOwnershipError):
            owned.signal_group(number)
    assert not [signal_number for _, signal_number in delivered if signal_number != 0]
    assert owned.poll() is None
    assert anchor.poll() is None
    assert os.getpgid(anchor.pid) == anchor.pid


def test_signal_group_propagates_failed_delivery_instead_of_reporting_success_or_exit(
    tmp_path: Path,
    launched: list[tuple[object, dict[str, object], subprocess.Popen[bytes]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owned = OwnedProcess.spawn(
        [
            sys.executable,
            "-c",
            "import time; print('ready', flush=True); time.sleep(60)",
        ],
        cwd=tmp_path,
    )
    assert _line(owned.stdout) == b"ready\n"
    real_killpg = os.killpg

    def denied(pgid: int, number: int) -> None:
        if number == signal.SIGTERM:
            raise PermissionError("delivery denied")
        real_killpg(pgid, number)

    with monkeypatch.context() as patch:
        patch.setattr(os, "killpg", denied)
        _reject(OSError, lambda: owned.signal_group(signal.SIGTERM))
    assert owned.poll() is None
    assert launched[0][2].poll() is None


@pytest.mark.parametrize(
    "returncode,timed_out,term_sent,kill_sent",
    [
        (0, False, False, False),
        (7, True, False, False),
        (-15, True, True, False),
        (-9, True, True, True),
    ],
)
@pytest.mark.parametrize("cleanup", ["wait", "collect"])
def test_exit_collection_reports_exact_immutable_result_and_reaps_anchor_repeatedly(
    tmp_path: Path,
    launched: list[tuple[object, dict[str, object], subprocess.Popen[bytes]]],
    returncode: int,
    timed_out: bool,
    term_sent: bool,
    kill_sent: bool,
    cleanup: str,
) -> None:
    code = (
        f"import os; os.kill(os.getpid(), {-returncode})"
        if returncode < 0
        else f"raise SystemExit({returncode})"
    )
    owned = OwnedProcess.spawn([sys.executable, "-c", code], cwd=tmp_path)
    anchor = launched[0][2]
    deadline = time.monotonic() + 5
    while owned.poll() is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert owned.poll() == returncode
    if cleanup == "wait":
        assert owned.wait(timeout=5) == returncode
    expected = ProcessExit(
        returncode,
        -returncode if returncode < 0 else None,
        timed_out,
        term_sent,
        kill_sent,
    )
    assert (
        owned.collect_exit(
            timed_out=timed_out, term_sent=term_sent, kill_sent=kill_sent
        )
        == expected
    )
    with pytest.raises(ChildProcessError):
        os.waitpid(anchor.pid, os.WNOHANG)
    assert anchor.poll() is not None
    assert owned.signal_group(signal.SIGTERM) is False
    assert owned.signal_group(signal.SIGKILL) is False
    assert owned.wait(timeout=5) == returncode
    result = owned.collect_exit(
        timed_out=timed_out, term_sent=term_sent, kill_sent=kill_sent
    )
    assert result == expected
    for field in ("returncode", "signal", "timed_out", "term_sent", "kill_sent"):
        with pytest.raises(FrozenInstanceError):
            setattr(result, field, None)


@pytest.mark.parametrize("number", [signal.SIGINT, signal.SIGTERM, signal.SIGHUP])
def test_supervisor_scope_raises_received_signal_and_restores_prior_handlers(
    number: int,
) -> None:
    numbers = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    original = {item: signal.getsignal(item) for item in numbers}
    received: list[int] = []

    def prior(received_number: int, frame: object) -> None:
        received.append(received_number)

    try:
        for item in numbers:
            signal.signal(item, prior)
        with pytest.raises(SupervisorSignal) as raised, supervisor_signal_scope():
            os.kill(os.getpid(), number)
        assert raised.value.signal_number == number
        assert received == []
        assert all(signal.getsignal(item) is prior for item in numbers)
        os.kill(os.getpid(), number)
        assert received == [number]
    finally:
        for item, handler in original.items():
            signal.signal(item, handler)


@pytest.mark.parametrize("exceptional", [False, True])
def test_supervisor_scope_restores_distinct_handlers_on_normal_and_exception_exit(
    exceptional: bool,
) -> None:
    numbers = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    original = {item: signal.getsignal(item) for item in numbers}
    prior = {
        signal.SIGINT: signal.default_int_handler,
        signal.SIGTERM: signal.SIG_IGN,
        signal.SIGHUP: signal.SIG_DFL,
    }

    def enter_scope() -> None:
        with supervisor_signal_scope():
            assert all(callable(signal.getsignal(item)) for item in numbers)
            if exceptional:
                raise LookupError("body failed")

    try:
        for item, handler in prior.items():
            signal.signal(item, handler)
        if exceptional:
            with pytest.raises(LookupError, match="body failed"):
                enter_scope()
        else:
            enter_scope()
        assert {item: signal.getsignal(item) for item in numbers} == prior
    finally:
        for item, handler in original.items():
            signal.signal(item, handler)


def test_supervisor_scope_rejects_worker_thread_without_changing_any_handler() -> None:
    numbers = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    original = {item: signal.getsignal(item) for item in numbers}
    outcomes: list[object] = []

    def worker() -> None:
        try:
            with supervisor_signal_scope():
                outcomes.append("entered")
        except RuntimeError as error:
            outcomes.append(error)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert len(outcomes) == 1 and isinstance(outcomes[0], RuntimeError)
    assert {item: signal.getsignal(item) for item in numbers} == original


def test_supervisor_scope_restores_handlers_after_partial_installation_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    numbers = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    original = {item: signal.getsignal(item) for item in numbers}
    real_signal = signal.signal
    installations = 0

    def deny_second_installation(number: int, handler: object) -> object:
        nonlocal installations
        installations += 1
        if installations == 2:
            raise OSError("handler installation denied")
        return real_signal(number, handler)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(signal, "signal", deny_second_installation)
            with (
                pytest.raises(OSError, match="handler installation denied"),
                supervisor_signal_scope(),
            ):
                pytest.fail("scope entered after failed installation")
        assert {item: signal.getsignal(item) for item in numbers} == original
    finally:
        for item, handler in original.items():
            real_signal(item, handler)


@pytest.mark.parametrize(
    "number,expected",
    [(signal.SIGINT, 130), (signal.SIGTERM, 143), (signal.SIGHUP, 129)],
)
def test_supervisor_exit_code_preserves_received_signal_status(
    number: int, expected: int
) -> None:
    from ovcaq.runtime.process import supervisor_exit_code

    with pytest.raises(SupervisorSignal) as raised, supervisor_signal_scope():
        os.kill(os.getpid(), number)
    assert supervisor_exit_code(raised.value) == expected


def test_supervisor_exit_code_keeps_keyboard_interrupt_at_130() -> None:
    from ovcaq.runtime.process import supervisor_exit_code

    assert supervisor_exit_code(KeyboardInterrupt()) == 130


@pytest.mark.parametrize("error", [RuntimeError("failed"), SystemExit(7)])
def test_supervisor_exit_code_rejects_unrelated_exceptions(
    error: BaseException,
) -> None:
    from ovcaq.runtime.process import supervisor_exit_code

    with pytest.raises(TypeError):
        supervisor_exit_code(error)
