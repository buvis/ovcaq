"""Programs executed by the isolated installed interpreter for FT-04F11."""

__all__ = [
    "FSYNC_SCENARIO",
    "INITIALIZE_STATE",
    "INSTALLED_ORIGINS",
    "READ_LEDGER",
    "REPORT_ACTOR",
    "UPDATE_PRD",
]

INITIALIZE_STATE = """
import sys
from pathlib import Path
from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore

project = Path(sys.argv[1])
state_path = Path(sys.argv[2])
prd = sys.argv[3]
project.mkdir(parents=True, exist_ok=True)
state_path.parent.mkdir(parents=True, exist_ok=True)
state = new_state(repo_root=project)
state["batch"].update({
    "id": "batch", "status": "running",
    "started_at": "2026-09-05T20:00:00Z",
})
state["work"]["prd"] = prd
StateStore(state_path).initialize(state)
"""


READ_LEDGER = """
import json
import sys
from pathlib import Path
from ovcaq.workflow.records import load_deferred_records

runtime_root = Path(sys.argv[1])
print(json.dumps(load_deferred_records(runtime_root, "batch"), sort_keys=True))
"""


INSTALLED_ORIGINS = """
import json
import ovcaq
from ovcaq import cli, workflow_cli
from ovcaq.state import schema, store
from ovcaq.workflow import _files, records, reports

modules = (ovcaq, cli, workflow_cli, schema, store, _files, records, reports)
print(json.dumps({module.__name__: module.__file__ for module in modules}, sort_keys=True))
"""


UPDATE_PRD = """
import sys
from pathlib import Path
from ovcaq.state.store import StateStore

state_path = Path(sys.argv[1])
prd = sys.argv[2]
StateStore(state_path).transaction(
    lambda state: state["work"].update({"prd": prd})
)
"""


REPORT_ACTOR = """
import sys
from pathlib import Path
from unittest.mock import patch
from ovcaq.cli import main
from ovcaq.workflow import reports

root = Path(sys.argv[1])
original = reports._publish_file

def pause_before_publish(*args, **kwargs):
    print("READY", flush=True)
    if sys.stdin.readline() != "continue\\n":
        raise RuntimeError("report actor was not resumed")
    return original(*args, **kwargs)

with patch.object(reports, "_publish_file", autospec=True, side_effect=pause_before_publish):
    raise SystemExit(
        main(["--root", str(root), "--json", "workflow", "render", "report"])
    )
"""


FSYNC_SCENARIO = """
import errno
import io
import json
import os
import stat
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch
from ovcaq.cli import main
from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore
from ovcaq.workflow.records import load_deferred_records

project = Path(sys.argv[1])
failure_label = sys.argv[2]
project.mkdir(parents=True)
state_path = project / "independent/state.json"
state_path.parent.mkdir(parents=True)
state = new_state(repo_root=project)
state["batch"].update({
    "id": "batch", "status": "running",
    "started_at": "2026-09-05T20:00:00Z",
})
state["work"]["prd"] = "00004-a.md"
store = StateStore(state_path)
store.initialize(state)
authoritative = state_path.read_bytes()
runtime_root = project / "new/nested"
record_path = project / "record.json"
record_path.write_text(json.dumps({"op_id": "durable-one"}), encoding="utf-8")
expected = {
    "project-parent": project,
    "new-parent": project / "new",
    "runtime-root": runtime_root,
    "deferred-leaf": runtime_root / "deferred",
}
argv = [
    "--root", str(project), "--json", "workflow", "defer",
    "--runtime-root", str(runtime_root), "--state", str(state_path),
    "--prd", "00004-a.md", "--record", str(record_path),
]
real_fsync = os.fsync
runtime_absent_before = not runtime_root.exists()

def invoke(fail_at):
    observed = []
    delegated = []
    failed = False

    def observing_fsync(descriptor):
        nonlocal failed
        opened = os.fstat(descriptor)
        label = None
        if stat.S_ISDIR(opened.st_mode):
            identity = (opened.st_dev, opened.st_ino)
            for candidate, path in expected.items():
                if path.exists() and (path.stat().st_dev, path.stat().st_ino) == identity:
                    label = candidate
                    observed.append(candidate)
                    break
        real_fsync(descriptor)
        delegated.append(label or "non-directory")
        if fail_at is not None and label == fail_at and not failed:
            failed = True
            raise OSError(
                errno.EIO,
                f"injected directory fsync failure at {label}",
                str(expected[label]),
            )

    stdout = io.StringIO()
    stderr = io.StringIO()
    with (
        patch.object(os, "fsync", observing_fsync),
        redirect_stdout(stdout),
        redirect_stderr(stderr),
    ):
        exit_code = main(argv)
    return {
        "exit": exit_code,
        "stdout": stdout.getvalue(),
        "stderr": stderr.getvalue(),
        "directories": observed,
        "delegated_calls": len(delegated),
    }

failed = invoke(failure_label)
state_after_failure = state_path.read_bytes()
directories_after_failure = [
    label for label, path in expected.items() if path.exists()
]
retry = invoke(None)
ledger_path = runtime_root / "deferred/batch-deferred.json"
ledger_after_retry = ledger_path.read_bytes()
state_after_retry = state_path.read_bytes()
replay = invoke(None)
print(json.dumps({
    "failed": failed,
    "retry": retry,
    "replay": replay,
    "expected": list(expected),
    "runtime_absent_before": runtime_absent_before,
    "directories_after_failure": directories_after_failure,
    "state_valid_after_failure": bool(json.loads(state_after_failure)),
    "state_unchanged_after_retry": state_after_retry == authoritative,
    "state_unchanged_after_replay": state_path.read_bytes() == authoritative,
    "ledger_unchanged_by_replay": ledger_path.read_bytes() == ledger_after_retry,
    "ledger_ids": [row["op_id"] for row in load_deferred_records(runtime_root, "batch")],
    "state_changed_while_interrupted": state_after_failure != authoritative,
}, sort_keys=True))
"""
