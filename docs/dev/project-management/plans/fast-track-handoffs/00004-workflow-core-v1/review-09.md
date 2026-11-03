# FT-04R9 → FT-04F9 repair handoff

Date: 2026-09-05, Europe/Prague. FT-04R9 is complete:
**CHANGES_REQUESTED, five actionable findings** (one High, four Medium).
Nine terminal findings include four inherited/methodological KNOWN observations.

## Verify before changing anything

Work in `/Users/bob/git/src/github.com/buvis/ovcaq`.
Expected master HEAD: `78f916c366f74105b76e6f07d80a7a1aeb251e9f`.
Git status must be empty. Stop on mismatch; never reset/clean another session's work.
No implementation changes or commits were made in FT-04R9.
PRD remains `dev/local/prds/wip/00004-workflow-core-v1.md`.

Full implementation base: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`.
R8 repair base: `8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`.
Preserve the entire accepted source contract: P02-T01–P02-T10, all 55 owned rows,
and every phase exit. This is a work-session handoff; do not run completion
review until handing off to a separate fresh FT-04R10 session.

## Read first

- Repository/global AGENTS.md and the WIP PRD.
- `dev/local/plans/implementation-plan.md` (read only), coverage manifest,
  discovery 00001, `tests/characterization/migration.toml` and `current_system.toml`.
- [Cycle-09 verdict](../../../reviews/00004-workflow-core-v1-fast-review-09.md)
  and [source/evidence companion](../../../reviews/00004-workflow-core-v1-fast-review-09-evidence.md).
- [R8 repair/evidence preservation](rework-08.md), plus its probes/sizes.
- Cycle-09 [adjudication probes](../../../reviews/00004-cycle-09-adjudication-probes.py),
  [publication probes](../../../reviews/00004-cycle-09-publication-probes.py),
  [installed TOML result/command](../../../reviews/00004-cycle-09-installed-config.json).
  Probe results are adjacent; all fixtures are sanitized and temporary.

## Bounded repair tasks

1. **R9-01 (High, M) — close the residual ledger lock race.**
   P02-T06/P02-T07; `workflow/_files.py:98–99`.
   After lock identity validation and before native replacement, moving the
   sidecar lets a second legitimate writer finish under its replacement.
   The first stale replacement destroys that successful append, then raises an
   identity error. Retry does not restore the lost record. Nested and separate
   process probes both reproduce.
   Establish serialization that cannot split into stale writers across this
   interval; another pathname check alone does not prove it. Every successful
   append must remain present, lock-loss refusal must preserve durable evidence,
   and retry must yield exactly one record per operation ID. Preserve named
   boundary coverage, real subprocess evidence, original artifact identity,
   saga publication guards, strict decoding and exact/conflicting replay.
   Keep this root even with zero lens votes. Capture a failing regression before
   the repair; do not rely solely on the already-passing BEFORE_PUBLISH case.

2. **R9-02 (Medium, M) — verify report publication directory identity.**
   P02-T08; `reports.py:_output_directory/_publish_file`.
   Report, audit and final-state archive return success when their configured
   directory has been renamed/recreated; returned paths are absent.
   Retain and validate the configured directory chain through publication,
   identical-payload replay and successful return. Add replacement/retry
   regressions for all three surfaces; replacement must fail contextually,
   preserve authoritative state, and allow valid retry at the configured path.
   Preserve parent creation sync, post-replace/identical-replay fsync, refusal of
   nonregular paths, byte-identical rerenders, goldens and unrelated sections.

3. **R9-03 (Medium, S) — contain deep TOML decode failures.**
   P02-T09; `config.py:47`.
   Project and user configuration with 2,000 nested arrays escapes as a
   RecursionError traceback under installed `--json workflow select`.
   Bound the decode or normalize exhaustion into contextual symbolic CLI errors.
   Add installed project/user regressions for recognized and ignored keys,
   preserving configuration/state bytes and no stdout/traceback. Retain
   FIFO/nonregular/symlink refusal, defaults, precedence and installed origins.
   Do not add downstream provider/model configuration policy.

4. **R9-04 (Medium, S) — remove duplicate report section scanning.**
   Share the exact-heading/next-level-two-heading span finder between
   `_replace_section` and `_report_section`.
   Preserve duplicate collapse, missing-section error, heading boundaries,
   unrelated content and all existing behavioral assertions/goldens.

5. **R9-05 (Medium, S) — reuse the installed subprocess runner.**
   Have packaging_support._run delegate to _run_unchecked, retaining its
   assertion diagnostic. Preserve argv/cwd/environment/capture/text/timeout
   and installed-origin checks. Use existing behavioral coverage; avoid a test
   that merely asserts delegation.

## Settled decisions and preservation

- R8-K1 collision OR assertion and R8-K2 inherited 53-line add_task remain KNOWN.
  R9-K3 inherited schema size and R9-K4 full-base binding limit are also
  documented; no broad state or replay-tool restructuring.
- Retain all R8-01–R8-08 repairs/regressions. R8-03 is incomplete at the new
  interval; R9-02/R9-03 do not invalidate the repaired fsync/FIFO cases.
- Preserve terminal drain, conflicting-stall refusal, nonzero and legacy/mixed
  unknown totals, equal-key ordering, active-batch metrics, explicit recovery
  kind, lifecycle/ledger identity and publication fences, control-character
  refusal, provider neutrality and parser-derived docs.
- Null artifact on initially missing source intentionally preserves failure
  evidence and refuses later unidentified replacements. Do not delete that
  intent, fabricate identity, or add an abort/rollback API.
- Frontmatter parsing returns controls; the accepted derived-state/runtime
  owner boundary remains. Do not invent catchup/design completion or duplicate
  durable policy to satisfy the raw Blake objection.
- Runtime/provider configuration and Linux qualification keep their owners.
  No importer, old-command aliases, launcher markers, unrelated autopilot
  state, PRD closeout, implementation-plan edit, capsule refresh or next PRD.

## Verification and review gate

Fresh FT-04R9: full pytest **1315 passed in 19.06s**, zero failures/skips;
complete workflow/packaging **427 passed in 10.37s**. Sync, Ruff, format, mypy,
build and full-range whitespace passed. Darwin/Python 3.13.13 only.
The saved review passes its installed shape gate.

Use mise-managed uv; cache/Git writes may need sandbox escalation.
After repairs run complete workflow/packaging directories, the full suite and
the AGENTS.md quality gates. Preserve installed wheel/module origin checks.
Run the cycle-09 probes and retain the observed result, separating expected
refusals from unhandled errors.

The mandatory full implementation-base replay remains skipped on missing
packaging_support; do not retry that dead end or claim universal fail-first
binding. A bounded repair-base replay with complete test/support overlay
collected all 56 R8 cases: 46 failed, ten valid nonblank/zero preservation cases
passed. Installed ledger regressions first ran after their original repair;
the retrospective replay does not establish chronological TDD.

After bounded repairs, commit as authorized in the work session, record exact
HEAD/checks and hand off. Run FT-04R10 only in a fresh review session, with all
isolated Alice consensus, Blake PRD-only, Bob doubt plus de-slop and D1–D5
obligations, full rubrics and all source rows. External Bob/Carl nested wrappers
remain a dead end; do not bypass their guards or claim native model diversity.

Cycle-09 review files, prompts and probe results are intentionally retained
under ignored dev/local. Session-owned probe roots, subprocesses and detached
replay worktree were cleaned/reaped. Preserve all older evidence and others'
work. Final state/shape/artifact evidence:
[cycle-09 final audit](../../../reviews/00004-cycle-09-final-audit.json).

Unresolved questions: none.
