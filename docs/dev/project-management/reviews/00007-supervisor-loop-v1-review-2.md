---
prd: docs/dev/project-management/prds/wip/00007-supervisor-loop-v1.md
review: 2
date: 2026-10-03
head_sha: 3f5a0bdd3e3268eb08bbef2240beb3f6733eda59
reviewers: alice,blake,bob
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/reviews/00007-review-2-bob.txt.receipt.json
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: disabled
---

# Review: 00007-supervisor-loop-v1

Diff range: `bbe7d521321428b670d15c4ede00e31792a61e1c..3f5a0bdd3e3268eb08bbef2240beb3f6733eda59`

codex_rung_guard: fired (10 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude

Host substitution: isolated native Codex Alice and Blake ran on gpt-5.6-sol (logical sonnet, high effort), without parent context. Fresh external Claude Bob ran on claude-opus-5-5 (logical opus), carrying the full Bob persona, consensus rubric, D1-D5 doubt and de-slop appendices. The requested R1-R5 doubt intent is retained under the source D1-D5 identifiers. No Eve/Fable dispatch occurred or is claimed; the source guard suffix records the explicitly authorized non-Codex doubt substitution, not a failed Eve attempt. Provider independence comes from Claude Bob; Alice and Blake share an actual model. No codex_thread_id is emitted for Claude.

Carl: automatic approval review denied the optional Gemini dispatch before launch because it would export repository context/code to that destination. The denial is preserved in `00007-review-2-carl-denial.md`; no workaround, retry, model-unavailability latch or fabricated output is used. All three required reviewers and the Watcher have completed; all external processes were awaited. Engram pack: unavailable because this repository is not registered with gita; prompts retain the optional-pack sentinel.

## Decision

**Cap-out with deferrals, not a clean review.** Four HIGH, six actionable MEDIUM and six actionable LOW findings remain. Cycle 2 equals the committed cap 2, and this is unattended mode. Per the review gate's non-CRITICAL cap-out branch, all 16 unresolved findings are appended to `state.deferred_decisions` as `cap-overflow`; no repair task is created, no cap is raised, and no production code is changed. The canonical `converged` transition hands off to finalize with these deferrals. Existing capability-runner/provisioning and bootstrap-policy deferrals remain intact.

There are no CRITICAL findings. F09 and all ten computed mechanical findings are discarded with explicit evidence. F18 is routed to the verification queue; no work pass runs on this cap-out, so queue entries intentionally have no result. Independently executed review checks are described below. The previous cycle's queued suite passed and contributes no carry-forward failure.

## Consolidated findings

| ID | Consensus | Severity | Issue | File | Found by |
|---|---|---|---|---|---|
| F01 | [2/3] | 🟠 | A stop signal raised during a capability run is recorded as an ordinary capability failure and then swallowed, producing exit 1 without durable stop intent instead of the required signal exit and immediate-stop behavior. | src/ovcaq/runtime/supervisor.py:309 | BLAKE, BOB |
| F02 | [1/3] | 🟠 | `_loop` now wraps `_attempt` and `apply` in `except _STATE_ERRORS`, and that tuple includes bare `OSError` (supervisor.py:80). So these all become the durable attention "Supervisor state operation failed; inspect state before restarting.": a missing or non-executable agent binary (`Popen` FileNotFoundError/PermissionError, process.py:118), session-evidence I/O, config reads, and PRD file moves in `park`. The real message is dropped, and every later run halts until someone edits state by hand. At base the error propagated with its message. This also breaks the premise of the settled F23 deferral ("spawn failure remains explicit"). Only `run_once` is tested with a launch OSError (test_supervisor.py:443); `run()` is not. | src/ovcaq/runtime/supervisor.py:240 | BOB |
| F03 | [1/3] | 🟠 | Retry ceilings are held only in `Supervisor._retries`; restarting the supervisor resets rate-limit/connectivity/death budgets, so decisions are not reproducible from committed state plus summary and configured per-class caps can be exceeded. | src/ovcaq/runtime/supervisor.py:123 | BLAKE |
| F04 | [1/3] | 🟠 | Driver launch/bootstrap exceptions are finalized as HALT evidence and then re-raised before the bounded decision policy can classify, retry, park, or return a normal supervisor outcome. | src/ovcaq/runtime/supervisor.py:358 | BLAKE |
| F05 | [2/3] | 🟡 | The supplied `SupervisorSettings.capability_timeouts` is never read. The supervisor builds `CapabilityService` without a timeout (supervisor.py:287), and the service re-reads disk through `supervisor_settings(self._root)`. This repeats F16's flaw for the new field. It also re-parses runtime, policy and phase config on every attempt, so an unrelated config error blocks capability runs. Tests pass only because the disk config matches the supplied settings (test_capability_execution_contract.py:82). | src/ovcaq/runtime/capability.py:335 | ALICE, BOB |
| F06 | [2/3] | 🟡 | New tests hedge exactly the policy they were added to pin: `kind in {PARK, HALT}` (test_decision_retry_bound.py:60), `kind in {RETRY, WAIT}` (test_decision_retry_bound.py:87), and `kind in {HALT, PAUSE}` (test_supervisor_boundary_policy.py:38). Every parameter makes the exact kind knowable. These are not in the mech-check table. | tests/runtime/test_decision_retry_bound.py:60 | ALICE, BOB |
| F07 | [2/3] | ⚪ | `skip_empty_drain_capabilities` keeps a wall-clock fallback when `completed_at=None`. The only production caller passes the injected time (supervisor.py:261), so the fallback is reachable only from tests. | src/ovcaq/state/commands.py:635 | ALICE, BOB |
| F08 | [2/3] | ⚪ | `CapabilityService` checks `timeout_seconds` (typed `object`) in `__init__` and again in every `_execute`. Simpler: validate once in `__init__`, store the result as `int \| None`, and have `_execute` read the stored value. Behavior does not change. | src/ovcaq/runtime/capability.py:337 | ALICE, BOB |
| F09 | [1/3] | 🟡 | Empty-drain handling changes every required capability to optional before marking it skipped, erasing the pinned `required` contract instead of preserving the specified required-and-skipped state. | src/ovcaq/state/commands.py:646 | BLAKE |
| F10 | [1/3] | 🟡 | Any running optional capability blocks terminal completion even though the contract requires only required capabilities to be satisfied. | src/ovcaq/runtime/decision.py:183 | BLAKE |
| F11 | [1/3] | 🟡 | `ovcaq stop` validates PID identity and lock ownership before a separate `kill`, leaving a PID-reuse check-then-act window in which an unrelated process can receive SIGTERM. | src/ovcaq/supervisor_cli.py:105 | BLAKE |
| F12 | [1/3] | 🟡 | The shared repeat limit parks a PRD for a provider-wide failure. When the limit is hit while the connectivity or rate-limit budget still allows WAIT, `decide` falls through to PARK whenever a PRD is active. Two traced cases with limit 5: conn, conn, conn, rate_limit, rate_limit gives PARK; `connectivity_retries=10` parks on the 5th outage. Running out of the same class budget gives HALT instead (test_decision_terminal_failures.py:65), and plan §12.3 step 11 reserves halt for systemic failures. Two such parks trigger the systemic-park pause. The at-limit kind is not pinned by any test (hedged at test_decision_retry_bound.py:60). | src/ovcaq/runtime/decision.py:283 | BOB |
| F13 | [1/3] | 🟡 | Same bug as F07, in a sibling path: `request_pause` always overwrites `pause_reason` (with None when there is no `--reason`). So `ovcaq pause` during a review-cap or systemic-park pause erases the routing key that workflow/resume.py:17 reads. `pause --reason X` replaces that key, and `resume` now keeps the replacement for good. `_record_stop` already guards this case (supervisor.py:190). | src/ovcaq/state/commands.py:454 | BOB |
| F14 | [1/3] | ⚪ | Harmless revision conflicts now become sticky state failures. `RevisionConflictError` is a `StateError`, so an operator `pause` or `state set` that lands between the supervisor's read and its compare-and-set write (`record_progress`, `skip_empty_drain_capabilities`, `complete_batch`, capability `finish`) writes state-failure attention that blocks restart. The window is small. | src/ovcaq/runtime/supervisor.py:609 | BOB |
| F15 | [1/3] | ⚪ | When a retry succeeds while another required capability is still pending, `finish_capability` clears this capability's attention but leaves `batch.status="attention"`. The batch then shows attention with no `control.attention` until the other capability finishes. | src/ovcaq/state/commands.py:604 | BOB |
| F16 | [1/3] | ⚪ | A capability failure still overwrites any unrelated `control.attention`, even though the new success path deliberately keeps it. If a stale-owner reconcile or a manual retry fails over, say, a `supervisor.loop` notice, that notice is replaced; a later success then clears it without anyone acknowledging it. | src/ovcaq/state/commands.py:599 | BOB |
| F17 | [1/3] | ⚪ | `_capability_timeouts` accepts unknown keys in `[capabilities.NAME]`, while every other config table rejects them (config.py:428, config.py:456). A typo such as `timeout = 600` silently falls back to 10800 seconds. | src/ovcaq/config.py:413 | BOB |
| F18 | [1/3] | ⚪ | Cannot statically verify: pytest, ruff and mypy pass at HEAD 3f5a0bd (rework evidence records 3863 passed in 00007-rework-1-evidence/final-pytest.txt) | N/A | BOB |
| F19 | [1/3] | 🟡 | [MECH] test_init_rejects_project_config_path_collisions_before_state_publication hedges with `or`: either outcome satisfies it | tests/state/test_cli.py:358 | mech-check |
| F20 | [1/3] | 🟡 | [MECH] 15 touched test(s) pass against the pre-change code: test_capability_request_uses_bounded_configuration_without_agent_route, test_explicit_timeout_overrides_project_and_user_values +9 more | tests/runtime/test_capability_execution_contract.py | mech-check |
| F21 | [1/3] | 🟡 | [MECH] 150 touched test(s) pass against the pre-change code: test_empty_drain_skips_but_nonempty_drain_runs_sorted_required_capabilities, test_committed_progress_continues_before_session_failure_without_drain +144 more | tests/runtime/test_decision.py | mech-check |
| F22 | [1/3] | 🟡 | [MECH] 13 touched test(s) pass against the pre-change code: test_unchanged_attempts_share_the_persisted_phase_limit +7 more | tests/runtime/test_decision_retry_bound.py | mech-check |
| F23 | [1/3] | 🟡 | [MECH] 2 touched test(s) pass against the pre-change code: test_reconciliation_projects_interrupted_pending_without_rewriting_evidence | tests/runtime/test_session_metrics.py | mech-check |
| F24 | [1/3] | 🟡 | [MECH] 2 touched test(s) pass against the pre-change code: test_retry_budget_resets_after_progress_or_a_changed_failure_class | tests/runtime/test_supervisor.py | mech-check |
| F25 | [1/3] | 🟡 | [MECH] 1 touched test(s) pass against the pre-change code: test_run_commits_batch_identity_before_first_metric_and_preserves_work | tests/runtime/test_supervisor_batch_lifecycle.py | mech-check |
| F26 | [1/3] | 🟡 | [MECH] 24 touched test(s) pass against the pre-change code: test_committed_controls_block_every_startup_boundary +18 more | tests/runtime/test_supervisor_boundary_policy.py | mech-check |
| F27 | [1/3] | 🟡 | [MECH] 3 touched test(s) pass against the pre-change code: test_parser_exposes_init_state_and_workflow_command_inventory, test_incomplete_lifecycle_commands_fail_with_json_usage_errors | tests/runtime/test_supervisor_cli.py | mech-check |
| F28 | [1/3] | 🟡 | [MECH] 6 touched test(s) pass against the pre-change code: test_successful_retry_completes_batch_and_clears_only_its_attention, test_retry_rejects_stale_revision_without_state_or_backup_writes, test_success_cannot_complete_batch_with_another_unfinished_required_capability | tests/state/test_supervisor_commands.py | mech-check |

### Consolidation corrections

The installed consolidator ran first; its unmodified output is `00007-review-2-consolidation-raw.md`. Semantic duplicate grouping then merges Alice's two hedged-assertion findings with Bob's broader test finding (F06), Alice's combined configuration finding with Bob's resolved-settings and duplicate-validation findings separately (F05/F08), and the two wall-clock fallback reports (F07). Every original issue and rubric line remains verbatim in the reviewer sections. The launch-routing finding F04 stays separate from the diagnostic/state-failure regression F02; the probe qualifies F04's exception propagation claim. All ten `[MECH]` lines were absorbed; none was silently dropped.

### Auto-dismissed (ledger)

- [BLAKE] 🟠 Both public capability entry points install an unconditional `_UnavailableRunner`; consequently `ovcaq run --no-tui` can never complete a non-empty batch with a required capability, and `ovcaq capability retry agoge` can never succeed. | File: src/ovcaq/supervisor_cli.py:65 — Confirmed limitation, owned by PRD 00010. PRD 00007 P05-T06 explicitly requires the lifecycle against a fake; the coverage manifest assigns required real agoge execution and independent retry to 00010, whose provisioned execution proof integrates the real launcher runner. Keep the failure visible; do not introduce launcher-specific execution before that phase.

## Adjudication

- **F01 cap-overflow:** Confirmed with a real SIGTERM inside a fake capability runner: exit 1, failed capability, pause_requested=false and pause_reason=null. The broad failed-capability catch swallows SupervisorSignal and may also hide post-commit evidence errors. Expected signal exit 143 and durable operator-stop intent are absent.
- **F02 cap-overflow:** Confirmed: a synthetic launch OSError returns the generic supervisor state-failure outcome and persists supervisor.loop attention, with phase_repeats=0. The store is healthy. This is new evidence invalidating the explicit-spawn-error premise of settled F23; launcher readiness itself remains assigned to PRD 00010. Recovery should use the existing state CLI, never direct state editing.
- **F03 cap-overflow:** Confirmed with two fresh supervisor instances: configured connectivity_retries=1 produces WAIT twice while the durable phase counter reaches 2. The global phase cap bounds total attempts but does not preserve the configured per-class budget across restart. Resolving the persistent policy requires care; no schema or policy is changed at the cap.
- **F04 cap-overflow:** The launch-error path finalizes HALT and re-raises without consulting the failure decision table. Nuance: OSError is then caught by the outer state-error handler, rather than escaping run(); other launch exceptions still propagate. This broader bootstrap-routing gap is retained separately from F02, whose new regression is misclassifying non-state I/O and obscuring diagnostics.
- **F05 cap-overflow:** Confirmed statically: Supervisor._capability_service omits the resolved timeout and CapabilityService._execute reloads supervisor_settings from disk. A follow-up should pass the resolved per-capability value from the supervisor while preserving standalone retry configuration and validation semantics.
- **F06 cap-overflow:** Confirmed in the named test bodies. Alice separately raised the shared-limit and bootstrap alternatives; Bob also identified RETRY/WAIT. Assert exact outcomes after the provider-wide shared-limit policy in F12 is resolved; do not blindly hard-code PARK for provider-wide failures.
- **F07 cap-overflow:** The optional wall-clock fallback remains in the state service, though the sole production caller now passes injected time and the original production F22 is closed. Retain this LOW cleanup separately; a follow-up must assess the public method signature before making the timestamp mandatory.
- **F08 cap-overflow:** Duplicate validation is present. Simplification must preserve the current distinction between an omitted timeout and explicitly invalid None, which the tests require; an internal int-or-None representation can be used only after boundary validation.
- **F09 discarded:** The accepted design explicitly removes applicability (required=false) before skipping empty-drain capabilities to preserve the existing schema invariant that completed batches have no unsatisfied required entries. Design lines 22-29 and 195-197 document this deliberate choice. No new contract erosion was introduced by rework.
- **F10 cap-overflow:** The predicate checks every running capability although the design names required capabilities. Current compound start methods refuse optional capabilities, limiting the ordinary reachability; valid externally configured state can still expose the discrepancy. Retain the finding with that limitation.
- **F11 cap-overflow:** The read-identity/lock checks and os.kill are separate operations, so the static PID-reuse window exists. It is unchanged in this incremental diff and needs a supported platform ownership design rather than an extra check falsely promising atomicity. No signal was sent to an unrelated process during review.
- **F12 cap-overflow:** Confirmed statically: WAIT at the shared repeat limit falls through to PARK with an active PRD, while exhausted class budgets HALT. This needs explicit provider-wide versus PRD-specific policy and exact regression assertions; it is not resolved by merely replacing the existing test hedge with PARK.
- **F13 cap-overflow:** request_pause still overwrites pause_reason unconditionally. The rework preserved a phase-pause reason in resume and operator-stop paths, but the sibling pause command can erase that routing key first. Retain as a bounded recurrence of the notice-preservation problem.
- **F14 cap-overflow:** RevisionConflictError derives from StateError and the shown compare-and-set sites route it to sticky state failure. Re-reading committed state should be evaluated as bounded conflict handling, without weakening genuine store-failure barriers.
- **F15 cap-overflow:** After success clears this capability notice, the nonterminal branch does not restore batch.status from attention to running. The remaining required capability prevents premature completion, but the observable batch status is stale.
- **F16 cap-overflow:** The failure branch assigns control.attention regardless of an existing unrelated notice; subsequent success clears by capability site. Preserve earlier unacknowledged attention while retaining the capability failure detail in its durable attempt.
- **F17 cap-overflow:** _capability_timeouts uses get(timeout_seconds, 10800) without rejecting unknown table keys. A misspelled timeout silently uses the default; a bounded validation follow-up should allow only documented capability fields.
- **F18 routed to verification:** The four exact project commands are queued under Bob provenance. No work pass runs on cap-out, so their queue results remain absent. Independent review verification already ran the equivalent suite, root lint/format and mypy checks with retained argv/output: 3863 tests and typing pass; root lint/format retain the pre-existing 41-error/46-file artifact debt. This is not represented as a fresh work-phase queue execution.
- **F19 discarded:** Settled discard F19: the assertion is unchanged from the original PRD base. This rework moves a different inventory test out of the file. No new hedge was introduced.
- **F20 discarded:** Preserved default/explicit timeout and pre-existing validation paths are deliberately in the matrix. Configured timeout selection and new invalid inputs supply the failing regression cases. The task-12 report independently records 72 failed/26 passed red and a subsequent 2 failed/100 passed strengthening run. Passing baseline branches do not invalidate the new negative cases.
- **F21 discarded:** Most added parameter cases extend the existing productive-state-wins behavior to task/review/PRD/completed-PRD progress. Other edits align fixtures with persisted fingerprints or remove unrelated attention. Those behaviors must remain unchanged; new failure-budget and attention cases are in separate tests that fail at base.
- **F22 discarded:** Eleven successful-session cases already used the phase-repeat limit; two no-pending attention cases already halted. The changed unsuccessful-session/retry and stale-fingerprint cases fail at base. Keeping the successful/control branches is intentional regression coverage.
- **F23 discarded:** Startup reconciliation's interrupted projection is intentionally unchanged for both phase and capability rows. Task 12 explicitly preserved this behavior while removing the redundant live-attempt rebuild.
- **F24 discarded:** Both existing per-class reset tests intentionally retain their behavior; the repeat cap is raised locally to six so the new global backstop does not mask that assertion. Separate alternating-failure tests exercise the new cap.
- **F25 discarded:** `started=True` asserts an already initialized batch is preserved. The `started=False` case fails at base and pins the missing production initialization.
- **F26 discarded:** Three existing pause control types across four boundaries and two sites remain valid. Eight attention cases exercise the missing boundary halt. The enlarged matrix intentionally proves pause behavior is preserved.
- **F27 discarded:** The inventory case was moved unchanged from state tests; the two missing-argument cases strengthen assertions for already implemented command behavior. They fail at the original PRD work base `4e350272`, as retained in `00007-rework-1-evidence/task-15-red-replay.json` and `.txt`; they correctly pass the post-implementation cycle-1 review base.
- **F28 discarded:** Two unrelated-attention cases, one stale-revision case and three unfinished-other-capability cases preserve existing safeguards. The same test matrix fails at base for clearing capability-specific attention and publishing failed batch status.

## Verification


Reviewed HEAD: `3f5a0bdd3e3268eb08bbef2240beb3f6733eda59`.

- Fresh full suite: **3863 passed, 0 failed, 0 skipped**, 76.22 seconds. Two pytest temporary-directory cleanup warnings; no test failures.
- Dependency sync passed.
- `ruff check src tests`, `ruff format --check src tests`, and `mypy src/ovcaq` passed (172 formatted files; 58 typed source files).
- Wheel and sdist build passed.
- Repository-wide Ruff checks reproduce the prior 41 lint errors and 46 files requiring formatting in historical planning/review artifacts. Those artifacts are outside this change and remain untouched.
- Fail-first replay at `bbe7d521321428b670d15c4ede00e31792a61e1c`, with `PYTHONPATH=src` binding imports to the temporary worktree: 408 touched cases ran, 192 failed against base, 216 passed, zero collection-error files. All mechanical findings remain review inputs; passing preserved-behavior cases require adjudication.

Exact argv, exit codes and raw output are retained in the neighboring `00007-review-2-*.json` and `00007-review-2-*.log` files. The suite and replay used approved process permissions. The prior last-verification record was not reused because its SHA differed.

Schema validation passed and derived task totals agree at 15/15. The source rubrics were independently checked in raw outputs: Alice R1-R4/R6-R13; Blake B1-B19; Bob R1-R4/R6-R13 and D1-D5. Both receipt SHA-256 values match the immutable output and raw JSONL. The replay helper removed its temporary worktree; only the main checkout remains. Pre-existing AGENTS.md changes and historical untracked artifacts are preserved. No next gate is invoked in this session.

## Reproduction evidence

```json
{
  "capability_stop": {
    "exit": 1,
    "decision": "halt",
    "pause_requested": false,
    "pause_reason": null,
    "capability_status": "failed",
    "attention": {
      "created_at": "2026-10-02T12:00:00Z",
      "detail": "capability 'audit' failed: runner raised SupervisorSignal: Supervisor received signal 15; retry audit explicitly",
      "site": "capability:audit"
    }
  },
  "restart_retry_budget": {
    "configured_connectivity_retries": 1,
    "phase_repeat_limit": 6,
    "decisions": [
      "wait",
      "wait"
    ],
    "persisted_phase_repeats": 2
  },
  "launch_exception": {
    "exit": 1,
    "reason": "Supervisor state operation failed; inspect state before restarting.",
    "metrics": [
      "halt"
    ],
    "attention": {
      "created_at": "2026-10-02T12:00:00Z",
      "detail": "Supervisor state operation failed; inspect state before restarting.",
      "site": "supervisor.loop"
    },
    "phase_repeats": 0
  }
}
```

## Alice

[ALICE] 🟡 Shared-limit regression accepts either PARK or HALT, although every case has an active PRD and remaining class budget; assert PARK exactly. | File: tests/runtime/test_decision_retry_bound.py:60 | Task: 10
[ALICE] 🟡 Alternating bootstrap-failure regression accepts either HALT or PAUSE, although both sequences must halt; assert HALT exactly. | File: tests/runtime/test_supervisor_boundary_policy.py:39 | Task: 10
[ALICE] 🟡 Capability execution reparses all supervisor configuration despite an already-resolved `capability_timeouts` map and validates explicit timeouts twice; pass the resolved timeout into the service and replace the object sentinel with `int | None`. | File: src/ovcaq/runtime/capability.py:334 | Task: 12
[ALICE] ⚪ F22 remains partially reproducible: omitting `completed_at` still uses wall-clock time, and the state-service test exercises that uninjected path. Make the timestamp required. | File: src/ovcaq/state/commands.py:632 | Task: 9
Closure assessment: F01, F03-F05, F07-F13, F16-F18, F20, F25-F26, and F29-F32 are resolved. F22 is partial as reported above. F02, F06, and F23 remain settled deferrals. F14, F15, F19, F21, F24, F27, and F28 remain correctly discarded. Coordinator verification reports 3863 passed, 0 failed, 0 skipped at reviewed HEAD.
R1: fail
R2: fail
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

[BLAKE] 🟠 Retry ceilings are held only in `Supervisor._retries`; restarting the supervisor resets rate-limit/connectivity/death budgets, so decisions are not reproducible from committed state plus summary and configured per-class caps can be exceeded. | File: src/ovcaq/runtime/supervisor.py:123 | Task: P05-T01
[BLAKE] 🟠 A stop signal raised during a capability run is recorded as an ordinary capability failure and then swallowed, producing exit 1 without durable stop intent instead of the required signal exit and immediate-stop behavior. | File: src/ovcaq/runtime/supervisor.py:309 | Task: P05-T05
[BLAKE] 🟠 Both public capability entry points install an unconditional `_UnavailableRunner`; consequently `ovcaq run --no-tui` can never complete a non-empty batch with a required capability, and `ovcaq capability retry agoge` can never succeed. | File: src/ovcaq/supervisor_cli.py:65 | Task: P05-T06
[BLAKE] 🟠 Driver launch/bootstrap exceptions are finalized as HALT evidence and then re-raised before the bounded decision policy can classify, retry, park, or return a normal supervisor outcome. | File: src/ovcaq/runtime/supervisor.py:358 | Task: P05-T04
[BLAKE] 🟡 Empty-drain handling changes every required capability to optional before marking it skipped, erasing the pinned `required` contract instead of preserving the specified required-and-skipped state. | File: src/ovcaq/state/commands.py:646 | Task: P05-T06
[BLAKE] 🟡 Any running optional capability blocks terminal completion even though the contract requires only required capabilities to be satisfied. | File: src/ovcaq/runtime/decision.py:183 | Task: P05-T06
[BLAKE] 🟡 `ovcaq stop` validates PID identity and lock ownership before a separate `kill`, leaving a PID-reuse check-then-act window in which an unrelated process can receive SIGTERM. | File: src/ovcaq/supervisor_cli.py:105 | Task: P05-T05
B1: fail
B2: fail
B3: fail
B4: fail
B5: fail
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: fail
B12: fail
B13: pass
B14: pass
B15: fail
B16: fail
B17: fail
B18: pass
B19: pass


## Bob

[BOB] 🟠 New regression: `_run_capability` swallows every exception once the capability's status is `failed`, and that includes `SupervisorSignal` (an `Exception` subclass, process.py:33). If SIGTERM, SIGINT or `ovcaq stop` lands during a capability run, `_execute` (capability.py:351) records "runner raised SupervisorSignal" and re-raises; `_run_capability` then drops it, the loop halts on attention, and `run()` returns exit 1 instead of 128+N with no `operator_stop` pause. The base code re-raised. The same catch also hides finalize/evidence errors that occur after a failed attempt is committed. No test sends a signal during a capability run. | File: src/ovcaq/runtime/supervisor.py:309 | Task: 12
[BOB] 🟠 `_loop` now wraps `_attempt` and `apply` in `except _STATE_ERRORS`, and that tuple includes bare `OSError` (supervisor.py:80). So these all become the durable attention "Supervisor state operation failed; inspect state before restarting.": a missing or non-executable agent binary (`Popen` FileNotFoundError/PermissionError, process.py:118), session-evidence I/O, config reads, and PRD file moves in `park`. The real message is dropped, and every later run halts until someone edits state by hand. At base the error propagated with its message. This also breaks the premise of the settled F23 deferral ("spawn failure remains explicit"). Only `run_once` is tested with a launch OSError (test_supervisor.py:443); `run()` is not. | File: src/ovcaq/runtime/supervisor.py:240 | Task: 11
[BOB] 🟡 The shared repeat limit parks a PRD for a provider-wide failure. When the limit is hit while the connectivity or rate-limit budget still allows WAIT, `decide` falls through to PARK whenever a PRD is active. Two traced cases with limit 5: conn, conn, conn, rate_limit, rate_limit gives PARK; `connectivity_retries=10` parks on the 5th outage. Running out of the same class budget gives HALT instead (test_decision_terminal_failures.py:65), and plan §12.3 step 11 reserves halt for systemic failures. Two such parks trigger the systemic-park pause. The at-limit kind is not pinned by any test (hedged at test_decision_retry_bound.py:60). | File: src/ovcaq/runtime/decision.py:283 | Task: 10
[BOB] 🟡 The supplied `SupervisorSettings.capability_timeouts` is never read. The supervisor builds `CapabilityService` without a timeout (supervisor.py:287), and the service re-reads disk through `supervisor_settings(self._root)`. This repeats F16's flaw for the new field. It also re-parses runtime, policy and phase config on every attempt, so an unrelated config error blocks capability runs. Tests pass only because the disk config matches the supplied settings (test_capability_execution_contract.py:82). | File: src/ovcaq/runtime/capability.py:335 | Task: 12
[BOB] 🟡 Same bug as F07, in a sibling path: `request_pause` always overwrites `pause_reason` (with None when there is no `--reason`). So `ovcaq pause` during a review-cap or systemic-park pause erases the routing key that workflow/resume.py:17 reads. `pause --reason X` replaces that key, and `resume` now keeps the replacement for good. `_record_stop` already guards this case (supervisor.py:190). | File: src/ovcaq/state/commands.py:454 | Task: 10
[BOB] 🟡 New tests hedge exactly the policy they were added to pin: `kind in {PARK, HALT}` (test_decision_retry_bound.py:60), `kind in {RETRY, WAIT}` (test_decision_retry_bound.py:87), and `kind in {HALT, PAUSE}` (test_supervisor_boundary_policy.py:38). Every parameter makes the exact kind knowable. These are not in the mech-check table. | File: tests/runtime/test_decision_retry_bound.py:60 | Task: 10
[BOB] ⚪ Harmless revision conflicts now become sticky state failures. `RevisionConflictError` is a `StateError`, so an operator `pause` or `state set` that lands between the supervisor's read and its compare-and-set write (`record_progress`, `skip_empty_drain_capabilities`, `complete_batch`, capability `finish`) writes state-failure attention that blocks restart. The window is small. | File: src/ovcaq/runtime/supervisor.py:609 | Task: 11
[BOB] ⚪ When a retry succeeds while another required capability is still pending, `finish_capability` clears this capability's attention but leaves `batch.status="attention"`. The batch then shows attention with no `control.attention` until the other capability finishes. | File: src/ovcaq/state/commands.py:604 | Task: 9
[BOB] ⚪ A capability failure still overwrites any unrelated `control.attention`, even though the new success path deliberately keeps it. If a stale-owner reconcile or a manual retry fails over, say, a `supervisor.loop` notice, that notice is replaced; a later success then clears it without anyone acknowledging it. | File: src/ovcaq/state/commands.py:599 | Task: 9
[BOB] ⚪ `_capability_timeouts` accepts unknown keys in `[capabilities.NAME]`, while every other config table rejects them (config.py:428, config.py:456). A typo such as `timeout = 600` silently falls back to 10800 seconds. | File: src/ovcaq/config.py:413 | Task: 12
[BOB] ⚪ `skip_empty_drain_capabilities` keeps a wall-clock fallback when `completed_at=None`. The only production caller passes the injected time (supervisor.py:261), so the fallback is reachable only from tests. | File: src/ovcaq/state/commands.py:635 | Task: 9
[BOB] ⚪ `CapabilityService` checks `timeout_seconds` (typed `object`) in `__init__` and again in every `_execute`. Simpler: validate once in `__init__`, store the result as `int | None`, and have `_execute` read the stored value. Behavior does not change. | File: src/ovcaq/runtime/capability.py:337 | Task: 12
[BOB] ⚪ Cannot statically verify: pytest, ruff and mypy pass at HEAD 3f5a0bd (rework evidence records 3863 passed in 00007-rework-1-evidence/final-pytest.txt) | File: N/A | Task: general

**Prior findings:**
- **Closed:** F01, F03, F05, F08, F09, F10, F11, F12, F13, F17, F20, F25, F29, F30, F31, F32.
- **Closed:** F04. The cap is now bounded, but parking at the limit is a new finding (decision.py:283).
- **Closed:** F07, for `resume` only. The same bug in `request_pause` is a new finding.
- **Closed:** F16, for phases only. The new `capability_timeouts` field is a new finding.
- **Closed:** F18. It fails at the PRD base (task-15-red-replay.txt: 2 failed).
- **Closed:** F22 in production. A leftover fallback is a new ⚪ finding.
- **Settled, unchanged:** F02, F06.
- **Settled, but its premise is now broken:** F23 (see the second 🟠).
- **Discarded, not re-raised:** F14, F15, F19, F21, F24, F27, F28.
- **Replay:** the remaining pass-at-base lines pin behavior that already existed at bbe7d52; their failing parameters pin the change.

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass

FIX:
- SupervisorSignal and post-commit errors swallowed — src/ovcaq/runtime/supervisor.py:309 — re-raise `SupervisorSignal` before the broad handler; have `CapabilityService.run` return the failed state for the runner's own exception so the supervisor needs no catch-all; add a test that signals during a fake capability run and asserts exit 128+N and `operator_stop`
- Non-state OSError turned into state-failure attention — src/ovcaq/runtime/supervisor.py:240 — convert only store read/write errors via `_state_failure` and let spawn/evidence/config/park OSErrors propagate as at base; add a `run()` test with a missing agent binary
- PARK on provider-wide failure at the shared limit — src/ovcaq/runtime/decision.py:283 — when the limit is hit and `failure_decision.kind == WAIT`, return HALT, not PARK
- Supplied capability timeouts ignored — src/ovcaq/runtime/capability.py:335 — pass `self._settings.capability_timeouts` from Supervisor into CapabilityService; keep the disk read only for the standalone CLI retry
- `request_pause` erases the phase pause key — src/ovcaq/state/commands.py:454 — keep the existing `pause_reason` while work is phase-paused (same guard as `resume`)
- Hedged kind asserts — tests/runtime/test_decision_retry_bound.py:60 — assert the exact kind per parameter, also at test_decision_retry_bound.py:87 and test_supervisor_boundary_policy.py:38
- Revision conflict made sticky — src/ovcaq/runtime/supervisor.py:609 — handle `RevisionConflictError` by re-reading state and retrying, not through `_state_failure`
- Stale `batch.status="attention"` — src/ovcaq/state/commands.py:604 — when a success clears this capability's attention without completing the batch, set status back to `running`
- Failure overwrites unrelated attention — src/ovcaq/state/commands.py:599 — write capability attention only when none exists or it already belongs to a capability
- Unknown capability config keys — src/ovcaq/config.py:413 — reject keys other than `timeout_seconds`, as `_phase_tables` does
- Wall-clock fallback — src/ovcaq/state/commands.py:635 — make `completed_at` required and update test callers
- Timeout validated twice — src/ovcaq/runtime/capability.py:337 — validate once in `__init__` and store `int | None`
VERIFY:
- Full suite at HEAD — run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src/ovcaq` at 3f5a0bd
KNOWN:
- (none)

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

**Status:** Done. Review only, no files changed.
**Next:** Task complete. Suggested next: send the two 🟠 findings (signal swallowed during a capability run, OSError reported as a state failure) into rework cycle 2.

Verdict: 28 findings
Tests: 3863 passed, 0 failed, 0 skipped (suite run this cycle)
