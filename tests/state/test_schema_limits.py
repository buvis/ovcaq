from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import (
    Any,
    get_type_hints,
)

import pytest
from test_schema import (
    T0,
    _assert_schema_error,
    _dotted_path,
    _set_path,
    _valid_state,
)

from ovcaq.state.schema import (
    MAX_ATTEMPTS_PER_TASK,
    MAX_CAPABILITIES,
    MAX_CONTRACT_CARD_BYTES,
    MAX_JSON_DEPTH,
    MAX_JSON_INTEGER_DIGITS,
    MAX_OPEN_MAP_ITEMS,
    MAX_REVIEW_CYCLES,
    MAX_REVIEW_ITEMS,
    MAX_STATE_BYTES,
    MAX_STRING_BYTES,
    MAX_TASKS,
    AttemptEntry,
    ResourceLimitError,
    SchemaError,
    State,
    TaskEntry,
    decode_json,
    new_state,
    validate_state,
)


@pytest.mark.parametrize("sign", ("", "-"))
def test_decode_json_accepts_an_integer_at_the_digit_limit(sign: str) -> None:
    literal = sign + "9" * MAX_JSON_INTEGER_DIGITS

    assert decode_json(literal, source="boundary integer") == int(literal)


@pytest.mark.parametrize("constant", ("NaN", "Infinity", "-Infinity"))
def test_decode_json_rejects_nonstandard_numeric_constants(constant: str) -> None:
    with pytest.raises(ValueError, match="non-standard JSON constant"):
        decode_json(constant, source="non-standard number")


@pytest.mark.parametrize(
    ("mutation", "expected_path"),
    (
        pytest.param(
            lambda state, value: state.__setitem__("revision", value),
            "revision",
            id="typed-revision",
        ),
        pytest.param(
            lambda state, value: state["tasks"][0].__setitem__("id", value),
            "tasks[0].id",
            id="task-id",
        ),
        pytest.param(
            lambda state, value: state["tasks"][1].__setitem__("blocked_by", [value]),
            "tasks[1].blocked_by[0]",
            id="blocker-id",
        ),
        pytest.param(
            lambda state, value: state["work"]["extensions"].__setitem__(
                "tests/integer", value
            ),
            "work.extensions.tests/integer",
            id="open-json",
        ),
    ),
)
def test_validate_state_rejects_programmatic_integers_beyond_decoder_limit(
    tmp_path: Path,
    mutation: Any,
    expected_path: str,
) -> None:
    state = _valid_state(tmp_path)
    mutation(state, 10**MAX_JSON_INTEGER_DIGITS)

    with pytest.raises(ResourceLimitError, match=re.escape(expected_path)):
        validate_state(state)


def test_every_accepted_boundary_integer_round_trips_through_decoder(
    tmp_path: Path,
) -> None:
    maximum = 10**MAX_JSON_INTEGER_DIGITS - 1
    state = new_state(repo_root=tmp_path)
    state["revision"] = maximum
    state["work"]["extensions"] = {
        "tests/positive-integer": maximum,
        "tests/negative-integer": -maximum,
    }

    validated = validate_state(state)
    encoded = json.dumps(
        validated,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    assert decode_json(encoded, source="validated state") == validated


@pytest.mark.parametrize(
    ("mutation", "expected_path"),
    (
        pytest.param(
            lambda state: state["tasks"][1].__setitem__("id", 1),
            "tasks[1].id",
            id="duplicate-task-id",
        ),
        pytest.param(
            lambda state: state["tasks"][1].__setitem__("blocked_by", [999]),
            "tasks[1].blocked_by[0]",
            id="missing-blocker",
        ),
        pytest.param(
            lambda state: state["tasks"][1].__setitem__("blocked_by", [1, 1]),
            "tasks[1].blocked_by[1]",
            id="duplicate-blocker",
        ),
        pytest.param(
            lambda state: state["tasks"][0].__setitem__("blocked_by", [1]),
            "tasks[0].blocked_by[0]",
            id="self-blocker",
        ),
        pytest.param(
            lambda state: state["tasks"][0]["attempts"][0].__setitem__("number", 2),
            "tasks[0].attempts[0].number",
            id="attempt-number-gap",
        ),
        pytest.param(
            lambda state: state["tasks"][0]["attempts"].append(
                {
                    **copy.deepcopy(state["tasks"][0]["attempts"][0]),
                    "number": 3,
                }
            ),
            "tasks[0].attempts[1].number",
            id="attempt-number-noncontiguous",
        ),
        pytest.param(
            lambda state: state["work"].__setitem__("tasks_total", 3),
            "work.tasks_total",
            id="task-total-mismatch",
        ),
        pytest.param(
            lambda state: state["work"].__setitem__("tasks_completed", 0),
            "work.tasks_completed",
            id="task-completed-mismatch",
        ),
        pytest.param(
            lambda state: state["review"].__setitem__("rework_task_ids", [999]),
            "review.rework_task_ids[0]",
            id="unknown-rework-task",
        ),
        pytest.param(
            lambda state: state["review"]["cycles"].append(
                copy.deepcopy(state["review"]["cycles"][0])
            ),
            "review.cycles[1].cycle",
            id="duplicate-review-cycle",
        ),
        pytest.param(
            lambda state: state["review"]["decisions"].append(
                copy.deepcopy(state["review"]["decisions"][0])
            ),
            "review.decisions[1].id",
            id="duplicate-decision-id",
        ),
        pytest.param(
            lambda state: state["review"]["doubts"].append(
                copy.deepcopy(state["review"]["doubts"][0])
            ),
            "review.doubts[1].id",
            id="duplicate-doubt-id",
        ),
        pytest.param(
            lambda state: state["batch"]["capabilities"]["post-drain"]["attempts"][
                1
            ].__setitem__("id", "cap-attempt-1"),
            "batch.capabilities.post-drain.attempts[1].id",
            id="duplicate-capability-attempt-id",
        ),
        pytest.param(
            lambda state: state["batch"]["completed_prds"][0].__setitem__(
                "tasks_completed", 4
            ),
            "batch.completed_prds[0].tasks_completed",
            id="completed-prd-counts",
        ),
        pytest.param(
            lambda state: state["tasks"][0]["attempts"][0].__setitem__(
                "finished_at", "2026-08-26T09:59:59Z"
            ),
            "tasks[0].attempts[0].finished_at",
            id="attempt-finishes-before-start",
        ),
    ),
)
def test_validate_state_rejects_cross_field_invariant_violations(
    tmp_path: Path,
    mutation: Any,
    expected_path: str,
) -> None:
    state = _valid_state(tmp_path)
    mutation(state)

    _assert_schema_error(state, expected_path)


@pytest.mark.parametrize(
    "extension_key",
    (
        "Plugin/name",
        "plugin",
        "/name",
        "plugin/",
        "-plugin/name",
        "plugin/-name",
        "plugin/name with spaces",
        "plugin/name/extra",
    ),
)
@pytest.mark.parametrize(
    "map_path",
    (("work", "extensions"), ("review", "extensions")),
    ids=("work", "review"),
)
def test_validate_state_rejects_invalid_extension_keys(
    tmp_path: Path,
    extension_key: str,
    map_path: tuple[str, str],
) -> None:
    state = _valid_state(tmp_path)
    _set_path(state, map_path, {extension_key: True})

    _assert_schema_error(state, _dotted_path(map_path))


@pytest.mark.parametrize(
    "invalid_json",
    (
        pytest.param({1: "non-string key"}, id="non-string-key"),
        pytest.param(("tuple",), id="tuple"),
        pytest.param(float("nan"), id="nan"),
        pytest.param(float("inf"), id="positive-infinity"),
        pytest.param(float("-inf"), id="negative-infinity"),
    ),
)
def test_validate_state_rejects_non_json_metadata_values(
    tmp_path: Path,
    invalid_json: object,
) -> None:
    state = _valid_state(tmp_path)
    state["tasks"][0]["metadata"] = {"invalid": invalid_json}  # type: ignore[dict-item]

    _assert_schema_error(state, "tasks[0].metadata.invalid")


def test_validate_state_reports_the_first_full_path_to_an_unserializable_value(
    tmp_path: Path,
) -> None:
    state = _valid_state(tmp_path)
    state["tasks"][0]["metadata"] = {
        "first": {"invalid": object()},
        "later": object(),
    }

    _assert_schema_error(state, "tasks[0].metadata.first.invalid")


def test_validate_state_rejects_json_beyond_the_maximum_depth(
    tmp_path: Path,
) -> None:
    state = _valid_state(tmp_path)
    nested: object = None
    for _ in range(MAX_JSON_DEPTH + 2):
        nested = [nested]
    state["tasks"][0]["metadata"] = {"nested": nested}  # type: ignore[dict-item]

    _assert_schema_error(state, "tasks[0].metadata.nested")


def test_validate_state_rejects_open_maps_beyond_the_item_limit(
    tmp_path: Path,
) -> None:
    state = _valid_state(tmp_path)
    state["tasks"][0]["metadata"] = {
        f"key-{index}": index for index in range(MAX_OPEN_MAP_ITEMS + 1)
    }

    _assert_schema_error(state, "tasks[0].metadata")


@pytest.mark.parametrize(
    ("path", "oversized_value"),
    (
        pytest.param(
            ("tasks", 0, "description"),
            "é" * (MAX_STRING_BYTES // 2 + 1),
            id="utf8-string-bytes",
        ),
        pytest.param(
            ("work", "contract_card"),
            "é" * (MAX_CONTRACT_CARD_BYTES // 2 + 1),
            id="contract-card-bytes",
        ),
    ),
)
def test_validate_state_rejects_strings_over_their_utf8_byte_limits(
    tmp_path: Path,
    path: tuple[str | int, ...],
    oversized_value: str,
) -> None:
    state = _valid_state(tmp_path)
    _set_path(state, path, oversized_value)

    error = _assert_schema_error(state, _dotted_path(path))
    assert oversized_value not in str(error)
    assert len(str(error)) < len(oversized_value)


def _overfill_tasks(state: State) -> None:
    template = copy.deepcopy(state["tasks"][1])
    state["tasks"] = []
    for task_id in range(1, MAX_TASKS + 2):
        task = copy.deepcopy(template)
        task["id"] = task_id
        task["blocked_by"] = []
        state["tasks"].append(task)
    state["work"]["tasks_total"] = len(state["tasks"])
    state["work"]["tasks_completed"] = 0
    state["review"]["rework_task_ids"] = []


def _overfill_attempts(state: State) -> None:
    template = copy.deepcopy(state["tasks"][0]["attempts"][0])
    state["tasks"][0]["attempts"] = []
    for number in range(1, MAX_ATTEMPTS_PER_TASK + 2):
        attempt = copy.deepcopy(template)
        attempt["number"] = number
        state["tasks"][0]["attempts"].append(attempt)


def _overfill_review_cycles(state: State) -> None:
    template = copy.deepcopy(state["review"]["cycles"][0])
    state["review"]["cycles"] = []
    for cycle_number in range(1, MAX_REVIEW_CYCLES + 2):
        cycle = copy.deepcopy(template)
        cycle["cycle"] = cycle_number
        state["review"]["cycles"].append(cycle)
    state["review"]["cycle"] = MAX_REVIEW_CYCLES + 1


def _overfill_review_items(state: State) -> None:
    template = copy.deepcopy(state["review"]["decisions"][0])
    state["review"]["decisions"] = []
    for index in range(MAX_REVIEW_ITEMS + 1):
        decision = copy.deepcopy(template)
        decision["id"] = f"decision-{index}"
        state["review"]["decisions"].append(decision)


def _overfill_capabilities(state: State) -> None:
    state["batch"]["capabilities"] = {
        f"capability-{index}": {
            "required": False,
            "launcher": "codex",
            "plugin": "reviewer",
            "version": "1.0.0",
            "failure": "attention",
            "status": "skipped",
            "attempts": [],
        }
        for index in range(MAX_CAPABILITIES + 1)
    }


def _overfill_command_payload(state: State) -> None:
    state["review"]["cycles"][0]["test_run"]["command"] = [  # type: ignore[index]
        "x" * MAX_STRING_BYTES,
        "y" * MAX_STRING_BYTES,
        "z" * MAX_STRING_BYTES,
    ]


@pytest.mark.parametrize(
    ("mutation", "expected_path"),
    (
        pytest.param(_overfill_tasks, "tasks", id="tasks"),
        pytest.param(_overfill_attempts, "tasks[0].attempts", id="attempts"),
        pytest.param(_overfill_review_cycles, "review.cycles", id="review-cycles"),
        pytest.param(_overfill_review_items, "review.decisions", id="review-items"),
        pytest.param(_overfill_capabilities, "batch.capabilities", id="capabilities"),
        pytest.param(
            _overfill_command_payload,
            "review.cycles[0].test_run.command",
            id="command-payload",
        ),
    ),
)
def test_validate_state_rejects_owned_collections_over_their_limits(
    tmp_path: Path,
    mutation: Any,
    expected_path: str,
) -> None:
    state = _valid_state(tmp_path)
    mutation(state)

    _assert_schema_error(state, expected_path)


def test_validate_state_rejects_documents_over_the_canonical_byte_limit(
    tmp_path: Path,
) -> None:
    state = _valid_state(tmp_path)
    state["work"]["extensions"] = {
        f"plugin/value-{index}": "x" * (64 * 1024)
        for index in range(MAX_OPEN_MAP_ITEMS)
    }

    with pytest.raises(SchemaError):
        validate_state(state)


@pytest.mark.parametrize(
    "path",
    (
        pytest.param(("batch", "started_at"), id="batch"),
        pytest.param(("batch", "catchup", "completed_at"), id="catchup"),
        pytest.param(("tasks", 0, "attempts", 0, "finished_at"), id="attempt"),
        pytest.param(
            ("review", "cycles", 0, "decision_gate", "decided_at"),
            id="decision-gate",
        ),
        pytest.param(("review", "decisions", 0, "created_at"), id="decision"),
        pytest.param(("control", "attention", "created_at"), id="notice"),
        pytest.param(("recovery", "operation", "created_at"), id="recovery"),
        pytest.param(
            (
                "batch",
                "capabilities",
                "post-drain",
                "attempts",
                1,
                "finished_at",
            ),
            id="capability-attempt",
        ),
    ),
)
def test_validate_state_rejects_invalid_timestamps_at_nested_paths(
    tmp_path: Path,
    path: tuple[str | int, ...],
) -> None:
    state = _valid_state(tmp_path)
    _set_path(state, path, "2026-08-26T10:00:00+00:00")

    _assert_schema_error(state, _dotted_path(path))


def _fill_tasks_at_limit(state: State) -> None:
    _overfill_tasks(state)
    state["tasks"].pop()
    state["work"]["tasks_total"] = len(state["tasks"])


def _fill_attempts_at_limit(state: State) -> None:
    _overfill_attempts(state)
    state["tasks"][0]["attempts"].pop()


def _fill_review_cycles_at_limit(state: State) -> None:
    _overfill_review_cycles(state)
    state["review"]["cycles"].pop()
    state["review"]["cycle"] = MAX_REVIEW_CYCLES


def _fill_review_items_at_limit(state: State) -> None:
    _overfill_review_items(state)
    state["review"]["decisions"].pop()
    state["review"]["doubts"] = []
    state["review"]["rubric_verdicts"] = []
    state["review"]["rework_task_ids"] = []


def _fill_capabilities_at_limit(state: State) -> None:
    _overfill_capabilities(state)
    state["batch"]["capabilities"].popitem()


def _fill_open_map_at_limit(state: State) -> None:
    state["tasks"][0]["metadata"] = {
        f"key-{index}": index for index in range(MAX_OPEN_MAP_ITEMS)
    }


def _fill_maximum_task_attempt_shape(state: State) -> None:
    task_template = copy.deepcopy(state["tasks"][0])
    attempt_template = copy.deepcopy(task_template["attempts"][0])
    attempt_template.update(
        {
            "review_cycle": None,
            "cause": None,
            "pipeline": None,
            "cleanup_outcome": None,
            "started_at": T0,
            "finished_at": T0,
            "commit_sha": None,
            "escalation": None,
            "metadata": {},
        }
    )
    attempts = []
    for number in range(1, MAX_ATTEMPTS_PER_TASK + 1):
        attempt = copy.copy(attempt_template)
        attempt["number"] = number
        attempt["metadata"] = {}
        attempts.append(attempt)

    tasks = []
    for task_id in range(1, MAX_TASKS + 1):
        task = copy.deepcopy(task_template)
        task["id"] = task_id
        task["status"] = "completed"
        task["blocked_by"] = []
        task["attempts"] = copy.deepcopy(attempts)
        task["metadata"] = {}
        tasks.append(task)

    state["tasks"] = tasks
    state["work"]["tasks_total"] = MAX_TASKS
    state["work"]["tasks_completed"] = MAX_TASKS
    state["review"]["rework_task_ids"] = []


def test_validate_state_resolves_task_and_attempt_type_metadata_at_most_once_at_maximum_shape(
    tmp_path: Path,
) -> None:
    state = _valid_state(tmp_path)
    _fill_maximum_task_attempt_shape(state)
    canonical_bytes = (
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    assert len(canonical_bytes) <= MAX_STATE_BYTES
    resolutions = {TaskEntry: 0, AttemptEntry: 0}

    def count_type_hint_resolutions(frame: Any, event: str, _arg: object) -> None:
        if event != "call" or frame.f_code is not get_type_hints.__code__:
            return
        owner = frame.f_locals.get("obj")
        if owner in resolutions:
            resolutions[owner] += 1

    previous_profile = sys.getprofile()
    sys.setprofile(count_type_hint_resolutions)
    try:
        assert validate_state(state) == state
    finally:
        sys.setprofile(previous_profile)

    assert all(count <= 1 for count in resolutions.values()), resolutions


@pytest.mark.parametrize(
    "mutation",
    (
        pytest.param(_fill_tasks_at_limit, id="tasks"),
        pytest.param(_fill_attempts_at_limit, id="attempts"),
        pytest.param(_fill_review_cycles_at_limit, id="review-cycles"),
        pytest.param(_fill_review_items_at_limit, id="review-items"),
        pytest.param(_fill_capabilities_at_limit, id="capabilities"),
        pytest.param(_fill_open_map_at_limit, id="open-map"),
    ),
)
def test_validate_state_accepts_owned_collections_at_their_exact_limits(
    tmp_path: Path,
    mutation: Any,
) -> None:
    state = _valid_state(tmp_path)
    mutation(state)

    assert validate_state(state) == state


@pytest.mark.parametrize(
    ("path", "boundary_value"),
    (
        pytest.param(
            ("tasks", 0, "description"),
            "é" * (MAX_STRING_BYTES // 2),
            id="utf8-string",
        ),
        pytest.param(
            ("work", "contract_card"),
            "é" * (MAX_CONTRACT_CARD_BYTES // 2),
            id="contract-card",
        ),
    ),
)
def test_validate_state_accepts_strings_at_their_exact_utf8_byte_limits(
    tmp_path: Path,
    path: tuple[str | int, ...],
    boundary_value: str,
) -> None:
    state = _valid_state(tmp_path)
    _set_path(state, path, boundary_value)

    assert validate_state(state) == state
