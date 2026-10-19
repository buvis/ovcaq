from __future__ import annotations

import copy
import errno
import json
import multiprocessing
import os
import re
import socket
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from multiprocessing.connection import Connection
from pathlib import Path

_ORIGINAL_POPEN = subprocess.Popen
_ORIGINAL_POPEN_ATTRIBUTES = dict(subprocess.Popen.__dict__)

import pytest
from test_durability import (
    _stop_worker,
    _wait_for_worker_line,
    _worker_environment,
)
from test_schema import _valid_state

import ovcaq.state as state_package
import ovcaq.state.store as store_module
from ovcaq.state.schema import (
    MAX_JSON_DEPTH,
    MAX_JSON_INTEGER_DIGITS,
    MAX_STATE_BYTES,
    MAX_STRING_BYTES,
    SCHEMA_VERSION,
    ResourceLimitError,
    SchemaError,
    State,
    new_state,
)
from ovcaq.state.store import (
    BackupError,
    DurabilityBoundary,
    DurabilityUnsupportedError,
    FutureSchemaError,
    RevisionConflictError,
    StateError,
    StateExistsError,
    StateIOError,
    StateResourceLimitError,
    StateStore,
)


class MutatorFailure(RuntimeError):
    pass


def _canonical_bytes(state: State) -> bytes:
    return (
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _state_at_canonical_byte_limit(
    repo_root: Path, *, revision: int, extra_bytes: int = 0
) -> State:
    state = new_state(repo_root=repo_root)
    state["revision"] = revision
    state["work"]["extensions"] = {
        f"tests/filler-{index}": "x" * MAX_STRING_BYTES for index in range(15)
    }
    state["work"]["extensions"]["tests/boundary"] = ""
    remaining = MAX_STATE_BYTES - len(_canonical_bytes(state))
    assert 0 <= remaining <= MAX_STRING_BYTES
    assert remaining + extra_bytes <= MAX_STRING_BYTES
    state["work"]["extensions"]["tests/boundary"] = "x" * (remaining + extra_bytes)
    assert len(_canonical_bytes(state)) == MAX_STATE_BYTES + extra_bytes
    return state


def _invalid_state_bytes(kind: str, repo_root: Path) -> bytes | None:
    if kind == "missing":
        return None
    if kind == "malformed-json":
        return b'{"schema_version":'
    if kind == "non-object":
        return b"[]\n"

    invalid = new_state(repo_root=repo_root)
    if kind == "future-schema":
        invalid["schema_version"] = SCHEMA_VERSION + 1
    elif kind == "schema-invalid":
        invalid["revision"] = True
    else:
        raise AssertionError(f"unknown invalid-state kind: {kind}")
    return _canonical_bytes(invalid)


def _state_bytes_with_deep_json(repo_root: Path, *, depth: int = 2_000) -> bytes:
    marker = "deep-json-placeholder"
    state = new_state(repo_root=repo_root)
    state["work"]["extensions"] = {"tests/deep": marker}
    encoded = _canonical_bytes(state)
    deep_json = ("[" * depth + "null" + "]" * depth).encode()
    replaced = encoded.replace(json.dumps(marker).encode(), deep_json)
    assert replaced != encoded
    assert len(replaced) < MAX_STATE_BYTES
    return replaced


def _state_bytes_with_oversized_integer(repo_root: Path) -> bytes:
    encoded = _canonical_bytes(new_state(repo_root=repo_root))
    replaced = encoded.replace(
        b'"revision": 0,',
        b'"revision": ' + b"9" * 5_000 + b",",
        1,
    )
    assert replaced != encoded
    assert len(replaced) < MAX_STATE_BYTES
    return replaced


def _state_bytes_with_duplicate_key(repo_root: Path, kind: str) -> bytes:
    state = new_state(repo_root=repo_root)
    if kind == "open":
        state["work"]["extensions"] = {"tests/duplicate": "last"}
    encoded = _canonical_bytes(state)
    if kind == "root":
        replaced = encoded.replace(
            b'"revision": 0,',
            b'"revision": 999,\n  "revision": 0,',
            1,
        )
    elif kind == "owned":
        replaced = encoded.replace(
            b'"phase": "build",',
            b'"phase": "review",\n    "phase": "build",',
            1,
        )
    elif kind == "open":
        replaced = encoded.replace(
            b'"tests/duplicate": "last"',
            b'"tests/duplicate": "first",\n      "tests/duplicate": "last"',
            1,
        )
    else:
        raise AssertionError(f"unknown duplicate-key kind: {kind}")
    assert replaced != encoded
    return replaced


def _directory_bytes(directory: Path) -> dict[str, bytes]:
    return {
        entry.name: entry.read_bytes()
        for entry in directory.iterdir()
        if entry.is_file()
    }


def _file_with_bytes(state_path: Path, expected: bytes) -> Path:
    matches = [
        entry
        for entry in state_path.parent.iterdir()
        if entry != state_path and entry.is_file() and entry.read_bytes() == expected
    ]
    assert len(matches) == 1
    return matches[0]


def _sidecar_after_initialize(state_path: Path) -> Path:
    sidecars = [
        entry
        for entry in state_path.parent.iterdir()
        if entry != state_path and entry.is_file()
    ]
    assert len(sidecars) == 1
    return sidecars[0]


def _assert_original_popen_is_unchanged() -> None:
    assert subprocess.Popen is _ORIGINAL_POPEN
    assert dict(_ORIGINAL_POPEN.__dict__) == _ORIGINAL_POPEN_ATTRIBUTES


_CHILD_OPERATION = """
import sys
from pathlib import Path

from ovcaq.state import StateStore

store = StateStore(Path(sys.argv[1]))
operation = sys.argv[2]
marker = Path(sys.argv[3])

def mutate(state):
    marker.write_text("called\\n", encoding="utf-8")
    state["work"]["prd"] = "child-transaction.md"

print("ready", flush=True)
if operation == "read":
    store.read()
elif operation == "transaction":
    store.transaction(mutate)
else:
    raise AssertionError(operation)
print("done", flush=True)
"""


_REVISION_RACE_OPERATION = """
import json
import sys
import time
from pathlib import Path

from ovcaq.state.store import RevisionConflictError, StateStore

store = StateStore(Path(sys.argv[1]))
gate = Path(sys.argv[2])
marker = Path(sys.argv[3])
label = sys.argv[4]

def mutate(state):
    marker.write_text("called\\n", encoding="utf-8")
    state["work"]["prd"] = f"{label}.md"

print("ready", flush=True)
while not gate.exists():
    time.sleep(0.001)

try:
    committed = store.transaction(mutate, expected_revision=0)
except RevisionConflictError:
    outcome = {"result": "conflict"}
else:
    outcome = {"result": "success", "state": committed}
print(json.dumps(outcome, sort_keys=True), flush=True)
"""


_BOUNDARY_REPAIR_WRITER_OPERATION = """
import sys
from pathlib import Path

from ovcaq.state.store import DurabilityBoundary, StateStore

state_path = Path(sys.argv[1])
target = DurabilityBoundary[sys.argv[2]]

class BoundaryFailure(RuntimeError):
    pass

def fail_at_boundary(boundary):
    if boundary is target:
        print(boundary.name, flush=True)
        if sys.stdin.readline() != "fail\\n":
            raise AssertionError("unexpected repair command")
        raise BoundaryFailure(boundary.name)

def increment(state):
    extensions = state["work"]["extensions"]
    extensions["tests/counter"] += 1

try:
    StateStore(state_path, boundary_hook=fail_at_boundary).transaction(increment)
except BoundaryFailure:
    print("repaired", flush=True)
else:
    raise AssertionError("writer passed the requested durability boundary")
"""


def _increment_counter_process(state_path: str, connection: Connection) -> None:
    try:
        connection.send("ready")
        if connection.recv() != "start":
            raise AssertionError("unexpected counter command")

        def increment(state: State) -> None:
            state["work"]["extensions"]["tests/counter"] += 1

        committed = StateStore(Path(state_path)).transaction(increment)
        connection.send(("done", committed))
    finally:
        connection.close()


def _stop_spawned_process(process: multiprocessing.Process) -> None:
    if process.is_alive():
        process.terminate()
    process.join(timeout=5)
    if process.is_alive():
        process.kill()
        process.join(timeout=5)
    assert not process.is_alive()


@contextmanager
def _child_operation(
    state_path: Path, operation: str, *, cwd: Path, marker: Path
) -> Iterator[subprocess.Popen[str]]:
    process = _ORIGINAL_POPEN(
        [
            sys.executable,
            "-c",
            _CHILD_OPERATION,
            str(state_path),
            operation,
            str(marker),
        ],
        cwd=cwd,
        env=_worker_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        _wait_for_worker_line(process, "ready\n")
        yield process
    finally:
        _stop_worker(process)


def _assert_child_finishes(process: subprocess.Popen[str]) -> None:
    stdout, stderr = process.communicate(timeout=5)
    assert process.returncode == 0, stderr
    assert stdout == "done\n"


def _assert_child_blocks(process: subprocess.Popen[str]) -> None:
    try:
        stdout, stderr = process.communicate(timeout=0.5)
    except subprocess.TimeoutExpired:
        return
    raise AssertionError(
        f"child unexpectedly finished; stdout={stdout!r}, stderr={stderr!r}"
    )


_NEUTRAL_STORE_SCENARIO = """
import json
import sys
from pathlib import Path

from ovcaq.state import StateStore
from ovcaq.state.schema import new_state

state_path = Path(sys.argv[1])
repo_root = Path(sys.argv[2])
state_path.parent.mkdir(parents=True)
initial = new_state(repo_root=repo_root)
store = StateStore(state_path)
initialized = store.initialize(initial)
read = store.read()

def mutate(state):
    state["work"]["prd"] = "neutral-transaction.md"

committed = store.transaction(mutate, expected_revision=0)
restored = store.restore(expected_revision=1)
sys.stdout.write(
    json.dumps(
        {
            "initialized": initialized,
            "read": read,
            "committed": committed,
            "restored": restored,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
"""


_NEUTRAL_REVISION_CONFLICT_SCENARIO = """
import json
import os
import sys
from pathlib import Path

from ovcaq.state.schema import new_state
from ovcaq.state.store import RevisionConflictError, StateStore

state_path = Path(sys.argv[1])
repo_root = Path(sys.argv[2])
marker = Path(sys.argv[3])
state_path.parent.mkdir(parents=True)

assert "pytest" not in sys.modules
assert "pytest" not in str(Path.cwd()).casefold()
assert all("pytest" not in entry.casefold() for entry in sys.path)
assert all(
    "pytest" not in key.casefold() and "pytest" not in value.casefold()
    for key, value in os.environ.items()
)
frame = sys._getframe()
while frame is not None:
    assert "pytest" not in frame.f_code.co_filename.casefold()
    frame = frame.f_back

store = StateStore(state_path)
initial = new_state(repo_root=repo_root)
store.initialize(initial)
checks = []

def directory_bytes():
    return {
        entry.name: entry.read_bytes()
        for entry in state_path.parent.iterdir()
        if entry.is_file()
    }

def mutate(state):
    marker.write_text("called\\n", encoding="utf-8")
    state["work"]["prd"] = "must-not-persist.md"

def expect_transaction_conflict(expected_revision):
    before = directory_bytes()
    try:
        store.transaction(mutate, expected_revision=expected_revision)
    except RevisionConflictError:
        pass
    else:
        raise AssertionError("transaction did not reject expected revision")
    assert not marker.exists()
    assert directory_bytes() == before
    checks.append(["transaction", expected_revision])

def expect_restore_conflict(expected_revision):
    before = directory_bytes()
    try:
        store.restore(expected_revision=expected_revision)
    except RevisionConflictError:
        pass
    else:
        raise AssertionError("restore did not reject expected revision")
    assert directory_bytes() == before
    checks.append(["restore", expected_revision])

expect_transaction_conflict(False)
expect_restore_conflict(False)

def establish_backup(state):
    state["work"]["prd"] = "neutral-current.md"

committed = store.transaction(establish_backup, expected_revision=0)
for invalid_revision in (True, -1):
    expect_transaction_conflict(invalid_revision)
    expect_restore_conflict(invalid_revision)

sys.stdout.write(
    json.dumps(
        {
            "checks": checks,
            "committed": committed,
            "initial": initial,
            "neutral": True,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
"""


def _neutral_environment() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if "pytest" not in key.casefold() and "pytest" not in value.casefold()
    }


def test_importing_and_using_the_state_package_preserves_subprocess_popen(
    tmp_path: Path,
) -> None:
    _assert_original_popen_is_unchanged()
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    _assert_original_popen_is_unchanged()
    store.read()
    _assert_original_popen_is_unchanged()
    store.transaction(lambda _state: None)
    _assert_original_popen_is_unchanged()
    store.restore(expected_revision=1)
    _assert_original_popen_is_unchanged()


def test_store_operations_work_from_a_neutral_python_process() -> None:
    _assert_original_popen_is_unchanged()
    environment = _neutral_environment()
    assert all(
        "pytest" not in key.casefold() and "pytest" not in value.casefold()
        for key, value in environment.items()
    )

    with tempfile.TemporaryDirectory(prefix="ovcaq-neutral-store-") as temp_dir:
        neutral_root = Path(temp_dir)
        state_path = neutral_root / "runtime" / "state.json"
        process = _ORIGINAL_POPEN(
            [
                sys.executable,
                "-c",
                _NEUTRAL_STORE_SCENARIO,
                str(state_path),
                str(neutral_root),
            ],
            cwd=neutral_root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(timeout=10)

        assert process.returncode == 0, stderr
        outcomes = json.loads(stdout)
        initial = new_state(repo_root=neutral_root)
        assert outcomes["initialized"] == initial
        assert outcomes["read"] == initial
        assert outcomes["committed"]["revision"] == 1
        assert outcomes["committed"]["work"]["prd"] == "neutral-transaction.md"
        assert outcomes["restored"]["work"] == initial["work"]
        assert (
            json.loads(state_path.read_text(encoding="utf-8")) == outcomes["restored"]
        )
        assert state_path.read_bytes() == _canonical_bytes(outcomes["restored"])

    _assert_original_popen_is_unchanged()


def test_invalid_revisions_conflict_in_a_neutral_python_process() -> None:
    _assert_original_popen_is_unchanged()
    environment = _neutral_environment()

    with tempfile.TemporaryDirectory(prefix="ovcaq-neutral-revision-") as temp_dir:
        neutral_root = Path(temp_dir)
        state_path = neutral_root / "runtime" / "state.json"
        marker = neutral_root / "mutator-called"
        process = _ORIGINAL_POPEN(
            [
                sys.executable,
                "-c",
                _NEUTRAL_REVISION_CONFLICT_SCENARIO,
                str(state_path),
                str(neutral_root),
                str(marker),
            ],
            cwd=neutral_root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(timeout=10)

        assert process.returncode == 0, stderr
        outcomes = json.loads(stdout)
        assert outcomes["neutral"] is True
        assert outcomes["checks"] == [
            ["transaction", False],
            ["restore", False],
            ["transaction", True],
            ["restore", True],
            ["transaction", -1],
            ["restore", -1],
        ]
        assert not marker.exists()

        initial = new_state(repo_root=neutral_root)
        committed = copy.deepcopy(initial)
        committed["revision"] = 1
        committed["work"]["prd"] = "neutral-current.md"
        assert outcomes["initial"] == initial
        assert outcomes["committed"] == committed
        assert state_path.read_bytes() == _canonical_bytes(committed)
        assert _file_with_bytes(state_path, _canonical_bytes(initial)).read_bytes() == (
            _canonical_bytes(initial)
        )

    _assert_original_popen_is_unchanged()


def test_state_package_exports_the_store_contract_without_an_atomic_writer() -> None:
    expected_exports = {
        "State": State,
        "StateStore": StateStore,
        "SchemaError": SchemaError,
        "StateError": StateError,
        "StateIOError": StateIOError,
        "StateExistsError": StateExistsError,
        "BackupError": BackupError,
        "FutureSchemaError": FutureSchemaError,
        "RevisionConflictError": RevisionConflictError,
        "DurabilityUnsupportedError": DurabilityUnsupportedError,
    }

    for name, value in expected_exports.items():
        assert getattr(state_package, name) is value
    assert not any(
        not name.startswith("_") and "atomic" in name.casefold()
        for name in dir(state_package)
    )


def test_state_exceptions_share_the_documented_hierarchy() -> None:
    for error_type in (
        StateIOError,
        StateExistsError,
        BackupError,
        FutureSchemaError,
        RevisionConflictError,
    ):
        assert issubclass(error_type, StateError)
    assert issubclass(DurabilityUnsupportedError, StateIOError)


def test_read_rejects_deep_json_before_recursive_decoding(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    raw = _state_bytes_with_deep_json(tmp_path)
    state_path.write_bytes(raw)

    with pytest.raises(StateResourceLimitError, match="JSON nesting exceeds"):
        StateStore(state_path).read()

    assert state_path.read_bytes() == raw


def test_read_accepts_open_json_at_the_documented_depth_limit(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state = new_state(repo_root=tmp_path)
    nested: object = None
    for _ in range(MAX_JSON_DEPTH):
        nested = [nested]
    state["work"]["extensions"] = {"tests/depth-limit": nested}  # type: ignore[dict-item]
    store = StateStore(state_path)

    store.initialize(state)

    assert store.read() == state


def test_read_rejects_oversized_json_integer_as_a_resource_limit(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    raw = _state_bytes_with_oversized_integer(tmp_path)
    state_path.write_bytes(raw)

    with pytest.raises(StateResourceLimitError, match="integer literal"):
        StateStore(state_path).read()

    assert state_path.read_bytes() == raw


def test_initialize_rejects_programmatic_oversized_integer_without_publication(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    state = new_state(repo_root=tmp_path)
    state["work"]["extensions"] = {"tests/integer": 10**MAX_JSON_INTEGER_DIGITS}

    with pytest.raises(ResourceLimitError, match="integer value exceeds"):
        StateStore(state_path).initialize(state)

    assert not state_path.exists()
    assert not state_path.with_name("state.json.bak").exists()
    assert not state_path.with_name("state.json.lock").exists()


@pytest.mark.parametrize(
    ("mutation", "expected_path"),
    (
        pytest.param(
            lambda state: state["tasks"][0].__setitem__(
                "id", 10**MAX_JSON_INTEGER_DIGITS
            ),
            "tasks[0].id",
            id="task-id",
        ),
        pytest.param(
            lambda state: state["tasks"][1].__setitem__(
                "blocked_by", [10**MAX_JSON_INTEGER_DIGITS]
            ),
            "tasks[1].blocked_by[0]",
            id="blocker-id",
        ),
        pytest.param(
            lambda state: state["work"]["extensions"].__setitem__(
                "tests/integer", 10**MAX_JSON_INTEGER_DIGITS
            ),
            "work.extensions.tests/integer",
            id="open-json",
        ),
    ),
)
def test_transaction_rejects_programmatic_oversized_integers_without_mutation(
    tmp_path: Path,
    mutation: Callable[[State], None],
    expected_path: str,
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(_valid_state(tmp_path))
    before = _directory_bytes(tmp_path)

    with pytest.raises(
        ResourceLimitError,
        match=f"{re.escape(expected_path)}: integer",
    ):
        store.transaction(mutation)

    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize("operation", ("transaction", "restore"))
def test_maximum_revision_cannot_roll_over_to_unreadable_state(
    tmp_path: Path,
    operation: str,
) -> None:
    state_path = tmp_path / "state.json"
    maximum = 10**MAX_JSON_INTEGER_DIGITS - 1
    state = new_state(repo_root=tmp_path)
    state["revision"] = maximum
    raw = _canonical_bytes(state)
    state_path.write_bytes(raw)
    store = StateStore(state_path)

    assert store.read() == state
    if operation == "restore":
        state_path.with_name("state.json.bak").write_bytes(
            _canonical_bytes(new_state(repo_root=tmp_path))
        )
    before = _directory_bytes(tmp_path)

    with pytest.raises(ResourceLimitError, match="revision: integer value exceeds"):
        if operation == "transaction":
            store.transaction(lambda _state: None)
        else:
            store.restore()

    assert _directory_bytes(tmp_path) == before


@pytest.mark.parametrize("duplicate_kind", ("root", "owned", "open"))
def test_read_rejects_duplicate_json_keys_before_schema_validation(
    tmp_path: Path,
    duplicate_kind: str,
) -> None:
    state_path = tmp_path / "state.json"
    raw = _state_bytes_with_duplicate_key(tmp_path, duplicate_kind)
    state_path.write_bytes(raw)

    with pytest.raises(StateIOError, match="duplicate JSON object key"):
        StateStore(state_path).read()

    assert state_path.read_bytes() == raw


@pytest.mark.parametrize(
    ("artifact", "error_type"),
    (
        pytest.param("state", StateIOError, id="state"),
        pytest.param("backup", BackupError, id="backup"),
        pytest.param("lock", StateIOError, id="lock"),
    ),
)
def test_store_rejects_symlinked_artifacts_without_touching_targets(
    tmp_path: Path,
    artifact: str,
    error_type: type[Exception],
) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    state_path = runtime / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    store.transaction(lambda _state: None)
    artifact_path = state_path.with_name(
        {
            "state": "state.json",
            "backup": "state.json.bak",
            "lock": "state.json.lock",
        }[artifact]
    )
    victim = tmp_path / f"{artifact}-victim"
    victim.write_bytes(
        artifact_path.read_bytes() if artifact != "lock" else b"lock victim bytes\n"
    )
    victim.chmod(0o644)
    os.utime(victim, ns=(1_700_000_000_000_000_000, 1_700_000_100_000_000_000))
    artifact_path.unlink()
    artifact_path.symlink_to(victim)
    victim_bytes = victim.read_bytes()
    victim_before = victim.stat()

    operation = store.restore if artifact == "backup" else store.read
    with pytest.raises(error_type, match="symlink"):
        operation()

    victim_after = victim.stat()
    assert victim.read_bytes() == victim_bytes
    assert victim_after.st_mode == victim_before.st_mode
    assert victim_after.st_mtime_ns == victim_before.st_mtime_ns
    assert artifact_path.is_symlink()


@contextmanager
def _non_regular_artifact(path: Path, kind: str) -> Iterator[None]:
    channel: socket.socket | None = None
    socket_directory: tempfile.TemporaryDirectory[str] | None = None
    if kind == "fifo":
        os.mkfifo(path)
    elif kind == "socket":
        socket_directory = tempfile.TemporaryDirectory(prefix="ovcaq-socket-")
        short_path = Path(socket_directory.name) / "s"
        channel = socket.socket(socket.AF_UNIX)
        channel.bind(str(short_path))
        os.replace(short_path, path)
    elif kind == "directory":
        path.mkdir()
    else:
        raise AssertionError(f"unknown non-regular artifact kind: {kind}")
    try:
        yield
    finally:
        if channel is not None:
            channel.close()
        if socket_directory is not None:
            socket_directory.cleanup()


@pytest.mark.parametrize("kind", ("fifo", "socket", "directory"))
@pytest.mark.parametrize(
    ("artifact", "operation", "error_type"),
    (
        pytest.param(
            "state",
            lambda store: store.read(),
            StateIOError,
            id="state",
        ),
        pytest.param(
            "backup",
            lambda store: store.restore(),
            BackupError,
            id="backup",
        ),
    ),
)
def test_store_rejects_non_regular_artifacts_before_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    artifact: str,
    operation: Callable[[StateStore], object],
    error_type: type[Exception],
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    store.transaction(lambda _state: None)
    artifact_path = (
        state_path if artifact == "state" else state_path.with_name("state.json.bak")
    )
    artifact_path.unlink()
    real_open = store_module.os.open
    target_open_attempts = 0

    def track_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
    ) -> int:
        nonlocal target_open_attempts
        if Path(os.fsdecode(path)) == artifact_path:
            target_open_attempts += 1
            raise AssertionError(f"attempted blocking open of {artifact_path}")
        return real_open(path, flags, mode)

    with (
        _non_regular_artifact(artifact_path, kind),
        monkeypatch.context() as artifact_patch,
        pytest.raises(error_type, match="not a regular file"),
    ):
        artifact_patch.setattr(store_module.os, "open", track_open)
        operation(store)

    assert target_open_attempts == 0


def test_regular_state_reads_use_a_nonblocking_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "state.json"
    store = StateStore(state_path)
    state = store.initialize(new_state(repo_root=tmp_path))
    real_open = store_module.os.open
    state_open_flags: list[int] = []

    def track_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
    ) -> int:
        if Path(os.fsdecode(path)) == state_path:
            state_open_flags.append(flags)
        return real_open(path, flags, mode)

    monkeypatch.setattr(store_module.os, "open", track_open)

    assert store.read() == state
    assert len(state_open_flags) == 1
    assert state_open_flags[0] & os.O_NONBLOCK


@pytest.mark.parametrize(
    ("artifact", "operation", "error_type"),
    (
        pytest.param(
            "state",
            lambda store: store.read(),
            StateIOError,
            id="state-read",
        ),
        pytest.param(
            "backup",
            lambda store: store.transaction(lambda _state: None),
            StateIOError,
            id="backup-rotation",
        ),
        pytest.param(
            "backup",
            lambda store: store.restore(),
            BackupError,
            id="backup-restore",
        ),
        pytest.param(
            "lock",
            lambda store: store.read(),
            StateIOError,
            id="lock-permission",
        ),
    ),
)
def test_store_rejects_hard_linked_artifacts_without_touching_aliases(
    tmp_path: Path,
    artifact: str,
    operation: Callable[[StateStore], object],
    error_type: type[Exception],
) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    state_path = runtime / "state.json"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    store.transaction(lambda _state: None)
    artifact_path = state_path.with_name(
        {
            "state": "state.json",
            "backup": "state.json.bak",
            "lock": "state.json.lock",
        }[artifact]
    )
    expected_bytes = artifact_path.read_bytes()
    artifact_path.chmod(0o640)
    os.utime(
        artifact_path,
        ns=(1_700_000_000_000_000_000, 1_700_000_100_000_000_000),
    )
    aliases = tmp_path / "external-aliases"
    aliases.mkdir()
    alias = aliases / artifact
    os.link(artifact_path, alias)
    before = alias.stat()

    with pytest.raises(error_type, match="hard link"):
        operation(store)

    after = alias.stat()
    artifact_after = artifact_path.stat()
    assert alias.read_bytes() == expected_bytes
    assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
    assert (artifact_after.st_dev, artifact_after.st_ino) == (
        before.st_dev,
        before.st_ino,
    )
    assert after.st_nlink == before.st_nlink == 2
    assert after.st_mode == before.st_mode
    assert after.st_atime_ns == before.st_atime_ns
    assert after.st_mtime_ns == before.st_mtime_ns


@pytest.mark.parametrize(
    "invalid_backup",
    (
        pytest.param("deep", id="deep-json"),
        pytest.param("duplicate", id="duplicate-key"),
        pytest.param("integer", id="oversized-integer"),
    ),
)
def test_restore_rejects_deep_or_duplicate_backup_before_durable_changes(
    tmp_path: Path,
    invalid_backup: str,
) -> None:
    state_path = tmp_path / "state.json"
    backup_path = tmp_path / "state.json.bak"
    store = StateStore(state_path)
    store.initialize(new_state(repo_root=tmp_path))
    store.transaction(lambda _state: None)
    invalid_raw = (
        _state_bytes_with_deep_json(tmp_path)
        if invalid_backup == "deep"
        else (
            _state_bytes_with_duplicate_key(tmp_path, "root")
            if invalid_backup == "duplicate"
            else _state_bytes_with_oversized_integer(tmp_path)
        )
    )
    backup_path.write_bytes(invalid_raw)
    before = _directory_bytes(tmp_path)

    with pytest.raises(BackupError):
        store.restore()

    assert _directory_bytes(tmp_path) == before


def test_initialize_requires_an_existing_parent_without_creating_artifacts(
    tmp_path: Path,
) -> None:
    missing_root = tmp_path / "missing" / "runtime"
    state_path = missing_root / "state.json"

    with pytest.raises(StateIOError):
        StateStore(state_path).initialize(new_state(repo_root=tmp_path))

    assert not (tmp_path / "missing").exists()
    assert not state_path.exists()
    assert not state_path.with_name("state.json.lock").exists()
    assert not state_path.with_name("state.json.bak").exists()


def test_initialize_rejects_a_valid_nonzero_revision_without_artifacts(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    initial["revision"] = 1

    with pytest.raises(StateError, match="revision 0"):
        StateStore(state_path).initialize(initial)

    assert _directory_bytes(tmp_path) == {}


def test_initialize_existing_state_preserves_it_and_all_sibling_bytes(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    sibling_path = tmp_path / "operator-note"
    state_path.write_bytes(b"existing state bytes\n")
    sibling_path.write_bytes(b"sibling bytes\x00must survive")
    before = _directory_bytes(tmp_path)

    with pytest.raises(StateExistsError):
        StateStore(state_path).initialize(new_state(repo_root=tmp_path))

    assert _directory_bytes(tmp_path) == before


def test_initialize_create_only_race_preserves_the_competing_state(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "state.json"
    competing_bytes = b"concurrently published bytes\n"

    def publish_competing_state(boundary: DurabilityBoundary) -> None:
        if boundary is DurabilityBoundary.STATE_TEMP_FSYNCED:
            state_path.write_bytes(competing_bytes)

    store = StateStore(state_path, boundary_hook=publish_competing_state)

    with pytest.raises(StateExistsError):
        store.initialize(new_state(repo_root=tmp_path))

    assert state_path.read_bytes() == competing_bytes
    assert not state_path.with_name("state.json.bak").exists()
    assert not tuple(tmp_path.glob(".state.json.ovcaq-*.tmp"))


@pytest.mark.parametrize(
    "failure_boundary",
    (
        DurabilityBoundary.STATE_REPLACED,
        DurabilityBoundary.STATE_DIR_FSYNCED,
    ),
)
def test_initialize_hook_failure_after_publication_repairs_and_allows_retry(
    tmp_path: Path,
    failure_boundary: DurabilityBoundary,
) -> None:
    state_path = tmp_path / "state.json"
    sibling_path = tmp_path / "operator-note"
    sibling_path.write_bytes(b"keep me exact\n")
    failed = False

    def fail_once(boundary: DurabilityBoundary) -> None:
        nonlocal failed
        if boundary is failure_boundary and not failed:
            failed = True
            raise MutatorFailure(f"failed at {boundary.value}")

    store = StateStore(state_path, boundary_hook=fail_once)
    initial = new_state(repo_root=tmp_path)

    with pytest.raises(MutatorFailure, match=failure_boundary.value):
        store.initialize(initial)

    assert sibling_path.read_bytes() == b"keep me exact\n"
    assert not state_path.exists()
    assert not state_path.with_name("state.json.bak").exists()
    assert not tuple(tmp_path.glob(".state.json.ovcaq-*.tmp"))
    assert stat.S_IMODE(state_path.with_name("state.json.lock").stat().st_mode) == (
        0o600
    )

    assert store.initialize(initial) == initial
    assert state_path.read_bytes() == _canonical_bytes(initial)


@pytest.mark.parametrize(
    "failure_boundary",
    (
        DurabilityBoundary.STATE_TEMP_FSYNCED,
        DurabilityBoundary.STATE_REPLACED,
        DurabilityBoundary.STATE_DIR_FSYNCED,
    ),
)
def test_initialize_keyboard_interrupt_repairs_before_reraising(
    tmp_path: Path,
    failure_boundary: DurabilityBoundary,
) -> None:
    state_path = tmp_path / "state.json"

    def interrupt(boundary: DurabilityBoundary) -> None:
        if boundary is failure_boundary:
            raise KeyboardInterrupt

    store = StateStore(state_path, boundary_hook=interrupt)

    with pytest.raises(KeyboardInterrupt):
        store.initialize(new_state(repo_root=tmp_path))

    _assert_initialize_failure_repaired(tmp_path, state_path)


def _assert_initialize_failure_repaired(tmp_path: Path, state_path: Path) -> None:
    assert not state_path.exists()
    assert not state_path.with_name("state.json.bak").exists()
    assert not tuple(tmp_path.glob(".state.json.ovcaq-*.tmp"))


@pytest.mark.parametrize(
    ("failure_errno", "error_type"),
    (
        pytest.param(errno.EIO, StateIOError, id="io-error"),
        pytest.param(
            errno.EINVAL,
            DurabilityUnsupportedError,
            id="durability-unsupported",
        ),
    ),
)
def test_initialize_one_shot_directory_fsync_failure_repairs_and_allows_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_errno: int,
    error_type: type[StateIOError],
) -> None:
    state_path = tmp_path / "state.json"
    initial = new_state(repo_root=tmp_path)
    real_open = store_module.os.open
    real_fsync = store_module.os.fsync
    real_close = store_module.os.close
    directory_descriptors: set[int] = set()
    directory_fsync_attempts = 0

    def track_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
    ) -> int:
        descriptor = real_open(path, flags, mode)
        if Path(os.fsdecode(path)) == state_path.parent:
            directory_descriptors.add(descriptor)
        return descriptor

    def fail_first_directory_fsync(descriptor: int) -> None:
        nonlocal directory_fsync_attempts
        if descriptor in directory_descriptors:
            directory_fsync_attempts += 1
            if directory_fsync_attempts == 1:
                raise OSError(failure_errno, "injected directory fsync failure")
        real_fsync(descriptor)

    def track_close(descriptor: int) -> None:
        directory_descriptors.discard(descriptor)
        real_close(descriptor)

    monkeypatch.setattr(store_module.os, "open", track_open)
    monkeypatch.setattr(store_module.os, "fsync", fail_first_directory_fsync)
    monkeypatch.setattr(store_module.os, "close", track_close)
    store = StateStore(state_path)

    with pytest.raises(error_type, match="directory fsync"):
        store.initialize(initial)

    assert directory_fsync_attempts >= 2
    _assert_initialize_failure_repaired(tmp_path, state_path)

    assert store.initialize(initial) == initial
    assert state_path.read_bytes() == _canonical_bytes(initial)
