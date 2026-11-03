---
prd: docs/dev/project-management/prds/wip/00063-driver-failure-classes-tiers-v1.md
review: 2
date: 2026-10-29
head_sha: 9ec3396301866ed06d5ec006e041f1452cedd65d
codex_thread_id: 01a184de-f5f9-7871-914a-08f45ce01694
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: ab74df7a
  carl: 4fe0445b
---

# Review: 00063-driver-failure-classes-tiers-v1 (cycle 2)

Diff range: `be6ce0951346402bb212b7d4b6d75cb9c14c3de3..9ec3396301866ed06d5ec006e041f1452cedd65d` (incremental — the four cycle-1 rework commits)

codex_rung_guard: not fired

pack: failed (engram pack exit 1: not inside a registered repo; run `gita add /Users/bob/git/src/github.com/buvis/ovcaq`) — the review is degraded by the missing findings precedent, not invalid.

## Review Summary

Reviewed: 9 completed tasks (4 of them this cycle's rework: 02e9e13, 18468cf, 2efb001, 9ec3396)
PRDs checked: 00063-driver-failure-classes-tiers-v1

### Agent Status

- Alice: ✅ Available (consensus lens, legacy engine, incremental scope)
- Blake: ✅ Available (blind lens, PRD-only)
- Bob: ✅ Available (doubt lens + de-slop, codex, resumed thread 01a184de)
- Carl: ⚠️ Unavailable: gemini-run exit 1, backend=copilot model=gemini-3.8-flash, "You have exceeded your monthly quota". Retried once (exit 1, same reason) and the `-o` file was written empty, so he was not consolidated. Not exit 4, so no batch-level latch was written — the same one-off quota failure as cycle 1.
- Eve: ⏸️ Disabled: resolved doubt reviewer is `codex` and the codex doubt-roster guard did not fire (no task was implemented by codex).

Consolidation ran through `consolidate_findings.py` over three reviewer outputs, with `--ledger`/`--ledger-dismiss BLAKE` against the cycle-1 settled ledger (10 entries). The script printed no `### Auto-dismissed (ledger)` section.

The two mechanical blocks were empty this cycle: no tautological test shapes and no fail-first replay rows, so no `[MECH]` findings were absorbed. No `checks-1.json` queue exists, so nothing was carried forward.

**Decision-gate merge, recorded loudly.** `consolidate_findings.py` merges paraphrases only when two reviewers name the same file AND it folds them onto one row; it kept Bob's R7 and Alice's R8 separate because their severity cells differ, even though both name `tests/runtime/test_adapter_launch_routing.py:241` and state the same defect (prior R2's second half — no unconfigured Supervisor run through the real bundled drivers). The gate's own matching standard is issue text plus file, so those two are treated as one two-voice 🟡 row below, rendered under Bob's ref `R7` with Alice's wording folded in (her separate `R8` row is therefore absent from the table by design, and no row is numbered R8). Nothing was dropped: both reviewers' wording is retained.

**Working-tree note.** Alice ran two deliberate mutation checks and one classifier replay in the main checkout, which left `src/ovcaq/drivers/{claude,codex}_events.py` staged-reverted for part of the cycle; this blocked the first `autopilot verify` call with `dirty: true`. She restored the tree (`git status --porcelain` empty) and the gate was re-run clean at the same HEAD. No commit was affected.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | 🟡 | R3 only half fixed: the entry still ends "A PRD frontmatter tier floor must also name a key the table defines", which is false for the neutral keys — `workflow_settings` unions `NEUTRAL_TIERS` into `available_tiers` (src/ovcaq/config.py:315), so a `standard`/`deep` floor applies with no `[agents.<agent>.tiers]` table at all (frontmatter.py:136). docs/operations.md:84 states it correctly; make the CHANGELOG match, e.g. "A PRD frontmatter tier floor must name `standard`, `deep`, or a key the table defines." Bob's wording: replace it with "Neutral frontmatter floors work without configuration; custom floors require a configured tier key." | CHANGELOG.md:51 | 7 | ALICE, BOB |
| R2 | [1/3] | 🟠 | Reclassifying 429 as rate_limit makes a Claude rate limit halt the run immediately: with no reset banner `summary.rate_limit_reset_at` is None, so `_failure_decision` returns HALT "No bounded rate-limit retry remains" with zero attempts, where the pre-change `agent` class got `died_retries` first. The PRD's premise (a 429 should reach the bounded wait) is still unmet for the quoted diagnostic "HTTP 429 Too Many Requests", and no test covers the end-to-end rate-limit outcome for Claude | src/ovcaq/runtime/decision.py:197 | Phase 0 task 1 | BLAKE |
| R7 | [2/3] | 🟡 | Prior R2 is only partially resolved: the new test verifies both Supervisor call sites but drives the fake `Driver`, so no unconfigured Supervisor run exercises ClaudeDriver/CodexDriver argv, the edge `_map_model_to_tier` round trip for the neutral keys (including the Codex `default` collapse), or the `done` phase (the run stops after build and review). Add unconfigured Supervisor coverage for Claude and Codex, capturing build/review/done argv through the real driver construction path. Behavior is correct by inspection; the gap is coverage only. | tests/runtime/test_adapter_launch_routing.py:241 | 6 | BOB, ALICE |
| R3 | [1/3] | 🟡 | Claude classification matches by plain substring with no word boundary, unlike Codex, so a failing build session whose result text merely mentions OAuth ("the oauth_handler test failed") classifies as authentication and halts for operator access; "rate limit" or "getaddrinfo" in prose likewise reroutes. The PRD's marker-over-reach mitigation ("the table test includes the negative rows") is satisfied for Codex (rows at tests/drivers/test_adapter_failure_classes.py:324) but the Claude table ships no glued-identifier negative rows for the new markers | src/ovcaq/drivers/claude_events.py:223 | Phase 0 task 1 | BLAKE |
| R4 | [1/3] | 🟡 | "HTTP 4290" classifies as rate_limit and is locked in by a test comment as an "accepted asymmetry", which contradicts the hold 00056 rule the PRD pins ("numeric codes keep their http or status context") — Codex rejects the same shape at tests/drivers/test_adapter_failure_classes.py:323 | tests/drivers/test_adapter_failure_classes.py:482 | Phase 0 task 1 | BLAKE |
| R5 | [1/3] | 🟡 | Docs claim `default_tiers` is "required at DRIVER_API_VERSION 2", but `_register_driver` never validates the attribute and the version was deliberately not bumped; a third-party plugin already built against API 2 passes discovery and then raises a bare AttributeError inside `Supervisor.preflight` instead of a DriverDiscoveryError | src/ovcaq/drivers/base.py:129 | Phase 1 task 2 | BLAKE |
| R6 | [1/3] | 🟡 | Fail-silent config path: an existing project whose `[agents.<agent>.tiers]` defines only model-name keys now resolves build/review/done through the driver's own models instead of the operator's configured ones, with no warning at route resolution (documented in CHANGELOG.md:51 and docs/operations.md:82, but nothing surfaces it at runtime) | src/ovcaq/config.py:657 | Phase 1 task 2 | BLAKE |
| R9 | [1/3] | ⚪ | R5 residue: about 40 of the retained table rows still pass against the pre-change classifiers and pin pre-existing behavior rather than this change, e.g. the widened-whitespace unknowns at :337-342 and the precedence rows over pre-existing classes at :359-368 (the latter duplicate test_failure_precedence_is_independent_of_diagnostic_order at :215-234). Cuttable without losing a PRD-named pin. | tests/drivers/test_adapter_failure_classes.py:337 | 8 | ALICE |
| R10 | [1/3] | ⚪ | Two fixture sites outside both the PRD list and cycle-1 R1's list still use the old tier key: tests/drivers/test_codex_edge.py:31 (`tiers = { sonnet = "fixture-claude-model" }`, asserted at :100) and tests/integration/test_native_telemetry_identity.py:167, :282, :301 (`PhaseSettings("sonnet", ...)`). Self-consistent and green, so naming consistency only. | tests/integration/test_native_telemetry_identity.py:301 | 9 | ALICE |
| R11 | [1/3] | ⚪ | Simplification: the test replaces the harness driver (`h.driver = Driver(h.clock, [], default_tiers=tiers)`) and then assigns `h.driver.steps` on the next line; `Driver` is a plain mutable dataclass, so `h.driver.default_tiers = tiers` keeps the harness's own driver and drops a statement. | tests/runtime/test_adapter_launch_routing.py:249 | 6 | ALICE |
| R12 | [1/3] | ⚪ | Explicit `--available-tier KEY` flags bypass the neutral union (`available_tiers is None` guard), so an operator who lists tiers explicitly loses `standard`/`deep` and a frontmatter floor of standard or deep warns and applies no floor | src/ovcaq/config.py:315 | Phase 1 task 1 | BLAKE |
| R13 | [1/3] | ⚪ | `DEFAULT_PHASE_TIERS` is a mutable module-level dict while `NEUTRAL_TIERS` snapshots its values at import time; any in-process mutation silently desynchronizes phase defaults from `available_tiers` | src/ovcaq/config.py:32 | Phase 1 task 1 | BLAKE |
| R14 | [1/3] | ⚪ | `NEUTRAL_TIERS` is a new public config symbol outside the PRD's declared new-symbol set (`default_tiers` and the three driver attributes); harmless and derived, but unlisted | src/ovcaq/config.py:33 | Phase 1 task 1 | BLAKE |
| R15 | [1/3] | ⚪ | Codex execution records now store the literal "default" as the model for both tiers (route.model flows into session metadata/metrics), so the journal cannot say which model actually ran — an observability loss the spec implies but never states | src/ovcaq/drivers/codex.py:118 | Phase 1 task 2 | BLAKE |
| R16 | [1/3] | ⚪ | Because the merged table now contains the reserved literal, `build_launch` accepts a raw explicit model "default" without `allow_explicit_model` (the `model not in settings.tiers.values()` branch) and silently omits `-m`; previously that string was rejected as an unknown model | src/ovcaq/drivers/codex.py:148 | Phase 1 task 2 | BLAKE |
| R17 | [1/3] | ⚪ | PRD risk asks to document the model-name frontmatter-floor mapping in docs/operations.md, but Phase 2's own acceptance check forbids model names there; the mapping example consequently lives only in docs/driver-protocol.md:40 — an internal PRD contradiction resolved in favor of the grep | docs/operations.md:80 | Phase 2 | BLAKE |

## Follow-up Tasks Created

None. The cycle reached the rework cap (cycle 2 of cap 2) with an unresolved 🟠 and two actionable two-voice 🟡 rows, so the loop-mode cap-out path recorded them as cap-overflow deferrals and handed off to finalize. No rework pass and no tail sweep ran, so none of these rows became a task.

## Alice

Incremental verification of every cycle-1 finding, with mutation checks rather than inspection alone:

- **cycle-1 R1 (fixture migration) — resolved for every file it named.** `rg "\bsonnet\b|\bopus\b" tests src` leaves only intentional sites: the Claude driver's own default table (src/ovcaq/drivers/claude.py:41), its two assertions (tests/drivers/test_driver_v2.py:38, tests/runtime/test_adapter_launch_routing.py:188), the neutrality scanners, the arbitrary unknown-tier strings (tests/runtime/test_supervisor_preflight.py:88) and the deliberate `haiku` negative (:203). Two files outside both lists still key fixtures on `sonnet` (R10).
- **cycle-1 R2 (Supervisor passes `default_tiers`) — resolved and non-tautological, verified by mutation.** Deleting src/ovcaq/runtime/supervisor.py:173 makes the new test fail with `Unknown agent tier: standard` in `preflight`; deleting :482 makes it fail with `exit_code=1, HALT "attempt failed: Unknown agent tier: standard"`. Both call sites are pinned independently. The second half (real-driver unconfigured argv capture, `done` phase) was not delivered — R7.
- **cycle-1 R3 (CHANGELOG wording) — half resolved.** The silent-fallback rewording is accurate; the trailing frontmatter-floor sentence is still wrong — R1.
- **cycle-1 R4 (operations.md) — resolved on all four counts.** docs/operations.md:82-91 drops the "must now define" contradiction, states the floor rule neutrally, keeps the warn-and-no-floor coverage, names the reserved literal `default`, and keeps the driver-protocol pointer. `rg -n "sonnet|opus" docs/operations.md` finds nothing. The edit is mirrored in the generated source src/ovcaq/workflow_cli.py:34-47 and `test_workflow_docs_are_generated_from_the_live_parser` passes, so the file really is regenerated.
- **cycle-1 R5 (test bloat) — mostly resolved.** The combinatorial carrier/casing/pairwise-precedence generators and the fixture-only `test_codex_diagnostic_table_reaches_every_failure_class` are gone (82 lines, ~111 parametrized cases). Replaying the file against the pre-change classifiers now gives 61 failed, 188 passed, and the pre-existing marker pins survive. Residue: R9.

Gates she ran: full `uv run pytest -q` (3 failed, 8436 passed, 14 errors — all the sandbox `/bin/ps` denial); `uv run ruff check tests src` clean; `uv run ruff format --check tests src` 254 files already formatted. Worktree left clean.

Findings: R1, the coverage gap merged into R7, R9, R10, R11.

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

Alice's R9 fail is solely the CHANGELOG.md:51 sentence that contradicts shipped `available_tiers` behavior; she states code behavior itself matches the PRD.

## Blake

Blind audit from the PRD alone. He located and read src/ovcaq/config.py, src/ovcaq/drivers/{__init__,base,claude,codex,claude_events,codex_events,edge}.py, src/ovcaq/runtime/{supervisor,decision}.py, docs/driver-protocol.md, docs/operations.md, CHANGELOG.md and the named test files.

Narrow verification he ran: the five driver test files (519 passed); the two workflow config files plus tests/runtime/test_adapter_launch_routing.py (221 passed); the six "fixtures off the old tier keys" runtime files (97 passed); two integration files (20 passed); tests/packaging/test_installed_supervisor_cli.py (27 passed); `ruff check src tests` clean; `mypy src/ovcaq` clean. He independently attributed the test-gate exit 1 to the 17 `PermissionError: Operation not permitted: 'ps'` results in tests/integration/test_terminal_lifecycle.py and noted that Phase 2's `./tools/check` exit criterion therefore cannot pass in this sandbox for reasons outside the change.

Spec items he confirmed present: every Claude marker; both Codex alternations with the `\b` wrapper and auth-first precedence intact; `DEFAULT_PHASE_TIERS` moved to src/ovcaq/config.py:32 and gone from src/ovcaq/drivers/__init__.py and its `__all__`; the neutral keys unioned into `available_tiers`; `AgentDriver.default_tiers`; the Claude sonnet/opus table; the Codex double-`default` table with the `-m` segment omitted; `{**default_tiers, **settings.tiers}` in both constructors; `resolve_phase_route(..., default_tiers=None)` with the merged check; both supervisor call sites; `DRIVER_API_VERSION` still 2; all docs/CHANGELOG acceptance greps.

Findings: R2, R3, R4, R5, R6, R12, R13, R14, R15, R16, R17.

B1-B19: all pass.

## Bob

Doubt lens plus de-slop, codex, resuming his cycle-1 thread so he verified his own prior critique rather than re-reviewing from zero.

FIX:
- Prior R2 partially resolved — the new fake-driver test verifies both Supervisor call sites but bypasses the bundled drivers and edge conversion (R7).
- Prior R3 partially unresolved — the frontmatter-floor sentence still excludes the neutral keys (R1).

VERIFY: (none)
KNOWN: (none)

R1: fail
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

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Bob emitted twelve consensus verdict lines; the consensus rubric has no R5 rule, so the set is complete.

## Carl

Unavailable this cycle. `gemini-run.sh` exited 1 on both the first dispatch and the single retry, backend=copilot model=gemini-3.8-flash, reason "You have exceeded your monthly quota" (request ids 2A0D:197CD:B2B0E28:BC93ED2:6AE29150 and 2AED:344B5B:B6B96E5:C0976B6:6AE29176). The `-o` file was written empty and was not passed to consolidation. Exit 1 is a one-off runtime failure, not the exit 4 that would latch him unavailable for the batch, so no batch latch was written. Both his dispatch rows are closed `error`.

Verdict: 17 findings
Tests: 8436 passed, 3 failed, 14 errors (suite run this cycle; `uv run pytest -q` exit 1; all 3 failures and all 14 errors are in tests/integration/test_terminal_lifecycle.py, the documented macOS-seatbelt `/bin/ps` denial, confirmed independently by Alice and Blake; `autopilot verify --cycle 2` parsed no counts and wrote no last-verification.json record, so the counts above were read from its log at docs/dev/tmp/gate-9ec3396.log:3591)
