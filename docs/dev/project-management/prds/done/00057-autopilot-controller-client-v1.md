---
default_model: opus
model_tier_rationale: Cross-process contracts, extraction equivalence and concurrency require judgment.
lane: full
rework_cap: 3
catchup: force
---
# OVCAQ external workflow-controller client

Source: [three-layer design](../../designs/autopilot-optional-supervision.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
OVCAQ currently imports workflow state services. It needs a tested external controller protocol client before authority can move.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
controller_contract_fixtures → client accepts canonical producer fixtures.. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Client

#### Feature: Consume controller Contract A
- **Description**: Implement typed transport with no workflow policy.
- **Inputs**: Explicit controller argv, [workflow].actor_file credential path and pinned schema/fixture bundle.
- **Outputs**: Negotiation, snapshots, typed apply responses and external provenance.
- **Behavior**: Read Contract A from canonical design. Validate producer identity/digests, protocol-major and capabilities. No Python imports from plugin cache, shell evaluation or executable auto-discovery. Bound subprocess output and timeout; redact actor secrets; preserve request identity on retry, never invent acceptance from stdout prose. This PRD does not activate a second state authority.

### Capability: Prerequisites

#### Feature: Read-only dependency checks
- **Description**: Gate consumers on exact local and external evidence.
- **Inputs**: PRD ID, local done bucket, workflow config and explicit artifact paths.
- **Outputs**: Exit 0 ready or 1 unavailable with JSON diagnostics.
- **Behavior**: Create tools/autopilot-prerequisites. Graph: 58 needs 57+62 and controller core/jobs/reviews/records; 59 needs 58+63; 60 needs 59; 61 needs 60 and [autopilot].plugin_artifact with AP17 evidence; 64 needs 58; 65 needs 60+61+64 and [operator].client_artifact with Lantern03 evidence. Bound probes and validate provenance. Never fetch/write. Unknown IDs or missing config fail.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/workflow_client.py
src/ovcaq/config.py
src/ovcaq/cli.py
tests/workflow_client/test_transport.py
tests/workflow_client/test_contract_conformance.py
tests/workflow_client/test_controller_boundary.py
tests/workflow_client/test_contract.py
tests/workflow_client/test_kill_group_bounded.py
tests/workflow_client/test_apply_outcome_unknown.py
tests/workflow_client/test_actor_secret_redaction.py
tests/fixtures/workflow/controller-v1.json
tools/autopilot-prerequisites
tests/workflow_client/test_prerequisites.py
docs/operations.md
CHANGELOG.md
```

### Module: Client
- **Maps to capability**: Client
- **Responsibility**: Implement typed transport with no workflow policy.
- **Exports**: Negotiation, snapshots, typed apply responses and external provenance.
New symbols: `src/ovcaq/workflow_client.py`, `tests/workflow_client/test_transport.py`, `tests/workflow_client/test_contract.py`, `tests/fixtures/workflow/controller-v1.json`

### Module: Prerequisites
- **Maps to capability**: Prerequisites
- **Responsibility**: Gate consumers on exact local and external evidence.
- **Exports**: Exit 0 ready or 1 unavailable with JSON diagnostics.
New symbols: `tools/autopilot-prerequisites`, `tests/workflow_client/test_prerequisites.py`

## Dependency Graph

### Foundation Layer (Phase 0)
AP 00018 exported bundle required through [workflow].contract_bundle; this PRD defines a read-only Phase 0 precondition rather than a self-dependent eligibility helper. A fake executable suffices; no functioning Autopilot/controller runtime is required yet. Current writer seam: src/ovcaq/state/store.py:126. Recheck source after predecessor merges; that citation describes the pre-extraction implementation. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.

### Core Layer (Phase 1)
- **Client**: Depends on Phase 0 and the explicit task order below.
- **Prerequisites**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Client and Prerequisites.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Freeze imported producer bundle/provenance and request mapping. (depends on: declared prerequisites) — Acceptance: controller_bundle_digest rejects mismatched artifacts; recheck existing config/API ownership.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Implement argv transport, capability negotiation and typed errors. (depends on: Phase 0) — Acceptance: controller_timeout, output_bound, lost_ack_preserved and incompatible_major refuse safely.
- [ ] Implement the exact prerequisite dependency table and artifact probes. (depends on: Phase 1 task 1) — Acceptance: missing_artifact and unknown_prd fail without fetch/write; predecessor checks never accept backlog files.

The four tasks below are the review cycle 3 residuals (R2 to R7). The first-pass code is on master; these tasks correct it.

- [ ] Bound `_run` cleanup end to end (R2). (depends on: Phase 1 task 1) — Acceptance: run_with_detached_descendant_times_out_within_bound in tests/workflow_client/test_kill_group_bounded.py uses a fake controller that exits at once but leaves a `start_new_session=True` descendant holding stdout and stderr open for 8 s, sets `timeout_seconds=1`, and asserts `_run("contract")` raises `ControllerTimeoutError` in under 3 s; `_run` no longer exits through `with process:` (close the pipes without joining the readers, reap with a bounded wait).
- [ ] Classify post-spawn abnormal exits as unknown outcome (R4, R7). (depends on: Phase 1 task 1) — Acceptance: apply_nonzero_exit_after_spawn_is_outcome_unknown in tests/workflow_client/test_apply_outcome_unknown.py terminates a fake controller after it commits and before it acks and asserts `ApplyOutcomeUnknownError` with the request identity preserved for the retry; a launch failure (`FileNotFoundError` or `PermissionError` from `Popen`) stays a plain `ControllerError`; `ApplyOutcomeUnknownError` derives from `ControllerError`, not `ControllerTimeoutError`, its docstring names every trigger (timeout, output overrun, non-JSON or non-dict response, post-spawn non-zero exit), and timeout_base_does_not_catch_unknown_outcome asserts `except ControllerTimeoutError` lets an output-overrun `ApplyOutcomeUnknownError` through.
- [ ] Keep the actor file opaque in redaction (R5). (depends on: Phase 1 task 1) — Acceptance: redaction_never_reads_actor_file in tests/workflow_client/test_actor_secret_redaction.py monkeypatches `Path.read_bytes` and `open` to raise and asserts `_redact` still returns; a secret shorter than `MIN_SECRET_CHARS` and an unreadable actor file both yield a redacted diagnostic, never the raw controller output; test_redact_with_unreadable_actor_file_does_not_raise is replaced by a test that fails against the disclosing code.
- [ ] One digest definition for `contract_bundle_sha256` and strict bundle validation (R3, R6). (depends on: Phase 1 task 2) — Acceptance: prerequisites_and_client_share_one_digest in tests/workflow_client/test_prerequisites.py pins the real tests/fixtures/workflow/controller-v1.json with one configured sha256 of the raw file bytes and asserts both `tools/autopilot-prerequisites --prd 58` (with 57 and 62 staged in a temporary done bucket) and `controller_settings` accept it, so `_bundle_digest` hashes raw bytes, not canonical JSON; bundle_rejects_non_contract_json asserts `null`, `{}` and a bundle missing `protocol_major`, `operations` or `capabilities` fail the tool with a named reason; docs/operations.md documents the key and the raw-bytes digest in the client section, and the generator's `CONTROLLER_CLIENT_NOTES` is updated so render_command_reference() parity holds.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Run transport conformance against fake controller and document explicit configuration. (depends on: Phase 1) — Acceptance: no_plugin_import and controller_contract_fixtures pass with no adjacent checkout or installed upper-layer UI.

**Exit Criteria**: Named integration scenarios and `./tools/check` pass. Generated CLI documentation matches the parser; no hold is released.

## Test Strategy

### Critical Scenarios
- **Happy path**: controller_contract_fixtures → client accepts canonical producer fixtures.
- **Edge case**: lost_ack_preserved → retries retain the identical request.
- **Error case**: no_plugin_import → runtime cannot load plugin Python into its process.

## Risks

- Imported schema copies are not authoritative.
- Lifecycle entry gaps previously assigned here now belong to AP00019; retain discovery00003/cf8be72 coverage there.
