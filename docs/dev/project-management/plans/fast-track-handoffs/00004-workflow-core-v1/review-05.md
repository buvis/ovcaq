# FT-04R5 isolated cycle-05 review handoff

- PRD: `00004-workflow-core-v1`
- Session: `FT-04R5 — fresh isolated cycle-05 review`
- Review cycle: `05`
- Date: `2026-09-04`
- Base SHA: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`
- Reviewed/head SHA: `c512a4ad7d67af75b413ee8c9612b088d21fb4f4`
- Complete range:
  `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c512a4ad7d67af75b413ee8c9612b088d21fb4f4`
- Verdict: `changes_requested`
- Decision gate: `user_direction_required`
- Closeout ready: `false`
- Must-fix root causes: `3`
- Authorized follow-on rework: `none`

## Authorization and inputs

The user authorized a fresh isolated review from exact clean HEAD. The
coordinator read AGENTS, PRD 00004, fast-review-04, rework-04, the complete
range implementation/tests, and the mandatory source-contract inputs. Review
covered all 40 changed files and 6,094 additions / 33 deletions, not only
FT-04F4.

The accepted implementation plan remained byte-identical at SHA-256
`43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
Frozen autopilot state remained byte-identical at SHA-256
`ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f`.

## Fresh verification

- `mise exec -- uv sync --all-groups`: passed; 25 resolved / 24 checked.
- `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/packaging/test_installed_cli.py -q`: passed; 50 tests in 2.03s.
- `mise exec -- uv run pytest`: passed; 1,095 tests in 11.24s.
- `mise exec -- uv run ruff check .`: passed.
- `mise exec -- uv run ruff format --check .`: passed; 92 files formatted.
- `mise exec -- uv run mypy src/ovcaq`: passed; 47 source files.
- `mise exec -- uv build`: passed; sdist and wheel built.
- `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c512a4ad7d67af75b413ee8c9612b088d21fb4f4`: passed.
- Focused FT-04F3/FT-04F4 closure matrix: 27 passed / 97 deselected in 1.49s.

No verification failure was waived.

## Mandatory isolated lenses

All required lenses completed with distinct read-only packets and raw reports:

- Alice — consensus/architecture: `changes_requested`; three raw findings, with
  the characterized metrics/report migration gap promoted.
- Blake — blind PRD-only: `changes_requested`; three raw findings, none promoted
  after source-boundary reconciliation.
- Bob — doubt and de-slop: `changes_requested`; all six doubt questions and
  explicit R1–R5 results completed (`R1–R4 fail`, `R5 pass`); the reproduced
  control-character report failure was promoted.

No reviewer received prior review/rework conclusions, commit messages/logs,
coordinator findings, or another lens's output. No lens was omitted, merged,
substituted, or thinned.

Artifacts:

- `dev/local/reviews/00004-workflow-core-v1-fast-alice-05.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-blake-05.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-bob-05.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-review-05.md`

## FT-04F4 and retained FT-04F3 result

1. **Lifecycle-directory identity loss is not fully closed.** The new
   device/inode checks correctly reject WIP/hold rename-away at the after-intent
   boundary. They stop after `intent -> moved`. Coordinator real-filesystem
   reproductions renamed configured hold away at `AFTER_MOVE_BEFORE_APPEND` and
   `AFTER_APPEND_BEFORE_COMMIT`; both commands returned success, wrote the
   ledger, cleared recovery, reset tasks, and left the PRD only in relocated
   hold.
2. **Competing public state mutations are closed.** All thirteen mutating
   `StateService` paths, including restore, check active recovery under the
   state-store lock. Unit, saga, and installed-wheel tests prove rejection,
   exact byte/revision preservation, and successful later reconciliation.
3. **FT-04F3 durability is retained.** Lifecycle and deferred-record directory
   fsyncs still complete before the corresponding state advance.
4. **FT-04F3 recovery-kind identity is retained.** Durable `kind` continues to
   control exact replay and park-breaker behavior; both collision directions
   fail closed.

## Consolidated outcome

Three concrete roots block convergence:

1. Later saga boundaries can lose configured hold identity after the new checks
   end, yet still clear recovery and erase live PRD work.
2. P02-T08's frozen migration rows for state-plus-metrics report rendering and
   loop-metrics rendering were not ported. The retained three-row metrics
   fixture has no consumer; current renderers accept only state and deferred
   records and cannot emit wall time, cost, or token metrics.
3. Schema-valid newline identifiers inject report headings and cause
   `publish_report()` to raise `StopIteration`.

Frontmatter policy persistence, active-tier/config injection, review-cap
enforcement, defer/state linearization, successful PRD movement, and outcome
cross-validation remain in their previously settled later-runtime/caller or
nonblocking-hardening scope. Bob's R1–R4 cleanup findings are concrete but do
not block acceptance; R5 passed.

## Verdict, closeout readiness, and stop

Verdict: **changes requested**. `closeout_ready` is false. P02-T07 and P02-T08
do not pass at the reviewed head despite the green gate and the closed public
mutation fence.

This review-only session authorizes no repair. PRD 00004 remains in `wip`; no
implementation/test change, autopilot mutation, implementation-plan edit, PRD
move/closeout, capsule refresh, or next-PRD work was performed. Stop for
explicit user direction.
