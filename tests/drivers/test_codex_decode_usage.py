import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import LaunchRequest
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import Observation
from ovcaq.events.reducer import reduce_session

NATIVE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)


@pytest.fixture
def driver() -> CodexDriver:
    settings = AgentSettings(
        name="codex",
        command=("fixture-wrapper", "--literal-prefix", "fixture-launcher"),
        tiers={"standard": "fixture-model", "premium": "fixture-large"},
        environment={"TASK_MODE": "fixture"},
        options={},
    )
    return CodexDriver(settings, run_id="usage-run")


def native_usage(
    input_tokens: int = 120,
    cached_input_tokens: int = 100,
    cache_write_input_tokens: int = 0,
    output_tokens: int = 30,
    reasoning_output_tokens: int = 10,
) -> dict[str, object]:
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "cache_write_input_tokens": cache_write_input_tokens,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": reasoning_output_tokens,
    }


def expected_usage(
    input_tokens: int | None = 20,
    output_tokens: int | None = 30,
    cache_creation_input_tokens: int | None = 0,
    cache_read_input_tokens: int | None = 100,
    estimated: bool = False,
) -> dict[str, object]:
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_creation_input_tokens": cache_creation_input_tokens,
        "cache_read_input_tokens": cache_read_input_tokens,
        "tool_uses": None,
        "cost_usd": None,
        "estimated": estimated,
    }


def decode_record(
    driver: CodexDriver, record: dict[str, object], session_id: str | None
) -> tuple[str, tuple[Observation, ...]]:
    raw = json.dumps(record)
    before = datetime.now(UTC)
    observations = driver.decode(raw)
    after = datetime.now(UTC)
    assert observations
    for observation in observations:
        assert observation.protocol_version == 1
        assert observation.provider == "codex"
        assert observation.run_id == "usage-run"
        assert observation.session_id == session_id
        assert observation.timestamp.utcoffset() == timedelta(0)
        assert before <= observation.timestamp <= after
    return raw, observations


def start_thread(driver: CodexDriver, thread_id: str = "usage-thread") -> None:
    decode_record(driver, {"type": "thread.started", "thread_id": thread_id}, thread_id)


def complete(
    driver: CodexDriver,
    usage: object,
    session_id: str | None = "usage-thread",
) -> tuple[str, tuple[Observation, ...]]:
    return decode_record(driver, {"type": "turn.completed", "usage": usage}, session_id)


def assert_snapshot(
    observations: tuple[Observation, ...],
    expected: Mapping[str, object],
    identity: str = "thread:usage-thread",
) -> None:
    updated = [item for item in observations if item.type == "usage.updated"]
    terminal = [item for item in observations if item.type == "session.completed"]
    assert len(updated) == len(terminal) == 1
    assert updated[0].lane_id is None
    assert set(updated[0].payload) == {"usage", "identity"}
    assert updated[0].payload["identity"] == identity
    usage = updated[0].payload["usage"]
    assert isinstance(usage, Mapping)
    assert dict(usage) == dict(expected)
    if "usage" in terminal[0].payload:
        terminal_usage = terminal[0].payload["usage"]
        assert isinstance(terminal_usage, Mapping)
        assert dict(terminal_usage) == dict(expected)


def assert_unknown(raw: str, observations: tuple[Observation, ...]) -> None:
    unknown = [item for item in observations if item.type == "raw.unknown"]
    assert unknown
    for observation in unknown:
        payload = observation.payload
        assert set(payload) == {"reason", "raw_sha256", "preview"}
        assert isinstance(payload["reason"], str)
        assert payload["reason"]
        assert payload["raw_sha256"] == hashlib.sha256(raw.encode()).hexdigest()
        assert isinstance(payload["preview"], str)
        assert len(payload["preview"]) <= 512


@pytest.mark.parametrize(
    ("inclusive", "cached", "output", "uncached"),
    [(120, 100, 30, 20), (100, 0, 30, 100), (100, 100, 0, 0), (0, 0, 1, 0)],
)
def test_explicit_zero_write_subtracts_cache_and_keeps_output_exact(
    driver: CodexDriver, inclusive: int, cached: int, output: int, uncached: int
) -> None:
    start_thread(driver)
    _, observations = complete(driver, native_usage(inclusive, cached, 0, output, 0))
    assert_snapshot(observations, expected_usage(uncached, output, 0, cached))
    assert not any(item.type == "raw.unknown" for item in observations)


def test_reasoning_is_already_in_output_and_is_not_added_again(
    driver: CodexDriver,
) -> None:
    start_thread(driver)
    _, observations = complete(driver, native_usage(reasoning_output_tokens=17))
    assert_snapshot(observations, expected_usage())
    assert not any(item.type == "raw.unknown" for item in observations)


def test_adversarial_timestamp_extra_does_not_replace_receipt_time(
    driver: CodexDriver,
) -> None:
    start_thread(driver)
    _, observations = decode_record(
        driver,
        {
            "type": "turn.completed",
            "usage": native_usage(),
            "timestamp": "2000-01-01T00:00:00Z",
        },
        "usage-thread",
    )
    assert_snapshot(observations, expected_usage())


@pytest.mark.parametrize("explicit_start", [True, False])
@pytest.mark.parametrize(
    "totals",
    [(100, 200), (200, 100), (100, 200, 200), (200, 100, 200)],
    ids=["increasing", "out-of-order", "replayed", "replayed-out-of-order"],
)
def test_thread_totals_are_maxima_without_stable_turn_ids(
    driver: CodexDriver, explicit_start: bool, totals: tuple[int, ...]
) -> None:
    session_id = "usage-thread" if explicit_start else None
    identity = "thread:usage-thread" if explicit_start else "thread:unknown"
    if explicit_start:
        start_thread(driver)
    for total in totals:
        decode_record(driver, {"type": "turn.started"}, session_id)
        _, observations = complete(
            driver, native_usage(total, 0, 0, total // 10, 0), session_id
        )
    assert_snapshot(observations, expected_usage(200, 20, 0, 0), identity)
    assert not any(item.type == "raw.unknown" for item in observations)


def test_repeated_thread_start_does_not_clear_cumulative_usage(
    driver: CodexDriver,
) -> None:
    start_thread(driver)
    complete(driver, native_usage(200, 0, 0, 20, 0))
    start_thread(driver)
    _, observations = complete(driver, native_usage(100, 0, 0, 10, 0))
    assert_snapshot(observations, expected_usage(200, 20, 0, 0))


def test_each_normalized_field_has_its_own_maximum(
    driver: CodexDriver,
) -> None:
    start_thread(driver)
    complete(driver, native_usage(120, 100, 0, 30, 0))
    complete(driver, native_usage(200, 80, 0, 40, 0))
    _, observations = complete(driver, native_usage(160, 120, 0, 15, 0))
    assert_snapshot(observations, expected_usage(120, 40, 0, 120))
    assert not any(item.type == "raw.unknown" for item in observations)


def test_positive_write_exposes_native_cache_counts_and_partition_gap(
    driver: CodexDriver,
) -> None:
    start_thread(driver)
    raw, observations = complete(driver, native_usage(100, 20, 5, 25, 10))
    assert_snapshot(observations, expected_usage(None, 25, 5, 20, True))
    assert_unknown(raw, observations)


def test_cache_read_above_inclusive_input_is_unknown_without_clamping(
    driver: CodexDriver,
) -> None:
    start_thread(driver)
    raw, observations = complete(driver, native_usage(10, 20, 0, 30, 10))
    assert_snapshot(observations, expected_usage(None, 30, 0, 20))
    assert_unknown(raw, observations)


@pytest.mark.parametrize("field", NATIVE_FIELDS)
@pytest.mark.parametrize(
    "invalid",
    [True, False, -1, 1.0, float("nan"), float("inf"), "12", [], {}, None],
    ids=[
        "true",
        "false",
        "negative",
        "float",
        "nan",
        "inf",
        "text",
        "list",
        "map",
        "null",
    ],
)
def test_invalid_counter_is_rejected_individually_and_valid_counts_survive(
    driver: CodexDriver, field: str, invalid: object
) -> None:
    start_thread(driver)
    native = native_usage()
    native[field] = invalid
    expected = expected_usage()
    if field in NATIVE_FIELDS[:3]:
        expected["input_tokens"] = None
    if field == "cached_input_tokens":
        expected["cache_read_input_tokens"] = None
    if field == "cache_write_input_tokens":
        expected["cache_creation_input_tokens"] = None
    if field == "output_tokens":
        expected["output_tokens"] = None
    raw, observations = complete(driver, native)
    assert_snapshot(observations, expected)
    assert_unknown(raw, observations)


@pytest.mark.parametrize("field", NATIVE_FIELDS)
def test_omitted_counters_are_unknown_without_implicit_write_zero(
    driver: CodexDriver, field: str
) -> None:
    start_thread(driver)
    native = native_usage()
    del native[field]
    expected = expected_usage()
    if field in NATIVE_FIELDS[:3]:
        expected["input_tokens"] = None
    if field == "cached_input_tokens":
        expected["cache_read_input_tokens"] = None
    if field == "cache_write_input_tokens":
        expected["cache_creation_input_tokens"] = None
    if field == "output_tokens":
        expected["output_tokens"] = None
    raw, observations = complete(driver, native)
    assert_snapshot(observations, expected)
    if field in NATIVE_FIELDS[:3]:
        assert_unknown(raw, observations)


@pytest.mark.parametrize("usage", [None, [], "wrong-shape", 12, True])
def test_wrong_shaped_usage_returns_a_raw_gap_without_raising(
    driver: CodexDriver, usage: object
) -> None:
    start_thread(driver)
    raw, observations = complete(driver, usage)
    assert_unknown(raw, observations)


def test_missing_usage_object_returns_a_raw_gap_without_raising(
    driver: CodexDriver,
) -> None:
    start_thread(driver)
    raw, observations = decode_record(
        driver, {"type": "turn.completed"}, "usage-thread"
    )
    assert_unknown(raw, observations)


@pytest.mark.parametrize("native", [{}, native_usage(0, 0, 0, 0, 0)])
def test_absent_or_default_zero_telemetry_keeps_token_fields_unknown(
    driver: CodexDriver, native: dict[str, object]
) -> None:
    start_thread(driver)
    raw, observations = complete(driver, native)
    updated = [item for item in observations if item.type == "usage.updated"]
    assert len(updated) == 1
    usage = updated[0].payload["usage"]
    assert isinstance(usage, Mapping)
    assert isinstance(usage["estimated"], bool)
    expected = expected_usage(None, None, None, None)
    expected["estimated"] = usage["estimated"]
    assert_snapshot(observations, expected)
    assert_unknown(raw, observations)


def test_later_default_zero_snapshot_preserves_known_exact_maxima(
    driver: CodexDriver,
) -> None:
    start_thread(driver)
    complete(driver, native_usage())
    _, observations = complete(driver, native_usage(0, 0, 0, 0, 0))
    assert_snapshot(observations, expected_usage())


def test_default_zero_snapshot_does_not_prevent_later_exact_usage(
    driver: CodexDriver,
) -> None:
    start_thread(driver)
    complete(driver, native_usage(0, 0, 0, 0, 0))
    _, observations = complete(driver, native_usage())
    assert_snapshot(observations, expected_usage())
    assert not any(item.type == "raw.unknown" for item in observations)


def test_malformed_usage_preview_is_sanitized_and_bounded(
    driver: CodexDriver,
) -> None:
    start_thread(driver)
    credential = "sk-" + "SyntheticCredentialForDecoderTestOnly123456789012"
    native = native_usage()
    native["input_tokens"] = credential + " " + "x" * 1000
    raw, observations = complete(driver, native)
    assert_snapshot(observations, expected_usage(None))
    assert_unknown(raw, observations)
    for observation in observations:
        if observation.type == "raw.unknown":
            assert credential not in observation.payload["preview"]
            assert "[REDACTED]" in observation.payload["preview"]


@pytest.mark.parametrize("new_thread", [None, "second-thread"])
def test_build_launch_resets_identity_maxima_and_estimation_for_session_reuse(
    driver: CodexDriver, tmp_path: Path, new_thread: str | None
) -> None:
    start_thread(driver, "first-thread")
    complete(driver, native_usage(1000, 800, 5, 900, 0), "first-thread")
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    driver.build_launch(
        LaunchRequest(
            root=tmp_path,
            phase="build",
            prompt="Fixture-only launch construction.",
            model=None,
            effort=None,
            timeout_seconds=30,
            session_dir=session_dir,
        )
    )
    if new_thread is not None:
        start_thread(driver, new_thread)
    _, observations = complete(driver, native_usage(), new_thread)
    identity = "thread:unknown" if new_thread is None else f"thread:{new_thread}"
    assert_snapshot(observations, expected_usage(), identity)
    assert not any(item.type == "raw.unknown" for item in observations)


def test_conflicting_threads_remain_visible_and_reducer_fails_unknown(
    driver: CodexDriver,
) -> None:
    first_raw, first = decode_record(
        driver, {"type": "thread.started", "thread_id": "first"}, "first"
    )
    first_usage_raw, first_usage = complete(driver, native_usage(), "first")
    second_raw, second = decode_record(
        driver, {"type": "thread.started", "thread_id": "second"}, "second"
    )
    second_usage_raw, second_usage = complete(driver, native_usage(200), "second")
    updated = [item for item in second_usage if item.type == "usage.updated"]
    assert len(updated) == 1
    assert updated[0].payload["identity"] == "thread:second"
    records = (
        (first_raw, first),
        (first_usage_raw, first_usage),
        (second_raw, second),
        (second_usage_raw, second_usage),
    )
    gaps = [
        (raw, obs)
        for raw, obs in records
        if any(item.type == "raw.unknown" for item in obs)
    ]
    assert gaps
    for raw, observations in gaps:
        assert_unknown(raw, observations)
    summary = reduce_session((*first, *first_usage, *second, *second_usage), 0).summary
    assert summary.success is False
    assert summary.failure_class == "unknown"
