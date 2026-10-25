from __future__ import annotations

import itertools
import json
import shutil
from collections.abc import Callable
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path
from typing import Any

import pytest

from ovcaq.workflow_client import (
    PROTOCOL_MAJOR,
    ApplyResult,
    ControllerConfig,
    ControllerContract,
    ControllerError,
    ControllerOutputError,
    ControllerTimeoutError,
    IncompatibleContractError,
    MutationEnvelope,
    RejectedRequestError,
    RevisionConflictError,
    controller_bundle_digest,
)

BUNDLE = Path(__file__).parents[1] / "fixtures" / "workflow" / "controller-v1.json"
BUNDLE_FIELDS = {
    "protocol_major",
    "package_version",
    "schema_digest",
    "fixture_digest",
    "operations",
    "capabilities",
}
# The contract does not name the exception type raised by __post_init__
# validation, so accept any of the plausible validation failures.
INVALID = (ValueError, TypeError, OSError, ControllerError)
ERROR_SUBCLASSES = (
    IncompatibleContractError,
    ControllerTimeoutError,
    ControllerOutputError,
    RevisionConflictError,
    RejectedRequestError,
)
NULLABLE_IDENTITY = ("workflow_id", "actor_id", "lease_epoch")


def make_config(tmp_path: Path, **overrides: Any) -> ControllerConfig:
    fields: dict[str, Any] = {
        "argv": ("autopilot-controller", "serve"),
        "contract_bundle": BUNDLE,
        "actor_file": None,
        "project_root": tmp_path,
    }
    fields.update(overrides)
    return ControllerConfig(**fields)


def make_envelope(**overrides: Any) -> MutationEnvelope:
    fields: dict[str, Any] = {
        "protocol_major": PROTOCOL_MAJOR,
        "operation": "workflow.apply",
        "request_id": "req-0001",
        "expected_revision": 3,
        "project_id": "project-a",
        "workflow_id": "workflow-a",
        "actor_id": "actor-a",
        "lease_epoch": 2,
        "payload": {"event": "task.done"},
    }
    fields.update(overrides)
    return MutationEnvelope(**fields)


def load_bundle() -> dict[str, Any]:
    data = json.loads(BUNDLE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def make_contract() -> ControllerContract:
    data = load_bundle()
    return ControllerContract(
        protocol_major=data["protocol_major"],
        package_version=data["package_version"],
        schema_digest=data["schema_digest"],
        fixture_digest=data["fixture_digest"],
        operations=frozenset(data["operations"]),
        capabilities=frozenset(data["capabilities"]),
    )


def write_bundle(path: Path, data: dict[str, Any], **dump_args: Any) -> Path:
    path.write_text(json.dumps(data, **dump_args), encoding="utf-8")
    return path


# Protocol and error hierarchy


def test_protocol_major_is_one() -> None:
    assert PROTOCOL_MAJOR == 1


def test_controller_error_is_runtime_error() -> None:
    assert issubclass(ControllerError, RuntimeError)


@pytest.mark.parametrize("error_class", ERROR_SUBCLASSES, ids=lambda c: c.__name__)
def test_every_controller_failure_is_a_controller_error(
    error_class: type[ControllerError],
) -> None:
    assert issubclass(error_class, ControllerError)
    assert error_class is not ControllerError


@pytest.mark.parametrize(
    ("left", "right"),
    list(itertools.permutations(ERROR_SUBCLASSES, 2)),
    ids=lambda c: c.__name__,
)
def test_controller_failure_classes_are_distinct(
    left: type[ControllerError], right: type[ControllerError]
) -> None:
    assert left is not right
    assert not issubclass(left, right)


def test_rejected_request_exposes_code_retryable_and_detail() -> None:
    error = RejectedRequestError("lease_expired", True, "lease epoch 2 is stale")

    assert error.error_code == "lease_expired"
    assert error.retryable is True
    assert error.detail == "lease epoch 2 is stale"


def test_rejected_request_is_caught_as_controller_error() -> None:
    with pytest.raises(ControllerError) as caught:
        raise RejectedRequestError("invalid_transition", False, "phase mismatch")

    assert isinstance(caught.value, RejectedRequestError)
    assert caught.value.error_code == "invalid_transition"
    assert caught.value.retryable is False
    assert caught.value.detail == "phase mismatch"


# Frozen, slotted records


def build_config(tmp_path: Path) -> object:
    return make_config(tmp_path)


def build_contract(tmp_path: Path) -> object:
    return make_contract()


def build_apply_result(tmp_path: Path) -> object:
    return ApplyResult(
        ok=True, revision=1, result={"phase": "build"}, error_code=None, retryable=False
    )


def build_envelope(tmp_path: Path) -> object:
    return make_envelope()


@pytest.mark.parametrize(
    ("build", "field", "replacement"),
    [
        (build_config, "timeout_seconds", 60),
        (build_contract, "protocol_major", 2),
        (build_apply_result, "ok", False),
        (build_envelope, "workflow_id", None),
    ],
    ids=["config", "contract", "apply-result", "envelope"],
)
def test_public_records_are_frozen_slotted_dataclasses(
    tmp_path: Path,
    build: Callable[[Path], object],
    field: str,
    replacement: object,
) -> None:
    record = build(tmp_path)

    assert is_dataclass(record)
    assert not hasattr(record, "__dict__")
    with pytest.raises(FrozenInstanceError):
        setattr(record, field, replacement)


# ControllerConfig


def test_config_accepts_valid_fields_and_applies_defaults(tmp_path: Path) -> None:
    config = make_config(tmp_path)

    assert config.argv == ("autopilot-controller", "serve")
    assert config.contract_bundle == BUNDLE
    assert config.actor_file is None
    assert config.project_root == tmp_path
    assert config.timeout_seconds == 30
    assert config.max_output_bytes == 1_048_576


def test_config_accepts_single_element_argv_and_actor_file(tmp_path: Path) -> None:
    actor = tmp_path / "actor.json"
    config = make_config(tmp_path, argv=("controller",), actor_file=actor)

    assert config.argv == ("controller",)
    assert config.actor_file == actor


@pytest.mark.parametrize(
    "argv",
    [
        (),
        ("",),
        ("controller", ""),
        ["controller", "serve"],
        ("controller", 1),
        (b"controller",),
        (Path("controller"),),
        "controller",
    ],
    ids=[
        "empty-tuple",
        "empty-string",
        "trailing-empty-string",
        "list-not-tuple",
        "int-element",
        "bytes-element",
        "path-element",
        "bare-string",
    ],
)
def test_config_rejects_invalid_argv(tmp_path: Path, argv: object) -> None:
    with pytest.raises(INVALID):
        make_config(tmp_path, argv=argv)


def test_config_rejects_missing_contract_bundle(tmp_path: Path) -> None:
    with pytest.raises(INVALID):
        make_config(tmp_path, contract_bundle=tmp_path / "absent.json")


def test_config_rejects_directory_contract_bundle(tmp_path: Path) -> None:
    directory = tmp_path / "bundle.json"
    directory.mkdir()

    with pytest.raises(INVALID):
        make_config(tmp_path, contract_bundle=directory)


def test_config_accepts_bundle_copied_elsewhere(tmp_path: Path) -> None:
    copy = tmp_path / "controller-v1.json"
    shutil.copyfile(BUNDLE, copy)

    assert make_config(tmp_path, contract_bundle=copy).contract_bundle == copy


@pytest.mark.parametrize("timeout", [1, 30, 299, 300])
def test_config_accepts_timeout_within_bounds(tmp_path: Path, timeout: int) -> None:
    assert make_config(tmp_path, timeout_seconds=timeout).timeout_seconds == timeout


@pytest.mark.parametrize("timeout", [0, -1, 301, 3600])
def test_config_rejects_timeout_outside_bounds(tmp_path: Path, timeout: int) -> None:
    with pytest.raises(INVALID):
        make_config(tmp_path, timeout_seconds=timeout)


@pytest.mark.parametrize("limit", [1, 4096, 1_048_576, 16_777_216])
def test_config_accepts_positive_output_limit(tmp_path: Path, limit: int) -> None:
    assert make_config(tmp_path, max_output_bytes=limit).max_output_bytes == limit


@pytest.mark.parametrize("limit", [0, -1, -1_048_576])
def test_config_rejects_non_positive_output_limit(tmp_path: Path, limit: int) -> None:
    with pytest.raises(INVALID):
        make_config(tmp_path, max_output_bytes=limit)


# Bundle fixture, ControllerContract and ApplyResult


def test_bundle_fixture_carries_exactly_the_contract_fields() -> None:
    data = load_bundle()

    assert set(data) == BUNDLE_FIELDS
    assert data["protocol_major"] == PROTOCOL_MAJOR
    assert isinstance(data["package_version"], str) and data["package_version"]
    assert isinstance(data["schema_digest"], str) and data["schema_digest"]
    assert isinstance(data["fixture_digest"], str) and data["fixture_digest"]
    assert all(isinstance(item, str) and item for item in data["operations"])
    assert all(isinstance(item, str) and item for item in data["capabilities"])
    assert len(set(data["operations"])) == len(data["operations"])
    assert len(set(data["capabilities"])) == len(data["capabilities"])
    assert "workflow.open" in data["operations"]


def test_contract_maps_bundle_fixture_fields() -> None:
    data = load_bundle()
    contract = make_contract()

    assert contract.protocol_major == PROTOCOL_MAJOR
    assert contract.package_version == data["package_version"]
    assert contract.schema_digest == data["schema_digest"]
    assert contract.fixture_digest == data["fixture_digest"]
    assert contract.operations == frozenset(data["operations"])
    assert contract.capabilities == frozenset(data["capabilities"])


def test_apply_result_holds_success_and_rejection_shapes() -> None:
    accepted = ApplyResult(
        ok=True,
        revision=4,
        result={"phase": "review"},
        error_code=None,
        retryable=False,
    )
    rejected = ApplyResult(
        ok=False, revision=None, result=None, error_code="stale", retryable=True
    )

    assert (accepted.ok, accepted.revision, accepted.error_code) == (True, 4, None)
    assert accepted.result == {"phase": "review"}
    assert accepted.retryable is False
    assert (rejected.ok, rejected.revision, rejected.result) == (False, None, None)
    assert (rejected.error_code, rejected.retryable) == ("stale", True)


# MutationEnvelope


def test_envelope_accepts_fully_identified_mutation() -> None:
    envelope = make_envelope()

    assert envelope.protocol_major == PROTOCOL_MAJOR
    assert envelope.operation == "workflow.apply"
    assert envelope.request_id == "req-0001"
    assert envelope.expected_revision == 3
    assert envelope.project_id == "project-a"
    assert envelope.workflow_id == "workflow-a"
    assert envelope.actor_id == "actor-a"
    assert envelope.lease_epoch == 2
    assert envelope.payload == {"event": "task.done"}


def test_envelope_allows_null_identity_for_initial_open() -> None:
    envelope = make_envelope(
        operation="workflow.open",
        expected_revision=0,
        workflow_id=None,
        actor_id=None,
        lease_epoch=None,
    )

    assert envelope.workflow_id is None
    assert envelope.actor_id is None
    assert envelope.lease_epoch is None


def test_envelope_accepts_initial_open_with_full_identity() -> None:
    envelope = make_envelope(operation="workflow.open", expected_revision=0)

    assert envelope.workflow_id == "workflow-a"
    assert envelope.actor_id == "actor-a"
    assert envelope.lease_epoch == 2


NON_INITIAL_OPEN = [
    ("workflow.apply", 0),
    ("workflow.apply", 7),
    ("workflow.read", 0),
    ("contract.describe", 0),
    ("workflow.open", 1),
    ("workflow.open", 12),
]
NULL_SUBSETS = [
    subset
    for size in range(1, len(NULLABLE_IDENTITY) + 1)
    for subset in itertools.combinations(NULLABLE_IDENTITY, size)
]


@pytest.mark.parametrize(("operation", "expected_revision"), NON_INITIAL_OPEN)
def test_envelope_accepts_full_identity_outside_initial_open(
    operation: str, expected_revision: int
) -> None:
    envelope = make_envelope(operation=operation, expected_revision=expected_revision)

    assert envelope.operation == operation
    assert envelope.expected_revision == expected_revision


@pytest.mark.parametrize(
    ("operation", "expected_revision", "nulls"),
    [
        (operation, revision, nulls)
        for (operation, revision) in NON_INITIAL_OPEN
        for nulls in NULL_SUBSETS
    ],
    ids=[
        f"{operation}-rev{revision}-null-{'+'.join(nulls)}"
        for (operation, revision) in NON_INITIAL_OPEN
        for nulls in NULL_SUBSETS
    ],
)
def test_envelope_rejects_null_identity_outside_initial_open(
    operation: str, expected_revision: int, nulls: tuple[str, ...]
) -> None:
    with pytest.raises(INVALID):
        make_envelope(
            operation=operation,
            expected_revision=expected_revision,
            **{field: None for field in nulls},
        )


# controller_bundle_digest


def test_bundle_digest_is_stable_for_the_fixture() -> None:
    first = controller_bundle_digest(BUNDLE)
    second = controller_bundle_digest(BUNDLE)

    assert isinstance(first, str)
    assert first
    assert first == second


def test_bundle_digest_matches_byte_copy_at_another_path(tmp_path: Path) -> None:
    copy = tmp_path / "elsewhere" / "bundle.json"
    copy.parent.mkdir()
    shutil.copyfile(BUNDLE, copy)

    assert controller_bundle_digest(copy) == controller_bundle_digest(BUNDLE)


def test_bundle_digest_ignores_key_order_and_whitespace(tmp_path: Path) -> None:
    data = load_bundle()
    reordered = dict(reversed(list(data.items())))
    compact = write_bundle(tmp_path / "compact.json", reordered, separators=(",", ":"))
    spaced = write_bundle(tmp_path / "spaced.json", reordered, indent=8)

    expected = controller_bundle_digest(BUNDLE)

    assert controller_bundle_digest(compact) == expected
    assert controller_bundle_digest(spaced) == expected


def test_bundle_digest_detects_single_byte_value_change(tmp_path: Path) -> None:
    text = BUNDLE.read_text(encoding="utf-8")
    version = load_bundle()["package_version"]
    mutated_version = version[:-1] + ("1" if version[-1] != "1" else "2")
    mutated = tmp_path / "mutated.json"
    mutated.write_text(
        text.replace(f'"{version}"', f'"{mutated_version}"', 1), encoding="utf-8"
    )

    assert len(mutated.read_bytes()) == len(BUNDLE.read_bytes())
    assert mutated.read_bytes() != BUNDLE.read_bytes()
    assert controller_bundle_digest(mutated) != controller_bundle_digest(BUNDLE)


@pytest.mark.parametrize(
    "field",
    ["protocol_major", "schema_digest", "fixture_digest", "operations", "capabilities"],
)
def test_bundle_digest_rejects_mismatched_artifact(tmp_path: Path, field: str) -> None:
    data = load_bundle()
    mutations: dict[str, object] = {
        "protocol_major": data["protocol_major"] + 1,
        "schema_digest": data["schema_digest"][::-1],
        "fixture_digest": "0" * len(data["fixture_digest"]),
        "operations": [*data["operations"], "workflow.extra"],
        "capabilities": data["capabilities"][:-1],
    }
    assert mutations[field] != data[field]
    mutated = write_bundle(tmp_path / "mutated.json", {**data, field: mutations[field]})

    assert controller_bundle_digest(mutated) != controller_bundle_digest(BUNDLE)
