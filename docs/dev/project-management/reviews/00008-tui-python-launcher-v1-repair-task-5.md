# PRD 00008 recovery task 5

Public TUI pause/resume now hold shared registry exclusion through the guarded state transaction. Identity failure during publication rolls back exact state and backup bytes with committed=False; separate post-commit staleness retains the committed=True diagnostic. Interactive live CLI resume uses the same control service and CAS. Stop honors the injected registry. FleetRun.from_entry copies the six fields once for launch publication, CLI selection and discovery. No new lock, schema, writer, module or liveness policy.

Base:52c1aadafa0da5cfd3a02a267f147cc15b1510ca. Initial tests:882428f14e44ded74d49e101b6a0be2d1fe1f98a. Strengthened tests:8bdd20e1c99c630e18af10d80e00e531758b14bf. Implementation/final:ff7a6922c4207074a266d0b9d326bb91318a0376.

## Dispatch and verification

Logical opus mapped to OpenAI gpt-6-astra for all native task agents. UI routing attempted the installed Gemini wrapper; its unchanged nesting guard returned exit3 before a backend ran, retained in r5-gemini-probe.log. No guard was stripped. Qwen was excluded as UI, with no task preflight. Tess38264684 and12a68adc used two of four allowed calls. Devon8c8ff6ac independently proved eight wrong implementations passed all original14 selected cases; every production original was independently verified restored byte-for-byte. Tess strengthened every numbered point; no in-contract dismissals or second Devon run.

Main computed shape checked29 functions in two files with zero MECH findings. Manual four-check review passed: behavior names, observable effects, relevant boundary/error/concurrent cases, and non-tautological assertions. Test-only style passed. Main red at the strengthened test commit:21 failed,12 passed,59 deselected, reflecting missing behavior/interfaces rather than fixture errors.

Ivan3c61b902 implemented only five allowed production modules; its narrow33 cases passed. Coordinator inspection found the deleted existing post-commit check and e00992f7 restored it before commit. Both reports say ASSUMPTIONS:none. Canonical tests were independently checked byte-unchanged from the strengthened commit. Initial implementation sandbox uv-cache failure was retained and the approved retry passed; all real-process runs were awaited. Ivan reported an initial cat prompt read before learning the embedded prohibition; subsequent reads were bounded and compliant.

Main committed verification: uv run pytest -q --tb=line tests/integration/test_control_commit_identity.py tests/runtime/test_supervisor_cli.py -k 'control_commit or replacement_during_control or test_control or test_shared_run or test_injected_registry'. Exit0:33 passed,59 deselected,2 pytest cleanup warnings in9.67s. Exact command/output metadata is retained in r5-main-green.log and its JSON sidecar. The full suite remains deferred to the required phase-end gate.

Self-deslop skipped:trivial (latest implementation net-9 lines over6 files). Style clean; split hygiene clean; reflow clean. No new assumptions. Publication tests retain a bounded0.2s no-output observation, which is best-effort scheduling evidence, not proof against arbitrary child starvation. A direct post-commit-only identity-loss test was not added; preservation was checked in the diff. Healthy CLI attachment assertions pin root/run-ID at the viewer boundary, not the PID/start after that boundary. These limits remain available to fresh completion review.

## External review and dispositions

Pat3f124b03 ran through the installed use-sonnet wrapper with no tools, approved network access and a48,314-byte complete prompt, including the task4 guard prerequisite diff. Session052c7a75-e67e-4b27-9aa3-ce4cae7bde7a; actual Anthropic claude-sonnet-5-5 confirmed from transcript model metadata. Parser validated output before dispositions. All three closures F17/F24/F34 resolved; no CRITICAL/HIGH/MEDIUM findings. LOW duplicate initial identity read is retained: it obtains paths before taking exclusion, and the guarded entry must still revalidate after acquisition. The suggested closure-variable alternative would trade a read for mutable closure plumbing; no LOW-only correction was dispatched. This task review does not replace the mandatory fresh completion review.

## Raw task review

CLOSURE | resolved | F17 "Pause and resume verify run identity before and after the state commit, leaving a race where the selected run can exit and a replacement can start between verification and mutation" | `_mutate` now runs `validate` under `self._registry.guard_mutation(validate)` and passes `publication_guard=guard` to `StateService`. The guard re-validates at publication boundaries and rolls back, and `test_control_commit_owner_exit_rolls_back_before_replacement_reads` covers it with a real replacement process.

CLOSURE | resolved | F24 "`_resume_and_attach` repeats existing services. It builds a `FleetRun` from a `FleetEntry` by hand... skips the post-write re-verify... same copy also appears at supervisor_cli.py:260 and tui/discovery.py:22" | `cli.py` now calls `FleetRun.from_entry(entry)` and `RunControlService(registry).resume(run, revision)`, which includes the post-write re-verify. `supervisor_cli.py` and `discovery.py` also use `from_entry`.

CLOSURE | resolved | F34 "`RunControlService.stop` calls `stop_supervisor(run)`, which builds its own `FleetRegistry` instead of using the injected `self._registry`" | `stop` now calls `stop_supervisor(run, registry=self._registry)`, and `stop_supervisor` forwards the registry to `verify_run`. `test_injected_registry_stop_*` covers this with a private registry root.

LOW | src/ovcaq/tui/app.py:89 | `_mutate` calls `validate()` once to get `paths`, then `guard_mutation` calls it again on entry with nothing in between. That is one redundant pass. | Keep it only if `paths` is needed before the lock is taken. Otherwise take `paths` from a closure variable set by the first guarded `validate()` call.


## Tess numbered dispositions (raw)

# Tess task-5 strengthening — dispatch 12a68adc

Completed the single adversarial strengthening round. Only `tests/integration/test_control_commit_identity.py` changed. The existing runtime rollback oracle, production, workflow state, commits, and original reports were untouched. The complete rendered feedback was read, including a separately reread segment truncated by tool output. Cumulative input remains below 100K tokens.

1. strengthened: `test_control_commit_pause_resume_targets_only_selected_identity` — parametrized maintenance, a distinct reason, and None; exact supplied detail or absent notice is asserted along with one revision and unchanged noncontrol state.
2. strengthened: `test_control_commit_pause_resume_targets_only_selected_identity` — stale pause now independently requires RevisionConflictError and exact state/backup bytes, alongside the existing stale-resume oracle.
3. strengthened: `test_control_commit_rejects_missing_ownership_proof_with_live_process[lock]` — a real child releases its RunLock, emits a released barrier, and remains alive with unchanged registry/metadata. Both pause/resume reject with committed=False; stop emits no signal. Existing owner-exit/publication barriers are retained unchanged in behavior.
4. strengthened: `test_control_commit_rejects_missing_ownership_proof_with_live_process[registry-absent]` and `[registry-replaced]` — remove or replace only the selected registry entry while confirming real process liveness, held lock and unchanged metadata; pause/resume/stop reject with exact durable bytes and no signal.
5. strengthened: `test_injected_registry_stop_requires_all_proof_for_live_process` — service and direct callers reject independent run-ID, root, metadata, empty injected registry, and released-lock mismatches while exact PID/start remains live. Signals are captured only at the syscall boundary; signal-zero checks remain real. Existing healthy nondefault-registry stop coverage remains.
6. strengthened: `test_shared_run_conversion_and_discovery_preserve_distinct_entries` — real published entries include one malformed record and one exited-process stale record; exact malformed_entries and stale_entries path tuples must survive discovery. This preserves the existing FleetView diagnostic fields through the shared-conversion change, without inventing new diagnostics or schemas.
7. strengthened: `test_shared_run_conversion_copies_independent_identity_fields` — independent ID/agent parameter combinations include selected with two nongeneric agents; all six FleetRun fields must equal the input entry exactly.
8. strengthened: `test_shared_run_conversion_and_discovery_preserve_distinct_entries` — three distinct live child owners require cardinality three and exact complete membership, alongside stale/malformed exclusions.

All eight are within the supplied existing public-control/conversion contracts. No findings were dismissed as in-contract. No new lifecycle policy or guessed API was introduced. `_OWNER` gained an explicit release command for the new live-process/absent-lock scenario; its prior continue/exit path is preserved. Ruff formatting required extracting the existing CLI terminal boundary setup into a helper to keep the sound CLI test under the mandated size limit; its assertions and boundary behavior are preserved.

Exact narrow test command:

```text
mise exec -- python3 docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/r5-tess-strengthen-tests.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_control_commit_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_supervisor_cli.py -k 'control_commit or replacement_during_control or test_control or test_shared_run or test_injected_registry'
```

One actual pytest run this round: **92 collected, 33 selected, 12 passed, 21 failed, 59 deselected, 2 warnings in 4.94s; exit 1**. Log: `docs/dev/tmp/r5-tess-strengthen-tests.log`. Authorized escalation was used for uv cache/process access. No directories/full suite were run, and no adversarial production candidates were reapplied.

Failure breakdown against restored production:

- Four replacement publishers overtake selected control publication.
- Four final-boundary/old-oracle cases incorrectly report committed=True.
- One stale interactive resume returns success.
- One healthy custom-registry service stop rejects its valid owner.
- Six direct stop cases report missing `stop_supervisor(..., registry=...)` (TypeError).
- Five conversion cases report missing `FleetRun.from_entry` (AttributeError).

These exact additive interfaces remain missing in restored production; their specified tests are intentionally retained. The combined discovery test reaches the missing conversion before its final discovery assertions, so this run does not independently establish the new diagnostic/cardinality assertions against a completed implementation. No interface blocker prevented writing them because both additive contracts were explicitly supplied.

Passing cases: three pause-reason/CAS variants, healthy interactive resume, three isolated ownership-proof cases, and five negative service-stop cases. The two warnings are pytest cleanup warnings for prior temporary garbage directories.

Exact-file verification, completed before the coordinator asked not to duplicate its own gates:

- `r5-tess-strengthen-format.log`: Ruff format, exit 0.
- `r5-tess-strengthen-lint.log`: Ruff check, all checks passed, exit 0.
- `r5-tess-strengthen-format-check.log`: Ruff format --check, already formatted, exit 0.
- `r5-tess-strengthen-final-size.log`: 611 file lines; maximum function length 44 physical lines.

Inspection logs: `r5-tess-strengthen-read.log`, `r5-tess-strengthen-read-full.log`, `r5-tess-strengthen-read-gap.log`, `r5-tess-strengthen-size.log`. Original task report/logs are preserved. No further test rerun was used to recover counts. No production body reads were performed outside the explicitly supplied feedback text.

abort_reason: null

ASSUMPTIONS: none


## Devon evidence (raw)

# Devon R5 adversarial validation — task5

Eight independent wrong candidates broke the supplied tests. Every candidate passed all 14 selected cases, with 59 deselected and two pytest temporary-directory cleanup warnings. No tests, workflow state, or git operations were changed.

Weak points:

1. `test_control_commit_pause_resume_targets_only_selected_identity` — pause discards every supplied reason and always records maintenance — Parametrize successful pause with multiple distinct reasons and None; assert exact detail or absent reason each time.
2. `test_control_commit_pause_resume_targets_only_selected_identity` — pause ignores expected_revision while resume still enforces it — Attempt pause using a stale revision; require RevisionConflictError and byte-identical state plus backup.
3. `test_control_commit_owner_exit_rolls_back_before_replacement_reads` — verify_run omits run-lock ownership; tests invalidate both process and lock together, so process checking masks the omission — Release the selected run lock while keeping the selected process, registry and metadata live; assert pause/resume fail and preserve bytes, and stop emits no signal.
4. `test_control_commit_pause_resume_targets_only_selected_identity` — verify_run ignores all live registry membership after taking its snapshot — Remove or replace just the selected registry entry while retaining live process, lock and metadata; assert all selected controls reject without mutation or signal.
5. `test_injected_registry_stop_signals_only_exact_selected_owner` — stop_supervisor ignores the injected registry, metadata and lock and authorizes any matching live PID/start pair — Keep process identity live but mismatch run_id/root/metadata or supply an empty different registry; require rejection and zero signals for service and direct callers.
6. `test_shared_run_conversion_and_discovery_preserve_distinct_entries` — discovery always reports empty malformed_entries and stale_entries — Supply a registry with a malformed entry and a stale entry; assert exact diagnostic path tuples are preserved.
7. `test_shared_run_conversion_and_discovery_preserve_distinct_entries` — FleetRun.from_entry derives agent from run_id: selected maps to generic, every other ID maps to local — Parametrize arbitrary IDs and independent agent strings, including selected with a different agent, and assert every FleetRun field equals its entry.
8. `test_shared_run_conversion_and_discovery_preserve_distinct_entries` — discovery truncates the fleet to its first two entries — Publish at least three distinct live runs and assert complete cardinality and exact membership.

## Common callable baseline

Original source lacks the added conversion/injected-stop APIs and uses unguarded controls. Every candidate includes this same baseline: FleetRun.from_entry; stop registry forwarding; registry.guard_mutation plus StateService publication_guard for pause/resume; live interactive resume routed through RunControlService inside existing error translation. No baseline-only test was run. Candidate differences below are independent, never cumulative. This baseline is included in every full candidate diff.

```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/app.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/app.py
@@ -76,21 +76,18 @@
         )
 
     def stop(self, run: FleetRun) -> ProcessIdentity:
-        return stop_supervisor(run)
+        return stop_supervisor(run, registry=self._registry)
 
     def _mutate(self, run: FleetRun, change: Callable[[StateService], object]) -> None:
-        try:
-            paths = verify_run(run, self._registry)
-        except (OSError, ValueError, RuntimeError) as error:
-            raise StaleSelectionError(str(error), committed=False) from error
-        change(StateService(StateStore(paths.state_file)))
-        try:
-            verify_run(run, self._registry)
-        except (OSError, ValueError, RuntimeError) as error:
-            raise StaleSelectionError(
-                f"change committed, but the selection is now stale: {error}",
-                committed=True,
-            ) from error
+        def validate():
+            try:
+                return verify_run(run, self._registry)
+            except (OSError, ValueError, RuntimeError) as error:
+                raise StaleSelectionError(str(error), committed=False) from error
+
+        with self._registry.guard_mutation(validate) as guard:
+            paths = validate()
+            change(StateService(StateStore(paths.state_file), publication_guard=guard))
 
 
 @dataclass(frozen=True, slots=True)
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/cli.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/cli.py
@@ -514,12 +514,11 @@
     )
     revision = service.show()["revision"]
     try:
-        verify_run(run, registry)
+        RunControlService(registry).resume(run, revision)
     except (OSError, ValueError, RuntimeError) as error:
         raise CommandError(
             ErrorCode.RUNTIME_FORMAT, f"selected run is stale: {error}"
         ) from error
-    service.resume(expected_revision=revision)
     return _attach_view(root, run.root, run.run_id)
 
 
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
@@ -315,8 +315,8 @@
         time.sleep(min(LAUNCH_POLL_SECONDS, remaining))
 
 
-def stop_supervisor(run: FleetRun) -> ProcessIdentity:
-    verify_run(run)
+def stop_supervisor(run: FleetRun, *, registry: FleetRegistry | None = None) -> ProcessIdentity:
+    verify_run(run, registry)
     identity = ProcessIdentity(run.pid, run.process_start)
     os.kill(identity.pid, signal.SIGTERM)
     return identity
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/registry.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/registry.py
@@ -164,6 +164,12 @@
     started_at: str
     pid: int
     process_start: str
+
+
+    @classmethod
+    def from_entry(cls, entry: FleetEntry) -> Self:
+        return cls(entry.run_id, entry.root, entry.agent, entry.started_at,
+                   entry.pid, entry.process_start)
 
 
 @dataclass(frozen=True)
```

## Candidate 1: pause discards every supplied reason and always records maintenance

Exact full candidate diff: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-candidate-1.diff`. Isolated wrong implementation:

```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/app.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/app.py
@@ -62,7 +62,7 @@
     def pause(
         self, run: FleetRun, expected_revision: int, reason: str | None = None
     ) -> None:
-        notice = operator_notice(reason)
+        notice = operator_notice("maintenance")
         self._mutate(
             run,
             lambda service: service.request_pause(
```

Exact command:

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-test-1-approved.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_control_commit_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_supervisor_cli.py -k 'control_commit or replacement_during_control or test_control or test_shared_run or test_injected_registry'
```

Passing output (verbatim retained log):

```text
..............                                                           [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-2c4417a6-8383-4a16-8503-9d4b56208631
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-2c4417a6-8383-4a16-8503-9d4b56208631'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-04c62902-38e7-475c-a231-f27425fc4e31
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-04c62902-38e7-475c-a231-f27425fc4e31'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
14 passed, 59 deselected, 2 warnings in 6.32s
```

## Candidate 2: pause ignores expected_revision while resume still enforces it

Exact full candidate diff: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-candidate-2.diff`. Isolated wrong implementation:

```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/app.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/app.py
@@ -66,7 +66,7 @@
         self._mutate(
             run,
             lambda service: service.request_pause(
-                notice, expected_revision=expected_revision
+                notice, expected_revision=None
             ),
         )
 
```

Exact command:

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-test-2.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_control_commit_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_supervisor_cli.py -k 'control_commit or replacement_during_control or test_control or test_shared_run or test_injected_registry'
```

Passing output (verbatim retained log):

```text
..............                                                           [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-e2bba771-9269-49da-9151-59f2a23f6394
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-e2bba771-9269-49da-9151-59f2a23f6394'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-96213168-2171-4594-aaf8-31a85328b476
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-96213168-2171-4594-aaf8-31a85328b476'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
14 passed, 59 deselected, 2 warnings in 6.99s
```

## Candidate 3: verify_run omits run-lock ownership; tests invalidate both process and lock together, so process checking masks the omission

Exact full candidate diff: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-candidate-3.diff`. Isolated wrong implementation:

```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
@@ -171,7 +171,6 @@
             for entry in live
         )
         and process_matches(identity)
-        and run_lock_held(paths.run_lock)
     )
     if not trusted:
         raise RuntimeError(
```

Exact command:

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-test-3.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_control_commit_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_supervisor_cli.py -k 'control_commit or replacement_during_control or test_control or test_shared_run or test_injected_registry'
```

Passing output (verbatim retained log):

```text
..............                                                           [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-e7f4bd3d-4614-4504-a0c1-4d0b835c6bf9
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-e7f4bd3d-4614-4504-a0c1-4d0b835c6bf9'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-38da6461-1660-4846-b38b-63971c8da306
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-38da6461-1660-4846-b38b-63971c8da306'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
14 passed, 59 deselected, 2 warnings in 6.19s
```

## Candidate 4: verify_run ignores all live registry membership after taking its snapshot

Exact full candidate diff: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-candidate-4.diff`. Isolated wrong implementation:

```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
@@ -164,12 +164,6 @@
     trusted = (
         metadata.run_id == run.run_id
         and ProcessIdentity(metadata.pid, metadata.process_start) == identity
-        and any(
-            entry.run_id == run.run_id
-            and entry.root == run.root
-            and ProcessIdentity(entry.pid, entry.process_start) == identity
-            for entry in live
-        )
         and process_matches(identity)
         and run_lock_held(paths.run_lock)
     )
```

Exact command:

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-test-4.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_control_commit_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_supervisor_cli.py -k 'control_commit or replacement_during_control or test_control or test_shared_run or test_injected_registry'
```

Passing output (verbatim retained log):

```text
..............                                                           [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ab9d4f10-3a52-4bab-b417-bc582b6cadb7
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ab9d4f10-3a52-4bab-b417-bc582b6cadb7'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-66bb54fc-9e69-4a0e-a3a8-8a21b64c5ee9
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-66bb54fc-9e69-4a0e-a3a8-8a21b64c5ee9'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
14 passed, 59 deselected, 2 warnings in 6.21s
```

## Candidate 5: stop_supervisor ignores the injected registry, metadata and lock and authorizes any matching live PID/start pair

Exact full candidate diff: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-candidate-5.diff`. Isolated wrong implementation:

```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py
@@ -316,7 +316,8 @@
 
 
 def stop_supervisor(run: FleetRun, *, registry: FleetRegistry | None = None) -> ProcessIdentity:
-    verify_run(run, registry)
+    if not process_matches(ProcessIdentity(run.pid, run.process_start)):
+        raise RuntimeError("stale process")
     identity = ProcessIdentity(run.pid, run.process_start)
     os.kill(identity.pid, signal.SIGTERM)
     return identity
```

Exact command:

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-test-5.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_control_commit_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_supervisor_cli.py -k 'control_commit or replacement_during_control or test_control or test_shared_run or test_injected_registry'
```

Passing output (verbatim retained log):

```text
..............                                                           [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-30682c25-6a58-4b63-9ca7-594af7e7c4f6
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-30682c25-6a58-4b63-9ca7-594af7e7c4f6'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-7b1ddd34-642f-4c7a-9320-df4cf2f0986e
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-7b1ddd34-642f-4c7a-9320-df4cf2f0986e'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
14 passed, 59 deselected, 2 warnings in 7.63s
```

## Candidate 6: discovery always reports empty malformed_entries and stale_entries

Exact full candidate diff: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-candidate-6.diff`. Isolated wrong implementation:

```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/discovery.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/discovery.py
@@ -33,8 +33,8 @@
         runs=tuple(
             sorted(runs, key=lambda run: (run.root, run.started_at, run.run_id))
         ),
-        malformed_entries=snapshot.malformed,
-        stale_entries=snapshot.stale,
+        malformed_entries=(),
+        stale_entries=(),
     )
 
 
```

Exact command:

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-test-6.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_control_commit_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_supervisor_cli.py -k 'control_commit or replacement_during_control or test_control or test_shared_run or test_injected_registry'
```

Passing output (verbatim retained log):

```text
..............                                                           [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-82f1b8c7-17cf-4cbd-a533-22dd8846a78c
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-82f1b8c7-17cf-4cbd-a533-22dd8846a78c'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-b81935d7-5517-42bc-a85d-942aa49d6aff
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-b81935d7-5517-42bc-a85d-942aa49d6aff'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
14 passed, 59 deselected, 2 warnings in 7.35s
```

## Candidate 7: FleetRun.from_entry derives agent from run_id: selected maps to generic, every other ID maps to local

Exact full candidate diff: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-candidate-7.diff`. Isolated wrong implementation:

```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/registry.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/registry.py
@@ -168,7 +168,7 @@
 
     @classmethod
     def from_entry(cls, entry: FleetEntry) -> Self:
-        return cls(entry.run_id, entry.root, entry.agent, entry.started_at,
+        return cls(entry.run_id, entry.root, "generic" if entry.run_id == "selected" else "local", entry.started_at,
                    entry.pid, entry.process_start)
 
 
```

Exact command:

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-test-7.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_control_commit_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_supervisor_cli.py -k 'control_commit or replacement_during_control or test_control or test_shared_run or test_injected_registry'
```

Passing output (verbatim retained log):

```text
..............                                                           [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-2108c7a3-b283-4dfe-98e5-a0350b51aa95
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-2108c7a3-b283-4dfe-98e5-a0350b51aa95'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ce7a4c3d-748e-4eeb-b792-e0095c7e5c39
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ce7a4c3d-748e-4eeb-b792-e0095c7e5c39'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
14 passed, 59 deselected, 2 warnings in 8.48s
```

## Candidate 8: discovery truncates the fleet to its first two entries

Exact full candidate diff: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-candidate-8.diff`. Isolated wrong implementation:

```diff
--- /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/discovery.py
+++ /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/discovery.py
@@ -27,7 +27,7 @@
             pid=entry.pid,
             process_start=entry.process_start,
         )
-        for entry in snapshot.live
+        for entry in snapshot.live[:2]
     )
     return FleetView(
         runs=tuple(
```

Exact command:

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r5-devon-test-8.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_control_commit_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_supervisor_cli.py -k 'control_commit or replacement_during_control or test_control or test_shared_run or test_injected_registry'
```

Passing output (verbatim retained log):

```text
..............                                                           [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-05dae617-c0fb-4faf-a12f-70edc138ed77
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-05dae617-c0fb-4faf-a12f-70edc138ed77'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-3f611f1d-b0cd-4a9a-a1ad-ab354efcb0d4
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-3f611f1d-b0cd-4a9a-a1ad-ab354efcb0d4'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
14 passed, 59 deselected, 2 warnings in 7.27s
```

## Restoration and limits

All five supplied production originals were overwritten from their backup bytes and verified byte-for-byte. SHA-256 evidence:

- `/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/app.py`: `8eaaff38a17ed61a9bef06784f288bc50c3bc0eb93d5f0f8f38c68720fe89a5a`
- `/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/cli.py`: `2695efd2feb937f65a52a5067f935dc71d8a3922201492f169537f7f70308591`
- `/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py`: `db106f224bc92255fe7d55e26094c5d5441829b6afcec17c0f4f8033a2abdba5`
- `/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/discovery.py`: `2ab7ac1e02ce6e17e514a4e54e9777d726e5ca476bf486615e9f06a72f1bff52`
- `/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/registry.py`: `0f91dfab750a64340b0f4442ff6fad91489632511134b60a138f3dba6e44df8d`

The temporary candidate generator was overwritten with the required placeholder after restoration. Diffs, logs, supplied backups and this report remain as requested evidence. No rm command was invoked.

Scope is only the supplied 14 cases; these findings do not establish gaps across the 59 deselected tests or the wider suite. Candidate 7 is intentional fixture overfitting. Candidate 5 subsumes parts of 3 and 4 specifically for stop; the independent general verify_run omissions are separately demonstrated. Candidate 6 tests diagnostics outside the positive fixture; whether another existing test covers it is unknown. No full suite, lint, requirements, architecture, history or other implementation bodies were inspected. Initial prompt reads were unbounded shell reads; subsequent source inspection and all test execution used the bounded runner. Some imports-adjacent lines were returned during the declared source slices.

The first sandboxed candidate-1 command failed before pytest due to uv-cache access (exit 2), preserved in r5-devon-test-1.log. The approved retry used the same selected cases with a new unique log. Each candidate had exactly one actual pytest execution. All actual runs exited 0. Pytest itself emitted its own temporary-directory cleanup warnings; these were not test failures. Work finished within 15 minutes, so no 15-minute watchdog probe or 45-minute termination was needed.

abort_reason: null
