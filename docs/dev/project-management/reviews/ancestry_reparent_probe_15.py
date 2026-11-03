"""Observe ancestor replacement while preserving the runtime directory inode."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


def identity(path: Path) -> list[int]:
    value = path.stat()
    return [value.st_dev, value.st_ino]


def probe(replay: bool) -> dict[str, object]:
    from ovcaq.workflow import _files
    from ovcaq.workflow.records import record_defer

    with tempfile.TemporaryDirectory(prefix="ovcaq-r15-reparent-", dir="/private/tmp") as folder:
        project = Path(folder)
        ancestor = project / "ancestor"
        runtime = ancestor / "runtime"
        displaced = project / "displaced"
        ledger = runtime / "deferred/batch-deferred.json"
        runtime.mkdir(parents=True)
        record = {"op_id": "reparent-probe"}
        seed = record_defer(runtime, "00004-a.md", "batch", record).read_bytes() if replay else None
        original_runtime = identity(runtime)
        original_ancestor = identity(ancestor)
        confirmation_parent = identity(project)
        real_open, real_fsync = os.open, os.fsync
        replaced = False
        events = []

        def observe_fsync(descriptor: int) -> None:
            value = os.fstat(descriptor)
            real_fsync(descriptor)
            if stat.S_ISDIR(value.st_mode):
                events.append({"event": "fsync", "identity": [value.st_dev, value.st_ino]})

        def interleave_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            nonlocal replaced
            if os.fsdecode(path) == ledger.name and not replaced:
                ancestor.rename(displaced)
                ancestor.mkdir()
                (displaced / "runtime").rename(runtime)
                replaced = True
                events.append({"event": "replace-ancestor-and-reparent", "old_ancestor": original_ancestor,
                               "new_ancestor": identity(ancestor), "runtime": identity(runtime)})
            return real_open(path, flags, *args, **kwargs)

        with patch.object(os, "open", interleave_open), patch.object(os, "fsync", observe_fsync):
            try:
                result = record_defer(runtime, "00004-a.md", "batch", record)
                status, error = "success", None
            except Exception as caught:
                result, status, error = None, "refused", repr(caught)
        index = next(i for i, row in enumerate(events) if row["event"] == "replace-ancestor-and-reparent")
        return {"replay": replay, "status": status, "error": error,
                "module": _files.__file__, "prefix": sys.prefix,
                "module_sha256": hashlib.sha256(Path(_files.__file__).read_bytes()).hexdigest(),
                "ancestor_replaced": identity(ancestor) != original_ancestor,
                "runtime_identity_preserved": identity(runtime) == original_runtime,
                "ancestor_parent_confirmed_before": any(e.get("identity") == confirmation_parent for e in events[:index]),
                "ancestor_parent_confirmed_after": any(e.get("identity") == confirmation_parent for e in events[index+1:]),
                "replacement_ancestor_confirmed_after": any(e.get("identity") == identity(ancestor) for e in events[index+1:]),
                "returned_path_exists": result.exists() if result else None,
                "ledger": json.loads(ledger.read_text()) if ledger.exists() else None,
                "seed_preserved": ledger.read_bytes() == seed if seed is not None else None,
                "events": events,
                "limit": "Real filesystem rename/reparent and fsync observations; no simulated physical power loss."}


def main() -> None:
    if len(sys.argv) > 1:
        print(json.dumps(probe(sys.argv[1] == "replay")))
        return
    root = Path(__file__).resolve().parents[3]
    wheel = next((root / "dist").glob("*.whl"))
    with tempfile.TemporaryDirectory(prefix="ovcaq-r15-installed-", dir="/private/tmp") as folder:
        environment = Path(folder) / "venv"
        subprocess.run(["uv", "--no-cache", "venv", "--python", str(root / ".venv/bin/python"), str(environment)], check=True, timeout=60)
        python = environment / "bin/python"
        subprocess.run(["uv", "--no-cache", "pip", "install", "--python", str(python), "--no-deps", "--no-index", str(wheel)], check=True, timeout=60)
        rows = []
        for mode in ("direct", "replay"):
            result = subprocess.run([str(python), "-I", str(Path(__file__).resolve()), mode], cwd=folder, capture_output=True, text=True, check=True, timeout=30)
            row = json.loads(result.stdout)
            assert Path(row["module"]).is_relative_to(environment)
            assert "site-packages" in Path(row["module"]).parts
            assert row["module_sha256"] == hashlib.sha256((root / "src/ovcaq/workflow/_files.py").read_bytes()).hexdigest()
            rows.append(row)
        print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
