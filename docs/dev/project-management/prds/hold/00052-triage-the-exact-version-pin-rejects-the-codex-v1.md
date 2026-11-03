---
catchup: skip
design: skip
default_model: opus
model_tier_rationale: tagged-source equivalence and subprocess capture deadlines require judgment
ledger: deferred/202609062243-deferred.json
ledger_key: 21aaa03cb5e2
source_prd: 00009-codex-adapter-v1.md
severity: high
---

# Refresh the reviewed Codex launcher contract

## Overview

### Problem Statement

Review R8: the exact 0.160.0 guard rejects installed 0.160.1 and blocks 00010
preflight. The guard is intentional; its evidence needs refreshing. R17: no test
pins actual per-stream capture bounds. Sources: [discovery 00001](../../discovery/00001-ovcaq-v1.md),
[accepted design](../../designs/00009-codex-adapter-v1-design.md), [review R8/R17](../../reviews/00009-codex-adapter-v1-review-2.md),
[bounded evidence](../../autopilot/reports/version-policy-20261007.md).

### Target Users

The operator preparing Codex provisioning under PRD 00010.

### Success Metrics

Verified exact 0.160.1 passes fake authenticated preflight; unreviewed versions
fail before auth. Historical evidence remains truthful. Each returned probe
buffer stays <=16 KiB under oversized real offline subprocess output.

## Functional Decomposition

### Capability: Reviewed launcher compatibility

#### Feature: Fail-closed characterization

- **Description**: Verify installed contract before changing its guard.
- **Inputs**: Installed read-only version/help and official tagged sources.
- **Outputs**: Separate reviewed-0.160.1 captures, source snapshots/hashes and compatibility record.
- **Behavior**: Verify global `--ask-for-approval never`, `exec --json`, `--sandbox workspace-write`,
  `-C`, `-m`, `-c`, literal `--` prompt handling, exec schema and JSONL producer.
  Compare both tags' `codex-rs/exec/src/{cli.rs,exec_events.rs,event_processor_with_jsonl_output.rs}`
  plus defining shared CLI options source. Release notes alone are insufficient.
  Missing/incompatible evidence stops repair without changing the guard.

#### Feature: Exact reviewed-version refresh

- **Description**: Permit only newly reviewed 0.160.1.
- **Inputs**: Successful characterization; current driver/fake probe contract.
- **Outputs**: `_PINNED_VERSION = "0.160.1"`, fake default and evidence links.
- **Behavior**: Retain exact first-line comparison and refresh remediation.
  Reject 0.160.0, 0.160.2, prereleases, suffixes, aliases and malformed versions.
  Preserve original v1 0.160.0 captures/provenance/timestamps/JSONL family hashes;
  new provenance records revalidation of schema-synthetic families, never live capture.

### Capability: Bounded health evidence

#### Feature: Probe stream-cap regression

- **Description**: Pin existing 16 KiB per-stream capture limit.
- **Inputs**: Real offline subprocesses producing oversized stdout and stderr.
- **Outputs**: Tests of helper-returned buffers, exit status and diagnostics.
- **Behavior**: Each returned buffer stays <=16 KiB while both pipes drain;
  retain five-second deadline and stdin closure. Test version and auth operations.
  Preserve existing sanitized diagnostic coverage; do not add another runner.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/drivers/codex.py                    # exact guard and probe helper
tests/fixtures/codex/v1/                      # historical evidence and fake launcher
tests/fixtures/codex/reviewed-0.160.1/         # new captures, sources, provenance
tests/drivers/test_codex_fixtures.py           # historical evidence integrity
tests/drivers/test_codex_contract_refresh.py   # new evidence checks
tests/drivers/test_codex_rework_probe.py       # existing diagnostics/version tests
tests/drivers/test_codex_failures.py           # fake probe/auth expectations
tests/drivers/test_codex_fake.py               # fake default version expectations
tests/drivers/test_codex_probe_capture.py      # actual per-stream cap assertions
docs/driver-protocol.md                       # current/historical pin distinction
tests/fixtures/README.md                      # evidence pointers
CHANGELOG.md                                 # reviewed version change
```

### Module: Contract evidence

- **Maps to capability**: Reviewed launcher compatibility.
- **Responsibility**: Preserve history and establish the new exact contract.
- **Exports**: Reviewed artifacts and offline integrity tests.

### Module: Codex health adapter

- **Maps to capability**: Reviewed launcher compatibility; bounded health evidence.
- **Responsibility**: Exact guarded preflight and bounded read-only probes.
- **Exports**: Existing `CodexDriver.probe()` and `_run_probe_command`; no new public API.

## Dependency Graph

### Foundation Layer (Phase 0)

- **Contract evidence**: No dependencies; establishes compatibility premise.

### Core Layer (Phase 1)

- **Codex health adapter**: Depends on [Contract evidence].
- **Probe capture tests**: Depend on existing adapter; independent of pin change.

### Integration Layer (Phase 2)

- **Documentation and replay**: Depend on [Contract evidence, Codex health adapter].

## Implementation Phases

### Phase 0: Foundation

**Goal**: Verify 0.160.1 without relabeling historical evidence.

**Tasks**:
- [ ] Characterize both tags and installed `mise exec -- codex --version`, `--help`,
  `exec --help` (no deps). Premise: installed exact 0.160.1 is compatible; re-check
  at execution. Missing/incompatible evidence means skip pin edits, report blocker,
  leave repair incomplete. Acceptance: `mise exec -- uv run pytest tests/drivers/test_codex_contract_refresh.py`
  verifies nonempty captures, exact version, required flags, tagged source hashes,
  explicit schema/producer compatibility review and unchanged historical family hashes.

**Exit Criteria**: Source-backed compatible 0.160.1 record exists; otherwise stop fail-closed.

### Phase 1: Core

**Goal**: Refresh exact guard and prove bounded capture.
**Tasks**:
- [ ] Set exact pin/fake default to 0.160.1; refresh expectations (depends on: Phase 0).
  Acceptance: `mise exec -- uv run pytest tests/drivers/test_codex_rework_probe.py tests/drivers/test_codex_failures.py tests/drivers/test_codex_fake.py tests/drivers/test_codex_contract_refresh.py`
  passes exact supported version/fake auth; rejects old/future/suffixed versions before auth.
- [ ] Add direct helper-buffer cap regressions (depends on: existing probe helper).
  Acceptance: `mise exec -- uv run pytest tests/drivers/test_codex_probe_capture.py`
  asserts buffers <=16384 bytes for larger stdout/stderr in version/auth subprocesses,
  both pipes drained and deadline preserved; removing capture slicing fails tests.

**Exit Criteria**: Exact policy and actual buffer bounds are covered offline.

### Phase 2: Integration

**Goal**: Publish truthful evidence and preserve launch/normalization behavior.
**Tasks**:
- [ ] Update driver protocol, fixture README and changelog for current/historical pins (depends on: Phase 1).
  Acceptance: `mise exec -- uv run pytest tests/drivers/test_codex_fixtures.py tests/drivers/test_codex_launch.py tests/drivers/test_codex_decode.py tests/runtime/test_rework_health.py`
  passes; original captures unchanged and new JSONL provenance remains schema-synthetic.

**Exit Criteria**: `mise exec -- uv sync --all-groups`, `mise exec -- uv run pytest`, `mise exec -- uv run ruff check .`,
`mise exec -- uv run ruff format --check .`, `mise exec -- uv run mypy src/ovcaq`,
and `mise exec -- uv build` pass. Mandatory fresh-session full-lane reviews remain;
exclude optional Carl via runner scope without changing mandatory review lenses.

## Test Strategy

### Critical Scenarios

- **Happy path**: Exact reviewed 0.160.1 + fake auth → healthy; existing matrix replays.
- **Edge case**: Both pipes exceed cap → independently bounded buffers without deadlock.
- **Error case**: Unverified evidence or version drift → no guard refresh/no launch.

## Risks

- **Evidence drift**: Re-check at execution; keep historical provenance separately.
- **Scope creep**: No inference, login mutation, installs, state edits or provisioning;
  00010 owns reconciliation, explicit apply, releases and first real smoke.

Unresolved questions: None; unavailable compatibility evidence is a blocking outcome.
