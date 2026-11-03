# Final verification contract conflict

Full suite exit1: 1 failed, 5590 passed, 2 temporary-directory cleanup warnings in218.78s. Failure: `tests/drivers/test_codex_decode_terminals.py::test_top_level_error_is_sanitized_provisional_activity`, line146.

The existing test requires exact `sanitize_text(detail)`, which retains the ANSI sequence after redacting a credential. New task23 test at `tests/drivers/test_codex_rework_decode.py:154` explicitly rejects ESC/NUL in every detail payload for both top-level error and turn.failed, including the same top-level error path. Current bounded_detail strips controls uniformly.

Fresh isolated Ivan8361e46a verified both files: 1failed85passed, exit1. No edits. Splitting policy by event cannot satisfy both because both include error; splitting by length/content/failure classification would be arbitrary test-specific behavior. Shared sanitizer and tests remained read-only. Worker could not observe its model metadata itself; coordinator verified structured native turn_context gpt-6.1-sol/medium in preserved raw worker rollout, with exact line hashes in the native evidence index.

Operator decision requested: preserve existing credential-only normalization and correct the new test, or uniformly strip controls and update the old expectation. No decision inferred from time. Preserve failing assertion, implementation evidence, cycle1 reviewed snapshot, cycle1/cap2 and work_start_sha. No cycle advance or new review until authorized correction and full verification pass.

Other checks: uv sync --all-groups passed; Ruff lint passed; mypy passed61sourcefiles; formatting initially failed one wrapped expression and passed228files after delegated formatting-only fixfec2ad6; standard uv build initially hit sandbox DNS then identical required approved retry successfully built sdist/wheel. No queued verification file exists. Source final-verification prohibits relaxing the failing test; its exact instruction is “Do NOT relax the failing test.”
