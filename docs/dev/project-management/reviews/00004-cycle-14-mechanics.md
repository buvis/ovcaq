## Mechanical facts (computed, do not re-count)

Function line counts from `ast`. Cite these for countable claims; a
finding that contradicts this block is discarded at the review gate.

- `CHANGELOG.md` — skipped (non-python)
- `src/ovcaq/workflow/_files.py`
  - `_require_basename` — line 42, 2 lines
  - `_require_operation_id` — line 46, 2 lines
  - `_canonical_record_bytes` — line 50, 4 lines
  - `_fsync_directory` — line 56, 6 lines
  - `_fsync_directory_descriptor` — line 64, 2 lines
  - `_serialize_deferred_publication` — line 69, 12 lines
  - `_validate_record_encoding` — line 83, 10 lines
  - `_write_record_file` — line 95, 42 lines
  - `_finish_record_publication` — line 139, 18 lines
  - `_publish_record_file` — line 159, 15 lines
  - `_read_record_file` — line 176, 5 lines
  - `_read_record_content` — line 183, 38 lines
  - `record_defer` — line 223, 14 lines
  - `_deferred_item` — line 239, 6 lines
  - `_sync_deferred_directory` — line 247, 4 lines
  - `_ensure_directory_chain` — line 253, 26 lines
  - `_open_deferred_ledger` — line 282, 15 lines
  - `_lock_deferred_ledger` — line 300, 42 lines
  - `_lock_deferred_ledger.verify` — line 320, 13 lines
  - `_append_deferred_record` — line 344, 28 lines
  - `load_deferred_records` — line 374, 12 lines
  - `_open_lifecycle_directory` — line 389, 41 lines
  - `_verify_lifecycle_directory_identity` — line 432, 15 lines
  - `_artifact_stat` — line 449, 5 lines
  - `_validate_prd_artifact` — line 456, 4 lines
  - `_artifact_identity` — line 462, 4 lines
  - `_require_artifact_identity` — line 468, 6 lines
- `tests/packaging/rework_12_scripts.py` — no functions
- `tests/packaging/rework_13_scripts.py` — no functions
- `tests/packaging/test_rework_11.py`
  - `_assert_installed_origins` — line 25, 9 lines
  - `_initialize` — line 36, 8 lines
  - `_defer_command` — line 46, 23 lines
  - `_read_ledger` — line 71, 9 lines
  - `_seed_depth_ledger` — line 82, 15 lines
  - `_run_depth_candidate` — line 99, 20 lines
  - `_assert_candidate_within_depth_limit` — line 121, 20 lines
  - `_assert_candidate_exceeds_depth_limit` — line 143, 26 lines
  - `_assert_ledger_still_writable` — line 171, 24 lines
  - `test_installed_defer_keeps_the_composed_ledger_within_reader_depth_limit` — line 198, 41 lines
  - `test_installed_defer_retries_every_new_directory_fsync_after_failure` — line 245, 44 lines
  - `_set_prd` — line 291, 6 lines
  - `_render_command` — line 299, 10 lines
  - `_assert_retry_error` — line 311, 9 lines
  - `_successful_report_text` — line 322, 8 lines
  - `_seed_overlap_report` — line 332, 15 lines
  - `_start_report_actor` — line 349, 12 lines
  - `_await_actor_ready_and_start_publisher_b` — line 363, 21 lines
  - `_completed_process` — line 386, 7 lines
  - `_publication_or_none` — line 395, 6 lines
  - `_communicate_overlapping_publishers` — line 403, 42 lines
  - `_assert_overlap_publication_state` — line 447, 15 lines
  - `_retry_failed_overlap_publications` — line 464, 28 lines
  - `_assert_overlap_replay` — line 494, 17 lines
  - `_assert_overlap_final_report` — line 513, 18 lines
  - `test_installed_report_overlap_preserves_every_successful_publication` — line 533, 46 lines
- `tests/packaging/test_rework_13.py`
  - `_assert_installed` — line 19, 6 lines
  - `_prepare` — line 27, 19 lines
  - `_state_bytes` — line 48, 3 lines
  - `_identity` — line 53, 3 lines
  - `_invoke` — line 58, 34 lines
  - `_ledger` — line 94, 2 lines
  - `_assert_one_record` — line 98, 7 lines
  - `_assert_replaced_after_confirmation` — line 107, 32 lines
  - `test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt` — line 143, 47 lines
  - `test_installed_defer_confirms_parent_through_native_search_only_access` — line 192, 29 lines
  - `test_installed_defer_confirms_first_descendant_without_root_self_confirmation` — line 223, 28 lines
  - `test_installed_defer_avoids_creation_attempts_on_existing_external_ancestors` — line 253, 22 lines


## Tautological test shapes (computed, do not re-judge)

Each `[MECH]` line is a test whose shape cannot fail as written. Raise
it; step 6 adds any line the table lacks. `mech-check` is the finder.


Checked 7 test function(s) in 2 test file(s).


## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `be5e385bd971`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

replay: skipped (worktree add failed: Preparing worktree (detached HEAD be5e385)
fatal: could not create leading directories of '.git/worktrees/wt': Operation not permitted)

