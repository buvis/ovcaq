---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
review: 16
date: 2026-09-14
head_sha: 4011d1a3ce186ae9dcd023e8a7fb4b87412b935d
reviewers: alice,blake,bob
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/reviews/bob-output-00004-16-20260914.txt.receipt.json
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
---

# Review: 00004-workflow-core-v1

Diff range: `7b41798c80e06a2c341d75116a09c752203797f4..4011d1a3ce186ae9dcd023e8a7fb4b87412b935d`

codex_rung_guard: fired (7 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude

Reviewed all 20 completed tasks against PRD/source coverage; incremental implementation-aware diff covers the five files changed since cycle 15. Guard count is the reviewed snapshot: tasks 1, 2, 4, 7, 8, 9, 10 have actual Codex implementation attempts.

Host substitution: Alice and Blake ran as isolated native OpenAI gpt-5.6-sol agents (logical sonnet), with no parent conversation. Blake received PRD and mandatory source contracts only. Bob ran fresh through the autocodex helper as external Claude Opus, supplied the complete Bob persona, D1–D5 doubt rubric and de-slop appendix. His successful immutable receipt supplies the independent non-Codex doubt voice. No Eve or Fable dispatch occurred; the source-compatible guard suffix expresses the explicit Claude Bob host substitution, not an invented fifth reviewer. No native model diversity is claimed.

Carl: unavailable, optional Gemini dispatch guard refused exit 3: `refusing nested dispatch (already inside a CLI agent)`. No output counted, no batch unavailability latch. Bob helper exited 0 and every agent/process was awaited. Optional engram pack unavailable: repo is not registered.

## Decision and consolidated findings

The source consolidator ran successfully; its unchanged output is in `00004-cycle-16-script-consolidation.md`. Model-side adjudication then merged three Alice/Bob duplicates (diagnostic coverage, 51-line function, 80-line test) that its wording/path comparison missed. Both originals remain below. Two [MECH] replay observations were added. This yields 14 table findings plus the separately retained auto-dismissed Blake PRD-root finding.

No unresolved Critical/High remains. All seven actionable Medium/Low findings were closed by one normal D16 tail task; all other rows have verified discard reasons below. The doubt-roster gate passed before the sweep. No scope waiver or new deferral was needed; tail completion and final verification are recorded below.

| ID | Consensus | Severity | Issue | File | Found by |
|----|-----------|----------|-------|------|----------|
| R16-01 | [2/3] | 🟡 | The restored deferred-directory diagnostic has no committed regression covering initial file/symlink refusal or the vanished-directory second open, including full path and preserved cause/errno | tests/packaging/test_rework_13.py | Alice, Bob |
| R16-02 | [2/3] | 🟡 | `_ensure_directory_chain` is 51 lines because it embeds the 13-line ancestry verifier; move that verifier to a named helper to satisfy the function-size limit and simplify the chain walk | src/ovcaq/workflow/_files.py:268 | Alice, Bob |
| R16-03 | [2/3] | 🟡 | `test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry` is 80 lines; extract the safe-result and retry/replay assertion flows into helpers while retaining the parameterized chronology | tests/packaging/test_rework_13.py:357 | Alice, Bob |
| R16-04 | [1/3] | 🟡 | F4: _invoke reimplements subprocess.run's timeout kill/reap as a 16-line Popen block plus a framework-verifying `assert process.poll() is not None`; subprocess.run(timeout=20) already kills and waits on TimeoutExpired, and test_rework_12._invoke in the same diff keeps subprocess.run | tests/packaging/test_rework_13.py:58 | Bob |
| R16-05 | [1/3] | ⚪ | F5: os.mkdir(deferred.name, dir_fd=runtime) failures other than EEXIST (EACCES, ENOSPC, EBADF) still surface raw errno text with the bare name 'deferred'; same class as R15-03, on the create step the acceptance ("every failing open") did not name | src/ovcaq/workflow/_files.py:340 | Bob |
| R16-06 | [1/3] | ⚪ | F6: fix commit 93c049b changed a user-visible diagnostic (full deferred path on open failure) without a CHANGELOG entry; the only added Fixed line covers ancestry revalidation | CHANGELOG.md:24 | Bob |
| R16-07 | [1/3] | ⚪ | F7: reparent-refusal branch hedges `if _ledger(runtime).exists(): _assert_one_record(runtime)`; the shipped chronology deterministically refuses inside the first _read_record_content before any write, so the direct case should pin that no ledger exists | tests/packaging/test_rework_13.py:406 | Bob |

### Discarded after verification

| ID | Consensus | Severity | Issue | File | Found by |
|----|-----------|----------|-------|------|----------|
| Discarded | [1/3] | 🟠 | The final `verify_ancestry()` pass is still racy: replacing an ancestor immediately after its pathname `stat`, then reparenting the unchanged descendant subtree beneath the replacement, lets all later identity checks pass and publication return without confirming the replacement entries; the regression injects before verification begins and misses this window | src/ovcaq/workflow/_files.py:277 | ALICE |
| Discarded | [1/3] | 🟠 | The frontmatter port is incomplete: characterized `doubt_reviewer` and `consensus_engine` controls are silently ignored, while accepted `catchup`, `design`, `design_gate`, and `pause_on_ambiguity` values are returned but not committed, making later overwrite warnings impossible on fresh v1 state | src/ovcaq/workflow/frontmatter.py:15 | BLAKE |
| Discarded | [1/3] | 🟡 | Deferred-ledger reads validate only that items are objects; missing, unsafe, or duplicate `op_id` values survive loading, after which report rendering silently drops or collapses them, violating the operation-ID and no-lost-record contracts | src/ovcaq/workflow/_files.py:227 | BLAKE |
| Discarded | [1/3] | ⚪ | F8: Cannot statically verify: suite/ruff/format/mypy/build at 4011d1a; 1372/0/0 are reused same-HEAD records, not a fresh run | N/A | BOB |
| Discarded | [1/3] | ⚪ | F9: fail-first replay: 12 touched tests pass at base; all are behavior-preserving test edits (origin re-assertions in rework_12's concurrent test, re-parametrized cycle-13/14 regressions in rework_13), the 6 new reparent cases fail at base | tests/packaging/test_rework_13.py | BOB |
| Discarded | [1/3] | 🟡 | 2 touched test(s) pass against the pre-change code: test_installed_concurrent_creation_confirms_and_preserves_peer_directory | tests/packaging/test_rework_12.py | MECH |
| Discarded | [1/3] | 🟡 | 10 touched test(s) pass against the pre-change code: test_installed_defer_refuses_replaced_distant_ancestry_until_fresh_attempt +4 more | tests/packaging/test_rework_13.py | MECH |

- **ALICE: src/ovcaq/workflow/_files.py:277** — Alice retracted after deterministic installed-wheel probe and linearization analysis: direct/replay publication and a complete old-ancestry observation precede the external reparent. The later external mutation owns its directory durability. No success lacking a valid pre-mutation linearization point was found.
- **BLAKE: src/ovcaq/workflow/frontmatter.py:15** — Blake retracted against docs/state-protocol.md and frozen STATE-005/006/007/009/010/011: controls are derived from existing v1 owners. No duplicate state fields required; agent/model selection belongs to runtime.
- **BLAKE: src/ovcaq/workflow/_files.py:227** — Blake retracted: CMD-010 and STATE-113 require valid deduplicated public writes, already enforced; TEST-018 preserves tolerant report handling. No source contract requires semantic validation of externally malformed ledger rows.
- **BOB: N/A** — Verified six exit-0 command records with non-null 1372/0/0 counts at reviewed HEAD 4011d1a3ce186ae9dcd023e8a7fb4b87412b935d. Source requires reuse, not a repeated full suite. Bob labels this KNOWN.
- **BOB: tests/packaging/test_rework_13.py** — Behavior-preserving origin assertions and parametrized existing regressions intentionally pass at base. Six newly added reparent cases fail old production; instrumented replay includes the otherwise unoverlaid actor helper and fails specifically on missing post-reparent fsync.
- **MECH: tests/packaging/test_rework_12.py** — These two existing cases only gain installed-origin assertions; behavior-preserving test coverage passes old code by design.
- **MECH: tests/packaging/test_rework_13.py** — These ten cases preserve earlier behavior while parametrizing/restoring coverage. Six new reparent cases fail old production at the intended fsync assertion with the current actor overlaid.

### Auto-dismissed (ledger)

- [BLAKE] 🟠 Configured `prd_root` is never containment-checked, and absolute or `..` paths are resolved directly; `stall`/`park` can therefore move files outside the resolved project despite the source security contract allowing only an explicitly external state root | File: src/ovcaq/config.py:87 — Blake retracted: containment is specified for runtime roots, not all configured PRD roots. Absolute external PRD roots are deliberately supported; treating that explicit configuration as a containment violation extends the requirement.

Blake's independent source-only follow-up also retracts this finding. Every discard is appended with its verbatim issue to the settled ledger.

## Coverage and evidence

Accepted source plan SHA256: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
Frozen inventory SHA256: `d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9`.
Audit: `00004-cycle-16-source-audit.json` verifies all 55 owned Phase 2 migration rows and eight target routes. Alice and Blake explicitly evaluate P02-T01–T10, PRD Phase A/B/C exits, and all three source Phase 2 exits below. Final source coverage passes; Alice/Bob R1 and R12 retain the diagnostic-test and size-limit tail findings.

Prior-cycle reconciliation: Bob verifies R15-01–07 in code. Diagnostic regression coverage is the remaining R15-03 gap. Six new reparent scenarios cover distances 1, 3 and 5 in direct/replay forms; current proof preserves installed-wheel module origins.

Mechanical evidence: `00004-cycle-16-mechanics.md` retains computed function spans, shape checks, sandbox refusal, approved base replay and its 18-case result (6 fail, 12 pass). The initial replay did not overlay the actor helper, so the separate approved `instrumented_replay_16.py` repeated the six new cases with the current actor: `00004-cycle-16-instrumented-replay.json` confirms all six fail old production at the missing post-reparent fsync assertion. Temporary worktrees were removed.

Race adjudication: `final_stat_probe_16.py` and `00004-cycle-16-final-stat-probe.json` preserve installed-wheel direct/replay proof and timing. Success after an external swap on the final ancestry stat is real, but publication plus complete ancestry observation linearize before that swap; Alice retracts the hypothesized defect below.

Verification record at the exact reviewed HEAD contains all six required successful commands: uv sync --all-groups, pytest, Ruff lint, Ruff formatting, mypy and uv build, all via mise. Counts are reused as mandated, not presented as a new full-suite run. Previous checks queue was empty; this cycle's VERIFY bucket is empty and checks-16.json is [].

## Alice

[ALICE] 🟠 The final `verify_ancestry()` pass is still racy: replacing an ancestor immediately after its pathname `stat`, then reparenting the unchanged descendant subtree beneath the replacement, lets all later identity checks pass and publication return without confirming the replacement entries; the regression injects before verification begins and misses this window | File: src/ovcaq/workflow/_files.py:277 | Task: 9
[ALICE] 🟡 The restored deferred-directory diagnostic has no committed regression covering initial file/symlink refusal or the vanished-directory second open, including full path and preserved cause/errno | File: tests/packaging/test_rework_13.py | Task: 9
[ALICE] 🟡 `_ensure_directory_chain` is 51 lines because it embeds the 13-line ancestry verifier; move that verifier to a named helper to satisfy the function-size limit and simplify the chain walk | File: src/ovcaq/workflow/_files.py:268 | Task: 9
[ALICE] 🟡 `test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry` is 80 lines; extract the safe-result and retry/replay assertion flows into helpers while retaining the parameterized chronology | File: tests/packaging/test_rework_13.py:357 | Task: 9
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
R12: fail
R13: pass

### Source and timing adjudication (raw supplement)

Supplement to the unchanged initial report:

The High finding should be discarded after linearization analysis.

The proposed deterministic interleaving is:

1. Wrap `_append_deferred_record`; call the real function and arm the race only after it returns.
2. This targets `_open_deferred_ledger`’s final `verify()` at line 362.
3. During `verify_ancestry`, let `os.stat(ancestor)` obtain the original inode.
4. Before returning that stat result, rename/recreate the ancestor and reparent the unchanged descendant subtree beneath it.
5. Return the original stat result. Remaining descendant identities match, so verification and `record_defer` succeed.

This does reproduce success, but it does not establish the reported defect. The complete old ancestry existed when the target stat occurred, and direct publication or exact-replay syncing had already completed before the wrapper armed the race. The ancestry validation therefore has a valid linearization point immediately before the external swap. The external actor’s subsequent rename is responsible for its own directory durability.

If the mutation occurs before the target stat, the replacement is detected. If it occurs after the target stat, the completed publication and ancestry observation can linearize before it. I found no interleaving where OVCAQ adopts the replacement during publication, misses it in every later verification, and succeeds without a valid pre-mutation linearization point. The committed regression covers the relevant earlier mutation and refuses it. This changes R9 to pass; R1 remains failed for the missing diagnostic regression.

P02-T01: pass — `selection.py`, `test_selection.py`, and installed workflow-input tests cover WIP-first ordering, backlog fallback, hold exclusion, lifecycle paths, and configured roots.

P02-T02: pass — `frontmatter.py`, `test_frontmatter.py`, `test_applications.py`, and installed CLI tests cover defaults, validation, abstract tiers, overwrite warnings, and application.

P02-T03: pass — `transitions.py`, `test_transitions.py`, and application/CLI tests cover every transition and rejection row with compound state effects.

P02-T04: pass — `resume.py`, `policy.py`, `test_resume.py`, `test_policy.py`, and workflow CLI tests cover resume precedence and configurable plan ceiling behavior.

P02-T05: pass — `records.py`, `test_records.py`, and `test_applications.py` cover per-PRD reset ownership, batch preservation, deterministic summaries, rejection, and idempotency.

P02-T06: pass — `_files.py`, deferred-ledger, ledger-integrity/publication, installed-saga, and rework 11–13 tests cover operation-ID deduplication, serialization, durability, replay, ancestry replacement, and state-byte preservation. R1 remains failed because the restored full-path diagnostic has no committed file/symlink/second-open regression.

P02-T07: pass — saga, saga-artifact, saga-identity, saga-publication, and installed-saga tests cover park/stall intent, move, record, reset, commit, failpoints, and reconciliation.

P02-T08: pass — report, report-identity, report-recovery, installed-report, report-update, and golden tests cover deterministic audit/report/metrics rendering and serialized publication.

P02-T09: pass — configuration, boundary, installed workflow-input, and ancestry tests cover configured runtime paths and contain no production `dev/local/autopilot` reference.

P02-T10: pass — `test_workflow_cli.py` verifies `docs/operations.md` exactly equals output generated from the live parser and checks the state-protocol inventory.

Phase A: pass — characterized lifecycle fixtures plus selection, frontmatter, transition, resume, policy, reset, and completion suites match the v1 outcomes.

Phase B: pass — deferred and park/stall suites cover direct operation, interruption, reconciliation, exact replay, duplicate prevention, directory identity, and installed-wheel execution. The missing diagnostic regression is a rubric testing gap rather than a failed durability-boundary outcome.

Phase C: pass — all workflow commands, report surfaces, generated documentation, provider-string guards, and dependency guards are present and covered.

Source Phase 2 exit 1: pass — characterized lifecycle fixtures have equivalent OVCAQ outcomes under the v1 schema.

Source Phase 2 exit 2: pass — park/stall interruption is recoverable at every represented durable boundary without duplicate records or lost work.

Source Phase 2 exit 3: pass — workflow imports only state and standard-library/lower-layer modules; the boundary guard passes.

The cycle-16 source audit confirms the accepted-plan digest, frozen-inventory digest, all 55 Phase 2 migration rows, and all eight target routes at reviewed HEAD `4011d1a`. Recorded verification at that HEAD reports 1372 passed, zero failed, zero skipped, with sync, Ruff, mypy, and build successful.

## Blake

[BLAKE] 🟠 Configured `prd_root` is never containment-checked, and absolute or `..` paths are resolved directly; `stall`/`park` can therefore move files outside the resolved project despite the source security contract allowing only an explicitly external state root | File: src/ovcaq/config.py:87 | Task: P02-T01
[BLAKE] 🟠 The frontmatter port is incomplete: characterized `doubt_reviewer` and `consensus_engine` controls are silently ignored, while accepted `catchup`, `design`, `design_gate`, and `pause_on_ambiguity` values are returned but not committed, making later overwrite warnings impossible on fresh v1 state | File: src/ovcaq/workflow/frontmatter.py:15 | Task: P02-T02
[BLAKE] 🟡 Deferred-ledger reads validate only that items are objects; missing, unsafe, or duplicate `op_id` values survive loading, after which report rendering silently drops or collapses them, violating the operation-ID and no-lost-record contracts | File: src/ovcaq/workflow/_files.py:227 | Task: P02-T06

P02-T01: fail
P02-T02: fail
P02-T03: pass
P02-T04: pass
P02-T05: pass
P02-T06: fail
P02-T07: pass
P02-T08: fail
P02-T09: pass
P02-T10: pass

Phase A exit: fail
Phase B exit: pass
Phase C exit: fail
Phase 2 lifecycle-equivalence exit: fail
Phase 2 interruption-recovery exit: pass
Phase 2 dependency-boundary exit: pass

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
B16: pass
B17: fail
B18: pass
B19: pass

### Source-only adjudication (raw supplement)

1. RETRACTED — `prd_root` containment belongs to §7/P03-T01, owned by PRD 00005. P02-T01 only requires configured lifecycle resolution, and the characterized contract explicitly preserves absolute PRD roots.

2. RETRACTED — `STATE-005/006/007/009/010/011` are explicitly derived from `batch.catchup`, `work.design_doc`, `control.pause_reason`, and `review.lenses`; they must not be duplicated. Agent/model selection belongs to runtime configuration. P02-T02 retains the required neutral parsing/defaults, `review.cap`, abstract tier-floor resolution, unavailable-tier warning, and overwrite-warning behavior.

3. RETRACTED — No frozen contract requires semantically malformed on-disk ledger rows to fail loading. `CMD-010` requires appending a caller object with PRD attribution; `STATE-113` requires operation-ID deduplication for writes. Public writes require valid `op_id` values and reject conflicting replay. `TEST-018` explicitly preserves tolerant missing report data.

[BLAKE] ✅ No issues found

P02-T01: pass
P02-T02: pass
P02-T03: pass
P02-T04: pass
P02-T05: pass
P02-T06: pass
P02-T07: pass
P02-T08: pass
P02-T09: pass
P02-T10: pass

Phase A exit: pass
Phase B exit: pass
Phase C exit: pass
Phase 2 lifecycle-equivalence exit: pass
Phase 2 interruption-recovery exit: pass
Phase 2 dependency-boundary exit: pass

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

External Claude Opus output follows; the immutable original and receipt are linked in top matter. Only heading depth is adjusted for containment in this reviewer section.

### Prior-cycle reconciliation

- **R15-01** resolved: `_ensure_directory_chain` records every confirmed level in `ancestry` and yields `verify_ancestry`, which re-lstats the whole chain on every `verify_lock()` call (read, lock, publish, post-fsync, post-yield); park/stall reach it through the same `_open_deferred_ledger` verify. The 6 new reparent cases (distance 1/3/5 × direct/replay) fail at base for the intended reason (base returns 0 without post-reparent fsyncs).
- **R15-02** resolved: `assert_installed` on `_invoke`/`_await_event`/`_finish` (rework_12, incl. the exit-73 crash output) and `_invoke` (rework_13).
- **R15-03** resolved in code (both opens wrapped, cause chained, identity error inside the handler correctly escapes the outer `except OSError`) but ships without a regression test (F1).
- **R15-04/05/06/07** resolved (42-line parametrized test; `parent_stat`/`level_stat`; distance-1 restored; unused capability keys removed, consumers intact).
- Source reconciliation: P02-T01–T05, T08, T10 unchanged; T06/T07/T09 and the Phase B durable-boundary exit are now satisfied by the full-chain revalidation. Suite delta +8 (1364→1372) matches the added cases exactly.

### Findings

```
[BOB] 🟡 F1: R15-03 diagnostic fix has no regression test: no test places a symlink or regular file at runtime/deferred and asserts "deferred directory is not a real directory: <full path>" with the ELOOP/ENOTDIR cause chained; only the ad-hoc cycle-15 diagnostic probe exercised it | File: src/ovcaq/workflow/_files.py:336 | Task: 9
[BOB] 🟡 F2: _ensure_directory_chain grew to 51 lines (mechanical facts) with the nested verify_ancestry closure, over the 50-line limit; growth is introduced by this diff | File: src/ovcaq/workflow/_files.py:268 | Task: 9
[BOB] 🟡 F3: test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry is 80 lines (mechanical facts; task 9 style gate flagged it and it was left unfixed) | File: tests/packaging/test_rework_13.py:357 | Task: 9
[BOB] 🟡 F4: _invoke reimplements subprocess.run's timeout kill/reap as a 16-line Popen block plus a framework-verifying `assert process.poll() is not None`; subprocess.run(timeout=20) already kills and waits on TimeoutExpired, and test_rework_12._invoke in the same diff keeps subprocess.run | File: tests/packaging/test_rework_13.py:58 | Task: 9
[BOB] ⚪ F5: os.mkdir(deferred.name, dir_fd=runtime) failures other than EEXIST (EACCES, ENOSPC, EBADF) still surface raw errno text with the bare name 'deferred'; same class as R15-03, on the create step the acceptance ("every failing open") did not name | File: src/ovcaq/workflow/_files.py:340 | Task: 9
[BOB] ⚪ F6: fix commit 93c049b changed a user-visible diagnostic (full deferred path on open failure) without a CHANGELOG entry; the only added Fixed line covers ancestry revalidation | File: CHANGELOG.md:24 | Task: 9
[BOB] ⚪ F7: reparent-refusal branch hedges `if _ledger(runtime).exists(): _assert_one_record(runtime)`; the shipped chronology deterministically refuses inside the first _read_record_content before any write, so the direct case should pin that no ledger exists | File: tests/packaging/test_rework_13.py:406 | Task: 9
[BOB] ⚪ F8: Cannot statically verify: suite/ruff/format/mypy/build at 4011d1a; 1372/0/0 are reused same-HEAD records, not a fresh run | File: N/A | Task: general
[BOB] ⚪ F9: fail-first replay: 12 touched tests pass at base; all are behavior-preserving test edits (origin re-assertions in rework_12's concurrent test, re-parametrized cycle-13/14 regressions in rework_13), the 6 new reparent cases fail at base | File: tests/packaging/test_rework_13.py | Task: general
```

### Buckets

```
FIX:
- F1 — tests/workflow/test_deferred_ledger.py — add `test_defer_refuses_non_directory_deferred_with_full_path` parametrized over ("symlink", "regular-file") at runtime_root/"deferred"; assert `pytest.raises(OSError, match=f"deferred directory is not a real directory: {re.escape(str(deferred))}")`, `error.__cause__.errno in {errno.ELOOP, errno.ENOTDIR}`, and the symlink/file object untouched
- F2 — src/ovcaq/workflow/_files.py:277 — hoist to module-level `_verify_ancestry(ancestry: dict[Path, tuple[int, int]]) -> None` and `yield directory, partial(_verify_ancestry, ancestry)`; drops the function to ~38 lines, no behavior change
- F3 — tests/packaging/test_rework_13.py:386-407,414-436 — extract `_assert_reparent_outcome(result, index, runtime, ancestor)` (the exit 0/2 branch) and `_assert_fresh_attempts_confirm(installed, project, runtime, ancestor, previous_runtime, seeded, authoritative, displaced_runtime)` (retry + exact replay); test body falls under 50
- F4 — tests/packaging/test_rework_13.py:58-81 — revert to `subprocess.run([...], cwd=project, env=installed.environment, capture_output=True, text=True, check=False, timeout=20)` exactly as test_rework_12._invoke; drop the poll assert
- F5 — src/ovcaq/workflow/_files.py:339-342 — after `except FileExistsError: pass` add `except OSError as error: raise OSError(f"deferred directory could not be created: {deferred}") from error`
- F6 — CHANGELOG.md — add under Fixed: "Deferred directory open failures name the full configured path and chain the original errno."
- F7 — tests/packaging/test_rework_13.py:406-407 — replace with `if not replay: assert not _ledger(runtime).exists()` (replay bytes are already pinned at line 409)
VERIFY:
- (none)
KNOWN:
- F8 — read-only static sandbox cannot execute gates; same-HEAD exit-0 records for all six commands exist in the review context and are reused, not re-run
- F9 — task 10 is test-only by acceptance (restore origin proof, re-parametrize existing regressions), so those 12 tests passing at base is by design; the product change is pinned by the 6 reparent cases that fail at base
```

### Rubric verdicts

```
R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: fail
R13: pass
```

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

**Status**: Done.
**Changed**: nothing (review only); 9 findings = 7 FIX + 0 VERIFY + 2 KNOWN; R1/R12 fail, rest pass.
**Next**: Task complete. Suggested next: route F1–F4 into the rework loop, batch F5–F7 as a LOW multi-select.

## Follow-up

Seven quoted findings were completed in task 11 through the state CLI, with classifier-selected tier and a normal rework pipeline. Original reviewer verdicts above describe the reviewed HEAD; the tail implementation and its final verification are recorded separately below.

Verdict: 14 findings
Tests: 1372 passed, 0 failed, 0 skipped (reused from last-verification.json at 4011d1a3ce186ae9dcd023e8a7fb4b87412b935d)


## Tail completion

Task 11 closed all seven findings at `2742c08fe5f8194f65a36fa1e49a5980d69c16ef` through the normal lean work pipeline. Tests were committed before implementation; the intended diagnostic red cases failed and all six subsequently passed. Style and split gates passed; fresh self-deslop returned no slop found.

Pat's fresh external Claude Sonnet retry ran after the confirmed quota reset, exited 0, and produced seven resolved CLOSURE verdicts. Its two LOW notes were refuted by source inspection; both raw notes and reasons remain in `00004-cycle-16-pat-result.json`. No tail finding remains open.

Final tail verification: 1378 passed, 0 failed, 0 skipped; sync, Ruff, format, mypy and build all exited 0 at this HEAD. The runner emitted two pytest garbage-cleanup warnings. Cycle-16 queued checks are empty. [Work report](00004-cycle-16-tail-work-report.md) contains the commits, route/model evidence, full verification references, cleanup manifest and complete assumption ledger.

The original reviewer sections and their verdicts above remain the evidence for reviewed HEAD `4011d1a`. Task 11 adds an eighth task with an actual Codex implementation attempt after that snapshot; the original guard count of seven remains accurate for the PRD reviewers' input. All 21 tasks are now complete. The next session is finalize; no new review cycle is required by the converged tail-sweep procedure.
