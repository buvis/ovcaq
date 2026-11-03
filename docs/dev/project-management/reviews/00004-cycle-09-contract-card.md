# PRD 00004 — FT-04R9 contract card

Current step: fresh completion review complete; CHANGES_REQUESTED.
Reviewed HEAD: `78f916c366f74105b76e6f07d80a7a1aeb251e9f`.
Full base: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`.
Residuals: 5 FIX, 0 VERIFY, 4 KNOWN. No implementation edits this review.

Active invariants: exact-HEAD/clean-state preflight; all ten source tasks/55 rows;
one state writer; durable evidence and original artifact identity survive;
successful competing ledger records survive; state remains authoritative;
provider code stays at the edge; no live launcher reads; no shell evaluation.
Keep all R8 preservation checks, accepted null-artifact/derived-state ownership,
inherited R8-K1/R8-K2, and downstream runtime/provider/Linux ownership.

Next gate: fresh FT-04F9 work session addresses R9-01–R9-05 with bounded repairs
and retained regressions, runs full verification, then hands off and stops for
fresh FT-04R10 review. All isolated lenses and full R/B/D rubrics run again.
No autopilot state, plan edits, PRD closeout, capsule refresh or next PRD.

[Verdict](00004-workflow-core-v1-fast-review-09.md) ·
[Evidence](00004-workflow-core-v1-fast-review-09-evidence.md) ·
[Repair handoff](../plans/fast-track-handoffs/00004-workflow-core-v1/review-09.md)
