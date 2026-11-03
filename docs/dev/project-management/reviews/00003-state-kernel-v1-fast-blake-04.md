# Blake — blind PRD-only

## Verdict

pass

## Must fix

None.

## Can defer

None.

## PRD acceptance audit

1. **Integer serialization and revision rollover — pass.** Programmatic integers are bounded in both typed and open JSON fields (`src/ovcaq/state/schema.py:489-494`, `src/ovcaq/state/schema.py:523-535`). Accepted 640-digit values round-trip, while transaction and restore reject revision rollover before publication (`src/ovcaq/state/store.py:138-149`, `src/ovcaq/state/store.py:166-173`). Tests preserve state and backup bytes on overflow (`tests/state/test_store.py:662-748`). This satisfies total validation, monotonic revision, and failure-preservation requirements (`dev/local/prds/wip/00003-state-kernel-v1.md:54-70`).

2. **Non-regular artifacts and prompt fail-closed reads — pass.** State and backup paths receive pre-open `lstat` rejection for non-regular files, non-following/nonblocking opens, and post-open inode/type/link verification (`src/ovcaq/state/store.py:231-264`, `src/ovcaq/state/store.py:456-483`). FIFO, socket, and directory cases are tested without attempting a blocking open, and regular reads assert `O_NONBLOCK` (`tests/state/test_store.py:814-921`). This satisfies the PRD’s fail-closed-read requirement (`dev/local/prds/wip/00003-state-kernel-v1.md:67-71`).

3. **NaN/Infinity/-Infinity classification — pass.** The shared decoder rejects all three constants (`src/ovcaq/state/schema.py:433-451`). Inline and JSON-file paths translate decoder failures to `usage` (`src/ovcaq/cli.py:174-196`); durable state translates them to `state_io`, while restore wraps backup failures as `invalid_backup` (`src/ovcaq/state/store.py:266-295`). Boundary tests cover all three constants at all four locations and verify no mutation (`tests/state/test_cli_limits.py:67-177`). This satisfies total corrupt-input refusal and stable symbolic errors (`dev/local/prds/wip/00003-state-kernel-v1.md:54-57`, `dev/local/prds/wip/00003-state-kernel-v1.md:80-87`).

## Tests inspected or run

- Inspected the complete specified commit range and the focused schema, store, CLI, and protocol tests.
- Re-ran `git diff --check 9cda04a6a0279a6306c24015ee2d3173fb916e68..7b2e9776b6d03edcdfa2ca758c0c389024a903fe`; passed.
- Did not rerun pytest; coordinator evidence reports 883 passing tests and 33 passing focused repair cases at exact HEAD.

## Residual doubts

No verified defects.

Speculation: the suite asserts the pre-open rejection and `O_NONBLOCK` defenses separately rather than orchestrating a live regular-file-to-FIFO race. The implementation’s post-open identity/type verification closes that observed path, so this is not a change request.
