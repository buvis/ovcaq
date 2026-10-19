"""Offline integrity checks for the pinned, explicitly synthetic exec matrix."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "codex" / "v1"
FAMILIES = (
    "healthy.jsonl",
    "tool-active.jsonl",
    "lanes.jsonl",
    "rate-limited.jsonl",
    "connectivity-failed.jsonl",
    "permission-failed.jsonl",
    "authentication-failed.jsonl",
    "lanes-matched.jsonl",
    "malformed.jsonl",
)
SOURCES = [
    (
        "https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/"
        "codex-rs/exec/src/exec_events.rs"
    ),
    (
        "https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/"
        "codex-rs/exec/src/event_processor_with_jsonl_output.rs"
    ),
]
USAGE_KEYS = {
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
}


def records(name: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / name).read_text().splitlines()]


def test_installed_pin_and_help() -> None:
    assert (ROOT / "cli-version.txt").read_text() == "codex-cli 0.160.0\n"
    help_text = (ROOT / "cli-help.txt").read_text()
    assert "--ask-for-approval <APPROVAL_POLICY>" in help_text
    assert "- never:" in help_text
    assert "--approve-for-me" in help_text
    exec_help = (ROOT / "exec-help.txt").read_text()
    for option in ("--json", "--sandbox", "workspace-write", "-C,", "-m,", "-c,"):
        assert option in exec_help


def test_provenance_pin_and_sources() -> None:
    provenance = json.loads((ROOT / "provenance.json").read_text())
    assert provenance["schema_version"] == 1
    assert provenance["cli_version"] == "codex-cli 0.160.0"
    assert provenance["schema_source"] == SOURCES
    assert datetime.fromisoformat(provenance["captured_at"]).tzinfo is not None
    assert {entry["file"] for entry in provenance["families"]} == set(FAMILIES)
    assert len(provenance["families"]) == len(FAMILIES)


@pytest.mark.parametrize("name", FAMILIES)
def test_family_integrity_and_honest_provenance(name: str) -> None:
    provenance = json.loads((ROOT / "provenance.json").read_text())
    entry = next(entry for entry in provenance["families"] if entry["file"] == name)
    assert entry["sha256"] == hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    assert entry["source_kind"] == "schema-synthetic"
    assert entry["source"] == SOURCES
    assert entry["sanitization"]
    assert isinstance(entry["unsupported_fields"], list)
    assert {"cost", "lane", "telemetry", "live_capture"} <= set(
        entry["unsupported_fields"]
    )
    assert (ROOT / name).read_bytes().endswith(b"\n")


@pytest.mark.parametrize(
    "name",
    (*FAMILIES, "provenance.json", "cli-version.txt", "cli-help.txt", "exec-help.txt"),
)
def test_evidence_has_no_personal_paths_or_credentials(name: str) -> None:
    text = (ROOT / name).read_text()
    for forbidden in ("/Users/", "/home/", "Bearer ", "@gmail.com"):
        assert forbidden not in text
    assert re.search(r"\bsk-[A-Za-z0-9_-]{16,}", text) is None


def test_complete_native_top_level_and_item_matrix() -> None:
    events = [event for name in FAMILIES[:-1] for event in records(name)]
    assert {event["type"] for event in events} == {
        "thread.started",
        "turn.started",
        "turn.completed",
        "turn.failed",
        "item.started",
        "item.updated",
        "item.completed",
        "error",
    }
    items = [event["item"] for event in events if "item" in event]
    assert {item["type"] for item in items} == {
        "agent_message",
        "reasoning",
        "command_execution",
        "file_change",
        "mcp_tool_call",
        "collab_tool_call",
        "web_search",
        "todo_list",
        "error",
    }
    assert all(isinstance(item["id"], str) for item in items)
    assert all(
        set(event["usage"]) == USAGE_KEYS for event in events if "usage" in event
    )
    assert all(
        isinstance(value, int)
        for event in events
        if "usage" in event
        for value in event["usage"].values()
    )


@pytest.mark.parametrize(
    "kind,statuses",
    [
        ("command_execution", {"in_progress", "completed", "failed", "declined"}),
        ("file_change", {"in_progress", "completed", "failed"}),
        ("mcp_tool_call", {"in_progress", "completed", "failed"}),
        ("collab_tool_call", {"in_progress", "completed", "failed"}),
    ],
)
def test_native_status_variants(kind: str, statuses: set[str]) -> None:
    items = [
        event["item"]
        for name in FAMILIES[:-1]
        for event in records(name)
        if event.get("item", {}).get("type") == kind
    ]
    assert {item["status"] for item in items} == statuses


def test_collaboration_and_patch_variants() -> None:
    items = [event["item"] for event in records("lanes.jsonl") if "item" in event]
    calls = [item for item in items if item["type"] == "collab_tool_call"]
    assert {item["tool"] for item in calls} == {
        "spawn_agent",
        "send_input",
        "wait",
        "close_agent",
    }
    assert {
        state["status"] for item in calls for state in item["agents_states"].values()
    } == {
        "pending_init",
        "running",
        "interrupted",
        "completed",
        "errored",
        "shutdown",
        "not_found",
    }
    patches = [
        event["item"]
        for event in records("tool-active.jsonl")
        if event.get("item", {}).get("type") == "file_change"
    ]
    assert {change["kind"] for item in patches for change in item["changes"]} == {
        "add",
        "delete",
        "update",
    }


def test_error_can_recover_to_success() -> None:
    events = records("healthy.jsonl")
    assert (
        next(i for i, event in enumerate(events) if event["type"] == "error")
        < len(events) - 1
    )
    assert events[-1]["type"] == "turn.completed"
    assert not any(event["type"] == "turn.failed" for event in events)


@pytest.mark.parametrize("name", FAMILIES[3:7])
def test_error_then_identical_terminal_failure(name: str) -> None:
    events = records(name)
    assert events[-2]["type"] == "error"
    assert events[-1] == {
        "type": "turn.failed",
        "error": {"message": events[-2]["message"]},
    }


def test_absent_telemetry_has_zero_usage_not_invented_cost_or_lane() -> None:
    events = records("lanes.jsonl")
    assert events[-1]["usage"] == dict.fromkeys(USAGE_KEYS, 0)
    text = (ROOT / "lanes.jsonl").read_text()
    assert '"cost"' not in text
    assert '"lane"' not in text
    assert '"telemetry"' not in text


def test_tolerance_replay_redaction_and_truncation_examples() -> None:
    lines = (ROOT / "malformed.jsonl").read_text().splitlines()
    with pytest.raises(json.JSONDecodeError):
        json.loads(lines[-1])
    events = [json.loads(line) for line in lines[:-1]]
    assert {} in events
    assert {"type": 42} in events
    assert {"type": "item.completed", "item": None} in events
    assert {"type": "turn.completed"} in events
    assert {"type": "turn.completed", "usage": "invalid"} in events
    assert {
        "type": "turn.completed",
        "usage": {"input_tokens": 100, "output_tokens": 25},
    } in events
    assert any(event.get("type") == "future.event" for event in events)
    assert any(
        event.get("item", {}).get("type") == "future_item"
        for event in events
        if isinstance(event.get("item"), dict)
    )
    assert len(lines) != len(set(lines))
    assert "[REDACTED]" in "\n".join(lines)
    nested = next(event["future"] for event in events if "future" in event)
    for _ in range(32):
        nested = nested["nested"]
    assert nested == "[REDACTED]"


@pytest.mark.parametrize(
    "kind,fields",
    [
        ("agent_message", {"text"}),
        ("reasoning", {"text"}),
        ("command_execution", {"command", "aggregated_output", "exit_code", "status"}),
        ("file_change", {"changes", "status"}),
        ("mcp_tool_call", {"server", "tool", "arguments", "result", "error", "status"}),
        (
            "collab_tool_call",
            {
                "tool",
                "sender_thread_id",
                "receiver_thread_ids",
                "prompt",
                "agents_states",
                "status",
            },
        ),
        ("web_search", {"query", "action"}),
        ("todo_list", {"items"}),
        ("error", {"message"}),
    ],
)
def test_native_item_required_fields(kind: str, fields: set[str]) -> None:
    items = [
        event["item"]
        for name in FAMILIES[:-1]
        for event in records(name)
        if event.get("item", {}).get("type") == kind
    ]
    assert items
    assert all(fields <= set(item) for item in items)


def test_native_web_action_variants_and_optional_results() -> None:
    items = [
        event["item"]
        for event in records("tool-active.jsonl")
        if event.get("item", {}).get("type") == "web_search"
    ]
    assert {item["action"]["type"] for item in items} == {
        "search",
        "open_page",
        "find_in_page",
        "other",
    }
    assert any("results" not in item for item in items)
    assert any(item.get("results") == [] for item in items)
    assert any(item.get("results") for item in items)
