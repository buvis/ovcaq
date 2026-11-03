# FT-04R11 contract card

Current step: fresh full completion review finished; CHANGES_REQUESTED.
HEAD: 22d9193a0d00486b09ebea169e7a38a9f858799d.
Scope: P02-T01–T10, all 55 rows, all phase exits.
Terminal accounting: 7 = 3 FIX + 0 VERIFY + 4 KNOWN.

Next gate: a separate FT-04F11 work session repairs R11-01/R11-03/R11-02,
captures fail-first regressions and full gates, then hands off to fresh FT-04R12.
Never implement and run completion review in the same session.

Active invariants: sole state writer, provider-neutral workflow, preserved R8/R9
repairs and R10 complete report result, original saga identity/null-artifact
refusal, coordinator-only ledger serialization root, no loss of successful
records/sections, full source contract, raw evidence retention, settled K1–K4.
Historical PRD-00003 autopilot state remains unrelated and untouched.

No plan/capsule edits, importer, aliases, launcher markers, model policy,
abort/rollback API, duplicate frontmatter policy, Linux signoff, PRD closeout,
or next PRD.
