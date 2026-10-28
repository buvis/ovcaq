from __future__ import annotations

import builtins
import json
import pathlib
import secrets
from pathlib import Path
from typing import Any

import pytest
from tests.workflow_client.conftest import (
    FakeController,
    live_contract,
    make_client,
    make_envelope,
    marks_truncation,
    secret_fragments,
    write_actor_file,
)

from ovcaq.workflow_client import (
    MAX_STDERR_TAIL_CHARS,
    MIN_SECRET_CHARS,
    REDACTED_MARKER,
    TRUNCATION_MARKER,
    ControllerError,
    IncompatibleContractError,
)

CONTRACT_ANSWER = json.dumps(live_contract())

# Synthetic canaries only; never a real credential. Two distinct long values, so
# a replacement list hardcoded to one of them fails.
LONG_FIRST = "canary-alpha-" + "a" * (MIN_SECRET_CHARS + 40)
LONG_SECOND = "canary-omega-" + "z" * (MIN_SECRET_CHARS + 40)
# Exactly at the threshold: must be masked.
BOUNDARY_TOKEN = "t" * MIN_SECRET_CHARS
# One character below the threshold: must survive. NEAR_MISS_TOKEN is a strict
# prefix and substring of BOUNDARY_TOKEN and SHORT_PREFIX is a strict prefix of
# LONG_SECOND, so prefix or substring matching masks them and fails.
NEAR_MISS_TOKEN = "t" * (MIN_SECRET_CHARS - 1)
SHORT_PREFIX = LONG_SECOND[: MIN_SECRET_CHARS - 1]
# Not valid UTF-8, so a strict decode raises instead of yielding a diagnostic.
INVALID_UTF8 = b"\xff\xfe"
# Prose whose longest word sits between 5 and 7 characters, so a lower
# threshold eats real words and this literal stops matching.
PROSE = "exit 3: denied by remote"
# Multibyte words, all shorter than the threshold, so they must come back
# byte-identical and a different decoder is visible.
MULTIBYTE_PROSE = "échec révisé"
# A credential short enough that token-length masking can never reach it; the
# file holding it is one byte below MIN_SECRET_CHARS.
TINY_SECRET = "zq7xkv"
# Nonsense words, so the controller's own prose cannot be confused with the
# client's own wording in a diagnostic. Both are one character below the
# threshold, so token masking alone never reaches them.
CONTROLLER_PROSE = ("frobniz", "zarquon")


def fresh_secret() -> str:
    """A long token minted at run time, so no literal can be pre-baked.

    token_urlsafe mixes case, digits and punctuation, unlike the canaries.
    """
    return secrets.token_urlsafe(24)


def refuse_file_access(*args: Any, **kwargs: Any) -> Any:
    """Any attempt to open a file during redaction must be visible."""
    raise AssertionError("the redaction path tried to read a file")


def tiny_actor_file(tmp_path: Path) -> Path:
    """An actor file too small to hold a credential masking could reach."""
    path = write_actor_file(tmp_path, "tiny-actor", secret=TINY_SECRET, flavor="plain")
    assert path.stat().st_size < MIN_SECRET_CHARS
    return path


def unmaskable_actor_file(tmp_path: Path, state: str) -> Path:
    """An actor file whose credential token-length masking cannot reach."""
    if state == "tiny-credential":
        return tiny_actor_file(tmp_path)
    if state == "ordinary-name":
        # Nothing but this file's size says the credential is unmaskable.
        path = write_actor_file(tmp_path, "actor.json", secret="zq7", flavor="plain")
        assert path.stat().st_size < MIN_SECRET_CHARS
        return path
    path = tmp_path / "absent-actor.json"
    assert not path.exists()
    return path


def controller_stderr(secret: str) -> str:
    """Controller output that frames a secret with words of its own."""
    return f"{CONTROLLER_PROSE[0]} {secret} {CONTROLLER_PROSE[1]}"


def test_the_published_redaction_constants_keep_their_values() -> None:
    """The thresholds and markers are the contract, not free variables."""
    assert MIN_SECRET_CHARS == 8
    assert REDACTED_MARKER == "<redacted>"
    assert MAX_STDERR_TAIL_CHARS == 512
    assert TRUNCATION_MARKER == "...(truncated) "
    assert marks_truncation(TRUNCATION_MARKER)


def test_redaction_never_reads_actor_file(
    fake: FakeController,
    project_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor_path = write_actor_file(tmp_path, "actor.json", secret=LONG_FIRST)
    client = make_client(fake, project_root, actor_file=actor_path)
    minted = fresh_secret()
    raw = f"proof {LONG_FIRST} minted {minted} id {NEAR_MISS_TOKEN}"

    with monkeypatch.context() as patched:
        patched.setattr(pathlib.Path, "read_bytes", refuse_file_access)
        patched.setattr(pathlib.Path, "open", refuse_file_access)
        patched.setattr(builtins, "open", refuse_file_access)
        redacted = client._redact(raw)

    # A token minted in this process cannot be in any hardcoded list.
    assert redacted == (
        f"proof {REDACTED_MARKER} minted {REDACTED_MARKER} id {NEAR_MISS_TOKEN}"
    )
    assert LONG_FIRST not in redacted
    assert minted not in redacted
    assert not any(piece in redacted for piece in secret_fragments(LONG_FIRST))
    assert not any(piece in redacted for piece in secret_fragments(minted))
    # A short token is ordinary prose and stays legible.
    assert NEAR_MISS_TOKEN in redacted


def test_redacts_long_tokens_when_the_credential_is_below_the_threshold(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    """A credential too short to be collected from the file is not an excuse."""
    actor_path = write_actor_file(
        tmp_path, "short-actor", secret=NEAR_MISS_TOKEN, flavor="plain"
    )
    client = make_client(fake, project_root, actor_file=actor_path)
    minted = fresh_secret()
    raw = f"refused {NEAR_MISS_TOKEN} sent {LONG_SECOND} as {minted}"

    redacted = client._redact(raw)

    assert redacted == (
        f"refused {NEAR_MISS_TOKEN} sent {REDACTED_MARKER} as {REDACTED_MARKER}"
    )
    assert LONG_SECOND not in redacted
    assert minted not in redacted
    assert not any(piece in redacted for piece in secret_fragments(LONG_SECOND))
    assert not any(piece in redacted for piece in secret_fragments(minted))


@pytest.mark.parametrize("state", ["missing", "unreadable"])
def test_redacts_long_tokens_when_the_actor_file_cannot_be_read(
    fake: FakeController, project_root: Path, tmp_path: Path, state: str
) -> None:
    if state == "missing":
        actor_path = tmp_path / "missing-actor.json"
        assert not actor_path.exists()
    else:
        actor_path = write_actor_file(tmp_path, "locked-actor", secret=LONG_FIRST)
        actor_path.chmod(0o000)
    client = make_client(fake, project_root, actor_file=actor_path)
    minted = fresh_secret()
    raw = f"token {LONG_FIRST} minted {minted} id {NEAR_MISS_TOKEN}"

    redacted = client._redact(raw)

    assert redacted == (
        f"token {REDACTED_MARKER} minted {REDACTED_MARKER} id {NEAR_MISS_TOKEN}"
    )
    assert LONG_FIRST not in redacted
    assert minted not in redacted


def test_masks_every_token_at_the_threshold_and_keeps_shorter_ones(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    client = make_client(fake, project_root, actor_file=actor_file)
    minted = fresh_secret()

    assert client._redact("") == ""
    assert client._redact(BOUNDARY_TOKEN) == REDACTED_MARKER
    assert client._redact(minted) == REDACTED_MARKER
    assert client._redact(NEAR_MISS_TOKEN) == NEAR_MISS_TOKEN
    assert client._redact(SHORT_PREFIX) == SHORT_PREFIX
    # Several tokens, so a first-token or last-token shortcut fails.
    assert (
        client._redact(f"{LONG_FIRST} {NEAR_MISS_TOKEN} {SHORT_PREFIX} {LONG_SECOND}")
        == f"{REDACTED_MARKER} {NEAR_MISS_TOKEN} {SHORT_PREFIX} {REDACTED_MARKER}"
    )


def test_masks_long_tokens_whatever_characters_they_carry(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    """Credentials carry digits, case and punctuation, not only letters."""
    client = make_client(fake, project_root, actor_file=actor_file)

    assert client._redact('proof="sk-live_9F2bQ7xT" end') == f"{REDACTED_MARKER} end"
    assert client._redact("id Bearer-9F2bQ7xTzK!") == f"id {REDACTED_MARKER}"
    assert client._redact("sum 00000000 end") == f"sum {REDACTED_MARKER} end"
    assert client._redact(f"key {fresh_secret()} end") == f"key {REDACTED_MARKER} end"


def test_keeps_short_prose_and_the_shape_of_the_text(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    """Only long tokens go; the words and the whitespace around them stay."""
    client = make_client(fake, project_root, actor_file=actor_file)

    assert client._redact(PROSE) == PROSE
    assert (
        client._redact(f"auth failed\n{LONG_FIRST}\nretry now")
        == f"auth failed\n{REDACTED_MARKER}\nretry now"
    )
    assert (
        client._redact(f"id {NEAR_MISS_TOKEN}\t{LONG_SECOND} end")
        == f"id {NEAR_MISS_TOKEN}\t{REDACTED_MARKER} end"
    )


def test_bounded_truncates_the_redacted_text_and_keeps_its_tail(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    client = make_client(fake, project_root, actor_file=actor_file)
    unit = f"{NEAR_MISS_TOKEN} {LONG_FIRST} {SHORT_PREFIX} {LONG_SECOND}"
    repeats = MAX_STDERR_TAIL_CHARS // len(client._redact(unit)) + 2
    raw = " ".join([unit] * repeats)
    redacted = client._redact(raw)
    assert len(redacted) > MAX_STDERR_TAIL_CHARS

    bounded = client._bounded(raw)

    assert bounded.startswith(TRUNCATION_MARKER)
    assert marks_truncation(bounded)
    tail = bounded[len(TRUNCATION_MARKER) :]
    assert redacted.endswith(tail)
    # The tail spends the whole budget, so a token-sized tail is not a bound.
    assert MAX_STDERR_TAIL_CHARS - len(TRUNCATION_MARKER) <= len(tail)
    assert len(tail) <= MAX_STDERR_TAIL_CHARS
    assert REDACTED_MARKER in tail
    assert LONG_FIRST not in bounded
    assert LONG_SECOND not in bounded
    assert not any(piece in bounded for piece in secret_fragments(LONG_FIRST))
    assert not any(piece in bounded for piece in secret_fragments(LONG_SECOND))


def test_bounded_applies_the_bound_to_the_redacted_text(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    """The bound measures the masked text, so masking cannot be skipped."""
    client = make_client(fake, project_root, actor_file=actor_file)
    repeats = MAX_STDERR_TAIL_CHARS // len(LONG_FIRST) + 2
    raw = " ".join([LONG_FIRST] * repeats)
    redacted = client._redact(raw)
    assert len(raw) > MAX_STDERR_TAIL_CHARS
    assert len(redacted) <= MAX_STDERR_TAIL_CHARS

    bounded = client._bounded(raw)

    assert bounded == redacted
    assert not bounded.startswith(TRUNCATION_MARKER)
    assert LONG_FIRST not in bounded

    # A text that fits even before masking keeps its short tokens and its shape.
    fitting = f"{NEAR_MISS_TOKEN} {LONG_SECOND}"
    expected = f"{NEAR_MISS_TOKEN} {REDACTED_MARKER}"
    assert len(expected) <= MAX_STDERR_TAIL_CHARS
    assert client._bounded(fitting) == expected


@pytest.mark.parametrize(
    "trailer", [b"", INVALID_UTF8], ids=["valid-utf8", "invalid-utf8"]
)
def test_detail_decodes_bytes_and_masks_long_tokens(
    fake: FakeController, project_root: Path, actor_file: Path, trailer: bytes
) -> None:
    client = make_client(fake, project_root, actor_file=actor_file)
    raw = f"{NEAR_MISS_TOKEN} {LONG_FIRST} {SHORT_PREFIX}"

    detail = client._detail(raw.encode("utf-8") + b" " + trailer)

    assert isinstance(detail, str)
    assert REDACTED_MARKER in detail
    assert LONG_FIRST not in detail
    assert not any(piece in detail for piece in secret_fragments(LONG_FIRST))
    assert NEAR_MISS_TOKEN in detail
    assert SHORT_PREFIX in detail
    if trailer == INVALID_UTF8:
        # Undecodable bytes become the replacement character, not an exception
        # and not a silently different encoding.
        assert "�" in detail


def test_detail_keeps_secret_free_and_multibyte_stderr_whole(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    """Short-word output is a diagnostic on its own and must arrive intact."""
    client = make_client(fake, project_root, actor_file=actor_file)

    assert client._detail(PROSE.encode("utf-8")) == PROSE
    assert client._detail(MULTIBYTE_PROSE.encode("utf-8")) == MULTIBYTE_PROSE


def test_detail_bounds_long_stderr_through_the_same_pipeline(
    fake: FakeController, project_root: Path, actor_file: Path
) -> None:
    client = make_client(fake, project_root, actor_file=actor_file)
    unit = f"{NEAR_MISS_TOKEN} {LONG_SECOND} {SHORT_PREFIX}"
    repeats = MAX_STDERR_TAIL_CHARS // len(client._redact(unit)) + 2
    raw = " ".join([unit] * repeats)
    assert len(client._redact(raw)) > MAX_STDERR_TAIL_CHARS

    detail = client._detail(raw.encode("utf-8"))

    assert detail == client._bounded(raw)
    assert detail.startswith(TRUNCATION_MARKER)
    assert LONG_SECOND not in detail


def test_apply_diagnostic_is_masked_with_an_unreadable_actor_file(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    """The real failure path reports the controller's words without the secret."""
    actor_path = write_actor_file(
        tmp_path, "short-actor", secret=NEAR_MISS_TOKEN, flavor="plain"
    )
    actor_path.chmod(0o000)
    minted = fresh_secret()
    fake.respond(CONTRACT_ANSWER, verb="contract")
    # Short words only, so what survives beside the mask stays checkable.
    fake.respond("", verb="apply", stderr=f"auth bad {minted}", exit_code=3)
    client = make_client(fake, project_root, actor_file=actor_path)

    with pytest.raises(ControllerError) as caught:
        client.apply(make_envelope(request_id="req-redacted-stderr"))

    message = str(caught.value)
    assert "auth bad" in message
    assert REDACTED_MARKER in message
    assert minted not in message
    assert not any(piece in message for piece in secret_fragments(minted))
    # The path the client was configured with is what the controller received.
    assert str(actor_path) in fake.call_for("apply")["argv"]


def test_apply_diagnostic_drops_controller_text_when_the_credential_is_tiny(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    """A credential too short to mask costs the controller its whole message."""
    actor_path = tiny_actor_file(tmp_path)
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond("", verb="apply", stderr=controller_stderr(TINY_SECRET), exit_code=3)
    client = make_client(fake, project_root, actor_file=actor_path)

    with pytest.raises(ControllerError) as caught:
        client.apply(make_envelope(request_id="req-tiny-credential"))

    message = str(caught.value)
    assert TINY_SECRET not in message
    assert not any(word in message for word in CONTROLLER_PROSE)
    assert REDACTED_MARKER in message
    # The path the client was configured with is what the controller received.
    assert str(actor_path) in fake.call_for("apply")["argv"]


def test_apply_diagnostic_drops_controller_text_when_the_actor_file_cannot_be_stated(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    """An actor file behind an untraversable directory proves nothing safe."""
    locked = tmp_path / "locked dir"
    locked.mkdir()
    actor_path = write_actor_file(locked, "actor.json", secret=LONG_FIRST)
    locked.chmod(0o000)
    minted = fresh_secret()
    fake.respond(CONTRACT_ANSWER, verb="contract")
    fake.respond("", verb="apply", stderr=controller_stderr(minted), exit_code=3)
    client = make_client(fake, project_root, actor_file=actor_path)

    try:
        with pytest.raises(ControllerError) as caught:
            client.apply(make_envelope(request_id="req-unstatable-actor"))
    finally:
        locked.chmod(0o700)

    message = str(caught.value)
    assert minted not in message
    assert not any(piece in message for piece in secret_fragments(minted))
    assert not any(word in message for word in CONTROLLER_PROSE)
    assert REDACTED_MARKER in message


@pytest.mark.parametrize("state", ["tiny-credential", "ordinary-name", "missing-actor"])
def test_contract_drops_controller_text_when_the_credential_may_be_unmaskable(
    fake: FakeController, project_root: Path, tmp_path: Path, state: str
) -> None:
    """A mismatching live field is controller output, exactly as stderr is."""
    actor_path = unmaskable_actor_file(tmp_path, state)
    minted = fresh_secret()
    live_value = f"{CONTROLLER_PROSE[0]} {TINY_SECRET} {minted} {CONTROLLER_PROSE[1]}"
    fake.respond(json.dumps(live_contract(schema_digest=live_value)), verb="contract")
    client = make_client(fake, project_root, actor_file=actor_path)

    with pytest.raises(IncompatibleContractError) as caught:
        client.contract()

    message = str(caught.value)
    assert TINY_SECRET not in message
    assert minted not in message
    assert not any(word in message for word in CONTROLLER_PROSE)
    assert REDACTED_MARKER in message
    # The diagnostic still names the field that disagreed.
    assert "schema_digest" in message
    assert fake.verbs() == ["contract"]


@pytest.mark.parametrize("state", ["tiny-credential", "ordinary-name", "missing-actor"])
def test_contract_drops_controller_text_for_a_mismatched_protocol_major(
    fake: FakeController, project_root: Path, tmp_path: Path, state: str
) -> None:
    """A non-int protocol_major is controller output, exactly as stderr is."""
    actor_path = unmaskable_actor_file(tmp_path, state)
    minted = fresh_secret()
    live_value = f"{CONTROLLER_PROSE[0]} {TINY_SECRET} {minted} {CONTROLLER_PROSE[1]}"
    fake.respond(json.dumps(live_contract(protocol_major=live_value)), verb="contract")
    client = make_client(fake, project_root, actor_file=actor_path)

    with pytest.raises(IncompatibleContractError) as caught:
        client.contract()

    message = str(caught.value)
    assert TINY_SECRET not in message
    assert minted not in message
    assert not any(word in message for word in CONTROLLER_PROSE)
    assert REDACTED_MARKER in message
    # The diagnostic still names the field that disagreed.
    assert "protocol_major" in message
    assert fake.verbs() == ["contract"]


def test_contract_keeps_controller_prose_when_the_actor_file_reaches_the_threshold(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    """One byte more in the actor file, and the controller's words come back."""
    actor_path = write_actor_file(
        tmp_path, "boundary-actor", secret=NEAR_MISS_TOKEN, flavor="plain"
    )
    assert actor_path.stat().st_size == MIN_SECRET_CHARS
    minted = fresh_secret()
    live = live_contract(schema_digest=controller_stderr(minted))
    fake.respond(json.dumps(live), verb="contract")
    client = make_client(fake, project_root, actor_file=actor_path)

    with pytest.raises(IncompatibleContractError) as caught:
        client.contract()

    message = str(caught.value)
    assert all(word in message for word in CONTROLLER_PROSE)
    assert REDACTED_MARKER in message
    assert minted not in message
    assert not any(piece in message for piece in secret_fragments(minted))


def test_a_diagnostic_is_built_without_reading_the_actor_file(
    fake: FakeController,
    project_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Credential safety is settled without ever opening the actor file."""
    actor_path = write_actor_file(tmp_path, "actor.json", secret=LONG_FIRST)
    assert actor_path.stat().st_size >= MIN_SECRET_CHARS
    client = make_client(fake, project_root, actor_file=actor_path)
    minted = fresh_secret()
    raw = f"{CONTROLLER_PROSE[0]} {minted} {CONTROLLER_PROSE[1]} {NEAR_MISS_TOKEN}"

    with monkeypatch.context() as patched:
        patched.setattr(pathlib.Path, "read_bytes", refuse_file_access)
        patched.setattr(pathlib.Path, "open", refuse_file_access)
        patched.setattr(builtins, "open", refuse_file_access)
        detail = client._detail(raw.encode("utf-8"))

    assert all(word in detail for word in CONTROLLER_PROSE)
    assert REDACTED_MARKER in detail
    assert minted not in detail
    assert NEAR_MISS_TOKEN in detail
