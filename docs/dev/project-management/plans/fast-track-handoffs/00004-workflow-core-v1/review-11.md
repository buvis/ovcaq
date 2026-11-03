# FT-04R11 → FT-04F11 repair handoff

Date: 2026-09-06, Europe/Prague. Fresh full completion review finished:
**CHANGES_REQUESTED — three actionable findings: two High, one Medium.**
Terminal skill accounting: **7 = 3 FIX + 0 VERIFY + 4 KNOWN**.
R10-01 and the R8/R9 repairs pass. No implementation changes occurred in review.

## Verify before changing anything

- Repository: /Users/bob/git/src/github.com/buvis/ovcaq; branch master.
- Expected HEAD: `22d9193a0d00486b09ebea169e7a38a9f858799d`.
- Commit: `fix(workflow): return complete published report text`.
- Timestamp: `2026-09-05T22:53:07+02:00`.
- Git status and stashes must be empty. Stop on branch/HEAD/status mismatch;
  never reset/clean another session's work.
- Only the original checkout and master exist.
- Full implementation base: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`.
- R8 repair base: `8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`.
- Target PRD: `dev/local/prds/wip/00004-workflow-core-v1.md`.

A historical paused PRD-00003 autopilot state **does exist**, with 25 tasks and
mtime 1787864775.0302238. It is unrelated: do not attach, overwrite, create tasks
in, or otherwise mutate it. Its observed SHA-256 is
`ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f`.
PRD-00004 has no attached task store. This corrects the incoming handoff's broad
absence wording without changing the bounded standalone workflow.

## Read first

Global/repository AGENTS.md, WIP PRD, accepted implementation plan (read only),
coverage manifest, discovery 00001 and both characterization TOMLs.
P02-T01–T10, all 55 owned rows and every phase exit remain mandatory.

- [R11 verdict](../../../reviews/00004-workflow-core-v1-fast-review-11.md) and
  [complete evidence companion](../../../reviews/00004-workflow-core-v1-fast-review-11-evidence.md).
- [Fresh source join](../../../reviews/00004-cycle-11-owned-rows.json).
- [Installed reproduction source](../../../reviews/00004_cycle_11_probes.py) and
  [raw results](../../../reviews/00004-cycle-11-probes.json).
- [R11 verification](../../../reviews/00004-cycle-11-verification.json),
  [dispatch](../../../reviews/00004-cycle-11-dispatch.json), and
  [raw consolidation](../../../reviews/00004-cycle-11-consolidation-raw.md).
- [rework-10.md](rework-10.md), [review-10.md](review-10.md),
  [rework-09.md](rework-09.md) and their R9/R8 preservation links.

## Repair 1: R11-01 — validate the complete ledger (High, M)

Source: P02-T06; ART-016, CMD-010, STATE-112/113, TEST-013/014.
Location: `src/ovcaq/workflow/_files.py:311`.

`_deferred_item` validates the standalone item at depth zero; publication adds
two levels (`items[]`) without validating the composed ledger. Installed
depth31/32 append returns 0 but its reader raises ResourceLimitError. Exact
replay and any subsequent append return resource_limit/11. Prior seed bytes
remain within the unusable ledger. Depth30 works; depth33 refuses and preserves
the existing ledger. State bytes are unchanged throughout.

Acceptance:

1. Before production edits, add and run an installed failing regression for
   accepted item depth versus composed ledger depth. Include depth30,31,32,33,
   an existing seed record, exact replay and a later append. Retain raw red output.
2. Validate the complete prospective ledger before publication. A successful
   append must remain readable and replayable by the same supported reader.
   Rejected candidates leave existing ledger and authoritative state bytes
   unchanged. Retain contextual resource_limit JSON/exit11, no traceback.
3. Keep decoder strictness, safe IDs/attribution, exact/conflicting op-ID behavior,
   temporary cleanup, sidecar ownership, directory-inode serialization and
   serialized original-snapshot comparison. Do not relax the reader's limits
   or add a legacy ledger importer/repair API.
4. No new broad schema policy or production module is needed.

## Repair 2: R11-03 — persist created runtime ancestors (High, M)

Source: P02-T06/T09; shared ledger publication used by T07.
Location: `src/ovcaq/workflow/_files.py:233`.

A valid independent `--state` plus a missing configured `new/nested` runtime
root reaches `deferred.mkdir(parents=True)`. Initial defer and exact replay
both return 0, but fsync only `new/nested` and `new/nested/deferred`.
The project directory and `new` are never synced to persist their newly created
children. The fresh probe delegates each observed call to real os.fsync;
it establishes a protocol gap, not simulated power-loss data loss.

Acceptance:

1. Capture an installed fail-first regression with an existing independent state
   file and a previously absent nested configured runtime root.
2. Durably create the complete missing directory chain. Sync each required
   parent before successful return; retain directory and leaf identity guards.
3. Fail at each newly required parent sync, restart/retry with existing partial
   directories, and prove the required syncs are retried before success.
   Exact op-ID replay must also complete interrupted durability work without
   duplicate records or changing authoritative state.
4. Preserve R9's coordinator-only directory serialization, sidecar checks,
   serialized stale-snapshot refusal, named-boundary successful rivals and
   native-interval expected refusal. Do not substitute a pathname check for
   kernel serialization or weaken exclusion of reads.
5. Reuse appropriate existing filesystem helpers where behavior aligns; keep
   ownership explicit and avoid a general rollback or compatibility framework.

## Repair 3: R11-02 — prevent report lost updates (Medium, M)

Source: P02-T08; ART-013, CMD-019, TEST-018/020.
Location: `src/ovcaq/workflow/reports.py:701–706`.

Independent installed A pauses after reading/composing. State switches to B
through StateStore; the installed B console successfully publishes its section.
A resumes and succeeds, replacing B's section with A. Both return exit0. Seed
survives, A text equals its artifact, and a B retry restores all sections.
Thus R10 result equality remains fixed, while an earlier successful publication
is lost under overlap.

Acceptance:

1. Capture a chronological failing regression with real installed processes
   coordinated around read/compose/publication, different active-PRD snapshots,
   and a pre-existing unrelated section. Retain both stdout/stderr/exit results.
2. Serialize the whole report read/compose/publish operation, or reject stale
   publication under a real serialization boundary. A separate unlocked
   compare/check does not close the race. Preserve every successful section;
   if contention refuses, produce a contextual retry result and prove retry.
3. Cover exact replay and competing updates, avoiding deadlock or a hidden
   last-writer-wins loss. State bytes remain unchanged by rendering.
4. Keep R10's compose-once/publish-once complete text return and public Path
   return for existing publish_report callers. No unverified pathname reread,
   duplicate renderer or public API redesign.
5. Preserve root-through-leaf output verification during traversal/publication,
   identical replay and context exit; all report/audit/archive fsyncs, golden
   bytes, Unicode sections, duplicate collapse and summary replacement.

## Verification and preservation

Perform only these bounded repairs in a **fresh work session**. Run all installed
new regressions and full workflow/packaging preservation, full pytest, sync,
Ruff/format, mypy, build, and full-range whitespace. Preserve installed module
origins and capture raw fail-first evidence before product edits. Keep these
review probes unchanged; new post-repair probes must test expected corrected
behavior, since their current exit0 means successful defect observation.

R11 fresh suite: **1339 passed in 23.83s**, zero failures/skips; all remaining
AGENTS.md quality/build gates pass. Alice ran 102 additional overlapping focused
cases, all passing. Wheel and sdist rebuilt identically to R10:

- wheel: `8181a0ca7e3ff1dceb0577fd144347f73021451ca63cd049129a0c7a70739a6b`;
- sdist: `e869f5b37e43df1bdcd425a2be0897f2d69516e1cf04f32a0c203c8b035691ce`.

Plan SHA-256:
`43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
Inventory SHA-256:
`d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9`.

Preserve original saga artifact identities, strict decoding, typed recovery,
terminal drain, conflicting stall refusal, reset owners, nonzero/unknown totals,
equal-key ordering, active-batch metrics, substantive decision filtering
including zero, prompt nonregular refusal, control-character refusal,
provider-neutral guards and parser-derived docs.

**Settled, do not reopen:** initially absent source keeps null artifact and
failure evidence; later unidentified replacements are refused. Blake repeated
this blind objection; it creates no new repair. Returned frontmatter controls
retain their downstream owner. R8-K1/K2 and R9-K3/K4 remain KNOWN. The old
adjudication exit1 remains an obsolete rival-success assertion, retained beside
its installed expected-refusal supplement.

**Dead ends:** no retry of full-base replay (missing packaging_support), external
Bob/Carl nested-wrapper guards, or engram registration/capsule work. R8 bounded
replay remains 56 collected/46 failed/10 preservation passes. R9's 23 / R10's 1
chronological regressions do not establish universal full-base binding.

No importer, aliases, launcher markers, provider/model policy, abort/rollback API,
duplicate frontmatter policy, Linux signoff, unrelated autopilot state,
implementation-plan edit, capsule refresh, PRD closeout or next PRD.

## Next session

After repair commits and gates, retain exact HEAD and evidence, then end the work
session. Run **FT-04R12** only in a new completion-review session over the full
implementation range, all source tasks/55 rows/phase exits, with isolated Alice
consensus, Blake PRD-only and Bob doubt+de-slop, complete R/B/D rubrics.
No native model diversity is claimed.

R11 created no worktree, branch or executed plan. Probe roots/children were
cleaned/reaped; prior evidence and other sessions' material remain. Review
artifacts are intentionally retained under ignored dev/local paths.

Unresolved questions: none.
