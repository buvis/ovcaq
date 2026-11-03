---
prd: dev/local/prds/wip/00003-state-kernel-v1.md
session: FT-03R
review_kind: fast-track
cycle: 1
date: 2026-08-28
base_sha: 9cda04a6a0279a6306c24015ee2d3173fb916e68
head_sha: 9872123ac9be6433f95ad4fb5606ac48cb402fce
verdict: changes_requested
must_fix_root_causes: 3
rework_bundles: 1
reviewers:
  alice: available
  blake: available
  bob: available
---

# Fast review 01: 00003 state kernel v1

Complete PRD range reviewed:
`9cda04a6a0279a6306c24015ee2d3173fb916e68..9872123ac9be6433f95ad4fb5606ac48cb402fce`.
The range contains 28 changed files and 11,368 additions / 15 deletions. All
three mandatory isolated lenses completed without a retry.

Raw reports:

- `dev/local/reviews/00003-state-kernel-v1-fast-alice-01.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-blake-01.md`
- `dev/local/reviews/00003-state-kernel-v1-fast-bob-01.md`

## Verification at reviewed head

| Check | Result |
|---|---|
| `mise exec -- uv sync --all-groups` | passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest` | passed; 762 tests in 8.65s |
| `mise exec -- uv run ruff check .` | passed |
| `mise exec -- uv run ruff format --check .` | passed; 75 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | passed; 46 source files |
| `mise exec -- uv build` | passed; sdist and wheel built |
| `git diff --check <range>` | passed |
| accepted-plan SHA-256 | exact match: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5` |
| tracked worktree / HEAD after probes | clean / `9872123ac9be6433f95ad4fb5606ac48cb402fce` |

Alice's independent installed-wheel rerun was blocked by her subagent sandbox,
not by the implementation. The coordinator's canonical full suite, including
the installed-wheel tests, passed at the same head, so this is not a finding.

## Lens verdicts

| Lens | Verdict | Raw must-fix claims | Consolidated contribution |
|---|---|---:|---|
| Alice — consensus/architecture | changes requested | 1 | path containment / symlink safety |
| Blake — blind/PRD-only | changes requested | 1 | bounded deep-JSON failure handling |
| Bob — doubt and de-slop R1–R5 | changes requested | 4 | confirmed both above; split containment evidence; duplicate-key rejection |

## Consolidated must-fix bundle

Only bundle 1 is needed: **contract / correctness / security**. Bob's runtime-
directory and lock-sidecar reports are two manifestations of Alice's single
path-containment root cause, so they remain separate acceptance cases inside one
finding rather than becoming duplicate rework tasks.

### FT03R-01 — Keep derived runtime/store paths contained and reject symlink escapes

Severity: high. Found by Alice and Bob.

Evidence:

- `runtime_directory()` only joins strings at `src/ovcaq/paths.py:28-33`.
- `ovcaq init` calls `mkdir(..., exist_ok=True)` and `chmod(0700)` at
  `src/ovcaq/cli.py:215-219` without rejecting an existing directory symlink.
- `StateStore._locked()` opens and `fchmod(0600)`s the lock path at
  `src/ovcaq/state/store.py:175-185` without rejecting a symlink.
- Coordinator reproduction: with `dev/local/ovcaq` symlinked to an external
  directory, `ovcaq init` returned 0, changed the external directory from 0755
  to 0700, and created its `state.json`.
- Coordinator reproduction: with `state.json.lock` symlinked to a 0644 victim,
  `StateStore.read()` changed the victim to 0600.

Violated contract: accepted implementation plan lines 975–977 require configured
project/runtime paths to remain under the resolved project unless an external
state root is explicitly supplied. The PRD also requires a safe locked store and
project initialization of its own runtime tree.

Required regression evidence: directory-symlink and lock-symlink cases fail
closed with stable errors, do not chmod/write outside the project, and leave
victim bytes and metadata unchanged. Validate all derived runtime/store paths at
the boundary rather than fixing only the two reproduced spellings.

### FT03R-02 — Bound deep JSON before recursive decoding/copying and normalize failures

Severity: high. Found independently by Blake and Bob.

Evidence:

- `src/ovcaq/cli.py:169-181` parses JSON before OVCAQ's explicit depth validator;
  `src/ovcaq/state/commands.py:321` recursively copies a generic value before a
  transaction can validate it.
- `src/ovcaq/state/store.py:237-252` does not translate decoder recursion failure.
- Coordinator reproduction: a size-compliant 4,000-byte nested inline array
  passed to JSON `state set` raised raw `RecursionError` instead of returning a
  symbolic JSON failure.
- Coordinator reproduction: a 200,000-byte nested persisted value made
  `_decode_state()` raise raw `RecursionError`.

Violated contract: PRD lines 23–25, 54–57, 69–71, and 82–85 require deterministic
invalid-input behavior, total validation, fail-closed reads, explicit limits,
and stable stdout-safe symbolic errors.

Required regression evidence: deeply nested inline/file payloads and raw
state/backup bytes below their byte limits are rejected before unbounded
recursive work, return the documented symbolic error/exit class with no
traceback, and cannot mutate state or backup.

### FT03R-03 — Reject duplicate JSON object keys before closed-schema validation

Severity: medium. Found by Bob.

Evidence:

- Both `json.loads` calls at `src/ovcaq/cli.py:169-181` and
  `src/ovcaq/state/store.py:237-252` use default last-value-wins object parsing.
- Coordinator reproduction wrote an otherwise valid v1 state containing
  `"revision": 999, "revision": 0`; `StateStore.read()` accepted it and returned
  revision 0.

Violated contract: PRD lines 30–31 and 54–57 require malformed/corrupt state to
be rejected before mutation and total validation of the complete object.
Collapsing duplicate owned fields before validation destroys the evidence needed
to enforce that contract.

Required regression evidence: duplicate keys at the root and nested owned/open
objects are rejected consistently for durable state, backup, inline JSON, and
JSON files with stable errors and no durable changes.

## Deferred, known, and dismissed observations

| Observation | Disposition | Rationale |
|---|---|---|
| Several `derived` crosswalk rows are too vague to implement deterministically, especially `cap_rotations -> recovery.operation` | defer and clarify before PRD 00004 consumes the crosswalk | No current persistence defect reproduces, but the next workflow phase must not guess at the mapping. |
| Empty JSON object keys cannot be addressed through the path grammar | dismissed | The accepted design explicitly says empty keys fail; the PRD does not promise addressability for every open-map key, and whole-object recovery remains available. |
| Restore refuses a corrupt current document before reading a valid backup | known / no action | This ordering is explicit in the accepted design and protocol; it is not a current acceptance miss. |
| Repeated path matrices, neutral-process tests, and self-confirming port inventory add test bloat | defer | Functional, durability, and installed-wheel tests supply independent behavior evidence. This is maintainability cleanup, not a violated must-fix threshold. |
| Exact legacy-suite port completeness was not independently re-read by blind/Bob packets | dismissed as a review-packet limitation | Isolation intentionally withheld implementation rationale and external legacy sources; committed inventories plus passing native behavior/packaging suites remain the current P01-T11 evidence. |

## Acceptance and source-ID audit

| Obligation | Evidence at reviewed head | Status |
|---|---|---|
| P01-T01 schema/crosswalk | protocol has 184 machine-parity rows; crosswalk tests pass | present; vague derived rows deferred |
| P01-T02 total nested validation | schema constraint/invariant/limit suites pass | blocked by FT03R-02 and FT03R-03 |
| P01-T03 store/load/init/restore | sole store implementation and transaction/restore suites pass | blocked by FT03R-01 and FT03R-03 |
| P01-T04 directory fsync | six-boundary durability tests and failure translation pass | pass |
| P01-T05 revision/CAS | monotonic, invalid-revision, and concurrent CAS tests pass | pass |
| P01-T06 raw backup/create-only init | exact-byte backup, restore, race, and retry tests pass | pass |
| P01-T07 JSON paths | parser/get/set/append/delete matrix passes | pass |
| P01-T08 compound commands | task-ID/attempt/count/contract-card service tests pass | pass |
| P01-T09 protected generic writes | ancestor/descendant/unsafe tests pass | pass |
| P01-T10 installed CLI/errors/help | parser/docs/error/installed-wheel tests pass | blocked by FT03R-01, FT03R-02, FT03R-03 |
| P01-T11 native test port | inventory, portability, packaging, and full native suites pass | present; structural test observations deferred |
| P01-T12 real process durability | two-writer, reader/writer, repair, and six SIGKILL boundary tests pass | pass |

PRD acceptance is not converged: all-state-write ownership, ordinary failed-
mutation byte preservation, concurrency/durability, installed-wheel execution,
and the no-shim service surface have passing evidence, but total invalid-input
validation, stable error handling, and project-path containment have reproduced
must-fix gaps.

## Verdict and next phase

Verdict: **changes requested**. PRD 00003 remains in `wip`; it must not close at
this head. A fresh FT-03F rework session should fix all three root causes in the
single consolidated contract/correctness/security bundle, run targeted RED/GREEN
coverage and the complete gate, commit, write `rework-01.md`, and stop. Because
that session changes code, a later fresh review coordinator must rerun Alice,
Blake, and Bob over the complete updated PRD range before closeout.
