---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
review: 10
date: 2026-09-05
head_sha: 72562f6fd12fb039e91e4c7b1be29758d1901ec8
reviewers: alice,blake,bob
mode: standalone
consensus_engine: legacy
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
  eve: disabled
---

# FT-04R10 — PRD 00004 completion review

Diff range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..72562f6fd12fb039e91e4c7b1be29758d1901ec8`

codex_rung_guard: not fired

**CHANGES_REQUESTED — one new actionable Medium finding.** All five R9 repairs
are verified, including the coordinator-origin ledger serialization root.
Updated report JSON omits earlier PRD sections that its published artifact
retains. Four inherited/methodological KNOWN observations remain; terminal skill
count is five, with one FIX and no unresolved VERIFY.

Full implementation review: P02-T01–T10, all 55 owned rows and every phase exit.
Fresh **1338 tests passed**, zero failures/skips. Complete workflow/packaging
450 passed; sync, Ruff, formatting, mypy, build and full-range whitespace pass.
No implementation changes, PRD closeout or next PRD occurred.

Three isolated native host contexts ran Alice consensus, Blake PRD-only, Bob
static doubt plus de-slop with all R/B/D obligations. External Bob/Carl wrappers
were not retried or bypassed; no model diversity is claimed. Standalone guard
result above does not imply an absent task-attempt ledger was consulted.

[Full source/probe evidence](00004-workflow-core-v1-fast-review-10-evidence.md) ·
[Dispatch](00004-cycle-10-dispatch.json) ·
[Raw script consolidation](00004-cycle-10-consolidation-raw.md)

## Consolidated findings

| ID | Consensus | Severity | Finding and file | Found by | Disposition |
|---|---|---|---|---|---|
| R8-K1 | 2/3 + mech-check | Medium | Inherited collision OR assertion; tests/state/test_cli.py:372 | Alice, Bob, mech-check | KNOWN |
| R8-K2 | 2/3 | Low (settled) | Inherited 53-line add_task and unchanged packaging size exceptions; state/commands.py:148 | Alice, Bob | KNOWN |
| R9-K3 | 2/3 | Low (settled) | Inherited 933-line schema.py | Alice, Bob | KNOWN |
| R9-K4 | 2/3 | Low | Full implementation-base fail-first binding remains unproven | Alice, Bob | KNOWN |
| R10-01 | 1/3 + coordinator | Medium | Report JSON text differs from retained batch artifact after PRD update; workflow_cli.py:161 | Bob, coordinator confirmed in installed wheel | FIX |

## R10-01 evidence and acceptance

Render A, then set active PRD B through StateStore and run installed
`ovcaq --json workflow render report`. It succeeds, but `text` contains B only
while `path` contains A+B. Repeating the render preserves the mismatch. State
and the complete on-disk report are intact. Machine consumers lose earlier
section content from the returned representation.

Cause: `_dispatch_workflow_render` renders fresh text separately from
`publish_report`'s update of existing content. The accepted batch artifact and
the existing installed `text == file` assertion establish intended equality;
that test currently exercises first publication only.

[Installed probe source](00004-cycle-10-report-probe.py) /
[Compared text, module origins and results](00004-cycle-10-report-probe.json).
The probe reports successful reproduction, not a passing product expectation.

Bounded repair (P02-T08, CMD-019/TEST-018): compose/publish once and return that
exact verified text. Add installed A→B→A and exact-replay assertions preserving
earlier/unrelated sections, duplicate collapse and state bytes. Keep every R9
directory identity/fsync guarantee; avoid an unverified pathname reread or a
second renderer. Full acceptance and preservation details are in the handoff.

## Repair verification and adjudication

R9-01 directory-inode serialization and serialized snapshot comparison pass,
including sidecar restoration. Six unchanged R8 named-boundary nested/process
cases preserve successful rivals. The fresh installed native-interval rival
returns contextual `state_io` JSON/exit 2 with no traceback; original identity
refusal and retries preserve exactly one of each ID. R9-02's 16 output-chain
cases, R9-03's four deep-TOML installed cases, R9-04's shared scanner and R9-05's
subprocess helper reuse all pass. Full preservation details are in the companion.

The original adjudication script still exits 1 on its obsolete rival-success
assertion. Its raw tracebacks remain evidence; it is not counted as a passing
check or an unhandled installed CLI error. The separate installed rival and
unchanged supplement functions establish the expected behavior.

Blake's initially absent-source objection reproduces the explicitly settled
null-artifact refusal. A later unidentified file remains refused by requirement;
no intent deletion, identity adoption or abort API is authorized. It creates no
new repair task. Alice's no-new-findings conclusion does not negate the installed
report mismatch. Bob's VERIFY is resolved by fresh coordinator gates.

The script's schema location variants are merged; unchanged packaging lengths
are folded into the existing inherited size limitation, already in Alice's K2.
The original skipped full-base replay and bounded 56-case supplement remain
explicit. Raw opinions, counts, severities and rubric verdicts below are intact.

## Alice

[ALICE] 🟡 KNOWN R8-K1: inherited collision test retains the mechanically identified OR assertion; no new repair requested | File: tests/state/test_cli.py:372 | Task: general
[ALICE] ⚪ KNOWN R8-K2: inherited 53-line add_task exceeds the function limit; three unchanged packaging functions retain their accepted size exceptions | File: src/ovcaq/state/commands.py:148 | Task: general
[ALICE] ⚪ KNOWN R9-K3: inherited schema.py remains 933 lines; broad state restructuring is excluded | File: src/ovcaq/state/schema.py:1 | Task: general
[ALICE] ⚪ KNOWN R9-K4: comprehensive implementation-base fail-first binding remains unproven; the supplied bounded replay and 23 chronological repair regressions do not establish universal binding | File: N/A | Task: general

No new actionable finding. Reviewed the full implementation range `b43bf2c..72562f6`, all ten source tasks, all 55 owned rows, and every phase exit.

The five authorized repairs are verified:

| Repair | Assessment |
|---|---|
| R9-01 | Directory-inode locking serializes ledger reads and native replacement. Snapshot comparison also rejects stale publication after restoration of the original sidecar. Nested and real-process rivals, earlier named boundaries, refusal evidence, and exact retries pass. The coordinator-origin lock defect is retained explicitly and is repaired. |
| R9-02 | Report, audit, and archive publication retain and verify every directory from configured root through leaf. Replacement and identical-payload replay regressions cover each component, preserve state and displaced payloads, and permit valid retry. |
| R9-03 | TOML recursion is translated into contextual `ConfigurationError`. Independent project/user probes for recognized and ignored keys return usage JSON without traceback or mutation. Installed regressions preserve the same contract. |
| R9-04 | `_section_span` now supplies both section extraction and duplicate removal. Exact headings, next-heading boundaries, unrelated content, and golden behavior remain covered. |
| R9-05 | `_run` delegates to `_run_unchecked`, retaining command conversion, environment, cwd, capture, timeout, and assertion diagnostics. Installed-origin checks remain intact. |

Source-task coverage:

| Task | Assessment |
|---|---|
| P02-T01 | WIP priority, deterministic sequence ordering, backlog fallback, hold exclusion, and configured lifecycle paths covered. |
| P02-T02 | Frontmatter defaults, validation, warnings, abstract tiers, active-PRD binding, cap ownership, and CAS covered. Returned controls retain their accepted downstream owner. |
| P02-T03 | Six transition rows, rejection rows, complete effects, atomic publication, and terminal drain covered. |
| P02-T04 | Resume precedence, dependency-plan validation, fifteen-task policy, and override behavior covered. An independent maximum-size 512-task chain passes. |
| P02-T05 | Exact reset owners, batch preservation, completion summaries, substantive-decision filtering, and conflicting/idempotent completion covered. |
| P02-T06 | Attribution, operation-ID validation, strict decoding, conflicting replay, durable publication, and repaired serialization covered. |
| P02-T07 | Typed intent, artifact identity, exclusive moves, interruption/restart boundaries, state publication guards, and systemic second-park halt covered. |
| P02-T08 | Golden projections, unknown totals, metric ordering/scoping, deferred details, section preservation, and publication durability/identity covered. |
| P02-T09 | Defaults, CLI/project/user precedence, runtime containment, independent state override, tier keys, and malformed-input handling covered. |
| P02-T10 | Workflow registration and both command inventories derive from the live parser; documentation assertions remain intact. |

The complete owned-row trace is:

- Frontmatter: CMD-014, TEST-006.
- Policy: CMD-012, DEC-071, TEST-012.
- Records: ART-016, ART-017, ART-026, CMD-007, CMD-008, CMD-010, CMD-036, DEC-076–DEC-082, ENV-025, STATE-112, STATE-113, STATE-121, TEST-001, TEST-002, TEST-008, TEST-013–TEST-017, TEST-038, TEST-052.
- Reports: ART-012–ART-014, ART-039–ART-041, CMD-018–CMD-020, TEST-018–TEST-020, TEST-062.
- Resume: CMD-016, TEST-021.
- Selection: ART-036, CMD-013, TEST-027.
- Transitions: CMD-009, CMD-015, TEST-029.
- Parser documentation: TEST-005.

Phase A satisfies characterized lifecycle equivalence under v1 state. Phase B preserves recoverable interruption boundaries without duplicate records or lost work, subject to the explicitly accepted initially absent-source/null-artifact refusal. Phase C supplies installed commands, deterministic rendering, parser-derived documentation, and provider-neutral dependency boundaries.

R8 preservation remains intact: strict ledger decoding; original artifact identity; earlier lock-boundary behavior; complete deferred details; directory fsync retries; substantive decision filtering; prompt nonregular-input refusal; and retained assertions after test splitting. No additional behavior-preserving simplification warrants rework.

Independent verification passed **67 tests in 0.27s**, plus four TOML probes and the maximum-size dependency-chain probe. Full gates remain coordinator-owned. Disposable roots were cleaned, children reaped, and final Git status is empty. No repository files or reviewer output were written.

R2, R12, and R13 below retain the literal inherited/methodological exceptions; they introduce no new repair request.

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
R12: fail
R13: fail

## Blake

[BLAKE] 🟡 Missing PRD creates unrecoverable stall/park intent: `_begin_operation` commits `artifact=None`, then every retry rejects the restored file because `_require_artifact_identity` always rejects a null identity. Disposable probe confirmed revision 1 remains stuck at `intent` after restoring the PRD, fencing other workflow mutations. Reject missing sources before committing intent or provide safe reconciliation; the existing missing-source test never exercises retry. | File: src/ovcaq/workflow/records.py:559 | Task: P02-T07

B1: fail
B2: pass
B3: fail
B4: pass
B5: fail
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
B16: fail
B17: pass
B18: pass
B19: pass

## Bob

Reviewed P02-T01–T10, all 55 owned source rows, phase exits, and the full implementation range. Static inspection only; no files changed.

[BOB] 🟡 JSON report text omits previously rendered PRDs although the returned path retains them. After A→B, machine consumers receive B-only text while the artifact contains A+B; exact rerender preserves this mismatch. Coordinator’s installed-wheel probe confirms it. | File: src/ovcaq/workflow_cli.py:161 | Task: P02-T08
[BOB] ⚪ Cannot statically verify: tests, lint, formatting, typing, distribution build, and whitespace gates pass. Coordinator reports fresh passing gates; Bob executed none. | File: N/A | Task: general
[BOB] 🟡 R8-K1: inherited collision test retains the mechanically identified `or` hedge. | File: tests/state/test_cli.py:372 | Task: general
[BOB] 🟡 R8-K2: inherited add_task remains 53 lines against the 50-line rubric. | File: src/ovcaq/state/commands.py:148 | Task: general
[BOB] 🟡 R9-K3: inherited schema module exceeds the 800-line rubric. | File: src/ovcaq/state/schema.py | Task: general
[BOB] ⚪ R9-K4: universal full-range fail-first binding remains unproven; supplied bounded replay evidence does not establish it. | File: N/A | Task: general
[BOB] 🟡 Three unchanged packaging functions exceed 50 lines: installed_wheel (51), test_wheel_contains_exact_declared_package_and_metadata (79), and test_installed_version_and_every_declared_module_come_from_wheel (66). | File: N/A | Task: general

FIX:
- Report JSON/artifact mismatch — src/ovcaq/workflow_cli.py:161 — Compose and publish the report once, then return that exact composed text. Add installed A→B→A and exact-rerender assertions that `text` equals the published artifact while preserving earlier sections and state bytes.

VERIFY:
- Runtime gates — Confirm the coordinator’s FT-04R10 record for `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src/ovcaq`, `uv build`, and full-range `git diff --check`. Reported results already pass; no repeat execution is requested.

KNOWN:
- R8-K1 collision assertion — Explicitly retained by the settled scope decision; changing the inherited assertion is outside this review’s repair scope.
- R8-K2 add_task length — Explicitly retained; broad state-service restructuring is excluded.
- R9-K3 schema length — Explicitly retained; schema restructuring is excluded.
- R9-K4 replay limitation — The failed full-base replay is explicitly excluded from retry; bounded chronological evidence cannot replace universal proof.
- Inherited packaging function lengths — All three bodies remain unchanged from base and are explicitly excluded from restructuring.

Finding count: 7 = 1 FIX + 1 VERIFY + 5 KNOWN.

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: fail
R13: fail
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Handoff

Findings are reported in the [FT-04F10 handoff](../plans/fast-track-handoffs/00004-workflow-core-v1/review-10.md),
not written into an autopilot task store. PRD remains WIP. Next: one bounded
repair in a fresh work session, then fresh FT-04R11 with every mandated lens and
source obligation. [Contract card](00004-cycle-10-contract-card.md).
Saved-file gate and preservation audit: [final audit](00004-cycle-10-final-audit.json).

Verdict: 5 findings
Tests: 1338 passed, 0 failed, 0 skipped (suite run this cycle)
