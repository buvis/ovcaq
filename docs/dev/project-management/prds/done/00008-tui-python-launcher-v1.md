# OVCAQ TUI and Python launcher

Status: backlog | Version: 1 | Umbrella phase: 6 | Created: 2026-08-23

## Overview

### Source Contract

Implements Phase 6 source tasks `P06-T01`–`P06-T10` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

Tracon observes useful state but parses Claude-native streams and duplicates
process/registry behavior, while Bash owns run/attach job control. OVCAQ needs
one optional provider-neutral TUI and Python launcher using shared runtime models.

### Target User

The operator needs fleet/detail visibility, safe controls, detach/reattach, and
plain fallback without affecting supervisor correctness.

### Success Metrics

- TUI crash or detach leaves the supervisor and owned agent tree alive.
- Pause/stop affect exactly the selected run through public services.
- No duplicate registry, liveness, workflow policy, or provider decoder remains.
- `ovcaq run`/`attach` require no Bash; no-TUI works when Textual fails.
- Unknown/raw-only providers remain visibly degraded rather than fabricated.

## Preconditions and Boundaries

- Depends on completed PRDs 00002–00007.
- The TUI observes shared state, registry, metrics, and normalized observations.
- It does not decide lifecycle transitions or maintain independent liveness.
- Clipboard/platform extras are excluded unless isolated behind a capability
  adapter; correctness never depends on them.

## Functional Decomposition

### Capability: Shared Read Models

#### Feature: Fleet and project discovery

Project fleet/detail views consume the atomic runtime registry and state/session
models, including stale-safe selection and explicit provider identity.

#### Feature: Tolerant live projections

Tail state, normalized events, metrics, and raw fallback with inode/truncation
handling. Missing/corrupt/partial observational data degrades without crashing.

### Capability: Operator Presentation

#### Feature: Workflow and activity panels

Present phase, tasks, review cycles, activity lanes, duration, usage, cost when
known, failure/parking/stopping/halt status, and telemetry capability gaps.

#### Feature: Post-drain capability status

Show pending/running/failed/succeeded/skipped state, failure attention, retained
evidence, and the exact independent retry command.

### Capability: Python Run and Attach

#### Feature: Safe controls

Detach, boundary pause, resume/reattach, confirmed stop, help, and selection call
public runtime/state services for exactly one run; `attach` never starts another
supervisor. The accepted controls remain `q` detach, `p` boundary pause, and
confirmed `s` stop.

#### Feature: TTY and fallback lifecycle

Interactive `ovcaq run` starts the owned background supervisor and attaches by
default. `q` detaches. Non-TTY/`--no-tui` remains foreground. Textual startup or
runtime failure falls back to the plain renderer without killing the supervisor.

## Structural Decomposition

```text
src/ovcaq/
  tui/{__init__.py,app.py,discovery.py,model.py,panels.py}
  events/tail.py
  runtime/{registry.py,supervisor.py}
  cli.py
tests/tui/
tests/runtime/test_attach.py
tests/integration/test_terminal_lifecycle.py
```

- `tui/discovery.py`: thin view over shared registry; no second stale algorithm.
- `tui/model.py`: tolerant projections from shared/provider-neutral models.
- `tui/panels.py`: rendering only.
- `tui/app.py`: navigation and public-service controls.
- `cli.py`: `run` TTY behavior and `attach` selection/fallback.

## Dependency Graph

```text
shared registry/state/events/metrics -> TUI read model -> panels/app
supervisor public controls           -> pause/stop/detach
run ownership + terminal capability -> attach or plain fallback
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Read Models and Views

- [ ] Port tolerant log tailing and state/metrics projections.
- [ ] Port fleet discovery onto the shared registry.
- [ ] Port phase/task/review/activity/usage/capability panels.
- [ ] Rebrand all user strings and XDG theme/config paths.

**Exit Criteria**: Views render shared normalized data and explicit unknowns.

### Phase B: Controls and Attachment

- [ ] Port pause/resume/stop/detach/help through public services.
- [ ] Implement `ovcaq attach` and TTY-default attachment from `ovcaq run`.
- [ ] Ensure exactly one selected run receives control actions.
- [ ] Add Textual-failure and plain/raw-only fallback.

**Exit Criteria**: Detach/TUI failure leaves supervisor alive; controls are scoped.

### Phase C: Terminal Migration Proof

- [ ] Port terminal/process integration scenarios from the Bash suite.
- [ ] Remove duplicate TUI registry/liveness/provider decoding.
- [ ] Prove `run`, `attach`, and no-TUI paths need no Bash launcher.

**Exit Criteria**: Python owns launch/attach job control and Bash is unnecessary.

## Test Strategy

- Fleet discovery with malformed/stale entries and multiple projects.
- Inode rotation, truncation, partial state/event/metric records.
- Known/unknown usage and cost, activity lanes, failure/capability statuses.
- Pause/stop exact targeting, confirmation, detach/reattach.
- TUI startup/crash during a live supervisor; plain fallback.
- TTY versus non-TTY and `--no-tui` lifecycle with real subprocesses.

## Risks

- **Second policy engine**: TUI consumes services and exposes no transitions.
- **UI kills work**: Separate supervisor ownership and integration-test crashes.
- **Provider assumptions**: Render only normalized types and explicit unknowns.
- **Terminal variance**: Capability-detect and preserve headless correctness.

## Acceptance Criteria

- [ ] TUI crash/detach never terminates the supervisor.
- [ ] Pause/stop target one selected run through shared services.
- [ ] Fleet/detail/activity/capability views tolerate incomplete evidence.
- [ ] No duplicate liveness, registry, workflow, or provider parser exists.
- [ ] `ovcaq run`, `attach`, and no-TUI operation require no Bash.
- [ ] PRD 00009 can add Codex without changing TUI policy.

## Unresolved Questions

None.
