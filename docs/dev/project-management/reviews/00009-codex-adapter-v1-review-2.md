---
prd: docs/dev/project-management/prds/wip/00009-codex-adapter-v1.md
review: 2
date: 2026-10-06
head_sha: a5064af9d35f779a0032bce77154909a089c6a00
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: bd944fd9
  carl: 9dad5ad5
---

# Review: 00009-codex-adapter-v1

Diff range: `a7f4b4464c9bcb443b789c7e3c260cd6b3ef3375..a5064af9d35f779a0032bce77154909a089c6a00`

codex_rung_guard: not fired
provider_review_guard: satisfied

Carl: skipped for cycle 2 by explicit operator decision ("skip Carls") on 2026-10-07. The prior pre-launch denial remains preserved; no Gemini/Copilot export is authorized. Required Alice/Blake/Bob reviews and all 34 findings remain unchanged. Resume this cycle at the decision gate.
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/alice-output-00009-c2-20261006.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/blake-output-00009-c2-20261006.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00009-c2-20261006.txt.receipt.json

The operator-authorized model-provider guard supersedes the legacy launcher/Eve guard. Eve did not run. All three opposite-company lenses ran as fresh isolated Anthropic processes, observed claude-opus-5-5, requested opus/xhigh. Blake received only the PRD and repository access. No implementation thread was resumed.

## Review Summary

30/30 tasks complete; original work range preserved; this cycle reviews rework incrementally and Blake audits the entire PRD independently. All raw verdict lines are retained below. Required provider receipts and full rubric coverage validate.

Carl: unavailable (automatic approval review denied optional Gemini/Copilot export of repository context before launch; no backend ran, no retry or bypass). The host contract requires a precise persisted pause after permission denial. Operator must authorize Carl or explicitly skip this cycle; cycle/cap remain 2/2. No convergence, cap-out deferral, repairs or new tasks have been authorized by this pause.

Engram pack failed because the repository is unregistered. Tautology checker inspected 93 tests without findings. Replay ran 101 tests against the prior code: 86 failed, 15 passed; one file could not collect at base. All seven replay findings are absorbed below for later intent adjudication. No prior checks-1 queue exists. The replay worktree is removed.

The stage reused 5591 passing tests from b95bcaf; the coordinator subsequently ran the full suite at reviewed HEAD: 5591 passed, zero failed/skipped, two temporary-directory cleanup warnings, 223.28 seconds. Sync, Ruff lint/format, mypy (61 files) and package build all pass. Blake independently ran 5591 tests with the same two warnings. Durable verification: reports/00009-cycle2-verification.json.

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
| 19 | [D1] src/ovcaq/ | completed |
| 20 | [D1] prose | completed |
| 21 | [D1] tests/ | completed |
| 22 | [D1] tests/drivers/ | completed |
| 23 | [D1] Task 19 split: decoder | completed |
| 24 | [D1] Task 19 split: probe | completed |
| 25 | [D1] Task 19 split: placement | completed |
| 26 | [D1] Task 19 split: shared health and activity | completed |
| 27 | [D1] Task25 split: activity placement | completed |
| 28 | [D1] Task25 split: packaging inventory | completed |
| 29 | [D1] Task21 split: consistent native lane fixture | completed |
| 30 | [D1] Task21 split: unrelated import rewrap | completed |

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | 🟡 | The fix for R21 (interrupted/shutdown/not_found lanes) also catches lanes that already finished. The "started" set at codex.py:372 is built from every lane identity, including ones marked done. So a lane that completed and is later reported as `shutdown` (for example by a `close_agent` or `wait` call) emits `lane.failed`, and the TUI accepts the change from completed to failed. Confirmed by running it: running → completed → shutdown gives `['tool.completed', 'lane.failed']`. Fix: pass only lanes that are not done (`{lane for (cat, lane), done in self._identities.items() if cat == "lane" and not done}`), make `started_lanes` a required parameter (codex_events.py:205, its only caller always passes it), and add a test for completed-then-shutdown | src/ovcaq/drivers/codex.py:372 | 23 | ALICE, BOB |
| R2 | [2/3] | 🟡 | `bounded_detail` redacts credentials first and strips terminal controls second. A key split by an escape sequence therefore survives redaction and is joined back together. Confirmed: `bounded_detail("token sk-abc\x1b[0mdefghijklmnopqrstuvwxyz0123456789ABCDEF")` returns the full `sk-abcdef…` key unredacted, and that text lands in persisted `session.failed`, `rate_limit.started` and lane payloads. The existing `_bounded` (src/ovcaq/supervisor_cli.py:77) strips first and then sanitizes. Fix: swap the order, add a regression test, and consider sharing one helper instead of a second copy of the ANSI regex | src/ovcaq/drivers/codex_events.py:57 | 23 | ALICE, BOB |
| R3 | [2/3] | 🟡 | The R16 activity view drops the detail on error and warning messages. `_observe_activity` reads only `payload["text"]`, but the Codex provisional top-level `error` (codex.py:278) and Claude `rate_limit_warning` (claude_events.py:143) carry their message in `detail`, so they render as a bare "error" or "rate_limit_warning". These payloads and Codex `turn` messages also have no `message_id`, so they share the key `("message", "")`. The next `turn` line then replaces the error line. The test at tests/tui/test_rework_activity.py:86 uses `text` for kind `error`, so it never exercises the real provisional shape. Confirmed by code reading. Fix: fall back to `detail` when `text` is missing, give message_id-less entries a distinct key (for example kind plus sequence), and test the real provisional-error payload | src/ovcaq/tui/model.py:575 | 26 | ALICE, BOB |
| R4 | [2/3] | 🟡 | "Selected model is at capacity" (upstream ServerOverloaded, a transient overload) is now classified as `rate_limit`. That message never carries a reset time, so decision.py:197-213 halts the batch on the first occurrence. Before this rework it was `unknown` and got one retry. The design taxonomy puts "server unavailable/503" under connectivity, which waits and retries with a bound. Move `model is at capacity` to the connectivity pattern and update the expectation at tests/drivers/test_codex_rework_decode.py:94 | src/ovcaq/drivers/codex_events.py:309 | 23 | ALICE, BOB |
| R5 | [2/3] | 🟡 | Simplify `_report_runtime_error`. It is named as a reporter, but it now raises in 2 of its 3 branches. The third branch returns an `Exception` that the only caller ignores, and the caller then does a bare `raise` (supervisor_cli.py:193-194). Make it `-> None`, drop `return error` (fall through), or rename it `_raise_runtime_error`. Behavior stays the same | src/ovcaq/supervisor_cli.py:144 | 26 | ALICE, BOB |
| R6 | [2/3] | ⚪ | R6 is only partly fixed. Added now has two bullets, but a blank line still splits the Fixed list (CHANGELOG.md:45). The new Fixed bullet "**tui**: show bounded normalized tool, message and plan activity" repeats the Added bullet at :12 for this same unreleased PRD. Fold it into Added and remove the blank line | CHANGELOG.md:44 | 20 | ALICE, BOB |
| R7 | [1/3] | 🟠 | A single valid Codex record can crash the supervisor, which breaks the "malformed input degrades to `raw.unknown`" rule. Any JSON string holding a lone surrogate escape (a `thread_id`, agent text, error message) passes `CodexDriver.decode` unsanitized. `NormalizedEventWriter.write` then raises `UnicodeEncodeError` at `.encode("utf-8")`. That write sits outside the decoder's `try`, so the error escapes `RawFirstDecoder.feed`. `_stream` then SIGKILLs the child, and `_attempt` re-raises. Confirmed with a one-line repro: `{"type":"item.completed","item":{"id":"m","type":"agent_message","text":"\ud800"}}` gives `UnicodeEncodeError: surrogates not allowed`. The state layer already rejects lone surrogates; the event path does not. | src/ovcaq/events/tail.py:143 | B | BLAKE |
| R8 | [1/3] | 🟠 | The exact version pin rejects the Codex CLI installed on this machine, which blocks the "PRD 00010 can run the first real Codex smoke" criterion. `probe()` requires `codex-cli 0.160.0` exactly, but the installed binary reports `codex-cli 0.160.1`. Running the real probe returns `DriverHealth(healthy=False, detail='codex: observed 0.160.1; pinned 0.160.0; refresh the Codex fixture contract')`, and `ovcaq run --agent codex` refuses before launch. Installed `codex exec --help` flags still match the captured help, so only the pin fails. Any patch release breaks the adapter. | src/ovcaq/drivers/codex.py:200 | A | BLAKE |
| R9 | [1/3] | 🟡 | Simplify: `version[10:]` behind `version.startswith("codex-cli ")` is a magic slice of the prefix length. Use `version.removeprefix("codex-cli ")` and compare it to `version` to choose between the "observed" and "missing" detail. Behavior stays the same | src/ovcaq/drivers/codex.py:202 | 24 | ALICE |
| R10 | [1/3] | 🟡 | `activity_panel` prints all kept activity (up to 256 items) oldest first, after the lanes. In a busy session the newest tool call sits at the bottom of a frame that can pass 500 lines, below what the terminal shows. Plain mode reprints that whole frame on every change. | src/ovcaq/tui/panels.py:92 | 26 | BOB |
| R11 | [1/3] | 🟡 | The fixture docs are stale after the rework. The family table has no `lanes-matched.jsonl` row. Line 45 still says edge tests build matched variants in place, but that in-place rewrite was removed. Lines 72-73 still say activity panels render lanes only. docs/driver-protocol.md:217 also names only `lanes.jsonl`. | tests/fixtures/README.md:45 | general | BOB |
| R12 | [1/3] | 🟡 | The root cause of R10 is still there for three of the four failure fixtures. `test_fixture_error_then_identical_failure_has_one_terminal_and_rate_start` still builds its expected class by calling `classify_failure(detail)`. If the rate-limited, authentication or permission fixture fell back to unknown, the test would still pass. Only connectivity got an independent expected value. | tests/drivers/test_codex_decode_terminals.py:120 | 23 | BOB |
| R13 | [1/3] | 🟡 | Six new test files are named after the review loop (`test_codex_rework_*`, `test_rework_*`), not after the behavior they guard. `test_codex_rework_placement.py` also re-tests text, reasoning, error and plan items, sanitizing, and rejection of malformed items, which tests/drivers/test_codex_decode.py:80-231 already covers through `decode`. It also pins which module holds the helper. | tests/drivers/test_codex_rework_placement.py:1 | general | BOB |
| R14 | [1/3] | 🟡 | Simplify: `"; ".join(reason for reason in (gap, X) if reason)` appears three times (here, at :102, and at src/ovcaq/drivers/codex.py:312). In `turn_usage`, collect the reasons in a list and return `"; ".join(reasons) or None`. In `_usage_observations`, use `gap = f"{gap}; Conflicting thread identity" if gap else "Conflicting thread identity"`. | src/ovcaq/drivers/codex_events.py:93 | 23 | BOB |
| R15 | [1/3] | 🟡 | Simplify: `_bind_observations` hides a conditional dict merge (`dict(...) | {...} if A and B else payload`) inside a `replace()` keyword, inside a generator. Reading it right depends on operator precedence. A plain loop that sets `payload` with one `if` and then calls `replace` does the same and is easy to read. | src/ovcaq/events/tail.py:153 | 20 | BOB |
| R16 | [1/3] | 🟡 | Simplify: `assert_prd_completion` recomputes `handoff_revision`, which its caller already computed (:385), and uses it only in the done branch. Pass it in, or write `before["revision"] + 1` inline there. | tests/drivers/test_codex_fake.py:323 | 22 | BOB |
| R17 | [1/3] | ⚪ | No test pins the 16 KiB per-stream capture cap, which was the core of R3. If the slice at codex.py:76 were removed (unbounded capture), every probe test would still pass, because `_probe_failure` truncates the final detail to 16 KiB anyway (tests/drivers/test_codex_rework_probe.py:140 checks only `len(detail)`). Add a check that a large stdout on the version probe is captured to at most 16 KiB, for example by making the helper's returned buffers observable | src/ovcaq/drivers/codex.py:76 | 24 | ALICE |
| R18 | [1/3] | ⚪ | The driver accepts options the PRD never asks for. `sandbox` and `approval` can only equal their fixed defaults, so they do nothing. `allow_explicit_model` lets a launch skip the tier map, which the PRD says the model resolves through. | src/ovcaq/drivers/codex.py:118 | A | BLAKE |
| R19 | [1/3] | ⚪ | On the supervisor path the model is resolved through the tier map twice. `resolve_phase_route` hands over a resolved model value, and `build_launch` maps it through `settings.tiers` again, keys first. A value that also names another tier, such as `{default="o3", o3="o3-pro"}`, launches the wrong model. The Claude edge maps values back to keys first; Codex has no such step. | src/ovcaq/drivers/codex.py:138 | A | BLAKE |
| R20 | [1/3] | ⚪ | Failure classification matches bare status codes anywhere in the message. `\b401\b`, `\b403\b`, `\b502\b` and similar fire on unrelated numbers ("processed 401 files"), and authentication wins by precedence, so the wrong retry budget may be used. Suspected; not reproduced. | src/ovcaq/drivers/codex_events.py:299 | B | BLAKE |
| R21 | [1/3] | ⚪ | The full suite passes but warns twice: `PytestWarning: (rm_rf) error removing …/garbage-… Directory not empty`. Suspected cause: a process from a test still writes into tmp after teardown, possibly a fake descendant. Not traced. | N/A | C | BLAKE |
| R22 | [1/3] | ⚪ | The launch health gate now runs for every adapter, but test_rework_health.py configures only Codex. The decision gate asked for both adapters, and no test shows `ovcaq run --agent claude` stopping before spawn when `ClaudeDriver.probe` fails. | tests/runtime/test_rework_health.py:86 | 26 | BOB |
| R23 | [1/3] | ⚪ | `ClaudeDriver.probe` now gates every launch, but it calls `shutil.which(command)` with the supervisor's PATH, not the PATH from the configured environment overlay that the agent spawn uses. A Claude command found only through an overlay PATH may now be rejected. Suspected, not confirmed. | src/ovcaq/drivers/claude.py:81 | 26 | BOB |
| R24 | [1/3] | ⚪ | Cannot statically verify: the full test suite passes at the review HEAD (the gate reused 5591 passed at b95bcaf). | N/A | general | BOB |
| R25 | [1/3] | ⚪ | The probe now reads from pipes until end-of-file, so a wrapper's background child that keeps stdout open turns a healthy probe into a 5 s timeout. | src/ovcaq/drivers/codex.py:66 | 24 | BOB |
| R26 | [1/3] | ⚪ | An existing test, `test_fake_build_review_done_drain_capability_failure_and_independent_retry`, is 52 lines. This diff does not touch it: test_supervisor.py has no net change against the PRD base. | tests/runtime/test_supervisor.py:700 | general | BOB |
| R27 | [1/3] | 🟡 | Dead fallback: `payload.get("detail", payload.get("input"))` reads an `input` key that no driver emits (searching src for `"input"` finds only this line). The Claude case in tests/tui/test_rework_activity.py:57 builds a made-up `input` payload just to reach it. Drop the `input` fallback and make the Claude test use the real `tool.started` shape (`tool_id`, `name`, metadata) | src/ovcaq/tui/model.py:592 | 26 | ALICE |
| R28 | [1/3] | 🟡 | 1 touched test(s) pass against the pre-change code: test_command_backed_workflow_handoffs | tests/drivers/test_codex_fake.py | general | mech-check |
| R29 | [1/3] | 🟡 | 1 touched test(s) pass against the pre-change code: test_configured_prompts_remain_literal_phase_overrides | tests/drivers/test_codex_prompt.py | general | mech-check |
| R30 | [1/3] | 🟡 | 3 touched test(s) pass against the pre-change code: test_explicit_aware_rate_reset_accepts_punctuation_with_six_hour_ceiling | tests/drivers/test_codex_rework_decode.py | general | mech-check |
| R31 | [1/3] | 🟡 | 2 touched test(s) pass against the pre-change code: test_probe_rejects_version_aliases_that_are_not_exact_reviewed_evidence | tests/drivers/test_codex_rework_probe.py | general | mech-check |
| R32 | [1/3] | 🟡 | 1 touched test(s) pass against the pre-change code: test_repeated_native_thread_succeeds_with_terminal_evidence | tests/runtime/test_rework_thread_conflict.py | general | mech-check |
| R33 | [1/3] | 🟡 | 2 touched test(s) pass against the pre-change code: test_builtin_fake_command_handoffs_drain_and_retain_completed_results | tests/runtime/test_supervisor_adapters.py | general | mech-check |
| R34 | [1/3] | 🟡 | 5 touched test(s) pass against the pre-change code: test_fake_supervisor_evidence_drives_panels | tests/tui/test_codex_projection.py | general | mech-check |

### Auto-dismissed (ledger)


- [BLAKE] 🟠 (Suspected, strong evidence) The rate-limit reset parser only reads made-up phrasings, so real Codex usage limits will always halt instead of wait. `failure_reset` parses only `reset at <ISO-8601>` and `retry after N seconds`. The installed 0.160.1 binary contains the templates `hit your usage limit… Try again at <time>` and `try again in <N>(s|ms|seconds)`, and no `retry after N seconds` usage text. Real messages therefore never produce a reset deadline, and the shared policy HALTs on any rate limit without one. The "with reset" tests pass only because the fake and fixtures use the made-up phrase. | File: src/ovcaq/drivers/codex_events.py:332 — Requirements ambiguity: accepted design lines 187-192 permits explicit aware ISO or retry-after seconds only and rejects ambiguous local clock prose. Native formatter expansion needs a contract decision; retain unknown deadlines without guessing timezone.
- [BLAKE] 🟡 Every JSONL fixture family is schema-synthetic, including healthy, tool-active and lanes. The PRD allows synthesis only where live capture is impractical, naming rate-limited and permission-failed. Provenance says "No safe controlled existing JSONL transcript was supplied", so decoding of "actual" items is checked only against the implementer's reading of the Rust source. Risk is reduced: the installed binary does contain `cache_write_input_tokens`, `reasoning_output_tokens`, `receiver_thread_ids` and `agents_states`. | File: tests/fixtures/codex/v1/provenance.json:170 — Requirements ambiguity: PRD prefers live capture when practical; accepted design lines 65-76 authorizes honestly labeled synthesis when a safe existing transcript is unavailable. Provenance confirms none supplied. Decide capture policy at batch end; do not fabricate capture provenance or launch real smoke.
- [BLAKE] 🟡 Claude model-family names leak in as the provider-neutral default tiers, so Codex fails unless its tiers are named after Claude models. `DEFAULT_PHASE_TIERS = {"build": "sonnet", "review": "opus", "done": "sonnet"}` feeds `supervisor_settings`. A Codex config with tiers like `{standard, deep}` and no per-phase override fails `resolve_phase_route` with `ConfigurationError: Unknown agent tier: sonnet` (confirmed). Every Codex supervisor test works around this with `tiers = { sonnet = ..., opus = ... }`. The neutrality scan misses it because it leaves out `drivers/__init__.py`, and `config.py` imports the names indirectly. | File: src/ovcaq/drivers/__init__.py:18 — Requirements ambiguity: accepted design reuses shared config and logical tier mappings. Renaming shared defaults changes configuration behavior; decide neutral naming and migration scope at batch end.

## Consolidation Notes

Consolidated with the installed script; corrected one false merge: Alice's dead input-payload fallback is distinct from missing message details and remains its own row. Alice's malformed `[⚪ ALICE] placeholder removed` is explicitly an output artifact with no finding, retained verbatim below and excluded from counts. Seven mechanical replay findings are appended; they are computed facts, not automatically defects. No findings discarded or classified by the decision gate yet.

## Verification-check queue

Bob's named full-suite check is queued at checks-2.json; the coordinator already verified the same suite at HEAD using reporting flags. The Claude PATH item is not queued: its templated live workflow launch requires setup and changes workflow state, so it fails the project-verification command-shape rule. It remains an ordinary low finding for decision-gate handling. No queue entry is silently lost.

## Decision Gate Resolved (2026-10-07)

Operator skip of optional Carl is recorded above; required reviewers are reused. Schema, 30/30 counts, complete R/B/D rubrics, immutable receipts, successful raw reviewer results and unchanged implementation provenance pass the host boundary check.

Unattended cycle/cap is 2/2. R7 remains a confirmed HIGH: writing a decoded lone-surrogate observation raises UnicodeEncodeError. R8 remains a HIGH deployment-readiness finding; the exact fixture pin is deliberate, so expanding it requires a contract decision. Neither has been fixed or dismissed. The cap-out path defers R1-R23 and R25-R34 (33 rows) verbatim to state.deferred_decisions and the settled ledger. All seven replay rows are retained: passing at base alone does not establish a defect, so their intent remains for batch-end adjudication. No repair, new task, review cycle or cap increase runs.

R2 helper ordering reproduces with a generated synthetic key, but Observation sanitizes the reassembled key again: no synthetic key survives into normalized payloads in this probe. Preserve the helper concern; the reported normalized credential-persistence claim did not reproduce and does not establish a security-critical shipping leak. No real credential was used. R24 is verified by the existing 5591-pass full-suite record at reviewed HEAD. Evidence: reports/00009-cycle2-decision-probes.json.

Outcome: cap_deferred, ready for the canonical review-to-done handoff. This is completion with deferrals, not a clean review. Original findings, raw rubric verdicts and receipts remain unchanged.

## Alice

Provider: anthropic; observed model: claude-opus-5-5; requested model: opus; effort: xhigh; session: 209b026d-fb4c-4ddb-b336-c0c212b20f0f. Immutable raw source: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/alice-output-00009-c2-20261006-4947d471271e435e86e6dd277b27f47f.jsonl.

Prior cycle check: R1-R5, R7, R9-R14, R17-R20 and R24-R26 are fixed in the code. R16 and R21 are fixed, but each fix brought a new defect (listed below). R6 is only partly fixed. All touched test files pass (277 passed). `ruff check` and `mypy src/ovcaq` are clean.

[ALICE] 🟡 The fix for R21 (interrupted/shutdown/not_found lanes) also catches lanes that already finished. The "started" set at codex.py:372 is built from every lane identity, including ones marked done. So a lane that completed and is later reported as `shutdown` (for example by a `close_agent` or `wait` call) emits `lane.failed`, and the TUI accepts the change from completed to failed. Confirmed by running it: running → completed → shutdown gives `['tool.completed', 'lane.failed']`. Fix: pass only lanes that are not done (`{lane for (cat, lane), done in self._identities.items() if cat == "lane" and not done}`), make `started_lanes` a required parameter (codex_events.py:205, its only caller always passes it), and add a test for completed-then-shutdown | File: src/ovcaq/drivers/codex.py:372 | Task: 23
[ALICE] 🟡 `bounded_detail` redacts credentials first and strips terminal controls second. A key split by an escape sequence therefore survives redaction and is joined back together. Confirmed: `bounded_detail("token sk-abc\x1b[0mdefghijklmnopqrstuvwxyz0123456789ABCDEF")` returns the full `sk-abcdef…` key unredacted, and that text lands in persisted `session.failed`, `rate_limit.started` and lane payloads. The existing `_bounded` (src/ovcaq/supervisor_cli.py:77) strips first and then sanitizes. Fix: swap the order, add a regression test, and consider sharing one helper instead of a second copy of the ANSI regex | File: src/ovcaq/drivers/codex_events.py:57 | Task: 23
[ALICE] 🟡 The R16 activity view drops the detail on error and warning messages. `_observe_activity` reads only `payload["text"]`, but the Codex provisional top-level `error` (codex.py:278) and Claude `rate_limit_warning` (claude_events.py:143) carry their message in `detail`, so they render as a bare "error" or "rate_limit_warning". These payloads and Codex `turn` messages also have no `message_id`, so they share the key `("message", "")`. The next `turn` line then replaces the error line. The test at tests/tui/test_rework_activity.py:86 uses `text` for kind `error`, so it never exercises the real provisional shape. Confirmed by code reading. Fix: fall back to `detail` when `text` is missing, give message_id-less entries a distinct key (for example kind plus sequence), and test the real provisional-error payload | File: src/ovcaq/tui/model.py:575 | Task: 26
[ALICE] 🟡 "Selected model is at capacity" (upstream ServerOverloaded, a transient overload) is now classified as `rate_limit`. That message never carries a reset time, so decision.py:197-213 halts the batch on the first occurrence. Before this rework it was `unknown` and got one retry. The design taxonomy puts "server unavailable/503" under connectivity, which waits and retries with a bound. Move `model is at capacity` to the connectivity pattern and update the expectation at tests/drivers/test_codex_rework_decode.py:94 | File: src/ovcaq/drivers/codex_events.py:309 | Task: 23
[ALICE] 🟡 Simplify `_report_runtime_error`. It is named as a reporter, but it now raises in 2 of its 3 branches. The third branch returns an `Exception` that the only caller ignores, and the caller then does a bare `raise` (supervisor_cli.py:193-194). Make it `-> None`, drop `return error` (fall through), or rename it `_raise_runtime_error`. Behavior stays the same | File: src/ovcaq/supervisor_cli.py:144 | Task: 26
[ALICE] 🟡 Dead fallback: `payload.get("detail", payload.get("input"))` reads an `input` key that no driver emits (searching src for `"input"` finds only this line). The Claude case in tests/tui/test_rework_activity.py:57 builds a made-up `input` payload just to reach it. Drop the `input` fallback and make the Claude test use the real `tool.started` shape (`tool_id`, `name`, metadata) | File: src/ovcaq/tui/model.py:592 | Task: 26
[ALICE] 🟡 Simplify: `version[10:]` behind `version.startswith("codex-cli ")` is a magic slice of the prefix length. Use `version.removeprefix("codex-cli ")` and compare it to `version` to choose between the "observed" and "missing" detail. Behavior stays the same | File: src/ovcaq/drivers/codex.py:202 | Task: 24
[⚪ ALICE] placeholder removed
[ALICE] ⚪ No test pins the 16 KiB per-stream capture cap, which was the core of R3. If the slice at codex.py:76 were removed (unbounded capture), every probe test would still pass, because `_probe_failure` truncates the final detail to 16 KiB anyway (tests/drivers/test_codex_rework_probe.py:140 checks only `len(detail)`). Add a check that a large stdout on the version probe is captured to at most 16 KiB, for example by making the helper's returned buffers observable | File: src/ovcaq/drivers/codex.py:76 | Task: 24
[ALICE] ⚪ R6 is only partly fixed. Added now has two bullets, but a blank line still splits the Fixed list (CHANGELOG.md:45). The new Fixed bullet "**tui**: show bounded normalized tool, message and plan activity" repeats the Added bullet at :12 for this same unreleased PRD. Fold it into Added and remove the blank line | File: CHANGELOG.md:44 | Task: 20

R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

**Partly done.** The review is complete: 7 Medium and 2 Low findings, 3 rubric fails. Note: the line `[⚪ ALICE] placeholder removed` above is an output error with no finding behind it. It should be dropped before parsing; the Low findings are the two lines after it.

Next: You: feed these findings into the cycle 2 decision gate.

## Blake

Provider: anthropic; observed model: claude-opus-5-5; requested model: opus; effort: xhigh; session: 49754595-921c-499c-9c57-e63f28215ceb. Immutable raw source: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/blake-output-00009-c2-20261006-1f01799e4fa1474d8c7eb513fade9385.jsonl.

[BLAKE] 🟠 A single valid Codex record can crash the supervisor, which breaks the "malformed input degrades to `raw.unknown`" rule. Any JSON string holding a lone surrogate escape (a `thread_id`, agent text, error message) passes `CodexDriver.decode` unsanitized. `NormalizedEventWriter.write` then raises `UnicodeEncodeError` at `.encode("utf-8")`. That write sits outside the decoder's `try`, so the error escapes `RawFirstDecoder.feed`. `_stream` then SIGKILLs the child, and `_attempt` re-raises. Confirmed with a one-line repro: `{"type":"item.completed","item":{"id":"m","type":"agent_message","text":"\ud800"}}` gives `UnicodeEncodeError: surrogates not allowed`. The state layer already rejects lone surrogates; the event path does not. | File: src/ovcaq/events/tail.py:143 | Task: B
[BLAKE] 🟠 The exact version pin rejects the Codex CLI installed on this machine, which blocks the "PRD 00010 can run the first real Codex smoke" criterion. `probe()` requires `codex-cli 0.160.0` exactly, but the installed binary reports `codex-cli 0.160.1`. Running the real probe returns `DriverHealth(healthy=False, detail='codex: observed 0.160.1; pinned 0.160.0; refresh the Codex fixture contract')`, and `ovcaq run --agent codex` refuses before launch. Installed `codex exec --help` flags still match the captured help, so only the pin fails. Any patch release breaks the adapter. | File: src/ovcaq/drivers/codex.py:200 | Task: A
[BLAKE] 🟠 (Suspected, strong evidence) The rate-limit reset parser only reads made-up phrasings, so real Codex usage limits will always halt instead of wait. `failure_reset` parses only `reset at <ISO-8601>` and `retry after N seconds`. The installed 0.160.1 binary contains the templates `hit your usage limit… Try again at <time>` and `try again in <N>(s|ms|seconds)`, and no `retry after N seconds` usage text. Real messages therefore never produce a reset deadline, and the shared policy HALTs on any rate limit without one. The "with reset" tests pass only because the fake and fixtures use the made-up phrase. | File: src/ovcaq/drivers/codex_events.py:332 | Task: B
[BLAKE] 🟡 Every JSONL fixture family is schema-synthetic, including healthy, tool-active and lanes. The PRD allows synthesis only where live capture is impractical, naming rate-limited and permission-failed. Provenance says "No safe controlled existing JSONL transcript was supplied", so decoding of "actual" items is checked only against the implementer's reading of the Rust source. Risk is reduced: the installed binary does contain `cache_write_input_tokens`, `reasoning_output_tokens`, `receiver_thread_ids` and `agents_states`. | File: tests/fixtures/codex/v1/provenance.json:170 | Task: A
[BLAKE] 🟡 Claude model-family names leak in as the provider-neutral default tiers, so Codex fails unless its tiers are named after Claude models. `DEFAULT_PHASE_TIERS = {"build": "sonnet", "review": "opus", "done": "sonnet"}` feeds `supervisor_settings`. A Codex config with tiers like `{standard, deep}` and no per-phase override fails `resolve_phase_route` with `ConfigurationError: Unknown agent tier: sonnet` (confirmed). Every Codex supervisor test works around this with `tiers = { sonnet = ..., opus = ... }`. The neutrality scan misses it because it leaves out `drivers/__init__.py`, and `config.py` imports the names indirectly. | File: src/ovcaq/drivers/__init__.py:18 | Task: C
[BLAKE] ⚪ The driver accepts options the PRD never asks for. `sandbox` and `approval` can only equal their fixed defaults, so they do nothing. `allow_explicit_model` lets a launch skip the tier map, which the PRD says the model resolves through. | File: src/ovcaq/drivers/codex.py:118 | Task: A
[BLAKE] ⚪ On the supervisor path the model is resolved through the tier map twice. `resolve_phase_route` hands over a resolved model value, and `build_launch` maps it through `settings.tiers` again, keys first. A value that also names another tier, such as `{default="o3", o3="o3-pro"}`, launches the wrong model. The Claude edge maps values back to keys first; Codex has no such step. | File: src/ovcaq/drivers/codex.py:138 | Task: A
[BLAKE] ⚪ Failure classification matches bare status codes anywhere in the message. `\b401\b`, `\b403\b`, `\b502\b` and similar fire on unrelated numbers ("processed 401 files"), and authentication wins by precedence, so the wrong retry budget may be used. Suspected; not reproduced. | File: src/ovcaq/drivers/codex_events.py:299 | Task: B
[BLAKE] ⚪ The full suite passes but warns twice: `PytestWarning: (rm_rf) error removing …/garbage-… Directory not empty`. Suspected cause: a process from a test still writes into tmp after teardown, possibly a fake descendant. Not traced. | File: N/A | Task: C

Evidence:
- Full suite: `5591 passed, 2 warnings in 217.99s`. Codex-scoped subset: `1492 passed`.
- Searching `runtime/`, `tui/`, `events/`, `state/` and `workflow/` finds no Codex or Claude strings, so the supervisor has zero Codex branches.
- Fake build/review/done drains run through the shared `Supervisor`, for both Claude and Codex (`tests/runtime/test_supervisor_adapters.py:164`).
- Out of scope respected: `provision/codex.py` is unchanged since the skeleton, and no test calls the real `codex` binary.

B1: fail
B2: pass
B3: pass
B4: pass
B5: fail
B6: pass
B7: fail
B8: pass
B9: pass
B10: fail
B11: fail
B12: pass
B13: pass
B14: pass
B15: fail
B16: fail
B17: pass
B18: pass
B19: pass

## Bob

Provider: anthropic; observed model: claude-opus-5-5; requested model: opus; effort: xhigh; session: 49c243a4-aff8-49d3-874a-08b42128545a. Immutable raw source: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00009-c2-20261006-4bf34f58c9104aaab1ca117918bc560d.jsonl.

**Prior cycle status (BOB):** These findings are fixed in code: R1, R2, R3, R4, R5, R7, R9, R12, R13, R14, R17, R18, R19, R20, R24, R25 and R26. R26 is a net-zero diff of tests/runtime/test_supervisor.py against the PRD base, checked with a control path. Four were fixed only in part or caused a new problem: R21's fix lets a finished lane flip to failed (finding 1), R11's capacity mapping halts the batch (finding 2), R16's activity view has gaps (findings 3 and 4), and R10 got a fixture oracle for connectivity only (finding 7). R6 is mostly fixed (finding 12). The settled items (R8, R15, R22, R23, R27) were not re-raised.

[BOB] 🟡 A finished receiver lane can flip to failed. The R21 fix passes every remembered lane ID to `item_lanes`, including lanes already marked done. So a receiver that completed and is later reported `shutdown`, `interrupted` or `not_found` (for example by a later `close_agent` or `wait` record) emits `lane.failed`. `_observe_lane` (src/ovcaq/tui/model.py:616) then overwrites "completed" with "failed". The design says a completed receiver completes its lane, and the new test only covers running then interrupted. | File: src/ovcaq/drivers/codex.py:372 | Task: 23
[BOB] 🟡 The R11 rework maps "Selected model is at capacity" to rate_limit. That text has no reset, so `failure_reset` returns None and the decision policy halts the whole batch at once (src/ovcaq/runtime/decision.py:211). Before this change the text was unknown and got one retry. A short-lived server overload should wait and retry like connectivity (3 tries, 1800 s), not stop the run. | File: src/ovcaq/drivers/codex_events.py:309 | Task: 23
[BOB] 🟡 The Activity panel drops the detail of messages that have no `message_id`. `_observe_activity` reads only `text`, but the Codex top-level `error` activity and Claude `rate_limit_warning` carry `detail`, so they show as a bare "error" or "rate_limit_warning" with no message. All such messages, including every Codex `turn` marker, share the key ("message", "") and overwrite each other. No test covers a message without an ID. | File: src/ovcaq/tui/model.py:575 | Task: 26
[BOB] 🟡 `activity_panel` prints all kept activity (up to 256 items) oldest first, after the lanes. In a busy session the newest tool call sits at the bottom of a frame that can pass 500 lines, below what the terminal shows. Plain mode reprints that whole frame on every change. | File: src/ovcaq/tui/panels.py:92 | Task: 26
[BOB] 🟡 The fixture docs are stale after the rework. The family table has no `lanes-matched.jsonl` row. Line 45 still says edge tests build matched variants in place, but that in-place rewrite was removed. Lines 72-73 still say activity panels render lanes only. docs/driver-protocol.md:217 also names only `lanes.jsonl`. | File: tests/fixtures/README.md:45 | Task: general
[BOB] 🟡 `bounded_detail` redacts secrets before it strips terminal controls. `_LIKELY_SECRET` needs 20 token characters after `sk-`, so a token split by an ANSI or NUL byte (`sk-abc\x1b[0mdef...`) is not redacted, and the strip then joins it back whole. Confirmed by reading the regex. A real trigger is unlikely. The test puts the control bytes after the token, so it cannot catch this. | File: src/ovcaq/drivers/codex_events.py:57 | Task: 23
[BOB] 🟡 The root cause of R10 is still there for three of the four failure fixtures. `test_fixture_error_then_identical_failure_has_one_terminal_and_rate_start` still builds its expected class by calling `classify_failure(detail)`. If the rate-limited, authentication or permission fixture fell back to unknown, the test would still pass. Only connectivity got an independent expected value. | File: tests/drivers/test_codex_decode_terminals.py:120 | Task: 23
[BOB] 🟡 Six new test files are named after the review loop (`test_codex_rework_*`, `test_rework_*`), not after the behavior they guard. `test_codex_rework_placement.py` also re-tests text, reasoning, error and plan items, sanitizing, and rejection of malformed items, which tests/drivers/test_codex_decode.py:80-231 already covers through `decode`. It also pins which module holds the helper. | File: tests/drivers/test_codex_rework_placement.py:1 | Task: general
[BOB] 🟡 Simplify: `"; ".join(reason for reason in (gap, X) if reason)` appears three times (here, at :102, and at src/ovcaq/drivers/codex.py:312). In `turn_usage`, collect the reasons in a list and return `"; ".join(reasons) or None`. In `_usage_observations`, use `gap = f"{gap}; Conflicting thread identity" if gap else "Conflicting thread identity"`. | File: src/ovcaq/drivers/codex_events.py:93 | Task: 23
[BOB] 🟡 Simplify: `_report_runtime_error` is typed `-> Exception` and returns the error in one branch, but its only caller ignores the result and re-raises. It raises in the other two branches, and its name hides that. Make it `-> None` with a bare `return`, or rename it `_raise_runtime_error`. | File: src/ovcaq/supervisor_cli.py:144 | Task: 26
[BOB] 🟡 Simplify: `_bind_observations` hides a conditional dict merge (`dict(...) | {...} if A and B else payload`) inside a `replace()` keyword, inside a generator. Reading it right depends on operator precedence. A plain loop that sets `payload` with one `if` and then calls `replace` does the same and is easy to read. | File: src/ovcaq/events/tail.py:153 | Task: 20
[BOB] ⚪ The CHANGELOG Fixed lines 43-44 repeat the new Added lines 11-12 (launch health gate, activity display). Both are new behavior, and no version has been released. A blank line (45) still splits the Fixed list, as R6 noted. | File: CHANGELOG.md:43 | Task: 20
[BOB] ⚪ The launch health gate now runs for every adapter, but test_rework_health.py configures only Codex. The decision gate asked for both adapters, and no test shows `ovcaq run --agent claude` stopping before spawn when `ClaudeDriver.probe` fails. | File: tests/runtime/test_rework_health.py:86 | Task: 26
[BOB] 🟡 Simplify: `assert_prd_completion` recomputes `handoff_revision`, which its caller already computed (:385), and uses it only in the done branch. Pass it in, or write `before["revision"] + 1` inline there. | File: tests/drivers/test_codex_fake.py:323 | Task: 22
[BOB] ⚪ `ClaudeDriver.probe` now gates every launch, but it calls `shutil.which(command)` with the supervisor's PATH, not the PATH from the configured environment overlay that the agent spawn uses. A Claude command found only through an overlay PATH may now be rejected. Suspected, not confirmed. | File: src/ovcaq/drivers/claude.py:81 | Task: 26
[BOB] ⚪ Cannot statically verify: the full test suite passes at the review HEAD (the gate reused 5591 passed at b95bcaf). | File: N/A | Task: general
[BOB] ⚪ The probe now reads from pipes until end-of-file, so a wrapper's background child that keeps stdout open turns a healthy probe into a 5 s timeout. | File: src/ovcaq/drivers/codex.py:66 | Task: 24
[BOB] ⚪ An existing test, `test_fake_build_review_done_drain_capability_failure_and_independent_retry`, is 52 lines. This diff does not touch it: test_supervisor.py has no net change against the PRD base. | File: tests/runtime/test_supervisor.py:700 | Task: general

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

FIX:
- A finished receiver lane flips to failed on a later shutdown/interrupted/not_found — src/ovcaq/drivers/codex.py:372 — pass only lanes still running: `{lane_id for (category, lane_id), done in self._identities.items() if category == "lane" and not done}`. Make `started_lanes` a required `set[str]` (one caller) and drop the `is not None` guard at codex_events.py:231. Add a test: running, then completed, then shutdown gives no `lane.failed`.
- Capacity text halts the batch as a rate limit with no reset — src/ovcaq/drivers/codex_events.py:309 — move `model is at capacity` into the CONNECTIVITY pattern and change its test case at tests/drivers/test_codex_rework_decode.py:94 to "connectivity".
- Activity drops `detail` and merges messages without an ID — src/ovcaq/tui/model.py:575 — use `detail = payload.get("text", payload.get("detail"))`, skip kind `turn` (or key messages without an ID by kind), and add a test with a Codex top-level error and a Claude `rate_limit_warning`.
- Activity panel shows up to 256 items oldest first — src/ovcaq/tui/panels.py:92 — render only the newest items, newest first, e.g. `for item in reversed(view.activity[-20:])`, and pin that order in tests/tui/test_rework_activity.py.
- Stale fixture docs — tests/fixtures/README.md:45 — add a `lanes-matched.jsonl` row to the table, replace the "edge tests construct matched variants" sentence with the checked-in fixture, change lines 72-73 to say panels show tool/message/plan activity, and mention `lanes-matched.jsonl` at docs/driver-protocol.md:217.
- Redaction runs before control stripping — src/ovcaq/drivers/codex_events.py:57 — swap the order: `sanitize_text(re.sub(<pattern>, "", detail))[:4096]`. Add a test with `\x1b[0m` inside an `sk-` token.
- Expected class is computed by the code under test — tests/drivers/test_codex_decode_terminals.py:120 — parametrize with literal pairs (`rate-limited`/`rate_limit`, `authentication-failed`/`authentication`, `connectivity-failed`/`connectivity`, `permission-failed`/`permission`) and assert against those values.
- Test files named after the review loop, plus a duplicate placement file — tests/drivers/test_codex_rework_placement.py:1 — delete the placement file after moving its 4095/4096/4097 boundary case into tests/drivers/test_codex_decode.py. Rename the rest to domain names, e.g. test_codex_decode_hardening.py, test_codex_probe_capture.py, runtime/test_launch_health_gate.py, runtime/test_thread_identity.py, tui/test_activity_panel.py.
- Gap-join idiom appears three times — src/ovcaq/drivers/codex_events.py:93 — use a `reasons` list in `turn_usage` and a one-line f-string ternary at codex.py:312.
- Unused return value and misleading helper name — src/ovcaq/supervisor_cli.py:144 — change the return type to `-> None` and `return error` to `return`, or rename the helper `_raise_runtime_error`.
- Hard-to-read binding generator — src/ovcaq/events/tail.py:153 — use an explicit loop that builds `payload` with one `if`, then `replace(...)`.
- CHANGELOG Fixed entries repeat Added entries — CHANGELOG.md:43 — delete lines 43-44 (fold "rejects unhealthy adapters before launch" into line 11 if wanted) and the blank line 45.
- No Claude case for the launch health gate — tests/runtime/test_rework_health.py:86 — add a parametrized Claude case with a missing command. Assert a nonzero exit, a JSON error naming the command, and no spawn marker.
- `handoff_revision` computed twice — tests/drivers/test_codex_fake.py:323 — pass `handoff_revision` in from `assert_workflow_handoff`, or inline `before["revision"] + 1` in the done branch.
VERIFY:
- Claude probe PATH differs from the spawn PATH — configure `[agents.claude] command = ["claude-fixture"]` and `environment = { PATH = "<tmp>/bin" }`, with the fake script only in `<tmp>/bin`, then run `uv run python -m ovcaq --root <tmp> --json run --no-tui --agent claude`. If it fails with "Command is missing or not executable", pass the overlay PATH to `shutil.which(command, path=...)`.
- Full suite at the review HEAD — run `mise exec -- uv run pytest` and confirm 0 failed and 0 skipped.
KNOWN:
- A probe pipe held open by a descendant turns into a 5 s timeout — descendant ownership during the probe belongs to the settled R27 deferral (probe process-group policy decided at batch end), and the timeout path still fails closed.
- 52-line function at tests/runtime/test_supervisor.py:700 — this cycle left the function unchanged (net-zero diff against the PRD base), so splitting it is outside this rework; listed so it is not silently ignored.

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

Verdict: 34 findings
Tests: 5591 passed, 0 failed, 0 skipped (suite run this cycle at a5064af9d35f779a0032bce77154909a089c6a00; all six gates pass)
