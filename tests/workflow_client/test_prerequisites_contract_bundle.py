"""PRD 58's contract-bundle content and provenance validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from tests.workflow_client.prerequisites_support import (
    BUNDLE_KEY,
    BUNDLE_PATH,
    CLOSURE,
    GATES,
    VALID_BUNDLE,
    digest_variant,
    gate_config,
    mark_done,
    missing_of,
    report,
    run_tool,
    write_artifact,
    write_config,
    write_valid_bundle,
)

TABLE, KEY, TOKENS = GATES["58"]
ARTIFACT = f"artifacts/{KEY}.json"


def write_ready_artifact(root: Path) -> str:
    """Done predecessors and a satisfied controller-artifact gate for PRD 58."""
    mark_done(root, *CLOSURE["58"])
    return write_artifact(root / ARTIFACT, {"evidence": list(TOKENS)})


@pytest.mark.parametrize("body", [b"", b"{not valid"])
def test_empty_or_non_json_bundle_is_not_ready(tmp_path: Path, body: bytes) -> None:
    digest = write_ready_artifact(tmp_path)
    bundle_path = tmp_path / BUNDLE_PATH
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_bytes(body)
    # Digest matches the exact malformed bytes, so only parsing can fail here.
    bundle_digest = hashlib.sha256(body).hexdigest()
    write_config(
        tmp_path / "ovcaq.toml",
        gate_config(
            "58", ARTIFACT, digest, bundle=BUNDLE_PATH, bundle_digest=bundle_digest
        ),
    )

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY not in missing[0]


@pytest.mark.parametrize(
    "case",
    ["digest-mismatch", "truncated-digest", "last-hex-differs", "middle-hex-differs"],
)
def test_bundle_digest_mismatch_is_not_ready(tmp_path: Path, case: str) -> None:
    digest = write_ready_artifact(tmp_path)
    bundle_digest = write_valid_bundle(tmp_path)
    configured = digest_variant(case, bundle_digest)
    write_config(
        tmp_path / "ovcaq.toml",
        gate_config(
            "58", ARTIFACT, digest, bundle=BUNDLE_PATH, bundle_digest=configured
        ),
    )

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY not in missing[0]


def test_bundle_without_a_configured_digest_is_not_ready(tmp_path: Path) -> None:
    digest = write_ready_artifact(tmp_path)
    write_valid_bundle(tmp_path)
    write_config(
        tmp_path / "ovcaq.toml",
        gate_config("58", ARTIFACT, digest, bundle=BUNDLE_PATH),
    )

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY not in missing[0]


def test_two_distinct_valid_bundle_payloads_each_report_ready(tmp_path: Path) -> None:
    """A hardcoded bundle shape or digest would fail one of these two payloads."""
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    cases = (
        (first, {**VALID_BUNDLE, "package_version": "1.2.3"}),
        (second, {**VALID_BUNDLE, "package_version": "4.5.6"}),
    )
    for root, payload in cases:
        digest = write_ready_artifact(root)
        bundle_digest = write_valid_bundle(root, BUNDLE_PATH, payload)
        write_config(
            root / "ovcaq.toml",
            gate_config(
                "58", ARTIFACT, digest, bundle=BUNDLE_PATH, bundle_digest=bundle_digest
            ),
        )

        assert report(run_tool(root, "58"), 0) == {"ready": True, "prd": "58"}
