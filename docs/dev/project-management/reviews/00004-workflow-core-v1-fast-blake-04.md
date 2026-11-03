# FT-04R4 Blind PRD Review

- **Reviewed HEAD:** `e8fe191089d91140343e6246dffe66caf9caa6a9`
- **Reviewed range:** `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..e8fe191089d91140343e6246dffe66caf9caa6a9`
- **Isolation:** Blind PRD-only review. I read only the permitted PRD, complete-range diff, changed implementation/docs/tests, and necessary state/config lower-layer code. I did not read plans, handoffs, prior reviews, coverage/discovery documents, commit messages/logs, or other reviewers’ output.
- **Workspace:** Read-only; no repository files edited.
- **Verdict:** `changes_requested`

## Must fix

### 1. High — Completed PRDs remain in `wip` and are immediately selected again

**Evidence**

- Selection always prefers any selectable WIP file: `src/ovcaq/workflow/selection.py:32-40`.
- `complete_prd()` only records the summary and resets the park counter: `src/ovcaq/workflow/records.py:147-178`.
- The `more_prds` transition only calls the state reset: `src/ovcaq/workflow/transitions.py:61-63`.
- That reset preserves `work.prd` and performs no lifecycle file operation: `src/ovcaq/workflow/records.py:90-124`.
- `LifecyclePaths.done` is defined at `src/ovcaq/workflow/paths.py:17,36`, but no workflow implementation uses it.
- No installed workflow command moves a successfully completed PRD from `wip` to `done`.

**Reproduction**

In a temporary tree I created:

- `wip/00004-current.md`
- `backlog/00005-next.md`
- A converged state for `00004-current.md`

I then called `complete_prd_in_store()`, followed by `phase_complete(..., "more_prds")`, then `select_from_paths()`.

Observed:

```text
selection ('00004-current.md', 'wip')
current_in_wip True
current_in_done False
state_prd 00004-current.md
phase build
```

The declared workflow therefore loops back to the completed PRD unless an undocumented external actor mutates lifecycle files.

**Violated PRD requirements**

- Extract the current PRD lifecycle as deterministic services: PRD lines 17-20.
- Fixed build/review/done/drain lifecycle: line 40.
- Full `done-to-next-PRD` effects: lines 64-66.
- Complete PRDs and support next-PRD behavior: lines 68-71 and 154-162.
- Agents use installed workflow commands for handoff: lines 22-25.
- Stable services consumable by PRD 00005: line 178.

Completion needs an idempotent, recoverable retirement of the active WIP artifact, or another documented core-owned operation that makes subsequent selection advance.

### 2. High — Lifecycle-directory replacement can commit success after misplacing the PRD

**Evidence**

- The saga opens WIP and hold directory descriptors at `src/ovcaq/workflow/records.py:647-650`.
- After durable intent, the failpoint permits arbitrary intervening filesystem change: `src/ovcaq/workflow/records.py:700-708`.
- `_verify_move()` renames using the previously opened descriptors: `src/ovcaq/workflow/records.py:452-483`.
- It verifies contents through those descriptors, but never verifies that the descriptors still identify the directories currently named by `paths.wip` and `paths.hold`.
- The saga then records and clears recovery intent as successful: `src/ovcaq/workflow/records.py:711-746`.
- The existing swap test at `tests/workflow/test_sagas.py:535-562` removes the open hold directory before replacing it. It does not cover renaming that directory away, which leaves its descriptor valid.

**Reproduction**

At `AFTER_INTENT_BEFORE_MOVE`, I renamed the open `hold` directory to `relocated-hold`, then created `hold` as a symlink to another directory.

The saga returned success:

```text
result SagaResult(operation_id='op', kind='stall', replayed=False, systemic_halt=False)
wip False hold False relocated True external False
recovery None phase build
```

The PRD was moved into `relocated-hold`, was absent from the configured `hold`, and recovery intent was cleared. This is a lost-work/recovery-location failure even though the command reports success.

**Violated PRD requirements**

- Verified file moves protected by durable recovery intent: lines 75-78.
- Restart safely completes or retries every boundary without lost work: lines 135-142.
- Park/stall recovery at every durable boundary: line 175.

The saga must verify directory identity against the configured lifecycle names before advancing or committing, and retain enough durable evidence to recover if identity changes after intent.

### 3. Medium — Required lifecycle-fixture equivalence evidence is incomplete

**Evidence**

- `tests/fixtures/README.md:9-11` identifies the three legacy state fixtures as workflow transition, review-cycle, and convergence characterization evidence.
- `tests/workflow/test_characterized_fixtures.py:62-88` converts those fixtures but tests only `resume_target()`.
- Transition tests in `tests/workflow/test_transitions.py:10-224` use newly authored expectations rather than comparing against the characterized legacy outcomes.
- No fixture-backed equivalence test covers the full transition effects, reset/completion behavior, or lifecycle advancement.

**Violated PRD requirements**

- Existing lifecycle fixtures produce equivalent outcomes: lines 27-30.
- Phase A exit criterion requiring lifecycle fixtures to match current outcomes: line 133.
- Behavioral-drift mitigation: line 166.
- Explicit acceptance criterion: line 173.

Passing synthetic row tests demonstrates internal consistency, but does not prove the required equivalence to the characterized behavior.

## Can defer

### Frontmatter applications forget most effective settings

`apply_to_store()` removes prior catchup/design/gate/ambiguity extension values but only persists the review cap and optional tier floor: `src/ovcaq/workflow/frontmatter.py:170-189`.

A temporary replay showed that applying `catchup: skip`, `design: skip`, and `pause_on_ambiguity: true` left `work.extensions` empty; a later application changing them back produced no overwrite warnings. This may be acceptable if these are deliberately one-shot return values consumed immediately by runtime, but that lifetime contract should be explicit before PRD 00005 relies on it.

### Concurrent report publication can lose sections

`publish_report()` performs an unlocked read/modify/replace sequence at `src/ovcaq/workflow/reports.py:391-411`. Two concurrent renders for different PRDs can both read the same prior report and have the last replacement discard the other update. The PRD does not explicitly require concurrent rendering, so supervisor serialization may be sufficient for v1.

### Installed-wheel execution coverage is uneven

The installed-wheel suite executes defer, stall/park, frontmatter, and report failure paths, while several commands are only exposed through installed help and exercised in-process. Wheel import provenance substantially reduces packaging risk, but direct installed success cases for `select`, `phase-complete`, `resume-target`, `check-plan`, `complete-prd`, `render audit`, and `render metrics` would better substantiate the Phase C exit criterion.

## PRD acceptance assessment

| Requirement | Assessment | Evidence |
| --- | --- | --- |
| Current lifecycle fixtures have equivalent OVCAQ outcomes | **Fail** | Only resume-target equivalence is exercised; documented transition/convergence fixtures do not drive full-effect comparisons. |
| Every transition and rejection covered row-by-row | **Pass in isolation** | All declared allowed and rejected phase/outcome rows are tested in `test_transitions.py`. Integrated next-PRD behavior still fails. |
| Park/stall/defer recover at all durable boundaries | **Fail** | Directory rename/replacement reproduction commits while the PRD is outside configured WIP/hold. |
| No hardcoded legacy runtime root remains | **Pass** | Boundary guard scans workflow modules; complete-range inspection found no `dev/local/autopilot` workflow dependency. |
| Workflow imports only state and lower-layer/standard-library code | **Pass** | AST boundary guard covers the workflow package. |
| PRD 00005 can consume stable workflow and state services | **Fail** | The available services cannot advance past a completed WIP PRD, and recovery can clear intent after misplacing it. |
| Installed workflow command family exists | **Pass** | Parser, generated docs, in-process tests, and installed help expose all required verbs. |
| Deterministic audit/report/metrics rendering | **Pass** | Golden, idempotency, confinement, and parser/docs tests cover the declared projections. |
| Frontmatter, plan policy, resume, reset, deterministic summaries | **Pass with deferred caveat** | Focused unit/application tests cover these behaviors; frontmatter value lifetime remains unclear. |

## Tests inspected/run

Independently run:

```text
.venv/bin/pytest -q -p no:cacheprovider tests/workflow
185 passed in 0.39s
```

Also independently ran:

- Completion-to-selection temporary reproduction: reproduced completed WIP reselection.
- Directory rename/replacement temporary reproduction: reproduced successful commit with the PRD outside configured hold.
- Complete-range `git diff --check`: passed.
- Final `git status --short`: clean.

Inspected:

- All changed workflow implementation modules.
- Changed CLI workflow registration and dispatch.
- Workflow unit, application, saga, report, boundary, characterization, and CLI tests.
- Installed-wheel workflow tests and generated command documentation.
- Necessary state schema/store-facing service and path/config behavior.

Coordinator-provided fresh verification at the exact HEAD was also considered:

- `uv sync`: passed.
- Focused saga/installed tests: 44 passed.
- Full pytest: 1076 passed.
- Ruff check and format check: passed.
- Mypy: passed.
- Wheel build: passed.
- Complete-range diff check: passed.

## Residual doubts

- The PRD names the implementation plan, coverage manifest, and discovery document as mandatory source inputs, but the isolation packet explicitly prohibited reading them. Obligations stated only there could not be assessed.
- Drain changes only PRD phase/next-phase; whether batch completion status and timestamp belong to this workflow layer remains ambiguous from the permitted PRD.
- Standalone defer fencing is based on a committed-state read rather than participating in a state transaction, so races with a newly stamped recovery operation remain insufficiently characterized.
