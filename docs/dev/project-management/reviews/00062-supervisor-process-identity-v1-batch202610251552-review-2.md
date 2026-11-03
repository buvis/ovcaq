---
prd: docs/dev/project-management/prds/wip/00062-supervisor-process-identity-v1.md
review: 2
date: 2026-10-26
head_sha: 97c97660dc49a7ebaf8883cf5bedd8e0dec6d16a
codex_thread_id: 01a17990-13c9-7113-9781-81faa6c70ef4
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  bob: 46281c12
---

# Review: 00062-supervisor-process-identity-v1 (cycle 2)

Diff range: `fbadc41..97c9766`

codex_rung_guard: not fired

carl: skipped (permanently unavailable since cycle 2 of 00057-autopilot-controller-client-v1.md)

pack: failed (engram pack exit 1: not inside a registered repo)

Incremental review of the cycle-1 rework (tasks 5 and 6) against the cycle-1
consolidated findings. Bob resumed his cycle-1 codex thread.

## Gate state at HEAD (read this before the findings)

- `./tools/check` exits **1** on the same single ruff `BLE001` at
  `tests/workflow_client/test_kill_group_bounded.py:56` cycle 1 recorded. That
  file is outside this PRD's diff range; it is a pre-existing, out-of-scope
  violation already deferred in cycle 1. The gate stops there, before pytest.
- `uv run --locked pytest` at HEAD: **8124 passed, 4 failed, 14 errors** in 242s.
  Three of the failures and all 14 errors are
  `PermissionError: Operation not permitted: 'ps'` from
  `tests/integration/test_terminal_lifecycle.py` — the agent sandbox denying the
  `ps` binary, environmental, the same set cycle 1 saw.
- The fourth failure is new since cycle 1:
  `tests/integration/test_viewer_fallback.py::test_ordinary_fleet_ui_failure_uses_one_bounded_selection`
  ("viewer continued polling an ended selection"). Run alone it **passes**
  (`1 passed in 2.30s`), so it is order-dependent in the full suite. It touches
  no file in this diff. Recorded as R10, not resolved.

## Resolution of cycle-1 findings

- **R1** (fresh batch left running when the first attempt raises before
  `_open_session`): code added, but the revert trigger is wrong — see R2 below.
- **R2** (zero-byte probe result): **resolved**. Zero bytes now returns None
  whatever the errno; docs, `cli.py` notes and tests agree.
- **R3** (publication tracked only after each publish returns): **partly
  resolved**. Both records are tracked before their publish calls, but the
  cleanup can still raise (R1) and only the metadata write-then-raise case is
  tested (R6/R9).
- **R9** (probe messages missing platform and `ovcaq doctor`): **resolved in
  code**; unpinned by tests (R5).
- **R13** (`_PUBLISH_ERRORS` too narrow): unchanged in the code. Ledger-settled
  as single-voice in cycle 1; not re-raised.
- Every other cycle-1 🟡/⚪ row was ledger-discarded as single-voice.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [1/3] | 🟠 | `_cleanup_ownership_records` guards only `OSError`, but `FleetRegistry.remove` raises `ValueError` from `_directory`, `_mutation` and `_verify_root` ("Fleet root is not a real directory", "Fleet root changed", "Fleet lock is not a regular file"). Those are the same failures that make `publish` raise `ValueError` (which is in `_PUBLISH_ERRORS`), so the cleanup hits the same error on a fresh `FleetRegistry`. The `ValueError` escapes `_abandon_start` and `run` before `_revert_fresh_start` runs, leaving a batch running with no supervisor. That is the defect this PRD fixes, and the comment on the method ("a cleanup failure must never block the batch revert") is false for this case. Catch `(OSError, ValueError)` or wrap `_cleanup_ownership_records` so the revert always runs, and add a test where `publish` and `remove` both raise `ValueError`. | src/ovcaq/runtime/supervisor.py:283 | 6 | ALICE |
| R2 | [3/3] | 🟠 | The `_sessions <= 1` guard does not prove no session was opened: `_loop` bumps `_sessions` to 1 before the first `_attempt`, and `_attempt` re-raises after `_open_session` and `_conclude`. A `ConfigurationError` or `CommandError` from `build_launch`, `_collect` or the process-identity probe inside `OwnedProcess.spawn` therefore also reverts a batch whose first session already exists, flipping it to idle while a session metric and summary already hold that batch id. The spec and the cycle-1 R1 text say revert only before `_open_session`. Track "session opened" explicitly and revert only before that; add an after-opening regression test. Only the pre-session route failure is covered (tests/runtime/test_supervisor_preflight.py:554). | src/ovcaq/runtime/supervisor.py:246 | 6 | ALICE, BLAKE, BOB |
| R4 | [1/3] | 🟡 | For `_sessions > 1`, `_abandon_attempt` records nothing (no attention notice, no revert), while the first session writes attention on a resumed batch. A `CommandError` raised in a later session used to reach the CLI as a typed envelope, for example `process_probe` with exit 12. It is now flattened into exit 1 with "attempt failed: ..." and the batch is left running with no notice. Either limit the catch to the first attempt, or record attention for later attempts and keep the typed code. | src/ovcaq/runtime/supervisor.py:202 | 6 | ALICE |
| R5 | [1/3] | 🟡 | The rework changed the wrong-size and wrong-pid `process_probe` messages to name the platform and `ovcaq doctor`. `test_incomplete_kernel_record_is_typed_failure` and `test_identity_belonging_to_another_pid_is_typed_failure` only check the code and exit, so the message requirement from cycle-1 R9 is unpinned. Add assertions on `sys.platform` and "ovcaq doctor" in both tests. | tests/runtime/test_process_identity.py:249 | 5 | ALICE |
| R6 | [2/3] | 🟡 | Cycle-1 R3 asked for write-then-raise tests for both publishers. Only `publish_run_metadata` is covered. There is no test where `FleetRegistry.publish` writes the entry and then raises, so the new `FleetRegistry.remove(..., expected=...)` branch in `_cleanup_ownership_records` is never exercised. Add a fixture that calls the real fleet publisher before raising, and assert both attempted records disappear while foreign entries survive. | tests/runtime/test_supervisor_preflight.py:632 | 6 | ALICE, BOB |
| R7 | [1/3] | 🟡 | `Supervisor.preflight` returns early without checking routes when `boundary_decision(position)` is non-None (paused, drained or completed work). The spec says the build, review and done routes must all resolve before `start_batch`. The early return is an unrequested relaxation. A misconfigured tier is therefore not caught in those states. | src/ovcaq/runtime/supervisor.py:152 | general | BLAKE |
| R8 | [1/3] | 🟡 | `_abandon_attempt` changes state before ownership cleanup runs in `finally`. A crash between these operations can leave idle state with surviving ownership records. Perform ownership cleanup before the revert or attention write, preserving the required filesystem-first order. | src/ovcaq/runtime/supervisor.py:252 | 6 | BOB |
| R10 | [1/3] | 🟡 | The order-dependent viewer failure remains unexplained. Run `uv run --locked pytest -q --tb=short` at base `fbadc41511f5` with the same ordering and sandbox, and compare `test_ordinary_fleet_ui_failure_uses_one_bounded_selection` with the HEAD result. | tests/integration/test_viewer_fallback.py | 4 | BOB |
| R11 | [1/3] | ⚪ | `Supervisor.run` grew from 46 to 50 lines, the 50-line cap. The `ConfigurationError`/`CommandError` branch could go into `_loop` or a helper that wraps the first attempt. | src/ovcaq/runtime/supervisor.py:171 | 6 | ALICE |
| R12 | [1/3] | ⚪ | `_state_failure` is called with site `"startup"`, but the spec names `_state_failure("supervisor.startup")`. The tests pin `"startup"`, and a repo search found nothing for the spec string, so this looks like a spec wording mismatch. | src/ovcaq/runtime/supervisor.py:259 | general | BLAKE |
| R13 | [1/3] | ⚪ | The preflight failure for a missing process identity uses `ErrorCode.USAGE` with a generic message. The spec fixes the code only for the `ConfigurationError` mapping and passes probe errors through as `process_probe`, so this is acceptable but untyped for a None result. | src/ovcaq/runtime/supervisor.py:148 | general | BLAKE |

Consolidation notes:

- `consolidate_findings.py` emitted the `_sessions <= 1` defect as three rows —
  Bob's 🟠 at `supervisor.py:246`, Alice's 🟡 at `supervisor.py:253`, and
  Blake's 🟠 at `supervisor.py:253` which its `--ledger-dismiss BLAKE` filter
  auto-dismissed against a cycle-1 single-voice entry. **That dismissal is
  wrong** and is overridden here: the cycle-1 entry it matched was a different
  defect (the revision-pinned revert at `supervisor.py:246`), and Blake's row is
  this cycle's own finding. The three are merged into **R2 at [3/3] 🟠**, the
  highest-consensus row of the cycle. Alice's separate 🟡 row and Blake's
  dismissed 🟠 are therefore absent by merge, not by drop.
- Alice's and Bob's write-then-raise test-gap rows (same file, same defect) are
  merged into R6 at [2/3].
- Every other row is single-voice as emitted.

## Alice

Six findings, listed above as R1, R2 (merged), R4, R5, R6 and R11. She read the
context, diff, `supervisor.py`, `registry.py` and the process-identity tests and
ran no tests. Her consensus rubric:

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass

## Blake

Blind (PRD-only) lens. Four findings, listed above as R2 (merged), R7, R12 and
R13. Narrow run: 507 tests passed across `test_process_identity`,
`test_supervisor_preflight`, `test_capability`, `test_fleet_registry`,
`test_supervisor_cli`, `test_capability_lifecycle`, `test_runtime_cli` and
`tests/state/test_supervisor_commands.py`.

Verified compliant against the PRD: `process_identity` on libproc
`PROC_PIDTBSDINFO` with the 136-byte size and offsets 4, 12, 120 and 128 pinned
as constants; None for pid <= 0, a zero-byte return, or a zombie (status 5);
`CommandError(PROCESS_PROBE)` on a non-darwin platform, missing or unusable
libproc, wrong size, or pid mismatch, every message naming the platform and
`ovcaq doctor`; `ErrorCode.PROCESS_PROBE` = `process_probe` with exit 12; no
`ps` spawn under `src/ovcaq`; the `forbid_ps` autouse fixture; the six-entry
`_NAMES` with the `process_identity` doctor fact and a degraded fact;
`preflight()` ordered after `require_no_emergency_failure` and before
`_reconcile_capabilities` and `start_batch`; `revert_batch_start` enforcing all
four preconditions and wired for both the publication failure and the
first-attempt failure, with attention on a resumed batch;
`CapabilityService.retry` raising `CommandError(USAGE, "unknown capability:
NAME")` before `reconcile`; every named test present; `process_probe` documented
in `docs/operations.md`, `docs/state-protocol.md` and `CHANGELOG.md`.

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
B15: fail
B16: pass
B17: pass
B18: pass
B19: pass

## Bob

Doubt + de-slop lens (codex, static sandbox, resumed thread
`01a17990-13c9-7113-9781-81faa6c70ef4`).

FIX:
- high: `_sessions <= 1` does not prove no session opened; a later `CommandError` can wrongly revert a batch to idle (src/ovcaq/runtime/supervisor.py:246). Table row R2.
- medium: `_abandon_attempt` changes state before ownership cleanup runs in `finally` (src/ovcaq/runtime/supervisor.py:252). Table row R8.
- medium: prior R3 partly unverified — no fleet write-then-raise test (tests/runtime/test_supervisor_preflight.py:632). Table row R6.

VERIFY:
- medium: the order-dependent viewer failure remains unexplained (tests/integration/test_viewer_fallback.py). Table row R10. **Not queued** as a verification check: it names no check runnable in place — it requires running the suite at base `fbadc41511f5` — so it stays an ordinary finding, per the queue's exact-command rule.

KNOWN:
- (none)

R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Mechanical checks

- Tautological test shapes: none flagged.
- Fail-first replay: no `[MECH]` replay line this cycle.

## Carl

Carl: skipped (permanently unavailable since cycle 2 of 00057-autopilot-controller-client-v1.md)

Verdict: 11 findings
Tests: 8124 passed, 4 failed, 14 errors (suite run this cycle; 3 failures and all 14 errors are sandbox `ps` denials in tests/integration/test_terminal_lifecycle.py, the 4th is order-dependent and passes alone)
