# Discovery: Legacy runtime drift since characterization

> Historical assessment. The 2026-10-25 three-layer redesign supersedes earlier ownership conclusions: Autopilot/controller owns workflow truth, OVCAQ owns execution, Tower owns presentation. Preserve the source observations; use the current design and PRDs for implementation.

## 2026-10-25 ownership decisions

The user reaffirmed this boundary; the earlier two-backend proposal is superseded. [Corrected contract design](../designs/autopilot-optional-supervision.md) is the active mapping. The historical proposal/questions below remain evidence, not unresolved permission to duplicate the runtime.

| Cluster | Decided disposition | Owner |
| --- | --- | --- |
| Entry/selection/eligibility/frontmatter and PRD moves | port | OVCAQ 00057 |
| State/task/attempt persistence and typed mutation API | port | OVCAQ 00058 |
| Code-owned effort lanes and durable custody/review/verification | port / external-via-verb | OVCAQ 00059 |
| Loop/handoff/markers/brief/metrics/processes/TUI | port | OVCAQ 00060 |
| store_tree recorder and scoped post-phase git commits | port; ignored stores no-op, no forced tracking | OVCAQ 00060 |
| Waves/worktrees/review slots/assembly/landing | port as advanced capability, required for full replacement | OVCAQ 00061 |
| review_stage and review_close content preparation; custody/cap semantic classification | external-via-verb | Plugin 00013/00016; OVCAQ 00059 commits |
| rework_groups/findings_section/gate_lead/catchup_probe | external | Plugin 00013/00015 |
| verification execution/reuse calculations, dirty_tree/log_sink checks | external-via-verb; artifacts local, acceptance/persistence runtime-owned | Plugin 00013/00016; OVCAQ 00059/00060 |

The checked inventory must still expand these clusters into one row per module and changed behavior, including mixed-module splits and new source changes. Held cutover PRD 00011 explicitly requires that evidence. No retirement is newly authorized. Local plugin skills produce artifacts; they never own a workflow state tree or queue. Real artifact/contract exchange is tested at plugin 00016, not required to begin OVCAQ 00058.


## Classification

Depth: comprehensive | Date: 2026-10-19 | Status: open

## Problem

OVCAQ ported the personal run-autopilot runtime as characterized on
2026-08-25. The legacy runtime kept moving: `skills/run-autopilot` in
`buvis/claude-autopilot` has 1,040 commits since that date, and at least 34
new runtime modules (about 11,000 lines) appeared after it. PRD 00011 (personal
cutover) assumes OVCAQ already matches the legacy behavior and only needs
canaries and removal. That premise no longer holds. Cutting over today would
silently drop behavior the operator now relies on, such as Phase 0 entry,
code-decided effort lanes, waves, review staging, and test-gate reuse. Each
new module needs an explicit decision: port into OVCAQ, keep in the external
skill but route its state writes through OVCAQ, or retire.

## Requirements

### Must have

- A drift inventory: every legacy module and behavior added or changed since
  2026-08-25, each with one disposition (`port`, `external-via-verb`,
  `external`, `retire`) and an owner discovery or PRD.
- Every `external-via-verb` item gets an OVCAQ compound verb, so the skill
  never writes `state.json` directly (architecture invariant 1).
- PRD 00011's acceptance gains a parity check against the drift inventory.
- A freeze rule: new legacy runtime features after the inventory date land
  with an OVCAQ disposition in the same change, or wait until cutover.

### Out of scope

- Re-characterizing behavior unchanged since 2026-08-25.
- Porting review-lens content (personas, prompts, rubrics). It stays external.

## Constraints

- External capabilities stay external (invariant 6): review personas, prompts,
  and skill prose never move into the package.
- Provider-neutral core: lane, wave, and verification logic enters OVCAQ only
  without provider strings.

## Codebase Context

First-seen dates are the first commit of each file in `claude-autopilot`.
Proposed dispositions are a first pass for the inventory, not decisions.

| Legacy module | Since | Purpose | Proposed disposition |
| --- | --- | --- | --- |
| `enter.py`, `enter_io.py` | 09-29, 10-04 | Phase 0 step chain: bootstrap, park, stall stops, custody, select and move, stamp, catchup, design | `port` (selection and move: discovery 00003); remaining steps per row below |
| `records_park.py` | 10-13 | Phase 0 park-request handler | `port` (compare with OVCAQ `park`) |
| `eligibility.py` | 08-26 | PRD `eligibility:` gate at pick time | `port` into `workflow/selection.py` |
| `handoff.py`, `markers.py`, `handoff_request.py` | 09-14, 10-15, 09-26 | Session marker cleanup at lifecycle commits; usage-cap handoff warning | `port` into runtime |
| `loop_decision.py`, `loop_act.py`, `loop_gates.py` | 09-15 | Split loop driver: decision table, drained-path acts, preflight gates | `port` (diff against `runtime/decision.py`) |
| `convergence.py` | 09-14 | `review_converged` metric row | `port` into metrics |
| `brief.py` | 09-20 | Session brief rendered from state | `port` (state-derived render) |
| `lane.py`, `lane_check.py` | 09-20 | Code-decided effort lane (solo, fast-track, full) and escalation | `port` into routing policy |
| `triage.py` | 09-20 | Mint hold stubs for unowned deferred findings | `port` into workflow records |
| `store_tree.py` | 10-01 | Commit the record store after each phase, scoped to its pathspec | `port` (needs a records-commit policy) |
| `procinfo.py` | 10-13 | Process facts without `ps` | `port` (discovery 00004) |
| `verification.py`, `dirty_tree.py`, `log_sink_refusal.py` | 10-04, 10-15, 10-16 | Run the test gate once and reuse its record | decide: core capability or `external-via-verb` |
| `wave.py`, `wave_launch.py`, `wave_run.py`, `wave_review.py`, `wave_assemble.py`, `wave_slots.py` | 09-26 to 09-29 | Parallel PRD lanes, assembly branch, assembly review | decide: in or out of cutover scope |
| `review_stage.py`, `review_close.py` | 10-04 | Stage review inputs; apply a classified review to state | `external-via-verb` (needs an OVCAQ review-close verb) |
| `custody.py`, `cap_check.py` | 09-13, 10-15 | Cap-critical custody; regression classification across rework | `external-via-verb` |
| `rework_groups.py`, `findings_section.py`, `gate_lead.py` | 10-03, 10-13, 10-17 | Review findings parsing and rework task grouping | `external` |
| `catchup_probe.py` | 10-13 | gh and engram probe for catchup | `external` |

- **Integration points**: the run-autopilot skill and its `__main__.py` verbs
  are the callers to retarget at OVCAQ; `docs/dev/project-management/prds/hold/00011-personal-cutover-v1.md`
  holds the canary and removal plan.
- **Similar implementations**: the August characterization inventory and
  migration map (now kept in the private test archive) are the pattern for the
  drift inventory format.

## Approach

- **Chosen**: build the drift inventory as a checked file with one row per
  module and behavior, then promote each `port` cluster to its own PRD before
  00011. Treat waves as a scope decision, not a default port.
- **Why**: the August method (inventory, dispositions, owner per row) caught
  gaps mechanically; repeating it is cheaper than finding gaps in canaries.
- **Rejected alternatives**:
  - Cut over now and port gaps later: the legacy runtime is deleted at cutover,
    so lost behavior has no fallback.
  - Re-port everything: wastes effort on review content that must stay external.

## Success Criteria

- Every drift row has a disposition and an owner; none is "unknown".
- PRD 00011's canary checklist references the inventory and passes it.

## Risks

- **The legacy runtime keeps moving during the port**: apply the freeze rule;
  date-stamp the inventory and diff against it before cutover.
- **Scope explosion from waves**: decide waves explicitly; cutover can ship
  without them if sequential drains cover daily use.

## Open Questions

- Are waves required for cutover, or can personal use run sequential drains
  for a while?
- Does the test-gate reuse (`verification.py`) belong in core as a generic
  capability, or stay in the skill behind a verb?
- Should OVCAQ commit the record store itself (legacy `store_tree.py`), given
  that this repo now ignores `docs/dev/project-management/`?

## Discovery Log

### Q1: How large is the drift?

**Answer**: Measured 2026-10-19: 1,040 commits under `skills/run-autopilot`
since 2026-08-25; the 34 modules in the table total about 11,000 lines.
