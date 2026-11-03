# PRD 00005: authorized recovery for tasks 12–21

## Operator decision

On 2026-09-15 the operator replied **“ok, proceed”** to the proposed recovery:
authorize interactive recovery and existing repair tasks 12–21, start with F50,
keep the review cap at 2, and preserve the complete review process.
This resolves the authorization pause, not the defects. This session prepares
a fresh work session; it performs no implementation or completion review.

Read `/Users/bob/.config/autocodex/host.md` and the installed
`/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.2/skills/run-autopilot/SKILL.md`.
The host requires the authorized state update and a session boundary before
restarting `autocodex`.

## Preserved starting point

- PRD: `dev/local/prds/wip/00005-runtime-substrate-v1.md`.
- HEAD: `e34547e734339e31bcba89e26b3fd3cd58e99690`; tracked worktree clean.
- Work base: `2742c08fe5f8194f65a36fa1e49a5980d69c16ef`.
- Batch: `202609062243`; cycle/cap **1/2**; tasks **11/21** complete.
- Tasks 1–11 remain complete; tasks 12–21 remain pending with original bodies,
  tiers, and findings. Review 1, complete rubrics, Claude Bob receipt/raw hashes,
  state schema/counts, and enforcement plugin pins verified.

F50 remains open: the current `apply_purge` source locks mutable absolute paths
after opening the runtime directory. The saved synthetic root-swap proof deleted
active evidence while its original run lock stayed held. The reproduction used
only temporary synthetic files.

## Next work session

Committed `phase`/`next_phase` are `build`; `resume-target` must report
`/work continues at first non-completed task 12`. Read the PRD, existing design,
coverage manifest, and authoritative task descriptions. Resume the installed
work skill in rework mode with `rework_task_ids` **12–21 in order**. Do not
recreate tasks, repeat selection/design/planning or review 1, recapture the work
base, or start PRD 00006. The operator decision above supersedes the task bodies'
pre-recovery authorization warnings for this scope.

### Phase 5 scope decisions

| Task | Approved scope and constraints |
|---|---|
| 12 | F50 first: bind purge locks and deletion to the same verified ancestry. Bound aggregate reads, preserve malformed rows, and avoid repeated partial-write copies. |
| 13 | Secure fleet roots, locks, entries, and prune against substitution; retain private permissions and the project lock's authority. |
| 14 | Keep process ownership through descendant cleanup; fix watchdog completion and signal exits. Merely documenting a leak is insufficient. Test unrelated processes. |
| 15 | Enforce configured-path containment. Verify F12 against the PRD's resolved-root requirement AND the design's explicit symlink rejection. Do not broadly resolve away unsafe configured symlinks or relax security based on reviewer prose. |
| 16 | Preserve descriptor-relative session publication and the existing versioned schema, UTC timestamps, basename IDs, and containing-session identity. |
| 17 | Reconcile shared lock/process/metadata/fleet facts and add required doctor resource checks. Verify observation contention with real processes; do not adopt the untested F_GETLK suggestion. |
| 18 | Correct diagnostic payloads, exact purge argv, and ignored logs options. Follow the PRD's status/doctor preview requirement using the existing purge representation and stable top-level envelopes; no unrelated error-code/API expansion. |
| 19 | Provide owner-checked ephemeral cleanup required by the substrate PRD, without building the future supervisor loop or deleting persistent locks/retained evidence. |
| 20 | Preserve concurrent emergency evidence, bound decoding, and report the archive path. A same-account timing argument does not resolve the marker race. |
| 21 | Fix verified size/complexity problems and weak rejection assertions only in changed code; retain interfaces, safety properties, and an accurate changelog. |

There are exactly ten follow-ups, below the greater-than-ten scope alarm, and
cycle 1 is below cap 2. Critical fixes have explicit operator authorization.
Protocol C/D evidence is the local PRD/design's existing containment, ownership,
versioned evidence, completion, and diagnostics contracts. No new dependency,
durable schema, future lifecycle policy, or unrelated error contract is approved.
Per-finding decisions are retained in `00005-cycle-01-recovery-decisions.json`
and appended through the state CLI to `autonomous_decisions`.

All recorded discards and settled deferrals remain. F27 new error codes, F43
corrupt-log tolerance, F45 multiple-failure accumulation, and F46 inventory
performance policy stay deferred. No finding is declared fixed by authorization.

## Completion boundary

Run every mandated work step at its selected tier, including test authoring,
adversarial checks where required, implementation, per-task review, and final
verification. Retain the host's model/role mapping. Use meaningful race
regressions and real process/lock tests; run full pytest, Ruff lint/format, mypy,
and build. Prior passing tests at the unchanged HEAD are not repair evidence.

After ALL repairs pass, run canonical `phase-done --outcome tasks_done`, then
`phase-done --outcome rework`. The second transaction advances cycle to **2**
and clears `rework_task_ids`; cap stays **2**. Do not increment before repairs
finish. Write the handoff record/card and **END the work session**. A fresh
session runs cycle 2 with isolated Alice consensus, isolated Blake PRD-only
blind review, and fresh external Claude Bob doubt/de-slop, complete rubrics and
receipt. Never review repairs from their work session.

## Recovery mechanics

This is not a cap pause. The installed transition table has no paused-recovery
outcome, so this bounded Resume uses supported state CLI field operations,
keeping `pause_reason` until the queue, phase pair, decision records, and card
are ready. Recovery adds no fictitious attempt or completed-phase record.

Evidence: `00005-cycle-01-resume-before.json`,
`00005-cycle-01-resume-preflight.json`, and `00005-cycle-01-resume-audit.json`.
Original review artifacts remain unchanged. No project tests are rerun for
this state-only recovery. Restart with **`autocodex`** from the repository root;
this recovery session ends without launching it.
