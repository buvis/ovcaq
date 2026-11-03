# Discovery: Operator experience

## Classification

Depth: standard | Date: 2026-10-19 | Status: open

## Problem

A new operator meets avoidable friction in the first ten minutes. `doctor`
reports failure straight after `init`, shows raw errno text as a check status,
and still exits 0. Human output of `state show`, `state validate`, `status`,
and `doctor` is the same one-line JSON as `--json`. `status` never shows the
batch, phase, or PRD. There is no `--version`. Error texts point at the wrong
thing: `stop` with no run says it "cannot stop the running supervisor" with a
raw `run.json` errno, a missing project reports a lock-file errno, and
`workflow select` prints "drained" when the PRD root or state is missing or
corrupt. The agent configuration table (`command`, `tiers`, `options`,
`environment`) is documented only in the driver protocol, so the first `run`
fails with "Claude permission_mode must be auto" and nothing to point at.

## Requirements

### Must have

- `init` creates every directory `doctor` checks, or `doctor` reports
  "missing, created on first run" as a pass. Check statuses are words
  (`ok`, `missing`, `denied`), with the detail in a separate field.
- `doctor` exits non-zero when `ok` is false.
- Human mode renders readable text for `state show`, `status`, `doctor`, and
  mutating verbs (what changed, new revision). `--json` stays byte-stable.
- `status` shows batch id and status, active PRD, phase, next phase, pause
  state, and the live run if any.
- `ovcaq --version` prints the package version.
- Missing project: one message, "no OVCAQ state at PATH; run `ovcaq init`",
  with a dedicated exit code, for every verb that needs state.
- `stop` and `attach` with no live run use the same clean wording.
- `workflow select` errors when the PRD root or state is missing or invalid
  instead of reporting "drained".
- `park` after a completed `stall` explains why it refuses, or succeeds; the
  operations reference states the rule.
- `docs/operations.md` documents the full `[agents.<name>]` table with one
  working Claude and one working Codex example.

### Nice to have

- `ovcaq init --agent claude|codex` writes a commented starter `ovcaq.toml`.
- `pause` on a project with no live supervisor says the flag is stored for
  the next run.

### Out of scope

- TUI redesign. The interactive views stay as they are.
- Provisioning checks (`provision --check`). That is PRD 00010.

## Constraints

- `docs/operations.md` stays generated from the live parser; new prose goes
  into the renderer, not the file.
- JSON envelopes and exit codes are documented in `docs/state-protocol.md`;
  changes update that table and its tests together.

## Codebase Context

- **Relevant code**: `src/ovcaq/cli.py` (parser, output helpers, no
  `--version`); `src/ovcaq/cli_io.py`; `src/ovcaq/runtime_cli.py:193-223`
  (doctor checks), `:154-165` (run health); `src/ovcaq/supervisor_cli.py`
  (`stop` error text); `src/ovcaq/workflow/selection.py:45-60` (missing
  directories read as empty); `src/ovcaq/state/store.py` (lock-file errno on
  missing project); `src/ovcaq/config.py:184-215` (agent table shape).
- **Conventions**: errors are `CommandError(ErrorCode.X, message)` from
  `src/ovcaq/errors.py`; the command reference renders through
  `render_command_reference` and is checked by `tests/workflow/test_workflow_cli.py:375`.

## Success Criteria

- A scripted first-run journey (`init`, `doctor`, `status`, `--version`,
  `run` without config) produces no raw errno text and no false failure.
- Every human-mode command in the journey prints text a person can read
  without a JSON viewer.

## Risks

- **Human output churn breaks scripts**: scripts must use `--json`; state that
  rule in the operations reference before changing human output.

## Discovery Log

### Q1: Where do these come from?

**Answer**: The 2026-10-18 readiness review journey lane, findings 10 and 15,
each reproduced against the installed wheel.
