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
tests/drivers/test_adapter_failure_classes.py
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
  tests/drivers/test_adapter_failure_classes.py
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

## Design Doc

# Adapter operational corrections design

## Architecture fit

Repair provider-edge behavior from PRD 00009 without changing shared policy, driver API 2, observation protocol 1 or state schema 1. The operator owns local operation. Existing bounded retries and raw evidence remain authoritative. These are reversible code changes with no persistent-data migration; revert the repair commits if needed. PRD 00052 remains held and its strict version contract is untouched.

## Module placement

Edit `src/ovcaq/drivers/codex.py`, `codex_events.py`, `claude.py` and `edge.py` only where reproduced defects require changes. Add the PRD-named driver/runtime regression files and update existing fixture/terminal tests. Update `docs/driver-protocol.md` and `CHANGELOG.md` after behavioral work.

## Interfaces & contracts

Keep public `CodexDriver.build_launch(request: LaunchRequest) -> LaunchSpec` tier-key precedence unchanged, including explicit-model validation. Add a private `_ResolvedModelCodexDriver(CodexDriver)` in `drivers/edge.py`, mirroring `_ResolvedModelClaudeDriver`: its `build_launch` maps a configured model value back to a corresponding tier key before delegating. `build_driver` constructs this subclass for supervised routes. A resolved `o3` with tiers `{default: o3, o3: o3-pro}` must launch literal `o3`; direct `CodexDriver` given `o3` still launches `o3-pro`. The supervisor passes only selected.tiers[resolved.tier], per config.py:resolve_phase_route, so every supervised model is necessarily a configured tier value. A no-match literal cannot originate from this route; preserve public validation for any direct call rather than inventing a new explicit-model path. No provider strings or special cases enter shared runtime.

`item_lanes(item: object, started_lanes: set[str] | None = None)` retains its signature and return shape. The set passed by `CodexDriver._item_observations` contains only remembered lane identities whose terminal flag is false. `interrupted`, `shutdown`, and `not_found` synthesize `LANE_FAILED` only for those unfinished identities; completed lanes retain their completed observation history. Unsupported terminal statuses otherwise produce raw-unknown evidence. No additional lane state or TUI policy.

`classify_failure(detail: str) -> FailureClass` keeps authentication, permission, rate-limit, connectivity, timeout, agent precedence. Numeric 401/403/429/502/503 require explicit diagnostic context such as HTTP status, status code or error code, including genuine fixture spellings. Ordinary numeric counts remain UNKNOWN. Retain meaningful existing word diagnostics; `Selected model is at capacity` becomes CONNECTIVITY, using existing bounded WAIT/retry exhaustion. Do not change `failure_reset` grammar. Fixture expectations are literal independent oracles, never derived through the production classifier.

`ClaudeDriver.probe() -> DriverHealth` uses effective environment `os.environ` overlaid by configured launch environment when calling `shutil.which(command, path=effective_path)`. Explicit empty PATH stays empty; absent PATH follows subprocess/default PATH semantics. Absolute executable paths retain existing behavior. Codex probes already spawn with `dict(os.environ) | dict(settings.environment)`; reproduce and regress that behavior rather than changing it gratuitously. Both native adapters must fail health before supervisor spawn when command resolution is unhealthy. Fake Codex version/auth commands use the existing reviewed pin, never a live provider or a changed pin.

## Data flow

Supervisor route resolution passes a concrete configured value to the edge factory's driver; edge adaptation preserves that value through public tier resolution. Probe and launch see the same PATH overlay. Native records become existing observations; unfinished identity state controls synthetic lane failures. Connectivity summaries drive existing bounded retry policy. Raw JSONL remains available regardless of normalization.

## Reuse inventory

- `drivers/edge.py:_ResolvedModelClaudeDriver`: reuse inverse-tier adaptation for Codex without a second shared routing policy.
- `drivers/codex.py:_identities`, `_remember`: existing bounded terminal flags provide unfinished identity membership.
- `drivers/codex_events.py:item_lanes`, `classify_failure`: repair predicates in place, retain failure_reset and enum contracts.
- `drivers/codex.py:probe`, `_run_probe_command`: existing effective-environment subprocess probing supplies Codex PATH semantics.
- `drivers/claude.py:probe`, `_environment`: use existing launch environment for executable lookup.
- Existing fake-supervisor and fixture suites supply process isolation and bounded retry verification.

## Alternatives considered

1. Smallest diff: filter unfinished identities, constrain diagnostic numbers, and mirror the existing edge subclass. Chosen: preserves direct APIs and keeps provider adaptation at the edge.
2. Add a public resolved-model request flag or change direct tier precedence. Rejected: enlarges the driver contract and breaks existing callers.
3. Implement lifecycle or retry compensation in the TUI/shared runtime. Rejected: duplicates policy and violates the adapter boundary.

## Risks & edge cases

Repeated lane updates, unknown identities and bounded identity eviction must retain raw fallback. Numeric context must cover genuine fixtures without interpreting arbitrary prose counts. PATH absence and empty PATH differ. Duplicate configured model values may choose any matching key because each maps to the same literal value. Future native statuses, additional diagnostic spellings and launcher version updates can extend adapter fixtures independently; none requires broadening the strict pin or reset grammar now.

## Test strategy outline

Independent tests cover completed/running lane sequences for all three close statuses; positive numeric diagnostics and negative counts; literal class expectations for every failure fixture; capacity WAIT and retry exhaustion. Real fake-process supervisor tests capture colliding model argv and verify overlay-only, hidden-host and absolute executables plus both adapters' health-failure no-spawn. Preserve direct launch tests and run all six PRD verification gates after tasks. Full completion review runs in a fresh session.

## Review log

Dispatch 1 question: existing test_codex_failures bare-number precedence and test_codex_rework_decode capacity expectations conflict with corrected contract; planning must reconcile them while retaining independent literals. Native host mapping OpenAI gpt-6.1-sol/high; no blockers.
Dispatch 1 engagement retry question: absent PATH must use subprocess os.defpath; empty PATH needs an explicit conservative-health expectation. Anchored numeric, empty/missing PATH, collisions and eviction checked.
dispatch 1 (claude): cardinal-sin 0, blocker 0, non-blocker 0, question 2
Host identity above is the source schema label; actual native OpenAI gpt-6.1-sol/high.

Dispatch 2 non-blockers: empty/absent PATH semantics; completed/evicted/None lane details; cite retry bounds; enumerate diagnostic patterns; reconcile historical test literals. Questions: health gate location and classification policy wording. Raw output: docs/dev/tmp/00053-design-review-anthropic.txt. Blocker 1 closed by explicit supervised-route invariant (config.py:resolve_phase_route always selects a configured tier value); direct public validation unchanged.
dispatch 2 (codex): cardinal-sin 0, blocker 1, non-blocker 5, question 2
Host role swap: actual Anthropic sonnet via real use-sonnet wrapper, tool-less read-only; source codex is logical dispatch label only.

Dispatch 3: closed model blocker using supplied config/edge excerpts. Questions: same-agent route/factory invariant and health gate location. Existing drivers/base.py:_register_driver is confirmed health gate; CodexDriver.__init__ sets _settings. Non-blockers retained: PATH fallback, bounded retry citations, diagnostic spellings, lane edge cases, historical test literals, attribute citation and review-log hygiene. Raw verification output: docs/dev/tmp/00053-design-review-verify-anthropic.txt.
dispatch 3 (codex): cardinal-sin 0, blocker 0, non-blocker 7, question 2
Actual Anthropic sonnet, read-only use-sonnet host adaptation. All cardinal sins/blockers closed; 3/3 dispatches; no weak dispatches.
