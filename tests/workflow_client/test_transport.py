from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

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

BUNDLE = Path(__file__).parents[1] / "fixtures" / "workflow" / "controller-v1.json"
# Synthetic canary placed in the actor file's contents, never in its path.
CANARY = "super-secret-credential-xyz"
# The fake sleeps far longer than any timeout used here, so a timeout that
# fires must fire well inside TIMEOUT_BUDGET.
SLOW_SECONDS = 10
TIMEOUT_BUDGET = 5.0

# Fake controller: records its argv, cwd, pid and any --request file, then answers
# with the stdout, stderr, delay and exit code from the spec file in argv[1].
FAKE_CONTROLLER = """\
import json
import os
import sys
import time
from pathlib import Path

spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
record = {"argv": sys.argv, "cwd": os.getcwd(), "pid": os.getpid()}
if "--request" in sys.argv:
    request = Path(sys.argv[sys.argv.index("--request") + 1])
    record["request"] = request.read_text(encoding="utf-8")
    record["request_mode"] = request.stat().st_mode & 0o777
with open(spec["log"], "a", encoding="utf-8") as log:
    log.write(json.dumps(record) + "\\n")
sys.stdout.write(spec["stdout"])
sys.stdout.flush()
sys.stderr.write(spec["stderr"])
sys.stderr.flush()
time.sleep(spec["sleep"])
sys.exit(spec["exit"])
"""


@dataclass(frozen=True)
class FakeController:
    script: Path
    spec: Path
    log: Path

    @property
    def argv(self) -> tuple[str, ...]:
        return (sys.executable, str(self.script), str(self.spec))

    @property
    def child_argv(self) -> list[str]:
        """The controller's own sys.argv before the client's arguments."""
        return [str(self.script), str(self.spec)]

    def respond(
        self,
        stdout: str = "",
        *,
        stderr: str = "",
        sleep: float = 0,
        exit_code: int = 0,
    ) -> None:
        spec = {
            "log": str(self.log),
            "stdout": stdout,
            "stderr": stderr,
            "sleep": sleep,
            "exit": exit_code,
        }
        self.spec.write_text(json.dumps(spec), encoding="utf-8")

    def calls(self) -> list[dict[str, Any]]:
        if not self.log.exists():
            return []
        lines = self.log.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines]


@pytest.fixture
def fake(tmp_path: Path) -> FakeController:
    directory = tmp_path / "fake controller"
    directory.mkdir()
    script = directory / "controller.py"
    script.write_text(FAKE_CONTROLLER, encoding="utf-8")
    controller = FakeController(script, directory / "spec.json", tmp_path / "calls.log")
    controller.respond()
    return controller


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project root"
    root.mkdir()
    return root


@pytest.fixture
def actor_file(tmp_path: Path) -> Path:
    path = tmp_path / "actor.json"
    path.write_text(json.dumps({"actor_id": "actor-a", "proof": CANARY}), "utf-8")
    path.chmod(0o600)
    return path


def make_client(
    fake: FakeController,
    project_root: Path,
    *,
    actor_file: Path | None = None,
    bundle: Path = BUNDLE,
    **overrides: Any,
) -> ControllerClient:
    config = ControllerConfig(
        argv=fake.argv,
        contract_bundle=bundle,
        actor_file=actor_file,
        project_root=project_root,
        **overrides,
    )
    return ControllerClient(config)


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


def envelope_as_json(envelope: MutationEnvelope) -> dict[str, Any]:
    return {
        "protocol_major": envelope.protocol_major,
        "operation": envelope.operation,
        "request_id": envelope.request_id,
        "expected_revision": envelope.expected_revision,
        "project_id": envelope.project_id,
        "workflow_id": envelope.workflow_id,
        "actor_id": envelope.actor_id,
        "lease_epoch": envelope.lease_epoch,
        "payload": dict(envelope.payload),
    }


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


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


def request_path(call: dict[str, Any]) -> Path:
    argv = call["argv"]
    return Path(call["cwd"]) / argv[argv.index("--request") + 1]


def same_directory(left: str | Path, right: Path) -> bool:
    return Path(left).resolve() == right.resolve()


def process_ended(pid: int, *, within: float = 3.0) -> bool:
    """Poll until no process has pid, allowing for kill and reap latency."""
    deadline = time.monotonic() + within
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        if time.monotonic() > deadline:
            return False
        time.sleep(0.05)


def exception_chain(error: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and current not in chain:
        chain.append(current)
        current = current.__cause__ or current.__context__
    return chain


def call_contract(client: ControllerClient) -> object:
    return client.contract()


def call_snapshot(client: ControllerClient) -> object:
    return client.snapshot(workflow_id="workflow-a")


def call_apply(client: ControllerClient) -> object:
    return client.apply(make_envelope())


EVERY_CALL = pytest.mark.parametrize(
    "call",
    [call_contract, call_snapshot, call_apply],
    ids=["contract", "snapshot", "apply"],
)


# contract()


@pytest.mark.parametrize("variant", [False, True], ids=["fixture", "variant"])
def test_contract_runs_contract_verb_in_project_root_and_maps_bundle(
    fake: FakeController, project_root: Path, tmp_path: Path, variant: bool
) -> None:
    bundle = write_variant_bundle(tmp_path) if variant else BUNDLE
    pinned = load_json(bundle)
    # The live controller agrees on both digests but reports other fields the
    # bundle does not, so only the live answer can produce these values.
    live = {
        **pinned,
        "package_version": pinned["package_version"] + "+live",
        "operations": [*pinned["operations"], "workflow.live-only"],
        "capabilities": [*pinned["capabilities"], "live-only"],
    }
    fake.respond(json.dumps(live))

    contract = make_client(fake, project_root, bundle=bundle).contract()

    assert contract == expected_contract(live)
    assert contract.package_version == live["package_version"]
    assert "workflow.live-only" in contract.operations
    assert "live-only" in contract.capabilities
    assert isinstance(contract.operations, frozenset)
    assert isinstance(contract.capabilities, frozenset)
    [call] = fake.calls()
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
    fake.respond(json.dumps({**data, field: reported}))

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root).contract()

    assert reported in str(caught.value)
    assert pinned in str(caught.value)


def test_contract_compares_against_configured_bundle(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    # The live controller matches the repo fixture, but the client is pinned
    # to a different bundle, so the pin must win.
    fake.respond(BUNDLE.read_text(encoding="utf-8"))

    with pytest.raises(IncompatibleContractError):
        make_client(
            fake, project_root, bundle=write_variant_bundle(tmp_path)
        ).contract()

    assert len(fake.calls()) == 1


@pytest.mark.parametrize("major", [0, 2, 99])
def test_contract_rejects_incompatible_protocol_major(
    fake: FakeController, project_root: Path, major: int
) -> None:
    assert major != PROTOCOL_MAJOR
    fake.respond(json.dumps({**load_json(BUNDLE), "protocol_major": major}))

    with pytest.raises(IncompatibleContractError):
        make_client(fake, project_root).contract()

    assert len(fake.calls()) == 1


def test_contract_is_cached_per_client_instance_only(
    fake: FakeController, project_root: Path
) -> None:
    data = load_json(BUNDLE)
    fake.respond(json.dumps(data))
    client = make_client(fake, project_root)

    first = client.contract()
    second = client.contract()

    assert first == second == expected_contract(data)
    assert len(fake.calls()) == 1

    fresh = make_client(fake, project_root)
    assert fresh.contract() == first
    assert len(fake.calls()) == 2

    # A drifted controller cannot reach a validated instance, but a new
    # instance re-validates and refuses it.
    fake.respond(json.dumps({**data, "schema_digest": "0" * 64}))
    assert client.contract() == first
    assert len(fake.calls()) == 2
    with pytest.raises(IncompatibleContractError):
        make_client(fake, project_root).contract()
    assert len(fake.calls()) == 3


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
    # Stderr noise on a zero exit is not a failure.
    fake.respond(json.dumps(payload), stderr="warning: lease renewal slow\n")

    snapshot = make_client(fake, project_root).snapshot(workflow_id="workflow-a")

    assert snapshot == payload
    [call] = fake.calls()
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
    fake.respond(stdout)

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
    fake.respond(stderr="rejected: stale revision\n", exit_code=4)

    with pytest.raises(ControllerError):
        make_client(fake, project_root, actor_file=actor_file).apply(envelope)

    [call] = fake.calls()
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
    fake.respond(json.dumps({"ok": True, "revision": 6}))
    client = make_client(fake, project_root, actor_file=actor_file)

    for envelope in envelopes:
        with contextlib.suppress(ControllerError):
            client.apply(envelope)

    calls = fake.calls()
    assert len(calls) == 2
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
    # A structured rejection on a zero exit is a normal return, not an error.
    fake.respond(json.dumps(response) + "\n")

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
    [call] = fake.calls()
    assert not request_path(call).exists()


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
    fake.respond(json.dumps(MALFORMED_APPLY_RESPONSES[malformed]))
    outcome: object = None

    with pytest.raises(ControllerOutputError):
        outcome = make_client(fake, project_root, actor_file=actor_file).apply(
            make_envelope()
        )

    assert outcome is None
    [call] = fake.calls()
    assert not request_path(call).exists()


def test_apply_without_actor_file_refuses_before_spawning(
    fake: FakeController, project_root: Path
) -> None:
    client = make_client(fake, project_root, actor_file=None)

    with pytest.raises(ControllerError):
        client.apply(make_envelope())

    assert fake.calls() == []
    assert list(project_root.iterdir()) == []
    # The same actor-less client still serves read-only calls.
    fake.respond(json.dumps({"revision": 2}))
    assert client.snapshot(workflow_id="workflow-a") == {"revision": 2}
    assert len(fake.calls()) == 1


# Shared subprocess boundary


@EVERY_CALL
def test_call_raises_timeout_when_controller_outlives_timeout(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    call: Callable[[ControllerClient], object],
) -> None:
    fake.respond(sleep=SLOW_SECONDS)
    client = make_client(fake, project_root, actor_file=actor_file, timeout_seconds=1)
    started = time.monotonic()

    with pytest.raises(ControllerTimeoutError):
        call(client)

    assert time.monotonic() - started < TIMEOUT_BUDGET
    [record] = fake.calls()
    # A reported timeout must not leave the controller running behind it.
    assert process_ended(record["pid"])


def test_call_waits_up_to_configured_timeout_not_a_fixed_one(
    fake: FakeController, project_root: Path
) -> None:
    # A slow controller inside a generous timeout is a success, not a timeout.
    fake.respond(json.dumps({"revision": 9}), sleep=3)
    client = make_client(fake, project_root, timeout_seconds=10)

    assert client.snapshot(workflow_id="workflow-a") == {"revision": 9}
    assert len(fake.calls()) == 1


@EVERY_CALL
def test_call_rejects_stdout_over_output_bound(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    call: Callable[[ControllerClient], object],
) -> None:
    # A valid contract, far longer than 16 bytes: only the bound can reject it.
    fake.respond(BUNDLE.read_text(encoding="utf-8"))
    client = make_client(fake, project_root, actor_file=actor_file, max_output_bytes=16)

    with pytest.raises(ControllerOutputError):
        call(client)


@pytest.mark.parametrize(
    ("slack", "accepted"),
    [(1, True), (0, True), (-1, False)],
    ids=["under", "at-bound", "one-over"],
)
def test_snapshot_output_bound_admits_output_up_to_the_limit(
    fake: FakeController, project_root: Path, slack: int, accepted: bool
) -> None:
    payload = {"revision": 12, "phase": "build"}
    text = json.dumps(payload)
    fake.respond(text)
    limit = len(text.encode()) + slack
    client = make_client(fake, project_root, max_output_bytes=limit)

    if accepted:
        assert client.snapshot(workflow_id="workflow-a") == payload
    else:
        with pytest.raises(ControllerOutputError):
            client.snapshot(workflow_id="workflow-a")


@EVERY_CALL
@pytest.mark.parametrize(
    "stdout", ["{not json", "", '{"revision": 3'], ids=["garbage", "empty", "cut"]
)
def test_call_rejects_unparseable_stdout_on_zero_exit(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    call: Callable[[ControllerClient], object],
    stdout: str,
) -> None:
    fake.respond(stdout)

    with pytest.raises(ControllerOutputError):
        call(make_client(fake, project_root, actor_file=actor_file))


@EVERY_CALL
@pytest.mark.parametrize("exit_code", [1, 7])
def test_call_surfaces_stderr_when_controller_exits_nonzero(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    call: Callable[[ControllerClient], object],
    exit_code: int,
) -> None:
    detail = f"lease store locked (code {exit_code})"
    fake.respond(stderr=f"controller failed: {detail}\n", exit_code=exit_code)

    with pytest.raises(ControllerError) as caught:
        call(make_client(fake, project_root, actor_file=actor_file))

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
    # lost_ack_preserved: output written before a timeout kill is not an ack.
    fake.respond(ack, sleep=SLOW_SECONDS)
    client = make_client(fake, project_root, actor_file=actor_file, timeout_seconds=1)
    outcome: object = None

    with pytest.raises((ControllerTimeoutError, ControllerOutputError)):
        outcome = client.apply(make_envelope())

    assert not isinstance(outcome, ApplyResult)
    assert outcome is None
    [call] = fake.calls()
    assert not request_path(call).exists()


CANARY_FAILURES: dict[str, dict[str, Any]] = {
    "nonzero-exit": {"stderr": "actor rejected\n", "exit_code": 3},
    "timeout": {"sleep": SLOW_SECONDS},
    "malformed-output": {"stdout": "{not json"},
    "oversized-output": {"stdout": json.dumps({"padding": "x" * 64})},
}


@pytest.mark.parametrize("failure", list(CANARY_FAILURES))
def test_apply_errors_never_expose_actor_file_contents(
    fake: FakeController, project_root: Path, actor_file: Path, failure: str
) -> None:
    assert CANARY in actor_file.read_text(encoding="utf-8")
    assert CANARY not in str(actor_file)
    fake.respond(**CANARY_FAILURES[failure])
    client = make_client(
        fake,
        project_root,
        actor_file=actor_file,
        timeout_seconds=1,
        max_output_bytes=32,
    )

    with pytest.raises(ControllerError) as caught:
        client.apply(make_envelope())

    for error in exception_chain(caught.value):
        assert CANARY not in str(error)
        assert CANARY not in repr(error)
    [call] = fake.calls()
    argv = call["argv"]
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
    fake.respond(json.dumps({"revision": 1}))

    snapshot = ControllerClient(config).snapshot(workflow_id="workflow-a")

    assert snapshot == {"revision": 1}
    [call] = fake.calls()
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
