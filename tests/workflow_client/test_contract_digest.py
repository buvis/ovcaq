"""The one definition that turns a contract-bundle path into a digest."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pytest

from ovcaq.workflow_client import (
    PROTOCOL_MAJOR,
    IncompatibleContractError,
    controller_bundle_digest,
)

BUNDLE = Path(__file__).parents[1] / "fixtures" / "workflow" / "controller-v1.json"
# The fields a file must hold before it is a contract bundle at all.
REQUIRED_FIELDS = frozenset({"protocol_major", "operations", "capabilities"})


def load_bundle() -> dict[str, Any]:
    data = json.loads(BUNDLE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def write_bundle(path: Path, data: dict[str, Any], **dump_args: Any) -> Path:
    path.write_text(json.dumps(data, **dump_args), encoding="utf-8")
    return path


def write_raw(path: Path, text: str) -> Path:
    """A bundle written as text, for JSON no dumper would ever produce."""
    path.write_text(text, encoding="utf-8")
    return path


def raw_sha256(path: Path) -> str:
    """Reference digest: sha256 of the file's raw bytes, as sha256sum prints."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def complete_bundle_text(*extra: str, override: dict[str, str] | None = None) -> str:
    """Every fixture field as raw JSON text, plus `extra` entries verbatim.

    The result carries each required field, so a file built here can only be
    refused for the defect the caller injected.
    """
    replaced = {} if override is None else override
    entries = [
        f"{json.dumps(name)}: {replaced.get(name, json.dumps(value))}"
        for name, value in load_bundle().items()
    ]
    return "{" + ", ".join([*entries, *extra]) + "}"


def incomplete_body(field: str) -> bytes:
    data = load_bundle()
    del data[field]
    return json.dumps(data, indent=2).encode("utf-8")


# Digest of controller-v1.json, recomputed from the committed file's bytes, so
# the rule stays described even when the fixture changes on purpose. This is the
# value `sha256sum tests/fixtures/workflow/controller-v1.json` prints.
FIXTURE_DIGEST = raw_sha256(BUNDLE)


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


def test_bundle_digest_changes_with_key_order_and_whitespace(tmp_path: Path) -> None:
    data = load_bundle()
    reordered = dict(reversed(list(data.items())))
    compact = write_bundle(tmp_path / "compact.json", data, separators=(",", ":"))
    spaced = write_bundle(tmp_path / "spaced.json", data, indent=8)
    shuffled = write_bundle(
        tmp_path / "shuffled.json", reordered, separators=(",", ":")
    )

    fixture = controller_bundle_digest(BUNDLE)

    # Same values, different bytes: whitespace alone moves the digest.
    assert controller_bundle_digest(compact) != fixture
    assert controller_bundle_digest(spaced) != fixture
    assert controller_bundle_digest(spaced) != controller_bundle_digest(compact)
    # Same values and same formatting, different key order.
    assert controller_bundle_digest(shuffled) != controller_bundle_digest(compact)


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


def test_bundle_digest_is_sha256_of_the_raw_file_bytes() -> None:
    canonical = json.dumps(load_bundle(), sort_keys=True).encode()
    digest = controller_bundle_digest(BUNDLE)

    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    assert digest == raw_sha256(BUNDLE)
    assert digest == FIXTURE_DIGEST
    # The pretty-printed fixture's bytes differ from its canonical JSON form.
    assert BUNDLE.read_bytes() != canonical
    assert digest != hashlib.sha256(canonical).hexdigest()


def test_bundle_digest_follows_raw_byte_algorithm_for_mutated_copy(
    tmp_path: Path,
) -> None:
    data = load_bundle()
    mutated = write_bundle(
        tmp_path / "mutated.json", {**data, "package_version": "9.9.9"}, indent=3
    )
    digest = controller_bundle_digest(mutated)

    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    assert digest == raw_sha256(mutated)
    assert digest != FIXTURE_DIGEST


def test_bundle_digest_refuses_a_canonical_form_pin_for_the_pretty_fixture(
    tmp_path: Path,
) -> None:
    """One definition, not two: a pin of the other form of the same JSON fails."""
    canonical = json.dumps(load_bundle(), sort_keys=True).encode("utf-8")
    canonical_pin = hashlib.sha256(canonical).hexdigest()
    copy = tmp_path / "canonical.json"
    copy.write_bytes(canonical)
    assert json.loads(canonical) == load_bundle()
    assert canonical_pin != FIXTURE_DIGEST

    with pytest.raises(IncompatibleContractError) as caught:
        controller_bundle_digest(BUNDLE, expected_digest=canonical_pin)

    assert FIXTURE_DIGEST in str(caught.value)
    # And the other direction: the canonical file answers to its own bytes only.
    assert controller_bundle_digest(copy, canonical_pin) == canonical_pin
    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(copy, expected_digest=FIXTURE_DIGEST)


# Digesting a bundle is also validation: an artifact missing a required contract
# field is not a bundle, has no digest, and its refusal names the missing field.
@pytest.mark.parametrize("field", sorted(REQUIRED_FIELDS))
def test_bundle_digest_refuses_bundle_missing_a_required_field(
    tmp_path: Path, field: str
) -> None:
    data = load_bundle()
    del data[field]
    incomplete = write_bundle(tmp_path / "incomplete.json", data)

    with pytest.raises(IncompatibleContractError) as caught:
        controller_bundle_digest(incomplete)

    # The reason names the absent field and no field that is present, so it
    # reports which one is gone rather than reciting the whole requirement.
    reason = str(caught.value).replace(str(incomplete), "")
    assert field in reason
    assert all(present not in reason for present in REQUIRED_FIELDS - {field})


def test_bundle_digest_checks_that_required_fields_are_present_not_their_types(
    tmp_path: Path,
) -> None:
    """Deliberate choice: the digest path checks presence, never value shape.

    Field types and the protocol major are negotiated by contract(); a pin only
    answers whether this file is the bundle the operator pinned.
    """
    odd = write_bundle(
        tmp_path / "odd.json",
        {
            "protocol_major": "nope",
            "operations": {"workflow.open": True},
            "capabilities": None,
        },
    )

    assert controller_bundle_digest(odd) == raw_sha256(odd)


def test_bundle_digest_accepts_matching_expected_digest() -> None:
    assert re.fullmatch(r"[0-9a-f]{64}", FIXTURE_DIGEST)
    assert controller_bundle_digest(BUNDLE, FIXTURE_DIGEST) == FIXTURE_DIGEST
    assert controller_bundle_digest(BUNDLE, expected_digest=None) == FIXTURE_DIGEST


def test_bundle_digest_rejects_wrong_expected_digest() -> None:
    wrong = "0" * 64

    with pytest.raises(IncompatibleContractError) as caught:
        controller_bundle_digest(BUNDLE, expected_digest=wrong)

    assert wrong in str(caught.value)
    assert FIXTURE_DIGEST in str(caught.value)


@pytest.mark.parametrize(
    "pin",
    [
        FIXTURE_DIGEST[:1],
        FIXTURE_DIGEST[:32],
        FIXTURE_DIGEST[:63],
        FIXTURE_DIGEST + "0",
        "",
        "b",
    ],
    ids=["one-hex", "half", "truncated", "extended", "empty", "single-letter"],
)
def test_bundle_digest_rejects_a_pin_that_is_not_the_whole_digest(pin: str) -> None:
    """A pin is compared whole: a prefix of the digest pins nothing."""
    assert pin != FIXTURE_DIGEST

    with pytest.raises(IncompatibleContractError) as caught:
        controller_bundle_digest(BUNDLE, expected_digest=pin)

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


@pytest.mark.parametrize(
    "body",
    [
        b"null",
        b"{}",
        b"{not json",
        *(incomplete_body(field) for field in sorted(REQUIRED_FIELDS)),
    ],
    ids=[
        "null",
        "empty-object",
        "malformed",
        "no-capabilities",
        "no-operations",
        "no-protocol_major",
    ],
)
def test_bundle_digest_validates_the_file_even_when_the_pin_matches(
    tmp_path: Path, body: bytes
) -> None:
    """A matching pin never waives validation: a non-bundle has no digest."""
    bundle = tmp_path / "pinned.json"
    bundle.write_bytes(body)

    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(bundle, expected_digest=raw_sha256(bundle))


def test_bundle_digest_rejects_duplicate_keys(tmp_path: Path) -> None:
    text = complete_bundle_text(
        f'"operations": {json.dumps(load_bundle()["operations"])}'
    )
    duplicate = write_raw(tmp_path / "duplicate.json", text)

    # Last value wins, so a lenient parser sees the fixture itself: nothing but
    # the repeated key can refuse this file.
    assert json.loads(text) == load_bundle()
    with pytest.raises(IncompatibleContractError, match="duplicate"):
        controller_bundle_digest(duplicate)


def test_bundle_digest_rejects_nested_duplicate_keys(tmp_path: Path) -> None:
    nested = write_raw(
        tmp_path / "nested.json", complete_bundle_text('"extra": {"a": 1, "a": 2}')
    )
    clean = write_raw(
        tmp_path / "clean.json", complete_bundle_text('"extra": {"a": 1, "b": 2}')
    )

    # The same bundle without the repeated inner key has a digest, so the
    # refusal is about the duplicate, not about the extra field.
    assert controller_bundle_digest(clean) == raw_sha256(clean)
    with pytest.raises(IncompatibleContractError, match="duplicate"):
        controller_bundle_digest(nested)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_bundle_digest_rejects_non_finite_numbers(
    tmp_path: Path, constant: str
) -> None:
    text = complete_bundle_text(override={"protocol_major": constant})
    bundle = write_raw(tmp_path / "constant.json", text)

    # Every required field is present, so only the non-finite value is at fault.
    assert set(json.loads(text)) == set(load_bundle())
    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(bundle)


@pytest.mark.parametrize("text", ["[1]", '"bundle"', "1", "null"])
def test_bundle_digest_rejects_non_object_top_level(tmp_path: Path, text: str) -> None:
    bundle = write_raw(tmp_path / "top-level.json", text)

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


# Hex letter case is not part of a pin's identity: the operator who pastes
# `sha256sum` output in capitals names the same bundle the tool accepts.
MIXED_CASE_DIGEST = "".join(
    char.upper() if index % 2 else char for index, char in enumerate(FIXTURE_DIGEST)
)


@pytest.mark.parametrize(
    "pin",
    [FIXTURE_DIGEST, FIXTURE_DIGEST.upper(), MIXED_CASE_DIGEST],
    ids=["lower", "upper", "mixed"],
)
def test_bundle_digest_accepts_a_pin_differing_only_in_hex_letter_case(
    pin: str,
) -> None:
    """One configured value: the same digest in any letter case is one pin."""
    # The fixture digest holds hex letters, so the capitalised variants differ.
    assert any(char.isalpha() for char in FIXTURE_DIGEST)
    assert FIXTURE_DIGEST.upper() != FIXTURE_DIGEST
    assert pin.lower() == FIXTURE_DIGEST

    accepted = controller_bundle_digest(BUNDLE, expected_digest=pin)

    assert accepted.lower() == FIXTURE_DIGEST


@pytest.mark.parametrize(
    "pin",
    [
        FIXTURE_DIGEST.upper()[:32],
        FIXTURE_DIGEST.upper() + "0",
        f" {FIXTURE_DIGEST.upper()} ",
        hashlib.sha256(b"other bundle").hexdigest().upper(),
    ],
    ids=["half", "extended", "surrounded", "other-bundle"],
)
def test_bundle_digest_rejects_an_uppercase_pin_that_is_not_the_whole_digest(
    pin: str,
) -> None:
    """Letter case is all that is forgiven: prefixes and junk still fail."""
    assert pin.lower() != FIXTURE_DIGEST

    with pytest.raises(IncompatibleContractError) as caught:
        controller_bundle_digest(BUNDLE, expected_digest=pin)

    assert FIXTURE_DIGEST in str(caught.value)


def test_bundle_digest_rejects_an_uppercase_pin_taken_from_another_bundle(
    tmp_path: Path,
) -> None:
    """An uppercase pin is still compared against this file's own bytes."""
    other = write_bundle(
        tmp_path / "other.json", {**load_bundle(), "package_version": "9.9.9"}
    )
    assert raw_sha256(other) != FIXTURE_DIGEST

    with pytest.raises(IncompatibleContractError) as caught:
        controller_bundle_digest(other, expected_digest=FIXTURE_DIGEST.upper())

    assert raw_sha256(other) in str(caught.value)
    # The same call for the same file, pinned by its own digest in capitals.
    accepted = controller_bundle_digest(other, raw_sha256(other).upper())
    assert accepted.lower() == raw_sha256(other)
