# Task22 closure review

Bundled tool-less wrapper; requested sonnet/high verified environment, observed claude-sonnet-5-5, Anthropic. Session 04253d41-f512-4f52-bbcc-654b2e8ae726; dispatch6a35c7a7. Raw docs/dev/tmp/review-task-22.md. Initial coordinator verification-file shell quoting failed before render, and wrapper prompt-missing preflight executed no reviewer; corrected file creation via structured patch, rendered complete persona, then successful guarded dispatch. Both original closures resolved; LOW notes carried.

CLOSURE | resolved | 🟡 tests/drivers/test_codex_fake.py:311: Functions over the 50-line limit (`assert_workflow_handoff` 74, `test_command_backed_workflow_handoffs` 75, `test_builtin_fake_command_handoffs_drain_and_retain_completed_results` 56, `fake_codex.main` 51) | The diff extracts `assert_prd_completion`, `assert_handoff_observation`, `prepare_workflow_handoff` and `assert_completed_results`. The recorded AST spans are 43, 42, 50 and 35, all within the limit of 50. `main` was already split in d4ef489, before this task's base, and the diff doesn't regress it. The removed assertions reappear verbatim in the helpers.

CLOSURE | resolved | ⚪ tests/drivers/test_codex_prompt.py:52: the prompt-override test sets configured prompts equal to the default prompt, so it would pass if overrides were ignored | The configured prompts are now three distinct literals. The test calls `resolve_phase_route` for each phase and asserts `route.prompt == settings.prompts[phase]` and `route.prompt != NATIVE_PROMPT`. Ignored overrides would now fail.

LOW | tests/drivers/test_codex_fake.py:323 | `handoff_revision = before["revision"] + (1 if phase == "done" else 0)` is computed in both `assert_prd_completion` and `assert_workflow_handoff` (~line 386). | Compute it once in `assert_workflow_handoff` and pass it in, or drop the unused copy if `assert_prd_completion` doesn't need it.

LOW | tests/drivers/test_codex_fake.py:~345 | The new helpers carry full type annotations, but `assert_workflow_handoff` (12 positional params, untyped) and the rest of the file don't. | Match the surrounding style, or annotate `assert_workflow_handoff` in the same pass. Better still, bundle `environment, tmp_path, prd, historical, current` into one small context object to cut the parameter lists.

LOW | tests/drivers/test_codex_prompt.py:~80 | `resolve_phase_route` is called inside the loop with an identical `PhaseSettings("standard", "high", 10)` each iteration. | Hoist the `PhaseSettings` into a local variable above the loop.

Behavior note, not a finding: `test_probe_invocation_evidence` and the fake's `emit_invocation` now put probe evidence on stderr for `--version` and `login status`. The recorded run covers all 50 named cases across the original run and the process retry, and the two `ps` PermissionErrors were sandbox-only and passed on retry.
