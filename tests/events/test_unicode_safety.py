"""Unicode scalar contracts for shared observations, independent of drivers."""

import json
from datetime import UTC, datetime
from typing import Any

import pytest

from ovcaq.events import (
    FailureClass,
    Observation,
    ObservationType,
    SessionSummary,
    observation_from_record,
    observation_record,
    sanitize_json,
    summary_record,
)

NOW = datetime(2026, 9, 26, 12, 30, 15, 123456, tzinfo=UTC)
INVALID_SCALARS = (
    "\ud800",
    "\ud801",
    "\udbff",
    "\udc00",
    "\udc01",
    "\udfff",
    "\ud83d\ude80",
)
SCALAR_IDS = [
    "high-start",
    "high-interior",
    "high-end",
    "low-start",
    "low-interior",
    "low-end",
    "uncombined-pair",
]
VALID_SCALARS = (
    "",
    "Žluťoučký 日本語",
    "é",
    "العربية हिन्दी 한국어",
    "e\u0301",
    "\x00\t\n\x1f\x7f",
    "\ud7ff\ue000",
    "\U00010000\U0010ffff",
    "\U0001f680",
)
SCALAR_ERROR = r"^Strings must contain only Unicode scalar values$"
USAGE_DATA = {
    "input_tokens": 1,
    "output_tokens": 2,
    "cache_creation_input_tokens": None,
    "cache_read_input_tokens": None,
    "tool_uses": None,
    "cost_usd": None,
    "estimated": False,
}


def make_observation(**changes: Any) -> Observation:
    fields = {
        "protocol_version": 1,
        "timestamp": NOW,
        "provider": "test-driver",
        "run_id": "run-1",
        "session_id": "session-1",
        "lane_id": "lane-1",
        "type": ObservationType.ACTIVITY_MESSAGE,
        "payload": {"message": "working"},
    }
    fields.update(changes)
    return Observation(**fields)


def make_summary(**changes: Any) -> SessionSummary:
    fields = {
        "success": False,
        "session_id": "session-1",
        "failure_class": FailureClass.AGENT,
        "failure_detail": "request failed",
        "rate_limit_reset_at": None,
        "usage": None,
    }
    fields.update(changes)
    return SessionSummary(**fields)


def assert_scalar_json(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key.encode("utf-8", errors="strict")
            assert_scalar_json(child)
    elif isinstance(value, list):
        for child in value:
            assert_scalar_json(child)
    elif isinstance(value, str):
        value.encode("utf-8", errors="strict")


def replace_record_string(value: Any, original: str, replacement: str) -> Any:
    if isinstance(value, dict):
        return {
            replacement if key == original else key: replace_record_string(
                child, original, replacement
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [replace_record_string(child, original, replacement) for child in value]
    return replacement if value == original else value


def positioned_scalar(scalar: str, position: str) -> str:
    if position == "middle":
        return f"prefix{scalar}suffix"
    if position == "long_prefix":
        return f"{'a' * 96}{scalar}suffix"
    return scalar


def invalid_native_record(record: dict[str, Any], scalar: str) -> dict[str, Any]:
    # JSON decoding combines adjacent high/low escapes into a valid scalar.
    # A caller-supplied Python record still must reject uncombined code units.
    if scalar == "\ud83d\ude80":
        return record
    return json.loads(json.dumps(record, ensure_ascii=True))


def nested_json(value: Any, depth: int) -> Any:
    for index in range(depth):
        if index % 3 == 0:
            value = {"nested": value}
        elif index % 3 == 1:
            value = [value]
        else:
            value = (value,)
    return value


def payload_for_type(event_type: ObservationType) -> dict[str, Any]:
    if event_type is ObservationType.USAGE_UPDATED:
        return {"usage": USAGE_DATA, "identity": "valid"}
    if event_type is ObservationType.SESSION_COMPLETED:
        return {"usage": USAGE_DATA, "message": "valid"}
    if event_type is ObservationType.SESSION_FAILED:
        return {"failure_class": FailureClass.AGENT.value, "detail": "valid"}
    if event_type is ObservationType.RATE_LIMIT_STARTED:
        return {"reset_at": None, "window": None, "detail": "valid"}
    if event_type is ObservationType.RAW_UNKNOWN:
        return {"reason": "valid", "raw_sha256": "0" * 64, "preview": "valid"}
    return {"message": "valid"}


class ScalarText(str):
    """An ordinary string subclass accepted by the public text interfaces."""


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
@pytest.mark.parametrize("field", ["provider", "run_id", "session_id", "lane_id"])
@pytest.mark.parametrize("position", ["start", "middle", "long_prefix"])
def test_observation_rejects_invalid_scalar_identifiers(
    field: str, scalar: str, position: str
) -> None:
    with pytest.raises(ValueError, match=SCALAR_ERROR):
        make_observation(**{field: positioned_scalar(scalar, position)})


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
@pytest.mark.parametrize(
    "location",
    [
        "value",
        "nested_value",
        "nested_key",
        "tuple",
        "tuple_key",
        "secret",
        "secret_key",
        "deep_value",
        "deep_key",
    ],
)
@pytest.mark.parametrize("position", ["start", "middle", "long_prefix"])
def test_observation_rejects_invalid_scalars_recursively_in_payload(
    location: str, scalar: str, position: str
) -> None:
    scalar = positioned_scalar(scalar, position)
    payloads = {
        "value": {"message": scalar},
        "nested_value": {"message": ["valid", {"nested": scalar}]},
        "nested_key": {"message": ["valid", {scalar: "valid"}]},
        "tuple": {"message": ("valid", {"nested": scalar})},
        "tuple_key": {"message": ("valid", {scalar: "valid"})},
        "secret": {"message": "valid", "password": scalar},
        "secret_key": {"message": "valid", f"password{scalar}": "valid"},
        "deep_value": {"message": nested_json(scalar, 12)},
        "deep_key": {"message": nested_json({scalar: "valid"}, 12)},
    }
    with pytest.raises(ValueError, match=SCALAR_ERROR):
        make_observation(payload=payloads[location])


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
@pytest.mark.parametrize("field", ["session_id", "failure_detail"])
@pytest.mark.parametrize("position", ["start", "middle", "long_prefix"])
def test_summary_rejects_invalid_scalar_strings(
    field: str, scalar: str, position: str
) -> None:
    with pytest.raises(ValueError, match=SCALAR_ERROR):
        make_summary(**{field: positioned_scalar(scalar, position)})


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
@pytest.mark.parametrize(
    "location",
    [
        "root",
        "list",
        "tuple",
        "value",
        "nested_key",
        "tuple_key",
        "secret",
        "secret_key",
        "deep_value",
        "deep_key",
    ],
)
@pytest.mark.parametrize("position", ["start", "middle", "long_prefix"])
def test_sanitize_json_rejects_invalid_scalars_before_redaction(
    location: str, scalar: str, position: str
) -> None:
    scalar = positioned_scalar(scalar, position)
    values = {
        "root": scalar,
        "list": ["valid", scalar],
        "tuple": ("valid", scalar),
        "value": {"message": ["valid", {"nested": scalar}]},
        "nested_key": {"message": ["valid", {scalar: "valid"}]},
        "tuple_key": {"message": ("valid", {scalar: "valid"})},
        "secret": {"password": scalar},
        "secret_key": {f"password{scalar}": "valid"},
        "deep_value": nested_json(scalar, 12),
        "deep_key": nested_json({scalar: "valid"}, 12),
    }
    with pytest.raises(ValueError, match=SCALAR_ERROR):
        sanitize_json(values[location])


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
@pytest.mark.parametrize(
    "original", ["test-driver", "run-1", "session-1", "lane-1", "marker", "nested"]
)
def test_observation_record_decoder_rejects_invalid_scalars(
    original: str, scalar: str
) -> None:
    valid = make_observation(payload={"message": ["marker", {"nested": "valid"}]})
    record = replace_record_string(observation_record(valid), original, scalar)
    decoded_record = invalid_native_record(record, scalar)

    with pytest.raises(ValueError, match=SCALAR_ERROR):
        observation_from_record(decoded_record)


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
def test_usage_observation_rejects_invalid_scalar_identity(scalar: str) -> None:
    with pytest.raises(ValueError, match=SCALAR_ERROR):
        make_observation(
            type=ObservationType.USAGE_UPDATED,
            payload={"usage": USAGE_DATA, "identity": f"request-{scalar}"},
        )


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
def test_usage_record_decoder_rejects_invalid_scalar_identity(scalar: str) -> None:
    valid = make_observation(
        type=ObservationType.USAGE_UPDATED,
        payload={"usage": USAGE_DATA, "identity": "request-1"},
    )
    record = observation_record(valid)
    record["payload"] = {"usage": USAGE_DATA, "identity": f"request-{scalar}"}
    decoded_record = invalid_native_record(record, scalar)

    with pytest.raises(ValueError, match=SCALAR_ERROR):
        observation_from_record(decoded_record)


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
@pytest.mark.parametrize("location", ["secret_value", "secret_key"])
def test_record_decoder_rejects_invalid_scalar_before_secret_redaction(
    scalar: str,
    location: str,
) -> None:
    record = observation_record(make_observation())
    secret = (
        {"password": scalar}
        if location == "secret_value"
        else {f"password{scalar}": "valid"}
    )
    record["payload"] = {"message": "valid", **secret}
    decoded_record = invalid_native_record(record, scalar)

    with pytest.raises(ValueError, match=SCALAR_ERROR):
        observation_from_record(decoded_record)


def completion_additions(scalar: str) -> dict[str, Any]:
    return {
        "value": {"extra": {"nested": scalar}},
        "nested_key": {"extra": {scalar: "valid"}},
        "secret": {"password": scalar},
    }


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
@pytest.mark.parametrize("location", ["value", "nested_key", "secret"])
def test_completion_observation_rejects_invalid_scalars_before_redaction(
    location: str, scalar: str
) -> None:
    additions = completion_additions(scalar)
    payload = {"usage": USAGE_DATA, "message": "done", **additions[location]}

    with pytest.raises(ValueError, match=SCALAR_ERROR):
        make_observation(type=ObservationType.SESSION_COMPLETED, payload=payload)


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
@pytest.mark.parametrize("location", ["value", "nested_key", "secret"])
def test_completion_record_decoder_rejects_invalid_scalars_before_redaction(
    location: str, scalar: str
) -> None:
    valid = make_observation(
        type=ObservationType.SESSION_COMPLETED,
        payload={"usage": USAGE_DATA, "message": "done"},
    )
    additions = completion_additions(scalar)
    record = observation_record(valid)
    record["payload"] = {"usage": USAGE_DATA, "message": "done", **additions[location]}
    decoded_record = invalid_native_record(record, scalar)

    with pytest.raises(ValueError, match=SCALAR_ERROR):
        observation_from_record(decoded_record)


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
@pytest.mark.parametrize("event_type", list(ObservationType))
@pytest.mark.parametrize("location", ["value", "key"])
def test_every_observation_type_rejects_invalid_scalar_payloads(
    event_type: ObservationType, location: str, scalar: str
) -> None:
    valid_payload = payload_for_type(event_type)
    valid = make_observation(type=event_type, payload=valid_payload)
    valid_record = observation_record(valid)
    assert observation_from_record(valid_record) == valid
    assert valid_record["payload"] == valid_payload
    if location == "value":
        payload = replace_record_string(valid_payload, "valid", scalar)
    else:
        key = next(iter(valid_payload))
        payload = {
            f"{key}{scalar}" if name == key else name: value
            for name, value in valid_payload.items()
        }

    with pytest.raises(ValueError, match=SCALAR_ERROR):
        make_observation(type=event_type, payload=payload)
    valid_record["payload"] = payload
    decoded = invalid_native_record(valid_record, scalar)
    with pytest.raises(ValueError, match=SCALAR_ERROR):
        observation_from_record(decoded)


@pytest.mark.parametrize("scalar", INVALID_SCALARS, ids=SCALAR_IDS)
@pytest.mark.parametrize(
    "interface",
    [
        "root",
        "value",
        "key",
        "secret_key",
        "provider",
        "run_id",
        "session_id",
        "lane_id",
        "summary_session_id",
        "failure_detail",
        "payload_value",
        "payload_key",
    ],
)
def test_text_subclasses_reject_invalid_scalars(interface: str, scalar: str) -> None:
    text = ScalarText(scalar)
    values = {
        "root": text,
        "value": {"value": text},
        "key": {text: "valid"},
        "secret_key": {ScalarText(f"password{scalar}"): "valid"},
    }
    with pytest.raises(ValueError, match=SCALAR_ERROR):
        if interface in values:
            sanitize_json(values[interface])
        elif interface == "summary_session_id":
            make_summary(session_id=text)
        elif interface == "failure_detail":
            make_summary(failure_detail=text)
        elif interface == "payload_value":
            make_observation(payload={"message": text})
        elif interface == "payload_key":
            make_observation(payload={"message": {text: "valid"}})
        else:
            make_observation(**{interface: text})


@pytest.mark.parametrize("text", [text for text in VALID_SCALARS if text])
@pytest.mark.parametrize(
    "event_type", [ObservationType.USAGE_UPDATED, ObservationType.SESSION_COMPLETED]
)
def test_usage_and_completion_preserve_valid_unicode_scalars(
    event_type: ObservationType, text: str
) -> None:
    payload = (
        {"usage": USAGE_DATA, "identity": text}
        if event_type is ObservationType.USAGE_UPDATED
        else {"usage": USAGE_DATA, "message": text, "extra": {text: text}}
    )
    observation = make_observation(type=event_type, payload=payload)
    record = observation_record(observation)
    restored = observation_from_record(
        json.loads(json.dumps(record, ensure_ascii=True))
    )

    assert record["payload"] == payload
    assert restored.type is event_type
    assert observation_record(restored)["payload"] == payload


@pytest.mark.parametrize("text", VALID_SCALARS)
def test_shared_models_and_serializers_preserve_valid_unicode_scalars(
    text: str,
) -> None:
    payload = {"message": [text, {text: text}, None]}
    observation = make_observation(
        provider=text or "test-driver",
        run_id=text or "run-1",
        session_id=text or None,
        lane_id=text or None,
        payload=payload,
    )
    summary = make_summary(session_id=text or None, failure_detail=text)

    assert sanitize_json(payload) == payload
    assert sanitize_json(None) is None
    assert sanitize_json(text) == text
    record = observation_record(observation)
    assert record["payload"] == payload
    for field in ("provider", "run_id", "session_id", "lane_id"):
        assert record[field] == getattr(observation, field)
    restored = observation_from_record(
        json.loads(json.dumps(record, ensure_ascii=False))
    )
    assert observation_record(restored)["payload"] == payload
    assert restored.session_id == observation.session_id
    assert restored == observation
    assert summary.failure_detail == text
    assert summary_record(summary)["session_id"] == (text or None)
    assert summary_record(summary)["failure_detail"] == text
    assert_scalar_json(record)
    assert_scalar_json(summary_record(summary))


def test_valid_escaped_surrogate_pair_decodes_to_supported_scalar() -> None:
    scalar = json.loads(r'"\ud83d\ude80"')
    assert scalar == "\U0001f680"
    observation = make_observation(
        provider=scalar,
        run_id=scalar,
        session_id=scalar,
        lane_id=scalar,
        payload={"message": [scalar, {scalar: scalar}]},
    )
    summary = make_summary(session_id=scalar, failure_detail=scalar)

    assert sanitize_json({scalar: scalar}) == {scalar: scalar}
    record = observation_record(observation)
    restored = observation_from_record(
        json.loads(json.dumps(record, ensure_ascii=True))
    )
    assert restored == observation
    assert restored.provider == scalar
    assert observation_record(restored)["payload"] == {
        "message": [scalar, {scalar: scalar}]
    }
    assert summary.session_id == scalar
    assert summary.failure_detail == scalar
    assert summary_record(summary)["session_id"] == scalar
    assert summary_record(summary)["failure_detail"] == scalar
    assert_scalar_json(record)
    assert_scalar_json(summary_record(summary))
