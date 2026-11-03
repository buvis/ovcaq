---
default_model: opus
model_tier_rationale: a protocol attribute and a route signature change across config and both drivers; classification tables and default tier values are exact
lane: full
---
# Driver failure classes and neutral default tiers

Source: [discovery 00004](../../discovery/00004-supervisor-robustness.md), driver-edge half; hold stubs 00036 and 00056 are owned here. Created 2026-10-25. The supervisor-start half is PRD 00062.

## Overview

### Problem Statement
Verified 2026-10-25: Claude `failure_payload` classifies "OAuth token has expired", "HTTP 429 Too Many Requests", "rate limit exceeded", "read ECONNRESET" and "connect ETIMEDOUT" as agent; Codex `classify_failure` returns unknown for "OAuth token has expired", "token expired", "ECONNRESET", "ETIMEDOUT" and "ENOTFOUND". Only `FailureClass.RATE_LIMIT` reaches the bounded wait in src/ovcaq/runtime/decision.py, so a rate limit takes a died-retry and parks the PRD. `DEFAULT_PHASE_TIERS` in src/ovcaq/drivers/__init__.py is the model names sonnet, opus, sonnet and no driver ships a default tier table, so a project without `[agents.<agent>.tiers]` fails `resolve_phase_route` with "Unknown agent tier: sonnet".

### Target Users
Operators whose sessions hit auth expiry, rate limits or network faults; operators running Codex or Claude without a hand-written tier table.

### Success Metrics
The tests named in Implementation Phases pass. Each diagnostic listed below maps to its class in a table test for its driver. A project with no tier table resolves every phase route through the driver's default tiers.

## Functional Decomposition

### Capability: Failure classification

#### Feature: Claude diagnostics map to their classes
- **Description**: `_FAILURE_MARKERS` in src/ovcaq/drivers/claude_events.py gains the markers below; `failure_payload` and its precedence order are otherwise unchanged.
- **Inputs**: The lowercased terminal result text.
- **Outputs**: A failure_class string consumed by the Claude decoder.
- **Behavior**: authentication gains "oauth", "token has expired", "token expired", "expired token", "not logged in", "http 401", "status 401". rate_limit gains "http 429", "status 429", "too many requests", "rate limit", "rate-limit", "rate_limit". connectivity gains "econnreset", "etimedout", "econnrefused", "eai_again", "getaddrinfo". Numeric codes keep their http or status context (hold 00056 rule); a bare number never classifies.

#### Feature: Codex diagnostics map to their classes
- **Description**: `classify_failure` in src/ovcaq/drivers/codex_events.py gains the auth and socket-error alternatives it misses (hold 00036) and pins the status wording from hold 00056.
- **Inputs**: The native diagnostic string.
- **Outputs**: A `FailureClass`.
- **Behavior**: The AUTHENTICATION alternation gains `oauth|token (?:has )?expired|expired token`; the CONNECTIVITY alternation gains `econnreset|etimedout|econnrefused|enotfound|getaddrinfo|eai_again`; the word-boundary wrapper and the authentication-to-agent precedence are unchanged. Premise, verified 2026-10-25: "unexpected status 503 Service Unavailable", "unexpected status 502 Bad Gateway", "unexpected status 403 Forbidden" and "exceeded retry limit, last status: 429 Too Many Requests" already classify as connectivity, connectivity, permission and rate_limit; this PRD only pins them. "Authentication failed" and "MCP server authentication failed" stay unknown.

### Capability: Neutral tiers

#### Feature: Neutral default tier keys
- **Description**: The default phase tiers are the neutral keys standard and deep; model names leave the shared modules.
- **Inputs**: Phase name; user and project configuration.
- **Outputs**: `PhaseSettings.tier` equal to standard for build and done and deep for review when configuration names no tier.
- **Behavior**: `DEFAULT_PHASE_TIERS` moves to src/ovcaq/config.py with the values standard, deep, standard and leaves src/ovcaq/drivers/__init__.py and its `__all__`; the lazy import in `_supervisor_phases` goes with it. `workflow_settings` adds the two neutral keys to `available_tiers` so a frontmatter floor of standard or deep applies without configuration. Premise: `rg -c DEFAULT_PHASE_TIERS src/ovcaq` returns 4 today; if the constant already lives in config.py, preserve it and report.

#### Feature: Driver default tier tables
- **Description**: Each driver maps the neutral keys to its own models and the route resolver consults that table under the configured one.
- **Inputs**: The selected driver; configured `[agents.<agent>.tiers]`.
- **Outputs**: A resolved model for standard and deep with or without configuration.
- **Behavior**: `AgentDriver` gains a `default_tiers` attribute (a read-only mapping). `ClaudeDriver.default_tiers` is standard to sonnet and deep to opus, the model aliases the Claude CLI accepts. `CodexDriver.default_tiers` maps both keys to the literal default, and `CodexDriver.build_launch` emits no model segment when the resolved value is default, so the Codex CLI uses its own configured model; a project maps deep to a larger model in `[agents.codex.tiers]` when it wants one. Both constructors merge `{**default_tiers, **settings.tiers}` into their settings so `build_launch` and src/ovcaq/drivers/edge.py see the merged table. `resolve_phase_route` gains `default_tiers: Mapping[str, str] | None = None`, checks the resolved tier against the merged table and returns the merged model; every call site in src/ovcaq/runtime/supervisor.py passes `default_tiers=driver.default_tiers`. `DRIVER_API_VERSION` is unchanged; the attribute is additive and both bundled drivers implement it.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/drivers/claude_events.py  # Classes
src/ovcaq/drivers/codex_events.py  # Classes
tests/drivers/test_adapter_failure_classes.py  # Classes
src/ovcaq/config.py  # Tiers
src/ovcaq/drivers/__init__.py  # Tiers
src/ovcaq/drivers/base.py  # Tiers
src/ovcaq/drivers/claude.py  # Tiers
src/ovcaq/drivers/codex.py  # Tiers
src/ovcaq/runtime/supervisor.py  # Tiers
tests/drivers/test_driver_v2.py  # Tiers
tests/drivers/test_claude_launch.py  # Tiers
tests/drivers/test_codex_launch.py  # Tiers
tests/runtime/test_adapter_launch_routing.py  # Tiers
tests/runtime/test_supervisor_preflight.py  # Tiers (fixtures off the old tier keys)
tests/runtime/test_supervisor.py  # Tiers (fixtures off the old tier keys)
tests/runtime/test_supervisor_adapters.py  # Tiers (fixtures off the old tier keys)
tests/runtime/test_rework_health.py  # Tiers (fixtures off the old tier keys)
tests/runtime/test_adapter_health.py  # Tiers (fixtures off the old tier keys)
tests/runtime/test_supervisor_process.py  # Tiers (fixtures off the old tier keys)
tests/workflow/test_configuration.py  # Tiers
tests/workflow/test_supervisor_configuration.py  # Tiers (fixtures off the old tier keys)
tests/integration/test_observer_terminal_cleanup.py  # Tiers (fixtures off the old tier keys)
tests/integration/test_supervisor_live_telemetry.py  # Tiers (fixtures off the old tier keys)
tests/packaging/test_installed_supervisor_cli.py  # Tiers (fixtures off the old tier keys)
docs/driver-protocol.md  # Tiers
docs/operations.md  # Tiers
CHANGELOG.md  # Classes
```

### Module: Classes
- **Maps to capability**: Failure classification
- **Responsibility**: Keep provider diagnostics tables at the driver edge and complete.
- **Exports**: `failure_payload` (Claude), `classify_failure` (Codex), unchanged signatures.

### Module: Tiers
- **Maps to capability**: Neutral tiers
- **Responsibility**: Neutral defaults in config; provider models only inside each driver's default table.
- **Exports**: `DEFAULT_PHASE_TIERS` from config, `AgentDriver.default_tiers`, `resolve_phase_route` with `default_tiers`.
New symbols: `default_tiers`, `AgentDriver.default_tiers`, `ClaudeDriver.default_tiers`, `CodexDriver.default_tiers`

## Dependency Graph

### Foundation Layer (Phase 0)
No module dependencies; built first. Premise re-check before editing: the five Claude and five Codex diagnostics above still misclassify; if one is already fixed, keep it and pin it.
- **Classes**: table-driven classification in both drivers.

### Core Layer (Phase 1)
- **Tiers**: Depends on nothing in Classes; sequenced after it so the test gate runs once at the end. Task 2 of this layer depends on task 1 (the neutral constant must exist before drivers map it).

### Integration Layer (Phase 2)
- **Documentation**: Depends on Classes and Tiers.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Every named diagnostic reaches its class in both drivers.

**Tasks**:
- [ ] Add the Claude markers and a table test. (no deps) — Acceptance: claude_diagnostics_classify_by_table in tests/drivers/test_adapter_failure_classes.py maps each marker above to its class through `failure_payload` and keeps "Malformed terminal error evidence" for a non-string result; existing Claude decode and rate-limit tests pass.
- [ ] Add the Codex alternatives and pin the hold 00056 wording. (no deps) — Acceptance: codex_diagnostics_classify_by_table covers the five new strings and the four hold 00056 strings; test_generic_authentication_failure_messages_remain_unknown, test_numeric_status_substrings_in_identifiers_are_unknown and test_failure_precedence_is_independent_of_diagnostic_order still pass.

**Exit Criteria**: The named tests pass; tests/drivers/test_neutrality.py passes.

### Phase 1: Core
**Goal**: Neutral tier keys that resolve without configuration.

**Tasks**:
- [ ] Move `DEFAULT_PHASE_TIERS` to config.py with the neutral values and add the keys to `available_tiers`. (depends on: Phase 0) — Acceptance: neutral_default_tiers_are_always_available in tests/workflow/test_configuration.py asserts `DEFAULT_PHASE_TIERS` equals standard, deep, standard and that `available_tiers` contains standard and deep with and without configured tiers; the existing assertion at tests/workflow/test_configuration.py:160 gains standard after the `rg -c` premise `'{"fast", "deep"}'` returns 1; tests/drivers/test_neutrality.py passes.
- [ ] Add `default_tiers` to the protocol and both drivers, thread it through `resolve_phase_route` and the supervisor. (depends on: Phase 1 task 1) — Acceptance: api_two_declares_default_tiers in tests/drivers/test_driver_v2.py; claude_default_tiers_map_standard_and_deep in tests/drivers/test_claude_launch.py asserts `--model sonnet` and `--model opus` with empty configured tiers; codex_default_tier_omits_model_segment in tests/drivers/test_codex_launch.py asserts no `-m` segment for standard and deep and that a configured deep still emits its model; unconfigured_project_routes_through_driver_default_tiers in tests/runtime/test_adapter_launch_routing.py resolves build, review and done without "Unknown agent tier" and a configured tier still wins; every fixture and fake driver that names the old tier keys (the test files marked "fixtures off the old tier keys" under Repository Structure, found by the design review) migrates to standard and deep so the whole suite passes.

**Exit Criteria**: The named tests pass; test_configured_supervisor_launches_each_selected_literal_model_and_effort still passes.

### Phase 2: Integration
**Goal**: Documentation matches the shipped tables.

**Tasks**:
- [ ] Document the neutral keys, the driver default tables, the Codex default literal and the new failure markers in docs/driver-protocol.md and docs/operations.md; add CHANGELOG.md entries. (depends on: Phase 1) — Acceptance: `rg -n "default_tiers" docs/driver-protocol.md` and `rg -n "standard" docs/operations.md` each find at least one line; `rg -n "sonnet|opus" docs/operations.md` finds nothing; CHANGELOG.md gains Fixed entries for both drivers' classification and a Changed entry for the tier keys.

**Exit Criteria**: The named checks plus `./tools/check` pass.

## Test Strategy

### Critical Scenarios
- **Happy path**: unconfigured_project_routes_through_driver_default_tiers → a project with no tier table launches build on the driver's standard model and review on its deep model.
- **Edge case**: codex_default_tier_omits_model_segment → the default literal removes the model segment while a configured deep model is still emitted verbatim.
- **Error case**: claude_diagnostics_classify_by_table → "HTTP 429 Too Many Requests" yields rate_limit and "connect ETIMEDOUT" yields connectivity, not agent.

## Risks

- **Marker over-reach**: substring markers can match prose; the table test includes the negative rows that must stay unknown or agent, and numeric codes keep their context words.
- **Frontmatter floors written as model names**: an OVCAQ project whose PRDs carry `default_model: opus` now warns unless `[agents.<agent>.tiers]` maps opus; document the mapping in docs/operations.md.
- **Codex default literal**: the value default is reserved as a tier value for Codex; the docs say so and the test proves a configured model is never swallowed.
