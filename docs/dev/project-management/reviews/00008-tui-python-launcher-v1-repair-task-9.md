# PRD 00008 recovery task 9

Both actual Textual apps persist real user theme changes; mount loading does not overwrite missing/bad files. Theme resolution reuses the shared trusted anchor helper with identical unset/empty/relative/alias semantics. Application-owned descendants are opened with no-follow directory handles; bounded allowlisted reads and private atomic writes preserve neighboring files and detect observed concurrent descendant replacements. Temporary cleanup uses the held directory. A confirmed Pat MEDIUM corrected full-stat comparison so access-time-only changes do not reject saves; absence/presence, device/inode and nanosecond mtime remain checked.

Basef1004f349f08c5752098d54b9ec30fc099c663e6. Initial tests ed3b9a6, strengthened tests a87a7886f7f12bd002dc7ad14146e5d0096c90b9, implementation c84709101ddeb68705bad66f39caddb268df216f. Pat regression tests207b7ec628918eab29d7221a995d7123e6121194; finalba3092bcf66e9484725fda4994767a4b1cc831a2.

Micro mechanically eligible at claim, but partial implementation hit30net lines/3files; exact task-owned changes restored to clean claim snapshot. Full pipeline followed. Tess0d86eb0c20,358bytes; Devoncd58916f23,143; strengthen cdbc41f2 33,498; Ivan04a649c0 26,677; deslop4f8a3d7e12,451; Pat1e74367d34,650; regression Tess047bf57e9,479; correctionIvanae16458331,674; Patdeltadc07b8da8,348. Native agents actually gpt-6-astra/logicalopus, fresh isolated contexts. Gemini required UI probe failed exit3 nested guard, no backend ran; no guard bypass. Pat tool-free guarded Claude wrapper used approved network, session5a68dddc-dd25-4e18-b342-2dd5444b25dd, actualclaude-sonnet-5-5. No completion review in this build session.

Tess quality: behavior names, real outputs/effects, relevant edge/race cases, no tautologies; computed shapes clean, style clean. Devon proved8 independent wrong implementations each34passed; Tess strengthened7 and explicitly classified5 in-contract (historical warning clearing unspecified). Production restored and canonical test bytes independently checked. No second Devon. Main red11failed28passed; initial committed green39passed. Pat closedF21/F22 but found concurrent read atime false rejection. Added focused filesystem-boundary regression, main red1failed39passed, correction final40passed2 pre-existing pytest cleanup warnings,exit0,1.37s. The atime test performs a real read and deterministic atime-only utime to avoid relying on filesystem read-atime policy; preserved inode/content/mtime checks prove the relevant change. Initial blocked uv-cache attempts were retained and followed by isolated-cache or approved main runs; never reported green without execution.

Self-deslop ran full catalog and returned noop. Style/split clean before Pat and after correction; no reflow threshold hit. LOW private helper import accepted as reuse of the existing shared contract; duplicated5-line app watchers retained; save_theme nesting retained because scoped code is within size limits. At phase-end formatting, recheck save_theme (currently46 computed lines) and task7 _run; wrapping long calls may expand spans. Old tests/tui/test_app.py::test_symlinked_config_component_is_rejected contradicts accepted trusted-anchor semantics; reconcile actual full-suite failure without reintroducing discardedF07. No claim is made that this per-task suite is the full-project gate. ASSUMPTIONS: none.

## Raw initial Pat review

CLOSURE | resolved | F21 🟡 `save_theme` has no production caller; only tests call it. | Both `FleetApp.watch_theme` and `ProjectApp.watch_theme` call `save_theme(name)` once `_theme_ready` is set. `test_all_real_theme_changes_persist_and_load_in_a_later_app` changes the theme 5 times in each app and reloads it in a later app.

CLOSURE | resolved | F22 `_linked_dirs` rejects a symlinked `XDG_CONFIG_HOME`; `_config_root` re-implements XDG resolution and treats an empty value differently from `config.py`. | `_linked_dirs` is deleted. `_config_root` now calls the shared `_trusted_path`, and `_theme_directory` opens the anchor itself with `O_NOFOLLOW` after resolution. The `alias`, `home-alias`, `empty` and `relative` selections in `test_theme_storage_uses_shared_trusted_xdg_anchor_semantics` pass. I could not check from this prompt that the empty-value behavior matches `config.py`. The tests pin it to the current directory.

MEDIUM | src/ovcaq/tui/app.py:~230 | `save_theme` compares the full `os.stat_result` (`current != before`) to detect replacement. That tuple includes `st_atime`, so another process or app reading `theme` between the two stats (for example a second ovcaq starting `load_theme`) changes it. The save then fails with a false theme gap and the choice is not persisted. The tests only replace the file and never read it, so they miss this. | Compare identity and content stamps only: `current is None or before is None` must match, and otherwise `os.path.samestat(current, before)` and `current.st_mtime_ns == before.st_mtime_ns`. Add a test that reads the file between the two stats.

LOW | src/ovcaq/tui/app.py:19 | The module imports the private `_trusted_path` from `ovcaq.paths`, which couples it to an underscore-named helper across modules. | Expose it publicly (`trusted_path`) or add a public config-root helper in `paths.py` or `config.py`, and use that.

LOW | src/ovcaq/tui/app.py:~268,~357 | The two `watch_theme` bodies and the `_theme_ready` guard are duplicated across `FleetApp` and `ProjectApp`. They differ only in how the gap is shown. | Move the save-and-report step into one shared mixin or helper that takes a gap-reporting callable.

LOW | src/ovcaq/tui/app.py:~222 | `save_theme` is a single function of about 40 lines with 4 levels of nesting (`try`, `with`, `try`, `finally`/`try`). | Move the temp-write and replace step into a small helper `_replace_theme(anchor, directory, name)` to flatten it.


## Raw Pat delta review

CLOSURE | resolved | MEDIUM `save_theme` compares the full `os.stat_result` (`current != before`), so an atime-only change from a concurrent reader causes a false theme gap | The delta replaces `current != before` with a check on presence, `os.path.samestat` (device and inode) and `st_mtime_ns`, so atime no longer takes part. The new test `test_concurrent_reader_atime_update_does_not_prevent_saving_a_new_theme` reads the file and bumps only atime between the two stats, and expects `ThemeResult("gruvbox", None)`. Replacement is still caught: a new inode fails `samestat`, and an in-place edit changes mtime. The earlier replacement tests still pass (40 passed).

LOW | src/ovcaq/tui/app.py:~230 | The replacement check is a 3-level boolean expression that repeats `current is not None and before is not None`. | Pull it into a small helper such as `_same_file(before, current)`. It would return `before is None and current is None` when either is None, and otherwise `samestat(...) and a.st_mtime_ns == b.st_mtime_ns`. Behavior is identical and the call site becomes `if not _same_file(before, current)`.


## Final verification

........................................                                 [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-7c2a3a35-2bdf-4816-94d7-a0a0ee41ce91
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-7c2a3a35-2bdf-4816-94d7-a0a0ee41ce91'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-262dd981-1ee2-4fba-8afa-3469c9acc602
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-262dd981-1ee2-4fba-8afa-3469c9acc602'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
40 passed, 2 warnings in 1.37s

{
  "command": [
    "uv",
    "run",
    "pytest",
    "-q",
    "--tb=line",
    "tests/tui/test_theme_persistence.py"
  ],
  "exit": 0,
  "timeout_seconds": 300
}

## Initial Tess

# Recovery task 9 — requirements-only Tess report

Created `tests/tui/test_theme_persistence.py`: 11 test functions, 34 parameterized cases. No implementation, existing tests, state, or git writes. Read the complete assembled prompt and only authorized examples/helper. No production bodies read.

Verification: `UV_CACHE_DIR=/private/tmp/ovcaq-r9-tess-uv-cache uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/tui/test_theme_persistence.py` through the 300-second bounded helper.

Result: **10 failed, 24 passed, 2 warnings in 0.83s; exit 1**. Log: `docs/dev/tmp/r9-tess-pytest-isolated-cache.log`. Subsequent edits changed formatting only; no second suite run.

Initial launch used the default uv cache and exited 2 before collecting tests because sandbox access to `/Users/bob/.cache/uv/sdists-v9/.git` was denied. Retried with an isolated temporary cache. Both warnings in the executed suite concern pytest cleanup of pre-existing temporary directories.

Failures:

- `test_real_theme_changes_persist_twice_and_load_in_a_later_app[fleet]` and `[project]`: real `app.theme = "nord"` leaves saved theme `gruvbox`.
- `test_failed_user_theme_save_is_visible_and_app_can_still_detach[fleet]` and `[project]`: actual rendered app does not show the save failure gap after a user theme change.
- `test_theme_storage_uses_shared_trusted_xdg_anchor_semantics[empty]`: selects home default instead of current working directory.
- The same test `[alias]` and `[home-alias]`: `theme_path()` retains alias instead of resolving the trusted selected anchor. These cases stop at the path assertion before round-trip checks.
- `test_read_never_follows_a_descendant_replaced_at_the_open_boundary[directory]`: returns the substituted external theme (`gruvbox`), rather than rejecting or safely reading the original (`nord`).
- `test_save_preserves_concurrent_replacement_evidence_and_reports_a_gap[directory]` and `[file]`: reports successful save despite concurrent replacement. These cases stop at the gap assertion before subsequent evidence-preservation assertions.

Passing coverage includes invalid/unavailable mount preservation and visible gaps in both real apps, unset/relative XDG paths, five allowlisted themes with private atomic replacement, invalid-name preservation, invalid/oversized/undecodable content, directory/file symlink rejection, directory/FIFO nonregular files, and file-symlink substitution at the read boundary.

Race tests replace real filesystem descendants immediately before `os.open` reads the theme or opens a writable file; they intercept only this external filesystem boundary. They assert the injection actually occurred, preserve external evidence, and use no private application helpers. Safe reads from an already held original directory are accepted. App tests use real Textual `run_test` and actual theme property changes; no watcher or persistence stubs.

ASSUMPTIONS: none


## Strengthening dispositions

# Task 9 adversarial strengthening

Targeted changes only in `tests/tui/test_theme_persistence.py`. Existing sound tests preserved; no production, state, history, or git access. No second adversarial pass or candidate application. Supplied candidate examples were assessed against the original contract.

1. strengthened: `test_all_real_theme_changes_persist_and_load_in_a_later_app` makes five successive real reactive-property changes in each app, checks disk and load results after each, and mounts a later app with the final theme. A watcher limited to two saves fails on the third change.
2. strengthened: the same test drives all five allowed themes, including `textual-light`, through each actual mounted app. Every assignment differs from the previous theme.
3. strengthened: `test_mount_preserves_bad_file_and_displays_a_nonfatal_safe_gap` now asserts `app.theme == "textual-dark"` for both invalid and unavailable preferences in both apps, retaining content/inode preservation and rendered-gap checks.
4. strengthened: `test_mount_without_a_preference_uses_dark_without_writing` mounts both apps without a preference, asserts the actual default theme, and checks no preference appears during mount or after detach.
5. in-contract: the supplied contract requires a visible, nonfatal failure but specifies neither notification lifetime nor removal of historical failure messages after recovery. An app that successfully persists later changes while retaining the previous error notice satisfies those stated requirements. Requiring the previous gap to disappear would invent a notification-clearing contract. The existing actual-screen failure and successful-detach assertions remain unchanged.
6. strengthened: `test_allowlisted_save_is_private_atomic_and_leaves_no_temporary_files` seeds `config.toml` and an unrelated sibling before the initial save. It verifies both contents and inodes after initial creation and after each allowlisted atomic replacement, retaining the privacy, old-open-file, and no-temporary-file checks.
7. strengthened: `test_theme_storage_uses_shared_trusted_xdg_anchor_semantics` loads a saved nondefault preference, unlinks it, then requires `ThemeResult("textual-dark", None)` without recreating the preference.
8. strengthened: the same anchor test now includes absolute, relative, and explicitly selected symlink anchors containing spaces, checking canonical path, save/load round trip, on-disk content, and deletion/default behavior.

## Verification

One permitted narrow run against the restored original production files:

`UV_CACHE_DIR=/tmp/ovcaq-r9-uv mise exec -- python3 docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/r9-tess-strengthen-pytest.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/tui/test_theme_persistence.py`

Result: **11 failed, 28 passed, 2 warnings in 0.87s**, exit **1**, 39 cases total. Full output: `docs/dev/tmp/r9-tess-strengthen-pytest.log`; command/exit metadata: adjacent `.log.json`. No expectations were weakened to accommodate original production failures.

Failures:

- Actual theme changes do not persist: fleet and project (2).
- Failed user saves do not show the required visible gap: fleet and project (2).
- Shared anchor semantics disagree for empty, alias, home-alias, and alias-space selections (4).
- Concurrent parent replacement allows reading the substituted outside theme (1).
- Concurrent directory/file replacements incorrectly report successful saves (2).

The two warnings are pytest temporary-directory cleanup warnings (`Directory not empty`). They did not prevent execution. AST inspection confirmed 445 file lines and a maximum function span of 36 lines, below both limits. No helper file was needed. Total input remained below the 100K-token cap.

ASSUMPTIONS: none


## Regression Tess

# Task 9 access-time regression

Dispatch: `047bf57e`.

Added one behavior test to `tests/tui/test_theme_persistence.py`:
`test_concurrent_reader_atime_update_does_not_prevent_saving_a_new_theme`.
Existing tests and expectations are unchanged. No production, state, or git
changes were made, and no production bodies were read.

At the external `os.open` write boundary, the test performs a real read and a
deterministic access-time update, preserving modification time. It asserts the
injected event occurred and preserved device, inode, size, mode, and old content.
The new allowlisted theme must save successfully through atomic replacement;
the still-open prior file retains its identity and content, the new preference
loads, and no temporary files remain.

One bounded test invocation was attempted:

```text
mise exec -- python3 docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/r9-tess-atime-test-047bf57e.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/tui/test_theme_persistence.py
```

Exit code: **2**. Collection never started: **0 tests executed**; pytest emitted
no pass/fail/skip counts. uv could not initialize its cache because opening
`/Users/bob/.cache/uv/sdists-v9/.git` was denied by the sandbox. The single-run
restriction was preserved; this agent has not confirmed the expected red result.
Exact output and command metadata are saved in
`docs/dev/tmp/r9-tess-atime-test-047bf57e.log` and its `.log.json` sibling.

ASSUMPTIONS: none


## Implementation

# Ivan Task 9 implementation report

Implemented theme persistence in `src/ovcaq/tui/app.py` only.

- Both apps persist real theme changes through public Textual watchers, with initialization guarded against writes.
- Startup and save failures display the existing safe gap without interrupting detach or touching process controls.
- Theme paths reuse `_trusted_path` and the shared XDG selection semantics, including empty, relative, space-containing and aliased anchors.
- Reads, atomic writes and temporary cleanup use anchored no-follow directory handles. Save checks preserve descendant replacements observed during the write boundary.
- Tests, workflow state, changelog and git were not modified. No new production modules or dependencies. No full suite or lint was run.

Verification command (300-second bound, isolated UV cache):

```text
UV_CACHE_DIR=/tmp/ovcaq-r9-uv-cache .venv/bin/python docs/dev/tmp/run_bounded.py 300 /tmp/r9-ivan-tests.txt uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/tui/test_theme_persistence.py
```

Exact test output:

```text
.......................................                                  [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-be61ed24-6348-445c-909f-77dcd6fb5eb4
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-be61ed24-6348-445c-909f-77dcd6fb5eb4'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-16db41f3-ed33-4678-a616-12ec668d718c
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-16db41f3-ed33-4678-a616-12ec668d718c'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
39 passed, 2 warnings in 1.40s
```

Exit code: 0. Two pytest temporary-directory cleanup warnings; no failing tests.

Source size inspection (no lint):

```text
src/ovcaq/tui/app.py: 556 lines
_config_root: 4 lines
theme_path: 2 lines
_theme_directory: 21 lines
load_theme: 22 lines
save_theme: 39 lines
watch_theme: 5 lines
watch_theme: 5 lines
```

ASSUMPTIONS: none

FILES_TOUCHED:
src/ovcaq/tui/app.py
docs/dev/tmp/r9-ivan-report.md


## Correction

# Task 9 Pat MEDIUM correction

Changed only save_theme comparison in src/ovcaq/tui/app.py. Compare absence/presence, device/inode identity via os.path.samestat, and nanosecond mtime. Access-time changes no longer reject a valid save. Descriptor-relative publication and cleanup remain intact. No LOW refactors, tests, changelog, state, or git edits.

Verification command (300-second bound):
`UV_CACHE_DIR=/tmp/r9-ivan-atime-uv-cache python3 docs/dev/tmp/run_bounded.py 300 /tmp/r9-ivan-atime-pytest-isolated.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/tui/test_theme_persistence.py`

Exact output:
```text
........................................                                 [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ae184def-6d17-48f2-a775-f67e999c21e7
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ae184def-6d17-48f2-a775-f67e999c21e7'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-0c9c507d-c6b3-41af-a95a-9bcc67a351f0
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-0c9c507d-c6b3-41af-a95a-9bcc67a351f0'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
40 passed, 2 warnings in 1.31s
```
Exit: 0. Tests executed once: 40 passed. Two pytest cleanup warnings are preserved above.

Initial launch failed before pytest started because the default uv cache was sandbox-inaccessible. Exact output:
```text
error: Failed to initialize cache at `/Users/bob/.cache/uv`
  Caused by: failed to open file `/Users/bob/.cache/uv/sdists-v9/.git`: Operation not permitted (os error 1)
```
Exit: 2. Retried using an isolated cache as authorized.

Size check: save_theme 46 lines; module 563 lines.

ASSUMPTIONS: none

FILES_TOUCHED:
src/ovcaq/tui/app.py
docs/dev/tmp/r9-ivan-atime-report.md

Verification/inspection artifacts outside the repo: /tmp/r9-ivan-atime-{interface,app,size,pytest,pytest-isolated,report-write}.log and companion .log.json files; isolated uv cache at /tmp/r9-ivan-atime-uv-cache.


## Self-deslop

no slop found

Reviewed the complete dispatch prompt and all catalog entries against commit c84709101ddeb68705bad66f39caddb268df216f, scoped to CHANGELOG.md and src/ovcaq/tui/app.py. Read the complete named theme persistence test file.

Every added construct traces to the repair contract or existing behavior: trusted XDG resolution, descriptor-relative no-follow access, bounded regular-file reads, private atomic writes, concurrent replacement checks, cleanup, and guarded persistence with visible nonfatal failures in both apps. The shared context manager has two consumers; the two short watchers provide view-specific error presentation. No speculative configuration, dependencies, comments, debug artifacts, or removable indirection appeared.

No source/test/state changes and no commit. No removals were attempted, so no additional test run was required; the coordinator supplied the independent 39-test pass. Inspection runner calls used a 60-second bound and exited successfully. Total input remained well below 100K tokens.


## Devon raw report

# Task 9 adversarial test report

Verdict: BROKEN. Eight independent wrong implementations each passed all 34 cases. No test source was modified. Only app.py was temporarily changed; all three supplied production backup comparisons now match byte-for-byte. No git or state writes, network, or subagents. Input remained well below 100K tokens; no abort.

Each `r9-devon-cN.diff` is a standalone unified patch against the supplied original app.py. It includes the complete temporary baseline (trusted XDG anchors, directory-relative theme I/O and actual Textual theme watchers) plus that candidate’s single wrong behavior. Apply one patch at a time to the restored original to reproduce. The baseline is a test harness implementation, not a production recommendation. No requirements, task descriptions, history or sibling tests were read.

The initial candidate 1 invocation could not initialize the default UV cache because the sandbox denied it; that log is `r9-devon-c1.log` (exit 2, pytest never started). All actual test invocations used `UV_CACHE_DIR=/tmp/ovcaq-r9-uv` and the supplied 300-second runner. There were no failed test candidates. Each candidate was tested exactly once. Two nonfatal pytest cleanup warnings occurred per passing run and are retained in full below.

Weak points:

1. `test_real_theme_changes_persist_twice_and_load_in_a_later_app` - Both app watchers stop saving after two changes - Change the theme three or more times in each app; assert disk and a newly mounted app match the final choice.
2. `test_real_theme_changes_persist_twice_and_load_in_a_later_app` - Both app watchers silently ignore textual-light even though save_theme supports it - Drive all five allowed themes through each real App.theme property and assert each persists.
3. `test_mount_preserves_bad_file_and_displays_a_nonfatal_safe_gap` - Invalid/unreadable configuration displays gruvbox instead of the default - Assert app.theme == "textual-dark" after invalid and unavailable mounts.
4. `test_theme_storage_uses_shared_trusted_xdg_anchor_semantics` - A missing preference makes the mounted UI textual-light while the helper reports textual-dark - Mount both applications without a preference and assert the actual theme is textual-dark and no preference is written.
5. `test_failed_user_theme_save_is_visible_and_app_can_still_detach` - An error banner survives forever after a later successful theme save - Repair the file after a failed save, choose another theme, assert persistence and absence of the previous gap from the screen.
6. `test_allowlisted_save_is_private_atomic_and_leaves_no_temporary_files` - Every successful save deletes the neighboring config.toml - Seed config.toml and another unrelated sibling; assert their bytes/inodes remain unchanged after successful saves.
7. `test_theme_storage_uses_shared_trusted_xdg_anchor_semantics` - The loader returns a cached previous theme after the preference file has been removed - Load a saved nondefault theme, unlink the preference, then assert load_theme() == ThemeResult("textual-dark", None).
8. `test_theme_storage_uses_shared_trusted_xdg_anchor_semantics` - Load/save reject valid configuration paths containing spaces - Repeat round-trip checks under absolute, relative and symlinked XDG anchors containing spaces.

Wrong implementations and passing output:

## Candidate 1

Both app watchers stop saving after two changes. Full runnable patch: [r9-devon-c1.diff](r9-devon-c1.diff). Exact runner output: [r9-devon-c1-retry.log](r9-devon-c1-retry.log); exit metadata: [r9-devon-c1-retry.log.json](r9-devon-c1-retry.log.json).

```python
if count >= 2: return
```

```text
..................................                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-0ff20bff-a2d2-49c2-aff8-35a71e106fa9
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-0ff20bff-a2d2-49c2-aff8-35a71e106fa9'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-0727beb8-ffed-40e9-990a-c3d48a133108
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-0727beb8-ffed-40e9-990a-c3d48a133108'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 2 warnings in 1.21s

```

## Candidate 2

Both app watchers silently ignore textual-light even though save_theme supports it. Full runnable patch: [r9-devon-c2.diff](r9-devon-c2.diff). Exact runner output: [r9-devon-c2.log](r9-devon-c2.log); exit metadata: [r9-devon-c2.log.json](r9-devon-c2.log.json).

```python
if name == "textual-light": return
```

```text
..................................                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-43d725ad-3526-4850-b1eb-714a5bf814eb
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-43d725ad-3526-4850-b1eb-714a5bf814eb'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-fc043f2b-8d32-4eb1-9265-a6f29586256e
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-fc043f2b-8d32-4eb1-9265-a6f29586256e'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 2 warnings in 1.16s

```

## Candidate 3

Invalid/unreadable configuration displays gruvbox instead of the default. Full runnable patch: [r9-devon-c3.diff](r9-devon-c3.diff). Exact runner output: [r9-devon-c3.log](r9-devon-c3.log); exit metadata: [r9-devon-c3.log.json](r9-devon-c3.log.json).

```python
self.theme = result.name or "gruvbox"
```

```text
..................................                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-a10c4eb9-ef9b-4ee9-8966-f8e0c48563f8
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-a10c4eb9-ef9b-4ee9-8966-f8e0c48563f8'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c84e3be1-9c00-4a52-b4d7-fbb2ab7f8832
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c84e3be1-9c00-4a52-b4d7-fbb2ab7f8832'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 2 warnings in 1.17s

```

## Candidate 4

A missing preference makes the mounted UI textual-light while the helper reports textual-dark. Full runnable patch: [r9-devon-c4.diff](r9-devon-c4.diff). Exact runner output: [r9-devon-c4.log](r9-devon-c4.log); exit metadata: [r9-devon-c4.log.json](r9-devon-c4.log.json).

```python
self.theme = "textual-light" if not theme_path().exists() else result.name or _THEMES[0]
```

```text
..................................                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-a73d67bb-6bb1-49fb-bb8b-cea92e22bf58
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-a73d67bb-6bb1-49fb-bb8b-cea92e22bf58'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-cdbf8c1a-80d2-498f-b027-b072a1870664
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-cdbf8c1a-80d2-498f-b027-b072a1870664'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 2 warnings in 1.01s

```

## Candidate 5

An error banner survives forever after a later successful theme save. Full runnable patch: [r9-devon-c5.diff](r9-devon-c5.diff). Exact runner output: [r9-devon-c5.log](r9-devon-c5.log); exit metadata: [r9-devon-c5.log.json](r9-devon-c5.log.json).

```python
if result.gap: self._notify_error(result.gap)  # never clear after recovery
```

```text
..................................                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-9a77c4c1-818d-4375-952f-70a0164c420f
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-9a77c4c1-818d-4375-952f-70a0164c420f'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-8c899c14-8295-447a-8f2d-45e362acf2b9
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-8c899c14-8295-447a-8f2d-45e362acf2b9'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 2 warnings in 1.05s

```

## Candidate 6

Every successful save deletes the neighboring config.toml. Full runnable patch: [r9-devon-c6.diff](r9-devon-c6.diff). Exact runner output: [r9-devon-c6.log](r9-devon-c6.log); exit metadata: [r9-devon-c6.log.json](r9-devon-c6.log.json).

```python
(path.parent / "config.toml").unlink(missing_ok=True)
```

```text
..................................                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-9ec61cfc-c32d-4e55-9cda-39e369470abe
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-9ec61cfc-c32d-4e55-9cda-39e369470abe'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-e1108ecc-62e2-4a5d-9e2f-3cd6e1201428
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-e1108ecc-62e2-4a5d-9e2f-3cd6e1201428'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 2 warnings in 1.03s

```

## Candidate 7

The loader returns a cached previous theme after the preference file has been removed. Full runnable patch: [r9-devon-c7.diff](r9-devon-c7.diff). Exact runner output: [r9-devon-c7.log](r9-devon-c7.log); exit metadata: [r9-devon-c7.log.json](r9-devon-c7.log.json).

```python
except FileNotFoundError: return ThemeResult(_last_theme.get(path, _THEMES[0]), None)
```

```text
..................................                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-42aa235e-bfe1-4ee7-bea8-d9f38f873f93
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-42aa235e-bfe1-4ee7-bea8-d9f38f873f93'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-94e261eb-b1b2-4e5c-a760-84764abfd8c6
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-94e261eb-b1b2-4e5c-a760-84764abfd8c6'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 2 warnings in 1.06s

```

## Candidate 8

Load/save reject valid configuration paths containing spaces. Full runnable patch: [r9-devon-c8.diff](r9-devon-c8.diff). Exact runner output: [r9-devon-c8.log](r9-devon-c8.log); exit metadata: [r9-devon-c8.log.json](r9-devon-c8.log.json).

```python
if " " in str(path): return ThemeResult(None, _THEME_GAP)
```

```text
..................................                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-d73cb6b8-9c44-422f-a25a-9053ae180430
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-d73cb6b8-9c44-422f-a25a-9053ae180430'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-b14c54ff-6815-4a31-ae6b-a6d3624d08c6
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-b14c54ff-6815-4a31-ae6b-a6d3624d08c6'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 2 warnings in 1.01s

```

Restoration SHA-256 verification:

```json
{
  "/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/app.py": "bfdbbadcdb46ea9fd0340921058e959bb3bec390900c22c178832d62e1acbefa",
  "/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/config.py": "c48cc39ddd0ee8e075b38d2a5dd8c4750efc210c2ced8c08c6b181e4fdc8dc84",
  "/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/paths.py": "3bb2bdd7da9dc838e19751fb95c79aa072961849624978f9ab91bfb3a5cfb990"
}
```

Cleanup: temporary `r9-devon-baseline.txt` and `r9-devon-c2.candidate` through `r9-devon-c8.candidate` were overwritten with the requested placeholder. Runnable diffs, exact output and metadata were preserved as required. Existing backup artifacts were preserved.


## Complete adversarial candidate 1

```diff
--- a/src/ovcaq/tui/app.py
+++ b/src/ovcaq/tui/app.py
@@ -141,64 +141,87 @@
 
 
 def _config_root() -> Path:
-    configured = os.environ.get("XDG_CONFIG_HOME")
-    base = Path(configured) if configured else Path.home() / ".config"
-    return base if base.is_absolute() else Path.cwd() / base
+    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser().resolve()
 
 
 def theme_path() -> Path:
     return _config_root() / "ovcaq" / "theme"
 
 
-def _linked_dirs() -> bool:
-    path = theme_path()
-    return path.parent.is_symlink() or path.parent.parent.is_symlink()
+def _identity(path: Path) -> tuple[int, int]:
+    info = path.lstat()
+    return info.st_dev, info.st_ino
 
 
 def load_theme() -> ThemeResult:
     path = theme_path()
-    if _linked_dirs():
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
+    directory = fd = None
+    try:
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        fd = os.open("theme", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
+        info = os.fstat(fd)
+        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o444:
+            return ThemeResult(None, _THEME_GAP)
+        data = os.read(fd, _THEME_LIMIT + 1)
+        name = data.decode("utf-8").strip()
+        if len(data) > _THEME_LIMIT or name not in _THEMES:
+            return ThemeResult(None, _THEME_GAP)
+        return ThemeResult(name, None)
     except FileNotFoundError:
         return ThemeResult(_THEMES[0], None)
-    except OSError:
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        if not stat.S_ISREG(os.fstat(fd).st_mode):
-            return ThemeResult(None, _THEME_GAP)
-        data = os.read(fd, _THEME_LIMIT + 1)
-    except OSError:
+    except (OSError, UnicodeError):
         return ThemeResult(None, _THEME_GAP)
     finally:
-        os.close(fd)
-    name = data.decode("utf-8", errors="replace").strip()
-    if len(data) > _THEME_LIMIT or name not in _THEMES:
-        return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+        if fd is not None:
+            os.close(fd)
+        if directory is not None:
+            os.close(directory)
 
 
 def save_theme(name: str) -> ThemeResult:
     if name not in _THEMES:
         return ThemeResult(None, _THEME_GAP)
     path = theme_path()
-    try:
-        if _linked_dirs() or path.is_symlink():
+    directory = fd = None
+    temp = None
+    try:
+        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        info = os.fstat(directory)
+        parent_identity = info.st_dev, info.st_ino
+        os.fchmod(directory, 0o700)
+        try:
+            original = _identity(path)
+            if not stat.S_ISREG(path.lstat().st_mode):
+                return ThemeResult(None, _THEME_GAP)
+        except FileNotFoundError:
+            original = None
+        temp = ".theme-" + os.urandom(10).hex()
+        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
+        os.write(fd, (name + "\n").encode())
+        os.close(fd)
+        fd = None
+        try:
+            current = _identity(path)
+        except FileNotFoundError:
+            current = None
+        if _identity(path.parent) != parent_identity or current != original:
             return ThemeResult(None, _THEME_GAP)
-        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
-        path.parent.chmod(0o700)
-        fd, temp = tempfile.mkstemp(dir=path.parent)
-        try:
-            with os.fdopen(fd, "w") as handle:
-                handle.write(f"{name}\n")
-            os.replace(temp, path)
-        except BaseException:
-            Path(temp).unlink(missing_ok=True)
-            raise
+        os.replace(temp, "theme", src_dir_fd=directory, dst_dir_fd=directory)
+        temp = None
+        return ThemeResult(name, None)
     except OSError:
         return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+    finally:
+        if fd is not None:
+            os.close(fd)
+        if temp is not None and directory is not None:
+            try:
+                os.unlink(temp, dir_fd=directory)
+            except FileNotFoundError:
+                pass
+        if directory is not None:
+            os.close(directory)
 
 
 # ponytail: Textual is optional at import time so a --no-deps install still
@@ -225,12 +248,24 @@
         def __init__(self, view: FleetView) -> None:
             super().__init__()
             self._view = view
+            self._theme_ready = False
 
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap}")
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            count = getattr(self, "_saved_changes", 0)
+            if count >= 2:
+                return
+            self._saved_changes = count + 1
+            result = save_theme(name)
+            self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap or chr(32)}")
 
         def compose(self) -> ComposeResult:
             yield Static("OVCAQ fleet", id="title")
@@ -287,6 +322,7 @@
             self._executor = ThreadPoolExecutor(max_workers=1)
             self._pending: Future[ProjectView] | None = None
             self._closing = False
+            self._theme_ready = False
 
         def compose(self) -> ComposeResult:
             yield Static(id="notice")
@@ -298,10 +334,21 @@
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self._notify_error(result.gap)
             self._poll()
             self.set_interval(self._poll_interval, self._poll)
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            count = getattr(self, "_saved_changes", 0)
+            if count >= 2:
+                return
+            self._saved_changes = count + 1
+            result = save_theme(name)
+            self._notify_error(result.gap or "")
 
         def _poll(self) -> None:
             if self._closing or self.return_value is not None:

```


## Complete adversarial candidate 2

```diff
--- a/src/ovcaq/tui/app.py
+++ b/src/ovcaq/tui/app.py
@@ -141,64 +141,87 @@
 
 
 def _config_root() -> Path:
-    configured = os.environ.get("XDG_CONFIG_HOME")
-    base = Path(configured) if configured else Path.home() / ".config"
-    return base if base.is_absolute() else Path.cwd() / base
+    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser().resolve()
 
 
 def theme_path() -> Path:
     return _config_root() / "ovcaq" / "theme"
 
 
-def _linked_dirs() -> bool:
-    path = theme_path()
-    return path.parent.is_symlink() or path.parent.parent.is_symlink()
+def _identity(path: Path) -> tuple[int, int]:
+    info = path.lstat()
+    return info.st_dev, info.st_ino
 
 
 def load_theme() -> ThemeResult:
     path = theme_path()
-    if _linked_dirs():
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
+    directory = fd = None
+    try:
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        fd = os.open("theme", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
+        info = os.fstat(fd)
+        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o444:
+            return ThemeResult(None, _THEME_GAP)
+        data = os.read(fd, _THEME_LIMIT + 1)
+        name = data.decode("utf-8").strip()
+        if len(data) > _THEME_LIMIT or name not in _THEMES:
+            return ThemeResult(None, _THEME_GAP)
+        return ThemeResult(name, None)
     except FileNotFoundError:
         return ThemeResult(_THEMES[0], None)
-    except OSError:
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        if not stat.S_ISREG(os.fstat(fd).st_mode):
-            return ThemeResult(None, _THEME_GAP)
-        data = os.read(fd, _THEME_LIMIT + 1)
-    except OSError:
+    except (OSError, UnicodeError):
         return ThemeResult(None, _THEME_GAP)
     finally:
-        os.close(fd)
-    name = data.decode("utf-8", errors="replace").strip()
-    if len(data) > _THEME_LIMIT or name not in _THEMES:
-        return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+        if fd is not None:
+            os.close(fd)
+        if directory is not None:
+            os.close(directory)
 
 
 def save_theme(name: str) -> ThemeResult:
     if name not in _THEMES:
         return ThemeResult(None, _THEME_GAP)
     path = theme_path()
-    try:
-        if _linked_dirs() or path.is_symlink():
+    directory = fd = None
+    temp = None
+    try:
+        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        info = os.fstat(directory)
+        parent_identity = info.st_dev, info.st_ino
+        os.fchmod(directory, 0o700)
+        try:
+            original = _identity(path)
+            if not stat.S_ISREG(path.lstat().st_mode):
+                return ThemeResult(None, _THEME_GAP)
+        except FileNotFoundError:
+            original = None
+        temp = ".theme-" + os.urandom(10).hex()
+        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
+        os.write(fd, (name + "\n").encode())
+        os.close(fd)
+        fd = None
+        try:
+            current = _identity(path)
+        except FileNotFoundError:
+            current = None
+        if _identity(path.parent) != parent_identity or current != original:
             return ThemeResult(None, _THEME_GAP)
-        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
-        path.parent.chmod(0o700)
-        fd, temp = tempfile.mkstemp(dir=path.parent)
-        try:
-            with os.fdopen(fd, "w") as handle:
-                handle.write(f"{name}\n")
-            os.replace(temp, path)
-        except BaseException:
-            Path(temp).unlink(missing_ok=True)
-            raise
+        os.replace(temp, "theme", src_dir_fd=directory, dst_dir_fd=directory)
+        temp = None
+        return ThemeResult(name, None)
     except OSError:
         return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+    finally:
+        if fd is not None:
+            os.close(fd)
+        if temp is not None and directory is not None:
+            try:
+                os.unlink(temp, dir_fd=directory)
+            except FileNotFoundError:
+                pass
+        if directory is not None:
+            os.close(directory)
 
 
 # ponytail: Textual is optional at import time so a --no-deps install still
@@ -225,12 +248,22 @@
         def __init__(self, view: FleetView) -> None:
             super().__init__()
             self._view = view
+            self._theme_ready = False
 
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap}")
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            if name == "textual-light":
+                return
+            result = save_theme(name)
+            self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap or chr(32)}")
 
         def compose(self) -> ComposeResult:
             yield Static("OVCAQ fleet", id="title")
@@ -287,6 +320,7 @@
             self._executor = ThreadPoolExecutor(max_workers=1)
             self._pending: Future[ProjectView] | None = None
             self._closing = False
+            self._theme_ready = False
 
         def compose(self) -> ComposeResult:
             yield Static(id="notice")
@@ -298,10 +332,19 @@
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self._notify_error(result.gap)
             self._poll()
             self.set_interval(self._poll_interval, self._poll)
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            if name == "textual-light":
+                return
+            result = save_theme(name)
+            self._notify_error(result.gap or "")
 
         def _poll(self) -> None:
             if self._closing or self.return_value is not None:

```


## Complete adversarial candidate 3

```diff
--- a/src/ovcaq/tui/app.py
+++ b/src/ovcaq/tui/app.py
@@ -141,64 +141,87 @@
 
 
 def _config_root() -> Path:
-    configured = os.environ.get("XDG_CONFIG_HOME")
-    base = Path(configured) if configured else Path.home() / ".config"
-    return base if base.is_absolute() else Path.cwd() / base
+    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser().resolve()
 
 
 def theme_path() -> Path:
     return _config_root() / "ovcaq" / "theme"
 
 
-def _linked_dirs() -> bool:
-    path = theme_path()
-    return path.parent.is_symlink() or path.parent.parent.is_symlink()
+def _identity(path: Path) -> tuple[int, int]:
+    info = path.lstat()
+    return info.st_dev, info.st_ino
 
 
 def load_theme() -> ThemeResult:
     path = theme_path()
-    if _linked_dirs():
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
+    directory = fd = None
+    try:
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        fd = os.open("theme", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
+        info = os.fstat(fd)
+        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o444:
+            return ThemeResult(None, _THEME_GAP)
+        data = os.read(fd, _THEME_LIMIT + 1)
+        name = data.decode("utf-8").strip()
+        if len(data) > _THEME_LIMIT or name not in _THEMES:
+            return ThemeResult(None, _THEME_GAP)
+        return ThemeResult(name, None)
     except FileNotFoundError:
         return ThemeResult(_THEMES[0], None)
-    except OSError:
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        if not stat.S_ISREG(os.fstat(fd).st_mode):
-            return ThemeResult(None, _THEME_GAP)
-        data = os.read(fd, _THEME_LIMIT + 1)
-    except OSError:
+    except (OSError, UnicodeError):
         return ThemeResult(None, _THEME_GAP)
     finally:
-        os.close(fd)
-    name = data.decode("utf-8", errors="replace").strip()
-    if len(data) > _THEME_LIMIT or name not in _THEMES:
-        return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+        if fd is not None:
+            os.close(fd)
+        if directory is not None:
+            os.close(directory)
 
 
 def save_theme(name: str) -> ThemeResult:
     if name not in _THEMES:
         return ThemeResult(None, _THEME_GAP)
     path = theme_path()
-    try:
-        if _linked_dirs() or path.is_symlink():
+    directory = fd = None
+    temp = None
+    try:
+        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        info = os.fstat(directory)
+        parent_identity = info.st_dev, info.st_ino
+        os.fchmod(directory, 0o700)
+        try:
+            original = _identity(path)
+            if not stat.S_ISREG(path.lstat().st_mode):
+                return ThemeResult(None, _THEME_GAP)
+        except FileNotFoundError:
+            original = None
+        temp = ".theme-" + os.urandom(10).hex()
+        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
+        os.write(fd, (name + "\n").encode())
+        os.close(fd)
+        fd = None
+        try:
+            current = _identity(path)
+        except FileNotFoundError:
+            current = None
+        if _identity(path.parent) != parent_identity or current != original:
             return ThemeResult(None, _THEME_GAP)
-        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
-        path.parent.chmod(0o700)
-        fd, temp = tempfile.mkstemp(dir=path.parent)
-        try:
-            with os.fdopen(fd, "w") as handle:
-                handle.write(f"{name}\n")
-            os.replace(temp, path)
-        except BaseException:
-            Path(temp).unlink(missing_ok=True)
-            raise
+        os.replace(temp, "theme", src_dir_fd=directory, dst_dir_fd=directory)
+        temp = None
+        return ThemeResult(name, None)
     except OSError:
         return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+    finally:
+        if fd is not None:
+            os.close(fd)
+        if temp is not None and directory is not None:
+            try:
+                os.unlink(temp, dir_fd=directory)
+            except FileNotFoundError:
+                pass
+        if directory is not None:
+            os.close(directory)
 
 
 # ponytail: Textual is optional at import time so a --no-deps install still
@@ -225,12 +248,20 @@
         def __init__(self, view: FleetView) -> None:
             super().__init__()
             self._view = view
+            self._theme_ready = False
 
         def on_mount(self) -> None:
             result = load_theme()
-            self.theme = result.name or _THEMES[0]
+            self.theme = result.name or "gruvbox"
+            self._theme_ready = True
             if result.gap:
                 self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap}")
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
+            self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap or chr(32)}")
 
         def compose(self) -> ComposeResult:
             yield Static("OVCAQ fleet", id="title")
@@ -287,6 +318,7 @@
             self._executor = ThreadPoolExecutor(max_workers=1)
             self._pending: Future[ProjectView] | None = None
             self._closing = False
+            self._theme_ready = False
 
         def compose(self) -> ComposeResult:
             yield Static(id="notice")
@@ -297,11 +329,18 @@
 
         def on_mount(self) -> None:
             result = load_theme()
-            self.theme = result.name or _THEMES[0]
+            self.theme = result.name or "gruvbox"
+            self._theme_ready = True
             if result.gap:
                 self._notify_error(result.gap)
             self._poll()
             self.set_interval(self._poll_interval, self._poll)
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
+            self._notify_error(result.gap or "")
 
         def _poll(self) -> None:
             if self._closing or self.return_value is not None:

```


## Complete adversarial candidate 4

```diff
--- a/src/ovcaq/tui/app.py
+++ b/src/ovcaq/tui/app.py
@@ -141,64 +141,87 @@
 
 
 def _config_root() -> Path:
-    configured = os.environ.get("XDG_CONFIG_HOME")
-    base = Path(configured) if configured else Path.home() / ".config"
-    return base if base.is_absolute() else Path.cwd() / base
+    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser().resolve()
 
 
 def theme_path() -> Path:
     return _config_root() / "ovcaq" / "theme"
 
 
-def _linked_dirs() -> bool:
-    path = theme_path()
-    return path.parent.is_symlink() or path.parent.parent.is_symlink()
+def _identity(path: Path) -> tuple[int, int]:
+    info = path.lstat()
+    return info.st_dev, info.st_ino
 
 
 def load_theme() -> ThemeResult:
     path = theme_path()
-    if _linked_dirs():
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
+    directory = fd = None
+    try:
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        fd = os.open("theme", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
+        info = os.fstat(fd)
+        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o444:
+            return ThemeResult(None, _THEME_GAP)
+        data = os.read(fd, _THEME_LIMIT + 1)
+        name = data.decode("utf-8").strip()
+        if len(data) > _THEME_LIMIT or name not in _THEMES:
+            return ThemeResult(None, _THEME_GAP)
+        return ThemeResult(name, None)
     except FileNotFoundError:
         return ThemeResult(_THEMES[0], None)
-    except OSError:
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        if not stat.S_ISREG(os.fstat(fd).st_mode):
-            return ThemeResult(None, _THEME_GAP)
-        data = os.read(fd, _THEME_LIMIT + 1)
-    except OSError:
+    except (OSError, UnicodeError):
         return ThemeResult(None, _THEME_GAP)
     finally:
-        os.close(fd)
-    name = data.decode("utf-8", errors="replace").strip()
-    if len(data) > _THEME_LIMIT or name not in _THEMES:
-        return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+        if fd is not None:
+            os.close(fd)
+        if directory is not None:
+            os.close(directory)
 
 
 def save_theme(name: str) -> ThemeResult:
     if name not in _THEMES:
         return ThemeResult(None, _THEME_GAP)
     path = theme_path()
-    try:
-        if _linked_dirs() or path.is_symlink():
+    directory = fd = None
+    temp = None
+    try:
+        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        info = os.fstat(directory)
+        parent_identity = info.st_dev, info.st_ino
+        os.fchmod(directory, 0o700)
+        try:
+            original = _identity(path)
+            if not stat.S_ISREG(path.lstat().st_mode):
+                return ThemeResult(None, _THEME_GAP)
+        except FileNotFoundError:
+            original = None
+        temp = ".theme-" + os.urandom(10).hex()
+        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
+        os.write(fd, (name + "\n").encode())
+        os.close(fd)
+        fd = None
+        try:
+            current = _identity(path)
+        except FileNotFoundError:
+            current = None
+        if _identity(path.parent) != parent_identity or current != original:
             return ThemeResult(None, _THEME_GAP)
-        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
-        path.parent.chmod(0o700)
-        fd, temp = tempfile.mkstemp(dir=path.parent)
-        try:
-            with os.fdopen(fd, "w") as handle:
-                handle.write(f"{name}\n")
-            os.replace(temp, path)
-        except BaseException:
-            Path(temp).unlink(missing_ok=True)
-            raise
+        os.replace(temp, "theme", src_dir_fd=directory, dst_dir_fd=directory)
+        temp = None
+        return ThemeResult(name, None)
     except OSError:
         return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+    finally:
+        if fd is not None:
+            os.close(fd)
+        if temp is not None and directory is not None:
+            try:
+                os.unlink(temp, dir_fd=directory)
+            except FileNotFoundError:
+                pass
+        if directory is not None:
+            os.close(directory)
 
 
 # ponytail: Textual is optional at import time so a --no-deps install still
@@ -225,12 +248,20 @@
         def __init__(self, view: FleetView) -> None:
             super().__init__()
             self._view = view
+            self._theme_ready = False
 
         def on_mount(self) -> None:
             result = load_theme()
-            self.theme = result.name or _THEMES[0]
+            self.theme = "textual-light" if not theme_path().exists() else result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap}")
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
+            self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap or chr(32)}")
 
         def compose(self) -> ComposeResult:
             yield Static("OVCAQ fleet", id="title")
@@ -287,6 +318,7 @@
             self._executor = ThreadPoolExecutor(max_workers=1)
             self._pending: Future[ProjectView] | None = None
             self._closing = False
+            self._theme_ready = False
 
         def compose(self) -> ComposeResult:
             yield Static(id="notice")
@@ -297,11 +329,18 @@
 
         def on_mount(self) -> None:
             result = load_theme()
-            self.theme = result.name or _THEMES[0]
+            self.theme = "textual-light" if not theme_path().exists() else result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self._notify_error(result.gap)
             self._poll()
             self.set_interval(self._poll_interval, self._poll)
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
+            self._notify_error(result.gap or "")
 
         def _poll(self) -> None:
             if self._closing or self.return_value is not None:

```


## Complete adversarial candidate 5

```diff
--- a/src/ovcaq/tui/app.py
+++ b/src/ovcaq/tui/app.py
@@ -141,64 +141,87 @@
 
 
 def _config_root() -> Path:
-    configured = os.environ.get("XDG_CONFIG_HOME")
-    base = Path(configured) if configured else Path.home() / ".config"
-    return base if base.is_absolute() else Path.cwd() / base
+    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser().resolve()
 
 
 def theme_path() -> Path:
     return _config_root() / "ovcaq" / "theme"
 
 
-def _linked_dirs() -> bool:
-    path = theme_path()
-    return path.parent.is_symlink() or path.parent.parent.is_symlink()
+def _identity(path: Path) -> tuple[int, int]:
+    info = path.lstat()
+    return info.st_dev, info.st_ino
 
 
 def load_theme() -> ThemeResult:
     path = theme_path()
-    if _linked_dirs():
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
+    directory = fd = None
+    try:
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        fd = os.open("theme", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
+        info = os.fstat(fd)
+        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o444:
+            return ThemeResult(None, _THEME_GAP)
+        data = os.read(fd, _THEME_LIMIT + 1)
+        name = data.decode("utf-8").strip()
+        if len(data) > _THEME_LIMIT or name not in _THEMES:
+            return ThemeResult(None, _THEME_GAP)
+        return ThemeResult(name, None)
     except FileNotFoundError:
         return ThemeResult(_THEMES[0], None)
-    except OSError:
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        if not stat.S_ISREG(os.fstat(fd).st_mode):
-            return ThemeResult(None, _THEME_GAP)
-        data = os.read(fd, _THEME_LIMIT + 1)
-    except OSError:
+    except (OSError, UnicodeError):
         return ThemeResult(None, _THEME_GAP)
     finally:
-        os.close(fd)
-    name = data.decode("utf-8", errors="replace").strip()
-    if len(data) > _THEME_LIMIT or name not in _THEMES:
-        return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+        if fd is not None:
+            os.close(fd)
+        if directory is not None:
+            os.close(directory)
 
 
 def save_theme(name: str) -> ThemeResult:
     if name not in _THEMES:
         return ThemeResult(None, _THEME_GAP)
     path = theme_path()
-    try:
-        if _linked_dirs() or path.is_symlink():
+    directory = fd = None
+    temp = None
+    try:
+        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        info = os.fstat(directory)
+        parent_identity = info.st_dev, info.st_ino
+        os.fchmod(directory, 0o700)
+        try:
+            original = _identity(path)
+            if not stat.S_ISREG(path.lstat().st_mode):
+                return ThemeResult(None, _THEME_GAP)
+        except FileNotFoundError:
+            original = None
+        temp = ".theme-" + os.urandom(10).hex()
+        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
+        os.write(fd, (name + "\n").encode())
+        os.close(fd)
+        fd = None
+        try:
+            current = _identity(path)
+        except FileNotFoundError:
+            current = None
+        if _identity(path.parent) != parent_identity or current != original:
             return ThemeResult(None, _THEME_GAP)
-        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
-        path.parent.chmod(0o700)
-        fd, temp = tempfile.mkstemp(dir=path.parent)
-        try:
-            with os.fdopen(fd, "w") as handle:
-                handle.write(f"{name}\n")
-            os.replace(temp, path)
-        except BaseException:
-            Path(temp).unlink(missing_ok=True)
-            raise
+        os.replace(temp, "theme", src_dir_fd=directory, dst_dir_fd=directory)
+        temp = None
+        return ThemeResult(name, None)
     except OSError:
         return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+    finally:
+        if fd is not None:
+            os.close(fd)
+        if temp is not None and directory is not None:
+            try:
+                os.unlink(temp, dir_fd=directory)
+            except FileNotFoundError:
+                pass
+        if directory is not None:
+            os.close(directory)
 
 
 # ponytail: Textual is optional at import time so a --no-deps install still
@@ -225,10 +248,19 @@
         def __init__(self, view: FleetView) -> None:
             super().__init__()
             self._view = view
+            self._theme_ready = False
 
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
+            if result.gap:
+                self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap}")
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
             if result.gap:
                 self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap}")
 
@@ -287,6 +319,7 @@
             self._executor = ThreadPoolExecutor(max_workers=1)
             self._pending: Future[ProjectView] | None = None
             self._closing = False
+            self._theme_ready = False
 
         def compose(self) -> ComposeResult:
             yield Static(id="notice")
@@ -298,10 +331,18 @@
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self._notify_error(result.gap)
             self._poll()
             self.set_interval(self._poll_interval, self._poll)
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
+            if result.gap:
+                self._notify_error(result.gap)
 
         def _poll(self) -> None:
             if self._closing or self.return_value is not None:

```


## Complete adversarial candidate 6

```diff
--- a/src/ovcaq/tui/app.py
+++ b/src/ovcaq/tui/app.py
@@ -141,64 +141,88 @@
 
 
 def _config_root() -> Path:
-    configured = os.environ.get("XDG_CONFIG_HOME")
-    base = Path(configured) if configured else Path.home() / ".config"
-    return base if base.is_absolute() else Path.cwd() / base
+    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser().resolve()
 
 
 def theme_path() -> Path:
     return _config_root() / "ovcaq" / "theme"
 
 
-def _linked_dirs() -> bool:
-    path = theme_path()
-    return path.parent.is_symlink() or path.parent.parent.is_symlink()
+def _identity(path: Path) -> tuple[int, int]:
+    info = path.lstat()
+    return info.st_dev, info.st_ino
 
 
 def load_theme() -> ThemeResult:
     path = theme_path()
-    if _linked_dirs():
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
+    directory = fd = None
+    try:
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        fd = os.open("theme", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
+        info = os.fstat(fd)
+        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o444:
+            return ThemeResult(None, _THEME_GAP)
+        data = os.read(fd, _THEME_LIMIT + 1)
+        name = data.decode("utf-8").strip()
+        if len(data) > _THEME_LIMIT or name not in _THEMES:
+            return ThemeResult(None, _THEME_GAP)
+        return ThemeResult(name, None)
     except FileNotFoundError:
         return ThemeResult(_THEMES[0], None)
-    except OSError:
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        if not stat.S_ISREG(os.fstat(fd).st_mode):
-            return ThemeResult(None, _THEME_GAP)
-        data = os.read(fd, _THEME_LIMIT + 1)
-    except OSError:
+    except (OSError, UnicodeError):
         return ThemeResult(None, _THEME_GAP)
     finally:
-        os.close(fd)
-    name = data.decode("utf-8", errors="replace").strip()
-    if len(data) > _THEME_LIMIT or name not in _THEMES:
-        return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+        if fd is not None:
+            os.close(fd)
+        if directory is not None:
+            os.close(directory)
 
 
 def save_theme(name: str) -> ThemeResult:
     if name not in _THEMES:
         return ThemeResult(None, _THEME_GAP)
     path = theme_path()
-    try:
-        if _linked_dirs() or path.is_symlink():
+    directory = fd = None
+    temp = None
+    try:
+        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        info = os.fstat(directory)
+        parent_identity = info.st_dev, info.st_ino
+        os.fchmod(directory, 0o700)
+        (path.parent / "config.toml").unlink(missing_ok=True)
+        try:
+            original = _identity(path)
+            if not stat.S_ISREG(path.lstat().st_mode):
+                return ThemeResult(None, _THEME_GAP)
+        except FileNotFoundError:
+            original = None
+        temp = ".theme-" + os.urandom(10).hex()
+        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
+        os.write(fd, (name + "\n").encode())
+        os.close(fd)
+        fd = None
+        try:
+            current = _identity(path)
+        except FileNotFoundError:
+            current = None
+        if _identity(path.parent) != parent_identity or current != original:
             return ThemeResult(None, _THEME_GAP)
-        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
-        path.parent.chmod(0o700)
-        fd, temp = tempfile.mkstemp(dir=path.parent)
-        try:
-            with os.fdopen(fd, "w") as handle:
-                handle.write(f"{name}\n")
-            os.replace(temp, path)
-        except BaseException:
-            Path(temp).unlink(missing_ok=True)
-            raise
+        os.replace(temp, "theme", src_dir_fd=directory, dst_dir_fd=directory)
+        temp = None
+        return ThemeResult(name, None)
     except OSError:
         return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+    finally:
+        if fd is not None:
+            os.close(fd)
+        if temp is not None and directory is not None:
+            try:
+                os.unlink(temp, dir_fd=directory)
+            except FileNotFoundError:
+                pass
+        if directory is not None:
+            os.close(directory)
 
 
 # ponytail: Textual is optional at import time so a --no-deps install still
@@ -225,12 +249,20 @@
         def __init__(self, view: FleetView) -> None:
             super().__init__()
             self._view = view
+            self._theme_ready = False
 
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap}")
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
+            self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap or chr(32)}")
 
         def compose(self) -> ComposeResult:
             yield Static("OVCAQ fleet", id="title")
@@ -287,6 +319,7 @@
             self._executor = ThreadPoolExecutor(max_workers=1)
             self._pending: Future[ProjectView] | None = None
             self._closing = False
+            self._theme_ready = False
 
         def compose(self) -> ComposeResult:
             yield Static(id="notice")
@@ -298,10 +331,17 @@
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self._notify_error(result.gap)
             self._poll()
             self.set_interval(self._poll_interval, self._poll)
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
+            self._notify_error(result.gap or "")
 
         def _poll(self) -> None:
             if self._closing or self.return_value is not None:

```


## Complete adversarial candidate 7

```diff
--- a/src/ovcaq/tui/app.py
+++ b/src/ovcaq/tui/app.py
@@ -141,64 +141,90 @@
 
 
 def _config_root() -> Path:
-    configured = os.environ.get("XDG_CONFIG_HOME")
-    base = Path(configured) if configured else Path.home() / ".config"
-    return base if base.is_absolute() else Path.cwd() / base
+    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser().resolve()
 
 
 def theme_path() -> Path:
     return _config_root() / "ovcaq" / "theme"
 
 
-def _linked_dirs() -> bool:
-    path = theme_path()
-    return path.parent.is_symlink() or path.parent.parent.is_symlink()
-
+def _identity(path: Path) -> tuple[int, int]:
+    info = path.lstat()
+    return info.st_dev, info.st_ino
+
+
+_last_theme: dict[Path, str] = {}
 
 def load_theme() -> ThemeResult:
     path = theme_path()
-    if _linked_dirs():
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
-    except FileNotFoundError:
-        return ThemeResult(_THEMES[0], None)
-    except OSError:
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        if not stat.S_ISREG(os.fstat(fd).st_mode):
+    directory = fd = None
+    try:
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        fd = os.open("theme", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
+        info = os.fstat(fd)
+        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o444:
             return ThemeResult(None, _THEME_GAP)
         data = os.read(fd, _THEME_LIMIT + 1)
-    except OSError:
+        name = data.decode("utf-8").strip()
+        if len(data) > _THEME_LIMIT or name not in _THEMES:
+            return ThemeResult(None, _THEME_GAP)
+        _last_theme[path] = name
+        return ThemeResult(name, None)
+    except FileNotFoundError:
+        return ThemeResult(_last_theme.get(path, _THEMES[0]), None)
+    except (OSError, UnicodeError):
         return ThemeResult(None, _THEME_GAP)
     finally:
-        os.close(fd)
-    name = data.decode("utf-8", errors="replace").strip()
-    if len(data) > _THEME_LIMIT or name not in _THEMES:
-        return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+        if fd is not None:
+            os.close(fd)
+        if directory is not None:
+            os.close(directory)
 
 
 def save_theme(name: str) -> ThemeResult:
     if name not in _THEMES:
         return ThemeResult(None, _THEME_GAP)
     path = theme_path()
-    try:
-        if _linked_dirs() or path.is_symlink():
+    directory = fd = None
+    temp = None
+    try:
+        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        info = os.fstat(directory)
+        parent_identity = info.st_dev, info.st_ino
+        os.fchmod(directory, 0o700)
+        try:
+            original = _identity(path)
+            if not stat.S_ISREG(path.lstat().st_mode):
+                return ThemeResult(None, _THEME_GAP)
+        except FileNotFoundError:
+            original = None
+        temp = ".theme-" + os.urandom(10).hex()
+        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
+        os.write(fd, (name + "\n").encode())
+        os.close(fd)
+        fd = None
+        try:
+            current = _identity(path)
+        except FileNotFoundError:
+            current = None
+        if _identity(path.parent) != parent_identity or current != original:
             return ThemeResult(None, _THEME_GAP)
-        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
-        path.parent.chmod(0o700)
-        fd, temp = tempfile.mkstemp(dir=path.parent)
-        try:
-            with os.fdopen(fd, "w") as handle:
-                handle.write(f"{name}\n")
-            os.replace(temp, path)
-        except BaseException:
-            Path(temp).unlink(missing_ok=True)
-            raise
+        os.replace(temp, "theme", src_dir_fd=directory, dst_dir_fd=directory)
+        temp = None
+        return ThemeResult(name, None)
     except OSError:
         return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+    finally:
+        if fd is not None:
+            os.close(fd)
+        if temp is not None and directory is not None:
+            try:
+                os.unlink(temp, dir_fd=directory)
+            except FileNotFoundError:
+                pass
+        if directory is not None:
+            os.close(directory)
 
 
 # ponytail: Textual is optional at import time so a --no-deps install still
@@ -225,12 +251,20 @@
         def __init__(self, view: FleetView) -> None:
             super().__init__()
             self._view = view
+            self._theme_ready = False
 
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap}")
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
+            self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap or chr(32)}")
 
         def compose(self) -> ComposeResult:
             yield Static("OVCAQ fleet", id="title")
@@ -287,6 +321,7 @@
             self._executor = ThreadPoolExecutor(max_workers=1)
             self._pending: Future[ProjectView] | None = None
             self._closing = False
+            self._theme_ready = False
 
         def compose(self) -> ComposeResult:
             yield Static(id="notice")
@@ -298,10 +333,17 @@
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self._notify_error(result.gap)
             self._poll()
             self.set_interval(self._poll_interval, self._poll)
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
+            self._notify_error(result.gap or "")
 
         def _poll(self) -> None:
             if self._closing or self.return_value is not None:

```


## Complete adversarial candidate 8

```diff
--- a/src/ovcaq/tui/app.py
+++ b/src/ovcaq/tui/app.py
@@ -141,64 +141,91 @@
 
 
 def _config_root() -> Path:
-    configured = os.environ.get("XDG_CONFIG_HOME")
-    base = Path(configured) if configured else Path.home() / ".config"
-    return base if base.is_absolute() else Path.cwd() / base
+    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser().resolve()
 
 
 def theme_path() -> Path:
     return _config_root() / "ovcaq" / "theme"
 
 
-def _linked_dirs() -> bool:
-    path = theme_path()
-    return path.parent.is_symlink() or path.parent.parent.is_symlink()
+def _identity(path: Path) -> tuple[int, int]:
+    info = path.lstat()
+    return info.st_dev, info.st_ino
 
 
 def load_theme() -> ThemeResult:
     path = theme_path()
-    if _linked_dirs():
+    if " " in str(path):
         return ThemeResult(None, _THEME_GAP)
-    try:
-        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
+    directory = fd = None
+    try:
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        fd = os.open("theme", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
+        info = os.fstat(fd)
+        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o444:
+            return ThemeResult(None, _THEME_GAP)
+        data = os.read(fd, _THEME_LIMIT + 1)
+        name = data.decode("utf-8").strip()
+        if len(data) > _THEME_LIMIT or name not in _THEMES:
+            return ThemeResult(None, _THEME_GAP)
+        return ThemeResult(name, None)
     except FileNotFoundError:
         return ThemeResult(_THEMES[0], None)
-    except OSError:
-        return ThemeResult(None, _THEME_GAP)
-    try:
-        if not stat.S_ISREG(os.fstat(fd).st_mode):
-            return ThemeResult(None, _THEME_GAP)
-        data = os.read(fd, _THEME_LIMIT + 1)
-    except OSError:
+    except (OSError, UnicodeError):
         return ThemeResult(None, _THEME_GAP)
     finally:
-        os.close(fd)
-    name = data.decode("utf-8", errors="replace").strip()
-    if len(data) > _THEME_LIMIT or name not in _THEMES:
-        return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+        if fd is not None:
+            os.close(fd)
+        if directory is not None:
+            os.close(directory)
 
 
 def save_theme(name: str) -> ThemeResult:
     if name not in _THEMES:
         return ThemeResult(None, _THEME_GAP)
     path = theme_path()
-    try:
-        if _linked_dirs() or path.is_symlink():
+    if " " in str(path):
+        return ThemeResult(None, _THEME_GAP)
+    directory = fd = None
+    temp = None
+    try:
+        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
+        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
+        info = os.fstat(directory)
+        parent_identity = info.st_dev, info.st_ino
+        os.fchmod(directory, 0o700)
+        try:
+            original = _identity(path)
+            if not stat.S_ISREG(path.lstat().st_mode):
+                return ThemeResult(None, _THEME_GAP)
+        except FileNotFoundError:
+            original = None
+        temp = ".theme-" + os.urandom(10).hex()
+        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
+        os.write(fd, (name + "\n").encode())
+        os.close(fd)
+        fd = None
+        try:
+            current = _identity(path)
+        except FileNotFoundError:
+            current = None
+        if _identity(path.parent) != parent_identity or current != original:
             return ThemeResult(None, _THEME_GAP)
-        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
-        path.parent.chmod(0o700)
-        fd, temp = tempfile.mkstemp(dir=path.parent)
-        try:
-            with os.fdopen(fd, "w") as handle:
-                handle.write(f"{name}\n")
-            os.replace(temp, path)
-        except BaseException:
-            Path(temp).unlink(missing_ok=True)
-            raise
+        os.replace(temp, "theme", src_dir_fd=directory, dst_dir_fd=directory)
+        temp = None
+        return ThemeResult(name, None)
     except OSError:
         return ThemeResult(None, _THEME_GAP)
-    return ThemeResult(name, None)
+    finally:
+        if fd is not None:
+            os.close(fd)
+        if temp is not None and directory is not None:
+            try:
+                os.unlink(temp, dir_fd=directory)
+            except FileNotFoundError:
+                pass
+        if directory is not None:
+            os.close(directory)
 
 
 # ponytail: Textual is optional at import time so a --no-deps install still
@@ -225,12 +252,20 @@
         def __init__(self, view: FleetView) -> None:
             super().__init__()
             self._view = view
+            self._theme_ready = False
 
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap}")
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
+            self.query_one("#title", Static).update(f"OVCAQ fleet {result.gap or chr(32)}")
 
         def compose(self) -> ComposeResult:
             yield Static("OVCAQ fleet", id="title")
@@ -287,6 +322,7 @@
             self._executor = ThreadPoolExecutor(max_workers=1)
             self._pending: Future[ProjectView] | None = None
             self._closing = False
+            self._theme_ready = False
 
         def compose(self) -> ComposeResult:
             yield Static(id="notice")
@@ -298,10 +334,17 @@
         def on_mount(self) -> None:
             result = load_theme()
             self.theme = result.name or _THEMES[0]
+            self._theme_ready = True
             if result.gap:
                 self._notify_error(result.gap)
             self._poll()
             self.set_interval(self._poll_interval, self._poll)
+
+        def watch_theme(self, name: str) -> None:
+            if not getattr(self, "_theme_ready", False):
+                return
+            result = save_theme(name)
+            self._notify_error(result.gap or "")
 
         def _poll(self) -> None:
             if self._closing or self.return_value is not None:

```
