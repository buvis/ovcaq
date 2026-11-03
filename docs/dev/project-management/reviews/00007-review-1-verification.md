# PRD 00007 review cycle 1 verification

Reviewed HEAD: `bbe7d521321428b670d15c4ede00e31792a61e1c`.
Work base: `4e3502723c474cee41f69e3a090bc952be5185ab`.

- State schema validation passed; eight tasks, all completed; recorded totals agree.
- Canonical resume target: `run review loop at cycle 1`; no pause or stall exists.
- Fresh `UV_CACHE_DIR=/private/tmp/ovcaq-review-cache uv run pytest --tb=short`: **3501 passed, 0 failed, 0 skipped**, two pytest temporary-directory cleanup warnings, 70.14s. Executed with approved OS process permissions.
- Initial sandbox run: 3219 passed, 272 failed, 10 errors. Its process-dependent paths failed because `ps` execution was denied. That run is not the product verification verdict.
- `uv run ruff check src tests`: passed.
- `uv run ruff format --check src tests`: 164 files formatted; passed.
- `uv run mypy src/ovcaq`: passed, 58 source files.
- `uv build`: wheel and sdist passed with approved dependency-download access. Initial sandbox build failed to resolve hatchling because DNS was restricted.
- Full-root `ruff check . --statistics`: 41 errors in pre-existing planning/review artifacts, matching the build's prior result. Full-root `ruff format --check .`: 42 artifact files would be reformatted; 518 unchanged. Product checks above pass. No historical artifacts were rewritten to quiet these checks.
- Fail-first replay against the base, with `PYTHONPATH=src` pinning imports to the temporary worktree: 119 touched cases ran, 110 failed against base, nine passed; seven files could not collect without the new implementation. The three passing-test findings are retained for gate adjudication. Initial replay used the current editable checkout inadvertently (410 pass); that diagnostic run is superseded, not used to claim coverage.
- Mechanical test-shape scan: one `or`-hedge in an unchanged test in a changed file; retained for gate adjudication.
- Temporary replay worktree was removed by the replay helper. `git worktree list` shows only the main checkout.
- Engram pack unavailable: project is not registered in the local gita inventory. The optional retrieval pack was omitted with its documented sentinel; repository requirements and code remain available to all appropriate lenses.

## Capability probe

The probe uses an isolated temporary project and the existing capability fixture. It starts a capability, fails it, retries successfully, and evaluates the resulting drained boundary. It does not mutate this repository's workflow state.

```json
{
  "failed_batch_status": "running",
  "failed_attention": {"site": "capability:archive", "detail": "capability 'archive' failed: probe failure", "created_at": "2026-09-14T10:00:00Z"},
  "successful_retry_batch_status": "completed",
  "successful_retry_attention": {"site": "capability:archive", "detail": "capability 'archive' failed: probe failure", "created_at": "2026-09-14T10:00:00Z"},
  "drained_boundary_decision_despite_attention": "complete",
  "drained_work_unchanged": true
}
```

The two oversized functions are computed by the skill's AST checker: `Supervisor._collect` at line 386 has 54 lines; `_conclude` at line 501 has 51.

## Retry and initialization probes

The same isolated probe evaluated twelve alternating AGENT/CONNECTIVITY failures with phase_repeat_limit=3. Decisions alternated retry/wait throughout; persisted phase_repeats remained 0. Thus changing failure class bypasses the shared unchanged-phase bound (F04).

Resetting only the temporary fixture's batch id/status to their unstarted defaults then calling run_once raised `ValueError: record identifier must be a single path component`, with zero child launches (F05). No production workflow state was changed by either probe. The probe source is retained in `00007-review-1-inputs/probe_review_00007.py.txt`.
