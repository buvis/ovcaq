# FT-04F10 → FT-04R11 repair evidence

Date: 2026-09-05, Europe/Prague. R10-01 is repaired and committed.
Run completion review only in a fresh FT-04R11 session; this work session
did not run completion review, close the PRD, or start another PRD.

## Exact state

- Repository: /Users/bob/git/src/github.com/buvis/ovcaq, branch master.
- Verified clean starting HEAD: 72562f6fd12fb039e91e4c7b1be29758d1901ec8.
- Repair HEAD: 22d9193a0d00486b09ebea169e7a38a9f858799d.
- Commit: fix(workflow): return complete published report text.
- Commit timestamp: 2026-09-05T22:53:07+02:00.
- Full implementation base: b43bf2c94d5eb0fddafca55542ef2570b45e8d52.
- R8 repair base: 8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7.
- Repair diff: five files, +118/-3. No production module added.
- Git status and stashes empty; only master and the original checkout exist.
- PRD remains dev/local/prds/wip/00004-workflow-core-v1.md.

## Repair and chronological regression

R10-01 (Medium, P02-T08, CMD-019/TEST-018) is the only repair.
The CLI now obtains both path and complete text from reports._publish_report,
which composes once, publishes once, exits the verified directory context,
then returns a plain tuple. The existing publish_report signature and Path
return remain intact for all prior callers. No separate pathname reread,
second renderer, result class, or public API redesign was introduced.
The changelog records the corrected machine-visible behavior.

tests/packaging/test_report_updates.py exercises installed A→B→A, with an exact
rerender at every step. It captures all six JSON results and actual artifact
bytes decoded as UTF-8, checks equality and stable paths/replays, retains
earlier and unrelated Unicode sections, collapses duplicate active sections
and summaries, replaces summary cycles 2→5, and updates A from build/0-of-1
to done/drained/1-of-1 while retaining B's review section. Every render
checks that authoritative state bytes are unchanged. State fixture changes
use the installed StateStore through reports_scripts.UPDATE_REPORT_STATE.

Before production edits, the complete scenario ran and failed at the text/file
equality assertion, index 2 (B update). The initial run failed in 1.73s;
a second run retained durable raw output in [rework-10-red.txt](rework-10-red.txt)
(1 failed in 1.67s). Production diff was empty. After the repair, the same
behavioral assertions pass; only Ruff formatting changed their layout.
This is chronological evidence for this regression, not universal full-base
fail-first binding.

## Verification

All gates ran on Darwin, Python 3.13.13, pytest 9.1.1, through mise-managed uv.
The tested source/test tree is the committed tree. Counts overlap.
[Command/output record](rework-10-verification.json).

| Command | Observed result |
|---|---|
| mise exec -- uv sync --all-groups | Exit 0; 25 resolved, 24 checked |
| New installed regression plus report identity/recovery/goldens | 61 passed in 1.85s |
| mise exec -- uv run pytest tests/workflow/ tests/packaging/ -q | 451 passed in 13.34s |
| mise exec -- uv run pytest | 1339 passed in 23.42s; zero failures/skips |
| mise exec -- uv run ruff check . | All checks passed |
| mise exec -- uv run ruff format --check . | 117 files already formatted |
| mise exec -- uv run mypy src/ovcaq | No issues in 51 source files |
| mise exec -- uv build | sdist and wheel built |
| git diff --cached --check | Exit 0 before commit |
| git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..HEAD | Exit 0 after commit |

The new test was staged before complete packaging checks, preserving the
sdist tracked-file allowlist. All existing installed module-origin assertions
pass unchanged. The fact-forcing shell gate was satisfied; a prohibited
dev/local shell redirection was replaced with apply_patch. uv cache and Git
index sandbox failures were retried through escalation. No gate was waived.

## Installed comparison

[New probe source](rework-10-report-probe.py) adapts the R10 comparison only to
use a distinct evidence destination, include the reports module origin, and
assert all expected boolean outcomes. It runs the rebuilt wheel's console
command in a fresh temporary installation outside the checkout.

[Compared texts and exact results](rework-10-report-probe.json): exit 0;
first_text_matches_file and second_text_matches_file are true; A is in both
JSON and file, B is in both, exact replay is JSON/file stable, and state bytes
are unchanged. All three module origins are in temporary site-packages.
This is now a passing equality expectation. The old discrepancy result remains
unchanged under dev/local/reviews; its old exit 0 is not called a product pass.
A→B→A and richer changes are covered by the committed installed regression.

## Preservation and source contract

Global/repository AGENTS.md, WIP PRD, accepted plan (read only), coverage
manifest, discovery 00001, both characterization TOMLs and R10/R9 evidence
were read. Both TOMLs were parsed completely; all 603 inventory items and the
55 PRD-00004 owned rows retain their source/evidence/target/disposition.
All ten P02 source tasks and each phase exit remain required for fresh review.

Plan SHA-256: 43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5.
Inventory SHA-256: d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9.
These still match the accepted manifest. See the unchanged
[55-row source join](../../../reviews/00004-cycle-10-owned-rows.json).

AST comparison confirms all 37 report functions other than the former
publish_report body are unchanged, including root-through-leaf traversal,
native publication, identical replay, successful context exit, fsyncs,
strict decoding and section rendering. The original publication body is now
the private tuple-returning function, with the same guarded context.
reports.py is 722 lines; new/changed functions are at most 46 lines.
Every prior workflow test and installed test remains unchanged.

Keep R9-01's coordinator-only ledger root despite zero prior votes: opened-
directory serialization, excluded reads, serialized original-snapshot check,
sidecar ownership/restoration refusal, successful named-boundary rivals and
exact retries. The complete retained regressions pass. Ledger/saga code was
not edited. The old adjudication harness still has its obsolete rival-success
assertion; it was not rerun here and is not reported as passing. Keep both raw
exit-1 and installed expected-refusal evidence from R10: state_io/exit 2,
no traceback, and seed/first/second each surviving retry once.

All other preservation and settled scope in [review-10.md](review-10.md),
[rework-09.md](rework-09.md), and R10 verdict/evidence remain in force.
R8-K1/K2 and R9-K3/K4 remain KNOWN. Full-base replay stays skipped on missing
packaging_support; it was not retried or bypassed. R8 bounded replay remains
56 collected, 46 failed, ten valid preservation passes; it is not chronological
installed TDD. R9's 23 fail-first cases do not prove universal base binding.

Initially missing source retains null artifact/failure evidence and refuses
later unidentified replacements. Returned controls retain their downstream
owner. No importer, aliases, launcher markers, provider/model policy,
abort/rollback API, duplicate frontmatter policy, Linux signoff, unrelated
autopilot state, plan edit, capsule refresh, PRD closeout or next PRD.

## Artifacts and next session

- sdist SHA-256: e869f5b37e43df1bdcd425a2be0897f2d69516e1cf04f32a0c203c8b035691ce.
- wheel SHA-256: 8181a0ca7e3ff1dceb0577fd144347f73021451ca63cd049129a0c7a70739a6b.

No worktree, branch or executed plan was created. The independent probe root
and children were context-managed/reaped; pytest manages its temporary roots.
Older evidence and other sessions' files are retained. The new ignored
evidence, continuation prompt and distribution artifacts are intentional.

Run FT-04R11 only in a fresh review session over the full implementation range.
Use isolated Alice consensus, Blake PRD-only and Bob doubt plus de-slop with
full consensus/blind rubrics and D1–D5 (installed names for requested R1–R5).
Do not retry external Bob/Carl nested-wrapper guards or claim model diversity.
Completion is still review-pending; no completion verdict is issued here.

Unresolved questions: none.
