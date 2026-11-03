---
prd: 00004-workflow-core-v1
session: FT-04F6
next_session: FT-04R7
date: 2026-09-05
base_sha: c4b9ea38d2e11eac4a1de1a71bd7d4134142e661
head_sha: 47a8764760e1fedb82eb1514a344584fb7ad2f3e
implementation_base_sha: b43bf2c94d5eb0fddafca55542ef2570b45e8d52
status: ready_for_fresh_review
---

# PRD 00004 — FT-04F6 rework handoff

Implemented all six cycle-06 must-fix root causes in one commit:
`47a8764760e1fedb82eb1514a344584fb7ad2f3e`
(`fix(workflow): fence terminal state and deferred publication`).

Started from the exact requested clean HEAD. Read AGENTS.md, the WIP PRD,
consolidated cycle-06 review, current workflow implementation and relevant tests,
retained fixtures, accepted P02-T01–P02-T10 source/coverage rows, resolved
discovery, and all 55 PRD-00004 migration/inventory rows. No raw lens report,
earlier PRD-00004 review, or earlier handoff was read. No review ran in this session.

## Bundle 1 — contract and deterministic correctness

1. **Terminal drain:** transition application refuses every outcome once work is
   `done/""`. Park and stall reject drained work before filesystem effects or
   durable intent. Direct and installed CLI tests preserve state bytes and WIP.
2. **Conflicting stall intent:** pending recovery must match PRD, kind, site, and
   detail for stall. Tests isolate kind/site/detail conflicts and preserve state
   and files; park still deliberately reconciles pending stall or park intent.
3. **TEST-062 completed totals:** report rows tolerate incomplete records and
   filename-only legacy entries. Missing or invalid totals render `unknown` per
   field; empty totals remain zero and complete retained values remain nonzero.
   Direct tests and installed CLI dispatch cover empty, rich, legacy, and mixed
   summaries. The durable v1 schema remains strict: installed legacy cases inject
   a read-only projection at `StateStore.read`, then exercise the installed parser,
   dispatch, renderer, and report publication. They do not import legacy state.
4. **Total metric ordering:** canonical JSON supplies a final tie-breaker for
   sessions and convergence rows after the existing primary keys. Tests collide
   primary keys while varying rendered fields, reverse input, and require equal
   output, including installed metrics commands.

## Bundle 2 — publication identity and availability

5. **Deferred directory identity:** ledger locking, reading, temporary creation,
   replacement, cleanup, and fsync use a held directory descriptor. Identity is
   checked against the configured pathname around publication. Sagas retain the
   descriptor and ledger lock through advancement/commit, verify record and move
   evidence before and inside state transactions, and require ledger proof when
   resuming a recorded operation. Directory replacement fails with recovery and
   tasks retained; restoration permits exactly one recorded result.
   Tests exercise directory/symlink replacement at defer boundaries, replacement
   during creation/fsync, both saga commit boundaries, transaction entry, and
   restart with missing recorded proof. Installed CLI tests inject the existing
   boundary hooks and then reconcile using the console command without injection.
6. **Nonregular report targets:** existing output is opened nonblocking before
   regular-file validation. Direct subprocess and installed console tests reject
   FIFO, directory, and Unix socket targets within a three-second timeout,
   preserving target identity and returning a domain failure.

Existing WIP/hold identity tests, recovery mutation fencing, durability ordering,
explicit recovery kind, active-batch metrics, control-character refusal,
provider-neutral boundaries, and parser-generated documentation all pass. The
fsync spies now observe the bound deferred descriptor while retaining ordering
assertions. No command syntax, schema, dependency, or documentation generator
changed. CHANGELOG.md records the repaired behavior.

## Verification

| Command | Result |
| --- | --- |
| `mise exec -- uv sync --all-groups` | Passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/workflow/test_reports.py tests/workflow/test_transitions.py tests/packaging/test_installed_cli.py -q` | Passed; 173 tests in 5.92s |
| `mise exec -- uv run pytest` | Passed; 1,180 tests in 14.66s |
| `mise exec -- uv run ruff check .` | Passed |
| `mise exec -- uv run ruff format --check .` | Passed; 92 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | Passed; 47 source files |
| `mise exec -- uv build` | Passed; sdist and wheel built |
| `git diff --check c4b9ea38d2e11eac4a1de1a71bd7d4134142e661..HEAD` | Passed after commit |

The initial focused regressions reproduced all six defects before their fixes.
There are 72 additional passing tests over the starting HEAD. Tracked worktree is
clean. No extra worktree, branch, or repository temporary file was created.
This handoff is local and ignored under the existing dev/local policy.

## Fresh-session handoff

Start **FT-04R7** at exact clean HEAD
`47a8764760e1fedb82eb1514a344584fb7ad2f3e`.

Review the complete PRD implementation range
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..47a8764760e1fedb82eb1514a344584fb7ad2f3e`,
with the repair range above available separately. Run every mandatory review
lens in isolated contexts: Alice consensus, Blake blind/PRD-only, and Bob
doubt plus de-slop R1–R5. Preserve the blind lens's PRD-only input isolation.
Recheck every source obligation and retained behavior, including these six repairs.

Autopilot state, implementation plans, PRD location/status, and capsule were not
changed. No next PRD was started. FT-04F6 ends here; review belongs to FT-04R7.
