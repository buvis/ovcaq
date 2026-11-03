---
default_model: opus
model_tier_rationale: Cross-process contracts, extraction equivalence and concurrency require judgment.
lane: full
rework_cap: 3
catchup: force
plan_expansion: allow
eligibility: python3 tools/autopilot-prerequisites --prd 00059
---
# OVCAQ mixed-driver job placement and isolation

Source: [three-layer design](../../designs/autopilot-optional-supervision.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
One driver per run cannot express Codex implementation reviewed by another provider. Claude-free completion requires a real Gemini route. Plugin child wrappers must not become competing schedulers.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
codex_build_claude_review and codex_build_gemini_review → distinct configured providers execute required roles. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Placement

#### Feature: Role-to-driver routing
- **Description**: Place controller-declared jobs on compatible drivers.
- **Inputs**: Job graph, neutral tiers/effort, configured role routes and capability facts.
- **Outputs**: Validated route and immutable launch specification per job.
- **Behavior**: Map roles to driver/model/tier/effort in OVCAQ. Validate required distinct-driver constraints before spawning. No silent substitute when unavailable; preserve 00063 default-tier/failure classification. Required review roster and task acceptance come from controller, never core hardcoding.

The user selected Codex + Gemini for Claude-free certification. Add a Gemini adapter through the existing driver contract and edge registration; characterize supported CLI invocation, authentication, session identity, raw events, cancellation and failure classes. Provider identity is distinct from driver name: two aliases of Codex cannot meet provider diversity. Gemini supplies the independent doubt voice, including Eve when required; remaining controller-resolved roles use isolated Codex or Gemini sessions. No Claude fallback in this profile. Retain Claude compatibility and all roster/availability rules from the controller.

### Capability: Isolation

#### Feature: Independent collaborative contexts
- **Description**: Enforce context separation at each launch.
- **Inputs**: Controller input allowlist/digests, role credentials and driver adapters.
- **Outputs**: Fresh native sessions with raw evidence and attributed results.
- **Behavior**: Codex builder → fresh Claude review is required. Blind reviewer gets only allowed PRD/rubric/source, not builder narrative/history. Retry uses fresh context and records actual driver/model/session/code identity. Managed plugin wrappers submit intent; cross-session launches happen here. Native subagent delegation requires an explicit job capability. Preserve bounded recursion and forward configured Sonnet effort correctly.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/runtime/job_router.py
src/ovcaq/config.py
src/ovcaq/drivers/edge.py
src/ovcaq/drivers/gemini.py
tests/drivers/test_gemini.py
tests/runtime/test_job_routes.py
src/ovcaq/runtime/job_inputs.py
src/ovcaq/runtime/session.py
tests/runtime/test_mixed_driver_jobs.py
tests/runtime/test_blind_job_inputs.py
docs/operations.md
CHANGELOG.md
```

### Module: Placement
- **Maps to capability**: Placement
- **Responsibility**: Place controller-declared jobs on compatible drivers.
- **Exports**: Validated route and immutable launch specification per job.
New symbols: `src/ovcaq/runtime/job_router.py`, `tests/runtime/test_job_routes.py`, `src/ovcaq/drivers/gemini.py`, `tests/drivers/test_gemini.py`

### Module: Isolation
- **Maps to capability**: Isolation
- **Responsibility**: Enforce context separation at each launch.
- **Exports**: Fresh native sessions with raw evidence and attributed results.
New symbols: `src/ovcaq/runtime/job_inputs.py`, `tests/runtime/test_mixed_driver_jobs.py`, `tests/runtime/test_blind_job_inputs.py`

## Dependency Graph

### Foundation Layer (Phase 0)
OV 00058 and 00063 completed; controller job/review capabilities. Synthetic roles and fake drivers keep core free of plugin content. Current writer seam: src/ovcaq/state/store.py:126. Recheck source after predecessor merges; that citation describes the pre-extraction implementation. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Placement**: Depends on Phase 0 and the explicit task order below.
- **Isolation**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Placement and Isolation.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Define route configuration and input-manifest validation from controller fixtures; characterize the Gemini CLI at a declared supported version. (depends on: declared prerequisites) — Acceptance: job_route_contract and role_neutrality reject plugin persona/model names in core logic; recheck adapter premises and preserve raw Gemini launch/event fixtures.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Implement the Gemini driver, routing and capability/provider-diversity preflight. (depends on: Phase 0) — Acceptance: codex_build_claude_review, codex_build_gemini_review, gemini_driver_conformance and unavailable_distinct_driver_refused verify argv/model/effort, identity/events/cancellation/failures and reject same-provider aliases or Claude fallback for the Claude-free profile.
- [ ] Implement fresh contexts and filtered job inputs with scoped credentials. (depends on: Phase 1 task 1) — Acceptance: blind_context_excludes_builder, retry_context_is_fresh and nested_scheduler_denied use isolated fake driver processes.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Record actual launch/result attribution and exercise real Codex + Gemini host probes when available. (depends on: Phase 1) — Acceptance: driver_identity_recorded and no_prose_phase_advance retain raw provider/model/session evidence for AP 00017; unavailable real hosts remain uncertified and cannot satisfy cutover.

**Exit Criteria**: Named integration scenarios and `./tools/check` pass. Generated CLI documentation matches the parser; no hold is released.

## Test Strategy

### Critical Scenarios
- **Happy path**: codex_build_claude_review and codex_build_gemini_review → distinct configured providers execute required roles with fresh contexts.
- **Edge case**: retry_context_is_fresh → failure does not carry builder/reviewer narrative into retry.
- **Error case**: blind_context_excludes_builder → prohibited input never reaches reviewer process.

## Risks

- Native sessions must be proved by supported driver identity, not agent declarations.
- Routing does not grant permission to change controller review policy.
