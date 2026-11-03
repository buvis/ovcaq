# FT-04R8 evidence — PRD 00004

This record supports [the changes-requested review](00004-workflow-core-v1-fast-review-08.md): eight actionable roots, plus two inherited KNOWN findings. It records current-cycle evidence only. No prior reviews or handoffs were consulted except rework-07.md by coordinator/Alice.

## Identity and accepted contract

| Item | Verified value |
|---|---|
| Repository / branch | /Users/bob/git/src/github.com/buvis/ovcaq / master |
| Exact clean reviewed HEAD | 8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7 |
| Last commit | fix(workflow): fence saga publication and honor command inputs |
| Full implementation base | b43bf2c94d5eb0fddafca55542ef2570b45e8d52 |
| FT-04F7 repair base | 47a8764760e1fedb82eb1514a344584fb7ad2f3e |
| Scope | Nine commits; 57 changed files; +8844/-263 |
| PRD | dev/local/prds/wip/00004-workflow-core-v1.md, WIP v1 |
| Architecture authority | dev/local/plans/implementation-plan.md, read only |
| Plan SHA-256 | 43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5 |
| Characterization inventory SHA-256 | d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9 |
| Mandatory source inputs | AGENTS.md; dev/local/prds/implementation-plan-coverage.md; dev/local/discovery/00001-ovcaq-v1.md; tests/characterization/current_system.toml and migration.toml |
| Skill | /Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.0/skills/review-work-completion/SKILL.md |
| Installed plugin registry SHA | 57f10bb1911aa764c42c19e0bd194fddbc3f5209 |

The explicit full range replaces the skill's ordinary incremental/history route. Each source task has its own row in [the task context](../tmp/review-tasks-00004-cycle-08.md); no unrelated task store supplies completion assertions. Review records and the contract card remain in cycle-owned local paths. No autopilot state, ledger, capsule, retrieval pack, or prior-cycle checks were read or updated. Workflow isolation and native engine details are in [dispatch evidence](00004-cycle-08-dispatch.md).

## Independent verification

All coordinator commands below ran at the exact reviewed HEAD during this fresh review. Counts were observed, not reused from the repair handoff or last-verification state.

| Command | Observed result |
|---|---|
| `mise exec -- uv sync --all-groups` | Exit 0; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/workflow/test_reports.py tests/workflow/test_transitions.py tests/packaging/test_installed_cli.py -q` | Exit 0; 111 passed in 2.24s |
| `mise exec -- uv run pytest tests/workflow/ tests/packaging/ -q` | Exit 0; 365 passed in 9.48s; complete split-module replacement coverage |
| `mise exec -- uv run pytest` | Exit 0; 1252 passed in 18.02s; no failures/skips |
| `mise exec -- uv run ruff check .` | Exit 0; all checks passed |
| `mise exec -- uv run ruff format --check .` | Exit 0; 105 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | Exit 0; no issues in 51 source files |
| `mise exec -- uv build` | Exit 0; sdist and wheel built |
| `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..HEAD` | Exit 0; no whitespace errors |

Environment observed: Darwin, Python 3.13.13, pytest 9.1.1, mise-managed uv. Build outputs: `dist/ovcaq-0.1.0.dev0.tar.gz` and `dist/ovcaq-0.1.0.dev0-py3-none-any.whl`. Linux qualification retains downstream ownership.

Alice separately ran 346 focused workflow/input/saga/report tests in 8.07s. Blake separately passed 365 workflow/packaging cases, with four Unix-socket cases requiring a targeted escalated rerun after sandbox failures. Bob was static-only. These overlapping lens totals are not added to the coordinator's full-suite total.

## Ten source-task assessments

| Task | Acceptance and inspected implementation/test evidence | Result |
|---|---|---|
| P02-T01 | Lowest-sequence WIP before backlog; hold exclusion; missing/invalid directories; deterministic ties; lifecycle/configured paths; selection/configuration and installed-input tests | Covered; no additional behavioral gap found |
| P02-T02 | Frontmatter defaults, validation, explicit overrides, overwrite ownership, abstract tiers, unavailable-tier warning, active PRD and cap-three behavior; parser/application/installed tests | R8-07 input FIFO refusal missing |
| P02-T03 | All six phase/outcome rows and rejection rows, full effects, review resets and convergence markers, CAS compound mutation, terminal drain; transition/application/installed tests | Covered; preserve terminal drain |
| P02-T04 | Resume recovery precedence, paused/build/review/done mapping, retained lifecycle fixtures; tolerant task counting, 15-task ceiling, overrides and plan dependency validation | Covered; no additional behavioral gap found |
| P02-T05 | Exact per-PRD reset owners, batch/capability preservation, completion idempotence and PRD matching; records/application tests | R8-06 blank autonomous count missing |
| P02-T06 | Ledger root/items/attribution, op IDs, exact versus conflicting replay, locking, canonical publication, interruption recovery; deferred-ledger and installed tests | R8-01 strict decoding; R8-03 replaced lock; R8-07 record FIFO |
| P02-T07 | Intent/move/record/reset/commit; explicit kind, all named failpoints; conflicting stall refusal; first park and systemic second park; directory/publication fences and installed recovery tests | R8-02 source/held identity and restart gap blocks exit criterion |
| P02-T08 | Audit/report/metrics, report replacement and duplicate-section collapse, archives, retained metrics and goldens, legacy/mixed totals, equal-key ordering, batch filtering and control/nonregular rejection | R8-01 shared ledger reader; R8-04 omitted details; R8-05 durability; R8-06 blank rows |
| P02-T09 | CLI > project > user > defaults; nested cwd; independent state override; configured PRD/runtime/ledger/report roots; containment and symlink refusal | R8-07 configuration FIFO |
| P02-T10 | Generated operations/state protocol from live parser; command inventory and help contracts | Covered; no second manual command inventory |

Initial implementation attribution: P02-T01–T05 share `06fdf88149a7cafd6d3f4ec9aedf1510a59a652a`; P02-T06–T10 share `5a7ff023059bd396a177da7946a25ffe8d6d176d` (pure paths also in the former). All later repair commits within the full range were reviewed too.

Phase exit assessment: retained lifecycle fixtures match v1 outcomes; dependency/string guards pass; **recoverability without lost work at every durable boundary fails** on R8-02/R8-03. Current covered transitions and installed commands pass, but those passes do not approve PRD completion. R8-08 is a cross-cutting rubric obligation.

## All 55 owned characterization rows

The row set is taken from migration ownership for PRD 00004 and joined to the current-system inventory, not inferred from test filenames. [Exact source summaries, origins, and targets](00004-cycle-08-owned-rows.json) are retained. Every ID occurs once below; coverage means the obligation and current evidence were inspected, not that every scenario passes.

Implementation/test references for each group follow. Unqualified modules are under `src/ovcaq/workflow/`; unqualified test modules are under `tests/workflow/`.

- **Selection (3)**, P02-T01: selection.py, paths.py; test_selection.py, test_configuration.py; packaging/test_workflow_inputs.py.
- **Frontmatter (2)**, P02-T02: frontmatter.py, applications.py; test_frontmatter.py, test_applications.py; packaging/test_installed_cli.py.
- **Policy (3)**, P02-T04: policy.py; test_policy.py, test_applications.py, test_workflow_cli.py.
- **Resume (2)**, P02-T04: resume.py; test_resume.py, test_characterized_fixtures.py.
- **Transitions/reset (3)**, P02-T03/T05: transitions.py; test_transitions.py, test_records.py, test_applications.py.
- **Records (28)**, P02-T05/T06/T07/T09: records.py, _files.py; test_records.py, test_deferred_ledger.py, test_sagas.py, test_saga_identity.py, test_saga_publication.py, test_boundaries.py; packaging/test_installed_sagas.py, test_workflow_inputs.py.
- **Reports (13)**, P02-T08: reports.py; test_reports.py; packaging/test_installed_reports.py; retained metrics and v1 report goldens.
- **Docs (1)**, P02-T10: workflow/cli.py, cli.py; test_workflow_cli.py, state/test_cli.py; docs/operations.md, docs/state-protocol.md.

| Owned row | Source obligation | Evidence group | Assessment |
|---|---|---|---|
| ART-012 | reports batch state final | Reports | Gap: R8-05 |
| ART-013 | reports batch report | Reports | Gap: R8-01, R8-04, R8-05 |
| ART-014 | per-PRD audit report | Reports | Gap: R8-05 |
| ART-016 | deferred batch ledger | Records | Gap: R8-01, R8-03 |
| ART-017 | deferred batch ledger lock | Records | Gap: R8-03 |
| ART-026 | park-requested file | Records | Gap: R8-02 |
| ART-036 | PRD lifecycle directories | Selection | Inspected; no additional behavioral gap found |
| ART-039 | CLI golden state and metrics inputs | Reports | Gap: R8-04, R8-05, R8-06 |
| ART-040 | CLI archived batch golden | Reports | Gap: R8-05 |
| ART-041 | CLI golden expected outputs | Reports | Gap: R8-04, R8-05, R8-06 |
| CMD-007 | autopilot stall | Records | Gap: R8-02 |
| CMD-008 | autopilot park | Records | Gap: R8-02 |
| CMD-009 | autopilot reset-prd | Transitions/reset | Inspected; no additional behavioral gap found |
| CMD-010 | autopilot defer | Records | Gap: R8-01, R8-03 |
| CMD-012 | autopilot check-plan | Policy | Inspected; no additional behavioral gap found |
| CMD-013 | autopilot select | Selection | Inspected; no additional behavioral gap found |
| CMD-014 | autopilot frontmatter | Frontmatter | Gap: R8-07 |
| CMD-015 | autopilot phase-done | Transitions/reset | Inspected; no additional behavioral gap found |
| CMD-016 | autopilot resume-target | Resume | Inspected; no additional behavioral gap found |
| CMD-018 | autopilot render audit | Reports | Gap: R8-05 |
| CMD-019 | autopilot render report | Reports | Gap: R8-01, R8-04, R8-05 |
| CMD-020 | autopilot render metrics | Reports | Inspected; no additional behavioral gap found |
| CMD-036 | statectl complete-prd | Records | Gap: R8-06 |
| DEC-071 | oversized plan policy | Policy | Inspected; no additional behavioral gap found |
| DEC-076 | stall saga preflight refusal | Records | Inspected; no additional behavioral gap found |
| DEC-077 | stall saga recoverable failure | Records | Gap: R8-02 |
| DEC-078 | stall saga successful commit | Records | Gap: R8-02 |
| DEC-079 | park absent marker decision | Records | Covered by accepted v1 intent/hook redesign |
| DEC-080 | park malformed or stale marker ignored | Records | Covered by accepted v1 intent/hook redesign |
| DEC-081 | park continues batch | Records | Inspected; no additional behavioral gap found |
| DEC-082 | park systemic batch halt | Records | Inspected; no additional behavioral gap found |
| ENV-025 | _AUTOPILOT_CLI_FAILPOINT | Records | Covered by accepted v1 intent/hook redesign |
| STATE-112 | deferred ledger root | Records | Gap: R8-01, R8-03 |
| STATE-113 | deferred ledger items[] | Records | Gap: R8-01, R8-03 |
| STATE-121 | park-requested marker | Records | Gap: R8-02 |
| TEST-001 | cli/test_cli.py | Records | Gap: R8-02 |
| TEST-002 | cli/test_cli_default_paths.py | Records | Gap: R8-07 (configuration input) |
| TEST-005 | cli/test_doc_contract.py | Docs | Inspected; no additional behavioral gap found |
| TEST-006 | cli/test_frontmatter.py | Frontmatter | Gap: R8-07 |
| TEST-008 | cli/test_lifecycle_cli.py | Records | Inspected; no additional behavioral gap found |
| TEST-012 | cli/test_policy.py | Policy | Inspected; no additional behavioral gap found |
| TEST-013 | cli/test_records.py | Records | Inspected; no additional behavioral gap found |
| TEST-014 | cli/test_records_failure_paths.py | Records | Gap: R8-01, R8-03 |
| TEST-015 | cli/test_records_import_hygiene.py | Records | Inspected; no additional behavioral gap found |
| TEST-016 | cli/test_records_park.py | Records | Gap: R8-02 |
| TEST-017 | cli/test_records_stall.py | Records | Gap: R8-02 |
| TEST-018 | cli/test_render.py | Reports | Gap: R8-04, R8-05, R8-06 |
| TEST-019 | cli/test_render_autonomous_blank_rows.py | Reports | Gap: R8-06 |
| TEST-020 | cli/test_render_replace_section.py | Reports | Inspected; no additional behavioral gap found |
| TEST-021 | cli/test_resume.py | Resume | Inspected; no additional behavioral gap found |
| TEST-027 | cli/test_selection.py | Selection | Inspected; no additional behavioral gap found |
| TEST-029 | cli/test_transitions.py | Transitions/reset | Inspected; no additional behavioral gap found |
| TEST-038 | scripts/test_autopilot_phase2_stall.py | Records | Gap: R8-02 |
| TEST-052 | scripts/test_statectl_complete_prd.py | Records | Gap: R8-06 |
| TEST-062 | cli/test_render_batch_summary_nonzero_binding.py | Reports | Inspected; no additional behavioral gap found |

Accepted extraction adaptations remain settled: typed durable recovery intent and explicit operation kind replace launcher-specific marker handoff, named injectable boundary hooks replace the legacy test environment selector, and fixtures are adapted into the v1 schema. No legacy state importer, persistent old-command alias, launcher marker implementation, provider configuration policy, or Linux signoff is requested here.

Retained sanitized fixtures inspected and exercised: `tests/fixtures/claude/legacy-state-build.json`, `legacy-state-review.json`, `legacy-state-converged.json` through `test_characterized_fixtures.py`; `legacy-metrics.jsonl` through report tests; `tests/fixtures/workflow/reports/deferred.json` and expected `audit.md`, `metrics.md`, `report.md` through the migrated-golden test. The full suite also exercised characterization ownership checks. No tests read live launcher data.

Preservation checks include terminal drain, conflicting stall refusal, legacy/mixed unknown totals, equal-key metric ordering, active-batch filtering, explicit recovery kind, public state mutation fences, lifecycle/ledger path identity, control-character rejection, provider neutrality, and parser-generated documentation. New probes identify the remaining identity/durability gaps rather than waiving those invariants.

## Reproductions and limits

Run from the reviewed checkout:

```text
mise exec -- uv run python dev/local/reviews/00004-cycle-08-probes.py
```

[Executable probe](00004-cycle-08-probes.py) · [Observed JSON](00004-cycle-08-probes.json). The file records 17 observations from isolated temporary roots. Durable fixture state is initialized through StateStore. Boundary hooks and scoped mocks only affect the disposable scenario. CLI probes use the checkout's module with isolated XDG configuration; installed-wheel behavior is separately covered by the required suite and Blake.

| Finding | Probe cases | Observed evidence |
|---|---|---|
| R8-01 | deferred-duplicate-key; deferred-deep-json; deep-ledger-json-cli | Duplicate accepted, bytes changed, retained record absent. Deep input raises RecursionError. JSON report CLI exits 1 with traceback while preserving state and ledger. Blake additionally reproduces defer CLI. |
| R8-02 | stall/park × source-before-rename, held-after-rename, held-across-restart | Six successful final calls; held content is the replacement; original retained elsewhere by fixture; tasks zero; recovery null; ledger exists. Restart variant interrupts at recorded stage before replacing held path. |
| R8-03 | ledger-lock-replaced-before-publish | Second append reports success; final operation IDs contain only first. The hook forces a deterministic interleaving while the original lock FD remains held. |
| R8-04 | report-non-active-deferred-prd | Deferred count present; earlier PRD, detail and operation ID all absent from first report. |
| R8-05 | report-created-parent-durability; report-retry-after-directory-fsync-failure | Runtime parent unsynced; reports directory synced. Retry after injected directory-fsync failure returns success with zero directory syncs. This is syscall evidence, not a power-loss experiment. |
| R8-06 | schema-valid-blank-decision | Schema validates; autonomous_decisions is 1; blank audit row present. |
| R8-07 | fifo-frontmatter; fifo-defer; fifo-config | All exceed two seconds with no writer; child processes killed/reaped; state preserved. |

R8-08 is mechanical, not a behavioral reproduction. [AST measurements](00004-cycle-08-size-measurements.json) list overlength functions in changed files, including inherited examples that need scope adjudication. New workflow CLI tests measure 138 and 132 lines; new saga examples measure 93 and 117. `test_service_commands.py` is 962 lines versus 851 at base. R8-K2's production `add_task` is 53 lines at both base and HEAD; broad state-service restructuring is excluded.

Repair regressions should fail on these demonstrated outcomes and assert preservation/recovery, not merely substitute a generic exception assertion. The report provides bounded acceptance targets for each root; no implementation repairs were made in this session.

## Mechanical checks and fail-first replay

The installed `compute_mech_facts.py` ran over all changed Python files and its complete output is retained in [review context](../tmp/review-context-00004-cycle-08.md). `detect_tautological_tests.py` scanned 230 functions across 26 test files and flagged the OR assertion at `tests/state/test_cli.py:372`. That mandatory mechanical finding is absorbed as R8-K1 with Alice/Bob, then classified inherited using the exact base diff; it is not silently dropped.

The installed replay helper initially returned no usable test results: the overlay omitted `packaging_support`, causing runner exit 4 and a skipped replay block. That original output remains in context. The coordinator supplied [a complete test-overlay replay](00004-cycle-08-replay.py), including changed tests, split helpers, conftests, and retained fixtures in a temporary detached worktree at the implementation base. Base production code was preserved.

Command:

```text
mise exec -- uv run python dev/local/reviews/00004-cycle-08-replay.py
```

[Full base-run output and touched-case results](00004-cycle-08-replay-result.json):

- Base runner exit 1: **60 failed, 785 passed, 3 collection errors in 13.67s**. These are expected differences against the pre-workflow implementation, not failures at reviewed HEAD.
- Changed/touched parametrized cases: **54 failed, 0 passed, 0 skipped**. No passing-on-base mechanical finding was produced.
- Remaining collection barriers: `tests/state/test_cli_limits.py` cannot import new `ovcaq.cli_io`; `tests/state/test_service_commands.py` cannot import new `StateMutationConflictError`; `tests/workflow` cannot import new `ovcaq.workflow.paths`.
- The result's `uncollectable` parser field lists the first two file paths; the third directory-level error is retained in the raw output and included in the total.
- The 785 unchanged/base-compatible passes do not establish new-feature behavior binding. Module absence prevents certifying fail-first behavior for every new test. Bob V2's missing-helper issue was addressed, and this residual limitation is explicit.
- The replay was repeated only to persist full output after tool truncation. Temporary worktrees were removed in cleanup; final worktree listing contains only the original master checkout.

## Lens procedures and completeness

All required reviewers returned usable reports with complete rubric lines: Alice 12 consensus rules, Blake 19 blind rules, Bob 12 consensus plus five doubt rules. Consensus IDs are R1,R2,R3,R4,R6–R13 (the installed set has no R5). Blind IDs are B1–B19. Doubt IDs are D1–D5, the installed names for the user's five doubt obligations. Bob received de-slop and FIX/VERIFY/KNOWN requirements in addition to both numbered sets. Per-rule pass/fail values are retained unchanged in the main review and raw outputs; a D-series pass means the review met that rule, not that implementation findings vanished.

Isolation: fresh native subagents, no inherited conversation, no cross-reviewer messages, no raw report written until all reviewers finished. Blake got only PRD, blind rubric/persona, source-contract access and read-only controls; no repair/diff narrative. Bob got PRD/diff/mechanical source context but no repair handoff/design narrative. Only Alice/coordinator had rework-07.md access.

The [dispatch log](00004-cycle-08-dispatch.md) retains exact external Bob/Carl invocations and refusal results. Both external wrappers refused nested CLI dispatch. Bob used the permitted native fallback; Carl remained unavailable after one retry. No optional lane output is fabricated. Native host adaptation supplies isolated lenses but no model diversity. No external thread ID or consensus-engine run ID was produced. User restrictions supersede the ordinary prior-ledger, capsule, retrieval-pack, task-write, and autopilot contract-card locations.

## Retained cycle artifacts

| Artifact | Purpose |
|---|---|
| ../tmp/review-tasks-00004-cycle-08.md | Ten separate accepted source tasks and initial commit attribution |
| ../tmp/review-prd-00004-cycle-08.md | PRD review input |
| ../tmp/review-context-00004-cycle-08.md | Full-range context, mechanical facts and original replay limitation |
| ../tmp/review-diff-00004-cycle-08.diff | Complete reviewed implementation diff |
| ../tmp/alice-prompt-00004-cycle-08.md; ../tmp/alice-output-00004-cycle-08.txt | Exact Alice prompt and unmodified result |
| ../tmp/blake-prompt-00004-cycle-08.md; ../tmp/blake-output-00004-cycle-08.txt | Exact blind prompt and unmodified result |
| ../tmp/bob-prompt-00004-cycle-08.md; ../tmp/bob-output-00004-cycle-08.txt | Exact Bob fallback prompt and unmodified result |
| ../tmp/carl-prompt-00004-cycle-08.md | Optional unavailable lane input; no output claimed |
| 00004-cycle-08-dispatch.md | Host adaptation, exact wrapper refusal/retry evidence |
| 00004-cycle-08-consolidated-raw.md | Successful script's 14 pre-adjudication rows |
| 00004-cycle-08-owned-rows.json | Exact 55 source inventory rows and migration target paths |
| 00004-cycle-08-size-measurements.json | AST size evidence |
| 00004-cycle-08-probes.py; 00004-cycle-08-probes.json | Reusable coordinator reproductions and 17 observed results |
| 00004-cycle-08-replay.py; 00004-cycle-08-replay-result.json | Supplemented base replay and complete raw output |
| 00004-cycle-08-contract-card.md | Standalone transition contract, no task-store attachment |
| 00004-workflow-core-v1-fast-review-08.md | Consolidated verdict, root findings, disagreements and lens verdicts |
| 00004-workflow-core-v1-fast-review-08-evidence.md | This evidence record |

The [71-line repair handoff](../tmp/00004-handoff-20260905-1250.md) is retained. The installed review-file shape gate passed with --require-codex-guard. A separate artifact audit passed: three complete raw rubric sets, ten source-task rows, 55 unique owned IDs matching the inventory, 17 reproduction observations, valid Markdown links, all handoff sections, exact HEAD, empty status/stash list and only the original worktree. Its first invocation was denied uv-cache access by the sandbox; the required escalated rerun passed. No automatic approval rejection occurred.

Final handoff: 2026-09-05 12:50 CEST. Temporary fixtures and replay worktrees were cleaned, required local evidence retained. Existing review histories and other sessions' artifacts were untouched. No repairs or PRD closeout occurred; the reviewed HEAD remains 8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7.
