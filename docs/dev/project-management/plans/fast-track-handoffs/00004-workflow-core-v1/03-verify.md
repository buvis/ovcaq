# FT-04R verification handoff

- PRD: `00004-workflow-core-v1`
- Session: `FT-04R — deterministic verification`
- Date: `2026-09-01`
- Verdict: `pass`
- Reviewed range:
  `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..5a7ff023059bd396a177da7946a25ffe8d6d176d`
- Verified HEAD: `5a7ff023059bd396a177da7946a25ffe8d6d176d`
- Reviewed commits:
  - `06fdf88149a7cafd6d3f4ec9aedf1510a59a652a feat(workflow): implement deterministic pure rules`
  - `5a7ff023059bd396a177da7946a25ffe8d6d176d feat(workflow): add recoverable lifecycle boundary`

## Preconditions and protected artifacts

- Began and ended verification at exact HEAD
  `5a7ff023059bd396a177da7946a25ffe8d6d176d`.
- `git status --short --untracked-files=no`, `git diff --quiet HEAD --`, and
  `git diff --cached --quiet HEAD --` showed no tracked worktree or index
  changes before verification and again after all commands.
- `git diff --check
  b43bf2c94d5eb0fddafca55542ef2570b45e8d52..5a7ff023059bd396a177da7946a25ffe8d6d176d`
  exited 0 with no output.
- PRDs 00002 and 00003 remain at
  `dev/local/prds/done/00002-package-baseline-v1.md` and
  `dev/local/prds/done/00003-state-kernel-v1.md`.
- PRD 00004 remains at
  `dev/local/prds/wip/00004-workflow-core-v1.md`.
- Accepted implementation-plan SHA-256 before and after:
  `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
- Frozen `dev/local/autopilot/state.json` SHA-256 before and after:
  `ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f`.
- No autopilot command/state machine, review lens, PRD move, or production edit
  ran in this session.

## Exact verification commands

1. `mise exec -- uv sync --all-groups` — exit 0; `Resolved 25 packages in
   3ms`; `Checked 24 packages in 4ms`.
2. `mise exec -- uv run pytest` — exit 0; `1020 passed in 9.85s` on Darwin,
   Python 3.13.13, pytest 9.1.1.
3. `mise exec -- uv run ruff check .` — exit 0; `All checks passed!`.
4. `mise exec -- uv run ruff format --check .` — exit 0; `89 files already
   formatted`.
5. `mise exec -- uv run mypy src/ovcaq` — exit 0; `Success: no issues found in
   47 source files`.
6. `mise exec -- uv build` — exit 0; built
   `dist/ovcaq-0.1.0.dev0.tar.gz` and
   `dist/ovcaq-0.1.0.dev0-py3-none-any.whl` successfully, with the wheel built
   from the source distribution.
7. `mise exec -- uv run pytest tests/workflow
   tests/packaging/test_installed_cli.py -vv` — exit 0; `138 passed in 0.96s`.
8. A read-only `mise exec -- uv run python -c ...` exhaustive transition probe
   enumerated the four schema phases against all five public outcomes, plus an
   unknown phase and unknown outcome — exit 0; `transition matrix verified: 6
   accepted, 16 rejected`.

The full pytest gate rebuilt, installed, and imported the wheel in an isolated
environment. The focused run exposed every workflow row by test ID and repeated
the installed-wheel command-family checks.

## Source-ID coverage

| Source ID | Verified obligation and evidence |
| --- | --- |
| `P02-T01` | Selection and lifecycle-directory resolution: `test_selection.py` passes five-digit parsing, deterministic ordering, WIP priority, backlog fallback, hold exclusion, drain, missing/non-directory handling, and configured relative/absolute roots; inspected `workflow/paths.py` and `workflow/selection.py`. |
| `P02-T02` | Frontmatter defaults, warnings, abstract tier floor, and transactional application: `test_frontmatter.py` and `test_applications.py` pass all declared/default/invalid/overwrite/tier and revision-CAS cases; installed CLI coverage exercises the public parser boundary. |
| `P02-T03` | Closed transition table and compound `phase-complete`: `test_transitions.py` passes all six accepted rows, full valid effects, purity, and three representative rejection categories; an additional exhaustive probe verified the remaining known phase/outcome rejection pairs plus unknown phase/outcome inputs (`6 accepted, 16 rejected`); `test_applications.py` and `test_workflow_cli.py` prove one `StateStore` CAS transaction and stale-revision refusal. |
| `P02-T04` | Resume mapping and plan-size policy: `test_resume.py`, `test_policy.py`, characterized lifecycle fixtures, and public CLI tests pass recovery-first routing, build/review/pause/done rows, acyclic plan validation, invalid shapes, the exact `>15` ceiling, override behavior, and symbolic `oversized_plan` exit 3. |
| `P02-T05` | Per-PRD reset and completion summary: `test_records.py` passes exact cleared/preserved owners, purity, decision/task summary derivation, park-counter reset, idempotence, and mismatch/conflict refusal; store and CLI tests pass revision-CAS publication. |
| `P02-T06` | Defer ledger: `test_sagas.py` and `test_applications.py` pass required path-safe operation IDs, committed batch/active-PRD binding, canonical atomic publication, duplicate byte no-op, and invalid-boundary no-write behavior; inspected the dedicated lock/fsync path in `workflow/records.py`. |
| `P02-T07` | Stall/park saga: the focused matrix passes all five characterized boundaries for both operations (`after-mkdir-before-intent`, `after-intent-before-move`, `after-move-before-append`, `after-append-before-commit`, `after-commit-before-marker-delete`), exact revision/step/file/record states, replay, duplicate prevention, raw failure intent, conflict refusal, pending-stall reconciliation, and systemic second-park pause. |
| `P02-T08` | Deterministic audit/report/metrics: `test_reports.py` passes stable ordering, Markdown escaping, operation-ID deduplication, derived totals, and byte-idempotent audit/report publication; the CLI test executes all three surfaces without changing state revision. |
| `P02-T09` | Configured paths and legacy-root removal: relative and absolute lifecycle roots pass; CLI/sagas/reports consume the resolved repo root, `LifecyclePaths`, and runtime root; `test_boundaries.py` and direct inspection find no `dev/local/autopilot` or personal launcher path in workflow production code. |
| `P02-T10` | Parser-generated documentation: `docs/operations.md` equals `render_command_reference(build_parser())`; every workflow verb appears; `docs/state-protocol.md` command inventory is mechanically compared with every live leaf parser; the isolated installed-wheel help exposes the complete workflow family. |

## PRD acceptance coverage

1. **Equivalent lifecycle outcomes:** the three sanitized build-pending,
   review-cycle-two, and review-converged fixtures pass under v1 translation;
   the pure selection/frontmatter/resume/reset suites cover the remaining
   characterized rows.
2. **Every transition and rejection row:** all six closed transition rows pass
   with schema-valid complete effects. The exhaustive probe rejected all 14
   other known phase/outcome pairs plus explicit unknown-phase and
   unknown-outcome inputs; transition functions are also proven pure.
3. **Park/stall/defer recovery:** all ten stall/park failpoint combinations
   replay exactly once with no duplicate record; defer operation-ID retries are
   byte no-ops and invalid boundaries publish nothing.
4. **No hardcoded legacy runtime root:** the AST/string guard passes and direct
   inspection found no legacy runtime or personal launcher path in
   `src/ovcaq/workflow/`.
5. **Only state/lower-layer dependencies:** the AST import guard passes for
   every workflow module. Direct inspection found only standard-library,
   `ovcaq.state`, and sibling `ovcaq.workflow` imports, with no runtime, driver,
   event, TUI, provisioning, or launcher dependency.
6. **Stable services for PRD 00005:** pure functions, `StateStore` application
   boundaries, configured-path objects, reports, and the command parser import
   from the isolated wheel; package inventory and installed-module provenance
   tests pass outside the checkout.

## Inspected integration contracts

- **Installed command family:** exactly `select`, `frontmatter`,
  `phase-complete`, `resume-target`, `check-plan`, `stall`, `park`, `defer`,
  `complete-prd`, and `render audit|report|metrics` under `ovcaq workflow`.
- **Single parser truth:** `src/ovcaq/cli.py` owns registration and generates
  `docs/operations.md`; the complete `docs/state-protocol.md` inventory is also
  parser-checked.
- **StateStore-only authority:** frontmatter application, phase completion,
  completed-PRD insertion, saga intent/step/reset/commit, and systemic pause all
  accept `StateStore` and commit through `transaction()`. No workflow module
  opens or writes `state.json` directly. Defer ledgers and rendered reports are
  non-authoritative filesystem evidence.
- **Determinism:** transitions/reset/completion are deep-copy pure; reports sort
  unordered inputs, deduplicate records by operation ID, render complete
  projections, and preserve bytes on identical publication.
- **Range scope:** the two commits change workflow production modules, the
  shared CLI/error boundary, generated/operator protocol docs, and their tests
  and packaging inventories only. No runtime, driver, event, TUI, provisioning,
  or launcher implementation entered the range.

## Risks and next phase

- No unresolved verification failure, acceptance gap, source-ID gap, protected
  hash drift, tracked-worktree change, or scope breach was found.
- This is deterministic verification, not convergence review. PRD 00004 must
  remain in WIP until a separate fresh review coordinator runs Alice, Blake,
  and Bob and resolves every must-fix under the fast-track review protocol.
- Verification ran on macOS with Python 3.13.13; the declared lower bound is
  Python 3.12+, and cross-platform runtime/path integration remains owned by
  later PRDs.

## Fresh review coordinator exact first action

Start a fresh top-level read-only review coordinator from clean HEAD
`5a7ff023059bd396a177da7946a25ffe8d6d176d`; record the complete implementation
range
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..5a7ff023059bd396a177da7946a25ffe8d6d176d`
and this passing verification handoff, then dispatch Alice, Blake, and Bob
concurrently with exactly the isolated inputs and output contract in
`dev/local/plans/fast-track-implementation-plan.md`.
