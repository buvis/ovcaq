# FT-04R6 review handoff

PRD: `dev/local/prds/wip/00004-workflow-core-v1.md`  
Session: `FT-04R6`  
Next session: `FT-04F6` (fresh rework; only when directed)  
Reviewed HEAD: `c4b9ea38d2e11eac4a1de1a71bd7d4134142e661`  
Complete range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c4b9ea38d2e11eac4a1de1a71bd7d4134142e661`  
Verdict: `changes_requested`

## Review outcome

All three mandatory isolated lenses ran over the complete PRD. Alice passed;
Blake and Bob requested changes. Coordinator reproduction and adjudication
leaves six must-fix root causes in two bundles:

1. **Contract/deterministic correctness:** keep drained state terminal; reject a
   conflicting in-flight park from `stall`; migrate TEST-062's tolerant
   legacy/mixed completed-summary behavior; total-order equal-key metrics rows.
2. **Publication identity/availability:** bind deferred publication to the
   configured directory identity through saga advancement/commit; reject an
   existing FIFO report target without blocking.

The external same-basename frontmatter path and Bob's R2/R3 de-slop items were
adjudicated as deferred, not acceptance blockers.

## Durable artifacts

- `dev/local/reviews/00004-workflow-core-v1-fast-alice-06.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-blake-06.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-bob-06.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-review-06.md`

## Verified closed behavior

- WIP/hold replacement at both named late boundaries retains recovery and tasks
  and reconciles exactly once after identity restoration.
- Retained normalized metrics drive active-batch nonzero, empty-zero, and
  incomplete/unknown summaries without provider parsing.
- Control characters are rejected across lifecycle/report identifiers;
  publication returns a domain error without leaking `StopIteration`.
- Recovery mutation fencing, state/lifecycle fsync ordering, provider-neutral
  boundaries, and parser-generated documentation remain closed.

## Fresh gate

- targeted sagas/reports/installed CLI: `73 passed in 3.02s`
- full suite: `1108 passed in 11.87s`
- Ruff check/format, mypy over 47 source files, build, and full-range
  `git diff --check`: passed
- accepted-plan digest and all 55 PRD-00004 migration IDs: verified

## Next session

Start `FT-04F6` fresh from the consolidated cycle-06 review, the active PRD,
and exact reviewed HEAD. Implement both bounded bundles together, add direct and
installed regressions for each reproduced defect, rerun targeted/full gates,
commit the repair, write `rework-06.md`, and stop. Do not use earlier raw lens
reports or handoffs as implementation authority.

FT-04R6 made no implementation, plan, PRD lifecycle, capsule, or autopilot-state
mutation.
