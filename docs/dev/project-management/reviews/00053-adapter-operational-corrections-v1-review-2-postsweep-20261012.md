---
prd: docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
review: 2
date: 2026-10-12
head_sha: 4382d83eb48323204a920b555be04ea8deb1acc6
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  bob: 11af4a8f
---

# Fresh post-sweep review: PRD00053

Diff range: 7819970d7f807d6fad07b115af4f0df1fbc4a248..4382d83eb48323204a920b555be04ea8deb1acc6

autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/alice-output-00053-c2-postsweep-20261012.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/blake-output-00053-c2-postsweep-20261012.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00053-c2-postsweep-20261012.txt.receipt.json
provider_review_guard: satisfied
codex_rung_guard: not fired

The actual-model provider guard supersedes the legacy rung guard. No Eve ran. All three isolated reviewers served claude-opus-5-5 at xhigh. Carl remains disabled under the prior operator authorization. Full product range reviewed; raw management transcript diff is retained separately. Original cycle-2 review and receipts are unchanged.

## Review Summary

14/14 tasks completed; cycle and rework cap remain 2. All three external helpers exited 0; fresh receipts bind implementation fingerprint dc3a1730423571328f86544292cb0e93894ba9a48656555cf2efbf0411757b4b. Context pack failed because this repository is not registered with gita; sentinel retained. Mechanical shape check covered 77 functions in eight files, with no MECH findings. Fail-first replay was skipped because worktree creation was denied; preserved in context. Prior check queues are empty.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | 🟡 | The new HTTP-version prefix `http/\d+\.\d+` (src/ovcaq/drivers/codex_events.py:301) needs a minor version. So `HTTP/1.1 503` classifies, but HTTP/2 and HTTP/3 status lines do not, because they are written with no minor version. I ran `classify_failure`: "HTTP/2 503 Service Unavailable" and "HTTP/2 429" both return `unknown`, and the pre-change code returned connectivity and rate_limit. This also contradicts the CHANGELOG.md:43 claim that "HTTP-version status diagnostics" are recognized. If such a line reaches a Codex `turn.failed` (a guess, the same guess behind the HTTP/1.1 fix), a 503 skips the bounded connectivity WAIT and goes to died-retry then PARK, and a 429 retries instead of halting. Fix: make the minor version optional (`http(?:/\d+(?:\.\d+)?| status…)`) and add the "HTTP/2 503 Service Unavailable" and "HTTP/2 429 Too Many Requests" positives at tests/drivers/test_adapter_failure_classes.py:103. "HTTP Error 503: Service Unavailable" also returns `unknown`; that is lower likelihood, so decide whether it is in scope | src/ovcaq/drivers/codex_events.py:301 | 11 | ALICE, BLAKE |
| R2 | [1/3] | ⚪ | CHANGELOG.md:43 reads as a separate fix, but it only patches this PRD's own unreleased change at CHANGELOG.md:46. The reqwest and HTTP/1.1 forms always classified before this PRD (bare numbers matched), and "literal whitespace in word diagnostics" describes something that did not change. Fold the user-visible part into CHANGELOG.md:46 and drop line 43 | CHANGELOG.md:43 | 12 | ALICE |
| R3 | [1/3] | ⚪ | The new helper `_tier_request` is named with a noun phrase. The coding-style rule wants action-named functions to start with a verb. Rename it to, for example, `_map_model_to_tier` (both call sites are at src/ovcaq/drivers/edge.py:27 and src/ovcaq/drivers/edge.py:34) | src/ovcaq/drivers/edge.py:16 | 7 | ALICE |
| R4 | [1/3] | ⚪ | Every routine close of a completed lane (wait completed, then close_agent shutdown) now emits raw.unknown. The TUI then marks ordinary multi-agent sessions as having raw evidence. Late running or completed updates for terminal lanes emit nothing, so the two cases behave differently. This is documented and tested as intended, but it adds noise. | src/ovcaq/drivers/codex_events.py:233 | Phase 0 | BLAKE |
| R5 | [1/3] | ⚪ | Probe and launch can disagree on relative lookups. Both probes resolve relative PATH entries and relative command paths against the supervisor's own working directory, but launch runs with `cwd=request.root`. Absolute paths and normal PATH entries are unaffected. | src/ovcaq/drivers/claude.py:82 | Phase 1 | BLAKE |
| R6 | [1/3] | ⚪ | The Claude routing cases set every phase effort to "high" and give no reason. Config accepts low/medium/high/xhigh for any agent (src/ovcaq/config.py:364), and ClaudeDriver passes effort through unchanged, so Claude effort pass-through is only tested with one value | tests/runtime/test_adapter_launch_routing.py | 11 | BOB |
| R7 | [1/3] | ⚪ | The protocol doc says completed and failed lanes stay terminal "under all late receiver updates". But identity eviction removes terminal lanes first (src/ovcaq/drivers/codex.py:413). Once a lane is evicted, a late running update for it emits `lane.started` again | docs/driver-protocol.md | 4 | BOB |
| R8 | [1/3] | ⚪ | The CHANGELOG entry about reqwest/HTTP-version forms and literal whitespace describes no change from the pre-PRD base. Bare codes already matched those forms there, and whitespace was already literal. The entry records rework done inside this PRD and overlaps the numeric-context entry three lines below | CHANGELOG.md | 4 | BOB |
| R9 | [1/3] | ⚪ | `configured_driver` is annotated `-> CodexDriver` but returns `build_driver(...)`, which is typed `AgentDriver`. mypy only checks src/ovcaq, so nothing reports the mismatch | tests/drivers/test_codex_launch.py | 2 | BOB |

## Decision Gate

R1: confirmed HTTP/2 and HTTP/3 UNKNOWN; HTTP/1.1 503 remains connectivity. Native occurrence is speculative; keep medium severity. The broader status= and Error forms in Blake are recorded in his raw output and need a diagnostic-context scope decision.
R2/R8: same changelog duplication, one repair request; retain both original rows and provider evidence.
R3: bounded action-verb naming cleanup.
R4: discard as the already settled documented raw-evidence rule; terminal closes deliberately retain raw.unknown and tests pin it.
R5: settled out-of-scope cwd/relative-lookup limitation, now also attributed to Claude; preserve existing deferral and this new citation. No probe ownership redesign in this PRD.
R6: confirmed all Claude efforts are overwritten to high, leaving effort diversity untested. Bob VERIFY asks for deletion before testing: not queued, command shape includes edits. No edits executed.
R7: confirmed wording overclaims stability beyond remembered identity capacity; qualify documentation.
R9: confirmed AgentDriver factory result has narrower CodexDriver test annotation; bounded annotation cleanup.

Six distinct actionable findings remain (one medium, five low); no repair is authorized by the one-time post-sweep scope. Persist pause for operator decision, without creating tasks, raising cap, incrementing cycle or finalizing.

## Alice

Provider: anthropic; served model: claude-opus-5-5; effort: xhigh; session: 47cca245-95a2-4ec7-a55d-475ba8699fad.

[ALICE] 🟡 The new HTTP-version prefix `http/\d+\.\d+` (src/ovcaq/drivers/codex_events.py:301) needs a minor version. So `HTTP/1.1 503` classifies, but HTTP/2 and HTTP/3 status lines do not, because they are written with no minor version. I ran `classify_failure`: "HTTP/2 503 Service Unavailable" and "HTTP/2 429" both return `unknown`, and the pre-change code returned connectivity and rate_limit. This also contradicts the CHANGELOG.md:43 claim that "HTTP-version status diagnostics" are recognized. If such a line reaches a Codex `turn.failed` (a guess, the same guess behind the HTTP/1.1 fix), a 503 skips the bounded connectivity WAIT and goes to died-retry then PARK, and a 429 retries instead of halting. Fix: make the minor version optional (`http(?:/\d+(?:\.\d+)?| status…)`) and add the "HTTP/2 503 Service Unavailable" and "HTTP/2 429 Too Many Requests" positives at tests/drivers/test_adapter_failure_classes.py:103. "HTTP Error 503: Service Unavailable" also returns `unknown`; that is lower likelihood, so decide whether it is in scope | File: src/ovcaq/drivers/codex_events.py:301 | Task: 11
[ALICE] ⚪ CHANGELOG.md:43 reads as a separate fix, but it only patches this PRD's own unreleased change at CHANGELOG.md:46. The reqwest and HTTP/1.1 forms always classified before this PRD (bare numbers matched), and "literal whitespace in word diagnostics" describes something that did not change. Fold the user-visible part into CHANGELOG.md:46 and drop line 43 | File: CHANGELOG.md:43 | Task: 12
[ALICE] ⚪ The new helper `_tier_request` is named with a noun phrase. The coding-style rule wants action-named functions to start with a verb. Rename it to, for example, `_map_model_to_tier` (both call sites are at src/ovcaq/drivers/edge.py:27 and src/ovcaq/drivers/edge.py:34) | File: src/ovcaq/drivers/edge.py:16 | Task: 7

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

**Status:** Done.

**Changed:** Review only, no edits. I ran the PRD-scoped tests, Ruff and mypy at HEAD; I did not run the full suite. I ran the regex probes with `uv run python -c` against `classify_failure`.
```
416 passed, 2 warnings (tmp cleanup) | ruff: All checks passed! | mypy: Success: no issues found in 61 source files
```

**Next:** Task complete. Suggested next: send the HTTP/2 finding to the decision gate together with Blake's and Bob's outputs.

## Blake

Provider: anthropic; served model: claude-opus-5-5; effort: xhigh; session: 32165c1a-af5c-44fe-aef7-ad0b51204bf0.

Verified gate, all run in this session: the acceptance tests (273 passed), the full suite (7153 passed), `ruff check`, `ruff format --check` and `mypy` all clean. `uv build` succeeded into `/tmp/ovcaq-blake-build`. Source changes are limited to `claude.py`, `codex.py`, `codex_events.py` and `edge.py`. Driver API 2, observation protocol 1 and state schema 1 are unchanged.

[BLAKE] ⚪ Numeric classification no longer catches some explicit HTTP and status forms. `HTTP/2 429 Too Many Requests`, `HTTP/2 403 Forbidden`, `HTTP/2 502 Bad Gateway`, `status=429` and `Error 429: ...` all classify as unknown, and before this PRD they classified correctly. The version pattern only accepts a dotted version like `HTTP/1.1`. Native Codex 0.160 forms (`unexpected status N`, `last status: N`, `HTTP status client error (N`) are covered, so the practical impact is low. | File: src/ovcaq/drivers/codex_events.py:301 | Task: Phase 0
[BLAKE] ⚪ Every routine close of a completed lane (wait completed, then close_agent shutdown) now emits raw.unknown. The TUI then marks ordinary multi-agent sessions as having raw evidence. Late running or completed updates for terminal lanes emit nothing, so the two cases behave differently. This is documented and tested as intended, but it adds noise. | File: src/ovcaq/drivers/codex_events.py:233 | Task: Phase 0
[BLAKE] ⚪ Probe and launch can disagree on relative lookups. Both probes resolve relative PATH entries and relative command paths against the supervisor's own working directory, but launch runs with `cwd=request.root`. Absolute paths and normal PATH entries are unaffected. | File: src/ovcaq/drivers/claude.py:82 | Task: Phase 1

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

Provider: anthropic; served model: claude-opus-5-5; effort: xhigh; session: b5cef0a1-309b-46a1-bc91-e1c9237267cb.

[BOB] ⚪ The Claude routing cases set every phase effort to "high" and give no reason. Config accepts low/medium/high/xhigh for any agent (src/ovcaq/config.py:364), and ClaudeDriver passes effort through unchanged, so Claude effort pass-through is only tested with one value | File: tests/runtime/test_adapter_launch_routing.py | Task: 11
[BOB] ⚪ The protocol doc says completed and failed lanes stay terminal "under all late receiver updates". But identity eviction removes terminal lanes first (src/ovcaq/drivers/codex.py:413). Once a lane is evicted, a late running update for it emits `lane.started` again | File: docs/driver-protocol.md | Task: 4
[BOB] ⚪ The CHANGELOG entry about reqwest/HTTP-version forms and literal whitespace describes no change from the pre-PRD base. Bare codes already matched those forms there, and whitespace was already literal. The entry records rework done inside this PRD and overlaps the numeric-context entry three lines below | File: CHANGELOG.md | Task: 4
[BOB] ⚪ `configured_driver` is annotated `-> CodexDriver` but returns `build_driver(...)`, which is typed `AgentDriver`. mypy only checks src/ovcaq, so nothing reports the mismatch | File: tests/drivers/test_codex_launch.py | Task: 2

FIX:
- The doc claims terminal lanes stay terminal even after eviction — docs/driver-protocol.md:243 — change it to "Remembered completed and failed lanes remain terminal under late receiver updates"
- The changelog entry repeats another and describes no change from the base — CHANGELOG.md:43 — delete it, and add "including bare-status, reqwest and HTTP-version forms" to the numeric-context entry at CHANGELOG.md:46
- The return annotation is wrong — tests/drivers/test_codex_launch.py:32 — annotate `-> AgentDriver`, imported from `ovcaq.drivers.base`
VERIFY:
- The Claude effort override has no stated reason — delete tests/runtime/test_adapter_launch_routing.py:114-115, then run `uv run pytest -q tests/runtime/test_adapter_launch_routing.py -k claude`. If it passes, keep the lines deleted. If it fails, restore them with a one-line comment giving the reason
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

Verdict: 9 findings
Tests: 7153 passed, 0 failed, 0 skipped (Blake full suite this cycle; coordinator staged verification reused from last-verification.json at fd6d9a1)
