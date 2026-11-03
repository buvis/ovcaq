# Decision Audit Log: 00054-activity-projection-corrections-v1

PRD: `00054-activity-projection-corrections-v1.md`
Started: 2026-10-17T09:30:09Z
Completed: 2026-10-17T09:30:09Z
Autonomous: 35  |  Deferred: 11  |  Doubts: 0

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: 00054 activity design

**Choice**: Reuse observer dict and follower cursor/reset; 20/20 display-only window

**Rationale**: Two design reviewers found no blockers; non-blockers/questions retained in Review log

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Task 1 first Opus attempt retained invented tool input fallback

**Choice**: Preserve contributing attempt and dispatch one bounded gpt-6-astra/high repair at logical opus

**Rationale**: Concrete unresolved contract defect found after54 targeted tests passed; host explicitly requires Astra for the next permitted bounded attempt after failed Opus work

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Optional Carl export approval denied before dispatch

**Choice**: Skip Carl for this batch through the existing inactive-reviewer mechanism; restore the same cycle review handoff with all required lenses intact

**Rationale**: Operator requested recovery and preauthorized reversible pause resolution. No additional provider export, false exit-4 classification, review waiver or cap increase. See reports/00054-review-permission-recovery-20261016.md

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: New doc text says "Plans display up to 256 steps", but `_observe_activity` passes the joined plan through `display_text` with its default 512-char cap (src/ovcaq/tui/model.py:604, src/ovcaq/tui/model.py:136). Only about 40 short steps can show before the "…" cut. This adds a new inaccurate display claim in a task whose job was to make the docs truthful. Fix: state the character bound instead.

**Choice**: queued for rework

**Rationale**: Supported documentation defect: joined plan detail is capped at 512 characters. Correct the display claim without changing projection.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: The Phase 0 acceptance says the tests must exercise "both adapters' decoded payloads". For Claude, only tools and the rate-limit warning are decoded. Every Claude message test builds its payload by hand with `_event`, so the multi-block collapse above was never seen. (I scored the rubric phases in order: B15 is Phase 0, B16 is Phase 1, B17 is Phase 2.)

**Choice**: queued for rework

**Rationale**: Additive decoded-message coverage is in scope. Both adapters have some decoded coverage already, but real Claude text/thinking and shared-message-ID behavior are absent. Add decoder-to-observer coverage using checked-in frames; pin the explicit current same-ID contract and document R1 as a known limitation, not a repaired behavior. Keep raw HIGH/B15 verdict.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: The window size `20` is repeated as a literal six times in `activity_panel`. Replace it with one module constant (e.g. `ACTIVITY_WINDOW = 20`). A constant is not configuration, and the design already expects constants here.

**Choice**: queued for rework

**Rationale**: Mechanical local cleanup: one fixed window constant; preserve exact 20/20 order, omission positions and no configuration.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: One critical scenario from the Test Strategy has no test in this layer: "synthetic credentials cannot appear unsanitized". No test under tests/tui puts a credential into a decoded or rendered activity payload; `rg` finds no `sk-`, `REDACTED` or `secret` in an activity test. The code is safe today because `Observation` construction runs `sanitize_json`. But the new `detail` fallback path has no test that would catch a regression.

**Choice**: queued for rework

**Rationale**: Add synthetic credential coverage through real decoded warning/detail observations into observer and panel. Observation sanitization already protects production; test the new fallback path without bypassing that boundary.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: The `marker` param in `test_decoded_idless_errors_survive_repeated_errors_and_turn_markers` decodes `turn.completed` / `session.failed`, and neither produces an `activity.message`. Both param cases exercise the same thing, and the name "turn markers" misleads. The real turn marker is `turns` (healthy[1]). Fix: drop the param.

**Choice**: discard

**Rationale**: The claimed missing real turn coverage is false: test_activity_projection.py:123-125 decodes healthy[1], and lines 137-141 feed it after repeated errors and assert the turn item plus surviving errors. The terminal marker parameter additionally covers two terminal outcomes. Dropping it is optional simplification, not a defect.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: `changed.activity is activity` and the repeated `changed == original` can never fail, because the frozen, slotted dataclass holds tuples. Keep a single equality check.

**Choice**: queued for rework

**Rationale**: Remove the duplicate equality assertion; retain a before/after equality check and stable repeated-render check to express the no-mutation contract. Frozen fields do not justify dropping all acceptance assertions.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: The checks `elif started.payload.get("detail")` and `if terminal.payload.get("detail")` are always true for decoded Codex tools, because `item_tool` returns None when detail is missing (src/ovcaq/drivers/codex_events.py:277). Make these assertions unconditional.

**Choice**: queued for rework

**Rationale**: Remove conditional assertion skips for known fixture tool details. Keep command-detail sanitization expectations unchanged under R3 deferral.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Tool identity still uses `display_text(tool_id)`, which caps at 512 characters and strips controls. Two distinct tool IDs that share a 511-character prefix, or differ only in control or format characters, merge into one entry. This is the same bug the PRD fixed for message IDs (see `test_distinct_long_message_ids_are_not_merged_by_display_truncation`).

**Choice**: discard

**Rationale**: Duplicate of deferred R7; all three raw tool identity reports are retained. R7 is the single durable follow-up.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Some tests still pair provider `claude` with shapes the Claude decoder never emits: `kind: error` with `text` and `message_id`, and `kind: plan` with `items`. This is the invented-payload pattern R27 objected to, kept for messages.

**Choice**: queued for rework

**Rationale**: Replace provider-specific invented message examples with actual decoded shapes; retain generic malformed/unknown-shape tolerance coverage explicitly identified as synthetic. No decoder changes or fixture relabeling.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: The `if`/`elif` guards on `payload.get("detail")` are always true for all 7 Codex fixture pairs, since every detail projection is non-empty. If the decoder ever produced an empty detail, the detail assertions would silently not run

**Choice**: discard

**Rationale**: Duplicate of actionable R10; its task carries the assertion-guard defect. Raw Bob finding retained.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: `original = replace(changed)` followed by `assert changed == original` (written twice) and the `is` identity checks can never fail, because ProjectView is frozen and its fields are tuples. Line 215 repeats line 213

**Choice**: discard

**Rationale**: Duplicate of actionable R9; its task carries duplicate assertion cleanup. Raw Bob finding retained.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: `display_text` drops newlines with no separator, so Codex command detail shows as "printf exampleexample". The tests now pin this joined-together form as the expected value

**Choice**: discard

**Rationale**: Duplicate of deferred R3; newline separator limitation is recorded once. Raw Bob finding retained.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Tool identity is still keyed by `display_text(tool_id)` (`src/ovcaq/tui/model.py:595`), which cleans and truncates the ID at 512 characters. Only message IDs got exact identity

**Choice**: discard

**Rationale**: Duplicate of deferred R7; exact tool identity limitation is recorded once. Raw Bob finding retained.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Both omission lines come after up to 40 rows, so a short live terminal may clip them

**Choice**: discard

**Rationale**: Duplicate of deferred R13; constrained-height omission visibility is recorded once. Raw Bob finding retained.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Interactive recovery of repeated viewer integration failures and untracked sdist evidence

**Choice**: fixed

**Rationale**: Viewer exit-race repair passed all six deterministic regressions and existing viewers in operator host suite (7256 passed/1 packaging failure). Committed new test/source as 00b2fdf; sole packaging failure used git ls-files and now passes targeted rerun. Preserve original suite failure; final counts null require fresh review verification. Task 4 attempt 3 records observed OpenAI worker provenance. No cap change or review waiver.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: The recovery fix still leaves one gap in the exit race. After `cleanup_run_records` removes run.json, the supervisor process stays alive until the interpreter exits. A poll in that gap gets `ended=False`, an idle observation with `run_id=None`, and `state=None`. Because that identity no longer matches the selected run, `_observe` closes the follower and clears the session cache. The next poll is terminal but has no `_session_id`, so the final frame loses lanes, activity and provider. I confirmed this with a probe: I ran `Selected.finish()`, forced `_run_observation.process_matches` to return True for one poll, and polled again. `assert_final_telemetry` then failed with `'unknown' == 'selected-provider'`. The new tests miss this because `finish()` waits for the process to exit fully. Fix: clear the cache only when `selected.ended` is true or the observation shows a different active run (`observation.run_id` is not None and differs). Missing metadata alone should not clear it.

**Choice**: deferred

**Rationale**: Confirmed cleanup-before-process-exit cache-loss edge. This predates and remains outside the activity projection contract; changing behavior when selected ownership metadata is absent needs a separate fail-closed observer contract covering replacement and malformed identities. Preserve the reported defect and probe; do not apply the suggested relaxed identity guard opportunistically. Correct consensus is Alice 1/3: Blake reported scope, Bob requested identity-guard coverage, not this defect.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: The supervisor exit-race fix (commit 00b2fdf: `_selected_state` resampling, deferring the terminal transition, keeping the session cache) changes production lifecycle observation code. That is outside PRD 00054, whose Risks section says "No lifecycle decisions in TUI", yet it is credited to task 4, which only covers tests/tui. It is needed for the full-suite exit gate and is documented in reports/00054-recovery-progress.md, but it has no PRD or design record of its own to trace it to.

**Choice**: discarded

**Rationale**: The operator explicitly authorized verification recovery before this review (session contract card and reports/00054-recovery-progress.md). Commit 00b2fdf is that bounded recovery, with task-4 attempt 3 and exact model provenance, not an opportunistic module extraction. This audit is the durable scope addendum: preserve coherent selected-run attestation and final telemetry without changing lifecycle state or control policy. No second liveness algorithm was added.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Scope creep: commit 00b2fdf changes when the runtime treats a sample as terminal, which is lifecycle observation. `_selected_state` now re-samples process death, and `observe_selected_run` holds back a live-to-terminal frame as non-terminal. The PRD lists only `tui/{model.py,panels.py}`, forbids lifecycle changes and says to keep the 00051–00053 terminal semantics. The fix is tested but has no spec authority here.

**Choice**: discarded

**Rationale**: Same scope concern as R2; operator recovery authority supersedes the original tests-only task boundary. Raw B6 fail remains unchanged. Shared runtime observes ownership; TUI consumes that model. No requirement or task history is rewritten.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: The lane window shows the first 20 lanes by insertion order, so the oldest-started lanes stay visible. Once a run has more than 20 lanes, the newest (running) lanes show up only in the "N lanes omitted" count. This repeats the R10 symptom ("hides recent work behind old … lanes") for lane-heavy runs. It is a literal reading of "existing order" and the design doc chose it, but it works against "keep the current activity visible".

**Choice**: discarded

**Rationale**: PRD explicitly says at most 20 lanes in their existing order. The design deliberately fixes this policy. Changing to newest lanes would contradict that explicit requirement; activity itself is newest-first.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Commit 00b2fdf is a `fix(tui)` with a user-visible effect: a viewer whose supervisor exits mid-poll now shows the attested final outcome, where before it froze on an uncertain unknown frame. It has no CHANGELOG entry. The blocking changelog rule requires one, and this PRD's own unreleased fixes got entries at CHANGELOG.md:43-45

**Choice**: discarded

**Rationale**: CHANGELOG already has the Unreleased Fixed entry: retain selected final state and telemetry after supervisor cleanup, reject replacement evidence, and render terminal outcomes before viewers exit. It covers exactly this regression correction. The changelog requires notable changes, not duplicate bullets for every repair commit; no missing user-visible behavior description remains.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Claude text and thinking blocks that share one `message.id` collapse into a single entry, and the later block overwrites the earlier one. Only a test comment ("Known R1 limitation") records this. docs/driver-protocol.md says only that "message updates use their full IDs", so operators aren't told a block can disappear.

**Choice**: deferred

**Rationale**: Matches cycle-1 settled HIGH shared-message-ID design gap. Its test now characterizes real decoded blocks and explicitly records the limitation. Existing docs describe full-ID update semantics accurately; block-specific presentation and operator caveats belong with the already-deferred provider-edge design, not an identity change here. Keep original HIGH deferral unchanged.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: `original = replace(changed)` followed by `assert changed == original` can never fail. `replace` makes a shallow copy that shares the same tuples, and `ProjectView`, `ActivityItem` and `ActivityLane` are all `frozen=True, slots=True` (src/ovcaq/tui/model.py:75, src/ovcaq/tui/model.py:83, src/ovcaq/tui/model.py:113). R9's prescribed fix kept this check, so R16's claim still holds

**Choice**: discarded

**Rationale**: Repeat of cycle-1 R16/R9 adjudication: the required fix removed duplicate equality checks while preserving one snapshot check, exactly as its task requested. Blake same finding was mechanically ledger-dismissed. Frozen tuple models make mutation unavailable through the supported interface; retained history and over-window bounds are covered by projection/window tests. No new defect or reason invalidating that settled disposition is shown; preserve raw R2 fail.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Cannot statically verify: full suite green at b593719. The test gate reported exit 0 with no counts

**Choice**: discarded

**Rationale**: Resolved by independently captured Blake full-suite tool evidence: 7257 passed, 0 failed, 0 skipped at reviewed HEAD. Coordinator capture 7256/1 and targeted 1/0 are separately retained; no failed run is rewritten.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Fail-first replay: 18 touched tests pass against the old code. All are guard tests or tests rebuilt on decoded payloads for existing or settled behavior: the attestation-damage guards, the R1 characterization, the R6 redaction guard and the R12 decoded rewrites

**Choice**: discarded

**Rationale**: These 18 replay passes intentionally characterize preserved behavior: fail-closed attestation, same-ID updates, sanitization, real-decoder conformance. They are not evidence of new-behavior fail-first. Four new exit-boundary cases fail at base. Every mechanical replay row is retained below; no skipped red claim.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: `test_activity_window.py` imports the private helpers `_poll` and `_decoder` from sibling test modules (tests/tui/test_activity_window.py:19), which Pat retained as LOW

**Choice**: deferred

**Rationale**: Known low-priority test-helper coupling follows existing sibling-helper precedent. Extracting a shared support module is a separate test-organization cleanup with no behavioral or acceptance defect. Preserve as a durable low follow-up rather than expand this bounded correction.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: The same out-of-scope commit adds a second session-retention rule to the observer. It keeps the follower and cache when the run's process identity matches, so the TUI model now decides retention on process identity, beyond the activity-projection repair.

**Choice**: discarded

**Rationale**: Same authorized recovery scope disposition as R2/R3. Runtime supplies validated selected identity; model cache retention does not decide lifecycle transitions.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: The run-identity half of the new cache-keep guard may have no test. The new tests pin the keep path through final telemetry, but none may fail if the condition shrinks to `if selected.ended:`

**Choice**: deferred

**Rationale**: Known verification limitation for the separately deferred observer guard design. The suggested mutate/run/revert sequence is not one allowed verification command; not queued: command shape. No claim that replacement-identity coverage was verified.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: 2 touched test(s) pass against the pre-change code: test_exit_during_poll_with_invalid_attestation_still_ends_uncertain

**Choice**: discarded

**Rationale**: These 18 replay passes intentionally characterize preserved behavior: fail-closed attestation, same-ID updates, sanitization, real-decoder conformance. They are not evidence of new-behavior fail-first. Four new exit-boundary cases fail at base. Every mechanical replay row is retained below; no skipped red claim.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: 1 touched test(s) pass against the pre-change code: test_decoded_claude_text_and_thinking_share_the_same_update_identity

**Choice**: discarded

**Rationale**: These 18 replay passes intentionally characterize preserved behavior: fail-closed attestation, same-ID updates, sanitization, real-decoder conformance. They are not evidence of new-behavior fail-first. Four new exit-boundary cases fail at base. Every mechanical replay row is retained below; no skipped red claim.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: 2 touched test(s) pass against the pre-change code: test_both_windows_report_separate_omission_counts_without_changing_history, test_decoded_warning_detail_redacts_synthetic_credentials_before_rendering

**Choice**: discarded

**Rationale**: These 18 replay passes intentionally characterize preserved behavior: fail-closed attestation, same-ID updates, sanitization, real-decoder conformance. They are not evidence of new-behavior fail-first. Four new exit-boundary cases fail at base. Every mechanical replay row is retained below; no skipped red claim.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: 13 touched test(s) pass against the pre-change code: test_activity_displays_decoded_codex_tools_without_lanes +7 more

**Choice**: discarded

**Rationale**: These 18 replay passes intentionally characterize preserved behavior: fail-closed attestation, same-ID updates, sanitization, real-decoder conformance. They are not evidence of new-behavior fail-first. Four new exit-boundary cases fail at base. Every mechanical replay row is retained below; no skipped red claim.

### [autonomous] 2026-10-17T09:30:09Z

**Decision**: Captured full suite had 7256 passed/1 terminal detach startup timeout; unchanged isolated case passed 1/0, independent Blake full suite passed 7257/0.

**Choice**: deferred

**Rationale**: Retain potential real-subprocess startup flake. Unchanged test file, earlier staging full suite exit 0, isolated failure passed immediately and independent full suite passed. No evidence of a PRD regression; do not weaken waits or assertions.

### [deferred] 2026-10-17T09:30:09Z

**Decision**: Claude's decoder gives every text and thinking block in one message the same `message_id` (verified: decoding `tests/fixtures/claude/v1/healthy.jsonl` line 2 yields text and thinking, both `message-1`). The exact-ID key at model.py:576 therefore lets the thinking block replace the text, and "Working on the sanitized fixture." never reaches the panel. The test at tests/tui/test_activity_projection.py:83 (claude param) pins this kind-changing replacement as intended, and no test decodes a real Claude multi-block message. Fix: key on (kind, id), or add a block index at the decoder edge. If neither, record it as a deferred design gap.

**Choice**: defer

**Rationale**: Confirmed decoded multi-block collision, but the explicit Projection contract requires a nonblank message_id to update its existing item regardless of kind. Design alternative 3 rejects new decoder identities. Changing to (kind,id) contradicts that contract. Defer this pre-existing design gap for a separate provider-edge design; retain HIGH severity and raw B1 fail. No finding is waived.

### [deferred] 2026-10-17T09:30:09Z

**Decision**: Codex command detail is `command\noutput`, and `display_text` strips the `\n`, so the operator sees the command and its output run together ("printf exampleexample"). The new test asserts that string as the expected value (tests/tui/test_rework_activity.py:122), which treats an inaccurate render as intent. That conflicts with the PRD metric that tools "render accurate detail". Fix: turn line breaks into a visible separator before sanitizing, or record a deferral and stop asserting the fused text.

**Choice**: defer

**Rationale**: Confirmed pre-existing newline concatenation. Projection and PRD require preservation of existing text sanitization; changing global display_text affects all panels. Defer a separately scoped separator design; retain the current regression assertion until behavior changes.

### [deferred] 2026-10-17T09:30:09Z

**Decision**: Tool identity still uses `display_text(str(tool_id))`, which sanitizes and truncates the ID. Message IDs were just fixed for the same problem (same defect class, bug-fix discipline). Real tool IDs are short today, so the impact is low.

**Choice**: defer

**Rationale**: Confirmed pre-existing tool identity collision class. Exact identity in this PRD names message_id only; preserving tool behavior avoids an opportunistic identity redesign. Record separately for follow-up.

### [deferred] 2026-10-17T09:30:09Z

**Decision**: The "N activity entries omitted" line is printed after all 20 lanes instead of right after the activity block. In a panel limited by height, it is the first line cut off, and it reads as if it belongs to the lanes. A test locks in this placement.

**Choice**: defer

**Rationale**: Clipping is confirmed as an existing constrained-height presentation limitation, explicitly recorded by design dispatch 2. Presentation contract appends both omission lines after activity and lanes; preserve placement and defer alternate compact presentation.

### [deferred] 2026-10-17T09:30:09Z

**Decision**: Exit-criteria run: the full `uv run pytest` gave 7249 passed and 2 failed, both in `test_ordinary_project_ui_failure_restores_pty_and_reuses_observer[construction|start]`. That file passed 14/14 when rerun alone. I ran ruff and mypy at the same time as the suite, so the failures look timing-sensitive under load, and this PRD does not touch the file. ruff check, ruff format --check, mypy and `uv build` all passed. The PRD's own test files passed 80/80. I did not run `uv sync --all-groups`.

**Choice**: defer

**Rationale**: Preserve the full-suite 7249/2 failure and isolated 14/14 success as a potential timing flake in unchanged viewer fallback. No evidence establishes a PRD regression. Fresh full-suite result is separately recorded below; retain flake follow-up even if it passes.

### [deferred] 2026-10-17T09:30:09Z

**Decision**: Cannot statically verify: fail-first replay of the changed tests against 65926983 (the replay was skipped because the worktree could not be created)

**Choice**: defer

**Rationale**: Verification limitation retained: old-code fail-first replay was blocked by worktree permissions. Bob names a multi-step checkout/copy/run procedure, not one exact allowed verification command, so not queued: command shape. Original build red checks and mutation evidence remain available; no claim of completed replay.

### [deferred] 2026-10-17T09:30:09Z

**Decision**: The recovery fix still leaves one gap in the exit race. After `cleanup_run_records` removes run.json, the supervisor process stays alive until the interpreter exits. A poll in that gap gets `ended=False`, an idle observation with `run_id=None`, and `state=None`. Because that identity no longer matches the selected run, `_observe` closes the follower and clears the session cache. The next poll is terminal but has no `_session_id`, so the final frame loses lanes, activity and provider. I confirmed this with a probe: I ran `Selected.finish()`, forced `_run_observation.process_matches` to return True for one poll, and polled again. `assert_final_telemetry` then failed with `'unknown' == 'selected-provider'`. The new tests miss this because `finish()` waits for the process to exit fully. Fix: clear the cache only when `selected.ended` is true or the observation shows a different active run (`observation.run_id` is not None and differs). Missing metadata alone should not clear it.

**Choice**: defer

**Rationale**: Confirmed cleanup-before-process-exit cache-loss edge. This predates and remains outside the activity projection contract; changing behavior when selected ownership metadata is absent needs a separate fail-closed observer contract covering replacement and malformed identities. Preserve the reported defect and probe; do not apply the suggested relaxed identity guard opportunistically. Correct consensus is Alice 1/3: Blake reported scope, Bob requested identity-guard coverage, not this defect.

### [deferred] 2026-10-17T09:30:09Z

**Decision**: Claude text and thinking blocks that share one `message.id` collapse into a single entry, and the later block overwrites the earlier one. Only a test comment ("Known R1 limitation") records this. docs/driver-protocol.md says only that "message updates use their full IDs", so operators aren't told a block can disappear.

**Choice**: defer

**Rationale**: Matches cycle-1 settled HIGH shared-message-ID design gap. Its test now characterizes real decoded blocks and explicitly records the limitation. Existing docs describe full-ID update semantics accurately; block-specific presentation and operator caveats belong with the already-deferred provider-edge design, not an identity change here. Keep original HIGH deferral unchanged.

### [deferred] 2026-10-17T09:30:09Z

**Decision**: `test_activity_window.py` imports the private helpers `_poll` and `_decoder` from sibling test modules (tests/tui/test_activity_window.py:19), which Pat retained as LOW

**Choice**: defer

**Rationale**: Known low-priority test-helper coupling follows existing sibling-helper precedent. Extracting a shared support module is a separate test-organization cleanup with no behavioral or acceptance defect. Preserve as a durable low follow-up rather than expand this bounded correction.

### [deferred] 2026-10-17T09:30:09Z

**Decision**: The run-identity half of the new cache-keep guard may have no test. The new tests pin the keep path through final telemetry, but none may fail if the condition shrinks to `if selected.ended:`

**Choice**: defer

**Rationale**: Known verification limitation for the separately deferred observer guard design. The suggested mutate/run/revert sequence is not one allowed verification command; not queued: command shape. No claim that replacement-identity coverage was verified.

### [deferred] 2026-10-17T09:30:09Z

**Decision**: Captured full suite had 7256 passed/1 terminal detach startup timeout; unchanged isolated case passed 1/0, independent Blake full suite passed 7257/0.

**Choice**: defer

**Rationale**: Retain potential real-subprocess startup flake. Unchanged test file, earlier staging full suite exit 0, isolated failure passed immediately and independent full suite passed. No evidence of a PRD regression; do not weaken waits or assertions.
