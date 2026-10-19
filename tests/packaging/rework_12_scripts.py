"""Installed-interpreter programs for runtime ancestry durability regressions."""

__all__ = ["ANCESTRY_ACTOR", "ORIGIN_CHECK"]

ORIGIN_CHECK = r"""
import json
import sys
from pathlib import Path

def installed_origins() -> dict[str, str]:
    origins = {}
    for name, module in tuple(sys.modules.items()):
        if name == "ovcaq" or name.startswith("ovcaq."):
            filename = getattr(module, "__file__", None)
            assert filename, f"product module has no origin: {name}"
            path = Path(filename).resolve()
            origins[name] = str(path)
    assert "ovcaq" in origins
    return origins
"""

_COMMON = (
    ORIGIN_CHECK
    + r"""
import errno
import io
import os
import stat
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch
from ovcaq.cli import main
from ovcaq.workflow.records import record_defer

project = Path(sys.argv[1])
target = project / sys.argv[2]
mode = sys.argv[3]
runtime = project / "new/nested"
directories = (project, project / "new", runtime, runtime / "deferred")
state_path = project / "independent/state.json"
real_mkdir = Path.mkdir
real_fsync = os.fsync
created = False
paused = False
peer_seen = None
synced = []
failed_parent = False

def identity(path: Path) -> list[int]:
    current = path.stat()
    return [current.st_dev, current.st_ino]

def pause(event: str) -> None:
    message = {"event": event, "origins": installed_origins()}
    if event == "peer-created":
        message["identity"] = identity(target)
    print(json.dumps(message), file=sys.__stdout__, flush=True)
    assert sys.stdin.readline() == "continue\n", "actor was not resumed"

def observing_mkdir(path: Path, *args, **kwargs) -> None:
    global created, paused, peer_seen
    selected = path == target
    if selected and mode.startswith("racer") and not paused:
        paused = True
        pause("before-mkdir")
        peer_seen = identity(target)
    existed = path.exists()
    result = real_mkdir(path, *args, **kwargs)
    if selected and not existed:
        created = True
        if mode == "peer" and not paused:
            paused = True
            pause("peer-created")
    return result

def observing_fsync(descriptor: int) -> None:
    global failed_parent
    opened = os.fstat(descriptor)
    matched = None
    if stat.S_ISDIR(opened.st_mode):
        descriptor_identity = [opened.st_dev, opened.st_ino]
        for candidate in directories:
            if candidate.exists() and identity(candidate) == descriptor_identity:
                matched = candidate
                break
    if mode == "crash" and created and matched == target.parent:
        print(json.dumps({
            "event": "exit-before-parent-fsync", "target": str(target),
            "identity": identity(target), "parent_identity": descriptor_identity,
            "origins": installed_origins(),
        }), file=sys.__stdout__, flush=True)
        os._exit(73)
    real_fsync(descriptor)
    if matched is not None:
        synced.append({"path": str(matched), "identity": descriptor_identity})
    if mode == "racer-fail" and peer_seen and matched == target.parent:
        failed_parent = True
        raise OSError(errno.EIO, "injected peer parent fsync failure", str(matched))

def invoke_cli() -> dict:
    stdout, stderr = io.StringIO(), io.StringIO()
    argv = [
        "--root", str(project), "--json", "workflow", "defer",
        "--runtime-root", str(runtime), "--state", str(state_path),
        "--prd", "00004-a.md", "--record", str(project / "record.json"),
    ]
    with redirect_stdout(stdout), redirect_stderr(stderr):
        status = main(argv)
    return {"exit": status, "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}

def invoke_record() -> dict:
    try:
        path = record_defer(runtime, "00004-a.md", "batch", {"op_id": "crash-one"})
    except Exception as error:
        return {"exit": 2, "error": str(error)}
    return {"exit": 0, "path": str(path)}
"""
)

_RUN = r"""
installed_origins()
with patch.object(Path, "mkdir", observing_mkdir), patch.object(os, "fsync", observing_fsync):
    result = invoke_record() if mode in {"peer", "racer", "racer-fail"} else invoke_cli()
result.update({
    "origins": installed_origins(), "fsyncs": synced,
    "peer_seen": peer_seen, "failed_parent": failed_parent,
})
print(json.dumps(result), flush=True)
raise SystemExit(result["exit"])
"""

ANCESTRY_ACTOR = _COMMON + _RUN
