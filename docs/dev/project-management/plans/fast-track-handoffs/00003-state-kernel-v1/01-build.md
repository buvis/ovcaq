# FT-03A build handoff

- PRD: `00003-state-kernel-v1`
- Session: `FT-03A — Recorded repair bundle`
- Base SHA: `9bd52bb9d140237c2d9962d878afb7ef4a9f0c01`
- Head SHA: `9872123ac9be6433f95ad4fb5606ac48cb402fce`
- Commit: `fix(state): close state kernel review gaps`
- Complete PRD review range: `9cda04a6a0279a6306c24015ee2d3173fb916e68..9872123ac9be6433f95ad4fb5606ac48cb402fce`

## Source IDs covered

- `P01-T01`: corrected the legacy field crosswalk for `batch.mode`.
- `P01-T02`: completed UTF-8 and absolute-repository-root schema boundaries.
- `P01-T08`: reconciled absent versus caller-supplied task IDs.
- `P01-T10`: rejected invalid `ovcaq.toml` path collisions before state publication and proved typed resource-limit CLI classification.
- `P01-T11`: added regression coverage and removed the recorded split-test dead assignments.

This closes review-cycle-2 repair tasks 21–25: schema boundaries, supplied task
IDs, config collisions, the `batch.mode` crosswalk, and dead assignments.

## Files changed

Committed:

- `docs/state-protocol.md`
- `src/ovcaq/config.py`
- `src/ovcaq/state/commands.py`
- `src/ovcaq/state/schema.py`
- `tests/state/test_cli.py`
- `tests/state/test_cli_limits.py`
- `tests/state/test_crosswalk.py`
- `tests/state/test_schema.py`
- `tests/state/test_schema_constraints.py`
- `tests/state/test_schema_limits.py`
- `tests/state/test_service_commands.py`
- `tests/state/test_store_concurrency.py`
- `tests/state/test_store_transactions.py`

Local PRD authority reconciled after the commit:

- `dev/local/designs/00003-state-kernel-v1-design.md`
- `dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/01-build.md`

## Behavior completed

- Lone-surrogate values and keys now produce path-aware `SchemaError` values;
  no `UnicodeEncodeError` escapes validation or error rendering.
- `work.repo_root` must be absolute during full-document validation.
- Minimum-bound diagnostics derive from their threshold instead of indexing a
  two-element detail tuple.
- `TaskCreate.id` is optional: a supplied positive unique ID is preserved;
  only an absent ID allocates `max(existing IDs) + 1`; duplicate IDs fail the
  transaction without durable changes.
- Existing regular `ovcaq.toml` files remain untouched. Directory and broken
  symlink collisions fail as `state_io` before `state.json` publication.
- Legacy `batch.mode=autopilot` is retired; it is not renamed to the unrelated
  v1 lifecycle field `batch.status`.
- A below-16-MiB state exceeding the typed contract-card limit is proven to
  return `resource_limit` with exit 11.
- Removed the six recorded unused split-test declarations/captures.

## Verification

- RED regression set: `8 failed, 286 passed` before implementation.
- Focused repair set: `294 passed`.
- `mise exec -- uv run pytest tests/state tests/packaging tests/test_packaging.py`: `704 passed`.
- `mise exec -- uv sync --all-groups`: resolved 25 packages; checked 24 packages.
- `mise exec -- uv run pytest`: `762 passed`.
- `mise exec -- uv run ruff check .`: passed.
- `mise exec -- uv run ruff format --check .`: 75 files already formatted.
- `mise exec -- uv run mypy src/ovcaq`: no issues in 46 source files.
- `mise exec -- uv build`: built the sdist and wheel successfully.
- `git diff --cached --check`: passed before commit.

## Decisions

- Treat a supplied task ID as caller intent and let the closed state schema
  enforce integer, positivity, and uniqueness; allocation occurs only when the
  key is absent.
- Preserve an existing config target only when it resolves to a regular file;
  the two recorded collision shapes remain visible and cause initialization to
  fail closed.
- Retire `batch.mode` because legacy mode was the fixed value `autopilot`, while
  `batch.status` represents lifecycle state.
- Keep typed resource-limit classification unchanged and add the missing
  end-to-end CLI proof using `work.contract_card`.

## Known risks or failures

- No implementation or verification failure remains.
- Formal fresh-context FT-03R review is still required across the complete PRD
  range; it was intentionally not run in this session.
- `dev/local/autopilot/state.json` was not read for progress, mutated, or resumed.

## Next session and exact first action

Next session: `FT-03R — Fresh review`.

First action: from clean HEAD `9872123ac9be6433f95ad4fb5606ac48cb402fce`,
read the fast-track plan, PRD 00003, its accepted design, review-cycle-2 report,
and this handoff; then rerun the canonical PRD verification gate before
dispatching Alice, Blake, and Bob against
`9cda04a6a0279a6306c24015ee2d3173fb916e68..9872123ac9be6433f95ad4fb5606ac48cb402fce`.
