---
prd: docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
review: 2
date: 2026-10-10
head_sha: 307b7921355885221e8f8e4f66ba2a678b9f43c5
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  alice: 41c297a4
  blake: 2305d9ee
  bob: c47fd1ee
---

# Review: 00053-adapter-operational-corrections-v1

Diff range: `7819970d7f807d6fad07b115af4f0df1fbc4a248..307b7921355885221e8f8e4f66ba2a678b9f43c5`

codex_rung_guard: not fired
The model-provider guard supersedes the legacy launcher guard. Eve did not run.
provider_review_guard: satisfied
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/reviews/alice-output-00053-c2-20261010.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/reviews/blake-output-00053-c2-20261010-isolated.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/reviews/bob-output-00053-c2-20261010.txt.receipt.json

carl: skipped (operator-authorized repair batch; no Gemini/Copilot export)
pack: failed (repository not registered with gita; complete personas and rubrics retained)

## Review Summary

All ten completed tasks and the entire PRD work range received fresh isolated opposite-company Claude Opus 5.5/xhigh reviews. Every source R/B/D verdict is retained verbatim below. The original Blake run read git history, a source review and diffs, violating the host blind lens: preserved, excluded, and replaced once. The replacement's 56 tool calls contain no forbidden diff/history/review-artifact reads; it received only the PRD and product access. Alice and Bob exposed no current sibling review outputs. No implementation thread was resumed.

Implementation audit covers all original authors, contributing attempts, test writers and direct rework edits. The cycle1 reviewed snapshot is separately preserved. Current cycle2 fingerprint is 5b0275d8463f21dea0975e2233ffd8116b02b2a889adcf4a140061833044d869; review-route returned Anthropic. Source launcher labels are not model evidence.

Coordinator verification at reviewed HEAD: 7141 passed, zero failures/skips; sync, Ruff lint/format, mypy and build passed. Two pre-existing pytest cleanup warnings remain. Restricted process tests failed due ps denial; the interrupted run and approved full retry are recorded in 00053-review-2-sandbox-verification.json and 00053-review-2-verification.json. Stage incorrectly reused the preceding store-only commit's test record; the final counts come from this cycle's actual-HEAD run. Mechanical tautology check found none. Fail-first replay was skipped because sandbox worktree creation was denied; this limitation is retained rather than fabricated as coverage. Previous check queue is empty. Bob's VERIFY item is not queued: it names multiple binary-search commands, not a single project verification command; it remains ordinary R1 evidence.

CLI telemetry: stage opened Bob's row before dispatch. Alice/Blake transport rows were backfilled; their timestamps are bookkeeping, while immutable receipts provide actual start/completion times. All dispatches are awaited. Raw artifacts and prompts are backed up in reports/00053-review-2-evidence; receipt-addressed originals are retained.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/3] | 🟡 | Codex's HTTP client (reqwest) reports status errors as "HTTP status client error (429 Too Many Requests) for url (...)". The new numeric check still returns `unknown` for that form. I ran `classify_failure` on that string, on "HTTP status server error (503 Service Unavailable) for url (...)", on "HTTP status client error (403 Forbidden) ..." and on "HTTP/1.1 503 Service Unavailable", and all four give `unknown`. The pre-change code returned rate_limit, connectivity and permission for them. Both "HTTP status client error" and "HTTP status server error" are present as strings in the installed codex-cli 0.162.1 binary (confirmed with `rg -a`). Whether they ever reach a `turn.failed` message is my guess, not something I checked. If they do, a real 429 skips the rate-limit wait and a real 502/503 skips the bounded connectivity WAIT, just like the cycle-1 HIGH. This also contradicts docs/driver-protocol.md:271 ("require HTTP, status or error-code context"). Fix: also accept the code when the standard reason phrase follows it (e.g. `(?:403 forbidden|429 too many requests|502 bad gateway|503 service unavailable)`). Add the reqwest and HTTP/1.1 forms as literal positives in tests/drivers/test_adapter_failure_classes.py:63, and keep the ordinary-count negatives | src/ovcaq/drivers/codex_events.py:301 | 7 | ALICE, BLAKE, BOB |
| R2 | [2/3] | ⚪ | `INVALID_OPTIONS` was moved up to module level so the now-deleted factory test could share it. It has a single user again (`test_constructor_rejects_unknown_or_invalid_options`). Inline it back into that test's `@pytest.mark.parametrize`, so the only change left in that test is the `raised.type is ValueError` line | tests/drivers/test_codex_launch.py:140 | 8 | ALICE, BOB |
| R3 | [1/3] | 🟡 | The `continue` at codex.py:383 drops every native update for a lane that has already finished. codex-cli 0.162.1 ships a `resume_agent` tool ("Resume a previously closed agent by id so it can receive send_input"; I confirmed the string in the binary). So a lane can legitimately go completed → close → resume → running → errored. With the `continue`, the resumed run's running and errored updates disappear with no trace, and a later interrupt or shutdown of the resumed run becomes raw unknown instead of `lane.failed`. The pre-change code reported these. The TUI already handles a restart, because the last write wins (src/ovcaq/tui/model.py:607). The PRD only requires that close statuses do not fail a completed lane, and the unfinished-only filter at src/ovcaq/drivers/codex.py:372 already does that on its own. Fix: delete lines 383-384. Then flip `test_finished_lane_late_update_retains_only_non_lane_observations` (tests/drivers/test_adapter_outcomes.py:266) so it expects running → `lane.progress` and errored → `lane.failed`, and reword docs/driver-protocol.md:243. Confidence: the tool is confirmed; the exact `agents_states` sequence after a resume is my guess | src/ovcaq/drivers/codex.py:383 | 7 | ALICE |
| R4 | [1/3] | ⚪ | The CHANGELOG PATH entry says the change checks "both native adapters' executables" and preserves "standard missing/empty host PATH lookup". In fact only the Claude probe changed (Codex already used the merged environment). With an empty host PATH, the Claude probe is unhealthy while the Codex probe searches the current directory, which docs/driver-protocol.md:37 now says correctly. Reword the entry to say the fix is for Claude and to name that split | CHANGELOG.md:43 | 9 | ALICE |
| R5 | [1/3] | ⚪ | `classify_failure` now collapses whitespace (`" ".join(detail.split())`), so "Rate\tlimit reached" becomes rate_limit. The pre-change code returned unknown for it. That widens matching beyond "retain existing word diagnostics", and neither the CHANGELOG nor the protocol doc mentions it. The test `test_native_word_diagnostics_retain_case_and_whitespace_variants` calls it "retain" even though the whitespace case is new behavior. Either document the widening and rename the test, or drop line 300 and the tab case | src/ovcaq/drivers/codex_events.py:300 | 6 | ALICE |
| R6 | [1/3] | ⚪ | The normal Codex sequence (`wait` reports completed, then `close_agent` reports shutdown) emits `raw.unknown` on every close of a completed lane. The tests pin this at tests/drivers/test_adapter_outcomes.py:89. The lane result is right, but routine flows now show recurring normalization gaps. | src/ovcaq/drivers/codex_events.py:233 | P0-T1 | BLAKE |
| R7 | [1/3] | ⚪ | No supervisor-level regression covers the Claude model-collision path. The Claude edge wrapper behaves correctly: I checked directly that `{default: o3, o3: o3-pro, x: o3}` launches `o3` and `o3-pro`. But tests/runtime/test_adapter_launch_routing.py runs only the Codex fake through the supervisor, so a regression in `_ResolvedModelClaudeDriver` would go unnoticed. | src/ovcaq/drivers/edge.py:23 | P1-T1 | BLAKE |
| R8 | [1/3] | ⚪ | `assert retries.rate_limit == 0` can never fail. It checks the frozen `RetryState` the test built with `rate_limit=0`, and `decide` cannot change it (src/ovcaq/runtime/decision.py:84). Lines 200-201 already pin the non-rate-limit path | tests/drivers/test_adapter_failure_classes.py:225 | 6 | BOB |
| R9 | [1/3] | ⚪ | CHANGELOG says "preserving standard missing ... host PATH lookup", but the Claude probe changed. With no host PATH it now falls back to `os.defpath` (`/bin:/usr/bin`, src/ovcaq/drivers/claude.py:82). The old `shutil.which(command)` used `CS_PATH` (`/usr/bin:/bin:/usr/sbin:/sbin` here, confirmed with `getconf PATH` and the stdlib source). The new value matches the subprocess spawn, as the design asks, so only the wording is wrong | CHANGELOG.md:43 | 4 | BOB |
| R10 | [1/3] | ⚪ | The test for an absent host PATH probes `sh`, which is in both `os.defpath` and `CS_PATH`. It cannot tell the design's spawn-matching `os.defpath` fallback from the old `CS_PATH` one, so going back to `shutil.which(command, path=None)` would still pass (found by reading, not run) | tests/runtime/test_adapter_health.py:250 | 3 | BOB |

| R11 | [1/3] | ⚪ | A status prefix followed by an ordinary count still classifies. `status: 401 tests passed` returns `authentication` and `error code: 503 records` returns `connectivity` (confirmed by probe). The negative tests only cover counts with no status word in front. | src/ovcaq/drivers/codex_events.py:301 | P0-T1 | BLAKE |

| R12 | [1/3] | ⚪ | Suspected, not confirmed: a Codex `turn.failed` reading "Authentication failed" classifies as `unknown` (pinned at tests/drivers/test_adapter_failure_classes.py:129). That means a retry or park instead of the operator-access halt. The Claude classifier treats "authentication" as authentication, so the two adapters disagree. I could not check whether this was already the behavior before this change. | src/ovcaq/drivers/codex_events.py:306 | P0-T1 | BLAKE |

### Auto-dismissed (ledger)

- [BLAKE] ⚪ The health check and the real launch can resolve the executable from different directories. The Codex probe spawns without `cwd`, and the Claude probe runs `shutil.which` in the supervisor's working directory, but the launch spawns with `cwd=request.root`. With relative PATH entries, or an empty host PATH, the probe can disagree with the spawn, which goes against the Phase 1 exit criterion. docs/driver-protocol.md:37 documents the empty-PATH case but not relative overlay entries. | File: src/ovcaq/drivers/codex.py:47 — Known pre-existing caller/request-root cwd disagreement. PRD explicitly excludes probe descendant/ownership redesign and preserves Codex probe behavior. Defer outside this repair; do not change the current scope.


Consolidation used the installed script. Its heuristic merged distinct Blake ordinary-count and authentication findings into the same file's numeric-diagnostic row; R11/R12 restore those exact findings separately. All raw verdicts/findings remain below.

## Decision Gate

- R1: fix — Explicit HTTP status-line and reqwest contexts are bounded in-scope diagnostic coverage; preserve ordinary numeric counts and existing precedence.
- R2: fix — Remove single-use test indirection after deletion of its second consumer.
- R3: defer — Requirements ambiguity: resume/restart generation semantics are not specified by this PRD. The existing contract deliberately freezes completed/failed identities and pins late updates. A binary tool name does not prove a native status sequence; changing this would undo reviewed stability without a fixture. Preserve for separately specified adapter lifecycle work.
- R4: fix — Correct user-facing PATH changelog wording.
- R5: fix — Document whitespace normalization and name its regression honestly; preserve intentional classification behavior.
- R6: discard — Intentional documented raw-evidence rule: unsupported terminal close statuses on finished lanes retain RAW_UNKNOWN while preserving terminal identity. Exact tests and protocol document it. UI gap-noise redesign is outside this PRD; deleting evidence would contradict the reviewed contract.
- R7: fix — Add a fake-supervisor regression for the existing Claude edge caller affected by the shared helper; no live inference.
- R8: fix — Delete an assertion of an unchanged frozen input; decision-output assertions already bind the non-quota path.
- R9: fix — Same PATH changelog edit as R4, retaining both exact source findings in one group.
- R10: fix — Make the absent-PATH fixture distinguish os.defpath from CS_PATH; no production behavior change.
- R11: defer — Requirements ambiguity: mixed diagnostic-prefix/ordinary-count messages need an explicit precedence contract. Existing scope requires diagnostic status contexts and ordinary count negatives; do not invent a broader prose grammar or silently change precedence. Keep the confirmed counterexamples for later specified work.
- R12: discard — The old classifier did not match authentication failed; cycle1 deliberately removed that added pattern to retain existing word diagnostics. This is known original behavior, not a lost required diagnostic. Existing authentication fixtures use literal invalid-credentials/unauthorized oracles.

No unresolved CRITICAL/HIGH remains. MEDIUM/LOW fixes require the source tail sweep; no cap increase is requested. Convergence/finalization is blocked before implementation by the host/source tail-sweep provenance conflict: source says to finalize without another review after sweeping, while host convergence requires unchanged implementation provenance and receipts for the reviewed snapshot. New tail attempts would invalidate that fingerprint. No tail work has run; no repaired-source final-success claim is made.

## Source-finding closure evidence

Source is historical 00009-codex-adapter-v1-review-2.md; original findings remain untouched.

| Source refs | Current evidence and limits |
| --- | --- |
| R1 | Completed-lane stability and unsupported-close evidence pinned by task5/7/8, outcome and terminal regressions; routine RAW_UNKNOWN is documented. Resume/restart semantics R3 deferred as requirements ambiguity. |
| R4 | Capacity is connectivity with bounded WAIT/retry exhaustion; independent literal regressions pass. |
| R12 | Fixture classes remain independent literal oracles across all failure families. |
| R19 | Supervised Codex once-resolved model collision verified through fake supervisor; direct precedence preserved. R7 requests extra shared-helper Claude caller coverage. |
| R20 | Original ordinary-count and bare-status HIGH repaired, with exact positive/negative regressions; new HTTP-context R1 and mixed-context/count R11 remain unresolved. No complete classification-repair success claim. |
| R22/R23 | Effective PATH and both-adapter unhealthy/no-spawn checks pass; empty-host test/doc repair confirmed. R10 stronger missing-PATH control and changelog wording remain actionable. Existing probe/launch cwd limitation remains deferred. |

## Alice

Provider: Anthropic; observed model: claude-opus-5-5; effort: xhigh; session: a6016b31-fa26-421f-8db2-fb64ee96d88c.

[ALICE] 🟡 Codex's HTTP client (reqwest) reports status errors as "HTTP status client error (429 Too Many Requests) for url (...)". The new numeric check still returns `unknown` for that form. I ran `classify_failure` on that string, on "HTTP status server error (503 Service Unavailable) for url (...)", on "HTTP status client error (403 Forbidden) ..." and on "HTTP/1.1 503 Service Unavailable", and all four give `unknown`. The pre-change code returned rate_limit, connectivity and permission for them. Both "HTTP status client error" and "HTTP status server error" are present as strings in the installed codex-cli 0.162.1 binary (confirmed with `rg -a`). Whether they ever reach a `turn.failed` message is my guess, not something I checked. If they do, a real 429 skips the rate-limit wait and a real 502/503 skips the bounded connectivity WAIT, just like the cycle-1 HIGH. This also contradicts docs/driver-protocol.md:271 ("require HTTP, status or error-code context"). Fix: also accept the code when the standard reason phrase follows it (e.g. `(?:403 forbidden|429 too many requests|502 bad gateway|503 service unavailable)`). Add the reqwest and HTTP/1.1 forms as literal positives in tests/drivers/test_adapter_failure_classes.py:63, and keep the ordinary-count negatives | File: src/ovcaq/drivers/codex_events.py:301 | Task: 7
[ALICE] 🟡 The `continue` at codex.py:383 drops every native update for a lane that has already finished. codex-cli 0.162.1 ships a `resume_agent` tool ("Resume a previously closed agent by id so it can receive send_input"; I confirmed the string in the binary). So a lane can legitimately go completed → close → resume → running → errored. With the `continue`, the resumed run's running and errored updates disappear with no trace, and a later interrupt or shutdown of the resumed run becomes raw unknown instead of `lane.failed`. The pre-change code reported these. The TUI already handles a restart, because the last write wins (src/ovcaq/tui/model.py:607). The PRD only requires that close statuses do not fail a completed lane, and the unfinished-only filter at src/ovcaq/drivers/codex.py:372 already does that on its own. Fix: delete lines 383-384. Then flip `test_finished_lane_late_update_retains_only_non_lane_observations` (tests/drivers/test_adapter_outcomes.py:266) so it expects running → `lane.progress` and errored → `lane.failed`, and reword docs/driver-protocol.md:243. Confidence: the tool is confirmed; the exact `agents_states` sequence after a resume is my guess | File: src/ovcaq/drivers/codex.py:383 | Task: 7
[ALICE] ⚪ The CHANGELOG PATH entry says the change checks "both native adapters' executables" and preserves "standard missing/empty host PATH lookup". In fact only the Claude probe changed (Codex already used the merged environment). With an empty host PATH, the Claude probe is unhealthy while the Codex probe searches the current directory, which docs/driver-protocol.md:37 now says correctly. Reword the entry to say the fix is for Claude and to name that split | File: CHANGELOG.md:43 | Task: 9
[ALICE] ⚪ `classify_failure` now collapses whitespace (`" ".join(detail.split())`), so "Rate\tlimit reached" becomes rate_limit. The pre-change code returned unknown for it. That widens matching beyond "retain existing word diagnostics", and neither the CHANGELOG nor the protocol doc mentions it. The test `test_native_word_diagnostics_retain_case_and_whitespace_variants` calls it "retain" even though the whitespace case is new behavior. Either document the widening and rename the test, or drop line 300 and the tab case | File: src/ovcaq/drivers/codex_events.py:300 | Task: 6
[ALICE] ⚪ `INVALID_OPTIONS` was moved up to module level so the now-deleted factory test could share it. It has a single user again (`test_constructor_rejects_unknown_or_invalid_options`). Inline it back into that test's `@pytest.mark.parametrize`, so the only change left in that test is the `raised.type is ValueError` line | File: tests/drivers/test_codex_launch.py:140 | Task: 8

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

## Blake

Provider: Anthropic; observed model: claude-opus-5-5; effort: xhigh; session: 8eb362f7-e3c7-4a3c-8b0c-4d823832259b.

[BLAKE] 🟡 Some numeric codes that do come with an HTTP context still classify as unknown. `HTTP/1.1 503 Service Unavailable`, `HTTP/1.1 429 Too Many Requests`, `HTTP error 429` and a bare `429 Too Many Requests` all return `unknown` (confirmed with a direct `classify_failure` probe). The status prefix accepts only `HTTP N`, `status N` and `error code N`, so it misses status lines and reason phrases. These failures get the generic died-retry/park handling instead of connectivity WAIT or rate-limit handling. The pinned `unexpected status N` and `last status: N` forms do work. | File: src/ovcaq/drivers/codex_events.py:301 | Task: P0-T1
[BLAKE] ⚪ A status prefix followed by an ordinary count still classifies. `status: 401 tests passed` returns `authentication` and `error code: 503 records` returns `connectivity` (confirmed by probe). The negative tests only cover counts with no status word in front. | File: src/ovcaq/drivers/codex_events.py:301 | Task: P0-T1
[BLAKE] ⚪ The health check and the real launch can resolve the executable from different directories. The Codex probe spawns without `cwd`, and the Claude probe runs `shutil.which` in the supervisor's working directory, but the launch spawns with `cwd=request.root`. With relative PATH entries, or an empty host PATH, the probe can disagree with the spawn, which goes against the Phase 1 exit criterion. docs/driver-protocol.md:37 documents the empty-PATH case but not relative overlay entries. | File: src/ovcaq/drivers/codex.py:47 | Task: P1-T2
[BLAKE] ⚪ The normal Codex sequence (`wait` reports completed, then `close_agent` reports shutdown) emits `raw.unknown` on every close of a completed lane. The tests pin this at tests/drivers/test_adapter_outcomes.py:89. The lane result is right, but routine flows now show recurring normalization gaps. | File: src/ovcaq/drivers/codex_events.py:233 | Task: P0-T1
[BLAKE] ⚪ No supervisor-level regression covers the Claude model-collision path. The Claude edge wrapper behaves correctly: I checked directly that `{default: o3, o3: o3-pro, x: o3}` launches `o3` and `o3-pro`. But tests/runtime/test_adapter_launch_routing.py runs only the Codex fake through the supervisor, so a regression in `_ResolvedModelClaudeDriver` would go unnoticed. | File: src/ovcaq/drivers/edge.py:23 | Task: P1-T1
[BLAKE] ⚪ Suspected, not confirmed: a Codex `turn.failed` reading "Authentication failed" classifies as `unknown` (pinned at tests/drivers/test_adapter_failure_classes.py:129). That means a retry or park instead of the operator-access halt. The Claude classifier treats "authentication" as authentication, so the two adapters disagree. I could not check whether this was already the behavior before this change. | File: src/ovcaq/drivers/codex_events.py:306 | Task: P0-T1
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

Provider: Anthropic; observed model: claude-opus-5-5; effort: xhigh; session: a3cfd04a-db7b-4e1b-95fa-8b9bdc56ff7d.

[BOB] ⚪ `assert retries.rate_limit == 0` can never fail. It checks the frozen `RetryState` the test built with `rate_limit=0`, and `decide` cannot change it (src/ovcaq/runtime/decision.py:84). Lines 200-201 already pin the non-rate-limit path | File: tests/drivers/test_adapter_failure_classes.py:225 | Task: 6
[BOB] ⚪ `INVALID_OPTIONS` was moved to a module constant so the factory test could share it. The rework deleted that test (R13), so the constant has one user left and no longer serves any change | File: tests/drivers/test_codex_launch.py:140 | Task: 8
[BOB] ⚪ CHANGELOG says "preserving standard missing ... host PATH lookup", but the Claude probe changed. With no host PATH it now falls back to `os.defpath` (`/bin:/usr/bin`, src/ovcaq/drivers/claude.py:82). The old `shutil.which(command)` used `CS_PATH` (`/usr/bin:/bin:/usr/sbin:/sbin` here, confirmed with `getconf PATH` and the stdlib source). The new value matches the subprocess spawn, as the design asks, so only the wording is wrong | File: CHANGELOG.md:43 | Task: 4
[BOB] ⚪ The test for an absent host PATH probes `sh`, which is in both `os.defpath` and `CS_PATH`. It cannot tell the design's spawn-matching `os.defpath` fallback from the old `CS_PATH` one, so going back to `shutil.which(command, path=None)` would still pass (found by reading, not run) | File: tests/runtime/test_adapter_health.py:250 | Task: 3
[BOB] ⚪ Suspected, not run: `HTTP/1.1 503`, `status=503` and `status_code: 429` still come out UNKNOWN under the status prefix regex. No checked-in fixture holds a numeric code, so nothing shows whether Codex emits these forms | File: src/ovcaq/drivers/codex_events.py:301 | Task: 6

Prior-cycle findings (all confirmed in code):
- R1: resolved. Bare `status` is accepted (src/ovcaq/drivers/codex_events.py:301), with Codex-spelling positives at tests/drivers/test_adapter_failure_classes.py:63.
- R2 and R9 and R12: resolved. The protocol doc now matches the code (docs/driver-protocol.md:37, docs/driver-protocol.md:243).
- R3: resolved. The test now runs from the executable's directory (tests/runtime/test_adapter_health.py:268).
- R4: resolved. RAW_UNKNOWN is asserted on `closed` (tests/drivers/test_adapter_outcomes.py:89). Removing the unfinished-only filter would now fail this test.
- R6: resolved. Late running/errored/completed updates on a finished lane are pinned (tests/drivers/test_adapter_outcomes.py:257). Removing the `continue` would now fail this test.
- R5: resolved. The PRD's Phase 0 acceptance command now includes test_adapter_failure_classes.py.
- R7: resolved. `_tier_request` is shared by both drivers (src/ovcaq/drivers/edge.py:16).
- R8: resolved. The receiver parametrization and the non-JSON test are gone.
- R11: resolved. The `authentication failed` pattern is removed, with a test guarding against its return.
- R13: resolved. The factory test is deleted and the constructor test checks the exact exception type.
- Test count fell from 7165 to 7141 (−24). That matches exactly the parametrizations removed and added, so no test was lost by accident.

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

FIX:
- Assert that can never fail — tests/drivers/test_adapter_failure_classes.py:225 — delete `assert retries.rate_limit == 0`; lines 200-201 already pin the non-rate path.
- Single-use `INVALID_OPTIONS` left after R13 — tests/drivers/test_codex_launch.py:140 — move the tuple back into `@pytest.mark.parametrize("options", ...)` on `test_constructor_rejects_unknown_or_invalid_options`.
- CHANGELOG wrongly says the missing-PATH lookup is preserved — CHANGELOG.md:43 — reword to "a missing host PATH now uses the subprocess default search path (`os.defpath`); an empty host PATH keeps each adapter's previous lookup".
- Absent-PATH test cannot tell the two fallbacks apart — tests/runtime/test_adapter_health.py:250 — create a fixture executable in tmp_path, `monkeypatch.setattr(os, "defpath", str(fixture_dir))`, delete PATH, and assert healthy. A `CS_PATH` fallback would not find the fixture.
VERIFY:
- Whether Codex emits numeric codes in forms the regex misses (`HTTP/1.1 503`, `status=`, `status_code`) — run `mise which codex`, then `rg -a -c -e "HTTP/1\.[01] \{" -e "status_code" -e "status=\{" <that binary path>`. Zero counts close this; any hit needs a literal positive in tests/drivers/test_adapter_failure_classes.py.
KNOWN:
- (none)

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

**Done.** All 13 prior-cycle findings are resolved, and the rework adds no regression. 5 new low (⚪) findings: 4 fix, 1 verify.
**Next:** You: send the four FIX items and the VERIFY item to the cycle-2 decision gate.

Verdict: 12 findings
Tests: 7141 passed, 0 failed, 0 skipped (suite run this cycle at 307b7921355885221e8f8e4f66ba2a678b9f43c5; approved retry)
