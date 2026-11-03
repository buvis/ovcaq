# FT-04A build handoff

- PRD: `00004-workflow-core-v1`
- Session: `FT-04A — Pure rules`
- Date: `2026-08-30`
- Base SHA: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`
- Head SHA: `06fdf88149a7cafd6d3f4ec9aedf1510a59a652a`
- Commit: `feat(workflow): implement deterministic pure rules`
- Accepted implementation-plan SHA-256:
  `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`
- Frozen autopilot-state SHA-256 before/after:
  `ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f`

## Preconditions and lifecycle

- Started from exact clean HEAD `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`.
- Verified PRDs 00002 and 00003 under `dev/local/prds/done/`; PRD 00004's
  dependencies were complete.
- Verified the accepted plan digest before implementation and after the commit.
- Moved PRD 00004 from `backlog/` to `wip/`, changed its status to `wip`, and
  refreshed the project capsule Active Work section.
- Did not invoke `run-autopilot`, `autoclaude`, or any saved phase machine.
- Did not mutate `dev/local/autopilot/state.json`; its digest remained identical.

## Source IDs covered

- `P02-T01`: complete for selection and configured lifecycle-path resolution.
- `P02-T02`: complete pure parsing/default/warning/tier-floor rules; the public
  workflow command application remains FT-04B.
- `P02-T03`: pure closed transition table and full effect sets complete;
  StateStore-backed `phase-complete` command integration remains FT-04B.
- `P02-T04`: complete for v1 resume mapping, strict plan shape/dependency-cycle
  validation, and the characterized fifteen-task ceiling.
- `P02-T05`: complete for pure per-PRD reset, summary derivation, and idempotent
  completion; public command/attempt-ledger integration remains FT-04B.
- `P02-T09`: lifecycle-path portion complete with no legacy runtime-root
  literal; saga/report/CLI path consumers remain FT-04B.

FT-04B still owns `P02-T06`–`P02-T08`, the public/transactional part of
`P02-T03` and `P02-T05`, the remaining consumers for `P02-T09`, and `P02-T10`.

## Files changed

Production:

- `src/ovcaq/workflow/paths.py`
- `src/ovcaq/workflow/selection.py`
- `src/ovcaq/workflow/frontmatter.py`
- `src/ovcaq/workflow/policy.py`
- `src/ovcaq/workflow/transitions.py`
- `src/ovcaq/workflow/resume.py`
- `src/ovcaq/workflow/records.py`

Tests/package inventory:

- `tests/workflow/conftest.py`
- `tests/workflow/test_characterized_fixtures.py`
- `tests/workflow/test_selection.py`
- `tests/workflow/test_frontmatter.py`
- `tests/workflow/test_policy.py`
- `tests/workflow/test_transitions.py`
- `tests/workflow/test_resume.py`
- `tests/workflow/test_records.py`
- `tests/test_package_baseline.py`
- `tests/packaging/conftest.py`

## Behavior completed

- Selects the lowest five-digit Markdown PRD from `wip`, then `backlog`; `hold`
  is unreachable by the selection signature. Missing/non-directory lifecycle
  inputs are empty, and configured relative/absolute roots resolve without a
  runtime-directory assumption.
- Parses only a bounded flat frontmatter block, preserves characterized
  defaults/opt-ins/overwrite warnings, and treats `default_model` values as
  abstract tier keys. A missing tier map/key warns and applies no floor.
- Retains the strict `> 15` task ceiling and adds deterministic task-plan shape,
  reference, duplicate-ID, and dependency-cycle validation.
- Implements all six accepted transition rows and rejection rows. Effects are
  deep-copy pure; build starts review cycle one, rework increments/clears
  together, convergence marks review once, next-PRD uses one reset owner, and
  both drain rows write an empty `work.next_phase`.
- Derives resume targets from v1 committed state, with recovery operation first,
  then pause/review/build/done routing. Sanitized legacy build/review/converged
  fixtures retain their characterized outcomes after v1 translation.
- Resets only per-PRD owners while preserving the complete batch,
  `work.prd`, repository root, review cap, and operator pause request.
- Derives v1 completion summaries from decision statuses and materialized task
  counts. Repeated identical completion is idempotent; filename mismatch or a
  conflicting existing summary fails closed.
- Workflow production imports only state plus the standard library and contains
  no provider names/model identifiers or legacy runtime-root literal.

## Tests and exact results

- RED: `mise exec -- uv run pytest tests/workflow -q` → 4 expected collection
  errors because the empty workflow modules did not expose the new API.
- First GREEN: same command → `97 passed in 0.07s`.
- Final focused GREEN after characterized-fixture coverage:
  `mise exec -- uv run pytest tests/workflow -q` → `100 passed in 0.08s`.
- Initial full slice gate: `983 passed`, with one sdist allowlist failure because
  new test files were intentionally still untracked. Staging the cohesive slice
  made them committed-input candidates as required by the packaging contract.
- Final full slice gate: `mise exec -- uv run pytest` →
  `984 passed in 9.69s`.
- `mise exec -- uv run ruff check .` → `All checks passed!`.
- `mise exec -- uv run ruff format --check .` →
  `84 files already formatted`.
- `mise exec -- uv run mypy src/ovcaq` →
  `Success: no issues found in 47 source files`.
- `git diff --cached --check` → exit 0, no output.
- Final full pytest packaging cases built, inspected, and round-tripped the
  wheel/sdist successfully.

## Decisions

- Kept legacy pure function names where useful, but mapped all durable
  semantics to the closed v1 nesting instead of reintroducing flat state.
- Reset restores v1's pre-review cycle sentinel `0`; build-to-review establishes
  cycle `1`, and completion reports at least one cycle for characterized parity.
- Preserved the legacy next-PRD behavior of retaining the current PRD name until
  selection installs the next one; repository identity and batch state also
  remain untouched.
- Interpreted the retained `default_model` frontmatter key as a neutral tier-key
  hint. Workflow never resolves or names a provider model.
- Made completion retry-safe now because the PRD explicitly requires idempotent
  completion, even though the legacy append verb could duplicate a retry.
- Kept path containment/security ownership out of workflow; PRD 00005 owns
  project/runtime containment and discovery policy.

## Known risks or failures

- No unresolved test, lint, type, packaging, scope, or frozen-state failure.
- Frontmatter fields are pure effective values only until FT-04B wires the
  StateStore-backed public command.
- `phase-complete` and `complete-prd` are not public commands yet; FT-04B must
  compose these pure effects into one StateStore transaction with revision CAS.
- Defer, stall, park, durable recovery intent, failpoint replay, attempt-ledger
  writes, reports, generated docs, and neutrality guards are intentionally absent.

## Next session exact first action

Start fresh from `06fdf88149a7cafd6d3f4ec9aedf1510a59a652a`, read this handoff,
then begin FT-04B RED by porting the characterized defer/stall/park durable-boundary
matrix into `tests/workflow/` before adding any filesystem saga effect.
