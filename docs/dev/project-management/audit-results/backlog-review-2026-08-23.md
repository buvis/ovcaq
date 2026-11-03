# Backlog review - ovcaq - 2026-08-23

Verdict: GO — backlog now 00002–00009 after the apply pass (all Blocking
resolved by edits and holds). 00010–00014 parked in `hold/` pending companion
plugin work, attended 00010-C/00011 runs, and post-cutover return of the
public track. Codex plugin→skill delivery spike: **PASSED** (see Decisions
applied).

Scope: `dev/local/prds/backlog/` (13 PRDs, 00002-00014) against the accepted
implementation plan (SHA-256 verified: `43c75d3d…e845a5` matches the coverage
manifest) and the user's stated goal: generalize the autoclaude/autopilot loop
beyond Claude Code.

## Map

| # | PRD | phase | lines | subsystem | depends on | verdict |
|---|-----|-------|-------|-----------|------------|---------|
| 00002 | package-baseline | 0 | 208 | packaging/inventory | - | FIX |
| 00003 | state-kernel | 1 | 188 | state | 00002 | FIX |
| 00004 | workflow-core | 2 | 175 | workflow | 00002-3 | FIX |
| 00005 | runtime-substrate | 3 | 194 | runtime | 00002-4 | FIX |
| 00006 | events-claude-adapter | 4 | 179 | events/drivers | 00002-5 | FIX |
| 00007 | supervisor-loop | 5 | 176 | runtime | 00002-6 | FIX |
| 00008 | tui-python-launcher | 6 | 165 | tui | 00002-7 | FIX |
| 00009 | codex-adapter | 7 | 171 | drivers | 00002-8 | FIX |
| 00010 | plugin-provisioning | 8 | 208 | provision + external repos | 00002-9 | RESHAPE or FIX |
| 00011 | personal-cutover | 9 | 200 | migration (attended) | 00002-10 | RESHAPE (hold/attended) |
| 00012 | generic-driver-api | 10 | 167 | drivers/events | 00002-11 | FIX (or hold) |
| 00013 | linux-support | 11 | 165 | platform | 00002-12 | FIX (or hold) |
| 00014 | public-release | 12 | 199 | release (attended) | 00002-13 | FIX (or hold) |

All PRDs use one consistent house template (standard.md-derived with Source
Contract / Preconditions / Acceptance Criteria additions). All dependencies
point at lower numbers; numbering unique across backlog + discovery; backlog
contains only `NNNNN-slug-vN.md` files. wip/, hold/, done/ do not exist yet.

## Plan-coverage verification (the user's explicit ask)

- Coverage manifest's accepted digest matches the live plan file. Task count
  119 (P00-T01..P12-T08) re-added and confirmed: 8+12+10+11+9+9+10+7+11+13+6+5+8.
- Every phase's source tasks were traced into its owning PRD's features/phases:
  no dropped or diluted task found in any of the 13 PRDs. Notable good catches
  by the PRDs themselves: enforcement-hooks-inside-workflow-plugin (resolves a
  plan §14.1-vs-§14.3 seam), explicit approval gates (plan decision 10), the
  M-row and A-row closeout mapping in 00011/00014.
- Values consistent across plan and PRDs: marketplace `buvis-plugins`, sources
  `buvis/claude-plugins` + `buvis/codex-plugins`, ranges `>=1,<2` / `>=0.1,<1`,
  runtime root `dev/local/ovcaq`, XDG registry, q/p/s controls, failure
  vocabulary, canary shape incl. Alice/Blake/Bob lenses.
- Citation check (check_links): all backlog hits are path literals or declared
  future outputs (`dev/local/ovcaq`, legacy `dev/local/autopilot`,
  `phase-0-reconciliation.md`) - waived as forward references, none dangling.

## Findings

### Blocking

- [00010 + program] **G/H: The companion plugins are the critical path and the
  least-planned artifact in the program.** 00010's exit gates (real Codex
  workflow smoke, agoge smoke per launcher) consume `ovcaq-autopilot` and
  `agoge` releases in BOTH marketplaces that nothing produces:
  `buvis/codex-plugins` holds a README skeleton, `buvis/claude-plugins` has no
  ovcaq-autopilot, and a Codex agoge (7 QA agents) does not exist. The Codex
  workflow plugin must re-express the entire run-autopilot behavior
  (phase gates, three review lenses, recovery, state contract) with Codex-native
  mechanisms whose central assumption - a codex plugin can deliver skill
  instructions into a `codex exec` session - has never been exercised here.
  Fails as: 00010 Phase C stall / program-level dead end discovered after six
  PRDs of runtime are built on the assumption.
  Fix: 1-hour manual spike NOW (local skeleton plugin + `codex plugin add` +
  `codex exec` invoking its skill); open the bounded companion work records
  early (they are already required by 00010's boundaries - pull them forward);
  optionally split 00010 (see Reshapes).
- [00010, 00011, 00013, 00014] **B: Attended checkpoints sit inside an
  unattended backlog; 00011 is self-referential.** 00010-C requires explicit
  approval for real `--apply` + external publication; 00011 requires approval
  of the migration ledger, deletes the very machinery (`autoclaude`,
  run-autopilot skill, bash functions) that would be executing the batch, and
  its canaries are multi-hour `ovcaq run` batches that cannot fit a capped work
  session; 00011's P09-T01 precondition (no live legacy batch) is unsatisfiable
  from inside a legacy batch. 00013-C needs authenticated launchers on Linux;
  00014-C needs release authorization. Fails as: unattended hang / loop
  self-harm / wall-clock cap kill.
  Fix (recommended): drain 00002..00010(A+B) unattended; run 00010-C and 00011
  attended; hold 00012-00014 until cutover passes.
- [00004, 00007] **B/C: The per-agent routing and frontmatter-model contract is
  unpinned and currently Claude-shaped.** Open points a planner will otherwise
  invent: (a) config shape for per-agent per-phase model/effort (plan §7 shows
  only global `[phases.*]`); (b) what `default_model: opus` (a Claude tier) and
  the opus-frontmatter-pin mean when the batch agent is codex; (c) whether the
  codex driver maps `effort` (e.g. `-c model_reasoning_effort=...`) or ignores
  it, and whether ignoring is silent; (d) which layer owns the per-agent prompt
  template (today `/run-autopilot`, tomorrow a namespaced plugin skill).
  Fails as: wrong-TDD lock-in in 00004/00007 and Claude tier names leaking into
  provider-neutral workflow/config, undermining the generalization goal.
  Fix: pin `[agents.NAME.phases.PHASE] model/effort` + per-agent prompt in
  config (00007), and define frontmatter model hints as launcher-scoped
  (ignored with a warning for a non-matching launcher) in 00004.
- [all 13] **A: No task line carries an `Acceptance:` clause.** House style
  uses phase Exit Criteria + PRD-level Acceptance Criteria; plan-tasks copies
  per-task acceptance verbatim and invents one when absent. Fails as:
  wrong-TDD lock-in.
  Fix options: add a one-line "task acceptance = the named Pxx-Tyy source-task
  text plus this phase's exit criteria; copy both verbatim" rule to each PRD
  (cheap, keeps prose tax low; recommended); or write per-task clauses (~119
  lines); or accept the deviation explicitly.

### Non-blocking

- [00009] Failure-family Codex fixtures (rate-limited, permission-failed)
  cannot all be captured live on demand; pin a provenance policy that allows
  documented synthetic fixtures for failure families, marked in provenance.
- [00006] `WARDEN_UNATTENDED` is a third-party personal plugin's env var; the
  claude driver must not hardcode it (today's runner does). Make non-Claude env
  additions per-agent config; driver owns only CLAUDE_* variables.
- [00002] Seed the Phase 0 inventory with known-tricky rows so they cannot be
  missed: `_autopilot_fable_*` bash helpers + `fablectl.py` +
  `ledger/fable-requests.json` (fable rescue flow), the drained-path
  `purge-devlocal` script call in loop.py (`run_purge`), `notify_out` macOS
  notifications, `render_stream.py` presenter fallback chain, hook split
  (validate_state_json / review_coverage / context-cap → external plugin).
- [00002] Add `CHANGELOG.md` to the release skeleton - the standing changelog
  rule blocks every feat/fix commit without it, from Phase A onward.
- [all 13] Template drift vs `create-prd` law (house variant): features lack
  Inputs/Outputs/Behavior fields, no `### Module:` blocks, no layer headings in
  Dependency Graph. Consistent and information-preserving; recorded as accepted
  deviation unless the user wants conformance.

### Questions

- [00011] Canary PRD provenance: where do the two-PRD-per-launcher batches come
  from - purpose-authored trivial PRDs in a scratch repo (recommended: failures
  cannot damage real repos, content launcher-agnostic), this repo's own
  backlog tail, or another live repo?

## Reshapes

- Option (part of Blocking 2): split 00010 into 00010 (manifest, reconcilers,
  CLI/doctor/preflight, fake-CLI tests - loop-drainable) and a new tail PRD
  (external releases + explicit apply + real smokes - attended). Requires
  updating the coverage manifest's phase-ownership row for P08.
- Recommended batch boundary (no file moves in backlog needed except the
  public track): move 00012-00014 to `hold/` until 00011 passes; a human
  returns them. Faithful to the plan ("later track"); prevents autopilot from
  charging into Linux/publication right after cutover.

## Gaps

- No spec exists anywhere for the Codex workflow plugin's review-lens
  orchestration or a Codex agoge; the claude→ovcaq skill rewrite is also
  unsized. These live in external repos by design, but their feasibility gates
  this backlog (see Blocking 1).
- No CHANGELOG (covered above).

## End state after this batch

If 00002-00011 land: one installed `ovcaq` runtime with proven Claude and
Codex paths, legacy shell/skill runtime deleted, evidence retained; the
personal system depends on two external marketplaces it provisions but does
not own. If 00012-00014 also land: a public, Linux-capable, extension-ready
package. Half-finished risk: companion-plugin repos become the new
under-planned frontier - OVCAQ core is exhaustively specified while the
content that makes it useful has no comparable plan.

## Frontmatter tuning

| PRD | suggestion | why |
|-----|-----------|-----|
| 00003 | `design_gate: user` | the v1 schema/crosswalk is a one-way door; vet before tasks |
| 00007 | `rework_cap: 3` | decision-table parity is the hardest convergence in the batch |
| 00010, 00011 | `catchup: force` | launcher-global and external state moves between PRDs |

## Gate honesty

- Lens D (grounding) ran inline across this and the prior study session
  instead of via per-PRD subagents: binaries, flags (`codex` 0.149.0 root/exec
  /plugin/marketplace help, `claude plugin` install/list/marketplace help),
  marketplaces, current-source files/line counts, plan digest, and task-ID
  counts were verified directly. Still unverified: `codex plugin add --json`
  and `claude plugin marketplace list --json` flag shapes (deferred to Phase 8
  tests by the plan itself), live Codex JSONL event names. Closed during the
  apply pass: `codex plugin add <plugin>@<marketplace> --json` and
  `codex plugin marketplace add <local path> --json` verified live by the
  spike; the plan §2.4 OpenAI doc URLs 308-redirect to
  `learn.chatgpt.com/docs/*` (content resolvable — refresh the links when the
  plan is next edited).
- No PRD is already implemented (repo holds only the bootstrap commit); no
  wip/hold overlap (directories absent).

## Decisions applied

1. Companion-plugin risk → **spike now** (chosen); spike executed same day and
   **PASSED**: a local marketplace (`.agents/plugins/marketplace.json`) plus a
   skeleton plugin (`.codex-plugin/plugin.json` + `skills/*/SKILL.md`) was
   added via `codex plugin marketplace add` / `codex plugin add`, and a
   `codex exec` session implicitly selected the plugin-delivered skill from
   its description and followed it exactly (`OVCAQ_SPIKE_DELIVERY_OK`,
   gpt-5.6-sol, 22.9K tokens). Spike installs removed afterwards; zero
   launcher drift. Observations for later PRDs: the plugin cache path is
   `~/.codex/plugins/cache/<mkt>/<plugin>/<version>/`; personal `~/.codex`
   hooks (gateguard) actively interpose in codex sessions, so 00011's stale
   codex-hook cleanup is load-bearing for workflow reliability; the
   `codex-plugins` repo already carries the correct marketplace/plugin
   manifest shapes. QUEUED: open the bounded companion work records in
   `buvis/claude-plugins` and `buvis/codex-plugins` before OVCAQ build starts
   (00010 mandates them; do not wait for 00010).
2. Batch boundary → **hold 00010–00014**: moved to `dev/local/prds/hold/`;
   unattended batch is 00002–00009; 00010-C and 00011 run attended; 00012–14
   return after cutover. APPLIED (mv).
3. Routing contract → **neutral tiers**: abstract tier keys in frontmatter and
   `[phases.*]`; `[agents.NAME.tiers]` maps tiers to provider models;
   per-agent phase overrides and prompt template; neutral effort scale mapped
   by drivers, never silently dropped. APPLIED to 00004, 00006, 00007, 00009.
4. Task acceptance → **bridging rule** added to all 13 PRDs: task acceptance =
   verbatim `Pxx-Tyy` source text + owning phase exit criteria. APPLIED.
5. Canary provenance → **small real-repo PRDs**: selection criteria pinned in
   00011 (four small backlog PRDs from a live repo, two per launcher,
   machinery-free, git-recoverable). APPLIED.
6. Non-blocking batch → APPLIED: 00009 fixture provenance (synthetic failure
   families allowed, marked), 00006 warden-env-to-config, 00002 inventory
   seed + CHANGELOG.md. Template drift: no action chosen; stays recorded as an
   open non-blocking observation (not marked accepted).

Note: the neutral-tiers refinement stays compatible with plan §9 ("routing is
runtime configuration keyed by phase"); the plan file itself was not edited, so
the accepted digest in the coverage manifest remains valid.
