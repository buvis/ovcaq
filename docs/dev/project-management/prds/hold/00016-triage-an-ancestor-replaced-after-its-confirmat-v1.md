---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: 181da681994f
source_prd: 00004-workflow-core-v1.md
severity: high
---

# Triage: An ancestor replaced after its confirmation is silently adopted as the next l...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `13`, consensus `coordinator; Alice adjudication confirms`, raised against `00004-workflow-core-v1.md`.

Issue: An ancestor replaced after its confirmation is silently adopted as the next level's parent; defer returns success without fsyncing the replacement ancestor's parent

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `dev/local/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `181da681994f`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `dev/local/prds/hold/`
- **Responsibility**: hold ledger key `181da681994f` from `00004-workflow-core-v1.md` until a human triages it
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
