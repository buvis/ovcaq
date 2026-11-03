# Blake — blind PRD-only

## Verdict

changes_requested

## Must fix

1. **High — Drained state is not terminal.**
   - **Evidence:** `transitions.apply()` keys only on `work.phase`; therefore `(phase="done", next_phase="")` still accepts `more_prds` and resets to `build`. Reproduction produced `before=('done', '')`, `after=('build', 'build')`.
   - `park()` and `stall()` likewise have no phase/terminal guard. Parking a drained PRD moved it from `wip` to `hold` and reset state to `build`.
   - Existing transition tests only exercise `done/more_prds` with `next_phase="done"`; the rejection matrix omits the drained variant. Saga tests start from build.
   - **Violated requirement:** PRD test strategy requiring “post-drain state remaining terminal for the PRD”; P02-T03’s closed transition table/fail-closed behavior; P02-T07 recovery behavior.

2. **Medium — Frontmatter is bound only by basename, not lifecycle artifact identity.**
   - **Evidence:** `cli.py:617-623` reads any relative or absolute path, then passes only `prd_path.name` to `apply_to_store()`. An external file named `00004-workflow-core-v1.md` was accepted for an identically named active PRD and changed `review.cap` to `99`, despite the configured WIP PRD declaring `2`.
   - The installed test named `test_installed_frontmatter_binds_active_prd...` checks only a different basename, not an outside path or symlink with the correct basename.
   - **Violated requirement:** configured lifecycle-directory inputs and active committed-PRD binding under P02-T01/P02-T02 and the PRD’s “PRD Discovery and Inputs” capability.

## Can defer

None.

## PRD acceptance audit

- **P02-T01 — partial:** selection order, WIP priority, hold exclusion, invalid-directory behavior, and configurable path API are covered; lifecycle identity is bypassable by `frontmatter`.
- **P02-T02 — changes requested:** parsing, defaults, tier warnings, overwrite warnings, and CAS application pass; source-path binding fails.
- **P02-T03 — changes requested:** normal rows and listed rejection rows pass, but drained state can re-enter build.
- **P02-T04 — pass:** resume matrix, plan shape, cycle rejection, and size policy covered.
- **P02-T05 — pass:** per-PRD reset ownership, batch preservation, deterministic summary, and logical completion idempotency covered.
- **P02-T06 — pass:** operation-ID deduplication, conflicting replay rejection, atomic publication, and defer failpoints covered.
- **P02-T07 — changes requested:** durable-boundary reconciliation and directory-race defenses pass, but recovery commands can reopen terminal work.
- **P02-T08 — pass:** retained metrics, legitimate zero versus unknown totals, report section replacement, goldens, and idempotent publication covered.
- **P02-T09 — pass:** no production `dev/local/autopilot` reference remains; workflow runtime uses `dev/local/ovcaq`.
- **P02-T10 — pass:** operations and state-protocol inventories are checked against the live parser; installed workflow help is covered.
- **Exit: lifecycle fixture equivalence — pass:** the three retained lifecycle state fixtures map to expected v1 resume outcomes.
- **Exit: interruption recovery — pass for enumerated boundaries:** intent, rename/fsync, move, record publication, commit, replay, and lifecycle-directory replacement are exercised.
- **Exit: dependency direction/provider neutrality — pass:** AST import guards and forbidden-string/skill-command guards cover the workflow package.
- **Acceptance: every transition and rejection row — fail:** the state-dependent drained rejection is absent.
- **Acceptance: stable workflow service for PRD 00005 — fail:** terminality and PRD-source identity remain unsafe.

## Tests inspected or run

- Inspected the complete `b43bf2c9..c4b9ea3` implementation diff, workflow source, state-service fencing changes, retained fixtures/goldens, generated docs, workflow tests, and installed-wheel CLI tests.
- Ran `mise exec -- uv run pytest -q tests/workflow`: **202 passed**.
- Reproduced drained `done/"" → more_prds → build/build`.
- Reproduced `park()` moving a drained PRD to hold and resetting it to build.
- Reproduced external same-basename frontmatter changing committed policy.
- Confirmed clean worktree at exact HEAD `c4b9ea38d2e11eac4a1de1a71bd7d4134142e661`.
- Coordinator evidence accepted: targeted 73 passed; full pytest 1108 passed; sync, Ruff, mypy, build, diff-check, and plan hash passed.

## Residual doubts

- Corrupt retained `metrics.jsonl` is reported as `usage`; the permitted source contract does not define the expected symbolic class, so this was not elevated.
- Deferred-lock replacement and regular-file substitution races were not demonstrated under cooperating OVCAQ processes; existing tests cover lifecycle-directory identity changes and symlink escapes extensively.
