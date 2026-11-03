---
prd: docs/dev/project-management/prds/wip/00062-supervisor-process-identity-v1.md
review: 1
date: 2026-10-26
head_sha: fbadc41511f5183cec9088181a649c65d3144fe3
codex_thread_id: 01a17990-13c9-7113-9781-81faa6c70ef4
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  bob: d3cc89e7
---

# Review: 00062-supervisor-process-identity-v1

Diff range: `fa26fb7..fbadc41`

codex_rung_guard: not fired

carl: skipped (permanently unavailable since cycle 2 of 00057-autopilot-controller-client-v1.md)

pack: failed (engram pack exit 1: not inside a registered repo)

Reviewed: 4 completed tasks (all `claude` implementor, tier opus).

## Gate state at HEAD (read this before the findings)

- `./tools/check` exits **1** on one ruff `BLE001` at
  `tests/workflow_client/test_kill_group_bounded.py:56`. That file is **not** in
  this PRD's diff range (last touched by PRD 00057-era commits), so the project
  gate is red at HEAD for a pre-existing, out-of-scope reason. Recorded as a
  deferred decision, not fixed inside this PRD.
- `uv run --locked pytest` at HEAD: **8121 passed, 3 failed, 14 errors**. All 17
  non-passing results are `PermissionError: [Errno 1] Operation not permitted:
  'ps'` raised from `tests/integration/test_terminal_lifecycle.py`, i.e. the
  agent sandbox denying the `ps` binary. They are environmental, not code
  defects — but see R16: that helper is the one `ps` caller this PRD's task 4
  left unconverted, so converting it also makes the suite green in the sandbox.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [1/3] | 🟠 | `Supervisor.run` reverts a fresh batch only when `_publish_ownership` fails. The spec also requires the revert when the first `_attempt` raises before `_open_session`. `_loop` catches only `_STATE_ERRORS`. A `ConfigurationError` from `resolve_phase_route`, or a `CommandError` from `process_identity` in `_open_session`, propagates out of `run` and leaves `batch.status` running with no supervisor. That is the exact defect this PRD fixes. No test covers this path. | src/ovcaq/runtime/supervisor.py:188 | general | BLAKE |
| R2 | [1/3] | 🟠 | `process_identity` deviates from the spec on zero bytes returned. The spec says a pid the kernel does not know (zero bytes) returns None, and only sizes other than 0 or 136 raise. The code returns None only when errno is ESRCH. For any other errno, including errno 0, it raises `process_probe`. The tests pin this stricter behavior (`test_denied_probe_is_typed_failure_while_absent_pid_is_simply_gone`). The choice is defensible, but it contradicts the PRD. | src/ovcaq/runtime/registry.py:181 | general | BLAKE |
| R3 | [1/3] | 🟠 | Publication progress is recorded only after each publishing call returns. If either call writes its record and then raises, rollback misses that record and can leave an orphan. Track attempted publication, clean matching records independently, and test write-then-raise failures for both publishers. | src/ovcaq/runtime/supervisor.py:314 | 1 | BOB |
| R4 | [1/3] | 🟡 | `_abandon_start` swallows a cleanup failure with a bare `except OSError: pass`. The orphan run record can survive and nothing reports it, because the decision reason carries only the publication error. Fold the cleanup error into the decision reason, or record it, while still running the state step | src/ovcaq/runtime/supervisor.py:241 | 1 | ALICE |
| R5 | [1/3] | 🟡 | The `cleanup_run_records` leg of `_abandon_start` is effectively unreachable and untested. Nothing after `FleetRegistry.publish` returns can raise, so `_fleet_entry` is only set when no failure follows. The real gap is `publish` raising after it has already replaced the entry file: `_fleet_entry` is still None, the metadata-only branch runs, and the fleet entry is orphaned. Tests only exercise the metadata-only leg, via `fail_fleet_publish` | src/ovcaq/runtime/supervisor.py:237 | 1 | ALICE |
| R6 | [1/3] | 🟡 | New early-failure behaviors have no test. These are the removal-failure path (state step must still run), the revert falling back on a `RevisionConflict` or other state error (only the `ValueError` fallback is covered), and `CommandError` or `ValueError` from publication (only `OSError` and `RuntimeError` are covered). The `preflight` state-error branch returning `_state_failure("startup")` is also untested | tests/runtime/test_supervisor_preflight.py:423 | 1 | ALICE |
| R7 | [1/3] | 🟡 | Two tests pass against the pre-change code (fail-first replay): `test_cli_retry_of_a_declared_capability_is_not_a_usage_error` and `test_retry_accepts_a_declared_capability_and_runs_only_that_one`. The first uses a weak negative assertion (`code != "usage"` and `"unknown capability" not in message`). They guard against over-rejection but do not pin the change; assert the concrete outcome (exact envelope code and exit) or fold them into the unknown-name test as controls | tests/runtime/test_supervisor_cli_capability.py:88 | 2 | ALICE, mech-check |
| R8 | [1/3] | 🟡 | `Supervisor.preflight` now skips route validation for paused or drained work positions (task 4, via `boundary_decision`), but docs/operations.md, docs/state-protocol.md and `PROCESS_IDENTITY_NOTES` in src/ovcaq/cli.py still say `ovcaq run` validates the build, review and done routes before any state write. The docs overstate the contract; add the exception | docs/operations.md:61 | 3 | ALICE |
| R9 | [2/3] | 🟡 | Three `process_probe` messages break the spec's message requirement. The refused-probe, wrong-size and wrong-pid errors name neither the platform nor `ovcaq doctor`. Only the `_libproc` failures (non-darwin platform, missing library, unloadable library) do. The spec says every probe error names the platform and tells the operator to run `ovcaq doctor`. | src/ovcaq/runtime/registry.py:185 | general | BLAKE, BOB |
| R10 | [1/3] | 🟡 | `preflight()` skips route validation when `boundary_decision` is non-None (paused or drained work position, with pause and attention neutralised). The spec requires `resolve_phase_route` to succeed for build, review and done unconditionally. Commit f80c30d added the skip as a deliberate deviation. It is extra logic beyond the PRD and means a broken route passes preflight in that state. | src/ovcaq/runtime/supervisor.py:152 | general | BLAKE |
| R11 | [1/3] | 🟡 | The attention site written on early failure is "startup", not the spec's `_state_failure("supervisor.startup")`. "startup" was already the pre-existing site and the tests pin it (tests/runtime/test_supervisor_preflight.py:473). The text still deviates from the spec. | src/ovcaq/runtime/supervisor.py:244 | general | BLAKE |
| R12 | [1/3] | 🟡 | `_abandon_start` calls `revert_batch_start` pinned to `started["revision"]`. If anything commits to state between `start_batch` and the revert (for example an operator pause), the revert raises a revision conflict. The code then falls back to attention, leaving a running batch with no supervisor. The result is acceptable and recorded, but this is a residual gap in the "never running without a supervisor" goal. | src/ovcaq/runtime/supervisor.py:246 | general | BLAKE |
| R13 | [1/3] | 🟡 | `_PUBLISH_ERRORS` excludes ordinary exceptions such as `TypeError` and `KeyError`, although the contract requires rollback for any publication exception. Catch `Exception` around `_publish_ownership`; interrupts still propagate. | src/ovcaq/runtime/supervisor.py:190 | 1 | BOB |
| R15 | [1/3] | ⚪ | `tests/runtime/test_runtime_cli.py` is 1271 lines, over the 800 limit, and this diff grew it by 37. `tests/runtime/test_supervisor_cli.py` is 796 lines, right at the limit. Put the new `process_identity` doctor test in a separate file | tests/runtime/test_runtime_cli.py:931 | 1 | ALICE |
| R16 | [1/3] | ⚪ | Task 4 told the implementer to report anything `process_identity` cannot answer in `ps_field`. `ps_field("command", ...)` still spawns `ps` at three sites, and no report of this is in the diff. This is the source of the sandbox `PermissionError: 'ps'` failures and errors, so it is not a code defect, but the helper is only half converted | tests/integration/test_terminal_lifecycle.py:106 | 4 | ALICE |
| R17 | [1/3] | ⚪ | The `CONTROLLER_CLIENT_NOTES` text in `src/ovcaq/cli.py` was rewritten (PRD 58 artifact and capability wording) and is unrelated to PRD 00062. It appears to be generated-doc drift synced into the source. Keep it, but note it as out of scope | src/ovcaq/cli.py:277 | 3 | ALICE |
| R18 | [1/3] | ⚪ | `forbid_ps` matches any argv[0] whose basename is `ps` (for example /usr/bin/ps). That is broader than the spec's "ps or /bin/ps". It is harmless. | tests/runtime/conftest.py:18 | general | BLAKE |
| R19 | [1/3] | ⚪ | The runtime CLI test module exceeds the 800-line limit; its final function starts at line 1222. The violation predates this PRD, and restructuring the existing suite is outside scope. | tests/runtime/test_runtime_cli.py:1222 | general | BOB |

Consolidation notes: `consolidate_findings.py` emitted R9 and R14 as separate
rows (Blake and Bob wording differed) although both name the same defect at
`src/ovcaq/runtime/registry.py:185`. The decision gate merged them into R9 at
two-of-three consensus; R14 is therefore absent from this table by merge, not
by drop. The same judgment merged Alice's R8 (the docs) and Blake's R10 (the
code) into one two-of-three deviation, kept as two rows so both sites stay
named. Every other row is single-voice as emitted.

## Alice

Eight findings, listed above as R4-R8 and R15-R17. Her consensus rubric:

R1: fail
R2: fail
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: fail
R11: pass
R12: pass
R13: fail

## Blake

Blind (PRD-only) lens. Seven findings, listed above as R1, R2, R9, R10, R11,
R12, R18. He ran his own narrow checks: `uv run pytest tests/runtime
tests/state/test_cli.py tests/state/test_commands.py` → 1751 passed; `uv run
mypy src` → clean; `uv run ruff check src tests` → the one out-of-scope
`BLE001`. He confirms no `ps` spawn remains under `src/`.

Verified compliant against the PRD: libproc loaded through
`ctypes.util.find_library("proc")`; the 136-byte record size and offsets 4, 12,
120 and 128; `PROC_PIDTBSDINFO`; `SZOMB` = 5; the `f"{sec}.{usec:06d}"` token
format; non-positive pids, zombies and pid mismatches handled;
`ErrorCode.PROCESS_PROBE` = `process_probe` with exit code 12; the
`process_identity` doctor fact with a six-entry `_NAMES` and a degraded fact
flipping `ok` to false; `preflight` ordered after `require_no_emergency_failure`
and before `_reconcile_capabilities` and `start_batch`; `revert_batch_start`
enforcing all four preconditions; `CapabilityService.retry` raising
`CommandError(USAGE, "unknown capability: NAME")` before `reconcile`;
`process_probe` documented in `docs/operations.md`, `docs/state-protocol.md` and
`CHANGELOG.md`.

B1: fail
B2: pass
B3: pass
B4: pass
B5: fail
B6: fail
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

## Bob

Doubt + de-slop lens (codex, static sandbox, thread
`01a17990-13c9-7113-9781-81faa6c70ef4`).

FIX:
- high: Publication progress is recorded only after each publishing call returns; a write-then-raise leaves an orphan record (src/ovcaq/runtime/supervisor.py:314). Table row R3.
- medium: `_PUBLISH_ERRORS` excludes ordinary exceptions such as `TypeError` and `KeyError` (src/ovcaq/runtime/supervisor.py:190). Table row R13.
- medium: Refused probes, unexpected record sizes and PID mismatches produce messages without the platform and the `ovcaq doctor` remedy (src/ovcaq/runtime/registry.py:185). Table row R9.

VERIFY:
- (none)

KNOWN:
- low: The runtime CLI test module exceeds the 800-line limit; the violation predates this PRD and restructuring the existing suite is out of scope. Table row R19.

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
R13: fail

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Mechanical checks

- Tautological test shapes: 215 test functions in 15 files checked, none flagged.
- Fail-first replay: 57 touched tests ran against base `fa26fb71a8f6`, 55 failed
  there, 2 passed — `test_cli_retry_of_a_declared_capability_is_not_a_usage_error`
  and `test_retry_accepts_a_declared_capability_and_runs_only_that_one`, both
  absorbed into R7 with `mech-check` as a finder.

## Carl

Carl: skipped (permanently unavailable since cycle 2 of 00057-autopilot-controller-client-v1.md)

Verdict: 18 findings
Tests: 8121 passed, 3 failed, 14 errors (suite run this cycle; all 17 non-passing are sandbox `ps` denials in tests/integration/test_terminal_lifecycle.py)
