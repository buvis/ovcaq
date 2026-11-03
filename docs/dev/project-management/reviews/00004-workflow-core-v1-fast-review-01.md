---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
session: FT-04R1
review_kind: fast-track
cycle: 1
date: 2026-09-01
base_sha: b43bf2c94d5eb0fddafca55542ef2570b45e8d52
head_sha: 5a7ff023059bd396a177da7946a25ffe8d6d176d
verdict: changes_requested
decision_required: false
closeout_ready: false
must_fix_root_causes: 8
rework_bundles: 3
reviewers:
  alice: available
  blake: available
  bob: available_via_fallback
---

# Fast review 01: 00004 workflow core v1

Complete PRD implementation range reviewed:
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..5a7ff023059bd396a177da7946a25ffe8d6d176d`.
The range contains 30 changed files and 3,667 additions / 12 deletions.

Raw reports:

- `dev/local/reviews/00004-workflow-core-v1-fast-alice-01.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-blake-01.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-bob-01.md`

## Verification at reviewed head

| Check | Result |
|---|---|
| `mise exec -- uv sync --all-groups` | passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest` | passed; 1,020 tests in 9.85s |
| `mise exec -- uv run ruff check .` | passed |
| `mise exec -- uv run ruff format --check .` | passed; 89 files formatted |
| `mise exec -- uv run mypy src/ovcaq` | passed; 47 source files |
| `mise exec -- uv build` | passed; sdist and wheel built |
| focused workflow/installed CLI | passed; 138 tests in 0.96s |
| transient exhaustive transition probe | passed; 6 accepted / 16 rejected |
| `git diff --check <complete-range>` | passed |
| accepted-plan SHA-256 | `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5` |
| frozen autopilot-state SHA-256 | `ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f` |
| reviewed HEAD / tracked tree | exact / clean before artifact publication |

## Mandatory isolated lenses

| Lens | Verdict | Must-fix claims | Consolidated contribution |
|---|---|---:|---|
| Alice — consensus/architecture | changes requested | 7 | cycle reset, completion, defer conflict, lifecycle safety, evidence |
| Blake — blind/PRD-only | changes requested | 1 | independently reproduced lifecycle symlink escape |
| Bob — doubt/de-slop | changes requested | 7 | false replay and provider-specific resume leakage in addition to shared defects |

Alice, Blake, and the initial Bob context were dispatched concurrently with
isolated read-only packets. Alice and Blake completed normally. The initial Bob
context did not return after two completion requests and was interrupted; a
fresh fallback received the same isolated packet and completed every Phase 1
question and Phase 1.5 slop lens. No lens was omitted.

## Coordinator reproduction and reconciliation

The coordinator independently reproduced the following against the reviewed
HEAD using temporary directories only:

1. A symlinked `hold` directory moves the active WIP PRD to an external
   directory, then commits reset with `recovery.operation = null`.
2. `review + rework` increments the cycle while leaving a completed Alice lens
   and prior R1 failure live.
3. `complete_prd()` appends a completed summary while `work.phase == review`.
4. Reusing one defer `op_id` with different details silently preserves only the
   first payload.
5. Selection chooses a directory named `00001-directory.md` ahead of a regular
   PRD file.
6. A stall request for an already-held inactive PRD returns
   `SagaResult(replayed=True)` while the state and ledger remain unchanged and
   another PRD remains active.

Direct inspection confirms `resume.py:39` embeds the external `/work` skill
syntax in provider-neutral workflow output. These are contract defects, not
style preferences.

### Reclassified reviewer claims

- General configuration precedence, `ovcaq.toml` loading, PRD/runtime-root
  containment, and explicit external-state-root semantics are assigned to
  P03-T01 / PRD 00005 (`00005-runtime-substrate-v1.md:48-53,140-141`). PRD
  00004 already exposes a configured-root workflow service. The hardcoded CLI
  default and absent active-agent tier wiring are therefore recorded as a
  cross-PRD integration risk, not a PRD 00004 must-fix. Rework must not pull
  PRD 00005's configuration subsystem forward.
- Absolute configured lifecycle roots are intentionally covered by the PRD
  00004 resolver tests. The confirmed current defect is following a symlinked
  lifecycle child during a verified move, not merely accepting an absolute
  service input.
- Byte-identical duplicate `complete-prd` replay, Python 3.12 execution,
  Windows `fcntl`, transition-table duplication, docstring cleanup, negative
  custom ceilings, recovery batch-ID hardening, and report-directory symlink
  hardening are deferred. None reproduces an additional current PRD acceptance
  failure beyond the must-fix roots below.

## Must-fix root causes

### 1. Lifecycle artifact validation is not fail-closed

`selection.py:43-52` treats directory names as PRDs, and
`records.py:337-362,468` follows a symlinked lifecycle directory during a move.
Selection and mutation must operate only on validated regular, non-symlink PRD
files and lifecycle directories. Add regressions for directory-shaped PRDs and
symlinked WIP/hold paths. This root violates P02-T01, P02-T07, verified-move
recovery, and no-lost-work safety.

### 2. Destination existence is incorrectly treated as proof of replay

`records.py:473-488` returns success before validating the committed active PRD
or finding durable intent. An unrelated already-held PRD can therefore produce
a false-success stall. A no-intent replay must prove that the requested PRD is
the committed active PRD and that the destination represents this operation,
or fail closed without mutation. Add the reproduced inactive-PRD case.

### 3. Rework does not clear all cycle-local state

`transitions.py:40-46` preserves `review.lenses` and
`review.rubric_verdicts` across the cycle boundary even though neither value is
cycle-keyed. Clear all cycle-local owners while preserving durable review
history and batch-owned fields. Add a full-effect regression with populated
cycle-local state. This violates P02-T03 and the accepted `review + rework`
effect.

### 4. Completion does not require terminal workflow state

`records.py:122-145` accepts completion in build or review. Require the
authoritative terminal/converged state before appending a completed-PRD
summary; conflict must preserve bytes/revision. Replace the CLI test that
currently blesses review-phase completion and add build/review refusal cases.
This violates P02-T05 and state-over-prose lifecycle authority.

### 5. Defer operation-ID conflicts silently discard data

`records.py:293-299` must distinguish an exact duplicate payload from the same
operation ID reused for different content. Exact replay remains a byte no-op;
conflicting reuse must fail without modifying the ledger. Add both cases at the
service and installed CLI boundaries. This violates P02-T06 and no-lost-work
idempotence.

### 6. Provider-neutral resume output embeds an external skill command

`resume.py:39` returns `/work continues...`, leaking launcher/plugin syntax into
core. Return a provider-neutral action/result and strengthen the boundary guard
to cover external skill command identifiers. Update characterized expectations
without importing launcher content. This violates the provider-edge and
external-capability invariants.

### 7. The complete rejection matrix is not durable test evidence

`tests/workflow/test_transitions.py:91-107` commits only three representative
rejections. The verification session's transient `python -c ...` probe is
reported but not preserved as executable source. Commit the full valid-phase ×
public-outcome rejection matrix plus unknown phase/outcome cases so every row is
reproducible. This is a required P02-T03/acceptance evidence gap.

### 8. Defer interruption recovery lacks failpoint evidence

Park/stall cover all five durable boundaries, but defer tests cover only exact
duplicate and invalid-input behavior. Add deterministic interruption/failure
coverage around the deferred ledger's atomic publication boundary, including
retry and byte-preservation/no-duplicate assertions. This is a required
P02-T06 and every-durable-boundary evidence gap.

## Rework bundles

1. **Contract/correctness/security:** root causes 1-6 — fail-closed lifecycle
   artifacts and replay binding, complete cycle reset, terminal completion,
   conflict-safe operation IDs, and provider-neutral resume output.
2. **Integration/recovery/portability:** root causes 1, 2, 5, and 8 — targeted
   real-filesystem/failpoint tests for symlink paths, false replay, conflicting
   retries, and defer interruption/retry.
3. **Tests/docs/maintainability:** root causes 3, 4, 6, and 7 — full transition
   effects/rejections, corrected CLI completion flow, boundary guard, and
   parser-generated docs if observable command text changes.

## Verdict and next action

Verdict: **changes requested**. The passing deterministic gate does not close
the eight reproduced contract/evidence roots. PRD 00004 remains in `wip`; no
production code, PRD lifecycle file, project capsule, or autopilot state was
changed in this review session.

Next action: start a fresh `FT-04F1` rework session from this consolidated
review, the PRD, and clean reviewed HEAD. Fix all three bundles together, run
targeted regressions and the full verification gate, commit the cohesive
result, write `rework-01.md`, and stop. Any code-changing rework must then
receive a fresh review coordinator and all three isolated lenses.
