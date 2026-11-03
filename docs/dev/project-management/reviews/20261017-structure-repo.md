# Repository structure migration — 2026-10-17

Target: `/Users/bob/git/src/github.com/buvis/ovcaq`.
Mode: restructure. Status: INCOMPLETE; independent groups implemented, workflow
storage migration blocked by existing consumers. No production modules changed.

## Baseline and fit

The selected path is its own Git worktree, on `master` at `38dc3bf`.
No remotes or tags exist. Only the primary worktree exists. There is no configured
`core.hooksPath`; no hook manager was installed or changed.

Pre-existing local changes, preserved:

- Modified `docs/dev/project-management/autopilot/autocodex-metrics.jsonl`.
- Modified `docs/dev/project-management/autopilot/autocodex-sessions/8929523ac3b54a80883b21e7d1e895cb.jsonl`.
- Untracked `docs/dev/project-management/autopilot/reports/autocodex-3079b0d199bc415c87045893458e98d8-state-final.json`.

Python CLI/TUI: native `src/ovcaq` and test layout fit. Common tooling,
instruction bridges, and current architecture documentation fit.

MISFIT: replacing PRD status buckets or moving Autopilot records independently
would break existing readers/writers. The standard is a migration destination,
not grounds for changing product workflow behavior during repository restructuring.
Preserve original evidence and the single queue authority until consumers migrate.

## Applicability and path map

| Area / observed source | Fit and destination | Consumer / prerequisite | Action |
| --- | --- | --- | --- |
| `src/ovcaq/`, `tests/`, `pyproject.toml`, `uv.lock` | Native Python layout fits | Hatch, pytest, installed CLI | Preserve |
| Root `AGENTS.md`, absent `CLAUDE.md` | Shared prose plus import fits | Codex entry point; Claude import | Add one-line bridge; correct stale project status and checks |
| No nested maintained AGENTS scopes | No nested bridge needed | Tracked-file inventory and helper `--nested` | Verify |
| Absent mise/tasks/tools | Common commands fit | Installed mise 2026.10.7, Python 3.12.13, uv 0.13.0 | Add pinned tasks and five executable shims |
| `.github/workflows/ci.yml` | Existing checks fit | Same uv lint/format/type/test/build implementations | Preserve CI commands |
| `.github/workflows/release.yml`, manifest dev version | Artifact build fits; publication deferred | Public-release PRD 00014 is held; no remotes/tags | Preserve artifact workflow; no release task or publishing |
| Absent architecture overview | `docs/dev/architecture/README.md` fits | Current code boundaries and protocol docs | Add linked overview |
| `docs/dev/project-management/meta/` | Future `docs/dev/context/` | External context reader/writer migration required | Preserve sole capsule authority; do not duplicate/move |
| `docs/dev/project-management/plans/` | Authority and retained review evidence | AGENTS, capsule, characterization test, historical recovery links | Retain authoritative plans and evidence; no disposable executed plan created here |
| `docs/dev/project-management/prds/` | Future intake/spec bundles | Product `src/ovcaq/config.py:233`, bucket lifecycle services and external Autopilot | Deferred deviation; no invented approvals or secondary queue |
| `docs/dev/project-management/autopilot/` and paused evidence | Future runtime/records and scoped reviews | External runner, record-store, review recovery, cleanup; modified evidence | Deferred deviation; no live controls moved |
| Historical designs/discovery/reviews/audit results | Future classification by spec/scope | Queue migration and stable historical links | Preserve with original meaning until coherent migration |
| `docs/dev/tmp/`, obsolete `dev/local/` ignore | Canonical scratch fits | Existing scratch consumers; no tracked scratch | Replace obsolete ignore with exact scratch subtree ignore |
| No project-owned skills or projection config | Braid not applicable | No authored skills need projection | Do not import global skills or add hooks |
| No Specflow config or canonical spec bundles | Capability prerequisite unresolved | External runner still requires PRD buckets | Do not invent schema fields, hashes, or install a new workflow |

## Capability evidence and host boundaries

Installed mise validates all five tasks. `task.run_auto_install` is supported and
disabled for this repository. Task implementations call uv directly; shims call
their same-named task, so they cannot recurse through `tools/` on PATH.

Declared development host entry points are Codex (`AGENTS.md`, loaded in this
session) and Claude Code (`CLAUDE.md` importing `AGENTS.md`). Both are also product
adapter targets. No live Claude instruction-loading probe was performed; file
presence does not establish actual session loading. Copilot/Kiro/IDE/cloud adapters
are not declared repository integrations. No Kiro panel or skill projection is claimed.

The locally available external Autopilot source at
`/Users/bob/git/src/github.com/buvis/claude-autopilot/skills/run-autopilot/SKILL.md`
explicitly uses legacy state (line 62), deferred records (64), runtime layout (85),
durable capsule/records (111), and bucket selection (258/285). That is sufficient
negative capability evidence: a new Specflow config alone cannot switch its queue.
This source was read, not invoked. No external repository was modified.

Full/fast review rosters and fresh-session review boundaries are unchanged.
No creation, approval, supervisor run, cleanup purge, or recovery migration is
claimed. No release destination exists; public publication and release adapters
remain held product work, rather than a fabricated successful release command.

## Completed groups and resume point

1. Root instruction bridge and current project/development documentation added.
2. Mise tools/tasks and executable shims added; no global installation or hooks.
3. Scratch ignore corrected; historical workflow storage and dirty evidence retained.

Next migration group: first make OVCAQ and external workflow consumers accept the
same canonical spec representation and split runtime/records. Verify review gates,
recording pathspecs, recovery, context writers, and cleanup using isolated fixtures.
Then migrate queues/history/records together at a safe runner handoff boundary.
Keep all original IDs and provenance; do not derive approval hashes from done status.

## Verification

Validation results and the complete helper JSON follow below.

- `./tools/onboard`: PASS twice in the selected checkout; lockfile unchanged.
- Disposable local clone with structure files overlaid: first and repeated onboard
  and installed `uv run --locked ovcaq --help` PASS. No commits created.
- `mise tasks validate`: PASS, five tasks. Installed Python/uv satisfy pins.
  The existing checkout retains its compatible Python 3.13.16 virtual environment;
  the mise pin supplies Python 3.12.13 for new setup.
- All five shims: PASS POSIX syntax and relocated-checkout fixture with spaces in
  paths/arguments. Each anchors to its checkout, forwards arguments exactly, and
  preserves simulated failure status 23.
- Invocation from `/tmp`: `tools/run-tests tests/characterization/test_migration_contract.py -q`
  PASS, six tests. An initial invocation with a redundant `--` failed; documentation
  now gives the verified direct-argument syntax.
- Lint: PASS. Formatting: PASS, 241 files. Types: PASS, 61 source files.
- `./tools/build`: PASS, sdist and wheel. Removed unsupported `uv build --locked`
  discovered by validation; package metadata/lockfile were not changed.
- `./tools/check`: INCOMPLETE. Collected 7,257 tests. Interrupted after repeated
  process-test failures: `PermissionError: [Errno 1] Operation not permitted: 'ps'`
  at `runtime/registry.py:130`. Do not interpret this as a complete suite result.
- Narrow process test reproduced the same denial both normally and with the tool's
  escalation flag. The macOS Seatbelt boundary still applies. No test weakened.
- Original full-check warrant request `1385e7cda9df42c21f1a562a7ace8f15` was
  refused at human approval: `executable lies in an agent-writable path` for
  `tools/check`. The checkout shim is not an eligible broker executable.
- Replacement request `03b6c41c2a02f0a07128a2319ec83ff1` invokes the pinned,
  read-only installed uv executable directly for the remaining pytest step:
  `/Users/bob/.local/share/mise/installs/uv/0.13.0/uv-aarch64-apple-darwin/uv run --locked pytest`.
  Working directory: `/Users/bob/git/src/github.com/buvis/ovcaq`.
  Human approval refused this request too: `executable is not under a
  trusted_exe_roots entry`. No further broker requests or trust-policy changes
  are proposed. Both requests are refused, not pending.
- Remaining verification requires a direct run in the user's host terminal:
  change to `/Users/bob/git/src/github.com/buvis/ovcaq`, then run `./tools/check`.
  This runs the existing development checks outside the agent's Seatbelt profile;
  it does not require changing Warrant's executable trust policy. Results remain
  unverified until that run completes.
- `git diff --check`: PASS. Scratch probe is ignored. No tracked scratch moved.
- Actual linked Git worktree execution and live Claude loading were not probed.
  Relocated shims and fresh-clone checks are narrower evidence, not substitutes.
- Hooks, projection, optional Kiro, workflow conversion, cleanup conversion and
  public release are unimplemented/not claimed for the reasons above. No purge
  was run; no original evidence or recovery state was removed. No commit/push.

## Structural helper result

The exact helper JSON is pasted below. Its PASS certifies only the structural
subset, with two explicit DEVIATION results; overall migration remains INCOMPLETE.

```json
{
  "mode": "check",
  "target": "/Users/bob/git/src/github.com/buvis/ovcaq",
  "structural_gate": "PASS",
  "checks": [
    {
      "check": "own-git-worktree",
      "status": "PASS",
      "evidence": {
        "kind": "worktree",
        "root": "/Users/bob/git/src/github.com/buvis/ovcaq",
        "git_dir": "/Users/bob/git/src/github.com/buvis/ovcaq/.git",
        "explicit_worktree": false,
        "hooks_path_config": null,
        "hooks_path_foreign": null,
        "status_porcelain_v1_tokens": [
          " M .gitignore",
          " M AGENTS.md",
          " M CHANGELOG.md",
          " M README.md",
          " M docs/dev/project-management/autopilot/autocodex-metrics.jsonl",
          " M docs/dev/project-management/autopilot/autocodex-sessions/8929523ac3b54a80883b21e7d1e895cb.jsonl",
          "?? CLAUDE.md",
          "?? docs/dev/architecture/",
          "?? docs/dev/project-management/autopilot/reports/autocodex-3079b0d199bc415c87045893458e98d8-state-final.json",
          "?? docs/dev/project-management/reviews/20261017-structure-repo.md",
          "?? mise.toml",
          "?? tools/"
        ],
        "status_truncated": false
      }
    },
    {
      "check": "nonempty-README.md",
      "status": "PASS",
      "evidence": {
        "kind": "file",
        "bytes": 2307
      }
    },
    {
      "check": "nonempty-AGENTS.md",
      "status": "PASS",
      "evidence": {
        "kind": "file",
        "bytes": 5032
      }
    },
    {
      "check": "claude-imports-AGENTS.md",
      "status": "PASS",
      "evidence": {
        "path": "/Users/bob/git/src/github.com/buvis/ovcaq/CLAUDE.md",
        "kind": "file",
        "bytes": 11,
        "imports_adjacent_agents": true
      }
    },
    {
      "check": "local-hooks-path",
      "status": "PASS",
      "evidence": {
        "hooks_path_config": null,
        "foreign_hooks_path": null
      }
    },
    {
      "check": "untracked-docs/dev/tmp",
      "status": "PASS",
      "evidence": {
        "count": 0,
        "paths": []
      }
    },
    {
      "check": "untracked-.agents/autopilot/runtime",
      "status": "PASS",
      "evidence": {
        "count": 0,
        "paths": []
      }
    },
    {
      "check": "migrated-dev/bin",
      "status": "PASS",
      "evidence": {
        "supersedes": "retired in favor of tools/ with its callers (layout.md)",
        "count": 0,
        "paths": []
      }
    },
    {
      "check": "migrated-dev/local",
      "status": "PASS",
      "evidence": {
        "supersedes": "classify into tracked intake/specs instead of a dev/work bucket",
        "count": 0,
        "paths": []
      }
    },
    {
      "check": "migrated-docs/dev/project-management/autopilot",
      "status": "DEVIATION",
      "evidence": {
        "deviation_reason": "Deferred: external Autopilot still reads and writes legacy paths; modified session evidence is preserved",
        "would_fail": {
          "supersedes": "Autopilot records -> .agents/autopilot/records; runtime -> ignored .agents/autopilot/runtime (layout.md Workflow storage)",
          "count": 1809,
          "paths": [
            "docs/dev/project-management/autopilot/autocodex-metrics.jsonl",
            "docs/dev/project-management/autopilot/autocodex-monitor-20261002.log",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-catchup-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-devon2-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-ivan-1-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-ivan-1-repair-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-ivan2-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-ivan2_status-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-ivan3-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-recovery-viewer-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-rework-coordinator-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-rework-task4-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-rework-task4-regression-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-task-1-harness-repair-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-tess-1-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/00054-tess2-model-metadata.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/012c688e90954d18a912bbdeb51b151a.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/012c688e90954d18a912bbdeb51b151a.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/012c688e90954d18a912bbdeb51b151a.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/02854dcbda424fc58348d2d88156aaee.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/02854dcbda424fc58348d2d88156aaee.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/02854dcbda424fc58348d2d88156aaee.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/045fde1484e14b8b8bc66f91f0cfb716.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/045fde1484e14b8b8bc66f91f0cfb716.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/045fde1484e14b8b8bc66f91f0cfb716.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/0546a84322624e92b26e0d21b7a56949.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/0546a84322624e92b26e0d21b7a56949.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/0546a84322624e92b26e0d21b7a56949.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/065f64391bde4a0290aafc5421e164be.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/065f64391bde4a0290aafc5421e164be.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/065f64391bde4a0290aafc5421e164be.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/0a0ad0956e034d629d57f5b4bbfce36c.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/0a0ad0956e034d629d57f5b4bbfce36c.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/0a0ad0956e034d629d57f5b4bbfce36c.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/0a46fa8052f7444987f8629e29f47322.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/0a46fa8052f7444987f8629e29f47322.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/0a46fa8052f7444987f8629e29f47322.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/0bbf497227074b799ab13ae6790d0ff3.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/0bbf497227074b799ab13ae6790d0ff3.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/0bbf497227074b799ab13ae6790d0ff3.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/0cacb903373a4431a2fb47cb08d28f10.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/0cacb903373a4431a2fb47cb08d28f10.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/0cacb903373a4431a2fb47cb08d28f10.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/0d334e60760d4f2db6e89cb7150bc3ce.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/0d334e60760d4f2db6e89cb7150bc3ce.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/0d334e60760d4f2db6e89cb7150bc3ce.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/0e748dfbdd5549bfbb581d5d799532b0.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/0e748dfbdd5549bfbb581d5d799532b0.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/0e748dfbdd5549bfbb581d5d799532b0.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/0f59b7ce39c34d3ea69139982423ab51.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/0f59b7ce39c34d3ea69139982423ab51.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/0f59b7ce39c34d3ea69139982423ab51.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/0fdb13bd8661495e80d023565e3172c5.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/0fdb13bd8661495e80d023565e3172c5.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/0fdb13bd8661495e80d023565e3172c5.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/10237614757641a09ca725241545a81c.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/10237614757641a09ca725241545a81c.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/10237614757641a09ca725241545a81c.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/13c1b182ab7347c4b94b06f686d01813.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/13c1b182ab7347c4b94b06f686d01813.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/13c1b182ab7347c4b94b06f686d01813.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/170c1c32f262406f981e8006c63f5ee2.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/170c1c32f262406f981e8006c63f5ee2.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/170c1c32f262406f981e8006c63f5ee2.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/170d39bb82b540169f2519b5c012977c.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/170d39bb82b540169f2519b5c012977c.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/170d39bb82b540169f2519b5c012977c.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/179bb795f48e41a7859c71d628a6e4e7.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/179bb795f48e41a7859c71d628a6e4e7.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/179bb795f48e41a7859c71d628a6e4e7.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/183a3ed8effa4cc3a91fbc188c4fecca.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/183a3ed8effa4cc3a91fbc188c4fecca.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/183a3ed8effa4cc3a91fbc188c4fecca.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/1e55aa51866349ccbfa01e5db4c14b2b.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/1e55aa51866349ccbfa01e5db4c14b2b.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/1e55aa51866349ccbfa01e5db4c14b2b.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/1f85cf62a86149b4942d816fdf2a4d5a.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/1f85cf62a86149b4942d816fdf2a4d5a.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/1f85cf62a86149b4942d816fdf2a4d5a.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/20e00488d69c4049841e98345186f7e4.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/20e00488d69c4049841e98345186f7e4.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/20e00488d69c4049841e98345186f7e4.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/21941351347a436980547ee47d03be03.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/21941351347a436980547ee47d03be03.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/21941351347a436980547ee47d03be03.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/225615a4c35d4b4ea088a39f8b0092a7.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/225615a4c35d4b4ea088a39f8b0092a7.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/225615a4c35d4b4ea088a39f8b0092a7.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/2303ccc5b01245068532eb7de2c5039a.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/2303ccc5b01245068532eb7de2c5039a.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/2303ccc5b01245068532eb7de2c5039a.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/24af2b81b79a4dc09cbf11a70c1838d1.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/24af2b81b79a4dc09cbf11a70c1838d1.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/24af2b81b79a4dc09cbf11a70c1838d1.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/279781a2783542beaaa8681f17114874.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/279781a2783542beaaa8681f17114874.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/279781a2783542beaaa8681f17114874.stderr",
            "docs/dev/project-management/autopilot/autocodex-sessions/2b09597908e04fc9b2b1f1280915d888.jsonl",
            "docs/dev/project-management/autopilot/autocodex-sessions/2b09597908e04fc9b2b1f1280915d888.prompt.md",
            "docs/dev/project-management/autopilot/autocodex-sessions/2b09597908e04fc9b2b1f1280915d888.stderr"
          ]
        }
      }
    },
    {
      "check": "migrated-docs/dev/project-management/prds",
      "status": "DEVIATION",
      "evidence": {
        "deviation_reason": "Deferred: OVCAQ and external Autopilot consume PRD status buckets; spec-bundle support is required first",
        "would_fail": {
          "supersedes": "PRD buckets retire into intake/ and specs/ (layout.md)",
          "count": 56,
          "paths": [
            "docs/dev/project-management/prds/done/00002-package-baseline-v1.md",
            "docs/dev/project-management/prds/done/00003-state-kernel-v1.md",
            "docs/dev/project-management/prds/done/00004-workflow-core-v1.md",
            "docs/dev/project-management/prds/done/00005-runtime-substrate-v1.md",
            "docs/dev/project-management/prds/done/00006-events-claude-adapter-v1.md",
            "docs/dev/project-management/prds/done/00007-supervisor-loop-v1.md",
            "docs/dev/project-management/prds/done/00008-tui-python-launcher-v1.md",
            "docs/dev/project-management/prds/done/00009-codex-adapter-v1.md",
            "docs/dev/project-management/prds/done/00051-triage-a-single-valid-codex-record-can-crash-th-v1.md",
            "docs/dev/project-management/prds/done/00053-adapter-operational-corrections-v1.md",
            "docs/dev/project-management/prds/done/00054-activity-projection-corrections-v1.md",
            "docs/dev/project-management/prds/hold/00010-plugin-provisioning-v1.md",
            "docs/dev/project-management/prds/hold/00011-personal-cutover-v1.md",
            "docs/dev/project-management/prds/hold/00012-generic-driver-api-v1.md",
            "docs/dev/project-management/prds/hold/00013-linux-support-v1.md",
            "docs/dev/project-management/prds/hold/00014-public-release-v1.md",
            "docs/dev/project-management/prds/hold/00015-triage-r12-01-process-exit-after-runtime-ancest-v1.md",
            "docs/dev/project-management/prds/hold/00016-triage-an-ancestor-replaced-after-its-confirmat-v1.md",
            "docs/dev/project-management/prds/hold/00017-triage-confirmed-ancestor-identities-are-discar-v1.md",
            "docs/dev/project-management/prds/hold/00018-triage-replacing-an-already-confirmed-ancestor-v1.md",
            "docs/dev/project-management/prds/hold/00019-triage-fleet-entry-reads-are-not-identity-bound-v1.md",
            "docs/dev/project-management/prds/hold/00020-triage-signal-handling-only-raises-an-exception-v1.md",
            "docs/dev/project-management/prds/hold/00021-triage-three-code-paths-now-pick-the-state-file-v1.md",
            "docs/dev/project-management/prds/hold/00022-triage-apply-purge-opens-the-original-runtime-d-v1.md",
            "docs/dev/project-management/prds/hold/00023-triage-aggregate-purge-reads-each-newline-delim-v1.md",
            "docs/dev/project-management/prds/hold/00024-triage-fleet-registry-reads-follow-symlinks-the-v1.md",
            "docs/dev/project-management/prds/hold/00025-triage-fleet-operations-follow-a-replaced-or-sy-v1.md",
            "docs/dev/project-management/prds/hold/00026-triage-normal-exit-collection-closes-the-group-v1.md",
            "docs/dev/project-management/prds/hold/00027-triage-workflow-prd-and-state-paths-bypass-cont-v1.md",
            "docs/dev/project-management/prds/hold/00028-triage-symlink-rejection-extends-to-trust-ancho-v1.md",
            "docs/dev/project-management/prds/hold/00029-triage-session-publication-checks-paths-and-the-v1.md",
            "docs/dev/project-management/prds/hold/00030-triage-status-never-consults-fleetregistry-so-r-v1.md",
            "docs/dev/project-management/prds/hold/00031-triage-active-session-detection-validates-metad-v1.md",
            "docs/dev/project-management/prds/hold/00032-triage-doctor-omits-required-permission-writabi-v1.md",
            "docs/dev/project-management/prds/hold/00033-triage-read-only-observations-take-the-exclusiv-v1.md",
            "docs/dev/project-management/prds/hold/00034-triage-no-completion-operation-removes-ephemera-v1.md",
            "docs/dev/project-management/prds/hold/00035-triage-the-reducer-binds-identity-only-on-start-v1.md",
            "docs/dev/project-management/prds/hold/00036-triage-failure-classification-misses-standard-a-v1.md",
            "docs/dev/project-management/prds/hold/00037-triage-normalized-sanitization-preserves-arbitr-v1.md",
            "docs/dev/project-management/prds/hold/00038-triage-high-the-claude-adapter-implements-fallb-v1.md",
            "docs/dev/project-management/prds/hold/00039-triage-h1-h4-h5-m1-rate-limit-semantics-allowed-v1.md",
            "docs/dev/project-management/prds/hold/00040-triage-capability-failure-leaves-batch-status-a-v1.md",
            "docs/dev/project-management/prds/hold/00041-triage-retry-budgets-can-be-dodged-forever-supe-v1.md",
            "docs/dev/project-management/prds/hold/00042-triage-no-production-code-ever-starts-a-batch-n-v1.md",
            "docs/dev/project-management/prds/hold/00043-triage-projectobserver-follows-runtime-events-j-v1.md",
            "docs/dev/project-management/prds/hold/00044-triage-normal-supervisor-cleanup-removes-the-se-v1.md",
            "docs/dev/project-management/prds/hold/00045-triage-the-textual-timer-executes-registry-snap-v1.md",
            "docs/dev/project-management/prds/hold/00046-triage-active-duration-is-calculated-by-summing-v1.md",
            "docs/dev/project-management/prds/hold/00047-triage-json-run-without-no-tui-is-silently-disp-v1.md",
            "docs/dev/project-management/prds/hold/00048-triage-raw-only-crash-detection-cannot-work-the-v1.md",
            "docs/dev/project-management/prds/hold/00049-triage-pause-and-resume-verify-run-identity-bef-v1.md",
            "docs/dev/project-management/prds/hold/00050-triage-if-the-selected-supervisor-completes-dur-v1.md",
            "docs/dev/project-management/prds/hold/00052-triage-the-exact-version-pin-rejects-the-codex-v1.md",
            "docs/dev/project-management/prds/hold/00055-triage-the-review-1-two-pass-bounded-detail-lea-v1.md",
            "docs/dev/project-management/prds/hold/00056-triage-numeric-diagnostics-now-need-http-http-s-v1.md",
            "docs/dev/project-management/prds/implementation-plan-coverage.md"
          ]
        }
      }
    },
    {
      "check": "migrated-docs/dev/project-management/runs",
      "status": "PASS",
      "evidence": {
        "supersedes": "no runs/ category; use reviews/ by scope linked to records (layout.md)",
        "count": 0,
        "paths": []
      }
    },
    {
      "check": "executable-tools/onboard",
      "status": "PASS",
      "evidence": {
        "kind": "file",
        "bytes": 122
      }
    },
    {
      "check": "executable-tools/check",
      "status": "PASS",
      "evidence": {
        "kind": "file",
        "bytes": 120
      }
    },
    {
      "check": "executable-tools/format",
      "status": "PASS",
      "evidence": {
        "kind": "file",
        "bytes": 121
      }
    },
    {
      "check": "executable-tools/run-tests",
      "status": "PASS",
      "evidence": {
        "kind": "file",
        "bytes": 124
      }
    },
    {
      "check": "executable-tools/build",
      "status": "PASS",
      "evidence": {
        "kind": "file",
        "bytes": 120
      }
    }
  ],
  "deviations": {
    "migrated-docs/dev/project-management/autopilot": "Deferred: external Autopilot still reads and writes legacy paths; modified session evidence is preserved",
    "migrated-docs/dev/project-management/prds": "Deferred: OVCAQ and external Autopilot consume PRD status buckets; spec-bundle support is required first"
  },
  "not_applicable": {},
  "nested_scanned": true,
  "nested_scopes": [],
  "limitations": [
    "Checks core docs, Git boundary, tracked scratch/runtime, superseded layout, known links and shim modes.",
    "Without --nested, checks the root Claude bridge only. With --nested, also checks each tracked maintained nested AGENTS.md scope, excluding ignored/untracked scratch (including docs/dev/tmp), vendored/generated trees and fixtures; it reports gaps and never writes a nested bridge.",
    "local-hooks-path fails when core.hooksPath is an absolute path outside this worktree and its Git dir (a copied/relocated checkout pointing at the source). It does not prove hooks are installed or run, only that the configured path is local.",
    "migrated-<path> fails while a superseded layout is still tracked; it does not verify the content reached its new home, only that the old location is no longer committed.",
    "Import checks do not prove host loading under the session's settings/exclusions.",
    "No task/hook/release execution or approval/path-consumer validation.",
    "DEVIATION marks a FAIL waived under Fit; it does not fail the gate but is not a PASS.",
    "NOT-APPLICABLE marks a FAIL the operator declared out of scope for this repo kind (for example, no AGENTS.md so no bridge applies); it never auto-infers and must be requested per check, so it cannot silently hide a defect.",
    "A PASS gate is structural only: it is not evidence that hooks, releases, host instruction loading or workflow recovery actually work. COMPLETE still requires the mode reference's operational evidence."
  ]
}
```
