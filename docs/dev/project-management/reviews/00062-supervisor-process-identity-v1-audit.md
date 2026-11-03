# Decision Audit Log: 00062-supervisor-process-identity-v1

PRD: `00062-supervisor-process-identity-v1.md`
Started: 2026-10-28T05:43:53Z
Completed: 2026-10-28T05:43:53Z
Autonomous: 14  |  Deferred: 0  |  Doubts: 0

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: PRD 00062's first pass already landed on master during the earlier batch 202610251552, so state.work_start_sha had no value for this PRD and capturing the current HEAD would have scoped the review diff to the single remaining correction.

**Choice**: Pinned state.work_start_sha to 02c391de (parent of fa26fb7, PRD 00062's first commit) instead of the current HEAD 0f18ef1, so the review diff 02c391de..HEAD covers the PRD's whole work range.

**Rationale**: Capturing HEAD would have shown Alice and Blake a diff holding almost none of the PRD's implementation, so they would have reported the already-satisfied requirements as missing. This follows the documented recipe in project memory false-park-auth-revoked: pin work_start_sha to the commit before the PRD's first commit so the review covers the pre-park work. Caveat for the review session: no range covers 00062's commits plus this session's new ones without also including PRD 00057's, which landed after 00062's and already converged in this batch. Treat src/ovcaq/workflow_client.py, src/ovcaq/config.py, tools/autopilot-prerequisites and tests/workflow_client as already-reviewed out-of-scope context, not scope creep.

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: R11: early-failure revert covers only ConfigurationError and CommandError at supervisor.py:204, so an OSError from create_session in the first _open_session leaves a fresh batch running with no supervisor

**Choice**: overrode the ledger auto-dismissal and the single-voice discard rule; reinstated as a rework fix task

**Rationale**: the ledger matched it to a cycle-1 entry at supervisor.py:190 about _PUBLISH_ERRORS, a different leg of run() with a different exception tuple, and that entry's recorded reason was a bare single-voice discard rather than a refutation. The gate verified the claim directly against the code (_STATE_ERRORS at supervisor.py:93 includes OSError, the narrow catch at line 204, and _loop's except _STATE_ERRORS at 387-388 which performs no revert). Discarding it would ship a verified hole in the PRD's own 'early failure returns a fresh batch to idle' success metric

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: R3 and R4 both report the _session_opened flag placement at supervisor.py:533 but consolidate_findings.py left them as two [1/3] rows

**Choice**: treated as one finding carried by two voices (ALICE and BOB) and routed to a rework fix task instead of discarding each as single-voice

**Rationale**: the two rows name the same file and the same line and describe the same defect in different words; the single-voice rule is a noise filter for a defect only one reviewer saw, and applying it to a merge miss would discard a two-voice finding

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: R2: process_identity returns None on a zero-byte proc_pidinfo result even when errno is EPERM/EACCES, so a denied live process reads as dead and can be pruned

**Choice**: classified as an additive auto-fix and routed to rework rather than deferred as a requirements ambiguity

**Rationale**: the PRD's Outputs text only covers 'a pid the kernel does not know (zero bytes returned)' and never mentions errno, so this is a spec gap rather than code contradicting the spec. The PRD's own Risks section states the intended behavior is to surface process_probe instead of pruning live entries as dead, and registry.py:153 already passes use_errno=True while no branch ever reads errno, so the errno distinction was set up and left unused. The fix adds an errno branch and tests without changing any signature, and cycle 1 of 2 leaves a rework cycle available

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: Nine findings and mechanical replay rows target src/ovcaq/workflow_client.py and tests/workflow_client, which belong to PRD 00057

**Choice**: discarded as out-of-scope reviewed context, recorded in the per-PRD ledger

**Rationale**: state.work_start_sha 02c391de spans PRD 00062's whole work range, and because 00062's first pass landed in the earlier batch while 00057 was completed in between, the range also carries 00057's already-converged commits. Those files are not this PRD's surface and 00057 passed its own three review cycles; the fail-first replay rows against them are an artifact of replaying 00057's tests against a base that predates 00057

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: The session-opened branch deviates from the PRD helper with no code comment saying why. The tests assert only `attention["detail"].strip()` and `site == "startup"`, so swapping `_attention_notice` for `_state_failure` would pass. Pin `attention["detail"]` as `attempt failed: kernel probe refused` in `test_failure_after_session_opened_never_reverts`. Add a one-line comment that the generic `_state_failure` text would mislabel a probe or route failure as a state failure.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: A zero-byte probe returns None even for EPERM/EACCES, so denied live processes appear dead and can be pruned. The PRD explicitly requires a process_probe error for these cases.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: `_session_opened` is set after `create_session` rather than at `_open_session`'s return as the PRD specifies, and no test pins that placement. A refactor to the PRD placement, or to before `create_session`, would pass every test. Add a test where `publish_session_metric` raises `CommandError` after the session directory exists and assert the batch stays running with attention, or add a comment at supervisor.py:533 saying "session exists on disk, so never revert". BOB, independently: `_session_opened` becomes true before `_open_session` returns, contrary to the required boundary; a partial opening can therefore set the flag.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: Early-failure revert covers only `ConfigurationError` and `CommandError` from the loop. `_loop` catches `_STATE_ERRORS` (including `OSError`) and returns `_state_failure("supervisor.loop")` with no revert. An `OSError` from `create_session` inside the first `_open_session`, before `_session_opened` is set, therefore leaves a fresh batch `running` with no supervisor, which is the bug this task targets. A bare `AssertionError` from `assert identity is not None` in `_open_session` (src/ovcaq/runtime/supervisor.py:520), or any other `ValueError`/`RuntimeError` from the first attempt, escapes `_abandon_attempt` the same way.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: R3 (high): zero-byte proc_pidinfo with EINVAL/ENOMEM/EFAULT returns None (registry.py:183)

**Choice**: discarded - contradicts computed/spec facts

**Rationale**: PRD 00062:28-29 requires None for a zero-byte result and enumerates four raise causes that exclude errno; the call site passes a fixed 136-byte buffer with pinned argtypes, so EINVAL/EFAULT/ENOMEM are unreachable. Refuted, not deferred.

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: Consolidator merged three distinct findings at supervisor.py:398, :211 and :549 into one [3/3] row (cycle 2)

**Choice**: split into R1, R9 and R10 at the gate

**Rationale**: suffix stripping merged three different defects at three lines; the merge inflated consensus on the widened-catch finding and hid two others inside its text

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: R5 (medium): the EPERM/EACCES raise in process_identity is one branch wider than the PRD enumeration (registry.py:181)

**Choice**: discarded as single-voice, recorded as a known deviation

**Rationale**: the branch is the fix cycle 1's high-severity R2 demanded and task 3 shipped with a test; reverting it inside the same PRD would reopen a closed finding. Deviation stated plainly in the review file and the ledger.

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: `_loop` now catches `ValueError`, `RuntimeError` and `AssertionError` for every attempt. Once a session has opened, these go to `_state_failure("supervisor.loop")`, which writes the generic "Supervisor state operation failed" text, and the original error is dropped with nothing logged. Before the rework they surfaced as a traceback. `ConfigurationError` subclasses `ValueError`, so it takes the same path. A later-session route error used to reach `_abandon_attempt` and record "attempt failed: <message>", and it now gets the generic text. Limit the widened catch to the not-yet-opened case (re-raise when `self._session_opened`), or put the error text into the attention detail. No test pins the session-opened behaviour for these exception types.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-28T05:43:53Z

**Decision**: The cycle-1 R1 test pin is still missing. `test_failure_after_session_opened_never_reverts` asserts only `attention["detail"].strip()` and the site, so replacing `_attention_notice` with `_state_failure` still passes. Assert `attention["detail"] == "attempt failed: kernel probe refused"`. The new comment sits inside the `except _STATE_ERRORS` fallback and reads as if it explains that fallback. Move it to the `_attention_notice` call it justifies.

**Choice**: auto-fixed

**Rationale**: fixed by review-close
