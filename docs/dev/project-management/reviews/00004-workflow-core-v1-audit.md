# Decision Audit Log: 00004-workflow-core-v1

PRD: `00004-workflow-core-v1.md`
Started: 2026-09-14T00:22:57Z
Completed: 2026-09-14T00:22:57Z
Autonomous: 59  |  Deferred: 13  |  Doubts: 29

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F1: Report publication contention reuses the deferred ledger's message and the generic state_io code, so a supervisor can only tell "retry me" from a real disk failure by string-matching the word "retry"

**Choice**: queued

**Rationale**: Task 2 corrects misleading publication context; optional error-code redesign is declined as unestablished by the current contract.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F2: _ensure_directory_chain dropped exist_ok, so a peer creating the same missing runtime ancestor makes defer fail with a bare FileExistsError; the sibling helper paths.ensure_runtime_directory:102 handles that case

**Choice**: queued

**Rationale**: Task 1 also covers safe concurrent ancestor creation.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F3: Assertion cannot fail as written: delegated_calls counts every fsync and directories counts a labeled subset, so the inequality holds by construction

**Choice**: queued

**Rationale**: Task 3 replaces redundant evidence with meaningful assertions.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F4: reports.publish_report has no production caller; workflow_cli reaches into the module-private reports._publish_report instead

**Choice**: discarded

**Rationale**: The R10 repair explicitly retains the public Path-returning publish_report contract while CLI consumes complete composed text from the shared publication. Both paths have callers; removal/renaming offers no required simplification.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F5: FSYNC_SCENARIO emits state_changed_while_interrupted; no assertion reads it

**Choice**: queued

**Rationale**: Task 3 replaces redundant evidence with meaningful assertions.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: V1: Cannot statically verify: suite, ruff, format, mypy, and build gates at the reviewed head

**Choice**: verified

**Rationale**: All five gates ran successfully at reviewed HEAD using the mise-managed uv; recorded verification queue avoids duplicate execution.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: R12-01: process exit after runtime ancestor mkdir but before parent fsync leaves a retry/replay durability gap

**Choice**: pause

**Rationale**: Detected data-loss risk: installed fresh retry and exact replay return success without confirming interrupted parent entries.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: External Claude Bob unavailable before inference

**Choice**: pause

**Rationale**: Cycle 13 incomplete: external Claude Bob was rejected before inference (API 429, five-hour quota exhausted; reset 2026-09-07 19:50 Europe/Prague). No receipt or D1-D5 verdict; independent doubt voice unavailable. Two Medium ancestry findings retained. See dev/local/reviews/00004-workflow-core-v1-cycle-13-incomplete.md. Interactive recovery required; preserve cycle 13 and cap 2.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: `check-plan` exposes an unspecified `--ceiling` override, letting callers bypass the fixed 15-task plan-size policy with a large value and accepting nonsensical negative ceilings instead of rejecting invalid input

**Choice**: discarded

**Rationale**: Withdrawn by Blake: frozen source inventory TEST-012 explicitly requires override semantics, and CMD-012/DEC-071/TEST-012 migrate under PRD 00004. No positive-only domain or fixed non-overridable policy is specified.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: External Claude Bob unavailable before inference: API connectivity/DNS ENOTFOUND

**Choice**: pause

**Rationale**: Host requires pause after mandatory Bob helper terminal failure. Helper exit 1; zero tokens, no output/receipt/D verdicts. No quota rejection or reset time. Native review retains two Medium ancestry findings; cap and cycle unchanged.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: `workflow check-plan` exposes an extra `--ceiling` option absent from the specified command and accepts zero or negative values, allowing a valid empty plan to be rejected as oversized

**Choice**: discarded

**Rationale**: Blake retracted after verifying TEST-012 requires override semantics/CLI exposure and DEC-071 specifies no positive-only domain. Mandatory migration assigns these source rows to PRD 00004/P02-T04.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: Cycle 13 external reviewer connectivity recovered

**Choice**: resume

**Rationale**: Operator explicitly said "ok, resume" after the successful Claude Opus probe and installed host network-approval guidance. Queue a fresh full cycle-13 review; preserve cap 2, both open Medium ancestry findings, all tasks, and historical review evidence.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: An ancestor replaced after its confirmation is silently adopted as the next level's parent; defer returns success without fsyncing the replacement ancestor's parent

**Choice**: pause

**Rationale**: Installed-wheel probe succeeds with no parent fsync after replacement. Detected data-loss risk requires pause before repairs.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: `_ensure_directory_chain` now opens every absolute ancestor with `O_RDONLY`, so a configured runtime below a search-only directory can be traversable and writable yet defer fails with `EACCES`; preserve crash confirmation while opening only directories OVCAQ must confirm or use a descriptor mode compatible with execute-only traversal

**Choice**: queued_pending_operator_recovery

**Rationale**: Alice and Bob B1 identify the same search-only ancestor access failure. Local O_SEARCH probe supplies a bounded alternative; preserve crash and identity confirmation.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: The ancestry loop treats the filesystem root as its own child, opening `/` twice, calling `mkdir(exist_ok=True)` on it, and fsyncing it even though OVCAQ can never create that anchor; exclude the root self-step while retaining parent confirmation for every potentially interrupted runtime ancestor

**Choice**: queued_pending_operator_recovery

**Rationale**: Alice and Bob B2 identify the same root self-step; retain the higher reported severity.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: B3: _assert_retry_error hedges: the else branch (any nonzero code with "retry" anywhere in the JSON) is unreachable in the overlap scenario (REPORT_ACTOR pauses inside _publish_file while holding the flock, so B can only fail with the state_io busy error; cli.py:456 maps every OSError to state_io) and keeps the pre-fix loose assertion alive, so a changed code or message still passes

**Choice**: queued_pending_operator_recovery

**Rationale**: Exact contention error assertions can replace the weak fallback in the controlled overlap scenario.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: B4: ORIGIN_CHECK.installed_origins asserts in-child (sys.prefix, site-packages) what every consumer re-asserts test-side through _assert_installed against installed.root; the in-child asserts are redundant

**Choice**: queued_pending_operator_recovery

**Rationale**: The parent-side installed-origin check already validates the returned module origins; the duplicate child-side assertions are removable within these tests.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: B5: Suspected sandbox break: defer/stall/park now issue mkdir and open(O_RDONLY|O_DIRECTORY) against `/`, `/Users`, `$HOME` from inside launcher sessions that run under `codex exec --sandbox workspace-write` (plan §10.4); Path.mkdir(exist_ok=True) swallows only FileExistsError, so a seatbelt EPERM ahead of the kernel EEXIST fails every ledger write

**Choice**: verification_pending

**Rationale**: Not queued: suggested command uses placeholders and a nested Codex CLI; host prohibits nested Codex simulation. The source and installed probes succeeded in this host sandbox, refuting a universal failure here. Actual launcher sandbox coverage remains unverified.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: Frontmatter application silently discards the effective catchup, design, design-gate, and pause-on-ambiguity controls: `apply_to_store` parses and returns them but removes their extension keys and persists only rework cap and tier, violating CMD-014’s requirement to transactionally apply derived state fields

**Choice**: discarded

**Rationale**: The cycle-9 adjudication already settled returned-control/downstream ownership, repeated in cycle-10 and cycle-11 source evidence. The v1 state crosswalk derives controls rather than duplicating policy; tests/workflow/test_applications.py pins returned controls and durable cap/tier/CAS behavior. No new evidence invalidates that boundary.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: Operator authorized bounded recovery of tasks 4–6

**Choice**: repair

**Rationale**: Operator explicitly requested: Repair tasks 4–6 and prepare autocodex to resume. Execute these tasks with required work gates, then hand off to cycle 14 review; preserve cap 2, batch, work base and review history. Keep wrapper paused during repair.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: Operator-authorized tasks 4–6 completed and verified

**Choice**: resume_review

**Rationale**: Original replacement probe now refuses with retryable identity error; task tests, deeper installed probes, real launcher sandbox checks and full suite passed. Restore review origin for canonical phase-done rework. Cap stays 2; all prior evidence remains. Next review must be fresh.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: Confirmed ancestor identities are discarded when `_ensure_directory_chain` returns; replacing `runtime_root` before `deferred.mkdir()` lets publication or replay succeed in a replacement tree whose parent entry was never fsynced, leaving R13-01’s durability risk open. Keep the confirmed runtime ancestry bound through ledger creation/publication and reverify before success.

**Choice**: pause

**Rationale**: Both independent reviewers identify the same handoff gap. Installed-wheel direct append and replay succeed after real runtime replacement without a later parent fsync; detected data-loss risk mandates pause.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: The replacement regression varies absolute depth but always replaces `runtime.parent`, so an implementation checking only the final two ancestors passes. Commit the retained distance-3/5 probe as an installed regression to bind the every-ancestor requirement.

**Choice**: queued_pending_operator_recovery

**Rationale**: Committed cases always replace runtime.parent. Prior Devon evidence and distance-3/5 probes establish the test-depth gap; commit durable regressions while preserving chronological direct/replay assertions.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: B2: the non-Darwin search_only fallback PermissionError branch has no committed test; only an ad-hoc probe (00004-cycle-13-fallback-probe.json) exercised it

**Choice**: queued_pending_operator_recovery

**Rationale**: The new explicit fallback PermissionError contract was checked only by an ad-hoc probe. A forced fallback test can run on the supported macOS host and preserve errno/cause/path without adding Linux support.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: B5: O_SEARCH resolution inlined with a re-derived `access == os.O_RDONLY` check and a magic literal that is Darwin O_EXEC (SDK fcntl.h:162-163: O_SEARCH = O_EXEC|O_DIRECTORY); hoist to a module constant `_O_SEARCH: int | None` and branch on `is None` (also gives B2 a one-line patch hook); the test actor duplicates the same literal

**Choice**: queued_pending_operator_recovery

**Rationale**: Local SDK fcntl.h confirms O_SEARCH is O_EXEC | O_DIRECTORY; current combined flags are correct. Naming the capability and using an explicit unsupported sentinel is a bounded readability/testing improvement, not a flag-value defect.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: B4: fallback PermissionError passes a Path as filename so str(error) renders `PosixPath('...')` (probe evidence line 10) while every other message in the module renders the bare path; cli.py:462 emits str(error)

**Choice**: queued_pending_operator_recovery

**Rationale**: The retained forced-fallback probe confirms PosixPath(...) appears in the user-visible message. Passing the filesystem string preserves errno/cause and aligns path formatting.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: B6: `opened` is reused for the parent fstat and then the level fstat (Pat LOW note carried forward)

**Choice**: queued_pending_operator_recovery

**Rationale**: The same local name is reused for two different directory identities. Descriptive parent/level names can be applied with the bounded ancestry repair.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: B7: search test asserts child-hardcoded constants (`read_denied is True`, `search_fsync is True`, `euid != 0` already guaranteed by the skip)

**Choice**: queued_pending_operator_recovery

**Rationale**: The child capability check already refuses or skips unless the three returned conditions hold. Remove redundant metadata assertions while retaining the actual filesystem, fsync, exit, record and state checks.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: B8: `_assert_installed`, `_identity`, `_prepare` duplicate test_rework_12.py near-verbatim (only the required module name differs)

**Choice**: queued_pending_operator_recovery

**Rationale**: Origin and inode helpers duplicate existing installed-test logic. Share only common setup/checks, preserving the differing state backup and per-scenario preparation semantics; do not add generic testing infrastructure.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: `prd_root` is never passed through project containment or symlink-component validation: absolute roots are accepted and `resolve()` follows an in-project symlink outside the repository. Because park/stall consume these paths and rename `wip/<prd>` into `hold/<prd>`, repository or user configuration can make OVCAQ move files in an external tree, contrary to the source contract’s requirement that configured project/runtime paths remain under the resolved project except an explicitly supplied external state root.

**Choice**: discarded

**Rationale**: Blake retracted: containment is specified for runtime roots, not all configured PRD roots. Absolute external PRD roots are deliberately supported; treating that explicit configuration as a containment violation extends the requirement.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: `workflow check-plan` adds an unspecified `--ceiling` option and accepts every integer without validation. A large value bypasses the fixed 15-task loop policy, while a negative value classifies even an empty plan as oversized; this makes the installed policy caller-controlled and violates the no-extra-options and input-validation rules.

**Choice**: discarded

**Rationale**: Auto-dismissed by the settled ledger and retracted by Blake: frozen TEST-012 requires override semantics and CLI exposure, CMD-012/DEC-071/TEST-012 migrate under this PRD, and no positive-only domain is specified.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: Operator authorized bounded Resume for existing cycle-14 repair tasks 7–8

**Choice**: resume_build

**Rationale**: The pasted continuation explicitly authorizes Resume and preparation only in this recovery session. Queue existing tasks 7 then 8 for a fresh autocodex work session; preserve cap 2, cycle 14, batch, original work base and all completed task/review history. The data-loss defect is still open; the operator decision pause is resolved. Complete all mandatory work gates, then hand off to a fresh review with every mandatory lens. No repair or reviewer is launched here.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: Replacing an already confirmed ancestor and reparenting the same runtime inode beneath its replacement before ledger open is accepted by direct append and exact replay, without any later fsync of the ancestor's parent or the replacement ancestor. Runtime-only identity checks do not preserve the confirmed ancestry through successful publication.

**Recommendation**: Installed module hash matches reviewed checkout; two fresh subprocesses demonstrate real ancestor replacement/reparent, successful return, no later parent fsync. Safety pause takes precedence over ordinary cap deferral.

**Choice**: queued for operator-authorized recovery

**Rationale**: Installed-wheel direct/replay probe reproduces successful return after ancestor replacement and reparenting of the same runtime inode, with no later confirmation of the replacement directory entries. Detected data-loss risk mandates pause. Final parent descriptor remains open, but no ancestor identity is reverified after yield.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F1: per-result installed-origin verification dropped from test_rework_12 `_invoke`/`_await_event`/`_finish` and test_rework_13 `_invoke`; actor results still carry `origins` but nothing asserts them, contrary to task 6 ("on every subprocess result and event") and task 7/8 ("preserve installed-wheel origin coverage")

**Choice**: queued for operator-authorized recovery

**Rationale**: Alice and Bob independently found removed assert_installed calls; coordinator verified all four result/event consumers. Initialization retains a check, but it does not establish the origin of every later subprocess.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F2: `_open_deferred_ledger` opens `deferred` via dir_fd with no wrapping, so a symlink/regular-file `deferred` (ELOOP/ENOTDIR) or a vanished dir on the second open surfaces raw errno text with the bare name 'deferred'; pre-change `_open_lifecycle_directory` reported "deferred directory is not a real directory: <full path>"

**Choice**: queued for operator-authorized recovery

**Rationale**: Coordinator source-runtime probe reproduces symlink and regular-file refusal as bare "deferred" ENOTDIR, omitting the configured path. Both objects remain untouched. Restore diagnostic context while preserving safe refusal and causal errno.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F3: `test_installed_defer_refuses_runtime_replacement_before_deferred_creation` and `..._during_ledger_publication` are ~50-line near-duplicates (only mode string and assertion helper differ), both at the 50-line ceiling

**Choice**: queued for operator-authorized recovery

**Rationale**: Two newly added direct/replay tests have the same setup/action/assert/retry flow with different injection mode and boundary assertion helper. Parametrize the shared flow while retaining scenario-specific chronology and state/record assertions.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F4: B6 unresolved: `opened` reused for parent fstat then level fstat despite "keep parent and child identities legible" acceptance

**Choice**: queued for operator-authorized recovery

**Rationale**: Previous R14-06 remains open: the implementation still assigns parent and child fstat results to opened. Rename the two identities without altering behavior.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F5: distance-1 (runtime.parent) replacement coverage removed when parametrize moved to (3, 5)

**Choice**: queued for operator-authorized recovery

**Rationale**: Changing distances to (3, 5) removed the former immediate-parent case. The runtime-replacement cases target the runtime itself; restore distance 1 alongside the new distant cases.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F6: `search_capability()` still returns `euid`, `read_denied`, `search_fsync` constants no test reads

**Choice**: queued for operator-authorized recovery

**Rationale**: Actor capability metadata euid/read_denied/search_fsync is no longer consumed; remove these emitted keys while retaining real permission and fsync checks.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: Effective `catchup`, `design`, `design_gate`, and `pause_on_ambiguity` frontmatter values are returned to the caller but discarded from committed state; only the review cap and tier survive, so restart/resume cannot reproduce the declared workflow policy and `catchup: skip` still follows `batch.catchup`

**Choice**: discarded

**Rationale**: Retracted by Blake after source-only adjudication: docs/state-protocol.md:321-323,327 and frozen inventory classify these controls as derived and allocate ownership to existing v1 fields. No new evidence invalidates the prior ledger decision.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: PRD discovery converts missing, unreadable, symlinked, or non-directory lifecycle roots into empty candidate lists, allowing an inaccessible `wip` to fall through to backlog or an invalid tree to report `drained`; this can skip higher-priority work or prematurely terminate a batch instead of surfacing the invalid-directory error required by the selection test strategy

**Choice**: discarded

**Rationale**: Retracted by Blake: mandatory selection source specifies WIP priority/fallback/drain but no required error outcome for absent/invalid/symlink directories. PermissionError from iterdir is not caught. Test strategy naming these cases is not an error contract.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: `defer_record` validates active batch/PRD with an unlocked read and then publishes the external ledger independently, without revision CAS or durable recovery intent; a concurrent completion/reset can therefore leave a successfully written deferred record attributed from stale state

**Choice**: discarded

**Rationale**: Retracted by Blake: CMD-010 and STATE-112/113 define an independently locked PRD/batch-attributed append; recovery.operation supports park/stall only. A later state change does not invalidate immutable attribution from the validated invocation.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: Operator authorized bounded recovery of tasks 9-10

**Choice**: repair

**Rationale**: Operator answered yes to repairing ancestry verification and regression coverage, then handing off to a fresh full review. Prepare a fresh build for only tasks 9-10; preserve cycle 15, cap 2, batch, completed work and review history. No findings are waived.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: The restored deferred-directory diagnostic has no committed regression covering initial file/symlink refusal or the vanished-directory second open, including full path and preserved cause/errno

**Choice**: tail_sweep

**Rationale**: Source-verified bounded Medium/Low finding. Task 11 carries this exact issue; normal work pipeline before finalize handoff.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: `_ensure_directory_chain` is 51 lines because it embeds the 13-line ancestry verifier; move that verifier to a named helper to satisfy the function-size limit and simplify the chain walk

**Choice**: tail_sweep

**Rationale**: Source-verified bounded Medium/Low finding. Task 11 carries this exact issue; normal work pipeline before finalize handoff.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: `test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry` is 80 lines; extract the safe-result and retry/replay assertion flows into helpers while retaining the parameterized chronology

**Choice**: tail_sweep

**Rationale**: Source-verified bounded Medium/Low finding. Task 11 carries this exact issue; normal work pipeline before finalize handoff.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F4: _invoke reimplements subprocess.run's timeout kill/reap as a 16-line Popen block plus a framework-verifying `assert process.poll() is not None`; subprocess.run(timeout=20) already kills and waits on TimeoutExpired, and test_rework_12._invoke in the same diff keeps subprocess.run

**Choice**: tail_sweep

**Rationale**: Source-verified bounded Medium/Low finding. Task 11 carries this exact issue; normal work pipeline before finalize handoff.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F5: os.mkdir(deferred.name, dir_fd=runtime) failures other than EEXIST (EACCES, ENOSPC, EBADF) still surface raw errno text with the bare name 'deferred'; same class as R15-03, on the create step the acceptance ("every failing open") did not name

**Choice**: tail_sweep

**Rationale**: Source-verified bounded Medium/Low finding. Task 11 carries this exact issue; normal work pipeline before finalize handoff.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F6: fix commit 93c049b changed a user-visible diagnostic (full deferred path on open failure) without a CHANGELOG entry; the only added Fixed line covers ancestry revalidation

**Choice**: tail_sweep

**Rationale**: Source-verified bounded Medium/Low finding. Task 11 carries this exact issue; normal work pipeline before finalize handoff.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F7: reparent-refusal branch hedges `if _ledger(runtime).exists(): _assert_one_record(runtime)`; the shipped chronology deterministically refuses inside the first _read_record_content before any write, so the direct case should pin that no ledger exists

**Choice**: tail_sweep

**Rationale**: Source-verified bounded Medium/Low finding. Task 11 carries this exact issue; normal work pipeline before finalize handoff.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: The final `verify_ancestry()` pass is still racy: replacing an ancestor immediately after its pathname `stat`, then reparenting the unchanged descendant subtree beneath the replacement, lets all later identity checks pass and publication return without confirming the replacement entries; the regression injects before verification begins and misses this window

**Choice**: discarded

**Rationale**: Alice retracted after deterministic installed-wheel probe and linearization analysis: direct/replay publication and a complete old-ancestry observation precede the external reparent. The later external mutation owns its directory durability. No success lacking a valid pre-mutation linearization point was found.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: The frontmatter port is incomplete: characterized `doubt_reviewer` and `consensus_engine` controls are silently ignored, while accepted `catchup`, `design`, `design_gate`, and `pause_on_ambiguity` values are returned but not committed, making later overwrite warnings impossible on fresh v1 state

**Choice**: discarded

**Rationale**: Blake retracted against docs/state-protocol.md and frozen STATE-005/006/007/009/010/011: controls are derived from existing v1 owners. No duplicate state fields required; agent/model selection belongs to runtime.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: Deferred-ledger reads validate only that items are objects; missing, unsafe, or duplicate `op_id` values survive loading, after which report rendering silently drops or collapses them, violating the operation-ID and no-lost-record contracts

**Choice**: discarded

**Rationale**: Blake retracted: CMD-010 and STATE-113 require valid deduplicated public writes, already enforced; TEST-018 preserves tolerant report handling. No source contract requires semantic validation of externally malformed ledger rows.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F8: Cannot statically verify: suite/ruff/format/mypy/build at 4011d1a; 1372/0/0 are reused same-HEAD records, not a fresh run

**Choice**: discarded

**Rationale**: Verified six exit-0 command records with non-null 1372/0/0 counts at reviewed HEAD 4011d1a3ce186ae9dcd023e8a7fb4b87412b935d. Source requires reuse, not a repeated full suite. Bob labels this KNOWN.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: F9: fail-first replay: 12 touched tests pass at base; all are behavior-preserving test edits (origin re-assertions in rework_12's concurrent test, re-parametrized cycle-13/14 regressions in rework_13), the 6 new reparent cases fail at base

**Choice**: discarded

**Rationale**: Behavior-preserving origin assertions and parametrized existing regressions intentionally pass at base. Six newly added reparent cases fail old production; instrumented replay includes the otherwise unoverlaid actor helper and fails specifically on missing post-reparent fsync.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: 2 touched test(s) pass against the pre-change code: test_installed_concurrent_creation_confirms_and_preserves_peer_directory

**Choice**: discarded

**Rationale**: These two existing cases only gain installed-origin assertions; behavior-preserving test coverage passes old code by design.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: 10 touched test(s) pass against the pre-change code: test_installed_defer_refuses_replaced_distant_ancestry_until_fresh_attempt +4 more

**Choice**: discarded

**Rationale**: These ten cases preserve earlier behavior while parametrizing/restoring coverage. Six new reparent cases fail old production at the intended fsync assertion with the current actor overlaid.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: `_assert_reparented_retry_and_replay` takes a `previous_runtime: list[int]` parameter that is never referenced in the function body

**Choice**: discarded

**Rationale**: The parameter is used at tests/packaging/test_rework_13.py:398: assert identity(runtime) == previous_runtime.

### [autonomous] 2026-09-14T00:22:57Z

**Decision**: `authoritative` is annotated `tuple[bytes, bytes]` but is assigned from a single `_state_bytes(project)` call and compared with `==` against one such call — the tuple annotation doesn't match the value's actual shape

**Choice**: discarded

**Rationale**: _state_bytes at tests/packaging/test_rework_13.py:41-43 explicitly returns tuple[bytes, bytes], containing state and backup bytes. The annotation is correct.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: K1: A ledger written past the reader's depth limit by a pre-fix build stays unreadable and unappendable; the repair is prospective only

**Choice**: known

**Rationale**: Fresh-state one-way extraction explicitly excludes an importer or historical corrupt-ledger repair.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: K2: render report requires runtime_root to already exist while defer now creates its chain

**Choice**: known

**Rationale**: Render requires an existing configured runtime root and fails loudly; no accepted clause requires render to provision it.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: R8-K1: inherited config-collision test retains the mechanically flagged either-or assertion

**Choice**: known

**Rationale**: Inherited collision assertion is a settled exception; broad state-test restructuring excluded.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: R8-K2: inherited 53-line add_task and three unchanged packaging functions exceed R12

**Choice**: known

**Rationale**: Inherited function-size exceptions are settled; retain existing API and test boundaries.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: R9-K3: inherited state schema remains 933 lines, over R13

**Choice**: known

**Rationale**: Inherited schema-size exception is settled; broad state restructuring excluded.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: R9-K4: universal implementation-base fail-first binding remains unproven; this cycle's replay was skipped outright (worktree creation denied)

**Choice**: known

**Rationale**: Universal full-base fail-first binding remains unproven; current replay collection fails on missing packaging_support. Retain narrower chronological regressions.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: B6: paths.ensure_runtime_directory (`ovcaq init`) creates the project root and runtime chain with mkdir(parents=True) and no directory fsync; the durability this diff adds does not cover init-created levels (today the unbounded walk confirms them incidentally on the first ledger write)

**Choice**: known

**Rationale**: Unchanged init ancestry provisioning belongs to P03-T01/PRD 00005. No init durability guarantee is newly asserted here; retain the limitation for its owning phase.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: B7: level.mkdir(exist_ok=True) creates the runtime root with default umask mode while ensure_runtime_directory gives the runtime leaf 0o700 (plan §15 restrictive permissions)

**Choice**: known

**Rationale**: Inherited runtime-root mode behavior belongs to P03-T01 provisioning policy. Existing record/lock permissions remain checked; no new policy is introduced in this review.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: B8: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay of the rework_12 crash/racer tests and the two exact-message asserts (replay skipped: worktree denied); recorded gates at HEAD be5e385 (1352 passed) taken from last-verification.json

**Choice**: known

**Rationale**: Same-HEAD suite/lint/format/types/build are verified by last-verification.json. Residual full fail-first binding is the settled R9-K4 limitation. Not queued: archive/pipe/overlay instructions violate the single verification-command shape.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: B9: on platforms without a fsync-capable search descriptor (glibc Linux) defer beneath a 0111 ancestor still fails; the fix only names the requirement

**Choice**: settled-deferral

**Rationale**: The mandatory resolved discovery explicitly excludes Linux from the personal-cutover milestone. Keep the explicit fallback failure and durability gate; no new Linux-support task.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: B10: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay of the 7 rework_13 cases (replay skipped: worktree denied); host reports 1359 passed / 0 skipped at 7291d9f; static trace shows each new test fails pre-change

**Choice**: settled-deferral

**Rationale**: Fresh suite at reviewed HEAD passed 1359/0/0; other required gates have same-HEAD successful records. Full fail-first binding remains the settled R9-K4 limitation; the current replay attempt was skipped on worktree denial.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: F7: `_O_SEARCH` falls back to `os.O_EXEC`; on musl Linux O_EXEC == O_PATH, whose descriptors reject fsync, so every ancestor open in `_ensure_directory_chain` would fail even when readable (suspected, pre-existing via os.O_SEARCH there)

**Choice**: deferred as known limitation

**Rationale**: Linux is explicitly excluded from the current personal-cutover milestone. Bob's musl-specific concern is unverified here and attributed as a suspected pre-existing limitation, not a confirmed host defect.

### [deferred] 2026-09-14T00:22:57Z

**Decision**: F8: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay for packaging tests (base collection failed on missing packaging_support helpers); host reports 1364 passed / 0 skipped at 7b41798

**Choice**: deferred as known limitation

**Rationale**: Fresh suite passes 1364/0/0; other required gates reuse same-HEAD successful records. Approved replay produced two red tests but two packaging files failed collection at base, so their behavioral fail-first binding remains limited. No broad rebuild is queued solely to repeat already recorded gates.

### [doubt] 2026-09-14T00:22:57Z

**Decision**: R12-01: successful retry/replay omits interrupted runtime-parent fsync

### [doubt] 2026-09-14T00:22:57Z

**Decision**: An ancestor replaced after its confirmation is silently adopted as the next level's parent; defer returns success without fsyncing the replacement ancestor's parent

### [doubt] 2026-09-14T00:22:57Z

**Decision**: `_ensure_directory_chain` now opens every absolute ancestor with `O_RDONLY`, so a configured runtime below a search-only directory can be traversable and writable yet defer fails with `EACCES`; preserve crash confirmation while opening only directories OVCAQ must confirm or use a descriptor mode compatible with execute-only traversal

### [doubt] 2026-09-14T00:22:57Z

**Decision**: The ancestry loop treats the filesystem root as its own child, opening `/` twice, calling `mkdir(exist_ok=True)` on it, and fsyncing it even though OVCAQ can never create that anchor; exclude the root self-step while retaining parent confirmation for every potentially interrupted runtime ancestor

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B3: _assert_retry_error hedges: the else branch (any nonzero code with "retry" anywhere in the JSON) is unreachable in the overlap scenario (REPORT_ACTOR pauses inside _publish_file while holding the flock, so B can only fail with the state_io busy error; cli.py:456 maps every OSError to state_io) and keeps the pre-fix loose assertion alive, so a changed code or message still passes

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B4: ORIGIN_CHECK.installed_origins asserts in-child (sys.prefix, site-packages) what every consumer re-asserts test-side through _assert_installed against installed.root; the in-child asserts are redundant

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B5: Suspected sandbox break: defer/stall/park now issue mkdir and open(O_RDONLY|O_DIRECTORY) against `/`, `/Users`, `$HOME` from inside launcher sessions that run under `codex exec --sandbox workspace-write` (plan §10.4); Path.mkdir(exist_ok=True) swallows only FileExistsError, so a seatbelt EPERM ahead of the kernel EEXIST fails every ledger write

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B6: paths.ensure_runtime_directory (`ovcaq init`) creates the project root and runtime chain with mkdir(parents=True) and no directory fsync; the durability this diff adds does not cover init-created levels (today the unbounded walk confirms them incidentally on the first ledger write)

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B7: level.mkdir(exist_ok=True) creates the runtime root with default umask mode while ensure_runtime_directory gives the runtime leaf 0o700 (plan §15 restrictive permissions)

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B8: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay of the rework_12 crash/racer tests and the two exact-message asserts (replay skipped: worktree denied); recorded gates at HEAD be5e385 (1352 passed) taken from last-verification.json

### [doubt] 2026-09-14T00:22:57Z

**Decision**: Confirmed ancestor identities are discarded when `_ensure_directory_chain` returns; replacing `runtime_root` before `deferred.mkdir()` lets publication or replay succeed in a replacement tree whose parent entry was never fsynced, leaving R13-01’s durability risk open. Keep the confirmed runtime ancestry bound through ledger creation/publication and reverify before success.

### [doubt] 2026-09-14T00:22:57Z

**Decision**: The replacement regression varies absolute depth but always replaces `runtime.parent`, so an implementation checking only the final two ancestors passes. Commit the retained distance-3/5 probe as an installed regression to bind the every-ancestor requirement.

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B2: the non-Darwin search_only fallback PermissionError branch has no committed test; only an ad-hoc probe (00004-cycle-13-fallback-probe.json) exercised it

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B5: O_SEARCH resolution inlined with a re-derived `access == os.O_RDONLY` check and a magic literal that is Darwin O_EXEC (SDK fcntl.h:162-163: O_SEARCH = O_EXEC|O_DIRECTORY); hoist to a module constant `_O_SEARCH: int | None` and branch on `is None` (also gives B2 a one-line patch hook); the test actor duplicates the same literal

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B4: fallback PermissionError passes a Path as filename so str(error) renders `PosixPath('...')` (probe evidence line 10) while every other message in the module renders the bare path; cli.py:462 emits str(error)

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B6: `opened` is reused for the parent fstat and then the level fstat (Pat LOW note carried forward)

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B7: search test asserts child-hardcoded constants (`read_denied is True`, `search_fsync is True`, `euid != 0` already guaranteed by the skip)

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B8: `_assert_installed`, `_identity`, `_prepare` duplicate test_rework_12.py near-verbatim (only the required module name differs)

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B9: on platforms without a fsync-capable search descriptor (glibc Linux) defer beneath a 0111 ancestor still fails; the fix only names the requirement

### [doubt] 2026-09-14T00:22:57Z

**Decision**: B10: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay of the 7 rework_13 cases (replay skipped: worktree denied); host reports 1359 passed / 0 skipped at 7291d9f; static trace shows each new test fails pre-change

### [doubt] 2026-09-14T00:22:57Z

**Decision**: Replacing an already confirmed ancestor and reparenting the same runtime inode beneath its replacement before ledger open is accepted by direct append and exact replay, without any later fsync of the ancestor's parent or the replacement ancestor. Runtime-only identity checks do not preserve the confirmed ancestry through successful publication.

### [doubt] 2026-09-14T00:22:57Z

**Decision**: F1: per-result installed-origin verification dropped from test_rework_12 `_invoke`/`_await_event`/`_finish` and test_rework_13 `_invoke`; actor results still carry `origins` but nothing asserts them, contrary to task 6 ("on every subprocess result and event") and task 7/8 ("preserve installed-wheel origin coverage")

### [doubt] 2026-09-14T00:22:57Z

**Decision**: F2: `_open_deferred_ledger` opens `deferred` via dir_fd with no wrapping, so a symlink/regular-file `deferred` (ELOOP/ENOTDIR) or a vanished dir on the second open surfaces raw errno text with the bare name 'deferred'; pre-change `_open_lifecycle_directory` reported "deferred directory is not a real directory: <full path>"

### [doubt] 2026-09-14T00:22:57Z

**Decision**: F3: `test_installed_defer_refuses_runtime_replacement_before_deferred_creation` and `..._during_ledger_publication` are ~50-line near-duplicates (only mode string and assertion helper differ), both at the 50-line ceiling

### [doubt] 2026-09-14T00:22:57Z

**Decision**: F4: B6 unresolved: `opened` reused for parent fstat then level fstat despite "keep parent and child identities legible" acceptance

### [doubt] 2026-09-14T00:22:57Z

**Decision**: F5: distance-1 (runtime.parent) replacement coverage removed when parametrize moved to (3, 5)

### [doubt] 2026-09-14T00:22:57Z

**Decision**: F6: `search_capability()` still returns `euid`, `read_denied`, `search_fsync` constants no test reads

### [doubt] 2026-09-14T00:22:57Z

**Decision**: F7: `_O_SEARCH` falls back to `os.O_EXEC`; on musl Linux O_EXEC == O_PATH, whose descriptors reject fsync, so every ancestor open in `_ensure_directory_chain` would fail even when readable (suspected, pre-existing via os.O_SEARCH there)

### [doubt] 2026-09-14T00:22:57Z

**Decision**: F8: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay for packaging tests (base collection failed on missing packaging_support helpers); host reports 1364 passed / 0 skipped at 7b41798
