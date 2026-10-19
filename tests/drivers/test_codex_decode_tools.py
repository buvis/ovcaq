"""Synthetic, public-API tests for native tool observations."""

import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import LaunchRequest, LaunchSpec
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import Observation

RUN_ID = "synthetic-tool-run"
THREAD_ID = "synthetic-tool-thread"
SECRET = "SYNTHETIC_PRIVATE_CREDENTIAL_987654321"
LARGE_TEXT = "synthetic-large-result-" * 4096


@pytest.fixture
def driver() -> CodexDriver:
    settings = AgentSettings(
        name="codex",
        command=("fixture-launcher",),
        tiers={"standard": "fixture-model"},
        environment={"TASK_MODE": "synthetic-tool-test"},
        options={},
    )
    instance = CodexDriver(settings, run_id=RUN_ID)
    instance.decode(json.dumps({"type": "thread.started", "thread_id": THREAD_ID}))
    return instance


def tool_item(kind: str, item_id: str = "synthetic-item") -> dict[str, Any]:
    item: dict[str, Any] = {"id": item_id, "type": kind}
    if kind == "command_execution":
        item.update(command="printf synthetic", aggregated_output="", exit_code=None)
    elif kind == "file_change":
        item["changes"] = [{"path": "synthetic/file.txt", "kind": "update"}]
    elif kind == "mcp_tool_call":
        item.update(
            server="synthetic-server",
            tool="lookup",
            arguments={},
            result=None,
            error=None,
        )
    elif kind == "web_search":
        item.update(
            query="synthetic query",
            action={"type": "search", "query": "synthetic query"},
        )
    if kind != "web_search":
        item["status"] = "in_progress"
    return item


def decode_item(
    driver: CodexDriver,
    item: dict[str, Any],
    event: str = "item.completed",
) -> tuple[Observation, ...]:
    before = datetime.now(UTC)
    observations = driver.decode(json.dumps({"type": event, "item": item}))
    after = datetime.now(UTC)
    assert isinstance(observations, tuple)
    for observation in observations:
        assert isinstance(observation, Observation)
        assert observation.protocol_version == 1
        assert observation.provider == "codex"
        assert observation.run_id == RUN_ID
        assert observation.session_id == THREAD_ID
        assert observation.timestamp.utcoffset() == timedelta(0)
        assert before <= observation.timestamp <= after
    return observations


def assert_tool(
    observations: tuple[Observation, ...],
    expected: str,
    item_id: str,
) -> Observation:
    assert len(observations) == 1
    observation = observations[0]
    assert observation.type == expected
    assert observation.payload["tool_id"] == item_id
    name = observation.payload["name"]
    assert isinstance(name, str) and name.strip()
    assert not any(
        provider in name.lower() for provider in ("codex", "claude", "anthropic")
    )
    if "detail" in observation.payload:
        assert isinstance(observation.payload["detail"], str)
    return observation


def assert_unknown(observations: tuple[Observation, ...], raw: str) -> None:
    unknown = [
        observation for observation in observations if observation.type == "raw.unknown"
    ]
    assert unknown
    for observation in unknown:
        assert set(observation.payload) == {"reason", "raw_sha256", "preview"}
        assert observation.payload["raw_sha256"] == sha256(raw.encode()).hexdigest()
        assert isinstance(observation.payload["preview"], str)
        assert len(observation.payload["preview"]) <= 512
        if raw.strip():
            assert observation.payload["preview"].strip()
        assert isinstance(observation.payload["reason"], str)
        assert observation.payload["reason"].strip()


@pytest.mark.parametrize("event", ["item.started", "item.updated", "item.completed"])
@pytest.mark.parametrize(
    ("kind", "status", "expected"),
    [
        ("command_execution", "in_progress", "tool.started"),
        ("command_execution", "completed", "tool.completed"),
        ("command_execution", "failed", "tool.failed"),
        ("command_execution", "declined", "tool.failed"),
        ("file_change", "in_progress", "tool.started"),
        ("file_change", "completed", "tool.completed"),
        ("file_change", "failed", "tool.failed"),
        ("mcp_tool_call", "in_progress", "tool.started"),
        ("mcp_tool_call", "completed", "tool.completed"),
        ("mcp_tool_call", "failed", "tool.failed"),
    ],
    ids=[
        "command-running",
        "command-success",
        "command-failed",
        "command-declined",
        "file-running",
        "file-success",
        "file-failed",
        "mcp-running",
        "mcp-success",
        "mcp-failed",
    ],
)
def test_native_status_projects_each_supported_item_event(
    driver: CodexDriver,
    event: str,
    kind: str,
    status: str,
    expected: str,
) -> None:
    item = tool_item(kind)
    item["status"] = status
    if kind == "command_execution" and status == "completed":
        item["exit_code"] = 0
    if kind == "mcp_tool_call" and status == "completed":
        item["result"] = {
            "content": [{"type": "text", "text": "synthetic answer"}],
            "structured_content": None,
        }
    assert_tool(decode_item(driver, item, event), expected, item["id"])


@pytest.mark.parametrize(
    ("event", "expected"),
    [
        ("item.started", "tool.started"),
        ("item.updated", "tool.started"),
        ("item.completed", "tool.completed"),
    ],
)
@pytest.mark.parametrize(
    "action",
    [
        {"type": "search", "query": "synthetic", "queries": ["synthetic"]},
        {"type": "open_page", "url": "https://example.invalid/synthetic"},
        {
            "type": "find_in_page",
            "url": "https://example.invalid/synthetic",
            "pattern": "synthetic",
        },
        {"type": "other"},
        {"type": "search"},
        {"type": "search", "query": None, "queries": None},
        {"type": "open_page"},
        {"type": "open_page", "url": None},
        {"type": "find_in_page"},
        {"type": "find_in_page", "url": None, "pattern": None},
        {"type": "synthetic_future_action"},
    ],
    ids=[
        "search",
        "open",
        "find",
        "other",
        "search-omitted",
        "search-null",
        "open-omitted",
        "open-null",
        "find-omitted",
        "find-null",
        "future-as-other",
    ],
)
def test_web_lifecycle_uses_item_events_without_native_status(
    driver: CodexDriver,
    event: str,
    expected: str,
    action: dict[str, Any],
) -> None:
    item = tool_item("web_search")
    item["action"] = action
    assert_tool(decode_item(driver, item, event), expected, item["id"])


@pytest.mark.parametrize(
    "action",
    [
        {},
        {"type": None},
        {"type": 42},
        {"type": []},
        {"type": "search", "query": 42},
        {"type": "search", "queries": "wrong"},
        {"type": "search", "queries": [42]},
        {"type": "open_page", "url": 42},
        {"type": "find_in_page", "url": {}},
        {"type": "find_in_page", "pattern": []},
    ],
    ids=[
        "missing-type",
        "null-type",
        "number-type",
        "list-type",
        "query-number",
        "queries-string",
        "queries-nonstrings",
        "open-url-number",
        "find-url-object",
        "find-pattern-list",
    ],
)
@pytest.mark.parametrize("event", ["item.started", "item.updated", "item.completed"])
def test_web_action_rejects_malformed_tag_and_present_optional_field_types(
    driver: CodexDriver,
    action: dict[str, Any],
    event: str,
) -> None:
    item = tool_item("web_search")
    item["action"] = action
    raw = json.dumps({"type": event, "item": item})
    observations = driver.decode(raw)
    assert_unknown(observations, raw)
    assert all(observation.type == "raw.unknown" for observation in observations)


@pytest.mark.parametrize(
    "kind", ["command_execution", "file_change", "mcp_tool_call", "web_search"]
)
def test_started_updated_completed_preserve_one_native_tool_identity(
    driver: CodexDriver,
    kind: str,
) -> None:
    item = tool_item(kind)
    assert_tool(decode_item(driver, item, "item.started"), "tool.started", item["id"])
    updated = decode_item(driver, item, "item.updated")
    assert updated
    assert all(observation.type == "tool.started" for observation in updated)
    assert all(observation.payload["tool_id"] == item["id"] for observation in updated)
    if kind != "web_search":
        item["status"] = "completed"
    if kind == "command_execution":
        item["exit_code"] = 0
    assert_tool(decode_item(driver, item), "tool.completed", item["id"])


@pytest.mark.parametrize("exit_code", [-1, 1, 127])
@pytest.mark.parametrize("status", ["in_progress", "completed", "failed", "declined"])
@pytest.mark.parametrize("event", ["item.started", "item.updated", "item.completed"])
def test_nonzero_command_exit_dominates_every_native_status_and_item_event(
    driver: CodexDriver,
    exit_code: int,
    status: str,
    event: str,
) -> None:
    item = tool_item("command_execution")
    item.update(
        status=status, exit_code=exit_code, aggregated_output="synthetic result"
    )
    assert_tool(decode_item(driver, item, event), "tool.failed", item["id"])


def test_explicit_mcp_error_is_tool_failure_even_with_completed_status(
    driver: CodexDriver,
) -> None:
    item = tool_item("mcp_tool_call")
    item.update(status="completed", error={"message": "synthetic tool failure"})
    assert_tool(decode_item(driver, item), "tool.failed", item["id"])


def test_command_stdout_never_becomes_provider_health(driver: CodexDriver) -> None:
    item = tool_item("command_execution")
    marker = "safe-command-marker"
    item.update(
        command=f"printf {marker}",
        status="completed",
        exit_code=0,
        aggregated_output=(
            f"{marker}: "
            "rate limit exceeded; quota exhausted; retry after 120; "
            "authentication failed; permission denied; connection refused; timeout"
        ),
    )
    observation = assert_tool(decode_item(driver, item), "tool.completed", item["id"])
    assert marker in observation.payload["detail"]


def test_file_change_detail_summarizes_all_paths_and_kinds(driver: CodexDriver) -> None:
    item = tool_item("file_change")
    item.update(
        status="completed",
        changes=[
            {"path": "synthetic/new.txt", "kind": "add"},
            {"path": "synthetic/deleted.txt", "kind": "delete"},
            {"path": "synthetic/changed.txt", "kind": "update"},
        ],
    )
    observation = assert_tool(decode_item(driver, item), "tool.completed", item["id"])
    detail = observation.payload["detail"]
    assert isinstance(detail, str)
    for change in item["changes"]:
        assert change["path"] in detail
        assert change["kind"] in detail


def test_mcp_large_result_and_sensitive_metadata_are_bounded_and_sanitized(
    driver: CodexDriver,
) -> None:
    item = tool_item("mcp_tool_call")
    marker = "safe-mcp-marker"
    item.update(
        server=marker,
        tool=marker,
        status="completed",
        arguments={"token": SECRET},
        result={
            "content": [{"type": "text", "text": marker + LARGE_TEXT}],
            "_meta": {"password": SECRET},
            "structured_content": {"token": SECRET, "answer": marker + LARGE_TEXT},
        },
    )
    observation = assert_tool(decode_item(driver, item), "tool.completed", item["id"])
    detail = observation.payload["detail"]
    assert isinstance(detail, str)
    assert marker in detail
    assert len(detail) < len(LARGE_TEXT)
    serialized = json.dumps(dict(observation.payload))
    assert SECRET not in serialized
    assert LARGE_TEXT not in serialized


def test_web_large_results_and_sensitive_url_are_bounded_and_sanitized(
    driver: CodexDriver,
) -> None:
    item = tool_item("web_search")
    marker = "safe-web-marker"
    url = f"https://example.invalid/{marker}?token={SECRET}"
    item.update(
        query=marker,
        action={"type": "open_page", "url": url},
        results=[{"url": url, "title": marker + LARGE_TEXT}],
    )
    observation = assert_tool(decode_item(driver, item), "tool.completed", item["id"])
    detail = observation.payload["detail"]
    assert isinstance(detail, str)
    assert marker in detail
    assert len(detail) < len(LARGE_TEXT)
    serialized = json.dumps(dict(observation.payload))
    assert SECRET not in serialized
    assert LARGE_TEXT not in serialized


@pytest.mark.parametrize(
    ("kind", "field", "value"),
    [
        ("command_execution", "command", None),
        ("command_execution", "aggregated_output", []),
        ("command_execution", "exit_code", True),
        ("command_execution", "exit_code", "0"),
        ("command_execution", "status", "future"),
        ("file_change", "changes", {}),
        ("file_change", "changes", [{"path": 42, "kind": "add"}]),
        ("file_change", "changes", [{"path": "synthetic", "kind": "future"}]),
        ("file_change", "status", "declined"),
        ("mcp_tool_call", "server", []),
        ("mcp_tool_call", "tool", None),
        ("mcp_tool_call", "result", []),
        ("mcp_tool_call", "result", {"content": "wrong", "structured_content": None}),
        ("mcp_tool_call", "error", {"message": 42}),
        ("mcp_tool_call", "status", "declined"),
        ("web_search", "query", None),
        ("web_search", "action", []),
        ("web_search", "results", {}),
        ("command_execution", "id", ""),
        ("file_change", "id", None),
        ("mcp_tool_call", "id", True),
        ("web_search", "id", []),
    ],
    ids=[
        "command-null",
        "output-list",
        "exit-bool",
        "exit-string",
        "command-status",
        "changes-object",
        "path-number",
        "change-kind",
        "file-status",
        "server-list",
        "tool-null",
        "result-list",
        "content-string",
        "error-number",
        "mcp-status",
        "query-null",
        "action-list",
        "results-object",
        "id-empty",
        "id-null",
        "id-bool",
        "id-list",
    ],
)
def test_wrong_native_shapes_and_unknown_statuses_return_only_raw(
    driver: CodexDriver,
    kind: str,
    field: str,
    value: Any,
) -> None:
    item = tool_item(kind)
    item[field] = value
    raw = json.dumps({"type": "item.completed", "item": item})
    observations = driver.decode(raw)
    assert_unknown(observations, raw)
    assert all(observation.type == "raw.unknown" for observation in observations)


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "{",
        "null",
        "[]",
        "42",
        "{}",
        '{"type":42}',
        '{"type":"item.completed","item":null}',
        '{"type":"item.completed","item":{"id":"synthetic-future","type":"future_item"}}',
        '{"type":"future.event","item":{"id":"synthetic-future","type":"web_search"}}',
        '{"type":"future.event","padding":"' + LARGE_TEXT + '"}',
        '{"type":"future.event","padding":' + "[" * 1200 + "0" + "]" * 1200 + "}",
    ],
    ids=[
        "empty",
        "invalid-json",
        "null",
        "array",
        "number",
        "missing-type",
        "type-number",
        "item-null",
        "future-item",
        "future-event",
        "oversized",
        "recursive-json",
    ],
)
def test_invalid_and_future_records_never_raise_and_keep_raw_evidence(
    driver: CodexDriver,
    raw: str,
) -> None:
    observations = driver.decode(raw)
    assert_unknown(observations, raw)
    assert all(observation.type == "raw.unknown" for observation in observations)


@pytest.mark.parametrize("key", ["token", "password"])
def test_raw_preview_sanitizes_variable_synthetic_credentials_and_keeps_safe_context(
    driver: CodexDriver,
    key: str,
) -> None:
    secret = f"synthetic-{uuid4().hex}"
    marker = "safe-preview-marker"
    raw = json.dumps(
        {
            "type": "future.event",
            "safe_context": marker,
            key: secret,
            "padding": LARGE_TEXT,
        }
    )
    observations = driver.decode(raw)
    assert_unknown(observations, raw)
    assert all(secret not in str(observation.payload) for observation in observations)
    assert all(marker in observation.payload["preview"] for observation in observations)


@pytest.mark.parametrize(
    "kind", ["command_execution", "file_change", "mcp_tool_call", "web_search"]
)
def test_missing_required_native_tool_field_stays_raw(
    driver: CodexDriver, kind: str
) -> None:
    item = tool_item(kind)
    field = {
        "command_execution": "command",
        "file_change": "changes",
        "mcp_tool_call": "server",
        "web_search": "action",
    }[kind]
    del item[field]
    raw = json.dumps({"type": "item.completed", "item": item})
    observations = driver.decode(raw)
    assert_unknown(observations, raw)
    assert all(observation.type == "raw.unknown" for observation in observations)


def test_4097th_identity_emits_visible_raw_gap_and_launch_resets_capacity(
    driver: CodexDriver,
    tmp_path: Path,
) -> None:
    for number in range(4096):
        item = tool_item("web_search", f"synthetic-{number}")
        assert_tool(
            decode_item(driver, item, "item.started"), "tool.started", item["id"]
        )
    item = tool_item("web_search", "synthetic-overflow")
    raw = json.dumps({"type": "item.started", "item": item})
    observations = driver.decode(raw)
    assert_unknown(observations, raw)
    tools = tuple(
        observation
        for observation in observations
        if observation.type == "tool.started"
    )
    assert_tool(tools, "tool.started", item["id"])
    request = LaunchRequest(
        root=tmp_path / "synthetic-project",
        phase="build",
        prompt="synthetic prompt",
        model=None,
        effort=None,
        timeout_seconds=30,
        session_dir=tmp_path / "synthetic-session",
    )
    launch = driver.build_launch(request)
    assert isinstance(launch, LaunchSpec)
    assert isinstance(launch.argv, tuple)
    assert launch.argv[0] == "fixture-launcher"
    assert request.prompt in launch.argv
    assert launch.cwd == request.root
    assert launch.env["TASK_MODE"] == "synthetic-tool-test"
    assert launch.raw_format == "codex-exec-json-v1"
    driver.decode(json.dumps({"type": "thread.started", "thread_id": THREAD_ID}))
    for number in range(4096):
        item = tool_item("web_search", f"fresh-synthetic-{number}")
        assert_tool(
            decode_item(driver, item, "item.started"), "tool.started", item["id"]
        )


def test_eviction_prefers_oldest_terminal_then_oldest_live_identity(
    driver: CodexDriver,
) -> None:
    live = tool_item("web_search", "live_old")
    assert_tool(decode_item(driver, live, "item.started"), "tool.started", "live_old")
    failed = tool_item("command_execution", "done_old")
    failed.update(status="failed", exit_code=1)
    assert_tool(decode_item(driver, failed), "tool.failed", "done_old")
    completed = tool_item("file_change", "done_next")
    completed["status"] = "completed"
    assert_tool(decode_item(driver, completed), "tool.completed", "done_next")
    kinds = ("command_execution", "file_change", "mcp_tool_call", "web_search")
    for number in range(4093):
        item = tool_item(kinds[number % len(kinds)], f"fill_{number}")
        assert_tool(
            decode_item(driver, item, "item.started"), "tool.started", item["id"]
        )
    for number, victim in enumerate(("done_old", "done_next", "live_old")):
        item = tool_item("web_search", f"extra_{number}")
        raw = json.dumps({"type": "item.started", "item": item})
        observations = driver.decode(raw)
        assert_unknown(observations, raw)
        evidence = " ".join(
            str(observation.payload)
            for observation in observations
            if observation.type == "raw.unknown"
        )
        assert victim in evidence
        tools = tuple(
            observation
            for observation in observations
            if observation.type == "tool.started"
        )
        assert_tool(tools, "tool.started", item["id"])


def test_malformed_items_do_not_consume_remembered_identity_capacity(
    driver: CodexDriver,
) -> None:
    for number in range(4096):
        item = tool_item("web_search", f"invalid-synthetic-{number}")
        item["action"] = None
        raw = json.dumps({"type": "item.started", "item": item})
        observations = driver.decode(raw)
        assert_unknown(observations, raw)
        assert all(observation.type == "raw.unknown" for observation in observations)
    item = tool_item("web_search", "valid-synthetic-after-errors")
    assert_tool(decode_item(driver, item, "item.started"), "tool.started", item["id"])
