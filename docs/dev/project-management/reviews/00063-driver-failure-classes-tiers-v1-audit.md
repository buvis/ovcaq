# Decision Audit Log: 00063-driver-failure-classes-tiers-v1

PRD: `00063-driver-failure-classes-tiers-v1.md`
Started: 2026-10-29T00:43:55Z
Completed: 2026-10-29T00:43:55Z
Autonomous: 35  |  Deferred: 3  |  Doubts: 0

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: The PRD asks to migrate every fixture and fake driver in the files marked "fixtures off the old tier keys". Several still use `sonnet`/`opus` tier tables and `PhaseSettings("sonnet"...)`: tests/runtime/test_supervisor_process.py:75, :161, :180; tests/integration/test_observer_terminal_cleanup.py:87, :348; tests/integration/test_supervisor_live_telemetry.py:188, :207. These fixtures still pass because they are self-consistent. Fixtures with the same stale keys outside the PRD's file list are tests/runtime/test_rework_thread_conflict.py:69, tests/integration/test_launcher_outcomes.py:57, tests/integration/test_terminal_lifecycle.py:236 and tests/tui/test_codex_projection.py:165. The ones routing through default phases now ignore the configured `model-s`/`model-o` and use the driver defaults. Migrate the PRD-listed files to `standard`/`deep`, and the others for the same reason.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: No test proves the Supervisor passes the driver's `default_tiers` to `resolve_phase_route`. All four fake drivers carry an empty table; the `route` stand-in in test_supervisor_preflight defaults `default_tiers` to None; `test_unconfigured_project_routes_through_driver_default_tiers` calls `resolve_phase_route` directly, not through `Supervisor`. Deleting `default_tiers=` at both supervisor call sites would leave every test green, yet this is the PRD happy path. Add a Supervisor-level test with a fake whose `default_tiers` is non-empty and a project with no tier table, asserting preflight passes and `_attempt` launches with the mapped model. Separately, the unconfigured-project test at tests/runtime/test_adapter_launch_routing.py:192 bypasses Supervisor and the edge model-to-tier conversion by passing `route.tier` directly to `build_launch`: add an unconfigured Supervisor test for both drivers that captures build/review/done argv and exercises both route-resolution call sites.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: The breaking-change entry is inaccurate. It says a tiers table naming only models "no longer resolves the default routes". In fact the routes resolve silently to the driver's own models (`default_tiers` is merged under the table), so the operator's models are ignored. Task 5 required the note that such a table "now falls through to the driver's own models". Reword the entry to describe the silent fallback, and distinguish the built-in neutral keys from custom keys rather than requiring configured keys for neutral frontmatter floors.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: docs/operations.md is under-documented and self-contradictory on four counts. (1) :82 says a tiers table "must now define standard and deep", then says a table with neither key "silently falls through to the driver's own models instead of failing"; the drivers merge `{**default_tiers, **settings.tiers}`, so no definition is required and the two sentences disagree. (2) Task 5 asked for the PRD frontmatter floor to be stated there as a rule — it applies only when its value is a tier key in the table, written with a neutral placeholder — and the amended sentence at :80-:87 adds no such rule; the existing "unavailable hint warns and applies no floor" is the only coverage. (3) The Risks section asks the same file to document the frontmatter-floor risk (a PRD naming a non-neutral default model warns unless the agent tier table maps it); only docs/driver-protocol.md:37-45 shows an example. (4) The explicitly required reserved literal `default` is not named. Fix all four in the generated documentation source `src/ovcaq/workflow_cli.py` and regenerate operations.md, keeping the driver-protocol reference and the provider-neutrality invariant.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: Test bloat that does not pin this change, in one file. The replay shows 99 new tests in the failure-class file pass against the pre-change code, plus 5 in `test_claude_default_tiers_do_not_bypass_launch_validation`. The PRD requires one table test per driver plus the pinned negatives. The generated carrier-sentence, casing and pairwise-precedence suites exercise old markers such as `unauthorized`, `permission denied`, `timed out` and `agent loop died`. Keep rows that fail at base or that the PRD names as pins; cut the rest (about 300 lines). Separately, `test_codex_diagnostic_table_reaches_every_failure_class` at :384 checks only expected values in its own fixture, never classifier behavior: remove that redundant fixture-only test and retain the parametrized classifier assertions.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R1: The PRD asks to migrate every fixture and fake driver in the files marked "fixtures off the old tier keys". Several still use `sonnet`/`opus` tier tables and `PhaseSettings("sonnet"...)`: tests/runtime/test_supervisor_process.py:75, :161, :

**Choice**: auto-fix (R1 routed into a [D1] rework task)

**Rationale**: cycle 1 decision gate: multi-voice finding, fix is additive or mechanical, so auto-fix applies without escalation

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R2: No test proves the Supervisor passes the driver's `default_tiers` to `resolve_phase_route`. All four fake drivers carry an empty table; the `route` stand-in in test_supervisor_preflight defaults `default_tiers` to None; `test_unconfigured_p

**Choice**: auto-fix (R2 routed into a [D1] rework task)

**Rationale**: cycle 1 decision gate: multi-voice finding, fix is additive or mechanical, so auto-fix applies without escalation

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R3: The breaking-change entry is inaccurate. It says a tiers table naming only models "no longer resolves the default routes". In fact the routes resolve silently to the driver's own models (`default_tiers` is merged under the table), so the op

**Choice**: auto-fix (R3 routed into a [D1] rework task)

**Rationale**: cycle 1 decision gate: multi-voice finding, fix is additive or mechanical, so auto-fix applies without escalation

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R4: docs/operations.md is under-documented and self-contradictory on four counts. (1) :82 says a tiers table "must now define standard and deep", then says a table with neither key "silently falls through to the driver's own models instead of f

**Choice**: auto-fix (R4 routed into a [D1] rework task)

**Rationale**: cycle 1 decision gate: multi-voice finding, fix is additive or mechanical, so auto-fix applies without escalation

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R5: Test bloat that does not pin this change, in one file. The replay shows 99 new tests in the failure-class file pass against the pre-change code, plus 5 in `test_claude_default_tiers_do_not_bypass_launch_validation`. The PRD requires one tab

**Choice**: auto-fix (R5 routed into a [D1] rework task)

**Rationale**: cycle 1 decision gate: multi-voice finding, fix is additive or mechanical, so auto-fix applies without escalation

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R6: Possible scope drift. Task 5 said to touch no source file, but `WORKFLOW_INPUT_NOTES` in src/ovcaq/workflow_cli.py:34 was edited. This is the generated source of the operations.md text, so it is likely justified, but the edit should be call

**Choice**: discard (R6, no task created)

**Rationale**: cycle 1 decision gate: single-voice; and already called out: docs/dev/project-management/meta/assumptions.md records the task-5 operations.md edit site as wrong and the WORKFLOW_INPUT_NOTES move as the deliberate fix (step-7 regression 1)

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R7: The docs sentence "the digit breaks no boundary after `429`" is muddled. The point is that `\b` does not hold between `429` and `0`.

**Choice**: discard (R7, no task created)

**Rationale**: cycle 1 decision gate: single-voice

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R8: Smaller deviations from the contract. The reserved literal is the private `_PROVIDER_DEFAULT_MODEL` rather than the contract's named constant. `build_launch` sets `model = None` instead of using the contract's conditional on the argv segmen

**Choice**: discard (R8, no task created)

**Rationale**: cycle 1 decision gate: single-voice; the reporter states both deviations are behaviour-equivalent

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R9: File sizes are close to the 800-line limit: src/ovcaq/runtime/supervisor.py is 782 lines, tests/runtime/test_supervisor.py 780 and tests/workflow/test_configuration.py 775. All are under the limit.

**Choice**: discard (R9, no task created)

**Rationale**: cycle 1 decision gate: single-voice; and not a defect by its own text - every named file is under the limit

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R10: src/ovcaq/config.py:33 adds an unspecified public constant, `NEUTRAL_TIERS`. It is derived from `DEFAULT_PHASE_TIERS` and used only by `workflow_settings`. It is small and harmless, but the PRD does not list it.

**Choice**: discard (R10, no task created)

**Rationale**: cycle 1 decision gate: single-voice; the design doc's verbatim contract for task 3 names the NEUTRAL_TIERS union in workflow_settings, so it is specified, just not in the PRD body

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R11: 1 touched test passes against the pre-change code: test_installed_explicit_available_tiers_override_the_active_map

**Choice**: discard (R11, no task created)

**Rationale**: cycle 1 decision gate: mech-check replay on a behavior-preserving fixture migration: this test was touched only to move off the old tier keys, so passing against the pre-change code is expected, not unpinned behavior

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R12: 1 touched test passes against the pre-change code: test_supplied_phase_settings_control_each_workflow_launch

**Choice**: discard (R12, no task created)

**Rationale**: cycle 1 decision gate: mech-check replay on a behavior-preserving fixture migration: touched only to move off the old tier keys

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R13: 1 touched test passes against the pre-change code: test_create_session_os_error_before_session_opens_reverts_a_fresh_batch

**Choice**: discard (R13, no task created)

**Rationale**: cycle 1 decision gate: mech-check replay on a formatting-only change: the only edit to this file in range is the ruff-format reflow at 981342e

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R14: 3 touched tests pass against the pre-change code: test_preflight_resolves_routes_for_the_driver_agent, test_preflight_accepts_a_tier_only_the_agent_override_supplies, test_preflight_reports_the_override_tier_not_the_neutral_one

**Choice**: discard (R14, no task created)

**Rationale**: cycle 1 decision gate: mech-check replay on a behavior-preserving stand-in change: the `route` stand-in gained a defaulted `default_tiers` parameter, which by design leaves existing behavior unchanged. R2 is the finding that this seam is under-tested, and it is being fixed.

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R15: 8 touched tests pass against the pre-change code: test_explicit_phase_mapping_rejects_extra_nonroutable_keys, test_explicit_phase_mapping_rejects_untyped_values, test_config_rejects_nonroutable_phase_tables and 5 more

**Choice**: discard (R15, no task created)

**Rationale**: cycle 1 decision gate: mech-check replay on a behavior-preserving fixture migration: these rows assert rejection of malformed phase tables and were touched only to move the arbitrary tier strings off the old keys

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: Carl (gemini/copilot) failed twice with 'You have exceeded your monthly quota' (exit 1, not exit 4)

**Choice**: continued the cycle with Alice, Blake and Bob; no batch unavailability latch written

**Rationale**: Safety Checks graceful-degradation row: a transient reviewer failure must not break an unattended run, and exit 1 is a runtime failure rather than the exit-4 permanent-configuration class that latches for the batch

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: consolidate_findings.py left four pairs of same-defect findings unmerged because each pair named two different file cells, so every one read as single-voice

**Choice**: merged the four pairs in the review file's Consolidated Findings table, renumbered refs in row order, and recorded the merge explicitly in the review file

**Rationale**: the decision gate's documented standard for matching is issue text plus file, and review-close enforces the single-voice discard mechanically off the Consensus cell; leaving the rows split would have discarded four genuinely multi-voice defects on a consolidator artifact

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R3: Claude classification matches by plain substring with no word boundary, so prose mentioning oauth/rate limit/getaddrinfo reroutes (src/ovcaq/drivers/claude_events.py:223)

**Choice**: discarded

**Rationale**: single-voice; the PRD specifies the Claude markers as plain substrings, so substring matching is the shipped contract

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R4: HTTP 4290 classifies as rate_limit, locked in as an accepted asymmetry (tests/drivers/test_adapter_failure_classes.py:482)

**Choice**: discarded

**Rationale**: single-voice; the pinned hold 00056 rule requires http/status context, which HTTP 4290 satisfies, and the asymmetry is recorded deliberately in the test

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R5: docs claim default_tiers is required at DRIVER_API_VERSION 2 but _register_driver never validates it (src/ovcaq/drivers/base.py:129)

**Choice**: discarded

**Rationale**: single-voice; the PRD deliberately does not bump DRIVER_API_VERSION and lists no discovery-validation work, so a registry check is new scope

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R6: fail-silent config path - a model-name-only tiers table resolves through the driver's own models with no runtime warning (src/ovcaq/config.py:657)

**Choice**: discarded

**Rationale**: single-voice; the silent fallback is the PRD's chosen migration behavior, documented by cycle 1's R3/R4 fixes; a runtime warning is new scope

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R9: about 40 retained table rows still pass against the pre-change classifiers (tests/drivers/test_adapter_failure_classes.py:337)

**Choice**: discarded

**Rationale**: single-voice; cycle 1's R5 trim already removed the generated bloat and the reporter states the residue loses no PRD-named pin

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R10: two fixture sites outside the PRD list still use the old sonnet tier key (tests/integration/test_native_telemetry_identity.py:301)

**Choice**: discarded

**Rationale**: single-voice; both files sit outside the PRD's file list and are self-consistent and green - naming consistency only

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R11: the test replaces the harness driver instead of assigning default_tiers on it (tests/runtime/test_adapter_launch_routing.py:249)

**Choice**: discarded

**Rationale**: single-voice; a one-statement style preference in a passing test

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R12: explicit --available-tier flags bypass the neutral union, losing standard/deep (src/ovcaq/config.py:315)

**Choice**: discarded

**Rationale**: single-voice; an explicit tier list overriding the defaults is the documented meaning of the flag, and warn-and-no-floor is already documented behavior

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R13: DEFAULT_PHASE_TIERS is mutable while NEUTRAL_TIERS snapshots it at import time (src/ovcaq/config.py:32)

**Choice**: discarded

**Rationale**: single-voice; nothing in the codebase mutates DEFAULT_PHASE_TIERS, so this guards a caller that does not exist

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R14: NEUTRAL_TIERS is a new public config symbol outside the PRD's declared new-symbol set (src/ovcaq/config.py:33)

**Choice**: discarded

**Rationale**: single-voice; and already settled in cycle 1 as this PRD's ledger entry for R10 - the design doc's task-3 contract names the NEUTRAL_TIERS union

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R15: Codex execution records store the literal default as the model for both tiers (src/ovcaq/drivers/codex.py:118)

**Choice**: discarded

**Rationale**: single-voice; the reserved default literal with the -m segment omitted is the PRD's explicit task-2 contract, and the spec never states the observability requirement

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R16: build_launch accepts a raw explicit model default without allow_explicit_model and omits -m (src/ovcaq/drivers/codex.py:148)

**Choice**: discarded

**Rationale**: single-voice; accepting a legitimate member of the merged tier table is the direct consequence of the PRD's own default_tiers merge

### [autonomous] 2026-10-29T00:43:55Z

**Decision**: R17: the frontmatter-floor mapping example lives only in docs/driver-protocol.md because operations.md forbids model names (docs/operations.md:80)

**Choice**: discarded

**Rationale**: single-voice; a PRD-internal contradiction already resolved in favor of the binding acceptance grep, and cycle 1's R4 kept the driver-protocol pointer

### [deferred] 2026-10-29T00:43:55Z

**Decision**: Reclassifying 429 as rate_limit makes a Claude rate limit halt the run immediately: with no reset banner summary.rate_limit_reset_at is None, so _failure_decision (src/ovcaq/runtime/decision.py:197) returns HALT "No bounded rate-limit retry remains" with zero attempts, where the pre-change agent class got died_retries first. The PRD premise that a 429 should reach the bounded wait is unmet for "HTTP 429 Too Many Requests", and no test covers the end-to-end Claude rate-limit outcome.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-29T00:43:55Z

**Decision**: CHANGELOG.md:51 still ends "A PRD frontmatter tier floor must also name a key the table defines", which is false for the neutral keys: workflow_settings unions NEUTRAL_TIERS into available_tiers, so a standard/deep floor applies with no agent tiers table at all. docs/operations.md:84 states it correctly; make the CHANGELOG match.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-10-29T00:43:55Z

**Decision**: Prior R2 only partially resolved: the new test verifies both Supervisor call sites but drives the fake Driver, so no unconfigured Supervisor run exercises ClaudeDriver/CodexDriver argv, the edge _map_model_to_tier round trip for the neutral keys (including the Codex default collapse), or the done phase. Coverage gap only; behavior is correct by inspection.

**Choice**: deferred to batch end

**Rationale**: rework cap reached with this finding unresolved
