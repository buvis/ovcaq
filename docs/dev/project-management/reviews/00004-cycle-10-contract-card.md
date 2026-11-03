# FT-04R10 contract card

Current step: fresh standalone completion review finished at 72562f6fd12fb039e91e4c7b1be29758d1901ec8.
Verdict: CHANGES_REQUESTED; R10-01 report JSON/artifact mismatch is the sole FIX.
Four inherited KNOWN observations remain, no unresolved VERIFY.

Active invariants: full implementation range, P02-T01–T10, 55 owned rows,
source phase exits; one state writer, typed durable recovery and original
artifact identity, repaired directory-inode ledger serialization and content
comparison, report root-to-leaf identity/fsync, terminal drain, provider neutrality.

Next gate: fresh FT-04F10 bounded repair and verification, then fresh FT-04R11
completion review with all isolated lenses and full R/B/D rubrics.
No PRD closeout, next PRD, unrelated state, source-plan edit or capsule refresh.

Full-base replay limitation and external nested-wrapper guards remain in force.
Standalone: no autopilot task store or contract state was created/mutated.
