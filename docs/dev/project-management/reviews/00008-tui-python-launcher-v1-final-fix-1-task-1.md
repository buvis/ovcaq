# Phase-final regression cycle 1, task 1

Dispatch 1bda9911; actual gpt-5.6-sol; committed c0cde680f9a29f913310ea829be13ad59c90a7ae. Source final-verification procedure: reopened owning task, isolated full-persona Ivan fix, preserved accepted contracts, focused failed checks. No completion review ran. Original task pipeline and review evidence remain in repair-task-1.md.

Implemented the standalone `run_once()` metadata regression fix in `Supervisor._open_session`.

When no full-loop owner has been published, session creation now skips the run-metadata refresh. Full `run()` executions still update the existing canonical metadata with each session ID, preserving the original run ID and owner start time.

Verification:

- `python docs/dev/tmp/run_bounded.py 300 /tmp/rfinal-fix-1-task-1-pytest.log uv run pytest -q --tb=line tests/runtime/test_supervisor.py tests/runtime/test_supervisor_durable_stop.py tests/integration/test_native_telemetry_identity.py` — exit 2 before test collection because the sandbox denied access to `/Users/bob/.cache/uv`; 0 tests run.
- `python docs/dev/tmp/run_bounded.py 300 /tmp/rfinal-fix-1-task-1-pytest-escalated.log uv run pytest -q --tb=line tests/runtime/test_supervisor.py tests/runtime/test_supervisor_durable_stop.py tests/integration/test_native_telemetry_identity.py` — exit 0; 55 passed, 2 cleanup warnings.
- `python docs/dev/tmp/run_bounded.py 300 /tmp/rfinal-fix-1-task-1-ruff-check.log uv run ruff check src/ovcaq/runtime/supervisor.py` — exit 0; all checks passed.
- `python docs/dev/tmp/run_bounded.py 300 /tmp/rfinal-fix-1-task-1-ruff-format.log uv run ruff format --check src/ovcaq/runtime/supervisor.py` — exit 0; 1 file already formatted.

ASSUMPTIONS: none

FILES_TOUCHED:
src/ovcaq/runtime/supervisor.py
docs/dev/tmp/rfinal-fix-1-task-1-report.md
