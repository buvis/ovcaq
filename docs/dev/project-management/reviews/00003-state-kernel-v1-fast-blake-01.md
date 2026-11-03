# Blake — blind/PRD-only
Verdict: changes_requested
## Must fix
Deeply nested, size-compliant JSON escapes stable error handling; severity: medium; `src/ovcaq/cli.py:169-181,409-430` and `src/ovcaq/state/store.py:237-252` catch ordinary decode errors but not `RecursionError`. A 200,000-byte nested array passed through `main(["--json", "state", "set", ...])` raised uncaught `RecursionError` instead of returning symbolic JSON failure; `_decode_state()` reproduced the same result for persisted bytes. Violated requirements: deterministic behavior under invalid input, fail-closed corrupt/non-object reads, explicit depth limits, and stable stdout-safe machine errors.
## Can defer
Valid JSON empty-string keys cannot be addressed through JSON paths; evidence: `src/ovcaq/state/schema.py:456-467` permits them in metadata and nested extension JSON, while `src/ovcaq/state/paths.py:33-35` rejects `[""]`; rationale: low-impact path-grammar limitation, with whole-object recovery still available.
## Tests inspected or run
- Reviewed complete range `9cda04a6a0279a6306c24015ee2d3173fb916e68..9872123ac9be6433f95ad4fb5606ac48cb402fce`.
- Inspected schema, constraints, invariants, limits, crosswalk, store transaction/concurrency/durability, service/CLI, installed-wheel, path, and packaging tests.
- Specifically inspected real-process `test_sigkill_at_each_locked_mutation_boundary_preserves_recoverable_state`, concurrent CAS/no-lost-update tests, byte-identical failure-repair tests, and `test_installed_entry_points_execute_every_state_command_from_hostile_cwd`.
- Focused check via `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src mise exec -- python -B`: deeply nested `_decode_state()` input raised `RecursionError`.
- Focused actual CLI-path check via the same interpreter: deeply nested inline JSON passed to `main()` raised `RecursionError`.
- Relied on supplied gates: `uv sync --all-groups` resolved 25/checked 24; pytest 762 passed; Ruff check passed; Ruff format check passed for 75 files; mypy passed for 46 source files; sdist and wheel built; range `git diff --check` passed.
## Residual doubts
The PRD incorporates source-plan tasks by reference, but those referenced documents were excluded from the review packet; parity beyond the explicit PRD and touched machine crosswalk could not be independently checked.
