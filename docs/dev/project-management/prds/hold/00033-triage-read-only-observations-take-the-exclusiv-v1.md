---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: f0b3aab7ebc2
source_prd: 00005-runtime-substrate-v1.md
severity: high
---

# Triage: Read-only observations take the exclusive run lock (`_run_health` via `RunLoc...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `1`, consensus `[1/3]`, raised against `00005-runtime-substrate-v1.md`.

Issue: Read-only observations take the exclusive run lock (`_run_health` via `RunLock.acquire`, `_active_session_id` via `flock LOCK_EX|LOCK_NB`, plus `plan_purge` in doctor); a supervisor starting inside that window is refused as a duplicate; TUI polling widens it

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `dev/local/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `f0b3aab7ebc2`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `dev/local/prds/hold/`
- **Responsibility**: hold ledger key `f0b3aab7ebc2` from `00005-runtime-substrate-v1.md` until a human triages it
- **Exports**: none

### Dependencies
- triage: No dependencies (foundation)

## Tasks

### Phase 0: Foundation
- [ ] triage: promote to backlog or close - Acceptance: this file is no longer under dev/local/prds/hold/

### Phase 1: Core
No implementation tasks until attended triage.

## Success Criteria

- This file is no longer under `dev/local/prds/hold/`.
