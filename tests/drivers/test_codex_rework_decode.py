import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import FailureClass, Observation

FIXTURES = Path(__file__).parents[1] / "fixtures" / "codex" / "v1"
FAKE_CREDENTIAL = "sk-" + "SyntheticCredentialForDecoderTestOnly123456789012"


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


def failure_record(event: str, detail: str) -> dict[str, object]:
    if event == "error":
        return {"type": event, "message": detail}
    return {"type": event, "error": {"message": detail}}


def raw_reasons(observations: tuple[Observation, ...], raw: str) -> str:
    gaps = [o for o in observations if o.type == "raw.unknown"]
    assert gaps
    for gap in gaps:
        assert gap.payload["raw_sha256"] == hashlib.sha256(raw.encode()).hexdigest()
        assert isinstance(gap.payload["reason"], str)
        assert 0 < len(gap.payload["reason"]) <= 4096
        assert len(gap.payload["preview"]) <= 512
    return " ".join(str(gap.payload["reason"]) for gap in gaps).lower()


def tool_record(kind: str) -> dict[str, object]:
    item: dict[str, object] = {"id": "unsafe-result", "type": kind}
    if kind == "mcp_tool_call":
        item.update(
            server="fixture-server",
            tool="lookup",
            status="completed",
            arguments={},
            result={"content": ["NESTED"], "structured_content": None},
            error=None,
        )
    else:
        item.update(
            query="fixture query",
            action={"type": "search", "query": "fixture query"},
            results=["NESTED"],
        )
    return {"type": "item.completed", "item": item}


def collab_record(child_status: str, message: str) -> dict[str, object]:
    return {
        "type": "item.updated",
        "item": {
            "id": "collab-rework",
            "type": "collab_tool_call",
            "tool": "spawn_agent",
            "sender_thread_id": "parent",
            "receiver_thread_ids": ["child"],
            "prompt": "Inspect receiver",
            "agents_states": {"child": {"status": child_status, "message": message}},
            "status": "in_progress",
        },
    }


@pytest.mark.parametrize("event", ["error", "turn.failed"])
@pytest.mark.parametrize(
    ("detail", "failure_class"),
    [
        ("stream disconnected before completion", "connectivity"),
        ("Quota exceeded. Check your plan and billing details.", "rate_limit"),
        ("internal error; agent loop died unexpectedly", "agent"),
        ("sandbox error", "permission"),
        ("Selected model is at capacity", "connectivity"),
        ("usage limits", "rate_limit"),
        ("quota limits", "rate_limit"),
        ("rate limiting", "rate_limit"),
    ],
)
def test_native_diagnostics_have_independent_failure_classification(
    driver: CodexDriver, event: str, detail: str, failure_class: str
) -> None:
    observations = decode(driver, failure_record(event, detail))
    normalized = next(
        o for o in observations if o.type in {"session.failed", "activity.message"}
    )
    assert normalized.payload["failure_class"] == failure_class
    assert normalized.payload["detail"] == detail
    summary = driver.summarize(observations, 1)
    assert not summary.success
    assert summary.failure_class == FailureClass(failure_class)
    assert summary.failure_detail == detail


def test_checked_in_connectivity_failure_uses_independent_oracle(
    driver: CodexDriver,
) -> None:
    lines = (FIXTURES / "connectivity-failed.jsonl").read_text().splitlines()
    observations = tuple(o for line in lines for o in driver.decode(line))
    terminal = [o for o in observations if o.type == "session.failed"]
    provisional = [
        o
        for o in observations
        if o.type == "activity.message" and o.payload.get("kind") == "error"
    ]
    assert len(terminal) == len(provisional) == 1
    assert terminal[0].payload["failure_class"] == "connectivity"
    assert provisional[0].payload["failure_class"] == "connectivity"
    assert not any(o.type == "rate_limit.started" for o in observations)
    summary = driver.summarize(observations, 1)
    assert not summary.success
    assert summary.failure_class == FailureClass("connectivity")


@pytest.mark.parametrize("event", ["error", "turn.failed"])
def test_failure_classifies_full_text_before_sanitizing_and_capping_detail(
    driver: CodexDriver, event: str
) -> None:
    detail = "Safe context " + FAKE_CREDENTIAL + "\x1b[31m\x00" + "x" * 5000
    detail += " Rate limit reached"
    observations = decode(driver, failure_record(event, detail))
    normalized = next(
        o for o in observations if o.type in {"session.failed", "activity.message"}
    )
    assert normalized.payload["failure_class"] == "rate_limit"
    for observation in observations:
        if "detail" in observation.payload:
            bounded = observation.payload["detail"]
            assert isinstance(bounded, str)
            assert bounded.startswith("Safe context ")
            assert 0 < len(bounded) <= 4096
            assert FAKE_CREDENTIAL not in bounded
            assert "[REDACTED]" in bounded
            assert "\x1b" not in bounded and "\x00" not in bounded
    summary = driver.summarize(observations, 1)
    assert not summary.success
    assert summary.failure_class == FailureClass("rate_limit")
    assert summary.failure_detail == normalized.payload["detail"]


@pytest.mark.parametrize("kind", ["mcp_tool_call", "web_search"])
@pytest.mark.parametrize("hazard", ["NaN", "Infinity", "-Infinity", "deep"])
def test_unsafe_tool_json_never_raises_and_explains_raw_gap(
    driver: CodexDriver, kind: str, hazard: str
) -> None:
    nested = "[" * 1200 + "0" + "]" * 1200 if hazard == "deep" else hazard
    raw = json.dumps(tool_record(kind)).replace('"NESTED"', nested)
    observations = driver.decode(raw)
    assert observations
    assert all(o.type == "raw.unknown" for o in observations)
    reasons = raw_reasons(observations, raw)
    if hazard == "deep":
        assert re.search(r"nest|depth|recurs|malformed|invalid.{0,20}json", reasons)
    else:
        assert re.search(
            r"non.?finite|nan|infinity|malformed|invalid.{0,20}json", reasons
        )


@pytest.mark.parametrize("punctuation", [".", ",", ")"])
@pytest.mark.parametrize("hours", [1, 7])
def test_explicit_aware_rate_reset_accepts_punctuation_with_six_hour_ceiling(
    driver: CodexDriver, punctuation: str, hours: int
) -> None:
    reset = datetime.now(UTC) + timedelta(hours=hours)
    detail = f"Rate limit reached; reset at {reset.isoformat()}{punctuation}"
    observations = decode(driver, failure_record("turn.failed", detail))
    rate = next(o for o in observations if o.type == "rate_limit.started")
    summary = driver.summarize(observations, 1)
    assert not summary.success
    assert summary.failure_class == FailureClass("rate_limit")
    if hours == 1:
        assert datetime.fromisoformat(rate.payload["reset_at"]) == reset
        assert summary.rate_limit_reset_at == reset
    else:
        assert rate.payload["reset_at"] is None
        assert summary.rate_limit_reset_at is None


@pytest.mark.parametrize("child_status", ["interrupted", "shutdown", "not_found"])
def test_previously_started_receiver_closes_as_failed_on_non_success_terminal(
    driver: CodexDriver, child_status: str
) -> None:
    decode(driver, {"type": "thread.started", "thread_id": "parent"})
    started = decode(driver, collab_record("running", "Receiver starts"))
    assert any(o.type == "lane.started" and o.lane_id == "child" for o in started)
    message = "Receiver stopped " + FAKE_CREDENTIAL + "\x00" + "x" * 5000
    observations = decode(driver, collab_record(child_status, message))
    terminal = [o for o in observations if o.type == "lane.failed"]
    assert len(terminal) == 1
    assert terminal[0].lane_id == "child"
    assert terminal[0].session_id == "parent"
    assert not any(o.type == "lane.completed" for o in observations)
    detail = terminal[0].payload["detail"]
    assert isinstance(detail, str) and 0 < len(detail) <= 4096
    assert FAKE_CREDENTIAL not in detail and "\x00" not in detail
    assert isinstance(terminal[0].payload["label"], str)
    assert terminal[0].payload["label"]


@pytest.mark.parametrize(
    ("reads", "writes"),
    [(20, 0), (0, 5)],
    ids=["reads-exceed-input", "write-partition"],
)
def test_malformed_usage_reason_survives_simultaneous_partition_gap(
    driver: CodexDriver, reads: int, writes: int
) -> None:
    raw = json.dumps(
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 10,
                "cached_input_tokens": reads,
                "cache_write_input_tokens": writes,
                "output_tokens": True,
                "reasoning_output_tokens": 0,
            },
        }
    )
    observations = driver.decode(raw)
    reasons = raw_reasons(observations, raw)
    assert re.search(r"malformed|invalid|non.?integer|boolean|bool", reasons)
    assert re.search(r"partition|cache|read.{0,30}input|input.{0,30}read", reasons)
    usage = next(o for o in observations if o.type == "usage.updated")
    assert usage.payload["usage"]["input_tokens"] is None
    assert usage.payload["usage"]["output_tokens"] is None
    assert usage.payload["usage"]["cache_read_input_tokens"] == reads
    assert usage.payload["usage"]["cache_creation_input_tokens"] == writes


def test_thread_conflict_reason_survives_simultaneous_usage_gap(
    driver: CodexDriver,
) -> None:
    first = decode(driver, {"type": "thread.started", "thread_id": "first"})
    second = decode(driver, {"type": "thread.started", "thread_id": "second"})
    raw = json.dumps(
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 10,
                "cached_input_tokens": 20,
                "cache_write_input_tokens": 0,
                "output_tokens": 30,
                "reasoning_output_tokens": 0,
            },
        }
    )
    observations = driver.decode(raw)
    reasons = raw_reasons(observations, raw)
    assert "thread" in reasons
    assert re.search(r"conflict|mismatch|changed|multiple|identity", reasons)
    assert re.search(r"partition|cache|read.{0,30}input|input.{0,30}read", reasons)
    summary = driver.summarize((*first, *second, *observations), 0)
    assert not summary.success
    assert summary.failure_class == FailureClass("unknown")
