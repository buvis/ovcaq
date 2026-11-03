# Discovery: Workflow entry and PRD lifecycle ownership

## Classification

Depth: comprehensive | Date: 2026-10-19 | Status: open

## Problem

After `ovcaq init`, no OVCAQ command can make a PRD active. `workflow select`
only reports a name. `work.prd` is written by no production code, and it is a
protected path, so the only route is `ovcaq state set --unsafe work.prd`. No
command moves a PRD from `backlog/` to `wip/` or from `wip/` to `done/`. After a
successful `complete-prd` and `phase-complete --outcome drained`, the file stays
in `wip/` and `select` offers the same PRD again. The phase verbs accept work
that makes no sense: `phase-complete --outcome tasks_done` on a fresh idle batch
with no PRD moves the project into review. A refused `workflow stall` can leave
a recovery operation that no supported command can clear. Every test that
drives a lifecycle hand-writes `batch.*` and `work.prd` through the store, so the
suite never noticed. Without this, no stock agent can drain a batch through
OVCAQ, and cutover (PRD 00011) cannot start.

## Requirements

### Must have

- One OVCAQ verb enters a PRD: it selects (wip first, then backlog), moves the
  file backlog to wip with a verified move, sets `work.prd`, resets per-PRD
  fields, and commits all of it in one recoverable step. Replaying it after a
  crash at any boundary converges.
- One OVCAQ step closes a PRD: `complete-prd` (or the `done`/`drained`
  transition) moves the file wip to done with a verified move and records it in
  `batch.completed_prds`.
- `select` never offers a PRD already in `batch.completed_prds`.
- `phase-complete` refuses unless a batch is running and a PRD is active, with a
  usage error that names the missing precondition. `build -> drained` keeps its
  current meaning only when the queue is empty.
- `stall` and `park` validate that the PRD file is in `wip/` (or proven in
  `hold/`) before they stamp the recovery intent. A replay of an intent with a
  null artifact either rebinds the identity or aborts the intent cleanly.
- An operator can clear a stuck recovery operation through a documented verb
  that requires an explicit flag and writes a recovery record. It never needs a
  hand edit of `state.json`.
- `init`, `state`, `status`, `workflow`, and `run` resolve the state file
  through one resolver that honors `ovcaq.toml` (hold 00021).
- A test drives the installed wheel from `ovcaq init` to a drained batch where
  the fake agent changes state only through the `ovcaq` console script.

### Nice to have

- `workflow enter --dry-run` prints the selection, the move, and the state
  diff without changing anything.
- `status` shows the active PRD, phase, and batch status.

### Out of scope

- Wave and lane execution (several PRDs in parallel). See discovery 00007.
- Design, catchup, and budget steps from the legacy Phase 0 chain. See 00007.

## Constraints

- One state writer: every change goes through `StateStore.transaction`.
- File moves follow the existing saga pattern in `workflow/records.py`: durable
  intent, verified move, commit, then marker cleanup. No new saga framework.
- Workflow modules stay pure and provider-neutral; no `claude`/`codex` strings.
- No legacy alias names (`enter.py`, `statectl`) as public commands.

## Codebase Context

- **Relevant code**: `src/ovcaq/workflow_cli.py:290-294` (`select` returns and
  commits nothing); `src/ovcaq/workflow/selection.py:34-60`;
  `src/ovcaq/workflow/transitions.py:80-93` (`apply` checks only recovery idle
  and the transition table); `src/ovcaq/workflow/records.py:178` (`complete_prd`,
  no file move), `:494-521` (`_prepare_operation` builds `artifact: None`),
  `:524-562` (`_begin_operation` stamps the intent even when the PRD is in
  neither bucket), `:69` (`require_recovery_idle`); `src/ovcaq/state/commands.py:66-69`
  (protected paths); `src/ovcaq/config.py:244-251`, `:344-351`, `src/ovcaq/cli.py:475`,
  `src/ovcaq/paths.py:151` (three state-file resolvers).
- **Conventions**: compound mutations live in `state/commands.py` or
  `workflow/records.py` and are exposed through `workflow_cli.py`; tests mirror
  the package (`tests/workflow/`, installed-wheel tests in `tests/packaging/`).
- **Integration points**: the external run-autopilot skill calls these verbs;
  the supervisor reads `work.prd` and `next_phase` in `runtime/decision.py`.
- **Similar implementations**: legacy `claude-autopilot`
  `skills/run-autopilot/cli/enter.py` (added 2026-09-29, after OVCAQ's August
  characterization). Its `_select` (line 184) does the verified backlog to wip
  move, and `_write_prd` (line 267) sets `prd` and the frontmatter fields. The
  wip-to-hold saga in OVCAQ `records.py` is the pattern for the new moves.

## Approach

- **Chosen**: OVCAQ owns PRD identity and bucket moves. Add a `workflow enter`
  verb (select, verified move, set `work.prd`, reset fields) and extend
  `complete-prd` with the verified wip-to-done move, both on the existing saga.
  Add preconditions to `transitions.apply`. Fix the stall intent order.
- **Why**: state decides, prose does not (architecture invariant 2). If the
  agent moves files, OVCAQ state and the filesystem can disagree with no owner.
  The legacy runtime already moved this into code for the same reason.
- **Rejected alternatives**:
  - Keep moves in the external skill and document `state set --unsafe`: makes
    an unsafe recovery tool part of the normal path and repeats the bug class.
  - Let `select` commit as a side effect: a read verb that writes surprises
    callers and breaks `--dry-run` style use.

## Success Criteria

- Installed wheel, fresh project: `init`, `enter`, phase verbs through
  `drained` leave the PRD in `done/`, `batch.status` completed, and no
  `--unsafe` call anywhere in the test.
- The reproduction from the 2026-10-18 review (stall with the PRD in backlog)
  either refuses with no state change or recovers through a supported verb.
- `phase-complete` straight after `init` exits non-zero and changes nothing.
- One resolver: with `[workflow] runtime_root = "rt"`, `init`, `state get`,
  `status`, and `workflow resume-target` agree on the same file.

## Risks

- **Saga regressions**: the stall saga has a large failpoint matrix. Add the
  new moves with the same boundary hooks and extend the matrix, do not fork it.
- **Contract change for the external skill**: the run-autopilot skill must call
  `workflow enter` instead of moving files. Ship the verb first, then change
  the skill in the cutover work (00011).
- **Resolver unification changes paths for existing projects**: no OVCAQ
  project is live yet, so fresh state is acceptable (discovery 00001 Q8).

## Open Questions

- Should `enter` also stamp `work_start_sha` and frontmatter-derived fields, as
  legacy `enter.py` does at step 8.5 and step 10, or should those stay in
  `workflow frontmatter`?
- Does `build -> drained` stay legal, or does an empty queue become a
  boundary decision only?

## Discovery Log

### Q1: Who owns PRD activation and bucket moves?

**Answer**: Derived from the 2026-10-18 readiness review and the legacy code.
OVCAQ, because the legacy runtime moved the same steps from prose into
`enter.py`. Confirm when promoting to a PRD.

### Q2: Is a stuck recovery operation acceptable as a hand-edit case?

**Answer**: No. Architecture invariant 1 forbids direct `state.json` edits, so
recovery needs a verb.
