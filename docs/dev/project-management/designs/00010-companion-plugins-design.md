# Companion-plugin design (PRD 00010 external content)

## 2026-10-25 three-layer architecture amendment

The user's latest design supersedes both previous boundary corrections. External Autopilot owns skills/hooks/review preparation plus one canonical workflow controller: state, lifecycle, tasks, code-selected lanes, review/custody/verification acceptance and record commits. Standalone use is stateful, with manually started isolated sessions. OVCAQ owns headless session/process orchestration, role-to-driver placement, collaboration/waves/worktrees and the operations API. Tower owns terminal presentation as a separate API client.

[Canonical contract and delivery graph](../designs/autopilot-optional-supervision.md) governs conflicting ownership/packaging statements in the historical source plan below. Reuse the tested existing workflow services in Autopilot; never implement two writers or synchronize duplicate workflow state. Separate execution journal belongs to OVCAQ. Codex-build/Claude-review, manual-to-managed lease transfer and UI-crash survival are required canaries. No bundled plugin/controller/TUI content in final OVCAQ.

The original P00–P12, M01–M23 and A01–A15 IDs and behavior obligations remain intact. Their original locations below are historical decomposition, not authority to restore old ownership. Coverage reconciliation assigns extraction evidence to AP00018–00021, orchestration to OV00057–00061, API/headless packaging to OV00064/00065 and presentation to Tower00001–00003. Held provisioning/cutover/release need all relevant artifacts; no hold, live installation, publication or source removal is activated. Agoge remains required.

Scope: the external launcher content PRD 00010 consumes — the `ovcaq-autopilot`
workflow plugins for Claude Code and Codex, the Codex `agoge` capability, and
the claude-agoge compatibility release. Drawn forward from PRD 00010 per the
2026-08-23 backlog-review decision so feasibility and contracts are pinned while
PRDs 00002–00004 build. This doc feeds the bounded work records in
`buvis/claude-plugins`(-indexed repos) and `buvis/codex-plugins`; it is an input
to PRD 00010's own later design pass, not a replacement for it. It never
redefines PRD acceptance criteria.

Feasibility basis: the 2026-08-23 spike proved codex plugin→skill delivery end
to end (`.agents/plugins/marketplace.json` marketplace, `.codex-plugin/
plugin.json` plugin, `skills/<name>/SKILL.md` skill, implicit selection by
description inside `codex exec`, cache at
`~/.codex/plugins/cache/<mkt>/<plugin>/<version>/`).

## Architecture fit

OVCAQ core (plan §4) owns state, workflow verbs, supervision, drivers, events,
TUI, and provisioning. Everything the agent is *told to do* inside a session —
phase procedures, review lenses, recovery choreography, QA packs — is launcher
content in external marketplaces. The only coupling is the versioned `ovcaq`
CLI/state protocol (`docs/state-protocol.md` once PRD 00003 lands) plus the
driver prompt that invokes the installed skill. Four deliverables sit on that
boundary:

1. `ovcaq-autopilot` for Claude Code — port of the personal run-autopilot skill
   family, rewritten from `statectl`/`autopilot` to `ovcaq` verbs.
2. `ovcaq-autopilot` for Codex — native re-expression of the same workflow and
   state protocol with codex-child review lenses.
3. `agoge` for Codex — port of the claude-agoge QA pack to codex-native
   execution.
4. claude-agoge — verified compatible as released: 0.1.1's `--authorized`
   accepts any single-word token (the gate is skill prose, not a whitelist), so
   `ovcaq-drain` works as-is. At most a docs example lands later; no release is
   required or gated on.

## Module placement

New repository `buvis/claude-ovcaq-autopilot` (mirrors the released-plugin
convention of claude-agoge/claude-aegis; indexed by URL from
`buvis/claude-plugins` `.claude-plugin/marketplace.json`):

```text
claude-ovcaq-autopilot/
├── .claude-plugin/{plugin.json,marketplace.json}   # name "ovcaq-autopilot", 1.0.0
├── CHANGELOG.md, README.md, LICENSE
├── skills/
│   ├── run-autopilot/{SKILL.md,references/*.md,prompts/de-sloppify.md}
│   ├── design-solution/SKILL.md
│   ├── plan-tasks/{SKILL.md,references/*.md,scripts/list-prds.sh}
│   ├── work/{SKILL.md,references/*.md}
│   ├── review-work-completion/{SKILL.md,references/*.md,scripts/*}
│   └── review-blindly/{SKILL.md,references/rubric.md}
├── agents/{alice,blake,bob,carl,eve,ivan,pat}.md
├── hooks/{hooks.json,validate_state_json_hook.py,review_coverage_hook.py,
│          reinject_contract_card.py,tests/}   # context-cap hook retired (C6.9)
├── scripts/{gate.py,await_reviewer_outputs.py,gather-context.sh,
│            compute_mech_facts.py,consolidate_findings.py,
│            codex-run.sh,gemini-run.sh}
└── dev/bin/{release,release-checks}                # copied release tooling
```

Existing repository `buvis/codex-plugins` (monorepo marketplace, entries in
`.agents/plugins/marketplace.json`; flip `policy.installation` off
`NOT_AVAILABLE` at release):

```text
codex-plugins/plugins/
├── ovcaq-autopilot/                                # 1.0.0
│   ├── .codex-plugin/plugin.json                   # exists (skeleton)
│   └── skills/ovcaq-autopilot/
│       ├── SKILL.md                                # gate dispatch + protocol
│       ├── references/{phase-build.md,phase-review.md,phase-done.md,
│       │               recovery.md,decision-framework.md,state-protocol.md}
│       ├── prompts/{consensus.md,blind.md,doubt.md,de-sloppify.md}
│       └── scripts/{gate.py,consolidate_findings.py,compute_mech_facts.py}
└── agoge/                                          # 0.1.0
    ├── .codex-plugin/plugin.json
    └── skills/run-agoge/
        ├── SKILL.md                                # recon → armed lanes → report
        ├── prompts/{olivia,walter,heidi,judy,wendy,peggy,trudy}.md
        ├── references/{finding-contract.md,*-playbook.md,prd-emission.md}
        └── scripts/allocate_prd_number.py
```

Existing repository `buvis/claude-agoge`: no change required. The released
0.1.1 authorization gate is skill prose that accepts any single-word
`--authorized` token and treats an absent token as unarmed-QA, not an error —
`ovcaq-drain` is accepted as-is (verified against its SKILL.md and
`test_agoge_authorization_gate.py`).

Nothing lands in the OVCAQ package; PRD 00010's wheel audit stays valid.

## Interfaces & contracts

### C1. Plugin↔OVCAQ session protocol (both launchers, verbatim for skill text)

1. Preamble: run `ovcaq state show --json`; require exit 0,
   `schema_version == 1`, AND `cli_protocol == 1` (C6.11 — schema alone does
   not prove verb semantics). On failure: report and end the session with no
   repository changes.
2. Compound verbs for everything that has one; the generic
   `state set/append/delete` touch ONLY leaf fields on the state-protocol
   doc's agent-writable allowlist (C6.7). Lifecycle and transition-owned
   fields are protected by the STORE (rejected without `--unsafe`, plan §6),
   not by prose; `--unsafe` is never used. Never edit `state.json` (or its
   `.bak`/`.lock`) with any file tool.
3. Exactly one `ovcaq workflow phase-complete --outcome <outcome>` per session
   at the hand-off, with `<outcome>` one of `tasks_done | rework | converged |
   more_prds | drained`; the legal (phase, outcome) pairs are plan §9's
   transition table and the store rejects any other pair — prose is never the
   guard. End the session after it succeeds. Carve-out: a session the
   supervisor terminates (wall-clock timeout or usage cap, C6.9) ends without
   a `phase-complete`; the supervisor owns the resulting state.
4. State-write failure: before any retry, re-read `ovcaq state show --json` —
   if the mutation is already visible (the command committed before the error
   reached the caller), do NOT re-issue it. Retry a genuinely unapplied
   command once; `phase-complete` retries additionally pass the pre-attempt
   `revision` as compare-and-set so a duplicated transition is rejected by the
   store. Still failing → stop immediately: no further edits, no reverts, no
   cleanup; end the session (plan §8.5: two failed attempts stop the session
   — "leave the repository unchanged" means take no further action, not
   revert; uncommitted work-in-progress stays in place for the operator).
   `ovcaq state restore` is an operator/supervisor recovery tool; the agent
   never invokes it. No marker files.
5. Unattended detection: environment `OVCAQ_UNATTENDED=1` (set by the
   supervisor on every launched session) replaces `$_AUTOPILOT_LOOP` and
   `CLAUDE_UNATTENDED` in all skill branching (AskUserQuestion ban, push
   deferral, stall-instead-of-pause).
6. Paths: the skill never resolves the state file; `ovcaq` resolves the
   project from cwd. Agent-visible runtime files are only those
   `docs/state-protocol.md` documents: `dev/local/ovcaq/replan-context.md` and
   `dev/local/ovcaq/contract-card.md` (agent-written scratch), read-only
   `dev/local/ovcaq/reports/` and `dev/local/ovcaq/deferred/`, plus the repo's
   `dev/local/tmp/` staging area for session-scoped scratch under an
   `ovcaq-<runid>-` name prefix. Scratch holds prompts and intermediates only
   — never the sole copy of evidence (C4's lens raw outputs are saved
   durably first) — and is bounded by supervisor-owned GC (C6.13), not by
   convention.

### C2. Command mapping (old → new, exhaustive for the skill rewrite)

| Current call | Plugin calls |
|---|---|
| `statectl.py <f> get/set/append/del PATH VAL` | `ovcaq state get/set/append/delete PATH JSON` (documented agent-writable paths only) |
| `statectl.py <f> task-add FILE` | `ovcaq state task add FILE` (prints id) |
| `task-start/task-done ID` | `ovcaq state task start ID` / `ovcaq state task complete ID FILE` |
| `task-set-body/set-meta/set-status` | `ovcaq state task set-body/set-meta/set-status` |
| `tasks-clear` | `ovcaq state task clear` |
| `append-attempt ID FILE` | `ovcaq state task attempt ID FILE` |
| `set-contract-card FILE` | `ovcaq state contract set FILE` |
| `complete-prd NAME` | `ovcaq workflow complete-prd --prd NAME` |
| `autopilot phase-done --outcome O` | `ovcaq workflow phase-complete --outcome O` |
| `autopilot select` | `ovcaq workflow select` (JSON `{prd, source}`; verified move semantics per PRD 00004) |
| `autopilot frontmatter --prd P` | `ovcaq workflow frontmatter --prd P` |
| `autopilot resume-target` | `ovcaq workflow resume-target` |
| `autopilot check-plan` | `ovcaq workflow check-plan` |
| `autopilot stall/park` | `ovcaq workflow stall --prd N --site S --detail T` / `ovcaq workflow park` |
| `autopilot defer --prd --batch --json` | `ovcaq workflow defer --prd NAME --record FILE` |
| `autopilot render audit\|report\|metrics` | `ovcaq workflow render audit\|report\|metrics` |
| `autopilot restore` | retired skill-side — `ovcaq state restore` is operator/supervisor recovery only (C1.4); the skill's restore-and-retry choreography does not survive the port |
| `autopilot init` | `ovcaq init` |
| `autopilot status` | `ovcaq status [--json]` |
| `autopilot gate --review-file …` | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate.py --review-file …` (plugin-owned; see C6) |
| `autopilot reset-prd` (crash recovery) | retired — `ovcaq workflow park` reconciles the `recovery.operation` saga |
| `autopilot_context_cap_hook.py` state writes (`cap_rotations` append, in-flight task reset, `next_phase`) | retired — supervisor-owned usage cap and rotation (C6.9) |
| `fablectl.py …` (fable rescue) | retired in v1 (escalation exhausted → stall, unchanged path) |
| `notify.py --send …` | retired skill-side — supervisor owns notifications (P05-T05) |
| marker files (`pause-requested`, `paused-by-operator`, `state-write-failed`, `park-requested`) | retired — `ovcaq pause`/typed state/C1.4 |
| `loop-metrics.jsonl` appends (`review_converged` row) | retired — review history lives in state; `ovcaq workflow render metrics` derives it |
| `installed_plugins.json` read for `batch.plugin_versions` pin | retired skill-side — core batch pinning (plan §14.3) |

### C3. Driver prompt defaults (per-agent config, overridable)

- claude: `/ovcaq-autopilot:run-autopilot`
- codex: `Run one OVCAQ autopilot phase handoff for this repository using the
  ovcaq-autopilot skill.` (implicit selection by description — proven by the
  spike; the skill description is exactly `Use when asked to run one OVCAQ
  autopilot phase handoff.`)

### C4. Codex review lenses (codex plugin, phase-review)

Each cycle runs three isolated child sessions from the workflow session, one
per lens, sequentially, output via `-o`:

```text
codex --ask-for-approval never exec --sandbox read-only -C <repo> \
  -o dev/local/tmp/<lens>-output-<id>.txt - < dev/local/tmp/<lens>-prompt-<id>.md
```

- Lenses and prompt sources: consensus (`prompts/consensus.md`, diff+PRD+tasks
  +mechanical-facts+ledger), blind (`prompts/blind.md`, PRD+rubric only),
  doubt (`prompts/doubt.md`, doubt rubric D1–D5 + de-slop). Same consolidation
  contract as Claude's `consolidate_findings.py` (bundled), same ledger and
  convergence rules (no unresolved CRITICAL/HIGH), same review-file shape
  checked by the bundled `gate.py`.
- Lens-output integrity and evidence: each child writes `-o` to
  `…-<lens>-output-<id>.txt.part`; the skill validates the output against the
  lens-output contract (reviewer section shape + verdict lines) and only then
  renames it to its final name — a lens output counts as complete ONLY by
  passing that validation for the current cycle/lens identity, never by file
  existence, so a TERM'd partial write is re-run. Before consolidation
  cleanup, each validated raw lens output is copied durably to
  `dev/local/reviews/<prd-stem>-lens-<cycle>-<lens>.txt` (review satellites,
  retained like review files) — child-session raw evidence survives
  normalization, honoring the plan's raw-evidence invariant for sessions the
  supervisor cannot tee.
- Sandbox precondition (PROBED 2026-08-23, both directions): a nested
  `codex exec` child inside a `workspace-write` sandbox FAILS — "failed to
  initialize in-process app-server client: Operation not permitted" — even
  with `-c sandbox_workspace_write.network_access=true`; the identical nested
  call under an unsandboxed outer session succeeds (`NESTED_CODEX_OK`, 7s).
  Therefore the codex REVIEW-phase session (and the agoge capability session,
  C5) runs with an explicit per-phase config opt-in —
  `[agents.codex.phases.review] sandbox = "danger-full-access"` — surfaced by
  a loud driver preflight, exactly the treatment plan §15 gives Claude's
  unattended permissions. This is an explicit operator configuration, never a
  default (§15 forbids only the default); build/done phases keep
  `workspace-write`. The public-track evolution that restores sandboxing is
  supervisor-mediated lens sub-sessions (the supervisor, already the process
  owner, runs the lens children itself); recorded for PRD 00012+.
- Bundled-script resolution (PROBED 2026-08-23): a skill script executed from
  the versioned plugin cache by skill-directory-relative path
  (`sh …/skills/<skill>/scripts/probe.sh` → `BUNDLED_SCRIPT_OK`) under the
  default read-only sandbox. C4 gating and the agoge scripts rest on a proven
  mechanism.
- v1 limitation (recorded): all three lenses run on codex models — no
  cross-model diversity on the codex driver. The lens *contract* (consensus,
  blind, doubt-rubric) is preserved; adding external-CLI reviewers to the codex
  plugin is a later minor release.

### C4a. Claude review lenses (claude plugin)

The ported review-work-completion keeps its proven external-CLI roster and
degradation contract, now stated as part of this design: Bob (doubt) runs on
the bundled `codex-run.sh` when `codex` resolves on PATH, with the ported
Claude-subagent fallback so the doubt lens NEVER silently drops; Carl (UI) runs
on `gemini-run.sh` only when a gemini/copilot CLI resolves, else he is skipped
and noted in the review file; both are preflighted exactly as the source
skill's step 1 does today. Neither CLI is a plugin requirement: with both
absent, every mandatory lens (consensus, blind, doubt) still runs on Claude
subagents. Claude's Bash is permission-gated, not kernel-sandboxed, so the C4
nested-sandbox failure does not apply on this launcher.

### C5. Codex agoge capability

- Skill `run-agoge` (description: `Use when asked to run authorized agoge
  product QA over this repository.`). Authorization semantics match
  claude-agoge exactly: `--authorized <token>` is a single-word token with no
  whitelist; an ABSENT token is not an error — QA runs with the
  runtime-security lane unarmed; a present token arms it. The gate is skill
  prose plus ported gate tests (claude-agoge's
  `test_agoge_authorization_gate.py` pattern), not a script whitelist.
- Lanes: recon (olivia prompt) plans arming; each armed specialist runs as one
  child `codex exec --sandbox workspace-write` session with its prompt file;
  findings normalize to `references/finding-contract.md`; one report to
  `dev/local/audit-results/`. Because lanes are nested children, the OUTER
  agoge capability session needs the same explicit unsandboxed per-capability
  config opt-in as the review phase (C4 probe result), with the same loud
  preflight.
- Capability invocation prompts (packaged OVCAQ defaults, overridable in
  config; consumed by `runtime/capability.py` through the driver, never a
  shell):
  - claude: `/agoge:run-agoge <repo> --authorized ovcaq-drain`
  - codex: `Run authorized agoge product QA over this repository. Authorization
    token: ovcaq-drain.`
- Sandbox override contract: the codex agoge capability session requires
  `[capabilities.agoge.agents.codex] sandbox = "danger-full-access"` (the
  capability-scoped sibling of C4's `[agents.codex.phases.review]` key; C6.12
  routes both). Absent opt-in FAILS CLOSED: the driver preflight refuses the
  capability attempt with actionable `control.attention` naming the exact
  config key — drained PRDs are preserved and the attempt is retryable after
  the operator opts in.

### C6. Core-contract deltas this design surfaces (route into PRD 00002's
phase-0 reconciliation record; none changes an accepted plan decision)

1. `OVCAQ_UNATTENDED=1` in every supervisor-launched session's environment
   (lands in PRD 00006/00007 launch behavior).
2. Capability invocation prompts per launcher as packaged, overridable config
   (PRD 00007/00010), values in C5.
3. `cli/gate.py` + `review_coverage_hook.py` + `check_review_file.py`
   disposition: external Claude plugin content, not OVCAQ core (PRD 00002
   inventory rows; explains `gate`'s absence from plan §6).
4. `autopilot reset-prd` standalone verb: absorbed by the `recovery.operation`
   saga (PRD 00004 confirms in the crosswalk).
5. Skill-side metric appends retired: v1 `review.cycles` must carry enough per
   -cycle history (cycle number, outcome, deferral count) for
   `ovcaq workflow render metrics` to derive convergence stats (PRD 00003
   crosswalk requirement).
6. Fable-rescue loop machinery (`fablectl.py`, `_autopilot_fable_*`,
   `ledger/fable-requests.json`) retired in v1 (PRD 00002 retirement rows).
7. Agent-writable v1 state the plugins require (PRD 00003 crosswalk inputs):
   task entries via task verbs; review decisions, doubts, rubric verdicts, and
   lens progress; `work.design_doc`; contract card; catchup cache fields
   (`batch.catchup_completed_at`, `batch.catchup_head_sha`). NOT
   `work.repo_root` or `work.work_start_sha` (C6.10), and NOT
   `recovery.replan_count` (C6.14).
8. `git-ferry` stays OUT of the requirement manifest — plan §14.1's four-row
   set and PRD 00010's no-fifth-requirement text stand unchanged. Instead the
   ported catchup step degrades: when `git-ferry:catchup` is installed the
   claude plugin uses it; when absent (and always on codex, which has no
   git-ferry) phase-build runs a native delta refresh — re-read `wip/` PRDs,
   update the capsule's Active Work section, write the
   `batch.catchup_completed_at`/`batch.catchup_head_sha` cache fields — with a
   logged note.
9. Supervisor-owned usage cap replaces `autopilot_context_cap_hook.py`: per
   -agent config (e.g. `[agents.claude] usage_cap_tokens`) read against
   `usage.updated` observations; at the cap the supervisor TERMs the session's
   whole process group, then re-reads committed state before applying any
   effect. Per phase: a build-phase cap resets the in-flight task to `pending`
   through the store, records the rotation under `recovery`, and relaunches
   build — a second consecutive rotation on the same task stalls the PRD
   (`oversized_task`), preserving the livelock guard; a review-phase cap
   relaunches the same review cycle with no task reset — completed lens
   artifacts skip only by passing the C4 lens-output validation for the
   current cycle, never by bare file existence; a done-phase cap relaunches
   the done phase, whose finalize steps are idempotent by construction
   (verified moves, idempotent `complete-prd`, deterministic renders), and
   `drained` launches no agent session; a capability-session cap takes the
   capability failure path (attempt `failed`, attention). Every
   supervisor-launched session kind is one of these four. Child-session usage
   is NOT aggregated
   into the outer count (recorded limitation) — the wall-clock timeout and
   group TERM bound children. (PRD 00006/00007 launch-and-decision behavior;
   PRD 00003 crosswalk carries the rotation record.) This also ends the
   USAGE_CAP constant mirror — the cap is configuration, not code.
10. `work.repo_root` and `work.work_start_sha` become supervisor-owned: the
   core captures both once per PRD at its first build launch (preserved on
   re-entry, reset by `more_prds`), and the store rejects agent writes to them
   — an agent-supplied root or baseline SHA could redirect operations or
   shrink the review diff (PRD 00003 ownership + PRD 00007 capture).
11. `ovcaq state show --json` and `ovcaq status --json` expose an integer
   `cli_protocol` (starts at 1) beside `schema_version`; plugins pin it in the
   C1.1 preamble. Schema version proves data shape; `cli_protocol` proves verb
   names, arguments, and outcome semantics (PRD 00003 CLI output contract).
12. Sandbox override configuration: per-phase
   (`[agents.NAME.phases.PHASE] sandbox`) and per-capability
   (`[capabilities.CAP.agents.NAME] sandbox`) keys, honored by the driver
   with a loud preflight; a session kind that REQUIRES an elevated sandbox
   (codex review, codex agoge — C4/C5) fails closed with the exact key named
   when the opt-in is absent (PRD 00006/00007 driver-config behavior).
13. Supervisor-owned scratch GC: at run start and run finalization the
   supervisor deletes `dev/local/tmp/ovcaq-*` entries older than 7 days and
   enforces oldest-first removal above a size bound (config
   `scratch_max_mb`, default 512). Only the `ovcaq-` prefix is swept — user
   files in `dev/local/tmp/` are untouched — and durable evidence never
   lives there (C1.6/C4), so the sweep can never violate retention
   (PRD 00005 session/retention behavior).
14. The replan procedure becomes one compound `ovcaq workflow replan
   --record FILE` operation: it increments the store-owned bounded
   `recovery.replan_count`, clears tasks, and persists the replan record
   atomically; at the documented ceiling it refuses, and the skill takes the
   existing stall path (`replan_exhausted`). `recovery.replan_count` leaves
   the agent-writable list (PRD 00004 workflow verbs; PRD 00003 ownership).

### C7. Versions and release pairing

| Artifact | Version | Manifest range | Repo |
|---|---|---|---|
| claude ovcaq-autopilot | 1.0.0 | `>=1,<2` | buvis/claude-ovcaq-autopilot (new) |
| codex ovcaq-autopilot | 1.0.0 | `>=1,<2` | buvis/codex-plugins (exists, skeleton) |
| codex agoge | 0.1.0 | `>=0.1,<1` | buvis/codex-plugins (new dir) |
| claude agoge | 0.1.1 | `>=0.1,<1` | buvis/claude-agoge (as released, no change) |

Compatibility handshake is one-directional by design: OVCAQ pins plugin
versions (plan §14.3); plugins verify the runtime only through C1.1.

## Data flow

One phase session, either launcher: supervisor resolves phase config → driver
builds argv with the C3 prompt and `OVCAQ_UNATTENDED=1` → session loads the
installed plugin skill → skill preamble (C1.1) → gate dispatch on
`work.phase` → phase work, all durable effects through `ovcaq state`/`ovcaq
workflow` → one `phase-complete` (C1.3) → session exits → supervisor reads
state + SessionSummary and decides. Post-drain: supervisor invokes the agoge
capability (C5) via the same driver path; the plugin writes QA findings to the
repo; OVCAQ records the attempt and capability status in state. No plugin ever
writes capability status, events, or metrics.

## Reuse inventory

- Personal run-autopilot family — the source content to port: core SKILL.md
  (313 lines), three gate references, recovery/decision-framework/state-schema
  references, de-sloppify prompt; plan-tasks, work, design-solution,
  review-work-completion (+ its scripts: `gather-context.sh`,
  `compute_mech_facts.py`, `consolidate_findings.py`,
  `await_reviewer_outputs.py`, `check_review_file.py`), review-blindly rubric;
  agents `~/.claude/agents/{alice,blake,bob,carl,eve,ivan,pat}.md`; hooks
  `validate_state_json_hook.py`, `review_coverage_hook.py`,
  `autopilot_context_cap_hook.py`, `reinject_contract_card.py` — all read this
  session (paths above).
- claude-agoge (released 0.1.1) — reused as-is plus the one-token 0.2.0
  change; its `skills/run-agoge` + `agents/*` + playbooks are the source for
  the codex port; its `dev/bin/release`(-checks) and
  `claude-plugins/scripts/{release-plugin,validate-versions.mjs}` are the
  release tooling to copy.
- claude-aegis — the proven plugin-hooks pattern (`hooks/hooks.json` + scripts
  + tests) the claude plugin copies.
- codex-plugins repo — working marketplace manifest
  (`.agents/plugins/marketplace.json`) and `ovcaq-autopilot` plugin.json
  skeleton, both verified live by the spike; `codex plugin marketplace add
  <local path> --json` and `codex plugin add <plugin>@<mkt> --json` verified.
- use-codex/use-gemini scripts (`codex-run.sh`, `gemini-run.sh`) — bundled
  into plugin `scripts/` with `${CLAUDE_PLUGIN_ROOT}`-relative references.
- git-ferry:catchup — already a marketplace plugin; consumed via the
  requirement manifest (C6.8), not copied.
- Searched and absent (greps run): `dependencies` key in
  `claude-{aegis,warden,git-ferry}/.claude-plugin/plugin.json` — nothing found
  (the same rg matched `hooks` in aegis, proving the pattern); a codex plugin
  hooks mechanism — nothing in the codex plugin/skills docs fetched 2026-08-23,
  so the codex plugin ships no hooks (C4/C1 guards instead); an existing
  OVCAQ-side prompt/skill for either launcher — only the codex README skeleton.

## Alternatives considered

1. **Chosen: two native workflow plugins sharing the C1 protocol.** Claude gets
   the ported family verbatim-in-behavior; codex gets a native re-expression
   with codex-child lenses; agoge ports as a prompt-pack. Cost: two content
   trees to maintain. What that buys: each launcher uses only supported native
   mechanisms, and the codex path proves agent-neutrality for real (the
   project's stated point).
2. **Smallest diff: claude plugin only; codex plugin shells `claude` children
   for lenses.** Least new authoring, and the review keeps cross-model
   diversity. Rejected: the codex path would require a working claude install,
   so "run the workflow through Codex" would be false as a generalization
   proof; kept as a contingency if codex-lens quality disappoints in canary.
3. **Single-source workflow spec compiled to both launcher formats.** Ends
   double maintenance, but builds a generator before either target is proven;
   revisit in the public track if content drift becomes a measured pain.

## Risks & edge cases

- **Unsandboxed codex review/agoge sessions** (the C4 probe outcome): the
  explicit `danger-full-access` opt-in for those two session kinds widens the
  blast radius versus workspace-write. Mitigations: loud driver preflight,
  supervisor watchdog + process-group TERM, git recoverability, and the
  public-track supervisor-mediated lens design that removes the need. Child
  cost also rises (three lens sessions per cycle) — the codex review
  `timeout_seconds` default must budget serialized children plus
  consolidation.
- **Trigger collision during transition**: personal `/run-autopilot` and the
  plugin skill coexist until PRD 00011 removes the personal family. Claude
  invocation is namespaced (C3) so the driver path is unambiguous; the plugin
  skill descriptions all say "OVCAQ" to keep implicit matching apart.
- **Engram pack step** (review step 3) references a personal repo path — the
  plugin gates it behind `ENGRAM_PROJECT` env; absent → the existing
  non-fatal degradation. No personal path ships.
- **consensus_engine `workflow`/`shadow`** relies on a `~/.claude/workflows`
  asset; v1 plugin supports `legacy` only and warns-then-falls-back on the
  other values (schema still accepts them). Fanout port is a plugin v1.1
  candidate once workflow-in-plugin support is probed.
- **Next changes this design must not box in**: the generic argv driver
  (PRD 00012) reuses the codex plugin's prompt-file shape — keep the codex
  SKILL.md free of codex-only assumptions in its state protocol section; Linux
  (PRD 00013) — no absolute personal paths anywhere in plugin content; a
  future cross-model codex lens roster — lens dispatch in the codex skill is a
  table, not inline prose.
- **Qwen routing is stripped from plugin v1**: `work`/`plan-tasks`'s qwen
  integration references personal infra (`~/.claude/skills/use-qwen/scripts/*`,
  `~/.pi/agent/models.json`) that must not ship in marketplace content; v1
  tasks route to Claude tiers only, and qwen may return later behind an
  env-gated external-helper contract like engram. Superpowers references ship
  as-is (by-name, conditional on availability).

## Test strategy outline

- Claude plugin: `claude plugin validate .`; hook tests ported with the hooks;
  a protocol-conformance test that runs the skill's documented C1/C2 calls
  against a fake `ovcaq` bin recording argv and asserting sequence (preamble →
  verbs → exactly one phase-complete); release-checks wired like claude-agoge.
- Codex plugin: same fake-`ovcaq` conformance driven through one real
  `codex exec` skill invocation (the spike pattern, kept as a repo test);
  prompt files lint against the finding/verdict formats `gate.py` checks.
- Codex agoge: authorization-gate tests ported from claude-agoge's prose-gate
  pattern — absent token leaves the runtime-security lane unarmed, a present
  token arms it; report lands in `dev/local/audit-results/`.
- Cross-repo: OVCAQ PRD 00010 provisioning tests consume these releases via
  fake marketplaces first, then the real smokes (P08-T11) close the loop.

## Review log

dispatch 1 (claude): cardinal-sin 0, blocker 7, non-blocker 4, question 2

Blockers fixed in-doc: C1.4 stop-after-two (restore is operator-only);
context-cap hook retired for the supervisor-owned cap (new C6.9, C1.3
carve-out, C2 row); claude-agoge gate corrected (no 0.2.0 release — 0.1.1
accepts any token; codex gate redefined as semantics-matching prose, absent
token = unarmed QA); `${CLAUDE_PLUGIN_ROOT}` fixed and codex bundled-script
resolution named as the first codex probe; qwen stripped from v1 (personal
paths); git-ferry kept out of the manifest with a native catchup degradation
on both launchers (C6.8); `append-attempt` → `ovcaq state task attempt` row
added.

dispatch 2 (codex): cardinal-sin 0, blocker 9, non-blocker 1, question 1

Dispatch-2 blockers fixed in-doc: idempotent retry discipline (re-read before
retry; CAS revision on phase-complete retries) in C1.4; generic-verb allowlist
+ store-guard clarification in C1.2; `cli_protocol` handshake (C1.1 + new
C6.11); claude external-CLI reviewer contract stated (new C4a); the two
unproven codex mechanisms PROBED live — bundled-script execution from cache
PASSED, nested `codex exec` under workspace-write FAILED ("failed to
initialize in-process app-server client: Operation not permitted") while the
unsandboxed outer succeeded — design pivoted to an explicit per-phase
`danger-full-access` opt-in for codex review/agoge sessions with loud
preflight (C4/C5), supervisor-mediated lenses recorded as the public-track
evolution; `dev/local/tmp/` added to the C1.6 allowlist; "repository
unchanged" reworded to stop-immediately semantics (no reverts) in C1.4;
`work.repo_root`/`work.work_start_sha` moved to supervisor-owned (C6.7 +
new C6.10); usage-cap semantics defined per phase/capability with group TERM
and the child-usage limitation recorded (C6.9).

Dispatch-2 non-blocker (recorded, not fixed): the `>=0.1,<1` agoge ranges are
broad for pre-1.0 versioning — the ranges are plan §14.1-pinned, resolved
versions are batch-pinned at runtime, and tightening to `>=0.1,<0.2` is a
PRD 00010 manifest-finalization (P08-T01) consideration.

Dispatch-2 question, answered in-doc: legal (phase, outcome) pairs are plan
§9's transition table, enforced by the store (C1.3).

dispatch 3 (codex): cardinal-sin 1, blocker 5, non-blocker 3, question 1

Dispatch 3 verified prior blockers 1–8 resolved (checked-correct, each citing
the resolving section) and judged prior blocker 9 partially open. Its own
findings, all fixed in-doc: done-phase/drained cap semantics completing the
per-session-kind enumeration (C6.9); the contradictory `autopilot restore`
mapping row retired (C2); lens outputs now validated against the lens-output
contract with atomic `.part`→final promotion, never skipped by bare existence
(C4, C6.9); validated raw lens outputs copied durably to
`dev/local/reviews/<prd-stem>-lens-<cycle>-<lens>.txt` before scratch cleanup,
honoring the raw-evidence invariant (C4); the scratch cardinal sin closed by
supervisor-owned prefix-scoped GC with age and size bounds (C1.6 + new C6.13);
`recovery.replan_count` moved to store-owned behind a compound
`ovcaq workflow replan` verb with a refusal ceiling (C6.7 + new C6.14); the
capability sandbox override key named with fail-closed preflight (C5 + new
C6.12).

Dispatch-3 non-blockers (recorded, not fixed): agoge range breadth (duplicate
of dispatch 2's, same routing to P08-T01); negative conformance cases for the
C1 failure/retry branches belong in the plugin test suites (noted for the
work records); the "heidy" typo finding targeted a transcription slip in the
reviewer's prompt copy — the design file itself reads `heidi`, no change
needed.

Dispatch-3 question, answered in-doc: the capability sandbox override contract
is now C5/C6.12 with fail-closed behavior.

Non-blockers from dispatch 1 (recorded, not fixed):
- N1 (finding 8): codex catchup provider was unspecified — addressed as a side
  effect of the C6.8 rewrite (native delta refresh on codex).
- N2 (finding 9): intra-family sub-skill invocations must be namespaced
  (`/ovcaq-autopilot:work` etc.) in the port, not bare names, while personal
  twins coexist pre-00011.
- N3 (finding 10): C6 should also route (a) `replan-context.md` /
  `contract-card.md` / `deferred/` as state-protocol doc additions (PRD 00003)
  and (b) `ENGRAM_PROJECT` env passthrough (PRD 00006/00007) — the supervisor
  env surface must let the gate open.
- N4 (finding 11): USAGE_CAP mirror concern — resolved structurally by C6.9
  (cap is config).

Questions (recorded):
- Q1 (finding 12): should the codex review phase get its own timeout default,
  given three serialized lenses vs Claude's concurrent roster?
- Q2 (finding 13): is the real `codex exec` conformance test CI-gated,
  auto-skipped without auth/network, or manual-only evidence?
