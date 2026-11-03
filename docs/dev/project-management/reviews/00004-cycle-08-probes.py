"""FT-04R8 coordinator observations; all mutations use disposable fixtures."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from ovcaq.state.schema import new_state, validate_state
from ovcaq.state.store import StateStore
from ovcaq.workflow import records, reports
from ovcaq.workflow.paths import resolve_lifecycle_paths

PRD = "00004-workflow-core-v1.md"


def environment(root: Path):
    paths = resolve_lifecycle_paths(root, Path("prds"))
    paths.wip.mkdir(parents=True)
    (paths.wip / PRD).write_text("original PRD work\n")
    runtime = root / "runtime"
    runtime.mkdir()
    state = new_state(repo_root=root)
    state["batch"].update(id="review-08", status="running", started_at="2026-09-05T10:00:00Z")
    state["work"].update(prd=PRD, tasks_total=1)
    state["tasks"] = [{
        "id": 1, "name": "unfinished work", "description": "preserve on conflict",
        "active_form": "Working", "status": "in_progress", "blocked_by": [],
        "tier": None, "files_touched": None, "public_contract_edit": None,
        "estimates": {"input_tokens": None, "context_peak": None},
        "attempts": [], "metadata": {},
    }]
    store = StateStore(runtime / "state.json")
    store.initialize(state)
    return store, paths, runtime


def run(kind: str, replacement: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="ft04r8-") as temporary:
        root = Path(temporary).resolve()
        store, paths, runtime = environment(root)
        retained = root / "original-retained.md"
        native_rename = records.rename_exclusive

        def replace(path: Path) -> None:
            path.rename(retained)
            path.write_text("different concurrent PRD\n")

        def before_rename(*args, **kwargs) -> None:
            if replacement == "source-before-rename":
                replace(paths.wip / PRD)
            native_rename(*args, **kwargs)

        def boundary(reached: records.SagaBoundary) -> None:
            if replacement == "held-after-rename" and reached == records.SagaBoundary.AFTER_RENAME_BEFORE_DIRECTORY_FSYNC:
                replace(paths.hold / PRD)
            if replacement == "held-across-restart" and reached == records.SagaBoundary.AFTER_APPEND_BEFORE_COMMIT:
                raise RuntimeError("simulated interruption")

        kwargs = dict(store=store, paths=paths, runtime_root=runtime,
                      operation_id_factory=lambda: "probe-08", boundary_hook=boundary,
                      now=lambda: "2026-09-05T10:00:00Z")
        if kind == "stall":
            kwargs.update(prd=PRD, site="probe", detail="identity check")
        error = None
        try:
            with patch.object(records, "rename_exclusive", before_rename):
                try:
                    getattr(records, kind)(**kwargs)
                except RuntimeError:
                    if replacement != "held-across-restart":
                        raise
                    assert store.read()["recovery"]["operation"]["step"] == "recorded"
                    replace(paths.hold / PRD)
                    kwargs["boundary_hook"] = None
                    getattr(records, kind)(**kwargs)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        state = store.read()
        return {
            "case": f"{kind}/{replacement}", "error": error,
            "held_text": (paths.hold / PRD).read_text(),
            "original_retained": retained.read_text(), "tasks": len(state["tasks"]),
            "recovery": state["recovery"]["operation"],
            "ledger_exists": (runtime / "deferred/review-08-deferred.json").exists(),
        }


def ledger_lock_replacement() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="ft04r8-ledger-") as temporary:
        runtime = Path(temporary).resolve()
        second_returned = False

        def boundary(reached: records.DeferBoundary) -> None:
            nonlocal second_returned
            if reached != records.DeferBoundary.BEFORE_PUBLISH:
                return
            lock = runtime / "deferred/review-08-deferred.json.lock"
            lock.rename(lock.with_suffix(".retained"))
            records.record_defer(runtime, PRD, "review-08", {"op_id": "second"})
            second_returned = True

        records.record_defer(runtime, PRD, "review-08", {"op_id": "first"}, boundary_hook=boundary)
        rows = records.load_deferred_records(runtime, "review-08")
        return {"case": "ledger-lock-replaced-before-publish", "second_append_returned_success": second_returned,
                "final_operation_ids": [row["op_id"] for row in rows]}


def report_other_prd() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="ft04r8-report-") as temporary:
        root = Path(temporary).resolve()
        store, _paths, runtime = environment(root)
        state = store.read()
        earlier = "00003-earlier.md"
        detail = "critical deferred detail for earlier PRD"
        record = {"op_id": "older-record", "prd": earlier, "type": "stall", "site": "design_gate", "detail": detail}
        path = reports.publish_report(runtime, state, (record,))
        text = path.read_text()
        return {"case": "report-non-active-deferred-prd", "deferred_count_present": "- Deferred records: 1" in text,
                "earlier_prd_present": earlier in text, "detail_present": detail in text,
                "operation_id_present": "older-record" in text}


def corrupt_ledger() -> list[dict[str, object]]:
    rows = []
    for case, content in (
        ("duplicate-key", '{"batch_id":"review-08","items":[{"op_id":"keep-me","prd":"00003-earlier.md","detail":"retained finding"}],"items":[]}'),
        ("deep-json", '{"batch_id":"review-08","items":[{"op_id":"deep","data":' + '[' * 10000 + '0' + ']' * 10000 + '}]}'),
    ):
        with tempfile.TemporaryDirectory(prefix="ft04r8-corrupt-") as temporary:
            runtime = Path(temporary).resolve()
            target = runtime / "deferred/review-08-deferred.json"
            target.parent.mkdir()
            target.write_text(content)
            error = None
            try:
                records.record_defer(runtime, PRD, "review-08", {"op_id": "new"})
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
            rows.append({"case": f"deferred-{case}", "error": error, "accepted": error is None,
                         "ledger_bytes_preserved": target.read_text() == content,
                         "retained_record_present": "keep-me" in target.read_text()})
    return rows


def deep_ledger_cli() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="ft04r8-cli-") as temporary:
        root = Path(temporary).resolve()
        store, _paths, runtime = environment(root)
        ledger = runtime / "deferred/review-08-deferred.json"
        ledger.parent.mkdir()
        payload = '{"batch_id":"review-08","items":[{"op_id":"deep","data":' + '[' * 10000 + '0' + ']' * 10000 + '}]}'
        ledger.write_text(payload)
        before = store.path.read_bytes()
        result = subprocess.run([sys.executable, "-m", "ovcaq", "--root", str(root), "--json", "workflow", "render", "report", "--runtime-root", "runtime"],
                                env={**os.environ, "XDG_CONFIG_HOME": str(root / "xdg")},
                                capture_output=True, text=True, check=False, timeout=5)
        return {"case": "deep-ledger-json-cli", "exit": result.returncode, "stdout": result.stdout,
                "traceback": "Traceback" in result.stderr, "last_stderr_line": result.stderr.splitlines()[-1],
                "state_preserved": before == store.path.read_bytes(), "ledger_preserved": ledger.read_text() == payload}


def blank_decision() -> dict[str, object]:
    state = new_state(repo_root=Path("/sanitized-review-project"))
    state["work"]["prd"] = PRD
    state["review"]["decisions"] = [{"id": "", "kind": "", "summary": "", "rationale": "", "cycle": None,
                                      "created_at": "2026-09-05T10:00:00Z", "status": "applied"}]
    validate_state(state)
    summary = records.completed_prd_summary(state)
    return {"case": "schema-valid-blank-decision", "validated": True,
            "autonomous_decisions": summary["autonomous_decisions"],
            "blank_audit_row": "|  | applied |  |  |  |  |" in reports.render_audit(state)}


def fifo_inputs() -> list[dict[str, object]]:
    rows = []
    for case in ("frontmatter", "defer", "config"):
        with tempfile.TemporaryDirectory(prefix="ft04r8-fifo-") as temporary:
            root = Path(temporary).resolve()
            store, _paths, _runtime = environment(root)
            fifo = root / ("ovcaq.toml" if case == "config" else PRD)
            os.mkfifo(fifo)
            arguments = {"frontmatter": ["frontmatter", "--prd", str(fifo)],
                         "defer": ["defer", "--prd", PRD, "--record", str(fifo)], "config": ["select"]}[case]
            before = store.path.read_bytes()
            timeout = False
            try:
                result = subprocess.run([sys.executable, "-m", "ovcaq", "--root", str(root), "--json", "workflow", *arguments, "--runtime-root", "runtime"],
                                        env={**os.environ, "XDG_CONFIG_HOME": str(root / "xdg")},
                                        capture_output=True, text=True, check=False, timeout=2)
            except subprocess.TimeoutExpired:
                timeout = True
            rows.append({"case": f"fifo-{case}", "exceeded_two_seconds": timeout,
                         "state_preserved": store.path.read_bytes() == before})
    return rows


def report_durability() -> list[dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="ft04r8-fsync-") as temporary:
        root = Path(temporary).resolve()
        store, _paths, runtime = environment(root)
        state = store.read()
        real_sync = os.fsync
        directories = []

        def observe(descriptor: int) -> None:
            opened = os.fstat(descriptor)
            if stat.S_ISDIR(opened.st_mode):
                directories.append(opened.st_ino)
            real_sync(descriptor)

        with patch.object(reports.os, "fsync", observe):
            reports.publish_report(runtime, state, ())
        creation = {"case": "report-created-parent-durability", "runtime_parent_synced": runtime.stat().st_ino in directories,
                    "reports_directory_synced": (runtime / "reports").stat().st_ino in directories}
        state["work"]["prd"] = "00005-next.md"

        def fail_directory(descriptor: int) -> None:
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise OSError("injected directory fsync failure")
            real_sync(descriptor)

        error = None
        try:
            with patch.object(reports.os, "fsync", fail_directory):
                reports.publish_report(runtime, state, ())
        except OSError as exc:
            error = str(exc)
        directories.clear()
        with patch.object(reports.os, "fsync", observe):
            path = reports.publish_report(runtime, state, ())
        replay = {"case": "report-retry-after-directory-fsync-failure", "first_error": error,
                  "retry_returned_success": path.is_file(), "retry_directory_sync_count": len(directories)}
        return [creation, replay]


if __name__ == "__main__":
    observations = [run(kind, replacement) for kind in ("stall", "park")
                    for replacement in ("source-before-rename", "held-after-rename", "held-across-restart")]
    observations.append(ledger_lock_replacement())
    observations.append(report_other_prd())
    observations.extend(corrupt_ledger())
    observations.append(deep_ledger_cli())
    observations.append(blank_decision())
    observations.extend(fifo_inputs())
    observations.extend(report_durability())
    print(json.dumps(observations, indent=2))
