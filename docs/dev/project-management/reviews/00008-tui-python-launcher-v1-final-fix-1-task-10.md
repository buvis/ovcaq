# Phase-final regression cycle 1, task 10

Dispatch a16b721f; actual gpt-5.6-sol; committed e90ce6bea414a775b008d5098b746a2e44dee3ef. Source final-verification procedure: reopened owning task, isolated full-persona Ivan fix, preserved accepted contracts, focused failed checks. No completion review ran. Original task pipeline and review evidence remain in repair-task-10.md.

# Task 10 report

Fixed the scoped Ruff findings without changing viewer fallback or process-control behavior.

- Ordered `secrets` before `select` in `src/ovcaq/tui/app.py`.
- Ordered the integration test imports according to Ruff's configured import sections.
- Added narrow `BLE001` suppressions at the optional Textual import boundary, fleet UI fallback boundary, and project UI fallback boundary. Each suppression explains why arbitrary ordinary exceptions are intentionally converted to plain-view fallback. `BaseException` subclasses still propagate.
- Applied scoped Ruff formatting; it collapsed the `OptionList` yield.

## Verification

- `/usr/bin/python3 docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task10-format-escalated.log mise exec -- uv run ruff format src/ovcaq/tui/app.py tests/integration/test_viewer_fallback.py` — exit 0; 1 file reformatted, 1 unchanged.
- `/usr/bin/python3 docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task10-pytest.log mise exec -- uv run pytest -q --tb=line tests/integration/test_viewer_fallback.py` — exit 0; 14 passed, 2 pytest temporary-directory cleanup warnings.
- `/usr/bin/python3 docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task10-ruff-check-final.log mise exec -- uv run ruff check src/ovcaq/tui/app.py tests/integration/test_viewer_fallback.py` — exit 0; all checks passed.
- `/usr/bin/python3 docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task10-ruff-format-check-final.log mise exec -- uv run ruff format --check src/ovcaq/tui/app.py tests/integration/test_viewer_fallback.py` — exit 0; 2 files already formatted.

An earlier scoped Ruff check exited 1 because the test imports initially used the wrong configured section order; the final check above verifies the correction. The first sandboxed formatter attempt exited 2 because uv could not access its cache; the same bounded command succeeded with approved cache access as recorded above.

ASSUMPTIONS: none

FILES_TOUCHED:
src/ovcaq/tui/app.py
tests/integration/test_viewer_fallback.py
docs/dev/tmp/rfinal-fix-1-task-10-report.md
docs/dev/tmp/task10-read-app-2.log
docs/dev/tmp/task10-read-test-2.log
docs/dev/tmp/task10-format.log
docs/dev/tmp/task10-format-escalated.log
docs/dev/tmp/task10-ruff-check.log
docs/dev/tmp/task10-ruff-format-check.log
docs/dev/tmp/task10-pytest.log
docs/dev/tmp/task10-ruff-check-final.log
docs/dev/tmp/task10-ruff-format-check-final.log
