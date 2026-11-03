
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D16] Close deferred diagnostic and regression cleanup tail (M)


Description:
Fix the seven bounded cycle-16 diagnostic/test/style findings. This tail introduces full configured-path context for deferred-directory creation errors while preserving each original OSError as __cause__. Preserve the existing filesystem publication/locking/fsync algorithm and its chronology.

Contract:
- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/workflow/_files.py: private deferred-directory diagnostics and behavior-preserving function extraction; public record_defer(runtime_root: Path, prd: str, batch_id: str, record: dict, *, boundary_hook=None) -> Path is unchanged.
- /Users/bob/git/src/github.com/buvis/ovcaq/tests/workflow/test_deferred_diagnostics.py: Tess-owned new behavioral regressions, read-only for Ivan.
- /Users/bob/git/src/github.com/buvis/ovcaq/tests/packaging/test_rework_13.py: preserve installed-wheel/reparent direct and replay chronology and all parameter cases while shortening the 80-line test, using subprocess.run timeout handling, and pinning direct refusal before ledger creation.
- /Users/bob/git/src/github.com/buvis/ovcaq/CHANGELOG.md: mention the full-path diagnostics for open/create errors.
No exported signature/schema/wire format change; no new algorithm or persisted-data transform.

### Findings (verbatim)
🟡 The restored deferred-directory diagnostic has no committed regression covering initial file/symlink refusal or the vanished-directory second open, including full path and preserved cause/errno | File: tests/packaging/test_rework_13.py | Consensus: [2/3]
🟡 `_ensure_directory_chain` is 51 lines because it embeds the 13-line ancestry verifier; move that verifier to a named helper to satisfy the function-size limit and simplify the chain walk | File: src/ovcaq/workflow/_files.py:268 | Consensus: [2/3]
🟡 `test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry` is 80 lines; extract the safe-result and retry/replay assertion flows into helpers while retaining the parameterized chronology | File: tests/packaging/test_rework_13.py:357 | Consensus: [2/3]
🟡 F4: _invoke reimplements subprocess.run's timeout kill/reap as a 16-line Popen block plus a framework-verifying `assert process.poll() is not None`; subprocess.run(timeout=20) already kills and waits on TimeoutExpired, and test_rework_12._invoke in the same diff keeps subprocess.run | File: tests/packaging/test_rework_13.py:58 | Consensus: [1/3]
⚪ F5: os.mkdir(deferred.name, dir_fd=runtime) failures other than EEXIST (EACCES, ENOSPC, EBADF) still surface raw errno text with the bare name 'deferred'; same class as R15-03, on the create step the acceptance ("every failing open") did not name | File: src/ovcaq/workflow/_files.py:340 | Consensus: [1/3]
⚪ F6: fix commit 93c049b changed a user-visible diagnostic (full deferred path on open failure) without a CHANGELOG entry; the only added Fixed line covers ancestry revalidation | File: CHANGELOG.md:24 | Consensus: [1/3]
⚪ F7: reparent-refusal branch hedges `if _ledger(runtime).exists(): _assert_one_record(runtime)`; the shipped chronology deterministically refuses inside the first _read_record_content before any write, so the direct case should pin that no ledger exists | File: tests/packaging/test_rework_13.py:406 | Consensus: [1/3]

Acceptance criteria:
- Every quoted finding no longer reproduces.
- Committed tests cover existing deferred path as real regular file and symlink, the second open after disappearance, and creation OSErrors EACCES/ENOSPC/EBADF; full path is in the outer error and original cause errno is retained. Existing file/symlink and target sentinel remain untouched; no deferred record is published on refusal.
- Both open failures use "deferred directory is not a real directory: <full path>"; creation failure uses "deferred directory could not be created: <full path>".
- Named function extraction keeps all modified Python functions <=50 lines. Maintain all real durability checks, direct/replay parameter cases and installed module-origin checks. Subprocess timeouts remain bounded and reaped by subprocess.run(timeout=20).
- No ledger is created on the direct reparent-refusal chronology; replay preserves authoritative bytes.
Verify: mise exec -- uv run pytest tests/workflow/test_deferred_diagnostics.py


Acceptance criteria:
- Every quoted finding no longer reproduces.
- Committed tests cover existing deferred path as real regular file and symlink, the second open after disappearance, and creation OSErrors EACCES/ENOSPC/EBADF; full path is in the outer error and original cause errno is retained. Existing file/symlink and target sentinel remain untouched; no deferred record is published on refusal.
- Both open failures use "deferred directory is not a real directory: <full path>"; creation failure uses "deferred directory could not be created: <full path>".
- Named function extraction keeps all modified Python functions <=50 lines. Maintain all real durability checks, direct/replay parameter cases and installed module-origin checks. Subprocess timeouts remain bounded and reaped by subprocess.run(timeout=20).
- No ledger is created on the direct reparent-refusal chronology; replay preserves authoritative bytes.


## Diff under review

```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 6f8592d..c2517fa 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -21,6 +21,7 @@ The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
 
 ### Fixed
 
+- Deferred directory setup diagnostics report the full configured path while preserving the originating OS error.
 - Deferred publication revalidates the complete confirmed runtime ancestry before returning success.
 - Deferred ancestry confirmation detects replaced ancestors on reopen, supports search-only access, and avoids redundant ancestor creation and root confirmation.
 - Shared publication contention reports `publication busy; retry: <path>` for both reports and deferred ledgers.
diff --git a/src/ovcaq/workflow/_files.py b/src/ovcaq/workflow/_files.py
index 1085135..bb3b0db 100644
--- a/src/ovcaq/workflow/_files.py
+++ b/src/ovcaq/workflow/_files.py
@@ -264,6 +264,21 @@ def _sync_deferred_directory(path: Path, directory: int) -> None:
     _verify_lifecycle_directory_identity(path, directory, label="deferred")
 
 
+def _verify_directory_chain(ancestry: dict[Path, tuple[int, int]]) -> None:
+    for ancestor, identity in ancestry.items():
+        try:
+            linked = os.stat(ancestor, follow_symlinks=False)
+        except OSError as error:
+            raise OSError(
+                f"runtime directory identity changed; retry: {ancestor}"
+            ) from error
+        if not stat.S_ISDIR(linked.st_mode) or identity != (
+            linked.st_dev,
+            linked.st_ino,
+        ):
+            raise OSError(f"runtime directory identity changed; retry: {ancestor}")
+
+
 @contextmanager
 def _ensure_directory_chain(
     path: Path,
@@ -275,18 +290,7 @@ def _ensure_directory_chain(
     ancestry: dict[Path, tuple[int, int]] = {}
 
     def verify_ancestry() -> None:
-        for ancestor, identity in ancestry.items():
-            try:
-                linked = os.stat(ancestor, follow_symlinks=False)
-            except OSError as error:
-                raise OSError(
-                    f"runtime directory identity changed; retry: {ancestor}"
-                ) from error
-            if not stat.S_ISDIR(linked.st_mode) or identity != (
-                linked.st_dev,
-                linked.st_ino,
-            ):
-                raise OSError(f"runtime directory identity changed; retry: {ancestor}")
+        _verify_directory_chain(ancestry)
 
     for level in levels[1:]:
         with _open_lifecycle_directory(
@@ -340,6 +344,10 @@ def _open_deferred_ledger(
                 os.mkdir(deferred.name, mode=0o700, dir_fd=runtime)
             except FileExistsError:
                 pass
+            except OSError as error:
+                raise OSError(
+                    f"deferred directory could not be created: {deferred}"
+                ) from error
             verify_runtime()
             try:
                 directory = os.open(deferred.name, flags, dir_fd=runtime)
diff --git a/tests/packaging/test_rework_13.py b/tests/packaging/test_rework_13.py
index 58a9f11..ded3c8e 100644
--- a/tests/packaging/test_rework_13.py
+++ b/tests/packaging/test_rework_13.py
@@ -55,7 +55,7 @@ def _invoke(
         runtime = project / "ancestor/runtime"
     if ancestor is None:
         ancestor = runtime.parent
-    with subprocess.Popen(
+    process = subprocess.run(
         [
             installed.python,
             "-I",
@@ -68,19 +68,13 @@ def _invoke(
         ],
         cwd=project,
         env=installed.environment,
-        stdout=subprocess.PIPE,
-        stderr=subprocess.PIPE,
+        capture_output=True,
         text=True,
-    ) as process:
-        try:
-            stdout, stderr = process.communicate(timeout=20)
-        finally:
-            if process.poll() is None:
-                process.kill()
-            process.communicate()
-        assert process.poll() is not None
-    value: dict[str, Any] = json.loads(stdout)
-    assert process.returncode == value["exit"], (stdout, stderr)
+        timeout=20,
+        check=False,
+    )
+    value: dict[str, Any] = json.loads(process.stdout)
+    assert process.returncode == value["exit"], (process.stdout, process.stderr)
     assert_installed(value["origins"], installed, "ovcaq.workflow.records")
     return value
 
@@ -350,51 +344,27 @@ def _assert_runtime_reparented_after_chain_confirmation(
     return index
 
 
-@pytest.mark.parametrize("replay", (False, True), ids=("direct", "exact-replay"))
-@pytest.mark.parametrize(
-    "distance", (1, 3, 5), ids=("distance-1", "distance-3", "distance-5")
-)
-def test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry(
-    installed_wheel: InstalledWheel, tmp_path: Path, replay: bool, distance: int
+def _assert_reparented_result_is_safe(
+    result: dict[str, Any],
+    runtime: Path,
+    ancestor: Path,
+    confirmation_index: int,
+    replay: bool,
+    seeded: bytes | None,
 ) -> None:
-    project = _prepare(installed_wheel, tmp_path)
-    authoritative = _state_bytes(project)
-    runtime = project / uuid4().hex / "one/two/three/four/runtime"
-    runtime.mkdir(parents=True)
-    ancestor = runtime.parents[distance - 1]
-    previous_ancestor, previous_runtime = identity(ancestor), identity(runtime)
-    seeded = None
-    if replay:
-        seed = _invoke(
-            installed_wheel, project, "normal", runtime=runtime, ancestor=ancestor
-        )
-        assert seed["exit"] == 0, seed
-        seeded = _assert_one_record(runtime)
-        assert _state_bytes(project) == authoritative
-
-    result = _invoke(
-        installed_wheel,
-        project,
-        "reparent-during-publication",
-        runtime=runtime,
-        ancestor=ancestor,
-    )
-    index = _assert_runtime_reparented_after_chain_confirmation(
-        result, project, runtime, ancestor, previous_ancestor, previous_runtime
-    )
     events = result["events"]
     if result["exit"] == 0:
         assert result["path"] == str(_ledger(runtime))
         returned = {"kind": "returned", "path": str(_ledger(runtime))}
         assert events.count(returned) == 1, result
         return_index = events.index(returned)
-        assert index < return_index, result
+        assert confirmation_index < return_index, result
         for parent in (ancestor.parent, ancestor):
             assert {
                 "kind": "fsync",
                 "path": str(parent),
                 "identity": identity(parent),
-            } in events[index + 1 : return_index], result
+            } in events[confirmation_index + 1 : return_index], result
         _assert_one_record(runtime)
     else:
         assert result["exit"] == 2, result
@@ -403,17 +373,25 @@ def test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry(
         assert str(ancestor) in result["error"].split("identity changed; retry", 1)[1]
         assert "path" not in result
         assert not any(event["kind"] == "returned" for event in events), result
-        if _ledger(runtime).exists():
-            _assert_one_record(runtime)
+        if replay:
+            assert _ledger(runtime).read_bytes() == seeded
+        else:
+            assert not _ledger(runtime).exists()
     if replay:
         assert _ledger(runtime).read_bytes() == seeded
-    assert _state_bytes(project) == authoritative
-    displaced_runtime = project / "displaced" / runtime.relative_to(ancestor)
-    assert not displaced_runtime.exists()
 
-    retry = _invoke(
-        installed_wheel, project, "normal", runtime=runtime, ancestor=ancestor
-    )
+
+def _assert_reparented_retry_and_replay(
+    installed: InstalledWheel,
+    project: Path,
+    runtime: Path,
+    ancestor: Path,
+    authoritative: tuple[bytes, bytes],
+    previous_runtime: list[int],
+    replay: bool,
+    seeded: bytes | None,
+) -> None:
+    retry = _invoke(installed, project, "normal", runtime=runtime, ancestor=ancestor)
     assert retry["exit"] == 0, retry
     assert retry["path"] == str(_ledger(runtime))
     committed = _assert_one_record(runtime)
@@ -426,13 +404,62 @@ def test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry(
             "identity": identity(parent),
         } in retry["events"], retry
     exact_replay = _invoke(
-        installed_wheel, project, "normal", runtime=runtime, ancestor=ancestor
+        installed, project, "normal", runtime=runtime, ancestor=ancestor
     )
     assert exact_replay["exit"] == 0, exact_replay
     assert _assert_one_record(runtime) == committed
     if replay:
         assert committed == seeded
     assert _state_bytes(project) == authoritative
+
+
+@pytest.mark.parametrize("replay", (False, True), ids=("direct", "exact-replay"))
+@pytest.mark.parametrize(
+    "distance", (1, 3, 5), ids=("distance-1", "distance-3", "distance-5")
+)
+def test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry(
+    installed_wheel: InstalledWheel, tmp_path: Path, replay: bool, distance: int
+) -> None:
+    project = _prepare(installed_wheel, tmp_path)
+    authoritative = _state_bytes(project)
+    runtime = project / uuid4().hex / "one/two/three/four/runtime"
+    runtime.mkdir(parents=True)
+    ancestor = runtime.parents[distance - 1]
+    previous_ancestor, previous_runtime = identity(ancestor), identity(runtime)
+    seeded = None
+    if replay:
+        seed = _invoke(
+            installed_wheel, project, "normal", runtime=runtime, ancestor=ancestor
+        )
+        assert seed["exit"] == 0, seed
+        seeded = _assert_one_record(runtime)
+        assert _state_bytes(project) == authoritative
+
+    result = _invoke(
+        installed_wheel,
+        project,
+        "reparent-during-publication",
+        runtime=runtime,
+        ancestor=ancestor,
+    )
+    index = _assert_runtime_reparented_after_chain_confirmation(
+        result, project, runtime, ancestor, previous_ancestor, previous_runtime
+    )
+    _assert_reparented_result_is_safe(result, runtime, ancestor, index, replay, seeded)
+    assert _state_bytes(project) == authoritative
+    displaced_runtime = project / "displaced" / runtime.relative_to(ancestor)
+    assert not displaced_runtime.exists()
+
+    _assert_reparented_retry_and_replay(
+        installed_wheel,
+        project,
+        runtime,
+        ancestor,
+        authoritative,
+        previous_runtime,
+        replay,
+        seeded,
+    )
     assert not displaced_runtime.exists()
 
 
diff --git a/tests/workflow/test_deferred_diagnostics.py b/tests/workflow/test_deferred_diagnostics.py
new file mode 100644
index 0000000..db29f9f
--- /dev/null
+++ b/tests/workflow/test_deferred_diagnostics.py
@@ -0,0 +1,140 @@
+from __future__ import annotations
+
+import errno
+import os
+from pathlib import Path
+
+import pytest
+
+from ovcaq.workflow.records import record_defer
+
+PRD = "00004-workflow-core-v1.md"
+BATCH_ID = "batch-16"
+RECORD = {"op_id": "diagnostic-16", "detail": "test"}
+
+
+def _is_deferred_path(
+    path: str | os.PathLike[str], dir_fd: int | None, runtime_root: Path
+) -> bool:
+    candidate = Path(path)
+    if candidate.is_absolute():
+        return candidate == runtime_root / "deferred"
+    if dir_fd is None or candidate != Path("deferred"):
+        return False
+    directory = os.fstat(dir_fd)
+    root = runtime_root.stat()
+    return (directory.st_dev, directory.st_ino) == (root.st_dev, root.st_ino)
+
+
+def test_record_defer_refuses_regular_file_at_deferred_path(tmp_path: Path) -> None:
+    runtime_root = tmp_path.resolve()
+    deferred = runtime_root / "deferred"
+    published = deferred / f"{BATCH_ID}-deferred.json"
+    deferred.write_bytes(b"obstruction")
+    inode = deferred.stat().st_ino
+
+    with pytest.raises(OSError) as raised:
+        record_defer(runtime_root, PRD, BATCH_ID, RECORD)
+
+    assert (
+        str(raised.value) == f"deferred directory is not a real directory: {deferred}"
+    )
+    assert isinstance(raised.value.__cause__, OSError)
+    assert raised.value.__cause__.errno == errno.ENOTDIR
+    assert deferred.stat().st_ino == inode
+    assert deferred.read_bytes() == b"obstruction"
+    assert not published.exists()
+
+
+def test_record_defer_refuses_symlink_at_deferred_path(tmp_path: Path) -> None:
+    runtime_root = tmp_path.resolve()
+    deferred = runtime_root / "deferred"
+    target = runtime_root / "target"
+    target.mkdir()
+    sentinel = target / "sentinel"
+    sentinel.write_bytes(b"untouched")
+    sentinel_inode = sentinel.stat().st_ino
+    deferred.symlink_to(target, target_is_directory=True)
+    link_inode = deferred.lstat().st_ino
+
+    with pytest.raises(OSError) as raised:
+        record_defer(runtime_root, PRD, BATCH_ID, RECORD)
+
+    assert (
+        str(raised.value) == f"deferred directory is not a real directory: {deferred}"
+    )
+    assert isinstance(raised.value.__cause__, OSError)
+    assert raised.value.__cause__.errno in {errno.ELOOP, errno.ENOTDIR}
+    assert deferred.is_symlink()
+    assert deferred.lstat().st_ino == link_inode
+    assert sentinel.stat().st_ino == sentinel_inode
+    assert sentinel.read_bytes() == b"untouched"
+    assert sorted(item.name for item in target.iterdir()) == ["sentinel"]
+
+
+def test_record_defer_reports_directory_vanishing_before_second_open(
+    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
+) -> None:
+    runtime_root = tmp_path.resolve()
+    deferred = runtime_root / "deferred"
+    published = deferred / f"{BATCH_ID}-deferred.json"
+    actual_open = os.open
+    deferred_opens = 0
+
+    def vanish_on_second_open(
+        path: str | os.PathLike[str],
+        flags: int,
+        mode: int = 0o777,
+        *,
+        dir_fd: int | None = None,
+    ) -> int:
+        nonlocal deferred_opens
+        if _is_deferred_path(path, dir_fd, runtime_root):
+            deferred_opens += 1
+            if deferred_opens == 2:
+                deferred.rmdir()
+        return actual_open(path, flags, mode, dir_fd=dir_fd)
+
+    monkeypatch.setattr(os, "open", vanish_on_second_open)
+    with pytest.raises(OSError) as raised:
+        record_defer(runtime_root, PRD, BATCH_ID, RECORD)
+
+    assert deferred_opens == 2
+    assert (
+        str(raised.value) == f"deferred directory is not a real directory: {deferred}"
+    )
+    assert isinstance(raised.value.__cause__, OSError)
+    assert raised.value.__cause__.errno == errno.ENOENT
+    assert not deferred.exists()
+    assert not published.exists()
+
+
+@pytest.mark.parametrize("error_number", (errno.EACCES, errno.ENOSPC, errno.EBADF))
+def test_record_defer_reports_directory_creation_error(
+    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error_number: int
+) -> None:
+    runtime_root = tmp_path.resolve()
+    deferred = runtime_root / "deferred"
+    published = deferred / f"{BATCH_ID}-deferred.json"
+    actual_mkdir = os.mkdir
+    failure = OSError(error_number, os.strerror(error_number), deferred)
+
+    def fail_deferred_mkdir(
+        path: str | os.PathLike[str],
+        mode: int = 0o777,
+        *,
+        dir_fd: int | None = None,
+    ) -> None:
+        if _is_deferred_path(path, dir_fd, runtime_root):
+            raise failure
+        actual_mkdir(path, mode, dir_fd=dir_fd)
+
+    monkeypatch.setattr(os, "mkdir", fail_deferred_mkdir)
+    with pytest.raises(OSError) as raised:
+        record_defer(runtime_root, PRD, BATCH_ID, RECORD)
+
+    assert str(raised.value) == f"deferred directory could not be created: {deferred}"
+    assert raised.value.__cause__ is failure
+    assert raised.value.__cause__.errno == error_number
+    assert not deferred.exists()
+    assert not published.exists()

```

## Recorded verification

The task's tests were run before this review. This is what they reported:

Task base 4011d1a3ce186ae9dcd023e8a7fb4b87412b935d; initial tests 80d549f8f677c48e9848eab166aef9ccc88e11d5; current HEAD 2742c08fe5f8194f65a36fa1e49a5980d69c16ef.
Before implementation: mise exec -- uv run pytest tests/workflow/test_deferred_diagnostics.py -> exit1; 3 failed (creation-error diagnostic mismatches), 3 passed, no collection errors.
After implementation and correcting the coordinator-supplied public ledger filename: mise exec -- uv run pytest tests/workflow/test_deferred_diagnostics.py -> exit0.
============================= test session starts ==============================
platform darwin -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/bob/git/src/github.com/buvis/ovcaq
configfile: pyproject.toml
collected 6 items

tests/workflow/test_deferred_diagnostics.py ......                       [100%]

=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-465c2396-f024-4822-83c9-7e3a424473d2
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-465c2396-f024-4822-83c9-7e3a424473d2'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ede528bd-5064-4a72-9454-40741b6f503a
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ede528bd-5064-4a72-9454-40741b6f503a'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 6 passed, 2 warnings in 0.02s =========================

Style-limit and split-hygiene checks passed at this HEAD. Fresh self-deslop found no permissible removals. The full workspace suite is mandated after task closure and has not run on this tail yet; prior 1372/0/0 counts were at reviewed HEAD4011d1a.
The earlier Pat dispatch stopped at quota before producing any review. This prompt will contain the complete current diff for the single authorized retry after reset; no previous review verdict is assumed.

Measured AST spans (end_lineno - lineno + 1): _verify_directory_chain 13, _ensure_directory_chain 40, _open_deferred_ledger 47, _invoke 34, _assert_reparented_result_is_safe 35, _assert_reparented_retry_and_replay 30, test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry 44 lines. All are below the 50-line limit.


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


