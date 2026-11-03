# OVCAQ implementation-plan PRD coverage

Status: accepted | Scope: umbrella Phases 0–12 | Updated: 2026-10-25

Accepted source-plan SHA-256:
`e68762c926e3542a2ee696369855530b61ddc71e0ee120c0d3688f63ae730a82`

## Purpose

This manifest makes the accepted implementation plan and PRDs 00002–00014
equivalent. Implementing every PRD completes the plan only when every acceptance
criterion and independent review has passing evidence and the two milestone
closeout PRDs verify the mappings below.

Discovery 00001 is the resolved shared discovery for this decomposition. It
covers the cross-cutting product and migration once; no PRD has a pending
discovery gate. The accepted implementation plan remains the source contract.

PRD 00011 closes the one-way personal migration after Phases 0–9. PRD 00014
closes the full plan after the separate generic-driver, Linux, and public-release
track in Phases 10–12.

## Completion Rules

1. Follow the dependency graph, normally numerical within each track; a later phase cannot hide a failing dependency. The three-layer amendment requires AP00017/00021, OV00057–00065 as applicable, and Lantern00003 before personal cutover; held00010/00011 specify exact readiness gates.
2. Move a PRD to `done` only after acceptance and mandated review pass with
   durable evidence.
3. End each owning phase/PRD with its own conventional commit and independent
   review before beginning its consumer; do not combine phases into one
   unreviewed implementation boundary.
4. Every source task and exit criterion under implementation-plan Phases 0–12
   is incorporated without dilution into its owning PRD. IDs `P00-T01` through
   `P12-T08` are materialized in the accepted plan and must never be reused or
   renumbered; grouped PRD wording cannot waive an individual source task.
5. Before planning or executing a PRD, verify the exact source-plan digest above.
   Track progress in PRD/evidence records, not by editing source-plan checkboxes.
   Any source-plan change stops execution until reviewed reconciliation updates
   its IDs, owning PRDs, this manifest, and the accepted digest.
6. Phase closeout evidence must map every one of the 119 source task IDs to a
   passing test, inspected artifact, committed result, or explicit retirement
   already authorized by the plan. Absence of a row blocks PRD completion.
7. Earlier generated schemas, inventories, fixtures, protocols, and pins
   constrain later PRDs; later work cannot guess around them.
8. Migration IDs `M01`–`M23` and personal-acceptance IDs `A01`–`A15` are
   materialized in the accepted plan. PRD 00011 must link evidence for each ID.
9. PRD 00014 must link evidence for every source task/exit criterion, plan
   contract, migration row, personal acceptance row, and release requirement.
10. Final messages/checkmarks are not evidence without tests, committed state,
   retained sessions, inspected artifacts, or auditable migration results.

## Plan Contract Ownership

| Implementation-plan contract | PRD owner(s) | Closeout evidence |
|---|---|---|
| §1 outcomes | 00003–00011 | personal-cutover outcome table and 00011 canaries |
| §2 verified current system | 00002 | characterized inventory, fixtures, baseline, migration manifest |
| §3 operating model | 00003–00010 | state/service/driver/supervisor/provision integration evidence |
| §4 product/package boundaries | 00002, 00006, 00010, 00014 | import guards and distribution-content audits |
| §5 repository shape/dependencies | 00002–00010 | package skeleton plus dependency-direction tests |
| §6 public commands/output | 00003–00012, 00014 | installed CLI/help/JSON/error-code/docs compatibility tests |
| §7 configuration/paths | 00005, 00011, 00013 | precedence, XDG, containment, arbitrary-cwd, macOS/Linux tests |
| §8 state design | 00003, 00007, 00010 | schema/transaction/control/capability contract tests |
| §9 workflow core | 00004 | pure workflow, saga, reporting, and CLI tests |
| §10 driver protocol | 00006, 00009, 00012 | first-party and installed third-party conformance suites |
| §11 normalized events | 00006, 00008, 00009, 00012 | fixtures, tolerant reduction, TUI and raw fallback tests |
| §12 supervisor/process model | 00005, 00007 | decision parity plus real process/lock/signal tests |
| §13 TUI migration | 00008 | shared-model controls, fallback, detach/reattach tests |
| §14 external provisioning | 00007, 00010 | check/apply/idempotency/pin/drift and real capability smokes |
| §15 security/failure policy | 00003, 00005–00010, 00014 | fail-closed tests and release security review |
| §16 test strategy | 00002–00014 | each PRD's required unit/integration/packaging evidence |
| §17 implementation sequence | 00002–00014 | phase ownership table below |
| §18 migration mapping | 00002–00011 | migration disposition table and 00011 legacy audit |
| §19 personal acceptance | 00003–00011 | cross-cutting table and 00011 closeout bundle |
| §20 risks | 00002–00014 | per-PRD mitigations plus 00014 final review |
| §21 resolved decisions | 00002, 00010–00014 | license, milestone boundary, capabilities, canaries, retention |
| §22 unresolved questions | all | every PRD ends with no unresolved question |

## Phase Ownership

| Phase | Source IDs | Count | PRD | Required completion output |
|---|---|---:|---|---|
| 0 — repository/contract baseline | P00-T01…P00-T08 | 8 | 00002 | package skeleton, inventories, fixtures, baselines, packaging gates |
| 1 — state kernel | P01-T01…P01-T12 | 12 | 00003 | sole writer, v1 schema/crosswalk, state CLI, durability proof |
| 2 — workflow core | P02-T01…P02-T10 | 10 | 00004 | lifecycle, recoverable records, reports, workflow CLI |
| 3 — runtime substrate | P03-T01…P03-T11 | 11 | 00005 | paths, lock/registry, process groups, sessions/retention |
| 4 — events/Claude adapter | P04-T01…P04-T09 | 9 | 00006 | normalized protocol, driver seam, Claude conformance |
| 5 — supervisor | P05-T01…P05-T09 | 9 | 00007 | state-led decisions, no-TUI loop, capability lifecycle |
| 6 — TUI/Python launcher | P06-T01…P06-T10 | 10 | 00008 | shared-model TUI, controls, Bash-free run/attach |
| 7 — Codex adapter | P07-T01…P07-T07 | 7 | 00009 | Codex fixture/fake conformance and TUI projection |
| 8 — provisioning | P08-T01…P08-T11 | 11 | 00010 | reconciliation, external releases, pins, real smokes |
| 9 — personal cutover | P09-T01…P09-T13 | 13 | 00011 | both canaries, legacy removal, instruction/path migration |
| 10 — generic driver API | P10-T01…P10-T06 | 6 | 00012 | argv driver, installed extension proof, stable driver/event API |
| 11 — Linux support | P11-T01…P11-T05 | 5 | 00013 | common runtime contracts, Linux install/terminal/launcher gates |
| 12 — public release | P12-T01…P12-T08 | 8 | 00014 | stable docs/policies, security/artifact gates, publication |

The source-task count is 119. Count or ordering drift between the accepted plan
and this table is a contract failure that must be reconciled before work starts.

## Execution Authorization Ownership

| External/destructive action | Owner | Required authorization evidence |
|---|---|---|
| Companion repository changes/releases and real launcher `--apply` | 00010 | exact repositories, commits/versions, publish targets, dry-run apply plan |
| Personal runtime/state/dotfile/Codex-home migration | 00011 | passing canaries plus enumerated target/recovery ledger |
| Release tag, marketplace pairing, and package publication | 00014 | commit, version, checksums, tag/index destinations, compatible plugin versions |

Implementation work may prepare and verify these actions. It may execute them
only after the corresponding explicit approval; earlier approval or PRD backlog
status is not a substitute for the final target-specific authorization.

## Public Command Ownership

| Command family | Primary PRD(s) |
|---|---|
| `ovcaq init`, `state *` | 00003 |
| `workflow *` | 00004 |
| `status`, `logs`, `logs purge`, base `doctor` | 00005 |
| `run --no-tui`, `pause`, `resume`, `stop`, `capability retry` | 00007 |
| interactive `run`, `attach`, TUI controls | 00008 |
| Codex launch behavior | 00009 |
| `provision --check/--apply`, provisioning doctor/preflight | 00010 |
| `doctor --driver NAME` | 00012 |
| public command/docs compatibility guarantee | 00014 |

## Personal-Cutover Outcome Ownership

| Outcome | Primary evidence owner | Prerequisites |
|---|---|---|
| Installed command and TUI | 00011 | 00002, 00008 |
| Real Claude drains workflow | 00011 | 00006, 00007, 00010 |
| Real Codex drains workflow | 00011 | 00009, 00010 |
| All agent state writes use OVCAQ | 00011 | 00003, 00004, 00010 plugins |
| State plus summary decides | 00007 | 00003, 00006 |
| Normalized TUI for both providers | 00009 | 00006, 00008 |
| Check/apply provisioning | 00010 | 00005, 00006, 00009 |
| Required agoge and independent retry | 00010 | 00003, 00007 |
| Separate full two-PRD canaries | 00011 | 00010 |
| No old production path/runtime | 00011 | all extraction PRDs |

## Architecture Invariant Ownership

| Invariant | Primary PRD | Final proof |
|---|---|---|
| One state writer | 00003 | 00011 duplicate/direct-write audit |
| State decides; prose does not | 00007 | real canaries in 00011 |
| Provider code stays at edge | 00006 | Codex/generic no-branch proofs in 00009/00012 |
| Raw evidence survives normalization | 00006 | retention/canary evidence in 00011 |
| TUI observes shared models | 00008 | duplicate-policy/liveness audit |
| External capabilities stay external | 00010 | wheel/content audit in 00011/00014 |
| Configured commands never shell-evaluate | 00005 | adapter/provision/generic tests |

## Migration Disposition Ownership

| ID | Current artifact | Destination/disposition | Primary PRD | Closeout proof |
|---|---|---|---|---|
| M01 | `cli/schema.py` | deepen in `state/schema.py` | 00003 | crosswalk/schema tests |
| M02 | `cli/state.py` | `state/store.py`; revision/fsync | 00003 | durability tests |
| M03 | `cli/statectl.py` | state commands/CLI | 00003 | installed CLI tests |
| M04 | `scripts/statectl.py` | delete shim | 00011 | final legacy search |
| M05 | `cli/transitions.py` | `workflow/transitions.py` | 00004 | transition matrix |
| M06 | `cli/selection.py` | `workflow/selection.py` | 00004 | selection fixtures |
| M07 | `cli/frontmatter.py` | `workflow/frontmatter.py` | 00004 | parser fixtures |
| M08 | `cli/resume.py` | `workflow/resume.py` | 00004 | resume matrix |
| M09 | `cli/policy.py` | `workflow/policy.py` | 00004 | policy tests |
| M10 | `cli/records.py` | workflow records saga | 00004 | failpoint/reconcile matrix |
| M11 | `cli/render_*` | workflow reports | 00004 | deterministic golden tests |
| M12 | `cli/routing.py` | config plus adapters/runtime | 00007 | parity and provider guards |
| M13 | `cli/runner.py` | process substrate plus adapters | 00006 | 00005 process and adapter tests |
| M14 | `cli/usage_limit.py` | provider classifiers | 00006 | Claude plus 00009 Codex tests |
| M15 | `cli/watchdog.py` | runtime watchdog | 00005 | real process-group tests |
| M16 | `cli/loop.py` | supervisor decision/effects | 00007 | full loop parity inventory |
| M17 | `scripts/tracon/*` | events/TUI | 00008 | shared-model/terminal tests |
| M18 | `scripts/render_stream.py` | decoder/plain renderer | 00008 | 00006 decoder and fallback tests |
| M19 | `_walk_up.py` | installed path discovery | 00005 | arbitrary-cwd tests |
| M20 | Bash wrapper/job control | Python run/attach, then delete | 00011 | 00008 replacement and shell audit |
| M21 | post-drain `run_agoge` glue | capability lifecycle/plugins | 00010 | 00007 fake and real smoke evidence |
| M22 | Claude workflow skill | external Claude plugin | 00010 | compatible release; 00011 removal |
| M23 | stale Codex workflow skill | external plugin; delete old | 00011 | 00010 release and home audit |

## Cross-Cutting Acceptance Ownership

| Acceptance group | Primary PRD(s) |
|---|---|
| Fresh state, no direct edits, nested durability | 00003, 00011 |
| Pure workflow/decision tables row-by-row | 00004, 00007 |
| Claude/Codex adapter conformance | 00006, 00009 |
| Raw/normalized retention and explicit purge | 00005, 00006 |
| TUI, duplicate run, process cleanup | 00005, 00008 |
| Provision idempotency, pins, required agoge | 00007, 00010 |
| Full canaries and one-way legacy removal | 00011 |
| Generic extension and raw-only execution | 00012 |
| macOS/Linux common guarantees | 00013 |
| Stable contracts, docs, security, artifacts, publication | 00014 |

## PRD 00011 Migration Closeout Evidence

- Passing acceptance/review records for PRDs 00002–00011.
- Separate Claude/Codex canaries with all mandatory review lenses.
- Retained state revisions, raw/normalized logs, summaries, metrics, and pins.
- Completed migration table with no pending/ambiguous disposition.
- Searches covering old commands/paths, direct edits, bootstraps, duplicate code,
  and bundled external content.
- Proof old state was archived/deleted without import/dual writing.
- Proof global source instructions and personal commands name OVCAQ.
- Approved target ledger with recovery references and verified postconditions.

## PRD 00014 Full-Plan Closeout Evidence

- Passing acceptance/review records for PRDs 00002–00014.
- PRD 00011 migration evidence remains valid after public-track changes.
- Installed third-party extension and published conformance proof.
- Common macOS/Linux state/runtime and first-party launcher proof.
- Versioned state/CLI/driver/event policies match executable contracts.
- Full quality/security/artifact matrices and immutable checksums.
- Public-package clean installs plus compatible marketplace release pairing.
- No personal paths, state, transcripts, secrets, or plugin content in artifacts.
- Release authorization record exactly matching published targets and checksums.

## Unresolved Questions

None.

## Three-layer reconciliation, 2026-10-25

The latest [design](../designs/autopilot-optional-supervision.md) and accepted-plan amendment supersede old owner labels while preserving every source task/behavior. Existing completed PRDs prove the pre-extraction implementation; they do not by themselves prove the new distribution boundaries.

| Source contract / IDs | New owner and implementation evidence |
| --- | --- |
| P00-T01…P00-T08 baseline/package contracts | Original00002 evidence plus AP00012/00018, OV00057/00064 and Lantern00001 exports |
| P01-T01…P01-T12 state kernel | AP00018 canonical controller, OV00058 removal of old writer |
| P02-T01…P02-T10 lifecycle/records | AP00019–00021; preserve cf8be72 and00062 regression evidence |
| P03-T01…P03-T11 runtime substrate | OV00058/00060 execution journal/process recovery; no copied workflow truth |
| P04-T01…P04-T09 events/Claude | Original00006 plus OV00059/00064 public projection and routing |
| P05-T01…P05-T09 supervision | OV00059/00060 with controller acceptance and original agoge behavior |
| P06-T01…P06-T10 TUI/launcher | OV00064/00065 headless API/launch, Lantern00001–00003 presentation/controls; no task dropped |
| P07-T01…P07-T07 Codex | Original00009 plus OV00059 mixed-driver route/isolation and Lantern00003 projection |
| P08-T01…P08-T11 provisioning | Held00010; external Autopilot/controller compatibility, independent optional TUI |
| P09-T01…P09-T13 personal cutover | Held00011; installed three-layer canaries and all source-disposition evidence |
| P10-T01…P10-T06 generic drivers | Held00012; operations-protocol observations and separate-client fixtures |
| P11-T01…P11-T05 Linux | Held00013; independent headless and UI artifact gates |
| P12-T01…P12-T08 public release | Held00014; controller/operations compatibility and independently versioned distributions |
| R11/R12/R16 + record-store behavior | AP00018–00021 workflow acceptance/records; host guards remain AP00014/00016 |
| R13/R15 + process half of R28 | OV00059–00061, existing00062/00063 robustness unchanged |
| R14 presentation | OV00064 public projection/control plus Lantern00001–00003 and OV00065 packaging |
| M01–M23 and A01–A15 | Held00011 retains every ID; bind evidence to controller, orchestration or presentation owner rather than old monolith |

No IDs are renumbered or retired. Each individual source task still needs evidence; the range mapping is ownership, not a waiver. Original closeout tables above retain historical PRD numbers; this table adds the mandatory extraction/consumer evidence. Current AGENTS and tracked architecture distinguish implementation from target.

AP00016/00017 have no OVCAQ prerequisite. OV00057 can use AP00018 fixtures; OV00058 needs installed AP00021 and00062. OV00059 needs00063, then00060/00061. OV00064 can run beside orchestration after00058. Lantern00003 depends on OV00060/00061/00064, never00065; OV00065 consumes its parity evidence. This avoids an extraction cycle. Source retirement remains held.
