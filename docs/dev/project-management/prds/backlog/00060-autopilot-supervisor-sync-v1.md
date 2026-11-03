---
default_model: opus
model_tier_rationale: Cross-process contracts, extraction equivalence and concurrency require judgment.
lane: full
rework_cap: 3
catchup: force
eligibility: python3 tools/autopilot-prerequisites --prd 00060
---
# OVCAQ headless supervision and controller reconciliation

Source: [three-layer design](../../designs/autopilot-optional-supervision.md). Revised 2026-10-25. Planning only; no publication, live installation, source retirement or hold activation.

## Overview

### Problem Statement
Controller claims and OS process starts can fail independently. Headless execution must recover without duplicate agents or fabricated workflow completion.

### Target Users
Users running Autopilot independently or through headless OVCAQ, and maintainers verifying the layer boundary.

### Success Metrics
headless_mixed_driver_drain → supervised lifecycle completes through the same controller.. Named edge/error scenarios must also pass; real-host support requires separate probe evidence.

## Functional Decomposition

### Capability: Supervision

#### Feature: Controller-driven session lifecycle
- **Description**: Drive fresh sessions from committed job plans.
- **Inputs**: Controller claims, execution journal and normalized session events.
- **Outputs**: Bounded agent launches, result reporting and continuation.
- **Behavior**: Acquire controller owner lease; persist launch intent; claim job; launch; report exit/evidence idempotently; request controller acceptance and record commit. Override spoofed inherited bindings after driver env construction. Invalidate credentials on exit. Never derive completion from final text or successful exit. Records.commit is controller-owned; no git record writer in core.

Required real-host certification uses OV 00059's Codex + Gemini routes: Codex builds, Gemini supplies the independent doubt voice, and every controller-required role retains fresh isolation. Prove build, review, rework, completion, records, next-PRD continuation and final drain with Claude executables/configuration/credentials and source/author-home runtime resources inaccessible. Keep required Codex/Gemini authentication isolated. Export exact controller/plugin/driver versions/digests and provider/model/session/input/code evidence for AP 00017. No Claude fallback; unavailable stays incomplete for certification while fake-host protocol tests remain independently runnable.

#### Feature: Agoge push hold around final QA
- **Description**: OVCAQ holds pushes into the Project while it runs the final agoge product-QA pass, and releases the hold only after it has checked the repository itself. Carried over from the frozen claude-autopilot hold PRD 00371 (requirements only) through the AP port ownership map: the loop's arm, run and settle belong to supervision (source loop rows R13/R14); the pre-push guard belongs to the plugin (AP 00014 `custody_push_denied`, inventory UTIL-042/R16).
- **Inputs**: Project root, batch id, agoge log path, the execution journal.
- **Outputs**: The hold file `<autopilot dir>/agoge-hold` and a status of `released`, `changed`, `unverified` or `unarmed`.
- **Behavior**: Before launching agoge, write one `running` entry (`op_id` `agoge-<batch>`, `kind` `agoge`, `repo_root`, `batch`, `status`, `since`, `log`, `hold`) to `{"entries": [...]}` through an atomic write under a lock; this file shape is the contract AP 00014's guard reads, and OVCAQ never claims to enforce a push itself. A hold that cannot be written means no agoge run (`unarmed`). After the run, whatever its exit code, take a fresh snapshot and compare it with the pre-run one: HEAD, refs (ignoring `refs/heads/agoge/`), a hash of local git config, worktree list, a hash of the index, and tracked status (ignoring agoge's profile paths). Every git call uses `--no-optional-locks`, and every path and refname is decoded as filesystem bytes (compare agoge PRD 00006). No change: remove the entry, `released`. Any change, a comparison that cannot run, an undecodable value, or an interrupted run (the `running` entry stays) keeps the hold and notifies the Supervisor; only the Supervisor clears a kept hold, and OVCAQ never runs a restore command. The comparison is OVCAQ's own check and does not depend on the agoge version: an agoge sidecar `target_integrity` of `changed` or `unknown` adds a change, and a missing or older sidecar adds nothing and never releases a hold the comparison kept.

### Capability: Recovery

#### Feature: Reconcile split failure boundaries
- **Description**: Recover process ownership and pending controller effects.
- **Inputs**: Persisted intent, exact process identity, controller epoch and raw results.
- **Outputs**: Safe reattach/termination/reissue or actionable attention.
- **Behavior**: Test crash before/after intent, claim, spawn, exit report and acknowledgement. No exactly-once spawn claim. Reissue only after previous process identity/claim is reconciled. Controller outage prevents new scheduling/advance; stopping owned processes remains available and pending outcomes reconcile later. Preserve bounded retry/rate-limit/park/drain/agoge behavior and source loop rows R13/R14.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/runtime/supervisor.py
src/ovcaq/runtime/session.py
src/ovcaq/runtime/decision.py
src/ovcaq/supervisor_cli.py
tests/runtime/test_controller_supervision.py
src/ovcaq/runtime/reconciliation.py
src/ovcaq/runtime/execution_store.py
src/ovcaq/runtime/registry.py
src/ovcaq/runtime/agoge_hold.py
tests/runtime/test_agoge_hold.py
tests/runtime/test_launch_reconciliation.py
tests/runtime/test_controller_outage.py
docs/operations.md
CHANGELOG.md
```

### Module: Supervision
- **Maps to capability**: Supervision
- **Responsibility**: Drive fresh sessions from committed job plans.
- **Exports**: Bounded agent launches, result reporting and continuation.
New symbols: `tests/runtime/test_controller_supervision.py`, `src/ovcaq/runtime/agoge_hold.py`, `tests/runtime/test_agoge_hold.py`

### Module: Recovery
- **Maps to capability**: Recovery
- **Responsibility**: Recover process ownership and pending controller effects.
- **Exports**: Safe reattach/termination/reissue or actionable attention.
New symbols: `src/ovcaq/runtime/reconciliation.py`, `src/ovcaq/runtime/execution_store.py`, `tests/runtime/test_launch_reconciliation.py`, `tests/runtime/test_controller_outage.py`

## Dependency Graph

### Foundation Layer (Phase 0)
OV 00059 completed (therefore 00058,00062,00063); compatible installed controller. AP00016 plugin integration is optional for synthetic-host tests, required for final real-host readiness. Current writer seam: src/ovcaq/state/store.py:126. Recheck source after predecessor merges; that citation describes the pre-extraction implementation. All workflow, process and git tests use temporary roots; never the implementation batch's state. These interfaces are chosen design requirements, not claims that they already exist.
- **Characterization/contracts**: Depends on the prerequisites above.
- **Push-guard boundary**: the agoge hold file shape is shared with AP 00014, which owns the plugin guard that reads it (`custody_push_denied` extended to hold entries). This PRD writes and settles the hold and tests it with a fake guard reader; the real guard's denial is AP 00014's acceptance, and a missing guard is reported as an unmet dependency, never as enforced protection. The frozen claude-autopilot PRD 00371 is requirements-only input and is not edited.

### Core Layer (Phase 1)
- **Supervision**: Depends on Phase 0 and the explicit task order below.
- **Recovery**: Depends on Phase 0 and the explicit task order below.

### Integration Layer (Phase 2)
- **Installed evidence and documentation**: Depends on Supervision and Recovery.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Characterize premises and freeze inputs.

**Tasks**:
- [ ] Characterize source supervision/limit/drain behavior and freeze crash matrix. (depends on: declared prerequisites) — Acceptance: supervisor_source_parity and crash_boundary_matrix cover every intent/claim/spawn/report boundary; recheck current fixes.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 1: Core
**Goal**: Implement the declared ownership boundary.

**Tasks**:
- [ ] Wire job claims, launch binding and controller acceptance/record calls. (depends on: Phase 0) — Acceptance: fresh_phase_handoff, forged_binding_overridden and record_failure_no_phase_replay enforce authority.
- [ ] Implement the agoge push hold (arm, snapshot/compare, settle) in `src/ovcaq/runtime/agoge_hold.py` and wire it around the final QA launch. (depends on: Phase 1 task 1) — Acceptance: agoge_hold_armed_during_run, agoge_hold_released_when_unchanged, agoge_hold_kept_on_repo_change, agoge_hold_kept_on_failed_comparison, agoge_hold_kept_after_interrupted_run, agoge_hold_independent_of_agoge_version and agoge_hold_undecodable_path_kept run against real temporary repositories (tag, moved remote-tracking ref, staged change, config change, added worktree each keep the hold; a new `refs/heads/agoge/` branch, a changed profile and a new report file do not; an arm failure launches nothing; no restore command is ever executed).
- [ ] Implement restart/outage reconciliation with real process identities. (depends on: Phase 1 task 1) — Acceptance: no_duplicate_active_job, stale_epoch_rejected and stop_during_controller_outage use real subprocesses.

**Exit Criteria**: Named task scenarios pass. Recheck observed-state premises; preserve already-satisfied behavior, skip and report conflicting edits.

### Phase 2: Integration
**Goal**: Prove installed behavior and record evidence.

**Tasks**:
- [ ] Run mixed-driver fake-host fresh workflow through rework/drain and preserve required agoge semantics; separately run the opt-in real Codex + Gemini canary. (depends on: Phase 1) — Acceptance: headless_mixed_driver_drain and controller_receipt_replay prove protocol readiness; codex_gemini_managed proves the complete real lifecycle with installed artifacts and temporary state, or records unavailable without issuing a passed certificate. Ordinary CI needs no provider credentials.

**Exit Criteria**: Named integration scenarios and `./tools/check` pass. Generated CLI documentation matches the parser; no hold is released.

## Test Strategy

### Critical Scenarios
- **Happy path**: headless_mixed_driver_drain → supervised lifecycle completes through the same controller.
- **Edge case**: stop_during_controller_outage → owned processes stop while reconciliation remains visible.
- **Error case**: no_duplicate_active_job → crash recovery cannot launch a second live owner.
- **Error case**: agoge_hold_kept_after_interrupted_run → a killed final QA leaves the `running` entry and the hold stays.
- **Edge case**: agoge_hold_independent_of_agoge_version → an agoge without the integrity sidecar (or an older one) that tags the repo still keeps the hold.

## Risks

- Controller availability gates new work but must not prevent emergency process cleanup.
- API/UI consumers receive revision-tagged observations; cached state never authorizes transitions.
- Pushes from the operator's own terminal are seen by no host hook; the hold's notification is the only signal there (a git pre-push hook is out of scope, as in 00371).
- The hold compares status letters and ignores untracked files; agoge's content-hashing sidecar is extra evidence, not a substitute.
