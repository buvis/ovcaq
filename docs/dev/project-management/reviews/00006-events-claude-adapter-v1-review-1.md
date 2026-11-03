---
prd: dev/local/prds/wip/00006-events-claude-adapter-v1.md
review: 1
date: 2026-09-26
head_sha: 24fcec3bed6a41044c3d149d1f42bd678864e7e0
reviewers: alice,blake,bob
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/tmp/bob-output-00006-c1-20260926-1510.txt.receipt.json
---

# PRD 00006 — review cycle 1

Diff range: `666776af6ecb3baebb70e3eeb1c1b828fe64d135..24fcec3bed6a41044c3d149d1f42bd678864e7e0`
codex_rung_guard: fired (10 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude

Host substitution: Alice and Blake ran in isolated native Codex `gpt-5.6-sol` contexts (logical sonnet). Bob ran fresh through the authorized autocodex helper on external Claude, logical opus; raw init/message evidence identifies `claude-opus-5-5`. Bob supplies the independent provider doubt/de-slop voice. Native Fable is unavailable in this host; no Eve dispatch or Eve result is claimed, and Fable was not mapped to Astra. The source gate's fallback suffix records the authorized non-Codex Bob substitution.
Dispatch evidence: native tasks `/root/alice_review`, `/root/blake_review`; Bob CLI dispatch `94af96e1`; Carl CLI dispatch `19af5fa8`.
Carl: unavailable this cycle, exit 3: `refusing nested dispatch (already inside a CLI agent)`. No backend ran, no guard was removed, no permanent-unavailability batch latch was set, and no stale output was consumed.
Pack: unavailable; engram reported this repository is not gita-registered. Optional context omitted.
Scope: full PRD range; gather-context's current-branch diff was corrected to committed work_start_sha, 216477 bytes.
Accepted source-plan SHA-256 verified: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
All launched agents/processes completed before output consolidation. Bob output and raw-log hashes match the receipt. All 12 Alice R, 19 Blake B, 12 Bob R, and 5 Bob D verdicts are present verbatim below.

## Consolidated findings

| ID | Consensus | Severity | Issue | File | Found by | Disposition |
|---|---|---|---|---|---|---|
| A1 | [1/3] | 🟠 high | High Credential rejection omits `authorization`, `cookie`, and `credential`, so secret-bearing environment/options keys and values can enter agent settings and the launch overlay despite the PRD’s closed sensitive-key contract | src/ovcaq/config.py:43 | ALICE | auto-fix |
| A2 | [1/3] | 🟡 medium | Medium `agent_settings()` rejects configurations without an explicit command instead of applying the required `(name,)` default | src/ovcaq/config.py:156 | ALICE | auto-fix |
| A3 | [1/3] | 🟠 high | High The Claude adapter implements `fallback_tier` and emits raw format `stream-json`, while the accepted contract specifies the `fallback_model` option and `claude-stream-json-v1`; existing tests pin the divergent behavior | src/ovcaq/drivers/claude.py:40 | ALICE | auto-fix |
| A4 | [1/3] | 🟠 high | High Rate-limit terminal banners are only classified and never parsed into a future timezone-qualified reset observation, so valid banner reset times cannot reach `SessionSummary.rate_limit_reset_at` as required | src/ovcaq/drivers/claude_events.py:154 | ALICE | auto-fix |
| A5 | [1/3] | 🟡 medium | Medium `workflow_settings()` duplicates agent-tier merging instead of delegating to `agent_settings()`, allowing workflow callers to accept agent configurations that the launch configuration rejects | src/ovcaq/config.py:221 | ALICE | auto-fix |
| A6 | [2/3] | 🟡 medium | Medium The new scripted-process test function is 56 lines, exceeding the 50-line function limit | tests/drivers/test_claude_process.py:96 | ALICE, BOB | auto-fix |
| A7 | [2/3] | 🟡 medium | Medium The new Claude driver test file is 893 lines, exceeding the 800-line file limit | tests/drivers/test_claude.py:1 | ALICE, BOB | auto-fix |
| B1 | [1/3] | 🟠 high | Built-in driver registration is not implemented: `discover_drivers` requires callers to supply an arbitrary built-in iterable, and the public driver package defines no registry or factory that registers Claude by its unique name, so production discovery can return no Claude driver | src/ovcaq/drivers/base.py:165 | BLAKE | discarded |
| B2 | [1/3] | 🟠 high | Normalized-event redaction only catches credential-shaped keys and assignment syntax; bare likely secrets such as provider API tokens embedded in activity or tool text are persisted unchanged, violating the requirement to redact likely secrets from normalized evidence | src/ovcaq/events/model.py:22 | BLAKE | auto-fix |
| O1 | [1/3] | 🟠 high | LaunchSpec.env is the child's whole environment (OwnedProcess.spawn passes it straight to Popen; test_claude_process checks that HOST_ONLY_MARKER is None in the child), and ClaudeDriver sets only CLAUDE_UNATTENDED, CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS and WARDEN_UNATTENDED. With no PATH, Popen looks up a bare `command=["claude"]` only in /bin:/usr/bin, so launch fails with FileNotFoundError while probe() (shutil.which with the host PATH) still reports healthy. The agent's Bash tool also gets no PATH/HOME, so mise, git and uv go missing. The source runner.py child_env() passed the full host env through, dropping only host markers, and the PRD says "environment additions". Confirmed by reading the code; the fake-claude test hides it because it uses an absolute path | src/ovcaq/drivers/claude.py:66 | BOB | discarded |
| O2 | [1/3] | 🟠 high | rate_limit_payload maps `allowed_warning` to rate_limit.started whatever the window, and drops rateLimitType. The reducer then turns any generic agent/unknown failure (or a missing terminal record) into RATE_LIMIT with the warning's reset, which can be days away for a seven_day warning. The source never treated allowed_warning as a limit: only `rejected` counts, and only a five_hour warning is a yield signal (usage_limit.py _warning_reset; golden 00199:41). So the port drops that five_hour/seven_day distinction and can make the supervisor wait out a weekly window after an unrelated failure | src/ovcaq/drivers/claude_events.py:109 | BOB | auto-fix |
| O3 | [1/3] | 🟡 medium | The env allowlist hard-codes the personal key WARDEN_UNATTENDED and rejects every other non-CLAUDE_ key from per-agent config. The PRD says other additions (for example WARDEN_UNATTENDED) "come from per-agent configuration, never from driver constants" | src/ovcaq/drivers/claude.py:60 | BOB | auto-fix |
| O4 | [1/3] | 🟡 medium | block_payload handles tool_result only when `content` is a string. List-form content (Task/subagent and MCP results) and missing content give no tool.completed/tool.failed, and a user record made only of such blocks becomes raw.unknown. The source render_stream._result_text joined the list's text blocks, and tracon retired lanes whatever the content shape | src/ovcaq/drivers/claude_events.py:57 | BOB | auto-fix |
| O5 | [1/3] | 🟡 medium | The `"\ufffd" not in raw_line` guard sends any valid record containing a literal U+FFFD to raw.unknown (common in tool output decoded with replacement; a terminal result record lost this way makes the summary unsuccessful). The driver's raw_sha256 also hashes the re-encoded replaced text, not the raw bytes, so it can't be matched to the raw evidence | src/ovcaq/drivers/claude.py:132 | BOB | auto-fix |
| O6 | [1/3] | 🟡 medium | The Claude driver never sets estimated=True. Message-summed interim usage is inferred, yet it is reported as exact, and _update_usage folds message maxima into the "exact" result snapshot (the test expects cache_creation 6 against a reported 3). Plan §11 says `estimated=true` is mandatory on inferred values, so the reducer's estimation logic is dead for the only real driver | src/ovcaq/drivers/claude.py:299 | BOB | auto-fix |
| O7 | [1/3] | 🟡 medium | RawFirstDecoder's fallback raw.unknown uses run_id="unknown" and session_id=None (and a literal protocol_version=1 instead of PROTOCOL_VERSION), so oversized frames and frames the driver fails to decode drop the run's identity in normalized evidence | src/ovcaq/events/tail.py:103 | BOB | auto-fix |
| O8 | [1/3] | 🟡 medium | Driver lifetime is not specified. ClaudeDriver.decode keeps per-session state (usage totals, session_id, a 1 MiB Bloom filter), but discovery builds one probed instance per name through a zero-argument DriverFactory, which cannot construct ClaudeDriver(settings, run_id=...). No built-in registration exists. Reusing one instance across sessions would inflate usage and leak the previous session_id into pre-init observations | docs/driver-protocol.md:18 | BOB | auto-fix |
| O9 | [1/3] | 🟡 medium | RawSessionWriter is now an empty subclass kept after the rename, with no caller in src (AGENTS.md: no compatibility shims). Parametrizing test_raw_session over two identical classes doubles every case and adds no coverage | src/ovcaq/runtime/session.py:140 | BOB | auto-fix |
| O10 | [1/3] | 🟡 medium | Tautological test: test_fake_driver_summary_agrees_with_shared_reduction compares a test-local FakeDriver.summarize, which is literally reduce_session(...).summary, with reduce_session and cannot fail | tests/drivers/test_contract.py:329 | BOB | auto-fix |
| O13 | [1/3] | ⚪ low | The record_timestamp happy path is untested: a valid offset timestamp converted to UTC, and a naive timestamp falling back to now. The only parametrized cases are invalid values | src/ovcaq/drivers/claude_events.py:10 | BOB | auto-fix |
| O14 | [1/3] | ⚪ low | The neutrality guard scans only events/, runtime/, tui/ and drivers/base.py. It skips workflow/, state/, cli*.py and config.py, where P05 routing lands, so the AGENTS.md provider-neutral rule is only partly enforced | tests/drivers/test_neutrality.py:5 | BOB | auto-fix |
| O15 | [1/3] | ⚪ low | A hand-rolled 1 MiB-per-driver Bloom filter guards against message-id replays after more than 4096 other message ids, which may never happen in Claude stream-json | src/ovcaq/drivers/claude.py:73 | BOB | discarded |
| O16 | [1/3] | ⚪ low | There is no "loud preflight" for unattended permissions. A missing mode fails loudly, but when the mode is configured, probe()/DriverHealth.detail never mentions the unattended permission mode (plan §15) | src/ovcaq/drivers/claude.py:75 | BOB | auto-fix |
| O17 | [1/3] | ⚪ low | The protocol doc doesn't say that usage.updated snapshots must be cumulative per session. The reducer folds fields by per-field max, so a per-turn delta driver (the Codex driver in PRD 00009) would undercount | docs/driver-protocol.md:18 | BOB | auto-fix |
| O18 | [1/3] | ⚪ low | The prompt is the last positional argument with no `--` before it, so a prompt starting with "-" would be parsed as a CLI option | src/ovcaq/drivers/claude.py:84 | BOB | settled-deferral |
| O19 | [1/3] | ⚪ low | Cannot statically verify: the test/lint/type/build suite passes at HEAD (reused last-verification.json reports 2731 passed, 0 skipped) | N/A | BOB | routed to verification |
| M1 | [1/3] | 🟡 medium | 40 touched test(s) pass against the pre-change code: test_shared_modules_do_not_import_provider_modules +34 more | tests/drivers/test_neutrality.py | mech-check | discarded |

Consolidation used the installed script. Its over-merge of A2 (missing command default) and A5 (workflow tier-reader delegation) was split back into two rows because these are distinct defects; both verbatim texts survive. A6/O12 and A7/O11 are the same size-limit findings and retain both reviewers. M1 is the mandatory mechanical replay finding. The untouched script output is retained separately.

## Decision gate

Cycle 1 is below cap 2. Five unresolved HIGH findings (A1, A3, A4, B2, O2) require rework. No CRITICAL finding or actual credential exposure was found. Synthetic probes only were used; no real credentials were read or emitted. There are 21 actionable rows grouped into five bounded tasks, so the scope alarm does not fire.

- **B1 — discarded:** The accepted design explicitly defines discover_drivers(builtins: Iterable[DriverPlugin]); _register_driver registers each driver by unique name and checks duplicates. tests/drivers/test_registry.py:10 exercises Claude registration through a closure. Automatic supervisor composition belongs to PRD 00007; an implicit provider import into neutral discovery would break the boundary.
- **O1 — discarded:** The accepted design states LaunchSpec.env is an overlay and its Data flow step 2 assigns deliberate host-environment merging to the later supervisor. OwnedProcess.spawn accepts the final environment, so the test passes a self-contained fake environment deliberately. No production supervisor caller exists in this PRD. Keep provider code from copying os.environ; clarify overlay composition in the protocol documentation task.
- **O15 — discarded:** The committed task-7 decision explicitly requires a bounded exact cache and fixed Bloom filter to suppress evicted replays. The requirement is deduplication with bounded memory, not proof that a current captured run exceeds 4096 identities. Deleting the filter on absence of such logs would reintroduce a required replay failure. Inferred/possibly undercounted usage is fixed under O6.
- **O18 — settled-deferral:** Exact argv matches the characterized runner and this phase's accepted launch contract; the built-in workflow prompts begin with '/'. General arbitrary leading-hyphen prompt handling is outside the current exact-port contract. Preserve the limitation for batch-end review rather than change argv without that contract decision.
- **O19 — routed to verification:** The current-HEAD work verification already reports 2731/0/0 and all quality/build commands passed, so review reuses it. Queue Bob's five named project checks for the next work phase's mandatory verification pass; do not create a task just to run the suite.
- **M1 — discarded:** The 40 tests that pass on base are provider-neutrality backfill guards and existing behavior coverage; the base already satisfies those invariants. Ten changed test files fail collection against the old code. A guard intentionally passing on a clean base is not tautological. Its assertions fail on prohibited imports or source identifiers.

A3 passed local research protocols C/D: the accepted design explicitly names fallback_model and claude-stream-json-v1, while task 6 omitted these exact details. Correct the missing contract transmission; preserve the PRD's auto-only unattended launch. No public stability guarantee exists yet and no dependency is added. O3 follows the PRD's explicit per-agent configured additions over the design's narrower personal allowlist.

For other bounded HIGH fixes, validation and redaction checks or reset classification/parser handling are added within the existing PRD contract. O8's assertion that a zero-argument factory cannot capture settings/run_id is refuted by test_registry's closure; its missing lifecycle documentation is retained and fixed. Bob's two non-command VERIFY requests (Bloom logs, permission ownership) are not queued: command shape; they are resolved as O15's discard and O16's preflight task. O19 supplies five exact allowed project commands for the next work verification pass.

## Rework tasks

- Task 11: [D1] Repair configuration and redaction contracts (M); findings A1, A2, A5, B2; logical sonnet (default); pending.
- Task 12: [D1] Reconcile the Claude launch contract and preflight (M); findings A3, O3, O16; logical opus (contract); pending.
- Task 13: [D1] Correct Claude stream semantics and raw fallback evidence (L); findings A4, O2, O4, O5, O6, O7, O13; logical opus (contract); pending.
- Task 14: [D1] Remove redundant evidence and test scaffolding (M); findings A6, A7, O9, O10, O14; logical opus (contract); pending.
- Task 15: [D1] Document session ownership and cumulative observations (S); findings O8, O17; logical sonnet (default); pending.

The session stops after queueing. Phase and next_phase remain review; cycle stays 1. The next fresh session resumes Phase 6 through the existing review-file plus unfinished rework_task_ids rule. No repairs or cycle increment occur in this review session.

## Validation evidence

Tests: 2731 passed, 0 failed, 0 skipped (reused from last-verification.json at 24fcec3bed6a41044c3d149d1f42bd678864e7e0)

Same-HEAD quality/build record: uv sync --all-groups, uv run ruff check ., uv run ruff format --check ., uv run mypy src/ovcaq, and uv build each exited 0. No repeat full suite was run during review.
State schema and task counts validated before dispatch; final handoff validates them again.
Mechanical facts and test-shape checks ran. Shapes reported no findings. The initial replay was sandbox-blocked at worktree metadata creation; the approved retry completed and its temporary worktree was removed.

## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `666776af6ecb`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

[MECH] 🟡 40 touched test(s) pass against the pre-change code: test_shared_modules_do_not_import_provider_modules +34 more | File: tests/drivers/test_neutrality.py | Task: general

Replay: 40 touched test(s) ran, 0 failed against base, 40 passed; 10 test file(s) could not be collected at base (their tests fail there). Command: mise exec -- uv run pytest


Synthetic confirmation: bare Bearer sentinel remained unredacted; a credential-shaped configured environment key was accepted; a future timezone-qualified limit banner yielded no reset. These confirm the relevant boundary findings without using live secrets.

## Task → commit mapping

# Completed task → commit mapping

| Task | Name | Commits |
|---|---|---|
| 1 | Define the normalized event protocol | d88fe38, 9b6c00b, 7402894 |
| 2 | Implement deterministic session reduction | d521867, f86de73, 431a5e1, 54c7230, 14e7525 |
| 3 | Define driver ABI and discovery | 3a4c241, 24f683b, 881da3b, 2cb56c1 |
| 4 | Load per-agent settings | 2d42d98, f46c254, a2093ac, 408e711 |
| 5 | Persist raw-first normalized evidence | 1b77226, 9effa7c, fa358a9 |
| 6 | Implement exact Claude launch contract | 7c6bd13, 04181ea, 032e550 |
| 7 | Decode Claude streams into normalized observations | c039c61, 96618a9, bcd784a, aca3a14 |
| 8 | Port Claude fixtures and conformance tests | 749021b, ca2688b |
| 9 | Enforce provider-neutral shared modules | fe03dd1, f506a05 |
| 10 | Document the version-1 driver protocol | 24fcec3 |

## Alice

[ALICE] 🟠 High Credential rejection omits `authorization`, `cookie`, and `credential`, so secret-bearing environment/options keys and values can enter agent settings and the launch overlay despite the PRD’s closed sensitive-key contract | File: src/ovcaq/config.py:43 | Task: 4
[ALICE] 🟡 Medium `agent_settings()` rejects configurations without an explicit command instead of applying the required `(name,)` default | File: src/ovcaq/config.py:156 | Task: 4
[ALICE] 🟠 High The Claude adapter implements `fallback_tier` and emits raw format `stream-json`, while the accepted contract specifies the `fallback_model` option and `claude-stream-json-v1`; existing tests pin the divergent behavior | File: src/ovcaq/drivers/claude.py:40 | Task: 6
[ALICE] 🟠 High Rate-limit terminal banners are only classified and never parsed into a future timezone-qualified reset observation, so valid banner reset times cannot reach `SessionSummary.rate_limit_reset_at` as required | File: src/ovcaq/drivers/claude_events.py:154 | Task: 7
[ALICE] 🟡 Medium `workflow_settings()` duplicates agent-tier merging instead of delegating to `agent_settings()`, allowing workflow callers to accept agent configurations that the launch configuration rejects | File: src/ovcaq/config.py:221 | Task: 4
[ALICE] 🟡 Medium The new scripted-process test function is 56 lines, exceeding the 50-line function limit | File: tests/drivers/test_claude_process.py:96 | Task: 8
[ALICE] 🟡 Medium The new Claude driver test file is 893 lines, exceeding the 800-line file limit | File: tests/drivers/test_claude.py:1 | Task: 8
R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: pass
R11: pass
R12: fail
R13: fail

## Blake

[BLAKE] 🟠 Built-in driver registration is not implemented: `discover_drivers` requires callers to supply an arbitrary built-in iterable, and the public driver package defines no registry or factory that registers Claude by its unique name, so production discovery can return no Claude driver | File: src/ovcaq/drivers/base.py:165 | Task: general
[BLAKE] 🟠 Normalized-event redaction only catches credential-shaped keys and assignment syntax; bare likely secrets such as provider API tokens embedded in activity or tool text are persisted unchanged, violating the requirement to redact likely secrets from normalized evidence | File: src/ovcaq/events/model.py:22 | Task: general
B1: fail
B2: pass
B3: fail
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: fail
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: pass
B17: pass
B18: pass
B19: pass

## Bob

The review found 19 issues: 2 high, 8 medium, 9 low. The most serious is that a real Claude launch would probably fail. The closed launch environment leaves out `PATH` and `HOME`, which the old runner passed through from the host.

```
[BOB] 🟠 LaunchSpec.env is the child's whole environment (OwnedProcess.spawn passes it straight to Popen; test_claude_process checks that HOST_ONLY_MARKER is None in the child), and ClaudeDriver sets only CLAUDE_UNATTENDED, CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS and WARDEN_UNATTENDED. With no PATH, Popen looks up a bare `command=["claude"]` only in /bin:/usr/bin, so launch fails with FileNotFoundError while probe() (shutil.which with the host PATH) still reports healthy. The agent's Bash tool also gets no PATH/HOME, so mise, git and uv go missing. The source runner.py child_env() passed the full host env through, dropping only host markers, and the PRD says "environment additions". Confirmed by reading the code; the fake-claude test hides it because it uses an absolute path | File: src/ovcaq/drivers/claude.py:66 | Task: P04-T04
[BOB] 🟠 rate_limit_payload maps `allowed_warning` to rate_limit.started whatever the window, and drops rateLimitType. The reducer then turns any generic agent/unknown failure (or a missing terminal record) into RATE_LIMIT with the warning's reset, which can be days away for a seven_day warning. The source never treated allowed_warning as a limit: only `rejected` counts, and only a five_hour warning is a yield signal (usage_limit.py _warning_reset; golden 00199:41). So the port drops that five_hour/seven_day distinction and can make the supervisor wait out a weekly window after an unrelated failure | File: src/ovcaq/drivers/claude_events.py:109 | Task: P04-T06
[BOB] 🟡 The env allowlist hard-codes the personal key WARDEN_UNATTENDED and rejects every other non-CLAUDE_ key from per-agent config. The PRD says other additions (for example WARDEN_UNATTENDED) "come from per-agent configuration, never from driver constants" | File: src/ovcaq/drivers/claude.py:60 | Task: P04-T04
[BOB] 🟡 block_payload handles tool_result only when `content` is a string. List-form content (Task/subagent and MCP results) and missing content give no tool.completed/tool.failed, and a user record made only of such blocks becomes raw.unknown. The source render_stream._result_text joined the list's text blocks, and tracon retired lanes whatever the content shape | File: src/ovcaq/drivers/claude_events.py:57 | Task: P04-T05
[BOB] 🟡 The `"\ufffd" not in raw_line` guard sends any valid record containing a literal U+FFFD to raw.unknown (common in tool output decoded with replacement; a terminal result record lost this way makes the summary unsuccessful). The driver's raw_sha256 also hashes the re-encoded replaced text, not the raw bytes, so it can't be matched to the raw evidence | File: src/ovcaq/drivers/claude.py:132 | Task: P04-T05
[BOB] 🟡 The Claude driver never sets estimated=True. Message-summed interim usage is inferred, yet it is reported as exact, and _update_usage folds message maxima into the "exact" result snapshot (the test expects cache_creation 6 against a reported 3). Plan §11 says `estimated=true` is mandatory on inferred values, so the reducer's estimation logic is dead for the only real driver | File: src/ovcaq/drivers/claude.py:299 | Task: P04-T05
[BOB] 🟡 RawFirstDecoder's fallback raw.unknown uses run_id="unknown" and session_id=None (and a literal protocol_version=1 instead of PROTOCOL_VERSION), so oversized frames and frames the driver fails to decode drop the run's identity in normalized evidence | File: src/ovcaq/events/tail.py:103 | Task: P04-T02
[BOB] 🟡 Driver lifetime is not specified. ClaudeDriver.decode keeps per-session state (usage totals, session_id, a 1 MiB Bloom filter), but discovery builds one probed instance per name through a zero-argument DriverFactory, which cannot construct ClaudeDriver(settings, run_id=...). No built-in registration exists. Reusing one instance across sessions would inflate usage and leak the previous session_id into pre-init observations | File: docs/driver-protocol.md:18 | Task: P04-T03
[BOB] 🟡 RawSessionWriter is now an empty subclass kept after the rename, with no caller in src (AGENTS.md: no compatibility shims). Parametrizing test_raw_session over two identical classes doubles every case and adds no coverage | File: src/ovcaq/runtime/session.py:140 | Task: P04-T02
[BOB] 🟡 Tautological test: test_fake_driver_summary_agrees_with_shared_reduction compares a test-local FakeDriver.summarize, which is literally reduce_session(...).summary, with reduce_session and cannot fail | File: tests/drivers/test_contract.py:329 | Task: P04-T01
[BOB] ⚪ test_claude.py is 893 lines, over the 800-line file cap | File: tests/drivers/test_claude.py:1 | Task: P04-T08
[BOB] ⚪ test_scripted_claude_runs_through_launch_and_owned_process is 56 lines, over the 50-line function cap | File: tests/drivers/test_claude_process.py:96 | Task: P04-T08
[BOB] ⚪ The record_timestamp happy path is untested: a valid offset timestamp converted to UTC, and a naive timestamp falling back to now. The only parametrized cases are invalid values | File: src/ovcaq/drivers/claude_events.py:10 | Task: P04-T05
[BOB] ⚪ The neutrality guard scans only events/, runtime/, tui/ and drivers/base.py. It skips workflow/, state/, cli*.py and config.py, where P05 routing lands, so the AGENTS.md provider-neutral rule is only partly enforced | File: tests/drivers/test_neutrality.py:5 | Task: P04-T09
[BOB] ⚪ A hand-rolled 1 MiB-per-driver Bloom filter guards against message-id replays after more than 4096 other message ids, which may never happen in Claude stream-json | File: src/ovcaq/drivers/claude.py:73 | Task: P04-T05
[BOB] ⚪ There is no "loud preflight" for unattended permissions. A missing mode fails loudly, but when the mode is configured, probe()/DriverHealth.detail never mentions the unattended permission mode (plan §15) | File: src/ovcaq/drivers/claude.py:75 | Task: P04-T04
[BOB] ⚪ The protocol doc doesn't say that usage.updated snapshots must be cumulative per session. The reducer folds fields by per-field max, so a per-turn delta driver (the Codex driver in PRD 00009) would undercount | File: docs/driver-protocol.md:18 | Task: P04-T01
[BOB] ⚪ The prompt is the last positional argument with no `--` before it, so a prompt starting with "-" would be parsed as a CLI option | File: src/ovcaq/drivers/claude.py:84 | Task: P04-T04
[BOB] ⚪ Cannot statically verify: the test/lint/type/build suite passes at HEAD (reused last-verification.json reports 2731 passed, 0 skipped) | File: N/A | Task: general
```

FIX:
- The closed env drops PATH/HOME, so a bare `claude` command can't be found at spawn — src/ovcaq/drivers/claude.py:66 — build the child env as the host env minus the source HOST_MARKERS (CODEX_*, COPILOT_*), then the CLAUDE defaults, then the configured additions (port runner.child_env). Update docs/driver-protocol.md:18 ("closed") and the HOST_ONLY_MARKER assertion in tests/drivers/test_claude_process.py. Add a test showing that a bare command name found by probe() also spawns.
- allowed_warning is treated as a live limit and the window type is lost — src/ovcaq/drivers/claude_events.py:109 — emit rate_limit.started only for `rejected`. Map `allowed_warning` to a non-limit observation (or leave it out) and keep `rate_limit_type` in the payload. Update the parametrized test in test_claude.py.
- WARDEN_UNATTENDED is a hard-coded allowlist entry — src/ovcaq/drivers/claude.py:60 — remove the literal and accept any configured key the config credential check passes. Keep only the fixed CLAUDE_ defaults protected from override.
- List-content tool results are dropped — src/ovcaq/drivers/claude_events.py:57 — accept `list` content by joining the dict text blocks (as source _result_text does). Treat missing content as "", then sanitize and bound as now. Add list and missing-content test cases.
- The U+FFFD heuristic and the non-raw digest — src/ovcaq/drivers/claude.py:132 — in RawFirstDecoder._complete, decode strictly. On UnicodeDecodeError, emit the tail's raw.unknown (true byte digest) and skip driver.decode. Remove the `"\ufffd"` guard and add a test where a valid record with a literal U+FFFD still decodes.
- Inferred usage is marked exact — src/ovcaq/drivers/claude.py:299 — mark message-derived snapshots `estimated=True`. Build the result snapshot only from the result's own counters and cost, and let reduce_session fold them (its estimation rule already covers this). Update test_usage_replays… and test_result_emits….
- Tail fallback loses run identity — src/ovcaq/events/tail.py:103 — add a required `run_id` parameter to RawFirstDecoder, carry the last seen session_id, and use PROTOCOL_VERSION at src/ovcaq/events/tail.py:100.
- Driver lifetime is unspecified — docs/driver-protocol.md:18 — state that one driver instance decodes exactly one session and that discovery instances are only for probing and naming. Show how a built-in wraps ClaudeDriver(settings, run_id) in a zero-argument factory.
- Empty RawSessionWriter shim — src/ovcaq/runtime/session.py:140 — delete the subclass, switch tests/drivers/test_claude_process.py to SessionEvidenceWriter, and drop the `writer_type` parametrization from tests/runtime/test_raw_session.py.
- Tautological fake summary test — tests/drivers/test_contract.py:329 — delete it, or assert explicit expected SessionSummary fields per case (success, failure_class) instead of comparing with reduce_session.
- test_claude.py over the file cap — tests/drivers/test_claude.py:1 — split into test_claude_launch.py (argv/env/probe) and test_claude_decode.py (stream/fixtures).
- Test function over 50 lines — tests/drivers/test_claude_process.py:96 — move the spawn/read/finish/collect loop into a `_run_owned(decoder, spec)` helper.
- record_timestamp happy path untested — src/ovcaq/drivers/claude_events.py:10 — add cases: "2026-01-01T02:00:00+02:00" gives 2026-01-01T00:00Z, and a naive ISO string gives the fallback.
- Neutrality guard scope too narrow — tests/drivers/test_neutrality.py:5 — add src/ovcaq/workflow, src/ovcaq/state, src/ovcaq/cli.py, src/ovcaq/workflow_cli.py, src/ovcaq/runtime_cli.py and src/ovcaq/config.py to SCANNED_PATHS.
- Cumulative-usage contract undocumented — docs/driver-protocol.md:18 — add one sentence: usage.updated carries cumulative per-session snapshots, which are folded by per-field max.

VERIFY:
- Bloom filter necessity — check captured real Claude stream-json logs (for example `~/.claude/autopilot-loops` session logs) for any assistant `message.id` that reappears after more than 4096 distinct intervening ids. If none does, replace the filter with the bounded LRU alone.
- Loud unattended-permission preflight — check whether dev/local/prds PRD 00007 or the `ovcaq doctor` spec assigns the "loud preflight" notice (plan §15). If neither does, add the permission mode to ClaudeDriver.probe() detail.
- Suite passes at HEAD — run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src/ovcaq` and `uv build`, and confirm each exits 0.

KNOWN:
- Prompt passed without a `--` separator — the argv matches the characterized source runner.build_argv exactly (PRD asks for an exact port), and OVCAQ-generated prompts start with "/"; changing the argv shape needs a separate decision.

```
R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: fail
R13: fail
```

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

The Cloudflare Developer Platform, Excalidraw and Tidal connectors on claude.ai need authorizing in claude.ai connector settings before they can be used. This review didn't need them.

Verdict: 27 findings
Tests: 2731 passed, 0 failed, 0 skipped (reused from last-verification.json at 24fcec3bed6a41044c3d149d1f42bd678864e7e0)
