from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ovcaq.workflow.records import DeferBoundary, load_deferred_records, record_defer


@pytest.mark.parametrize(
    "payload",
    (
        '{"batch_id":"batch","items":[{"op_id":"keep-me"}],"items":[]}',
        '{"batch_id":"batch","items":[{"data":'
        + "[" * 10000
        + "0"
        + "]" * 10000
        + "}]}",
        '{"batch_id":"batch","items":[{"op_id":"keep-me","op_id":"lost"}]}',
    ),
    ids=("duplicate-root", "deep-nesting", "duplicate-item"),
)
@pytest.mark.parametrize("action", ("append", "load"))
def test_malformed_ledger_refuses_without_changing_bytes(
    tmp_path: Path, payload: str, action: str
) -> None:
    path = tmp_path / "deferred/batch-deferred.json"
    path.parent.mkdir()
    path.write_text(payload)
    before = path.read_bytes()

    with pytest.raises(ValueError, match="deferred"):
        if action == "append":
            record_defer(tmp_path, "00004.md", "batch", {"op_id": "new"})
        else:
            load_deferred_records(tmp_path, "batch")

    assert path.read_bytes() == before
    assert list(path.parent.glob("*.tmp")) == []


def _append_competitor(root: Path, writer: str) -> Path:
    if writer == "process":
        script = """
import sys
from pathlib import Path
from ovcaq.workflow.records import record_defer
record_defer(Path(sys.argv[1]), "00004.md", "batch", {"op_id": "second"})
"""
        result = subprocess.run(
            [sys.executable, "-c", script, str(root)],
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
        assert result.returncode == 0, result.stderr
        return root / "deferred/batch-deferred.json"
    return record_defer(root, "00004.md", "batch", {"op_id": "second"})


@pytest.mark.parametrize("writer", ("nested", "process"))
@pytest.mark.parametrize("boundary", tuple(DeferBoundary))
def test_replaced_lock_refuses_and_preserves_successful_competing_append(
    tmp_path: Path, boundary: DeferBoundary, writer: str
) -> None:
    second_paths: list[Path] = []

    def replace(reached: DeferBoundary) -> None:
        if reached is boundary:
            lock = tmp_path / "deferred/batch-deferred.json.lock"
            lock.rename(lock.with_suffix(".retained"))
            second_paths.append(_append_competitor(tmp_path, writer))

    with pytest.raises(OSError, match="deferred lock identity changed"):
        record_defer(
            tmp_path, "00004.md", "batch", {"op_id": "first"}, boundary_hook=replace
        )

    assert len(second_paths) == 1
    rows = json.loads(second_paths[0].read_bytes())["items"]
    expected = (
        ["second"] if boundary is DeferBoundary.BEFORE_PUBLISH else ["first", "second"]
    )
    assert [row["op_id"] for row in rows] == expected
    record_defer(tmp_path, "00004.md", "batch", {"op_id": "first"})
    rows = load_deferred_records(tmp_path, "batch")
    assert sorted(row["op_id"] for row in rows) == ["first", "second"]
