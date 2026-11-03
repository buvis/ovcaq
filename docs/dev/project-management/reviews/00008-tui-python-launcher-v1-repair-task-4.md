# PRD 00008 recovery task 4

Shared guarded mutation prerequisite completed. FleetRegistry.guard_mutation holds existing registry mutation exclusion through state commit or rollback and validates exact selection plus root/lock identity at publication boundaries. StateService forwards the optional callback to its existing transaction helper. StateStore already provides exact-byte rollback and was not changed. No new lock file, schema, writer or liveness algorithm.

F17 remains OPEN end to end: the public callers still use the old checks. The confirmed remaining gap belongs to already-planned dependent task 5. This task completion records the independently tested prerequisite, not closure of the original issue; task 5 and the fresh completion review must close it.

Base: 019949ad8f49dd73f645662ee658fa5aec429dda. Initial tests: 205a4879867846a271bafac367f35d8e0a486cf0; strengthened tests: d1b06c8b4f68c4256148077c21602a612af32d4f. Implementation: 0d082466bde394233dae41d183ee4f3ecddcf7ca. Required style correction: 52c1aadafa0da5cfd3a02a267f147cc15b1510ca.

## Dispatch and verification

Logical opus mapped to OpenAI gpt-6-astra for every native task agent. Backend contract task routed to the native Opus-role implementation; Qwen/Codex-rung interception did not apply. Tess: 20322a18,65a21792,25619156 (three of four calls used). Quality retry separated publication-complete from the later state read, preventing the state lock from masquerading as registry exclusion. Computed tautology and all four manual checks passed, as did test-only style limits.

Devon b3513884 independently proved eight candidates passed all original 42 cases. Main session verified all three original production files restored byte-for-byte and canonical tests unchanged. Tess strengthened seven and classified post-context use in-contract; every numbered disposition is retained below. No second Devon pass.

Ivan ef786dcf implemented two production modules. The main pre-commit review found a public callback signature mismatch; 73bbddc4 corrected validate: Callable[[], object] while preserving a None-returning publication guard. Fresh isolated cleanup 69380873 found no slop. Style gate flagged StateService.add_task at 53 lines; the one permitted correction a6b108c9 collapsed two expressions without changing their AST/behavior, yielding 47 lines. No tests changed during implementation/style. No assumptions reported.

Main red: 82 failed,4 passed (missing guard APIs, not fixture failures). Main green: 86 passed. Final committed HEAD52c1aadafa0da5cfd3a02a267f147cc15b1510ca: uv run pytest -q --tb=line tests/integration/test_guarded_run_mutation.py tests/state/test_guarded_service.py; exit0,86 passed,2 warnings in6.71s. Warnings are pytest temporary-directory cleanup. Real subprocess/ps/filesystem access used the exact approved command. Initial sandbox uv-cache failure evidence remains in the implementor report; retry succeeded. Full suite deferred until all tasks complete.

Self-deslop: noop. Style: fixed:52c1aadafa0da5cfd3a02a267f147cc15b1510ca. Split hygiene: clean. Reflow: clean. Tests exercise six durable boundaries for both actions, exact state/backup restoration including missing backup and BaseException, successful/CAS/reused guards, real owner exit and replacement publication, release after normal/error exit, symlink lock and late lock replacement. The 0.2s no-output blocking observation is bounded best-effort scheduling evidence; it is not a proof under arbitrary child starvation. The child signals attempting after acquiring RunLock and mutation-complete before reading StateStore, reducing but not eliminating that limitation.

## External review and dispositions

Pat f0f86751 used tool-free Anthropic claude-sonnet-5-5 (transcript-confirmed), session3ea7c585-1e27-440b-8845-cc85f2cb09fe, via the installed guarded wrapper with approved network access. The38,040-byte prompt included full diff, recorded final test result and explicit caller-wiring boundary. A prior prompt rowaf41b565 was prepared but never dispatched because the required style correction came first; it is closed error with that precise reason, not counted as a review.

Parser validated the review. Its unresolved F17 verdict is confirmed and retained as a pending HIGH closure obligation for task5, whose approved scope owns public wiring; no unsupported whole-issue closure is claimed here. No new correctness defect was reported in the shared prerequisite. The formatting LOW is explained by the mandatory style gate. Shared test helper import and bounded blocking observation LOWs remain for fresh completion review; no extra repair cycle was triggered for LOW findings.

## Raw task review

CLOSURE | unresolved | "F17 🟠 Pause and resume verify run identity before and after the state commit, leaving a race where the selected run can exit and a replacement can start between verification and mutation; the replacement then receives the control action despite the exact-targeting requirement | File: src/ovcaq/tui/app.py:82" | The diff adds `FleetRegistry.guard_mutation` and `StateService(publication_guard=...)`, and the integration tests show rollback before a replacement can read the action. It does not touch `src/ovcaq/tui/app.py`, so the reachable defect there stays open until task 5 wires the callers. This matches the task's stated scope.

LOW | src/ovcaq/state/commands.py:200 | `add_task` and a nearby `_transaction` call are reformatted (multi-line collapsed to one line). The change is unrelated to the guard and widens the diff. | Drop those hunks, or keep them only if a line-length gate requires them.

LOW | tests/integration/test_guarded_run_mutation.py:12 | The file imports helpers from a sibling test module in another directory (`from test_guarded_service import ...`, which lives in `tests/state`). This works only because of how pytest sets `sys.path`, and it couples two test packages. | Move `seed`, `invoke`, `durable_bytes`, `NOTICE` and `RejectedOwner` into a shared `tests/` helper module or fixture.

LOW | tests/integration/test_guarded_run_mutation.py:100 | `assert_blocked` proves "publisher is blocked" with a 0.2s `select` timeout. A slow child can pass this check without the lock having blocked it, so the test can pass wrongly under load. It cannot fail wrongly. | Confirm blocking through an observable state, such as the registry lock being held. If a timeout stays, document it as best-effort.


## Tess numbered dispositions (raw)

# Task 4 Tess adversarial strengthening

Dispatch 25619156; Tess call 3 of 4. Targeted changes only to the authorized state test module. All existing integration process/publication barriers, exact-byte assertions, CAS behavior, trust rejection tests, and prior reports are preserved. No production, workflow state, or git changes. No further Devon round performed.

1. strengthened: `test_rejecting_guard_prevents_mutation_without_cas_or_on_idle_batch` invokes both pause and resume with the expected_revision keyword omitted for a running batch, requires the callback's rejection, and verifies identical state/backup bytes and state revision.
2. strengthened: `test_control_change_commits_once_and_preserves_unrelated_state` covers None and two distinct notices for both guarded and ordinary pause, asserting the exact input as pause_reason.
3. strengthened: `test_control_change_commits_once_and_preserves_unrelated_state` explicitly asserts resume clears pause_reason to None in the existing non-paused fixture, independently of the ordinary-service comparison. The newly authorized existing supervisor-command test confirms these control semantics.
4. in-contract: The pinned contract guarantees exclusion “while the context is active” and shows StateService use inside that context. Calling a retained guard after context exit falls outside the specified lifetime; neither post-exit rejection nor an exception type is defined. No new lifetime contract was invented. The coordinator confirmed this classification without expanding the API contract.
5. strengthened: `test_revision_conflict_preserves_bytes_and_allows_later_guarded_commit` retains its conflict and successful retry assertions, then invalidates the same service's guard and invokes the opposite control action. It requires rejection and preserves the first successful commit's exact state/backup bytes and revision.
6. strengthened: `test_guard_rejection_at_every_durable_boundary_restores_exact_bytes` now also raises KeyboardInterrupt and SystemExit from the publication guard at each durable boundary for both operations. It asserts exact rollback, temporary-file cleanup, and a subsequent successful ordinary operation.
7. strengthened: `test_guard_rejection_at_every_durable_boundary_restores_exact_bytes` adds an initialized revision-zero state with no backup and checks that precondition explicitly. Every-boundary rejection must preserve original state bytes and absent backup. This is a separate scenario rather than an unnecessary cross-product with interrupt types.
8. strengthened: `test_rejecting_guard_prevents_mutation_without_cas_or_on_idle_batch` also uses a schema-valid new_state initial batch with a matching explicit revision, requires guard rejection for both operations, and asserts no durable changes. Its non-running precondition is explicit.

Validation: one exact bounded approved run of `uv run pytest -q --tb=line tests/integration/test_guarded_run_mutation.py tests/state/test_guarded_service.py` returned **82 failed, 4 passed, 2 warnings; exit 1**, in 1.67 seconds. The intentionally absent registry guard and StateService publication_guard APIs remain the blockers. The four ordinary control cases pass. Warnings concern pytest temporary-directory cleanup. Log: `docs/dev/tmp/r4-tess-strengthen-tests.log`. Ruff check passed; the changed file is below 800 lines and each function below 50 computed lines.

No unresolved interface ambiguity. Input remains below 100K tokens.

ASSUMPTIONS: none


## Devon evidence (raw)

# Devon task4 adversarial validation — dispatchb3513884

Only supplied tests, public interfaces, runner and explicitly allowed source slices read. Input stays below 100K tokens. Initial sandbox run could not initialize uv cache; infrastructure failure, not an exploit verdict. Exact output is in r4-devon-attempt-1-sandbox.log. All verdicts use the exact authorized bounded two-file command.

Shared candidate implementation (added missing public APIs):

```diff
--- original/registry.py
+++ base/registry.py
@@ -294,6 +294,26 @@
             yield
         finally:
             os.close(descriptor)
+
+    @contextmanager
+    def guard_mutation(self, validate):
+        with self._directory(create=True) as directory:
+            assert directory is not None
+            with self._mutation(directory):
+                active = True
+                def guard():
+                    if not active:
+                        raise ValueError("Guard is closed")
+                    self._verify_root(directory)
+                    observed = os.stat("fleet.lock", dir_fd=directory, follow_symlinks=False)
+                    if not os.path.samestat(self._lock_identity, observed):
+                        raise ValueError("Fleet lock changed")
+                    validate()
+                guard()
+                try:
+                    yield guard
+                finally:
+                    active = False
 
     def publish(self, entry: FleetEntry) -> Path:
         document = asdict(entry)
--- original/commands.py
+++ base/commands.py
@@ -135,8 +135,9 @@
 
 
 class StateService:
-    def __init__(self, store: StateStore) -> None:
+    def __init__(self, store: StateStore, *, publication_guard: Callable[[], None] | None = None) -> None:
         self._store = store
+        self._publication_guard = publication_guard
 
     def show(self) -> State:
         return self._store.read()
@@ -161,6 +162,7 @@
         return self._store.transaction(
             guarded,
             expected_revision=expected_revision,
+            publication_guard=self._publication_guard,
         )
 
     def add_task(
```

## Attempt 1

```diff
--- base/commands.py
+++ candidate/commands.py
@@ -162,7 +162,7 @@
         return self._store.transaction(
             guarded,
             expected_revision=expected_revision,
-            publication_guard=self._publication_guard,
+            publication_guard=self._publication_guard if expected_revision is not None else None,
         )
 
     def add_task(
```

Exact test output:

```text
..........................................                               [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-7d30a384-fd4c-45d3-8532-c690c72c885d
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-7d30a384-fd4c-45d3-8532-c690c72c885d'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-622fba31-02f4-4ce2-a822-e4743e1ba8bc
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-622fba31-02f4-4ce2-a822-e4743e1ba8bc'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
42 passed, 2 warnings in 6.54s
```

## Attempt 2

```diff
--- base/commands.py
+++ candidate/commands.py
@@ -449,7 +449,7 @@
         *,
         expected_revision: int | None = None,
     ) -> State:
-        stored_reason = copy.deepcopy(reason)
+        stored_reason = {"site": "supervisor", "detail": "Selected owner pause", "created_at": "2026-08-26T10:00:00Z"}
 
         def mutate(state: State) -> None:
             state["control"]["pause_requested"] = True
```

Exact test output:

```text
..........................................                               [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-548d9b29-b8aa-494b-838b-6d05ae52f9bb
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-548d9b29-b8aa-494b-838b-6d05ae52f9bb'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-93ba7663-f666-4494-9be8-cfbaaeddfba8
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-93ba7663-f666-4494-9be8-cfbaaeddfba8'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
42 passed, 2 warnings in 6.30s
```

## Attempt 3

```diff
--- base/commands.py
+++ candidate/commands.py
@@ -461,7 +461,7 @@
         def mutate(state: State) -> None:
             state["control"]["pause_requested"] = False
             if "paused" not in (state["work"]["phase"], state["work"]["next_phase"]):
-                state["control"]["pause_reason"] = None
+                pass  # Deliberately retain the obsolete pause reason
 
         return self._transaction(mutate, expected_revision=expected_revision)
 
```

Exact test output:

```text
..........................................                               [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-bea3c773-4373-4b25-8363-fd66d3c76a40
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-bea3c773-4373-4b25-8363-fd66d3c76a40'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-aa4c16ad-3648-45c4-b6b6-34c75ec3abc6
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-aa4c16ad-3648-45c4-b6b6-34c75ec3abc6'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
42 passed, 2 warnings in 6.31s
```

## Attempt 4

```diff
--- base/registry.py
+++ candidate/registry.py
@@ -303,7 +303,7 @@
                 active = True
                 def guard():
                     if not active:
-                        raise ValueError("Guard is closed")
+                        return  # Deliberately accept a guard after its lock was released
                     self._verify_root(directory)
                     observed = os.stat("fleet.lock", dir_fd=directory, follow_symlinks=False)
                     if not os.path.samestat(self._lock_identity, observed):
```

Exact test output:

```text
..........................................                               [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-dd885183-45ae-4381-8911-f005e5683484
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-dd885183-45ae-4381-8911-f005e5683484'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-f803361b-fe58-4f5d-998e-24259ce2e037
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-f803361b-fe58-4f5d-998e-24259ce2e037'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
42 passed, 2 warnings in 6.37s
```

## Attempt 5

```diff
--- base/commands.py
+++ candidate/commands.py
@@ -159,11 +159,13 @@
             _require_recovery_idle(state)
             return mutator(state)
 
-        return self._store.transaction(
+        result = self._store.transaction(
             guarded,
             expected_revision=expected_revision,
             publication_guard=self._publication_guard,
         )
+        self._publication_guard = None  # Guard only the first successful operation
+        return result
 
     def add_task(
         self,
```

Exact test output:

```text
..........................................                               [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-73a84086-0d05-4673-b27c-da87e6b190a0
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-73a84086-0d05-4673-b27c-da87e6b190a0'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-95cab4f9-12d1-4109-ac01-11307a7a8866
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-95cab4f9-12d1-4109-ac01-11307a7a8866'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
42 passed, 2 warnings in 6.26s
```

## Attempt 6

```diff
--- base/store.py
+++ candidate/store.py
@@ -336,7 +336,7 @@
                 directory_boundary=DurabilityBoundary.STATE_DIR_FSYNCED,
                 publication_guard=publication_guard,
             )
-        except BaseException:
+        except Exception:
             if (
                 self._snapshot(self._path) != old_state
                 or self._snapshot(self._backup_path) != old_backup
```

Exact test output:

```text
..........................................                               [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-6bbbbb89-8a9a-412e-af19-7c49e88dbef8
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-6bbbbb89-8a9a-412e-af19-7c49e88dbef8'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-481111fe-1836-48d0-8cd6-0d8e46b6776d
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-481111fe-1836-48d0-8cd6-0d8e46b6776d'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
42 passed, 2 warnings in 6.44s
```

## Attempt 7

```diff
--- base/store.py
+++ candidate/store.py
@@ -337,6 +337,8 @@
                 publication_guard=publication_guard,
             )
         except BaseException:
+            if old_backup is None:
+                raise  # Leave the partially published pair when no old backup existed
             if (
                 self._snapshot(self._path) != old_state
                 or self._snapshot(self._backup_path) != old_backup
```

Exact test output:

```text
..........................................                               [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-f308dd64-cc7e-40d8-bfbf-f2e10d371582
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-f308dd64-cc7e-40d8-bfbf-f2e10d371582'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-fba55864-98e3-4dc6-897e-09bc39ba0b64
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-fba55864-98e3-4dc6-897e-09bc39ba0b64'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
42 passed, 2 warnings in 6.51s
```

## Attempt 8

```diff
--- base/commands.py
+++ candidate/commands.py
@@ -162,7 +162,8 @@
         return self._store.transaction(
             guarded,
             expected_revision=expected_revision,
-            publication_guard=self._publication_guard,
+            publication_guard=(self._publication_guard
+                if self._store.read()["batch"]["status"] == "running" else None),
         )
 
     def add_task(
```

Exact test output:

```text
..........................................                               [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-fe4f0f23-0e61-4297-b232-4acaab14bf50
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-fe4f0f23-0e61-4297-b232-4acaab14bf50'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-1ef680c9-0694-45a2-b268-f06bd105ff30
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-1ef680c9-0694-45a2-b268-f06bd105ff30'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
42 passed, 2 warnings in 6.18s
```

## Proven result

Eight independent wrong implementations each passed all 42 supplied tests (each exit 0). Stop: eight-success maximum reached; no test-rejected candidates. One sandbox infrastructure failure preceded the first successful execution. Each candidate starts from the shared API implementation above, not the preceding wrong candidate. Full unique logs and runner metadata are retained as `r4-devon-attempt-{1..8}.log[.json]`. Pytest emitted two existing temporary-directory cleanup warnings on each run.

Weak points:

1. test_guard_rejection_at_every_durable_boundary_restores_exact_bytes - omitting expected_revision disables the service guard entirely - invoke both operations without expected_revision using a rejecting guard and assert rejection plus identical state/backup bytes.
2. test_control_change_commits_once_and_preserves_unrelated_state - request_pause ignores its reason and hardcodes the one fixture notice - parameterize None and distinct notices and assert pause_reason equals each exact input.
3. test_control_change_commits_once_and_preserves_unrelated_state / test_guarded_control_result_matches_ordinary_service - resume leaves an obsolete pause_reason, and the ordinary-service oracle has the same defect - explicitly assert pause_reason is None for the non-paused phases in the fixture.
4. test_ownership_mutation_waits_and_is_released_on_context_exit - the yielded publication guard silently succeeds after its context has released the fleet lock - retain it, exit the context, pass it to StateService and assert failure with unchanged durable bytes.
5. test_revision_conflict_preserves_bytes_and_allows_later_guarded_commit - StateService discards its guard after its first successful mutation - reuse one service for a successful commit, invalidate its guard, then assert the second mutation fails without publishing bytes.
6. test_guard_rejection_at_every_durable_boundary_restores_exact_bytes - rollback catches Exception only, leaving partial publication on KeyboardInterrupt/SystemExit - parameterize BaseException subclasses at durable boundaries and assert exact restoration and temporary-file cleanup.
7. test_guard_rejection_at_every_durable_boundary_restores_exact_bytes - rollback is skipped whenever the backup was absent before publication - start with initialized state and no backup, reject at each boundary, assert original state bytes and absent backup afterward.
8. test_guard_rejection_at_every_durable_boundary_restores_exact_bytes - service ignores publication_guard for every batch status except running - exercise a schema-valid idle initial state with a rejecting guard and assert rejection and no durable changes.

## Restoration

All three production files restored byte-for-byte from pre-dispatch backups. No tests, workflow state, commits or other production paths changed. Candidate helper and three temporary candidate-base files overwritten with the mandated placeholder line; reports, attempt logs and pre-dispatch backups retained.

Verified SHA-256:

```text
src/ovcaq/runtime/registry.py: 60185c9807b27436ca3c93e248cd04a8a6f8327bcc7823553e0d81289627b2c6
src/ovcaq/state/commands.py: 4302433cac118c798d47cd74037293697040fc2f91c341411d400c546b0b2df2
src/ovcaq/state/store.py: b7ade1f13f7c4ef8cb65ce07ac5c228e235ab293ae9e82562e7d449e721307e7
```

abort_reason: null
