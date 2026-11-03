# FT-04R11 evidence companion

Date: 2026-09-06 Europe/Prague; this session began on 2026-09-05.
Reviewed HEAD `22d9193a0d00486b09ebea169e7a38a9f858799d`, branch master.
Full base `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`.
The review is complete; implementation completion is **not approved**.

## Sources and scope

Global/repository AGENTS.md, WIP PRD, accepted plan, coverage manifest,
resolved discovery 00001 and both characterization TOMLs were read. Both TOMLs
parsed completely: 603 inventory items, with exactly 55 unique PRD-00004 owned
rows joined to source/evidence/target/disposition. All ten source tasks retain
individual rows and original shared implementation commits in
[task context](../tmp/review-tasks-00004-cycle-11.md).
[Fresh full source join](00004-cycle-11-owned-rows.json) retains every field.

Plan SHA-256: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
Inventory SHA-256: `d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9`.
Both match the accepted manifest. No accepted-plan edit occurred.

[Preparation script](00004_cycle_11_prepare.py) invokes the mandated
gather-context helper with an explicit full base. Its temporary copy redirects
only output storage into a context-managed temporary directory; all resulting
repo artifacts are written by apply_patch. Both mechanical helpers run over
the complete 73-file changed list. Prompts independently substitute registry
bodies and full rubrics; there is no copied fallback prompt.
[Implementation context](../tmp/review-context-00004-cycle-11.md) includes measured
function sizes and the single inherited MECH finding.

The source pack used is
`/Users/bob/git/src/github.com/buvis/claude-autopilot`; its required codex wrapper
is executable. Personas/frontmatter and invocation/retry/output contracts were
read. Missing engram registration is an optional-pack failure, not permission to
change the registry or refresh the capsule. No review-target design document or
settled JSON ledger exists; settled decisions are supplied in Alice/Bob prompts
and applied visibly to Blake after his blind review.

## Fresh verification

[Raw command/output record](00004-cycle-11-verification.json):

| Command | Result |
|---|---|
| mise exec -- uv sync --all-groups | Exit 0, 25 resolved/24 checked |
| mise exec -- uv run pytest | 1339 passed in 23.83s; zero failed/skipped |
| mise exec -- uv run ruff check . | All checks passed |
| mise exec -- uv run ruff format --check . | 117 files already formatted |
| mise exec -- uv run mypy src/ovcaq | No issues in 51 source files |
| mise exec -- uv build | Wheel/sdist built |
| git diff --check full-base..HEAD | Exit 0 |
| Alice focused overlapping verification | 102 passed in 3.88s; not added to suite total |

The full suite includes all workflow/packaging tests and the installed A→B→A
report regression. No redundant second workflow/packaging suite was run.
No unrelated last-verification record supplied counts. Sandbox uv cache
failure was retried with escalation; fact-forcing refusals were satisfied and
the quality calls rerun successfully. No verification gate was waived.

Built wheel SHA-256:
`8181a0ca7e3ff1dceb0577fd144347f73021451ca63cd049129a0c7a70739a6b`.
Built sdist SHA-256:
`e869f5b37e43df1bdcd425a2be0897f2d69516e1cf04f32a0c203c8b035691ce`.
Both equal the R10 repair handoff.

## Fresh installed adjudication

[Executable probe source](00004_cycle_11_probes.py) /
[complete raw subprocess output](00004-cycle-11-probes.json).

The script installs the rebuilt wheel in a fresh temporary environment, removes
PYTHONPATH/PYTHONHOME/VIRTUAL_ENV influence, runs outside the checkout and verifies
six module origins in site-packages. Every project/state/record is disposable;
all authoritative probe changes use installed StateStore. The root and child
processes are context-managed/reaped. Outer exit 0 means all *defect-observation
assertions* held. It is not a passing product expectation.

### R11-01: standalone item depth versus ledger depth

| Standalone depth | Append | Read | Exact replay | Subsequent seed append |
|---|---|---|---|---|
| 30 | 0 | seed+nested | 0 | 0 |
| 31 | 0 | ResourceLimitError | 11 | 11 |
| 32 | 0 | ResourceLimitError | 11 | 11 |
| 33 | 11, seed bytes unchanged | seed | 11 | 0 |

Every row preserves authoritative state. Depth31/32 payloads are valid as
standalone inputs but become invalid under `items[]`. Their successful writer
publishes bytes rejected by the existing reader. Existing records are not
deleted from the bytes; the ledger becomes unusable through public operations.
This directly blocks CMD-010/STATE-112/STATE-113 and propagates to ledger readers
and later sagas. New tests must bind rejection to unchanged existing bytes.

### R11-02: real-process report overlap

Seed publication succeeds. A's installed CLI entry runs in a child process and
pauses only immediately before its existing publication call, after reading and
composing. Installed StateStore commits active B; the unmodified installed
console publishes B. A resumes. Both report commands return exit 0, but A's
final artifact omits B. Prior seed remains; A returned text equals artifact.
A B retry reconstructs seed+A+B. The coordination changes scheduling, not the
product's rendering/composition/publication implementation.

A stale report snapshot is a reachable command overlap, and accepted batch
reports preserve prior PRD sections. No supervisor, model, or arbitrary graph
policy is needed to fix this publication boundary.

### R11-03: nested configured-root durability

Installed CLI `main` uses a valid independent --state and initially absent
configured `new/nested` runtime root. An fsync observer compares directory
device/inode and calls the original os.fsync for every observed call.
Both initial defer and exact replay return exit 0 and leave one valid record.

Observed directory syncs: `new/nested`, `new/nested/deferred`.
Omitted: project root (for child `new`) and `new` (for child `nested`).
Thus the completed operation never persists the entire created directory chain,
and identical replay still does not repair it. This is a missing durability
protocol, not a claim that this probe simulated power loss or observed file loss.

## Ten source tasks and phase exits

| Task | Current assessment |
|---|---|
| P02-T01 | Covered: WIP/backlog/hold rules, deterministic sequence and equal-key ordering, configured lifecycle paths |
| P02-T02 | Covered: bounded frontmatter/defaults/warnings, abstract tiers, active-PRD/CAS binding, settled downstream-control owner |
| P02-T03 | Covered: all six transition rows, rejections, complete atomic effects and terminal drain |
| P02-T04 | Covered: resume precedence, plan shape/dependencies, fifteen-task ceiling and override |
| P02-T05 | Covered: exact reset owners, batch/capability preservation, completion conflict/replay, zero/blank decisions and summaries |
| P02-T06 | Blocked by R11-01 and R11-03; idempotent operation IDs and R9 serialization repairs otherwise pass |
| P02-T07 | Existing failpoint/identity/reset/commit matrix passes; new ledger durability gap applies to its shared deferred publication |
| P02-T08 | Blocked by R11-02; R10 result equality, golden projections, output identity/fsync, metrics scoping and unknown totals pass |
| P02-T09 | Configuration resolution passes; configured nested-root durability integration blocked by R11-03 |
| P02-T10 | Covered: registry/parser-derived documentation and installed command contract |

Verbatim source exits:
- current lifecycle fixtures have equivalent OVCAQ outcomes under the new
  schema;
- park/stall interruption is recoverable at every durable boundary;
- workflow package imports no runtime, driver, TUI, or launcher module.

Assessment: lifecycle equivalence and dependency exits pass; complete durability
acceptance remains blocked by R11-03 despite passing retained boundary tests.
PRD Phase A passes. Phase B is blocked by R11-01/R11-03. Phase C is blocked by
R11-02 and the ledger publication integration. Passing retained tests do not
supersede independently reproduced gaps.

## All 55 owned rows

Each row maps to its unchanged accepted source text. “Covered” is scoped evidence,
not exhaustive adversarial proof. Shared-service blockers remain attached to the
task/phase even when one row's retained scenarios pass.

| Owned ID | Accepted obligation | Evidence group | Current assessment |
|---|---|---|---|
| CMD-014 | Parses PRD controls, warns on defaults, and transactionally applies the derived state fields. | Frontmatter | Covered within settled returned-control/downstream ownership |
| TEST-006 | Characterizes PRD frontmatter parsing, defaults, enum and integer validation, malformed blocks, optional flags, and warnings. | Frontmatter | Covered within settled returned-control/downstream ownership |
| CMD-012 | Reads the task snapshot and returns a distinct failure when its count exceeds the loop ceiling. | Policy | Retained behavior covered by current tests and inspection |
| DEC-071 | A real task list longer than the ceiling is over-limit; missing or non-list tasks count as zero. | Policy | Retained behavior covered by current tests and inspection |
| TEST-012 | Characterizes the fifteen-task plan ceiling, override semantics, tolerant task counting, no mutation, CLI exposure, and missing-state failure. | Policy | Retained behavior covered by current tests and inspection |
| ART-016 | deferred/{batch}-deferred.json append ledger used for stalls and decisions carried to batch end. | Records | R11-01/R11-03 block complete ledger validation/durability |
| ART-017 | Independent sidecar advisory lock serializing deferred-ledger updates. | Records | R9 coordinator serialization root and exact retries pass; preserve |
| ART-026 | Verified JSON handoff from supervisor death/stall decision to the next workflow session. | Records | Retained behavior covered by current tests and inspection |
| CMD-007 | Runs the durable stall saga for a PRD, including hold move, defer record, and reset. | Records | Named saga boundaries pass; ledger-dependent durability remains blocked by R11-03 |
| CMD-008 | Consumes or reconciles a park request and applies the systemic-park breaker. | Records | Named saga boundaries pass; ledger-dependent durability remains blocked by R11-03 |
| CMD-010 | Appends one JSON object to a batch deferred ledger with PRD attribution. | Records | R11-01/R11-03 block complete ledger validation/durability |
| CMD-036 | Appends a computed completed-PRD batch summary and resets consecutive parks. | Records | Retained behavior covered by current tests and inspection |
| DEC-076 | Malformed or conflicting stall intent, mismatched PRD, or missing batch identity refuses before filesystem effects. | Records | Retained behavior covered by current tests and inspection |
| DEC-077 | Hold creation/move, deferred append, or state transaction failure returns its distinct code while durable intent preserves retryability. | Records | Named saga boundaries pass; ledger-dependent durability remains blocked by R11-03 |
| DEC-078 | Verified move plus deduplicated defer record commits PRD reset, park-breaker rule, and intent deletion atomically. | Records | Named saga boundaries pass; ledger-dependent durability remains blocked by R11-03 |
| DEC-079 | No marker returns no-work unless a pending stall intent exists, which is reconciled first. | Records | Retained behavior covered by current tests and inspection |
| DEC-080 | Malformed marker or PRD no longer in wip is deleted and returns ignored without moving another PRD. | Records | Retained behavior covered by current tests and inspection |
| DEC-081 | The first consecutive wrapper-death park moves and resets the PRD, increments the breaker, and continues. | Records | Retained behavior covered by current tests and inspection |
| DEC-082 | The second consecutive wrapper-death park also writes paused/systemic_park state and returns the halt code. | Records | Retained behavior covered by current tests and inspection |
| ENV-025 | Test-only durable-saga interruption selector for named stall/park boundaries. | Records | Retained behavior covered by current tests and inspection |
| STATE-112 | Per-batch durable deferred object containing batch_id and ordered items. | Records | R11-01/R11-03 block complete ledger validation/durability |
| STATE-113 | Caller record copied with prd attribution; op_id deduplicates retrying stall appends. | Records | R11-01/R11-03 block complete ledger validation/durability |
| STATE-121 | JSON handoff carrying prd and reason for the next session's durable park saga. | Records | Retained behavior covered by current tests and inspection |
| TEST-001 | Characterizes subprocess dispatch, stall and park outcomes, reset and restore behavior, deferred records, diagnostics, and exit codes. | Records | Retained behavior covered by current tests and inspection |
| TEST-002 | Characterizes walk-up default path resolution and explicit state or PRD-directory override precedence for stall and park. | Records | Retained behavior covered by current tests and inspection |
| TEST-008 | Characterizes selection, phase transitions, resume targets, convergence, rework, drain, frontmatter application, walk-up paths, and future-state refusal. | Records | Retained behavior covered by current tests and inspection |
| TEST-013 | Characterizes deferred-log append and deduplication plus the authoritative per-PRD reset field set and preservation rules. | Records | R11-01/R11-03 block complete ledger validation/durability |
| TEST-014 | Characterizes record, stall, and park boundary failures, corrupt shapes, invalid identifiers, filesystem errors, idempotent retry, and no-effect guarantees. | Records | R11-01/R11-03 block complete ledger validation/durability |
| TEST-015 | Pins that importing records through the CLI does not leak the scripts directory into the interpreter search path. | Records | Retained behavior covered by current tests and inspection |
| TEST-016 | Characterizes park-marker reconciliation, crash recovery, conflicting stall intents, atomic reset and counter updates, and systemic second-park halt. | Records | Named saga boundaries pass; ledger-dependent durability remains blocked by R11-03 |
| TEST-017 | Characterizes durable stall intent, verified PRD moves, deferred append, reset composition, crash-point retries, conflicts, and site-specific park-counter handling. | Records | Named saga boundaries pass; ledger-dependent durability remains blocked by R11-03 |
| TEST-038 | Pins phase-two stall effects: PRD moves to hold, stall clearing, per-PRD reset, batch preservation, hold creation, and sequence retention. | Records | Named saga boundaries pass; ledger-dependent durability remains blocked by R11-03 |
| TEST-052 | Characterizes atomic completed-PRD record creation, task and cycle defaults, escalated and autonomous decision counts, blank-row filtering, PRD matching, reset, and sibling preservation. | Records | Retained behavior covered by current tests and inspection |
| ART-012 | Drained state archived as reports/{batch}-state-final.json before post-drain actions. | Reports | Retained behavior covered by current tests and inspection |
| ART-013 | Durable batch Markdown report with replaceable per-PRD sections, stalled records, and final summary. | Reports | R11-02 blocks preservation under overlapping publication; R10 equality passes |
| ART-014 | Durable review-directory Markdown projection of autonomous, deferred, and doubt decision arrays. | Reports | Retained behavior covered by current tests and inspection |
| ART-039 | Current sanitized rendering inputs, including legacy and rich nested state shapes. | Reports | Retained behavior covered by current tests and inspection |
| ART-040 | Current archived batch-state contract with completed-PRD and decision history. | Reports | Retained behavior covered by current tests and inspection |
| ART-041 | Expected audit, metrics, report-section, report-summary, and status rendering contracts. | Reports | Retained behavior covered by current tests and inspection |
| CMD-018 | Renders the per-PRD decision audit from state arrays into the repository review directory. | Reports | Retained behavior covered by current tests and inspection |
| CMD-019 | Creates or updates batch report PRD, stalled, or summary sections from state and metrics. | Reports | R11-02 blocks preservation under overlapping publication; R10 equality passes |
| CMD-020 | Prints a deterministic Markdown summary of loop metrics rows. | Reports | Retained behavior covered by current tests and inspection |
| TEST-018 | Characterizes status, audit, metrics, and report rendering against goldens, tolerant missing data, batch scoping, decision tables, flags, and rerender effects. | Reports | R11-02 blocks preservation under overlapping publication; R10 equality passes |
| TEST-019 | Pins omission of wholly blank autonomous-decision rows while retaining zero and any populated renderable cell. | Reports | Retained behavior covered by current tests and inspection |
| TEST-020 | Characterizes exact Markdown section replacement, duplicate collapse, heading boundaries, unrelated-section preservation, and report idempotence. | Reports | R11-02 blocks preservation under overlapping publication; R10 equality passes |
| TEST-062 | Characterizes batch-summary binding of completed-PRD counts and cycle and decision totals: nonzero retained values, legitimate empty zeros, and unknown sums for legacy or mixed records. | Reports | Retained behavior covered by current tests and inspection |
| CMD-016 | Returns the authoritative resume target after schema-version preflight. | Resume | Retained behavior covered by current tests and inspection |
| TEST-021 | Characterizes resume-target priority across stall intent, park marker, pause and stall state, phase routing, legacy phases, and systemic park halt without mutation. | Resume | Retained behavior covered by current tests and inspection |
| ART-036 | backlog, wip, hold, and done files provide selection and verified-move lifecycle evidence. | Selection | Retained behavior covered by current tests and inspection |
| CMD-013 | Selects deterministically from wip then backlog while excluding hold, returning JSON even when drained. | Selection | Retained behavior covered by current tests and inspection |
| TEST-027 | Characterizes five-digit PRD sequence parsing, deterministic ordering, Markdown filtering, work-in-progress priority, backlog fallback, drain, and hold exclusion. | Selection | Retained behavior covered by current tests and inspection |
| CMD-009 | Atomically clears per-PRD state and restores build counters and phase markers. | Transitions | Retained behavior covered by current tests and inspection |
| CMD-015 | Applies one named workflow outcome from the current phase as an atomic transition. | Transitions | Retained behavior covered by current tests and inspection |
| TEST-029 | Characterizes the pure transition table for phase advancement, rework, convergence, per-PRD reset, drain, marker idempotence, and unknown input refusal. | Transitions | Retained behavior covered by current tests and inspection |
| TEST-005 | Pins documentation coverage for every registered CLI subcommand. | Docs | Retained behavior covered by current tests and inspection |

Evidence groups refer to the current files:

- Selection: workflow/selection.py and paths.py; test_selection.py,
  test_configuration.py, packaging/test_workflow_inputs.py.
- Frontmatter: frontmatter.py/workflow_cli.py; test_frontmatter.py,
  test_applications.py, installed inputs/integrity.
- Policy/Resume: policy.py/resume.py; test_policy.py, test_resume.py,
  test_characterized_fixtures.py and installed CLI.
- Transitions: transitions.py; test_transitions.py, test_applications.py,
  test_records.py and installed lifecycle/sagas.
- Records: records.py/_files.py/_rename.py; all deferred_ledger,
  ledger_integrity, ledger_publication, records, sagas, saga_artifacts,
  saga_identity, saga_publication, boundaries, blank_decisions tests;
  installed sagas/input integrity; state recovery/service contracts.
- Reports: reports.py; test_reports.py, report_recovery, report_identity,
  blank_decisions; installed_reports, test_report_updates and sanitized goldens.
- Docs: cli.py/workflow_cli.py, workflow CLI/state CLI docs tests, operations.md
  and state-protocol.md.

## Preserved repairs and settled decisions

R10's complete result text is composed/published once and returned after verified
context exit. Its installed six-render A→B→A regression passes. No unverified
reread or public API redesign is requested.

R9's coordinator-only ledger serialization root remains: opened-directory kernel
lock, excluded reads, serialized original-snapshot comparison, sidecar ownership
and restored-sidecar refusal. Native-interval and named-boundary regressions pass.
The old rival-success adjudication raw exit 1 is retained alongside its
expected-refusal supplement; it was not rerun or misreported as passing.

R9 root-through-leaf report/audit/archive identity, deep-TOML usage errors, shared
section scanner and subprocess helper reuse all remain. R8 original saga artifact
identity, strict decoding, complete deferred details, publication/replay fsyncs,
substantive decision filtering and prompt nonregular-input refusal remain.

Retain terminal drain, conflict refusal, nonzero/unknown totals, equal-key
ordering, active-batch metrics, typed recovery kind, provider neutrality and
parser-derived docs. Null-artifact intent and refusal of later unidentified files
remain settled. Returned frontmatter controls keep their downstream owner.

Mechanical exceptions: K1 OR assertion; K2 add_task53 and three unchanged packaging
functions; K3 schema933; K4 full-base replay limitation. Measured current files:
_files403/max-function48, records783/max50, reports722/max45, schema933/max47,
commands435/max53. No new size exception is introduced by R10.
The detector's generic “cannot fail” preamble is broader than the localized OR
finding; other assertions in that test can fail.

Full-base replay was not retried. R8 bounded replay remains 56/46/10; its installed
tests were post-repair and replay is not chronological TDD. R9 23 fail-first cases
and R10's chronological report case are narrower evidence, not universal binding.
No Linux qualification is claimed.

## Consolidation, isolation and audit

Eleven script rows become seven terminal entries after visible merging of
report and K2 duplicates, resolution of VERIFY and dismissal of the settled
Blake objection. MECH attaches to K1. Bob raw count remains 8=3+1+4; final count
is 7=3+0+4. No raw opinion/severity/rubric line is rewritten.
All reviewers returned before any raw output save.

Blake received only PRD and specification sources, no diff/history/repair
decisions. Alice/Bob received full checklist/consensus rubric; Bob additionally
received both doubt/de-slop lenses and D1–D5. Native host substitution does not
establish model diversity. External Bob/Carl guard dead ends were not retried.

Historical paused PRD-00003 state exists with 25 tasks, contrary to the broad
absence wording in the incoming handoff. Branch/HEAD/clean-status preconditions
matched. Its old mtime remained 1787864775.0302238 during this review; it was not
attached or mutated. No PRD-00004 task store was fabricated. The contract card
and follow-up remain under this review's own paths.

620 prior artifacts, including the PRD, were hash-checked with zero
changes. No source/test/doc/PRD/plan/capsule edit or commit occurred. Only master
and the original worktree remain; status/stashes empty. No executed plan was
created. New review evidence and rebuilt artifacts are intentional.
Final integrity and shape gate are in [final audit](00004-cycle-11-final-audit.json).
