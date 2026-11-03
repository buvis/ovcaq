# FT-04B build handoff

- PRD: `00004-workflow-core-v1`
- Session: `FT-04B — Sagas and public boundary`
- Date: `2026-09-01`
- Base SHA: `06fdf88149a7cafd6d3f4ec9aedf1510a59a652a`
- Head SHA: `5a7ff023059bd396a177da7946a25ffe8d6d176d`
- Commit: `feat(workflow): add recoverable lifecycle boundary`
- Accepted implementation-plan SHA-256 before/after:
  `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`
- Frozen autopilot-state SHA-256 before/after:
  `ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f`

## Preconditions and scope

- Started from exact clean HEAD `06fdf88149a7cafd6d3f4ec9aedf1510a59a652a`.
- Verified PRDs 00002 and 00003 under `dev/local/prds/done/` and PRD 00004
  under `dev/local/prds/wip/`.
- Implemented only FT-04B. No runtime supervision, driver, event, TUI,
  provisioning, launcher, or provider-routing behavior was added.
- Did not invoke `run-autopilot`, `autoclaude`, or the review phase.
- Did not mutate `dev/local/autopilot/state.json`.

## Source IDs covered

- `P02-T02`: completed the StateStore-backed public frontmatter application.
- `P02-T03`: completed `phase-complete` as one revision-CAS transaction.
- `P02-T04`: exposed resume and plan policy through the installed workflow CLI;
  oversized plans retain exit 3 with symbolic `oversized_plan` output.
- `P02-T05`: completed the revision-CAS `complete-prd` boundary with
  idempotent deterministic summary insertion.
- `P02-T06`: complete idempotent defer ledger keyed by required operation IDs.
- `P02-T07`: complete recoverable stall/park saga and all five characterized
  failpoint/replay boundaries.
- `P02-T08`: complete deterministic audit, report, and metrics projections and
  idempotent publication.
- `P02-T09`: complete configured lifecycle/runtime-path consumption for sagas,
  records, reports, and CLI; no legacy runtime-root literal remains.
- `P02-T10`: complete live-parser workflow command reference and parser/docs
  contract coverage.

Together with FT-04A, all `P02-T01` through `P02-T10` implementation work is
present. PRD closeout remains owned by FT-04R after fresh verification and all
three review lenses converge.

## Files changed

Production and documentation:

- `src/ovcaq/cli.py`
- `src/ovcaq/errors.py`
- `src/ovcaq/workflow/frontmatter.py`
- `src/ovcaq/workflow/records.py`
- `src/ovcaq/workflow/reports.py`
- `src/ovcaq/workflow/transitions.py`
- `docs/operations.md`
- `docs/state-protocol.md`

Tests and packaging contracts:

- `tests/workflow/test_applications.py`
- `tests/workflow/test_boundaries.py`
- `tests/workflow/test_reports.py`
- `tests/workflow/test_sagas.py`
- `tests/workflow/test_workflow_cli.py`
- `tests/packaging/test_installed_cli.py`
- `tests/state/test_cli.py`
- `tests/state/test_commands.py`

## Behavior completed

- Defer records require a path-safe operation ID, bind to the committed active
  batch/PRD, serialize under a dedicated lock, publish atomically with file and
  directory fsync, and make duplicate operation-ID retries byte no-ops.
- Stall and park persist `recovery.operation` intent before moving a PRD from
  configured `wip` to `hold`. They verify regular-file source/destination state,
  fsync both lifecycle directories, append raw site/detail evidence, advance
  durable steps through StateStore, reset per-PRD owners, and clear recovery in
  the final commit.
- Restart replays `intent`, `moved`, and `recorded` states without duplicate
  evidence. Park reconciles any pending stall first. Two consecutive wrapper
  parks commit a systemic pause and reset atomically.
- Frontmatter, phase completion, and PRD completion use StateStore transactions
  with optional expected-revision CAS. Frontmatter effects use namespaced
  workflow extensions plus the owned review cap.
- Audit/report/metrics text is derived deterministically from committed v1
  state and deduplicated records. Audit and report files publish atomically and
  unchanged rerenders preserve bytes.
- The installed `ovcaq workflow` family contains exactly `select`,
  `frontmatter`, `phase-complete`, `resume-target`, `check-plan`, `stall`,
  `park`, `defer`, `complete-prd`, and `render audit|report|metrics`.
- `docs/operations.md` is generated from the live parser. The complete parser
  inventory in `docs/state-protocol.md` is mechanically checked.
- AST import and forbidden-string guards keep workflow independent of runtime,
  drivers, events, TUI, provisioning, provider names, and the legacy runtime
  root.

## Tests and exact results

TDD evidence:

- Saga RED: `pytest tests/workflow/test_sagas.py -q` failed during collection
  because `RecoveryConflictError` and the saga API did not exist.
- Application/report RED failed during collection because `apply_to_store` and
  `publish_audit` did not exist.
- CLI RED failed during collection because `render_command_reference` did not
  exist.
- First saga GREEN: `19 passed`.
- Combined saga/application/report GREEN: `28 passed`.

Final gates:

- `mise exec -- uv sync --all-groups` (offline cache) →
  `Resolved 25 packages`; `Checked 24 packages`.
- `mise exec -- uv run pytest tests/workflow -q` →
  `135 passed in 0.24s`.
- State/package-baseline integration rerun with Unix-socket/build permissions →
  `864 passed in 8.80s`.
- `mise exec -- uv run pytest -q` (offline cache) →
  `1020 passed in 9.87s`.
- `mise exec -- uv run ruff check .` → `All checks passed!`.
- `mise exec -- uv run ruff format --check .` →
  `89 files already formatted`.
- `mise exec -- uv run mypy src/ovcaq` →
  `Success: no issues found in 47 source files`.
- `mise exec -- uv build --offline --no-build-isolation --out-dir
  /private/tmp/ovcaq-ft04b-build-20260901-a` → source distribution and wheel
  built successfully.
- `git diff --cached --check` before commit → exit 0, no output.

The first unrestricted state integration attempt exposed only sandbox limits:
Unix-socket creation was denied and its isolated build could not resolve
Hatchling. The permitted rerun passed. The first full-suite attempt exposed a
pytest module-name collision between state and workflow `test_cli.py`; renaming
the new module to `test_workflow_cli.py` fixed collection, and the full rerun
passed.

## Decisions

- Kept FT-04A pure rules intact and added thin StateStore-backed application
  boundaries instead of duplicating transition/reset policy in the CLI.
- Used v1 `recovery.operation` as the sole durable saga intent. Marker files
  remain retired; the characterized `after-commit-before-marker-delete`
  failpoint name is preserved as a post-commit replay boundary.
- Kept the defer ledger outside `state.json` with its own lock because it is
  append evidence, while every authoritative lifecycle mutation remains a
  StateStore transaction.
- Preserved the legacy plan-ceiling exit status while adding the shared CLI
  contract's stable `oversized_plan` symbolic error.
- Renderers are complete projections, not append-only formatting state, so the
  same committed inputs always produce the same bytes.

## Known risks or failures

- No unresolved test, lint, format, type, packaging, scope, or frozen-state
  failure.
- FT-04R must review the complete PRD implementation range, not only this
  commit. No review was run in this implementation session.
- The requested handoff is an ignored `dev/local` artifact written after the
  implementation commit; the tracked worktree is clean.

## Review session exact first action

Start a fresh top-level FT-04R verification session from clean
`5a7ff023059bd396a177da7946a25ffe8d6d176d`, record the complete PRD range
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..5a7ff023059bd396a177da7946a25ffe8d6d176d`,
read this handoff, and run `mise exec -- uv sync --all-groups` as the first
verification command. Complete the full six-command gate before starting a
separate fresh review coordinator that dispatches Alice, Blake, and Bob with
the isolation rules in `fast-track-implementation-plan.md`.
