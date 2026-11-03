# OVCAQ supervisor loop

Status: backlog | Version: 1 | Umbrella phase: 5 | Created: 2026-08-23

## Overview

### Source Contract

Implements Phase 5 source tasks `P05-T01`–`P05-T09` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

The current loop contains proven routing, retry, pause, park, drain, metrics,
and post-drain behavior but mixes provider details with orchestration. OVCAQ
needs a state-led supervisor that runs without Bash and explains every next
action from committed state plus a normalized session result.

### Target User

Operators need a reliable headless runner; agents need fresh phase sessions;
later UI code needs one authoritative supervisor rather than duplicate policy.

### Success Metrics

- A fake Claude driver drains build/review/done through `ovcaq run --no-tui`.
- Every continuation and halt is a tested pure decision from state plus summary.
- The full legacy loop/parity inventory has one implemented or retired outcome.
- Exactly one metric row is emitted per attempted session.
- Agoge failure preserves drained PRDs and retries independently.

## Preconditions and Boundaries

- Depends on completed PRDs 00002–00006.
- State and workflow services own durable transitions; drivers own provider data.
- This PRD provides foreground/no-TUI operation only; interactive attachment is
  PRD 00008.
- Agent final prose is never authoritative.

## Functional Decomposition

### Capability: Pure Post-Session Decisions

#### Feature: Ordered decision table

Compare pre/post state revision and fingerprints; let valid progress win over
provider exit noise; then evaluate pause, capabilities, completion, continuation,
rate limit, retry, repeated fingerprints, park, and systemic halt in that order.

#### Feature: Bounded failure policy

Classify credible provider rate limits, connectivity loss, timeout, process
death, permission/authentication failure, bootstrap failure, and repeat stalls.
All waits/retries/caps come from configuration and injectable time.

### Capability: Session Orchestration

#### Feature: Phase routing and execution

Resolve phase-specific agent/model/effort/timeout configuration, create one
fresh session, snapshot state, invoke the driver through runtime process/session
services, then reduce the result and execute exactly one decision. Routing
configuration is provider-neutral: `[phases.PHASE]` names tier, effort, and
timeout; `[agents.NAME.tiers]` maps tier keys to provider model identifiers;
`[agents.NAME.phases.PHASE]` may override tier or effort; the per-agent prompt
template lives in agent configuration with a driver-provided default. Drivers
map the neutral effort scale to their native control and never drop it
silently.

#### Feature: Lifecycle controls and evidence

Honor boundary pause, resume by clearing durable pause intent, immediate stop,
drain/archive, provider-neutral durable attention projected by the TUI,
raw/normalized logs, and one metrics row per session. The current personal
`notify_out` OS-script path is retired rather than copied. Fail closed if state
is unreadable.

### Capability: Post-Drain Capabilities

#### Feature: Durable generic lifecycle

For non-empty drain, move required capability through pending/running/failed/
succeeded; persist unique attempts and actionable attention. Empty batches mark
it skipped. Completed batch requires all required capabilities satisfied.

#### Feature: Independent agoge retry

`ovcaq capability retry agoge` reconciles stale running ownership, refuses a
live owner, creates an idempotent attempt, and never reopens drained PRD phases.

## Structural Decomposition

```text
src/ovcaq/
  runtime/
    decision.py
    supervisor.py
    capability.py
    session.py
  config.py
  cli.py
tests/runtime/
  test_decision.py
  test_supervisor.py
  test_capability.py
  test_loop_parity.py
```

- `decision.py`: pure ordered decision types/table; no I/O or provider parsing.
- `supervisor.py`: effects, loop lifecycle, routing, retries, metrics.
- `capability.py`: provider-neutral post-drain attempts and retry ownership.
- `session.py`: shared session execution/evidence integration from PRD 00005.

## Dependency Graph

```text
state + workflow + SessionSummary -> pure decision
config + process/session + driver -> supervisor effects -> next state/session
drained state + capability runner -> capability lifecycle -> batch completion
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Decision and Routing Core

- [ ] Extract the ordered post-session decision table as pure data/functions.
- [ ] Port phase agent/model/effort/timeout routing from configuration.
- [ ] Port snapshots, progress detection, fingerprints, and repeat accounting.
- [ ] Cover every parity-inventory decision or explicit retirement.

**Exit Criteria**: Every next action is reproducible from state plus summary.

### Phase B: Supervisor Effects

- [ ] Implement fresh-session launch/reduction/decision execution.
- [ ] Port bounded wait/retry/death/park/systemic-halt behavior.
- [ ] Port pause, resume, stop, drain, archive, provider-neutral attention, and
  metrics behavior; retire the personal OS-notification script path.
- [ ] Implement `ovcaq run --no-tui` foreground lifecycle and signal outcomes.

**Exit Criteria**: Fake Claude drains without Bash and emits one metric row per
session attempt.

### Phase C: Required Capability Lifecycle

- [ ] Implement generic pinned capability attempts and transition validation.
- [ ] Implement failure attention, nonzero exit, stale-owner reconciliation, and
  `ovcaq capability retry agoge` against a fake capability.
- [ ] Prove failure/retry never changes drained PRD results.

**Exit Criteria**: Success completes the batch; failure remains actionable and
independently retryable.

## Test Strategy

- Productive state plus nonzero exit; untouched state plus success prose.
- Pause/resume/stop, next phase, empty/non-empty drain, and completed capabilities.
- Rate limit with/without credible reset; bounded connectivity/death/timeout.
- Repeated fingerprints, park versus bootstrap/systemic halt.
- Agoge success/failure/stale-running/live-owner/independent retry.
- State read/write failure prevents another launch.
- One metric row per attempt and complete parity-inventory coverage.

## Risks

- **Prose-led continuation**: Decision inputs exclude final messages.
- **Retry storms**: Bound every wait/retry and test exhaustion outcomes.
- **Capability reopens work**: Make drained PRD state immutable to retry effects.
- **Hidden provider branch**: Accept only protocol types in supervisor modules.

## Acceptance Criteria

- [ ] Fake Claude drains build/review/done through installed no-TUI command.
- [ ] Every decision is explainable from committed state plus summary.
- [ ] Legacy loop inventory is fully implemented or explicitly retired.
- [ ] Metrics, pause, stop, retry, park, and halt contracts pass.
- [ ] Required post-drain capability lifecycle and independent retry pass.
- [ ] PRD 00008 can attach without owning lifecycle policy.

## Unresolved Questions

None.


## Mandatory source: docs/dev/project-management/plans/implementation-plan.md

# OVCAQ implementation and migration plan

Status: accepted · Prepared: 2026-08-22 · Decisions reconciled: 2026-08-22 · Visibility: local/private
Scope: standalone package, macOS personal cutover, then a separate public-release
track

PRD decomposition: shared discovery is
`dev/local/discovery/00001-ovcaq-v1.md`; implementation PRDs are backlog
00002–00014; exact source-contract ownership and closeout rules are in
`dev/local/prds/implementation-plan-coverage.md`.

## Executive decision

Build OVCAQ as one installable Python package with the `ovcaq` command. It will
absorb the existing Python autopilot CLI, the real `statectl` implementation,
the Python supervisor loop, and tracon. Bash will no longer own product logic or
be required as the launcher.

OVCAQ will be agent-neutral at the process and telemetry boundaries, not a
general-purpose workflow engine. Its initial workflow remains the opinionated
PRD lifecycle already used by autopilot: select work, build, review/rework,
finalize, and drain. Claude Code and Codex are first-party adapters for the
personal cutover. A generic argv adapter, Linux support, compatibility
guarantees, and public publishing belong to a later public-release track.

Skills, agents, hooks, and plugins remain external. OVCAQ carries only a
declarative requirement manifest, generic capability lifecycle state, and
launcher-specific reconciliation code. It uses the launcher's supported
marketplace commands to check or explicitly install the required workflow and
post-drain agoge capabilities.

The cutover is deliberately light:

- no legacy command aliases in the released package;
- no dual writes;
- no old-state importer;
- no rollback framework;
- one two-PRD canary per launcher, then delete the old shell/skill-owned runtime
  only after both pass.

## 1. Outcomes

The personal-cutover milestone is complete when:

1. `uv tool install ovcaq` provides one `ovcaq` command and the TUI.
2. `ovcaq run --agent claude` can drain the same build/review/done workflow
   currently driven by `autoclaude`.
3. `ovcaq run --agent codex` can run the workflow through `codex exec --json`.
4. Every agent-authored state change is performed by an OVCAQ command.
5. The supervisor derives continuation from state, not the agent's final prose.
6. The TUI displays either provider through one normalized event model.
7. `ovcaq provision --agent <name> --check` detects missing launcher content and
   `--apply` reconciles it from an external marketplace.
8. Every non-empty drained batch runs the required pinned agoge capability;
   failure preserves drained PRDs, records actionable attention, exits nonzero,
   and can be retried without replaying a workflow phase.
9. Separate two-PRD Claude and Codex canaries prove full review, next-PRD
   continuation, final drain, and agoge on macOS.
10. No production path points into `~/.claude/skills/run-autopilot` or a user's
   dotfiles.

The later public-release track adds Linux support, the generic third-party driver
and decoder extension API, an explicit compatibility policy, and package
publication. None blocks the personal cutover.

### Non-goals for the personal cutover

- Arbitrary user-defined workflow graphs.
- Distributed/multi-host scheduling.
- A web dashboard or remote daemon API.
- Linux and Windows support.
- A generic third-party argv driver or decoder extension API.
- Cross-version state, CLI, driver, or event protocol compatibility guarantees.
- Public package publication and release-polish work.
- Cloud agents that cannot execute the local `ovcaq` CLI against the same
  working tree.
- Bundling or publishing the external Claude/Codex workflow plugins from this
  repository.
- Preserving the `autoclaude`, `autopilot`, `tracon`, or `statectl` command
  names.

## 2. Verified current system

This plan is based on the on-disk implementation and its PRDs, not the older
description of a Bash loop.

| Concern | Current owner | Finding | OVCAQ destination |
|---|---|---|---|
| terminal launch | `~/.config/bash/plugins/development.plugin.bash` | Bash does preflight, process-group/TUI job control, and delegates to Python | `ovcaq run` / `ovcaq attach` |
| supervisor loop | `~/.claude/skills/run-autopilot/cli/loop.py` | Python already owns routing, launch, retry, pause, park, metrics, drain | `runtime/` |
| agent launch | `cli/runner.py` | binary is injectable but argv/env/events are Claude-specific | `drivers/` + shared runner |
| state transaction | `cli/state.py` | one locked, validated, backed-up writer | `state/store.py` |
| ordinary mutations | `cli/statectl.py` | real 634-line implementation; script path is only a shim | `ovcaq state ...` |
| phase transitions | `cli/transitions.py` + `autopilot phase-done` | adjacent to statectl, not part of it | compound state/workflow commands |
| park/stall/defer | `cli/records.py` | filesystem saga with durable intent/retry | `workflow/records.py` |
| selection/frontmatter/policy | `cli/*.py` | mostly pure and extraction-ready | `workflow/` |
| telemetry/TUI | `scripts/tracon/*` | observer/control surface; not the loop driver | `events/` + `tui/` |
| workflow instructions | `run-autopilot/SKILL.md` and related skills/agents | loaded inside each provider session | external launcher plugins |
| installation | Claude plugin marketplace and personal skill paths | no single reconciler | `provision/` |

### 2.1 Statectl was planned and is implemented

The original design was PRD 00068: a stdlib CLI with generic
`get/set/append/del`, atomic replacement, an advisory lock, a rotating backup,
and refusal to overwrite corrupt state.

PRD 00051 introduced the real durable boundary:

- `schema.py` for validation/versioning;
- `state.py` for locked transactions, exclusive init, and restore;
- `records.py` for recoverable park/stall/defer operations;
- lifecycle CLI commands beside statectl.

PRD 00089 then moved statectl onto that sole validated writer and left
`scripts/statectl.py` as a compatibility shim. PRD 00120 made `state.tasks`
canonical and added compound task verbs. PRD 00132 fixed future-schema refusal,
help, and command/documentation truth.

Therefore OVCAQ must extract this implementation, not invent another state
manager. The architectural correction is to expose ordinary mutations and
lifecycle transitions under one installed command while preserving one store.

### 2.2 Current state guarantees worth keeping

- The lock covers the read, mutation, validation, backup, and replace.
- A mutation validates before changing the backup.
- The backup contains the raw pre-transaction bytes.
- Writes use a same-directory temporary file, file `fsync`, and `os.replace`.
- Init is create-only.
- Restore validates its input.
- Future schema versions are refused before the mutator runs.
- Compound task verbs resolve tasks by ID and update derived counts atomically.
- Park/stall use durable intent so a killed process can reconcile the next run.

Two existing gaps should be closed before declaring OVCAQ's state format
public:

- task/attempt element validation is shallow;
- the file is fsynced before rename, but the containing directory is not
  fsynced after rename.

### 2.3 The current portability seam is false

Changing `runner_bin` does not make the loop agent-neutral. The current runner
still constructs Claude flags, sets Claude/Warden environment variables,
expects Claude stream JSON, parses Anthropic errors and rate limits, and routes
Claude model identifiers.

The required seam is:

```text
agent adapter = launch specification + raw event decoder + session summary
```

The supervisor consumes only the summary and committed state. The TUI consumes
only normalized observations.

### 2.4 Codex provides the necessary headless contract

Official OpenAI documentation defines `codex exec` as the non-interactive
entry point. With `--json`, stdout is JSONL containing events such as
`thread.started`, `turn.started`, `item.*`, `turn.completed`, `turn.failed`, and
`error`, including token usage on completion. Workspace edits use the explicit
`--sandbox workspace-write` mode.

Useful documentation:

- <https://developers.openai.com/codex/non-interactive-mode>
- <https://developers.openai.com/codex/build-skills>
- <https://developers.openai.com/codex/build-plugins>

### 2.5 Marketplace boundary

Codex and Claude Code both have structured plugin/marketplace CLIs, but their
commands and manifests differ. OVCAQ must use adapters rather than edit config
files or caches directly.

Claude Code reconciliation primitives:

```text
claude plugin marketplace list --json
claude plugin marketplace add <source>
claude plugin list --available --json
claude plugin install <plugin>@<marketplace> --scope user
claude plugin update <plugin>@<marketplace>
```

Codex reconciliation primitives:

```text
codex plugin marketplace list --json
codex plugin marketplace add <source> --json
codex plugin marketplace upgrade <name>
codex plugin list --available --json
codex plugin add <plugin>@<marketplace> --json
```

Launcher content is split by native manifest format:

- Claude Code: `buvis/claude-plugins`
- Codex: `buvis/codex-plugins`

OVCAQ coordinates compatible releases and provisioning but never vendors either
marketplace's content.

## 3. Target operating model

```text
operator
  |
  | ovcaq run / attach / pause / stop / provision
  v
OVCAQ CLI ------------------------------------------------------+
  |                                                            |
  +--> provisioner --> launcher marketplace CLI --> plugin     |
  |                                                            |
  +--> supervisor --> agent driver --> claude/codex/custom     |
  |         |                 |                                |
  |         |                 +--> raw session JSONL            |
  |         |                                                  |
  |         +--> normalized observations --> metrics/events ----+--> TUI
  |         |
  |         +--> decision(state delta, session summary)
  |                           |
  +--> state service <--------+<-- agent invokes `ovcaq state`
             |
             +--> dev/local/ovcaq/state.json
```

One headless agent session performs one workflow handoff. It reads the external
autopilot skill, does the current phase, commits the transition through OVCAQ,
and exits. The supervisor rereads state and either launches the next fresh
session, waits, pauses, parks, stops, or drains.

## 4. Product and package boundaries

### Core package contains

- project/config/path discovery;
- schema and transactional persistence;
- task, transition, selection, park/stall/defer, and reporting commands;
- run registry and duplicate-run locking;
- process-group ownership, signals, watchdog, and session log retention;
- decision table and retry policy;
- normalized event types and reducers;
- built-in Claude and Codex drivers for the personal cutover;
- a generic argv driver and decoder entry points in the later public-release
  track;
- Textual/Rich TUI;
- launcher marketplace reconciliation adapters;
- declarative external requirement metadata;
- tests and sanitized event fixtures.

### External marketplace content contains

- `run-autopilot` workflow instructions for each launcher;
- build/planning/review skills;
- reviewer/subagent definitions;
- launcher hooks that enforce direct-state-edit bans or context/review gates;
- the required post-drain agoge capability and any optional safety plugins;
- launcher-specific prompt syntax and skill metadata.

### Boundary rule

An external skill may depend on the `ovcaq` executable and its documented state
protocol. OVCAQ must never import or execute Python modules from the plugin
cache. The only coupling is versioned CLI/protocol metadata.

## 5. Repository shape

```text
ovcaq/
├── AGENTS.md
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── src/
│   └── ovcaq/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── paths.py
│       ├── errors.py
│       ├── state/
│       │   ├── schema.py
│       │   ├── store.py
│       │   ├── paths.py
│       │   └── commands.py
│       ├── workflow/
│       │   ├── transitions.py
│       │   ├── selection.py
│       │   ├── frontmatter.py
│       │   ├── resume.py
│       │   ├── policy.py
│       │   ├── records.py
│       │   └── reports.py
│       ├── runtime/
│       │   ├── supervisor.py
│       │   ├── decision.py
│       │   ├── registry.py
│       │   ├── process.py
│       │   ├── watchdog.py
│       │   ├── capability.py
│       │   └── session.py
│       ├── drivers/
│       │   ├── base.py
│       │   ├── claude.py
│       │   ├── codex.py
│       │   └── command.py
│       ├── events/
│       │   ├── model.py
│       │   ├── reducer.py
│       │   └── tail.py
│       ├── tui/
│       │   ├── app.py
│       │   ├── discovery.py
│       │   ├── model.py
│       │   └── panels.py
│       ├── provision/
│       │   ├── manifest.py
│       │   ├── reconcile.py
│       │   ├── claude.py
│       │   └── codex.py
│       └── resources/
│           └── extensions.toml
├── tests/
│   ├── fixtures/
│   │   ├── claude/
│   │   └── codex/
│   ├── state/
│   ├── workflow/
│   ├── runtime/
│   ├── drivers/
│   ├── tui/
│   └── provision/
└── docs/
    ├── state-protocol.md
    ├── driver-protocol.md
    └── operations.md
```

### Dependency direction

```text
state <- workflow <- runtime <- CLI/TUI
events <- drivers <- runtime
provision <- CLI
```

`state` imports no workflow/runtime/provider/UI module. `workflow` imports only
state and stdlib. Drivers can import normalized event types but not TUI.
Provisioning is independent of runtime execution.

## 6. Public command design

### Operator commands

| Command | Responsibility |
|---|---|
| `ovcaq init` | create project config/runtime directories and fresh state |
| `ovcaq run [--agent NAME] [--no-tui]` | preflight, start one supervisor, attach TUI by default on a TTY |
| `ovcaq attach [--root PATH]` | observe/control an existing run; fleet view when root omitted |
| `ovcaq status [--json]` | deterministic run/state summary |
| `ovcaq pause` | request a boundary pause through state |
| `ovcaq resume` | clear an operator pause and run/reattach |
| `ovcaq stop` | stop the active process group and record the stopped outcome |
| `ovcaq logs [--session ID]` | locate/tail retained raw or normalized logs |
| `ovcaq logs purge --before YYYY-MM-DD [--apply]` | preview or explicitly delete retained logs older than a cutoff; never runs automatically |
| `ovcaq doctor [--agent NAME]` | check Python, agent binary/auth, plugin requirements, paths, locks |
| `ovcaq provision --agent NAME --check` | report marketplace/plugin drift without mutation |
| `ovcaq provision --agent NAME --apply` | idempotently add/upgrade/install required external content |
| `ovcaq capability retry agoge` | retry failed post-drain QA without replaying completed workflow phases |

`run` performs `provision --check` and fails with a concrete remediation command.
It does not silently install or update third-party content.

### Workflow commands

These replace today's mixed `autopilot` subcommands:

```text
ovcaq workflow select
ovcaq workflow frontmatter --prd PATH
ovcaq workflow phase-complete --outcome OUTCOME
ovcaq workflow resume-target
ovcaq workflow check-plan
ovcaq workflow stall --prd NAME --site SITE --detail TEXT
ovcaq workflow park
ovcaq workflow defer --prd NAME --record FILE
ovcaq workflow complete-prd --prd NAME
ovcaq workflow render audit|report|metrics
```

### State commands

Agent instructions use compound verbs whenever one exists:

```text
ovcaq state show [--json]
ovcaq state validate
ovcaq state get PATH
ovcaq state set PATH JSON
ovcaq state append PATH JSON
ovcaq state delete PATH
ovcaq state task add FILE
ovcaq state task start ID
ovcaq state task attempt ID FILE
ovcaq state task complete ID FILE
ovcaq state task set-body ID FILE
ovcaq state task set-meta ID FILE
ovcaq state task set-status ID STATUS
ovcaq state task clear
ovcaq state contract set FILE
ovcaq state restore
```

Generic set/append/delete remain recovery escape hatches. Transition-owned
fields reject generic mutation unless `--unsafe` is explicitly supplied. Normal
skills never use `--unsafe`.

### CLI output contract

- Human output goes to stderr for mutations/progress and stdout for requested
  data.
- Every machine-consumed command supports `--json` or emits JSON by definition.
- Errors have stable symbolic codes in JSON in addition to process exit codes.
- Mutation commands are idempotent where operationally required.
- Help is generated from the live parser/command registry and tested against
  documentation examples.

## 7. Configuration and paths

Configuration precedence:

1. CLI flags.
2. tracked project `ovcaq.toml`.
3. user config at `${XDG_CONFIG_HOME:-~/.config}/ovcaq/config.toml`.
4. package defaults.

Avoid the current broad `_AUTOPILOT_*` environment surface. Environment
variables are reserved for secrets, CI/test path overrides, and launcher needs.

Example project configuration:

```toml
version = 1
agent = "codex"

[workflow]
prd_root = "dev/local/prds"
runtime_root = "dev/local/ovcaq"

[agents.codex]
sandbox = "workspace-write"
approval = "never"

[phases.build]
effort = "high"
timeout_seconds = 7200

[phases.review]
effort = "xhigh"
timeout_seconds = 10800

[extensions.codex]
marketplace = "buvis-plugins"
source = "buvis/codex-plugins"
plugin = "ovcaq-autopilot"

[capabilities.agoge]
timeout_seconds = 3600
```

Runtime files default to:

```text
<repo>/dev/local/ovcaq/
  state.json
  state.json.lock
  state.json.bak
  run.lock
  run.json
  events.jsonl
  metrics.jsonl
  sessions/<session-id>/raw.jsonl
  sessions/<session-id>/meta.json
  sessions/<session-id>/summary.json
  reports/
```

Raw session logs and agoge output are durable evidence. Create them with
user-only permissions and retain them indefinitely by default. Normal run
cleanup removes only ephemeral locks, live registry entries, and temporary
files. Deletion occurs only through an explicit `ovcaq logs purge ... --apply`
or a documented manual operation; OVCAQ never schedules log expiry.

Fleet registry entries live under
`${XDG_STATE_HOME:-~/.local/state}/ovcaq/runs/`. The per-project `run.lock`, not
the registry PID alone, is the duplicate-run authority.

## 8. State design

### 8.1 Authority

`state.json` is the authoritative workflow handoff. Event and metric logs are
observational and may lag or be absent without changing the next action.

Only `StateStore.transaction()` writes the file. Both the public state CLI and
internal supervisor/workflow services call the same application service.

### 8.2 Initial schema

Use a clean OVCAQ v1 schema rather than preserving today's flat file solely for
compatibility:

```json
{
  "schema_version": 1,
  "revision": 17,
  "batch": {
    "id": "20260822-123456",
    "status": "running",
    "completed_prds": [],
    "parks_consecutive": 0,
    "capabilities": {
      "agoge": {
        "required": true,
        "launcher": "codex",
        "plugin": "agoge",
        "version": "0.1.1",
        "failure": "attention",
        "status": "pending",
        "attempts": []
      }
    }
  },
  "work": {
    "prd": "00140-example.md",
    "phase": "build",
    "next_phase": "review",
    "completed_phases": [],
    "work_start_sha": null,
    "repo_root": "/repo"
  },
  "tasks": [],
  "review": {
    "cycle": 0,
    "cap": 3,
    "cycles": [],
    "decisions": [],
    "doubts": []
  },
  "control": {
    "pause_requested": false,
    "pause_reason": null,
    "attention": null
  },
  "recovery": {
    "operation": null,
    "replan_count": 0,
    "phase_fingerprint": null,
    "phase_repeats": 0
  }
}
```

The implementation task must create a field-by-field schema document and map
every live current field to one of: retained, renamed, derived, event-only, or
retired. Do not copy unknown historical fields into v1 by default.

### 8.3 Transaction contract

For every mutation:

1. Open/create `<state>.lock` and take an exclusive lock.
2. Read and parse the current bytes while holding the lock.
3. Refuse future schema versions.
4. Verify optional compare-and-set `revision` when supplied.
5. Deep-copy before passing state to mutation logic.
6. Apply exactly one compound mutation.
7. Validate the complete resulting schema, including task, attempt, and
   capability elements.
8. Increment `revision`.
9. Write and file-fsync a same-directory temporary backup of current bytes.
10. Atomically replace `<state>.bak`.
11. Write and file-fsync the new state to a same-directory temporary file.
12. Atomically replace `state.json`.
13. Directory-fsync after both published renames where supported.
14. Release the lock.

If mutation or validation fails, both state and backup remain byte-identical.

### 8.4 Control intent

Replace loose pause/park/state-write marker files with typed state fields or a
typed recovery operation written through the store:

- pause is a durable `control.pause_requested` intent consumed only at a
  session boundary;
- stop is an immediate process signal plus a supervisor-authored state outcome;
- park/stall is a durable `recovery.operation` saga reconciled on restart;
- state-write failure is a supervisor error when possible; the only last-resort
  side channel is an emergency file written when the store cannot function.

### 8.5 Agent contract

Every launcher skill must state:

- never edit `state.json`;
- read with `ovcaq state show/get`;
- write tasks and outcomes using compound commands;
- call `ovcaq workflow phase-complete` exactly once at handoff;
- end the session after the command succeeds;
- if a state write fails twice, stop work and leave the repository unchanged
  except for already committed work.

### 8.6 Post-drain capability contract

Agoge is external launcher content, but OVCAQ owns its provider-neutral lifecycle:

1. Batch initialization resolves and pins the selected launcher's required
   `agoge` capability, including plugin and compatible version. Missing or
   incompatible content fails preflight before the first workflow phase.
2. A non-empty final drain commits all PRD completion state and atomically marks
   agoge `pending`. Empty batches skip it explicitly.
3. The supervisor records a unique attempt, marks it `running`, and invokes the
   launcher's capability without shell evaluation. Its raw output is retained as
   session evidence.
4. Success marks agoge `succeeded` and completes the batch with exit code zero.
5. Failure marks agoge `failed`, records actionable `control.attention`, and
   sets the batch status to `attention`. The supervisor exits nonzero without
   changing drained PRDs or replaying a workflow phase.
6. `ovcaq capability retry agoge` starts a new idempotent attempt from `failed`.
   It refuses while a live attempt owns the capability and reconciles a stale
   `running` attempt before retrying.

Capability states are `pending`, `running`, `failed`, `succeeded`, or `skipped`.
Every transition uses the state store; launcher plugins never write capability
state directly. Required capabilities must be `succeeded` before batch status
becomes `completed`.

## 9. Workflow core

Keep the initial lifecycle fixed and deterministic:

```text
build + tasks_done   -> review
review + rework      -> review (cycle + 1, clear cycle-local data)
review + converged   -> done
done + more_prds     -> build (reset per-PRD fields)
done + drained       -> drained
build + drained      -> drained
```

`drained` is terminal for the PRD workflow, not necessarily for batch
finalization. A non-empty drained batch remains supervisor-owned until required
post-drain capabilities are `succeeded`; a capability failure leaves the PRD
result drained while the batch exits with attention.

Move these current pure modules first:

- PRD selection: lowest sequence in `wip`, then `backlog`, never `hold`;
- frontmatter parsing/defaults;
- transition table and full effect set;
- resume-target mapping;
- plan-size policy.

Move `records` after the store. Park/stall is a filesystem saga, so preserve
the current failpoint/retry matrix around intent, verified move, deferred
record, reset, and commit.

Workflow logic must not know which agent executes a phase. Agent/model routing
is runtime configuration keyed by phase.

## 10. Driver protocol

### 10.1 Types

```python
@dataclass(frozen=True)
class LaunchRequest:
    root: Path
    phase: str
    prompt: str
    model: str | None
    effort: str | None
    timeout_seconds: int
    session_dir: Path

@dataclass(frozen=True)
class LaunchSpec:
    argv: tuple[str, ...]
    env: Mapping[str, str]
    cwd: Path
    raw_format: str

@dataclass(frozen=True)
class SessionSummary:
    success: bool
    session_id: str | None
    failure_class: str | None
    failure_detail: str | None
    rate_limit_reset_at: datetime | None
    usage: Usage | None
```

```python
class AgentDriver(Protocol):
    name: str

    def probe(self) -> DriverHealth: ...
    def build_launch(self, request: LaunchRequest) -> LaunchSpec: ...
    def decode(self, raw_line: str) -> Iterable[Observation]: ...
    def summarize(self, observations: Iterable[Observation], exit_code: int) -> SessionSummary: ...
```

No driver returns a workflow decision.

### 10.2 Discovery

Built-ins register by name. Third-party packages register through the
`ovcaq.drivers` Python entry-point group. `ovcaq doctor` lists discovered
drivers and validates duplicate names.

### 10.3 Claude driver

Characterize and then relocate the current launch contract:

```text
claude -p
  --permission-mode auto
  --model <configured>
  --effort <configured>
  [--fallback-model <configured>]
  --output-format stream-json
  --verbose
  <provider-specific invocation of run-autopilot>
```

The driver alone owns Claude environment variables, model suffixes, stream
decoder, Anthropic rate-limit/connectivity handling, and native task/subagent
event attribution.

### 10.4 Codex driver

Start from the documented CLI contract and validate exact flags against the
installed version in tests:

```text
codex
  --ask-for-approval never
  exec
  --json
  --sandbox workspace-write
  -C <repo>
  [-m <configured>]
  <prompt invoking the installed run-autopilot skill>
```

Decode `thread.started`, `turn.*`, `item.*`, and `error`. Do not require cost
if Codex exposes only tokens. Unsupported telemetry stays unknown rather than
estimated as fact.

### 10.5 Generic command driver

Allow an argv template in config, never a shell string. It receives a generated
prompt file and environment variables naming the repository and state path. It
can run the workflow with raw-only telemetry. Optional decoder packages may add
structured observations later.

## 11. Normalized event protocol

Each observation contains:

```text
protocol_version
timestamp
provider
run_id
session_id (optional until known)
lane_id (optional)
type
payload
```

Required types:

- `session.started`
- `activity.message`
- `tool.started`, `tool.completed`, `tool.failed`
- `lane.started`, `lane.progress`, `lane.completed`, `lane.failed`
- `usage.updated`
- `rate_limit.started`, `rate_limit.cleared`
- `session.completed`, `session.failed`
- `raw.unknown`

Rules:

- Decoder never raises for an unknown/malformed line.
- Raw output is written before decoding.
- Usage counters are monotonic within a session and deduplicated by provider
  event identity when available.
- `estimated=true` is mandatory on inferred values.
- Failure classes are a closed core vocabulary (`rate_limit`, `connectivity`,
  `permission`, `authentication`, `timeout`, `agent`, `unknown`) plus raw detail.
- Provider-native payloads do not leak into state.

## 12. Supervisor and process model

### 12.1 Single-run ownership

- Supervisor takes a non-blocking exclusive `run.lock` in the project runtime
  directory for its full lifetime.
- Registry is discovery metadata, not the lock.
- Registry records root, PID, process start identity, run ID, agent, and start
  time; it is written atomically.
- Stale entries are pruned centrally by one shared registry module used by CLI
  and TUI.

### 12.2 Agent ownership

- Spawn every agent without `shell=True`, with stdin closed.
- Create a dedicated process group/session for the agent tree.
- Watchdog sends TERM, waits a configured grace period, then KILLs the group.
- Supervisor signal handling cancels the live group, records the result when the
  store is available, removes registry metadata, and releases its lock.
- Orphan detection is based on owned process groups/run identity, not duplicated
  `ps` regexes in loop and TUI.

### 12.3 Decision ordering

After a session exits:

1. Read state and compare revision/mtime to the pre-launch snapshot.
2. A valid productive state transition wins over provider exit noise.
3. Honor requested pause.
4. A drained workflow with a required `pending`, stale `running`, or `failed`
   post-drain capability follows the capability contract; failure exits nonzero
   and never reopens a completed workflow phase.
5. Empty next phase plus all required capabilities `succeeded` or `skipped`
   means the batch is complete.
6. A changed state with another phase means continue.
7. With no state progress, inspect normalized rate-limit/failure summary.
8. Wait for a bounded provider rate limit when reset information is credible.
9. Retry a bounded connectivity/session death.
10. Detect repeated identical phase fingerprints.
11. Park the selected PRD or halt a bootstrap/systemic failure.

This preserves the strongest current property: workflow state wins over prose
and incidental process exit status.

### 12.4 Run/TUI relationship

`ovcaq run` starts the supervisor as the owned background process and attaches
the TUI on an interactive terminal. `q` detaches; `p` requests a boundary
pause; `s` confirms and stops the process group. `ovcaq run --no-tui` keeps the
supervisor in the foreground for CI/headless use. `ovcaq attach` never starts a
second supervisor.

## 13. TUI migration

Move tracon only after the shared state, registry, event, and driver types are
stable.

Keep:

- fleet and project detail views;
- phase/task/review presentation;
- live log tailing with inode/truncation handling;
- usage, cost when available, duration, and activity lanes;
- pause/stop/detach controls;
- degraded operation when logs or metrics are incomplete.

Change:

- rebrand all tracon/autoclaude/Claude-specific text;
- consume normalized observations rather than Claude JSON directly;
- share registry/liveness code with runtime;
- use XDG theme/config paths;
- show provider and telemetry capability gaps explicitly;
- model state-write failure, parking, stopping, and systemic halt as statuses;
- remove clipboard/platform behavior unless implemented through a small
  capability adapter.

The TUI must remain optional for correctness. A broken Textual dependency or
terminal cannot prevent `ovcaq run --no-tui`.

## 14. Provisioning external launcher content

### 14.1 Requirement manifest

Ship identifiers, not content:

```toml
manifest_version = 1

[[requirement]]
launcher = "claude"
marketplace_name = "buvis-plugins"
marketplace_source = "buvis/claude-plugins"
plugin = "ovcaq-autopilot"
version = ">=1,<2"
capability = "workflow.autopilot"
required = true

[[requirement]]
launcher = "codex"
marketplace_name = "buvis-plugins"
marketplace_source = "buvis/codex-plugins"
plugin = "ovcaq-autopilot"
version = ">=1,<2"
capability = "workflow.autopilot"
required = true

[[requirement]]
launcher = "claude"
marketplace_name = "buvis-plugins"
marketplace_source = "buvis/claude-plugins"
plugin = "agoge"
version = ">=0.1,<1"
capability = "post_drain.agoge"
required = true

[[requirement]]
launcher = "codex"
marketplace_name = "buvis-plugins"
marketplace_source = "buvis/codex-plugins"
plugin = "agoge"
version = ">=0.1,<1"
capability = "post_drain.agoge"
required = true
```

Project/user config may override the source or version for local development.
An override cannot make agoge optional in the personal-cutover profile.

### 14.2 Reconciliation algorithm

For the chosen launcher:

1. Locate the binary through PATH/mise guidance and report its version.
2. Run the launcher's structured marketplace list.
3. Add the configured marketplace only under `--apply`.
4. Upgrade/refresh its snapshot only under `--apply`.
5. List available/installed plugins as JSON.
6. Verify the required plugin and acceptable version.
7. Install/update only under `--apply`.
8. Re-list and verify the postcondition.
9. Run a launcher-specific skill/plugin visibility probe when possible.
10. Emit a machine-readable reconciliation report.

Every step is idempotent. A failed install leaves a clear launcher command for
manual repair. OVCAQ does not install the Claude/Codex binary, log the user in,
or bypass workspace/admin policy.

### 14.3 Batch pinning

At batch start, record resolved versions of required enforcement, workflow, and
post-drain capability plugins in state. Refuse a new phase after unexpected
mid-batch drift unless the operator explicitly refreshes the pin. Keep this
provider-neutral by storing launcher/plugin/version/capability tuples. The batch
contract also records whether each capability is required and its failure policy.

## 15. Security and failure policy

- Default Codex to `workspace-write` and explicit approval policy; never default
  to danger-full-access or bypass flags.
- Treat Claude unattended permissions as a driver configuration with a loud
  preflight, not a hidden global default.
- Never interpolate plugin sources, paths, models, or prompt text into a shell.
- Redact environment values and likely secrets from normalized logs while
  retaining the original raw file with user-only permissions.
- Create runtime files with restrictive permissions.
- Validate configured project/runtime paths remain under the resolved project
  unless the user explicitly supplies an external state root.
- A provider decoder failure cannot crash the loop.
- A state failure is fail-closed: do not launch another agent when the
  authoritative handoff cannot be read or written.
- Provisioning is dry-run/check by default and mutates only under `--apply`.

## 16. Test strategy

### 16.1 State tests

- missing/corrupt/non-object/future-schema input;
- whole-schema and changed-field rejection;
- complete task/attempt/review/batch/capability element validation;
- two-process concurrent mutations with no lost updates;
- compare-and-set revision conflicts;
- mutator/validator exceptions preserve state and backup bytes;
- kill/failpoints before and after every durable boundary;
- file and directory fsync behavior through injected functions;
- create-only init and validated restore;
- generic path parsing including negative indices;
- compound task counts and task-ID resolution;
- permissions on created files.

### 16.2 Workflow tests

- every transition's full effect set;
- unknown phase/outcome rejection;
- PRD selection ordering and hold exclusion;
- frontmatter defaults/warnings;
- reset ownership and batch preservation;
- park/stall failpoint reconciliation and idempotent records;
- drain and next-PRD behavior;
- report rendering idempotency.
- post-drain capability state transitions never reopen drained PRD state.

### 16.3 Driver contract tests

For every driver:

- exact argv and environment additions;
- cwd/stdin/process-group behavior;
- raw output byte preservation;
- decoder totality over malformed/unknown lines;
- session/model ID extraction;
- terminal result/failure classification;
- token/cost semantics and estimation flags;
- rate-limit/reset handling;
- TERM/KILL response.

Sanitized full JSONL fixtures are required for healthy, tool-active,
subagent/lane, rate-limited, connectivity-failed, permission-failed, and
malformed sessions for both Claude and Codex.

### 16.4 Decision tests

Run the same decision matrix with fake Claude and Codex drivers during personal
cutover, then add the generic driver to the matrix in Phase 10:

- productive state + nonzero provider exit: state wins;
- untouched state + success prose: no false progress;
- rate limit with/without reset time;
- bounded connectivity retry;
- timeout and genuine death;
- repeated phase fingerprint;
- park versus bootstrap halt;
- operator pause/stop/drain;
- mid-batch capability drift;
- agoge success, failure, stale-running reconciliation, and independent retry.

### 16.5 Process/registry tests

- duplicate run refused by lock;
- stale/malformed/recycled-PID registry entries;
- detach/reattach;
- TUI crash leaves supervisor alive;
- supervisor crash kills owned agent group;
- Ctrl-C/TERM/HUP exit codes and cleanup;
- timeout TERM then KILL;
- no unrelated process is signalled;
- macOS CI coverage for personal-cutover process assumptions.

### 16.6 Provisioning tests

Use fake launcher executables and captured JSON:

- marketplace absent/present/stale;
- plugin absent/present/disabled/wrong version;
- check never mutates;
- apply emits exact supported commands;
- second apply is a no-op;
- partial failure reports the remaining drift;
- unsupported launcher capability produces a manual action, not config edits.
- required agoge absent/present/incompatible for both launchers;
- failed agoge remains retryable without changing drained PRDs.

### 16.7 Retention tests

- raw session and agoge logs use user-only permissions;
- normal completion removes ephemeral locks/registry entries but retains evidence;
- no timer, startup path, or completion path automatically deletes retained logs;
- purge defaults to preview, refuses active sessions, and deletes only the
  explicitly selected cutoff under `--apply`.

### 16.8 Packaging gates

- install wheel into a clean temporary environment;
- run `ovcaq --help`, state, doctor, and no-TUI smoke outside the checkout;
- import from a cwd containing a decoy `cli/` package;
- no production `sys.path.insert`;
- no live-home fixtures or hardcoded `/Users/bob` paths;
- no `~/.claude/skills/run-autopilot` literals;
- provider-neutral module scan;
- sdist and wheel contain required resources but no plugin/skill contents.

## 17. Detailed implementation sequence

Each phase ends with a commit and its exit criteria. Do not begin a later phase
to hide a failing earlier boundary. Phases 0–9 are the personal-cutover track and
map one-to-one to independently planned and reviewed PRDs. Phases 10–12 form the
later public-release track and do not block personal cutover.

### Phase 0 — repository and contract baseline

Goal: make the new repository installable and preserve evidence before moving
behavior.

Tasks:

- [ ] [P00-T01] Add `pyproject.toml` for Python 3.12+, src layout, `ovcaq` console script,
  Textual/Rich runtime dependencies, and pytest/ruff/mypy dev groups.
- [ ] [P00-T02] Add `uv.lock`, package version, license, CI, and release skeleton.
- [ ] [P00-T03] Create empty package boundaries matching section 5; no copied production
  logic yet.
- [ ] [P00-T04] Copy only sanitized golden fixtures and establish provenance notes.
- [ ] [P00-T05] Inventory every current CLI command, state field, loop decision,
  environment knob, shell behavior, tracon status, and test file.
- [ ] [P00-T06] Create machine-checked migration manifests for those inventories
  and reconcile downstream PRDs/coverage against the characterized evidence.
- [ ] [P00-T07] Capture baseline results of current state/CLI/loop/tracon suites.
- [ ] [P00-T08] Add clean-wheel/import-from-arbitrary-cwd smoke tests.

Exit criteria:

- clean `uv sync`, lint, type, test, and wheel build;
- every current behavior has a target or explicit retirement entry;
- no production behavior copied without a characterization test.

### Phase 1 — state kernel

Goal: land the standalone sole writer before any caller moves.

Tasks:

- [ ] [P01-T01] Port `schema.py` into `ovcaq.state.schema` and define the cleaned v1
  schema/field crosswalk.
- [ ] [P01-T02] Deepen validation for task, attempt, review, batch, capability, control,
  and recovery entries.
- [ ] [P01-T03] Port transaction/load/init/restore into `ovcaq.state.store`.
- [ ] [P01-T04] Add directory fsync after atomic publication where supported.
- [ ] [P01-T05] Add monotonic `revision` and optional compare-and-set.
- [ ] [P01-T06] Retain one rotating raw-byte backup and create-only init.
- [ ] [P01-T07] Port generic JSON path parser/mutations as recovery operations.
- [ ] [P01-T08] Port compound task and contract-card operations.
- [ ] [P01-T09] Make transition-owned paths reject generic writes without `--unsafe`.
- [ ] [P01-T10] Implement `ovcaq state` parser, JSON errors, and generated help.
- [ ] [P01-T11] Port all state/statectl tests without shim or sys.path assumptions.
- [ ] [P01-T12] Add real multi-process and kill/failpoint durability tests.

Exit criteria:

- all state writes flow through one store;
- a failed mutation cannot alter state or backup;
- full schema validates every documented nested owner;
- installed `ovcaq state` works outside the checkout.

### Phase 2 — deterministic workflow core

Goal: move decisions that need no agent or UI.

Tasks:

- [ ] [P02-T01] Port PRD selection and lifecycle directory resolution.
- [ ] [P02-T02] Port frontmatter parsing/defaults and overwrite warnings.
- [ ] [P02-T03] Port transition table and compound `phase-complete` command.
- [ ] [P02-T04] Port resume mapping and plan-size policy.
- [ ] [P02-T05] Port reset and completed-PRD summary derivation.
- [ ] [P02-T06] Port defer ledger with idempotent operation IDs.
- [ ] [P02-T07] Port stall/park filesystem saga and every existing failpoint.
- [ ] [P02-T08] Port deterministic audit/report/metrics rendering.
- [ ] [P02-T09] Replace hardcoded `dev/local/autopilot` with configured
  `dev/local/ovcaq`.
- [ ] [P02-T10] Generate workflow command documentation from the parser.

Exit criteria:

- current lifecycle fixtures have equivalent OVCAQ outcomes under the new
  schema;
- park/stall interruption is recoverable at every durable boundary;
- workflow package imports no runtime, driver, TUI, or launcher module.

### Phase 3 — shared runtime substrate

Goal: consolidate process, registry, path, and session ownership before moving
the loop or TUI.

Tasks:

- [ ] [P03-T01] Implement project/root/runtime discovery in `paths.py`.
- [ ] [P03-T02] Implement per-project `run.lock` duplicate guard.
- [ ] [P03-T03] Implement one atomic XDG fleet registry and stale-entry pruning.
- [ ] [P03-T04] Define run/session metadata and directory lifecycle.
- [ ] [P03-T05] Implement process-group spawn/TERM/KILL with no shell.
- [ ] [P03-T06] Port watchdog with injectable clock and grace period.
- [ ] [P03-T07] Implement raw session tee before any decoding.
- [ ] [P03-T08] Implement retained-log inventory plus preview/apply purge with active-run
  refusal and no automatic expiry path.
- [ ] [P03-T09] Make `status`/`doctor` report retained evidence size and the exact purge
  preview command.
- [ ] [P03-T10] Implement signal cleanup and emergency state-write failure reporting.
- [ ] [P03-T11] Add platform capability probes and macOS integration tests.

Exit criteria:

- duplicate supervisors cannot start;
- owned agent trees stop without touching unrelated processes;
- registry metadata and live session state survive detach;
- completion removes only ephemeral registry/lock/temp artifacts and retains raw
  session evidence indefinitely.

### Phase 4 — event protocol and Claude adapter

Goal: move the existing behavior through the new adapter seam before adding a
second provider.

Tasks:

- [ ] [P04-T01] Define `Observation`, `Usage`, `SessionSummary`, and failure classes.
- [ ] [P04-T02] Implement raw-line-tolerant reducers and normalized event persistence.
- [ ] [P04-T03] Implement driver registry/entry-point discovery.
- [ ] [P04-T04] Port the exact Claude launch contract into `drivers/claude.py`.
- [ ] [P04-T05] Port Claude stream decoding, task/lane attribution, usage, and cost.
- [ ] [P04-T06] Move Claude rate-limit/connectivity parsing behind the driver.
- [ ] [P04-T07] Replace Claude model constants in shared routing with per-agent config.
- [ ] [P04-T08] Port sanitized Claude fixtures and exact argv/event tests.
- [ ] [P04-T09] Add provider-neutral import/string guard tests.

Exit criteria:

- Claude can complete one scripted fake-agent loop through the adapter;
- shared runtime/TUI-facing modules contain no Claude parsing;
- unknown Claude events degrade safely.

### Phase 5 — supervisor loop

Goal: replace `cli/loop.py` and the Bash loop entry.

Tasks:

- [ ] [P05-T01] Extract the post-session decision table as a pure function.
- [ ] [P05-T02] Port phase/model/effort/timeout routing from config.
- [ ] [P05-T03] Port state snapshot/progress/fingerprint logic.
- [ ] [P05-T04] Port bounded rate-limit, connectivity, death, park, and systemic-halt
  behavior using `SessionSummary`.
- [ ] [P05-T05] Port pause, stop, drain, archive, metrics, and notification behavior.
- [ ] [P05-T06] Implement the provider-neutral post-drain capability state machine,
  including durable attempts, failure attention, and independent retry against
  a fake agoge capability.
- [ ] [P05-T07] Implement `ovcaq run --no-tui` foreground supervisor.
- [ ] [P05-T08] Add exact one-metric-row-per-session behavior.
- [ ] [P05-T09] Test every row of the existing 00106 parity inventory against the new
  destination or an explicit retirement.

Exit criteria:

- a fake Claude driver drains build/review/done without Bash;
- every continuation is explainable from state + summary;
- the old Python loop's decision inventory is fully accounted for.

### Phase 6 — TUI extraction and Python launcher

Goal: absorb tracon and eliminate Bash job-control ownership.

Tasks:

- [ ] [P06-T01] Port log tailing and tolerant state/metrics projections.
- [ ] [P06-T02] Port fleet discovery onto the shared registry.
- [ ] [P06-T03] Port phase/task/review panels onto normalized observations.
- [ ] [P06-T04] Present post-drain capability pending/running/failed/succeeded status and
  actionable retry guidance.
- [ ] [P06-T05] Port pause/stop/detach/help controls using public services.
- [ ] [P06-T06] Rebrand all user-facing strings and XDG paths to OVCAQ.
- [ ] [P06-T07] Add raw-only/unknown-provider degradation.
- [ ] [P06-T08] Implement `ovcaq attach` and TTY-default attachment from `ovcaq run`.
- [ ] [P06-T09] Make Textual failure fall back to the foreground/plain renderer.
- [ ] [P06-T10] Port terminal/process integration scenarios from the Bash suite.

Exit criteria:

- TUI crash/detach does not kill the supervisor;
- pause/stop act on exactly one selected run;
- no duplicate registry/liveness implementation remains;
- Bash is unnecessary for run or attach.

### Phase 7 — Codex adapter

Goal: run the same state workflow through Codex CLI.

Tasks:

- [ ] [P07-T01] Capture sanitized installed-version Codex JSONL fixtures.
- [ ] [P07-T02] Implement exact `codex exec --json` launch spec with explicit sandbox,
  approval, cwd, model, and prompt handling.
- [ ] [P07-T03] Decode thread, turn, item, tool, file-change, MCP, web, usage, and error
  events that are actually present.
- [ ] [P07-T04] Implement Codex-specific auth/rate-limit/failure classification.
- [ ] [P07-T05] Write a provider-specific prompt that invokes the installed autopilot
  skill and enforces state-only handoff.
- [ ] [P07-T06] Run the shared driver and decision conformance suites.
- [ ] [P07-T07] Verify TUI provider/activity/usage display and raw fallback.

Exit criteria:

- Codex completes build/review/done against fixture/fake execution;
- exact argv, decoder, and state-handoff contracts pass without requiring
  launcher-global plugin mutation;
- the supervisor has zero Codex-specific branches.

### Phase 8 — external plugin provisioning

Goal: make launcher readiness declarative and reproducible without bundling
workflow content.

Tasks:

- [ ] [P08-T01] Finalize the external plugin requirement manifest/version contract.
- [ ] [P08-T02] Implement generic reconciliation plan/report types.
- [ ] [P08-T03] Implement Claude marketplace list/add/update/install/check adapter.
- [ ] [P08-T04] Implement Codex marketplace list/add/upgrade/add/check adapter.
- [ ] [P08-T05] Implement `ovcaq provision --check|--apply` and `doctor` integration.
- [ ] [P08-T06] Make `run` refuse missing/incompatible required content with the exact
  remediation command.
- [ ] [P08-T07] Require compatible workflow and agoge capabilities for both launchers.
- [ ] [P08-T08] Record resolved plugin/capability versions in batch state and enforce drift
  checks.
- [ ] [P08-T09] Test with fake CLIs and local marketplace fixtures.
- [ ] [P08-T10] Create linked work packages in the external repositories, then
  coordinate a Claude plugin and Codex plugin that expose the same OVCAQ state
  protocol and required agoge capability; publication requires explicit approval.
- [ ] [P08-T11] After explicit local provisioning, run one real Codex smoke phase that
  commits an OVCAQ state handoff and one isolated agoge smoke for each launcher.

Exit criteria:

- fresh launcher setup reaches ready state from one explicit apply command;
- second apply is a no-op;
- real Codex workflow and both launcher-specific agoge capability probes pass;
- the wheel contains requirement metadata but no skill/agent/plugin contents.

### Phase 9 — one-way local cutover

Goal: move the personal workflow to OVCAQ and delete the duplicate runtime.

Tasks:

- [ ] [P09-T01] Ensure no legacy autopilot batch is running; complete or abandon it.
- [ ] [P09-T02] Install the local OVCAQ wheel with `uv tool install`.
- [ ] [P09-T03] Provision/update the external Claude workflow and agoge capabilities.
- [ ] [P09-T04] Run a two-PRD Claude canary through build, every mandated review lens,
  done, next-PRD continuation, final drain, and successful agoge.
- [ ] [P09-T05] Provision/update the external Codex workflow and agoge capabilities.
- [ ] [P09-T06] Run a separate two-PRD Codex canary proving the same full path.
- [ ] [P09-T07] Verify both canaries retained raw evidence and pinned capability versions.
- [ ] [P09-T08] Record both passing gates and obtain explicit approval for the
  enumerated migration targets before removing any legacy runtime entry point.
- [ ] [P09-T09] Remove `tracon`, `autopilot`, and `autoclaude` shell functions and their
  tests.
- [ ] [P09-T10] Remove the extracted CLI/runtime/tracon code from the personal
  `run-autopilot` skill, leaving only external plugin content where appropriate.
- [ ] [P09-T11] Remove the stale Codex personal autopilot skill/hook implementation.
- [ ] [P09-T12] Update global instructions to name `ovcaq run` and the external workflow
  plugin.
- [ ] [P09-T13] Verify `rg` finds no live invocation of old commands or direct state edits.

Exit criteria:

- both launchers use the installed OVCAQ package;
- separate two-PRD canary records prove full review, continuation, drain, and
  agoge for Claude and Codex;
- only one state/runtime implementation exists;
- old state is archived or deleted, not migrated;
- all personal docs and commands point to OVCAQ.

Personal cutover is complete here. The following phases are a separate
public-release track.

### Phase 10 — generic driver and extension API

Goal: substantiate “any AI agent” beyond two first-party providers.

Tasks:

- [ ] [P10-T01] Implement configured argv driver with placeholder validation and no shell.
- [ ] [P10-T02] Define/install a sample third-party decoder through Python entry points.
- [ ] [P10-T03] Document minimum loop capability versus rich telemetry capability.
- [ ] [P10-T04] Add raw-only TUI and generic failure behavior.
- [ ] [P10-T05] Add driver conformance command: `ovcaq doctor --driver NAME`.
- [ ] [P10-T06] Publish the stable driver/event protocol and compatibility policy.

Exit criteria:

- a fake third-party package registers a driver without core changes;
- raw-only execution can advance state and drain;
- unavailable telemetry is visibly unknown, never fabricated.

### Phase 11 — Linux support

Goal: add Linux to the supported public package without making it a retroactive
personal-cutover gate.

Tasks:

- [ ] [P11-T01] Run state-lock, file/directory fsync, process-group, signal, registry, and
  watchdog integration suites on Linux.
- [ ] [P11-T02] Replace or capability-gate any remaining macOS-only runtime or TUI behavior.
- [ ] [P11-T03] Validate XDG paths, terminal detach/attach, and no-TUI operation on Linux.
- [ ] [P11-T04] Add Linux wheel installation and clean-environment smoke tests to CI.
- [ ] [P11-T05] Document supported distributions and required system capabilities.

Exit criteria:

- macOS and Linux pass the same provider-neutral state/runtime contract suites;
- both first-party launchers pass supported Linux smoke tests;
- unsupported platform capabilities fail in `doctor` with actionable guidance.

### Phase 12 — public release

Goal: publish a maintainable first public release.

Tasks:

- [ ] [P12-T01] Complete operator, state protocol, driver protocol, provisioning, and
  troubleshooting docs.
- [ ] [P12-T02] Declare stable state and CLI compatibility policies, including the first
  migration guarantees that follow the fresh-state personal cutover.
- [ ] [P12-T03] Add architecture decision records for state authority, adapter seam, and
  external plugin boundary.
- [ ] [P12-T04] Run full lint/type/unit/integration/packaging matrices.
- [ ] [P12-T05] Run security review of subprocess/config/path/log handling.
- [ ] [P12-T06] Build and inspect sdist/wheel contents.
- [ ] [P12-T07] Obtain explicit release authorization for the exact commit,
  version, artifact checksums, and destinations; then tag and publish the first
  package release.
- [ ] [P12-T08] Document marketplace plugin minimum versions paired with the release.

Exit criteria:

- clean install can provision and run either first-party launcher on supported
  macOS and Linux environments;
- a sample third-party driver installs and passes its published conformance
  contract;
- versioned protocol docs match tests;
- release artifacts contain no personal paths, state, transcripts, or plugin
  content.

## 18. Migration mapping

| ID | Current artifact | Destination | Disposition |
|---|---|---|---|
| M01 | `cli/schema.py` | `state/schema.py` | port and deepen |
| M02 | `cli/state.py` | `state/store.py` | port; add revision + directory fsync |
| M03 | `cli/statectl.py` | `state/commands.py` + CLI | split generic/domain operations |
| M04 | `scripts/statectl.py` | none | delete shim |
| M05 | `cli/transitions.py` | `workflow/transitions.py` | port |
| M06 | `cli/selection.py` | `workflow/selection.py` | port |
| M07 | `cli/frontmatter.py` | `workflow/frontmatter.py` | port |
| M08 | `cli/resume.py` | `workflow/resume.py` | port |
| M09 | `cli/policy.py` | `workflow/policy.py` | port |
| M10 | `cli/records.py` | `workflow/records.py` | port saga/failpoints |
| M11 | `cli/render_*` | `workflow/reports.py` | consolidate |
| M12 | `cli/routing.py` | config + drivers/runtime | remove model globals |
| M13 | `cli/runner.py` | `runtime/process.py` + drivers | split common/provider |
| M14 | `cli/usage_limit.py` | provider drivers | split by provider |
| M15 | `cli/watchdog.py` | `runtime/watchdog.py` | port process-group semantics |
| M16 | `cli/loop.py` | runtime modules | split decisions/effects/registry |
| M17 | `scripts/tracon/*` | events + tui | port last; normalize/rebrand |
| M18 | `scripts/render_stream.py` | driver decoder/plain renderer | split |
| M19 | `_walk_up.py` | `paths.py` | replace with installed package logic |
| M20 | Bash wrapper/job control | `ovcaq run/attach` | replace in Python |
| M21 | post-drain `run_agoge` glue | capability lifecycle + external agoge plugins | replace swallowed failure with durable retryable outcome |
| M22 | Claude workflow skill | external Claude plugin | rewrite to OVCAQ CLI |
| M23 | stale Codex workflow skill | external Codex plugin | replace, do not incrementally fix |

## 19. Personal-cutover acceptance checklist

- [ ] [A01] One installed console command.
- [ ] [A02] Fresh state under `dev/local/ovcaq`.
- [ ] [A03] No direct agent edits of state.
- [ ] [A04] Full nested schema validation and atomic durability tests.
- [ ] [A05] Pure transition/decision tables covered row-by-row.
- [ ] [A06] Claude and Codex adapter conformance.
- [ ] [A07] Raw and normalized session evidence retained indefinitely by default with
  user-only permissions; purge is explicit and preview-first.
- [ ] [A08] TUI works for both first-party launchers.
- [ ] [A09] Duplicate run and process cleanup integration tests.
- [ ] [A10] Provision check/apply is idempotent for both launchers and verifies the
  required workflow and agoge capabilities.
- [ ] [A11] Agoge failure preserves drained PRDs, exits nonzero with attention, and is
  independently retryable.
- [ ] [A12] Separate two-PRD Claude and Codex canaries prove full review,
  continuation, final drain, and agoge.
- [ ] [A13] External content absent from wheel.
- [ ] [A14] No production personal paths or `sys.path` bootstraps.
- [ ] [A15] No old aliases or dual runtime after cutover.

## 20. Principal risks

1. **Self-hosted cutover:** the current workflow implements its replacement.
   Mitigation: build and test OVCAQ independently, cut only with no live batch,
   and require separate passing two-PRD Claude and Codex canaries before deleting
   the old code.
2. **State saga regression:** park/stall crosses state and filesystem
   boundaries. Mitigation: port the existing durable intent and failpoint matrix
   before refactoring its shape.
3. **Process-tree leaks:** direct-child watchdog behavior may leave nested
   processes. Mitigation: own a process group/session and test TERM/KILL with
   grandchildren.
4. **Provider event drift:** CLI JSON schemas evolve. Mitigation: tolerant
   decoders, raw retention, versioned fixtures, and unknown-event fallback.
5. **Provisioning mutates user-global launcher state:** Mitigation: check by
   default, explicit `--apply`, structured postcondition verification, no cache
   editing.
6. **Required capability coupling:** workflow completion depends on compatible
   external agoge content. Mitigation: preflight and pin it at batch start,
   persist every attempt, and retry failure without reopening drained work.
7. **Sensitive log accumulation:** raw evidence may contain secrets or consume
   disk indefinitely. Mitigation: user-only permissions, documented location,
   visibility in `doctor`, and an explicit preview-first purge command.
8. **Over-generalization:** a generic workflow engine would delay the real
   extraction. Mitigation: keep the autopilot lifecycle fixed; generalize only
   the first-party adapter and capability edges until personal cutover; defer the
   generic driver to the public-release track.

## 21. Resolved decisions

1. This local implementation plan remains authoritative under `AGENTS.md`.
   Discovery decisions are inputs merged here, not a competing contract.
2. Personal cutover is a macOS-only milestone. Generic drivers, Linux,
   compatibility guarantees, and publishing are a later public-release track.
3. Agoge is required external content. OVCAQ owns a generic durable capability
   lifecycle, while launcher marketplaces own the implementation.
4. Phase 7 proves Codex with fixtures/fakes; Phase 8 provisions compatible
   external content and runs the first real Codex smoke.
5. Legacy removal requires a separate two-PRD canary for Claude and Codex.
6. Raw logs remain indefinitely by default; only an explicit preview-first purge
   removes them.
7. Personal-cutover Phases 0–9 map one-to-one to independently reviewed PRDs.
8. Linux is required before the first public release, not before personal
   cutover.
9. OVCAQ uses the MIT license for the initial package and public release.
10. Real launcher-global mutation, external-repository publication, legacy
    removal, release tagging, and package publication require explicit approval
    for enumerated targets after their prerequisite evidence passes.

## 22. Unresolved questions

None.


## Mandatory source: docs/dev/project-management/prds/implementation-plan-coverage.md

# OVCAQ implementation-plan PRD coverage

Status: accepted | Scope: umbrella Phases 0–12 | Updated: 2026-08-23

Accepted source-plan SHA-256:
`43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`

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

1. Implement PRDs numerically; a later phase cannot hide a failing dependency.
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


## Mandatory source: docs/dev/project-management/discovery/00001-ovcaq-v1.md

# Discovery: OVCAQ personal cutover

## Classification

Depth: comprehensive | Date: 2026-08-22 | Status: resolved

OVCAQ is a cross-cutting extraction spanning durable state, workflow policy,
process supervision, provider adapters, telemetry, a TUI, provisioning, and a
one-way migration. The decisions from this discovery have been merged into
`dev/local/plans/implementation-plan.md`, which remains the implementation
authority under `AGENTS.md`. Both are legitimate local-workflow artifacts and
source decision records.

## Problem

The working autopilot system is split across a personal Claude Code skill,
Python modules, shell launch glue, direct launcher assumptions, and the tracon
TUI. Its apparent agent seam is not portable: shared runtime code still owns
Claude-specific arguments, environment variables, events, models, and failure
handling. OVCAQ must consolidate that behavior behind one installed command
without weakening state durability or lifecycle decisions during the
self-hosted cutover.

The primary personal-cutover user is the repository owner. A successful local
cutover defines this milestone; public reuse is secondary.

## Requirements

### Must have

- Replace the current personal `autoclaude`/autopilot runtime with one
  installable `ovcaq` command and one authoritative state writer.
- Preserve the fixed PRD lifecycle and make continuation depend on committed
  state plus a normalized session result, never final agent prose.
- Keep provider-specific launch, event, model, and failure behavior behind
  driver boundaries.
- Support the existing Claude workflow and a Codex workflow through external
  launcher plugins rather than bundled skills, agents, hooks, or plugins.
- Declare post-drain agoge as a required default capability, reconcile it only
  under explicit `--apply`, and include its compatible version and failure
  behavior in the batch contract.
- If agoge fails, preserve the drained PRD result, persist actionable
  attention, exit nonzero, and allow agoge to be retried without replaying any
  completed workflow phase.
- Preserve raw session evidence while making normalized telemetry tolerant of
  malformed and unknown provider events.
- Retain raw session logs indefinitely with user-only permissions and no
  automatic deletion; provide an explicit preview-first purge command and
  document manual cleanup.
- Complete a one-way local canary and remove the duplicate personal runtime
  after both launcher paths are proven.
- Deliver the personal cutover as a sequenced PRD series grouped by architectural
  dependency boundaries, with one independently reviewed PRD per implementation
  boundary and the local implementation plan as the umbrella contract.

### Later public-release track

- Make installation and configuration convenient for other solo developers.
- Add Linux support as a gate for the first public release.
- Provide a generic third-party driver extension path.
- Declare stable state, CLI, driver, and event compatibility policies.
- Publish a polished public package after the personal cutover is stable.

### Out of scope for personal cutover

- Arbitrary workflow graphs.
- Distributed or multi-host scheduling.
- A web dashboard or remote daemon API.
- Cloud agents without access to the local repository and `ovcaq` CLI.
- Legacy command aliases, old-state import, dual writes, or a rollback
  framework.
- Bundling external launcher content in the OVCAQ package.
- Linux support in the personal-cutover milestone.
- The generic third-party driver API and sample external decoder.
- Public package publishing and its release-polish work.

## Constraints

- Every durable state mutation must use the sole state store.
- State and workflow modules remain provider-neutral.
- Configured commands are argv arrays and are never shell-evaluated.
- Provisioning checks by default and mutates launcher-global state only under
  explicit `--apply`.
- A compatible agoge capability is required at batch start and pinned with the
  other resolved external capabilities.
- The initial migration is a fresh-state, one-way cutover.
- The personal-cutover milestone targets macOS only; Linux is deferred until the
  public-release track.
- Personal cutover ends at successful Claude and Codex canaries plus
  legacy-runtime removal; generic-driver and public-release phases do not block
  it.
- Schema and CLI protocol versions support validation and future-version
  refusal, but personal cutover makes no cross-version compatibility guarantee;
  breaking upgrades may require fresh state until stability is explicitly
  declared.
- Raw logs are retained until manually deleted. OVCAQ must not expire them
  automatically during personal cutover; `ovcaq logs purge` previews by default and
  deletes only under an explicit apply action.
- Python 3.12+, `uv`, pytest, ruff, and mypy define the package toolchain.

## Codebase Context

- **Relevant code**: The production tree currently contains only `README.md` and
  `AGENTS.md`; local discovery and planning live under `dev/local/`. The
  extraction source is the personal `run-autopilot` skill, including a 1,239-line
  supervisor loop, 634-line state CLI, 615-line records saga, and roughly
  2,565 lines of tracon models, discovery, stream, panels, and screens.
- **Conventions**: The current implementation uses small pure workflow
  functions beside explicit state, process, and UI boundaries, with colocated
  pytest characterization tests and golden fixtures.
- **Integration points**: State/schema/statectl, transitions/selection/resume,
  park/stall records, runner/watchdog/loop, tracon, shell launcher glue, and
  the external Claude and Codex plugin repositories.
- **Similar implementations**: The existing state transaction and recoverable
  park/stall saga are the behavioral references to port and deepen rather than
  redesign opportunistically.

## Approach

- **Chosen**: Extract the existing proven lifecycle in dependency order—state,
  pure workflow, runtime, Claude/events, supervisor, TUI, Codex, then
  provisioning—and perform a fresh-state local cutover. Specify each
  implementation boundary as its own PRD so it must satisfy independent exit
  criteria and review before its consumers move.
- **Why**: It preserves evidence and minimizes the self-hosted migration risk
  while correcting the false provider seam.
- **Rejected alternatives**:
  - General workflow engine first: expands scope without helping the personal
    cutover.
  - Compatibility migration: creates dual ownership and rollback complexity
    for an early-stage one-way extraction.
  - Plugin content inside core: couples package releases to launcher-native
    skills and manifests.

## Success Criteria

- A two-PRD canary batch drains through the installed OVCAQ package for each of
  Claude and Codex, proving build, full review, done, next-PRD continuation,
  final drain, and the required post-drain agoge run.
- All state changes are attributable to OVCAQ commands or services, and no
  production path invokes the old runtime after cutover.
- State, decision, process-group, driver, TUI, provisioning, and packaging
  acceptance tests pass on macOS.

## Risks

- **Self-hosted cutover**: Build independently, cut over only without a live
  legacy batch, run a two-PRD canary through each launcher, then remove the old
  runtime.
- **State saga regression**: Port the durable intent and failpoint matrix before
  changing its shape.
- **Provider event drift**: Preserve raw JSONL and make decoding total with an
  explicit unknown observation.
- **Required extension coupling**: Pin a compatible agoge version at batch
  start and fail preflight or post-drain explicitly when it is unavailable;
  keep post-drain retry independent from completed PRD state.
- **Scope inflation**: Keep generic-driver, Linux, compatibility, and publishing
  work off the personal-cutover critical path; execute them in the later
  public-release track.
- **Pre-stability protocol churn**: Keep protocol versions explicit and refuse
  unknown future state, but document when an upgrade requires a fresh batch
  rather than building migration machinery prematurely.
- **Sensitive log accumulation**: Create raw logs with user-only permissions,
  redact normalized output, expose their location in diagnostics, and provide a
  preview-first explicit purge command; personal cutover deliberately performs
  no automatic pruning.

## Recommended PRD Sequence

1. **Package baseline**: scaffold the installable package and preserve
   characterization evidence.
2. **State kernel**: land the sole durable writer, cleaned schema, and state CLI.
3. **Deterministic workflow core**: extract selection, transitions, policy,
   reports, and recoverable park/stall records onto the new state schema.
4. **Shared runtime substrate**: establish path, registry, process-group,
   watchdog, session, and raw-evidence ownership.
5. **Event protocol and Claude adapter**: normalize evidence and move the first
   provider behind the driver contract.
6. **Supervisor loop**: implement state-led continuation and the durable generic
   post-drain capability lifecycle against fakes.
7. **TUI and Python launcher**: move tracon onto shared models and remove Bash
   ownership of run/attach behavior.
8. **Codex adapter**: prove argv, decoding, and handoff against fixtures/fakes;
   do not require launcher-global plugin mutation yet.
9. **Provisioning and required external content**: reconcile Claude/Codex
   workflow plugins and agoge, coordinate companion repositories, then run the
   first real Codex and launcher-specific agoge smoke tests.
10. **Personal cutover**: run separate two-PRD canaries for both launchers,
    verify agoge and retained evidence, then remove the legacy runtime and update
    dotfiles/instructions.

Generic-driver support, Linux, compatibility guarantees, and public publishing
belong to a later PRD series.

## Discovery Log

### Q1: Who is the primary personal-cutover user?

**Answer**: The repository owner. A successful personal cutover is sufficient;
public reuse is secondary.

### Q2: Must personal cutover support Linux?

**Answer**: No. Personal cutover supports macOS only; Linux follows
before the later public release.

### Q3: Is post-drain agoge required for personal cutover?

**Answer**: Yes. Agoge is required in the default capability manifest, but
launcher-global installation still occurs only under explicit `--apply`.

### Q4: Where does the personal-cutover boundary end?

**Answer**: After Claude and Codex macOS canaries, required
provisioning/agoge, and deletion of the old runtime. Generic-driver support,
Linux, and public publishing are deferred.

### Q5: Should personal cutover be one PRD or multiple sequenced PRDs?

**Answer**: Use one independently reviewed PRD for each of the ten
personal-cutover implementation boundaries.

### Q6: What live canary is sufficient before deleting the legacy runtime?

**Answer**: One two-PRD batch per launcher, proving next-PRD continuation as
well as full review, drain, and agoge.

### Q7: What persists if required post-drain agoge fails?

**Answer**: Completed PRDs remain drained. OVCAQ persists actionable attention,
exits nonzero, and permits an independent agoge retry without replaying workflow
phases.

### Q8: When does the state/CLI protocol become compatibility-stable?

**Answer**: No cross-version compatibility guarantee is made until stability
is explicitly declared. Pre-stability breaking changes may require fresh state.

### Q9: How should personal cutover retain raw session logs?

**Answer**: Indefinitely. OVCAQ performs no automatic expiry. Operators may use
an explicit `ovcaq logs purge` command that previews by default and deletes only
under an apply action.

### Q10: Which document is authoritative after discovery?

**Answer**: The local `dev/local/plans/implementation-plan.md`. Accepted
discovery decisions are merged there. Both documents remain legitimate
local-workflow records; tracking status does not determine authority.

### Q11: When does the first real Codex smoke run?

**Answer**: The Codex adapter PRD is fixture/fake-only. The first real smoke runs
in the following provisioning PRD after compatible external workflow content is
installed explicitly.

### Q12: Where do generic-driver, Linux, and publishing work belong?

**Answer**: In a separate public-release PRD series after personal cutover.
Linux is required before the first public release; none of the three blocks
personal cutover.
