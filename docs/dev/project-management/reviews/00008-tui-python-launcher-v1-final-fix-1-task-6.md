# Phase-final regression cycle 1, task 6

Dispatch 10afeedb; actual gpt-5.6-sol; committed 6279a75c514867b21bd14f9559ac89a71cd2e780. Source final-verification procedure: reopened owning task, isolated full-persona Ivan fix, preserved accepted contracts, focused failed checks. No completion review ran. Original task pipeline and review evidence remain in repair-task-6.md.

# Regression fix report — task 6

Repaired the test seams for lazy viewer imports and the explicit JSON foreground contract.

- Patched `attach` at `ovcaq.tui.app.attach`, where the lazy import is used.
- Patched `verify_run` at `ovcaq.tui.app.verify_run`, where `RunControlService` uses it.
- Added the fake registry's guarded mutation context so interactive resume exercises the public control boundary while retaining identity revalidation.
- Made JSON foreground success cases pass `--no-tui` explicitly and retained targeted rejection coverage for JSON run without it.
- Kept the PTY JSON lifecycle assertion that the foreground supervisor PID equals the invoking process PID.

## Verification

Initial sandbox attempts were blocked before tool execution by inaccessible uv cache state:

`python docs/dev/tmp/run_bounded.py 300 /tmp/rfinal6-pytest.log uv run pytest -q --tb=line tests/runtime/test_attach.py tests/integration/test_control_commit_identity.py tests/integration/test_terminal_lifecycle.py`

- Exit: 2
- Result: uv cache initialization failed with `Operation not permitted`; no tests ran.

`python docs/dev/tmp/run_bounded.py 300 /tmp/rfinal6-ruff-check.log uv run ruff check tests/runtime/test_attach.py tests/integration/test_control_commit_identity.py tests/integration/test_terminal_lifecycle.py`

- Exit: 2
- Result: uv cache initialization failed with `Operation not permitted`; Ruff did not run.

`python docs/dev/tmp/run_bounded.py 300 /tmp/rfinal6-ruff-format.log uv run ruff format --check tests/runtime/test_attach.py tests/integration/test_control_commit_identity.py tests/integration/test_terminal_lifecycle.py`

- Exit: 2
- Result: uv cache initialization failed with `Operation not permitted`; Ruff did not run.

The exact bounded commands were rerun with uv cache and real-process access:

`python docs/dev/tmp/run_bounded.py 300 /tmp/rfinal6-pytest.log uv run pytest -q --tb=line tests/runtime/test_attach.py tests/integration/test_control_commit_identity.py tests/integration/test_terminal_lifecycle.py`

- Exit: 0
- Result: 79 passed, 2 pytest temporary-directory cleanup warnings, 30.18s.

`python docs/dev/tmp/run_bounded.py 300 /tmp/rfinal6-ruff-check.log uv run ruff check tests/runtime/test_attach.py tests/integration/test_control_commit_identity.py tests/integration/test_terminal_lifecycle.py`

- Exit: 0
- Result: All checks passed.

`python docs/dev/tmp/run_bounded.py 300 /tmp/rfinal6-ruff-format.log uv run ruff format --check tests/runtime/test_attach.py tests/integration/test_control_commit_identity.py tests/integration/test_terminal_lifecycle.py`

- Exit: 0
- Result: 3 files already formatted.

ASSUMPTIONS: The prompt's explicit seam-repair contract authorizes the narrow behavioral updates to the three allowlisted test files despite the generic implementor preamble saying tests are the spec.

FILES_TOUCHED:
tests/runtime/test_attach.py
tests/integration/test_control_commit_identity.py
tests/integration/test_terminal_lifecycle.py
docs/dev/tmp/rfinal-fix-1-task-6-report.md
