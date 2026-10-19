import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import LaunchRequest
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import Observation, sanitize_text
from ovcaq.events.reducer import reduce_session

FAKE_CREDENTIAL = "sk-" + "SyntheticCredentialForDecoderTestOnly123456789012"


def assert_credential_redacted(text: str) -> None:
    assert FAKE_CREDENTIAL not in text
    assert "[REDACTED]" in text


@pytest.fixture
def driver() -> CodexDriver:
    settings = AgentSettings(
        name="codex",
        command=("fixture-wrapper", "--literal-prefix", "fixture-launcher"),
        tiers={"standard": "fixture-model", "premium": "fixture-large"},
        environment={"TASK_MODE": "fixture", "TASK_LABEL": "two words"},
        options={},
    )
    return CodexDriver(settings, run_id="decode-run")


def decode_record(driver: CodexDriver, record: object) -> tuple[Observation, ...]:
    return driver.decode(json.dumps(record))


def strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [text for child in value.values() for text in strings(child)]
    if isinstance(value, (list, tuple)):
        return [text for child in value for text in strings(child)]
    return []


def assert_identity(observation: Observation, session_id: str | None) -> None:
    assert observation.protocol_version == 1
    assert observation.provider == "codex"
    assert observation.run_id == "decode-run"
    assert observation.session_id == session_id
    assert observation.lane_id is None


def test_thread_and_turn_preserve_identity_and_use_utc_receipt_time(
    driver: CodexDriver,
) -> None:
    before = datetime.now(UTC)
    started = decode_record(
        driver, {"type": "thread.started", "thread_id": "example-healthy"}
    )
    turn = decode_record(driver, {"type": "turn.started"})
    after = datetime.now(UTC)
    assert len(started) == len(turn) == 1
    assert started[0].type == "session.started"
    assert turn[0].type == "activity.message"
    assert turn[0].payload["kind"] == "turn"
    for observation in (*started, *turn):
        assert_identity(observation, "example-healthy")
        assert observation.timestamp.utcoffset() == timedelta(0)
        assert before <= observation.timestamp <= after


@pytest.mark.parametrize("event", ["item.started", "item.updated", "item.completed"])
@pytest.mark.parametrize(
    ("native_kind", "kind"), [("agent_message", "text"), ("reasoning", "thinking")]
)
def test_text_and_reasoning_items_preserve_text_and_item_identity(
    driver: CodexDriver, event: str, native_kind: str, kind: str
) -> None:
    decode_record(driver, {"type": "thread.started", "thread_id": "text-thread"})
    text = "Inspect the example project.\nKeep this second line."
    observations = decode_record(
        driver,
        {"type": event, "item": {"id": "item_text", "type": native_kind, "text": text}},
    )
    assert len(observations) == 1
    observation = observations[0]
    assert_identity(observation, "text-thread")
    assert observation.type == "activity.message"
    assert observation.payload["kind"] == kind
    assert observation.payload["text"] == text
    assert "item_text" in strings(observation.payload)


@pytest.mark.parametrize("size", [4096, 4097, 12000])
def test_text_is_sanitized_and_bounded(driver: CodexDriver, size: int) -> None:
    text = "Visible " + "x" * (size - 8)
    observations = decode_record(
        driver,
        {
            "type": "item.completed",
            "item": {"id": "bounded", "type": "agent_message", "text": text},
        },
    )
    assert len(observations) == 1
    payload = observations[0].payload
    assert payload["kind"] == "text"
    rendered = payload["text"]
    assert isinstance(rendered, str)
    assert rendered.startswith("Visible ")
    assert 0 < len(rendered) <= 4096
    if size == 4096:
        assert rendered == text
    controlled = "\x1b[31mVisible\x1b[0m\x00 warning " + FAKE_CREDENTIAL
    sanitized = decode_record(
        driver,
        {
            "type": "item.updated",
            "item": {"id": "sanitized", "type": "reasoning", "text": controlled},
        },
    )
    assert sanitized[0].payload["text"] == sanitize_text(controlled)
    assert_credential_redacted(sanitized[0].payload["text"])


@pytest.mark.parametrize("event", ["item.started", "item.updated", "item.completed"])
@pytest.mark.parametrize("completed", [False, True])
def test_todo_items_preserve_plan_steps(
    driver: CodexDriver, event: str, completed: bool
) -> None:
    observations = decode_record(
        driver,
        {
            "type": event,
            "item": {
                "id": "item_14",
                "type": "todo_list",
                "items": [
                    {"text": "Inspect example", "completed": completed},
                    {"text": "Verify example", "completed": False},
                ],
            },
        },
    )
    assert len(observations) == 1
    observation = observations[0]
    assert observation.type == "activity.message"
    assert observation.payload["kind"] == "plan"
    detail = "\n".join(strings(observation.payload))
    assert "Inspect example" in detail
    assert "Verify example" in detail
    assert all(text == sanitize_text(text) for text in strings(observation.payload))


def test_plan_detail_is_sanitized_and_bounded(driver: CodexDriver) -> None:
    observations = decode_record(
        driver,
        {
            "type": "item.updated",
            "item": {
                "id": "plan-long",
                "type": "todo_list",
                "items": [
                    {
                        "text": "\x1b[31mInspect\x1b[0m "
                        + FAKE_CREDENTIAL
                        + " "
                        + "x" * 12000,
                        "completed": False,
                    },
                ],
            },
        },
    )
    assert len(observations) == 1
    payload = observations[0].payload
    assert payload["kind"] == "plan"
    detail = strings(payload)
    assert any("Inspect" in text for text in detail)
    assert all(len(text) <= 4096 and text == sanitize_text(text) for text in detail)
    assert_credential_redacted("\n".join(detail))


@pytest.mark.parametrize("event", ["item.started", "item.updated", "item.completed"])
def test_nonfatal_error_items_remain_activity(driver: CodexDriver, event: str) -> None:
    message = "Example non-fatal \x1b[31mwarning\x1b[0m. " + FAKE_CREDENTIAL
    observations = decode_record(
        driver,
        {
            "type": event,
            "item": {"id": "item_warning", "type": "error", "message": message},
        },
    )
    assert len(observations) == 1
    observation = observations[0]
    assert observation.type == "activity.message"
    assert observation.payload["kind"] == "error"
    assert sanitize_text(message) in "\n".join(strings(observation.payload))
    assert all(
        len(text) <= 4096 and text == sanitize_text(text)
        for text in strings(observation.payload)
    )
    assert_credential_redacted("\n".join(strings(observation.payload)))


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "not JSON",
        "null",
        "[]",
        "42",
        "{}",
        '{"type":42}',
        '{"type":"thread.started","thread_id":null}',
        '{"type":"thread.started","thread_id":""}',
        '{"type":"thread.started","thread_id":42}',
        '{"type":"item.completed","item":null}',
        '{"type":"item.completed","item":[]}',
        '{"type":"item.completed","item":{"type":"agent_message","text":42}}',
        '{"type":"item.completed","item":{"id":"","type":"agent_message","text":"x"}}',
        '{"type":"item.completed","item":{"id":42,"type":"reasoning","text":"x"}}',
        '{"type":"item.completed","item":{"id":"a","type":"agent_message","text":null}}',
        '{"type":"item.completed","item":{"id":"a","type":"todo_list","items":{}}}',
        '{"type":"item.completed","item":{"id":"a","type":"todo_list","items":[null]}}',
        '{"type":"item.completed","item":{"id":"a","type":"todo_list","items":[{"text":42,"completed":false}]}}',
        '{"type":"item.completed","item":{"id":"a","type":"todo_list","items":[{"text":"x","completed":"yes"}]}}',
        '{"type":"item.completed","item":{"id":"a","type":"error","message":null}}',
        '{"type":"item.completed","item":{"id":"future","type":"future_item","extra":true}}',
        '{"type":"future.event","extra":true}',
        '{"type":"item.completed","item":',
        "[" * 2000 + "0" + "]" * 2000,
        FAKE_CREDENTIAL + " \x1b[31m" + "invalid\x00" * 1000,
    ],
)
def test_malformed_and_future_records_return_sanitized_raw_without_changing_thread(
    driver: CodexDriver, raw: str
) -> None:
    decode_record(driver, {"type": "thread.started", "thread_id": "stable-thread"})
    before = datetime.now(UTC)
    observations = driver.decode(raw)
    after = datetime.now(UTC)
    assert isinstance(observations, tuple)
    unknowns = [
        observation for observation in observations if observation.type == "raw.unknown"
    ]
    assert unknowns
    for observation in unknowns:
        assert_identity(observation, "stable-thread")
        assert before <= observation.timestamp <= after
        assert observation.timestamp.utcoffset() == timedelta(0)
        payload = observation.payload
        assert set(payload) == {"reason", "raw_sha256", "preview"}
        assert isinstance(payload["reason"], str) and payload["reason"]
        assert payload["reason"] == sanitize_text(payload["reason"])
        assert payload["raw_sha256"] == hashlib.sha256(raw.encode()).hexdigest()
        assert isinstance(payload["preview"], str)
        assert len(payload["preview"]) <= 512
        assert payload["preview"] == sanitize_text(payload["preview"])
        if FAKE_CREDENTIAL in raw:
            assert_credential_redacted(payload["preview"])
        if raw and sanitize_text(raw):
            assert payload["preview"]
            assert payload["preview"] in sanitize_text(raw)
    turn = decode_record(driver, {"type": "turn.started"})
    assert turn[0].type == "activity.message"
    assert_identity(turn[0], "stable-thread")


def test_unknown_extra_fields_do_not_contaminate_normalized_payload(
    driver: CodexDriver,
) -> None:
    observations = decode_record(
        driver,
        {
            "type": "thread.started",
            "thread_id": "example-unknown-fields",
            "new_field": "native-only-marker",
        },
    )
    assert len(observations) == 1
    assert observations[0].type == "session.started"
    assert_identity(observations[0], "example-unknown-fields")
    assert "native-only-marker" not in strings(observations[0].payload)


def test_conflicting_threads_remain_visible_to_shared_reducer(
    driver: CodexDriver,
) -> None:
    first = decode_record(driver, {"type": "thread.started", "thread_id": "thread-one"})
    second = decode_record(
        driver, {"type": "thread.started", "thread_id": "thread-two"}
    )
    assert [observation.session_id for observation in (*first, *second)] == [
        "thread-one",
        "thread-two",
    ]
    assert all(
        observation.type == "session.started" for observation in (*first, *second)
    )
    reduction = reduce_session((*first, *second), exit_code=0)
    assert reduction.summary.success is False
    assert reduction.summary.failure_class == "unknown"


def test_launch_reuse_resets_thread_and_remembered_items_without_changing_launch(
    driver: CodexDriver, tmp_path: Path
) -> None:
    request = LaunchRequest(
        root=tmp_path / "project with spaces",
        phase="build",
        prompt="fixture prompt",
        model=None,
        effort=None,
        timeout_seconds=123,
        session_dir=tmp_path / "session",
    )
    first_launch = driver.build_launch(request)
    decode_record(driver, {"type": "thread.started", "thread_id": "old-thread"})
    item = {
        "type": "item.completed",
        "item": {
            "id": "item_replay",
            "type": "agent_message",
            "text": "Replayed example",
        },
    }
    old_item = decode_record(driver, item)
    second_launch = driver.build_launch(request)
    assert second_launch.argv == first_launch.argv
    assert second_launch.env == first_launch.env
    assert second_launch.cwd == first_launch.cwd
    assert second_launch.raw_format == first_launch.raw_format
    turn = decode_record(driver, {"type": "turn.started"})
    assert_identity(turn[0], None)
    started = decode_record(
        driver, {"type": "thread.started", "thread_id": "new-thread"}
    )
    replayed = decode_record(driver, item)
    assert len(old_item) == len(replayed) == 1
    assert replayed[0].type == "activity.message"
    assert replayed[0].payload["text"] == "Replayed example"
    assert_identity(replayed[0], "new-thread")
    assert_identity(started[0], "new-thread")
