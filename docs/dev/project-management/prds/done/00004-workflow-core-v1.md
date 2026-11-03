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
