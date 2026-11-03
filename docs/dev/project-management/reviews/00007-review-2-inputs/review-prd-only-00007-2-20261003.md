# OVCAQ supervisor loop

Status: backlog | Version: 1 | Umbrella phase: 5 | Created: 2026-08-23

## Overview

### Source Contract

Implements Phase 5 source tasks `P05-T01`–`P05-T09` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

The current loop contains proven routing, retry, pause, park, drain, metrics,
and post-drain behavior but mixes provider details with orchestration. OVCAQ
needs a state-led supervisor that runs without Bash and explains every next
action from committed state plus a normalized session result.

### Target User

Operators need a reliable headless runner; agents need fresh phase sessions;
later UI code needs one authoritative supervisor rather than duplicate policy.

### Success Metrics

- A fake Claude driver drains build/review/done through `ovcaq run --no-tui`.
- Every continuation and halt is a tested pure decision from state plus summary.
- The full legacy loop/parity inventory has one implemented or retired outcome.
- Exactly one metric row is emitted per attempted session.
- Agoge failure preserves drained PRDs and retries independently.

## Preconditions and Boundaries

- Depends on completed PRDs 00002–00006.
- State and workflow services own durable transitions; drivers own provider data.
- This PRD provides foreground/no-TUI operation only; interactive attachment is
  PRD 00008.
- Agent final prose is never authoritative.

## Functional Decomposition

### Capability: Pure Post-Session Decisions

#### Feature: Ordered decision table

Compare pre/post state revision and fingerprints; let valid progress win over
provider exit noise; then evaluate pause, capabilities, completion, continuation,
rate limit, retry, repeated fingerprints, park, and systemic halt in that order.

#### Feature: Bounded failure policy

Classify credible provider rate limits, connectivity loss, timeout, process
death, permission/authentication failure, bootstrap failure, and repeat stalls.
All waits/retries/caps come from configuration and injectable time.

### Capability: Session Orchestration

#### Feature: Phase routing and execution

Resolve phase-specific agent/model/effort/timeout configuration, create one
fresh session, snapshot state, invoke the driver through runtime process/session
services, then reduce the result and execute exactly one decision. Routing
configuration is provider-neutral: `[phases.PHASE]` names tier, effort, and
timeout; `[agents.NAME.tiers]` maps tier keys to provider model identifiers;
`[agents.NAME.phases.PHASE]` may override tier or effort; the per-agent prompt
template lives in agent configuration with a driver-provided default. Drivers
map the neutral effort scale to their native control and never drop it
silently.

#### Feature: Lifecycle controls and evidence

Honor boundary pause, resume by clearing durable pause intent, immediate stop,
drain/archive, provider-neutral durable attention projected by the TUI,
raw/normalized logs, and one metrics row per session. The current personal
`notify_out` OS-script path is retired rather than copied. Fail closed if state
is unreadable.

### Capability: Post-Drain Capabilities

#### Feature: Durable generic lifecycle

For non-empty drain, move required capability through pending/running/failed/
succeeded; persist unique attempts and actionable attention. Empty batches mark
it skipped. Completed batch requires all required capabilities satisfied.

#### Feature: Independent agoge retry

`ovcaq capability retry agoge` reconciles stale running ownership, refuses a
live owner, creates an idempotent attempt, and never reopens drained PRD phases.

## Structural Decomposition

```text
src/ovcaq/
  runtime/
    decision.py
    supervisor.py
    capability.py
    session.py
  config.py
  cli.py
tests/runtime/
  test_decision.py
  test_supervisor.py
  test_capability.py
  test_loop_parity.py
```

- `decision.py`: pure ordered decision types/table; no I/O or provider parsing.
- `supervisor.py`: effects, loop lifecycle, routing, retries, metrics.
- `capability.py`: provider-neutral post-drain attempts and retry ownership.
- `session.py`: shared session execution/evidence integration from PRD 00005.

## Dependency Graph

```text
state + workflow + SessionSummary -> pure decision
config + process/session + driver -> supervisor effects -> next state/session
drained state + capability runner -> capability lifecycle -> batch completion
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Decision and Routing Core

- [ ] Extract the ordered post-session decision table as pure data/functions.
- [ ] Port phase agent/model/effort/timeout routing from configuration.
- [ ] Port snapshots, progress detection, fingerprints, and repeat accounting.
- [ ] Cover every parity-inventory decision or explicit retirement.

**Exit Criteria**: Every next action is reproducible from state plus summary.

### Phase B: Supervisor Effects

- [ ] Implement fresh-session launch/reduction/decision execution.
- [ ] Port bounded wait/retry/death/park/systemic-halt behavior.
- [ ] Port pause, resume, stop, drain, archive, provider-neutral attention, and
  metrics behavior; retire the personal OS-notification script path.
- [ ] Implement `ovcaq run --no-tui` foreground lifecycle and signal outcomes.

**Exit Criteria**: Fake Claude drains without Bash and emits one metric row per
session attempt.

### Phase C: Required Capability Lifecycle

- [ ] Implement generic pinned capability attempts and transition validation.
- [ ] Implement failure attention, nonzero exit, stale-owner reconciliation, and
  `ovcaq capability retry agoge` against a fake capability.
- [ ] Prove failure/retry never changes drained PRD results.

**Exit Criteria**: Success completes the batch; failure remains actionable and
independently retryable.

## Test Strategy

- Productive state plus nonzero exit; untouched state plus success prose.
- Pause/resume/stop, next phase, empty/non-empty drain, and completed capabilities.
- Rate limit with/without credible reset; bounded connectivity/death/timeout.
- Repeated fingerprints, park versus bootstrap/systemic halt.
- Agoge success/failure/stale-running/live-owner/independent retry.
- State read/write failure prevents another launch.
- One metric row per attempt and complete parity-inventory coverage.

## Risks

- **Prose-led continuation**: Decision inputs exclude final messages.
- **Retry storms**: Bound every wait/retry and test exhaustion outcomes.
- **Capability reopens work**: Make drained PRD state immutable to retry effects.
- **Hidden provider branch**: Accept only protocol types in supervisor modules.

## Acceptance Criteria

- [ ] Fake Claude drains build/review/done through installed no-TUI command.
- [ ] Every decision is explainable from committed state plus summary.
- [ ] Legacy loop inventory is fully implemented or explicitly retired.
- [ ] Metrics, pause, stop, retry, park, and halt contracts pass.
- [ ] Required post-drain capability lifecycle and independent retry pass.
- [ ] PRD 00008 can attach without owning lifecycle policy.

## Unresolved Questions

None.
