from __future__ import annotations

import json
from pathlib import Path

from tests.workflow_client.conftest import (
    FakeController,
    make_client,
    write_actor_file,
)

from ovcaq.workflow_client import REDACTED_MARKER

# Synthetic canaries used only as actor-file contents, never real credentials.
FIRST_PROOF = "first-proof-value-99"
SECOND_PROOF = "second-proof-value-77"
WOULD_BE_PROOF = "would-be-proof-value-12"


def test_redact_picks_up_rotated_secret_after_cache_is_populated(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    actor_path = write_actor_file(tmp_path, "actor.json", secret=FIRST_PROOF)
    client = make_client(fake, project_root, actor_file=actor_path)
    # Populate the per-client secret cache with the original secret.
    assert client._redact(f"before {FIRST_PROOF} after") == (
        f"before {REDACTED_MARKER} after"
    )

    # The actor file's secret rotates after the cache was populated.
    actor_path.write_text(
        json.dumps({"actor_id": "actor-a", "auth": {"proof": SECOND_PROOF}}),
        encoding="utf-8",
    )

    redacted = client._redact(f"before {SECOND_PROOF} after")

    assert SECOND_PROOF not in redacted
    assert redacted == f"before {REDACTED_MARKER} after"


def test_redact_with_unreadable_actor_file_does_not_raise(
    fake: FakeController, project_root: Path, tmp_path: Path
) -> None:
    missing_actor = tmp_path / "missing-actor.json"
    assert not missing_actor.exists()
    client = make_client(fake, project_root, actor_file=missing_actor)

    redacted = client._redact(f"token={WOULD_BE_PROOF}")

    # Documented behavior (see _actor_secrets' docstring): an unreadable
    # actor file yields no secrets, so nothing is redacted and no error is
    # raised.
    assert redacted == f"token={WOULD_BE_PROOF}"
    assert REDACTED_MARKER not in redacted
