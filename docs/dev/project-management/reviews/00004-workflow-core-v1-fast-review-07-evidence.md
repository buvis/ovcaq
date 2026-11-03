# FT-04R7 independent reproduction evidence

Reviewed HEAD: `47a8764760e1fedb82eb1514a344584fb7ad2f3e`.
All operations below use freshly created temporary projects. No repository implementation, live PRD, or autopilot state is modified.

The coordinator ran the script against the checkout and the freshly built wheel. The final combined run used the wheel from a working directory outside the checkout:

```text
mise exec -- uv run --no-project --with /Users/bob/git/src/github.com/buvis/ovcaq/dist/ovcaq-0.1.0.dev0-py3-none-any.whl python /tmp/ft_04r7_reproduce.py
```

A separate import-origin check resolved `ovcaq` under uv's `site-packages`, not the checkout. Recreate the script below in a temporary file to rerun. Exit zero means the observation script completed; its timeout/success/state fields are the actual defect evidence, not passing conformance assertions. The FIFO subprocess uses the installed `ovcaq.cli.main` entry function with the real parser and dispatch.

## Observed output

```jsonl
{"case": "concurrent-hold-overwrite", "injected": true, "returned_success": true, "held_bytes": "# Preserve this PRD\n", "recovery": null, "tasks_remaining": 0}
{"case": "cli-park-halt", "first_exit": 0, "second_exit": 0, "second_json": {"ok": true, "result": {"kind": "park", "operation_id": "45840a803a7f4beb80c22c229bd3a846", "replayed": false, "systemic_halt": true}, "revision": 9}, "phase": "paused"}
{"case": "configured-paths", "select_exit": 0, "selection": "{\"prd\": null, \"source\": \"drained\"}\n", "resume_exit": 2, "resume_error": "{\"error\": {\"code\": \"state_io\", \"message\": \"cannot open state lock /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/ft-04r7-paths-ql098n8d/dev/local/ovcaq/state.json.lock: [Errno 2] No such file or directory: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/ft-04r7-paths-ql098n8d/dev/local/ovcaq/state.json.lock'\", \"path\": null}, \"ok\": false}\n"}
{"case": "cli-tier-floor", "before": {"workflow/tier-floor": "deep"}, "after": {}, "exit": 0, "stderr": "ovcaq: PRD frontmatter tier 'deep' is unavailable; applying no tier floor\n"}
{"case": "missing-batch-preflight", "hold_before": false, "hold_after": true, "state_unchanged": true, "error": "ValueError('cannot start recovery without batch.id')"}
{"case": "metrics-fifo", "surface": "metrics", "timeout_seconds": 2}
{"case": "metrics-fifo", "surface": "report", "timeout_seconds": 2}
{"case": "unsafe-batch-preflight", "kind": "stall", "wip_present": false, "hold_present": true, "recovery_step": "moved", "state_unchanged": false, "errors": ["WorkflowIdentifierError(\"batch_id must be a nonempty printable path-safe component: '../escape'\")", "WorkflowIdentifierError(\"batch_id must be a nonempty printable path-safe component: '../escape'\")"]}
{"case": "commit-directory-swap", "kind": "stall", "target": "deferred", "swap_injected": true, "recovery": null, "tasks_remaining": 0, "ledger_at_configured_path": false, "prd_in_configured_hold": true, "returned_success": true, "operation_id": "proof-operation"}
{"case": "commit-directory-swap", "kind": "stall", "target": "wip", "swap_injected": true, "recovery": null, "tasks_remaining": 0, "ledger_at_configured_path": true, "prd_in_configured_hold": true, "returned_success": true, "operation_id": "proof-operation"}
{"case": "commit-directory-swap", "kind": "stall", "target": "hold", "swap_injected": true, "recovery": null, "tasks_remaining": 0, "ledger_at_configured_path": true, "prd_in_configured_hold": false, "returned_success": true, "operation_id": "proof-operation"}
{"case": "unsafe-batch-preflight", "kind": "park", "wip_present": false, "hold_present": true, "recovery_step": "moved", "state_unchanged": false, "errors": ["WorkflowIdentifierError(\"batch_id must be a nonempty printable path-safe component: '../escape'\")", "WorkflowIdentifierError(\"batch_id must be a nonempty printable path-safe component: '../escape'\")"]}
{"case": "commit-directory-swap", "kind": "park", "target": "deferred", "swap_injected": true, "recovery": null, "tasks_remaining": 0, "ledger_at_configured_path": false, "prd_in_configured_hold": true, "returned_success": true, "operation_id": "proof-operation"}
{"case": "commit-directory-swap", "kind": "park", "target": "wip", "swap_injected": true, "recovery": null, "tasks_remaining": 0, "ledger_at_configured_path": true, "prd_in_configured_hold": true, "returned_success": true, "operation_id": "proof-operation"}
{"case": "commit-directory-swap", "kind": "park", "target": "hold", "swap_injected": true, "recovery": null, "tasks_remaining": 0, "ledger_at_configured_path": true, "prd_in_configured_hold": false, "returned_success": true, "operation_id": "proof-operation"}
```

## Interpretation

- A valid unstarted batch with an active WIP PRD creates `hold/` before missing-batch refusal (state bytes remain unchanged).
- A schema-valid but path-unsafe batch identifier moves the PRD, leaves recovery at `moved`, and repeats the same refusal on retry for both stall and park.
- A FIFO metric ledger without a writer makes both render commands exceed the two-second timeout. The subprocess is killed/reaped by `subprocess.run`; the FIFO inode and state bytes remain unchanged.
- At the final transaction's existing `BACKUP_TEMP_FSYNCED` failpoint, the mutator has already checked filesystem identity but state publication has not occurred. Replacing the deferred, WIP, or hold directory here still lets stall and park report success, clear recovery, and clear the unfinished task. Deferred replacement leaves no ledger at its configured name; hold replacement leaves no PRD in configured hold. This concerns replacement before state publication, not arbitrary changes after a completed operation.

## Reproduction script

```python
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from ovcaq.state.schema import new_state
from ovcaq.state.store import DurabilityBoundary, StateStore
from ovcaq.workflow.paths import resolve_lifecycle_paths
from ovcaq.workflow.records import park, stall
from ovcaq.workflow import records as records_module
from ovcaq.workflow.frontmatter import apply_to_store

PRD = "00004-proof.md"


def setup(root: Path):
    (root / ".git").mkdir()
    paths = resolve_lifecycle_paths(root, Path("dev/local/prds"))
    paths.wip.mkdir(parents=True)
    (paths.wip / PRD).write_text("# Preserve this PRD\n")
    runtime = root / "dev/local/ovcaq"
    runtime.mkdir(parents=True)
    state = new_state(repo_root=root)
    state["work"]["prd"] = PRD
    state["batch"].update(id="proof-batch", status="running", started_at="2026-09-05T12:00:00Z")
    state["tasks"] = [{"id": 1, "name": "unfinished", "description": "retained work", "active_form": "working", "status": "in_progress", "blocked_by": [], "tier": None, "files_touched": None, "public_contract_edit": None, "estimates": {"input_tokens": None, "context_peak": None}, "attempts": [], "metadata": {}}]
    state["work"]["tasks_total"] = 1
    store = StateStore(runtime / "state.json")
    store.initialize(state)
    return store, paths, runtime


def metrics_fifo(surface: str):
    with TemporaryDirectory(prefix="ft-04r7-fifo-") as temporary:
        root = Path(temporary).resolve()
        store, _paths, runtime = setup(root)
        before = store.path.read_bytes()
        fifo = runtime / "metrics.jsonl"
        os.mkfifo(fifo)
        inode = fifo.stat().st_ino
        command = [sys.executable, "-c", "from ovcaq.cli import main; raise SystemExit(main())", "--root", str(root), "--json", "workflow", "render", surface]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=2)
            outcome = {"exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        except subprocess.TimeoutExpired:
            outcome = {"timeout_seconds": 2}
        assert fifo.stat().st_ino == inode
        assert store.path.read_bytes() == before
        print(json.dumps({"case": "metrics-fifo", "surface": surface, **outcome}))


def missing_batch_preflight():
    with TemporaryDirectory(prefix="ft-04r7-preflight-") as temporary:
        root = Path(temporary).resolve()
        store, paths, runtime = setup(root)
        store.transaction(lambda state: state.update(batch=new_state(repo_root=root)["batch"]))
        before = store.path.read_bytes()
        hold_before = paths.hold.exists()
        try:
            stall(store, paths=paths, runtime_root=runtime, prd=PRD, site="proof", detail="proof")
            error = None
        except Exception as caught:
            error = repr(caught)
        print(json.dumps({"case": "missing-batch-preflight", "hold_before": hold_before, "hold_after": paths.hold.exists(), "state_unchanged": store.path.read_bytes() == before, "error": error}))


def unsafe_batch_preflight(kind: str):
    with TemporaryDirectory(prefix="ft-04r7-invalid-batch-") as temporary:
        root = Path(temporary).resolve()
        store, paths, runtime = setup(root)
        store.transaction(lambda state: state["batch"].update(id="../escape"))
        before = store.path.read_bytes()
        arguments = dict(paths=paths, runtime_root=runtime, detail="proof", operation_id_factory=lambda: "proof-operation", now=lambda: "2026-09-05T12:00:00Z")
        errors = []
        for attempt in range(2):
            try:
                if kind == "stall":
                    stall(store, prd=PRD, site="proof", **arguments)
                else:
                    park(store, **arguments)
            except Exception as caught:
                errors.append(repr(caught))
        current = store.read()
        print(json.dumps({"case": "unsafe-batch-preflight", "kind": kind, "wip_present": (paths.wip / PRD).exists(), "hold_present": (paths.hold / PRD).exists(), "recovery_step": current["recovery"]["operation"]["step"], "state_unchanged": store.path.read_bytes() == before, "errors": errors}))


def hold_overwrite():
    with TemporaryDirectory(prefix="ft-04r7-no-clobber-") as temporary:
        root = Path(temporary).resolve()
        store, paths, runtime = setup(root)
        original_rename = records_module.os.rename
        held = paths.hold / PRD
        injected = False

        def race(source, destination, **kwargs):
            nonlocal injected
            if source == PRD and destination == PRD and not injected:
                held.write_text("# Concurrent held work must survive\n")
                injected = True
            return original_rename(source, destination, **kwargs)

        records_module.os.rename = race
        try:
            result = stall(store, paths=paths, runtime_root=runtime, prd=PRD, site="proof", detail="proof")
        finally:
            records_module.os.rename = original_rename
        current = store.read()
        print(json.dumps({"case": "concurrent-hold-overwrite", "injected": injected, "returned_success": result.operation_id is not None, "held_bytes": held.read_text(), "recovery": current["recovery"]["operation"], "tasks_remaining": len(current["tasks"])}))


def cli_park_halt():
    with TemporaryDirectory(prefix="ft-04r7-halt-") as temporary:
        root = Path(temporary).resolve()
        store, paths, runtime = setup(root)
        command = [sys.executable, "-c", "from ovcaq.cli import main; raise SystemExit(main())", "--root", str(root), "--json", "workflow", "park"]
        first = subprocess.run(command, capture_output=True, text=True, timeout=3)
        second_prd = "00005-proof.md"
        (paths.wip / second_prd).write_text("# Next PRD\n")
        store.transaction(lambda state: state["work"].update(prd=second_prd))
        second = subprocess.run(command, capture_output=True, text=True, timeout=3)
        print(json.dumps({"case": "cli-park-halt", "first_exit": first.returncode, "second_exit": second.returncode, "second_json": json.loads(second.stdout), "phase": store.read()["work"]["phase"]}))


def configured_paths():
    with TemporaryDirectory(prefix="ft-04r7-paths-") as temporary:
        root = Path(temporary).resolve()
        store, paths, runtime = setup(root)
        paths.root.rename(root / "custom-prds")
        runtime.rename(root / "custom-runtime")
        (root / "ovcaq.toml").write_text('[workflow]\nprd_root = "custom-prds"\nruntime_root = "custom-runtime"\n')
        command = [sys.executable, "-c", "from ovcaq.cli import main; raise SystemExit(main())", "--root", str(root), "--json", "workflow"]
        selected = subprocess.run([*command, "select"], capture_output=True, text=True, timeout=3)
        resumed = subprocess.run([*command, "resume-target"], capture_output=True, text=True, timeout=3)
        print(json.dumps({"case": "configured-paths", "select_exit": selected.returncode, "selection": selected.stdout, "resume_exit": resumed.returncode, "resume_error": resumed.stderr}))


def cli_tier_floor():
    with TemporaryDirectory(prefix="ft-04r7-tier-") as temporary:
        root = Path(temporary).resolve()
        store, paths, runtime = setup(root)
        prd_path = paths.wip / PRD
        content = "---\ndefault_model: deep\n---\n# PRD\n"
        prd_path.write_text(content)
        apply_to_store(store, content, prd=PRD, available_tiers={"deep"})
        before = store.read()["work"]["extensions"].copy()
        command = [sys.executable, "-c", "from ovcaq.cli import main; raise SystemExit(main())", "--root", str(root), "--json", "workflow", "frontmatter", "--prd", str(prd_path)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=3)
        print(json.dumps({"case": "cli-tier-floor", "before": before, "after": store.read()["work"]["extensions"], "exit": result.returncode, "stderr": result.stderr}))


def commit_swap(kind: str, target: str):
    with TemporaryDirectory(prefix="ft-04r7-commit-") as temporary:
        root = Path(temporary).resolve()
        initial_store, paths, runtime = setup(root)
        changed = False
        directory = runtime / "deferred" if target == "deferred" else getattr(paths, target)
        moved = directory.with_name(directory.name + "-moved")

        def interrupt(boundary):
            nonlocal changed
            if changed or boundary != DurabilityBoundary.BACKUP_TEMP_FSYNCED:
                return
            current = json.loads(initial_store.path.read_text())
            operation = current["recovery"]["operation"]
            if operation and operation["step"] == "recorded":
                directory.rename(moved)
                directory.mkdir()
                changed = True

        store = StateStore(initial_store.path, boundary_hook=interrupt)
        arguments = dict(paths=paths, runtime_root=runtime, detail="proof", operation_id_factory=lambda: "proof-operation", now=lambda: "2026-09-05T12:00:00Z")
        try:
            result = stall(store, prd=PRD, site="proof", **arguments) if kind == "stall" else park(store, **arguments)
            outcome = {"returned_success": True, "operation_id": result.operation_id}
        except Exception as error:
            outcome = {"returned_success": False, "error": repr(error)}
        state = initial_store.read()
        print(json.dumps({"case": "commit-directory-swap", "kind": kind, "target": target, "swap_injected": changed, "recovery": state["recovery"]["operation"], "tasks_remaining": len(state["tasks"]), "ledger_at_configured_path": (runtime / "deferred/proof-batch-deferred.json").exists(), "prd_in_configured_hold": (paths.hold / PRD).exists(), **outcome}))


if __name__ == "__main__":
    hold_overwrite()
    cli_park_halt()
    configured_paths()
    cli_tier_floor()
    missing_batch_preflight()
    for surface in ("metrics", "report"):
        metrics_fifo(surface)
    for kind in ("stall", "park"):
        unsafe_batch_preflight(kind)
        for target in ("deferred", "wip", "hold"):
            commit_swap(kind, target)
```

## Additional reproduced contract gaps

- Creating a held destination after the existing precheck and immediately before the original rename destroys the concurrent held file. The command reports success and clears recovery/tasks. A second pathname check cannot make the rename non-overwriting.
- Two sequential PRD parks produce a committed systemic pause, but both commands exit zero. The second JSON response still says `ok: true` with `systemic_halt: true`.
- Configuring custom PRD/runtime roots leaves command discovery at hardcoded defaults: selection returns drained despite a custom WIP PRD, and resume attempts the default missing state lock.
- After the service validates and commits tier `deep` using an available tier map, the identical PRD passed through the CLI loses that floor because dispatch supplies no available tier keys. This demonstrates the missing command-level configuration input; it does not validate any particular provider's tier map.

## Mechanical quality checks

Independent `ast` measurement counts function spans from `lineno` through `end_lineno`, inclusive. File sizes count `splitlines()`. Results agree with the review procedure's mechanical-facts script.

| Production file | Lines |
|---|---:|
| src/ovcaq/workflow/records.py | 955 |
| src/ovcaq/cli.py | 838 |
| tests/packaging/test_installed_cli.py | 1,174 |
| tests/workflow/test_sagas.py | 1,201 |

| Function | Location | Lines |
|---|---|---:|
| _execute_operation | src/ovcaq/workflow/records.py:728 | 169 |
| _dispatch_workflow | src/ovcaq/cli.py:605 | 109 |
| _add_workflow_commands | src/ovcaq/cli.py:145 | 76 |
| main | src/ovcaq/cli.py:784 | 55 |
| parse | src/ovcaq/workflow/frontmatter.py:86 | 51 |
| render_audit | src/ovcaq/workflow/reports.py:58 | 59 |
| render_report | src/ovcaq/workflow/reports.py:272 | 85 |
| render_metrics | src/ovcaq/workflow/reports.py:359 | 61 |

Direct source inspection also confirms `source_stat is None` is unreachable inside the `if source_exists` branch at records.py:543, and `_more_prds` has one reference (the transition table) and only calls `reset_prd_fields`. These are behavior-preserving simplification candidates; the necessary directory descriptor, ledger lock, state guard, and failpoint mechanisms are not candidates for removal.

The first two production files and these two test files newly exceed 800 lines in the review range. The preexisting 851-line tests/state/test_service_commands.py grows to 962; its preexisting size violation is not a new root cause. Measurements target actual changed code, not a line-to-spec ratio.
