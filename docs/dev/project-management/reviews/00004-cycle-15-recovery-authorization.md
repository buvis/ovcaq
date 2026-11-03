# Cycle 15 recovery authorization and fresh-work handoff

The operator answered **yes** to: “Authorize queued tasks 9–10 to fix ancestry verification and regression coverage, then hand off to a fresh full review?” This explicitly authorizes the existing two repair tasks and the associated work/review gates. It does not waive findings, raise the cap, reset history, or authorize completion without review.

## Resume contract

- PRD: `dev/local/prds/wip/00004-workflow-core-v1.md`.
- Reviewed HEAD: `7b41798c80e06a2c341d75116a09c752203797f4`.
- Batch: `202609062243`; original work base: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`.
- Preserve cycle 15 and cap 2 during recovery preparation; retain all 18 completed tasks and their attempts. Queue existing tasks 9 and 10 in `rework_task_ids`; task 10 depends on task 9.
- The fresh build session must read the resolved autocodex host contract, installed run-autopilot build gate, and work skill including its rework-mode reference. Preserve task 9's `opus` and task 10's `sonnet` logical tiers, subject to the source's ordinary routing requirements and host mappings.
- Treat the authorization above as satisfying the pending tasks' “do not execute until operator authorizes” precondition. Their original findings and acceptance criteria remain unchanged.
- Task 9 repairs full ancestry verification, contextual deferred-directory diagnostics, and parent/child identity naming. Task 10 restores every-result/event installed-origin proof and immediate-parent coverage, consolidates duplicate test flows, and removes unused capability fields. Both tasks' complete descriptions in state remain authoritative.
- Run all skill-mandated task steps and the repository's complete verification gate. Retain direct/replay, same-inode reparenting, immediate/distant ancestors, search-only access, state/backup bytes, chronological fsync, exactly-once, and installed-wheel evidence. The full suite has **not** been rerun during this authorization session.
- After both tasks and work gates complete, use `phase-done --outcome tasks_done` for build → review, then `phase-done --outcome rework` to apply the completed-rework cycle increment and clear `rework_task_ids`. This prepares cycle **16** with cap **2**, without overwriting cycle-15 review evidence. Write the contract card/handoff and **end the work session**. No review lens runs in that work session.
- The next fresh review must run Alice, Blake, and external Claude Bob with every required rubric and receipt. Do not defer the reproduced data-loss risk merely because cycle exceeds cap, or equate operator permission to repair with permission to waive future findings.

## Evidence

- `dev/local/reviews/00004-workflow-core-v1-review-15.md`
- `dev/local/reviews/00004-cycle-15-interactive-diagnosis.md`
- `dev/local/reviews/00004-cycle-15-interactive-reparent-probe.json` — both installed-wheel cases reproduced the defect at the reviewed HEAD.

The installed transition table has no `paused` → `build` outcome. Authorized recovery therefore uses the installed `cli.statectl.mutate` boundary for one locked, validated transaction containing the approval record, rework task filter, phase/next phase, pause removal, and contract card. Ordinary completion transitions above continue through `phase-done`; no plugin or production code is changed here.

## Verified handoff result

Authorization was committed through the installed writer while holding the autocodex ownership lock. State schema validation passes; the canonical `resume-target` now returns `/work continues at first non-completed task 9`. Phase/next phase are `build`, rework IDs are `9,10`, and the pause marker is cleared. Only the six intended fields changed; tasks, attempts, batch, base, cycle 15, cap 2 and all review history are preserved. The old pause reason survives in the authorization decision and pre-transition backup. The contract card matches state, the leave telemetry was recorded, and the tracked worktree remains clean. This session performed no repairs; the next work session owns them.
