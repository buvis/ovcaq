---
catchup: skip
design: skip
ledger: deferred/202609062243-deferred.json
ledger_key: 17d7d345e669
source_prd: 00005-runtime-substrate-v1.md
severity: high
---

# Triage: Symlink rejection extends to trust anchors: `_checked_path` walks from `/`, s...

## Problem

Deferred finding with no PRD owner when this stub was minted: batch `202609062243`, ledger `deferred/202609062243-deferred.json`, type `autonomous_research`, cycle `1`, consensus `[1/3]`, raised against `00005-runtime-substrate-v1.md`.

Issue: Symlink rejection extends to trust anchors: `_checked_path` walks from `/`, so `--root /tmp/x` or `/var/...` fails on macOS (`/tmp`→`/private/tmp`) and a symlinked `~/.config` (stow/chezmoi) makes `_read_config` raise even when no config file exists; this now breaks every pre-existing workflow command too

## Solution

Attended triage. A human promotes this finding into a backlog PRD through normal PRD authoring and review, or closes it. Autopilot never drains `dev/local/prds/hold/`, and this stub is never auto-promoted.

## Requirements

### Must have
- A triage decision for ledger key `17d7d345e669`: a backlog PRD, or closed.

### Nice to have
- None until triage.

## Implementation

### Module: triage
- **Location**: `dev/local/prds/hold/`
- **Responsibility**: hold ledger key `17d7d345e669` from `00005-runtime-substrate-v1.md` until a human triages it
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
