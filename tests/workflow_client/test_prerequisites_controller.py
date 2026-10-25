"""PRD 58's controller-artifact gate and contract-bundle precondition."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from tests.workflow_client.prerequisites_support import (
    BUNDLE_KEY,
    BUNDLE_PATH,
    CLOSURE,
    DIRECT,
    GATES,
    UNMET_GATE_CASES,
    assert_refused,
    build_unmet_gate,
    foreign_keys,
    gate_config,
    make_ready,
    mark_done,
    missing_of,
    near_misses,
    padded,
    report,
    run_tool,
    write_artifact,
    write_bundle,
    write_config,
    write_valid_bundle,
)

TABLE, KEY, TOKENS = GATES["58"]
ARTIFACT = f"artifacts/{KEY}.json"
CAP = 16 * 1024 * 1024
DECOY_DIGEST = hashlib.sha256(b"decoy").hexdigest()


def write_gate(
    root: Path,
    *,
    evidence: list[str] | None = None,
    bundle: str | None = BUNDLE_PATH,
) -> Path:
    """Done predecessors, a controller artifact and a valid bundle for PRD 58."""
    mark_done(root, *CLOSURE["58"])
    tokens = list(TOKENS) if evidence is None else evidence
    digest = write_artifact(root / ARTIFACT, {"evidence": tokens})
    bundle_digest = None
    if bundle is not None:
        bundle_digest = write_valid_bundle(root, bundle)
    config = root / "ovcaq.toml"
    write_config(
        config,
        gate_config("58", ARTIFACT, digest, bundle=bundle, bundle_digest=bundle_digest),
    )
    return config


def padded_json(size: int) -> bytes:
    """A valid controller artifact padded with whitespace to exactly size."""
    body = json.dumps({"evidence": list(TOKENS)}).encode("utf-8")
    return body + b" " * (size - len(body))


def test_prd_58_is_not_ready_on_predecessors_alone(tmp_path: Path) -> None:
    mark_done(tmp_path, *CLOSURE["58"])

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 2
    assert KEY in missing[0]
    assert BUNDLE_KEY in missing[1]
    for dep in DIRECT["58"]:
        assert not any(padded(dep) in entry for entry in missing)


@pytest.mark.parametrize("variant", ["relative-lower-digest", "absolute-upper-digest"])
def test_prd_58_is_ready_with_controller_evidence_and_contract_bundle(
    tmp_path: Path, variant: str
) -> None:
    mark_done(tmp_path, *CLOSURE["58"])
    artifact = tmp_path / "artifacts" / f"{KEY}.json"
    if variant == "relative-lower-digest":
        digest = write_artifact(artifact, {"evidence": list(TOKENS)})
        path = ARTIFACT
        bundle = BUNDLE_PATH
        bundle_digest = write_valid_bundle(tmp_path, bundle)
    else:
        evidence = ["AP00017", *reversed(TOKENS), "extra"]
        digest = write_artifact(artifact, {"evidence": evidence, "name": KEY}).upper()
        path = str(artifact)
        bundle = str(tmp_path / "bundles" / "exported.json")
        bundle_digest = write_valid_bundle(
            tmp_path, "bundles/exported.json", {"bundle": "contract"}
        ).upper()
    write_config(
        tmp_path / "ovcaq.toml",
        gate_config("58", path, digest, bundle=bundle, bundle_digest=bundle_digest),
    )

    assert report(run_tool(tmp_path, "58"), 0) == {"ready": True, "prd": "58"}


@pytest.mark.parametrize(
    ("evidence", "absent"),
    [
        (["jobs", "reviews", "records"], "core"),
        (["core", "reviews", "records"], "jobs"),
        (["core", "jobs", "records"], "reviews"),
        (["core", "jobs", "reviews"], "records"),
        (["core", "jobs"], "reviews"),
        (["records"], "core"),
    ],
)
def test_partial_evidence_leaves_prd_58_unready_and_names_a_missing_token(
    tmp_path: Path, evidence: list[str], absent: str
) -> None:
    write_gate(tmp_path, evidence=evidence)

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 1
    assert KEY in missing[0]
    assert absent in missing[0]
    # Only the absent tokens are named; a message listing all four is wrong.
    for token in TOKENS:
        assert (token in missing[0]) == (token not in evidence)


def test_the_message_changes_with_the_tokens_that_are_missing(tmp_path: Path) -> None:
    without_core, without_records = tmp_path / "first", tmp_path / "second"
    without_core.mkdir()
    without_records.mkdir()
    write_gate(without_core, evidence=["jobs", "reviews", "records"])
    write_gate(without_records, evidence=["core", "jobs", "reviews"])

    first = missing_of(run_tool(without_core, "58"), "58")
    second = missing_of(run_tool(without_records, "58"), "58")

    assert "core" in first[0]
    assert "records" not in first[0]
    assert "records" in second[0]
    assert "core" not in second[0]


@pytest.mark.parametrize("token", TOKENS)
def test_near_miss_evidence_never_satisfies_a_required_token(
    tmp_path: Path, token: str
) -> None:
    others = [other for other in TOKENS if other != token]
    evidence = [*others, *near_misses(token)]
    write_gate(tmp_path, evidence=evidence)

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 1
    assert KEY in missing[0]
    for other in TOKENS:
        assert (other in missing[0]) == (other not in evidence)


@pytest.mark.parametrize("case", UNMET_GATE_CASES)
def test_controller_artifact_rejection_is_unmet_not_a_config_error(
    tmp_path: Path, case: str
) -> None:
    mark_done(tmp_path, *CLOSURE["58"])
    text = build_unmet_gate(tmp_path, "58", case)
    if text is not None:
        write_config(tmp_path / "ovcaq.toml", text)

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert any(KEY in entry for entry in missing)
    assert all(KEY in entry or BUNDLE_KEY in entry for entry in missing)
    for foreign in foreign_keys("58"):
        assert not any(foreign in entry for entry in missing)
    for dep in DIRECT["58"]:
        assert not any(padded(dep) in entry for entry in missing)


@pytest.mark.parametrize(
    ("size", "ready"), [(CAP, True), (CAP + 1, False), (4 * CAP, False)]
)
def test_controller_artifact_is_read_under_a_16_mib_cap(
    tmp_path: Path, size: int, ready: bool
) -> None:
    mark_done(tmp_path, *CLOSURE["58"])
    payload = padded_json(size)
    assert len(payload) == size
    digest = write_artifact(tmp_path / ARTIFACT, payload)
    bundle_digest = write_valid_bundle(tmp_path)
    write_config(
        tmp_path / "ovcaq.toml",
        gate_config(
            "58", ARTIFACT, digest, bundle=BUNDLE_PATH, bundle_digest=bundle_digest
        ),
    )

    result = run_tool(tmp_path, "58")

    if ready:
        assert report(result, 0) == {"ready": True, "prd": "58"}
    else:
        missing = missing_of(result, "58")
        assert len(missing) == 1
        assert KEY in missing[0]


@pytest.mark.parametrize(
    "line",
    [
        f"{KEY} = 5",
        f'{KEY} = ["{ARTIFACT}"]',
        f"{KEY}_sha256 = 5",
        f'{KEY}_sha256 = ["{DECOY_DIGEST}"]',
        f"{BUNDLE_KEY} = 5",
        f'{BUNDLE_KEY} = ["{BUNDLE_PATH}"]',
        f"{BUNDLE_KEY} = true",
        f"{BUNDLE_KEY}_sha256 = 5",
        f'{BUNDLE_KEY}_sha256 = ["{DECOY_DIGEST}"]',
    ],
)
def test_non_string_workflow_values_are_refused(tmp_path: Path, line: str) -> None:
    config = write_gate(tmp_path)
    name = line.split(" = ")[0]
    kept = [
        line if existing.startswith(f"{name} =") else existing
        for existing in config.read_text(encoding="utf-8").splitlines()
    ]
    assert line in kept
    write_config(config, "\n".join(kept) + "\n")

    assert_refused(run_tool(tmp_path, "58"), name)


def test_workflow_table_holding_a_scalar_is_refused(tmp_path: Path) -> None:
    write_gate(tmp_path)
    write_config(tmp_path / "ovcaq.toml", f'{TABLE} = "oops"\n')

    assert_refused(run_tool(tmp_path, "58"), TABLE)


@pytest.mark.parametrize(
    "case",
    [
        "unset",
        "missing-file",
        "directory",
        "symlinked-file",
        "symlinked-parent-dir",
        "symlinked-parent-escapes-root",
    ],
)
def test_contract_bundle_must_name_an_existing_regular_file(
    tmp_path: Path, case: str
) -> None:
    mark_done(tmp_path, *CLOSURE["58"])
    digest = write_artifact(tmp_path / ARTIFACT, {"evidence": list(TOKENS)})
    real = write_bundle(tmp_path, "bundles/exported.json")
    bundle: str | None = "bundles/exported.json"
    if case == "unset":
        bundle = None
    elif case == "missing-file":
        bundle = "bundles/absent.json"
    elif case == "directory":
        bundle = "bundles"
    elif case == "symlinked-file":
        (tmp_path / "bundles" / "mirror.json").symlink_to(real)
        bundle = "bundles/mirror.json"
    elif case == "symlinked-parent-dir":
        (tmp_path / "exports").symlink_to(
            tmp_path / "bundles", target_is_directory=True
        )
        bundle = "exports/exported.json"
    else:
        outside = tmp_path.parent / f"outside-{tmp_path.name}"
        write_bundle(outside, "exported.json")
        (tmp_path / "exports").symlink_to(outside, target_is_directory=True)
        bundle = "exports/exported.json"
    write_config(
        tmp_path / "ovcaq.toml", gate_config("58", ARTIFACT, digest, bundle=bundle)
    )

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY not in missing[0]


def test_relative_paths_resolve_against_cwd_not_the_config_directory(
    tmp_path: Path,
) -> None:
    mark_done(tmp_path, *CLOSURE["58"])
    digest = write_artifact(tmp_path / ARTIFACT, {"evidence": list(TOKENS)})
    bundle_digest = write_valid_bundle(tmp_path)
    config = tmp_path / "conf" / "gate.toml"
    # Beside the config sits a decoy artifact and no bundle at all.
    write_artifact(config.parent / ARTIFACT, {"evidence": ["core", "jobs"]})
    write_config(
        config,
        gate_config(
            "58", ARTIFACT, digest, bundle=BUNDLE_PATH, bundle_digest=bundle_digest
        ),
    )

    result = run_tool(tmp_path, "58", "--config", str(config))

    assert report(result, 0) == {"ready": True, "prd": "58"}


def test_prd_58_ignores_the_other_prds_artifact_gates(tmp_path: Path) -> None:
    config = write_gate(tmp_path)
    decoys = (
        "[autopilot]\n"
        'plugin_artifact = "artifacts/absent-plugin.json"\n'
        f'plugin_artifact_sha256 = "{DECOY_DIGEST}"\n'
        "[operator]\n"
        'client_artifact = "artifacts/absent-client.json"\n'
        f'client_artifact_sha256 = "{DECOY_DIGEST}"\n'
    )
    write_config(config, config.read_text(encoding="utf-8") + decoys)

    assert report(run_tool(tmp_path, "58"), 0) == {"ready": True, "prd": "58"}


def test_contract_bundle_counts_only_under_the_workflow_table(tmp_path: Path) -> None:
    mark_done(tmp_path, *CLOSURE["58"])
    digest = write_artifact(tmp_path / ARTIFACT, {"evidence": list(TOKENS)})
    write_bundle(tmp_path)
    # The artifact gate is met; only the bundle hides in a foreign table.
    write_config(
        tmp_path / "ovcaq.toml",
        gate_config("58", ARTIFACT, digest)
        + f"[autopilot]\n{BUNDLE_KEY} = {json.dumps(BUNDLE_PATH)}\n",
    )

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY not in missing[0]


@pytest.mark.parametrize("prd", ["61", "65"])
def test_other_prds_ignore_the_controller_gate_and_the_bundle(
    tmp_path: Path, prd: str
) -> None:
    make_ready(tmp_path, prd)
    config = tmp_path / "ovcaq.toml"
    decoys = (
        f"[{TABLE}]\n"
        f'{KEY} = "artifacts/absent-controller.json"\n'
        f'{KEY}_sha256 = "{DECOY_DIGEST}"\n'
        f'{BUNDLE_KEY} = "artifacts/absent-bundle.json"\n'
    )
    write_config(config, config.read_text(encoding="utf-8") + decoys)

    assert report(run_tool(tmp_path, prd), 0) == {"ready": True, "prd": prd}


def test_missing_lists_predecessors_then_the_artifact_then_the_bundle(
    tmp_path: Path,
) -> None:
    mark_done(tmp_path, "62")

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 3
    assert padded("57") in missing[0]
    assert KEY in missing[1]
    assert BUNDLE_KEY in missing[2]
    assert not any(padded("62") in entry for entry in missing)
