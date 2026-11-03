# Review Context

## Code Changes

### Changed Files
_Diff scope: incremental review (changes since be5e385bd9714952b4803ee30f7c72e661c278f2)_

```
 CHANGELOG.md                         |   1 +
 src/ovcaq/workflow/_files.py         |  39 ++++-
 tests/packaging/rework_12_scripts.py |   3 -
 tests/packaging/rework_13_scripts.py | 147 +++++++++++++++++++
 tests/packaging/test_rework_11.py    |  10 +-
 tests/packaging/test_rework_13.py    | 274 +++++++++++++++++++++++++++++++++++
 6 files changed, 459 insertions(+), 15 deletions(-)
```

### Diff Content
Full diff available at: /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/tmp/review-diff-00004-14-20260913.diff

(569 lines)

## PRD Requirements

# OVCAQ deterministic workflow core

Status: wip | Version: 1 | Umbrella phase: 2 | Created: 2026-08-23

## Overview

### Source Contract

Implements Phase 2 source tasks `P02-T01`–`P02-T10` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

The current PRD lifecycle is spread across selection, frontmatter, transitions,
resume policy, records sagas, and renderers inside a personal skill. OVCAQ needs
that behavior extracted as provider-neutral deterministic services before a
supervisor or UI can consume it.

### Target User

Agents use installed workflow commands for handoff; the supervisor uses pure
workflow results; the operator receives deterministic reports.

### Success Metrics

- Existing lifecycle fixtures produce equivalent outcomes under OVCAQ v1 state.
- Every transition effect is covered row-by-row.
- Park/stall/defer recover idempotently at every durable interruption point.
- Workflow modules import no runtime, driver, provider, event, TUI, or launcher
  module.
- Command documentation is generated from the live parser.

## Preconditions and Boundaries

- Depends on completed PRDs 00002 and 00003.
- Consumes only committed state through the state application service.
- Keeps the fixed build/review/done/drain lifecycle; no arbitrary workflow graph.
- Agent/model selection belongs to runtime configuration, not workflow logic.

## Functional Decomposition

### Capability: PRD Discovery and Inputs

#### Feature: Selection and lifecycle paths

Select the lowest sequence in `wip`, then `backlog`, never `hold`; resolve
configured lifecycle directories without hardcoded `dev/local/autopilot` paths.

#### Feature: Frontmatter and plan policy

Parse/default frontmatter, report overwrite warnings, validate plan shape, and
derive the plan-size policy used by workflow instructions. Frontmatter model
hints name abstract tier keys, never provider model identifiers; a tier key is
resolved through the active agent's configured tier map, and a hint naming a
tier absent from that map logs a warning and applies no floor.

### Capability: Deterministic Lifecycle

#### Feature: Transition table

Implement full effects for build-to-review, review rework/convergence,
done-to-next-PRD, and drain. `phase-complete` performs one compound state
mutation; unknown phase/outcome pairs fail closed.

#### Feature: Resume, reset, and completion

Derive resume targets, reset only per-PRD owners, preserve batch fields, and
complete PRDs idempotently with deterministic summaries.

### Capability: Recoverable Records and Reports

#### Feature: Defer and park/stall sagas

Use operation IDs and durable `recovery.operation` intent around verified file
moves, record writes, reset, and commit. Restart reconciles any interrupted step.

#### Feature: Deterministic rendering

Render audit, report, and metrics views idempotently from state and records.
Human/machine output follows the shared CLI contract.

The installed command family is `select`, `frontmatter`, `phase-complete`,
`resume-target`, `check-plan`, `stall`, `park`, `defer`, `complete-prd`, and
`render audit|report|metrics` under `ovcaq workflow`.

## Structural Decomposition

```text
src/ovcaq/workflow/
  __init__.py
  selection.py
  frontmatter.py
  transitions.py
  resume.py
  policy.py
  records.py
  reports.py
src/ovcaq/cli.py
tests/workflow/
docs/operations.md
```

- Pure modules own selection, parsing, transition effects, resume, and policy.
- `records.py` is the only workflow filesystem saga and writes state only through
  the state service.
- `reports.py` owns deterministic projections, not durable authority.
- `cli.py` registers workflow verbs from one command registry.

## Dependency Graph

```text
PRD 00003 state service -> selection/frontmatter/policy
                       -> transitions/resume/reset/completion
                       -> records sagas
all workflow models    -> deterministic reports -> workflow CLI
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Pure Workflow Rules

- [ ] Port selection, lifecycle paths, frontmatter, resume, and plan policy.
- [ ] Port the transition table and every full effect set.
- [ ] Port reset/completed-PRD summary derivation.

**Exit Criteria**: Pure lifecycle fixtures match current outcomes under v1 state.

### Phase B: Recoverable Filesystem Operations

- [ ] Port defer with idempotent operation IDs.
- [ ] Port park/stall intent, move, record, reset, and commit steps.
- [ ] Port and extend every existing failpoint/reconciliation test.

**Exit Criteria**: Restart completes or safely retries every interrupted durable
boundary without duplicate records or lost work.

### Phase C: Commands, Reports, and Docs

- [ ] Implement all accepted `ovcaq workflow` commands.
- [ ] Consolidate audit/report/metrics rendering.
- [ ] Generate workflow command documentation from the parser.
- [ ] Add provider-neutral dependency/string guards.

**Exit Criteria**: Installed commands and deterministic renderers pass; workflow
has no higher-layer dependency.

## Test Strategy

- Selection order, `hold` exclusion, absent/invalid directories.
- Frontmatter defaults, explicit overrides, and warnings.
- Every phase/outcome row, rejection row, and complete effect set.
- Per-PRD reset versus preserved batch/capability state.
- Park/stall/defer failpoints, operation replay, and duplicate prevention.
- Drain/next-PRD behavior and post-drain state remaining terminal for the PRD.
- Idempotent report updates and parser/docs contract tests.

## Risks

- **Behavioral drift**: Run PRD 00002 characterization cases before refactoring.
- **Saga regression**: Preserve durable intent ordering and failpoint names first.
- **Layer leakage**: Enforce imports and forbidden provider strings in tests.
- **Duplicate command truth**: Generate help/docs from one registry.

## Acceptance Criteria

- [ ] Current lifecycle fixtures have equivalent OVCAQ outcomes.
- [ ] Every transition and rejection is covered row-by-row.
- [ ] Park/stall/defer recover at all durable boundaries.
- [ ] No hardcoded legacy runtime root remains.
- [ ] Workflow imports only state and standard-library/lower-layer code.
- [ ] PRD 00005 can consume stable workflow and state services.

## Unresolved Questions

None.


## Mechanical facts (computed, do not re-count)

Function line counts from `ast`. Cite these for countable claims; a
finding that contradicts this block is discarded at the review gate.

- `CHANGELOG.md` — skipped (non-python)
- `src/ovcaq/workflow/_files.py`
  - `_require_basename` — line 42, 2 lines
  - `_require_operation_id` — line 46, 2 lines
  - `_canonical_record_bytes` — line 50, 4 lines
  - `_fsync_directory` — line 56, 6 lines
  - `_fsync_directory_descriptor` — line 64, 2 lines
  - `_serialize_deferred_publication` — line 69, 12 lines
  - `_validate_record_encoding` — line 83, 10 lines
  - `_write_record_file` — line 95, 42 lines
  - `_finish_record_publication` — line 139, 18 lines
  - `_publish_record_file` — line 159, 15 lines
  - `_read_record_file` — line 176, 5 lines
  - `_read_record_content` — line 183, 38 lines
  - `record_defer` — line 223, 14 lines
  - `_deferred_item` — line 239, 6 lines
  - `_sync_deferred_directory` — line 247, 4 lines
  - `_ensure_directory_chain` — line 253, 26 lines
  - `_open_deferred_ledger` — line 282, 15 lines
  - `_lock_deferred_ledger` — line 300, 42 lines
  - `_lock_deferred_ledger.verify` — line 320, 13 lines
  - `_append_deferred_record` — line 344, 28 lines
  - `load_deferred_records` — line 374, 12 lines
  - `_open_lifecycle_directory` — line 389, 41 lines
  - `_verify_lifecycle_directory_identity` — line 432, 15 lines
  - `_artifact_stat` — line 449, 5 lines
  - `_validate_prd_artifact` — line 456, 4 lines
  - `_artifact_identity` — line 462, 4 lines
  - `_require_artifact_identity` — line 468, 6 lines
- `tests/packaging/rework_12_scripts.py` — no functions
- `tests/packaging/rework_13_scripts.py` — no functions
- `tests/packaging/test_rework_11.py`
  - `_assert_installed_origins` — line 25, 9 lines
  - `_initialize` — line 36, 8 lines
  - `_defer_command` — line 46, 23 lines
  - `_read_ledger` — line 71, 9 lines
  - `_seed_depth_ledger` — line 82, 15 lines
  - `_run_depth_candidate` — line 99, 20 lines
  - `_assert_candidate_within_depth_limit` — line 121, 20 lines
  - `_assert_candidate_exceeds_depth_limit` — line 143, 26 lines
  - `_assert_ledger_still_writable` — line 171, 24 lines
  - `test_installed_defer_keeps_the_composed_ledger_within_reader_depth_limit` — line 198, 41 lines
  - `test_installed_defer_retries_every_new_directory_fsync_after_failure` — line 245, 44 lines
  - `_set_prd` — line 291, 6 lines
  - `_render_command` — line 299, 10 lines
  - `_assert_retry_error` — line 311, 9 lines
  - `_successful_report_text` — line 322, 8 lines
  - `_seed_overlap_report` — line 332, 15 lines
  - `_start_report_actor` — line 349, 12 lines
  - `_await_actor_ready_and_start_publisher_b` — line 363, 21 lines
  - `_completed_process` — line 386, 7 lines
  - `_publication_or_none` — line 395, 6 lines
  - `_communicate_overlapping_publishers` — line 403, 42 lines
  - `_assert_overlap_publication_state` — line 447, 15 lines
  - `_retry_failed_overlap_publications` — line 464, 28 lines
  - `_assert_overlap_replay` — line 494, 17 lines
  - `_assert_overlap_final_report` — line 513, 18 lines
  - `test_installed_report_overlap_preserves_every_successful_publication` — line 533, 46 lines
- `tests/packaging/test_rework_13.py`
  - `_assert_installed` — line 19, 6 lines
  - `_prepare` — line 27, 19 lines
  - `_state_bytes` — line 48, 3 lines
  - `_identity` — line 53, 3 lines
  - `_invoke` — line 58, 34 lines
  - `_ledger` — line 94, 2 lines
  - `_assert_one_record` — line 98, 7 lines
  - `_assert_replaced_after_confirmation` — line 107, 32 lines
  - `test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt` — line 143, 47 lines
  - `test_installed_defer_confirms_parent_through_native_search_only_access` — line 192, 29 lines
  - `test_installed_defer_confirms_first_descendant_without_root_self_confirmation` — line 223, 28 lines
  - `test_installed_defer_avoids_creation_attempts_on_existing_external_ancestors` — line 253, 22 lines


## Tautological test shapes (computed, do not re-judge)

Each `[MECH]` line is a test whose shape cannot fail as written. Raise
it; step 6 adds any line the table lacks. `mech-check` is the finder.


Checked 7 test function(s) in 2 test file(s).


## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `be5e385bd971`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

replay: skipped (worktree add failed: Preparing worktree (detached HEAD be5e385)
fatal: could not create leading directories of '.git/worktrees/wt': Operation not permitted)


## Current verification evidence

Reviewed HEAD: 7291d9f80c5b7a55f63c406552e5b3e27025acad. Fresh suite: mise exec -- uv run pytest --basetemp /private/tmp/ovcaq-r14-full — exit 0, 1359 passed in 23.47s, 0 failed, 0 skipped. Other required gates recorded at the reviewed SHA in dev/local/autopilot/last-verification.json: sync, Ruff lint, Ruff format, mypy, build all exit 0. Its test counts were null after formatting, so the suite was rerun this review. No design document exists for this PRD.

## Architecture

# AGENTS.md — OVCAQ

OVCAQ means **Orchestration, Visibility, and Control for Agent Queues**. It is
an installable Python CLI/TUI that supervises a PRD-driven workflow through
Claude Code, Codex, or another headless coding agent.

The global `AGENTS.md` remains in force. This file adds project-specific rules.

## Current state

The repository is in planning/bootstrap. Until an implementation PRD replaces
it, `dev/local/plans/implementation-plan.md` is the architecture and sequencing
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
do not build an importer for the current `dev/local/autopilot/state.json` unless
a later requirement explicitly needs it. Temporary delegation during a local
canary is acceptable, but do not ship `autoclaude`, `autopilot`, `tracon`, or
`statectl` aliases as permanent public APIs.

