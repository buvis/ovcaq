# Cycle 13 repair report — PRD 00004-workflow-core-v1

Operator request: “Repair tasks 4–6 and prepare autocodex to resume.”

Repairs completed; hand off to fresh cycle 14 review. Rework cap remains 2. Batch 202609062243 and original work_start_sha b43bf2c94d5eb0fddafca55542ef2570b45e8d52 are preserved. All 16 tasks are complete. This work session did not run the mandatory PRD completion review.

## Changes and commits

- c1b9345787cfb0534d70d3a96fc905b414468b57: commit seven installed-wheel regression cases before implementation. All seven failed on unchanged production; all four replacement cases reached incorrect success after verified real replacement chronology.
- 6d5a306a22f2522e541ddb666608580ebd810331: task 4 retains the confirmed device/inode across each ancestor reopen, refuses replacements with a path-specific retry error, uses native search descriptors where available, skips existing-directory mkdir and omits root self-confirmation.
- fd728dfab366b77c7c025f460765dc4afd8b9211: task 4 patch-review retry makes fallback read-permission failures explain the durability requirement, retaining the path, errno and original cause.
- c11b054e620c1f14669136d7191c3fc6a7ac2627: task 5 requires exit 2, state_io, empty stdout and the exact report-specific publication busy message.
- e7d3fc40a0c1d7321639927d6f8cdff6ca0ede25: task 6 removes only the redundant child prefix/site-packages assertions and their unused prefix variable; parent checks and child filename/package guards remain.
- 7291d9f80c5b7a55f63c406552e5b3e27025acad: final format gate correction, one condition collapsed to one line. Python AST matches the full-suite-tested commit exactly.

## Work procedure and review

Task 4 used isolated Tess, Devon and Ivan native gpt-6-astra/xhigh agents, mapping the source procedure's logical Opus tier. Tess ran twice, Devon ran both mandated adversarial rounds, and Ivan implemented the fix plus a MEDIUM diagnostic retry and the final formatting correction. Every dispatch has a closed telemetry row. The prepared but undispatched Pat row cdfdcc86 was closed after correcting a duration typo before launch; it was not an extra model call.

Devon round 1 found a literal-name shortcut; generated names killed it. Round 2 found that the permanent tests still allow a mutant checking only the final two ancestors. The two-round cap was honored and this weakness is preserved in 00004-cycle-13-task4-devon-2.md. A separate installed-wheel probe at relative distances 3 and 5, direct and replay, verified that this implementation refuses the same replacement at those distances. The same four probes falsely succeeded on the baseline. These probes mitigate this concrete gap for the repair; they do not make the committed test suite exhaustive.

Tasks 5 and 6 passed the installed micro_lane_eligible predicate at claim time: one non-CRITICAL finding in one clean file each. Coordinator edits stayed below the ceiling (net -4 and -3 lines respectively). Tess/Devon/red checks were skipped by that explicit lane, and Pat was retained.

Pat used external Claude CLI with model argument sonnet and no tools, through the installed use-sonnet helper. Task 4: four original closures resolved; one MEDIUM fallback diagnostic finding was repaired; the delta review returned NO FINDINGS. Task 5: closure resolved, NO FINDINGS. Task 6: closure resolved, NO FINDINGS. The first task-4 review's LOW suggestion to rename the two local fstat values remains a naming note for fresh review; it was not retried under the LOW policy.

Reviewer sessions:
- task 4: 2c91f348-1493-48c0-9d35-f459247a547a
- task 5: ff0c2907-866b-4399-8136-3ff518680085
- task 6: afc6e167-c3fc-4e2e-94ba-84fa64b830fb

They can be resumed with the use-sonnet helper's -R session ID, or the latest Claude session with sonnet resume / claude --continue. No reviewer or implementor is left running.

4: style_gate: clean, split_hygiene: clean (initial repair); final format-only attempt split_hygiene: skipped:no-tests.
5: style_gate: clean, split_hygiene: clean.
6: style_gate: clean, split_hygiene: clean.
Self-deslop skipped by the explicit trivial-change rule: initial implementation net +23 in two files; subsequent task-4 commits each one file; tasks 5/6 micro lane. No reflow tripwire fired. No assumptions were added by this repair.

## Verification and limits

- New task-4 cases: 7 passed in 1.14s; after diagnostic retry, 7 passed in 1.20s.
- Task-5 controlled report overlap: 1 passed in 1.02s.
- Task-6 consumers and existing crash/peer cases: 11 passed in 1.95s.
- Full suite at e7d3fc4: 1359 passed in 25.19s, zero failures or skips.
- uv sync --all-groups, ruff check ., mypy src/ovcaq and uv build passed.
- ruff format --check . initially found one wrapped condition. The exact formatting-only correction was committed; rerunning that failed command passed: 123 files already formatted. An AST comparison proved the final change preserves Python behavior.
- Per the installed final-verification rule, only the failed command was rerun. last-verification.json names final HEAD but records null counts because the full-suite counts belong to the pre-format SHA. The fresh review should rerun the suite when it reads those null counts. Complete pre-format results are in 00004-cycle-13-verification-before-format.json.
- Cycle-13 queued verification checks were an empty array.
- Initial pytest runs emitted old temporary-directory cleanup warnings; dedicated basetemp runs and the full suite were clean.
- One shape-check invocation first used the wrong installed helper directory; it was rerun from review-work-completion/scripts and passed. The initial adversarial build environment could not locate hatchling; the corrected explicit project interpreter ran all mutant tests. Neither failed invocation is counted as a passing check.

The original installed-wheel failure probe now reports replacement_happened=true and status=refused, with a retryable identity error and no successful ledger return (00004-cycle-13-original-probe-after.json). Distant replacement evidence is in 00004-cycle-13-distant-before.json and -after.json.

The supported installed launcher sandbox command was:
mise exec -- codex sandbox -P :workspace --include-managed-config -C /Users/bob/git/src/github.com/buvis/ovcaq -- /Users/bob/git/src/github.com/buvis/ovcaq/.venv/bin/python /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/reviews/00004-cycle-13-sandbox-check.py

Before and after the ancestry fix, the sandbox denied a unique external-home write with EPERM and successfully ran source-checkout defer/stall/park, each with exactly one record. This used Codex 0.154.0's supported executor, workspace policy and managed configuration; no nested agent or stripped guards. It refutes the universal sandbox-failure suspicion for the currently installed launcher, not every historical version. See 00004-cycle-13-sandbox-before.json and -after.json.

Native macOS search-only access was tested as uid501 with real 0111 permissions. The forced O_RDONLY permission branch was also tested against real permissions, and readable fallback publication passed (00004-cycle-13-fallback-probe.json). Native Linux was not executed. Platforms without a fsync-capable search descriptor require read access for durable confirmation; the failure now says so. Linux O_PATH is a traversal handle rather than a replacement for a descriptor supporting filesystem I/O ([Linux open(2)](https://man7.org/linux/man-pages/man2/open.2.html)); required directory fsyncs remain enforced. No physical power loss was simulated.

## Recovery and evidence

All state changes use the installed statectl/transaction boundary. The guarded prepare-review script verifies 16/16 tasks, preserved unrelated tasks/batch, green commands and AST equivalence, then restores review origin while next_phase remains paused. The canonical phase-done --outcome rework atomically increments the cycle to 14 and clears rework_task_ids. It preserves cap 2 and the original work base. Final contract card and handoff point to fresh review, never in-session review.

The original cycle-13 review, raw session, external Bob receipt, prior pause handoff, pre-repair state/card/verification and autonomous-decision history remain intact. This repair does not certify cycle-14 PRD convergence; that requires all mandatory lenses in the next session.

Current-run scratch prompts, parsed inputs and attempt payloads are archived under 00004-cycle-13-repair-inputs/. Current-run disposable test/adversarial/schema trees are cleaned after verification. Historical scratch and review artifacts are preserved. No worktrees or branches were created.

## Existing assumption ledger (preserved verbatim)

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
