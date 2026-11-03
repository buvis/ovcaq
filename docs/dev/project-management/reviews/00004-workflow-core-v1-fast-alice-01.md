# Alice — consensus/architecture

## Verdict

changes_requested

## Must fix

- **Installed workflow commands ignore required configuration — high.**
  `src/ovcaq/config.py:8-15` only touches `ovcaq.toml`;
  `src/ovcaq/cli.py:502-505,540-554` hardcodes `dev/local/prds` and never
  supplies the active agent tier map. A configured PRD root reproduced as
  `{"prd": null, "source": "drained"}` despite containing a valid WIP PRD.
  Violates P02-T01/P02-T02/P02-T09 and the configured-directory/frontmatter
  contract.

- **Lifecycle paths can escape the project and feed destructive moves — high.**
  `src/ovcaq/workflow/paths.py:25-30` accepts absolute and `..` paths without
  containment, while `src/ovcaq/workflow/records.py:333-362,468-476,521-522`
  does not reject symlinked lifecycle directories before renaming. Violates
  the accepted path-security policy and the PRD's verified-move requirement.

- **Rework leaves prior-cycle review results live — high.**
  `src/ovcaq/workflow/transitions.py:40-46` increments the cycle but clears only
  `rework_task_ids`; `review.lenses` and `review.rubric_verdicts`, which have no
  cycle discriminator (`src/ovcaq/state/schema.py:220-235`), remain populated.
  A probe returned cycle 2 with Alice still completed and an R1 failure still
  live. Violates the explicit `review + rework` full effect, which must clear
  cycle-local data.

- **`complete-prd` can durably complete an unfinished PRD — high.**
  `src/ovcaq/workflow/records.py:122-145` checks the filename but not terminal
  phase or review convergence. `tests/workflow/test_workflow_cli.py:104-158`
  demonstrates completion immediately after `build -> review`. This creates
  contradictory authoritative state and violates the fixed lifecycle.

- **A reused defer operation ID with a different payload silently loses the
  later record — high.** `src/ovcaq/workflow/records.py:293-299` returns success
  for any matching `op_id` without comparing canonical payloads. A probe kept
  `detail: first` and silently discarded `detail: second`. Violates P02-T06 and
  the no-lost-work/idempotent recovery criteria.

- **Selection accepts directories as PRDs — medium.**
  `src/ovcaq/workflow/selection.py:43-47` returns every directory entry name;
  `selectable()` filters only suffix and numeric prefix. A WIP directory named
  `00001-not-a-prd.md` was selected ahead of a real PRD. Violates P02-T01.

- **Required row/boundary evidence is not committed — medium.**
  `tests/workflow/test_transitions.py:91-107` covers only three rejection
  examples, not every rejection row. `tests/workflow/test_sagas.py:108-177`
  covers park/stall failpoints, while defer coverage at lines 297-337 has no
  interruption failpoints. The handoff's transient transition probe is not a
  reproducible committed test. Violates the PRD's row-by-row and every-durable-
  boundary acceptance requirements.

## Can defer

- `complete_prd_in_store()` increments revision on an otherwise idempotent
  replay (`tests/workflow/test_applications.py:110-126`). Duplicate summary
  prevention works, so byte-level idempotence can be clarified after the
  terminal-phase guard is fixed.
- Python 3.12 was not exercised; verification used Python 3.13.13. No inspected
  syntax appeared incompatible, but the declared lower bound remains unverified.

## Tests inspected or run

- `mise exec -- uv run pytest tests/workflow tests/packaging/test_installed_cli.py -q`
  — 138 passed.
- Read-only probes reproduced conflicting defer-ID loss, stale rework-cycle
  state, invalid-directory selection, and ignored configured PRD root.
- Inspected all changed workflow modules, CLI/docs, workflow tests,
  installed-wheel tests, exact-range diff, and verification handoff.
- Confirmed HEAD `5a7ff023059bd396a177da7946a25ffe8d6d176d`;
  `git diff --check` passed and tracked worktree remained clean.

## Residual doubts

- Recovery intent records no batch ID, while replay chooses the current batch
  at `src/ovcaq/workflow/records.py:526-537`; an unsafe batch replacement could
  misattribute evidence.
- Evidence/report subdirectories are not protected against symlink substitution
  before atomic publication.
