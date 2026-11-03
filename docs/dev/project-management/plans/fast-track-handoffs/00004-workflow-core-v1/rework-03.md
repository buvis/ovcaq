---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
session: FT-04F3
date: 2026-09-03
starting_head: f2453760591875f1faf241ec9c0291303232efd9
rework_commit: e8fe191089d91140343e6246dffe66caf9caa6a9
new_head: e8fe191089d91140343e6246dffe66caf9caa6a9
complete_prd_review_range: b43bf2c94d5eb0fddafca55542ef2570b45e8d52..e8fe191089d91140343e6246dffe66caf9caa6a9
next_session: FT-04R4
---

# Rework 03 handoff: workflow core v1

Committed `fix(workflow): make recovery replay durable` at
`e8fe191089d91140343e6246dffe66caf9caa6a9` from clean starting HEAD
`f2453760591875f1faf241ec9c0291303232efd9`.

## Consolidated root-cause closure

1. Recovery replay now re-establishes filesystem durability before advancing
   state. Ensuring `hold` and `deferred` fsyncs the directory that owns the
   entry; move verification fsyncs both lifecycle directory descriptors even
   when replay finds the PRD already moved; and exact deferred-record replay
   fsyncs the record directory before returning. Controlled real-filesystem
   interruptions after rename and replace prove replay performs the required
   sync while recovery remains at `intent` or `moved`, respectively.
2. Recovery kind is now explicit durable authority. Stall/park ledger entries
   persist `kind`; exact replay matches that field rather than inferring from
   `site`; and the park breaker uses intent kind alone. Service and
   installed-wheel regressions prove exact stall and park replay, correct
   breaker behavior, and fail-closed rejection of the `wrapper_died`
   cross-kind collision without byte changes.

No deferred fast-review-03 claim was implemented. Configuration, tier maps,
supervisor/cap policy, successful PRD movement, and next-PRD behavior were not
changed.

## Verification

Focused real-filesystem and installed-wheel regressions:

- `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/packaging/test_installed_cli.py -q`
  — passed; 44 tests in 2.36s.

Complete gate:

- `mise exec -- uv sync --all-groups` — passed; 25 packages resolved, 24 checked.
- `mise exec -- uv run pytest` — passed; 1,076 tests in 13.63s.
- `mise exec -- uv run ruff check .` — passed.
- `mise exec -- uv run ruff format --check .` — passed; 92 files formatted.
- `mise exec -- uv run mypy src/ovcaq` — passed; 47 source files.
- `mise exec -- uv build` — passed; built
  `dist/ovcaq-0.1.0.dev0.tar.gz` and
  `dist/ovcaq-0.1.0.dev0-py3-none-any.whl`.
- `git diff --check` — passed before commit.

## Required next action

The next session must be a fresh isolated FT-04R4 review over the complete PRD
range:

`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..e8fe191089d91140343e6246dffe66caf9caa6a9`

Do not review only the rework commit. This session did not run review, mutate
autopilot state, edit either implementation plan, move or close the PRD,
refresh the capsule, or begin another PRD.
