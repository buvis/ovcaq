---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
session: FT-04R7
review: 7
date: 2026-09-05
head_sha: 47a8764760e1fedb82eb1514a344584fb7ad2f3e
implementation_base_sha: b43bf2c94d5eb0fddafca55542ef2570b45e8d52
repair_base_sha: c4b9ea38d2e11eac4a1de1a71bd7d4134142e661
reviewers: alice,blake,bob
status: changes_requested
must_fix_groups: 7
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
---

# PRD 00004 — FT-04R7

**Changes requested: seven reproduced must-fix groups (four High, three Medium).** Every required check passes, but filesystem races, late validation, and command integration leave the full PRD contract incomplete.

Diff range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..47a8764760e1fedb82eb1514a344584fb7ad2f3e`

Cycle-06 repair range: `c4b9ea38d2e11eac4a1de1a71bd7d4134142e661..47a8764760e1fedb82eb1514a344584fb7ad2f3e`

codex_rung_guard: not fired

## Review provenance

Started from the exact requested HEAD with empty `git status --porcelain=v1`. Reviewed the full implementation range, current code/tests/retained fixtures, AGENTS.md, the WIP PRD, accepted source plan, coverage manifest, resolved discovery, and all 55 characterization/inventory rows owned by PRD 00004. The source-plan SHA-256 matches the accepted `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.

Only coordinator and Alice read the permitted current `rework-06.md`. No earlier review, earlier handoff, preexisting raw lens report, settled-decision ledger, or capsule was read. Retrieval/history packs were intentionally omitted. The existing autopilot state identifies PRD 00003; its task store was not treated as PRD 00004 context, and it was not mutated. This is a standalone review, with no task creation or state stamping.

All mandatory lenses ran in fresh native subagents with `fork_turns=none`, using independently assembled installed review-agent personas and full rubrics. Blake received only the PRD, blind rubric, source-reference permission, and read restrictions, then found implementation himself. Bob remained static-only. Native Claude Task agents are unavailable in this host, so Alice/Blake used the available Codex subagent engine; the Codex helper refused nested execution with exit 3, so Bob used the native fallback. The optional Gemini/Carl helper also refused nested execution and was skipped. All three disciplines completed, but this run does not claim cross-provider model diversity.

Coordinator-originated commit/preflight counterexamples were sent to Alice for adversarial assessment. They were not sent to Blake or Bob and are not counted as additional independent lens votes. No reviewer saw another lens's report before finishing. Raw lens text was saved after all reviewers completed.

## Consolidated root causes

Consensus counts lens agreement, excluding the coordinator. Severity and closure depend on independently reproduced behavior, not vote count.

| ID | Severity | Root cause / impact | Lenses | Contract |
|---|---|---|---|---|
| R7-01 | High | The verified PRD move uses an overwriting rename after a separate existence check; concurrent held work can be destroyed. | Blake [1/3] | P02-T07; DEC-076–078; TEST-014/017 |
| R7-02 | High | Filesystem evidence is verified before the state store's commit I/O; directory replacement during publication still clears tasks and recovery. | Alice [1/3] | P02-T07; durable-boundary exit criterion |
| R7-03 | High | Batch identity is validated after lifecycle filesystem effects; unsafe identifiers strand a moved recovery, and missing identity creates hold before refusal. | Alice [1/3] | P02-T07; DEC-076; TEST-014 |
| R7-04 | High | Installed workflow dispatch constructs fixed/incomplete configuration inputs; configured roots are ignored and valid tier hints are discarded. | Blake [1/3] | P02-T01/02/09; TEST-002; PRD configured-path and abstract-tier features |
| R7-05 | Medium | Metric input uses a blocking open without regular-file validation; FIFO input hangs both report commands. | Alice, Bob [2/3] | P02-T08; explicit error handling / bounded report operation |
| R7-06 | Medium | The CLI drops the saga's systemic-halt outcome and exits zero after the second consecutive park. | Alice [1/3] | P02-T07; DEC-082; TEST-016 |
| R7-07 | Medium | New orchestration is oversized and retains avoidable forwarding/defensive code; measured review quality limits fail. | Alice, Bob [2/3] | Consensus R12/R13; mandatory de-slop R1–R3 |

### R7-01 — move must refuse destination replacement atomically

`src/ovcaq/workflow/records.py:535` checks the destination, then line 545 calls `os.rename`, which may replace it. The coordinator wrapped that existing syscall boundary to create `hold/<prd>` with distinct content after the precheck and immediately before the real rename. The built-wheel saga returned success, replaced the held content with the WIP content, cleared recovery, and reset the unfinished task. No directory replacement or symlink is needed.

Use a move/publication primitive that refuses an occupied destination atomically on the supported platform. Preserve recovery intent and both artifacts on conflict; another preceding stat check is insufficient. Regressions must create the competing destination at the syscall boundary and require its original bytes to survive.

### R7-02 — keep evidence valid through state publication

`records.py:696` calls `verify()` only at mutator entry. `StateStore.transaction` subsequently validates and publishes backup/state bytes (`src/ovcaq/state/store.py:140`, `:145`) without rechecking saga evidence.

The coordinator used the state store's existing `BACKUP_TEMP_FSYNCED` hook only when durable recovery was `recorded`. Renaming configured deferred/WIP/hold away and creating a replacement at that point let both stall and park return success and clear recovery/tasks. Deferred replacement left no ledger at the configured path; hold replacement left no PRD in configured hold. These are six reproduced variants of one finalization defect. The hook fires before state publication; this finding does not demand protection against arbitrary changes after an already completed operation.

Bind the final publication to validated filesystem evidence and retain recoverable intent if the relevant names change before finalization. Extend tests beyond transaction entry to the store's actual publication boundaries, preserving state/backup failure guarantees and the held descriptors/ledger lock. The current `test_saga_checks_deferred_identity_inside_state_transaction` swaps before calling the real transaction and misses this interval.

### R7-03 — validate the complete batch identity before side effects

`records.py:768` creates hold before checking `batch.id` at line 800; printable/path-safe validation occurs still later in `_open_deferred_ledger`, after the move and `moved` state transaction.

With a schema-valid `batch.id='../escape'`, both stall and park move the PRD from WIP to hold, leave recovery at `moved`, and reject the identifier. A second invocation fails identically. Recovery fencing then prevents public state mutations from correcting the batch ID. With an empty batch ID, the call leaves state bytes unchanged but creates hold before refusal, contradicting DEC-076.

Validate required batch identity and all operation inputs that can fail deterministically before creating lifecycle directories or stamping intent. Add missing/unsafe batch tests requiring unchanged state/backup and lifecycle artifacts, plus successful operation after correction without an orphaned recovery.

### R7-04 — propagate configured command inputs

`src/ovcaq/cli.py:564` and `:610` construct lifecycle paths from the literal default; `_workflow_context` also obtains the fixed runtime state path. The coordinator placed a real WIP PRD and valid state under custom roots and wrote the source plan's `[workflow] prd_root` / `runtime_root` configuration. Installed `workflow select` returned drained; `resume-target` attempted the missing default lock and exited 2. The pure path resolver's configurable arguments do not make those installed commands configurable.

`cli.py:619` also omits `available_tiers`. In a separate wheel reproduction, the service validated and committed a `deep` tier floor using `available_tiers={'deep'}`. Running the identical PRD through the CLI warned that the tier was unavailable, exited zero, and removed the floor. The pure parser's missing-tier warning is correct when a real active map lacks the key; dispatch currently never supplies any map.

Provide resolved lifecycle/runtime roots and active abstract tier keys to the installed command boundary, preserving configured precedence and generated documentation. The broad project/user configuration framework has downstream ownership in PRD 00005, and provider/model routing remains external to workflow. This repair should satisfy PRD 00004's explicitly required configured inputs and retained TEST-002 override behavior without importing runtime/provider policy into pure workflow modules; it is not authorization to execute PRD 00005.

### R7-05 — refuse nonregular metric input before reading

`src/ovcaq/workflow/reports.py:133` calls `Path.read_text` before any file-type check. The coordinator created `metrics.jsonl` as a FIFO with no writer. Both installed `workflow render metrics` and `workflow render report` exceeded a two-second subprocess timeout. The state bytes and FIFO inode stayed unchanged. The repaired output-target reader cannot help because CLI dispatch loads metrics first.

Open metric input nonblockingly, validate the opened descriptor as a regular file before reading, and return a domain error promptly for FIFO/nonregular input. Retain the absent-ledger behavior and add bounded subprocess coverage for both commands.

### R7-06 — preserve the systemic halt at the command boundary

`src/ovcaq/cli.py:682` converts the park result to an ordinary mutation result; `main` returns zero at line 826. The coordinator parked two distinct PRDs sequentially. The second call committed phase `paused`, returned `systemic_halt: true`, and still exited zero with `ok: true`. Human mode provides only a revision, not the halt outcome.

Propagate a distinct halt status and actionable human/machine output after the successful durable pause. DEC-082 explicitly requires a halt code; the library result flag alone does not satisfy it. Add installed tests for first park, second park, and exact replay without incrementing the breaker.

### R7-07 — simplify within existing boundaries

Independent AST/source measurements confirm the new `records._execute_operation` spans 169 lines, CLI workflow dispatch 109, command registration 76, and the audit/report/metrics renderers 59/85/61. The evidence attachment lists the full measured production violations. Newly oversized files are `records.py` (955), `cli.py` (838), `test_sagas.py` (1,201), and `test_installed_cli.py` (1,174).

Separate existing intent/move/ledger/commit stages and CLI handlers/render sections while retaining explicit ownership, resource lifetimes, named failpoints, parser authority, and all coverage. Partition large test modules by existing responsibilities. Do not expand this into unrelated refactoring of preexisting oversized files.

Within the same bounded simplification pass, remove the impossible `source_stat is None` alternative inside `if source_exists` (`records.py:543`) by branching on the stat results directly, and replace the one-caller `_more_prds` forwarding wrapper (`transitions.py:61`) with the existing reset function in the transition table. These are separate concrete symptoms of unnecessary implementation bulk, not additional correctness defects. A line-to-spec ratio alone is not evidence of bloat and is not an acceptance target; no failpoint, guard, or retained test should be removed to reduce counts.

## Explicit repair and regression scrutiny

| Area requested for cycle-07 | Result and evidence |
|---|---|
| Terminal drain | Verified: every outcome is refused after done/empty next phase; park/stall refuse before filesystem effects. Direct and installed tests pass. |
| Conflicting stall intent | Verified: PRD/kind/site/detail conflicts refuse; park's deliberate reconciliation uses recorded kind. |
| TEST-062 completed totals | Verified: empty zeros, retained nonzero values, incomplete/filename-only legacy and mixed rows yield per-field unknown totals. Installed legacy tests inject a read-only projection because strict v1 storage rejects legacy rows; no importer is claimed. |
| Equal-key metrics/convergence ordering | Verified: canonical JSON tie-breakers produce identical output under reversed colliding rows, including installed metrics tests. |
| Deferred-directory identity through publication and saga commit | Publication and transaction-entry tests pass; final commit remains open under R7-02. |
| FIFO/nonregular report output targets | Verified: FIFO, directory, socket, symlink/hardlink safeguards use the shared nonblocking regular-file reader. Adjacent metric input remains open under R7-05. |
| WIP/hold identity and replay proof | Existing before-move/after-move/before-commit directory tests and no-intent held-PRD proof tests pass. The actual rename race and commit-publication interval remain open under R7-01/R7-02. |
| Recovery mutation fencing | Verified across public state mutations, restore, workflow transitions, completion, frontmatter and defer when recovery is already active. This guard makes R7-03's stranded operation material. |
| Durability ordering | Existing rename and ledger replacement replay fsync ordering passes; directory parent synchronization and state-store failure tests pass. Publication identity is separately R7-02. |
| Explicit recovery kind | Verified for exact replay, stall/park collisions, pending-stall reconciliation and breaker behavior. CLI halt propagation remains R7-06. |
| Active-batch metrics | Verified: report/metrics filtering and aggregate unknown-versus-zero behavior pass. |
| Control-character rejection | Safe component validation and installed heading/path refusal tests pass. Batch validation must occur earlier in the saga under R7-03. |
| Provider-neutral boundaries | Workflow imports/strings and installed distribution boundaries pass; source inspection found no provider/runtime leakage. |
| Parser-generated documentation | Live-parser equality checks for operations and state-protocol inventories pass. |

## Source-task coverage

One row per accepted source task. Evidence applies to the complete reviewed range at the pinned HEAD; these rows do not mark the PRD closed.

| Task | Inspected implementation and evidence | Status |
|---|---|---|
| P02-T01 | selection.py/paths.py; selection ordering, absent/invalid directories, hold exclusion, configurable resolver tests | Pure behavior verified; installed configuration R7-04 |
| P02-T02 | frontmatter.py; defaults/enums/integers/opt-ins, overwrite ownership, active-PRD and CAS tests | Service behavior verified; CLI tiers R7-04 |
| P02-T03 | transitions.py; all six rows, rejection matrix, rework full effects and terminal drain | Functional behavior verified; R7-07 quality |
| P02-T04 | resume.py/policy.py; retained lifecycle fixtures, recovery priority, plan shape/ceiling and overrides | Verified |
| P02-T05 | records.py reset/summary/completion; exact owner reset, batch preservation, idempotence and mismatch refusal | Verified |
| P02-T06 | deferred ledger append/dedup/conflict, sidecar locking, directory-bound publication and retry tests | Standalone append verified; saga commit integration R7-02 |
| P02-T07 | park/stall intent, move, record, reset, commit; all retained and added failure boundaries | R7-01/02/03/06 |
| P02-T08 | audit/report/metrics projections, retained metrics and v1 goldens, section replacement/final archive | R7-05; R7-07 quality |
| P02-T09 | neutral runtime defaults and no legacy-root strings; service path injection and installed commands | Installed configuration R7-04 |
| P02-T10 | command registry and generated docs equality/installed help tests | Verified |

The 55 owned source IDs were individually read through `migration.toml` and `current_system.toml`: ART-012/013/014/016/017/026/036/039/040/041; CMD-007/008/009/010/012/013/014/015/016/018/019/020/036; DEC-071/076/077/078/079/080/081/082; ENV-025; STATE-112/113/121; TEST-001/002/005/006/008/012/013/014/015/016/017/018/019/020/021/027/029/038/052/062. The fresh-state model uses committed explicit recovery intent and verified lifecycle evidence; no legacy importer, permanent aliases, or provider marker parser is required by this report.

Phase exits: lifecycle fixtures match under v1 and provider neutrality passes. Recoverability at every durable boundary does not pass because R7-01–03 remain. The full PRD cannot converge on test counts alone.

## Verification

| Required command | Fresh result |
|---|---|
| `mise exec -- uv sync --all-groups` | Passed; 25 resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/workflow/test_reports.py tests/workflow/test_transitions.py tests/packaging/test_installed_cli.py -q` | 173 passed in 5.87s |
| `mise exec -- uv run pytest` | 1,180 passed in 14.57s; 0 failed, 0 skipped |
| `mise exec -- uv run ruff check .` | Passed |
| `mise exec -- uv run ruff format --check .` | Passed; 92 files |
| `mise exec -- uv run mypy src/ovcaq` | Passed; 47 source files |
| `mise exec -- uv build` | Passed; sdist and wheel built |
| `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..HEAD` | Passed |

Python: 3.13.13 on macOS. All must-fix behavior was independently reproduced by the coordinator in temporary projects, including against the freshly built wheel from outside the checkout. The [evidence attachment](00004-workflow-core-v1-fast-review-07-evidence.md) preserves the exact runnable observation script, outputs, and mechanical measurements. Its probes deliberately demonstrate missing guarantees and are not additional passing conformance tests.

## Alice

[Raw cycle-07 report](00004-workflow-core-v1-fast-review-07-alice.md). Completed consensus/architecture review of the full diff, source contract and current permitted handoff. Findings map to R7-02/03/05/06/07. Reported an additional workflow/state suite pass after sandbox-only failures were rerun; coordinator's required suite above is the authoritative count for this report.

## Blake

[Raw cycle-07 report](00004-workflow-core-v1-fast-review-07-blake.md). Completed blind PRD-only review, independently locating code and reproducing the held-file overwrite and configured-path behavior. Findings map to R7-01/04. All B1–B19 verdicts are present. A lane-local socket restriction was resolved on retry; it is not a product defect.

## Bob

[Raw cycle-07 report](00004-workflow-core-v1-fast-review-07-bob.md). Completed static doubt plus de-slop review. F1 maps to R7-05; F2–F4 join R7-07. His VERIFY V1 is discharged by every fresh required check above. His dismissal of directory identity at inspected boundaries does not cover the later state-publication reproduction in R7-02.

| De-slop rubric | Lens result | Consolidated disposition |
|---|---|---|
| R1 — bloat ratio | fail | Use measured oversized functions/files in R7-07; ratio alone is not a finding. |
| R2 — defensive impossibility | fail | Confirmed redundant impossible branch, R7-07. |
| R3 — single-caller abstraction | fail | Confirmed forwarding wrapper, R7-07; recovery transaction wrapper is justified. |
| R4 — paraphrasing comments | pass | No must-fix identified. |
| R5 — framework-verification tests | pass | Parser/docs and filesystem tests enforce product contracts. |

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

All required per-rule lines were mechanically checked: Alice/Bob consensus sets, Blake B1–B19, and Bob D1–D5; none are missing. Raw verdicts remain unchanged in the lens files. The installed `check_review_file.py --require-codex-guard` shape gate passed.

## Consolidation dispositions

The installed `consolidate_findings.py` ran successfully without historical ledger input. It emitted 13 candidate rows. Coordinator grouping merges five quality rows into R7-07 and two missing-configuration rows into R7-04, and discharges Bob V1 with fresh checks, leaving seven actionable root-cause groups. FIFO and measured quality have two-lens agreement. No single-lens defect was dismissed for lacking consensus, and no reproduction was converted into a repair in this session.

## Fresh-session next step

Start **FT-04F7** from clean HEAD `47a8764760e1fedb82eb1514a344584fb7ad2f3e`, using this consolidated report and its evidence to repair R7-01–R7-07. Preserve all cycle-06 regressions and accepted source obligations. After repairs and the required checks, hand off and stop; run **FT-04R8** with every mandatory isolated lens in a new session at the resulting exact clean HEAD.

No implementation was repaired; autopilot state, implementation plans, PRD location/status and capsule remain unchanged. No next PRD was begun, worktree/branch created, or commit made. Cycle staging files and the coordinator's temporary reproducer are removed after retaining the review/evidence artifacts; existing plans and unrelated temporary material are untouched.

Verdict: 7 findings
Tests: 1180 passed, 0 failed, 0 skipped (suite run this cycle)
