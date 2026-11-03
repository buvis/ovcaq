---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: 7eff39270dab
source_prd: 00007-supervisor-loop-v1.md
severity: high
---

# Triage: No production code ever starts a batch. Nothing in `src/` writes `batch.id` o...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `1`, consensus `1/3`, raised against `00007-supervisor-loop-v1.md`.

Issue: No production code ever starts a batch. Nothing in `src/` writes `batch.id` or `batch.status="running"`, and `new_state` leaves `batch.id=""`. So `ovcaq init` followed by `ovcaq run --no-tui` raises at `_open_session` → `publish_session_metric` → `_validate_identifier("")`, and `archive_final_state` also requires the id. The installed drain acceptance test passes only because its SEED script writes the batch fields straight through StateStore

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `7eff39270dab`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `7eff39270dab` from `00007-supervisor-loop-v1.md` until a human triages it
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
