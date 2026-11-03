# Alice — consensus/architecture

## Verdict

`changes_requested`

## Must fix

1. **A held active PRD is accepted as a completed replay without durable evidence.**
   - Severity: high; silent record/state-loss risk.
   - Evidence: `src/ovcaq/workflow/records.py:544-556` returns success whenever the active PRD is absent from `wip` and present in `hold`, without requiring recovery intent, a matching deferred record, or reset state.
   - Reproduction: a `/tmp` probe initialized an active PRD with one pending task, moved it from `wip` to `hold` before invoking `stall`, then observed:
     `{"ledger_exists": false, "recovery": null, "result": {"operation_id": null, "replayed": true}, "revision": 0, "tasks_total": 1}`.
     The command reported successful replay while performing none of move-record-reset-commit.
   - Violates PRD `dev/local/prds/wip/00004-workflow-core-v1.md:75-78`, source task P02-T07 at `dev/local/plans/implementation-plan.md:1164`, and the recoverability exit criterion at `dev/local/plans/implementation-plan.md:1174`.

2. **Durable recovery intent does not fence competing workflow mutations, so a committed transition can be erased during reconciliation.**
   - Severity: high; authoritative state changes can be lost.
   - Evidence: intent is committed at `src/ovcaq/workflow/records.py:463-468`; `phase_complete` at `src/ovcaq/workflow/transitions.py:84-114` does not reject active recovery; saga commit resets PRD state at `src/ovcaq/workflow/records.py:472-500`. This conflicts with recovery precedence already encoded at `src/ovcaq/workflow/resume.py:10-12`.
   - Reproduction: interrupting `stall` after intent, calling `phase_complete(..., "tasks_done")`, then replaying `stall` produced:
     `after_intent={"phase":"build","revision":1,"recovery_step":"intent"}`;
     `phase_complete={"phase":"review","revision":2}`;
     `after_reconcile={"phase":"build","review_cycle":0,"revision":5,"recovery":null}`.
     The valid review transition was silently discarded.
   - Violates PRD recovery semantics at `dev/local/prds/wip/00004-workflow-core-v1.md:77-78`, success metric at `:31`, P02-T03/P02-T07, and the Phase 2 recoverability exit criterion.

3. **Frontmatter persistence bypasses the accepted v1 state crosswalk.**
   - Severity: high; earlier schema/protocol contract breach.
   - Evidence: `src/ovcaq/workflow/frontmatter.py:24-29` invents durable `work.extensions` copies for catchup mode, design mode, design gate, and pause-on-ambiguity; `:160-174` writes them. The accepted protocol says those legacy fields are derived from `batch.catchup`, `work.design_doc`, and `control.pause_reason`, not duplicated (`docs/state-protocol.md:300-317`). `tests/workflow/test_applications.py:43-50` explicitly locks in the conflicting representation.
   - Inspection result: applying frontmatter persists `workflow/catchup-mode`, `workflow/design-mode`, and `workflow/pause-on-ambiguity` instead of using/reconciling the previously accepted targets.
   - Violates coverage rule 7 at `dev/local/prds/implementation-plan-coverage.md:42-43` and P02-T02. The earlier schema must be followed or explicitly reconciled; an extension-map workaround is not contract-equivalent.

4. **P02-T08’s characterized report/golden port is incomplete.**
   - Severity: high; required source behavior and acceptance evidence gap.
   - Evidence: the committed migration route assigns final-state archive, audit/report/metrics goldens, replaceable report sections, and their characterization tests to `workflow/reports.py` (`tests/characterization/migration.toml:69-76`; source evidence at `tests/characterization/current_system.toml:2513-2535`, `:2729-2751`). The implementation only renders a current snapshot and replaces one whole report (`src/ovcaq/workflow/reports.py:100-150`, `:233-243`); it has no final-state archive or replaceable per-PRD section behavior. Tests assert synthetic substrings rather than migrated golden equivalence (`tests/workflow/test_reports.py:75-149`), and the complete diff adds no migrated golden fixtures.
   - Violates P02-T08 at `dev/local/plans/implementation-plan.md:1165`, coverage rule 7, and the lifecycle-equivalence success metric at `dev/local/prds/wip/00004-workflow-core-v1.md:29`.

## Can defer

None.

## Tests inspected or run

- Confirmed clean exact HEAD `56b664fc44c359b0b97282aa2e116dbf9ed44ff9`.
- Inspected every changed production, documentation, and test file across `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..56b664fc44c359b0b97282aa2e116dbf9ed44ff9`; complete range is 30 files, 4,239 insertions, 12 deletions.
- `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..56b664fc44c359b0b97282aa2e116dbf9ed44ff9` — passed, no output.
- `PYTHONDONTWRITEBYTECODE=1 mise exec -- uv run pytest -p no:cacheprovider tests/workflow tests/packaging/test_installed_cli.py -q` — first sandboxed attempt could not access the existing uv cache; authorized rerun passed: `167 passed in 1.31s`.
- Two `mise exec -- uv run python -c <temporary /tmp probe>` reproductions produced the exact saga failures reported above.
- Exact-HEAD packet evidence inspected:
  - `mise exec -- uv sync --all-groups` — passed, 25 resolved/24 checked.
  - Full pytest — 1,049 passed in 10.95s.
  - Ruff check — passed.
  - Ruff format check — passed, 89 files.
  - Mypy — passed, 47 source files.
  - `uv build` — passed.
  - Accepted-plan SHA-256 matched `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
  - Frozen autopilot-state SHA-256 evidence was `ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f`; state was not read or mutated during review.

## Residual doubts

- Items 1 and 2 are reproduced defects, not concurrency speculation.
- Items 3 and 4 are direct committed-contract inconsistencies/evidence gaps established by inspection.
- I did not classify future configuration wiring for lifecycle roots or active-agent tier maps: their pure seams exist, while broader configuration ownership belongs to a later PRD.
- I did not test adversarial filesystem type-changing races; no claim about them is included.
