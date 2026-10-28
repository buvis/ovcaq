"""PRD 58's controller-artifact gate and contract-bundle precondition."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import pytest
from tests.workflow_client.conftest import (
    FakeController,
    live_contract,
    load_json,
    make_client,
)
from tests.workflow_client.prerequisites_support import (
    BUNDLE_KEY,
    BUNDLE_PATH,
    CLOSURE,
    DIRECT,
    GATES,
    TOOL,
    UNMET_GATE_CASES,
    VALID_BUNDLE,
    assert_refused,
    build_unmet_gate,
    digest_variant,
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

from ovcaq.workflow_client import IncompatibleContractError, controller_bundle_digest

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
            tmp_path,
            "bundles/exported.json",
            {**VALID_BUNDLE, "package_version": "1.4.2"},
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


# One definition of a valid pinned bundle: the tool's PRD 58 gate and the
# controller client must accept and refuse the very same configured value.


def bundle_text(*extra: str, override: dict[str, str] | None = None) -> str:
    """The valid bundle as raw JSON text, plus `extra` entries verbatim.

    Every required field is present, so a file built here can only be refused
    for the defect the caller injected.
    """
    replaced = {} if override is None else override
    entries = [
        f"{json.dumps(name)}: {replaced.get(name, json.dumps(value))}"
        for name, value in VALID_BUNDLE.items()
    ]
    return "{" + ", ".join([*entries, *extra]) + "}"


def stage_bundle(root: Path, body: bytes, pin: str) -> Path:
    """PRD 58 with predecessors done, its artifact met and `body` pinned."""
    root.mkdir(parents=True, exist_ok=True)
    mark_done(root, *CLOSURE["58"])
    digest = write_artifact(root / ARTIFACT, {"evidence": list(TOKENS)})
    bundle = root / BUNDLE_PATH
    write_artifact(bundle, body)
    write_config(
        root / "ovcaq.toml",
        gate_config("58", ARTIFACT, digest, bundle=BUNDLE_PATH, bundle_digest=pin),
    )
    return bundle


def hex_case(digest: str, case: str) -> str:
    """The same digest in the letter case an operator might paste."""
    if case == "upper":
        return digest.upper()
    if case == "alternating":
        return "".join(
            char.upper() if index % 2 else char for index, char in enumerate(digest)
        )
    if case == "first-letter-only":
        index = next(at for at, char in enumerate(digest) if char.isalpha())
        return digest[:index] + digest[index].upper() + digest[index + 1 :]
    if case == "scattered":
        picker = random.Random(20261028)
        return "".join(
            char.upper() if picker.getrandbits(1) else char for char in digest
        )
    return digest


@pytest.mark.parametrize(
    "case", ["lower", "upper", "alternating", "first-letter-only", "scattered"]
)
def test_one_pin_in_any_hex_case_is_accepted_by_the_tool_and_the_client(
    tmp_path: Path, fake: FakeController, project_root: Path, case: str
) -> None:
    """The pin an operator configures once is read the same way by both."""
    root = tmp_path / "project"
    body = json.dumps({**VALID_BUNDLE, "package_version": "1.4.2"}).encode("utf-8")
    digest = hashlib.sha256(body).hexdigest()
    pin = hex_case(digest, case)
    bundle = stage_bundle(root, body, pin)
    # The pinned value is the sha256 of the bundle file's raw bytes, spelled in
    # a letter case that differs from it unless the case is "lower".
    assert pin.lower() == hashlib.sha256(bundle.read_bytes()).hexdigest()
    assert (pin == digest) == (case == "lower")
    fake.respond(
        json.dumps(live_contract(load_json(bundle), package_version="1.4.2+live")),
        verb="contract",
    )

    assert report(run_tool(root, "58"), 0) == {"ready": True, "prd": "58"}

    contract = make_client(
        fake, project_root, bundle=bundle, bundle_digest=pin
    ).contract()

    assert contract.package_version == "1.4.2+live"
    # Both consumers answer with the file's own lowercase digest.
    assert controller_bundle_digest(bundle, pin) == digest
    # The configured controller argv reached the process the client spawned.
    assert len(fake.calls()) == 1
    assert fake.call_for("contract")["argv"][:2] == fake.child_argv


@pytest.mark.parametrize(
    "case",
    [
        "prefix",
        "extended",
        "surrounded",
        "other-bundle",
        "last-hex-differs",
        "middle-hex-differs",
    ],
)
def test_a_pin_that_is_not_the_whole_digest_is_refused_by_both(
    tmp_path: Path, case: str
) -> None:
    """Hex case is all that is forgiven: a near miss still refuses the bundle."""
    root = tmp_path / "project"
    body = json.dumps(VALID_BUNDLE).encode("utf-8")
    digest = hashlib.sha256(body).hexdigest()
    pin = {
        "prefix": digest.upper()[:32],
        "extended": digest.upper() + "0",
        "surrounded": f" {digest.upper()} ",
        "other-bundle": hashlib.sha256(b"other bundle").hexdigest().upper(),
        # One hex character wrong, at the end and in the middle: same length,
        # same leading characters, still a different bundle.
        "last-hex-differs": digest_variant("last-hex-differs", digest).upper(),
        "middle-hex-differs": digest_variant("middle-hex-differs", digest).upper(),
    }[case]
    assert pin.lower() != digest
    bundle = stage_bundle(root, body, pin)

    missing = missing_of(run_tool(root, "58"), "58")

    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY not in missing[0]
    with pytest.raises(IncompatibleContractError) as caught:
        controller_bundle_digest(bundle, pin)
    assert digest in str(caught.value)


def test_the_client_refuses_an_uppercase_prefix_pin_before_spawning(
    tmp_path: Path, fake: FakeController, project_root: Path
) -> None:
    """The refusal is loud and closed: no controller runs on a bad pin."""
    body = json.dumps(VALID_BUNDLE).encode("utf-8")
    digest = hashlib.sha256(body).hexdigest()
    pin = digest.upper()[:32]
    bundle = stage_bundle(tmp_path / "project", body, pin)
    fake.respond(json.dumps(live_contract(load_json(bundle))), verb="contract")

    with pytest.raises(IncompatibleContractError) as caught:
        make_client(fake, project_root, bundle=bundle, bundle_digest=pin).contract()

    assert digest in str(caught.value)
    assert fake.calls() == []


@pytest.mark.parametrize(
    "case",
    [
        "duplicate-key",
        "duplicate-optional-key",
        "nested-duplicate-key",
        "nan",
        "infinity",
    ],
)
def test_a_bundle_that_is_not_strict_json_is_refused_by_both(
    tmp_path: Path, fake: FakeController, project_root: Path, case: str
) -> None:
    """The gate never passes a bundle the client refuses at start-up."""
    root = tmp_path / "project"
    text = {
        "duplicate-key": bundle_text(
            f'"operations": {json.dumps(VALID_BUNDLE["operations"])}'
        ),
        # A repeated key neither consumer requires: strictness is about the
        # document, not about the fields a bundle must carry.
        "duplicate-optional-key": bundle_text(
            f'"package_version": {json.dumps(VALID_BUNDLE["package_version"])}'
        ),
        "nested-duplicate-key": bundle_text('"extra": {"a": 1, "a": 2}'),
        "nan": bundle_text(override={"protocol_major": "NaN"}),
        "infinity": bundle_text(override={"protocol_major": "Infinity"}),
    }[case]
    body = text.encode("utf-8")
    # A lenient parser sees a complete bundle, so only strictness can refuse it.
    assert set(json.loads(body)) >= set(VALID_BUNDLE)
    pin = hashlib.sha256(body).hexdigest()
    bundle = stage_bundle(root, body, pin)
    fake.respond(json.dumps(live_contract()), verb="contract")

    missing = missing_of(run_tool(root, "58"), "58")

    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY not in missing[0]
    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(bundle)
    with pytest.raises(IncompatibleContractError):
        make_client(fake, project_root, bundle=bundle, bundle_digest=pin).contract()
    assert fake.calls() == []


@pytest.mark.parametrize(
    "extra",
    ["", '"note": "NaN and Infinity are words in this string"'],
    ids=["plain", "non-finite-words-inside-a-string"],
)
def test_a_strict_bundle_written_the_same_way_is_accepted_by_both(
    tmp_path: Path, fake: FakeController, project_root: Path, extra: str
) -> None:
    """Same construction without the defect: the accept side of the same shape."""
    root = tmp_path / "project"
    body = bundle_text(*([extra] if extra else [])).encode("utf-8")
    pin = hashlib.sha256(body).hexdigest()
    bundle = stage_bundle(root, body, pin)
    parsed = json.loads(body)
    # Every valid field, unchanged; the spelling NaN only ever sits in a string.
    assert {name: parsed[name] for name in VALID_BUNDLE} == VALID_BUNDLE
    assert ("NaN" in body.decode("utf-8")) == bool(extra)
    fake.respond(json.dumps(live_contract(load_json(bundle))), verb="contract")

    assert report(run_tool(root, "58"), 0) == {"ready": True, "prd": "58"}

    contract = make_client(
        fake, project_root, bundle=bundle, bundle_digest=pin
    ).contract()

    assert contract.package_version == VALID_BUNDLE["package_version"]
    assert controller_bundle_digest(bundle, pin) == pin


def without_field(field: str) -> bytes:
    body = {name: value for name, value in VALID_BUNDLE.items() if name != field}
    assert field not in body
    return json.dumps(body).encode("utf-8")


@pytest.mark.parametrize(
    "body",
    [b"{not json", b"{}", without_field("protocol_major")],
    ids=["not-json", "empty-object", "no-protocol_major"],
)
def test_a_pinned_file_that_is_not_a_contract_bundle_is_refused_by_both(
    tmp_path: Path, body: bytes
) -> None:
    """A matching pin waives no validation: both consumers still read the file."""
    root = tmp_path / "project"
    pin = hashlib.sha256(body).hexdigest()
    bundle = stage_bundle(root, body, pin)
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == pin

    missing = missing_of(run_tool(root, "58"), "58")

    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY not in missing[0]
    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(bundle, pin)


def test_a_bundle_configured_without_a_pin_is_not_accepted(tmp_path: Path) -> None:
    """An unpinned bundle names nothing, however valid the file itself is."""
    mark_done(tmp_path, *CLOSURE["58"])
    digest = write_artifact(tmp_path / ARTIFACT, {"evidence": list(TOKENS)})
    bundle_digest = write_valid_bundle(tmp_path)
    assert (tmp_path / BUNDLE_PATH).is_file()
    unpinned = gate_config("58", ARTIFACT, digest, bundle=BUNDLE_PATH)
    write_config(tmp_path / "ovcaq.toml", unpinned)

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY not in missing[0]
    # The same valid bundle with its pin configured is ready, so only the
    # absent pin refused it.
    write_config(
        tmp_path / "ovcaq.toml",
        gate_config(
            "58", ARTIFACT, digest, bundle=BUNDLE_PATH, bundle_digest=bundle_digest
        ),
    )
    assert report(run_tool(tmp_path, "58"), 0) == {"ready": True, "prd": "58"}


def padded_bundle(size: int) -> bytes:
    """The valid bundle padded with whitespace to exactly size bytes."""
    body = json.dumps(VALID_BUNDLE).encode("utf-8")
    return body + b" " * (size - len(body))


@pytest.mark.parametrize(("size", "ready"), [(CAP, True), (CAP + 1, False)])
def test_contract_bundle_is_read_under_a_16_mib_cap(
    tmp_path: Path, size: int, ready: bool
) -> None:
    mark_done(tmp_path, *CLOSURE["58"])
    digest = write_artifact(tmp_path / ARTIFACT, {"evidence": list(TOKENS)})
    payload = padded_bundle(size)
    assert len(payload) == size
    bundle_digest = write_valid_bundle(tmp_path, BUNDLE_PATH, payload)
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
        assert BUNDLE_KEY in missing[0]
        assert KEY not in missing[0]


def test_the_tool_imports_nothing_from_ovcaq() -> None:
    """The tool copies the strict parse; it never imports the client package."""
    lines = [
        line.strip()
        for line in TOOL.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith(("import ", "from "))
    ]

    # Control: the extraction really found the tool's stdlib imports.
    assert any(line.startswith("import json") for line in lines)
    assert not [line for line in lines if "ovcaq" in line]
