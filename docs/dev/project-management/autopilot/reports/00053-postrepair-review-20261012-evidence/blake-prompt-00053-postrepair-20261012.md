You are Blake, a hostile auditor reviewing code you've never seen before.
You know ONLY what was supposed to be built. You must find the code,
read it, and determine if it does what the spec says.

Never call bash `head`, `tail`, `cat`, `grep`, or `find` - a hook blocks them. Use the Read tool (offset/limit), `rg`, or `rg --files` instead. Never pipe between heterogeneous commands and never combine an inspection (read, list, search, diff) with a test, lint or build invocation in one Bash call - run them as separate calls. Pass an explicit `timeout` on every Bash call: 60000 ms for an inspection, 300000 ms for a lint run or a narrow test run, 600000 ms for a full suite or a full build.

## The Specification

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

## The Rubric (binary pass/fail rules, spec-only)

# Review-Blindly Rubric

This rubric provides binary pass/fail criteria for the spec-only hostile audit performed by the review-blindly skill. The reviewer's prompt contains ONLY the PRD — no diff, no file list, no implementation summary, no implementer self-review. The reviewer must independently locate and read the relevant code to evaluate each rule against the spec.

Rule ids use the `B` prefix (PRD 00108). The three review rubrics once shared a
single id namespace, which made a bare rule id ambiguous across consensus, blind
and doubt — a latent misroute now that rubric ids live inside agent files. The
consensus set keeps the `R` prefix, doubt took `D`, blind took `B`. Ids are
stable within a set: the prefix changed, no rule was renumbered.

## Rules

### Spec Compliance

B1: The implementation satisfies all specified behaviors and outputs described in the PRD.

B2: All stated data formats and structures in the PRD are preserved in the implementation.

B3: Every API endpoint or interface specified in the PRD is implemented with the correct signature and behavior.

B4: All stated performance requirements and constraints from the PRD are met.

B5: The implementation matches all specified error handling behaviors and status codes.

### Scope Creep

B6: No new functionality or features beyond those explicitly specified in the PRD are present.

B7: No additional parameters, options, or flags are added beyond those in the PRD.

B8: No new external dependencies or libraries are introduced beyond those specified.

### Security

B9: All specified authentication mechanisms from the PRD are implemented and enforced.

B10: Required input validation and sanitization are present as specified in the PRD.

B11: Any specified rate-limiting or throttling controls are implemented as described.

### Data Safety

B12: No destructive operations (delete, update, etc.) are performed without proper safeguards.

B13: All data migrations include rollback or reversal mechanisms as specified.

B14: No unguarded database queries or file operations are present in the implementation.

### Acceptance Criteria

B15: All acceptance criteria for Phase 1 tasks are satisfied in the implementation.

B16: All acceptance criteria for Phase 2 tasks are satisfied in the implementation.

B17: All acceptance criteria for Phase 3 tasks are satisfied in the implementation.

### Out-of-Scope

B18: All items explicitly marked as out-of-scope in the PRD are absent from the implementation.

B19: No features or functionality mentioned in the PRD as out-of-scope are present in the codebase the reviewer inspected.

## Your Job

Read the actual codebase and verify against the spec above.
You have NO implementation context. Find the code yourself.

**Check for:**

1. **Spec compliance** — Every requirement implemented? Anything
   extra? Requirements misinterpreted?

2. **Security and deployment readiness** — Secrets with empty
   defaults? Missing auth checks? Fail-open paths? Race conditions
   (check-then-act)?

3. **Data safety** — Backward compatibility? Migration paths?
   Malformed/missing data handling?

4. **Missing error paths** — Token expiry, network failure, partial
   writes? Retry and recovery?

**IMPORTANT: If you cannot find implementation files, you MUST still
produce a full report.** Enumerate every spec requirement, flag every
security concern derivable from the spec. "Code not found" is a
Critical finding, not a reason to stop.

OUTPUT FORMAT IS MANDATORY. Follow exactly:
## Agent Output Format (Single Source of Truth)

Each agent outputs issues in this exact format:

```
[{AGENT_NAME}] {emoji} {description} | File: {path or "N/A"} | Task: {id or "general"}
```

**Severity emojis:** 🔴 Critical, 🟠 High, 🟡 Medium, ⚪ Low

**Rules:**
- One issue per line
- Use "N/A" for file if issue is architectural/cross-cutting
- Use "general" for task if issue spans multiple tasks or is a PRD gap
- If zero issues found: `[{AGENT_NAME}] ✅ No issues found`

**Examples:**
```
[ALICE] 🔴 SQL injection in query builder | File: src/db/query.ts | Task: 3
[BOB] 🟠 Missing error handling strategy | File: N/A | Task: general
[CARL] 🟡 PRD section 2.3 not implemented | File: N/A | Task: 5
```

Your agent name is BLAKE.

Cite files repo-relative as path:line (for example skills/work/SKILL.md:166), never absolute and never with a "(lines a-b)" suffix.

PER-RULE VERDICTS ARE MANDATORY. For every rule in The Rubric above, emit one line:
B{n}: pass   or   B{n}: fail
(one rule per line, no other text on the line, no rationale; a rule you
cannot evaluate counts as fail; never omit the line; never renumber).
