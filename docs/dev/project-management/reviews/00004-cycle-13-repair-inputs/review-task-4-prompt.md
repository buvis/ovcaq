
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D13] Preserve confirmed ancestry across replacement and access boundaries (M)


Description:
Review cycle 13 follow-up. PAUSED: no execution is authorized by the connectivity recovery or this artifact. Operator recovery must authorize repairs; preserve the fresh work/review boundary.

### Findings (verbatim)
- high: An ancestor replaced after its confirmation is silently adopted as the next level's parent; defer returns success without fsyncing the replacement ancestor's parent | File: src/ovcaq/workflow/_files.py:255 | Consensus: coordinator; Alice adjudication confirms
- medium: `_ensure_directory_chain` now opens every absolute ancestor with `O_RDONLY`, so a configured runtime below a search-only directory can be traversable and writable yet defer fails with `EACCES`; preserve crash confirmation while opening only directories OVCAQ must confirm or use a descriptor mode compatible with execute-only traversal | File: src/ovcaq/workflow/_files.py:256 | Consensus: 2/3
- medium: The ancestry loop treats the filesystem root as its own child, opening `/` twice, calling `mkdir(exist_ok=True)` on it, and fsyncing it even though OVCAQ can never create that anchor; exclude the root self-step while retaining parent confirmation for every potentially interrupted runtime ancestor | File: src/ovcaq/workflow/_files.py:255 | Consensus: 2/3
- medium: B5: Suspected sandbox break: defer/stall/park now issue mkdir and open(O_RDONLY|O_DIRECTORY) against `/`, `/Users`, `$HOME` from inside launcher sessions that run under `codex exec --sandbox workspace-write` (plan §10.4); Path.mkdir(exist_ok=True) swallows only FileExistsError, so a seatbelt EPERM ahead of the kernel EEXIST fails every ledger write | File: src/ovcaq/workflow/_files.py:257 | Consensus: 1/3

### Acceptance criteria
Every quoted defect no longer reproduces. Before successful publication or exact replay, an ancestor inode adopted after a prior confirmation must either be refused with a retryable identity error or have its own parent confirmed again. Preserve existing abrupt-exit retries, peer creation, identity checks, exactly-once records, and state/backup bytes. Preserve search-only path access without dropping required confirmations. Remove only the redundant root self-step. Resolve the launcher-sandbox VERIFY finding with a concrete supported check; do not launch nested Codex, strip guards, or claim coverage from a different sandbox.

### Evidence
Review: dev/local/reviews/00004-workflow-core-v1-review-13.md
Probe: dev/local/reviews/00004-cycle-13-approved-installed-probe.json
Original work base, cycle 13 and cap 2 remain unchanged.


Acceptance criteria:
Every quoted defect no longer reproduces. Before successful publication or exact replay, an ancestor inode adopted after a prior confirmation must either be refused with a retryable identity error or have its own parent confirmed again. Preserve existing abrupt-exit retries, peer creation, identity checks, exactly-once records, and state/backup bytes. Preserve search-only path access without dropping required confirmations. Remove only the redundant root self-step. Resolve the launcher-sandbox VERIFY finding with a concrete supported check; do not launch nested Codex, strip guards, or claim coverage from a different sandbox.


## Diff under review

```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 5d12c9e..337e86e 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -21,6 +21,7 @@ The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
 
 ### Fixed
 
+- Deferred ancestry confirmation detects replaced ancestors on reopen, supports search-only access, and avoids redundant ancestor creation and root confirmation.
 - Shared publication contention reports `publication busy; retry: <path>` for both reports and deferred ledgers.
 - Deferred retries and replays confirm existing runtime ancestry after abrupt exits and preserve directories created by concurrent callers when confirmation fails.
 - Deferred publication validates the complete prospective ledger and persists newly created runtime ancestors; overlapping report renders no longer lose successful sections.
diff --git a/src/ovcaq/workflow/_files.py b/src/ovcaq/workflow/_files.py
index 0c01264..d016231 100644
--- a/src/ovcaq/workflow/_files.py
+++ b/src/ovcaq/workflow/_files.py
@@ -6,6 +6,7 @@ import fcntl
 import json
 import os
 import stat
+import sys
 import uuid
 from collections.abc import Callable, Iterator
 from contextlib import contextmanager
@@ -252,15 +253,29 @@ def _sync_deferred_directory(path: Path, directory: int) -> None:
 def _ensure_directory_chain(path: Path) -> None:
     """Confirm every ancestor, including levels left by interrupted creators."""
     path = path.resolve()
-    for level in (*reversed(path.parents), path):
-        with _open_lifecycle_directory(level.parent, label="runtime") as parent:
-            level.mkdir(exist_ok=True)
-            with _open_lifecycle_directory(level, label="runtime") as directory:
+    levels = (*reversed(path.parents), path)
+    confirmed: tuple[int, int] | None = None
+    for level in levels[1:]:
+        with _open_lifecycle_directory(
+            level.parent, label="runtime", search_only=True
+        ) as parent:
+            opened = os.fstat(parent)
+            if confirmed is not None and confirmed != (opened.st_dev, opened.st_ino):
+                raise OSError(
+                    f"runtime directory identity changed; retry: {level.parent}"
+                )
+            if not level.exists():
+                level.mkdir(exist_ok=True)
+            with _open_lifecycle_directory(
+                level, label="runtime", search_only=True
+            ) as directory:
                 os.fsync(parent)
                 _verify_lifecycle_directory_identity(
                     level.parent, parent, label="runtime"
                 )
                 _verify_lifecycle_directory_identity(level, directory, label="runtime")
+                opened = os.fstat(directory)
+                confirmed = (opened.st_dev, opened.st_ino)
 
 
 @contextmanager
@@ -376,13 +391,20 @@ def _open_lifecycle_directory(
     *,
     create: bool = False,
     label: str = "lifecycle",
+    search_only: bool = False,
 ) -> Iterator[int]:
     """Open a verified lifecycle directory without following its final link."""
     if create:
         directory.mkdir(exist_ok=True)
         _fsync_directory(directory.parent)
+    access = os.O_RDONLY
+    if search_only:
+        # Python may omit Darwin's native, fsync-capable O_SEARCH constant.
+        access = getattr(
+            os, "O_SEARCH", 0x40000000 if sys.platform == "darwin" else os.O_RDONLY
+        )
     flags = (
-        os.O_RDONLY
+        access
         | getattr(os, "O_DIRECTORY", 0)
         | getattr(os, "O_NOFOLLOW", 0)
         | getattr(os, "O_CLOEXEC", 0)
diff --git a/tests/packaging/rework_13_scripts.py b/tests/packaging/rework_13_scripts.py
new file mode 100644
index 0000000..100bada
--- /dev/null
+++ b/tests/packaging/rework_13_scripts.py
@@ -0,0 +1,147 @@
+from __future__ import annotations
+
+from rework_12_scripts import ORIGIN_CHECK
+
+__all__ = ["ANCESTRY_BOUNDARY_ACTOR"]
+
+ANCESTRY_BOUNDARY_ACTOR = (
+    ORIGIN_CHECK
+    + r"""
+import errno
+import os
+import stat
+from unittest.mock import patch
+from ovcaq.workflow.records import record_defer
+
+project = Path(sys.argv[1])
+mode = sys.argv[2]
+runtime = Path(sys.argv[3])
+ancestor = Path(sys.argv[4])
+displaced = project / "displaced"
+real_open = os.open
+real_stat = os.stat
+real_mkdir = os.mkdir
+real_fsync = os.fsync
+events = []
+replaced = False
+ancestor_confirmed = False
+known_directories = {}
+
+def identity(value):
+    return [value.st_dev, value.st_ino]
+
+for directory in (*runtime.parents, runtime, runtime / "deferred"):
+    try:
+        known_directories[tuple(identity(real_stat(directory)))] = str(directory)
+    except FileNotFoundError:
+        pass
+
+def absolute(path, dir_fd=None):
+    if isinstance(path, int):
+        return known_directories.get(tuple(identity(os.fstat(path))))
+    name = os.fsdecode(path)
+    if not os.path.isabs(name) and dir_fd is not None:
+        parent = known_directories[tuple(identity(os.fstat(dir_fd)))]
+        name = os.path.join(parent, name)
+    return os.path.abspath(name)
+
+def observed(path, value):
+    if stat.S_ISDIR(value.st_mode):
+        key = identity(value)
+        known_directories[tuple(key)] = path
+        events.append({"kind": "observed", "path": path, "identity": key})
+
+def observing_stat(path, *args, **kwargs):
+    value = real_stat(path, *args, **kwargs)
+    observed(absolute(path, kwargs.get("dir_fd")), value)
+    return value
+
+def observing_open(path, flags, *args, **kwargs):
+    global replaced
+    name = absolute(path, kwargs.get("dir_fd"))
+    if mode == "replace" and name == str(ancestor) and ancestor_confirmed and not replaced:
+        previous = identity(real_stat(ancestor))
+        os.rename(ancestor, displaced)
+        real_mkdir(ancestor)
+        replaced = True
+        events.append({
+            "kind": "replaced", "path": str(ancestor), "previous": previous,
+            "displaced": identity(real_stat(displaced)),
+            "replacement": identity(real_stat(ancestor)),
+            "boundary": "before-reopen",
+        })
+    descriptor = real_open(path, flags, *args, **kwargs)
+    observed(name, os.fstat(descriptor))
+    return descriptor
+
+def observing_mkdir(path, *args, **kwargs):
+    name = absolute(path, kwargs.get("dir_fd"))
+    forbidden = mode == "forbid-ancestor-mkdir" and Path(name) in runtime.parents
+    events.append({"kind": "mkdir", "path": name, "forbidden": forbidden})
+    if forbidden:
+        raise PermissionError(errno.EPERM, "injected forbidden ancestor mkdir", name)
+    return real_mkdir(path, *args, **kwargs)
+
+def observing_fsync(descriptor):
+    global ancestor_confirmed
+    value = os.fstat(descriptor)
+    real_fsync(descriptor)
+    if not stat.S_ISDIR(value.st_mode):
+        return
+    name = known_directories.get(tuple(identity(value)))
+    events.append({"kind": "fsync", "path": name, "identity": identity(value)})
+    if name == str(ancestor.parent):
+        ancestor_confirmed = True
+
+def search_capability():
+    if os.geteuid() == 0:
+        return {"skip": "root bypasses execute-only directory permissions"}
+    # Darwin exposes O_SEARCH natively even when Python omits the constant.
+    search = getattr(os, "O_SEARCH", 0x40000000 if sys.platform == "darwin" else None)
+    if search is None:
+        return {"skip": "platform has no native fsync-capable O_SEARCH descriptor"}
+    try:
+        descriptor = real_open(ancestor, os.O_RDONLY | os.O_DIRECTORY)
+    except PermissionError:
+        pass
+    else:
+        os.close(descriptor)
+        raise AssertionError("read access bypasses the real 0111 directory mode")
+    descriptor = None
+    try:
+        descriptor = real_open(ancestor, search | os.O_DIRECTORY)
+        real_fsync(descriptor)
+    except OSError as error:
+        return {"skip": f"native O_SEARCH directory fsync unavailable: {error}"}
+    finally:
+        if descriptor is not None:
+            os.close(descriptor)
+    return {"euid": os.geteuid(), "read_denied": True, "search_fsync": True}
+
+def invoke():
+    capability = search_capability() if mode == "search" else {}
+    if "skip" in capability:
+        return {"exit": 0, **capability}
+    try:
+        with (
+            patch.object(os, "open", observing_open),
+            patch.object(os, "stat", observing_stat),
+            patch.object(os, "mkdir", observing_mkdir),
+            patch.object(os, "fsync", observing_fsync),
+        ):
+            path = record_defer(
+                runtime, "00004-a.md", "batch", {"op_id": "replacement-probe"}
+            )
+    except Exception as error:
+        return {
+            "exit": 2, "error": str(error), "os_error": isinstance(error, OSError),
+            **capability,
+        }
+    return {"exit": 0, "path": str(path), **capability}
+
+result = invoke()
+result.update({"origins": installed_origins(), "events": events})
+print(json.dumps(result), flush=True)
+raise SystemExit(result["exit"])
+"""
+)
diff --git a/tests/packaging/test_rework_13.py b/tests/packaging/test_rework_13.py
new file mode 100644
index 0000000..5a90f4d
--- /dev/null
+++ b/tests/packaging/test_rework_13.py
@@ -0,0 +1,274 @@
+from __future__ import annotations
+
+import json
+import stat
+import subprocess
+from pathlib import Path
+from typing import Any
+from uuid import uuid4
+
+import pytest
+from packaging_support import InstalledWheel, run_checked
+from rework_11_scripts import INITIALIZE_STATE
+from rework_12_scripts import ORIGIN_CHECK
+from rework_13_scripts import ANCESTRY_BOUNDARY_ACTOR
+
+PRD = "00004-a.md"
+
+
+def _assert_installed(origins: dict[str, str], installed: InstalledWheel) -> None:
+    assert "ovcaq.workflow.records" in origins
+    for module, filename in origins.items():
+        path = Path(filename).resolve()
+        assert path.is_relative_to(installed.root.resolve()), (module, filename)
+        assert "site-packages" in path.parts, (module, filename)
+
+
+def _prepare(installed: InstalledWheel, tmp_path: Path) -> Path:
+    project = tmp_path.resolve() / "project"
+    state = project / "independent/state.json"
+    project.mkdir()
+    script = (
+        INITIALIZE_STATE
+        + ORIGIN_CHECK
+        + "\nfrom ovcaq.workflow.records import record_defer\n"
+        + "print(json.dumps(installed_origins()))\n"
+    )
+    result = run_checked(
+        [installed.python, "-I", "-c", script, project, state, PRD],
+        cwd=project,
+        env=installed.environment,
+    )
+    _assert_installed(json.loads(result.stdout), installed)
+    state.with_suffix(".json.bak").write_bytes(state.read_bytes())
+    (project / "ancestor").mkdir()
+    return project
+
+
+def _state_bytes(project: Path) -> tuple[bytes, bytes]:
+    state = project / "independent/state.json"
+    return state.read_bytes(), state.with_suffix(".json.bak").read_bytes()
+
+
+def _identity(path: Path) -> list[int]:
+    value = path.stat()
+    return [value.st_dev, value.st_ino]
+
+
+def _invoke(
+    installed: InstalledWheel,
+    project: Path,
+    mode: str,
+    *,
+    runtime: Path | None = None,
+    ancestor: Path | None = None,
+) -> dict[str, Any]:
+    if runtime is None:
+        runtime = project / "ancestor/runtime"
+    if ancestor is None:
+        ancestor = runtime.parent
+    result = subprocess.run(
+        [
+            installed.python,
+            "-I",
+            "-c",
+            ANCESTRY_BOUNDARY_ACTOR,
+            str(project),
+            mode,
+            str(runtime),
+            str(ancestor),
+        ],
+        cwd=project,
+        env=installed.environment,
+        capture_output=True,
+        text=True,
+        check=False,
+        timeout=20,
+    )
+    value: dict[str, Any] = json.loads(result.stdout)
+    _assert_installed(value["origins"], installed)
+    assert result.returncode == value["exit"], (result.stdout, result.stderr)
+    return value
+
+
+def _ledger(runtime: Path) -> Path:
+    return runtime / "deferred/batch-deferred.json"
+
+
+def _assert_one_record(runtime: Path) -> bytes:
+    content = _ledger(runtime).read_bytes()
+    assert json.loads(content) == {
+        "batch_id": "batch",
+        "items": [{"op_id": "replacement-probe", "prd": PRD}],
+    }
+    return content
+
+
+def _assert_replaced_after_confirmation(
+    interrupted: dict[str, Any], project: Path, ancestor: Path, previous: list[int]
+) -> None:
+    events = interrupted["events"]
+    replacements = [event for event in events if event["kind"] == "replaced"]
+    assert len(replacements) == 1, interrupted
+    replacement = replacements[0]
+    assert replacement["previous"] == previous
+    assert replacement["displaced"] == previous == _identity(project / "displaced")
+    assert replacement["replacement"] == _identity(ancestor)
+    assert replacement["replacement"] != previous
+    assert replacement["boundary"] == "before-reopen"
+    index = events.index(replacement)
+    assert {
+        "kind": "fsync",
+        "path": str(ancestor.parent),
+        "identity": _identity(ancestor.parent),
+    } in events[:index]
+    assert {
+        "kind": "observed",
+        "path": str(ancestor),
+        "identity": previous,
+    } in events[:index]
+    assert events[index + 1] == {
+        "kind": "observed",
+        "path": str(ancestor),
+        "identity": replacement["replacement"],
+    }
+    assert not any(
+        event["kind"] == "fsync" and event["path"] == str(ancestor)
+        for event in events[:index]
+    ), interrupted
+
+
+@pytest.mark.parametrize("replay", (False, True), ids=("direct", "exact-replay"))
+@pytest.mark.parametrize("position", ("parent", "nested-parent"))
+def test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt(
+    installed_wheel: InstalledWheel, tmp_path: Path, replay: bool, position: str
+) -> None:
+    project = _prepare(installed_wheel, tmp_path)
+    authoritative = _state_bytes(project)
+    container = project if position == "parent" else project / "branch"
+    ancestor = container / uuid4().hex
+    ancestor.mkdir(parents=True)
+    runtime = ancestor / "runtime"
+    displaced_runtime = project / "displaced" / runtime.relative_to(ancestor)
+    previous = _identity(ancestor)
+    seeded = None
+    if replay:
+        assert (
+            _invoke(
+                installed_wheel, project, "normal", runtime=runtime, ancestor=ancestor
+            )["exit"]
+            == 0
+        )
+        seeded = _assert_one_record(runtime)
+        assert _state_bytes(project) == authoritative
+
+    interrupted = _invoke(
+        installed_wheel, project, "replace", runtime=runtime, ancestor=ancestor
+    )
+    _assert_replaced_after_confirmation(interrupted, project, ancestor, previous)
+    assert interrupted["exit"] == 2, interrupted
+    assert interrupted["os_error"] is True, interrupted
+    assert "identity changed; retry" in interrupted["error"]
+    assert str(ancestor) in interrupted["error"].split("identity changed; retry", 1)[1]
+    assert "path" not in interrupted
+    assert not _ledger(runtime).exists()
+    assert _state_bytes(project) == authoritative
+    if replay:
+        assert _ledger(displaced_runtime).read_bytes() == seeded
+    else:
+        assert not _ledger(displaced_runtime).exists()
+
+    retry = _invoke(
+        installed_wheel, project, "normal", runtime=runtime, ancestor=ancestor
+    )
+    assert retry["exit"] == 0, retry
+    assert retry["path"] == str(_ledger(runtime))
+    _assert_one_record(runtime)
+    assert _state_bytes(project) == authoritative
+    if replay:
+        assert _ledger(displaced_runtime).read_bytes() == seeded
+
+
+def test_installed_defer_confirms_parent_through_native_search_only_access(
+    installed_wheel: InstalledWheel, tmp_path: Path
+) -> None:
+    project = _prepare(installed_wheel, tmp_path)
+    authoritative = _state_bytes(project)
+    ancestor = project / "ancestor"
+    runtime = ancestor / "runtime"
+    runtime.mkdir()
+    original_mode = stat.S_IMODE(ancestor.stat().st_mode)
+    try:
+        ancestor.chmod(0o111)
+        assert stat.S_IMODE(ancestor.stat().st_mode) == 0o111
+        result = _invoke(installed_wheel, project, "search")
+    finally:
+        ancestor.chmod(original_mode)
+    assert _state_bytes(project) == authoritative
+    if "skip" in result:
+        pytest.skip(result["skip"])
+    assert result["exit"] == 0, result
+    assert result["euid"] != 0
+    assert result["read_denied"] is True
+    assert result["search_fsync"] is True
+    assert {
+        "kind": "fsync",
+        "path": str(ancestor),
+        "identity": _identity(ancestor),
+    } in result["events"]
+    assert result["path"] == str(_ledger(runtime))
+    _assert_one_record(runtime)
+
+
+def test_installed_defer_confirms_first_descendant_without_root_self_confirmation(
+    installed_wheel: InstalledWheel, tmp_path: Path
+) -> None:
+    project = _prepare(installed_wheel, tmp_path)
+    authoritative = _state_bytes(project)
+    result = _invoke(installed_wheel, project, "normal")
+    assert result["exit"] == 0, result
+    root = Path(project.anchor)
+    first_descendant = root / project.parts[1]
+    events = result["events"]
+    assert not any(
+        event["kind"] == "mkdir" and event["path"] == str(root) for event in events
+    ), result
+    confirmations = [
+        event
+        for event in events
+        if event["kind"] == "fsync" and event["path"] == str(root)
+    ]
+    assert confirmations == [
+        {"kind": "fsync", "path": str(root), "identity": _identity(root)}
+    ], result
+    assert {
+        "kind": "observed",
+        "path": str(first_descendant),
+        "identity": _identity(first_descendant),
+    } in events[: events.index(confirmations[0])]
+    _assert_one_record(project / "ancestor/runtime")
+    assert _state_bytes(project) == authoritative
+
+
+def test_installed_defer_avoids_creation_attempts_on_existing_external_ancestors(
+    installed_wheel: InstalledWheel, tmp_path: Path
+) -> None:
+    project = _prepare(installed_wheel, tmp_path)
+    authoritative = _state_bytes(project)
+    result = _invoke(installed_wheel, project, "forbid-ancestor-mkdir")
+    assert result["exit"] == 0, result
+    assert not [
+        event
+        for event in result["events"]
+        if event["kind"] == "mkdir" and event["forbidden"]
+    ], result
+    runtime = project / "ancestor/runtime"
+    for parent in runtime.parents:
+        assert {
+            "kind": "fsync",
+            "path": str(parent),
+            "identity": _identity(parent),
+        } in result["events"], (str(parent), result)
+    assert result["path"] == str(_ledger(runtime))
+    _assert_one_record(runtime)
+    assert _state_bytes(project) == authoritative
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

Operator explicitly authorized repairs of tasks 4–6; the PAUSED wording in the historical task text is superseded by that recorded request. Workflow remains paused until all repairs and the fresh-session handoff are ready.

mise exec -- uv run --offline --no-sync pytest tests/packaging/test_rework_13.py -q --basetemp /private/tmp/ovcaq-r13-task4-green
Exit 0: 7 passed in 1.14s. Before implementation at test commit c1b9345787cfb0534d70d3a96fc905b414468b57, the same seven cases all failed against unchanged production; all four replacement cases reached the incorrect success result after confirming actual replacement chronology.

mise exec -- uv run --offline --no-sync python dev/local/reviews/00004-cycle-13-distant-ancestor-check.py /private/tmp/ovcaq-r13-task4-green/ovcaq-installed-wheel0/venv
Exit 0: replacement three and five levels above runtime, direct and exact replay, all refused with the path-specific identity retry OSError; fresh retry produced exactly one record. Installed origin assertions, real replacement chronology, state/backup bytes and displaced prior ledgers verified. The same four probes succeeded incorrectly on the baseline installed wheel. Evidence: dev/local/reviews/00004-cycle-13-distant-after.json.

Adversarial validation ran both mandated rounds. Round 1 found literal-name coverage weakness; generated-name tests killed that mutant. Round 2 found that a mutant checking only the last two ancestors could still pass all seven tests. Two-round cap honored and limitation recorded; the additional distant-ancestor probe above addresses that concrete gap for this implementation. This does not claim that the committed tests are exhaustive.

mise exec -- codex sandbox -P :workspace --include-managed-config -C /Users/bob/git/src/github.com/buvis/ovcaq -- /Users/bob/git/src/github.com/buvis/ovcaq/.venv/bin/python /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/reviews/00004-cycle-13-sandbox-check.py
Exit 0 before and after the repair. This is the installed Codex 0.154.0 supported local sandbox executor, with the actual workspace policy and managed configuration, not a model dispatch or different substitute sandbox. A unique write outside the workspace was denied with EPERM; source-checkout CLI defer/stall/park each returned 0 and exactly one deferred record. No nested agent and no guard stripping. The universal sandbox failure suspicion is refuted for the installed launcher. It incorrectly assumes current pathlib swallows only FileExistsError; the production diff now also avoids existing-ancestor mkdir entirely. Historical launcher versions and physical power loss were not tested. Evidence: dev/local/reviews/00004-cycle-13-sandbox-after.json.

Style-limit and split-hygiene checks passed for all task candidates. Implementation commit net +23 lines in two files: self-deslop skipped under the explicit trivial-change rule. Full repository verification follows tasks 5 and 6; prior crash/peer tests have not yet been rerun on this implementation.


Judge only from this prompt: the diff above, the task text, and this recorded
result. Do not read other files, run commands, or re-run the tests. What is not
in this prompt is not evidence, and a finding you cannot ground in what is here
is one you should not report.

# Simplification Mandate (step 5.7 reviewer-prompt appendix)

Append this block **verbatim** to every per-task code-reviewer prompt (see
`SKILL.md` step 5.7). It ships inside the prompt, so it must stay
self-contained.

> Beyond bugs, actively hunt for simplification in the diff under review. For
> every added or changed file, ask "what would make this simpler to read
> without changing what it does?" and flag concrete behavior-preserving
> opportunities to: reduce complexity (needless indirection, dead branches,
> single-caller abstractions, nesting deeper than 4 levels, functions over 50
> lines); eliminate redundancy (logic duplicated within the diff or against
> existing code, a helper that reimplements a stdlib or existing utility);
> improve naming (names that state intent, no opaque abbreviations); and
> remove dead code. Follow CLAUDE.md / AGENTS.md conventions and the
> surrounding code's style.
>
> Report each concrete behavior-preserving simplification as a LOW finding,
> with file:line, the current shape, and the simpler replacement. LOW findings
> are carried to the PRD-level review, never retried here.
>
> Do not over-simplify: never propose a change that trades clarity for
> brevity, drops error handling, collapses a deliberate boundary, or removes a
> documented invariant. Simpler means easier to read and maintain, not shorter
> at any cost. If a change would alter behavior, it is out of scope — do not
> flag it.


## Reporting contract

Report one finding per line, in exactly this shape:

SEVERITY | file:line | issue | fix

Severities are CRITICAL, HIGH, MEDIUM, LOW.

Severity has a fixed meaning here, and it decides what happens next. MEDIUM is
reserved for a correctness or security defect this diff introduces that its own
tests do not catch: a wrong result, an unhandled error path, data loss,
injection, secret exposure, or a missing authorization check. Style, naming,
duplication, structure and maintainability are LOW, and so is every
behavior-preserving simplification, whatever its size. A LOW is noted and
carried to the PRD-level review; it is never retried in this loop.

If the diff has no findings, emit the literal line:

NO FINDINGS

## Closure verdicts (only when the description carries a findings block)

When the Description above contains a `### Findings (verbatim)` block, this is
a rework task and each quoted finding is a claim to check. Before your findings
lines, emit one verdict per quoted finding, in this shape:

CLOSURE | resolved|unresolved | <the finding, quoted> | <one line of evidence from the diff>

Judge each finding against the diff, not against the commit message and not
against how clean the code reads. A diff that improves the file while leaving
the quoted defect reachable is `unresolved`. Quote the line that resolves it,
or say what still reaches the defect. Emit a verdict for every quoted finding,
including ones you judge already fixed elsewhere.


