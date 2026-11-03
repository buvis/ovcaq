Review: docs/dev/project-management/reviews/00009-codex-adapter-v1-review-1.md
Design context: docs/dev/project-management/designs/00009-codex-adapter-v1-design.md

Includes behavioral R19, not only prose cleanup: uphold conflicting-thread unknown-failure through a real fake Supervisor regression and provider-neutral normalized evidence; do not merely weaken the specified contract in docs. Coordinate with task 19 conflict-gap fixes and then reconcile documentation/changelog. No provider-specific runtime parser or branch.

Acceptance: every quoted finding no longer reproduces; preserve all existing assertions and full shared conformance. Run source work pipeline, independent behavioral regressions where needed, and its mandatory final verification.

### Findings (verbatim)
- 🟡 CHANGELOG.md:9: CHANGELOG adds nine bullets for one unreleased feature. Three lead with internal task IDs ("P07-T02 adds", "P07-T03 task 1", "P07-T04 adds") instead of the user-visible effect, blank lines split the Added and Fixed lists, and both "Fixed" bullets fix code that was never released. Collapse to one or two user-facing Added bullets (carried Pat LOW) (found by: ALICE, BOB)
- 🟡 docs/driver-protocol.md:167: The conflicting-thread contract does not survive the supervised path. Supervisor passes `session_id` to RawFirstDecoder (src/ovcaq/runtime/supervisor.py:455), which rebinds run_id and session_id on every observation (src/ovcaq/events/tail.py:137). The reducer never sees distinct thread IDs, so the "reduce to unknown failure" claim and "supplied run ID and current thread as session ID" in the docs hold only in unit tests that call `reduce_session` directly. (found by: BOB)
