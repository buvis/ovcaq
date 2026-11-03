---
prd: docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
review: 2
date: 2026-10-12
head_sha: 6761a37d52b1363dc7d8d3a8ce44e17e9246287c
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
dispatch_rows:
  alice: 2e133434
  blake: 4b0dcb92
  bob: e834d5d0
---

# Review: 00053 adapter operational corrections — fresh three-repair review

Diff range: `7819970d7f807d6fad07b115af4f0df1fbc4a248..6761a37d52b1363dc7d8d3a8ce44e17e9246287c`

codex_rung_guard: not fired
provider_review_guard: satisfied
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-three-repair-review-20261012-evidence/alice-output.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-three-repair-review-20261012-evidence/blake-output.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-three-repair-review-20261012-evidence/bob-output.txt.receipt.json

The model-provider guard supersedes the legacy launcher guard. All implementation authors served OpenAI models, so independent Anthropic Alice/Blake/Bob reviewed the whole PRD range. Eve did not run. Each fresh process served `claude-opus-5-5`, requested `opus/xhigh`; no implementation thread was resumed. Audit fingerprint: `224988c1bf7002d797c23f74b43dd2b1aefcd8c56c8cac2c43ce101e0d6f1fcc`. Carl is disabled by operator authorization.

## Review summary

22/22 completed tasks. All three processes exited 0; output and raw-evidence hashes and complete strict rubric verdicts validated. Alice: session `9158ddf2-fa0a-443c-accb-dac3853618e2`; Blake: `e4aba6fe-c1ef-4bb4-9330-a3c3ab9029bb`; Bob: `f2e14e0b-51d5-4366-8947-1190eacb867a`. Alice and Blake dispatch ledger rows were opened after process launch; receipts supply actual start/completion times. Bob's row was opened by review-stage.

Review-stage assembled full personas and rubrics, task rows, PRD/design context, AST mechanical facts and tautology checks. Blake received only the PRD, blind persona and rubric. Fail-first replay was omitted (optional flag); no `[MECH]` finding was emitted. The previous cycle's verification queue is empty. Engram pack failed because this repository is not registered; prompts carry the source sentinel. No rubric or lens was reduced.

The stage gate used plain `uv` and returned exit 2 without counts. The fresh coordinator invocation through mise passed, as did independent Alice/Blake runs. Reviewers initially saw the prior host-blocked evidence; their raw conclusions are retained unchanged below. Current evidence resolves those verification concerns without rewriting the earlier failed runs.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [1/3] | 🟡 | The new status prefix in `classify_failure` (src/ovcaq/drivers/codex_events.py:302) ends in `\s*:?\s*`. That is two whitespace runs side by side, so a native error with "status", "HTTP" or "error code" followed by a long run of whitespace backtracks in quadratic time. Measured at HEAD: 16k spaces took 0.55 s and 64k spaces took 8.34 s. The old bare-number regex had no such run. Decode runs inline in the supervisor read loop (src/ovcaq/runtime/supervisor.py:516) on frames up to 1 MiB (src/ovcaq/events/tail.py:60). Python's `re` holds the GIL, so the watchdog cannot fire while it runs. A full 1 MiB frame extrapolates to roughly 35 minutes (a guess, not run). The trigger needs tens of thousands of whitespace characters right after the keyword, so it is unlikely to happen. Fix: use `\s*(?::\s*)?` instead. It took 1.2 ms at 64k and matched the same way on "HTTP status: 429", "status code: 429", "last status: 429", "HTTP 429" and "status=429". Also add a regression test that expects "status" + 200,000 spaces + "x" to classify as unknown | src/ovcaq/drivers/codex_events.py | 6 | ALICE |
| R2 | [1/3] | 🟡 | `test_unrelated_item_type_does_not_transition_lane` (tests/drivers/test_adapter_outcomes.py:204) and `test_unrelated_event_type_does_not_transition_lane` (tests/drivers/test_adapter_outcomes.py:231) are line-for-line copies. They differ only in one `collab_record` keyword: `item_type="command_execution"` in one, `event_type="thread.started"` in the other. Merge them into one test parametrized over that keyword dict (passed as `**override`). That cuts about 24 lines and keeps the same coverage | tests/drivers/test_adapter_outcomes.py | 5 | ALICE |
| R3 | [1/3] | ⚪ | The recorded verification for this cycle has no green full suite. It shows 555 failed and 172 errors, which it attributes to the sandbox denying `ps`. I reran at HEAD 6761a37 with `mise exec -- uv run pytest -q`: 7154 passed, 0 failed, 0 skipped, exit 0. `ruff check`, `ruff format --check` and `mypy src/ovcaq` also exit 0. Record this green run before closing the phase-2 gate | docs/dev/project-management/autopilot/reports/00053-three-repair-20261012-evidence/verification.json | general | ALICE |
| R4 | [1/3] | ⚪ | A completed lane can still turn into a failure after the identity cache fills. At 4096 entries, eviction drops finished entries first, so long sessions lose finished lanes before anything else. Reproduced: start lane `child`, complete it, decode 4096 command items, then send a late `errored` update for `child`. The decoder emits `lane.failed` for `child`, alongside the raw capacity-gap evidence. Native Codex is unlikely to send `errored` after `completed`, so the practical risk is low. | src/ovcaq/drivers/codex.py:414 | Phase 0 | BLAKE |
| R5 | [1/3] | ⚪ | Drivers built by `build_driver` read any model value as "already resolved". So with tiers `{default: o3, o3: o3-pro}`, a request for tier key `o3` launches `o3` through `build_driver`, but `o3-pro` through a directly built driver. Only the supervisor uses `build_driver`, and the docs state this, but the same interface now behaves differently depending on how the driver was built. | src/ovcaq/drivers/edge.py:16 | Phase 1 | BLAKE |
| R6 | [1/3] | ⚪ | Already deferred: some explicit HTTP/status forms now come out `unknown`, though they classified correctly before this PRD. Confirmed: `HTTP Error 429: Too Many Requests`, `HTTP error 503`, `status=429` and `status_code=429` all give `unknown`. Tests pin `status=429` and `Error 429:` as `unknown`. The native Codex forms are covered. | src/ovcaq/drivers/codex_events.py:300 | Phase 0 | BLAKE |
| R7 | [1/3] | ⚪ | Cannot statically verify: the PRD phase-2 exit gate (`uv run pytest`) at HEAD 7fbcfd0. The settled reason ("current-HEAD verification: 7165 passed") no longer holds. The last green full run was at 9b8c55a (task 17, 7159 passed). Tasks 18-22 then changed the shared Claude workflow wrapper (`write_workflow_fixture` now emits a `fake_invocation` row) and renamed helpers. Every run recorded since then fails: the full suite shows 555 failed and 172 errors, and the narrow task-22 run fails all 6 cases of the phase-1 acceptance test plus both `test_supervisor_adapters.py` cases. Each failure is `PermissionError: 'ps'`. Collection succeeded, so the renamed imports resolve, but no passing run exists for the acceptance assertions at HEAD | tests/runtime/test_adapter_launch_routing.py | general | BOB |
| R8 | [1/3] | ⚪ | Test padding in a new file: `test_unrelated_item_type_does_not_transition_lane` and `test_unrelated_event_type_does_not_transition_lane` each run once per close status (interrupted, shutdown, not_found). The command_execution record and the `thread.started` record both turn into raw unknown before `item_lanes` is ever called (`item_tool` returns None because the record has no `command` field, and the decode branch has no `thread_id`). The follow-up close assertion repeats `test_unfinished_lane_fails_after_close_status`. So 6 cases run where 2 would do. Task 20 removed the same kind of padding. Fix: drop the `child_status` parametrize from both tests and use "shutdown" | tests/drivers/test_adapter_outcomes.py | 5 | BOB |

### Auto-dismissed (ledger)

- [BLAKE] ⚪ A late `running`, `completed` or `errored` update for a finished lane is dropped with no raw-unknown observation. A late close status (`shutdown`, `interrupted`, `not_found`) for the same lane does get raw-unknown evidence. The behavior is documented, and the raw session file still holds the line. | File: src/ovcaq/drivers/codex.py:383 — Requirements ambiguity: resume/restart generation semantics are not specified by this PRD. The existing contract deliberately freezes completed/failed identities and pins late updates. A binary tool name does not prove a native status sequence; changing this would undo reviewed stability without a fixture. Preserve for separately specified adapter lifecycle work.
- [BLAKE] ⚪ Already deferred: the health check and the launch resolve relative lookups against different directories. This covers relative command paths, relative PATH entries, and Codex's current-directory search when host PATH is empty. The probe uses the supervisor's working directory, but the launch runs in the project root, so the two can disagree when `--root` points somewhere else. With an empty host PATH, the Claude probe reports unhealthy while the launch would succeed. | File: src/ovcaq/drivers/claude.py:82 — Existing out-of-scope relative-path/cwd limitation; probe ownership redesign excluded by PRD. New Claude citation retained.

## Dispositions and operator decision

- R1: actionable Medium. Source inspection confirms adjacent whitespace quantifiers in the newly introduced diagnostic prefix. Alice's raw evidence records bounded measurements (16k/64k spaces); the 1 MiB time is explicitly an extrapolation. A bounded regex correction and adversarial whitespace regression are proposed, not implemented.
- R2 and R8: actionable overlapping test cleanup. Both name the same two discriminator tests: duplicate bodies and redundant close-status parametrization. Preserve both proposals; one bounded cleanup can address both.
- R3 and R7: resolved by fresh verification at reviewed HEAD: full suite 7154 passed; Bob's exact narrow acceptance check 8 passed. Sync, Ruff lint/format, mypy and build also pass. Counts are recorded in the sibling verification.json and last-verification.json. Historical failed evidence remains unchanged.
- R4: actionable Low cache-eviction edge. Source inspection confirms finished lane identities can be evicted before the late-update guard, allowing a later errored update to project failure. Blake's raw process evidence contains its reproducer. The bounded-cache policy predates this change; whether to expand completed-lane protection is an operator scope decision. No cache policy is changed.
- R5: discarded as intended contract. The PRD explicitly distinguishes the supervisor's once-resolved route from direct-driver tier precedence, requires the edge adaptation pattern, and forbids reversing the public direct precedence. The factory is the supervisor edge, with this behavior documented.
- R6: settled grammar deferral (prior five-repair R3). The additional bare reason-phrase examples were merged by the consolidator's citation/similarity matcher; all raw findings remain in Blake's section. Expanding non-native diagnostic grammar or reason-phrase matching requires a later explicit contract. Existing R3 grammar/R5 signal-flake deferrals, R4 empty-PATH limitation and R6 evidence-retention disposition from the five-repair review remain in force.

Four actionable rows (R1/R2/R4/R8), representing three repair areas, remain for operator disposition. No CRITICAL/HIGH finding was raised. All source rubric verdicts pass. The operator-approved recovery expressly authorizes this fresh review only: no further repairs, cap increase or finalization. Cycle/cap remain 2/2. No follow-up task was created, no implementation changed, and no convergence/finalize transition was authorized.

## Verification-check queue

Bob's VERIFY bucket names two independent project commands. Both were run by the coordinator at the reviewed code: `mise exec -- uv run pytest -q tests/runtime/test_adapter_launch_routing.py tests/runtime/test_supervisor_adapters.py` (8 passed, exit 0) and `mise exec -- uv run pytest -q --tb=line` (7154 passed, exit 0). The current cycle queue records both passing results; no unrun verification remains.

## Alice

[ALICE] 🟡 The new status prefix in `classify_failure` (src/ovcaq/drivers/codex_events.py:302) ends in `\s*:?\s*`. That is two whitespace runs side by side, so a native error with "status", "HTTP" or "error code" followed by a long run of whitespace backtracks in quadratic time. Measured at HEAD: 16k spaces took 0.55 s and 64k spaces took 8.34 s. The old bare-number regex had no such run. Decode runs inline in the supervisor read loop (src/ovcaq/runtime/supervisor.py:516) on frames up to 1 MiB (src/ovcaq/events/tail.py:60). Python's `re` holds the GIL, so the watchdog cannot fire while it runs. A full 1 MiB frame extrapolates to roughly 35 minutes (a guess, not run). The trigger needs tens of thousands of whitespace characters right after the keyword, so it is unlikely to happen. Fix: use `\s*(?::\s*)?` instead. It took 1.2 ms at 64k and matched the same way on "HTTP status: 429", "status code: 429", "last status: 429", "HTTP 429" and "status=429". Also add a regression test that expects "status" + 200,000 spaces + "x" to classify as unknown | File: src/ovcaq/drivers/codex_events.py | Task: 6
[ALICE] 🟡 `test_unrelated_item_type_does_not_transition_lane` (tests/drivers/test_adapter_outcomes.py:204) and `test_unrelated_event_type_does_not_transition_lane` (tests/drivers/test_adapter_outcomes.py:231) are line-for-line copies. They differ only in one `collab_record` keyword: `item_type="command_execution"` in one, `event_type="thread.started"` in the other. Merge them into one test parametrized over that keyword dict (passed as `**override`). That cuts about 24 lines and keeps the same coverage | File: tests/drivers/test_adapter_outcomes.py | Task: 5
[ALICE] ⚪ The recorded verification for this cycle has no green full suite. It shows 555 failed and 172 errors, which it attributes to the sandbox denying `ps`. I reran at HEAD 6761a37 with `mise exec -- uv run pytest -q`: 7154 passed, 0 failed, 0 skipped, exit 0. `ruff check`, `ruff format --check` and `mypy src/ovcaq` also exit 0. Record this green run before closing the phase-2 gate | File: docs/dev/project-management/autopilot/reports/00053-three-repair-20261012-evidence/verification.json | Task: general

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

## Blake

Six findings, all low severity. The full gate passes and nothing blocks the PRD. The three unsettled ones sit on edge paths, and the other three were already deferred in earlier review rounds.

Gates (run fresh): the six acceptance test files gave `274 passed`, and the full suite gave `7154 passed`. `ruff check` reported `All checks passed!`, `ruff format --check` reported `236 files already formatted`, and mypy reported `no issues found in 61 source files`. `uv build` built both the sdist and the wheel, output to `/tmp`. Nothing changed outside `src/ovcaq/drivers`, so driver API 2, protocol 1 and state schema 1 are untouched. The PRD's Phases 0/1/2 are scored in order as B15/B16/B17.

[BLAKE] ⚪ A completed lane can still turn into a failure after the identity cache fills. At 4096 entries, eviction drops finished entries first, so long sessions lose finished lanes before anything else. Reproduced: start lane `child`, complete it, decode 4096 command items, then send a late `errored` update for `child`. The decoder emits `lane.failed` for `child`, alongside the raw capacity-gap evidence. Native Codex is unlikely to send `errored` after `completed`, so the practical risk is low. | File: src/ovcaq/drivers/codex.py:414 | Task: Phase 0
[BLAKE] ⚪ A late `running`, `completed` or `errored` update for a finished lane is dropped with no raw-unknown observation. A late close status (`shutdown`, `interrupted`, `not_found`) for the same lane does get raw-unknown evidence. The behavior is documented, and the raw session file still holds the line. | File: src/ovcaq/drivers/codex.py:383 | Task: Phase 0
[BLAKE] ⚪ Drivers built by `build_driver` read any model value as "already resolved". So with tiers `{default: o3, o3: o3-pro}`, a request for tier key `o3` launches `o3` through `build_driver`, but `o3-pro` through a directly built driver. Only the supervisor uses `build_driver`, and the docs state this, but the same interface now behaves differently depending on how the driver was built. | File: src/ovcaq/drivers/edge.py:16 | Task: Phase 1
[BLAKE] ⚪ Already deferred: some explicit HTTP/status forms now come out `unknown`, though they classified correctly before this PRD. Confirmed: `HTTP Error 429: Too Many Requests`, `HTTP error 503`, `status=429` and `status_code=429` all give `unknown`. Tests pin `status=429` and `Error 429:` as `unknown`. The native Codex forms are covered. | File: src/ovcaq/drivers/codex_events.py:300 | Task: Phase 0
[BLAKE] ⚪ Already deferred: the health check and the launch resolve relative lookups against different directories. This covers relative command paths, relative PATH entries, and Codex's current-directory search when host PATH is empty. The probe uses the supervisor's working directory, but the launch runs in the project root, so the two can disagree when `--root` points somewhere else. With an empty host PATH, the Claude probe reports unhealthy while the launch would succeed. | File: src/ovcaq/drivers/claude.py:82 | Task: Phase 1
[BLAKE] ⚪ Already deferred: an HTTP status number given only with its reason phrase, with no `HTTP`/`status` prefix, now comes out `unknown`. Examples: `503 Service Unavailable` and `429 Too Many Requests`. Before this PRD these classified correctly. The spec's context rule allows this, but those reason phrases could have been kept as word-based diagnostics. | File: src/ovcaq/drivers/codex_events.py:304 | Task: Phase 0

B1: pass
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: pass
B16: pass
B17: pass
B18: pass
B19: pass

Next: You: decide whether to fix the eviction issue (finding 1) in this PRD or defer it with the other edge-path items.

## Bob

[BOB] ⚪ Cannot statically verify: the PRD phase-2 exit gate (`uv run pytest`) at HEAD 7fbcfd0. The settled reason ("current-HEAD verification: 7165 passed") no longer holds. The last green full run was at 9b8c55a (task 17, 7159 passed). Tasks 18-22 then changed the shared Claude workflow wrapper (`write_workflow_fixture` now emits a `fake_invocation` row) and renamed helpers. Every run recorded since then fails: the full suite shows 555 failed and 172 errors, and the narrow task-22 run fails all 6 cases of the phase-1 acceptance test plus both `test_supervisor_adapters.py` cases. Each failure is `PermissionError: 'ps'`. Collection succeeded, so the renamed imports resolve, but no passing run exists for the acceptance assertions at HEAD | File: tests/runtime/test_adapter_launch_routing.py | Task: general
[BOB] ⚪ Test padding in a new file: `test_unrelated_item_type_does_not_transition_lane` and `test_unrelated_event_type_does_not_transition_lane` each run once per close status (interrupted, shutdown, not_found). The command_execution record and the `thread.started` record both turn into raw unknown before `item_lanes` is ever called (`item_tool` returns None because the record has no `command` field, and the decode branch has no `thread_id`). The follow-up close assertion repeats `test_unfinished_lane_fails_after_close_status`. So 6 cases run where 2 would do. Task 20 removed the same kind of padding. Fix: drop the `child_status` parametrize from both tests and use "shutdown" | File: tests/drivers/test_adapter_outcomes.py | Task: 5

FIX:
- Close-status parametrization on two tests whose records never reach `item_lanes` (6 cases where 2 would do) — tests/drivers/test_adapter_outcomes.py:203 and tests/drivers/test_adapter_outcomes.py:230 — remove `@pytest.mark.parametrize("child_status", ...)` from both tests and pass the literal "shutdown" to both `collab_record` calls in each test
VERIFY:
- No passing run at HEAD 7fbcfd0 for the phase-1 routing acceptance test or the full suite; every run recorded since task 18 fails with `PermissionError: 'ps'` — on a host where `ps` is allowed, run `mise exec -- uv run pytest -q tests/runtime/test_adapter_launch_routing.py tests/runtime/test_supervisor_adapters.py` (expect 8 passed), then `mise exec -- uv run pytest -q` (expect 0 failed, 0 errors), and record the counts in `docs/dev/project-management/autopilot/last-verification.json`
KNOWN:
- (none)

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

Verdict: 8 findings
Tests: 7154 passed, 0 failed, 0 skipped (suite run this cycle via mise at 6761a37; 2 temporary-directory cleanup warnings)
