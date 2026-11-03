# Phase-final regression cycle 1, task 2

Dispatch b6755da8; actual gpt-6-astra; committed dd0a7b36e9966422fa5ae3c5aa17f4c09dd5cd29. Source final-verification procedure: reopened owning task, isolated full-persona Ivan fix, preserved accepted contracts, focused failed checks. No completion review ran. Original task pipeline and review evidence remain in repair-task-2.md.

# Task 2 regression repair

Status: complete for task 2; two unchanged duration assertions remain for task 3.

The projection fixture keeps the real selected-run observation context active and mocks its low-level run observation input with the selected process identity. Identity replacement changes both the registry fixture and observation evidence, preserving the production guard before replacement state reads. The real-follower fixture retains the ownership input after undoing mocks and now writes normalized records to the session-specific path used by the observer. All original behavioral assertions remain.

The Projection support class moved to tests/tui/model_support.py to keep the test file below 800 lines. The exact production package inventory now includes ovcaq.runtime._run_observation. Runtime observation source was changed only by Ruff signature formatting. The raw-file fixture now explicitly sets the public raw_only field, preserving its original raw-only telemetry assertions.

Coordinator authorized a narrow production repair in ProjectObserver._observe after the migrated failure-injection case revealed uncaught context errors. It catches the existing OSError/ValueError observation taxonomy around context entry, reads, and exit, then uses the existing invalidation path. It does not suppress process-control exceptions or bypass ownership revalidation.

Verification commands (all invoked from the repository root):

- `python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task2-format-runtime.log uv run ruff format src/ovcaq/runtime/_run_observation.py` — exit 2; sandbox denied uv cache access. Retried with escalation below.
- `python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task2-format-runtime-retry.log uv run ruff format src/ovcaq/runtime/_run_observation.py` — exit 0, one file reformatted.
- `python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task2-lint-01.log uv run ruff check src/ovcaq/runtime/_run_observation.py tests/tui/test_model.py tests/tui/model_support.py tests/packaging/packaging_support.py` — exit 0.
- `python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task2-format-check-01.log uv run ruff format --check src/ovcaq/runtime/_run_observation.py tests/tui/test_model.py tests/tui/model_support.py tests/packaging/packaging_support.py` — exit 0, four files formatted.
- `python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task2-tests-01.log uv run pytest -q --tb=line tests/tui/test_model.py tests/packaging/test_distribution.py::test_wheel_contains_exact_declared_package_and_metadata tests/packaging/test_distribution.py::test_sdist_contains_only_allowlisted_committed_inputs` — exit 1, 54 passed, 7 failed, two temporary-directory cleanup warnings. Wheel inventory passed. Two duration failures belong to task 3; remaining failures prompted the fixture and production repairs above. Sdist expected committed inputs excludes the new helper until the coordinator stages it.
- `python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task2-lint-02.log uv run ruff check src/ovcaq/runtime/_run_observation.py src/ovcaq/tui/model.py tests/tui/test_model.py tests/tui/model_support.py tests/packaging/packaging_support.py` — exit 0.
- `python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task2-format-check-02.log uv run ruff format --check src/ovcaq/runtime/_run_observation.py src/ovcaq/tui/model.py tests/tui/test_model.py tests/tui/model_support.py tests/packaging/packaging_support.py` — exit 1; previously unformatted duration comprehension in model.py, outside initial scope.
- `python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task2-format-model.log uv run ruff format src/ovcaq/tui/model.py` — exit 0, one file reformatted; coordinator explicitly authorized the existing duration-comprehension whitespace wrap.
- `python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task2-lint-final.log uv run ruff check src/ovcaq/runtime/_run_observation.py src/ovcaq/tui/model.py tests/tui/test_model.py tests/tui/model_support.py tests/packaging/packaging_support.py` — exit 0.
- `python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task2-format-check-final.log uv run ruff format --check src/ovcaq/runtime/_run_observation.py src/ovcaq/tui/model.py tests/tui/test_model.py tests/tui/model_support.py tests/packaging/packaging_support.py` — exit 0, five files formatted.
- `python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task2-tests-final.log uv run pytest -q --tb=line tests/tui/test_model.py tests/packaging/test_distribution.py::test_sdist_contains_only_allowlisted_committed_inputs` — exit 1, 58 passed, 2 failed, two temporary-directory cleanup warnings. Sdist passed after the coordinator staged the support file; wheel passed in the initial run and was not needlessly repeated. Every process completed.

Remaining failures, left unchanged for task 3:

- `tests/tui/test_model.py::test_metrics_supply_duration_and_known_usage_without_inventing_provider` at line 440: expected metric sum 150.0; actual live elapsed duration 55743.763227.
- `tests/tui/test_model.py::test_absent_numeric_telemetry_remains_unknown` at line 464: expected None; actual live elapsed duration 55743.799013. This same test also retains its later expected 60.0 duration assertion for task 3 to reconcile.

Final AST/line-size inspection: every function in the five touched Python files is at most 50 physical lines, and every file is below 800 lines. No git/state commands, subagents, or broad test suite were run by this worker. No unrelated cleanup was performed. Inspection logs use distinct task2-read/size paths under docs/dev/tmp; verification logs are named explicitly above.

ASSUMPTIONS: none

FILES_TOUCHED:
src/ovcaq/runtime/_run_observation.py
src/ovcaq/tui/model.py
tests/tui/test_model.py
tests/tui/model_support.py
tests/packaging/packaging_support.py
docs/dev/tmp/rfinal-fix-1-task-2-report.md

Coordinator checks: check_style_limits.py clean; check_reflow.py exit 0; uv run mypy src/ovcaq exit 0 (60 source files), rfinal-task2-mypy.log. split_hygiene: failed: three necessary packaging_support exports reported UNUSED; the mandated deletion-only full-persona Ivan pass (4f356bde, native gpt-6-astra) verified consumers and made no unsafe deletion; repeat checker unchanged. This is a checker limitation, not dead code.

Result: BLOCKED — all three UNUSED findings are checker false positives; no safe deletion is permitted.

Verified definitions in tests/packaging/packaging_support.py and the explicitly permitted consumer lines in tests/packaging/test_distribution.py:

- PROJECT_ROOT: imported at line 24; read as subprocess cwd at 178 and source root at 473.
- DECLARED_PACKAGE_MEMBERS: imported at line 22; read for archive inventory at 246 and 385 and source enumeration at 472.
- DECLARED_RESOURCE_MEMBERS: imported at line 23; read for archive inventory at 246 and 386.

Deleting these public exports would break their consumers and package inventory checks. The checker only considered same-file reads. No source or test files were modified, no assertions or expectations were changed, and no tests were rerun because there was no edit. No git or state writes occurred.

Both bounded inspections completed with exit code 0 and a 60-second limit. Before the invocation syntax was supplied, a helper --help probe failed immediately with ValueError (the helper expects an integer timeout); it did not inspect additional source. Total input stayed below 100K.

FILES_TOUCHED:
docs/dev/tmp/rfinal-task2-hygiene-read-1.log
docs/dev/tmp/rfinal-task2-hygiene-read-2.log
docs/dev/tmp/rfinal-task2-hygiene-report.md

ASSUMPTIONS: none
