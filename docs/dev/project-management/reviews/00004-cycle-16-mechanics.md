## Mechanical facts (computed, do not re-count)

Function line counts from `ast`. Cite these for countable claims; a
finding that contradicts this block is discarded at the review gate.

- `src/ovcaq/workflow/_files.py`
  - `_require_basename` — line 43, 2 lines
  - `_require_operation_id` — line 47, 2 lines
  - `_canonical_record_bytes` — line 51, 4 lines
  - `_fsync_directory` — line 57, 6 lines
  - `_fsync_directory_descriptor` — line 65, 2 lines
  - `_serialize_deferred_publication` — line 70, 12 lines
  - `_validate_record_encoding` — line 84, 10 lines
  - `_write_record_file` — line 96, 42 lines
  - `_finish_record_publication` — line 140, 18 lines
  - `_publish_record_file` — line 160, 17 lines
  - `_read_record_file` — line 179, 8 lines
  - `_read_record_content` — line 189, 46 lines
  - `record_defer` — line 237, 14 lines
  - `_deferred_item` — line 253, 6 lines
  - `_sync_deferred_directory` — line 261, 4 lines
  - `_ensure_directory_chain` — line 268, 51 lines
  - `_ensure_directory_chain.verify_ancestry` — line 277, 13 lines
  - `_open_deferred_ledger` — line 322, 43 lines
  - `_open_deferred_ledger.verify` — line 356, 3 lines
  - `_lock_deferred_ledger` — line 368, 42 lines
  - `_lock_deferred_ledger.verify` — line 388, 13 lines
  - `_append_deferred_record` — line 412, 28 lines
  - `load_deferred_records` — line 442, 12 lines
  - `_open_lifecycle_directory` — line 457, 36 lines
  - `_verify_lifecycle_directory_identity` — line 495, 15 lines
  - `_artifact_stat` — line 512, 5 lines
  - `_validate_prd_artifact` — line 519, 4 lines
  - `_artifact_identity` — line 525, 4 lines
  - `_require_artifact_identity` — line 531, 6 lines
- `tests/packaging/rework_13_scripts.py` — no functions
- `tests/packaging/test_rework_12.py`
  - `_prepare` — line 24, 8 lines
  - `_state_bytes` — line 34, 7 lines
  - `_command` — line 43, 12 lines
  - `_invoke` — line 57, 16 lines
  - `_assert_confirmed` — line 75, 5 lines
  - `_assert_one_record` — line 82, 9 lines
  - `_actor` — line 94, 18 lines
  - `_await_event` — line 114, 12 lines
  - `_finish` — line 128, 9 lines
  - `test_installed_retry_and_replay_confirm_ancestry_after_abrupt_exit` — line 140, 26 lines
  - `test_installed_concurrent_creation_confirms_and_preserves_peer_directory` — line 169, 35 lines
- `tests/packaging/test_rework_13.py`
  - `_prepare` — line 26, 13 lines
  - `_state_bytes` — line 41, 3 lines
  - `_invoke` — line 46, 40 lines
  - `_ledger` — line 88, 2 lines
  - `_assert_one_record` — line 92, 7 lines
  - `_assert_replaced_after_confirmation` — line 101, 32 lines
  - `_assert_runtime_replaced_at_deferred_mkdir` — line 135, 29 lines
  - `_assert_runtime_replaced_during_publication` — line 166, 35 lines
  - `test_installed_defer_refuses_replaced_distant_ancestry_until_fresh_attempt` — line 207, 46 lines
  - `test_installed_defer_refuses_runtime_replacement_until_fresh_attempt` — line 261, 42 lines
  - `_assert_runtime_reparented_after_chain_confirmation` — line 305, 46 lines
  - `test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry` — line 357, 80 lines
  - `test_installed_defer_confirms_parent_through_native_search_only_access` — line 440, 37 lines
  - `test_installed_defer_refuses_execute_only_ancestor_without_search_descriptor` — line 480, 35 lines
  - `test_installed_defer_confirms_first_descendant_without_root_self_confirmation` — line 517, 28 lines
  - `test_installed_defer_avoids_creation_attempts_on_existing_external_ancestors` — line 547, 22 lines
- `CHANGELOG.md` — skipped (non-python)

## Tautological test shapes (computed, do not re-judge)

Each `[MECH]` line is a test whose shape cannot fail as written. Raise
it; step 6 adds any line the table lacks. `mech-check` is the finder.


Checked 9 test function(s) in 2 test file(s).

### Initial sandbox replay attempt
## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `7b41798c80e0`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

replay: skipped (worktree add failed: Preparing worktree (detached HEAD 7b41798)
fatal: could not create leading directories of '.git/worktrees/wt': Operation not permitted)

### Approved retry
## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `7b41798c80e0`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

[MECH] 🟡 2 touched test(s) pass against the pre-change code: test_installed_concurrent_creation_confirms_and_preserves_peer_directory | File: tests/packaging/test_rework_12.py | Task: general
[MECH] 🟡 10 touched test(s) pass against the pre-change code: test_installed_defer_refuses_replaced_distant_ancestry_until_fresh_attempt +4 more | File: tests/packaging/test_rework_13.py | Task: general

Replay: 18 touched test(s) ran, 6 failed against base, 12 passed; 0 test file(s) could not be collected at base (their tests fail there). Command: mise exec -- uv run pytest

