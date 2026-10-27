from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest
from tests.workflow_client.prerequisites_support import (
    BUNDLE_FIXTURE,
    BUNDLE_KEY,
    BUNDLE_PATH,
    CLOSURE,
    DEPENDENCY_CASES,
    DIRECT,
    FORBIDDEN_IMPORTS,
    GATES,
    ID_SPELLINGS,
    OTHER_GATE,
    PRDS,
    TOOL,
    UNMET_GATE_CASES,
    assert_refused,
    build_unmet_gate,
    digest_variant,
    foreign_keys,
    gate_config,
    make_ready,
    mark_done,
    missing_of,
    padded,
    report,
    run_tool,
    satisfy_gate,
    write_artifact,
    write_config,
)

from ovcaq.config import controller_settings
from ovcaq.workflow_client import IncompatibleContractError, controller_bundle_digest

# Dependency graph


@pytest.mark.parametrize("prd", sorted(DIRECT))
def test_reports_ready_when_every_predecessor_is_done(tmp_path: Path, prd: str) -> None:
    make_ready(tmp_path, prd)

    assert report(run_tool(tmp_path, prd), 0) == {"ready": True, "prd": prd}


@pytest.mark.parametrize(("prd", "dep"), DEPENDENCY_CASES)
def test_names_the_single_unmet_predecessor(tmp_path: Path, prd: str, dep: str) -> None:
    mark_done(tmp_path, *(done for done in CLOSURE[prd] if done != dep))
    satisfy_gate(tmp_path, prd)

    missing = missing_of(run_tool(tmp_path, prd), prd)

    assert len(missing) == 1
    assert padded(dep) in missing[0]
    for other in DIRECT[prd]:
        if other != dep:
            assert padded(other) not in missing[0]


def test_missing_done_directory_leaves_every_predecessor_unmet_in_graph_order(
    tmp_path: Path,
) -> None:
    mark_done(tmp_path, "57", "62", bucket="backlog")
    satisfy_gate(tmp_path, "58")

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 2
    assert "00057" in missing[0]
    assert "00062" in missing[1]


@pytest.mark.parametrize(
    ("prd", "unmet"),
    [("61", ("60",)), ("65", ("60", "61", "64"))],
)
def test_lists_predecessors_in_graph_order_before_artifact_entries(
    tmp_path: Path, prd: str, unmet: tuple[str, ...]
) -> None:
    mark_done(tmp_path, *(done for done in CLOSURE[prd] if done not in unmet))
    _, key, _ = GATES[prd]

    missing = missing_of(run_tool(tmp_path, prd), prd)

    for index, dep in enumerate(unmet):
        assert padded(dep) in missing[index]
    artifact_entries = missing[len(unmet) :]
    assert artifact_entries
    assert all(key in entry for entry in artifact_entries)
    for foreign in foreign_keys(prd):
        assert not any(foreign in entry for entry in missing)


@pytest.mark.parametrize("bucket", ["backlog", "wip", "hold", "all"])
def test_predecessor_outside_done_is_never_accepted(
    tmp_path: Path, bucket: str
) -> None:
    mark_done(tmp_path, "62")
    for name in ["backlog", "wip", "hold"] if bucket == "all" else [bucket]:
        mark_done(tmp_path, "57", bucket=name)
    satisfy_gate(tmp_path, "58")

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 1
    assert "00057" in missing[0]


@pytest.mark.parametrize(
    ("name", "accepted"),
    [
        ("00057-a.md", True),
        ("00057-controller-core.md", True),
        ("00057.md", False),
        ("00057-x.txt", False),
        ("00057-x.md.bak", False),
        ("00057_x.md", False),
        ("000570-x.md", False),
        ("0057-x.md", False),
        ("57-x.md", False),
        ("x00057-x.md", False),
        ("nested/00057-x.md", False),
    ],
)
def test_done_file_name_must_be_padded_id_dash_slug_md(
    tmp_path: Path, name: str, accepted: bool
) -> None:
    mark_done(tmp_path, "62")
    entry = tmp_path / PRDS / "done" / name
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text("# PRD 57\n", encoding="utf-8")
    satisfy_gate(tmp_path, "58")

    result = run_tool(tmp_path, "58")

    if accepted:
        assert report(result, 0) == {"ready": True, "prd": "58"}
    else:
        missing = missing_of(result, "58")
        assert len(missing) == 1
        assert "00057" in missing[0]


@pytest.mark.parametrize("kind", ["symlink", "directory", "symlinked-done-dir"])
def test_done_entry_must_be_a_regular_file(tmp_path: Path, kind: str) -> None:
    mark_done(tmp_path, "57", "62", bucket="backlog")
    done = tmp_path / PRDS / "done"
    unmet: tuple[str, ...] = ("57",)
    if kind == "symlinked-done-dir":
        done.symlink_to(tmp_path / PRDS / "backlog", target_is_directory=True)
        unmet = ("57", "62")
    else:
        mark_done(tmp_path, "62")
        entry = done / "00057-slice-57.md"
        if kind == "symlink":
            entry.symlink_to(tmp_path / PRDS / "backlog" / "00057-slice-57.md")
        else:
            entry.mkdir()
    satisfy_gate(tmp_path, "58")

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == len(unmet)
    for index, dep in enumerate(unmet):
        assert padded(dep) in missing[index]


# PRD ID handling


@pytest.mark.parametrize(("prd", "given"), ID_SPELLINGS)
def test_accepts_id_with_or_without_leading_zeros_and_echoes_it(
    tmp_path: Path, prd: str, given: str
) -> None:
    make_ready(tmp_path, prd)

    assert report(run_tool(tmp_path, given), 0) == {"ready": True, "prd": given}


@pytest.mark.parametrize("prd", ["64", "00064"])
def test_echoes_given_id_when_unavailable(tmp_path: Path, prd: str) -> None:
    mark_done(tmp_path, *(done for done in CLOSURE["64"] if done != "58"))
    satisfy_gate(tmp_path, "64")

    missing = missing_of(run_tool(tmp_path, prd), prd)

    assert len(missing) == 1
    assert "00058" in missing[0]


@pytest.mark.parametrize(
    "prd",
    [
        "abc",
        "",
        "00057",
        "00062",
        "00099",
        "63",
        "5",
        "580",
        "5800058",
        "58.0",
        "0x3a",
        "5_8",
        "+58",
        " 58 ",
        "٥٨",  # Arabic-Indic digits for 58
        "000058",  # a supported PRD, but over the five-character limit
        "000065",
    ],
)
def test_unknown_prd(tmp_path: Path, prd: str) -> None:
    mark_done(tmp_path, *CLOSURE["65"])
    satisfy_gate(tmp_path, "61")

    named = [prd.strip()] if prd.strip() else []

    assert_refused(run_tool(tmp_path, prd), *named)


# Artifact gates (PRD 61 and 65)


@pytest.mark.parametrize("prd", ["61", "65"])
@pytest.mark.parametrize("variant", ["relative-single", "absolute-multi-upper"])
def test_artifact_gate_is_met_by_matching_digest_and_evidence(
    tmp_path: Path, prd: str, variant: str
) -> None:
    mark_done(tmp_path, *CLOSURE[prd])
    _, key, tokens = GATES[prd]
    artifact = tmp_path / "artifacts" / f"{key}.json"
    if variant == "relative-single":
        digest = write_artifact(artifact, {"evidence": list(tokens)})
        path = f"artifacts/{key}.json"
    else:
        evidence = ["AP00001", *tokens, "Lantern00001"]
        digest = write_artifact(artifact, {"evidence": evidence, "name": key}).upper()
        path = str(artifact)
    write_config(tmp_path / "ovcaq.toml", gate_config(prd, path, digest))

    assert report(run_tool(tmp_path, prd), 0) == {"ready": True, "prd": prd}


@pytest.mark.parametrize("prd", ["61", "65"])
@pytest.mark.parametrize("case", UNMET_GATE_CASES)
def test_missing_artifact(tmp_path: Path, prd: str, case: str) -> None:
    mark_done(tmp_path, *CLOSURE[prd])
    text = build_unmet_gate(tmp_path, prd, case)
    if text is not None:
        write_config(tmp_path / "ovcaq.toml", text)
    _, key, _ = GATES[prd]

    missing = missing_of(run_tool(tmp_path, prd), prd)

    assert missing
    assert all(key in entry for entry in missing)
    for foreign in foreign_keys(prd):
        assert not any(foreign in entry for entry in missing)
    for dep in DIRECT[prd]:
        assert not any(padded(dep) in entry for entry in missing)


@pytest.mark.parametrize("prd", ["61", "65"])
def test_relative_artifact_path_resolves_against_cwd_not_config_file(
    tmp_path: Path, prd: str
) -> None:
    mark_done(tmp_path, *CLOSURE[prd])
    _, key, tokens = GATES[prd]
    _, _, other_tokens = GATES[OTHER_GATE[prd]]
    digest = write_artifact(
        tmp_path / "artifacts" / f"{key}.json", {"evidence": list(tokens)}
    )
    config = tmp_path / "conf" / "gate.toml"
    decoy = config.parent / "artifacts" / f"{key}.json"
    write_artifact(decoy, {"evidence": list(other_tokens)})
    write_config(config, gate_config(prd, f"artifacts/{key}.json", digest))

    result = run_tool(tmp_path, prd, "--config", str(config))

    assert report(result, 0) == {"ready": True, "prd": prd}


# Config selection and errors


@pytest.mark.parametrize("prd", ["61", "65"])
@pytest.mark.parametrize("satisfied_in", ["explicit", "default"])
def test_explicit_config_replaces_project_config(
    tmp_path: Path, prd: str, satisfied_in: str
) -> None:
    make_ready(tmp_path, prd)
    good = (tmp_path / "ovcaq.toml").read_text(encoding="utf-8")
    explicit = tmp_path / "conf" / "explicit.toml"
    if satisfied_in == "explicit":
        write_config(explicit, good)
        write_config(tmp_path / "ovcaq.toml", "")
    else:
        write_config(explicit, "")
    _, key, _ = GATES[prd]

    result = run_tool(tmp_path, prd, "--config", str(explicit))

    if satisfied_in == "explicit":
        assert report(result, 0) == {"ready": True, "prd": prd}
    else:
        missing = missing_of(result, prd)
        assert missing
        assert all(key in entry for entry in missing)


@pytest.mark.parametrize("prd", ["58", "61", "65"])
@pytest.mark.parametrize(
    "case",
    [
        "missing-explicit",
        "unparseable-default",
        "unparseable-explicit",
        "path-is-int",
        "path-is-list",
        "digest-is-int",
        "table-is-scalar",
    ],
)
def test_config_errors_exit_2_without_stdout(
    tmp_path: Path, prd: str, case: str
) -> None:
    make_ready(tmp_path, prd)
    table, key, _ = GATES[prd]
    explicit = tmp_path / "conf" / "explicit.toml"
    extra: list[str] = []
    named = [str(explicit)]
    if case == "missing-explicit":
        extra = ["--config", str(explicit)]
    elif case == "unparseable-default":
        write_config(tmp_path / "ovcaq.toml", f"[{table}\n{key} = \n")
        named = ["ovcaq.toml"]
    elif case == "unparseable-explicit":
        write_config(explicit, f"[{table}\n{key} = \n")
        extra = ["--config", str(explicit)]
    elif case == "table-is-scalar":
        write_config(tmp_path / "ovcaq.toml", f'{table} = "oops"\n')
        named = [table]
    else:
        name, value = {
            "path-is-int": (key, "5"),
            "path-is-list": (key, json.dumps([f"artifacts/{key}.json"])),
            "digest-is-int": (f"{key}_sha256", "5"),
        }[case]
        text = (tmp_path / "ovcaq.toml").read_text(encoding="utf-8")
        lines = [
            f"{name} = {value}" if line.startswith(f"{name} =") else line
            for line in text.splitlines()
        ]
        write_config(tmp_path / "ovcaq.toml", "\n".join(lines) + "\n")
        named = [name]

    assert_refused(run_tool(tmp_path, prd, *extra), *named)


# Script source


def imported_modules(source: str) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and node.args:
            func = node.func
            name = (
                func.attr
                if isinstance(func, ast.Attribute)
                else getattr(func, "id", "")
            )
            first = node.args[0]
            if name in {"__import__", "import_module"} and isinstance(
                first, ast.Constant
            ):
                modules.add(str(first.value).split(".")[0])
    return modules


def test_script_is_stdlib_only_without_network_or_subprocess() -> None:
    source = TOOL.read_text(encoding="utf-8")

    assert source.splitlines()[0] == "#!/usr/bin/env python3"
    modules = imported_modules(source)
    assert modules
    assert not modules & FORBIDDEN_IMPORTS
    assert modules <= set(sys.stdlib_module_names)


# One digest definition and strict bundle validation

TABLE_58, KEY_58, TOKENS_58 = GATES["58"]
ARTIFACT_58 = f"artifacts/{KEY_58}.json"
CONTROLLER_ARGV = ["autopilot-controller", "serve"]
REQUIRED_BUNDLE_FIELDS = ["protocol_major", "operations", "capabilities"]


def raw_sha256(data: bytes) -> str:
    """The one digest an operator computes: sha256 of the bundle file's bytes."""
    return hashlib.sha256(data).hexdigest()


def stage_bundle(root: Path, body: bytes, pin: str, *, argv: bool = False) -> Path:
    """PRD 58 with every predecessor done, its artifact met and `body` pinned."""
    mark_done(root, *CLOSURE["58"])
    artifact = write_artifact(root / ARTIFACT_58, {"evidence": list(TOKENS_58)})
    bundle = root / BUNDLE_PATH
    bundle.parent.mkdir(parents=True, exist_ok=True)
    bundle.write_bytes(body)
    text = gate_config(
        "58", ARTIFACT_58, artifact, bundle=BUNDLE_PATH, bundle_digest=pin
    )
    if argv:
        text += f"controller_argv = {json.dumps(CONTROLLER_ARGV)}\n"
    write_config(root / "ovcaq.toml", text)
    return bundle


def bundle_body(case: str) -> bytes:
    """Raw bundle bytes; only "fixture" is a valid contract bundle."""
    if case == "fixture":
        return BUNDLE_FIXTURE.read_bytes()
    if case == "null":
        return b"null"
    if case == "empty-object":
        return b"{}"
    data = json.loads(BUNDLE_FIXTURE.read_bytes())
    del data[case.removeprefix("no-")]
    return json.dumps(data, indent=2).encode("utf-8")


def test_prerequisites_and_client_share_one_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The committed pretty-printed fixture, pinned by its raw file bytes."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
    body = BUNDLE_FIXTURE.read_bytes()
    pin = raw_sha256(body)
    # Only a raw-bytes digest can accept this file: its bytes are not canonical.
    assert body != json.dumps(json.loads(body), sort_keys=True).encode("utf-8")
    stage_bundle(tmp_path, body, pin, argv=True)

    assert report(run_tool(tmp_path, "58"), 0) == {"ready": True, "prd": "58"}

    settings = controller_settings(tmp_path)
    assert settings is not None
    assert settings.contract_bundle == tmp_path / BUNDLE_PATH
    assert settings.contract_bundle.read_bytes() == body
    assert settings.bundle_digest == pin
    assert controller_bundle_digest(settings.contract_bundle, pin) == pin


@pytest.mark.parametrize(
    "case",
    ["last-hex-differs", "middle-hex-differs", "truncated-digest", "single-hex"],
)
def test_prerequisites_and_client_share_one_digest_refusing_a_near_miss(
    tmp_path: Path, case: str
) -> None:
    body = BUNDLE_FIXTURE.read_bytes()
    pin = raw_sha256(body)
    near = digest_variant(case, pin)
    # Both consumers compare the whole digest, so a prefix of it pins nothing.
    assert near != pin
    assert re.fullmatch(r"[0-9a-f]{64}", pin)
    bundle = stage_bundle(tmp_path, body, near)

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY_58 not in missing[0]
    with pytest.raises(IncompatibleContractError) as caught:
        controller_bundle_digest(bundle, near)
    assert near in str(caught.value)
    assert pin in str(caught.value)


def test_one_digest_definition_hashes_raw_bytes_not_canonical_json(
    tmp_path: Path,
) -> None:
    """Same JSON, different bytes, so the pin of one must refuse the other."""
    pretty = BUNDLE_FIXTURE.read_bytes()
    canonical = json.dumps(json.loads(pretty), sort_keys=True).encode("utf-8")
    assert json.loads(pretty) == json.loads(canonical)
    assert pretty != canonical
    first, second = tmp_path / "pretty.json", tmp_path / "canonical.json"
    first.write_bytes(pretty)
    second.write_bytes(canonical)

    assert controller_bundle_digest(first) == raw_sha256(pretty)
    assert controller_bundle_digest(second) == raw_sha256(canonical)
    assert controller_bundle_digest(first) != controller_bundle_digest(second)
    # Neither form answers to the other's pin, in either direction.
    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(first, raw_sha256(canonical))
    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(second, raw_sha256(pretty))

    for body, pin in ((canonical, pretty), (pretty, canonical)):
        stage_bundle(tmp_path, body, raw_sha256(pin))
        missing = missing_of(run_tool(tmp_path, "58"), "58")

        assert len(missing) == 1
        assert BUNDLE_KEY in missing[0]
        assert KEY_58 not in missing[0]


@pytest.mark.parametrize(
    ("case", "accepted"),
    [
        ("fixture", True),
        ("null", False),
        ("empty-object", False),
        *((f"no-{field}", False) for field in REQUIRED_BUNDLE_FIELDS),
    ],
)
def test_bundle_rejects_non_contract_json(
    tmp_path: Path, case: str, accepted: bool
) -> None:
    body = bundle_body(case)
    bundle = stage_bundle(tmp_path, body, raw_sha256(body))

    result = run_tool(tmp_path, "58")

    assert "Traceback" not in result.stderr
    if accepted:
        assert report(result, 0) == {"ready": True, "prd": "58"}
        assert controller_bundle_digest(bundle) == raw_sha256(body)
        return
    missing = missing_of(result, "58")
    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY_58 not in missing[0]
    with pytest.raises(IncompatibleContractError):
        controller_bundle_digest(bundle)


# The bundle path earns the same hardening as the artifact path. Content and pin
# are correct in every case below, so only the path check can refuse them.
CAP = 16 * 1024 * 1024
BUNDLE_PATH_CASES = [
    "directory",
    "symlinked-file",
    "symlinked-parent-dir",
    "symlinked-parent-escapes-root",
]


def stage_bundle_elsewhere(root: Path, where: str, pin: str) -> None:
    """PRD 58 ready, with the bundle pinned at the configured path `where`."""
    mark_done(root, *CLOSURE["58"])
    artifact = write_artifact(root / ARTIFACT_58, {"evidence": list(TOKENS_58)})
    write_config(
        root / "ovcaq.toml",
        gate_config("58", ARTIFACT_58, artifact, bundle=where, bundle_digest=pin),
    )


@pytest.mark.parametrize("case", BUNDLE_PATH_CASES)
def test_valid_pinned_bundle_is_refused_when_its_path_is_not_a_plain_file(
    tmp_path: Path, case: str
) -> None:
    body = BUNDLE_FIXTURE.read_bytes()
    pin = raw_sha256(body)
    real = tmp_path / "bundles" / "contract-bundle.json"
    write_artifact(real, body)
    where = "bundles"
    if case == "symlinked-file":
        (real.parent / "mirror.json").symlink_to(real)
        where = "bundles/mirror.json"
    elif case == "symlinked-parent-dir":
        (tmp_path / "exports").symlink_to(real.parent, target_is_directory=True)
        where = "exports/contract-bundle.json"
    elif case == "symlinked-parent-escapes-root":
        outside = tmp_path.parent / f"outside-{tmp_path.name}"
        write_artifact(outside / "contract-bundle.json", body)
        (tmp_path / "exports").symlink_to(outside, target_is_directory=True)
        where = "exports/contract-bundle.json"
    stage_bundle_elsewhere(tmp_path, where, pin)

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY_58 not in missing[0]


@pytest.mark.parametrize(("size", "ready"), [(CAP, True), (CAP + 1, False)])
def test_bundle_is_hashed_and_parsed_from_one_read_under_a_16_mib_cap(
    tmp_path: Path, size: int, ready: bool
) -> None:
    """Padding is valid JSON and correctly pinned, so only the cap refuses it."""
    body = BUNDLE_FIXTURE.read_bytes()
    padded_body = body + b" " * (size - len(body))
    assert len(padded_body) == size
    assert json.loads(padded_body) == json.loads(body)
    stage_bundle(tmp_path, padded_body, raw_sha256(padded_body))

    result = run_tool(tmp_path, "58")

    if ready:
        assert report(result, 0) == {"ready": True, "prd": "58"}
        return
    missing = missing_of(result, "58")
    assert len(missing) == 1
    assert BUNDLE_KEY in missing[0]
    assert KEY_58 not in missing[0]
