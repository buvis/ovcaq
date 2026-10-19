import hashlib
import json
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import FailureClass, Observation
from ovcaq.events.reducer import reduce_session, session_failure_observation

FIXTURES = Path(__file__).parents[1] / "fixtures" / "codex" / "v1"
FAKE_CREDENTIAL = "sk-" + "SyntheticCredentialForDecoderTestOnly123456789012"
NOW = datetime.now(UTC)


@pytest.fixture
def driver() -> CodexDriver:
    settings = AgentSettings(
        name="codex",
        command=("fixture-wrapper",),
        tiers={"standard": "fixture-model"},
        environment={},
        options={},
    )
    return CodexDriver(settings, run_id="terminal-run")


def decode(driver: CodexDriver, record: dict[str, object]) -> tuple[Observation, ...]:
    return driver.decode(json.dumps(record))


def supplied(kind: str, payload: dict[str, object]) -> Observation:
    return Observation(
        protocol_version=1,
        timestamp=NOW,
        provider="codex",
        run_id="supplied-run",
        session_id="supplied-thread",
        lane_id=None,
        type=kind,
        payload=payload,
    )


class SingleUse:
    def __init__(self, observations: Iterable[Observation]) -> None:
        self.observations = tuple(observations)
        self.iterations = 0

    def __iter__(self) -> Iterator[Observation]:
        self.iterations += 1
        assert self.iterations == 1, "summarize consumed its iterable more than once"
        yield from self.observations


@pytest.mark.parametrize(
    ("detail", "failure_class"),
    [
        ("Unauthorized: HTTP 401", "authentication"),
        ("Sandbox denied: HTTP 403", "permission"),
        ("Quota limit reached: HTTP 429", "rate_limit"),
        ("Connection reset: HTTP 503", "connectivity"),
        ("Request timed out", "timeout"),
        ("Selected model is at capacity", "connectivity"),
        ("Unexpected diagnostic", "unknown"),
    ],
)
def test_native_failure_emits_classified_terminal_with_receipt_identity(
    driver: CodexDriver, detail: str, failure_class: str
) -> None:
    decode(driver, {"type": "thread.started", "thread_id": "failure-thread"})
    before = datetime.now(UTC)
    observations = decode(driver, {"type": "turn.failed", "error": {"message": detail}})
    after = datetime.now(UTC)
    expected = ["session.failed"]
    if failure_class == "rate_limit":
        expected.append("rate_limit.started")
    assert sorted(o.type for o in observations) == sorted(expected)
    terminal = next(o for o in observations if o.type == "session.failed")
    assert dict(terminal.payload) == {"failure_class": failure_class, "detail": detail}
    for observation in observations:
        assert observation.protocol_version == 1
        assert observation.provider == "codex"
        assert observation.run_id == "terminal-run"
        assert observation.session_id == "failure-thread"
        assert observation.timestamp.utcoffset() == timedelta(0)
        assert before <= observation.timestamp <= after
    summary = driver.summarize(observations, 1)
    assert summary == reduce_session(observations, 1).summary
    assert not summary.success
    assert summary.failure_class == FailureClass(failure_class)
    assert summary.failure_detail == detail


@pytest.mark.parametrize(
    ("fixture", "failure_class"),
    [
        ("rate-limited", "rate_limit"),
        ("authentication-failed", "authentication"),
        ("connectivity-failed", "connectivity"),
        ("permission-failed", "permission"),
    ],
)
def test_fixture_error_then_identical_failure_has_one_terminal_and_rate_start(
    driver: CodexDriver, fixture: str, failure_class: str
) -> None:
    records = (FIXTURES / f"{fixture}.jsonl").read_text().splitlines()
    observations = tuple(o for line in records for o in driver.decode(line))
    failures = [o for o in observations if o.type == "session.failed"]
    provisional = [
        o
        for o in observations
        if o.payload.get("kind") == "error" and "failure_class" in o.payload
    ]
    assert len(failures) == len(provisional) == 1
    detail = json.loads(records[-1])["error"]["message"]
    assert failures[0].payload["failure_class"] == failure_class
    assert provisional[0].payload["failure_class"] == failure_class
    assert provisional[0].type == "activity.message"
    rates = [o for o in observations if o.type == "rate_limit.started"]
    assert len(rates) == int(failure_class == "rate_limit")
    for rate in rates:
        assert dict(rate.payload) == {
            "reset_at": None,
            "window": None,
            "detail": detail,
        }
    stream = SingleUse(observations)
    assert driver.summarize(stream, 1) == reduce_session(observations, 1).summary
    assert stream.iterations == 1


def test_top_level_error_is_sanitized_provisional_activity(driver: CodexDriver) -> None:
    detail = f"Unauthorized {FAKE_CREDENTIAL}\x1b[31m"
    observations = decode(driver, {"type": "error", "message": detail})
    assert len(observations) == 1
    activity = observations[0]
    assert activity.type == "activity.message"
    assert activity.payload["kind"] == "error"
    assert activity.payload["failure_class"] == "authentication"
    assert activity.payload["reset_at"] is None
    assert activity.payload["detail"] == "Unauthorized [REDACTED]"
    assert FAKE_CREDENTIAL not in activity.payload["detail"]
    assert "[REDACTED]" in activity.payload["detail"]


@pytest.mark.parametrize(
    "reset", ["retry after 30 seconds", "retry after 21600 seconds"]
)
def test_native_rate_failure_preserves_explicit_bounded_reset(
    driver: CodexDriver, reset: str
) -> None:
    detail = f"Rate limit reached; {reset}"
    observations = decode(driver, {"type": "turn.failed", "error": {"message": detail}})
    failure = next(o for o in observations if o.type == "session.failed")
    rate = next(o for o in observations if o.type == "rate_limit.started")
    seconds = int(reset.split()[2])
    expected = rate.timestamp + timedelta(seconds=seconds)
    actual = datetime.fromisoformat(rate.payload["reset_at"])
    assert actual.utcoffset() == timedelta(0)
    assert abs((actual - expected).total_seconds()) < 1
    assert dict(failure.payload) == {"failure_class": "rate_limit", "detail": detail}
    assert rate.payload["window"] is None
    assert rate.payload["detail"] == detail
    assert driver.summarize(observations, 1).rate_limit_reset_at == actual


def test_provisional_rate_error_preserves_explicit_utc_reset_without_terminal(
    driver: CodexDriver,
) -> None:
    reset = datetime.now(UTC) + timedelta(seconds=120)
    detail = f"Rate limit reached; reset at {reset.isoformat()}"
    observations = decode(driver, {"type": "error", "message": detail})
    assert len(observations) == 1
    activity = observations[0]
    assert activity.type == "activity.message"
    assert activity.payload["kind"] == "error"
    assert activity.payload["failure_class"] == "rate_limit"
    assert activity.payload["detail"] == detail
    assert datetime.fromisoformat(activity.payload["reset_at"]) == reset
    summary = driver.summarize(SingleUse(observations), 1)
    assert summary.failure_class == FailureClass("rate_limit")
    assert summary.rate_limit_reset_at == reset


@pytest.mark.parametrize(
    "reset",
    [
        "try again in 60 seconds",
        "retry after -1 seconds",
        "retry after 21601 seconds",
        "retry after nan seconds",
        "retry after 1e999 seconds",
        "reset at 2020-01-01T00:00:00Z",
        "reset at 2099-01-01T00:00:00",
        "reset at 3:00 PM",
        "",
    ],
)
def test_native_rate_failure_keeps_missing_or_invalid_reset_unknown(
    driver: CodexDriver, reset: str
) -> None:
    detail = f"Rate limit reached; {reset}"
    observations = decode(driver, {"type": "turn.failed", "error": {"message": detail}})
    rate = next(o for o in observations if o.type == "rate_limit.started")
    assert dict(rate.payload) == {"reset_at": None, "window": None, "detail": detail}
    assert driver.summarize(observations, 1).rate_limit_reset_at is None


def test_recovered_provisional_error_has_no_failure_or_rate_observations(
    driver: CodexDriver,
) -> None:
    lines = (FIXTURES / "healthy.jsonl").read_text().splitlines()
    observations = tuple(o for line in lines for o in driver.decode(line))
    assert not any(
        o.type in {"session.failed", "rate_limit.started"} for o in observations
    )
    assert any(o.payload.get("kind") == "error" for o in observations)
    stream = SingleUse(observations)
    summary = driver.summarize(stream, 0)
    assert summary == reduce_session(observations, 0).summary
    assert summary.success
    assert summary.failure_class is None
    assert summary.failure_detail is None
    assert stream.iterations == 1


def test_nonfatal_item_error_never_supplies_provisional_failure_metadata(
    driver: CodexDriver,
) -> None:
    observations = decode(
        driver,
        {
            "type": "item.completed",
            "item": {
                "id": "warning-429",
                "type": "error",
                "message": "Rate limit reached",
            },
        },
    )
    assert observations
    assert all(o.type == "activity.message" for o in observations)
    for observation in observations:
        assert "failure_class" not in observation.payload
        assert "reset_at" not in observation.payload
    assert driver.summarize(observations, 0) == reduce_session(observations, 0).summary


@pytest.mark.parametrize("failure_class", [value.value for value in FailureClass])
def test_supplied_provisional_metadata_is_authoritative_without_prior_decode(
    driver: CodexDriver, failure_class: str
) -> None:
    reset = NOW + timedelta(seconds=90) if failure_class == "rate_limit" else None
    activity = supplied(
        "activity.message",
        {
            "kind": "error",
            "detail": "Opaque normalized diagnostic",
            "failure_class": failure_class,
            "reset_at": reset.isoformat() if reset else None,
        },
    )
    stream = SingleUse([activity])
    summary = driver.summarize(stream, 0)
    assert not summary.success
    assert summary.session_id == "supplied-thread"
    assert summary.failure_class == FailureClass(failure_class)
    assert summary.failure_detail == "Opaque normalized diagnostic"
    assert summary.rate_limit_reset_at == reset
    assert stream.iterations == 1
    assert activity.payload["kind"] == "error"


def test_latest_provisional_error_supersedes_earlier_normalized_metadata(
    driver: CodexDriver,
) -> None:
    first = supplied(
        "activity.message",
        {
            "kind": "error",
            "detail": "First",
            "failure_class": "rate_limit",
            "reset_at": (NOW + timedelta(seconds=30)).isoformat(),
        },
    )
    last = supplied(
        "activity.message",
        {
            "kind": "error",
            "detail": "Last",
            "failure_class": "authentication",
            "reset_at": None,
        },
    )
    summary = driver.summarize(SingleUse([first, last]), 1)
    assert not summary.success
    assert summary.failure_class == FailureClass("authentication")
    assert summary.failure_detail == "Last"
    assert summary.rate_limit_reset_at is None


@pytest.mark.parametrize("exit_code", [0, 1])
def test_empty_or_nonprovisional_input_preserves_shared_reducer_result(
    driver: CodexDriver, exit_code: int
) -> None:
    for observations in [
        [],
        [
            supplied(
                "activity.message",
                {"kind": "message", "detail": "Quoted example: HTTP 429; rate limit"},
            )
        ],
    ]:
        stream = SingleUse(observations)
        summary = driver.summarize(stream, exit_code)
        assert summary == reduce_session(observations, exit_code).summary
        assert not summary.success
        assert stream.iterations == 1


def test_reused_driver_never_applies_stale_provisional_error(
    driver: CodexDriver,
) -> None:
    old = decode(driver, {"type": "error", "message": "Unauthorized"})
    assert driver.summarize(old, 1).failure_class == FailureClass("authentication")
    fresh = [supplied("activity.message", {"kind": "message", "detail": "Fresh input"})]
    assert driver.summarize(SingleUse(fresh), 0) == reduce_session(fresh, 0).summary
    assert driver.summarize(SingleUse([]), 1) == reduce_session([], 1).summary


@pytest.mark.parametrize(
    "runtime_class", [FailureClass("timeout"), FailureClass("agent")]
)
def test_runtime_terminal_preserves_reducer_precedence_over_provisional_error(
    driver: CodexDriver, runtime_class: FailureClass
) -> None:
    provisional = supplied(
        "activity.message",
        {
            "kind": "error",
            "detail": "Quota limit",
            "failure_class": "rate_limit",
            "reset_at": (NOW + timedelta(seconds=90)).isoformat(),
        },
    )
    runtime = session_failure_observation(
        timestamp=NOW,
        provider="runtime",
        run_id="supplied-run",
        session_id="supplied-thread",
        failure_class=runtime_class,
        detail="Runtime terminal",
    )
    observations = [provisional, runtime]
    assert (
        driver.summarize(SingleUse(observations), 1)
        == reduce_session(observations, 1).summary
    )


def test_multiple_turn_terminals_preserve_shared_reducer_result(
    driver: CodexDriver,
) -> None:
    decode(driver, {"type": "thread.started", "thread_id": "multi-turn"})
    first = decode(
        driver, {"type": "turn.failed", "error": {"message": "Unauthorized"}}
    )
    second = decode(
        driver,
        {
            "type": "turn.completed",
            "usage": {"input_tokens": 3, "cached_input_tokens": 0, "output_tokens": 2},
        },
    )
    observations = [*first, *second]
    assert (
        driver.summarize(SingleUse(observations), 0)
        == reduce_session(observations, 0).summary
    )


def test_conflicting_terminal_identities_preserve_shared_reducer_result(
    driver: CodexDriver,
) -> None:
    first = supplied(
        "session.failed", {"failure_class": "permission", "detail": "Denied"}
    )
    second = Observation(
        protocol_version=1,
        timestamp=NOW,
        provider="codex",
        run_id="supplied-run",
        session_id="other-thread",
        lane_id=None,
        type="session.failed",
        payload={"failure_class": "authentication", "detail": "Login"},
    )
    observations = [first, second]
    expected = reduce_session(observations, 1).summary
    assert driver.summarize(SingleUse(observations), 1) == expected
    assert expected.failure_class == FailureClass("unknown")
    assert expected.failure_detail is None


@pytest.mark.parametrize(
    "record",
    [
        {"type": "turn.failed"},
        {"type": "turn.failed", "error": None},
        {"type": "turn.failed", "error": []},
        {"type": "turn.failed", "error": {"message": 429}},
        {"type": "error"},
        {"type": "error", "message": None},
        {"type": "error", "message": ["Unauthorized"]},
    ],
)
def test_malformed_failure_records_degrade_to_hashed_raw_without_state_changes(
    driver: CodexDriver, record: dict[str, object]
) -> None:
    decode(driver, {"type": "thread.started", "thread_id": "valid-thread"})
    raw_line = json.dumps(record)
    observations = driver.decode(raw_line)
    assert observations
    assert all(o.type == "raw.unknown" for o in observations)
    for observation in observations:
        assert set(observation.payload) == {"reason", "raw_sha256", "preview"}
        assert (
            observation.payload["raw_sha256"]
            == hashlib.sha256(raw_line.encode()).hexdigest()
        )
        assert isinstance(observation.payload["reason"], str)
        assert observation.payload["reason"]
        assert len(observation.payload["preview"]) <= 512
        assert observation.session_id == "valid-thread"
    terminal = decode(
        driver, {"type": "turn.failed", "error": {"message": "Unauthorized"}}
    )
    assert (
        next(o for o in terminal if o.type == "session.failed").session_id
        == "valid-thread"
    )
