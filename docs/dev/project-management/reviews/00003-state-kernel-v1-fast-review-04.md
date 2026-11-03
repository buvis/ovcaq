---
prd: dev/local/prds/wip/00003-state-kernel-v1.md
session: FT-03R4
review_kind: fast-track
cycle: 4
date: 2026-08-29
base_sha: 9cda04a6a0279a6306c24015ee2d3173fb916e68
head_sha: 7b2e9776b6d03edcdfa2ca758c0c389024a903fe
verdict: pass
decision_required: false
closeout_ready: true
must_fix_root_causes: 0
rework_bundles: 0
reviewers:
  alice: available
  blake: available
  bob: available_via_fallback
---

# Fast review 04: 00003 state kernel v1

Complete updated PRD range reviewed:
`9cda04a6a0279a6306c24015ee2d3173fb916e68..7b2e9776b6d03edcdfa2ca758c0c389024a903fe`.
The range contains 28 changed files and 13,116 additions / 15 deletions. Review
covered the complete implementation range while the exceptional decision
bounded new must-fix scope to the three cycle-03 repairs and regressions. It did
not reopen deferred cycle-03 cleanup.

Exceptional repair commit `7b2e977` changes six files with 429 additions / 10
deletions.

Raw reports:

- `dev/local/reviews/00003-state-kernel-v1-fast-alice-04.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-blake-04.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-bob-04.md`

## Verification at reviewed head

| Check | Result |
|---|---|
| `mise exec -- uv sync --all-groups` | passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest` | passed; 883 tests in 9.57s |
| `mise exec -- uv run ruff check .` | passed |
| `mise exec -- uv run ruff format --check .` | passed; 75 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | passed; 46 source files |
| `mise exec -- uv build` | passed; sdist and wheel built |
| `git diff --check <complete-range>` | passed |
| focused exceptional-repair regression | passed; 33 selected / 118 deselected in 0.30s |
| accepted-plan SHA-256 | exact match: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5` |
| tracked worktree / HEAD after gates | clean / `7b2e9776b6d03edcdfa2ca758c0c389024a903fe` |

The focused matrix selected strict non-standard constants, programmatic integer
limits, accepted-boundary integer round trips, maximum-revision transaction and
restore rollover, non-regular state/backup artifacts, and regular read
`O_NONBLOCK` behavior across `test_schema_limits.py`, `test_store.py`, and
`test_cli_limits.py`.

## Mandatory isolated lenses

| Lens | Verdict | Must-fix claims | Consolidated contribution |
|---|---|---:|---|
| Alice — consensus/architecture | pass | 0 | design detail lag is non-authoritative maintenance |
| Blake — blind/PRD-only | pass | 0 | all three repaired boundaries independently satisfy the PRD |
| Bob — doubt and de-slop, full R1–R5 | pass | 0 | all doubts classified; R1–R5 pass |

Alice, Blake, and the initial Bob context were dispatched concurrently with the
required isolated packets. Alice and Blake completed normally. The initial Bob
context did not return after two completion requests and was interrupted; the
plan-mandated one-time fresh fallback received the same isolated read-only
packet and completed the full doubt plus R1–R5 lens. No lens was omitted.

## Coordinator reconciliation

### Integer serialization closure and revision rollover

Converged. `schema.py` applies the decoder's 640-digit magnitude bound to both
typed fields and recursively validated open JSON values. Transaction and restore
assign the next store-owned revision and validate it before either backup or
state publication. The focused cases cover typed revisions, task IDs, blocker
IDs, open JSON, initialization, transaction preservation, positive/negative
accepted-boundary round trips, and maximum-revision transaction and restore
failure with byte-identical artifacts.

### Non-regular state and backup artifacts

Converged. The store rejects non-regular path metadata before opening, uses
non-following nonblocking read opens, and verifies descriptor/path identity,
regular-file type, and single-link state before reading. The six FIFO/socket/
directory × state/backup cases prove prompt pre-open rejection and correct
state/backup exception classes; a regular read asserts `O_NONBLOCK`.

Alice and Blake noted that no single test forces a regular-to-FIFO substitution
between `lstat` and `open`. This is not a required evidence gap: the individual
preflight, nonblocking-open, and post-open identity/type checks are exercised,
and no reviewer reproduced a blocking or unsafe path.

### Strict JSON constants and error classification

Converged. The sole decoder rejects `NaN`, `Infinity`, and `-Infinity` through
`parse_constant` before schema validation. The focused matrix covers three
decoder cases and all twelve inline/file/durable-state/backup CLI combinations,
including `usage`/1, `state_io`/2, and `invalid_backup`/8 plus byte preservation.

Bob's suggestion for direct store-level programmatic non-finite-float cases is
not a missing contract proof. `test_validate_state_rejects_non_json_metadata_values`
already covers programmatic `nan`, positive infinity, and negative infinity;
all initialize, transaction, and restore publication paths validate before
canonical encoding.

## Deferred and dismissed observations

| Observation | Disposition | Rationale |
|---|---|---|
| Design artifact does not repeat the new integer constant and artifact-open detail | defer | `docs/state-protocol.md` is the authoritative owned protocol and is current; implementation and tests match it. |
| No single deterministic regular-to-FIFO lstat/open race test | defer as optional hardening | Separate tests cover the preflight, `O_NONBLOCK`, and post-open safeguards; no defect or required-evidence gap was reproduced. |
| No direct store test dedicated to programmatic non-finite floats | dismissed | Existing schema coverage checks all three values and every store publication path invokes whole-state validation. |
| Cycle-03 dependency policy, test/doc bulk, inventory structure, and other cleanup | unchanged / out of scope | The exceptional decision explicitly barred reopening deferred cycle-03 cleanup. |

## Acceptance and source-ID audit

| Obligation | Evidence at reviewed head | Status |
|---|---|---|
| P01-T01 schema/crosswalk | 184 machine-parity rows plus strict shared decoder and integer domain | pass |
| P01-T02 total nested validation | complete schema suites plus integer/non-standard-number regressions | pass |
| P01-T03 store/load/init/restore | ordinary, alias, non-regular, interrupt, repair, and error suites | pass |
| P01-T04 directory fsync | six-boundary durability and repair-fsync suites | pass |
| P01-T05 revision/CAS | monotonic, invalid-revision, concurrent CAS, and maximum rollover cases | pass |
| P01-T06 raw backup/create-only init | exact-byte backup/init/restore/race and invalid-artifact cases | pass |
| P01-T07 JSON paths | parser/get/set/append/delete and deep-value preflight suites | pass |
| P01-T08 compound commands | task/attempt/count/contract-card, exact-ID, and oversized programmatic ID/value cases | pass |
| P01-T09 protected generic writes | ancestor/descendant/unsafe suites | pass |
| P01-T10 installed CLI/errors/help | parser/docs/error/installed-wheel plus twelve strict-constant classifications | pass |
| P01-T11 native test port | inventory, portability, packaging, and full native suite | pass |
| P01-T12 real process durability | writer/contention/SIGKILL and real SIGINT suites | pass |

All PRD acceptance criteria and source-ID obligations have passing evidence at
the reviewed head. PRD 00004 can consume the installed state service without a
compatibility shim.

## Verdict and next action

Verdict: **pass**. The exceptional repairs converge at
`7b2e9776b6d03edcdfa2ca758c0c389024a903fe`; there are no unresolved must-fix
findings and no rework bundle. No further rework is authorized or needed.

The contract's next action is a fresh `FT-03F` closeout session. This review
coordinator does not close or move PRD 00003, refresh the project capsule, or
start PRD 00004.

No code, tests, production documentation, PRD lifecycle file, project capsule,
or autopilot state was changed in FT-03R4. Only the cycle-04 raw review,
consolidated review, and review handoff artifacts were written.
