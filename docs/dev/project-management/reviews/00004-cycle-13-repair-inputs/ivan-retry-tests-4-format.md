Final verification on e7d3fc40a0c1d7321639927d6f8cdff6ca0ede25: 1359 tests passed in 25.19s; ruff lint, mypy and uv build passed. Only the formatting check failed.

Command: mise exec -- uv run ruff format --check .
Exit 1: src/ovcaq/workflow/_files.py:415:12, one file would be reformatted, 122 already formatted.

Ruff requests exactly this formatting-only replacement in the new diagnostic:
    if search_only and access == os.O_RDONLY and isinstance(error, PermissionError):
instead of the current five-line parenthesized condition.

Fix only this formatting regression in src/ovcaq/workflow/_files.py. Do not edit tests, other code, changelog, workflow state or commits. Do not rerun the full suite; only the failed format command should be rerun after the coordinator commits. Return the exact touched file. This is the work skill's final-verification failure path, not a new task or review cycle.
