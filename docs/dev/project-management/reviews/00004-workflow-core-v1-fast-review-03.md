---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
session: FT-04R3
review_kind: fast-track
cycle: 3
date: 2026-09-02
base_sha: b43bf2c94d5eb0fddafca55542ef2570b45e8d52
head_sha: f2453760591875f1faf241ec9c0291303232efd9
verdict: changes_requested
decision_required: true
closeout_ready: false
final_fast_track_cycle: true
must_fix_root_causes: 2
rework_bundles: 0
reviewers:
  alice: available
  blake: available
  bob: available
---

# Fast review 03: 00004 workflow core v1

Complete PRD range reviewed:
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..f2453760591875f1faf241ec9c0291303232efd9`.
The range contains 36 changed files and 5,349 additions / 15 deletions across
all four PRD commits. Review was not limited to the final rework commit.

Raw reports:

- `dev/local/reviews/00004-workflow-core-v1-fast-alice-03.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-blake-03.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-bob-03.md`

## Verification at reviewed head

| Check | Result |
|---|---|
| `mise exec -- uv sync --all-groups` | passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest` | passed; 1,068 tests in 13.84s |
| `mise exec -- uv run ruff check .` | passed |
| `mise exec -- uv run ruff format --check .` | passed; 92 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | passed; 47 source files |
| `mise exec -- uv build` | passed; sdist and wheel built |
| focused workflow/installed wheel | passed; 186 tests in 2.11s |
| eight-root regression matrix | passed; 18 named tests in 1.54s |
| `git diff --check <complete-range>` | passed |
| accepted-plan SHA-256 | `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5` |
| frozen autopilot-state SHA-256 | `ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f` |
| reviewed HEAD / tracked tree | exact / clean before artifact publication |

The complete gate ran afresh at exact HEAD. No gate failure was waived. The
frozen autopilot state and accepted implementation plan remained byte-identical
to their cycle-02 recorded hashes.

## Mandatory isolated lenses

| Lens | Verdict | Raw claims | Consolidated contribution |
|---|---|---:|---|
| Alice — consensus/architecture | changes requested | 4 | replay durability and recovery-kind ambiguity |
| Blake — blind/PRD-only | changes requested | 4 | recovery-kind ambiguity independently identified |
| Bob — doubt/de-slop, R1–R5 | changes requested | 7 FIX | recovery-kind ambiguity independently identified; R1–R5 all fail |

All three lenses were dispatched concurrently in fresh, isolated contexts.
Alice received AGENTS, the accepted implementation plan, PRD, complete diff,
and fresh gate evidence. Blake received only the PRD, complete diff, and gate
evidence. Bob received AGENTS, PRD, complete diff, and gate evidence. No lens
received prior review/rework material or another lens's output. No lens was
omitted, merged, or retried.

## Closure audit of fast-review-02 roots

All eight exact cycle-02 roots have direct closure evidence at the reviewed
HEAD. This does not make the cycle converge: the complete review found two
additional residual recovery-contract roots below.

| # | Cycle-02 root | Closure evidence | Result |
|---:|---|---|---|
| 1 | No-intent destination presence falsely reports completed replay | `records._completed_operation_id()` now requires a matching batch ledger operation and reset-state evidence. Service tests cover active held refusal and proven replay; `test_installed_stall_rejects_active_held_prd_without_durable_proof` covers the installed command with unchanged state/file bytes. | closed for the reproduced false-success case |
| 2 | Active recovery intent does not fence competing mutations | `require_recovery_idle()` guards frontmatter, phase completion, PRD completion, and public defer. Service tests prove byte/revision preservation; the saga test rejects a competing transition and then reconciles normally. | closed |
| 3 | After-intent lifecycle-directory substitution escapes the tree | Move, verification, and directory sync now use verified directory descriptors with no-follow final-component opens. The exact `AFTER_INTENT_BEFORE_MOVE` symlink-swap regression leaves the external target untouched, the source in WIP, recovery intent present, and work unreset. | closed |
| 4 | Frontmatter lacks active-PRD attribution/crosswalk/cap ownership | Application now binds the supplied basename to committed `work.prd`, removes duplicate derived legacy extensions, and records ownership of an explicit cap 3. Service, public-boundary, and installed-wheel tests prove wrong-PRD refusal and the later `3 -> 2` warning. | closed |
| 5 | Characterized report migration is incomplete | Reports now replace one per-PRD section, retain batch summary totals, archive canonical terminal state, and compare audit/report/metrics against migrated v1 goldens with recorded provenance. CLI coverage proves terminal report archival without deleting live state. | closed |
| 6 | Report publication can traverse or follow an output symlink | Filename components are validated and publication is descriptor-relative, no-follow, atomic, and directory-synced. Service and installed-wheel regressions reject traversal and symlinked report parents while preserving external sentinels; valid rerenders remain byte-idempotent. | closed |
| 7 | Workflow command truth exists in two manual inventories | Both documentation surfaces are emitted from the live parser. The state-protocol inventory is marked generated and its exact parser output is contract-tested; `docs/operations.md` still equals the generated full reference. | closed |
| 8 | Hold exclusion and transition-target tests are self-fulfilling | Hold exclusion now creates a real lifecycle tree with a held-only PRD. Every accepted transition row now compares `next_phase()` to the full effect actually applied. | closed |

The named 18-test closure run included the real temporary-filesystem cases for
roots 1–3 and 6 and the installed-wheel regressions for no-intent replay,
frontmatter attribution/cap ownership, and report traversal/symlink confinement.
All 18 passed.

## Surviving must-fix roots

### 1. Recovery replay skips durability work before advancing state

Severity: **high**. `records._verify_move()` fsyncs the WIP and hold directory
descriptors only when it performs the rename. If a process dies after rename
but before either fsync, replay observes the already-moved file, performs zero
directory fsyncs, and advances the durable operation to `moved`. Likewise,
`record_defer()` returns immediately for an exact existing record; a replay
after replace but before directory fsync performs zero directory syncs before
the saga advances to `recorded`. Creating `hold` or `deferred` also does not
fsync the parent that owns the new directory entry.

Coordinator reproduction in a temporary filesystem instrumented the two replay
paths and observed:

```text
already_moved_replay_fsync_calls 0
exact_record_replay_directory_fsync_calls 0
```

This is a data-loss/durability risk and a direct miss against P02-T07 and the
Phase 2 exit criterion that every interruption boundary recover safely. Replay
must re-establish the required directory durability before advancing state, and
new lifecycle/record directories must durably publish their parent entries.

### 2. Public stall accepts a site value that makes exact replay change kind

Severity: **high**. `workflow stall --site` accepts arbitrary text. Deferred
saga records omit the recovery kind and always store `type: stall`, while
`_completed_operation_id()` infers `park` solely from `site == wrapper_died`.
`_commit_operation()` also uses the site heuristic for the park breaker.

The coordinator reproduced the accepted public-service input in a temporary
filesystem:

```text
first SagaResult(operation_id='op', kind='stall', replayed=False, systemic_halt=False)
second_error RecoveryConflictError held PRD '00004-workflow-core-v1.md' has no durable recovery proof
```

The first call commits successfully; its identical post-commit retry is not
idempotent. Alice, Blake, and Bob identified this same root independently. The
record must persist and match the explicit recovery kind, or `wrapper_died`
must be rejected as a reserved stall site; breaker behavior must use the same
unambiguous authority. Add service and installed-command exact-replay coverage.

## Reconciled and deferred reviewer claims

- Successful WIP-to-done movement, successor activation, and sequencing of
  separate completion/transition commands remain caller/supervisor/launcher
  lifecycle responsibilities under the accepted plan. The Phase 2 table owns
  the state effects; PRD 00004 does not gain a second filesystem saga. This is
  the same settled scope call recorded in fast-review-02.
- Project configuration loading, configured-root containment/precedence, and
  active-agent tier-map injection begin with P03-T01 / PRD 00005 and later
  runtime routing. PRD 00004 supplies the configured lifecycle-path and
  abstract-tier seams; it does not pull the future loader into workflow core.
- Rework-cap pause/enforcement is supervisor decision policy. The accepted
  Phase 2 table requires `review + rework -> review (cycle + 1)`; later runtime
  work owns cap rotation and operator branching.
- A separate installed-wheel behavior matrix for every verb is additional test
  depth, not a current evidence gap: the installed entrypoint/family and module
  provenance are tested, the common dispatch is covered in-process, and the
  risky rework boundaries have dedicated installed-wheel regressions.
- Retaining `work.prd` across per-PRD reset and the duplicated transition target
  metadata match the accepted reset/table contracts. Their integration and
  localized de-slop concerns are non-blocking for this PRD.

## Verdict and mandatory stop

Verdict: **changes requested**. The full deterministic gate passes and all eight
cycle-02 roots have closure evidence, but two high-severity recovery-contract
roots remain after the final permitted fast-track review cycle.

Per the fast-track convergence rule, no additional rework cycle is authorized.
PRD 00004 remains in `wip` and `closeout_ready` is false. Stop for user
direction. This session did not edit production code, mutate autopilot state,
edit either implementation plan, move the PRD, refresh the project capsule, or
begin another PRD.
