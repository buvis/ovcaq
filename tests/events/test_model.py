"""Public version-one observation contract, independent of agent drivers."""

import json
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from enum import StrEnum

import pytest

from ovcaq.events import (
    PROTOCOL_VERSION,
    FailureClass,
    Observation,
    ObservationType,
    SessionSummary,
    Usage,
    observation_from_record,
    observation_record,
    sanitize_json,
    sanitize_text,
    summary_record,
)

NOW = datetime(2026, 9, 26, 12, 30, 15, 123456, tzinfo=UTC)
COUNTERS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "tool_uses",
)
USAGE_DATA = dict.fromkeys(COUNTERS, 0) | {"cost_usd": 0.0, "estimated": False}
CLOSED_PAYLOADS = {
    "usage.updated": {"usage": USAGE_DATA, "identity": "request-1"},
    "session.failed": {"failure_class": "agent", "detail": "request failed"},
    "rate_limit.started": {
        "reset_at": "2026-09-26T13:00:00Z",
        "window": "five_hour",
        "detail": "wait",
    },
    "raw.unknown": {
        "reason": "unrecognized",
        "raw_sha256": "a" * 64,
        "preview": "data",
    },
}
CREDENTIAL_CASES = [
    ("password=other-secret", "password=[REDACTED]"),
    ("Authorization: Bearer Q7v-k9_42", "Authorization: Bearer [REDACTED]"),
    ("authorization: bearer mN8p23", "authorization: bearer [REDACTED]"),
    ("access_token=R4j-62_y", "access_token=[REDACTED]"),
    ("X-Secret: another-value", "X-Secret: [REDACTED]"),
    ("PASSWORD=Z8n4p2", "PASSWORD=[REDACTED]"),
    ("api_key: key-73_B", "api_key: [REDACTED]"),
    ("cookie=session-29", "cookie=[REDACTED]"),
    ("client_credential: c6D_8f", "client_credential: [REDACTED]"),
]


def make_observation(**changes):
    fields = {
        "protocol_version": 1,
        "timestamp": NOW,
        "provider": "test-driver",
        "run_id": "run-1",
        "session_id": "session-1",
        "lane_id": "lane-1",
        "type": ObservationType("activity.message"),
        "payload": {"message": "working"},
    }
    fields.update(changes)
    return Observation(**fields)


def make_summary(**changes):
    fields = {
        "success": False,
        "session_id": "session-1",
        "failure_class": FailureClass("agent"),
        "failure_detail": "request failed",
        "rate_limit_reset_at": None,
        "usage": None,
    }
    fields.update(changes)
    return SessionSummary(**fields)


def assert_ordinary_json(value):
    if type(value) is dict:
        assert all(type(key) is str for key in value)
        for child in value.values():
            assert_ordinary_json(child)
    elif type(value) is list:
        for child in value:
            assert_ordinary_json(child)
    else:
        assert type(value) in (str, int, float, bool, type(None))


def test_protocol_and_enums_expose_exact_version_one_values():
    assert type(PROTOCOL_VERSION) is int
    assert PROTOCOL_VERSION == 1
    assert issubclass(ObservationType, StrEnum)
    assert issubclass(FailureClass, StrEnum)
    assert {member.value for member in ObservationType} == {
        "session.started",
        "activity.message",
        "tool.started",
        "tool.completed",
        "tool.failed",
        "lane.started",
        "lane.progress",
        "lane.completed",
        "lane.failed",
        "usage.updated",
        "rate_limit.started",
        "rate_limit.cleared",
        "session.completed",
        "session.failed",
        "raw.unknown",
    }
    assert {member.value for member in FailureClass} == {
        "rate_limit",
        "connectivity",
        "permission",
        "authentication",
        "timeout",
        "agent",
        "unknown",
    }


@pytest.mark.parametrize(
    "instance,field,replacement",
    [
        (Usage(**USAGE_DATA), "input_tokens", 3),
        (make_observation(), "run_id", "other"),
        (make_summary(), "success", True),
    ],
)
def test_public_models_are_frozen_slotted_dataclasses(instance, field, replacement):
    assert is_dataclass(instance)
    assert not hasattr(instance, "__dict__")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        setattr(instance, field, replacement)


@pytest.mark.parametrize("value", [None, 0, 1, 10**12])
def test_usage_accepts_optional_nonnegative_integer_counters(value):
    usage = Usage(**dict.fromkeys(COUNTERS, value), cost_usd=None)
    assert all(getattr(usage, field) == value for field in COUNTERS)
    assert usage.cost_usd is None
    assert usage.estimated is False


@pytest.mark.parametrize("field", COUNTERS)
@pytest.mark.parametrize("value", [-1, True, False, 1.5, "1"])
def test_usage_rejects_invalid_counters(field, value):
    with pytest.raises((TypeError, ValueError)):
        Usage(**(USAGE_DATA | {field: value}))


@pytest.mark.parametrize("value", [0.0, 0.125, 1234.5])
def test_usage_accepts_nonnegative_finite_cost(value):
    usage = Usage(**(USAGE_DATA | {"cost_usd": value, "estimated": True}))
    assert usage.cost_usd == value
    assert usage.estimated is True


@pytest.mark.parametrize(
    "value", [-0.1, float("nan"), float("inf"), -float("inf"), True, "1"]
)
def test_usage_rejects_invalid_cost(value):
    with pytest.raises((TypeError, ValueError)):
        Usage(**(USAGE_DATA | {"cost_usd": value}))


@pytest.mark.parametrize("value", [None, 0, 1, "false"])
def test_usage_requires_boolean_estimation_flag(value):
    with pytest.raises((TypeError, ValueError)):
        Usage(**(USAGE_DATA | {"estimated": value}))


@pytest.mark.parametrize("version", [-1, 0, 2, 999, True, "1", None])
def test_observation_rejects_invalid_protocol_versions(version):
    with pytest.raises((TypeError, ValueError)):
        make_observation(protocol_version=version)


@pytest.mark.parametrize(
    "timestamp",
    [
        NOW.replace(tzinfo=None),
        NOW.astimezone(timezone(timedelta(hours=2))),
        NOW.astimezone(timezone(timedelta(hours=-3))),
        "2026-09-26T12:30:15Z",
        None,
    ],
)
def test_observation_rejects_timestamps_that_are_not_aware_utc(timestamp):
    with pytest.raises((TypeError, ValueError)):
        make_observation(timestamp=timestamp)


@pytest.mark.parametrize("field", ["provider", "run_id", "session_id", "lane_id"])
@pytest.mark.parametrize("value", ["", 7, False])
def test_observation_rejects_invalid_identifiers(field, value):
    with pytest.raises((TypeError, ValueError)):
        make_observation(**{field: value})


@pytest.mark.parametrize("field", ["provider", "run_id"])
def test_observation_requires_provider_and_run_id(field):
    with pytest.raises((TypeError, ValueError)):
        make_observation(**{field: None})


def test_observation_allows_absent_optional_identifiers():
    observation = make_observation(session_id=None, lane_id=None)
    assert observation.session_id is None
    assert observation.lane_id is None


@pytest.mark.parametrize("kind", [None, 1, "unrecognized.event"])
def test_observation_rejects_invalid_event_types(kind):
    with pytest.raises((TypeError, ValueError)):
        make_observation(type=kind)


def test_observation_payload_is_deeply_copied_and_immutable():
    original = {"items": [{"message": "original"}], "metadata": {"count": 1}}
    observation = make_observation(payload=original)
    original["items"][0]["message"] = "changed"
    original["items"].append({"message": "extra"})
    original["metadata"]["count"] = 2
    assert observation_record(observation)["payload"] == {
        "items": [{"message": "original"}],
        "metadata": {"count": 1},
    }
    with pytest.raises(TypeError):
        observation.payload["new"] = "value"
    with pytest.raises(TypeError):
        observation.payload["items"][0]["message"] = "changed"
    with pytest.raises((AttributeError, TypeError)):
        observation.payload["items"].append("extra")


@pytest.mark.parametrize(
    "key",
    [
        "access_token",
        "HEADER_AUTHORIZATION",
        "mySecret",
        "password",
        "api_key",
        "Cookie",
        "client_credential",
        "token_header",
    ],
)
def test_json_sanitization_redacts_sensitive_keys_recursively(key):
    source = {"nested": [{key: "sensitive-value", "message": "token budget exhausted"}]}
    result = sanitize_json(source)
    assert result == {
        "nested": [{key: "[REDACTED]", "message": "token budget exhausted"}]
    }


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Authorization: Bearer abc123", "Authorization: Bearer [REDACTED]"),
        ("authorization: bearer abc123", "authorization: bearer [REDACTED]"),
        ("access_token=abc123", "access_token=[REDACTED]"),
        ("X-Secret: abc123", "X-Secret: [REDACTED]"),
        ("PASSWORD=abc123", "PASSWORD=[REDACTED]"),
        ("api_key: abc123", "api_key: [REDACTED]"),
        ("cookie=abc123", "cookie=[REDACTED]"),
        ("client_credential: abc123", "client_credential: [REDACTED]"),
    ]
    + CREDENTIAL_CASES,
)
def test_text_sanitization_redacts_only_credential_values(text, expected):
    assert sanitize_text(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "token budget exhausted",
        "secret handshake",
        "password validation failed",
        "authorization denied",
        "cookie jar",
        "credential unavailable",
        "api_key field is absent",
        "Bearer harmless",
        "message=ordinary",
    ],
)
def test_text_sanitization_preserves_unassigned_harmless_prose(text):
    assert sanitize_text(text) == text


def test_observation_redacts_payload_before_exposing_it():
    observation = make_observation(payload={"nested": [{"API_KEY": "private"}]})
    assert observation.payload["nested"][0]["API_KEY"] == "[REDACTED]"
    assert observation_record(observation)["payload"] == {
        "nested": [{"API_KEY": "[REDACTED]"}],
    }


@pytest.mark.parametrize("text,expected", CREDENTIAL_CASES)
@pytest.mark.parametrize(
    "kind,field",
    [
        ("activity.message", "message"),
        ("session.failed", "detail"),
        ("rate_limit.started", "detail"),
        ("raw.unknown", "preview"),
    ],
)
def test_observation_redacts_varied_credentials_before_exposure(
    kind, field, text, expected
):
    payload = CLOSED_PAYLOADS.get(kind, {}) | {field: text}
    observation = make_observation(type=ObservationType(kind), payload=payload)
    assert observation.payload[field] == expected
    assert observation_record(observation)["payload"][field] == expected


@pytest.mark.parametrize("text,expected", CREDENTIAL_CASES)
def test_record_decoder_redacts_varied_credentials_in_nested_text(text, expected):
    record = observation_record(make_observation())
    record["payload"] = {"nested": [{"message": text}]}
    restored = observation_from_record(record)
    assert restored.payload["nested"][0]["message"] == expected
    assert observation_record(restored)["payload"] == {
        "nested": [{"message": expected}]
    }


@pytest.mark.parametrize("text,expected", CREDENTIAL_CASES)
def test_summary_redacts_varied_credentials_before_exposure(text, expected):
    summary = make_summary(failure_detail=text)
    assert summary.failure_detail == expected
    assert summary_record(summary)["failure_detail"] == expected


@pytest.mark.parametrize("kind,payload", CLOSED_PAYLOADS.items())
def test_closed_payloads_accept_their_required_shapes(kind, payload):
    observation = make_observation(type=ObservationType(kind), payload=payload)
    record = observation_record(observation)
    assert record["payload"] == payload
    assert observation_record(observation_from_record(record)) == record


@pytest.mark.parametrize("kind,payload", CLOSED_PAYLOADS.items())
def test_closed_payloads_reject_missing_and_extra_keys(kind, payload):
    invalid_payloads = [payload | {"unexpected": "value"}]
    invalid_payloads.extend(
        {k: v for k, v in payload.items() if k != missing} for missing in payload
    )
    for invalid in invalid_payloads:
        with pytest.raises((TypeError, ValueError)):
            make_observation(type=ObservationType(kind), payload=invalid)


@pytest.mark.parametrize(
    "kind,field,value",
    [
        ("usage.updated", "usage", "usage"),
        ("usage.updated", "usage", None),
        ("usage.updated", "identity", 1),
        ("usage.updated", "identity", {}),
        ("session.failed", "failure_class", "unrecognized"),
        ("session.failed", "failure_class", None),
        ("session.failed", "detail", None),
        ("session.failed", "detail", 1),
        ("rate_limit.started", "detail", None),
        ("rate_limit.started", "reset_at", NOW),
        ("rate_limit.started", "reset_at", "tomorrow"),
        ("rate_limit.started", "reset_at", "2026-09-26T13:00:00+02:00"),
        ("raw.unknown", "reason", None),
        ("raw.unknown", "preview", []),
        ("raw.unknown", "raw_sha256", "a" * 63),
        ("raw.unknown", "raw_sha256", "a" * 65),
        ("raw.unknown", "raw_sha256", "A" * 64),
        ("raw.unknown", "raw_sha256", "g" * 64),
    ],
)
def test_closed_payloads_reject_invalid_value_types(kind, field, value):
    with pytest.raises((TypeError, ValueError)):
        make_observation(
            type=ObservationType(kind), payload=CLOSED_PAYLOADS[kind] | {field: value}
        )


@pytest.mark.parametrize(
    "kind,field",
    [
        ("usage.updated", "identity"),
        ("rate_limit.started", "reset_at"),
    ],
)
def test_closed_payloads_allow_explicit_null_optional_values(kind, field):
    observation = make_observation(
        type=ObservationType(kind), payload=CLOSED_PAYLOADS[kind] | {field: None}
    )
    assert observation_record(observation)["payload"][field] is None


@pytest.mark.parametrize(
    "field,value",
    [("input_tokens", -1), ("output_tokens", True), ("cost_usd", float("inf"))],
)
def test_usage_payload_rejects_invalid_serialized_usage(field, value):
    payload = {"usage": USAGE_DATA | {field: value}, "identity": None}
    with pytest.raises((TypeError, ValueError)):
        make_observation(type=ObservationType("usage.updated"), payload=payload)


def test_unknown_preview_is_sanitized_then_hard_truncated():
    preview = "token=" + "s" * 700 + " " + "x" * 700
    observation = make_observation(
        type=ObservationType("raw.unknown"),
        payload=CLOSED_PAYLOADS["raw.unknown"] | {"preview": preview},
    )
    expected = ("token=[REDACTED] " + "x" * 700)[:512]
    assert observation.payload["preview"] == expected
    assert observation_record(observation)["payload"]["preview"] == expected


def test_failure_detail_is_sanitized_then_hard_truncated_at_construction():
    detail = "password=" + "s" * 5000 + " " + "x" * 5000
    summary = make_summary(failure_detail=detail)
    expected = ("password=[REDACTED] " + "x" * 5000)[:4096]
    assert summary.failure_detail == expected
    assert summary_record(summary)["failure_detail"] == expected


@pytest.mark.parametrize("length", [4095, 4096, 4097])
def test_failure_detail_preserves_text_through_the_length_limit(length):
    summary = make_summary(failure_detail="x" * length)
    assert summary.failure_detail == "x" * min(length, 4096)


@pytest.mark.parametrize("length", [511, 512, 513])
def test_unknown_preview_preserves_text_through_the_length_limit(length):
    observation = make_observation(
        type=ObservationType("raw.unknown"),
        payload=CLOSED_PAYLOADS["raw.unknown"] | {"preview": "x" * length},
    )
    assert observation.payload["preview"] == "x" * min(length, 512)


@pytest.mark.parametrize(
    "timestamp",
    [
        NOW.replace(tzinfo=None),
        NOW.astimezone(timezone(timedelta(hours=2))),
    ],
)
def test_summary_rejects_reset_times_that_are_not_aware_utc(timestamp):
    with pytest.raises((TypeError, ValueError)):
        make_summary(rate_limit_reset_at=timestamp)


def test_summary_exposes_optional_fields_and_serializes_usage():
    summary = make_summary(
        success=True,
        session_id=None,
        failure_class=None,
        failure_detail=None,
        usage=Usage(**USAGE_DATA),
        rate_limit_reset_at=NOW,
    )
    record = summary_record(summary)
    assert summary.success is True
    assert summary.session_id is None
    assert summary.failure_class is None
    assert summary.failure_detail is None
    assert record["success"] is True
    assert record["usage"] == USAGE_DATA
    assert datetime.fromisoformat(record["rate_limit_reset_at"]) == NOW
    assert_ordinary_json(record)
    assert json.dumps(record, allow_nan=False) == json.dumps(
        summary_record(summary), allow_nan=False
    )


def test_observation_records_round_trip_with_utc_timestamps_and_json_containers():
    observation = make_observation(
        payload={"items": [{"message": "hello"}], "count": 2}
    )
    record = observation_record(observation)
    assert_ordinary_json(record)
    assert record["protocol_version"] == 1
    assert record["type"] == "activity.message"
    assert record["provider"] == "test-driver"
    assert record["run_id"] == "run-1"
    assert record["session_id"] == "session-1"
    assert record["lane_id"] == "lane-1"
    assert "T" in record["timestamp"]
    assert record["timestamp"].endswith(("Z", "+00:00"))
    assert datetime.fromisoformat(record["timestamp"]) == NOW
    serialized = json.dumps(record, allow_nan=False)
    assert serialized == json.dumps(observation_record(observation), allow_nan=False)
    restored = observation_from_record(json.loads(serialized))
    assert restored.timestamp == NOW
    assert restored.type == observation.type
    assert observation_record(restored) == record


def test_mutating_serialized_records_does_not_mutate_observations():
    observation = make_observation(payload={"items": [{"message": "hello"}]})
    record = observation_record(observation)
    record["payload"]["items"][0]["message"] = "changed"
    assert observation_record(observation)["payload"] == {
        "items": [{"message": "hello"}]
    }


@pytest.mark.parametrize("version", [-1, 0, 2, 999, True, "1", None])
def test_record_decoder_rejects_unknown_or_invalid_versions(version):
    record = observation_record(make_observation())
    record["protocol_version"] = version
    with pytest.raises((TypeError, ValueError)):
        observation_from_record(record)


def test_record_decoder_redacts_sensitive_payloads():
    record = observation_record(make_observation())
    record["payload"] = {"nested": {"password": "private"}}
    restored = observation_from_record(record)
    assert restored.payload["nested"]["password"] == "[REDACTED]"
    assert "private" not in json.dumps(observation_record(restored))
