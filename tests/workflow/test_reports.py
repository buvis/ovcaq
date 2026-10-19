from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

from ovcaq.state.schema import CompletedPrd, State, validate_state
from ovcaq.workflow.reports import (
    ReportError,
    archive_final_state,
    load_metric_rows,
    publish_audit,
    publish_report,
    reduce_metrics,
    render_audit,
    render_metrics,
    render_report,
)

METRICS_FIXTURE = Path("tests/fixtures/claude/legacy-metrics.jsonl")


def _metric_rows(*, batch_id: str = "20260830-120000") -> tuple[dict[str, object], ...]:
    return tuple(
        {**row, "batch": batch_id} for row in load_metric_rows(METRICS_FIXTURE)
    )


def _decision(identifier: str, status: str) -> dict[str, object]:
    return {
        "id": identifier,
        "kind": "scope",
        "summary": f"Summary {identifier} | safe",
        "rationale": f"Rationale {identifier}\nsecond line",
        "cycle": 1,
        "created_at": "2026-08-30T12:10:00Z",
        "status": status,
    }


def _task(identifier: int, status: str) -> dict[str, object]:
    return {
        "id": identifier,
        "name": f"task-{identifier}",
        "description": f"Reporting fixture task {identifier}",
        "active_form": f"Running task {identifier}",
        "status": status,
        "blocked_by": [],
        "tier": None,
        "files_touched": None,
        "public_contract_edit": None,
        "estimates": {"input_tokens": None, "context_peak": None},
        "attempts": [],
        "metadata": {},
    }


def _populate_report_cycles(state: State) -> None:
    state["review"]["cycles"] = [
        {
            "cycle": 1,
            "review_file": "docs/dev/project-management/reviews/review-1.md",
            "reviewers": {"consensus": "passed", "blind": "passed"},
            "issues_found": 2,
            "follow_up_tasks": 1,
            "deferred": 1,
            "recurring_issues": [],
            "decision_gate": None,
            "rework_commits": [],
            "rework_notes": [],
            "fix_audit": [],
            "test_run": None,
        }
    ]


def _populated(state: State) -> State:
    state["review"]["cycle"] = 1
    state["review"]["decisions"] = [
        _decision("applied", "applied"),
        _decision("deferred", "deferred"),
        _decision("escalated", "escalated"),
    ]  # type: ignore[typeddict-item]
    state["review"]["doubts"] = [
        {
            "id": "doubt-1",
            "description": "Verify | boundary",
            "category": "verify",
            "justification": "needs replay",
            "status": "pending",
            "source": "review",
        }
    ]
    _populate_report_cycles(state)
    state["work"]["tasks_total"] = 3
    state["work"]["tasks_completed"] = 2
    state["tasks"] = [
        _task(1, "completed"),
        _task(2, "completed"),
        _task(3, "pending"),
    ]  # type: ignore[typeddict-item]
    state["batch"]["completed_prds"] = [
        {
            "filename": "00003-state-kernel-v1.md",
            "cycles": 2,
            "autonomous_decisions": 4,
            "escalated_decisions": 1,
            "tasks_completed": 12,
            "tasks_total": 12,
        }
    ]
    return state


def test_audit_render_is_deterministic_and_table_safe(workflow_state: State) -> None:
    state = _populated(workflow_state)

    first = render_audit(state)
    second = render_audit(state)

    assert first == second
    assert first.startswith("# Workflow audit: 00004-workflow-core-v1.md\n")
    assert "| applied | applied | 1 | scope | Summary applied \\| safe |" in first
    assert "Rationale applied second line" in first
    assert "| doubt-1 | pending | verify | Verify \\| boundary |" in first


def test_report_render_combines_state_and_operation_deduped_records(
    workflow_state: State,
) -> None:
    state = _populated(workflow_state)
    records = [
        {
            "op_id": "operation-1",
            "prd": "00004-workflow-core-v1.md",
            "type": "stall",
            "site": "design_gate",
            "detail": "approval | missing",
        },
        {
            "op_id": "operation-1",
            "prd": "00004-workflow-core-v1.md",
            "type": "stall",
            "site": "design_gate",
            "detail": "approval | missing",
        },
    ]

    rows = (
        *_metric_rows(),
        {
            "batch": "another-batch",
            "phase_launched": "review",
            "wall_secs": 1000,
            "cost_usd": 1000,
            "tokens_out": 1000,
        },
    )
    text = render_report(state, records, rows)

    assert text.count("| operation-1 |") == 1
    assert "| 00003-state-kernel-v1.md | 2 | 12/12 | 4 | 1 |" in text
    assert "approval \\| missing" in text
    assert "- Sessions: 2" in text
    assert "- Wall seconds: 27" in text
    assert "- Cost USD: 0.27" in text
    assert "- Output tokens: 22" in text
    assert text == render_report(
        state,
        reversed(records),
        reversed(rows),
    )


def test_metrics_render_reduces_retained_characterized_rows() -> None:
    rows = _metric_rows()

    summary = reduce_metrics(rows)
    text = render_metrics(rows)

    assert summary.sessions == 2
    assert summary.wall_secs == 27
    assert str(summary.cost_usd) == "0.27"
    assert summary.tokens_out == 22
    assert summary.review_convergences == 1
    assert summary.cycles_to_converge == 2
    assert "- Sessions: 2" in text
    assert "- Wall seconds: 27" in text
    assert "- Cost USD: 0.27" in text
    assert "- Output tokens: 22" in text
    assert "- Review convergences: 1" in text
    assert "- Cycles to converge: 2" in text
    assert "| 00000-example.md | build | build | continue |" in text
    assert "| 00000-example.md | 2 | converged |" in text
    assert text == render_metrics(reversed(rows))


def test_empty_metrics_bind_legitimate_zero_totals_to_report(
    workflow_state: State,
) -> None:
    metrics = render_metrics(())
    report = render_report(workflow_state, (), ())

    for text in (metrics, report):
        assert "- Sessions: 0" in text
        assert "- Wall seconds: 0" in text
        assert "- Cost USD: 0.00" in text
        assert "- Output tokens: 0" in text
        assert "- Review convergences: 0" in text
        assert "- Cycles to converge: 0" in text
    assert "- PRDs completed: 0" in report
    assert "- Total cycles: 0" in report
    assert "- Applied decisions: 0" in report
    assert "- Escalated decisions: 0" in report


def test_missing_values_remain_unknown_in_nonempty_metric_totals() -> None:
    rows = (
        {
            "batch": "batch-1",
            "phase_launched": "build",
            "wall_secs": 100,
        },
    )

    text = render_metrics(rows)

    assert "- Wall seconds: 100" in text
    assert "- Cost USD: unknown" in text
    assert "- Output tokens: unknown" in text


@pytest.mark.parametrize("mixed", (False, True), ids=("legacy", "mixed"))
@pytest.mark.parametrize(
    "legacy",
    ({"filename": "00001-legacy.md"}, "00001-legacy.md"),
    ids=("partial-record", "filename-only"),
)
def test_completed_summary_legacy_and_mixed_rows_keep_unknown_totals(
    workflow_state: State, mixed: bool, legacy: object
) -> None:
    state = _populated(workflow_state)
    rich = state["batch"]["completed_prds"][0]
    state["batch"]["completed_prds"] = cast(
        list[CompletedPrd], [rich, legacy] if mixed else [legacy]
    )

    text = render_report(state, ())

    assert f"- PRDs completed: {2 if mixed else 1}" in text
    assert "- Total cycles: unknown" in text
    assert "- Applied decisions: unknown" in text
    assert "- Escalated decisions: unknown" in text
    assert "| 00001-legacy.md | unknown | unknown/unknown | unknown | unknown |" in text


@pytest.mark.parametrize("value", (None, True, "2"))
def test_completed_summary_unknowns_are_per_field(
    workflow_state: State, value: object
) -> None:
    state = _populated(workflow_state)
    state["batch"]["completed_prds"][0]["cycles"] = value  # type: ignore[typeddict-item]

    text = render_report(state, ())

    assert "- Total cycles: unknown" in text
    assert "- Applied decisions: 4" in text
    assert "- Escalated decisions: 1" in text
    assert "| 00003-state-kernel-v1.md | unknown | 12/12 | 4 | 1 |" in text


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("phase_end", "review"),
        ("signal", "done"),
        ("model", "other-tier"),
        ("wall_secs", 3),
        ("cost_usd", 0.01),
        ("tokens_out", 5),
    ),
)
def test_session_sort_key_collisions_have_deterministic_order(
    field: str, value: object
) -> None:
    first = _metric_rows()[0]
    second = {**first, field: value}

    assert render_metrics((first, second)) == render_metrics((second, first))


@pytest.mark.parametrize(
    ("field", "value"), (("cycles_to_converge", 3), ("outcome", "other"))
)
def test_convergence_sort_key_collisions_have_deterministic_order(
    field: str, value: object
) -> None:
    first = _metric_rows()[-1]
    second = {**first, field: value}

    assert render_metrics((first, second)) == render_metrics((second, first))


@pytest.mark.parametrize("kind", ("fifo", "directory", "socket"))
def test_report_nonregular_target_is_rejected_without_blocking(
    tmp_path: Path, workflow_state: State, kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "reports" / "20260830-120000-report.md"
    target.parent.mkdir()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        if kind == "fifo":
            os.mkfifo(target)
        elif kind == "directory":
            target.mkdir()
        else:
            monkeypatch.chdir(target.parent)
            listener.bind(target.name)
        before = target.lstat()
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import json, sys
from pathlib import Path
from ovcaq.workflow.reports import publish_report
try:
    publish_report(Path(sys.argv[1]), json.loads(sys.argv[2]), ())
except OSError:
    sys.exit(2)
""",
                str(tmp_path),
                json.dumps(workflow_state),
            ],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )

    assert result.returncode == 2, result.stderr
    assert target.lstat().st_ino == before.st_ino
    assert target.lstat().st_mode == before.st_mode
    assert list(target.parent.iterdir()) == [target]


def test_audit_and_report_publication_are_byte_idempotent(
    tmp_path: Path,
    workflow_state: State,
) -> None:
    state = _populated(workflow_state)
    runtime = tmp_path / "docs" / "dev" / "project-management" / "ovcaq"
    runtime.mkdir(parents=True)

    audit_path = publish_audit(tmp_path, state)
    rows = load_metric_rows(METRICS_FIXTURE)
    report_path = publish_report(runtime, state, [], rows)
    audit_before = audit_path.read_bytes()
    report_before = report_path.read_bytes()

    assert publish_audit(tmp_path, state) == audit_path
    assert publish_report(runtime, state, [], rows) == report_path
    assert audit_path.read_bytes() == audit_before
    assert report_path.read_bytes() == report_before
    assert audit_path == (
        tmp_path / "docs/dev/project-management/reviews/00004-workflow-core-v1-audit.md"
    )
    assert report_path == runtime / "reports/20260830-120000-report.md"


def test_report_publication_replaces_only_the_active_prd_section(
    tmp_path: Path,
    workflow_state: State,
) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    first_path = publish_report(runtime, _populated(workflow_state), [])
    first_text = first_path.read_text(encoding="utf-8")

    workflow_state["work"]["prd"] = "00005-runtime-v1.md"
    workflow_state["work"]["tasks_completed"] = 1
    workflow_state["work"]["tasks_total"] = 2
    publish_report(runtime, workflow_state, [])
    workflow_state["work"]["prd"] = "00004-workflow-core-v1.md"
    publish_report(runtime, workflow_state, [])
    text = first_path.read_text(encoding="utf-8")

    assert first_text.count("## 00004-workflow-core-v1.md") == 1
    assert text.count("## 00004-workflow-core-v1.md") == 1
    assert text.count("## 00005-runtime-v1.md") == 1
    assert text.count("# Workflow report: 20260830-120000") == 1
    assert text.count("## Batch Summary") == 1
    assert "- Total cycles: 2" in text
    assert "- Applied decisions: 4" in text
    assert "- Escalated decisions: 1" in text


def test_report_publication_collapses_preexisting_duplicate_prd_sections(
    tmp_path: Path,
    workflow_state: State,
) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    path = publish_report(runtime, _populated(workflow_state), [])
    text = path.read_text(encoding="utf-8")
    start = text.index("## 00004-workflow-core-v1.md")
    end = text.index("## Batch Summary")
    duplicate = text[start:end]
    path.write_text(
        text + "\n## Unrelated\n\nKeep me.\n\n" + duplicate, encoding="utf-8"
    )

    publish_report(runtime, workflow_state, [])
    repaired = path.read_text(encoding="utf-8")

    assert repaired.count("## 00004-workflow-core-v1.md") == 1
    assert repaired.count("## Batch Summary") == 1
    assert "## Unrelated\n\nKeep me." in repaired


def test_final_state_archive_is_canonical_and_byte_idempotent(
    tmp_path: Path,
    workflow_state: State,
) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    workflow_state["work"]["phase"] = "done"
    workflow_state["work"]["next_phase"] = ""

    path = archive_final_state(runtime, workflow_state)
    before = path.read_bytes()

    assert archive_final_state(runtime, workflow_state) == path
    assert path.read_bytes() == before
    assert json.loads(before) == workflow_state
    assert path == runtime / "reports/20260830-120000-state-final.json"


def test_final_state_archive_rejects_nonterminal_state(
    tmp_path: Path,
    workflow_state: State,
) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()

    with pytest.raises(ValueError, match="terminal drained state"):
        archive_final_state(runtime, workflow_state)

    assert not (runtime / "reports").exists()


def test_report_publication_rejects_path_unsafe_batch_id(
    tmp_path: Path,
    workflow_state: State,
) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    workflow_state["batch"]["id"] = "../escaped"

    with pytest.raises(ValueError, match="batch.id"):
        publish_report(runtime, workflow_state, [])

    assert not (runtime / "reports").exists()
    assert not (runtime / "escaped-report.md").exists()


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("batch", "safe\nunsafe"),
        ("prd", "00004-safe\n## Injected.md"),
    ),
)
def test_report_publication_rejects_control_characters_with_domain_error(
    tmp_path: Path,
    workflow_state: State,
    field: str,
    value: str,
) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    if field == "batch":
        workflow_state["batch"]["id"] = value
    else:
        workflow_state["work"]["prd"] = value

    with pytest.raises(ReportError, match="printable path-safe component"):
        publish_report(runtime, workflow_state, [], ())

    assert not (runtime / "reports").exists()


def test_public_renderers_reject_control_characters_in_headings(
    workflow_state: State,
) -> None:
    workflow_state["work"]["prd"] = "00004-safe\n## Injected.md"

    with pytest.raises(ReportError, match="work.prd"):
        render_audit(workflow_state)
    with pytest.raises(ReportError, match="work.prd"):
        render_report(workflow_state, (), ())


def test_report_publication_rejects_symlinked_parent_without_touching_external(
    tmp_path: Path,
    workflow_state: State,
) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    external = tmp_path / "external-reports"
    external.mkdir()
    sentinel = external / "20260830-120000-report.md"
    sentinel.write_text("sentinel\n", encoding="utf-8")
    (runtime / "reports").symlink_to(external, target_is_directory=True)

    with pytest.raises(OSError):
        publish_report(runtime, workflow_state, [])

    assert sentinel.read_text(encoding="utf-8") == "sentinel\n"


def test_render_surfaces_match_migrated_v1_goldens(
    workflow_state: State,
) -> None:
    state = _populated(workflow_state)
    fixture = Path("tests/fixtures/workflow/reports")
    records = json.loads(fixture.joinpath("deferred.json").read_text(encoding="utf-8"))[
        "items"
    ]
    metric_rows = _metric_rows()
    expected = fixture / "expected"

    validate_state(state)

    assert render_audit(state) == expected.joinpath("audit.md").read_text(
        encoding="utf-8"
    )
    assert render_report(state, records, metric_rows) == expected.joinpath(
        "report.md"
    ).read_text(encoding="utf-8")
    assert render_metrics(metric_rows) == expected.joinpath("metrics.md").read_text(
        encoding="utf-8"
    )
