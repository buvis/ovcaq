---
prd: docs/dev/project-management/prds/wip/00062-supervisor-process-identity-v1.md
review: 1
date: 2026-10-28
head_sha: 186584f05272cfa01041822d2807983f01b37b55
codex_thread_id: 01a180d3-e689-77e1-bb4f-cfec0995b7b5
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: 30b1f15b
  carl: 538cf06a
---

# Review: 00062-supervisor-process-identity-v1

Diff range: `02c391de..186584f`

codex_rung_guard: not fired

carl: unavailable (gemini-run.sh exited 1 on the first dispatch, row `538cf06a`, and on
the retry, row `12487860`, both "You have exceeded your monthly quota", backend=copilot
model=gemini-3.8-flash). Fourth consecutive cycle lost to the same monthly quota. A quota
exit is a one-off runtime failure, **not** the permanent exit-4 class, so Carl is NOT
latched for the batch. He published a 0-byte `-o` file, which was not consolidated.

pack: failed (engram pack exit 1: not inside a registered repo; run `gita add /Users/bob/git/src/github.com/buvis/ovcaq`)

Reviewed: 1 completed task (`claude` implementor, tier opus).

## Scope note (read before the findings)

`state.work_start_sha` is `02c391de`, which deliberately spans PRD 00062's **whole** work
range. Because 00062's first pass landed in the earlier batch 202610251552 and PRD 00057
was completed in between, this range also carries 00057's already-converged
`workflow_client` commits. `src/ovcaq/workflow_client.py`, `src/ovcaq/config.py`,
`tools/autopilot-prerequisites` and `tests/workflow_client/**` are therefore reviewed
out-of-scope context, not this PRD's surface, and findings against them are discarded on
that ground rather than counted as scope creep.

Six of the PRD's seven tasks were verified already satisfied on master at planning time.
Only Phase 1 task 4 ("Harden the early-failure revert — review cycle 2 residuals R1, R2,
R6") was built this session, as commits 9bbbf35, cbaf58c, e228a3f and 186584f.

Cycle 1 review files from the earlier batch were preserved as
`00062-supervisor-process-identity-v1-batch202610251552-review-{1,2}.md` so this batch's
cycle numbering starts clean without deleting durable review history.

## Gate state at HEAD

- `./tools/check` (ruff + mypy + format): **All checks passed!** The `BLE001` that made the
  gate red in the earlier batch was fixed by `d440d98`.
- `uv run --locked pytest`: **8220 passed, 61 failed, 14 errors** in 241.59s. Every one of
  the 61 failures and 14 errors is in `tests/integration` or `tests/tui` and is caused by
  the agent sandbox denying the `/bin/ps` binary (`PermissionError: Operation not
  permitted: 'ps'`). `tests/runtime` and `tests/state` are fully green. Blake confirmed
  independently that the failing tests spawn `ps` themselves
  (`tests/integration/test_terminal_lifecycle.py:108`) and that nothing under `src/ovcaq`
  does.

`review-stage`'s gate parser did not recognise pytest's own summary line, so it reported
`counts unavailable`. The counts above are read verbatim from its own log at
`docs/dev/tmp/gate-20261028-0430.log:6113` rather than by re-running the suite.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | 🟡 | The session-opened branch deviates from the PRD helper with no code comment saying why. The tests assert only `attention["detail"].strip()` and `site == "startup"`, so swapping `_attention_notice` for `_state_failure` would pass. Pin `attention["detail"]` as `attempt failed: kernel probe refused` in `test_failure_after_session_opened_never_reverts`. Add a one-line comment that the generic `_state_failure` text would mislabel a probe or route failure as a state failure. | src/ovcaq/runtime/supervisor.py:264 | 1 | ALICE, BLAKE |
| R2 | [1/3] | 🟠 | A zero-byte probe returns None even for EPERM/EACCES, so denied live processes appear dead and can be pruned. The PRD explicitly requires a process_probe error for these cases. | src/ovcaq/runtime/registry.py:180 | general | BOB |
| R3 | [2/3] | 🟡 | `_session_opened` is set after `create_session` rather than at `_open_session`'s return as the PRD specifies, and no test pins that placement. A refactor to the PRD placement, or to before `create_session`, would pass every test. Add a test where `publish_session_metric` raises `CommandError` after the session directory exists and assert the batch stays running with attention, or add a comment at supervisor.py:533 saying "session exists on disk, so never revert". BOB, independently: `_session_opened` becomes true before `_open_session` returns, contrary to the required boundary; a partial opening can therefore set the flag. | src/ovcaq/runtime/supervisor.py:533 | 1 | ALICE, BOB |
| R5 | [1/3] | 🟡 | Abandoned reader threads retain threads and pipe descriptors indefinitely when a detached descendant keeps the pipes open. Repeated timeouts accumulate these resources. | src/ovcaq/workflow_client.py:483 | general | BOB |
| R6 | [1/3] | 🟡 | The unavailable-library test sets a non-Darwin platform, which rejects the probe before the mocked find_library(None) branch executes. That failure path remains untested. | tests/runtime/test_process_identity.py:174 | general | BOB |
| R7 | [1/3] | 🟡 | Two new stage_bundle helpers duplicate predecessor, artifact, bundle and configuration setup. Move their common setup into prerequisites_support. | tests/workflow_client/test_prerequisites_controller.py:410 | general | BOB |
| R8 | [1/3] | ⚪ | The fallback `except _STATE_ERRORS: self._state_failure("startup")` in the session-opened branch is untested. No test makes the attention write itself fail after a session opened. It is low risk, since it mirrors the tested `_revert_fresh_start` fallback. | src/ovcaq/runtime/supervisor.py:269 | 1 | ALICE |
| R9 | [1/3] | ⚪ | `StateService.revert_batch_start` makes `expected_revision` optional (default None). The spec signature is keyword-only and required. | src/ovcaq/state/commands.py:516 | Phase 1 task 3 | BLAKE |
| R10 | [1/3] | ⚪ | Test placement differs from the spec. The identity tests live in tests/runtime/test_process_identity.py, not test_fleet_registry.py. The early-failure hardening tests live in tests/runtime/test_supervisor_early_failure.py, not test_supervisor_preflight.py. The named tests exist and pass. | tests/runtime/test_supervisor_early_failure.py | Phase 1 task 4 | BLAKE |
| R11 | [1/3] | 🟠 | Early-failure revert covers only `ConfigurationError` and `CommandError` from the loop. `_loop` catches `_STATE_ERRORS` (including `OSError`) and returns `_state_failure("supervisor.loop")` with no revert. An `OSError` from `create_session` inside the first `_open_session`, before `_session_opened` is set, therefore leaves a fresh batch `running` with no supervisor, which is the bug this task targets. A bare `AssertionError` from `assert identity is not None` in `_open_session` (src/ovcaq/runtime/supervisor.py:520), or any other `ValueError`/`RuntimeError` from the first attempt, escapes `_abandon_attempt` the same way. | src/ovcaq/runtime/supervisor.py:204 | Phase 1 task 3 | BLAKE |
| R12 | [1/3] | 🟡 | 2 touched test(s) pass against the pre-change code: test_cli_retry_of_a_declared_capability_is_not_a_usage_error | tests/runtime/test_supervisor_cli_capability.py | general | mech-check |
| R13 | [1/3] | 🟡 | 2 touched test(s) pass against the pre-change code: test_the_published_redaction_constants_keep_their_values, test_detail_keeps_secret_free_and_multibyte_stderr_whole | tests/workflow_client/test_actor_secret_redaction.py | general | mech-check |
| R14 | [1/3] | 🟡 | 17 touched test(s) pass against the pre-change code: test_apply_raises_outcome_unknown_on_output_bound_overrun, test_apply_raises_outcome_unknown_on_non_json_stdout_after_zero_exit, test_apply_raises_outcome_unknown_on_malformed_response +11 more | tests/workflow_client/test_apply_outcome_unknown.py | general | mech-check |
| R15 | [1/3] | 🟡 | 3 touched test(s) pass against the pre-change code: test_envelope_rejects_missing_request_or_project_id_on_initial_open | tests/workflow_client/test_contract.py | general | mech-check |
| R16 | [1/3] | 🟡 | 27 touched test(s) pass against the pre-change code: test_bundle_digest_is_stable_for_the_fixture, test_bundle_digest_matches_byte_copy_at_another_path, test_bundle_digest_detects_single_byte_value_change, test_bundle_digest_rejects_mismatched_artifact +21 more | tests/workflow_client/test_contract_digest.py | general | mech-check |
| R17 | [1/3] | 🟡 | 3 touched test(s) pass against the pre-change code: test_nonzero_exit_message_keeps_only_a_marked_tail_of_long_prose_stderr | tests/workflow_client/test_controller_boundary.py | general | mech-check |
| R18 | [1/3] | 🟡 | 5 touched test(s) pass against the pre-change code: test_kill_group_completes_within_bounded_time_when_signal_is_denied, test_kill_group_reports_a_signal_failure_that_is_not_a_denial, test_kill_group_ends_a_grandchild_sharing_the_controller_group, test_capture_completes_within_bounded_time_when_a_pipe_stays_open | tests/workflow_client/test_kill_group_bounded.py | general | mech-check |
| R19 | [1/3] | 🟡 | 44 touched test(s) pass against the pre-change code: test_contract_rejects_live_controller_missing_a_pinned_operation, test_contract_rejects_live_controller_missing_a_pinned_capability +38 more | tests/workflow_client/test_negotiation.py | general | mech-check |
| R20 | [1/3] | 🟡 | 5 touched test(s) pass against the pre-change code: test_call_raises_timeout_when_controller_outlives_timeout, test_apply_never_returns_result_when_ack_precedes_timeout | tests/workflow_client/test_transport.py | general | mech-check |

R12-R20 are the fail-first replay's `[MECH]` rows, absorbed per the consolidation rules.
R1 merged ALICE's `supervisor.py:264` with BLAKE's `supervisor.py:268` after suffix
stripping.

Two gate corrections to the consolidator's output, both recorded in
`autonomous_decisions`:

- **R3 is a gate merge.** `consolidate_findings.py` emitted ALICE's and BOB's reports of
  the `_session_opened` placement as two separate single-voice rows (its old R3 and R4)
  because the wording differs, although both name
  `src/ovcaq/runtime/supervisor.py:533` and the same defect. They are merged here as one
  two-voice row carrying both reviewers' words verbatim. Applying the single-voice discard
  rule to a merge miss would have thrown away a two-voice finding.
- **R11 is carried at 🟠, above BLAKE's own 🟡.** The gate verified the claim directly
  against the code rather than taking his word for it, and what it proves is a reachable
  path that leaves a freshly started batch at `status: running` with no supervisor — the
  exact condition this PRD's "Early failure returns a fresh batch to idle" feature exists
  to eliminate, and a named success metric. The PRD conditions the revert on *when* the
  failure happens, not on the exception's type. A medium single-voice row would have been
  discarded, so the severity is the honest carrier of the verification, not a device to
  force a task.

### Auto-dismissed (ledger)

- [BLAKE] 🟡 Preflight skips route validation when the workflow is at a boundary (paused, attention set, or drained). The spec says routes for build, review and done must always resolve before `start_batch`. A misconfigured tier on a paused or attention-flagged project is therefore found only after resume, which is the failure mode the PRD set out to remove. | File: src/ovcaq/runtime/supervisor.py:155 — single-voice
- [BLAKE] 🟡 Early-failure revert covers only `ConfigurationError` and `CommandError` from the loop. `_loop` catches `_STATE_ERRORS` (including `OSError`) and returns `_state_failure("supervisor.loop")` with no revert. An `OSError` from `create_session` inside the first `_open_session`, before `_session_opened` is set, therefore leaves a fresh batch `running` with no supervisor, which is the bug this task targets. A bare `AssertionError` from `assert identity is not None` in `_open_session` (src/ovcaq/runtime/supervisor.py:520), or any other `ValueError`/`RuntimeError` from the first attempt, escapes `_abandon_attempt` the same way. | File: src/ovcaq/runtime/supervisor.py:204 — single-voice

**The second auto-dismissal was overridden at the decision gate** and reinstated above as
R11. The ledger matched it to a cycle-1 entry at `src/ovcaq/runtime/supervisor.py:190`
about `_PUBLISH_ERRORS` excluding `TypeError`/`KeyError`. That is a different leg of
`run()`: `_publish_ownership` is guarded by the broad `_PUBLISH_ERRORS`, while the
first-`_attempt` leg at line 204 is guarded only by `(ConfigurationError, CommandError)`.
The settled entry's recorded reason was a bare `single-voice` discard, not a refutation of
the claim. The gate verified the reinstated claim directly against the code:
`_STATE_ERRORS = (StateError, SchemaError, OSError)` at `supervisor.py:93`,
`_PUBLISH_ERRORS = (*_STATE_ERRORS, CommandError, RuntimeError, ValueError)` at line 96,
the narrow catch at line 204, and `_loop`'s `except _STATE_ERRORS: return
self._state_failure("supervisor.loop")` at lines 387-388, which performs no revert.

The first auto-dismissal stands: it was settled as single-voice in both cycle 1 and cycle 2
of the earlier batch, at `supervisor.py:152`.

## Alice (consensus)

Ran `tests/runtime/test_supervisor_early_failure.py` and
`tests/runtime/test_supervisor_preflight.py`: 32 passed. Did not re-run the full suite.
Treated `workflow_client`, `config` and the `autopilot-prerequisites` tool as out of scope.

**Deviation (a) — `_attention_notice("startup", detail)` instead of
`_state_failure("supervisor.startup")` at supervisor.py:264: ACCEPT.** The implementor's
"false emergency marker" reason is weak — `_state_failure` goes through
`record_state_failure` (`src/ovcaq/runtime/session.py:580`), which writes the emergency
marker only when the notice write itself fails, and on success writes the same attention
notice. A better reason exists: `_state_failure` hard-codes the detail "Supervisor state
operation failed; inspect state before restarting", which would be false here because the
cause is a `CommandError` or `ConfigurationError`, not a state failure. The direct call
keeps the real cause in `attention.detail`. The fallback to `_state_failure("startup")` on
`_STATE_ERRORS` (lines 269-270) preserves the emergency-marker guarantee if the notice
write fails. The site string "startup" matches the settled decision, so only the helper and
the detail text differ from the PRD. The inconsistency is real but contained: the other
abandon legs (lines 184, 189, 275, 282) are genuine state failures, where the generic text
is correct.

**Deviation (b) — `_session_opened = True` at supervisor.py:533 rather than at
`_open_session`'s return: ACCEPT, but unpinned.** Between line 533 and the return there are
only `publish_session_metric` and `publish_run_metadata` (lines 551-555). The `except` at
line 204 catches only `ConfigurationError` and `CommandError`; those two calls raise
`OSError` or `ValueError`, which already propagate uncaught, so no reachable path behaves
differently from the PRD placement today. The earlier placement is the safer one: once
`create_session` has created the session directory, the batch is never reverted over
existing session evidence. No test pins the placement.

Other checks: `_cleanup_ownership_records` catches `(OSError, ValueError)` on the fleet
removal leg (line 305) with the metadata leg keeping its own try, matching the contract;
`_session_opened` is initialised in `__init__` (line 144) and reset in `run()` (line 174);
the `_state_failure` refactor into `_attention_notice` preserves behavior; the new sibling
test module avoids growing `test_supervisor_preflight.py` past the 800-line limit; `run` is
about 40 lines and `_abandon_attempt` about 20, both under the 50-line cap; the CHANGELOG
entries are present; no secrets, injection risks or debug markers.

Three new tests bind to intent, and two would fail against the old code:
`test_failure_after_session_opened_never_reverts`
(`tests/runtime/test_supervisor_early_failure.py:200`) — the old `_sessions <= 1` check
would revert the batch to idle; `test_cleanup_failure_never_blocks_the_revert` (line 56) —
the old code lets the `ValueError` escape; `test_fleet_entry_written_then_raise_is_removed`
(line 268) pins existing behavior and passes against the old code, which the task text
anticipated as test-only.

Findings: R1, R3 (merged with BOB's row), R8.

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

## Blake (blind, PRD-only)

Located the code himself from the spec alone. Ran
`tests/runtime/test_process_identity.py`, `test_supervisor_preflight.py`,
`test_supervisor_early_failure.py` and `tests/state/test_supervisor_commands.py`: 166
passed. Did not re-run the full suite.

Findings: R11 (reinstated over a wrong ledger dismissal), R9, R10, plus two rows absorbed
elsewhere (his `supervisor.py:268` row merged into R1; his `supervisor.py:155` row
auto-dismissed as settled).

Verified as spec-compliant:

- **Probe:** `process_identity` reads libproc `proc_pidinfo` with `PROC_PIDTBSDINFO`. The
  struct size is 136 bytes with offsets 4, 12, 120 and 128. The token is
  `{sec}.{usec:06d}`. It returns None for pid <= 0, for zero bytes returned, and for
  SZOMB. A wrong size, a wrong pid, a library load failure or a non-darwin platform raises
  `CommandError(PROCESS_PROBE)` (exit 12) naming the platform and `ovcaq doctor`.
  (`src/ovcaq/runtime/registry.py:128`; `src/ovcaq/errors.py:20,37`)
- **No `ps` in `src/ovcaq`:** the only `ps` mentions are documentation strings in
  `src/ovcaq/cli.py`. The `forbid_ps` autouse fixture is in
  `tests/runtime/conftest.py:21`.
- **Doctor fact:** `_NAMES` has six entries and `require_process_capabilities` requires
  them. `_probe_process_identity` returns supported with the token, or degraded with the
  error text. (`src/ovcaq/runtime/capability.py:38,183,197`)
- **Preflight position:** it runs after `require_no_emergency_failure` and before
  `_reconcile_capabilities` and `start_batch`. `ConfigurationError` becomes
  `CommandError(USAGE)` with the original message, and the probe error passes through.
  (`src/ovcaq/runtime/supervisor.py:180`)
- **`revert_batch_start`:** it checks status running, matching `batch.id`, `work.prd` None
  and `completed_prds` empty, and raises `ValueError` otherwise. It restores id "",
  `started_at` None and status idle. (`src/ovcaq/state/commands.py:516`)
- **Session-opened flag and cleanup:** the explicit `_session_opened` flag exists
  (`supervisor.py:533`) and `_cleanup_ownership_records` catches `OSError` and `ValueError`
  for each record independently (`supervisor.py:284`).
- **Unknown capability:** `CapabilityService.retry` checks membership first and raises
  `CommandError(USAGE, "unknown capability: NAME")` (`src/ovcaq/runtime/capability.py:341`).
  `_retry` does not rewrap `CommandError`. No production declaration of a required
  capability exists, and the pin test `run_declares_no_required_capability` exists.
- **Docs and changelog:** `process_probe` appears in `CHANGELOG.md`, `docs/operations.md`
  and `docs/state-protocol.md`.
- **Tests:** all tests named in the spec exist.
- **Failures outside the runtime tests:** the integration and TUI failures come from tests
  that spawn `ps` themselves (`tests/integration/test_terminal_lifecycle.py:108`). They are
  not caused by `src`.

B1: fail
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: pass
B16: pass
B17: pass
B18: pass
B19: pass

## Bob (codex — doubt lens + de-slop)

Findings: R2, R3 (merged with ALICE's row), R5, R6, R7.

FIX:
- Distinguish zero-byte results by errno; raise process_probe except for ESRCH or zero, and correct the tests and documentation.
- Set `_session_opened` immediately after `_open_session` returns; test an exception before that return.
- Use deadline-aware nonblocking pipe reads so timeout cleanup closes descriptors without abandoning blocked threads.
- Test find_library returning None on Darwin separately from unsupported-platform rejection.
- Consolidate the duplicated stage_bundle setup; retain caller-specific configuration in each test.

VERIFY:
- (none)

KNOWN:
- (none)

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: fail

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl (UI / frontend & design)

Unavailable — see the `carl:` line in the top matter. No UI/design voice reviewed this PRD
in any cycle of either batch. The PRD touches no frontend, so the loss is low-impact here,
but the roster was three of four this cycle, never four.

Verdict: 19 findings
Tests: 8220 passed, 61 failed, 14 errors (suite run this cycle; every failure and error in tests/integration or tests/tui from the sandbox /bin/ps denial)
