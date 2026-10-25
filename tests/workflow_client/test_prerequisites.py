from __future__ import annotations

import ast
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "autopilot-prerequisites"
PRDS = Path("docs") / "dev" / "project-management" / "prds"

DIRECT: dict[str, tuple[str, ...]] = {
    "58": ("57", "62"),
    "59": ("58", "63"),
    "60": ("59",),
    "61": ("60",),
    "64": ("58",),
    "65": ("60", "61", "64"),
}
# Full predecessor closure, so tests hold whether the tool checks direct
# dependencies only or walks the graph transitively.
CLOSURE: dict[str, tuple[str, ...]] = {
    "58": ("57", "62"),
    "59": ("57", "62", "58", "63"),
    "60": ("57", "62", "58", "63", "59"),
    "61": ("57", "62", "58", "63", "59", "60"),
    "64": ("57", "62", "58"),
    "65": ("57", "62", "58", "63", "59", "60", "61", "64"),
}
GATES: dict[str, tuple[str, str, str]] = {
    "61": ("autopilot", "plugin_artifact", "AP00017"),
    "65": ("operator", "client_artifact", "Lantern00003"),
}
OTHER_GATE = {"61": "65", "65": "61"}
DEPENDENCY_CASES = [(prd, dep) for prd, deps in DIRECT.items() for dep in deps]
FORBIDDEN_IMPORTS = {"socket", "urllib", "http", "requests", "subprocess", "ovcaq"}


def snapshot(root: Path) -> dict[str, tuple[int, int, int]]:
    # Root's own mtime catches a file created and deleted directly in cwd.
    info = root.lstat()
    entries = {".": (stat.S_IFMT(info.st_mode), info.st_size, info.st_mtime_ns)}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            info = path.lstat()
            entries[str(path.relative_to(root))] = (
                stat.S_IFMT(info.st_mode),
                info.st_size,
                info.st_mtime_ns,
            )
    return entries


def run_tool(root: Path, prd: str, *extra: str) -> subprocess.CompletedProcess[str]:
    """Run the tool from the project root and prove it wrote nothing there."""
    # A missing script also exits 2 with empty stdout; never let that pass.
    assert TOOL.is_file()
    before = snapshot(root)
    result = subprocess.run(
        [sys.executable, str(TOOL), "--prd", prd, *extra],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert snapshot(root) == before
    return result


def report(result: subprocess.CompletedProcess[str], code: int) -> dict[str, object]:
    assert result.returncode == code, result.stderr
    lines = result.stdout.splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert isinstance(payload, dict)
    return payload


def missing_of(result: subprocess.CompletedProcess[str], prd: str) -> list[str]:
    payload = report(result, 1)
    assert set(payload) == {"ready", "prd", "missing"}
    assert payload["ready"] is False
    assert payload["prd"] == prd
    missing = payload["missing"]
    assert isinstance(missing, list)
    assert all(isinstance(entry, str) for entry in missing)
    return missing


def assert_refused(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip() != ""


def padded(prd: str) -> str:
    return f"{int(prd):05d}"


def mark_done(root: Path, *prds: str, bucket: str = "done") -> None:
    directory = root / PRDS / bucket
    directory.mkdir(parents=True, exist_ok=True)
    for prd in prds:
        (directory / f"{padded(prd)}-slice-{prd}.md").write_text(
            f"# PRD {prd}\n", encoding="utf-8"
        )


def write_artifact(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (
        payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    )
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def gate_config(prd: str, path: str | None, digest: str | None) -> str:
    table, key, _ = GATES[prd]
    lines = [f"[{table}]"]
    if path is not None:
        lines.append(f"{key} = {json.dumps(path)}")
    if digest is not None:
        lines.append(f"{key}_sha256 = {json.dumps(digest)}")
    return "\n".join(lines) + "\n"


def write_config(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def satisfy_gate(root: Path, prd: str) -> None:
    if prd not in GATES:
        return
    _, key, token = GATES[prd]
    digest = write_artifact(root / "artifacts" / f"{key}.json", {"evidence": [token]})
    write_config(root / "ovcaq.toml", gate_config(prd, f"artifacts/{key}.json", digest))


def make_ready(root: Path, prd: str) -> None:
    mark_done(root, *CLOSURE[prd])
    satisfy_gate(root, prd)


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


def test_prd_58_is_gated_on_57_and_62_only(tmp_path: Path) -> None:
    mark_done(tmp_path, "57", "62")

    assert report(run_tool(tmp_path, "58"), 0) == {"ready": True, "prd": "58"}


def test_missing_done_directory_leaves_every_predecessor_unmet_in_graph_order(
    tmp_path: Path,
) -> None:
    mark_done(tmp_path, "57", "62", bucket="backlog")

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
    _, other_key, _ = GATES[OTHER_GATE[prd]]

    missing = missing_of(run_tool(tmp_path, prd), prd)

    for index, dep in enumerate(unmet):
        assert padded(dep) in missing[index]
    artifact_entries = missing[len(unmet) :]
    assert artifact_entries
    assert all(key in entry for entry in artifact_entries)
    assert not any(other_key in entry for entry in missing)


@pytest.mark.parametrize("bucket", ["backlog", "wip", "hold", "all"])
def test_predecessor_outside_done_is_never_accepted(
    tmp_path: Path, bucket: str
) -> None:
    mark_done(tmp_path, "62")
    for name in ["backlog", "wip", "hold"] if bucket == "all" else [bucket]:
        mark_done(tmp_path, "57", bucket=name)

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

    missing = missing_of(run_tool(tmp_path, "58"), "58")

    assert len(missing) == len(unmet)
    for index, dep in enumerate(unmet):
        assert padded(dep) in missing[index]


# PRD ID handling


@pytest.mark.parametrize("prd", ["58", "058", "00058"])
def test_accepts_id_with_or_without_leading_zeros_and_echoes_it(
    tmp_path: Path, prd: str
) -> None:
    mark_done(tmp_path, "57", "62")

    assert report(run_tool(tmp_path, prd), 0) == {"ready": True, "prd": prd}


@pytest.mark.parametrize("prd", ["64", "00064"])
def test_echoes_given_id_when_unavailable(tmp_path: Path, prd: str) -> None:
    mark_done(tmp_path, "57", "62")

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
    ],
)
def test_unknown_prd(tmp_path: Path, prd: str) -> None:
    mark_done(tmp_path, *CLOSURE["65"])
    satisfy_gate(tmp_path, "61")

    assert_refused(run_tool(tmp_path, prd))


# Artifact gates (PRD 61 and 65)


@pytest.mark.parametrize("prd", ["61", "65"])
@pytest.mark.parametrize("variant", ["relative-single", "absolute-multi-upper"])
def test_artifact_gate_is_met_by_matching_digest_and_evidence(
    tmp_path: Path, prd: str, variant: str
) -> None:
    mark_done(tmp_path, *CLOSURE[prd])
    _, key, token = GATES[prd]
    artifact = tmp_path / "artifacts" / f"{key}.json"
    if variant == "relative-single":
        digest = write_artifact(artifact, {"evidence": [token]})
        path = f"artifacts/{key}.json"
    else:
        evidence = ["AP00001", token, "Lantern00001"]
        digest = write_artifact(artifact, {"evidence": evidence, "name": key}).upper()
        path = str(artifact)
    write_config(tmp_path / "ovcaq.toml", gate_config(prd, path, digest))

    assert report(run_tool(tmp_path, prd), 0) == {"ready": True, "prd": prd}


def build_unmet_gate(root: Path, prd: str, case: str) -> str | None:
    table, key, token = GATES[prd]
    other_table, _, other_token = GATES[OTHER_GATE[prd]]
    payloads: dict[str, object] = {
        "no-evidence-key": {"name": key},
        "empty-evidence": {"evidence": []},
        "evidence-string": {"evidence": token},
        "nested-evidence": {"evidence": [[token]]},
        "near-miss-evidence": {
            "evidence": [token + "0", token.lower(), "X" + token, token[:-1]]
        },
        "other-prd-evidence": {"evidence": [other_token]},
        "evidence-dict": {"evidence": {token: False}},
        "not-json": b"{x",
        "top-level-list": [token],
    }
    artifact = root / "artifacts" / f"{key}.json"
    digest = write_artifact(artifact, payloads.get(case, {"evidence": [token]}))
    path = f"artifacts/{key}.json"
    if case == "no-config-file":
        return None
    if case == "no-table":
        return ""
    if case == "wrong-table":
        return gate_config(prd, path, digest).replace(f"[{table}]", f"[{other_table}]")
    if case == "no-path-key":
        return gate_config(prd, None, digest)
    if case == "no-digest-key":
        return gate_config(prd, path, None)
    if case == "missing-file":
        return gate_config(prd, "artifacts/absent.json", digest)
    if case == "directory":
        return gate_config(prd, "artifacts", digest)
    if case == "symlinked-file":
        (root / "artifacts" / "linked.json").symlink_to(artifact)
        return gate_config(prd, "artifacts/linked.json", digest)
    if case == "symlinked-parent-dir":
        (root / "linked").symlink_to(root / "artifacts", target_is_directory=True)
        return gate_config(prd, f"linked/{key}.json", digest)
    if case == "last-hex-differs":
        return gate_config(prd, path, digest[:-1] + ("1" if digest[-1] == "0" else "0"))
    if case == "digest-mismatch":
        return gate_config(prd, path, hashlib.sha256(b"other").hexdigest())
    if case == "truncated-digest":
        return gate_config(prd, path, digest[:-1])
    return gate_config(prd, path, digest)


UNMET_GATE_CASES = [
    "no-config-file",
    "no-table",
    "wrong-table",
    "no-path-key",
    "no-digest-key",
    "missing-file",
    "directory",
    "symlinked-file",
    "symlinked-parent-dir",
    "digest-mismatch",
    "truncated-digest",
    "last-hex-differs",
    "no-evidence-key",
    "empty-evidence",
    "evidence-string",
    "evidence-dict",
    "nested-evidence",
    "near-miss-evidence",
    "other-prd-evidence",
    "not-json",
    "top-level-list",
]


@pytest.mark.parametrize("prd", ["61", "65"])
@pytest.mark.parametrize("case", UNMET_GATE_CASES)
def test_missing_artifact(tmp_path: Path, prd: str, case: str) -> None:
    mark_done(tmp_path, *CLOSURE[prd])
    text = build_unmet_gate(tmp_path, prd, case)
    if text is not None:
        write_config(tmp_path / "ovcaq.toml", text)
    _, key, _ = GATES[prd]
    _, other_key, _ = GATES[OTHER_GATE[prd]]

    missing = missing_of(run_tool(tmp_path, prd), prd)

    assert missing
    assert all(key in entry for entry in missing)
    assert not any(other_key in entry for entry in missing)
    for dep in DIRECT[prd]:
        assert not any(padded(dep) in entry for entry in missing)


@pytest.mark.parametrize("prd", ["61", "65"])
def test_relative_artifact_path_resolves_against_cwd_not_config_file(
    tmp_path: Path, prd: str
) -> None:
    mark_done(tmp_path, *CLOSURE[prd])
    _, key, token = GATES[prd]
    _, _, other_token = GATES[OTHER_GATE[prd]]
    digest = write_artifact(
        tmp_path / "artifacts" / f"{key}.json", {"evidence": [token]}
    )
    config = tmp_path / "conf" / "gate.toml"
    decoy = config.parent / "artifacts" / f"{key}.json"
    write_artifact(decoy, {"evidence": [other_token]})
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


@pytest.mark.parametrize("prd", ["61", "65"])
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
    if case == "missing-explicit":
        extra = ["--config", str(explicit)]
    elif case == "unparseable-default":
        write_config(tmp_path / "ovcaq.toml", f"[{table}\n{key} = \n")
    elif case == "unparseable-explicit":
        write_config(explicit, f"[{table}\n{key} = \n")
        extra = ["--config", str(explicit)]
    elif case == "table-is-scalar":
        write_config(tmp_path / "ovcaq.toml", f'{table} = "oops"\n')
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

    assert_refused(run_tool(tmp_path, prd, *extra))


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
