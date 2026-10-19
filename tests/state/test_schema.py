from __future__ import annotations

import calendar
import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import (
    Any,
)

import pytest

from ovcaq.state.schema import (
    ReviewCycle,
    SchemaError,
    State,
    TaskEntry,
    new_state,
    validate_state,
)


def _clean_batch_defaults() -> dict[str, object]:
    return {
        "id": "",
        "status": "idle",
        "started_at": None,
        "completed_at": None,
        "completed_prds": [],
        "parks_consecutive": 0,
        "catchup": {"completed_at": None, "head_sha": None},
        "capabilities": {},
    }


def _clean_work_defaults(repo_root: Path) -> dict[str, object]:
    return {
        "prd": None,
        "phase": "build",
        "next_phase": "build",
        "completed_phases": [],
        "work_start_sha": None,
        "repo_root": str(repo_root.resolve()),
        "design_doc": None,
        "contract_card": None,
        "tasks_total": 0,
        "tasks_completed": 0,
        "extensions": {},
    }


def _clean_review_defaults() -> dict[str, object]:
    return {
        "cycle": 0,
        "cap": 3,
        "cycles": [],
        "decisions": [],
        "doubts": [],
        "rubric_verdicts": [],
        "rework_task_ids": [],
        "lenses": {},
        "extensions": {},
    }


def test_new_state_returns_the_complete_clean_v1_defaults(tmp_path: Path) -> None:
    repo_root = tmp_path / "clean-state-defaults"
    repo_root.mkdir(parents=True)
    non_normalized_root = repo_root / ".." / repo_root.name
    assert new_state(repo_root=non_normalized_root) == {
        "schema_version": 1,
        "revision": 0,
        "batch": _clean_batch_defaults(),
        "work": _clean_work_defaults(repo_root),
        "tasks": [],
        "review": _clean_review_defaults(),
        "control": {
            "pause_requested": False,
            "pause_reason": None,
            "attention": None,
        },
        "recovery": {
            "operation": None,
            "replan_count": 0,
            "phase_fingerprint": None,
            "phase_repeats": 0,
        },
    }


@pytest.mark.parametrize(
    "relative_name",
    ("flock", "team/queue-control", "Repository With Spaces"),
)
def test_new_state_accepts_arbitrary_repository_path_names(
    tmp_path: Path, relative_name: str
) -> None:
    repo_root = tmp_path / relative_name
    repo_root.mkdir(parents=True)

    state = new_state(repo_root=repo_root / ".." / repo_root.name)

    assert state["work"]["repo_root"] == str(repo_root.resolve())


def test_new_state_accepts_a_runtime_generated_repository_name(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / f"repo-{uuid.uuid4().hex}"
    repo_root.mkdir()

    state = new_state(repo_root=repo_root)

    assert state["work"]["repo_root"] == str(repo_root.resolve())


def test_new_state_returns_fresh_independent_mutable_containers(
    tmp_path: Path,
) -> None:
    first = new_state(repo_root=tmp_path / "first")
    second = new_state(repo_root=tmp_path / "second")
    container_pairs = (
        (first, second),
        (first["batch"], second["batch"]),
        (first["batch"]["completed_prds"], second["batch"]["completed_prds"]),
        (first["batch"]["catchup"], second["batch"]["catchup"]),
        (first["batch"]["capabilities"], second["batch"]["capabilities"]),
        (first["work"], second["work"]),
        (first["work"]["completed_phases"], second["work"]["completed_phases"]),
        (first["work"]["extensions"], second["work"]["extensions"]),
        (first["tasks"], second["tasks"]),
        (first["review"], second["review"]),
        (first["review"]["cycles"], second["review"]["cycles"]),
        (first["review"]["decisions"], second["review"]["decisions"]),
        (first["review"]["doubts"], second["review"]["doubts"]),
        (
            first["review"]["rubric_verdicts"],
            second["review"]["rubric_verdicts"],
        ),
        (first["review"]["rework_task_ids"], second["review"]["rework_task_ids"]),
        (first["review"]["lenses"], second["review"]["lenses"]),
        (first["review"]["extensions"], second["review"]["extensions"]),
        (first["control"], second["control"]),
        (first["recovery"], second["recovery"]),
    )

    assert all(left is not right for left, right in container_pairs)


T0 = "2026-08-26T10:00:00Z"
T1 = "2026-08-26T10:01:00.123456Z"
T2 = "2026-08-26T10:02:00Z"
T3 = "2026-08-26T10:03:00Z"


def _populate_valid_batch(state: State) -> None:
    state["batch"].update(
        {
            "id": "batch-1",
            "status": "running",
            "started_at": T0,
            "completed_prds": [
                {
                    "filename": "00001-bootstrap.md",
                    "cycles": 1,
                    "autonomous_decisions": 2,
                    "escalated_decisions": 0,
                    "tasks_completed": 3,
                    "tasks_total": 3,
                }
            ],
            "catchup": {"completed_at": T0, "head_sha": "abc123"},
            "capabilities": {
                "post-drain": {
                    "required": True,
                    "launcher": "codex",
                    "plugin": "reviewer",
                    "version": "1.0.0",
                    "failure": "attention",
                    "status": "succeeded",
                    "attempts": [
                        {
                            "id": "cap-attempt-1",
                            "status": "failed",
                            "started_at": T0,
                            "finished_at": T1,
                            "session_id": "session-1",
                            "detail": "retry required",
                        },
                        {
                            "id": "cap-attempt-2",
                            "status": "succeeded",
                            "started_at": T1,
                            "finished_at": T2,
                            "session_id": "session-2",
                            "detail": None,
                        },
                    ],
                }
            },
        }
    )


def _populate_valid_work(state: State) -> None:
    state["work"].update(
        {
            "prd": "00002-state-kernel.md",
            "work_start_sha": "def456",
            "design_doc": "docs/dev/project-management/designs/00003-state-kernel-v1-design.md",
            "contract_card": "Validate every owned object.",
            "tasks_total": 2,
            "tasks_completed": 1,
            "extensions": {"review/score": {"value": 1.0, "passed": True}},
        }
    )


def _valid_completed_task() -> TaskEntry:
    return {
        "id": 1,
        "name": "Validate state",
        "description": "Validate a complete state tree.",
        "active_form": "Validating state",
        "status": "completed",
        "blocked_by": [],
        "tier": "full",
        "files_touched": 2,
        "public_contract_edit": True,
        "estimates": {"input_tokens": 2000, "context_peak": 4000},
        "attempts": [
            {
                "number": 1,
                "tier": "full",
                "driver": "generic",
                "outcome": "completed",
                "review_cycle": 1,
                "cause": None,
                "pipeline": "full",
                "cleanup_outcome": "clean",
                "started_at": T0,
                "finished_at": T1,
                "commit_sha": "fedcba",
                "escalation": {
                    "reason": "rescue",
                    "from_tier": "lean",
                    "diagnosis": "solid_spec",
                    "repair_used": True,
                },
                "metadata": {"nested": [1, {"ok": True}]},
            }
        ],
        "metadata": {"owner": "tess", "notes": None},
    }


def _valid_pending_task() -> TaskEntry:
    return {
        "id": 2,
        "name": "Persist state",
        "description": "Persist only validated state.",
        "active_form": "Persisting state",
        "status": "pending",
        "blocked_by": [1],
        "tier": None,
        "files_touched": None,
        "public_contract_edit": None,
        "estimates": {"input_tokens": None, "context_peak": None},
        "attempts": [],
        "metadata": {},
    }


def _populate_valid_tasks(state: State) -> None:
    state["tasks"] = [_valid_completed_task(), _valid_pending_task()]


def _valid_review_cycle() -> ReviewCycle:
    return {
        "cycle": 1,
        "review_file": "review-1.md",
        "reviewers": {"alice": "passed", "blake": "unavailable"},
        "issues_found": 1,
        "follow_up_tasks": 1,
        "deferred": 0,
        "recurring_issues": ["schema drift"],
        "decision_gate": {
            "decision": "continue",
            "detail": "The finding is actionable.",
            "decided_at": T2,
        },
        "rework_commits": ["123abc"],
        "rework_notes": ["Tightened validation."],
        "fix_audit": ["R1 passed"],
        "test_run": {
            "command": ["pytest", "tests/state/test_schema.py"],
            "exit_code": 0,
            "summary": "All focused tests passed.",
        },
    }


def _populate_valid_review(state: State) -> None:
    state["review"].update(
        {
            "cycle": 1,
            "cycles": [_valid_review_cycle()],
            "decisions": [
                {
                    "id": "decision-1",
                    "kind": "implementation",
                    "summary": "Keep state provider-neutral.",
                    "rationale": "Provider details belong at the edge.",
                    "cycle": 1,
                    "created_at": T2,
                    "status": "applied",
                }
            ],
            "doubts": [
                {
                    "id": "doubt-1",
                    "description": "Could a nested owner remain open?",
                    "category": "verify",
                    "justification": "Every owner is closed by contract.",
                    "status": "resolved",
                    "source": "review",
                }
            ],
            "rubric_verdicts": [
                {"rule_id": "R1", "verdict": "pass", "source": "review"}
            ],
            "rework_task_ids": [2],
            "lenses": {"alice": "completed", "blake": "failed"},
            "extensions": {"review/metadata": ["bounded", "finite"]},
        }
    )


def _populate_valid_recovery(state: State) -> None:
    state["control"]["attention"] = {
        "site": "review",
        "detail": "Operator attention is recorded.",
        "created_at": T2,
    }
    state["recovery"].update(
        {
            "operation": {
                "id": "recovery-1",
                "kind": "stall",
                "step": "recorded",
                "prd": "00002-state-kernel.md",
                "site": "review",
                "detail": "A prior stall was recorded.",
                "source": "backlog/00002.md",
                "destination": "blocked/00002.md",
                "artifact": None,
                "created_at": T1,
            },
            "replan_count": 1,
            "phase_fingerprint": "fingerprint-1",
            "phase_repeats": 1,
        }
    )


def _valid_state(repo_root: Path) -> State:
    state = new_state(repo_root=repo_root)
    _populate_valid_batch(state)
    _populate_valid_work(state)
    _populate_valid_tasks(state)
    _populate_valid_review(state)
    _populate_valid_recovery(state)
    return state


def _at_path(value: Any, path: tuple[str | int, ...]) -> Any:
    current = value
    for part in path:
        current = current[part]
    return current


def _set_path(value: Any, path: tuple[str | int, ...], replacement: object) -> None:
    _at_path(value, path[:-1])[path[-1]] = replacement


def _dotted_path(path: tuple[str | int, ...]) -> str:
    result = ""
    for part in path:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}" if result else part
    return result


def _assert_schema_error(value: object, expected_path: str) -> SchemaError:
    with pytest.raises(SchemaError) as raised:
        validate_state(value)
    assert expected_path in str(raised.value)
    return raised.value


_NEUTRAL_STATE_VALIDATOR = """
import json
import sys

from ovcaq.state.schema import validate_state

document = json.loads(sys.stdin.read())
try:
    validate_state(document)
except Exception as error:
    payload = {
        "exception": f"{type(error).__module__}.{type(error).__qualname__}",
        "message": str(error),
    }
else:
    payload = {"exception": None, "message": None}
sys.stdout.write(json.dumps(payload))
"""


def _validate_in_neutral_process(value: object) -> dict[str, str | None]:
    environment = os.environ.copy()
    environment.pop("PYTEST_CURRENT_TEST", None)
    source_path = str(Path(__file__).parents[2] / "src")
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_path
        if existing_pythonpath is None
        else os.pathsep.join((source_path, existing_pythonpath))
    )
    completed = subprocess.run(
        [sys.executable, "-c", _NEUTRAL_STATE_VALIDATOR],
        input=json.dumps(value),
        text=True,
        capture_output=True,
        check=True,
        cwd=Path(__file__).parents[2],
        env=environment,
    )
    result = json.loads(completed.stdout)
    assert isinstance(result, dict)
    return result


def _neutral_invalid_state(tmp_path: Path, case: str) -> State:
    state = _valid_state(tmp_path)
    if case == "unknown-owned-field":
        state["review"]["cycles"][0]["unexpected"] = True  # type: ignore[typeddict-unknown-key]
    elif case == "missing-owned-field":
        del state["recovery"]["operation"]["destination"]
    elif case == "integer-is-boolean":
        state["revision"] = True
    elif case == "duplicate-task-id":
        state["tasks"][1]["id"] = state["tasks"][0]["id"]
    elif case == "inconsistent-task-count":
        state["work"]["tasks_total"] = len(state["tasks"]) + 1
    elif case == "malformed-nested-timestamp":
        state["tasks"][0]["attempts"][0]["finished_at"] = T0[:-1]
    elif case == "invalid-extension-key":
        state["work"]["extensions"]["Invalid Key"] = None
    else:
        raise AssertionError(f"unknown neutral validation case: {case}")
    return state


def _runtime_valid_timestamps() -> tuple[str, ...]:
    seed = datetime.now(UTC)
    base = seed.strftime("%Y-%m-%dT%H:%M:%S")
    fraction = f"{seed.microsecond:06d}"
    fractional_widths = tuple(
        f"{base}{f'.{fraction[:width]}' if width else ''}Z" for width in range(7)
    )
    another_date = (seed + timedelta(days=37)).strftime("%Y-%m-%dT%H:%M:%SZ")
    leap_year = next(
        year for year in range(seed.year, seed.year + 9) if calendar.isleap(year)
    )
    leap_day = datetime(leap_year, 2, 29, 23, 59, 59, tzinfo=UTC).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return (*fractional_widths, another_date, leap_day)


def _runtime_invalid_timestamps() -> tuple[object, ...]:
    seed = datetime.now(UTC)
    base = seed.strftime("%Y-%m-%dT%H:%M:%S")
    valid_plain = f"{base}Z"
    fraction = f"{seed.microsecond:06d}"
    leap_year = next(
        year for year in range(seed.year, seed.year + 9) if calendar.isleap(year)
    )
    non_leap_year = next(
        year for year in range(seed.year, seed.year + 5) if not calendar.isleap(year)
    )
    return (
        None,
        0,
        "",
        valid_plain[:-1],
        f"{valid_plain[:-1]}+00:00",
        f"{valid_plain[:-1]}z",
        valid_plain.replace("T", " ", 1),
        f"{base}.{fraction}0Z",
        f"{leap_year:04d}-02-30T12:00:00Z",
        f"{non_leap_year:04d}-02-29T12:00:00Z",
        f"{seed.year:04d}-{seed.month:02d}-{seed.day:02d}T24:00:00Z",
    )


OWNED_OBJECT_CASES = (
    pytest.param((), "revision", id="state"),
    pytest.param(("batch",), "id", id="batch"),
    pytest.param(("batch", "catchup"), "head_sha", id="catchup-cache"),
    pytest.param(("batch", "completed_prds", 0), "filename", id="completed-prd"),
    pytest.param(("batch", "capabilities", "post-drain"), "failure", id="capability"),
    pytest.param(
        ("batch", "capabilities", "post-drain", "attempts", 1),
        "detail",
        id="capability-attempt",
    ),
    pytest.param(("work",), "repo_root", id="work"),
    pytest.param(("tasks", 0), "active_form", id="task"),
    pytest.param(("tasks", 0, "estimates"), "context_peak", id="estimates"),
    pytest.param(("tasks", 0, "attempts", 0), "cleanup_outcome", id="attempt"),
    pytest.param(
        ("tasks", 0, "attempts", 0, "escalation"),
        "diagnosis",
        id="escalation",
    ),
    pytest.param(("review",), "cap", id="review"),
    pytest.param(("review", "cycles", 0), "recurring_issues", id="review-cycle"),
    pytest.param(
        ("review", "cycles", 0, "decision_gate"),
        "detail",
        id="decision-gate",
    ),
    pytest.param(("review", "cycles", 0, "test_run"), "summary", id="test-run"),
    pytest.param(("review", "decisions", 0), "kind", id="decision"),
    pytest.param(("review", "doubts", 0), "justification", id="doubt"),
    pytest.param(("review", "rubric_verdicts", 0), "source", id="rubric-verdict"),
    pytest.param(("control",), "attention", id="control"),
    pytest.param(("control", "attention"), "detail", id="notice"),
    pytest.param(("recovery",), "phase_fingerprint", id="recovery"),
    pytest.param(("recovery", "operation"), "destination", id="recovery-operation"),
)
