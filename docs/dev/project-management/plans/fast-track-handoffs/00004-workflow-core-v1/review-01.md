# FT-04R1 convergence-review handoff

- PRD: `00004-workflow-core-v1`
- Session: `FT-04R1 — cycle-01 convergence review`
- Review cycle: `01`
- Base SHA: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`
- Reviewed/head SHA: `5a7ff023059bd396a177da7946a25ffe8d6d176d`
- Complete range:
  `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..5a7ff023059bd396a177da7946a25ffe8d6d176d`
- Verdict: `changes_requested`
- Decision gate: `rework_required`
- Must-fix root causes: `8`
- Rework bundles: `3`

## Inputs and protected state

The fresh coordinator read the fast-track plan, accepted implementation plan,
PRD 00004, verification handoff, exact diff, and changed implementation/tests.
No PRD 00004 design artifact exists.

- Verified review start/head: `5a7ff023059bd396a177da7946a25ffe8d6d176d`
- Tracked worktree/index: clean before review artifact publication
- Accepted implementation-plan SHA-256:
  `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`
- Frozen `dev/local/autopilot/state.json` SHA-256:
  `ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f`
- No autopilot command/state machine, PRD move, production edit, or project
  capsule edit ran.

## Verification inherited at reviewed head

- Full pytest: 1,020 passed.
- Ruff check and format check: passed.
- mypy: passed for 47 source files.
- Build: sdist and wheel passed.
- Focused workflow/installed CLI: 138 passed.
- Transient exhaustive transition probe: 6 accepted / 16 rejected.
- `git diff --check` on the complete range: passed.

## Mandatory isolated lenses

- Alice: `changes_requested`, seven must-fix claims.
- Blake: `changes_requested`, one independently reproduced must-fix.
- Bob fallback: `changes_requested`, seven must-fix claims; all doubt/de-slop
  questions completed.

Alice, Blake, and the initial Bob context launched concurrently. The initial
Bob context did not return after two completion requests and was interrupted.
The required fresh fallback received the same isolated input packet and
returned the complete Bob report. No lens was omitted.

Artifacts:

- `dev/local/reviews/00004-workflow-core-v1-fast-alice-01.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-blake-01.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-bob-01.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-review-01.md`

## Consolidated outcome

The coordinator independently reproduced lifecycle symlink escape, stale
cycle-local review data, premature completion, conflicting defer-ID loss,
directory-as-PRD selection, and false saga replay for an inactive held PRD.
Direct inspection confirmed external `/work` skill syntax in provider-neutral
resume output. Committed tests also omit the full transition rejection matrix
and defer interruption/retry boundaries.

These form three rework bundles:

1. contract/correctness/security;
2. integration/recovery/portability;
3. tests/docs/maintainability.

General config precedence/path containment remains owned by P03-T01 / PRD
00005 and must not be pulled into this rework. The exact root-cause dispositions
and bundle membership are authoritative in the consolidated review.

## Next session and exact first action

Next session: `FT-04F1 — consolidated rework`.

First action: from clean HEAD
`5a7ff023059bd396a177da7946a25ffe8d6d176d`, read only:

- `dev/local/prds/wip/00004-workflow-core-v1.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-review-01.md`
- the committed repository

Fix all eight must-fix root causes across the three bundles in one cohesive
session without implementing deferred PRD 00005 configuration precedence.
Run targeted regressions continuously, then the complete verification gate.
Commit the rework conventionally, write `rework-01.md` with exact results and
the updated complete range, and stop. Do not review or close PRD 00004 in the
rework session; the code-changing rework requires a fresh three-lens review.

### Next-session prompt

```text
Execute FT-04F1 consolidated rework for PRD 00004 from:

    dev/local/reviews/00004-workflow-core-v1-fast-review-01.md

Start from clean HEAD 5a7ff023059bd396a177da7946a25ffe8d6d176d.
Read only the consolidated review, the WIP PRD, and the committed repository.
Fix all eight must-fix root causes in the three defined bundles; do not pull
PRD 00005 configuration precedence/containment into scope. Run targeted tests
and the full verification gate, commit the cohesive rework, write
dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/rework-01.md, and
stop. Do not run review or closeout in the rework session.
```
