# Cycle 2 interactive recovery handoff

Operator authorized resuming the reviewer-failure pause on 2026-10-04, preserving cycle 2 and rework cap 2. This session prepares the fresh review only; it dispatches no reviewer or repair and claims no convergence.

The pause was `reviewer_fail`: external Claude Bob's approved dispatch exited 1 because `docs/dev/tmp/bob-output-2.txt` already existed; no fresh output or receipt was published. Its context also included the design document. Preserve `00008-tui-python-launcher-v1-review-attempt-2.md`, `00008-tui-python-launcher-v1-bob-invalid-2.md`, all raw logs, and the stale output as evidence only. There is no canonical cycle-2 review artifact.

Fresh-session requirements:

- Read `~/.config/autocodex/host.md`, the installed run-autopilot review gate, review-work-completion skill, complete personas and rubrics. Run all mandatory lenses anew; prior Alice/Blake output is evidence, not a substitute for fresh dispatch.
- Alice and Blake use isolated native Codex gpt-6.1-sol/high prompts without parent history. Blake receives only PRD requirements, without diff, file list, plan, design, history, or sibling findings.
- Bob uses a fresh external Claude Opus helper dispatch, full Bob persona, consensus rubric, doubt D1-D5 and de-slop appendix. Retain the user's R1-R5 doubt intent under D1-D5. Claude Bob is the independent provider substitution; never claim an Eve dispatch or Codex thread.
- Bob's requirements context must contain the PRD without the design document or implementation plan. Mechanical evidence and the current diff remain separate review evidence. Inspect the assembled input before dispatch; do not reuse the biased shared context. The staged `docs/dev/tmp/bob-context-2-corrected.md` and `bob-prompt-2-corrected.md` are candidates to inspect and refresh, not automatically certified inputs. Regenerate current-cycle mechanical evidence and remove stale duplicate replay claims.
- Generate a fresh UUID and use absolute UUID-qualified paths for the Bob prompt, context, output and associated evidence, for example `docs/dev/tmp/bob-output-00008-c2-<uuid>.txt`. Verify output and receipt paths do not exist before dispatch. Never use `bob-output-2.txt`. Use `/Users/bob/.config/autocodex/driver.py --cd /Users/bob/git/src/github.com/buvis/ovcaq reviewer -f <absolute-prompt> -o <absolute-unique-output>` with required network approval. Await the same helper through quota waits.
- Require the successful helper receipt and stamp `autocodex_bob_receipt: <absolute receipt path>` in consolidated review top matter. Preserve immutable raw JSONL/stderr, reviewer text, accurate model provenance, all raw Alice R, Blake B, and Bob D verdicts. Follow optional Carl and required guard procedures without bypassing nesting guards.
- Preserve cycle 2, cap 2, batch identity, work_start_sha, all 14 completed tasks, deferred decisions and prior review history. Resume clears the resolved pause only. Do not increment the cycle, raise the cap, replan, repair, create a canonical review, or mark convergence in this recovery session. The fresh review applies the unchanged cap policy after complete valid evidence.

Prior checks: `verification-2.md` records 4579 passing tests and green sync, Ruff, mypy and build at product HEAD `7b47cef26fc8fa97fae726e4317629ee5053dc71`. `replay-2.md` records the approved replay's 600-second timeout and removed temporary worktree. These are retained evidence, not a fresh review verdict.

Recovery uses the existing state CLI. The installed transition table has no paused-resume outcome; the documented recovery field setters restore phase and next_phase to review without the `rework` outcome, which would incorrectly increment cycle 2.

Unresolved questions: none for this authorized recovery. Fresh review findings remain unclassified until every mandatory lens completes.
