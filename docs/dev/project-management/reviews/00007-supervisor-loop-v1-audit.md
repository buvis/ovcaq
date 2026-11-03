# Decision Audit Log: 00007-supervisor-loop-v1

PRD: `00007-supervisor-loop-v1.md`
Started: 2026-10-03T00:53:20Z
Completed: 2026-10-03T00:53:20Z
Autonomous: 47  |  Deferred: 19  |  Doubts: 0

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Supervisor loop design choice

**Choice**: Use a pure state-plus-SessionSummary decision table, a thin effectful supervisor, pre-spawn canonical session metrics, and explicit durable post-drain capability attempts.

**Rationale**: Preserves the sole-writer/provider-edge invariants while covering all Phase 5 source obligations; unresolved advisory items remain in the design Review log.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: CapabilityService constructor and retry idempotency were unspecified

**Choice**: Construct with root, StateStore, RuntimePaths, run_id, clock, and timeout; process ownership is read from retained SessionMetadata and checked with process_matches. retry is state-guarded: one call creates exactly one attempt; success/live ownership rejects repeats; a later explicit call after a failed attempt intentionally creates a new attempt.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Capability result raw-evidence JSON schema was unspecified

**Choice**: CapabilityService.finish appends one UTF-8 JSON line containing exactly the public CapabilityExecution fields: success, session_id, and detail. Values match the execution object; detail remains null on success and carries the actionable failure string on failure.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: No atomic StateService path existed for failed capability retry

**Choice**: Add StateService.retry_capability(name, attempt, expected_revision=None), accepting only required failed capabilities and atomically appending one fresh running attempt; keep start_capability pending-only.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Supervisor Clock and apply() boolean semantics were unspecified

**Choice**: Supervisor clock provides now(), monotonic(), and wait(event, timeout); sleeper handles decision waits. apply(decision) returns true for continuing actions (continue, retry, wait, park, run/skip capability) and false for terminal pause, complete, or halt. Pause and complete exit 0; halt exits 1; signals exit 128+signal.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Capability failure leaves `batch.status` as running, and a later successful retry does not clear its stale `control.attention`, violating the lifecycle contract and leaving completed state with failure attention

**Recommendation**: PRD 00007 and its mandatory implementation-plan contract; review verification and bounded probe. No dependency, schema migration, or changed public signature is required.

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Extract timeout-observation construction from `_collect`; the new function is 54 lines and exceeds the 50-line limit

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Retry budgets can be dodged forever. `Supervisor._decide` resets `RetryState` whenever the failure class changes, and failure-path RETRY/WAIT decisions never advance `phase_repeats`. Alternating failures (agent death, then connectivity, then agent death...) therefore relaunch sessions without limit. This breaks the PRD's "Retry storms: Bound every wait/retry" mitigation. Confirmed by tracing `decide` and `_decide`

**Recommendation**: PRD 00007 and its mandatory implementation-plan contract; review verification and bounded probe. No dependency, schema migration, or changed public signature is required.

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: No production code ever starts a batch. Nothing in `src/` writes `batch.id` or `batch.status="running"`, and `new_state` leaves `batch.id=""`. So `ovcaq init` followed by `ovcaq run --no-tui` raises at `_open_session` → `publish_session_metric` → `_validate_identifier("")`, and `archive_final_state` also requires the id. The installed drain acceptance test passes only because its SEED script writes the batch fields straight through StateStore

**Recommendation**: PRD 00007 and its mandatory implementation-plan contract; review verification and bounded probe. No dependency, schema migration, or changed public signature is required.

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `StateService.resume` always clears `pause_reason` but leaves `work.phase/next_phase == "paused"`. After a systemic park (records.py:445) or a `review_cap` pause, it erases the reason and the review_cap routing key that `workflow/resume.py:17` reads. Meanwhile `_boundary` still returns PAUSE, so `ovcaq run` exits 0 with 0 sessions and no explanation

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: The batch status lifecycle is incomplete. `apply(COMPLETE)` only archives, so a drain with no *required* capability (non-empty drain, or empty drain with only optional pending capabilities) archives `batch.status` still `running`. A failed capability never sets `batch.status="attention"`, which plan §8.6 step 5 requires

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Capability timeout comes from the workflow phase route (`resolve_phase_route(work.phase or next_phase)`), not from capability config (plan §7 `[capabilities.agoge] timeout_seconds`). Startup `_reconcile_capabilities` resolves a full agent route (it needs agent config and a valid tier, and raises on phase `paused`) only to throw the timeout away

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Reports count capability metric rows as workflow sessions. Canonical rows always carry `phase_launched` (None for capabilities) and `_metric_partitions` selects sessions by key presence. One capability attempt therefore inflates the session count and turns batch cost/token totals to unknown. No test covers it (test_canonical_metrics only has phase rows)

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `_metric_partitions` silently drops any row whose `usage` is not a Mapping, using a `for usage in [...] if isinstance(...)` comprehension trick. That swallows an error and is hard to read

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Extra `reconcile_metrics` calls. `CapabilityService._begin` rebuilds the aggregate right after publishing the pending row, so the aggregate shows the live capability attempt as `interrupted` for its whole run. `Supervisor._run_capability` calls it again after `finish`→`_finalize` already did

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `Supervisor._run_capability` duplicates CapabilityService. It hand-builds `SessionPaths` that `_begin` already returned and `start` threw away, and re-implements `retry`'s run/finish-on-exception flow with a different failure detail (bare `str(error)` vs "runner raised …; retry X explicitly")

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `_ResolvedModelClaudeDriver` inverts the tier map to turn the supervisor's resolved model back into a tier key so `ClaudeDriver` can resolve it again. The round trip is a subclass whose only job is undoing work

**Choice**: cycle 1: discard

**Rationale**: The shim is a current protocol adaptation: supervisor LaunchRequest.model is the concrete resolved model, while the existing adapter accepts configured tier keys. Passing route.tier as suggested contradicts the supervised request contract. The provider-edge conversion has a present architectural purpose; no incorrect mapping or changed behavior was demonstrated.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `DEFAULT_PHASE_TIERS = {"build": "sonnet", "review": "opus", ...}` lives in the provider-neutral `ovcaq.drivers` package init and feeds `config._supervisor_phases`. Neutral routing defaults are therefore Claude tier names: any agent without `sonnet`/`opus` tier keys fails with "Unknown agent tier" (AGENTS.md: model names live under their adapter)

**Choice**: cycle 1: discard

**Rationale**: sonnet/opus here are configured logical tier keys, not provider model identifiers. The accepted design explicitly specifies these defaults, and custom agents can set phase tiers mapped to arbitrary provider model IDs. Unknown-tier rejection is required validation. Moving them into one provider would introduce coupling rather than fix a defect.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Nothing in `src/` reads `SupervisorSettings.phases`. The supervisor routes through `resolve_phase_route(root, …)`, which rebuilds settings from disk (parsing both TOML files twice per call). So the validated `phases=` override and the `**explicit: object` runtime type checks in `supervisor_settings` only matter to tests

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `_boundary` is a second, pre-launch decision table outside decision.py. It imports the private `_capability_decision` and ignores the `control.attention` that `decide` halts on, so a non-drained state with attention launches a session before halting (PRD: every halt is a pure, table-tested decision)

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `test_incomplete_lifecycle_commands_fail_with_json_usage_errors` passes against the pre-change code, because unknown commands also return `usage`. It pins neither `run` requiring `--no-tui` nor `capability retry` requiring NAME (fail-first replay)

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] `test_init_rejects_project_config_path_collisions_before_state_publication` hedges with `config.is_dir() or config.is_symlink()`, so either param passes on either outcome (existing test, in a touched file)

**Choice**: cycle 1: discard

**Rationale**: The reported test body is unchanged from the work base; only a separate command-inventory test changed in this file. This is pre-existing test debt outside this PRD diff. The shape fact is retained, not disputed.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: tests/state/test_cli.py is 812 lines (807 at base); this diff grows a file already over the 800-line cap

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Every lifecycle failure (unknown agent, live capability owner, unavailable runner, unverifiable or failed stop) maps to `runtime_format`. Callers cannot tell "retry later" from a config error

**Choice**: cycle 1: discard

**Rationale**: The existing stable runtime_format envelope is the accepted CLI contract. The PRD requires stable symbolic codes but does not require distinct codes per cause; messages identify each cause. Adding a new public error taxonomy is unrequested API scope.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `skip_empty_drain_capabilities` stamps `completed_at` from `datetime.now(UTC)` instead of the injected clock, unlike `finish_capability` (PRD: injectable time)

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: New `# noqa: PLC0414` suppression markers re-export `SessionEvidenceWriter`/`EvidenceLimitError` from session.py

**Choice**: cycle 1: discard

**Rationale**: Explicit same-name re-exports preserve the established public import boundary after the evidence writer split. PLC0414 suppressions are narrowly documented, and product lint passes. An __all__ rewrite or importing a private module from callers offers no verified simplification and weakens the public seam.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `ProgressSnapshot.phase_fingerprint` is captured and persisted but `decide` never compares it, so repeat counts carry across restarts even when state changed between runs

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Cannot statically verify: the full suite passes at HEAD bbe7d52 (recorded 3501 passed at 18f90e2, before the handoff commit)

**Choice**: cycle 1: routed to verification

**Rationale**: Resolved for this reviewed HEAD by the approved fresh suite: 3501 passed, zero failed/skipped. Also retain Bob's exact project suite command in the verification queue for the mandatory rework verification pass; no separate implementation task.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] 6 params of `test_incompatible_versions_fail_before_factory_construction` pass against the pre-change code

**Choice**: cycle 1: discard

**Rationale**: Six unchanged invalid-version parameters (-1/0/99 across two sources) intentionally preserve rejection behavior. The changed API-v1 parameters fail against base and pin API-v2 rejection. Passing baseline cases are not a missing behavior test.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] `test_empty_metrics_reduce_to_zero_sessions` passes against the pre-change code

**Choice**: cycle 1: discard

**Rationale**: Empty-input metrics behavior is intentionally unchanged. The canonical/mixed-row tests fail against base and pin the new projection. Retaining a baseline empty-input regression is valid coverage.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Extract finalized metric construction/publication from `_conclude`; the new function is 51 lines and exceeds the 50-line limit

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `record_state_failure` has no production caller. Supervisor state read/write failures return HALT without emergency evidence, so the `require_no_emergency_failure` gate never fires for a real failure and the next `ovcaq run` relaunches (plan §8.4)

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `Supervisor.run` reconciles capabilities (a state write) before `require_no_emergency_failure`, so it writes state before checking whether the store was declared broken

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: `ovcaq stop` leaves no durable stopped outcome in state. The SIGTERM path only finalizes summary.json and the metric (`decision="halt"`), but plan §6 and §8.4 require "record the stopped outcome" as a supervisor-authored state outcome

**Choice**: cycle 1: fix

**Rationale**: Verified in current source and within PRD 00007; bounded regression task carries this finding verbatim.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: A bootstrap repeat-stall (no PRD) returns PAUSE with exit 0 and writes no pause intent; the plan (§12.3 step 11) says halt. CI reads it as success, and every rerun burns another session before pausing again (test asserts `(0, PAUSE, 3)`)

**Choice**: cycle 1: retain accepted design pending policy reconciliation

**Rationale**: Conservative existing behavior; this choice blocks none of the seven repairs.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Empty-drain handling changes every required capability to optional before marking it skipped, erasing the pinned `required` contract instead of preserving the specified required-and-skipped state.

**Choice**: cycle 2: discarded

**Rationale**: The accepted design explicitly removes applicability (required=false) before skipping empty-drain capabilities to preserve the existing schema invariant that completed batches have no unsatisfied required entries. Design lines 22-29 and 195-197 document this deliberate choice. No new contract erosion was introduced by rework.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: Cannot statically verify: pytest, ruff and mypy pass at HEAD 3f5a0bd (rework evidence records 3863 passed in 00007-rework-1-evidence/final-pytest.txt)

**Choice**: cycle 2: routed to verification

**Rationale**: The four exact project commands are queued under Bob provenance. No work pass runs on cap-out, so their queue results remain absent. Independent review verification already ran the equivalent suite, root lint/format and mypy checks with retained argv/output: 3863 tests and typing pass; root lint/format retain the pre-existing 41-error/46-file artifact debt. This is not represented as a fresh work-phase queue execution.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] test_init_rejects_project_config_path_collisions_before_state_publication hedges with `or`: either outcome satisfies it

**Choice**: cycle 2: discarded

**Rationale**: Settled discard F19: the assertion is unchanged from the original PRD base. This rework moves a different inventory test out of the file. No new hedge was introduced.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] 15 touched test(s) pass against the pre-change code: test_capability_request_uses_bounded_configuration_without_agent_route, test_explicit_timeout_overrides_project_and_user_values +9 more

**Choice**: cycle 2: discarded

**Rationale**: Preserved default/explicit timeout and pre-existing validation paths are deliberately in the matrix. Configured timeout selection and new invalid inputs supply the failing regression cases. The task-12 report independently records 72 failed/26 passed red and a subsequent 2 failed/100 passed strengthening run. Passing baseline branches do not invalidate the new negative cases.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] 150 touched test(s) pass against the pre-change code: test_empty_drain_skips_but_nonempty_drain_runs_sorted_required_capabilities, test_committed_progress_continues_before_session_failure_without_drain +144 more

**Choice**: cycle 2: discarded

**Rationale**: Most added parameter cases extend the existing productive-state-wins behavior to task/review/PRD/completed-PRD progress. Other edits align fixtures with persisted fingerprints or remove unrelated attention. Those behaviors must remain unchanged; new failure-budget and attention cases are in separate tests that fail at base.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] 13 touched test(s) pass against the pre-change code: test_unchanged_attempts_share_the_persisted_phase_limit +7 more

**Choice**: cycle 2: discarded

**Rationale**: Eleven successful-session cases already used the phase-repeat limit; two no-pending attention cases already halted. The changed unsuccessful-session/retry and stale-fingerprint cases fail at base. Keeping the successful/control branches is intentional regression coverage.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] 2 touched test(s) pass against the pre-change code: test_reconciliation_projects_interrupted_pending_without_rewriting_evidence

**Choice**: cycle 2: discarded

**Rationale**: Startup reconciliation's interrupted projection is intentionally unchanged for both phase and capability rows. Task 12 explicitly preserved this behavior while removing the redundant live-attempt rebuild.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] 2 touched test(s) pass against the pre-change code: test_retry_budget_resets_after_progress_or_a_changed_failure_class

**Choice**: cycle 2: discarded

**Rationale**: Both existing per-class reset tests intentionally retain their behavior; the repeat cap is raised locally to six so the new global backstop does not mask that assertion. Separate alternating-failure tests exercise the new cap.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] 1 touched test(s) pass against the pre-change code: test_run_commits_batch_identity_before_first_metric_and_preserves_work

**Choice**: cycle 2: discarded

**Rationale**: `started=True` asserts an already initialized batch is preserved. The `started=False` case fails at base and pins the missing production initialization.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] 24 touched test(s) pass against the pre-change code: test_committed_controls_block_every_startup_boundary +18 more

**Choice**: cycle 2: discarded

**Rationale**: Three existing pause control types across four boundaries and two sites remain valid. Eight attention cases exercise the missing boundary halt. The enlarged matrix intentionally proves pause behavior is preserved.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] 3 touched test(s) pass against the pre-change code: test_parser_exposes_init_state_and_workflow_command_inventory, test_incomplete_lifecycle_commands_fail_with_json_usage_errors

**Choice**: cycle 2: discarded

**Rationale**: The inventory case was moved unchanged from state tests; the two missing-argument cases strengthen assertions for already implemented command behavior. They fail at the original PRD work base `4e350272`, as retained in `00007-rework-1-evidence/task-15-red-replay.json` and `.txt`; they correctly pass the post-implementation cycle-1 review base.

### [autonomous] 2026-10-03T00:53:20Z

**Decision**: [MECH] 6 touched test(s) pass against the pre-change code: test_successful_retry_completes_batch_and_clears_only_its_attention, test_retry_rejects_stale_revision_without_state_or_backup_writes, test_success_cannot_complete_batch_with_another_unfinished_required_capability

**Choice**: cycle 2: discarded

**Rationale**: Two unrelated-attention cases, one stale-revision case and three unfinished-other-capability cases preserve existing safeguards. The same test matrix fails at base for clearing capability-specific attention and publishing failed batch status.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: `ovcaq run --no-tui` and `ovcaq capability retry agoge` always select an unavailable capability runner, so required capabilities can never succeed through the installed public commands

**Choice**: cycle 1: defer

**Rationale**: Confirmed limitation, owned by PRD 00010. PRD 00007 P05-T06 explicitly requires the lifecycle against a fake; the coverage manifest assigns required real agoge execution and independent retry to 00010, whose provisioned execution proof integrates the real launcher runner. Keep the failure visible; do not introduce launcher-specific execution before that phase.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: A bootstrap repeat-stall (no PRD) returns PAUSE with exit 0 and writes no pause intent; the plan (§12.3 step 11) says halt. CI reads it as success, and every rerun burns another session before pausing again (test asserts `(0, PAUSE, 3)`)

**Choice**: cycle 1: defer

**Rationale**: Requirements conflict: accepted design and task 1 explicitly specify bootstrap repeat PAUSE, while plan section 12.3 says bootstrap halt. The implementation matches the reviewed design. Preserve the existing behavior until the plan/design policy is reconciled; record the zero exit and missing durable intent limitation.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: `ovcaq run` never calls `driver.probe()` (`build_driver` skips discovery and probe), so a missing agent binary shows up as a spawn exception after session evidence already exists

**Choice**: cycle 1: defer

**Rationale**: Driver readiness/provisioning preflight belongs to PRD 00010 P08-T05/P08-T06 and must compose binary/auth/plugin readiness together. Current spawn failure remains explicit and preserves evidence. Retain this requirement for that owning PRD rather than inventing a partial live connectivity preflight in the fake-focused Phase 5.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: A stop signal raised during a capability run is recorded as an ordinary capability failure and then swallowed, producing exit 1 without durable stop intent instead of the required signal exit and immediate-stop behavior.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; Confirmed with a real SIGTERM inside a fake capability runner: exit 1, failed capability, pause_requested=false and pause_reason=null. The broad failed-capability catch swallows SupervisorSignal and may also hide post-commit evidence errors. Expected signal exit 143 and durable operator-stop intent are absent.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: `_loop` now wraps `_attempt` and `apply` in `except _STATE_ERRORS`, and that tuple includes bare `OSError` (supervisor.py:80). So these all become the durable attention "Supervisor state operation failed; inspect state before restarting.": a missing or non-executable agent binary (`Popen` FileNotFoundError/PermissionError, process.py:118), session-evidence I/O, config reads, and PRD file moves in `park`. The real message is dropped, and every later run halts until someone edits state by hand. At base the error propagated with its message. This also breaks the premise of the settled F23 deferral ("spawn failure remains explicit"). Only `run_once` is tested with a launch OSError (test_supervisor.py:443); `run()` is not.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; Confirmed: a synthetic launch OSError returns the generic supervisor state-failure outcome and persists supervisor.loop attention, with phase_repeats=0. The store is healthy. This is new evidence invalidating the explicit-spawn-error premise of settled F23; launcher readiness itself remains assigned to PRD 00010. Recovery should use the existing state CLI, never direct state editing.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: Retry ceilings are held only in `Supervisor._retries`; restarting the supervisor resets rate-limit/connectivity/death budgets, so decisions are not reproducible from committed state plus summary and configured per-class caps can be exceeded.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; Confirmed with two fresh supervisor instances: configured connectivity_retries=1 produces WAIT twice while the durable phase counter reaches 2. The global phase cap bounds total attempts but does not preserve the configured per-class budget across restart. Resolving the persistent policy requires care; no schema or policy is changed at the cap.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: Driver launch/bootstrap exceptions are finalized as HALT evidence and then re-raised before the bounded decision policy can classify, retry, park, or return a normal supervisor outcome.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; The launch-error path finalizes HALT and re-raises without consulting the failure decision table. Nuance: OSError is then caught by the outer state-error handler, rather than escaping run(); other launch exceptions still propagate. This broader bootstrap-routing gap is retained separately from F02, whose new regression is misclassifying non-state I/O and obscuring diagnostics.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: The supplied `SupervisorSettings.capability_timeouts` is never read. The supervisor builds `CapabilityService` without a timeout (supervisor.py:287), and the service re-reads disk through `supervisor_settings(self._root)`. This repeats F16's flaw for the new field. It also re-parses runtime, policy and phase config on every attempt, so an unrelated config error blocks capability runs. Tests pass only because the disk config matches the supplied settings (test_capability_execution_contract.py:82).

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; Confirmed statically: Supervisor._capability_service omits the resolved timeout and CapabilityService._execute reloads supervisor_settings from disk. A follow-up should pass the resolved per-capability value from the supervisor while preserving standalone retry configuration and validation semantics.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: New tests hedge exactly the policy they were added to pin: `kind in {PARK, HALT}` (test_decision_retry_bound.py:60), `kind in {RETRY, WAIT}` (test_decision_retry_bound.py:87), and `kind in {HALT, PAUSE}` (test_supervisor_boundary_policy.py:38). Every parameter makes the exact kind knowable. These are not in the mech-check table.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; Confirmed in the named test bodies. Alice separately raised the shared-limit and bootstrap alternatives; Bob also identified RETRY/WAIT. Assert exact outcomes after the provider-wide shared-limit policy in F12 is resolved; do not blindly hard-code PARK for provider-wide failures.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: `skip_empty_drain_capabilities` keeps a wall-clock fallback when `completed_at=None`. The only production caller passes the injected time (supervisor.py:261), so the fallback is reachable only from tests.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; The optional wall-clock fallback remains in the state service, though the sole production caller now passes injected time and the original production F22 is closed. Retain this LOW cleanup separately; a follow-up must assess the public method signature before making the timestamp mandatory.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: `CapabilityService` checks `timeout_seconds` (typed `object`) in `__init__` and again in every `_execute`. Simpler: validate once in `__init__`, store the result as `int | None`, and have `_execute` read the stored value. Behavior does not change.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; Duplicate validation is present. Simplification must preserve the current distinction between an omitted timeout and explicitly invalid None, which the tests require; an internal int-or-None representation can be used only after boundary validation.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: Any running optional capability blocks terminal completion even though the contract requires only required capabilities to be satisfied.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; The predicate checks every running capability although the design names required capabilities. Current compound start methods refuse optional capabilities, limiting the ordinary reachability; valid externally configured state can still expose the discrepancy. Retain the finding with that limitation.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: `ovcaq stop` validates PID identity and lock ownership before a separate `kill`, leaving a PID-reuse check-then-act window in which an unrelated process can receive SIGTERM.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; The read-identity/lock checks and os.kill are separate operations, so the static PID-reuse window exists. It is unchanged in this incremental diff and needs a supported platform ownership design rather than an extra check falsely promising atomicity. No signal was sent to an unrelated process during review.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: The shared repeat limit parks a PRD for a provider-wide failure. When the limit is hit while the connectivity or rate-limit budget still allows WAIT, `decide` falls through to PARK whenever a PRD is active. Two traced cases with limit 5: conn, conn, conn, rate_limit, rate_limit gives PARK; `connectivity_retries=10` parks on the 5th outage. Running out of the same class budget gives HALT instead (test_decision_terminal_failures.py:65), and plan §12.3 step 11 reserves halt for systemic failures. Two such parks trigger the systemic-park pause. The at-limit kind is not pinned by any test (hedged at test_decision_retry_bound.py:60).

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; Confirmed statically: WAIT at the shared repeat limit falls through to PARK with an active PRD, while exhausted class budgets HALT. This needs explicit provider-wide versus PRD-specific policy and exact regression assertions; it is not resolved by merely replacing the existing test hedge with PARK.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: Same bug as F07, in a sibling path: `request_pause` always overwrites `pause_reason` (with None when there is no `--reason`). So `ovcaq pause` during a review-cap or systemic-park pause erases the routing key that workflow/resume.py:17 reads. `pause --reason X` replaces that key, and `resume` now keeps the replacement for good. `_record_stop` already guards this case (supervisor.py:190).

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; request_pause still overwrites pause_reason unconditionally. The rework preserved a phase-pause reason in resume and operator-stop paths, but the sibling pause command can erase that routing key first. Retain as a bounded recurrence of the notice-preservation problem.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: Harmless revision conflicts now become sticky state failures. `RevisionConflictError` is a `StateError`, so an operator `pause` or `state set` that lands between the supervisor's read and its compare-and-set write (`record_progress`, `skip_empty_drain_capabilities`, `complete_batch`, capability `finish`) writes state-failure attention that blocks restart. The window is small.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; RevisionConflictError derives from StateError and the shown compare-and-set sites route it to sticky state failure. Re-reading committed state should be evaluated as bounded conflict handling, without weakening genuine store-failure barriers.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: When a retry succeeds while another required capability is still pending, `finish_capability` clears this capability's attention but leaves `batch.status="attention"`. The batch then shows attention with no `control.attention` until the other capability finishes.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; After success clears this capability notice, the nonterminal branch does not restore batch.status from attention to running. The remaining required capability prevents premature completion, but the observable batch status is stale.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: A capability failure still overwrites any unrelated `control.attention`, even though the new success path deliberately keeps it. If a stale-owner reconcile or a manual retry fails over, say, a `supervisor.loop` notice, that notice is replaced; a later success then clears it without anyone acknowledging it.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; The failure branch assigns control.attention regardless of an existing unrelated notice; subsequent success clears by capability site. Preserve earlier unacknowledged attention while retaining the capability failure detail in its durable attempt.

### [deferred] 2026-10-03T00:53:20Z

**Decision**: `_capability_timeouts` accepts unknown keys in `[capabilities.NAME]`, while every other config table rejects them (config.py:428, config.py:456). A typo such as `timeout = 600` silently falls back to 10800 seconds.

**Choice**: cycle 2: cap-overflow

**Rationale**: rework cap reached with this finding unresolved; _capability_timeouts uses get(timeout_seconds, 10800) without rejecting unknown table keys. A misspelled timeout silently uses the default; a bounded validation follow-up should allow only documented capability fields.
