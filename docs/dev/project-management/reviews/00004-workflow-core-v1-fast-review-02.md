---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
session: FT-04R2
review_kind: fast-track
cycle: 2
date: 2026-09-02
base_sha: b43bf2c94d5eb0fddafca55542ef2570b45e8d52
head_sha: 56b664fc44c359b0b97282aa2e116dbf9ed44ff9
verdict: changes_requested
decision_required: false
closeout_ready: false
must_fix_root_causes: 8
rework_bundles: 3
reviewers:
  alice: available
  blake: available
  bob: available
---

# Fast review 02: 00004 workflow core v1

Complete updated PRD range reviewed:
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..56b664fc44c359b0b97282aa2e116dbf9ed44ff9`.
The range contains 30 changed files and 4,239 additions / 12 deletions across
all three PRD commits. Review was not limited to the rework commit.

Raw reports:

- `dev/local/reviews/00004-workflow-core-v1-fast-alice-02.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-blake-02.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-bob-02.md`

## Verification at reviewed head

| Check | Result |
|---|---|
| `mise exec -- uv sync --all-groups` | passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest` | passed; 1,049 tests in 10.95s |
| `mise exec -- uv run ruff check .` | passed |
| `mise exec -- uv run ruff format --check .` | passed; 89 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | passed; 47 source files |
| `mise exec -- uv build` | passed; sdist and wheel built |
| focused workflow/installed CLI | passed; 167 tests in 1.22s |
| `git diff --check <complete-range>` | passed |
| accepted-plan SHA-256 | `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5` |
| frozen autopilot-state SHA-256 | `ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f` |
| reviewed HEAD / tracked tree | exact / clean before artifact publication |

The gate ran afresh at exact HEAD. The first sandboxed `uv` access was denied
by the user cache boundary; the authorized rerun of every affected command
passed. No gate failure was waived.

## Mandatory isolated lenses

| Lens | Verdict | Raw must-fix claims | Consolidated contribution |
|---|---|---:|---|
| Alice — consensus/architecture | changes requested | 4 | false replay, recovery fencing, state crosswalk, characterized reports |
| Blake — blind/PRD-only | changes requested | 3 | false replay and installed report-directory escape independently reproduced |
| Bob — doubt/de-slop, R1–R5 | changes requested | 10 | attribution, path escape, warnings, docs/tests, and boundary challenges |

All three lenses were dispatched concurrently with their mandatory isolated
packets. Alice received AGENTS, accepted-plan, PRD, complete diff, and gate
evidence; no PRD 00004 design artifact exists. Blake received only the PRD,
complete diff, and gate evidence. Bob received AGENTS, PRD, complete diff, and
gate evidence and completed all six doubt questions plus R1–R5. None received
another lens's output, and no lens was omitted or retried.

## Cycle-01 rework audit

The complete range confirms the cycle-01 rework closed six roots outright:
cycle-local review reset, terminal-only completion, conflicting defer IDs,
provider-neutral resume text, durable rejection-matrix evidence, and defer
publication failpoints. Static lifecycle artifact validation also rejects the
previous directory and symlink cases.

Two corrected areas remain incomplete under different reproduced states:

- no-intent replay now rejects an *inactive* held PRD but still reports success
  for the active held PRD without any matching durable operation; and
- lifecycle directories are validated before intent, but a directory can be
  replaced by a symlink at the declared after-intent boundary and then be
  followed by the move.

The latter is stronger evidence than cycle 01's check-time case; both are
retained below rather than counted as new duplicates.

## Coordinator reproduction and reconciliation

The coordinator independently reproduced four disputed safety claims in
temporary directories only:

1. An active PRD present only in `hold`, with no recovery intent or ledger,
   returned `SagaResult(operation_id=None, replayed=True)` while state bytes and
   its pending task were unchanged.
2. Replacing `hold` with a symlink after durable intent but before move caused
   the PRD to be renamed into an external directory; reconciliation then reset
   state and cleared recovery.
3. A schema-valid batch ID containing `../` segments made the public report
   publisher create a report outside `runtime/reports`.
4. Symlinking the installed command's report directory to an external
   directory caused `workflow render report` to overwrite an external sentinel
   and exit successfully.

Alice separately reproduced loss of a valid `phase-complete` mutation committed
while recovery intent was active: saga reconciliation reset the phase back to
build. Bob reproduced wrong-PRD frontmatter mutation and the missing cap-3
overwrite warning. These are concrete failures, not speculative races or style
preferences.

### Reclassified reviewer claims

- Moving a converged PRD from `wip` to `done` and promoting `backlog` to `wip`
  remain caller/launcher lifecycle steps under the accepted migration source;
  P02-T05 owns summary/reset and the accepted transition table owns state
  effects. The reproduced reselection is a cross-boundary integration risk, not
  authority to invent a second filesystem saga in PRD 00004. Ownership must be
  made explicit before its supervisor/launcher consumer lands.
- `review.cap` enforcement belongs to supervisor decision policy: the accepted
  Phase 2 table explicitly defines `review + rework -> review (cycle + 1)`,
  while later runtime/supervisor work owns rotation and cap pauses. The core
  must preserve and expose the cap but must not pull PRD 00007 policy forward.
- General configuration loading/root precedence and active-agent tier-map
  injection remain P03-T01 / PRD 00005 and later routing work, as ruled in
  cycle 01. PRD 00004 must retain the pure configured-root and abstract-tier
  seams, but need not implement the future loader.
- Conflicting duplicate operation IDs supplied directly to `render_report` are
  outside the valid ledger produced by `record_defer`, which now rejects that
  conflict. Rejecting corrupted duplicates while loading can be hardened later;
  input order for an invalid multiset is not an additional current acceptance
  failure.
- Unknown-phase fallback, the CAS-adjacent active-operation guard, and the
  single-caller `_workflow_context` helper are localized R2/R3 cleanup, not
  correctness blockers.

## Must-fix root causes

### 1. No-intent destination presence still masquerades as completed replay

`records.py:544-556` accepts an active PRD already present in `hold` as proof
that the entire saga completed. It returns before intent, deferred record,
reset, or commit, leaving pending work live while reporting success. A
no-intent request must fail closed unless durable state and records prove the
same completed operation; filesystem placement alone is not authority. Add the
reproduced active-PRD case at service and installed boundaries. This is the
still-reproduced cycle-01 replay root and violates P02-T07 recovery/no-lost-work
semantics.

### 2. Active recovery intent does not fence competing workflow mutations

`phase_complete()` can commit while `recovery.operation` is active. The later
saga commit calls `reset_prd_fields()` and silently erases that valid
transition. Recovery already has precedence in `resume_target`; enforce the
same precedence at every workflow mutation boundary except the matching
reconciliation path. Add a regression that interrupts after intent, rejects a
competing mutation without byte/revision change, then reconciles normally.
This violates P02-T03/P02-T07 and the recoverability exit criterion.

### 3. Lifecycle validation is vulnerable at a declared durable boundary

`records.py:525-538` validates lifecycle directories before intent, while
`_verify_move()` later performs path-based checks and rename. At
`AFTER_INTENT_BEFORE_MOVE`, replacing `hold` with a symlink redirects the PRD
outside the lifecycle tree and still allows state reset. Anchor move and fsync
operations to verified directory handles or equivalently guarantee no-follow
containment at use time. Commit a boundary-hook regression proving an external
target and state remain unchanged. This is a security/data-loss continuation
of cycle-01 root 1 and violates verified-move recovery.

### 4. Frontmatter application is not bound to the accepted state contract

The application boundary has three coupled authority defects:

- `workflow frontmatter --prd` applies arbitrary file content without checking
  that its basename equals committed `work.prd`;
- `frontmatter.py:24-29,160-174` durably duplicates catchup/design/gate/ambiguity
  legacy fields in `work.extensions`, contradicting the accepted v1 crosswalk's
  derived targets in `docs/state-protocol.md:311-317`; and
- treating every existing cap of `3` as an unowned bootstrap default suppresses
  a real overwrite warning after an explicitly applied cap `3` is replaced.

Bind application to the active PRD, reconcile persistence with the accepted
schema/crosswalk instead of inventing duplicate core state, and preserve enough
ownership semantics to report every real overwrite. Add transactional and
installed regressions for wrong-PRD refusal, accepted state targets, and `3 ->
2` warning behavior. This violates P02-T02, committed-state attribution, and
coverage rule 7.

### 5. P02-T08's characterized reporting migration is incomplete

The accepted migration route assigns `ART-012`–`ART-014`, `ART-039`–`ART-041`,
`CMD-018`–`CMD-020`, and `TEST-018`–`TEST-020`/`TEST-062` to
`workflow/reports.py`. The current port emits synthetic current snapshots but
does not implement the final-state archive or replaceable per-PRD report
sections, and it does not migrate the audit/report/metrics golden fixtures.
Port or explicitly reconcile every routed behavior and retain golden
equivalence evidence. This is a P02-T08/source-ID evidence gap and violates the
lifecycle-equivalence success metric.

### 6. Report publication is not confined to its declared output root

`reports.py:190-210,224-243` follows symlinked parent directories, and
`publish_report()` interpolates a schema-valid but path-unsafe `batch.id` into
the destination. The installed command can overwrite an external file through
a symlink, while the stable service can traverse outside `runtime/reports`.
Validate every filename component and publish relative to a verified,
non-symlink directory without a check/use gap. Add direct service and installed
CLI regressions for traversal, pre-existing symlink parents, unchanged external
sentinels, and byte-idempotent valid output. This is a reproduced
security/data-loss risk under P02-T08.

### 7. Workflow command truth is maintained in two documentation inventories

`docs/operations.md` is generated from `render_command_reference()`, but
`docs/state-protocol.md:20-56` contains a second manually maintained verb list.
A comparison test detects drift only after someone edits both surfaces; it does
not make the second list parser-generated. Generate the inventory from the live
parser as part of its owning documentation flow or replace the duplicate with a
link to the generated reference. This violates P02-T10 and the repository's
single command-registry rule.

### 8. Two named acceptance tests do not exercise their claimed contracts

`test_selection_cannot_receive_hold` checks only the `select()` signature and
never populates `hold`; `test_next_phase_agrees_with_effect_table` checks only
membership in a literal set and never compares metadata with the effect's
committed `work.next_phase`. Both pass if the claimed behavior regresses. Add a
path-level hold-exclusion case and compare every accepted row's `next_phase()`
result with its applied full effect. Add focused regressions for roots 1–7 in
their owning suites. This is a required P02-T01/P02-T03 acceptance-evidence
gap, not a coverage-percentage preference.

## Rework bundles

1. **Contract/correctness/security:** roots 1–6 — fail closed on unproven replay,
   fence recovery authority, make lifecycle/report filesystem operations
   path-confined, and repair frontmatter/report contract coverage.
2. **Integration/recovery/portability:** roots 1–3 and 6 — exercise the exact
   durable boundary, competing mutation, no-intent replay, traversal, and
   symlink cases with real temporary filesystems and installed commands.
3. **Tests/docs/maintainability:** roots 4, 5, 7, and 8 — reconcile the state
   crosswalk, migrate report goldens/section behavior, restore parser-owned
   documentation, and replace self-fulfilling tests with behavioral evidence.

## Verdict and next action

Verdict: **changes requested**. The complete deterministic gate passes, but
eight reproduced or directly evidenced contract, safety, architecture, and
required-evidence roots block convergence. PRD 00004 remains in `wip`; no
production code, PRD lifecycle file, project capsule, or autopilot state was
changed in this review session.

The fast-track protocol permits one final consolidated rework/review cycle.
Start fresh `FT-04F2` from this review, the PRD, and clean reviewed HEAD. Fix all
three bundles together, run targeted regressions and the complete gate, commit
the cohesive result, write `rework-02.md`, and stop. A fresh `FT-04R3` must then
run all three isolated lenses over the complete PRD range. If any must-fix root
survives that second rework, stop for a user decision rather than extending the
loop.
