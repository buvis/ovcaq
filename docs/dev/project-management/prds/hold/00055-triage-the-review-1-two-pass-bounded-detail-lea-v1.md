---
catchup: skip
design: skip
ledger: deferred/202610092123-deferred.json
ledger_key: 7dc79595bba3
source_prd: 00051-triage-a-single-valid-codex-record-can-crash-th-v1.md
severity: high
---

# Triage: The review-1 two-pass `bounded_detail` leaks the tail of a split token. When...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202610092123`, ledger `deferred/202610092123-deferred.json`, type `cap-overflow`, cycle `2`, consensus `[3/3]`, raised against `00051-triage-a-single-valid-codex-record-can-crash-th-v1.md`.

Issue: The review-1 two-pass `bounded_detail` leaks the tail of a split token. When the control sits after 20 or more body characters, pass 1 redacts the head. Control removal then glues the tail onto `[REDACTED]`, and pass 2 finds no `sk-` or `Bearer` prefix to match. I ran it to confirm: `bounded_detail('Diagnostic sk-abcdefghijklmnopqrstuvwxyz\x1b[0m0123456789ABCDEF')` returns `'Diagnostic [REDACTED]0123456789ABCDEF'`, the real `turn.failed` payload detail is the same, and `'Bearer '+'a'*23+'\x00bbbbbbbb'` returns `'Bearer [REDACTED]bbbbbbbb'`. Task 3's strip-first order redacted these fully, and pre-PRD code leaked the same way. This breaks two PRD rules ("ANSI/NUL splits of ordinary synthetic tokens are redacted", "synthetic credential fragments never enter normalized details") and makes docs/driver-protocol.md:224 claim too much. Every split test cuts at `token[:6]`, so no test catches it. Fix: before control removal, absorb token characters stuck to a marker across recognized controls with `re.sub(rf"\[REDACTED\](?:{controls})+[A-Za-z0-9_.-]+", "[REDACTED]", sanitize_text(protected))`. I probed this on both leaks plus `x\x00sk-…`, the OSC case and the cap reproducer, and all came out fully redacted (I did not run the suite with it). Also add SPLIT_DETAILS cases that split after 20 or more body characters, for both bare and Bearer tokens

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `docs/dev/project-management/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `7dc79595bba3`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `docs/dev/project-management/prds/hold/`
- **Responsibility**: hold ledger key `7dc79595bba3` from `00051-triage-a-single-valid-codex-record-can-crash-th-v1.md` until a human triages it
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
