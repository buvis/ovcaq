# FT-04R3 blind PRD review

- Reviewed HEAD: `f2453760591875f1faf241ec9c0291303232efd9`
- Complete range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..f2453760591875f1faf241ec9c0291303232efd9`
- Verdict: `changes_requested`

## Findings

### 1. High — Successful completion cannot advance reliably to the next PRD

- Root cause: `complete-prd` only appends a state summary, while `done/more_prds` only resets per-PRD fields. Neither operation moves the completed WIP file to `done`, and reset deliberately retains the old `work.prd`.
- Evidence:
  - WIP always wins selection: `src/ovcaq/workflow/selection.py:32-40`.
  - `complete_prd` has no lifecycle-path or filesystem effect: `src/ovcaq/workflow/records.py:144-175`.
  - Reset retains the previous PRD, codified by the test expectation: `tests/workflow/test_records.py:69-88`.
  - `done/more_prds` delegates only to that reset: `src/ovcaq/workflow/transitions.py:61-77`.
  - `LifecyclePaths.done` is defined but unused by production workflow operations: `src/ovcaq/workflow/paths.py:9-37`.
- Impact: After completing PRD A, `workflow select` still finds A in WIP and returns it instead of backlog PRD B. The installed command family cannot perform the PRD’s required done-to-next-PRD handoff without undocumented external file manipulation.
- Required fix: Provide a deterministic, idempotent successful-completion handoff that verifies and moves WIP to done, records completion, and leaves state ready to select/activate the next PRD. Protect multi-resource interruption boundaries with recovery intent and add an installed-command test covering A completion followed by selection of B.

### 2. High — Installed commands ignore configured lifecycle directories

- Root cause: The reusable path resolver accepts a configured root, but the CLI unconditionally supplies `Path("dev/local/prds")`.
- Evidence:
  - Configurable resolver contract: `src/ovcaq/workflow/paths.py:20-37`.
  - Hardcoded workflow context: `src/ovcaq/cli.py:554-557`.
  - The public dispatch repeats the same hardcoded root, including `select`: `src/ovcaq/cli.py:590-600`.
  - No lifecycle-root input exists in the workflow parser: `src/ovcaq/cli.py:140-216`.
- Impact: `select`, `stall`, and `park` inspect or move files in the default tree even when the project config points elsewhere. For mutating commands this can target the wrong filesystem tree.
- Required fix: Resolve the lifecycle root once from project configuration and thread it through every installed workflow operation. Add installed-command coverage for non-default relative and absolute lifecycle roots.

### 3. Medium — The installed frontmatter command can never honor a valid tier hint

- Root cause: Tier resolution requires `available_tiers`, but CLI dispatch never supplies the active agent’s configured tier map.
- Evidence:
  - A tier is applied only when present in `available_tiers`; otherwise it warns and applies no floor: `src/ovcaq/workflow/frontmatter.py:126-134`.
  - `apply_to_store` exposes the required input: `src/ovcaq/workflow/frontmatter.py:151-160`.
  - CLI invocation omits it: `src/ovcaq/cli.py:601-609`.
  - The command parser exposes no equivalent input: `src/ovcaq/cli.py:151-156`.
- Impact: Every `default_model` declaration invoked through the accepted installed command is treated as unavailable, even when it is a valid abstract tier for the active agent. This violates the PRD’s configured-tier-map behavior.
- Required fix: Obtain the active agent tier map from runtime configuration or a stable command input and pass it to `apply_to_store`. Test both available and unavailable tiers through the installed command.

### 4. Medium — An accepted `stall` input is not idempotent after commit

- Root cause: Deferred records do not preserve the operation kind. Replay infers `park` solely when `site == "wrapper_died"`, although public `stall` accepts that site without restriction.
- Evidence:
  - Replay inference: `src/ovcaq/workflow/records.py:489-512`.
  - Both park and stall records are written with `"type": "stall"` and no explicit kind: `src/ovcaq/workflow/records.py:697-711`.
  - `stall` accepts an unrestricted site: `src/ovcaq/workflow/records.py:726-751`; `src/ovcaq/cli.py:184-190`.
- Impact: `workflow stall --site wrapper_died ...` can complete successfully, but an exact retry after the final commit is classified as a park and fails with “no durable recovery proof.” Thus recovery is not idempotent for all inputs accepted by the installed interface.
- Required fix: Persist and match the explicit recovery kind in the deferred record, or reject the reserved site for `stall`. Add post-commit replay coverage for the boundary case.

## PRD acceptance-criteria coverage

| Acceptance criterion | Assessment | Evidence |
|---|---|---|
| Current lifecycle fixtures have equivalent OVCAQ outcomes | Covered, narrowly | Resume characterization in `tests/workflow/test_characterized_fixtures.py:62-88`; report goldens in `tests/workflow/test_reports.py:292-312`. Does not exercise successful filesystem advancement. |
| Every transition and rejection is covered row-by-row | Partial | Defined rows and rejection matrix are enumerated in `tests/workflow/test_transitions.py:10-40,164-197`; the done-to-next full operational effect remains incomplete per finding 1. |
| Park/stall/defer recover at all durable boundaries | Not met | Standard failpoints are exercised in `tests/workflow/test_sagas.py:110-179`, but the accepted stall-site replay failure in finding 4 remains. |
| No hardcoded legacy runtime root remains | Met literally | Workflow string guard includes `dev/local/autopilot`: `tests/workflow/test_boundaries.py:14-22,46-53`. Configured lifecycle behavior still fails separately per finding 2. |
| Workflow imports only state and standard-library/lower-layer code | Met | AST dependency guard: `tests/workflow/test_boundaries.py:6-43`; inspected workflow imports conform. |
| PRD 00005 can consume stable workflow and state services | Partial | Pure modules exist, but configured paths, installed tier resolution, and successful next-PRD handoff are not complete. |

## Scope assessment

No material scope creep found. Parser-generated documentation, path confinement, deterministic final-state archival, and the new plan-size error are reasonably connected to workflow commands, rendering, drain behavior, and filesystem safety. Provider/runtime policy has not leaked into workflow modules.

## Verification evidence

Fresh supplied gate evidence:

- `mise exec -- uv sync --all-groups`: exit 0; 25 resolved, 24 checked.
- `mise exec -- uv run pytest`: exit 0; 1068 passed in 13.84s.
- `mise exec -- uv run ruff check .`: exit 0.
- `mise exec -- uv run ruff format --check .`: exit 0; 92 files formatted.
- `mise exec -- uv run mypy src/ovcaq`: exit 0; 47 source files clean.
- `mise exec -- uv build`: exit 0; sdist and wheel built.
- Additional read-only check: complete-range `git diff --check` passed.

Passing gates establish consistency with the current tests, but the identified cases are absent from those tests.

## Isolation statement

I reviewed the complete specified range, not only the final rework commit. I used only the allowed PRD, complete diff, changed files for surrounding context, and supplied gate evidence. I did not read implementation plans, AGENTS files, prior reviews, handoffs, commit messages, or another reviewer’s output.
