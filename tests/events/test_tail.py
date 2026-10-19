from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
import time
import tracemalloc
from collections.abc import Callable, Iterable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ovcaq.events import (
    PROTOCOL_VERSION,
    Observation,
    ObservationType,
    observation_from_record,
    observation_record,
)
from ovcaq.events.tail import NormalizedEventWriter, RawFirstDecoder
from ovcaq.runtime.session import EvidenceLimitError, SessionEvidenceWriter


def _observation(message: str) -> Observation:
    return Observation(
        protocol_version=1,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        provider="fake",
        run_id="run-1",
        session_id=None,
        lane_id=None,
        type=ObservationType.ACTIVITY_MESSAGE,
        payload={"message": message},
    )


def _read_observations(path: Path) -> tuple[Observation, ...]:
    return tuple(
        observation_from_record(json.loads(line))
        for line in path.read_bytes().splitlines()
    )


def _assert_unknown_evidence(
    observation: Observation, frame: bytes, ordinary: str
) -> None:
    assert observation.type == ObservationType.RAW_UNKNOWN
    assert observation.payload["raw_sha256"] == hashlib.sha256(frame).hexdigest()
    reason = observation.payload["reason"]
    assert isinstance(reason, str) and reason.strip()
    preview = observation.payload["preview"]
    assert isinstance(preview, str)
    assert ordinary in preview


class RecordingDriver:
    name = "fake"

    def __init__(self, before_decode: Callable[[], None] | None = None) -> None:
        self.lines: list[str] = []
        self.before_decode = before_decode

    def decode(self, raw_line: str) -> Iterable[Observation]:
        if self.before_decode is not None:
            self.before_decode()
        self.lines.append(raw_line)
        return (_observation(raw_line), _observation("second observation"))


@pytest.fixture
def evidence(tmp_path: Path):
    raw = SessionEvidenceWriter(
        tmp_path / "raw.jsonl", max_bytes=4 << 20, min_free_bytes=0
    )
    normalized = NormalizedEventWriter(
        tmp_path / "normalized.jsonl", max_bytes=4 << 20, min_free_bytes=0
    )
    try:
        yield raw, normalized
    finally:
        normalized.close()
        raw.close()


def test_normalized_lines_are_private_sanitized_and_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "normalized.jsonl"
    previous_umask = os.umask(0)
    try:
        writer = NormalizedEventWriter(path, max_bytes=4096, min_free_bytes=0)
    finally:
        os.umask(previous_umask)
    observations = (_observation("token=hidden-value\nhello é"), _observation("next"))
    try:
        assert stat.S_ISREG(path.stat().st_mode)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        previous_size = 0
        for observation in observations:
            accepted = writer.write(observation)
            content = path.read_bytes()
            assert accepted == len(content) - previous_size
            assert content.endswith(b"\n")
            assert b"hidden-value" not in content
            previous_size = len(content)
        lines = path.read_bytes().splitlines()
        assert len(lines) == len(observations)
        assert [json.loads(line) for line in lines] == [
            observation_record(observation) for observation in observations
        ]
        assert _read_observations(path) == observations
    finally:
        writer.close()


@pytest.mark.parametrize(
    "obstacle", ["file", "symlink", "dangling", "directory", "fifo"]
)
def test_normalized_creation_preserves_existing_paths(
    tmp_path: Path, obstacle: str
) -> None:
    path = tmp_path / "normalized.jsonl"
    target = tmp_path / "target"
    target.write_bytes(b"preserve")
    if obstacle == "file":
        path.write_bytes(b"prior evidence")
    elif obstacle == "symlink":
        path.symlink_to(target)
    elif obstacle == "dangling":
        path.symlink_to(tmp_path / "missing")
    elif obstacle == "directory":
        path.mkdir()
    else:
        os.mkfifo(path)
    before = path.lstat()
    with pytest.raises(OSError):
        NormalizedEventWriter(path, max_bytes=4096, min_free_bytes=0)
    assert os.path.samestat(before, path.lstat())
    assert target.read_bytes() == b"preserve"
    assert not (tmp_path / "missing").exists()
    if obstacle == "file":
        assert path.read_bytes() == b"prior evidence"


def test_normalized_ceiling_rejects_whole_record_without_damaging_prior_line(
    tmp_path: Path,
) -> None:
    observation = _observation("bounded")
    reference = tmp_path / "reference.jsonl"
    writer = NormalizedEventWriter(reference, max_bytes=4096, min_free_bytes=0)
    try:
        length = writer.write(observation)
    finally:
        writer.close()
    path = tmp_path / "normalized.jsonl"
    writer = NormalizedEventWriter(path, max_bytes=length, min_free_bytes=0)
    try:
        assert writer.write(observation) == length
        with pytest.raises(EvidenceLimitError):
            writer.write(observation)
        assert path.read_bytes() == reference.read_bytes()
        assert _read_observations(path) == (observation,)
    finally:
        writer.close()


@pytest.mark.parametrize("obstacle", ["symlink", "world-writable"])
def test_normalized_writer_rejects_unsafe_parent(tmp_path: Path, obstacle: str) -> None:
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    parent = tmp_path / "session"
    if obstacle == "symlink":
        parent.symlink_to(target, target_is_directory=True)
    else:
        parent.mkdir(mode=0o700)
        parent.chmod(0o777)
    with pytest.raises(ValueError):
        NormalizedEventWriter(
            parent / "normalized.jsonl", max_bytes=4096, min_free_bytes=0
        )
    assert not (parent / "normalized.jsonl").exists()
    assert list(target.iterdir()) == []


def test_normalized_records_respect_space_floor_and_finish_partial_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    available = 10000

    def filesystem_space(_location: object) -> os.statvfs_result:
        return os.statvfs_result((1, 1, 10000, 10000, available, 1, 1, 1, 0, 255))

    monkeypatch.setattr(os, "statvfs", filesystem_space)
    monkeypatch.setattr(os, "fstatvfs", filesystem_space)
    path = tmp_path / "normalized.jsonl"
    writer = NormalizedEventWriter(path, max_bytes=4096, min_free_bytes=128)
    real_write = os.write
    calls = 0

    def partial_write(descriptor: int, payload: bytes) -> int:
        nonlocal calls
        calls += 1
        if calls % 3 == 1:
            raise InterruptedError(errno.EINTR, "interrupted")
        return real_write(descriptor, payload[:17])

    observation = _observation("partial é")
    try:
        with monkeypatch.context() as patch:
            patch.setattr(os, "write", partial_write)
            length = writer.write(observation)
        assert length == len(path.read_bytes())
        available = 128 + length - 1
        with pytest.raises(EvidenceLimitError):
            writer.write(observation)
        assert _read_observations(path) == (observation,)
        available = 128 + length
        assert writer.write(observation) == length
        assert _read_observations(path) == (observation, observation)
    finally:
        writer.close()


def test_normalized_write_failure_preserves_prior_line_and_partial_new_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "normalized.jsonl"
    writer = NormalizedEventWriter(path, max_bytes=4096, min_free_bytes=0)
    observation = _observation("partial failure")
    real_write = os.write
    accepted = False

    def failing_write(descriptor: int, payload: bytes) -> int:
        nonlocal accepted
        if not accepted:
            accepted = True
            return real_write(descriptor, payload[:7])
        raise OSError(errno.ENOSPC, "injected disk full")

    try:
        writer.write(observation)
        previous = path.read_bytes()
        with monkeypatch.context() as patch:
            patch.setattr(os, "write", failing_write)
            with pytest.raises(OSError):
                writer.write(observation)
        assert path.read_bytes() == previous + previous[:7]
    finally:
        writer.close()
    assert path.read_bytes() == previous + previous[:7]


def test_normalized_close_syncs_and_closes_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "normalized.jsonl"
    writer = NormalizedEventWriter(path, max_bytes=4096, min_free_bytes=0)
    observation = _observation("durable")
    writer.write(observation)
    information = path.stat()
    real_fsync, real_close = os.fsync, os.close
    events: list[str] = []

    def sync(descriptor: int) -> None:
        is_evidence = os.path.samestat(information, os.fstat(descriptor))
        real_fsync(descriptor)
        if is_evidence:
            events.append("sync")

    def close(descriptor: int) -> None:
        is_evidence = os.path.samestat(information, os.fstat(descriptor))
        real_close(descriptor)
        if is_evidence:
            events.append("close")

    monkeypatch.setattr(os, "fsync", sync)
    monkeypatch.setattr(os, "close", close)
    try:
        writer.close()
        writer.close()
        assert events == ["sync", "close"]
        with pytest.raises(ValueError):
            writer.write(observation)
        assert _read_observations(path) == (observation,)
    finally:
        writer.close()


@pytest.mark.parametrize("chunk_size", [1, 3, 4096])
def test_frames_decode_only_after_exact_raw_bytes_are_synced(
    tmp_path: Path, evidence, monkeypatch: pytest.MonkeyPatch, chunk_size: int
) -> None:
    raw, normalized = evidence
    path = tmp_path / "raw.jsonl"
    information = path.stat()
    real_fsync = os.fsync
    durable = b""
    expected = b""

    def sync(descriptor: int) -> None:
        nonlocal durable
        real_fsync(descriptor)
        if os.path.samestat(information, os.fstat(descriptor)):
            durable = path.read_bytes()

    def before_decode() -> None:
        assert path.read_bytes() == expected
        assert durable == expected

    monkeypatch.setattr(os, "fsync", sync)
    driver = RecordingDriver(before_decode)
    decoder = RawFirstDecoder(
        raw=raw, normalized=normalized, driver=driver, run_id="run-1"
    )
    payload = b"first\r\n\n\xc3\xa9\nlast"
    emitted: tuple[Observation, ...] = ()
    assert decoder.feed(b"") == ()
    for offset in range(0, len(payload), chunk_size):
        chunk = payload[offset : offset + chunk_size]
        expected += chunk
        emitted += decoder.feed(chunk)
        assert path.read_bytes() == expected
        assert _read_observations(tmp_path / "normalized.jsonl") == emitted
    assert driver.lines == ["first", "", "é"]
    emitted += decoder.finish()
    assert driver.lines == ["first", "", "é", "last"]
    assert emitted == tuple(
        observation
        for line in driver.lines
        for observation in (_observation(line), _observation("second observation"))
    )
    assert _read_observations(tmp_path / "normalized.jsonl") == emitted


@pytest.mark.parametrize("chunk_size", (1, 4096))
@pytest.mark.parametrize("terminated", (False, True))
def test_invalid_utf8_preserves_original_bytes_and_emits_one_bounded_unknown(
    tmp_path: Path, evidence, chunk_size: int, terminated: bool
) -> None:
    raw, normalized = evidence
    driver = RecordingDriver()
    decoder = RawFirstDecoder(
        raw=raw, normalized=normalized, driver=driver, run_id="run-1"
    )
    frame = b'{"text":"ordinary token=hidden-value \xff' + b"x" * 1000 + b'"}'
    stream = b"good\n" + frame + (b"\n" if terminated else b"")
    emitted = (
        tuple(
            item
            for offset in range(0, len(stream), chunk_size)
            for item in decoder.feed(stream[offset : offset + chunk_size])
        )
        + decoder.finish()
    )
    assert len(emitted) == 3
    assert emitted[:2] == (_observation("good"), _observation("second observation"))
    unknown = emitted[-1]
    _assert_unknown_evidence(unknown, frame, "ordinary")
    assert unknown.run_id == "run-1"
    assert unknown.protocol_version == PROTOCOL_VERSION
    assert len(unknown.payload["preview"]) <= 512
    assert "hidden-value" not in unknown.payload["preview"]
    assert driver.lines == ["good"]
    assert (tmp_path / "raw.jsonl").read_bytes() == stream
    assert _read_observations(tmp_path / "normalized.jsonl") == emitted


def test_raw_decoder_requires_explicit_run_identity(evidence) -> None:
    raw, normalized = evidence
    with pytest.raises(TypeError, match="run_id"):
        RawFirstDecoder(raw=raw, normalized=normalized, driver=RecordingDriver())


@pytest.mark.parametrize("failure", ("oversized", "driver"))
def test_fallback_retains_latest_session_and_supplied_run_identity(
    tmp_path: Path, evidence, failure: str
) -> None:
    class SessionDriver(RecordingDriver):
        def decode(self, raw_line: str) -> Iterable[Observation]:
            if raw_line == "bad":
                raise RuntimeError("password=hidden-failure")
            session = raw_line if raw_line.startswith("session-") else None
            return (replace(_observation(raw_line), session_id=session),)

    raw, normalized = evidence
    decoder = RawFirstDecoder(
        raw=raw,
        normalized=normalized,
        driver=SessionDriver(),
        max_frame_bytes=32,
        run_id="supplied-run",
    )
    frame = b"x" * 33 if failure == "oversized" else b"bad"
    stream = b"session-first\nsession-last\nno-session\n" + frame + b"\n"
    emitted = decoder.feed(stream) + decoder.finish()
    assert len(emitted) == 4
    unknown = emitted[-1]
    _assert_unknown_evidence(unknown, frame, frame.decode())
    assert unknown.run_id == "supplied-run"
    assert unknown.session_id == "session-last"
    assert unknown.protocol_version == PROTOCOL_VERSION
    assert unknown.lane_id is None
    assert unknown.provider == "fake"
    assert len(unknown.payload["preview"]) <= 512
    assert "hidden-failure" not in json.dumps(observation_record(unknown))
    assert (tmp_path / "raw.jsonl").read_bytes() == stream
    assert _read_observations(tmp_path / "normalized.jsonl") == emitted


def test_empty_eof_does_not_create_an_extra_frame(evidence) -> None:
    raw, normalized = evidence
    driver = RecordingDriver()
    decoder = RawFirstDecoder(
        raw=raw, normalized=normalized, driver=driver, run_id="run-1"
    )
    assert decoder.finish() == ()
    assert driver.lines == []


def test_rejected_raw_chunk_never_reaches_decoder_or_normalized_evidence(
    tmp_path: Path,
) -> None:
    raw = SessionEvidenceWriter(tmp_path / "raw.jsonl", max_bytes=0, min_free_bytes=0)
    normalized = NormalizedEventWriter(
        tmp_path / "normalized.jsonl", max_bytes=4096, min_free_bytes=0
    )
    driver = RecordingDriver()
    decoder = RawFirstDecoder(
        raw=raw, normalized=normalized, driver=driver, run_id="run-1"
    )
    try:
        with pytest.raises(EvidenceLimitError):
            decoder.feed(b"rejected\n")
        assert driver.lines == []
        assert (tmp_path / "raw.jsonl").read_bytes() == b""
        assert (tmp_path / "normalized.jsonl").read_bytes() == b""
    finally:
        normalized.close()
        raw.close()


def test_terminated_stream_has_no_extra_eof_observation(evidence) -> None:
    raw, normalized = evidence
    driver = RecordingDriver()
    decoder = RawFirstDecoder(
        raw=raw, normalized=normalized, driver=driver, run_id="run-1"
    )
    assert tuple(decoder.feed(b"\n")) == (
        _observation(""),
        _observation("second observation"),
    )
    assert decoder.finish() == ()
    assert driver.lines == [""]


@pytest.mark.parametrize("terminated", [True, False])
def test_oversized_frame_emits_one_sanitized_unknown_and_recovers(
    tmp_path: Path, evidence, terminated: bool
) -> None:
    raw, normalized = evidence
    driver = RecordingDriver()
    decoder = RawFirstDecoder(
        raw=raw,
        normalized=normalized,
        driver=driver,
        max_frame_bytes=32,
        run_id="run-1",
    )
    frame = b"ordinary token=hidden-value " + b"b" * 15 + b"c" * 100
    chunks = [b"a" * 32 + b"\n", frame[:35], frame[35:]]
    if terminated:
        chunks.append(b"\nok\n")
    emitted = tuple(item for chunk in chunks for item in decoder.feed(chunk))
    emitted += decoder.finish()
    unknown = [item for item in emitted if item.type == ObservationType.RAW_UNKNOWN]
    assert len(unknown) == 1
    _assert_unknown_evidence(unknown[0], frame, "ordinary")
    assert unknown[0].provider == "fake"
    assert unknown[0].run_id == "run-1"
    assert unknown[0].protocol_version == PROTOCOL_VERSION
    assert unknown[0].session_id is None and unknown[0].lane_id is None
    assert unknown[0].timestamp.utcoffset().total_seconds() == 0
    assert "hidden-value" not in json.dumps(observation_record(unknown[0]))
    assert driver.lines == ["a" * 32] + (["ok"] if terminated else [])
    assert len(emitted) == (5 if terminated else 3)
    assert _read_observations(tmp_path / "normalized.jsonl") == emitted
    assert (tmp_path / "raw.jsonl").read_bytes() == b"".join(chunks)


@pytest.mark.parametrize("during_iteration", [False, True])
def test_unexpected_driver_failure_becomes_one_unknown_then_next_frame_decodes(
    tmp_path: Path, evidence, during_iteration: bool
) -> None:
    class FailingDriver(RecordingDriver):
        def decode(self, raw_line: str) -> Iterable[Observation]:
            if raw_line == "bad":
                if during_iteration:
                    return self.fail_lazily()
                raise RuntimeError("password=hidden-failure")
            return super().decode(raw_line)

        def fail_lazily(self) -> Iterable[Observation]:
            yield _observation("incomplete decoding")
            raise RuntimeError("password=hidden-failure")

    raw, normalized = evidence
    driver = FailingDriver()
    decoder = RawFirstDecoder(
        raw=raw, normalized=normalized, driver=driver, run_id="run-1"
    )
    emitted = decoder.feed(b"bad\ngood\n") + decoder.finish()
    assert len(emitted) == 3
    assert emitted[0].type == ObservationType.RAW_UNKNOWN
    _assert_unknown_evidence(emitted[0], b"bad", "bad")
    assert emitted[1:] == (_observation("good"), _observation("second observation"))
    assert "hidden-failure" not in json.dumps(observation_record(emitted[0]))
    assert _read_observations(tmp_path / "normalized.jsonl") == emitted
    assert (tmp_path / "raw.jsonl").read_bytes() == b"bad\ngood\n"


def test_oversized_unterminated_input_does_not_accumulate_unbounded_memory(
    tmp_path: Path, evidence
) -> None:
    raw, normalized = evidence
    driver = RecordingDriver()
    decoder = RawFirstDecoder(
        raw=raw,
        normalized=normalized,
        driver=driver,
        max_frame_bytes=64,
        run_id="run-1",
    )
    chunk = b"x" * 4096
    emitted: list[Observation] = []
    tracemalloc.start()
    try:
        for _ in range(512):
            emitted.extend(decoder.feed(chunk))
        emitted.extend(decoder.finish())
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 512 * 1024
    assert len(emitted) == 1
    _assert_unknown_evidence(emitted[0], chunk * 512, "x")
    assert driver.lines == []
    assert (tmp_path / "raw.jsonl").read_bytes() == chunk * 512
    assert _read_observations(tmp_path / "normalized.jsonl") == tuple(emitted)


@pytest.mark.parametrize("chunk_size", [1, 17, 4096])
def test_multiple_bad_frames_preserve_distinct_evidence_across_chunk_boundaries(
    tmp_path: Path, evidence, chunk_size: int
) -> None:
    class FailingDriver(RecordingDriver):
        def decode(self, raw_line: str) -> Iterable[Observation]:
            if raw_line.startswith("broken"):
                raise RuntimeError("password=hidden-exception")
            return super().decode(raw_line)

    frames = (
        b"oversize-alpha token=hidden-alpha " + b"x" * 90,
        b"broken-beta token=hidden-beta \xff",
        b"oversize-gamma token=hidden-gamma " + b"y" * 91,
        b"broken-delta token=hidden-delta\r",
    )
    stream = b"\r\n".join(frames[:3]) + b"\r\ngood\n" + frames[3]
    raw, normalized = evidence
    driver = FailingDriver()
    decoder = RawFirstDecoder(
        raw=raw,
        normalized=normalized,
        driver=driver,
        max_frame_bytes=64,
        run_id="run-1",
    )
    emitted = (
        tuple(
            item
            for offset in range(0, len(stream), chunk_size)
            for item in decoder.feed(stream[offset : offset + chunk_size])
        )
        + decoder.finish()
    )
    unknown = [item for item in emitted if item.type == ObservationType.RAW_UNKNOWN]
    assert len(unknown) == 4 and len(emitted) == 6
    for observation, frame in zip(unknown, frames, strict=True):
        _assert_unknown_evidence(observation, frame, frame.split()[0].decode())
        assert "hidden-" not in json.dumps(observation_record(observation))
    for oversized in (unknown[0], unknown[2]):
        for failed in (unknown[1], unknown[3]):
            assert oversized.payload["reason"] != failed.payload["reason"]
    assert driver.lines == ["good"]
    assert emitted[3:5] == (_observation("good"), _observation("second observation"))
    assert (tmp_path / "raw.jsonl").read_bytes() == stream
    assert _read_observations(tmp_path / "normalized.jsonl") == emitted


@pytest.mark.parametrize(
    "opener,body",
    (
        (" Bearer ", "Zq7v9k42mN8p23R4j62yAbCdEfGhIjKlMnOp"),
        (" ", "sk-" + "Zq7v9k42mN8p23R4j62yAbCdEfGhIjKl"),
    ),
)
def test_fallback_preview_hides_secret_prefix_straddling_truncation_boundary(
    tmp_path: Path, evidence, opener: str, body: str
) -> None:
    class FailingDriver(RecordingDriver):
        def decode(self, raw_line: str) -> Iterable[Observation]:
            raise RuntimeError("decode failed")

    raw, normalized = evidence
    decoder = RawFirstDecoder(
        raw=raw, normalized=normalized, driver=FailingDriver(), run_id="run-1"
    )
    for lead in range(500 - len(opener), 512 - len(opener) + 1):
        frame = ("x" * lead + opener + body).encode()
        (unknown,) = decoder.feed(frame + b"\n")
        preview = unknown.payload["preview"]
        assert len(preview) <= 512
        assert not any(preview.endswith(body[:k]) for k in range(1, len(body) + 1))


@pytest.mark.parametrize(
    "opener,body",
    (
        (" Bearer ", "Zq7v9k42mN8p23R4j62yAbCdEfGhIjKlMnOp"),
        (" ", "sk-" + "Zq7v9k42mN8p23R4j62yAbCdEfGhIjKl"),
    ),
)
def test_oversized_preview_hides_secret_prefix_straddling_frame_cut(
    evidence, opener: str, body: str
) -> None:
    raw, normalized = evidence
    decoder = RawFirstDecoder(
        raw=raw,
        normalized=normalized,
        driver=RecordingDriver(),
        max_frame_bytes=512,
        run_id="run-1",
    )
    for lead in range(490 - len(opener), 512 - len(opener) + 1):
        frame = ("x" * lead + opener + body + " " + "y" * 600).encode()
        (unknown,) = decoder.feed(frame + b"\n")
        preview = unknown.payload["preview"]
        assert len(preview) <= 512
        secret = body.removeprefix("sk-")
        assert not any(secret[:k] in preview for k in range(1, len(secret) + 1))


def test_oversized_unbroken_preview_hides_sk_prefix_at_frame_cut(evidence) -> None:
    raw, normalized = evidence
    decoder = RawFirstDecoder(
        raw=raw,
        normalized=normalized,
        driver=RecordingDriver(),
        max_frame_bytes=512,
        run_id="run-1",
    )
    body = "Zq7v9k42mN8p" + "23R4j62yAbCdEfGhIjKl"
    frame = ("x" * 494 + "-" + "sk-" + body + "y" * 600).encode()
    (unknown,) = decoder.feed(frame + b"\n")
    preview = unknown.payload["preview"]
    assert preview == ""
    assert not any(body[:k] in preview for k in range(1, len(body) + 1))


def _oversized_preview(evidence, frame: str) -> str:
    raw, normalized = evidence
    decoder = RawFirstDecoder(
        raw=raw,
        normalized=normalized,
        driver=RecordingDriver(),
        max_frame_bytes=512,
        run_id="run-1",
    )
    (unknown,) = decoder.feed(frame.encode() + b"\n")
    assert unknown.type == ObservationType.RAW_UNKNOWN
    preview = unknown.payload["preview"]
    assert isinstance(preview, str)
    return preview


def test_unbroken_truncated_window_hides_token_chars_after_inner_sk_marker(
    evidence,
) -> None:
    preview = _oversized_preview(evidence, "x" * 490 + "-sk-ABCDEsk-" + "Z" * 600)
    assert preview == ""
    assert "ABCDE" not in preview


def test_unbroken_truncated_window_with_dotted_capital_i_previews_empty(
    evidence,
) -> None:
    preview = _oversized_preview(evidence, "İ" * 10 + "x" * 480 + "sk-" + "Q" * 600)
    assert preview == ""


@pytest.mark.parametrize(
    "frame,expected",
    ((b"hello\r\n", "hello"), (b"a\rb\r\n", "a\rb")),
)
def test_short_fallback_frame_drops_only_one_trailing_cr(
    evidence, frame: bytes, expected: str
) -> None:
    class FailingDriver(RecordingDriver):
        def decode(self, raw_line: str) -> Iterable[Observation]:
            raise RuntimeError("decode failed")

    raw, normalized = evidence
    decoder = RawFirstDecoder(
        raw=raw, normalized=normalized, driver=FailingDriver(), run_id="run-1"
    )
    (unknown,) = decoder.feed(frame)
    assert unknown.type == ObservationType.RAW_UNKNOWN
    assert unknown.payload["preview"] == expected


def test_failed_long_unbroken_frame_previews_in_bounded_time(evidence) -> None:
    class FailingDriver(RecordingDriver):
        def decode(self, raw_line: str) -> Iterable[Observation]:
            raise RuntimeError("decode failed")

    raw, normalized = evidence
    decoder = RawFirstDecoder(
        raw=raw, normalized=normalized, driver=FailingDriver(), run_id="run-1"
    )
    started = time.perf_counter()
    (unknown,) = decoder.feed(b"a" * 200_000) + decoder.finish()
    assert time.perf_counter() - started < 1.0
    assert unknown.type == ObservationType.RAW_UNKNOWN
    assert len(unknown.payload["preview"]) <= 512
