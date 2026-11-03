# FT-04R12 review handoff — paused

Reviewed HEAD: `39ecaf4f95c79df6a88c30e4626386a352d1505b` on `master`; product
tree unchanged. Full range starts at `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`.

Cycle 12 completion review ran all three required lenses: isolated native Codex
Sol Alice and Blake, plus fresh external Claude Opus Bob. Every raw R/B/D verdict
is retained. Bob's successful receipt and immutable raw output validate. Carl's
runner refused nested dispatch before a provider call; no guard was bypassed.
All reviewers and processes were awaited.

Canonical review: `dev/local/reviews/00004-workflow-core-v1-review-12.md`.
Evidence: `dev/local/reviews/00004-workflow-core-v1-review-12-evidence.md`.
Bob receipt: `dev/local/reviews/00004-cycle-12-bob-retry-output.txt.receipt.json`.

**CHANGES_REQUESTED.** Coordinator finding R12-01 confirms a remaining runtime
ancestor durability gap: exit a process after mkdir but before parent fsync;
fresh installed retry and exact replay return success without confirming that
parent entry. Existing caught-error regressions pass because their cleanup runs.
This is syscall durability evidence and consequent data-loss risk, not an
observed physical power-loss experiment.

The source run-autopilot Error Handling row mandates PAUSE on detected data-loss
risk. State was committed through statectl: phase/next_phase `paused`, cycle 12
unchanged, pause_reason.site `data_loss_risk`, 13 tasks/10 completed, pending IDs
1–3, all reviewer statuses recorded, and Claude-sourced D1–D5 verdicts retained.
No rework, convergence marker, cycle increment, PRD lifecycle move or next gate.

Pending tasks preserve every accepted finding verbatim:

1. Runtime ancestor confirmation after abrupt exit (R12-01), plus Bob F2 safe
   concurrent creation. Require a chronological installed regression with an
   actual child exit before parent fsync and fresh-process retry/replay.
2. Correct report-publication contention context (Bob F1). Optional error-code
   redesign is not adopted without an accepted contract requirement.
3. Replace redundant fsync evidence and assert failed-call state preservation
   (Bob F3/F5).

Bob F4 is discarded with a verified reason in the settled ledger: the R10 public
Path-returning API and CLI complete-text result deliberately share one publisher.
V1's five gates are satisfied by this cycle's actual runs. Six KNOWN entries
remain recorded; none was silently dropped. Counts: 13 observations = 5 FIX +
1 VERIFIED + 6 KNOWN + 1 DISCARDED, grouped into three repair tasks.

Verification: 1,348 passed in 22.14 seconds, no failures/skips; sync, Ruff,
format, mypy, wheel/sdist and full-range whitespace pass. Full-base mechanical
replay reached the retained missing-packaging_support collection limitation.
Ten source tasks, all 55 owned rows and every phase exit were reconciled; the
all-durable-boundaries exit remains blocked by R12-01.

A later authorized repair session must read the canonical review and the queued
task descriptions, implement only those bounded fixes, preserve the listed
R8/R9/R10/R11 invariants, run the work pipeline, and hand off to a fresh review
process. Do not treat this pause or green existing tests as PRD completion.

Unresolved questions: none about the defect; repair is pending at the persisted
safety pause.
