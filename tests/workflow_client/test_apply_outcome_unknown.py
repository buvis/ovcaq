from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from tests.workflow_client.conftest import (
    ACCEPTED_APPLY,
    SLOW_SECONDS,
    TIMEOUT_BUDGET,
    FakeController,
    broken_program,
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


class UnlaunchableController(FakeController):
    """A fake whose argv[0] cannot be executed, so the program never starts."""

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
    assert not isinstance(caught.value, ControllerOutputError)
    assert fake.verbs() == ["contract", "apply"]


def test_apply_raises_outcome_unknown_on_malformed_response(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    malformed = {key: value for key, value in ACCEPTED_APPLY.items() if key != "ok"}
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps(malformed), verb="apply")
    client = make_client(fake, project_root, actor_file=actor_file)
    envelope = make_envelope(request_id="req-malformed")

    with pytest.raises(ApplyOutcomeUnknownError) as caught:
        client.apply(envelope)

    assert caught.value.request_id == "req-malformed"
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
    assert isinstance(caught.value, ControllerError)
    assert fake.verbs() == ["contract", "apply"]
    # The id must travel from the envelope to the controller, so the caller can
    # replay the identical request.
    sent = json.loads(fake.call_for("apply")["request"])
    assert sent["request_id"] == request_id


def test_apply_zero_exit_with_ack_is_not_outcome_unknown(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    """The accepting arm of the same shape, so a constant raise cannot pass."""
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond(json.dumps(ACCEPTED_APPLY), verb="apply", exit_code=0)
    client = make_client(fake, project_root, actor_file=actor_file)

    result = client.apply(make_envelope(request_id="req-clean-exit"))

    assert result is not None
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
    client = make_client(
        UnlaunchableController(fake, broken_program(tmp_path, kind)),
        project_root,
        actor_file=actor_file,
    )

    with pytest.raises(ControllerError) as caught:
        client.apply(make_envelope(request_id="req-never-launched"))

    assert not isinstance(caught.value, ApplyOutcomeUnknownError)
    assert fake.verbs() == []


# A non-apply call hitting the same failure modes must keep raising the plain
# error class, never ApplyOutcomeUnknownError.


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
    assert fake.verbs()[-1] == "snapshot"


def test_snapshot_raises_plain_output_error_on_non_json_stdout(
    fake: FakeController, project_root: Path
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond("{not json", verb="snapshot")
    client = make_client(fake, project_root)

    with pytest.raises(ControllerOutputError) as caught:
        client.snapshot(workflow_id="workflow-a")

    assert not isinstance(caught.value, ApplyOutcomeUnknownError)
    assert fake.verbs()[-1] == "snapshot"


def test_snapshot_raises_plain_output_error_on_non_dict_response(
    fake: FakeController, project_root: Path
) -> None:
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond("[1, 2]", verb="snapshot")
    client = make_client(fake, project_root)

    with pytest.raises(ControllerOutputError) as caught:
        client.snapshot(workflow_id="workflow-a")

    assert not isinstance(caught.value, ApplyOutcomeUnknownError)
    assert fake.verbs()[-1] == "snapshot"


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
