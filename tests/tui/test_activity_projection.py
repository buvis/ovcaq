from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from ovcaq.events.model import Observation, observation_from_record, observation_record
from ovcaq.events.tail import JsonlFollower, TailBatch
from ovcaq.tui.model import MAX_ACTIVITY

from . import test_model
from .model_support import Projection
from .test_rework_activity import FIXTURES, _decoder, _event

projection = test_model.projection
_FOLLOWER_READ = JsonlFollower.read


def _poll(
    projection: Projection, *events: Observation, reset: bool = False
) -> tuple[str | None, ...]:
    projection.batches.append(TailBatch(events, (), reset, False, True))
    return tuple(item.detail for item in projection.poll().activity)


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"text": "visible text", "detail": "fallback"}, "visible text"),
        ({"text": None, "detail": "fallback"}, "fallback"),
        ({"detail": "fallback"}, "fallback"),
        ({"text": "", "detail": "fallback"}, ""),
        ({"text": ""}, ""),
        ({"text": None, "detail": None}, None),
    ],
    ids=[
        "text",
        "null-text",
        "absent-text",
        "empty-text",
        "empty-without-detail",
        "no-detail",
    ],
)
def test_activity_uses_non_null_text_before_detail(
    projection: Projection, payload: dict[str, object], expected: str | None
) -> None:
    event = _event("codex", "activity.message", {"kind": "error", **payload})

    assert _poll(projection, event) == (expected,)
    assert tuple(item.detail for item in projection.poll().activity) == (expected,)


@pytest.mark.parametrize(
    "identity",
    [{}, {"message_id": None}, {"message_id": ""}, {"message_id": " \t "}],
    ids=["absent", "null", "empty", "whitespace"],
)
@pytest.mark.parametrize("kind", ["text", "thinking", "error"])
def test_identical_messages_without_real_ids_remain_distinct_across_polls(
    projection: Projection, identity: dict[str, object], kind: str
) -> None:
    event = _event(
        "codex", "activity.message", {"kind": kind, "text": "retry", **identity}
    )

    assert _poll(projection, event, event) == ("retry", "retry")
    assert tuple(item.detail for item in projection.poll().activity) == (
        "retry",
        "retry",
    )
    assert _poll(projection, event) == ("retry", "retry", "retry")
    assert tuple(item.detail for item in projection.poll().activity) == (
        "retry",
        "retry",
        "retry",
    )


def test_decoded_claude_text_and_thinking_share_the_same_update_identity(
    projection: Projection,
) -> None:
    decoder = _decoder("claude")
    healthy = (FIXTURES / "claude" / "v1" / "healthy.jsonl").read_text().splitlines()
    text, thinking = (
        replace(event, session_id="session-1")
        for event in decoder.decode(healthy[1])
        if event.type.value == "activity.message"
    )

    assert text.payload["kind"] == "text"
    assert thinking.payload["kind"] == "thinking"
    assert text.payload["message_id"] == thinking.payload["message_id"] == "message-1"
    assert _poll(projection, text) == ("Working on the sanitized fixture.",)
    assert projection.poll().activity[0].label == "text"
    # Known R1 limitation: later blocks replace earlier blocks with the same ID.
    assert _poll(projection, thinking) == ("Check the public contract.",)
    assert projection.poll().activity[0].label == "thinking"
    assert _poll(projection, text, thinking, reset=True) == (
        "Check the public contract.",
    )


@pytest.mark.parametrize("provider", ["claude", "codex"])
def test_real_message_updates_replace_one_item_and_move_it_to_most_recent(
    projection: Projection, provider: str
) -> None:
    first = _event(
        provider,
        "activity.message",
        {"kind": "text", "message_id": "first", "text": "old"},
    )
    second = _event(
        provider,
        "activity.message",
        {"kind": "text", "message_id": "second", "text": "other"},
    )
    updated = replace(
        first, payload={**first.payload, "kind": "thinking", "text": "latest"}
    )

    assert _poll(projection, first, second) == ("old", "other")
    assert _poll(projection, updated) == ("other", "latest")
    assert tuple(item.label for item in projection.poll().activity) == (
        "text",
        "thinking",
    )
    assert tuple(item.detail for item in projection.poll().activity) == (
        "other",
        "latest",
    )
    assert _poll(projection, updated) == ("other", "latest")


@pytest.mark.parametrize("marker", ["completed", "failed"])
def test_decoded_idless_errors_survive_repeated_errors_and_turn_markers(
    projection: Projection, marker: str
) -> None:
    decoder = _decoder("codex")
    healthy = (FIXTURES / "codex" / "v1" / "healthy.jsonl").read_text().splitlines()
    failed = (FIXTURES / "codex" / "v1" / "rate-limited.jsonl").read_text().splitlines()
    errors = tuple(
        replace(event, session_id="session-1") for event in decoder.decode(healthy[3])
    )
    turns = tuple(
        replace(event, session_id="session-1") for event in decoder.decode(healthy[1])
    )
    markers = tuple(
        replace(event, session_id="session-1")
        for event in decoder.decode(
            healthy[-1] if marker == "completed" else failed[-1]
        )
    )
    detail = "Temporary stream interruption; retrying."

    assert _poll(projection, *errors) == (detail,)
    assert _poll(projection, *errors, *markers) == (detail, detail)
    assert tuple(item.detail for item in projection.poll().activity) == (detail, detail)
    _poll(projection, *turns)
    activity = projection.poll().activity
    assert len(activity) == 3
    assert tuple(item.detail for item in activity[:2]) == (detail, detail)
    assert activity[-1].label == "turn"


@pytest.mark.parametrize("window", ["five_hour", "seven_day"])
def test_decoded_claude_warnings_keep_detail_and_remain_distinct(
    projection: Projection, window: str
) -> None:
    decoder = _decoder("claude")
    frame = json.dumps(
        {
            "type": "rate_limit_event",
            "session_id": "session-1",
            "rate_limit_info": {
                "status": "allowed_warning",
                "resetsAt": 4102444800,
                "rateLimitType": window,
            },
        }
    )
    (warning,) = decoder.decode(frame)
    assert warning.type.value == "activity.message"
    assert warning.payload["kind"] == "rate_limit_warning"
    detail = warning.payload["detail"]
    assert isinstance(detail, str)
    assert "allowed_warning" in detail
    assert window in detail
    unrelated = _event(
        "claude", "activity.message", {"kind": "text", "text": "unrelated message"}
    )

    assert _poll(projection, warning) == (detail,)
    assert projection.poll().activity[0].label == "rate_limit_warning"
    assert _poll(projection, unrelated) == (detail, "unrelated message")
    assert _poll(projection, *decoder.decode(frame)) == (
        detail,
        "unrelated message",
        detail,
    )
    assert tuple(item.detail for item in projection.poll().activity) == (
        detail,
        "unrelated message",
        detail,
    )


@pytest.mark.parametrize("real_ids", [False, True])
def test_activity_evicts_oldest_observations_at_retained_bound(
    projection: Projection, real_ids: bool
) -> None:
    events = tuple(
        _event(
            "codex",
            "activity.message",
            {
                "kind": "text",
                "text": f"message-{index}",
                **({"message_id": str(index)} if real_ids else {}),
            },
        )
        for index in range(MAX_ACTIVITY + 3)
    )
    expected = tuple(f"message-{index}" for index in range(3, MAX_ACTIVITY + 3))

    assert _poll(projection, *events) == expected
    assert len(projection.poll().activity) == MAX_ACTIVITY
    assert _poll(projection, events[0]) == (*expected[1:], "message-0")
    assert len(projection.poll().activity) == MAX_ACTIVITY


def test_retained_real_id_update_keeps_bound_and_becomes_most_recent(
    projection: Projection,
) -> None:
    events = tuple(
        _event(
            "codex",
            "activity.message",
            {"kind": "text", "text": str(index), "message_id": str(index)},
        )
        for index in range(MAX_ACTIVITY)
    )
    _poll(projection, *events)
    updated = replace(events[0], payload={**events[0].payload, "text": "latest"})

    assert _poll(projection, updated) == (
        *(str(index) for index in range(1, MAX_ACTIVITY)),
        "latest",
    )
    assert len(projection.poll().activity) == MAX_ACTIVITY


def test_distinct_long_message_ids_are_not_merged_by_display_truncation(
    projection: Projection,
) -> None:
    prefix = "same-prefix-" * 100
    first = _event(
        "codex",
        "activity.message",
        {"kind": "text", "message_id": prefix + "first", "text": "first"},
    )
    second = replace(
        first,
        payload={"kind": "text", "message_id": prefix + "second", "text": "second"},
    )

    assert _poll(projection, first, second) == ("first", "second")
    updated = replace(first, payload={**first.payload, "text": "updated"})
    assert _poll(projection, updated) == ("second", "updated")


def test_real_follower_snapshots_do_not_replay_unchanged_idless_records(
    projection: Projection,
    tmp_path: Path,
) -> None:
    event = _event("codex", "activity.message", {"kind": "error", "detail": "retry"})
    path = tmp_path / "activity.jsonl"
    line = json.dumps(observation_record(event)) + "\n"
    path.write_text(line)
    follower = JsonlFollower(path, observation_from_record)
    try:
        projection.batches.append(_FOLLOWER_READ(follower))
        assert tuple(item.detail for item in projection.poll().activity) == ("retry",)
        projection.batches.append(_FOLLOWER_READ(follower))
        assert tuple(item.detail for item in projection.poll().activity) == ("retry",)
        with path.open("a") as stream:
            stream.write(line)
        projection.batches.append(_FOLLOWER_READ(follower))
        assert tuple(item.detail for item in projection.poll().activity) == (
            "retry",
            "retry",
        )
        projection.batches.append(_FOLLOWER_READ(follower))
        assert tuple(item.detail for item in projection.poll().activity) == (
            "retry",
            "retry",
        )
    finally:
        follower.close()


def test_session_change_resets_activity_before_new_session_observations(
    projection: Projection,
) -> None:
    previous = _event(
        "codex", "activity.message", {"kind": "error", "detail": "previous"}
    )
    current = replace(
        previous, session_id="session-2", payload={"kind": "error", "detail": "current"}
    )
    assert _poll(projection, previous) == ("previous",)
    projection.observation = replace(
        projection.observation, active_session_id="session-2"
    )

    assert _poll(projection, previous, current) == ("current",)
    assert _poll(projection, current) == ("current", "current")
    assert tuple(item.detail for item in projection.poll().activity) == (
        "current",
        "current",
    )


def test_observer_reset_clears_activity_and_replays_distinct_observations(
    projection: Projection,
) -> None:
    stale = _event(
        "codex",
        "activity.message",
        {"kind": "text", "message_id": "same", "text": "stale"},
    )
    anonymous = _event(
        "codex", "activity.message", {"kind": "error", "detail": "retry"}
    )
    replayed = replace(stale, payload={**stale.payload, "text": "replayed"})

    assert _poll(projection, stale, anonymous, anonymous) == ("stale", "retry", "retry")
    assert _poll(projection, replayed, anonymous, reset=True) == ("replayed", "retry")
    assert tuple(item.detail for item in projection.poll().activity) == (
        "replayed",
        "retry",
    )
    assert _poll(projection, anonymous) == ("replayed", "retry", "retry")
    assert _poll(projection, reset=True) == ()
    assert _poll(projection, anonymous) == ("retry",)
