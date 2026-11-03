---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
review: 9
date: 2026-09-05
head_sha: 78f916c366f74105b76e6f07d80a7a1aeb251e9f
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

# FT-04R9 — PRD 00004 completion review

Diff range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..78f916c366f74105b76e6f07d80a7a1aeb251e9f`

codex_rung_guard: not fired

**CHANGES_REQUESTED — five actionable findings: one High, four Medium.**
The ledger lock repair still permits loss of a successful rival append.
Report publication can report success at an absent configured path, and nested
project/user TOML escapes the JSON error contract. Two concrete duplication
findings also require bounded rework. Four inherited/methodological observations
remain KNOWN, giving nine residual findings in the terminal skill count.

Reviewed the full implementation range, all ten P02 source tasks, all 55 owned
characterization rows, and every R8-01–R8-08 repair. Fresh full suite:
**1,315 passed, zero failed/skipped**. Sync, complete workflow/packaging suites,
Ruff, formatting, mypy, build and full-range whitespace pass. Passing gates do
not establish the missing publication guarantees.

This fresh standalone review used three isolated native host contexts and the
installed persona/rubric prompts. Alice ran consensus, Blake PRD-only, Bob doubt
plus de-slop and D1–D5 (the installed names for the requested doubt R1–R5).
External Bob/Carl nested guards were not retried or bypassed, per the handoff.
No model diversity is claimed. Eve was not enabled. No unrelated autopilot
state was consulted or created; the guard above is the standalone result, not
a claim about an absent implementation-attempt ledger.

[Full source and verification evidence](00004-workflow-core-v1-fast-review-09-evidence.md) ·
[dispatch record](00004-cycle-09-dispatch.json) ·
[raw script consolidation](00004-cycle-09-consolidation-raw.md)

## Consolidated findings

The table is sorted by lens consensus then severity. Coordinator evidence can
establish a defect with zero lens votes. R9-01 remains the first repair priority.

| ID | Consensus | Severity | Finding and file | Found by | Disposition |
|---|---|---|---|---|---|
| R9-02 | 2/3 | Medium | Report/audit/archive publication returns success through a displaced output directory; reports.py:499 | Alice, Bob; coordinator reproduced | FIX |
| R9-03 | 1/3 | Medium | Deep TOML raises uncaught RecursionError; config.py:47 | Alice; coordinator reproduced in checkout and installed wheel | FIX |
| R9-04 | 1/3 | Medium | Duplicate exact-heading span scanner; reports.py:570/590 | Bob; coordinator inspected | FIX |
| R9-05 | 1/3 | Medium | Duplicate installed subprocess runner; packaging_support.py:162/184 | Bob; coordinator inspected | FIX |
| R8-K1 | 1/3 + mech-check | Medium | Inherited collision test hedges with OR; tests/state/test_cli.py:372 | Bob, mechanical check | KNOWN |
| R8-K2 | 1/3 | Low | Inherited 53-line add_task; state/commands.py:148 | Bob; AST comparison | KNOWN |
| R9-K3 | 1/3 | Low | Inherited oversized schema.py, 933 versus 927 base lines | Bob; AST comparison | KNOWN |
| R9-K4 | 1/3 | Low | Full implementation-base fail-first binding remains unproven | Bob; mechanical replay | KNOWN |
| R9-01 | 0/3 + coordinator | High | Lock replacement after validation lets stale ledger replacement destroy a successful rival append; workflow/_files.py:99 | Coordinator | FIX |

## Actionable evidence and acceptance

**R9-01 — P02-T06/P02-T07, durable serialization and no lost work.**
Rename the held sidecar after `verify_lock()` and before native `os.replace`.
A second writer acquires the replacement sidecar, appends `second`, and returns
success. The first writer then replaces the ledger with `first` and ultimately
raises an identity error. Both before and after retry, only `first` remains.
Nested and real-process variants reproduce; the process exits 0. Existing
BEFORE_PUBLISH tests cover an earlier, now-protected boundary.
Repair must prevent successful rival records being overwritten across this
interval, retaining original refusal and safe retry. Another unsynchronized
pathname check alone does not establish serialization. Preserve sidecar
ownership and saga guards, strict reads, op-ID replay and all R8 identity checks.

**R9-02 — P02-T08, durable report locations.**
Rename/recreate the output directory before native publication. Report, audit
and final-state archive all return a path that does not exist; their payload
is only in the displaced directory. Retain verified directory-chain identity
through publication, identical-content replay and successful return. A detected
replacement must refuse contextually; retry against the valid configured
directory must produce its expected file without changing authoritative state.
Keep parent creation sync, replay directory sync, nonregular refusal, section
idempotence and existing golden content.

**R9-03 — P02-T09, installed workflow configuration input.**
About 4 KB of nested TOML arrays triggers RecursionError, a traceback and exit 1
under `--json workflow select`. Both project/user scopes fail from a freshly
installed wheel outside the checkout. Bound decoding or translate exhaustion
into the existing contextual symbolic error contract; no traceback or partial
mutation. Cover recognized and ignored keys while preserving config/state bytes,
FIFO/symlink refusal, defaults and precedence. This repair does not add provider
configuration policy.

**R9-04 — P02-T08, de-slop.**
Share the identical exact-heading/next-level-two-heading span lookup between
`_replace_section` and `_report_section`. Preserve duplicate removal,
missing-section errors, boundary behavior and unrelated sections. Existing
behavioral section/golden tests should validate the change.

**R9-05 — packaging support, de-slop.**
Have `_run` delegate to `_run_unchecked` and retain its detailed assertion.
Keep identical argv conversion, cwd, environment, capture/text behavior and
timeout. Rerun complete workflow/packaging directories and retain installed
module-origin checks. No test that merely mirrors this delegation is needed.

## Adjudication and inherited observations

Alice's R8-03 “repaired” judgment covers the checked boundaries. The later
syscall interleaving contradicts the broader guarantee, so R9-01 remains
despite zero lens votes. R8-01/02/04/05/06/07/08 repairs are verified with their
preservation checks; R9-02 and R9-03 identify additional boundaries, not a
retraction of the repaired fsync/FIFO behavior.

Blake's frontmatter behavior was reproduced, but its proposed ownership change
would reopen the settled derived-state/runtime boundary. Returned controls are
inputs for the downstream owner; parsing does not manufacture catchup/design
completion or store duplicate policy. The current cap/tier application and
overwrite ownership are tested. Bob's absent-source null-artifact refusal was
also reproduced and is explicitly required by rework-08's failure-evidence
preservation rule. A later unidentified replacement remains refused; automatic
recovery from initially absent source is not claimed. Both raw objections stay
below; neither becomes an implementation task. Detailed evidence and scope
reasoning are in the companion document.

Bob's VERIFY gates were run successfully this cycle. His two exact duplication
findings are accepted despite Alice's different simplification judgment.

R8-K1/R8-K2 remain inherited KNOWN per the user's settled decisions.
R9-K3 is a six-line schema type extension in an already oversized file; broad
state restructuring is excluded. R9-K4 retains the full-base replay limitation:
the mandated helper skipped on missing packaging_support. A bounded repair-base
supplement collected all 56 R8 regressions: 46 failed, ten valid preservation
cases passed. This is not comprehensive full-range binding, nor proof that the
installed ledger tests originally ran before repair. Three inherited packaging
overlength functions are AST-identical to the full base and remain part of the
inherited size limitation.

## Alice

Isolated implementation-aware consensus; full PRD/source/diff/mechanical
context and authorized cycle-08 repair evidence. Verbatim final output:

[ALICE] 🟡 Report, audit, and final-state archive publication can succeed after their output directory is replaced, returning a path that does not exist; retain and recheck directory identity through publication and successful return | File: src/ovcaq/workflow/reports.py:499 | Task: P02-T08
[ALICE] 🟡 Deeply nested project or user TOML raises uncaught RecursionError, breaking the JSON CLI error contract; bound parsing and translate resource exhaustion into a contextual symbolic error | File: src/ovcaq/config.py:47 | Task: P02-T09

Independent evidence:

- For each of `publish_report`, `publish_audit`, and `archive_final_state`, a temporary-root probe renamed the output directory aside and recreated it immediately before native `os.replace`. All three returned successfully; every returned path was absent, while the payload existed only inside the displaced directory.
- Project and user configurations containing `ignored = ` followed by 2,000 nested arrays caused `python -B -m ovcaq --root <tmp> --json workflow select` to exit 1 with a traceback ending in `RecursionError`. Stderr was not JSON; state bytes remained unchanged.
- The focused R8 regression run passed **48 tests in 0.23s**, covering ledger integrity, artifact identity, report recovery, and blank decisions. The full suite remains coordinator-owned.
- All probe roots, subprocesses, and the dedicated pytest temporary tree were cleaned. No repository files or Git state were changed.

Every prior repair was checked:

| Repair | Assessment |
|---|---|
| R8-01 | Repaired: guarded decoding preserves duplicate-key/depth evidence; malformed ledger reads refuse before rewriting. |
| R8-02 | Repaired: durable device/inode identity survives intent, move, recorded-stage restart, and publication guards. Substitution preserves unfinished work. |
| R8-03 | Repaired and explicitly retained: sidecar ownership is checked before read/modify, replacement, replay completion, and saga commit. Nested and subprocess competitors survive; retry retains both records. |
| R8-04 | Repaired: batch summary reconstructs earlier/current deferred details with PRD attribution, independently of prior Markdown history. |
| R8-05 | Specified fsync omissions repaired: creation/retry sync parents; identical-content replay syncs its directory. The new directory-identity finding above remains separate. |
| R8-06 | Repaired: completion and audit share substantive-content filtering; metadata-only decisions disappear while populated cells remain. |
| R8-07 | Repaired: named payload/config inputs open nonblockingly and validate regular-file type. Installed FIFO tests cover all four requested surfaces. Deep TOML remains the separate gap above. |
| R8-08 | Repaired: independent scenarios were split with retained assertions and shared setup. Supplied mechanical evidence shows the new workflow/packaging functions meet the limit and the state-service test module is reduced. |

Full source-task coverage:

| Source task | Assessment |
|---|---|
| P02-T01 | Selection, five-digit ordering, WIP priority, backlog fallback, hold exclusion, configured lifecycle paths, missing/nonregular directories covered. |
| P02-T02 | Defaults, enums, positive caps, optional controls, abstract tiers, active-PRD binding, overwrite warnings, and CAS covered. Accepted derived-state mappings retained. |
| P02-T03 | All six transition rows, rejection rows, complete effects, atomic mutation, and terminal drain covered. |
| P02-T04 | Resume precedence and plan shape/size policy covered; no higher-layer dependency introduced. |
| P02-T05 | Exact reset ownership, batch preservation, deterministic completion summaries, matching/conflicting replay, and decision filtering covered. |
| P02-T06 | Deferred attribution, operation-ID replay/conflict behavior, strict reads, serialization, and durable retry covered, including the coordinator-origin lock root. |
| P02-T07 | Typed recovery intent, all named interruption points, verified exclusive moves, restart reconciliation, state-publication fencing, and systemic second-park halt covered. |
| P02-T08 | Golden projections, unknown totals, batch scoping, stable metric ordering, replaceable sections, deferred details, and fsync repairs covered; publication identity remains defective. |
| P02-T09 | Defaults, CLI/project/user precedence, runtime containment, independent state override, and active tier keys covered; malformed-config error handling remains defective. |
| P02-T10 | Workflow registration and both documentation inventories derive from the live parser; documentation contract tests cover the command family. |

All **55 owned rows** were traced through the supplied join and accepted migration inventory:

- Frontmatter: CMD-014, TEST-006.
- Policy: CMD-012, DEC-071, TEST-012.
- Records: ART-016, ART-017, ART-026, CMD-007, CMD-008, CMD-010, CMD-036, DEC-076–DEC-082, ENV-025, STATE-112, STATE-113, STATE-121, TEST-001, TEST-002, TEST-008, TEST-013–TEST-017, TEST-038, TEST-052.
- Reports: ART-012–ART-014, ART-039–ART-041, CMD-018–CMD-020, TEST-018–TEST-020, TEST-062.
- Resume: CMD-016, TEST-021.
- Selection: ART-036, CMD-013, TEST-027.
- Transitions: CMD-009, CMD-015, TEST-029.
- Parser documentation: TEST-005.

The bounded coordinator replay establishes 46 pre-repair failures among 56 R8 behavioral cases. The ten passing decision cases preserve existing nonblank/zero behavior; they are not new tautology findings. The full implementation-base replay limitation remains explicit.

Accepted inherited observations remain KNOWN without new repair requests: the collision test’s OR assertion and existing overlength functions, including `StateService.add_task`. R12 below records the literal inherited size exception; R8-08 introduced no remaining size violation. No additional behavior-preserving simplification warrants rework.

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: pass

## Blake

Isolated PRD-only context with accepted source references and all B1–B19.
No diff, changed-file list, repair handoff, other output or design context.
Verbatim final output:

[BLAKE] 🟠 Frontmatter application discards catchup/design controls instead of committing their effective policy. `catchup: skip` leaves resume targeting catchup; `catchup: force` leaves completed catchup skipped. Only the review cap and tier floor persist, so subsequent applications also cannot report overwrites of the discarded controls. | File: src/ovcaq/workflow/frontmatter.py:191 | Task: P02-T02

Verified with an in-memory store that validates committed state:

- `catchup: skip`, initially incomplete → `build: catchup then planning`.
- `catchup: force`, initially completed → `skip catchup -> planning`.

This conflicts with the committed-state boundary, characterized frontmatter application (`CMD-014`), and derived ownership documented for `batch.catchup`.

The accepted plan digest matches. Generated command documentation matches the parser. Workflow dependency and provider-string inspection found no violations. Reviewed recovery implementation and boundary tests; no additional actionable findings. No files changed or full suite run.

B15–B17 map to PRD Phases A–C. B4 has no specified performance budget; the plan ceiling is implemented. B9 and B11 are not applicable because authentication and throttling are unspecified. B13 is not applicable: migration and rollback machinery are explicitly excluded.

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
B15: fail
B16: pass
B17: fail
B18: pass
B19: pass

## Bob

Isolated static doubt and de-slop review; full diff/source/mechanical context,
consensus rubric and the complete two-lens FIX/VERIFY/KNOWN/D1–D5 instructions.
No repair handoff, other lens output or design context. Verbatim final output:

[BOB] 🟠 B1: Missing PRD creates an unrecoverable null-artifact intent that fences every public state mutation | File: src/ovcaq/workflow/records.py:559 | Task: P02-T07
[BOB] 🟡 B2: Report publication can succeed after its output directory is renamed, returning a nonexistent configured path | File: src/ovcaq/workflow/reports.py:499 | Task: P02-T08
[BOB] 🟡 B3: Section removal and extraction duplicate the same heading-span scanner | File: src/ovcaq/workflow/reports.py:570 | Task: P02-T08
[BOB] 🟡 B4: Installed-command helpers duplicate identical subprocess invocation logic | File: tests/packaging/packaging_support.py:162 | Task: general
[BOB] ⚪ B5: Cannot statically verify test, lint, formatting, type-check and build execution; coordinator reports fresh passing gates | File: N/A | Task: general
[BOB] 🟡 B6: Retained inherited collision test contains the mechanically identified OR assertion | File: tests/state/test_cli.py:372 | Task: general
[BOB] ⚪ B7: Retained inherited StateService.add_task exceeds the function limit at 53 lines | File: src/ovcaq/state/commands.py:148 | Task: general
[BOB] ⚪ B8: Lightly changed inherited schema module exceeds the file limit at 933 lines | File: src/ovcaq/state/schema.py:1 | Task: general
[BOB] ⚪ B9: Comprehensive implementation-base fail-first binding remains unproven | File: N/A | Task: general

FIX:

- B1 — `records.py:559` stamps `artifact=None` when neither lifecycle location contains the PRD. Restoring the source cannot satisfy `_require_artifact_identity`; even `--unsafe` mutations and restore remain fenced. Reject absent source before intent publication, and change the existing missing-source test to cover restoration followed by successful retry.
- B2 — `reports.py:499` verifies directory identity only during opening. Renaming `reports` after opening leaves publication operating through its retained descriptor while returning the original pathname. Revalidate the configured directory chain through publication and before returning; cover audit, report and archive replacement/retry.
- B3 — `reports.py:570` and `:590` repeat exact-heading lookup and next-level-two-heading scanning. Share one private span finder while preserving duplicate removal and missing-section errors.
- B4 — `packaging_support.py:162` duplicates `_run_unchecked`’s invocation. Have `_run` call `_run_unchecked`, retaining its existing diagnostic assertion.

VERIFY:

- B5 — Exact checks: `mise exec -- uv run pytest`, `mise exec -- uv run ruff check .`, `mise exec -- uv run ruff format --check .`, `mise exec -- uv run mypy src/ovcaq`, and `mise exec -- uv build`. Coordinator reports these passed; this static reviewer executed none.

KNOWN:

- B6 — Explicitly settled inherited assertion; no PRD-00004 repair requested.
- B7 — Explicitly settled inherited function size; broad state restructuring is excluded.
- B8 — The schema was already beyond 800 lines before this six-line addition; splitting inherited state ownership is outside this workflow extraction.
- B9 — Full-base replay aborted on missing `packaging_support`; broad replay-tool repair is explicitly excluded. The supplied repair-base supplement collected 56 cases: 46 failed and ten valid preservation cases passed. It does not establish comprehensive fail-first binding.

9 findings = 4 FIX + 1 VERIFY + 4 KNOWN.

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: fail

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Handoff

Follow-ups are reported in the [FT-04F9 repair handoff](../plans/fast-track-handoffs/00004-workflow-core-v1/review-09.md),
not written into an autopilot task store. This session changes review evidence
only. The PRD remains WIP; implementation plans, capsule and older evidence
remain untouched. The [standalone contract card](00004-cycle-09-contract-card.md)
records the next gate: bounded repair in a fresh work session, then a fresh
FT-04R10 completion review with every mandated lens and source obligation.

Saved-file shape gate and final state/artifact audit:
[final audit](00004-cycle-09-final-audit.json).

Verdict: 9 findings
Tests: 1315 passed, 0 failed, 0 skipped (suite run this cycle)
