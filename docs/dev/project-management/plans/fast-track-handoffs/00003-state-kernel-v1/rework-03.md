# FT-03E exceptional bounded-rework handoff

- PRD: `00003-state-kernel-v1`
- Session: `FT-03E — Exceptional bounded rework`
- Rework cycle: `03` (exceptional, explicitly authorized)
- Base SHA: `296e757cb96007a8c2079b0c4015f836b4fe4c2b`
- Head SHA: `7b2e9776b6d03edcdfa2ca758c0c389024a903fe`
- Commit: `7b2e977 fix(state): close exceptional cycle-03 gaps`
- Complete next-review range:
  `9cda04a6a0279a6306c24015ee2d3173fb916e68..7b2e9776b6d03edcdfa2ca758c0c389024a903fe`

## Authorization and inputs

`decision-01.md` records the user's explicit authorization for exactly one
exceptional bounded rework followed by one fresh mandatory three-lens review.
This session changed only the three authorized cycle-03 root causes and their
direct regression evidence.

Inputs read:

- `dev/local/plans/fast-track-implementation-plan.md`
- Phase-1 rows in `dev/local/plans/implementation-plan.md`
- `dev/local/prds/wip/00003-state-kernel-v1.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-review-03.md`
- `dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/review-03.md`
- `dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/decision-01.md`

Work started from the exact clean authorized base. No autopilot skill, command,
wrapper, saved state transition, or lifecycle move was invoked.

## Source IDs covered

- `P01-T02`: integer serialization closure and strict JSON decoding.
- `P01-T03`, `P01-T06`: fail-closed state/backup artifact reads and publication
  of only subsequently readable state.
- `P01-T05`: maximum accepted revision cannot roll into a 641-digit revision.
- `P01-T08`: programmatic task IDs, blocker IDs, and open JSON values share the
  decoder's integer limit before durable change.
- `P01-T10`: stable inline/file `usage`, durable `state_io`, and backup
  `invalid_backup` classifications for non-standard JSON constants.
- `P01-T11`: native regression coverage for every repaired boundary.

## Files changed

- `src/ovcaq/state/schema.py`
- `src/ovcaq/state/store.py`
- `docs/state-protocol.md`
- `tests/state/test_schema_limits.py`
- `tests/state/test_store.py`
- `tests/state/test_cli_limits.py`

## Authorized root causes resolved

### FT03R3-01 — Integer serialization closure

- Programmatic integers use the same 640-digit magnitude limit as textual JSON
  integers. The check uses integer magnitude rather than decimal conversion, so
  arbitrarily large in-memory integers fail deterministically.
- Typed fields and recursively validated open JSON values share that check.
- Initialization and transactions reject oversized programmatic values before
  publishing state or rotating backup bytes.
- Transactions and restores cannot advance the maximum accepted 640-digit
  revision into unreadable 641-digit state. State and backup bytes remain exact.
- Positive and negative maximum accepted integers round-trip through canonical
  serialization and the shared decoder.

### FT03R3-02 — Non-regular artifact preflight

- Existing state, backup, and lock artifacts must be regular files before any
  open. Symlink and multi-link checks remain in force.
- State and backup reads add `O_NONBLOCK`; this closes the lstat/open race where
  a regular pathname is replaced by a FIFO after preflight.
- FIFO, Unix-socket, and directory state/backup artifacts fail with the existing
  state/backup error classes before the target path is opened. Device nodes were
  not safely constructible in the unprivileged test environment.
- Regular single-link reads retain their behavior and are explicitly covered.

### FT03R3-03 — Strict JSON constants

- The sole JSON decoder rejects `NaN`, `Infinity`, and `-Infinity` through
  `parse_constant` before schema validation.
- Inline and JSON-file payloads return `usage`/1; malformed durable state returns
  `state_io`/2; malformed backup JSON returns `invalid_backup`/8.
- All twelve CLI cases retain empty stdout and preserve durable bytes.

## RED/GREEN evidence

- The first RED run reached the reproduced FIFO blocking open. A target-open
  guard was then added so the regression could fail without hanging the suite.
- Guarded focused RED matrix: `29 failed, 1 passed`; all three root causes were
  reproduced. The one pass was the already-valid 640-digit round-trip boundary.
- Initial focused GREEN matrix: `30 passed`.
- Expanded affected-file matrix after task/blocker durable-byte and restore
  rollover coverage: `151 passed in 2.44s`.
- Complete state matrix: `mise exec -- uv run pytest tests/state` — `811 passed
  in 8.13s`.

## Canonical verification

- `mise exec -- uv sync --all-groups`: passed; 25 packages resolved, 24 checked.
- `mise exec -- uv run pytest`: passed; 883 tests in 9.39s.
- `mise exec -- uv run ruff check .`: passed.
- `mise exec -- uv run ruff format --check .`: passed; 75 files already
  formatted.
- `mise exec -- uv run mypy src/ovcaq`: passed; 46 source files.
- `mise exec -- uv build`: passed; sdist and wheel built.
- `git diff --check` and staged `git diff --cached --check`: passed.
- Tracked worktree after commit: clean at
  `7b2e9776b6d03edcdfa2ca758c0c389024a903fe`.

## Decisions and bounds preserved

- The public schema version, command inventory, symbolic errors, and exit codes
  did not change.
- No deferred cycle-03 cleanup was reopened. The rework did not touch workflow,
  runtime, provider, TUI, provisioning, PRD lifecycle, project capsule, or
  `dev/local/autopilot/state.json`.
- PRD 00003 remains in `wip`. This implementation session did not run any review
  lens, close or move the PRD, or begin review cycle 04.
- No further rework cycle is authorized. A cycle-04 gate failure or reproduced
  contract defect requires another explicit user decision.

## Next session and exact first action

Next session: `FT-03R4 — Exceptional cycle-04 convergence-review coordinator`.

First action: from clean HEAD
`7b2e9776b6d03edcdfa2ca758c0c389024a903fe`, read the decision handoff and this
rework handoff, rerun canonical verification and the focused three-root-cause
regressions, then dispatch isolated Alice, Blake, and Bob concurrently. Review
the three exceptional repairs and their regression evidence at the new head;
do not reopen cycle-03 deferred cleanup.

### Next-session prompt

```text
Execute the exceptional review authorized by:

    dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/decision-01.md

Start a fresh FT-03R4 cycle-04 convergence-review coordinator session for PRD
00003. Read:

    dev/local/plans/fast-track-implementation-plan.md
    dev/local/prds/wip/00003-state-kernel-v1.md
    dev/local/reviews/00003-state-kernel-v1-fast-review-03.md
    dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/decision-01.md
    dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/rework-03.md

From clean HEAD 7b2e9776b6d03edcdfa2ca758c0c389024a903fe, rerun the complete
canonical PRD verification gate and focused regressions for integer
serialization/revision rollover, non-regular state/backup artifacts, and strict
NaN/Infinity/-Infinity classification. Review the complete updated PRD range:

    9cda04a6a0279a6306c24015ee2d3173fb916e68..7b2e9776b6d03edcdfa2ca758c0c389024a903fe

Dispatch all three mandatory lenses concurrently in isolated contexts using the
packets required by the fast-track plan: Alice (consensus/architecture), Blake
(blind PRD-only), and Bob (doubt plus de-slop, full R1-R5). The review evaluates
the three exceptional repairs and their regressions at the new head; it does not
reopen deferred cycle-03 cleanup. Each reviewer is read-only. Save cycle-04 raw
reports, write the consolidated cycle-04 review and review-04.md, and stop for
the contract's next action. No further rework is authorized. Do not edit code,
close or move the PRD, invoke run-autopilot/autoclaude, or mutate
dev/local/autopilot/state.json in the review session.
```
