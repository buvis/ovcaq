from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers import claude_events
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.events import Observation, ObservationType

PRAGUE_BANNER = "You've hit your session limit · resets 8:10pm (Europe/Prague)"
ANCHOR = datetime(2099, 6, 1, 10, tzinfo=UTC)
FAR_RESET = datetime(2100, 1, 1, tzinfo=UTC)
WINTER_ANCHOR = datetime(2099, 1, 15, 10, tzinfo=UTC)
# 21:00 CET on the eve of the 2099-03-29 switch to CEST.
BEFORE_PRAGUE_DST = datetime(2099, 3, 28, 20, tzinfo=UTC)


@pytest.fixture
def driver() -> ClaudeDriver:
    settings = AgentSettings(
        name="claude",
        command=(sys.executable, "--literal-wrapper-argument"),
        tiers={"standard": "provider-primary"},
        environment={},
        options={"permission_mode": "auto"},
    )
    return ClaudeDriver(settings, run_id="run-rate")


def limit_event(
    driver: ClaudeDriver, status: str, window: object = "five_hour"
) -> tuple[Observation, ...]:
    info = {"status": status, "resetsAt": 4102444800, "rateLimitType": window}
    return driver.decode(
        json.dumps(
            {"type": "rate_limit_event", "session_id": "s1", "rate_limit_info": info}
        )
    )


def rejected_event(
    driver: ClaudeDriver, resets_at: int | None
) -> tuple[Observation, ...]:
    info: dict[str, object] = {"status": "rejected", "rateLimitType": "five_hour"}
    if resets_at is not None:
        info["resetsAt"] = resets_at
    return driver.decode(
        json.dumps(
            {"type": "rate_limit_event", "session_id": "s1", "rate_limit_info": info}
        )
    )


def failed_result(
    driver: ClaudeDriver, detail: str, timestamp: str | None = None
) -> tuple[Observation, ...]:
    record = {
        "type": "result",
        "subtype": "error",
        "is_error": True,
        "session_id": "s1",
        "result": detail,
    }
    if timestamp is not None:
        record["timestamp"] = timestamp
    return driver.decode(json.dumps(record))


def of_type(
    observations: tuple[Observation, ...], kind: ObservationType
) -> list[Observation]:
    return [o for o in observations if o.type == kind]


def test_rejected_event_reset_wins_over_later_terminal_banner(
    driver: ClaudeDriver,
) -> None:
    observations = (
        *limit_event(driver, "rejected"),
        *failed_result(driver, PRAGUE_BANNER, "2099-06-01T10:00:00Z"),
    )
    started = of_type(observations, ObservationType.RATE_LIMIT_STARTED)
    assert len(started) == 1
    assert started[0].payload["reset_at"] == "2100-01-01T00:00:00Z"
    failed = of_type(observations, ObservationType.SESSION_FAILED)
    assert failed[-1].payload["failure_class"] == "rate_limit"
    summary = driver.summarize(observations, 1)
    assert summary.failure_class == "rate_limit"
    assert summary.rate_limit_reset_at == FAR_RESET


def test_earlier_credible_rejection_reset_still_wins_over_later_banner(
    driver: ClaudeDriver,
) -> None:
    rejection_reset = datetime(2099, 6, 1, 12, tzinfo=UTC)
    observations = (
        *rejected_event(driver, int(rejection_reset.timestamp())),
        *failed_result(driver, PRAGUE_BANNER, "2099-06-01T10:00:00Z"),
    )
    started = of_type(observations, ObservationType.RATE_LIMIT_STARTED)
    assert [o.payload["reset_at"] for o in started] == ["2099-06-01T12:00:00Z"]
    assert driver.summarize(observations, 1).rate_limit_reset_at == rejection_reset


def test_warning_after_rejection_does_not_clear_live_limit(
    driver: ClaudeDriver,
) -> None:
    observations = (
        *limit_event(driver, "rejected"),
        *limit_event(driver, "allowed_warning"),
        *failed_result(driver, "provider execution failed"),
    )
    assert not of_type(observations, ObservationType.RATE_LIMIT_CLEARED)
    summary = driver.summarize(observations, 1)
    assert summary.failure_class == "rate_limit"
    assert summary.rate_limit_reset_at == FAR_RESET


@pytest.mark.parametrize("window", ("seven_day", "five_hour"))
def test_lone_warning_is_activity_and_never_upgrades_agent_failure(
    driver: ClaudeDriver, window: str
) -> None:
    warning = limit_event(driver, "allowed_warning", window)
    (message,) = of_type(warning, ObservationType.ACTIVITY_MESSAGE)
    assert message.payload["kind"] == "rate_limit_warning"
    assert message.payload["window"] == window
    assert message.payload["reset_at"] == "2100-01-01T00:00:00Z"
    assert not of_type(warning, ObservationType.RATE_LIMIT_STARTED)
    assert not of_type(warning, ObservationType.RATE_LIMIT_CLEARED)
    observations = (*warning, *failed_result(driver, "provider execution failed"))
    summary = driver.summarize(observations, 1)
    assert summary.failure_class == "agent"
    assert summary.rate_limit_reset_at is None


@pytest.mark.parametrize("status", ("rejected", "allowed_warning", "allowed"))
@pytest.mark.parametrize("window", (None, 5, ["five_hour"]))
def test_non_text_limit_type_yields_null_window(
    driver: ClaudeDriver, status: str, window: object
) -> None:
    observations = limit_event(driver, status, window)
    (payload,) = (o.payload for o in observations if "window" in o.payload)
    assert payload["window"] is None


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    (
        ("2099-06-01T10:00:00Z", "2099-06-01T18:10:00Z"),
        ("2099-06-01T19:00:00Z", "2099-06-02T18:10:00Z"),
    ),
)
def test_zoned_banner_resolves_reset_from_result_timestamp(
    driver: ClaudeDriver, timestamp: str, expected: str
) -> None:
    observations = failed_result(driver, PRAGUE_BANNER, timestamp)
    (started,) = of_type(observations, ObservationType.RATE_LIMIT_STARTED)
    assert dict(started.payload) == {
        "reset_at": expected,
        "window": None,
        "detail": PRAGUE_BANNER,
    }
    (failed,) = of_type(observations, ObservationType.SESSION_FAILED)
    assert failed.payload["failure_class"] == "rate_limit"
    summary = driver.summarize(observations, 1)
    assert summary.rate_limit_reset_at == datetime.fromisoformat(expected)


def test_zoned_banner_without_timestamp_anchors_on_current_time(
    driver: ClaudeDriver,
) -> None:
    prague = ZoneInfo("Europe/Prague")
    before = datetime.now(prague)
    observations = failed_result(driver, PRAGUE_BANNER)
    reset = driver.summarize(observations, 1).rate_limit_reset_at
    expected = before.replace(hour=20, minute=10, second=0, microsecond=0)
    if expected <= before:
        expected += timedelta(days=1)
    assert reset == expected.astimezone(UTC)


@pytest.mark.parametrize(
    ("detail", "timestamp"),
    (
        ("You've hit your session limit · resets 8:10pm (Mars/Olympus)", None),
        ("You've hit your session limit · resets 8:10pm", None),
        ("You've hit your usage limit · resets at 3pm", None),
        (PRAGUE_BANNER, "2000-06-01T10:00:00Z"),
    ),
)
def test_uncredible_banner_never_schedules_retry(
    driver: ClaudeDriver, detail: str, timestamp: str | None
) -> None:
    observations = failed_result(driver, detail, timestamp)
    assert not of_type(observations, ObservationType.RATE_LIMIT_STARTED)
    summary = driver.summarize(observations, 1)
    assert summary.failure_class == "rate_limit"
    assert summary.rate_limit_reset_at is None


@pytest.mark.parametrize(
    ("text", "anchor", "expected"),
    (
        (PRAGUE_BANNER, ANCHOR, "2099-06-01T18:10:00Z"),
        (PRAGUE_BANNER, ANCHOR.replace(hour=19), "2099-06-02T18:10:00Z"),
        (PRAGUE_BANNER, ANCHOR.replace(hour=18, minute=10), "2099-06-02T18:10:00Z"),
        ("resets at 3PM (Europe/Prague)", ANCHOR, "2099-06-01T13:00:00Z"),
        ("resets 12am ( UTC )", ANCHOR, "2099-06-02T00:00:00Z"),
        ("resets 12:30pm (UTC)", ANCHOR, "2099-06-01T12:30:00Z"),
        ("resets 9am (America/New_York)", ANCHOR, "2099-06-01T13:00:00Z"),
        (PRAGUE_BANNER, WINTER_ANCHOR, "2099-01-15T19:10:00Z"),
        ("resets 9am (America/New_York)", WINTER_ANCHOR, "2099-01-15T14:00:00Z"),
        ("resets 8pm (Asia/Tokyo)", ANCHOR, "2099-06-01T11:00:00Z"),
        ("resets 8pm (Asia/Kathmandu)", ANCHOR, "2099-06-01T14:15:00Z"),
        (PRAGUE_BANNER, BEFORE_PRAGUE_DST, "2099-03-29T18:10:00Z"),
    ),
)
def test_banner_reset_resolves_next_zoned_wall_clock_time(
    text: str, anchor: datetime, expected: str
) -> None:
    now = datetime(2099, 1, 1, tzinfo=UTC)
    assert claude_events.banner_reset(text, anchor, now) == expected


@pytest.mark.parametrize(
    ("text", "now"),
    (
        ("resets 8:10pm (Mars/Olympus)", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets 8:10pm ()", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets 8:10pm", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets at 3pm", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets soon (Europe/Prague)", datetime(2099, 1, 1, tzinfo=UTC)),
        (PRAGUE_BANNER, datetime(2099, 6, 1, 18, 10, tzinfo=UTC)),
        (PRAGUE_BANNER, datetime(2099, 6, 2, tzinfo=UTC)),
    ),
)
def test_banner_reset_rejects_unzoned_unknown_and_non_future_times(
    text: str, now: datetime
) -> None:
    assert claude_events.banner_reset(text, ANCHOR, now) is None


@pytest.mark.parametrize(
    "anchor",
    (datetime(2095, 1, 10, tzinfo=UTC), datetime(2096, 3, 10, tzinfo=UTC)),
    ids=("non_leap_anchor_year", "leap_day_already_passed"),
)
def test_banner_reset_never_skips_invalid_year_to_later_leap_day(
    anchor: datetime,
) -> None:
    now = datetime(2090, 1, 1, tzinfo=UTC)
    text = "resets Feb 29 at 9am (UTC)"
    assert claude_events.banner_reset(text, anchor, now) is None


def test_banner_applies_after_credible_then_resetless_rejection(
    driver: ClaudeDriver,
) -> None:
    credible = int(datetime(2099, 6, 1, 12, tzinfo=UTC).timestamp())
    observations = (
        *rejected_event(driver, credible),
        *rejected_event(driver, None),
        *failed_result(driver, PRAGUE_BANNER, "2099-06-01T10:00:00Z"),
    )
    started = of_type(observations, ObservationType.RATE_LIMIT_STARTED)
    banner_started = [o for o in started if o.payload.get("detail") == PRAGUE_BANNER]
    assert len(banner_started) == 1
    assert banner_started[0].payload["reset_at"] == "2099-06-01T18:10:00Z"
    summary = driver.summarize(observations, 1)
    assert summary.failure_class == "rate_limit"
    assert summary.rate_limit_reset_at == datetime(2099, 6, 1, 18, 10, tzinfo=UTC)


def test_banner_after_credible_rejection_is_ignored_while_only_warned(
    driver: ClaudeDriver,
) -> None:
    observations = (
        *limit_event(driver, "rejected"),
        *limit_event(driver, "allowed_warning"),
        *failed_result(driver, PRAGUE_BANNER, "2099-06-01T10:00:00Z"),
    )
    started = of_type(observations, ObservationType.RATE_LIMIT_STARTED)
    assert [o.payload["reset_at"] for o in started] == ["2100-01-01T00:00:00Z"]
    assert not [o for o in started if o.payload.get("detail") == PRAGUE_BANNER]
    summary = driver.summarize(observations, 1)
    assert summary.failure_class == "rate_limit"
    assert summary.rate_limit_reset_at == FAR_RESET


def test_banner_after_cleared_rejection_starts_new_limit_with_banner_reset(
    driver: ClaudeDriver,
) -> None:
    observations = (
        *limit_event(driver, "rejected"),
        *limit_event(driver, "allowed"),
        *failed_result(driver, PRAGUE_BANNER, "2099-06-01T10:00:00Z"),
    )
    started = of_type(observations, ObservationType.RATE_LIMIT_STARTED)
    banner_started = [o for o in started if o.payload.get("detail") == PRAGUE_BANNER]
    assert [o.payload["reset_at"] for o in banner_started] == ["2099-06-01T18:10:00Z"]
    summary = driver.summarize(observations, 1)
    assert summary.failure_class == "rate_limit"
    assert summary.rate_limit_reset_at == datetime(2099, 6, 1, 18, 10, tzinfo=UTC)


@pytest.mark.parametrize("status", ("allowed_warning", "allowed"))
def test_banner_after_lone_non_rejected_event_schedules_banner_reset(
    driver: ClaudeDriver, status: str
) -> None:
    observations = (
        *limit_event(driver, status),
        *failed_result(driver, PRAGUE_BANNER, "2099-06-01T10:00:00Z"),
    )
    started = of_type(observations, ObservationType.RATE_LIMIT_STARTED)
    assert [(o.payload["reset_at"], o.payload["detail"]) for o in started] == [
        ("2099-06-01T18:10:00Z", PRAGUE_BANNER)
    ]
    summary = driver.summarize(observations, 1)
    assert summary.failure_class == "rate_limit"
    assert summary.rate_limit_reset_at == datetime(2099, 6, 1, 18, 10, tzinfo=UTC)


@pytest.mark.parametrize(
    "resets_at", (None, 946684800), ids=("missing_reset", "past_reset")
)
def test_banner_reset_applies_after_rejection_without_credible_reset(
    driver: ClaudeDriver, resets_at: int | None
) -> None:
    observations = (
        *rejected_event(driver, resets_at),
        *failed_result(driver, PRAGUE_BANNER, "2099-06-01T10:00:00Z"),
    )
    started = of_type(observations, ObservationType.RATE_LIMIT_STARTED)
    banner_started = [o for o in started if o.payload.get("detail") == PRAGUE_BANNER]
    assert len(banner_started) == 1
    assert banner_started[0].payload["reset_at"] == "2099-06-01T18:10:00Z"
    summary = driver.summarize(observations, 1)
    assert summary.failure_class == "rate_limit"
    assert summary.rate_limit_reset_at == datetime(2099, 6, 1, 18, 10, tzinfo=UTC)


def test_dated_banner_schedules_multi_day_reset(driver: ClaudeDriver) -> None:
    detail = "You've hit your weekly limit · resets Sep 20 at 11am (Europe/Prague)"
    observations = failed_result(driver, detail, "2099-06-01T10:00:00Z")
    (started,) = of_type(observations, ObservationType.RATE_LIMIT_STARTED)
    assert started.payload["reset_at"] == "2099-09-20T09:00:00Z"
    summary = driver.summarize(observations, 1)
    assert summary.rate_limit_reset_at == datetime(2099, 9, 20, 9, tzinfo=UTC)


@pytest.mark.parametrize(
    ("text", "anchor", "expected"),
    (
        ("resets Sep 20 at 11am (Europe/Prague)", ANCHOR, "2099-09-20T09:00:00Z"),
        ("resets Jan 5 at 9am (Europe/Prague)", ANCHOR, "2100-01-05T08:00:00Z"),
        (
            "resets Sep 20 at 11am (Europe/Prague)",
            WINTER_ANCHOR,
            "2099-09-20T09:00:00Z",
        ),
        ("resets sep 20 at 11am (Europe/Prague)", ANCHOR, "2099-09-20T09:00:00Z"),
        ("resets SEP 20 at 11am (Europe/Prague)", ANCHOR, "2099-09-20T09:00:00Z"),
        ("resets Jun 1 at 11am (UTC)", ANCHOR, "2099-06-01T11:00:00Z"),
        ("resets Jun 1 at 10am (UTC)", ANCHOR, "2100-06-01T10:00:00Z"),
        ("resets Jun 1 at 9am (UTC)", ANCHOR, "2100-06-01T09:00:00Z"),
        ("resets Jan 5 at 9am (UTC)", ANCHOR, "2100-01-05T09:00:00Z"),
        ("resets Jan 5 at 9am (UTC)", WINTER_ANCHOR, "2100-01-05T09:00:00Z"),
        ("resets Dec 1 at 9:05pm (UTC)", ANCHOR, "2099-12-01T21:05:00Z"),
        ("resets Dec 31 at 12am (UTC)", ANCHOR, "2099-12-31T00:00:00Z"),
        (
            "resets Dec 31 at 11pm (America/New_York)",
            datetime(2100, 1, 1, 2, tzinfo=UTC),
            "2100-01-01T04:00:00Z",
        ),
        ("resets Jan 31 at 9am (UTC)", ANCHOR, "2100-01-31T09:00:00Z"),
        ("resets Feb 28 at 9am (UTC)", ANCHOR, "2100-02-28T09:00:00Z"),
        ("resets Mar 31 at 9am (UTC)", ANCHOR, "2100-03-31T09:00:00Z"),
        ("resets Apr 30 at 9am (UTC)", ANCHOR, "2100-04-30T09:00:00Z"),
        ("resets May 31 at 9am (UTC)", ANCHOR, "2100-05-31T09:00:00Z"),
        ("resets Jun 30 at 9am (UTC)", ANCHOR, "2099-06-30T09:00:00Z"),
        ("resets Jul 31 at 9am (UTC)", ANCHOR, "2099-07-31T09:00:00Z"),
        ("resets Aug 31 at 9am (UTC)", ANCHOR, "2099-08-31T09:00:00Z"),
        ("resets Sep 30 at 9am (UTC)", ANCHOR, "2099-09-30T09:00:00Z"),
        ("resets Oct 31 at 9am (UTC)", ANCHOR, "2099-10-31T09:00:00Z"),
        ("resets Nov 30 at 9am (UTC)", ANCHOR, "2099-11-30T09:00:00Z"),
        ("resets Dec 31 at 9am (UTC)", ANCHOR, "2099-12-31T09:00:00Z"),
        (
            "resets Feb 29 at 9am (UTC)",
            datetime(2096, 1, 10, tzinfo=UTC),
            "2096-02-29T09:00:00Z",
        ),
        (
            "resets Feb 28 at 9am (UTC)",
            datetime(2095, 3, 1, tzinfo=UTC),
            "2096-02-28T09:00:00Z",
        ),
    ),
)
def test_banner_reset_resolves_dated_banner_in_anchor_local_year(
    text: str, anchor: datetime, expected: str
) -> None:
    now = datetime(2090, 1, 1, tzinfo=UTC)
    assert claude_events.banner_reset(text, anchor, now) == expected


@pytest.mark.parametrize(
    ("text", "now"),
    (
        ("resets Feb 30 at 9am (UTC)", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets Sep 31 at 9am (UTC)", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets Sep 0 at 9am (UTC)", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets Sep 32 at 9am (UTC)", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets Feb 29 at 9am (UTC)", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets Sep 20 at 13pm (UTC)", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets Sep 20 at 9:60am (UTC)", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets Sept 20 at 9am (UTC)", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets Foo 20 at 9am (UTC)", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets Sep 20 at 9am (Mars/Olympus)", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets Sep 20 at 9am", datetime(2099, 1, 1, tzinfo=UTC)),
        ("resets Sep 20 at 9am (UTC)", datetime(2099, 9, 20, 9, tzinfo=UTC)),
        ("resets Sep 20 at 9am (UTC)", datetime(2099, 9, 21, tzinfo=UTC)),
    ),
)
def test_banner_reset_rejects_invalid_or_non_future_dated_banners(
    text: str, now: datetime
) -> None:
    assert claude_events.banner_reset(text, ANCHOR, now) is None
