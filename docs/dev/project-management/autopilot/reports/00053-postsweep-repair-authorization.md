# PRD00053 post-sweep repair authorization

On 2026-10-12 the operator chose "Fix all 6, re-review" for the
`post_sweep_review_decision` pause raised by
`reviews/00053-adapter-operational-corrections-v1-review-2-postsweep-20261012.md`.

This is a second one-time exception, scoped like
`00053-tail-sweep-authorization.md`, and it supersedes that file's "no further
repair loop" clause for these six findings only:

1. R1 (medium): make the HTTP minor version optional in
   `classify_failure` (`src/ovcaq/drivers/codex_events.py:301`) so `HTTP/2 503`,
   `HTTP/2 429`, `HTTP/3 ...` classify as before. Add HTTP/2 positives to
   `tests/drivers/test_adapter_failure_classes.py`. Out of scope: `status=429`
   and `Error 429:` forms (Blake) - not native Codex forms, not widened here.
2. R2/R8: drop the redundant `CHANGELOG.md:43` entry; fold the user-visible part
   into the numeric-context entry (`CHANGELOG.md:46`).
3. R3: rename `_tier_request` in `src/ovcaq/drivers/edge.py` to a verb-led name.
4. R6: cover more than one Claude effort value in
   `tests/runtime/test_adapter_launch_routing.py` (or state why all are `high`).
5. R7: qualify `docs/driver-protocol.md:243` to "remembered" completed and
   failed lanes.
6. R9: annotate `configured_driver` in `tests/drivers/test_codex_launch.py` as
   `-> AgentDriver`.

R4 (discard, settled) and R5 (existing out-of-scope deferral) stay as decided.

Queued as tasks 15-17 named `[D2] Tail sweep: ...`, with `rework_task_ids` set.
Keep cycle and rework_cap at 2. Resume at review / Tail sweep step 3. After the
tasks and work checks pass, hand off and STOP; do not finalize against the
post-sweep receipts. The next fresh session regenerates the implementation-model
audit and runs complete fresh Alice, Blake and Bob provider rosters with unique
output paths, preserving all prior reviews and receipts. If that review needs
further implementation, pause for an operator decision again.

Pass this file alone through autocodex `--scope` (it takes one path); it
restates every still-binding term of the earlier authorization.
