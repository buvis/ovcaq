from __future__ import annotations

import pytest

from ovcaq.state.schema import DecisionEntry, State, validate_state
from ovcaq.workflow.records import completed_prd_summary
from ovcaq.workflow.reports import render_audit


@pytest.mark.parametrize("status", ("applied", "escalated", "deferred"))
@pytest.mark.parametrize("content", ("", " \t\n", "0", "retained"))
def test_decision_counts_and_audit_share_substantive_content_filter(
    workflow_state: State, status: str, content: str
) -> None:
    decision: DecisionEntry = {
        "id": "",
        "kind": "",
        "summary": content,
        "rationale": "",
        "cycle": None,
        "status": status,
        "created_at": "2026-09-05T10:00:00Z",
    }
    workflow_state["review"]["decisions"] = [decision]
    validate_state(workflow_state)
    count = int(bool(content.strip()))
    summary = completed_prd_summary(workflow_state)
    assert summary["autonomous_decisions"] == (count if status == "applied" else 0)
    assert summary["escalated_decisions"] == (count if status == "escalated" else 0)
    audit = render_audit(workflow_state)
    assert (f"|  | {status} |" in audit) is bool(count)
    assert ("_No decisions recorded._" in audit) is (not count)


@pytest.mark.parametrize(
    "field,value", (("id", "id"), ("kind", "scope"), ("rationale", "why"), ("cycle", 0))
)
def test_any_substantive_cell_including_numeric_zero_survives(
    workflow_state: State, field: str, value: object
) -> None:
    decision = {
        "id": "",
        "kind": "",
        "summary": "",
        "rationale": "",
        "cycle": None,
        "status": "applied",
        "created_at": "2026-09-05T10:00:00Z",
    }
    decision[field] = value
    workflow_state["review"]["decisions"] = [decision]
    assert completed_prd_summary(workflow_state)["autonomous_decisions"] == 1
    assert "_No decisions recorded._" not in render_audit(workflow_state)
    assert f"| {value} |" in render_audit(workflow_state)
