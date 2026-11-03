---
prd: docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
review: 2
date: 2026-10-12
head_sha: b1fab1866840c21ba0b091b7c676472aab961f12
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  bob: 6c58d6a8
---

# Fresh post-repair review: PRD00053

Diff range: 7819970d7f807d6fad07b115af4f0df1fbc4a248..b1fab1866840c21ba0b091b7c676472aab961f12

autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/alice-output.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/blake-output.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/bob-output.txt.receipt.json
provider_review_guard: satisfied
codex_rung_guard: not fired

The actual implementation-model provider guard supersedes the legacy rung guard. No Eve ran. All three fresh isolated external helpers exited 0, serving claude-opus-5-5 with requested xhigh effort. Session IDs and immutable raw evidence are in the receipts. Carl remains disabled under the prior operator authorization. Each lens covered the full PRD work range; Blake received only the PRD and his full blind rubric.

## Review Summary

All 17 tasks are complete. The six authorized repairs are present. Cycle and rework cap remain 2. The implementation audit retains all prior contributing attempts and adds task-15 test/implementation authors plus task-16/17 direct micro edits. Receipts bind the refreshed implementation snapshot. Prior reviews and receipts are preserved.

Staging reused verification for unchanged product code at 9b8c55a; only workflow artifacts changed after that commit. Blake independently ran the six acceptance files (279 passed), full suite (7159 passed), sync --locked, Ruff lint/format, mypy and build successfully. Context pack unavailable because the repo is not registered with gita. Fail-first replay skipped because worktree creation was denied; this limitation remains explicit. Mechanical shape check reported no findings. Prior verification queues are empty.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [1/3] | 🟡 | tests/runtime/test_adapter_launch_routing.py:30 re-implements the runpy Claude wrapper from tests/runtime/test_supervisor_adapters.py:44. The wrapper rebinds `fake_codex.workflow.__globals__['__file__']` to the Claude fixture, and the new copy adds only an `edge['emit_invocation'](sys.argv[1:])` call. That leaves two copies of a hack tied to fake_codex.py internals, and they will drift apart. Keep one wrapper builder in test_supervisor_adapters.py that always emits the invocation (Codex `main()` already emits it unconditionally) and call it from both files | tests/runtime/test_adapter_launch_routing.py | 11 | BOB |
| R2 | [1/3] | ⚪ | CHANGELOG.md:46 still says completed and failed Codex receiver lanes stay terminal "under late updates", with no qualifier. Task 16 fixed this same overclaim in docs/driver-protocol.md:243, which now says "Remembered completed and failed lanes". Lanes stop being remembered once they are evicted (src/ovcaq/drivers/codex.py:413 evicts finished identities first, at 4096 identities). After that, a late `running` update starts the lane again. Add "remembered" to the CHANGELOG entry so it matches the protocol doc | CHANGELOG.md | 16 | ALICE |
| R3 | [1/3] | ⚪ | The bare word "status" counts as an HTTP context, so ordinary counts after it still get a failure class. Confirmed: "status 401 files processed" and "exit status 401" both return `authentication`. Inside the PRD's wording, but no negative control is pinned for it | src/ovcaq/drivers/codex_events.py:302 | P0-T1 | BLAKE |
| R4 | [1/3] | ⚪ | A late update for a lane that already finished is now dropped with no `raw_unknown` record, while a late close status for the same lane does emit one. So a contradictory late "errored" after "completed" leaves no trace in the normalized stream; only raw.jsonl keeps it. `item_lanes(started_lanes=None)` also keeps its optional default: a caller that leaves it out never fails a lane on close (review R1 asked for it to be required) | src/ovcaq/drivers/codex.py:383 | P0-T1 | BLAKE |
| R5 | [1/3] | ⚪ | docs/driver-protocol.md:185 says "the driver preserves that resolved value", but only drivers built by `build_driver` do that. A `CodexDriver` constructed directly and passed to `Supervisor` (as in tests/runtime/test_rework_thread_conflict.py:108) still remaps a colliding value through tier-key precedence. Reword to "the driver built by `build_driver` preserves that resolved value" | docs/driver-protocol.md | 4 | BOB |
| R6 | [1/3] | ⚪ | CHANGELOG.md:45 puts two fixes in one entry. Its clause "retry model capacity as connectivity through bounded WAIT/retry exhaustion" does not read as a sentence, and "reqwest" is implementation jargon. Split it into a numeric-context entry and a separate entry: "classify 'Selected model is at capacity' as connectivity so it gets bounded WAIT retries instead of rate-limit handling" | CHANGELOG.md | 16 | BOB |
| R7 | [1/3] | ⚪ | tests/runtime/test_adapter_health.py:90 runs `command_name` over three names ("fixture-agent-health", "overlay-runner", "queue-worker"). In both probes all three take the same code path, so there are 6 cases where 2 would do. R8 removed the same kind of padding from test_adapter_outcomes.py. Keep one name | tests/runtime/test_adapter_health.py | 3 | BOB |

### Auto-dismissed (ledger)

- [BLAKE] ⚪ Some real-looking HTTP lines that lack an "HTTP"/"status"/"error code" prefix are now `unknown`. Confirmed by direct call: "429 Too Many Requests", "503 Service Unavailable", "502 Bad Gateway", "403 Forbidden", `{"status": 429}` and `statusCode: 503`. Before this change they were classified, so a bare "429 Too Many Requests" now takes the immediate generic retry instead of the rate-limit wait or halt. "401 Unauthorized" still works through the word "unauthorized", so the four codes behave differently. The forms Codex actually emits ("unexpected status 503 …", "last status: 429 …", reqwest, HTTP/x) are covered and pinned | File: src/ovcaq/drivers/codex_events.py:300 — Requirements ambiguity: mixed diagnostic-prefix/ordinary-count messages need an explicit precedence contract. Existing scope requires diagnostic status contexts and ordinary count negatives; do not invent a broader prose grammar or silently change precedence. Keep the confirmed counterexamples for later specified work.
- [BLAKE] ⚪ Suspected, not reproduced: health checks look up the executable relative to the supervisor's own working directory, but the real launch runs in the project root (`cwd=request.root`). The Claude check uses `shutil.which`; the Codex check starts its probe without setting a working directory. A relative PATH entry, an empty PATH segment, or a relative command can therefore pass the check and fail at launch, or the reverse, whenever `--root` differs from the process directory. The documented empty-host-PATH case also differs: Claude reports unhealthy while the launch would search the root directory. The exit criterion "health checks and actual spawn agree" holds only for absolute PATH entries | File: src/ovcaq/drivers/claude.py:82 — Existing out-of-scope relative-path/cwd limitation; probe ownership redesign excluded by PRD. New Claude citation retained.

## Decision Gate

R1: confirmed duplicated runpy wrapper at test_adapter_launch_routing.py:30 and test_supervisor_adapters.py:44-50; bounded test-helper consolidation suggested. Medium, actionable pending authorization.
R2: confirmed CHANGELOG.md:46 lacks the remembered-identity qualifier now present in protocol documentation. Low, actionable pending authorization.
R3: settled deferral. Ordinary-count wording following a diagnostic status prefix needs a separately specified precedence contract. Same limitation already recorded at codex_events.py:301; no new repair.
R4: settled terminal-identity contract. Late updates preserve completed/failed identities and raw session output survives. Changing generation/restart or normalized evidence policy remains out of scope. The optional item_lanes default is existing helper behavior, not a new public requirement; production decode always supplies remembered unfinished identities. Discard this repeated finding without changing code.
R5: confirmed protocol wording overstates raw driver behavior: edge build_driver adaptation preserves route-selected values, while direct drivers retain tier-key precedence. Low documentation qualification, actionable pending authorization.
R6: confirmed changelog sentence combines numeric contexts and capacity behavior; readability suggestion is bounded. Low, actionable pending authorization.
R7: confirmed three command names exercise the same lookup path for each provider. Low test-padding cleanup, actionable pending authorization.

The consolidator auto-dismissed Blake's unsupported diagnostic forms using a related ledger reason. The gate corrects that rationale here: native bare-status, reqwest and HTTP/x forms are pinned; the cited bare reason phrases, JSON status and statusCode forms have no demonstrated native event fixture and are outside the operator-authorized widening. This is a scope decision, not a claim that the observed UNKNOWN results are false. Blake's relative-lookup issue matches the existing out-of-scope cwd/probe deferral.

Five distinct actionable findings remain: one Medium and four Low. No Critical or High. All raw rubric verdicts passed. The operator's one-time scope explicitly requires a new decision if fresh review needs further implementation. Do not create tasks, repair, increase cap, increment cycle or finalize. Persist post_repair_review_decision pause.

## Alice

**Anthropic**

Provider: anthropic; served model: claude-opus-5-5; requested effort: xhigh; session: 72270a79-d858-47f4-bf6a-48f6d7ce563f; source: docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/alice-output-71006cca714e4990ac519742ea445bf2.jsonl

[ALICE] ⚪ CHANGELOG.md:46 still says completed and failed Codex receiver lanes stay terminal "under late updates", with no qualifier. Task 16 fixed this same overclaim in docs/driver-protocol.md:243, which now says "Remembered completed and failed lanes". Lanes stop being remembered once they are evicted (src/ovcaq/drivers/codex.py:413 evicts finished identities first, at 4096 identities). After that, a late `running` update starts the lane again. Add "remembered" to the CHANGELOG entry so it matches the protocol doc | File: CHANGELOG.md | Task: 16

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

**Anthropic**

Provider: anthropic; served model: claude-opus-5-5; requested effort: xhigh; session: 50f8a28a-df86-420f-8e2d-a4ad1cc4bd6a; source: docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/blake-output-a6d87910ee7743fd83acd241486d3ed5.jsonl

Ran myself: the 6 acceptance test files (279 passed), the full suite (7159 passed), ruff check, ruff format --check, mypy and uv build (all clean), plus `uv sync --all-groups --locked` (I used `--locked` to avoid rewriting the lockfile). I also called `classify_failure` directly on extra inputs. No Critical or High issues. All four findings are Low, three of them confirmed by those runs and one suspected.

[BLAKE] ⚪ Some real-looking HTTP lines that lack an "HTTP"/"status"/"error code" prefix are now `unknown`. Confirmed by direct call: "429 Too Many Requests", "503 Service Unavailable", "502 Bad Gateway", "403 Forbidden", `{"status": 429}` and `statusCode: 503`. Before this change they were classified, so a bare "429 Too Many Requests" now takes the immediate generic retry instead of the rate-limit wait or halt. "401 Unauthorized" still works through the word "unauthorized", so the four codes behave differently. The forms Codex actually emits ("unexpected status 503 …", "last status: 429 …", reqwest, HTTP/x) are covered and pinned | File: src/ovcaq/drivers/codex_events.py:300 | Task: P0-T1
[BLAKE] ⚪ The bare word "status" counts as an HTTP context, so ordinary counts after it still get a failure class. Confirmed: "status 401 files processed" and "exit status 401" both return `authentication`. Inside the PRD's wording, but no negative control is pinned for it | File: src/ovcaq/drivers/codex_events.py:302 | Task: P0-T1
[BLAKE] ⚪ Suspected, not reproduced: health checks look up the executable relative to the supervisor's own working directory, but the real launch runs in the project root (`cwd=request.root`). The Claude check uses `shutil.which`; the Codex check starts its probe without setting a working directory. A relative PATH entry, an empty PATH segment, or a relative command can therefore pass the check and fail at launch, or the reverse, whenever `--root` differs from the process directory. The documented empty-host-PATH case also differs: Claude reports unhealthy while the launch would search the root directory. The exit criterion "health checks and actual spawn agree" holds only for absolute PATH entries | File: src/ovcaq/drivers/claude.py:82 | Task: P1-T2
[BLAKE] ⚪ A late update for a lane that already finished is now dropped with no `raw_unknown` record, while a late close status for the same lane does emit one. So a contradictory late "errored" after "completed" leaves no trace in the normalized stream; only raw.jsonl keeps it. `item_lanes(started_lanes=None)` also keeps its optional default: a caller that leaves it out never fails a lane on close (review R1 asked for it to be required) | File: src/ovcaq/drivers/codex.py:383 | Task: P0-T1

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

## Bob

**Anthropic**

Provider: anthropic; served model: claude-opus-5-5; requested effort: xhigh; session: f4334e85-8f02-4e3b-9493-d8686c7b34a0; source: docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/bob-output-cebe25bde513499a910b4c0179c35df1.jsonl

[BOB] 🟡 tests/runtime/test_adapter_launch_routing.py:30 re-implements the runpy Claude wrapper from tests/runtime/test_supervisor_adapters.py:44. The wrapper rebinds `fake_codex.workflow.__globals__['__file__']` to the Claude fixture, and the new copy adds only an `edge['emit_invocation'](sys.argv[1:])` call. That leaves two copies of a hack tied to fake_codex.py internals, and they will drift apart. Keep one wrapper builder in test_supervisor_adapters.py that always emits the invocation (Codex `main()` already emits it unconditionally) and call it from both files | File: tests/runtime/test_adapter_launch_routing.py | Task: 11
[BOB] ⚪ docs/driver-protocol.md:185 says "the driver preserves that resolved value", but only drivers built by `build_driver` do that. A `CodexDriver` constructed directly and passed to `Supervisor` (as in tests/runtime/test_rework_thread_conflict.py:108) still remaps a colliding value through tier-key precedence. Reword to "the driver built by `build_driver` preserves that resolved value" | File: docs/driver-protocol.md | Task: 4
[BOB] ⚪ CHANGELOG.md:45 puts two fixes in one entry. Its clause "retry model capacity as connectivity through bounded WAIT/retry exhaustion" does not read as a sentence, and "reqwest" is implementation jargon. Split it into a numeric-context entry and a separate entry: "classify 'Selected model is at capacity' as connectivity so it gets bounded WAIT retries instead of rate-limit handling" | File: CHANGELOG.md | Task: 16
[BOB] ⚪ tests/runtime/test_adapter_health.py:90 runs `command_name` over three names ("fixture-agent-health", "overlay-runner", "queue-worker"). In both probes all three take the same code path, so there are 6 cases where 2 would do. R8 removed the same kind of padding from test_adapter_outcomes.py. Keep one name | File: tests/runtime/test_adapter_health.py | Task: 3

FIX:
- Duplicated runpy Claude fake wrapper — tests/runtime/test_adapter_launch_routing.py:30 — move the wrapper builder into tests/runtime/test_supervisor_adapters.py so it always calls `emit_invocation`, then use it from `workflow_agent` and `configured_workflow`
- Resolved-model doc wording claims too much — docs/driver-protocol.md:185 — replace "the driver preserves" with "the driver built by `build_driver` preserves"
- Fused, hard-to-parse changelog entry — CHANGELOG.md:45 — split it into a numeric HTTP/status/error-code context entry and a capacity-as-connectivity entry, and drop "reqwest"
- Command-name parametrization adds cases that test nothing new — tests/runtime/test_adapter_health.py:90 — remove the `command_name` parametrize and keep `fixture-agent-health`
VERIFY:
- (none)
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

Verdict: 7 findings
Tests: 7159 passed, 0 failed, 0 skipped (reused work verification at 9b8c55a; independently rerun by Blake this cycle)
