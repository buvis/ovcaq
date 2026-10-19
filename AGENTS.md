# AGENTS.md — OVCAQ

OVCAQ means **Orchestration, Visibility, and Control for Agent Queues**. It is
an installable Python CLI/TUI that supervises a PRD-driven workflow through
Claude Code, Codex, or another headless coding agent.

The global `AGENTS.md` remains in force. This file adds project-specific rules.

## Current state

State, workflow, runtime, adapters, and the TUI are implemented. Provisioning,
personal cutover, and public release remain held work.
The maintainer's implementation plan, kept outside this repository, retains
architecture and sequencing authority. Do not create production modules
opportunistically outside that sequence. Read applicable nested AGENTS.md files before editing
their scopes if the host has not loaded them.

## Product boundary

OVCAQ core owns state, lifecycle commands, process supervision, agent adapters,
normalized events, observability, the TUI, and launcher provisioning checks.

OVCAQ core does **not** contain launcher-specific skills, agents, hooks, or
plugins. Those live in external marketplaces. Core may carry declarative
identifiers and version requirements needed to reconcile them.

## Architecture invariants

1. **One state writer.** Every durable `state.json` mutation goes through the
   state store. Agents mutate state only through `ovcaq state` or a higher-level
   OVCAQ command. Never instruct an agent to edit `state.json` directly.
2. **State decides; prose does not.** Session completion, phase handoff, pause,
   drain, retry, and failure decisions derive from committed state plus a
   normalized session result. A final agent message is never authoritative.
3. **Provider code stays at the edge.** Claude/Codex argv, environment variables,
   event formats, model names, rate-limit parsing, and connectivity checks live
   under their adapter. Shared runtime and UI code must not parse provider-native
   events.
4. **Raw evidence survives normalization.** Preserve each session's raw output.
   Normalizers are tolerant and must degrade to an unknown/raw observation
   instead of crashing the supervisor.
5. **The TUI observes shared models.** It reads state, registry, metrics, and
   normalized observations. It does not implement lifecycle policy or maintain a
   second liveness algorithm.
6. **External capabilities stay external.** Provisioning invokes a launcher's
   supported marketplace/plugin CLI and verifies the result. It does not copy
   plugin contents into this package or hand-edit launcher caches.
7. **No shell evaluation of configured commands.** Store agent commands as argv
   arrays and spawn them without `shell=True`.

## Target layout

```text
src/ovcaq/
  state/        # schema, transactions, compound mutations
  workflow/     # PRD selection, transitions, records, policy
  runtime/      # supervisor, decisions, registry, process ownership
  drivers/      # Claude, Codex, and generic command adapters
  events/       # normalized event model and session reduction
  tui/          # discovery and Textual/Rich presentation
  provision/    # marketplace/plugin reconciliation
tests/          # mirrors package boundaries; provider JSONL fixtures
docs/           # tracked architecture and operator documentation
```

## Toolchain

- Python 3.12+ managed through `mise`.
- `uv` for environments, locking, build, and command execution.
- `pytest` for tests; `ruff` for formatting/linting; `mypy` for package types.
- Keep the runtime dependency set small. Textual/Rich are justified by the TUI;
  prefer the standard library for state, locking, configuration, and subprocesses.

Development commands are defined in `mise.toml`; executable `tools/` shims run
them from this checkout. Setup and verification:

```bash
mise install
./tools/onboard
./tools/check
```

## Development rules

- Characterize current behavior before moving it from `~/.claude`.
- Extract state first, then pure workflow logic, runtime, adapters, TUI, and
  provisioning in that order.
- Sanitized Claude and Codex JSONL fixtures belong in `tests/fixtures/`; tests
  never read live files from `~/.claude` or `~/.codex`.
- Test process-group, lock, and signal behavior with real subprocesses in
  addition to unit tests.
- Documentation for commands comes from the same command registry/parser as the
  implementation; do not maintain a second hand-written verb inventory.
- Keep provider-neutral modules free of the strings `claude`, `anthropic`,
  `codex`, and provider model identifiers except in tests that enforce this rule.
- Use conventional commits. No compatibility shim, dual writer, or rollback
  framework is required for the initial cutover.

## Migration stance

This is a one-way early-stage extraction. Start a fresh OVCAQ batch/state tree;
do not build an importer for the current `docs/dev/project-management/autopilot/state.json` unless
a later requirement explicitly needs it. Temporary delegation during a local
canary is acceptable, but do not ship `autoclaude`, `autopilot`, `tracon`, or
`statectl` aliases as permanent public APIs.
