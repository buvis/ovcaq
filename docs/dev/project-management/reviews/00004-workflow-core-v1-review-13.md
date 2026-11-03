---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
review: 13
attempt: 20260913-approved
date: 2026-09-13
head_sha: be5e385bd9714952b4803ee30f7c72e661c278f2
reviewers: alice,blake,bob
consensus_engine: legacy
status: completed-review-paused-data-loss-risk
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/reviews/bob-output-00004-13-20260913-approved.txt.receipt.json
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: unavailable
---

# PRD 00004 — cycle 13 review

Diff range: `39ecaf4f95c79df6a88c30e4626386a352d1505b..be5e385bd9714952b4803ee30f7c72e661c278f2`

codex_rung_guard: fired (2 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude

**CHANGES_REQUESTED — completed review; PAUSE for detected data-loss risk.**
The installed-wheel probe reproduced a successful ledger write after a confirmed ancestor was replaced, without another fsync of that ancestor's parent. R13-01 is an unresolved High. This is syscall-ordering evidence and resulting durability risk, not an observation of physical power-loss loss.

All mandatory reviewers completed in this fresh review session. The authorized Claude Bob substitution supplies the independent provider doubt voice; Fable is absent from native host capabilities, and no Eve/Fable dispatch is claimed. The source guard suffix describes that substitution, not a fictitious fifth reviewer. Original committed attempts identify exactly two Codex-implemented tasks.

The run-autopilot Error Handling rule “Detected data-loss risk → PAUSE” applies in both modes and takes precedence over ordinary loop-mode cap deferral. No repairs, cap increase, convergence, cycle increment, PRD move or finalization occurred. Cycle 13, cap 2, batch 202609062243, original work base `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`, and all 13 original completed tasks are preserved. Three newly described follow-ups are pending (13/16 complete).

## Consolidated findings

The installed consolidation script ran successfully on all three raw reviewer outputs; its [raw table](00004-cycle-13-approved-consolidation-raw.md) and [dispatch-time ledger](00004-cycle-13-approved-ledger-at-dispatch.json) are retained. It left two paraphrase pairs separate; coordinator adjudication merges Alice's ancestry access finding with Bob B1 and Alice's root self-step with Bob B2. Raw reports remain unchanged below. R13-01 was discovered by the coordinator and subsequently examined by Alice; it is not counted as independent initial reviewer consensus.

12 observations (11 reviewer lines + 1 coordinator finding), minus 2 duplicate pairs = 10 distinct findings: **5 FIX + 1 VERIFY + 3 KNOWN + 1 DISCARDED**. No mechanical finding or failed previous-cycle check was omitted.

| ID | Consensus | Severity | Finding (representative source wording verbatim) | File | Disposition |
|---|---|---|---|---|---|
| R13-01 | coordinator; Alice adjudication confirms | high | An ancestor replaced after its confirmation is silently adopted as the next level's parent; defer returns success without fsyncing the replacement ancestor's parent | src/ovcaq/workflow/_files.py:255 | FIX |
| R13-02 | 2/3 | medium | `_ensure_directory_chain` now opens every absolute ancestor with `O_RDONLY`, so a configured runtime below a search-only directory can be traversable and writable yet defer fails with `EACCES`; preserve crash confirmation while opening only directories OVCAQ must confirm or use a descriptor mode compatible with execute-only traversal | src/ovcaq/workflow/_files.py:256 | FIX |
| R13-03 | 2/3 | medium | The ancestry loop treats the filesystem root as its own child, opening `/` twice, calling `mkdir(exist_ok=True)` on it, and fsyncing it even though OVCAQ can never create that anchor; exclude the root self-step while retaining parent confirmation for every potentially interrupted runtime ancestor | src/ovcaq/workflow/_files.py:255 | FIX |
| R13-04 | 1/3 | medium | B3: _assert_retry_error hedges: the else branch (any nonzero code with "retry" anywhere in the JSON) is unreachable in the overlap scenario (REPORT_ACTOR pauses inside _publish_file while holding the flock, so B can only fail with the state_io busy error; cli.py:456 maps every OSError to state_io) and keeps the pre-fix loose assertion alive, so a changed code or message still passes | tests/packaging/test_rework_11.py:317 | FIX |
| R13-05 | 1/3 | low | B4: ORIGIN_CHECK.installed_origins asserts in-child (sys.prefix, site-packages) what every consumer re-asserts test-side through _assert_installed against installed.root; the in-child asserts are redundant | tests/packaging/rework_12_scripts.py:84 | FIX |
| R13-06 | 1/3 | medium | B5: Suspected sandbox break: defer/stall/park now issue mkdir and open(O_RDONLY\|O_DIRECTORY) against `/`, `/Users`, `$HOME` from inside launcher sessions that run under `codex exec --sandbox workspace-write` (plan §10.4); Path.mkdir(exist_ok=True) swallows only FileExistsError, so a seatbelt EPERM ahead of the kernel EEXIST fails every ledger write | src/ovcaq/workflow/_files.py:257 | VERIFY |
| R13-07 | 1/3 | low | B6: paths.ensure_runtime_directory (`ovcaq init`) creates the project root and runtime chain with mkdir(parents=True) and no directory fsync; the durability this diff adds does not cover init-created levels (today the unbounded walk confirms them incidentally on the first ledger write) | src/ovcaq/paths.py:94 | KNOWN |
| R13-08 | 1/3 | low | B7: level.mkdir(exist_ok=True) creates the runtime root with default umask mode while ensure_runtime_directory gives the runtime leaf 0o700 (plan §15 restrictive permissions) | src/ovcaq/workflow/_files.py:257 | KNOWN |
| R13-09 | 1/3 | low | B8: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay of the rework_12 crash/racer tests and the two exact-message asserts (replay skipped: worktree denied); recorded gates at HEAD be5e385 (1352 passed) taken from last-verification.json | N/A | KNOWN |
| R13-10 | 1/3 | high | Frontmatter application silently discards the effective catchup, design, design-gate, and pause-on-ambiguity controls: `apply_to_store` parses and returns them but removes their extension keys and persists only rework cap and tier, violating CMD-014’s requirement to transactionally apply derived state fields | src/ovcaq/workflow/frontmatter.py:191 | DISCARDED |

## Adjudication

- **R13-01 — FIX:** Installed-wheel probe succeeds with no parent fsync after replacement. Detected data-loss risk requires pause before repairs.
- **R13-02 — FIX:** Alice and Bob B1 identify the same search-only ancestor access failure. Local O_SEARCH probe supplies a bounded alternative; preserve crash and identity confirmation.
- **R13-03 — FIX:** Alice and Bob B2 identify the same root self-step; retain the higher reported severity.
- **R13-04 — FIX:** Exact contention error assertions can replace the weak fallback in the controlled overlap scenario.
- **R13-05 — FIX:** The parent-side installed-origin check already validates the returned module origins; the duplicate child-side assertions are removable within these tests.
- **R13-06 — VERIFY:** Not queued: suggested command uses placeholders and a nested Codex CLI; host prohibits nested Codex simulation. The source and installed probes succeeded in this host sandbox, refuting a universal failure here. Actual launcher sandbox coverage remains unverified.
- **R13-07 — KNOWN:** Unchanged init ancestry provisioning belongs to P03-T01/PRD 00005. No init durability guarantee is newly asserted here; retain the limitation for its owning phase.
- **R13-08 — KNOWN:** Inherited runtime-root mode behavior belongs to P03-T01 provisioning policy. Existing record/lock permissions remain checked; no new policy is introduced in this review.
- **R13-09 — KNOWN:** Same-HEAD suite/lint/format/types/build are verified by last-verification.json. Residual full fail-first binding is the settled R9-K4 limitation. Not queued: archive/pipe/overlay instructions violate the single verification-command shape.
- **R13-10 — DISCARDED:** The cycle-9 adjudication already settled returned-control/downstream ownership, repeated in cycle-10 and cycle-11 source evidence. The v1 state crosswalk derives controls rather than duplicating policy; tests/workflow/test_applications.py pins returned controls and durable cap/tier/CAS behavior. No new evidence invalidates that boundary.

The earlier cycle-12 abrupt-exit cases are repaired at their tested boundaries. R13-01 adds a replacement between iterations: the function confirms inode A, releases it, then silently adopts inode B when reopening the same pathname as the next child's parent. It fsyncs B for the new child but never fsyncs B's parent after the replacement. The public record_defer API returns a real path containing one expected record.

The probe ran both against checkout source and against the current wheel under isolated Python outside the checkout. The wheel's _files.py bytes equal reviewed source. Retained [installed result](00004-cycle-13-approved-installed-probe.json), [reproduction script](ancestry_replacement_probe_13.py), and [Alice adjudication supplement](00004-cycle-13-approved-ancestry-supplement.md) supply evidence. Temporary probe directories and virtualenvs were removed. The initial uv-venv attempt failed with exit 2 before the product ran; the successful retry used the explicit mise interpreter, an isolated writable cache and offline installation.

A safe bounded repair must retain confirmed identities across traversal steps and refuse or reconfirm replacement ancestors before success. It must preserve abrupt-exit recovery, peer creation, exact replay, record uniqueness and state bytes. Merely stopping at the first existing ancestor would regress the prior repair. Bob's suggested project-root bound also requires proof that the boundary is durably established; his own B6 notes init-created ancestry is not currently confirmed there.

The [directory-mode probe](00004-cycle-13-approved-directory-probe.md) shows O_SEARCH can open and fsync a mode-0111 directory on this macOS/Python host. It is a candidate for a later bounded permission repair, not implementation evidence.

Blake's frontmatter behavior is real but repeats the cycle-9 settled derived-state/downstream ownership decision (fast-review-09 adjudication, repeated in fast-review-10/11 evidence). The state crosswalk derives catchup/design controls; returning controls does not authorize duplicating those policy fields or fabricating completion. His raw High and failed B verdicts are retained unchanged. The missing persistent ledger entry for this settled finding is now recorded explicitly.

Bob's two VERIFY recipes are not queued: B5 uses placeholders and nested Codex, which this host forbids; B8 uses a pipe and mutation/overlay sequence. His raw D3: pass is preserved as his verdict; coordinator checking found these recipes do not satisfy the runnable single-command queue contract. B5 remains an explicit verification follow-up. B8's current quality gates are verified, while its residual fail-first binding remains the settled R9-K4 limitation.

## Source coverage and gates

The [source audit](00004-cycle-13-approved-source-audit.json) confirms the accepted source-plan SHA-256 and all 55 owned migration IDs across eight routes: frontmatter 2, policy 3, records 28, reports 13, resume 2, selection 3, transitions 3, parser/docs 1. All P02-T01–P02-T10 obligations and owning phase exits were reconciled through source, prior accepted evidence and current reviewer coverage. P02-T06/T09 and the recoverable-filesystem exit remain open because of R13-01/R13-02; no missing row is represented as completed.

[Mechanical evidence](00004-cycle-13-approved-mechanics.md): 7 test functions in 3 changed test files, no shape findings. Fail-first replay was attempted and skipped because the sandbox denied .git/worktrees/wt creation; it is not a passing replay. Engram was attempted and failed because the repository is unregistered; no pack supplied.

All five previous-cycle queue entries already carry integer exit 0 at reviewed HEAD, so none are carried forward as failed/unrun. This cycle's queue remains an empty JSON array. The six recorded project gates match reviewed HEAD: sync, pytest (1352/0/0), Ruff lint, formatting, mypy, and build. Counts are reused as required, not a new full-suite run. Blake additionally reported 420 focused tests plus Ruff/mypy passing; these do not replace the authoritative full-suite counts.

Source schema validation and task-count consistency pass. The saved review passed the installed shape and doubt-constraint gates and the host receipt/rubric validation. The pause is committed and the [final audit](00004-cycle-13-approved-final-audit.json) verifies 13/16 tasks, preserved original task/batch records, unchanged HEAD and a clean tracked worktree. Contract-card comparison follows the CLI's documented whitespace normalization.

## Dispatch provenance

- Alice: native OpenAI gpt-5.6-sol, logical sonnet, fork_turns=none, /root/alice_r13_approved. Complete installed persona and consensus rubric read from assembled prompt; implementation-aware.
- Blake: native OpenAI gpt-5.6-sol, logical sonnet, fork_turns=none, /root/blake_r13_approved. Complete installed persona, PRD and B1–B19 rubric; required linked source specifications only. No diff, history, design, state, sibling findings, or implementation task plan.
- Bob: external Claude, requested opus, actual claude-opus-5, fresh session through the authorized driver helper with approved network access; exit 0. Full Bob persona, consensus rubric and Eve-derived doubt/de-slop appendix, all D1–D5. Immutable output and raw JSONL hashes are in the receipt. No stale codex_thread_id is emitted.
- Carl: optional helper exit 3, “refusing nested dispatch (already inside a CLI agent)”; no backend inference, output, or permanent-unavailability latch. No guard stripped.
- Watcher: native gpt-5.6-luna, logical haiku, scaffolding only, /root/watcher_r13_approved; returned DONE. All agents and external processes reached terminal results.

The two native review lenses share a model. Provider diversity comes from the actual Claude Bob dispatch only. Completed-review staging files were archived under [original dispatch inputs](00004-cycle-13-approved-inputs/README.md); earlier sessions' artifacts were left intact. No worktree or branch was created.

## Follow-up tasks

- Task 4: [D13] Preserve confirmed ancestry across replacement and access boundaries (M); R13-01, R13-02, R13-03, R13-06. Pending, no implementation dispatched.
- Task 5: [D13] Make report contention assertions exact (S); R13-04. Pending, no implementation dispatched.
- Task 6: [D13] Remove redundant child origin assertions (S); R13-05. Pending, no implementation dispatched.

The pause leaves these tasks unstarted. Recovery must explicitly resolve the data-loss-risk decision and preserve a fresh work/review handoff. No routine repair is inferred from connectivity recovery.

## Alice

Inspected the incremental diff from `39ecaf4` through reviewed HEAD `be5e385`, the assembled review context, mandatory Phase 2 source specifications, changed implementation/tests, and relevant callers. Reused recorded HEAD-matched gates: 1,352 tests passed with zero failures/skips; Ruff lint/format, mypy, and build passed. Universal implementation-base replay remains the settled R9-K4 limitation.

Prior findings: R12-01, F1, F2, F3, and F5 are repaired by chronological installed-wheel coverage and the implementation changes. F4 remains correctly discarded. V1 is verified. K1, K2, R8-K1, R8-K2, R9-K3, and R9-K4 remain settled and were not re-raised.

P02-T01 through P02-T05 remain reconciled through unchanged selection/path, frontmatter, transitions, resume/policy, reset/completion implementations and existing characterization/row tests. P02-T06 is materially repaired for crash retry, exact replay, peer creation, state-byte preservation, and exactly-once ledger publication, but the valid search-only-ancestor regression below prevents full acceptance. P02-T07 remains reconciled through unchanged saga/failpoint coverage. P02-T08’s contention diagnostic is repaired and its publication behavior remains covered. P02-T09 is affected by the same configured-runtime-path permissions regression. P02-T10 remains reconciled through parser/docs contract coverage.

Phase A exit passes on existing lifecycle fixture evidence. Phase B exit fails because a configured runtime beneath a traversable search-only ancestor can no longer reach defer/recovery, despite the repaired abrupt-exit cases. Phase C exit fails because the installed command path inherits that valid configured-path regression; provider-neutral dependency/string guards and parser-generated docs otherwise remain satisfied.

R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass
[ALICE] 🟡 `_ensure_directory_chain` now opens every absolute ancestor with `O_RDONLY`, so a configured runtime below a search-only directory can be traversable and writable yet defer fails with `EACCES`; preserve crash confirmation while opening only directories OVCAQ must confirm or use a descriptor mode compatible with execute-only traversal | File: src/ovcaq/workflow/_files.py:256 | Task: P02-T06/P02-T09
[ALICE] 🟡 The ancestry loop treats the filesystem root as its own child, opening `/` twice, calling `mkdir(exist_ok=True)` on it, and fsyncing it even though OVCAQ can never create that anchor; exclude the root self-step while retaining parent confirmation for every potentially interrupted runtime ancestor | File: src/ovcaq/workflow/_files.py:255 | Task: P02-T06/P02-T09

### Subsequent adjudication supplement

This was a separate response after the original independent review, assessing coordinator evidence. It does not replace original R verdicts or create an extra consensus vote.

Conclusion: this is an in-scope durability and identity defect. The probe uses ordinary rename/mkdir concurrency already covered by the accepted peer-creation, directory-identity, and crash-recovery requirements. The implementation silently adopts a different ancestor inode between traversal steps, so it cannot dismiss the case as an unsupported outside actor.

The violated guarantee is: before successful ledger publication or exact replay, every runtime ancestor identity used by the operation must have its directory entry confirmed by an `fsync` of its parent. Here the old `ancestor` entry is confirmed, then replaced; the operation uses the new inode as `runtime`’s parent and returns success without confirming the new `ancestor` entry in `project`. This is syscall-ordering evidence only, not evidence of loss after physical power failure.

Bounded safe repair: retain each confirmed level’s identity into the next traversal step and never silently adopt a replacement. When reopening a level as the next child’s parent, compare it with the identity just confirmed. If it changed, either fail closed with a retryable identity error, or re-confirm the replacement by fsyncing its parent and verifying both pathname identities before creating/confirming the child. Add one focused chronological regression matching the probe and assert that success cannot occur without a post-replacement parent fsync; preserve concurrent peer creation, abrupt-exit recovery, exact replay, and exactly-once records.


## Blake

[BLAKE] 🟠 Frontmatter application silently discards the effective catchup, design, design-gate, and pause-on-ambiguity controls: `apply_to_store` parses and returns them but removes their extension keys and persists only rework cap and tier, violating CMD-014’s requirement to transactionally apply derived state fields | File: src/ovcaq/workflow/frontmatter.py:191 | Task: P02-T02

P02-T01: Inspected `workflow/selection.py`, `workflow/paths.py`, configuration tests, and selection tests. WIP priority, numeric ordering, backlog fallback, hold exclusion, configured lifecycle roots, missing/non-directory handling, and symlink refusal are implemented.

P02-T02: Inspected `workflow/frontmatter.py`, application tests, parser tests, the frozen CMD-014 characterization, and state crosswalk. Parsing, defaults, tier validation, and warnings exist, but durable application drops four parsed controls as reported above.

P02-T03: Inspected `workflow/transitions.py`, CLI dispatch, and transition tests. All six accepted rows, rejection rows, drained terminal behavior, complete effect checks, recovery fencing, and single-store CAS mutation are covered.

P02-T04: Inspected `workflow/resume.py`, `workflow/policy.py`, and their tests. Recovery precedence, build/review/paused/done mappings, plan validation, dependency-cycle checks, and the 15-task policy are implemented.

P02-T05: Inspected `workflow/records.py`, application tests, and transition tests. Reset ownership preserves batch state, clears per-PRD owners, and completed summaries are validated, deterministic, conflict-aware, and idempotent.

P02-T06: Inspected `workflow/_files.py`, deferred-ledger tests, publication tests, and installed saga tests. Operation-ID deduplication, conflicting replay rejection, locked atomic publication, directory fsync, bounded validation, and interruption retry are implemented.

P02-T07: Inspected `workflow/records.py`, `_files.py`, `_rename.py`, and saga/failpoint/identity/publication tests. Durable intent, verified exclusive move, record, reset, commit, replay, artifact identity, and every declared boundary are covered.

P02-T08: Inspected `workflow/reports.py`, golden fixtures, report identity/recovery tests, and installed report tests. Audit/report/metrics projections are deterministic, safely published, replayable, and batch-filtered.

P02-T09: Inspected workflow/configuration paths and repository searches. Defaults use `dev/local/ovcaq`; no production workflow hardcoding of `dev/local/autopilot`, personal paths, or legacy skill roots was found.

P02-T10: Inspected `cli.py`, `workflow_cli.py`, `docs/operations.md`, and parser/docs tests. The installed workflow family is registered centrally and operations documentation is generated and checked from the live parser.

Phase A exit: fail. Lifecycle fixture/resume and transition evidence passes, but frontmatter outcomes are not equivalent because several effective controls are not committed.

Phase B exit: pass. The declared defer and park/stall interruption boundaries, replay paths, duplicate prevention, identity checks, and installed-package sagas are covered.

Phase C exit: pass. All accepted workflow commands and renderers are present; parser-generated documentation is checked; static inspection found no workflow imports from runtime, drivers, events, TUI, or provisioning and no provider strings.

Evidence inspected: mandatory PRD-only prompt; accepted implementation plan; coverage manifest; resolved discovery; frozen characterization and migration manifests; workflow source, CLI registration, generated operations documentation, workflow fixtures, workflow tests, and relevant installed-package tests. Verification ran 420 focused tests successfully, plus Ruff and mypy successfully.

Limits: Read-only blind review. I did not inspect git history/diffs, workflow state, implementation task plans, designs, reviews, handoffs, sibling findings, or other reviewer prompts. I did not mutate files or state.

B1: fail
B2: fail
B3: fail
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: fail
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: pass
B17: pass
B18: pass
B19: pass


## Bob

Raw reviewer text follows with headings nested for this section; immutable original is in the receipt-linked output.

### Findings

```
[BOB] 🟡 B1: _ensure_directory_chain walks from `/` and read-opens, mkdirs, fsyncs and identity-verifies every ancestor of the runtime root (`/`, `/Users`, `$HOME`, ...) that OVCAQ can never have left unconfirmed; adds a fail-closed dependency on O_RDONLY access and directory-fsync support for every ancestor filesystem, and an EACCES ancestor is misreported as "runtime directory is not a real directory" (line 393). `_validated_runtime_path` (paths.py:37) already guarantees the runtime root sits below the resolved project root, so bounding the walk there keeps the abrupt-exit guarantee: the project root is fsynced as parent of the first level below it and every lower level is confirmed regardless of existence | File: src/ovcaq/workflow/_files.py:255 | Task: 1
[BOB] ⚪ B2: First iteration is a self-step: Path("/").parent == Path("/"), so root is opened twice, `mkdir(exist_ok=True)` is issued against `/`, `/` is fsynced and verified against itself, then fsynced again as parent of the next level | File: src/ovcaq/workflow/_files.py:255 | Task: 1
[BOB] 🟡 B3: _assert_retry_error hedges: the else branch (any nonzero code with "retry" anywhere in the JSON) is unreachable in the overlap scenario (REPORT_ACTOR pauses inside _publish_file while holding the flock, so B can only fail with the state_io busy error; cli.py:456 maps every OSError to state_io) and keeps the pre-fix loose assertion alive, so a changed code or message still passes | File: tests/packaging/test_rework_11.py:317 | Task: 2
[BOB] ⚪ B4: ORIGIN_CHECK.installed_origins asserts in-child (sys.prefix, site-packages) what every consumer re-asserts test-side through _assert_installed against installed.root; the in-child asserts are redundant | File: tests/packaging/rework_12_scripts.py:84 | Task: 1
[BOB] 🟡 B5: Suspected sandbox break: defer/stall/park now issue mkdir and open(O_RDONLY|O_DIRECTORY) against `/`, `/Users`, `$HOME` from inside launcher sessions that run under `codex exec --sandbox workspace-write` (plan §10.4); Path.mkdir(exist_ok=True) swallows only FileExistsError, so a seatbelt EPERM ahead of the kernel EEXIST fails every ledger write | File: src/ovcaq/workflow/_files.py:257 | Task: 1
[BOB] ⚪ B6: paths.ensure_runtime_directory (`ovcaq init`) creates the project root and runtime chain with mkdir(parents=True) and no directory fsync; the durability this diff adds does not cover init-created levels (today the unbounded walk confirms them incidentally on the first ledger write) | File: src/ovcaq/paths.py:94 | Task: general
[BOB] ⚪ B7: level.mkdir(exist_ok=True) creates the runtime root with default umask mode while ensure_runtime_directory gives the runtime leaf 0o700 (plan §15 restrictive permissions) | File: src/ovcaq/workflow/_files.py:257 | Task: 1
[BOB] ⚪ B8: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay of the rework_12 crash/racer tests and the two exact-message asserts (replay skipped: worktree denied); recorded gates at HEAD be5e385 (1352 passed) taken from last-verification.json | File: N/A | Task: general
```

```
FIX:
- B1 — src/ovcaq/workflow/_files.py:255 — thread the validated project root (`root` in _dispatch_workflow -> defer_record; `paths`/state in _record_and_commit) into _open_deferred_ledger; iterate only the levels of `runtime_root.relative_to(root)` with the root as first parent; drop `path.resolve()` (needed only because ancestors above the root such as `/tmp` are symlinks). test_rework_12 _assert_confirmed (project, new, nested) stays valid.
- B2 — src/ovcaq/workflow/_files.py:255 — disappears with B1; standalone: `for level in (*reversed(path.parents[:-1]), path)`.
- B3 — tests/packaging/test_rework_11.py:317 — assert unconditionally `error["code"] == "state_io"`, `returncode == 2`, `message == f"publication busy; retry: {report_path}"`; delete the else branch.
- B4 — tests/packaging/rework_12_scripts.py:84 — drop the three in-child asserts, keep the origins dict.
VERIFY:
- B5 — run `ovcaq workflow defer --record ...` (or tests/packaging/test_rework_12.py) inside `codex exec --sandbox workspace-write -C <repo under $HOME>` and inside Claude Code's sandbox; expect exit 0 and no PermissionError from Path.mkdir on `/`, `/Users`, `$HOME`.
- B8 — `git archive 39ecaf4 | tar -x -C /tmp/base`, overlay HEAD's tests/, run `uv run pytest tests/packaging/test_rework_12.py tests/packaging/test_rework_11.py tests/workflow/test_ledger_publication.py`; expect the crash/racer tests and both `publication busy; retry:` asserts to fail there and pass at HEAD.
KNOWN:
- B6 — init/P03-T01 territory (paths.py unchanged in this diff); fresh-state extraction excludes a durability repair of init.
- B7 — mode retained from the pre-change line; runtime-root permission policy belongs to ensure_runtime_directory/P03-T01, not this cycle's repair tasks.
```

### Prior findings against code

R12-01 fixed (every level's parent fsynced on every call; os._exit crash regression for `new` and `new/nested`, retry and replay confirm project/new/nested with identity preserved). F1 fixed (reports.py:707 passes report_path; message exact in two tests). F2 fixed (exist_ok, no rmdir; racer/racer-fail preserve the peer's inode). F3 fixed (always-true compare gone). F5 fixed (line 278 reads the key). F4, K1, K2, R8-K1, R8-K2, R9-K3, R9-K4, `--ceiling`: settled, not re-raised.

### P02 reconciliation (incremental scope)

- P02-T06: touched; evidence test_rework_12 (crash x2, concurrent x2), exactly-once record and state bytes asserted. P02-T08: touched; busy message carries the report path. P02-T09: touched; residual B1/B5.
- P02-T01–T05, T07, T10: zero lines in this diff (6-file stat); rest on prior accepted evidence, not re-reviewed (limit).
- Phase A exit: untouched. Phase B exit: strengthened (abrupt-exit retry/replay, peer preservation); B1/B5 are a new retry-failure mode, not lost work. Phase C exit: _files.py imports only ovcaq.state.schema and ovcaq.workflow.paths (lines 16–23); installed gates recorded, not re-run.

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
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

**Status**: Done.
**Changed**: nothing (review only). 8 findings: 4 FIX (2 Medium, 2 Low), 2 VERIFY, 2 KNOWN; R1–R13 and D1–D5 all pass.
**Next**: Task complete. Suggested next: queue B1+B3 as one rework task and run the B5 sandbox check before accepting.

## Carl

Unavailable: helper exit 3, nested-dispatch guard refusal. No model or rubric result fabricated.

## Handoff

Canonical review is complete, but acceptance is blocked. Persist phase/next_phase paused, pause_reason.site data_loss_risk, current completed lens roster and raw doubt verdicts through the existing statectl CLI. No phase-done outcome represents this safety pause. Commit the pause reason before the two phase fields so an interrupted sequence still tells the wrapper to stop; validate the final committed shape.

Follow [the recovery handoff](../plans/fast-track-handoffs/00004-workflow-core-v1/review-13-approved-pause.md). The next session must read the installed Resume procedure, review this evidence and obtain the required operator decision before repairs. Keep the canonical review and all earlier incomplete attempts intact.

Verdict: 10 findings
Tests: 1352 passed, 0 failed, 0 skipped (reused from last-verification.json at be5e385bd9714952b4803ee30f7c72e661c278f2)
