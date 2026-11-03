---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
review: 13
date: 2026-09-07
head_sha: be5e385bd9714952b4803ee30f7c72e661c278f2
reviewers: alice,blake
consensus_engine: legacy
status: incomplete
agents:
  alice: available
  blake: available
  bob: unavailable
  carl: unavailable
  eve: unavailable
---

# Cycle 13 — incomplete; paused for unavailable Claude Bob

Diff range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..be5e385bd9714952b4803ee30f7c72e661c278f2`

codex_rung_guard: fired (2 codex-implemented task(s)); constraint UNMET

**This is not a completed review.** Bob's external Claude Opus process returned
an API 429 quota rejection before inference. The host contract requires the
independent Claude doubt/de-slop voice every cycle and explicitly requires a
pause if it is unavailable. There is no Bob reviewer text, successful receipt,
or current D1-D5 verdict to certify. No stale cycle-12 rubric is reused.

Quota reset: **2026-09-07 19:50 Europe/Prague (17:50 UTC)**. The dispatch taxonomy
forbids retrying an unchanged exhausted quota. Carl separately exited 3 on the
existing nesting guard; no backend ran, and no permanent batch latch applies.
Fable is unavailable through the native host tools; no Eve dispatch or substitute
Fable model is claimed. The intended external Claude Bob host substitution
could not provide the independent voice. No Codex CLI or guard bypass was used.

[Immutable Bob raw JSONL](00004-cycle-13-bob-output-8e22f932bdb843f896b7c570679c4ab6.jsonl)
and its empty stderr sidecar are retained. [Failure metadata](00004-cycle-13-dispatch-failure.json)
records the raw hash, API error and reset. `autocodex_bob_receipt` is deliberately
absent: the helper creates a receipt only for a successful complete reviewer.

State remains at cycle 13, cap 2, with the same batch, base and 13 completed
tasks. No rework, task retry, cap increase, convergence or finalize transition
was performed. The two candidate repairs below remain findings until the full
review and decision gate can complete. This artifact avoids the canonical
`-review-13.md` filename so an incomplete cycle cannot be skipped on recovery.

## Consolidated findings

The script consolidated only the two successful native reviewers; 1/2 is not
three-provider consensus. Mechanical findings are absorbed below.

| Consensus | Severity | Issue | File | Task | Found By |
|-----------|----------|-------|------|------|----------|
| [1/2] | 🟡 | Runtime directory creation walks from `/` and read-opens/fsyncs every ancestor, so a valid configured runtime beneath a search-only ancestor fails with “not a real directory”; the source-tree `0111` ancestor probe reproduced the failure | src/ovcaq/workflow/_files.py:252 | P02-T06/P02-T09 | ALICE |
| [1/2] | 🟡 | `_ensure_directory_chain` processes `/` as a level and then opens/fsyncs `/` again as the parent of the first real component; skip the root self-step because the following iteration already verifies and syncs that same directory | src/ovcaq/workflow/_files.py:255 | P02-T06 | ALICE |

| [1/2] | 🟡 | `test_init_rejects_project_config_path_collisions_before_state_publication` hedges with `or`: either outcome satisfies it | tests/state/test_cli.py:372 | general | mech-check; settled R8-K1 |

Terminal observation accounting: **3 findings = 2 open Medium + 1 settled
Medium**. Bob unavailability is a separate review blocker. The settled test
shape is retained, not silently dropped. There are no previous failed or unrun
verification checks to carry forward: all five cycle-12 queue entries record
integer exit 0 at the reviewed HEAD. Bob produced no VERIFY bucket, so this
cycle's queue is empty.

The permission finding is supported by a source-tree probe, not an installed
CLI probe. It fails loudly and does not establish lost data. A safe eventual
repair must retain actual-exit retry/replay durability, peer directory ownership,
identity checks and serialization; blindly stopping confirmation at runtime_root
would reintroduce the earlier crash gap. No architecture choice is made here.

The root self-step is confirmed at `_files.py:255`: `/` is its own parent in
the first iteration and is then confirmed again for the first real component.
The older claim that every ancestor is fsynced twice is inaccurate; only the
root receives this redundant parent sync. It is a concrete small cleanup, not
evidence of missing durability.

Blake's initial High claim that `--ceiling` is unauthorized was withdrawn after
consulting `current_system.toml` TEST-012, which explicitly characterizes override
semantics. CMD-012/DEC-071/TEST-012 are owned by PRD 00004. `policy.py` and the
source CLI retain that behavior. The positive-only domain is not a specified
contract. The original claim is ledger-discarded with this verified reason.

## Coverage and method

All ten source tasks and the three phase exits were reviewed. Alice leaves
P02-T06/P02-T09 and the configured-path acceptance open. The source-owned rows
are mechanically enumerated in [source coverage](00004-cycle-13-source-coverage.json).
The accepted plan digest is `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.

| Source target | Count | IDs |
|---|---:|---|
| src/ovcaq/workflow/frontmatter.py | 2 | CMD-014, TEST-006 |
| src/ovcaq/workflow/policy.py | 3 | CMD-012, DEC-071, TEST-012 |
| src/ovcaq/workflow/records.py | 28 | ART-016, ART-017, ART-026, CMD-007, CMD-008, CMD-010, CMD-036, DEC-076, DEC-077, DEC-078, DEC-079, DEC-080, DEC-081, DEC-082, ENV-025, STATE-112, STATE-113, STATE-121, TEST-001, TEST-002, TEST-008, TEST-013, TEST-014, TEST-015, TEST-016, TEST-017, TEST-038, TEST-052 |
| src/ovcaq/workflow/reports.py | 13 | ART-012, ART-013, ART-014, ART-039, ART-040, ART-041, CMD-018, CMD-019, CMD-020, TEST-018, TEST-019, TEST-020, TEST-062 |
| src/ovcaq/workflow/resume.py | 2 | CMD-016, TEST-021 |
| src/ovcaq/workflow/selection.py | 3 | ART-036, CMD-013, TEST-027 |
| src/ovcaq/workflow/transitions.py | 3 | CMD-009, CMD-015, TEST-029 |
| tests/workflow/ | 1 | TEST-005 |

The computed counts total 55. Alice's raw records subtotal says 31, but its
listed IDs and the manifest compute **28**; the raw response is retained below
and the corrected count is used here. TEST-005 owns parser/document coverage.

Alice and Blake each ran as native `gpt-5.6-sol`, logical tier `sonnet`, with
`fork_turns=none` and independently assembled complete personas/rubrics. Blake
received only the PRD, its mandatory specification links and blind rubric, with
no implementation context, diff, history, handoff, pack or sibling findings.
The native lanes use the same model; no native model-diversity claim is made.
Alice's first coverage summary was identification-only and was returned for
completion; her final report below supersedes it. Her first R2/R12/R13 passes
were corrected to failures: settled disposition does not change binary rubric
truth. Blake's initial rubric failures attached to the withdrawn override claim;
the corrected complete rubric is retained below. Their initial verdict records
remain in the review audit satellite.

All reviewers/processes were awaited. Bob exit 1 and Carl exit 3 were consumed.
The watcher was stopped after Bob's terminal failure and its command session
39333 completed. Alice's probe directory was removed after restoring permissions.

The full review covers 77 changed files. [Mechanical evidence](00004-cycle-13-mechanics.md)
contains per-function facts and test checks. Full-base replay was skipped because
the sandbox denied worktree creation, not because tests passed. Engram pack failed
because the repository is unregistered; no registration or optional pack repair
was attempted. No source tests read live personal runtime state.

The matching `last-verification.json` provides all six successful required gates
at this exact HEAD: uv sync, 1352 pytest tests, Ruff, formatting, mypy and wheel/
sdist build. These results are reused as instructed, not presented as new runs.
Blake additionally reports 431 selected tests, Ruff and mypy passing in his lane;
those do not replace the recorded full-suite counts.

## Alice

[ALICE] 🟡 Runtime directory creation walks from `/` and read-opens/fsyncs every ancestor, so a valid configured runtime beneath a search-only ancestor fails with “not a real directory”; the source-tree `0111` ancestor probe reproduced the failure | File: src/ovcaq/workflow/_files.py:252 | Task: P02-T06/P02-T09
[ALICE] 🟡 `_ensure_directory_chain` processes `/` as a level and then opens/fsyncs `/` again as the parent of the first real component; skip the root self-step because the following iteration already verifies and syncs that same directory | File: src/ovcaq/workflow/_files.py:255 | Task: P02-T06

Source-inventory reconciliation: all 55 PRD-00004 rows were located in `tests/characterization/migration.toml`, matched to `current_system.toml`, and reconciled by their declared target:

- Frontmatter, 2 rows: `CMD-014`, `TEST-006`. `frontmatter.py`, application tests, CLI tests, and installed tests cover defaults, validation, warnings, tier hints, active-PRD binding, and transactional application.
- Policy, 3 rows: `CMD-012`, `DEC-071`, `TEST-012`. `policy.py` and policy/CLI tests cover the 15-task ceiling, override, tolerant counting, graph validation, and oversized-plan failure.
- Records/lifecycle, 31 rows: `ART-016`, `ART-017`, `ART-026`, `CMD-007`, `CMD-008`, `CMD-010`, `CMD-036`, `DEC-076`–`DEC-082`, `ENV-025`, `STATE-112`, `STATE-113`, `STATE-121`, `TEST-001`, `TEST-002`, `TEST-008`, `TEST-013`–`TEST-017`, `TEST-038`, `TEST-052`. `records.py`, `_files.py`, `_rename.py`, unit saga/ledger tests, and installed saga/rework tests cover defer deduplication, lock/publication integrity, lifecycle moves, durable intent and every named boundary, exact replay, conflict refusal, artifact/directory identity, reset ownership, completed summaries, and systemic second-park halt. The search-only ancestor failure leaves this group incomplete.
- Reports, 13 rows: `ART-012`–`ART-014`, `ART-039`–`ART-041`, `CMD-018`–`CMD-020`, `TEST-018`–`TEST-020`, `TEST-062`. `reports.py`, renderer goldens, identity/recovery tests, overlap tests, and installed report tests cover deterministic audit/report/metrics output, stable sorting, batch scoping, idempotent section replacement, complete returned publication text, contention, nonregular/symlink refusal, and final-state archival.
- Resume, 2 rows: `CMD-016`, `TEST-021`. `resume.py` and resume/characterized-fixture tests cover recovery precedence, build/review/paused/done branches, and purity.
- Selection, 3 rows: `ART-036`, `CMD-013`, `TEST-027`. `selection.py`, `paths.py`, and selection/configuration tests cover five-digit ordering, wip priority, backlog fallback, hold exclusion, drain, non-files, symlinks, and configured lifecycle paths.
- Transitions, 3 rows: `CMD-009`, `CMD-015`, `TEST-029`. `transitions.py`, `records.reset_prd_fields`, transition/application tests, and CLI tests cover every accepted and rejected row, full effects, purity, reset delegation, and one CAS transaction.
- Parser/docs, 1 row: `TEST-005`. `cli.py`, `workflow_cli.py`, and `test_workflow_docs_are_generated_from_the_live_parser` bind `docs/operations.md` and the state-protocol command inventory to the live parser.

P02 task reconciliation:

- P02-T01–T05: implemented with direct unit and CLI coverage.
- P02-T06: ledger semantics and crash replay are implemented, but configured-path support is incomplete at restricted ancestors; root handling also has one concrete redundancy.
- P02-T07–T08: implemented with boundary, replay, publication, golden, and installed-command coverage.
- P02-T09: configured roots replaced the legacy hardcoded root, but the restricted-ancestor failure prevents unconditional acceptance.
- P02-T10: parser-generated documentation is directly equality-tested.

Exit reconciliation:

- Phase A: covered by characterized lifecycle fixtures, exhaustive transition/rejection rows, state-application tests, and pure-function tests.
- Phase B: fail because P02-T06/P02-T09 reject an otherwise traversable configured runtime solely due to permissions outside that runtime.
- Phase C: covered by installed command-family tests, renderer goldens, parser/document equality, and workflow forbidden-dependency/string checks identified in the reviewed suite.
- Overall PRD acceptance remains incomplete for the same Phase B/configured-path finding.

Evidence limits: I read the complete workflow implementation, the PRD and Phase 2 source plan, the complete 55-row ownership manifest and inventory summaries/evidence references, and the relevant unit/packaging test bodies or test inventories. I did not inspect the historical external source files named by every frozen evidence reference, did not execute the full suite, and did not independently reproduce every failpoint. The supplied HEAD verification remains the execution evidence: 1352 passed, zero failed/skipped, with ruff, format, mypy, and build successful.

The exact probe directory `/private/tmp/tmp2uu0d1ev` was removed with scoped `rmdir` calls after permissions had already been restored; a subsequent existence check printed `removed`.

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

## Blake

The finding is unsupported and should be withdrawn.

The authoritative sources do not establish a non-overridable ceiling:

- `implementation-plan.md:668` requires the “plan-size policy.”
- `implementation-plan.md:1161` requires P02-T04 to “Port resume mapping and plan-size policy.”
- `current_system.toml:3940-3943` defines the behavior as comparing a real task list against “the ceiling.”
- Most decisively, `current_system.toml:4426-4431` says `cli/test_policy.py` characterizes “the fifteen-task plan ceiling, override semantics, tolerant task counting, no mutation, CLI exposure, and missing-state failure.”

Therefore `--ceiling` is part of the mandatory characterized behavior, not scope creep.

Implementation evidence inspected:

- `src/ovcaq/workflow/policy.py:8` sets the default ceiling to 15.
- `src/ovcaq/workflow/policy.py:15-22` accepts an override and compares task count against it.
- `src/ovcaq/workflow_cli.py:91-99` exposes `check-plan --ceiling`, defaulting to 15.
- `src/ovcaq/workflow_cli.py:220-230` validates plan shape, applies the selected ceiling, and returns `OVERSIZED_PLAN` with the count and ceiling.
- `docs/operations.md` is generated from the parser and identifies the option.
- The inspected CLI test demonstrated `--ceiling -1` produces `oversized_plan`. That behavior looked suspicious in isolation, but the characterized contract explicitly requires override semantics and does not specify a positive-only domain. It cannot support a blind-review defect.

Coverage actually inspected:

- P02-T01: `selection.py`, `paths.py`, selection/configuration tests.
- P02-T02: `frontmatter.py`, frontmatter/application/CLI tests.
- P02-T03: `transitions.py`, row/rejection/application/CLI tests.
- P02-T04: `resume.py`, `policy.py`, characterized fixtures and policy/CLI tests.
- P02-T05: completion/reset logic in `records.py` and application/record tests.
- P02-T06: defer implementation in `_files.py`/`records.py` and deferred-ledger tests.
- P02-T07: park/stall saga in `records.py`, `_files.py`, `_rename.py`, including durable-boundary, identity, publication, and replay tests.
- P02-T08: `reports.py`, golden/report identity/recovery/publication tests.
- P02-T09: configuration/path implementation and legacy-path/provider-boundary searches/tests.
- P02-T10: parser-derived command reference in `cli.py`, `workflow_cli.py`, `docs/operations.md`, and parser/docs contract tests.
- Phase exit evidence: characterized lifecycle tests, saga interruption tests, package boundary guards, installed CLI/report/saga tests.
- Verification run: 431 selected workflow/packaging tests passed; Ruff and mypy passed.

Corrected report:

[BLAKE] ✅ No issues found
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

Unavailable before inference: API 429, five-hour quota exhausted, resets at
19:50 Europe/Prague. Static doubt/de-slop review did not run. No R or D raw
verdict exists for this cycle and none is fabricated. Intended provider Claude,
requested alias opus; raw model usage is empty, so no actual model is inferred.

## Carl

Unavailable: runner exit 3, `refusing nested dispatch (already inside a CLI agent)`.
No model was dispatched or output consolidated.

Verdict: 3 findings
Tests: 1352 passed, 0 failed, 0 skipped (reused from last-verification.json at be5e385bd9714952b4803ee30f7c72e661c278f2)
