import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.codex import CodexDriver
from ovcaq.drivers.codex_events import bounded_detail
from ovcaq.events.model import Observation
from ovcaq.events.tail import NormalizedEventWriter

TOKEN = "sk-" + "abcdefghijklmnopqrstuvwxyz0123456789ABCDEF"
CAP_REPRODUCER = "x" * 4080 + " sk-abc\x1b[0mdefghijklmnopqrstuvwxyz0123456789ABCDEF"
SPLIT_DETAILS = [
    pytest.param(CAP_REPRODUCER, "x" * 4080 + " [REDACTED]", id="exact-cap"),
    pytest.param(
        "Diagnostic sk-abc\x1b[31mdefghijklmnopqrstuvwxyz0123456789ABCDEF",
        "Diagnostic [REDACTED]",
        id="ansi-split",
    ),
    pytest.param(
        "Diagnostic sk-abc\x00defghijklmnopqrstuvwxyz0123456789ABCDEF",
        "Diagnostic [REDACTED]",
        id="nul-split",
    ),
    pytest.param(
        "Bearer " + TOKEN,
        "Bearer [REDACTED]",
        id="bearer",
    ),
    pytest.param(
        "Diagnostic \x1b]0;" + TOKEN + "\x07 After",
        "Diagnostic ]0;[REDACTED] After",
        id="osc-controls",
    ),
    *[
        pytest.param(
            "Before " + token[:6] + control + token[6:] + " After",
            "Before [REDACTED] After",
            id=f"alternate-{index}-{control_id}",
        )
        for index, token in enumerate(["sk-" + "Q7" * 20, "sk-" + "4bcD" * 12])
        for control_id, control in [
            ("plain", ""),
            ("ansi", "\x1b[0m"),
            ("nul", "\x00"),
        ]
    ],
]
CONTROL_DETAILS = [
    pytest.param(detail, expected, id=f"{kind}-{placement}-{ord(control):02x}")
    for control in [
        "\x00",
        "\x08",
        "\x0b",
        "\x0c",
        "\x0e",
        "\x1b",
        "\x1f",
        "\x7f",
    ]
    for kind, token, prefix in [
        ("bare", TOKEN, ""),
        ("bearer", "Q7" * 20, "Bearer "),
    ]
    for placement, detail, expected in [
        (
            "boundary",
            "Before" + control + prefix + token + " After",
            "Before" + prefix + "[REDACTED] After",
        ),
        (
            "inside",
            "Before " + prefix + token[:6] + control + token[6:] + " After",
            "Before " + prefix + "[REDACTED] After",
        ),
    ]
]


@pytest.fixture
def driver() -> CodexDriver:
    return CodexDriver(
        AgentSettings(
            name="codex",
            command=("fixture-wrapper",),
            tiers={"standard": "fixture-model"},
            environment={},
            options={},
        ),
        run_id="detail-safety-run",
    )


def decode_failure(
    driver: CodexDriver, kind: str, detail: str
) -> tuple[Observation, ...]:
    record = (
        {"type": "error", "message": detail}
        if kind == "error"
        else {"type": "turn.failed", "error": {"message": detail}}
    )
    return driver.decode(json.dumps(record))


def assert_safe_details(
    tmp_path: Path, observations: tuple[Observation, ...], expected: str
) -> None:
    assert observations
    for observation in observations:
        assert observation.payload["detail"] == expected
        assert len(observation.payload["detail"]) <= 4096
        assert "\x1b" not in observation.payload["detail"]
        assert "\x00" not in observation.payload["detail"]
        assert TOKEN not in observation.payload["detail"]
        assert "sk-abcdefghijkl" not in observation.payload["detail"]
    path = tmp_path / "normalized.jsonl"
    writer = NormalizedEventWriter(path, max_bytes=1 << 20, min_free_bytes=0)
    try:
        for observation in observations:
            writer.write(observation)
        writer.flush()
    finally:
        writer.close()
    saved = path.read_bytes()
    assert TOKEN.encode() not in saved
    assert b"sk-abcdefghijkl" not in saved
    assert b"\\u001b" not in saved
    assert b"\\u0000" not in saved
    records = [json.loads(line) for line in saved.splitlines()]
    assert len(records) == len(observations)
    assert all(record["payload"]["detail"] == expected for record in records)


@pytest.mark.parametrize(("detail", "expected"), CONTROL_DETAILS)
def test_bounded_detail_redacts_control_boundaries_and_reconstructed_credentials(
    detail: str, expected: str
) -> None:
    assert bounded_detail(detail) == expected


@pytest.mark.parametrize("kind", ["error", "turn.failed"])
@pytest.mark.parametrize(("detail", "expected"), CONTROL_DETAILS)
def test_native_failure_saves_redaction_at_control_boundaries_and_inside_credentials(
    driver: CodexDriver,
    tmp_path: Path,
    kind: str,
    detail: str,
    expected: str,
) -> None:
    observations = decode_failure(driver, kind, detail)
    assert [value.type for value in observations] == [
        "activity.message" if kind == "error" else "session.failed"
    ]
    assert observations[0].payload["failure_class"] == "unknown"
    assert_safe_details(tmp_path, observations, expected)


@pytest.mark.parametrize(("detail", "expected"), SPLIT_DETAILS)
def test_bounded_detail_redacts_reconstructed_tokens_before_capping(
    detail: str, expected: str
) -> None:
    actual = bounded_detail(detail)
    assert actual == expected
    assert len(actual) <= 4096
    assert TOKEN not in actual
    assert "sk-abcdefghijkl" not in actual
    assert "\x1b" not in actual
    assert "\x00" not in actual


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        ("", ""),
        ("x" * 4095, "x" * 4095),
        ("x" * 4096, "x" * 4096),
        ("x" * 4097, "x" * 4096),
        ("y" * 4095, "y" * 4095),
        ("y" * 4096, "y" * 4096),
        ("y" * 4097, "y" * 4096),
        ("Diagnostic " * 500, ("Diagnostic " * 500)[:4096]),
        ("OK", "OK"),
        ("Warning!", "Warning!"),
        ("First\nSecond", "First\nSecond"),
        ("First\tSecond", "First\tSecond"),
        (
            "A\x1b[31mB\x1b[0m\x00\x08\x0b\x0c\x0e\x1f\x7f\t\nC",
            "AB\t\nC",
        ),
        ("\x00" * 4096 + "Visible", "Visible"),
    ],
)
def test_bounded_detail_preserves_printable_text_and_caps_after_control_removal(
    detail: str, expected: str
) -> None:
    actual = bounded_detail(detail)
    assert actual == expected
    assert len(actual) <= 4096


@pytest.mark.parametrize("kind", ["error", "turn.failed"])
@pytest.mark.parametrize(("detail", "expected"), SPLIT_DETAILS)
def test_native_failure_redacts_diagnostic_payload_and_saved_jsonl(
    driver: CodexDriver,
    tmp_path: Path,
    kind: str,
    detail: str,
    expected: str,
) -> None:
    observations = decode_failure(driver, kind, detail)
    assert [value.type for value in observations] == [
        "activity.message" if kind == "error" else "session.failed"
    ]
    assert observations[0].payload["failure_class"] == "unknown"
    if kind == "error":
        assert observations[0].payload["kind"] == "error"
        assert observations[0].payload["reset_at"] is None
    assert_safe_details(tmp_path, observations, expected)


@pytest.mark.parametrize("kind", ["error", "turn.failed"])
@pytest.mark.parametrize("detail", ["OK", "Warning!", "First\nSecond", "First\tSecond"])
def test_native_failure_preserves_short_and_formatted_saved_details(
    driver: CodexDriver, tmp_path: Path, kind: str, detail: str
) -> None:
    observations = decode_failure(driver, kind, detail)
    assert [value.type for value in observations] == [
        "activity.message" if kind == "error" else "session.failed"
    ]
    assert observations[0].payload["failure_class"] == "unknown"
    assert_safe_details(tmp_path, observations, detail)


@pytest.mark.parametrize("kind", ["error", "turn.failed"])
@pytest.mark.parametrize("seconds", [30, 21600, -1, 21601])
def test_native_rate_limit_uses_full_text_for_reset_and_saves_bounded_redaction(
    driver: CodexDriver, tmp_path: Path, kind: str, seconds: int
) -> None:
    detail = CAP_REPRODUCER + f" HTTP 429; retry after {seconds} seconds"
    observations = decode_failure(driver, kind, detail)
    if kind == "error":
        assert [value.type for value in observations] == ["activity.message"]
        failure = rate = observations[0]
        assert failure.payload["kind"] == "error"
    else:
        assert sorted(value.type for value in observations) == [
            "rate_limit.started",
            "session.failed",
        ]
        failure = next(
            value for value in observations if value.type == "session.failed"
        )
        rate = next(
            value for value in observations if value.type == "rate_limit.started"
        )
        assert rate.payload["window"] is None
    assert failure.payload["failure_class"] == "rate_limit"
    reset_at = rate.payload["reset_at"]
    if 0 <= seconds <= 21600:
        assert isinstance(reset_at, str)
        actual = datetime.fromisoformat(reset_at)
        assert actual.utcoffset() == timedelta(0)
        expected_reset = rate.timestamp + timedelta(seconds=seconds)
        assert abs((actual - expected_reset).total_seconds()) < 1
    else:
        assert reset_at is None
    expected_detail = (
        "x" * 4080 + " [REDACTED]" + f" HTTP 429; retry after {seconds} seconds"
    )[:4096]
    assert_safe_details(tmp_path, observations, expected_detail)


@pytest.mark.parametrize("kind", ["error", "turn.failed"])
@pytest.mark.parametrize(
    ("native_suffix", "expected_class"),
    [
        (
            "Unauthorized: HTTP 401; HTTP 429; retry after 30 seconds",
            "authentication",
        ),
        ("Sandbox denied: HTTP 403", "permission"),
        ("Connection reset: HTTP 503", "connectivity"),
        ("Request timed out", "timeout"),
        ("Unau\x1b[0mthorized", "unknown"),
    ],
)
def test_native_failure_preserves_full_original_classification_before_cleaning(
    driver: CodexDriver, kind: str, native_suffix: str, expected_class: str
) -> None:
    detail = "x" * 4096 + " " + native_suffix
    observations = decode_failure(driver, kind, detail)
    failure = next(
        value
        for value in observations
        if value.type == ("activity.message" if kind == "error" else "session.failed")
    )
    assert failure.payload["failure_class"] == expected_class
    assert failure.payload["detail"] == "x" * 4096


@pytest.mark.parametrize(("detail", "expected"), SPLIT_DETAILS)
def test_receiver_lane_redacts_message_payload_and_saved_jsonl(
    driver: CodexDriver, tmp_path: Path, detail: str, expected: str
) -> None:
    driver.decode(json.dumps({"type": "thread.started", "thread_id": "parent"}))
    observations = driver.decode(
        json.dumps(
            {
                "type": "item.started",
                "item": {
                    "id": "collab-1",
                    "type": "collab_tool_call",
                    "tool": "spawn_agent",
                    "sender_thread_id": "parent",
                    "receiver_thread_ids": ["child-1"],
                    "prompt": "Inspect receiver",
                    "agents_states": {
                        "child-1": {"status": "running", "message": detail}
                    },
                    "status": "in_progress",
                },
            }
        )
    )
    lanes = tuple(value for value in observations if value.lane_id == "child-1")
    assert len(lanes) == 1
    assert lanes[0].type == "lane.started"
    lane_detail = lanes[0].payload["detail"]
    assert isinstance(lane_detail, str)
    assert "\x1b" not in lane_detail
    assert "\x00" not in lane_detail
    assert_safe_details(tmp_path, lanes, expected)
