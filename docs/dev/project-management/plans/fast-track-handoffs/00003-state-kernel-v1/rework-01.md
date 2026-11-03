# FT-03F rework handoff

- PRD: `00003-state-kernel-v1`
- Session: `FT-03F — Consolidated rework`
- Rework cycle: `01`
- Base SHA: `9872123ac9be6433f95ad4fb5606ac48cb402fce`
- Head SHA: `ff00f1f5b848043293ee8d92fbd11d0d38053738`
- Commit: `fix(state): harden JSON and path boundaries`
- Complete PRD range for the next review:
  `9cda04a6a0279a6306c24015ee2d3173fb916e68..ff00f1f5b848043293ee8d92fbd11d0d38053738`
- Consolidated bundle: `contract / correctness / security`

## Source IDs covered

- `P01-T02`: bounded total JSON validation and duplicate-key rejection.
- `P01-T03`: fail-closed state/backup/lock path handling and durable decode errors.
- `P01-T07`: generic JSON values are depth-validated before recursive copy work.
- `P01-T10`: stable CLI classifications for deep JSON, duplicate keys, and unsafe paths.
- `P01-T11`: native regression and installed-wheel coverage for the repaired boundary.

## Findings resolved

### FT03R-01 — Derived path containment and symlink escapes

- `runtime_directory()` resolves the project root, proves containment, and rejects
  symlinks in every derived `dev/local/ovcaq` component.
- Initialization creates the derived path one component at a time, revalidates it,
  opens the final runtime directory with no-follow flags, verifies its descriptor,
  and applies mode `0700` through that descriptor.
- State, backup, and lock artifacts reject symlinks before use. Reads and lock
  acquisition use no-follow flags and verify the opened descriptor still matches
  the path before reading or changing permissions.
- Atomic publication relies on the already-private temporary inode and no longer
  performs a path-following chmod after replacement.
- Regression cases cover symlinks at `dev`, `local`, and `ovcaq`, plus state,
  backup, and lock artifacts. External victim bytes and metadata remain unchanged.

### FT03R-02 — Bounded deep JSON and stable errors

- One shared decoder lexically bounds nesting before `json.loads`; the envelope
  accounts for owned schema wrappers while preserving the documented open-JSON
  depth limit.
- In-memory state receives an iterative depth preflight before encoding or copying.
- Generic set/append values validate before `deepcopy`; returned transaction
  replacements validate before the store creates its isolated committed copy.
- Deep inline/file payloads return `resource_limit`; deep durable state returns the
  same symbol; deep backup JSON returns `invalid_backup`. No traceback or durable
  mutation occurs.
- A positive store round trip at exactly `MAX_JSON_DEPTH` guards the valid boundary.

### FT03R-03 — Duplicate JSON keys

- The shared decoder uses an object-pairs hook that rejects a duplicate before a
  dictionary can collapse it.
- Coverage includes root owned keys, nested owned keys, open-map keys, inline JSON,
  JSON files, durable state, and backups.
- Inline/file duplicates return `usage`, durable-state duplicates return `state_io`,
  and backup duplicates return `invalid_backup`, all without durable changes.

## Files changed

- `src/ovcaq/paths.py`
- `src/ovcaq/cli.py`
- `src/ovcaq/state/schema.py`
- `src/ovcaq/state/store.py`
- `src/ovcaq/state/commands.py`
- `docs/state-protocol.md`
- `tests/state/test_cli.py`
- `tests/state/test_cli_limits.py`
- `tests/state/test_commands.py`
- `tests/state/test_store.py`

## Test-first evidence

- Focused RED command over the 14 new regression test functions: `23 failed, 3
  passed`. The failures reproduced all three root causes; the three passes were
  existing broad backup/resource wrappers that did not yet exercise the missing
  decoder checks.
- The same focused selection after implementation: `26 passed in 0.29s`.
- Broader state suite during implementation: `717 passed in 8.04s`.

## Targeted verification

```text
mise exec -- uv run pytest -q \
  tests/state/test_cli.py \
  tests/state/test_cli_limits.py \
  tests/state/test_commands.py \
  tests/state/test_store.py \
  tests/state/test_store_transactions.py \
  tests/state/test_store_concurrency.py \
  tests/state/test_durability.py \
  tests/state/test_installed_state.py
```

Result: `206 passed in 5.11s`.

## Canonical verification

- `mise exec -- uv sync --all-groups`: passed; 25 packages resolved, 24 checked.
- `mise exec -- uv run pytest`: passed; 789 tests in 9.12s.
- `mise exec -- uv run ruff check .`: passed.
- `mise exec -- uv run ruff format --check .`: passed; 75 files formatted.
- `mise exec -- uv run mypy src/ovcaq`: passed; 46 source files.
- `mise exec -- uv build`: passed; sdist and wheel built.
- `git diff --check`: passed before commit.
- Accepted implementation-plan SHA-256 remained
  `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
- Tracked worktree was clean immediately after commit.

## Decisions

- Duplicate-key handling is centralized with depth preflight so CLI and durable
  state cannot drift between decoders.
- The decoder envelope is `MAX_JSON_DEPTH + 8`: owned v1 wrappers fit inside it,
  while open JSON retains the documented `MAX_JSON_DEPTH` semantic limit.
- Symlink rejection is enforced at both project derivation and store-artifact use;
  an explicitly supplied arbitrary `StateStore` parent remains supported.
- Existing symbolic error values and exit codes were preserved; no public command
  or schema version changed.

## Known risks or failures

- No verification failures remain at this head.
- The code-changing rework is not converged until a fresh coordinator reruns all
  three isolated review lenses over the complete updated PRD range.
- The previously deferred vague derived-crosswalk wording remains deferred for
  clarification before PRD 00004 consumes it; this rework did not expand scope.
- PRD 00003 remains in `wip`. No review, lifecycle move, closeout, or autopilot
  state mutation occurred in FT-03F.

## Next session and exact first action

Next session: `FT-03R2 — Fresh convergence review`.

First action: from clean HEAD
`ff00f1f5b848043293ee8d92fbd11d0d38053738`, read the fast-track plan, PRD
00003, fast review 01, and this handoff; rerun the canonical verification gate,
then dispatch isolated Alice, Blake, and Bob concurrently over the complete
range `9cda04a6a0279a6306c24015ee2d3173fb916e68..ff00f1f5b848043293ee8d92fbd11d0d38053738`.

### Next-session prompt

```text
Execute the fast-track plan from:

    dev/local/plans/fast-track-implementation-plan.md

Start a fresh FT-03R2 convergence-review coordinator for PRD 00003. Read:

    dev/local/prds/wip/00003-state-kernel-v1.md
    dev/local/reviews/00003-state-kernel-v1-fast-review-01.md
    dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/rework-01.md

From clean HEAD ff00f1f5b848043293ee8d92fbd11d0d38053738, rerun the complete canonical PRD verification gate. Review the complete updated PRD range:

    9cda04a6a0279a6306c24015ee2d3173fb916e68..ff00f1f5b848043293ee8d92fbd11d0d38053738

Dispatch isolated Alice (consensus/architecture), Blake (blind PRD-only), and Bob (doubt plus de-slop, full R1-R5) concurrently with exactly the packets required by the fast-track plan. Each reviewer is read-only. Save their raw reports as cycle 02 artifacts, reconcile reproduced findings without code edits, write the consolidated cycle 02 review and:

    dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/review-02.md

Do not omit or thin any lens. Do not review only the rework commit. Do not edit code or close/move the PRD in the review session. Do not invoke run-autopilot, autoclaude, or mutate dev/local/autopilot/state.json. Print the next-session prompt and stop.
```
