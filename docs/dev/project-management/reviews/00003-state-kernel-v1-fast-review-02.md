---
prd: dev/local/prds/wip/00003-state-kernel-v1.md
session: FT-03R2
review_kind: fast-track
cycle: 2
date: 2026-08-28
base_sha: 9cda04a6a0279a6306c24015ee2d3173fb916e68
head_sha: ff00f1f5b848043293ee8d92fbd11d0d38053738
verdict: changes_requested
must_fix_root_causes: 4
rework_bundles: 2
reviewers:
  alice: available
  blake: retry
  bob: available
---

# Fast review 02: 00003 state kernel v1

Complete updated PRD range reviewed:
`9cda04a6a0279a6306c24015ee2d3173fb916e68..ff00f1f5b848043293ee8d92fbd11d0d38053738`.
The range contains 28 changed files and 12,127 additions / 15 deletions. Review
covered the complete implementation range, not only rework commit `ff00f1f`.

Raw reports:

- `dev/local/reviews/00003-state-kernel-v1-fast-alice-02.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-blake-02.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-bob-02.md`

## Verification at reviewed head

| Check | Result |
|---|---|
| `mise exec -- uv sync --all-groups` | passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest` | passed; 789 tests in 9.26s |
| `mise exec -- uv run ruff check .` | passed |
| `mise exec -- uv run ruff format --check .` | passed; 75 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | passed; 46 source files |
| `mise exec -- uv build` | passed; sdist and wheel built |
| `git diff --check <complete-range>` | passed |
| focused cycle-01 convergence matrix | passed; 27 deep-JSON, duplicate-key, and symlink cases in 0.16s |
| accepted-plan SHA-256 | exact match: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5` |
| tracked worktree / HEAD after probes | clean / `ff00f1f5b848043293ee8d92fbd11d0d38053738` |

The cycle-01 fixes converge on their stated cases: deeply nested JSON and
duplicate keys now fail with stable errors, and symlinked derived/runtime/store
artifacts leave external victims unchanged. The passing gate does not exercise
the four newly reproduced boundaries below.

## Mandatory isolated lenses

| Lens | Verdict | Raw must-fix claims | Consolidated contribution |
|---|---|---:|---|
| Alice — consensus/architecture | changes requested | 3 | oversized integer decoding; hard-link isolation; strict task-ID resolution |
| Blake — blind/PRD-only | pass | 0 | independent PRD-only contract check found no additional issue |
| Bob — doubt and de-slop, full R1–R5 | changes requested | 1 | interrupt-safe publication repair |

The first Blake worker remained unavailable after repeated completion requests.
It was interrupted and the lens was dispatched once more in a fresh isolated
subagent with the identical blind packet, as required by the fast-track fallback
rule. The retry completed and its raw report is the cycle-02 Blake artifact.

## Coordinator reconciliation

The coordinator independently reproduced every raw must-fix claim:

- a transaction interrupted with `KeyboardInterrupt` at `BACKUP_REPLACED` left
  state unchanged but replaced the previous backup with current-state bytes;
- initialization interrupted at `STATE_REPLACED` raised while leaving a readable
  revision-zero state committed;
- a size-compliant state containing a 5,000-digit `revision` raised raw
  `ValueError`; the installed CLI classified the durable-state failure as
  `usage`/1, and restore let the same backup decoder error escape;
- a hard-linked lock artifact changed its external victim from 0644 to 0600 and
  was accepted for a successful read;
- both `StateService.start_task(True)` and `start_task(1.0)` matched task ID 1,
  committed `in_progress`, and returned the aliased input as `task_id`.

Blake's pass does not dismiss independently reproduced defects. Alice's
pathname-swap/TOCTOU residual doubt was not reproduced and remains deferred
rather than becoming a must-fix.

## Consolidated must-fix bundles

### Bundle 1 — contract / correctness / security

#### FT03R2-01 — Reject multi-linked store artifacts before use

Severity: high. Found by Alice; reproduced by the coordinator.

Evidence:

- `StateStore._verify_open_artifact()` at `src/ovcaq/state/store.py:467-478`
  verifies regular-file type and path/descriptor inode identity but not
  `st_nlink`.
- `_locked()` then calls `fchmod(0600)` at `src/ovcaq/state/store.py:181-196`.
- Replacing `state.json.lock` with a hard link to a 0644 external victim made
  `StateStore.read()` succeed and changed both names' shared inode to 0600.

Violated contract: the accepted plan's project/runtime containment policy,
PRD `P01-T03` safe locked-store boundary, and the cycle-01 external-victim
postcondition. An artifact with an outside alias also permits mutation outside
the advisory-lock namespace.

Required regression evidence: existing hard-linked state, backup, and lock
artifacts fail closed before reads, permission changes, backup rotation, restore,
or publication; each external alias retains bytes, mode, timestamps, and link
identity. Normal single-link artifacts and atomic replacement continue to pass.

#### FT03R2-02 — Bound JSON integer conversion and normalize every decoder failure

Severity: medium. Found by Alice; reproduced by the coordinator.

Evidence:

- `decode_json()` at `src/ovcaq/state/schema.py:421-427` delegates integer
  conversion to `json.loads()` without an explicit numeric-literal bound.
- `_decode_state()` at `src/ovcaq/state/store.py:274-296` does not translate the
  resulting `ValueError` from Python's integer digit limit.
- Restore wraps only `SchemaError` and `StateError` at
  `src/ovcaq/state/store.py:160-165`.
- A state below `MAX_STATE_BYTES` with a 5,000-digit `revision` raised raw
  `ValueError`; `ovcaq --json state show` reported `usage`/1 rather than a stable
  durable-state class, and the same backup error escaped `BackupError`.

Violated contract: `P01-T02` total validation, `P01-T03` fail-closed reads and
restore, and `P01-T10` stable stdout-safe symbolic errors.

Required regression evidence: explicitly bound integer literals before Python-
version-dependent conversion; oversized numeric literals in durable state,
backup, inline JSON, and JSON files receive documented symbolic/exit classes
with no raw `ValueError`, traceback, or durable mutation. Valid boundary
integers and ordinary schema-invalid integers retain their intended behavior.

#### FT03R2-03 — Require exact non-boolean integer task IDs at the service boundary

Severity: medium. Found by Alice; reproduced by the coordinator.

Evidence:

- `_task_by_id()` at `src/ovcaq/state/commands.py:59-63` uses ordinary equality,
  where `True == 1` and `1.0 == 1`.
- `StateService.start_task(True)` and `start_task(1.0)` both changed task 1 to
  `in_progress` and returned the invalid alias as the result ID.

Violated contract: the documented non-boolean integer identifier contract,
`P01-T08` deterministic task-ID resolution, and the no-shim service boundary
that PRD 00004 must consume.

Required regression evidence: every task-ID-taking service operation rejects
booleans, floats, and other equality aliases before opening a transaction;
state, backup, and revision remain byte-identical. Valid integer IDs retain the
complete add/start/attempt/complete/body/meta/status behavior.

### Bundle 2 — integration / recovery / portability

#### FT03R2-04 — Repair publication on `KeyboardInterrupt` before re-raising

Severity: high. Found by Bob; reproduced by the coordinator.

Evidence:

- `_commit_pair()` and `_publish_bytes()` catch `Exception` only at
  `src/ovcaq/state/store.py:321` and `src/ovcaq/state/store.py:357`.
- `KeyboardInterrupt` derives directly from `BaseException`, so it bypasses both
  repair paths.
- At `BACKUP_REPLACED`, an interrupted transaction preserved state but destroyed
  the previous backup by replacing it with current-state bytes.
- At initialization's `STATE_REPLACED`, `initialize()` raised while leaving a
  valid revision-zero state published, so the command can report interruption
  although retry observes `state_exists`.

Violated contract: failed mutations leave state and backup byte-identical;
create-only initialization is deterministic; every durable boundary is tested;
and the state writer is crash/signal safe.

Required regression evidence: injected `KeyboardInterrupt` across every
applicable initialization, transaction, and restore publication boundary repairs
pre-operation state/backup bytes (or removes an interrupted create-only state),
fsyncs repair, and re-raises the interrupt. Add a representative real-subprocess
SIGINT case so Python signal delivery is not proved only by a synthetic exception.
Existing ordinary-exception and SIGKILL recovery matrices must remain green.

## Deferred, known, and dismissed observations

| Observation | Disposition | Rationale |
|---|---|---|
| Several `derived` crosswalk rows remain too vague to consume deterministically, especially `cap_rotations -> recovery.operation` | defer and clarify before PRD 00004 consumes the crosswalk | Repeated from cycle 01; no current persistence defect reproduces. |
| Pathname-based runtime validation may retain a concurrent parent-component swap/TOCTOU window | defer / unconfirmed | Alice identified a residual doubt but did not reproduce an escape. Speculation alone does not meet must-fix policy. |
| Repeated subprocess harnesses, test-file bulk, trivial declaration-paraphrasing docstrings, and the `subprocess.Popen` invariance test add structural slop | defer | Bob supplied concrete R1/R4/R5 evidence, but these are maintainability issues rather than acceptance failures. |
| Valid empty JSON object keys cannot be addressed through the path grammar | dismissed | The accepted design explicitly rejects empty path keys and whole-object recovery remains available. |
| Restore refuses a corrupt current document before reading a valid backup | known / no action | Explicit accepted store contract, not a current acceptance miss. |
| Reviewer installed-wheel reruns were sandbox-limited | dismissed | The coordinator's canonical same-head suite includes both installed-wheel tests and passed. |
| SIGKILL tests do not prove literal power-loss persistence | known | They prove the PRD's supported process-failure boundary; physical power-loss certification is not in scope. |

## Acceptance and source-ID audit

| Obligation | Evidence at reviewed head | Status |
|---|---|---|
| P01-T01 schema/crosswalk | 184 machine-parity rows and crosswalk tests pass | present; vague derived rows deferred |
| P01-T02 total nested validation | schema/depth/duplicate suites pass | blocked by FT03R2-02 |
| P01-T03 store/load/init/restore | sole store and ordinary repair suites pass | blocked by FT03R2-01, FT03R2-02, FT03R2-04 |
| P01-T04 directory fsync | six-boundary durability and failure translation pass | pass |
| P01-T05 revision/CAS | monotonic, invalid-revision, and concurrent CAS suites pass | pass |
| P01-T06 raw backup/create-only init | normal exact-byte backup/init/restore/race tests pass | blocked by FT03R2-04 |
| P01-T07 JSON paths | parser/get/set/append/delete and deep-value preflight pass | pass |
| P01-T08 compound commands | ordinary task/attempt/count/contract-card suites pass | blocked by FT03R2-03 |
| P01-T09 protected generic writes | ancestor/descendant/unsafe suites pass | pass |
| P01-T10 installed CLI/errors/help | parser/docs/error/installed-wheel suites pass | blocked by FT03R2-02 |
| P01-T11 native test port | inventory, portability, packaging, and full native suites pass | present; structural slop deferred |
| P01-T12 real process durability | writer/contention/SIGKILL boundary suites pass | blocked by missing SIGINT repair evidence in FT03R2-04 |

PRD acceptance is not converged. Sole-writer ownership, the documented schema,
ordinary mutation preservation, concurrency, installed-wheel execution, and the
cycle-01 rework cases pass, but interrupt-safe durability, artifact isolation,
total decoder normalization, and strict service task-ID resolution have
reproduced gaps.

## Verdict and next phase

Verdict: **changes requested**. PRD 00003 remains in `wip`; it must not close or
move at this head. This is the first rework's convergence review, so the fast-
track budget permits one final fresh rework/review cycle. A fresh `FT-03F2`
session should fix both bundles together, add RED/GREEN evidence for all four
root causes, rerun targeted and complete gates, commit, write `rework-02.md`,
and stop. Any code change then requires a fresh cycle-03 Alice/Blake/Bob review
over the complete updated PRD range. If a must-fix survives that second rework,
stop for a user decision rather than extending the loop.
