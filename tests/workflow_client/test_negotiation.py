from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

import pytest
from tests.workflow_client.conftest import (
    ACCEPTED_APPLY,
    APPLY_RESPONSES,
    BUNDLE,
    FIXTURE,
    OMIT,
    FakeController,
    envelope_as_json,
    live_contract,
    load_json,
    make_client,
    make_envelope,
    marks_truncation,
    request_path,
    secret_fragments,
    write_bundle,
)

from ovcaq.workflow_client import (
    MAX_STDERR_TAIL_CHARS,
    MIN_SECRET_CHARS,
    PROTOCOL_MAJOR,
    REDACTED_MARKER,
    TRUNCATION_MARKER,
    ApplyResult,
    ControllerClient,
    ControllerConfig,
    ControllerOutputError,
    IncompatibleContractError,
    controller_bundle_digest,
)

# 1. Advertised-set negotiation


@pytest.mark.parametrize("operation", FIXTURE["operations"])
def test_contract_rejects_live_controller_missing_a_pinned_operation(
    fake: FakeController, project_root: Path, operation: str
) -> None:
    kept = [name for name in FIXTURE["operations"] if name != operation]
    fake.respond(json.dumps(live_contract(operations=kept)), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root).contract()

    assert operation in str(caught.value)
    assert len(fake.calls()) == 1


@pytest.mark.parametrize("capability", FIXTURE["capabilities"])
def test_contract_rejects_live_controller_missing_a_pinned_capability(
    fake: FakeController, project_root: Path, capability: str
) -> None:
    kept = [name for name in FIXTURE["capabilities"] if name != capability]
    fake.respond(json.dumps(live_contract(capabilities=kept)), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root).contract()

    assert capability in str(caught.value)
    assert len(fake.calls()) == 1


def test_contract_rejects_live_operation_that_only_extends_a_pinned_name(
    fake: FakeController, project_root: Path
) -> None:
    # "workflow.apply-v2" is a different operation, not the pinned one.
    pinned = "workflow.apply"
    renamed = [
        f"{name}-v2" if name == pinned else name for name in FIXTURE["operations"]
    ]
    fake.respond(json.dumps(live_contract(operations=renamed)), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root).contract()

    assert pinned in str(caught.value)
    assert len(fake.calls()) == 1


def test_contract_rejects_a_capability_advertised_only_as_an_operation(
    fake: FakeController, project_root: Path
) -> None:
    capability = "idempotent-request-id"
    live = live_contract(
        capabilities=[name for name in FIXTURE["capabilities"] if name != capability]
    )
    live["operations"] = [*live["operations"], capability]
    fake.respond(json.dumps(live), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root).contract()

    assert capability in str(caught.value)


def test_contract_rejects_a_pinned_name_present_only_in_an_unrelated_field(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    # The digest text mentions the capability; the capability list does not.
    capability = "lease-epoch"
    bundle = write_bundle(tmp_path, schema_digest=f"{capability}-{'0' * 48}")
    pinned = load_json(bundle)
    kept = [name for name in pinned["capabilities"] if name != capability]
    fake.respond(json.dumps(live_contract(pinned, capabilities=kept)), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root, bundle=bundle).contract()

    assert capability in str(caught.value)


@pytest.mark.parametrize(
    ("operations", "capabilities"),
    [
        (["contract.describe", "workflow.open", "workflow.read", "workflow.apply"], []),
        (["workflow.open"], ["lease-epoch"]),
    ],
    ids=["all-operations", "fewer-pinned"],
)
def test_contract_accepts_live_controller_advertising_more_than_pinned(
    fake: FakeController,
    project_root: Path,
    tmp_path: Path,
    operations: list[str],
    capabilities: list[str],
) -> None:
    bundle = write_bundle(tmp_path, operations=operations, capabilities=capabilities)
    live = live_contract(load_json(bundle))
    fake.respond(json.dumps(live), verb="contract")

    contract = make_client(fake, project_root, bundle=bundle).contract()

    assert contract.operations >= frozenset(operations)
    assert contract.capabilities >= frozenset(capabilities)
    assert "workflow.live-only" in contract.operations
    assert "live-only" in contract.capabilities


# 2. Producer identity


@pytest.mark.parametrize("pinned_version", ["1.0.0", "1.4.2"])
@pytest.mark.parametrize(
    "suffix", ["", "+live", "+build.7", "+sha.deadbeef", "+2", "+g1a2b3c.dirty"]
)
def test_contract_accepts_live_package_version_equal_or_build_tagged(
    fake: FakeController,
    project_root: Path,
    tmp_path: Path,
    pinned_version: str,
    suffix: str,
) -> None:
    bundle = write_bundle(tmp_path, package_version=pinned_version)
    live_version = pinned_version + suffix
    live = live_contract(load_json(bundle), package_version=live_version)
    fake.respond(json.dumps(live), verb="contract")

    contract = make_client(fake, project_root, bundle=bundle).contract()

    assert contract.package_version == live_version


@pytest.mark.parametrize(
    "live_version",
    ["1.0.1", "2.0.0", "0.9.0+live", "1.0.0-rc1", "", "1.0.0+", "11.0.0"],
)
def test_contract_rejects_live_package_version_other_than_the_pinned_one(
    fake: FakeController, project_root: Path, live_version: str
) -> None:
    assert live_version != FIXTURE["package_version"]
    live = live_contract(package_version=live_version)
    fake.respond(json.dumps(live), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root).contract()

    assert FIXTURE["package_version"] in str(caught.value)
    assert live_version in str(caught.value)


# 3. Required fields are validated before they are compared

PINNED_FIELDS = ["package_version", "schema_digest", "fixture_digest"]
UNUSABLE_LIVE = {
    "package_version": [100, None, ["1.0.0"], {"v": "1.0.0"}],
    "schema_digest": [OMIT, "", 7, None],
    "fixture_digest": [OMIT, "", 7, None],
}
UNUSABLE_LIVE_CASES = [
    (name, value) for name, values in UNUSABLE_LIVE.items() for value in values
]


@pytest.mark.parametrize("field_name", PINNED_FIELDS)
@pytest.mark.parametrize(
    "pinned_value", [OMIT, "", 123, None], ids=["missing", "empty", "int", "null"]
)
def test_contract_rejects_pinned_bundle_with_an_unusable_required_string(
    fake: FakeController,
    project_root: Path,
    tmp_path: Path,
    field_name: str,
    pinned_value: Any,
) -> None:
    bundle = write_bundle(tmp_path, **{field_name: pinned_value})
    fake.respond(json.dumps(live_contract()), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root, bundle=bundle).contract()

    # The pinned document is at fault, not the controller's output.
    assert field_name in str(caught.value)
    assert not isinstance(caught.value, ControllerOutputError)


@pytest.mark.parametrize(
    "omitted",
    [
        PINNED_FIELDS + ["operations", "capabilities"],
        ["operations", "capabilities"],
    ],
    ids=["only-protocol-major", "every-string-but-no-sets"],
)
def test_contract_rejects_pinned_bundle_without_operations_or_capabilities(
    fake: FakeController, project_root: Path, tmp_path: Path, omitted: list[str]
) -> None:
    bundle = write_bundle(tmp_path, **{name: OMIT for name in omitted})
    pinned = load_json(bundle)
    assert pinned["protocol_major"] == PROTOCOL_MAJOR
    assert not {"operations", "capabilities"} & set(pinned)
    fake.respond(json.dumps(live_contract()), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root, bundle=bundle).contract()

    # A bundle without operations or capabilities is refused as a bundle, so the
    # reason names one of those before any pinned string is ever compared.
    assert any(name in str(caught.value) for name in ("operations", "capabilities"))
    assert "package_version" not in str(caught.value)
    assert not isinstance(caught.value, ControllerOutputError)


@pytest.mark.parametrize("unusable", [None, ""], ids=["null", "empty"])
@pytest.mark.parametrize("field_name", PINNED_FIELDS)
def test_contract_refuses_required_strings_that_are_unusable_in_both_documents(
    fake: FakeController,
    project_root: Path,
    tmp_path: Path,
    field_name: str,
    unusable: Any,
) -> None:
    # Matching values are not agreement when neither value is usable.
    bundle = write_bundle(tmp_path, **{field_name: unusable})
    fake.respond(json.dumps(live_contract(**{field_name: unusable})), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root, bundle=bundle).contract()

    assert field_name in str(caught.value)
    assert not isinstance(caught.value, ControllerOutputError)


@pytest.mark.parametrize(("field_name", "live_value"), UNUSABLE_LIVE_CASES)
def test_contract_reports_an_unusable_live_field_as_an_output_error(
    fake: FakeController, project_root: Path, field_name: str, live_value: Any
) -> None:
    live = live_contract(**{field_name: live_value})
    if live_value is OMIT:
        del live[field_name]
    fake.respond(json.dumps(live), verb="contract")

    with pytest.raises(ControllerOutputError) as caught:
        make_client(fake, project_root).contract()

    assert not isinstance(caught.value, IncompatibleContractError)


# 4. Bundle-digest pinning


def test_config_leaves_bundle_digest_unpinned_by_default(
    fake: FakeController, project_root: Path
) -> None:
    config = ControllerConfig(
        argv=fake.argv,
        contract_bundle=BUNDLE,
        actor_file=None,
        project_root=project_root,
    )

    assert config.bundle_digest is None


@pytest.mark.parametrize(
    "value",
    [
        123,
        "",
        b"",
        b"abc",
        [],
        ["0" * 64],
        {},
        {"digest": "0" * 64},
        1.5,
        0.5,
        True,
        object(),
    ],
)
def test_config_rejects_bundle_digest_that_is_not_a_nonempty_string(
    fake: FakeController, project_root: Path, value: Any
) -> None:
    with pytest.raises((TypeError, ValueError)):
        ControllerConfig(
            argv=fake.argv,
            contract_bundle=BUNDLE,
            actor_file=None,
            project_root=project_root,
            bundle_digest=value,
        )


def test_contract_accepts_bundle_whose_content_digest_matches_the_pin(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    bundle = write_bundle(tmp_path, package_version="1.4.2")
    live = live_contract(load_json(bundle), package_version="1.4.2+live")
    fake.respond(json.dumps(live), verb="contract")

    contract = make_client(
        fake,
        project_root,
        bundle=bundle,
        bundle_digest=controller_bundle_digest(bundle),
    ).contract()

    assert contract.package_version == "1.4.2+live"
    assert len(fake.calls()) == 1


@pytest.mark.parametrize(
    "tamper",
    [
        {"package_version": "1.0.1"},
        {"schema_digest": "0" * 64},
        {"operations": ["contract.describe", "workflow.open", "workflow.read"]},
        {"capabilities": ["expected-revision", "lease-epoch"]},
        {"protocol_major": PROTOCOL_MAJOR + 1},
    ],
    ids=["version", "schema", "operations", "capabilities", "major"],
)
def test_contract_rejects_tampered_bundle_before_spawning_the_controller(
    fake: FakeController, project_root: Path, tmp_path: Path, tamper: dict[str, Any]
) -> None:
    bundle = write_bundle(tmp_path)
    pin = controller_bundle_digest(bundle)
    tampered = write_bundle(tmp_path, **tamper)
    fake.respond(json.dumps(live_contract()), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root, bundle=tampered, bundle_digest=pin).contract()

    assert pin in str(caught.value)
    assert controller_bundle_digest(tampered) in str(caught.value)
    assert fake.calls() == []


def test_contract_skips_the_content_digest_check_when_it_is_unpinned(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    # The same edited bundle that a pin rejects is served without a pin.
    bundle = write_bundle(tmp_path, package_version="2.5.0")
    live = live_contract(load_json(bundle), package_version="2.5.0+live")
    fake.respond(json.dumps(live), verb="contract")

    contract = make_client(
        fake, project_root, bundle=bundle, bundle_digest=None
    ).contract()

    assert contract.package_version == "2.5.0+live"


# 9. Negotiation is mandatory before snapshot() and apply()


def test_snapshot_negotiates_the_contract_before_issuing_its_verb(
    fake: FakeController, project_root: Path
) -> None:
    payload = {"workflow_id": "workflow-a", "revision": 7, "phase": "review"}
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(json.dumps(payload), verb="snapshot")

    snapshot = make_client(fake, project_root).snapshot(workflow_id="workflow-a")

    assert snapshot == payload
    calls = fake.calls()
    assert [record["verb"] for record in calls] == ["contract", "snapshot"]
    assert calls[0]["argv"] == [*fake.child_argv, "--json", "contract"]
    assert calls[1]["argv"] == [
        *fake.child_argv,
        "--json",
        "snapshot",
        "--project-root",
        str(project_root),
    ]


@pytest.mark.parametrize("response", APPLY_RESPONSES, ids=["accepted", "rejected"])
def test_apply_negotiates_the_contract_before_issuing_its_verb(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    response: dict[str, Any],
) -> None:
    envelope = make_envelope(request_id="req-0101", expected_revision=4)
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(json.dumps(response), verb="apply")

    result = make_client(fake, project_root, actor_file=actor_file).apply(envelope)

    assert isinstance(result, ApplyResult)
    assert result.ok is response["ok"]
    assert result.revision == response["revision"]
    assert result.result == response["result"]
    assert result.error_code == response["error_code"]
    assert result.retryable is response["retryable"]
    assert fake.verbs() == ["contract", "apply"]
    assert fake.call_for("contract")["argv"] == [*fake.child_argv, "--json", "contract"]
    call = fake.call_for("apply")
    # The envelope really travelled in the request file, privately.
    assert json.loads(call["request"]) == envelope_as_json(envelope)
    assert call["request_mode"] == 0o600
    assert not request_path(call).exists()


def failing_negotiation(
    fake: FakeController,
    project_root: Path,
    tmp_path: Path,
    failure: str,
    *,
    actor_file: Path | None = None,
) -> tuple[ControllerClient, list[str]]:
    """A client whose negotiation must fail, with the calls it may make."""
    if failure == "digest-mismatch":
        pin = controller_bundle_digest(write_bundle(tmp_path))
        edited = write_bundle(tmp_path, package_version="9.9.9")
        fake.respond(json.dumps(live_contract()), verb="contract")
        client = make_client(
            fake,
            project_root,
            actor_file=actor_file,
            bundle=edited,
            bundle_digest=pin,
        )
        return client, []
    if failure == "protocol-major":
        live = live_contract(protocol_major=PROTOCOL_MAJOR + 1)
    else:
        live = live_contract(
            capabilities=[
                name
                for name in FIXTURE["capabilities"]
                if name != "idempotent-request-id"
            ]
        )
    fake.respond(json.dumps(live), verb="contract")
    return make_client(fake, project_root, actor_file=actor_file), ["contract"]


NEGOTIATION_FAILURES = ["protocol-major", "missing-capability", "digest-mismatch"]


@pytest.mark.parametrize("failure", NEGOTIATION_FAILURES)
def test_failed_negotiation_never_reaches_the_snapshot_verb(
    fake: FakeController, project_root: Path, tmp_path: Path, failure: str
) -> None:
    fake.respond(json.dumps({"revision": 1}), verb="snapshot")
    client, expected = failing_negotiation(fake, project_root, tmp_path, failure)

    with pytest.raises(IncompatibleContractError):
        client.snapshot(workflow_id="workflow-a")

    assert fake.verbs() == expected


@pytest.mark.parametrize("failure", NEGOTIATION_FAILURES)
def test_failed_negotiation_never_reaches_the_apply_verb(
    fake: FakeController,
    project_root: Path,
    tmp_path: Path,
    actor_file: Path,
    failure: str,
) -> None:
    fake.respond(json.dumps(ACCEPTED_APPLY), verb="apply")
    client, expected = failing_negotiation(
        fake, project_root, tmp_path, failure, actor_file=actor_file
    )

    with pytest.raises(IncompatibleContractError):
        client.apply(make_envelope())

    assert fake.verbs() == expected
    assert list(project_root.iterdir()) == []


def test_negotiation_happens_at_most_once_per_client(
    fake: FakeController, project_root: Path
) -> None:
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(json.dumps({"revision": 4}), verb="snapshot")
    client = make_client(fake, project_root)

    assert client.snapshot(workflow_id="workflow-a") == {"revision": 4}
    assert client.snapshot(workflow_id="workflow-b") == {"revision": 4}

    assert fake.verbs() == ["contract", "snapshot", "snapshot"]


def test_an_already_negotiated_client_does_not_negotiate_again(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(json.dumps({"revision": 5}), verb="snapshot")
    fake.respond(json.dumps(ACCEPTED_APPLY), verb="apply")
    client = make_client(fake, project_root, actor_file=actor_file)

    client.contract()
    assert client.snapshot(workflow_id="workflow-a") == {"revision": 5}
    client.apply(make_envelope())

    assert fake.verbs() == ["contract", "snapshot", "apply"]


# 10. Mismatch diagnostics carry live values through the stderr pipeline

# Synthetic canaries only; never a real credential. Two distinct long values, so
# a replacement list hardcoded to one of them fails.
LONG_CANARY = "canary-negotiate-" + "n" * (MIN_SECRET_CHARS + 40)
RIVAL_CANARY = "canary-rival-" + "r" * (MIN_SECRET_CHARS + 40)
# One character below the threshold, and a strict prefix of both canaries, so
# prefix or substring masking eats it and fails.
LEGIBLE_WORD = RIVAL_CANARY[: MIN_SECRET_CHARS - 1]
# Filler short enough to survive masking, so the bound measures real text.
SHORT_FILLER = "t" * (MIN_SECRET_CHARS - 1)
# Marker words that sit at one end of a padded value only, so a dropped head
# and a kept tail are both visible.
HEAD_WORD = "zarq-hd"
TAIL_WORD = "zarq-tl"


def minted_secret() -> str:
    """A long token minted at run time, so no literal can be pre-baked."""
    return secrets.token_urlsafe(24)


def padded_live_value(words: int) -> str:
    """A mismatching live value built only from tokens masking must keep."""
    filler = " ".join([SHORT_FILLER] * words)
    return f"{HEAD_WORD} {filler} {TAIL_WORD}"


@pytest.mark.parametrize("field_name", PINNED_FIELDS)
@pytest.mark.parametrize("canary", [LONG_CANARY, RIVAL_CANARY], ids=["alpha", "rival"])
def test_contract_redacts_a_secret_echoed_into_a_mismatching_live_field(
    fake: FakeController, project_root: Path, field_name: str, canary: str
) -> None:
    """A controller cannot smuggle credential bytes out through a mismatch."""
    minted = minted_secret()
    live_value = f"{LEGIBLE_WORD} {canary} {minted}"
    assert live_value != FIXTURE[field_name]
    live: dict[str, Any] = {field_name: live_value}
    fake.respond(json.dumps(live_contract(**live)), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root, actor_file=None).contract()

    message = str(caught.value)
    assert canary not in message
    assert minted not in message
    assert not any(piece in message for piece in secret_fragments(canary))
    assert not any(piece in message for piece in secret_fragments(minted))
    assert REDACTED_MARKER in message
    # Short words stay legible, and the pinned side comes from the local bundle.
    assert LEGIBLE_WORD in message
    assert FIXTURE[field_name] in message
    assert fake.verbs() == ["contract"]


@pytest.mark.parametrize(
    ("words", "truncates"),
    [(MAX_STDERR_TAIL_CHARS // 32, False), (MAX_STDERR_TAIL_CHARS // 4, True)],
    ids=["within-bound", "over-long"],
)
def test_contract_bounds_the_mismatching_live_value_it_reports(
    fake: FakeController, project_root: Path, words: int, truncates: bool
) -> None:
    """An over-long live value cannot grow the diagnostic without limit."""
    live_value = padded_live_value(words)
    assert (len(live_value) > MAX_STDERR_TAIL_CHARS) is truncates
    fake.respond(json.dumps(live_contract(schema_digest=live_value)), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root, actor_file=None).contract()

    message = str(caught.value)
    # The tail is what a reader needs, so it survives either way.
    assert TAIL_WORD in message
    if truncates:
        assert live_value not in message
        assert HEAD_WORD not in message
        assert TRUNCATION_MARKER in message
        assert marks_truncation(message)
        assert message.count(SHORT_FILLER) <= MAX_STDERR_TAIL_CHARS // 8
    else:
        assert live_value in message
        assert HEAD_WORD in message
    # The live value really came from the controller this client spawned.
    assert fake.call_for("contract")["argv"] == [*fake.child_argv, "--json", "contract"]
