from __future__ import annotations

import hashlib
import itertools
import json
import re
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


def canonical_sha256(path: Path) -> str:
    """Reference digest: sha256 of the sort_keys canonical JSON dump."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


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


def test_config_rejects_symlinked_contract_bundle(tmp_path: Path) -> None:
    target = tmp_path / "controller-v1.json"
    shutil.copyfile(BUNDLE, target)
    link = tmp_path / "linked.json"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="symlink"):
        make_config(tmp_path, contract_bundle=link)


def test_config_rejects_bundle_under_symlinked_directory(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    shutil.copyfile(BUNDLE, real / "controller-v1.json")
    (tmp_path / "alias").symlink_to(real, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink"):
        make_config(tmp_path, contract_bundle=tmp_path / "alias" / "controller-v1.json")


# Bundle content (malformed JSON, missing protocol_major) is deliberately not
# tested at ControllerConfig construction. This task's contract limits
# __post_init__ to "contract_bundle must exist and be a regular file"; parsing
# and checking the bundle belongs to the later contract()/transport task.
# Requiring it here would invent a requirement the task contract does not state.


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
    # Pin the fixture's actual values so the mapping is checked against known
    # content, not only read back from whatever the fixture happens to hold.
    assert contract.protocol_major == 1
    assert contract.package_version == "1.0.0"
    assert contract.operations == frozenset(
        {"contract.describe", "workflow.open", "workflow.read", "workflow.apply"}
    )
    assert contract.capabilities == frozenset(
        {"expected-revision", "idempotent-request-id", "lease-epoch"}
    )
    assert isinstance(contract.operations, frozenset)
    assert isinstance(contract.capabilities, frozenset)


def test_contract_fields_follow_declared_order_and_compare_by_value() -> None:
    data = load_bundle()
    positional = ControllerContract(
        data["protocol_major"],
        data["package_version"],
        data["schema_digest"],
        data["fixture_digest"],
        frozenset(data["operations"]),
        frozenset(data["capabilities"]),
    )

    assert positional == make_contract()
    assert hash(positional) == hash(make_contract())
    assert positional != ControllerContract(
        data["protocol_major"] + 1,
        data["package_version"],
        data["schema_digest"],
        data["fixture_digest"],
        frozenset(data["operations"]),
        frozenset(data["capabilities"]),
    )


def test_apply_result_fields_follow_declared_order() -> None:
    positional = ApplyResult(False, 9, {"phase": "done"}, "stale", True)

    assert positional.ok is False
    assert positional.revision == 9
    assert positional.result == {"phase": "done"}
    assert positional.error_code == "stale"
    assert positional.retryable is True
    assert positional == ApplyResult(
        ok=False,
        revision=9,
        result={"phase": "done"},
        error_code="stale",
        retryable=True,
    )


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


# Only the exact string "workflow.open" is exempt; unknown operations and
# near-miss spellings are not, even at expected_revision 0.
NOT_OPEN_OPERATIONS = [
    "workflow.bogus",
    "workflow.Open",
    "WORKFLOW.OPEN",
    "workflow.open ",
    " workflow.open",
    "workflow.opened",
    "workflow_open",
    "open",
    "",
]


@pytest.mark.parametrize(
    ("operation", "nulls"),
    [(operation, nulls) for operation in NOT_OPEN_OPERATIONS for nulls in NULL_SUBSETS],
    ids=[
        f"{operation!r}-null-{'+'.join(nulls)}"
        for operation in NOT_OPEN_OPERATIONS
        for nulls in NULL_SUBSETS
    ],
)
def test_envelope_rejects_null_identity_for_non_open_operation_at_revision_zero(
    operation: str, nulls: tuple[str, ...]
) -> None:
    with pytest.raises(INVALID):
        make_envelope(
            operation=operation,
            expected_revision=0,
            **{field: None for field in nulls},
        )


# The exemption needs expected_revision to be the int 0, not merely falsy or
# below one.
NOT_REVISION_ZERO = [-1, -100, False, 0.0, None]


@pytest.mark.parametrize(
    ("expected_revision", "nulls"),
    [(revision, nulls) for revision in NOT_REVISION_ZERO for nulls in NULL_SUBSETS],
    ids=[
        f"rev{revision!r}-null-{'+'.join(nulls)}"
        for revision in NOT_REVISION_ZERO
        for nulls in NULL_SUBSETS
    ],
)
def test_envelope_rejects_null_identity_for_open_without_int_zero_revision(
    expected_revision: object, nulls: tuple[str, ...]
) -> None:
    with pytest.raises(INVALID):
        make_envelope(
            operation="workflow.open",
            expected_revision=expected_revision,
            **{field: None for field in nulls},
        )


@pytest.mark.parametrize("protocol_major", [0, 2, -1, 99, "1", None])
def test_envelope_rejects_protocol_major_other_than_current(
    protocol_major: object,
) -> None:
    assert protocol_major != PROTOCOL_MAJOR
    with pytest.raises(INVALID):
        make_envelope(protocol_major=protocol_major)


@pytest.mark.parametrize("protocol_major", [0, 2, -1, 99, "1", None])
def test_envelope_rejects_protocol_major_other_than_current_on_initial_open(
    protocol_major: object,
) -> None:
    with pytest.raises(INVALID):
        make_envelope(
            protocol_major=protocol_major,
            operation="workflow.open",
            expected_revision=0,
            workflow_id=None,
            actor_id=None,
            lease_epoch=None,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [("request_id", ""), ("project_id", ""), ("project_id", None)],
    ids=["empty-request-id", "empty-project-id", "none-project-id"],
)
def test_envelope_rejects_missing_request_or_project_id(
    field: str, value: object
) -> None:
    with pytest.raises(INVALID):
        make_envelope(**{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [("request_id", ""), ("project_id", ""), ("project_id", None)],
    ids=["empty-request-id", "empty-project-id", "none-project-id"],
)
def test_envelope_rejects_missing_request_or_project_id_on_initial_open(
    field: str, value: object
) -> None:
    with pytest.raises(INVALID):
        make_envelope(
            operation="workflow.open",
            expected_revision=0,
            workflow_id=None,
            actor_id=None,
            lease_epoch=None,
            **{field: value},
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


# Pinned digest of controller-v1.json: sha256 hexdigest of
# json.dumps(json.loads(text), sort_keys=True).encode(). Update it only when the
# fixture changes on purpose.
FIXTURE_DIGEST = "b98f0a684c273ecda4448b41bb4f909b34cc834edb972b775616e579a91bc728"
NO_PROTOCOL_MAJOR_DIGEST = (
    "7aa99a16f7381c22142e03c5a8fa3d229f46badc78d0b1ddd6e95d2d2c785884"
)


def test_bundle_digest_is_sha256_of_sorted_key_canonical_json() -> None:
    digest = controller_bundle_digest(BUNDLE)

    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    assert digest == canonical_sha256(BUNDLE)
    assert digest == FIXTURE_DIGEST


def test_bundle_digest_follows_canonical_algorithm_for_mutated_copy(
    tmp_path: Path,
) -> None:
    data = load_bundle()
    mutated = write_bundle(
        tmp_path / "mutated.json", {**data, "package_version": "9.9.9"}, indent=3
    )
    digest = controller_bundle_digest(mutated)

    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    assert digest == canonical_sha256(mutated)
    assert digest != FIXTURE_DIGEST


# Digesting is a content hash, not schema validation: a bundle missing a field
# still digests, to a value distinct from the complete fixture. Rejecting the
# incomplete artifact is the consumer's job when it compares digests.
def test_bundle_digest_hashes_bundle_missing_protocol_major(tmp_path: Path) -> None:
    data = load_bundle()
    del data["protocol_major"]
    incomplete = write_bundle(tmp_path / "no-protocol-major.json", data)

    digest = controller_bundle_digest(incomplete)

    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    assert digest == canonical_sha256(incomplete)
    assert digest == NO_PROTOCOL_MAJOR_DIGEST
    assert digest != FIXTURE_DIGEST


def test_bundle_digest_accepts_matching_expected_digest() -> None:
    assert controller_bundle_digest(BUNDLE, FIXTURE_DIGEST) == FIXTURE_DIGEST
    assert controller_bundle_digest(BUNDLE, expected_digest=None) == FIXTURE_DIGEST


def test_bundle_digest_rejects_wrong_expected_digest() -> None:
    wrong = "0" * 64

    with pytest.raises(IncompatibleContractError) as caught:
        controller_bundle_digest(BUNDLE, expected_digest=wrong)

    assert wrong in str(caught.value)
    assert FIXTURE_DIGEST in str(caught.value)


def test_bundle_digest_rejects_mutated_artifact_against_pinned_digest(
    tmp_path: Path,
) -> None:
    data = load_bundle()
    mutated = write_bundle(
        tmp_path / "mutated.json", {**data, "protocol_major": PROTOCOL_MAJOR + 1}
    )

    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(mutated, expected_digest=FIXTURE_DIGEST)


def test_bundle_digest_rejects_duplicate_keys(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"protocol_major": 2, "protocol_major": 1}', encoding="utf-8")
    single = write_bundle(tmp_path / "single.json", {"protocol_major": 1})

    # Plain json.loads keeps the last value, so both files used to digest alike.
    assert canonical_sha256(duplicate) == canonical_sha256(single)
    with pytest.raises(IncompatibleContractError, match="duplicate"):
        controller_bundle_digest(duplicate)


def test_bundle_digest_rejects_nested_duplicate_keys(tmp_path: Path) -> None:
    nested = tmp_path / "nested.json"
    nested.write_text('{"outer": {"a": 1, "a": 2}}', encoding="utf-8")

    with pytest.raises(IncompatibleContractError, match="duplicate"):
        controller_bundle_digest(nested)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_bundle_digest_rejects_non_finite_numbers(
    tmp_path: Path, constant: str
) -> None:
    bundle = tmp_path / "constant.json"
    bundle.write_text(f'{{"protocol_major": {constant}}}', encoding="utf-8")

    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(bundle)


@pytest.mark.parametrize("text", ["[1]", '"bundle"', "1", "null"])
def test_bundle_digest_rejects_non_object_top_level(tmp_path: Path, text: str) -> None:
    bundle = tmp_path / "top-level.json"
    bundle.write_text(text, encoding="utf-8")

    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(bundle)


@pytest.mark.parametrize(
    "content",
    [b"{not json", b"", b"\xff\xfe{}"],
    ids=["malformed", "empty", "not-utf8"],
)
def test_bundle_digest_wraps_parse_failures(tmp_path: Path, content: bytes) -> None:
    bundle = tmp_path / "broken.json"
    bundle.write_bytes(content)

    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(bundle)


def test_bundle_digest_wraps_missing_file(tmp_path: Path) -> None:
    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(tmp_path / "absent.json")
