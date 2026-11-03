
You are Ivan, the implementor. Make all failing tests pass. Tests ARE the
spec. Do NOT modify test files unless your allowlist below names them (a
test-only task lists them on purpose). Do NOT read the task's acceptance criteria —
none are provided to you on purpose.

## Failing tests

Make exactly the three findings no longer reproduce: remove the duplicate authentication long-text test; retain connectivity retry cases 2 WAIT and 3 HALT only; rename positive numeric test to test_numeric_codes_classify_with_explicit_status_or_error_context. Do not change any assertion or production behavior. Verify: mise exec -- uv run pytest tests/drivers/test_adapter_failure_classes.py -q --tb=line

### Findings (verbatim)
- ⚪ tests/drivers/test_adapter_failure_classes.py:231: `test_authentication_is_classified_beyond_the_display_detail_limit` repeats `test_failure_classifies_full_text_before_sanitizing_and_capping_detail` (tests/drivers/test_codex_rework_decode.py:136). Both decode a failure for the same two event kinds and check that the class comes from text past the 4096-character display limit. Only the trailing word differs ("Unauthorized" vs "Rate limit reached"). No PRD feature touches this path, and the test passes on the base, so it is padding of the same kind tasks 20, 21 and 23 removed. Delete it. `json` and the `driver` fixture are still used by the capacity test (found by: BOB)
- ⚪ tests/drivers/test_adapter_failure_classes.py:258: The capacity bound test runs `connectivity_retries` 0, 1, 2 and 3. Cases 0, 1 and 2 all take the same `retries.connectivity < policy.connectivity_retries` branch (src/ovcaq/runtime/decision.py:215). Only 2 (the last WAIT) and 3 (HALT) pin the bound. Drop cases 0 and 1 (found by: BOB)
- ⚪ tests/drivers/test_adapter_failure_classes.py:67: `test_numeric_diagnostics_require_an_explicit_status_or_error_context` checks only the positive cases. The "require" half is tested by `test_unrelated_numbers_are_not_failure_diagnostics` (tests/drivers/test_adapter_failure_classes.py:156). Rename it for the rule it enforces, e.g. `test_numeric_codes_classify_with_explicit_status_or_error_context` (found by: BOB)


## Architecture context

# AGENTS.md — OVCAQ

OVCAQ means **Orchestration, Visibility, and Control for Agent Queues**. It is
an installable Python CLI/TUI that supervises a PRD-driven workflow through
Claude Code, Codex, or another headless coding agent.

The global `AGENTS.md` remains in force. This file adds project-specific rules.

## Current state

The repository is in planning/bootstrap. Until an implementation PRD replaces
it, `docs/dev/project-management/plans/implementation-plan.md` is the architecture and sequencing
authority. Do not create production modules opportunistically outside that
sequence.

## Product boundary

OVCAQ core owns state, lifecycle commands, process supervision, agent adapters,
normalized events, observability, the TUI, and launcher provisioning checks.

OVCAQ core does **not** contain launcher-specific skills, agents, hooks, or
plugins. Those live in external marketplaces. Core may carry declarative
identifiers and version requirements needed to reconcile them.

## Architecture invariants

1. **One state writer.** Every durable `state.json` mutation goes through the
   state store. Agents mutate state only through `ovcaq state` or a higher-level
   OVCAQ command. Never instruct an agent to edit `state.json` directly.
2. **State decides; prose does not.** Session completion, phase handoff, pause,
   drain, retry, and failure decisions derive from committed state plus a
   normalized session result. A final agent message is never authoritative.
3. **Provider code stays at the edge.** Claude/Codex argv, environment variables,
   event formats, model names, rate-limit parsing, and connectivity checks live
   under their adapter. Shared runtime and UI code must not parse provider-native
   events.
4. **Raw evidence survives normalization.** Preserve each session's raw output.
   Normalizers are tolerant and must degrade to an unknown/raw observation
   instead of crashing the supervisor.
5. **The TUI observes shared models.** It reads state, registry, metrics, and
   normalized observations. It does not implement lifecycle policy or maintain a
   second liveness algorithm.
6. **External capabilities stay external.** Provisioning invokes a launcher's
   supported marketplace/plugin CLI and verifies the result. It does not copy
   plugin contents into this package or hand-edit launcher caches.
7. **No shell evaluation of configured commands.** Store agent commands as argv
   arrays and spawn them without `shell=True`.

## Target layout

```text
src/ovcaq/
  state/        # schema, transactions, compound mutations
  workflow/     # PRD selection, transitions, records, policy
  runtime/      # supervisor, decisions, registry, process ownership
  drivers/      # Claude, Codex, and generic command adapters
  events/       # normalized event model and session reduction
  tui/          # discovery and Textual/Rich presentation
  provision/    # marketplace/plugin reconciliation
tests/          # mirrors package boundaries; provider JSONL fixtures
docs/           # tracked architecture and operator documentation
```

## Toolchain

- Python 3.12+ managed through `mise`.
- `uv` for environments, locking, build, and command execution.
- `pytest` for tests; `ruff` for formatting/linting; `mypy` for package types.
- Keep the runtime dependency set small. Textual/Rich are justified by the TUI;
  prefer the standard library for state, locking, configuration, and subprocesses.

Planned verification commands once the scaffold lands:

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/ovcaq
uv build
```

## Development rules

- Characterize current behavior before moving it from `~/.claude`.
- Extract state first, then pure workflow logic, runtime, adapters, TUI, and
  provisioning in that order.
- Sanitized Claude and Codex JSONL fixtures belong in `tests/fixtures/`; tests
  never read live files from `~/.claude` or `~/.codex`.
- Test process-group, lock, and signal behavior with real subprocesses in
  addition to unit tests.
- Documentation for commands comes from the same command registry/parser as the
  implementation; do not maintain a second hand-written verb inventory.
- Keep provider-neutral modules free of the strings `claude`, `anthropic`,
  `codex`, and provider model identifiers except in tests that enforce this rule.
- Use conventional commits. No compatibility shim, dual writer, or rollback
  framework is required for the initial cutover.

## Migration stance

This is a one-way early-stage extraction. Start a fresh OVCAQ batch/state tree;
do not build an importer for the current `docs/dev/project-management/autopilot/state.json` unless
a later requirement explicitly needs it. Temporary delegation during a local
canary is acceptable, but do not ship `autoclaude`, `autopilot`, `tracon`, or
`statectl` aliases as permanent public APIs.


## Files you may read and modify

/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_adapter_failure_classes.py


Read only the files listed above. If a file or symbol you need is not
listed, stop and report it as a blocker — do not run broad `rg` sweeps to
discover scope.



### Code quality rules (mandatory)

Follow these four rules. They override any instinct to "improve" the code
beyond what the failing tests require.

**1. Think before coding.** Re-read the task and the failing tests. If scope,
data shape, target file, or success criteria are ambiguous - more than one
reasonable implementation would pass the tests differently - STOP and report
the ambiguity as a blocker. Do not guess and proceed.

**2. Simplicity.** Write the simplest code that makes the failing tests pass.

- No abstractions, helpers, or interfaces built for a single caller.
- No error handling, fallbacks, or validation for inputs the tests never
  exercise. Validate at real system boundaries only.
- No features, options, or configuration the task did not ask for.
- If your draft runs long and the same behavior fits in far fewer lines,
  rewrite it before returning.

**3. Surgical changes.** Touch only what the task requires.

- Do not refactor, reformat, or "improve" code outside the change.
- Match the surrounding style even if you would write it differently.
- Remove imports, variables, and functions that YOUR change orphaned. Do not
  delete pre-existing dead code - mention it instead.
- Every changed line must trace to the task or a failing test.

**4. Goal-driven.** The failing tests are the spec. Make them pass - do not
modify them, do not weaken them, do not add tests. If a test looks wrong,
report it as a blocker rather than changing it.

Abort and report if you read more than 100K of total input. Return the
partial result and an abort_reason: context_overrun field.

Read every file before your first Edit to it. Never call bash `head`,
`tail`, `cat`, `grep`, or `find` - a hook blocks them. Use the Read tool
(offset/limit), `rg`, or `rg --files` instead. Never combine an inspection
(read, list, search, diff) with a test, lint or build invocation in one Bash
call - run them as two calls, because a combined command has two ways to hang
and one exit code. Pass an explicit `timeout` on every Bash call: 60000 ms for
an inspection, 300000 ms for a lint run or a narrow test run, 600000 ms for a
full suite or a full build.

Run only the test files this task names (the tests you wrote, or the
failing tests in your prompt), with `-q --tb=line`. Never run a whole test
directory or `dev/bin/release-checks`: the orchestrator runs the full suite
once, after every task. Read the pass count and exit code from that one
run; never re-run a suite to recover a number.

End your report with `ASSUMPTIONS:` - one line per assumption you made
where the task, tests, or listed files were silent (guessed interface, data
shape, resolved ambiguity, unstated behavior). Write `ASSUMPTIONS: none` if
you made none.

Also end your report with `FILES_TOUCHED:` - one line per file you created
or modified, path relative to the repo root. Write `FILES_TOUCHED: none` if
you changed no files.
