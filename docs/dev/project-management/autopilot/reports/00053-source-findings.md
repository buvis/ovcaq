# PRD 00053 source-finding repair evidence

All rows are implemented, with fresh full review pending. Historical findings and deferred evidence remain unchanged. This build report does not establish final closure.

Source: `reviews/00009-codex-adapter-v1-review-2.md`, relative to the autopilot directory.

| Source ref | Repair | Evidence |
|---|---|---|
| R1, line 80 | Completed lanes remain terminal; only unfinished lanes receive synthetic failures. Late progress and repeated closure cannot reopen them. | Task 5; commits 0c9214f, 2b7a62d; `test_adapter_outcomes.py`, 49 cases passed. |
| R4, line 83 | “Selected model is at capacity” is connectivity, entering bounded WAIT and eventually exhausting retry. | Task 6; commit 4074403; `test_adapter_failure_classes.py` and terminal/rework fixtures. |
| R12, line 91 | Failure fixtures use independent literal expected classes. | Task 6; four fixture families in failure-class, terminal, failure and rework tests; 255 cases passed. |
| R19, line 98 | Supervised Codex consumes the already resolved model once. Direct Codex tier precedence remains unchanged. | Task 2; commit b137ad1; configured fake supervisors exercise three phases and collisions, direct factory/driver checks; 96 cases passed. |
| R20, line 99 | Numeric status codes need diagnostic context; ordinary counts do not determine failure class. Existing precedence and reset parsing remain intact. | Task 6; commit 4074403; explicit status context, count negatives, boundaries and long-tail regressions. |
| R22, line 101 | Both native adapters have effective-PATH coverage and real public CLI rejection checks before session execution/publication. | Task 3; commit 115a453; `test_adapter_health.py`, 28 cases passed. |
| R23, line 102 | Claude executable discovery uses the child environment PATH, including inherited and standard missing/empty-host behavior. | Task 3; overlay-only, hidden-host, multi-entry, executable bits, absolute paths, symlinks and fallback regressions. |

Driver API 2, observation protocol 1 and state schema 1 remain unchanged. Documentation is aligned in commits 9f6ea75 and 6c1b3f2. Pat LOW findings and workflow deviations are retained in the task reports and build-progress report for fresh review.

Full verification at 6c1b3f2: 7,165 tests passed, two existing temporary-directory warnings; dependency sync, Ruff lint, mypy and build passed. Formatter initially failed on three test files. One correction cycle committed AST-preserving formatting at 85d6029, 68b15e6 and 426ce90; the full formatter check then passed for 236 files. Only the failed command was rerun, as required. Final verification counts are null because the suite ran before those formatting commits; the exact historical counts remain in `00053-verification-initial.json`.

Other repair-batch findings are not closed here: PRD 00051 has its unresolved HIGH; PRD 00052 remains held on the strict launcher-version mismatch. PRD 00054 is next after this PRD completes review/finalization. PRD 00010 and other held PRDs remain held.

## Fresh review 1 — 2026-10-10

Alice, Blake and isolated Bob completed opposite-provider Opus/xhigh reviews with immutable receipts. The canonical `reviews/00053-adapter-operational-corrections-v1-review-1.md` preserves all rubric verdicts and source-ref outcomes. The review does not converge: all three identify a HIGH gap in bare `status N` numeric diagnostics, leaving source R20 unresolved. Lane raw-evidence coverage, PATH documentation/test discrimination and simplification follow-ups remain open. Four exact-finding rework tasks (7–10) are queued; cycle remains 1, cap remains 2.

Current reviewed HEAD `bade6a5d9eae960f515eeffda84349eb7a50bc81` passes 7,165 tests, zero failures/skips, sync, lint, format, mypy and build. The first Bob output exposed sibling reviewer logs through a broad search and was excluded; its raw evidence remains intact. The fresh replacement used bounded searches and showed no sibling-output exposure. Verification evidence is `00053-review-1-verification.json`; no final source-closure or batch-success claim is made.

## Cycle-1 rework — fresh session, 2026-10-10

Tasks7–10 now have committed repair and per-task Pat closure evidence; full PRD closure awaits fresh cycle2 Alice/Blake/Bob review. R20's bare native status HIGH has literal four-message regressions and a bounded regex repair (f9584e8, b42b99b). R1's completed-lane close now pins RAW_UNKNOWN, and completed/failed late updates have exact terminal expectations and no lane/raw observation assertions (b42b99b, de8dec1). The protocol now documents failed-lane freezing and terminal-close raw evidence accurately. Duplicate inverse-tier logic shares one private helper; direct tier semantics remain unchanged. R12/R22 independent literal oracles and fake-only verification remain intact.

The acceptance command now names diagnostic coverage; receiver-name padding and unrelated/non-boundary factory tests were removed (de8dec1). R23/R22 empty-host-PATH docs distinguish adapters (7f195ec), and the fake executable now exists in the test cwd (90f69bc). Task10's first helper-directory edit failed FileExistsError; corrected before task completion, preserving both commits. No provider inference, CLI-version relaxation, new API, enum or schema was introduced.

Pat marked every quoted task finding resolved. Residual LOW observations are retained in 00053-rework-1-evidence/pat-7.txt (terminal-close raw flag noise) and pat-8.txt (remaining overlapping outcome controls); they are inputs to the fresh full review, not silently dismissed. Existing Codex probe caller/request-root cwd deferral remains unresolved. This rework does not close PRD00051's HIGH, PRD00052's strict-version hold, or PRD00010 provisioning prerequisites. Canonical cycle1 audit/snapshot, historical source refs and immutable provider receipts remain unchanged. New actual implementation metadata is retained in 00053-rework-1-model-evidence.md and its raw logs for cycle2 audit regeneration.

Final rework verification at90f69bc:7141 passed,0 failed/skipped, two existing pytest cleanup warnings; sync, lint, format, mypy and build pass. See 00053-rework-1-verification.json. Fresh full cycle2 remains mandatory before final source closure.

## Cycle 2 full review — 2026-10-10

Fresh full Alice/Blake/isolated Blake replacement/Bob evidence is retained; only accepted Alice/Blake/Bob form consensus. Review2 confirms original bare-status HIGH and earlier rework closures. Source R20 still has explicit HTTP-context forms left UNKNOWN (review2R1) and a mixed-prefix ordinary-count ambiguity (R11). R1 completed-lane stability is pinned; restarted-agent identity semantics R3 are deferred rather than guessed. R4/R12/R19 capacity, independent oracles and Codex once-resolved model regressions pass; extra Claude helper caller coverage R7 is queued. R22/R23 PATH repairs are confirmed, with stronger missing-PATH coverage R10 and wording tail queued. No complete intended repair success or final source closure is asserted while tasks11–14 remain unimplemented.

Actual reviewed HEAD307b792:7141 passed,0failed/skipped; all sync/lint/format/type/build gates pass. Cycle2 contains no CRITICAL/HIGH, but the mandated tail sweep conflicts with host provenance-at-convergence: source step4 forbids a post-sweep review, host requires receipts for unchanged implementation provenance. Pause is persisted before any sweep work; cap2 unchanged. Exact review findings, classifications, receipts and raw provenance remain preserved. Other repair-batch blockers are unchanged.
