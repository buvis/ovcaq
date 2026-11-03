---
prd: dev/local/prds/wip/00006-events-claude-adapter-v1.md
review: 3
date: 2026-09-30
head_sha: ad892b3c2bb24086c1f6c973e5f7d0d9389dadd7
codex_thread_id: 01a0f0de-3f58-7c11-8e35-741cec8413c8
reviewers: alice,blake,bob,carl,eve
---

# PRD 00006 — review cycle 3

Diff range: `b5ee110cc0c78ef0f886c49d433721e6e3d8f325..ad892b3c2bb24086c1f6c973e5f7d0d9389dadd7`

codex_rung_guard: fired (15 codex-implemented task(s))

Incremental review of the cycle-2 rework (tasks 16-18). All five lenses ran: Alice (Claude subagent), Blake (blind, PRD-only), Bob (codex CLI, consensus + doubt/de-slop), Carl (copilot backend, model gemini-3.8-flash), Eve (Fable). pack: skipped (engram not installed on this host). Consolidation ran through `consolidate_findings.py` with the ledger filter. Eve's doubt output carries FIX/VERIFY/KNOWN buckets, not issue lines, so the orchestrator transcribed her three FIX items into `[EVE]` issue lines and assigned severities (fail loud: those severities are the orchestrator's, not Eve's). Eve's E1 timing claim was re-measured by the orchestrator at HEAD: `sanitize_text("a"*n)` took 0.22 s at 4 KB, 3.5 s at 16 KB, 14.3 s at 32 KB (confirmed quadratic). `git diff b5ee110 HEAD -- src/ovcaq/events/tail.py` confirms task 17 widened the preview input from `self._buffer[:512]` to the whole buffer.

All ten cycle-2 code findings (H1, H3, H4, H5, M1, M2, L1-L4) are resolved per Alice, Bob, Carl and Eve. V1 is closed: the cycle-2 queue's `uv run pytest` and `uv build` both exited 0 at ad892b3 (`checks-2.json`), so nothing carries forward.

## Consolidated findings

| ID | Consensus | Severity | Issue | File | Found by | Disposition |
|---|---|---|---|---|---|---|
| E1 | [1/5] | 🟠 high | `sanitize_text` is quadratic on long unbroken `[\w-]` runs (leading `[\w-]*` in both `_CREDENTIAL` prefix alternatives backtracks); task 17's sanitize-first fix widened the raw.unknown preview input from 512 bytes to the whole frame (up to 1 MiB), so one bad frame can stall decoding for hours | src/ovcaq/events/model.py:25 | EVE | open, confirmed by orchestrator measurement |
| M1 | [1/5] | 🟡 medium | `rejected → allowed → banner`: clearing `_limit_live` lets the banner emit a new `rate_limit.started`, though task 16 says "no rejected event decoded earlier in this session" | src/ovcaq/drivers/claude.py:191 | BOB | open |
| M2 | [1/5] | 🟡 medium | With `max_frame_bytes=512` the retained buffer can end mid-secret before redaction, so the preview exposes a prefix at the frame boundary | src/ovcaq/events/tail.py:123 | BOB | open |
| M3 | [1/5] | 🟡 medium | Dated weekly banners (`resets Sep 20 at 11am (Europe/Prague)`) do not match `RESET_BANNER`, so multi-day limits carry no reset | src/ovcaq/drivers/claude_events.py:150 | EVE | open |
| M4 | [1/5] | 🟡 medium | A rejected event with no credible reset still suppresses a credible banner reset (summary keeps null); narrows the literal task-16 wording | src/ovcaq/drivers/claude.py:189 | EVE | open (contract question) |
| M5 | [1/5] | 🟡 medium | Loud preflight for unattended permissions is only a constructor error plus a probe detail string | src/ovcaq/drivers/claude.py:74 | BLAKE | open |
| M6 | [1/5] | 🟡 medium | Extra `allow_explicit_model` option and `fallback_model` validation go beyond the PRD | src/ovcaq/drivers/claude.py:41 | BLAKE | discarded: accepted cycle-1 launch-option decision (explicit models opt-in only) and cycle-1 A3 fallback_model contract |
| M7 | [1/5] | 🟡 medium | Decoding lives in `drivers/claude_events.py`; test names differ from the PRD list; no stdin field, prompt passed in argv | src/ovcaq/drivers/claude_events.py | BLAKE | discarded: helper module stays inside the Claude driver edge; exact argv (prompt as argv) is the characterized launch contract |
| L1 | [1/5] | ⚪ low | Protocol doc does not describe `allowed_warning` as `activity.message` kind `rate_limit_warning` | docs/driver-protocol.md:55 | ALICE | open |
| L2 | [1/5] | ⚪ low | Empty 0-byte placeholder files for out-of-scope Codex/generic drivers sit in the tree | src/ovcaq/drivers/codex.py | BLAKE | open |
| L3 | [1/5] | ⚪ low | Fixture matrix bundles failure classes into one failures.jsonl instead of distinct files | tests/fixtures/claude/v1/failures.jsonl | BLAKE | open |
| L4 | [1/5] | ⚪ low | Fixed 1 MiB Bloom filter per driver can undercount on false positives | src/ovcaq/drivers/claude.py:72 | BLAKE | discarded: settled cycle-1 ledger entry (Bloom filter required by task-7 decision); the ledger filter missed the paraphrase |
| L5 | [1/5] | ⚪ low | Cannot statically verify the suite/lint/type/build at HEAD | N/A | BOB | resolved: last-verification.json at ad892b3 records all seven commands exit 0 |
| R1 | [1/5] | 🟡 medium | 5 touched tests pass against the pre-change code (neutrality directory guard) | tests/drivers/test_neutrality.py | mech-check | discarded: L2-requested guard pins existing directories by design |
| R2 | [1/5] | 🟡 medium | 7 touched tests pass against the pre-change code (model rework negative params, prose guards) | tests/events/test_model_rework.py | mech-check | discarded: negative-branch params and harmless-prose guards; x-api-key/apiKey and shape pins fail at base (Eve verified) |
| R3 | [1/5] | 🟡 medium | 6 touched tests pass against the pre-change code (direct AgentSettings validation) | tests/workflow/test_configuration_rework.py | mech-check | discarded: L1 asked for tests of existing validation, which pass at base by design |

Not queued for verification: Eve's VERIFY (run `uv run python -c "from zoneinfo import ZoneInfo; print(ZoneInfo('Europe/Prague'))"` on each intended Linux/container host, add `tzdata` if it raises) is host-specific and cannot be answered on this macOS host (not queued: command shape). No `checks-3.json` was written.

## Mechanical test checks

Shape check: no tautological test functions among 137 in 8 changed test files. Fail-first replay against b5ee110: 113 touched tests ran, 95 failed at base, 18 passed (rows R1-R3).

## Alice

[ALICE] ⚪ docs/driver-protocol.md:55 documents the rate_limit.started payload shape but never says that a provider "allowed_warning" now arrives as activity.message kind "rate_limit_warning" (with window, reset_at, detail) and no longer as rate_limit.cleared. This changes the observation vocabulary that consumers see. | File: docs/driver-protocol.md:55 | Task: 16

All cycle-2 findings resolved (H1, H3, H4, H5, M1, M2, L1-L4); V1 relies on the work phase's record.

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

[BLAKE] 🟡 Extra driver option `allow_explicit_model` and `fallback_model` validation go beyond the PRD | File: src/ovcaq/drivers/claude.py:41 | Task: general
[BLAKE] 🟡 "Loud preflight" for unattended permissions is only a constructor ValueError plus a probe() detail string; probe reports healthy | File: src/ovcaq/drivers/claude.py:74 | Task: general
[BLAKE] 🟡 Structure deviates from the PRD layout (`drivers/claude_events.py`, test names, no stdin field, prompt in argv) | File: src/ovcaq/drivers/claude_events.py | Task: general
[BLAKE] ⚪ Empty (0-byte) tracked placeholder files for out-of-scope work | File: src/ovcaq/drivers/codex.py | Task: general
[BLAKE] ⚪ Fixture matrix is thin (three bundled JSONL files) | File: tests/fixtures/claude/v1/failures.jsonl | Task: general
[BLAKE] ⚪ Fixed 1 MiB Bloom filter can undercount on false positives | File: src/ovcaq/drivers/claude.py:72 | Task: general

B1: fail
B2: pass
B3: pass
B4: pass
B5: pass
B6: fail
B7: fail
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: pass
B16: fail
B17: pass
B18: pass
B19: fail

## Bob

Codex ran fresh (no prior thread id). A gateguard fact-forcing hook blocked its first `cat` once; the rest of the run completed and the output is complete.

[BOB] 🟡 FIX: After `rejected → allowed → terminal banner`, clearing `_limit_live` permits a new `rate_limit.started`, despite task 16 requiring no earlier rejected event in the session; track that history separately and test this sequence. | File: src/ovcaq/drivers/claude.py:191 | Task: 16
[BOB] 🟡 FIX: With `max_frame_bytes=512`, the retained buffer can end partway through a Bearer or `sk-` secret before redaction; the 512-character normalized preview then exposes its prefix. Cover the configured frame boundary as well as the preview boundary. | File: src/ovcaq/events/tail.py:123 | Task: 17
[BOB] ⚪ Cannot statically verify: Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src/ovcaq`, and `uv build` at final HEAD to confirm the recorded verification. | File: N/A | Task: general

R1: fail
R2: pass
R3: pass
R4: fail
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

Backend copilot, model gemini-3.8-flash. Carl also ran the suite, lint, type check and build in his own shell (not recorded as this cycle's Tests line).

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

Full output: dev/local/tmp/eve-output-00006-c3.txt. FIX bucket transcribed as E1, M3, M4 above.

FIX:
- sanitize_text quadratic on long unbroken runs; L3 widened fallback preview to the whole frame — src/ovcaq/events/model.py:25 — drop the leading `[\w-]*` from both alternatives; add a 200 KB frame regression test
- Dated weekly banners dropped — src/ovcaq/drivers/claude_events.py:150 — optional `Mon DD at` date prefix resolved on the anchor's local year
- Rejected event without credible reset suppresses a credible banner reset — src/ovcaq/drivers/claude.py:189 — gate banner parsing on a known credible reset
VERIFY:
- tzdata absent on minimal Linux hosts makes zoned banners resolve to None — run the ZoneInfo('Europe/Prague') probe on each intended host; add `tzdata` if it raises
KNOWN:
- Wall-clock test can flake at 20:10:00 Prague — needs an injected clock (ABI change)
- 2099 DST expectations pin tzdata's extrapolated rule — speculative external change
- 18 fail-first passes — settled rule; pinning params fail at base

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 16 findings
Tests: 2933 passed, 0 failed, 0 skipped (reused from last-verification.json at ad892b3c2bb24086c1f6c973e5f7d0d9389dadd7)
