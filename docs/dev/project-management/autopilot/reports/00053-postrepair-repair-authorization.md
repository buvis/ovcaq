# PRD00053 post-repair recovery authorization

On 2026-10-12 the operator explicitly replied: "fix all five and re-review".
This resolves `post_repair_review_decision` from
`reviews/00053-adapter-operational-corrections-v1-review-2-postrepair-20261012.md`.

Authorize one bounded repair pass for that review's five actionable findings:

1. R1 (Medium): consolidate the duplicated runpy Claude wrapper into one test
   helper shared by `test_supervisor_adapters.py` and `test_adapter_launch_routing.py`,
   preserving invocation evidence.
2. R2 (Low): qualify CHANGELOG terminal-lane wording with "remembered".
3. R5 (Low): qualify resolved-model preservation as applying to drivers built
   by `build_driver` in `docs/driver-protocol.md`.
4. R6 (Low): split and clarify the numeric-context and capacity CHANGELOG entry.
5. R7 (Low): remove redundant command-name parametrization from
   `tests/runtime/test_adapter_health.py`, retaining one name and both providers.

R3 remains deferred; R4 remains discarded. Preserve all previous settled scope
decisions, reviews, receipts, raw evidence, and implementation provenance.
Carl remains disabled. No production behavior expansion is authorized.

Keep cycle and rework_cap at 2. Queue through `review-close --batch-id tail-sweep`
against the post-repair review, then resume review / Tail sweep step 3 using the
installed work pipeline. After repair tasks and required work gates pass, hand
off and STOP for a fresh review session. This authorization overrides the
source Tail sweep step 4 prohibition on re-review for this pass only; do not
finalize against pre-repair receipts or increment the cycle.

The fresh session must regenerate the implementation-model audit from actual
author evidence, validate review-route, and run complete fresh Alice, Blake,
and Bob provider rosters with unique evidence paths. Preserve all full rubrics
and provider routing. If fresh review needs further implementation, pause for
another operator decision; this is not an unlimited repair loop.

Pass this file as autocodex `--scope`; it supersedes earlier one-time repair
limits only for these five findings and restates the binding handoff terms.
