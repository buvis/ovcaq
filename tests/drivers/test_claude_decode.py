from __future__ import annotations

import gc
import hashlib
import json
import sys
import tracemalloc
from collections.abc import Mapping
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.drivers.claude_events import record_timestamp
from ovcaq.events import (
    PROTOCOL_VERSION,
    Observation,
    ObservationType,
    Usage,
    observation_record,
    reduce_session,
)

CLAUDE_FIXTURES = Path(__file__).parents[1] / "fixtures" / "claude" / "v1"


@pytest.fixture
def settings() -> AgentSettings:
    return AgentSettings(
        name="claude",
        command=(sys.executable, "--literal-wrapper-argument"),
        tiers={"standard": "provider-primary", "backup": "provider-backup"},
        environment={"WARDEN_UNATTENDED": "1"},
        options={"permission_mode": "auto"},
    )


@pytest.fixture
def decoder(settings: AgentSettings) -> ClaudeDriver:
    return ClaudeDriver(settings, run_id="run-7")


def decode_record(driver: ClaudeDriver, record: object) -> tuple[Observation, ...]:
    observations = driver.decode(
        record if isinstance(record, str) else json.dumps(record)
    )
    assert isinstance(observations, tuple)
    assert observations
    for observation in observations:
        assert observation.protocol_version == PROTOCOL_VERSION
        assert observation.provider == "claude"
        assert observation.run_id == "run-7"
        assert observation.timestamp.utcoffset() == UTC.utcoffset(None)
        json.dumps(observation_record(observation), allow_nan=False)
    return observations


def message_usage(driver: ClaudeDriver, identity: str, count: int) -> Observation:
    counters = {
        "input_tokens": count,
        "output_tokens": count * 2,
        "cache_creation_input_tokens": count * 3,
        "cache_read_input_tokens": count * 4,
    }
    observations = decode_record(
        driver,
        {
            "type": "assistant",
            "session_id": "s1",
            "message": {"id": identity, "content": [], "usage": counters},
        },
    )
    usage = tuple(o for o in observations if o.type == ObservationType.USAGE_UPDATED)
    assert len(usage) == 1
    assert usage[0].payload["identity"] == f"message:{identity}"
    return usage[0]


def terminal_error(driver: ClaudeDriver, detail: object) -> tuple[Observation, ...]:
    return decode_record(
        driver,
        '{"type":"result","subtype":"error","is_error":true,"session_id":"s1",'
        f'"result":{json.dumps(detail)}}}',
    )


def test_init_maps_metadata_and_retains_session_for_later_activity(
    decoder: ClaudeDriver,
) -> None:
    (started,) = decode_record(
        decoder,
        '{"type":"system","subtype":"init","session_id":"s1",'
        '"model":"claude-test","claude_code_version":"2.1.208",'
        '"permissionMode":"auto","native_blob":{"internal":"omit-me"}}',
    )
    assert started.type == ObservationType.SESSION_STARTED
    assert started.session_id == "s1"
    assert started.lane_id is None
    assert dict(started.payload) == {
        "model": "claude-test",
        "permission_mode": "auto",
        "version": "2.1.208",
    }
    (activity,) = decode_record(
        decoder,
        {
            "type": "assistant",
            "parent_tool_use_id": "parent-1",
            "message": {"id": "m1", "content": [{"type": "text", "text": "hello"}]},
        },
    )
    assert activity.session_id == "s1"
    assert activity.lane_id == "parent-1"
    assert activity.type == ObservationType.ACTIVITY_MESSAGE
    assert dict(activity.payload) == {
        "kind": "text",
        "text": "hello",
        "message_id": "m1",
    }


@pytest.mark.parametrize("timestamp", (None, {}, [], "not-a-date", 1e300))
def test_message_preserves_valid_blocks_despite_bad_blocks_and_timestamps(
    decoder: ClaudeDriver,
    timestamp: object,
) -> None:
    observations = decode_record(
        decoder,
        '{"type":"assistant","session_id":"s1","parent_tool_use_id":"lane-1",'
        f'"timestamp":{json.dumps(timestamp)},'
        '"message":{"id":"m1","content":[null,3,{"type":"text","text":{}},'
        '{"type":"text","text":"hello"},'
        '{"type":"thinking","thinking":"reason"},'
        '{"type":"tool_use","id":"tu1","name":"Read",'
        '"input":{"file_path":"native-input-must-disappear"}}]}}',
    )
    assert [o.type for o in observations] == [
        ObservationType.ACTIVITY_MESSAGE,
        ObservationType.ACTIVITY_MESSAGE,
        ObservationType.TOOL_STARTED,
    ]
    assert [dict(o.payload) for o in observations] == [
        {"kind": "text", "text": "hello", "message_id": "m1"},
        {"kind": "thinking", "text": "reason", "message_id": "m1"},
        {"tool_id": "tu1", "name": "Read", "message_id": "m1"},
    ]
    assert {o.session_id for o in observations} == {"s1"}
    assert {o.lane_id for o in observations} == {"lane-1"}


@pytest.mark.parametrize("is_error", (False, True))
@pytest.mark.parametrize(
    ("content", "detail"),
    (
        ({"content": "done password=private-value"}, "done password=[REDACTED]"),
        (
            {
                "content": [
                    {"type": "text", "text": "first"},
                    None,
                    {"type": "text", "text": 7},
                    {"type": "text", "text": "password=private-value"},
                ]
            },
            "first password=[REDACTED]",
        ),
        ({}, ""),
        ({"content": "password=private-value " + "x" * 5000}, None),
    ),
)
def test_tool_results_map_outcome_and_sanitize_details(
    decoder: ClaudeDriver,
    is_error: bool,
    content: dict[str, object],
    detail: str | None,
) -> None:
    (observation,) = decode_record(
        decoder,
        {
            "type": "user",
            "session_id": "s1",
            "parent_tool_use_id": "lane-1",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tu1",
                        "is_error": is_error,
                        **content,
                    }
                ]
            },
        },
    )
    assert observation.type == (
        ObservationType.TOOL_FAILED if is_error else ObservationType.TOOL_COMPLETED
    )
    assert observation.session_id == "s1"
    assert observation.lane_id == "lane-1"
    assert set(observation.payload) == {"tool_id", "detail"}
    assert observation.payload["tool_id"] == "tu1"
    assert "private-value" not in observation.payload["detail"]
    assert len(observation.payload["detail"]) <= 4096
    if detail is not None:
        assert observation.payload["detail"] == detail
    else:
        assert observation.payload["detail"].startswith("password=[REDACTED] ")


@pytest.mark.parametrize(
    ("subtype", "fields", "kind", "payload"),
    (
        (
            "task_started",
            (
                '{"tool_use_id":"tu1","description":"job",'
                '"task_type":"local_agent","subagent_type":"Explore"}'
            ),
            ObservationType.LANE_STARTED,
            (
                '{"task_id":"t1","tool_id":"tu1","description":"job",'
                '"task_type":"local_agent","subagent_type":"Explore"}'
            ),
        ),
        (
            "task_progress",
            (
                '{"description":"reading","last_tool_name":"Read",'
                '"usage":{"tool_uses":2,"total_tokens":12,"duration_ms":40}}'
            ),
            ObservationType.LANE_PROGRESS,
            (
                '{"task_id":"t1","description":"reading","last_tool_name":"Read",'
                '"tool_uses":2,"total_tokens":12,"duration_ms":40}'
            ),
        ),
        (
            "task_notification",
            '{"status":"completed"}',
            ObservationType.LANE_COMPLETED,
            '{"task_id":"t1","status":"completed"}',
        ),
        (
            "task_notification",
            '{"status":"failed"}',
            ObservationType.LANE_FAILED,
            '{"task_id":"t1","status":"failed"}',
        ),
        (
            "task_updated",
            '{"patch":{"status":"stopped"}}',
            ObservationType.LANE_FAILED,
            '{"task_id":"t1","status":"stopped"}',
        ),
    ),
)
def test_task_records_map_to_lanes_with_projected_payloads(
    decoder: ClaudeDriver,
    subtype: str,
    fields: str,
    kind: ObservationType,
    payload: str,
) -> None:
    observations = decode_record(
        decoder,
        {
            "type": "system",
            "subtype": subtype,
            "session_id": "s1",
            "task_id": "t1",
            "parent_tool_use_id": "fallback",
            **json.loads(fields),
        },
    )
    lane = tuple(o for o in observations if o.type == kind)
    assert len(lane) == 1
    assert lane[0].lane_id == "t1"
    assert lane[0].session_id == "s1"
    assert dict(lane[0].payload) == json.loads(payload)


def test_background_snapshot_skips_invalid_entries_and_projects_valid_tasks(
    decoder: ClaudeDriver,
) -> None:
    (observation,) = decode_record(
        decoder,
        '{"type":"system","subtype":"background_tasks_changed",'
        '"tasks":[null,4,{"task_id":null},{"task_id":"b1","description":"job",'
        '"task_type":"local_bash","status":"running",'
        '"native_blob":{"private":"do-not-copy"}}]}',
    )
    assert observation.type == ObservationType.LANE_PROGRESS
    assert observation.lane_id == "b1"
    assert dict(observation.payload) == {
        "task_id": "b1",
        "description": "job",
        "task_type": "local_bash",
        "status": "running",
    }


def test_usage_replays_replace_contributions_without_double_counting_or_regression(
    decoder: ClaudeDriver,
) -> None:
    snapshots = [
        message_usage(decoder, identity, count)
        for identity, count in (
            ("m1", 2),
            ("m1", 2),
            ("m2", 3),
            ("m1", 4),
            ("m1", 1),
        )
    ]
    for snapshot, count in zip(snapshots, (2, 2, 5, 7, 7), strict=True):
        usage = snapshot.payload["usage"]
        assert isinstance(usage, Mapping)
        assert usage["input_tokens"] == count
        assert usage["output_tokens"] == count * 2
        assert usage["cache_creation_input_tokens"] == count * 3
        assert usage["cache_read_input_tokens"] == count * 4
        assert usage["estimated"] is True


def test_message_usage_memory_plateaus_and_evicted_replays_do_not_add_usage(
    decoder: ClaudeDriver,
) -> None:
    tracemalloc.start()
    try:
        retained = []
        for batch in range(4):
            for index in range(batch * 8192, (batch + 1) * 8192):
                decoder.decode(
                    '{"type":"assistant","session_id":"s1","message":'
                    f'{{"id":"m{index:08d}","content":[],"usage":'
                    '{"input_tokens":1,"output_tokens":2}}}'
                )
            gc.collect()
            retained.append(tracemalloc.get_traced_memory()[0])
        # Allow allocator/cache noise after twice the 4096-entry bound is warm.
        assert retained[-1] - retained[0] < 1024 * 1024, retained
    finally:
        tracemalloc.stop()
    replay = message_usage(decoder, "m00000000", 1)
    assert replay.payload["usage"]["input_tokens"] == 32768
    assert replay.payload["usage"]["output_tokens"] == 65536


@pytest.mark.parametrize(
    ("subtype", "is_error", "terminal"),
    (
        ("success", False, ObservationType.SESSION_COMPLETED),
        ("error", True, ObservationType.SESSION_FAILED),
    ),
)
def test_result_emits_exact_cumulative_usage_immediately_before_terminal(
    decoder: ClaudeDriver,
    subtype: str,
    is_error: bool,
    terminal: ObservationType,
) -> None:
    message = message_usage(decoder, "m1", 2)
    observations = decode_record(
        decoder,
        {
            "type": "result",
            "subtype": subtype,
            "is_error": is_error,
            "session_id": "s1",
            "result": "finished",
            "total_cost_usd": 1.25,
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20,
                "cache_creation_input_tokens": 3,
                "cache_read_input_tokens": 4,
            },
        },
    )
    assert [o.type for o in observations] == [ObservationType.USAGE_UPDATED, terminal]
    expected = asdict(
        Usage(
            input_tokens=10,
            output_tokens=20,
            cache_creation_input_tokens=3,
            cache_read_input_tokens=4,
            cost_usd=1.25,
        )
    )
    assert dict(observations[0].payload) == {
        "identity": "result:s1",
        "usage": expected,
    }
    assert observations[-1].session_id == "s1"
    assert decoder.summarize(iter(observations), 0).usage == Usage(**expected)
    reduced = reduce_session((message, *observations), 0).summary.usage
    assert reduced == replace(
        Usage(**expected),
        cache_creation_input_tokens=6,
        cache_read_input_tokens=8,
        estimated=True,
    )
    if not is_error:
        assert dict(observations[-1].payload) == {"usage": expected}


@pytest.mark.parametrize(
    ("status", "kind"),
    (
        ("rejected", ObservationType.RATE_LIMIT_STARTED),
        ("allowed_warning", ObservationType.ACTIVITY_MESSAGE),
        ("allowed", ObservationType.RATE_LIMIT_CLEARED),
    ),
)
@pytest.mark.parametrize(
    ("reset", "expected"),
    (
        (4102444800, "2100-01-01T00:00:00Z"),
        (1, None),
        ("4102444800", None),
        (True, None),
        (None, None),
    ),
)
@pytest.mark.parametrize("limit_type", ("five_hour", "seven_day"))
def test_rate_limit_status_and_explicit_future_numeric_resets_are_normalized(
    decoder: ClaudeDriver,
    status: str,
    kind: ObservationType,
    reset: object,
    expected: str | None,
    limit_type: str,
) -> None:
    observations = decode_record(
        decoder,
        {
            "type": "rate_limit_event",
            "session_id": "s1",
            "rate_limit_info": {
                "status": status,
                "resetsAt": reset,
                "rateLimitType": limit_type,
            },
        },
    )
    rate = tuple(o for o in observations if o.type == kind)
    assert len(rate) == 1
    assert rate[0].session_id == "s1"
    assert isinstance(rate[0].payload["detail"], str)
    assert limit_type in rate[0].payload["detail"]
    assert status in rate[0].payload["detail"]
    assert rate[0].payload["window"] == limit_type
    if kind == ObservationType.RATE_LIMIT_STARTED:
        assert set(rate[0].payload) == {"reset_at", "window", "detail"}
        assert rate[0].payload["reset_at"] == expected
    elif kind == ObservationType.ACTIVITY_MESSAGE:
        assert set(rate[0].payload) == {"kind", "window", "reset_at", "detail"}
        assert rate[0].payload["kind"] == "rate_limit_warning"
        assert rate[0].payload["reset_at"] == expected
        assert not any(
            o.type == ObservationType.RATE_LIMIT_CLEARED for o in observations
        )
    else:
        assert set(rate[0].payload) == {"window", "detail"}
    if status == "rejected":
        assert decoder.summarize(observations, 1).failure_class == "rate_limit"
    else:
        assert not any(
            o.type == ObservationType.RATE_LIMIT_STARTED for o in observations
        )
        failed = terminal_error(decoder, "provider execution failed")
        summary = decoder.summarize((*observations, *failed), 1)
        assert summary.failure_class == "agent"
        assert summary.rate_limit_reset_at is None


@pytest.mark.parametrize(
    ("detail", "failure_class"),
    (
        ("Permission denied", "permission"),
        ("operation not permitted", "permission"),
        ("Authentication failed", "authentication"),
        ("UNAUTHORIZED", "authentication"),
        ("invalid api key", "authentication"),
        ("You've hit your session limit", "rate_limit"),
        ("You've hit your usage limit", "rate_limit"),
        ("You've hit your weekly limit", "rate_limit"),
        ("usage limit reached", "rate_limit"),
        ("getaddrinfo ENOTFOUND api.example.test", "connectivity"),
        ("DNS lookup failed", "connectivity"),
        ("socket hang up", "connectivity"),
        ("connection refused", "connectivity"),
        ("connection reset", "connectivity"),
        ("API unavailable", "connectivity"),
        ("request timed out", "timeout"),
        ("request timeout", "timeout"),
        ("provider execution failed", "agent"),
    ),
)
def test_terminal_error_classifies_evidence_and_bounds_sanitized_detail(
    decoder: ClaudeDriver,
    detail: str,
    failure_class: str,
) -> None:
    observations = terminal_error(
        decoder, detail + " password=secret-value " + "x" * 5000
    )
    failure = observations[-1]
    assert failure.type == ObservationType.SESSION_FAILED
    assert set(failure.payload) == {"failure_class", "detail"}
    assert failure.payload["failure_class"] == failure_class
    assert failure.payload["detail"].startswith(detail)
    assert "secret-value" not in failure.payload["detail"]
    assert "[REDACTED]" in failure.payload["detail"]
    assert len(failure.payload["detail"]) <= 4096
    summary = decoder.summarize(iter(observations), 0)
    assert summary.failure_class == failure_class
    assert summary.success is False


@pytest.mark.parametrize(
    "detail",
    (
        "You've hit your usage limit; resets soon",
        "You've hit your usage limit; resets at 3pm",
        "You've hit your usage limit; resets 2100-01-01T00:00:00",
        "You've hit your usage limit; resets 2100-99-99T00:00:00Z",
        "You've hit your usage limit; resets 2000-01-01T00:00:00Z",
    ),
)
def test_vague_unqualified_and_past_reset_prose_never_schedules_retry(
    decoder: ClaudeDriver,
    detail: str,
) -> None:
    observations = terminal_error(decoder, detail)
    summary = decoder.summarize(observations, 1)
    assert summary.failure_class == "rate_limit"
    assert summary.rate_limit_reset_at is None


@pytest.mark.parametrize(
    "raw_line",
    (
        "",
        "{broken",
        "null",
        "[]",
        "1",
        '"text"',
        '{"type":"not-known","password":"hidden-secret"}',
        '{"type":"assistant","message":null}',
        '{"type":"assistant","message":{"content":[null,4,{}]}}',
        '{"type":"system","subtype":"background_tasks_changed","tasks":[null,{}]}',
        "password=hidden-secret " + "x" * 2000,
    ),
)
def test_undecodable_input_yields_exactly_one_sanitized_bounded_unknown(
    decoder: ClaudeDriver,
    raw_line: str,
) -> None:
    observations = decoder.decode(raw_line)
    assert isinstance(observations, tuple)
    assert len(observations) == 1
    observation = observations[0]
    assert observation.type == ObservationType.RAW_UNKNOWN
    assert set(observation.payload) == {"reason", "raw_sha256", "preview"}
    assert observation.payload["reason"]
    assert (
        observation.payload["raw_sha256"]
        == hashlib.sha256(raw_line.encode()).hexdigest()
    )
    assert len(observation.payload["preview"]) <= 512
    assert "hidden-secret" not in observation.payload["preview"]


@pytest.mark.parametrize("detail", (None, {}, [], 42))
def test_malformed_terminal_evidence_is_an_unknown_failure(
    decoder: ClaudeDriver,
    detail: object,
) -> None:
    observations = terminal_error(decoder, detail)
    assert observations[-1].type == ObservationType.SESSION_FAILED
    assert observations[-1].payload["failure_class"] == "unknown"
    assert decoder.summarize(observations, 1).failure_class == "unknown"


@pytest.mark.parametrize(
    ("reset", "expected"),
    (
        ("2100-01-01T00:00:00Z", "2100-01-01T00:00:00Z"),
        ("2100-01-01T02:00:00+02:00", "2100-01-01T00:00:00Z"),
        ("2097-06-15T18:42:09Z", "2097-06-15T18:42:09Z"),
        ("2099-12-31T23:45:17-03:30", "2100-01-01T03:15:17Z"),
        ("2104-03-01T00:15:23+05:45", "2104-02-29T18:30:23Z"),
        ("2112-08-19T08:12:34-07:00", "2112-08-19T15:12:34Z"),
    ),
)
def test_terminal_limit_banner_preserves_credible_future_reset(
    decoder: ClaudeDriver, reset: str, expected: str
) -> None:
    observations = terminal_error(
        decoder, f"You've hit your usage limit; resets {reset}"
    )
    limits = [o for o in observations if o.type == ObservationType.RATE_LIMIT_STARTED]
    assert len(limits) == 1
    assert limits[0].payload["reset_at"] == expected
    summary = decoder.summarize(observations, 1)
    assert summary.failure_class == "rate_limit"
    assert summary.rate_limit_reset_at == datetime.fromisoformat(expected)


def test_valid_json_with_literal_replacement_character_remains_decodable(
    decoder: ClaudeDriver,
) -> None:
    (started,) = decode_record(
        decoder,
        '{"type":"system","subtype":"init","session_id":"s1","model":"bad\ufffd"}',
    )
    assert started.type == ObservationType.SESSION_STARTED
    assert started.session_id == "s1"
    assert started.payload["model"] == "bad\ufffd"


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    (
        ("2026-09-27T14:30:00+02:00", datetime(2026, 9, 27, 12, 30, tzinfo=UTC)),
        ("2026-09-27T14:30:00", datetime(2026, 9, 28, tzinfo=UTC)),
    ),
)
def test_record_timestamp_normalizes_offsets_and_rejects_naive_time(
    timestamp: str, expected: datetime
) -> None:
    actual = record_timestamp(
        {"timestamp": timestamp}, datetime(2026, 9, 28, tzinfo=UTC)
    )
    assert actual == expected
    assert actual.tzinfo == UTC


def test_terminal_usage_does_not_fill_unreported_counters_from_messages(
    decoder: ClaudeDriver,
) -> None:
    message = message_usage(decoder, "m1", 2)
    observations = decode_record(
        decoder,
        {
            "type": "result",
            "subtype": "success",
            "session_id": "s1",
            "usage": {"input_tokens": 1},
            "total_cost_usd": 0.5,
        },
    )
    assert observations[0].payload["usage"] == asdict(
        Usage(input_tokens=1, cost_usd=0.5)
    )
    for sequence in ((message, *observations), (*observations, message)):
        assert reduce_session(sequence, 0).summary.usage == Usage(
            input_tokens=2,
            output_tokens=4,
            cache_creation_input_tokens=6,
            cache_read_input_tokens=8,
            cost_usd=0.5,
            estimated=True,
        )


def test_allowed_status_clears_previous_live_limit(decoder: ClaudeDriver) -> None:
    observations = tuple(
        observation
        for status in ("rejected", "allowed")
        for observation in decode_record(
            decoder,
            {
                "type": "rate_limit_event",
                "session_id": "s1",
                "rate_limit_info": {
                    "status": status,
                    "resetsAt": 4102444800,
                    "rateLimitType": "five_hour",
                },
            },
        )
    )
    summary = decoder.summarize(
        (*observations, *terminal_error(decoder, "provider execution failed")), 1
    )
    assert summary.failure_class == "agent"
    assert summary.rate_limit_reset_at is None


def test_versioned_healthy_fixture_covers_required_claude_records(
    settings: AgentSettings,
) -> None:
    driver = ClaudeDriver(settings, run_id="fixture-run")
    observations = tuple(
        observation
        for raw_line in (CLAUDE_FIXTURES / "healthy.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        for observation in driver.decode(raw_line)
    )

    assert [observation.type for observation in observations] == [
        ObservationType.SESSION_STARTED,
        ObservationType.ACTIVITY_MESSAGE,
        ObservationType.ACTIVITY_MESSAGE,
        ObservationType.TOOL_STARTED,
        ObservationType.USAGE_UPDATED,
        ObservationType.TOOL_COMPLETED,
        ObservationType.LANE_STARTED,
        ObservationType.LANE_PROGRESS,
        ObservationType.LANE_COMPLETED,
        ObservationType.LANE_PROGRESS,
        ObservationType.RATE_LIMIT_CLEARED,
        ObservationType.USAGE_UPDATED,
        ObservationType.SESSION_COMPLETED,
    ]
    assert {observation.lane_id for observation in observations} >= {
        "lane-parent",
        "lane-1",
        "background-1",
    }
    summary = driver.summarize(observations, 0)
    assert summary.success is True
    assert summary.session_id == "fixture-session"
    assert summary.failure_class is None
    assert summary.usage == Usage(
        input_tokens=12,
        output_tokens=5,
        cache_creation_input_tokens=2,
        cache_read_input_tokens=3,
        cost_usd=0.25,
    )


def test_versioned_failure_fixture_covers_failure_and_rate_limit_matrix(
    settings: AgentSettings,
) -> None:
    raw_lines = (
        (CLAUDE_FIXTURES / "failures.jsonl").read_text(encoding="utf-8").splitlines()
    )
    expected = (
        ("connectivity", None),
        ("authentication", None),
        ("permission", None),
        ("timeout", None),
        ("agent", None),
        ("rate_limit", None),
        ("rate_limit", datetime(2100, 1, 1, tzinfo=UTC)),
        ("rate_limit", datetime(2099, 6, 1, 18, 10, tzinfo=UTC)),
    )

    for index, (raw_line, (failure_class, reset_at)) in enumerate(
        zip(raw_lines, expected, strict=True)
    ):
        driver = ClaudeDriver(settings, run_id=f"fixture-failure-{index}")
        observations = driver.decode(raw_line)
        summary = driver.summarize(observations, 1)
        assert summary.success is False
        assert summary.failure_class == failure_class
        assert summary.rate_limit_reset_at == reset_at


def test_versioned_malformed_fixture_is_total_sanitized_and_bounded(
    settings: AgentSettings,
) -> None:
    driver = ClaudeDriver(settings, run_id="fixture-malformed")
    raw_lines = (
        (CLAUDE_FIXTURES / "malformed.jsonl").read_text(encoding="utf-8").splitlines()
    )

    observations = tuple(driver.decode(raw_line) for raw_line in raw_lines)

    assert all(len(decoded) == 1 for decoded in observations)
    assert all(
        decoded[0].type == ObservationType.RAW_UNKNOWN for decoded in observations
    )
    records = json.dumps([observation_record(decoded[0]) for decoded in observations])
    assert "sanitized-secret" not in records
    assert all(len(decoded[0].payload["preview"]) <= 512 for decoded in observations)
