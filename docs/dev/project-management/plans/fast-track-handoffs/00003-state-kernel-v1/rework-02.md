# FT-03F2 final convergence-rework handoff

- PRD: `00003-state-kernel-v1`
- Session: `FT-03F2 — Final convergence rework`
- Rework cycle: `02`
- Base SHA: `ff00f1f5b848043293ee8d92fbd11d0d38053738`
- Head SHA: `296e757cb96007a8c2079b0c4015f836b4fe4c2b`
- Commit: `296e757 fix(state): close final convergence gaps`
- Complete next-review range:
  `9cda04a6a0279a6306c24015ee2d3173fb916e68..296e757cb96007a8c2079b0c4015f836b4fe4c2b`

## Inputs read

- `dev/local/plans/fast-track-implementation-plan.md`
- `dev/local/prds/wip/00003-state-kernel-v1.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-review-02.md`
- `dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/review-02.md`

PRD 00002 remained the completed dependency. Work started from the exact clean
requested base. No autopilot command, skill, wrapper, saved task list, or state
transition was invoked.

## Source IDs covered

- `P01-T02`: bounded JSON integer conversion and total decoder failure
  normalization.
- `P01-T03`, `P01-T04`, `P01-T06`: multi-link rejection and
  interrupt-safe initialization, transaction, restore, repair, and repair fsync.
- `P01-T08`: exact task-ID validation at every compound service boundary.
- `P01-T10`: stable state, backup, inline/file payload, and installed-CLI
  symbolic failures.
- `P01-T12`: real-subprocess SIGINT repair evidence in addition to injected
  boundary coverage.

## Files changed

- `src/ovcaq/state/schema.py`
- `src/ovcaq/state/store.py`
- `src/ovcaq/state/commands.py`
- `src/ovcaq/cli.py`
- `docs/state-protocol.md`
- `tests/state/test_store.py`
- `tests/state/test_store_transactions.py`
- `tests/state/test_durability.py`
- `tests/state/test_service_commands.py`
- `tests/state/test_cli_limits.py`
- `tests/state/test_installed_state.py`
- `tests/state/test_schema_invariants.py`
- `tests/state/test_schema_limits.py`

## Behavior completed

1. State, backup, and lock artifacts must have exactly one hard link. Both the
   pathname observation and opened descriptor are checked before reading,
   chmod, rotation, restore, or publication. State reads, backup rotation,
   backup restore, and lock permission cases preserve external-alias bytes,
   mode, atime, mtime, inode, and link count.
2. JSON integer literals are explicitly capped at 640 digits before `int`
   conversion. Positive and negative boundary literals remain valid.
   Oversized durable state is `resource_limit`; oversized backup JSON is
   `invalid_backup`; inline and JSON-file inputs are `resource_limit`.
   Decoder `ValueError` failures cannot leak as raw tracebacks or accidental
   `usage` failures.
3. Supplied task IDs, blocker IDs, and every ID-taking task service method
   require `type(value) is int` before opening a transaction. Booleans,
   floats, integer subclasses, and equality aliases preserve state, backup,
   lock bytes, and revision.
4. Initialization publication and paired transaction/restore publication now
   repair on `BaseException`, fsync repaired directory state, clean temporary
   files, and re-raise `KeyboardInterrupt`. The injected matrix covers all
   three initialization boundaries and all six transaction/restore boundaries.
   A real child process interrupted with `SIGINT` at
   `BACKUP_REPLACED` proves exact backup repair before interrupt exit.

## RED/GREEN evidence

- Initial focused RED matrix: 45 failed / 3 passed. It reproduced all four
  consolidated root causes; the three passing cases were pre-publication
  interrupt boundaries that already changed no durable bytes.
- Initial installed-wheel RED:
  `test_installed_cli_normalizes_oversized_durable_integer` failed with
  `usage`/1 instead of `resource_limit`/11.
- Focused GREEN matrix: 52 passed.
- Exact-type service expansion: 32 passed, including integer subclasses.
- Installed-wheel GREEN regression: 1 passed.
- Final post-commit state/service/durability/CLI matrix:
  `mise exec -- uv run pytest tests/state` — 778 passed in 7.82s.

## Canonical verification

- `mise exec -- uv sync --all-groups`: passed; 25 packages resolved, 24
  checked.
- `mise exec -- uv run pytest`: passed; 850 tests in 9.24s.
- `mise exec -- uv run ruff check .`: passed.
- `mise exec -- uv run ruff format --check .`: passed; 75 files already
  formatted.
- `mise exec -- uv run mypy src/ovcaq`: passed; 46 source files.
- `mise exec -- uv build`: passed; sdist and wheel built.
- `git diff --check`: passed.
- Tracked worktree after commit: clean at
  `296e757cb96007a8c2079b0c4015f836b4fe4c2b`.

## Decisions

- The 640-digit ceiling matches Python's minimum configurable integer-string
  threshold, so accepted boundary conversion is independent of the runtime's
  larger default while remaining far above every state-domain integer.
- Link count is enforced both before open and after descriptor acquisition;
  the second check closes the pathname/open race already covered for symlinks
  and inode identity.
- Publication cleanup catches `BaseException` only to restore invariants and
  then re-raises the original interrupt; the CLI does not convert or swallow
  `KeyboardInterrupt`.
- Task IDs are exact built-in integers, not merely equality-compatible values.
  Defensive lookup validation remains in addition to public preflight.

## Known risks and limits

- This is the final allowed rework cycle. If cycle-03 reproduces any must-fix,
  stop with exact evidence for a user decision; do not start another rework
  loop.
- Review-02's deferred crosswalk wording, unconfirmed runtime pathname TOCTOU,
  and non-blocking test/documentation slop remain deferred. This session did not
  expand scope into those observations.
- PRD 00003 remains in `wip`. This session did not review, close, move, or edit
  it and did not refresh the project capsule.
- `dev/local/autopilot/state.json` remained frozen and was not mutated.

## Next session and exact first action

Next session: `FT-03R3 — Final cycle-03 convergence review coordinator`.

First action: from clean HEAD
`296e757cb96007a8c2079b0c4015f836b4fe4c2b`, pin the complete PRD range
`9cda04a6a0279a6306c24015ee2d3173fb916e68..296e757cb96007a8c2079b0c4015f836b4fe4c2b`,
rerun canonical verification, then dispatch isolated Alice, Blake, and Bob
concurrently over that complete range.

### Next-session prompt

```text
Execute the fast-track plan from:

    dev/local/plans/fast-track-implementation-plan.md

Start a fresh FT-03R3 final cycle-03 convergence-review coordinator session for
PRD 00003. Read:

    dev/local/prds/wip/00003-state-kernel-v1.md
    dev/local/plans/fast-track-handoffs/00003-state-kernel-v1/rework-02.md

From clean HEAD 296e757cb96007a8c2079b0c4015f836b4fe4c2b, review the complete
updated PRD range:

    9cda04a6a0279a6306c24015ee2d3173fb916e68..296e757cb96007a8c2079b0c4015f836b4fe4c2b

Rerun the complete canonical PRD verification gate and the focused hard-link,
integer-limit/error-normalization, exact task-ID, injected KeyboardInterrupt,
real-subprocess SIGINT, and installed-CLI regressions. Then dispatch all three
mandatory lenses concurrently in isolated contexts:

- Alice receives AGENTS.md, the accepted plan, PRD, relevant design artifact,
  complete diff, and verification evidence.
- Blake receives only the PRD, complete diff, and verification evidence; do not
  provide implementation handoffs, design rationale, earlier reviews, or other
  reviewers' output.
- Bob receives AGENTS.md, the PRD, complete diff, and verification evidence and
  applies the full R1-R5 doubt/de-slop rubric.

Save the raw reports as cycle-03 Alice, Blake, and Bob artifacts and write the
consolidated cycle-03 review plus review-03 handoff. The coordinator performs no
code edits and must not close or move the PRD. This is the final allowed
rework/review cycle: if any must-fix is reproduced or survives, stop with exact
evidence for a user decision and do not start a third rework. If all three
lenses converge with no must-fix, hand off to a fresh closeout session. Do not
invoke run-autopilot, autoclaude, or mutate
dev/local/autopilot/state.json. Print the next-session prompt and stop.
```
