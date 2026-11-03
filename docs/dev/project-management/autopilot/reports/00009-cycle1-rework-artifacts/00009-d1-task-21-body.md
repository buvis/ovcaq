Review: docs/dev/project-management/reviews/00009-codex-adapter-v1-review-1.md
Design context: docs/dev/project-management/designs/00009-codex-adapter-v1-design.md

Retain mismatched receiver-ID raw fallback coverage; add a separate consistent native collab record for real Supervisor lane presentation, refresh fixture SHA-256 provenance honestly, and remove the unrelated import rewrap. No live workflow or launcher-global mutation.

Acceptance: every quoted finding no longer reproduces; preserve all existing assertions and full shared conformance. Run source work pipeline, independent behavioral regressions where needed, and its mandatory final verification.

### Findings (verbatim)
- 🟡 tests/tui/test_codex_projection.py:256: P07-T07 wants actual native lanes shown from real fake-Supervisor output. In `lanes.jsonl`, the `receiver_thread_ids` and `agents_states` keys never match, so the fake-Supervisor "lanes" scenario asserts no lanes. The only visible lane comes from a test that rewrites the provider payload in place (`matched=True`). (found by: BOB)
- ⚪ tests/runtime/test_supervisor.py:29: The only change to test_supervisor.py is a no-op import rewrap. It does not trace to the task, which put the drain in a new file instead. (found by: BOB)
