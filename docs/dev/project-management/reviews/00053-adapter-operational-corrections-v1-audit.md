# Decision Audit Log: 00053-adapter-operational-corrections-v1

PRD: `00053-adapter-operational-corrections-v1.md`
Started: 2026-10-14T19:55:07Z
Completed: 2026-10-14T19:55:07Z
Autonomous: 119  |  Deferred: 8  |  Doubts: 0

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 00053 design and task routing

**Choice**: Use reviewed minimal adapter-edge design and four logical opus tasks

**Rationale**: Three design dispatches passed; non-blockers retained. Risk eligibility-split exemption; no inference preflight under operator fixture/fake scope

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Native outcome task exceeded test-author read budget

**Choice**: Split task 1 into sequential lane task 5 and diagnostic task 6; task 1 now verifies split completion

**Rationale**: First Tess stopped without edits at 134661 input bytes; narrowed self-contained prompts preserve full pipeline and original acceptance

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Original task1 aborted before implementation and was split into task5 lanes/task6 diagnostics

**Choice**: After both replacement tasks complete, verify combined narrow contract and mark original coordination umbrella completed through task-set-status; retain aborted attempt without fabricating a successful implementation attempt

**Rationale**: Installed task-splitting procedure permits original completed/blocked carrier; all substantive implementation provenance remains in split tasks

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Numeric diagnostics now need "HTTP", "HTTP status", "status code" or "error code" (src/ovcaq/drivers/codex_events.py:301), so Codex's own status wording falls to UNKNOWN. I ran `classify_failure` on "unexpected status 503 Service Unavailable", "unexpected status 502 Bad Gateway", "unexpected status 403 Forbidden" and "exceeded retry limit, last status: 429 Too Many Requests", and all four return `unknown`. The old code returned connectivity, permission and rate_limit for these. Both prefixes are confirmed as strings in the installed codex 0.162.1 binary; the "503 Service Unavailable" suffix is my guess at how Codex renders the code. Effect: 502/503 skip the bounded connectivity WAIT and get an immediate died-retry and then PARK, and 403 retries instead of halting for the operator. The PRD allows "HTTP/status/error-code" context, and "status 503" is a status context. Fix: accept a bare `status` (e.g. `(?:http(?: status)? | status(?: code)? | error code)`) and add both Codex spellings as literal positives in tests/drivers/test_adapter_failure_classes.py:55

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The docs say an empty host PATH "searches the current directory" for both native adapters, but `ClaudeDriver.probe` passes `path=""` to `shutil.which`, which returns None (checked on Python 3.13). tests/runtime/test_adapter_health.py:263 asserts unhealthy. So the Claude probe treats an empty host PATH as unhealthy, while only the Codex subprocess probe searches the current directory. Fix the sentence to say this

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The "fixture" case in `test_claude_probe_keeps_empty_host_path_unhealthy` puts the executable in tmp_path/bin while the working directory is tmp_path. It cannot tell the conservative empty-PATH handling apart from a current-directory search. Put the executable in the working directory to pin the choice

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Only the `continue` at src/ovcaq/drivers/codex.py:383 is pinned by tests. The unfinished-only `started_lanes` filter at src/ovcaq/drivers/codex.py:372 is not: dropping it still suppresses LANE_FAILED through the `continue`, and no test asserts the RAW_UNKNOWN that the design requires for a close status on a completed lane (I ran it: completed then shutdown gives `raw.unknown`; that the tests miss its removal comes from reading them, not a run). Add a RAW_UNKNOWN assertion on `closed` in `test_completed_lane_remains_completed_after_close_status` (tests/drivers/test_adapter_outcomes.py:89)

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The Phase 0 acceptance command (`tests/drivers/test_adapter_outcomes.py tests/drivers/test_codex_decode_terminals.py`) does not test the capacity WAIT and retry exhaustion, the unrelated-number negatives, or HTTP positives that rely on the number alone. Those tests live in tests/drivers/test_adapter_failure_classes.py, a file the PRD does not list, so the stated acceptance run passes without proving them.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The normal sequence spawn → wait(completed) → close_agent(shutdown) now emits raw.unknown for every completed lane, which sets the TUI raw-evidence flag (tui/model.py:548). Late running/errored/completed updates for a finished lane are dropped with no trace (codex.py:383). No test asserts either outcome, so the design's "raw-unknown evidence" rule is unpinned

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `_ResolvedModelCodexDriver.build_launch` copies `_ResolvedModelClaudeDriver.build_launch` line for line. A module helper `_tier_request(settings, request)` would leave each override as one line: `return super().build_launch(_tier_request(self._settings, request))`

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 40 of the 49 new outcome test cases pass on the pre-change code and repeat existing tests: test_codex_rework_decode.py:201 already covers an unfinished lane failing on close, and test_codex_decode_lanes.py:257 covers an unstarted receiver staying raw. The 3-way receiver-name parametrization exercises no extra code path, and `test_non_json_output_retains_raw_unknown` has nothing to do with lanes

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The `continue` at codex.py:383 freezes failed lanes as well as completed ones, and silently drops late `errored`/`running`/`completed` updates with no raw-unknown evidence (I ran it: completed then errored gives only `tool.completed`, while completed then shutdown gives `raw.unknown`). docs/driver-protocol.md:242 describes only completed lanes. Document that failed lanes also stay terminal, or emit raw evidence consistently

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The new `authentication failed` pattern goes beyond "retain existing word diagnostics". The authentication fixture already classifies through "invalid credentials", and the new pattern widens the authentication HALT to messages like "MCP server authentication failed"

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: A normal Codex sub-agent run (spawn running, then wait completed, then close_agent shutdown) now emits `raw.unknown` on every close of a completed lane. I confirmed this with a real decode run. It sets the TUI's raw-evidence flag (src/ovcaq/tui/model.py:548). The doc at docs/driver-protocol.md:244 says only unstarted receivers and missing attribution produce raw unknown evidence.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `test_configured_factory_rejects_unknown_or_invalid_options` re-tests `CodexDriver.__init__`, which the new subclass does not override, and passes on the pre-change code. Its `pytest.raises(ValueError)` also accepts `ConfigurationError` (a ValueError subclass) raised by config parsing, so it can pass for the wrong reason

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Numeric diagnostics now need "HTTP", "HTTP status", "status code" or "error code" (src/ovcaq/drivers/codex_events.py:301), so Codex's own status wording falls to UNKNOWN. I ran `classify_failure` on "unexpected status 503 Service Unavailable", "unexpected status 502 Bad Gateway", "unexpected status 403 Forbidden" and "exceeded retry limit, last status: 429 Too Many Requests", and all four return `unknown`. The old code returned connectivity, permission and rate_limit for these. Both prefixes are confirmed as strings in the installed codex 0.162.1 binary; the "503 Service Unavailable" suffix is my guess at how Codex renders the code. Effect: 502/503 skip the bounded connectivity WAIT and get an immediate died-retry and then PARK, and 403 retries instead of halting for the operator. The PRD allows "HTTP/status/error-code" context, and "status 503" is a status context. Fix: accept a bare `status` (e.g. `(?:http(?: status)? | status(?: code)? | error code)`) and add both Codex spellings as literal positives in tests/drivers/test_adapter_failure_classes.py:55

**Recommendation**: Bounded provider-edge matching repair directly required by PRD; preserve ordinary-count negatives and unchanged precedence.

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The docs say an empty host PATH "searches the current directory" for both native adapters, but `ClaudeDriver.probe` passes `path=""` to `shutil.which`, which returns None (checked on Python 3.13). tests/runtime/test_adapter_health.py:263 asserts unhealthy. So the Claude probe treats an empty host PATH as unhealthy, while only the Codex subprocess probe searches the current directory. Fix the sentence to say this

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The "fixture" case in `test_claude_probe_keeps_empty_host_path_unhealthy` puts the executable in tmp_path/bin while the working directory is tmp_path. It cannot tell the conservative empty-PATH handling apart from a current-directory search. Put the executable in the working directory to pin the choice

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Only the `continue` at src/ovcaq/drivers/codex.py:383 is pinned by tests. The unfinished-only `started_lanes` filter at src/ovcaq/drivers/codex.py:372 is not: dropping it still suppresses LANE_FAILED through the `continue`, and no test asserts the RAW_UNKNOWN that the design requires for a close status on a completed lane (I ran it: completed then shutdown gives `raw.unknown`; that the tests miss its removal comes from reading them, not a run). Add a RAW_UNKNOWN assertion on `closed` in `test_completed_lane_remains_completed_after_close_status` (tests/drivers/test_adapter_outcomes.py:89)

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The Phase 0 acceptance command (`tests/drivers/test_adapter_outcomes.py tests/drivers/test_codex_decode_terminals.py`) does not test the capacity WAIT and retry exhaustion, the unrelated-number negatives, or HTTP positives that rely on the number alone. Those tests live in tests/drivers/test_adapter_failure_classes.py, a file the PRD does not list, so the stated acceptance run passes without proving them.

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The normal sequence spawn → wait(completed) → close_agent(shutdown) now emits raw.unknown for every completed lane, which sets the TUI raw-evidence flag (tui/model.py:548). Late running/errored/completed updates for a finished lane are dropped with no trace (codex.py:383). No test asserts either outcome, so the design's "raw-unknown evidence" rule is unpinned

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `_ResolvedModelCodexDriver.build_launch` copies `_ResolvedModelClaudeDriver.build_launch` line for line. A module helper `_tier_request(settings, request)` would leave each override as one line: `return super().build_launch(_tier_request(self._settings, request))`

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 40 of the 49 new outcome test cases pass on the pre-change code and repeat existing tests: test_codex_rework_decode.py:201 already covers an unfinished lane failing on close, and test_codex_decode_lanes.py:257 covers an unstarted receiver staying raw. The 3-way receiver-name parametrization exercises no extra code path, and `test_non_json_output_retains_raw_unknown` has nothing to do with lanes

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The `continue` at codex.py:383 freezes failed lanes as well as completed ones, and silently drops late `errored`/`running`/`completed` updates with no raw-unknown evidence (I ran it: completed then errored gives only `tool.completed`, while completed then shutdown gives `raw.unknown`). docs/driver-protocol.md:242 describes only completed lanes. Document that failed lanes also stay terminal, or emit raw evidence consistently

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `_ResolvedModelCodexDriver.build_launch` is identical to `_ResolvedModelClaudeDriver.build_launch` (inverse tier map plus `replace`). A shared module function such as `_tier_key_request(settings, request)` called by both overrides would remove the copy. The design asked for mirroring, so this is low

**Choice**: discard

**Rationale**: Duplicate of R7: both cite the identical inverse-tier overrides. R7 is fixed; no second task is needed. Raw findings remain preserved.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The new `authentication failed` pattern goes beyond "retain existing word diagnostics". The authentication fixture already classifies through "invalid credentials", and the new pattern widens the authentication HALT to messages like "MCP server authentication failed"

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: A normal Codex sub-agent run (spawn running, then wait completed, then close_agent shutdown) now emits `raw.unknown` on every close of a completed lane. I confirmed this with a real decode run. It sets the TUI's raw-evidence flag (src/ovcaq/tui/model.py:548). The doc at docs/driver-protocol.md:244 says only unstarted receivers and missing attribution produce raw unknown evidence.

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `test_configured_factory_rejects_unknown_or_invalid_options` re-tests `CodexDriver.__init__`, which the new subclass does not override, and passes on the pre-change code. Its `pytest.raises(ValueError)` also accepts `ConfigurationError` (a ValueError subclass) raised by config parsing, so it can pass for the wrong reason

**Choice**: fix

**Rationale**: Bounded in-scope correction; complete verbatim finding retained for rework.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Cannot statically verify: phase-2 exit gate (pytest, ruff check, ruff format --check, mypy, uv build). The test gate reports exit 0 but gives no counts

**Choice**: discard

**Rationale**: Resolved by current-HEAD verification: 7165 passed, 0 failed, 0 skipped; sync, Ruff lint/format, mypy and build all exit 0. See 00053-review-1-verification.json. Bob VERIFY command uses &&, so not queued: command shape; each required gate already ran separately.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The Codex probe runs in the caller's working directory, while the launch runs in request.root. A relative command or an empty-PATH lookup can therefore succeed in the probe and fail at launch, or the reverse (existing behavior)

**Choice**: defer

**Rationale**: Known pre-existing caller/request-root cwd disagreement. PRD explicitly excludes probe descendant/ownership redesign and preserves Codex probe behavior. Defer outside this repair; do not change the current scope.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 33 touched test(s) pass against the pre-change code: test_numeric_diagnostics_require_an_explicit_status_or_error_context +27 more

**Choice**: discard

**Rationale**: Existing valid HTTP/word diagnostics, precedence and reset parsing are compatibility controls the PRD explicitly requires retaining. New false-positive negatives and capacity cases fail at base; literal oracle expectations are independently pinned. Passing preservation cases are not tautologies.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 40 touched test(s) pass against the pre-change code: test_unfinished_lane_fails_after_close_status +34 more

**Choice**: discard

**Rationale**: New completed-lane regressions fail at base; running/unstarted/unknown preservation cases deliberately cover unchanged behavior. R8 separately fixes actual redundant test padding; it is not silently dismissed by this characterization decision.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 10 touched test(s) pass against the pre-change code: test_native_failure_emits_classified_terminal_with_receipt_identity +4 more

**Choice**: discard

**Rationale**: Existing terminal fixture outcomes remain unchanged; only the independent literal oracle replaces a production-derived expected class. Such an oracle correction is expected to pass base.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 7 touched test(s) pass against the pre-change code: test_failure_classification_uses_documented_precedence +1 more

**Choice**: discard

**Rationale**: Existing failure fixtures and reset behavior are compatibility controls; independent literal oracles replace classifier-derived expectations without requiring changed production outcomes.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 81 touched test(s) pass against the pre-change code: test_launch_has_exact_order_and_omits_unconfigured_flags +75 more

**Choice**: discard

**Rationale**: Direct tier precedence, explicit-model validation, safe flags and ordinary config remain unchanged by contract; supervised collision regressions fail at base. R13 separately fixes the broad factory exception check.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 14 touched test(s) pass against the pre-change code: test_native_diagnostics_have_independent_failure_classification +8 more

**Choice**: discard

**Rationale**: Existing diagnostic fixture is deliberately unchanged, with expected CONNECTIVITY now a literal independent oracle. Passing at base is required characterization.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 21 touched test(s) pass against the pre-change code: test_probe_finds_executable_available_only_on_overlay_path, test_probe_rejects_absolute_command_that_is_not_an_executable_file +15 more

**Choice**: discard

**Rationale**: Codex effective PATH already behaved correctly and PRD requires regression rather than forced production edits; inherited/absolute/default health controls preserve behavior. Claude overlay failures fail at base. R3 separately repairs the empty-PATH test discrimination.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 1 touched test(s) pass against the pre-change code: test_configured_supervisor_launches_each_selected_literal_model_and_effort

**Choice**: discard

**Rationale**: This parametrized test includes unchanged non-colliding routes as compatibility controls; colliding Codex route cases fail at base. A passing invocation of the same test function does not negate its failing cases.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Codex's HTTP client (reqwest) reports status errors as "HTTP status client error (429 Too Many Requests) for url (...)". The new numeric check still returns `unknown` for that form. I ran `classify_failure` on that string, on "HTTP status server error (503 Service Unavailable) for url (...)", on "HTTP status client error (403 Forbidden) ..." and on "HTTP/1.1 503 Service Unavailable", and all four give `unknown`. The pre-change code returned rate_limit, connectivity and permission for them. Both "HTTP status client error" and "HTTP status server error" are present as strings in the installed codex-cli 0.162.1 binary (confirmed with `rg -a`). Whether they ever reach a `turn.failed` message is my guess, not something I checked. If they do, a real 429 skips the rate-limit wait and a real 502/503 skips the bounded connectivity WAIT, just like the cycle-1 HIGH. This also contradicts docs/driver-protocol.md:271 ("require HTTP, status or error-code context"). Fix: also accept the code when the standard reason phrase follows it (e.g. `(?:403 forbidden | 429 too many requests | 502 bad gateway | 503 service unavailable)`). Add the reqwest and HTTP/1.1 forms as literal positives in tests/drivers/test_adapter_failure_classes.py:63, and keep the ordinary-count negatives

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `INVALID_OPTIONS` was moved up to module level so the now-deleted factory test could share it. It has a single user again (`test_constructor_rejects_unknown_or_invalid_options`). Inline it back into that test's `@pytest.mark.parametrize`, so the only change left in that test is the `raised.type is ValueError` line

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The CHANGELOG PATH entry says the change checks "both native adapters' executables" and preserves "standard missing/empty host PATH lookup". In fact only the Claude probe changed (Codex already used the merged environment). With an empty host PATH, the Claude probe is unhealthy while the Codex probe searches the current directory, which docs/driver-protocol.md:37 now says correctly. Reword the entry to say the fix is for Claude and to name that split

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `classify_failure` now collapses whitespace (`" ".join(detail.split())`), so "Rate\tlimit reached" becomes rate_limit. The pre-change code returned unknown for it. That widens matching beyond "retain existing word diagnostics", and neither the CHANGELOG nor the protocol doc mentions it. The test `test_native_word_diagnostics_retain_case_and_whitespace_variants` calls it "retain" even though the whitespace case is new behavior. Either document the widening and rename the test, or drop line 300 and the tab case

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: No supervisor-level regression covers the Claude model-collision path. The Claude edge wrapper behaves correctly: I checked directly that `{default: o3, o3: o3-pro, x: o3}` launches `o3` and `o3-pro`. But tests/runtime/test_adapter_launch_routing.py runs only the Codex fake through the supervisor, so a regression in `_ResolvedModelClaudeDriver` would go unnoticed.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `assert retries.rate_limit == 0` can never fail. It checks the frozen `RetryState` the test built with `rate_limit=0`, and `decide` cannot change it (src/ovcaq/runtime/decision.py:84). Lines 200-201 already pin the non-rate-limit path

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: CHANGELOG says "preserving standard missing ... host PATH lookup", but the Claude probe changed. With no host PATH it now falls back to `os.defpath` (`/bin:/usr/bin`, src/ovcaq/drivers/claude.py:82). The old `shutil.which(command)` used `CS_PATH` (`/usr/bin:/bin:/usr/sbin:/sbin` here, confirmed with `getconf PATH` and the stdlib source). The new value matches the subprocess spawn, as the design asks, so only the wording is wrong

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The test for an absent host PATH probes `sh`, which is in both `os.defpath` and `CS_PATH`. It cannot tell the design's spawn-matching `os.defpath` fallback from the old `CS_PATH` one, so going back to `shutil.which(command, path=None)` would still pass (found by reading, not run)

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The new HTTP-version prefix `http/\d+\.\d+` (src/ovcaq/drivers/codex_events.py:301) needs a minor version. So `HTTP/1.1 503` classifies, but HTTP/2 and HTTP/3 status lines do not, because they are written with no minor version. I ran `classify_failure`: "HTTP/2 503 Service Unavailable" and "HTTP/2 429" both return `unknown`, and the pre-change code returned connectivity and rate_limit. This also contradicts the CHANGELOG.md:43 claim that "HTTP-version status diagnostics" are recognized. If such a line reaches a Codex `turn.failed` (a guess, the same guess behind the HTTP/1.1 fix), a 503 skips the bounded connectivity WAIT and goes to died-retry then PARK, and a 429 retries instead of halting. Fix: make the minor version optional (`http(?:/\d+(?:\.\d+)?| status…)`) and add the "HTTP/2 503 Service Unavailable" and "HTTP/2 429 Too Many Requests" positives at tests/drivers/test_adapter_failure_classes.py:103. "HTTP Error 503: Service Unavailable" also returns `unknown`; that is lower likelihood, so decide whether it is in scope

**Choice**: auto-fixed

**Rationale**: Operator authorized Fix all 6, re-review on 2026-10-12; implemented by task 15. Fresh full provider review required before finalization.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: CHANGELOG.md:43 reads as a separate fix, but it only patches this PRD's own unreleased change at CHANGELOG.md:46. The reqwest and HTTP/1.1 forms always classified before this PRD (bare numbers matched), and "literal whitespace in word diagnostics" describes something that did not change. Fold the user-visible part into CHANGELOG.md:46 and drop line 43

**Choice**: auto-fixed

**Rationale**: Operator authorized Fix all 6, re-review on 2026-10-12; implemented by task 16. Fresh full provider review required before finalization.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The new helper `_tier_request` is named with a noun phrase. The coding-style rule wants action-named functions to start with a verb. Rename it to, for example, `_map_model_to_tier` (both call sites are at src/ovcaq/drivers/edge.py:27 and src/ovcaq/drivers/edge.py:34)

**Choice**: auto-fixed

**Rationale**: Operator authorized Fix all 6, re-review on 2026-10-12; implemented by task 15. Fresh full provider review required before finalization.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Every routine close of a completed lane (wait completed, then close_agent shutdown) now emits raw.unknown. The TUI then marks ordinary multi-agent sessions as having raw evidence. Late running or completed updates for terminal lanes emit nothing, so the two cases behave differently. This is documented and tested as intended, but it adds noise.

**Choice**: discard

**Rationale**: Previously settled and intentionally pinned raw-evidence behavior; no contract change authorized.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The Claude routing cases set every phase effort to "high" and give no reason. Config accepts low/medium/high/xhigh for any agent (src/ovcaq/config.py:364), and ClaudeDriver passes effort through unchanged, so Claude effort pass-through is only tested with one value

**Choice**: auto-fixed

**Rationale**: Operator authorized Fix all 6, re-review on 2026-10-12; implemented by task 17. Fresh full provider review required before finalization.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The protocol doc says completed and failed lanes stay terminal "under all late receiver updates". But identity eviction removes terminal lanes first (src/ovcaq/drivers/codex.py:413). Once a lane is evicted, a late running update for it emits `lane.started` again

**Choice**: auto-fixed

**Rationale**: Operator authorized Fix all 6, re-review on 2026-10-12; implemented by task 16. Fresh full provider review required before finalization.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The CHANGELOG entry about reqwest/HTTP-version forms and literal whitespace describes no change from the pre-PRD base. Bare codes already matched those forms there, and whitespace was already literal. The entry records rework done inside this PRD and overlaps the numeric-context entry three lines below

**Choice**: discard

**Rationale**: Duplicate of R2 changelog finding; one distinct repair request, both raw outputs preserved.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `configured_driver` is annotated `-> CodexDriver` but returns `build_driver(...)`, which is typed `AgentDriver`. mypy only checks src/ovcaq, so nothing reports the mismatch

**Choice**: auto-fixed

**Rationale**: Operator authorized Fix all 6, re-review on 2026-10-12; implemented by task 17. Fresh full provider review required before finalization.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The bare word "status" counts as an HTTP context, so ordinary counts after it still get a failure class. Confirmed: "status 401 files processed" and "exit status 401" both return `authentication`. Inside the PRD's wording, but no negative control is pinned for it

**Choice**: defer

**Rationale**: Existing mixed diagnostic-prefix/count precedence limitation; requires later explicit contract.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: A late update for a lane that already finished is now dropped with no `raw_unknown` record, while a late close status for the same lane does emit one. So a contradictory late "errored" after "completed" leaves no trace in the normalized stream; only raw.jsonl keeps it. `item_lanes(started_lanes=None)` also keeps its optional default: a caller that leaves it out never fails a lane on close (review R1 asked for it to be required)

**Choice**: discard

**Rationale**: Existing remembered-terminal identity contract; raw session evidence survives. Production decoder supplies unfinished identities; no new required helper signature.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: tests/runtime/test_adapter_launch_routing.py:30 re-implements the runpy Claude wrapper from tests/runtime/test_supervisor_adapters.py:44. The wrapper rebinds `fake_codex.workflow.__globals__['__file__']` to the Claude fixture, and the new copy adds only an `edge['emit_invocation'](sys.argv[1:])` call. That leaves two copies of a hack tied to fake_codex.py internals, and they will drift apart. Keep one wrapper builder in test_supervisor_adapters.py that always emits the invocation (Codex `main()` already emits it unconditionally) and call it from both files

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: CHANGELOG.md:46 still says completed and failed Codex receiver lanes stay terminal "under late updates", with no qualifier. Task 16 fixed this same overclaim in docs/driver-protocol.md:243, which now says "Remembered completed and failed lanes". Lanes stop being remembered once they are evicted (src/ovcaq/drivers/codex.py:413 evicts finished identities first, at 4096 identities). After that, a late `running` update starts the lane again. Add "remembered" to the CHANGELOG entry so it matches the protocol doc

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: docs/driver-protocol.md:185 says "the driver preserves that resolved value", but only drivers built by `build_driver` do that. A `CodexDriver` constructed directly and passed to `Supervisor` (as in tests/runtime/test_rework_thread_conflict.py:108) still remaps a colliding value through tier-key precedence. Reword to "the driver built by `build_driver` preserves that resolved value"

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: CHANGELOG.md:45 puts two fixes in one entry. Its clause "retry model capacity as connectivity through bounded WAIT/retry exhaustion" does not read as a sentence, and "reqwest" is implementation jargon. Split it into a numeric-context entry and a separate entry: "classify 'Selected model is at capacity' as connectivity so it gets bounded WAIT retries instead of rate-limit handling"

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: tests/runtime/test_adapter_health.py:90 runs `command_name` over three names ("fixture-agent-health", "overlay-runner", "queue-worker"). In both probes all three take the same code path, so there are 6 cases where 2 would do. R8 removed the same kind of padding from test_adapter_outcomes.py. Keep one name

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Five actionable post-repair findings R1/R2/R5/R6/R7

**Choice**: operator-authorized

**Rationale**: Operator said "fix all five and re-review". One bounded repair pass via tasks 18-20, then fresh full provider review; cycle/cap remain 2. Scope: reports/00053-postrepair-repair-authorization.md.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Pat18: workflow_fixture naming; rename to a verb-led helper name.

**Choice**: carry-to-review

**Rationale**: Operator approved task18/20 prompt export and read-only reviews. Both original closures resolved; new LOW carried to fresh full review. No additional repair authorized. Evidence: reports/00053-approved-task-reviews-handoff.md.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Task 20 stopped passing a name to `fake_executable`, so its `name: str = "fixture-agent-health"` parameter is now dead: all 9 callers use the default. This file is new in this PRD, so the leftover comes from the repair itself. Fix: drop the parameter and write `executable = directory / "fixture-agent-health"`

**Choice**: operator-decision-required

**Rationale**: Unused fake_executable name parameter confirmed; bounded authorization prohibits further repairs.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Carried Pat18 LOW: `workflow_fixture` writes the Claude wrapper file and returns its path, but its name is a noun. Action functions should start with a verb, e.g. `write_workflow_fixture` (call sites tests/runtime/test_supervisor_adapters.py:56 and tests/runtime/test_adapter_launch_routing.py:33). The new helpers `configured_workflow` (tests/runtime/test_adapter_launch_routing.py:24) and `configured_driver` (tests/drivers/test_codex_launch.py:30) have the same shape. Against renaming: the older helpers in the same file (`adapter_harness`, `workflow_agent`) also use nouns, so a rename would break from the file's current style

**Choice**: operator-decision-required

**Rationale**: Carried action-helper naming finding confirmed; further cleanup requires operator authorization.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The numeric grammar only accepts `HTTP[/x.y]`, `HTTP status [client|server error (]`, `status [code][:]` and `error code[:]`. Other explicit HTTP or error forms used to classify through the bare number and now return `unknown`. Confirmed by running the classifier: "HTTP Error 503: Service Unavailable" gives unknown (was connectivity), "HTTP Error 429: Too Many Requests" gives unknown (was rate_limit), "Error 403: Forbidden" gives unknown (was permission), "status=429" gives unknown. The tests pin `status=429` and `Error 429:` as UNKNOWN. Codex's own Rust forms (`unexpected status N ...`, `last status: N`, reqwest `HTTP status ... error (N ...)`) are covered, so the risk is limited to non-native formats.

**Choice**: defer

**Rationale**: Additional non-native diagnostic grammar needs explicit scope; preserve pinned unknown forms and current production behavior.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: With an empty host PATH, the Claude probe reports unhealthy because `shutil.which(path="")` returns None. The launch would still find the command in the project root, because subprocess treats an empty PATH as the current directory. The Codex probe reports healthy in the same environment, so the two adapters disagree. This is documented as intentional and fails safe (false unhealthy), but it does not "resolve under the launch environment".

**Choice**: settled-deferral

**Rationale**: Intentional pinned empty-PATH behavior; preserve existing directory-dependent probe/launch limitation.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Flaky test: `test_installed_foreground_signals_return_shell_status_and_stop_the_driver[15]` failed once under full-suite load (returncode 1, expected 143). It passed in isolation (3/3) and in a second full run (7155 passed). Not traced to this diff, but this PRD's exit gate depends on `uv run pytest` passing.

**Choice**: defer

**Rationale**: Existing signal-test flake not traced to this PRD; isolation and second full suite passed; preserve raw evidence for separate work.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: A 16 MB binary review artifact is committed to the tracked project-management tree. This is permanent history bloat for evidence that could be regenerated or summarized.

**Choice**: discard

**Rationale**: Operator requires preserving prior raw evidence and receipts; no history/evidence cleanup authorized.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `test_claude_probe_rejects_sh_hidden_by_overlay_path` repeats the `[claude]` case of `test_probe_rejects_host_executable_hidden_by_overlay_path` (tests/runtime/test_adapter_health.py:213). Both put the command on the host PATH, use an overlay without it, and hit the same `shutil.which(..., path=overlay) is None` branch, and both fail on the base code. This is the same kind of padding task 20 removed from line 90

**Choice**: operator-decision-required

**Rationale**: Overlapping hidden-by-overlay Claude tests confirmed; retain both-provider coverage in any authorized cleanup.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Task 20 stopped passing a name to `fake_executable`, so its `name: str = "fixture-agent-health"` parameter is now dead: all 9 callers use the default. This file is new in this PRD, so the leftover comes from the repair itself. Fix: drop the parameter and write `executable = directory / "fixture-agent-health"`

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Carried Pat18 LOW: `workflow_fixture` writes the Claude wrapper file and returns its path, but its name is a noun. Action functions should start with a verb, e.g. `write_workflow_fixture` (call sites tests/runtime/test_supervisor_adapters.py:56 and tests/runtime/test_adapter_launch_routing.py:33). The new helpers `configured_workflow` (tests/runtime/test_adapter_launch_routing.py:24) and `configured_driver` (tests/drivers/test_codex_launch.py:30) have the same shape. Against renaming: the older helpers in the same file (`adapter_harness`, `workflow_agent`) also use nouns, so a rename would break from the file's current style

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `test_claude_probe_rejects_sh_hidden_by_overlay_path` repeats the `[claude]` case of `test_probe_rejects_host_executable_hidden_by_overlay_path` (tests/runtime/test_adapter_health.py:213). Both put the command on the host PATH, use an overlay without it, and hit the same `shutil.which(..., path=overlay) is None` branch, and both fail on the base code. This is the same kind of padding task 20 removed from line 90

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: R1/R2/R7 in fresh five-repair review

**Choice**: Operator approved bounded repair of all three findings

**Rationale**: User replied yes, approved on 2026-10-12; preserve cycle/cap=2, all evidence and settled decisions; fresh review required after work, no further repairs/finalization authorized.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: R1 regex backtracking; R2/R8 test cleanup; R4 cache eviction

**Choice**: operator-authorized bounded recovery

**Rationale**: 2026-10-13: user approved R1 and combined R2/R8 repairs, R4 deferral, cap 3 and one fresh complete review; authorization at reports/00053-recovery-20261013/authorization.md.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The new status prefix in `classify_failure` (src/ovcaq/drivers/codex_events.py:302) ends in `\s*:?\s*`. That is two whitespace runs side by side, so a native error with "status", "HTTP" or "error code" followed by a long run of whitespace backtracks in quadratic time. Measured at HEAD: 16k spaces took 0.55 s and 64k spaces took 8.34 s. The old bare-number regex had no such run. Decode runs inline in the supervisor read loop (src/ovcaq/runtime/supervisor.py:516) on frames up to 1 MiB (src/ovcaq/events/tail.py:60). Python's `re` holds the GIL, so the watchdog cannot fire while it runs. A full 1 MiB frame extrapolates to roughly 35 minutes (a guess, not run). The trigger needs tens of thousands of whitespace characters right after the keyword, so it is unlikely to happen. Fix: use `\s*(?::\s*)?` instead. It took 1.2 ms at 64k and matched the same way on "HTTP status: 429", "status code: 429", "last status: 429", "HTTP 429" and "status=429". Also add a regression test that expects "status" + 200,000 spaces + "x" to classify as unknown

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `test_unrelated_item_type_does_not_transition_lane` (tests/drivers/test_adapter_outcomes.py:204) and `test_unrelated_event_type_does_not_transition_lane` (tests/drivers/test_adapter_outcomes.py:231) are line-for-line copies. They differ only in one `collab_record` keyword: `item_type="command_execution"` in one, `event_type="thread.started"` in the other. Merge them into one test parametrized over that keyword dict (passed as `**override`). That cuts about 24 lines and keeps the same coverage

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Test padding in a new file: `test_unrelated_item_type_does_not_transition_lane` and `test_unrelated_event_type_does_not_transition_lane` each run once per close status (interrupted, shutdown, not_found). The command_execution record and the `thread.started` record both turn into raw unknown before `item_lanes` is ever called (`item_tool` returns None because the record has no `command` field, and the decode branch has no `thread_id`). The follow-up close assertion repeats `test_unfinished_lane_fails_after_close_status`. So 6 cases run where 2 would do. Task 20 removed the same kind of padding. Fix: drop the `child_status` parametrize from both tests and use "shutdown"

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: R2 phase-2 exit gate and prior queued routing/full checks

**Choice**: resolved by fresh verification

**Rationale**: Approved runs at e75b50a: full suite 7151 passed; exact routing/supervisor queue 8 passed; sync/Ruff/format/mypy/build pass. Raw evidence retained.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: R3 diagnostic spellings auto-dismissed by an unrelated authentication-failed ledger row

**Choice**: restored for operator decision

**Rationale**: The matched reason does not cover status=429, Error 429 or HTTP error 503. Preserve the raw dismissal but reverse its disposition; no new repair authorized.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: R4-R11 passing-base replay controls

**Choice**: discarded as compatibility controls

**Rationale**: PRD explicitly preserves fixture, direct precedence, Codex PATH, reset grammar and ordinary-route behavior. Existing same-file ledger reasons still hold; 56 touched tests fail at base. All eight computed rows preserved.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: CHANGELOG.md:43 says the change will "avoid quadratic backtracking when Codex failure diagnostics contain long whitespace runs after a status prefix". That status prefix was added earlier in this same unreleased PRD (codex_events.py:300), and the pre-PRD base had no such regex. Compared with the base, users see no change. Task 16 deleted an earlier entry of the same kind ("describes no change from the pre-PRD base"). Delete this entry too. The `fix` commit type seems to have forced the entry, so a follow-up `docs` commit can remove it

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Some explicit status-code messages now classify as `unknown`. Before this change they classified correctly. Probed: `status=429`, `Error 429: Too Many Requests`, `HTTP error 503`, and bare reason-phrase forms like `429 Too Many Requests` and `503 Service Unavailable`. The spec allows numbers only in explicit HTTP/status/error-code context, and `status=429` and `Error 429:` are exactly that. Worse, tests/drivers/test_adapter_failure_classes.py:115 locks `status=429` and `Error 429:` in as `unknown`, so the wrong answer is now enforced as the expected class. Impact: a real 429 or 503 in these forms goes to the generic retry-then-PARK path instead of the bounded WAIT or rate-limit path. The native Codex forms ("unexpected status N", reqwest, HTTP/x) are covered.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Review-3 R1 changelog and R3 explicit diagnostic spellings

**Choice**: operator-authorized repair and clean-review finalization

**Rationale**: User agreed on 2026-10-13: repair both, cap 3→4 for one fresh full Alice/Blake/Bob review, normal finalization if clean. Preserve settled deferrals; no automatic new repairs/cap increases. reports/00053-cycle3-recovery-20261013/authorization.md.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: R6 fresh full verification

**Choice**: resolved by fresh verification

**Rationale**: 7202 tests passed, zero failed/skipped at badf378; all six gates pass; raw full-suite.log retained.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The protocol doc still says numeric codes "require HTTP, status or error-code context". Since task 25, bare `Error 429:` and `status=429` also count. CHANGELOG.md:45 says "HTTP/status/error context", so the two documents disagree. Change the doc to "HTTP, status or error context" to match the code and the changelog

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The ` error` branch inside the `http(...)` group of the `status` prefix can never change a result, so it is dead code. The new bare `error(?: code)?` branch already matches every string it catches, because a word boundary always sits between "http " and "error". I checked this by running both regexes on 4,288,305 generated token strings: 0 differences. Simpler version with the same behavior: `r"(?:http(?:/\d+(?:\.\d+)?| status(?: (?:client|server) error \()?)?"`, keeping line 302 as it is. "HTTP error 503" still returns connectivity through the bare `error` branch, so the `hTtP ErRoR {code}` tests keep passing

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: CHANGELOG.md:45 lists regex branch names ("equals-delimited status, bare error, HTTP error, native bare-status and HTTP-version forms"). It also restates unchanged behavior ("retain existing authentication word diagnostics and genuine rate/quota limits"). That describes the implementation, not what users see

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Review-4 R1 protocol wording, R2 redundant regex alternatives, R5 changelog wording

**Choice**: operator-authorized repairs completed; one fresh cycle-5 full review and clean-review finalization authorized

**Rationale**: Five separate I agree replies; reports/00053-cycle4-recovery-20261013/authorization.md. New actionable findings or a cap above 5 require operator disposition. Full verification remains required after host ps denial.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Only the private subclasses built by `build_driver` map a resolved model back to its tier key. A Supervisor given a plain `CodexDriver`/`ClaudeDriver` or an entry-point driver still applies tier lookup to the resolved model, so `LaunchRequest.model` stays ambiguous between tier and model. This follows the PRD's chosen edge pattern; only the CLI path is protected

**Choice**: discard

**Rationale**: Compatibility boundary required by PRD: preserve direct build_launch tier-key precedence and use the existing edge adaptation pattern. Plain-driver and third-party-driver route semantics are outside this correction; Blake explicitly acknowledges the chosen edge pattern. No new behavior or interface authorized.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: This cycle's incremental diff is 378,503 lines, and only about 1,300 of them are product code, tests and docs. The rest is committed autopilot evidence, including review diffs that git can regenerate: a 169,912-line review-diff.diff and a 16 MB review-diff-00053-postrepair-20261012.diff.gz. Each committed review diff contains the earlier cycles' diffs, so the repo grows faster every cycle

**Choice**: known

**Rationale**: KNOWN tooling limitation: historical tracked review diffs recursively include prior evidence. This belongs to external autopilot tooling, outside the adapter PRD. No historical evidence deleted; this cycle keeps its reproducible diff in docs/dev/tmp only.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Labeled status forms classify correctly, but HTTP diagnostics without a label now return `unknown` where the old bare-number match classified them. Reproduced: `429 Too Many Requests`, `503 Service Unavailable`, `HTTPS 503`, `{"status":429}`, `"statusCode": 401` and `code: 429` all give `unknown`. So a real 429 or 503 reported in one of these forms no longer gets rate-limit or connectivity WAIT handling. The PRD's "explicit HTTP/status/error-code context" rule allows this, but it narrows "genuine HTTP diagnostics", and there is no negative or positive pin for these forms

**Choice**: discard

**Rationale**: The automatic mixed-count ledger match is unrelated and is reversed. Correct disposition: previously settled bare reason phrases, JSON/SDK labels, and additional diagnostic grammar require separately specified forms/fixtures. Cycle-4 ledger explicitly excludes bare phrases and JSON labels. HTTPS and a generic code label gain no new contract. Preserve every reported example as KNOWN; no broader grammar authorized.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 111 touched test(s) pass against the pre-change code: test_numeric_diagnostics_require_an_explicit_status_or_error_context +105 more

**Choice**: discard

**Rationale**: Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 17 touched test(s) pass against the pre-change code: test_unfinished_lane_fails_after_close_status +11 more

**Choice**: discard

**Rationale**: Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 10 touched test(s) pass against the pre-change code: test_native_failure_emits_classified_terminal_with_receipt_identity +4 more

**Choice**: discard

**Rationale**: Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 7 touched test(s) pass against the pre-change code: test_failure_classification_uses_documented_precedence +1 more

**Choice**: discard

**Rationale**: Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 61 touched test(s) pass against the pre-change code: test_launch_has_exact_order_and_omits_unconfigured_flags +55 more

**Choice**: discard

**Rationale**: Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 14 touched test(s) pass against the pre-change code: test_native_diagnostics_have_independent_failure_classification +8 more

**Choice**: discard

**Rationale**: Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 18 touched test(s) pass against the pre-change code: test_probe_finds_executable_available_only_on_overlay_path, test_probe_rejects_absolute_command_that_is_not_an_executable_file, test_probe_rejects_file_without_execute_permission +12 more

**Choice**: discard

**Rationale**: Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 4 touched test(s) pass against the pre-change code: test_configured_supervisor_launches_each_selected_literal_model_and_effort

**Choice**: discard

**Rationale**: Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Cycle-5 R1/R3/R4/R5/R6 and cap 5 require operator authorization

**Choice**: fix

**Rationale**: Fix all five cycle-5 findings R1/R3/R4/R5/R6; raise rework_cap from 5 to 6; run one more full all-lens cycle 6 in a fresh session and normal finalization only if all review gates pass. New authorization supersedes earlier limits only for these repairs and cycle 6. Preserve historical evidence and settled deferrals; no broader contract changes.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The task-28 and task-19 edits left the prose wrapping uneven. docs/driver-protocol.md:274 is 103 characters long, the only long line in the file that is not a link or a table row. Line 272 also runs past the file's ~80-column wrap. Lines 186-191 break after "tier-key precedence:", which makes the next sentence look like the start of a list, and line 191 stops at "`low`,". Fix: reflow both paragraphs to ~80 columns without changing any words

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `test_authentication_is_classified_beyond_the_display_detail_limit` repeats `test_failure_classifies_full_text_before_sanitizing_and_capping_detail` (tests/drivers/test_codex_rework_decode.py:136). Both decode a failure for the same two event kinds and check that the class comes from text past the 4096-character display limit. Only the trailing word differs ("Unauthorized" vs "Rate limit reached"). No PRD feature touches this path, and the test passes on the base, so it is padding of the same kind tasks 20, 21 and 23 removed. Delete it. `json` and the `driver` fixture are still used by the capacity test

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The capacity bound test runs `connectivity_retries` 0, 1, 2 and 3. Cases 0, 1 and 2 all take the same `retries.connectivity < policy.connectivity_retries` branch (src/ovcaq/runtime/decision.py:215). Only 2 (the last WAIT) and 3 (HALT) pin the bound. Drop cases 0 and 1

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: `test_numeric_diagnostics_require_an_explicit_status_or_error_context` checks only the positive cases. The "require" half is tested by `test_unrelated_numbers_are_not_failure_diagnostics` (tests/drivers/test_adapter_failure_classes.py:156). Rename it for the rule it enforces, e.g. `test_numeric_codes_classify_with_explicit_status_or_error_context`

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: docs/driver-protocol.md:36 says both native adapters fall back to the standard default search path when the host PATH is missing. Only Claude has a test for this (`test_claude_probe_uses_default_search_path_when_host_path_is_absent`). The design says to "reproduce and regress" the existing Codex probe behavior. Parametrize the test over ("claude", "codex") and drop "claude" from its name. As I read `os.get_exec_path`, the patched `os.defpath` also steers the Codex subprocess lookup (not run)

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Routine reversible recovery and review dispositions

**Choice**: apply

**Rationale**: User-global ~/.claude/AGENTS.md Autonomy section updated 2026-10-14: own the outcome, fix supported in-scope findings, reject false positives with evidence, durably defer out-of-scope items without cosmetic/routine questions. Supersedes older ask-first skill/host prose. Every required review lens, gate, fresh-session boundary, scope and explicit cycle6 cap remains binding.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Full-suite verification blocked by inherited macOS process-inspection restriction

**Choice**: handoff

**Rationale**: Raw partial full suite retained (85 failed,3299 passed,27 errors; interrupted exit130). ps denied exit126; required escalated representative retry confirms PermissionError errno1 ps at process_identity. No product suppression or policy change. Parent directed fresh cycle6 handoff with full-suite gate explicitly pending; no claim of green completion or finalization.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: A plain `error` label counts as a numeric code context because the ` code` part is optional (`error(?: code)?`). So `Error: 401 tests passed` comes back `authentication`. That is an ordinary count after a generic error label, not the "error-code" context the PRD describes

**Choice**: discard

**Rationale**: Previously settled mixed diagnostic-prefix/count precedence limitation (cycle 2): status: 401 tests passed and error code: 503 records. Error: 401 tests passed is the same ambiguity, not a new contract. PRD preserves genuine Error 401: diagnostics; broader prose grammar requires separate specification.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: The Claude probe checks only `command[0]` against the overlay `PATH`. With a wrapper argv (for example `env claude`), it never checks that the wrapped executable exists, while the Codex probe runs the full wrapper argv. This predates the PRD, but the PRD lists wrapper argv as a probe input

**Choice**: defer to batch end

**Rationale**: Existing wrapper-inner-executable limitation: base 7819970 Claude probe already checks only command[0]. The reviewed design explicitly requires shutil.which(command, path=effective_path), not execution or parsing of arbitrary wrapper argv. Effective PATH lookup is implemented and tested. Further wrapper health semantics need a separately specified contract.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: Cannot statically verify: the Phase-2 exit gate (full `uv run pytest`) at HEAD. The settled 7202-passed run was at 93fd36f. The only run at cf48315 (`last-verification.json`) stopped with exit 130 (partial: 85 failed, 27 errors, blamed on the macOS `ps` denial), and this cycle's test gate exited 2 with no summary line. The rework since 93fd36f touches only tests and docs, and both narrow runs pass (136 passed; 2 passed), so the settled reason does not cover HEAD

**Choice**: routed to verification; passed

**Rationale**: Resolved by approved full suite at reviewed HEAD ca878006eba9e0fff0f1eb175a30557d82f8278b: uv run pytest -q --tb=line exited 0, 7199 passed, 0 failed/skipped. Sync, Ruff lint/format, mypy and build also pass. Alice independently obtained the same full-suite result.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 109 touched test(s) pass against the pre-change code: test_numeric_codes_classify_with_explicit_status_or_error_context +103 more

**Choice**: discard

**Rationale**: Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 17 touched test(s) pass against the pre-change code: test_unfinished_lane_fails_after_close_status +11 more

**Choice**: discard

**Rationale**: Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 10 touched test(s) pass against the pre-change code: test_native_failure_emits_classified_terminal_with_receipt_identity +4 more

**Choice**: discard

**Rationale**: Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 7 touched test(s) pass against the pre-change code: test_failure_classification_uses_documented_precedence +1 more

**Choice**: discard

**Rationale**: Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 61 touched test(s) pass against the pre-change code: test_launch_has_exact_order_and_omits_unconfigured_flags +55 more

**Choice**: discard

**Rationale**: Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 14 touched test(s) pass against the pre-change code: test_native_diagnostics_have_independent_failure_classification +8 more

**Choice**: discard

**Rationale**: Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 19 touched test(s) pass against the pre-change code: test_probe_finds_executable_available_only_on_overlay_path, test_probe_rejects_absolute_command_that_is_not_an_executable_file, test_probe_rejects_file_without_execute_permission +13 more

**Choice**: discard

**Rationale**: Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics.

### [autonomous] 2026-10-14T19:55:07Z

**Decision**: 4 touched test(s) pass against the pre-change code: test_configured_supervisor_launches_each_selected_literal_model_and_effort

**Choice**: discard

**Rationale**: Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics.

### [deferred] 2026-10-14T19:55:07Z

**Decision**: The Codex probe runs in the caller's working directory, while the launch runs in request.root. A relative command or an empty-PATH lookup can therefore succeed in the probe and fail at launch, or the reverse (existing behavior)

**Rationale**: Known pre-existing caller/request-root cwd disagreement; PRD preserves Codex probe behavior and excludes probe ownership redesign. Requires later approved scope; unresolved limitation retained.

### [deferred] 2026-10-14T19:55:07Z

**Decision**: The `continue` at codex.py:383 drops every native update for a lane that has already finished. codex-cli 0.162.1 ships a `resume_agent` tool ("Resume a previously closed agent by id so it can receive send_input"; I confirmed the string in the binary). So a lane can legitimately go completed → close → resume → running → errored. With the `continue`, the resumed run's running and errored updates disappear with no trace, and a later interrupt or shutdown of the resumed run becomes raw unknown instead of `lane.failed`. The pre-change code reported these. The TUI already handles a restart, because the last write wins (src/ovcaq/tui/model.py:607). The PRD only requires that close statuses do not fail a completed lane, and the unfinished-only filter at src/ovcaq/drivers/codex.py:372 already does that on its own. Fix: delete lines 383-384. Then flip `test_finished_lane_late_update_retains_only_non_lane_observations` (tests/drivers/test_adapter_outcomes.py:266) so it expects running → `lane.progress` and errored → `lane.failed`, and reword docs/driver-protocol.md:243. Confidence: the tool is confirmed; the exact `agents_states` sequence after a resume is my guess

**Rationale**: Requirements ambiguity: resume/restart generation semantics are not specified by this PRD. The existing contract deliberately freezes completed/failed identities and pins late updates. A binary tool name does not prove a native status sequence; changing this would undo reviewed stability without a fixture. Preserve for separately specified adapter lifecycle work.

### [deferred] 2026-10-14T19:55:07Z

**Decision**: A status prefix followed by an ordinary count still classifies. `status: 401 tests passed` returns `authentication` and `error code: 503 records` returns `connectivity` (confirmed by probe). The negative tests only cover counts with no status word in front.

**Rationale**: Requirements ambiguity: mixed diagnostic-prefix/ordinary-count messages need an explicit precedence contract. Existing scope requires diagnostic status contexts and ordinary count negatives; do not invent a broader prose grammar or silently change precedence. Keep the confirmed counterexamples for later specified work.

### [deferred] 2026-10-14T19:55:07Z

**Decision**: Probe and launch can disagree on relative lookups. Both probes resolve relative PATH entries and relative command paths against the supervisor's own working directory, but launch runs with `cwd=request.root`. Absolute paths and normal PATH entries are unaffected.

**Choice**: defer

**Rationale**: Existing out-of-scope relative-path/cwd limitation; probe ownership redesign excluded by PRD. New Claude citation retained.

### [deferred] 2026-10-14T19:55:07Z

**Decision**: The numeric grammar only accepts `HTTP[/x.y]`, `HTTP status [client|server error (]`, `status [code][:]` and `error code[:]`. Other explicit HTTP or error forms used to classify through the bare number and now return `unknown`. Confirmed by running the classifier: "HTTP Error 503: Service Unavailable" gives unknown (was connectivity), "HTTP Error 429: Too Many Requests" gives unknown (was rate_limit), "Error 403: Forbidden" gives unknown (was permission), "status=429" gives unknown. The tests pin `status=429` and `Error 429:` as UNKNOWN. Codex's own Rust forms (`unexpected status N ...`, `last status: N`, reqwest `HTTP status ... error (N ...)`) are covered, so the risk is limited to non-native formats.

**Rationale**: Additional non-native diagnostic grammar needs explicit scope; preserve pinned unknown forms and current production behavior. Superseded for explicit HTTP/status/error spellings by operator authorization 2026-10-13 and completed task 25; earlier deferral retained as history. Bare numbers/reason phrases gain no new contract.

### [deferred] 2026-10-14T19:55:07Z

**Decision**: Flaky test: `test_installed_foreground_signals_return_shell_status_and_stop_the_driver[15]` failed once under full-suite load (returncode 1, expected 143). It passed in isolation (3/3) and in a second full run (7155 passed). Not traced to this diff, but this PRD's exit gate depends on `uv run pytest` passing.

**Rationale**: Existing signal-test flake not traced to this PRD; isolation and second full suite passed; preserve raw evidence for separate work.

### [deferred] 2026-10-14T19:55:07Z

**Decision**: A completed lane can still turn into a failure after the identity cache fills. At 4096 entries, eviction drops finished entries first, so long sessions lose finished lanes before anything else. Reproduced: start lane `child`, complete it, decode 4096 command items, then send a late `errored` update for `child`. The decoder emits `lane.failed` for `child`, alongside the raw capacity-gap evidence. Native Codex is unlikely to send `errored` after `completed`, so the practical risk is low.

**Rationale**: Operator approved deferral on 2026-10-13: pre-existing bounded identity-cache policy; completed-lane retention after eviction needs separately scoped lifecycle work. R4 from review-2-three-repair-20261012; preserve raw capacity-gap evidence.

### [deferred] 2026-10-14T19:55:07Z

**Decision**: The Claude probe checks only `command[0]` against the overlay `PATH`. With a wrapper argv (for example `env claude`), it never checks that the wrapped executable exists, while the Codex probe runs the full wrapper argv. This predates the PRD, but the PRD lists wrapper argv as a probe input

**Rationale**: Existing wrapper-inner-executable limitation: base 7819970 Claude probe already checks only command[0]. The reviewed design explicitly requires shutil.which(command, path=effective_path), not execution or parsing of arbitrary wrapper argv. Effective PATH lookup is implemented and tested. Further wrapper health semantics need a separately specified contract.
