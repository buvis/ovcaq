# OVCAQ event protocol and Claude adapter

Status: backlog | Version: 1 | Umbrella phase: 4 | Created: 2026-08-23

## Overview

### Source Contract

Implements Phase 4 source tasks `P04-T01`–`P04-T09` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

The current runner appears injectable but still owns Claude argv, environment,
models, JSON events, rate limits, and failure parsing. OVCAQ needs a normalized
event contract and a real provider edge before adding a second launcher.

### Target User

The supervisor needs provider-neutral launch/results; the TUI needs normalized
observations; operators need raw evidence preserved when decoding drifts.

### Success Metrics

- A scripted fake Claude session completes through the driver protocol.
- Every raw line is retained before decoding; malformed/unknown lines never
  crash the session reducer.
- Shared runtime and TUI-facing modules contain no Claude/Anthropic parsing or
  model identifiers.
- Exact argv, environment additions, usage, cost, lane, rate-limit, and failure
  behavior pass against sanitized fixtures.

## Preconditions and Boundaries

- Depends on completed PRDs 00002–00005.
- Drivers launch and summarize sessions but never return workflow decisions.
- Provider-native payloads never enter authoritative state.
- Codex behavior is deferred to PRD 00009; generic drivers to public release.

## Functional Decomposition

### Capability: Normalized Observation Protocol

#### Feature: Versioned event model

Define immutable `Observation`, `Usage`, and `SessionSummary` types with
protocol/timestamp/provider/run/session/lane identity, typed activity, and a
closed failure vocabulary: rate-limit, connectivity, permission, authentication,
timeout, agent, and unknown. Required observations cover session start/complete/
fail, activity messages, tool and lane start/progress/complete/fail, usage,
rate-limit start/clear, and `raw.unknown`.

#### Feature: Total reduction and persistence

Decode every raw line to zero or more observations; malformed or unknown input
becomes `raw.unknown`. Usage is monotonic and deduplicated; inferred values carry
`estimated=true`; normalized events redact environment values and likely secrets
while user-only raw evidence remains intact. Events are observational only.

### Capability: Driver Boundary

#### Feature: Launch and health protocol

Define `LaunchRequest`, `LaunchSpec`, `DriverHealth`, and `AgentDriver` methods
for probe, shell-free argv/env/cwd construction, decode, and summarize. Built-ins
register by unique name; entry-point discovery detects duplicates.

#### Feature: Session summary

Reduce observations plus exit code into success, session identity, failure
class/detail, credible rate-limit reset, and usage without choosing the next
workflow phase.

### Capability: Claude Driver

#### Feature: Exact launch contract

Port `claude -p`, unattended permission mode, configured model/effort/fallback,
stream-json/verbose output, prompt invocation, and only `CLAUDE_*` environment
variables behind `drivers/claude.py`; the model resolves through the agent tier
map, and any other environment addition (for example a personal
`WARDEN_UNATTENDED`) comes from per-agent configuration, never from driver
constants. Unattended permissions receive a loud preflight rather than an
implicit global default.

#### Feature: Claude stream decoder

Port message/tool/task/subagent attribution, usage/cost, terminal outcomes,
Anthropic rate-limit and connectivity classification, and unknown fallback from
sanitized current-version fixtures.

## Structural Decomposition

```text
src/ovcaq/
  events/{__init__.py,model.py,reducer.py,tail.py}
  drivers/{__init__.py,base.py,claude.py}
  config.py
tests/
  events/{test_model.py,test_reducer.py}
  drivers/{test_registry.py,test_claude.py,test_neutrality.py}
  fixtures/claude/*.jsonl
docs/driver-protocol.md
```

- `events/model.py`: normalized immutable types and failure vocabulary.
- `events/reducer.py`: total reduction, usage monotonicity, terminal summary.
- `drivers/base.py`: protocols and built-in/entry-point registry.
- `drivers/claude.py`: all Claude launch, decode, and classification behavior.
- `events/tail.py`: provider-neutral normalized-event persistence/tailing.

## Dependency Graph

```text
PRD 00005 raw session substrate -> event model/reducer
event model + driver protocol   -> Claude adapter -> SessionSummary
Claude fixtures                 -> argv/decoder/conformance tests
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Protocols and Reducers

- [ ] Define normalized event, usage, failure, health, launch, and summary types.
- [ ] Implement tolerant reduction, normalized persistence, and raw fallback.
- [ ] Implement built-in and entry-point driver discovery with duplicate checks.

**Exit Criteria**: Protocol tests prove total decoding and provider-neutral data.

### Phase B: Claude Launch and Decoding

- [ ] Characterize and port exact Claude argv/environment construction.
- [ ] Port stream event, task/lane, usage, cost, and terminal decoding.
- [ ] Move rate-limit/connectivity/model handling entirely behind the adapter.
- [ ] Sanitize/version the required Claude fixture matrix.

**Exit Criteria**: Exact fixture/argv tests pass; unknown events degrade safely.

### Phase C: Conformance and Guardrails

- [ ] Run shared driver conformance against scripted fake Claude execution.
- [ ] Persist raw-before-normalized evidence and verify summary results.
- [ ] Add import/string guards for provider-neutral modules.
- [ ] Publish driver/event contracts without promising compatibility yet.

**Exit Criteria**: Fake Claude completes one adapter session and no shared module
contains provider parsing.

## Test Strategy

- Healthy, tool-active, lane/subagent, rate-limited, connectivity-failed,
  permission-failed, terminal-failed, malformed, and unknown Claude JSONL.
- Exact argv/env/cwd/stdin and configured model/effort/fallback behavior.
- Raw byte preservation before decoder invocation.
- Usage monotonicity/deduplication, cost availability, and estimation markers.
- Normalized redaction versus byte-identical user-only raw evidence.
- Session identity, terminal classification, and TERM/KILL response.
- Duplicate driver registration and provider-neutral import/string scans.

## Risks

- **Event drift**: Preserve raw evidence and make decode total.
- **False neutrality**: Enforce forbidden imports/strings in shared modules.
- **Usage double count**: Deduplicate by provider identity and test monotonicity.
- **Premature protocol stability**: Version the protocol but defer compatibility
  guarantees until public release.

## Acceptance Criteria

- [ ] Fake Claude runs through `AgentDriver` and produces `SessionSummary`.
- [ ] Raw and normalized evidence satisfy ordering and permission contracts.
- [ ] Required Claude fixture/argv/conformance tests pass.
- [ ] Unknown input yields observable raw fallback, never a decoder crash.
- [ ] Shared runtime/TUI-facing modules are provider-neutral.
- [ ] PRD 00007 can decide solely from state plus `SessionSummary`.

## Unresolved Questions

None.
