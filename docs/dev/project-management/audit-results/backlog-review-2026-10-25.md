# Backlog review - ovcaq - 2026-10-25

Verdict: GO (7 PRDs READY; 0 Blocking open; see Decisions applied for the two user choices and the mid-review rewrite)

Target: `docs/dev/project-management/prds/backlog/`. At the start: 5 PRDs (00057-00061) created 2026-10-25 from `designs/autopilot-optional-supervision.md`. At the end: 7 PRDs; 00062 and 00063 were created during this review from discovery 00004 (user decision), and 00058-00061 were rewritten in one batch at 11:40 by the user's parallel session on the corrected boundary design (same design path, "corrected at the user's request on 2026-10-25"). Every lens and every mechanical gate below was re-run on the final set. `wip/` empty. `hold/` 47 parked. Law: `~/.agents/skills/create-prd` SKILL.md and `assets/standard.md` as of today.

Mechanical gates on the final set: `check_links.py` 0 findings under backlog/wip. `ground_prd.py` 0 missing, 0 unresolved, 0 unverified. Frontmatter parsed with the live autopilot `cli.frontmatter` and `cli.eligibility`: every key is a recognized name; 00057's gate evaluates to exit 1 in the sandbox as intended. Seven top-level sections in every PRD, in template order; every task line carries `Acceptance:`; `#### Feature:` names unique per PRD; 127-152 lines each. `.migration-placeholder` in `backlog/` is skipped by `selection.py` (no `.md` suffix, no 5-digit prefix). Discovery files 00001-00009 share numbers with done PRDs 00002-00009: pre-existing, outside the backlog, no action.

## Map

| # | PRD | template | lines | subsystems | depends on | verdict |
|---|-----|----------|-------|------------|------------|---------|
| 00057 | Lifecycle entry and recovery | standard | 127 | workflow, cli, paths, tools, docs | discovery 00003; process identity working in the loop's environment (eligibility, i.e. 00062 done) | READY |
| 00058 | OVCAQ-owned workflow protocol | standard | 133 | workflow, state, contracts, supervisor_cli, tools, pyproject | 00057 (eligibility) | READY |
| 00059 | Review, lane and evidence transactions | standard | 134 | workflow, state, docs | 00058 (eligibility) | READY |
| 00060 | Supervision, records and contract exchange | standard | 144 | runtime, drivers, config, tui, workflow, tools, docs | 00058, 00059, 00062, 00063 (eligibility) | READY |
| 00061 | Advanced waves and operator parity | standard | 131 | workflow, runtime, state, tui, tools, docs | 00060; agent-plugins 00016 artifact via `ovcaq.toml` `[autopilot] plugin_artifact` (eligibility) | READY |
| 00062 | Supervisor process identity and start preflight | standard | 152 | runtime, state, errors, supervisor_cli, docs | none; first in-sandbox-eligible PRD | READY |
| 00063 | Driver failure classes and neutral default tiers | standard | 137 | drivers, config, runtime, docs | none (runs after 00057 by number) | READY |

Drain order in the sandbox: 00062, 00057, 00058, 00059, 00063, 00060, then 00061 once `[autopilot] plugin_artifact` names a compatible plugin artifact. 00060 depends on the higher number 00063; the prerequisite tool 00057 builds makes that safe (00060 is skipped, 00063 has no gate and runs, 00060 becomes eligible), so it is not an order break.

## Findings

Status after the apply pass and the 11:40 rewrite. "Resolved by rewrite" means the user's parallel revision removed the defect before or while this review's edit landed.

### Blocking

- [all] B Executability: every Phase 2 Exit Criteria requires `./tools/check`, and 00058/00060/00061 acceptance tests use real subprocesses and process contention. The batch runs through `autoclaude` -> `caffeinate -is run-agent python3 .../cli/__main__.py loop` (`~/.config/bash/plugins/development.plugin.bash:401`), inside the Seatbelt profile, which denies `/bin/ps` (verified 2026-10-25: `ps -o pid= -p 1` -> Operation not permitted; `registry.process_identity(os.getpid())` -> PermissionError; `tests/runtime/test_fleet_registry.py::test_process_identity_requires_alive_pid_and_matching_start` fails). `src/ovcaq/runtime/registry.py:131` still runs ps. No PRD owned the fix -> fails as: rework thrash on every PRD's final gate for a cause none of them owns. Resolved: user chose to gate 00057 on the real precondition and to create the discovery-00004 PRD; 00062 now carries the fix and drains first.
- [00057, 00058, 00061] B/C: the prerequisite tool gating four PRDs had no stated contract, and the cross-repo artifact locations were "explicitly supplied" by nobody -> fails as: wrong-TDD lock-in on the tool; permanent silent skip or stall. Resolved: DAG and `ovcaq.toml` `[autopilot]` key pinned in 00057's Resolver module; the rewrite then removed 00058's bundle dependency (OVCAQ owns the protocol), leaving `plugin_artifact` for 00061 only, which 00057 and 00061 now state.
- [00058] B: public command names and owner-marker path lived only in the design doc -> fails as: wrong-TDD lock-in across repos. Resolved: command names, request/response fields, error codes and the closed operation set are now in 00058's Feature text; the owner marker was removed by the corrected design.
- [all five original] C Coherence: Phase 1 task pairs shared acceptance tests and both depended only on Phase 0 -> fails as: rework thrash. Resolved: disjoint tests and `depends on: Phase 1 task 1` in all five (the rewrite kept them; 00060 now chains four Phase 1 tasks).
- [00059, 00061] E Collisions: `src/ovcaq/contracts/fixtures-v1.json` listed as touched while 00058 vendors it hashed and 00060 refuses on digest drift -> fails as: goal reversal inside the set. Resolved: removed from both trees; local fixtures now under `tests/fixtures/workflow/`.

### Non-blocking

- [00060] C: TUI files sat under Module Sync. Resolved by rewrite (Module Supervision).
- [00057] D: "concurrent working-tree fixes" now cites commit cf8be72 and its two test files.
- [00058-00061] E: parity inventory rows R12/R16/R28, R13/R14, R15 now named in each Foundation layer.
- [00061] A: "tUI" typo fixed.
- [00060] F: the rewrite added a Records capability (store_tree.py port) and a fourth Phase 1 task; seven task lines against the 15-task ceiling. `plan_expansion: allow` applied, matching the user's reshape decision for the same reason.
- [00062] A: `ErrorCode.PROCESS_PROBE` (value process_probe, exit 12), `Supervisor.preflight`, `StateService.revert_batch_start` and the start-token format are names set by this PRD, derived from discovery 00004's wording; no `(guess)` markers remain.
- [all] A: Module `Exports` in 00057-00061 are prose rather than symbol lists; accepted for `default_model: opus` with Phase 1.5 design owning the HOW.

### Questions

- Neutral tier key names (discovery 00004 Open Question): user chose standard / deep; 00063 encodes it, with the consequence that an OVCAQ-side frontmatter floor written as `opus` warns unless `[agents.<agent>.tiers]` maps it (documented in 00063 Risks).
- Unrunnable required capability (discovery 00004 Open Question): resolved from the repo. No production path declares a required capability (`rg -n "required=True|\"required\": True" src/ovcaq` matches argparse only), so 00062 pins that fact with a test instead of adding runner-availability checks.

## Reshapes

- 00058, 00059, 00061 (now also 00060): four to seven task lines each, but the legacy source they port is large (waves 2,717 lines plus about 25 test files; review/lane/custody 3,267 lines; store_tree.py in 00060). The check-plan gate stalls past 15 tasks or past 3.0x the task lines once more than 8 are planned -> fails as: stall. User chose `plan_expansion: allow` (with `rework_cap: 3`) over splitting. Applied to 00058, 00059, 00060, 00061.
- Discovery 00004 split into 00062 (supervisor start: identity, doctor fact, preflight, early-failure revert, capability retry usage error) and 00063 (driver edge: failure classes, neutral tiers). Loosely coupled subsystems; each stands alone.

## Gaps

- Hold stubs 00036 (Codex auth/ECONNRESET classes) and 00056 (Codex bare status wording) are now owned by 00063; 00056's four strings already classify correctly today (verified), so 00063 only pins them. Both stubs can be closed by moving them out of `hold/` (attended triage; not done here).
- Discovery 00002's ordered must-haves 1 (public preview, 00008), 4 (end-to-end verification, 00006), 5 (hold retriage, 00009) and 6 (operator experience, 00005) still have no PRDs. The corrected design says they complement this track. Recommend `/create-prd` on 00008 (small, user-prioritized) and `/assess-evolution` for the rest. Not invented here.
- No fix-type PRDs without regression tests; no deprecations without removal.

## End state after this batch

In the sandbox, a drain started now runs 00062 (ps-free process identity, preflight before `start_batch`, typed probe error, doctor fact), then 00057 (`workflow enter`, verified bucket moves, one resolver, the prerequisite tool), 00058 (OVCAQ-owned typed workflow CLI with CAS/replay and contract export), 00059 (atomic review close, code-owned lanes, custody and verification records), 00063 (driver failure classes, neutral standard/deep tiers with driver defaults), 00060 (session binding, record-store commits, contract exchange), and stops with 00061 waiting for a plugin artifact from agent-plugins 00016. OVCAQ then has everything the corrected design assigns to the runtime half except waves. Still lacking afterwards: public preview surface, an end-to-end drain canary on CI, operator experience, hold retriage, provisioning and cutover (held 00010/00011).

## Frontmatter tuning

| PRD | suggestion | why |
|-----|------------|-----|
| 00057-00061 | `rework_cap: 3` (applied) | judgment-heavy PRDs; default 2 was tuned on well-specified work |
| 00058-00061 | `catchup: force` (applied) | each predecessor rewrites `workflow_cli.py`, `state/schema.py`, `state/commands.py`, both docs |
| 00058-00061 | `plan_expansion: allow` (applied) | reshape decision kept them whole |
| 00057 | `eligibility: uv run python -c "... registry.process_identity(os.getpid())"` (applied) | skipped in any environment where the full gate would fail on ps |
| 00058 | `design_gate: user` (not applied; user's call) | public protocol another repo codes against |
| 00062, 00063 | none beyond `default_model: opus`, `lane: full` | well-specified; default caps suffice |

## Decisions applied

User decisions (AskUserQuestion, 2026-10-25):

- Sandbox gate: option 1. 00057 carries `eligibility: uv run python -c "import os; from ovcaq.runtime import registry; registry.process_identity(os.getpid())"`; evaluated from the repo root in this sandbox with the live `cli.eligibility`: exit 1, i.e. skipped until process identity works. `/create-prd` was then run on discovery 00004 inside this session, producing 00062 and 00063 (grounding gate 0 blocking on both drafts before saving).
- Reshape: option 1. `plan_expansion: allow` beside `rework_cap: 3` on 00058, 00059, 00061; extended to 00060 after the rewrite added its Records capability.
- Tier keys (create-prd, discovery 00004 Open Question): standard / deep.

Adjudicated under standing authorization (routine reversible PRD edits), all on the pre-rewrite text and then re-verified on the rewritten text:

- 00057: Resolver module states the prerequisite tool contract (DAG 00058<-00057, 00059<-00058, 00060<-00058+00059+00062+00063, 00061<-00060; `[autopilot] plugin_artifact` for 00061; missing predecessor, key or path exits 1; read-only). Phase 0 acceptance covers exit 1 on an unmet predecessor or missing key or path. Problem Statement cites cf8be72. Phase 1 tasks disjoint and sequential. `rework_cap: 3`.
- 00058: exact command names copied in (the rewrite expanded them into full request/response/error contracts); Foundation names rows R12/R16/R28; Phase 1 tasks disjoint and sequential. `rework_cap: 3`, `catchup: force`, `plan_expansion: allow`.
- 00059: `fixtures-v1.json` removed from the tree; Policy inputs read-only; rows named; Phase 1 tasks disjoint and sequential. Same frontmatter as 00058.
- 00060: Foundation names 00062 and 00063 as the robustness prerequisites; rows R13/R14 named; TUI files under Supervision (rewrite); Phase 1 tasks chained. `rework_cap: 3`, `catchup: force`, `plan_expansion: allow`.
- 00061: `fixtures-v1.json` removed; Observation reads runtime-owned shapes; Foundation names `plugin_artifact` and row R15; Phase 1 task 2 depends on task 1; Phase 2 acceptance no longer repeats Phase 1 tests; typo fixed. Same frontmatter as 00058.
- 00062 and 00063 (new): written on `assets/standard.md`; grounded against the code read today (`registry.py:131`, `supervisor.py:136-184`, `capability.py:36-42` and `:179-189`, `config.py:502-521` and `:544-583`, `claude_events.py:223-261`, `codex_events.py:298-339`, `supervisor_cli.py:68-73` and `:451-472`, `state/commands.py:502-531`); the proc_pidinfo premise and the current misclassifications were verified by running probes in this sandbox.

Left as suggestion only: `design_gate: user` on 00058; closing hold stubs 00036 and 00056.

Per-PRD verdict after apply: 00057-00063 READY. Backlog: GO.
