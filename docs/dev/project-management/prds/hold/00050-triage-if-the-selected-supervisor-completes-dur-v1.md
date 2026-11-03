---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: 437a130c43aa
source_prd: 00008-tui-python-launcher-v1.md
severity: high
---

# Triage: If the selected supervisor completes during evidence reads, exit revalidation...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `cap-overflow`, cycle `2`, consensus `1/3`, op_id `finalize-status-00008-tui-python-launcher-v1.md-2-F01`, raised against `00008-tui-python-launcher-v1.md`.

Issue: If the selected supervisor completes during evidence reads, exit revalidation discards even valid selected-owner final state and sets ended=True; ProjectObserver permanently caches unknown, so both viewers return failed/1 for normal completion. Reobserve the attested final selection before caching a terminal result.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `437a130c43aa`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `437a130c43aa` from `00008-tui-python-launcher-v1.md` until a human triages it
- **Exports**: none

### Dependencies
- triage: No dependencies (foundation)

## Tasks

### Phase 0: Foundation
- [ ] triage: promote to backlog or close - Acceptance: this file is no longer under docs/dev/project-management/prds/hold/

### Phase 1: Core
No implementation tasks until attended triage.

## Success Criteria

- This file is no longer under `docs/dev/project-management/prds/hold/`.
