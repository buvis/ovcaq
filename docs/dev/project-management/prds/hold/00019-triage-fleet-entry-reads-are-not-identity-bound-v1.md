---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: a6cc2fc6cd9d
source_prd: 00005-runtime-substrate-v1.md
severity: high
---

# Triage: Fleet entry reads are not identity-bound to deletion: `_scan` records a pre-o...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `cap-overflow`, cycle `2`, consensus `[1/3]`, raised against `00005-runtime-substrate-v1.md`.

Issue: Fleet entry reads are not identity-bound to deletion: `_scan` records a pre-open inode without comparing it to the opened descriptor, while `remove` validates contents and then unlinks the pathname without rechecking its inode; a replacement during either gap can make prune delete a live record or remove delete a new owner’s record

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `dev/local/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `a6cc2fc6cd9d`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `dev/local/prds/hold/`
- **Responsibility**: hold ledger key `a6cc2fc6cd9d` from `00005-runtime-substrate-v1.md` until a human triages it
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
