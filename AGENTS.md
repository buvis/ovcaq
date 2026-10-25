# AGENTS.md — OVCAQ

OVCAQ means **Orchestration, Visibility, and Control for Agent Queues**.
It supervises agent sessions and collaboration above Claude Code, Codex and
other supported drivers. The global AGENTS.md remains in force.

## Current state and target

The current Python 3.12 application still bundles workflow state and a TUI.
The approved three-layer target moves workflow authority into Autopilot's
external controller and terminal presentation into Lantern (working name).
OVCAQ retains headless orchestration, drivers, execution records and operations API.
The [architecture](docs/dev/architecture/README.md) distinguishes current code from target.
Private planning under docs/dev/project-management defines sequencing; do not
extract opportunistically or remove services before their consumer passes parity.
Provisioning, personal cutover and public release remain held.

## Ownership invariants

1. **One workflow writer.** Before extraction this is the existing StateStore;
   after PRD00058 it is the external controller. Never dual-write or silently
   fall back. Agents never edit workflow state.json directly.
2. **State decides; prose does not.** Controller-accepted workflow state and
   normalized execution facts determine continuation. Final messages and exit
   zero cannot authorize completion or waive review requirements.
3. **OVCAQ owns execution.** Process identity, driver placement, fresh sessions,
   collaboration, retry, waves/worktrees and cleanup stay above agent sessions.
   An execution journal is not a second copy of workflow truth.
4. **Provider code stays at the edge.** Provider argv/environment/events/models
   and failure classification live in drivers. Preserve raw evidence; unknown
   events degrade explicitly instead of crashing supervision.
5. **Presentation stays external.** Lantern consumes the public operations API.
   OVCAQ owns shared projection/liveness and validates controls. UI detachment
   or failure cannot stop a run; headless installation needs no UI dependencies.
6. **External capabilities stay external.** Never bundle plugin/controller/TUI
   content or import plugin-cache Python. Provision through supported launcher
   interfaces and verify concrete versions/contracts.
7. **No shell evaluation of configured commands.** Use explicit argv arrays.

## Code boundaries

- src/ovcaq/runtime: supervision, process ownership and execution journal.
- src/ovcaq/drivers and events: adapters and normalized/raw observations.
- src/ovcaq/state and workflow: current implementation; extracted by PRD00058.
- src/ovcaq/tui: current presentation; removed only after PRD00065 parity.
- Planned workflow_client and operations: public controller/API boundaries.
- tests: temporary projects, process fixtures and installed-artifact checks.

## Toolchain and verification

- Python 3.12+ through mise; uv for environments/builds and dependencies.
- pytest, ruff and mypy; setup with ./tools/onboard, verify with ./tools/check.
- Keep dependencies small; remove Textual/Rich from core during TUI extraction.
- Characterize source behavior before moving it; retain mapped regression evidence.
- Test locks, process groups, identity and signals with real subprocesses.
- Never read live ~/.claude or ~/.codex files in tests or mutate the executing
  batch's workflow state. Use sanitized fixtures and temporary roots.
- Generate command documentation from the parser; no parallel verb inventory.
- Keep provider-neutral modules free of provider/model identifiers except
  boundary tests that enforce this rule.
- Use conventional commits; read applicable nested AGENTS.md before edits.

## Migration stance

Use fresh workflow/execution trees, not a legacy-state importer. Preserve all
required plugin behaviors, review boundaries and source-disposition evidence.
Current implementation and temporary adapters can coexist during development,
but only one workflow authority may serve a run. No permanent autoclaude,
autopilot, tracon or statectl command aliases, dual writer or rollback framework.
No source retirement, live installation or publication follows from planning.
