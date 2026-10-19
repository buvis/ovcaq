from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from test_schema import (
    OWNED_OBJECT_CASES,
    _assert_schema_error,
    _at_path,
    _dotted_path,
    _neutral_invalid_state,
    _runtime_invalid_timestamps,
    _runtime_valid_timestamps,
    _set_path,
    _valid_state,
    _validate_in_neutral_process,
)

from ovcaq.state.schema import (
    MAX_ATTEMPTS_PER_TASK,
    SchemaError,
    validate_state,
    validate_timestamp,
)


def test_schema_error_is_a_value_error() -> None:
    assert issubclass(SchemaError, ValueError)


def test_validate_state_accepts_every_owned_object_and_returns_a_deep_copy(
    tmp_path: Path,
) -> None:
    source = _valid_state(tmp_path)
    source_snapshot = copy.deepcopy(source)
    source_bytes = json.dumps(
        source, ensure_ascii=False, separators=(",", ":")
    ).encode()

    validated = validate_state(source)

    assert source == source_snapshot
    assert (
        json.dumps(source, ensure_ascii=False, separators=(",", ":")).encode()
        == source_bytes
    )
    assert validated == source
    assert validated is not source
    assert validated["batch"] is not source["batch"]
    assert validated["batch"]["catchup"] is not source["batch"]["catchup"]
    assert validated["tasks"] is not source["tasks"]
    assert validated["tasks"][0] is not source["tasks"][0]
    assert validated["tasks"][0]["metadata"] is not source["tasks"][0]["metadata"]
    assert (
        validated["tasks"][0]["attempts"][0]["metadata"]
        is not source["tasks"][0]["attempts"][0]["metadata"]
    )
    assert _at_path(
        validated, ("tasks", 0, "attempts", 0, "metadata", "nested")
    ) is not _at_path(source, ("tasks", 0, "attempts", 0, "metadata", "nested"))
    assert _at_path(
        validated, ("tasks", 0, "attempts", 0, "metadata", "nested", 1)
    ) is not _at_path(source, ("tasks", 0, "attempts", 0, "metadata", "nested", 1))
    assert validated["review"]["cycles"] is not source["review"]["cycles"]
    assert validated["review"]["extensions"] is not source["review"]["extensions"]
    assert _at_path(
        validated, ("review", "extensions", "review/metadata")
    ) is not _at_path(source, ("review", "extensions", "review/metadata"))
    assert validated["control"]["attention"] is not source["control"]["attention"]
    assert validated["recovery"]["operation"] is not source["recovery"]["operation"]

    source["tasks"][0]["name"] = "mutated after validation"
    assert validated["tasks"][0]["name"] == "Validate state"


@pytest.mark.parametrize(
    "timestamp",
    _runtime_valid_timestamps(),
    ids=(
        "no-fraction",
        "one-fractional-digit",
        "two-fractional-digits",
        "three-fractional-digits",
        "four-fractional-digits",
        "five-fractional-digits",
        "six-fractional-digits",
        "different-date",
        "leap-day",
    ),
)
def test_validate_timestamp_returns_strict_utc_rfc3339_input_unchanged(
    timestamp: str,
) -> None:
    assert validate_timestamp(timestamp, "event.created_at") == timestamp


@pytest.mark.parametrize(
    "timestamp",
    _runtime_invalid_timestamps(),
    ids=(
        "none",
        "integer",
        "empty",
        "missing-zone",
        "numeric-offset",
        "lowercase-zone",
        "space-separator",
        "seven-fractional-digits",
        "invalid-leap-month-day",
        "non-leap-february-29",
        "hour-24",
    ),
)
def test_validate_timestamp_rejects_non_utc_or_malformed_values(
    timestamp: object,
) -> None:
    with pytest.raises(SchemaError) as raised:
        validate_timestamp(timestamp, "event.created_at")
    assert "event.created_at" in str(raised.value)


@pytest.mark.parametrize("value", (None, [], "state", 1, True))
def test_validate_state_rejects_non_object_documents(value: object) -> None:
    with pytest.raises(SchemaError):
        validate_state(value)


@pytest.mark.parametrize(
    ("case", "offending_path"),
    (
        pytest.param(
            "unknown-owned-field",
            "review.cycles[0].unexpected",
            id="unknown-owned-field",
        ),
        pytest.param(
            "missing-owned-field",
            "recovery.operation.destination",
            id="missing-owned-field",
        ),
        pytest.param("integer-is-boolean", "revision", id="integer-is-boolean"),
        pytest.param("duplicate-task-id", "tasks[1].id", id="duplicate-task-id"),
        pytest.param(
            "inconsistent-task-count",
            "work.tasks_total",
            id="inconsistent-task-count",
        ),
        pytest.param(
            "malformed-nested-timestamp",
            "tasks[0].attempts[0].finished_at",
            id="malformed-nested-timestamp",
        ),
        pytest.param(
            "invalid-extension-key",
            "work.extensions.Invalid Key",
            id="invalid-extension-key",
        ),
    ),
)
def test_validate_state_rejects_representative_invalid_documents_from_an_external_caller(
    tmp_path: Path,
    case: str,
    offending_path: str,
) -> None:
    result = _validate_in_neutral_process(_neutral_invalid_state(tmp_path, case))

    assert result["exception"] == "ovcaq.state.schema.SchemaError"
    assert offending_path in (result["message"] or "")


@pytest.mark.parametrize(
    ("mutation", "expected_path"),
    (
        pytest.param(
            lambda state: state["tasks"][0].__setitem__("name", "\ud800"),
            "tasks[0].name",
            id="owned-value",
        ),
        pytest.param(
            lambda state: state["tasks"][0]["metadata"].__setitem__(
                "\ud800", "invalid key"
            ),
            "tasks[0].metadata.\\ud800",
            id="open-map-key",
        ),
    ),
)
def test_validate_state_rejects_lone_surrogates_with_path_aware_schema_errors(
    tmp_path: Path,
    mutation: Any,
    expected_path: str,
) -> None:
    state = _valid_state(tmp_path)
    mutation(state)

    with pytest.raises(SchemaError) as raised:
        validate_state(state)

    assert expected_path in str(raised.value)


def test_validate_state_rejects_relative_repository_roots(tmp_path: Path) -> None:
    state = _valid_state(tmp_path)
    state["work"]["repo_root"] = "relative/repository"

    _assert_schema_error(state, "work.repo_root")


def test_validate_state_rejects_a_missing_schema_version_first(
    tmp_path: Path,
) -> None:
    state = _valid_state(tmp_path)
    del state["schema_version"]

    _assert_schema_error(state, "schema_version")


@pytest.mark.parametrize("version", (True, 0, 2, 999))
def test_validate_state_rejects_non_v1_schema_versions(
    tmp_path: Path, version: object
) -> None:
    state = _valid_state(tmp_path)
    state["schema_version"] = version  # type: ignore[typeddict-item]

    _assert_schema_error(state, "schema_version")


def test_batch_constraints_report_timestamp_before_numeric_bounds(
    tmp_path: Path,
) -> None:
    state = _valid_state(tmp_path)
    state["batch"]["parks_consecutive"] = -1
    state["batch"]["started_at"] = "malformed"

    _assert_schema_error(state, "batch.started_at")


def test_task_constraints_report_name_before_attempt_limit(tmp_path: Path) -> None:
    state = _valid_state(tmp_path)
    state["tasks"][0]["name"] = ""
    state["tasks"][0]["attempts"] *= MAX_ATTEMPTS_PER_TASK + 1

    _assert_schema_error(state, "tasks[0].name")


@pytest.mark.parametrize(("object_path", "required_field"), OWNED_OBJECT_CASES)
def test_validate_state_rejects_missing_fields_in_every_owned_object(
    tmp_path: Path,
    object_path: tuple[str | int, ...],
    required_field: str,
) -> None:
    state = _valid_state(tmp_path)
    del _at_path(state, object_path)[required_field]

    _assert_schema_error(state, _dotted_path((*object_path, required_field)))


@pytest.mark.parametrize(("object_path", "required_field"), OWNED_OBJECT_CASES)
def test_validate_state_rejects_unknown_fields_in_every_owned_object(
    tmp_path: Path,
    object_path: tuple[str | int, ...],
    required_field: str,
) -> None:
    state = _valid_state(tmp_path)
    _at_path(state, object_path)["unexpected"] = required_field

    _assert_schema_error(state, _dotted_path((*object_path, "unexpected")))


@pytest.mark.parametrize(
    ("path", "invalid_value"),
    (
        pytest.param(("revision",), True, id="revision-bool"),
        pytest.param(("revision",), -1, id="revision-negative"),
        pytest.param(("batch", "status"), "broken", id="batch-status"),
        pytest.param(
            ("batch", "parks_consecutive"), -1, id="parks-consecutive-negative"
        ),
        pytest.param(
            ("batch", "completed_prds", 0, "cycles"),
            -1,
            id="completed-prd-cycles-negative",
        ),
        pytest.param(("work", "phase"), "planning", id="phase"),
        pytest.param(("work", "next_phase"), "planning", id="next-phase"),
        pytest.param(("work", "completed_phases"), ["build"], id="completed-phases"),
        pytest.param(("tasks", 0, "id"), True, id="task-id-bool"),
        pytest.param(("tasks", 0, "id"), 0, id="task-id-zero"),
        pytest.param(("tasks", 0, "name"), "", id="task-name-empty"),
        pytest.param(("tasks", 0, "status"), "running", id="task-status"),
        pytest.param(("tasks", 0, "files_touched"), -1, id="files-touched-negative"),
        pytest.param(
            ("tasks", 0, "public_contract_edit"),
            1,
            id="public-contract-edit-int",
        ),
        pytest.param(
            ("tasks", 0, "estimates", "input_tokens"),
            -1,
            id="estimated-input-negative",
        ),
        pytest.param(
            ("tasks", 0, "estimates", "context_peak"),
            True,
            id="context-peak-bool",
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "number"), 0, id="attempt-number-zero"
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "outcome"),
            "running",
            id="attempt-outcome",
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "review_cycle"),
            0,
            id="attempt-review-cycle-zero",
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "pipeline"),
            "extended",
            id="attempt-pipeline",
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "escalation", "reason"),
            "manual",
            id="escalation-reason",
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "escalation", "diagnosis"),
            "unknown",
            id="escalation-diagnosis",
        ),
        pytest.param(("review", "cycle"), -1, id="review-cycle-negative"),
        pytest.param(("review", "cap"), 0, id="review-cap-zero"),
        pytest.param(
            ("review", "cycles", 0, "reviewers", "alice"),
            "timed_out",
            id="reviewer-status",
        ),
        pytest.param(
            ("review", "cycles", 0, "issues_found"),
            -1,
            id="issues-found-negative",
        ),
        pytest.param(
            ("review", "cycles", 0, "test_run", "exit_code"),
            True,
            id="test-exit-code-bool",
        ),
        pytest.param(
            ("review", "decisions", 0, "status"),
            "pending",
            id="decision-status",
        ),
        pytest.param(("review", "doubts", 0, "category"), "later", id="doubt-category"),
        pytest.param(("review", "doubts", 0, "status"), "open", id="doubt-status"),
        pytest.param(
            ("review", "rubric_verdicts", 0, "verdict"),
            "unknown",
            id="rubric-verdict",
        ),
        pytest.param(("review", "lenses", "alice"), "passed", id="lens-status"),
        pytest.param(("control", "attention", "site"), 1, id="notice-site-type"),
        pytest.param(("recovery", "replan_count"), -1, id="replan-count-negative"),
        pytest.param(("recovery", "operation", "kind"), "retry", id="recovery-kind"),
        pytest.param(("recovery", "operation", "step"), "complete", id="recovery-step"),
        pytest.param(
            ("batch", "capabilities", "post-drain", "failure"),
            "ignore",
            id="capability-failure",
        ),
        pytest.param(
            ("batch", "capabilities", "post-drain", "status"),
            "complete",
            id="capability-status",
        ),
        pytest.param(
            (
                "batch",
                "capabilities",
                "post-drain",
                "attempts",
                1,
                "status",
            ),
            "pending",
            id="capability-attempt-status",
        ),
    ),
)
def test_validate_state_rejects_invalid_types_enums_and_numeric_bounds(
    tmp_path: Path,
    path: tuple[str | int, ...],
    invalid_value: object,
) -> None:
    state = _valid_state(tmp_path)
    _set_path(state, path, invalid_value)

    _assert_schema_error(state, _dotted_path(path))


@pytest.mark.parametrize(
    ("path", "wrong_type"),
    (
        pytest.param(("batch", "id"), 1, id="batch-id"),
        pytest.param(("batch", "started_at"), 1, id="batch-started-at"),
        pytest.param(("batch", "completed_at"), 1, id="batch-completed-at"),
        pytest.param(("batch", "completed_prds"), {}, id="completed-prds"),
        pytest.param(("batch", "catchup"), [], id="catchup"),
        pytest.param(("batch", "capabilities"), [], id="capabilities"),
        pytest.param(("batch", "catchup", "head_sha"), 1, id="catchup-head-sha"),
        pytest.param(
            ("batch", "completed_prds", 0, "filename"),
            1,
            id="completed-prd-filename",
        ),
        pytest.param(
            ("batch", "completed_prds", 0, "autonomous_decisions"),
            True,
            id="completed-prd-autonomous-decisions",
        ),
        pytest.param(
            ("batch", "completed_prds", 0, "tasks_total"),
            True,
            id="completed-prd-tasks-total",
        ),
        pytest.param(
            ("batch", "capabilities", "post-drain", "required"),
            1,
            id="capability-required",
        ),
        pytest.param(
            ("batch", "capabilities", "post-drain", "launcher"),
            1,
            id="capability-launcher",
        ),
        pytest.param(
            ("batch", "capabilities", "post-drain", "plugin"),
            1,
            id="capability-plugin",
        ),
        pytest.param(
            ("batch", "capabilities", "post-drain", "version"),
            1,
            id="capability-version",
        ),
        pytest.param(
            ("batch", "capabilities", "post-drain", "attempts"),
            {},
            id="capability-attempts",
        ),
        pytest.param(
            (
                "batch",
                "capabilities",
                "post-drain",
                "attempts",
                1,
                "id",
            ),
            1,
            id="capability-attempt-id",
        ),
        pytest.param(
            (
                "batch",
                "capabilities",
                "post-drain",
                "attempts",
                1,
                "started_at",
            ),
            1,
            id="capability-attempt-started-at",
        ),
        pytest.param(
            (
                "batch",
                "capabilities",
                "post-drain",
                "attempts",
                1,
                "session_id",
            ),
            1,
            id="capability-attempt-session-id",
        ),
        pytest.param(
            (
                "batch",
                "capabilities",
                "post-drain",
                "attempts",
                1,
                "detail",
            ),
            1,
            id="capability-attempt-detail",
        ),
        pytest.param(("work", "prd"), 1, id="work-prd"),
        pytest.param(("work", "repo_root"), 1, id="repo-root"),
        pytest.param(("work", "design_doc"), 1, id="design-doc"),
        pytest.param(("work", "contract_card"), 1, id="contract-card"),
        pytest.param(("work", "tasks_total"), True, id="tasks-total-bool"),
        pytest.param(("work", "tasks_completed"), True, id="tasks-completed-bool"),
        pytest.param(("work", "extensions"), [], id="work-extensions"),
        pytest.param(("tasks",), {}, id="tasks"),
        pytest.param(("tasks", 0, "description"), 1, id="task-description"),
        pytest.param(("tasks", 0, "active_form"), 1, id="task-active-form"),
        pytest.param(("tasks", 0, "blocked_by"), {}, id="task-blocked-by"),
        pytest.param(("tasks", 0, "tier"), 1, id="task-tier"),
        pytest.param(("tasks", 0, "attempts"), {}, id="task-attempts"),
        pytest.param(("tasks", 0, "metadata"), [], id="task-metadata"),
        pytest.param(("tasks", 0, "attempts", 0, "tier"), 1, id="attempt-tier"),
        pytest.param(("tasks", 0, "attempts", 0, "driver"), 1, id="attempt-driver"),
        pytest.param(("tasks", 0, "attempts", 0, "cause"), 1, id="attempt-cause"),
        pytest.param(
            ("tasks", 0, "attempts", 0, "cleanup_outcome"),
            1,
            id="attempt-cleanup-outcome",
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "started_at"),
            1,
            id="attempt-started-at",
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "commit_sha"),
            1,
            id="attempt-commit-sha",
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "escalation"),
            [],
            id="attempt-escalation",
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "metadata"),
            [],
            id="attempt-metadata",
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "escalation", "from_tier"),
            1,
            id="escalation-from-tier",
        ),
        pytest.param(
            ("tasks", 0, "attempts", 0, "escalation", "repair_used"),
            1,
            id="escalation-repair-used",
        ),
        pytest.param(("review", "cycles"), {}, id="review-cycles"),
        pytest.param(("review", "decisions"), {}, id="review-decisions"),
        pytest.param(("review", "doubts"), {}, id="review-doubts"),
        pytest.param(("review", "rubric_verdicts"), {}, id="review-rubric-verdicts"),
        pytest.param(("review", "rework_task_ids"), {}, id="review-rework-task-ids"),
        pytest.param(("review", "lenses"), [], id="review-lenses"),
        pytest.param(("review", "extensions"), [], id="review-extensions"),
        pytest.param(
            ("review", "cycles", 0, "review_file"),
            1,
            id="review-cycle-file",
        ),
        pytest.param(
            ("review", "cycles", 0, "reviewers"),
            [],
            id="review-cycle-reviewers",
        ),
        pytest.param(
            ("review", "cycles", 0, "recurring_issues"),
            {},
            id="review-cycle-recurring-issues",
        ),
        pytest.param(
            ("review", "cycles", 0, "decision_gate"),
            [],
            id="review-cycle-decision-gate",
        ),
        pytest.param(
            ("review", "cycles", 0, "rework_commits"),
            {},
            id="review-cycle-rework-commits",
        ),
        pytest.param(
            ("review", "cycles", 0, "rework_notes"),
            {},
            id="review-cycle-rework-notes",
        ),
        pytest.param(
            ("review", "cycles", 0, "fix_audit"),
            {},
            id="review-cycle-fix-audit",
        ),
        pytest.param(
            ("review", "cycles", 0, "test_run"),
            [],
            id="review-cycle-test-run",
        ),
        pytest.param(
            ("review", "cycles", 0, "decision_gate", "decision"),
            1,
            id="decision-gate-decision",
        ),
        pytest.param(
            ("review", "cycles", 0, "decision_gate", "detail"),
            1,
            id="decision-gate-detail",
        ),
        pytest.param(
            ("review", "cycles", 0, "test_run", "command"),
            "pytest",
            id="test-run-command",
        ),
        pytest.param(
            ("review", "cycles", 0, "test_run", "summary"),
            1,
            id="test-run-summary",
        ),
        pytest.param(("review", "decisions", 0, "summary"), 1, id="decision-summary"),
        pytest.param(("review", "decisions", 0, "cycle"), "1", id="decision-cycle"),
        pytest.param(
            ("review", "doubts", 0, "description"),
            1,
            id="doubt-description",
        ),
        pytest.param(
            ("review", "doubts", 0, "justification"),
            1,
            id="doubt-justification",
        ),
        pytest.param(
            ("review", "rubric_verdicts", 0, "rule_id"),
            1,
            id="rubric-rule-id",
        ),
        pytest.param(("control", "pause_requested"), 1, id="pause-requested"),
        pytest.param(("control", "pause_reason"), [], id="pause-reason"),
        pytest.param(("recovery", "operation"), [], id="recovery-operation"),
        pytest.param(("recovery", "phase_fingerprint"), 1, id="phase-fingerprint"),
        pytest.param(("recovery", "phase_repeats"), True, id="phase-repeats"),
        pytest.param(("recovery", "operation", "id"), 1, id="recovery-operation-id"),
        pytest.param(("recovery", "operation", "prd"), 1, id="recovery-operation-prd"),
        pytest.param(
            ("recovery", "operation", "source"),
            1,
            id="recovery-operation-source",
        ),
        pytest.param(
            ("recovery", "operation", "destination"),
            1,
            id="recovery-operation-destination",
        ),
    ),
)
def test_validate_state_rejects_wrong_field_types_at_their_full_paths(
    tmp_path: Path,
    path: tuple[str | int, ...],
    wrong_type: object,
) -> None:
    state = _valid_state(tmp_path)
    _set_path(state, path, wrong_type)

    _assert_schema_error(state, _dotted_path(path))


def test_validate_state_does_not_mutate_invalid_input(tmp_path: Path) -> None:
    state = _valid_state(tmp_path)
    state["tasks"][0]["name"] = 1  # type: ignore[typeddict-item]
    snapshot = copy.deepcopy(state)

    _assert_schema_error(state, "tasks[0].name")

    assert state == snapshot
