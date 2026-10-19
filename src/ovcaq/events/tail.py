"""Persist raw evidence before decoding bounded newline-delimited frames."""

import hashlib
import json
import os
import stat
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from ovcaq.drivers.base import AgentDriver
from ovcaq.events import (
    PROTOCOL_VERSION,
    Observation,
    ObservationType,
    observation_record,
    sanitize_text,
)
from ovcaq.events.model import has_invalid_unicode_scalar
from ovcaq.runtime.session import SessionEvidenceWriter
from ovcaq.state.schema import MAX_STATE_BYTES, JSONValue

_PREVIEW_WINDOW_BYTES = 4096


class NormalizedEventWriter:
    """Write sanitized observations as private, bounded JSONL evidence."""

    def __init__(self, path: Path, *, max_bytes: int, min_free_bytes: int) -> None:
        self._writer = SessionEvidenceWriter(
            path, max_bytes=max_bytes, min_free_bytes=min_free_bytes
        )

    def write(self, observation: Observation) -> int:
        payload = json.dumps(
            observation_record(observation), ensure_ascii=False, allow_nan=False
        )
        return self._writer.write((payload + "\n").encode("utf-8"))

    def flush(self) -> None:
        self._writer.flush()

    def close(self) -> None:
        self._writer.close()


class RawFirstDecoder:
    """Frame only durable raw bytes, retaining bounded previews on decode failure."""

    def __init__(
        self,
        *,
        raw: SessionEvidenceWriter,
        normalized: NormalizedEventWriter,
        driver: AgentDriver,
        run_id: str,
        session_id: str | None = None,
        max_frame_bytes: int = 1024 * 1024,
    ) -> None:
        self._raw = raw
        self._normalized = normalized
        self._driver = driver
        self._run_id = run_id
        self._session_id = session_id
        self._bind_identity = session_id is not None
        self._max_frame_bytes = max_frame_bytes
        self._buffer = bytearray()
        self._length = 0
        self._digest = hashlib.sha256()
        self._last = b""

    def feed(self, chunk: bytes) -> tuple[Observation, ...]:
        self._raw.write(chunk)
        self._raw.flush()
        emitted: list[Observation] = []
        offset = 0
        view = memoryview(chunk)
        while offset < len(chunk):
            newline = chunk.find(b"\n", offset)
            end = len(chunk) if newline < 0 else newline
            segment = view[offset:end]
            if segment:
                # Defer the last byte so CRLF framing excludes its CR from the
                # digest, even when the CR and LF arrive in separate chunks.
                self._digest.update(self._last)
                self._digest.update(segment[:-1])
                self._last = bytes(segment[-1:])
                self._length += len(segment)
                capacity = max(self._max_frame_bytes + 1, 512) - len(self._buffer)
                self._buffer.extend(segment[:capacity])
            if newline < 0:
                break
            emitted.extend(self._complete(terminated=True))
            offset = newline + 1
        return tuple(emitted)

    def finish(self) -> tuple[Observation, ...]:
        self._raw.flush()
        return self._complete(terminated=False) if self._length else ()

    @staticmethod
    def _has_invalid_json_scalar(frame: str) -> bool:
        try:
            record = json.loads(frame)
        except (ValueError, RecursionError):
            return False
        return has_invalid_unicode_scalar(record)

    def _complete(self, *, terminated: bool) -> tuple[Observation, ...]:
        trim_cr = terminated and self._last == b"\r"
        length = self._length - int(trim_cr)
        if not trim_cr:
            self._digest.update(self._last)
        reason = "frame exceeds byte limit"
        observations: tuple[Observation, ...] | None = None
        if length <= self._max_frame_bytes:
            try:
                frame = self._buffer[:length].decode("utf-8")
            except UnicodeDecodeError:
                reason = "frame contains invalid UTF-8"
            else:
                try:
                    if self._has_invalid_json_scalar(frame):
                        reason = "frame contains invalid Unicode scalar value"
                    else:
                        # Consume lazy iterables before publishing any part of a frame.
                        observations = tuple(self._driver.decode(frame))
                except Exception:  # noqa: BLE001 - provider failures become observations
                    reason = "driver failed to decode frame"
        if observations is None:
            observations = (self._unknown_observation(reason=reason, length=length),)
        observations = self._bind_observations(observations)
        self._buffer.clear()
        self._length = 0
        self._digest = hashlib.sha256()
        self._last = b""
        for observation in observations:
            self._normalized.write(observation)
            if observation.session_id is not None:
                self._session_id = observation.session_id
        return observations

    def _unknown_observation(self, *, reason: str, length: int) -> Observation:
        return Observation(
            protocol_version=PROTOCOL_VERSION,
            timestamp=datetime.now(UTC),
            provider=self._driver.name,
            run_id=self._run_id,
            session_id=self._session_id,
            lane_id=None,
            type=ObservationType.RAW_UNKNOWN,
            payload={
                "reason": reason,
                "raw_sha256": self._digest.hexdigest(),
                "preview": self._preview(length),
            },
        )

    def _bind_observations(
        self, observations: tuple[Observation, ...]
    ) -> tuple[Observation, ...]:
        if not self._bind_identity:
            return observations
        return tuple(
            replace(
                observation,
                run_id=self._run_id,
                session_id=self._session_id,
                payload=(
                    dict(observation.payload)
                    | {"source_session_id": observation.session_id}
                    if observation.type == ObservationType.SESSION_STARTED
                    and observation.session_id is not None
                    else observation.payload
                ),
            )
            for observation in observations
        )

    def _preview(self, length: int) -> str:
        """Sanitize a bounded head of the frame, never a cut-off final token."""
        window = bytes(self._buffer[: min(_PREVIEW_WINDOW_BYTES, length)])
        text = window.decode("utf-8", errors="replace")
        if len(window) < length:
            # The window ends mid-frame; a secret may straddle the cut.
            end = len(text)
            while end and not text[end - 1].isspace():
                end -= 1
            if not end:
                # Unbroken window: an `sk-` token may hide in it unredacted.
                end = 0 if "sk-" in text.lower() else len(text)
            text = text[:end]
        return sanitize_text(text)[:512]


@dataclass(frozen=True, slots=True)
class TailGap:
    kind: Literal["missing", "replaced", "truncated", "malformed", "oversized"]
    detail: str


@dataclass(frozen=True, slots=True)
class TailBatch[T]:
    records: tuple[T, ...]
    gaps: tuple[TailGap, ...]
    reset: bool
    backlog: bool
    complete_history: bool


class JsonlFollower[T]:
    """Follow appended JSONL objects with bounded work, never writing the file."""

    def __init__(
        self,
        path: Path,
        decode: Callable[[Mapping[str, JSONValue]], T],
        *,
        max_record_bytes: int = MAX_STATE_BYTES,
        replay_bytes: int = 256 * 1024,
        max_read_bytes: int = 1024 * 1024,
        max_records: int = 1024,
    ) -> None:
        self._path = path
        self._decoder = decode
        self._replay_bytes = replay_bytes
        self._max_records = max_records
        self._max_read_bytes = max_read_bytes
        self._max_record_bytes = max_record_bytes
        self._fd: int | None = None
        self._started = False
        self._offset = 0
        self._pending = bytearray()
        # Skips the rest of a row cut by replay or exceeding the size limit.
        self._discarding = False
        self._complete = True

    def close(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def read(self) -> TailBatch[T]:
        gaps: list[TailGap] = []
        try:
            information = os.lstat(self._path)
        except FileNotFoundError:
            return TailBatch(
                (), (TailGap("missing", "file does not exist"),), False, False, False
            )
        if not stat.S_ISREG(information.st_mode):
            return TailBatch(
                (), (TailGap("missing", "not a regular file"),), False, False, False
            )
        reset = self._reset_if_changed(information, gaps)
        if self._fd is None:
            try:
                self._open(information)
            except (OSError, ValueError) as error:
                gap = TailGap("missing", f"cannot open file: {type(error).__name__}")
                return TailBatch((), (*gaps, gap), reset, False, False)
        assert self._fd is not None
        records: list[T] = []
        budget = self._max_read_bytes
        while budget > 0 and len(records) < self._max_records:
            chunk = os.pread(self._fd, min(budget, 64 * 1024), self._offset)
            if not chunk:
                break
            consumed = self._consume(chunk, records, gaps)
            self._offset += consumed
            budget -= consumed
            if consumed < len(chunk):
                break
        backlog = self._offset < os.fstat(self._fd).st_size
        return TailBatch(
            tuple(records), tuple(gaps), reset, backlog, self._complete and not backlog
        )

    def _reset_if_changed(
        self, information: os.stat_result, gaps: list[TailGap]
    ) -> bool:
        if self._fd is None:
            return False
        held = os.fstat(self._fd)
        change: Literal["replaced", "truncated"] | None = None
        if not os.path.samestat(held, information):
            change = "replaced"
        elif information.st_size < self._offset:
            change = "truncated"
        if change is None:
            return False
        self.close()
        gaps.append(TailGap(change, f"file was {change}; restarting at 0"))
        self._offset = 0
        self._pending.clear()
        self._discarding = False
        self._complete = True
        return True

    def _open(self, information: os.stat_result) -> None:
        descriptor = os.open(self._path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        if not os.path.samestat(information, os.fstat(descriptor)):
            os.close(descriptor)
            raise ValueError("file changed while opening")
        self._fd = descriptor
        if self._started:
            return
        self._started = True
        size = information.st_size
        if size > self._replay_bytes:
            self._offset = size - self._replay_bytes
            self._complete = False
            self._discarding = os.pread(descriptor, 1, self._offset - 1) != b"\n"

    def _consume(self, chunk: bytes, records: list[T], gaps: list[TailGap]) -> int:
        start = 0
        while start < len(chunk) and len(records) < self._max_records:
            newline = chunk.find(b"\n", start)
            end = len(chunk) if newline < 0 else newline
            if not self._discarding:
                if len(self._pending) + end - start > self._max_record_bytes:
                    self._pending.clear()
                    self._discarding = True
                    gaps.append(
                        TailGap(
                            "oversized", f"row exceeds {self._max_record_bytes} bytes"
                        )
                    )
                else:
                    self._pending += chunk[start:end]
            if newline < 0:
                return len(chunk)
            if self._discarding:
                self._discarding = False
            else:
                self._decode(bytes(self._pending), records, gaps)
                self._pending.clear()
            start = newline + 1
        return start

    def _decode(self, line: bytes, records: list[T], gaps: list[TailGap]) -> None:
        try:
            record = json.loads(line.decode("utf-8"))
            if not isinstance(record, dict):
                raise TypeError("row is not a JSON object")
            records.append(self._decoder(cast(Mapping[str, JSONValue], record)))
        except Exception as error:  # noqa: BLE001 - decoder failures become gaps
            # JSON RecursionError and any decoder fault become gaps; signals do not.
            gaps.append(TailGap("malformed", f"row rejected: {type(error).__name__}"))
