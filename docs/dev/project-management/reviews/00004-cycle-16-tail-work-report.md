# Cycle 16 tail work return — PRD 00004

Task 11 completed the seven actionable Medium/Low findings from the converging review. All 21 tasks are completed. Final code HEAD: `2742c08fe5f8194f65a36fa1e49a5980d69c16ef`. No unresolved tail finding or queued verification escape remains.

## Changes and commits

- `80d549f8f677c48e9848eab166aef9ccc88e11d5`: Tess's diagnostic regressions committed before implementation.
- `92c60bc5479d556cb8515a7fa3c88d7a5560c0a5`: full-path creation diagnostics with the original OS error as cause; named ancestry-verifier extraction; shorter installed-wheel regression helpers; stdlib timeout handling; definite no-ledger assertion on direct refusal; changelog entry.
- `2742c08fe5f8194f65a36fa1e49a5980d69c16ef`: corrected three new test assertions to the verified public `<batch_id>-deferred.json` name after a coordinator-supplied interface error.

The publication, locking, fsync chronology, direct/replay cases at ancestor distances 1/3/5, and installed-module-origin checks remain covered.

## Dispatch and gates

Task tier: logical sonnet, classifier reason default, lean pipeline. Seven findings excluded the micro lane. Qwen was excluded by the implementation file set. Source doctor-first returned unhealthy (two empty Codex hook targets); no external implementation interception or nested Codex CLI ran. The host-mapped native fallback used actual OpenAI `gpt-5.6-sol`, recorded as implementor `codex`. See [routing evidence](00004-cycle-16-tail-routing.md).

Tess ran in an isolated native Sol context, with two bounded quality corrections. Ivan and the fresh self-deslop reviewer also ran as isolated native Sol agents. All returned and every dispatch telemetry row is closed. Devon was correctly omitted for the source's sonnet tier.

The initial behavioral red check was 3 failed / 3 passed, with failures confined to the intended creation-error diagnostic mismatch. After implementation and the ledger-name correction, the six diagnostic cases passed. Both runs and their full output are preserved in the cycle evidence.

11: style_gate: clean, split_hygiene: clean

self_deslop: noop — the fresh reviewer reported `no slop found`. Measured modified function spans are all at most 47 lines; [AST evidence](00004-cycle-16-tail-function-spans.json).

## Pat closure review

Actual reviewer: Claude `claude-sonnet-5`, requested alias sonnet, no tools, fresh session `f720ee31-d14d-4dd7-aee8-a9706cbbf630`. The initial dispatch failed at quota, producing no review. Its output and telemetry remain unchanged. The single runner retry was dispatched after 2026-09-14 00:10:05 UTC, with the complete current diff and all seven findings.

The retry exited 0; the installed parser exited 0 and returned seven resolved CLOSURE verdicts. Raw output: [Pat retry](pat-output-00004-16-task-11-retry.txt). Parsed result, provider evidence and adjudication: [Pat result](00004-cycle-16-pat-result.json).

Both new LOW notes were discarded after checking the source:

- The supposedly unused `previous_runtime` parameter is used by `assert identity(runtime) == previous_runtime` at `tests/packaging/test_rework_13.py:398`.
- The supposedly wrong `tuple[bytes, bytes]` annotation matches `_state_bytes`, which returns state and backup bytes at lines 41–43.

No repair or extra review cycle was needed. The reviewed PRD snapshot remains `4011d1a`; Alice's, Blake's and Bob's raw rubric verdicts remain unchanged in the consolidated review. Bob's immutable successful Claude Opus receipt remains valid.

## Final verification

All commands ran once at final HEAD `2742c08fe5f8194f65a36fa1e49a5980d69c16ef`:

| Command | Exit |
|---|---|
| `mise exec -- uv sync --all-groups` | 0 |
| `mise exec -- uv run pytest` | 0 |
| `mise exec -- uv run ruff check .` | 0 |
| `mise exec -- uv run ruff format --check .` | 0 |
| `mise exec -- uv run mypy src/ovcaq` | 0 |
| `mise exec -- uv build` | 0 |

Runner summary: **1378 passed, 2 warnings in 27.84s**. Zero failures or skips. The warnings concern pytest garbage-directory cleanup (`ENOTEMPTY`), not test failures. [Full command output](00004-cycle-16-tail-verification.json) is preserved; `last-verification.json` contains this exact HEAD and the six exit codes. Cycle-16 queued checks are an empty array.

## Cleanup and handoff

Archived 35 completed dispatch inputs from `dev/local/tmp` into [the cycle input archive](00004-cycle-16-inputs/manifest.json), with original paths, byte sizes and SHA-256 hashes. Bob's raw log, output and receipt remain at their original immutable paths. The repository has one worktree and one branch, with a clean working tree. No executed plan was created in `dev/local/plans`; the accepted implementation plan remains active architecture authority.

Work returns to the converged cycle-16 review gate. The coordinator must commit the canonical `review -> done` transition, write its handoff card and leave row, then end this session. Finalization belongs to a fresh process.

## Assumption ledger

The existing per-plan ledger is retained and appended in rework mode:

# Task 1 — Define the clean v1 state schema and 184-field crosswalk

- Assignment-style typing aliases use `typing` as `__module__`; schema origin is verified by namespace identity.
- Meaningful crosswalk rationales contain at least three word tokens and 12 characters.
- Inline Markdown code spans are presentation-only when crosswalk targets are compared semantically.

# Task 2 — Implement total nested and cross-field validation

- Invalid v1 values raise `SchemaError`, a `ValueError` subclass, with the first full dotted path and a bounded offending-value representation.
- List indexes render as `[n]`; map keys render as dotted path components.
- Named maximums are inclusive, so values exactly at a limit are valid.
- Timestamp ordering is nondecreasing; adjacent attempts may meet at the same instant.

# Task 3 — Port the sole locked StateStore transaction boundary

- The public exception surface is `StateError`, `StateIOError`, `StateExistsError`, `BackupError`, `FutureSchemaError`, `RevisionConflictError`, and `DurabilityUnsupportedError`; durability-unsupported errors are state I/O errors.
- `DurabilityBoundary.BACKUP_REPLACED` denotes completed backup publication and is a deterministic repair failpoint.
- Directory fsync remains a hard durability gate; unsupported or failed directory fsync is never swallowed.

# Task 4 — Add file and directory fsync publication guarantees

- Store-owned stale temporary files match `.state.json.ovcaq-*.tmp` exactly.
- Create-only initialization emits the state replacement durability boundary.
- P01-T03 already supplied the complete P01-T04 production behavior, so this task legitimately added only dedicated durability coverage.

# Task 5 — Add monotonic revision and compare-and-set conflicts

- Boolean, negative, and other non-integer `expected_revision` values use the store's single compare-and-set failure surface, `RevisionConflictError`.
- Revision expectations are validated and compared only after the exclusive sidecar lock is held.

# Task 6 — Finish create-only init, raw backup, and validated restore

- StateStore requires an existing parent directory and never creates or chmods it; project-level initialization owns runtime-directory provisioning.
- When create-only publication succeeds and a later step fails, the store removes only the state created by that call and directory-fsyncs the repair before re-raising.
- A repair directory-fsync failure propagates; durability failures are never swallowed.

# Task 7 — Port generic JSON-path recovery operations

- Path error-message wording is not public contract; invalid grammar, traversal, bounds, and root mutations share `ValueError`.
- Decimal index digits preserve the source parser's `str.isdigit()` behavior, including Unicode decimal digits accepted by `int()`.
- The module remains pure and leaves whole-state validation to the state-store transaction boundary.

# Task 8 — Implement compound task, attempt, and contract-card commands

- Omitted task-create fields use closed-schema neutral defaults: empty description/active form and dependencies, null routing/count metadata, empty estimates/metadata, pending status, and no attempts.
- `clear_tasks()` also clears `review.rework_task_ids` atomically so the command always proposes a valid state rather than refusing when dependent references exist.
- `set_task_body()` replaces `tasks[].description` verbatim; command-domain failures use `ValueError`, while revision conflicts retain `RevisionConflictError`.

# Task 9 — Protect transition-owned paths and require explicit unsafe recovery

- Ownership protection failures use `ValueError`; parsed token sequences, not raw spelling, determine whether a path is a strict extension descendant.
- Extension namespace keys continue to use the schema's slash-delimited lowercase/digit/hyphen contract.
- Protected paths are rejected before a transaction; accepted and unsafe paths retain the full store transaction, schema, revision, backup, and durability boundary.

# Task 10 — Implement the installed init/state CLI and stable output contract

- Directory `fsync` raising `EINVAL` uses the store's typed unsupported-durability error and maps to exit 10.
- JSON initialization reports revision 0 with a null result; restore increments from the current revision while restoring the prior backup snapshot.
- Only `DurabilityUnsupportedError` maps to durability-unsupported; other state I/O failures map to `state_io`.
- The initial assumption that `--json` wrapped successful reads was corrected during review: requested show/get/validate data remains raw JSON, while the success envelope is mutation-only.
- With no OVCAQ marker and no Git top level, project-root discovery falls back to the absolute current directory.
- The final-verification retry's explicit failing-file target authorized the formatter-only edit to Tess-authored `tests/state/test_commands.py`, which was absent from Ivan's original production-file allowlist.

# Review rework task 14 — Harden CLI payloads and error typing

- Well-formed non-object task JSON uses the existing symbolic `usage` error contract established for malformed JSON payloads.

# Review rework task 17 — Complete the state service and protocol contract

- Field constraints accompany each backticked `Owner.field` on the same documentation line.
- Each symbolic error and numeric exit code share a documentation line.

# Review rework task 18 — Make project initialization retry-safe and metadata-safe

- The test filesystem honors POSIX owner write permissions.

# Review rework task 7 — Bind confirmed ancestry through ledger publication

- Ancestor distance 1 means `runtime_root.parent`; distance-3 and distance-5 regressions therefore use `runtime_root.parents[2]` and `runtime_root.parents[4]`.
- Exact replay simulates a concurrent missing deferred entry before the real directory-creation race boundary.
- Opening the batch ledger is the externally observable start of the ledger-publication window.
## 11: [D16] Close deferred diagnostic and regression cleanup tail

- Tess treated `os.open` and `os.mkdir` as external filesystem boundaries suitable for failure injection.
- Tess matched descriptor-relative deferred paths by the runtime directory's `(st_dev, st_ino)` identity, allowing either absolute or `dir_fd`-relative calls.
- The coordinator initially supplied the wrong ledger filename in Tess's interface context. It was corrected to the verified public `<batch_id>-deferred.json` name before task closure; all three assertions now use that name.
- Ivan and the final Tess correction reported no further assumptions.
