---
prd: docs/dev/project-management/prds/wip/00006-events-claude-adapter-v1.md
review: 5
date: 2026-10-02
head_sha: 0228eb00f39a3152a008351212fee3b01603a646
reviewers: alice,blake,bob
---

# PRD 00006 — review cycle 5

Diff range: `82a12fef994d746c9bcd93acdaf478481f3fcf48..0228eb00f39a3152a008351212fee3b01603a646`

codex_rung_guard: fired (15 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00006-c5-20261002.txt.receipt.json

Full PRD work range: `666776af6ecb3baebb70e3eeb1c1b828fe64d135..0228eb00f39a3152a008351212fee3b01603a646`.

The incremental consensus/doubt review checks cycle-4 rework and prior findings; Blake independently reviewed the full PRD and its mandatory source contracts. All 23 tasks were completed before dispatch. Source-plan SHA-256 matches the accepted manifest: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.

Alice and Blake ran as isolated native Codex subagents on `gpt-5.6-sol` (logical sonnet), with no parent conversation. Bob ran fresh through the autocodex reviewer helper on Claude Opus; raw events identify `claude-opus-5-5` (logical opus). This is the user's explicit Claude Bob host substitution, not a claim of native model diversity. No Codex review thread was resumed.

Eve/Fable is unavailable in this host's native model roster; no Eve dispatch or Fable capability is claimed. The independent-provider doubt requirement is covered by Claude Bob's full D1-D5 and de-slop review. Carl's installed Gemini helper exited 3, `refusing nested dispatch (already inside a CLI agent)`; no backend ran, no nesting guard was bypassed, and this refusal is not latched as permanent batch unavailability. All native agents and external processes were awaited in this session.

pack: failed (engram exit 1: repository is not registered in `/Users/bob/.config/gita/repos.csv`; deterministic, no retry).

## Consolidated findings

Consolidation used `consolidate_findings.py` with the Blake ledger filter, then absorbed both mechanical replay rows. The coordinator reinstated C5-13: the automatic match's rationale applies to configured overlays, while Blake's concrete nested-object counterexample bypasses that boundary. Raw reviewer verdicts below remain unchanged by decision-gate dispositions.

| ID | Consensus | Severity | Issue | File | Found by | Disposition |
|---|---|---|---|---|---|---|
| C5-01 | [2/3] | 🟡 medium | `_preview` still preserves a whitespace-free truncated window unless it contains `sk-`, contrary to Task 22’s unconditional empty-preview contract; replace the conditional with `end = 0` and update the older test that expects an `x` preview. | src/ovcaq/events/tail.py:148 | ALICE, BOB | cap-overflow |
| C5-02 | [1/3] | 🟠 high | The reducer binds identity only on start or terminal events, allowing earlier observations from another session to contaminate a successful summary and its usage | src/ovcaq/events/reducer.py:42 | BLAKE | cap-overflow |
| C5-03 | [1/3] | 🟠 high | Failure classification misses standard authentication, rate-limit, and connectivity forms such as expired OAuth tokens, HTTP 429, and ECONNRESET, classifying them as generic agent failures | src/ovcaq/drivers/claude_events.py:223 | BLAKE | cap-overflow |
| C5-04 | [1/3] | 🟡 medium | The provider-neutral events layer imports both the downstream driver layer and runtime persistence, reversing the mandated `events <- drivers <- runtime` dependency direction | src/ovcaq/events/tail.py:8 | BLAKE | cap-overflow |
| C5-05 | [1/3] | 🟡 medium | The required normalized-event tailing interface is absent; `events/tail.py` only provides writing and raw-stream decoding | src/ovcaq/events/tail.py:21 | BLAKE | discarded |
| C5-06 | [1/3] | 🟡 medium | Claude process conformance exercises only normal completion and does not verify the specified live TERM/KILL response | tests/drivers/test_claude_process.py:119 | BLAKE | cap-overflow |
| C5-07 | [1/3] | 🟡 medium | Authorization values that use a scheme other than Bearer still leak. sanitize_text("Authorization: Basic dXNlcjpwYXNzd29yZA==") gives "Authorization: [REDACTED] dXNlcjpwYXNzd29yZA==": only the scheme word is redacted. The same happens with `token ghp_…` and `Digest …`. This gap already existed at 82a12fe, but the diff rewrote this exact clause as `(?:bearer\s+)?`. No test covers it | src/ovcaq/events/model.py:29 | BOB | cap-overflow |
| C5-08 | [1/3] | 🟡 medium | Once `continue` became `return None`, the `for … else: return None` branch can no longer run: the year+1 pass either raises or builds a time later than `local`. The loop can become one constructor plus `replace(year=local.year + 1)`, which raises ValueError for Feb 29 and gives the same results | src/ovcaq/drivers/claude_events.py:200 | BOB | cap-overflow |
| C5-09 | [1/3] | ⚪ low | JSON keys with escaped quotes inside raw previews are not redacted. In `{\"apiKey\": \"v\"}` the key is followed by a backslash, so `["']?\s*[:=]` fails and `v` survives in raw.unknown previews (claude.py:151, tail.py:152). This already existed at 82a12fe. It matters most when stream records change shape and many records fall back to raw.unknown | src/ovcaq/events/model.py:29 | BOB | cap-overflow |
| C5-10 | [1/3] | ⚪ low | The protocol doc describes the preview wrongly. It says "512-byte window", but the window is _PREVIEW_WINDOW_BYTES = 4096 (or the frame-buffer cap if smaller). It says a trailing CR "never" reaches the preview, but finish() on an unterminated `…\r` frame keeps it (trim_cr needs `terminated`) | docs/driver-protocol.md:77 | BOB | cap-overflow |
| C5-11 | [1/3] | ⚪ low | Two asserts are redundant: each `not any(...)` / `"ABCDE" not in preview` check follows `assert preview == ""` and can never add anything | tests/events/test_tail.py:668 | BOB | cap-overflow |
| C5-12 | [1/3] | ⚪ low | Cannot statically verify: full `uv run pytest` at 0228eb0 (the context says "currently running"; tasks 22 and 23 record no suite output, including the DST time-only banner tests) | N/A | BOB | discarded |
| C5-13 | [1/3] | 🟠 high | Normalized sanitization preserves arbitrary values nested under `environment`, so credentials with non-sensitive variable names can leak into normalized logs | src/ovcaq/events/model.py:95 | BLAKE | cap-overflow |
| C5-14 | [1/3] | 🟡 medium | 29 touched test(s) pass against the pre-change code: test_banner_reset_never_skips_invalid_year_to_later_leap_day, test_banner_applies_after_credible_then_resetless_rejection, test_banner_reset_resolves_dated_banner_in_anchor_local_year +23 more | tests/drivers/test_claude_rate_limit.py | mech-check | discarded |
| C5-15 | [1/3] | 🟡 medium | 1 touched test(s) pass against the pre-change code: test_text_sanitization_redacts_assignment_with_long_sensitive_key | tests/events/test_model_rework.py | mech-check | discarded |

### Automatic ledger matches

The script emitted the following section. Its first dismissal is explicitly overturned by C5-13; the other two remain settled.


- [BLAKE] 🟠 Normalized sanitization preserves arbitrary values nested under `environment`, so credentials with non-sensitive variable names can leak into normalized logs | File: src/ovcaq/events/model.py:95 — Configuration rejects credential-shaped environment keys and values (cycle-1 A1 fix, src/ovcaq/config.py), so the configured overlay holds only non-secret control flags such as CLAUDE_UNATTENDED=1. The accepted design reads the PRD's 'redact environment values' as key-based redaction plus narrow likely-secret patterns; value-matching '1' or 'auto' in free text would corrupt ordinary prose.
- [BLAKE] 🟡 The undocumented `allow_explicit_model` option bypasses the required agent-tier model resolution contract | File: src/ovcaq/drivers/claude.py:41 — Accepted cycle-1 launch-option decision: models resolve through tiers and explicit models are opt-in only; fallback_model is the cycle-1 A3 design contract.
- [BLAKE] 🟡 The required full failure-session fixture matrix is represented by unrelated one-line terminal records, so stateful rate-limit, connectivity, permission, and terminal-failure sessions are not covered | File: tests/fixtures/claude/v1/failures.jsonl:1 — PRD layout is fixtures/claude/*.jsonl; the matrix requirement is class coverage, which failures.jsonl provides one class per line. Splitting files is churn.


## Decision gate

Cycle 5 reached `rework_cap: 5`. Three HIGH findings remain unresolved: C5-02, C5-03 and C5-13. No CRITICAL finding was reported. The loop-mode cap branch defers all eleven unresolved findings (3 high, 5 medium, 3 low) to batch-end review, creates no repair tasks, and hands off to the finalize phase as converged-with-deferrals. This is a cap-limited exit, not a clean review.

The synthetic probes reproduce:
- usage from `old-session` survives a later `new-session` completion, yielding successful new-session usage of 999 input tokens;
- `OAuth token expired`, `HTTP 429 Too Many Requests`, and `ECONNRESET` each classify as `agent`;
- `sanitize_json({"environment":{"CONFIG_VALUE":"synthetic-private-value"}})` retains the nested value;
- Basic/token authorization values and escaped JSON credential keys survive normalization.

The nested-environment finding is not resolved by the earlier configured-overlay decision: Observation/sanitize_json accepts arbitrary structured payloads independently of AgentSettings. It is reinstated and deferred, not silently dismissed. The failure-classification finding concerns missed error forms; the older settled low finding concerns false-positive substring matches, so it does not settle this gap.

No actual secret was used or observed in these probes. Evidence files remain user-private; these are unresolved redaction defects, without evidence of an active disclosure.

### Discards and resolved checks

- **C5-05:** No Phase 4 source task or specified callable requires a normalized-file reader here. P06-T01 of the accepted source plan owns log tailing; the accepted design explicitly assigns normalized tailing to PRD 00008. This phase provides record conversion, the writer and raw-first decoder.
- **C5-12:** Resolved by the current review session: uv run pytest -q at 0228eb00f39a3152a008351212fee3b01603a646 exited 0 with 3003 passed, 0 failed, 0 skipped. Bob had read the context before the foreground suite completed.
- **C5-14:** Behavior-preserving date construction and explicit coverage backfill intentionally pass on the base. Task 23 explicitly required pinning rejected(R)->rejected(no reset)->banner without changing behavior. Existing date parameters plus the leap-day-already-passed negative case also pass on base; the non-leap-anchor case fails. Replay found 10 changed cases failing, not a tautological assertion.
- **C5-15:** The suffix=10 parameter is a pre-existing behavior guard; suffix=65 and suffix=1000 fail against the base. The computed replay groups parameter cases under one function name. Passing the short-key control is intentional.

All dispositions are recorded in state and the settled-decisions ledger. C5-01 recurs because the work pass preserved an older test's expectation despite Task 22's exact contract; reaching the cap prevents another repair attempt here. The failure count is not used to justify skipping any lens.

## Mechanical checks and quality gates

State/schema validation and task counts passed (23/23). The required replay first encountered the filesystem sandbox's Git-worktree restriction, then succeeded under approved execution. It removed its temporary worktree; the repository has only the main worktree.

## Tautological test shapes (computed, do not re-judge)

Each `[MECH]` line is a test whose shape cannot fail as written. Raise
it; step 6 adds any line the table lacks. `mech-check` is the finder.


Checked 59 test function(s) in 3 test file(s).


## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `82a12fef994d`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

[MECH] 🟡 29 touched test(s) pass against the pre-change code: test_banner_reset_never_skips_invalid_year_to_later_leap_day, test_banner_applies_after_credible_then_resetless_rejection, test_banner_reset_resolves_dated_banner_in_anchor_local_year +23 more | File: tests/drivers/test_claude_rate_limit.py | Task: general
[MECH] 🟡 1 touched test(s) pass against the pre-change code: test_text_sanitization_redacts_assignment_with_long_sensitive_key | File: tests/events/test_model_rework.py | Task: general

Replay: 40 touched test(s) ran, 10 failed against base, 30 passed; 0 test file(s) could not be collected at base (their tests fail there). Command: uv run python -m pytest


The previous cycle had no verification queue. Bob's VERIFY request for the full suite was satisfied by this session's already-required foreground run (`uv run pytest -q`); the queue records the equivalent command and its exit 0 rather than rerunning it. The suite finished after Bob had read his context.

- `uv run pytest -q`: 3003 passed, 0 failed, 0 skipped; two pytest temporary-directory cleanup warnings.
- `uv run mypy src/ovcaq`: passed, 55 source files.
- `uv build`: sdist and wheel built.
- `uv run ruff check src tests`: passed.
- `uv run ruff format --check src tests`: passed, 149 files.
- `uv run ruff check .`: failed, 41 findings in existing untracked project-management probes.
- `uv run ruff format --check .`: failed, 41 existing project-management artifacts. These repository-wide hygiene failures remain the explicit cycle-4 deferral; they are not reported as green.

Structured evidence: [verification](00006-events-claude-adapter-v1-verification-5.json), [probes](00006-events-claude-adapter-v1-probes-5.json), [findings/dispositions](00006-events-claude-adapter-v1-findings-5.json), [verification queue](00006-events-claude-adapter-v1-checks-5.json). Complete reviewer text and immutable Claude evidence are retained alongside this review in `00006-cycle-5-evidence/`, with the original helper paths preserved for receipt validation.

## Alice

Provider/model: Codex `gpt-5.6-sol`; isolated native consensus review, logical sonnet. Raw result follows.

[ALICE] 🟡 `_preview` still preserves a whitespace-free truncated window unless it contains `sk-`, contrary to Task 22’s unconditional empty-preview contract; replace the conditional with `end = 0` and update the older test that expects an `x` preview. | File: src/ovcaq/events/tail.py:148 | Task: 22
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

Provider/model: Codex `gpt-5.6-sol`; isolated native PRD-only blind review, logical sonnet. Raw result follows.

[BLAKE] 🟠 Normalized sanitization preserves arbitrary values nested under `environment`, so credentials with non-sensitive variable names can leak into normalized logs | File: src/ovcaq/events/model.py:95 | Task: general
[BLAKE] 🟠 The reducer binds identity only on start or terminal events, allowing earlier observations from another session to contaminate a successful summary and its usage | File: src/ovcaq/events/reducer.py:42 | Task: general
[BLAKE] 🟠 Failure classification misses standard authentication, rate-limit, and connectivity forms such as expired OAuth tokens, HTTP 429, and ECONNRESET, classifying them as generic agent failures | File: src/ovcaq/drivers/claude_events.py:223 | Task: general
[BLAKE] 🟡 The undocumented `allow_explicit_model` option bypasses the required agent-tier model resolution contract | File: src/ovcaq/drivers/claude.py:41 | Task: general
[BLAKE] 🟡 The provider-neutral events layer imports both the downstream driver layer and runtime persistence, reversing the mandated `events <- drivers <- runtime` dependency direction | File: src/ovcaq/events/tail.py:8 | Task: general
[BLAKE] 🟡 The required normalized-event tailing interface is absent; `events/tail.py` only provides writing and raw-stream decoding | File: src/ovcaq/events/tail.py:21 | Task: general
[BLAKE] 🟡 The required full failure-session fixture matrix is represented by unrelated one-line terminal records, so stateful rate-limit, connectivity, permission, and terminal-failure sessions are not covered | File: tests/fixtures/claude/v1/failures.jsonl:1 | Task: general
[BLAKE] 🟡 Claude process conformance exercises only normal completion and does not verify the specified live TERM/KILL response | File: tests/drivers/test_claude_process.py:119 | Task: general
B1: fail
B2: fail
B3: fail
B4: pass
B5: fail
B6: fail
B7: fail
B8: pass
B9: fail
B10: fail
B11: fail
B12: pass
B13: pass
B14: pass
B15: fail
B16: fail
B17: fail
B18: pass
B19: pass


## Bob

Provider/model: Claude `claude-opus-5-5`; fresh external helper, logical opus, exit 0. User-authorized host substitution; no retry and no stale Codex thread. Raw result follows.

**Prior findings, checked against HEAD 0228eb0**

- **B1** (long-key leak): fixed. `model.py:27-31` now starts a key only at the start of a run of word characters or hyphens, so there is no length cap and each run is scanned a fixed number of times. Against 82a12fe the 65- and 1000-character cases leave `private-value` unredacted.
- **P1**: fixed. Any `sk-` in a cut-off window with no whitespace now gives an empty preview (`tail.py:150`). Against 82a12fe, the ABCDE case leaves `-sk-ABCDE` in the preview. The U+0130 case leaves `sk-QQQQQQQ` there.
- **P2**: the deviation is now written up in `docs/driver-protocol.md:77-80` and the CHANGELOG. The code still differs from the task-22 contract (see finding 4).
- **P3**: fixed (`claude_events.py:206`). Against 82a12fe the `[non_leap_anchor_year]` case returns `2096-02-29T09:00:00Z`, so that test fails there.
- **P4**: pinned by the test at `test_claude_rate_limit.py:261` and documented at docs :64-65. It matches `claude.py:190` plus the reducer, where the last `rate_limit.started` wins.
- **P5**: fixed, and the behavior is the same. `local.replace(..., fold=0)` plus a one-day timedelta does the same wall-clock math as the two old `datetime(...)` calls.
- **L2**: fixed (`tail.py:141`). Against 82a12fe both test cases keep the trailing `\r`.
- **L3**: pinned.
- **K1, K2, P6, P7, L1**: already settled. Not raised again.
- **Fail-first [MECH] lines**: the test cases that pass at 82a12fe are ones that pin existing behavior, by design. Task 23 item 3 asks for the pinning, and that covers `leap_day_already_passed`, Feb 28 and suffix=10. The cases that carry the fix fail at 82a12fe when I trace the old code. This matches the settled "pinning guards" decision, so I did not raise them.

**Issues**

```
[BOB] 🟡 Authorization values that use a scheme other than Bearer still leak. sanitize_text("Authorization: Basic dXNlcjpwYXNzd29yZA==") gives "Authorization: [REDACTED] dXNlcjpwYXNzd29yZA==": only the scheme word is redacted. The same happens with `token ghp_…` and `Digest …`. This gap already existed at 82a12fe, but the diff rewrote this exact clause as `(?:bearer\s+)?`. No test covers it | File: src/ovcaq/events/model.py:29 | Task: 21
[BOB] 🟡 Once `continue` became `return None`, the `for … else: return None` branch can no longer run: the year+1 pass either raises or builds a time later than `local`. The loop can become one constructor plus `replace(year=local.year + 1)`, which raises ValueError for Feb 29 and gives the same results | File: src/ovcaq/drivers/claude_events.py:200 | Task: 23
[BOB] ⚪ JSON keys with escaped quotes inside raw previews are not redacted. In `{\"apiKey\": \"v\"}` the key is followed by a backslash, so `["']?\s*[:=]` fails and `v` survives in raw.unknown previews (claude.py:151, tail.py:152). This already existed at 82a12fe. It matters most when stream records change shape and many records fall back to raw.unknown | File: src/ovcaq/events/model.py:29 | Task: 21
[BOB] ⚪ Task-22 contract item 1 says every cut-off window with no whitespace previews as empty. The code empties it only when it contains the literal `sk-`. That ties tail.py to the patterns in _LIKELY_SECRET: if a new bare-secret pattern is added there, the cut-off leak quietly comes back. The conflicting test is test_tail.py:547 (it expects "x" in the preview) | File: src/ovcaq/events/tail.py:150 | Task: 22
[BOB] ⚪ The protocol doc describes the preview wrongly. It says "512-byte window", but the window is _PREVIEW_WINDOW_BYTES = 4096 (or the frame-buffer cap if smaller). It says a trailing CR "never" reaches the preview, but finish() on an unterminated `…\r` frame keeps it (trim_cr needs `terminated`) | File: docs/driver-protocol.md:77 | Task: 22
[BOB] ⚪ Two asserts are redundant: each `not any(...)` / `"ABCDE" not in preview` check follows `assert preview == ""` and can never add anything | File: tests/events/test_tail.py:668 | Task: 22
[BOB] ⚪ Cannot statically verify: full `uv run pytest` at 0228eb0 (the context says "currently running"; tasks 22 and 23 record no suite output, including the DST time-only banner tests) | File: N/A | Task: general
```

FIX:
- Non-Bearer Authorization schemes leak their credentials. `src/ovcaq/events/model.py:29`. Change `(?:bearer\s+)?` to `(?:(?:bearer|basic|digest|token)\s+)?`. Add a test that `Authorization: Basic <b64>` and `Authorization: token <v>` leave no trace of the value.
- `for…else` can no longer run. `src/ovcaq/drivers/claude_events.py:200-210`. Replace it with `try: wall = datetime(local.year, month, int(match[2]), hour, minute, tzinfo=zone); if wall <= local: wall = wall.replace(year=local.year + 1)` and `except ValueError: return None`.
- Keys with escaped quotes are not redacted. `src/ovcaq/events/model.py:29`. Change `[\"']?` to `(?:\\?[\"'])?`. Add a test that `{\"apiKey\": \"v\"}` leaves no `v`.
- The preview depends on the literal `sk-` and departs from the task-22 contract. `src/ovcaq/events/tail.py:150`. Set `end = 0` for every cut-off window with no whitespace. Update the conflicting `"x"` expectation at `tests/events/test_tail.py:547` and note there that it contradicts the task-22 contract. Then remove the `sk-` sentence from docs :78-79.
- The doc misstates the window size and the CR rule. `docs/driver-protocol.md:77-80`. Change "512-byte window" to "4096-byte preview window, or the frame-byte cap if smaller". Change "A frame's trailing CR" to "An LF-terminated frame's trailing CR".
- Redundant asserts. `tests/events/test_tail.py:668`, `:692`. Delete the follow-up `not any(...)` and `"ABCDE" not in preview` lines.

VERIFY:
- Full suite at HEAD is unconfirmed. Run `uv run pytest` at 0228eb0 and confirm exit 0. That includes `tests/drivers/test_claude_rate_limit.py`, which holds the DST time-only tests behind the P5 simplification.

KNOWN:
- (none)

R1: pass
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
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

Verdict: 15 findings
Tests: 3003 passed, 0 failed, 0 skipped (suite run this cycle)
