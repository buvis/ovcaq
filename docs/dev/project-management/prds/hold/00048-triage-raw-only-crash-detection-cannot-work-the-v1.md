---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: bc67f0d97e0e
source_prd: 00008-tui-python-launcher-v1.md
severity: high
---

# Triage: Raw-only crash detection cannot work: the normalized file is created before s...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `1`, consensus `1/3`, raised against `00008-tui-python-launcher-v1.md`.

Issue: Raw-only crash detection cannot work: the normalized file is created before streaming begins, while evidence status treats mere file existence as successful normalization, so a crash after raw persistence but before normalization renders partial/unavailable instead of raw-only

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `bc67f0d97e0e`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `bc67f0d97e0e` from `00008-tui-python-launcher-v1.md` until a human triages it
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
