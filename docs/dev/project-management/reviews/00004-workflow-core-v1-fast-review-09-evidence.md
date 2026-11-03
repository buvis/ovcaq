# FT-04R9 evidence — PRD 00004

Review date: 2026-09-05, Europe/Prague. This is fresh review-session evidence,
not a reuse of the repair session's verification. The initial tool outage ended
without writes; work resumed after the user's “maybe it works now” message.

## Scope and state

Verified before changes: master at `78f916c366f74105b76e6f07d80a7a1aeb251e9f`,
empty Git status. Full implementation range:
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..78f916c366f74105b76e6f07d80a7a1aeb251e9f`.
Ten commits, 70 changed files, +9362/-348. Repair-only base:
`8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`.
The coordinator reviewed the full range and current workflow implementation;
the newest commit was not substituted for the full obligation set.

Mandatory inputs read: AGENTS.md, WIP PRD, accepted implementation plan (read
only), coverage manifest, resolved discovery 00001, both characterization TOMLs,
cycle-08 verdict/evidence and rework-08 with its probe/size evidence. No older
review history or live launcher data was opened.

Fresh source-contract join: exactly ten source tasks and **55 owned rows**.
[Join and source text](00004-cycle-09-owned-rows.json);
[preflight](00004-cycle-09-preflight.json).
Plan SHA-256: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
Inventory SHA-256: `d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9`.
Both match the accepted coverage pointers.

[Task context](../tmp/review-tasks-00004-cycle-09.md) retains each source task
and phase exit criterion verbatim, one task per row. P02-T01–T05 share initial
commit `06fdf88149a7cafd6d3f4ec9aedf1510a59a652a`; P02-T06–T10 share
`5a7ff023059bd396a177da7946a25ffe8d6d176d` (pure paths also in the former).
All eight subsequent repair commits are in the reviewed range.

## Fresh verification

Exact command output: [verification log](00004-cycle-09-verification.md).
All commands used mise-managed uv. A cache sandbox denial was rerun through
the approved escalation path.

| Command | Result |
|---|---|
| `mise exec -- uv sync --all-groups` | Exit 0; 25 resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/ tests/packaging/ -q` | 427 passed in 10.37s |
| `mise exec -- uv run pytest` | 1315 passed in 19.06s; 0 failed, 0 skipped |
| `mise exec -- uv run ruff check .` | All checks passed |
| `mise exec -- uv run ruff format --check .` | 114 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | No issues in 51 source files |
| `mise exec -- uv build` | sdist and wheel built |
| `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..HEAD` | Exit 0 |

Darwin, Python 3.13.13, pytest 9.1.1. Both complete workflow/packaging directories
were run after the prior test splits, including installed-origin checks.
Alice separately ran 48 focused R8 regressions in 0.23s. Counts overlap and are
not added together. Blake used isolated probes; Bob was static-only. Bob's
VERIFY item is resolved by these fresh coordinator gates, without a second
suite-only task.

## Ten source-task assessments

| Task | Contract and current evidence | Assessment |
|---|---|---|
| P02-T01 | Selection ordering, ties, hold exclusion, invalid/missing directories and configured lifecycle paths; selection/configuration tests and installed workflow inputs. | Covered. |
| P02-T02 | Defaults/enums/positive caps/optional flags, active-PRD binding, CAS, overwrite ownership, abstract tier availability; frontmatter/application and installed CLI tests. | Covered within accepted derived-state boundary; Blake disagreement adjudicated below. |
| P02-T03 | Six phase/outcome rows, all rejection rows and full effects, atomic revision, rework/convergence/reset and terminal drain; transitions/application/installed tests. | Covered; terminal drain must remain terminal. |
| P02-T04 | Recovery/pause/phase/task resume precedence, schema preflight, tolerant plan counting, 15-task ceiling, override and dependency shape; resume/policy/characterized fixtures. | Covered; runtime execution policy retains its owner. |
| P02-T05 | Exact reset owners, sibling and batch/capability preservation, deterministic completed summaries, matching/conflicting replay and substantive decision counts; records/application/blank-decision suites. | Covered; R8-06 verified. |
| P02-T06 | Attribution, strict root/items decoding, operation-ID replay/conflict, canonical durable writes, sidecar lock ownership, retries and nonregular inputs; ledger/boundary and installed tests. | Blocked by R9-01. Tests at named boundaries pass, but the final pre-replace interval loses a successful append. |
| P02-T07 | Durable typed intent, explicit kind, original device/inode, exclusive move, recorded-stage restart, publication guards, reset/commit, conflict refusal, second-park halt and all named failpoints. | R8-02 repaired; shared ledger guarantee blocked by R9-01. Missing-source refusal remains accepted. |
| P02-T08 | Audit/report/metrics goldens, unknown legacy/mixed totals, nonzero binding, equal-key stable ordering, active-batch filtering, replaceable sections, full deferred details, archive and fsync/replay. | Blocked by R9-02 publication identity; R9-04 is bounded de-slop. R8-04/05/06 repaired. |
| P02-T09 | CLI > project > user > defaults, walk-up paths, independent state override, configured lifecycle/runtime/ledger/report roots, containment/symlink/FIFO refusal and active tier keys. | Blocked by R9-03 malformed project/user TOML; downstream provider configuration is excluded. |
| P02-T10 | Live workflow registry, root parser, generated operations/state-protocol inventories, help and documentation contract tests. | Covered; no second handwritten verb inventory. |

Phase A's pure fixtures/transitions/reset checks pass within accepted ownership.
Phase B's “without duplicate records or lost work” exit is blocked by R9-01.
Phase C's installed/rendering exit is blocked by R9-02/R9-03 even though its
retained tests pass. Provider-neutral dependency/string guards and parser/docs
checks pass. PRD completion is not approved.

## All 55 owned characterization rows

Evidence groups name current files, after the R8 splits. Paths for unqualified
test names below are under `tests/workflow/`; production under
`src/ovcaq/workflow/`, except the shared config/CLI/path modules.

- **Selection (3):** selection.py, paths.py; test_selection.py,
  test_configuration.py, packaging/test_workflow_inputs.py.
- **Frontmatter (2):** frontmatter.py, workflow_cli.py; test_frontmatter.py,
  test_applications.py, packaging/test_installed_cli.py and test_input_integrity.py.
- **Policy (3):** policy.py; test_policy.py, test_applications.py,
  test_workflow_cli.py and installed CLI tests.
- **Resume (2):** resume.py; test_resume.py, test_characterized_fixtures.py,
  installed workflow inputs/sagas.
- **Transitions (3):** transitions.py; test_transitions.py, test_records.py,
  test_applications.py, installed lifecycle dispatch.
- **Records (28):** records.py, _files.py, _rename.py; test_records.py,
  test_deferred_ledger.py, test_ledger_integrity.py, test_sagas.py,
  test_saga_artifacts.py, test_saga_identity.py, test_saga_publication.py,
  test_boundaries.py, test_blank_decisions.py; packaging/test_installed_sagas.py,
  test_workflow_inputs.py, test_input_integrity.py; split state
  test_recovery_mutations.py and test_service_contracts.py.
- **Reports (13):** reports.py, shared decision filter in records.py;
  test_reports.py, test_report_recovery.py, test_blank_decisions.py,
  packaging/test_installed_reports.py, retained sanitized metrics and v1 goldens.
- **Docs (1):** workflow_cli.py, cli.py; test_workflow_cli.py, state/test_cli.py;
  operations.md and state-protocol.md inventories generated from the parser.

“Covered” means traced to implementation and passing retained checks; it is not
a claim that every adversarial input has been exhausted. Cross-cutting blockers
remain attached to the task and phase even where an individual projection passes.

| Owned ID | Accepted source obligation | Evidence group | Current assessment |
|---|---|---|---|
| ART-012 | Drained state archived as reports/{batch}-state-final.json before post-drain actions. | Reports | Projection covered; publication identity R9-02 |
| ART-013 | Durable batch Markdown report with replaceable per-PRD sections, stalled records, and final summary. | Reports | Projection covered; publication identity R9-02 |
| ART-014 | Durable review-directory Markdown projection of autonomous, deferred, and doubt decision arrays. | Reports | Projection covered; publication identity R9-02 |
| ART-016 | deferred/{batch}-deferred.json append ledger used for stalls and decisions carried to batch end. | Records | R9-01: lock split can lose a successful append |
| ART-017 | Independent sidecar advisory lock serializing deferred-ledger updates. | Records | R9-01: lock split can lose a successful append |
| ART-026 | Verified JSON handoff from supervisor death/stall decision to the next workflow session. | Records | Identity/failpoints covered; shared ledger blocker R9-01 |
| ART-036 | backlog, wip, hold, and done files provide selection and verified-move lifecycle evidence. | Selection | Covered; retain characterized behavior |
| ART-039 | Current sanitized rendering inputs, including legacy and rich nested state shapes. | Reports | Covered; retain characterized behavior |
| ART-040 | Current archived batch-state contract with completed-PRD and decision history. | Reports | Covered; retain characterized behavior |
| ART-041 | Expected audit, metrics, report-section, report-summary, and status rendering contracts. | Reports | Covered; retain characterized behavior |
| CMD-007 | Runs the durable stall saga for a PRD, including hold move, defer record, and reset. | Records | Identity/failpoints covered; shared ledger blocker R9-01 |
| CMD-008 | Consumes or reconciles a park request and applies the systemic-park breaker. | Records | Identity/failpoints covered; shared ledger blocker R9-01 |
| CMD-009 | Atomically clears per-PRD state and restores build counters and phase markers. | Transitions | Covered; retain characterized behavior |
| CMD-010 | Appends one JSON object to a batch deferred ledger with PRD attribution. | Records | R9-01: lock split can lose a successful append |
| CMD-012 | Reads the task snapshot and returns a distinct failure when its count exceeds the loop ceiling. | Policy | Covered; retain characterized behavior |
| CMD-013 | Selects deterministically from wip then backlog while excluding hold, returning JSON even when drained. | Selection | Covered; retain characterized behavior |
| CMD-014 | Parses PRD controls, warns on defaults, and transactionally applies the derived state fields. | Frontmatter | Covered within accepted derived-state ownership |
| CMD-015 | Applies one named workflow outcome from the current phase as an atomic transition. | Transitions | Covered; retain characterized behavior |
| CMD-016 | Returns the authoritative resume target after schema-version preflight. | Resume | Covered; retain characterized behavior |
| CMD-018 | Renders the per-PRD decision audit from state arrays into the repository review directory. | Reports | Projection covered; publication identity R9-02 |
| CMD-019 | Creates or updates batch report PRD, stalled, or summary sections from state and metrics. | Reports | Projection covered; publication identity R9-02 |
| CMD-020 | Prints a deterministic Markdown summary of loop metrics rows. | Reports | Covered; retain characterized behavior |
| CMD-036 | Appends a computed completed-PRD batch summary and resets consecutive parks. | Records | Covered; retain characterized behavior |
| DEC-071 | A real task list longer than the ceiling is over-limit; missing or non-list tasks count as zero. | Policy | Covered; retain characterized behavior |
| DEC-076 | Malformed or conflicting stall intent, mismatched PRD, or missing batch identity refuses before filesystem effects. | Records | Covered; retain characterized behavior |
| DEC-077 | Hold creation/move, deferred append, or state transaction failure returns its distinct code while durable intent preserves retryability. | Records | Covered; retain characterized behavior |
| DEC-078 | Verified move plus deduplicated defer record commits PRD reset, park-breaker rule, and intent deletion atomically. | Records | Covered; retain characterized behavior |
| DEC-079 | No marker returns no-work unless a pending stall intent exists, which is reconciled first. | Records | Covered; retain characterized behavior |
| DEC-080 | Malformed marker or PRD no longer in wip is deleted and returns ignored without moving another PRD. | Records | Covered; retain characterized behavior |
| DEC-081 | The first consecutive wrapper-death park moves and resets the PRD, increments the breaker, and continues. | Records | Covered; retain characterized behavior |
| DEC-082 | The second consecutive wrapper-death park also writes paused/systemic_park state and returns the halt code. | Records | Covered; retain characterized behavior |
| ENV-025 | Test-only durable-saga interruption selector for named stall/park boundaries. | Records | Covered; retain characterized behavior |
| STATE-112 | Per-batch durable deferred object containing batch_id and ordered items. | Records | R9-01: lock split can lose a successful append |
| STATE-113 | Caller record copied with prd attribution; op_id deduplicates retrying stall appends. | Records | R9-01: lock split can lose a successful append |
| STATE-121 | JSON handoff carrying prd and reason for the next session's durable park saga. | Records | Identity/failpoints covered; shared ledger blocker R9-01 |
| TEST-001 | Characterizes subprocess dispatch, stall and park outcomes, reset and restore behavior, deferred records, diagnostics, and exit codes. | Records | Identity/failpoints covered; shared ledger blocker R9-01 |
| TEST-002 | Characterizes walk-up default path resolution and explicit state or PRD-directory override precedence for stall and park. | Records | Paths covered; malformed configuration R9-03 |
| TEST-005 | Pins documentation coverage for every registered CLI subcommand. | Docs | Covered; retain characterized behavior |
| TEST-006 | Characterizes PRD frontmatter parsing, defaults, enum and integer validation, malformed blocks, optional flags, and warnings. | Frontmatter | Covered within accepted derived-state ownership |
| TEST-008 | Characterizes selection, phase transitions, resume targets, convergence, rework, drain, frontmatter application, walk-up paths, and future-state refusal. | Records | Identity/failpoints covered; shared ledger blocker R9-01 |
| TEST-012 | Characterizes the fifteen-task plan ceiling, override semantics, tolerant task counting, no mutation, CLI exposure, and missing-state failure. | Policy | Covered; retain characterized behavior |
| TEST-013 | Characterizes deferred-log append and deduplication plus the authoritative per-PRD reset field set and preservation rules. | Records | R9-01: lock split can lose a successful append |
| TEST-014 | Characterizes record, stall, and park boundary failures, corrupt shapes, invalid identifiers, filesystem errors, idempotent retry, and no-effect guarantees. | Records | R9-01: lock split can lose a successful append |
| TEST-015 | Pins that importing records through the CLI does not leak the scripts directory into the interpreter search path. | Records | Covered; retain characterized behavior |
| TEST-016 | Characterizes park-marker reconciliation, crash recovery, conflicting stall intents, atomic reset and counter updates, and systemic second-park halt. | Records | Identity/failpoints covered; shared ledger blocker R9-01 |
| TEST-017 | Characterizes durable stall intent, verified PRD moves, deferred append, reset composition, crash-point retries, conflicts, and site-specific park-counter handling. | Records | Identity/failpoints covered; shared ledger blocker R9-01 |
| TEST-018 | Characterizes status, audit, metrics, and report rendering against goldens, tolerant missing data, batch scoping, decision tables, flags, and rerender effects. | Reports | Projection covered; publication identity R9-02 |
| TEST-019 | Pins omission of wholly blank autonomous-decision rows while retaining zero and any populated renderable cell. | Reports | Covered; retain characterized behavior |
| TEST-020 | Characterizes exact Markdown section replacement, duplicate collapse, heading boundaries, unrelated-section preservation, and report idempotence. | Reports | Projection covered; publication identity R9-02 |
| TEST-021 | Characterizes resume-target priority across stall intent, park marker, pause and stall state, phase routing, legacy phases, and systemic park halt without mutation. | Resume | Covered; retain characterized behavior |
| TEST-027 | Characterizes five-digit PRD sequence parsing, deterministic ordering, Markdown filtering, work-in-progress priority, backlog fallback, drain, and hold exclusion. | Selection | Covered; retain characterized behavior |
| TEST-029 | Characterizes the pure transition table for phase advancement, rework, convergence, per-PRD reset, drain, marker idempotence, and unknown input refusal. | Transitions | Covered; retain characterized behavior |
| TEST-038 | Pins phase-two stall effects: PRD moves to hold, stall clearing, per-PRD reset, batch preservation, hold creation, and sequence retention. | Records | Identity/failpoints covered; shared ledger blocker R9-01 |
| TEST-052 | Characterizes atomic completed-PRD record creation, task and cycle defaults, escalated and autonomous decision counts, blank-row filtering, PRD matching, reset, and sibling preservation. | Records | Covered; retain characterized behavior |
| TEST-062 | Characterizes batch-summary binding of completed-PRD counts and cycle and decision totals: nonzero retained values, legitimate empty zeros, and unknown sums for legacy or mixed records. | Reports | Covered; retain characterized behavior |

Accepted extraction adaptations remain: typed intent and explicit operation
kind replace launcher-specific handoff markers; injectable named boundary hooks
replace the legacy test environment selector; sanitized fixtures use v1 state.
No importer, permanent old-command alias, launcher marker, provider policy,
unrelated state restructuring or Linux signoff is added to this review's scope.

## R8-01–R8-08 reassessment

| Repair | Fresh evidence | Verdict |
|---|---|---|
| R8-01 | Duplicate root/item keys and excessive JSON depth refuse; ledger bytes survive append/load/report; installed errors are contextual usage/resource-limit JSON. New ledger-integrity and installed input tests pass. | Repaired. |
| R8-02 | Source/held replacement before rename, after rename and across intent/moved/recorded restart retains tasks, intent and original device/inode. Original-artifact restoration reconciles once; exact replay retains bytes. | Repaired. |
| R8-03 | Named BEFORE_PUBLISH and post-replace boundaries with nested/real-process rivals pass. New syscall-boundary nested and real-process probes lose the rival append before the original reports identity loss. | Incomplete: R9-01 preserves the coordinator-only root. |
| R8-04 | First rendering contains earlier/current PRD deferred details and attribution; duplicate/reordered inputs, changed detail, next PRD and exact rerender pass. | Repaired. |
| R8-05 | Report/audit/archive parent sync on creation/existing retry; post-replace directory-fsync failure and identical-content replay sync pass. | Specified fsync repairs verified. New pathname-identity defect is R9-02. |
| R8-06 | Metadata/status-only blank rows excluded; substantive ID/kind/summary/rationale/cycle, string/numeric zero and populated individual cells retained. | Repaired. |
| R8-07 | Installed frontmatter, defer, project-config and user-config FIFOs refuse within two seconds, with state preservation and symbolic JSON errors. | Specified regular-file repair verified. Nested TOML is new R9-03. |
| R8-08 | Complete split suites pass. State service tests 774 lines, records.py 783. New/changed workflow/packaging functions <=50; three inherited packaging functions AST-identical to base. | Repaired; R9-04/05 are separate bounded duplication findings. |

## Reproductions and counterexamples

[Coordinator probe source](00004-cycle-09-probes.py) /
[19 observations](00004-cycle-09-probes.json) reuse only the explicitly authorized
cycle-08 sanitized fixture functions, with fresh lock/config variants.
[Publication probe source](00004-cycle-09-publication-probes.py) /
[three publication observations](00004-cycle-09-publication-probes.json).
[Adjudication probe source](00004-cycle-09-adjudication-probes.py) /
[results](00004-cycle-09-adjudication-probes.json).
Run each with `mise exec -- uv run python <repo-relative-script-path>`.
All effects use disposable roots and scoped mocks; subprocesses have timeouts
and are reaped.

**R9-01:** At `_files.py:98–99`, `verify_lock()` has returned but native
`os.replace` has not run. Rename the held sidecar aside; a legitimate second
writer acquires the new sidecar, commits `second`, and returns success. Let the
first writer resume its native replacement. The first later raises
“deferred lock identity changed,” but the ledger contains only `first`.
Retry still contains only `first`. This reproduces with a nested writer and
with a separate Python process (exit 0, “committed second”). It is an actual
successful record loss, not merely a changed lock pathname. The earlier
BEFORE_PUBLISH control preserves `second`, and retry produces
`second, first`; this locates the remaining interval beyond the repaired hook.

**R9-02:** Rename and recreate the publication directory just before native
replacement. All three APIs return success with a nonexistent returned path;
the report/audit/archive payload is only in the displaced directory.
The retained fd prevents symlink traversal but does not prove that the
configured directory still names that fd. Protect the chain through publication,
identical replay and successful return; preserve the existing fsync guarantees.

**R9-03:** Project and user TOML with 2,000 nested arrays raises RecursionError
from `config.py:47` before the JSON command error boundary can normalize it.
The coordinator used a workflow path field; Alice independently used an ignored
key. The same failure reproduces in a freshly installed wheel outside the
checkout, with both ovcaq and ovcaq.config origins in its temporary site-packages:
[exact installed command and result](00004-cycle-09-installed-config.json).
Both scopes exit 1, emit a traceback and no stdout; config bytes survive.
Existing-state probes preserve state too. This is the current workflow's shared
input reader, not downstream provider/model policy.

**R9-04/05:** Direct source inspection confirms duplicated heading-span lookup
at reports.py:570/590 and identical subprocess invocation at
packaging_support.py:162/184. These are newly introduced surfaces in the full
range. One private span finder and delegation from _run to _run_unchecked
remove duplicated policy without changing behavior. Preserve all assertions,
installed origins, timeout/environment, diagnostic text and section semantics.

## Disagreement adjudication

No reviewer saw another reviewer's output before returning. Raw outputs and
their failures remain verbatim in the main review; a coordinator disposition
does not rewrite a lens verdict.

- **Alice's R8-03 repaired assessment:** valid for the inspected named boundaries,
  contradicted by the later syscall interleaving. R9-01 stays High with **0/3
  lens votes**, independently reproduced by the coordinator, including a real
  rival process. Consensus is not a veto over demonstrated record loss.
- **Blake frontmatter objection:** observed behavior is confirmed using a real
  StateStore: skip/force are returned in `FrontmatterApplication.fields`, while
  `resume_target` still follows committed catchup facts; changing these controls
  later produces no overwrite warning for a nonexistent durable control copy.
  The accepted source task is parsing/defaults/warnings, and the accepted v1
  crosswalk derives legacy catchup/design/pause/reviewer signals from their
  state owners rather than storing duplicate policy. Current tests deliberately
  bind returned fields separately from cap/tier ownership. The settled
  downstream runtime/configuration owner must consume policy inputs and record
  actual lifecycle facts; parsing cannot fabricate catchup/design completion.
  No new PRD-00004 repair is requested. This disposition does **not** claim that
  skip/force are already executed or that frontmatter is durable runtime policy.
  References: frontmatter.py:165–216, resume.py:34–47,
  docs/state-protocol.md:310–327, test_applications.py:29–107.
- **Bob B1 null-artifact intent:** observed dead end is confirmed. Missing source
  publishes explicit null identity and preserves the unfinished task. A later
  file is rejected; retry preserves state bytes. Rework-08 explicitly accepts
  null as missing-source failure evidence and forbids adoption of a later
  replacement; test_sagas.py:209 pins it and state-protocol.md:222 documents it.
  Removing that intent or accepting an unverified artifact would reverse the
  required preservation decision. No automatic recovery from an initially
  absent, unidentified source is claimed. A new abort/rollback API is not
  authorized. The raw finding is retained as a settled-scope objection, with
  no repair task.
- **Bob B5 executable verification:** resolved by the fresh gates above.
- **Bob B3/B4 versus Alice's no-additional-simplification judgment:** coordinator
  accepts the two exact duplications as the skill's required bounded Medium
  de-slop findings; no behavioral restructuring is proposed.

## Mechanical checks and limitations

All three mandated helpers ran; their exact commands/output are in the
[implementation context](../tmp/review-context-00004-cycle-09.md).
AST facts and test-shape checks were available to implementation-aware lenses.
The detector examined 263 test functions in 36 files and emitted one MECH row:
`test_init_rejects_project_config_path_collisions_before_state_publication`
at tests/state/test_cli.py:372. It is absorbed into inherited R8-K1, with
mech-check explicitly listed. Other assertions in the test still fail, so
the detector's generic “cannot fail” preamble overstates this local weakness.

The mandated full-base replay helper returned “skipped,” exit 4 from pytest
collection, missing `packaging_support`. That is not evidence of passing
behavior on the base and no comprehensive full-range fail-first claim follows.
The known broken invocation was not retried.

A separate bounded **repair-base** replay overlays all current tests/support,
never production, on a disposable detached worktree at `8ef6c0d`.
[Replay program](00004-cycle-09-repair-replay.py);
[complete observed result](00004-cycle-09-repair-replay-result.json).
Five retained R8 regression files collected all 56 cases: **46 failed, 10 passed
in 9.81s**. The ten passes preserve valid nonblank/zero decision behavior.
Production diff was empty; the worktree was removed. This supplies binding for
the eight installed regression cases as well, but they originally ran after
their repair: this review is not chronological TDD evidence.

[AST comparison](00004-cycle-09-size-measurements.json): add_task remains 53
lines, with only the transaction wrapper changed; schema.py was 927 lines
before the required six-line artifact identity type. Installed-wheel fixture
51, distribution assertion 79, origin assertion 66 are structurally unchanged.
R8-K1/R8-K2 remain KNOWN; inherited schema size and incomplete full-base binding
are retained as R9-K3/R9-K4. No broad state split or replay-tool project is added.

Darwin syscall/failpoint evidence is not a power-loss test or Linux
qualification. Native isolated host lenses provide prompt isolation, **not model
diversity**. External nested dispatch guards were not bypassed or retried.
No review result derives from live launcher fixtures.

## Lens execution and terminal accounting

[Dispatch record](00004-cycle-09-dispatch.json) retains roles, prompt paths and
visibility restrictions. Alice: full R1–R4/R6–R13 consensus rubric. Blake:
complete B1–B19 PRD-only rubric. Bob: full consensus rubric plus both doubt and
de-slop lenses, FIX/VERIFY/KNOWN and **D1–D5** (the installed names for the
requested doubt R1–R5 obligations). There is no consensus R5 in this version;
no rule was silently omitted.

Bob's raw count is 9 = 4 FIX + 1 VERIFY + 4 KNOWN. All five doubt verdicts are
pass in his raw response. Coordinator moves his B1 to the settled-scope
adjudication and resolves B5 through execution; it adds Alice's TOML finding
and the coordinator lock finding. After scoped objections and verified checks
are resolved, terminal residual count is **9 = 5 FIX + 0 VERIFY + 4 KNOWN**.
Each residual has one disposition, bounded action or written inherited reason.
Raw consolidation yielded 11 rows and is retained unchanged
[here](00004-cycle-09-consolidation-raw.md); post-consolidation reasoning is
explicit above rather than hidden in script inputs.

All three native reviewers completed before any raw output was written.
Standalone mode: no autopilot task store/queue, attempt ledger, persisted doubt
verdicts or unrelated state was read or mutated. Reported follow-ups are in the
[repair handoff](../plans/fast-track-handoffs/00004-workflow-core-v1/review-09.md).
The review file shape gate and final artifact/state audit are recorded in
[final audit](00004-cycle-09-final-audit.json). The PRD and accepted plan remain
unchanged; retained session artifacts are intentional evidence.
