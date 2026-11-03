---
prd: dev/local/prds/wip/00003-state-kernel-v1.md
session: FT-03R3
review_kind: fast-track
cycle: 3
date: 2026-08-28
base_sha: 9cda04a6a0279a6306c24015ee2d3173fb916e68
head_sha: 296e757cb96007a8c2079b0c4015f836b4fe4c2b
verdict: changes_requested
decision_required: true
must_fix_root_causes: 3
rework_bundles: 0
reviewers:
  alice: available
  blake: available
  bob: available
---

# Fast review 03: 00003 state kernel v1

Complete updated PRD range reviewed:
`9cda04a6a0279a6306c24015ee2d3173fb916e68..296e757cb96007a8c2079b0c4015f836b4fe4c2b`.
The range contains 28 changed files and 12,697 additions / 15 deletions. Review
covered the complete implementation range, not only final rework commit
`296e757`.

Raw reports:

- `dev/local/reviews/00003-state-kernel-v1-fast-alice-03.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-blake-03.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-bob-03.md`

## Verification at reviewed head

| Check | Result |
|---|---|
| `mise exec -- uv sync --all-groups` | passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest` | passed; 850 tests in 9.28s |
| `mise exec -- uv run ruff check .` | passed |
| `mise exec -- uv run ruff format --check .` | passed; 75 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | passed; 46 source files |
| `mise exec -- uv build` | passed; sdist and wheel built |
| `git diff --check <complete-range>` | passed |
| focused hard-link regression | passed; 4 tests in 0.13s |
| focused integer-limit/error-normalization regression | passed; 9 tests in 0.76s |
| focused exact task-ID regression | passed; 32 tests in 0.16s |
| focused injected `KeyboardInterrupt` regression | passed; 15 tests in 0.06s |
| focused real-subprocess SIGINT regression | passed; 1 test in 0.04s |
| full installed-CLI regression | passed; 3 tests in 1.17s |
| accepted-plan SHA-256 | exact match: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5` |
| tracked worktree / HEAD after gates | clean / `296e757cb96007a8c2079b0c4015f836b4fe4c2b` |

The final-rework regressions converge on their named cases: state, backup, and
lock hard links fail without changing aliases; textual oversized integers have
stable errors; aliased task IDs fail before transaction; injected interrupts
repair all applicable boundaries; real SIGINT repairs the replaced backup; and
the installed wheel normalizes oversized durable integer input. The three
reproduced defects below exercise adjacent boundaries absent from those tests.

## Mandatory isolated lenses

| Lens | Verdict | Raw must-fix claims | Consolidated contribution |
|---|---|---:|---|
| Alice — consensus/architecture | pass | 0 | no additional issue |
| Blake — blind/PRD-only | changes requested | 2 | blocking special-file reads; non-standard JSON error normalization |
| Bob — doubt and de-slop, full R1–R5 | changes requested | 1 | programmatic integer / serialization closure |

All three lenses completed concurrently in isolated contexts. Alice received
AGENTS.md, the accepted plan, PRD, design, complete diff, and verification
evidence. Blake received only the PRD, complete diff, and verification evidence.
Bob received AGENTS.md, the PRD, complete diff, and verification evidence and
completed all doubt questions plus explicit R1–R5 verdicts. No retry or fallback
was required.

Alice's pass does not dismiss independently reproduced defects from the other
two mandatory lenses.

## Coordinator reconciliation

The coordinator independently reproduced all three raw must-fix root causes at
the exact reviewed head without changing repository files:

1. `new_state()` with `work.extensions["tests/bigint"] = 10**640` passed
   `StateStore.initialize()` and wrote 1,749 bytes, but the immediate `read()`
   failed with `StateResourceLimitError: state: JSON integer literal exceeds 640
   digits`. The same value committed through `transaction()` at revision 1 and
   made the resulting state unreadable while leaving the revision-zero backup
   readable.
2. A readable state whose revision was a 640-digit all-nines integer passed
   `read()`. A no-op transaction incremented it to a 641-digit revision and
   returned success; the immediate reread failed with the same resource-limit
   error. The store can therefore generate the invalid publication itself.
3. Replacing `state.json` with a FIFO caused a child `StateStore.read()` to
   exceed a 0.5-second timeout. `_read_bytes()` opens the path in blocking mode
   before `_verify_open_artifact()` can reject the non-regular descriptor. The
   same `_read_bytes()` path serves backup reads.
4. Inline `NaN` returned exit 1 / symbolic `invalid_state` with empty stdout,
   rather than documented `usage`. A complete otherwise-valid durable state
   containing `NaN` returned exit 1 / `invalid_state`, rather than documented
   `state_io`. Python's default `json.loads()` accepts `NaN`, `Infinity`, and
   `-Infinity` unless `parse_constant` rejects them.

These are three root causes: items 1–2 are one validation/serialization-closure
defect; item 3 is non-regular artifact preflight ordering; item 4 is strict JSON
decoder/error normalization.

## Reproduced must-fix findings

### FT03R3-01 — Enforce integer serialization closure before publication

Severity: high. Found by Bob; reproduced by the coordinator.

Evidence:

- `decode_json()` at `src/ovcaq/state/schema.py:422-429` rejects integer text
  longer than 640 digits.
- `_require_integer()` and `_validate_json()` accept programmatic integers
  without the corresponding digit bound at `src/ovcaq/state/schema.py:483-486`
  and `src/ovcaq/state/schema.py:515-521`.
- Initialization, service/generic mutations, and store-generated revision
  rollover can publish a value the next `read()` rejects.

Violated contract: total validation before mutation/publication, a validated
crash-safe sole writer, readable/recoverable committed state, and Phase B's
requirement that no tested failure publishes invalid state.

Required evidence if rework is explicitly authorized: programmatic oversized
typed integers, task/blocker IDs, and open JSON values fail before durable
change; a maximum accepted revision cannot roll over into unreadable bytes; and
every accepted state round-trips through canonical serialization and
`decode_json()`.

### FT03R3-02 — Reject non-regular artifacts before blocking open

Severity: high. Found by Blake; reproduced by the coordinator.

Evidence:

- `_reject_aliased_artifact()` at `src/ovcaq/state/store.py:454-466` rejects
  symlinks and multi-linked regular files but does not reject FIFOs or other
  special files.
- `_read_bytes()` at `src/ovcaq/state/store.py:227-239` calls blocking
  `os.open(path, O_RDONLY)` before `_verify_open_artifact()` checks whether the
  descriptor is regular.
- A FIFO at `state.json` blocked beyond 0.5 seconds instead of failing closed.

Violated contract: deterministic behavior under invalid input, fail-closed
reads/restores, and safe state/backup artifact handling. A workspace-local
special file can indefinitely deny state service.

Required evidence if rework is explicitly authorized: state and backup FIFOs,
sockets, devices where safely constructible, and directories fail promptly with
the documented state/backup error without opening a blocking path; regular
single-link artifacts retain current behavior.

### FT03R3-03 — Reject non-standard JSON constants at the decoder boundary

Severity: medium. Found by Blake; reproduced by the coordinator.

Evidence:

- `decode_json()` at `src/ovcaq/state/schema.py:431` calls Python
  `json.loads()` without `parse_constant`, so `NaN`, `Infinity`, and
  `-Infinity` reach schema validation as floats rather than failing JSON syntax.
- Inline `NaN` is reported as `invalid_state`; the protocol documents malformed
  inline/file JSON as `usage`.
- Durable `NaN` is reported as `invalid_state`/1; the protocol documents
  malformed durable JSON as `state_io`/2.

Violated contract: finite JSON validation and stable stdout-safe symbolic error
classification across command, state, and backup decoding.

Required evidence if rework is explicitly authorized: all three non-standard
constants are rejected for inline payloads, JSON files, durable state, and
backup with their documented symbolic/exit classes and no durable mutation.

## Deferred, known, and dismissed observations

| Observation | Disposition | Rationale |
|---|---|---|
| Task dependency cycles validate | known / defer to PRD 00004 | PRD 00003 enforces target existence, uniqueness, and no self-reference; workflow transition policy is explicitly out of scope. |
| Real SIGKILL is not repeated separately for restore | defer | Restore uses the shared paired-publication path and has exhaustive injected-boundary coverage; current PRD requires representative real process evidence, which exists. |
| Crosswalk `derived` wording remains vague in some rows | defer | Repeated observation with no reproduced current persistence defect; clarify before a consumer needs the ambiguous derivation. |
| Runtime parent-component pathname TOCTOU remains unconfirmed | defer | No reviewer reproduced an escape; speculation does not meet the must-fix threshold. |
| Test bulk, annotation mirrors, packaging inventory checks, redundant task-ID guard, and paraphrasing docstrings | defer | Bob supplied concrete R1/R2/R4/R5 evidence, but these are maintainability cleanup rather than a PRD acceptance failure. |
| Cyclic in-memory JSON might hang validation | dismissed | Bob's probe promptly returned the bounded-depth `ResourceLimitError`. |
| Final-rework hard-link repair may be incomplete | dismissed | Coordinator and Bob focused tests passed all four named cases; Alice inspected the implementation. |

## Acceptance and source-ID audit

| Obligation | Evidence at reviewed head | Status |
|---|---|---|
| P01-T01 schema/crosswalk | 184 machine-parity rows and crosswalk tests pass | present; vague derived wording deferred |
| P01-T02 total nested validation | schema, bounds, depth, duplicate, and textual-integer suites pass | blocked by FT03R3-01 and FT03R3-03 |
| P01-T03 store/load/init/restore | ordinary repair, alias, interrupt, and error suites pass | blocked by FT03R3-01 and FT03R3-02 |
| P01-T04 directory fsync | six-boundary durability and repair-fsync suites pass | pass |
| P01-T05 revision/CAS | monotonic, invalid-revision, and concurrent CAS suites pass | blocked by reproduced 640-to-641-digit rollover in FT03R3-01 |
| P01-T06 raw backup/create-only init | exact-byte backup/init/restore/race suites pass | blocked by unreadable accepted initialization in FT03R3-01 |
| P01-T07 JSON paths | parser/get/set/append/delete and deep-value preflight pass | pass |
| P01-T08 compound commands | task/attempt/count/contract-card and exact-ID suites pass | blocked by programmatic oversized ID/value path in FT03R3-01 |
| P01-T09 protected generic writes | ancestor/descendant/unsafe suites pass | pass |
| P01-T10 installed CLI/errors/help | parser/docs/error/installed-wheel suites pass | blocked by FT03R3-03 symbolic classification |
| P01-T11 native test port | inventory, portability, packaging, and full native suites pass | present; structural slop deferred |
| P01-T12 real process durability | writer/contention/SIGKILL and real SIGINT suites pass | pass |

PRD acceptance is not converged. The final-rework targets pass, but total
validation, fail-closed invalid-artifact handling, and stable JSON error
classification have reproduced gaps. PRD 00004 cannot safely consume a service
that can publish a state its own reader rejects.

## Verdict and decision gate

Verdict: **changes requested; user decision required**. PRD 00003 remains in
`wip` and must not close or move at this head.

This was the final allowed rework/review cycle. Three must-fix root causes were
reproduced after the second rework. Per the fast-track convergence rule, the
coordinator creates no third rework bundle and does not start rework. Further
implementation requires explicit user direction that overrides or revises the
cycle budget/contract. Closeout is not the next phase under the current rules.

No code, tests, production documentation, PRD lifecycle file, project capsule,
or autopilot state was changed in FT-03R3.
