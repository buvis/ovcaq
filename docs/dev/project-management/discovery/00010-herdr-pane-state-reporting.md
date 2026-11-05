# Discovery: Herdr compatibility, report loop state to the hosting pane

## Classification

Depth: standard | Date: 2026-11-01 | Status: open (idea, preliminary research)

## Problem

The operator runs the OVCAQ loop inside a [Herdr](https://herdr.dev) pane,
in the project workspace or in a worktree workspace Herdr created. Herdr's
sidebar shows every pane's agent and lifecycle state (`idle`, `working`,
`blocked`, `done`, `unknown`) and drives notifications and sounds from it.
Herdr learns that state in two ways: screen-manifest detection for agents it
knows (Claude, Codex, ...), or explicit reports from an integration over its
socket API. An OVCAQ pane fits neither: the screen shows OVCAQ's log or TUI,
not a Claude prompt box, and OVCAQ never reports. The expected result is a
pane that reads `unknown`, flaps between states, or carries a stale Claude
session, while the loop is actually building, parked, or waiting for the
operator. The state of the loop must be visible and correct wherever Herdr
shows the project or worktree it runs in.

Two concrete defects are predictable from code reading alone (unmeasured in a
live pane so far, see Q1):

1. **Headless children inherit the pane identity.** The supervisor launches
   `claude -p` with `os.environ | spec.env`
   (`src/ovcaq/runtime/supervisor.py:647`), so `HERDR_ENV`, `HERDR_PANE_ID`
   and `HERDR_SOCKET_PATH` reach each headless session. The installed Herdr
   Claude integration (`~/.claude/hooks/herdr-agent-state.sh`, v11) fires on
   every `SessionStart`, including print mode, and sends
   `pane.report_agent_session` with the headless session id. Herdr then
   records that headless session as the pane's Claude session and, with the
   default `[session] resume_agents_on_restore = true`, would try to resume a
   `claude -p` transcript interactively after a server restart. The Codex
   hook in `~/.codex/herdr-agent-state.sh` does the same for Codex children.
2. **Nothing reports OVCAQ's own state.** Herdr's process detection may name
   the pane `claude` after the child process and then run the Claude screen
   manifest against OVCAQ output, which matches nothing, or it shows the pane
   as a plain shell. Either way the sidebar does not say "working" during a
   session, "blocked" when a PRD parks or auth fails, or "done" when the
   batch drains.

## Requirements

### Must have

- When `HERDR_ENV=1`, `HERDR_PANE_ID` and `HERDR_SOCKET_PATH` are set in the
  supervisor's environment, the supervisor reports its lifecycle to that
  pane through `pane.report_agent` with `source = "ovcaq"`,
  `agent = "ovcaq"`, a monotonic `seq` (`time.time_ns()`), and a short
  `message`. Mapping from supervisor events to Herdr states:

  | Supervisor event | Herdr state | Message |
  | --- | --- | --- |
  | `_attempt` opened a session | `working` | `<phase> <prd> · session N` |
  | `apply(WAIT)` (rate-limit or connectivity backoff) | `working` | decision reason plus wait seconds |
  | `apply(RETRY)`, `apply(CONTINUE)`, capability run | `working` | decision reason |
  | `apply(PARK)`, `HALT` with attention, auth or permission failure, `state-write-failed`, emergency failure | `blocked` | decision reason or attention detail |
  | `run()` returns with `PAUSE` or `COMPLETE` | `idle` | `paused` or `batch complete` |
  | `run()` returns with any other terminal decision | `blocked` | decision reason |

  Herdr derives `done` itself (`idle` not yet seen), so a finished batch
  surfaces as Herdr's done badge and completion sound.
- Outside Herdr (any of the three variables missing) the reporter is a
  no-op. Report failures (socket missing, timeout, error reply) are ignored
  and never affect supervision; the connect timeout stays well under one
  second, matching Herdr's own hooks.
- Driver children never see Herdr's pane identity: strip every `HERDR_*`
  key (and `TERM_PROGRAM=herdr`) from the environment OVCAQ passes to
  `OwnedProcess.spawn` so the Claude and Codex Herdr hooks stay silent inside
  headless sessions. OVCAQ is the single reporter for its pane.
- Transport is the newline-delimited JSON socket protocol over
  `HERDR_SOCKET_PATH` with the stdlib `socket` module, the same shape the
  installed hooks use. No dependency on the `herdr` binary or its version.
- Tests: a pytest fixture runs a throwaway Unix socket server, captures the
  request lines, and asserts method, params and state sequence for one
  session, a park, and a drained batch; a test asserts the no-op when the
  variables are missing; a launch test asserts the scrubbed child
  environment. No live `~/.config/herdr` access.

### Nice to have

- `pane.report_metadata` with `title = "<prd> <phase>"` and tokens `prd`,
  `phase`, `cycle`, `driver`, so the operator can add `$prd` or `$phase` to
  `[ui.sidebar.agents] rows` in Herdr's config. `display_agent = "ovcaq:
  claude"` names the driver without claiming a built-in agent name.
- Report the active PRD and phase through the message even in TUI mode, so
  the collapsed sidebar rail stays informative.

### Out of scope

- Multi-worktree waves (PRD 00061). A pane can report only for itself; a
  loop that fans out to several worktrees cannot address the other
  workspaces' panes. Revisit with workspace metadata when waves land.
- Controlling Herdr (splitting panes, starting agents). OVCAQ only reports.
- A Herdr detection manifest or `herdr integration install ovcaq`. Herdr
  documents reporting from the agent's own code as the supported route; a
  new agent kind needs a Herdr binary change and is unnecessary here.
- Tower. Herdr reporting is a liveness sink the supervisor pushes to, like
  a terminal title, not a UI that reads the operations API. When PRD 00064
  ships, the sink can move to a consumer of that API without changing what
  Herdr sees.

## Constraints

- Herdr 0.9.5 is installed via mise; docs for that exact tag are at
  `https://raw.githubusercontent.com/herdrdev/herdr/v0.9.5/docs/next/website/src/content/docs/`
  (`socket-api.mdx`, `add-herdr-support.mdx`, `agents.mdx`,
  `integrations.mdx`, `cli-reference.mdx`).
- Reportable states are `idle | working | blocked | unknown`. `source` must
  not start with `herdr:`; `agent` must be OVCAQ's own name, not `claude`.
  Reports with a `seq` not above the last accepted one are ignored.
- Once a source reports, Herdr skips screen detection for the pane and the
  source holds lifecycle authority until `pane.release_agent`, or until the
  pane returns to an idle shell prompt, which clears the agent within a
  second or two.
- Sandboxed sessions (`~/bin/run-agent`, buvis PRD 00160) do not see Herdr's
  real socket. `HERDR_SOCKET_PATH` points at `~/.config/herdr-relay/relay.sock`,
  and `~/bin/herdr-relay` forwards exactly `pane.report_agent`,
  `pane.report_agent_session` and `pane.report_metadata`. Everything OVCAQ
  needs passes; `pane.release_agent` does not, so cleanup relies on the
  shell-prompt safety net. `herdr agent list|explain` are also refused in
  the sandbox, so live verification runs from the operator's own pane.
- Repo rules: argv arrays only, no shell; provider-neutral modules stay free
  of provider names (Herdr is not a provider, so `runtime/herdr.py` is fine);
  tests use temporary roots and real sockets, never live `~/.config`.

## Codebase Context

- `src/ovcaq/runtime/supervisor.py`: `run()` (178) owns the run lock and the
  terminal decision; `_loop()` (388) alternates `boundary_decision` and
  `_attempt()`; `apply()` (406) is the one place every `DecisionKind` passes;
  `_attempt()` (472) opens the session and `_stream()` (641) spawns the child
  with `os.environ | dict(spec.env)`. Four call sites cover the whole mapping:
  after `_open_session`, inside `apply`, and the two exits of `run()`.
- `src/ovcaq/runtime/decision.py`: `DecisionKind` is the vocabulary to map;
  `ProgressSnapshot.attention` and `pause_reason` carry the block detail.
- `src/ovcaq/tui/model.py:_status` (180) already folds state, observation and
  metrics into `RunStatus` (`running`, `attention`, `parking`, `halted`,
  `paused`, `completed`, ...). A polling sidecar would reuse it; the in-process
  reporter does not need it because the supervisor sees the transitions.
- `src/ovcaq/supervisor_cli.py:_spawn_supervisor` (356): interactive `run`
  spawns a detached supervisor (`start_new_session=True`) with `**os.environ`,
  so the supervisor inherits the launching pane's `HERDR_PANE_ID` in TUI mode
  as well as in `--no-tui` mode. The pane binding follows the launch pane.
- `src/ovcaq/drivers/claude.py:72` and `drivers/codex.py:190` build driver
  environments from `os.environ`; the scrub belongs in `_stream()` so one
  line covers every driver.
- Herdr's own hook for reference: `~/.claude/hooks/herdr-agent-state.sh`
  (stdlib socket, `settimeout(0.5)`, `seq = time.time_ns()`, ignores all
  errors). Herdr's live pane map is `~/.config/herdr/session.json`; the
  OVCAQ workspace is `w1A` ("📡 ovcaq"), worktree workspaces carry
  `worktree_space.is_linked_worktree = true`.

## Success Criteria

- In a Herdr pane, `ovcaq run --no-tui` shows `ovcaq · working` in the
  sidebar while a session runs, `blocked` with the park or attention reason
  when the loop stops for the operator, and Herdr's done badge after a
  drained batch. Verified from an unsandboxed pane with `herdr agent list`
  and `herdr agent explain <pane>`.
- `~/.config/herdr/session.json` never records a headless `claude -p` or
  Codex session id for the OVCAQ pane after a run.
- The same binary run outside Herdr opens no socket and logs nothing new.
- `./tools/check` passes with the socket fixture tests.

## Risks

- **Detached supervisor versus the shell-prompt safety net.** After `q`
  detaches the TUI, the pane returns to a shell prompt and Herdr clears the
  agent, while the detached supervisor keeps reporting to that pane id. Herdr
  may re-add and re-clear the agent on every report (flapping) or keep the
  later report. Measure before deciding; the fallback is to report only from
  a foreground `--no-tui` supervisor. Ceiling noted in code as a `ponytail:`
  comment.
- **Dead pane ids.** A closed pane returns `not_found`; a moved pane keeps the
  old id as an alias. Both are harmless if errors are ignored.
- **Semantic drift.** Herdr's `working` means "busy, nothing needed from
  the user". Mapping `WAIT` to `working` keeps notifications quiet during
  rate-limit backoff; mapping it to `idle` would raise a false done badge.
  The table above is the proposal; the operator decides the final mapping.
- **Herdr protocol changes.** The raw socket shape is documented and the
  installed hooks rely on it, but Herdr is pre-1.0. Pin the fixture to the
  0.9.5 request shape and keep the reporter at four call sites.

## Open Questions

- Q: What does Herdr show today for an OVCAQ pane in each mode (`--no-tui`,
  TUI attached, TUI detached)? Needs one measured run from an unsandboxed
  pane with `herdr agent explain`. This decides whether the detached case is
  in scope.
- Q: Should the active PRD and phase ride in `message` only, or also in
  metadata tokens for sidebar rows? Default: message only in v1.
- Q: Should the buvis relay also forward `pane.release_agent` so the
  supervisor can release on exit instead of leaning on the shell-prompt
  safety net? Only if Q1 shows stale agents after exit.

## Discovery Log

### Q1: Can a non-built-in tool report its own state to Herdr at all?

**Answer**: Yes, and it is the documented route. Herdr's "add Herdr support"
guide says to call `pane.report_agent` from the agent's own code when
`HERDR_ENV=1`, with an own `source` and `agent` label, `working` on turn
start, `idle` when ready, `blocked` when the user must decide, and that no
pull request or Herdr release is needed. Agents that do this are listed as
"Supported by the agent" with nothing to install.

### Q2: Does the sandbox block it?

**Answer**: No. The relay the launcher points `HERDR_SOCKET_PATH` at forwards
the three report methods, which is exactly the set OVCAQ needs. It blocks
`pane.release_agent` and every read or control method, which only affects
cleanup and live verification.

### Q3: Push from the supervisor or poll from a sidecar?

**Answer**: Push. The supervisor already knows every transition, four call
sites cover the mapping, the pane id is inherited, and there is no new
process or dependency. A sidecar would poll `observe_run` and `_status`,
could report for a run it did not launch, and would be the natural shape once
the operations API (PRD 00064) exists; nothing in the push design blocks that
move later.

### Q4: How does worktree placement matter?

**Answer**: It does not change the design. Herdr maps a pane to a workspace by
id, not by cwd; a worktree workspace is a normal workspace with Git
provenance. A loop launched in a worktree pane inherits that pane's id and
reports there. Only a loop that fans out to other worktrees (PRD 00061) would
need to address panes it does not own, which stays out of scope.
