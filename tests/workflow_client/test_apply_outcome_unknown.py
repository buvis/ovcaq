from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest
from tests.workflow_client.conftest import (
    ACCEPTED_APPLY,
    REJECTED_APPLY,
    SLOW_SECONDS,
    TIMEOUT_BUDGET,
    FakeController,
    envelope_as_json,
    live_contract,
    make_client,
    make_envelope,
)

from ovcaq.workflow_client import (
    ApplyOutcomeUnknownError,
    ControllerError,
    ControllerOutputError,
    ControllerTimeoutError,
)

# Negotiation is mandatory, so every apply/snapshot call spends a contract hop
# first; this answer satisfies the pinned fixture bundle.
CONTRACT_ANSWER = json.dumps(live_contract())


def oversized_apply_answer(bound: int) -> str:
    """A well-formed apply response padded past the output bound."""
    return json.dumps({**ACCEPTED_APPLY, "result": {"pad": "x" * bound}})


def oversized_snapshot_answer(bound: int) -> str:
    """A well-formed snapshot response padded past the output bound."""
    return json.dumps({"revision": 3, "pad": "x" * bound})


def read_flag(argv: list[str], flag: str) -> str:
    """The value the controller received for flag, so a dropped flag fails."""
    assert flag in argv, f"{flag} missing from {argv}"
    return argv[argv.index(flag) + 1]


def write_launcher(fake: FakeController, tmp_path: Path) -> Path:
    """An executable copy of the fake, reachable as argv[0] until a test breaks it."""
    path = tmp_path / "controller-launcher"
    path.write_text(
        f"#!{sys.executable}\n{fake.script.read_text(encoding='utf-8')}",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def break_launcher(program: Path, kind: str) -> None:
    """Make an already-working program unlaunchable, between two hops."""
    if kind == "missing":
        program.unlink()
    else:
        program.chmod(0o644)


class LaunchedController(FakeController):
    """A fake reached through its own program file, which a test can break."""

    def __init__(self, fake: FakeController, program: Path) -> None:
        super().__init__(fake.script, fake.spec, fake.log, dict(fake.answers))
        self.program = program

    @property
    def argv(self) -> tuple[str, ...]:
        return (str(self.program), str(self.spec))


# A controller that died after spawning: it may have committed before the ack
# never arrived. Two request ids, two exit codes and two stdout shapes, so a
# hardcoded id, a hardcoded exit code or an empty-output shortcut fails.
CRASHED_AFTER_COMMIT = [
    ("req-crash-after-commit", 1, ""),
    ("req-crash", 17, '{"ok": tr'),
]

# A response that is syntactically JSON but breaks the ApplyResult contract,
# one field at a time, so a presence-only check on "ok" cannot pass.
MALFORMED_APPLY = [
    pytest.param(
        {key: value for key, value in ACCEPTED_APPLY.items() if key != "ok"},
        id="ok-absent",
    ),
    pytest.param({**ACCEPTED_APPLY, "ok": "yes"}, id="ok-not-bool"),
    pytest.param({**ACCEPTED_APPLY, "revision": "six"}, id="revision-not-int"),
    pytest.param({**ACCEPTED_APPLY, "result": [1, 2]}, id="result-not-dict"),
    pytest.param({**ACCEPTED_APPLY, "retryable": None}, id="retryable-not-bool"),
]

# A snapshot payload no constant return value can guess.
SNAPSHOT_PAYLOAD = {"revision": 9, "workflow_id": "workflow-a", "phase": "review"}


# apply() must turn every post-spawn, commit-ambiguous failure into
# ApplyOutcomeUnknownError, never the plain error class.


def test_apply_raises_outcome_unknown_on_output_bound_overrun(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    bound = len(CONTRACT_ANSWER.encode())
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(oversized_apply_answer(bound), verb="apply")
    client = make_client(
        fake, project_root, actor_file=actor_file, max_output_bytes=bound
    )
    envelope = make_envelope(request_id="req-bound-overrun")

    with pytest.raises(ApplyOutcomeUnknownError) as caught:
        client.apply(envelope)

    assert caught.value.request_id == "req-bound-overrun"
    assert "req-bound-overrun" in str(caught.value)
    assert isinstance(caught.value.__cause__, ControllerOutputError)
    assert not isinstance(caught.value, ControllerOutputError)
    assert fake.verbs() == ["contract", "apply"]


def test_apply_raises_outcome_unknown_on_non_json_stdout_after_zero_exit(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond("{not json", verb="apply")
    client = make_client(fake, project_root, actor_file=actor_file)
    envelope = make_envelope(request_id="req-non-json")

    with pytest.raises(ApplyOutcomeUnknownError) as caught:
        client.apply(envelope)

    assert caught.value.request_id == "req-non-json"
    assert "req-non-json" in str(caught.value)
    assert isinstance(caught.value.__cause__, ControllerOutputError)
    assert not isinstance(caught.value, ControllerOutputError)
    assert fake.verbs() == ["contract", "apply"]


@pytest.mark.parametrize("response", MALFORMED_APPLY)
def test_apply_raises_outcome_unknown_on_malformed_response(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    response: dict[str, object],
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps(response), verb="apply")
    client = make_client(fake, project_root, actor_file=actor_file)
    envelope = make_envelope(request_id="req-malformed")

    with pytest.raises(ApplyOutcomeUnknownError) as caught:
        client.apply(envelope)

    assert caught.value.request_id == "req-malformed"
    assert "req-malformed" in str(caught.value)
    assert not isinstance(caught.value, ControllerOutputError)
    assert fake.verbs() == ["contract", "apply"]


def test_apply_raises_outcome_unknown_on_timeout(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(sleep=SLOW_SECONDS, verb="apply")
    client = make_client(fake, project_root, actor_file=actor_file, timeout_seconds=1)
    envelope = make_envelope(request_id="req-timeout")
    started = time.monotonic()

    with pytest.raises(ApplyOutcomeUnknownError) as caught:
        client.apply(envelope)

    assert time.monotonic() - started < TIMEOUT_BUDGET
    assert caught.value.request_id == "req-timeout"
    assert "req-timeout" in str(caught.value)
    assert isinstance(caught.value.__cause__, ControllerTimeoutError)
    assert fake.verbs() == ["contract", "apply"]


@pytest.mark.parametrize(
    ("request_id", "exit_code", "partial_stdout"),
    CRASHED_AFTER_COMMIT,
    ids=["silent-death", "truncated-ack"],
)
def test_apply_nonzero_exit_after_spawn_is_outcome_unknown(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    request_id: str,
    exit_code: int,
    partial_stdout: str,
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(
        partial_stdout,
        verb="apply",
        stderr="committed, then crashed",
        exit_code=exit_code,
    )
    client = make_client(fake, project_root, actor_file=actor_file)
    envelope = make_envelope(request_id=request_id)

    with pytest.raises(ApplyOutcomeUnknownError) as caught:
        client.apply(envelope)

    assert caught.value.request_id == request_id
    # The caller has to learn which request to replay and what the controller
    # said before it died.
    assert request_id in str(caught.value)
    assert "committed, then crashed" in str(caught.value)
    assert isinstance(caught.value.__cause__, ControllerError)
    assert fake.verbs() == ["contract", "apply"]
    # The whole envelope must travel to the controller in a private file, with
    # the actor and project the client was configured with.
    call = fake.call_for("apply")
    assert json.loads(call["request"]) == envelope_as_json(envelope)
    assert call["request_mode"] == 0o600
    assert read_flag(call["argv"], "--actor-file") == str(actor_file)
    assert read_flag(call["argv"], "--project-root") == str(project_root)


@pytest.mark.parametrize(
    "response",
    [
        pytest.param(ACCEPTED_APPLY, id="accepted"),
        pytest.param(REJECTED_APPLY, id="rejected"),
    ],
)
def test_apply_zero_exit_with_ack_is_not_outcome_unknown(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    response: dict[str, object],
) -> None:
    """Both acked arms, field by field, so a constant result cannot pass."""
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps(response), verb="apply", exit_code=0)
    client = make_client(fake, project_root, actor_file=actor_file)

    result = client.apply(make_envelope(request_id="req-clean-exit"))

    assert result.ok is response["ok"]
    assert result.revision == response["revision"]
    assert result.result == response["result"]
    assert result.error_code == response["error_code"]
    assert result.retryable is response["retryable"]
    assert fake.verbs() == ["contract", "apply"]


# A controller that could not be launched never ran, so the outcome is known:
# the mutation did not happen.


@pytest.mark.parametrize("kind", ["missing", "not-executable"])
def test_apply_launch_failure_is_plain_controller_error(
    fake: FakeController,
    project_root: Path,
    actor_file: Path,
    tmp_path: Path,
    kind: str,
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps(ACCEPTED_APPLY), verb="apply")
    controller = LaunchedController(fake, write_launcher(fake, tmp_path))
    client = make_client(controller, project_root, actor_file=actor_file)
    # The contract hop runs while the program still works, so only the apply
    # spawn itself fails to start.
    client.contract()
    break_launcher(controller.program, kind)

    with pytest.raises(ControllerError) as caught:
        client.apply(make_envelope(request_id="req-never-launched"))

    assert isinstance(caught.value, ControllerError)
    assert not isinstance(caught.value, ApplyOutcomeUnknownError)
    assert fake.verbs() == ["contract"]


def test_apply_without_an_actor_file_fails_before_spawning_anything(
    fake: FakeController, project_root: Path
) -> None:
    # Both hops are answerable, so an implementation that negotiates first and
    # only then notices the missing credential records a contract call here.
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps(ACCEPTED_APPLY), verb="apply")
    client = make_client(fake, project_root)

    with pytest.raises(ControllerError) as caught:
        client.apply(make_envelope(request_id="req-no-actor-file"))

    # Nothing ran, so the outcome is known: the mutation did not happen.
    assert not isinstance(caught.value, ApplyOutcomeUnknownError)
    assert fake.verbs() == []


# A non-apply call hitting the same failure modes must keep raising the plain
# error class, never ApplyOutcomeUnknownError, and must report what the
# controller actually said.


def test_snapshot_returns_the_controller_payload(
    fake: FakeController, project_root: Path
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps(SNAPSHOT_PAYLOAD), verb="snapshot")
    client = make_client(fake, project_root)

    snapshot = client.snapshot(workflow_id="workflow-a")

    assert snapshot == SNAPSHOT_PAYLOAD
    assert fake.verbs() == ["contract", "snapshot"]


def test_snapshot_raises_plain_output_error_on_output_bound_overrun(
    fake: FakeController, project_root: Path
) -> None:
    bound = len(CONTRACT_ANSWER.encode())
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(oversized_snapshot_answer(bound), verb="snapshot")
    client = make_client(fake, project_root, max_output_bytes=bound)

    with pytest.raises(ControllerOutputError) as caught:
        client.snapshot(workflow_id="workflow-a")

    assert not isinstance(caught.value, ApplyOutcomeUnknownError)
    assert fake.verbs() == ["contract", "snapshot"]


def test_snapshot_raises_plain_output_error_on_non_json_stdout(
    fake: FakeController, project_root: Path
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond("{not json", verb="snapshot")
    client = make_client(fake, project_root)

    with pytest.raises(ControllerOutputError) as caught:
        client.snapshot(workflow_id="workflow-a")

    assert not isinstance(caught.value, ApplyOutcomeUnknownError)
    assert fake.verbs() == ["contract", "snapshot"]


def test_snapshot_raises_plain_output_error_on_non_dict_response(
    fake: FakeController, project_root: Path
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond("[1, 2]", verb="snapshot")
    client = make_client(fake, project_root)

    with pytest.raises(ControllerOutputError) as caught:
        client.snapshot(workflow_id="workflow-a")

    assert not isinstance(caught.value, ApplyOutcomeUnknownError)
    assert fake.verbs() == ["contract", "snapshot"]


# An unknown outcome is not a timeout: a caller that swallows timeouts must not
# swallow it, because the mutation may already have applied.

# One entry per required trigger, with the wordings that count as naming it.
TRIGGER_WORDINGS = {
    "timeout": ("timeout", "timed out", "times out"),
    "output overrun": ("overrun", "output bound", "output limit", "too much output"),
    "non-JSON response": ("non-json", "not json", "unparseable", "invalid json"),
    "non-dict response": ("non-dict", "not a dict", "non-mapping", "not a mapping"),
    "post-spawn non-zero exit": (
        "non-zero exit",
        "nonzero exit",
        "exits non-zero",
        "exited non-zero",
    ),
}


def test_timeout_base_does_not_catch_unknown_outcome(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    bound = len(CONTRACT_ANSWER.encode())
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(oversized_apply_answer(bound), verb="apply")
    client = make_client(
        fake, project_root, actor_file=actor_file, max_output_bytes=bound
    )
    envelope = make_envelope(request_id="req-overrun-not-timeout")

    with pytest.raises(ApplyOutcomeUnknownError) as caught:
        try:
            client.apply(envelope)
        except ControllerTimeoutError as swallowed:
            pytest.fail(f"a timeout handler swallowed {type(swallowed).__name__}")

    assert caught.value.request_id == "req-overrun-not-timeout"
    assert "req-overrun-not-timeout" in str(caught.value)
    assert issubclass(ApplyOutcomeUnknownError, ControllerError)
    assert not issubclass(ApplyOutcomeUnknownError, ControllerTimeoutError)
    assert fake.verbs() == ["contract", "apply"]


def test_outcome_unknown_docstring_names_every_trigger() -> None:
    doc = (ApplyOutcomeUnknownError.__doc__ or "").lower()

    unnamed = [
        trigger
        for trigger, wordings in TRIGGER_WORDINGS.items()
        if not any(wording in doc for wording in wordings)
    ]

    assert not unnamed, f"docstring does not name {unnamed}: {doc!r}"
