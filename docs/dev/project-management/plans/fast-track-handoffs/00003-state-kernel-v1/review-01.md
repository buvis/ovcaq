# FT-03R review handoff

- PRD: `00003-state-kernel-v1`
- Session: `FT-03R — Fresh review`
- Review cycle: `01`
- Base SHA: `9cda04a6a0279a6306c24015ee2d3173fb916e68`
- Reviewed/head SHA: `9872123ac9be6433f95ad4fb5606ac48cb402fce`
- Complete range: `9cda04a6a0279a6306c24015ee2d3173fb916e68..9872123ac9be6433f95ad4fb5606ac48cb402fce`
- Verdict: `changes_requested`

## Inputs read

- `dev/local/plans/fast-track-implementation-plan.md`
- `dev/local/plans/implementation-plan.md`
- `dev/local/prds/implementation-plan-coverage.md`
- `dev/local/prds/wip/00003-state-kernel-v1.md`
- `dev/local/designs/00003-state-kernel-v1-design.md`
- `dev/local/reviews/00003-state-kernel-v1-review-02.md`
- `dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/01-build.md`

The accepted implementation-plan digest matched
`43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.

## Canonical verification

- `mise exec -- uv sync --all-groups`: passed; 25 packages resolved, 24 checked.
- `mise exec -- uv run pytest`: passed; 762 tests in 8.65s.
- `mise exec -- uv run ruff check .`: passed.
- `mise exec -- uv run ruff format --check .`: passed; 75 files already formatted.
- `mise exec -- uv run mypy src/ovcaq`: passed; 46 source files.
- `mise exec -- uv build`: passed; sdist and wheel built.
- `git diff --check <complete-range>`: passed.

## Mandatory isolated lenses

All three lenses ran concurrently with isolated packets and completed without a
retry:

- Alice — consensus/architecture: `changes_requested`.
- Blake — blind/PRD-only: `changes_requested`.
- Bob — doubt and de-slop, full R1–R5: `changes_requested`.

Artifacts:

- `dev/local/reviews/00003-state-kernel-v1-fast-alice-01.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-blake-01.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-bob-01.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-review-01.md`

## Consolidated outcome

The raw reports reduce to three reproduced root causes in one allowed rework
bundle, **contract / correctness / security**:

1. Validate containment and reject symlink escapes for derived runtime/store
   paths. Runtime-directory and lock-sidecar cases currently chmod or write to
   external targets.
2. Bound deeply nested JSON before recursive decode/copy work and translate every
   rejection to the stable symbolic CLI/state errors.
3. Reject duplicate JSON object keys before parsing destroys closed-schema
   evidence.

Deferred observations are recorded only in the consolidated review. They do not
create extra rework bundles: vague derived crosswalk semantics should be
clarified before PRD 00004 consumes them; empty-key paths and corrupt-current
restore follow the accepted design; test bloat/manifest structure is not a
reproduced product defect.

No code, tests, production documentation, PRD lifecycle file, project capsule,
or autopilot state was changed in FT-03R. PRD 00003 remains in `wip`.

## Known risks or failures

- The canonical gate passes but lacks regression cases for all three reproduced
  root causes.
- Any code-changing rework requires a later fresh three-lens review; FT-03F must
  not review or close the PRD in its work session.
- `dev/local/autopilot/state.json` remains frozen and was not mutated or used as
  progress authority.

## Next session and exact first action

Next session: `FT-03F — Consolidated rework`.

First action: from clean HEAD
`9872123ac9be6433f95ad4fb5606ac48cb402fce`, read the fast-track plan, PRD 00003,
the consolidated fast review, and this handoff; write focused failing tests for
all three root causes before changing production code.

### Next-session prompt

```text
Execute the fast-track plan from:

    dev/local/plans/fast-track-implementation-plan.md

Start session FT-03F for PRD 00003. Read:

    dev/local/prds/wip/00003-state-kernel-v1.md
    dev/local/reviews/00003-state-kernel-v1-fast-review-01.md
    dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/review-01.md

From clean HEAD 9872123ac9be6433f95ad4fb5606ac48cb402fce, apply the single consolidated contract/correctness/security rework bundle. First add focused failing regression tests, then fix all three root causes: derived runtime/store path containment and symlink escapes; bounded deep-JSON rejection with stable symbolic errors; and duplicate JSON-key rejection before closed-schema validation. Run targeted state/durability/installed-CLI coverage, then the complete canonical PRD verification gate. Commit the cohesive rework conventionally and write:

    dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/rework-01.md

Do not review or close the PRD in the rework session. Hand off to a fresh review coordinator that reruns isolated Alice, Blake, and Bob over the complete updated PRD range. Do not invoke run-autopilot, autoclaude, or mutate dev/local/autopilot/state.json. Print that next-session prompt and stop.
```
