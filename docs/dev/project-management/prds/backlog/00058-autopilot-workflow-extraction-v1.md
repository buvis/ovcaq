---
default_model: opus
model_tier_rationale: Cross-process contracts, extraction equivalence and concurrency require judgment.
lane: full
rework_cap: 3
catchup: force
plan_expansion: allow
eligibility: python3 tools/autopilot-prerequisites --prd 00058
---
# OVCAQ workflow authority extraction

Source: [three-layer design](../../designs/autopilot-optional-supervision.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
OVCAQ must cease being a second workflow writer while preserving current behavior and keeping process ownership local.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
same_state_manual_to_managed → same controller/state under both launch modes.. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Extraction

#### Feature: Replace direct workflow access
- **Description**: Route semantic state through the external controller.
- **Inputs**: Current state/workflow services, CLI entry points, source fixture mapping and installed controller.
- **Outputs**: Supervisor/workflow callers using one external authority.
- **Behavior**: Premise: current runtime, workflow_cli and TUI call StateService/StateStore. Inventory every read/write and route it through workflow_client. Remove workflow writer implementation only after installed equivalence, retaining source attribution/test mapping in the controller. Existing user-facing workflow/state verbs may become typed forwarding during this private transition but expose no raw setter. Final public docs name controller operations. No dual-write/fallback.

### Capability: Execution

#### Feature: Separate execution journal
- **Description**: Keep process facts without duplicating workflow truth.
- **Inputs**: Run identity, process ownership, claims, controller snapshots and recovery facts.
- **Outputs**: Execution journal with revision-tagged cached projections.
- **Behavior**: Process journal owns launches/routes/retries/raw references and operational control intent. Controller alone owns PRD/task/review truth. Adapt current TUI through controller client temporarily so it still runs before extraction; no direct writer survives. Preserve cf8be72 and 00062 guards. Tests retired from OVCAQ require mapped passing controller equivalents, not blanket deletion.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/workflow_client.py
src/ovcaq/cli.py
src/ovcaq/workflow_cli.py
src/ovcaq/supervisor_cli.py
src/ovcaq/runtime/supervisor.py
tests/workflow_client/test_extraction.py
tests/packaging/test_controller_boundary.py
src/ovcaq/runtime/execution_store.py
src/ovcaq/runtime/registry.py
src/ovcaq/tui/app.py
src/ovcaq/tui/model.py
tests/runtime/test_execution_store.py
docs/dev/architecture/README.md
docs/operations.md
CHANGELOG.md
```

### Module: Extraction
- **Maps to capability**: Extraction
- **Responsibility**: Route semantic state through the external controller.
- **Exports**: Supervisor/workflow callers using one external authority.
New symbols: `src/ovcaq/workflow_client.py`, `tests/workflow_client/test_extraction.py`, `tests/packaging/test_controller_boundary.py`

### Module: Execution
- **Maps to capability**: Execution
- **Responsibility**: Keep process facts without duplicating workflow truth.
- **Exports**: Execution journal with revision-tagged cached projections.
New symbols: `src/ovcaq/runtime/execution_store.py`, `src/ovcaq/tui/app.py`, `src/ovcaq/tui/model.py`, `tests/runtime/test_execution_store.py`

### Module: Existing source retirement
- **Maps to capability**: Extraction
- **Responsibility**: Reconcile each existing implementation/test with retained producer or consumer evidence before adaptation/removal.
- **Exports**: Source-to-destination coverage, no duplicate implementation.
- **Location**: `tests/workflow/test_applications.py`, `tests/workflow/test_ledger_publication.py`, `tests/workflow/test_selection.py`, `tests/workflow/test_records.py`, `tests/workflow/test_supervisor_configuration.py`, `tests/workflow/test_frontmatter.py`, `tests/workflow/test_deferred_diagnostics.py`, `tests/workflow/test_saga_artifacts.py`, `tests/workflow/test_deferred_ledger.py`, `tests/workflow/test_configuration.py`, `tests/workflow/test_canonical_metrics.py`, `tests/workflow/test_transition_preconditions.py`, `tests/workflow/test_resume.py`, `tests/workflow/test_blank_decisions.py`, `tests/workflow/test_ledger_integrity.py`, `tests/workflow/conftest.py`, `tests/workflow/test_saga_identity.py`, `tests/workflow/test_workflow_cli.py`, `tests/workflow/test_reports.py`, `tests/workflow/test_report_recovery.py`, `tests/workflow/test_sagas.py`, `tests/workflow/test_recovery_preconditions.py`, `tests/workflow/test_characterized_fixtures.py`, `tests/workflow/test_policy.py`, `tests/workflow/test_saga_publication.py`, `tests/workflow/test_boundaries.py`, `tests/workflow/saga_support.py`, `tests/workflow/test_transitions.py`, `tests/workflow/test_configuration_rework.py`, `tests/workflow/test_report_identity.py`, `tests/state/test_guarded_service.py`, `src/ovcaq/workflow/__init__.py`, `tests/state/test_store.py`, `src/ovcaq/workflow/policy.py`, `tests/state/test_schema.py`, `src/ovcaq/workflow/records.py`, `tests/state/test_schema_invariants.py`, `src/ovcaq/workflow/paths.py`, `tests/state/test_durability.py`, `src/ovcaq/workflow/frontmatter.py`, `tests/state/test_schema_limits.py`, `src/ovcaq/workflow/resume.py`, `tests/state/test_recovery_mutations.py`, `tests/state/test_service_commands.py`, `tests/state/test_store_concurrency.py`, `tests/state/test_schema_constraints.py`, `tests/state/test_cli.py`, `tests/state/test_store_transactions.py`, `tests/state/test_cli_limits.py`, `tests/state/test_installed_state.py`, `tests/state/test_supervisor_resume_preservation.py`, `tests/state/test_paths.py`, `tests/state/test_commands.py`, `tests/state/test_supervisor_commands.py`, `tests/state/test_service_contracts.py`, `src/ovcaq/workflow/reports.py`, `src/ovcaq/workflow/_files.py`, `src/ovcaq/workflow/transitions.py`, `src/ovcaq/workflow/_rename.py`, `src/ovcaq/workflow/selection.py`, `src/ovcaq/state/__init__.py`, `src/ovcaq/state/commands.py`, `src/ovcaq/state/schema.py`, `src/ovcaq/state/store.py`, `src/ovcaq/state/paths.py`
- **Location**: `src/ovcaq/runtime/_retention.py`, `src/ovcaq/runtime/_run_observation.py`, `src/ovcaq/runtime_cli.py`, `src/ovcaq/events/tail.py`, `src/ovcaq/cli_io.py`, `src/ovcaq/runtime/capability.py`, `src/ovcaq/runtime/_session_io.py`, `src/ovcaq/runtime/decision.py`, `src/ovcaq/runtime/session.py`, `docs/state-protocol.md`
New symbols: None; existing source files only.

## Dependency Graph

### Foundation Layer (Phase 0)
OV 00057 and 00062 completed; installed AP 00021 controller with core/jobs/reviews/records capabilities. Reconcile AP extraction against then-current OVCAQ fixes, including startup revert, before removal. Current writer seam: src/ovcaq/state/store.py:126. Recheck source after predecessor merges; that citation describes the pre-extraction implementation. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Extraction**: Depends on Phase 0 and the explicit task order below.
- **Execution**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Extraction and Execution.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Inventory every existing state/workflow caller and all source regression tests. (depends on: declared prerequisites) — Acceptance: extraction_inventory rejects unowned callers/test retirements; recheck source and skip/report conflicts.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Route workflow callers to the installed controller and isolate execution data. (depends on: Phase 0) — Acceptance: single_workflow_writer, startup_revert_preserved and transition_preconditions preserve current guards.
- [ ] Remove old workflow authority after mapping test evidence and adapt temporary TUI reads/controls. (depends on: Phase 1 task 1) — Acceptance: no_direct_workflow_mutation and extraction_behavior_equivalence cover CLI/runtime/UI callers; no fallback backend.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Run installed lifecycle/rework/completion with standalone-created controller state. (depends on: Phase 1) — Acceptance: same_state_manual_to_managed and no_live_state_import prove lease transfer without conversion or dual writes.

**Exit Criteria**: Named integration scenarios and `./tools/check` pass. Generated CLI documentation matches the parser; no hold is released.

## Test Strategy

### Critical Scenarios
- **Happy path**: same_state_manual_to_managed → same controller/state under both launch modes.
- **Edge case**: startup_revert_preserved → failed launch cannot leave false running workflow.
- **Error case**: single_workflow_writer → OVCAQ cannot mutate workflow files directly.

## Risks

- Workflow and execution consistency is reconciled, not a transaction across processes.
- Do not remove behavior merely because its old test imports a retired module.
