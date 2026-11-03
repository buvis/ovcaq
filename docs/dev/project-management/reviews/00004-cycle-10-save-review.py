"""Save FT-04R10 findings, source coverage, dispatch provenance and handoff."""

import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path.cwd()
REV = ROOT / "dev/local/reviews"
TMP = ROOT / "dev/local/tmp"
HANDOFF = ROOT / "dev/local/plans/fast-track-handoffs/00004-workflow-core-v1"
PACK = Path("/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.0")
HEAD = "72562f6fd12fb039e91e4c7b1be29758d1901ec8"
BASE = "b43bf2c94d5eb0fddafca55542ef2570b45e8d52"
TAG = "00004-cycle-10"
STEM = "00004-workflow-core-v1-fast-review-10"
raw = {name: (TMP / f"{name}-output-{TAG}.txt").read_text().strip() for name in ("alice", "blake", "bob")}
source = json.loads((REV / f"{TAG}-owned-rows.json").read_text())
for name, prefixes in {"alice": {"R": {1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13}}, "blake": {"B": set(range(1, 20))}, "bob": {"R": {1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13}, "D": set(range(1, 6))}}.items():
    lines = re.findall(r"^([RBD])(\d+): (pass|fail)$", raw[name], re.M)
    assert len(lines) == sum(len(values) for values in prefixes.values())
    for prefix, expected in prefixes.items():
        assert {int(number) for actual, number, _ in lines if actual == prefix} == expected

consolidation = subprocess.run([sys.executable, str(PACK / "skills/review-work-completion/scripts/consolidate_findings.py"), *[f"{name.upper()}:{TMP / f'{name}-output-{TAG}.txt'}" for name in raw]], capture_output=True, text=True, check=True)
(REV / f"{TAG}-consolidation-raw.md").write_text(consolidation.stdout)

dispatch = {
    "cycle": "FT-04R10", "date": "2026-09-05", "head": HEAD, "full_range": f"{BASE}..{HEAD}",
    "mode": "standalone", "skill": str(PACK / "skills/review-work-completion/SKILL.md"),
    "consensus_engine": "legacy", "doubt_reviewer": "codex", "codex_rung_guard": "not fired",
    "native_contexts": True, "fork_turns": "none", "model_overrides": False, "model_diversity": False,
    "external_wrappers": "Not retried or bypassed, per explicit user instruction preserving nested-dispatch refusals.",
    "carl": "disabled; known nested external dispatch unavailable and user says do not retry",
    "eve": "disabled; standalone PRD default; no attempt store attached or consulted",
    "pack": "No retrieval pack or capsule refresh; explicit review-only source scope and prior retrieval restriction retained.",
    "state_store": "No unrelated autopilot state consulted, created, attached or mutated.",
    "host_adapter": "Installed persona bodies and rubrics inlined into isolated native contexts; read-only shell used for file inspection because no separate Read tool is available. Bob remained static-only.",
    "source_tasks": 10, "owned_rows": 55,
    "reviewers": [
        {"name": "alice", "agent": "/root/alice", "lens": "implementation-aware consensus", "persona": "agents/alice.md", "visibility": "PRD, full diff, mandatory source references, mechanical facts, explicitly authorized R9/rework09 evidence and settled decisions; no other lens output", "rubric": [f"R{n}" for n in (1,2,3,4,6,7,8,9,10,11,12,13)], "checks": "67 focused tests, 4 independent TOML probes, maximum-size plan chain"},
        {"name": "blake", "agent": "/root/blake", "lens": "PRD-only blind", "persona": "agents/blake.md", "visibility": "PRD and accepted specification references only; no diff, changed-file list, history, repair context, design doc, pack or other output", "rubric": [f"B{n}" for n in range(1,20)], "checks": "Independent missing-source disposable probe; no full suite"},
        {"name": "bob", "agent": "/root/bob", "lens": "static doubt and de-slop", "persona": "agents/bob.md plus agents/eve.md Two lenses, buckets and complete doubt rubric", "visibility": "PRD, full diff/current files, source contract, mechanical facts and settled constraints; no design doc, repair handoff or prior reviewer output", "rubric": [f"R{n}" for n in (1,2,3,4,6,7,8,9,10,11,12,13)] + [f"D{n}" for n in range(1,6)], "checks": "Static only. Coordinator supplied fresh gate results and confirmed Bob-origin report doubt before Bob finalized."},
    ],
    "isolation": "All three completed before any raw output was written. No cross-lens findings were shared. Bob first identified report mismatch, then coordinator independently reproduced and sent only that evidence back to Bob.",
    "consolidation": "Installed script output retained verbatim (9 rows); coordinator canonicalizes schema location, folds inherited packaging sizes into existing size limitation, resolves VERIFY and adjudicates settled null-artifact objection.",
    "review_only": True,
}
for reviewer in dispatch["reviewers"]:
    reviewer.update(status="completed", prompt=f"dev/local/tmp/{reviewer['name']}-prompt-{TAG}.md", output=f"dev/local/tmp/{reviewer['name']}-output-{TAG}.txt")
(REV / f"{TAG}-dispatch.json").write_text(json.dumps(dispatch, indent=2) + "\n")

evidence = f"""# FT-04R10 evidence — PRD 00004

Fresh review on 2026-09-05, Europe/Prague. Verified before changes: master at
`{HEAD}`, clean Git status, expected commit title and timestamp
`2026-09-05T22:20:36+02:00`. Full implementation range:
`{BASE}..{HEAD}` — 11 commits, 72 files, +9674/-348.
The latest repair commit was not substituted for the full implementation scope.

Read repository/global AGENTS.md, WIP PRD, accepted implementation plan (read
only), coverage manifest, discovery 00001, both characterization TOMLs, R9
verdict/evidence and bounded decisions, rework08/probes/sizes, rework09 contract,
regressions and verification/probe evidence. Both TOMLs were parsed in full and
joined freshly; all 55 owned rows retain source, evidence, disposition and
target in [the source join]({TAG}-owned-rows.json). All ten task texts and source
phase exits remain verbatim in [task context](../tmp/review-tasks-{TAG}.md).

Plan SHA-256: `{source['plan_sha256']}`.
Inventory SHA-256: `{source['inventory_sha256']}`.
Both match the accepted manifest and repair handoff. P02-T01–T05 share initial
commit `06fdf88149a7cafd6d3f4ec9aedf1510a59a652a`; T06–T10 share
`5a7ff023059bd396a177da7946a25ffe8d6d176d`. All repairs remain in the full range.

## Fresh verification

[Exact command results]({TAG}-verification.json). All executions used
mise-managed uv on Darwin, Python 3.13.13, pytest 9.1.1.

| Command | Observed result |
|---|---|
| `mise exec -- uv sync --all-groups` | Exit 0; 25 resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/ tests/packaging/ -q` | 450 passed in 11.21s |
| `mise exec -- uv run pytest` | 1338 passed in 22.44s; zero failures/skips |
| `mise exec -- uv run ruff check .` | All checks passed |
| `mise exec -- uv run ruff format --check .` | 116 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | No issues in 51 source files |
| `mise exec -- uv build` | sdist and wheel built |
| `git diff --check {BASE}..HEAD` | Exit 0 |

Alice independently ran 67 focused tests in 0.27s and four TOML probes, plus a
maximum-size 512-task dependency chain. Counts overlap and are not added to the
full suite. Bob's static VERIFY is resolved by the fresh coordinator record;
no redundant full-suite run or task is needed. A later read-only probe-summary
command hit uv's cache sandbox restriction and passed through the required
escalation retry. The initial shell fact-forcing gate was satisfied before
preflight ran. No implementation check was waived.

## R9 and R8 preservation

| Repair | Fresh evidence and disposition |
|---|---|
| R9-01 | Repaired. Opened-directory inode lock excludes competing reads and native replacement. Serialized original-snapshot comparison catches restored-sidecar stale writes. New nested/process tests and six unchanged R8 named-boundary nested/process tests pass. The coordinator-only root remains explicit despite zero R9 lens votes. |
| R9-02 | Repaired. Root-to-leaf identities survive traversal, replacement, identical replay and context exit. All 16 report/audit/archive component tests pass; displaced payload and state bytes survive, valid retries/rerenders match. |
| R9-03 | Repaired. RecursionError maps to contextual ConfigurationError/usage. Four installed recognized/ignored project/user TOML cases pass in the full suite and fresh independent wheel probe. |
| R9-04 | Repaired. Shared `_section_span` removes the duplicated heading scan while retaining duplicate collapse, missing-section refusal, exact heading boundaries and unrelated content. |
| R9-05 | Repaired. `_run` delegates to `_run_unchecked`; conversion/cwd/env/capture/text/60-second timeout and diagnostic assertion retained. Both complete suites and installed origins pass. |

Retained R8 guarantees: strict duplicate/deep JSON decoding and byte preservation;
original PRD device/inode identity at intent/move/recorded restart/publication;
sidecar ownership and lifecycle/ledger fences; earlier boundary competitor
survival; complete cross-PRD deferred details; creation, replacement and replay
directory fsyncs; substantive decision filtering with numeric/string zero;
nonregular/FIFO input refusal; test assertions preserved after splits. Terminal
drain, conflicting-stall refusal, nonzero/unknown totals, equal-key metric
ordering, active-batch scope, explicit recovery kind, control-character refusal,
provider neutrality and parser-derived docs remain covered by the full suite.
No R8 named test was edited in the R9 repair or this review.

## Independent coordinator probes

All original cycle09 scripts were read and rerun unchanged. Fresh stdout/stderr
and exits are retained separately from the old results:

- [Original 19-observation harness]({TAG}-original-probes.json): exit 0.
  BEFORE_PUBLISH rival succeeds and survives (`second`, then `second, first`
  after retry). Native-interval rival is refused; the old callback propagates
  refusal and prevents the first native replacement, then retries `first`.
- [Original publication harness]({TAG}-original-publication-probes.json): exit 0;
  report/audit/archive all refuse displaced directory identities and retain
  their payloads.
- [Original adjudication harness]({TAG}-original-adjudication-probes.json):
  **exit 1**, retained in full. Its `assert rival.returncode == 0` is obsolete
  because the bare child-library call raises expected contention. This harness
  is not reported as passing and its traceback is not an unhandled CLI error.
- [Unchanged remaining adjudication functions]({TAG}-adjudication-supplement.json)
  complete successfully. Frontmatter derived-state ownership and initially
  absent-source/null-artifact refusal remain as settled.

[Probe orchestrator]({TAG}-probes.py) adds an independent installed-wheel rival
at the native replacement syscall. [Exact result]({TAG}-installed-lock.json):
the rival returns exit **2**, `state_io` JSON, contextual `deferred publication
busy; retry`, empty stdout and no traceback. The original native replacement
continues, then its displaced sidecar causes the required identity refusal.
Retries produce `seed, first, second` exactly once, preserve authoritative state
and make further replay byte-identical. Module origins are in the temporary
installation's site-packages. This supplements the new real-process library
regression and keeps resource/contention refusals distinct from unhandled errors.

[Installed TOML results]({TAG}-installed-config.json): all four project/user ×
recognized/ignored cases return usage JSON/exit 1 with source path, empty stdout,
no traceback and unchanged config/state. Temporary installations, probe roots
and children were context-managed/reaped.

## R10-01 — report JSON text disagrees with published artifact

**Medium, FIX, P02-T08 / CMD-019 / TEST-018**, with integration through P02-T09's
shared machine output contract. Bob identified the issue statically before the
coordinator confirmed it in a clean wheel install outside the checkout.

`workflow_cli.py:161` computes fresh `render_report(state, ...)` for JSON `text`,
then `publish_report` computes a different `_updated_report(existing, ...)` that
retains earlier PRD sections and unrelated content. Render A, change active PRD
to B through StateStore, render B: JSON `text` contains B only, while the returned
`path` contains A+B. Both commands succeed; exact rerender repeats the mismatch.
Authoritative state and the complete on-disk report remain intact. This is an
incomplete machine-readable representation, not loss of ledger/state data.

[Executable installed probe]({TAG}-report-probe.py) /
[full compared texts, origins and observations]({TAG}-report-probe.json).
First publication has `text == file`; the second has false equality, A absent
from JSON and present in the file, B present in both. The probe's exit 0 means
it observed the discrepancy successfully, not that the product contract passed.

The accepted report is a batch artifact with replaceable per-PRD sections
(ART-013/CMD-019). JSON `text` and `path` are presented as the same render result;
the installed completed-summary test already asserts their equality for first
publication (`tests/packaging/test_installed_reports.py:164`). No distinct
partial-text contract is documented. Returning different content on update
breaks that established contract for machine consumers. This gap is in the full
implementation range, independent of the correctly repaired R9 path identity.

Bounded repair: compose/publish once and return the exact composed text from
that verified operation. Avoid a separate unverified pathname reread. Add
installed A→B→A and exact replay coverage; `text` must equal the actual published
artifact, retain prior and unrelated sections, collapse duplicates, and leave
state bytes unchanged. Preserve report/audit/archive identity/fsync guards,
configured-path retry, all golden projections and the ledger serialization root.
Do not add a second renderer or redesign public workflow ownership.

## Ten source-task assessments

| Task | Current evidence | Assessment |
|---|---|---|
| P02-T01 | selection/paths/configuration + installed input tests | Covered: total ordering, WIP/backlog/hold rules and configured lifecycle paths. |
| P02-T02 | frontmatter/applications + installed inputs | Covered within settled returned-control/downstream ownership; caps/tiers/CAS/warnings preserved. |
| P02-T03 | transitions/applications/records + installed lifecycle | Covered: all six effect rows, rejection rows, atomic handoff and terminal drain. |
| P02-T04 | resume/policy/characterized fixtures + installed CLI | Covered: recovery/pause/phase/task precedence, shape/ceiling/override; no runtime policy added. |
| P02-T05 | records/applications/blank decisions + service contracts | Covered: exact reset owners, batch preservation, deterministic completion, conflicting replay, zero/blank filtering. |
| P02-T06 | deferred ledger/integrity/publication + installed lock probe | Covered: attribution, op IDs, exact/conflicting replay, strict reads and repaired kernel serialization. |
| P02-T07 | sagas/artifacts/identity/publication/boundaries + installed sagas | Covered: typed intent, every durable boundary, original identities and fail-closed reset/commit; absent-source stance retained. |
| P02-T08 | reports/recovery/identity/blank decisions + installed reports | R9 repairs pass; R10-01 blocks machine output consistency on report updates. Other deterministic projections preserved. |
| P02-T09 | configuration/paths/installed inputs/TOML/FIFO tests | Configuration and malformed-input obligations covered; R10-01 is separately attached to report CLI integration. |
| P02-T10 | live registry/parser, documentation contract tests | Covered: operations/state-protocol inventories generated from parser; no duplicate handwritten verbs. |

Source Phase 2 exits: lifecycle fixtures match v1 outcomes; park/stall interruption
recovers or safely refuses at every durable boundary under the accepted original
identity stance; workflow imports no runtime/driver/TUI/launcher module.
PRD Phase A passes; Phase B passes under the settled absent-source constraint.
Phase C remains **blocked by R10-01** despite passing retained tests because its
installed report result is incomplete after an update. Completion is not approved.

## All 55 owned rows

Each row below joins directly to its unchanged accepted source summary and
target. Groups identify passing current implementation/tests; cross-cutting
blockers remain attached to the task/phase, even when a row's projection passes.
“Covered” is evidence within the accepted contract, not exhaustive adversarial
proof or universal implementation-base binding.

| Owned ID | Accepted source obligation | Evidence group | Current assessment |
|---|---|---|---|
"""

for row in sorted(source["owned"], key=lambda value: value["id"]):
    target = row["route"]["target"]
    group = Path(target).stem.title() if target.startswith("src/") else "Docs"
    assessment = "Covered; preserve characterized behavior"
    if row["id"] in {"CMD-019", "TEST-018"}:
        assessment = "R10-01: updated report JSON text differs from published batch artifact"
    elif row["id"] == "ART-013":
        assessment = "On-disk artifact covered; machine representation gap R10-01"
    elif row["id"] in {"CMD-014", "TEST-006"}:
        assessment = "Covered within settled returned-control ownership"
    elif row["id"] in {"ART-016", "ART-017", "CMD-010", "STATE-112", "STATE-113", "TEST-013", "TEST-014"}:
        assessment = "Covered, including repaired coordinator lock root and exact retry"
    evidence += f"| {row['id']} | {row['summary'].replace('|', chr(92) + '|')} | {group} | {assessment} |\n"

evidence += f"""
Evidence groups (test filenames are under tests/workflow unless qualified):

- Selection: selection.py/paths.py; test_selection.py, test_configuration.py,
  packaging/test_workflow_inputs.py.
- Frontmatter: frontmatter.py/workflow_cli.py; test_frontmatter.py,
  test_applications.py, packaging/test_installed_cli.py/test_input_integrity.py.
- Policy/Resume: policy.py/resume.py; test_policy.py, test_resume.py,
  test_characterized_fixtures.py, test_workflow_cli.py and installed inputs.
- Transitions: transitions.py; test_transitions.py, test_records.py,
  test_applications.py and installed lifecycle/saga cases.
- Records: records.py/_files.py/_rename.py; test_records.py,
  test_deferred_ledger.py, test_ledger_integrity.py, test_ledger_publication.py,
  test_sagas.py, test_saga_artifacts.py, test_saga_identity.py,
  test_saga_publication.py, test_boundaries.py, test_blank_decisions.py;
  packaging/test_installed_sagas.py/test_input_integrity.py and
  state/test_recovery_mutations.py/test_service_contracts.py.
- Reports: reports.py and shared decision filter; test_reports.py,
  test_report_recovery.py, test_report_identity.py, test_blank_decisions.py,
  packaging/test_installed_reports.py and retained sanitized goldens.
- Docs: cli.py/workflow_cli.py; test_workflow_cli.py, state/test_cli.py,
  generated operations.md/state-protocol.md inventories.

Accepted adaptations remain: typed recovery kind replaces launcher markers;
injectable named failpoints replace test environment selectors; sanitized
fixtures use v1 state. No importer, alias, provider/model policy or Linux signoff.

## Adjudication and methodological limits

Blake's null-artifact observation is reproducible and retained verbatim. It is
the explicitly settled refusal from rework08/review09: an initially absent
source keeps failure evidence, and an unidentified later file must not be
adopted. It does not authorize a repair to delete intent, invent identity or add
abort/rollback API. The source task's safe-retry requirement is interpreted with
that explicit user decision. No new evidence invalidates its rationale. Blake
received no repair history, as required by the blind lens.

Alice's no-new-issue assessment does not refute Bob's report result mismatch;
the installed observation and existing equality assertion establish R10-01.
The R9 ledger root was independently checked rather than dropped by consensus.

Mechanical AST and test-shape helpers ran over the full changed-file list in
[implementation context](../tmp/review-context-{TAG}.md). The single MECH OR
assertion is absorbed in inherited R8-K1 with `mech-check` attribution; other
assertions in that test can fail, so the detector's generic preamble is broader
than the localized finding. Fresh [size measurements]({TAG}-sizes.json) retain
add_task 53, schema.py 933, and unchanged packaging function sizes 51/79/66.
The 800/50-line exceptions are inherited; no broad restructuring is requested.

The mandatory full implementation-base replay remains **skipped**, missing
packaging_support at collection. Its known broken invocation was not retried.
The bounded R8 repair-base supplement remains 56 collected, 46 failed and ten
valid preservation passes. Its installed tests were originally post-repair;
retrospective replay is not chronological TDD. The 23 R9 fail-first cases do not
establish universal full-range binding. These are KNOWN, not newly failed tests.

Raw consolidation has nine rows because schema.py versus schema.py:1 were not
merged, packaging size was listed separately, and VERIFY/Blake's scoped objection
remain raw. Coordinator merges schema location, folds unchanged packaging sizes
into R8-K2's existing inherited size limitation (also named by Alice), resolves
VERIFY and adjudicates the settled objection. Nothing is silently discarded.
Terminal accounting: **5 = 1 FIX + 0 VERIFY + 4 KNOWN**. Bob's raw accounting
remains 7 = 1 FIX + 1 VERIFY + 5 KNOWN, with every D1–D5 verdict retained.
Settled Low severities for inherited K2/K3 remain unchanged despite Bob's raw
Medium rubric observations. No new severity or repair scope is inferred.

All lenses carried full installed rubrics: Alice consensus R1–R4/R6–R13; Blake
B1–B19; Bob consensus plus both doubt/de-slop lenses and D1–D5 (the installed
names for requested doubt R1–R5). There is no consensus R5 in this version.
[Dispatch provenance]({TAG}-dispatch.json) records visibility and host adapters.
All returned before raw outputs were saved. Native contexts provide prompt
isolation, not model diversity. External Bob/Carl guards were not retried or
bypassed. Standalone mode did not attach an unrelated state/attempt ledger,
fabricate tasks, write a verification queue or persist doubt state.

No source/test/doc/PRD/plan/capsule change or commit was made. No worktree,
branch or executed plan was created. Probe roots/children were cleaned/reaped.
Older evidence is retained and checked by content hash in the final audit.
Review prompts, inputs, scripts, raw results and built artifacts are intentionally
retained. Both build hashes match the handoff:
sdist `e633eb9803b311210106b7673db408c63e27205ec2669184421e43fd10bc19ec`;
wheel `f3e6b76240f72608ecf9d4761ff172e2502ee358c9cd79d152324ad9b1fe657a`.
The saved review shape and final source/artifact audit are recorded in
[{TAG}-final-audit.json]({TAG}-final-audit.json).
"""
(REV / f"{STEM}-evidence.md").write_text(evidence)

review = f"""---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
review: 10
date: 2026-09-05
head_sha: {HEAD}
reviewers: alice,blake,bob
mode: standalone
consensus_engine: legacy
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
  eve: disabled
---

# FT-04R10 — PRD 00004 completion review

Diff range: `{BASE}..{HEAD}`

codex_rung_guard: not fired

**CHANGES_REQUESTED — one new actionable Medium finding.** All five R9 repairs
are verified, including the coordinator-origin ledger serialization root.
Updated report JSON omits earlier PRD sections that its published artifact
retains. Four inherited/methodological KNOWN observations remain; terminal skill
count is five, with one FIX and no unresolved VERIFY.

Full implementation review: P02-T01–T10, all 55 owned rows and every phase exit.
Fresh **1338 tests passed**, zero failures/skips. Complete workflow/packaging
450 passed; sync, Ruff, formatting, mypy, build and full-range whitespace pass.
No implementation changes, PRD closeout or next PRD occurred.

Three isolated native host contexts ran Alice consensus, Blake PRD-only, Bob
static doubt plus de-slop with all R/B/D obligations. External Bob/Carl wrappers
were not retried or bypassed; no model diversity is claimed. Standalone guard
result above does not imply an absent task-attempt ledger was consulted.

[Full source/probe evidence]({STEM}-evidence.md) ·
[Dispatch]({TAG}-dispatch.json) ·
[Raw script consolidation]({TAG}-consolidation-raw.md)

## Consolidated findings

| ID | Consensus | Severity | Finding and file | Found by | Disposition |
|---|---|---|---|---|---|
| R8-K1 | 2/3 + mech-check | Medium | Inherited collision OR assertion; tests/state/test_cli.py:372 | Alice, Bob, mech-check | KNOWN |
| R8-K2 | 2/3 | Low (settled) | Inherited 53-line add_task and unchanged packaging size exceptions; state/commands.py:148 | Alice, Bob | KNOWN |
| R9-K3 | 2/3 | Low (settled) | Inherited 933-line schema.py | Alice, Bob | KNOWN |
| R9-K4 | 2/3 | Low | Full implementation-base fail-first binding remains unproven | Alice, Bob | KNOWN |
| R10-01 | 1/3 + coordinator | Medium | Report JSON text differs from retained batch artifact after PRD update; workflow_cli.py:161 | Bob, coordinator confirmed in installed wheel | FIX |

## R10-01 evidence and acceptance

Render A, then set active PRD B through StateStore and run installed
`ovcaq --json workflow render report`. It succeeds, but `text` contains B only
while `path` contains A+B. Repeating the render preserves the mismatch. State
and the complete on-disk report are intact. Machine consumers lose earlier
section content from the returned representation.

Cause: `_dispatch_workflow_render` renders fresh text separately from
`publish_report`'s update of existing content. The accepted batch artifact and
the existing installed `text == file` assertion establish intended equality;
that test currently exercises first publication only.

[Installed probe source]({TAG}-report-probe.py) /
[Compared text, module origins and results]({TAG}-report-probe.json).
The probe reports successful reproduction, not a passing product expectation.

Bounded repair (P02-T08, CMD-019/TEST-018): compose/publish once and return that
exact verified text. Add installed A→B→A and exact-replay assertions preserving
earlier/unrelated sections, duplicate collapse and state bytes. Keep every R9
directory identity/fsync guarantee; avoid an unverified pathname reread or a
second renderer. Full acceptance and preservation details are in the handoff.

## Repair verification and adjudication

R9-01 directory-inode serialization and serialized snapshot comparison pass,
including sidecar restoration. Six unchanged R8 named-boundary nested/process
cases preserve successful rivals. The fresh installed native-interval rival
returns contextual `state_io` JSON/exit 2 with no traceback; original identity
refusal and retries preserve exactly one of each ID. R9-02's 16 output-chain
cases, R9-03's four deep-TOML installed cases, R9-04's shared scanner and R9-05's
subprocess helper reuse all pass. Full preservation details are in the companion.

The original adjudication script still exits 1 on its obsolete rival-success
assertion. Its raw tracebacks remain evidence; it is not counted as a passing
check or an unhandled installed CLI error. The separate installed rival and
unchanged supplement functions establish the expected behavior.

Blake's initially absent-source objection reproduces the explicitly settled
null-artifact refusal. A later unidentified file remains refused by requirement;
no intent deletion, identity adoption or abort API is authorized. It creates no
new repair task. Alice's no-new-findings conclusion does not negate the installed
report mismatch. Bob's VERIFY is resolved by fresh coordinator gates.

The script's schema location variants are merged; unchanged packaging lengths
are folded into the existing inherited size limitation, already in Alice's K2.
The original skipped full-base replay and bounded 56-case supplement remain
explicit. Raw opinions, counts, severities and rubric verdicts below are intact.

"""
for name in raw:
    review += f"## {name.title()}\n\n{raw[name]}\n\n"
review += f"""## Handoff

Findings are reported in the [FT-04F10 handoff](../plans/fast-track-handoffs/00004-workflow-core-v1/review-10.md),
not written into an autopilot task store. PRD remains WIP. Next: one bounded
repair in a fresh work session, then fresh FT-04R11 with every mandated lens and
source obligation. [Contract card]({TAG}-contract-card.md).
Saved-file gate and preservation audit: [final audit]({TAG}-final-audit.json).

Verdict: 5 findings
Tests: 1338 passed, 0 failed, 0 skipped (suite run this cycle)
"""
(REV / f"{STEM}.md").write_text(review)

handoff = f"""# FT-04R10 → FT-04F10 repair handoff

Date: 2026-09-05, Europe/Prague. Fresh completion review finished:
**CHANGES_REQUESTED, one actionable Medium finding**. All five R9 repairs pass.
Terminal skill count: 5 = 1 FIX + 0 VERIFY + 4 inherited/methodological KNOWN.

## Verify before changing anything

- Repository: `/Users/bob/git/src/github.com/buvis/ovcaq`, branch `master`.
- Expected HEAD: `{HEAD}`.
- Commit: `fix(workflow): serialize ledger publication and verify output paths`.
- Timestamp: `2026-09-05T22:20:36+02:00`.
- Git status must be empty. Stop on mismatch; never reset/clean others' work.
- Full implementation base: `{BASE}`.
- R8 repair base: `8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`.
- PRD remains `dev/local/prds/wip/00004-workflow-core-v1.md`.

No source/test/doc/PRD changes or commit occurred in FT-04R10. This handoff
reports bounded follow-up work; no task store or unrelated autopilot state was
created. Keep implementation and completion review in separate fresh sessions.

## Read first

Read global/repository AGENTS.md, the WIP PRD, accepted implementation plan
(read only), coverage manifest, discovery 00001 and both characterization TOMLs.
Preserve P02-T01–T10, all 55 owned rows and every phase exit.

- [R10 verdict](../../../reviews/{STEM}.md) and
  [full source/evidence companion](../../../reviews/{STEM}-evidence.md).
- [Fresh join](../../../reviews/{TAG}-owned-rows.json),
  [installed reproduction](../../../reviews/{TAG}-report-probe.py),
  [compared texts/results](../../../reviews/{TAG}-report-probe.json).
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
Plan SHA-256 remains `{source['plan_sha256']}`.
Inventory SHA-256 remains `{source['inventory_sha256']}`.

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
"""
(HANDOFF / "review-10.md").write_text(handoff)
card = f"""# FT-04R10 contract card

Current step: fresh standalone completion review finished at {HEAD}.
Verdict: CHANGES_REQUESTED; R10-01 report JSON/artifact mismatch is the sole FIX.
Four inherited KNOWN observations remain, no unresolved VERIFY.

Active invariants: full implementation range, P02-T01–T10, 55 owned rows,
source phase exits; one state writer, typed durable recovery and original
artifact identity, repaired directory-inode ledger serialization and content
comparison, report root-to-leaf identity/fsync, terminal drain, provider neutrality.

Next gate: fresh FT-04F10 bounded repair and verification, then fresh FT-04R11
completion review with all isolated lenses and full R/B/D rubrics.
No PRD closeout, next PRD, unrelated state, source-plan edit or capsule refresh.

Full-base replay limitation and external nested-wrapper guards remain in force.
Standalone: no autopilot task store or contract state was created/mutated.
"""
(REV / f"{TAG}-contract-card.md").write_text(card)
print(json.dumps({"review": str(REV / f"{STEM}.md"), "evidence": str(REV / f"{STEM}-evidence.md"), "handoff": str(HANDOFF / "review-10.md"), "terminal": {"fix": 1, "verify": 0, "known": 4, "total": 5}, "raw_consolidation_rows": len(re.findall(r"^\| \[", consolidation.stdout, re.M))}, indent=2))
