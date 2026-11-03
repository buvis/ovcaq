"""Review probe: ancestor replacement during the last identity-validation pass."""
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


def probe(replay: bool, inject_at: int | None = None) -> dict[str, object]:
    from ovcaq.workflow import _files
    from ovcaq.workflow.records import record_defer

    with tempfile.TemporaryDirectory(prefix="ovcaq-r16-stat-", dir="/private/tmp") as folder:
        project = Path(folder)
        ancestor = project / "ancestor"
        runtime = ancestor / "runtime"
        displaced = project / "displaced"
        ledger = runtime / "deferred/batch-deferred.json"
        runtime.mkdir(parents=True)
        record = {"op_id": "final-stat-probe"}
        seed = record_defer(runtime, "00004-a.md", "batch", record).read_bytes() if replay else None
        real_stat, real_fsync = os.stat, os.fsync
        checks = 0
        events: list[dict[str, object]] = []

        def identity(path: Path) -> list[int]:
            value = real_stat(path)
            return [value.st_dev, value.st_ino]

        original_runtime = identity(runtime)
        original_ancestor = identity(ancestor)
        original_parent = identity(project)

        def observe_fsync(descriptor: int) -> None:
            value = os.fstat(descriptor)
            real_fsync(descriptor)
            events.append({"event": "fsync", "directory": stat.S_ISDIR(value.st_mode),
                           "identity": [value.st_dev, value.st_ino]})

        def interleave_stat(path: object, *args: object, **kwargs: object) -> os.stat_result:
            nonlocal checks
            value = real_stat(path, *args, **kwargs)
            if path == ancestor and sys._getframe(1).f_code.co_name == "verify_ancestry":
                checks += 1
                events.append({"event": "ancestor-check", "number": checks})
                if checks == inject_at:
                    ancestor.rename(displaced)
                    ancestor.mkdir()
                    (displaced / "runtime").rename(runtime)
                    events.append({"event": "reparent", "check": checks,
                                   "old_ancestor": original_ancestor,
                                   "new_ancestor": identity(ancestor),
                                   "same_runtime": identity(runtime) == original_runtime})
            return value

        with patch.object(os, "stat", interleave_stat), patch.object(os, "fsync", observe_fsync):
            try:
                result = record_defer(runtime, "00004-a.md", "batch", record)
                outcome, error = "success", None
            except Exception as caught:
                result, outcome, error = None, "refused", repr(caught)
        events.append({"event": "returned", "outcome": outcome})
        swaps = [i for i, e in enumerate(events) if e["event"] == "reparent"]
        after = events[swaps[0] + 1:] if swaps else []
        return {"replay": replay, "inject_at": inject_at, "checks": checks,
                "outcome": outcome, "error": error, "events": events,
                "module": _files.__file__, "prefix": sys.prefix,
                "module_sha256": hashlib.sha256(Path(_files.__file__).read_bytes()).hexdigest(),
                "ancestor_replaced": identity(ancestor) != original_ancestor,
                "runtime_preserved": identity(runtime) == original_runtime,
                "ancestor_parent_fsync_after": any(e.get("identity") == original_parent for e in after),
                "replacement_ancestor_fsync_after": any(e.get("identity") == identity(ancestor) for e in after),
                "ledger_exists": ledger.exists(), "ledger": json.loads(ledger.read_text()) if ledger.exists() else None,
                "seed_preserved": ledger.read_bytes() == seed if seed is not None else None,
                "returned_path_exists": result.exists() if result else None,
                "limit": "Real rename/reparent and fsync tracing, injected after final ancestor stat but before its return. No physical power-loss simulation; external reparent occurs after ledger publication fsync."}


def main() -> None:
    if len(sys.argv) > 1:
        replay = sys.argv[1] == "replay"
        baseline = probe(replay)
        trial = probe(replay, int(baseline["checks"]))
        print(json.dumps({"baseline": baseline, "trial": trial}))
        return
    root = Path(__file__).resolve().parents[3]
    wheel = next((root / "dist").glob("*.whl"))
    rows = []
    with tempfile.TemporaryDirectory(prefix="ovcaq-r16-installed-", dir="/private/tmp") as folder:
        environment = Path(folder) / "venv"
        subprocess.run(["uv", "--no-cache", "venv", "--python", str(root / ".venv/bin/python"),
                        str(environment)], check=True, timeout=60)
        python = environment / "bin/python"
        subprocess.run(["uv", "--no-cache", "pip", "install", "--python", str(python),
                        "--no-deps", "--no-index", str(wheel)], check=True, timeout=60)
        for mode in ("direct", "replay"):
            result = subprocess.run([str(python), "-I", str(Path(__file__).resolve()), mode],
                                    cwd=folder, capture_output=True, text=True, check=True, timeout=30)
            row = json.loads(result.stdout)
            for result_row in row.values():
                assert Path(result_row["module"]).is_relative_to(environment)
                assert "site-packages" in Path(result_row["module"]).parts
                assert result_row["module_sha256"] == hashlib.sha256((root / "src/ovcaq/workflow/_files.py").read_bytes()).hexdigest()
            rows.append(row)
    (root / "dev/local/reviews/00004-cycle-16-final-stat-probe.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps([{k: v for k, v in r["trial"].items() if k != "events"} for r in rows], indent=2))


if __name__ == "__main__":
    main()

