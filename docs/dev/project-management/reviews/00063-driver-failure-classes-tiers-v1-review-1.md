---
prd: docs/dev/project-management/prds/wip/00063-driver-failure-classes-tiers-v1.md
review: 1
date: 2026-10-29
head_sha: be6ce0951346402bb212b7d4b6d75cb9c14c3de3
codex_thread_id: 01a184de-f5f9-7871-914a-08f45ce01694
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: f118ec7f
  carl: 7dcf0593
---

# Review: 00063-driver-failure-classes-tiers-v1

Diff range: `f6f652f29bd89a4a69914ac1bb5329c335771fbf..be6ce0951346402bb212b7d4b6d75cb9c14c3de3`

codex_rung_guard: not fired

pack: failed (engram pack exit 1: not inside a registered repo; run `gita add /Users/bob/git/src/github.com/buvis/ovcaq`) — the review is degraded by the missing findings precedent, not invalid.

## Review Summary

Reviewed: 5 completed tasks
PRDs checked: 00063-driver-failure-classes-tiers-v1

### Agent Status

- Alice: ✅ Available (consensus lens, legacy engine)
- Blake: ✅ Available (blind lens, PRD-only)
- Bob: ✅ Available (doubt lens + de-slop, codex)
- Carl: ⚠️ Unavailable: gemini-run exit 1, backend=copilot model=gemini-3.8-flash, "You have exceeded your monthly quota". Retried once (exit 1, same reason). Not exit 4, so no batch-level latch was written.
- Eve: ⏸️ Disabled: resolved doubt reviewer is `codex` and the codex doubt-roster guard did not fire (no task was implemented by codex).

Consolidation ran through `consolidate_findings.py` over three reviewer outputs. No settled-decisions ledger exists (cycle 1), so the `--ledger`/`--ledger-dismiss` flags were omitted. The script merged Alice's and Blake's stale-fixture findings into R1 after citation-suffix stripping.


**Decision-gate merge, recorded loudly.** `consolidate_findings.py` merges paraphrases only when two reviewers name the same file, so four pairs of rows describing one defect each across two different file cells stayed separate, every one of them reading as single-voice. The gate's own standard for matching is issue text plus file, and `review-close` enforces the single-voice rule mechanically off the Consensus cell, so those rows are merged here and the cells now state the real agreement. The merges: Alice's supervisor-call-site finding with Bob's launch-routing-test finding (one defect: no Supervisor-level test of `default_tiers` routing); Alice's and Bob's CHANGELOG:51 findings (same wrong claim, same fix); Alice's, Blake's two and Bob's `docs/operations.md` findings (one under-documented file, four points); Alice's and Bob's `tests/drivers/test_adapter_failure_classes.py` findings (same file, same cut). Nothing was dropped in the merge: every merged row's issue cell carries all of its source findings' points, and `review-close` transcribes them into the task's `### Findings (verbatim)` block. Refs were renumbered in rendered row order after merging.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | 🟡 | The PRD asks to migrate every fixture and fake driver in the files marked "fixtures off the old tier keys". Several still use `sonnet`/`opus` tier tables and `PhaseSettings("sonnet"...)`: tests/runtime/test_supervisor_process.py:75, :161, :180; tests/integration/test_observer_terminal_cleanup.py:87, :348; tests/integration/test_supervisor_live_telemetry.py:188, :207. These fixtures still pass because they are self-consistent. Fixtures with the same stale keys outside the PRD's file list are tests/runtime/test_rework_thread_conflict.py:69, tests/integration/test_launcher_outcomes.py:57, tests/integration/test_terminal_lifecycle.py:236 and tests/tui/test_codex_projection.py:165. The ones routing through default phases now ignore the configured `model-s`/`model-o` and use the driver defaults. Migrate the PRD-listed files to `standard`/`deep`, and the others for the same reason. | tests/runtime/test_supervisor_process.py:75 | 4 | ALICE, BLAKE |
| R2 | [2/3] | 🟠 | No test proves the Supervisor passes the driver's `default_tiers` to `resolve_phase_route`. All four fake drivers carry an empty table; the `route` stand-in in test_supervisor_preflight defaults `default_tiers` to None; `test_unconfigured_project_routes_through_driver_default_tiers` calls `resolve_phase_route` directly, not through `Supervisor`. Deleting `default_tiers=` at both supervisor call sites would leave every test green, yet this is the PRD happy path. Add a Supervisor-level test with a fake whose `default_tiers` is non-empty and a project with no tier table, asserting preflight passes and `_attempt` launches with the mapped model. Separately, the unconfigured-project test at tests/runtime/test_adapter_launch_routing.py:192 bypasses Supervisor and the edge model-to-tier conversion by passing `route.tier` directly to `build_launch`: add an unconfigured Supervisor test for both drivers that captures build/review/done argv and exercises both route-resolution call sites. | src/ovcaq/runtime/supervisor.py:173 | 4 | ALICE, BOB |
| R3 | [2/3] | 🟡 | The breaking-change entry is inaccurate. It says a tiers table naming only models "no longer resolves the default routes". In fact the routes resolve silently to the driver's own models (`default_tiers` is merged under the table), so the operator's models are ignored. Task 5 required the note that such a table "now falls through to the driver's own models". Reword the entry to describe the silent fallback, and distinguish the built-in neutral keys from custom keys rather than requiring configured keys for neutral frontmatter floors. | CHANGELOG.md:51 | 5 | ALICE, BOB |
| R4 | [3/3] | 🟡 | docs/operations.md is under-documented and self-contradictory on four counts. (1) :82 says a tiers table "must now define standard and deep", then says a table with neither key "silently falls through to the driver's own models instead of failing"; the drivers merge `{**default_tiers, **settings.tiers}`, so no definition is required and the two sentences disagree. (2) Task 5 asked for the PRD frontmatter floor to be stated there as a rule — it applies only when its value is a tier key in the table, written with a neutral placeholder — and the amended sentence at :80-:87 adds no such rule; the existing "unavailable hint warns and applies no floor" is the only coverage. (3) The Risks section asks the same file to document the frontmatter-floor risk (a PRD naming a non-neutral default model warns unless the agent tier table maps it); only docs/driver-protocol.md:37-45 shows an example. (4) The explicitly required reserved literal `default` is not named. Fix all four in the generated documentation source `src/ovcaq/workflow_cli.py` and regenerate operations.md, keeping the driver-protocol reference and the provider-neutrality invariant. | docs/operations.md:80 | 5 | ALICE, BLAKE, BOB |
| R5 | [3/3] | 🟡 | Test bloat that does not pin this change, in one file. The replay shows 99 new tests in the failure-class file pass against the pre-change code, plus 5 in `test_claude_default_tiers_do_not_bypass_launch_validation`. The PRD requires one table test per driver plus the pinned negatives. The generated carrier-sentence, casing and pairwise-precedence suites exercise old markers such as `unauthorized`, `permission denied`, `timed out` and `agent loop died`. Keep rows that fail at base or that the PRD names as pins; cut the rest (about 300 lines). Separately, `test_codex_diagnostic_table_reaches_every_failure_class` at :384 checks only expected values in its own fixture, never classifier behavior: remove that redundant fixture-only test and retain the parametrized classifier assertions. | tests/drivers/test_adapter_failure_classes.py:461 | 1 | ALICE, BOB, mech-check |
| R6 | [1/3] | 🟡 | Possible scope drift. Task 5 said to touch no source file, but `WORKFLOW_INPUT_NOTES` in src/ovcaq/workflow_cli.py:34 was edited. This is the generated source of the operations.md text, so it is likely justified, but the edit should be called out. | src/ovcaq/workflow_cli.py:34 | 5 | ALICE |
| R7 | [1/3] | ⚪ | The docs sentence "the digit breaks no boundary after `429`" is muddled. The point is that `\b` does not hold between `429` and `0`. | docs/driver-protocol.md:90 | 5 | ALICE |
| R8 | [1/3] | ⚪ | Smaller deviations from the contract. The reserved literal is the private `_PROVIDER_DEFAULT_MODEL` rather than the contract's named constant. `build_launch` sets `model = None` instead of using the contract's conditional on the argv segment. Both are behaviour-equivalent. The optional fakes in tests/drivers/test_contract.py:34 and tests/drivers/test_discovery.py:25 still lack `default_tiers`. | src/ovcaq/drivers/codex.py:152 | 4 | ALICE |
| R9 | [1/3] | ⚪ | File sizes are close to the 800-line limit: src/ovcaq/runtime/supervisor.py is 782 lines, tests/runtime/test_supervisor.py 780 and tests/workflow/test_configuration.py 775. All are under the limit. | N/A | general | ALICE |
| R10 | [1/3] | ⚪ | src/ovcaq/config.py:33 adds an unspecified public constant, `NEUTRAL_TIERS`. It is derived from `DEFAULT_PHASE_TIERS` and used only by `workflow_settings`. It is small and harmless, but the PRD does not list it. | src/ovcaq/config.py:33 | 1 | BLAKE |
| R11 | [1/3] | 🟡 | 1 touched test passes against the pre-change code: test_installed_explicit_available_tiers_override_the_active_map | tests/packaging/test_workflow_inputs.py | general | mech-check |
| R12 | [1/3] | 🟡 | 1 touched test passes against the pre-change code: test_supplied_phase_settings_control_each_workflow_launch | tests/runtime/test_supervisor.py | general | mech-check |
| R13 | [1/3] | 🟡 | 1 touched test passes against the pre-change code: test_create_session_os_error_before_session_opens_reverts_a_fresh_batch | tests/runtime/test_supervisor_early_failure.py | general | mech-check |
| R14 | [1/3] | 🟡 | 3 touched tests pass against the pre-change code: test_preflight_resolves_routes_for_the_driver_agent, test_preflight_accepts_a_tier_only_the_agent_override_supplies, test_preflight_reports_the_override_tier_not_the_neutral_one | tests/runtime/test_supervisor_preflight.py | general | mech-check |
| R15 | [1/3] | 🟡 | 8 touched tests pass against the pre-change code: test_explicit_phase_mapping_rejects_extra_nonroutable_keys, test_explicit_phase_mapping_rejects_untyped_values, test_config_rejects_nonroutable_phase_tables and 5 more | tests/workflow/test_supervisor_configuration.py | general | mech-check |

R11-R15 are the fail-first replay block's `[MECH]` lines absorbed per step 6; R5 already named the two replay rows for test_adapter_failure_classes.py and test_claude_launch.py, so `mech-check` was appended to its finders instead of adding separate rows.

## Follow-up Tasks Created

None by this skill (PRD 00249 removed task creation here). The decision gate classifies these rows and makes the single `review-close` call.

## Alice

Consensus lens, implementation-aware, legacy engine. Nine findings; after the decision-gate merge they appear above as R1-R5 (merged rows) and R6-R9.

Alice's own notes: she verified the source changes in config.py, claude.py, codex.py, the `_FAILURE_MARKERS` table, `classify_failure`, base.py and the supervisor wiring against the design contract; they match, and the round trip through edge.py is consistent. She confirmed the integration/tui failures are environmental by re-running tests/integration/test_terminal_lifecycle.py (fails on `ps` PermissionError) and test_launcher_outcomes.py plus test_codex_projection.py (42 passed). She states she did not inspect five F results individually and assumed, without verifying, that they were the same `ps` denial.

R1: fail
R2: fail
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

## Blake

Blind lens, PRD-only: no diff, no file list, no review history, no design doc. He located the code himself. Four findings; after the merge they appear above as R1, R4 (two of his points) and R10.

Everything else matched the spec. He confirmed: all Claude spec markers present at src/ovcaq/drivers/claude_events.py:223-272 with precedence unchanged and the non-string result still yielding "Malformed terminal error evidence"; the Codex authentication and connectivity alternations at src/ovcaq/drivers/codex_events.py:310,330-331 with the word-boundary wrapper unchanged; `DEFAULT_PHASE_TIERS` at src/ovcaq/config.py:32 with the neutral values, removed from src/ovcaq/drivers/__init__.py, and no old tier key in shared modules; `workflow_settings` unioning the neutral keys into `available_tiers` at src/ovcaq/config.py:314; `AgentDriver.default_tiers` at src/ovcaq/drivers/base.py:87; both driver tables and both constructor merges; `resolve_phase_route` taking `default_tiers` at src/ovcaq/config.py:632-668; both supervisor call sites at src/ovcaq/runtime/supervisor.py:173,482; `DRIVER_API_VERSION` unchanged; all seven named tests present; both doc grep acceptance checks satisfied; all three CHANGELOG entry kinds present; working tree clean. He ran two narrow slices (2120 passed, then 1731 passed) rather than the full suite, and did not run ruff or mypy.

B1: pass
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
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

Doubt lens plus de-slop, codex, static-only sandbox. Prompt was the inlined shape (review context and full diff inlined verbatim, 236892 bytes). Four findings; after the merge they appear above as R2, R3, R4 and R5. His dispatch row's `prompt_bytes` reflects the staged render, not the inlined prompt actually sent.

FIX: his four findings, merged above into R2, R3, R4 and R5.
VERIFY: (none).
KNOWN: (none).

No verification-check queue file was written for this cycle: Bob's VERIFY bucket is empty, and the queue's `source` reserves `"bob"` in any case.

R1: fail
R2: fail
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

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Not run. `gemini-run.sh` exited 1 on both the first dispatch and the single retry, with `backend=copilot model=gemini-3.8-flash` and "You have exceeded your monthly quota". That is a runtime failure, not the exit-4 permanent-configuration class, so no `state.batch.unavailable_reviewers` latch was written and a later cycle will try him again. The diff is backend and CLI code with no UI surface, so his frontend and design specialism had little to add here; the cycle is degraded by one voice, not invalid.

Verdict: 15 findings
Tests: 8546 passed, 3 failed, 14 errors (suite run this cycle; `uv run pytest -q` exit 1; all 3 failures and all 14 errors are in tests/integration/test_terminal_lifecycle.py, the documented /bin/ps sandbox denial; `autopilot verify` parsed no counts from this run and wrote no last-verification.json record, so the counts above were read from its log at docs/dev/tmp/gate-be6ce09.log:3592)
