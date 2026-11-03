---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: aad0050932ea
source_prd: 00005-runtime-substrate-v1.md
severity: high
---

# Triage: Session publication checks paths and then reopens them by pathname, so parent...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `1`, consensus `[1/3]`, raised against `00005-runtime-substrate-v1.md`.

Issue: Session publication checks paths and then reopens them by pathname, so parent replacement can redirect durable metadata outside the validated runtime tree

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `dev/local/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `aad0050932ea`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `dev/local/prds/hold/`
- **Responsibility**: hold ledger key `aad0050932ea` from `00005-runtime-substrate-v1.md` until a human triages it
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
