# FT-04F1 consolidated rework handoff

- PRD: `00004-workflow-core-v1`
- Session: `FT-04F1 — consolidated rework`
- Rework cycle: `01`
- Date: `2026-09-01`
- Base SHA: `5a7ff023059bd396a177da7946a25ffe8d6d176d`
- Head SHA: `56b664fc44c359b0b97282aa2e116dbf9ed44ff9`
- Commit: `fix(workflow): close fast-review contract gaps`
- Complete PRD range for the next review:
  `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..56b664fc44c359b0b97282aa2e116dbf9ed44ff9`
- Consolidated review:
  `dev/local/reviews/00004-workflow-core-v1-fast-review-01.md`
- Must-fix root causes resolved: `8`
- Rework bundles completed: `3`

## Root-cause disposition

### 1. Lifecycle artifacts fail closed

- Path selection now reads only regular, non-symlink PRD files from a real,
  non-symlink lifecycle directory. Directory-shaped and symlinked PRD entries
  cannot win selection.
- Stall/park validate WIP and hold as non-symlink directories before use and
  validate source/destination PRDs as regular, non-symlink files before
  stamping new intent or moving bytes.
- Real-filesystem regressions cover directory-shaped PRDs, symlinked PRD
  entries, and symlinked WIP/hold directories without state, ledger, or
  external-target mutation.

### 2. No-intent replay is bound to committed authority

- A destination in hold is considered replay evidence only after the requested
  PRD matches `work.prd`; inactive held PRDs now fail with
  `RecoveryConflictError` before filesystem or state mutation.
- The destination must also be the validated regular, non-symlink artifact at
  the requested PRD's exact hold path.

### 3. Rework clears complete cycle-local state

- `review + rework` clears doubts, rubric verdicts, rework task IDs, and lens
  status before starting the next cycle.
- Durable review-cycle records, decisions, review extensions, the review cap,
  and all batch-owned state remain intact. The regression validates the full
  resulting state against the v1 schema.

### 4. Completion requires terminal convergence

- `complete_prd()` requires both `work.phase == "done"` and the committed
  `review` completion marker before deriving or appending a summary.
- Direct, StateStore, and CLI regressions reject build/review completion while
  preserving state bytes and revision. The CLI success flow now commits
  `review + converged` before `complete-prd`.

### 5. Defer operation IDs are conflict-safe

- An existing operation ID is a replay only when its complete canonical payload,
  including the bound PRD, is identical.
- Reusing an ID for different content raises `DeferredRecordConflictError`
  without changing ledger bytes.
- Exact replay and conflict cases pass at record, StateStore service,
  in-process CLI, and built/installed-wheel CLI boundaries.

### 6. Resume output is provider-neutral

- Build resume now returns `continue build at first non-completed task N` and
  contains no external `/work` skill syntax.
- Characterized expectations were updated and the workflow boundary guard now
  rejects `/work`, `/run-autopilot`, and `/review-work-completion` identifiers.

### 7. Complete rejection matrix is durable

- `test_transitions.py` now commits all 14 rejected valid-phase/public-outcome
  pairs plus explicit unknown-phase and unknown-outcome rows.
- Every rejection is exercised through both `apply()` and `next_phase()`;
  the six accepted rows and their complete effects remain separately covered.

### 8. Defer publication has interruption evidence

- `DeferBoundary` exposes deterministic `before-publish` and `after-publish`
  failpoints around the atomic ledger replacement and directory fsync.
- Before-publication failure preserves the existing ledger byte-for-byte and a
  retry appends once. After-publication failure leaves a durable record and an
  exact retry is a byte-identical no-op with no duplicate item.

## Scope and files

Production changes are limited to:

- `src/ovcaq/workflow/records.py`
- `src/ovcaq/workflow/resume.py`
- `src/ovcaq/workflow/selection.py`
- `src/ovcaq/workflow/transitions.py`

Regression updates are limited to workflow and installed-wheel CLI tests. No
configuration loader, precedence rule, configured-root containment policy,
runtime, driver, event, TUI, provisioning, launcher content, command alias, PRD
lifecycle move, or autopilot state mutation entered this rework. PRD 00005
configuration precedence/containment remains out of scope.

## Test-first and targeted evidence

- The first focused run stopped during collection because the newly specified
  `DeferBoundary` API did not yet exist, confirming the interruption-evidence
  gap before implementation.
- Focused root-cause suite after implementation: `117 passed in 0.25s`.
- Corrected resume characterization/boundary suite: `19 passed in 0.02s`.
- Built-wheel installed defer replay/conflict regression: `1 passed in 0.83s`.
- Final canonical focused command:

  ```text
  mise exec -- uv run pytest tests/workflow tests/packaging/test_installed_cli.py
  ```

  Result: `167 passed in 1.10s`.

## Full verification gate

- `mise exec -- uv sync --all-groups`: passed; 25 packages resolved, 24 checked.
- `mise exec -- uv run pytest`: passed; 1,049 tests in 9.45s.
- `mise exec -- uv run ruff check .`: passed.
- `mise exec -- uv run ruff format --check .`: passed; 89 files formatted.
- `mise exec -- uv run mypy src/ovcaq`: passed; 47 source files.
- `mise exec -- uv build`: passed; sdist and wheel built.
- `git diff --check`: passed before staging and commit.
- The tracked worktree was clean immediately after commit.

The first full-gate attempt found one stale characterized `/work` expectation
after all other 1,048 tests passed. That expected provider-specific text was
updated as required by root cause 6; the complete gate above then passed.

## Known risks and session boundary

- No verification failure remains at this head.
- The source/destination checks are scoped to PRD 00004 lifecycle children.
  General configured-root precedence and containment remain assigned to PRD
  00005.
- PRD 00004 remains in `wip`. This session did not run review, closeout, a PRD
  move, or any autopilot command/state mutation.
- Code-changing rework is not converged until a fresh coordinator runs every
  mandatory isolated lens over the complete updated PRD range.

## Next session and exact first action

Next session: `FT-04R2 — fresh convergence review`.

First action: from clean HEAD
`56b664fc44c359b0b97282aa2e116dbf9ed44ff9`, read the PRD, consolidated cycle-01
review, and this handoff; rerun the canonical verification gate, then dispatch
isolated Alice, Blake, and Bob over the complete range
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..56b664fc44c359b0b97282aa2e116dbf9ed44ff9`.
Do not review only the rework commit.

### Next-session prompt

```text
Start a fresh FT-04R2 convergence-review coordinator for PRD 00004 from clean
HEAD 56b664fc44c359b0b97282aa2e116dbf9ed44ff9. Read:

    dev/local/prds/wip/00004-workflow-core-v1.md
    dev/local/reviews/00004-workflow-core-v1-fast-review-01.md
    dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/rework-01.md

Rerun the complete verification gate, then review the complete updated PRD
range:

    b43bf2c94d5eb0fddafca55542ef2570b45e8d52..56b664fc44c359b0b97282aa2e116dbf9ed44ff9

Dispatch isolated Alice (consensus/architecture), Blake (blind PRD-only), and
Bob (doubt plus de-slop, full R1-R5) with the mandatory fast-track packets.
Save the cycle-02 raw reports, reconcile reproduced findings without code edits,
write the consolidated cycle-02 review and review handoff, then stop. Do not
omit or thin any lens, review only the rework commit, edit code, move/close the
PRD, or mutate autopilot state in the review session.
```
