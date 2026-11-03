---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
session: FT-04F4
date: 2026-09-03
starting_head: e8fe191089d91140343e6246dffe66caf9caa6a9
rework_commit: c512a4ad7d67af75b413ee8c9612b088d21fb4f4
new_head: c512a4ad7d67af75b413ee8c9612b088d21fb4f4
complete_prd_review_range: b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c512a4ad7d67af75b413ee8c9612b088d21fb4f4
next_session: FT-04R5
---

# Rework 04 handoff: workflow core v1

Committed `fix(workflow): close recovery race windows` at
`c512a4ad7d67af75b413ee8c9612b088d21fb4f4` from clean starting HEAD
`e8fe191089d91140343e6246dffe66caf9caa6a9`.

## Bounded root-cause closure

1. Lifecycle move verification now binds each open WIP and hold descriptor to
   the configured pathname's device/inode identity. It verifies both identities
   before artifact inspection, after the rename boundary, and around the
   lifecycle-directory fsyncs. Renaming either directory away and replacing its
   configured pathname after durable intent therefore fails closed at `intent`:
   recovery and original task state remain durable, no ledger is written, and
   the replacement target is untouched. Restoring the configured identity lets
   normal replay durably move, record, reset, and clear recovery.
2. Every public `StateService` mutation checks for active recovery inside its
   locked state transaction. This covers all task mutations, contract updates,
   allowed and unsafe generic set/append/delete operations, and restore. Restore
   receives a state-layer precondition evaluated under the store lock. The
   state layer imports no workflow code; workflow replay continues to use the
   lower-level `StateStore`. Generic CLI conflicts retain usage-error semantics
   rather than being mislabeled as invalid paths.

Both FT-04F3 closures remain intact: lifecycle and record directory durability
is re-established before state advances, and explicit durable recovery kind
continues to control replay and park-breaker behavior.

## Exact regression coverage

- Deterministic real-filesystem tests rename away and symlink-replace WIP and
  hold independently at `AFTER_INTENT_BEFORE_MOVE`. Each proves retained
  recovery/task state, no deferred record, unchanged external sentinel/target,
  correct surviving PRD location, and successful reconciliation after the
  configured identity is restored.
- Service saga tests interrupt after intent, reject task creation, contract
  replacement, and an allowed generic extension mutation without changing
  state bytes or revision, then reconcile successfully without data loss.
- State-service tests exercise all thirteen public mutation paths during active
  recovery, including generic set/append/delete and restore, and prove exact
  state/backup byte preservation.
- The installed-wheel test creates durable interrupted intent through the
  installed package, rejects task, contract, and allowed generic CLI mutations
  with unchanged state bytes, then safely reconciles through the installed
  `workflow stall` command.

## Fresh verification

- `mise exec -- uv sync --all-groups` — passed; 25 packages resolved, 24
  checked.
- `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/packaging/test_installed_cli.py -q`
  — passed; 50 tests in 1.91s.
- `mise exec -- uv run pytest` — passed; 1,095 tests in 10.73s.
- `mise exec -- uv run ruff check .` — passed.
- `mise exec -- uv run ruff format --check .` — passed; 92 files formatted.
- `mise exec -- uv run mypy src/ovcaq` — passed; 47 source files.
- `mise exec -- uv build` — passed; sdist and wheel built.
- `git diff --check` — passed.

## Required next action

Start a fresh isolated `FT-04R5` three-lens review. Run the complete mandatory
Alice consensus/architecture, Blake blind PRD-only, and Bob doubt plus de-slop
R1-R5 lenses over the complete updated PRD range:

`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c512a4ad7d67af75b413ee8c9612b088d21fb4f4`

Review the complete range, not only the FT-04F4 repair commit. This session did
not run review, mutate autopilot state, edit either implementation plan, move or
close the PRD, refresh the capsule, or begin another PRD.
