# OVCAQ one-way personal cutover

## Three-layer requirements — 2026-10-25

This PRD remains held. [Architecture authority](../../designs/autopilot-optional-supervision.md) supersedes older ownership/packaging wording below: workflow state/lifecycle/lanes/review/records belong to Autopilot's controller; session/process/collaboration and operations API to OVCAQ; TUI presentation to Tower. All historical state-command criteria below are satisfied through that controller; all TUI criteria through the separate API client. Every original source task/acceptance ID remains required under the reconciled coverage manifest.

Before source retirement require AP00017 standalone stateful evidence, installed same-controller managed transfer and mixed Codex-build/Claude-review canaries, OV00061 wave parity, Tower00003 installed parity and OV00065 headless packaging. Plugin contains one controller but no process supervisor/TUI; OVCAQ contains no workflow writer or presentation. Validate controller-owned record commits, ignored-store no-op and unrelated-index preservation. Retain exact approved-target ledger and all drift/source IDs. No importer or source removal is authorized by this planning edit.

Completeness correction (2026-10-25): consume AP 00012's frozen source inventory and behavior/regression map, with exact replacement artifact digests and passed evidence for every promised profile. Missing or unavailable evidence is not parity. Require AP 00017's real Codex + Gemini standalone and managed Claude-free certificates, including OV 00059/00060 attribution and full lifecycle/continuation/drain evidence; mixed Codex-build/Claude-review alone cannot satisfy that claim. Retain existing compatibility canaries. Source package removal is owned by claude-autopilot held PRD 00370 and its exact approved target ledger; this PRD must not independently delete that package.

## Overview

### Source Contract

Implements Phase 9 source tasks `P09-T01`–`P09-T13` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

OVCAQ is not the personal runtime until both real launchers prove the complete
workflow and the duplicate shell/skill-owned implementation is removed. Because
the current system builds its replacement, deletion must follow recorded canary
evidence rather than confidence or final agent prose.

### Target User

The repository owner needs one installed `ovcaq` runtime, two proven launcher
paths, retained evidence, and no surviving legacy invocation or state writer.

### Success Metrics

- Separate two-PRD Claude and Codex batches prove build, all mandatory review
  lenses, done, next-PRD continuation, final drain, and successful agoge.
- Both canaries retain raw/normalized evidence and pinned capability versions.
- No legacy runtime entry point is removed before both canary gates pass.
- After migration, only one state/runtime implementation and one public command
  family remain; `rg` finds no live old invocation or direct state edit.

## Preconditions and Boundaries

- Depends on completed and independently reviewed PRDs 00002–00010.
- Uses `dev/local/prds/implementation-plan-coverage.md` as the mandatory
  personal-migration closeout checklist; every applicable row needs evidence.
- No legacy autopilot batch may be live; complete or explicitly abandon it.
- Cutover starts fresh OVCAQ state; old state is archived or deleted, not imported.
- No compatibility aliases, dual writes, rollback framework, or public-release
  work. Version control remains the recovery mechanism for deleted tracked code.
- Before mutation, inventory exact OVCAQ, dotfiles, personal-skill, Codex-home,
  state-tree, and launcher-global targets with recovery evidence; broad globs or
  unresolved paths are forbidden.
- After both canaries pass, obtain explicit approval for that target ledger
  before deletion, archival, global instruction edits, or launcher-global apply.

## Functional Decomposition

### Capability: Cutover Preflight

#### Feature: Quiescence and install

Prove no legacy batch/process owns the repository, record current versions and
recovery references, build/install the local MIT-licensed wheel with `uv tool`,
initialize fresh `dev/local/ovcaq`, and run doctor/provision checks.

#### Feature: Canary contract

Canary batches run in a real repository: select four genuinely small backlog
PRDs from a live repo (two per launcher, different PRDs per launcher), each
non-empty, free of autopilot/OVCAQ machinery edits, and recoverable via version
control. Each batch must prove next-PRD
continuation and the complete review phase in a fresh session: consensus/Alice,
blind PRD-only/Blake, and doubt plus de-slop rubric R1–R5/Bob.

### Capability: Independent Launcher Gates

#### Feature: Claude canary

Provision/update compatible Claude workflow/agoge plugins explicitly; run and
record a two-PRD batch through build, every review lens, done, continuation,
drain, agoge, and zero exit.

#### Feature: Codex canary

In a separate fresh batch/state tree, explicitly provision/update Codex content
and prove the identical path. Do not reuse Claude success as Codex evidence.

#### Feature: Evidence gate

For both canaries verify commits/state revisions, review records, raw/normalized
logs, session summaries, metrics, final drained PRDs, batch completion, and
pinned workflow/agoge versions before setting the deletion gate passed.

### Capability: Legacy Runtime Migration

#### Feature: Shell and personal-runtime removal

Remove `tracon`, `autopilot`, and `autoclaude` shell functions and tests; remove
extracted CLI/runtime/tracon code and shims from the personal `run-autopilot`
skill; remove stale Codex personal skill/hook behavior. Keep launcher content
only in external marketplaces. A migration ledger partitions targets by
repository/home owner and records exact paths, recovery reference, action, and
postcondition for each.

#### Feature: Instruction and path migration

Update the user-global instruction source `~/.claude/AGENTS.md` to name
`ovcaq run` and external plugins; never edit its pointer files. Update personal
docs/config/commands and eliminate live `dev/local/autopilot` runtime paths.

#### Feature: Final audit

Verify one writer/runner/TUI, installed arbitrary-cwd operation, no old aliases,
no direct state edits, no production personal paths or `sys.path` bootstraps,
external content absent from the wheel, and all personal-cutover acceptance
checks satisfied.

## Structural Decomposition

```text
OVCAQ repo: docs/operations.md, installed wheel, dev/local/ovcaq evidence
dotfiles: shell launcher/functions/tests and ~/.claude/AGENTS.md
personal skill: ~/.claude/skills/run-autopilot extraction sources/shims
Codex home: stale personal autopilot skill/hook implementation
external marketplaces: retained Claude/Codex workflow and agoge content
```

No new compatibility production module is created by this PRD.

## Dependency Graph

```text
PRDs 00002–00010 reviewed -> quiescent legacy runtime -> install/provision
install/provision -> Claude canary ----+
                  -> Codex canary -----+-> evidence gate -> legacy removal
legacy removal -> instruction/path audit -> personal cutover complete
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Safe Preflight

- [ ] Prove legacy quiescence and record recovery/version references.
- [ ] Install the local wheel, initialize fresh state, and pass doctor checks.
- [ ] Define separate two-PRD canary batches and required evidence checklist.

**Exit Criteria**: Both launchers are ready; legacy code remains intact.

### Phase B: Claude and Codex Canary Gates

- [ ] Provision and run the full two-PRD Claude canary.
- [ ] Verify every review lens, continuation, drain, agoge, logs, and pins.
- [ ] Provision and run a separate full two-PRD Codex canary.
- [ ] Verify the identical evidence contract and record both passing gates.

**Exit Criteria**: Two independent passing gate records exist; no legacy removal
occurred earlier.

### Phase C: One-Way Migration and Audit

- [ ] Freeze the enumerated migration ledger and obtain explicit approval for
  its destructive and launcher-global actions.
- [ ] Remove shell functions/tests and extracted personal runtime/TUI/shims.
- [ ] Remove stale Codex personal skill/hook implementation.
- [ ] Update global source instructions, personal docs, paths, and commands.
- [ ] Archive or delete old state without migration.
- [ ] Run repository/home searches and the full personal acceptance matrix.

**Exit Criteria**: Installed OVCAQ is the sole personal runtime and all old live
entry points/state writers are gone.

## Test Strategy

- Preflight refuses live legacy ownership or incompatible external content.
- Separate Claude/Codex two-PRD canaries with all three review lenses.
- Next-PRD continuation, final drain, agoge success, exit code, evidence, pins.
- Negative deletion gate: either failed canary leaves legacy runtime untouched.
- Post-removal installed CLI/TUI/no-TUI and state/provision/doctor checks.
- `rg` audit of old command names, direct state edits, legacy paths, personal
  bootstraps, and duplicate runtime code.

## Risks

- **Self-hosted deletion**: Require both recorded canary gates first.
- **Launcher false equivalence**: Use separate batches and evidence sets.
- **Instruction drift**: Edit only the global source file, then audit pointers.
- **Hidden legacy caller**: Search code, tests, shell config, hooks, and docs.
- **Evidence loss**: Verify retention before deleting any runtime source.

## Acceptance Criteria

- [ ] Both launcher canaries prove full review, continuation, drain, and agoge.
- [ ] Both retain raw/normalized evidence and pinned compatible versions.
- [ ] All migration-map retire/port/replace dispositions are verified complete.
- [ ] The approved migration ledger accounts for every changed external/home
  target and records its recovery reference and verified postcondition.
- [ ] Exactly one installed state/runtime/TUI implementation remains.
- [ ] Old state is archived/deleted, never imported or dual-written.
- [ ] All personal docs/instructions/commands point to OVCAQ/external plugins.
- [ ] No old aliases, live legacy paths, direct state edits, or bundled external
  content remain.
- [ ] Every personal-cutover acceptance item in the umbrella plan passes.
- [ ] Every Phase 0–9 and migration row in the implementation-plan coverage
  manifest has linked evidence.

## Unresolved Questions

None.
