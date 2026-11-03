---
prd: dev/local/prds/wip/00006-events-claude-adapter-v1.md
review: 2
date: 2026-09-28
head_sha: b5ee110cc0c78ef0f886c49d433721e6e3d8f325
reviewers: alice,blake,bob
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/tmp/bob-output-00006-c2.txt.receipt.json
---

# PRD 00006 — review cycle 2

Diff range: `24fcec3bed6a41044c3d149d1f42bd678864e7e0..b5ee110cc0c78ef0f886c49d433721e6e3d8f325`

codex_rung_guard: fired (15 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude

Host substitution: Alice and Blake ran in isolated native Codex `gpt-5.6-sol` contexts (logical sonnet). Bob ran fresh through the authorized autocodex helper on external Claude Opus and supplied the independent doubt/de-slop voice. Native Fable was unavailable; no Eve result is claimed. Carl's optional Gemini launcher refused nested dispatch (exit 3) before a backend ran. The refusal was recorded and no stale Carl output was used. The engram pack was unavailable because this repository is not gita-registered.
Bob dispatch receipt and raw-log SHA-256 values were verified against the files. The helper's receipt reports cycle 1 because its host state path is stale; the cycle-2 prompt, output file and authoritative state identify this run as cycle 2.

## Consolidated findings

| ID | Consensus | Severity | Issue | File | Found by | Disposition |
|---|---|---|---|---|---|---|
| V1 | [2/3] | 🟡 medium | Final-HEAD full pytest remains unverified: queued `uv run pytest` exited 1; only the failing packaging test passed afterward | N/A | ALICE, BOB; verify-check | open verification |
| H1 | [1/3] | 🟠 high | `allowed_warning` emits `rate_limit.cleared` and can erase an earlier rejected limit | src/ovcaq/drivers/claude_events.py:125 | ALICE | open at cap |
| H2 | [1/3] | 🟠 high | Nonzero exit after `session.completed` leaves `success=True` | src/ovcaq/events/reducer.py:105 | BLAKE | discarded: accepted terminal matrix |
| H3 | [2/3] | 🟠 high | Normalized sanitizer misses `x-api-key` and `apiKey` secret shapes | src/ovcaq/events/model.py:22 | BLAKE, BOB | open at cap |
| H4 | [1/3] | 🟠 high | Terminal banner overwrites a prior rejected event's credible reset with null | src/ovcaq/drivers/claude.py:287 | BOB | open at cap |
| H5 | [1/3] | 🟠 high | Real `resets 8:10pm (Europe/Prague)` limit banners are not parsed | src/ovcaq/drivers/claude.py:278 | BOB | open at cap |
| M1 | [1/3] | 🟡 medium | Rate-limit window and warning reset survive only as prose or are dropped | src/ovcaq/drivers/claude_events.py:122 | BOB | open at cap |
| M2 | [1/3] | 🟡 medium | `agent_settings` duplicates validation and carries needless merge temporaries | src/ovcaq/config.py:190 | BOB | open at cap |
| L1 | [1/3] | ⚪ low | Direct `AgentSettings` name, command, and tier checks lack tests | src/ovcaq/config.py:95 | BOB | open at cap |
| L2 | [1/3] | ⚪ low | Neutrality scan includes nonexistent `src/ovcaq/cli` directory | tests/drivers/test_neutrality.py:13 | BOB | open at cap |
| L3 | [1/3] | ⚪ low | Raw fallback preview truncates before redaction, exposing a secret prefix at its boundary | src/ovcaq/events/tail.py:123 | BOB | open at cap |
| L4 | [1/3] | ⚪ low | Protocol documentation example calls undefined `new_run_id()` | docs/driver-protocol.md:34 | BOB | open at cap |
| L5 | [1/3] | ⚪ low | Credential-key substring matching rejects legitimate token-related control names | src/ovcaq/config.py:45 | BOB | discarded: accepted containing-key contract |
| R1 | [1/3] | 🟡 medium | 61 touched decoder tests pass against the pre-change code | tests/drivers/test_claude_decode.py | mech-check | discarded: split/moved behavior tests |
| R2 | [1/3] | 🟡 medium | 41 touched launch tests pass against the pre-change code | tests/drivers/test_claude_launch.py | mech-check | discarded: split/moved behavior tests |
| R3 | [1/3] | 🟡 medium | 7 touched driver-contract tests pass against the pre-change code | tests/drivers/test_contract.py | mech-check | discarded: existing protocol coverage |
| R4 | [1/3] | 🟡 medium | 5 touched model rework tests pass against the pre-change code | tests/events/test_model_rework.py | mech-check | discarded: benign prose and typed-usage preservation |
| R5 | [1/3] | 🟡 medium | 39 touched raw writer tests pass against the pre-change code | tests/runtime/test_raw_session.py | mech-check | discarded: writer rename preserves behavior |
| R6 | [1/3] | 🟡 medium | 5 touched configuration tests pass against the pre-change code | tests/workflow/test_configuration.py | mech-check | discarded: pre-existing behavior coverage |
| R7 | [1/3] | 🟡 medium | 9 touched configuration-rework tests pass against the pre-change code | tests/workflow/test_configuration_rework.py | mech-check | discarded: cases pin existing rejection behavior |

The installed consolidator parsed all three reviewer outputs. It left Blake's and Bob's `x-api-key` reports in separate rows; they describe the same sanitizer defect at the same file, so H3 combines them and takes the higher severity. The complete raw reviewer findings remain below. The cycle-1 queued `uv run pytest` exit 1 is V1, carried into this cycle under the verification-check rule; the other four queued checks exited 0.

## Decision gate

Cycle 2 has reached the interactive rework cap (2/2). H1, H3, H4 and H5 are unresolved HIGH findings, so convergence is blocked and the prescribed transition is a cap pause. No cycle-1 task is rerun. No new repair task is dispatched in this review session.

H2 is discarded because the accepted design's terminal conflict matrix explicitly says a completed terminal wins even when the process exit is nonzero; `tests/events/test_reducer.py::test_last_completion_supplies_serialized_usage` pins both exit codes. L5 is discarded because the accepted design explicitly rejects keys containing credential words; broadening it requires a contract decision. R1–R7 are retained above as computed replay observations, then discarded as regression findings: the cycle split or preserved many tests for existing behavior, while 133 of 300 touched tests failed against the prior code. The rework-specific redaction and contract cases that failed at base provide the change signal. These dispositions do not clear V1 or any open code finding.

V1 remains open even though the untracked placeholder and two related `.gitkeep` files were removed and the focused packaging test passed. The final-HEAD queued full suite still exited 1 (2,850 passed, 1 failed). The cycle-2 verification queue records `uv run pytest` and `uv build` as unrun checks. Bob's composite VERIFY request also named `git status --porcelain` and sdist inspection; these were not queued because they are not a single allowed project test/lint/build/type-check command. The work handoff's earlier full suite passed 2,851 tests, and the four other queued quality/build checks exited 0; neither fact converts the queued failure to a pass.

### Resumed decision gate (2026-09-29, cap 3)

Operator raised `rework_cap` to 3; cycle 2 < 3, so rework proceeds. No CRITICAL, so no rework design. Queued D2 tasks: 16 (H1, H4, H5, M1; opus), 17 (H3, L3; sonnet), 18 (M2, L1, L2, L4; sonnet). V1 routed to verification (`uv run pytest`, `uv build`). Discards unchanged and written to the ledger.

## Mechanical test checks

The shape check found no tautological test functions among 112 in 10 changed test files. The fail-first replay ran 300 touched tests against the cycle-1 head: 133 failed and 167 passed; it emitted R1–R7. The temporary replay worktree was removed after its approved sandbox retry.

## Alice

[ALICE] 🟠 `allowed_warning` emits `rate_limit.cleared`, so a warning arriving after a rejected event erases the live limit and can suppress the required rate-limit summary; preserve the warning without clearing prior rejection state | File: src/ovcaq/drivers/claude_events.py:125 | Task: 13
[ALICE] ⚪ Final-HEAD full pytest verification remains open: the queued run exited 1, and only the formerly failing packaging test was rerun afterward | File: N/A | Task: general
R1: fail
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

[BLAKE] 🟠 A nonzero process exit is ignored after `session.completed`, so a crashed session can produce `success=True` and incorrectly drive later workflow decisions | File: src/ovcaq/events/reducer.py:105 | Task: general
[BLAKE] 🟠 Normalized observations do not redact configured environment values, and the credential matcher misses common names such as `x-api-key`, allowing secrets into normalized evidence | File: src/ovcaq/events/model.py:22 | Task: general
B1: fail
B2: pass
B3: pass
B4: pass
B5: fail
B6: pass
B7: pass
B8: pass
B9: pass
B10: fail
B11: pass
B12: pass
B13: pass
B14: pass
B15: pass
B16: fail
B17: fail
B18: pass
B19: pass

## Bob

Prior-finding status (cycle 1 → HEAD): A1, A2, A3, A5, A6, A7, O3, O4, O5, O6, O7, O9, O10, O13, O14, O16 and O17 are resolved. O8 is documented, but the doc example calls a helper that doesn't exist (see below). B2 is only partly fixed: the new sanitizer still misses the hyphenated and camelCase API-key forms. O2 is only partly fixed: `allowed_warning` no longer starts a limit, but the five_hour/seven_day window survives only as prose. A4 is **not** resolved for the real banner shape, and its fix introduced a regression. Two things are confirmed by reading the code, not by running it. The legacy parser (`usage_limit.py` in the installed autopilot plugin, v0.5.6) matches the banner "resets 8:10pm (Europe/Prague)" and lets a rejected event's `resetsAt` win over the banner. The reducer (`src/ovcaq/events/reducer.py:60`) keeps the last `rate_limit.started` it sees.

```
[BOB] 🟠 Regression from the A4 fix: every terminal limit banner now emits rate_limit.started, with reset_at=None whenever the banner has no ISO time (always, for real banners). The reducer keeps the last live limit (reducer.py:60). So the real stream order "rejected rate_limit_event (resetsAt) → result banner" now ends with SessionSummary.rate_limit_reset_at=None. Before the rework, the summary kept the event's reset. The source rule is that resetsAt wins over the banner. No test covers event followed by banner | File: src/ovcaq/drivers/claude.py:287 | Task: 13
[BOB] 🟠 A4 is still open for real banners. Task 13 said to port the reset parser from the old source, which matches "resets 8:10pm (Europe/Prague)" (clock time + zone name, next occurrence after the error time). The port only accepts ISO-8601 times with an offset, which Claude does not print. Every test and fixture uses made-up ISO strings, so a real limit banner never yields a reset time | File: src/ovcaq/drivers/claude.py:278 | Task: 13
[BOB] 🟡 The five_hour vs seven_day window survives only as prose inside detail ("Rate limit allowed_warning: five_hour"), and the warning's resetsAt is dropped. Later policy (PRD 00007) would have to parse Claude words out of prose, which breaks the "state decides; prose does not" and provider-edge rules. Task 13 asked for this as normalized observation data | File: src/ovcaq/drivers/claude_events.py:122 | Task: 13
[BOB] 🟡 The normalized sanitizer uses the literal key word api_key. So "x-api-key: <value>" in tool or activity text, and JSON keys like x-api-key or apiKey, stay unredacted unless the value happens to start with sk-. config.py already uses api[_-]?key, so the two credential detectors disagree | File: src/ovcaq/events/model.py:22 | Task: 11
[BOB] 🟡 Simplification: agent_settings() repeats the tier/environment non-empty and credential loop that AgentSettings.__post_init__ now runs on the same values. The diff also adds unneeded user_agents/project_agents temporaries and turns the 2-line pattern select in _check_credentials into a 5-line if/else with no change in behavior | File: src/ovcaq/config.py:190 | Task: 11
[BOB] ⚪ The new name, command and tier checks in AgentSettings.__post_init__ have no direct-construction test. Only the environment/options credential cases are tested | File: src/ovcaq/config.py:95 | Task: 11
[BOB] ⚪ The neutrality guard lists src/ovcaq/cli, which does not exist (cli is the file cli.py). rglob quietly returns nothing, so the entry is dead, and a mistyped path in future would quietly scan nothing | File: tests/drivers/test_neutrality.py:13 | Task: 14
[BOB] ⚪ The fallback preview cuts raw bytes to 512 before sanitizing. A Bearer or sk- token that crosses the cut drops below the 20-character pattern floor, so its prefix stays in normalized evidence. The driver path sanitizes first and then truncates | File: src/ovcaq/events/tail.py:123 | Task: 13
[BOB] ⚪ The doc example calls new_run_id(), which does not exist in ovcaq, although the doc says it describes the implemented exports and Task 10 required checking examples against them | File: docs/driver-protocol.md:34 | Task: 15
[BOB] ⚪ Key matching by substring now rejects real non-secret Claude settings such as MAX_THINKING_TOKENS and CLAUDE_CODE_MAX_OUTPUT_TOKENS. The rework also flipped the earlier test that accepted TOKENIZER | File: src/ovcaq/config.py:45 | Task: 11
[BOB] ⚪ Cannot statically verify: the full suite passes at HEAD. The queued uv run pytest exited 1 at b5ee110 (a packaging failure); afterwards only the single packaging test was rerun | File: N/A | Task: general
```

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: fail
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

```
FIX:
- A banner's rate_limit.started overwrites a rejected event's reset in the reducer — src/ovcaq/drivers/claude.py:287 — Emit the banner's rate_limit.started only when the banner gives a credible reset and this session has decoded no rejected rate_limit_event (session.failed(rate_limit) already sets the class). Add a regression test: rejected event (resetsAt 4102444800), then a banner result; assert rate_limit_reset_at == 2100-01-01Z
- The old source's banner format was not ported — src/ovcaq/drivers/claude.py:278 — Move a compiled module-level RESET_TIME pattern into claude_events.py and require the "(Zone)" group. Resolve the zone with zoneinfo, anchor on the result record's timestamp, take the next occurrence after the anchor, and return None for unknown zones or past times. Drop the synthetic-dict record_timestamp reuse. Add a fixture line in the real "resets 8:10pm (Europe/Prague)" shape
- The window difference exists only as prose, and the warning reset is dropped — src/ovcaq/drivers/claude_events.py:122 — Add a structured neutral window field, plus the warning's credible reset_at, to the rate-limit payloads. Extend the rate-limit shape in events/model.py and keep the detail prose
- The sanitizer misses x-api-key and apiKey forms — src/ovcaq/events/model.py:22 — Change api_key to api[_-]?key in _SENSITIVE. Add tests for "x-api-key: synthetic-value" in text and for {"apiKey": ...}
- Validation duplicated in agent_settings, plus churn in _check_credentials — src/ovcaq/config.py:190 — Merge tiers/environment with {**user, **project} and let __post_init__ validate them (keep the list-type check on command). Drop the *_agents temporaries. Restore `pattern = _CREDENTIAL_KEY if key else _CREDENTIAL_VALUE`
- Direct AgentSettings validation is untested — src/ovcaq/config.py:95 — Add a parametrized direct-construction test that rejects an empty name, an empty command, a blank command part, and an empty tier key or value
- Dead cli entry in the neutrality scan list — tests/drivers/test_neutrality.py:13 — Remove the entry (the top-level glob already covers cli.py) and assert that every SCANNED_PATHS entry is a directory
- Preview cut happens before sanitizing — src/ovcaq/events/tail.py:123 — Sanitize the whole decoded retained buffer, then cut to 512
- Nonexistent helper in the doc example — docs/driver-protocol.md:34 — Use `lambda: ClaudeDriver(settings, run_id=run_id)`, with run_id supplied by the caller
VERIFY:
- The full suite and packaging are green at HEAD — run `git status --porcelain` (expect empty), then `uv run pytest` (expect exit 0), then `uv build` and confirm the sdist file list has no untracked placeholder
KNOWN:
- Credential-key substring matching rejects MAX_THINKING_TOKENS / CLAUDE_CODE_MAX_OUTPUT_TOKENS — The accepted design says keys "containing" the words are rejected, and the supervisor's later host-environment merge still delivers these settings. A carve-out would change the credential-key contract, so it is a design decision, not rework
```

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

Verdict: 20 findings
Tests: 2850 passed, 1 failed, 0 skipped (reused from last-verification.json at b5ee110cc0c78ef0f886c49d433721e6e3d8f325)
