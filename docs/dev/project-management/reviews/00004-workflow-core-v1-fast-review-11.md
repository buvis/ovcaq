---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
review: 11
date: 2026-09-06
head_sha: 22d9193a0d00486b09ebea169e7a38a9f858799d
reviewers: alice,blake,bob
mode: standalone
consensus_engine: legacy
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
  eve: disabled
---

# FT-04R11 — PRD 00004 completion review

Diff range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..22d9193a0d00486b09ebea169e7a38a9f858799d`

codex_rung_guard: not fired

**CHANGES_REQUESTED — three actionable findings: two High, one Medium.**
R10-01 is verified repaired. R8/R9 repairs, including the coordinator-only
ledger serialization root, remain preserved. Terminal accounting:
**7 = 3 FIX + 0 VERIFY + 4 inherited/methodological KNOWN**.

Full review of P02-T01–T10, all 55 owned rows and all phase exits. Fresh suite:
**1339 passed in 23.83s**, zero failures/skips. Sync, Ruff, formatting, mypy,
build and full-range whitespace pass. All product/source/test/doc files remain
unchanged at the reviewed HEAD; no PRD closeout or next PRD.

[Source and probe evidence](00004-workflow-core-v1-fast-review-11-evidence.md) ·
[Installed raw results](00004-cycle-11-probes.json) ·
[Script consolidation](00004-cycle-11-consolidation-raw.md) ·
[Dispatch](00004-cycle-11-dispatch.json)

## Consolidated findings

| ID | Consensus | Severity | Finding | Source | Disposition |
|---|---|---|---|---|---|
| R11-01 | 1/3 + coordinator | High | A valid standalone record becomes unreadable after its ledger envelope adds two nesting levels; append succeeds, then load/replay/subsequent append refuse | Bob; _files.py:311; P02-T06 | FIX |
| R11-03 | 1/3 + coordinator | High | Deferred publication omits fsync of newly created runtime ancestors' parents, including exact retry | Bob; _files.py:233; P02-T06/T09 | FIX |
| R11-02 | 2/3 + coordinator | Medium | Concurrent report read/compose/publish loses a successfully published PRD section | Blake, Bob; reports.py:701–706; P02-T08 | FIX |
| R8-K1 | 2/3 + mech-check | Medium | Inherited collision OR assertion | tests/state/test_cli.py:372 | KNOWN |
| R8-K2 | 2/3 | Low (settled) | Inherited 53-line add_task and unchanged packaging size exceptions | state/commands.py:148 | KNOWN |
| R9-K3 | 2/3 | Low (settled) | Inherited 933-line state schema | state/schema.py:1 | KNOWN |
| R9-K4 | 2/3 | Low | Universal implementation-base fail-first binding remains unproven | N/A | KNOWN |

## Evidence and bounded follow-up

**R11-01 — validate the composed ledger before publishing.** Installed console
append at standalone depths 31 and 32 returns exit 0. Loading raises
ResourceLimitError; exact replay and a subsequent seed-record append both return
resource_limit/exit 11. The existing seed remains in the JSON bytes but the
complete ledger is unusable through its readers. Depth 30 is a passing control;
depth 33 refuses before changing the existing ledger. Every case preserves
authoritative state bytes. This is a writer/reader validation mismatch, separate
from R8's correctly strict decoder.

**R11-03 — make the entire created directory chain durable.** With an existing
independent state file and a configured missing `new/nested` runtime root,
installed CLI dispatch successfully defers and replays. Instrumentation delegates
every fsync to the real syscall and records directory inodes: both invocations
sync `new/nested` and `new/nested/deferred`, but omit the project directory and
`new`. Those omitted calls are required to persist their newly created child
entries. Record and state bytes are valid during this run; this is syscall
durability evidence, not observed power-loss data loss. Complete interrupted
parent syncs on retry while preserving ledger locks and identity checks.

**R11-02 — serialize report composition through publication or reject stale
publication.** A real installed process pauses A immediately before native
publication, after composing its section. State switches to B through StateStore;
the unmodified installed console publishes B successfully. Resuming A also
succeeds but drops B from the final report. Both exit 0. The seed section survives
and A's returned text equals the final artifact, so R10-01 remains fixed.
An explicit B retry restores A+B; the initial successful B publication was still
lost. Preserve prior/unrelated sections, exact replay, path identity guards,
fsyncs, and complete returned text.

Each repair needs a chronological failing regression before production edits,
a bounded implementation, preservation tests and full gates. Detailed acceptance
is in [the fresh-work handoff](../plans/fast-track-handoffs/00004-workflow-core-v1/review-11.md).
Findings are reported here and in that handoff, not written into a task store.

## Adjudication and limits

Blake's missing-source objection is the settled null-artifact refusal. It does
not invalidate its stated reason: no original identity exists, so a later
unidentified file cannot be adopted. Preserve his raw High objection and failing
B verdicts below, but create no repair for it. No abort/rollback API is authorized.

Alice's no-new-findings assessment does not negate the installed reproductions.
The script emitted eleven rows. Coordinator merges report locations 701/702
and the two K2 phrasings, resolves Bob's V1 through fresh gates, and dismisses
the settled Blake objection with the reason above. The single MECH OR finding
joins K1. No finding is silently discarded. Raw severities and verdicts remain
unchanged; K2/K3 retain their settled Low disposition.

Alice ran 102 overlapping focused cases, all passing. All reviewer results were
received before their raw files were saved. Each lane used a fresh native host
context (`fork_turns=none`): Alice implementation-aware consensus, Blake PRD-only,
Bob static consensus plus doubt/de-slop. All twelve consensus rules
R1–R4/R6–R13, all B1–B19 and D1–D5 are retained. The installed rubric has no R5;
D1–D5 are the installed names for the requested doubt R1–R5.

External Bob/Carl nested-wrapper guards were not retried or bypassed. Native host
substitution provides prompt isolation; no native Claude or model diversity is
claimed. Eve was not enabled. The optional engram pack failed because this
checkout is unregistered; no registration or capsule refresh was attempted.

The existing paused PRD-00003 autopilot state is historical and unrelated. It was
read only to identify its target, never attached or mutated. PRD-00004 has no
attached task/attempt store; no review_lenses, doubt state, queue or task entries
were written into that file. The guard line above is for this standalone review.

Full-base replay remains skipped on the retained missing packaging_support
collection failure. R8's bounded replay remains 56 collected/46 failed/10
preservation passes; R9's 23 and R10's one chronological regression do not prove
universal full-base binding. Linux retains its downstream owner.

## Alice

[ALICE] 🟡 KNOWN R8-K1: inherited collision test retains the mechanically identified OR assertion; no new repair requested | File: tests/state/test_cli.py:372 | Task: general
[ALICE] ⚪ KNOWN R8-K2: inherited 53-line add_task and three unchanged packaging functions retain their accepted function-size exceptions | File: src/ovcaq/state/commands.py:148 | Task: general
[ALICE] ⚪ KNOWN R9-K3: inherited schema.py remains 933 lines; broad state restructuring is excluded | File: src/ovcaq/state/schema.py:1 | Task: general
[ALICE] ⚪ KNOWN R9-K4: universal implementation-base fail-first binding remains unproven; retained replay and chronological repair regressions establish narrower evidence | File: N/A | Task: general

No new actionable findings.

Reviewed the full implementation scope, accepted source contract, supplied repair evidence, workflow production modules, state integration, installed commands, and behavioral tests. Both characterization TOMLs parsed completely; all 55 owned source/evidence/disposition/target records and accepted source hashes match the supplied join.

Independent focused verification: **102 passed in 3.88s**, exit 0. This covered installed report updates and input integrity, ledger publication/integrity, report identity/recovery, and saga publication. Temporary roots were context-managed and children reaped. Coordinator owns the full gates; these overlapping cases are not an additional full-suite count.

| Repair | Assessment |
|---|---|
| R10-01 | Pass. CLI obtains path and complete composed text from the same verified publication. Installed A→B→A and all six render/replay results equal UTF-8 artifact contents. Earlier PRDs, unrelated Unicode sections, changed summaries, duplicate collapse, and unchanged state are asserted. Existing `publish_report` callers retain their Path return. |
| R9-01 | Pass. Opened-directory inode locking serializes reads and native replacement; comparison under that lock rejects stale snapshots after sidecar restoration. Nested/process rivals, successful earlier-boundary rivals, refusal evidence, and exactly-once retries remain covered. The coordinator-only lock root is explicitly retained. |
| R9-02 | Pass. Every configured output directory from root through leaf remains open and verified during traversal, publication, identical replay, and successful context exit. Sixteen report/audit/archive replacement cases preserve evidence and permit valid retry. |
| R9-03 | Pass. Deep project/user TOML failures become contextual usage errors without traceback, stdout, or state/configuration mutation. Both recognized and ignored keys are covered. |
| R9-04 | Pass. Shared `_section_span` supplies extraction and duplicate removal while retaining exact headings, boundaries, unrelated content, and goldens. |
| R9-05 | Pass. `_run` delegates to `_run_unchecked`; subprocess arguments, environment, cwd, capture, timeout, and diagnostics remain intact. |

| Source task | Assessment |
|---|---|
| P02-T01 | Covered: deterministic sequence ordering, WIP priority, backlog fallback, hold exclusion, missing/invalid directories, configured lifecycle roots. |
| P02-T02 | Covered: bounded parsing, defaults, warnings, abstract tiers, active-PRD binding, CAS, and settled returned-control ownership. |
| P02-T03 | Covered: six transition effect rows, rejection rows, atomic handoff, rework clearing, convergence, reset, terminal drain. |
| P02-T04 | Covered: recovery/pause/phase/task resume precedence, dependency validation, tolerant counting, ceiling and override behavior. |
| P02-T05 | Covered: exact reset owners, preserved batch/capability fields, deterministic summaries, conflicting completion refusal, substantive decision filtering. |
| P02-T06 | Covered: attributed deferred records, operation IDs, exact/conflicting replay, strict decoding, durable publication, repaired serialization. |
| P02-T07 | Covered: typed durable intent, original artifact identity, exclusive move, every durable boundary, recovery fences, atomic reset/commit, systemic park halt. |
| P02-T08 | Covered: deterministic audit/report/metrics, complete report results, section preservation, zero/unknown totals, batch scoping, archives and durable retries. |
| P02-T09 | Covered: configuration precedence, walk-up resolution, independent state override, containment and malformed/nonregular input handling. |
| P02-T10 | Covered: command reference and protocol inventory generated from the live parser and checked against installed commands. |

Every owned ID below was assessed as covered within its accepted extraction disposition:

| Evidence group | Owned IDs | Assessment |
|---|---|---|
| Selection | ART-036, CMD-013, TEST-027 | Ordering, lifecycle paths, filtering, and drain selection covered. |
| Frontmatter | CMD-014, TEST-006 | Parsing/application covered within the settled downstream-control boundary. |
| Policy | CMD-012, DEC-071, TEST-012 | Shape, counting, ceiling, override, and CLI error behavior covered. |
| Resume | CMD-016, TEST-021 | Committed-state precedence and schema preflight covered; launcher markers remain excluded. |
| Transitions | CMD-009, CMD-015, TEST-029 | Reset and every transition/rejection effect set covered. |
| Records | ART-016, ART-017, ART-026, CMD-007, CMD-008, CMD-010, CMD-036, DEC-076, DEC-077, DEC-078, DEC-079, DEC-080, DEC-081, DEC-082, ENV-025, STATE-112, STATE-113, STATE-121, TEST-001, TEST-002, TEST-008, TEST-013, TEST-014, TEST-015, TEST-016, TEST-017, TEST-038, TEST-052 | Typed-intent replacement for marker semantics, failpoint hooks, identity preservation, ledger serialization, replay/conflict handling, reset, completion, and installed dispatch covered. |
| Reports | ART-012, ART-013, ART-014, ART-039, ART-040, ART-041, CMD-018, CMD-019, CMD-020, TEST-018, TEST-019, TEST-020, TEST-062 | Retained fixtures, deterministic projections, complete machine results, section updates, blank/zero handling, unknown totals, and verified publication covered. |
| Documentation | TEST-005 | Parser-derived command coverage verified. |

All three source phase exits pass within the settled contract: lifecycle fixtures have equivalent v1 outcomes; park/stall interruptions reconcile or safely refuse while preserving evidence; workflow has no runtime/driver/event/TUI/launcher dependency. PRD Phases A, B, and C are covered. Initially absent sources retain null identity and failure evidence; this accepted boundary is not reopened.

No additional concrete simplification warrants rework. Descriptor lifetimes, identity checks, and publication guards preserve deliberate invariants. No new secrets, unsafe command evaluation, skipped/xfail tests, debug statements, or placeholder implementation were identified. Literal rubric failures below reflect the four settled observations, not new repair requests.

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

[BLAKE] 🟠 Missing PRD source creates unrecoverable intent: when the active PRD exists in neither WIP nor hold, `_begin_operation` commits `artifact=None` before failing. A disposable probe restored the source and retried; reconciliation still failed with “PRD artifact identity changed,” leaving normal workflow mutations permanently fenced. Reject absent sources before publishing intent. | File: src/ovcaq/workflow/records.py:559 | Task: P02-T07
[BLAKE] 🟡 Overlapping report renders silently lose successfully published PRD sections. `_publish_report` reads and composes without locking or compare-and-set; `_publish_file` then overwrites intervening changes. A disposable probe published the second PRD between the first render’s composition and publication; both calls succeeded, but the second section disappeared. Serialize the complete read/compose/publish operation or reject stale publication. | File: src/ovcaq/workflow/reports.py:701 | Task: P02-T08

B1: fail
B2: pass
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

[BOB] 🟠 F1: Defer validates an item before adding two ledger nesting levels, so a depth-31/32 record can publish successfully and then make loading, replay, and subsequent appends fail with ResourceLimitError. | File: src/ovcaq/workflow/_files.py:311 | Task: P02-T06
[BOB] 🟡 F2: Concurrent report publishers can read the same existing report, both return success, and overwrite the other publisher’s newly added PRD section. | File: src/ovcaq/workflow/reports.py:702 | Task: P02-T08
[BOB] 🟠 F3: Defer creates missing runtime ancestors with parents=True but syncs only the immediate runtime directory; successful publication can therefore lose its directory chain after interruption. | File: src/ovcaq/workflow/_files.py:233 | Task: P02-T06
[BOB] ⚪ V1: Cannot statically verify: full test, lint, formatting, typing, and build gates pass on the reviewed head. | File: N/A | Task: general
[BOB] 🟡 R8-K1: The inherited config-collision test retains the mechanically flagged either-or assertion. | File: tests/state/test_cli.py:372 | Task: general
[BOB] 🟡 R8-K2: StateService.add_task remains 53 lines, exceeding R12’s limit. | File: src/ovcaq/state/commands.py:148 | Task: general
[BOB] 🟡 R9-K3: The inherited state schema remains above R13’s 800-line limit. | File: src/ovcaq/state/schema.py | Task: general
[BOB] ⚪ R9-K4: Full implementation-base fail-first binding remains unverified; bounded repair evidence does not establish universal coverage. | File: N/A | Task: general

FIX:
- F1 — src/ovcaq/workflow/_files.py:311 — Validate the composed ledger before publication. Add boundary-depth cases proving accepted records remain readable and rejected appends preserve existing bytes.
- F2 — src/ovcaq/workflow/reports.py:702 — Serialize report read, composition, and publication. Add coordinated A/B publishers proving both sections survive or one caller explicitly retries.
- F3 — src/ovcaq/workflow/_files.py:233 — Durably create the complete missing directory chain and complete interrupted parent syncs on retry. Cover a new nested runtime root with an existing independent state file.

VERIFY:
- V1 — Run `mise exec -- uv run pytest`, `mise exec -- uv run ruff check .`, `mise exec -- uv run ruff format --check .`, `mise exec -- uv run mypy src/ovcaq`, and `mise exec -- uv build` on reviewed head `22d9193a0d00486b09ebea169e7a38a9f858799d`; retain results.

KNOWN:
- R8-K1 — Inherited assertion explicitly retained by the supplied scope decision.
- R8-K2 — Existing state-service function explicitly retained; broader restructuring is excluded.
- R9-K3 — Existing schema size explicitly retained; schema restructuring is excluded.
- R9-K4 — The full-base replay collection dead end is explicitly excluded from retry.

Count conservation: **8 = 3 FIX + 1 VERIFY + 4 KNOWN**.

Reviewed all ten source tasks, all 55 owned rows, and all phase exits. Both correctness and de-slop lenses applied; no additional simplification finding. The three unchanged inherited packaging overlength functions remain excluded as instructed.

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: pass
R11: pass
R12: fail
R13: fail
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 7 findings
Tests: 1339 passed, 0 failed, 0 skipped (suite run this cycle)
