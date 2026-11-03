# FT-04R10 evidence — PRD 00004

Fresh review on 2026-09-05, Europe/Prague. Verified before changes: master at
`72562f6fd12fb039e91e4c7b1be29758d1901ec8`, clean Git status, expected commit title and timestamp
`2026-09-05T22:20:36+02:00`. Full implementation range:
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..72562f6fd12fb039e91e4c7b1be29758d1901ec8` — 11 commits, 72 files, +9674/-348.
The latest repair commit was not substituted for the full implementation scope.

Read repository/global AGENTS.md, WIP PRD, accepted implementation plan (read
only), coverage manifest, discovery 00001, both characterization TOMLs, R9
verdict/evidence and bounded decisions, rework08/probes/sizes, rework09 contract,
regressions and verification/probe evidence. Both TOMLs were parsed in full and
joined freshly; all 55 owned rows retain source, evidence, disposition and
target in [the source join](00004-cycle-10-owned-rows.json). All ten task texts and source
phase exits remain verbatim in [task context](../tmp/review-tasks-00004-cycle-10.md).

Plan SHA-256: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
Inventory SHA-256: `d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9`.
Both match the accepted manifest and repair handoff. P02-T01–T05 share initial
commit `06fdf88149a7cafd6d3f4ec9aedf1510a59a652a`; T06–T10 share
`5a7ff023059bd396a177da7946a25ffe8d6d176d`. All repairs remain in the full range.

## Fresh verification

[Exact command results](00004-cycle-10-verification.json). All executions used
mise-managed uv on Darwin, Python 3.13.13, pytest 9.1.1.

| Command | Observed result |
|---|---|
| `mise exec -- uv sync --all-groups` | Exit 0; 25 resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/ tests/packaging/ -q` | 450 passed in 11.21s |
| `mise exec -- uv run pytest` | 1338 passed in 22.44s; zero failures/skips |
| `mise exec -- uv run ruff check .` | All checks passed |
| `mise exec -- uv run ruff format --check .` | 116 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | No issues in 51 source files |
| `mise exec -- uv build` | sdist and wheel built |
| `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..HEAD` | Exit 0 |

Alice independently ran 67 focused tests in 0.27s and four TOML probes, plus a
maximum-size 512-task dependency chain. Counts overlap and are not added to the
full suite. Bob's static VERIFY is resolved by the fresh coordinator record;
no redundant full-suite run or task is needed. A later read-only probe-summary
command hit uv's cache sandbox restriction and passed through the required
escalation retry. The initial shell fact-forcing gate was satisfied before
preflight ran. No implementation check was waived.

## R9 and R8 preservation

| Repair | Fresh evidence and disposition |
|---|---|
| R9-01 | Repaired. Opened-directory inode lock excludes competing reads and native replacement. Serialized original-snapshot comparison catches restored-sidecar stale writes. New nested/process tests and six unchanged R8 named-boundary nested/process tests pass. The coordinator-only root remains explicit despite zero R9 lens votes. |
| R9-02 | Repaired. Root-to-leaf identities survive traversal, replacement, identical replay and context exit. All 16 report/audit/archive component tests pass; displaced payload and state bytes survive, valid retries/rerenders match. |
| R9-03 | Repaired. RecursionError maps to contextual ConfigurationError/usage. Four installed recognized/ignored project/user TOML cases pass in the full suite and fresh independent wheel probe. |
| R9-04 | Repaired. Shared `_section_span` removes the duplicated heading scan while retaining duplicate collapse, missing-section refusal, exact heading boundaries and unrelated content. |
| R9-05 | Repaired. `_run` delegates to `_run_unchecked`; conversion/cwd/env/capture/text/60-second timeout and diagnostic assertion retained. Both complete suites and installed origins pass. |

Retained R8 guarantees: strict duplicate/deep JSON decoding and byte preservation;
original PRD device/inode identity at intent/move/recorded restart/publication;
sidecar ownership and lifecycle/ledger fences; earlier boundary competitor
survival; complete cross-PRD deferred details; creation, replacement and replay
directory fsyncs; substantive decision filtering with numeric/string zero;
nonregular/FIFO input refusal; test assertions preserved after splits. Terminal
drain, conflicting-stall refusal, nonzero/unknown totals, equal-key metric
ordering, active-batch scope, explicit recovery kind, control-character refusal,
provider neutrality and parser-derived docs remain covered by the full suite.
No R8 named test was edited in the R9 repair or this review.

## Independent coordinator probes

All original cycle09 scripts were read and rerun unchanged. Fresh stdout/stderr
and exits are retained separately from the old results:

- [Original 19-observation harness](00004-cycle-10-original-probes.json): exit 0.
  BEFORE_PUBLISH rival succeeds and survives (`second`, then `second, first`
  after retry). Native-interval rival is refused; the old callback propagates
  refusal and prevents the first native replacement, then retries `first`.
- [Original publication harness](00004-cycle-10-original-publication-probes.json): exit 0;
  report/audit/archive all refuse displaced directory identities and retain
  their payloads.
- [Original adjudication harness](00004-cycle-10-original-adjudication-probes.json):
  **exit 1**, retained in full. Its `assert rival.returncode == 0` is obsolete
  because the bare child-library call raises expected contention. This harness
  is not reported as passing and its traceback is not an unhandled CLI error.
- [Unchanged remaining adjudication functions](00004-cycle-10-adjudication-supplement.json)
  complete successfully. Frontmatter derived-state ownership and initially
  absent-source/null-artifact refusal remain as settled.

[Probe orchestrator](00004-cycle-10-probes.py) adds an independent installed-wheel rival
at the native replacement syscall. [Exact result](00004-cycle-10-installed-lock.json):
the rival returns exit **2**, `state_io` JSON, contextual `deferred publication
busy; retry`, empty stdout and no traceback. The original native replacement
continues, then its displaced sidecar causes the required identity refusal.
Retries produce `seed, first, second` exactly once, preserve authoritative state
and make further replay byte-identical. Module origins are in the temporary
installation's site-packages. This supplements the new real-process library
regression and keeps resource/contention refusals distinct from unhandled errors.

[Installed TOML results](00004-cycle-10-installed-config.json): all four project/user ×
recognized/ignored cases return usage JSON/exit 1 with source path, empty stdout,
no traceback and unchanged config/state. Temporary installations, probe roots
and children were context-managed/reaped.

## R10-01 — report JSON text disagrees with published artifact

**Medium, FIX, P02-T08 / CMD-019 / TEST-018**, with integration through P02-T09's
shared machine output contract. Bob identified the issue statically before the
coordinator confirmed it in a clean wheel install outside the checkout.

`workflow_cli.py:161` computes fresh `render_report(state, ...)` for JSON `text`,
then `publish_report` computes a different `_updated_report(existing, ...)` that
retains earlier PRD sections and unrelated content. Render A, change active PRD
to B through StateStore, render B: JSON `text` contains B only, while the returned
`path` contains A+B. Both commands succeed; exact rerender repeats the mismatch.
Authoritative state and the complete on-disk report remain intact. This is an
incomplete machine-readable representation, not loss of ledger/state data.

[Executable installed probe](00004-cycle-10-report-probe.py) /
[full compared texts, origins and observations](00004-cycle-10-report-probe.json).
First publication has `text == file`; the second has false equality, A absent
from JSON and present in the file, B present in both. The probe's exit 0 means
it observed the discrepancy successfully, not that the product contract passed.

The accepted report is a batch artifact with replaceable per-PRD sections
(ART-013/CMD-019). JSON `text` and `path` are presented as the same render result;
the installed completed-summary test already asserts their equality for first
publication (`tests/packaging/test_installed_reports.py:164`). No distinct
partial-text contract is documented. Returning different content on update
breaks that established contract for machine consumers. This gap is in the full
implementation range, independent of the correctly repaired R9 path identity.

Bounded repair: compose/publish once and return the exact composed text from
that verified operation. Avoid a separate unverified pathname reread. Add
installed A→B→A and exact replay coverage; `text` must equal the actual published
artifact, retain prior and unrelated sections, collapse duplicates, and leave
state bytes unchanged. Preserve report/audit/archive identity/fsync guards,
configured-path retry, all golden projections and the ledger serialization root.
Do not add a second renderer or redesign public workflow ownership.

## Ten source-task assessments

| Task | Current evidence | Assessment |
|---|---|---|
| P02-T01 | selection/paths/configuration + installed input tests | Covered: total ordering, WIP/backlog/hold rules and configured lifecycle paths. |
| P02-T02 | frontmatter/applications + installed inputs | Covered within settled returned-control/downstream ownership; caps/tiers/CAS/warnings preserved. |
| P02-T03 | transitions/applications/records + installed lifecycle | Covered: all six effect rows, rejection rows, atomic handoff and terminal drain. |
| P02-T04 | resume/policy/characterized fixtures + installed CLI | Covered: recovery/pause/phase/task precedence, shape/ceiling/override; no runtime policy added. |
| P02-T05 | records/applications/blank decisions + service contracts | Covered: exact reset owners, batch preservation, deterministic completion, conflicting replay, zero/blank filtering. |
| P02-T06 | deferred ledger/integrity/publication + installed lock probe | Covered: attribution, op IDs, exact/conflicting replay, strict reads and repaired kernel serialization. |
| P02-T07 | sagas/artifacts/identity/publication/boundaries + installed sagas | Covered: typed intent, every durable boundary, original identities and fail-closed reset/commit; absent-source stance retained. |
| P02-T08 | reports/recovery/identity/blank decisions + installed reports | R9 repairs pass; R10-01 blocks machine output consistency on report updates. Other deterministic projections preserved. |
| P02-T09 | configuration/paths/installed inputs/TOML/FIFO tests | Configuration and malformed-input obligations covered; R10-01 is separately attached to report CLI integration. |
| P02-T10 | live registry/parser, documentation contract tests | Covered: operations/state-protocol inventories generated from parser; no duplicate handwritten verbs. |

Source Phase 2 exits: lifecycle fixtures match v1 outcomes; park/stall interruption
recovers or safely refuses at every durable boundary under the accepted original
identity stance; workflow imports no runtime/driver/TUI/launcher module.
PRD Phase A passes; Phase B passes under the settled absent-source constraint.
Phase C remains **blocked by R10-01** despite passing retained tests because its
installed report result is incomplete after an update. Completion is not approved.

## All 55 owned rows

Each row below joins directly to its unchanged accepted source summary and
target. Groups identify passing current implementation/tests; cross-cutting
blockers remain attached to the task/phase, even when a row's projection passes.
“Covered” is evidence within the accepted contract, not exhaustive adversarial
proof or universal implementation-base binding.

| Owned ID | Accepted source obligation | Evidence group | Current assessment |
|---|---|---|---|
| ART-012 | Drained state archived as reports/{batch}-state-final.json before post-drain actions. | Reports | Covered; preserve characterized behavior |
| ART-013 | Durable batch Markdown report with replaceable per-PRD sections, stalled records, and final summary. | Reports | On-disk artifact covered; machine representation gap R10-01 |
| ART-014 | Durable review-directory Markdown projection of autonomous, deferred, and doubt decision arrays. | Reports | Covered; preserve characterized behavior |
| ART-016 | deferred/{batch}-deferred.json append ledger used for stalls and decisions carried to batch end. | Records | Covered, including repaired coordinator lock root and exact retry |
| ART-017 | Independent sidecar advisory lock serializing deferred-ledger updates. | Records | Covered, including repaired coordinator lock root and exact retry |
| ART-026 | Verified JSON handoff from supervisor death/stall decision to the next workflow session. | Records | Covered; preserve characterized behavior |
| ART-036 | backlog, wip, hold, and done files provide selection and verified-move lifecycle evidence. | Selection | Covered; preserve characterized behavior |
| ART-039 | Current sanitized rendering inputs, including legacy and rich nested state shapes. | Reports | Covered; preserve characterized behavior |
| ART-040 | Current archived batch-state contract with completed-PRD and decision history. | Reports | Covered; preserve characterized behavior |
| ART-041 | Expected audit, metrics, report-section, report-summary, and status rendering contracts. | Reports | Covered; preserve characterized behavior |
| CMD-007 | Runs the durable stall saga for a PRD, including hold move, defer record, and reset. | Records | Covered; preserve characterized behavior |
| CMD-008 | Consumes or reconciles a park request and applies the systemic-park breaker. | Records | Covered; preserve characterized behavior |
| CMD-009 | Atomically clears per-PRD state and restores build counters and phase markers. | Transitions | Covered; preserve characterized behavior |
| CMD-010 | Appends one JSON object to a batch deferred ledger with PRD attribution. | Records | Covered, including repaired coordinator lock root and exact retry |
| CMD-012 | Reads the task snapshot and returns a distinct failure when its count exceeds the loop ceiling. | Policy | Covered; preserve characterized behavior |
| CMD-013 | Selects deterministically from wip then backlog while excluding hold, returning JSON even when drained. | Selection | Covered; preserve characterized behavior |
| CMD-014 | Parses PRD controls, warns on defaults, and transactionally applies the derived state fields. | Frontmatter | Covered within settled returned-control ownership |
| CMD-015 | Applies one named workflow outcome from the current phase as an atomic transition. | Transitions | Covered; preserve characterized behavior |
| CMD-016 | Returns the authoritative resume target after schema-version preflight. | Resume | Covered; preserve characterized behavior |
| CMD-018 | Renders the per-PRD decision audit from state arrays into the repository review directory. | Reports | Covered; preserve characterized behavior |
| CMD-019 | Creates or updates batch report PRD, stalled, or summary sections from state and metrics. | Reports | R10-01: updated report JSON text differs from published batch artifact |
| CMD-020 | Prints a deterministic Markdown summary of loop metrics rows. | Reports | Covered; preserve characterized behavior |
| CMD-036 | Appends a computed completed-PRD batch summary and resets consecutive parks. | Records | Covered; preserve characterized behavior |
| DEC-071 | A real task list longer than the ceiling is over-limit; missing or non-list tasks count as zero. | Policy | Covered; preserve characterized behavior |
| DEC-076 | Malformed or conflicting stall intent, mismatched PRD, or missing batch identity refuses before filesystem effects. | Records | Covered; preserve characterized behavior |
| DEC-077 | Hold creation/move, deferred append, or state transaction failure returns its distinct code while durable intent preserves retryability. | Records | Covered; preserve characterized behavior |
| DEC-078 | Verified move plus deduplicated defer record commits PRD reset, park-breaker rule, and intent deletion atomically. | Records | Covered; preserve characterized behavior |
| DEC-079 | No marker returns no-work unless a pending stall intent exists, which is reconciled first. | Records | Covered; preserve characterized behavior |
| DEC-080 | Malformed marker or PRD no longer in wip is deleted and returns ignored without moving another PRD. | Records | Covered; preserve characterized behavior |
| DEC-081 | The first consecutive wrapper-death park moves and resets the PRD, increments the breaker, and continues. | Records | Covered; preserve characterized behavior |
| DEC-082 | The second consecutive wrapper-death park also writes paused/systemic_park state and returns the halt code. | Records | Covered; preserve characterized behavior |
| ENV-025 | Test-only durable-saga interruption selector for named stall/park boundaries. | Records | Covered; preserve characterized behavior |
| STATE-112 | Per-batch durable deferred object containing batch_id and ordered items. | Records | Covered, including repaired coordinator lock root and exact retry |
| STATE-113 | Caller record copied with prd attribution; op_id deduplicates retrying stall appends. | Records | Covered, including repaired coordinator lock root and exact retry |
| STATE-121 | JSON handoff carrying prd and reason for the next session's durable park saga. | Records | Covered; preserve characterized behavior |
| TEST-001 | Characterizes subprocess dispatch, stall and park outcomes, reset and restore behavior, deferred records, diagnostics, and exit codes. | Records | Covered; preserve characterized behavior |
| TEST-002 | Characterizes walk-up default path resolution and explicit state or PRD-directory override precedence for stall and park. | Records | Covered; preserve characterized behavior |
| TEST-005 | Pins documentation coverage for every registered CLI subcommand. | Docs | Covered; preserve characterized behavior |
| TEST-006 | Characterizes PRD frontmatter parsing, defaults, enum and integer validation, malformed blocks, optional flags, and warnings. | Frontmatter | Covered within settled returned-control ownership |
| TEST-008 | Characterizes selection, phase transitions, resume targets, convergence, rework, drain, frontmatter application, walk-up paths, and future-state refusal. | Records | Covered; preserve characterized behavior |
| TEST-012 | Characterizes the fifteen-task plan ceiling, override semantics, tolerant task counting, no mutation, CLI exposure, and missing-state failure. | Policy | Covered; preserve characterized behavior |
| TEST-013 | Characterizes deferred-log append and deduplication plus the authoritative per-PRD reset field set and preservation rules. | Records | Covered, including repaired coordinator lock root and exact retry |
| TEST-014 | Characterizes record, stall, and park boundary failures, corrupt shapes, invalid identifiers, filesystem errors, idempotent retry, and no-effect guarantees. | Records | Covered, including repaired coordinator lock root and exact retry |
| TEST-015 | Pins that importing records through the CLI does not leak the scripts directory into the interpreter search path. | Records | Covered; preserve characterized behavior |
| TEST-016 | Characterizes park-marker reconciliation, crash recovery, conflicting stall intents, atomic reset and counter updates, and systemic second-park halt. | Records | Covered; preserve characterized behavior |
| TEST-017 | Characterizes durable stall intent, verified PRD moves, deferred append, reset composition, crash-point retries, conflicts, and site-specific park-counter handling. | Records | Covered; preserve characterized behavior |
| TEST-018 | Characterizes status, audit, metrics, and report rendering against goldens, tolerant missing data, batch scoping, decision tables, flags, and rerender effects. | Reports | R10-01: updated report JSON text differs from published batch artifact |
| TEST-019 | Pins omission of wholly blank autonomous-decision rows while retaining zero and any populated renderable cell. | Reports | Covered; preserve characterized behavior |
| TEST-020 | Characterizes exact Markdown section replacement, duplicate collapse, heading boundaries, unrelated-section preservation, and report idempotence. | Reports | Covered; preserve characterized behavior |
| TEST-021 | Characterizes resume-target priority across stall intent, park marker, pause and stall state, phase routing, legacy phases, and systemic park halt without mutation. | Resume | Covered; preserve characterized behavior |
| TEST-027 | Characterizes five-digit PRD sequence parsing, deterministic ordering, Markdown filtering, work-in-progress priority, backlog fallback, drain, and hold exclusion. | Selection | Covered; preserve characterized behavior |
| TEST-029 | Characterizes the pure transition table for phase advancement, rework, convergence, per-PRD reset, drain, marker idempotence, and unknown input refusal. | Transitions | Covered; preserve characterized behavior |
| TEST-038 | Pins phase-two stall effects: PRD moves to hold, stall clearing, per-PRD reset, batch preservation, hold creation, and sequence retention. | Records | Covered; preserve characterized behavior |
| TEST-052 | Characterizes atomic completed-PRD record creation, task and cycle defaults, escalated and autonomous decision counts, blank-row filtering, PRD matching, reset, and sibling preservation. | Records | Covered; preserve characterized behavior |
| TEST-062 | Characterizes batch-summary binding of completed-PRD counts and cycle and decision totals: nonzero retained values, legitimate empty zeros, and unknown sums for legacy or mixed records. | Reports | Covered; preserve characterized behavior |

Evidence groups (test filenames are under tests/workflow unless qualified):

- Selection: selection.py/paths.py; test_selection.py, test_configuration.py,
  packaging/test_workflow_inputs.py.
- Frontmatter: frontmatter.py/workflow_cli.py; test_frontmatter.py,
  test_applications.py, packaging/test_installed_cli.py/test_input_integrity.py.
- Policy/Resume: policy.py/resume.py; test_policy.py, test_resume.py,
  test_characterized_fixtures.py, test_workflow_cli.py and installed inputs.
- Transitions: transitions.py; test_transitions.py, test_records.py,
  test_applications.py and installed lifecycle/saga cases.
- Records: records.py/_files.py/_rename.py; test_records.py,
  test_deferred_ledger.py, test_ledger_integrity.py, test_ledger_publication.py,
  test_sagas.py, test_saga_artifacts.py, test_saga_identity.py,
  test_saga_publication.py, test_boundaries.py, test_blank_decisions.py;
  packaging/test_installed_sagas.py/test_input_integrity.py and
  state/test_recovery_mutations.py/test_service_contracts.py.
- Reports: reports.py and shared decision filter; test_reports.py,
  test_report_recovery.py, test_report_identity.py, test_blank_decisions.py,
  packaging/test_installed_reports.py and retained sanitized goldens.
- Docs: cli.py/workflow_cli.py; test_workflow_cli.py, state/test_cli.py,
  generated operations.md/state-protocol.md inventories.

Accepted adaptations remain: typed recovery kind replaces launcher markers;
injectable named failpoints replace test environment selectors; sanitized
fixtures use v1 state. No importer, alias, provider/model policy or Linux signoff.

## Adjudication and methodological limits

Blake's null-artifact observation is reproducible and retained verbatim. It is
the explicitly settled refusal from rework08/review09: an initially absent
source keeps failure evidence, and an unidentified later file must not be
adopted. It does not authorize a repair to delete intent, invent identity or add
abort/rollback API. The source task's safe-retry requirement is interpreted with
that explicit user decision. No new evidence invalidates its rationale. Blake
received no repair history, as required by the blind lens.

Alice's no-new-issue assessment does not refute Bob's report result mismatch;
the installed observation and existing equality assertion establish R10-01.
The R9 ledger root was independently checked rather than dropped by consensus.

Mechanical AST and test-shape helpers ran over the full changed-file list in
[implementation context](../tmp/review-context-00004-cycle-10.md). The single MECH OR
assertion is absorbed in inherited R8-K1 with `mech-check` attribution; other
assertions in that test can fail, so the detector's generic preamble is broader
than the localized finding. Fresh [size measurements](00004-cycle-10-sizes.json) retain
add_task 53, schema.py 933, and unchanged packaging function sizes 51/79/66.
The 800/50-line exceptions are inherited; no broad restructuring is requested.

The mandatory full implementation-base replay remains **skipped**, missing
packaging_support at collection. Its known broken invocation was not retried.
The bounded R8 repair-base supplement remains 56 collected, 46 failed and ten
valid preservation passes. Its installed tests were originally post-repair;
retrospective replay is not chronological TDD. The 23 R9 fail-first cases do not
establish universal full-range binding. These are KNOWN, not newly failed tests.

Raw consolidation has nine rows because schema.py versus schema.py:1 were not
merged, packaging size was listed separately, and VERIFY/Blake's scoped objection
remain raw. Coordinator merges schema location, folds unchanged packaging sizes
into R8-K2's existing inherited size limitation (also named by Alice), resolves
VERIFY and adjudicates the settled objection. Nothing is silently discarded.
Terminal accounting: **5 = 1 FIX + 0 VERIFY + 4 KNOWN**. Bob's raw accounting
remains 7 = 1 FIX + 1 VERIFY + 5 KNOWN, with every D1–D5 verdict retained.
Settled Low severities for inherited K2/K3 remain unchanged despite Bob's raw
Medium rubric observations. No new severity or repair scope is inferred.

All lenses carried full installed rubrics: Alice consensus R1–R4/R6–R13; Blake
B1–B19; Bob consensus plus both doubt/de-slop lenses and D1–D5 (the installed
names for requested doubt R1–R5). There is no consensus R5 in this version.
[Dispatch provenance](00004-cycle-10-dispatch.json) records visibility and host adapters.
All returned before raw outputs were saved. Native contexts provide prompt
isolation, not model diversity. External Bob/Carl guards were not retried or
bypassed. Standalone mode did not attach an unrelated state/attempt ledger,
fabricate tasks, write a verification queue or persist doubt state.

No source/test/doc/PRD/plan/capsule change or commit was made. No worktree,
branch or executed plan was created. Probe roots/children were cleaned/reaped.
Older evidence is retained and checked by content hash in the final audit.
Review prompts, inputs, scripts, raw results and built artifacts are intentionally
retained. Both build hashes match the handoff:
sdist `e633eb9803b311210106b7673db408c63e27205ec2669184421e43fd10bc19ec`;
wheel `f3e6b76240f72608ecf9d4761ff172e2502ee358c9cd79d152324ad9b1fe657a`.
The saved review shape and final source/artifact audit are recorded in
[00004-cycle-10-final-audit.json](00004-cycle-10-final-audit.json).
