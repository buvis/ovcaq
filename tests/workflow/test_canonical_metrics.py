from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ovcaq.state.schema import State
from ovcaq.workflow.reports import (
    load_metric_rows,
    reduce_metrics,
    render_metrics,
    render_report,
)


def _canonical(batch_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "phase",
        "run_id": "run-1",
        "session_id": "session-1",
        "batch_id": batch_id,
        "prd": "00004-workflow-core-v1.md",
        "phase_launched": "build",
        "capability": None,
        "phase_end": "review",
        "decision": "continue",
        "started_at": "2026-08-30T12:00:00Z",
        "finished_at": "2026-08-30T12:00:12Z",
        "wall_seconds": 12,
        "model": "test-model",
        "usage": {
            "input_tokens": 10,
            "output_tokens": 7,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "tool_uses": 1,
            "cost_usd": 0.25,
            "estimated": False,
        },
    }


def _capability(batch_id: str) -> dict[str, object]:
    return {
        **_canonical(batch_id),
        "kind": "capability",
        "phase_launched": None,
        "capability": "provider-connectivity",
        "phase_end": None,
        "model": None,
        "usage": None,
    }


def test_reports_load_and_reduce_mixed_legacy_and_canonical_metrics(
    tmp_path: Path,
    workflow_state: State,
) -> None:
    batch = workflow_state["batch"]["id"]
    canonical = {
        **_canonical(batch),
        "wall_seconds": 13,
        "finished_at": "2026-08-30T12:00:13Z",
    }
    legacy = {
        "batch": batch,
        "prd": "00004-workflow-core-v1.md",
        "phase_launched": "build",
        "phase_end": "review",
        "decision": "continue",
        "wall_secs": 8,
        "cost_usd": 0.5,
        "tokens_out": 3,
    }
    other = {**_canonical("another-batch"), "session_id": "other-session"}
    path = tmp_path / "mixed.jsonl"
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in (legacy, canonical, other))
    )
    rows = load_metric_rows(path)
    assert rows == (legacy, canonical, other)
    summary = reduce_metrics(rows[:2])
    assert summary.sessions == 2
    assert summary.wall_secs == 21
    assert summary.cost_usd == 0.75
    assert summary.tokens_out == 10
    for text in (
        render_metrics(rows, batch_id=batch),
        render_report(workflow_state, (), rows),
    ):
        _assert_totals(text, 2, 21, "0.75", "10")
    workflow_state["batch"]["id"] = "another-batch"
    for text in (
        render_metrics(rows, batch_id="another-batch"),
        render_report(workflow_state, (), rows),
    ):
        _assert_totals(text, 1, 12, "0.25", "7")


def _assert_totals(text: str, sessions: int, wall: int, cost: str, tokens: str) -> None:
    for label, expected in (
        ("Sessions", str(sessions)),
        ("Wall seconds", str(wall)),
        ("Cost USD", cost),
        ("Output tokens", tokens),
    ):
        assert [
            line for line in text.splitlines() if line.startswith(f"- {label}:")
        ] == [f"- {label}: {expected}"]


def test_empty_metrics_reduce_to_zero_sessions() -> None:
    summary = reduce_metrics(())
    assert summary.sessions == 0
    assert summary.wall_secs == 0
    assert summary.cost_usd == 0
    assert summary.tokens_out == 0
    _assert_totals(render_metrics(()), 0, 0, "0.00", "0")


def test_one_canonical_session_preserves_known_usage(workflow_state: State) -> None:
    row = _canonical(workflow_state["batch"]["id"])
    summary = reduce_metrics((row,))
    assert summary.sessions == 1
    assert summary.wall_secs == 12
    assert summary.cost_usd == 0.25
    assert summary.tokens_out == 7
    for text in (render_metrics((row,)), render_report(workflow_state, (), (row,))):
        _assert_totals(text, 1, 12, "0.25", "7")


@pytest.mark.parametrize(
    "usage",
    (
        None,
        {
            "input_tokens": None,
            "output_tokens": None,
            "cache_creation_input_tokens": None,
            "cache_read_input_tokens": None,
            "tool_uses": None,
            "cost_usd": None,
            "estimated": False,
        },
    ),
)
def test_missing_canonical_usage_remains_unknown_in_metrics_and_report(
    workflow_state: State,
    usage: object,
) -> None:
    row = {**_canonical(workflow_state["batch"]["id"]), "usage": usage}
    summary = reduce_metrics((row,))
    assert summary.sessions == 1
    assert summary.wall_secs == 12
    assert summary.cost_usd is None
    assert summary.tokens_out is None
    for text in (render_metrics((row,)), render_report(workflow_state, (), (row,))):
        _assert_totals(text, 1, 12, "unknown", "unknown")


def test_capabilities_are_retained_but_excluded_from_workflow_totals(
    tmp_path: Path,
    workflow_state: State,
) -> None:
    batch = workflow_state["batch"]["id"]
    phase = _canonical(batch)
    capability = _capability(batch)
    legacy_session = {
        "batch": batch,
        "prd": "00004-workflow-core-v1.md",
        "phase_launched": "build",
        "phase_end": "review",
        "decision": "continue",
        "wall_secs": 8,
        "cost_usd": 0.5,
        "tokens_out": 3,
    }
    convergence = {
        "event": "review_converged",
        "batch": batch,
        "cycles_to_converge": 2,
    }
    other = {**_canonical("another-batch"), "session_id": "other-session"}
    evidence = (phase, capability, legacy_session, convergence, other)
    original = deepcopy(evidence)
    path = tmp_path / "mixed-capability.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in evidence))

    rows = load_metric_rows(path)
    assert rows == evidence
    summary = reduce_metrics(rows[:-1])
    assert summary.sessions == 2
    assert summary.wall_secs == 20
    assert summary.cost_usd == 0.75
    assert summary.tokens_out == 10
    assert summary.review_convergences == 1
    assert summary.cycles_to_converge == 2
    metrics = render_metrics(rows, batch_id=batch)
    report = render_report(workflow_state, (), rows)
    for text in (metrics, report):
        _assert_totals(text, 2, 20, "0.75", "10")
    assert render_metrics(rows, batch_id=batch) == metrics
    assert render_report(workflow_state, (), rows) == report
    assert evidence == original


def test_malformed_canonical_usage_retains_session_with_unknown_totals(
    workflow_state: State,
) -> None:
    row = {**_canonical(workflow_state["batch"]["id"]), "usage": "malformed"}
    original = deepcopy(row)
    summary = reduce_metrics((row,))
    assert summary.sessions == 1
    assert summary.wall_secs == 12
    assert summary.cost_usd is None
    assert summary.tokens_out is None
    for text in (render_metrics((row,)), render_report(workflow_state, (), (row,))):
        _assert_totals(text, 1, 12, "unknown", "unknown")
    assert row == original
