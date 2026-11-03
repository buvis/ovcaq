---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: d797236ac1cd
source_prd: 00005-runtime-substrate-v1.md
severity: critical
---

# Triage: apply_purge opens the original runtime directory but acquires run.lock and re...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `1`, consensus `[1/3]`, raised against `00005-runtime-substrate-v1.md`.

Issue: apply_purge opens the original runtime directory but acquires run.lock and retention.lock through its replaceable pathname; swapping that directory lets purge delete active evidence while the original run.lock remains held.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `dev/local/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `d797236ac1cd`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `dev/local/prds/hold/`
- **Responsibility**: hold ledger key `d797236ac1cd` from `00005-runtime-substrate-v1.md` until a human triages it
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
