# FT-04R2 convergence-review handoff

- PRD: `00004-workflow-core-v1`
- Session: `FT-04R2 — cycle-02 convergence review`
- Review cycle: `02`
- Date: `2026-09-02`
- Base SHA: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`
- Reviewed/head SHA: `56b664fc44c359b0b97282aa2e116dbf9ed44ff9`
- Complete range:
  `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..56b664fc44c359b0b97282aa2e116dbf9ed44ff9`
- Verdict: `changes_requested`
- Decision gate: `final_rework_required`
- Must-fix root causes: `8`
- Rework bundles: `3`

## Inputs and protected state

The fresh coordinator read the fast-track plan, accepted implementation plan,
PRD 00004, cycle-01 consolidated review, rework-01 handoff, complete diff, and
all changed implementation/tests. No PRD 00004 design artifact exists.

- Verified review start/head: `56b664fc44c359b0b97282aa2e116dbf9ed44ff9`
- Tracked worktree/index: clean before review artifact publication
- Accepted implementation-plan SHA-256:
  `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`
- Frozen `dev/local/autopilot/state.json` SHA-256:
  `ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f`
- No autopilot command/state machine, PRD move, production edit, or project
  capsule edit ran.

## Verification at reviewed head

- `uv sync --all-groups`: passed; 25 resolved / 24 checked.
- Full pytest: 1,049 passed in 10.95s.
- Ruff check and format check: passed; 89 files formatted.
- mypy: passed for 47 source files.
- Build: sdist and wheel passed.
- Focused workflow/installed CLI: 167 passed in 1.22s.
- `git diff --check` on the complete range: passed.

## Mandatory isolated lenses

- Alice: `changes_requested`, four raw must-fix claims.
- Blake: `changes_requested`, three raw must-fix claims.
- Bob: `changes_requested`, ten FIX doubts, three KNOWN doubts, and complete
  R1–R5 results (`R1/R4 pass`; `R2/R3/R5 fail`).

All three ran concurrently with the mandatory isolated packets. Blake received
no plan, design, handoff, earlier-review, AGENTS, or peer-review context. No lens
was omitted, thinned, or retried.

Artifacts:

- `dev/local/reviews/00004-workflow-core-v1-fast-alice-02.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-blake-02.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-bob-02.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-review-02.md`

## Consolidated outcome

The coordinator retained eight canonical roots:

1. active held PRD falsely accepted as a completed no-intent replay;
2. competing workflow mutations are not fenced during durable recovery;
3. lifecycle directory substitution redirects a move after intent;
4. frontmatter application violates active-PRD attribution, the v1 crosswalk,
   and real overwrite-warning behavior;
5. P02-T08's routed final archive/report-section/golden behavior is incomplete;
6. report publication permits traversal and symlink escape;
7. workflow command truth is duplicated outside the generated reference; and
8. hold exclusion and transition/effect agreement lack behavioral evidence.

The authoritative evidence, reclassifications, and bundle membership are in
the consolidated review. Configuration/tier-map loading, cap-pause enforcement,
and caller-owned PRD lifecycle moves remain outside this rework.

## Next session and exact first action

Next session: `FT-04F2 — final consolidated rework`.

First action: from exact clean HEAD
`56b664fc44c359b0b97282aa2e116dbf9ed44ff9`, read only the PRD and
`dev/local/reviews/00004-workflow-core-v1-fast-review-02.md`, then reproduce the
eight roots before editing. Fix all three bundles as one cohesive rework, run
their focused real-filesystem/installed-command regressions and the complete
verification gate, commit, write
`dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/rework-02.md`, and
stop. Do not close or move the PRD and do not mutate autopilot state.

Any code change requires fresh `FT-04R3` review of the complete range
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..<new-head>` by isolated Alice,
Blake, and Bob. If a must-fix survives this final rework/review allowance, stop
with exact evidence for user decision.
