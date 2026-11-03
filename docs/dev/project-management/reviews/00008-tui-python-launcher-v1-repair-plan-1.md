# PRD 00008 repair replan 1

Source: recovery-1 and rework-1 reports, review-1 at `5544b1f`, current
implementation at `e013397`. The source-plan SHA-256 matches the coverage
manifest. Original tasks 1–10 are not replanned. Partial tasks 11/12 and all
raw verdicts remain preserved in the recovery report.

The plan-expansion gate passed: 12 tasks, all file sets present. Estimates
include the full PRD, task contract and writable sources plus the mandated
55,000-token overhead; every task is below 75,000. Qwen's planning preflight
failed `endpoint_unreachable`, so eligibility splitting is inactive.

| New task | Old task | Remaining scope | Tier | Estimated tokens |
|---|---|---|---|---:|
| 1 | 11 | Real adapter identity and evidence-status typing | sonnet | 73431 |
| 2 | 12 | Exact ended owner, observation lock and active evidence window | opus | 73192 |
| 3 | 13 | Responsive polling and elapsed duration | opus | 67129 |
| 4 | 14 | Shared exact-run mutation synchronization | opus | 71617 |
| 5 | 14 | Control callers and registry reuse | opus | 71267 |
| 6 | 15 | JSON run opt-in and lazy UI imports | sonnet | 63575 |
| 7 | 15 | Quick completion and launch diagnostics | opus | 71000 |
| 8 | 16 | Fleet sanitization and discovery gaps | sonnet | 62858 |
| 9 | 17 | Theme persistence and trusted XDG anchor | opus | 69385 |
| 10 | 18 | Plain fallback, EOF and redraws | sonnet | 61904 |
| 11 | 19 | Collision assertion and decoder exception catch | sonnet | 66917 |
| 12 | 20 | Parser-generated documentation and release notes | sonnet | 67624 |
| 13 | New prerequisite | Project normalized lane descriptions | sonnet | 61666 |
| 14 | Newly confirmed boundary defect | Preserve unknown usage in final metrics and remove fixture workaround | opus | 67451 |

During task 1, the committed real-adapter regression first failed on run ID.
Commit `28bf789` fixes canonical identity and the evidence typing error, then
the same assertion chain exposes a separate normalized-description projection
gap (`1 failed, 5 passed`). Adding the TUI source to task 1 would exceed its
75K recovery estimate, so task 13 isolates that gap under the rework micro lane.
Task 1 is pending on task 13 and retains its original test/implementation
commits and remaining post-implementation gates. Its split interruption is
recorded as an aborted attempt, not completion. The new dependency is
13 → 1 → 2 → … → 12; only one task is in progress at a time.

Task 14 follows task 12. The task-1 test author's failed runs and coordinator
source inspection confirm that final metrics reject valid normalized unknown
numeric values. This task aligns validation with the accepted unknown-value
contract and removes the fixture's fabricated tool count, so final verification
exercises the real adapter summary unchanged. It adds no state fields or
provider-specific parsing. The code classifier assigns opus/contract because
the persisted metric validator changes; its estimate remains below 75K.

Dependencies retain the original sequence, with old tasks 14 and 15 split at
independently verifiable service/caller and CLI/launch boundaries. New IDs were
captured from task-add before assigning each subsequent dependency. The tighter
near-budget ownership tasks retain correlated service/caller changes where
splitting would leave broken ownership semantics; no Qwen-driven split applies.

Contracts and acceptance are copied from the reviewed design and PRD/source
phase. There is no new PRD/design conflict. Prior additive read-model fields
and retained lifecycle tests are reused. Old task12's exhausted four Tess
dispatches and completed Devon pass remain evidence; the replan does not grant
another test-authoring budget for that same repair.

Host provenance: Codex coordinates; native logical sonnet maps to
`gpt-5.6-sol`, logical opus to `gpt-6-astra`; external Claude dispatches keep
their real provider. Existing review1 cannot approve repaired code. Product
gates and fresh review remain outstanding; cycle 1 and rework cap 2 are unchanged.

Unresolved questions: none.

Task7 implementation amendment: existing selection errors had no typed distinction
between absent selection and arbitrary viewer failures. The state-backed contract
adds only a `ValueError` subtype in `tui/discovery.py`, preserving ambiguous
selection semantics. The extra1,419-byte source keeps the conservative estimate
at71,000 tokens, below75,000. The nullable launch result and exact-child terminal
proof requirement are recorded in the task body and its completion evidence.

Recovery handoff note: installed `cli/transitions.py` makes build/tasks_done
advance only phase/next_phase; it does not increment cycle. These tasks finish
the already-reviewed cycle-1 rework, so after all work and final gates complete,
the coordinator must also apply the canonical review/rework transition before
ending: that atomically advances cycle to 2 and clears rework_task_ids. This is
completion bookkeeping, not invocation of review in the build session. Preserve
rework_cap=2 and the original work_start_sha. A fresh process must run every
cycle-2 lens; review-1 at 5544b1f is not approval of the repaired HEAD.
