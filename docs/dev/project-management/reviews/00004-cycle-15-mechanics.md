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
  - `_ensure_directory_chain` — line 268, 29 lines
  - `_open_deferred_ledger` — line 300, 48 lines
  - `_open_deferred_ledger.verify_runtime` — line 308, 9 lines
  - `_open_deferred_ledger.verify` — line 339, 3 lines
  - `_lock_deferred_ledger` — line 351, 42 lines
  - `_lock_deferred_ledger.verify` — line 371, 13 lines
  - `_append_deferred_record` — line 395, 28 lines
  - `load_deferred_records` — line 425, 12 lines
  - `_open_lifecycle_directory` — line 440, 36 lines
  - `_verify_lifecycle_directory_identity` — line 478, 15 lines
  - `_artifact_stat` — line 495, 5 lines
  - `_validate_prd_artifact` — line 502, 4 lines
  - `_artifact_identity` — line 508, 4 lines
  - `_require_artifact_identity` — line 514, 6 lines
- `tests/packaging/packaging_support.py`
  - `_module_member` — line 82, 5 lines
  - `assert_installed` — line 108, 8 lines
  - `identity` — line 118, 3 lines
  - `initialize_installed_state` — line 123, 17 lines
  - `command_text` — line 142, 2 lines
  - `run_checked` — line 146, 21 lines
  - `isolated_environment` — line 169, 20 lines
  - `_run` — line 191, 12 lines
  - `_run_unchecked` — line 205, 15 lines
  - `_hostile_cwd` — line 222, 9 lines
  - `_installed_workflow_root` — line 233, 38 lines
  - `workflow_command` — line 273, 12 lines
  - `stall_command` — line 287, 14 lines
- `tests/packaging/rework_13_scripts.py` — no functions
- `tests/packaging/test_rework_12.py`
  - `_prepare` — line 19, 8 lines
  - `_state_bytes` — line 29, 7 lines
  - `_command` — line 38, 12 lines
  - `_invoke` — line 52, 15 lines
  - `_assert_confirmed` — line 69, 5 lines
  - `_assert_one_record` — line 76, 9 lines
  - `_actor` — line 88, 18 lines
  - `_await_event` — line 108, 9 lines
  - `_finish` — line 119, 6 lines
  - `test_installed_retry_and_replay_confirm_ancestry_after_abrupt_exit` — line 128, 26 lines
  - `test_installed_concurrent_creation_confirms_and_preserves_peer_directory` — line 157, 35 lines
- `tests/packaging/test_rework_13.py`
  - `_prepare` — line 21, 13 lines
  - `_state_bytes` — line 36, 3 lines
  - `_invoke` — line 41, 33 lines
  - `_ledger` — line 76, 2 lines
  - `_assert_one_record` — line 80, 7 lines
  - `_assert_replaced_after_confirmation` — line 89, 32 lines
  - `_assert_runtime_replaced_at_deferred_mkdir` — line 123, 29 lines
  - `_assert_runtime_replaced_during_publication` — line 154, 35 lines
  - `test_installed_defer_refuses_replaced_distant_ancestry_until_fresh_attempt` — line 193, 46 lines
  - `test_installed_defer_refuses_runtime_replacement_before_deferred_creation` — line 242, 50 lines
  - `test_installed_defer_refuses_runtime_replacement_during_ledger_publication` — line 295, 50 lines
  - `test_installed_defer_confirms_parent_through_native_search_only_access` — line 348, 37 lines
  - `test_installed_defer_refuses_execute_only_ancestor_without_search_descriptor` — line 388, 35 lines
  - `test_installed_defer_confirms_first_descendant_without_root_self_confirmation` — line 425, 28 lines
  - `test_installed_defer_avoids_creation_attempts_on_existing_external_ancestors` — line 455, 22 lines
- `tests/workflow/test_deferred_ledger.py`
  - `test_defer_directory_replacement_fails_then_replays_once` — line 21, 41 lines
  - `test_defer_directory_replacement_fails_then_replays_once.replace` — line 34, 7 lines
  - `_directory_replacement_io` — line 64, 38 lines
  - `_directory_replacement_io.replace_directory` — line 71, 5 lines
  - `_directory_replacement_io.open_at` — line 77, 14 lines
  - `_directory_replacement_io.fsync_at` — line 92, 8 lines
  - `test_defer_io_stays_bound_to_opened_directory` — line 105, 28 lines
  - `test_creating_deferred_fsyncs_its_parent` — line 135, 19 lines
  - `test_creating_deferred_fsyncs_its_parent.spy_fsync` — line 141, 3 lines
  - `test_record_defer_requires_and_deduplicates_operation_ids` — line 156, 20 lines
  - `test_record_defer_rejects_conflicting_operation_id_without_byte_changes` — line 178, 16 lines
  - `test_record_defer_retry_before_atomic_publish_preserves_existing_bytes` — line 196, 21 lines
  - `test_record_defer_retry_before_atomic_publish_preserves_existing_bytes.interrupt` — line 204, 3 lines
  - `test_record_defer_retry_after_atomic_publish_is_byte_exact_noop` — line 219, 24 lines
  - `test_record_defer_retry_after_atomic_publish_is_byte_exact_noop.interrupt` — line 224, 3 lines
  - `test_record_defer_rejects_invalid_boundaries_without_writing` — line 256, 10 lines
- `tests/workflow/test_saga_identity.py`
  - `test_saga_deferred_directory_replacement_preserves_recovery_until_restored` — line 33, 33 lines
  - `test_saga_deferred_directory_replacement_preserves_recovery_until_restored.replace` — line 43, 4 lines
  - `test_recorded_recovery_requires_ledger_proof_after_restart` — line 68, 27 lines
  - `test_replay_after_rename_before_directory_fsync_syncs_both_lifecycle_dirs` — line 97, 35 lines
  - `test_replay_after_rename_before_directory_fsync_syncs_both_lifecycle_dirs.spy_fsync` — line 118, 3 lines
  - `test_after_intent_rename_away_of_lifecycle_directory_fails_recoverably` — line 135, 50 lines
  - `test_after_intent_rename_away_of_lifecycle_directory_fails_recoverably.replace_lifecycle` — line 148, 4 lines
  - `test_later_boundary_lifecycle_replacement_fails_then_reconciles` — line 195, 48 lines
  - `test_later_boundary_lifecycle_replacement_fails_then_reconciles.replace_lifecycle` — line 211, 4 lines
  - `test_after_intent_symlink_swap_cannot_escape_verified_hold_directory` — line 245, 28 lines
  - `test_after_intent_symlink_swap_cannot_escape_verified_hold_directory.replace_hold` — line 254, 4 lines
  - `test_saga_rejects_symlinked_lifecycle_directories_without_mutation` — line 276, 25 lines

## Tautological test shapes (computed, do not re-judge)

Each `[MECH]` line is a test whose shape cannot fail as written. Raise
it; step 6 adds any line the table lacks. `mech-check` is the finder.


Checked 24 test function(s) in 4 test file(s).

## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `7291d9f80c5b`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

replay: skipped (worktree add failed: Preparing worktree (detached HEAD 7291d9f)
fatal: could not create leading directories of '.git/worktrees/wt': Operation not permitted)

## Fail-first replay (approved retry)

Replay: 2 touched tests ran, 2 failed against base, 0 passed; 2 test files could not be collected at base (their tests fail there). Command: mise exec -- uv run pytest
The initial sandbox attempt could not create .git/worktrees/wt; the exact helper was then approved and completed with exit 0. Collection failures are not passing behavioral replay.

