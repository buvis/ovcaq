# Sanitization contract recovery

The operator explicitly agreed on 2026-10-06 to strip terminal controls from
normalized Codex error details and update the old contradictory test, preserving
credential-redaction assertions and raw evidence. This supersedes the unresolved
choice in `00009-cycle1-sanitization-blocker.md`; that historical report remains
unchanged.

Commit `b95bcaf4fe1aa6edcf80762257aea40acec8ab37` changes only
`tests/drivers/test_codex_decode_terminals.py`: the error detail is independently
expected to equal `Unauthorized [REDACTED]`, and the unused sanitizer import is
removed. The assertion checks both redaction and removal of the ANSI sequence.
Production code and the shared sanitizer are unchanged. Existing ESC/NUL and
4096-character regressions remain in the newer test file.

The bounded final-verification repair used native worker
`/root/sanitize_contract`, session `01a112a8-c2f2-7d30-9403-ac645607272b`.
Structured `turn_context` metadata confirms OpenAI `gpt-6.1-sol`, medium effort,
matching the logical sonnet tier. The preserved raw transcript is
`00009-cycle1-recovery-worker.jsonl`; its line-8 hash and task-23 correlation are
in `00009-cycle1-recovery-worker-evidence.json`. The worker reported no assumptions.
The dispatch was assembled directly rather than through the source render helper;
no synthetic dispatch-start receipt was created retrospectively. The raw session
preserves the actual prompt, execution, model metadata and result.

This is the final-verification regression-fix path, following the operator's
contract decision, rather than a rerun of the completed task pipeline. The prior
task-23 Pat review remains historical evidence; the next full review must inspect
the corrected tree in a fresh session. The cycle-1 implementation audit and
reviewed snapshot remain unchanged. Before cycle 2, regenerate the audit using
the original audit, the cycle-1 rework-worker evidence, and this recovery-worker
evidence, then run the host `review-route` check. Preserve all three independent
review lenses and the cap of 2.

Verification at `b95bcaf4fe1aa6edcf80762257aea40acec8ab37`:

- `mise exec -- uv run pytest -q --tb=line`: 5591 passed, zero failures,
  2 temporary-directory cleanup warnings, exit 0, 247.08 seconds.
- The two named decoder files: 86 passed, exit 0.
- `mise exec -- uv run ruff check .`: exit 0.
- `mise exec -- uv run ruff format --check .`: 228 files already formatted,
  exit 0.
- Source style-limit and split-hygiene checks for the changed test: exit 0.
- Existing cycle-1 review coverage/guard gate: exit 0.
- State schema and task-count consistency: valid before handoff.

No queued verification file exists. The previous successful sync, mypy and build
results are retained from the blocker report; this test-only correction reran
the failed full suite and the affected lint/format checks, as required by the
final-verification repair procedure. No new worktree, branch, or scratch plan
was created. Existing architecture and unfinished portfolio plans are retained.

After task 23 closes, the canonical `phase-done --outcome rework` transition
hands off to cycle 2, with all 30 tasks completed and cap 2 unchanged. Completion
review is not run in this implementation recovery session. The verification
record retains the actual tested SHA; a later store-only commit must not be
misrepresented as the SHA tested.
