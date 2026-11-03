---
catchup: run
design: run
rework_cap: 2
default_model: opus
model_tier_rationale: stable identity for ID-less observations and bounded presentation require designed behavior
---

# Faithful recent activity display

## Overview

### Problem Statement

[PRD 00009 review 2](../../reviews/00009-codex-adapter-v1-review-2.md) R3 shows
real provisional errors/warnings lose detail and are overwritten by unrelated
ID-less turn messages. R10 hides recent work behind old activity and lanes.
R27 tests invented input payloads, while R11 documents obsolete fixture/display
behavior. Repair these shared-model presentation defects under the
[resolved discovery](../../discovery/00001-ovcaq-v1.md).
Premise: recheck each defect before changing code; already-correct behavior gets
regression coverage and an explicit skip, never a forced rewrite.

### Target Users

Operators watching current tool activity and failure details in live or plain TUI.

### Success Metrics

Decoder-produced errors, warnings, tools and plans render accurate detail;
unrelated ID-less records remain distinct; the latest activity appears first.
Retained model history stays bounded at the existing MAX_ACTIVITY limit.

## Functional Decomposition

### Capability: Accurate activity projection

#### Feature: Actual payload details and identities
- **Description**: Project native adapters' real normalized payloads faithfully.
- **Inputs**: activity.message records with text or detail, with or without a
  nonblank message_id; real normalized tool and plan records.
- **Outputs**: Existing ActivityItem records in the shared ProjectView.
- **Behavior**: Use text when present, otherwise detail. Real message IDs update
  their existing item; absent/blank IDs identify distinct observed records so a
  turn marker cannot replace an error. Repeated snapshots must not duplicate
  already-consumed records. Preserve existing eviction, reset and bounds.
  Remove the invented tool input fallback and use actual driver output in tests.

### Capability: Recent activity presentation

#### Feature: Bounded recent window
- **Description**: Keep the current activity visible with large retained histories.
- **Inputs**: ProjectView activity and lane histories.
- **Outputs**: Rich Activity panel used by live and plain rendering.
- **Behavior**: Render the newest 20 activity entries first, newest first; then
  at most 20 lanes in their existing order. State how many entries/lanes were
  omitted when nonzero. This display limit does not truncate retained models or
  change lifecycle policy. Preserve existing text sanitization and empty states.
  The fixed window is this repair's explicit UI policy, requiring no user choice
  during implementation and no new configuration surface.

#### Feature: Current fixture and display documentation
- **Description**: Make operator/fixture documentation match checked-in evidence.
- **Inputs**: Existing lanes-matched.jsonl and actual normalized activity behavior.
- **Outputs**: Updated fixture matrix, driver protocol and changelog.
- **Behavior**: Document matched-lane fixture truthfully; remove the obsolete
  in-place variant and lanes-only claims. Describe tools/messages/plans, detail
  fallback, and the recent window without claiming real provider smoke evidence.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/tui/{model.py,panels.py}
tests/tui/test_activity_projection.py    # new behavioral regressions
tests/tui/test_activity_window.py        # new renderer regressions
tests/tui/test_rework_activity.py        # replace invented payload assertion
tests/fixtures/README.md
docs/driver-protocol.md
CHANGELOG.md
```

### Module: Activity model
- **Maps to capability**: Accurate activity projection.
- **Responsibility**: Shared normalized projection and real-payload regression coverage.
- **Exports**: Existing ProjectObserver, ProjectView and ActivityItem; no new public API.

### Module: Activity presentation
- **Maps to capability**: Recent activity presentation.
- **Responsibility**: Bounded renderer, renderer tests, fixture/protocol documentation
  and user-facing changelog.
- **Exports**: Existing activity_panel; no provider-specific code in TUI.

## Dependency Graph

### Foundation Layer (Phase 0)
- **Activity model**: Existing normalized event records and bounded shared observer.

### Core Layer (Phase 1)
- **Activity presentation**: Depends on Activity model.

### Integration Layer (Phase 2)
- **Documentation and conformance**: Depends on Activity model and Activity presentation.
- Execute after 00051–00053 repairs; preserve their terminal and safety semantics.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Preserve correct message detail and identity through projection.

**Tasks**:
- [ ] Repair projection and actual-shape tests (no deps). Acceptance: `uv run
  pytest tests/tui/test_activity_projection.py tests/tui/test_rework_activity.py`
  exercises both adapters' decoded payloads, repeated ID-less errors followed by
  turn markers, real-ID updates, repeated snapshots, eviction and observer reset.

**Exit Criteria**: Error detail survives unrelated later events without duplicates.

### Phase 1: Core
**Goal**: Put current activity at the top of bounded output.

**Tasks**:
- [ ] Render the recent window (depends on: Phase 0). Acceptance: `uv run pytest
  tests/tui/test_activity_window.py` asserts newest activity precedes lanes,
  exact 20-entry/20-lane limits, omission counts, empty states, safe text and
  unchanged retained ProjectView history through Rich Console text capture.

**Exit Criteria**: Live/plain Activity content has deterministic bounded entries.

### Phase 2: Integration
**Goal**: Align documentation with actual fixtures and final display behavior.

**Tasks**:
- [ ] Correct fixture matrix, protocol and changelog (depends on: Phase 1).
  Acceptance: documents name lanes-matched.jsonl, actual activity and the 20/20
  window; obsolete in-place variant and lanes-only assertions are absent.

**Exit Criteria**: `uv sync --all-groups`, `uv run pytest`, `uv run ruff check .`,
`uv run ruff format --check .`, `uv run mypy src/ovcaq` and `uv build` pass.
Run all mandatory review lenses in a fresh session after build handoff.

## Test Strategy

### Critical Scenarios
- **Happy path**: Tools with true IDs update one entry and display current state.
- **Edge case**: ID-less warning/error/turn messages remain distinct at the cap.
- **Error case**: Controls and synthetic credentials cannot appear unsanitized;
  arbitrary unknown shapes retain tolerant existing handling.

## Risks

- **Duplicate replay**: Use actual observer cursor semantics rather than random IDs.
- **Hidden history**: Omission counts make the display window explicit; raw evidence
  and retained model data are unchanged.
- **Scope**: No lifecycle decisions in TUI, new configuration, historical test
  renaming, fixture relabeling or real provider calls.
