---
default_model: opus
model_tier_rationale: Cross-process contracts, extraction equivalence and concurrency require judgment.
lane: full
rework_cap: 3
catchup: force
plan_expansion: allow
eligibility: python3 tools/autopilot-prerequisites --prd 00061
---
# OVCAQ waves and worktree collaboration

Source: [three-layer design](../../designs/autopilot-optional-supervision.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
Advanced parallel work must preserve source worktree/assembly/review/landing behavior without moving workflow acceptance or TUI into the scheduler.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
cross_driver_wave_review → distinct driver reviewers consume isolated member work.. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Waves

#### Feature: Concurrent execution mechanics
- **Description**: Own worktree/process scheduling and recovery.
- **Inputs**: Controller-authorized wave/member plans, isolated worktrees and available review capacity.
- **Outputs**: Reserved workers, joined results, assembly and guarded landing facts.
- **Behavior**: Characterize every source wave CLI/option. OVCAQ owns reservations, process identities, slots, worktree creation/cleanup, assembly and git landing mechanics. Controller owns semantic members/review/custody acceptance; request permission before landing/push and recheck source/code identity. Explicit existing push authorization remains required. No duplicate workflow writer.

### Capability: Observations

#### Feature: Publish wave outcomes
- **Description**: Expose operator facts through the public projection.
- **Inputs**: Wave execution journal, controller snapshots and normalized events.
- **Outputs**: Versioned wave/job observations and partial-failure details.
- **Behavior**: Preserve abort, retry, interrupted landing and cleanup semantics. Emit neutral data for OV00064; do not edit or require TUI code. Advertise advanced readiness only after all source rows have evidence.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/runtime/waves.py
src/ovcaq/runtime/worktrees.py
src/ovcaq/runtime/wave_recovery.py
tests/runtime/test_waves.py
tests/runtime/test_wave_recovery.py
src/ovcaq/runtime/wave_observation.py
tests/runtime/test_wave_observation.py
docs/operations.md
CHANGELOG.md
```

### Module: Waves
- **Maps to capability**: Waves
- **Responsibility**: Own worktree/process scheduling and recovery.
- **Exports**: Reserved workers, joined results, assembly and guarded landing facts.
New symbols: `src/ovcaq/runtime/waves.py`, `src/ovcaq/runtime/worktrees.py`, `src/ovcaq/runtime/wave_recovery.py`, `tests/runtime/test_waves.py`, `tests/runtime/test_wave_recovery.py`

### Module: Observations
- **Maps to capability**: Observations
- **Responsibility**: Expose operator facts through the public projection.
- **Exports**: Versioned wave/job observations and partial-failure details.
New symbols: `src/ovcaq/runtime/wave_observation.py`, `tests/runtime/test_wave_observation.py`

## Dependency Graph

### Foundation Layer (Phase 0)
OV 00060 completed and explicit [autopilot].plugin_artifact with AP00017 conformance plus controller workflow.waves.v1. No Tower dependency. Current writer seam: src/ovcaq/state/store.py:126. Recheck source after predecessor merges; that citation describes the pre-extraction implementation. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Waves**: Depends on Phase 0 and the explicit task order below.
- **Observations**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Waves and Observations.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Map all source wave behaviors/options and controller acceptance points. (depends on: declared prerequisites) — Acceptance: wave_source_inventory rechecks source and rejects omitted behaviors.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Implement reservations, isolated workers/review slots and assembly/landing mechanics. (depends on: Phase 0) — Acceptance: wave_slot_exclusion, cross_driver_wave_review and custody_blocks_land preserve identities and controller permission.
- [ ] Implement abort/recovery/cleanup and revision-tagged observations. (depends on: Phase 1 task 1) — Acceptance: interrupted_landing_recovery and wave_partial_failure do not delete user work or duplicate processes.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Run installed plugin/controller wave canaries through public commands. (depends on: Phase 1) — Acceptance: advanced_profile_truth and wave_operator_parity require exact source coverage without TUI dependency.

**Exit Criteria**: Named integration scenarios and `./tools/check` pass. Generated CLI documentation matches the parser; no hold is released.

## Test Strategy

### Critical Scenarios
- **Happy path**: cross_driver_wave_review → distinct driver reviewers consume isolated member work.
- **Edge case**: interrupted_landing_recovery → landing reconciles its actual git outcome.
- **Error case**: custody_blocks_land → orchestration cannot bypass controller custody.

## Risks

- Concurrent git effects need recoverable intent and exact worktree ownership.
- Cleaning a worktree is authorized only after preserving its required evidence and work.
