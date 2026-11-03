---
session: FT-04F7
next_session: FT-04R8
prd: dev/local/prds/wip/00004-workflow-core-v1.md
status: repaired_awaiting_fresh_review
date: 2026-09-05
base_sha: 47a8764760e1fedb82eb1514a344584fb7ad2f3e
head_sha: 8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7
implementation_base_sha: b43bf2c94d5eb0fddafca55542ef2570b45e8d52
---

# FT-04F7 repair and evidence handoff

Repairs for R7-01–R7-07 are committed at exact clean HEAD `8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`.
Commit: `fix(workflow): fence saga publication and honor command inputs`.

Repair range: `47a8764760e1fedb82eb1514a344584fb7ad2f3e..8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`.
Full implementation range for fresh review: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`.

## Inputs and scope

Started at the requested exact base with empty Git status. Read AGENTS.md, the WIP PRD,
consolidated fast-review-07 and its evidence attachment, current implementation/tests,
retained lifecycle and report fixtures, accepted P02-T01–P02-T10 coverage, resolved
shared discovery, coverage manifest, and every one of the 55 owned characterization
rows. The source-plan SHA-256 still equals
`43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.

No earlier review, earlier handoff, or raw lens report was read. No review skill or
review lens ran here. No autopilot state, implementation plan, PRD status/location,
or capsule was changed. No other PRD, branch, or worktree was started.

## Reproductions and repairs

The current review's Python observation script was extracted into a session-owned
temporary file and executed against the untouched base checkout before production
edits. Its observations reproduced all six behavioral findings. Exit zero meant the
observation script finished, not that the behaviors conformed. Installed-wheel
regressions additionally reproduced the command failures before their dispatch repairs.

| Finding | Observed before repair | Committed repair and regression evidence |
|---|---|---|
| R7-01 | A distinct held file created between the destination precheck and real rename was overwritten; recovery and unfinished tasks were cleared. | Darwin `renameatx_np` with `RENAME_EXCL` atomically refuses occupied destinations. The native declaration and flag were checked against the installed SDK's `sys/stdio.h`. Both stall/park regression injections create the competing file immediately before the native move helper; both original artifacts and durable intent survive. Moving the conflict aside permits successful recovery. |
| R7-02 | At `BACKUP_TEMP_FSYNCED` while recovery was recorded, replacing WIP, hold, or deferred let both sagas clear tasks/recovery and report success: six reproduced variants. A later added probe also reproduced replacement of the held PRD file during final state publication. | `StateStore.transaction` accepts a publication guard, invoked after each of the six publication boundaries, including after replacement and final directory fsync. Failures use the existing exact state/backup repair path. Saga directory descriptors, ledger lock, ledger membership checks, and held-file identity remain bound through commit. All 36 directory/operation/boundary combinations preserve exact state/backup bytes and recover once the original directory is restored. Both held-file replacement regressions pass. Intermediate move/record transactions also receive their evidence guards. |
| R7-03 | Empty identity created hold before refusing. `../escape` moved the PRD, stranded recovery at moved, and refused again on retry for both sagas. | Batch identity, requested PRD, full intent compatibility, generated operation ID, timestamp, and the complete candidate recovery schema are validated before hold creation or intent stamping. Eight missing/unsafe/control-character batch cases preserve state, backup, WIP bytes, and absent hold/deferred directories; public state correction then permits success without orphaned intent. |
| R7-04 | Custom project roots returned a drained selection and attempted the missing default state lock. CLI frontmatter discarded the service's validated deep floor because no available keys reached dispatch. | A narrow workflow input reader resolves CLI > project > user > defaults. Every workflow leaf accepts PRD/runtime/state overrides. Active abstract tier keys come from the selected agent's merged configured tiers or explicit repeated available-tier flags; model values remain opaque. Installed tests cover nested-cwd discovery, custom roots, stall/park precedence, independent state override, ledger/report locations, valid and unavailable tiers, and explicit tier override. Runtime path checks retain containment and symlink refusal. Parser-generated docs describe the inputs. |
| R7-05 | FIFO metrics input without a writer exceeded two seconds for both installed report and metrics commands. | The shared descriptor reader opens nonblockingly and validates a single-linked regular file before reading. Six bounded installed FIFO/directory/socket cases return a domain error, preserving state/backup and input inode without report publication. Missing input still yields empty rows. |
| R7-06 | The second consecutive park durably paused the workflow but exited zero with `ok: true`; human output showed only a revision. | Exit 4 and `status: systemic_park` propagate the committed halt. JSON includes `ok: false`, revision, and the saga result. Human stderr directs inspection of held PRDs and the pause reason. Installed first/second/exact-replay tests verify the breaker remains at two on replay. The retained kind-collision test now expects the required halt code. |
| R7-07 | AST/source measurements reproduced oversized functions and files, the impossible source-stat alternative, and the one-caller reset forwarding wrapper. | Split intent, move, record, and commit stages; isolate directory/ledger IO, CLI payload IO and workflow dispatch; extract render sections and frontmatter enum application. Split large tests by existing responsibilities. Remove the impossible stat branch and use the authoritative reset directly in the transition table. Guards, failpoints, parser authority, and acceptance assertions remain. |

Regression development initially exposed two empty-batch setup errors (running state
cannot have an empty ID) and two overlong Unix-socket fixture paths; these harness
issues were corrected. The independent missing-batch observation already reproduced
R7-03. Module splits also required relocating existing monkeypatch targets, including
the CLI payload-size constant. No acceptance test was dropped to clear these failures.

## Bounded simplification measurements

Function spans count `lineno` through `end_lineno`, inclusive, using Python AST.

| Function | Before | After |
|---|---:|---:|
| records._execute_operation | 169 | 47 |
| workflow command dispatch | 109 | 33 |
| workflow command registration | 76 | 15 |
| cli.main | 55 | 37 |
| frontmatter.parse | 51 | 41 |
| reports.render_audit | 59 | 27 |
| reports.render_report | 85 | 27 |
| reports.render_metrics | 61 | 37 |

`records.py`: 955 → 762 lines; `cli.py`: 838 → 548. New IO/dispatch modules are
34–314 lines. Every function in workflow and the touched CLI/configuration modules
is at most 50 lines; each scoped production file is under 800 lines.

The original 1,201-line saga test file is partitioned into 610-line `test_sagas.py`,
299-line `test_saga_identity.py`, 255-line `test_deferred_ledger.py`, and shared fixtures.
The original 1,174-line installed CLI file is partitioned into 239-line
`test_installed_cli.py`, 527-line `test_installed_sagas.py`, 348-line
`test_installed_reports.py`, and shared helpers. AST checks verified all 31 original
saga test functions and all 16 original installed CLI test functions remain exactly
once. The full count rises from 1,180 to 1,252 with 72 new parameterized cases.

## Verification at the committed implementation

Python 3.13.13, pytest 9.1.1, macOS. All checks ran on the final staged implementation,
which was then committed without production or test changes.

| Command | Result |
|---|---|
| `mise exec -- uv sync --all-groups` | Passed; 25 resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/workflow/test_reports.py tests/workflow/test_transitions.py tests/packaging/test_installed_cli.py -q` | 111 passed in 2.28s |
| Complete split/replacement and added coverage command below | 134 passed in 7.60s |
| `mise exec -- uv run pytest` | 1,252 passed in 18.60s; no failures or skips |
| `mise exec -- uv run ruff check .` | Passed |
| `mise exec -- uv run ruff format --check .` | Passed; 105 files |
| `mise exec -- uv run mypy src/ovcaq` | Passed; 51 source files |
| `mise exec -- uv build` | Passed; sdist and wheel |
| `git diff --check 47a8764760e1fedb82eb1514a344584fb7ad2f3e..HEAD` | Passed after commit |
| `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..HEAD` | Passed after commit |
| `git status --porcelain=v1` | Empty after commit |

Complete replacement/additional coverage:

```bash
mise exec -- uv run pytest \
  tests/workflow/test_saga_identity.py \
  tests/workflow/test_deferred_ledger.py \
  tests/workflow/test_saga_publication.py \
  tests/packaging/test_installed_reports.py \
  tests/packaging/test_installed_sagas.py \
  tests/packaging/test_workflow_inputs.py \
  tests/workflow/test_configuration.py -q
```

The full suite includes real process/lock/signal/durability checks, installed-wheel
execution outside the checkout, distribution content guards, provider-neutral
boundaries, retained report/lifecycle goldens, terminal drain, conflicting stall
refusal, legacy/mixed totals, equal-key ordering, active-batch metrics, control-character
refusal, explicit recovery kind, and parser/documentation equality.

## Accepted source obligations

| Source task | Current coverage |
|---|---|
| P02-T01 | selection/path tests; installed configured-root and nested-cwd tests |
| P02-T02 | frontmatter and application tests; configured and overridden active tier inputs |
| P02-T03 | all transition rows/rejections, full effects, CAS, terminal drain |
| P02-T04 | resume matrix, retained lifecycle fixtures, plan shape/ceiling policy |
| P02-T05 | exact per-PRD reset, batch preservation, completion summaries/idempotence |
| P02-T06 | deferred append/dedup/conflict, locking, directory identity and publication recovery |
| P02-T07 | all retained saga failpoints plus nonclobber move, early validation, publication guards and halt propagation |
| P02-T08 | report/audit/metrics goldens, legacy totals, stable ordering, active-batch filtering, bounded nonregular inputs/outputs |
| P02-T09 | configured workflow runtime/state inputs with retained path guards; no legacy runtime roots |
| P02-T10 | live parser registration and generated operations/state-protocol inventory equality |

All 55 owned inventory IDs read and retained in scope:
ART-012/013/014/016/017/026/036/039/040/041;
CMD-007/008/009/010/012/013/014/015/016/018/019/020/036;
DEC-071/076/077/078/079/080/081/082; ENV-025;
STATE-112/113/121;
TEST-001/002/005/006/008/012/013/014/015/016/017/018/019/020/021/027/029/038/052/062.

These results are repair evidence, not PRD closeout or fresh-review approval.

## Remaining scope and cleanup

No known consolidated finding remains unaddressed; independent review is pending.
The atomic move uses the supported macOS native primitive and refuses safely where
that primitive is unavailable. Linux implementation/qualification remains downstream;
no Linux claim is made. The configuration addition is limited to workflow inputs.
Shared runtime configuration policy, model routing, provisioning, and launcher execution
remain with their owning downstream PRDs. Filesystem evidence is checked throughout
publication; this does not claim protection from unrelated changes after completion.

The temporary reproduction helper was removed. No worktree, orphan branch, executed
plan, or repository-local temporary plan was created. Existing local plans, prior
reviews/handoffs, fixtures and unrelated artifacts remain. This handoff resides under
the repository's ignored `dev/local/` tree, so retaining it leaves Git clean.

## Fresh review handoff — STOP

Start **FT-04R8** in a fresh session from exact clean HEAD
`8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`. Its full implementation range remains
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`.

Require every isolated lens: **Alice consensus**, **Blake blind/PRD-only**, and
**Bob doubt plus de-slop R1–R5**. Give Blake only the PRD/source-contract access and
blind rubric, without this repair narrative or consolidated findings. Each lens
must have a fresh isolated context; no lens runs in FT-04F7. Apply the fresh-review
workflow in that next session. Do not infer convergence from passing test counts.

FT-04F7 ends here. No autopilot-state handoff stamp is authorized or needed.
