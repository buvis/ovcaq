# PRD 00053: three approved test repairs

Operator approved R1/R2/R7 on 2026-10-12. The bounded repair is complete in two commits: `d395915` (task 21, R1/R7) and `7fbcfd0` (task 22, R2). Only four test files changed, 10 insertions and 27 deletions. Production behavior and all previous evidence remain intact. Cycle/rework cap remain 2/2; all 22 tasks are complete.

Task 21 removes the unused `fake_executable` name argument and the dedicated Claude/sh overlay-PATH test, retaining the both-provider parametrized test. Task 22 renames `workflow_fixture`, `configured_workflow`, and `configured_driver` to `write_workflow_fixture`, `configure_workflow`, and `configure_driver`, including their references. No other helper naming was changed.

Both tasks used the installed work pipeline with native isolated Ivan workers (logical sonnet, observed `gpt-6.1-sol/medium`). The host contract's coordinator-delegation rule was applied to both tasks. Test-only classification skips Tess/red-check/Devon and self-deslop. Both style-limit and split-hygiene gates passed. Per-task Pat reviews through the use-sonnet wrapper observed `claude-sonnet-5-5`, requested high effort, with no tools. All three CLOSURE verdicts are resolved; both reviews returned NO FINDINGS and passed the parser. These reviews do not replace the fresh completion roster.

21: style_gate: clean, split_hygiene: clean
22: style_gate: clean, split_hygiene: clean

Both implementors reported ASSUMPTIONS: none. The existing assumptions ledger remains unchanged: original test authors/implementors and cycle-1 rework reported none; the historical task-10 fixture-directory correction and direct-author attribution remain documented there.

## Verification

Task 21: 23 passed, exit 0, two pytest temporary-directory cleanup warnings.
Task 22: 73 passed, 8 failed, exit 1. Every failure is `PermissionError: Operation not permitted: ps`; worker and coordinator escalated retries hit the same host restriction. No tests were weakened. The failed invocation is retained as failed, not represented as a green run.

`uv sync --all-groups`, `ruff check .`, `ruff format --check .` (236 files), `mypy src/ovcaq` (61 files), and `uv build` all passed. `git diff --check`, full state-schema validation and task-count consistency passed. The review's queued verification list is empty.

The first full suite completed with **6428 passed, 555 failed, 172 errors, 2 warnings**, exit 1, in 518.12 seconds. Its complete output is preserved as `pytest-full-first-run.txt`. It contains 611 direct `ps` PermissionError lines and additional startup failures/timeouts; not every failure was independently diagnosed. The host-required escalated retry reproduced the failure/error pattern near 46% and was interrupted by the coordinator (exit 130); its partial output is `pytest-full.txt`. There is no green full-suite result. The sibling `verification.json` retains both attempts. Runtime `last-verification.json` records both exits and null counts because the last attempt was interrupted. Host-blocked verification follows the work skill's fail-loud exception; do not interpret task completion as verified runtime success.

## Fresh-session instructions

Run a fresh full completion review, with all three lenses and complete rubrics, through the host's model-provider routing. Preserve cycle/cap at 2 and use a new uniquely named review artifact, e.g. `00053-adapter-operational-corrections-v1-review-2-three-repair-20261012.md`. The same-cycle existing-review skip must not reuse pre-repair receipts: this is an explicitly authorized fresh post-repair review.

Preserve the existing implementation-model audit and receipt-bound snapshot until the fresh review regenerates its audit. Add the hash-pinned worker lines in `00053-three-repair-20261012-evidence/additional-implementation-evidence.json` to historical evidence; each task's raw session metadata, implementation tool calls and prompt correlate the author and commit. Both new workers served OpenAI models, so the required full roster remains Anthropic Alice/Blake/Bob. Pat is read-only and excluded from implementation provenance. Run `driver.py review-route` before dispatch and verify every evidence hash.

Preserve R3 grammar and R5 signal-flake deferrals, R4's settled empty-PATH limitation, and R6's discarded evidence-cleanup proposal. Keep Carl disabled and all previous reviews, raw evidence and receipts. No further repairs, cap increase, or finalization was approved in this recovery. Never finalize against pre-repair receipts. Surface fresh actionable findings for operator disposition.

## Recovery and cleanup

`review-close --batch-id tail-sweep` created tasks 21/22. It also retained old completed rework IDs 18/19/20; the recovery transaction narrowed the queue to the newly authorized tasks. Since the installed phase-done table has no paused-resume transition, paused-to-build recovery used the existing validated, atomic `statectl.mutate` writer, preserving siblings and recording the operator decision. The final build-to-review handoff uses canonical `phase-done --outcome tasks_done`.

No additional worktrees or orphan branches exist. No plan was executed by this bounded recovery; retained architecture plans and historical handoffs are evidence, not cleanup targets. Only this session's temporary prompt/input/diff files are removed after preserving their durable evidence. Pre-existing autocodex session/metrics changes are runtime evidence and are retained.
