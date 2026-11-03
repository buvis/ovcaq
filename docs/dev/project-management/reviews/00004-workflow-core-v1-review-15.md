---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
review: 15
date: 2026-09-13
head_sha: 7b41798c80e06a2c341d75116a09c752203797f4
reviewers: alice,blake,bob
consensus_engine: legacy
status: completed-review-paused-data-loss-risk
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/reviews/bob-output-00004-15-20260913.txt.receipt.json
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: unavailable
---

# PRD 00004 — cycle 15 review

Diff range: `7291d9f80c5b7a55f63c406552e5b3e27025acad..7b41798c80e06a2c341d75116a09c752203797f4`

codex_rung_guard: fired (5 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude

**CHANGES_REQUESTED — review complete; PAUSE for detected data-loss risk.**

The installed-wheel probe performs real ancestor replacement and reparents the same runtime inode beneath the replacement. Both direct append and exact replay return success without a later fsync of the ancestor's parent or the replacement ancestor. Runtime identity stays unchanged, bypassing the new verifier. This is syscall-order evidence of a durability gap, not a physical power-loss simulation.

The installed [run-autopilot skill](/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.2/skills/run-autopilot/SKILL.md) mandates “Detected data-loss risk” → “PAUSE” in both modes. This safety rule overrides ordinary loop-mode cap deferral. The pause is committed through the installed state CLI; tasks 9 and 10 are queued only. No repair, cycle increment, cap change, PRD move or finalize handoff occurred. Cycle **15**, cap **2**, batch **202609062243**, original base `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`, and all 18 prior completed tasks/attempts are preserved. The task snapshot is now **18/20 complete**.

## Consolidated findings

The installed consolidation script completed successfully; its [raw table](00004-cycle-15-consolidation-raw.md) preserves all 13 issue lines. It did not merge Alice's and Bob's origin finding because they named different affected files, nor auto-dismiss Blake's frontmatter paraphrase. Coordinator consolidation merges only that duplicate pair and applies Blake's three source-supported retractions: **12 distinct findings = 7 FIX + 0 VERIFY + 2 KNOWN + 3 DISCARDED**. The actionable set is two High, two Medium and three Low findings. The prior check queue and this cycle's queue are empty; the mechanical checks emitted no findings.

| ID | Consensus | Severity | Finding | File | Disposition |
|---|---|---|---|---|---|
| R15-01 | 1/3 (Alice adjudication of coordinator evidence) | high | Replacing an already confirmed ancestor and reparenting the same runtime inode beneath its replacement before ledger open is accepted by direct append and exact replay, without any later fsync of the ancestor's parent or the replacement ancestor. Runtime-only identity checks do not preserve the confirmed ancestry through successful publication. | src/ovcaq/workflow/_files.py:306 | FIX |
| R15-02 | 2/3 | high | F1: per-result installed-origin verification dropped from test_rework_12 `_invoke`/`_await_event`/`_finish` and test_rework_13 `_invoke`; actor results still carry `origins` but nothing asserts them, contrary to task 6 ("on every subprocess result and event") and task 7/8 ("preserve installed-wheel origin coverage") | tests/packaging/test_rework_13.py:71 | FIX |
| R15-03 | 1/3 | medium | F2: `_open_deferred_ledger` opens `deferred` via dir_fd with no wrapping, so a symlink/regular-file `deferred` (ELOOP/ENOTDIR) or a vanished dir on the second open surfaces raw errno text with the bare name 'deferred'; pre-change `_open_lifecycle_directory` reported "deferred directory is not a real directory: <full path>" | src/ovcaq/workflow/_files.py:325 | FIX |
| R15-04 | 1/3 | medium | F3: `test_installed_defer_refuses_runtime_replacement_before_deferred_creation` and `..._during_ledger_publication` are ~50-line near-duplicates (only mode string and assertion helper differ), both at the 50-line ceiling | tests/packaging/test_rework_13.py:242 | FIX |
| R15-05 | 1/3 | low | F4: B6 unresolved: `opened` reused for parent fstat then level fstat despite "keep parent and child identities legible" acceptance | src/ovcaq/workflow/_files.py:277 | FIX |
| R15-06 | 1/3 | low | F5: distance-1 (runtime.parent) replacement coverage removed when parametrize moved to (3, 5) | tests/packaging/test_rework_13.py:192 | FIX |
| R15-07 | 1/3 | low | F6: `search_capability()` still returns `euid`, `read_denied`, `search_fsync` constants no test reads | tests/packaging/rework_13_scripts.py:172 | FIX |
| R15-08 | 1/3 | low | F7: `_O_SEARCH` falls back to `os.O_EXEC`; on musl Linux O_EXEC == O_PATH, whose descriptors reject fsync, so every ancestor open in `_ensure_directory_chain` would fail even when readable (suspected, pre-existing via os.O_SEARCH there) | src/ovcaq/workflow/_files.py:25 | KNOWN |
| R15-09 | 1/3 | low | F8: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay for packaging tests (base collection failed on missing packaging_support helpers); host reports 1364 passed / 0 skipped at 7b41798 | N/A | KNOWN |
| R15-10 | 1/3 | high | Effective `catchup`, `design`, `design_gate`, and `pause_on_ambiguity` frontmatter values are returned to the caller but discarded from committed state; only the review cap and tier survive, so restart/resume cannot reproduce the declared workflow policy and `catchup: skip` still follows `batch.catchup` | src/ovcaq/workflow/frontmatter.py | DISCARDED |
| R15-11 | 1/3 | high | PRD discovery converts missing, unreadable, symlinked, or non-directory lifecycle roots into empty candidate lists, allowing an inaccessible `wip` to fall through to backlog or an invalid tree to report `drained`; this can skip higher-priority work or prematurely terminate a batch instead of surfacing the invalid-directory error required by the selection test strategy | src/ovcaq/workflow/selection.py | DISCARDED |
| R15-12 | 1/3 | high | `defer_record` validates active batch/PRD with an unlocked read and then publishes the external ledger independently, without revision CAS or durable recovery intent; a concurrent completion/reset can therefore leave a successfully written deferred record attributed from stale state | src/ovcaq/workflow/records.py | DISCARDED |

## Adjudication

- **R15-01 — FIX:** Installed-wheel direct/replay probe reproduces successful return after ancestor replacement and reparenting of the same runtime inode, with no later confirmation of the replacement directory entries. Detected data-loss risk mandates pause. Final parent descriptor remains open, but no ancestor identity is reverified after yield.
- **R15-02 — FIX:** Alice and Bob independently found removed assert_installed calls; coordinator verified all four result/event consumers. Initialization retains a check, but it does not establish the origin of every later subprocess.
- **R15-03 — FIX:** Coordinator source-runtime probe reproduces symlink and regular-file refusal as bare "deferred" ENOTDIR, omitting the configured path. Both objects remain untouched. Restore diagnostic context while preserving safe refusal and causal errno.
- **R15-04 — FIX:** Two newly added direct/replay tests have the same setup/action/assert/retry flow with different injection mode and boundary assertion helper. Parametrize the shared flow while retaining scenario-specific chronology and state/record assertions.
- **R15-05 — FIX:** Previous R14-06 remains open: the implementation still assigns parent and child fstat results to opened. Rename the two identities without altering behavior.
- **R15-06 — FIX:** Changing distances to (3, 5) removed the former immediate-parent case. The runtime-replacement cases target the runtime itself; restore distance 1 alongside the new distant cases.
- **R15-07 — FIX:** Actor capability metadata euid/read_denied/search_fsync is no longer consumed; remove these emitted keys while retaining real permission and fsync checks.
- **R15-08 — KNOWN:** Linux is explicitly excluded from the current personal-cutover milestone. Bob's musl-specific concern is unverified here and attributed as a suspected pre-existing limitation, not a confirmed host defect.
- **R15-09 — KNOWN:** Fresh suite passes 1364/0/0; other required gates reuse same-HEAD successful records. Approved replay produced two red tests but two packaging files failed collection at base, so their behavioral fail-first binding remains limited. No broad rebuild is queued solely to repeat already recorded gates.
- **R15-10 — DISCARDED:** Retracted by Blake after source-only adjudication: docs/state-protocol.md:321-323,327 and frozen inventory classify these controls as derived and allocate ownership to existing v1 fields. No new evidence invalidates the prior ledger decision.
- **R15-11 — DISCARDED:** Retracted by Blake: mandatory selection source specifies WIP priority/fallback/drain but no required error outcome for absent/invalid/symlink directories. PermissionError from iterdir is not caught. Test strategy naming these cases is not an error contract.
- **R15-12 — DISCARDED:** Retracted by Blake: CMD-010 and STATE-112/113 define an independently locked PRD/batch-attributed append; recovery.operation supports park/stall only. A later state change does not invalidate immutable attribution from the validated invocation.

R15-01 was discovered and reproduced by the coordinator before Alice received it for adjudication. Alice confirmed it after her initial report; this is explicitly a prompted confirmation, not an independent initial discovery or a fourth reviewer vote. Bob did not review this new probe and classified the original runtime-replacement interleaving as resolved. His original finding dispositions and passing R verdicts are retained unchanged below.

One factual correction to Alice's supplement: the final ancestor/parent context remains open while the generator yields the runtime descriptor; it does not close literally every ancestor descriptor before publication. The defect is that those ancestor identities are not revalidated after yield. Runtime-only identity checks still accept the demonstrated reparenting. The [probe](00004-cycle-15-installed-reparent-probe.json) establishes this directly.

The installed probe used a fresh temporary wheel installation, isolated `-I` subprocesses for direct append and exact replay, and a module hash equal to the reviewed checkout. Both subprocesses were reaped and the installation/scenario directories removed. The [diagnostic probe](00004-cycle-15-diagnostic-probe.json), run through the existing project interpreter, separately confirms F2's missing full path for file and symlink cases and preservation of the existing objects. Its first uv launch failed on cache access; direct interpreter execution avoided that unrelated cache access.

Protocol B: this is the fifth cycle in the ancestry-confirmation family (cycles 11–15). Prior fixes confirmed existing ancestors, then checked identity between adjacent reopens, then retained the runtime descriptor through ledger publication. The remaining gap is the lifetime of ancestor identities: a replacement ancestor can contain the same runtime inode. Carry/reverify the full chain or reconfirm newly adopted entries; another runtime-only check cannot close it. Three-or-more recurrence requires escalation, and observed data-loss risk independently requires a pause. R14-06's parent/child naming requirement is also still open rather than newly invented.

The two KNOWN items and three discards were appended to the settled ledger with verbatim finding text and reasons. Blake's [source-only supplement](00004-cycle-15-blake-adjudication.md) retracts all his findings and supplies corrected B verdicts; the original failed verdicts remain below. No source or sibling review history was provided to Blake.

## Source coverage and verification

The [source audit](00004-cycle-15-source-audit.json) verifies accepted-plan SHA-256 `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`, the frozen inventory digest, all **55** PRD-owned migration rows and all eight existing target routes. Reviewers reconciled P02-T01–P02-T10 and phase exits. After adjudication, T01–T05, T08 and T10 remain satisfied; T06/T07/T09 retain the shared ledger ancestry defect. Phase A remains satisfied. Phase B is open; Phase C's functionality/docs/dependency guards pass, but touched installed-command regression provenance is weakened until R15-02 is repaired.

The fresh full suite passed **1364 tests in 26.15s**, with zero failures/skips and two pytest temporary-directory cleanup warnings. It was run because the same-HEAD last-verification record had null counts and retained an earlier failing full-suite command. The fresh suite supersedes that failure after the repair. Sync, Ruff lint, Ruff format, mypy and build reuse their recorded exit-0 commands at this exact HEAD; reused checks are not claimed as new executions. [Verification evidence](00004-cycle-15-verification.md) distinguishes these paths. Blake additionally ran the workflow subset (373 passed); that narrower run does not replace the full suite.

The [mechanical blocks](00004-cycle-15-mechanics.md) report changed Python functions at or below 50 lines, 24 test functions inspected in four files, no tautological shape findings. The first replay failed to create a worktree in the sandbox. The exact approved retry completed: **2 touched tests ran, both failed against base, none passed; 2 test files failed base collection**. Collection failure is not proof of behavioral regression binding; the packaging replay limit is retained explicitly. The temporary worktree was removed. Engram pack was attempted and failed because the repo is not registered; no pack supplied. No design doc exists.

Complete state/schema validation, task-count consistency, all raw R/B/D verdict sets, saved-review shape, doubt-roster constraint and the host's receipt/hash validation are executed explicitly. No Claude hook is assumed. Final results are in [final audit](00004-cycle-15-final-audit.json).

## Dispatch provenance

- Alice: native OpenAI **gpt-5.6-sol**, logical sonnet, `fork_turns=none`, `/root/alice_r15`. Complete installed persona/checklist/R rubric, current context, prior findings and settled ledger. Initial report preserved separately; coordinator-probe adjudication is identified as such.
- Blake: native OpenAI **gpt-5.6-sol**, logical sonnet, `fork_turns=none`, `/root/blake_r15`. Complete installed persona, PRD and B1–B19; mandatory PRD-linked accepted source specifications. No work plan, diff, changed-file list, design, state, history or sibling findings. Follow-up supplied only source-check questions about his own findings.
- Bob: external Claude Opus via the exact authorized helper with approved network access; actual raw model **claude-opus-5**, fresh session, exit 0. Complete Bob persona/checklist/R rubric plus full Eve-derived doubt/de-slop appendix and D1–D5. Immutable text/raw hashes, root, PRD, cycle and session identity are in the receipt. No Codex thread id emitted.
- Carl: installed use-gemini helper exit **3**, “refusing nested dispatch (already inside a CLI agent).” No provider inference/output, no guard removal, no retry of unchanged refusal, no permanent-unavailability latch.
- Watcher: native **gpt-5.6-luna**, logical haiku, scaffolding only, `/root/watcher_r15`; removed Carl after terminal refusal and returned DONE after Bob. Every dispatched process and agent is terminal.

The native reviewers share one model. Claude Bob supplies the independent provider voice. The Codex guard counts exactly five task entries with a Codex attempt: 1, 2, 4, 7, 8. Fable is not an available native host model; no Eve/Fable dispatch occurred. The mandated guard suffix represents the explicit **Claude Bob host substitution** supplying the non-Codex doubt voice, not a claim that Eve was dispatched.

## Follow-up tasks

- **9 — [D15] Preserve confirmed ancestry across runtime reparenting (M):** R15-01, R15-03, R15-05. Installed classifier: opus / algorithmic_risk (shared filesystem state across processes).
- **10 — [D15] Restore installed-origin proof and preserve test coverage (M):** R15-02, R15-04, R15-06, R15-07. Installed classifier: sonnet / test_port; depends on task 9.

All seven assigned findings appear verbatim in task descriptions. Tasks remain pending; `rework_task_ids` remains empty because Phase 6 was not entered. Operator recovery must authorize repairs and preserve a fresh work/review session boundary. The PRD has no frontmatter model floor.

## Alice

[ALICE] 🟡 The shared test cleanup removed parent-side installed-origin verification from every actor/invocation result in both rework suites, although D13 explicitly required retaining that check for every subprocess; `origins` is still emitted but never asserted, so a subprocess importing checkout code instead of the installed wheel can pass these regressions. Restore `assert_installed(value["origins"], installed, required_module)` in `_invoke`, `_await_event`, and `_finish` or an equivalent common wrapper. | File: tests/packaging/test_rework_12.py:52 | Task: P02-T06/P02-T09
R1: fail
R2: fail
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass
P02-T01: pass — selection and configured lifecycle resolution remain accepted and unchanged by this incremental diff.
P02-T02: pass — frontmatter parsing/defaults and warning behavior remain accepted and unchanged.
P02-T03: pass — transition table and compound phase completion remain accepted and unchanged.
P02-T04: pass — resume mapping and plan-size policy remain accepted and unchanged.
P02-T05: pass — reset ownership and deterministic completion summaries remain accepted and unchanged.
P02-T06: fail — ledger publication now retains and rechecks runtime identity through creation/read/publish, with direct/replay and distance-3/5 coverage, but installed-origin assertions were removed from the subprocess regressions contrary to the accepted D13 constraint.
P02-T07: pass — saga identity integration reflects the additional runtime-root fsync and existing reconciliation coverage remains intact.
P02-T08: pass — deterministic report/audit/metrics behavior is unchanged; prior exact publication-contention coverage remains accepted.
P02-T09: fail — durable configured-runtime ancestry behavior is covered, including search-only access and fallback diagnostics, but the installed-origin regression weakens proof that those subprocess checks exercise the installed package.
P02-T10: pass — parser-generated workflow command documentation remains accepted and unchanged.
Phase A exit: pass — pure lifecycle fixture behavior is outside the incremental changes and remains accepted.
Phase B exit: fail — implementation safely refuses runtime replacement through ledger publication and preserves replay/state bytes, but the mandatory installed-wheel provenance check no longer covers every regression subprocess.
Phase C exit: fail — same-HEAD suite and tool gates pass, but installed-command provenance is no longer asserted for each touched actor invocation.

### Coordinator-probe adjudication after the initial report (raw)

[ALICE] 🟠 Confirmed: retaining only the runtime descriptor and inode is insufficient. `_ensure_directory_chain` closes all ancestor descriptors before publication, and `verify_runtime()` compares only the runtime inode. The probe replaces `ancestor`, reparents the same runtime inode beneath the replacement, then proves direct append and exact replay return success without fsyncing either `ancestor.parent` or the replacement ancestor. A crash can therefore lose the newly created ancestor/runtime directory entries despite successful ledger publication. This violates D14’s requirement to keep the confirmed runtime ancestry bound through publication, P02-T06/P02-T09 durable ancestry, and Phase B’s requirement that every interrupted durable boundary safely retry without lost work. Preserve and reverify the full ancestor identity chain through success, or refuse this reparenting with a path-specific retryable identity error. | File: src/ovcaq/workflow/_files.py:300 | Task: P02-T06/P02-T09

## Blake

[BLAKE] 🟠 Effective `catchup`, `design`, `design_gate`, and `pause_on_ambiguity` frontmatter values are returned to the caller but discarded from committed state; only the review cap and tier survive, so restart/resume cannot reproduce the declared workflow policy and `catchup: skip` still follows `batch.catchup` | File: src/ovcaq/workflow/frontmatter.py | Task: P02-T02
[BLAKE] 🟠 PRD discovery converts missing, unreadable, symlinked, or non-directory lifecycle roots into empty candidate lists, allowing an inaccessible `wip` to fall through to backlog or an invalid tree to report `drained`; this can skip higher-priority work or prematurely terminate a batch instead of surfacing the invalid-directory error required by the selection test strategy | File: src/ovcaq/workflow/selection.py | Task: P02-T01
[BLAKE] 🟠 `defer_record` validates active batch/PRD with an unlocked read and then publishes the external ledger independently, without revision CAS or durable recovery intent; a concurrent completion/reset can therefore leave a successfully written deferred record attributed from stale state | File: src/ovcaq/workflow/records.py | Task: P02-T06
B1: fail
B2: fail
B3: fail
B4: pass
B5: fail
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: fail
B15: fail
B16: fail
B17: pass
B18: pass
B19: pass

Source-task coverage: P02-T01 fail; P02-T02 fail; P02-T03 pass; P02-T04 pass; P02-T05 pass; P02-T06 fail; P02-T07 pass; P02-T08 pass; P02-T09 pass; P02-T10 pass.

Phase-exit coverage: Phase A fails because frontmatter policy is not durably represented and invalid discovery can yield false lifecycle outcomes. Phase B fails because standalone defer publication is not coupled to the validated state revision/recovery intent, although park/stall durable-boundary recovery is implemented. Phase C passes: all required workflow commands and deterministic renderers are registered, parser-derived operations documentation is present, and workflow dependency/provider guards pass.

Verification: `mise exec -- uv run pytest tests/workflow` completed with 373 passed and two pytest temporary-directory cleanup warnings.

### Source-only adjudication supplement (raw)

Source-only adjudication supplement; the original raw report remains unchanged.

- Frontmatter finding: **retracted**. The frozen v1 crosswalk explicitly classifies `catchup_mode`, `design_mode`, `design_gate`, and `pause_on_ambiguity` as derived values represented by `batch.catchup`, `work.design_doc`, and `control.pause_reason`; it forbids duplicating them as durable policy fields. `RecoveryKind` and the schema provide no alternate frontmatter owner. Returning parsed effective values while committing only owned fields matches that contract. Evidence: `docs/state-protocol.md:321-323,327`; `tests/characterization/current_system.toml:1140-1192`.

- Selection finding: **retracted**. No mandatory source says missing, invalid, or symlink lifecycle directories must raise. The frozen characterization requires WIP priority, backlog fallback, drain, and hold exclusion; the PRD test strategy merely names absent/invalid-directory cases without assigning error outcomes. The implementation’s explicit empty-input behavior is therefore compliant. A `PermissionError` from `iterdir()` is distinct: it is not caught and propagates rather than becoming an empty directory. Evidence: `tests/characterization/current_system.toml:742-756,2706-2711,4546-4551`; `src/ovcaq/workflow/selection.py:31-47`.

- Defer finding: **retracted**. The frozen command contract defines standalone defer as appending a PRD-attributed object to a per-batch ledger. The ledger is independently locked, and operation IDs provide replay deduplication. Durable `recovery.operation` is structurally limited to `park` and `stall`; requiring a defer recovery intent or state CAS would contradict the accepted schema. The batch and PRD captured by the validated read intentionally identify immutable output for that invocation, so later state progress does not retroactively misattribute it. Evidence: `tests/characterization/current_system.toml:724-728,1996-2010,2548-2560`; `src/ovcaq/state/schema.py:59,257-269`.

Corrected verdicts:

B1: pass
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: pass
B16: pass
B17: pass
B18: pass
B19: pass

Corrected source-task coverage: P02-T01–P02-T10 pass.

Corrected phase-exit coverage: Phases A, B, and C pass.

## Bob

**Prior-finding dispositions (cycle 14 → this diff)**

| ID | Disposition |
|---|---|
| R14-01 | Resolved: `_ensure_directory_chain` now yields the runtime fd; `deferred` open/mkdir are `dir_fd`-relative; `verify_runtime` is folded into the verify callable run before, during and after publication (`_files.py:306-347`); installed regressions at deferred-mkdir and ledger-open boundaries, direct + exact replay. |
| R14-02 | Resolved: `distance` parametrize (3, 5) direct/replay committed (`test_rework_13.py:191`). Distance-1 coverage dropped (new F5). |
| R14-03 | Resolved: `test_installed_defer_refuses_execute_only_ancestor_without_search_descriptor` forces the no-descriptor path on Darwin with real 0o111, pins exit/errno/cause/path. |
| R14-04 | Resolved: `_O_SEARCH` module constant, `is None` branch; actor uses the same getattr chain; effective flags asserted in-test. |
| R14-05 | Resolved: `str(directory)`; test asserts no `PosixPath(`. |
| R14-06 | **Not resolved**: `opened` still reused at `_files.py:277` and `:292`. |
| R14-07 | Resolved on the assertion side; child still emits the three constant keys (new F6). |
| R14-08 | Resolved via `packaging_support` helpers, but per-result origin asserts were dropped (new F1). |
| R14-09 / R14-10 | KNOWN, settled, unchanged. |
| R14-11 / R14-12 | Discarded, settled, not re-raised. |

**Findings**

```
[BOB] 🟠 F1: per-result installed-origin verification dropped from test_rework_12 `_invoke`/`_await_event`/`_finish` and test_rework_13 `_invoke`; actor results still carry `origins` but nothing asserts them, contrary to task 6 ("on every subprocess result and event") and task 7/8 ("preserve installed-wheel origin coverage") | File: tests/packaging/test_rework_13.py:71 | Task: 8
[BOB] 🟡 F2: `_open_deferred_ledger` opens `deferred` via dir_fd with no wrapping, so a symlink/regular-file `deferred` (ELOOP/ENOTDIR) or a vanished dir on the second open surfaces raw errno text with the bare name 'deferred'; pre-change `_open_lifecycle_directory` reported "deferred directory is not a real directory: <full path>" | File: src/ovcaq/workflow/_files.py:325 | Task: 7
[BOB] 🟡 F3: `test_installed_defer_refuses_runtime_replacement_before_deferred_creation` and `..._during_ledger_publication` are ~50-line near-duplicates (only mode string and assertion helper differ), both at the 50-line ceiling | File: tests/packaging/test_rework_13.py:242 | Task: 7
[BOB] ⚪ F4: B6 unresolved: `opened` reused for parent fstat then level fstat despite "keep parent and child identities legible" acceptance | File: src/ovcaq/workflow/_files.py:277 | Task: 7
[BOB] ⚪ F5: distance-1 (runtime.parent) replacement coverage removed when parametrize moved to (3, 5) | File: tests/packaging/test_rework_13.py:192 | Task: 7
[BOB] ⚪ F6: `search_capability()` still returns `euid`, `read_denied`, `search_fsync` constants no test reads | File: tests/packaging/rework_13_scripts.py:172 | Task: 8
[BOB] ⚪ F7: `_O_SEARCH` falls back to `os.O_EXEC`; on musl Linux O_EXEC == O_PATH, whose descriptors reject fsync, so every ancestor open in `_ensure_directory_chain` would fail even when readable (suspected, pre-existing via os.O_SEARCH there) | File: src/ovcaq/workflow/_files.py:25 | Task: 8
[BOB] ⚪ F8: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay for packaging tests (base collection failed on missing packaging_support helpers); host reports 1364 passed / 0 skipped at 7b41798 | File: N/A | Task: general
```

**Consensus rubric**

```
R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass
```

**Buckets**

```
FIX:
- F1 dropped origin asserts — tests/packaging/test_rework_13.py:71, test_rework_12.py:52/108/119 — call `assert_installed(value["origins"], installed, "ovcaq.workflow.records")` (13) / `"ovcaq"` (12) at each site; restore `installed` param on `_await_event`/`_finish`
- F2 raw deferred-open errors — src/ovcaq/workflow/_files.py:325,332 — wrap both `os.open(deferred.name, ...)` in a local `open_deferred()` that re-raises FileNotFoundError and maps other OSError to `OSError(f"deferred directory is not a real directory: {deferred}") from error`
- F3 duplicate replacement tests — tests/packaging/test_rework_13.py:242-336 — one test parametrized over `(mode, assert_helper)`; give `_assert_runtime_replaced_at_deferred_mkdir` a `replay` kwarg so both helpers share a signature
- F4 `opened` reuse — src/ovcaq/workflow/_files.py:277,292 — rename to `parent_identity` / `level_identity`
- F5 distance-1 dropped — tests/packaging/test_rework_13.py:192 — `("distance", (1, 3, 5))`
- F6 dead capability keys — tests/packaging/rework_13_scripts.py:172-174 — delete `euid`, `read_denied`, `search_fsync`
VERIFY:
- (none)
KNOWN:
- F7 musl O_EXEC==O_PATH fsync failure — Linux is excluded from the personal-cutover milestone by the resolved discovery (settled B9); behavior is pre-existing, not introduced here
- F8 runtime gates — fresh suite 1364/0/0 at reviewed HEAD; ruff/format/mypy/build reuse same-HEAD exit-0 records; packaging fail-first binding is the settled R9-K4 limitation (base cannot collect the new helper imports)
```

**Doubt rubric**

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

Counts: 8 findings = 6 FIX + 0 VERIFY + 2 KNOWN.

**Status**: Done.
**Changed**: nothing (review only); 8 findings (1 High, 2 Medium, 5 Low), 1 prior finding (R14-06) unresolved.
**Next**: Task complete. Suggested next: route F1 and F4 into the rework loop first (both are acceptance-text breaches of tasks 6-8).

## Final result

Verdict: 12 findings
Tests: 1364 passed, 0 failed, 0 skipped (suite run this cycle at 7b41798c80e06a2c341d75116a09c752203797f4)
