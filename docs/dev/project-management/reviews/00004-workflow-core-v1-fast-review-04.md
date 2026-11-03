---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
session: FT-04R4
review_kind: fast-track
cycle: 4
date: 2026-09-03
base_sha: b43bf2c94d5eb0fddafca55542ef2570b45e8d52
head_sha: e8fe191089d91140343e6246dffe66caf9caa6a9
verdict: changes_requested
decision_required: true
closeout_ready: false
must_fix_root_causes: 2
rework_bundles: 0
reviewers:
  alice: available
  blake: available
  bob: available_via_fallback
---

# Fast review 04: 00004 workflow core v1

Complete updated PRD range reviewed:
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..e8fe191089d91140343e6246dffe66caf9caa6a9`.
The range contains 36 changed files and 5,669 additions / 15 deletions. Review
covered the complete implementation range, not only the FT-04F3 commit. The
FT-04F3 commit changes three files with 326 additions / 6 deletions.

Raw reports:

- `dev/local/reviews/00004-workflow-core-v1-fast-alice-04.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-blake-04.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-bob-04.md`

## Verification at reviewed head

| Check | Result |
|---|---|
| `mise exec -- uv sync --all-groups` | passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/packaging/test_installed_cli.py -q` | passed; 44 tests in 1.68s |
| `mise exec -- uv run pytest` | passed; 1,076 tests in 10.88s |
| `mise exec -- uv run ruff check .` | passed |
| `mise exec -- uv run ruff format --check .` | passed; 92 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | passed; 47 source files |
| `mise exec -- uv build` | passed; sdist and wheel built |
| `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..e8fe191089d91140343e6246dffe66caf9caa6a9` | passed |
| focused FT-04F3 closure matrix | passed; 8 selected / 36 deselected in 2.37s |
| accepted-plan SHA-256 | exact match: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5` |
| frozen autopilot-state SHA-256 | exact match: `ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f` |
| reviewed HEAD / tracked tree before artifact publication | exact / clean |

All requested gates ran afresh at the exact reviewed head. No gate failure was
waived. The accepted implementation plan and frozen autopilot state remained
byte-identical to the hashes recorded in fast-review-03.

## Mandatory isolated lenses

| Lens | Raw verdict | Raw must-fix claims | Consolidated contribution |
|---|---|---:|---|
| Alice — consensus/architecture | changes requested | 2 | both claims remain in previously deferred next-PRD/tier-map scope |
| Blake — blind/PRD-only | changes requested | 3 | reproduced lifecycle-directory identity loss promoted; completion and fixture-depth claims not promoted |
| Bob — doubt/de-slop, R1–R5 | changes requested | 5 FIX | reproduced competing public state mutation promoted; completion/cap/frontmatter/tasks-done claims not promoted; R1–R4 fail, R5 pass |

Alice, Blake, and the initial Bob context were dispatched concurrently with the
required isolated packets. Alice received AGENTS, the accepted plan and required
inputs, the PRD, complete diff, and fresh gate evidence. Blake received only the
PRD, complete diff, current implementation/tests, and gate evidence. Bob
received AGENTS, the PRD, complete diff, current implementation/tests, and gate
evidence. No lens received fast-review-03, rework-03, implementation rationale,
commit messages, or another lens's output.

The initial Bob context did not return after two completion requests and was
interrupted. The plan-required fresh fallback received the identical isolated
read-only Bob packet and completed all six doubt questions and explicit R1–R5
results. No lens was omitted or merged.

## FT-04F3 closure audit

### 1. Recovery replay re-establishes filesystem durability before state advances

**Closed for the exact FT-04F3 contract.**

- `_open_lifecycle_directory(..., create=True)` creates `hold` and fsyncs the
  lifecycle root that owns the new directory entry before intent is stamped:
  `src/ovcaq/workflow/records.py:409-434`.
- `record_defer()` creates `deferred` and fsyncs its parent before the record is
  used: `src/ovcaq/workflow/records.py:307-359`.
- `_verify_move()` validates terminal placement and then fsyncs both the WIP and
  hold directory descriptors whether it performed the rename or found the PRD
  already moved. Only afterward does `_execute_operation()` advance
  `intent -> moved`: `src/ovcaq/workflow/records.py:452-483,699-710`.
- Exact deferred-record replay fsyncs the record directory before returning;
  only afterward does the saga advance `moved -> recorded`:
  `src/ovcaq/workflow/records.py:345-359,711-736`.
- Controlled interruptions immediately after rename and replace leave recovery
  at `intent` and `moved`, respectively. Replay proves both lifecycle-directory
  syncs and the record-directory sync happen before state advances:
  `tests/workflow/test_sagas.py:399-508`.

The coordinator's eight-test focused closure matrix passed. The new
lifecycle-directory identity finding below does not refute these exact fsync
ordering results; it shows that the descriptors being made durable can cease to
name the configured lifecycle directories.

### 2. Recovery kind is unambiguous

**Closed for the exact FT-04F3 contract.**

- Durable recovery intent stores explicit `kind`, and the deferred ledger now
  persists the same `kind`: `src/ovcaq/workflow/records.py:549-580,722-733`.
- No-intent exact replay matches the stored kind instead of inferring it from
  `site`: `src/ovcaq/workflow/records.py:503-525`.
- Park-breaker increment/pause and stall reset are driven by
  `operation["kind"]`, not `wrapper_died`: `src/ovcaq/workflow/records.py:583-613`.
- Service tests cover exact stall and park replay, the breaker outcomes, and
  both `wrapper_died` cross-kind collisions with unchanged state/ledger bytes:
  `tests/workflow/test_sagas.py:303-397`.
- Installed-wheel tests cover the same two exact retries and both collision
  directions at the public command boundary:
  `tests/packaging/test_installed_cli.py:255-335`.

The focused closure matrix and the complete focused suite passed. No heuristic
kind inference remains in the inspected recovery path.

## Surviving must-fix roots

### 1. Open lifecycle descriptors can stop naming the configured directories

Severity: **high**.

The saga opens WIP and hold descriptors before
`AFTER_INTENT_BEFORE_MOVE`. If `hold` is renamed while its descriptor is open
and the configured pathname is replaced, `_verify_move()` continues through the
still-valid old descriptor. It verifies and fsyncs that relocated directory,
then advances state, writes the record, resets work, and clears recovery without
checking that the descriptor still identifies `paths.hold`.

Blake reproduced the failure. The coordinator independently repeated it in a
temporary real filesystem by renaming `hold` to `relocated-hold` and replacing
the configured `hold` pathname with a directory symlink at the declared
after-intent boundary. Observed:

```text
kind stall
recovery None
wip False
configured_hold False
relocated_hold True
external False
phase build
```

The command reports success and clears durable recovery while the PRD is absent
from both configured lifecycle locations. This is a lost-work/location defect
against P02-T07, the verified-move contract, and the Phase 2 recoverability exit
criterion. It is concrete new evidence that the cycle-02 after-intent directory
substitution closure covered unlink/symlink replacement but not rename-away of
an already-open directory.

Required repair: bind use-time move verification to the configured lifecycle
directory identities and fail closed without clearing recovery if either name
no longer refers to the verified directory. Add deterministic regressions for
rename-away/replacement of both WIP and hold at the after-intent boundary and
prove the PRD remains recoverable and no external target is mutated.

### 2. Public state mutations can commit during recovery and be erased by replay

Severity: **high**.

The workflow application methods fence active recovery, but ordinary public
`StateService` mutation transactions do not. Bob interrupted stall after durable
intent, successfully added a task through `StateService.add_task()`, then
replayed the saga. The replay's `reset_prd_fields()` erased both tasks and
cleared recovery.

The coordinator independently reproduced the same sequence in a temporary
state tree:

```text
mutation_revision 2
before_replay ['original', 'concurrent']
after_replay []
recovery None
```

This is silent loss of a valid state-store commit. It invalidates the broad
cycle-03 closure statement that active recovery fences competing mutations and
violates P02-T07's no-lost-work recovery requirement.

Required repair: ensure every public mutation that could be overwritten by
recovery either rejects active recovery inside its state transaction or causes
the saga to fail closed on an intervening revision without discarding the
mutation. Preserve state-layer dependency direction. Add service and installed
command regressions that interrupt after intent, reject or preserve task,
contract, and allowed generic mutations, then reconcile without data loss.

## Reconciled and deferred reviewer claims

- Successful WIP-to-done movement, successor activation, retained `work.prd`,
  and the sequencing of completion/transition commands remain the already
  settled caller/supervisor/launcher responsibilities. The accepted Phase 2
  table owns state effects, and the user explicitly barred broadening successful
  PRD-move or next-PRD scope. Alice, Blake, and Bob's related claims are not
  promoted.
- Project configuration loading, configured-root containment/precedence, and
  active-agent tier-map injection begin with P03-T01 / PRD 00005 and later
  runtime routing. The current pure seams remain the Phase 2 deliverable; no
  configuration or tier-map claim is promoted.
- Rework-cap pause/enforcement is supervisor decision policy. The accepted
  Phase 2 row remains `review + rework -> review (cycle + 1)`; Bob's cap claim
  is not promoted.
- Frontmatter returns catchup/design/gate/ambiguity choices in its structured
  application result. The state-protocol crosswalk describes canonical mapping
  of legacy state, not a requirement to synthesize completed catchup or pause
  state merely from frontmatter. Runtime consumption is later integration
  scope, so Bob's persistence claim is not promoted.
- `tasks_done` is the explicit structured outcome accepted by the closed
  transition table. The source contract requires row rejection and full
  effects, not a second task-completion validator inside that row. Bob's
  additional precondition is hardening, not a current acceptance miss.
- The checked-in legacy state fixtures cover the retained resume outcomes;
  transition full effects/rejections and migrated report equivalence have
  separate direct and golden tests. The FT-04F3 commit changed only recovery
  code/tests, so Blake supplied no new evidence invalidating the prior fixture
  coverage disposition.
- A full installed-wheel behavior matrix for every verb, dependency-aware task
  selection, report-writer locking, a stricter import-test allowlist, direct
  process-kill saga coverage, and the localized R1–R4 de-slop items remain
  non-blocking additional depth or later-runtime work. R5 passed.

## Acceptance and source-ID audit

| Obligation | Evidence at reviewed head | Status |
|---|---|---|
| P02-T01 selection/lifecycle paths | ordering, hold exclusion, invalid-artifact and resolver suites | pass within settled configuration scope |
| P02-T02 frontmatter | parsing/default/warning/attribution/cap-owner tests | pass within settled tier-map scope |
| P02-T03 transition table | every accepted/rejected row and complete effect comparison | pass |
| P02-T04 resume/plan policy | resume matrix, recovery priority, plan shape/ceiling tests | pass |
| P02-T05 reset/completion summary | owner-preservation, CAS, summary/idempotency tests | pass within settled next-PRD scope |
| P02-T06 defer ledger | operation-ID, conflict, atomic publication and replay tests | pass |
| P02-T07 stall/park saga | FT-04F3 fsync/kind closures pass; directory identity and state-mutation fencing fail | **fail** |
| P02-T08 reports | migrated goldens, idempotent section update, confinement/final archive tests | pass |
| P02-T09 legacy-root replacement | forbidden-string/runtime-root guards | pass within settled configuration scope |
| P02-T10 generated docs | parser/reference/protocol inventory equality tests | pass |

Four PRD acceptance criteria retain passing evidence. `Park/stall/defer recover
at all durable boundaries` and stable consumption by PRD 00005 remain blocked
by the two reproduced recovery roots.

## Verdict and mandatory stop

Verdict: **changes requested**. Both FT-04F3 roots close for their exact
requested contracts and every deterministic gate passes, but the complete-range
review reproduced two high-severity recovery defects. PRD 00004 is not ready
for closeout.

No further repair/review cycle is authorized by this review-only session.
`decision_required` is true, `closeout_ready` is false, and no rework bundle was
created. PRD 00004 remains in `wip`. Stop for user direction; do not edit code or
tests, mutate autopilot state, edit either implementation plan, move/close the
PRD, refresh the capsule, or begin another PRD.
