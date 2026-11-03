---
prd: docs/dev/project-management/prds/wip/00009-codex-adapter-v1.md
review: 1
date: 2026-10-05
head_sha: a7f4b4464c9bcb443b789c7e3c260cd6b3ef3375
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: 96ace41a
  carl: 66390ae4
---

# Review: 00009-codex-adapter-v1

Diff range: `e16ab432e8ce3e64029303b7e7d61bb7777b0894..a7f4b4464c9bcb443b789c7e3c260cd6b3ef3375`

codex_rung_guard: not fired
provider_review_guard: satisfied
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/alice-output-00009-c1-20261005.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/blake-output-00009-c1-20261005.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00009-c1-20261005.txt.receipt.json

The operator-authorized model-provider guard supersedes the legacy launcher-based Eve guard. Eve did not run. All required opposite-company rosters succeeded.

## Review Summary

18/18 completed tasks; full PRD work range. Three fresh isolated external Anthropic Claude Opus 5.5/xhigh reviews. Blake received only PRD/repository access. Immutable raw JSONL, stderr, text and receipts remain under docs/dev/tmp/.

Carl: skipped for cycle 1 by explicit operator decision on 2026-10-06, following the pre-launch approval denial. Required Alice/Blake/Bob reviews remain complete.

Engram pack failed: repo is unregistered. Fail-first replay skipped: sandbox could not create .git/worktrees/wt. Shape checker inspected 177 test functions in 18 files with no findings. No prior-cycle checks exist.

The staging gate reused 5467 passing tests at 4dc6c5d (subsequent commits changed workflow store only). Blake independently reports 5467 passing tests and clean ruff, formatting and mypy. Recorded build verification also includes successful uv sync and uv build.

## Coverage

| Task | Name | Status |
|---|---|---|
| 1 | P07-T03a: Decode thread, turn, text and plan records with total raw fallback | completed |
| 2 | P07-T03b: Decode command, file, MCP and web tool lifecycles | completed |
| 3 | P07-T03c: Project native collab tools and bounded receiver lanes | completed |
| 4 | P07-T03d: Normalize thread-cumulative usage with honest cache partitions | completed |
| 5 | P07-T03e: Decode native terminal failures and reduce provisional errors once | completed |
| 6 | P07-T05: Provide native skill prompts with one state-only handoff | completed |
| 7 | P07-T06a: Add the isolated scripted fake Codex executable | completed |
| 8 | P07-T06b: Run shared driver, raw-first and real process conformance | completed |
| 9 | P07-T06c: Prove shared decisions and command-backed build-review-done drain | completed |
| 10 | P07-T07: Verify Codex identity, activity, usage and raw projection | completed |
| 11 | P07-T03/P07-T05–T07: Document the live driver contract and evidence | completed |
| 12 | P07-T06aa: Fake argv, probes and replay | completed |
| 13 | P07-T06ab: Fake process and workflow scenarios | completed |
| 14 | P07-T06c0: Correct command-backed fake PRD completion | completed |
| 15 | P07-T06c1: Shared decision matrix for both native adapters | completed |
| 16 | P07-T06c2: Command-backed fake supervisor drain and retained results | completed |
| 17 | P07-T03/T05–T07: Document final driver API and decoding contract | completed |
| 18 | P07-T03/T05–T07: Document fixture provenance and remaining adapter changes | completed |

Full staged task contracts: docs/dev/tmp/review-tasks-00009-c1-20261005.md. Staged diff/context cover the same full range.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | 🟡 | Native failure `detail` is never bounded. `_failure_observations` passes the raw message straight into the `activity.message`, `session.failed` and `rate_limit.started` payloads, and `Observation` only sanitizes, it does not truncate. Confirmed: a 20000-char `turn.failed` message yields two observations with 20015-char details, and a top-level `error` keeps all 20000 chars. Frames up to 1 MiB pass through, and the rate-limit record duplicates them. The contract caps text/detail at 4096, and Claude's `failure_payload` bounds at source (src/ovcaq/drivers/claude_events.py:261). Fix: `detail = sanitize_text(detail)[:4096]` after classification, plus a regression test | src/ovcaq/drivers/codex.py:212 | 5 | ALICE, BOB |
| R2 | [2/3] | 🟡 | `CodexDriver.decode` raises on valid-JSON records that carry `NaN` or `Infinity` (which `json.loads` accepts) inside an MCP `result` or web `results`. `sanitize_json` raises `ValueError("JSON numbers must be finite")` out of `mcp_detail`/`web_detail`, confirmed with a one-line mcp_tool_call record. The shared `RawFirstDecoder` catch keeps the supervisor alive. But the driver's own contract ("never raise, return raw.unknown with a specific reason") fails, and the evidence reason drops to the generic "driver failed to decode frame". Deep nesting near the recursion limit takes the same path. Fix at the boundary: either `json.loads(raw_line, parse_constant=<raise ValueError>)`, which codex.py:165 already catches, or catch `(ValueError, TypeError, RecursionError)` in the two detail helpers. Add a malformed-record test | src/ovcaq/drivers/codex_events.py:99 | 2 | ALICE, BOB |
| R3 | [2/3] | 🟡 | Probe capture misses the bounded 16 KiB stdout/stderr contract. `--version` stdout streams into an unbounded `TemporaryFile`; only the 4096-byte read is capped. Auth stdout and all stderr go to DEVNULL, so an auth failure reports only "authentication check failed", with no exit code and no `codex login` hint. The contract asks for "sanitized actionable detail". This is a carried Pat MEDIUM/LOW that is still open. Capture through a pipe with a hard 16 KiB cap, and add the exit code and a login hint to the sanitized detail | src/ovcaq/drivers/codex.py:117 | general | ALICE, BOB |
| R4 | [2/3] | 🟡 | Functions over the 50-line limit, per the mechanical facts: `assert_workflow_handoff` (74) and `test_command_backed_workflow_handoffs` (75) in tests/drivers/test_codex_fake.py; `test_builtin_fake_command_handoffs_drain_and_retain_completed_results` (56) in tests/runtime/test_supervisor_adapters.py:154; `main` (51) in tests/fixtures/codex/v1/fake_codex.py:195. The build report already records the fake_codex.main style-gate failure. Split the per-phase handoff assertions into helpers | tests/drivers/test_codex_fake.py:311 | 13 | ALICE, BOB |
| R5 | [2/3] | 🟡 | Simplify `probe`: on each iteration the loop recomputes `label` by comparing `operation == ("--version",)`, then branches on `label` twice more, and the `"0.160.0"` literal appears twice. Iterate `(("version", ("--version",)), ("authentication", ("login", "status")))` and hoist `_PINNED_VERSION = "0.160.0"`. Same behavior, fewer branches | src/ovcaq/drivers/codex.py:115 | general | ALICE, BOB |
| R6 | [2/3] | 🟡 | CHANGELOG adds nine bullets for one unreleased feature. Three lead with internal task IDs ("P07-T02 adds", "P07-T03 task 1", "P07-T04 adds") instead of the user-visible effect, blank lines split the Added and Fixed lists, and both "Fixed" bullets fix code that was never released. Collapse to one or two user-facing Added bullets (carried Pat LOW) | CHANGELOG.md:9 | general | ALICE, BOB |
| R7 | [2/3] | 🟡 | `codex_activity.py` is a third module (43 lines) outside the design's module placement (codex.py + codex_events.py) and outside every task's writable Location, and it forced a packaging-inventory edit. Fold `item_activity` into codex_events.py | src/ovcaq/drivers/codex_activity.py:6 | 1 | ALICE, BOB |
| R8 | [2/3] | 🟡 | The rate-limit reset parser only accepts "reset at <ISO>" and "retry after N seconds". Real Codex 0.160.0 says "Try again at 3:45 PM." or "try again later" (upstream `retry_suffix`/`retry_suffix_after_or`). The repo's own rate-limited fixture ("try again in 60 seconds") is deliberately left unparsed. Result: every real Codex usage limit has an unknown reset and HALTs, so the "rate-limit with reset" path only works for text Codex never emits. tests/drivers/test_conformance.py:241 calls that invented text "native". | src/ovcaq/drivers/codex_events.py:262 | P07-T04 | BLAKE, BOB |
| R9 | [2/3] | ⚪ | `failure_reset` captures `reset at (\S+)`, so a trailing `.`, `,` or `)` makes `fromisoformat` fail and silently drops a valid deadline. `classify_failure` misses "usage limits", "quota limits" and "rate limiting" because of the trailing `\b`. Both fall back safely to None/unknown (carried Pat LOWs) | src/ovcaq/drivers/codex_events.py:262 | general | ALICE, BOB |
| R10 | [1/3] | 🟠 | Checked-in `connectivity-failed.jsonl` fixture does not classify as connectivity. Its message "Connection failed: unable to reach example endpoint." matches none of the connectivity patterns, so the classifier returns `unknown` (confirmed by running it). The fixture test can't catch this because it builds its expected value by calling `classify_failure` itself (tests/drivers/test_codex_decode_terminals.py:120). The decision matrix skips the fixture and uses a made-up "connection refused" string instead (tests/runtime/test_codex_decisions.py:138). Phase B exit ("fixture matrix produces expected summaries") fails for this family. | src/ovcaq/drivers/codex_events.py:245 | P07-T04 | BLAKE |
| R11 | [1/3] | 🟠 | Failure classifier is not based on real Codex 0.160.0 error text (checked against upstream `codex-rs/protocol/src/error.rs` at tag rust-v0.160.0). These real messages all come back `unknown`: "stream disconnected before completion: …" (Codex's main network failure), "Quota exceeded. Check your plan and billing details.", "internal error; agent loop died unexpectedly", "sandbox error: …", "Selected model is at capacity". Impact: a real network drop uses the died-retry budget (default 1) and then parks or halts, instead of the connectivity wait (3 retries, 1800 s). | src/ovcaq/drivers/codex_events.py:230 | P07-T04 | BLAKE |
| R12 | [1/3] | 🟡 | The version pin can be bypassed. `\bcodex-cli (\d+\.\d+\.\d+)\b` matches anywhere in the first 4096 bytes and accepts `codex-cli 0.160.0-beta.1` and `codex-cli 0.160.0.7` as `0.160.0` (confirmed). So probe reports an unreviewed CLI as healthy, which defeats the "fail health on an unreviewed version" drift guard. This is a carried Pat MEDIUM that is still open (00009-task-3-pat-02-corrected.md). Anchor to the first line, e.g. `^codex-cli (\d+\.\d+\.\d+)\s*$`, and test prerelease and extra-component outputs | src/ovcaq/drivers/codex.py:139 | general | ALICE |
| R13 | [1/3] | 🟡 | Simplify: the check uses `isinstance(..., bool)` and then needs a justification comment plus a `# noqa: TRY004` suppression in order to raise ValueError. Claude makes the same check as `type(options.get("allow_explicit_model", False)) is not bool` (src/ovcaq/drivers/claude.py:49) with no suppression. Use that idiom and drop the comment and the noqa. Behavior is identical, since bool cannot be subclassed | src/ovcaq/drivers/codex.py:58 | general | ALICE |
| R14 | [1/3] | 🟡 | `CodexDriver.probe()` (binary check, exact 0.160.0 version pin, `login status` auth check) never runs in production. `build_driver` and `supervisor_cli` build the driver without probing it. Only `discover_drivers` calls `probe()` (src/ovcaq/drivers/base.py:155), and no code under src calls `discover_drivers`. So the CLI-drift guard and the auth check do nothing in real runs, and a newer CLI would launch unchecked. | src/ovcaq/drivers/edge.py:26 | P07-T04 | BLAKE |
| R15 | [1/3] | 🟡 | All 8 JSONL fixture families are `schema-synthetic`, including healthy and tool-active, even though codex-cli 0.160.0 is installed here. The PRD allows synthesized families only when live capture is impractical (rate-limited, permission-failed). The made-up failure messages (see the connectivity finding) show the drift this causes. | tests/fixtures/codex/v1/provenance.json:12 | Phase A | BLAKE |
| R16 | [1/3] | 🟡 | The TUI Activity panel shows only lanes. Codex command, file-change, MCP, web, plan and message activity is decoded but never displayed, so a Codex session without collaboration lanes shows "no lanes observed". The PRD requires that the "TUI shows Codex identity/activity/usage". docs/driver-protocol.md:273 admits that panels render lanes only. | src/ovcaq/tui/panels.py:86 | Phase C | BLAKE |
| R17 | [1/3] | 🟡 | P07-T07 wants actual native lanes shown from real fake-Supervisor output. In `lanes.jsonl`, the `receiver_thread_ids` and `agents_states` keys never match, so the fake-Supervisor "lanes" scenario asserts no lanes. The only visible lane comes from a test that rewrites the provider payload in place (`matched=True`). | tests/tui/test_codex_projection.py:256 | 10 | BOB |
| R18 | [1/3] | 🟡 | Simplification: chained ternary for `detail`. Replace with `source = record if event == "error" else record.get("error")` and `detail = source.get("message") if isinstance(source, dict) else None`. | src/ovcaq/drivers/codex.py:205 | 5 | BOB |
| R19 | [1/3] | 🟡 | The conflicting-thread contract does not survive the supervised path. Supervisor passes `session_id` to RawFirstDecoder (src/ovcaq/runtime/supervisor.py:455), which rebinds run_id and session_id on every observation (src/ovcaq/events/tail.py:137). The reducer never sees distinct thread IDs, so the "reduce to unknown failure" claim and "supplied run ID and current thread as session ID" in the docs hold only in unit tests that call `reduce_session` directly. | docs/driver-protocol.md:167 | general | BOB |
| R20 | [1/3] | ⚪ | `turn_usage` keeps a single `gap` string, and later branches overwrite it. A malformed-counter reason gets replaced by the partition or reads-exceed-input reason, so the raw.unknown still appears but names only the last cause. Keep the first reason or join them | src/ovcaq/drivers/codex_events.py:44 | 4 | ALICE |
| R21 | [1/3] | ⚪ | The Codex lane statuses `interrupted`, `shutdown` and `not_found` are mapped to raw.unknown with no lane end event. A lane that was started earlier then shows as "running" in the TUI forever. | src/ovcaq/drivers/codex_events.py:154 | Phase B | BLAKE |
| R22 | [1/3] | ⚪ | Scope creep: the `sandbox` and `approval` driver options are not in the PRD and accept only their one hard-coded value. They add config surface that changes nothing. | src/ovcaq/drivers/codex.py:51 | P07-T02 | BLAKE |
| R23 | [1/3] | ⚪ | Default phase tiers use Claude family names (`sonnet`/`opus`), so a Codex config must define those tier keys or override every phase. The Codex tests hide this by using `{"sonnet":…, "opus":…}` (tests/tui/test_codex_projection.py:66). The PRD lists src/ovcaq/config.py, but it was not changed. | src/ovcaq/drivers/__init__.py:18 | general | BLAKE |
| R24 | [1/3] | ⚪ | The prompt-override test sets the configured prompts equal to the default prompt and then checks `default_prompt`, so it would still pass if overrides were ignored. | tests/drivers/test_codex_prompt.py:52 | Phase A | BLAKE |
| R25 | [1/3] | ⚪ | `gap = gap or "Conflicting thread identity"` drops the conflict reason when the usage itself also has a gap (malformed or all-zero). `_thread_conflict` is then cleared, so the conflict is never reported. | src/ovcaq/drivers/codex.py:254 | 4 | BOB |
| R26 | [1/3] | ⚪ | The only change to test_supervisor.py is a no-op import rewrap. It does not trace to the task, which put the drain in a new file instead. | tests/runtime/test_supervisor.py:29 | 16 | BOB |
| R27 | [1/3] | ⚪ | On timeout, `subprocess.run(timeout=5)` kills only the direct child, so wrapper descendants can be orphaned. | src/ovcaq/drivers/codex.py:119 | P07-T04 | BOB |

Consolidation was model-side after the script incorrectly clustered unrelated same-file findings (version pin, capture bounds, failure detail and label simplification). Nine confirmed duplicate pairs were combined: 36 raw issues become 27 distinct findings, including two HIGH. Every original issue and rubric verdict is retained below.

## Alice

Provider: Anthropic; served model: claude-opus-5-5; effort: xhigh; session: a6fdae3c-51cd-4f44-ac33-f7a6f875d98d. Source: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/alice-output-00009-c1-20261005.txt`.

[ALICE] 🟡 Native failure `detail` is never bounded. `_failure_observations` passes the raw message straight into the `activity.message`, `session.failed` and `rate_limit.started` payloads, and `Observation` only sanitizes, it does not truncate. Confirmed: a 20000-char `turn.failed` message yields two observations with 20015-char details, and a top-level `error` keeps all 20000 chars. Frames up to 1 MiB pass through, and the rate-limit record duplicates them. The contract caps text/detail at 4096, and Claude's `failure_payload` bounds at source (src/ovcaq/drivers/claude_events.py:261). Fix: `detail = sanitize_text(detail)[:4096]` after classification, plus a regression test | File: src/ovcaq/drivers/codex.py:212 | Task: 5
[ALICE] 🟡 `CodexDriver.decode` raises on valid-JSON records that carry `NaN` or `Infinity` (which `json.loads` accepts) inside an MCP `result` or web `results`. `sanitize_json` raises `ValueError("JSON numbers must be finite")` out of `mcp_detail`/`web_detail`, confirmed with a one-line mcp_tool_call record. The shared `RawFirstDecoder` catch keeps the supervisor alive. But the driver's own contract ("never raise, return raw.unknown with a specific reason") fails, and the evidence reason drops to the generic "driver failed to decode frame". Deep nesting near the recursion limit takes the same path. Fix at the boundary: either `json.loads(raw_line, parse_constant=<raise ValueError>)`, which codex.py:165 already catches, or catch `(ValueError, TypeError, RecursionError)` in the two detail helpers. Add a malformed-record test | File: src/ovcaq/drivers/codex_events.py:99 | Task: 2
[ALICE] 🟡 The version pin can be bypassed. `\bcodex-cli (\d+\.\d+\.\d+)\b` matches anywhere in the first 4096 bytes and accepts `codex-cli 0.160.0-beta.1` and `codex-cli 0.160.0.7` as `0.160.0` (confirmed). So probe reports an unreviewed CLI as healthy, which defeats the "fail health on an unreviewed version" drift guard. This is a carried Pat MEDIUM that is still open (00009-task-3-pat-02-corrected.md). Anchor to the first line, e.g. `^codex-cli (\d+\.\d+\.\d+)\s*$`, and test prerelease and extra-component outputs | File: src/ovcaq/drivers/codex.py:139 | Task: general
[ALICE] 🟡 Probe capture misses the bounded 16 KiB stdout/stderr contract. `--version` stdout streams into an unbounded `TemporaryFile`; only the 4096-byte read is capped. Auth stdout and all stderr go to DEVNULL, so an auth failure reports only "authentication check failed", with no exit code and no `codex login` hint. The contract asks for "sanitized actionable detail". This is a carried Pat MEDIUM/LOW that is still open. Capture through a pipe with a hard 16 KiB cap, and add the exit code and a login hint to the sanitized detail | File: src/ovcaq/drivers/codex.py:117 | Task: general
[ALICE] 🟡 Functions over the 50-line limit, per the mechanical facts: `assert_workflow_handoff` (74) and `test_command_backed_workflow_handoffs` (75) in tests/drivers/test_codex_fake.py; `test_builtin_fake_command_handoffs_drain_and_retain_completed_results` (56) in tests/runtime/test_supervisor_adapters.py:154; `main` (51) in tests/fixtures/codex/v1/fake_codex.py:195. The build report already records the fake_codex.main style-gate failure. Split the per-phase handoff assertions into helpers | File: tests/drivers/test_codex_fake.py:311 | Task: 13
[ALICE] 🟡 Simplify: the check uses `isinstance(..., bool)` and then needs a justification comment plus a `# noqa: TRY004` suppression in order to raise ValueError. Claude makes the same check as `type(options.get("allow_explicit_model", False)) is not bool` (src/ovcaq/drivers/claude.py:49) with no suppression. Use that idiom and drop the comment and the noqa. Behavior is identical, since bool cannot be subclassed | File: src/ovcaq/drivers/codex.py:58 | Task: general
[ALICE] 🟡 Simplify `probe`: on each iteration the loop recomputes `label` by comparing `operation == ("--version",)`, then branches on `label` twice more, and the `"0.160.0"` literal appears twice. Iterate `(("version", ("--version",)), ("authentication", ("login", "status")))` and hoist `_PINNED_VERSION = "0.160.0"`. Same behavior, fewer branches | File: src/ovcaq/drivers/codex.py:115 | Task: general
[ALICE] ⚪ CHANGELOG adds nine bullets for one unreleased feature. Three lead with internal task IDs ("P07-T02 adds", "P07-T03 task 1", "P07-T04 adds") instead of the user-visible effect, blank lines split the Added and Fixed lists, and both "Fixed" bullets fix code that was never released. Collapse to one or two user-facing Added bullets (carried Pat LOW) | File: CHANGELOG.md:9 | Task: general
[ALICE] ⚪ `failure_reset` captures `reset at (\S+)`, so a trailing `.`, `,` or `)` makes `fromisoformat` fail and silently drops a valid deadline. `classify_failure` misses "usage limits", "quota limits" and "rate limiting" because of the trailing `\b`. Both fall back safely to None/unknown (carried Pat LOWs) | File: src/ovcaq/drivers/codex_events.py:262 | Task: general
[ALICE] ⚪ `turn_usage` keeps a single `gap` string, and later branches overwrite it. A malformed-counter reason gets replaced by the partition or reads-exceed-input reason, so the raw.unknown still appears but names only the last cause. Keep the first reason or join them | File: src/ovcaq/drivers/codex_events.py:44 | Task: 4
[ALICE] ⚪ `codex_activity.py` is a third module (43 lines) outside the design's module placement (codex.py + codex_events.py) and outside every task's writable Location, and it forced a packaging-inventory edit. Fold `item_activity` into codex_events.py | File: src/ovcaq/drivers/codex_activity.py:6 | Task: 1

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
R12: fail
R13: pass

## Blake

Provider: Anthropic; served model: claude-opus-5-5; effort: xhigh; session: 0f7490a3-dfda-42f7-9ce5-0f9a83e564fd. Source: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/blake-output-00009-c1-20261005.txt`.

[BLAKE] 🟠 Checked-in `connectivity-failed.jsonl` fixture does not classify as connectivity. Its message "Connection failed: unable to reach example endpoint." matches none of the connectivity patterns, so the classifier returns `unknown` (confirmed by running it). The fixture test can't catch this because it builds its expected value by calling `classify_failure` itself (tests/drivers/test_codex_decode_terminals.py:120). The decision matrix skips the fixture and uses a made-up "connection refused" string instead (tests/runtime/test_codex_decisions.py:138). Phase B exit ("fixture matrix produces expected summaries") fails for this family. | File: src/ovcaq/drivers/codex_events.py:245 | Task: P07-T04
[BLAKE] 🟠 Failure classifier is not based on real Codex 0.160.0 error text (checked against upstream `codex-rs/protocol/src/error.rs` at tag rust-v0.160.0). These real messages all come back `unknown`: "stream disconnected before completion: …" (Codex's main network failure), "Quota exceeded. Check your plan and billing details.", "internal error; agent loop died unexpectedly", "sandbox error: …", "Selected model is at capacity". Impact: a real network drop uses the died-retry budget (default 1) and then parks or halts, instead of the connectivity wait (3 retries, 1800 s). | File: src/ovcaq/drivers/codex_events.py:230 | Task: P07-T04
[BLAKE] 🟡 The rate-limit reset parser only accepts "reset at <ISO>" and "retry after N seconds". Real Codex 0.160.0 says "Try again at 3:45 PM." or "try again later" (upstream `retry_suffix`/`retry_suffix_after_or`). The repo's own rate-limited fixture ("try again in 60 seconds") is deliberately left unparsed. Result: every real Codex usage limit has an unknown reset and HALTs, so the "rate-limit with reset" path only works for text Codex never emits. tests/drivers/test_conformance.py:241 calls that invented text "native". | File: src/ovcaq/drivers/codex_events.py:262 | Task: P07-T04
[BLAKE] 🟡 `CodexDriver.probe()` (binary check, exact 0.160.0 version pin, `login status` auth check) never runs in production. `build_driver` and `supervisor_cli` build the driver without probing it. Only `discover_drivers` calls `probe()` (src/ovcaq/drivers/base.py:155), and no code under src calls `discover_drivers`. So the CLI-drift guard and the auth check do nothing in real runs, and a newer CLI would launch unchecked. | File: src/ovcaq/drivers/edge.py:26 | Task: P07-T04
[BLAKE] 🟡 All 8 JSONL fixture families are `schema-synthetic`, including healthy and tool-active, even though codex-cli 0.160.0 is installed here. The PRD allows synthesized families only when live capture is impractical (rate-limited, permission-failed). The made-up failure messages (see the connectivity finding) show the drift this causes. | File: tests/fixtures/codex/v1/provenance.json:12 | Task: Phase A
[BLAKE] 🟡 The TUI Activity panel shows only lanes. Codex command, file-change, MCP, web, plan and message activity is decoded but never displayed, so a Codex session without collaboration lanes shows "no lanes observed". The PRD requires that the "TUI shows Codex identity/activity/usage". docs/driver-protocol.md:273 admits that panels render lanes only. | File: src/ovcaq/tui/panels.py:86 | Task: Phase C
[BLAKE] ⚪ The Codex lane statuses `interrupted`, `shutdown` and `not_found` are mapped to raw.unknown with no lane end event. A lane that was started earlier then shows as "running" in the TUI forever. | File: src/ovcaq/drivers/codex_events.py:154 | Task: Phase B
[BLAKE] ⚪ Scope creep: the `sandbox` and `approval` driver options are not in the PRD and accept only their one hard-coded value. They add config surface that changes nothing. | File: src/ovcaq/drivers/codex.py:51 | Task: P07-T02
[BLAKE] ⚪ Default phase tiers use Claude family names (`sonnet`/`opus`), so a Codex config must define those tier keys or override every phase. The Codex tests hide this by using `{"sonnet":…, "opus":…}` (tests/tui/test_codex_projection.py:66). The PRD lists src/ovcaq/config.py, but it was not changed. | File: src/ovcaq/drivers/__init__.py:18 | Task: general
[BLAKE] ⚪ The prompt-override test sets the configured prompts equal to the default prompt and then checks `default_prompt`, so it would still pass if overrides were ignored. | File: tests/drivers/test_codex_prompt.py:52 | Task: Phase A

Gates (all exit 0):
```
uv run pytest           -> 5467 passed, 2 warnings (tmp cleanup race from a parallel run)
Codex-scoped subset     -> 985 passed
ruff check / ruff format --check / mypy src/ovcaq -> clean
```

B1: fail
B2: pass
B3: pass
B4: pass
B5: fail
B6: pass
B7: fail
B8: pass
B9: fail
B10: pass
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

Provider: Anthropic; served model: claude-opus-5-5; effort: xhigh; session: e5e22198-5561-4e41-8e8e-e1b8c23d1209. Source: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00009-c1-20261005.txt`.

[BOB] 🟡 Failure detail has no length cap. `_failure_observations` checks that `detail` is a string, then puts the full native message into `activity.message`, `session.failed` and `rate_limit.started`. Sanitization happens, but nothing limits the length, so normalized records can hold up to the 1 MiB frame cap. The spec says "Bound text/detail to 4096". | File: src/ovcaq/drivers/codex.py:212 | Task: 5
[BOB] 🟡 The version probe writes stdout to an unbounded `TemporaryFile`. Only the read is capped, at 4096 bytes, so the child can fill the disk during the 5 s window. The contract asks for 16 KiB bounded capture. This was carried from the task-3 Pat review and is still open. | File: src/ovcaq/drivers/codex.py:117 | Task: P07-T04
[BOB] 🟡 P07-T07 wants actual native lanes shown from real fake-Supervisor output. In `lanes.jsonl`, the `receiver_thread_ids` and `agents_states` keys never match, so the fake-Supervisor "lanes" scenario asserts no lanes. The only visible lane comes from a test that rewrites the provider payload in place (`matched=True`). | File: tests/tui/test_codex_projection.py:256 | Task: 10
[BOB] 🟡 Four functions exceed the 50-line limit (R12): `assert_workflow_handoff` (74 lines, 12 positional params), `test_command_backed_workflow_handoffs` (75), `test_builtin_fake_command_handoffs_drain_and_retain_completed_results` (56) and fake `main` (51). | File: tests/drivers/test_codex_fake.py:311 | Task: general
[BOB] 🟡 CHANGELOG adds 9 Added and 2 Fixed entries for one unreleased feature. Some name internal task IDs ("P07-T03 task 1", "P07-T04", "P07-T02") and describe implementation detail ("package inventory"). Fixed entries for code that never shipped are noise. Task 18 asked for one concise entry. | File: CHANGELOG.md:11 | Task: 18
[BOB] 🟡 Simplification: `codex_activity.py` is a 43-line module holding one function with one caller. Fold `item_activity` into `codex_events.py` next to `item_tool`/`item_lanes` (about 320 lines total) and drop its packaging-inventory entry. | File: src/ovcaq/drivers/codex_activity.py:6 | Task: 1
[BOB] 🟡 Simplification: `probe` works out the label with `operation == ("--version",)`, reads `version` after the loop, and repeats the literal "0.160.0" pin. Iterate `(("version", ("--version",)), ("authentication", ("login", "status")))` and add a `_PINNED_VERSION` constant. | File: src/ovcaq/drivers/codex.py:115 | Task: P07-T04
[BOB] 🟡 Simplification: chained ternary for `detail`. Replace with `source = record if event == "error" else record.get("error")` and `detail = source.get("message") if isinstance(source, dict) else None`. | File: src/ovcaq/drivers/codex.py:205 | Task: 5
[BOB] ⚪ `json.loads` accepts NaN/Infinity by default. A non-finite number inside an MCP `result` or web `results` makes `sanitize_json` raise from `decode`. Only RawFirstDecoder's catch-all turns that into raw.unknown, so a direct `decode` call breaks the "return raw.unknown" contract. | File: src/ovcaq/drivers/codex.py:164 | Task: 2
[BOB] ⚪ `gap = gap or "Conflicting thread identity"` drops the conflict reason when the usage itself also has a gap (malformed or all-zero). `_thread_conflict` is then cleared, so the conflict is never reported. | File: src/ovcaq/drivers/codex.py:254 | Task: 4
[BOB] ⚪ `reset at (\S+)` captures trailing punctuation, so "reset at 2026-10-05T12:00:00Z." returns None. | File: src/ovcaq/drivers/codex_events.py:262 | Task: P07-T04
[BOB] ⚪ The only change to test_supervisor.py is a no-op import rewrap. It does not trace to the task, which put the drain in a new file instead. | File: tests/runtime/test_supervisor.py:29 | Task: 16
[BOB] 🟡 The conflicting-thread contract does not survive the supervised path. Supervisor passes `session_id` to RawFirstDecoder (src/ovcaq/runtime/supervisor.py:455), which rebinds run_id and session_id on every observation (src/ovcaq/events/tail.py:137). The reducer never sees distinct thread IDs, so the "reduce to unknown failure" claim and "supplied run ID and current thread as session ID" in the docs hold only in unit tests that call `reduce_session` directly. | File: docs/driver-protocol.md:167 | Task: general
[BOB] ⚪ On timeout, `subprocess.run(timeout=5)` kills only the direct child, so wrapper descendants can be orphaned. | File: src/ovcaq/drivers/codex.py:119 | Task: P07-T04
[BOB] ⚪ The reset grammar only accepts `retry after N seconds` or `reset at <ISO>`. The rate-limited fixture says "try again in 60 seconds", so it never yields a reset. | File: tests/fixtures/codex/v1/rate-limited.jsonl:3 | Task: 5

R1: pass
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: fail
R13: pass

FIX:
- Unbounded failure detail — src/ovcaq/drivers/codex.py:212 — classify on the full text, then store `bounded = sanitize_text(detail)[:4096]` in the activity, session.failed and rate_limit payloads; add a test with a 10k-char message asserting `len(detail) <= 4096`
- Probe temp file has no size limit — src/ovcaq/drivers/codex.py:117 — use `Popen(stdout=PIPE)`, read at most 16 KiB, kill the child on overflow or at the 5 s deadline, and drop `TemporaryFile`
- No native lane through the fake Supervisor — tests/fixtures/codex/v1/lanes.jsonl:3 — add one collab record whose `agents_states` key equals its receiver ID, refresh the provenance sha256, and assert at tests/tui/test_codex_projection.py:256 that the "lanes" scenario renders that lane
- Functions over 50 lines — tests/drivers/test_codex_fake.py:311 — split out `_assert_prd_completion` and the `phase-complete` argv check, pass a small dataclass instead of 12 positional args, move the historical/current seeding at :407 into a fixture, and hoist the fake `main` replay set (tests/fixtures/codex/v1/fake_codex.py:229) and the tests/runtime/test_supervisor_adapters.py:154 setup into helpers
- Changelog bloat — CHANGELOG.md:11 — replace the 9 Added entries with one or two user-visible `**drivers**` lines, remove task IDs, and drop the two Fixed entries for unreleased Codex code
- Single-caller module — src/ovcaq/drivers/codex_activity.py:6 — move `item_activity` into codex_events.py, update the import at src/ovcaq/drivers/codex.py:16 and the packaging inventory
- Probe label and pin duplication — src/ovcaq/drivers/codex.py:115 — iterate (label, operation) pairs and add `_PINNED_VERSION = "0.160.0"`
- Chained ternary — src/ovcaq/drivers/codex.py:205 — use the two-line `source`/`detail` form above
- NaN/Infinity leaks a raise from decode — src/ovcaq/drivers/codex.py:164 — pass `json.loads(raw_line, parse_constant=...)` a handler that raises ValueError, which the existing except turns into raw.unknown; add a malformed case with `NaN` in an MCP result
- Conflict gap dropped — src/ovcaq/drivers/codex.py:254 — when `_thread_conflict` is set, emit the conflict as its own raw.unknown, alongside any usage gap
- Reset regex takes trailing punctuation — src/ovcaq/drivers/codex_events.py:262 — capture `(\d{4}-\d{2}-\d{2}T[\d:.]+(?:Z|[+-]\d{2}:\d{2}))` instead of `\S+`, and add a trailing-period test
- No-op import rewrap — tests/runtime/test_supervisor.py:29 — revert the hunk
VERIFY:
- Conflicting threads under the real Supervisor — add a fake_codex scenario that emits `thread.started` A, then `thread.started` B, then `turn.completed`; run `Supervisor.run_once()` with it and assert `result.summary.success is False and result.summary.failure_class == "unknown"`. If it fails, which static reading of tail.py:137 predicts, either detect the conflict in `CodexDriver.summarize` from distinct `usage.updated` identity payloads, or correct docs/driver-protocol.md:167 to say the Supervisor-bound session ID replaces thread identity
KNOWN:
- Probe timeout can orphan wrapper descendants — recorded as a dispatch-3 non-blocker in the accepted design; P07-T04 probe ownership is outside this PRD's fixture/fake scope
- Narrow reset grammar ("try again in N seconds" gives no reset) — the spec allows only explicit ISO or `retry after N seconds`, and the design log records the missing native-formatter evidence as an open non-blocker

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

## Carl

Unavailable before launch: automatic approval review denied the Gemini payload/destination. No output exists and no substitute ran.

Recovery, 2026-10-06: the operator explicitly authorized skipping optional Carl for this cycle and resuming the decision gate using the existing reviews. This does not authorize a Gemini dispatch or change future-cycle policy.

## Decision Gate

Cycle 1: 22 fixes, 5 settled deferrals. Both HIGHs remain unresolved and queued for repair. Cycle 1 is below cap 2. No CRITICAL, new dependency, blocking foundational decision, prior-cycle recurrence or exact runnable verification-queue entry. New bounded D1 follow-ups retain original attempt history. The canonical grouper caps follow-ups at four tasks, below the scope alarm. No implementation or convergence occurs here.

HIGH R10/R11 add provider-edge diagnostic recognition and independent regressions without changing signatures, types, schemas or public interfaces; Protocol C/D triggers do not apply. Pat carry-forwards are pre-completion reviews, not prior review-cycle repairs; Protocol B does not apply.

| Ref | Classification | Reason |
|---|---|---|
| R1 | Auto-fix (queued) | Mechanical bound/sanitization fix after full-text classification, with independent regressions. |
| R2 | Auto-fix (queued) | Mechanical direct-decoder totality fix for nonfinite/deep malformed detail, before state mutation. |
| R3 | Auto-fix (queued) | Mechanical accepted 16 KiB probe-capture contract and actionable sanitized failure detail; fixture/fake checks only. |
| R4 | Auto-fix (queued) | Mechanical helper extraction using computed function lengths, preserving behavioral assertions. |
| R5 | Auto-fix (queued) | Mechanical probe-label/version-pin simplification with R3/R12. |
| R6 | Auto-fix (queued) | Mechanical concise user-visible unreleased feature notes; remove task IDs. |
| R7 | Auto-fix (queued) | Mechanical module placement correction and package-inventory reconciliation. |
| R8 | Defer to batch end | Requirements ambiguity: accepted design lines 187-192 permits explicit aware ISO or retry-after seconds only and rejects ambiguous local clock prose. Native formatter expansion needs a contract decision; retain unknown deadlines without guessing timezone. |
| R9 | Auto-fix (queued) | Low severity mechanical classifier/reset grammar fixes preserving aware/future/six-hour rules. |
| R10 | Auto-fix (queued) | Additive-only HIGH: extend connectivity recognition and independently assert checked-in fixture expectations; no signature/type/schema/public-interface change. |
| R11 | Auto-fix (queued) | Additive-only HIGH: extend provider-edge diagnostic recognition with pinned upstream evidence and independent regressions; preserve precedence/unknown fallback, no public API/data-model change. |
| R12 | Auto-fix (queued) | Mechanical exact version-pin validation and prerelease/extra-component regressions. |
| R13 | Auto-fix (queued) | Mechanical bool-validation simplification preserving exception contract. |
| R14 | Auto-fix (queued) | Medium 1/3: invoke existing health contract at provider-neutral production launch boundary, covered by fake probes and both adapters; no provider-specific supervisor branch. |
| R15 | Defer to batch end | Requirements ambiguity: PRD prefers live capture when practical; accepted design lines 65-76 authorizes honestly labeled synthesis when a safe existing transcript is unavailable. Provenance confirms none supplied. Decide capture policy at batch end; do not fabricate capture provenance or launch real smoke. |
| R16 | Auto-fix (queued) | Medium 1/3: display existing normalized activity through shared presentation models, covered by both adapters and neutrality scans. |
| R17 | Auto-fix (queued) | Medium 1/3: consistent native collab fixture plus real Supervisor lane assertion; preserve mismatched-ID unknown coverage and refresh provenance hash. |
| R18 | Auto-fix (queued) | Mechanical failure-detail expression simplification with R1. |
| R19 | Auto-fix (queued) | Medium 1/3: real Supervisor conflicting-thread regression and uphold specified unknown-failure contract through normalized evidence. Do not weaken docs or add provider branches. |
| R20 | Auto-fix (queued) | Low severity mechanical preservation of all usage-gap reasons. |
| R21 | Auto-fix (queued) | Low severity additive terminal lane projections backed by pinned native status evidence. |
| R22 | Defer to batch end | Requirements ambiguity: accepted design lines 99-101 mandates the sandbox/approval options that this finding calls out of scope. Removing accepted config requires a contract decision; preserve safe fixed values. |
| R23 | Defer to batch end | Requirements ambiguity: accepted design reuses shared config and logical tier mappings. Renaming shared defaults changes configuration behavior; decide neutral naming and migration scope at batch end. |
| R24 | Auto-fix (queued) | Low severity distinct override regression through actual prompt-resolution path. |
| R25 | Auto-fix (queued) | Low severity independent conflict-gap preservation with R19. |
| R26 | Auto-fix (queued) | Low severity revert unrelated import-only rewrap. |
| R27 | Defer to batch end | Accepted design dispatch-3 non-blocker records probe descendant ownership outside this fixture/fake PRD. Defer ownership policy rather than silently expand process-group behavior. |

Deferred findings are preserved verbatim in the settled-decisions ledger and workflow decisions. Bob VERIFY lacks an exact existing command, so R19 remains a behavioral fix. The operator-authorized Carl skip applies only to this cycle. All required raw rubrics and immutable receipts are unchanged.

Queued canonical task groups (no manual splitting/merging):

- Task 19 (sonnet): R1, R2, R3, R5, R7, R9, R10, R11, R12, R13, R14, R16, R18, R20, R21, R25
- Task 20 (sonnet): R6, R19
- Task 21 (sonnet): R17, R26
- Task 22 (sonnet): R4, R24

Validation: schema and 18/22 task counts pass; all 22 fix findings appear exactly once across pending tasks; all five deferrals have detailed state and ledger records; original 18 tasks/attempt provenance unchanged; snapshot-bound full rubrics and three immutable Anthropic receipts pass.

Verdict: 27 findings
Tests: 5467 passed, 0 failed, 0 skipped (staging reused last-verification.json at 4dc6c5d; Blake independently ran the suite this cycle)
