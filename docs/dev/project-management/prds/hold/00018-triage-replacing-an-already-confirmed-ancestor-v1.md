---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: 61e411555a61
source_prd: 00004-workflow-core-v1.md
severity: high
---

# Triage: Replacing an already confirmed ancestor and reparenting the same runtime inod...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `15`, consensus `1/3 (Alice adjudication of coordinator evidence)`, raised against `00004-workflow-core-v1.md`.

Issue: Replacing an already confirmed ancestor and reparenting the same runtime inode beneath its replacement before ledger open is accepted by direct append and exact replay, without any later fsync of the ancestor's parent or the replacement ancestor. Runtime-only identity checks do not preserve the confirmed ancestry through successful publication.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `dev/local/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `61e411555a61`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `dev/local/prds/hold/`
- **Responsibility**: hold ledger key `61e411555a61` from `00004-workflow-core-v1.md` until a human triages it
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
