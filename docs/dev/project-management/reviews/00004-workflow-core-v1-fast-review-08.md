---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
review: 8
review_id: FT-04R8
date: 2026-09-05
head_sha: 8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7
base_sha: b43bf2c94d5eb0fddafca55542ef2570b45e8d52
repair_base_sha: 47a8764760e1fedb82eb1514a344584fb7ad2f3e
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: disabled
outcome: CHANGES_REQUESTED
---

# FT-04R8: PRD 00004 fresh completion review

Diff range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`

codex_rung_guard: not fired

**CHANGES_REQUESTED — eight actionable root causes: three high and five medium.** Seven behavioral defects were independently reproduced by the coordinator; the eighth is a measured test-structure violation. Two inherited findings are also retained below as KNOWN, making ten total findings in the skill's terminal count. Passing tests do not establish the required recovery and reporting guarantees.

The full nine-commit implementation (57 changed files, +8844/-263), including FT-04F7, was reviewed against P02-T01–P02-T10 and all 55 owned characterization rows. HEAD and empty Git status were verified before review. No implementation, PRD, source plan, or autopilot state was changed.

This is a standalone review: findings are reported here, **not written as autopilot tasks**. The user prohibited attaching an unrelated task store, prior reviews, old handoffs, or old raw reports. Only coordinator/Alice read rework-07.md. No stored implementor predicate was inspected, so the guard line records the standalone route, not a claim that the implementation used no Codex. No model-diversity claim is made.

## Consolidated findings

Consensus counts actual lens agreement out of three. The table is ordered by consensus then severity; repair priority follows severity. The coordinator's independent finding has zero lens votes and remains blocking on its reproduced evidence.

| ID | Consensus | Severity | Root cause and location | Found by | Disposition |
|---|---|---|---|---|---|
| R8-01 | 2/3 | High | Deferred-ledger reads discard duplicate keys and allow unbounded JSON nesting; `src/ovcaq/workflow/_files.py:131` | Blake, Bob; coordinator reproduced | FIX |
| R8-08 | 2/3 | Medium | New oversized multi-scenario tests and growth of an already oversized test module; `tests/workflow/test_workflow_cli.py:81` | Alice, Bob; coordinator measured | FIX |
| R8-K1 | 2/3 + mech-check | Medium | Unchanged collision test accepts either a directory or symlink; `tests/state/test_cli.py:372` | Alice, Bob, mechanical check | KNOWN, inherited |
| R8-02 | 1/3 | High | Stall/park artifact identity is established too late and lost across restart; `src/ovcaq/workflow/records.py:569` | Alice; coordinator reproduced six variants | FIX |
| R8-04 | 1/3 | Medium | Earlier PRDs' deferred/stalled details disappear unless already rendered; `src/ovcaq/workflow/reports.py:310` | Bob; coordinator reproduced | FIX |
| R8-05 | 1/3 | Medium | Report path creation and identical-content retry omit required directory durability; `src/ovcaq/workflow/reports.py:475` | Bob; coordinator instrumented | FIX |
| R8-06 | 1/3 | Medium | Schema-valid blank decisions are counted and rendered; `src/ovcaq/workflow/records.py:147` | Alice; coordinator reproduced | FIX |
| R8-07 | 1/3 | Medium | Named PRD, record, and configuration inputs block on FIFOs; `src/ovcaq/cli_io.py:19`, `src/ovcaq/config.py:36` | Alice; coordinator reproduced | FIX |
| R8-K2 | 1/3 | Low | Inherited 53-line `StateService.add_task`; `src/ovcaq/state/commands.py:148` | Bob; coordinator compared base | KNOWN, inherited |
| R8-03 | 0/3 | High | Replaced sidecar lock allows a successful append to be overwritten; `src/ovcaq/workflow/_files.py:193` | Coordinator | FIX |

### R8-01 — reject malformed ledgers before decoding loses evidence

P02-T06/P02-T08; ART-016, STATE-112/113, CMD-010/019, TEST-014. A ledger with two `items` keys, the first containing `keep-me`, is accepted and rewritten without that retained record. A ledger containing 10,000 nested arrays raises uncaught `RecursionError`; the coordinator's `--json workflow render report` exits 1 with a traceback, and Blake reproduced the defer command path too.

Use the existing guarded decoder (`state/schema.py:437`) or equivalent strict lower-layer behavior for ledger reads, preserving contextual symbolic CLI errors. Reject duplicate keys and excessive nesting before publication; state and ledger bytes must remain unchanged. Cover installed defer and report entry points as well as lower-layer parsing. Bob rated this medium; the reproduced silent record loss warrants high.

### R8-02 — retain the identity of the original PRD through recovery

P02-T07; CMD-007/008, DEC-077/078, TEST-016/017 and the phase's every-boundary recovery criterion. Both stall and park accept a different PRD artifact when the source is replaced just before rename, the held path is replaced at `AFTER_RENAME_BEFORE_DIRECTORY_FSYNC`, or the held path is replaced after a recorded-stage interruption and the operation restarts. All six calls complete with the replacement at the held path, no unfinished tasks, and no recovery intent.

Bind the operation to the source artifact before moving it and retain verifiable identity through every durable stage and restart. Conflict must preserve unfinished state and recovery evidence instead of resetting it. The probe deliberately retains the original at another temporary path to prove the substitution; success nevertheless detaches lifecycle state from that original. Preserve the existing directory and publication fences.

### R8-03 — fence the ledger lock until publication is complete

P02-T06; ART-017 explicitly requires an independent sidecar lock serializing ledger updates. At `DeferBoundary.BEFORE_PUBLISH`, rename the held lock aside and call a second legitimate `record_defer`. The second call acquires the replacement lock and succeeds. The original call then succeeds too, publishing only `first` and silently losing `second`.

Verify the lock pathname still names the owned lock through the read/modify/publication boundary, with a safe refusal/recovery contract when it changes. Preserve the competing successful append. Add a regression that asserts both the public result and durable record contents. The bounded reproduction uses nested calls at the boundary to create the same interleaving; it is not a stress-test estimate. Do not add a second state writer.

### R8-04 — reconstruct all batch deferred details

P02-T08; ART-013 and CMD-019. Render a batch report for the current PRD with an earlier PRD's stall record, without any previously published report. The report says `Deferred records: 1` but contains neither the earlier PRD, its operation ID, nor its detail. Preserving old Markdown sections cannot supply a section never written.

Render deferred/stalled details with PRD attribution for the whole batch independently of report history. Test the first rendering after moving to another PRD, then rerender to verify deterministic replacement and deduplication.

### R8-05 — complete directory durability on creation and retry

P02-T08; durable ART-012/013/014 and report/archive publication. Fsync instrumentation shows new `reports/` is synced but its runtime parent is not after creation. An injected directory-fsync failure after replacement leaves the intended bytes present; retry returns success with **zero directory fsync calls** because identical bytes trigger an early return at `reports.py:520`.

Sync verified parent directories when establishing publication paths, including retry after prior creation, and finish directory durability before accepting identical-content replay. Cover the shared report/audit/archive publisher while retaining nonregular-output refusal and descriptor identity checks. This evidence establishes missing durability operations; no physical power-loss experiment was performed.

### R8-06 — honor the retained blank-decision contract

P02-T05/P02-T08; TEST-019 and TEST-052 explicitly require filtering wholly blank autonomous decision content while preserving zero and populated cells. `validate_state` accepts `{"id":"","kind":"","summary":"","rationale":"","cycle":null,"created_at":"2026-09-05T10:00:00Z","status":"applied"}`. Completion counts one autonomous decision and audit rendering emits `|  | applied |  |  |  |  |`.

Filter substantive blank decision content consistently in counts and rendering, or explicitly reject this shape at the authoritative boundary with equivalent source-contract coverage. An applied status and timestamp alone must not defeat blank-content filtering. Pin blank, zero, and partially populated cases.

### R8-07 — reject nonregular named inputs without blocking

P02-T02/P02-T06/P02-T09; installed command error behavior and configured-path inputs. A FIFO without a writer supplied to `frontmatter --prd`, `defer --record`, or as project `ovcaq.toml` makes each CLI child exceed a two-second timeout. Each was killed and reaped; durable state stayed unchanged.

Open named file inputs nonblockingly and validate regular-file type before reading, using bounded CLI regressions and symbolic machine errors. Apply the existing nonregular-metrics approach consistently without weakening safe path handling. This finding concerns the documented file inputs, not a newly requested streaming interface.

### R8-08 — split new oversized test scenarios without losing coverage

General review rubric R1/R2/R7; acceptance applies to tests as supplied, with no production-only exemption. New examples are 138/132 lines at `test_workflow_cli.py:81/288`, 93 at `test_sagas.py:322`, and 117 at `test_installed_sagas.py:411`. The touched `tests/state/test_service_commands.py` grew from 851 to 962 lines (+111).

Split independent scenarios and coherent recovery/state groups; extract reusable setup where it reduces duplication, including the existing installed-root helper. Inspect the retained AST measurements for all new violations. Preserve lifecycle sequences, assertions, parametrized boundaries, and installed-wheel origin checks; rerun entire workflow/packaging directories and the full suite after splits. Do not broaden this into restructuring inherited production state services.

## Adjudication and retained disagreements

The installed consolidation script succeeded and emitted 14 raw rows. Coordinator root-cause adjudication merged Bob F2 with Blake's ledger-decoder finding, Alice/Bob/mechanical collision findings into R8-K1, and the two new-test size findings into R8-08. R8-03 was added from independent probing. [Raw consolidation](00004-cycle-08-consolidated-raw.md) remains unchanged.

R8-K1 is explicitly absorbed, not silently discarded: the flagged `is_dir() or is_symlink()` assertion is unchanged from the base. The only changes in its file rename a docs test and add the workflow parser inventory. Earlier assertions can still fail, so the detector's generic “test cannot fail” description overstates the weakness. Its weak collision-identity assertion remains an inherited KNOWN finding, with no PRD-00004 repair requested.

R8-K2 retains the inherited 53-line production method as KNOWN; the change is the transaction wrapper call, not newly added method complexity. Bob treated the already oversized state-test file as inherited too; Alice objected to its new growth. The coordinator accepts the bounded new-test split in R8-08 and excludes broad inherited cleanup.

Bob V1 is resolved by fresh coordinator tests, lint, type-check, formatting, and build. Bob V2 prompted the complete test-overlay replay supplement: 54 touched parametrized cases fail on base, zero pass; absent base modules still prevent collection of other new tests. This is limited fail-first evidence, not proof that every added assertion binds its behavior. No replay finding claiming a touched test passes on base was produced. The tooling limitation and full output are retained in the evidence file.

Blake's covered-case passes for park/stall and completion do not refute R8-02/R8-06. Bob's reference to strict v1 decision shapes also does not exclude the schema-valid blank probe. All raw rule verdicts remain unchanged. A reproduced defect is not dismissed for lacking multiple votes.

## Alice

Fresh native Codex subagent, consensus persona/rubric; complete implementation context and rework-07.md. No external Claude engine is claimed. Reported artifact identity, FIFO input, blank decisions, mechanical collision preservation, and test-size findings. Independently ran 346 focused tests successfully.

[Exact prompt](../tmp/alice-prompt-00004-cycle-08.md) · [Unmodified report](../tmp/alice-output-00004-cycle-08.txt)

R1: fail
R2: fail
R3: pass
R4: pass
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: fail

## Blake

Fresh native Codex subagent, blind PRD/source-contract access and B1–B19 rubric only. Located implementation independently; received no diff, task narrative, repair handoff, or other reviewer findings. Reproduced malformed-ledger data loss and deep-nesting failure. Independently verified 365 workflow/packaging cases (361 sandbox, four socket cases on an escalated rerun).

[Exact prompt](../tmp/blake-prompt-00004-cycle-08.md) · [Unmodified report](../tmp/blake-output-00004-cycle-08.txt)

B1: fail
B2: fail
B3: fail
B4: pass
B5: fail
B6: pass
B7: pass
B8: pass
B9: pass
B10: fail
B11: pass
B12: fail
B13: pass
B14: fail
B15: pass
B16: fail
B17: fail
B18: pass
B19: pass

## Bob

Fresh native Codex fallback after the prescribed external runner refused nested dispatch. Static PRD/diff/source review with every consensus rule and the doubt/de-slop rubric, plus FIX/VERIFY/KNOWN dispositions. No repair handoff or another lens's output. Bob did not run tests; coordinator verification resolves the executable checks above.

The installed doubt rubric uses D1–D5 for the five obligations called R1–R5 in the continuation. Both the consensus R-series and doubt D-series were supplied in full and are retained below; no lens or rule was omitted.

[Exact prompt](../tmp/bob-prompt-00004-cycle-08.md) · [Unmodified report](../tmp/bob-output-00004-cycle-08.txt)

R1: fail
R2: fail
R3: pass
R4: pass
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: fail
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Execution, coverage, and handoff

Alice, Blake, and Bob each started with `fork_turns=none`. All completed before any raw output was saved. No cross-reviewer findings were shared. All three used the inherited native host model: this supplies independent contexts, not model diversity.

The optional Carl/Gemini runner refused nested dispatch twice, so no Carl report exists or is counted. Bob's native fallback was the permitted host adaptation; no wrapper guard was bypassed. Eve was not opted in, and no unrelated state predicate was consulted. The legacy consensus path ran; no workflow/shadow run or external thread ID is claimed. See [dispatch evidence](00004-cycle-08-dispatch.md).

The [evidence record](00004-workflow-core-v1-fast-review-08-evidence.md) retains exact SHAs, all ten task assessments, all 55 row mappings, retained fixtures, fresh verification, reproductions, mechanical checks, replay limitations, and artifact inventory. Full suite: 1,252 passed in 18.02s; Ruff, format, mypy, build, full-range whitespace checks passed.

Next gate: [FT-04F8 repair handoff](../tmp/00004-handoff-20260905-1250.md) addresses R8-01–R8-08 with regressions, then hands off and stops for fresh FT-04R9 review. PRD completion remains unapproved. The standalone [contract card](00004-cycle-08-contract-card.md) stays outside autopilot state as required by this session's scope. The saved-file shape gate and final artifact audit passed; HEAD/status/stashes/worktrees remained unchanged and clean before the 12:50 CEST handoff.

Verdict: 10 findings
Tests: 1252 passed, 0 failed, 0 skipped (suite run this cycle)
