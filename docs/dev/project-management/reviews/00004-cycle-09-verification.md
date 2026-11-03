# FT-04R9 fresh verification

## sync

Command: `mise exec -- uv sync --all-groups`

Exit: 0

```text
Resolved 25 packages in 3ms
Checked 24 packages in 2ms
```

## workflow_packaging

Command: `mise exec -- uv run pytest tests/workflow/ tests/packaging/ -q`

Exit: 0

```text
........................................................................ [ 16%]
........................................................................ [ 33%]
........................................................................ [ 50%]
........................................................................ [ 67%]
........................................................................ [ 84%]
...................................................................      [100%]
427 passed in 10.37s
```

## pytest

Command: `mise exec -- uv run pytest`

Exit: 0

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/bob/git/src/github.com/buvis/ovcaq
configfile: pyproject.toml
collected 1315 items

tests/characterization/test_migration_contract.py ......                 [  0%]
tests/packaging/test_distribution.py ........                            [  1%]
tests/packaging/test_input_integrity.py ........                         [  1%]
tests/packaging/test_installed_cli.py ...........                        [  2%]
tests/packaging/test_installed_reports.py .............                  [  3%]
tests/packaging/test_installed_sagas.py .................                [  4%]
tests/packaging/test_workflow_inputs.py ................                 [  6%]
tests/state/test_cli.py ................................................ [  9%]
......                                                                   [ 10%]
tests/state/test_cli_limits.py ...............................           [ 12%]
tests/state/test_commands.py ..........................                  [ 14%]
tests/state/test_crosswalk.py .......                                    [ 14%]
tests/state/test_durability.py ..............                            [ 16%]
tests/state/test_installed_state.py ...                                  [ 16%]
tests/state/test_paths.py .............................................. [ 19%]
........................................................................ [ 25%]
..........................                                               [ 27%]
tests/state/test_recovery_mutations.py .............                     [ 28%]
tests/state/test_schema.py ......                                        [ 28%]
tests/state/test_schema_constraints.py ................................. [ 31%]
........................................................................ [ 36%]
........................................................................ [ 42%]
...........................                                              [ 44%]
tests/state/test_schema_invariants.py .................................. [ 46%]
.......................                                                  [ 48%]
tests/state/test_schema_limits.py ...................................... [ 51%]
.....................................                                    [ 54%]
tests/state/test_service_commands.py ................................... [ 56%]
........................                                                 [ 58%]
tests/state/test_service_contracts.py ..                                 [ 58%]
tests/state/test_store.py .............................................  [ 62%]
tests/state/test_store_concurrency.py .......................            [ 64%]
tests/state/test_store_transactions.py ................................. [ 66%]
.............................                                            [ 68%]
tests/test_package_baseline.py ......................................... [ 71%]
............                                                             [ 72%]
tests/test_packaging.py ....                                             [ 73%]
tests/workflow/test_applications.py ..........                           [ 73%]
tests/workflow/test_blank_decisions.py ................                  [ 75%]
tests/workflow/test_boundaries.py ...                                    [ 75%]
tests/workflow/test_characterized_fixtures.py ...                        [ 75%]
tests/workflow/test_configuration.py ........                            [ 76%]
tests/workflow/test_deferred_ledger.py ...................               [ 77%]
tests/workflow/test_frontmatter.py ...........................           [ 79%]
tests/workflow/test_ledger_integrity.py ............                     [ 80%]
tests/workflow/test_policy.py ............                               [ 81%]
tests/workflow/test_records.py ............                              [ 82%]
tests/workflow/test_report_recovery.py ..........                        [ 83%]
tests/workflow/test_reports.py ..................................        [ 85%]
tests/workflow/test_resume.py .............                              [ 86%]
tests/workflow/test_saga_artifacts.py ..........                         [ 87%]
tests/workflow/test_saga_identity.py ...............                     [ 88%]
tests/workflow/test_saga_publication.py ................................ [ 91%]
................                                                         [ 92%]
tests/workflow/test_sagas.py ................................            [ 94%]
tests/workflow/test_selection.py .........................               [ 96%]
tests/workflow/test_transitions.py ..................................    [ 99%]
tests/workflow/test_workflow_cli.py ...........                          [100%]

============================ 1315 passed in 19.06s =============================
```

## ruff

Command: `mise exec -- uv run ruff check .`

Exit: 0

```text
All checks passed!
```

## format

Command: `mise exec -- uv run ruff format --check .`

Exit: 0

```text
114 files already formatted
```

## mypy

Command: `mise exec -- uv run mypy src/ovcaq`

Exit: 0

```text
Success: no issues found in 51 source files
```

## build

Command: `mise exec -- uv build`

Exit: 0

```text
Building source distribution...
Building wheel from source distribution...
Successfully built dist/ovcaq-0.1.0.dev0.tar.gz
Successfully built dist/ovcaq-0.1.0.dev0-py3-none-any.whl
```

## whitespace

Command: `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..HEAD`

Exit: 0

```text
```

