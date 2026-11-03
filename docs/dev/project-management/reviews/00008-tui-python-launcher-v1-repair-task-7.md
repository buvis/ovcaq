# PRD 00008 recovery task 7

Launcher completion now requires the newly launched child's exact terminal evidence and committed completed state. Verified fast completion returns LaunchedSupervisor(None), avoiding nonexistent live attachment. The CLI recognizes typed missing-selection cleanup races and rechecks that same evidence; other viewer errors remain errors. Parent-created private report descriptors preserve early child configuration/layout failures, bounded sanitized text uses the existing redactor, and both report environment keys are consumed before driver construction. Configured runtime roots are prepared through ensure_runtime_layout. Both exited-child and still-starting duplicate-owner failures guide attach without telling the operator to stop the healthy owner.

Base:92e15b3a097cce6e7e044dd5c57678ff29531e4c. Initial tests:23716ae46de973cf6ba3ea9b1eb7b1f783bea991. Devon-strengthened tests:00cb682a0b1cc83db95a79a9e184237ea4cc7fd7. Final tests:cecb65294f072c16d5ed4b05a811825a38c17d57. Implementation:f22b99d27cdca8b796db30c6d3a36745a6c282a3. Style:53c75fec64120a16facc59d419fff340e5cfd6ad. Final:ec7857d9c1e1f2a52d08167421d779c3982abaa5.

## Scope and dispatch

Backend opus row2 mapped to native OpenAI gpt-6-astra. Qwen planner exclusion tier; task preflight null; no Gemini probe or external Codex-rung dispatch. The coordinator recorded the nullable LaunchedSupervisor.run contract through the state CLI and autonomous decision record. During implementation, plain ValueError could not distinguish missing selection from arbitrary viewer failures. The state-backed writable contract gained only discovery.py's MissingRunError(ValueError), preserving ambiguous selection. Added source1419 bytes; conservative task estimate71000 remains under75000. No new module, provider parser, state writer, liveness policy or dependency. paths.py needed no edit.

Tess c5280f33(31,248 bytes) produced24 cases,14pass10red. Quality retry89d15902(12,057) fixed a computed OR hedge and added reflected hostile input;25cases14pass11red. The first values used in a config type-error test were not guaranteed to reach the diagnostic. The added real unknown-agent failure exposed actual synthetic credential leakage. Initial Tess used cat before reading its embedded restriction; subsequent reads were bounded. Sandbox cache/process failures and approved retries are retained; all children were awaited.

Devon d12c9ddb(43,201) initially returned an automated possible-cybersecurity-risk content-filter error without useful output or edits. The debug procedure preserved it, checked the tree and used one unchanged-prompt infrastructure retry clarifying authorized local mutation testing and synthetic data. No safeguard/model/permission setting was bypassed. The retry proved five independent wrong variants each passed all25 cases; two earlier baseline candidates failed2 and1 cases. All three source backups and canonical tests were independently verified restored byte-for-byte. Full raw evidence follows; no second Devon pass ran.

Tess c3fa46df(46,616) strengthened every numbered gap: committed state binding using a real opaque child report, explicit agent, custom argv prefix, delayed publication/deadline, and successful report cleanup. No in-contract dismissals. Main red:11failed18passed. Initial Ivan a07e2fae(36,449) passed29 cases but globally changed ordinary CLI error emission. Coordinator correction e0584b57(39,575) restored that contract and scoped sanitized bounded CommandError creation to the supervisor, preserving code/path. Canonical tests remained unchanged. Independent committed run passed29 cases.

Fresh cleanup c61b5a59(18,711) returned no slop. Style gate found _run54lines. One style pass4f03d702(13,278) extracted inherited-report validation while preserving descriptor cleanup; final _run47lines and mechanical gates pass. Initial reflow flag src/ovcaq/supervisor_cli.py:26 is retained: these are the targeted launcher/report changes, not a silent clean verdict. Split hygiene clean. Formatter conformity remains assigned to mandatory phase-end verification.

## Review and final correction

Pat's first prepared prompt26251e7a measured55138bytes and was NOT dispatched. One permitted trim removed duplicate/historical description context, preserving complete diff/persona/findings/verification and all current semantic obligations. Dispatch160b8d5f used49788bytes through the tool-free installed Claude wrapper with approved network. Session32b77091-7038-4183-b95d-d58ebc9f68b9, actual claude-sonnet-5-5 confirmed from model metadata. Parser accepted four resolved closures and five LOW notes before dispositions.

Coordinator rejected Pat's qualified F35 closure: its evidence awaited duplicate-child exit, leaving the parent-side still-starting branch's stop guidance reachable. Tess ca6be7c8(12070bytes), fourth/final dispatch and second quality retry, added a finite startup pipe barrier. All29 prior cases passed and the new ordering failed exactly on ovcaq stop. Main independently recorded1failed29passed. All15 test functions pass computed tautology checks and manual four-check review; test style clean. Ivan9806f249(40803bytes) changed only the ambiguous/unrelated-ownership guidance branch and passed30cases. No signal, state, owner-proof, retry, timeout or other behavior changed.

Final independent command: uv run pytest -q --tb=line tests/integration/test_launcher_outcomes.py. Exit0:30passed,2pytest temporary-directory cleanup warnings,in2.57s. Exact command and output: docs/dev/tmp/r7-owner-green.log and JSON sidecar. Style and split hygiene were rechecked after the final commit and pass. The full suite is still deferred to the mandatory phase-end gate.

Delta Pat ab42d70d(8172bytes) resumed the same tool-free session with the nonempty53c75fe..ec7857d delta and recorded verification. Parser accepted F35 resolved for both orderings, plus two LOW notes. All four original findings are now closed; no HIGH/MEDIUM remains. This task review does not replace fresh completion review.

## LOW dispositions and coverage limits

- Retain private Supervisor._metadata access for the existing immutable final identity; public API cleanup remains LOW, outside this narrow correction.
- Reject moving completion evaluation inside observe_selected_run: its exit revalidates and may set state=None, so evaluating before exit would weaken the invariant. Source lines127–145 were checked.
- Refute initial _run length claim with the passing computed gate after the committed style fix.
- Retain repeated/source-scoped sanitization: persisted and read evidence are separately bounded; ordinary non-CommandError state/I/O/value exception classifications remain unchanged. Generic CLI error emission is deliberately preserved.
- Retain the branch-local failure construction LOW; it avoids adding optional guidance machinery solely for one distinct ownership failure. The candidates originate in registry.snapshot().live, but attach can still reject inconsistent ownership. Guidance never signals or promises an attachment succeeds.
- Formatting LOWs remain for the required final ruff format gate. Ensure any formatter fix also preserves the function limit.
- Environment consumption is tested via real driver-construction failure, not direct instruction-order instrumentation. Deadline coverage uses0.15s with a2s wall-clock tolerance. All process fixtures have finite cleanup.

## Assumptions

- Diagnostic newline separators are allowed; other Unicode Cc controls are rejected.
- The parent-created explicitly inherited private descriptor is the capability for diagnostics before child configuration resolves. Environment-only path destinations still require resolved-runtime containment.
- MissingRunError is the coordinator-authorized narrow contract amendment, not a user-selected design choice; nullable quick-completion outcome was recorded likewise.

## Raw initial Pat review

CLOSURE | resolved | F11 `supervisor_settings()` runs before the child claims its launch report and before the guarded block | `_run` now calls `supervisor_settings(root)`, `_claim_launch_report` and `ensure_runtime_layout` inside the `try`, and an inherited fd is verified first, so early failures reach `_write_launch_report`. `test_child_configuration_failure_preserves_actionable_private_report` and `test_early_layout_failure_preserves_diagnostic_and_collision` pass.

CLOSURE | resolved | F20 Interactive `run`/`resume` on a batch that finishes right away reports a crash (exit 0 writes no report; attach races cleanup) | On exit 0 the child writes its session metadata as JSON to the report. `launch_supervisor` then calls `_completed_launch`, which requires pid equality and `completed_run` (selected-run evidence with ended and status "completed"), and returns `LaunchedSupervisor(None)`. `_launch_and_attach` returns 0 on `run is None`. It also catches `MissingRunError` and returns 0 only if `completed_run` holds. The quick-completion and cleanup-race tests pass for the five outcomes.

CLOSURE | resolved | F35 Duplicate-owner failure says "end it with `ovcaq stop`", which would kill the healthy owner | The child converts `DuplicateRunError` to a `CommandError` ending in "use `ovcaq attach`" and writes it to the report. `test_duplicate_owner_guides_attach_without_signaling_healthy_owner` asserts "ovcaq attach" is present and "ovcaq stop" is absent. The original "stop" text site (old line 252) is outside the diff, so the resolution rests on that test covering the reachable path.

CLOSURE | resolved | F36 `launch_supervisor` creates the derived runtime tree but writes its report under the configured `runtime_root` | `launch_supervisor` now builds `paths = ensure_runtime_layout(supervisor_settings(root).runtime.paths)` and puts the report in `paths.runtime_root`. `test_configured_layout_drains_without_creating_unused_default_tree` covers contained and external layouts and asserts the default tree is never created.

LOW | src/ovcaq/supervisor_cli.py:_run (`elif supervisor._metadata is not None`) | The launcher reads the private `_metadata` attribute of `Supervisor` across a module boundary | Expose a public `metadata` property on `Supervisor`, or return the metadata from `run()`.

LOW | src/ovcaq/supervisor_cli.py:_run | The function now exceeds 50 lines and mixes report claiming, layout, supervisor construction and error mapping | Extract the report setup (inherited fd vs path) into a helper that returns `report` and `descriptor`.

LOW | src/ovcaq/supervisor_cli.py:completed_run | `with observe_selected_run(...) as selected: pass` followed by reading `selected` after the context exits; this relies on the object staying valid after exit | Evaluate the `ended`/`state` check inside the `with` block and return from there.

LOW | src/ovcaq/supervisor_cli.py:_run, launch_supervisor | Several lines look non-conforming to `ruff format` and the project's `ruff format --check`: `clock=_Clock(), sleeper=time.sleep,`, `report, child.pid, None,`, the multi-kwarg `env={...}` and the `os.dup(report) if isinstance(...) \ else ...` expression; some lines also exceed 88 columns. The recorded run did not include ruff | Run `ruff format` on `supervisor_cli.py`; if the line length is already configured, only the multi-value lines need splitting.

LOW | src/ovcaq/supervisor_cli.py:_bounded, _read_launch_report | `_bounded` is applied on write and again on read, and `_run` applies it to `CommandError` text only; the `StateError`/`OSError`/`ValueError` branch re-raises unbounded text to stderr | Either bound once at the report write and the CLI emission boundary, or document that raw errors in that branch are intentionally unbounded.


## Raw delta Pat review

CLOSURE | resolved | HIGH F35 (src/ovcaq/supervisor_cli.py:_published_run and _launch_failure): the unrelated-ownership branch still emitted `ovcaq stop` guidance while the new child was starting | The delta replaces `_launch_failure(..., "has ambiguous or unrelated ownership")` with a `LaunchError` whose detail reads "inspect the existing owner with `ovcaq attach`". It has no stop text, `exit_code` is None, and the report path is kept. The `duplicate_startup` fixture now runs the duplicate-owner test in both the "exited" and "starting" orderings. The "starting" case asserts the child is alive at the barrier. The test still asserts no "ovcaq stop", no signal to the owner, and that the owner's identity and state are unchanged. All 30 tests pass.

LOW | src/ovcaq/supervisor_cli.py:_published_run (new `raise LaunchError(LaunchFailureEvidence(...))`) | The branch builds its own `LaunchFailureEvidence` instead of going through `_launch_failure`. Any formatting or report-content handling in `_launch_failure` (I can't see its body in this delta) now diverges between the two paths. The guidance also fires for every ambiguous or unrelated ownership case, including ones with no healthy owner to attach to | Let `_launch_failure` take an optional guidance suffix so there is one construction site. Keep the attach hint only where a live owner is confirmed.

LOW | src/ovcaq/supervisor_cli.py:_published_run | The `raise LaunchError(LaunchFailureEvidence(` layout does not match `ruff format` style | Run `ruff format` in the phase-end gate, which is already scheduled.


## Raw Devon evidence

# Task 7 Devon mutation validation

Verdict: five verified coverage gaps. All 25 task7 tests passed for candidates 3–7. No tests were modified; all three source files restored byte-for-byte from supplied backups. No git or state writes. Every test command and child-owning runner was awaited.

The initial sandbox run could not open the existing uv cache (exit 2); the same bounded test command then ran with approved local filesystem/process access. This was infrastructure only, not a test result.

Candidate 1: 23 passed, 2 failed (configuration report lacked context; duplicate-owner report lacked attach guidance). Candidate 2: 24 passed, 1 failed (stderr newline exceeded the 4096-byte bound). Candidate 3 corrected these baseline issues and retained the intentionally wrong completion protocol. Candidates 4–7 each start from candidate 3, not from the previous mutation.

Weak points:
1. test_exit_without_exact_child_commit_proof_is_failure — a report containing only matching PID and done=true is accepted without checking any committed state/revision/batch evidence — add a replacement child that writes this report and exits zero without completing the batch; require LaunchError and unchanged state. Candidate 3: 25 passed.
2. test_live_handshake_returns_exact_published_child_identity — launch_supervisor can discard its explicit agent argument because every launch supplies None — launch with a configured alternate agent and assert the spawned argv/observed selected agent. Candidate 4: 25 passed.
3. test_real_empty_child_commits_completion_before_parent_first_poll — launch_supervisor can ignore argv_prefix and hardcode the module command — pass a finite custom launcher that records invocation and assert it ran. Candidate 5: 25 passed.
4. test_live_handshake_returns_exact_published_child_identity — timeout_seconds can be forced to zero, rejecting every not-yet-published child immediately; the fixture waits for publication before returning Popen — return before publication, release a finite barrier within the configured deadline, and require successful attachment; also exercise a bounded timeout. Candidate 6: 25 passed.
5. test_real_empty_child_commits_completion_before_parent_first_poll / test_live_handshake_returns_exact_published_child_identity — successful launches may retain their reports forever — assert report paths are absent after both successful outcomes, while preserving failure reports. Candidate 7: 25 passed.

Scope caveat: the supplied public signatures/tests are the only contract available to this validator. Agent/argv/deadline/report-cleanup findings concern the public launcher API and existing helper behavior; coordinator should decide whether each belongs in task7 regression coverage.

## Restoration hashes
- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py: SHA256 c1fedace1f66238dee0f6936bf2d27422ef047477c7b681e2f8a33955fda3a68 (equals backup)
- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/cli.py: SHA256 b204c396c6057cfc412777282d287f795760cc2acf95630fcc0e5aca3f4a4536 (equals backup)
- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/paths.py: SHA256 3bb2bdd7da9dc838e19751fb95c79aa072961849624978f9ab91bfb3a5cfb990 (equals backup)
- Canonical test file current SHA256: a2903f8938499f98258a85925af92dcce57036cea116d81c73f625e96d296e4b; never written by this validator. Coordinator owns comparison against commit 23716ae46de973cf6ba3ea9b1eb7b1f783bea991.

## Candidate 1

Exact argv:
```
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /tmp/devon-r7-test-1-access.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py
```

Actual output:
```
.........F..............F                                                [100%]
=================================== FAILURES ===================================
E   assert False
     +  where False = any(<generator object assert_private_diagnostic.<locals>.<genexpr> at 0x10b942ea0>)
/Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py:247: assert False
E   AssertionError: assert 'ovcaq attach' in 'supervisor pid 62070 exited with code 1: supervisor failed: Run lock is already held: /private/var/folders/m6/1mnc9pd...0000gn/T/pytest-of-bob/pytest-12324/test_duplicate_owner_guides_at0/project/docs/dev/project-management/ovcaq/run.lock'
/Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py:516: AssertionError: assert 'ovcaq attach' in 'supervisor pid 62070 exited with code 1: supervisor failed: Run lock is already held: /private/var/folders/m6/1mnc9pd...0000gn/T/pytest-of-bob/pytest-12324/test_duplicate_owner_guides_at0/project/docs/dev/project-management/ovcaq/run.lock'
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-853466f2-fc0a-4220-bbc6-9cd18647708a
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-853466f2-fc0a-4220-bbc6-9cd18647708a'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-3535afda-a247-4cef-9c8e-adfd1d961009
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-3535afda-a247-4cef-9c8e-adfd1d961009'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/integration/test_launcher_outcomes.py::test_child_configuration_failure_preserves_actionable_private_report
FAILED tests/integration/test_launcher_outcomes.py::test_duplicate_owner_guides_attach_without_signaling_healthy_owner
2 failed, 23 passed, 2 warnings in 2.04s

```

Diff (1–3 against supplied backups; 4–7 isolated mutation against candidate 3):
```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
@@ -4,6 +4,8 @@
 
 import argparse
 import json
+import re
+import unicodedata
 import os
 import signal
 import stat
@@ -66,6 +68,8 @@
 
 
 def _bounded(text: str) -> str:
+    text = re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", text)
+    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cc" or ch == "\n")
     return text.encode("utf-8")[:MAX_REPORT_BYTES].decode("utf-8", "ignore")
 
 
@@ -113,7 +117,7 @@
         out.write(_bounded(detail).encode("utf-8"))
 
 
-def _run(args: argparse.Namespace, root: Path) -> SupervisorResult:
+def _run_inner(args: argparse.Namespace, root: Path) -> SupervisorResult:
     settings = supervisor_settings(root)
     report = _claim_launch_report(settings.runtime.paths.runtime_root)
     try:
@@ -145,6 +149,29 @@
     return value, None, False, outcome.exit_code
 
 
+def _run(args: argparse.Namespace, root: Path) -> SupervisorResult:
+    value = os.environ.pop(LAUNCH_REPORT_ENV, None)
+    report = None
+    try:
+        try:
+            runtime_root = supervisor_settings(root).runtime.paths.runtime_root
+        except Exception:
+            runtime_root = root / "docs/dev/project-management/ovcaq"
+        if value is not None:
+            os.environ[LAUNCH_REPORT_ENV] = value
+            report = _claim_launch_report(runtime_root)
+        result = _run_inner(args, root)
+        if result[3] == 0:
+            _write_launch_report(report, json.dumps({"pid": os.getpid(), "done": True}))
+        return result
+    except Exception as error:
+        detail = _bounded(str(error) or type(error).__name__)
+        _write_launch_report(report, detail)
+        raise CommandError(ErrorCode.RUNTIME_FORMAT, detail) from error
+    finally:
+        os.environ.pop(LAUNCH_REPORT_ENV, None)
+
+
 def operator_notice(reason: str | None) -> Notice | None:
     if reason is None:
         return None
@@ -182,7 +209,7 @@
 
 @dataclass(frozen=True, slots=True)
 class LaunchedSupervisor:
-    run: FleetRun
+    run: FleetRun | None
 
 
 @dataclass(frozen=True, slots=True)
@@ -249,7 +276,7 @@
         or identity is None
         or identity.started != entry.process_start
     ):
-        raise _launch_failure(report, pid, None, "has ambiguous or unrelated ownership")
+        raise LaunchError(LaunchFailureEvidence(None, "existing owner: use ovcaq attach", report))
     status = observe_run(paths).status
     if status == "inconsistent":
         raise _launch_failure(report, pid, None, "has an inconsistent run observation")
@@ -267,8 +294,8 @@
     timeout_seconds: float = 10.0,
 ) -> LaunchedSupervisor:
     """Spawn a detached foreground supervisor and wait for its exact publication."""
-    ensure_runtime_directory(root)
     paths = supervisor_settings(root).runtime.paths
+    paths.runtime_root.mkdir(parents=True, exist_ok=True)
     report = paths.runtime_root / f"launch-{uuid4().hex}.report"
     os.close(
         os.open(report, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
@@ -291,6 +318,13 @@
     while True:
         exit_code = child.poll()
         if exit_code is not None:
+            try:
+                proof = json.loads(_read_launch_report(report))
+            except ValueError:
+                proof = {}
+            if exit_code == 0 and proof == {"pid": child.pid, "done": True}:
+                report.unlink()
+                return LaunchedSupervisor(None)
             raise _launch_failure(report, child.pid, exit_code, "exited")
         launched = _published_run(registry, paths, root, child.pid, report)
         if launched is not None:
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/cli.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/cli.py
@@ -486,7 +486,19 @@
         raise CommandError(
             ErrorCode.RUNTIME_FORMAT, str(error), path=str(error.evidence.path)
         ) from error
-    return _attach_view(root, run.root, run.run_id)
+    if run is None:
+        return 0
+    paths = supervisor_settings(root).runtime.paths
+    batch_id = StateStore(paths.state_file).read()["batch"]["id"]
+    try:
+        return _attach_view(root, run.root, run.run_id)
+    except (ValueError, RuntimeError) as error:
+        from ovcaq.runtime._run_observation import observe_selected_run
+        if "no match" in str(error).lower():
+            with observe_selected_run(paths, run, batch_id=batch_id) as selected:
+                if selected.ended and selected.state is not None and selected.state["batch"]["status"] == "completed":
+                    return 0
+        raise ValueError(str(error)) from error
 
 
 def _resume_and_attach(root: Path) -> int:

```

## Candidate 2

Exact argv:
```
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /tmp/devon-r7-test-2.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py
```

Actual output:
```
.................F.......                                                [100%]
=================================== FAILURES ===================================
E   AssertionError: assert 4097 <= 4096
     +  where 4097 = len(b'runtime configuration: unknown agent: hostile-agent-[31m[redacted]\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\x...\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\n')
     +    where b'runtime configuration: unknown agent: hostile-agent-[31m[redacted]\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\x...\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\n' = <built-in method encode of str object at 0x8b20a6800>('utf-8')
     +      where <built-in method encode of str object at 0x8b20a6800> = 'runtime configuration: unknown agent: hostile-agent-[31m[redacted]ééééééééééééééééééééééééééééééééééééééééééééééééééé...éééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééééé\n'.encode
/Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py:369: AssertionError: assert 4097 <= 4096
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-f05c0b59-c0c0-422d-9691-b086ebf921e3
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-f05c0b59-c0c0-422d-9691-b086ebf921e3'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-678ce654-0e96-40f4-bf46-d96cedc8b9d9
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-678ce654-0e96-40f4-bf46-d96cedc8b9d9'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/integration/test_launcher_outcomes.py::test_reflected_hostile_agent_preserves_bounded_private_diagnostics
1 failed, 24 passed, 2 warnings in 2.01s

```

Diff (1–3 against supplied backups; 4–7 isolated mutation against candidate 3):
```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
@@ -4,6 +4,8 @@
 
 import argparse
 import json
+import re
+import unicodedata
 import os
 import signal
 import stat
@@ -66,6 +68,8 @@
 
 
 def _bounded(text: str) -> str:
+    text = re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", text)
+    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cc" or ch == "\n")
     return text.encode("utf-8")[:MAX_REPORT_BYTES].decode("utf-8", "ignore")
 
 
@@ -113,7 +117,7 @@
         out.write(_bounded(detail).encode("utf-8"))
 
 
-def _run(args: argparse.Namespace, root: Path) -> SupervisorResult:
+def _run_inner(args: argparse.Namespace, root: Path) -> SupervisorResult:
     settings = supervisor_settings(root)
     report = _claim_launch_report(settings.runtime.paths.runtime_root)
     try:
@@ -145,6 +149,31 @@
     return value, None, False, outcome.exit_code
 
 
+def _run(args: argparse.Namespace, root: Path) -> SupervisorResult:
+    value = os.environ.pop(LAUNCH_REPORT_ENV, None)
+    report = None
+    try:
+        try:
+            runtime_root = supervisor_settings(root).runtime.paths.runtime_root
+        except Exception:
+            runtime_root = root / "docs/dev/project-management/ovcaq"
+        if value is not None:
+            os.environ[LAUNCH_REPORT_ENV] = value
+            report = _claim_launch_report(runtime_root)
+        result = _run_inner(args, root)
+        if result[3] == 0:
+            _write_launch_report(report, json.dumps({"pid": os.getpid(), "done": True}))
+        return result
+    except Exception as error:
+        detail = _bounded("runtime configuration: " + (str(error) or type(error).__name__))
+        if "lock is already held" in detail.lower():
+            detail += "; use ovcaq attach"
+        _write_launch_report(report, detail)
+        raise CommandError(ErrorCode.RUNTIME_FORMAT, detail) from error
+    finally:
+        os.environ.pop(LAUNCH_REPORT_ENV, None)
+
+
 def operator_notice(reason: str | None) -> Notice | None:
     if reason is None:
         return None
@@ -182,7 +211,7 @@
 
 @dataclass(frozen=True, slots=True)
 class LaunchedSupervisor:
-    run: FleetRun
+    run: FleetRun | None
 
 
 @dataclass(frozen=True, slots=True)
@@ -249,7 +278,7 @@
         or identity is None
         or identity.started != entry.process_start
     ):
-        raise _launch_failure(report, pid, None, "has ambiguous or unrelated ownership")
+        raise LaunchError(LaunchFailureEvidence(None, "existing owner: use ovcaq attach", report))
     status = observe_run(paths).status
     if status == "inconsistent":
         raise _launch_failure(report, pid, None, "has an inconsistent run observation")
@@ -267,8 +296,8 @@
     timeout_seconds: float = 10.0,
 ) -> LaunchedSupervisor:
     """Spawn a detached foreground supervisor and wait for its exact publication."""
-    ensure_runtime_directory(root)
     paths = supervisor_settings(root).runtime.paths
+    paths.runtime_root.mkdir(parents=True, exist_ok=True)
     report = paths.runtime_root / f"launch-{uuid4().hex}.report"
     os.close(
         os.open(report, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
@@ -291,6 +320,13 @@
     while True:
         exit_code = child.poll()
         if exit_code is not None:
+            try:
+                proof = json.loads(_read_launch_report(report))
+            except ValueError:
+                proof = {}
+            if exit_code == 0 and proof == {"pid": child.pid, "done": True}:
+                report.unlink()
+                return LaunchedSupervisor(None)
             raise _launch_failure(report, child.pid, exit_code, "exited")
         launched = _published_run(registry, paths, root, child.pid, report)
         if launched is not None:
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/cli.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/cli.py
@@ -486,7 +486,19 @@
         raise CommandError(
             ErrorCode.RUNTIME_FORMAT, str(error), path=str(error.evidence.path)
         ) from error
-    return _attach_view(root, run.root, run.run_id)
+    if run is None:
+        return 0
+    paths = supervisor_settings(root).runtime.paths
+    batch_id = StateStore(paths.state_file).read()["batch"]["id"]
+    try:
+        return _attach_view(root, run.root, run.run_id)
+    except (ValueError, RuntimeError) as error:
+        from ovcaq.runtime._run_observation import observe_selected_run
+        if "no match" in str(error).lower():
+            with observe_selected_run(paths, run, batch_id=batch_id) as selected:
+                if selected.ended and selected.state is not None and selected.state["batch"]["status"] == "completed":
+                    return 0
+        raise ValueError(str(error)) from error
 
 
 def _resume_and_attach(root: Path) -> int:

```

## Candidate 3

Exact argv:
```
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /tmp/devon-r7-test-3.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py
```

Actual output:
```
.........................                                                [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-4b5a46e8-522b-4569-96c7-a0a22b6b3a28
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-4b5a46e8-522b-4569-96c7-a0a22b6b3a28'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-e0e54111-9fc7-451f-9dad-2dfd2f471781
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-e0e54111-9fc7-451f-9dad-2dfd2f471781'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 2 warnings in 2.92s

```

Diff (1–3 against supplied backups; 4–7 isolated mutation against candidate 3):
```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
@@ -4,6 +4,8 @@
 
 import argparse
 import json
+import re
+import unicodedata
 import os
 import signal
 import stat
@@ -66,7 +68,9 @@
 
 
 def _bounded(text: str) -> str:
-    return text.encode("utf-8")[:MAX_REPORT_BYTES].decode("utf-8", "ignore")
+    text = re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", text)
+    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cc" or ch == "\n")
+    return text.encode("utf-8")[:MAX_REPORT_BYTES - 1].decode("utf-8", "ignore")
 
 
 def _open_report(report: Path, flags: int) -> int:
@@ -113,7 +117,7 @@
         out.write(_bounded(detail).encode("utf-8"))
 
 
-def _run(args: argparse.Namespace, root: Path) -> SupervisorResult:
+def _run_inner(args: argparse.Namespace, root: Path) -> SupervisorResult:
     settings = supervisor_settings(root)
     report = _claim_launch_report(settings.runtime.paths.runtime_root)
     try:
@@ -145,6 +149,31 @@
     return value, None, False, outcome.exit_code
 
 
+def _run(args: argparse.Namespace, root: Path) -> SupervisorResult:
+    value = os.environ.pop(LAUNCH_REPORT_ENV, None)
+    report = None
+    try:
+        try:
+            runtime_root = supervisor_settings(root).runtime.paths.runtime_root
+        except Exception:
+            runtime_root = root / "docs/dev/project-management/ovcaq"
+        if value is not None:
+            os.environ[LAUNCH_REPORT_ENV] = value
+            report = _claim_launch_report(runtime_root)
+        result = _run_inner(args, root)
+        if result[3] == 0:
+            _write_launch_report(report, json.dumps({"pid": os.getpid(), "done": True}))
+        return result
+    except Exception as error:
+        detail = _bounded("runtime configuration: " + (str(error) or type(error).__name__))
+        if "lock is already held" in detail.lower():
+            detail += "; use ovcaq attach"
+        _write_launch_report(report, detail)
+        raise CommandError(ErrorCode.RUNTIME_FORMAT, detail) from error
+    finally:
+        os.environ.pop(LAUNCH_REPORT_ENV, None)
+
+
 def operator_notice(reason: str | None) -> Notice | None:
     if reason is None:
         return None
@@ -182,7 +211,7 @@
 
 @dataclass(frozen=True, slots=True)
 class LaunchedSupervisor:
-    run: FleetRun
+    run: FleetRun | None
 
 
 @dataclass(frozen=True, slots=True)
@@ -249,7 +278,7 @@
         or identity is None
         or identity.started != entry.process_start
     ):
-        raise _launch_failure(report, pid, None, "has ambiguous or unrelated ownership")
+        raise LaunchError(LaunchFailureEvidence(None, "existing owner: use ovcaq attach", report))
     status = observe_run(paths).status
     if status == "inconsistent":
         raise _launch_failure(report, pid, None, "has an inconsistent run observation")
@@ -267,8 +296,8 @@
     timeout_seconds: float = 10.0,
 ) -> LaunchedSupervisor:
     """Spawn a detached foreground supervisor and wait for its exact publication."""
-    ensure_runtime_directory(root)
     paths = supervisor_settings(root).runtime.paths
+    paths.runtime_root.mkdir(parents=True, exist_ok=True)
     report = paths.runtime_root / f"launch-{uuid4().hex}.report"
     os.close(
         os.open(report, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
@@ -291,6 +320,13 @@
     while True:
         exit_code = child.poll()
         if exit_code is not None:
+            try:
+                proof = json.loads(_read_launch_report(report))
+            except ValueError:
+                proof = {}
+            if exit_code == 0 and proof == {"pid": child.pid, "done": True}:
+                report.unlink()
+                return LaunchedSupervisor(None)
             raise _launch_failure(report, child.pid, exit_code, "exited")
         launched = _published_run(registry, paths, root, child.pid, report)
         if launched is not None:
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/cli.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/cli.py
@@ -486,7 +486,19 @@
         raise CommandError(
             ErrorCode.RUNTIME_FORMAT, str(error), path=str(error.evidence.path)
         ) from error
-    return _attach_view(root, run.root, run.run_id)
+    if run is None:
+        return 0
+    paths = supervisor_settings(root).runtime.paths
+    batch_id = StateStore(paths.state_file).read()["batch"]["id"]
+    try:
+        return _attach_view(root, run.root, run.run_id)
+    except (ValueError, RuntimeError) as error:
+        from ovcaq.runtime._run_observation import observe_selected_run
+        if "no match" in str(error).lower():
+            with observe_selected_run(paths, run, batch_id=batch_id) as selected:
+                if selected.ended and selected.state is not None and selected.state["batch"]["status"] == "completed":
+                    return 0
+        raise ValueError(str(error)) from error
 
 
 def _resume_and_attach(root: Path) -> int:

```

## Candidate 4

Exact argv:
```
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /tmp/devon-r7-test-4.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py
```

Actual output:
```
.........................                                                [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-cea151e0-d568-40a2-a18d-020a75114783
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-cea151e0-d568-40a2-a18d-020a75114783'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-666c25ce-3e36-42c8-853c-8c910a2f9269
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-666c25ce-3e36-42c8-853c-8c910a2f9269'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 2 warnings in 2.36s

```

Diff (1–3 against supplied backups; 4–7 isolated mutation against candidate 3):
```diff
--- src/ovcaq/supervisor_cli.py
+++ src/ovcaq/supervisor_cli.py
@@ -303,8 +303,8 @@
         os.open(report, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
     )
     argv = (*argv_prefix, "--root", str(root), "run", "--no-tui")
-    if agent is not None:
-        argv += ("--agent", agent)
+    # Wrong: discard explicit agent selection.
+    agent = None
     child = subprocess.Popen(
         argv,
         stdin=subprocess.DEVNULL,

```

## Candidate 5

Exact argv:
```
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /tmp/devon-r7-test-5.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py
```

Actual output:
```
.........................                                                [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-5fa6a578-53df-487a-9c80-0d63b08e1c77
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-5fa6a578-53df-487a-9c80-0d63b08e1c77'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-e42001b6-763b-4713-9dea-ff92e808f040
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-e42001b6-763b-4713-9dea-ff92e808f040'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 2 warnings in 2.22s

```

Diff (1–3 against supplied backups; 4–7 isolated mutation against candidate 3):
```diff
--- src/ovcaq/supervisor_cli.py
+++ src/ovcaq/supervisor_cli.py
@@ -302,6 +302,7 @@
     os.close(
         os.open(report, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
     )
+    argv_prefix = (sys.executable, "-m", "ovcaq")
     argv = (*argv_prefix, "--root", str(root), "run", "--no-tui")
     if agent is not None:
         argv += ("--agent", agent)

```

## Candidate 6

Exact argv:
```
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /tmp/devon-r7-test-6.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py
```

Actual output:
```
.........................                                                [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c0ed29bf-a591-4987-85d0-56e3f785aac4
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c0ed29bf-a591-4987-85d0-56e3f785aac4'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c5631048-1a61-446a-9195-32b2a8b91b5c
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c5631048-1a61-446a-9195-32b2a8b91b5c'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 2 warnings in 2.10s

```

Diff (1–3 against supplied backups; 4–7 isolated mutation against candidate 3):
```diff
--- src/ovcaq/supervisor_cli.py
+++ src/ovcaq/supervisor_cli.py
@@ -316,6 +316,7 @@
         env={**os.environ, LAUNCH_REPORT_ENV: str(report)},
     )
     registry = FleetRegistry(paths.fleet_root)
+    timeout_seconds = 0.0
     deadline = time.monotonic() + timeout_seconds
     while True:
         exit_code = child.poll()

```

## Candidate 7

Exact argv:
```
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /tmp/devon-r7-test-7.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py
```

Actual output:
```
.........................                                                [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-a6ae171b-e62b-437d-83fc-ae418c2cd51e
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-a6ae171b-e62b-437d-83fc-ae418c2cd51e'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-bdf6e93b-7966-489a-8b6d-be10a5342497
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-bdf6e93b-7966-489a-8b6d-be10a5342497'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
25 passed, 2 warnings in 2.10s

```

Diff (1–3 against supplied backups; 4–7 isolated mutation against candidate 3):
```diff
--- src/ovcaq/supervisor_cli.py
+++ src/ovcaq/supervisor_cli.py
@@ -284,7 +284,7 @@
         raise _launch_failure(report, pid, None, "has an inconsistent run observation")
     if status != "active":
         return None
-    report.unlink()
+    pass  # Wrong: retain successful launch report forever
     return LaunchedSupervisor(FleetRun.from_entry(entry))
 
 
@@ -325,7 +325,7 @@
             except ValueError:
                 proof = {}
             if exit_code == 0 and proof == {"pid": child.pid, "done": True}:
-                report.unlink()
+                pass  # Wrong: retain successful launch report forever
                 return LaunchedSupervisor(None)
             raise _launch_failure(report, child.pid, exit_code, "exited")
         launched = _published_run(registry, paths, root, child.pid, report)

```


## Raw Tess strengthening dispositions

# Task 7 Tess strengthening

1. strengthened: `test_child_completion_report_cannot_complete_a_replacement_batch`. The real foreground child completes and supplies its own opaque report. At the exited-child/pre-parent-poll boundary, the public state service starts a replacement batch. The parent must reject success and preserve both replacement state and failure report. A matching-PID/done-only candidate accepts this case incorrectly. No report keys or encoding are prescribed.
2. strengthened: `test_live_handshake_returns_exact_published_child_identity[alternate]`. A configured alternate agent is passed explicitly; the real fixture child publishes the agent it received in argv. The returned exact FleetRun must name that agent. The default-agent case remains.
3. strengthened: `test_real_empty_child_commits_completion_before_parent_first_poll`. A custom argv prefix records its actual arguments, then runs the real CLI with runpy. The test requires that record, exactly one child, committed completion, and no live registry entry.
4. strengthened: `test_live_handshake_waits_for_publication_within_configured_deadline` and `test_unpublished_child_fails_within_configured_deadline`. A real child waits at a pipe barrier. Publication remains impossible through the first parent poll and is released at the second process-poll boundary. A separate never-released child must produce failure within the configured bounded interval. Fixture teardown kills and awaits it.
5. strengthened: `test_real_empty_child_commits_completion_before_parent_first_poll` and `test_live_handshake_returns_exact_published_child_identity`. Both successful outcomes require removal of the exact provisioned report. Existing private diagnostic preservation checks remain; replacement-state failure also preserves the exact report bytes.

Only `tests/integration/test_launcher_outcomes.py` changed. No helper file, production, workflow state, or git changes. File is 638 lines; every function is under 50 source lines, hence also under 50 computed lines. Existing real-process, unsafe-destination, diagnostic, attach-race, and duplicate-owner cases remain.

Validation command: `mise exec -- python3 docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/r7-tess-strengthen-pytest-access.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py`.

Result against restored production: **18 passed, 11 failed, 2 warnings in 2.47s; exit 1**. The failures cover existing required quick completion, custom layout, early diagnostics, hostile diagnostic sanitization, successful attach cleanup race, and duplicate-owner guidance. New rejection/forwarding/deadline cases passed. An initial sandbox attempt exited 2 before pytest because the existing uv cache was inaccessible; preserved at `r7-tess-strengthen-pytest.log`. The authorized-access test process was awaited. Pytest warnings concerned cleanup of pre-existing garbage directories.

After that run, formatting was tidied and the successful quick-completion report-removal assertion was moved after the successful return assertion, so it does not mask a launcher exception. No second suite was run merely to recover a count. No mutation was reapplied: candidate rejection is reasoned from the supplied diffs, not claimed as separately executed verification.

ASSUMPTIONS:
- Newlines remain allowed as diagnostic separators; other Unicode Cc controls are rejected, preserving the existing diagnostic test convention.
- The 0.15-second timeout allows up to 2 seconds total wall time for process startup and normal scheduling; unusually overloaded hosts may exceed that bound. Successful delayed publication uses a pipe barrier and process polls rather than a guessed sleep.


## Raw final Tess quality evidence

Task 7 final Tess duplicate-owner quality retry (dispatchca6be7c8).

Changed only tests/integration/test_launcher_outcomes.py. Preserved the existing
exited-child duplicate-owner scenario and all prior assertions. Added a starting
ordering through a parametrized fixture: the real child announces startup through
stdout, then waits on stdin with a finite 10-second select deadline before entering
the real CLI. The existing spawn boundary reads that announcement and checks the
child is alive before returning it. The healthy owner is already published.
Existing finite process cleanup awaits both children. No production, state, or git
operations; no helper file or subagents.

Verification: 29 passed, 1 failed, 2 warnings in 2.56s; exit 1.
The new [starting] case fails at test_launcher_outcomes.py:653 because the
LaunchError evidence includes `ovcaq stop`, violating F35. The attach-guidance
assertion immediately before it passes. All 29 prior cases still pass.
Warnings concern pytest cleanup of pre-existing temporary garbage directories.

Command: uv run pytest -q --tb=line
/Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_launcher_outcomes.py
(through the required 300-second bounded runner).

Initial sandbox attempt: exit 2, uv cache access denied; preserved in
docs/dev/tmp/r7-tess-owner-tests.log. Approved process/cache access run and exact
failure output: docs/dev/tmp/r7-tess-owner-tests-approved.log.

Size inspection: 661 file lines; every function under 50 computed nonempty,
noncomment lines. Recorded in docs/dev/tmp/r7-tess-owner-size.log.

ASSUMPTIONS: none


## Raw dispatch failure and debug evidence

# Task 7 native validator launch failure

## Failure Capture
- Session / task: autocodex build, repair task7, Devon dispatch d12c9ddb.
- Goal in progress: evaluate local regression tests by temporary wrong implementations, restore all files, report observed test gaps.
- Error: Agent errored: This content was flagged for possible cybersecurity risk. If this seems wrong, try rephrasing your request. If you're doing authorized security work that requires more cyber permissive safeguards, apply for Daybreak access via https://platform.openai.com/settings/organization/status-and-access before retrying.
- Last successful step: tests committed23716ae; prompt measured43,201 bytes.
- Last failed tool / command: native collaboration.spawn_agent task devon_r7.
- Repeated pattern seen: none; first infrastructure failure for task7.
- Environment assumptions to verify: scoped production/test slice unchanged, no worker processes or partial report; git status confirms only existing workflow-store changes. No context-pressure evidence; the failure returned immediately, before any useful result.

## Recovery Action
- Diagnosis chosen: automated dispatch content-filter rejection, not an implementation/test failure. Exact trigger unknown. The requested work is benign local unit-test mutation testing using synthetic fixtures; it accesses no external targets or real credentials.
- Smallest action taken: one allowed infrastructure retry with the same complete measured prompt and a clarifying outer description of the local test scope. No safeguard, networking permission, guard or model setting is changed.
- Why this is safe: the tests and required persona remain unchanged; writable sources are backed up, no live service is targeted, and all local child processes require cleanup. The task is authorized by the invoked workflow.
- What evidence would prove the fix worked: native agent returns an actual bounded test-validation result and restores the task slice; another infrastructure failure requires persisted pause without advancing.

## Agent Self-Debug Report
- Session / task: autocodex build / task7.
- Failure: native validator launch rejected by content filter.
- Root cause: policy-layer classification; exact reason unavailable.
- Recovery action: tree inspection plus one unchanged-prompt infrastructure retry.
- Result: success; same-prompt retry returned five verified coverage gaps. Main independently verified all three production originals restored and canonical tests unchanged.
- Token / time burn risk: capped at one retry and45-minute watchdog; no repeated bypass attempts.
- Follow-up needed: complete the normal Tess strengthening and implementation gates. The same dispatch row is closed again with outcome ok; the initial error remains preserved.
- Preventive change to encode later: none; no repository configuration change justified by one classifier failure.
