from __future__ import annotations

import contextlib
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import pytest
from tests.workflow_client.conftest import (
    ACCEPTED_APPLY,
    BUNDLE,
    CALL_BY_VERB,
    CANARY,
    EVERY_VERB,
    SLOW_SECONDS,
    TIMEOUT_BUDGET,
    FakeController,
    envelope_as_json,
    exception_chain,
    live_contract,
    load_json,
    make_client,
    make_envelope,
    process_ended,
    request_path,
)

from ovcaq.workflow_client import (
    PROTOCOL_MAJOR,
    ApplyResult,
    ControllerClient,
    ControllerConfig,
    ControllerContract,
    ControllerError,
    ControllerOutputError,
    ControllerTimeoutError,
    IncompatibleContractError,
    MutationEnvelope,
)

# Negotiation is mandatory, so every snapshot or apply call spends a contract
# hop first; this answer satisfies the pinned fixture bundle.
CONTRACT_ANSWER = json.dumps(live_contract())


def write_variant_bundle(tmp_path: Path) -> Path:
    """A second valid bundle whose every field differs from the fixture."""
    path = tmp_path / "variant-bundle.json"
    data = {
        "protocol_major": PROTOCOL_MAJOR,
        "package_version": "1.4.2",
        "schema_digest": hashlib.sha256(b"variant schema").hexdigest(),
        "fixture_digest": hashlib.sha256(b"variant fixture").hexdigest(),
        "operations": ["workflow.open", "workflow.read"],
        "capabilities": [],
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def expected_contract(data: dict[str, Any]) -> ControllerContract:
    return ControllerContract(
        protocol_major=data["protocol_major"],
        package_version=data["package_version"],
        schema_digest=data["schema_digest"],
        fixture_digest=data["fixture_digest"],
        operations=frozenset(data["operations"]),
        capabilities=frozenset(data["capabilities"]),
    )


def same_directory(left: str | Path, right: Path) -> bool:
    return Path(left).resolve() == right.resolve()


def oversized_answer(verb: str, padding: str) -> str:
    """A well-formed answer for the verb, padded past the output bound."""
    live = live_contract()
    answers = {
        "contract": {**live, "capabilities": [*live["capabilities"], padding]},
        "snapshot": {"revision": 3, "padding": padding},
        "apply": {**ACCEPTED_APPLY, "result": {"phase": "review", "pad": padding}},
    }
    return json.dumps(answers[verb])


# contract()


@pytest.mark.parametrize("variant", [False, True], ids=["fixture", "variant"])
def test_contract_runs_contract_verb_in_project_root_and_maps_bundle(
    fake: FakeController, project_root: Path, tmp_path: Path, variant: bool
) -> None:
    bundle = write_variant_bundle(tmp_path) if variant else BUNDLE
    pinned = load_json(bundle)
    # The live controller agrees on both digests but reports other fields the
    # bundle does not, so only the live answer can produce these values.
    live = live_contract(pinned, package_version=pinned["package_version"] + "+live")
    fake.respond(json.dumps(live), verb="contract")

    contract = make_client(fake, project_root, bundle=bundle).contract()

    assert contract == expected_contract(live)
    assert contract.package_version == live["package_version"]
    assert "workflow.live-only" in contract.operations
    assert "live-only" in contract.capabilities
    assert isinstance(contract.operations, frozenset)
    assert isinstance(contract.capabilities, frozenset)
    assert fake.verbs() == ["contract"]
    call = fake.call_for("contract")
    assert call["argv"] == [*fake.child_argv, "--json", "contract"]
    assert same_directory(call["cwd"], project_root)


@pytest.mark.parametrize("field", ["schema_digest", "fixture_digest"])
@pytest.mark.parametrize("kind", ["last-char", "prefix", "extended"])
def test_contract_rejects_digest_not_pinned_by_bundle(
    fake: FakeController, project_root: Path, field: str, kind: str
) -> None:
    data = load_json(BUNDLE)
    pinned = data[field]
    reported = {
        "last-char": pinned[:-1] + ("0" if pinned[-1] != "0" else "1"),
        "prefix": pinned[:32],
        "extended": pinned + "0",
    }[kind]
    fake.respond(json.dumps({**data, field: reported}), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root).contract()

    assert reported in str(caught.value)
    assert pinned in str(caught.value)


def test_contract_compares_against_configured_bundle(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    # The live controller matches the repo fixture, but the client is pinned
    # to a different bundle, so the pin must win.
    fake.respond(BUNDLE.read_text(encoding="utf-8"), verb="contract")

    with pytest.raises(IncompatibleContractError):
        make_client(
            fake, project_root, bundle=write_variant_bundle(tmp_path)
        ).contract()

    assert fake.verbs() == ["contract"]


@pytest.mark.parametrize("major", [0, 2, 99])
def test_contract_rejects_incompatible_protocol_major(
    fake: FakeController, project_root: Path, major: int
) -> None:
    assert major != PROTOCOL_MAJOR
    fake.respond(
        json.dumps({**load_json(BUNDLE), "protocol_major": major}), verb="contract"
    )

    with pytest.raises(IncompatibleContractError):
        make_client(fake, project_root).contract()

    assert fake.verbs() == ["contract"]


def test_contract_is_cached_per_client_instance_only(
    fake: FakeController, project_root: Path
) -> None:
    data = load_json(BUNDLE)
    fake.respond(json.dumps(data), verb="contract")
    client = make_client(fake, project_root)

    first = client.contract()
    second = client.contract()

    assert first == second == expected_contract(data)
    assert fake.verbs() == ["contract"]

    fresh = make_client(fake, project_root)
    assert fresh.contract() == first
    assert fake.verbs() == ["contract", "contract"]

    # A drifted controller cannot reach a validated instance, but a new
    # instance re-validates and refuses it.
    fake.respond(json.dumps({**data, "schema_digest": "0" * 64}), verb="contract")
    assert client.contract() == first
    assert fake.verbs() == ["contract", "contract"]
    with pytest.raises(IncompatibleContractError):
        make_client(fake, project_root).contract()
    assert fake.verbs() == ["contract", "contract", "contract"]


# snapshot()

SNAPSHOTS = [
    {},
    {
        "workflow_id": "workflow-a",
        "revision": 7,
        "phase": "review",
        "tasks": [{"id": "t1", "done": True}, {"id": "t2", "done": False}],
        "lease": None,
    },
    {"workflow_id": "workflow-b", "revision": 0, "notes": [], "x": {"y": 2.5}},
]


@pytest.mark.parametrize("payload", SNAPSHOTS, ids=["empty", "populated", "other"])
def test_snapshot_runs_snapshot_verb_and_returns_payload_unmodified(
    fake: FakeController, project_root: Path, payload: dict[str, Any]
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    # Stderr noise on a zero exit is not a failure.
    fake.respond(
        json.dumps(payload), stderr="warning: lease renewal slow\n", verb="snapshot"
    )

    snapshot = make_client(fake, project_root).snapshot(workflow_id="workflow-a")

    assert snapshot == payload
    assert fake.verbs() == ["contract", "snapshot"]
    call = fake.call_for("snapshot")
    assert call["argv"] == [
        *fake.child_argv,
        "--json",
        "snapshot",
        "--project-root",
        str(project_root),
    ]
    assert same_directory(call["cwd"], project_root)


@pytest.mark.parametrize("stdout", ["[1, 2]", "42", '"x"'], ids=["list", "int", "str"])
def test_snapshot_rejects_json_that_is_not_an_object(
    fake: FakeController, project_root: Path, stdout: str
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(stdout, verb="snapshot")

    with pytest.raises(ControllerOutputError):
        make_client(fake, project_root).snapshot(workflow_id="workflow-a")


# apply()

ENVELOPES = [
    make_envelope(),
    make_envelope(
        operation="workflow.open",
        request_id="req-0002",
        expected_revision=0,
        workflow_id=None,
        actor_id=None,
        lease_epoch=None,
        payload={"prd": "00058", "tiers": ["fast", "deep"]},
    ),
]


@pytest.mark.parametrize("envelope", ENVELOPES, ids=["apply", "initial-open"])
def test_apply_hands_envelope_to_controller_in_private_request_file(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    envelope: MutationEnvelope,
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(stderr="rejected: stale revision\n", exit_code=4, verb="apply")

    with pytest.raises(ControllerError):
        make_client(fake, project_root, actor_file=actor_file).apply(envelope)

    assert fake.verbs() == ["contract", "apply"]
    call = fake.call_for("apply")
    assert call["argv"][:-1] == [
        *fake.child_argv,
        "--json",
        "apply",
        "--project-root",
        str(project_root),
        "--actor-file",
        str(actor_file),
        "--request",
    ]
    assert same_directory(call["cwd"], project_root)
    assert json.loads(call["request"]) == envelope_as_json(envelope)
    assert call["request_mode"] == 0o600
    assert not request_path(call).exists()
    assert list(project_root.iterdir()) == []


def test_apply_removes_request_file_after_controller_exits_zero(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    # The task does not pin the apply response JSON, so this test checks only
    # the request-file lifecycle on a zero exit, not the returned ApplyResult.
    # Two back-to-back calls on one client must not share a request file, so
    # a fixed, predictable path fails here.
    envelopes = [
        make_envelope(request_id="req-0003", expected_revision=5),
        make_envelope(request_id="req-0004", expected_revision=6),
    ]
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps({"ok": True, "revision": 6}), verb="apply")
    client = make_client(fake, project_root, actor_file=actor_file)

    for envelope in envelopes:
        with contextlib.suppress(ControllerError):
            client.apply(envelope)

    assert fake.verbs() == ["contract", "apply", "apply"]
    calls = [call for call in fake.calls() if call["verb"] == "apply"]
    for call, envelope in zip(calls, envelopes, strict=True):
        assert json.loads(call["request"]) == envelope_as_json(envelope)
        assert call["request_mode"] == 0o600
        assert not request_path(call).exists()
    assert request_path(calls[0]) != request_path(calls[1])
    assert list(project_root.iterdir()) == []


APPLY_RESPONSES = [
    (
        {
            "ok": True,
            "revision": 4,
            "result": {"phase": "build"},
            "error_code": None,
            "retryable": False,
        },
        ApplyResult(
            ok=True,
            revision=4,
            result={"phase": "build"},
            error_code=None,
            retryable=False,
        ),
    ),
    (
        {
            "ok": False,
            "revision": None,
            "result": None,
            "error_code": "stale",
            "retryable": True,
        },
        ApplyResult(
            ok=False, revision=None, result=None, error_code="stale", retryable=True
        ),
    ),
]


@pytest.mark.parametrize(
    ("response", "expected"), APPLY_RESPONSES, ids=["accepted", "rejected"]
)
def test_apply_returns_controller_response_as_apply_result(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    response: dict[str, Any],
    expected: ApplyResult,
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    # A structured rejection on a zero exit is a normal return, not an error.
    fake.respond(json.dumps(response) + "\n", verb="apply")

    result = make_client(fake, project_root, actor_file=actor_file).apply(
        make_envelope()
    )

    assert isinstance(result, ApplyResult)
    assert result.ok is expected.ok
    assert result.revision == expected.revision
    assert result.result == expected.result
    assert result.error_code == expected.error_code
    assert result.retryable is expected.retryable
    assert result == expected
    assert fake.verbs() == ["contract", "apply"]
    assert not request_path(fake.call_for("apply")).exists()


VALID_APPLY_RESPONSE = APPLY_RESPONSES[0][0]
MALFORMED_APPLY_RESPONSES = {
    "missing-ok": {k: v for k, v in VALID_APPLY_RESPONSE.items() if k != "ok"},
    "string-ok": {**VALID_APPLY_RESPONSE, "ok": "yes"},
    "string-revision": {**VALID_APPLY_RESPONSE, "revision": "3"},
}


@pytest.mark.parametrize("malformed", list(MALFORMED_APPLY_RESPONSES))
def test_apply_rejects_malformed_controller_response(
    fake: FakeController, project_root: Path, actor_file: Path, malformed: str
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps(MALFORMED_APPLY_RESPONSES[malformed]), verb="apply")
    outcome: object = None

    with pytest.raises(ControllerOutputError):
        outcome = make_client(fake, project_root, actor_file=actor_file).apply(
            make_envelope()
        )

    assert outcome is None
    assert fake.verbs() == ["contract", "apply"]
    assert not request_path(fake.call_for("apply")).exists()


def test_apply_without_actor_file_refuses_before_spawning(
    fake: FakeController, project_root: Path
) -> None:
    client = make_client(fake, project_root, actor_file=None)

    with pytest.raises(ControllerError):
        client.apply(make_envelope())

    assert fake.calls() == []
    assert list(project_root.iterdir()) == []
    # The same actor-less client still serves read-only calls.
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps({"revision": 2}), verb="snapshot")
    assert client.snapshot(workflow_id="workflow-a") == {"revision": 2}
    assert fake.verbs() == ["contract", "snapshot"]


# Shared subprocess boundary


@EVERY_VERB
def test_call_raises_timeout_when_controller_outlives_timeout(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    verb: str,
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(sleep=SLOW_SECONDS, verb=verb)
    client = make_client(fake, project_root, actor_file=actor_file, timeout_seconds=1)
    started = time.monotonic()

    with pytest.raises(ControllerTimeoutError):
        CALL_BY_VERB[verb](client)

    assert time.monotonic() - started < TIMEOUT_BUDGET
    assert fake.verbs() == (["contract"] if verb == "contract" else ["contract", verb])
    # A reported timeout must not leave the controller running behind it.
    assert process_ended(fake.call_for(verb)["pid"])


def test_call_waits_up_to_configured_timeout_not_a_fixed_one(
    fake: FakeController, project_root: Path
) -> None:
    # A slow controller inside a generous timeout is a success, not a timeout.
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps({"revision": 9}), sleep=3, verb="snapshot")
    client = make_client(fake, project_root, timeout_seconds=10)

    assert client.snapshot(workflow_id="workflow-a") == {"revision": 9}
    assert fake.verbs() == ["contract", "snapshot"]


@EVERY_VERB
def test_call_rejects_stdout_over_output_bound(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    verb: str,
) -> None:
    # The bound admits the negotiation answer exactly, and every padded answer
    # is well formed for its verb, so only the bound can reject it.
    bound = len(CONTRACT_ANSWER.encode())
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(oversized_answer(verb, "x" * bound), verb=verb)
    client = make_client(
        fake, project_root, actor_file=actor_file, max_output_bytes=bound
    )

    with pytest.raises(ControllerOutputError):
        CALL_BY_VERB[verb](client)

    # The verb's own hop is what the bound rejected, not the negotiation hop.
    assert fake.verbs()[-1] == verb


@pytest.mark.parametrize(
    ("slack", "accepted"),
    [(1, True), (0, True), (-1, False)],
    ids=["under", "at-bound", "one-over"],
)
def test_snapshot_output_bound_admits_output_up_to_the_limit(
    fake: FakeController, project_root: Path, slack: int, accepted: bool
) -> None:
    # The payload is padded past the negotiation answer, so the limit under
    # test still leaves the contract hop room to pass.
    payload = {"revision": 12, "phase": "build", "pad": "x" * len(CONTRACT_ANSWER)}
    text = json.dumps(payload)
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(text, verb="snapshot")
    limit = len(text.encode()) + slack
    client = make_client(fake, project_root, max_output_bytes=limit)

    if accepted:
        assert client.snapshot(workflow_id="workflow-a") == payload
    else:
        with pytest.raises(ControllerOutputError):
            client.snapshot(workflow_id="workflow-a")


@EVERY_VERB
@pytest.mark.parametrize(
    "stdout", ["{not json", "", '{"revision": 3'], ids=["garbage", "empty", "cut"]
)
def test_call_rejects_unparseable_stdout_on_zero_exit(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    verb: str,
    stdout: str,
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(stdout, verb=verb)

    with pytest.raises(ControllerOutputError):
        CALL_BY_VERB[verb](make_client(fake, project_root, actor_file=actor_file))


@EVERY_VERB
@pytest.mark.parametrize("exit_code", [1, 7])
def test_call_surfaces_stderr_when_controller_exits_nonzero(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    verb: str,
    exit_code: int,
) -> None:
    detail = f"lease store locked (code {exit_code})"
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(
        stderr=f"controller failed: {detail}\n", exit_code=exit_code, verb=verb
    )

    with pytest.raises(ControllerError) as caught:
        CALL_BY_VERB[verb](make_client(fake, project_root, actor_file=actor_file))

    assert not isinstance(caught.value, ControllerTimeoutError)
    assert not isinstance(caught.value, ControllerOutputError)
    assert detail in str(caught.value)


@pytest.mark.parametrize(
    "ack",
    ['{"ok": true, "revision": 5', '{"ok": true, "revision": 5}\n'],
    ids=["partial-line", "complete-line"],
)
def test_apply_never_returns_result_when_ack_precedes_timeout(
    fake: FakeController, project_root: Path, actor_file: Path, ack: str
) -> None:
    # lost_ack_preserved: output written before a timeout kill is not an ack,
    # and a retry after the lost acknowledgement resends the same request.
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(ack, sleep=SLOW_SECONDS, verb="apply")
    client = make_client(fake, project_root, actor_file=actor_file, timeout_seconds=1)
    envelope = make_envelope()

    for _ in range(2):
        outcome: object = None
        with pytest.raises((ControllerTimeoutError, ControllerOutputError)):
            outcome = client.apply(envelope)
        assert not isinstance(outcome, ApplyResult)
        assert outcome is None

    assert fake.verbs() == ["contract", "apply", "apply"]
    first, retry = [call for call in fake.calls() if call["verb"] == "apply"]
    assert json.loads(first["request"]) == envelope_as_json(envelope)
    assert json.loads(retry["request"]) == json.loads(first["request"])
    assert not request_path(first).exists()
    assert not request_path(retry).exists()


# The bound has to admit the negotiation answer, so the oversized failure pads
# past that answer instead of past a bare 32 bytes.
OUTPUT_BOUND = len(CONTRACT_ANSWER.encode()) + 32
CANARY_FAILURES: dict[str, dict[str, Any]] = {
    "nonzero-exit": {"stderr": "actor rejected\n", "exit_code": 3},
    "timeout": {"sleep": SLOW_SECONDS},
    "malformed-output": {"stdout": "{not json"},
    "oversized-output": {"stdout": json.dumps({"padding": "x" * OUTPUT_BOUND})},
}


@pytest.mark.parametrize("failure", list(CANARY_FAILURES))
def test_apply_errors_never_expose_actor_file_contents(
    fake: FakeController, project_root: Path, actor_file: Path, failure: str
) -> None:
    assert CANARY in actor_file.read_text(encoding="utf-8")
    assert CANARY not in str(actor_file)
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(**CANARY_FAILURES[failure], verb="apply")
    client = make_client(
        fake,
        project_root,
        actor_file=actor_file,
        timeout_seconds=1,
        max_output_bytes=OUTPUT_BOUND,
    )

    with pytest.raises(ControllerError) as caught:
        client.apply(make_envelope())

    for error in exception_chain(caught.value):
        assert CANARY not in str(error)
        assert CANARY not in repr(error)
    assert fake.verbs() == ["contract", "apply"]
    argv = fake.call_for("apply")["argv"]
    assert argv[argv.index("--actor-file") + 1] == str(actor_file)


def test_argv_reaches_controller_verbatim_without_shell(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    hostile = "$(touch pwned) `touch pwned`; touch pwned | * > pwned"
    config = ControllerConfig(
        argv=(*fake.argv, hostile),
        contract_bundle=BUNDLE,
        actor_file=None,
        project_root=project_root,
    )
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps({"revision": 1}), verb="snapshot")

    snapshot = ControllerClient(config).snapshot(workflow_id="workflow-a")

    assert snapshot == {"revision": 1}
    assert fake.verbs() == ["contract", "snapshot"]
    call = fake.call_for("snapshot")
    assert call["argv"] == [
        *fake.child_argv,
        hostile,
        "--json",
        "snapshot",
        "--project-root",
        str(project_root),
    ]
    assert not (project_root / "pwned").exists()
    assert not (tmp_path / "pwned").exists()
