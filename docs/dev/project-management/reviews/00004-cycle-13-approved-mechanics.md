## Mechanical facts (computed, do not re-count)

Function line counts from `ast`. Cite these for countable claims; a
finding that contradicts this block is discarded at the review gate.

- `CHANGELOG.md` — skipped (non-python)
- `src/ovcaq/workflow/_files.py`
  - `_require_basename` — line 41, 2 lines
  - `_require_operation_id` — line 45, 2 lines
  - `_canonical_record_bytes` — line 49, 4 lines
  - `_fsync_directory` — line 55, 6 lines
  - `_fsync_directory_descriptor` — line 63, 2 lines
  - `_serialize_deferred_publication` — line 68, 12 lines
  - `_validate_record_encoding` — line 82, 10 lines
  - `_write_record_file` — line 94, 42 lines
  - `_finish_record_publication` — line 138, 18 lines
  - `_publish_record_file` — line 158, 15 lines
  - `_read_record_file` — line 175, 5 lines
  - `_read_record_content` — line 182, 38 lines
  - `record_defer` — line 222, 14 lines
  - `_deferred_item` — line 238, 6 lines
  - `_sync_deferred_directory` — line 246, 4 lines
  - `_ensure_directory_chain` — line 252, 12 lines
  - `_open_deferred_ledger` — line 267, 15 lines
  - `_lock_deferred_ledger` — line 285, 42 lines
  - `_lock_deferred_ledger.verify` — line 305, 13 lines
  - `_append_deferred_record` — line 329, 28 lines
  - `load_deferred_records` — line 359, 12 lines
  - `_open_lifecycle_directory` — line 374, 27 lines
  - `_verify_lifecycle_directory_identity` — line 403, 15 lines
  - `_artifact_stat` — line 420, 5 lines
  - `_validate_prd_artifact` — line 427, 4 lines
  - `_artifact_identity` — line 433, 4 lines
  - `_require_artifact_identity` — line 439, 6 lines
- `tests/packaging/rework_12_scripts.py` — no functions
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
  - `_assert_retry_error` — line 311, 13 lines
  - `_successful_report_text` — line 326, 8 lines
  - `_seed_overlap_report` — line 336, 15 lines
  - `_start_report_actor` — line 353, 12 lines
  - `_await_actor_ready_and_start_publisher_b` — line 367, 21 lines
  - `_completed_process` — line 390, 7 lines
  - `_publication_or_none` — line 399, 6 lines
  - `_communicate_overlapping_publishers` — line 407, 42 lines
  - `_assert_overlap_publication_state` — line 451, 15 lines
  - `_retry_failed_overlap_publications` — line 468, 28 lines
  - `_assert_overlap_replay` — line 498, 17 lines
  - `_assert_overlap_final_report` — line 517, 18 lines
  - `test_installed_report_overlap_preserves_every_successful_publication` — line 537, 46 lines
- `tests/packaging/test_rework_12.py`
  - `_assert_installed` — line 19, 6 lines
  - `_prepare` — line 27, 16 lines
  - `_state_bytes` — line 45, 7 lines
  - `_identity` — line 54, 3 lines
  - `_command` — line 59, 12 lines
  - `_invoke` — line 73, 16 lines
  - `_assert_confirmed` — line 91, 6 lines
  - `_assert_one_record` — line 99, 9 lines
  - `_actor` — line 111, 18 lines
  - `_await_event` — line 131, 12 lines
  - `_finish` — line 145, 9 lines
  - `test_installed_retry_and_replay_confirm_ancestry_after_abrupt_exit` — line 157, 26 lines
  - `test_installed_concurrent_creation_confirms_and_preserves_peer_directory` — line 186, 35 lines
- `tests/workflow/test_ledger_publication.py`
  - `_rival` — line 14, 28 lines
  - `test_sidecar_replacement_inside_native_publish_cannot_lose_successful_append` — line 45, 43 lines
  - `test_sidecar_replacement_inside_native_publish_cannot_lose_successful_append.replace` — line 54, 10 lines
  - `test_restored_sidecar_cannot_authorize_overwriting_a_newer_ledger` — line 90, 31 lines
  - `test_restored_sidecar_cannot_authorize_overwriting_a_newer_ledger.compete` — line 95, 8 lines

## Tautological test shapes (computed, do not re-judge)

Each `[MECH]` line is a test whose shape cannot fail as written. Raise
it; step 6 adds any line the table lacks. `mech-check` is the finder.


Checked 7 test function(s) in 3 test file(s).

## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `39ecaf4f95c7`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

replay: skipped (worktree add failed: Preparing worktree (detached HEAD 39ecaf4)
fatal: could not create leading directories of '.git/worktrees/wt': Operation not permitted)

Context pack: unavailable (engram: repository is not registered); no fallback pack invented.

