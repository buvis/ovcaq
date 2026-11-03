# FT-03R3 final convergence-review handoff

- PRD: `00003-state-kernel-v1`
- Session: `FT-03R3 — Final cycle-03 convergence review`
- Review cycle: `03`
- Base SHA: `9cda04a6a0279a6306c24015ee2d3173fb916e68`
- Reviewed/head SHA: `296e757cb96007a8c2079b0c4015f836b4fe4c2b`
- Complete range: `9cda04a6a0279a6306c24015ee2d3173fb916e68..296e757cb96007a8c2079b0c4015f836b4fe4c2b`
- Verdict: `changes_requested`
- Decision gate: `user_decision_required`

## Inputs read

- `AGENTS.md` and user-global instructions
- `dev/local/plans/fast-track-implementation-plan.md`
- `dev/local/plans/implementation-plan.md`
- `dev/local/prds/implementation-plan-coverage.md`
- `dev/local/prds/wip/00003-state-kernel-v1.md`
- `dev/local/designs/00003-state-kernel-v1-design.md`
- `dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/rework-02.md`
- cycle-02 consolidated review/handoff for carry-forward dispositions

The accepted implementation-plan digest matched
`43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
Work started from the exact clean requested head. The complete PRD range contains
28 changed files and 12,697 additions / 15 deletions.

## Canonical verification

- `mise exec -- uv sync --all-groups`: passed; 25 packages resolved, 24 checked.
- `mise exec -- uv run pytest`: passed; 850 tests in 9.28s.
- `mise exec -- uv run ruff check .`: passed.
- `mise exec -- uv run ruff format --check .`: passed; 75 files formatted.
- `mise exec -- uv run mypy src/ovcaq`: passed; 46 source files.
- `mise exec -- uv build`: passed; sdist and wheel built.
- `git diff --check <complete-range>`: passed.
- Focused hard-link matrix: 4 passed in 0.13s.
- Focused integer-limit/error-normalization matrix: 9 passed in 0.76s.
- Focused exact task-ID matrix: 32 passed in 0.16s.
- Focused injected `KeyboardInterrupt` matrix: 15 passed in 0.06s.
- Focused real-subprocess SIGINT regression: 1 passed in 0.04s.
- Full installed-CLI regression: 3 passed in 1.17s.
- Tracked worktree remained clean at
  `296e757cb96007a8c2079b0c4015f836b4fe4c2b` after verification and probes.

## Mandatory isolated lenses

All three mandatory lenses completed concurrently in isolated contexts with no
retry or fallback:

- Alice — consensus/architecture: `pass`.
- Blake — blind/PRD-only: `changes_requested` with two must-fix claims.
- Bob — doubt and de-slop, full R1–R5: `changes_requested` with one must-fix
  claim.

Artifacts:

- `dev/local/reviews/00003-state-kernel-v1-fast-alice-03.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-blake-03.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-bob-03.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-review-03.md`

## Consolidated outcome

The coordinator independently reproduced three must-fix root causes:

1. Programmatic integers longer than 640 digits pass schema/service/store
   validation and publish successfully, but immediate reads and restores reject
   the committed bytes. The store also rolls a readable 640-digit revision into
   an unreadable 641-digit revision on a successful transaction.
2. A FIFO substituted for `state.json` blocks `StateStore.read()` before the
   post-open regular-file check; the 0.5-second coordinator probe timed out.
   Backup reads use the same blocking path.
3. `NaN` is accepted by Python's JSON decoder and classified as `invalid_state`
   for both inline and durable inputs, rather than the documented `usage` and
   `state_io` symbolic errors. `Infinity` and `-Infinity` use the same decoder
   path.

The final-rework hard-link, textual integer, exact task-ID, injected interrupt,
real SIGINT, and installed-wheel regressions all converge. The new findings are
adjacent untested boundaries and are not dismissed by the green canonical gate
or Alice's pass.

## Decision rule

This was the final allowed rework/review cycle. Because reproduced must-fix
findings survive after two reworks, the fast-track plan forbids an automatic
third rework. Stop for explicit user direction. Do not create a rework-03
bundle, edit code, or proceed to closeout under the current contract.

PRD 00003 remains in `wip`. No code, tests, production documentation, PRD
lifecycle file, project capsule, or `dev/local/autopilot/state.json` was changed
by the coordinator. No autopilot skill, command, wrapper, or state transition
was invoked.

## Known risks and deferred items

- Task dependency-cycle policy belongs to PRD 00004.
- Real SIGKILL is not repeated specifically for restore, but restore shares the
  tested publication path and has exhaustive injected-boundary coverage.
- Crosswalk derived-wording ambiguity, unconfirmed runtime pathname TOCTOU, and
  Bob's concrete test/doc abstraction slop remain deferred and non-blocking.
- Closeout is blocked by the three reproduced root causes unless the user
  explicitly revises the cycle budget or acceptance contract.

## Next session and exact first action

Next session: `FT-03D — Final-cycle user decision`.

First action: from clean HEAD
`296e757cb96007a8c2079b0c4015f836b4fe4c2b`, read the consolidated cycle-03
review and this handoff, present the three exact reproduced root causes, and ask
the user whether to authorize one exceptional bounded rework/review cycle or
provide different explicit contract/closeout direction. Do not change code or
PRD lifecycle state before that decision.

### Next-session prompt

```text
Execute the fast-track plan from:

    dev/local/plans/fast-track-implementation-plan.md

Start a fresh FT-03D final-cycle user-decision session for PRD 00003. Read:

    dev/local/prds/wip/00003-state-kernel-v1.md
    dev/local/reviews/00003-state-kernel-v1-fast-review-03.md
    dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/review-03.md

At clean HEAD 296e757cb96007a8c2079b0c4015f836b4fe4c2b, present the three
cycle-03 must-fix root causes and their exact coordinator reproductions:
programmatic/rollover integers can publish unreadable state; FIFO state/backup
artifacts can block before regular-file validation; and NaN/Infinity JSON
constants receive incorrect stable symbolic errors.

This was the final allowed rework/review cycle. Do not start a third rework,
edit code, close or move the PRD, invoke run-autopilot/autoclaude, or mutate
dev/local/autopilot/state.json without explicit user direction. Ask one concise
decision question: whether to authorize one exceptional bounded rework plus a
fresh three-lens review for only these reproduced root causes, or provide
different explicit contract/closeout direction. Record the decision in a new
handoff and stop.
```
