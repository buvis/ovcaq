# PRD 00004 cycle 15 — interactive failure diagnosis

## Failure Capture
- Session / task: autocodex review session `ce1b29877e7e4601a7074c259598923f`; PRD `00004-workflow-core-v1.md`, cycle 15.
- Goal in progress: converge workflow-core review after the task 7/8 ancestry repairs.
- Error: committed `pause_reason.site=data_loss_risk`; phase and next phase both `paused`.
- Last successful step: review final audit and `turn.completed`; Alice, Blake and external Claude Bob completed. The recorded full suite passed 1,364 tests.
- Last failed tool / command: no terminal tool failure; the separate installed-wheel probe returned success on both direct append and exact replay after an ancestor replacement without confirming the replacement entries with fsync.
- Repeated pattern seen: cycles 13–15 successively exposed gaps in ancestor confirmation; current runtime-only identity verification misses reparenting that preserves the runtime inode.
- Context pressure: no context-overflow failure recorded at session end; repeated fresh recovery/review sessions remain a time/token cost.
- Environment assumptions to verify: HEAD `7b41798c80e06a2c341d75116a09c752203797f4`, clean worktree, exact installed-wheel source match, correct repo state, no live worktree owner.

## Recovery Action
- Diagnosis chosen: application durability defect plus an intentional workflow safety pause. The driver received a completed review session.
- Smallest action taken: read the host contract, installed run-autopilot skill, build-gate resume procedure, recovery reference, committed state, cycle-15 report, source and probe. The canonical `resume-target` returns `paused: await user`.
- Why this is safe: diagnosis uses existing evidence and an isolated temporary-filesystem probe. It does not clear the pause, modify production code, change the cap, or run a review cycle.
- What evidence would prove the fix worked: both reparenting cases refuse with a path-specific retryable identity error, or confirm the replacement ancestry before returning success; installed-origin assertions and immediate/distant ancestor coverage pass; full gates and a subsequent fresh review pass.

## Concrete recovery proposal
1. Authorize the two existing queued tasks, 9 and 10, as one bounded recovery attempt.
2. Task 9: preserve and validate the confirmed ancestor chain throughout publication/replay, restore contextual deferred-directory errors, and distinguish parent/child identity names.
3. Task 10: restore installed-origin assertions on every subprocess result/event and immediate-parent coverage, preserve the new reparenting regressions, and consolidate duplicate test flows.
4. Use the installed state CLI for the authorized build transition; preserve batch `202609062243`, all 18 completed tasks and their attempts, cycle 15, cap 2, and the original PRD base.
5. Complete repairs and required gates in a work session, then hand off and end that session before the next complete Alice/Blake/Bob review. Do not waive findings or declare the PRD complete.

## Agent Self-Debug Report
- Session / task: interactive diagnosis of cycle-15 pause.
- Failure: direct/replay ledger success after ancestor replacement with no later parent fsync.
- Root cause: `_ensure_directory_chain` discards earlier ancestor identities; later verification retains only the runtime inode, which survives reparenting.
- Recovery action: prepared the bounded task 9/10 proposal and reran the existing probe in a fresh isolated wheel installation. Both direct append and exact replay reproduced success after ancestor replacement, with the runtime inode preserved and no subsequent fsync of the replacement ancestor or its parent. The probe verified installed origin and exact source hash. Evidence: `00004-cycle-15-interactive-reparent-probe.json`.
- Result: partial — diagnosis complete; operator recovery decision remains required.
- Token / time burn risk: repeating the same review without addressing the whole ancestor chain will consume another long session; the repeated “codex running” lines are heartbeat output, not evidence of a stuck tool.
- Follow-up needed: explicit authorization to execute the queued repairs and resume from this safety pause.
- Preventive change to encode later: retain the real same-inode reparenting probe as an installed-wheel regression with chronological fsync assertions.

Validation: installed state schema passes; phase/next phase remain paused, tasks remain 18/20 complete, pending IDs are 9/10, cycle remains 15 and cap remains 2. There is only the main worktree and branch; the probe cleaned up its temporary directories. No production edits or workflow-state mutations were made. No physical power loss or actual user-data loss was demonstrated.

The approval requirement is explicit in `/Users/bob/.config/autocodex/host.md` (Interactive recovery: unattended wording does not authorize clearing a pause or starting repairs). The installed run-autopilot `SKILL.md:300` mandates “Detected data-loss risk” → “PAUSE”; its resume procedure requires the operator decision. This is not an inference that ordinary reversible bug fixes always need approval.

## Operator response

The operator subsequently answered **yes** to the two queued repairs and a fresh full review. See `00004-cycle-15-recovery-authorization.md` for the authorized scope and fresh-work handoff. The defect remains open until those repairs and verification finish.
