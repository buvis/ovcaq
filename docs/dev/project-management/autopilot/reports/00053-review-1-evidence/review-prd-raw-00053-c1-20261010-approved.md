---
catchup: run
design: run
rework_cap: 2
default_model: opus
model_tier_rationale: diagnostic classification and model handoff require new predicates with regression preservation
---

# Adapter operational corrections

## Overview

### Problem Statement

[PRD 00009 review 2](../../reviews/00009-codex-adapter-v1-review-2.md) R1,
R4, R19, R20 and R23 reproduce incorrect terminal lanes, overload policy,
double model resolution, numeric false diagnoses, and overlay PATH rejection.
R12/R22 identify missing independent regression coverage for these paths.
This repairs completed adapter behavior under the [resolved discovery](../../discovery/00001-ovcaq-v1.md)
and [architecture](../../plans/implementation-plan.md), before provisioning.
Premise: recheck each finding at execution; if already corrected, retain a
regression and report it instead of forcing a production edit.

### Target Users

Operators using configured model tiers, wrapper PATHs and native agent diagnostics.

### Success Metrics

Named regressions prove correct argv, no spawn after failed health checks,
bounded overload retries, stable completed lanes and literal failure classes.
Keep driver API 2, observation protocol 1 and state schema 1 unchanged.

## Functional Decomposition

### Capability: Accurate native outcomes

#### Feature: Completed lane stability
- **Description**: A later close/wait cannot turn an already completed lane into failure.
- **Inputs**: Native lane running, completed, then shutdown/interrupted/not_found.
- **Outputs**: Existing normalized lane observations.
- **Behavior**: Only remembered unfinished lanes qualify for synthetic failure
  on these statuses. A completed lane remains completed; running-then-interrupted
  still fails. No TUI lifecycle workaround or new terminal state.

#### Feature: Diagnostic classification
- **Description**: Distinguish transient capacity from quota and unrelated numbers.
- **Inputs**: Native failure diagnostics and existing versioned failure fixtures.
- **Outputs**: Existing FailureClass values with unchanged precedence.
- **Behavior**: 'Selected model is at capacity' is connectivity, entering the
  existing bounded WAIT/retry policy. Numeric 401/403/429/502/503 classify only
  in explicit HTTP/status/error-code diagnostic contexts; 'processed 401 files'
  and equivalent ordinary counts remain unknown. Retain existing meaningful
  word-based diagnostics and genuine quota classification. Do not expand reset
  grammar or scan arbitrary agent prose. Pin every failure fixture's expected
  class as a literal independent oracle, not a call to classify_failure.

### Capability: Faithful configured launch

#### Feature: Resolve model once
- **Description**: Launch the model chosen by resolve_phase_route without remapping it.
- **Inputs**: Configured tiers including `{default: o3, o3: o3-pro}`.
- **Outputs**: Literal model argument selected by the route.
- **Behavior**: A supervised route for default launches o3. Preserve the existing
  direct build_launch tier-key precedence, explicit-model opt-in validation and
  the provider-neutral supervisor. Follow the existing edge adaptation pattern;
  do not reverse public tier precedence or introduce a second model policy.

#### Feature: Probe launch PATH
- **Description**: Health checks resolve executable names under the launch environment.
- **Inputs**: Host environment plus configured PATH overlay and wrapper argv.
- **Outputs**: Existing DriverHealth result and shared no-spawn failure.
- **Behavior**: A command available only through the overlay probes healthy;
  an overlay that hides it probes unhealthy. Absolute paths retain behavior.
  Cover both adapters' health failure before spawn without real inference.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/drivers/{codex.py,codex_events.py,claude.py}
src/ovcaq/drivers/edge.py                 # existing edge factories
tests/drivers/test_adapter_outcomes.py   # new behavioral regressions
tests/drivers/test_codex_decode_terminals.py
tests/runtime/test_adapter_launch_routing.py # new real-fake launch checks
tests/runtime/test_adapter_health.py     # new no-spawn/overlay checks
docs/driver-protocol.md
CHANGELOG.md
```

### Module: Native outcomes
- **Maps to capability**: Accurate native outcomes.
- **Responsibility**: Provider-edge lane and failure interpretation, independent
  driver regressions and corresponding protocol documentation.
- **Exports**: Existing CodexDriver.decode, item_lanes and classify_failure contracts.

### Module: Launch edges
- **Maps to capability**: Faithful configured launch.
- **Responsibility**: Correct model/environment adaptation, runtime regression
  fixtures and user-facing changelog entries.
- **Exports**: Existing driver probe/build_launch and registered factory interfaces.

## Dependency Graph

### Foundation Layer (Phase 0)
- **Native outcomes**: Existing drivers, event protocol and shared decision policy.

### Core Layer (Phase 1)
- **Launch edges**: Existing route resolver and driver registry; independent of
  outcome changes but executed after them to avoid shared-file contention.

### Integration Layer (Phase 2)
- **Regression/documentation closeout**: Depends on Native outcomes and Launch edges.
- Execute after PRDs 00051 and 00052; do not reopen their safety or version contracts.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Correct lane and diagnostic outcomes.

**Tasks**:
- [ ] Repair native outcomes and independent fixture expectations (no deps).
  Acceptance: `uv run pytest tests/drivers/test_adapter_outcomes.py
  tests/drivers/test_codex_decode_terminals.py` covers each completed/unfinished
  lane status, capacity WAIT and retry exhaustion, genuine HTTP diagnostics,
  unrelated numeric counts, and all failure fixtures with literal expected classes.

**Exit Criteria**: Native outcomes choose the existing correct lifecycle policy.

### Phase 1: Core
**Goal**: Make configured launches match their preflight and resolved route.

**Tasks**:
- [ ] Correct resolved-model edge adaptation (depends on: Phase 0).
  Acceptance: `uv run pytest tests/runtime/test_adapter_launch_routing.py
  tests/drivers/test_codex_launch.py` proves colliding tier/model values launch the
  route's model through the real fake supervisor and direct tier-key precedence remains.
- [ ] Correct PATH probing and both-adapter no-spawn coverage (depends on: Phase 0).
  Acceptance: `uv run pytest tests/runtime/test_adapter_health.py` covers temporary
  executable available only on overlay PATH, hidden host executable, absolute
  executable, and unhealthy launch prevention for both native adapters.

**Exit Criteria**: Route selection, health checks and actual spawn agree.

### Phase 2: Integration
**Goal**: Close the documented findings with coherent public behavior.

**Tasks**:
- [ ] Update protocol and changelog for the repaired behavior (depends on: Phase 1).
  Acceptance: documents describe once-resolved models, effective PATH probing,
  completed-lane stability and capacity connectivity; no new options or schemas.

**Exit Criteria**: `uv sync --all-groups`, `uv run pytest`, `uv run ruff check .`,
`uv run ruff format --check .`, `uv run mypy src/ovcaq` and `uv build` pass.
Full mandatory review runs in a fresh session after build handoff.

## Test Strategy

### Critical Scenarios
- **Happy path**: Ordinary configured routes and native terminals retain behavior.
- **Edge case**: Model value is another tier key; overlay PATH differs from host.
- **Error case**: Transient capacity retries with bounds; ordinary counts never
  masquerade as authentication, permission, quota or connectivity failures.

## Risks

- **Public compatibility**: Preserve direct tier precedence and strict argv behavior.
- **Broad matching**: Pin positive diagnostic forms and numeric negative controls.
- **Scope**: No rate-reset grammar, tier-default migration, probe descendant
  ownership redesign, provisioning or other held triage work.
