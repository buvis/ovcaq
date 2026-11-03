"""FT-04R9 adjudication: syscall interleaving and settled-scope observations."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore
from ovcaq.workflow import _files, records
from ovcaq.workflow.frontmatter import apply_to_store
from ovcaq.workflow.resume import resume_target


def process_lock_race():
    with tempfile.TemporaryDirectory(prefix="ft04r9-process-lock-") as name:
        root = Path(name).resolve()
        native_replace = os.replace
        rival = None

        def replace(*args, **kwargs):
            nonlocal rival
            if rival is None and args[1] == "batch-deferred.json":
                lock = root / "deferred/batch-deferred.json.lock"
                lock.rename(lock.with_suffix(".retained"))
                program = (
                    "import sys; from pathlib import Path; "
                    "from ovcaq.workflow.records import record_defer; "
                    "record_defer(Path(sys.argv[1]), '00004.md', 'batch', "
                    "{'op_id':'second'}); print('committed second')"
                )
                rival = subprocess.run(
                    [sys.executable, "-B", "-c", program, str(root)],
                    capture_output=True, text=True, timeout=5, check=False,
                    env={**os.environ, "XDG_CONFIG_HOME": str(root / "xdg")},
                )
                assert rival.returncode == 0, rival.stderr
            native_replace(*args, **kwargs)

        error = None
        with patch.object(_files.os, "replace", replace):
            try:
                records.record_defer(root, "00004.md", "batch", {"op_id": "first"})
            except OSError as exc:
                error = str(exc)
        before = [row["op_id"] for row in records.load_deferred_records(root, "batch")]
        records.record_defer(root, "00004.md", "batch", {"op_id": "first"})
        return {
            "case": "real-process-rival-at-replace", "error": error,
            "rival_exit": rival.returncode, "rival_stdout": rival.stdout,
            "before_retry": before,
            "after_retry": [row["op_id"] for row in records.load_deferred_records(root, "batch")],
        }


def frontmatter_policy(mode, completed):
    with tempfile.TemporaryDirectory(prefix="ft04r9-frontmatter-") as name:
        root = Path(name).resolve()
        state = new_state(repo_root=root)
        state["work"]["prd"] = "00004.md"
        state["batch"]["catchup"]["completed_at"] = completed
        store = StateStore(root / "state.json")
        store.initialize(state)
        result = apply_to_store(store, f"---\ncatchup: {mode}\ndesign: skip\n---\n", prd="00004.md")
        second = apply_to_store(store, "---\ncatchup: run\n---\n", prd="00004.md")
        return {
            "case": f"frontmatter-{mode}", "returned_fields": result.fields,
            "committed_catchup": result.state["batch"]["catchup"],
            "resume": resume_target(result.state), "second_warnings": second.warnings,
        }


def missing_source():
    spec = importlib.util.spec_from_file_location(
        "cycle08", Path(__file__).with_name("00004-cycle-08-probes.py")
    )
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    with tempfile.TemporaryDirectory(prefix="ft04r9-absent-source-") as name:
        store, paths, runtime = old.environment(Path(name).resolve())
        source = paths.wip / old.PRD
        source.unlink()
        errors = []
        args = dict(store=store, paths=paths, runtime_root=runtime, prd=old.PRD,
                    site="probe", detail="identity check",
                    operation_id_factory=lambda: "missing-source-09")
        try:
            records.stall(**args)
        except OSError as exc:
            errors.append(str(exc))
        before = store.path.read_bytes()
        source.write_text("later file without original identity\n")
        try:
            records.stall(**args)
        except OSError as exc:
            errors.append(str(exc))
        state = store.read()
        return {"case": "missing-source-refusal", "errors": errors,
                "artifact": state["recovery"]["operation"]["artifact"],
                "tasks": len(state["tasks"]), "restored_input_preserved": source.exists(),
                "retry_state_bytes_preserved": store.path.read_bytes() == before}


if __name__ == "__main__":
    print(json.dumps([
        process_lock_race(), frontmatter_policy("skip", None),
        frontmatter_policy("force", "2026-09-05T10:00:00Z"), missing_source(),
    ], indent=2))
