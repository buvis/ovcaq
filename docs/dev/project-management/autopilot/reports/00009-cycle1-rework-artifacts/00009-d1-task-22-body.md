Review: docs/dev/project-management/reviews/00009-codex-adapter-v1-review-1.md
Design context: docs/dev/project-management/designs/00009-codex-adapter-v1-design.md

Extract helpers without weakening existing assertions, handle all four overlength functions, and exercise configured prompt overrides through real resolution using distinct values. Coordinate fake-fixture edits with task 21.

Acceptance: every quoted finding no longer reproduces; preserve all existing assertions and full shared conformance. Run source work pipeline, independent behavioral regressions where needed, and its mandatory final verification.

### Findings (verbatim)
- 🟡 tests/drivers/test_codex_fake.py:311: Functions over the 50-line limit, per the mechanical facts: `assert_workflow_handoff` (74) and `test_command_backed_workflow_handoffs` (75) in tests/drivers/test_codex_fake.py; `test_builtin_fake_command_handoffs_drain_and_retain_completed_results` (56) in tests/runtime/test_supervisor_adapters.py:154; `main` (51) in tests/fixtures/codex/v1/fake_codex.py:195. The build report already records the fake_codex.main style-gate failure. Split the per-phase handoff assertions into helpers (found by: ALICE, BOB)
- ⚪ tests/drivers/test_codex_prompt.py:52: The prompt-override test sets the configured prompts equal to the default prompt and then checks `default_prompt`, so it would still pass if overrides were ignored. (found by: BLAKE)
