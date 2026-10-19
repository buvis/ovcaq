from __future__ import annotations

from rework_12_scripts import ORIGIN_CHECK

__all__ = ["ANCESTRY_BOUNDARY_ACTOR"]

ANCESTRY_BOUNDARY_ACTOR = (
    ORIGIN_CHECK
    + r"""
import errno
import os
import stat
from contextlib import contextmanager, nullcontext
from unittest.mock import patch

project = Path(sys.argv[1])
mode = sys.argv[2]
runtime = Path(sys.argv[3])
ancestor = Path(sys.argv[4])
displaced = project / "displaced"
real_open = os.open
real_stat = os.stat
real_mkdir = os.mkdir
real_fsync = os.fsync
events = []
replaced = False
ancestor_confirmed = False
forced_missing = False
known_directories = {}
ledger = runtime / "deferred/batch-deferred.json"
exact_replay = ledger.exists()
access_error = None

def identity(value):
    return [value.st_dev, value.st_ino]

for directory in (*runtime.parents, runtime, runtime / "deferred"):
    try:
        known_directories[tuple(identity(real_stat(directory)))] = str(directory)
    except FileNotFoundError:
        pass

def absolute(path, dir_fd=None):
    if isinstance(path, int):
        return known_directories.get(tuple(identity(os.fstat(path))))
    name = os.fsdecode(path)
    if not os.path.isabs(name) and dir_fd is not None:
        parent = known_directories[tuple(identity(os.fstat(dir_fd)))]
        name = os.path.join(parent, name)
    return os.path.abspath(name)

def observed(path, value):
    if stat.S_ISDIR(value.st_mode):
        key = identity(value)
        known_directories[tuple(key)] = path
        events.append({"kind": "observed", "path": path, "identity": key})

def observing_stat(path, *args, **kwargs):
    value = real_stat(path, *args, **kwargs)
    observed(absolute(path, kwargs.get("dir_fd")), value)
    return value

def observing_open(path, flags, *args, **kwargs):
    global access_error, forced_missing, replaced
    name = absolute(path, kwargs.get("dir_fd"))
    if mode in {"search", "no-search"} and name == str(ancestor):
        events.append({"kind": "open", "path": name, "flags": flags})
    if (
        mode == "reparent-during-publication"
        and name == str(ledger)
        and ancestor_confirmed
        and not replaced
    ):
        previous = identity(real_stat(ancestor))
        runtime_before = identity(real_stat(runtime))
        child = runtime.relative_to(ancestor).parts[0]
        os.rename(ancestor, displaced)
        real_mkdir(ancestor)
        os.rename(displaced / child, ancestor / child)
        replaced = True
        events.append({
            "kind": "reparented", "path": str(ancestor), "previous": previous,
            "displaced": identity(real_stat(displaced)),
            "replacement": identity(real_stat(ancestor)),
            "runtime_before": runtime_before,
            "runtime_after": identity(real_stat(runtime)),
            "boundary": "ledger-open",
        })
    if (
        mode == "replace-during-publication"
        and name == str(ledger)
        and ancestor_confirmed
        and not replaced
    ):
        previous = identity(real_stat(runtime))
        os.rename(runtime, displaced)
        real_mkdir(runtime)
        replaced = True
        events.append({
            "kind": "replaced", "path": str(runtime), "previous": previous,
            "displaced": identity(real_stat(displaced)),
            "replacement": identity(real_stat(runtime)),
            "boundary": "ledger-open",
        })
    if (
        mode == "replace-at-deferred-mkdir"
        and name == str(runtime / "deferred")
        and ancestor_confirmed
        and exact_replay
        and not forced_missing
    ):
        forced_missing = True
        raise FileNotFoundError(errno.ENOENT, "injected concurrent absence", name)
    if mode == "replace" and name == str(ancestor) and ancestor_confirmed and not replaced:
        previous = identity(real_stat(ancestor))
        os.rename(ancestor, displaced)
        real_mkdir(ancestor)
        replaced = True
        events.append({
            "kind": "replaced", "path": str(ancestor), "previous": previous,
            "displaced": identity(real_stat(displaced)),
            "replacement": identity(real_stat(ancestor)),
            "boundary": "before-reopen",
        })
    try:
        descriptor = real_open(path, flags, *args, **kwargs)
    except PermissionError as error:
        if name == str(ancestor):
            access_error = error
        raise
    observed(name, os.fstat(descriptor))
    return descriptor

def observing_mkdir(path, *args, **kwargs):
    global replaced
    name = absolute(path, kwargs.get("dir_fd"))
    if (
        mode == "replace-at-deferred-mkdir"
        and name == str(runtime / "deferred")
        and ancestor_confirmed
        and not replaced
    ):
        previous = identity(real_stat(runtime))
        os.rename(runtime, displaced)
        real_mkdir(runtime)
        replaced = True
        events.append({
            "kind": "replaced", "path": str(runtime), "previous": previous,
            "displaced": identity(real_stat(displaced)),
            "replacement": identity(real_stat(runtime)),
            "boundary": "deferred-mkdir",
        })
    forbidden = mode == "forbid-ancestor-mkdir" and Path(name) in runtime.parents
    events.append({"kind": "mkdir", "path": name, "forbidden": forbidden})
    if forbidden:
        raise PermissionError(errno.EPERM, "injected forbidden ancestor mkdir", name)
    return real_mkdir(path, *args, **kwargs)

def observing_fsync(descriptor):
    global ancestor_confirmed
    value = os.fstat(descriptor)
    real_fsync(descriptor)
    if not stat.S_ISDIR(value.st_mode):
        return
    name = known_directories.get(tuple(identity(value)))
    events.append({"kind": "fsync", "path": name, "identity": identity(value)})
    if name == str(ancestor.parent):
        ancestor_confirmed = True

def search_capability():
    if os.geteuid() == 0:
        return {"skip": "root bypasses execute-only directory permissions"}
    search = getattr(os, "O_SEARCH", getattr(os, "O_EXEC", None))
    if search is None:
        return {"skip": "platform has no native fsync-capable O_SEARCH descriptor"}
    try:
        descriptor = real_open(ancestor, os.O_RDONLY | os.O_DIRECTORY)
    except PermissionError:
        pass
    else:
        os.close(descriptor)
        raise AssertionError("read access bypasses the real 0111 directory mode")
    descriptor = None
    try:
        descriptor = real_open(ancestor, search | os.O_DIRECTORY)
        real_fsync(descriptor)
    except OSError as error:
        return {"skip": f"native O_SEARCH directory fsync unavailable: {error}"}
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return {
        "native_search_flag": search,
        "directory_flag": os.O_DIRECTORY,
    }

@contextmanager
def without_search_descriptors():
    hidden = {}
    for name in ("O_SEARCH", "O_EXEC"):
        if hasattr(os, name):
            hidden[name] = getattr(os, name)
            delattr(os, name)
    try:
        yield
    finally:
        for name, value in hidden.items():
            setattr(os, name, value)

def invoke():
    capability = search_capability() if mode in {"search", "no-search"} else {}
    if "skip" in capability:
        return {"exit": 0, **capability}
    descriptors_hidden = False
    try:
        with (
            without_search_descriptors() if mode == "no-search" else nullcontext(),
        ):
            descriptors_hidden = not hasattr(os, "O_SEARCH") and not hasattr(
                os, "O_EXEC"
            )
            from ovcaq.workflow.records import record_defer
            with (
                patch.object(os, "open", observing_open),
                patch.object(os, "stat", observing_stat),
                patch.object(os, "mkdir", observing_mkdir),
                patch.object(os, "fsync", observing_fsync),
            ):
                path = record_defer(
                    runtime, "00004-a.md", "batch", {"op_id": "replacement-probe"}
                )
                if mode == "reparent-during-publication":
                    events.append({"kind": "returned", "path": str(path)})
    except Exception as error:
        return {
            "exit": 2, "error": str(error), "os_error": isinstance(error, OSError),
            "permission_error": isinstance(error, PermissionError),
            "errno": error.errno if isinstance(error, OSError) else None,
            "cause_type": (
                type(error.__cause__).__name__ if error.__cause__ is not None else None
            ),
            "cause_errno": (
                error.__cause__.errno
                if isinstance(error.__cause__, OSError)
                else None
            ),
            "cause_is_original": error.__cause__ is access_error,
            "descriptors_hidden": descriptors_hidden,
            **capability,
        }
    return {
        "exit": 0,
        "path": str(path),
        "descriptors_hidden": descriptors_hidden,
        **capability,
    }

result = invoke()
result.update({"origins": installed_origins(), "events": events})
print(json.dumps(result), flush=True)
raise SystemExit(result["exit"])
"""
)
