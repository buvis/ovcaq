---
default_model: opus
model_tier_rationale: process identity under pid reuse, a ctypes struct reader and a batch-state revert path need judgment; acceptance tests are exact
lane: full
---
# Supervisor process identity and start preflight

Source: [discovery 00004](../../discovery/00004-supervisor-robustness.md), supervisor-start half. Created 2026-10-25. The driver-edge half (failure classification, neutral tier keys) is PRD 00063.

## Overview

### Problem Statement
`process_identity` in src/ovcaq/runtime/registry.py shells out to ps. Where ps is missing or denied (minimal containers, the macOS Seatbelt profile the agent loop runs under) `ovcaq run` dies after `start_batch` has already committed, so `batch.status` stays `running` with no supervisor and `status` reports idle. Verified 2026-10-25 in the sandbox: `process_identity(os.getpid())` raises PermissionError and test_fleet_registry.py fails on it. Route misconfiguration (an unknown tier) is also found only inside the first attempt, after the batch started. `capability retry` with an unknown name raises a KeyError traceback instead of a usage error.

### Target Users
Operators running OVCAQ in sandboxes or minimal images; the unattended autopilot loop, whose full test gate currently fails on the ps call alone.

### Success Metrics
The tests named in Implementation Phases pass. With the `forbid_ps` fixture active, the whole tests/runtime directory passes, so nothing under src/ovcaq spawns ps. `ovcaq doctor --json` lists a `process_identity` capability fact. A preflight failure leaves `state.json` at the same revision.

## Functional Decomposition

### Capability: Process identity

#### Feature: Kernel process identity probe
- **Description**: `process_identity(pid)` reads start time and status through libproc proc_pidinfo with `PROC_PIDTBSDINFO` instead of ps.
- **Inputs**: A pid.
- **Outputs**: `ProcessIdentity(pid, started)` with `started` equal to f"{pbi_start_tvsec}.{pbi_start_tvusec:06d}"; None for pid <= 0, a pid the kernel does not know (zero bytes returned), or a zombie (pbi_status equal to 5, SZOMB).
- **Behavior**: Load libproc through ctypes (find_library "proc"). struct proc_bsdinfo is 136 bytes: pbi_status is the uint32 at offset 4, pbi_pid the uint32 at offset 12, pbi_start_tvsec the uint64 at offset 120, pbi_start_tvusec the uint64 at offset 128 (verified 2026-10-25 against the running process inside the sandbox). A returned size other than 0 or 136, a pbi_pid that differs from the requested pid, a libproc load failure, or a non-darwin platform raises `CommandError` with the new `ErrorCode.PROCESS_PROBE` (value process_probe, exit code 12) and a message that names the platform and tells the operator to run `ovcaq doctor`. Never `state_io`, never a bare OSError, never a subprocess. `process_matches` is unchanged. Linux stays PRD 00013.

#### Feature: Doctor process identity fact
- **Description**: `probe_platform` reports whether the identity probe resolves the current process.
- **Inputs**: The running process.
- **Outputs**: A sixth `CapabilityResult` named `process_identity`: `supported` with the token in the detail when the probe returns an identity, `degraded` with the error text otherwise.
- **Behavior**: `_NAMES` gains `process_identity`; `require_process_capabilities` requires exactly six facts. `ovcaq doctor --json` lists the fact under `capabilities` and reports `ok: false` when it is degraded. Premise: tests/runtime/test_capability.py pins five facts today (`rg -c "exactly_five_facts" tests/runtime/test_capability.py` returns 1); the test is renamed to six, not deleted.

### Capability: Start preflight

#### Feature: Validation before the batch starts
- **Description**: `Supervisor.run` validates its environment and every phase route before `start_batch`.
- **Inputs**: The resolved supervisor settings, the selected driver, the current process.
- **Outputs**: Either a started batch or a typed error with the state revision unchanged.
- **Behavior**: New `Supervisor.preflight()` runs after `require_no_emergency_failure` and before `_reconcile_capabilities` and `start_batch`. It requires `process_identity(os.getpid())` to return an identity, and `resolve_phase_route(root, phase, agent=driver.name, phase_settings=settings.phases[phase])` to succeed for build, review and done. A `ConfigurationError` becomes `CommandError(ErrorCode.USAGE, message)` with the original message; a probe error passes through as process_probe. No transaction runs before preflight passes, so a failure leaves `revision` and `batch.status` untouched and `ovcaq run` exits with the error envelope.

#### Feature: Early failure returns a fresh batch to idle
- **Description**: A failure after `start_batch` but before the first session metric does not leave a running batch with no supervisor.
- **Inputs**: Whether this run moved the batch from idle to running; the failure between `start_batch` and `_open_session`.
- **Outputs**: `batch.status` idle again for a batch this run started; an attention notice for a batch that was already running.
- **Behavior**: New `StateService.revert_batch_start(batch_id, *, expected_revision)` restores `batch.id`, `batch.started_at` and `batch.status` to their `new_state` defaults only when `batch.status` is running, `batch.id` equals `batch_id`, `work.prd` is None and `batch.completed_prds` is empty; any other state raises ValueError. `Supervisor.run` calls it when `_publish_ownership` or the first `_attempt` raises before `_open_session` and the batch was idle when `run` began; otherwise the existing `_state_failure("supervisor.startup")` attention path records the failure. Either way the run exits 1 with the failure detail. "Before `_open_session`" is tracked with an explicit session-opened flag set when `_open_session` returns; `_sessions <= 1` is not the signal, because `_loop` bumps `_sessions` before the first attempt. `_cleanup_ownership_records` catches OSError and ValueError (`FleetRegistry.remove` raises ValueError from `_directory`, `_mutation` and `_verify_root`), so a cleanup failure never blocks the revert.

### Capability: Capability command safety

#### Feature: Unknown capability name is a usage error
- **Description**: `capability retry NAME` for a name absent from `batch.capabilities` returns a usage error envelope.
- **Inputs**: The capability name argument.
- **Outputs**: `CommandError(ErrorCode.USAGE, "unknown capability: NAME")`, exit 1, JSON envelope; no traceback.
- **Behavior**: `CapabilityService.retry` checks membership before `reconcile` touches `batch.capabilities[name]`. Premise, verified 2026-10-25: no production path under src/ovcaq declares a required capability (`rg -n "required=True|\"required\": True" src/ovcaq` matches argparse only), so `run` already never declares a capability `_UnavailableRunner` cannot execute; this PRD pins that fact with a test and changes no runner. If a production declaration exists at execution time, skip the pin and report it.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/errors.py  # Identity
src/ovcaq/runtime/registry.py  # Identity
src/ovcaq/runtime/capability.py  # Identity, Safety
tests/runtime/conftest.py  # Identity
tests/runtime/test_fleet_registry.py  # Identity
tests/runtime/test_capability.py  # Identity
tests/runtime/test_runtime_cli.py  # Identity
src/ovcaq/runtime/supervisor.py  # Preflight
src/ovcaq/state/commands.py  # Preflight
tests/runtime/test_supervisor_preflight.py  # Preflight
tests/state/test_supervisor_commands.py  # Preflight
src/ovcaq/supervisor_cli.py  # Safety
tests/runtime/test_capability_lifecycle.py  # Safety
tests/runtime/test_supervisor_cli.py  # Safety
docs/operations.md  # Identity
docs/state-protocol.md  # Identity
CHANGELOG.md  # Identity
```

### Module: Identity
- **Maps to capability**: Process identity
- **Responsibility**: Resolve process identity from the kernel, expose it as a doctor fact, and name the failure with its own error code.
- **Exports**: `process_identity`, `process_matches`, `ProcessIdentity` (unchanged signatures), `ErrorCode.PROCESS_PROBE`, the `process_identity` capability fact, the `forbid_ps` autouse fixture for tests/runtime.
New symbols: `ErrorCode.PROCESS_PROBE`, `PROC_PIDTBSDINFO`, `forbid_ps`, `tests/runtime/conftest.py`

### Module: Preflight
- **Maps to capability**: Start preflight
- **Responsibility**: Validate before committing a batch; revert a fresh batch the supervisor could not serve.
- **Exports**: `Supervisor.preflight`, `StateService.revert_batch_start`.
New symbols: `Supervisor.preflight`, `StateService.revert_batch_start`, `tests/runtime/test_supervisor_preflight.py`

### Module: Safety
- **Maps to capability**: Capability command safety
- **Responsibility**: Keep capability commands inside the typed error contract.
- **Exports**: `CapabilityService.retry` membership check surfaced by `supervisor_cli._retry` as `usage`.

## Dependency Graph

### Foundation Layer (Phase 0)
No module dependencies; built first. Premise re-check before editing: `process_identity` still spawns ps and `capability retry` still raises KeyError for an unknown name; if either is already fixed, preserve it and report the task satisfied.
- **Identity**: the probe and the error code every other module consumes.

### Core Layer (Phase 1)
- **Preflight**: Depends on Identity (preflight calls the probe; the revert path reuses its typed error).

### Integration Layer (Phase 2)
- **Safety**: Depends on Identity (shares the typed error contract); documentation depends on Identity and Preflight.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Process identity without ps, typed failure, and a suite that proves nothing spawns ps.

**Tasks**:
- [ ] Replace the ps call in `process_identity` with the libproc reader and add `ErrorCode.PROCESS_PROBE` (exit 12) with its remedy message; add the `forbid_ps` autouse fixture in tests/runtime/conftest.py that makes any subprocess spawn whose argv[0] is ps or /bin/ps raise PermissionError. (no deps) — Acceptance: test_process_identity_requires_alive_pid_and_matching_start and test_child_identity_stays_live_until_process_exit pass under `forbid_ps`; new process_probe_unavailable_is_typed asserts that a libproc load failure raises CommandError with code process_probe and exit 12 and that the message names `ovcaq doctor`; new zombie_process_has_no_identity asserts a reaped child returns None.

**Exit Criteria**: tests/runtime/test_fleet_registry.py passes in a sandbox that denies ps.

### Phase 1: Core
**Goal**: Preflight before the batch starts; a fresh batch never stays running without a supervisor.

**Tasks**:
- [ ] Add the `process_identity` doctor fact and widen `require_process_capabilities` to six facts. (depends on: Phase 0) — Acceptance: doctor_reports_process_identity_fact in tests/runtime/test_runtime_cli.py asserts the fact appears and a degraded probe flips ok to false; test_platform_probe_returns_exactly_six_facts_in_a_stable_order replaces the five-fact test after the `rg -c` premise returns 1.
- [ ] Add `Supervisor.preflight()` and call it before `_reconcile_capabilities` and `start_batch`. (depends on: Phase 0) — Acceptance: preflight_rejects_unknown_tier_without_state_change and preflight_rejects_missing_process_identity_without_state_change in tests/runtime/test_supervisor_preflight.py assert the error code, exit code and an unchanged revision; test_run_commits_batch_identity_before_first_metric_and_preserves_work still passes.
- [ ] Add `StateService.revert_batch_start` and the supervisor's early-failure branch. (depends on: Phase 1 task 2) — Acceptance: revert_batch_start_requires_fresh_running_batch in tests/state/test_supervisor_commands.py covers each precondition; early_failure_returns_fresh_batch_to_idle and early_failure_on_resumed_batch_records_attention in tests/runtime/test_supervisor_preflight.py inject a failing `FleetRegistry.publish` and assert idle versus attention plus exit 1.
- [ ] Harden the early-failure revert (review cycle 2 residuals R1, R2, R6; the code from the first pass is on master, this task corrects it). (depends on: Phase 1 task 3) — Acceptance: cleanup_failure_never_blocks_the_revert in tests/runtime/test_supervisor_preflight.py makes `FleetRegistry.publish` and `FleetRegistry.remove` both raise ValueError and asserts the batch still returns to idle with exit 1; failure_after_session_opened_never_reverts raises a `CommandError` from the process-identity probe inside the first `OwnedProcess.spawn`, after `_open_session` returned, and asserts `batch.status` stays running with an attention notice; fleet_entry_written_then_raise_is_removed calls the real fleet publisher before raising and asserts both attempted ownership records disappear while a foreign fleet entry survives.

**Exit Criteria**: The named tests pass; `ovcaq status` after an injected early failure on a fresh project reports an idle batch.

### Phase 2: Integration
**Goal**: Typed capability errors, pinned premise, current documentation.

**Tasks**:
- [ ] Make `CapabilityService.retry` reject an unknown name as a usage error and pin the no-required-capability premise. (depends on: Phase 0) — Acceptance: retry_unknown_capability_is_a_usage_error in tests/runtime/test_supervisor_cli.py asserts the JSON envelope code usage and exit 1 with no traceback text; run_declares_no_required_capability in tests/runtime/test_capability_lifecycle.py asserts a fresh `run` reaches its first session with `batch.capabilities` empty.
- [ ] Document the `process_identity` doctor fact and the process_probe error in docs/operations.md and docs/state-protocol.md; add CHANGELOG.md entries. (depends on: Phase 1) — Acceptance: `rg -n "process_probe" docs/state-protocol.md docs/operations.md CHANGELOG.md` finds all three files; test_live_parser_inventory_and_generated_operations_include_runtime_commands passes.

**Exit Criteria**: The named tests plus `./tools/check` pass in a sandbox that denies ps.

## Test Strategy

### Critical Scenarios
- **Happy path**: test_child_identity_stays_live_until_process_exit under `forbid_ps` → a child's identity is stable while alive, distinct from the parent's, and None after exit, without spawning ps.
- **Edge case**: early_failure_returns_fresh_batch_to_idle → a registry publish failure after `start_batch` leaves `batch.status` idle, no attention, exit 1.
- **Error case**: preflight_rejects_unknown_tier_without_state_change → an unknown tier exits with code usage and the state revision is unchanged.

## Risks

- **Struct layout drift**: pin the 136-byte size and the four offsets as constants, assert pbi_pid equals the requested pid, and test against the running process.
- **Pid reuse between probe and publish**: the token carries microseconds and `process_matches` compares the whole token; a recycled pid never matches.
- **Probe raises where callers expected None**: `FleetRegistry.snapshot` and `status` surface process_probe instead of pruning live entries as dead; this is the intended fail-loud behavior.
