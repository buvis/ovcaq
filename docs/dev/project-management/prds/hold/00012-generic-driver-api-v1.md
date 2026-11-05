# OVCAQ generic driver and extension API

## Three-layer requirements — 2026-10-25

This PRD remains held. [Architecture authority](../../designs/autopilot-optional-supervision.md) supersedes older ownership/packaging wording below: workflow state/lifecycle/lanes/review/records belong to Autopilot's controller; session/process/collaboration and operations API to OVCAQ; TUI presentation to Tower. All historical state-command criteria below are satisfied through that controller; all TUI criteria through the separate API client. Every original source task/acceptance ID remains required under the reconciled coverage manifest.

Generic drivers supply normalized execution facts to OVCAQ operations API. Raw-only/unknown telemetry is explicit; rendering acceptance is tested in separate Tower fixtures/integration. Do not add UI imports/dependencies to OVCAQ or implement Autopilot workflow policy in drivers. Preserve installed third-party extension conformance and existing release holds.

## Overview

### Source Contract

Implements Phase 10 source tasks `P10-T01`–`P10-T06` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

Two built-in adapters prove a seam, but OVCAQ cannot claim broader agent support
until a third-party package can register a driver/decoder without core changes
and a raw-only agent can still advance authoritative state safely.

### Target User

Agent-tool authors need a stable extension contract; operators need conformance
diagnostics and honest degraded telemetry for generic headless commands.

### Success Metrics

- A separately built/installed fake package registers through Python entry points
  without modifying OVCAQ core.
- A raw-only configured argv driver advances state and drains the workflow.
- Invalid placeholders or duplicate driver names fail before process launch.
- Unavailable telemetry is visibly unknown, never fabricated.
- Published driver/event protocols match conformance tests and policy.

## Preconditions and Boundaries

- Depends on completed PRDs 00002–00011 and stable personal-cutover evidence.
- Extends the process/event seam, not the fixed PRD workflow graph.
- Configured commands are argv arrays; no shell strings or evaluation.
- State/CLI compatibility policy is finalized in PRD 00014; this PRD stabilizes
  driver/event extension contracts.

## Functional Decomposition

### Capability: Generic Command Driver

#### Feature: Validated argv template

Accept an argv array with a closed placeholder set for repository, prompt file,
state path, phase, model, effort, and session directory. Reject missing, unknown,
ambiguous, or shell-like templates before launch.

#### Feature: Minimum loop contract

Generate a prompt file and environment references to the repository/state CLI.
A generic agent may run with raw-only telemetry if it can commit the required
OVCAQ handoff; provider-specific global configuration is not required.

### Capability: Third-Party Extension Discovery

#### Feature: Driver and decoder entry points

Publish stable `ovcaq.drivers` entry-point interfaces, unique-name resolution,
health probing, version/capability metadata, and optional structured decoders.

#### Feature: Installed sample extension

Build and install a separate sample package that registers a driver/decoder,
emits structured and unknown events, responds to process signals, and passes the
same conformance suite as built-ins where capability-applicable.

### Capability: Generic Diagnostics and Presentation

#### Feature: Driver conformance command

`ovcaq doctor --driver NAME` reports discovery source, protocol compatibility,
health, launch capabilities, telemetry levels, and actionable failures.

#### Feature: Raw-only runtime/TUI behavior

Supervisor decisions remain state-led when telemetry is absent; generic failure
is classified conservatively and TUI fields show unknown/raw-only capability.

## Structural Decomposition

```text
src/ovcaq/
  drivers/{base.py,command.py}
  events/{model.py,reducer.py}
  tui/model.py
  cli.py
tests/drivers/{test_command.py,test_extensions.py,test_conformance.py}
tests/fixtures/sample_driver/
docs/{driver-protocol.md,operations.md}
```

- `drivers/command.py`: argv-template validation and generic launch/summary.
- `drivers/base.py`: stable extension discovery and capability metadata.
- Sample driver is built/installed as an external distribution in tests, never
  imported through a checkout path.

## Dependency Graph

```text
stable driver/event protocols -> generic argv driver -> raw-only execution
stable entry points -> installed sample package -> conformance command/tests
telemetry capabilities -> runtime/TUI degraded presentation
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Generic Launch and Raw-Only Loop

- [ ] Define/validate argv placeholders and prompt/environment contract.
- [ ] Implement shell-free generic launch and conservative summary behavior.
- [ ] Drain the workflow using raw-only fake execution and committed state.
- [ ] Run every capability-applicable shared post-session decision row through
  the generic driver.

**Exit Criteria**: Generic raw-only execution advances and drains without core
provider branches.

### Phase B: External Extension Proof

- [ ] Stabilize driver/decoder entry-point and capability metadata contracts.
- [ ] Build/install a separate sample driver/decoder distribution.
- [ ] Run capability-aware conformance and duplicate/incompatible-name tests.

**Exit Criteria**: Third-party registration works without core changes.

### Phase C: Diagnostics, TUI, and Publication

- [ ] Implement `doctor --driver NAME` conformance/health output.
- [ ] Add raw-only TUI and generic failure presentation.
- [ ] Publish versioned driver/event docs and compatibility policy.

**Exit Criteria**: Docs, diagnostics, and tests define the same stable contract.

## Test Strategy

- Valid, missing, unknown, repeated, and injection-like argv placeholders.
- No shell execution; prompt/state/repo/session paths with spaces.
- Entry-point absent/duplicate/incompatible and installed sample discovery.
- Raw-only progress, drain, failure, timeout, TERM/KILL, and evidence retention.
- Optional decoder structured events plus malformed/unknown fallback.
- TUI unknown telemetry and doctor machine/human output.

## Risks

- **Arbitrary command injection**: Arrays, closed placeholders, no shell.
- **Nominal extensibility only**: Require a separately installed sample package.
- **Fake telemetry**: Capability metadata and explicit unknowns.
- **Premature broad workflow engine**: Extend launch/telemetry only.

## Acceptance Criteria

- [ ] External sample driver registers and passes applicable conformance tests.
- [ ] Raw-only execution advances state and drains.
- [ ] Invalid templates and duplicate/incompatible extensions fail prelaunch.
- [ ] Doctor and TUI expose capability gaps accurately.
- [ ] Stable driver/event docs and compatibility policy match tests.
- [ ] PRD 00013 can exercise provider-neutral contracts on Linux.

## Unresolved Questions

None.
