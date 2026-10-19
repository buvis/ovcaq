from __future__ import annotations

import os
import stat
from collections.abc import Callable
from pathlib import Path

import pytest

from ovcaq.state.schema import State
from ovcaq.workflow.reports import archive_final_state, publish_audit, publish_report


def test_first_batch_report_includes_earlier_prd_details_and_replaces_them(
    tmp_path: Path, workflow_state: State
) -> None:
    earlier = {
        "op_id": "earlier",
        "prd": "00003-earlier.md",
        "type": "stall",
        "detail": "unfinished design",
    }
    current = {
        "op_id": "current",
        "prd": workflow_state["work"]["prd"],
        "detail": "current detail",
    }
    path = publish_report(tmp_path, workflow_state, (current, earlier, earlier))
    text = path.read_text()
    assert "- Deferred records: 2" in text
    assert text.count("unfinished design") == 1
    assert text.count("| 00003-earlier.md | earlier |") == 1
    assert text.count("current detail") == 1
    publish_report(tmp_path, workflow_state, (earlier, current))
    assert path.read_text() == text
    workflow_state["work"]["prd"] = "00005-next.md"
    earlier["detail"] = "updated design detail"
    publish_report(tmp_path, workflow_state, (earlier, current, earlier))
    updated = path.read_text()
    assert "unfinished design" not in updated
    assert updated.count("updated design detail") == 1
    assert updated.count("current detail") == 1
    publish_report(tmp_path, workflow_state, (current, earlier))
    assert path.read_text() == updated


@pytest.fixture(params=("report", "audit", "archive"))
def publisher(
    request: pytest.FixtureRequest, workflow_state: State, tmp_path: Path
) -> Callable[[], Path]:
    workflow_state["work"].update(phase="done", next_phase="")
    return {
        "report": lambda: publish_report(tmp_path, workflow_state, ()),
        "audit": lambda: publish_audit(tmp_path, workflow_state),
        "archive": lambda: archive_final_state(tmp_path, workflow_state),
    }[request.param]


def _observe_syncs(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    synced: list[int] = []
    native_sync = os.fsync

    def sync(descriptor: int) -> None:
        metadata = os.fstat(descriptor)
        if stat.S_ISDIR(metadata.st_mode):
            synced.append(metadata.st_ino)
        native_sync(descriptor)

    monkeypatch.setattr(os, "fsync", sync)
    return synced


def test_publication_syncs_each_created_directory_parent(
    publisher: Callable[[], Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    synced = _observe_syncs(monkeypatch)
    path = publisher()
    assert tmp_path.stat().st_ino in synced
    assert path.parent.stat().st_ino in synced
    assert all(
        parent.stat().st_ino in synced
        for parent in path.parents
        if parent.is_relative_to(tmp_path)
    )


def test_identical_retry_finishes_failed_publication_directory_sync(
    publisher: Callable[[], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = publisher()
    payload = path.read_bytes()
    path.unlink()
    native_sync = os.fsync

    def fail_after_replace(descriptor: int) -> None:
        if path.exists() and stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise OSError("injected directory fsync failure")
        native_sync(descriptor)

    with monkeypatch.context() as patches:
        patches.setattr(os, "fsync", fail_after_replace)
        with pytest.raises(OSError, match="injected directory fsync failure"):
            publisher()
    assert path.read_bytes() == payload
    synced = _observe_syncs(monkeypatch)
    assert publisher() == path
    assert path.parent.stat().st_ino in synced
    assert path.read_bytes() == payload


def test_retry_syncs_parent_after_interrupted_directory_creation(
    publisher: Callable[[], Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    native_sync = os.fsync

    def fail_directory(descriptor: int) -> None:
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise OSError("interrupted directory creation")
        native_sync(descriptor)

    with monkeypatch.context() as patches:
        patches.setattr(os, "fsync", fail_directory)
        with pytest.raises(OSError, match="interrupted directory creation"):
            publisher()

    synced = _observe_syncs(monkeypatch)
    path = publisher()
    assert tmp_path.stat().st_ino in synced
    assert path.parent.stat().st_ino in synced
