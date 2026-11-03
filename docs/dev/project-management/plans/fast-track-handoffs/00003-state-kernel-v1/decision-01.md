---
prd: dev/local/prds/wip/00003-state-kernel-v1.md
session: FT-03D
decision_kind: final-cycle-user-decision
date: 2026-08-28
head_sha: 296e757cb96007a8c2079b0c4015f836b4fe4c2b
decision: exceptional_bounded_rework_authorized
authorized_rework_cycles: 1
required_review_cycle: 4
---

# FT-03D final-cycle user decision handoff

## Decision

The user answered `yes` to the decision gate presented from clean HEAD
`296e757cb96007a8c2079b0c4015f836b4fe4c2b`.

This explicitly authorizes exactly one exceptional bounded rework followed by
one fresh mandatory three-lens review. The authorization is limited to the three
cycle-03 must-fix root causes reproduced in
`dev/local/reviews/00003-state-kernel-v1-fast-review-03.md`:

1. Enforce integer serialization closure for programmatic values and generated
   revision rollover so a successful publication is always readable.
2. Reject FIFO and other non-regular state/backup artifacts before any blocking
   open.
3. Reject `NaN`, `Infinity`, and `-Infinity` at the JSON decoder boundary with
   the documented symbolic and exit classifications for inline/file, durable
   state, and backup inputs.

## Bounds

- Start the exceptional rework in a fresh top-level session.
- Change only code, tests, and owned documentation necessary to close the three
  reproduced root causes and their directly required regression evidence.
- Run targeted regressions and the complete verification gate, commit the
  cohesive repair conventionally, and write `rework-03.md`; then stop.
- Start review cycle 04 in another fresh coordinator session and run Alice,
  Blake, and Bob in isolated contexts. The review evaluates these three repairs
  and regressions at the new head; it does not reopen deferred cycle-03 cleanup.
- No further rework cycle is authorized. If any authorized root cause remains,
  a gate fails, or the bounded repair introduces a reproduced contract defect,
  stop for another explicit user decision.
- Do not invoke `run-autopilot`, `autoclaude`, an autopilot state transition, or
  mutate `dev/local/autopilot/state.json`.
- Do not close or move PRD 00003 before the exceptional rework and fresh
  three-lens review converge.

## Session result

No rework was started in FT-03D. No code, tests, production documentation, PRD
lifecycle file, project capsule, or autopilot state was changed. This decision
handoff is the only session artifact.

## Next session and exact first action

Next session: `FT-03E — Exceptional bounded rework`.

From clean HEAD `296e757cb96007a8c2079b0c4015f836b4fe4c2b`, read the fast-track
plan, PRD 00003, the consolidated cycle-03 review, `review-03.md`, and this
decision handoff. Implement only the three authorized root-cause repairs and
their required regression evidence. Do not begin review cycle 04 in the rework
session.
