from __future__ import annotations

import copy
from pathlib import Path
from typing import (
    Any,
    ForwardRef,
    Literal,
    get_args,
    get_origin,
    get_type_hints,
    is_typeddict,
)

import pytest

from ovcaq.state import schema as state_schema
from ovcaq.state.schema import (
    MAX_ATTEMPTS_PER_TASK,
    MAX_CAPABILITIES,
    MAX_COMMAND_PAYLOAD_BYTES,
    MAX_CONTRACT_CARD_BYTES,
    MAX_JSON_DEPTH,
    MAX_JSON_INTEGER_DIGITS,
    MAX_OPEN_MAP_ITEMS,
    MAX_REVIEW_CYCLES,
    MAX_REVIEW_ITEMS,
    MAX_STATE_BYTES,
    MAX_STRING_BYTES,
    MAX_TASKS,
    SCHEMA_VERSION,
    TIMESTAMP_FORMAT,
    ArtifactIdentity,
    AttemptEntry,
    AttemptOutcome,
    BatchState,
    BatchStatus,
    CapabilityAttempt,
    CapabilityEntry,
    CapabilityStatus,
    CatchupCache,
    CompletedPrd,
    ControlState,
    DecisionEntry,
    DecisionGate,
    DecisionStatus,
    DoubtEntry,
    EscalationEntry,
    JSONScalar,
    JSONValue,
    NextPhase,
    Notice,
    Phase,
    RecoveryKind,
    RecoveryOperation,
    RecoveryState,
    RecoveryStep,
    ReviewCategory,
    ReviewCycle,
    ReviewerStatus,
    ReviewItemStatus,
    ReviewState,
    RubricVerdict,
    State,
    TaskEntry,
    TaskEstimates,
    TaskStatus,
    WorkState,
    validate_state,
)
from ovcaq.state.schema import (
    TestRun as StateTestRun,
)

JSON_VALUE_MAP_ANNOTATION = "dict[str,JSONValue]"


from test_schema import (
    T0,
    T1,
    T2,
    T3,
    _assert_schema_error,
    _valid_state,
)


def test_schema_constants_match_the_v1_protocol_limits() -> None:
    assert {
        "schema_version": SCHEMA_VERSION,
        "timestamp_format": TIMESTAMP_FORMAT,
        "max_state_bytes": MAX_STATE_BYTES,
        "max_command_payload_bytes": MAX_COMMAND_PAYLOAD_BYTES,
        "max_string_bytes": MAX_STRING_BYTES,
        "max_contract_card_bytes": MAX_CONTRACT_CARD_BYTES,
        "max_json_depth": MAX_JSON_DEPTH,
        "max_json_integer_digits": MAX_JSON_INTEGER_DIGITS,
        "max_tasks": MAX_TASKS,
        "max_attempts_per_task": MAX_ATTEMPTS_PER_TASK,
        "max_review_cycles": MAX_REVIEW_CYCLES,
        "max_review_items": MAX_REVIEW_ITEMS,
        "max_capabilities": MAX_CAPABILITIES,
        "max_open_map_items": MAX_OPEN_MAP_ITEMS,
    } == {
        "schema_version": 1,
        "timestamp_format": "UTC RFC 3339: YYYY-MM-DDTHH:MM:SS[.ffffff]Z",
        "max_state_bytes": 16 * 1024 * 1024,
        "max_command_payload_bytes": 2 * 1024 * 1024,
        "max_string_bytes": 1024 * 1024,
        "max_contract_card_bytes": 64 * 1024,
        "max_json_depth": 32,
        "max_json_integer_digits": 640,
        "max_tasks": 512,
        "max_attempts_per_task": 64,
        "max_review_cycles": 32,
        "max_review_items": 1024,
        "max_capabilities": 64,
        "max_open_map_items": 256,
    }


def _resolve_non_recursive_annotation(annotation: object) -> object:
    holder = type(
        "_AnnotationHolder",
        (),
        {"__annotations__": {"value": annotation}},
    )
    return get_type_hints(
        holder,
        globalns=vars(state_schema),
        localns=vars(state_schema),
    )["value"]


def _json_value_map_annotation(annotation: object) -> str | None:
    if isinstance(annotation, ForwardRef):
        return "".join(annotation.__forward_arg__.split())
    if isinstance(annotation, str):
        return "".join(annotation.split())
    if get_origin(annotation) is dict and get_args(annotation) == (str, JSONValue):
        return JSON_VALUE_MAP_ANNOTATION
    return None


@pytest.mark.parametrize(
    ("owner", "expected_annotations"),
    (
        (
            State,
            {
                "schema_version": int,
                "revision": int,
                "batch": BatchState,
                "work": WorkState,
                "tasks": list[TaskEntry],
                "review": ReviewState,
                "control": ControlState,
                "recovery": RecoveryState,
            },
        ),
        (
            BatchState,
            {
                "id": str,
                "status": BatchStatus,
                "started_at": str | None,
                "completed_at": str | None,
                "completed_prds": list[CompletedPrd],
                "parks_consecutive": int,
                "catchup": CatchupCache,
                "capabilities": dict[str, CapabilityEntry],
            },
        ),
        (
            CatchupCache,
            {
                "completed_at": str | None,
                "head_sha": str | None,
            },
        ),
        (
            CompletedPrd,
            {
                "filename": str,
                "cycles": int,
                "autonomous_decisions": int,
                "escalated_decisions": int,
                "tasks_completed": int,
                "tasks_total": int,
            },
        ),
        (
            WorkState,
            {
                "prd": str | None,
                "phase": Phase,
                "next_phase": NextPhase,
                "completed_phases": list[Literal["review"]],
                "work_start_sha": str | None,
                "repo_root": str,
                "design_doc": str | None,
                "contract_card": str | None,
                "tasks_total": int,
                "tasks_completed": int,
                "extensions": JSON_VALUE_MAP_ANNOTATION,
            },
        ),
        (
            TaskEntry,
            {
                "id": int,
                "name": str,
                "description": str,
                "active_form": str,
                "status": TaskStatus,
                "blocked_by": list[int],
                "tier": str | None,
                "files_touched": int | None,
                "public_contract_edit": bool | None,
                "estimates": TaskEstimates,
                "attempts": list[AttemptEntry],
                "metadata": JSON_VALUE_MAP_ANNOTATION,
            },
        ),
        (
            TaskEstimates,
            {
                "input_tokens": int | None,
                "context_peak": int | None,
            },
        ),
        (
            AttemptEntry,
            {
                "number": int,
                "tier": str,
                "driver": str,
                "outcome": AttemptOutcome,
                "review_cycle": int | None,
                "cause": str | None,
                "pipeline": Literal["minimal", "lean", "full"] | None,
                "cleanup_outcome": str | None,
                "started_at": str,
                "finished_at": str,
                "commit_sha": str | None,
                "escalation": EscalationEntry | None,
                "metadata": JSON_VALUE_MAP_ANNOTATION,
            },
        ),
        (
            EscalationEntry,
            {
                "reason": Literal["gate_failure", "review_flag", "rescue"],
                "from_tier": str,
                "diagnosis": Literal["spec_gap", "solid_spec"] | None,
                "repair_used": bool,
            },
        ),
        (
            ReviewState,
            {
                "cycle": int,
                "cap": int,
                "cycles": list[ReviewCycle],
                "decisions": list[DecisionEntry],
                "doubts": list[DoubtEntry],
                "rubric_verdicts": list[RubricVerdict],
                "rework_task_ids": list[int],
                "lenses": dict[
                    str, Literal["pending", "running", "completed", "failed"]
                ],
                "extensions": JSON_VALUE_MAP_ANNOTATION,
            },
        ),
        (
            ReviewCycle,
            {
                "cycle": int,
                "review_file": str,
                "reviewers": dict[str, ReviewerStatus],
                "issues_found": int,
                "follow_up_tasks": int,
                "deferred": int,
                "recurring_issues": list[str],
                "decision_gate": DecisionGate | None,
                "rework_commits": list[str],
                "rework_notes": list[str],
                "fix_audit": list[str],
                "test_run": StateTestRun | None,
            },
        ),
        (
            DecisionGate,
            {
                "decision": str,
                "detail": str,
                "decided_at": str,
            },
        ),
        (
            StateTestRun,
            {
                "command": list[str],
                "exit_code": int,
                "summary": str,
            },
        ),
        (
            DecisionEntry,
            {
                "id": str,
                "kind": str,
                "summary": str,
                "rationale": str,
                "cycle": int | None,
                "created_at": str,
                "status": DecisionStatus,
            },
        ),
        (
            DoubtEntry,
            {
                "id": str,
                "description": str,
                "category": ReviewCategory,
                "justification": str | None,
                "status": ReviewItemStatus,
                "source": str | None,
            },
        ),
        (
            RubricVerdict,
            {
                "rule_id": str,
                "verdict": Literal["pass", "fail"],
                "source": str | None,
            },
        ),
        (
            ControlState,
            {
                "pause_requested": bool,
                "pause_reason": Notice | None,
                "attention": Notice | None,
            },
        ),
        (
            Notice,
            {
                "site": str,
                "detail": str,
                "created_at": str,
            },
        ),
        (
            RecoveryState,
            {
                "operation": RecoveryOperation | None,
                "replan_count": int,
                "phase_fingerprint": str | None,
                "phase_repeats": int,
            },
        ),
        (
            ArtifactIdentity,
            {"device": int, "inode": int},
        ),
        (
            RecoveryOperation,
            {
                "id": str,
                "kind": RecoveryKind,
                "step": RecoveryStep,
                "prd": str,
                "site": str,
                "detail": str,
                "source": str,
                "destination": str,
                "artifact": ArtifactIdentity | None,
                "created_at": str,
            },
        ),
        (
            CapabilityEntry,
            {
                "required": bool,
                "launcher": str,
                "plugin": str,
                "version": str,
                "failure": Literal["attention"],
                "status": CapabilityStatus,
                "attempts": list[CapabilityAttempt],
            },
        ),
        (
            CapabilityAttempt,
            {
                "id": str,
                "status": Literal["running", "failed", "succeeded"],
                "started_at": str,
                "finished_at": str | None,
                "session_id": str | None,
                "detail": str | None,
            },
        ),
    ),
    ids=(
        "state",
        "batch",
        "catchup-cache",
        "completed-prd",
        "work",
        "task",
        "task-estimates",
        "attempt",
        "escalation",
        "review",
        "review-cycle",
        "decision-gate",
        "test-run",
        "decision",
        "doubt",
        "rubric-verdict",
        "control",
        "notice",
        "recovery",
        "artifact-identity",
        "recovery-operation",
        "capability",
        "capability-attempt",
    ),
)
def test_nested_schema_owner_requires_exactly_its_documented_annotations(
    owner: Any, expected_annotations: dict[str, object]
) -> None:
    assert is_typeddict(owner)
    assert owner.__module__ == state_schema.__name__
    assert getattr(state_schema, owner.__name__) is owner
    assert owner.__total__ is True
    assert owner.__required_keys__ == frozenset(expected_annotations)
    assert owner.__optional_keys__ == frozenset()
    for field, expected_annotation in expected_annotations.items():
        actual_annotation = owner.__annotations__[field]
        if expected_annotation == JSON_VALUE_MAP_ANNOTATION:
            assert (
                _json_value_map_annotation(actual_annotation)
                == JSON_VALUE_MAP_ANNOTATION
            )
        else:
            assert (
                _resolve_non_recursive_annotation(actual_annotation)
                == expected_annotation
            )


@pytest.mark.parametrize(
    ("symbol_name", "literal", "expected_values"),
    (
        ("Phase", Phase, {"build", "review", "done", "paused"}),
        ("NextPhase", NextPhase, {"build", "review", "done", "paused", ""}),
        (
            "BatchStatus",
            BatchStatus,
            {"idle", "running", "attention", "completed"},
        ),
        ("TaskStatus", TaskStatus, {"pending", "in_progress", "completed"}),
        (
            "AttemptOutcome",
            AttemptOutcome,
            {"completed", "aborted", "review_flagged", "rework_failed", "escalated"},
        ),
        (
            "CapabilityStatus",
            CapabilityStatus,
            {"pending", "running", "failed", "succeeded", "skipped"},
        ),
        ("ReviewCategory", ReviewCategory, {"fix", "verify", "known"}),
        ("ReviewItemStatus", ReviewItemStatus, {"pending", "resolved"}),
        (
            "ReviewerStatus",
            ReviewerStatus,
            {"available", "unavailable", "disabled", "passed", "failed"},
        ),
        (
            "DecisionStatus",
            DecisionStatus,
            {"applied", "deferred", "escalated"},
        ),
        ("RecoveryKind", RecoveryKind, {"park", "stall"}),
        ("RecoveryStep", RecoveryStep, {"intent", "moved", "recorded"}),
    ),
    ids=(
        "phase",
        "next-phase",
        "batch-status",
        "task-status",
        "attempt-outcome",
        "capability-status",
        "review-category",
        "review-item-status",
        "reviewer-status",
        "decision-status",
        "recovery-kind",
        "recovery-step",
    ),
)
def test_state_literal_accepts_exactly_the_documented_values(
    symbol_name: str, literal: object, expected_values: set[str]
) -> None:
    assert getattr(state_schema, symbol_name) is literal
    assert set(get_args(literal)) == expected_values


def test_json_aliases_define_only_recursive_finite_json_values() -> None:
    assert state_schema.JSONScalar is JSONScalar
    assert state_schema.JSONValue is JSONValue
    assert set(get_args(JSONScalar)) == {str, int, float, bool, type(None)}
    assert set(get_args(JSONValue)) == {
        str,
        int,
        float,
        bool,
        type(None),
        list[ForwardRef("JSONValue")],
        dict[str, ForwardRef("JSONValue")],
    }


def test_validate_state_accepts_a_completed_batch_with_succeeded_requirements(
    tmp_path: Path,
) -> None:
    state = _valid_state(tmp_path)
    state["batch"]["status"] = "completed"
    state["batch"]["completed_at"] = T3

    assert validate_state(state) == state


@pytest.mark.parametrize(
    ("mutation", "expected_path"),
    (
        pytest.param(
            lambda state: state["batch"].__setitem__("id", ""),
            "batch.id",
            id="running-empty-id",
        ),
        pytest.param(
            lambda state: (
                state["batch"].__setitem__("status", "completed"),
                state["batch"].__setitem__("completed_at", None),
            ),
            "batch.completed_at",
            id="completed-without-time",
        ),
        pytest.param(
            lambda state: (
                state["batch"].__setitem__("status", "completed"),
                state["batch"].__setitem__("completed_at", T3),
                state["batch"]["capabilities"]["post-drain"].__setitem__(
                    "status", "failed"
                ),
                state["batch"]["capabilities"]["post-drain"]["attempts"][
                    -1
                ].__setitem__("status", "failed"),
            ),
            "batch.capabilities.post-drain.status",
            id="completed-required-capability-failed",
        ),
    ),
)
def test_validate_state_rejects_invalid_batch_terminal_invariants(
    tmp_path: Path,
    mutation: Any,
    expected_path: str,
) -> None:
    state = _valid_state(tmp_path)
    mutation(state)

    _assert_schema_error(state, expected_path)


def _capability_attempt(
    status: str,
    *,
    started_at: str = T0,
    finished_at: str | None = T1,
    attempt_id: str = "attempt-1",
) -> dict[str, object]:
    return {
        "id": attempt_id,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "session_id": "session-1",
        "detail": None,
    }


def _capability(
    status: str,
    *,
    required: bool = True,
    attempts: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "required": required,
        "launcher": "codex",
        "plugin": "reviewer",
        "version": "1.0.0",
        "failure": "attention",
        "status": status,
        "attempts": [] if attempts is None else attempts,
    }


@pytest.mark.parametrize(
    "capability",
    (
        pytest.param(_capability("pending"), id="pending"),
        pytest.param(
            _capability(
                "running",
                attempts=[_capability_attempt("running", finished_at=None)],
            ),
            id="running",
        ),
        pytest.param(
            _capability("failed", attempts=[_capability_attempt("failed")]),
            id="failed",
        ),
        pytest.param(
            _capability("succeeded", attempts=[_capability_attempt("succeeded")]),
            id="succeeded",
        ),
        pytest.param(_capability("skipped", required=False), id="skipped"),
    ),
)
def test_validate_state_accepts_each_valid_capability_status_matrix_row(
    tmp_path: Path,
    capability: dict[str, object],
) -> None:
    state = _valid_state(tmp_path)
    state["batch"]["capabilities"] = {"post-drain": copy.deepcopy(capability)}  # type: ignore[typeddict-item]

    assert validate_state(state) == state


@pytest.mark.parametrize(
    ("capability", "expected_path"),
    (
        pytest.param(
            _capability(
                "pending",
                attempts=[_capability_attempt("running", finished_at=None)],
            ),
            "batch.capabilities.post-drain.attempts",
            id="pending-with-attempt",
        ),
        pytest.param(
            _capability("running"),
            "batch.capabilities.post-drain.attempts",
            id="running-without-attempt",
        ),
        pytest.param(
            _capability(
                "running", attempts=[_capability_attempt("running", finished_at=T1)]
            ),
            "batch.capabilities.post-drain.attempts[0].finished_at",
            id="running-finished",
        ),
        pytest.param(
            _capability(
                "failed", attempts=[_capability_attempt("failed", finished_at=None)]
            ),
            "batch.capabilities.post-drain.attempts[0].finished_at",
            id="failed-unfinished",
        ),
        pytest.param(
            _capability("failed", attempts=[_capability_attempt("succeeded")]),
            "batch.capabilities.post-drain.attempts[0].status",
            id="failed-latest-status-mismatch",
        ),
        pytest.param(
            _capability("succeeded", attempts=[_capability_attempt("failed")]),
            "batch.capabilities.post-drain.attempts[0].status",
            id="succeeded-latest-status-mismatch",
        ),
        pytest.param(
            _capability("skipped", required=True),
            "batch.capabilities.post-drain.required",
            id="required-skipped",
        ),
        pytest.param(
            _capability(
                "skipped",
                required=False,
                attempts=[_capability_attempt("succeeded")],
            ),
            "batch.capabilities.post-drain.attempts",
            id="skipped-with-attempt",
        ),
        pytest.param(
            _capability(
                "succeeded",
                attempts=[
                    _capability_attempt("running", finished_at=None),
                    _capability_attempt(
                        "succeeded",
                        started_at=T1,
                        finished_at=T2,
                        attempt_id="attempt-2",
                    ),
                ],
            ),
            "batch.capabilities.post-drain.attempts[0]",
            id="nonterminal-prior-attempt",
        ),
        pytest.param(
            _capability(
                "succeeded",
                attempts=[
                    _capability_attempt("failed", finished_at=T2),
                    _capability_attempt(
                        "succeeded",
                        started_at=T1,
                        finished_at=T3,
                        attempt_id="attempt-2",
                    ),
                ],
            ),
            "batch.capabilities.post-drain.attempts[1].started_at",
            id="attempts-out-of-order",
        ),
        pytest.param(
            _capability(
                "succeeded",
                attempts=[
                    _capability_attempt("succeeded", started_at=T2, finished_at=T1)
                ],
            ),
            "batch.capabilities.post-drain.attempts[0].finished_at",
            id="attempt-finishes-before-start",
        ),
    ),
)
def test_validate_state_rejects_invalid_capability_status_matrix_rows(
    tmp_path: Path,
    capability: dict[str, object],
    expected_path: str,
) -> None:
    state = _valid_state(tmp_path)
    state["batch"]["capabilities"] = {"post-drain": copy.deepcopy(capability)}  # type: ignore[typeddict-item]

    _assert_schema_error(state, expected_path)
