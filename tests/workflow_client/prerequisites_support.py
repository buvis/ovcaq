"""Shared data and helpers for the autopilot-prerequisites CLI tests."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

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
# table, path key, every evidence token the gate requires
GATES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "58": ("workflow", "controller_artifact", ("core", "jobs", "reviews", "records")),
    "61": ("autopilot", "plugin_artifact", ("AP00017",)),
    "65": ("operator", "client_artifact", ("Lantern00003",)),
}
OTHER_GATE = {"58": "61", "61": "65", "65": "61"}
# PRDs that also probe a read-only precondition path, and the key naming it.
BUNDLE_KEY = "contract_bundle"
BUNDLE_PATH = "artifacts/contract-bundle.json"
PRECONDITION = {"58": BUNDLE_KEY}
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


def foreign_keys(prd: str) -> tuple[str, ...]:
    """Config keys that belong to another PRD, so they must never leak."""
    keys = [key for other, (_, key, _) in GATES.items() if other != prd]
    if prd not in PRECONDITION:
        keys.append(BUNDLE_KEY)
    return tuple(keys)


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


def write_bundle(root: Path, name: str = BUNDLE_PATH, body: str = "{not json") -> Path:
    """A precondition bundle whose body never parses, so a read would show."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def gate_config(
    prd: str, path: str | None, digest: str | None, *, bundle: str | None = None
) -> str:
    table, key, _ = GATES[prd]
    lines = [f"[{table}]"]
    if path is not None:
        lines.append(f"{key} = {json.dumps(path)}")
    if digest is not None:
        lines.append(f"{key}_sha256 = {json.dumps(digest)}")
    if bundle is not None:
        lines.append(f"{BUNDLE_KEY} = {json.dumps(bundle)}")
    return "\n".join(lines) + "\n"


def write_config(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def satisfy_gate(root: Path, prd: str) -> None:
    if prd not in GATES:
        return
    _, key, tokens = GATES[prd]
    digest = write_artifact(
        root / "artifacts" / f"{key}.json", {"evidence": list(tokens)}
    )
    bundle = None
    if prd in PRECONDITION:
        write_bundle(root)
        bundle = BUNDLE_PATH
    write_config(
        root / "ovcaq.toml",
        gate_config(prd, f"artifacts/{key}.json", digest, bundle=bundle),
    )


def make_ready(root: Path, prd: str) -> None:
    mark_done(root, *CLOSURE[prd])
    satisfy_gate(root, prd)


def near_misses(token: str) -> list[str]:
    """Tokens sharing a prefix, suffix or spelling with the real one."""
    variants = [
        token + "0",
        "X" + token,
        token[:-1],
        token.swapcase(),
        token.capitalize(),
    ]
    return [variant for variant in variants if variant != token]


def unmet_payloads(prd: str) -> dict[str, object]:
    _, key, tokens = GATES[prd]
    _, _, other_tokens = GATES[OTHER_GATE[prd]]
    return {
        "no-evidence-key": {"name": key},
        "empty-evidence": {"evidence": []},
        "evidence-string": {"evidence": tokens[0]},
        "nested-evidence": {"evidence": [list(tokens)]},
        "near-miss-evidence": {"evidence": near_misses(tokens[0]) + list(tokens[1:])},
        "other-prd-evidence": {"evidence": list(other_tokens)},
        "evidence-dict": {"evidence": {token: False for token in tokens}},
        "not-json": b"{x",
        "top-level-list": list(tokens),
    }


def build_unmet_gate(root: Path, prd: str, case: str) -> str | None:
    table, key, tokens = GATES[prd]
    other_table, _, _ = GATES[OTHER_GATE[prd]]
    artifact = root / "artifacts" / f"{key}.json"
    digest = write_artifact(
        artifact, unmet_payloads(prd).get(case, {"evidence": list(tokens)})
    )
    path = f"artifacts/{key}.json"
    # A satisfied precondition keeps every case about the artifact alone.
    bundle = None
    if prd in PRECONDITION:
        write_bundle(root)
        bundle = BUNDLE_PATH

    def config(where: str | None, hexdigest: str | None) -> str:
        return gate_config(prd, where, hexdigest, bundle=bundle)

    if case == "no-config-file":
        return None
    if case == "no-table":
        return ""
    if case == "wrong-table":
        return config(path, digest).replace(f"[{table}]", f"[{other_table}]")
    if case == "no-path-key":
        return config(None, digest)
    if case == "no-digest-key":
        return config(path, None)
    if case == "missing-file":
        return config("artifacts/absent.json", digest)
    if case == "directory":
        return config("artifacts", digest)
    if case == "symlinked-file":
        (root / "artifacts" / "linked.json").symlink_to(artifact)
        return config("artifacts/linked.json", digest)
    if case == "symlinked-parent-dir":
        (root / "linked").symlink_to(root / "artifacts", target_is_directory=True)
        return config(f"linked/{key}.json", digest)
    if case == "last-hex-differs":
        return config(path, digest[:-1] + ("1" if digest[-1] == "0" else "0"))
    if case == "digest-mismatch":
        return config(path, hashlib.sha256(b"other").hexdigest())
    if case == "truncated-digest":
        return config(path, digest[:-1])
    return config(path, digest)


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
