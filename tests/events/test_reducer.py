"""Requirements for deterministic, provider-neutral session reduction."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime, timedelta, timezone

import pytest

from ovcaq.events import (
    FailureClass,
    Observation,
    ObservationType,
    Reduction,
    SessionSummary,
    Usage,
    observation_record,
    reduce_session,
    session_failure_observation,
)

NOW = datetime(2026, 9, 26, 12, 30, tzinfo=UTC)
RESET = datetime(2026, 9, 26, 13, 0, tzinfo=UTC)
COUNTERS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "tool_uses",
)
EMPTY_USAGE = dict.fromkeys(COUNTERS) | {"cost_usd": None, "estimated": False}


def event(kind, payload=None, session_id="session-1", **changes):
    fields = {
        "protocol_version": 1,
        "timestamp": NOW,
        "provider": "test-driver",
        "run_id": "run-1",
        "session_id": session_id,
        "lane_id": None,
        "type": ObservationType(kind),
        "payload": {} if payload is None else payload,
    }
    return Observation(**(fields | changes))


def usage_event(identity=None, **changes):
    return event(
        "usage.updated", {"identity": identity, "usage": EMPTY_USAGE | changes}
    )


def failure(failure_class="agent", detail="failed", session_id="session-1"):
    return event(
        "session.failed",
        {"failure_class": failure_class, "detail": detail},
        session_id=session_id,
    )


def limit(detail="wait", reset_at="2026-09-26T13:00:00Z"):
    return event(
        "rate_limit.started", {"reset_at": reset_at, "window": None, "detail": detail}
    )


def test_reduction_preserves_original_observations_and_is_deterministic():
    observations = (
        event("session.started"),
        event("activity.message", {"message": "working"}),
        usage_event(input_tokens=3),
        event("session.completed"),
    )
    first = reduce_session(iter(observations), exit_code=0)
    second = reduce_session(observations, exit_code=0)
    assert isinstance(first, Reduction)
    assert isinstance(first.summary, SessionSummary)
    assert type(first.observations) is tuple
    assert first.observations == observations
    assert all(a is b for a, b in zip(first.observations, observations, strict=True))
    assert first == second
    assert first.summary.success is True
    assert first.summary.session_id == "session-1"
    assert first.summary.failure_class is None
    assert first.summary.failure_detail is None
    assert first.summary.usage == Usage(**(EMPTY_USAGE | {"input_tokens": 3}))


def test_reduction_is_a_frozen_slotted_dataclass():
    reduced = reduce_session((), exit_code=0)
    assert is_dataclass(reduced)
    assert not hasattr(reduced, "__dict__")
    assert Reduction(reduced.observations, reduced.summary) == reduced
    for field, value in (("observations", ()), ("summary", reduced.summary)):
        with pytest.raises((FrozenInstanceError, AttributeError)):
            setattr(reduced, field, value)


@pytest.mark.parametrize(
    "exit_code,kind", [(0, "unknown"), (1, "agent"), (-15, "agent")]
)
@pytest.mark.parametrize("started", [False, True])
def test_missing_terminal_is_unsuccessful_even_with_zero_exit(exit_code, kind, started):
    observations = (event("session.started"),) if started else ()
    reduced = reduce_session(observations, exit_code=exit_code)
    assert reduced.observations == observations
    assert reduced.summary.success is False
    assert reduced.summary.failure_class == FailureClass(kind)
    assert reduced.summary.session_id == ("session-1" if started else None)
    assert reduced.summary.usage is None
    assert reduced.summary.rate_limit_reset_at is None


@pytest.mark.parametrize("identity", [None, "request-1"])
def test_identical_snapshots_never_add_usage(identity):
    values = dict.fromkeys(COUNTERS, 9) | {"cost_usd": 0.25, "estimated": False}
    observation = usage_event(identity, **values)
    reduced = reduce_session((observation, observation, observation), exit_code=0)
    assert reduced.observations == (observation, observation, observation)
    assert reduced.summary.usage == Usage(**values)


@pytest.mark.parametrize("identities", [(None, None), ("a", "a"), ("a", "b")])
def test_usage_snapshots_merge_each_numeric_field_by_maximum(identities):
    first = dict(zip(COUNTERS, (10, 1, 30, 2, 5), strict=True)) | {"cost_usd": 0.5}
    second = dict(zip(COUNTERS, (3, 20, None, 40, 1), strict=True)) | {"cost_usd": 0.2}
    observations = (
        usage_event(identities[0], **first),
        usage_event(identities[1], **second),
        usage_event(None),
    )
    summary = reduce_session(observations, exit_code=0).summary
    expected = dict(zip(COUNTERS, (10, 20, 30, 40, 5), strict=True))
    assert summary.usage == Usage(**expected, cost_usd=0.5, estimated=False)


@pytest.mark.parametrize("field", (*COUNTERS, "cost_usd"))
def test_usage_keeps_zero_and_accepts_a_later_larger_value(field):
    zero, larger = (0.0, 2.0) if field == "cost_usd" else (0, 2)
    observations = (usage_event(**{field: zero}), usage_event(**{field: larger}))
    initial = reduce_session(observations[:1], exit_code=0).summary.usage
    final = reduce_session(observations, exit_code=0).summary.usage
    assert initial == Usage(**(EMPTY_USAGE | {field: zero}))
    assert final == Usage(**(EMPTY_USAGE | {field: larger}))


@pytest.mark.parametrize(
    "exact,expected_estimated",
    [
        ({"input_tokens": 10, "output_tokens": 20, "cost_usd": 0.5}, False),
        ({"input_tokens": 11, "output_tokens": 21, "cost_usd": 0.6}, False),
        ({"input_tokens": 10, "output_tokens": 20}, True),
        ({"input_tokens": 10, "cost_usd": 0.5}, True),
        ({"input_tokens": 9, "output_tokens": 21, "cost_usd": 0.6}, True),
    ],
)
def test_exact_usage_clears_estimation_only_when_it_covers_all_winners(
    exact, expected_estimated
):
    observations = (
        usage_event(input_tokens=10, output_tokens=20, cost_usd=0.5, estimated=True),
        usage_event(**exact),
    )
    summary = reduce_session(observations, exit_code=0).summary
    expected = EMPTY_USAGE | {
        "input_tokens": max(10, exact.get("input_tokens", 0)),
        "output_tokens": max(20, exact.get("output_tokens", 0)),
        "cost_usd": max(0.5, exact.get("cost_usd", 0)),
        "estimated": expected_estimated,
    }
    assert summary.usage == Usage(**expected)


@pytest.mark.parametrize("field", (*COUNTERS, "cost_usd"))
def test_estimate_that_exceeds_an_exact_winner_marks_usage_estimated(field):
    exact, estimated = (2.0, 3.0) if field == "cost_usd" else (2, 3)
    observations = (
        usage_event(**{field: exact}),
        usage_event(**{field: estimated, "estimated": True}),
    )
    expected = EMPTY_USAGE | {field: estimated, "estimated": True}
    assert reduce_session(observations, exit_code=0).summary.usage == Usage(**expected)


@pytest.mark.parametrize("estimated_value", [None, 0, 5, 10])
def test_dominated_estimate_does_not_downgrade_exact_usage(estimated_value):
    exact = dict.fromkeys(COUNTERS, 10) | {"cost_usd": 10.0, "estimated": False}
    estimate = dict.fromkeys(COUNTERS, estimated_value) | {
        "cost_usd": None if estimated_value is None else float(estimated_value),
        "estimated": True,
    }
    summary = reduce_session(
        (usage_event("exact", **exact), usage_event("estimate", **estimate)),
        exit_code=0,
    ).summary
    assert summary.usage == Usage(**exact)


def test_duplicate_estimate_after_exact_confirmation_stays_exact():
    estimate = usage_event("request-1", input_tokens=10, estimated=True)
    exact = usage_event("request-2", input_tokens=10)
    reduced = reduce_session((estimate, exact, estimate), exit_code=0)
    assert reduced.observations == (estimate, exact, estimate)
    assert reduced.summary.usage == Usage(**(EMPTY_USAGE | {"input_tokens": 10}))


@pytest.mark.parametrize("terminal", [event("session.completed"), failure()])
def test_null_start_does_not_prevent_terminal_identity_binding(terminal):
    observations = (event("session.started", session_id=None), terminal)
    summary = reduce_session(observations, exit_code=0).summary
    assert summary.session_id == "session-1"
    assert summary.success is (terminal.type == ObservationType.SESSION_COMPLETED)


def test_first_non_null_start_binds_session_with_anonymous_terminals():
    observations = (
        event("session.started", session_id=None),
        event("session.started", session_id="bound"),
        event("session.completed", session_id=None),
    )
    summary = reduce_session(observations, exit_code=0).summary
    assert summary.session_id == "bound"
    assert summary.success is True
    assert summary.failure_class is None


@pytest.mark.parametrize(
    "kind", ["session.started", "activity.message", "session.completed"]
)
def test_later_different_session_identity_forces_unknown_failure(kind):
    observations = (
        event("session.started"),
        event(kind, session_id="other-session"),
        event("session.completed"),
    )
    summary = reduce_session(observations, exit_code=0).summary
    assert summary.success is False
    assert summary.failure_class == FailureClass.UNKNOWN


def test_conflicting_terminal_identities_fail_without_a_start():
    observations = (
        event("session.completed", session_id="first"),
        event("session.completed", session_id="second"),
    )
    summary = reduce_session(observations, exit_code=0).summary
    assert summary.success is False
    assert summary.failure_class == FailureClass.UNKNOWN


@pytest.mark.parametrize(
    "terminal", [event("session.completed"), failure("timeout", "late")]
)
def test_equal_duplicate_terminals_are_idempotent(terminal):
    once = reduce_session((terminal,), exit_code=0)
    twice = reduce_session((terminal, terminal), exit_code=0)
    assert once.summary == twice.summary
    assert twice.observations == (terminal, terminal)


@pytest.mark.parametrize("exit_code", [0, 2, -15])
@pytest.mark.parametrize("failure_first", [False, True])
def test_failure_wins_over_completion_in_either_order(exit_code, failure_first):
    completed = event("session.completed")
    failed = failure("permission", "denied")
    observations = (failed, completed) if failure_first else (completed, failed)
    summary = reduce_session(observations, exit_code=exit_code).summary
    assert summary.success is False
    assert summary.failure_class == FailureClass.PERMISSION
    assert summary.failure_detail == "denied"
    assert summary.session_id == "session-1"


def test_last_failure_supplies_class_and_detail_even_after_completion():
    observations = (
        failure("authentication", "first failure"),
        event("session.completed"),
        failure("timeout", "last failure"),
    )
    summary = reduce_session(observations, exit_code=0).summary
    assert summary.success is False
    assert summary.failure_class == FailureClass.TIMEOUT
    assert summary.failure_detail == "last failure"


@pytest.mark.parametrize("exit_code", [0, 1])
def test_last_completion_supplies_serialized_usage(exit_code):
    observations = (
        event("session.completed", {"usage": EMPTY_USAGE | {"input_tokens": 7}}),
        event("session.completed", {"usage": EMPTY_USAGE | {"input_tokens": 9}}),
    )
    summary = reduce_session(observations, exit_code=exit_code).summary
    assert summary.success is True
    assert summary.failure_class is None
    assert summary.usage == Usage(**(EMPTY_USAGE | {"input_tokens": 9}))


def test_usage_after_completion_still_participates():
    observations = (
        event("session.completed", {"usage": EMPTY_USAGE | {"input_tokens": 7}}),
        usage_event(input_tokens=9, output_tokens=4),
    )
    summary = reduce_session(observations, exit_code=0).summary
    expected = EMPTY_USAGE | {"input_tokens": 9, "output_tokens": 4}
    assert summary.success is True
    assert summary.usage == Usage(**expected)


def test_later_completion_never_lowers_earlier_usage_winners():
    first = EMPTY_USAGE | {"input_tokens": 12, "output_tokens": 2, "cost_usd": 0.5}
    last = EMPTY_USAGE | {"input_tokens": 7, "output_tokens": 5, "cost_usd": 0.2}
    observations = (
        event("session.completed", {"usage": first}),
        event("session.completed", {"usage": last}),
    )
    summary = reduce_session(observations, exit_code=0).summary
    expected = first | {"output_tokens": 5}
    assert summary.success is True
    assert summary.failure_class is None
    assert summary.usage == Usage(**expected)


@pytest.mark.parametrize("exit_code", [0, 1])
@pytest.mark.parametrize("terminal", [None, "unknown", "agent"])
def test_live_limit_upgrades_missing_or_generic_failure(terminal, exit_code):
    observations = [event("session.started"), limit()]
    if terminal is not None:
        observations.append(failure(terminal, "generic failure"))
    summary = reduce_session(observations, exit_code=exit_code).summary
    assert summary.success is False
    assert summary.failure_class == FailureClass.RATE_LIMIT
    assert summary.failure_detail == "wait"
    assert summary.rate_limit_reset_at == RESET


@pytest.mark.parametrize(
    "latest_reset",
    [
        datetime(2026, 9, 26, 13, 45, tzinfo=UTC),
        datetime(2026, 9, 26, 12, 45, tzinfo=UTC),
    ],
)
def test_successive_live_limits_preserve_the_latest_supplied_reset(latest_reset):
    observations = (
        limit("first wait"),
        limit("latest wait", reset_at=latest_reset.isoformat().replace("+00:00", "Z")),
    )
    summary = reduce_session(observations, exit_code=0).summary
    assert summary.success is False
    assert summary.failure_class == FailureClass.RATE_LIMIT
    assert summary.failure_detail == "latest wait"
    assert summary.rate_limit_reset_at == latest_reset


@pytest.mark.parametrize(
    "kind", ["connectivity", "permission", "authentication", "timeout"]
)
def test_live_limit_preserves_specific_failure(kind):
    summary = reduce_session((failure(kind, "specific"), limit()), exit_code=1).summary
    assert summary.success is False
    assert summary.failure_class == FailureClass(kind)
    assert summary.failure_detail == "specific"


@pytest.mark.parametrize("limit_first", [False, True])
def test_explicit_completion_remains_successful_with_live_limit(limit_first):
    completed = event("session.completed")
    observations = (limit(), completed) if limit_first else (completed, limit())
    summary = reduce_session(observations, exit_code=0).summary
    assert summary.success is True
    assert summary.failure_class is None
    assert summary.failure_detail is None


@pytest.mark.parametrize("terminal", [None, "unknown", "agent"])
def test_cleared_limit_no_longer_upgrades_a_failure(terminal):
    observations = [limit(), event("rate_limit.cleared")]
    if terminal is not None:
        observations.append(failure(terminal, "original"))
    summary = reduce_session(observations, exit_code=1).summary
    assert summary.success is False
    assert summary.failure_class == FailureClass(terminal or "agent")
    assert summary.rate_limit_reset_at is None
    if terminal is not None:
        assert summary.failure_detail == "original"


def test_clear_before_a_limit_does_not_clear_the_future_limit():
    observations = (event("rate_limit.cleared"), limit("new wait", reset_at=None))
    summary = reduce_session(observations, exit_code=0).summary
    assert summary.success is False
    assert summary.failure_class == FailureClass.RATE_LIMIT
    assert summary.failure_detail == "new wait"
    assert summary.rate_limit_reset_at is None


def test_new_limit_after_clear_supplies_current_detail_and_reset():
    observations = (
        limit("old wait", reset_at=None),
        event("rate_limit.cleared"),
        limit("new wait"),
    )
    summary = reduce_session(observations, exit_code=0).summary
    assert summary.failure_class == FailureClass.RATE_LIMIT
    assert summary.failure_detail == "new wait"
    assert summary.rate_limit_reset_at == RESET


@pytest.mark.parametrize("session_id", [None, "session-1"])
@pytest.mark.parametrize("failure_class", list(FailureClass))
def test_synthetic_failure_preserves_normalized_fields(session_id, failure_class):
    observation = session_failure_observation(
        timestamp=NOW,
        provider="custom-driver",
        run_id="run-2",
        session_id=session_id,
        failure_class=failure_class,
        detail="failure detail",
    )
    assert isinstance(observation, Observation)
    assert observation.protocol_version == 1
    assert observation.timestamp == NOW
    assert observation.provider == "custom-driver"
    assert observation.run_id == "run-2"
    assert observation.session_id == session_id
    assert observation.lane_id is None
    assert observation.type == ObservationType.SESSION_FAILED
    assert observation_record(observation)["payload"] == {
        "failure_class": failure_class.value,
        "detail": "failure detail",
    }


def test_synthetic_failure_sanitizes_detail_before_exposing_it():
    observation = session_failure_observation(
        timestamp=NOW,
        provider="custom-driver",
        run_id="run-1",
        session_id=None,
        failure_class=FailureClass.AGENT,
        detail="Authorization: Bearer private-value",
    )
    expected = "Authorization: Bearer [REDACTED]"
    assert observation.payload["detail"] == expected
    assert observation_record(observation)["payload"]["detail"] == expected
    assert (
        reduce_session((observation,), exit_code=1).summary.failure_detail == expected
    )


@pytest.mark.parametrize(
    "timestamp",
    [NOW.replace(tzinfo=None), NOW.astimezone(timezone(timedelta(hours=2)))],
)
def test_synthetic_failure_rejects_non_utc_timestamps(timestamp):
    with pytest.raises((TypeError, ValueError)):
        session_failure_observation(
            timestamp=timestamp,
            provider="custom-driver",
            run_id="run-1",
            session_id=None,
            failure_class=FailureClass.UNKNOWN,
            detail="failed",
        )
