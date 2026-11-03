# PRD 00008 — prompt-overrun recovery 1

The installed run-autopilot Phase 0 `enter` returned `stop: replan`;
`resume-target` confirmed `subagent_prompt_overrun` recovery for old task 12.
The repair prompt measured 51,332 bytes initially and 50,185 after its single
allowed trim. Neither repair was dispatched. This session performed recovery
only and changed no product code.

Before `tasks-clear`, all ten unfinished task records were checked for exact
JSON equality with the [recovery snapshot](00008-tui-python-launcher-v1-recovery-1.md).
That snapshot, its raw Pat verdicts, and all ten completed task names were
preserved in `autopilot/replan-context.md`. The new planning budget is 75,000
tokens per task; the separate assembled-prompt ceiling remains 50,000 bytes.
The 53,890-byte context is for the planner, not a whole subagent prompt.

The state CLI cleared tasks/counts, cleared stale rework IDs and the abort
marker, set `replan_count=1`, and set both phase fields to `build`, as prescribed
by `references/recovery.md` steps 4–6. No `phase-done` outcome models abort
recovery; none was called. Batch `202609062243`, cycle 1, cap 2, review history,
and base `1f500258065d431de41102dcc64f8d43d07ac44f` are retained.

Completed implementation to preserve:

- Old task 1: bounded JSONL tailing and shared metric/evidence readers.
- Old task 2: identity-bound fleet discovery.
- Old task 3: provider-neutral project projections and core panels.
- Old task 4: post-drain capability status and retry evidence.
- Old task 5: exact-run controls and Textual navigation.
- Old task 6: OVCAQ branding and theme persistence.
- Old task 7: raw-only and unknown-provider degradation.
- Old task 8: Python launch, attach and resume lifecycle.
- Old task 9: plain-renderer fallback.
- Old task 10: terminal lifecycle and provider-neutrality integration tests.

These completed entries do not close later findings. Old task 11 still needs
real-adapter identity normalization and evidence-status typing; old task 12
still needs exact ended-owner attribution, noninterfering observation and
active-evidence-window checks. Old tasks 13–20 retain their full requirements.
Replanning must preserve coverage and remap dependencies to the new IDs.

Verification: pre-reset schema/count consistency passed (10/20); historical
review 1 passed the CLI artifact gate with the Codex-rung guard. Its Alice R,
Blake B and Bob D verdicts remain in their respective raw sections. The review
applies to `5544b1fc9c27838f8941c2266867a6c34ef10902`, not the repaired tree.
No product tests were rerun for this recovery-only session. Existing tests and
remaining limits are recorded in the [rework evidence](00008-tui-python-launcher-v1-rework-1.md).
Post-reset schema/counts, preserved batch/base/cycle/cap, complete unfinished
snapshot, contract-card equality, raw rubric verdicts, Bob receipt presence,
the review artifact gate with `--assert-constraint-met`, and `git diff --check`
all passed. `resume-target` now reports `build: catchup then planning`.
Full product gates and a fresh post-repair review remain required.

The recovery procedure ends this session and hands planning to a fresh build
process. Codex remains coordinator; Claude retains the authorized external
dispatch and doubt-review roles.
