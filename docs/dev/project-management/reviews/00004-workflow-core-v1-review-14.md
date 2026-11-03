---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
review: 14
date: 2026-09-13
head_sha: 7291d9f80c5b7a55f63c406552e5b3e27025acad
reviewers: alice,blake,bob
consensus_engine: legacy
status: completed-review-paused-data-loss-risk
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/reviews/bob-output-00004-14-20260913.txt.receipt.json
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: unavailable
---

# PRD 00004 — cycle 14 review

Diff range: `be5e385bd9714952b4803ee30f7c72e661c278f2..7291d9f80c5b7a55f63c406552e5b3e27025acad`

codex_rung_guard: fired (3 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude

**CHANGES_REQUESTED — review complete; PAUSE for detected data-loss risk.**

Alice and external Claude Bob independently identify the same High: the confirmed runtime identity is lost at the handoff from ancestry traversal to ledger creation. An installed-wheel probe reproduces successful direct append and replay after real runtime replacement, without a subsequent fsync of the replacement's parent. This is syscall-order evidence of a durability gap, not a physical power-loss simulation.

The installed [run-autopilot skill](/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.2/skills/run-autopilot/SKILL.md) mandates “Detected data-loss risk” → “PAUSE” in both modes. That safety rule takes precedence over ordinary loop-mode cap deferral. Repairs require an operator recovery decision. This review creates tasks 7 and 8 but does not execute them, increment cycle 14, change cap 2, move the PRD, or enter finalization. The 16 previously completed tasks, batch 202609062243, and original work base `b43bf2c94d5eb0fddafca55542ef2570b45e8d52` are preserved.

## Consolidated findings

The installed consolidation script ran successfully. Its [raw table](00004-cycle-14-consolidation-raw.md) merged the deeper-ancestry test pair and auto-dismissed Blake's ceiling claim. Coordinator consolidation also merges Alice's and Bob B1's same-file handoff finding. Fourteen raw issue lines minus two duplicate pairs produce **12 distinct findings: 8 FIX, 0 VERIFY, 2 KNOWN, 2 DISCARDED**. The eight actionable findings are one High, three Medium, and four Low. No mechanical finding or prior queued check is omitted.

| ID | Consensus | Severity | Finding (representative wording verbatim) | File | Disposition |
|---|---|---|---|---|---|
| R14-01 | 2/3 | high | Confirmed ancestor identities are discarded when `_ensure_directory_chain` returns; replacing `runtime_root` before `deferred.mkdir()` lets publication or replay succeed in a replacement tree whose parent entry was never fsynced, leaving R13-01’s durability risk open. Keep the confirmed runtime ancestry bound through ledger creation/publication and reverify before success. | src/ovcaq/workflow/_files.py:288 | FIX |
| R14-02 | 2/3 | medium | The replacement regression varies absolute depth but always replaces `runtime.parent`, so an implementation checking only the final two ancestors passes. Commit the retained distance-3/5 probe as an installed regression to bind the every-ancestor requirement. | tests/packaging/test_rework_13.py:143 | FIX |
| R14-03 | 1/3 | medium | B2: the non-Darwin search_only fallback PermissionError branch has no committed test; only an ad-hoc probe (00004-cycle-13-fallback-probe.json) exercised it | src/ovcaq/workflow/_files.py:415 | FIX |
| R14-04 | 1/3 | medium | B5: O_SEARCH resolution inlined with a re-derived `access == os.O_RDONLY` check and a magic literal that is Darwin O_EXEC (SDK fcntl.h:162-163: O_SEARCH = O_EXEC\|O_DIRECTORY); hoist to a module constant `_O_SEARCH: int \| None` and branch on `is None` (also gives B2 a one-line patch hook); the test actor duplicates the same literal | src/ovcaq/workflow/_files.py:400 | FIX |
| R14-05 | 1/3 | low | B4: fallback PermissionError passes a Path as filename so str(error) renders `PosixPath('...')` (probe evidence line 10) while every other message in the module renders the bare path; cli.py:462 emits str(error) | src/ovcaq/workflow/_files.py:420 | FIX |
| R14-06 | 1/3 | low | B6: `opened` is reused for the parent fstat and then the level fstat (Pat LOW note carried forward) | src/ovcaq/workflow/_files.py:262 | FIX |
| R14-07 | 1/3 | low | B7: search test asserts child-hardcoded constants (`read_denied is True`, `search_fsync is True`, `euid != 0` already guaranteed by the skip) | tests/packaging/test_rework_13.py:220 | FIX |
| R14-08 | 1/3 | low | B8: `_assert_installed`, `_identity`, `_prepare` duplicate test_rework_12.py near-verbatim (only the required module name differs) | tests/packaging/test_rework_13.py:19 | FIX |
| R14-09 | 1/3 | low | B9: on platforms without a fsync-capable search descriptor (glibc Linux) defer beneath a 0111 ancestor still fails; the fix only names the requirement | src/ovcaq/workflow/_files.py:415 | KNOWN |
| R14-10 | 1/3 | low | B10: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay of the 7 rework_13 cases (replay skipped: worktree denied); host reports 1359 passed / 0 skipped at 7291d9f; static trace shows each new test fails pre-change | N/A | KNOWN |
| R14-11 | 1/3 | high | `prd_root` is never passed through project containment or symlink-component validation: absolute roots are accepted and `resolve()` follows an in-project symlink outside the repository. Because park/stall consume these paths and rename `wip/<prd>` into `hold/<prd>`, repository or user configuration can make OVCAQ move files in an external tree, contrary to the source contract’s requirement that configured project/runtime paths remain under the resolved project except an explicitly supplied external state root. | src/ovcaq/config.py:87 | DISCARDED |
| R14-12 | 1/3 | medium | `workflow check-plan` adds an unspecified `--ceiling` option and accepts every integer without validation. A large value bypasses the fixed 15-task loop policy, while a negative value classifies even an empty plan as oversized; this makes the installed policy caller-controlled and violates the no-extra-options and input-validation rules. | src/ovcaq/workflow_cli.py:95 | DISCARDED |

## Adjudication

- **R14-01 — FIX:** Both independent reviewers identify the same handoff gap. Installed-wheel direct append and replay succeed after real runtime replacement without a later parent fsync; detected data-loss risk mandates pause.
- **R14-02 — FIX:** Committed cases always replace runtime.parent. Prior Devon evidence and distance-3/5 probes establish the test-depth gap; commit durable regressions while preserving chronological direct/replay assertions.
- **R14-03 — FIX:** The new explicit fallback PermissionError contract was checked only by an ad-hoc probe. A forced fallback test can run on the supported macOS host and preserve errno/cause/path without adding Linux support.
- **R14-04 — FIX:** Local SDK fcntl.h confirms O_SEARCH is O_EXEC | O_DIRECTORY; current combined flags are correct. Naming the capability and using an explicit unsupported sentinel is a bounded readability/testing improvement, not a flag-value defect.
- **R14-05 — FIX:** The retained forced-fallback probe confirms PosixPath(...) appears in the user-visible message. Passing the filesystem string preserves errno/cause and aligns path formatting.
- **R14-06 — FIX:** The same local name is reused for two different directory identities. Descriptive parent/level names can be applied with the bounded ancestry repair.
- **R14-07 — FIX:** The child capability check already refuses or skips unless the three returned conditions hold. Remove redundant metadata assertions while retaining the actual filesystem, fsync, exit, record and state checks.
- **R14-08 — FIX:** Origin and inode helpers duplicate existing installed-test logic. Share only common setup/checks, preserving the differing state backup and per-scenario preparation semantics; do not add generic testing infrastructure.
- **R14-09 — KNOWN:** The mandatory resolved discovery explicitly excludes Linux from the personal-cutover milestone. Keep the explicit fallback failure and durability gate; no new Linux-support task.
- **R14-10 — KNOWN:** Fresh suite at reviewed HEAD passed 1359/0/0; other required gates have same-HEAD successful records. Full fail-first binding remains the settled R9-K4 limitation; the current replay attempt was skipped on worktree denial.
- **R14-11 — DISCARDED:** Blake retracted: containment is specified for runtime roots, not all configured PRD roots. Absolute external PRD roots are deliberately supported; treating that explicit configuration as a containment violation extends the requirement.
- **R14-12 — DISCARDED:** Auto-dismissed by the settled ledger and retracted by Blake: frozen TEST-012 requires override semantics and CLI exposure, CMD-012/DEC-071/TEST-012 migrate under this PRD, and no positive-only domain is specified.

The installed [handoff probe](00004-cycle-14-installed-handoff-probe.json) uses public `record_defer`, intercepts the actual `deferred.mkdir` syscall boundary, performs a real rename/recreation of runtime, and observes real fsync calls. Both first append and replay succeed in the new runtime. Each trace confirms the old runtime entry before replacement and no parent confirmation afterward. The old seeded ledger remains intact in the displaced tree. The [probe source](ancestry_handoff_probe_14.py) uses isolated temporary directories, which it removes. Its installed module SHA-256 equals the reviewed checkout's bytes. The coordinator discovered and ran this probe before either initial reviewer report arrived; it supports the two-reviewer finding without adding a consensus vote.

Protocol B: cycles 11–14 have exposed the same ancestry-confirmation family. Cycle 12 confirmed existing/interrupted ancestors; cycle 13 retained device/inode between adjacent reopens. The current fix ends that identity lifetime before `_open_deferred_ledger` creates and publishes the record, so the final hop still silently adopts a replacement. A different approach is to keep confirmed directory handles/identities bound through child creation and publication, use relative operations where appropriate, and reverify before success; merely checking before the replacement boundary is insufficient. This is at least the fourth family occurrence, although this exact caller-boundary interleaving is first proved in cycle 14. Detected data-loss risk requires pause before repair.

The distance-3/5 tests are still temporary evidence rather than committed regression coverage. Alice and Bob agree on that gap. The new diagnostic fallback can be tested by forcing its branch on macOS; doing so does not expand the milestone to Linux. The local SDK header confirms `O_SEARCH = O_EXEC | O_DIRECTORY`, while the current implementation combines the literal with `O_DIRECTORY`; B5 is a readability/testability finding, not evidence that today's effective flags are wrong. B8's cleanup must preserve scenario-specific preparation, notably backup and record setup, while sharing common checks.

Blake withdrew both findings after source-only adjudication; his original failed B verdicts are retained unchanged below. [His supplement](00004-cycle-14-blake-adjudication.md) explains that PRD-root containment was an unsupported extension of runtime-root requirements, and frozen TEST-012 explicitly mandates ceiling override semantics. The ceiling also matched the existing settled ledger automatically. These are discarded findings, not unresolved High/Medium defects.

### Auto-dismissed (ledger)

- [BLAKE] 🟡 `workflow check-plan` adds an unspecified `--ceiling` option and accepts every integer without validation. A large value bypasses the fixed 15-task loop policy, while a negative value classifies even an empty plan as oversized; this makes the installed policy caller-controlled and violates the no-extra-options and input-validation rules. | File: src/ovcaq/workflow_cli.py:95 — Withdrawn by Blake: frozen source inventory TEST-012 explicitly requires override semantics, and CMD-012/DEC-071/TEST-012 migrate under PRD 00004. No positive-only domain or fixed non-overridable policy is specified.

## Source coverage and verification

The [source audit](00004-cycle-14-source-audit.json) verifies the unchanged accepted-plan SHA-256 and all 55 migration rows, including their full frozen content and eight target routes. Both native reviewers explicitly reconciled P02-T01–P02-T10 and owning phase exits. After adjudication, T01–T05, T08 and T10 remain reconciled; T06/T07/T09 and the durable filesystem exit remain open because of R14-01. Phase A pure rules and Phase C commands/docs/import guards pass; Phase B cannot be accepted.

The [mechanical blocks](00004-cycle-14-mechanics.md) report every changed Python function below 50 lines, seven test functions checked in two test files, and no shape findings. Fail-first replay was attempted using the installed helper and skipped because the sandbox denied `.git/worktrees/wt` creation; no passing replay is claimed. Earlier red tests and deeper ad-hoc probes remain useful narrower evidence. Engram pack was attempted and failed because this repository is unregistered; no pack was supplied. No design doc exists for this PRD.

The prior cycle's check queue is empty, so there are no failed/unrun checks to carry. Bob emitted no VERIFY items; the cycle-14 queue is also empty. The fresh suite passed **1359 tests in 23.47s**, zero failures or skips, at reviewed HEAD. It was rerun because last-verification.json had null counts following a formatting-only commit. Sync, Ruff lint, Ruff format, mypy and build reuse their recorded exit-0 results at this same HEAD. [Verification evidence](00004-cycle-14-verification.md) names the reuse and the fresh suite separately.

The source schema, task counts, complete raw R/B/D rubrics, saved-review shape, doubt constraint, and host receipt validation are checked explicitly; no Claude hook is presumed to have run. Final committed-state results are retained in [final audit](00004-cycle-14-final-audit.json).

## Dispatch provenance

- Alice: native OpenAI gpt-5.6-sol, logical sonnet, `fork_turns=none`, /root/alice_r14. Full installed persona, consensus rubric, implementation-aware context, prior findings, and settled ledger.
- Blake: native OpenAI gpt-5.6-sol, logical sonnet, `fork_turns=none`, /root/blake_r14. Full installed persona, PRD, B1–B19, and mandatory linked source specifications. No diff, task plan, design, history, state, or sibling findings. His post-review supplement received only source evidence relevant to his own two findings.
- Bob: external Claude Opus via the exact authorized driver helper, with approved network access. Actual model `claude-opus-5`, fresh session, helper exit 0. Full Bob persona, consensus rubric, Eve-derived doubt/de-slop appendix and D1–D5. Immutable text/raw JSONL hashes and session identity are in the receipt. No Codex thread id is emitted.
- Carl: optional use-gemini helper exit 3, “refusing nested dispatch (already inside a CLI agent).” No provider inference, output, guard removal, retry or permanent-unavailability latch.
- Watcher: native gpt-5.6-luna, logical haiku, scaffolding only, /root/watcher_r14. First WAITING return was resumed; after Carl's terminal exit it watched only Bob and returned DONE. Every reviewer and helper is terminal.

The native reviewers share a model; independent provider evidence comes from Claude Bob. The source Codex-rung guard fires for exactly three tasks (1, 2 and 4) with Codex attempts. Fable is absent from the available native host models. The required guard suffix records the explicit Claude Bob host substitution and its non-Codex doubt voice; it does not claim an Eve/Fable dispatch.

## Follow-up tasks

- **7 — [D14] Bind confirmed ancestry through ledger publication (M):** R14-01, R14-02, R14-06.
- **8 — [D14] Pin ancestry fallback diagnostics and simplify test scaffolding (M):** R14-03, R14-04, R14-05, R14-07, R14-08.

Both tasks are pending. Their descriptions reproduce every assigned finding verbatim with severity, file and consensus. Task 8 follows task 7 because their scopes overlap. No rework was dispatched and prior completed task attempts were not rewritten.

## Alice

[ALICE] 🟠 Confirmed ancestor identities are discarded when `_ensure_directory_chain` returns; replacing `runtime_root` before `deferred.mkdir()` lets publication or replay succeed in a replacement tree whose parent entry was never fsynced, leaving R13-01’s durability risk open. Keep the confirmed runtime ancestry bound through ledger creation/publication and reverify before success. | File: src/ovcaq/workflow/_files.py:288 | Task: P02-T06/P02-T07/P02-T09
[ALICE] 🟡 The replacement regression varies absolute depth but always replaces `runtime.parent`, so an implementation checking only the final two ancestors passes. Commit the retained distance-3/5 probe as an installed regression to bind the every-ancestor requirement. | File: tests/packaging/test_rework_13.py:143 | Task: P02-T06/P02-T07/P02-T09

P02-T01: pass — selection and configured lifecycle resolution remain reconciled.
P02-T02: pass — frontmatter parsing/defaults/warnings remain reconciled.
P02-T03: pass — transition rows and compound phase completion remain reconciled.
P02-T04: pass — resume mapping and plan policy remain reconciled.
P02-T05: pass — reset and deterministic completion remain reconciled.
P02-T06: fail — durable defer publication retains the caller-boundary ancestry gap.
P02-T07: fail — stall/park use the same affected deferred-ledger boundary.
P02-T08: pass — exact report contention assertions close R13-04.
P02-T09: fail — configured runtime ancestry is not bound through publication.
P02-T10: pass — parser-generated documentation remains reconciled.
Phase A exit: pass.
Phase B exit: fail — safe retry at every durable boundary remains unproven and incomplete.
Phase C exit: pass.

R13-02, R13-03, R13-04, and R13-05 are closed. The supported launcher sandbox evidence resolves R13-06 for the current macOS milestone. R13-01 remains open at the caller boundary.

R1: fail
R2: fail
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

## Blake

P02-T01: fail — selection order and hold exclusion are correct, but lifecycle-root resolution permits external and symlink-escaped PRD trees.

P02-T02: pass — defaults, validation, warnings, abstract tier handling, and state application are implemented.

P02-T03: pass — all six transition rows, compound store mutation, terminal drain, and rejection rows are implemented.

P02-T04: fail — resume mapping works, but the fixed 15-task policy is exposed as an unrestricted override.

P02-T05: pass — per-PRD reset ownership, batch preservation, and deterministic completion summaries are implemented.

P02-T06: pass — defer records require operation IDs and provide atomic, conflict-detecting replay.

P02-T07: pass — park/stall intent, move, record, reset, commit, artifact identity, and durable-boundary reconciliation are implemented.

P02-T08: pass — audit, report, metrics, and terminal-state publication are deterministic and idempotent.

P02-T09: pass — workflow defaults use `dev/local/ovcaq`, configuration precedence is implemented, and no legacy runtime literal remains in workflow code.

P02-T10: pass — workflow documentation is generated from the live parser and contract-tested.

Phase A exit: pass — characterized lifecycle outcomes are mapped to v1 behavior, though T01 and T04 retain the findings below.

Phase B exit: pass — every declared durable saga boundary has restart/replay coverage without duplicate records or lost PRD identity.

Phase C exit: pass — all workflow commands and renderers exist, generated docs match the parser, and dependency/provider-string guards cover the workflow package.

[BLAKE] 🟠 `prd_root` is never passed through project containment or symlink-component validation: absolute roots are accepted and `resolve()` follows an in-project symlink outside the repository. Because park/stall consume these paths and rename `wip/<prd>` into `hold/<prd>`, repository or user configuration can make OVCAQ move files in an external tree, contrary to the source contract’s requirement that configured project/runtime paths remain under the resolved project except an explicitly supplied external state root. | File: src/ovcaq/config.py:87 | Task: P02-T01
[BLAKE] 🟡 `workflow check-plan` adds an unspecified `--ceiling` option and accepts every integer without validation. A large value bypasses the fixed 15-task loop policy, while a negative value classifies even an empty plan as oversized; this makes the installed policy caller-controlled and violates the no-extra-options and input-validation rules. | File: src/ovcaq/workflow_cli.py:95 | Task: P02-T04

B1: fail
B2: pass
B3: pass
B4: pass
B5: fail
B6: fail
B7: fail
B8: pass
B9: pass
B10: fail
B11: pass
B12: fail
B13: pass
B14: fail
B15: fail
B16: pass
B17: pass
B18: pass
B19: pass

### Subsequent source adjudication (original verdicts preserved)

1. **Retract containment finding.** The only source clause is implementation-plan §15: “Validate configured project/runtime paths remain under the resolved project unless the user explicitly supplies an external state root” (lines 976–977). It does not name `prd_root`. `docs/operations.md` narrows containment to “Runtime roots,” while `tests/workflow/test_selection.py:118` deliberately preserves an absolute external PRD root. Extending containment to PRD lifecycle roots was an inference unsupported by the mandatory source.

2. **Retract ceiling finding.** `tests/characterization/current_system.toml:4430` explicitly requires “the fifteen-task plan ceiling, override semantics … [and] CLI exposure.” `tests/characterization/migration.toml:52–58` assigns CMD-012/DEC-071/TEST-012 to P02-T04 and mandates migration. No source clause requires a positive ceiling. The option and unrestricted integer behavior are therefore characterized requirements, not scope creep.

## Bob

The raw review is reproduced below with section headings nested under Bob; immutable original is receipt-linked.

### Prior findings (R13) reconciliation

- R13-01 resolved inside `_ensure_directory_chain` (`confirmed` dev/ino carried across each reopen); residual at the chain→`deferred` hop (B1 below).
- R13-02 resolved on Darwin (native `O_EXEC`-based search descriptor; live 0111 test executed: suite reports 0 skipped). Linux still fails, with a clearer message (B9).
- R13-03 resolved (`levels[1:]`; test pins one root fsync, no root mkdir).
- R13-04 resolved (exact exit 2 / `state_io` / message).
- R13-05 resolved (child prefix/site-packages asserts and `prefix` removed; `sys` still used).
- R13-06 refuted by supplied evidence (`00004-cycle-13-sandbox-after.json`: control write EPERM, defer/stall/park exit 0, one record each). Limit: the JSON records no SHA; the report text places it post-fix. Note the premise was also wrong: 3.12 `Path.mkdir(exist_ok=True)` catches any `OSError` and checks `is_dir()`, not only `FileExistsError`.
- R13-07/08/09 KNOWN, settled, untouched. R13-10 discarded, not re-raised.
- Source obligations: diff touches only P02-T05/T06 durability (defer saga) plus test scaffolding; all other P02 obligations unchanged since earlier cycles. Phase B exit ("safely retries every interrupted durable boundary without lost work") has one residual: B1.

### Findings

```
[BOB] 🟠 B1: runtime root replaced after _ensure_directory_chain returns is adopted by deferred.mkdir/_fsync_directory(deferred.parent) with no identity compare, so defer succeeds while the replacement root's entry in its parent is never fsynced (R13-01 class, one hop further; repro: trigger rename+mkdir of runtime on the deferred mkdir instead of on reopen) | File: src/ovcaq/workflow/_files.py:288 | Task: 4
[BOB] 🟡 B2: the non-Darwin search_only fallback PermissionError branch has no committed test; only an ad-hoc probe (00004-cycle-13-fallback-probe.json) exercised it | File: src/ovcaq/workflow/_files.py:415 | Task: 4
[BOB] 🟡 B3: replacement test pins only direct-parent replacement (both `position` values make ancestor == runtime.parent); a mutant comparing identity only on the last hop passes (Devon round 2, acknowledged in repair report; distance 3/5 probes not committed) | File: tests/packaging/test_rework_13.py:143 | Task: 4
[BOB] 🟡 B5: O_SEARCH resolution inlined with a re-derived `access == os.O_RDONLY` check and a magic literal that is Darwin O_EXEC (SDK fcntl.h:162-163: O_SEARCH = O_EXEC|O_DIRECTORY); hoist to a module constant `_O_SEARCH: int | None` and branch on `is None` (also gives B2 a one-line patch hook); the test actor duplicates the same literal | File: src/ovcaq/workflow/_files.py:400 | Task: 4
[BOB] ⚪ B4: fallback PermissionError passes a Path as filename so str(error) renders `PosixPath('...')` (probe evidence line 10) while every other message in the module renders the bare path; cli.py:462 emits str(error) | File: src/ovcaq/workflow/_files.py:420 | Task: 4
[BOB] ⚪ B6: `opened` is reused for the parent fstat and then the level fstat (Pat LOW note carried forward) | File: src/ovcaq/workflow/_files.py:262 | Task: 4
[BOB] ⚪ B7: search test asserts child-hardcoded constants (`read_denied is True`, `search_fsync is True`, `euid != 0` already guaranteed by the skip) | File: tests/packaging/test_rework_13.py:220 | Task: 4
[BOB] ⚪ B8: `_assert_installed`, `_identity`, `_prepare` duplicate test_rework_12.py near-verbatim (only the required module name differs) | File: tests/packaging/test_rework_13.py:19 | Task: 4
[BOB] ⚪ B9: on platforms without a fsync-capable search descriptor (glibc Linux) defer beneath a 0111 ancestor still fails; the fix only names the requirement | File: src/ovcaq/workflow/_files.py:415 | Task: 4
[BOB] ⚪ B10: Cannot statically verify: suite/ruff/format/mypy/build and fail-first replay of the 7 rework_13 cases (replay skipped: worktree denied); host reports 1359 passed / 0 skipped at 7291d9f; static trace shows each new test fails pre-change | File: N/A | Task: general
```

```
FIX:
- B1 — src/ovcaq/workflow/_files.py:288 — return `confirmed` from `_ensure_directory_chain`; in `_open_deferred_ledger` open `runtime_root` via `_open_lifecycle_directory`, raise `runtime directory identity changed; retry: ...` when fstat dev/ino differs, then `deferred.mkdir(...)` and fsync that descriptor instead of `_fsync_directory(deferred.parent)`; add a `replace-runtime` actor mode triggering on the deferred mkdir. Class-preventing alternative: descend with dir_fd-relative opens.
- B2 — src/ovcaq/workflow/_files.py:415 — add a `fallback` actor mode that patches the search flag away (after B5: `patch.object(_files, "_O_SEARCH", None)`), chmods the ancestor 0111, asserts exit 2, errno 13, the "requires read access" message and `__cause__` PermissionError.
- B3 — tests/packaging/test_rework_13.py:143 — replace `position` with a `distance` param (1 and 3): `runtime = ancestor.joinpath(*["mid"] * (distance - 1), "runtime")`; `_invoke` and `displaced_runtime` already handle it.
- B4 — src/ovcaq/workflow/_files.py:420 — pass `str(directory)` as the filename argument.
- B5 — src/ovcaq/workflow/_files.py:400 — module constant `_O_SEARCH = getattr(os, "O_SEARCH", 0x40000000 if sys.platform == "darwin" else None)` with a comment naming it O_EXEC; `access = _O_SEARCH if search_only and _O_SEARCH is not None else os.O_RDONLY`; fallback branch tests `_O_SEARCH is None`.
- B6 — src/ovcaq/workflow/_files.py:262,277 — rename to `parent_stat` / `level_stat`.
- B7 — tests/packaging/test_rework_13.py:220-222 — delete the three constant asserts; the child already raises if read is not denied and skips otherwise.
- B8 — tests/packaging/test_rework_13.py:19-45 — move `_assert_installed(origins, installed, required="ovcaq")` and `_identity` to packaging_support.py; import in both rework tests.
VERIFY:
- (none)
KNOWN:
- B9 — no POSIX-portable descriptor both traverses a search-only directory and accepts fsync (Linux O_PATH cannot fsync); the failure is explicit and the durability gate is kept; restricting the walk to OVCAQ-created levels is impossible because init's `mkdir(parents=True)` leaves no ownership record (settled R13-07).
- B10 — static-only sandbox; fail-first replay tooling cannot create worktrees (settled R13-09/R9-K4); host owns runtime gates and supplied 1359 passed / 0 skipped.
```

```
R1: fail
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

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

**Status**: Done.
**Changed**: nothing (review only). 10 findings: 8 FIX, 0 VERIFY, 2 KNOWN; R1 fails on B2/B3.
**Next**: Task complete. Suggested next: route B1 (High) and B2/B3/B5 (Medium) into the cycle-14 rework loop; B1 first since its actor mode also serves B3.

## Carl

Unavailable: helper exit 3, “refusing nested dispatch (already inside a CLI agent).” Not counted as a completed reviewer.

Verdict: 12 findings
Tests: 1359 passed, 0 failed, 0 skipped (suite run this cycle)
