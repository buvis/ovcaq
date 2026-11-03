---
default_model: opus
model_tier_rationale: Public protocol, stale controls and extraction equivalence require judgment.
lane: full
eligibility: python3 tools/autopilot-prerequisites --prd 00065
---
# OVCAQ headless distribution and TUI removal

Source: [three-layer design](../../designs/autopilot-optional-supervision.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
Even after API extraction the wheel and default command still bundle/launch Textual/Rich. The orchestration product must stand alone.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
headless_without_lantern → installed OVCAQ runs with no UI package.. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Distribution

#### Feature: Remove bundled presentation
- **Description**: Finish the one-way TUI extraction after parity.
- **Inputs**: OV00064 protocol, Lantern00003 installed artifact/evidence and source presentation map.
- **Outputs**: OVCAQ package with no UI modules or Textual/Rich dependency.
- **Behavior**: Premise: pyproject dependencies include rich/textual; CLI imports tui and autoattaches. Recheck, remove only mapped presentation after consumer parity. Preserve normalized projection in operations. Update lock/package tests; no optional extra that still couples core to Lantern.

### Capability: Launch

#### Feature: Headless command semantics
- **Description**: Separate starting supervision from attaching a UI.
- **Inputs**: TTY/non-TTY, foreground/default or explicit --detach.
- **Outputs**: Stable run identity and generated migration guidance.
- **Behavior**: ovcaq run remains foreground by default in all terminals; --detach launches supervisor and returns run/epoch. No automatic attach/import/launch of Lantern. Remove ovcaq attach and --no-tui behavior with explicit migration diagnostics, not permanent aliases. Resume controls do not attach. Update installed command tests and generated documentation. Closing Lantern never stops the supervisor.

## Structural Decomposition

### Repository Structure

```text
pyproject.toml
uv.lock
src/ovcaq/tui/__init__.py
src/ovcaq/tui/app.py
src/ovcaq/tui/model.py
src/ovcaq/tui/panels.py
src/ovcaq/tui/discovery.py
tests/packaging/test_headless_distribution.py
src/ovcaq/cli.py
src/ovcaq/supervisor_cli.py
tests/runtime/test_headless_launch.py
tests/packaging/test_installed_headless.py
docs/dev/architecture/README.md
docs/operations.md
README.md
CHANGELOG.md
```

### Module: Distribution
- **Maps to capability**: Distribution
- **Responsibility**: Finish the one-way TUI extraction after parity.
- **Exports**: OVCAQ package with no UI modules or Textual/Rich dependency.
New symbols: `tests/packaging/test_headless_distribution.py`

### Module: Launch
- **Maps to capability**: Launch
- **Responsibility**: Separate starting supervision from attaching a UI.
- **Exports**: Stable run identity and generated migration guidance.
New symbols: `tests/runtime/test_headless_launch.py`, `tests/packaging/test_installed_headless.py`

### Module: Existing source retirement
- **Maps to capability**: Distribution
- **Responsibility**: Reconcile each existing implementation/test with retained producer or consumer evidence before adaptation/removal.
- **Exports**: Source-to-destination coverage, no duplicate implementation.
- **Location**: `tests/tui/test_app.py`, `tests/tui/test_app_ended_selection.py`, `tests/tui/test_app_poll_responsiveness.py`, `tests/tui/model_support.py`, `tests/tui/test_activity_window.py`, `tests/tui/test_model_live_evidence.py`, `tests/tui/test_model_elapsed_duration.py`, `tests/tui/test_discovery.py`, `tests/tui/test_panels.py`, `tests/tui/test_activity_projection.py`, `tests/tui/test_rework_activity.py`, `tests/tui/test_neutrality.py`, `tests/tui/test_theme_persistence.py`, `tests/tui/test_codex_projection.py`, `tests/tui/test_model.py`
New symbols: None; existing source files only.

## Dependency Graph

### Foundation Layer (Phase 0)
OV00060,00061,00064 completed plus explicit [operator].client_artifact carrying Lantern00003 parity. Do not delete UI before that artifact is verified. Adapt/retire existing TUI tests only against mapped consumer or producer coverage. Existing coupling: src/ovcaq/tui/app.py:16 and pyproject.toml:16. Recheck these pre-extraction premises at execution. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Distribution**: Depends on Phase 0 and the explicit task order below.
- **Launch**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Distribution and Launch.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Recheck distribution/CLI premises and map every presentation test to producer/client evidence. (depends on: declared prerequisites) — Acceptance: ui_retirement_map blocks removal for unowned behavior or missing installed Lantern evidence.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Remove bundled UI/dependencies and preserve operations projection. (depends on: Phase 0) — Acceptance: wheel_no_tui_dependency and core_imports_no_ui inspect built wheel and a clean environment without UI packages.
- [ ] Implement headless defaults, detach and command migration diagnostics. (depends on: Phase 1 task 1) — Acceptance: tty_run_is_headless, detached_identity and removed_attach_diagnostic verify actual processes and generated help.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Run installed independent-product acceptance and record cutover evidence. (depends on: Phase 1) — Acceptance: headless_without_lantern, ui_crash_survival and independent_upgrade_contract prove optional presentation; no public release/hold activation.

**Exit Criteria**: Named integration scenarios and `./tools/check` pass; generated operations docs match parser output.

## Test Strategy

### Critical Scenarios
- **Happy path**: headless_without_lantern → installed OVCAQ runs with no UI package.
- **Edge case**: ui_crash_survival → killing Lantern leaves supervisor alive.
- **Error case**: wheel_no_tui_dependency → build metadata/imports contain no Textual/Rich or bundled UI.

## Risks

- Old CLI behavior intentionally changes; command docs and diagnostics must change together.
- Removing tests without a behavior/evidence destination would hide parity regressions.
