from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ovcaq.workflow.records import DeferBoundary, load_deferred_records, record_defer


def _rival(root: Path, writer: str) -> str | None:
    if writer == "nested":
        try:
            record_defer(root, "00004.md", "batch", {"op_id": "second"})
        except OSError as error:
            return str(error)
        return None
    script = """
import json, sys
from pathlib import Path
from ovcaq.workflow.records import record_defer
try:
    record_defer(Path(sys.argv[1]), "00004.md", "batch", {"op_id": "second"})
except OSError as error:
    print(json.dumps(str(error)))
else:
    print("null")
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(root)],
        capture_output=True,
        text=True,
        check=False,
        timeout=3,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    return json.loads(result.stdout)


@pytest.mark.parametrize("writer", ("nested", "process"))
def test_sidecar_replacement_inside_native_publish_cannot_lose_successful_append(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, writer: str
) -> None:
    path = record_defer(tmp_path, "00004.md", "batch", {"op_id": "seed"})
    native_replace = os.replace
    rival_errors: list[str | None] = []
    successful = {"seed"}
    replaced = False

    def replace(source: str, destination: str, **kwargs: int) -> None:
        nonlocal replaced
        if destination == path.name and not replaced:
            replaced = True
            lock = path.with_suffix(".json.lock")
            lock.rename(lock.with_suffix(".retained"))
            rival_errors.append(_rival(tmp_path, writer))
            if rival_errors[0] is None:
                successful.add("second")
        native_replace(source, destination, **kwargs)

    with monkeypatch.context() as patches:
        patches.setattr(os, "replace", replace)
        with pytest.raises(OSError, match="deferred lock identity changed"):
            record_defer(tmp_path, "00004.md", "batch", {"op_id": "first"})

    rows = load_deferred_records(tmp_path, "batch")
    assert successful <= {row["op_id"] for row in rows}
    assert len(rival_errors) == 1
    assert rival_errors[0] == f"publication busy; retry: {path}"
    assert [row["op_id"] for row in rows] == ["seed", "first"]
    for op_id in ("second", "first"):
        record_defer(tmp_path, "00004.md", "batch", {"op_id": op_id})
    before = path.read_bytes()
    for op_id in ("seed", "first", "second"):
        record_defer(tmp_path, "00004.md", "batch", {"op_id": op_id})
    assert path.read_bytes() == before
    assert [row["op_id"] for row in load_deferred_records(tmp_path, "batch")] == [
        "seed",
        "first",
        "second",
    ]
    assert path.with_suffix(".json.retained").is_file()
    assert list(path.parent.glob("*.tmp")) == []


def test_restored_sidecar_cannot_authorize_overwriting_a_newer_ledger(
    tmp_path: Path,
) -> None:
    path = record_defer(tmp_path, "00004.md", "batch", {"op_id": "seed"})

    def compete(boundary: DeferBoundary) -> None:
        if boundary is DeferBoundary.BEFORE_PUBLISH:
            lock = path.with_suffix(".json.lock")
            retained = lock.with_suffix(".retained")
            lock.rename(retained)
            record_defer(tmp_path, "00004.md", "batch", {"op_id": "second"})
            lock.unlink()
            retained.rename(lock)

    with pytest.raises(OSError, match="deferred record changed during publication"):
        record_defer(
            tmp_path, "00004.md", "batch", {"op_id": "first"}, boundary_hook=compete
        )
    before = path.read_bytes()
    assert [row["op_id"] for row in load_deferred_records(tmp_path, "batch")] == [
        "seed",
        "second",
    ]
    record_defer(tmp_path, "00004.md", "batch", {"op_id": "second"})
    assert path.read_bytes() == before
    record_defer(tmp_path, "00004.md", "batch", {"op_id": "first"})
    assert [row["op_id"] for row in load_deferred_records(tmp_path, "batch")] == [
        "seed",
        "second",
        "first",
    ]
