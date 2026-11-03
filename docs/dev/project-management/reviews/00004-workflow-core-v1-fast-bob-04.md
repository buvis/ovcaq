# FT-04R4 Bob doubt + de-slop review

## Isolation

- Reviewed HEAD: `e8fe191089d91140343e6246dffe66caf9caa6a9`
- Reviewed range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..e8fe191089d91140343e6246dffe66caf9caa6a9`
- Read-only isolated review.
- Inspected only `AGENTS.md`, the PRD, the complete range diff, all changed implementation/docs/tests, and necessary state-layer code.
- Did not read plans, coverage/discovery documents, reviews, handoffs, commit messages/logs, or other reviewers’ output.
- No repository file was edited.

## Verdict

`changes_requested`

## Must fix

1. **Completed PRDs remain selectable in `wip`.**

   `complete_prd()` only appends a summary and resets the park counter (`src/ovcaq/workflow/records.py:147-178`). Neither it nor any other workflow path moves the PRD from `paths.wip` to `paths.done`; `paths.done` has no production consumer. `select_from_paths()` consequently selects the completed file again.

   Reproduction with two WIP PRDs:

   ```text
   selection_after_complete ('00001-first.md', 'wip')
   active_after_more_prds 00001-first.md
   done_exists False wip_exists True
   ```

   This misses the PRD’s completion/done-to-next-PRD lifecycle and makes forward progress loop on the completed PRD. Completion needs an idempotent, recoverable WIP-to-done operation coordinated with the summary/state commit.

2. **The persisted rework cap is never enforced.**

   Frontmatter commits `review.cap`, and `resume_target()` has special handling for a `review_cap` pause, but `_rework()` unconditionally increments the cycle and remains in review (`src/ovcaq/workflow/transitions.py:40-49`). No production path creates the cap pause.

   Reproduction with `review.cap == 1` and `review.cycle == 1`:

   ```text
   cap_rework review 2 None
   ```

   This bypasses the configured cap and leaves the cap-resume branch unreachable. The transition must atomically pause at the cap with the required durable notice instead of advancing indefinitely.

3. **Frontmatter lifecycle choices are lost across state-driven resume.**

   `apply_to_store()` reports `catchup_mode`, `design_mode`, `design_gate`, and `pause_on_ambiguity`, but removes their extension keys without materializing equivalent state (`src/ovcaq/workflow/frontmatter.py:170-189`). The documented crosswalk says these values are derived from committed state, yet applying `catchup: skip` does not update `batch.catchup`; `resume_target()` therefore directs catchup to run.

   Reproduction:

   ```text
   frontmatter_fields {'catchup_mode': 'skip', 'design_mode': 'run', 'rework_cap': 1}
   frontmatter_extensions {}
   resume_after_catchup_skip build: catchup then planning
   ```

   This contradicts both the PRD frontmatter behavior and “state decides; prose does not.” Effective choices must survive restart in their canonical state representation, or resume must otherwise derive the same committed decision.

4. **A public state mutation can commit during recovery and then be silently erased.**

   The workflow-level functions fence on `recovery.operation`, but `StateService` task/contract mutations do not. After a stall intent was durably stamped, `StateService.add_task()` succeeded; replay then called `reset_prd_fields()` and discarded both existing and newly committed tasks.

   Reproduction:

   ```text
   task_mutation_during_recovery {'revision': 2, 'task_id': 2} ['original', 'concurrent']
   tasks_after_reconcile []
   ```

   This is a reproduced data-loss race across public `ovcaq state` and recovery operations. The recovery ownership fence must cover competing state mutations, or recovery commit must use a revision/precondition that cannot erase intervening work.

5. **`tasks_done` accepts state that still has pending tasks.**

   `_to_review()` changes phases without checking committed task status/counts (`src/ovcaq/workflow/transitions.py:31-37`). A state with one pending task and `tasks_completed == 0` was accepted:

   ```text
   pending_tasks_done review 0 1
   ```

   The resulting state is schema-valid, so later completion can record an unfinished PRD. This breaches the state-authoritative completion invariant. The transition must reject `tasks_done` unless committed task state proves completion.

## Can defer

- The CLI currently hardcodes `dev/local/prds` in `_dispatch_workflow()` and `_workflow_context()`. I verified that `resolve_lifecycle_paths()` itself correctly accepts relative or absolute configured roots, while the current project config has no lifecycle-root field. I therefore do not treat CLI configuration plumbing as an FT-04R4 blocker, but the runtime integration must not strand that configurability.
- Remove the redundant null check in `_verify_move()` and the unreachable unknown-phase fallback in `resume_target()`.
- Inline the single-caller `_workflow_context()` wrapper.
- Trim trivial paraphrasing docstrings and duplicated installed-package scenarios identified under R1/R4.

## Doubt audit

Total doubts: **10**

- **FIX / confirmed:** 5
- **VERIFY / dismissed as blocker:** 1
- **KNOWN / can defer:** 4

No fixes were applied because this review was explicitly read-only.

### 1. Least confidence

- **D1 — Completion filesystem lifecycle: VERIFY → FIX.** Confirmed that completion leaves the PRD in WIP and selection chooses it again. Must-fix finding 1.
- **D2 — Review-cap transition: VERIFY → FIX.** Confirmed that a rework at the cap advances to cycle 2 without pausing. Must-fix finding 2.

### 2. Assumptions checked against code/docs

- **D3 — Frontmatter output is equivalent to committed state: VERIFY → FIX.** It is not. `catchup: skip` is returned transiently but state-driven resume still schedules catchup. Must-fix finding 3.
- **D4 — Configured lifecycle paths are completely absent: VERIFY → dismissed as an FT blocker.** The pure resolver accepts caller-supplied relative and absolute roots and is tested. Only current CLI plumbing uses the default, and the current config layer exposes no alternate field. Retained as a scoped integration concern.

### 3. Original task/PRD completeness

- **D5 — Done-to-next-PRD and idempotent completion are complete: VERIFY → FIX.** Summary idempotency exists, but lifecycle completion does not; the completed artifact remains selectable. Must-fix finding 1.
- **D6 — Rework/convergence effects include cap behavior: VERIFY → FIX.** No producer exists for the `review_cap` pause handled by resume. Must-fix finding 2.

### 4. Practical failures, edges, races, and error paths

- **D7 — Recovery intent fences all competing public mutations: VERIFY → FIX.** A task mutation commits during recovery and is erased on replay. Must-fix finding 4.
- **D8 — A claimed `tasks_done` outcome cannot contradict committed state: VERIFY → FIX.** Pending tasks are accepted. Must-fix finding 5.

### 5. Alternate approach

- **D9 — Lifecycle policy is split across weakly coordinated calls: KNOWN.** I would use one authoritative transition/application boundary that validates state-derived preconditions and coordinates filesystem intent, record publication, state commit, and replay. The current split between `phase-complete`, `complete-prd`, selection, and file movement leaves critical obligations between commands. This is actionable through findings 1, 2, 4, and 5; broader consolidation can follow later.

### 6. Missing validations

- **D10 — Required negative/integration cases are absent: KNOWN pending fixes.** Missing tests include:

  - completion moves WIP to done and selection advances;
  - replay at every completion boundary;
  - rework at/below/above `review.cap`;
  - origin and resume of a `review_cap` pause;
  - frontmatter application followed by process restart/resume;
  - task/contract/generic state mutations during active recovery;
  - rejection of `tasks_done` with pending or in-progress tasks.

## R1–R5 de-slop rubric

### R1 — Bloat ratio/diff proportionality: FAIL

- Range size: 5,669 additions, 15 deletions, **5,654 net lines**.
- Acceptance-criteria section: **63 words**.
- Ratio: approximately **89.7 net lines per acceptance word**.
- Breakdown: 2,149 net source lines, 3,474 net test lines, 31 net documentation lines.
- Much of the saga code is justified by durability requirements. The clearest reducible bloat is `tests/packaging/test_installed_cli.py:116-457`, which repeats detailed defer, stall/park, frontmatter, and report scenarios already covered by workflow and in-process CLI tests. Installed-wheel coverage could retain provenance/import checks plus representative command/saga smoke coverage while removing roughly 200–250 repeated lines.
- Classification: **KNOWN / can defer**; proportionality cleanup is not itself a correctness blocker.

### R2 — Defensive impossibility: FAIL

- `src/ovcaq/workflow/records.py:467`: inside `if source_exists`, where `source_exists` was defined as `source_stat is not None`, the nested `source_stat is None` branch is impossible.
- `src/ovcaq/workflow/resume.py:46`: `State` loaded through `StateStore` can only have schema-valid phases, so the `"unknown phase"` fallback is unreachable on the public path.
- Classification: **KNOWN / can defer**; both are nonfunctional de-slop items.

### R3 — Unjustified single-caller abstraction: FAIL

- `_workflow_context()` (`src/ovcaq/cli.py:554-557`) has one caller at line 600 and only constructs a store, paths, and runtime root. It adds indirection without independent policy or testability.
- Classification: **KNOWN / can defer**; inline it or give it an actual configuration-loading responsibility.

### R4 — Comment/docstring paraphrasing: FAIL

Examples include:

- `selection.sequence()` at `src/ovcaq/workflow/selection.py:18-19`;
- `selection.selectable()` at `src/ovcaq/workflow/selection.py:24-25`;
- `paths.resolve_lifecycle_paths()` at `src/ovcaq/workflow/paths.py:20-24`;
- `transitions.next_phase()` at `src/ovcaq/workflow/transitions.py:96-97`.

These docstrings restate names/signatures rather than explaining non-obvious policy. Classification: **KNOWN / can defer**.

### R5 — Framework-/mock-/shape-only tests: PASS

- Parser/inventory shape tests enforce the explicit live-parser documentation contract.
- Import/string boundary tests enforce explicit architecture invariants.
- Fsync monkeypatch tests check required ordering relative to durable state steps, not Python/mock behavior alone.
- Installed-wheel tests verify packaging provenance and hostile-CWD behavior.
- No test was found whose sole meaningful assertion merely confirmed a mock call or language/framework behavior.

## Tests inspected/run

Inspected:

- The complete changed production and documentation diff.
- All changed workflow test files, fixtures, installed-package tests, and small state/package test modifications.
- Necessary lower-layer state schema, state store, state service, config, and path code.

Run independently:

```text
env PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests/workflow -q -p no:cacheprovider
185 passed in 1.23s
```

```text
git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..e8fe191089d91140343e6246dffe66caf9caa6a9
passed
```

Temporary-path reproductions confirmed all five must-fix behaviors above.

Fresh coordinator verification at exact HEAD was also supplied:

- `uv sync`: passed, 25 resolved / 24 checked.
- Focused saga + installed CLI pytest: 44 passed in 1.68s.
- Full pytest: 1,076 passed in 10.88s.
- Ruff check: passed.
- Ruff format check: passed, 92 files.
- Mypy: passed, 47 source files.
- Build: passed.
- Complete-range diff check: passed.

## Residual doubts

- The pure path resolver supports configured roots, but current CLI commands cannot obtain one from project configuration.
- Deferred-record state checking and record publication are not one atomic transaction; the demonstrated broader recovery fence defect should be fixed before deciding whether an additional defer-specific concurrency test is needed.
- Report publishing is projection-only and therefore less critical, but concurrent writers have no report lock; later runtime supervision should ensure serialized publication or make last-writer repair explicit.
