---
default_model: opus
model_tier_rationale: Public protocol, stale controls and extraction equivalence require judgment.
lane: full
eligibility: python3 tools/autopilot-prerequisites --prd 00064
---
# OVCAQ public operations API

Source: [three-layer design](../../designs/autopilot-optional-supervision.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
The current TUI imports StateStore, registry and supervisor internals. An independent client needs a stable observation/control boundary.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
operations_without_ui → headless API works independently of Textual/Rich.. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Observations

#### Feature: Versioned operations projection
- **Description**: Publish normalized fleet/run observations without a TUI dependency.
- **Inputs**: Execution registry/journal, controller snapshots and existing shared observation reducers.
- **Outputs**: Contract/list/snapshot/events commands and exported schemas/fixtures.
- **Behavior**: Implement Contract C command spellings and fields exactly. Extract producer projection from current tui/model.py while leaving rendering in the UI. Keep shared liveness algorithm, provider normalization and raw evidence in OVCAQ. Revision-tagged snapshots, sequence/cursor, bounded retention, gap/reset, unknown/raw-only/partial states and safe bounded log references are mandatory. API version is separate from controller protocol.

### Capability: Controls

#### Feature: Identity-bound operator requests
- **Description**: Expose control with durable receipts and truthful outcomes.
- **Inputs**: Exact run ID/epoch, expected control revision, observed workflow revision and idempotent request.
- **Outputs**: Pause/resume/stop/retry responses: accepted/applied/rejected/committed-but-observation-stale.
- **Behavior**: OVCAQ validates identity before/after effects, forwards workflow effects to controller, and owns OS signals/escalation. Preserve existing RunControlService committed-stale semantics. Lost acknowledgements replay receipts; stale selection cannot affect a replacement run. Controller outage permits stop for owned processes with pending reconciliation visible: exact run epoch/control CAS still applies, but stale/unavailable workflow revision cannot veto stop. Pause inhibits dispatch at a safe boundary; resume rechecks controller permission; retry requests a legal job attempt without rewinding workflow truth. Export producer provenance; no UI import.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/operations/__init__.py
src/ovcaq/operations/projection.py
src/ovcaq/operations/protocol.py
src/ovcaq/operations/events.py
src/ovcaq/operations_cli.py
src/ovcaq/cli.py
tests/operations/test_projection.py
tests/operations/test_stream.py
contracts/operations-v1.json
contracts/operations-fixtures-v1.json
contracts/operations-provenance.json
src/ovcaq/operations/control.py
src/ovcaq/tui/app.py
src/ovcaq/tui/model.py
tests/operations/test_controls.py
tests/operations/test_contract.py
tools/export-operations-contract
docs/operations.md
CHANGELOG.md
```

### Module: Observations
- **Maps to capability**: Observations
- **Responsibility**: Publish normalized fleet/run observations without a TUI dependency.
- **Exports**: Contract/list/snapshot/events commands and exported schemas/fixtures.
New symbols: `src/ovcaq/operations/__init__.py`, `src/ovcaq/operations/projection.py`, `src/ovcaq/operations/protocol.py`, `src/ovcaq/operations/events.py`, `src/ovcaq/operations_cli.py`, `tests/operations/test_projection.py`, `tests/operations/test_stream.py`, `contracts/operations-v1.json`, `contracts/operations-fixtures-v1.json`, `contracts/operations-provenance.json`

### Module: Controls
- **Maps to capability**: Controls
- **Responsibility**: Expose control with durable receipts and truthful outcomes.
- **Exports**: Pause/resume/stop/retry responses: accepted/applied/rejected/committed-but-observation-stale.
New symbols: `src/ovcaq/operations/control.py`, `tests/operations/test_controls.py`, `tests/operations/test_contract.py`, `tools/export-operations-contract`

## Dependency Graph

### Foundation Layer (Phase 0)
OV00058 completed. Work can run beside 00059/00060 with fake execution facts; serialize shared cli.py edits. Core observations/controls are implemented here; later job/wave capabilities expose unavailable until their producers land. Existing coupling: src/ovcaq/tui/app.py:16 and pyproject.toml:16. Recheck these pre-extraction premises at execution. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Observations**: Depends on Phase 0 and the explicit task order below.
- **Controls**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Observations and Controls.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Define exact request/response/event schemas and characterize existing projection/control semantics. (depends on: declared prerequisites) — Acceptance: operations_fixture_contract and projection_source_map recheck app/model coupling before extraction.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Extract observation projection and implement contract/list/snapshot/events commands. (depends on: Phase 0) — Acceptance: event_gap_resnapshot, unknown_not_completed and raw_only_projection retain source liveness outcomes without importing Textual/Rich.
- [ ] Implement controls with CAS, exact identity and durable receipts. (depends on: Phase 1 task 1) — Acceptance: stale_run_control_refused, committed_observation_stale and stop_with_controller_offline preserve identity safety.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Export schemas/fixtures/provenance and adapt the temporary bundled UI to public operations. (depends on: Phase 1) — Acceptance: operations_without_ui and control_lost_ack_replay run with UI modules blocked; publication is not included.

**Exit Criteria**: Named integration scenarios and `./tools/check` pass; generated operations docs match parser output.

## Test Strategy

### Critical Scenarios
- **Happy path**: operations_without_ui → headless API works independently of Textual/Rich.
- **Edge case**: event_gap_resnapshot → clients receive explicit loss and can rebuild view.
- **Error case**: stale_run_control_refused → recycled run/PID cannot receive stale commands.

## Risks

- Projection must not grow a second liveness algorithm.
- Avoid an HTTP daemon or broker; initial local CLI JSON/JSONL is sufficient.
