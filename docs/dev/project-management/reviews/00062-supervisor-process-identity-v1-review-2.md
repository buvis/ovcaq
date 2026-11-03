---
prd: docs/dev/project-management/prds/wip/00062-supervisor-process-identity-v1.md
review: 2
date: 2026-10-28
head_sha: a12b659075a9e9c69c97999de27224ff960c2b1a
codex_thread_id: 01a180d3-e689-77e1-bb4f-cfec0995b7b5
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: cd2cfcc2
  carl: 1ca0a783
---

# Review: 00062-supervisor-process-identity-v1 (cycle 2, incremental)

Diff range: `186584f..a12b659`

codex_rung_guard: not fired

carl: unavailable (gemini-run.sh exited 1 on the first dispatch, row `1ca0a783`, and on the
retry, row `a55db94c`, both "You have exceeded your monthly quota", backend=copilot
model=gemini-3.8-flash). Fifth consecutive cycle lost to the same monthly quota. A quota
exit is a one-off runtime failure, **not** the permanent exit-4 class, so Carl is NOT
latched for the batch. He published a 0-byte `-o` file, which was not consolidated.

pack: failed (engram pack exit 1: not inside a registered repo; run `gita add /Users/bob/git/src/github.com/buvis/ovcaq`)

Reviewed: the cycle-1 rework only — commits 2ef01f8, df43989 (task 2) and a12b659
(task 3). Bob resumed his cycle-1 codex thread, so his verification is against his own
earlier critique.

Mechanical blocks this cycle: 0 tautological test shapes (22 test functions checked in 2
files), and the fail-first replay ran 0 touched tests (both touched test files fail to
collect against the base commit, because they exercise code the rework added). No `[MECH]`
findings, so none were absorbed. No prior-cycle verification-check queue exists for this
batch, so nothing was carried forward.

## Gate state at HEAD

- `uv run --locked pytest`: **8280 passed, 3 failed, 14 errors** in 251.13s. All 3 failures
  and all 14 errors are in `tests/integration/test_terminal_lifecycle.py`, caused by the
  agent sandbox denying the `/bin/ps` binary (`PermissionError: Operation not permitted:
  'ps'`). `tests/runtime` and `tests/state` are fully green (Alice: 2654 passed; Blake:
  1682 passed in `tests/runtime`). This is the same sandbox-caused failure class cycle 1
  recorded, now 3 failed instead of 61 — no new failure outside it.
- `review-stage`'s gate parser again did not recognise pytest's own summary line and
  reported `counts unavailable`. The counts above are read verbatim from its own log at
  `docs/dev/tmp/gate-20261028-c2.log:3760` rather than by re-running the suite, which the
  same gate run had already completed this cycle.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | 🟡 | `_loop` now catches `ValueError`, `RuntimeError` and `AssertionError` for every attempt. Once a session has opened, these go to `_state_failure("supervisor.loop")`, which writes the generic "Supervisor state operation failed" text, and the original error is dropped with nothing logged. Before the rework they surfaced as a traceback. `ConfigurationError` subclasses `ValueError`, so it takes the same path. A later-session route error used to reach `_abandon_attempt` and record "attempt failed: <message>", and it now gets the generic text. Limit the widened catch to the not-yet-opened case (re-raise when `self._session_opened`), or put the error text into the attention detail. No test pins the session-opened behaviour for these exception types. BOB, independently: the widened loop catch extends the new recovery beyond its intended pre-session scope and drops the error detail. | src/ovcaq/runtime/supervisor.py:398 | 2 | ALICE, BOB |
| R2 | [2/3] | 🟡 | The cycle-1 R1 test pin is still missing. `test_failure_after_session_opened_never_reverts` asserts only `attention["detail"].strip()` and the site, so replacing `_attention_notice` with `_state_failure` still passes. Assert `attention["detail"] == "attempt failed: kernel probe refused"`. The new comment sits inside the `except _STATE_ERRORS` fallback and reads as if it explains that fallback. Move it to the `_attention_notice` call it justifies. | tests/runtime/test_supervisor_early_failure.py:228 | 2 | ALICE, BOB |
| R3 | [1/3] | 🟠 | Zero-byte results with EINVAL, ENOMEM or EFAULT still return None, allowing probe failures to classify live processes as dead. The PRD permits only ESRCH or zero; the updated tests encode the incorrect fallback. | src/ovcaq/runtime/registry.py:183 | 3 | BOB |
| R4 | [1/3] | 🟡 | The new `_started` attribute exists only to carry a local from `run` into `_loop`. Pass `started` as a `_loop` argument instead. That removes the field, its reset in `run` and its `__init__` line. | src/ovcaq/runtime/supervisor.py:196 | 2 | ALICE |
| R5 | [1/3] | 🟡 | `process_identity` raises `CommandError(process_probe)` when `proc_pidinfo` returns 0 bytes with errno EPERM or EACCES. The spec says a zero-byte result means a pid the kernel does not know, so it must return None. The spec lists only three failure causes: a size other than 0 or 136, a pbi_pid mismatch, and a libproc load failure or non-darwin platform. A live pid the sandbox denies now makes `FleetRegistry.snapshot` and `process_matches` raise. Commit a12b659 added this branch. | src/ovcaq/runtime/registry.py:181 | Phase 0 task 1 | BLAKE |
| R6 | [1/3] | ⚪ | Extra changes beyond the spec. `_release_run` was extracted from `run`, a refactor for a function-length lint, in commit 186584f. `_PUBLISH_ERRORS` and `_ATTEMPT_ERRORS` tuples were added, which widen the caught exception set to include `AssertionError`, `RuntimeError` and `ValueError`. `_probe_process_identity` also catches `struct.error` and `OSError`. These look harmless and are needed to satisfy the hardening task, but the spec does not list them. | src/ovcaq/runtime/supervisor.py:96 | general | BLAKE |
| R7 | [1/3] | ⚪ | A first-attempt failure outside the caught set (`ConfigurationError`, `CommandError`, `_STATE_ERRORS`, `AssertionError`, `RuntimeError`, `ValueError`) would propagate uncaught. Examples are `KeyError` and `TypeError`. A fresh batch would then stay `running` with no supervisor. `_release_run` still tears down ownership. This is an uncovered residual, not a spec violation. | src/ovcaq/runtime/supervisor.py:398 | Phase 1 task 4 | BLAKE |
| R8 | [1/3] | ⚪ | `require_process_capabilities` is defined and widened to six facts, but nothing under src/ovcaq calls it. This predates the PRD. The spec does not require a caller. | src/ovcaq/runtime/capability.py:197 | Phase 1 task 1 | BLAKE |
| R9 | [1/3] | 🟡 | The `ConfigurationError` arm of `except (ConfigurationError, CommandError)` in `run` is now dead for anything `_loop` raises. `ConfigurationError` is a `ValueError`, so `_loop` catches it first. Drop it from the outer tuple and keep `CommandError`. | src/ovcaq/runtime/supervisor.py:211 | 2 | ALICE |
| R10 | [1/3] | 🟡 | The session-opened flag is set inside `_open_session`, right after `create_session` returns. The spec says to set it when `_open_session` returns. The earlier timing is safer. A `publish_session_metric` failure now takes the attention path, not the revert. The behaviour differs from the spec text, and the PRD does not document it. | src/ovcaq/runtime/supervisor.py:549 | Phase 1 task 4 | BLAKE |

### Gate corrections to the consolidator's output

- **R1, R9 and R10 were one merged row and are split here.** `consolidate_findings.py`
  merged `supervisor.py:398` (ALICE + BOB, the widened loop catch), `supervisor.py:211`
  (ALICE, the dead `ConfigurationError` arm) and `supervisor.py:549` (BLAKE, the
  session-opened flag placement) into a single three-voice row after suffix stripping — its
  own warning line names the merge. They are three different defects at three different
  lines. Split, the widened catch is genuinely two-voice (ALICE, BOB) and the other two
  are single-voice. Leaving the merge would have inflated consensus on R1 and hidden two
  findings inside another's text.

## Prior-cycle findings: verification

- **R11 (🟠, cycle 1) — resolved.** `_ATTEMPT_ERRORS` plus `self._started` route a
  first-attempt `OSError`, `AssertionError`, `ValueError` or `RuntimeError` with no
  session opened into `_abandon_attempt`, which reverts the fresh batch. Alice confirmed
  the two new tests (`test_supervisor_early_failure.py:167` and `:198`) fail against the
  old code.
- **R2 (🟠, cycle 1) — resolved as implemented, but the fix itself is now disputed.**
  `registry.py:179` zeroes errno before the call and raises `PROCESS_PROBE` on a zero-byte
  result with EPERM/EACCES; the new test at `test_process_identity.py:231` fails against
  the old code. BLAKE (R5 above) reads the same branch as a deviation from the PRD text.
  See the disposition of R3 and R5 below.
- **R3 (🟡, cycle 1) — resolved by the comment** at `supervisor.py:546`, which the finding
  allowed in place of a pinning test. BLAKE re-raises the underlying placement as R10.
- **R1 (🟡, cycle 1) — only partly resolved.** The comment landed; the requested
  `attention["detail"]` assertion did not. Re-raised as R2 above by both ALICE and BOB.

## Decision gate dispositions

**R3 (🟠) is discarded, with the PRD text as the refutation — not as a settled deferral.**
Its premise is "the PRD permits only ESRCH or zero". The PRD says the opposite
(`00062-supervisor-process-identity-v1.md:28-29`): `process_identity` returns `None` for
"a pid the kernel does not know (zero bytes returned)", and the four enumerated raise
causes are a returned size other than 0 or 136, a `pbi_pid` mismatch, a libproc load
failure, and a non-darwin platform. Errno is not among them. Beyond the spec reading, the
named errnos are unreachable at this call site: `registry.py:178-180` passes a
`ctypes.create_string_buffer(136)` with `PROC_BSDINFO_SIZE` as the length and
`argtypes`/`restype` pinned at `registry.py:162-169`, so EINVAL, EFAULT and ENOMEM would
all require a malformed buffer or size this code cannot produce. The finding names no
reachable path and asks the code to move further from the spec, so it is refuted rather
than deferred. This is the only 🟠 of the cycle; discarding it on verified grounds is what
leaves the cycle with no unresolved CRITICAL or HIGH.

**R5 (🟡) is discarded as single-voice, and recorded as a known deviation.** BLAKE is
right that the EPERM/EACCES raise is not in the PRD's enumeration — but it is exactly the
fix cycle 1's 🟠 R2 demanded and task 3 shipped with a test, and reverting it inside the
same PRD would re-open a finding the previous cycle closed. The honest statement is that
the implementation is one branch wider than the spec text: a zero-byte result whose errno
is EPERM or EACCES raises `process_probe` instead of returning `None`. That is fail-loud
behaviour for a denial the operator can act on, and it is the case this sandbox actually
produces. Ledgered so it is not re-argued, and visible here rather than silent.

**R4, R6, R7, R8, R9, R10 are discarded as single-voice** Medium/Low rows, each appended
to the ledger with that reason. R10 additionally matches cycle 1's settled R3.

**R1 and R2 (both two-voice 🟡) are swept.** Medium findings never block convergence, so they
go to the tail sweep rather than a third review cycle.

## Alice (consensus)

Ran `uv run --locked pytest tests/runtime tests/state -q`: 2654 passed. `ruff check
src/ovcaq/runtime tests/runtime` clean. No skips or xfails added. Verified R11 and R2 of
cycle 1 as genuinely fixed, with the fail-first direction checked against the old code for
each new test. Findings: R1, R2, R4, R9.

R1: pass
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
R13: pass

## Blake (blind, PRD-only)

Located the code from the spec alone. Ran `uv run pytest tests/runtime` (1682 passed) and
a narrow run of the preflight, early-failure, process-identity, capability and
supervisor-commands tests (235 passed); did not re-run the full suite, reading the staged
test-gate block instead. Findings: R5, R6, R7, R8, R10, plus one 🟠 and one ⚪ auto-dismissed
against the ledger (below).

Verified as meeting the spec: the libproc reader's constant, size, offsets, zombie handling
and token format; no `ps` spawn anywhere under `src/ovcaq`; `ErrorCode.PROCESS_PROBE` =
`process_probe` at exit 12; the six-fact doctor surface and its `ok: false` on a degraded
fact; `revert_batch_start`'s four preconditions and its reset to schema defaults;
`_cleanup_ownership_records` catching OSError and ValueError with `expected=`-guarded
registry removal; `CapabilityService.retry`'s membership check and usage envelope; the
no-production-required-capability premise; `process_probe` present in `docs/operations.md`,
`docs/state-protocol.md` and `CHANGELOG.md`; the `forbid_ps` autouse fixture; and every
acceptance test named in the spec existing, some in sibling modules.

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

## Bob (codex — doubt lens + de-slop)

Resumed codex thread `01a180d3`, so his cycle-1 critique is the baseline. Findings: R1, R2,
R3.

FIX:
- Incorrect errno fallback — src/ovcaq/runtime/registry.py:183 — Return None only for zero/ESRCH; otherwise raise process_probe with errno and strerror. Correct the tests.
- Missing R1 assertion — tests/runtime/test_supervisor_early_failure.py:228 — Assert `attention["detail"] == "attempt failed: kernel probe refused"`.
- Overbroad post-session catch — src/ovcaq/runtime/supervisor.py:398 — Preserve existing handling for state errors; propagate newly caught non-state errors after opening, or retain their original failure detail. Add a regression test.

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
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl (UI / frontend & design)

Unavailable — see the `carl:` line in the top matter. No UI/design voice has reviewed this
PRD in any cycle of either batch. The PRD touches no frontend, so the loss is low-impact
here, but the roster was three of four this cycle, never four.

### Auto-dismissed (ledger)

- [BLAKE] 🟠 `Supervisor.preflight` validates the build, review and done routes only when `boundary_decision` returns None. For a paused, attention-flagged or drained position it returns early and skips the route check. The spec requires all three routes to resolve on every run, and has no pause/drain carve-out. A misconfigured tier on a paused or drained batch still passes preflight, and `start_batch` can then run. The code also builds a modified snapshot with `pause_requested=False, attention=None` to compute this skip. | File: src/ovcaq/runtime/supervisor.py:158 — single-voice
- [BLAKE] ⚪ The spec names the attention path `_state_failure("supervisor.startup")`, but the code uses site `"startup"` throughout. The tests pin `"startup"`. The string `supervisor.startup` appears nowhere in the repo history I searched. This is a spec drift, not a regression. | File: src/ovcaq/runtime/supervisor.py:190 — single-voice

Both dismissals stand. The preflight route-validation skip was settled as single-voice in
cycle 1 of this batch and in both cycles of the earlier batch (`supervisor.py:152`,
`supervisor.py:155`, `docs/operations.md:61`), and the `"startup"` site string was settled
in the earlier batch at `supervisor.py:244`; neither settled reason has been shown to no
longer hold.

Verdict: 10 findings
Tests: 8280 passed, 3 failed, 14 errors (suite run this cycle; every failure and error in tests/integration/test_terminal_lifecycle.py from the sandbox /bin/ps denial)
