# FT-04R4 exceptional convergence-review handoff

- PRD: `00004-workflow-core-v1`
- Session: `FT-04R4 — fresh isolated cycle-04 review`
- Review cycle: `04`
- Date: `2026-09-03`
- Base SHA: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`
- Reviewed/head SHA: `e8fe191089d91140343e6246dffe66caf9caa6a9`
- Complete range:
  `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..e8fe191089d91140343e6246dffe66caf9caa6a9`
- Verdict: `changes_requested`
- Decision gate: `user_direction_required`
- Closeout ready: `false`
- Must-fix root causes: `2`
- Authorized follow-on rework: `none`

## Authorization and inputs

The user authorized this fresh isolated review after FT-04F3. Work started from
the exact clean requested head and reviewed the complete PRD range, not only the
repair commit.

Inputs read by the coordinator:

- `AGENTS.md` and user-global instructions
- `dev/local/plans/fast-track-implementation-plan.md`
- `dev/local/plans/implementation-plan.md`
- `dev/local/prds/implementation-plan-coverage.md`
- `dev/local/discovery/00001-ovcaq-v1.md`
- `dev/local/prds/wip/00004-workflow-core-v1.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-review-03.md`
- `dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/rework-03.md`
- the complete range diff, current implementation, and relevant tests

The accepted implementation-plan digest matched
`43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
The frozen autopilot state remained byte-identical at
`ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f`.
The complete range contains 36 changed files and 5,669 additions / 15
deletions.

## Fresh verification

- `mise exec -- uv sync --all-groups`: passed; 25 resolved / 24 checked.
- `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/packaging/test_installed_cli.py -q`: passed; 44 tests in 1.68s.
- `mise exec -- uv run pytest`: passed; 1,076 tests in 10.88s.
- `mise exec -- uv run ruff check .`: passed.
- `mise exec -- uv run ruff format --check .`: passed; 92 files formatted.
- `mise exec -- uv run mypy src/ovcaq`: passed; 47 source files.
- `mise exec -- uv build`: passed; sdist and wheel built.
- `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..e8fe191089d91140343e6246dffe66caf9caa6a9`: passed.
- Focused FT-04F3 closure matrix: 8 passed / 36 deselected in 2.37s.

No verification failure was waived.

## Mandatory isolated lenses

All three required review lenses completed read-only with the established
packet boundaries:

- Alice — consensus/architecture: `changes_requested`; her two raw blockers
  remain in explicitly deferred next-PRD and tier-map scope.
- Blake — blind PRD-only: `changes_requested`; independently reproduced the
  promoted lifecycle-directory identity failure.
- Bob — doubt and de-slop: `changes_requested`; completed all six doubt
  questions and R1–R5 (`R1–R4 fail`, `R5 pass`) and independently reproduced the
  promoted competing-state-mutation loss.

Alice, Blake, and the initial Bob context were launched concurrently. The first
Bob context did not return after two completion requests and was interrupted.
The required fresh fallback received the identical isolated Bob packet and
returned the complete report. No lens received prior review/rework artifacts or
another lens's output, and no lens was omitted or merged.

Artifacts:

- `dev/local/reviews/00004-workflow-core-v1-fast-alice-04.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-blake-04.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-bob-04.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-review-04.md`

## FT-04F3 closure audit

Both requested repair roots close for their exact contracts:

1. Hold/deferred creation fsyncs the directory owning each new entry; already-
   moved replay fsyncs both WIP and hold descriptors before `intent -> moved`;
   exact deferred-record replay fsyncs the record directory before
   `moved -> recorded`. Controlled post-rename/post-replace interruptions and
   the eight-test closure matrix pass.
2. Recovery `kind` is durable in intent and records, controls exact replay and
   park-breaker behavior, and no longer derives from `wrapper_died`. Exact
   stall/park retries and both cross-kind collision directions pass at service
   and installed-command boundaries with unchanged bytes.

## Consolidated outcome

Two high-severity recovery roots block convergence:

1. An already-open lifecycle descriptor can be renamed away from its configured
   pathname. The saga then moves and fsyncs through the relocated descriptor,
   clears recovery, and reports success while the PRD is absent from configured
   WIP and hold. Blake and the coordinator reproduced this on a real temporary
   filesystem.
2. Ordinary public state mutations are not fenced by active recovery. A task
   addition committed after durable intent, then replay erased both tasks and
   cleared recovery. Bob and the coordinator independently reproduced the data
   loss.

These are concrete new complete-range findings. The first invalidates the
earlier after-intent directory-substitution closure for rename-away; the second
invalidates the broad statement that active recovery fences competing
mutations. Neither broadens configuration, tier-map, supervisor, cap-policy,
successful PRD-move, or next-PRD scope.

Successful WIP-to-done movement/successor activation, retained `work.prd`,
configuration/tier injection, cap enforcement, installed-wheel matrix depth,
and other reviewer cleanup remain deferred under the established scope. No
deferred fast-review-03 claim was promoted without new invalidating evidence.

## Verdict, closeout readiness, and stop

Verdict: **changes requested**. `closeout_ready` is false. P02-T07 and the
park/stall recoverability acceptance criterion do not pass at the reviewed
head, despite the green gate and the two exact FT-04F3 closures.

This review session does not authorize another repair cycle. PRD 00004 remains
in `wip`; no code/test change, autopilot mutation, plan edit, PRD move, capsule
refresh, closeout, or next-PRD work was performed. Stop for explicit user
direction.

If the user authorizes another bounded exception, the next fresh session should
receive only this consolidated review, the PRD, and the repository; repair the
two promoted recovery roots together, run targeted and full gates, commit, write
a rework handoff, and stop for another fresh three-lens review. Do not treat this
sentence as authorization.
