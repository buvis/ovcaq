import gc
import hashlib
import json
import tracemalloc
from collections.abc import Iterator, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import LaunchRequest
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import Observation

FIXTURE = Path(__file__).parents[1] / "fixtures/codex/v1/lanes.jsonl"
FAKE_CREDENTIAL = "sk-" + "SyntheticCredentialForLaneTestOnly123456789012"


@pytest.fixture
def driver() -> CodexDriver:
    settings = AgentSettings(
        name="codex",
        command=("fixture-wrapper", "--literal-prefix", "fixture-launcher"),
        tiers={"standard": "fixture-model", "premium": "fixture-large"},
        environment={"TASK_MODE": "fixture"},
        options={},
    )
    result = CodexDriver(settings, run_id="lane-run")
    result.decode(json.dumps({"type": "thread.started", "thread_id": "parent"}))
    return result


def collab_record(
    *,
    item_id: str = "collab-1",
    receiver: str = "child-1",
    child_status: str = "running",
    tool: str = "spawn_agent",
    event: str = "item.started",
    status: str = "in_progress",
    message: str | None = "Receiver evidence",
    prompt: str | None = "Inspect receiver",
) -> dict[str, object]:
    return {
        "type": event,
        "item": {
            "id": item_id,
            "type": "collab_tool_call",
            "tool": tool,
            "sender_thread_id": "parent",
            "receiver_thread_ids": [receiver],
            "prompt": prompt,
            "agents_states": {receiver: {"status": child_status, "message": message}},
            "status": status,
        },
    }


def decode_record(
    driver: CodexDriver, record: dict[str, object]
) -> tuple[Observation, ...]:
    return driver.decode(json.dumps(record))


def lanes(observations: tuple[Observation, ...]) -> list[Observation]:
    return [value for value in observations if value.type.startswith("lane.")]


def tools(observations: tuple[Observation, ...]) -> list[Observation]:
    return [value for value in observations if value.type.startswith("tool.")]


def assert_raw(observations: tuple[Observation, ...], raw: str) -> None:
    unknown = [value for value in observations if value.type == "raw.unknown"]
    assert unknown
    for value in unknown:
        assert value.payload["raw_sha256"] == hashlib.sha256(raw.encode()).hexdigest()
        assert isinstance(value.payload["reason"], str)
        assert value.payload["reason"]
        assert isinstance(value.payload["preview"], str)
        assert len(value.payload["preview"]) <= 512


def identity_text(observations: tuple[Observation, ...]) -> str:
    return " ".join(
        str(value.payload) for value in observations if value.type == "raw.unknown"
    )


def assert_overflow_evidence(observations: tuple[Observation, ...], raw: str) -> None:
    assert_raw(observations, raw)
    for value in observations:
        if value.type == "raw.unknown":
            preview = value.payload["preview"]
            assert "overflow-item" in preview
            assert "overflow-lane" in preview
            assert FAKE_CREDENTIAL not in preview
            assert "[REDACTED]" in preview


def fill_active_identities(driver: CodexDriver, count: int) -> None:
    for index in range(count):
        observations = decode_record(
            driver,
            collab_record(item_id=f"active-item-{index}", receiver=f"active-{index}"),
        )
        assert not any(value.type == "raw.unknown" for value in observations)
        assert {value.lane_id for value in lanes(observations)} == {f"active-{index}"}


def payload_strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from payload_strings(item)
    elif isinstance(value, Sequence):
        for item in value:
            yield from payload_strings(item)


def stream_fixed_width_identities(driver: CodexDriver, start: int, count: int) -> None:
    for index in range(start, start + count):
        receiver = f"receiver-{index:016d}"
        observations = decode_record(
            driver,
            collab_record(item_id=f"item-{index:016d}", receiver=receiver),
        )
        assert {value.lane_id for value in lanes(observations)} == {receiver}
        del observations
    gc.collect()


@pytest.mark.parametrize("tool", ["spawn_agent", "send_input", "wait", "close_agent"])
@pytest.mark.parametrize(
    ("event", "status", "expected"),
    [
        ("item.started", "in_progress", "tool.started"),
        ("item.completed", "completed", "tool.completed"),
        ("item.completed", "failed", "tool.failed"),
    ],
)
def test_projects_native_collab_tool_lifecycle(
    driver: CodexDriver, tool: str, event: str, status: str, expected: str
) -> None:
    prompt = f"Inspect native receiver {uuid4().hex}"
    observations = decode_record(
        driver,
        collab_record(
            tool=tool,
            event=event,
            status=status,
            prompt=prompt + " " + FAKE_CREDENTIAL + "\x00",
        ),
    )
    projected = tools(observations)
    assert len(projected) == 1
    assert projected[0].type == expected
    assert projected[0].payload["tool_id"] == "collab-1"
    assert isinstance(projected[0].payload["name"], str)
    assert projected[0].payload["name"]
    assert isinstance(projected[0].payload["detail"], str)
    assert prompt in projected[0].payload["detail"]
    assert "[REDACTED]" in projected[0].payload["detail"]
    assert FAKE_CREDENTIAL not in projected[0].payload["detail"]


def test_fixture_receiver_mismatch_preserves_raw_evidence_without_lanes(
    driver: CodexDriver,
) -> None:
    for raw in FIXTURE.read_text().splitlines():
        if json.loads(raw)["type"] not in {"item.started", "item.completed"}:
            continue
        observations = driver.decode(raw)
        assert not lanes(observations)
        assert_raw(observations, raw)


@pytest.mark.parametrize("child_status", ["pending_init", "running"])
def test_attributed_active_receiver_starts_with_current_thread_and_receipt_time(
    driver: CodexDriver, child_status: str
) -> None:
    record = collab_record(child_status=child_status)
    record["timestamp"] = "2000-01-01T00:00:00Z"
    before = datetime.now(UTC)
    observations = decode_record(driver, record)
    after = datetime.now(UTC)
    projected = lanes(observations)
    assert len(projected) == 1
    assert projected[0].type == "lane.started"
    assert projected[0].lane_id == "child-1"
    assert isinstance(projected[0].payload["label"], str)
    assert projected[0].payload["label"]
    assert "Receiver evidence" in projected[0].payload["detail"]
    for value in observations:
        assert value.protocol_version == 1
        assert value.provider == "codex"
        assert value.run_id == "lane-run"
        assert value.session_id == "parent"
        assert value.timestamp.utcoffset() == timedelta(0)
        assert before <= value.timestamp <= after


def test_receiver_progress_and_duplicate_states_keep_one_lane_identity(
    driver: CodexDriver,
) -> None:
    initial_message = f"Receiver initializes {uuid4().hex}"
    update_message = f"Receiver advances {uuid4().hex}"
    pending = collab_record(child_status="pending_init", message=initial_message)
    started = lanes(decode_record(driver, pending))
    assert [value.type for value in started] == ["lane.started"]
    assert initial_message in started[0].payload["detail"]
    assert update_message not in started[0].payload["detail"]
    running = collab_record(event="item.updated", message=update_message)
    progress = lanes(decode_record(driver, running))
    assert len(progress) == 1
    assert progress[0].type == "lane.progress"
    assert progress[0].lane_id == "child-1"
    assert update_message in progress[0].payload["detail"]
    assert initial_message not in progress[0].payload["detail"]
    duplicate = lanes(decode_record(driver, running))
    assert all(value.type == "lane.progress" for value in duplicate)
    assert all(value.lane_id == "child-1" for value in duplicate)
    assert all(update_message in value.payload["detail"] for value in duplicate)


@pytest.mark.parametrize(
    ("child_status", "tool_status", "expected_lane", "expected_tool"),
    [
        ("completed", "failed", "lane.completed", "tool.failed"),
        ("errored", "completed", "lane.failed", "tool.completed"),
    ],
)
def test_receiver_terminal_status_is_independent_of_tool_status(
    driver: CodexDriver,
    child_status: str,
    tool_status: str,
    expected_lane: str,
    expected_tool: str,
) -> None:
    decode_record(driver, collab_record())
    observations = decode_record(
        driver,
        collab_record(
            event="item.completed", status=tool_status, child_status=child_status
        ),
    )
    assert [value.type for value in tools(observations)] == [expected_tool]
    assert [value.type for value in lanes(observations)] == [expected_lane]
    assert lanes(observations)[0].lane_id == "child-1"
    assert "Receiver evidence" in lanes(observations)[0].payload["detail"]


@pytest.mark.parametrize("child_status", ["interrupted", "shutdown", "not_found"])
def test_unsupported_child_terminal_states_stay_raw_without_success(
    driver: CodexDriver, child_status: str
) -> None:
    raw = json.dumps(
        collab_record(
            event="item.completed", status="completed", child_status=child_status
        )
    )
    observations = driver.decode(raw)
    assert_raw(observations, raw)
    assert not lanes(observations)
    assert [value.type for value in tools(observations)] == ["tool.completed"]


@pytest.mark.parametrize(
    ("receivers", "states"),
    [
        ([], {"child-1": {"status": "completed", "message": "Evidence"}}),
        (["child-1"], {}),
        (["child-1"], {"unrelated": {"status": "completed", "message": "Evidence"}}),
    ],
    ids=["no-receiver", "no-agent-state", "mismatched-agent-state"],
)
def test_missing_receiver_attribution_stays_raw(
    driver: CodexDriver, receivers: list[str], states: dict[str, object]
) -> None:
    record = collab_record(event="item.completed", status="completed")
    record["item"]["receiver_thread_ids"] = receivers
    record["item"]["agents_states"] = states
    raw = json.dumps(record)
    observations = driver.decode(raw)
    assert_raw(observations, raw)
    assert not lanes(observations)


def test_multiple_receivers_keep_separate_attribution_and_actual_status(
    driver: CodexDriver,
) -> None:
    message_a = f"Receiver A evidence {uuid4().hex}"
    message_b = f"Receiver B evidence {uuid4().hex}"
    record = collab_record()
    record["item"]["receiver_thread_ids"] = ["child-a", "child-b"]
    record["item"]["agents_states"] = {
        "child-a": {"status": "running", "message": message_a},
        "child-b": {"status": "errored", "message": message_b},
    }
    projected = {value.lane_id: value for value in lanes(decode_record(driver, record))}
    assert set(projected) == {"child-a", "child-b"}
    assert projected["child-a"].type == "lane.started"
    assert projected["child-b"].type == "lane.failed"
    assert message_a in projected["child-a"].payload["detail"]
    assert message_b not in projected["child-a"].payload["detail"]
    assert message_b in projected["child-b"].payload["detail"]
    assert message_a not in projected["child-b"].payload["detail"]


@pytest.mark.parametrize(
    ("child_status", "expected_lane"),
    [("completed", "lane.completed"), ("errored", "lane.failed")],
)
@pytest.mark.parametrize(
    "bad_state",
    [
        {"status": "interrupted", "message": "Invalid sibling evidence"},
        {"status": "running", "message": ["Invalid sibling evidence"]},
    ],
    ids=["unsupported-status", "malformed-message"],
)
@pytest.mark.parametrize("bad_first", [False, True], ids=["valid-first", "bad-first"])
def test_bad_receiver_sibling_preserves_attributed_native_terminal(
    driver: CodexDriver,
    child_status: str,
    expected_lane: str,
    bad_state: dict[str, object],
    bad_first: bool,
) -> None:
    message = f"Valid receiver terminal {uuid4().hex}"
    receivers = ["valid-child", "bad-child"]
    if bad_first:
        receivers.reverse()
    states = {
        "valid-child": {"status": child_status, "message": message},
        "bad-child": bad_state,
    }
    record = collab_record(event="item.completed", status="completed")
    record["item"]["receiver_thread_ids"] = receivers
    record["item"]["agents_states"] = {
        receiver: states[receiver] for receiver in receivers
    }
    raw = json.dumps(record)
    observations = driver.decode(raw)
    projected = lanes(observations)
    assert len(projected) == 1
    assert projected[0].lane_id == "valid-child"
    assert projected[0].type == expected_lane
    assert message in projected[0].payload["detail"]
    assert "Invalid sibling evidence" not in projected[0].payload["detail"]
    assert [value.type for value in tools(observations)] == ["tool.completed"]
    assert tools(observations)[0].payload["tool_id"] == "collab-1"
    assert_raw(observations, raw)
    for value in observations:
        if value.type == "raw.unknown":
            assert "collab-1" in value.payload["preview"]
            assert "valid-child" in value.payload["preview"]
            assert "bad-child" in value.payload["preview"]


def test_out_of_order_receiver_update_preserves_child_progress_evidence(
    driver: CodexDriver,
) -> None:
    raw = json.dumps(collab_record(event="item.updated"))
    observations = driver.decode(raw)
    projected = lanes(observations)
    evidence = next(
        value
        for value in observations
        if value.type in {"lane.started", "lane.progress", "raw.unknown"}
    )
    if evidence.type == "raw.unknown":
        assert (
            evidence.payload["raw_sha256"] == hashlib.sha256(raw.encode()).hexdigest()
        )
        assert isinstance(evidence.payload["reason"], str)
        assert evidence.payload["reason"]
        assert isinstance(evidence.payload["preview"], str)
        assert len(evidence.payload["preview"]) <= 512
    else:
        assert evidence.lane_id == "child-1"
        assert "Receiver evidence" in evidence.payload["detail"]
    assert all(value.lane_id == "child-1" for value in projected)
    assert all(value.type in {"lane.started", "lane.progress"} for value in projected)
    assert all("Receiver evidence" in value.payload["detail"] for value in projected)
    assert not any(
        value.type in {"lane.completed", "lane.failed"} for value in observations
    )


def test_receiver_evidence_is_sanitized_and_bounded(driver: CodexDriver) -> None:
    message = "Receiver evidence " + FAKE_CREDENTIAL + "\x00" + "x" * 64000
    observations = decode_record(driver, collab_record(message=message))
    projected = lanes(observations)
    assert len(projected) == 1
    detail = projected[0].payload["detail"]
    assert isinstance(detail, str)
    assert "Receiver evidence" in detail
    assert FAKE_CREDENTIAL not in detail
    assert "[REDACTED]" in detail
    assert len(detail) < len(message)
    assert FAKE_CREDENTIAL not in str([value.payload for value in observations])


@pytest.mark.parametrize("fallback", ["unsupported-child", "invalid-json"])
def test_fallback_payloads_redact_credentials_preserving_raw_digest(
    driver: CodexDriver, fallback: str
) -> None:
    record = collab_record(
        child_status="interrupted",
        prompt="Fallback evidence " + FAKE_CREDENTIAL + "\x00",
    )
    raw = json.dumps(record)
    if fallback == "invalid-json":
        raw = "\x1b" + raw
    observations = driver.decode(raw)
    assert_raw(observations, raw)
    assert not lanes(observations)
    for value in observations:
        for text in payload_strings(value.payload):
            assert FAKE_CREDENTIAL not in text
    previews = [
        value.payload["preview"]
        for value in observations
        if value.type == "raw.unknown"
    ]
    assert all("[REDACTED]" in preview for preview in previews)


@pytest.mark.parametrize(
    "malformation", ["unknown-status", "null-state", "bad-message"]
)
def test_malformed_child_state_is_raw_and_does_not_poison_later_evidence(
    driver: CodexDriver, malformation: str
) -> None:
    record = collab_record()
    states = {
        "unknown-status": {"status": "future_status", "message": "Evidence"},
        "null-state": None,
        "bad-message": {"status": "running", "message": ["not a string"]},
    }
    record["item"]["agents_states"] = {"child-1": states[malformation]}
    raw = json.dumps(record)
    observations = driver.decode(raw)
    assert_raw(observations, raw)
    assert not lanes(observations)
    repaired = lanes(decode_record(driver, collab_record()))
    assert len(repaired) == 1
    assert repaired[0].type == "lane.started"
    assert repaired[0].lane_id == "child-1"


def test_shared_identity_budget_emits_visible_gap_at_4097th_identity(
    driver: CodexDriver,
) -> None:
    fill_active_identities(driver, 2048)
    raw = json.dumps(
        collab_record(
            item_id="overflow-item",
            receiver="overflow-lane",
            prompt="Overflow evidence " + FAKE_CREDENTIAL + "\x00",
        )
    )
    overflow = driver.decode(raw)
    assert_overflow_evidence(overflow, raw)
    gap = identity_text(overflow)
    assert "active-item-0" in gap
    assert "active-0" in gap
    assert {value.lane_id for value in lanes(overflow)} == {"overflow-lane"}


def test_identity_eviction_prefers_terminal_over_older_active_identities(
    driver: CodexDriver,
) -> None:
    fill_active_identities(driver, 1)
    decode_record(
        driver,
        collab_record(
            item_id="terminal-item",
            receiver="terminal-lane",
            event="item.completed",
            status="completed",
            child_status="completed",
        ),
    )
    for index in range(2046):
        observations = decode_record(
            driver,
            collab_record(item_id=f"filler-item-{index}", receiver=f"filler-{index}"),
        )
        assert not any(value.type == "raw.unknown" for value in observations)
    raw = json.dumps(
        collab_record(
            item_id="overflow-item",
            receiver="overflow-lane",
            prompt="Overflow evidence " + FAKE_CREDENTIAL + "\x00",
        )
    )
    overflow = driver.decode(raw)
    assert_overflow_evidence(overflow, raw)
    gap = identity_text(overflow)
    assert "terminal-item" in gap
    assert "terminal-lane" in gap
    assert "active-item-0" not in gap
    assert "active-0" not in gap
    progress = lanes(
        decode_record(
            driver,
            collab_record(
                item_id="active-item-0", receiver="active-0", event="item.updated"
            ),
        )
    )
    assert [value.type for value in progress] == ["lane.progress"]


def test_duplicate_evidence_does_not_consume_extra_identity_capacity(
    driver: CodexDriver,
) -> None:
    for index in range(2048):
        record = collab_record(item_id=f"item-{index}", receiver=f"child-{index}")
        for observations in (
            decode_record(driver, record),
            decode_record(driver, record),
        ):
            assert not any(value.type == "raw.unknown" for value in observations)
            assert all(
                value.lane_id == f"child-{index}" for value in lanes(observations)
            )
            assert not any(
                value.type in {"lane.completed", "lane.failed"}
                for value in observations
            )


def test_retained_memory_plateaus_after_identity_budget_saturation(
    driver: CodexDriver,
) -> None:
    already_tracing = tracemalloc.is_tracing()
    tracemalloc.start()
    try:
        gc.collect()
        baseline = tracemalloc.get_traced_memory()[0]
        stream_fixed_width_identities(driver, 0, 4096)
        saturated = tracemalloc.get_traced_memory()[0]
        saturated_allocation = saturated - baseline
        assert saturated_allocation > 0
        stream_fixed_width_identities(driver, 4096, 32768)
        sustained = tracemalloc.get_traced_memory()[0]
        assert sustained - saturated <= saturated_allocation
    finally:
        if not already_tracing:
            tracemalloc.stop()


def test_launch_construction_preserves_configured_command_and_request(
    driver: CodexDriver, tmp_path: Path
) -> None:
    request = LaunchRequest(
        root=tmp_path,
        phase="build",
        prompt=f"Inspect fixture task {uuid4().hex}",
        model="fixture-model",
        effort=None,
        timeout_seconds=30,
        session_dir=tmp_path / "session",
    )
    launch = driver.build_launch(request)
    assert launch.argv[:3] == (
        "fixture-wrapper",
        "--literal-prefix",
        "fixture-launcher",
    )
    assert request.prompt in launch.argv
    assert request.model in launch.argv
    assert launch.cwd == request.root
    assert launch.env["TASK_MODE"] == "fixture"
    assert launch.raw_format == "codex-exec-json-v1"


def test_launch_resets_remembered_receiver_identity_and_capacity(
    driver: CodexDriver, tmp_path: Path
) -> None:
    fill_active_identities(driver, 2048)
    request = LaunchRequest(
        root=tmp_path,
        phase="build",
        prompt="Fixture-only launch construction",
        model="fixture-model",
        effort=None,
        timeout_seconds=30,
        session_dir=tmp_path / "session",
    )
    driver.build_launch(request)
    driver.decode(json.dumps({"type": "thread.started", "thread_id": "new-parent"}))
    observations = decode_record(
        driver, collab_record(item_id="active-item-0", receiver="active-0")
    )
    assert [value.type for value in tools(observations)] == ["tool.started"]
    assert [value.type for value in lanes(observations)] == ["lane.started"]
    assert all(value.session_id == "new-parent" for value in observations)
    assert not any(value.type == "raw.unknown" for value in observations)
    new = decode_record(driver, collab_record(item_id="new-item", receiver="new-lane"))
    assert not any(value.type == "raw.unknown" for value in new)
    assert {value.lane_id for value in lanes(new)} == {"new-lane"}
