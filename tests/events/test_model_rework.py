from __future__ import annotations

import time
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

import pytest

from ovcaq.events import (
    Observation,
    ObservationType,
    Usage,
    observation_record,
    sanitize_json,
    sanitize_text,
)


@pytest.mark.parametrize(
    "text,expected",
    (
        ("Bearer Q7v-k9_42." + "mN8p23.R4j62y", "Bearer [REDACTED]"),
        ("bEaReR Q7v-k9_42" + "mN8p23R4j62y", "bEaReR [REDACTED]"),
        (
            "request used sk-synthetic_" + "Q7v-k9_42mN8p23R4j62y",
            "request used [REDACTED]",
        ),
        (
            "token sk-test-synthetic-" + "Q7v_k9-42mN8p23R4j62y",
            "token [REDACTED]",
        ),
    ),
)
def test_text_sanitization_redacts_bare_likely_secret_tokens(
    text: str, expected: str
) -> None:
    assert sanitize_text(text) == expected


@pytest.mark.parametrize(
    "text",
    (
        "Bearer harmless",
        "token budget exhausted after 42 requests",
        "authorization denied because the credential is unavailable",
        "cookie jar contains 3 entries",
    ),
)
def test_text_sanitization_preserves_harmless_prose(text: str) -> None:
    assert sanitize_text(text) == text


def test_usage_preserves_typed_numeric_counters_during_sanitization() -> None:
    usage = Usage(
        input_tokens=101,
        output_tokens=23,
        cache_creation_input_tokens=7,
        cache_read_input_tokens=11,
        tool_uses=3,
        cost_usd=0.125,
        estimated=False,
    )
    observation = Observation(
        protocol_version=1,
        timestamp=datetime(2026, 9, 26, tzinfo=UTC),
        provider="test-driver",
        run_id="run-1",
        session_id="session-1",
        lane_id=None,
        type=ObservationType("usage.updated"),
        payload={"usage": asdict(usage), "identity": "request-1"},
    )
    serialized = observation_record(observation)["payload"]["usage"]

    assert serialized == asdict(usage)
    assert type(serialized["input_tokens"]) is int
    assert type(serialized["cost_usd"]) is float
    assert type(serialized["estimated"]) is bool


def rate_limit_started(payload: dict[str, Any]) -> Observation:
    return Observation(
        protocol_version=1,
        timestamp=datetime(2026, 9, 26, tzinfo=UTC),
        provider="test-driver",
        run_id="run-1",
        session_id="session-1",
        lane_id=None,
        type=ObservationType.RATE_LIMIT_STARTED,
        payload=payload,
    )


@pytest.mark.parametrize("window", ("five_hour", "seven_day", None))
def test_rate_limit_started_carries_structured_window_label(
    window: str | None,
) -> None:
    payload = {"reset_at": "2100-01-01T00:00:00Z", "window": window, "detail": "wait"}
    observation = rate_limit_started(payload)
    assert observation.payload["window"] == window
    assert observation_record(observation)["payload"] == payload


@pytest.mark.parametrize(
    "payload",
    (
        {"reset_at": None, "detail": "wait"},
        {"reset_at": None, "window": None},
        {"window": None, "detail": "wait"},
        {"reset_at": None, "window": None, "detail": "wait", "extra": "x"},
    ),
)
def test_rate_limit_started_rejects_payload_without_exact_key_set(
    payload: dict[str, Any],
) -> None:
    with pytest.raises(ValueError):
        rate_limit_started(payload)


@pytest.mark.parametrize("window", (1, 1.5, True, ["five_hour"], {"w": "x"}))
def test_rate_limit_started_rejects_non_text_window(window: object) -> None:
    with pytest.raises(TypeError):
        rate_limit_started({"reset_at": None, "window": window, "detail": "wait"})


API_KEY_NAMES = (
    "api_key",
    "api-key",
    "apikey",
    "API_KEY",
    "x-api-key",
    "apiKey",
    "X-Api-Key",
)


@pytest.mark.parametrize("name", API_KEY_NAMES)
def test_text_sanitization_redacts_api_key_names_in_free_text(name: str) -> None:
    value = "synthetic-" + "Q7v9k42mN8p23R4j62y"
    assert sanitize_text(name + ": " + value) == name + ": [REDACTED]"


@pytest.mark.parametrize("name", ("apiKey", "x-api-key", "X-Api-Key"))
def test_text_sanitization_leaves_no_trace_of_quoted_api_key_value(name: str) -> None:
    value = "synthetic-" + "Q7v9k42mN8p23R4j62y"
    text = "request body " + '{"' + name + '": "' + value + '"} sent'
    assert value not in sanitize_text(text)


@pytest.mark.parametrize("name", ("apiKey", "x-api-key", "X-Api-Key"))
def test_json_sanitization_redacts_api_key_mapping_values(name: str) -> None:
    value = "synthetic-" + "Q7v9k42mN8p23R4j62y"
    result = sanitize_json({name: value, "note": "ordinary"})
    assert result == {name: "[REDACTED]", "note": "ordinary"}


@pytest.mark.parametrize(
    "text",
    ("the api key rotates weekly", "apiary keeper notes"),
)
def test_text_sanitization_preserves_prose_resembling_api_key(text: str) -> None:
    assert sanitize_text(text) == text


@pytest.mark.parametrize("name", ("apiKey", "x-api-key", "X-Api-Key"))
def test_observation_record_redacts_api_key_payload_values(name: str) -> None:
    value = "synthetic-" + "Q7v9k42mN8p23R4j62y"
    observation = Observation(
        protocol_version=1,
        timestamp=datetime(2026, 9, 26, tzinfo=UTC),
        provider="test-driver",
        run_id="run-1",
        session_id="session-1",
        lane_id=None,
        type=ObservationType.ACTIVITY_MESSAGE,
        payload={"message": "hello", name: value},
    )
    record = observation_record(observation)
    assert value not in repr(record)
    assert record["payload"][name] == "[REDACTED]"


@pytest.mark.parametrize("text", ("a" * 200_000, "token" * 40_000))
def test_text_sanitization_stays_linear_on_long_unbroken_runs(text: str) -> None:
    started = time.perf_counter()
    assert sanitize_text(text) == text
    assert time.perf_counter() - started < 1.0


@pytest.mark.parametrize(
    "key",
    ("x-api-key: ", "my_token=", "HTTP_AUTHORIZATION: Bearer ", '"apiKey": '),
)
def test_text_sanitization_redacts_values_behind_prefixed_key_names(key: str) -> None:
    value = "synthetic-" + "Q7v9k42mN8p23R4j62y"
    assert value not in sanitize_text("header " + key + value + " end")


@pytest.mark.parametrize("suffix", (10, 65, 1000))
def test_text_sanitization_redacts_assignment_with_long_sensitive_key(
    suffix: int,
) -> None:
    key = "token" + "x" * suffix
    assert sanitize_text(key + "=private-value") == key + "=[REDACTED]"


@pytest.mark.parametrize("key", ("authorization" + "x" * 1000, "token"))
def test_text_sanitization_keeps_bearer_scheme_and_redacts_its_value(key: str) -> None:
    assert sanitize_text(key + ": bearer abc") == key + ": bearer [REDACTED]"
