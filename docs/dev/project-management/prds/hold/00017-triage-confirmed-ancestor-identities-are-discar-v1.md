---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: 7add87f85ae4
source_prd: 00004-workflow-core-v1.md
severity: high
---

# Triage: Confirmed ancestor identities are discarded when `_ensure_directory_chain` re...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `14`, consensus `2/3`, raised against `00004-workflow-core-v1.md`.

Issue: Confirmed ancestor identities are discarded when `_ensure_directory_chain` returns; replacing `runtime_root` before `deferred.mkdir()` lets publication or replay succeed in a replacement tree whose parent entry was never fsynced, leaving R13-01’s durability risk open. Keep the confirmed runtime ancestry bound through ledger creation/publication and reverify before success.

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `dev/local/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `7add87f85ae4`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `dev/local/prds/hold/`
- **Responsibility**: hold ledger key `7add87f85ae4` from `00004-workflow-core-v1.md` until a human triages it
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
