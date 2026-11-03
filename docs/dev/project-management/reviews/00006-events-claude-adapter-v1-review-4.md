---
prd: dev/local/prds/wip/00006-events-claude-adapter-v1.md
review: 4
date: 2026-09-30
head_sha: 82a12fef994d746c9bcd93acdaf478481f3fcf48
codex_thread_id: 01a0f0de-3f58-7c11-8e35-741cec8413c8
reviewers: alice,blake,bob,carl,eve
---

# PRD 00006 — review cycle 4

Diff range: `ad892b3c2bb24086c1f6c973e5f7d0d9389dadd7..82a12fef994d746c9bcd93acdaf478481f3fcf48`

codex_rung_guard: fired (15 codex-implemented task(s))

Incremental review of the cycle-3 rework (tasks 19-20). All five lenses ran: Alice (Claude subagent), Blake (blind, PRD-only, with Filesystem notes), Bob (codex CLI resuming thread 01a0f0de, consensus + doubt/de-slop), Carl (copilot backend, model gemini-3.8-flash), Eve (Fable). pack: failed (`engram pack` exit 1: "not inside a registered repo; register it in ~/.config/gita/repos.csv"; deterministic, not retried). Consolidation ran through `consolidate_findings.py` with the ledger filter. Eve's doubt output carries FIX/VERIFY/KNOWN buckets, not issue lines, so the orchestrator transcribed her five FIX items into `[EVE]` issue lines and assigned severities (fail loud: those severities are the orchestrator's, not Eve's).

All five cycle-3 findings (E1, M2, M3, M4, L1) are resolved per Alice, Carl and Eve. Eve measured `sanitize_text` at 8 ms on 200 KB of `a` and 50 ms on `"token"*40000`.

Orchestrator probe at HEAD (confirms Bob's B1): `sanitize_text("token" + "x"*65 + "=private-value")` returns the input unchanged, while the 10-char suffix form returns `tokenxxxxxxxxxx=[REDACTED]`. At ad892b3 the unbounded suffix redacted the long form, so this is a regression task 19 introduced with its `{0,64}` bound (documented at src/ovcaq/events/model.py:24-25; Eve files it KNOWN, Bob files it FIX 🟠). Also confirmed: `banner_reset("resets Feb 29 at 9am (UTC)", anchor 2095-01-10)` returns `2096-02-29T09:00:00Z` (Bob: contract violation; Eve: correct behavior, untested).

## Consolidated findings

| ID | Consensus | Severity | Issue | File | Found by |
|---|---|---|---|---|---|
| B1 | [1/5] | 🟠 high | The new 64-character suffix cap leaks previously redacted assignments such as `"token" + "x"*65 + "=private-value"`. Preserve long-key redaction with a linear scanner and add a regression test | src/ovcaq/events/model.py:28 | BOB (Eve: KNOWN, deliberate bound) |
| K1 | [1/5] | 🟠 high | Normalized events do not redact configured environment values; only key names and likely-secret patterns are redacted | src/ovcaq/events/model.py:22 | BLAKE |
| K2 | [1/5] | 🟠 high | ClaudeDriver is never registered as a built-in; no DriverPlugin or entry point | src/ovcaq/drivers/base.py:165 | BLAKE (re-raise of the settled cycle-1 entry; ledger matcher missed the paraphrase) |
| P1 | [2/5] | 🟡 medium | The last-`sk-` fallback in `_preview` can expose a secret prefix: `"x"*490 + "-sk-ABCDEsk-" + "Z"*600` at a 512-byte limit retains `ABCDE`; Eve: the marker is found in `text.lower()` but sliced in `text`, so U+0130 shifts the cut and leaks token chars | src/ovcaq/events/tail.py:150 | BOB, EVE |
| P2 | [2/5] | 🟡 medium | Contract deviation undocumented: a whitespace-free window keeps text up to the last `sk-` marker instead of becoming empty (Alice/Eve: record it; Bob: remove it) | src/ovcaq/events/tail.py:173 | ALICE, EVE |
| P3 | [1/5] | 🟡 medium | Invalid dates advance to the next year: `resets Feb 29 at 9am (UTC)` anchored 2095-01-10 returns 2096 instead of None | src/ovcaq/drivers/claude_events.py:205 | BOB |
| P4 | [1/5] | 🟡 medium | `rejected(credible R) -> rejected(no reset) -> banner B` is unpinned by a test and undocumented | src/ovcaq/drivers/claude.py:190 | EVE |
| P5 | [1/5] | 🟡 medium | Time-only branch builds the same `datetime(...)` twice; simplify | src/ovcaq/drivers/claude_events.py:206 | ALICE |
| P6 | [1/5] | 🟡 medium | Extra `allow_explicit_model`/`fallback_model` options, Bloom filter, banner and ISO reset parsing beyond spec | src/ovcaq/drivers/claude.py:39 | BLAKE (re-raise of settled entries) |
| P7 | [1/5] | 🟡 medium | Fixture matrix thin; `test_registry.py` has a single test | tests/fixtures/claude/v1/healthy.jsonl | BLAKE (re-raise of settled fixture entry) |
| L1 | [1/5] | ⚪ low | Failure classification is substring-based and can misclassify benign text | src/ovcaq/drivers/claude_events.py:223 | BLAKE |
| L2 | [1/5] | ⚪ low | CRLF frames shorter than the window leak the CR into the preview | src/ovcaq/events/tail.py:141 | EVE |
| L3 | [1/5] | ⚪ low | Feb 29 fall-through from a non-leap anchor year is untested | tests/drivers/test_claude_rate_limit.py:361 | EVE |
| L4 | [1/5] | ⚪ low | Cannot statically verify the suite/lint/type/build at 82a12fe | N/A | BOB (resolved: last-verification.json at 82a12fe records all five commands exit 0) |

### Auto-dismissed (ledger)

- [BLAKE] 🟡 Empty placeholder modules `drivers/codex.py` and `drivers/command.py` | File: src/ovcaq/drivers/codex.py — P00-T03 import-only package skeleton pinned by tests; PRD 00009 fills codex.py.
- [BLAKE] 🟡 Structure drift: decoding in `drivers/claude_events.py` | File: src/ovcaq/drivers/claude_events.py — The helper module stays inside the Claude driver edge; exact argv is the characterized launch contract.
- [BLAKE] ⚪ Loud preflight is only a health-detail string plus a constructor check | File: src/ovcaq/drivers/claude.py:81 — Recurs cycle-1 O16 (fixed); a configured mode is not a failure.

Not queued for verification: Eve's two VERIFY items. The fail-first replay check needs a base worktree with HEAD test files overlaid, which is not one command in the repo (not queued: command shape). The real weekly-banner capture names no runnable command (not queued: command shape). No `checks-4.json` was written. No `checks-3.json` existed, so nothing carries forward.

Step 7 (follow-up task creation) held: this is cycle 4 at rework_cap 4 with unresolved 🟠 rows, so the Phase 5 cap check decides before any task is created.

## Mechanical test checks

Shape check: no tautological test functions among 52 in 3 changed test files. Fail-first replay against ad892b3: skipped. The runner timed out after 600 s, because base's quadratic `sanitize_text` makes the new 200 KB timing tests run for hours there. No per-test result.

## Alice

[ALICE] 🟡 Simplification: the time-only branch builds the same `datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone)` twice (once, then again after the day bump). Build it with `local.replace(hour=hour, minute=minute, second=0, microsecond=0)` and add `timedelta(days=1)` when it is not after `local`. Behavior is unchanged, but check DST handling with the zone-aware replace before adopting it. | File: src/ovcaq/drivers/claude_events.py:206 | Task: 20
[ALICE] 🟡 Deviation from the task 19 contract, safe but undocumented: for an unbroken window the code keeps the text up to the last `sk-` marker. The contract says the window becomes empty. Record it in the design or task notes so the contract and code do not drift. | File: src/ovcaq/events/tail.py:173 | Task: 19

E1, M2, M3, M4, L1 resolved.

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

[BLAKE] 🟠 Normalized events must redact environment values; nothing matches configured `AgentSettings.environment` values | File: src/ovcaq/events/model.py:22 | Task: general
[BLAKE] 🟠 ClaudeDriver is never registered as a built-in | File: src/ovcaq/drivers/base.py:165 | Task: general
[BLAKE] 🟡 Empty placeholder modules `drivers/codex.py` and `drivers/command.py` | File: src/ovcaq/drivers/codex.py | Task: general
[BLAKE] 🟡 Structure drift: decoding in unlisted `drivers/claude_events.py` | File: src/ovcaq/drivers/claude_events.py | Task: general
[BLAKE] 🟡 Extra behavior beyond spec (explicit-model/fallback options, Bloom filter, banner and ISO reset parsing) | File: src/ovcaq/drivers/claude.py:39 | Task: general
[BLAKE] 🟡 Fixture matrix is thin | File: tests/fixtures/claude/v1/healthy.jsonl | Task: general
[BLAKE] ⚪ Failure classification is substring-based | File: src/ovcaq/drivers/claude_events.py:223 | Task: general
[BLAKE] ⚪ Loud preflight is only a health-detail string plus a constructor check | File: src/ovcaq/drivers/claude.py:81 | Task: general

B1: fail
B2: pass
B3: fail
B4: pass
B5: pass
B6: fail
B7: fail
B8: pass
B9: pass
B10: fail
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: fail
B17: fail
B18: fail
B19: fail

## Bob

Codex resumed thread 01a0f0de; exit 0, single run.

[BOB] 🟠 FIX: The new 64-character suffix cap leaks previously redacted assignments such as `"token" + "x"*65 + "=private-value"`. Preserve long-key redaction with a linear scanner and add a regression test. | File: src/ovcaq/events/model.py:28 | Task: 19
[BOB] 🟡 FIX: The last-`sk-` fallback violates the required empty preview for truncated windows without whitespace and can expose a secret prefix: with a 512-byte frame limit, `"x"*490 + "-sk-ABCDEsk-" + "Z"*600` retains `ABCDE`. Remove this exception and replace the test's `startswith("x")` expectation with an empty-preview assertion. | File: src/ovcaq/events/tail.py:150 | Task: 19
[BOB] 🟡 FIX: Invalid dates silently advance to the next year: `resets Feb 29 at 9am (UTC)` anchored on 2095-01-10 returns a 2096 reset instead of rejecting the invalid 2095 date. Select the year before date validation and test this case. | File: src/ovcaq/drivers/claude_events.py:205 | Task: 20
[BOB] ⚪ Cannot statically verify: reported runtime results at 82a12fe for `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src/ovcaq`, and `uv build`; the supplied work-phase record reports success. | File: N/A | Task: general

R1: fail
R2: fail
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
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

## Carl

Backend copilot, model gemini-3.8-flash. Carl also ran the suite, lint and type check in his own shell (2990 tests pass; not recorded as this cycle's Tests line).

[CARL] ✅ No issues found

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

## Eve

Full output: dev/local/tmp/eve-output-00006-c4.txt. FIX bucket transcribed as P1 (merged with Bob), P2, P4, L2, L3 above.

FIX:
- `_preview` finds the `sk-` marker in `text.lower()` but slices `text`; U+0130 shifts the cut and leaks token chars — src/ovcaq/events/tail.py:150
- CRLF frames shorter than the window leak the CR into the preview — src/ovcaq/events/tail.py:141
- Unrecorded contract deviation (whitespace-free window keeps text up to the last `sk-`) — amend the contract wording, no code change
- `rejected(credible R) -> rejected(no reset) -> banner B` unpinned — src/ovcaq/drivers/claude.py:190 — add a test, extend docs/driver-protocol.md:62-63
- Feb 29 fall-through untested — tests/drivers/test_claude_rate_limit.py:361
VERIFY:
- Fail-first evidence missing for the new tests (replay timed out at base) — base-worktree pytest run with the three HEAD test files overlaid, `-k "not stays_linear and not bounded_time"`
- Dated-banner grammar not from a captured session — capture a real weekly-limit result record and add it to failures.jsonl
KNOWN:
- Key names with more than 64 `[\w-]` chars after the sensitive word are no longer redacted — deliberate bound for linear scanning
- A multi-word quoted secret straddling the cut leaks its middle words
- The two 1.0 s wall-clock assertions can flake under CI load (20x margin)
- Pat's duplicate `datetime(...)` construction — pre-existing shape
- Pat's `_MONTHS` literal — correct (`calendar.month_abbr` is locale-dependent)

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 14 findings
Tests: 2990 passed, 0 failed, 0 skipped (reused from last-verification.json at 82a12fef994d746c9bcd93acdaf478481f3fcf48)
