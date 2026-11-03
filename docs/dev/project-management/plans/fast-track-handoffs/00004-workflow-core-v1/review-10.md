# FT-04R10 → FT-04F10 repair handoff

Date: 2026-09-05, Europe/Prague. Fresh completion review finished:
**CHANGES_REQUESTED, one actionable Medium finding**. All five R9 repairs pass.
Terminal skill count: 5 = 1 FIX + 0 VERIFY + 4 inherited/methodological KNOWN.

## Verify before changing anything

- Repository: `/Users/bob/git/src/github.com/buvis/ovcaq`, branch `master`.
- Expected HEAD: `72562f6fd12fb039e91e4c7b1be29758d1901ec8`.
- Commit: `fix(workflow): serialize ledger publication and verify output paths`.
- Timestamp: `2026-09-05T22:20:36+02:00`.
- Git status must be empty. Stop on mismatch; never reset/clean others' work.
- Full implementation base: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`.
- R8 repair base: `8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`.
- PRD remains `dev/local/prds/wip/00004-workflow-core-v1.md`.

No source/test/doc/PRD changes or commit occurred in FT-04R10. This handoff
reports bounded follow-up work; no task store or unrelated autopilot state was
created. Keep implementation and completion review in separate fresh sessions.

## Read first

Read global/repository AGENTS.md, the WIP PRD, accepted implementation plan
(read only), coverage manifest, discovery 00001 and both characterization TOMLs.
Preserve P02-T01–T10, all 55 owned rows and every phase exit.

- [R10 verdict](../../../reviews/00004-workflow-core-v1-fast-review-10.md) and
  [full source/evidence companion](../../../reviews/00004-workflow-core-v1-fast-review-10-evidence.md).
- [Fresh join](../../../reviews/00004-cycle-10-owned-rows.json),
  [installed reproduction](../../../reviews/00004-cycle-10-report-probe.py),
  [compared texts/results](../../../reviews/00004-cycle-10-report-probe.json).
- R9 verdict/evidence and review-09.md/rework-09.md remain authoritative for
  their repairs and settled scope, along with rework08/probes/sizes.

## One bounded repair

**R10-01 (Medium, M) — return the actual updated report text.**
P02-T08; CMD-019 and TEST-018; `src/ovcaq/workflow_cli.py:161`.

The installed report command independently computes fresh `render_report` text
and publishes `_updated_report(existing, ...)`. After A→B, JSON `text` omits A,
while the returned `path` contains A+B. Exact rerender repeats this mismatch.
The full report and authoritative state bytes survive. Existing installed
first-publication tests assert `text == file` but do not cover this update.

Acceptance:

1. Capture an installed failing regression before production edits. Cover
   A→B→A within one batch, with meaningful changes to current sections and exact
   rerender. `text` equals the actual artifact bytes decoded as UTF-8 each time.
2. Compose/publish once and return the same complete verified content. Preserve
   prior PRD and unrelated sections, duplicate collapse, summary replacement,
   golden bytes and unchanged state. Avoid a separate unverified pathname
   reread, duplicate renderer, or public API redesign.
3. Keep root-through-leaf identity verification during traversal, native
   publication, identical replay and successful context exit. Retain every
   report/audit/archive fsync, configured-path refusal/retry and nonregular test.
4. Preserve all existing signatures/callers where practical; if a bounded
   internal return value is needed, update callers coherently. Do not introduce
   an abstraction solely to transport two known values.
5. Run complete workflow/packaging tests, full pytest, sync, Ruff/format, mypy,
   build and full-range whitespace. Preserve installed module-origin checks.
   The new installed reproduction should become equality-preserving; report
   its observed result accurately rather than treating old discrepancy output
   as a pass.

## Preservation and settled decisions

R9-01–R9-05 all verified. Keep the coordinator-only ledger root despite zero
prior votes: opened-directory kernel serialization, reads excluded from native
replacement, serialized original-snapshot comparison, sidecar ownership,
restored-sidecar refusal, named-boundary successful rivals and exact retries.
Fresh installed rival at native publication returns state_io JSON/exit 2 with
no traceback, and retries preserve seed/first/second once each. Original old
adjudication harness still exits 1 on obsolete rival-success assertion; never
claim that raw run passes. Preserve both raw and expected-refusal evidence.

Retain original saga artifact identities, lifecycle/ledger publication fences,
strict decoding, typed recovery kind, terminal drain, conflicting stall refusal,
nonzero and unknown totals, equal-key ordering, active-batch metrics, substantive
decision filtering including zero, control-character refusal, provider neutrality
and parser-derived docs. No R8 named test was rewritten by R9 or R10 review.

R8-K1 collision OR and R8-K2 add_task/unchanged packaging sizes remain KNOWN;
R9-K3 schema size and R9-K4 replay limitation remain KNOWN. Full-base replay
stays skipped on missing packaging_support and must not be retried/bypassed.
The R8 bounded replay remains 56 collected, 46 failed, ten valid preservation
passes; it is not chronological installed TDD. R9's 23 fail-first cases do not
establish universal implementation-base binding.

Initially missing source retains null artifact and failure evidence; later
unidentified replacements remain refused. Do not add abort/rollback API or
duplicate frontmatter policy. Returned controls retain their downstream owner.
No importer, aliases, launcher markers, provider/model policy, Linux signoff,
unrelated autopilot state, plan edit, capsule refresh, PRD closeout or next PRD.

## Verified state and next review

FT-04R10 fresh full suite: **1338 passed in 22.44s**, zero failures/skips.
Workflow/packaging: **450 passed in 11.21s**. All other AGENTS.md gates pass.
Alice ran 67 additional overlapping focused cases plus independent probes.
Darwin/Python 3.13.13/pytest 9.1.1; Linux retains its downstream owner.
Plan SHA-256 remains `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
Inventory SHA-256 remains `d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9`.

After the bounded work, retain exact HEAD/checks and hand off. Run FT-04R11 only
in a fresh review session, reviewing the full implementation range with isolated
Alice consensus, Blake PRD-only and Bob doubt plus de-slop, full consensus/blind
rubrics and D1–D5 (installed names for requested doubt R1–R5). Do not retry
external Bob/Carl nested-wrapper guards or claim native model diversity.

Only original checkout is registered; Git status/stashes empty. No worktree,
branch or executed plan was created. Probe roots/children were cleaned/reaped;
older evidence and other sessions' files are retained. New review evidence and
builds remain intentionally under ignored paths. Artifact hashes match handoff:
sdist `e633eb9803b311210106b7673db408c63e27205ec2669184421e43fd10bc19ec`;
wheel `f3e6b76240f72608ecf9d4761ff172e2502ee358c9cd79d152324ad9b1fe657a`.

Unresolved questions: none.
