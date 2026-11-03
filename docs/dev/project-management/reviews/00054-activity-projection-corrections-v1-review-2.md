---
prd: docs/dev/project-management/prds/wip/00054-activity-projection-corrections-v1.md
review: 2
date: 2026-10-17
head_sha: b593719ff4610b92f0aa002f29a962ce1f4debc7
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
dispatch_rows:
  bob: e5a53b9a
---

# Review: Faithful recent activity display

Diff range: 76972b520dfd3d3004aeed4a18689e921ec56aec..b593719ff4610b92f0aa002f29a962ce1f4debc7
Full PRD work range: 65926983d26de98d55692fd1232ad12a1de48caf..b593719ff4610b92f0aa002f29a962ce1f4debc7

codex_rung_guard: not fired
provider_review_guard: satisfied
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/alice-output-00054-c2-20261017.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/blake-output-00054-c2-20261017.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00054-c2-20261017.txt.receipt.json

carl: skipped (batch policy skip since cycle 1 of 00054-activity-projection-corrections-v1.md; backend availability not determined)

The model-provider guard supersedes the legacy launcher guard. Eve did not run. All three independent fresh reviewer processes served claude-opus-5-5, helper-requested xhigh, with isolated full source personas/rubrics. Blake received only PRD and repository access. Source sessions, hashes and receipts are retained in 00054-cycle2-review-evidence. No implementation changed this session. State schema and 7/7 task counts pass. Host review-route validates all 18 contributing model evidence rows, including tests, prior attempts, micro edits and recovery. Pack failed because repository is not registered with engram; prompts used the explicit no-pack sentinel. No stage errors. Optional Carl's prior policy denial remains intact; no dispatch or backend-availability claim.

Verification: staging full suite exit 0, counts unavailable because its adapter requires PASS/FAIL/SKIP/EXIT. Coordinator capture then had 7256 passed/1 failed (terminal detach startup timeout), with raw output/XML; the failed case passed 1/0 immediately unchanged. Blake independently ran and awaited the full suite: 7257 passed, 0 failed, 0 skipped, 2 cleanup warnings, 295.65s; raw line 279 is hash-bound in reports/00054-cycle2-verification.json. He also ran sync, ruff check/format, mypy and build successfully. No merged or invented 7257/0 coordinator result. Last-verification identifies the independent raw source and retains earlier run outcomes separately.

## Consolidated Findings

Consolidation used the source script, then corrected its file-level overmerge: R1 contains only Alice's cache-loss report (1/3), not Blake's scope objection or Bob's missing-guard-test question. Those distinct raw findings are restored as R11/R12. R2/R3 remain visible duplicates across source citations. Script output and stderr are archived verbatim. All raw findings and mechanical rows survive.

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [1/3] | 🟡 | The recovery fix still leaves one gap in the exit race. After `cleanup_run_records` removes run.json, the supervisor process stays alive until the interpreter exits. A poll in that gap gets `ended=False`, an idle observation with `run_id=None`, and `state=None`. Because that identity no longer matches the selected run, `_observe` closes the follower and clears the session cache. The next poll is terminal but has no `_session_id`, so the final frame loses lanes, activity and provider. I confirmed this with a probe: I ran `Selected.finish()`, forced `_run_observation.process_matches` to return True for one poll, and polled again. `assert_final_telemetry` then failed with `'unknown' == 'selected-provider'`. The new tests miss this because `finish()` waits for the process to exit fully. Fix: clear the cache only when `selected.ended` is true or the observation shows a different active run (`observation.run_id` is not None and differs). Missing metadata alone should not clear it. | src/ovcaq/tui/model.py:468 | 4 | ALICE |
| R2 | [2/3] | ⚪ | The supervisor exit-race fix (commit 00b2fdf: `_selected_state` resampling, deferring the terminal transition, keeping the session cache) changes production lifecycle observation code. That is outside PRD 00054, whose Risks section says "No lifecycle decisions in TUI", yet it is credited to task 4, which only covers tests/tui. It is needed for the full-suite exit gate and is documented in reports/00054-recovery-progress.md, but it has no PRD or design record of its own to trace it to. | src/ovcaq/runtime/_run_observation.py:102 | 4 | ALICE, BOB |
| R3 | [1/3] | 🟡 | Scope creep: commit 00b2fdf changes when the runtime treats a sample as terminal, which is lifecycle observation. `_selected_state` now re-samples process death, and `observe_selected_run` holds back a live-to-terminal frame as non-terminal. The PRD lists only `tui/{model.py,panels.py}`, forbids lifecycle changes and says to keep the 00051–00053 terminal semantics. The fix is tested but has no spec authority here. | src/ovcaq/runtime/_run_observation.py:106 | general | BLAKE |
| R4 | [1/3] | 🟡 | The lane window shows the first 20 lanes by insertion order, so the oldest-started lanes stay visible. Once a run has more than 20 lanes, the newest (running) lanes show up only in the "N lanes omitted" count. This repeats the R10 symptom ("hides recent work behind old … lanes") for lane-heavy runs. It is a literal reading of "existing order" and the design doc chose it, but it works against "keep the current activity visible". | src/ovcaq/tui/panels.py:99 | Phase 1 | BLAKE |
| R5 | [1/3] | 🟡 | Commit 00b2fdf is a `fix(tui)` with a user-visible effect: a viewer whose supervisor exits mid-poll now shows the attested final outcome, where before it froze on an uncertain unknown frame. It has no CHANGELOG entry. The blocking changelog rule requires one, and this PRD's own unreleased fixes got entries at CHANGELOG.md:43-45 | CHANGELOG.md:41 | general | BOB |
| R6 | [1/3] | ⚪ | Claude text and thinking blocks that share one `message.id` collapse into a single entry, and the later block overwrites the earlier one. Only a test comment ("Known R1 limitation") records this. docs/driver-protocol.md says only that "message updates use their full IDs", so operators aren't told a block can disappear. | tests/tui/test_activity_projection.py:98 | Phase 0 | BLAKE |
| R7 | [1/3] | ⚪ | `original = replace(changed)` followed by `assert changed == original` can never fail. `replace` makes a shallow copy that shares the same tuples, and `ProjectView`, `ActivityItem` and `ActivityLane` are all `frozen=True, slots=True` (src/ovcaq/tui/model.py:75, src/ovcaq/tui/model.py:83, src/ovcaq/tui/model.py:113). R9's prescribed fix kept this check, so R16's claim still holds | tests/tui/test_activity_window.py:220 | 4 | BOB |
| R8 | [1/3] | ⚪ | Cannot statically verify: full suite green at b593719. The test gate reported exit 0 with no counts | N/A | general | BOB |
| R9 | [1/3] | ⚪ | Fail-first replay: 18 touched tests pass against the old code. All are guard tests or tests rebuilt on decoded payloads for existing or settled behavior: the attestation-damage guards, the R1 characterization, the R6 redaction guard and the R12 decoded rewrites | N/A | general | BOB |
| R10 | [1/3] | ⚪ | `test_activity_window.py` imports the private helpers `_poll` and `_decoder` from sibling test modules (tests/tui/test_activity_window.py:19), which Pat retained as LOW | tests/tui/test_activity_window.py:19 | 4 | BOB |
| R11 | [1/3] | 🟡 | The same out-of-scope commit adds a second session-retention rule to the observer. It keeps the follower and cache when the run's process identity matches, so the TUI model now decides retention on process identity, beyond the activity-projection repair. | src/ovcaq/tui/model.py:468 | general | BLAKE |
| R12 | [1/3] | ⚪ | The run-identity half of the new cache-keep guard may have no test. The new tests pin the keep path through final telemetry, but none may fail if the condition shrinks to `if selected.ended:` | src/ovcaq/tui/model.py:468 | 4 | BOB |
| R13 | [1/3] | 🟡 | 2 touched test(s) pass against the pre-change code: test_exit_during_poll_with_invalid_attestation_still_ends_uncertain | tests/integration/test_observer_exit_during_poll.py | general | mech-check |
| R14 | [1/3] | 🟡 | 1 touched test(s) pass against the pre-change code: test_decoded_claude_text_and_thinking_share_the_same_update_identity | tests/tui/test_activity_projection.py | general | mech-check |
| R15 | [1/3] | 🟡 | 2 touched test(s) pass against the pre-change code: test_both_windows_report_separate_omission_counts_without_changing_history, test_decoded_warning_detail_redacts_synthetic_credentials_before_rendering | tests/tui/test_activity_window.py | general | mech-check |
| R16 | [1/3] | 🟡 | 13 touched test(s) pass against the pre-change code: test_activity_displays_decoded_codex_tools_without_lanes +7 more | tests/tui/test_rework_activity.py | general | mech-check |
| R17 | [1/3] | ⚪ | Captured full suite had 7256 passed/1 terminal detach startup timeout; unchanged isolated case passed 1/0, independent Blake full suite passed 7257/0. | tests/integration/test_terminal_lifecycle.py:368 | general | verification |

### Auto-dismissed (ledger)

- [BLAKE] ⚪ The tool identity key still passes through `display_text`, which cuts at 512 characters. Two distinct long tool IDs with the same prefix would merge into one entry. This is the same truncation-merge defect the PRD fixed for message IDs (real IDs are short, so the risk is low). | File: src/ovcaq/tui/model.py:604 — Confirmed pre-existing tool identity collision class. Exact identity in this PRD names message_id only; preserving tool behavior avoids an opportunistic identity redesign. Record separately for follow-up.
- [BLAKE] ⚪ The "unchanged retained ProjectView history" check can't fail. `original = replace(changed)` shares the same immutable tuples, so `changed == original` always holds. Retention beyond the 20-entry window is tested only in the projection eviction test, never together with rendering. | File: tests/tui/test_activity_window.py:198 — Duplicate of actionable R9; its task carries duplicate assertion cleanup. Raw Bob finding retained.

## Alice

Independent Anthropic claude-opus-5-5, helper-requested xhigh; raw verdicts verbatim below.

### Anthropic

[ALICE] 🟡 The recovery fix still leaves one gap in the exit race. After `cleanup_run_records` removes run.json, the supervisor process stays alive until the interpreter exits. A poll in that gap gets `ended=False`, an idle observation with `run_id=None`, and `state=None`. Because that identity no longer matches the selected run, `_observe` closes the follower and clears the session cache. The next poll is terminal but has no `_session_id`, so the final frame loses lanes, activity and provider. I confirmed this with a probe: I ran `Selected.finish()`, forced `_run_observation.process_matches` to return True for one poll, and polled again. `assert_final_telemetry` then failed with `'unknown' == 'selected-provider'`. The new tests miss this because `finish()` waits for the process to exit fully. Fix: clear the cache only when `selected.ended` is true or the observation shows a different active run (`observation.run_id` is not None and differs). Missing metadata alone should not clear it. | File: src/ovcaq/tui/model.py:468 | Task: 4
[ALICE] ⚪ The supervisor exit-race fix (commit 00b2fdf: `_selected_state` resampling, deferring the terminal transition, keeping the session cache) changes production lifecycle observation code. That is outside PRD 00054, whose Risks section says "No lifecycle decisions in TUI", yet it is credited to task 4, which only covers tests/tui. It is needed for the full-suite exit gate and is documented in reports/00054-recovery-progress.md, but it has no PRD or design record of its own to trace it to. | File: src/ovcaq/runtime/_run_observation.py:102 | Task: 4

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

Status of prior findings:
- **Resolved:** R2, R4, R5, R6, R9, R10, R12.
  - R2: the 512-char bound and ellipsis now match `display_text` at src/ovcaq/tui/model.py:136.
  - R4: real Claude multi-block and literal-message frames are now decoded.
  - R5: the `ACTIVITY_WINDOW` constant is in place.
  - R6: credentials in decoded warning detail are redacted through to the render.
  - R9: one equality check is left.
  - R10: the detail assertions now run unconditionally.
  - R12: the claude error and plan cases now use real decoder shapes.
- **Deferred, still reproduces as recorded:** R1, R3, R7 and R13. The R9 rubric fail keeps the settled R1 verdict.
- **Not re-raised:** the fail-first [MECH] lines. The test-only rework and the fail-closed attestation guards pass at base by design.

Checks run:
- PRD test files: 80 passed.
- tests/tui plus the observer-cleanup, viewer-fallback and exit-during-poll integration tests: 427 passed.
- ruff check, ruff format --check and mypy all clean.
- I did not run the full suite, because the coordinator's capture run is in progress. I removed the probe files afterwards.

## Blake

Independent Anthropic claude-opus-5-5, helper-requested xhigh; raw verdicts verbatim below.

### Anthropic

[BLAKE] 🟡 Scope creep: commit 00b2fdf changes when the runtime treats a sample as terminal, which is lifecycle observation. `_selected_state` now re-samples process death, and `observe_selected_run` holds back a live-to-terminal frame as non-terminal. The PRD lists only `tui/{model.py,panels.py}`, forbids lifecycle changes and says to keep the 00051–00053 terminal semantics. The fix is tested but has no spec authority here. | File: src/ovcaq/runtime/_run_observation.py:106 | Task: general
[BLAKE] 🟡 The same out-of-scope commit adds a second session-retention rule to the observer. It keeps the follower and cache when the run's process identity matches, so the TUI model now decides retention on process identity, beyond the activity-projection repair. | File: src/ovcaq/tui/model.py:468 | Task: general
[BLAKE] 🟡 The lane window shows the first 20 lanes by insertion order, so the oldest-started lanes stay visible. Once a run has more than 20 lanes, the newest (running) lanes show up only in the "N lanes omitted" count. This repeats the R10 symptom ("hides recent work behind old … lanes") for lane-heavy runs. It is a literal reading of "existing order" and the design doc chose it, but it works against "keep the current activity visible". | File: src/ovcaq/tui/panels.py:99 | Task: Phase 1
[BLAKE] ⚪ Claude text and thinking blocks that share one `message.id` collapse into a single entry, and the later block overwrites the earlier one. Only a test comment ("Known R1 limitation") records this. docs/driver-protocol.md says only that "message updates use their full IDs", so operators aren't told a block can disappear. | File: tests/tui/test_activity_projection.py:98 | Task: Phase 0
[BLAKE] ⚪ The tool identity key still passes through `display_text`, which cuts at 512 characters. Two distinct long tool IDs with the same prefix would merge into one entry. This is the same truncation-merge defect the PRD fixed for message IDs (real IDs are short, so the risk is low). | File: src/ovcaq/tui/model.py:604 | Task: Phase 0
[BLAKE] ⚪ The "unchanged retained ProjectView history" check can't fail. `original = replace(changed)` shares the same immutable tuples, so `changed == original` always holds. Retention beyond the 20-entry window is tested only in the projection eviction test, never together with rendering. | File: tests/tui/test_activity_window.py:198 | Task: Phase 1

Checks I ran myself on HEAD b593719:
- `uv sync --all-groups`: ok.
- The three PRD test files: 80 passed.
- Full `uv run pytest`: 7257 passed, 0 failed, 0 skipped. There were 2 pytest temp-directory cleanup warnings.
- `ruff check`, `ruff format --check` and `mypy src/ovcaq`: all clean.
- `uv build` (written to /tmp/ovcaq-blake-build): ok.

Spec items I confirmed in the code:
- Messages use `text` when it is not null, otherwise `detail`.
- A message ID that is blank or missing gets a sequence key, so it can't replace another entry.
- Real IDs are used whole, not truncated.
- The invented tool `input` fallback is gone.
- The 256-entry retention limit and eviction work as before.
- Activity renders newest-first, capped at 20, ahead of the lanes, and both omission counts appear.
- The docs name `lanes-matched.jsonl`, and the in-place and lanes-only claims are gone.
- The TUI code contains no provider names.

B1: pass
B2: pass
B3: pass
B4: pass
B5: pass
B6: fail
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: pass
B16: pass
B17: pass
B18: pass
B19: pass

## Bob

Independent Anthropic claude-opus-5-5, helper-requested xhigh; raw verdicts verbatim below.

### Anthropic

Rework check done. Prior-cycle findings: R2, R4, R5, R6, R10 and R12 are fixed. R9 got the fix it asked for, but one assert that can never fail is still there (finding 2). The settled deferrals (R1, R3, R7, R13, R14, R20) were not re-raised. The new viewer exit-race fix looks correct: all four exit points it handles fail against the old code, and the cases with missing or damaged attestation still end as unknown. It has no changelog entry and no task of its own.

[BOB] 🟡 Commit 00b2fdf is a `fix(tui)` with a user-visible effect: a viewer whose supervisor exits mid-poll now shows the attested final outcome, where before it froze on an uncertain unknown frame. It has no CHANGELOG entry. The blocking changelog rule requires one, and this PRD's own unreleased fixes got entries at CHANGELOG.md:43-45 | File: CHANGELOG.md:41 | Task: general
[BOB] ⚪ `original = replace(changed)` followed by `assert changed == original` can never fail. `replace` makes a shallow copy that shares the same tuples, and `ProjectView`, `ActivityItem` and `ActivityLane` are all `frozen=True, slots=True` (src/ovcaq/tui/model.py:75, src/ovcaq/tui/model.py:83, src/ovcaq/tui/model.py:113). R9's prescribed fix kept this check, so R16's claim still holds | File: tests/tui/test_activity_window.py:220 | Task: 4
[BOB] ⚪ Production lifecycle-observation changes (src/ovcaq/runtime/_run_observation.py:106, src/ovcaq/runtime/_run_observation.py:156, src/ovcaq/tui/model.py:468) are credited to task 4. That task is tests-only and its boundary says "Do not expand this task beyond its quoted findings". No task in PRD 00054 covers the exit race | File: src/ovcaq/runtime/_run_observation.py:106 | Task: 4
[BOB] ⚪ The run-identity half of the new cache-keep guard may have no test. The new tests pin the keep path through final telemetry, but none may fail if the condition shrinks to `if selected.ended:` | File: src/ovcaq/tui/model.py:468 | Task: 4
[BOB] ⚪ Cannot statically verify: full suite green at b593719. The test gate reported exit 0 with no counts | File: N/A | Task: general
[BOB] ⚪ Fail-first replay: 18 touched tests pass against the old code. All are guard tests or tests rebuilt on decoded payloads for existing or settled behavior: the attestation-damage guards, the R1 characterization, the R6 redaction guard and the R12 decoded rewrites | File: N/A | Task: general
[BOB] ⚪ `test_activity_window.py` imports the private helpers `_poll` and `_decoder` from sibling test modules (tests/tui/test_activity_window.py:19), which Pat retained as LOW | File: tests/tui/test_activity_window.py:19 | Task: 4

FIX:
- Fix commit has no changelog entry — CHANGELOG.md:41 — add under Fixed: `- **tui**: keep observing when the selected supervisor exits mid-poll, so viewers show its attested final outcome and telemetry instead of an uncertain frame.`
- Assert that can never fail — tests/tui/test_activity_window.py:220 — delete line 198 (`original = replace(changed)`) and line 220. The frozen types already guarantee immutability, and `text == _render(changed)` stays.
- Production fix filed under a tests-only task — src/ovcaq/runtime/_run_observation.py:106 — record the exit-race repair (00b2fdf) as its own task, or as the R14 follow-up closure, through the state CLI or ledger. Keep it off task 4.

VERIFY:
- Untested identity half of the guard — change src/ovcaq/tui/model.py:468 to `if selected.ended:`, run `uv run pytest tests/tui tests/integration -q`, then revert. If all tests pass, add a test where a non-terminal invalid sample with no matching run/process identity clears the session cache.
- Full suite at b593719 — confirm the coordinator's foreground capture reports a pytest summary line with 0 failed and 0 errors.

KNOWN:
- 18 touched tests pass against the old code — they are guard, characterization or decoded-payload rewrites of existing or settled behavior. The 4 exit-point params that carry this cycle's new behavior fail against the old code as they should.
- Private helpers imported across test modules — this follows precedent from cycle 1 (tests/tui/test_activity_projection.py:15 imports from test_rework_activity). Moving them into tests/tui/model_support.py is a separate cleanup.

R1: pass
R2: fail
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

## Decision gate

- R1 — defer: Confirmed cleanup-before-process-exit cache-loss edge. This predates and remains outside the activity projection contract; changing behavior when selected ownership metadata is absent needs a separate fail-closed observer contract covering replacement and malformed identities. Preserve the reported defect and probe; do not apply the suggested relaxed identity guard opportunistically. Correct consensus is Alice 1/3: Blake reported scope, Bob requested identity-guard coverage, not this defect.
- R2 — discard: The operator explicitly authorized verification recovery before this review (session contract card and reports/00054-recovery-progress.md). Commit 00b2fdf is that bounded recovery, with task-4 attempt 3 and exact model provenance, not an opportunistic module extraction. This audit is the durable scope addendum: preserve coherent selected-run attestation and final telemetry without changing lifecycle state or control policy. No second liveness algorithm was added.
- R3 — discard: Same scope concern as R2; operator recovery authority supersedes the original tests-only task boundary. Raw B6 fail remains unchanged. Shared runtime observes ownership; TUI consumes that model. No requirement or task history is rewritten.
- R4 — discard: PRD explicitly says at most 20 lanes in their existing order. The design deliberately fixes this policy. Changing to newest lanes would contradict that explicit requirement; activity itself is newest-first.
- R5 — discard: CHANGELOG already has the Unreleased Fixed entry: retain selected final state and telemetry after supervisor cleanup, reject replacement evidence, and render terminal outcomes before viewers exit. It covers exactly this regression correction. The changelog requires notable changes, not duplicate bullets for every repair commit; no missing user-visible behavior description remains.
- R6 — defer: Matches cycle-1 settled HIGH shared-message-ID design gap. Its test now characterizes real decoded blocks and explicitly records the limitation. Existing docs describe full-ID update semantics accurately; block-specific presentation and operator caveats belong with the already-deferred provider-edge design, not an identity change here. Keep original HIGH deferral unchanged.
- R7 — discard: Repeat of cycle-1 R16/R9 adjudication: the required fix removed duplicate equality checks while preserving one snapshot check, exactly as its task requested. Blake same finding was mechanically ledger-dismissed. Frozen tuple models make mutation unavailable through the supported interface; retained history and over-window bounds are covered by projection/window tests. No new defect or reason invalidating that settled disposition is shown; preserve raw R2 fail.
- R8 — discard: Resolved by independently captured Blake full-suite tool evidence: 7257 passed, 0 failed, 0 skipped at reviewed HEAD. Coordinator capture 7256/1 and targeted 1/0 are separately retained; no failed run is rewritten.
- R9 — discard: These 18 replay passes intentionally characterize preserved behavior: fail-closed attestation, same-ID updates, sanitization, real-decoder conformance. They are not evidence of new-behavior fail-first. Four new exit-boundary cases fail at base. Every mechanical replay row is retained below; no skipped red claim.
- R10 — defer: Known low-priority test-helper coupling follows existing sibling-helper precedent. Extracting a shared support module is a separate test-organization cleanup with no behavioral or acceptance defect. Preserve as a durable low follow-up rather than expand this bounded correction.
- R11 — discard: Same authorized recovery scope disposition as R2/R3. Runtime supplies validated selected identity; model cache retention does not decide lifecycle transitions.
- R12 — defer: Known verification limitation for the separately deferred observer guard design. The suggested mutate/run/revert sequence is not one allowed verification command; not queued: command shape. No claim that replacement-identity coverage was verified.
- R13 — discard: These 18 replay passes intentionally characterize preserved behavior: fail-closed attestation, same-ID updates, sanitization, real-decoder conformance. They are not evidence of new-behavior fail-first. Four new exit-boundary cases fail at base. Every mechanical replay row is retained below; no skipped red claim.
- R14 — discard: These 18 replay passes intentionally characterize preserved behavior: fail-closed attestation, same-ID updates, sanitization, real-decoder conformance. They are not evidence of new-behavior fail-first. Four new exit-boundary cases fail at base. Every mechanical replay row is retained below; no skipped red claim.
- R15 — discard: These 18 replay passes intentionally characterize preserved behavior: fail-closed attestation, same-ID updates, sanitization, real-decoder conformance. They are not evidence of new-behavior fail-first. Four new exit-boundary cases fail at base. Every mechanical replay row is retained below; no skipped red claim.
- R16 — discard: These 18 replay passes intentionally characterize preserved behavior: fail-closed attestation, same-ID updates, sanitization, real-decoder conformance. They are not evidence of new-behavior fail-first. Four new exit-boundary cases fail at base. Every mechanical replay row is retained below; no skipped red claim.
- R17 — defer: Retain potential real-subprocess startup flake. Unchanged test file, earlier staging full suite exit 0, isolated failure passed immediately and independent full suite passed. No evidence of a PRD regression; do not weaken waits or assertions.

No unresolved CRITICAL/HIGH remains. The original shared-message HIGH remains a settled deferral, never downgraded. The remaining observer race and guard-design verification limitation are explicitly deferred with scope/safety reasons. No actionable in-scope Medium/Low remains, so the tail sweep has zero selected findings and creates no tasks. Cap 2 is unchanged. No cycle increment, provenance rewrite, repair or new review waiver.

Verification queue: empty. Bob's mutation/run/revert procedure is not queued (command shape); his full-suite concern is resolved by the independent raw successful result. No previous-cycle checks exist. All four mechanical replay rows are intentional guard/characterization/conformance passes and are explicitly adjudicated above. Mechanical tautology detector produced no findings.

Verdict: 17 findings
Tests: 7257 passed, 0 failed, 0 skipped (suite run this cycle by Blake; raw tool result and hash retained)
