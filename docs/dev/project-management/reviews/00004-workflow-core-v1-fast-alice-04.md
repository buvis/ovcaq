# FT-04R4 Alice consensus/architecture review

## Reviewed target and isolation

- HEAD: `e8fe191089d91140343e6246dffe66caf9caa6a9`
- Complete range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..e8fe191089d91140343e6246dffe66caf9caa6a9`
- Accepted-plan SHA-256 independently verified: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`
- Reviewed only the allowed packet, complete range diff, changed implementation/docs/tests, and necessary state-layer code.
- Did not inspect prohibited reviews, fast-track handoffs/plans, implementation handoffs, commit logs/messages, or other reviewers’ output.
- Read-only review; reproductions used temporary paths. Repository remained clean.

## Verdict

`changes_requested`

## Must fix

### High — `done + more_prds` leaves the completed PRD authoritative in the new build phase

Evidence:

- The contract requires the done-to-next transition’s full effects and resetting per-PRD owners: `dev/local/prds/wip/00004-workflow-core-v1.md:64-71`.
- The accepted lifecycle explicitly specifies `done + more_prds -> build (reset per-PRD fields)`: `dev/local/plans/implementation-plan.md:646-655`, source IDs P02-T03/P02-T05 at `dev/local/plans/implementation-plan.md:1160-1162`.
- `reset_prd_fields()` changes phase and other per-PRD data but never clears or replaces `work.prd`: `src/ovcaq/workflow/records.py:90-124`.
- The `more_prds` row delegates directly to that reset: `src/ovcaq/workflow/transitions.py:61-77`.
- `workflow select` is read-only, so no current compound workflow operation installs the selected PRD during this handoff: `src/ovcaq/cli.py:594-598`.

Reproduction at reviewed HEAD:

```text
initial: work.prd=00004-old.md, work.phase=done, completed_phases=[review]
apply(state, "more_prds")
result: work.prd=00004-old.md, work.phase=build
resume_target(result): build: catchup then planning
```

A durable restart after this handoff therefore treats the completed PRD as the active build PRD. That can repeat work or fail against a PRD already moved out of `wip`; state no longer describes a valid done-to-next boundary. Existing tests encode preservation of the old PRD rather than testing interruption between PRDs (`tests/workflow/test_records.py:34-100`).

Separate the saga-replay reset needs from next-PRD transition ownership, then add a restart test proving `more_prds` cannot resume against the completed PRD.

### Medium — the installed frontmatter command cannot accept any valid tier hint

Evidence:

- The PRD requires tier keys to be resolved against the active agent’s configured tier map, accepting available keys and warning only for absent keys: `dev/local/prds/wip/00004-workflow-core-v1.md:52-58` (P02-T02).
- The parser supports this only when `available_tiers` is supplied: `src/ovcaq/workflow/frontmatter.py:86-90`, `src/ovcaq/workflow/frontmatter.py:126-134`.
- `apply_to_store()` defaults that input to `None`: `src/ovcaq/workflow/frontmatter.py:151-160`.
- The installed command never supplies a tier map: `src/ovcaq/cli.py:601-609`.

Reproduction using an initialized temporary project and an active PRD containing `default_model: deep`:

```text
ovcaq: PRD frontmatter tier 'deep' is unavailable; applying no tier floor
result fields: catchup_mode, design_mode, rework_cap only
work.extensions: {}
exit: 0
```

Thus every tier is treated as unavailable through the installed command, even though direct unit tests can inject a set. Wire a provider-neutral active tier-key set into the command boundary and cover both available and unavailable tiers through installed-command tests.

## Can defer

### Dependency-aware resume selection

`resume_target()` chooses the first non-completed task without checking `blocked_by`: `src/ovcaq/workflow/resume.py:30-39`. The state protocol retains dependency edges, and plan validation accepts arbitrary acyclic ordering. No explicit P02 criterion requires choosing the first runnable task, so this need not block Phase 2, but it should be resolved before supervisor execution to avoid selecting a blocked task.

### Full configuration wiring for lifecycle roots

The pure resolver accepts configured relative or absolute roots, but CLI wiring still supplies `Path("dev/local/prds")`: `src/ovcaq/cli.py:554-557`, `src/ovcaq/cli.py:594-595`. No legacy runtime root remains, and broader configuration/path ownership belongs to the next runtime phase, so this can defer if PRD 00005 wires the existing seam rather than duplicating it.

### Import guard is a denylist rather than the claimed allowlist

`tests/workflow/test_boundaries.py:30-43` forbids selected higher-layer packages but would not catch imports from `ovcaq.cli`, `ovcaq.config`, or an arbitrary third-party dependency. Current workflow code is clean by inspection, so this is not a present architecture breach, but an allowlist would better preserve the stated lower-layer-only contract.

## Acceptance and source-ID assessment

| Source ID | Assessment | Evidence |
|---|---|---|
| P02-T01 | Pass | Deterministic WIP/backlog selection, hold exclusion, lifecycle resolver, missing/invalid/symlink cases. |
| P02-T02 | Changes required | Parsing/default/warning unit coverage is good; installed tier-map resolution is absent. |
| P02-T03 | Changes required | Matrix and rejection coverage are complete, but `more_prds` does not establish a valid next-PRD state. |
| P02-T04 | Pass | Resume matrix, recovery priority, plan ceiling, shape, references, and cycle checks. |
| P02-T05 | Changes required | Summary/idempotency coverage passes; next-PRD reset retains the completed active PRD. |
| P02-T06 | Pass | Operation-ID deduplication, conflicting replay rejection, and publish retry coverage. |
| P02-T07 | Pass | Intent/move/record/reset/commit saga, directory fsync, symlink resistance, replay, and park breaker are well covered. |
| P02-T08 | Pass | Deterministic goldens, byte-idempotent publication, section replacement, confinement, and final snapshot. |
| P02-T09 | Pass for Phase 2 | No production `dev/local/autopilot` root remains; OVCAQ runtime defaults and boundary scan pass. |
| P02-T10 | Pass | Workflow reference and complete protocol inventory derive from the live parser and are tested exactly. |

Phase exit assessment:

- Lifecycle fixture equivalence: passing but narrow; three migrated legacy states exercise resume outcomes.
- Recoverability: strong passing evidence across every enumerated durable boundary, exact replay, collision handling, directory fsync, and installed CLI cases.
- Dependency direction/provider neutrality: passes current code inspection and guards.
- Installed command family/renderers: passes, except for tier-map semantics above.
- Stable consumption by PRD 00005: blocked by the stale-PRD next transition.

## Architecture assessment

- One state writer: pass. Workflow state mutations use `StateStore.transaction()`.
- State decides; prose does not: violated at the `more_prds` boundary because committed state still identifies the completed PRD as active build work.
- Provider code stays at the edge: pass; workflow code contains no provider branches or identifiers.
- Raw-evidence normalization, TUI ownership, external provisioning, and configured-command shell safety: not materially exercised by this Phase 2 range.
- Filesystem authority: pass. Recovery intent is durable, reports remain projections, and no marker-file/dual-writer design was introduced.
- Scope: appropriately confined to workflow/state-facing code overall.

## Tests inspected and run

Fresh coordinator evidence accepted at exact HEAD:

- `uv sync`: passed.
- Focused saga/installed CLI suite: 44 passed.
- Full pytest: 1,076 passed.
- Ruff check and format check: passed.
- Mypy: passed.
- `uv build`: passed.
- Complete-range `git diff --check`: passed.

Independent review execution:

- `pytest -p no:cacheprovider tests/workflow -q`: 185 passed.
- `pytest -p no:cacheprovider tests/packaging/test_installed_cli.py -q`: 9 passed.
- Accepted-plan digest: matched.
- Complete-range `git diff --check`: passed.
- Targeted pure transition/resume reproduction confirmed stale `work.prd`.
- Targeted temporary installed-command reproduction confirmed all tier hints are rejected without a usable configured tier map.

## Residual doubts

- Legacy-equivalence evidence converts fixtures into v1 through a test-local adapter rather than comparing both implementations against a retained oracle. Provenance is documented, so this is not blocking, but it limits drift detection.
- Recovery testing is exceptionally thorough for injected interruption points; true process-kill coverage for workflow sagas was not independently rerun in this review.
- The future supervisor must define atomic selected-PRD activation rather than compensating for an ambiguous workflow transition after the fact.
