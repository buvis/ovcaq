# OVCAQ Codex adapter

Status: backlog | Version: 1 | Umbrella phase: 7 | Created: 2026-08-23

## Overview

### Source Contract

Implements Phase 7 source tasks `P07-T01`–`P07-T07` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

OVCAQ has a provider-neutral seam only after a genuinely different launcher can
use it without supervisor or TUI branches. Codex must run the same state-led
workflow through `codex exec --json` using fixture/fake evidence before any
launcher-global plugin mutation.

### Target User

The repository owner needs Codex as a first-party personal-cutover launcher;
shared runtime/TUI consumers need equivalent normalized behavior where Codex
exposes it and explicit unknowns where it does not.

### Success Metrics

- Fixture/fake Codex drains build/review/done through shared conformance suites.
- Exact installed-version argv, prompt, JSONL, and state-handoff contracts pass.
- The supervisor contains zero Codex-specific branches.
- TUI shows Codex identity/activity/usage and honest raw fallback.
- No test or implementation mutates launcher-global plugin state.

## Preconditions and Boundaries

- Depends on completed PRDs 00002–00008.
- Uses the PRD 00006 driver/event protocols unchanged or records a protocol fix
  that also passes Claude conformance.
- This PRD is fixture/fake-only; real plugin provisioning and smoke are PRD 00010.
- Unsupported cost/telemetry stays unknown; no fabricated estimates.

## Functional Decomposition

### Capability: Codex Launch Contract

#### Feature: Exact shell-free argv

Build argv with global `--ask-for-approval never` before `exec`, then `--json`,
`--sandbox workspace-write`, `-C <repo>`, optional configured model, and prompt.
Validate exact flags against the installed CLI version captured with fixtures.
The configured model resolves through the agent tier map; the neutral effort
scale maps to the Codex reasoning-effort configuration override, and an
unmappable effort logs a warning rather than being dropped silently.

#### Feature: State-only handoff prompt

Invoke the installed Codex autopilot skill by provider-native syntax; require
OVCAQ state/workflow commands, exactly one successful phase handoff, and session
exit. Do not embed plugin files or direct `state.json` editing instructions.

### Capability: Codex Event and Failure Adapter

#### Feature: Installed-version JSONL decoding

Decode actual thread, turn, agent message, reasoning, command, file change, MCP,
web, plan, usage, and error items into normalized observations. Malformed and
new items degrade to `raw.unknown`.

#### Feature: Health and failure summary

Probe binary/version/auth and classify Codex-specific authentication,
permission, rate-limit, connectivity, timeout, agent, and unknown outcomes into
the shared failure vocabulary.

### Capability: Shared Conformance

#### Feature: Workflow and decision parity

Run the same driver, decision, state-handoff, process-signal, and raw-evidence
suites used by Claude through a scripted fake Codex executable.

#### Feature: Provider-neutral presentation

Verify TUI/provider models show available activity and usage, omit unavailable
cost, label estimates, and retain raw-only visibility.

## Structural Decomposition

```text
src/ovcaq/drivers/codex.py
src/ovcaq/config.py
tests/drivers/test_codex.py
tests/drivers/test_conformance.py
tests/fixtures/codex/*.jsonl
tests/runtime/test_codex_decisions.py
tests/tui/test_codex_projection.py
docs/driver-protocol.md
```

- `drivers/codex.py`: Codex probe, argv, prompt, decoder, and summary only.
- Shared runtime/events/TUI modules may change only for provider-neutral fixes
  covered by both adapters.
- Fixtures record installed Codex version and sanitized provenance, marking
  each family captured live or synthesized from the documented event schema
  when live capture is impractical (rate-limited, permission-failed).

## Dependency Graph

```text
PRD 00006 protocols + PRD 00007 decisions + PRD 00008 projections
  -> Codex fixtures -> Codex adapter -> shared conformance
                                  -> fake workflow drain
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Fixtures and Launch Contract

- [ ] Capture/sanitize/version healthy, tool-active, subagent/lane,
  rate-limited, connectivity-failed, permission-failed, and malformed JSONL
  fixture families, recording explicit unknowns where Codex lacks a native kind.
- [ ] Implement exact global/exec argv ordering, sandbox, cwd, model, and prompt.
- [ ] Test state-only handoff language without provisioning external content.

**Exit Criteria**: Exact argv/prompt tests pass against installed-version help and
fixtures.

### Phase B: Decoder and Failure Classification

- [ ] Decode all observed event/item kinds into normalized observations.
- [ ] Implement usage semantics and explicit unknown cost.
- [ ] Implement auth/rate-limit/connectivity/permission/failure classification.
- [ ] Prove malformed/unknown input never crashes reduction.

**Exit Criteria**: Fixture matrix produces expected observations and summaries.

### Phase C: End-to-End Fake Conformance

- [ ] Run shared driver/process/decision suites for Codex.
- [ ] Drain build/review/done through fake execution and committed handoffs.
- [ ] Verify TUI identity/activity/usage/raw fallback.
- [ ] Assert supervisor/runtime contain no Codex-specific branch or parser.

**Exit Criteria**: Codex passes shared conformance without global plugin mutation.

## Test Strategy

- Exact argv order, environment additions, cwd, stdin, model, and prompt.
- Healthy/tool-active/subagent-or-lane/rate-limited/connectivity/permission and
  malformed fixtures covering thread/turn/tool/file/MCP/web/plan/usage/error.
- Auth, permission, rate-limit with/without reset, connectivity, timeout, death.
- Raw-before-decode evidence and TERM/KILL response.
- Productive state plus noisy exit and untouched state plus success prose.
- TUI available/unknown telemetry semantics and provider-neutral scans.

## Risks

- **CLI drift**: Pin fixture provenance and validate current installed help.
- **False feature parity**: Unknown telemetry stays explicit, never invented.
- **Leaky abstraction**: Shared fixes must pass Claude and neutrality tests.
- **Premature real smoke**: Defer launcher mutation until PRD 00010.

## Acceptance Criteria

- [ ] Fixture/fake Codex drains build/review/done through shared runtime.
- [ ] Exact argv, decoder, prompt, and state-handoff contracts pass.
- [ ] Raw/unknown behavior and failure classifications are total.
- [ ] TUI displays Codex without assuming cost or Claude-native fields.
- [ ] Supervisor has zero Codex-specific branches.
- [ ] PRD 00010 can provision and run the first real Codex smoke.

## Unresolved Questions

None.
