import json
from hashlib import sha256

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import Observation, ObservationType


@pytest.fixture
def driver() -> CodexDriver:
    settings = AgentSettings(
        name="codex",
        command=("fixture-wrapper",),
        tiers={"standard": "fixture-model"},
        environment={},
        options={},
    )
    return CodexDriver(settings, run_id="rework-run")


def decode(driver: CodexDriver, record: dict[str, object]) -> tuple[Observation, ...]:
    return driver.decode(json.dumps(record))


def collab_record(
    child_status: str,
    *,
    tool: str = "spawn_agent",
    receiver: str = "child",
    event_type: str = "item.completed",
    item_type: str = "collab_tool_call",
    status: str = "completed",
) -> dict[str, object]:
    return {
        "type": event_type,
        "item": {
            "id": f"collab-{tool}-{child_status}",
            "type": item_type,
            "tool": tool,
            "sender_thread_id": "parent",
            "receiver_thread_ids": [receiver],
            "agents_states": {
                receiver: {"status": child_status, "message": "Inspect receiver"}
            },
            "status": status,
        },
    }


def start_lane(driver: CodexDriver, receiver: str = "child") -> None:
    observations = decode(
        driver,
        collab_record(
            "running",
            receiver=receiver,
            event_type="item.started",
            status="in_progress",
        ),
    )
    assert [
        observation.lane_id
        for observation in observations
        if observation.type == ObservationType.LANE_STARTED
    ] == [receiver]
    assert not any(
        observation.type == ObservationType.LANE_FAILED for observation in observations
    )


@pytest.mark.parametrize("tool", ["wait", "close_agent"])
@pytest.mark.parametrize("child_status", ["interrupted", "shutdown", "not_found"])
def test_completed_lane_remains_completed_after_close_status(
    driver: CodexDriver, tool: str, child_status: str
) -> None:
    start_lane(driver)
    completed = decode(driver, collab_record("completed", tool="wait"))
    assert [
        observation.lane_id
        for observation in completed
        if observation.type == ObservationType.LANE_COMPLETED
    ] == ["child"]
    assert not any(
        observation.type == ObservationType.LANE_FAILED for observation in completed
    )

    closed = decode(driver, collab_record(child_status, tool=tool))
    assert any(
        observation.type == ObservationType.RAW_UNKNOWN for observation in closed
    )
    assert not any(
        observation.type
        in (ObservationType.LANE_FAILED, ObservationType.LANE_COMPLETED)
        for observation in closed
    )


@pytest.mark.parametrize("tool", ["wait", "close_agent"])
@pytest.mark.parametrize("child_status", ["interrupted", "shutdown", "not_found"])
def test_unfinished_lane_fails_after_close_status(
    driver: CodexDriver, tool: str, child_status: str
) -> None:
    start_lane(driver)

    observations = decode(driver, collab_record(child_status, tool=tool))

    failures = [
        observation
        for observation in observations
        if observation.type == ObservationType.LANE_FAILED
    ]
    assert len(failures) == 1
    assert failures[0].lane_id == "child"
    assert not any(
        observation.type == ObservationType.LANE_COMPLETED
        for observation in observations
    )


@pytest.mark.parametrize("child_status", ["interrupted", "shutdown", "not_found"])
def test_unknown_receiver_close_retains_raw_unknown(
    driver: CodexDriver, child_status: str
) -> None:
    start_lane(driver)

    raw_line = json.dumps(
        collab_record(child_status, tool="close_agent", receiver="unseen")
    )
    observations = driver.decode(raw_line)

    assert any(
        observation.type == ObservationType.RAW_UNKNOWN
        and observation.payload["raw_sha256"] == sha256(raw_line.encode()).hexdigest()
        and observation.payload["preview"] == raw_line[:512]
        for observation in observations
    )
    assert not any(
        observation.type == ObservationType.LANE_FAILED for observation in observations
    )
    known_receiver = decode(driver, collab_record(child_status, tool="close_agent"))
    assert [
        observation.lane_id
        for observation in known_receiver
        if observation.type == ObservationType.LANE_FAILED
    ] == ["child"]


@pytest.mark.parametrize("child_status", ["interrupted", "shutdown", "not_found"])
def test_repeated_close_does_not_fail_lane_again(
    driver: CodexDriver, child_status: str
) -> None:
    start_lane(driver)
    record = collab_record(child_status, tool="close_agent")
    first_close = decode(driver, record)
    assert (
        sum(
            observation.type == ObservationType.LANE_FAILED
            and observation.lane_id == "child"
            for observation in first_close
        )
        == 1
    )

    repeated_close = decode(driver, record)

    assert not any(
        observation.type
        in (ObservationType.LANE_FAILED, ObservationType.LANE_COMPLETED)
        for observation in repeated_close
    )


@pytest.mark.parametrize("tool", ["wait", "close_agent"])
@pytest.mark.parametrize("child_status", ["interrupted", "shutdown", "not_found"])
def test_completed_receiver_does_not_prevent_unfinished_receiver_failure(
    driver: CodexDriver, tool: str, child_status: str
) -> None:
    start_lane(driver, "finished")
    start_lane(driver, "unfinished")
    completed = decode(
        driver, collab_record("completed", tool="wait", receiver="finished")
    )
    assert [
        observation.lane_id
        for observation in completed
        if observation.type == ObservationType.LANE_COMPLETED
    ] == ["finished"]

    closed = decode(
        driver, collab_record(child_status, tool=tool, receiver="unfinished")
    )
    assert [
        observation.lane_id
        for observation in closed
        if observation.type == ObservationType.LANE_FAILED
    ] == ["unfinished"]
    assert not any(
        observation.type == ObservationType.LANE_COMPLETED for observation in closed
    )


@pytest.mark.parametrize(
    "override",
    [{"item_type": "command_execution"}, {"event_type": "thread.started"}],
    ids=["item-type", "event-type"],
)
def test_unrelated_discriminator_does_not_transition_lane(
    driver: CodexDriver, override: dict[str, str]
) -> None:
    start_lane(driver)
    observations = decode(
        driver,
        collab_record("shutdown", tool="close_agent", **override),
    )
    assert not any(
        observation.type
        in (
            ObservationType.LANE_STARTED,
            ObservationType.LANE_PROGRESS,
            ObservationType.LANE_COMPLETED,
            ObservationType.LANE_FAILED,
        )
        for observation in observations
    )
    closed = decode(driver, collab_record("shutdown", tool="close_agent"))
    assert [
        observation.lane_id
        for observation in closed
        if observation.type == ObservationType.LANE_FAILED
    ] == ["child"]


@pytest.mark.parametrize(
    ("terminal_status", "terminal_type"),
    [
        ("completed", ObservationType.LANE_COMPLETED),
        ("errored", ObservationType.LANE_FAILED),
    ],
    ids=["completed", "failed"],
)
@pytest.mark.parametrize("late_status", ["running", "errored", "completed"])
def test_finished_lane_late_update_retains_only_non_lane_observations(
    driver: CodexDriver,
    terminal_status: str,
    terminal_type: ObservationType,
    late_status: str,
) -> None:
    start_lane(driver)
    terminal = decode(driver, collab_record(terminal_status, tool="wait"))
    assert [
        (observation.type, observation.lane_id)
        for observation in terminal
        if observation.type
        in (ObservationType.LANE_COMPLETED, ObservationType.LANE_FAILED)
    ] == [(terminal_type, "child")]

    observations = decode(driver, collab_record(late_status, tool="wait"))

    assert observations
    assert all(
        observation.type
        not in (
            ObservationType.LANE_STARTED,
            ObservationType.LANE_PROGRESS,
            ObservationType.LANE_FAILED,
            ObservationType.LANE_COMPLETED,
            ObservationType.RAW_UNKNOWN,
        )
        for observation in observations
    )
