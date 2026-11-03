---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
review: 12
date: 2026-09-07
head_sha: 39ecaf4f95c79df6a88c30e4626386a352d1505b
reviewers: alice,blake,bob
consensus_engine: legacy
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/reviews/00004-cycle-12-bob-retry-output.txt.receipt.json
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: disabled
---

# PRD 00004 — cycle 12 completion review

Diff range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..39ecaf4f95c79df6a88c30e4626386a352d1505b`

codex_rung_guard: not fired

**CHANGES_REQUESTED; pause for detected data-loss risk.** R12-01 remains an
unresolved High. Existing tests pass, but a new installed-wheel crash probe shows
successful retry and exact replay omitting an interrupted runtime ancestor's
parent fsync. No rework, convergence, PRD closeout, or next gate ran here.

Terminal accounting: **13 observations = 5 FIX + 1 VERIFIED + 6 KNOWN + 1
DISCARDED**. Five fix observations are grouped into three pending tasks (IDs
1, 2, 3), with each source finding preserved verbatim. The source snapshot now
has 13 tasks, 10 completed. All ten original source obligations remain distinct.

[Source and probe evidence](00004-workflow-core-v1-review-12-evidence.md) ·
[Installed crash observations](00004-cycle-12-crash-probe.json) ·
[Raw script consolidation](00004-cycle-12-consolidation-raw.md) ·
[Verification](00004-cycle-12-verification.json)

## Consolidated findings

| ID | Consensus | Severity | Finding | File | Disposition |
|---|---|---|---|---|---|
| R12-01 | coordinator | High | Process exit after mkdir but before parent fsync leaves an unconfirmed ancestor; fresh retry and exact replay succeed without confirming that parent | src/ovcaq/workflow/_files.py:252 | FIX; data-loss-risk pause; task 1 |
| F1 | 1/3 | Medium | F1: Report publication contention reuses the deferred ledger's message and the generic state_io code, so a supervisor can only tell "retry me" from a real disk failure by string-matching the word "retry" | src/ovcaq/workflow/_files.py:75 | FIX (diagnostic context only; optional error-code redesign declined) |
| F2 | 1/3 | Medium | F2: _ensure_directory_chain dropped exist_ok, so a peer creating the same missing runtime ancestor makes defer fail with a bare FileExistsError; the sibling helper paths.ensure_runtime_directory:102 handles that case | src/ovcaq/workflow/_files.py:265 | FIX (task 1) |
| F3 | 1/3 | Medium | F3: Assertion cannot fail as written: delegated_calls counts every fsync and directories counts a labeled subset, so the inequality holds by construction | tests/packaging/test_rework_11.py:278 | FIX (task 3) |
| F4 | 1/3 | Medium | F4: reports.publish_report has no production caller; workflow_cli reaches into the module-private reports._publish_report instead | src/ovcaq/workflow/reports.py:676 | DISCARDED (verified retained public Path contract) |
| F5 | 1/3 | Low | F5: FSYNC_SCENARIO emits state_changed_while_interrupted; no assertion reads it | tests/packaging/rework_11_scripts.py:202 | FIX (task 3) |
| V1 | 1/3 | Low | V1: Cannot statically verify: suite, ruff, format, mypy, and build gates at the reviewed head | N/A | VERIFIED (this cycle's five gates) |
| K1 | 1/3 | Low | K1: A ledger written past the reader's depth limit by a pre-fix build stays unreadable and unappendable; the repair is prospective only | src/ovcaq/workflow/_files.py:82 | KNOWN (fresh-state extraction; no importer) |
| K2 | 1/3 | Low | K2: render report requires runtime_root to already exist while defer now creates its chain | src/ovcaq/workflow/reports.py:507 | KNOWN (render root prerequisite) |
| R8-K1 | 1/3 + mech-check | Medium | R8-K1: inherited config-collision test retains the mechanically flagged either-or assertion | tests/state/test_cli.py:372 | KNOWN (settled; also mech-check) |
| R8-K2 | 1/3 | Low | R8-K2: inherited 53-line add_task and three unchanged packaging functions exceed R12 | src/ovcaq/state/commands.py:148 | KNOWN (settled) |
| R9-K3 | 1/3 | Low | R9-K3: inherited state schema remains 933 lines, over R13 | src/ovcaq/state/schema.py:1 | KNOWN (settled) |
| R9-K4 | 1/3 | Low | R9-K4: universal implementation-base fail-first binding remains unproven; this cycle's replay was skipped outright (worktree creation denied) | N/A | KNOWN (settled replay limitation) |

## Adjudication

R12-01 was independently reproduced by the coordinator; it was not raised by
any of the three reviewers and is not counted as reviewer consensus. The source
helper checks only missing directories. A real child exit (73) after mkdir and
before parent fsync bypasses OSError cleanup, leaving an existing unconfirmed
entry. Fresh installed retry and exact replay both exit 0 and omit that parent
fsync. State and ledger bytes are retained in the probe. This is observed syscall
durability evidence and consequent data-loss risk, not a claim of observed
physical power-loss loss.

R11-01 (prospective composed-ledger validation) and R11-02 (serialized report
read/compose/publish) remain repaired. R11-03 is correct for ordinary execution
and caught fsync failures but incomplete for abrupt process exit. Alice's and
Bob's raw repaired verdicts remain below; the coordinator's stronger crash
evidence changes the final disposition. The all-durable-boundaries exit and
P02-T06/T09 cannot be signed off yet. All 55 owned rows and all three phase exits
were reconciled; the remaining gap is explicit rather than waived.

F1 is accepted for its misleading deferred-ledger message on report contention.
The optional suggestion to assign a different machine error code is not adopted:
the reviewed contract does not establish that change, and it would broaden the
task beyond correcting context. F2 joins the runtime-ancestor repair while
preserving ownership checks. F3 and F5 share the bounded test-evidence task.

F4 is discarded after reading reports.py:676–712, workflow_cli.py:161, and the
R10 repair handoff. The public Path-returning API was deliberately retained while
the CLI obtains the complete composed text from the same publication. Both paths
have callers and share one implementation; removing or renaming that public
contract is not a necessary simplification. The reason is recorded in the
settled-decisions ledger.

V1 is satisfied by the five actual coordinator runs at this HEAD. Its queue
records the executed commands, requested mise-prefixed equivalents, results and
evidence; no duplicate suite was run. There is no previous cycle-11 check queue
to carry forward. The mechanical OR assertion is absorbed into R8-K1.

K1 is retained because historical malformed-ledger repair/import is outside this
fresh-state extraction, not because unreleased software makes local bad ledgers
impossible. K2 is a loud render-root prerequisite, not a lost-publication path.
R8-K1/K2 and R9-K3/K4 stay settled. The latest replay advanced past sandbox
worktree denial and reached the retained packaging_support collection failure;
raw earlier reviewer wording is preserved without claiming a full-base pass.

The core run-autopilot Error Handling row says **Detected data-loss risk → PAUSE**
in both modes. That mandatory safety pause takes precedence over ordinary
cap-overflow deferral. Cycle 12 and cap 2 are preserved; no cap-deferred convergence
or cycle increment is fabricated. The exact outstanding task and repair
acceptance are persisted for a later work session.

## Dispatch and method evidence

Alice: native Codex gpt-5.6-sol, logical sonnet, isolated prompt, fork_turns=none,
agent /root/alice_r12. Blake: the same actual model and logical tier, independently
isolated, agent /root/blake_r12, PRD-only with no diff, file list, history, plan of
the implementation, handoff or sibling findings. The linked accepted source plan
is part of the PRD specification. No native model-diversity claim is made.

Bob: fresh external Anthropic Claude via the authorized autocodex helper,
logical opus, requested alias opus, actual raw-event model claude-opus-5.
This is the explicit Claude Bob host substitution for the former external Codex
role. The initial sandbox dispatch exhausted API retries with ENOTFOUND and no
inference; immutable raw JSONL and stderr remain beside the successful retry.
The sole permitted retry received normal network permission and exited 0 with
the receipt above. No Codex CLI, resumed Codex thread, fake Eve dispatch, Fable
substitution or guard bypass occurred. The attached imported task store has no
attempt records, so its literal Codex-implementor predicate counts zero; that
absence is not evidence about all historical implementations.

Bob ran static analysis and no product tests/builds. His receipt's raw events
show 22 Read calls and 11 read-only shell inspections (wc, rg, git), despite the
persona's no-shell instruction. This method deviation is retained explicitly;
none changed files or executed product code. His findings remain usable static
evidence. Alice's verification sentence refers to the supplied prior repair
handoff; the coordinator independently reproduced the same 1,348-test pass this
cycle.

Carl: unavailable, runner exit 3, “refusing nested dispatch (already inside a CLI
agent)”; no backend/model was dispatched, no output was consolidated, no unchanged
retry or guard bypass occurred. No permanent-unavailability batch latch applies.
Engram pack: failed because this checkout is unregistered; no registration or
capsule refresh was performed. The Watcher ended DONE after the successful Bob
output, and every reviewer process and subagent was awaited before saving native
reviewer output files.

All twelve consensus R rules (R1–R4/R6–R13), B1–B19 and Bob's D1–D5 are retained
verbatim in their corresponding sections. The source consensus rubric has no R5.
D1–D5 retain the requested doubt R1–R5 intent under the installed identifiers.

## Alice

[ALICE] ✅ No issues found

Coverage reconciliation:

- P02-T01: selection order, hold exclusion, lifecycle paths, missing/non-directory/symlink handling covered by `selection.py`, `paths.py`, configuration tests, and installed CLI tests.
- P02-T02: frontmatter defaults, validation, warnings, abstract tier handling, transactional application, and wrong-PRD rejection covered.
- P02-T03: every transition and rejection row, full effect sets, terminal drain, purity, and one-CAS `phase-complete` covered.
- P02-T04: build/review/paused/done resume rows and plan shape/ceiling policy covered.
- P02-T05: exact per-PRD reset ownership, preserved batch state, deterministic completion summaries, conflict rejection, and idempotence covered.
- P02-T06: deferred ledger locking, operation-ID deduplication/conflict rejection, strict decoding, publication boundaries, and replay covered.
- P02-T07: stall/park intent, move, record, reset, commit, identity checks, failpoints, recovery fencing, exact replay, and systemic second-park behavior covered.
- P02-T08: deterministic audit/report/metrics rendering, golden output, metric reduction, report section replacement, archive behavior, publication identity, and idempotence covered.
- P02-T09: configured `dev/local/ovcaq` root, overrides, traversal/symlink rejection, and absence of legacy runtime strings covered.
- P02-T10: complete installed command family and parser-derived documentation contract covered.

All 55 ownership IDs reconcile to implementation and tests:

- `frontmatter.py`: CMD-014, TEST-006.
- `policy.py`: CMD-012, DEC-071, TEST-012.
- `records.py`: ART-016, ART-017, ART-026, CMD-007, CMD-008, CMD-010, CMD-036, DEC-076, DEC-077, DEC-078, DEC-079, DEC-080, DEC-081, DEC-082, ENV-025, STATE-112, STATE-113, STATE-121, TEST-001, TEST-002, TEST-008, TEST-013, TEST-014, TEST-015, TEST-016, TEST-017, TEST-038, TEST-052.
- `reports.py`: ART-012, ART-013, ART-014, ART-039, ART-040, ART-041, CMD-018, CMD-019, CMD-020, TEST-018, TEST-019, TEST-020, TEST-062.
- `resume.py`: CMD-016, TEST-021.
- `selection.py`: ART-036, CMD-013, TEST-027.
- `transitions.py`: CMD-009, CMD-015, TEST-029.
- Workflow boundary suite: TEST-005.

Every source phase exit is supported:

- Current lifecycle fixtures have equivalent OVCAQ outcomes under the v1 schema through characterized fixture, transition, resume, application, and installed-command coverage.
- Park/stall interruption is recoverable at every durable boundary through saga failpoint, publication, identity, recovery, and installed-wheel coverage.
- Workflow imports no runtime, driver, TUI, or launcher module; AST import guards and forbidden provider/legacy-string guards enforce this boundary.

Prior repair verification:

- R11-01 verified: the prospective complete ledger is canonicalized, decoded, and subjected to reader-equivalent bounded JSON validation before disk mutation. Installed regressions accept depth 30, reject depths 31–33 with `resource_limit`/11, preserve prior ledger and authoritative state bytes, retain subsequent writability, and verify replay behavior.
- R11-02 verified: report read, composition, and publication now occur under directory-inode serialization. The installed overlapping-publisher regression requires every successful publication to remain present, retries a busy publisher, preserves prior and unrelated sections, checks exact replay, and confirms returned text equals published bytes.
- R11-03 verified: missing runtime ancestors are created top-down and each new entry is confirmed by fsyncing its parent. Installed regressions inject failures at project parent, intermediate parent, runtime root, and deferred leaf; retry resumes from the failed boundary, preserves confirmed ancestors, keeps state authoritative, and avoids duplicate ledger entries.

The coordinator-provided verification reports 1,348 passing tests with zero failures or skips, plus clean Ruff, formatting, mypy, build, and diff checks. No new debug markers, placeholders, unsafe command construction, secrets, swallowed errors, or scope additions were found.

Settled limitations remain reflected in the binary rubric: R2 fails because universal implementation-base fail-first binding is unproven and the inherited collision test contains the accepted either-or assertion; R12 fails for the inherited 53-line `StateService.add_task`; R13 fails for the inherited 933-line state schema. These are the preserved R8-K1, R8-K2, R9-K3, and R9-K4 limitations and are not new findings.

R1: pass
R2: fail
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: fail
R13: fail

## Blake

[BLAKE] ✅ No issues found.

Evidence: inspected all workflow production modules, workflow CLI registration/dispatch, generated operations documentation, configuration/path handling, and the Phase A–C test suites. The implementation covers the six transition rows and rejection matrix, deterministic selection, frontmatter tier policy, plan validation, resume/reset/completion behavior, durable defer/park/stall recovery boundaries, guarded atomic file publication, deterministic renderers, CLI output/error contracts, and provider/layer boundary guards. No unauthorized dependencies, provider coupling, legacy runtime paths, or out-of-scope workflow features were found.

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

## Bob — doubt + de-slop review, PRD 00004 cycle 12

HEAD `39ecaf4f95c79df6a88c30e4626386a352d1505b` confirmed; working tree clean (`git status --porcelain -uall` empty, `git log -1` proves the command shape). Static review only — no tests, linters, or builds run.

### Prior-finding verification (read, not executed)

**R11-01 — repaired.** `_files.py:82` `_validate_record_encoding` canonicalizes the *composed* ledger, then applies the reader's exact pair (`decode_json` + `validate_json_value(…, "deferred")`) before anything touches disk, and `_write_record_file:105` runs it outside the `try`, so a rejection leaves prior bytes untouched. Depth arithmetic checks out against `MAX_JSON_DEPTH = 32` (schema.py:36): with the `{batch_id, items:[…]}` envelope the innermost value of a depth-*d* record lands at `d+2`, so 30 passes and 31+ raise `ResourceLimitError`. Depth 33 was already refused by the per-item check at `_deferred_item:242`, which makes it an honest control rather than new coverage — consistent with the handoff's 5-failed/4-passed fail-first split.

**R11-03 — repaired.** `_ensure_directory_chain` (`_files.py:252`) walks up to the first existing level, then creates top-down and confirms each new entry by fsyncing its parent, removing the just-created child if that fsync fails so a retry rediscovers the same boundary. Chain order for `project/new/nested/deferred` is `project → new → nested → deferred`, matching the four parametrized failure points. Symlinked ancestors cannot reach this code: `config.workflow_settings:95` routes the configured root through `paths._reject_symlink_components`.

**R11-02 — repaired.** `reports._publish_report:705-712` now holds the reports-directory `flock` across read → compose → publish. The pause point the actor patches (`_publish_file`) sits *inside* that lock, so a contender is refused rather than silently overwriting. `_assert_overlap_publication_state:456-459` is the binding assertion: it demands that any publisher that exited 0 has its section in the artifact, which is exactly what the pre-change code violated.

### Issues

```
[BOB] 🟡 F1: Report publication contention reuses the deferred ledger's message and the generic state_io code, so a supervisor can only tell "retry me" from a real disk failure by string-matching the word "retry" | File: src/ovcaq/workflow/_files.py:75 | Task: P02-T08
[BOB] 🟡 F2: _ensure_directory_chain dropped exist_ok, so a peer creating the same missing runtime ancestor makes defer fail with a bare FileExistsError; the sibling helper paths.ensure_runtime_directory:102 handles that case | File: src/ovcaq/workflow/_files.py:265 | Task: P02-T06
[BOB] 🟡 F3: Assertion cannot fail as written: delegated_calls counts every fsync and directories counts a labeled subset, so the inequality holds by construction | File: tests/packaging/test_rework_11.py:278 | Task: P02-T06
[BOB] 🟡 F4: reports.publish_report has no production caller; workflow_cli reaches into the module-private reports._publish_report instead | File: src/ovcaq/workflow/reports.py:676 | Task: P02-T08
[BOB] ⚪ F5: FSYNC_SCENARIO emits state_changed_while_interrupted; no assertion reads it | File: tests/packaging/rework_11_scripts.py:202 | Task: P02-T06
[BOB] ⚪ V1: Cannot statically verify: suite, ruff, format, mypy, and build gates at the reviewed head | File: N/A | Task: general
[BOB] ⚪ K1: A ledger written past the reader's depth limit by a pre-fix build stays unreadable and unappendable; the repair is prospective only | File: src/ovcaq/workflow/_files.py:82 | Task: P02-T06
[BOB] ⚪ K2: render report requires runtime_root to already exist while defer now creates its chain | File: src/ovcaq/workflow/reports.py:507 | Task: P02-T08
[BOB] 🟡 R8-K1: inherited config-collision test retains the mechanically flagged either-or assertion | File: tests/state/test_cli.py:372 | Task: general
[BOB] ⚪ R8-K2: inherited 53-line add_task and three unchanged packaging functions exceed R12 | File: src/ovcaq/state/commands.py:148 | Task: general
[BOB] ⚪ R9-K3: inherited state schema remains 933 lines, over R13 | File: src/ovcaq/state/schema.py:1 | Task: general
[BOB] ⚪ R9-K4: universal implementation-base fail-first binding remains unproven; this cycle's replay was skipped outright (worktree creation denied) | File: N/A | Task: general
```

### Buckets

```
FIX:
- [BOB] 🟡 F1 report contention message/code — src/ovcaq/workflow/_files.py:75, used from reports.py:707 — add a `label` parameter to `_serialize_deferred_publication` (default "deferred") so the report path raises "report publication busy; retry: <…>-report.md"; optionally map contention to REVISION_CONFLICT rather than STATE_IO, which already means "contention, retry" in errors.py:28.
- [BOB] 🟡 F2 concurrent ancestor creation — src/ovcaq/workflow/_files.py:265 — wrap `level.mkdir()` in `try/except FileExistsError`, still fsync `level.parent`, and skip the `rmdir` compensation for a level this process did not create.
- [BOB] 🟡 F3 always-true assertion — tests/packaging/test_rework_11.py:278 — assert the delegated label sequence contains the required labels in expected order, or drop the line; `assert failed["delegated_calls"] > 0` at :263 is weak for the same reason.
- [BOB] 🟡 F4 single-caller indirection — src/ovcaq/workflow/reports.py:676 and src/ovcaq/workflow_cli.py:161 — promote the two-value function to public (`publish_report_text`) and either delete `publish_report` or define it in terms of the public one, updating the ~10 workflow-test call sites.
- [BOB] ⚪ F5 dead evidence key — tests/packaging/rework_11_scripts.py:202 — assert it in test_rework_11.py or remove the key.
VERIFY:
- [BOB] ⚪ V1 gates at reviewed head — run `mise exec -- uv run pytest`, `mise exec -- uv run ruff check .`, `mise exec -- uv run ruff format --check .`, `mise exec -- uv run mypy src/ovcaq`, and `mise exec -- uv build` at `39ecaf4f95c79df6a88c30e4626386a352d1505b`; retain results. Coordinator reports 1348 passed / 0 failed / 0 skipped in 22.14s plus clean ruff, format (119 files), mypy (51 files) and build — supplied as evidence, not reproduced here.
KNOWN:
- [BOB] ⚪ K1 poisoned pre-fix ledger — out of scope: the accepted repair was prospective validation only, and the package has no released version (CHANGELOG carries `[Unreleased]` alone), so no such ledger can exist in the field.
- [BOB] ⚪ K2 render vs defer root creation — out of scope: R11-03 was scoped to deferred publication; render fails loudly with no durability loss and no PRD clause requires it to create the configured root.
- [BOB] 🟡 R8-K1 — settled inherited assertion; broad state-test restructuring excluded.
- [BOB] ⚪ R8-K2 — settled inherited function sizes; preserve the accepted exceptions.
- [BOB] ⚪ R9-K3 — settled inherited schema size; state restructuring excluded.
- [BOB] ⚪ R9-K4 — settled; the base-worktree replay is a retained known limitation, not retried.
```

Count conservation: **12 = 5 FIX + 1 VERIFY + 6 KNOWN**.

Reconciled all ten source tasks and the three phase exits. The installed command family is complete (`workflow_cli.py:64-134`), docs are byte-compared against the live parser (`test_workflow_cli.py:373`), and `dev/local/autopilot` is guarded as a forbidden string (`test_boundaries.py:19`). The `_finish_record_publication` extraction preserves the boundary-hook order exactly; the only behavioral difference is a post-replace `os.unlink` of the temporary name that always hits the swallowed `FileNotFoundError`, which the existing failpoint replay tests would catch if it removed the published file. All files are within 800 lines except the settled `schema.py`; the new 576-line test file respects the 50-line function limit throughout.

R1: pass
R2: fail
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: fail
R13: fail
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

---

**Status**: Done.
**Changed**: nothing — review only, no files written.
```
HEAD 39ecaf4f95c79df6a88c30e4626386a352d1505b
git status --porcelain -uall -> (empty)
12 findings = 5 FIX + 1 VERIFY + 6 KNOWN
```
**Next**: Task complete. Suggested next: route F1–F5 into the cycle-12 rework handoff; F2 is the only one with a correctness edge (concurrent defer against a missing runtime root).

Verdict: 13 findings
Tests: 1348 passed, 0 failed, 0 skipped (suite run this cycle)
