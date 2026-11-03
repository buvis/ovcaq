# Phase-final regression cycle 1, task 3

Dispatch 389641ab; actual gpt-6-astra; committed 3664599d46927422a6934bfad8361e6aaaf82db2. Source final-verification procedure: reopened owning task, isolated full-persona Ivan fix, preserved accepted contracts, focused failed checks. No completion review ran. Original task pipeline and review evidence remain in repair-task-3.md.

# Task 3 regression repair

Completed within the allowlist. Active model fixtures inject a fixed clock five minutes after the selected run start; legacy 150/60/None duration expectations now assert 300 seconds independently of usage. Terminal telemetry asserts the exact durable completed_at minus selected-run started_at, rather than metric.wall_seconds. The stale-control test boundedly waits for the rendered PRD before pressing pause and preserves its visible-error, exact target, and call-count assertions. Ruff formatted the elapsed-duration test and the changed model-test signature; model.py was already formatted and remained unchanged.

Verification (all processes awaited):

```text
python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/rfinal-task3-format.log uv run ruff format src/ovcaq/tui/model.py tests/tui/test_model_elapsed_duration.py tests/tui/model_support.py tests/tui/test_model.py tests/integration/test_observer_terminal_cleanup.py tests/tui/test_app.py
exit 0; 2 files reformatted, 4 unchanged

python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/rfinal-task3-tests.log uv run pytest tests/tui/test_model.py tests/tui/test_model_elapsed_duration.py tests/integration/test_observer_terminal_cleanup.py tests/tui/test_app.py::test_control_error_remains_visible_without_retargeting -q --tb=line
exit 0; 90 passed, 2 warnings in 10.40s

python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/rfinal-task3-lint.log uv run ruff check src/ovcaq/tui/model.py tests/tui/test_model_elapsed_duration.py tests/tui/model_support.py tests/tui/test_model.py tests/integration/test_observer_terminal_cleanup.py tests/tui/test_app.py
exit 0; all checks passed

python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/rfinal-task3-format-check.log uv run ruff format --check src/ovcaq/tui/model.py tests/tui/test_model_elapsed_duration.py tests/tui/model_support.py tests/tui/test_model.py tests/integration/test_observer_terminal_cleanup.py tests/tui/test_app.py
exit 0; 6 files already formatted
```

Warnings were pytest temporary-directory cleanup failures (directory not empty). No test failure. A bounded AST/file-size inspection exited 0: all six files remain under 800 physical lines and all functions under 50 nonblank, noncomment lines. No production behavior, state, git, or changelog changes; no full suite.

ASSUMPTIONS: none

FILES_TOUCHED:
tests/tui/model_support.py
tests/tui/test_model.py
tests/tui/test_model_elapsed_duration.py
tests/integration/test_observer_terminal_cleanup.py
tests/tui/test_app.py
docs/dev/tmp/rfinal-fix-1-task-3-report.md

Coordinator gates: style_gate: clean; split_hygiene: clean; check_reflow: exit 0. Exact renamed test nodes have no active documentation or proof-matrix consumers.
