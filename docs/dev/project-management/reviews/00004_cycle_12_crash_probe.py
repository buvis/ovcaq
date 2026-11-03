"""Reproduce an interrupted runtime-directory confirmation using installed code."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ACTOR = r'''
import io
import json
import os
import stat
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from ovcaq.cli import main
from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore
from ovcaq.workflow import _files

root = Path(sys.argv[1])
mode = sys.argv[2]
boundary = sys.argv[3]
state_path = root / "authoritative/state.json"
runtime = root / "new/nested"
if mode == "initialize":
    state_path.parent.mkdir()
    state = new_state(repo_root=root)
    state["batch"].update(id="batch", status="running", started_at="2026-09-07T00:00:00Z")
    state["work"]["prd"] = "00004-a.md"
    StateStore(state_path).initialize(state)
    (root / "record.json").write_text(json.dumps({"op_id": "crash-one"}))
    print(json.dumps({"origin": _files.__file__}))
    raise SystemExit(0)
argv = ["--root", str(root), "--json", "workflow", "defer",
        "--runtime-root", str(runtime), "--state", str(state_path),
        "--prd", "00004-a.md", "--record", str(root / "record.json")]
paths = {"project": root, "new": root / "new", "runtime": runtime,
         "deferred": runtime / "deferred"}
if mode == "crash":
    real_sync = _files._fsync_directory
    def interrupt_before_sync(path):
        if path == paths[boundary]:
            os._exit(73)
        real_sync(path)
    with patch.object(_files, "_fsync_directory", interrupt_before_sync):
        raise SystemExit(main(argv))
observed = []
real_fsync = os.fsync
def observe(descriptor):
    opened = os.fstat(descriptor)
    if stat.S_ISDIR(opened.st_mode):
        identity = (opened.st_dev, opened.st_ino)
        for label, path in paths.items():
            if path.exists() and (path.stat().st_dev, path.stat().st_ino) == identity:
                observed.append(label)
                break
    return real_fsync(descriptor)
stdout, stderr = io.StringIO(), io.StringIO()
with patch.object(os, "fsync", observe), redirect_stdout(stdout), redirect_stderr(stderr):
    exit_code = main(argv)
print(json.dumps({"exit": exit_code, "stdout": stdout.getvalue(),
                  "stderr": stderr.getvalue(), "fsynced_directories": observed}))
'''


def invoke(python: str, root: Path, mode: str, boundary: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
        environment.pop(name, None)
    environment.update(PYTHONNOUSERSITE="1", XDG_CONFIG_HOME=str(root / "config"))
    return subprocess.run(
        [python, "-c", ACTOR, str(root), mode, boundary],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def scenario(python: str, boundary: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="ovcaq-r12-crash-") as temporary:
        root = Path(temporary).resolve()
        initialized = invoke(python, root, "initialize", boundary)
        assert initialized.returncode == 0, initialized.stderr
        origin = json.loads(initialized.stdout)["origin"]
        assert "site-packages" in origin, origin
        state_path = root / "authoritative/state.json"
        original_state = state_path.read_bytes()
        crashed = invoke(python, root, "crash", boundary)
        assert crashed.returncode == 73, crashed.stderr
        survivors = [name for name in ("new", "new/nested") if (root / name).exists()]
        assert state_path.read_bytes() == original_state
        retry = invoke(python, root, "retry", boundary)
        assert retry.returncode == 0, retry.stderr
        evidence = json.loads(retry.stdout)
        assert evidence["exit"] == 0, evidence
        ledger = root / "new/nested/deferred/batch-deferred.json"
        first_ledger = ledger.read_bytes()
        replay = invoke(python, root, "retry", boundary)
        assert replay.returncode == 0, replay.stderr
        replay_evidence = json.loads(replay.stdout)
        assert replay_evidence["exit"] == 0, replay_evidence
        return {
            "boundary": boundary,
            "installed_origin": origin,
            "crash_exit": crashed.returncode,
            "surviving_directories": survivors,
            "retry": evidence,
            "replay": replay_evidence,
            "missing_parent_sync_on_success": boundary not in evidence["fsynced_directories"],
            "missing_parent_sync_on_replay": boundary not in replay_evidence["fsynced_directories"],
            "state_unchanged": state_path.read_bytes() == original_state,
            "ledger_unchanged_by_replay": ledger.read_bytes() == first_ledger,
            "ledger_items": json.loads(first_ledger)["items"],
        }


if __name__ == "__main__":
    print(json.dumps([scenario(sys.argv[1], boundary) for boundary in ("project", "new")], indent=2))
