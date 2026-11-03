---
catchup: skip
design: skip
ledger: deferred/202610092123-deferred.json
ledger_key: 31aa451d8e6b
source_prd: 00053-adapter-operational-corrections-v1.md
severity: high
---

# Triage: Numeric diagnostics now need "HTTP", "HTTP status", "status code" or "error c...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610092123`, ledger `deferred/202610092123-deferred.json`, type `autonomous_research`, cycle `1`, consensus `[3/3]`, raised against `00053-adapter-operational-corrections-v1.md`.

Issue: Numeric diagnostics now need "HTTP", "HTTP status", "status code" or "error code" (src/ovcaq/drivers/codex_events.py:301), so Codex's own status wording falls to UNKNOWN. I ran `classify_failure` on "unexpected status 503 Service Unavailable", "unexpected status 502 Bad Gateway", "unexpected status 403 Forbidden" and "exceeded retry limit, last status: 429 Too Many Requests", and all four return `unknown`. The old code returned connectivity, permission and rate_limit for these. Both prefixes are confirmed as strings in the installed codex 0.162.1 binary; the "503 Service Unavailable" suffix is my guess at how Codex renders the code. Effect: 502/503 skip the bounded connectivity WAIT and get an immediate died-retry and then PARK, and 403 retries instead of halting for the operator. The PRD allows "HTTP/status/error-code" context, and "status 503" is a status context. Fix: accept a bare `status` (e.g. `(?:http(?: status)? | status(?: code)? | error code)`) and add both Codex spellings as literal positives in tests/drivers/test_adapter_failure_classes.py:55

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `31aa451d8e6b`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `31aa451d8e6b` from `00053-adapter-operational-corrections-v1.md` until a human triages it
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
