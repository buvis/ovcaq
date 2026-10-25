from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from pathlib import Path

import pytest
from tests.workflow_client.conftest import (
    BUNDLE,
    CALL_BY_VERB,
    CANARY,
    EVERY_CALL,
    EVERY_VERB,
    FIXTURE,
    SLOW_SECONDS,
    TIMEOUT_BUDGET,
    FakeController,
    broken_program,
    call_contract,
    call_snapshot,
    exception_chain,
    hides_secret,
    live_contract,
    make_client,
    make_envelope,
    marks_truncation,
    process_ended,
    request_path,
    secret_fragments,
    write_actor_file,
)

from ovcaq.workflow_client import (
    MAX_STDERR_TAIL_CHARS,
    ApplyOutcomeUnknownError,
    ControllerClient,
    ControllerConfig,
    ControllerError,
    ControllerOutputError,
    ControllerTimeoutError,
)

# 5. Typed spawn failures


@EVERY_CALL
@pytest.mark.parametrize("kind", ["missing", "directory", "not-executable"])
def test_call_raises_controller_error_when_the_program_cannot_run(
    project_root: Path,
    actor_file: Path,
    tmp_path: Path,
    kind: str,
    call: Callable[[ControllerClient], object],
) -> None:
    program = broken_program(tmp_path, kind)
    client = ControllerClient(
        ControllerConfig(
            argv=(str(program),),
            contract_bundle=BUNDLE,
            actor_file=actor_file,
            project_root=project_root,
        )
    )

    with pytest.raises(ControllerError) as caught:
        call(client)

    assert not isinstance(caught.value, OSError)
    assert str(program) in str(caught.value)
    assert list(project_root.iterdir()) == []


@EVERY_CALL
def test_call_raises_controller_error_when_project_root_does_not_exist(
    fake: FakeController,
    actor_file: Path,
    tmp_path: Path,
    call: Callable[[ControllerClient], object],
) -> None:
    fake.respond(json.dumps(live_contract()), verb="contract")
    client = make_client(fake, tmp_path / "absent root", actor_file=actor_file)

    with pytest.raises(ControllerError) as caught:
        call(client)

    assert not isinstance(caught.value, OSError)


# 6. Both captured streams are bounded, before the exit status


@pytest.mark.parametrize("exit_code", [0, 3], ids=["zero-exit", "nonzero-exit"])
def test_contract_rejects_stderr_over_the_output_bound(
    fake: FakeController, project_root: Path, exit_code: int
) -> None:
    live = json.dumps(live_contract())
    limit = len(live.encode()) + 16
    fake.respond(live, stderr="e" * (limit + 500), exit_code=exit_code, verb="contract")

    with pytest.raises(ControllerOutputError):
        make_client(fake, project_root, max_output_bytes=limit).contract()


def test_contract_rejects_oversized_stdout_even_on_a_nonzero_exit(
    fake: FakeController, project_root: Path
) -> None:
    fake.respond(
        "x" * 400, stderr="controller failed: short\n", exit_code=3, verb="contract"
    )

    with pytest.raises(ControllerOutputError):
        make_client(fake, project_root, max_output_bytes=64).contract()


LARGE_BOUND = 1 << 20


def test_contract_accepts_a_large_payload_under_the_configured_output_bound(
    fake: FakeController, project_root: Path
) -> None:
    # A generously configured client must not apply a smaller hidden bound.
    vendor = [f"vendor.operation-{index:05d}" for index in range(3000)]
    live = live_contract(operations=[*FIXTURE["operations"], *vendor])
    text = json.dumps(live)
    assert len(text.encode()) > 64 * 1024
    fake.respond(text, verb="contract")

    contract = make_client(fake, project_root, max_output_bytes=LARGE_BOUND).contract()

    assert contract.operations >= frozenset(FIXTURE["operations"])
    assert vendor[-1] in contract.operations


def test_snapshot_accepts_a_large_payload_under_the_configured_output_bound(
    fake: FakeController, project_root: Path
) -> None:
    payload = {"workflow_id": "workflow-a", "revision": 7, "log": ["n" * 64] * 1024}
    text = json.dumps(payload)
    assert len(text.encode()) > 64 * 1024
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(text, verb="snapshot")

    client = make_client(fake, project_root, max_output_bytes=LARGE_BOUND)

    assert client.snapshot(workflow_id="workflow-a") == payload


# 7. The nonzero-exit detail is a bounded tail


@EVERY_VERB
def test_nonzero_exit_message_keeps_only_a_marked_tail_of_long_stderr(
    fake: FakeController, project_root: Path, tmp_path: Path, verb: str
) -> None:
    assert isinstance(MAX_STDERR_TAIL_CHARS, int)
    assert MAX_STDERR_TAIL_CHARS > 0
    head = "EARLIEST-LINE-AAAA"
    stderr = f"{head}\n{'f' * (MAX_STDERR_TAIL_CHARS * 2)}\nLATEST-LINE-ZZZZ\n"
    limit = len(stderr.encode()) + 1024
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(stderr=stderr, exit_code=5, verb=verb)
    client = make_client(
        fake,
        project_root,
        actor_file=write_actor_file(tmp_path, f"actor-{verb}.json"),
        max_output_bytes=limit,
    )

    with pytest.raises(ControllerError) as caught:
        CALL_BY_VERB[verb](client)

    message = str(caught.value)
    assert stderr.strip()[-MAX_STDERR_TAIL_CHARS:] in message
    assert head not in message
    assert len(message) <= 4 * MAX_STDERR_TAIL_CHARS + 500
    assert marks_truncation(message)


def test_nonzero_exit_message_keeps_short_stderr_whole_and_unmarked(
    fake: FakeController, project_root: Path
) -> None:
    detail = "lease store locked by another writer"
    assert len(detail) < MAX_STDERR_TAIL_CHARS
    fake.respond(stderr=f"controller failed: {detail}\n", exit_code=5, verb="contract")

    with pytest.raises(ControllerError) as caught:
        make_client(fake, project_root).contract()

    message = str(caught.value)
    assert detail in message
    assert not marks_truncation(message)


# 8. Actor-secret redaction


@pytest.mark.parametrize("flavor", ["plain", "json"])
def test_apply_error_hides_an_actor_secret_echoed_by_the_controller(
    fake: FakeController, project_root: Path, tmp_path: Path, flavor: str
) -> None:
    actor = write_actor_file(tmp_path, f"actor-{flavor}", secret=CANARY, flavor=flavor)
    # The marker sits right before the secret, so even a short kept tail holds it.
    detail = "stale:"
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(
        stderr=f"rejected lease as {detail} {CANARY}\n", exit_code=3, verb="apply"
    )

    with pytest.raises(ControllerError) as caught:
        make_client(fake, project_root, actor_file=actor).apply(make_envelope())

    for error in exception_chain(caught.value):
        for text in (str(error), repr(error)):
            assert CANARY not in text
            assert not any(piece in text for piece in secret_fragments(CANARY))
    message = str(caught.value)
    assert "redact" in message.lower()
    # The secret is replaced, not the whole controller detail dropped.
    assert detail in message
    argv = fake.call_for("apply")["argv"]
    assert argv[argv.index("--actor-file") + 1] == str(actor)


def test_apply_error_hides_an_actor_secret_echoed_on_stdout(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(f"not a controller response: {CANARY}\n", verb="apply")

    with pytest.raises(ControllerError) as caught:
        make_client(fake, project_root, actor_file=actor_file).apply(make_envelope())

    assert hides_secret(caught.value, CANARY)


def test_snapshot_error_hides_an_actor_secret_echoed_by_the_controller(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    detail = "lock:"
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(
        stderr=f"lease store {detail} {CANARY}\n", exit_code=4, verb="snapshot"
    )
    client = make_client(fake, project_root, actor_file=actor_file)

    with pytest.raises(ControllerError) as caught:
        client.snapshot(workflow_id="workflow-a")

    assert hides_secret(caught.value, CANARY)
    message = str(caught.value)
    assert "redact" in message.lower()
    assert detail in message


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores file permissions")
def test_apply_still_raises_controller_error_when_actor_file_is_unreadable(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    actor = tmp_path / "unreadable-actor.json"
    actor.write_text(json.dumps({"proof": CANARY}), encoding="utf-8")
    actor.chmod(0o000)
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(stderr="rejected: unusable actor proof\n", exit_code=3, verb="apply")

    with pytest.raises(ControllerError) as caught:
        make_client(fake, project_root, actor_file=actor).apply(make_envelope())

    assert not isinstance(caught.value, OSError)


# 10. A timed-out apply() reports an unknown outcome


@pytest.mark.parametrize("request_id", ["req-0007", "req-0042"])
def test_timed_out_apply_reports_an_unknown_outcome_for_its_request_id(
    fake: FakeController, project_root: Path, actor_file: Path, request_id: str
) -> None:
    fake.respond(json.dumps(live_contract()), verb="contract")
    # The controller leaves a long-lived child of its own in its process group.
    fake.respond(sleep=SLOW_SECONDS, grandchild=SLOW_SECONDS * 3, verb="apply")
    client = make_client(fake, project_root, actor_file=actor_file, timeout_seconds=1)
    started = time.monotonic()

    with pytest.raises(ApplyOutcomeUnknownError) as caught:
        client.apply(make_envelope(request_id=request_id))

    assert time.monotonic() - started < TIMEOUT_BUDGET
    assert isinstance(caught.value, ControllerTimeoutError)
    assert isinstance(caught.value, ControllerError)
    assert caught.value.request_id == request_id
    assert request_id in str(caught.value)
    assert "unknown" in str(caught.value).lower()
    call = fake.call_for("apply")
    assert not request_path(call).exists()
    assert process_ended(call["pid"])
    # Killing the direct child alone would leave this one running.
    assert process_ended(call["grandchild_pid"])
    assert list(project_root.iterdir()) == []


@pytest.mark.parametrize("verb", ["contract", "snapshot"])
def test_timed_out_read_call_is_a_plain_timeout_not_an_unknown_apply_outcome(
    fake: FakeController, project_root: Path, verb: str
) -> None:
    fake.respond(json.dumps(live_contract()), verb="contract")
    fake.respond(sleep=SLOW_SECONDS, verb=verb)
    client = make_client(fake, project_root, timeout_seconds=1)
    started = time.monotonic()

    with pytest.raises(ControllerTimeoutError) as caught:
        call_contract(client) if verb == "contract" else call_snapshot(client)

    assert time.monotonic() - started < TIMEOUT_BUDGET
    assert not isinstance(caught.value, ApplyOutcomeUnknownError)
    assert process_ended(fake.call_for(verb)["pid"])


def test_contract_finishes_and_kills_the_group_when_a_grandchild_holds_the_pipes(
    fake: FakeController, project_root: Path
) -> None:
    # The controller exits at once but leaves a long-sleeping grandchild holding
    # its stdout and stderr write ends, so neither pipe ever reaches EOF by
    # itself.
    fake.respond(
        json.dumps(live_contract()),
        verb="contract",
        grandchild=SLOW_SECONDS * 3,
        grandchild_inherits=True,
    )
    client = make_client(fake, project_root, timeout_seconds=1)
    started = time.monotonic()

    try:
        client.contract()
    except ControllerError:
        # Both terminal paths are legitimate here and the winner is a race: a
        # ControllerTimeoutError when the readers never saw EOF, or a plain
        # successful parse. What this test pins is that the call returns control
        # and that the grandchild is dead, not which path won. Any other
        # exception type fails the test.
        pass

    assert time.monotonic() - started < TIMEOUT_BUDGET
    assert process_ended(fake.call_for("contract")["grandchild_pid"])
