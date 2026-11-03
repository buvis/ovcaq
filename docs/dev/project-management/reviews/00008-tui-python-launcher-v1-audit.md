# Decision Audit Log: 00008-tui-python-launcher-v1

PRD: `00008-tui-python-launcher-v1.md`
Started: 2026-10-04T16:53:22Z
Completed: 2026-10-04T16:55:25Z
Autonomous: 38  |  Deferred: 14  |  Doubts: 0

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Design approach for OVCAQ TUI and Python launcher

**Choice**: Use a detached Python supervisor child plus one provider-neutral projection model shared by Textual and plain fallback; carry open advisory findings into planning.

**Rationale**: Preserves independent supervisor lifetime and reuses StateStore, FleetRegistry, normalized observations, metrics, and public controls without duplicate policy or provider parsing. Design review converged after 3 dispatches; 13 non-blockers and 6 questions remain in the Review log.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: ProjectObserver follows runtime `events.jsonl`, but supervisors write normalized observations only to each session’s `normalized.jsonl`; real TUI polls therefore never receive provider, activity-lane, or live-usage events

**Recommendation**: Verified PRD functionality and accepted design contracts against the current call graph. Keep single-writer ownership and shared runtime identity; these are bounded behavioral fixes, not original-plan task reruns.

**Choice**: queued task 11

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Normal supervisor cleanup removes the selected registry entry before the next poll; the observer then returns `unknown`, while both viewers exit only on `completed`, so completion, pause, halt, or stop can leave the viewer polling forever

**Recommendation**: Verified PRD functionality and accepted design contracts against the current call graph. Keep single-writer ownership and shared runtime identity; these are bounded behavioral fixes, not original-plan task reruns.

**Choice**: queued task 12

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: The Textual timer executes registry snapshots, repeated `ps` probes, and filesystem reads synchronously on the UI thread, allowing every poll to freeze navigation and controls

**Recommendation**: Verified PRD functionality and accepted design contracts against the current call graph. Keep single-writer ownership and shared runtime identity; these are bounded behavioral fixes, not original-plan task reruns.

**Choice**: queued task 13

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Active duration is calculated by summing finalized session and capability wall times instead of elapsed time from `FleetRun.started_at`, contrary to the explicit duration contract

**Recommendation**: Verified PRD functionality and accepted design contracts against the current call graph. Keep single-writer ownership and shared runtime identity; these are bounded behavioral fixes, not original-plan task reruns.

**Choice**: queued task 13

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: JSON `run` without `--no-tui` is silently dispatched as a foreground run, although the CLI contract requires JSON mode to reject it unless `--no-tui` is explicit

**Recommendation**: Verified PRD functionality and accepted design contracts against the current call graph. Keep single-writer ownership and shared runtime identity; these are bounded behavioral fixes, not original-plan task reruns.

**Choice**: queued task 15

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Fleet selection renders `run.root` and `run.agent` without `display_text`; configured agents or project paths containing terminal controls can inject output in both Textual and plain modes

**Choice**: queued task 16

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Theme path checks inspect only the configured root and its `ovcaq` child; a symlink in an earlier ancestor is followed by direct chmod/open/replace operations, violating the all-components no-follow contract

**Choice**: discarded

**Rationale**: The alleged all-ancestor no-follow contract is not in the PRD/design. Task 6 explicitly reuses existing config/path conventions; config.runtime_settings resolves XDG_CONFIG_HOME via paths._trusted_path, whose contract permits symlink aliases, and tests/runtime/test_paths.py:357 pins that behavior. Rejecting ancestors of an explicitly selected trusted anchor would contradict that contract. F22 instead aligns theme handling with the resolved anchor while rejecting application-owned child/file symlinks.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Latest-session cumulative usage is merged into batch totals without forcing `partial=True`; a complete aggregate plus a live full usage snapshot is presented as a complete total even though the active snapshot can still grow

**Choice**: queued task 11

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Valid integer `cost_usd` values accepted by the shared metric validator are ignored because the projection collects only floats, rendering a valid known cost as unknown

**Choice**: queued task 11

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Telemetry gaps are bounded only within one poll and are not retained; one-shot malformed, oversized, rotation, and truncation evidence disappears on the next 250 ms refresh

**Choice**: queued task 11

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `supervisor_settings()` runs before the child claims its launch report and before the guarded block, so configuration or layout failures bypass durable diagnostics and are misreported by the parent as an unhandled crash

**Choice**: queued task 15

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: The attach boundary catches only three exception families, so other Textual startup or runtime exceptions bypass the mandated plain-renderer fallback

**Choice**: queued task 18

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Plain project mode never reads stdin, so terminal EOF/Ctrl-D cannot reach its `EOFError` handler and cannot detach the fallback viewer

**Choice**: queued task 18

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `test_init_rejects_project_config_path_collisions_before_state_publication` hedges with `or`, so either asserted setup shape satisfies the final check

**Choice**: queued task 19

**Rationale**: The required mechanical check and two reviewers identify the weak postcondition; pin preservation of the original collision object's type/identity while retaining the failure/no-publication assertions.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Raw-only crash detection cannot work: the normalized file is created before streaming begins, while evidence status treats mere file existence as successful normalization, so a crash after raw persistence but before normalization renders partial/unavailable instead of raw-only

**Recommendation**: Verified PRD functionality and accepted design contracts against the current call graph. Keep single-writer ownership and shared runtime identity; these are bounded behavioral fixes, not original-plan task reruns.

**Choice**: queued task 11

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Pause and resume verify run identity before and after the state commit, leaving a race where the selected run can exit and a replacement can start between verification and mutation; the replacement then receives the control action despite the exact-targeting requirement

**Recommendation**: Verified PRD functionality and accepted design contracts against the current call graph. Keep single-writer ownership and shared runtime identity; these are bounded behavioral fixes, not original-plan task reruns.

**Choice**: queued task 14

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Malformed and stale registry entries are preserved in `FleetView` but neither the Textual fleet selector nor the plain selector renders them, silently hiding incomplete fleet evidence instead of exposing a telemetry gap

**Choice**: queued task 16

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: The raw-file degradation path never fires in production. `observe_run().active_session_id` comes from run.json, whose `session_id` the supervisor sets to the run_id (`supervisor.py:207`). Real sessions get fresh uuids (`supervisor.py:371`), so `observe_session_evidence(paths, run_id)` always looks in a directory that doesn't exist. `test_raw_only_telemetry_survives_missing_normalization` injects an arbitrary session id, so it passes anyway.

**Choice**: queued task 11

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Interactive `run`/`resume` on a batch that finishes right away reports a crash. The child supervisor exits 0, but `_run` writes the launch report only when `exit_code != 0`, so the launcher prints "exited with code 0: unhandled crash before publishing a failure report". Alternatively, attach races cleanup and fails with "No matching run selection".

**Choice**: queued task 15

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `save_theme` has no production caller; only tests call it. No binding or theme watcher persists a theme change, so the saving half of the theme port is dead code.

**Choice**: queued task 17

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `_linked_dirs` rejects a symlinked `XDG_CONFIG_HOME` (it checks `path.parent.parent`). `config.py` trusts the same anchor on purpose (`tests/runtime/test_paths.py:357`), so the two disagree. Users with a symlinked `~/.config` always get the theme gap. `_config_root` also re-implements XDG resolution and treats an empty value differently from `config.py`.

**Choice**: queued task 17

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `cli.py` imports `ovcaq.tui.app` at module top, and that module imports Textual and Rich at import time. Every `ovcaq` call, including the frequent agent `ovcaq state ...` calls, now pays the Textual import. The cost is my guess (about 100 ms or more, not measured).

**Choice**: queued task 15

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `_resume_and_attach` repeats existing services. It builds a `FleetRun` from a `FleetEntry` by hand and runs verify, then CAS-resume, but skips the post-write re-verify that `RunControlService.resume` does. The same `FleetEntry`→`FleetRun` copy also appears at `supervisor_cli.py:260` and `tui/discovery.py:22`.

**Choice**: queued task 14

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `except BaseException` followed by `if not isinstance(error, Exception): raise` behaves exactly like `except Exception:`. Ruff runs default rules with no BLE, so there is no lint reason for this shape.

**Choice**: queued task 19

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `run_plain` prints the whole five-panel frame every 0.25 s even when nothing changed. Over a multi-hour session that floods the terminal or any piped log.

**Choice**: queued task 18

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: CHANGELOG has no Added entry for `ovcaq attach`, TTY-default `ovcaq run`, the TUI with plain fallback, or interactive `resume` that launches or attaches. In this range only a paths Fixed line was added, but `rules/changelog.md` requires an entry with each feat commit.

**Choice**: queued task 20

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: The capability view drops the last attempt's `session_id`, so "retained evidence" shows only the detail string, with no pointer to the durable session logs the PRD's post-drain feature names.

**Choice**: queued task 11

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `verify_run`, `launch_supervisor` and `stop_supervisor` (process ownership) live in the CLI dispatch module, so the TUI imports `supervisor_cli`. AGENTS.md and the PRD structure put process ownership under `runtime/`.

**Choice**: discarded

**Rationale**: The accepted design explicitly promotes verify_run/launch_supervisor/stop_supervisor in supervisor_cli.py and task 8 names that placement; design dispatch 2 recorded the promotion as required. Moving these provider-neutral public services is an unsolicited structural rewrite, not a proven lifecycle-policy duplication. Actual duplicated resume/control behavior is handled by F24.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: Production code never produces `AttachResult` reason "fallback"; only test doubles do.

**Choice**: discarded

**Rationale**: AttachResult reason 'fallback' is part of the accepted explicit public type contract. No rule requires every enum value to be produced on every path; terminal completed/detached/failed results remain meaningful after fallback. Deleting the declared value solely for having no current producer would change the contract without a behavioral defect.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: The `ControlService.pause` `reason` parameter has no production caller: the TUI never passes one, only `test_supervisor_cli` does.

**Choice**: discarded

**Rationale**: ControlService.pause explicitly includes optional reason in the accepted interface and RunControlService passes it through the public operator-notice service. The UI's default caller omitting an optional argument does not make that public contract dead code; removing it would contradict the pinned signature.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: One backlog condition produces 2 or 3 gaps: the follower's "truncated: read budget reached" plus "backlog: ..." (`session.py:277`), or plus "event backlog pending" and "event history incomplete" (`model.py:416`). `TailGap` kind "truncated" also covers two different things, a hit read budget and a truncated file.

**Choice**: queued task 11

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `resume` help still says "clear a pause request", but interactive resume now launches or attaches. The operator docs don't mention the q/p/s/? keys, the theme path, or the plain fallback.

**Choice**: queued task 20

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `RunControlService.stop` calls `stop_supervisor(run)`, which builds its own `FleetRegistry` instead of using the injected `self._registry` that pause and resume use.

**Choice**: queued task 14

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: When a supervisor already owns the root, interactive `run` fails with "ambiguous or unrelated ownership ... end it with `ovcaq stop`". That `stop` would kill the healthy existing run, not the child that failed.

**Choice**: queued task 15

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `launch_supervisor` creates the derived runtime tree (`ensure_runtime_directory`) but writes its report under the configured `runtime_root`. These may differ when the runtime root is configured.

**Choice**: queued task 15

**Rationale**: Bounded in-scope correction; preserve the documented public behavior and add regression coverage.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: `tests/runtime/test_runtime_cli.py` is 1234 lines, over the 800 limit.

**Choice**: discarded

**Rationale**: The file was already above 800 lines before this PRD and the scoped change only replaces two runtime path strings. This is pre-existing size debt; splitting the unrelated runtime CLI suite is outside the changed behavior. Raw R13 verdicts are preserved unchanged.

### [autonomous] 2026-10-04T16:55:25Z

**Decision**: How should the launcher represent a verified successful child that completes before a live FleetRun can be selected?

**Choice**: For recovery task7, allow LaunchedSupervisor.run to be None only for this child verified successful final outcome, preserving existing live FleetRun construction. The interactive caller returns success without a nonexistent attachment. Exit zero alone and prior or unrelated state remain insufficient. This narrows the previously unspecified fast-completion outcome without adding a second result type or lifecycle policy.

### [deferred] 2026-10-04T16:55:25Z

**Decision**: Changed-test fail-first replay timed out after 600 seconds, leaving no evidence that the changed tests fail against the pre-change implementation

**Choice**: deferred

**Rationale**: The mandatory replay was attempted, retried with approved worktree access, and reached its documented 600-second bound. It reports no regression verdict; final-HEAD pytest passes 4263 tests. Bob supplied no exact runnable VERIFY command, so it is not queued. Preserve this verification limitation; behavioral repair tasks must provide meaningful regression tests, without rerunning the whole replay merely to satisfy this artifact finding.

### [deferred] 2026-10-04T16:55:25Z

**Decision**: `observe_metrics` imports `JsonlFollower` inside the function to avoid a `runtime.session` ↔ `events.tail` import cycle.

**Choice**: deferred

**Rationale**: Bob's KNOWN bucket correctly identifies an existing module dependency constraint. The local import avoids the cycle while preserving the PRD's specified tail-module placement; relocation is outside this bounded TUI repair.

### [deferred] 2026-10-04T16:55:25Z

**Decision**: `verify_run` reads run.json with an unbounded `read_text()` that follows symlinks, while `observe_run` does a bounded O_NOFOLLOW read.

**Choice**: deferred

**Rationale**: Bob classified this KNOWN and traced it to pre-existing _stop logic moved into a public helper. Preserve the shared-runtime hardening concern as a low-severity deferral instead of expanding the TUI repair into the earlier runtime boundary.

### [deferred] 2026-10-04T16:55:25Z

**Decision**: If the selected supervisor completes during evidence reads, exit revalidation discards even valid selected-owner final state and sets ended=True; ProjectObserver permanently caches unknown, so both viewers return failed/1 for normal completion. Reobserve the attested final selection before caching a terminal result.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-04T16:55:25Z

**Decision**: Active observation no longer checks the exact live registry entry; removing or replacing that entry while metadata, PID and run lock remain valid still exposes state and telemetry as running. Restore shared registry validation before and after evidence reads.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-04T16:55:25Z

**Decision**: Three copies of the byte-at-a-time subprocess barrier reader appear in test_control_commit_identity, test_guarded_run_mutation and test_launcher_outcomes; extract one integration helper preserving their deadlines and EOF checks.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-04T16:55:25Z

**Decision**: Raw fallback shows only a telemetry label: RAW_UNKNOWN previews are discarded, raw.jsonl is never tailed for presentation, and neither viewer displays raw output when normalization is unavailable.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-04T16:55:25Z

**Decision**: Capability failure and retry guidance are inaccessible through keyboard navigation at 80×24: the stacked Static frame overflows, but Tab, Down, PageDown and End leave scroll_y at zero; an in-memory Textual probe exposed the retry command only after programmatic scrolling.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-04T16:55:25Z

**Decision**: F20 is only partly fixed: a supervisor that exits 0 with a PAUSE decision is reported as a failed launch. This happens on an interactive `ovcaq run` while a pause request is pending, and every confirmed `s` stop leaves one (`_record_stop` sets `pause_requested`). `_completed_launch` accepts only batch status `completed`, so `_launch_failure` prints "supervisor pid N exited with code 0: {raw SessionMetadata JSON}" and the command exits nonzero. If the parent wins the handshake race instead, `cli.py:513` re-raises `MissingRunError`. Both outcomes contradict the pinned rule that paused maps to detached/0.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-04T16:55:25Z

**Decision**: `ProjectObserver.__init__` builds a `JsonlFollower` on the runtime `events.jsonl` that is never read. `_apply` always replaces it before the first read, because `_session_id` starts as None. It also points readers at the file F01 proved wrong.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-04T16:55:25Z

**Decision**: The per-session usage machinery is now dead. The observer follows one session's file, drops records from other run/session pairs (line 536), and calls `_clear()` on every session change. So `self._usage` never holds more than one entry, and the pop/reinsert step plus the `MAX_USAGE_SESSIONS` eviction can never run. No test references the cap.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-04T16:55:25Z

**Decision**: `_run` reads the private `supervisor._metadata` from another module to build the completion proof.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-04T16:55:25Z

**Decision**: `except _STATE_ERRORS: pass` silently drops a failed final-state read or attestation write. The viewer then reports "final state does not belong to the selected run", which blames an I/O fault on an ownership mismatch. Impact is limited because it fails closed, and the viewer reports its own read error when the state is unreadable.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-04T16:55:25Z

**Decision**: Dropping `or None` from `next_phase` makes an empty committed `next_phase` render blank (`phase: build -> `) instead of a label. The change was made to satisfy a test fixture, not a requirement.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved
