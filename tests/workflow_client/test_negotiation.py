from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from tests.workflow_client.conftest import (
    ACCEPTED_APPLY,
    BUNDLE,
    FIXTURE,
    OMIT,
    FakeController,
    live_contract,
    load_json,
    make_client,
    make_envelope,
    request_path,
    write_bundle,
)

from ovcaq.workflow_client import (
    PROTOCOL_MAJOR,
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
@pytest.mark.parametrize("suffix", ["", "+live", "+build.7"])
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

    with pytest.raises(IncompatibleContractError):
        make_client(fake, project_root, bundle=bundle).contract()


def test_contract_rejects_pinned_bundle_holding_only_protocol_major(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    bundle = write_bundle(
        tmp_path,
        package_version=OMIT,
        schema_digest=OMIT,
        fixture_digest=OMIT,
        operations=OMIT,
        capabilities=OMIT,
    )
    assert load_json(bundle) == {"protocol_major": PROTOCOL_MAJOR}
    fake.respond(json.dumps(live_contract()), verb="contract")

    with pytest.raises(IncompatibleContractError):
        make_client(fake, project_root, bundle=bundle).contract()


@pytest.mark.parametrize("field_name", ["schema_digest", "fixture_digest"])
def test_contract_refuses_digests_that_are_null_in_both_documents(
    fake: FakeController, project_root: Path, tmp_path: Path, field_name: str
) -> None:
    bundle = write_bundle(tmp_path, **{field_name: None})
    fake.respond(json.dumps(live_contract(**{field_name: None})), verb="contract")

    with pytest.raises((IncompatibleContractError, ControllerOutputError)):
        make_client(fake, project_root, bundle=bundle).contract()


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


@pytest.mark.parametrize("value", [123, "", b"abc", [], 1.5])
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


def test_apply_negotiates_the_contract_before_issuing_its_verb(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(json.dumps(ACCEPTED_APPLY), verb="apply")

    result = make_client(fake, project_root, actor_file=actor_file).apply(
        make_envelope()
    )

    assert isinstance(result, ApplyResult)
    assert result.revision == ACCEPTED_APPLY["revision"]
    assert fake.verbs() == ["contract", "apply"]
    assert fake.call_for("contract")["argv"] == [*fake.child_argv, "--json", "contract"]
    assert not request_path(fake.call_for("apply")).exists()


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
