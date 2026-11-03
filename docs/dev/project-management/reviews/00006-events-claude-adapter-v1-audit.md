# Decision Audit Log: 00006-events-claude-adapter-v1

PRD: `00006-events-claude-adapter-v1.md`
Started: 2026-10-02T11:22:57Z
Completed: 2026-10-02T11:22:57Z
Autonomous: 69  |  Deferred: 14  |  Doubts: 0

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Choose the Phase 4 event and Claude-driver design before task planning

**Choice**: Use a versioned immutable normalized protocol, bounded raw-first framing, one neutral reducer, and a Claude-only launch/decoder edge

**Rationale**: This preserves raw evidence and state authority while giving the supervisor, TUI, and later Codex adapter one provider-neutral contract

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Resolve underspecified normalized-protocol bounds and sanitizer patterns discovered by requirements-only test authoring

**Choice**: Use closed string/mapping payload types, reject non-UTC timestamps, bound failure detail at 4096 characters and raw preview at 512 characters, and redact only Bearer credentials plus sensitive-key assignments in free text

**Rationale**: These are pre-stability internal safety bounds; the choices are conservative, preserve private raw evidence, and avoid broad prose over-redaction

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: If a later session.completed observation reports lower cumulative usage than an earlier completion or usage snapshot, should the last completion replace the usage total or only select the terminal outcome?

**Choice**: All completion usage snapshots participate in the same fieldwise monotonic-maximum fold; the last completion selects terminal success but cannot lower cumulative counters.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Task 2 completion-usage tests expose that task 1 generic payload sanitization destroys normalized usage fields before reduction

**Choice**: Expand task 2 implementation scope to src/ovcaq/events/model.py so terminal usage receives the same typed schema-field treatment as usage.updated

**Rationale**: The reducer contract requires the last completion to supply final usage, which cannot be implemented after model construction has redacted the counters

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: How must driver discovery surface invalid names, entry-point load/factory/probe failures, and unhealthy probes when the accepted design only states that failures remain visible by driver name?

**Choice**: Use a fail-closed DriverDiscoveryError hierarchy: incompatible and duplicate cases have named subclasses; load, construction, name mismatch, probe exceptions, and unhealthy results raise driver-named discovery errors; built-ins retain input order and third-party entry points are sorted by name.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Which exception classes should task 3 validation use for invalid dataclass fields and loaded objects that are not DriverPlugin?

**Choice**: Raise TypeError for wrong Python field types, ValueError for correctly typed empty or non-positive values, and DriverDiscoveryError when built-in or entry-point discovery receives an object that is not DriverPlugin.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Does AgentSettings immutability apply to direct construction, and must tests require an explicit version field?

**Choice**: AgentSettings directly copies and freezes its mappings; version remains the optional top-level field where absence defaults to version 1, so task tests do not duplicate existing invalid-version coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: What exact framing and fallback behavior should RawFirstDecoder use for CRLF, blank frames, invalid UTF-8, oversized frames, and unexpected driver exceptions?

**Choice**: Write raw bytes first; split on LF and remove LF plus one preceding CR; decode UTF-8 with replacement; pass blank frames to the driver; finish only non-empty residue; emit and persist exactly one bounded RAW_UNKNOWN fallback per oversized frame or decoder exception, using driver.name and run_id unknown when no typed driver context is available.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: What exact option and environment vocabulary should the v1 Claude launch driver expose?

**Choice**: Use required permission_mode=auto, optional fallback_tier resolved through AgentSettings.tiers, and optional allow_explicit_model=false; emit only fixed CLAUDE_UNATTENDED=1 and CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 plus configured CLAUDE_* or WARDEN_UNATTENDED values, never inherit os.environ, and reject conflicting fixed values or unknown driver options.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Which compact neutral payload keys and bounded usage identity semantics should the Claude v1 decoder expose?

**Choice**: Map init, activity, tool, lane, background, usage, rate-limit, and terminal records to closed scalar-only payloads; never retain native blocks; keep at most 4096 assistant message identities; deduplicate replacements, preserve monotonic totals after eviction, emit exact result usage before terminal, retain session identity after init, and use strict future-only numeric or timezone-qualified rate-limit resets.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Task 7 lane-progress tests expose that generic payload sanitization redacts normalized numeric total_tokens before serialization

**Choice**: Expand task 7 implementation scope to src/ovcaq/events/model.py so closed normalized counter fields remain numeric while arbitrary credential-shaped payload keys stay redacted

**Rationale**: The accepted lane-progress contract requires numeric counters and cannot be implemented solely inside the Claude decoder after Observation construction sanitizes them

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: How can the Claude decoder suppress replays of evicted opaque message IDs while keeping identity memory bounded?

**Choice**: Keep a 4096-entry exact contribution cache plus a fixed-size at-least-1-MiB Bloom filter for evicted IDs; exact cached replacements adjust totals, evicted contributions remain anchored, and Bloom hits conservatively suppress possible replays or rare false-positive new IDs rather than inflate usage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: High Credential rejection omits `authorization`, `cookie`, and `credential`, so secret-bearing environment/options keys and values can enter agent settings and the launch overlay despite the PRD’s closed sensitive-key contract

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Medium `agent_settings()` rejects configurations without an explicit command instead of applying the required `(name,)` default

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: High The Claude adapter implements `fallback_tier` and emits raw format `stream-json`, while the accepted contract specifies the `fallback_model` option and `claude-stream-json-v1`; existing tests pin the divergent behavior

**Recommendation**: Correct the spec-transmission gap without changing the PRD auto-only unattended behavior

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: High Rate-limit terminal banners are only classified and never parsed into a future timezone-qualified reset observation, so valid banner reset times cannot reach `SessionSummary.rate_limit_reset_at` as required

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Medium `workflow_settings()` duplicates agent-tier merging instead of delegating to `agent_settings()`, allowing workflow callers to accept agent configurations that the launch configuration rejects

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Medium The new scripted-process test function is 56 lines, exceeding the 50-line function limit

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Medium The new Claude driver test file is 893 lines, exceeding the 800-line file limit

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Built-in driver registration is not implemented: `discover_drivers` requires callers to supply an arbitrary built-in iterable, and the public driver package defines no registry or factory that registers Claude by its unique name, so production discovery can return no Claude driver

**Choice**: discarded

**Rationale**: The accepted design explicitly defines discover_drivers(builtins: Iterable[DriverPlugin]); _register_driver registers each driver by unique name and checks duplicates. tests/drivers/test_registry.py:10 exercises Claude registration through a closure. Automatic supervisor composition belongs to PRD 00007; an implicit provider import into neutral discovery would break the boundary.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Normalized-event redaction only catches credential-shaped keys and assignment syntax; bare likely secrets such as provider API tokens embedded in activity or tool text are persisted unchanged, violating the requirement to redact likely secrets from normalized evidence

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: LaunchSpec.env is the child's whole environment (OwnedProcess.spawn passes it straight to Popen; test_claude_process checks that HOST_ONLY_MARKER is None in the child), and ClaudeDriver sets only CLAUDE_UNATTENDED, CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS and WARDEN_UNATTENDED. With no PATH, Popen looks up a bare `command=["claude"]` only in /bin:/usr/bin, so launch fails with FileNotFoundError while probe() (shutil.which with the host PATH) still reports healthy. The agent's Bash tool also gets no PATH/HOME, so mise, git and uv go missing. The source runner.py child_env() passed the full host env through, dropping only host markers, and the PRD says "environment additions". Confirmed by reading the code; the fake-claude test hides it because it uses an absolute path

**Choice**: discarded

**Rationale**: The accepted design states LaunchSpec.env is an overlay and its Data flow step 2 assigns deliberate host-environment merging to the later supervisor. OwnedProcess.spawn accepts the final environment, so the test passes a self-contained fake environment deliberately. No production supervisor caller exists in this PRD. Keep provider code from copying os.environ; clarify overlay composition in the protocol documentation task.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: rate_limit_payload maps `allowed_warning` to rate_limit.started whatever the window, and drops rateLimitType. The reducer then turns any generic agent/unknown failure (or a missing terminal record) into RATE_LIMIT with the warning's reset, which can be days away for a seven_day warning. The source never treated allowed_warning as a limit: only `rejected` counts, and only a five_hour warning is a yield signal (usage_limit.py _warning_reset; golden 00199:41). So the port drops that five_hour/seven_day distinction and can make the supervisor wait out a weekly window after an unrelated failure

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: The env allowlist hard-codes the personal key WARDEN_UNATTENDED and rejects every other non-CLAUDE_ key from per-agent config. The PRD says other additions (for example WARDEN_UNATTENDED) "come from per-agent configuration, never from driver constants"

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: block_payload handles tool_result only when `content` is a string. List-form content (Task/subagent and MCP results) and missing content give no tool.completed/tool.failed, and a user record made only of such blocks becomes raw.unknown. The source render_stream._result_text joined the list's text blocks, and tracon retired lanes whatever the content shape

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: The `"\ufffd" not in raw_line` guard sends any valid record containing a literal U+FFFD to raw.unknown (common in tool output decoded with replacement; a terminal result record lost this way makes the summary unsuccessful). The driver's raw_sha256 also hashes the re-encoded replaced text, not the raw bytes, so it can't be matched to the raw evidence

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: The Claude driver never sets estimated=True. Message-summed interim usage is inferred, yet it is reported as exact, and _update_usage folds message maxima into the "exact" result snapshot (the test expects cache_creation 6 against a reported 3). Plan §11 says `estimated=true` is mandatory on inferred values, so the reducer's estimation logic is dead for the only real driver

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: RawFirstDecoder's fallback raw.unknown uses run_id="unknown" and session_id=None (and a literal protocol_version=1 instead of PROTOCOL_VERSION), so oversized frames and frames the driver fails to decode drop the run's identity in normalized evidence

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Driver lifetime is not specified. ClaudeDriver.decode keeps per-session state (usage totals, session_id, a 1 MiB Bloom filter), but discovery builds one probed instance per name through a zero-argument DriverFactory, which cannot construct ClaudeDriver(settings, run_id=...). No built-in registration exists. Reusing one instance across sessions would inflate usage and leak the previous session_id into pre-init observations

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: RawSessionWriter is now an empty subclass kept after the rename, with no caller in src (AGENTS.md: no compatibility shims). Parametrizing test_raw_session over two identical classes doubles every case and adds no coverage

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Tautological test: test_fake_driver_summary_agrees_with_shared_reduction compares a test-local FakeDriver.summarize, which is literally reduce_session(...).summary, with reduce_session and cannot fail

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: The record_timestamp happy path is untested: a valid offset timestamp converted to UTC, and a naive timestamp falling back to now. The only parametrized cases are invalid values

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: The neutrality guard scans only events/, runtime/, tui/ and drivers/base.py. It skips workflow/, state/, cli*.py and config.py, where P05 routing lands, so the AGENTS.md provider-neutral rule is only partly enforced

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: A hand-rolled 1 MiB-per-driver Bloom filter guards against message-id replays after more than 4096 other message ids, which may never happen in Claude stream-json

**Choice**: discarded

**Rationale**: The committed task-7 decision explicitly requires a bounded exact cache and fixed Bloom filter to suppress evicted replays. The requirement is deduplication with bounded memory, not proof that a current captured run exceeds 4096 identities. Deleting the filter on absence of such logs would reintroduce a required replay failure. Inferred/possibly undercounted usage is fixed under O6.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: There is no "loud preflight" for unattended permissions. A missing mode fails loudly, but when the mode is configured, probe()/DriverHealth.detail never mentions the unattended permission mode (plan §15)

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: The protocol doc doesn't say that usage.updated snapshots must be cumulative per session. The reducer folds fields by per-field max, so a per-turn delta driver (the Codex driver in PRD 00009) would undercount

**Choice**: Queue bounded rework

**Rationale**: Bounded correction within PRD 00006; preserve the exact finding in its rework task and verify with regression coverage.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Cannot statically verify: the test/lint/type/build suite passes at HEAD (reused last-verification.json reports 2731 passed, 0 skipped)

**Choice**: routed to verification

**Rationale**: The current-HEAD work verification already reports 2731/0/0 and all quality/build commands passed, so review reuses it. Queue Bob's five named project checks for the next work phase's mandatory verification pass; do not create a task just to run the suite.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: 40 touched test(s) pass against the pre-change code: test_shared_modules_do_not_import_provider_modules +34 more

**Choice**: discarded

**Rationale**: The 40 tests that pass on base are provider-neutrality backfill guards and existing behavior coverage; the base already satisfies those invariants. Ten changed test files fail collection against the old code. A guard intentionally passing on a clean base is not tautological. Its assertions fail on prohibited imports or source identifiers.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Use external Claude Bob as the Codex guard's independent provider voice

**Choice**: Authorized autocodex host substitution

**Rationale**: All ten tasks include Codex attempts; Bob ran fresh on Claude Opus (raw model claude-opus-5-5) with full consensus and doubt/de-slop rubrics. Native Fable unavailable; no Eve dispatch claimed.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Two existing configuration tests contradict accepted command-default and sensitive-key substring contracts

**Choice**: Correct stale tests through Tess, retaining invalid explicit argv and harmless-control coverage

**Rationale**: The accepted design defaults command to the selected name even without an agent table and rejects case-insensitive credential substrings; task 11 repairs that contract, not the stale implementation. Synthetic likely-secret values are rejected in launch configuration and completely redacted in normalized text.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: A nonzero process exit is ignored after session.completed

**Choice**: discarded

**Rationale**: The accepted terminal conflict matrix makes completed terminal authoritative; test_last_completion_supplies_serialized_usage pins exit codes 0 and 1.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Credential-key substring matching rejects token-related control names

**Choice**: discarded

**Rationale**: The accepted design explicitly rejects configuration keys containing token or other credential words; changing that contract needs a separate decision.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: 61 touched decoder tests pass against the pre-change code

**Choice**: discarded

**Rationale**: Decoder tests were split and moved while preserving existing behavior; other touched tests fail against the base.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: 41 touched launch tests pass against the pre-change code

**Choice**: discarded

**Rationale**: Launch tests were split and moved while preserving existing behavior; other touched tests fail against the base.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: 7 touched driver-contract tests pass against the pre-change code

**Choice**: discarded

**Rationale**: These are existing protocol behavior guards, not new behavior claims.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: 5 touched model rework tests pass against the pre-change code

**Choice**: discarded

**Rationale**: Harmless prose and typed-usage preservation already worked; new redaction cases fail against base.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: 39 touched raw writer tests pass against the pre-change code

**Choice**: discarded

**Rationale**: The writer rename preserves its prior safety behavior, which these tests continue to guard.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: 5 touched configuration tests pass against the pre-change code

**Choice**: discarded

**Rationale**: These cover pre-existing configuration behavior; changed contract cases fail against base.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: 9 touched configuration-rework tests pass against the pre-change code

**Choice**: discarded

**Rationale**: Several cases pin pre-existing rejection behavior; changed contract cases fail against base.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: H1/H4/H5/M1 rate-limit semantics (allowed_warning clears limit; banner overwrites event reset; real clock+zone banners unparsed; window only in prose)

**Recommendation**: Legacy usage_limit.py pins banner shape and resetsAt precedence

**Choice**: Queue rework task 16 (opus, same tier)

**Rationale**: Cycle 2, cap 3 authorized. Protocol B (recurring A4/O2): spec-transmission gap (task 13 omitted real banner shape and event-wins precedence); exact contract now transcribed. Same tier, no escalation.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: H3 sanitizer misses x-api-key/apiKey; L3 preview truncates before redaction

**Choice**: Queue rework task 17 (sonnet)

**Rationale**: Additive redaction fix with regression tests; config.py already uses api[_-]?key.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: M2/L1/L2/L4 agent_settings duplication, missing direct-construction tests, dead neutrality path, undefined doc helper

**Choice**: Queue rework task 18 (sonnet)

**Rationale**: Mechanical, behavior-preserving fixes.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: V1 final-HEAD full pytest exited 1; uv build unrun

**Choice**: routed to verification

**Rationale**: Queued checks uv run pytest and uv build (checks-2.json) run in the work phase mandatory step-7 verification.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Cycle 3 hit rework cap 3 with E1 (quadratic sanitize_text reachable via task-17 whole-frame preview) unresolved

**Choice**: Interactive cap pause; user chose resume with rework_cap 4

**Rationale**: User decision 2026-09-30; review-3.md stays on disk so the next session skips Phase 4 and runs the decision gate plus rework for cycle 3

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: E1 quadratic sanitize_text + M2 preview frame-boundary secret prefix

**Choice**: Queue rework task 19 (opus)

**Rationale**: Cycle 3 < cap 4. Bounded regex and preview-window fix with timing and boundary regression tests; opus because the prior sonnet sanitize fix introduced E1.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: M1/M3/M4/L1 rate-limit banner precedence, dated banners, allowed_warning docs

**Choice**: Queue rework task 20 (opus, same tier as task 16)

**Rationale**: Protocol B (recurring rate-limit area): spec-transmission gap - task 16 used a live flag, not session history. Exact sequence contract transcribed; same tier.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: M5 loud preflight / L2 empty codex.py+command.py placeholders / L3 bundled failures.jsonl

**Choice**: discarded

**Rationale**: M5 recurs O16: missing permission_mode fails loudly and probe detail names the configured mode, satisfying the PRD contrast with an implicit default. L2: P00-T03 import-only skeleton pinned by test_package_baseline and packaging_support. L3: PRD layout fixtures/claude/*.jsonl is met; failure classes are covered per line.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: M1 rejected -> allowed -> banner emits a new rate_limit.started

**Choice**: discarded; task 20 contract revised

**Rationale**: Devon showed the literal task-16 rule forces a limit the provider already cleared to drive the retry time. A cleared limit followed by a fresh banner is new evidence, so the banner applies. Only M4 changes precedence: a rejected event without a credible reset no longer marks the limit live.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Cycle 4 hit rework cap 4 with B1 (64-char key-suffix cap in _CREDENTIAL leaks long-key assignments; regression from task 19) unresolved

**Choice**: Interactive cap pause; user chose resume with rework_cap 5

**Rationale**: User decision 2026-09-30; review-4.md stays on disk so the next session skips Phase 4 and runs the decision gate plus rework for cycle 4. Blake K1 (env-value redaction) and re-raises K2/P6/P7 discarded in ledger.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: B1 (high), P1-P5 (medium), L2-L3 (low) from review-4.md

**Choice**: Auto-fix via [D4] tasks 21 (B1), 22 (P1,P2,L2), 23 (P3,P4,P5,L3) at sonnet

**Rationale**: Cycle 4 < rework_cap 5. Fixes are additive or local to one function; no signature/schema change; no CRITICAL so no rework design. P1/P2: Bob's reading (empty preview per task-19 contract) chosen over documenting the sk- fallback, as it also closes the leak. P3/L3: Bob's reading (reject an invalid date in the selected year) chosen over Eve's.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: L4: Cannot statically verify the suite/lint/type/build at 82a12fe

**Choice**: Discard

**Rationale**: Resolved: last-verification.json at 82a12fe records all five commands exit 0.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: The required normalized-event tailing interface is absent; `events/tail.py` only provides writing and raw-stream decoding

**Choice**: discarded

**Rationale**: No Phase 4 source task or specified callable requires a normalized-file reader here. P06-T01 of the accepted source plan owns log tailing; the accepted design explicitly assigns normalized tailing to PRD 00008. This phase provides record conversion, the writer and raw-first decoder.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Cannot statically verify: full `uv run pytest` at 0228eb0 (the context says "currently running"; tasks 22 and 23 record no suite output, including the DST time-only banner tests)

**Choice**: resolved by current review verification

**Rationale**: Resolved by the current review session: uv run pytest -q at 0228eb00f39a3152a008351212fee3b01603a646 exited 0 with 3003 passed, 0 failed, 0 skipped. Bob had read the context before the foreground suite completed.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: 29 touched test(s) pass against the pre-change code: test_banner_reset_never_skips_invalid_year_to_later_leap_day, test_banner_applies_after_credible_then_resetless_rejection, test_banner_reset_resolves_dated_banner_in_anchor_local_year +23 more

**Choice**: discarded

**Rationale**: Behavior-preserving date construction and explicit coverage backfill intentionally pass on the base. Task 23 explicitly required pinning rejected(R)->rejected(no reset)->banner without changing behavior. Existing date parameters plus the leap-day-already-passed negative case also pass on base; the non-leap-anchor case fails. Replay found 10 changed cases failing, not a tautological assertion.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: 1 touched test(s) pass against the pre-change code: test_text_sanitization_redacts_assignment_with_long_sensitive_key

**Choice**: discarded

**Rationale**: The suffix=10 parameter is a pre-existing behavior guard; suffix=65 and suffix=1000 fail against the base. The computed replay groups parameter cases under one function name. Passing the short-key control is intentional.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Ledger auto-dismissal incorrectly folded nested environment objects into the earlier configured-overlay decision

**Choice**: reinstate C5-13 before cap classification

**Rationale**: sanitize_json({environment:{CONFIG_VALUE:synthetic-private-value}}) preserves the value. The cycle-4 rationale discusses configured overlay validation and free-text matching; it does not cover a structured environment object received as normalized payload. The original raw finding and the automatic dismissal are retained for audit.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: Required independent doubt voice under the autocodex host role swap

**Choice**: Run Bob as fresh external Claude Opus; preserve Fable unavailability

**Rationale**: 15 tasks have codex implementation evidence. No native Fable model is exposed; no Eve dispatch is claimed. The user-authorized Bob substitution supplied the complete consensus and D1-D5 doubt/de-slop lenses on claude-opus-5-5, independently of native Codex Alice and Blake. Carl refused nested dispatch with exit 3; no guard was bypassed.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: The undocumented `allow_explicit_model` option bypasses the required agent-tier model resolution contract

**Choice**: discarded by settled-decisions ledger

**Rationale**: The accepted cycle-1/3 decision explicitly allows opt-in model literals; the Blake ledger matcher correctly retained that prior decision.

### [autonomous] 2026-10-02T11:22:57Z

**Decision**: The required full failure-session fixture matrix is represented by unrelated one-line terminal records, so stateful rate-limit, connectivity, permission, and terminal-failure sessions are not covered

**Choice**: discarded by settled-decisions ledger

**Rationale**: Class coverage is represented one class per line and sequence behavior is tested in the decoder/rate-limit modules; the accepted cycle-3/4 fixture-layout decision remains in force.

### [deferred] 2026-10-02T11:22:57Z

**Decision**: The prompt is the last positional argument with no `--` before it, so a prompt starting with "-" would be parsed as a CLI option

**Choice**: Defer leading-hyphen prompt hardening

**Rationale**: Exact argv matches the characterized runner and this phase's accepted launch contract; the built-in workflow prompts begin with '/'. General arbitrary leading-hyphen prompt handling is outside the current exact-port contract. Preserve the limitation for batch-end review rather than change argv without that contract decision.

### [deferred] 2026-10-02T11:22:57Z

**Decision**: Failure classification is substring-based and can misclassify benign text

**Choice**: Defer classifier hardening

**Rationale**: Marker substrings are the characterized classification contract; replacing them needs real failure captures (PRD scope question), not a blind rewrite.

### [deferred] 2026-10-02T11:22:57Z

**Decision**: ruff check . and ruff format --check . fail on untracked docs/dev/project-management probe scripts after the dev/local -> docs/dev migration (no longer gitignored or ruff-excluded)

**Choice**: Defer repo hygiene

**Rationale**: Not PRD code; src/tests are clean. Needs a decision: ruff extend-exclude docs/dev, or prune/track the probe scripts.

### [deferred] 2026-10-02T11:22:57Z

**Decision**: `_preview` still preserves a whitespace-free truncated window unless it contains `sk-`, contrary to Task 22’s unconditional empty-preview contract; replace the conditional with `end = 0` and update the older test that expects an `x` preview.

**Choice**: deferred

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-02T11:22:57Z

**Decision**: The reducer binds identity only on start or terminal events, allowing earlier observations from another session to contaminate a successful summary and its usage

**Choice**: deferred

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-02T11:22:57Z

**Decision**: Failure classification misses standard authentication, rate-limit, and connectivity forms such as expired OAuth tokens, HTTP 429, and ECONNRESET, classifying them as generic agent failures

**Choice**: deferred

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-02T11:22:57Z

**Decision**: The provider-neutral events layer imports both the downstream driver layer and runtime persistence, reversing the mandated `events <- drivers <- runtime` dependency direction

**Choice**: deferred

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-02T11:22:57Z

**Decision**: Claude process conformance exercises only normal completion and does not verify the specified live TERM/KILL response

**Choice**: deferred

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-02T11:22:57Z

**Decision**: Authorization values that use a scheme other than Bearer still leak. sanitize_text("Authorization: Basic dXNlcjpwYXNzd29yZA==") gives "Authorization: [REDACTED] dXNlcjpwYXNzd29yZA==": only the scheme word is redacted. The same happens with `token ghp_…` and `Digest …`. This gap already existed at 82a12fe, but the diff rewrote this exact clause as `(?:bearer\s+)?`. No test covers it

**Choice**: deferred

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-02T11:22:57Z

**Decision**: Once `continue` became `return None`, the `for … else: return None` branch can no longer run: the year+1 pass either raises or builds a time later than `local`. The loop can become one constructor plus `replace(year=local.year + 1)`, which raises ValueError for Feb 29 and gives the same results

**Choice**: deferred

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-02T11:22:57Z

**Decision**: JSON keys with escaped quotes inside raw previews are not redacted. In `{\"apiKey\": \"v\"}` the key is followed by a backslash, so `["']?\s*[:=]` fails and `v` survives in raw.unknown previews (claude.py:151, tail.py:152). This already existed at 82a12fe. It matters most when stream records change shape and many records fall back to raw.unknown

**Choice**: deferred

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-02T11:22:57Z

**Decision**: The protocol doc describes the preview wrongly. It says "512-byte window", but the window is _PREVIEW_WINDOW_BYTES = 4096 (or the frame-buffer cap if smaller). It says a trailing CR "never" reaches the preview, but finish() on an unterminated `…\r` frame keeps it (trim_cr needs `terminated`)

**Choice**: deferred

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-02T11:22:57Z

**Decision**: Two asserts are redundant: each `not any(...)` / `"ABCDE" not in preview` check follows `assert preview == ""` and can never add anything

**Choice**: deferred

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-02T11:22:57Z

**Decision**: Normalized sanitization preserves arbitrary values nested under `environment`, so credentials with non-sensitive variable names can leak into normalized logs

**Choice**: deferred

**Rationale**: rework cap reached with this finding unresolved
