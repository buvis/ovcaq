# Repair readiness — 2026-10-07

## 00052 premise failure — 2026-10-10

00052 is blocked before implementation: installed `mise exec -- codex --version`
reports `codex-cli 0.162.1`, while its execution premise requires exact 0.160.1.
The strict 0.160.0 adapter guard and historical evidence remain unchanged.
R8 and R17 remain unresolved; no 00052 verification or fresh review ran.
See [blocker and resume boundary](00052-build-blocker.md) and its raw version
evidence. The workflow parks 00052 and continues with approved 00053/00054 in
fresh sessions. This is not repair success or final batch reassessment.

## Current cycle-2 review update — 2026-10-10

PRD 00051 full fresh Alice/Blake/Bob Anthropic reviews at b289ae4 are complete. All three agree on a residual HIGH late-control-split credential-suffix leak. Cycle 2/2 cap reached: HIGH and two remaining documentation/acceptance findings deferred, no cap increase or repair. Source 00009 cycle-2 R7 Unicode continuity has current fixture/subprocess/full-suite closure; source R2 intended split-token safety remains unresolved despite its original exact cap reproducer passing. 6981 tests and all lint/format/type/build gates pass; this does not prove R2 success. See 00051 review-2, immutable receipts and cycle2-review-evidence. Batch not complete; 00052–00054 have not run and 00010 remains held. Final four-PRD reassessment remains required. Historical text below is retained.


Latest review update, 2026-10-10: PRD 00051 cycle 1 completed all three opposite-company Claude Opus5.5/xhigh lenses with full rubrics and immutable receipts. Coordinator current-HEAD verification at 4c84d4d passed 6884 tests, lint/format/mypy/build and sync after an approved retry for sandbox ps denials. The original R7 Unicode and R2 cap regressions have review evidence, but a new HIGH (review-1 R5) reproduces word-boundary loss in strip-first redaction for synthetic bare/Bearer tokens. Repair is not complete: four grouped rework tasks 6–9 are queued, cycle stays 1 with cap 2, and no repair ran in the review session. Nine in-scope fixes are queued; broader TUI reconstruction/cyclic direct containers/exception-path surrogates/custom non-JSON drivers remain durable settled deferrals in review-1 and its ledger/state. Detailed audit: [00051 review cycle 1](../../reviews/00051-triage-a-single-valid-codex-record-can-crash-th-v1-review-1.md). PRDs 00052–00054 have not run; 00010 and other held PRDs remain held. Final four-PRD reassessment is still pending. Earlier recovery paragraphs are retained history, not current blockers.

Latest build update, 2026-10-10: PRD 00051 has all five tasks committed and build verification green at code HEAD0961e40. Full pytest6884passed/0failed; lint/format/type checking/build passed, with two pre-existing pytest cleanup warnings. Initial packaging/lint/format failures and source-preserving repairs remain in 00051-build-evidence.md and 00051-verification-first-run.json. R7 and R2 have build closure evidence but remain unresolved pending fresh full completion review. PRDs00052–00054 have not run;00010 remains held, with provisioning/publication/apply work outside this repair phase. This is not the final four-PRD readiness reassessment or a claim that the intended repair batch succeeded. Historical recovery records below remain unchanged and do not describe current execution state.

Latest recovery update, 2026-10-10 10:00 Europe/Prague: verified batch
202610092123, build → build, task 1 complete and task 2 in progress, no pause
markers, and a free autocodex runner lock before the authorized unchanged retry.
The runner acquired the lock but could not register in this restricted host.
Both fresh sessions (`b66fa556ac90412cb80349288ee4051c` and
`6ed693ceb5e1487682e148359feb8fd6`) failed before agent startup with
`failed to initialize in-process app-server client: Operation not permitted`.
Their stderr and raw session artifacts are preserved; persistent console output
is `/private/tmp/ovcaq-repair-runner-20261010-retry.log`. Runner PID 96744 exited
1; its lock was verified free afterward. No implementation or verification ran.
Statectl recorded phase/next_phase `paused` and pause reason
`host_execution_blocked`; an operator pause marker also prevents relaunch.
Resume requires a host session that permits the existing launcher, retaining
the saved scope and all safeguards. This session cannot request escalation.
Task-2 partial changes, prior rejection evidence, and all review obligations
remain intact. This update supersedes the state descriptions below.

Latest recovery update, 2026-10-10 09:56 Europe/Prague: the operator said
"I don't know how to repair that, please proceed", authorizing a retry through
the unchanged workflow and safeguards. Statectl recorded that decision, restored
phase/next_phase to build, and cleared pause_reason; the pause-requested marker
was removed. The subsequent networked launch approval was aborted before a
runner was observed: retry console log absent, runner lock free. The operator
then requested a new session. No runner is active. Resume from task 2's partial
work, preserving the provider rejection evidence below. Do not interpret the
earlier paused status below as the current state. No safeguards were relaxed.

Status as of 2026-10-10 resumed recovery: batch paused during PRD 00051 build
after a provider safety rejection. Task 1 is complete, with implementation
b3175de and a fresh recovery run of 957 passing focused tests. Its three LOW
patch findings remain recorded for full review. Task 2 is in_progress; its
independent frame tests are committed as 9688321, while implementation changes
in events/tail.py and CHANGELOG.md remain uncommitted. Tasks 3–5 are pending.
No repair PRD has completed, and no fresh completion review has run.

The approved restart used persistent console output at
`/private/tmp/ovcaq-repair-runner-20261010-resume.log`. Session
`autocodex-sessions/f8fb698e1d3542139c1803ad08a75890.jsonl` ended with a provider
error: "This content was flagged for possible cybersecurity risk." The wrapper
automatically started `c5f2b81d51b04e5d9ff3f0db8c8ddf0a`; the coordinator requested
pause and stopped its owned runner with SIGINT to prevent continued retries.
Exit 130 and a free runner lock were verified. State now records phase/next_phase
paused and pause_reason.site `provider_safety_rejection` via statectl.
Preserve both sessions, original broken-pipe evidence, and partial task-2 work.
Resolve the provider rejection/access requirement before restarting; do not
change providers or prompts merely to evade the safeguard.

The resumed child reran task-1 focused verification (957 passed), recorded in
`00051-build-evidence.md`. Task-2 pre-implementation tests had 245 failures and
passed test-quality/style gates; this is regression evidence, not repair
verification. Full tests/lint/types/build and fresh completion reviews remain
outstanding. Coordinator `git diff --check` passed after stopping the runner.

## Required closure

| PRD | Source findings | Current state |
| --- | --- | --- |
| 00051 | 00009 cycle 2 R2/R7 | Finalized cap-deferred after cycle 2: R7 Unicode/raw-first closure verified; original R2 cap case passes, but late-control credential suffix HIGH remains unresolved. 6981 tests and quality gates green; review-2 R1/R2/R3 retained; held triage 00055 owns HIGH |
| 00052 | R8/R17 | Premise-blocked: installed 0.162.1 differs from required 0.160.1; guard unchanged, both findings unresolved; no implementation/review |
| 00053 | R1/R4/R12/R19/R20/R22/R23 | Behavioral repairs and independent regressions pending |
| 00054 | R3/R10/R11/R27 | Shared projection, display window and documentation pending |

The repair runner must update this table with commits, verification and review
evidence at completion. A drained backlog or cap-deferred PRD is not proof that
these findings were resolved. Full disposition of all 34 source findings is in
[repair triage](repair-triage-20261007.md).

## PRD 00010 reassessment

Verdict: HOLD while repairs run; do not auto-promote with this batch.

The original prerequisites were recorded as completed PRDs 00002–00009, but
00009 closed with unresolved findings. The repairs above address known adapter
readiness issues. Additional historical deferred work remains held and must not
be implicitly treated as resolved.

The provisioning implementation is still absent: files under
`src/ovcaq/provision/` are empty scaffolds and `tests/provision/` does not exist.
00010 also requires independently reviewed/released companion plugins in
`buvis/claude-plugins` and `buvis/codex-plugins`, exact dry-run reconciliation
plans, explicit publication/apply authorization, and real Codex/agoge smoke
evidence. Those outputs have not been produced or authorized by this repair
batch. Launcher-global apply and publication remain later concrete approval
boundaries stated in 00010 itself.

After repair verification, reassess whether to split 00010's headless core
implementation from its attended external release/apply/smoke closeout. Do not
start that work merely because its lower sequence number sorts first.

## Historical unresolved questions (superseded by latest updates)

Provider safety rejection blocked further execution; no scope decision was missing.
External release/apply decisions require
the later implementation and exact plans before they can be presented for approval.

## 00051 finalization — 2026-10-10

Supersedes earlier build/recovery statuses above. All nine tasks completed; full fresh cycle-2 Alice/Blake/Bob review at b289ae4 retained one unanimous HIGH (R1) and cap-overflow MEDIUM R2/R3. Lifecycle completion is cap-deferred, not intended repair success. Source 00009 cycle2 R7 has fixture/process/full-suite closure; broader R2 fragment safety remains open. Eight deferred records migrated to deferred/202610092123-deferred.json; held 00055 is a triage artifact, not authorized repair execution. Review, immutable receipts, implementation audit and 00051-cycle2-verification.json remain preserved. Current gates: 6981 passed, zero failed/skipped, sync/Ruff/format/mypy/build green; two pre-existing pytest cleanup warnings. 00052–00054 pending; final whole-batch reassessment remains due after them. 00010 remains HOLD with unchanged external release/plan/approval boundaries.

## 00053 review cycle 2 — paused before tail, 2026-10-10

All ten completed tasks received fresh full opposite-company Alice/Blake/Bob Opus5.5/xhigh review at307b792. Review2 and immutable receipts retain every R/B/D verdict. Initial Blake's history/diff access was excluded; one fresh restricted replacement succeeded. Twelve consolidated findings: zero CRITICAL/HIGH, two MEDIUM, ten LOW. Eight actionable findings are grouped into queued, unstarted tail tasks11–14; two ambiguities are deferred and two intentional behaviors discarded with exact reasons. No final classification/source-repair success is claimed: source R20 has additional explicit HTTP-context gaps, while source R1 resume semantics and mixed-prefix count R11 need later specified scope. The original bare-status HIGH and prior rework findings are confirmed repaired; all historical evidence remains.

Full current-HEAD verification:7141passed/0failed/0skipped; sync, Ruff lint/format, mypy and build pass after approved process-access retry; two pre-existing cleanup warnings. State is paused at tail_sweep_provenance_contract. Required source tail implementation would change attempt provenance; source forbids another review afterward, while host convergence requires unchanged reviewed provenance. No sweep, cap increase or finalize ran. Proposed operator decision: permit fresh full opposite-company review after the sweep, retaining cap2, or supply a compatible policy. See canonical 00053-review-2, its summary and contract card. 00051 residual HIGH,00052 exact-version hold,00054 pending work and00010 HOLD remain unresolved; final batch reassessment is still due.
