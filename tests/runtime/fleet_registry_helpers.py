from __future__ import annotations

import fcntl
import json
import os
import stat
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

import pytest

from ovcaq.runtime.registry import FleetEntry, process_identity


def _entry(tmp_path: Path, run_id: str = "run-1") -> FleetEntry:
    identity = process_identity(os.getpid())
    assert identity is not None
    return FleetEntry(
        schema_version=1,
        root=tmp_path,
        pid=identity.pid,
        process_start=identity.started,
        run_id=run_id,
        agent="generic",
        started_at="2026-09-14T10:00:00Z",
    )


def _document(entry: FleetEntry) -> dict[str, object]:
    document = asdict(entry)
    document["root"] = str(entry.root)
    return document


def _dead_pid() -> int:
    result = subprocess.run(
        [sys.executable, "-c", "import os; print(os.getpid())"],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    return int(result.stdout.strip())


def _reject(expected: type[BaseException], operation: Callable[[], object]) -> None:
    with pytest.raises(expected):
        operation()


def _assert_mutation_lock_held(root: Path) -> None:
    with (root / "fleet.lock").open("rb") as stream, pytest.raises(BlockingIOError):
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _resolve_path(root: Path, path: str | Path, descriptor: object) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    if descriptor is None:
        return candidate.absolute()
    assert isinstance(descriptor, int)
    assert os.path.samestat(os.fstat(descriptor), root.stat())
    return root / candidate


def _write_entry_file(path: Path, entry: FleetEntry) -> tuple[bytes, os.stat_result]:
    encoded = json.dumps(_document(entry)).encode()
    return encoded, _write_file(path, encoded)


def _write_file(path: Path, encoded: bytes) -> os.stat_result:
    path.write_bytes(encoded)
    path.chmod(0o644)
    return path.stat()


def _assert_file_preserved(
    path: Path, encoded: bytes, original: os.stat_result
) -> None:
    assert path.read_bytes() == encoded
    assert os.path.samestat(path.stat(), original)
    assert stat.S_IMODE(path.stat().st_mode) == 0o644
