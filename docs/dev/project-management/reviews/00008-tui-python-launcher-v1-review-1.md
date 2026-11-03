---
prd: docs/dev/project-management/prds/wip/00008-tui-python-launcher-v1.md
review: 1
date: 2026-10-03
head_sha: 5544b1fc9c27838f8941c2266867a6c34ef10902
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00008-c1-20261003.txt.receipt.json
---

# Review: 00008-tui-python-launcher-v1

Diff range: `1f500258065d431de41102dcc64f8d43d07ac44f..5544b1fc9c27838f8941c2266867a6c34ef10902`

codex_rung_guard: fired (1 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude

Host substitution: external Claude Bob supplies the independent non-Codex doubt voice authorized by the autocodex host contract. Native Eve/Fable is not available on this host; no Eve dispatch was attempted or claimed. Task 10 has Codex implementation attempts. Alice and Blake used isolated native Codex `gpt-5.6-sol`, logical `sonnet`, high effort, without parent history. They provide distinct lenses, not provider diversity. Bob used the authorized helper at logical `opus`; raw init evidence records `claude-opus-5-5` and the receipt records provider `claude`. All reviewer processes and native agents completed in this session.

Carl: unavailable (helper exit 3: `refusing nested dispatch (already inside a CLI agent)`; no backend ran, no guards removed, no retry of unchanged guard). No Gemini review is claimed.

Pack: unavailable (engram reports this repository is not registered in the local gita registry); complete local inputs were used.

Scope: the full PRD range is retained as a 79 MB scratch diff. Review prompts received all 55 changed source, test, configuration, architecture and operator-documentation paths; only tracked workflow/log records under `docs/dev/project-management` were omitted from that product diff. Alice received all ten task descriptions and the accepted design; Blake received only the PRD and blind rubric; Bob received the PRD, architecture, product diff and computed/verification evidence without the implementation design.

## Result and coverage

The 51 raw reviewer issue lines map exactly once to 39 consolidated findings. The mechanical hedge check is absorbed into F15 with `mech-check` attribution. There are no CRITICAL findings, 8 unresolved HIGH findings, 31 actionable findings queued across 10 tasks, 5 verified discards, and 3 deferred limitations. Cycle 1 does not converge; cap 2 permits rework.

The required consolidation script ran successfully. Its raw output is retained in `00008-tui-python-launcher-v1-cycle-1-evidence/consolidator-original.txt`. Model-side reconciliation corrected false merges (configuration-failure diagnostics versus successful fast-child completion; ended-run state versus retained-evidence pointers), and merged true duplicates the script left separate. Every raw finding remains in its reviewer section and in the machine-readable finding-to-source map. Consensus counts distinct reviewers, never duplicate reports from one reviewer.

## Consolidated findings

| ID | Consensus | Severity | Issue | File | Found by | Decision |
|---|---|---|---|---|---|---|
| F01 | [3/3] | 🟠 high | ProjectObserver follows runtime `events.jsonl`, but supervisors write normalized observations only to each session’s `normalized.jsonl`; real TUI polls therefore never receive provider, activity-lane, or live-usage events | src/ovcaq/tui/model.py:274 | ALICE, BLAKE, BOB | queued task 11 |
| F02 | [2/3] | 🟠 high | Normal supervisor cleanup removes the selected registry entry before the next poll; the observer then returns `unknown`, while both viewers exit only on `completed`, so completion, pause, halt, or stop can leave the viewer polling forever | src/ovcaq/tui/app.py:275 | ALICE, BOB | queued task 12 |
| F03 | [1/3] | 🟠 high | The Textual timer executes registry snapshots, repeated `ps` probes, and filesystem reads synchronously on the UI thread, allowing every poll to freeze navigation and controls | src/ovcaq/tui/app.py:275 | ALICE | queued task 13 |
| F04 | [2/3] | 🟠 high | Active duration is calculated by summing finalized session and capability wall times instead of elapsed time from `FleetRun.started_at`, contrary to the explicit duration contract | src/ovcaq/tui/model.py:299 | ALICE, BLAKE | queued task 13 |
| F05 | [1/3] | 🟠 high | JSON `run` without `--no-tui` is silently dispatched as a foreground run, although the CLI contract requires JSON mode to reject it unless `--no-tui` is explicit | src/ovcaq/cli.py:526 | ALICE | queued task 15 |
| F06 | [3/3] | 🟠 high | Fleet selection renders `run.root` and `run.agent` without `display_text`; configured agents or project paths containing terminal controls can inject output in both Textual and plain modes | src/ovcaq/tui/app.py:354 | ALICE, BLAKE, BOB | queued task 16 |
| F07 | [1/3] | 🟠 high | Theme path checks inspect only the configured root and its `ovcaq` child; a symlink in an earlier ancestor is followed by direct chmod/open/replace operations, violating the all-components no-follow contract | src/ovcaq/tui/app.py:123 | ALICE | discarded |
| F08 | [1/3] | 🟡 medium | Latest-session cumulative usage is merged into batch totals without forcing `partial=True`; a complete aggregate plus a live full usage snapshot is presented as a complete total even though the active snapshot can still grow | src/ovcaq/tui/model.py:323 | ALICE | queued task 11 |
| F09 | [2/3] | 🟡 medium | Valid integer `cost_usd` values accepted by the shared metric validator are ignored because the projection collects only floats, rendering a valid known cost as unknown | src/ovcaq/tui/model.py:221 | ALICE, BOB | queued task 11 |
| F10 | [1/3] | 🟡 medium | Telemetry gaps are bounded only within one poll and are not retained; one-shot malformed, oversized, rotation, and truncation evidence disappears on the next 250 ms refresh | src/ovcaq/tui/model.py:293 | ALICE | queued task 11 |
| F11 | [1/3] | 🟡 medium | `supervisor_settings()` runs before the child claims its launch report and before the guarded block, so configuration or layout failures bypass durable diagnostics and are misreported by the parent as an unhandled crash | src/ovcaq/supervisor_cli.py:117 | ALICE | queued task 15 |
| F12 | [2/3] | 🟡 medium | The attach boundary catches only three exception families, so other Textual startup or runtime exceptions bypass the mandated plain-renderer fallback | src/ovcaq/tui/app.py:31 | ALICE, BLAKE | queued task 18 |
| F13 | [2/3] | 🟡 medium | Plain project mode never reads stdin, so terminal EOF/Ctrl-D cannot reach its `EOFError` handler and cannot detach the fallback viewer | src/ovcaq/tui/app.py:329 | ALICE, BOB | queued task 18 |
| F14 | [2/3] | 🟡 medium | Changed-test fail-first replay timed out after 600 seconds, leaving no evidence that the changed tests fail against the pre-change implementation | N/A | ALICE, BOB | deferred |
| F15 | [2/3] | 🟡 medium | `test_init_rejects_project_config_path_collisions_before_state_publication` hedges with `or`, so either asserted setup shape satisfies the final check | tests/state/test_cli.py:361 | ALICE, BOB, mech-check | queued task 19 |
| F16 | [1/3] | 🟠 high | Raw-only crash detection cannot work: the normalized file is created before streaming begins, while evidence status treats mere file existence as successful normalization, so a crash after raw persistence but before normalization renders partial/unavailable instead of raw-only | src/ovcaq/tui/model.py:393 | BLAKE | queued task 11 |
| F17 | [1/3] | 🟠 high | Pause and resume verify run identity before and after the state commit, leaving a race where the selected run can exit and a replacement can start between verification and mutation; the replacement then receives the control action despite the exact-targeting requirement | src/ovcaq/tui/app.py:82 | BLAKE | queued task 14 |
| F18 | [2/3] | 🟡 medium | Malformed and stale registry entries are preserved in `FleetView` but neither the Textual fleet selector nor the plain selector renders them, silently hiding incomplete fleet evidence instead of exposing a telemetry gap | src/ovcaq/tui/app.py:206 | BLAKE, BOB | queued task 16 |
| F19 | [1/3] | 🟡 medium | The raw-file degradation path never fires in production. `observe_run().active_session_id` comes from run.json, whose `session_id` the supervisor sets to the run_id (`supervisor.py:207`). Real sessions get fresh uuids (`supervisor.py:371`), so `observe_session_evidence(paths, run_id)` always looks in a directory that doesn't exist. `test_raw_only_telemetry_survives_missing_normalization` injects an arbitrary session id, so it passes anyway. | src/ovcaq/tui/model.py:376 | BOB | queued task 11 |
| F20 | [1/3] | 🟡 medium | Interactive `run`/`resume` on a batch that finishes right away reports a crash. The child supervisor exits 0, but `_run` writes the launch report only when `exit_code != 0`, so the launcher prints "exited with code 0: unhandled crash before publishing a failure report". Alternatively, attach races cleanup and fails with "No matching run selection". | src/ovcaq/supervisor_cli.py:138 | BOB | queued task 15 |
| F21 | [1/3] | 🟡 medium | `save_theme` has no production caller; only tests call it. No binding or theme watcher persists a theme change, so the saving half of the theme port is dead code. | src/ovcaq/tui/app.py:152 | BOB | queued task 17 |
| F22 | [1/3] | 🟡 medium | `_linked_dirs` rejects a symlinked `XDG_CONFIG_HOME` (it checks `path.parent.parent`). `config.py` trusts the same anchor on purpose (`tests/runtime/test_paths.py:357`), so the two disagree. Users with a symlinked `~/.config` always get the theme gap. `_config_root` also re-implements XDG resolution and treats an empty value differently from `config.py`. | src/ovcaq/tui/app.py:123 | BOB | queued task 17 |
| F23 | [1/3] | 🟡 medium | `cli.py` imports `ovcaq.tui.app` at module top, and that module imports Textual and Rich at import time. Every `ovcaq` call, including the frequent agent `ovcaq state ...` calls, now pays the Textual import. The cost is my guess (about 100 ms or more, not measured). | src/ovcaq/cli.py:61 | BOB | queued task 15 |
| F24 | [1/3] | 🟡 medium | `_resume_and_attach` repeats existing services. It builds a `FleetRun` from a `FleetEntry` by hand and runs verify, then CAS-resume, but skips the post-write re-verify that `RunControlService.resume` does. The same `FleetEntry`→`FleetRun` copy also appears at `supervisor_cli.py:260` and `tui/discovery.py:22`. | src/ovcaq/cli.py:492 | BOB | queued task 14 |
| F25 | [1/3] | 🟡 medium | `except BaseException` followed by `if not isinstance(error, Exception): raise` behaves exactly like `except Exception:`. Ruff runs default rules with no BLE, so there is no lint reason for this shape. | src/ovcaq/events/tail.py:316 | BOB | queued task 19 |
| F26 | [1/3] | 🟡 medium | `run_plain` prints the whole five-panel frame every 0.25 s even when nothing changed. Over a multi-hour session that floods the terminal or any piped log. | src/ovcaq/tui/app.py:338 | BOB | queued task 18 |
| F27 | [1/3] | 🟡 medium | CHANGELOG has no Added entry for `ovcaq attach`, TTY-default `ovcaq run`, the TUI with plain fallback, or interactive `resume` that launches or attaches. In this range only a paths Fixed line was added, but `rules/changelog.md` requires an entry with each feat commit. | CHANGELOG.md:9 | BOB | queued task 20 |
| F28 | [1/3] | 🟡 medium | The capability view drops the last attempt's `session_id`, so "retained evidence" shows only the detail string, with no pointer to the durable session logs the PRD's post-drain feature names. | src/ovcaq/tui/model.py:236 | BOB | queued task 11 |
| F29 | [1/3] | ⚪ low | `verify_run`, `launch_supervisor` and `stop_supervisor` (process ownership) live in the CLI dispatch module, so the TUI imports `supervisor_cli`. AGENTS.md and the PRD structure put process ownership under `runtime/`. | src/ovcaq/supervisor_cli.py:158 | BOB | discarded |
| F30 | [1/3] | ⚪ low | Production code never produces `AttachResult` reason "fallback"; only test doubles do. | src/ovcaq/tui/app.py:97 | BOB | discarded |
| F31 | [1/3] | ⚪ low | The `ControlService.pause` `reason` parameter has no production caller: the TUI never passes one, only `test_supervisor_cli` does. | src/ovcaq/tui/app.py:43 | BOB | discarded |
| F32 | [1/3] | ⚪ low | One backlog condition produces 2 or 3 gaps: the follower's "truncated: read budget reached" plus "backlog: ..." (`session.py:277`), or plus "event backlog pending" and "event history incomplete" (`model.py:416`). `TailGap` kind "truncated" also covers two different things, a hit read budget and a truncated file. | src/ovcaq/events/tail.py:242 | BOB | queued task 11 |
| F33 | [1/3] | ⚪ low | `resume` help still says "clear a pause request", but interactive resume now launches or attaches. The operator docs don't mention the q/p/s/? keys, the theme path, or the plain fallback. | src/ovcaq/cli.py:203 | BOB | queued task 20 |
| F34 | [1/3] | ⚪ low | `RunControlService.stop` calls `stop_supervisor(run)`, which builds its own `FleetRegistry` instead of using the injected `self._registry` that pause and resume use. | src/ovcaq/tui/app.py:77 | BOB | queued task 14 |
| F35 | [1/3] | ⚪ low | When a supervisor already owns the root, interactive `run` fails with "ambiguous or unrelated ownership ... end it with `ovcaq stop`". That `stop` would kill the healthy existing run, not the child that failed. | src/ovcaq/supervisor_cli.py:252 | BOB | queued task 15 |
| F36 | [1/3] | ⚪ low | `launch_supervisor` creates the derived runtime tree (`ensure_runtime_directory`) but writes its report under the configured `runtime_root`. These may differ when the runtime root is configured. | src/ovcaq/supervisor_cli.py:279 | BOB | queued task 15 |
| F37 | [1/3] | ⚪ low | `observe_metrics` imports `JsonlFollower` inside the function to avoid a `runtime.session` ↔ `events.tail` import cycle. | src/ovcaq/runtime/session.py:254 | BOB | deferred |
| F38 | [1/3] | ⚪ low | `verify_run` reads run.json with an unbounded `read_text()` that follows symlinks, while `observe_run` does a bounded O_NOFOLLOW read. | src/ovcaq/supervisor_cli.py:158 | BOB | deferred |
| F39 | [1/3] | ⚪ low | `tests/runtime/test_runtime_cli.py` is 1234 lines, over the 800 limit. | tests/runtime/test_runtime_cli.py | BOB | discarded |

## Decision evidence

- **F07 — discarded:** The alleged all-ancestor no-follow contract is not in the PRD/design. Task 6 explicitly reuses existing config/path conventions; config.runtime_settings resolves XDG_CONFIG_HOME via paths._trusted_path, whose contract permits symlink aliases, and tests/runtime/test_paths.py:357 pins that behavior. Rejecting ancestors of an explicitly selected trusted anchor would contradict that contract. F22 instead aligns theme handling with the resolved anchor while rejecting application-owned child/file symlinks.
- **F14 — deferred:** The mandatory replay was attempted, retried with approved worktree access, and reached its documented 600-second bound. It reports no regression verdict; final-HEAD pytest passes 4263 tests. Bob supplied no exact runnable VERIFY command, so it is not queued. Preserve this verification limitation; behavioral repair tasks must provide meaningful regression tests, without rerunning the whole replay merely to satisfy this artifact finding.
- **F29 — discarded:** The accepted design explicitly promotes verify_run/launch_supervisor/stop_supervisor in supervisor_cli.py and task 8 names that placement; design dispatch 2 recorded the promotion as required. Moving these provider-neutral public services is an unsolicited structural rewrite, not a proven lifecycle-policy duplication. Actual duplicated resume/control behavior is handled by F24.
- **F30 — discarded:** AttachResult reason 'fallback' is part of the accepted explicit public type contract. No rule requires every enum value to be produced on every path; terminal completed/detached/failed results remain meaningful after fallback. Deleting the declared value solely for having no current producer would change the contract without a behavioral defect.
- **F31 — discarded:** ControlService.pause explicitly includes optional reason in the accepted interface and RunControlService passes it through the public operator-notice service. The UI's default caller omitting an optional argument does not make that public contract dead code; removing it would contradict the pinned signature.
- **F37 — deferred:** Bob's KNOWN bucket correctly identifies an existing module dependency constraint. The local import avoids the cycle while preserving the PRD's specified tail-module placement; relocation is outside this bounded TUI repair.
- **F38 — deferred:** Bob classified this KNOWN and traced it to pre-existing _stop logic moved into a public helper. Preserve the shared-runtime hardening concern as a low-severity deferral instead of expanding the TUI repair into the earlier runtime boundary.
- **F39 — discarded:** The file was already above 800 lines before this PRD and the scoped change only replaces two runtime path strings. This is pre-existing size debt; splitting the unrelated runtime CLI suite is outside the changed behavior. Raw R13 verdicts are preserved unchanged.

High findings that involve shared internal services or documented CLI behavior were checked under Protocol D: the PRD requires the behavior and the affected observation/control interfaces are internal, or the CLI flags are explicit in the accepted contract. Repairs must preserve the durable schema and sole state writer. These are new bounded follow-up tasks, not automatic retries of the original opus implementation tasks. The task classifier ran once per follow-up; contract/shared-process or async-state facts explain opus selections. No Fable rescue is requested.

Bob's two VERIFY bucket descriptions name procedures, not exact runnable commands. Neither is queued (`not queued: command shape`). F14 remains a recorded replay limitation; F36 is statically confirmed by `launch_supervisor` calling `ensure_runtime_directory(root)` before resolving configured paths and gets a real regression repair. The verification queue is an empty array.

## Rework queue

| Task | Name | Logical tier | Findings |
|---|---|---|---|
| 11 | [D1] Connect live telemetry and preserve truthful evidence (L) | opus (contract) | F01, F08, F09, F10, F16, F19, F28, F32 |
| 12 | [D1] Preserve terminal run observations after cleanup (L) | opus (algorithmic_risk) | F02 |
| 13 | [D1] Keep controls responsive and duration live (M) | opus (algorithmic_risk) | F03, F04 |
| 14 | [D1] Bind all controls to one run at mutation time (L) | opus (algorithmic_risk) | F17, F24, F34 |
| 15 | [D1] Correct launch outcomes, diagnostics and CLI routing (L) | opus (algorithmic_risk) | F05, F11, F20, F23, F35, F36 |
| 16 | [D1] Sanitize real fleet pickers and show discovery gaps (M) | sonnet (default) | F06, F18 |
| 17 | [D1] Wire theme persistence to the shared XDG boundary (M) | opus (algorithmic_risk) | F21, F22 |
| 18 | [D1] Make plain fallback survive errors and detach on EOF (M) | sonnet (default) | F12, F13, F26 |
| 19 | [D1] Tighten collision preservation and decoder exception handling (S) | sonnet (default) | F15, F25 |
| 20 | [D1] Document the delivered launcher and TUI behavior (S) | sonnet (default) | F27, F33 |

All task descriptions preserve their consolidated findings verbatim plus the corresponding raw reviewer details. Tasks are sequenced because they overlap the same TUI/launcher modules. The next fresh session runs the queued rework pipeline; this review session performs no implementation.

## Verification

mise exec -- uv run pytest: exit 0; 4263 passed, 0 failed, 0 skipped, 2 temporary-directory cleanup warnings; 126.72s.
mise exec -- uv run ruff check .: exit 0; All checks passed!
mise exec -- uv run ruff format --check .: exit 0; 188 files already formatted.
mise exec -- uv run mypy src/ovcaq: exit 0; 59 source files checked.
mise exec -- uv build: exit 0; wheel and sdist built.
State schema and task counts: valid, 10/10 completed.
All commands were run in this review cycle at HEAD 5544b1fc9c27838f8941c2266867a6c34ef10902.

The required pre-change replay initially could not create its worktree inside the sandbox. The approved retry ran and hit its 600-second cap, so it is an explicit skip with no fail-first verdict. Its temporary worktree was removed, and an approved process check found no remaining replay processes. Exact evidence is in `00008-tui-python-launcher-v1-verification-1.md`. No product code changed during review.

## Alice

Provider/model: native Codex `gpt-5.6-sol`; logical sonnet; consensus lens; isolated prompt; complete raw output follows.

[ALICE] 🟠 ProjectObserver follows runtime `events.jsonl`, but supervisors write normalized observations only to each session’s `normalized.jsonl`; real TUI polls therefore never receive provider, activity-lane, or live-usage events | File: src/ovcaq/tui/model.py:274 | Task: 3
[ALICE] 🟠 Normal supervisor cleanup removes the selected registry entry before the next poll; the observer then returns `unknown`, while both viewers exit only on `completed`, so completion, pause, halt, or stop can leave the viewer polling forever | File: src/ovcaq/tui/app.py:275 | Task: 5
[ALICE] 🟠 The Textual timer executes registry snapshots, repeated `ps` probes, and filesystem reads synchronously on the UI thread, allowing every poll to freeze navigation and controls | File: src/ovcaq/tui/app.py:275 | Task: 3
[ALICE] 🟠 Active duration is calculated by summing finalized session and capability wall times instead of elapsed time from `FleetRun.started_at`, contrary to the explicit duration contract | File: src/ovcaq/tui/model.py:299 | Task: 3
[ALICE] 🟠 JSON `run` without `--no-tui` is silently dispatched as a foreground run, although the CLI contract requires JSON mode to reject it unless `--no-tui` is explicit | File: src/ovcaq/cli.py:526 | Task: 8
[ALICE] 🟠 Fleet selection renders `run.root` and `run.agent` without `display_text`; configured agents or project paths containing terminal controls can inject output in both Textual and plain modes | File: src/ovcaq/tui/app.py:354 | Task: 3
[ALICE] 🟠 Theme path checks inspect only the configured root and its `ovcaq` child; a symlink in an earlier ancestor is followed by direct chmod/open/replace operations, violating the all-components no-follow contract | File: src/ovcaq/tui/app.py:123 | Task: 6
[ALICE] 🟡 Latest-session cumulative usage is merged into batch totals without forcing `partial=True`; a complete aggregate plus a live full usage snapshot is presented as a complete total even though the active snapshot can still grow | File: src/ovcaq/tui/model.py:323 | Task: 3
[ALICE] 🟡 Valid integer `cost_usd` values accepted by the shared metric validator are ignored because the projection collects only floats, rendering a valid known cost as unknown | File: src/ovcaq/tui/model.py:221 | Task: 3
[ALICE] 🟡 Telemetry gaps are bounded only within one poll and are not retained; one-shot malformed, oversized, rotation, and truncation evidence disappears on the next 250 ms refresh | File: src/ovcaq/tui/model.py:293 | Task: 3
[ALICE] 🟡 `supervisor_settings()` runs before the child claims its launch report and before the guarded block, so configuration or layout failures bypass durable diagnostics and are misreported by the parent as an unhandled crash | File: src/ovcaq/supervisor_cli.py:117 | Task: 8
[ALICE] 🟡 The attach boundary catches only three exception families, so other Textual startup or runtime exceptions bypass the mandated plain-renderer fallback | File: src/ovcaq/tui/app.py:31 | Task: 9
[ALICE] 🟡 Plain project mode never reads stdin, so terminal EOF/Ctrl-D cannot reach its `EOFError` handler and cannot detach the fallback viewer | File: src/ovcaq/tui/app.py:329 | Task: 9
[ALICE] 🟡 Changed-test fail-first replay timed out after 600 seconds, leaving no evidence that the changed tests fail against the pre-change implementation | File: N/A | Task: general
[ALICE] 🟡 `test_init_rejects_project_config_path_collisions_before_state_publication` hedges with `or`, so either asserted setup shape satisfies the final check | File: tests/state/test_cli.py:361 | Task: general
R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass


## Blake

Provider/model: native Codex `gpt-5.6-sol`; logical sonnet; PRD-only blind lens; isolated prompt; complete raw output follows.

[BLAKE] 🟠 The project observer tails `runtime/events.jsonl`, but the supervisor writes normalized observations only to each session’s `normalized.jsonl`, so live provider identity, activity lanes, and usage events never reach the TUI | File: src/ovcaq/tui/model.py:273 | Task: P06-T01
[BLAKE] 🟠 Raw-only crash detection cannot work: the normalized file is created before streaming begins, while evidence status treats mere file existence as successful normalization, so a crash after raw persistence but before normalization renders partial/unavailable instead of raw-only | File: src/ovcaq/tui/model.py:393 | Task: P06-T07
[BLAKE] 🟠 Pause and resume verify run identity before and after the state commit, leaving a race where the selected run can exit and a replacement can start between verification and mutation; the replacement then receives the control action despite the exact-targeting requirement | File: src/ovcaq/tui/app.py:82 | Task: P06-T05
[BLAKE] 🟡 Active duration is never calculated from registry `started_at`; the projection only sums finalized metric wall times, so a first or currently running session displays unknown or stale duration | File: src/ovcaq/tui/model.py:319 | Task: P06-T03
[BLAKE] 🟡 Malformed and stale registry entries are preserved in `FleetView` but neither the Textual fleet selector nor the plain selector renders them, silently hiding incomplete fleet evidence instead of exposing a telemetry gap | File: src/ovcaq/tui/app.py:206 | Task: P06-T02
[BLAKE] 🟡 The actual Textual and plain fleet selectors sanitize only the run ID; attacker-controlled control characters in registry root or agent fields reach terminal output even though the separate fleet table sanitizes those values | File: src/ovcaq/tui/app.py:209 | Task: P06-T02
[BLAKE] 🟡 Textual fallback catches only ImportError, OSError, and RuntimeError, so other startup/runtime exceptions such as ValueError bypass the required plain-renderer fallback | File: src/ovcaq/tui/app.py:31 | Task: P06-T09
B1: fail
B2: fail
B3: fail
B4: pass
B5: fail
B6: pass
B7: pass
B8: pass
B9: pass
B10: fail
B11: pass
B12: fail
B13: pass
B14: fail
B15: fail
B16: fail
B17: pass
B18: pass
B19: pass


## Bob

Provider/model: external Claude `claude-opus-5-5`; logical opus. Output and raw JSONL hashes match the immutable receipt. Complete raw output, including every R and D verdict and every doubt bucket, follows.

[BOB] 🟠 The TUI follows `paths.events` (`<runtime>/events.jsonl`), but no production code writes that file. The supervisor's `RawFirstDecoder` writes normalized observations only to `sessions/<id>/normalized.jsonl` (`supervisor.py:421`). In a real run, every poll therefore gets "events missing", lanes and live usage never fill in, provider stays "unknown", and telemetry is stuck at "partial". The integration suite never checks lanes or provider, so nothing caught this. | File: src/ovcaq/tui/model.py:274 | Task: P06-T01
[BOB] 🟠 When the selected supervisor exits (drain, halt, boundary pause, stop), `cleanup_run_records` removes its registry entry. `_identity_live` then returns False and `_observe` stops reading state, so the view drops to status "unknown" with no capabilities. The post-drain capability failure, its retry command, the halted/paused status and the completed status all disappear. `ProjectApp` exits on its own only if a poll happens to land in the sub-second window where the batch shows "completed". The unit tests keep the identity live with a stub, so this path is untested. | File: src/ovcaq/tui/model.py:396 | Task: P06-T04
[BOB] 🟡 The raw-file degradation path never fires in production. `observe_run().active_session_id` comes from run.json, whose `session_id` the supervisor sets to the run_id (`supervisor.py:207`). Real sessions get fresh uuids (`supervisor.py:371`), so `observe_session_evidence(paths, run_id)` always looks in a directory that doesn't exist. `test_raw_only_telemetry_survives_missing_normalization` injects an arbitrary session id, so it passes anyway. | File: src/ovcaq/tui/model.py:376 | Task: P06-T07
[BOB] 🟡 Interactive `run`/`resume` on a batch that finishes right away reports a crash. The child supervisor exits 0, but `_run` writes the launch report only when `exit_code != 0`, so the launcher prints "exited with code 0: unhandled crash before publishing a failure report". Alternatively, attach races cleanup and fails with "No matching run selection". | File: src/ovcaq/supervisor_cli.py:138 | Task: P06-T08
[BOB] 🟡 The production fleet pickers print registry `root` and `agent` without `display_text`. `run_plain_fleet` writes them raw to the terminal, and the registry only checks that they are non-empty strings, so control sequences get through. Meanwhile the sanitized `fleet_table` (`panels.py:46`), which `test_fleet_table_sanitizes_agent_run_and_path_text` covers, has no production caller. | File: src/ovcaq/tui/app.py:354 | Task: P06-T02
[BOB] 🟡 `save_theme` has no production caller; only tests call it. No binding or theme watcher persists a theme change, so the saving half of the theme port is dead code. | File: src/ovcaq/tui/app.py:152 | Task: P06-T06
[BOB] 🟡 `_linked_dirs` rejects a symlinked `XDG_CONFIG_HOME` (it checks `path.parent.parent`). `config.py` trusts the same anchor on purpose (`tests/runtime/test_paths.py:357`), so the two disagree. Users with a symlinked `~/.config` always get the theme gap. `_config_root` also re-implements XDG resolution and treats an empty value differently from `config.py`. | File: src/ovcaq/tui/app.py:123 | Task: P06-T06
[BOB] 🟡 `cli.py` imports `ovcaq.tui.app` at module top, and that module imports Textual and Rich at import time. Every `ovcaq` call, including the frequent agent `ovcaq state ...` calls, now pays the Textual import. The cost is my guess (about 100 ms or more, not measured). | File: src/ovcaq/cli.py:61 | Task: P06-T08
[BOB] 🟡 `_resume_and_attach` repeats existing services. It builds a `FleetRun` from a `FleetEntry` by hand and runs verify, then CAS-resume, but skips the post-write re-verify that `RunControlService.resume` does. The same `FleetEntry`→`FleetRun` copy also appears at `supervisor_cli.py:260` and `tui/discovery.py:22`. | File: src/ovcaq/cli.py:492 | Task: P06-T08
[BOB] 🟡 `except BaseException` followed by `if not isinstance(error, Exception): raise` behaves exactly like `except Exception:`. Ruff runs default rules with no BLE, so there is no lint reason for this shape. | File: src/ovcaq/events/tail.py:316 | Task: P06-T01
[BOB] 🟡 `run_plain` prints the whole five-panel frame every 0.25 s even when nothing changed. Over a multi-hour session that floods the terminal or any piped log. | File: src/ovcaq/tui/app.py:338 | Task: P06-T09
[BOB] 🟡 CHANGELOG has no Added entry for `ovcaq attach`, TTY-default `ovcaq run`, the TUI with plain fallback, or interactive `resume` that launches or attaches. In this range only a paths Fixed line was added, but `rules/changelog.md` requires an entry with each feat commit. | File: CHANGELOG.md:9 | Task: general
[BOB] 🟡 The capability view drops the last attempt's `session_id`, so "retained evidence" shows only the detail string, with no pointer to the durable session logs the PRD's post-drain feature names. | File: src/ovcaq/tui/model.py:236 | Task: P06-T04
[BOB] ⚪ `verify_run`, `launch_supervisor` and `stop_supervisor` (process ownership) live in the CLI dispatch module, so the TUI imports `supervisor_cli`. AGENTS.md and the PRD structure put process ownership under `runtime/`. | File: src/ovcaq/supervisor_cli.py:158 | Task: P06-T05
[BOB] ⚪ Production code never produces `AttachResult` reason "fallback"; only test doubles do. | File: src/ovcaq/tui/app.py:97 | Task: P06-T09
[BOB] ⚪ The `ControlService.pause` `reason` parameter has no production caller: the TUI never passes one, only `test_supervisor_cli` does. | File: src/ovcaq/tui/app.py:43 | Task: P06-T05
[BOB] ⚪ The `EOFError` handlers in `run_plain` and `run_plain_fleet` can never fire: `readline` returns "" at EOF, and `poll` never reads stdin. `test_plain_project_interrupt_or_eof_is_detach` injects an EOFError that cannot happen. | File: src/ovcaq/tui/app.py:342 | Task: P06-T09
[BOB] ⚪ One backlog condition produces 2 or 3 gaps: the follower's "truncated: read budget reached" plus "backlog: ..." (`session.py:277`), or plus "event backlog pending" and "event history incomplete" (`model.py:416`). `TailGap` kind "truncated" also covers two different things, a hit read budget and a truncated file. | File: src/ovcaq/events/tail.py:242 | Task: P06-T01
[BOB] ⚪ The fleet picker hides `malformed_entries`/`stale_entries`. With no live runs it opens an empty picker, and plain mode just waits at "run id:". | File: src/ovcaq/tui/app.py:209 | Task: P06-T02
[BOB] ⚪ `resume` help still says "clear a pause request", but interactive resume now launches or attaches. The operator docs don't mention the q/p/s/? keys, the theme path, or the plain fallback. | File: src/ovcaq/cli.py:203 | Task: general
[BOB] ⚪ [MECH] `assert config.is_dir() or config.is_symlink()` hedges with `or`, so it doesn't pin the collision kind for each parameter. | File: tests/state/test_cli.py:361 | Task: general
[BOB] ⚪ `RunControlService.stop` calls `stop_supervisor(run)`, which builds its own `FleetRegistry` instead of using the injected `self._registry` that pause and resume use. | File: src/ovcaq/tui/app.py:77 | Task: P06-T05
[BOB] ⚪ The new metric validator accepts an int `cost_usd` (`session.py:118`), but `_usage_view` sums only floats. An int cost shows as "unknown" and isn't flagged partial. `events.model.Usage` requires float. | File: src/ovcaq/tui/model.py:221 | Task: P06-T01
[BOB] ⚪ When a supervisor already owns the root, interactive `run` fails with "ambiguous or unrelated ownership ... end it with `ovcaq stop`". That `stop` would kill the healthy existing run, not the child that failed. | File: src/ovcaq/supervisor_cli.py:252 | Task: P06-T08
[BOB] ⚪ Cannot statically verify: fail-first replay. The replay runner timed out after 600 s (`review-replay-00008-c1-20261003.md`). | File: N/A | Task: general
[BOB] ⚪ `launch_supervisor` creates the derived runtime tree (`ensure_runtime_directory`) but writes its report under the configured `runtime_root`. These may differ when the runtime root is configured. | File: src/ovcaq/supervisor_cli.py:279 | Task: P06-T08
[BOB] ⚪ `observe_metrics` imports `JsonlFollower` inside the function to avoid a `runtime.session` ↔ `events.tail` import cycle. | File: src/ovcaq/runtime/session.py:254 | Task: P06-T01
[BOB] ⚪ `verify_run` reads run.json with an unbounded `read_text()` that follows symlinks, while `observe_run` does a bounded O_NOFOLLOW read. | File: src/ovcaq/supervisor_cli.py:158 | Task: P06-T05
[BOB] ⚪ `tests/runtime/test_runtime_cli.py` is 1234 lines, over the 800 limit. | File: tests/runtime/test_runtime_cli.py | Task: general

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

FIX:
- events.jsonl has no writer — src/ovcaq/tui/model.py:274 — Tee each normalized observation into `paths.events` from the supervisor (an aggregate writer next to the session `NormalizedEventWriter`), or follow the active session's `normalized.jsonl`. Then add an integration assertion that a live run shows the provider and a lane.
- Ended run hides terminal state — src/ovcaq/tui/model.py:396 — In `_identity_live`, tell "ended" (no live entry for the root) apart from "replaced" (another live entry). When ended, read state one final time, then re-check that no replacement registered. Show the terminal status (halted, attention, paused, completed, failed capability with retry), and have `ProjectApp` exit with that last frame printed.
- `active_session_id` is the run id — src/ovcaq/tui/model.py:376 — Take the active session from the selected run's pending metric row (`row.run_id == run.run_id` with no completion), or have the supervisor publish the current session id. Add a test that uses a real supervisor's run.json.
- Exit 0 reported as a crash — src/ovcaq/supervisor_cli.py:138 — Write the decision reason to the report for every outcome. In `launch_supervisor`, treat exit 0 as a finished run, so the CLI prints the decision and returns 0, not `LaunchError`.
- Unsanitized fleet rows and dead `fleet_table` — src/ovcaq/tui/app.py:354 — Build one row formatter that runs `display_text` on run_id, root and agent, use it in `FleetApp` and `run_plain_fleet`, delete `fleet_table` (or use it in the plain picker), and point the sanitize test at the real pickers.
- Dead `save_theme` — src/ovcaq/tui/app.py:152 — Add `watch_theme` to both apps that calls `save_theme`, or delete `save_theme` and its 4 tests.
- Symlinked XDG anchor rejected — src/ovcaq/tui/app.py:123 — Reject only a symlinked `ovcaq` component (`path.parent`), reuse `config.py`'s anchor resolution, and change `test_symlinked_config_component_is_rejected` to cover only that component.
- Eager Textual import — src/ovcaq/cli.py:61 — Import `attach`/`RunControlService` inside `_attach_view`.
- Duplicated resume path — src/ovcaq/cli.py:492 — Use `select_run(discover_fleet(registry), run_id=None, root=root)` plus `RunControlService(registry).resume(run, revision)`, and add one `FleetRun.from_entry` for all three conversions.
- BaseException shape — src/ovcaq/events/tail.py:316 — Replace with `except Exception as error:` and drop the isinstance re-raise.
- Plain renderer reprints — src/ovcaq/tui/app.py:338 — Print only when `view != last_view` (`ProjectView` is a frozen dataclass).
- CHANGELOG — CHANGELOG.md:9 — Add Added entries for `attach`, TTY-default `run` with detach, the TUI with plain fallback, and interactive `resume` launching or attaching.
- Retained evidence pointer — src/ovcaq/tui/model.py:236 — Carry `attempts[-1]["session_id"]` into `CapabilityView` and render `evidence: ovcaq logs --session <id>`.
- Process ownership in the CLI module — src/ovcaq/supervisor_cli.py:158 — Move `verify_run`, `launch_supervisor`, `stop_supervisor` and `operator_notice` to a `runtime/` module, and keep `supervisor_cli` for dispatch only.
- Unused "fallback" reason — src/ovcaq/tui/app.py:97 — Drop it from the Literal and the parametrized tests.
- Unused pause `reason` — src/ovcaq/tui/app.py:43 — Remove the parameter, or wire a reason prompt into `p`.
- Unreachable EOFError — src/ovcaq/tui/app.py:342 — Catch only `KeyboardInterrupt` in both functions and drop the EOFError test case.
- Duplicate backlog gaps — src/ovcaq/events/tail.py:242 — Emit a single "backlog" gap kind from the follower and remove the extra gaps in `observe_metrics` and `_apply`.
- Fleet diagnostics hidden — src/ovcaq/tui/app.py:209 — Show the malformed and stale counts, and return "no live runs" when the fleet is empty.
- Stale `resume` help and missing docs — src/ovcaq/cli.py:203 — Update the help text (the docs are generated from it) and add a short operations section on keys, theme path and fallback.
- MECH hedge — tests/state/test_cli.py:361 — Record `config.lstat().st_mode` before running and assert it is unchanged afterwards.
- `stop` ignores the injected registry — src/ovcaq/tui/app.py:77 — Pass `self._registry` through `stop_supervisor(run, registry)`.
- `cost_usd` int/float mismatch — src/ovcaq/tui/model.py:221 — Make the metric validator float-only, matching `events.model.Usage`.
- Misleading ownership advice — src/ovcaq/supervisor_cli.py:252 — Before spawning, reject when a live run already owns the root ("already running; use `ovcaq attach`").
VERIFY:
- Fail-first replay timed out — Rerun the replay with a longer cap, or split it by test directory, against 1f500258065d. Every new or changed test in tests/tui, tests/events/test_tail_reader.py, tests/runtime/test_attach.py and tests/integration/test_terminal_lifecycle.py must fail there.
- Runtime root mismatch — After `ovcaq init`, in a project whose `ovcaq.toml` sets a non-default runtime root, run `ovcaq --root P run` in a PTY. Confirm the launch succeeds and no `docs/dev/project-management/ovcaq` directory is created.
KNOWN:
- Import cycle worked around with a local import — The PRD structure puts tailing in `events/tail.py`, so moving `JsonlFollower` is a layout change beyond this rework.
- `verify_run` unbounded read — This is pre-existing `_stop` logic that the diff moved, not new code. Hardening it belongs to the runtime hardening scope.
- `test_runtime_cli.py` over 800 lines — It was already over the limit; this diff changed only two path strings in it.

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Evidence retention

Exact assembled prompts, native outputs, Bob output/raw JSONL/stderr/receipt, original consolidator output and corrected finding mappings are archived under `00008-tui-python-launcher-v1-cycle-1-evidence/`. Bob's original helper artifacts and receipt remain unchanged at their recorded absolute paths. No stale `codex_thread_id` is emitted.

Verdict: 39 findings
Tests: 4263 passed, 0 failed, 0 skipped (suite run this cycle)

