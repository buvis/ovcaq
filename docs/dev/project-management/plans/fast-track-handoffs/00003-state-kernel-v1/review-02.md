# FT-03R2 convergence-review handoff

- PRD: `00003-state-kernel-v1`
- Session: `FT-03R2 — Fresh convergence review`
- Review cycle: `02`
- Base SHA: `9cda04a6a0279a6306c24015ee2d3173fb916e68`
- Reviewed/head SHA: `ff00f1f5b848043293ee8d92fbd11d0d38053738`
- Complete range: `9cda04a6a0279a6306c24015ee2d3173fb916e68..ff00f1f5b848043293ee8d92fbd11d0d38053738`
- Verdict: `changes_requested`

## Inputs read

- `dev/local/plans/fast-track-implementation-plan.md`
- `dev/local/plans/implementation-plan.md`
- `dev/local/prds/implementation-plan-coverage.md`
- `dev/local/prds/wip/00003-state-kernel-v1.md`
- `dev/local/designs/00003-state-kernel-v1-design.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-review-01.md`
- `dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/rework-01.md`

The accepted implementation-plan digest matched
`43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.

## Canonical verification

- `mise exec -- uv sync --all-groups`: passed; 25 packages resolved, 24 checked.
- `mise exec -- uv run pytest`: passed; 789 tests in 9.26s.
- `mise exec -- uv run ruff check .`: passed.
- `mise exec -- uv run ruff format --check .`: passed; 75 files formatted.
- `mise exec -- uv run mypy src/ovcaq`: passed; 46 source files.
- `mise exec -- uv build`: passed; sdist and wheel built.
- `git diff --check <complete-range>`: passed.
- Focused deep-JSON/duplicate-key/symlink convergence matrix: 27 passed in 0.16s.
- The tracked worktree was clean at pinned HEAD after verification and probes.

## Mandatory isolated lenses

All three mandatory lenses completed with isolated packets and no lens was
thinned:

- Alice — consensus/architecture: `changes_requested`.
- Blake — blind/PRD-only: `pass` on the required fresh retry.
- Bob — doubt and de-slop, full R1–R5: `changes_requested`.

The first Blake worker remained unavailable and was interrupted after repeated
completion requests. The lens was dispatched once more in a new isolated
subagent with the identical packet, as required by the fast-track fallback rule.

Artifacts:

- `dev/local/reviews/00003-state-kernel-v1-fast-alice-02.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-blake-02.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-bob-02.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-review-02.md`

## Consolidated outcome

The coordinator independently reproduced four root causes in two allowed
rework bundles:

1. **Contract / correctness / security:** reject multi-linked state/backup/lock
   artifacts before access or chmod; explicitly bound JSON integer conversion
   and normalize durable/backup/CLI failures; require exact non-boolean integer
   IDs for every compound task service operation.
2. **Integration / recovery / portability:** repair state/backup/create-only
   publication when `KeyboardInterrupt` lands at a durable boundary, then
   re-raise the interrupt.

The previous cycle's deep-JSON, duplicate-key, and symlink reproductions now
pass. Deferred crosswalk wording, unconfirmed runtime TOCTOU, and concrete test/
doc slop remain non-blocking under the fast-track must-fix policy.

No code, tests, production documentation, PRD lifecycle file, project capsule,
or autopilot state was changed in FT-03R2. PRD 00003 remains in `wip`.

## Known risks or failures

- The canonical gate is green because it has no regression coverage for the
  four newly reproduced root causes.
- This is the allowed final rework cycle. A later cycle-03 review that still
  reproduces a must-fix must stop for user direction rather than extending the
  loop.
- `dev/local/autopilot/state.json` remains frozen and was not mutated or used as
  progress authority.

## Next session and exact first action

Next session: `FT-03F2 — Final convergence rework`.

First action: from clean HEAD
`ff00f1f5b848043293ee8d92fbd11d0d38053738`, read the fast-track plan, PRD 00003,
the consolidated cycle-02 review, and this handoff; add focused failing tests for
all four reproduced root causes before changing production code.

### Next-session prompt

```text
Execute the fast-track plan from:

    dev/local/plans/fast-track-implementation-plan.md

Start a fresh FT-03F2 final convergence-rework session for PRD 00003. Read:

    dev/local/prds/wip/00003-state-kernel-v1.md
    dev/local/reviews/00003-state-kernel-v1-fast-review-02.md
    dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/review-02.md

From clean HEAD ff00f1f5b848043293ee8d92fbd11d0d38053738, apply both consolidated cycle-02 rework bundles. First add focused failing regression tests, then fix all four reproduced root causes: reject hard-linked state/backup/lock artifacts without touching aliases; bound JSON integer conversion and normalize state/backup/CLI errors; reject boolean, float, and other aliased task IDs at every compound service boundary; and repair initialization/transaction/restore publication when KeyboardInterrupt lands at a durable boundary before re-raising it. Include a representative real-subprocess SIGINT regression in addition to the injected boundary matrix.

Run targeted state/durability/service/installed-CLI coverage, then the complete canonical PRD verification gate. Commit the cohesive rework conventionally and write:

    dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/rework-02.md

Do not review or close/move the PRD in the rework session. Hand off to a fresh cycle-03 review coordinator that reruns isolated Alice, Blake, and Bob over the complete updated PRD range. This is the final allowed rework/review cycle; if a must-fix survives, stop with exact evidence for a user decision. Do not invoke run-autopilot, autoclaude, or mutate dev/local/autopilot/state.json. Print that next-session prompt and stop.
```
