---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: 05ddae07ff99
source_prd: 00007-supervisor-loop-v1.md
severity: high
---

# Triage: Retry budgets can be dodged forever. `Supervisor._decide` resets `RetryState`...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `1`, consensus `1/3`, raised against `00007-supervisor-loop-v1.md`.

Issue: Retry budgets can be dodged forever. `Supervisor._decide` resets `RetryState` whenever the failure class changes, and failure-path RETRY/WAIT decisions never advance `phase_repeats`. Alternating failures (agent death, then connectivity, then agent death...) therefore relaunch sessions without limit. This breaks the PRD's "Retry storms: Bound every wait/retry" mitigation. Confirmed by tracing `decide` and `_decide`

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `05ddae07ff99`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `05ddae07ff99` from `00007-supervisor-loop-v1.md` until a human triages it
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
