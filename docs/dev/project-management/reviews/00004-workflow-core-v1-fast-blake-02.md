# Blake — blind/PRD-only

## Verdict

`changes_requested`

## Must fix

1. **Completed PRDs remain selectable, so done-to-next-PRD loops back to the same PRD.**
   - Severity: High.
   - Evidence: `src/ovcaq/workflow/records.py:150-164` only appends a summary; `src/ovcaq/workflow/records.py:81-110` resets state without clearing/replacing `work.prd`; `src/ovcaq/cli.py:541-544` selects directly from unchanged lifecycle directories. `LifecyclePaths.done` is never used by workflow code.
   - Reproduction: In `/tmp`, I created `00004` and `00005` in `wip`, initialized valid converged state for `00004`, then invoked `complete-prd`, `phase-complete --outcome more_prds`, and `select`. All returned 0, but selection returned `{"prd":"00004-workflow-core-v1.md","source":"wip"}`; `00004` remained in `wip` and was absent from `done`.
   - Violated requirement: PRD lines 64-71 require full done-to-next-PRD effects and PRD completion; lines 156-162 explicitly require next-PRD behavior testing. The stated installed command family provides no other completion/move operation.

2. **Park/stall falsely reports replay success for an active held PRD without durable intent, record, reset, or commit.**
   - Severity: High.
   - Evidence: `src/ovcaq/workflow/records.py:544-556` treats “source absent, destination present” as a completed replay solely from filesystem placement and returns before the required saga steps.
   - Reproduction: In `/tmp`, I initialized valid running state with one unfinished task and active PRD `00004`, placed that PRD only in `hold`, and called `stall`. Result: `operation_id=None`, `replayed=True`, state bytes unchanged, one unfinished task remained, and no deferred ledger existed.
   - Violated requirement: PRD lines 77-78 and 137-142 require durable intent around move, record, reset, and commit, with safe reconciliation; line 175 requires recovery at all durable boundaries. This inconsistent input must fail closed or be reconciled, not silently claim success.

3. **Report/audit publication follows symlinked output directories and can overwrite files outside the intended tree.**
   - Severity: High, data-loss/security risk.
   - Evidence: `src/ovcaq/workflow/reports.py:190-210` accepts an existing parent without symlink validation, creates the temporary file through it, and replaces the destination; `src/ovcaq/workflow/reports.py:224-243` routes both public publishers through this helper.
   - Reproduction: In `/tmp`, I symlinked `dev/local/ovcaq/reports` to an external directory, placed a sentinel `batch-safe-report.md` there, initialized valid state, and invoked installed dispatch for `workflow render report`. Exit code was 0 and the external sentinel was overwritten.
   - Violated requirement: PRD lines 80-83 and 146-152 require installed deterministic report publication. A render operation must not escape its designated output root or destroy unrelated data.

## Can defer

None.

## Tests inspected or run

- Read the PRD first, then inspected the complete resulting implementation, tests, documentation, and all 30 changed files for `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..56b664fc44c359b0b97282aa2e116dbf9ed44ff9` (`4,239` insertions, `12` deletions).
- Confirmed exact `HEAD` was `56b664fc44c359b0b97282aa2e116dbf9ed44ff9`; `git status --short` was empty.
- `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..56b664fc44c359b0b97282aa2e116dbf9ed44ff9` passed with no output.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/workflow` — `163 passed in 0.30s`.
- Initial equivalent `mise exec -- uv run --no-sync pytest` attempt did not collect tests because the review sandbox denied UV cache initialization under `~/.cache/uv`; this was environmental, and the existing clean virtualenv run above passed.
- Ran three `/tmp`-only probes described under Must fix; all three reproduced the stated defects.
- Packet evidence at the exact clean HEAD: `mise exec -- uv sync --all-groups` passed (`25` resolved/`24` checked); full pytest passed (`1,049` in `10.95s`); Ruff check passed; Ruff format check passed (`89` files); mypy passed (`47` source files); `uv build` passed; focused workflow plus installed CLI passed (`167` in `1.22s`).

## Residual doubts

- Reproduced defects are classified under Must fix.
- Speculation only: saga path validation still uses check-then-path-operation sequences, so concurrent symlink swaps may remain possible. I did not reproduce that race and do not classify it as an additional finding.
- Exception failpoints exercise durable ordering, but I did not simulate kernel/power loss; no further defect is claimed.
