---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: fcc2b36f9729
source_prd: 00008-tui-python-launcher-v1.md
severity: high
---

# Triage: Active duration is calculated by summing finalized session and capability wal...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `1`, consensus `2/3`, raised against `00008-tui-python-launcher-v1.md`.

Issue: Active duration is calculated by summing finalized session and capability wall times instead of elapsed time from `FleetRun.started_at`, contrary to the explicit duration contract

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `fcc2b36f9729`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `fcc2b36f9729` from `00008-tui-python-launcher-v1.md` until a human triages it
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
