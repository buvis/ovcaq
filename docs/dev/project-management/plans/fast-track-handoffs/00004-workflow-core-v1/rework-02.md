---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
session: FT-04F2
date: 2026-09-02
starting_head: 56b664fc44c359b0b97282aa2e116dbf9ed44ff9
rework_commit: f2453760591875f1faf241ec9c0291303232efd9
new_head: f2453760591875f1faf241ec9c0291303232efd9
complete_prd_review_range: b43bf2c94d5eb0fddafca55542ef2570b45e8d52..f2453760591875f1faf241ec9c0291303232efd9
next_session: FT-04R3
---

# Rework 02 handoff: workflow core v1

Committed `fix: harden workflow recovery and reporting` at
`f2453760591875f1faf241ec9c0291303232efd9`.

## Consolidated root-cause closure

1. No-intent held-file replay now requires a matching durable ledger operation
   plus committed per-PRD reset evidence; unproven active-PRD placement fails
   closed at service and installed-command boundaries.
2. Frontmatter, phase completion, PRD completion, and public defer mutations now
   reject while recovery intent is active. The matching saga reconciliation
   path remains authoritative and completes normally.
3. Saga validation, rename, verification, and fsync use verified directory
   descriptors. The exact after-intent hold-directory symlink swap leaves the
   external target untouched and recovery intent/state work intact.
4. Frontmatter application is bound to committed `work.prd`; legacy derived
   controls are no longer duplicated in `work.extensions`; rework-cap ownership
   is durable, so an explicit `3 -> 2` replacement warns.
5. Reporting now preserves replaceable per-PRD sections, refreshes one batch
   summary with retained cycle/decision totals, archives canonical drained state,
   and has migrated v1 audit/report/metrics goldens.
6. Report and audit publication validate filename components and use
   descriptor-relative, no-follow atomic publication. Traversal and symlinked
   parents fail without changing external sentinels; valid rerenders are byte
   idempotent.
7. The state-protocol inventory is emitted by the live parser generator, while
   `docs/operations.md` remains the parser-generated workflow reference.
8. Hold exclusion is tested with real lifecycle paths, and every accepted
   transition row compares `next_phase()` with the applied full effect.

## Verification

Final complete gate at the committed tree:

- `mise exec -- uv sync --all-groups` — passed; 25 packages resolved, 24 checked.
- `mise exec -- uv run pytest` — passed; 1,068 tests.
- `mise exec -- uv run ruff check .` — passed.
- `mise exec -- uv run ruff format --check .` — passed; 92 files formatted.
- `mise exec -- uv run mypy src/ovcaq` — passed; 47 source files.
- `mise exec -- uv build` — passed; sdist and wheel built.

Focused workflow plus installed-wheel regressions also passed: 186 tests.

## Required next action

Start a fresh FT-04R3 coordinator review. Run isolated Alice consensus, Blake
blind/PRD-only, and Bob doubt/de-slop R1-R5 lenses over the complete updated PRD
range:

`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..f2453760591875f1faf241ec9c0291303232efd9`

Do not review only the rework commit. This session did not close or move the PRD,
mutate autopilot state, edit the accepted implementation plan, or begin another
PRD.
