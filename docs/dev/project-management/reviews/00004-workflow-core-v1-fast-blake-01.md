# Blake — blind/PRD-only

## Verdict

changes_requested

## Must fix

- **Lifecycle recovery follows symlinked lifecycle directories — high.**
  `resolve_lifecycle_paths()` appends unresolved child paths
  (`src/ovcaq/workflow/paths.py:31`); the saga accepts an existing `hold`
  symlink (`src/ovcaq/workflow/records.py:468`), checks only lexical path
  equality (line 337), then renames through that symlink (line 348). A targeted
  probe with `prds/hold` symlinked externally completed with
  `source_exists=False` and `external_exists=True`. This can move the active
  PRD outside its lifecycle tree and commit the reset. Violates verified moves
  and restart-safe recovery without lost work.

## Can defer

- Selection accepts directories whose names resemble PRD Markdown files.
  `_directory_names()` returns every entry name
  (`src/ovcaq/workflow/selection.py:43-47`), while `selectable()` checks only
  filename syntax (lines 24-29). This is robustness hardening under Blake's
  blind threshold because normal fixtures use regular files.

## Tests inspected or run

- `mise exec -- uv run pytest tests/workflow tests/packaging/test_installed_cli.py -q`
  — 138 passed.
- Targeted temporary-directory symlink probe reproduced the external move.
- Inspected workflow production modules, CLI boundary, generated docs, and
  workflow/application/saga/report/packaging tests.
- `git diff --check` was clean; tracked worktree remained clean at verified
  HEAD `5a7ff023059bd396a177da7946a25ffe8d6d176d`.

## Residual doubts

- Verification covered macOS/Python 3.13, not the Python 3.12 lower bound or
  other platforms.
- Active-agent tier-map integration is exposed by the service but not exercised
  through the public CLI; this may depend on PRD 00005.
