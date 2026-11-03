# Phase-final regression cycle 1, task 9

Dispatch 68e6d167; actual gpt-6-astra; committed c8cd2c525e54312895cec553fb9feb94c46182aa. Source final-verification procedure: reopened owning task, isolated full-persona Ivan fix, preserved accepted contracts, focused failed checks. No completion review ran. Original task pipeline and review evidence remain in repair-task-9.md.

# Task 9 repair

Changed the legacy anchor-alias test to require exactly `ThemeResult("nord", None)` and renamed it `test_trusted_xdg_config_alias_loads_intended_theme`. Coordinator confirmed its scoped exact-name search found no proof-matrix reference. Applied only the reported Ruff ternary wrap in `test_theme_persistence.py`. No production changes or unrelated assertion edits; app-owned descendant rejection assertions remain intact.

Verification (all commands awaited):

```text
python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task9-pytest.log uv run pytest tests/tui/test_app.py::test_trusted_xdg_config_alias_loads_intended_theme tests/tui/test_theme_persistence.py -q --tb=line
exit 0: 41 passed, 2 pytest temporary-directory cleanup warnings, 1.38s

python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task9-final-ruff-check.log uv run ruff check tests/tui/test_app.py tests/tui/test_theme_persistence.py
exit 0: All checks passed

python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task9-final-ruff-format-check.log uv run ruff format --check tests/tui/test_app.py tests/tui/test_theme_persistence.py
exit 0: 2 files already formatted
```

Earlier scoped checks:

```text
python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task9-format-diff.log uv run ruff format --diff tests/tui/test_app.py tests/tui/test_theme_persistence.py
exit 2: sandbox denied uv cache access

python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task9-format-diff-escalated.log uv run ruff format --diff tests/tui/test_app.py tests/tui/test_theme_persistence.py
exit 1: exactly one ternary-wrap formatting diff

python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task9-ruff-check.log uv run ruff check tests/tui/test_app.py tests/tui/test_theme_persistence.py
exit 0: All checks passed

python docs/dev/tmp/run_bounded.py 300 docs/dev/tmp/task9-ruff-format-check.log uv run ruff format --check tests/tui/test_app.py tests/tui/test_theme_persistence.py
exit 0: 2 files already formatted
```

ASSUMPTIONS: none

FILES_TOUCHED:
tests/tui/test_app.py
tests/tui/test_theme_persistence.py
docs/dev/tmp/rfinal-fix-1-task-9-report.md
docs/dev/tmp/task9-inspect-1.log
docs/dev/tmp/task9-inspect-2.log
docs/dev/tmp/task9-skill-python.log
docs/dev/tmp/task9-skill-testing.log
docs/dev/tmp/task9-format-diff.log
docs/dev/tmp/task9-format-diff-escalated.log
docs/dev/tmp/task9-ruff-check.log
docs/dev/tmp/task9-ruff-format-check.log
docs/dev/tmp/task9-pytest.log
docs/dev/tmp/task9-final-ruff-check.log
docs/dev/tmp/task9-final-ruff-format-check.log
