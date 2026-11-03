# Review Context

## Completed Tasks

| ID | Task | Status | Commit | Description | Shared with |
|----|------|--------|--------|-------------|-------------|
| 1 | Verify native outcome split completion | completed |  | Verify both split native-outcome tasks are completed and narrow tests pass; no production edits. Contract: Driver API 2, observation protocol 1, state schema 1 unchanged. Acceptance criteria: Acceptance: `uv run pytest tests/drivers/test_adapter_outcomes.py   tests/drivers/test_codex_decode_terminals.py` covers each completed/unfinished   lane status, capacity WAIT and retry exhaustion, genuine HTTP diagnostics,   unrelated numeric counts, and all failure fixtures with literal expected classes. Verify: uv run pytest -q --tb=line tests/drivers/test_adapter_outcomes.py tests/drivers/test_adapter_failure_classes.py tests/drivers/test_codex_decode_terminals.py |  |
| 2 | Preserve once-resolved supervised models | completed |  | Preserve once-resolved supervised models  Location: /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/drivers/edge.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_adapter_launch_routing.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_launch.py  Reuse: existing driver edge inverse-tier adaptation, identity flags, bounded connectivity policy and fake harnesses.  Premise: recheck each finding at execution; if already corrected, retain a regression and report it instead of forcing a production edit.  ### Contract Keep public `CodexDriver.build_launch(request: LaunchRequest) -> LaunchSpec` tier-key precedence unchanged, including explicit-model validation. Add a private `_ResolvedModelCodexDriver(CodexDriver)` in `drivers/edge.py`, mirroring `_ResolvedModelClaudeDriver`: its `build_launch` maps a configured model value back to a corresponding tier key before delegating. `build_driver` constructs this subclass for supervised routes. A resolved `o3` with tiers `{default: o3, o3: o3-pro}` must launch literal `o3`; direct `CodexDriver` given `o3` still launches `o3-pro`. The supervisor passes only selected.tiers[resolved.tier], per config.py:resolve_phase_route, so every supervised model is necessarily a configured tier value. A no-match literal cannot originate from this route; preserve public validation for any direct call rather than inventing a new explicit-model path. No provider strings or special cases enter shared runtime.  `item_lanes(item: object, started_lanes: set[str] \| None = None)` retains its signature and return shape. The set passed by `CodexDriver._item_observations` contains only remembered lane identities whose terminal flag is false. `interrupted`, `shutdown`, and `not_found` synthesize `LANE_FAILED` only for those unfinished identities; completed lanes retain their completed observation history. Unsupported terminal statuses otherwise produce raw-unknown evidence. No additional lane state or TUI policy.  `classify_failure(detail: str) -> FailureClass` keeps authentication, permission, rate-limit, connectivity, timeout, agent precedence. Numeric 401/403/429/502/503 require explicit diagnostic context such as HTTP status, status code or error code, including genuine fixture spellings. Ordinary numeric counts remain UNKNOWN. Retain meaningful existing word diagnostics; `Selected model is at capacity` becomes CONNECTIVITY, using existing bounded WAIT/retry exhaustion. Do not change `failure_reset` grammar. Fixture expectations are literal independent oracles, never derived through the production classifier.  `ClaudeDriver.probe() -> DriverHealth` uses effective environment `os.environ` overlaid by configured launch environment when calling `shutil.which(command, path=effective_path)`. Explicit empty PATH stays empty; absent PATH follows subprocess/default PATH semantics. Absolute executable paths retain existing behavior. Codex probes already spawn with `dict(os.environ) \| dict(settings.environment)`; reproduce and regress that behavior rather than changing it gratuitously. Both native adapters must fail health before supervisor spawn when command resolution is unhealthy. Fake Codex version/auth commands use the existing reviewed pin, never a live provider or a changed pin.  Details: Use real fake supervisor launch to observe literal selected model argv for colliding tier/value configuration; preserve direct Codex tier-key precedence and opt-in validation.  Acceptance criteria: Acceptance: `uv run pytest tests/runtime/test_adapter_launch_routing.py   tests/drivers/test_codex_launch.py` proves colliding tier/model values launch the   route's model through the real fake supervisor and direct tier-key precedence remains. - [ ]  Verify: uv run pytest -q --tb=line tests/runtime/test_adapter_launch_routing.py tests/drivers/test_codex_launch.py |  |
| 3 | Probe effective launch PATH and prevent unhealthy spawn | completed |  | Probe effective launch PATH and prevent unhealthy spawn  Location: /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/drivers/claude.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_adapter_health.py  Reuse: existing driver edge inverse-tier adaptation, identity flags, bounded connectivity policy and fake harnesses.  Premise: recheck each finding at execution; if already corrected, retain a regression and report it instead of forcing a production edit.  ### Contract Keep public `CodexDriver.build_launch(request: LaunchRequest) -> LaunchSpec` tier-key precedence unchanged, including explicit-model validation. Add a private `_ResolvedModelCodexDriver(CodexDriver)` in `drivers/edge.py`, mirroring `_ResolvedModelClaudeDriver`: its `build_launch` maps a configured model value back to a corresponding tier key before delegating. `build_driver` constructs this subclass for supervised routes. A resolved `o3` with tiers `{default: o3, o3: o3-pro}` must launch literal `o3`; direct `CodexDriver` given `o3` still launches `o3-pro`. The supervisor passes only selected.tiers[resolved.tier], per config.py:resolve_phase_route, so every supervised model is necessarily a configured tier value. A no-match literal cannot originate from this route; preserve public validation for any direct call rather than inventing a new explicit-model path. No provider strings or special cases enter shared runtime.  `item_lanes(item: object, started_lanes: set[str] \| None = None)` retains its signature and return shape. The set passed by `CodexDriver._item_observations` contains only remembered lane identities whose terminal flag is false. `interrupted`, `shutdown`, and `not_found` synthesize `LANE_FAILED` only for those unfinished identities; completed lanes retain their completed observation history. Unsupported terminal statuses otherwise produce raw-unknown evidence. No additional lane state or TUI policy.  `classify_failure(detail: str) -> FailureClass` keeps authentication, permission, rate-limit, connectivity, timeout, agent precedence. Numeric 401/403/429/502/503 require explicit diagnostic context such as HTTP status, status code or error code, including genuine fixture spellings. Ordinary numeric counts remain UNKNOWN. Retain meaningful existing word diagnostics; `Selected model is at capacity` becomes CONNECTIVITY, using existing bounded WAIT/retry exhaustion. Do not change `failure_reset` grammar. Fixture expectations are literal independent oracles, never derived through the production classifier.  `ClaudeDriver.probe() -> DriverHealth` uses effective environment `os.environ` overlaid by configured launch environment when calling `shutil.which(command, path=effective_path)`. Explicit empty PATH stays empty; absent PATH follows subprocess/default PATH semantics. Absolute executable paths retain existing behavior. Codex probes already spawn with `dict(os.environ) \| dict(settings.environment)`; reproduce and regress that behavior rather than changing it gratuitously. Both native adapters must fail health before supervisor spawn when command resolution is unhealthy. Fake Codex version/auth commands use the existing reviewed pin, never a live provider or a changed pin.  Details: Cover overlay-only executable, overlay hiding host executable, absolute command, missing PATH default os.defpath and empty PATH conservative unhealthy lookup, both native health failures preventing supervisor launch; Codex effective environment already exists so retain regression rather than forced edit.  Acceptance criteria: Acceptance: `uv run pytest tests/runtime/test_adapter_health.py` covers temporary   executable available only on overlay PATH, hidden host executable, absolute   executable, and unhealthy launch prevention for both native adapters.  Verify: uv run pytest -q --tb=line tests/runtime/test_adapter_health.py |  |
| 4 | Document repaired adapter behavior | completed |  | Document repaired adapter behavior  Location: /Users/bob/git/src/github.com/buvis/ovcaq/docs/driver-protocol.md, /Users/bob/git/src/github.com/buvis/ovcaq/CHANGELOG.md  Reuse: existing driver edge inverse-tier adaptation, identity flags, bounded connectivity policy and fake harnesses.  Premise: recheck each finding at execution; if already corrected, retain a regression and report it instead of forcing a production edit.  ### Contract Keep public `CodexDriver.build_launch(request: LaunchRequest) -> LaunchSpec` tier-key precedence unchanged, including explicit-model validation. Add a private `_ResolvedModelCodexDriver(CodexDriver)` in `drivers/edge.py`, mirroring `_ResolvedModelClaudeDriver`: its `build_launch` maps a configured model value back to a corresponding tier key before delegating. `build_driver` constructs this subclass for supervised routes. A resolved `o3` with tiers `{default: o3, o3: o3-pro}` must launch literal `o3`; direct `CodexDriver` given `o3` still launches `o3-pro`. The supervisor passes only selected.tiers[resolved.tier], per config.py:resolve_phase_route, so every supervised model is necessarily a configured tier value. A no-match literal cannot originate from this route; preserve public validation for any direct call rather than inventing a new explicit-model path. No provider strings or special cases enter shared runtime.  `item_lanes(item: object, started_lanes: set[str] \| None = None)` retains its signature and return shape. The set passed by `CodexDriver._item_observations` contains only remembered lane identities whose terminal flag is false. `interrupted`, `shutdown`, and `not_found` synthesize `LANE_FAILED` only for those unfinished identities; completed lanes retain their completed observation history. Unsupported terminal statuses otherwise produce raw-unknown evidence. No additional lane state or TUI policy.  `classify_failure(detail: str) -> FailureClass` keeps authentication, permission, rate-limit, connectivity, timeout, agent precedence. Numeric 401/403/429/502/503 require explicit diagnostic context such as HTTP status, status code or error code, including genuine fixture spellings. Ordinary numeric counts remain UNKNOWN. Retain meaningful existing word diagnostics; `Selected model is at capacity` becomes CONNECTIVITY, using existing bounded WAIT/retry exhaustion. Do not change `failure_reset` grammar. Fixture expectations are literal independent oracles, never derived through the production classifier.  `ClaudeDriver.probe() -> DriverHealth` uses effective environment `os.environ` overlaid by configured launch environment when calling `shutil.which(command, path=effective_path)`. Explicit empty PATH stays empty; absent PATH follows subprocess/default PATH semantics. Absolute executable paths retain existing behavior. Codex probes already spawn with `dict(os.environ) \| dict(settings.environment)`; reproduce and regress that behavior rather than changing it gratuitously. Both native adapters must fail health before supervisor spawn when command resolution is unhealthy. Fake Codex version/auth commands use the existing reviewed pin, never a live provider or a changed pin.  Details: Update protocol and changelog for once-resolved models, effective PATH, stable completed lanes and capacity connectivity. No new options, protocols, pins or schemas.  Acceptance criteria: Acceptance: documents describe once-resolved models, effective PATH probing,   completed-lane stability and capacity connectivity; no new options or schemas.  Verify: Review documentation against implemented behavior; full project verification at phase close. |  |
| 5 | Repair completed lane terminal stability | completed |  | Repair native outcomes and independent fixture expectations  Location: /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/drivers/codex.py, /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/drivers/codex_events.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_adapter_outcomes.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_terminals.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_failures.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_rework_decode.py  Reuse: existing driver edge inverse-tier adaptation, identity flags, bounded connectivity policy and fake harnesses.  Premise: recheck each finding at execution; if already corrected, retain a regression and report it instead of forcing a production edit.  ### Contract Keep public `CodexDriver.build_launch(request: LaunchRequest) -> LaunchSpec` tier-key precedence unchanged, including explicit-model validation. Add a private `_ResolvedModelCodexDriver(CodexDriver)` in `drivers/edge.py`, mirroring `_ResolvedModelClaudeDriver`: its `build_launch` maps a configured model value back to a corresponding tier key before delegating. `build_driver` constructs this subclass for supervised routes. A resolved `o3` with tiers `{default: o3, o3: o3-pro}` must launch literal `o3`; direct `CodexDriver` given `o3` still launches `o3-pro`. The supervisor passes only selected.tiers[resolved.tier], per config.py:resolve_phase_route, so every supervised model is necessarily a configured tier value. A no-match literal cannot originate from this route; preserve public validation for any direct call rather than inventing a new explicit-model path. No provider strings or special cases enter shared runtime.  `item_lanes(item: object, started_lanes: set[str] \| None = None)` retains its signature and return shape. The set passed by `CodexDriver._item_observations` contains only remembered lane identities whose terminal flag is false. `interrupted`, `shutdown`, and `not_found` synthesize `LANE_FAILED` only for those unfinished identities; completed lanes retain their completed observation history. Unsupported terminal statuses otherwise produce raw-unknown evidence. No additional lane state or TUI policy.  `classify_failure(detail: str) -> FailureClass` keeps authentication, permission, rate-limit, connectivity, timeout, agent precedence. Numeric 401/403/429/502/503 require explicit diagnostic context such as HTTP status, status code or error code, including genuine fixture spellings. Ordinary numeric counts remain UNKNOWN. Retain meaningful existing word diagnostics; `Selected model is at capacity` becomes CONNECTIVITY, using existing bounded WAIT/retry exhaustion. Do not change `failure_reset` grammar. Fixture expectations are literal independent oracles, never derived through the production classifier.  `ClaudeDriver.probe() -> DriverHealth` uses effective environment `os.environ` overlaid by configured launch environment when calling `shutil.which(command, path=effective_path)`. Explicit empty PATH stays empty; absent PATH follows subprocess/default PATH semantics. Absolute executable paths retain existing behavior. Codex probes already spawn with `dict(os.environ) \| dict(settings.environment)`; reproduce and regress that behavior rather than changing it gratuitously. Both native adapters must fail health before supervisor spawn when command resolution is unhealthy. Fake Codex version/auth commands use the existing reviewed pin, never a live provider or a changed pin.  Details: Cover completed and unfinished lane sequences for interrupted/shutdown/not_found; independent literal expected classes for all checked-in failure fixtures; explicit diagnostic context positives and ordinary count negatives; capacity CONNECTIVITY with existing bounded WAIT/exhaustion. Reconcile existing bare-number precedence tests to qualified HTTP diagnostics and existing capacity literals to connectivity without weakening independent assertions.  Acceptance criteria: Acceptance: `uv run pytest tests/drivers/test_adapter_outcomes.py   tests/drivers/test_codex_decode_terminals.py` covers each completed/unfinished   lane status, capacity WAIT and retry exhaustion, genuine HTTP diagnostics,   unrelated numeric counts, and all failure fixtures with literal expected classes.  Verify: uv run pytest -q --tb=line tests/drivers/test_adapter_outcomes.py tests/drivers/test_codex_decode_terminals.py tests/drivers/test_codex_failures.py tests/drivers/test_codex_rework_decode.py Split scope: Repair completed lane terminal stability. Only implement src/ovcaq/drivers/codex.py. Test targets: tests/drivers/test_adapter_outcomes.py. Other native-outcome features belong to the sibling split task. Verify: uv run pytest -q --tb=line tests/drivers/test_adapter_outcomes.py |  |
| 6 | Repair diagnostic classification and independent fixture expectations | completed |  | Repair native outcomes and independent fixture expectations  Location: /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/drivers/codex.py, /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/drivers/codex_events.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_adapter_outcomes.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_terminals.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_failures.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_rework_decode.py  Reuse: existing driver edge inverse-tier adaptation, identity flags, bounded connectivity policy and fake harnesses.  Premise: recheck each finding at execution; if already corrected, retain a regression and report it instead of forcing a production edit.  ### Contract Keep public `CodexDriver.build_launch(request: LaunchRequest) -> LaunchSpec` tier-key precedence unchanged, including explicit-model validation. Add a private `_ResolvedModelCodexDriver(CodexDriver)` in `drivers/edge.py`, mirroring `_ResolvedModelClaudeDriver`: its `build_launch` maps a configured model value back to a corresponding tier key before delegating. `build_driver` constructs this subclass for supervised routes. A resolved `o3` with tiers `{default: o3, o3: o3-pro}` must launch literal `o3`; direct `CodexDriver` given `o3` still launches `o3-pro`. The supervisor passes only selected.tiers[resolved.tier], per config.py:resolve_phase_route, so every supervised model is necessarily a configured tier value. A no-match literal cannot originate from this route; preserve public validation for any direct call rather than inventing a new explicit-model path. No provider strings or special cases enter shared runtime.  `item_lanes(item: object, started_lanes: set[str] \| None = None)` retains its signature and return shape. The set passed by `CodexDriver._item_observations` contains only remembered lane identities whose terminal flag is false. `interrupted`, `shutdown`, and `not_found` synthesize `LANE_FAILED` only for those unfinished identities; completed lanes retain their completed observation history. Unsupported terminal statuses otherwise produce raw-unknown evidence. No additional lane state or TUI policy.  `classify_failure(detail: str) -> FailureClass` keeps authentication, permission, rate-limit, connectivity, timeout, agent precedence. Numeric 401/403/429/502/503 require explicit diagnostic context such as HTTP status, status code or error code, including genuine fixture spellings. Ordinary numeric counts remain UNKNOWN. Retain meaningful existing word diagnostics; `Selected model is at capacity` becomes CONNECTIVITY, using existing bounded WAIT/retry exhaustion. Do not change `failure_reset` grammar. Fixture expectations are literal independent oracles, never derived through the production classifier.  `ClaudeDriver.probe() -> DriverHealth` uses effective environment `os.environ` overlaid by configured launch environment when calling `shutil.which(command, path=effective_path)`. Explicit empty PATH stays empty; absent PATH follows subprocess/default PATH semantics. Absolute executable paths retain existing behavior. Codex probes already spawn with `dict(os.environ) \| dict(settings.environment)`; reproduce and regress that behavior rather than changing it gratuitously. Both native adapters must fail health before supervisor spawn when command resolution is unhealthy. Fake Codex version/auth commands use the existing reviewed pin, never a live provider or a changed pin.  Details: Cover completed and unfinished lane sequences for interrupted/shutdown/not_found; independent literal expected classes for all checked-in failure fixtures; explicit diagnostic context positives and ordinary count negatives; capacity CONNECTIVITY with existing bounded WAIT/exhaustion. Reconcile existing bare-number precedence tests to qualified HTTP diagnostics and existing capacity literals to connectivity without weakening independent assertions.  Acceptance criteria: Acceptance: `uv run pytest tests/drivers/test_adapter_outcomes.py   tests/drivers/test_codex_decode_terminals.py` covers each completed/unfinished   lane status, capacity WAIT and retry exhaustion, genuine HTTP diagnostics,   unrelated numeric counts, and all failure fixtures with literal expected classes.  Verify: uv run pytest -q --tb=line tests/drivers/test_adapter_outcomes.py tests/drivers/test_codex_decode_terminals.py tests/drivers/test_codex_failures.py tests/drivers/test_codex_rework_decode.py Split scope: Repair diagnostic classification and independent fixture expectations. Only implement src/ovcaq/drivers/codex_events.py. Test targets: tests/drivers/test_adapter_failure_classes.py, tests/drivers/test_codex_decode_terminals.py, tests/drivers/test_codex_failures.py, tests/drivers/test_codex_rework_decode.py. Other native-outcome features belong to the sibling split task. Verify: uv run pytest -q --tb=line tests/drivers/test_adapter_failure_classes.py tests/drivers/test_codex_decode_terminals.py tests/drivers/test_codex_failures.py tests/drivers/test_codex_rework_decode.py |  |
| 7 | [D1] src/ovcaq/drivers/ | completed |  | ### Findings (verbatim) - 🟠 src/ovcaq/drivers/codex_events.py:301: Numeric diagnostics now need "HTTP", "HTTP status", "status code" or "error code" (src/ovcaq/drivers/codex_events.py:301), so Codex's own status wording falls to UNKNOWN. I ran `classify_failure` on "unexpected status 503 Service Unavailable", "unexpected status 502 Bad Gateway", "unexpected status 403 Forbidden" and "exceeded retry limit, last status: 429 Too Many Requests", and all four return `unknown`. The old code returned connectivity, permission and rate_limit for these. Both prefixes are confirmed as strings in the installed codex 0.162.1 binary; the "503 Service Unavailable" suffix is my guess at how Codex renders the code. Effect: 502/503 skip the bounded connectivity WAIT and get an immediate died-retry and then PARK, and 403 retries instead of halting for the operator. The PRD allows "HTTP/status/error-code" context, and "status 503" is a status context. Fix: accept a bare `status` (e.g. `(?:http(?: status)? \| status(?: code)? \| error code)`) and add both Codex spellings as literal positives in tests/drivers/test_adapter_failure_classes.py:55 (found by: ALICE, BLAKE, BOB) - 🟡 src/ovcaq/drivers/codex.py:372: Only the `continue` at src/ovcaq/drivers/codex.py:383 is pinned by tests. The unfinished-only `started_lanes` filter at src/ovcaq/drivers/codex.py:372 is not: dropping it still suppresses LANE_FAILED through the `continue`, and no test asserts the RAW_UNKNOWN that the design requires for a close status on a completed lane (I ran it: completed then shutdown gives `raw.unknown`; that the tests miss its removal comes from reading them, not a run). Add a RAW_UNKNOWN assertion on `closed` in `test_completed_lane_remains_completed_after_close_status` (tests/drivers/test_adapter_outcomes.py:89) (found by: ALICE) - 🟡 src/ovcaq/drivers/edge.py: `_ResolvedModelCodexDriver.build_launch` copies `_ResolvedModelClaudeDriver.build_launch` line for line. A module helper `_tier_request(settings, request)` would leave each override as one line: `return super().build_launch(_tier_request(self._settings, request))` (found by: BOB) - ⚪ src/ovcaq/drivers/codex.py:383: The `continue` at codex.py:383 freezes failed lanes as well as completed ones, and silently drops late `errored`/`running`/`completed` updates with no raw-unknown evidence (I ran it: completed then errored gives only `tool.completed`, while completed then shutdown gives `raw.unknown`). docs/driver-protocol.md:242 describes only completed lanes. Document that failed lanes also stay terminal, or emit raw evidence consistently (found by: ALICE) - ⚪ src/ovcaq/drivers/codex_events.py:307: The new `authentication failed` pattern goes beyond "retain existing word diagnostics". The authentication fixture already classifies through "invalid credentials", and the new pattern widens the authentication HALT to messages like "MCP server authentication failed" (found by: ALICE) - ⚪ src/ovcaq/drivers/codex_events.py:233: A normal Codex sub-agent run (spawn running, then wait completed, then close_agent shutdown) now emits `raw.unknown` on every close of a completed lane. I confirmed this with a real decode run. It sets the TUI's raw-evidence flag (src/ovcaq/tui/model.py:548). The doc at docs/driver-protocol.md:244 says only unstarted receivers and missing attribution produce raw unknown evidence. (found by: BLAKE) |  |
| 8 | [D1] tests/drivers/ | completed |  | ### Findings (verbatim) - 🟡 tests/drivers/test_adapter_outcomes.py:1: The Phase 0 acceptance command (`tests/drivers/test_adapter_outcomes.py tests/drivers/test_codex_decode_terminals.py`) does not test the capacity WAIT and retry exhaustion, the unrelated-number negatives, or HTTP positives that rely on the number alone. Those tests live in tests/drivers/test_adapter_failure_classes.py, a file the PRD does not list, so the stated acceptance run passes without proving them. (found by: BLAKE) - 🟡 tests/drivers/test_adapter_outcomes.py: The normal sequence spawn → wait(completed) → close_agent(shutdown) now emits raw.unknown for every completed lane, which sets the TUI raw-evidence flag (tui/model.py:548). Late running/errored/completed updates for a finished lane are dropped with no trace (codex.py:383). No test asserts either outcome, so the design's "raw-unknown evidence" rule is unpinned (found by: BOB) - 🟡 tests/drivers/test_adapter_outcomes.py: 40 of the 49 new outcome test cases pass on the pre-change code and repeat existing tests: test_codex_rework_decode.py:201 already covers an unfinished lane failing on close, and test_codex_decode_lanes.py:257 covers an unstarted receiver staying raw. The 3-way receiver-name parametrization exercises no extra code path, and `test_non_json_output_retains_raw_unknown` has nothing to do with lanes (found by: BOB) - ⚪ tests/drivers/test_codex_launch.py: `test_configured_factory_rejects_unknown_or_invalid_options` re-tests `CodexDriver.__init__`, which the new subclass does not override, and passes on the pre-change code. Its `pytest.raises(ValueError)` also accepts `ConfigurationError` (a ValueError subclass) raised by config parsing, so it can pass for the wrong reason (found by: BOB) |  |
| 9 | [D1] prose | completed |  | ### Findings (verbatim) - 🟡 docs/driver-protocol.md:37: The docs say an empty host PATH "searches the current directory" for both native adapters, but `ClaudeDriver.probe` passes `path=""` to `shutil.which`, which returns None (checked on Python 3.13). tests/runtime/test_adapter_health.py:263 asserts unhealthy. So the Claude probe treats an empty host PATH as unhealthy, while only the Codex subprocess probe searches the current directory. Fix the sentence to say this (found by: ALICE, BLAKE) |  |
| 10 | [D1] tests/runtime/test_adapter_health.py | completed |  | ### Findings (verbatim) - 🟡 tests/runtime/test_adapter_health.py:263: The "fixture" case in `test_claude_probe_keeps_empty_host_path_unhealthy` puts the executable in tmp_path/bin while the working directory is tmp_path. It cannot tell the conservative empty-PATH handling apart from a current-directory search. Put the executable in the working directory to pin the choice (found by: ALICE, BOB) |  |
| 11 | [D2] Tail sweep: src/ovcaq/drivers/ | completed |  | ### Findings (verbatim) - 🟡 src/ovcaq/drivers/codex_events.py:301: Codex's HTTP client (reqwest) reports status errors as "HTTP status client error (429 Too Many Requests) for url (...)". The new numeric check still returns `unknown` for that form. I ran `classify_failure` on that string, on "HTTP status server error (503 Service Unavailable) for url (...)", on "HTTP status client error (403 Forbidden) ..." and on "HTTP/1.1 503 Service Unavailable", and all four give `unknown`. The pre-change code returned rate_limit, connectivity and permission for them. Both "HTTP status client error" and "HTTP status server error" are present as strings in the installed codex-cli 0.162.1 binary (confirmed with `rg -a`). Whether they ever reach a `turn.failed` message is my guess, not something I checked. If they do, a real 429 skips the rate-limit wait and a real 502/503 skips the bounded connectivity WAIT, just like the cycle-1 HIGH. This also contradicts docs/driver-protocol.md:271 ("require HTTP, status or error-code context"). Fix: also accept the code when the standard reason phrase follows it (e.g. `(?:403 forbidden \| 429 too many requests \| 502 bad gateway \| 503 service unavailable)`). Add the reqwest and HTTP/1.1 forms as literal positives in tests/drivers/test_adapter_failure_classes.py:63, and keep the ordinary-count negatives (found by: ALICE, BLAKE, BOB) - ⚪ src/ovcaq/drivers/codex_events.py:300: `classify_failure` now collapses whitespace (`" ".join(detail.split())`), so "Rate\tlimit reached" becomes rate_limit. The pre-change code returned unknown for it. That widens matching beyond "retain existing word diagnostics", and neither the CHANGELOG nor the protocol doc mentions it. The test `test_native_word_diagnostics_retain_case_and_whitespace_variants` calls it "retain" even though the whitespace case is new behavior. Either document the widening and rename the test, or drop line 300 and the tab case (found by: ALICE) - ⚪ src/ovcaq/drivers/edge.py:23: No supervisor-level regression covers the Claude model-collision path. The Claude edge wrapper behaves correctly: I checked directly that `{default: o3, o3: o3-pro, x: o3}` launches `o3` and `o3-pro`. But tests/runtime/test_adapter_launch_routing.py runs only the Codex fake through the supervisor, so a regression in `_ResolvedModelClaudeDriver` would go unnoticed. (found by: BLAKE) |  |
| 12 | [D2] Tail sweep: prose | completed |  | ### Findings (verbatim) - ⚪ CHANGELOG.md:43: The CHANGELOG PATH entry says the change checks "both native adapters' executables" and preserves "standard missing/empty host PATH lookup". In fact only the Claude probe changed (Codex already used the merged environment). With an empty host PATH, the Claude probe is unhealthy while the Codex probe searches the current directory, which docs/driver-protocol.md:37 now says correctly. Reword the entry to say the fix is for Claude and to name that split (found by: ALICE) - ⚪ CHANGELOG.md:43: CHANGELOG says "preserving standard missing ... host PATH lookup", but the Claude probe changed. With no host PATH it now falls back to `os.defpath` (`/bin:/usr/bin`, src/ovcaq/drivers/claude.py:82). The old `shutil.which(command)` used `CS_PATH` (`/usr/bin:/bin:/usr/sbin:/sbin` here, confirmed with `getconf PATH` and the stdlib source). The new value matches the subprocess spawn, as the design asks, so only the wording is wrong (found by: BOB) |  |
| 13 | [D2] Tail sweep: tests/drivers/ | completed |  | ### Findings (verbatim) - ⚪ tests/drivers/test_codex_launch.py:140: `INVALID_OPTIONS` was moved up to module level so the now-deleted factory test could share it. It has a single user again (`test_constructor_rejects_unknown_or_invalid_options`). Inline it back into that test's `@pytest.mark.parametrize`, so the only change left in that test is the `raised.type is ValueError` line (found by: ALICE, BOB) - ⚪ tests/drivers/test_adapter_failure_classes.py:225: `assert retries.rate_limit == 0` can never fail. It checks the frozen `RetryState` the test built with `rate_limit=0`, and `decide` cannot change it (src/ovcaq/runtime/decision.py:84). Lines 200-201 already pin the non-rate-limit path (found by: BOB) |  |
| 14 | [D2] Tail sweep: tests/runtime/test_adapter_health.py | completed |  | ### Findings (verbatim) - ⚪ tests/runtime/test_adapter_health.py:250: The test for an absent host PATH probes `sh`, which is in both `os.defpath` and `CS_PATH`. It cannot tell the design's spawn-matching `os.defpath` fallback from the old `CS_PATH` one, so going back to `shutil.which(command, path=None)` would still pass (found by reading, not run) (found by: BOB) |  |
| 15 | [D2] Tail sweep: src/ovcaq/drivers/ (post-sweep) | completed |  | ### Findings (verbatim, post-sweep review 2026-10-12; authorization reports/00053-postsweep-repair-authorization.md) - 🟡 src/ovcaq/drivers/codex_events.py:301: The HTTP-version prefix `http/\d+\.\d+` requires a minor version, so "HTTP/2 503 Service Unavailable" and "HTTP/2 429 Too Many Requests" classify as `unknown` (pre-PRD: connectivity and rate_limit). Fix: make the minor version optional (`http(?:/\d+(?:\.\d+)?\| status...)`) and add HTTP/2 503 and HTTP/2 429 positives at tests/drivers/test_adapter_failure_classes.py:103. Do NOT widen to `status=N` or `Error N:` forms (out of scope by operator decision) (found by: ALICE, BLAKE) - ⚪ src/ovcaq/drivers/edge.py:16: helper `_tier_request` is a noun phrase; rename to a verb-led name such as `_map_model_to_tier` (call sites edge.py:27, edge.py:34) (found by: ALICE) |  |
| 16 | [D2] Tail sweep: CHANGELOG.md and docs/driver-protocol.md (post-sweep) | completed |  | ### Findings (verbatim, post-sweep review 2026-10-12; authorization reports/00053-postsweep-repair-authorization.md) - ⚪ CHANGELOG.md:43: entry about reqwest/HTTP-version forms and literal whitespace describes no change from the pre-PRD base and overlaps the numeric-context entry. Delete it, and add "including bare-status, reqwest and HTTP-version forms" to the numeric-context entry at CHANGELOG.md:46 (found by: ALICE, BOB) - ⚪ docs/driver-protocol.md:243: claims completed and failed lanes stay terminal "under all late receiver updates", but identity eviction (src/ovcaq/drivers/codex.py:413) removes terminal lanes first. Change to "Remembered completed and failed lanes remain terminal under late receiver updates" (found by: BOB) |  |
| 17 | [D2] Tail sweep: tests/ (post-sweep) | completed |  | ### Findings (verbatim, post-sweep review 2026-10-12; authorization reports/00053-postsweep-repair-authorization.md) - ⚪ tests/runtime/test_adapter_launch_routing.py:114-115: Claude routing cases set every phase effort to "high" with no reason; config accepts low/medium/high/xhigh (src/ovcaq/config.py:364) and ClaudeDriver passes effort through, so pass-through is tested with one value only. Cover at least two distinct effort values, or keep the override with a one-line comment giving the reason if removing it fails (found by: BOB) - ⚪ tests/drivers/test_codex_launch.py:32: `configured_driver` is annotated `-> CodexDriver` but returns `build_driver(...)` typed `AgentDriver`; annotate `-> AgentDriver` imported from `ovcaq.drivers.base` (found by: BOB) |  |
| 18 | [D2] Tail sweep: tests/runtime/test_adapter_launch_routing.py | completed |  | ### Findings (verbatim) - 🟡 tests/runtime/test_adapter_launch_routing.py: tests/runtime/test_adapter_launch_routing.py:30 re-implements the runpy Claude wrapper from tests/runtime/test_supervisor_adapters.py:44. The wrapper rebinds `fake_codex.workflow.__globals__['__file__']` to the Claude fixture, and the new copy adds only an `edge['emit_invocation'](sys.argv[1:])` call. That leaves two copies of a hack tied to fake_codex.py internals, and they will drift apart. Keep one wrapper builder in test_supervisor_adapters.py that always emits the invocation (Codex `main()` already emits it unconditionally) and call it from both files (found by: BOB) |  |
| 19 | [D2] Tail sweep: prose | completed |  | ### Findings (verbatim) - ⚪ CHANGELOG.md: CHANGELOG.md:46 still says completed and failed Codex receiver lanes stay terminal "under late updates", with no qualifier. Task 16 fixed this same overclaim in docs/driver-protocol.md:243, which now says "Remembered completed and failed lanes". Lanes stop being remembered once they are evicted (src/ovcaq/drivers/codex.py:413 evicts finished identities first, at 4096 identities). After that, a late `running` update starts the lane again. Add "remembered" to the CHANGELOG entry so it matches the protocol doc (found by: ALICE) - ⚪ docs/driver-protocol.md: docs/driver-protocol.md:185 says "the driver preserves that resolved value", but only drivers built by `build_driver` do that. A `CodexDriver` constructed directly and passed to `Supervisor` (as in tests/runtime/test_rework_thread_conflict.py:108) still remaps a colliding value through tier-key precedence. Reword to "the driver built by `build_driver` preserves that resolved value" (found by: BOB) - ⚪ CHANGELOG.md: CHANGELOG.md:45 puts two fixes in one entry. Its clause "retry model capacity as connectivity through bounded WAIT/retry exhaustion" does not read as a sentence, and "reqwest" is implementation jargon. Split it into a numeric-context entry and a separate entry: "classify 'Selected model is at capacity' as connectivity so it gets bounded WAIT retries instead of rate-limit handling" (found by: BOB) |  |
| 20 | [D2] Tail sweep: tests/runtime/test_adapter_health.py | completed |  | ### Findings (verbatim) - ⚪ tests/runtime/test_adapter_health.py: tests/runtime/test_adapter_health.py:90 runs `command_name` over three names ("fixture-agent-health", "overlay-runner", "queue-worker"). In both probes all three take the same code path, so there are 6 cases where 2 would do. R8 removed the same kind of padding from test_adapter_outcomes.py. Keep one name (found by: BOB) |  |

## Code Changes

### Changed Files
_Diff scope: incremental review (changes since 7819970d7f807d6fad07b115af4f0df1fbc4a248)_

```
 CHANGELOG.md                                       |     5 +
 .../autopilot/autocodex-metrics.jsonl              |    11 +
 .../20e00488d69c4049841e98345186f7e4.jsonl         |   200 +
 .../20e00488d69c4049841e98345186f7e4.prompt.md     |   217 +
 .../20e00488d69c4049841e98345186f7e4.stderr        |     8 +
 .../279781a2783542beaaa8681f17114874.jsonl         |   219 +
 .../279781a2783542beaaa8681f17114874.prompt.md     |   245 +
 .../279781a2783542beaaa8681f17114874.stderr        |     8 +
 .../347829f3e7c8444db80f7c361aa1829a.jsonl         |   119 +
 .../347829f3e7c8444db80f7c361aa1829a.prompt.md     |   217 +
 .../347829f3e7c8444db80f7c361aa1829a.stderr        |     8 +
 .../506935de425a4e46b8594c70db3d1b14.jsonl         |   337 +
 .../506935de425a4e46b8594c70db3d1b14.prompt.md     |   231 +
 .../506935de425a4e46b8594c70db3d1b14.stderr        |     8 +
 .../73283477de354a7f8ada998665ea18c5.jsonl         |   353 +
 .../73283477de354a7f8ada998665ea18c5.prompt.md     |   245 +
 .../73283477de354a7f8ada998665ea18c5.stderr        |     8 +
 .../802d38c005794cfaa2b4a8e5c972ab1e.jsonl         |  1370 +
 .../802d38c005794cfaa2b4a8e5c972ab1e.prompt.md     |   245 +
 .../802d38c005794cfaa2b4a8e5c972ab1e.stderr        |     9 +
 .../89a9a06960fb4564bc91d44a5a751a72.jsonl         |   204 +
 .../89a9a06960fb4564bc91d44a5a751a72.prompt.md     |   245 +
 .../89a9a06960fb4564bc91d44a5a751a72.stderr        |     8 +
 .../992dfab37880403fb77de3760d4ffbe2.jsonl         |   119 +
 .../992dfab37880403fb77de3760d4ffbe2.prompt.md     |   217 +
 .../992dfab37880403fb77de3760d4ffbe2.stderr        |     9 +
 .../b184edc3051047e1a011ea374b1f90d7.jsonl         |   154 +
 .../b184edc3051047e1a011ea374b1f90d7.prompt.md     |   231 +
 .../b184edc3051047e1a011ea374b1f90d7.stderr        |     8 +
 .../b8f0813f1cf84d20ac0f325bc1d82c35.jsonl         |   251 +
 .../b8f0813f1cf84d20ac0f325bc1d82c35.prompt.md     |   231 +
 .../b8f0813f1cf84d20ac0f325bc1d82c35.stderr        |     9 +
 .../f3e5d6d880fa45028ec82cb08e5b5de6.jsonl         |   262 +
 .../f3e5d6d880fa45028ec82cb08e5b5de6.prompt.md     |   217 +
 .../f3e5d6d880fa45028ec82cb08e5b5de6.stderr        |     8 +
 .../project-management/autopilot/contract-card.md  |    10 +-
 .../autopilot/dispatch-metrics.jsonl               |   149 +
 .../autopilot/last-verification.json               |    16 +-
 .../autopilot/ledger/dispatch-metrics.jsonl        |   149 +
 .../reports/00051-assumptions-snapshot.md          |     7 +
 .../00053-00053-design-review-anthropic.txt        |    53 +
 .../00053-00053-design-review-verify-anthropic.txt |    61 +
 ...rrections-v1-implementation-models-cycle-1.json |   344 +
 ...corrections-v1-implementation-models-cycle-1.md |    31 +
 ...plementation-models-cycle-2-pre-postrepair.json |   534 +
 ...v1-implementation-models-cycle-2-pre-sweep.json |   432 +
 ...s-v1-implementation-models-cycle-2-pre-sweep.md |    37 +
 ...ional-corrections-v1-implementation-models.json |   662 +
 ...ational-corrections-v1-implementation-models.md |    57 +
 ...3-18-01a12584-6da8-7ab3-b3fb-3199ecb95674.jsonl |   145 +
 ...1-36-01a12595-30c4-7ea2-9f5b-7d30acd36845.jsonl |   102 +
 .../reports/00053-approved-task-reviews-handoff.md |    46 +
 .../autopilot/reports/00053-build-progress.md      |    41 +
 .../autopilot/reports/00053-cleanup.json           |   335 +
 .../00053-host-recovery-20261012-handoff.md        |    32 +
 .../00053-host-recovery-20261012-verification.json |   103 +
 .../reports/00053-model-correlations.json          |   311 +
 ...3-34-01a1258d-d5e8-7ff2-bd56-564762d91666.jsonl |    53 +
 ...7-05-01a1259a-368d-7cc0-a13c-6508d855e6a1.jsonl |    58 +
 ...1-57-01a1259e-a86e-7991-a8f6-10e6fdbb3b27.jsonl |    35 +
 ...9-40-01a1259c-9163-7e91-aba2-00ac86f909e2.jsonl |    59 +
 ...7-53-01a1256d-2a93-70f2-a11a-e7f8016a3f00.jsonl |    82 +
 ...3-31-01a1257b-7994-7a30-ada3-382d34279d26.jsonl |    86 +
 ...2-22-01a125a8-3296-7a82-b8c1-ffba26eb9c8b.jsonl |    39 +
 ...3-22-01a125a9-1e1c-7410-9ac5-a2be36a4a33b.jsonl |    39 +
 ...8-06-01a125a4-4a43-7053-8bd7-3d710ff4e836.jsonl |    40 +
 ...5-19-01a12561-a6e6-73a2-b0a8-66ba9751f8f8.jsonl |    59 +
 ...7-23-01a1257f-0555-7891-bc0a-9cc852e4be16.jsonl |    85 +
 ...8-38-01a12589-50f8-7370-9967-aaa607f37385.jsonl |   175 +
 ...6-14-01a12590-45f8-7373-8770-0aea39dc3ba0.jsonl |   102 +
 ...9-58-01a12593-b073-7b91-a8da-9c1fd1cb6421.jsonl |    41 +
 ...4-54-01a12598-3682-75b0-99c2-c96af917308d.jsonl |    65 +
 ...7-48-01a12563-eda6-7cd1-904f-6abc2463ec74.jsonl |    59 +
 ...5-55-01a1256b-5e70-7a10-b173-31767b9534c0.jsonl |    76 +
 ...0-35-01a1256f-a3f7-75e2-a996-23e21c05a817.jsonl |   110 +
 ...6-39-01a12575-2fdb-7592-8d80-d4da98980196.jsonl |    55 +
 ...1-47-01a12579-e43e-7fa2-8697-2ecfaf0ebb24.jsonl |    67 +
 .../reports/00053-plugin-repin-20261012.md         |     8 +
 .../attempt-task-18.json                           |    17 +
 .../attempt-task-19.json                           |    21 +
 .../attempt-task-20.json                           |    17 +
 .../author-evidence.json                           |    26 +
 .../dispatch-ivan-19.txt                           |   193 +
 .../ivan-19.raw.jsonl                              |    44 +
 .../micro-author.raw.jsonl                         |   344 +
 .../review-task-18-acceptance.txt                  |     1 +
 .../review-task-18-approved.md                     |     3 +
 .../review-task-18-approved.raw.jsonl              |    26 +
 .../review-task-18-description.txt                 |     2 +
 .../review-task-18-prompt.md                       |   163 +
 .../review-task-18-subject.txt                     |     1 +
 .../review-task-18-verification.txt                |     2 +
 .../review-task-20-acceptance.txt                  |     1 +
 .../review-task-20-approved.md                     |     3 +
 .../review-task-20-approved.raw.jsonl              |    28 +
 .../review-task-20-description.txt                 |     2 +
 .../review-task-20-prompt.md                       |   119 +
 .../review-task-20-subject.txt                     |     1 +
 .../review-task-20-verification.txt                |     2 +
 .../task-diff-18.txt                               |    67 +
 .../task-diff-20.txt                               |    23 +
 ...-postrepair-recovery-20261012-model-evidence.md |    47 +
 .../00053-postrepair-recovery-20261012-work.md     |    68 +
 .../00053-postrepair-repair-authorization.md       |    37 +
 ...e-output-71006cca714e4990ac519742ea445bf2.jsonl |   327 +
 ...-output-71006cca714e4990ac519742ea445bf2.stderr |     0
 .../alice-output.txt                               |    14 +
 .../alice-output.txt.receipt.json                  |    17 +
 .../alice-prompt-00053-postrepair-20261012.md      |   179 +
 ...e-output-a6d87910ee7743fd83acd241486d3ed5.jsonl |   332 +
 ...-output-a6d87910ee7743fd83acd241486d3ed5.stderr |     0
 .../blake-output.txt                               |    26 +
 .../blake-output.txt.receipt.json                  |    17 +
 .../blake-prompt-00053-postrepair-20261012.md      |   303 +
 ...b-output-cebe25bde513499a910b4c0179c35df1.jsonl |   384 +
 ...-output-cebe25bde513499a910b4c0179c35df1.stderr |     0
 .../bob-output.txt                                 |    35 +
 .../bob-output.txt.receipt.json                    |    17 +
 .../bob-prompt-00053-postrepair-20261012.md        |   261 +
 .../consolidated.txt                               |    14 +
 .../diff-archive.json                              |     6 +
 .../review-context-00053-postrepair-20261012.md    |  1127 +
 .../review-diff-00053-postrepair-20261012.diff.gz  |   Bin 0 -> 16338973 bytes
 .../review-prd-00053-postrepair-20261012.md        |   237 +
 .../review-tasks-00053-postrepair-20261012.md      |    19 +
 ...0053-postrepair-review-20261012-validation.json |    27 +
 .../attempt-task-15.json                           |    16 +
 .../attempt-task-16.json                           |    15 +
 .../attempt-task-17.json                           |    17 +
 .../coordinator-source.json                        |    57 +
 .../coordinator.raw.jsonl                          |    13 +
 .../dispatch-ivan-15.txt                           |   451 +
 .../dispatch-settings.json                         |    37 +
 .../dispatch-tess-15.txt                           |   306 +
 .../ivan-15-files.txt                              |     2 +
 .../ivan-15-spec.txt                               |   264 +
 .../ivan-15.raw.jsonl                              |    63 +
 .../pat-15.raw.jsonl                               |    23 +
 .../pat-17.raw.jsonl                               |    23 +
 .../review-task-15-acceptance.txt                  |     1 +
 .../review-task-15-description.txt                 |     3 +
 .../review-task-15-prompt.md                       |   168 +
 .../review-task-15-subject.txt                     |     1 +
 .../review-task-15-verification.txt                |     3 +
 .../review-task-15.md                              |     6 +
 .../review-task-17-acceptance.txt                  |     1 +
 .../review-task-17-description.txt                 |     3 +
 .../review-task-17-prompt.md                       |   132 +
 .../review-task-17-subject.txt                     |     1 +
 .../review-task-17-verification.txt                |     2 +
 .../review-task-17.md                              |     5 +
 .../task-diff-15.txt                               |    70 +
 .../task-diff-17.txt                               |    35 +
 .../tess-15-acceptance.txt                         |     1 +
 .../tess-15-api.txt                                |     1 +
 .../tess-15-description.txt                        |     1 +
 .../tess-15-subject.txt                            |     1 +
 .../tess-15.raw.jsonl                              |    88 +
 .../test-diff-15.txt                               |    27 +
 ...053-postsweep-repair-20261012-model-evidence.md |    13 +
 ...053-postsweep-repair-20261012-verification.json |    53 +
 .../reports/00053-postsweep-repair-20261012.md     |    38 +
 .../00053-postsweep-repair-authorization.md        |    37 +
 ...20261012-e4a60124252b443c88dc5d26966dfe81.jsonl |   251 +
 ...0261012-e4a60124252b443c88dc5d26966dfe81.stderr |     0
 .../alice-output-00053-c2-postsweep-20261012.txt   |    25 +
 ...ut-00053-c2-postsweep-20261012.txt.receipt.json |    17 +
 .../alice-prompt-00053-c2-postsweep-20261012.md    |   173 +
 ...20261012-cf6275c6d78746a09b1227953ed3875b.jsonl |   358 +
 ...0261012-cf6275c6d78746a09b1227953ed3875b.stderr |     0
 .../blake-output-00053-c2-postsweep-20261012.txt   |    25 +
 ...ut-00053-c2-postsweep-20261012.txt.receipt.json |    17 +
 .../blake-prompt-00053-c2-postsweep-20261012.md    |   303 +
 ...20261012-fa107f9cf6d14f7d9878c651c416815d.jsonl |   344 +
 ...0261012-fa107f9cf6d14f7d9878c651c416815d.stderr |     0
 .../bob-output-00053-c2-postsweep-20261012.txt     |    34 +
 ...ut-00053-c2-postsweep-20261012.txt.receipt.json |    17 +
 .../bob-prompt-00053-c2-postsweep-20261012.md      |   255 +
 .../consolidated-script.md                         |    11 +
 .../review-context-00053-c2-postsweep-20261012.md  |   982 +
 .../review-diff-00053-c2-postsweep-20261012.diff   |  1524 ++
 .../review-prd-00053-c2-postsweep-20261012.md      |   237 +
 .../review-tasks-00053-c2-postsweep-20261012.md    |    16 +
 .../reviewer-metadata.json                         |    20 +
 .../00053-postsweep-review-20261012-handoff.md     |    13 +
 ...00053-postsweep-review-20261012-validation.json |    25 +
 .../autopilot/reports/00053-review-1-cleanup.json  |    55 +
 ...al-corrections-v1-decision-gate-1-findings.json |   236 +
 ...ional-corrections-v1-implementation-models.json |   344 +
 ...ational-corrections-v1-implementation-models.md |    31 +
 .../00053-review-pytest.log                        |   260 +
 .../00053-review-test-gate.py                      |    15 +
 .../alice-prompt-00053-c1-20261010-approved.md     |   151 +
 .../alice-prompt-00053-c1-20261010.md              |   151 +
 .../blake-prompt-00053-c1-20261010-approved.md     |   301 +
 .../blake-prompt-00053-c1-20261010.md              |   301 +
 .../bob-prompt-00053-c1-20261010-approved.md       |   233 +
 .../bob-prompt-00053-c1-20261010-isolated.md       |   236 +
 .../bob-prompt-00053-c1-20261010.md                |   233 +
 .../consolidator-stderr.txt                        |     2 +
 .../review-context-00053-c1-20261010-approved.md   |   583 +
 .../review-context-00053-c1-20261010.md            |   575 +
 .../review-diff-00053-c1-20261010-approved.diff    |  6641 +++++
 .../review-prd-00053-c1-20261010-approved.md       |   235 +
 .../review-prd-00053-c1-20261010.md                |   235 +
 .../review-prd-raw-00053-c1-20261010-approved.md}  |     0
 .../review-prd-raw-00053-c1-20261010.md            |   171 +
 .../review-tasks-00053-c1-20261010-approved.md     |     8 +
 .../review-tasks-00053-c1-20261010.md              |     8 +
 .../reports/00053-review-1-verification.json       |    38 +
 .../autopilot/reports/00053-review-2-cleanup.json  |    19 +
 ...al-corrections-v1-decision-gate-2-findings.json |    54 +
 ...ional-corrections-v1-tail-sweep-2-findings.json |   109 +
 ...20261010-01abbbef9d2045688ec6cffb740060c3.jsonl |   301 +
 ...0261010-01abbbef9d2045688ec6cffb740060c3.stderr |     0
 .../alice-output-00053-c2-20261010.txt             |    18 +
 ...alice-output-00053-c2-20261010.txt.receipt.json |    17 +
 .../alice-prompt-00053-c2-20261010.md              |   394 +
 ...20261010-a3b8ab94dd554de28d3e282362869911.jsonl |   352 +
 ...0261010-a3b8ab94dd554de28d3e282362869911.stderr |     0
 ...isolated-8526130ad66c4348868a1e8d29205983.jsonl |   337 +
 ...solated-8526130ad66c4348868a1e8d29205983.stderr |     0
 .../blake-output-00053-c2-20261010-isolated.txt    |    25 +
 ...put-00053-c2-20261010-isolated.txt.receipt.json |    17 +
 .../blake-output-00053-c2-20261010.txt             |    42 +
 ...blake-output-00053-c2-20261010.txt.receipt.json |    17 +
 .../blake-prompt-00053-c2-20261010-isolated.md     |   306 +
 .../blake-prompt-00053-c2-20261010.md              |   303 +
 ...20261010-58735a23c3bb4aeb8a381d670e6ec151.jsonl |   287 +
 ...0261010-58735a23c3bb4aeb8a381d670e6ec151.stderr |     0
 .../bob-output-00053-c2-20261010.txt               |    52 +
 .../bob-output-00053-c2-20261010.txt.receipt.json  |    17 +
 .../bob-prompt-00053-c2-20261010.md                |   476 +
 .../00053-review-2-evidence/chosen-findings.json   |   161 +
 .../consolidation-original.txt                     |    16 +
 .../00053-review-2-evidence/consolidation.stderr   |     1 +
 .../00053-review-2-evidence/ovcaq-review2-pause.py |    60 +
 .../ovcaq-review2-report.py                        |   151 +
 .../review-context-00053-c2-20261010.md            |   821 +
 .../review-diff-00053-c2-20261010.diff             | 25268 +++++++++++++++++++
 .../review-prd-00053-c2-20261010.md                |   237 +
 .../review-prd-raw-00053-c2-20261010.md            |   173 +
 .../review-tasks-00053-c2-20261010.md              |    12 +
 .../00053-review-2-sandbox-verification.json       |    13 +
 .../autopilot/reports/00053-review-2-summary.json  |   173 +
 .../reports/00053-review-2-verification.json       |    36 +
 .../coordinator-model-metadata.raw.jsonl           |     6 +
 .../coordinator-model-metadata.raw.source.json     |     1 +
 .../inputs/attempt-task-10.json                    |     1 +
 .../inputs/attempt-task-7.json                     |     1 +
 .../inputs/attempt-task-8.json                     |     1 +
 .../inputs/attempt-task-9.json                     |     1 +
 .../inputs/dispatch-ivan-7.txt                     |   427 +
 .../inputs/dispatch-ivan-8.txt                     |   196 +
 .../inputs/dispatch-tess-7.txt                     |   244 +
 .../inputs/ivan-7-checks.txt                       |   234 +
 .../inputs/ivan-7-context.txt                      |   107 +
 .../inputs/ivan-7-files.txt                        |     6 +
 .../inputs/ivan-8-checks.txt                       |     7 +
 .../inputs/ivan-8-context.txt                      |   107 +
 .../inputs/ivan-8-files.txt                        |     3 +
 .../inputs/review-task-10-acceptance.txt           |     1 +
 .../inputs/review-task-10-description.txt          |     2 +
 .../inputs/review-task-10-prompt.md                |   109 +
 .../inputs/review-task-10-subject.txt              |     1 +
 .../inputs/review-task-10-verification.txt         |     2 +
 .../inputs/review-task-10.md                       |     3 +
 .../inputs/review-task-7-acceptance.txt            |     1 +
 .../inputs/review-task-7-description.txt           |     7 +
 .../inputs/review-task-7-prompt.md                 |   284 +
 .../inputs/review-task-7-subject.txt               |     1 +
 .../inputs/review-task-7-verification.txt          |     3 +
 .../inputs/review-task-7.md                        |    13 +
 .../inputs/review-task-8-acceptance.txt            |     1 +
 .../inputs/review-task-8-description.txt           |     5 +
 .../inputs/review-task-8-prompt.md                 |   286 +
 .../inputs/review-task-8-subject.txt               |     1 +
 .../inputs/review-task-8-verification.txt          |     2 +
 .../inputs/review-task-8.md                        |     9 +
 .../inputs/review-task-9-acceptance.txt            |     1 +
 .../inputs/review-task-9-description.txt           |     2 +
 .../inputs/review-task-9-prompt.md                 |   112 +
 .../inputs/review-task-9-subject.txt               |     1 +
 .../inputs/review-task-9-verification.txt          |     2 +
 .../inputs/review-task-9.md                        |     3 +
 .../inputs/task-diff-10.txt                        |    13 +
 .../00053-rework-1-evidence/inputs/task-diff-7.txt |   182 +
 .../00053-rework-1-evidence/inputs/task-diff-8.txt |   187 +
 .../inputs/tess-7-acceptance.txt                   |     1 +
 .../inputs/tess-7-description.txt                  |     1 +
 .../inputs/tess-7-interfaces.txt                   |     1 +
 .../inputs/tess-7-subject.txt                      |     1 +
 .../00053-rework-1-evidence/inputs/test-diff-7.txt |    66 +
 .../00053-rework-1-evidence/ivan-7.raw.jsonl       |    67 +
 .../00053-rework-1-evidence/ivan-8.raw.jsonl       |    95 +
 .../00053-rework-1-evidence/pat-10.prompt.md       |   109 +
 .../reports/00053-rework-1-evidence/pat-10.txt     |     3 +
 .../00053-rework-1-evidence/pat-7.prompt.md        |   284 +
 .../reports/00053-rework-1-evidence/pat-7.txt      |    13 +
 .../00053-rework-1-evidence/pat-8.prompt.md        |   286 +
 .../reports/00053-rework-1-evidence/pat-8.txt      |     9 +
 .../00053-rework-1-evidence/pat-9.prompt.md        |   112 +
 .../reports/00053-rework-1-evidence/pat-9.txt      |     3 +
 .../00053-rework-1-evidence/tess-7.raw.jsonl       |    54 +
 .../reports/00053-rework-1-model-evidence.md       |    16 +
 .../autopilot/reports/00053-rework-1-report.md     |    22 +
 .../reports/00053-rework-1-verification.json       |    33 +
 .../autopilot/reports/00053-signing-recovery.md    |    16 +
 .../autopilot/reports/00053-source-findings.md     |    43 +
 .../reports/00053-tail-sweep-20261011-pat-11.md    |     9 +
 .../reports/00053-tail-sweep-20261011-pat-12.md    |     5 +
 .../reports/00053-tail-sweep-20261011-pat-13.md    |    11 +
 .../reports/00053-tail-sweep-20261011-pat-14.md    |     3 +
 .../00053-tail-sweep-20261011-turn-metadata.jsonl  |     1 +
 .../autopilot/reports/00053-tail-sweep-20261011.md |    42 +
 .../reports/00053-tail-sweep-authorization.md      |    23 +
 .../ivan11.raw.jsonl                               |    47 +
 .../micro.raw.jsonl                                |   449 +
 .../tess11.raw.jsonl                               |   123 +
 .../reports/00053-tail-sweep-signing-pause.md      |    16 +
 .../00053-task11-signing-recovery-20261011.md      |    25 +
 .../autopilot/reports/00053-task2-pat.md           |     3 +
 .../autopilot/reports/00053-task3-pat.md           |     7 +
 .../autopilot/reports/00053-task5-pat.md           |     7 +
 .../autopilot/reports/00053-task6-pat.md           |     7 +
 .../reports/00053-verification-initial.json        |    34 +
 .../autopilot/reports/repair-readiness-20261007.md |     6 +
 .../project-management/autopilot/session-brief.md  |    26 +-
 ...53-adapter-operational-corrections-v1-design.md |    61 +
 docs/dev/project-management/meta/assumptions.md    |    10 +-
 .../dev/project-management/meta/project-capsule.md |    47 +-
 .../00053-adapter-operational-corrections-v1.md    |   173 +
 ...dapter-operational-corrections-v1-checks-1.json |     1 +
 ...dapter-operational-corrections-v1-checks-2.json |     1 +
 ...-adapter-operational-corrections-v1-ledger.json |   167 +
 ...-adapter-operational-corrections-v1-review-1.md |   215 +
 ...-corrections-v1-review-2-postrepair-20261012.md |   162 +
 ...l-corrections-v1-review-2-postsweep-20261012.md |   159 +
 ...-adapter-operational-corrections-v1-review-2.md |   209 +
 ...20261010-536db8fa0d974849a0e9dbf16ee412ce.jsonl |   247 +
 ...0261010-536db8fa0d974849a0e9dbf16ee412ce.stderr |     0
 .../reviews/alice-output-00053-c1-20261010.txt     |    20 +
 ...alice-output-00053-c1-20261010.txt.receipt.json |    17 +
 .../reviews/alice-output-00053-c2-20261010.txt     |    18 +
 ...alice-output-00053-c2-20261010.txt.receipt.json |    17 +
 ...20261010-de1e8e0e176c4d6f9b78bf0d26530c7e.jsonl |   296 +
 ...0261010-de1e8e0e176c4d6f9b78bf0d26530c7e.stderr |     0
 .../reviews/blake-output-00053-c1-20261010.txt     |    30 +
 ...blake-output-00053-c1-20261010.txt.receipt.json |    17 +
 .../blake-output-00053-c2-20261010-isolated.txt    |    25 +
 ...put-00053-c2-20261010-isolated.txt.receipt.json |    17 +
 ...20261010-50ac8b76d6804401b8d9830e5aca3dcc.jsonl |   305 +
 ...0261010-50ac8b76d6804401b8d9830e5aca3dcc.stderr |     0
 ...isolated-f4d99ec9d703472d8106aaa61685dc6b.jsonl |   330 +
 ...solated-f4d99ec9d703472d8106aaa61685dc6b.stderr |     0
 .../bob-output-00053-c1-20261010-isolated.txt      |    41 +
 ...put-00053-c1-20261010-isolated.txt.receipt.json |    17 +
 .../reviews/bob-output-00053-c1-20261010.txt       |    43 +
 .../bob-output-00053-c1-20261010.txt.receipt.json  |    17 +
 .../reviews/bob-output-00053-c2-20261010.txt       |    52 +
 .../bob-output-00053-c2-20261010.txt.receipt.json  |    17 +
 docs/driver-protocol.md                            |    37 +-
 src/ovcaq/drivers/claude.py                        |     4 +-
 src/ovcaq/drivers/codex.py                         |     8 +-
 src/ovcaq/drivers/codex_events.py                  |    20 +-
 src/ovcaq/drivers/edge.py                          |    25 +-
 tests/drivers/test_adapter_failure_classes.py      |   262 +
 tests/drivers/test_adapter_outcomes.py             |   294 +
 tests/drivers/test_codex_decode_terminals.py       |    21 +-
 tests/drivers/test_codex_failures.py               |    11 +-
 tests/drivers/test_codex_launch.py                 |    87 +-
 tests/drivers/test_codex_rework_decode.py          |     2 +-
 tests/runtime/test_adapter_health.py               |   339 +
 tests/runtime/test_adapter_launch_routing.py       |   143 +
 tests/runtime/test_supervisor_adapters.py          |    10 +-
 375 files changed, 72362 insertions(+), 106 deletions(-)
```

### Diff Content
Full diff available at: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/review-diff-00053-five-repair-20261012.diff

(75017 lines)

## PRD Requirements

---
catchup: run
design: run
rework_cap: 2
default_model: opus
model_tier_rationale: diagnostic classification and model handoff require new predicates with regression preservation
---

# Adapter operational corrections

## Overview

### Problem Statement

[PRD 00009 review 2](../../reviews/00009-codex-adapter-v1-review-2.md) R1,
R4, R19, R20 and R23 reproduce incorrect terminal lanes, overload policy,
double model resolution, numeric false diagnoses, and overlay PATH rejection.
R12/R22 identify missing independent regression coverage for these paths.
This repairs completed adapter behavior under the [resolved discovery](../../discovery/00001-ovcaq-v1.md)
and [architecture](../../plans/implementation-plan.md), before provisioning.
Premise: recheck each finding at execution; if already corrected, retain a
regression and report it instead of forcing a production edit.

### Target Users

Operators using configured model tiers, wrapper PATHs and native agent diagnostics.

### Success Metrics

Named regressions prove correct argv, no spawn after failed health checks,
bounded overload retries, stable completed lanes and literal failure classes.
Keep driver API 2, observation protocol 1 and state schema 1 unchanged.

## Functional Decomposition

### Capability: Accurate native outcomes

#### Feature: Completed lane stability
- **Description**: A later close/wait cannot turn an already completed lane into failure.
- **Inputs**: Native lane running, completed, then shutdown/interrupted/not_found.
- **Outputs**: Existing normalized lane observations.
- **Behavior**: Only remembered unfinished lanes qualify for synthetic failure
  on these statuses. A completed lane remains completed; running-then-interrupted
  still fails. No TUI lifecycle workaround or new terminal state.

#### Feature: Diagnostic classification
- **Description**: Distinguish transient capacity from quota and unrelated numbers.
- **Inputs**: Native failure diagnostics and existing versioned failure fixtures.
- **Outputs**: Existing FailureClass values with unchanged precedence.
- **Behavior**: 'Selected model is at capacity' is connectivity, entering the
  existing bounded WAIT/retry policy. Numeric 401/403/429/502/503 classify only
  in explicit HTTP/status/error-code diagnostic contexts; 'processed 401 files'
  and equivalent ordinary counts remain unknown. Retain existing meaningful
  word-based diagnostics and genuine quota classification. Do not expand reset
  grammar or scan arbitrary agent prose. Pin every failure fixture's expected
  class as a literal independent oracle, not a call to classify_failure.

### Capability: Faithful configured launch

#### Feature: Resolve model once
- **Description**: Launch the model chosen by resolve_phase_route without remapping it.
- **Inputs**: Configured tiers including `{default: o3, o3: o3-pro}`.
- **Outputs**: Literal model argument selected by the route.
- **Behavior**: A supervised route for default launches o3. Preserve the existing
  direct build_launch tier-key precedence, explicit-model opt-in validation and
  the provider-neutral supervisor. Follow the existing edge adaptation pattern;
  do not reverse public tier precedence or introduce a second model policy.

#### Feature: Probe launch PATH
- **Description**: Health checks resolve executable names under the launch environment.
- **Inputs**: Host environment plus configured PATH overlay and wrapper argv.
- **Outputs**: Existing DriverHealth result and shared no-spawn failure.
- **Behavior**: A command available only through the overlay probes healthy;
  an overlay that hides it probes unhealthy. Absolute paths retain behavior.
  Cover both adapters' health failure before spawn without real inference.

## Structural Decomposition

### Repository Structure

```text
src/ovcaq/drivers/{codex.py,codex_events.py,claude.py}
src/ovcaq/drivers/edge.py                 # existing edge factories
tests/drivers/test_adapter_outcomes.py   # new behavioral regressions
tests/drivers/test_adapter_failure_classes.py
tests/drivers/test_codex_decode_terminals.py
tests/runtime/test_adapter_launch_routing.py # new real-fake launch checks
tests/runtime/test_adapter_health.py     # new no-spawn/overlay checks
docs/driver-protocol.md
CHANGELOG.md
```

### Module: Native outcomes
- **Maps to capability**: Accurate native outcomes.
- **Responsibility**: Provider-edge lane and failure interpretation, independent
  driver regressions and corresponding protocol documentation.
- **Exports**: Existing CodexDriver.decode, item_lanes and classify_failure contracts.

### Module: Launch edges
- **Maps to capability**: Faithful configured launch.
- **Responsibility**: Correct model/environment adaptation, runtime regression
  fixtures and user-facing changelog entries.
- **Exports**: Existing driver probe/build_launch and registered factory interfaces.

## Dependency Graph

### Foundation Layer (Phase 0)
- **Native outcomes**: Existing drivers, event protocol and shared decision policy.

### Core Layer (Phase 1)
- **Launch edges**: Existing route resolver and driver registry; independent of
  outcome changes but executed after them to avoid shared-file contention.

### Integration Layer (Phase 2)
- **Regression/documentation closeout**: Depends on Native outcomes and Launch edges.
- Execute after PRDs 00051 and 00052; do not reopen their safety or version contracts.

## Implementation Phases

### Phase 0: Foundation
**Goal**: Correct lane and diagnostic outcomes.

**Tasks**:
- [ ] Repair native outcomes and independent fixture expectations (no deps).
  Acceptance: `uv run pytest tests/drivers/test_adapter_outcomes.py
  tests/drivers/test_adapter_failure_classes.py
  tests/drivers/test_codex_decode_terminals.py` covers each completed/unfinished
  lane status, capacity WAIT and retry exhaustion, genuine HTTP diagnostics,
  unrelated numeric counts, and all failure fixtures with literal expected classes.

**Exit Criteria**: Native outcomes choose the existing correct lifecycle policy.

### Phase 1: Core
**Goal**: Make configured launches match their preflight and resolved route.

**Tasks**:
- [ ] Correct resolved-model edge adaptation (depends on: Phase 0).
  Acceptance: `uv run pytest tests/runtime/test_adapter_launch_routing.py
  tests/drivers/test_codex_launch.py` proves colliding tier/model values launch the
  route's model through the real fake supervisor and direct tier-key precedence remains.
- [ ] Correct PATH probing and both-adapter no-spawn coverage (depends on: Phase 0).
  Acceptance: `uv run pytest tests/runtime/test_adapter_health.py` covers temporary
  executable available only on overlay PATH, hidden host executable, absolute
  executable, and unhealthy launch prevention for both native adapters.

**Exit Criteria**: Route selection, health checks and actual spawn agree.

### Phase 2: Integration
**Goal**: Close the documented findings with coherent public behavior.

**Tasks**:
- [ ] Update protocol and changelog for the repaired behavior (depends on: Phase 1).
  Acceptance: documents describe once-resolved models, effective PATH probing,
  completed-lane stability and capacity connectivity; no new options or schemas.

**Exit Criteria**: `uv sync --all-groups`, `uv run pytest`, `uv run ruff check .`,
`uv run ruff format --check .`, `uv run mypy src/ovcaq` and `uv build` pass.
Full mandatory review runs in a fresh session after build handoff.

## Test Strategy

### Critical Scenarios
- **Happy path**: Ordinary configured routes and native terminals retain behavior.
- **Edge case**: Model value is another tier key; overlay PATH differs from host.
- **Error case**: Transient capacity retries with bounds; ordinary counts never
  masquerade as authentication, permission, quota or connectivity failures.

## Risks

- **Public compatibility**: Preserve direct tier precedence and strict argv behavior.
- **Broad matching**: Pin positive diagnostic forms and numeric negative controls.
- **Scope**: No rate-reset grammar, tier-default migration, probe descendant
  ownership redesign, provisioning or other held triage work.

## Design Doc

# Adapter operational corrections design

## Architecture fit

Repair provider-edge behavior from PRD 00009 without changing shared policy, driver API 2, observation protocol 1 or state schema 1. The operator owns local operation. Existing bounded retries and raw evidence remain authoritative. These are reversible code changes with no persistent-data migration; revert the repair commits if needed. PRD 00052 remains held and its strict version contract is untouched.

## Module placement

Edit `src/ovcaq/drivers/codex.py`, `codex_events.py`, `claude.py` and `edge.py` only where reproduced defects require changes. Add the PRD-named driver/runtime regression files and update existing fixture/terminal tests. Update `docs/driver-protocol.md` and `CHANGELOG.md` after behavioral work.

## Interfaces & contracts

Keep public `CodexDriver.build_launch(request: LaunchRequest) -> LaunchSpec` tier-key precedence unchanged, including explicit-model validation. Add a private `_ResolvedModelCodexDriver(CodexDriver)` in `drivers/edge.py`, mirroring `_ResolvedModelClaudeDriver`: its `build_launch` maps a configured model value back to a corresponding tier key before delegating. `build_driver` constructs this subclass for supervised routes. A resolved `o3` with tiers `{default: o3, o3: o3-pro}` must launch literal `o3`; direct `CodexDriver` given `o3` still launches `o3-pro`. The supervisor passes only selected.tiers[resolved.tier], per config.py:resolve_phase_route, so every supervised model is necessarily a configured tier value. A no-match literal cannot originate from this route; preserve public validation for any direct call rather than inventing a new explicit-model path. No provider strings or special cases enter shared runtime.

`item_lanes(item: object, started_lanes: set[str] | None = None)` retains its signature and return shape. The set passed by `CodexDriver._item_observations` contains only remembered lane identities whose terminal flag is false. `interrupted`, `shutdown`, and `not_found` synthesize `LANE_FAILED` only for those unfinished identities; completed lanes retain their completed observation history. Unsupported terminal statuses otherwise produce raw-unknown evidence. No additional lane state or TUI policy.

`classify_failure(detail: str) -> FailureClass` keeps authentication, permission, rate-limit, connectivity, timeout, agent precedence. Numeric 401/403/429/502/503 require explicit diagnostic context such as HTTP status, status code or error code, including genuine fixture spellings. Ordinary numeric counts remain UNKNOWN. Retain meaningful existing word diagnostics; `Selected model is at capacity` becomes CONNECTIVITY, using existing bounded WAIT/retry exhaustion. Do not change `failure_reset` grammar. Fixture expectations are literal independent oracles, never derived through the production classifier.

`ClaudeDriver.probe() -> DriverHealth` uses effective environment `os.environ` overlaid by configured launch environment when calling `shutil.which(command, path=effective_path)`. Explicit empty PATH stays empty; absent PATH follows subprocess/default PATH semantics. Absolute executable paths retain existing behavior. Codex probes already spawn with `dict(os.environ) | dict(settings.environment)`; reproduce and regress that behavior rather than changing it gratuitously. Both native adapters must fail health before supervisor spawn when command resolution is unhealthy. Fake Codex version/auth commands use the existing reviewed pin, never a live provider or a changed pin.

## Data flow

Supervisor route resolution passes a concrete configured value to the edge factory's driver; edge adaptation preserves that value through public tier resolution. Probe and launch see the same PATH overlay. Native records become existing observations; unfinished identity state controls synthetic lane failures. Connectivity summaries drive existing bounded retry policy. Raw JSONL remains available regardless of normalization.

## Reuse inventory

- `drivers/edge.py:_ResolvedModelClaudeDriver`: reuse inverse-tier adaptation for Codex without a second shared routing policy.
- `drivers/codex.py:_identities`, `_remember`: existing bounded terminal flags provide unfinished identity membership.
- `drivers/codex_events.py:item_lanes`, `classify_failure`: repair predicates in place, retain failure_reset and enum contracts.
- `drivers/codex.py:probe`, `_run_probe_command`: existing effective-environment subprocess probing supplies Codex PATH semantics.
- `drivers/claude.py:probe`, `_environment`: use existing launch environment for executable lookup.
- Existing fake-supervisor and fixture suites supply process isolation and bounded retry verification.

## Alternatives considered

1. Smallest diff: filter unfinished identities, constrain diagnostic numbers, and mirror the existing edge subclass. Chosen: preserves direct APIs and keeps provider adaptation at the edge.
2. Add a public resolved-model request flag or change direct tier precedence. Rejected: enlarges the driver contract and breaks existing callers.
3. Implement lifecycle or retry compensation in the TUI/shared runtime. Rejected: duplicates policy and violates the adapter boundary.

## Risks & edge cases

Repeated lane updates, unknown identities and bounded identity eviction must retain raw fallback. Numeric context must cover genuine fixtures without interpreting arbitrary prose counts. PATH absence and empty PATH differ. Duplicate configured model values may choose any matching key because each maps to the same literal value. Future native statuses, additional diagnostic spellings and launcher version updates can extend adapter fixtures independently; none requires broadening the strict pin or reset grammar now.

## Test strategy outline

Independent tests cover completed/running lane sequences for all three close statuses; positive numeric diagnostics and negative counts; literal class expectations for every failure fixture; capacity WAIT and retry exhaustion. Real fake-process supervisor tests capture colliding model argv and verify overlay-only, hidden-host and absolute executables plus both adapters' health-failure no-spawn. Preserve direct launch tests and run all six PRD verification gates after tasks. Full completion review runs in a fresh session.

## Review log

Dispatch 1 question: existing test_codex_failures bare-number precedence and test_codex_rework_decode capacity expectations conflict with corrected contract; planning must reconcile them while retaining independent literals. Native host mapping OpenAI gpt-6.1-sol/high; no blockers.
Dispatch 1 engagement retry question: absent PATH must use subprocess os.defpath; empty PATH needs an explicit conservative-health expectation. Anchored numeric, empty/missing PATH, collisions and eviction checked.
dispatch 1 (claude): cardinal-sin 0, blocker 0, non-blocker 0, question 2
Host identity above is the source schema label; actual native OpenAI gpt-6.1-sol/high.

Dispatch 2 non-blockers: empty/absent PATH semantics; completed/evicted/None lane details; cite retry bounds; enumerate diagnostic patterns; reconcile historical test literals. Questions: health gate location and classification policy wording. Raw output: docs/dev/tmp/00053-design-review-anthropic.txt. Blocker 1 closed by explicit supervised-route invariant (config.py:resolve_phase_route always selects a configured tier value); direct public validation unchanged.
dispatch 2 (codex): cardinal-sin 0, blocker 1, non-blocker 5, question 2
Host role swap: actual Anthropic sonnet via real use-sonnet wrapper, tool-less read-only; source codex is logical dispatch label only.

Dispatch 3: closed model blocker using supplied config/edge excerpts. Questions: same-agent route/factory invariant and health gate location. Existing drivers/base.py:_register_driver is confirmed health gate; CodexDriver.__init__ sets _settings. Non-blockers retained: PATH fallback, bounded retry citations, diagnostic spellings, lane edge cases, historical test literals, attribute citation and review-log hygiene. Raw verification output: docs/dev/tmp/00053-design-review-verify-anthropic.txt.
dispatch 3 (codex): cardinal-sin 0, blocker 0, non-blocker 7, question 2
Actual Anthropic sonnet, read-only use-sonnet host adaptation. All cardinal sins/blockers closed; 3/3 dispatches; no weak dispatches.

## Mechanical facts (computed, do not re-count)

Function line counts from `ast`. Cite these for countable claims; a
finding that contradicts this block is discarded at the review gate.

- `CHANGELOG.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-metrics.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/20e00488d69c4049841e98345186f7e4.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/20e00488d69c4049841e98345186f7e4.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/20e00488d69c4049841e98345186f7e4.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/279781a2783542beaaa8681f17114874.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/279781a2783542beaaa8681f17114874.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/279781a2783542beaaa8681f17114874.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/347829f3e7c8444db80f7c361aa1829a.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/347829f3e7c8444db80f7c361aa1829a.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/347829f3e7c8444db80f7c361aa1829a.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/506935de425a4e46b8594c70db3d1b14.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/506935de425a4e46b8594c70db3d1b14.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/506935de425a4e46b8594c70db3d1b14.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/73283477de354a7f8ada998665ea18c5.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/73283477de354a7f8ada998665ea18c5.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/73283477de354a7f8ada998665ea18c5.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/802d38c005794cfaa2b4a8e5c972ab1e.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/802d38c005794cfaa2b4a8e5c972ab1e.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/802d38c005794cfaa2b4a8e5c972ab1e.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/89a9a06960fb4564bc91d44a5a751a72.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/89a9a06960fb4564bc91d44a5a751a72.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/89a9a06960fb4564bc91d44a5a751a72.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/992dfab37880403fb77de3760d4ffbe2.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/992dfab37880403fb77de3760d4ffbe2.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/992dfab37880403fb77de3760d4ffbe2.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/b184edc3051047e1a011ea374b1f90d7.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/b184edc3051047e1a011ea374b1f90d7.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/b184edc3051047e1a011ea374b1f90d7.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/b8f0813f1cf84d20ac0f325bc1d82c35.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/b8f0813f1cf84d20ac0f325bc1d82c35.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/b8f0813f1cf84d20ac0f325bc1d82c35.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/f3e5d6d880fa45028ec82cb08e5b5de6.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/f3e5d6d880fa45028ec82cb08e5b5de6.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/autocodex-sessions/f3e5d6d880fa45028ec82cb08e5b5de6.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/contract-card.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/dispatch-metrics.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/last-verification.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/ledger/dispatch-metrics.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00051-assumptions-snapshot.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-00053-design-review-anthropic.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-00053-design-review-verify-anthropic.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-adapter-operational-corrections-v1-implementation-models-cycle-1.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-adapter-operational-corrections-v1-implementation-models-cycle-1.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-adapter-operational-corrections-v1-implementation-models-cycle-2-pre-postrepair.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-adapter-operational-corrections-v1-implementation-models-cycle-2-pre-sweep.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-adapter-operational-corrections-v1-implementation-models-cycle-2-pre-sweep.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-adapter-operational-corrections-v1-implementation-models.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-adapter-operational-corrections-v1-implementation-models.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-adversarial-evidence/devon_2-rollout-2026-10-10T13-13-18-01a12584-6da8-7ab3-b3fb-3199ecb95674.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-adversarial-evidence/devon_3_current-rollout-2026-10-10T13-31-36-01a12595-30c4-7ea2-9f5b-7d30acd36845.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-approved-task-reviews-handoff.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-build-progress.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-cleanup.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-host-recovery-20261012-handoff.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-host-recovery-20261012-verification.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-correlations.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/ivan_2_current-rollout-2026-10-10T13-23-34-01a1258d-d5e8-7ff2-bd56-564762d91666.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/ivan_3_current-rollout-2026-10-10T13-37-05-01a1259a-368d-7cc0-a13c-6508d855e6a1.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/ivan_4_correction-rollout-2026-10-10T13-41-57-01a1259e-a86e-7991-a8f6-10e6fdbb3b27.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/ivan_4_current-rollout-2026-10-10T13-39-40-01a1259c-9163-7e91-aba2-00ac86f909e2.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/ivan_5-rollout-2026-10-10T12-47-53-01a1256d-2a93-70f2-a11a-e7f8016a3f00.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/ivan_6-rollout-2026-10-10T13-03-31-01a1257b-7994-7a30-ada3-382d34279d26.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/ivan_format_2-rollout-2026-10-10T13-52-22-01a125a8-3296-7a82-b8c1-ffba26eb9c8b.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/ivan_format_3-rollout-2026-10-10T13-53-22-01a125a9-1e1c-7410-9ac5-a2be36a4a33b.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/ivan_format_5-rollout-2026-10-10T13-48-06-01a125a4-4a43-7053-8bd7-3d710ff4e836.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/tess_1-rollout-2026-10-10T12-35-19-01a12561-a6e6-73a2-b0a8-66ba9751f8f8.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/tess_2-rollout-2026-10-10T13-07-23-01a1257f-0555-7891-bc0a-9cc852e4be16.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/tess_2_strengthen-rollout-2026-10-10T13-18-38-01a12589-50f8-7370-9967-aaa607f37385.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/tess_3_current-rollout-2026-10-10T13-26-14-01a12590-45f8-7373-8770-0aea39dc3ba0.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/tess_3_quality_current-rollout-2026-10-10T13-29-58-01a12593-b073-7b91-a8da-9c1fd1cb6421.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/tess_3_strengthen_current-rollout-2026-10-10T13-34-54-01a12598-3682-75b0-99c2-c96af917308d.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/tess_5-rollout-2026-10-10T12-37-48-01a12563-eda6-7cd1-904f-6abc2463ec74.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/tess_5_strengthen-rollout-2026-10-10T12-45-55-01a1256b-5e70-7a10-b173-31767b9534c0.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/tess_6-rollout-2026-10-10T12-50-35-01a1256f-a3f7-75e2-a996-23e21c05a817.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/tess_6_interface-rollout-2026-10-10T12-56-39-01a12575-2fdb-7592-8d80-d4da98980196.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-model-evidence/tess_6_strengthen-rollout-2026-10-10T13-01-47-01a12579-e43e-7fa2-8697-2ecfaf0ebb24.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-plugin-repin-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/attempt-task-18.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/attempt-task-19.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/attempt-task-20.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/author-evidence.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/dispatch-ivan-19.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/ivan-19.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/micro-author.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-18-acceptance.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-18-approved.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-18-approved.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-18-description.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-18-prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-18-subject.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-18-verification.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-20-acceptance.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-20-approved.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-20-approved.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-20-description.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-20-prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-20-subject.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/review-task-20-verification.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/task-diff-18.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-evidence/task-diff-20.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-model-evidence.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-recovery-20261012-work.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-repair-authorization.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/alice-output-71006cca714e4990ac519742ea445bf2.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/alice-output-71006cca714e4990ac519742ea445bf2.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/alice-output.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/alice-output.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/alice-prompt-00053-postrepair-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/blake-output-a6d87910ee7743fd83acd241486d3ed5.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/blake-output-a6d87910ee7743fd83acd241486d3ed5.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/blake-output.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/blake-output.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/blake-prompt-00053-postrepair-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/bob-output-cebe25bde513499a910b4c0179c35df1.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/bob-output-cebe25bde513499a910b4c0179c35df1.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/bob-output.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/bob-output.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/bob-prompt-00053-postrepair-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/consolidated.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/diff-archive.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/review-context-00053-postrepair-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/review-diff-00053-postrepair-20261012.diff.gz` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/review-prd-00053-postrepair-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/review-tasks-00053-postrepair-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-validation.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/attempt-task-15.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/attempt-task-16.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/attempt-task-17.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/coordinator-source.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/coordinator.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/dispatch-ivan-15.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/dispatch-settings.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/dispatch-tess-15.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/ivan-15-files.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/ivan-15-spec.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/ivan-15.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/pat-15.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/pat-17.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-15-acceptance.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-15-description.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-15-prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-15-subject.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-15-verification.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-15.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-17-acceptance.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-17-description.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-17-prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-17-subject.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-17-verification.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/review-task-17.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/task-diff-15.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/task-diff-17.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/tess-15-acceptance.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/tess-15-api.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/tess-15-description.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/tess-15-subject.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/tess-15.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-evidence/test-diff-15.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-model-evidence.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012-verification.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-repair-authorization.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/alice-output-00053-c2-postsweep-20261012-e4a60124252b443c88dc5d26966dfe81.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/alice-output-00053-c2-postsweep-20261012-e4a60124252b443c88dc5d26966dfe81.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/alice-output-00053-c2-postsweep-20261012.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/alice-output-00053-c2-postsweep-20261012.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/alice-prompt-00053-c2-postsweep-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/blake-output-00053-c2-postsweep-20261012-cf6275c6d78746a09b1227953ed3875b.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/blake-output-00053-c2-postsweep-20261012-cf6275c6d78746a09b1227953ed3875b.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/blake-output-00053-c2-postsweep-20261012.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/blake-output-00053-c2-postsweep-20261012.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/blake-prompt-00053-c2-postsweep-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/bob-output-00053-c2-postsweep-20261012-fa107f9cf6d14f7d9878c651c416815d.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/bob-output-00053-c2-postsweep-20261012-fa107f9cf6d14f7d9878c651c416815d.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/bob-output-00053-c2-postsweep-20261012.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/bob-output-00053-c2-postsweep-20261012.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/bob-prompt-00053-c2-postsweep-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/consolidated-script.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/review-context-00053-c2-postsweep-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/review-diff-00053-c2-postsweep-20261012.diff` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/review-prd-00053-c2-postsweep-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/review-tasks-00053-c2-postsweep-20261012.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-evidence/reviewer-metadata.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-handoff.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-postsweep-review-20261012-validation.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-cleanup.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/00053-adapter-operational-corrections-v1-decision-gate-1-findings.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/00053-adapter-operational-corrections-v1-implementation-models.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/00053-adapter-operational-corrections-v1-implementation-models.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/00053-review-pytest.log` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/00053-review-test-gate.py` — no functions
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/alice-prompt-00053-c1-20261010-approved.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/alice-prompt-00053-c1-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/blake-prompt-00053-c1-20261010-approved.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/blake-prompt-00053-c1-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/bob-prompt-00053-c1-20261010-approved.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/bob-prompt-00053-c1-20261010-isolated.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/bob-prompt-00053-c1-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/consolidator-stderr.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/review-context-00053-c1-20261010-approved.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/review-context-00053-c1-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/review-diff-00053-c1-20261010-approved.diff` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/review-prd-00053-c1-20261010-approved.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/review-prd-00053-c1-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/review-prd-raw-00053-c1-20261010-approved.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/review-prd-raw-00053-c1-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/review-tasks-00053-c1-20261010-approved.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-evidence/review-tasks-00053-c1-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-1-verification.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-cleanup.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/00053-adapter-operational-corrections-v1-decision-gate-2-findings.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/00053-adapter-operational-corrections-v1-tail-sweep-2-findings.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/alice-output-00053-c2-20261010-01abbbef9d2045688ec6cffb740060c3.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/alice-output-00053-c2-20261010-01abbbef9d2045688ec6cffb740060c3.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/alice-output-00053-c2-20261010.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/alice-output-00053-c2-20261010.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/alice-prompt-00053-c2-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/blake-output-00053-c2-20261010-a3b8ab94dd554de28d3e282362869911.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/blake-output-00053-c2-20261010-a3b8ab94dd554de28d3e282362869911.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/blake-output-00053-c2-20261010-isolated-8526130ad66c4348868a1e8d29205983.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/blake-output-00053-c2-20261010-isolated-8526130ad66c4348868a1e8d29205983.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/blake-output-00053-c2-20261010-isolated.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/blake-output-00053-c2-20261010-isolated.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/blake-output-00053-c2-20261010.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/blake-output-00053-c2-20261010.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/blake-prompt-00053-c2-20261010-isolated.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/blake-prompt-00053-c2-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/bob-output-00053-c2-20261010-58735a23c3bb4aeb8a381d670e6ec151.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/bob-output-00053-c2-20261010-58735a23c3bb4aeb8a381d670e6ec151.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/bob-output-00053-c2-20261010.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/bob-output-00053-c2-20261010.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/bob-prompt-00053-c2-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/chosen-findings.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/consolidation-original.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/consolidation.stderr` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/ovcaq-review2-pause.py`
  - `call` — line 11, 2 lines
  - `set_value` — line 13, 2 lines
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/ovcaq-review2-report.py` — no functions
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/review-context-00053-c2-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/review-diff-00053-c2-20261010.diff` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/review-prd-00053-c2-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/review-prd-raw-00053-c2-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-evidence/review-tasks-00053-c2-20261010.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-sandbox-verification.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-summary.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-review-2-verification.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/coordinator-model-metadata.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/coordinator-model-metadata.raw.source.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/attempt-task-10.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/attempt-task-7.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/attempt-task-8.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/attempt-task-9.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/dispatch-ivan-7.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/dispatch-ivan-8.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/dispatch-tess-7.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/ivan-7-checks.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/ivan-7-context.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/ivan-7-files.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/ivan-8-checks.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/ivan-8-context.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/ivan-8-files.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-10-acceptance.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-10-description.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-10-prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-10-subject.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-10-verification.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-10.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-7-acceptance.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-7-description.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-7-prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-7-subject.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-7-verification.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-7.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-8-acceptance.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-8-description.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-8-prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-8-subject.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-8-verification.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-8.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-9-acceptance.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-9-description.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-9-prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-9-subject.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-9-verification.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/review-task-9.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/task-diff-10.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/task-diff-7.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/task-diff-8.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/tess-7-acceptance.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/tess-7-description.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/tess-7-interfaces.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/tess-7-subject.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/inputs/test-diff-7.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/ivan-7.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/ivan-8.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/pat-10.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/pat-10.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/pat-7.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/pat-7.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/pat-8.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/pat-8.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/pat-9.prompt.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/pat-9.txt` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-evidence/tess-7.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-model-evidence.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-report.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-rework-1-verification.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-signing-recovery.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-source-findings.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-tail-sweep-20261011-pat-11.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-tail-sweep-20261011-pat-12.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-tail-sweep-20261011-pat-13.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-tail-sweep-20261011-pat-14.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-tail-sweep-20261011-turn-metadata.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-tail-sweep-20261011.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-tail-sweep-authorization.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-tail-sweep-model-evidence/ivan11.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-tail-sweep-model-evidence/micro.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-tail-sweep-model-evidence/tess11.raw.jsonl` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-tail-sweep-signing-pause.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-task11-signing-recovery-20261011.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-task2-pat.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-task3-pat.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-task5-pat.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-task6-pat.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/00053-verification-initial.json` — skipped (non-python)
- `docs/dev/project-management/autopilot/reports/repair-readiness-20261007.md` — skipped (non-python)
- `docs/dev/project-management/autopilot/session-brief.md` — skipped (non-python)
- `docs/dev/project-management/designs/00053-adapter-operational-corrections-v1-design.md` — skipped (non-python)
- `docs/dev/project-management/meta/assumptions.md` — skipped (non-python)
- `docs/dev/project-management/meta/project-capsule.md` — skipped (non-python)
- `docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md` — skipped (non-python)
- `docs/dev/project-management/reviews/00053-adapter-operational-corrections-v1-checks-1.json` — skipped (non-python)
- `docs/dev/project-management/reviews/00053-adapter-operational-corrections-v1-checks-2.json` — skipped (non-python)
- `docs/dev/project-management/reviews/00053-adapter-operational-corrections-v1-ledger.json` — skipped (non-python)
- `docs/dev/project-management/reviews/00053-adapter-operational-corrections-v1-review-1.md` — skipped (non-python)
- `docs/dev/project-management/reviews/00053-adapter-operational-corrections-v1-review-2-postrepair-20261012.md` — skipped (non-python)
- `docs/dev/project-management/reviews/00053-adapter-operational-corrections-v1-review-2-postsweep-20261012.md` — skipped (non-python)
- `docs/dev/project-management/reviews/00053-adapter-operational-corrections-v1-review-2.md` — skipped (non-python)
- `docs/dev/project-management/reviews/alice-output-00053-c1-20261010-536db8fa0d974849a0e9dbf16ee412ce.jsonl` — skipped (non-python)
- `docs/dev/project-management/reviews/alice-output-00053-c1-20261010-536db8fa0d974849a0e9dbf16ee412ce.stderr` — skipped (non-python)
- `docs/dev/project-management/reviews/alice-output-00053-c1-20261010.txt` — skipped (non-python)
- `docs/dev/project-management/reviews/alice-output-00053-c1-20261010.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/reviews/alice-output-00053-c2-20261010.txt` — skipped (non-python)
- `docs/dev/project-management/reviews/alice-output-00053-c2-20261010.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/reviews/blake-output-00053-c1-20261010-de1e8e0e176c4d6f9b78bf0d26530c7e.jsonl` — skipped (non-python)
- `docs/dev/project-management/reviews/blake-output-00053-c1-20261010-de1e8e0e176c4d6f9b78bf0d26530c7e.stderr` — skipped (non-python)
- `docs/dev/project-management/reviews/blake-output-00053-c1-20261010.txt` — skipped (non-python)
- `docs/dev/project-management/reviews/blake-output-00053-c1-20261010.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/reviews/blake-output-00053-c2-20261010-isolated.txt` — skipped (non-python)
- `docs/dev/project-management/reviews/blake-output-00053-c2-20261010-isolated.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/reviews/bob-output-00053-c1-20261010-50ac8b76d6804401b8d9830e5aca3dcc.jsonl` — skipped (non-python)
- `docs/dev/project-management/reviews/bob-output-00053-c1-20261010-50ac8b76d6804401b8d9830e5aca3dcc.stderr` — skipped (non-python)
- `docs/dev/project-management/reviews/bob-output-00053-c1-20261010-isolated-f4d99ec9d703472d8106aaa61685dc6b.jsonl` — skipped (non-python)
- `docs/dev/project-management/reviews/bob-output-00053-c1-20261010-isolated-f4d99ec9d703472d8106aaa61685dc6b.stderr` — skipped (non-python)
- `docs/dev/project-management/reviews/bob-output-00053-c1-20261010-isolated.txt` — skipped (non-python)
- `docs/dev/project-management/reviews/bob-output-00053-c1-20261010-isolated.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/reviews/bob-output-00053-c1-20261010.txt` — skipped (non-python)
- `docs/dev/project-management/reviews/bob-output-00053-c1-20261010.txt.receipt.json` — skipped (non-python)
- `docs/dev/project-management/reviews/bob-output-00053-c2-20261010.txt` — skipped (non-python)
- `docs/dev/project-management/reviews/bob-output-00053-c2-20261010.txt.receipt.json` — skipped (non-python)
- `docs/driver-protocol.md` — skipped (non-python)
- `src/ovcaq/drivers/claude.py`
  - `ClaudeDriver.__init__` — line 40, 34 lines
  - `ClaudeDriver.default_prompt` — line 75, 4 lines
  - `ClaudeDriver.probe` — line 80, 11 lines
  - `ClaudeDriver.build_launch` — line 92, 39 lines
  - `ClaudeDriver.decode` — line 132, 32 lines
  - `ClaudeDriver._decode_record` — line 165, 39 lines
  - `ClaudeDriver._decode_message` — line 205, 37 lines
  - `ClaudeDriver._decode_tasks` — line 243, 20 lines
  - `ClaudeDriver._decode_result` — line 264, 45 lines
  - `ClaudeDriver._observation` — line 310, 17 lines
  - `ClaudeDriver._update_usage` — line 328, 35 lines
  - `ClaudeDriver._remember_usage` — line 364, 26 lines
  - `ClaudeDriver.summarize` — line 391, 4 lines
- `src/ovcaq/drivers/codex.py`
  - `_run_probe_command` — line 42, 41 lines
  - `_probe_failure` — line 85, 17 lines
  - `CodexDriver.__init__` — line 116, 17 lines
  - `CodexDriver.build_launch` — line 134, 43 lines
  - `CodexDriver.probe` — line 178, 36 lines
  - `CodexDriver.decode` — line 215, 45 lines
  - `CodexDriver._failure_observations` — line 261, 42 lines
  - `CodexDriver._usage_observations` — line 304, 44 lines
  - `CodexDriver._item_observations` — line 349, 46 lines
  - `CodexDriver._remember` — line 396, 42 lines
  - `CodexDriver._observation` — line 439, 17 lines
  - `CodexDriver.summarize` — line 457, 47 lines
  - `CodexDriver.default_prompt` — line 505, 4 lines
- `src/ovcaq/drivers/codex_events.py`
  - `item_activity` — line 17, 38 lines
  - `bounded_detail` — line 57, 11 lines
  - `turn_usage` — line 70, 48 lines
  - `command_detail` — line 120, 11 lines
  - `file_detail` — line 133, 12 lines
  - `mcp_detail` — line 147, 14 lines
  - `web_detail` — line 163, 31 lines
  - `collab_detail` — line 196, 9 lines
  - `item_lanes` — line 207, 47 lines
  - `item_tool` — line 256, 40 lines
  - `classify_failure` — line 298, 42 lines
  - `failure_reset` — line 342, 21 lines
- `src/ovcaq/drivers/edge.py`
  - `_map_model_to_tier` — line 16, 7 lines
  - `_ResolvedModelClaudeDriver.build_launch` — line 28, 2 lines
  - `_ResolvedModelCodexDriver.build_launch` — line 35, 2 lines
  - `build_driver` — line 39, 7 lines
- `tests/drivers/test_adapter_failure_classes.py`
  - `driver` — line 24, 9 lines
  - `running_snapshot` — line 35, 6 lines
  - `test_numeric_diagnostics_require_an_explicit_status_or_error_context` — line 57, 4 lines
  - `test_explicit_bare_status_diagnostics_are_classified` — line 75, 4 lines
  - `test_reqwest_and_http_version_status_diagnostics_are_classified` — line 107, 4 lines
  - `test_unsupported_numeric_status_forms_remain_unknown` — line 114, 2 lines
  - `test_unrelated_numbers_are_not_failure_diagnostics` — line 129, 4 lines
  - `test_ordinary_resource_capacity_is_unknown` — line 143, 2 lines
  - `test_numeric_diagnostics_require_a_complete_status_number` — line 148, 2 lines
  - `test_native_word_diagnostics_retain_case_without_widening_whitespace` — line 161, 4 lines
  - `test_generic_authentication_failure_messages_remain_unknown` — line 170, 2 lines
  - `test_failure_precedence_is_independent_of_diagnostic_order` — line 190, 4 lines
  - `test_authentication_is_classified_beyond_the_display_detail_limit` — line 197, 16 lines
  - `test_model_capacity_uses_connectivity_wait_until_exact_retry_bound` — line 224, 39 lines
- `tests/drivers/test_adapter_outcomes.py`
  - `driver` — line 12, 9 lines
  - `decode` — line 23, 2 lines
  - `collab_record` — line 27, 23 lines
  - `start_lane` — line 52, 18 lines
  - `test_completed_lane_remains_completed_after_close_status` — line 74, 23 lines
  - `test_unfinished_lane_fails_after_close_status` — line 101, 18 lines
  - `test_unknown_receiver_close_retains_raw_unknown` — line 122, 25 lines
  - `test_repeated_close_does_not_fail_lane_again` — line 150, 22 lines
  - `test_completed_receiver_does_not_prevent_unfinished_receiver_failure` — line 176, 25 lines
  - `test_unrelated_item_type_does_not_transition_lane` — line 204, 24 lines
  - `test_unrelated_event_type_does_not_transition_lane` — line 231, 24 lines
  - `test_finished_lane_late_update_retains_only_non_lane_observations` — line 266, 29 lines
- `tests/drivers/test_codex_decode_terminals.py`
  - `driver` — line 20, 9 lines
  - `decode` — line 31, 2 lines
  - `supplied` — line 35, 11 lines
  - `SingleUse.__init__` — line 49, 3 lines
  - `SingleUse.__iter__` — line 53, 4 lines
  - `test_native_failure_emits_classified_terminal_with_receipt_identity` — line 71, 25 lines
  - `test_fixture_error_then_identical_failure_has_one_terminal_and_rate_start` — line 107, 27 lines
  - `test_top_level_error_is_sanitized_provisional_activity` — line 136, 12 lines
  - `test_native_rate_failure_preserves_explicit_bounded_reset` — line 153, 16 lines
  - `test_provisional_rate_error_preserves_explicit_utc_reset_without_terminal` — line 171, 16 lines
  - `test_native_rate_failure_keeps_missing_or_invalid_reset_unknown` — line 203, 8 lines
  - `test_recovered_provisional_error_has_no_failure_or_rate_observations` — line 213, 16 lines
  - `test_nonfatal_item_error_never_supplies_provisional_failure_metadata` — line 231, 20 lines
  - `test_supplied_provisional_metadata_is_authoritative_without_prior_decode` — line 254, 22 lines
  - `test_latest_provisional_error_supersedes_earlier_normalized_metadata` — line 278, 26 lines
  - `test_empty_or_nonprovisional_input_preserves_shared_reducer_result` — line 307, 17 lines
  - `test_reused_driver_never_applies_stale_provisional_error` — line 326, 8 lines
  - `test_runtime_terminal_preserves_reducer_precedence_over_provisional_error` — line 339, 25 lines
  - `test_multiple_turn_terminals_preserve_shared_reducer_result` — line 366, 19 lines
  - `test_conflicting_terminal_identities_preserve_shared_reducer_result` — line 387, 21 lines
  - `test_malformed_failure_records_degrade_to_hashed_raw_without_state_changes` — line 422, 25 lines
- `tests/drivers/test_codex_failures.py`
  - `probe_root` — line 84, 9 lines
  - `probe_driver` — line 95, 28 lines
  - `probe_records` — line 125, 3 lines
  - `test_healthy_probe_checks_only_version_and_auth_with_closed_stdin` — line 130, 29 lines
  - `test_probe_rejects_missing_or_nonexecutable_binary` — line 162, 12 lines
  - `test_probe_reports_unhealthy_version_or_auth_status` — line 180, 21 lines
  - `test_probe_sanitizes_auth_credentials_on_stderr` — line 203, 9 lines
  - `test_probe_does_not_disclose_credentials_from_version_stdout` — line 217, 10 lines
  - `test_probe_bounds_oversized_output_without_disclosing_raw_credentials` — line 229, 16 lines
  - `test_probe_times_out_each_read_only_command_after_five_seconds` — line 248, 14 lines
  - `test_classifies_native_failure_detail_case_insensitively` — line 307, 4 lines
  - `test_failure_classification_uses_documented_precedence` — line 328, 4 lines
  - `test_numeric_status_substrings_in_identifiers_are_unknown` — line 336, 4 lines
  - `test_failure_reset_accepts_explicit_future_aware_resets` — line 353, 6 lines
  - `test_failure_reset_rejects_missing_ambiguous_invalid_or_unbounded_resets` — line 384, 4 lines
  - `test_failure_reset_compares_aware_now_using_its_actual_instant` — line 390, 5 lines
  - `test_failure_reset_anchors_relative_delay_to_supplied_now` — line 405, 6 lines
- `tests/drivers/test_codex_launch.py`
  - `toml_value` — line 18, 10 lines
  - `configured_driver` — line 30, 16 lines
  - `settings` — line 49, 8 lines
  - `launch_request` — line 60, 10 lines
  - `test_launch_has_exact_order_and_omits_unconfigured_flags` — line 78, 38 lines
  - `test_accepted_options_keep_the_safe_launch_defaults` — line 132, 6 lines
  - `test_constructor_rejects_unknown_or_invalid_options` — line 167, 6 lines
  - `test_tier_key_resolves_before_a_matching_configured_model_value` — line 186, 11 lines
  - `test_arbitrary_explicit_models_require_the_opt_in` — line 201, 26 lines
  - `test_unmapped_effort_warns_once_and_omits_the_override` — line 230, 15 lines
  - `test_blank_effort_is_rejected` — line 248, 6 lines
  - `test_building_a_launch_does_not_spawn_or_evaluate_literal_inputs` — line 256, 25 lines
  - `test_building_a_launch_does_not_spawn_or_evaluate_literal_inputs.unexpected_spawn` — line 262, 2 lines
- `tests/drivers/test_codex_rework_decode.py`
  - `driver` — line 18, 9 lines
  - `decode` — line 29, 2 lines
  - `failure_record` — line 33, 4 lines
  - `raw_reasons` — line 39, 9 lines
  - `tool_record` — line 50, 18 lines
  - `collab_record` — line 70, 14 lines
  - `test_native_diagnostics_have_independent_failure_classification` — line 100, 13 lines
  - `test_checked_in_connectivity_failure_uses_independent_oracle` — line 115, 18 lines
  - `test_failure_classifies_full_text_before_sanitizing_and_capping_detail` — line 136, 23 lines
  - `test_unsafe_tool_json_never_raises_and_explains_raw_gap` — line 163, 15 lines
  - `test_explicit_aware_rate_reset_accepts_punctuation_with_six_hour_ceiling` — line 182, 16 lines
  - `test_previously_started_receiver_closes_as_failed_on_non_success_terminal` — line 201, 18 lines
  - `test_malformed_usage_reason_survives_simultaneous_partition_gap` — line 226, 24 lines
  - `test_thread_conflict_reason_survives_simultaneous_usage_gap` — line 252, 25 lines
- `tests/runtime/test_adapter_health.py`
  - `isolated_homes` — line 22, 5 lines
  - `fake_executable` — line 29, 25 lines
  - `driver_for` — line 56, 16 lines
  - `assert_probe_evidence` — line 74, 13 lines
  - `test_probe_finds_executable_available_only_on_overlay_path` — line 90, 22 lines
  - `test_probe_rejects_absolute_command_that_is_not_an_executable_file` — line 116, 19 lines
  - `test_probe_rejects_file_without_execute_permission` — line 139, 19 lines
  - `test_probe_finds_executable_symlink_on_overlay_path` — line 161, 18 lines
  - `test_claude_probe_rejects_sh_hidden_by_overlay_path` — line 181, 14 lines
  - `test_probe_finds_executable_on_inherited_host_path` — line 198, 12 lines
  - `test_probe_rejects_host_executable_hidden_by_overlay_path` — line 213, 14 lines
  - `test_probe_preserves_absolute_executable_with_unrelated_overlay_path` — line 230, 14 lines
  - `test_claude_probe_uses_default_search_path_when_host_path_is_absent` — line 246, 15 lines
  - `test_claude_probe_keeps_empty_host_path_unhealthy` — line 264, 16 lines
  - `initialize_running_project` — line 282, 12 lines
  - `initialize_running_project.start` — line 287, 5 lines
  - `configure_project` — line 296, 14 lines
  - `test_unhealthy_overlay_blocks_supervised_phase_exec_and_publication` — line 313, 27 lines
- `tests/runtime/test_adapter_launch_routing.py`
  - `configured_workflow` — line 24, 35 lines
  - `test_configured_supervisor_launches_each_selected_literal_model_and_effort` — line 100, 44 lines
- `tests/runtime/test_supervisor_adapters.py`
  - `adapter_harness` — line 23, 15 lines
  - `workflow_fixture` — line 40, 13 lines
  - `workflow_agent` — line 55, 24 lines
  - `prepare_workflow` — line 81, 21 lines
  - `prepare_workflow.prepare` — line 95, 4 lines
  - `assert_handoff` — line 104, 40 lines
  - `assert_retained_evidence` — line 146, 11 lines
  - `assert_completed_results` — line 159, 8 lines
  - `test_builtin_fake_command_handoffs_drain_and_retain_completed_results` — line 170, 50 lines

## Tautological test shapes (computed, do not re-judge)

Each `[MECH]` line is a test whose shape cannot fail as written. Raise
it; step 6 adds any line the table lacks. `mech-check` is the finder.


Checked 79 test function(s) in 9 test file(s).

## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `7819970d7f80`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

replay: skipped (worktree add failed: Preparing worktree (detached HEAD 7819970)
fatal: could not create leading directories of '.git/worktrees/wt': Operation not permitted)

## Settled decisions — do not re-raise

> These calls were already made in an earlier cycle of this same review, with
> the reasons given. Do not re-raise them. Raise a NEW finding only if you can
> show the settled reason no longer holds.

- [discarded] low: `_ResolvedModelCodexDriver.build_launch` is identical to `_ResolvedModelClaudeDriver.build_launch` (inverse tier map plus `replace`). A shared module function such as `_tier_key_request(settings, request)` called by both overrides would remove the copy. The design asked for mirroring, so this is low (src/ovcaq/drivers/edge.py:26) - reason: Duplicate of R7: both cite the identical inverse-tier overrides. R7 is fixed; no second task is needed. Raw findings remain preserved.
- [discarded] low: Cannot statically verify: phase-2 exit gate (pytest, ruff check, ruff format --check, mypy, uv build). The test gate reports exit 0 but gives no counts (N/A) - reason: Resolved by current-HEAD verification: 7165 passed, 0 failed, 0 skipped; sync, Ruff lint/format, mypy and build all exit 0. See 00053-review-1-verification.json. Bob VERIFY command uses &&, so not queued: command shape; each required gate already ran separately.
- [settled-deferral] low: The Codex probe runs in the caller's working directory, while the launch runs in request.root. A relative command or an empty-PATH lookup can therefore succeed in the probe and fail at launch, or the reverse (existing behavior) (src/ovcaq/drivers/codex.py) - reason: Known pre-existing caller/request-root cwd disagreement. PRD explicitly excludes probe descendant/ownership redesign and preserves Codex probe behavior. Defer outside this repair; do not change the current scope.
- [discarded] medium: 33 touched test(s) pass against the pre-change code: test_numeric_diagnostics_require_an_explicit_status_or_error_context +27 more (tests/drivers/test_adapter_failure_classes.py) - reason: Existing valid HTTP/word diagnostics, precedence and reset parsing are compatibility controls the PRD explicitly requires retaining. New false-positive negatives and capacity cases fail at base; literal oracle expectations are independently pinned. Passing preservation cases are not tautologies.
- [discarded] medium: 40 touched test(s) pass against the pre-change code: test_unfinished_lane_fails_after_close_status +34 more (tests/drivers/test_adapter_outcomes.py) - reason: New completed-lane regressions fail at base; running/unstarted/unknown preservation cases deliberately cover unchanged behavior. R8 separately fixes actual redundant test padding; it is not silently dismissed by this characterization decision.
- [discarded] medium: 10 touched test(s) pass against the pre-change code: test_native_failure_emits_classified_terminal_with_receipt_identity +4 more (tests/drivers/test_codex_decode_terminals.py) - reason: Existing terminal fixture outcomes remain unchanged; only the independent literal oracle replaces a production-derived expected class. Such an oracle correction is expected to pass base.
- [discarded] medium: 7 touched test(s) pass against the pre-change code: test_failure_classification_uses_documented_precedence +1 more (tests/drivers/test_codex_failures.py) - reason: Existing failure fixtures and reset behavior are compatibility controls; independent literal oracles replace classifier-derived expectations without requiring changed production outcomes.
- [discarded] medium: 81 touched test(s) pass against the pre-change code: test_launch_has_exact_order_and_omits_unconfigured_flags +75 more (tests/drivers/test_codex_launch.py) - reason: Direct tier precedence, explicit-model validation, safe flags and ordinary config remain unchanged by contract; supervised collision regressions fail at base. R13 separately fixes the broad factory exception check.
- [discarded] medium: 14 touched test(s) pass against the pre-change code: test_native_diagnostics_have_independent_failure_classification +8 more (tests/drivers/test_codex_rework_decode.py) - reason: Existing diagnostic fixture is deliberately unchanged, with expected CONNECTIVITY now a literal independent oracle. Passing at base is required characterization.
- [discarded] medium: 21 touched test(s) pass against the pre-change code: test_probe_finds_executable_available_only_on_overlay_path, test_probe_rejects_absolute_command_that_is_not_an_executable_file +15 more (tests/runtime/test_adapter_health.py) - reason: Codex effective PATH already behaved correctly and PRD requires regression rather than forced production edits; inherited/absolute/default health controls preserve behavior. Claude overlay failures fail at base. R3 separately repairs the empty-PATH test discrimination.
- [discarded] medium: 1 touched test(s) pass against the pre-change code: test_configured_supervisor_launches_each_selected_literal_model_and_effort (tests/runtime/test_adapter_launch_routing.py) - reason: This parametrized test includes unchanged non-colliding routes as compatibility controls; colliding Codex route cases fail at base. A passing invocation of the same test function does not negate its failing cases.
- [settled-deferral] medium: The `continue` at codex.py:383 drops every native update for a lane that has already finished. codex-cli 0.162.1 ships a `resume_agent` tool ("Resume a previously closed agent by id so it can receive send_input"; I confirmed the string in the binary). So a lane can legitimately go completed → close → resume → running → errored. With the `continue`, the resumed run's running and errored updates disappear with no trace, and a later interrupt or shutdown of the resumed run becomes raw unknown instead of `lane.failed`. The pre-change code reported these. The TUI already handles a restart, because the last write wins (src/ovcaq/tui/model.py:607). The PRD only requires that close statuses do not fail a completed lane, and the unfinished-only filter at src/ovcaq/drivers/codex.py:372 already does that on its own. Fix: delete lines 383-384. Then flip `test_finished_lane_late_update_retains_only_non_lane_observations` (tests/drivers/test_adapter_outcomes.py:266) so it expects running → `lane.progress` and errored → `lane.failed`, and reword docs/driver-protocol.md:243. Confidence: the tool is confirmed; the exact `agents_states` sequence after a resume is my guess (src/ovcaq/drivers/codex.py:383) - reason: Requirements ambiguity: resume/restart generation semantics are not specified by this PRD. The existing contract deliberately freezes completed/failed identities and pins late updates. A binary tool name does not prove a native status sequence; changing this would undo reviewed stability without a fixture. Preserve for separately specified adapter lifecycle work.
- [discarded] low: The normal Codex sequence (`wait` reports completed, then `close_agent` reports shutdown) emits `raw.unknown` on every close of a completed lane. The tests pin this at tests/drivers/test_adapter_outcomes.py:89. The lane result is right, but routine flows now show recurring normalization gaps. (src/ovcaq/drivers/codex_events.py:233) - reason: Intentional documented raw-evidence rule: unsupported terminal close statuses on finished lanes retain RAW_UNKNOWN while preserving terminal identity. Exact tests and protocol document it. UI gap-noise redesign is outside this PRD; deleting evidence would contradict the reviewed contract.
- [settled-deferral] low: A status prefix followed by an ordinary count still classifies. `status: 401 tests passed` returns `authentication` and `error code: 503 records` returns `connectivity` (confirmed by probe). The negative tests only cover counts with no status word in front. (src/ovcaq/drivers/codex_events.py:301) - reason: Requirements ambiguity: mixed diagnostic-prefix/ordinary-count messages need an explicit precedence contract. Existing scope requires diagnostic status contexts and ordinary count negatives; do not invent a broader prose grammar or silently change precedence. Keep the confirmed counterexamples for later specified work.
- [discarded] low: Suspected, not confirmed: a Codex `turn.failed` reading "Authentication failed" classifies as `unknown` (pinned at tests/drivers/test_adapter_failure_classes.py:129). That means a retry or park instead of the operator-access halt. The Claude classifier treats "authentication" as authentication, so the two adapters disagree. I could not check whether this was already the behavior before this change. (src/ovcaq/drivers/codex_events.py:306) - reason: The old classifier did not match authentication failed; cycle1 deliberately removed that added pattern to retain existing word diagnostics. This is known original behavior, not a lost required diagnostic. Existing authentication fixtures use literal invalid-credentials/unauthorized oracles.
- [discarded] low: Every routine close of a completed lane (wait completed, then close_agent shutdown) now emits raw.unknown. The TUI then marks ordinary multi-agent sessions as having raw evidence. Late running or completed updates for terminal lanes emit nothing, so the two cases behave differently. This is documented and tested as intended, but it adds noise. (src/ovcaq/drivers/codex_events.py:233) - reason: Previously settled and intentionally pinned raw-evidence behavior; no contract change authorized.
- [settled-deferral] low: Probe and launch can disagree on relative lookups. Both probes resolve relative PATH entries and relative command paths against the supervisor's own working directory, but launch runs with `cwd=request.root`. Absolute paths and normal PATH entries are unaffected. (src/ovcaq/drivers/claude.py:82) - reason: Existing out-of-scope relative-path/cwd limitation; probe ownership redesign excluded by PRD. New Claude citation retained.
- [discarded] low: The CHANGELOG entry about reqwest/HTTP-version forms and literal whitespace describes no change from the pre-PRD base. Bare codes already matched those forms there, and whitespace was already literal. The entry records rework done inside this PRD and overlaps the numeric-context entry three lines below (CHANGELOG.md) - reason: Duplicate of R2 changelog finding; one distinct repair request, both raw outputs preserved.
- [settled-deferral] low: The bare word "status" counts as an HTTP context, so ordinary counts after it still get a failure class. Confirmed: "status 401 files processed" and "exit status 401" both return `authentication`. Inside the PRD's wording, but no negative control is pinned for it (src/ovcaq/drivers/codex_events.py:302) - reason: Existing mixed diagnostic-prefix/count precedence limitation; requires later explicit contract.
- [discarded] low: A late update for a lane that already finished is now dropped with no `raw_unknown` record, while a late close status for the same lane does emit one. So a contradictory late "errored" after "completed" leaves no trace in the normalized stream; only raw.jsonl keeps it. `item_lanes(started_lanes=None)` also keeps its optional default: a caller that leaves it out never fails a lane on close (review R1 asked for it to be required) (src/ovcaq/drivers/codex.py:383) - reason: Existing remembered-terminal identity contract; raw session evidence survives. Production decoder supplies unfinished identities; no new required helper signature.

## Context Pack

Pack file: (no pack available this cycle)

### Findings precedent

(no pack available this cycle)

## Test gate

Tests: 7155 passed, 0 failed, 0 skipped (reused from last-verification.json at deb7300)

## Approved repair handoff

Tasks18–20 repaired the five authorized findings. Verify their closures in the whole PRD range. Carry the read-only Pat18 LOW: tests/runtime/test_supervisor_adapters.py:40 workflow_fixture is a noun; action functions should use a verb-led name. No additional implementation is authorized without an operator decision. Prior scope decisions remain settled.
