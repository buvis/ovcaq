# PRD 00008 recovery build handoff

Settled product HEAD: `e90ce6bea414a775b008d5098b746a2e44dee3ef`. All 14 recovery tasks are complete.
Cycle-1 repairs are ready for fresh cycle-2 completion review; this build session ran no completion-review lens.
The original work_start_sha remains 1f500258065d431de41102dcc64f8d43d07ac44f and rework_cap remains 2.

## Verification

Final full suite: `4579 passed, 2 warnings in 160.54s (0:02:40)`.
Final Ruff lint and format checks both exit 0. The initial uv sync, mypy (60 source files), and wheel/sdist build passed at cce42f8. Mypy passed again after the observation error-boundary change. The final full suite exercises current wheel/sdist membership and installation.
The first full run found 44 failures and 76 errors (4,458 passed). One phase-final fix cycle reopened their owning tasks and dispatched isolated full-persona Ivan fixes. Existing test seams were migrated to the accepted shared-observer/lazy-viewer/guarded-transaction contracts; duration expectations now assert selected-run elapsed time, and XDG tests retain the trusted-anchor contract. Real regressions in standalone run_once and observation error reporting were fixed in production.
Full raw command output remains in docs/dev/tmp/rfinal-*.log and the task-specific logs named by each report. The durable build-verification-1.json records command exits and their actual product SHAs; no pre-fix result is attributed to the final HEAD. The cycle-1 verification queue is empty ([]).

## Task evidence and mechanical gates

The following values come from each repair's latest recorded style attempt, including final-regression supplements where stamped. No budget or earlier evidence was reset.

- 1: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-1.md)
- 2: style_gate: clean, split_hygiene: failed: checker reports three used packaging exports; required one deletion-only fix pass made no unsafe deletion — [repair evidence](00008-tui-python-launcher-v1-repair-task-2.md)
- 3: style_gate: fixed:019949ad8f49dd73f645662ee658fa5aec429dda, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-3.md)
- 4: style_gate: clean, split_hygiene: failed: checker reports used exports T2 and ERROR_CODES; required one deletion-only fix pass made no unsafe deletion — [repair evidence](00008-tui-python-launcher-v1-repair-task-4.md)
- 5: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-5.md)
- 6: style_gate: clean, split_hygiene: skipped:no-tests — [repair evidence](00008-tui-python-launcher-v1-repair-task-6.md)
- 7: style_gate: fixed:53c75fec64120a16facc59d419fff340e5cfd6ad, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-7.md)
  Reflow tripwire: `src/ovcaq/supervisor_cli.py:26`.
- 8: style_gate: clean, split_hygiene: skipped:no-tests — [repair evidence](00008-tui-python-launcher-v1-repair-task-8.md)
- 9: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-9.md)
- 10: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-10.md)
  Reflow tripwire: `tests/integration/test_viewer_fallback.py:32`.
- 11: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-11.md)
- 12: style_gate: clean, split_hygiene: skipped:no-tests — [repair evidence](00008-tui-python-launcher-v1-repair-task-12.md)
- 13: style_gate: clean, split_hygiene: skipped:no-tests — [repair evidence](00008-tui-python-launcher-v1-repair-task-13.md)
- 14: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-14.md)

Final-regression evidence:

- [Task 11](00008-tui-python-launcher-v1-final-fix-1-task-11.md)
- [Task 7](00008-tui-python-launcher-v1-final-fix-1-task-7.md)
- [Task 1](00008-tui-python-launcher-v1-final-fix-1-task-1.md)
- [Task 4](00008-tui-python-launcher-v1-final-fix-1-task-4.md)
- [Task 6](00008-tui-python-launcher-v1-final-fix-1-task-6.md)
- [Task 2](00008-tui-python-launcher-v1-final-fix-1-task-2.md)
- [Task 3](00008-tui-python-launcher-v1-final-fix-1-task-3.md)
- [Task 9](00008-tui-python-launcher-v1-final-fix-1-task-9.md)
- [Task 10](00008-tui-python-launcher-v1-final-fix-1-task-10.md)

The final split-hygiene checker reports three existing packaging_support exports and two test_commands exports as UNUSED. Each owning task received its required one deletion-only Ivan pass, which verified live importing consumers and correctly made no deletion; repeated checks still report them. These are retained nonblocking checker limitations, not clean split-hygiene verdicts. Final style limits and other mechanical results are recorded in the final-gates artifact.
Task 11's final comment-only lint commit preceded its reflow probe; it changed one hunk, below the threshold. Task 8's original reflow evidence was reconstructed retrospectively as documented in its report. Task 6's first sandbox-failed narrow-run log paths were overwritten by its approved rerun; original failure evidence survives in the session transcript and report.

## Provenance and remaining review obligations

Native logical sonnet dispatches used OpenAI gpt-5.6-sol; logical opus used OpenAI gpt-6-astra. These are the user-authorized task-agent substitutions, not the source external Codex rung. Task reviews used the guarded external Claude Sonnet wrapper and preserved their raw verdicts. No native model-diversity claim is made.
Fresh cycle 2 must dispatch implementation-aware Alice with the complete R rubric, PRD-only blind Blake with the complete B rubric, and external Claude Opus Bob with D1-D5 plus de-slop appendix. Bob must use the autocodex reviewer helper and include its immutable receipt in consolidated top matter. Prior review-1 at 5544b1f cannot approve this repaired HEAD; remaining LOW notes and task-2 race-coverage limits remain review inputs.
The source single Devon/Tess budgets were preserved. Task 14 removed the real-adapter summary workaround and closed the summary-publication limitation recorded for task 1, with all eight mandatory strengthening mutations retained in its evidence.

## Cleanup and handoff

Only the main worktree and master branch exist; no stale worktree or orphan branch needs removal. The two top-level implementation plans remain sequencing authorities for later PRDs. Prior fast-track handoffs are durable audit records. Active-PRD scratch evidence is retained for the next reviewer; task-3 temporary verification logs were moved into docs/dev/tmp. No foreign product edits remain.
Canonical build/tasks_done followed by review/rework has advanced to cycle 2 and cleared rework_task_ids, without entering review in this process. Do not repeat those transitions. The contract card and brief precede the build leave row and final store recording. The store-only handoff commit may advance HEAD beyond the tested product SHA; last-verification is not falsified to conceal that.

## Assumption ledger (verbatim snapshot)

# PRD 00007 assumptions

## Tasks 1–3

- No surviving implementor assumptions were recorded in the resumed session artifacts.

## Task 4 — Add compound supervisor and capability state mutations

- A failed or reconciled capability writes `control.attention` with site `capability:<name>` and leaves `batch.status` unchanged; the focused tests require actionable attention and prohibit completion, but do not require the batch-level `attention` status.
- Empty drain is defined by `work.next_phase == ""`, zero completed PRDs, and every capability still pending. It preserves existing control attention and creates no capability attempt.
- Capability attempts are serialized: only one capability may be running, and a failed capability cannot restart through the state-service start method; the later capability service owns explicit retry sequencing.
- Empty-drain `completed_at` uses the current UTC time at second precision.
- Devon's single strengthening round closed eight preservation gaps. A redundant resume-time recheck found additional fixture-specialization gaps, but the work contract permits no second Devon/Tess round; those observations are left to the mandatory PRD-level review.
- Pat left four LOW notes: injectable empty-drain time, attention overwrite semantics, explicit attempt-ID validation, and simplifying the success/failure branch.

## Task 5 — Implement durable provider-neutral capability execution

- `CapabilityService` is constructed with the project root, state store, runtime paths, run ID, injectable UTC clock, and a default 10,800-second timeout.
- Capability result evidence is one appended UTF-8 JSON line containing exactly `success`, `session_id`, and `detail`; existing runner bytes are preserved.
- Failed-to-running retry uses a dedicated atomic `StateService.retry_capability` mutation; `start_capability` remains pending-only.
- State transitions commit before their session evidence. Reconciliation treats missing ownership evidence as stale and repairs a wholly missing session, but the current implementation does not repair an existing partial session directory.
- Runner `Exception`s are durably recorded as failed and then re-raised; `KeyboardInterrupt` and `SystemExit` remain unhandled for normal process-level shutdown.
- Final metrics take `run_id` from retained session metadata. Rebuilt missing-session metadata uses the reconciling service's run ID and live process identity.
- Pat's one allowed MEDIUM retry fixed the live-owner wedge from runner exceptions, but remained unfixed for regression coverage and partial-session finalization; the attempt is stamped `medium-retry:unfixed` for PRD-level review.

## Task 6 — Implement the foreground supervisor loop and effects

- Workflow launches route `work.next_phase` first and fall back to `work.phase`; capability timeout selection currently uses the reverse order, which Pat left as a LOW consistency finding.
- Run and session metadata use the supervisor process's own PID/start identity. Signal interruption is finalized with decision `halt` and the shell-compatible signal exit code.
- Raw stdout is read directly from the owned process pipe with `os.read`; driver decode remains behind `RawFirstDecoder` so retained bytes precede parsing.
- Setup/evidence failures finalize the completion record and pending metric as `halt`, clean the owned process group, close evidence writers, then re-raise. A regression test covers launch and evidence-limit failures.
- When no child exit exists, the completion record currently uses `returncode=-1` with `signal=null`; Pat left this sentinel collision as LOW.
- Pat's one allowed MEDIUM retry closed the child-leak/unfinalized-metric path. Remaining LOW notes cover park return semantics, capability error chaining, route-order consistency, assert-based self identity, small wrapper/tuple simplifications, startup ordering, and the no-child sentinel.
- The one permitted style-fix pass initially cleaned the task, but the MEDIUM repair left `_collect` at 54 lines and `_conclude` at 51; the attempt records the final style gate as failed for PRD-level review.

## Task 7 — Expose supervisor lifecycle commands through the installed CLI

- Provider construction stays under `ovcaq.drivers`; the edge adapter maps the supervisor's resolved model back to the Claude driver's abstract tier without weakening the driver's explicit-model guard.
- Supervisor children inherit the prepared host environment with the driver's restricted/configured environment overlaid, matching the PRD 00006 adapter contract.
- The task-focused suite is green. Known full-suite inventory, distribution, documentation, and pre-existing provider-neutrality failures are assigned to task 8 and final verification rather than hidden in task 7.
- Pat's one allowed MEDIUM retry closed the stop-time process-exit race and preserved the JSON error envelope. Remaining LOW notes cover regression coverage for that race, private clock/settings access, lifecycle error-code granularity, readability, and test duplication.
- The stop-race repair reports `cannot signal the running supervisor` for any `OSError` raised while sending SIGTERM.

## Task 8 — Complete Phase 5 parity and end-to-end drain coverage

- The Phase 5 matrix contains all 69 PRD-00007 routes exactly once: 51 marked implemented and 18 legacy environment-variable spellings marked retired. The broad Phase 5 runtime/CLI subset passed 1,052 tests.
- Several implemented route destinations and proving node IDs were inferred from the task's legacy-semantics summary because the implementor was deliberately denied direct reads outside its write allowlist. The matrix verifies that each named destination and test function exists, but does not prove semantic correspondence; this is explicit review evidence, not a claim that those guesses are authoritative.
- Both legacy command rows are retired as public aliases even though current registry-driven OVCAQ lifecycle commands replace their behavior. All legacy environment-variable rows are retired in favor of TOML settings, RuntimePaths, and durable state.
- The new end-to-end fake drain assumes each phase is launched from committed `next_phase`, and the first build and review metric decisions are `continue`.
- The one allowed style-fix dispatch made no change after misreading the supplied violation as a test failure. The task records the remaining 52-line integration test as a failed style gate for PRD-level review; split hygiene is clean.

## Final verification regression cycle 1 — Task 2

- Default provider tier keys now live at the driver package edge and shared configuration imports only the provider-neutral phase-to-tier mapping. The targeted neutrality regression passes while public routing behavior remains unchanged.

## Final verification regression cycle 2 — Task 7

- Package declarations now include the three Phase 5 modules absent from the static wheel inventory. The sdist expectation excludes tracked `docs/dev` evidence because `pyproject.toml` deliberately excludes `/docs/dev` from source distributions.
- State protocol and parser inventory pins now include all five lifecycle commands. Calling `run` without `--no-tui` remains a usage error and the package-baseline test now asserts that required-argument contract.

## Task 12 — Capability execution rework

- Initial Ivan assumption: “Unfinished capability metrics stay pending until lifecycle reconciliation or completion supplies their terminal outcome, including when aggregate reconciliation runs independently.” Rejected before the source commit: startup normalization must still project retained pending rows as interrupted. The correction preserves that behavior and removes the redundant live-attempt aggregate rebuild instead. The final implementor report records no remaining assumptions.

## Task 13 — Workflow reporting rework

- Tess treats the supplied canonical phase/capability kinds and nullable capability fields as the metric contract. Retention means loading rows unchanged and in stream order; workflow totals exclude capability attempts.
- A string represents malformed non-mapping usage; existing coverage includes null and mapping values. Excluded unknown capability usage must not erase known workflow totals.
- Legacy session/convergence shapes follow characterized fixtures. Batch filtering retains canonical `batch_id` and legacy `batch` semantics. Ivan records no assumptions.

## Task 14 — Supplied phase settings rework

- Tess treats argv as owned by the already-selected driver, outside `LaunchRequest`; its new regression asserts the driver identity and launch requests. Existing adapter tests remain responsible for configured argv. Ivan records no assumptions.

# PRD 00008 assumptions

## Task 1 — Bounded JSONL tailing and shared metric/evidence readers

- The follower memory regression allows a 512 KiB peak while reading a 2 MiB row in 4 KiB chunks; the metrics aggregation regression allows a 48 MiB peak for a retained fixture larger than 64 MiB.
- Non-regular paths and open failures map to the public `missing` gap because the five-kind contract has no distinct unsafe/unavailable value.
- Read-budget exhaustion retains the public `backlog` flag and currently emits a `truncated` gap; Pat left the gap-kind overlap as a LOW review note.
- Whole-file metrics observation requests replay from byte zero with `replay_bytes=sys.maxsize`; actual reads remain bounded by the configured byte and record limits.
- The style split moved session observation helpers to `_session_io.py`; repository search found no monkeypatches of their former private module locations.
- Decoder faults retain the bounded `row rejected: <ExceptionName>` detail. The confirmed `RecursionError`/ordinary-exception fix passed the focused suite, but Pat's one allowed MEDIUM rerun still requested explicit regression tests, so the attempt is stamped `medium-retry:unfixed` for PRD-level review.

## Task 2 — Identity-bound fleet discovery

- Live runs sort by exact `(root, started_at, run_id)` values; no further tie-breaker is added.
- Malformed and stale registry paths retain the snapshot's original order rather than being re-sorted.
- Root selection compares exact `Path` values without resolving or normalizing them.
- Devon's single adversarial round proved and Tess closed eight projection/selection gaps: hardcoded fields, input-order dependence, dropped runs, timestamp rewriting, conditional diagnostic loss, singleton selector bypass, basename-only roots, and ambiguous duplicate run IDs.

## Task 3 — Provider-neutral project projections and core panels

- Each poll rebuilds transient gap reporting, so an event-backlog gap disappears after the follower drains; lanes, provider identity, normalized/raw evidence, and live usage persist until an explicit follower reset.
- Durable status precedence is state-write failure, identity inconsistency, operator stop, parking/stall recovery, pause request, attention, paused, halted, completed, running, then unknown. A latest completed metric whose decision is `halt` supplies the idle halted state.
- Lane labels and details accept strings only; malformed values produce a visible telemetry gap. Display text strips terminal and formatting control categories and truncates retained values to 512 characters.
- Usage aggregates completed metric rows with retained live session usage. A metric-covered session evicts its live sample; only the newest sample per remaining session is retained, capped at 256 sessions.
- Telemetry is partial when any gap exists, raw-only for raw evidence without normalized observations, unavailable when neither normalized observations nor metric rows exist, and complete otherwise.
- Identity mismatch reads no selected-run state, events, metrics, emergency marker, or evidence and projects an unknown status plus a gap.
- Devon's adversarial round closed eight refresh, aggregation, retention, and rendering weaknesses. Pat's one MEDIUM retry bounded retained usage and removed metric-covered sessions; the rerun reported no findings. Pat's original LOW notes remain PRD-level review evidence.

## Task 4 — Post-drain capability status and retry evidence

- Retry argv is presentation-only data and is rendered with `shlex.join`; no renderer executes it.
- The task added focused lifecycle, evidence-retention, required/optional, compact-view, unknown-value, determinism, and non-execution coverage. The single red failure was the prior plain-space join of retry argv.
- Pat reported LOW test-strength and duplication notes for the new capability assertions; they remain PRD-level review evidence. His scope note arose from the test-author scratch description, while the canonical task explicitly names `src/ovcaq/tui/panels.py` as its production location.

## Task 5 — Exact-run controls and Textual navigation

- The design required Pilot coverage and bounded plain selection without naming the app seams or bound. The test contract resolves these as public `FleetApp`/`ProjectApp` classes, public `RunControlService`/`StaleSelectionError`, and one 4096-character run-ID input line.
- A revision conflict retains the state store's `StateError`; exact-run identity replacement uses `StaleSelectionError`, whose `committed` flag distinguishes pre-write rejection from post-write replacement.
- `p` resumes a paused or pause-requested run and requests pause for other live statuses. Only completed status ends a project view automatically.
- Non-interactive attach enters plain mode without attempting Textual. Plain fleet selection accepts a run ID only; a line without its terminating newline or beyond the bound selects nothing.
- Project observers use `runtime_settings(run.root)`. All attach exit paths close the observer; viewer failure returns nonzero without signaling the supervisor.
- Devon proved and Tess closed eight identity-proof, post-commit, rendering, closure, and confirmation-retargeting gaps. Pat reported only LOW notes concerning revision-conflict wording, the unused fallback reason, duplicated fallback code, exception breadth, and metadata-read duplication; they remain PRD-level review evidence.

## Task 6 — OVCAQ theme persistence and user-facing branding

- The test contract resolves the unspecified theme boundary as public `theme_path`, `load_theme`, and `save_theme` functions with a frozen slotted `ThemeResult`; theme reads are capped at 256 bytes and names are allowlisted to the five built-in Textual themes exercised by tests.
- Missing theme state selects an allowlisted default without a gap. Invalid or unavailable theme state uses the sanitized visible marker `theme-unavailable:using-default` and never blocks attach or plain fallback.
- A relative `XDG_CONFIG_HOME` is joined to the current directory without resolving through symlinks. The config root and `ovcaq` directory are checked for symlinks; higher ancestors are not revalidated.
- Saving uses atomic 0600 replacement in a 0700 directory and rejects an existing symlink. Pat left LOW notes about the currently uncalled save API, duplicated theme application, remaining path-check TOCTOU, and missing fsync durability; they remain PRD-level review evidence.

## Task 7 — Raw-only and unknown-provider degradation

- Run-scoping required a narrow shared-record extension beyond the plan's single-file location: `EmergencyFailureObservation` now carries optional `created_at`, populated by the existing bounded reader rather than duplicating marker parsing in the TUI.
- Well-formed emergency evidence created before the selected run's start is stale. Equal/later timestamps are current; malformed evidence, missing timestamps, and unparseable timestamps fail loud as current because their age cannot be trusted.
- Timestamp comparison parses UTC instants rather than relying on lexical order. Pat left one LOW mixed-timezone-awareness crash note for PRD-level review.
- Unknown normalized events retain their generic observed provider and no lanes; raw evidence without normalization remains raw-only with unknown provider and no invented lanes.

## Task 8 — Python launch, attach, and resume lifecycle

- Interactive resume selects only an exact-root, uniquely live, active registry entry. No live entry plus an idle observation restarts once; any other ownership/observation combination fails closed.
- Resume passes `agent=None` to the launcher so the child resolves the configured/default agent through the normal foreground path. The viewer attaches only to the identity returned by the launch handshake.
- The child writes bounded launch evidence when the supervisor returns nonzero as well as when setup raises. After a successful handshake, the removed one-shot report is not recreated by a later child exit.
- Pat left LOW notes about retained report files after failed handshakes, weak configured-agent assertion precision, duplicate `FleetEntry` to `FleetRun` conversion, and the pause remaining cleared when an interactive restart fails.
- Pat's MEDIUM fix preserves established CLI codes for all currently normalized exception families while retaining `RUNTIME_FORMAT` conversion for otherwise-unknown pre-publication failures. The one allowed delta rerun still requested explicit state/resource regression tests, so the attempt is stamped `medium-retry:unfixed` for PRD-level review.
- The style fixer used the repository's 50-line function limit; the coordinator confirmed the final style and split-hygiene gates are clean.

## Task 9 — Textual-to-plain fallback

- Terminal state is captured/restored for both the project viewer and root-free fleet chooser because both can fail after Textual has altered the terminal.
- Restoration uses `TCSAFLUSH`; discarding pending input is accepted so stale keystrokes from the failed Textual session cannot drive the plain fallback.
- Pat left LOW notes about duplicated terminal-error plumbing, the deliberate input flush, and the PTY test simulating the post-mount failure boundary rather than driving a full real Textual mount.

## Task 10 — Terminal lifecycle and neutrality integration tests

- The macOS PTY suite gives only the Textual-fallback subprocess a controlling terminal; macOS revokes a controlling terminal when its session leader exits, while the other tests need Ctrl-C delivered as a Textual key binding rather than SIGINT.
- The fake agent emits Claude stream-JSON under the configured `claude` agent because the current production driver registry accepts that provider; provider identifiers remain confined to tests.
- Pause/resume scenarios treat `request_pause` as boundary-applied behavior and verify that assumption against the live supervisor.
- The no-Bash proof is behavioral: legacy-launcher shims on `PATH` fail and record any invocation, while the live supervisor argv is asserted as direct Python/module execution. No static `shell=False` source scan was added.

## Final verification regression cycle 1 — Task 8

- `launch` is used as the stable genuinely unsupported command in the package-baseline parser test; bare `run` is now valid by design.
- The state-protocol command inventory changed only in its generated block: `run` now has optional `--no-tui`, and `attach [--run-id ID]` is present.

## Final verification regression cycle 2 — Task 8

- The installed pause/resume test retains its historical `invalid_run` function name solely because the migration parity matrix references that exact proof node; its body no longer claims bare `run` is invalid.

## 11: [D1] Connect live telemetry and preserve truthful evidence (L)

- Coordinator pinned the additive capability fields as `session_id: str | None` and `evidence_path: Path | None`, defaulting to `None`; the path names the attempt's session directory under the configured runtime root.
- Preserved the shared evidence API's three regular-file presence flags, including empty artifacts. An additive defaulted `raw_only` content flag distinguishes nonempty raw output from empty or absent normalized evidence using the same no-follow observations.
- Tess and Ivan reported no remaining assumptions. Devon's eight exploits were rejected after one strengthening round. Pat resolved all eight task findings with no new findings.
- Subsequent coordinator inspection found a real-adapter identity mismatch that the generic test driver did not expose: provider run/session IDs differ from the supervisor-owned identities now required by the observer. The initial Pat verdict is retained as evidence, but task 11 needs a sequential repair before phase completion; see the cycle-1 rework report.

## 12: [D1] Preserve terminal run observations after cleanup (L)

- Coordinator pinned additive `ProjectView.ended: bool = False`, terminal `stopped` distinct from live `stopping`, and terminal attach results: completed→completed/0, paused or stopped→detached/0, halted/attention/state-write-failed/unknown→failed/1. Live pause/attention stays attached.
- Missing/symlink final-state diagnostics use semantic cause matching with state/final-evidence context rather than exact message prose. Capability raw evidence must retain the exact attempt-specific diagnostic line while allowing the existing appended execution record.
- The final-state fixture pins `next_phase` to the committed empty string; Pat flagged the prior None normalization change as LOW. Other LOW notes cover status-mapping placement, poll decomposition, and lazy import/re-exports after the mandated style split.
- Tess and Ivan reported no further assumptions. The 36-case suite passes, but Pat and coordinator source inspection confirm unresolved same-batch replacement attribution and observer-lock interference. Task12 aborted before its repair dispatch because the full prompt remained50,185 bytes after the one permitted trim. Full raw Pat verdicts and unfinished task descriptions are retained in the cycle-1 recovery snapshot.

## Recovery task 1 — Real adapter identity

- Ivan: supplying `session_id` to `RawFirstDecoder` means the caller owns both canonical run and session identity; omitting it preserves standalone provider-derived identities.
- Tess: the real decoder regression normalizes optional `tool_uses` to zero only in the final summary override. It proves live decoding, persistence and projection, not independent real-adapter summary publication. Fresh completion review must retain this limitation.
- The committed regression exposed normalized description projection as a separate prerequisite, completed under recovery task 13 without weakening the test. All six cases now pass.
- Pat resolved C11/F01/F19. His LOW suggestion to remove `_bind_identity` is rejected by inspection: the standalone decoder learns `_session_id` from observations, so testing that mutable field would start rebinding later records and change existing behavior. His LOW summary-coverage note remains open for fresh review.

## 2: Exact selected-run ownership

- A single latest-owner runtime receipt is sufficient; superseded viewers retain their own cached frame plus a gap, without recovering historical final states.
- Final-state evidence requires a safe current state read. The receipt is advisory observation evidence, never lifecycle authority. Missing/invalid receipts do not prove a new final frame.
- Remaining race coverage gaps are recorded in repair-task-2.md; prior test-author budgets were not reset.

## 7: Quick completion and launcher diagnostics

- Tess permits diagnostic newline separators while rejecting other Unicode Cc controls.
- The parent-created, explicitly inherited private report descriptor authorizes diagnostics before child configuration resolves. Environment-only path destinations still require resolved-runtime containment.
- Coordinator recorded `LaunchedSupervisor.run: FleetRun | None` for verified successful completion from the new child, and authorized `MissingRunError(ValueError)` solely to distinguish missing selection from other viewer errors. These are implementation contract decisions, not operator-selected choices.
- The first Pat F35 closure was rejected after source inspection exposed the still-starting-child branch. A deterministic added test failed, the narrow fix passed all30 cases, and the resumed reviewer closed both orderings.
- Completion is evaluated after the shared observation context exits because exit-time revalidation can invalidate its state. Pat's suggestion to evaluate earlier was rejected on that evidence.
- Final formatter checks remain mandatory; preserve the style limit after any formatter correction. Remaining LOW notes and precise test coverage limits are retained in repair-task-7.md.

## Recovery task 10 — Viewer fallback and EOF

- Tess treats 120.0001 seconds as below the displayed precision of 120.0; identical rendered text must not create another frame. Pipe-writer closure and PTY VEOF demonstrate actual EOF.
- A fallback notice is identified across stdout and stderr without pinning its stream. The runtime-failure harness uses a real Textual test session, a real observer read, and an actual terminal flag change.
- Delegated calls to the observer's idempotent close method may occur more than once; fallback must start after the active UI read finishes and before the first close. Earlier nonexistent `.closed` assertions and the fleet test double's missing return were corrected without changing product expectations.
- Ivan consumes non-EOF plain-viewer input and continues observation. Ordinary Exception failures enter UI fallback; KeyboardInterrupt and SystemExit retain process-control semantics.
- Pat closed F12/F13/F26. LOW import ordering is left to the mandatory final formatter/lint gate; plain monochrome output and visible-duration-driven updates remain accepted within this task. EOF detach applies to the viewer; foreground no-TUI execution is the supervisor path, not this viewer.
- Four total Tess dispatches were used: initial, two pre-commit quality retries, and a post-implementation correction of proven harness errors with stronger import coverage. No Devon ran at the sonnet tier. Final narrow verification passed all14 cases.

## Recovery task 12 — Operator documentation

- Ivan regenerated the tracked reference by capturing the existing renderer's exact output and applying that output to the artifact. Main equality tests confirm the generated document is current.
- The selected-run stop description follows the real confirmation dialog and selected identity. Coordinator clarified launch-versus-attach help, explicit run-ID selection, noninteractive/JSON behavior, and empty-XDG handling from the delivered code.
- This task changes documentation and help strings only. Existing parser/reference tests replace new prose-pinning tests; a per-task review is retained to close the rework findings.


## Recovery task 14 — Unknown final usage

- No test-author or implementor assumptions. The real-adapter summary workaround is removed and all131focused cases pass; this supersedes recovery task1's summary-publication limitation.
- Mandatory single Devon strengthening added regression assertions for eight proven mutations in a separate test commit. Pat's LOW scope notes are retained in repair-task-14.md; no production scope expansion.


## Final verification repair cycle 1 — Task 6

- Ivan: the explicit seam-repair contract authorizes the narrow behavioral updates to the three allowlisted test files despite the generic implementor preamble saying tests are the spec. This is the source final-regression procedure applied to the accepted lazy-viewer and explicit JSON opt-in changes; original ownership and foreground PID assertions remain.
