---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: 9b7a23856899
source_prd: 00007-supervisor-loop-v1.md
severity: high
---

# Triage: Capability failure leaves `batch.status` as running, and a later successful r...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `1`, consensus `3/3`, raised against `00007-supervisor-loop-v1.md`.

Issue: Capability failure leaves `batch.status` as running, and a later successful retry does not clear its stale `control.attention`, violating the lifecycle contract and leaving completed state with failure attention

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `9b7a23856899`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `9b7a23856899` from `00007-supervisor-loop-v1.md` until a human triages it
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
