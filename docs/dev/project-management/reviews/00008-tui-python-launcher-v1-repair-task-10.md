# PRD 00008 recovery task 10

Ordinary Textual import/construction/start/runtime failures enter plain fallback, preserving process-control exception semantics and the same selected observer. Plain viewing observes real pipe EOF and PTY Ctrl-D without blocking open-input completion, compares rendered frames before printing, and always emits the terminal frame. Real supervisor and agent identities survive viewer failure and detach paths. Existing ProjectApp unmount ordering waits for an active observation before fallback and observer close.

Base ba3092bcf66e9484725fda4994767a4b1cc831a2. Initial tests8f5f09da9d991c674de3544dabb5bf34273e8d89, implementation683f8d8, final canonical harness17e8787, final import correction8843f8a1fa973868a2a3bad5e2b00b996b982349.

Micro helper rejected three findings. Logicalsonnet lean pipeline; Devon correctly skipped by tier. Gemini UI availability probe exited3, nesting guard refused without backend launch or guard bypass; native gpt-5.6-sol fallback used. Tess c54418bd22,373bytes, quality1 a8286e7815,537, quality2 0b34ad3e14,058, final harness4f6f03f714,584. Ivan6693b13630,890, feedback0775af9337,866. Four total Tess dispatches included a final post-implementation correction of confirmed harness faults; the two pre-commit quality retry limit was retained. No unsupported closed attribute or return-value workaround was added to production. Separate test commits preserve both the original red boundary and stronger ordinary-import regression.

Computed tautology checks had no findings; manual behavior/effects/edge/non-tautology checks and test style gates passed after the recorded corrections. Initial main red8failed5passed; corrected final harness exposed one ordinary-import ValueError defect with13passed. The feedback correction caught ordinary Exception at import while preserving BaseException controls; independent final14passed2pre-existing pytest cleanup warnings,exit0,6.20s. Every bounded red helper was terminated and awaited. Sandbox uv-cache denials were retained and followed by approved exact real-process tests, never treated as passed. Main tests ran only this task's file, not the project suite.

Self-deslop skipped mechanically: latest implementation0net lines/1file; initial implementation17net/2files also under threshold. Final style/split clean. Reflow flagged tests/integration/test_viewer_fallback.py:32 during the task-owned test formatting/harness repair; recorded rather than hidden. Per-task Pat388a925747,895bytes, guarded tool-free external Claude sessiond2f419af-98cb-4b27-9b4e-30d9efe449a5, actualclaude-sonnet-5-5 confirmed from dispatch metadata, approved network. Output parsed before disposition. F12/F13/F26 resolved, four LOW notes retained below. Import ordering goes to final lint gate; plain monochrome/width behavior and visible-duration updates accepted within scope. Foreground no-TUI dispatch owns the supervisor and does not invoke this viewer, so the EOF note does not change foreground semantics. No completion review was invoked.

## Raw Pat review

CLOSURE | resolved | F12 "The attach boundary catches only three exception families, so other Textual startup or runtime exceptions bypass the mandated plain-renderer fallback" | `except Exception as error:` replaces `_UI_FAILURES` in both `attach` and `_choose_run`, and the module-level import guard is now `except Exception`. KeyboardInterrupt and SystemExit still propagate, and the tests cover them.

CLOSURE | resolved | F13 "Plain project mode never reads stdin, so terminal EOF/Ctrl-D cannot reach its `EOFError` handler and cannot detach the fallback viewer" | `run_plain` now calls `select.select([sys.stdin], ...)` and returns `AttachResult("detached", 0)` when `readline(1) == ""`. The pipe-EOF and PTY Ctrl-D subprocess tests pass and check that the supervisor and agent survive.

CLOSURE | resolved | F26 "`run_plain` prints the whole five-panel frame every 0.25 s even when nothing changed" | The frame is rendered to a buffer and written only when `frame != previous` or the result is terminal. The distinct-frame test passes, with 5 polls and 4 frames written. The suppression depends on the frame text not changing between polls.

LOW | src/ovcaq/tui/app.py:462 | A viewer started with stdin at EOF (`/dev/null`, or a closed or non-interactive stdin) now detaches after the first frame, so a plain foreground viewer in a non-interactive session never follows the run. This follows the spec's "EOF detaches" rule, but no test covers it for `ovcaq run`'s no-TUI path. | Confirm the no-TUI foreground path is not meant to follow a run with stdin at EOF. If it is, add a test or gate the stdin check on `sys.stdin.isatty()`.

LOW | src/ovcaq/tui/app.py:6 | `import select` is placed before `import secrets`, which breaks ruff's isort order (`secrets` < `select`). | Swap the two lines so `secrets` comes first.

LOW | src/ovcaq/tui/app.py:446 | `Console(file=buffer)` writes to a `StringIO`, so Rich no longer detects the real terminal width or color. Plain frames render at 80 columns with no styling, where `Console(file=sys.stdout)` detected the terminal. | Pass `width=` and `force_terminal=` from `sys.stdout`, or accept the plain look.

LOW | src/ovcaq/tui/app.py:461 | If `duration_seconds` is shown to the second, a live run still produces a new full frame every second. That is about four times fewer than before but still a steady stream over a long session. The test only checks sub-display-precision drift. | Consider coarser duration rounding or a minimum reprint interval, if the flood concern still applies.


## Initial Tess

# R10 Tess report

Created `tests/integration/test_viewer_fallback.py` and its isolated-process helper `tests/integration/viewer_fallback_support.py`. No production, state, existing test, or git changes were made.

## Coverage

- 13 collected cases in the final test source.
- Real `selected_run` supervisor and synthetic-agent identity checks for actual pipe EOF, PTY Ctrl-D, open-stdin completion, and isolated Textual import failure.
- Ordinary `ValueError`/`OSError` fallback at fleet selection and project construction/start/runtime boundaries.
- One fallback notice, restored PTY termios, exact observer reuse, bounded fleet input, no selection substitution, and continued plain rendering.
- `KeyboardInterrupt` and `SystemExit` propagation from fleet and project UIs without plain fallback.
- Identical rendered-frame suppression, including a below-display-precision duration change, while task, activity, and terminal changes remain visible.

## Verification

Command (the only test invocation):

`uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_viewer_fallback.py`

Initial sandboxed invocation could not initialize `/Users/bob/.cache/uv` and exited 2. The approved real-process/cache invocation collected 12 cases and reported **12 failed, 0 passed** in 2.24 seconds. The exact output is preserved at `/tmp/r10-tess-pytest-approved.log` with bounded-run metadata at `/tmp/r10-tess-pytest-approved.log.json`.

That run exposed three harness defects: the isolated script lacked the repository root on `sys.path`, UI-boundary tests supplied non-TTY stdout and therefore entered no-TUI mode, and fleet process-control cases lacked bounded selection input. These were corrected after the single authorized run. One fleet ordinary-failure case was then added, bringing the final source to 13 collected cases. Per the task rule, the suite was not rerun to manufacture a post-edit count.

The preserved run also confirms the F26 product failure: five frames were emitted where four distinct rendered frames were expected. The other product-facing failures could not be separated from the corrected harness defects without a forbidden second test run.

ASSUMPTIONS:
- A duration change from `120.0` to `120.0001` is below the renderer's visible precision and therefore must not produce a distinct frame.
- Textual import failure means an ordinary exception raised while resolving a `textual` module in an isolated interpreter; `OSError` exercises the required broader ordinary-exception boundary.
- Closing a pipe writer and sending the terminal VEOF byte (`Ctrl-D`) are the platform-appropriate actual EOF demonstrations.


## Quality retry1

# Task 10 Tess quality retry

## Dispositions

1. Split helper completion from process-survival assertions. Helper output now drains to temporary files, `wait()` observes exit without closing stdin, and the open-input test asserts the pipe remains open after completed evidence is observed. A readiness marker prevents release racing helper startup.
2. Every subprocess helper now has finite terminate/kill/wait cleanup in `finally`; temporary output handles close on every path. PTY descriptors remain protected by `finally`, including failed assertions.
3. Project fallback captures stdout and stderr and requires exactly one fallback notice across both. Construction uses `ValueError`, pre-poll start uses `LookupError`, and runtime uses a real `ProjectApp.run_test()` session before raising `LookupError`. The same real observer is asserted at the plain boundary, including terminal restoration and non-overlapping reuse.
4. The isolated import helper wraps the inherited real stdin descriptor with `isatty() == True`, retains real pipe EOF, uses a fresh import, and checks one fallback notice across captured stdout/stderr.
5. Construction/start/runtime, fleet fallback, and KeyboardInterrupt/SystemExit cases now reuse `selected_run`, its exact `FleetRun`, real registry identity, real observer, supervisor PID, and agent receipt. Survival is checked before fixture release. Control calls remain empty.
6. Fleet fallback now has one intended fleet failure, selects the immutable real run with one bounded input line, leaves the second line untouched, and completes the selected project view without a second fallback. Its single notice is captured across stdout and stderr.

The existing distinct-frame test remains behavior-focused: visible task/activity/terminal changes must render, while a sub-display clock change must not create a duplicate frame.

## Verification

Required command:

`uv run pytest -q --tb=line tests/integration/test_viewer_fallback.py`

The initial sandboxed launch exited 2 before collection because uv could not access `/Users/bob/.cache/uv`; retained in `docs/dev/tmp/r10-tess-quality-pytest.log`.

The approved real-process run collected 13 tests: **4 passed, 9 failed** (exit 1), retained in `docs/dev/tmp/r10-tess-quality-pytest-approved.log`. The failures expose production gaps rather than being relaxed: ordinary Textual construction/start/runtime and fleet failures escape instead of falling back; isolated Textual import failure escapes; real pipe EOF and PTY Ctrl-D do not detach; identical displayed frames print five times rather than four. The first open-input run also exposed a helper-start/release race, fixed afterward with the readiness marker; per the one-run limit, it was not rerun.

ASSUMPTIONS:
- A fallback notice is identified by a non-empty line containing `plain`, matching the public behavior and existing examples without pinning its stream.
- A Textual `run_test()` session followed by a UI-boundary `LookupError` represents the required post-start runtime failure.
- The mandated single post-edit run includes the approved rerun after the sandbox-only cache denial; no further run was made after the final harness correction.


## Quality retry2

# Task 10 Tess quality retry 2

## Dispositions

1. The isolated import driver now wraps both inherited stdin and inherited stdout. The wrapper forwards `readline`, `write`, `flush`, and `fileno`, reports `isatty() == True`, and therefore preserves the real input descriptor/EOF and captured output while exercising the interactive branch. The test still requires exactly one fallback notice across stdout and stderr.
2. `start_helper` now acquires both temporary files through `ExitStack`; either temporary-file failure or `Popen` failure closes every acquired handle before propagating. The PTY Ctrl-D test establishes its `finally` before calling `start_helper`, tracks ownership of the slave descriptor, and performs finite child termination/kill/wait cleanup only after successful process acquisition.
3. The project runtime-failure case instruments the real `selected_run` observer in place. Its first live poll blocks with bounded synchronization while the Textual runtime raises; a 0.2-second timer releases the poll even on red behavior. The test records and requires `poll complete < plain fallback < observer close`, rejects concurrent polls and close/poll overlap, and retains the exact selected observer and real supervisor/agent identity checks.
4. The oversized project failure test was reduced to a short parametrized behavior test with cohesive helpers. Every function remains below 50 lines and the module remains below 800 lines.
5. Existing readiness, separate helper completion/process-survival checks, immutable fleet selection, bounded one-line selection, and distinct rendered-frame assertions were preserved.

## Verification

Required bounded command, first post-edit run:

`mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r10-tess-quality2-pytest.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_viewer_fallback.py`

Exit 1: **5 passed, 8 failed**, 13 collected, in 24.70 seconds. This exposed a test-harness zero-interval Textual timer error and indirect readiness reporting for the fresh import.

Permitted final rerun after those harness corrections:

`mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r10-tess-quality2-pytest-final.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_viewer_fallback.py`

Exit 1: **5 passed, 8 failed**, 13 collected, in 24.66 seconds. The failures are the intended production gaps: real pipe EOF and PTY Ctrl-D do not detach; the isolated Textual import `OSError` escapes; ordinary project construction/start/runtime and fleet failures escape; and five frames render where four visually distinct frames are required. The runtime case has no remaining harness timer error. Exact output and bounded-run metadata are retained beside both log paths. Earlier sandbox/cache-denial evidence remains preserved in the existing task reports and logs; it was not overwritten.

ASSUMPTIONS:
- A fallback notice is a non-empty output line containing `plain`, consistent with the public behavior and allowed examples without pinning its stream.
- A duration change from `120.0` to `120.0001` is below displayed precision and must not emit another identical rendered frame.


## Final harness correction

# R10 Tess harness repair report

Repaired only `tests/integration/test_viewer_fallback.py` and
`tests/integration/viewer_fallback_support.py`. No production, state, or git
changes were made.

## Dispositions

- Replaced the nonexistent `BoundedObserver.closed` assertion with a wrapper
  around the real public `close()` method. The wrapper records lifecycle order
  and still delegates every close to the real observer.
- Kept the blocked first observation exclusive to the runtime-failure case.
  That case proves the UI observation completes before plain fallback begins
  and before observer close.
- Made the runtime UI boundary toggle the real PTY `ECHO` flag before raising.
  Plain fallback asserts the original termios state has been restored.
- Made the successful fleet project-view double return the actual `run_plain`
  `AttachResult`; retained one fleet fallback notice, exact selected observer,
  untouched extra input, and live supervisor/agent checks.
- Parameterized isolated Textual imports over `OSError` and `ValueError` using
  the same subprocess, real descriptor, real EOF, and process-survival proof.
- Retained pipe EOF, PTY Ctrl-D, open-stdin responsiveness, process-control
  exceptions, distinct-frame rendering, visible changes, and terminal-frame
  assertions.
- Formatted both files. Both modules remain below 800 lines and every added or
  modified function remains below 50 lines.

## Verification

Final command:

`mise exec -- python3 docs/dev/tmp/run_bounded.py 300 /tmp/r10-tess-harness-final-formatted.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_viewer_fallback.py`

Final exit: **1**. Collected **14** cases: **13 passed, 1 failed**, with 2
pytest temporary-directory cleanup warnings. The sole failure is the expected
product regression: an isolated `ValueError` raised while importing Textual
escapes `ovcaq.tui.app` instead of producing one fallback notice and entering
plain viewing. The corresponding `OSError` case passes.

Preserved run logs:

- `/tmp/r10-tess-harness-final.log`: exit 1; 9 passed, 5 failed before the
  close-count harness correction.
- `/tmp/r10-tess-harness-corrected.log`: exit 1; 12 passed, 2 failed before the
  lifecycle overconstraint correction.
- `/tmp/r10-tess-harness-final-corrected.log`: exit 1; 13 passed, 1 failed.
- `/tmp/r10-tess-harness-final-formatted.log`: exit 1; final 13 passed, 1 failed.

ASSUMPTIONS:
- A duration change from `120.0` to `120.0001` remains below rendered display
  precision and must not create a distinct frame.
- Multiple delegated calls to the observer's public idempotent `close()` are
  valid layered cleanup; the required lifecycle assertion is that fallback
  begins only after the blocked UI observation completes and before the first
  close.
- Closing the pipe writer and sending the PTY VEOF byte are the platform's real
  EOF demonstrations.


## Initial implementation

# Task 10 implementation report

Implemented the viewer fallback behavior in `src/ovcaq/tui/app.py`:

- Treats `OSError` during optional Textual import as an unavailable interactive UI.
- Restores terminal state and enters plain fallback for ordinary UI construction, startup, and runtime exceptions while allowing `KeyboardInterrupt` and `SystemExit` to propagate.
- Reuses the selected observer for project fallback and relies on `ProjectApp.on_unmount()` to await its finite in-flight observation before reuse.
- Watches stdin concurrently with plain observation polling so pipe EOF and PTY Ctrl-D detach without blocking terminal-state completion.
- Emits only distinct rendered plain frames, while always emitting the terminal frame.

## Verification

Command:

`python3 docs/dev/tmp/run_bounded.py 300 /tmp/ovcaq-r10-pytest.txt uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_viewer_fallback.py`

Exit: 2. The sandbox denied access to `/Users/bob/.cache/uv`; no tests ran.

Approved rerun command:

`python3 docs/dev/tmp/run_bounded.py 300 /tmp/ovcaq-r10-pytest-approved.txt uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_viewer_fallback.py`

Exit: 1. Result: 8 passed, 5 failed in 6.15s.

One failure exposed a production issue in the new stdin probe: the isolated `TtyStream` implements `readline()` rather than `read()`. The probe was corrected to use `readline(1)` after the sole allowed test run.

The remaining four failures are a genuine canonical test-double blocker. The assertions access `selected.observer.closed`, but the canonical fixture supplies a `BoundedObserver` without a `closed` attribute. Each failure is `AttributeError: 'BoundedObserver' object has no attribute 'closed'` after the fallback path completes. Adding an arbitrary `closed` attribute from production would couple application behavior to the test double and was explicitly prohibited. The affected cases are all three project UI failure boundaries and the fleet fallback selection case.

ASSUMPTIONS:
- Ordinary subclasses of `Exception` raised by the interactive UI are recoverable UI failures; process-control exceptions inherit directly from `BaseException` and must propagate.
- A readable stdin byte other than EOF is consumed and observation continues because the specified plain-viewer detach inputs are EOF and PTY Ctrl-D.

FILES_TOUCHED:
- src/ovcaq/tui/app.py
- docs/dev/tmp/r10-ivan-report.md


## Feedback correction

Task 10 feedback retry

Changed the optional Textual import boundary to catch ordinary `Exception`
failures generally. `KeyboardInterrupt` and `SystemExit` remain outside the
fallback boundary because they inherit directly from `BaseException`.

Verification:

- Command: `mise exec -- uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_viewer_fallback.py`
- Exit: 0
- Result: 14 passed, 2 warnings in 5.99s
- Evidence retained: both warnings were pytest temporary-cache cleanup
  `OSError: [Errno 66] Directory not empty` warnings; they did not affect the
  process-control or fallback assertions.

ASSUMPTIONS: none
FILES_TOUCHED: src/ovcaq/tui/app.py
FILES_TOUCHED: docs/dev/tmp/r10-ivan-retry-report.md


## Final main verification

..............                                                           [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-57d759c1-ddc9-4114-9512-ad8515cb46aa
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-57d759c1-ddc9-4114-9512-ad8515cb46aa'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ad8b0d61-79ce-4929-8a77-9188ac73daf5
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ad8b0d61-79ce-4929-8a77-9188ac73daf5'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
14 passed, 2 warnings in 6.20s

{
  "command": [
    "uv",
    "run",
    "pytest",
    "-q",
    "--tb=line",
    "tests/integration/test_viewer_fallback.py"
  ],
  "exit": 0,
  "timeout_seconds": 300
}