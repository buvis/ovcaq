"""Raw-first rejection of native frames containing invalid Unicode scalars."""

import copy
import errno
import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events import (
    Observation,
    ObservationType,
    observation_from_record,
    summary_record,
)
from ovcaq.events.tail import NormalizedEventWriter, RawFirstDecoder
from ovcaq.runtime.session import SessionEvidenceWriter


def native_unicode_driver() -> CodexDriver:
    return CodexDriver(
        AgentSettings(
            name="codex",
            command=("fixture-wrapper",),
            tiers={"standard": "fixture-model"},
            environment={},
            options={},
        ),
        run_id="unicode-run",
    )


def native_unicode_record(kind: str) -> dict[str, Any]:
    return {
        "startup": {"type": "thread.started", "thread_id": "poisoned-parent"},
        "completion": {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 99,
                "cached_input_tokens": 9,
                "output_tokens": 88,
            },
        },
        "collaboration": {
            "type": "item.started",
            "item": {
                "id": "collab-1",
                "type": "collab_tool_call",
                "tool": "spawn_agent",
                "sender_thread_id": "healthy-parent",
                "receiver_thread_ids": ["child-1"],
                "prompt": "Inspect receiver",
                "agents_states": {
                    "child-1": {"status": "running", "message": "Receiver evidence"}
                },
                "status": "in_progress",
            },
        },
    }[kind]


def unicode_adapter_state(driver: CodexDriver) -> tuple[Any, ...]:
    return copy.deepcopy(
        tuple(
            getattr(driver, field)
            for field in ("_session_id", "_usage", "_thread_conflict", "_identities")
        )
    )


def unicode_normalized(path: Path) -> tuple[Observation, ...]:
    return tuple(
        observation_from_record(json.loads(line))
        for line in path.read_bytes().splitlines()
    )


@pytest.fixture
def unicode_tail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    raw_path = tmp_path / "raw.jsonl"
    normalized_path = tmp_path / "normalized.jsonl"
    raw = SessionEvidenceWriter(raw_path, max_bytes=1 << 20, min_free_bytes=0)
    normalized = NormalizedEventWriter(
        normalized_path, max_bytes=1 << 20, min_free_bytes=0
    )
    raw_information = raw_path.stat()
    durable: list[bytes] = []
    real_fsync = os.fsync

    def sync(descriptor: int) -> None:
        real_fsync(descriptor)
        if os.path.samestat(raw_information, os.fstat(descriptor)):
            durable.append(raw_path.read_bytes())

    monkeypatch.setattr(os, "fsync", sync)
    driver = native_unicode_driver()
    decoder = RawFirstDecoder(
        raw=raw,
        normalized=normalized,
        driver=driver,
        run_id="unicode-run",
        session_id="owned-session",
    )
    try:
        yield driver, decoder, raw_path, normalized_path, durable
    finally:
        normalized.close()
        raw.close()


def assert_unicode_gap(observations: tuple[Observation, ...], frame: bytes) -> None:
    assert len(observations) == 1
    gap = observations[0]
    assert gap.type is ObservationType.RAW_UNKNOWN
    assert gap.run_id == "unicode-run"
    assert gap.session_id == "owned-session"
    assert set(gap.payload) == {"reason", "raw_sha256", "preview"}
    assert gap.payload["reason"] == "frame contains invalid Unicode scalar value"
    assert gap.payload["raw_sha256"] == hashlib.sha256(frame).hexdigest()
    preview = gap.payload["preview"]
    assert isinstance(preview, str) and len(preview) <= 512
    assert "native-marker" in preview
    assert "synthetic-hidden" not in preview
    assert "[REDACTED]" in preview
    assert "\x1b" not in preview
    preview.encode("utf-8", errors="strict")


def poisoned_unicode_frame(kind: str, location: str, scalar: str) -> bytes:
    record = native_unicode_record(kind)
    record = {
        "note": "native-marker token=synthetic-hidden\x1b[31m",
        "padding": "x" * 700,
        **record,
    }
    if location == "native":
        if kind == "startup":
            record["thread_id"] = "poisoned-parent" + scalar
        elif kind == "completion":
            record["usage"]["ignored"] = scalar
        else:
            record["item"]["agents_states"]["child-1"]["message"] = scalar
    elif location == "ignored-value":
        record["ignored"] = scalar
    elif location == "nested-value":
        record["ignored"] = [{"deeper": [None, scalar]}]
    elif location == "nested-key":
        record["ignored"] = [{"deeper": [{scalar: "ignored"}]}]
    else:
        record["password"] = scalar
    return json.dumps(record, ensure_ascii=True).encode()


@pytest.mark.parametrize("scalar", [chr(0xD800), chr(0xDFFF)], ids=["high", "low"])
@pytest.mark.parametrize("kind", ["startup", "completion", "collaboration"])
@pytest.mark.parametrize(
    "location",
    ["native", "ignored-value", "nested-value", "nested-key", "secret"],
)
@pytest.mark.parametrize("initialized", [False, True])
@pytest.mark.parametrize(
    ("framing", "digest_suffix"),
    [(b"\n", b""), (b"\r\n", b""), (b"", b""), (b"\r\r\n", b"\r")],
    ids=["newline", "crlf", "unterminated", "one-framing-cr"],
)
def test_unsafe_native_frame_is_one_durable_gap_without_adapter_mutation(
    unicode_tail: Any,
    scalar: str,
    kind: str,
    location: str,
    initialized: bool,
    framing: bytes,
    digest_suffix: bytes,
) -> None:
    driver, decoder, raw_path, normalized_path, durable = unicode_tail
    emitted: tuple[Observation, ...] = ()
    if initialized:
        startup = {"type": "thread.started", "thread_id": "healthy-parent"}
        emitted += decoder.feed(json.dumps(startup).encode() + b"\n")
        emitted += decoder.feed(
            json.dumps(native_unicode_record("collaboration")).encode() + b"\n"
        )
    before = unicode_adapter_state(driver)
    previous = raw_path.read_bytes()
    frame = poisoned_unicode_frame(kind, location, scalar)
    wire = frame + framing
    assert decoder.feed(wire[:17]) == ()
    assert unicode_adapter_state(driver) == before
    rejected = decoder.feed(wire[17:]) + decoder.finish()
    assert_unicode_gap(rejected, frame + digest_suffix)
    assert unicode_adapter_state(driver) == before
    assert raw_path.read_bytes() == previous + wire
    assert durable[-1] == previous + wire
    assert unicode_normalized(normalized_path) == emitted + rejected


@pytest.mark.parametrize("kind", ["startup", "completion", "collaboration"])
def test_rejected_native_frame_preserves_later_healthy_identity_usage_and_terminal(
    unicode_tail: Any,
    kind: str,
) -> None:
    driver, decoder, raw_path, normalized_path, durable = unicode_tail
    frame = poisoned_unicode_frame(kind, "nested-key", "\udc00")
    rejected = decoder.feed(frame + b"\n")
    assert_unicode_gap(rejected, frame)
    startup = {"type": "thread.started", "thread_id": "healthy-parent"}
    collaboration = native_unicode_record("collaboration")
    completion = {
        "type": "turn.completed",
        "usage": {
            "input_tokens": 3,
            "cached_input_tokens": 0,
            "cache_write_input_tokens": 0,
            "output_tokens": 2,
        },
    }
    healthy_wire = b"".join(
        json.dumps(record).encode() + b"\n"
        for record in (startup, collaboration, completion)
    )
    healthy = decoder.feed(healthy_wire) + decoder.finish()
    assert all(value.type is not ObservationType.RAW_UNKNOWN for value in healthy)
    assert {value.type for value in healthy} >= {
        ObservationType.SESSION_STARTED,
        ObservationType.LANE_STARTED,
        ObservationType.USAGE_UPDATED,
        ObservationType.SESSION_COMPLETED,
    }
    assert all(value.session_id == "owned-session" for value in healthy)
    assert driver._session_id == "healthy-parent"
    summary = driver.summarize((*rejected, *healthy), 0)
    assert summary.success and summary.session_id == "owned-session"
    usage = summary_record(summary)["usage"]
    assert usage["input_tokens"] == 3 and usage["output_tokens"] == 2
    assert raw_path.read_bytes() == durable[-1] == frame + b"\n" + healthy_wire
    assert unicode_normalized(normalized_path) == rejected + healthy


def test_valid_escaped_pair_remains_a_native_startup_record(unicode_tail: Any) -> None:
    driver, decoder, raw_path, normalized_path, durable = unicode_tail
    identity = "healthy-\U0001f680"
    frame = json.dumps(
        {
            "type": "thread.started",
            "thread_id": identity,
            "ignored": {"\U0001f680": ["\U0001f680"]},
        },
        ensure_ascii=True,
    ).encode()
    assert b"\\ud83d\\ude80" in frame
    observations = decoder.feed(frame + b"\r\n") + decoder.finish()
    assert len(observations) == 1
    assert observations[0].type is ObservationType.SESSION_STARTED
    assert observations[0].payload["source_session_id"] == identity
    assert observations[0].session_id == "owned-session"
    assert driver._session_id == identity
    assert raw_path.read_bytes() == durable[-1] == frame + b"\r\n"
    assert unicode_normalized(normalized_path) == observations


@pytest.mark.parametrize(
    "frame", [b"not JSON \\ud800", rb'{"type":"thread.started","ignored":"\ud800"']
)
def test_malformed_and_non_json_frames_keep_native_delegation(
    unicode_tail: Any,
    frame: bytes,
) -> None:
    driver, decoder, raw_path, normalized_path, durable = unicode_tail
    expected = native_unicode_driver().decode(frame.decode())
    before = unicode_adapter_state(driver)
    observations = decoder.feed(frame + b"\n") + decoder.finish()
    assert [(value.type, dict(value.payload)) for value in observations] == [
        (value.type, dict(value.payload)) for value in expected
    ]
    assert all(value.session_id == "owned-session" for value in observations)
    assert all(
        value.payload["reason"] != "frame contains invalid Unicode scalar value"
        for value in observations
    )
    assert unicode_adapter_state(driver) == before
    assert raw_path.read_bytes() == durable[-1] == frame + b"\n"
    assert unicode_normalized(normalized_path) == observations


def test_deep_json_recursion_preserves_native_gap_and_durable_evidence(
    unicode_tail: Any,
) -> None:
    driver, decoder, raw_path, normalized_path, durable = unicode_tail
    driver.decode(json.dumps({"type": "thread.started", "thread_id": "healthy-parent"}))
    driver.decode(json.dumps(native_unicode_record("completion")))
    depth = 100_000
    frame = (
        b'{"type":"thread.started","thread_id":"poisoned-parent","ignored":'
        + b"[" * depth
        + b"0"
        + b"]" * depth
        + b"}"
    )
    with pytest.raises(RecursionError):
        json.loads(frame)
    expected = native_unicode_driver().decode(frame.decode())
    assert len(expected) == 1
    assert expected[0].type is ObservationType.RAW_UNKNOWN
    before = unicode_adapter_state(driver)
    observations = decoder.feed(frame + b"\n") + decoder.finish()
    assert len(observations) == 1
    gap = observations[0]
    assert gap.type is ObservationType.RAW_UNKNOWN
    assert gap.run_id == "unicode-run"
    assert gap.session_id == "owned-session"
    assert dict(gap.payload) == dict(expected[0].payload)
    assert gap.payload["reason"] != "frame contains invalid Unicode scalar value"
    assert gap.payload["raw_sha256"] == hashlib.sha256(frame).hexdigest()
    assert unicode_adapter_state(driver) == before
    assert raw_path.read_bytes() == durable[-1] == frame + b"\n"
    assert unicode_normalized(normalized_path) == observations


@pytest.mark.parametrize("stage", ["raw", "normalized"])
@pytest.mark.parametrize("error_number", [errno.ENOSPC, errno.EIO])
def test_real_writer_failures_propagate_from_unsafe_native_frames(
    unicode_tail: Any,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    error_number: int,
) -> None:
    driver, decoder, raw_path, normalized_path, durable = unicode_tail
    target = raw_path if stage == "raw" else normalized_path
    information = target.stat()
    failure = OSError(error_number, "injected evidence write failure")
    real_write = os.write

    def failing_write(descriptor: int, payload: bytes) -> int:
        if os.path.samestat(information, os.fstat(descriptor)):
            raise failure
        return real_write(descriptor, payload)

    before = unicode_adapter_state(driver)
    frame = poisoned_unicode_frame("startup", "ignored-value", "\ud800")
    with monkeypatch.context() as patch:
        patch.setattr(os, "write", failing_write)
        with pytest.raises(OSError) as caught:
            decoder.feed(frame + b"\n")
    assert caught.value is failure
    assert unicode_adapter_state(driver) == before
    assert normalized_path.read_bytes() == b""
    assert raw_path.read_bytes() == (b"" if stage == "raw" else frame + b"\n")
    if stage == "normalized":
        assert durable[-1] == frame + b"\n"
