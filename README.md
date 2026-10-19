# OVCAQ

**Orchestration, Visibility, and Control for Agent Queues.**

OVCAQ is an agent-neutral supervisor for the PRD-driven workflow currently
implemented by the Claude Code `autoclaude`/autopilot loop, `statectl`, and the
tracon TUI.

The core package provides:

- durable workflow state and its CLI;
- queue/lifecycle transitions;
- supervised headless agent sessions;
- normalized telemetry and the terminal UI;
- launcher checks. External plugin reconciliation remains planned.

Agent instructions, skills, agents, hooks, and plugins remain in external
marketplaces and are not bundled in this repository.

Status: **development**. State, workflow, process supervision, Claude and Codex
adapters, and the terminal UI are implemented. Provisioning, personal cutover,
and public release remain held work.

## Development

Install [mise](https://mise.jdx.dev/), review and trust this repository's
`mise.toml`, then run `mise install` and `./tools/onboard`.
Python 3.12.13 and uv 0.13.0 are pinned; Python 3.12+ is supported.
Onboarding uses `uv.lock` and does not configure Git hooks or agent plugins.

| Command | Purpose |
| --- | --- |
| `./tools/onboard` | Synchronize all development dependencies from the lockfile |
| `./tools/check` | Check lint, formatting, types, tests, and distribution builds |
| `./tools/format` | Apply Python formatting |
| `./tools/run-tests tests/state -q` | Run selected tests |
| `./tools/build` | Build source and wheel distributions in `dist/` |

Each shim runs its same-named mise task from its own checkout and forwards
arguments and exit status. Activate mise in your shell to use bare command names
from `tools/`. Tasks do not install missing mise tools automatically; run
`mise install` explicitly when needed. CI uses the same uv check implementations.

Use `uv run ovcaq --help` for the live command interface. See the generated
[operator reference](docs/operations.md), [state protocol](docs/state-protocol.md),
[driver protocol](docs/driver-protocol.md), and
[architecture overview](docs/dev/architecture/README.md).
