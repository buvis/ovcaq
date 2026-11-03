---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: ad7f618a1dde
source_prd: 00006-events-claude-adapter-v1.md
severity: high
---

# Triage: H1/H4/H5/M1 rate-limit semantics (allowed_warning clears limit; banner overwr...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `2`, raised against `00006-events-claude-adapter-v1.md`.

Issue: H1/H4/H5/M1 rate-limit semantics (allowed_warning clears limit; banner overwrites event reset; real clock+zone banners unparsed; window only in prose)

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `ad7f618a1dde`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `ad7f618a1dde` from `00006-events-claude-adapter-v1.md` until a human triages it
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
