from __future__ import annotations

import json
import os
import tracemalloc
from pathlib import Path

import pytest

from ovcaq.events.tail import JsonlFollower


def test_empty_file_and_split_utf8_append_emit_complete_rows_once(
    tmp_path: Path,
) -> None:
    path = tmp_path / "events.jsonl"
    path.touch()
    follower = JsonlFollower(path, dict)
    try:
        empty = follower.read()
        assert empty.records == () and empty.gaps == ()
        assert empty.complete_history and not empty.backlog
        with path.open("ab") as stream:
            stream.write(b'{"text":"\xc3')
        assert follower.read().records == ()
        with path.open("ab") as stream:
            stream.write(b'\xa9"}\n{"text":"next"}\n')
        batch = follower.read()
        assert batch.records == ({"text": "é"}, {"text": "next"})
        assert batch.gaps == () and not batch.backlog
        assert follower.read().records == ()
        assert path.read_bytes() == b'{"text":"\xc3\xa9"}\n{"text":"next"}\n'
        nested = {
            "event": "custom.event",
            "payload": {"items": [1, None, {"enabled": True}], "ratio": 1.25},
            "metadata": {"label": "café", "empty": {}},
        }
        serialized = json.dumps(nested).encode() + b"\n"
        with path.open("ab") as stream:
            stream.write(serialized)
        assert follower.read().records == (nested,)
        assert follower.read().records == ()
        assert path.read_bytes().endswith(serialized)
    finally:
        follower.close()


@pytest.mark.parametrize("prefix", (b"", b'{"old":"long discarded record"}\n'))
def test_replay_at_a_row_boundary_keeps_the_first_whole_row(
    tmp_path: Path, prefix: bytes
) -> None:
    path = tmp_path / "events.jsonl"
    retained = b'{"n":1}\n{"n":2}\n'
    path.write_bytes(prefix + retained)
    follower = JsonlFollower(path, dict, replay_bytes=len(retained))
    try:
        batch = follower.read()
        assert batch.records == ({"n": 1}, {"n": 2})
        assert batch.complete_history is (not prefix)
        assert not batch.backlog
        assert path.read_bytes() == prefix + retained
    finally:
        follower.close()


def test_replay_discards_only_the_initial_partial_row(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_bytes(b'{"old":"discarded"}\n{"n":2}\n')
    follower = JsonlFollower(path, dict, replay_bytes=len(b'ded"}\n{"n":2}\n'))
    try:
        batch = follower.read()
        assert batch.records == ({"n": 2},)
        assert not batch.complete_history and not batch.backlog
        with path.open("ab") as stream:
            stream.write(b'{"n":3}\n')
        later = follower.read()
        assert later.records == ({"n": 3},)
        assert not later.complete_history
    finally:
        follower.close()


@pytest.mark.parametrize("limits", ({"max_records": 1}, {"max_read_bytes": 8}))
def test_each_call_caps_work_and_resumes_without_losing_rows(
    tmp_path: Path, limits: dict[str, int]
) -> None:
    path = tmp_path / "events.jsonl"
    path.write_bytes(b'{"n":1}\n{"n":2}\n{"n":3}\n')
    follower = JsonlFollower(path, dict, **limits)
    try:
        first = follower.read()
        second = follower.read()
        third = follower.read()
        assert first.records == ({"n": 1},)
        assert second.records == ({"n": 2},)
        assert third.records == ({"n": 3},)
        assert first.backlog and second.backlog
        assert not first.complete_history and not second.complete_history
        assert not third.backlog and third.complete_history
        assert follower.read().records == ()
    finally:
        follower.close()


@pytest.mark.parametrize("change", ("truncated", "replaced"))
def test_file_reset_discards_buffered_data_and_restarts_at_zero(
    tmp_path: Path, change: str
) -> None:
    path = tmp_path / "events.jsonl"
    path.write_bytes(b'{"old":1}\n{"unfinished":"prior')
    follower = JsonlFollower(path, dict, replay_bytes=8)
    try:
        assert not follower.read().complete_history
        replacement = b'{"n":1}\n{"n":2}\n'
        if change == "truncated":
            path.write_bytes(replacement)
        else:
            new = tmp_path / "replacement.jsonl"
            new.write_bytes(replacement)
            new.replace(path)
        batch = follower.read()
        assert batch.reset
        assert change in {gap.kind for gap in batch.gaps}
        assert batch.records == ({"n": 1}, {"n": 2})
        assert batch.complete_history and not batch.backlog
        assert path.read_bytes() == replacement
    finally:
        follower.close()


@pytest.mark.parametrize("bad", (b"{bad}", b"[]", b'{"n":"\xff"}'))
def test_malformed_rows_report_gaps_and_allow_later_valid_records(
    tmp_path: Path, bad: bytes
) -> None:
    path = tmp_path / "events.jsonl"
    content = b'{"n":1}\n' + bad + b'\n{"n":2}\n'
    path.write_bytes(content)
    follower = JsonlFollower(path, dict)
    try:
        batch = follower.read()
        assert batch.records == ({"n": 1}, {"n": 2})
        assert "malformed" in {gap.kind for gap in batch.gaps}
        assert all(isinstance(gap.detail, str) and gap.detail for gap in batch.gaps)
        assert path.read_bytes() == content
    finally:
        follower.close()


def test_decoder_rejection_does_not_discard_later_valid_objects(tmp_path: Path) -> None:
    def decode(record):
        if record["n"] == 2:
            raise ValueError("invalid record")
        return record["n"]

    path = tmp_path / "events.jsonl"
    path.write_bytes(b'{"n":1}\n{"n":2}\n{"n":3}\n')
    follower = JsonlFollower(path, decode)
    try:
        batch = follower.read()
        assert batch.records == (1, 3)
        assert "malformed" in {gap.kind for gap in batch.gaps}
    finally:
        follower.close()


def test_oversized_unfinished_row_uses_bounded_memory_and_recovers(
    tmp_path: Path,
) -> None:
    path = tmp_path / "events.jsonl"
    path.write_bytes(b"x" * (2 * 1024 * 1024))
    follower = JsonlFollower(
        path,
        dict,
        max_record_bytes=32,
        replay_bytes=4 * 1024 * 1024,
        max_read_bytes=4096,
    )
    gaps = []
    tracemalloc.start()
    try:
        for _ in range(512):
            batch = follower.read()
            assert batch.records == ()
            gaps.extend(batch.gaps)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    try:
        assert peak < 512 * 1024
        with path.open("ab") as stream:
            stream.write(b'\n{"n":1}\n')
        recovered = follower.read()
        assert recovered.records == ({"n": 1},)
        gaps.extend(recovered.gaps)
        assert "oversized" in {gap.kind for gap in gaps}
    finally:
        follower.close()


@pytest.mark.parametrize("obstacle", ("missing", "symlink", "directory", "fifo"))
def test_unavailable_or_unsafe_files_report_gaps_without_reading_targets(
    tmp_path: Path, obstacle: str
) -> None:
    path = tmp_path / "events.jsonl"
    target = tmp_path / "target.jsonl"
    target.write_bytes(b'{"private":1}\n')
    if obstacle == "symlink":
        path.symlink_to(target)
    elif obstacle == "directory":
        path.mkdir()
    elif obstacle == "fifo":
        os.mkfifo(path)
    follower = JsonlFollower(path, dict)
    try:
        batch = follower.read()
        assert batch.records == () and batch.gaps
        assert not batch.complete_history
        if obstacle == "missing":
            assert "missing" in {gap.kind for gap in batch.gaps}
            assert not path.exists()
        assert target.read_bytes() == b'{"private":1}\n'
    finally:
        follower.close()
