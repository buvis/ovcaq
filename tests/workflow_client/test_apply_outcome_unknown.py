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
    live_contract,
    make_client,
    make_envelope,
)

from ovcaq.workflow_client import (
    ApplyOutcomeUnknownError,
    ControllerOutputError,
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
