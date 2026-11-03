## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `e4d765c42d1b`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

[MECH] 🟡 66 touched test(s) pass against the pre-change code: test_bounded_detail_redacts_reconstructed_tokens_before_capping, test_bounded_detail_preserves_printable_text_and_caps_after_control_removal +60 more | File: tests/drivers/test_codex_detail_safety.py | Task: general
[MECH] 🟡 5 touched test(s) pass against the pre-change code: test_valid_escaped_pair_remains_a_native_startup_record, test_malformed_and_non_json_frames_keep_native_delegation, test_real_writer_failures_propagate_from_unsafe_native_frames | File: tests/events/test_unicode_frames.py | Task: general
[MECH] 🟡 26 touched test(s) pass against the pre-change code: test_usage_and_completion_preserve_valid_unicode_scalars +20 more | File: tests/events/test_unicode_safety.py | Task: general

Replay: 1293 touched test(s) ran, 1196 failed against base, 97 passed; 0 test file(s) could not be collected at base (their tests fail there). Command: env UV_CACHE_DIR=/private/tmp/ovcaq-uv-cache mise exec -- uv run pytest -q --tb=line
