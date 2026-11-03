---
prd: 00004-workflow-core-v1
session: FT-04R6
review_kind: fast-track
cycle: 6
date: 2026-09-05
base_sha: b43bf2c94d5eb0fddafca55542ef2570b45e8d52
head_sha: c4b9ea38d2e11eac4a1de1a71bd7d4134142e661
verdict: changes_requested
must_fix_root_causes: 6
rework_bundles: 2
reviewers:
  alice: pass
  blake: changes_requested
  bob: changes_requested
---

# PRD 00004 fast-track review — cycle 06

## Scope and isolation

- Reviewed exact clean HEAD `c4b9ea38d2e11eac4a1de1a71bd7d4134142e661` over the complete implementation range `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c4b9ea38d2e11eac4a1de1a71bd7d4134142e661`.
- Reviewed all P02-T01–P02-T10 obligations, all 55 PRD-00004 migration IDs, retained lifecycle/report/metrics fixtures, the complete current implementation and relevant tests, parser-derived documentation, and the full range diff.
- Accepted-plan digest: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
- Alice, Blake, and Bob ran concurrently in isolated read-only contexts. No earlier PRD-00004 review, raw-lens report, or earlier handoff was supplied or read; only the explicitly permitted `rework-05.md` reached Alice/coordinator.

Raw reports:

- `dev/local/reviews/00004-workflow-core-v1-fast-alice-06.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-blake-06.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-bob-06.md`

## Mandatory lens verdicts

| Lens | Verdict | Must-fix findings |
| --- | --- | ---: |
| Alice — consensus/architecture | pass | 0 |
| Blake — blind PRD-only | changes requested | 2 |
| Bob — doubt plus de-slop R1–R5 | changes requested | 3 |

Bob's rubric verdicts: R1 pass, R2 fail, R3 fail, R4 pass, R5 pass. The R2/R3 items are low-priority de-slop findings and do not independently block acceptance.

## Coordinator-reproduced must-fix root causes

### Bundle 1 — contract and deterministic correctness

1. **High — drained workflow state can re-enter active work.**
   - `src/ovcaq/workflow/transitions.py:84-93` chooses a row from `work.phase` alone. With `phase="done"` and terminal `next_phase=""`, `more_prds` resets the state to `build/build`.
   - `park()` also accepts the same drained state, moves its PRD to hold, and resets it to `build/build`.
   - Coordinator reproductions returned `('done', '') -> ('build', 'build')` and `{'phase': 'build', 'next_phase': 'build', 'held': True}`.
   - This violates the PRD test-strategy requirement that post-drain state remain terminal and the closed/fail-closed P02-T03 transition contract.

2. **High — `stall` silently reconciles a conflicting in-flight `park`.**
   - `src/ovcaq/workflow/records.py:666-680` checks only the PRD when `reconcile_any` is false; it does not require the pending operation's kind, site, and detail to match the requested stall.
   - Coordinator reproduction interrupted `park` at `AFTER_INTENT_BEFORE_MOVE`, then invoked `stall` for the same PRD with different site/detail. It returned `{'requested': 'stall', 'result_kind': 'park', 'parks_consecutive': 1}`.
   - This violates explicit recovery-kind behavior and retained decision DEC-076's conflicting-intent refusal. `park` may retain its deliberate reconcile-any behavior; `stall` must not.

3. **Medium — mandatory TEST-062 legacy/mixed completed-summary behavior is absent.**
   - `src/ovcaq/workflow/reports.py:303-319` directly indexes completed-record fields. A retained row missing `tasks_completed` raises `KeyError: 'tasks_completed'`.
   - TEST-062 explicitly requires nonzero retained totals, legitimate empty zeroes, and unknown sums for legacy or mixed completed records. Current tests cover those semantics only for metric rows.

4. **Medium — equal-key metric rows are input-order dependent.**
   - `src/ovcaq/workflow/reports.py:191-215` sorts sessions and convergence rows with partial keys. Distinct rows sharing those keys retain input order.
   - Coordinator reproduction with two same-batch/PRD/timestamp/phase session rows but different rendered signal/usage fields returned `False` for `render_metrics((a, b)) == render_metrics((b, a))`.
   - This violates P02-T08 and the PRD's deterministic-rendering exit criterion. The retained fixture's timestamps are unique, so its reversed-input test does not cover collisions.

### Bundle 2 — publication identity and availability

5. **High — deferred publication can be committed outside the configured directory.**
   - `src/ovcaq/workflow/records.py:239-268` creates/replaces/fsyncs by pathname after the directory check in `record_defer`; it does not bind those actions to an opened, identity-checked deferred-directory descriptor.
   - At `AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC`, renaming `runtime/deferred` away and creating a replacement yielded `{'returned_exists': False, 'relocated_exists': True, 'configured_dir_empty': True}` while the call returned successfully.
   - A full saga can consequently advance/commit while its durable record is absent from the configured ledger path. This violates P02-T06/P02-T07 durability and the no-lost-record exit criterion.

6. **Medium — an existing FIFO report target blocks before nonregular-file rejection.**
   - `src/ovcaq/workflow/reports.py:459-470` opens an existing output with blocking `O_RDONLY`, then validates it with `fstat`.
   - A subprocess publishing over a FIFO named `batch-report.md` timed out after 0.75 seconds; the intended regular-file guard was never reached. The state store's equivalent read uses `O_NONBLOCK` before type validation.
   - This is a reproduced availability defect in report publication and must return a bounded domain failure instead of hanging.

## Explicit requested verification

| Area | Result |
| --- | --- |
| WIP/hold identity at `AFTER_MOVE_BEFORE_APPEND` and `AFTER_APPEND_BEFORE_COMMIT` | closed for both directories: recovery/tasks survive replacement and reconcile exactly once after restoration |
| Retained metrics nonzero/empty/incomplete active-batch summaries | closed for the characterized rows; deterministic equal-key ordering remains open as finding 4 |
| Control characters and `StopIteration` containment | closed: lifecycle/report components reject controls; publication returns a domain error and preserves prior bytes |
| Recovery mutation fencing | closed for state service, frontmatter, transitions, completion, defer, and restore |
| Durability ordering | lifecycle/state ordering closed; deferred-directory identity remains open as finding 5 |
| Explicit recovery kind | stored/replayed explicitly, but conflicting in-flight `stall`/`park` behavior remains open as finding 2 |
| Provider-neutral workflow boundary | closed |
| Parser-generated command documentation | closed |

## Acceptance and source coverage

P02-T01, T02, T04, T05, T09, and T10 have complete inspected evidence. P02-T03 fails terminal drain behavior; P02-T06/T07 fail conflicting-intent and deferred-directory recovery guarantees; P02-T08 fails TEST-062 and total-order determinism. Every one of the 55 migration IDs is present in the manifest/current inventory, but TEST-062 is not behaviorally satisfied.

## Adjudicated non-blockers

- **External same-basename frontmatter path:** Blake reproduced that `--prd PATH` accepts external content when its basename matches the active PRD. The published command contract explicitly accepts a path, while neither the PRD nor accepted source row requires that path to resolve under WIP. Treat as deferred input-confinement hardening, not a PRD-00004 must-fix.
- **R2 redundant `source_stat is None` guard:** confirmed but harmless; defer cleanup.
- **R3 one-use `_workflow_context` wrapper:** confirmed low-impact maintainability preference; defer cleanup.
- Config/tier-map injection and runtime metrics production remain later-PRD integration seams.

## Fresh verification at reviewed HEAD

| Command | Result |
| --- | --- |
| `mise exec -- uv sync --all-groups` | passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/workflow/test_reports.py tests/packaging/test_installed_cli.py -q` | passed; 73 tests in 3.02s |
| `mise exec -- uv run pytest` | passed; 1,108 tests in 11.87s |
| `mise exec -- uv run ruff check .` | passed |
| `mise exec -- uv run ruff format --check .` | passed; 92 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | passed; 47 source files |
| `mise exec -- uv build` | passed; sdist and wheel built |
| `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..HEAD` | passed |

Additional reviewer checks: Alice 10 focused tests passed; Blake's workflow suite passed 202 tests; Bob's 26 focused tests passed. Passing gates do not cover the six coordinator-reproduced cases above.

## Verdict

**changes_requested** — six must-fix root causes remain in two bounded rework bundles. No implementation fix was made in FT-04R6.
