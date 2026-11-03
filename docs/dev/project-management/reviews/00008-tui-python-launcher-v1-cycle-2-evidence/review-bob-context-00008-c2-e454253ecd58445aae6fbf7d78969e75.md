# PRD (requirements authority; no implementation design)
# OVCAQ TUI and Python launcher

Status: backlog | Version: 1 | Umbrella phase: 6 | Created: 2026-08-23

## Overview

### Source Contract

Implements Phase 6 source tasks `P06-T01`–`P06-T10` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

Tracon observes useful state but parses Claude-native streams and duplicates
process/registry behavior, while Bash owns run/attach job control. OVCAQ needs
one optional provider-neutral TUI and Python launcher using shared runtime models.

### Target User

The operator needs fleet/detail visibility, safe controls, detach/reattach, and
plain fallback without affecting supervisor correctness.

### Success Metrics

- TUI crash or detach leaves the supervisor and owned agent tree alive.
- Pause/stop affect exactly the selected run through public services.
- No duplicate registry, liveness, workflow policy, or provider decoder remains.
- `ovcaq run`/`attach` require no Bash; no-TUI works when Textual fails.
- Unknown/raw-only providers remain visibly degraded rather than fabricated.

## Preconditions and Boundaries

- Depends on completed PRDs 00002–00007.
- The TUI observes shared state, registry, metrics, and normalized observations.
- It does not decide lifecycle transitions or maintain independent liveness.
- Clipboard/platform extras are excluded unless isolated behind a capability
  adapter; correctness never depends on them.

## Functional Decomposition

### Capability: Shared Read Models

#### Feature: Fleet and project discovery

Project fleet/detail views consume the atomic runtime registry and state/session
models, including stale-safe selection and explicit provider identity.

#### Feature: Tolerant live projections

Tail state, normalized events, metrics, and raw fallback with inode/truncation
handling. Missing/corrupt/partial observational data degrades without crashing.

### Capability: Operator Presentation

#### Feature: Workflow and activity panels

Present phase, tasks, review cycles, activity lanes, duration, usage, cost when
known, failure/parking/stopping/halt status, and telemetry capability gaps.

#### Feature: Post-drain capability status

Show pending/running/failed/succeeded/skipped state, failure attention, retained
evidence, and the exact independent retry command.

### Capability: Python Run and Attach

#### Feature: Safe controls

Detach, boundary pause, resume/reattach, confirmed stop, help, and selection call
public runtime/state services for exactly one run; `attach` never starts another
supervisor. The accepted controls remain `q` detach, `p` boundary pause, and
confirmed `s` stop.

#### Feature: TTY and fallback lifecycle

Interactive `ovcaq run` starts the owned background supervisor and attaches by
default. `q` detaches. Non-TTY/`--no-tui` remains foreground. Textual startup or
runtime failure falls back to the plain renderer without killing the supervisor.

## Structural Decomposition

```text
src/ovcaq/
  tui/{__init__.py,app.py,discovery.py,model.py,panels.py}
  events/tail.py
  runtime/{registry.py,supervisor.py}
  cli.py
tests/tui/
tests/runtime/test_attach.py
tests/integration/test_terminal_lifecycle.py
```

- `tui/discovery.py`: thin view over shared registry; no second stale algorithm.
- `tui/model.py`: tolerant projections from shared/provider-neutral models.
- `tui/panels.py`: rendering only.
- `tui/app.py`: navigation and public-service controls.
- `cli.py`: `run` TTY behavior and `attach` selection/fallback.

## Dependency Graph

```text
shared registry/state/events/metrics -> TUI read model -> panels/app
supervisor public controls           -> pause/stop/detach
run ownership + terminal capability -> attach or plain fallback
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Read Models and Views

- [ ] Port tolerant log tailing and state/metrics projections.
- [ ] Port fleet discovery onto the shared registry.
- [ ] Port phase/task/review/activity/usage/capability panels.
- [ ] Rebrand all user strings and XDG theme/config paths.

**Exit Criteria**: Views render shared normalized data and explicit unknowns.

### Phase B: Controls and Attachment

- [ ] Port pause/resume/stop/detach/help through public services.
- [ ] Implement `ovcaq attach` and TTY-default attachment from `ovcaq run`.
- [ ] Ensure exactly one selected run receives control actions.
- [ ] Add Textual-failure and plain/raw-only fallback.

**Exit Criteria**: Detach/TUI failure leaves supervisor alive; controls are scoped.

### Phase C: Terminal Migration Proof

- [ ] Port terminal/process integration scenarios from the Bash suite.
- [ ] Remove duplicate TUI registry/liveness/provider decoding.
- [ ] Prove `run`, `attach`, and no-TUI paths need no Bash launcher.

**Exit Criteria**: Python owns launch/attach job control and Bash is unnecessary.

## Test Strategy

- Fleet discovery with malformed/stale entries and multiple projects.
- Inode rotation, truncation, partial state/event/metric records.
- Known/unknown usage and cost, activity lanes, failure/capability statuses.
- Pause/stop exact targeting, confirmation, detach/reattach.
- TUI startup/crash during a live supervisor; plain fallback.
- TTY versus non-TTY and `--no-tui` lifecycle with real subprocesses.

## Risks

- **Second policy engine**: TUI consumes services and exposes no transitions.
- **UI kills work**: Separate supervisor ownership and integration-test crashes.
- **Provider assumptions**: Render only normalized types and explicit unknowns.
- **Terminal variance**: Capability-detect and preserve headless correctness.

## Acceptance Criteria

- [ ] TUI crash/detach never terminates the supervisor.
- [ ] Pause/stop target one selected run through shared services.
- [ ] Fleet/detail/activity/capability views tolerate incomplete evidence.
- [ ] No duplicate liveness, registry, workflow, or provider parser exists.
- [ ] `ovcaq run`, `attach`, and no-TUI operation require no Bash.
- [ ] PRD 00009 can add Codex without changing TUI policy.

## Unresolved Questions

None.


## Architecture
# AGENTS.md — OVCAQ

OVCAQ means **Orchestration, Visibility, and Control for Agent Queues**. It is
an installable Python CLI/TUI that supervises a PRD-driven workflow through
Claude Code, Codex, or another headless coding agent.

The global `AGENTS.md` remains in force. This file adds project-specific rules.

## Current state

The repository is in planning/bootstrap. Until an implementation PRD replaces
it, `docs/dev/project-management/plans/implementation-plan.md` is the architecture and sequencing
authority. Do not create production modules opportunistically outside that
sequence.

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

Planned verification commands once the scaffold lands:

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/ovcaq
uv build
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


## Product diff scope
The full gathered diff retains all workflow/log records. For review use the complete product diff at /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/review-product-diff-00008-c2-e454253ecd58445aae6fbf7d78969e75.diff. All changed production/test/configuration/operator-doc paths follow:
CHANGELOG.md
docs/operations.md
src/ovcaq/cli.py
src/ovcaq/events/tail.py
src/ovcaq/runtime/_run_observation.py
src/ovcaq/runtime/registry.py
src/ovcaq/runtime/session.py
src/ovcaq/runtime/supervisor.py
src/ovcaq/state/commands.py
src/ovcaq/supervisor_cli.py
src/ovcaq/tui/app.py
src/ovcaq/tui/discovery.py
src/ovcaq/tui/model.py
src/ovcaq/tui/panels.py
tests/integration/test_control_commit_identity.py
tests/integration/test_guarded_run_mutation.py
tests/integration/test_launcher_outcomes.py
tests/integration/test_native_telemetry_identity.py
tests/integration/test_observer_terminal_cleanup.py
tests/integration/test_observer_terminal_viewers.py
tests/integration/test_supervisor_live_telemetry.py
tests/integration/test_terminal_lifecycle.py
tests/integration/test_viewer_fallback.py
tests/integration/viewer_fallback_support.py
tests/packaging/packaging_support.py
tests/runtime/test_attach.py
tests/runtime/test_session_metrics.py
tests/runtime/test_supervisor_cli.py
tests/state/test_cli.py
tests/state/test_commands.py
tests/state/test_guarded_service.py
tests/tui/model_support.py
tests/tui/test_app.py
tests/tui/test_app_ended_selection.py
tests/tui/test_app_poll_responsiveness.py
tests/tui/test_model.py
tests/tui/test_model_elapsed_duration.py
tests/tui/test_model_live_evidence.py
tests/tui/test_theme_persistence.py

## Mechanical facts (computed, do not re-count)

Function line counts from `ast`. Cite these for countable claims; a
finding that contradicts this block is discarded at the review gate.

- `CHANGELOG.md` — skipped (non-python)
- `docs/operations.md` — skipped (non-python)
- `src/ovcaq/cli.py`
  - `_ArgumentParser.__init__` — line 69, 3 lines
  - `_ArgumentParser.error` — line 73, 3 lines
  - `_add_expected_revision` — line 78, 2 lines
  - `_add_generic_mutation_options` — line 82, 3 lines
  - `_add_generic_state_commands` — line 87, 16 lines
  - `_add_task_commands` — line 105, 35 lines
  - `_add_contract_and_restore_commands` — line 142, 12 lines
  - `build_parser` — line 156, 34 lines
  - `_add_supervisor_commands` — line 192, 18 lines
  - `_leaf_command_parsers` — line 212, 18 lines
  - `command_inventory` — line 232, 16 lines
  - `render_state_protocol_command_inventory` — line 250, 13 lines
  - `render_command_reference` — line 265, 43 lines
  - `_path_operation` — line 310, 14 lines
  - `_dispatch_init_or_read` — line 329, 23 lines
  - `_dispatch_generic_mutation` — line 354, 39 lines
  - `_dispatch_attempt_command` — line 395, 16 lines
  - `_dispatch_task_or_contract` — line 413, 49 lines
  - `_dispatch` — line 464, 21 lines
  - `_attach_view` — line 487, 11 lines
  - `_launch_and_attach` — line 500, 17 lines
  - `_resume_and_attach` — line 519, 26 lines
  - `_dispatch_interactive` — line 547, 14 lines
  - `_normalize_error` — line 563, 26 lines
  - `_write_json` — line 591, 2 lines
  - `_emit_failure` — line 595, 16 lines
  - `_emit_workflow` — line 613, 23 lines
  - `main` — line 638, 32 lines
  - `_emit_result` — line 672, 24 lines
- `src/ovcaq/events/tail.py`
  - `NormalizedEventWriter.__init__` — line 30, 4 lines
  - `NormalizedEventWriter.write` — line 35, 5 lines
  - `NormalizedEventWriter.flush` — line 41, 2 lines
  - `NormalizedEventWriter.close` — line 44, 2 lines
  - `RawFirstDecoder.__init__` — line 51, 21 lines
  - `RawFirstDecoder.feed` — line 73, 24 lines
  - `RawFirstDecoder.finish` — line 98, 3 lines
  - `RawFirstDecoder._complete` — line 102, 49 lines
  - `RawFirstDecoder._preview` — line 152, 14 lines
  - `JsonlFollower.__init__` — line 186, 23 lines
  - `JsonlFollower.close` — line 210, 4 lines
  - `JsonlFollower.read` — line 215, 35 lines
  - `JsonlFollower._reset_if_changed` — line 251, 20 lines
  - `JsonlFollower._open` — line 272, 14 lines
  - `JsonlFollower._consume` — line 287, 25 lines
  - `JsonlFollower._decode` — line 313, 9 lines
- `src/ovcaq/runtime/_run_observation.py`
  - `_state_digest` — line 45, 3 lines
  - `publish_terminal_evidence` — line 50, 21 lines
  - `_verify_terminal_state` — line 73, 27 lines
  - `_selected_state` — line 102, 24 lines
  - `observe_selected_run` — line 129, 19 lines
  - `observe_run` — line 150, 47 lines
- `src/ovcaq/runtime/registry.py`
  - `observe_unowned_run` — line 27, 18 lines
  - `run_lock_held` — line 47, 25 lines
  - `RunLock.__init__` — line 77, 2 lines
  - `RunLock.acquire` — line 81, 22 lines
  - `RunLock.close` — line 104, 8 lines
  - `RunLock.__enter__` — line 113, 2 lines
  - `RunLock.__exit__` — line 116, 2 lines
  - `process_identity` — line 126, 16 lines
  - `process_matches` — line 144, 2 lines
  - `FleetRun.from_entry` — line 169, 9 lines
  - `_validate_run_id` — line 187, 3 lines
  - `_decode_entry` — line 192, 23 lines
  - `_read_entry` — line 217, 16 lines
  - `FleetRegistry.__init__` — line 238, 4 lines
  - `FleetRegistry._verify_root` — line 243, 16 lines
  - `FleetRegistry._directory` — line 261, 19 lines
  - `FleetRegistry._mutation` — line 282, 26 lines
  - `FleetRegistry.guard_mutation` — line 310, 26 lines
  - `FleetRegistry.guard_mutation.guard` — line 325, 8 lines
  - `FleetRegistry.publish` — line 337, 37 lines
  - `FleetRegistry._scan` — line 375, 27 lines
  - `FleetRegistry.snapshot` — line 403, 5 lines
  - `FleetRegistry.remove` — line 409, 18 lines
  - `FleetRegistry.prune` — line 428, 31 lines
- `src/ovcaq/runtime/session.py`
  - `_validate_metric_completion_and_usage` — line 95, 42 lines
  - `_metric_payload` — line 139, 45 lines
  - `metric_from_record` — line 186, 9 lines
  - `_read_metric` — line 197, 7 lines
  - `publish_session_metric` — line 206, 17 lines
  - `reconcile_metrics` — line 225, 20 lines
  - `observe_metrics` — line 254, 35 lines
  - `observe_session_evidence` — line 299, 23 lines
  - `observe_emergency_failure` — line 332, 12 lines
  - `_validate_identifier` — line 357, 8 lines
  - `_metadata_payload` — line 367, 11 lines
  - `parse_session_metadata` — line 380, 9 lines
  - `create_session` — line 391, 34 lines
  - `publish_run_metadata` — line 427, 5 lines
  - `cleanup_run_records` — line 434, 49 lines
  - `publish_session_summary` — line 485, 45 lines
  - `_emergency_fields` — line 532, 7 lines
  - `_read_emergency` — line 541, 37 lines
  - `record_state_failure` — line 580, 37 lines
  - `require_no_emergency_failure` — line 619, 8 lines
  - `_archive_emergency_evidence` — line 629, 27 lines
  - `acknowledge_emergency_failure` — line 658, 46 lines
  - `inventory_evidence` — line 737, 7 lines
  - `plan_purge` — line 746, 11 lines
  - `apply_purge` — line 759, 5 lines
- `src/ovcaq/runtime/supervisor.py`
  - `Clock.now` — line 91, 1 lines
  - `CapabilityRunnerResolver.__call__` — line 95, 1 lines
  - `_timestamp` — line 105, 2 lines
  - `Supervisor.__init__` — line 110, 25 lines
  - `Supervisor.run` — line 136, 49 lines
  - `Supervisor._state_failure` — line 186, 19 lines
  - `Supervisor._state_failure.write_notice` — line 189, 10 lines
  - `Supervisor._state_failure.write_notice.mutate` — line 190, 7 lines
  - `Supervisor._record_stop` — line 206, 14 lines
  - `Supervisor._record_stop.mutate` — line 207, 8 lines
  - `Supervisor._publish_ownership` — line 221, 28 lines
  - `Supervisor._loop` — line 250, 12 lines
  - `Supervisor.run_once` — line 263, 4 lines
  - `Supervisor.apply` — line 268, 29 lines
  - `Supervisor._archive` — line 298, 7 lines
  - `Supervisor._capability_service` — line 306, 8 lines
  - `Supervisor._reconcile_capabilities` — line 315, 7 lines
  - `Supervisor._run_capability` — line 323, 9 lines
  - `Supervisor._attempt` — line 334, 48 lines
  - `Supervisor._open_session` — line 383, 46 lines
  - `Supervisor._collect` — line 430, 49 lines
  - `Supervisor._record_timeout` — line 480, 17 lines
  - `Supervisor._stream` — line 498, 34 lines
  - `Supervisor._publish_summary` — line 533, 24 lines
  - `Supervisor._conclude` — line 558, 48 lines
  - `Supervisor._decide` — line 607, 33 lines
- `src/ovcaq/state/commands.py`
  - `_require_task_id` — line 72, 4 lines
  - `_preflight_task_create_ids` — line 78, 7 lines
  - `_task_by_id` — line 87, 6 lines
  - `_refresh_task_counts` — line 95, 5 lines
  - `_result` — line 102, 2 lines
  - `_require_recovery_idle` — line 106, 6 lines
  - `_capability_by_name` — line 114, 5 lines
  - `_require_detail` — line 121, 4 lines
  - `_generic_path` — line 127, 8 lines
  - `StateService.__init__` — line 138, 9 lines
  - `StateService.show` — line 148, 2 lines
  - `StateService.validate` — line 151, 2 lines
  - `StateService.get` — line 154, 3 lines
  - `StateService._transaction` — line 158, 15 lines
  - `StateService._transaction.guarded` — line 164, 3 lines
  - `StateService.add_task` — line 174, 47 lines
  - `StateService.add_task.mutate` — line 183, 35 lines
  - `StateService.start_task` — line 222, 17 lines
  - `StateService.start_task.mutate` — line 230, 3 lines
  - `StateService.append_attempt` — line 240, 22 lines
  - `StateService.append_attempt.mutate` — line 249, 7 lines
  - `StateService.complete_task` — line 263, 23 lines
  - `StateService.complete_task.mutate` — line 272, 8 lines
  - `StateService.set_task_body` — line 287, 18 lines
  - `StateService.set_task_body.mutate` — line 296, 3 lines
  - `StateService.set_task_meta` — line 306, 31 lines
  - `StateService.set_task_meta.mutate` — line 315, 16 lines
  - `StateService.set_task_status` — line 338, 21 lines
  - `StateService.set_task_status.mutate` — line 347, 6 lines
  - `StateService.clear_tasks` — line 360, 15 lines
  - `StateService.clear_tasks.mutate` — line 365, 4 lines
  - `StateService.set_contract_card` — line 376, 14 lines
  - `StateService.set_contract_card.mutate` — line 382, 2 lines
  - `StateService.set` — line 391, 18 lines
  - `StateService.set.mutate` — line 402, 2 lines
  - `StateService.append` — line 410, 18 lines
  - `StateService.append.mutate` — line 421, 2 lines
  - `StateService.delete` — line 429, 16 lines
  - `StateService.delete.mutate` — line 438, 2 lines
  - `StateService.request_pause` — line 446, 13 lines
  - `StateService.request_pause.mutate` — line 454, 3 lines
  - `StateService.resume` — line 460, 7 lines
  - `StateService.resume.mutate` — line 461, 4 lines
  - `StateService.record_progress` — line 468, 19 lines
  - `StateService.record_progress.mutate` — line 482, 3 lines
  - `StateService.start_batch` — line 488, 13 lines
  - `StateService.start_batch.mutate` — line 493, 6 lines
  - `StateService.complete_batch` — line 502, 16 lines
  - `StateService.complete_batch.mutate` — line 507, 9 lines
  - `StateService.start_capability` — line 519, 8 lines
  - `StateService.retry_capability` — line 528, 8 lines
  - `StateService._begin_capability` — line 537, 28 lines
  - `StateService._begin_capability.mutate` — line 550, 13 lines
  - `StateService.finish_capability` — line 566, 49 lines
  - `StateService.finish_capability.mutate` — line 579, 34 lines
  - `StateService.reconcile_capability` — line 616, 17 lines
  - `StateService.skip_empty_drain_capabilities` — line 634, 20 lines
  - `StateService.skip_empty_drain_capabilities.mutate` — line 640, 12 lines
  - `StateService.restore` — line 655, 10 lines
- `src/ovcaq/supervisor_cli.py`
  - `_now` — line 59, 2 lines
  - `_Clock.now` — line 64, 2 lines
  - `_UnavailableRunner.run` — line 69, 5 lines
  - `_bounded` — line 76, 6 lines
  - `_open_report` — line 84, 7 lines
  - `_claim_launch_report` — line 93, 21 lines
  - `_write_launch_report` — line 116, 17 lines
  - `_verify_inherited_report` — line 135, 7 lines
  - `_report_runtime_error` — line 144, 5 lines
  - `_run` — line 151, 48 lines
  - `operator_notice` — line 201, 8 lines
  - `verify_run` — line 211, 23 lines
  - `LaunchError.__init__` — line 251, 3 lines
  - `_read_launch_report` — line 256, 8 lines
  - `completed_run` — line 266, 9 lines
  - `_completed_launch` — line 277, 14 lines
  - `_launch_failure` — line 293, 14 lines
  - `_published_run` — line 309, 40 lines
  - `_spawn_supervisor` — line 351, 21 lines
  - `launch_supervisor` — line 374, 38 lines
  - `stop_supervisor` — line 414, 7 lines
  - `_stop` — line 423, 21 lines
  - `_retry` — line 446, 22 lines
  - `dispatch_supervisor` — line 470, 20 lines
- `src/ovcaq/tui/app.py`
  - `_fleet_row` — line 38, 4 lines
  - `_fleet_status` — line 44, 6 lines
  - `_frame` — line 52, 5 lines
  - `ControlService.pause` — line 60, 3 lines
  - `ControlService.resume` — line 63, 1 lines
  - `ControlService.stop` — line 64, 1 lines
  - `StaleSelectionError.__init__` — line 68, 3 lines
  - `RunControlService.__init__` — line 76, 2 lines
  - `RunControlService.pause` — line 79, 10 lines
  - `RunControlService.resume` — line 90, 4 lines
  - `RunControlService.stop` — line 95, 2 lines
  - `RunControlService._mutate` — line 98, 17 lines
  - `RunControlService._mutate.validate` — line 99, 5 lines
  - `_terminal_result` — line 123, 8 lines
  - `_config_root` — line 145, 4 lines
  - `theme_path` — line 151, 2 lines
  - `_theme_directory` — line 156, 21 lines
  - `load_theme` — line 179, 22 lines
  - `save_theme` — line 203, 46 lines
  - `FleetApp.__init__` — line 272, 4 lines
  - `FleetApp.on_mount` — line 277, 6 lines
  - `FleetApp.watch_theme` — line 284, 5 lines
  - `FleetApp.compose` — line 290, 4 lines
  - `FleetApp.on_option_list_option_selected` — line 295, 4 lines
  - `FleetApp.action_detach` — line 300, 2 lines
  - `_ConfirmStop.__init__` — line 310, 3 lines
  - `_ConfirmStop.compose` — line 314, 2 lines
  - `_ConfirmStop.action_answer` — line 317, 2 lines
  - `ProjectApp.__init__` — line 328, 16 lines
  - `ProjectApp.compose` — line 345, 6 lines
  - `ProjectApp.on_mount` — line 352, 8 lines
  - `ProjectApp.watch_theme` — line 361, 5 lines
  - `ProjectApp._poll` — line 367, 22 lines
  - `ProjectApp.on_unmount` — line 390, 4 lines
  - `ProjectApp._notify_error` — line 395, 2 lines
  - `ProjectApp._control` — line 398, 7 lines
  - `ProjectApp.action_detach` — line 406, 2 lines
  - `ProjectApp.action_toggle_help` — line 409, 3 lines
  - `ProjectApp.action_toggle_pause` — line 413, 10 lines
  - `ProjectApp.action_stop` — line 424, 11 lines
  - `ProjectApp.action_stop.answered` — line 430, 3 lines
  - `run_plain` — line 437, 34 lines
  - `run_plain_fleet` — line 473, 20 lines
  - `_fallback_notice` — line 495, 6 lines
  - `_capture_terminal` — line 503, 5 lines
  - `_restore_terminal` — line 510, 7 lines
  - `_interactive` — line 519, 2 lines
  - `_choose_run` — line 523, 17 lines
  - `attach` — line 542, 36 lines
- `src/ovcaq/tui/discovery.py`
  - `discover_fleet` — line 22, 11 lines
  - `select_run` — line 35, 14 lines
- `src/ovcaq/tui/model.py`
  - `display_text` — line 127, 8 lines
  - `_guard` — line 137, 8 lines
  - `_payload_text` — line 147, 6 lines
  - `_emergency_current` — line 155, 14 lines
  - `_status` — line 171, 48 lines
  - `_usage_view` — line 221, 25 lines
  - `_usage_view.total` — line 227, 3 lines
  - `_capabilities` — line 248, 25 lines
  - `_bounded_gaps` — line 275, 5 lines
  - `ProjectObserver.__init__` — line 285, 16 lines
  - `ProjectObserver._clear` — line 302, 6 lines
  - `ProjectObserver.close` — line 309, 2 lines
  - `ProjectObserver.poll` — line 312, 43 lines
  - `ProjectObserver._duration` — line 356, 22 lines
  - `ProjectObserver._project` — line 379, 41 lines
  - `ProjectObserver._telemetry` — line 421, 10 lines
  - `ProjectObserver._observe` — line 432, 30 lines
  - `ProjectObserver._evidence` — line 463, 44 lines
  - `ProjectObserver._apply` — line 508, 45 lines
  - `ProjectObserver._observe_lane` — line 554, 32 lines
- `src/ovcaq/tui/panels.py`
  - `_known` — line 18, 2 lines
  - `_panel` — line 22, 6 lines
  - `_usage` — line 30, 14 lines
  - `fleet_table` — line 46, 11 lines
  - `workflow_panel` — line 59, 16 lines
  - `tasks_panel` — line 77, 3 lines
  - `review_panel` — line 82, 2 lines
  - `activity_panel` — line 86, 7 lines
  - `capability_panel` — line 95, 20 lines
  - `plain_frame` — line 117, 17 lines
- `tests/integration/test_control_commit_identity.py`
  - `_child` — line 79, 18 lines
  - `_line` — line 99, 13 lines
  - `_send` — line 114, 4 lines
  - `_bytes` — line 120, 3 lines
  - `_owner` — line 142, 37 lines
  - `fleet` — line 182, 18 lines
  - `_hook` — line 202, 9 lines
  - `_hook.initialize` — line 207, 2 lines
  - `_assert_other` — line 213, 7 lines
  - `_assert_only_control` — line 222, 15 lines
  - `test_control_commit_pause_resume_targets_only_selected_identity` — line 240, 29 lines
  - `test_control_commit_owner_exit_rolls_back_before_replacement_reads` — line 276, 44 lines
  - `test_control_commit_owner_exit_rolls_back_before_replacement_reads.invalidate` — line 293, 11 lines
  - `test_control_commit_last_boundary_identity_replacement_rolls_back` — line 323, 30 lines
  - `test_control_commit_last_boundary_identity_replacement_rolls_back.invalidate` — line 337, 6 lines
  - `_terminal_boundaries` — line 355, 19 lines
  - `_terminal_boundaries.attach` — line 363, 3 lines
  - `_terminal_boundaries.launch` — line 367, 3 lines
  - `test_control_commit_interactive_resume_preserves_exact_live_selection` — line 377, 42 lines
  - `test_control_commit_interactive_resume_preserves_exact_live_selection.invalidate` — line 393, 6 lines
  - `test_injected_registry_stop_signals_only_exact_selected_owner` — line 423, 33 lines
  - `test_injected_registry_stop_signals_only_exact_selected_owner.signal_boundary` — line 435, 5 lines
  - `test_injected_registry_stop_signals_only_exact_selected_owner.stop` — line 441, 4 lines
  - `test_shared_run_conversion_and_discovery_preserve_distinct_entries` — line 458, 21 lines
  - `test_shared_run_conversion_copies_independent_identity_fields` — line 483, 28 lines
  - `_capture_signals` — line 513, 12 lines
  - `_capture_signals.signal_boundary` — line 517, 5 lines
  - `_release_lock` — line 527, 6 lines
  - `test_control_commit_rejects_missing_ownership_proof_with_live_process` — line 536, 35 lines
  - `test_injected_registry_stop_requires_all_proof_for_live_process` — line 578, 34 lines
- `tests/integration/test_guarded_run_mutation.py`
  - `child` — line 64, 18 lines
  - `line` — line 84, 13 lines
  - `send` — line 99, 4 lines
  - `entry_for` — line 105, 12 lines
  - `validate_owner` — line 119, 4 lines
  - `assert_blocked` — line 125, 5 lines
  - `exit_owner` — line 132, 4 lines
  - `assert_replacement` — line 138, 4 lines
  - `test_owner_exit_during_publication_rolls_back_before_replacement_reads` — line 146, 49 lines
  - `test_owner_exit_during_publication_rolls_back_before_replacement_reads.invalidate` — line 167, 7 lines
  - `test_live_selected_owner_commits_control_once` — line 198, 23 lines
  - `test_ownership_mutation_waits_and_is_released_on_context_exit` — line 225, 35 lines
  - `test_stale_selection_cannot_change_replacement_state` — line 263, 38 lines
  - `test_guard_rejects_symlinked_registry_lock_without_touching_target` — line 303, 26 lines
  - `test_guard_rejects_replaced_lock_at_last_boundary_and_rolls_back` — line 331, 36 lines
  - `test_guard_rejects_replaced_lock_at_last_boundary_and_rolls_back.substitute` — line 345, 5 lines
- `tests/integration/test_launcher_outcomes.py`
  - `isolated_environment` — line 40, 9 lines
  - `project` — line 51, 25 lines
  - `service` — line 78, 2 lines
  - `finish` — line 82, 10 lines
  - `line` — line 94, 13 lines
  - `SpawnBoundary.spawn` — line 122, 22 lines
  - `boundary` — line 147, 8 lines
  - `assert_drained` — line 157, 6 lines
  - `test_real_empty_child_commits_completion_before_parent_first_poll` — line 165, 23 lines
  - `test_interactive_quick_completion_returns_zero_without_live_attachment` — line 191, 19 lines
  - `test_interactive_quick_completion_returns_zero_without_live_attachment.unexpected_attachment` — line 203, 2 lines
  - `test_configured_layout_drains_without_creating_unused_default_tree` — line 213, 15 lines
  - `test_exit_without_exact_child_commit_proof_is_failure` — line 232, 18 lines
  - `test_child_completion_report_cannot_complete_a_replacement_batch` — line 252, 21 lines
  - `test_child_completion_report_cannot_complete_a_replacement_batch.replace_completed_batch` — line 258, 5 lines
  - `assert_private_diagnostic` — line 275, 20 lines
  - `test_child_configuration_failure_preserves_actionable_private_report` — line 297, 15 lines
  - `test_early_layout_failure_preserves_diagnostic_and_collision` — line 315, 28 lines
  - `test_early_layout_failure_preserves_diagnostic_and_collision.collide` — line 325, 7 lines
  - `test_child_rejects_unsafe_report_destination_without_overwriting_it` — line 348, 25 lines
  - `test_report_environment_is_consumed_on_driver_construction_failure` — line 375, 12 lines
  - `test_reflected_hostile_agent_preserves_bounded_private_diagnostics` — line 389, 28 lines
  - `release` — line 458, 6 lines
  - `test_live_handshake_returns_exact_published_child_identity` — line 467, 22 lines
  - `delay_publication` — line 491, 6 lines
  - `test_live_handshake_waits_for_publication_within_configured_deadline` — line 499, 33 lines
  - `test_live_handshake_waits_for_publication_within_configured_deadline.release_after_first_poll` — line 506, 14 lines
  - `test_live_handshake_waits_for_publication_within_configured_deadline.release_after_first_poll.polled` — line 509, 9 lines
  - `test_unpublished_child_fails_within_configured_deadline` — line 534, 16 lines
  - `test_attachment_cleanup_race_requires_exact_successful_terminal_evidence` — line 555, 36 lines
  - `test_attachment_cleanup_race_requires_exact_successful_terminal_evidence.raced_attach` — line 570, 9 lines
  - `duplicate_startup` — line 594, 17 lines
  - `duplicate_startup.assert_starting` — line 595, 2 lines
  - `test_duplicate_owner_guides_attach_without_signaling_healthy_owner` — line 613, 48 lines
  - `test_duplicate_owner_guides_attach_without_signaling_healthy_owner.record_signal` — line 633, 3 lines
  - `test_duplicate_owner_guides_attach_without_signaling_healthy_owner.record_group` — line 637, 3 lines
- `tests/integration/test_native_telemetry_identity.py`
  - `Clock.now` — line 35, 2 lines
  - `Clock.monotonic` — line 38, 2 lines
  - `Clock.wait` — line 41, 2 lines
  - `native_usage` — line 55, 7 lines
  - `native_lifecycle_rows` — line 64, 30 lines
  - `native_activity_row` — line 96, 19 lines
  - `native_result_row` — line 117, 10 lines
  - `native_session_payload` — line 129, 11 lines
  - `child_code` — line 142, 10 lines
  - `LiveClaudeDriver.__init__` — line 163, 15 lines
  - `LiveClaudeDriver.build_launch` — line 179, 12 lines
  - `LiveClaudeDriver.decode` — line 192, 8 lines
  - `LiveClaudeDriver.capture` — line 201, 47 lines
  - `LiveClaudeDriver.summarize` — line 249, 7 lines
  - `LiveClaudeDriver.advance` — line 257, 15 lines
  - `live_settings` — line 274, 32 lines
  - `run_live_claude` — line 308, 21 lines
  - `test_real_claude_telemetry_binds_native_ids_to_owning_supervisor_sessions` — line 331, 34 lines
  - `test_evidence_presence_distinguishes_empty_normalized_from_raw_only_content` — line 378, 19 lines
- `tests/integration/test_observer_terminal_cleanup.py`
  - `Clock.now` — line 53, 2 lines
  - `Clock.monotonic` — line 56, 2 lines
  - `Clock.wait` — line 59, 2 lines
  - `BoundedObserver.poll` — line 68, 5 lines
  - `settings_for` — line 75, 16 lines
  - `seed` — line 93, 49 lines
  - `update_tasks` — line 144, 5 lines
  - `Driver.default_prompt` — line 162, 2 lines
  - `Driver.build_launch` — line 165, 20 lines
  - `Driver.decode` — line 186, 29 lines
  - `Driver.summarize` — line 216, 12 lines
  - `Driver.finish` — line 229, 38 lines
  - `FailedCapability.run` — line 270, 7 lines
  - `worker` — line 279, 23 lines
  - `Selected.finish` — line 313, 12 lines
  - `wait_ready` — line 327, 10 lines
  - `prepare` — line 339, 25 lines
  - `launch_worker` — line 366, 17 lines
  - `selected_run` — line 386, 46 lines
  - `isolated_config` — line 435, 4 lines
  - `assert_committed` — line 441, 13 lines
  - `assert_final_telemetry` — line 456, 31 lines
  - `test_final_commit_survives_supervisor_cleanup_between_polls` — line 491, 31 lines
  - `test_failed_capability_retains_retry_and_session_evidence_after_exit` — line 524, 31 lines
  - `test_replacement_never_becomes_the_ended_selection` — line 559, 37 lines
  - `ReplacementDuringRead.publish` — line 610, 11 lines
  - `ReplacementDuringRead.open` — line 622, 16 lines
  - `ReplacementDuringRead.await_replacement` — line 639, 11 lines
  - `ReplacementDuringRead.close` — line 651, 7 lines
  - `assert_selected_race_evidence` — line 660, 28 lines
  - `test_replacement_starting_during_final_observation_cannot_supply_selected_data` — line 690, 28 lines
  - `test_unavailable_final_state_is_visible_and_cannot_claim_completion` — line 721, 28 lines
- `tests/integration/test_observer_terminal_viewers.py`
  - `assert_frame_values` — line 29, 7 lines
  - `test_plain_renders_final_selected_frame_and_returns_without_further_polls` — line 39, 21 lines
  - `test_textual_returns_terminal_result_after_real_supervisor_exit` — line 63, 36 lines
  - `test_textual_returns_terminal_result_after_real_supervisor_exit.exercise` — line 76, 21 lines
  - `test_live_pause_or_attention_does_not_end_textual_selection` — line 102, 36 lines
  - `test_live_pause_or_attention_does_not_end_textual_selection.change` — line 108, 9 lines
  - `test_live_pause_or_attention_does_not_end_textual_selection.exercise` — line 129, 5 lines
  - `set_live_status` — line 140, 9 lines
  - `test_plain_keeps_live_pause_or_attention_until_the_selected_run_ends` — line 152, 26 lines
  - `test_plain_keeps_live_pause_or_attention_until_the_selected_run_ends.release` — line 161, 4 lines
- `tests/integration/test_supervisor_live_telemetry.py`
  - `Clock.now` — line 30, 2 lines
  - `Clock.monotonic` — line 33, 2 lines
  - `Clock.wait` — line 36, 2 lines
  - `LiveDriver.default_prompt` — line 56, 2 lines
  - `LiveDriver.build_launch` — line 59, 24 lines
  - `LiveDriver.decode` — line 84, 32 lines
  - `LiveDriver.capture` — line 117, 28 lines
  - `LiveDriver.summarize` — line 146, 14 lines
  - `LiveDriver.advance` — line 161, 15 lines
  - `live_settings` — line 178, 33 lines
  - `run_live` — line 213, 25 lines
  - `assert_child_receipts` — line 240, 8 lines
  - `assert_session_identities` — line 250, 16 lines
  - `test_real_supervisor_streams_live_cumulative_usage_and_follows_session_rollover` — line 268, 27 lines
  - `test_real_supervisor_preserves_raw_bytes_when_precreated_normalization_is_empty` — line 297, 17 lines
- `tests/integration/test_terminal_lifecycle.py`
  - `wait_until` — line 95, 9 lines
  - `ps_field` — line 106, 9 lines
  - `gone` — line 117, 3 lines
  - `invocations` — line 122, 5 lines
  - `pause_requested` — line 129, 8 lines
  - `Term.pump` — line 146, 4 lines
  - `Term.wait_for` — line 151, 10 lines
  - `Term.expect` — line 162, 2 lines
  - `Term.send` — line 165, 2 lines
  - `Term.exit_code` — line 168, 4 lines
  - `Term.send_until_exit` — line 173, 8 lines
  - `Term.is_cooked` — line 182, 2 lines
  - `Term.close` — line 185, 8 lines
  - `World.__init__` — line 198, 25 lines
  - `World.project` — line 224, 35 lines
  - `World.project.seed` — line 253, 3 lines
  - `World.ovcaq` — line 260, 2 lines
  - `World.spawn` — line 263, 2 lines
  - `World.spawn_argv` — line 266, 17 lines
  - `World.pipe` — line 284, 14 lines
  - `World.live` — line 299, 5 lines
  - `World.wait_live` — line 305, 9 lines
  - `World.wait_live.ready` — line 308, 3 lines
  - `World.launcher_calls` — line 315, 2 lines
  - `World.close` — line 318, 20 lines
  - `World._reap` — line 340, 9 lines
  - `world` — line 352, 7 lines
  - `running` — line 361, 9 lines
  - `detach` — line 372, 5 lines
  - `assert_survives` — line 379, 4 lines
  - `test_interactive_run_detach_key_leaves_the_supervisor_alive` — line 386, 7 lines
  - `test_run_omits_agent_from_the_supervisor_argv_unless_requested` — line 396, 11 lines
  - `test_detached_supervisor_can_be_reattached_repeatedly` — line 409, 8 lines
  - `test_attach_without_root_displays_fleet_selection_in_the_terminal` — line 419, 10 lines
  - `test_plain_fleet_selection_lists_runs_and_detaches_on_eof` — line 431, 9 lines
  - `test_attach_never_launches_a_supervisor` — line 442, 7 lines
  - `test_json_attach_is_rejected_without_viewer_or_launch` — line 451, 7 lines
  - `test_p_requests_a_boundary_pause_and_the_run_stops_at_the_boundary` — line 460, 13 lines
  - `test_resume_reattaches_the_same_live_run` — line 475, 11 lines
  - `test_resume_after_boundary_pause_launches_once_and_attaches_the_new_run` — line 488, 17 lines
  - `test_cancelled_stop_leaves_the_run_alive` — line 507, 10 lines
  - `test_confirmed_stop_targets_exactly_the_selected_run` — line 519, 15 lines
  - `test_textual_failure_restores_the_terminal_and_falls_back_to_plain` — line 536, 16 lines
  - `test_noninteractive_runs_supervise_in_the_foreground_process` — line 564, 25 lines
  - `test_no_bash_launcher_is_invoked_or_required` — line 591, 9 lines
- `tests/integration/test_viewer_fallback.py`
  - `Controls.__init__` — line 41, 2 lines
  - `Controls.pause` — line 44, 4 lines
  - `Controls.resume` — line 49, 2 lines
  - `Controls.stop` — line 52, 3 lines
  - `Terminal.isatty` — line 58, 2 lines
  - `Registry.__init__` — line 63, 2 lines
  - `Registry.snapshot` — line 66, 11 lines
  - `Observer.__init__` — line 80, 4 lines
  - `Observer.poll` — line 85, 3 lines
  - `Observer.close` — line 89, 2 lines
  - `view` — line 93, 22 lines
  - `identities_alive` — line 117, 5 lines
  - `Helper.__init__` — line 125, 4 lines
  - `start_helper` — line 131, 16 lines
  - `wait_helper_ready` — line 149, 6 lines
  - `finish_helper` — line 157, 7 lines
  - `cleanup_helper` — line 166, 13 lines
  - `test_pipe_eof_detaches_live_plain_viewer_and_preserves_processes` — line 181, 15 lines
  - `test_pty_ctrl_d_detaches_live_plain_viewer_and_preserves_processes` — line 198, 21 lines
  - `test_open_stdin_does_not_block_observation_of_completion` — line 221, 15 lines
  - `test_isolated_textual_import_failure_falls_back_and_preserves_processes` — line 239, 17 lines
  - `PollProbe.__init__` — line 259, 10 lines
  - `PollProbe.poll` — line 270, 15 lines
  - `PollProbe.close` — line 286, 6 lines
  - `failing_app_type` — line 294, 27 lines
  - `failing_app_type.FailingApp.__init__` — line 298, 5 lines
  - `failing_app_type.FailingApp.run` — line 304, 15 lines
  - `failing_app_type.FailingApp.run.crash` — line 308, 9 lines
  - `assert_project_failure` — line 323, 25 lines
  - `exercise_project_failure` — line 350, 45 lines
  - `exercise_project_failure.plain` — line 363, 7 lines
  - `test_ordinary_project_ui_failure_restores_pty_and_reuses_observer` — line 398, 5 lines
  - `test_ui_process_control_exceptions_do_not_enter_plain_fallback` — line 407, 28 lines
  - `test_ordinary_fleet_ui_failure_uses_one_bounded_selection` — line 437, 50 lines
  - `test_ordinary_fleet_ui_failure_uses_one_bounded_selection.CompletingApp.__init__` — line 448, 5 lines
  - `test_ordinary_fleet_ui_failure_uses_one_bounded_selection.CompletingApp.run` — line 454, 5 lines
  - `test_plain_prints_only_distinct_frames_and_always_prints_terminal_frame` — line 489, 27 lines
- `tests/integration/viewer_fallback_support.py`
  - `TextualFailure.__init__` — line 21, 2 lines
  - `TextualFailure.find_spec` — line 24, 9 lines
  - `TtyStream.__init__` — line 38, 2 lines
  - `TtyStream.fileno` — line 41, 2 lines
  - `TtyStream.isatty` — line 44, 2 lines
  - `TtyStream.readline` — line 47, 2 lines
  - `TtyStream.write` — line 50, 2 lines
  - `TtyStream.flush` — line 53, 2 lines
  - `selected` — line 57, 4 lines
  - `write_result` — line 63, 4 lines
  - `plain` — line 69, 11 lines
  - `failed_import` — line 82, 24 lines
- `tests/packaging/packaging_support.py`
  - `_module_member` — line 91, 5 lines
  - `assert_installed` — line 117, 8 lines
  - `identity` — line 127, 3 lines
  - `initialize_installed_state` — line 132, 17 lines
  - `command_text` — line 151, 2 lines
  - `run_checked` — line 155, 21 lines
  - `isolated_environment` — line 178, 20 lines
  - `_run` — line 200, 12 lines
  - `_run_unchecked` — line 214, 15 lines
  - `_hostile_cwd` — line 231, 9 lines
  - `_installed_workflow_root` — line 242, 38 lines
  - `workflow_command` — line 282, 12 lines
  - `stall_command` — line 296, 14 lines
- `tests/runtime/test_attach.py`
  - `CliBoundary.launch` — line 29, 5 lines
  - `CliBoundary.attach` — line 35, 3 lines
  - `CliBoundary.snapshot` — line 39, 2 lines
  - `CliBoundary.guard_mutation` — line 43, 5 lines
  - `cli_boundary` — line 51, 14 lines
  - `test_interactive_run_launches_once_and_returns_exact_viewer_result` — line 72, 18 lines
  - `test_attach_selects_requested_scope_without_launching` — line 96, 17 lines
  - `test_json_attach_is_rejected_without_viewer_or_launch` — line 115, 13 lines
  - `_paused_project` — line 130, 11 lines
  - `_interactive_streams` — line 143, 3 lines
  - `test_resume_after_boundary_pause_launches_once_and_attaches_new_identity` — line 148, 20 lines
  - `test_noninteractive_resume_only_clears_pause` — line 174, 22 lines
  - `test_noninteractive_run_dispatches_foreground_without_detached_launch` — line 207, 24 lines
  - `test_noninteractive_run_dispatches_foreground_without_detached_launch.foreground` — line 218, 3 lines
  - `test_json_run_requires_explicit_foreground_opt_in` — line 233, 11 lines
  - `test_resume_revalidates_live_selected_run_then_attaches_without_launch` — line 247, 50 lines
  - `test_resume_revalidates_live_selected_run_then_attaches_without_launch.verify` — line 274, 3 lines
  - `test_stale_resume_selection_fails_closed_without_launch_or_attach` — line 299, 35 lines
  - `test_stale_resume_selection_fails_closed_without_launch_or_attach.stale` — line 320, 2 lines
  - `test_concurrent_resume_launch_loser_never_retries_or_attaches_other_owner` — line 336, 26 lines
  - `test_concurrent_resume_launch_loser_never_retries_or_attaches_other_owner.lose` — line 351, 3 lines
  - `test_resume_honors_configured_agent_when_restarting_after_pause` — line 364, 20 lines
- `tests/runtime/test_session_metrics.py`
  - `_metric` — line 26, 18 lines
  - `_metadata` — line 46, 10 lines
  - `_final` — line 58, 8 lines
  - `_rows` — line 68, 2 lines
  - `_usage` — line 72, 10 lines
  - `test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries` — line 86, 24 lines
  - `test_usage_requires_exact_keys_including_nullable_fields` — line 113, 20 lines
  - `test_pending_publication_and_finalization_keep_one_private_canonical_row` — line 135, 39 lines
  - `test_final_canonical_row_rejects_all_later_publications` — line 178, 26 lines
  - `test_initial_pending_publication_must_match_session_metadata` — line 207, 10 lines
  - `test_pending_row_cannot_be_finalized_under_another_identity` — line 220, 13 lines
  - `test_reconciliation_projects_interrupted_pending_without_rewriting_evidence` — line 236, 33 lines
  - `test_reconciliation_orders_by_start_then_session_and_does_not_accumulate_rows` — line 271, 28 lines
  - `test_capability_metrics_round_trip_without_phase_or_model` — line 301, 15 lines
  - `test_invalid_metric_values_are_rejected_without_replacing_pending` — line 340, 12 lines
  - `test_malformed_retained_rows_fail_visibly_and_preserve_previous_aggregate` — line 355, 22 lines
  - `test_metric_reader_round_trips_the_published_schema` — line 380, 5 lines
  - `test_metric_reader_rejects_invalid_schema_and_publication_invariants` — line 413, 6 lines
  - `test_metric_reader_rejects_missing_nullable_fields` — line 421, 5 lines
  - `test_metric_reader_rejects_invalid_values_in_complete_usage` — line 448, 28 lines
  - `test_metrics_choose_last_valid_session_rows_in_file_order_and_filter_batch` — line 478, 25 lines
  - `test_metrics_report_incomplete_aggregation_when_evidence_is_limited` — line 506, 24 lines
  - `test_metrics_default_record_budget_keeps_only_the_first_4096_rows` — line 532, 15 lines
  - `test_metrics_default_byte_budget_bounds_memory_and_leaves_later_rows_unread` — line 549, 25 lines
  - `test_explicit_byte_budget_reads_valid_rows_beyond_sixteen_mib` — line 576, 20 lines
  - `test_metrics_deduplicate_cumulative_usage_without_summing_session_updates` — line 598, 24 lines
  - `test_missing_evidence_observers_do_not_create_runtime_artifacts` — line 624, 11 lines
  - `test_session_evidence_does_not_follow_artifact_symlinks` — line 638, 13 lines
  - `test_session_evidence_reports_regular_raw_normalized_and_summary_artifacts` — line 653, 23 lines
  - `test_emergency_observation_preserves_marker_and_sanitizes_detail` — line 680, 30 lines
  - `test_emergency_observation_preserves_invalid_schema_as_malformed` — line 740, 15 lines
  - `test_emergency_observation_keeps_unsafe_marker_present_and_malformed` — line 758, 20 lines
- `tests/runtime/test_supervisor_cli.py`
  - `isolated_homes` — line 40, 3 lines
  - `_invoke` — line 45, 6 lines
  - `_success` — line 53, 7 lines
  - `_failure` — line 62, 13 lines
  - `_state` — line 77, 4 lines
  - `test_parser_inventory_and_reference_expose_the_same_lifecycle_commands` — line 83, 32 lines
  - `test_parser_exposes_init_state_and_workflow_command_inventory` — line 117, 23 lines
  - `test_pause_commits_boundary_intent_and_resume_clears_it` — line 143, 30 lines
  - `test_incomplete_lifecycle_commands_fail_with_json_usage_errors` — line 185, 12 lines
  - `test_stop_without_published_identity_fails_closed` — line 199, 9 lines
  - `selected_run` — line 220, 45 lines
  - `test_stop_signals_only_the_exact_fully_validated_supervisor` — line 267, 9 lines
  - `_invalidate_proof` — line 278, 46 lines
  - `test_stop_fails_closed_when_any_identity_or_ownership_proof_is_missing` — line 339, 10 lines
  - `test_stop_rejects_an_unregistered_run_even_when_metadata_matches` — line 351, 7 lines
  - `test_exact_run_pause_and_resume_use_compare_and_set` — line 360, 22 lines
  - `test_stale_selection_before_compare_and_set_leaves_state_untouched` — line 399, 17 lines
  - `test_replacement_during_control_rolls_back_then_reports_stale` — line 419, 35 lines
  - `test_replacement_during_control_rolls_back_then_reports_stale.replace_then_change_owner` — line 434, 7 lines
  - `FakeChild.poll` — line 461, 2 lines
  - `LaunchBoundary.spawn` — line 476, 6 lines
  - `LaunchBoundary.snapshot` — line 483, 2 lines
  - `launch_boundary` — line 488, 27 lines
  - `test_launch_detaches_exact_child_with_literal_argv_and_private_report` — line 519, 38 lines
  - `test_launch_rejects_ambiguous_or_unrelated_identity_without_replacement` — line 572, 27 lines
  - `test_launch_waits_for_exact_child_publication_only_until_configured_deadline` — line 602, 35 lines
  - `test_launch_waits_for_exact_child_publication_only_until_configured_deadline.tick` — line 611, 3 lines
  - `test_launch_waits_for_exact_child_publication_only_until_configured_deadline.sleep` — line 615, 2 lines
  - `test_launch_waits_for_exact_child_publication_only_until_configured_deadline.snapshot` — line 618, 4 lines
  - `test_timeout_names_child_and_explicit_attach_stop_recovery` — line 639, 16 lines
  - `test_early_exit_preserves_bounded_sanitized_failure_evidence` — line 660, 23 lines
  - `test_launch_report_is_private_before_child_runs` — line 685, 16 lines
  - `test_launch_report_is_private_before_child_runs.spawn` — line 692, 5 lines
  - `test_replaced_report_symlink_never_exposes_outside_content` — line 703, 24 lines
  - `test_replaced_report_symlink_never_exposes_outside_content.spawn` — line 713, 6 lines
  - `test_child_scrubs_report_environment_before_constructing_agent_driver` — line 729, 24 lines
  - `test_child_scrubs_report_environment_before_constructing_agent_driver.reject_driver` — line 743, 3 lines
  - `test_child_rejects_outside_report_destination_without_writing_it` — line 756, 26 lines
  - `test_child_rejects_outside_report_destination_without_writing_it.reject_driver` — line 774, 3 lines
- `tests/state/test_cli.py`
  - `_seed_restore_cli` — line 36, 22 lines
  - `test_state_restore_cli_routes_through_state_service` — line 60, 43 lines
  - `test_state_restore_cli_routes_through_state_service.recording_restore` — line 70, 7 lines
  - `test_error_code_contains_exactly_the_public_failure_values` — line 105, 2 lines
  - `test_main_normalizes_argparse_mistakes_to_usage_exit_one` — line 126, 9 lines
  - `test_main_accepts_only_declared_top_level_and_subparser_option_spellings` — line 137, 45 lines
  - `_assert_show_option_spellings` — line 184, 23 lines
  - `test_init_uses_explicit_root_preserves_config_and_ignores_legacy_state` — line 209, 43 lines
  - `test_init_rejects_symlinked_runtime_components_without_touching_target` — line 263, 35 lines
  - `test_init_config_creation_failure_leaves_no_state_and_retry_succeeds` — line 300, 28 lines
  - `_create_config_directory` — line 330, 2 lines
  - `_create_broken_config_symlink` — line 334, 2 lines
  - `test_init_rejects_project_config_path_collisions_before_state_publication` — line 345, 23 lines
  - `test_init_discovers_an_absolute_project_root_and_creates_missing_config` — line 371, 38 lines
  - `test_json_failures_have_stable_codes_exits_and_streams` — line 461, 25 lines
  - `test_schema_failures_are_classified_without_tracebacks` — line 489, 30 lines
  - `test_invalid_persisted_value_cannot_spoof_resource_limit_classification` — line 521, 19 lines
  - `test_inline_json_duplicate_keys_are_rejected_without_mutation` — line 552, 25 lines
  - `test_json_file_duplicate_keys_are_rejected_without_mutation` — line 589, 19 lines
  - `test_persisted_duplicate_keys_have_stable_state_io_error` — line 611, 38 lines
  - `test_duplicate_backup_has_stable_invalid_backup_error_without_mutation` — line 651, 36 lines
  - `test_object_only_task_payloads_reject_every_non_object_json_shape_without_mutation` — line 706, 20 lines
  - `test_directory_sync_refusal_reports_unsupported_durability` — line 728, 34 lines
  - `test_directory_sync_refusal_reports_unsupported_durability.refuse_directory_sync` — line 737, 4 lines
  - `test_exception_name_alone_does_not_report_unsupported_durability` — line 764, 37 lines
  - `test_exception_name_alone_does_not_report_unsupported_durability.raise_same_named_untyped_error` — line 775, 9 lines
- `tests/state/test_commands.py`
  - `_directory_bytes` — line 35, 6 lines
  - `_attempt` — line 43, 22 lines
  - `_task` — line 67, 33 lines
  - `_state_with_tasks` — line 102, 8 lines
  - `_store_for_state` — line 112, 4 lines
  - `_service_for_state` — line 118, 5 lines
  - `_record_transactions` — line 125, 19 lines
  - `_record_transactions.transaction` — line 129, 12 lines
  - `_service_with_transaction_spy` — line 146, 6 lines
  - `_task_by_id` — line 154, 4 lines
  - `_assert_result` — line 160, 8 lines
  - `test_generic_writable_prefixes_are_only_the_extension_containers` — line 170, 5 lines
  - `_service_with_namespaced_extensions` — line 177, 11 lines
  - `test_generic_mutations_accept_namespaced_extension_descendants` — line 190, 50 lines
  - `test_generic_mutations_reject_deep_values_before_copying_or_transacting` — line 243, 18 lines
  - `test_generic_mutations_protect_every_path_outside_strict_extension_descendants` — line 292, 23 lines
  - `test_unsafe_generic_mutations_recover_valid_core_fields` — line 317, 45 lines
  - `test_invalid_generic_mutations_preserve_state_and_backup` — line 418, 16 lines
  - `test_generic_mutation_revision_conflict_preserves_state_and_backup` — line 436, 20 lines
  - `_leaf_parsers` — line 475, 17 lines
  - `_parser_command_inventory` — line 494, 12 lines
  - `_invoke_main` — line 508, 7 lines
  - `_assert_json_failure` — line 517, 18 lines
  - `_initialize_cli_root` — line 537, 9 lines
  - `_initialize_running_cli_task` — line 548, 35 lines
- `tests/state/test_guarded_service.py`
  - `seed` — line 28, 18 lines
  - `invoke` — line 48, 10 lines
  - `durable_bytes` — line 60, 3 lines
  - `test_control_change_commits_once_and_preserves_unrelated_state` — line 75, 19 lines
  - `test_guard_rejection_at_every_durable_boundary_restores_exact_bytes` — line 107, 35 lines
  - `test_guard_rejection_at_every_durable_boundary_restores_exact_bytes.invalidate` — line 121, 3 lines
  - `test_guard_rejection_at_every_durable_boundary_restores_exact_bytes.guard` — line 125, 3 lines
  - `test_revision_conflict_preserves_bytes_and_allows_later_guarded_commit` — line 145, 28 lines
  - `test_revision_conflict_preserves_bytes_and_allows_later_guarded_commit.guard` — line 152, 3 lines
  - `test_rejecting_guard_prevents_mutation_without_cas_or_on_idle_batch` — line 177, 22 lines
  - `test_rejecting_guard_prevents_mutation_without_cas_or_on_idle_batch.reject` — line 191, 2 lines
  - `test_guarded_control_result_matches_ordinary_service` — line 202, 12 lines
- `tests/tui/model_support.py`
  - `FixedClock.now` — line 23, 3 lines
  - `Projection.owned_observation` — line 50, 7 lines
  - `Projection.poll` — line 58, 3 lines
- `tests/tui/test_app.py`
  - `_run` — line 40, 2 lines
  - `_view` — line 44, 20 lines
  - `_screen_text` — line 75, 6 lines
  - `Observer.__init__` — line 84, 5 lines
  - `Observer.poll` — line 90, 8 lines
  - `Observer.close` — line 99, 2 lines
  - `Controls.__init__` — line 104, 2 lines
  - `Controls.pause` — line 107, 4 lines
  - `Controls.resume` — line 112, 2 lines
  - `Controls.stop` — line 115, 3 lines
  - `Registry.__init__` — line 121, 3 lines
  - `Registry.snapshot` — line 125, 18 lines
  - `Terminal.isatty` — line 146, 2 lines
  - `InterruptingInput.readline` — line 151, 2 lines
  - `isolated_configuration` — line 156, 3 lines
  - `test_fleet_navigation_returns_the_exact_highlighted_run` — line 161, 10 lines
  - `test_fleet_navigation_returns_the_exact_highlighted_run.exercise` — line 165, 3 lines
  - `test_fleet_detaches_without_selecting_a_run` — line 174, 11 lines
  - `test_fleet_detaches_without_selecting_a_run.exercise` — line 177, 5 lines
  - `test_project_detaches_without_stopping_its_run` — line 188, 11 lines
  - `test_project_detaches_without_stopping_its_run.exercise` — line 192, 3 lines
  - `test_project_polls_and_controls_only_the_last_observed_run` — line 201, 37 lines
  - `test_project_polls_and_controls_only_the_last_observed_run.exercise` — line 210, 24 lines
  - `test_stop_requires_confirmation_and_cancellation_never_stops` — line 241, 24 lines
  - `test_stop_requires_confirmation_and_cancellation_never_stops.exercise` — line 248, 14 lines
  - `test_question_mark_toggles_visible_help_without_controls` — line 267, 17 lines
  - `test_question_mark_toggles_visible_help_without_controls.exercise` — line 271, 10 lines
  - `test_project_completion_exits_without_stopping` — line 286, 14 lines
  - `test_project_completion_exits_without_stopping.exercise` — line 290, 6 lines
  - `test_plain_fleet_reads_one_line_and_returns_exact_selection` — line 303, 11 lines
  - `test_plain_fleet_invalid_or_eof_input_never_selects_a_run` — line 317, 11 lines
  - `test_plain_fleet_interrupt_never_selects_a_run` — line 330, 7 lines
  - `test_plain_project_polls_until_completion` — line 339, 15 lines
  - `test_plain_project_interrupt_or_eof_is_detach` — line 357, 6 lines
  - `test_plain_project_observation_failure_returns_nonzero` — line 365, 6 lines
  - `test_attach_ui_failure_falls_back_with_same_selection_and_observer` — line 375, 36 lines
  - `test_attach_ui_failure_falls_back_with_same_selection_and_observer.observe` — line 385, 3 lines
  - `test_attach_ui_failure_falls_back_with_same_selection_and_observer.fail_viewer` — line 389, 5 lines
  - `test_fleet_ui_failure_selects_one_line_then_views_that_run` — line 413, 26 lines
  - `test_fleet_ui_failure_selects_one_line_then_views_that_run.observe` — line 420, 3 lines
  - `test_fleet_ui_failure_selects_one_line_then_views_that_run.fail_viewer` — line 424, 2 lines
  - `test_post_mount_failure_restores_terminal_before_plain_fallback` — line 441, 43 lines
  - `test_post_mount_failure_restores_terminal_before_plain_fallback.crash_after_mount` — line 451, 6 lines
  - `test_post_mount_failure_restores_terminal_before_plain_fallback.plain` — line 458, 5 lines
  - `test_control_error_remains_visible_without_retargeting` — line 486, 29 lines
  - `test_control_error_remains_visible_without_retargeting.RejectingControls.pause` — line 490, 5 lines
  - `test_control_error_remains_visible_without_retargeting.exercise` — line 499, 12 lines
  - `test_attach_viewer_failure_returns_nonzero_without_stopping` — line 517, 19 lines
  - `test_attach_viewer_failure_returns_nonzero_without_stopping.fail_viewer` — line 524, 2 lines
  - `test_attach_normal_detach_closes_the_selected_observer` — line 538, 15 lines
  - `test_theme_result_is_a_frozen_slotted_value` — line 555, 7 lines
  - `test_relative_config_root_resolves_against_current_directory` — line 564, 7 lines
  - `test_missing_theme_uses_an_allowlisted_default_without_a_gap` — line 573, 6 lines
  - `test_allowlisted_theme_round_trips_with_private_permissions` — line 582, 9 lines
  - `test_invalid_theme_name_does_not_mutate_existing_content` — line 594, 11 lines
  - `test_invalid_or_oversized_theme_returns_a_sanitized_gap` — line 612, 10 lines
  - `test_symlinked_theme_file_is_rejected_without_reading_target` — line 624, 14 lines
  - `test_trusted_xdg_config_alias_loads_intended_theme` — line 640, 13 lines
  - `test_non_regular_theme_file_returns_a_visible_gap` — line 655, 8 lines
  - `test_unavailable_theme_file_returns_a_visible_gap` — line 665, 12 lines
  - `test_theme_save_atomically_replaces_the_file_without_temp_artifacts` — line 679, 10 lines
  - `test_theme_save_rejects_an_existing_symlink_without_following_it` — line 691, 15 lines
  - `test_invalid_theme_gap_is_visible_without_blocking_project_ui` — line 708, 16 lines
  - `test_invalid_theme_gap_is_visible_without_blocking_project_ui.exercise` — line 715, 6 lines
  - `test_invalid_theme_does_not_block_attach_or_plain_fallback` — line 726, 24 lines
  - `test_rendered_and_source_ui_text_is_ovcaq_and_provider_neutral` — line 752, 30 lines
  - `test_rendered_and_source_ui_text_is_ovcaq_and_provider_neutral.render` — line 758, 8 lines
- `tests/tui/test_app_ended_selection.py`
  - `EndedObserver.__init__` — line 16, 24 lines
  - `EndedObserver.poll` — line 41, 5 lines
  - `EndedObserver.close` — line 47, 2 lines
  - `NoControls.pause` — line 52, 2 lines
  - `NoControls.resume` — line 55, 2 lines
  - `NoControls.stop` — line 58, 2 lines
  - `test_plain_ended_uncertain_result_fails_visibly_without_repolling` — line 63, 10 lines
  - `test_textual_ended_uncertain_result_fails_without_repolling` — line 76, 16 lines
  - `test_textual_ended_uncertain_result_fails_without_repolling.exercise` — line 85, 4 lines
- `tests/tui/test_app_poll_responsiveness.py`
  - `view_for` — line 22, 22 lines
  - `BlockedObserver.__init__` — line 47, 10 lines
  - `BlockedObserver.poll` — line 58, 19 lines
  - `BlockedObserver.close` — line 78, 5 lines
  - `Controls.__init__` — line 86, 2 lines
  - `Controls.pause` — line 89, 4 lines
  - `Controls.resume` — line 94, 2 lines
  - `Controls.stop` — line 97, 3 lines
  - `Registry.__init__` — line 103, 2 lines
  - `Registry.snapshot` — line 106, 17 lines
  - `Terminal.isatty` — line 126, 2 lines
  - `isolated_config` — line 131, 3 lines
  - `wait_for` — line 136, 4 lines
  - `test_help_and_detach_respond_before_blocked_poll_finishes` — line 143, 36 lines
  - `test_help_and_detach_respond_before_blocked_poll_finishes.exercise` — line 151, 22 lines
  - `test_poll_is_single_flight_and_completed_view_preserves_selected_controls` — line 181, 34 lines
  - `test_poll_is_single_flight_and_completed_view_preserves_selected_controls.exercise` — line 188, 19 lines
  - `headless_exit` — line 217, 15 lines
  - `headless_exit.exercise` — line 220, 9 lines
  - `test_attach_detach_or_fallback_finishes_observation_before_close_or_plain_poll` — line 235, 41 lines
  - `test_attach_detach_or_fallback_finishes_observation_before_close_or_plain_poll.plain` — line 245, 6 lines
- `tests/tui/test_model.py`
  - `_event` — line 42, 11 lines
  - `_batch` — line 55, 8 lines
  - `_metric` — line 65, 21 lines
  - `projection` — line 89, 34 lines
  - `_recovery` — line 125, 13 lines
  - `test_status_respects_durable_precedence_over_active_run` — line 155, 44 lines
  - `test_emergency_failure_only_applies_to_selected_run` — line 210, 11 lines
  - `test_state_projects_counts_phase_review_and_notice_without_mutating_input` — line 223, 29 lines
  - `test_active_operator_stop_takes_precedence_over_recovery_and_pause` — line 254, 17 lines
  - `test_idle_halt_metric_remains_visible_after_agent_exit` — line 273, 9 lines
  - `test_lane_labels_and_details_follow_the_normalized_contract` — line 284, 21 lines
  - `test_malformed_lane_display_values_become_visible_gaps` — line 308, 9 lines
  - `test_failed_capability_remains_visible_after_drain_with_exact_retry_argv` — line 322, 42 lines
  - `test_selected_identity_is_revalidated_before_reading_replacement_state` — line 369, 34 lines
  - `test_selected_identity_is_revalidated_before_reading_replacement_state.forbidden_read` — line 393, 2 lines
  - `test_observational_read_failure_becomes_gap_and_unknown_numeric_values` — line 409, 14 lines
  - `test_observational_read_failure_becomes_gap_and_unknown_numeric_values.unreadable` — line 412, 2 lines
  - `test_metrics_supply_known_usage_independently_of_elapsed_duration` — line 425, 20 lines
  - `test_partial_metrics_preserve_unknown_usage_and_diagnostic_gaps` — line 447, 13 lines
  - `test_absent_usage_remains_unknown_with_known_elapsed` — line 462, 21 lines
  - `test_raw_only_telemetry_survives_missing_normalization` — line 490, 43 lines
  - `test_raw_only_telemetry_survives_missing_normalization.evidence` — line 500, 3 lines
  - `test_lane_start_progress_and_terminal_records_keep_observed_provider` — line 538, 19 lines
  - `test_lane_without_start_reports_unknown_and_partial_history` — line 560, 12 lines
  - `test_lane_retention_evicts_oldest_terminal_before_active_lanes` — line 574, 19 lines
  - `test_gap_retention_deduplicates_and_collapses_overflow` — line 595, 15 lines
  - `test_follower_reset_clears_lanes_and_latest_session_usage` — line 612, 24 lines
  - `test_backlog_stays_visible_until_later_polls_drain_it` — line 638, 17 lines
  - `test_real_follower_tolerates_malformed_record_and_observes_valid_neighbor` — line 657, 18 lines
  - `test_display_text_preserves_plain_content_within_explicit_limit` — line 680, 8 lines
  - `test_display_text_removes_terminal_and_unicode_format_controls` — line 690, 10 lines
  - `test_projection_records_are_immutable_and_slotted` — line 719, 6 lines
  - `test_project_view_is_immutable_and_slotted` — line 727, 6 lines
  - `test_shared_observation_failures_are_reported_as_gaps` — line 744, 12 lines
  - `test_shared_observation_failures_are_reported_as_gaps.fail` — line 747, 2 lines
  - `test_observer_sanitizes_and_bounds_dynamic_values_before_returning_view` — line 758, 32 lines
- `tests/tui/test_model_elapsed_duration.py`
  - `ObservationClock.now` — line 41, 2 lines
  - `live_run` — line 52, 32 lines
  - `metric` — line 86, 20 lines
  - `test_active_duration_advances_from_run_start_independently_of_metrics` — line 109, 27 lines
  - `test_invalid_or_future_run_start_is_unknown_even_with_finalized_metrics` — line 147, 14 lines
  - `test_malformed_metrics_do_not_hide_elapsed_time_or_mutate_evidence` — line 163, 17 lines
  - `test_final_ended_duration_is_known_and_stable_on_later_polls` — line 182, 27 lines
  - `write_terminal_metrics` — line 211, 33 lines
  - `test_ended_pause_uses_only_selected_run_metric_end_or_unknown` — line 247, 29 lines
- `tests/tui/test_model_live_evidence.py`
  - `Evidence.event` — line 51, 14 lines
  - `Evidence.write` — line 66, 4 lines
  - `pending_metric` — line 72, 18 lines
  - `evidence` — line 93, 42 lines
  - `test_observer_filters_live_events_by_exact_run_and_session_identity` — line 146, 15 lines
  - `damage_stream` — line 163, 15 lines
  - `test_one_shot_stream_gaps_survive_later_refreshes` — line 181, 18 lines
  - `test_bounded_backlog_has_one_diagnostic_without_claiming_truncation` — line 201, 16 lines
  - `test_follower_backlog_does_not_report_a_truncation_gap` — line 219, 18 lines
  - `add_failed_capability` — line 239, 27 lines
  - `test_capability_exposes_last_attempt_evidence_under_configured_runtime_root` — line 270, 46 lines
  - `test_capability_evidence_defaults_preserve_existing_constructor` — line 318, 4 lines
  - `test_published_integer_and_float_costs_remain_known` — line 334, 26 lines
- `tests/tui/test_theme_persistence.py`
  - `Observer.__init__` — line 25, 20 lines
  - `Observer.poll` — line 46, 2 lines
  - `Observer.close` — line 49, 2 lines
  - `Controls.pause` — line 54, 4 lines
  - `Controls.resume` — line 59, 2 lines
  - `Controls.stop` — line 62, 2 lines
  - `_app` — line 66, 5 lines
  - `_screen_text` — line 73, 6 lines
  - `isolated_configuration` — line 82, 7 lines
  - `test_all_real_theme_changes_persist_and_load_in_a_later_app` — line 92, 32 lines
  - `test_all_real_theme_changes_persist_and_load_in_a_later_app.exercise` — line 99, 22 lines
  - `test_mount_preserves_bad_file_and_displays_a_nonfatal_safe_gap` — line 128, 31 lines
  - `test_mount_preserves_bad_file_and_displays_a_nonfatal_safe_gap.exercise` — line 144, 9 lines
  - `test_mount_without_a_preference_uses_dark_without_writing` — line 162, 16 lines
  - `test_mount_without_a_preference_uses_dark_without_writing.exercise` — line 169, 6 lines
  - `test_failed_user_theme_save_is_visible_and_app_can_still_detach` — line 181, 26 lines
  - `test_failed_user_theme_save_is_visible_and_app_can_still_detach.exercise` — line 190, 15 lines
  - `_select_anchor` — line 209, 30 lines
  - `test_theme_storage_uses_shared_trusted_xdg_anchor_semantics` — line 254, 13 lines
  - `test_allowlisted_save_is_private_atomic_and_leaves_no_temporary_files` — line 272, 30 lines
  - `test_disallowed_theme_names_preserve_the_existing_file` — line 305, 12 lines
  - `test_invalid_oversized_or_undecodable_file_is_ignored_without_content_leak` — line 322, 13 lines
  - `test_descendant_symlinks_are_rejected_without_changing_their_targets` — line 338, 23 lines
  - `test_nonregular_theme_files_are_ignored_without_blocking` — line 364, 11 lines
  - `test_read_never_follows_a_descendant_replaced_at_the_open_boundary` — line 378, 30 lines
  - `test_read_never_follows_a_descendant_replaced_at_the_open_boundary.replace_at_open` — line 390, 8 lines
  - `test_save_preserves_concurrent_replacement_evidence_and_reports_a_gap` — line 411, 36 lines
  - `test_save_preserves_concurrent_replacement_evidence_and_reports_a_gap.replace_at_open` — line 425, 8 lines
  - `test_concurrent_reader_atime_update_does_not_prevent_saving_a_new_theme` — line 449, 39 lines
  - `test_concurrent_reader_atime_update_does_not_prevent_saving_a_new_theme.read_at_open` — line 458, 17 lines


## Tautological test shapes (computed, do not re-judge)

Each `[MECH]` line is a test whose shape cannot fail as written. Raise
it; step 6 adds any line the table lacks. `mech-check` is the finder.


Checked 246 test function(s) in 22 test file(s).


## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `5544b1fc9c27`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

replay: skipped (runner did not complete: Command '['uv', 'run', 'pytest', '-q', '-rA', '--rootdir', '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/replay-shwrr56b/wt', '-p', 'no:cacheprovider', '--continue-on-collection-errors', 'tests/integration/test_control_commit_identity.py', 'tests/integration/test_guarded_run_mutation.py', 'tests/integration/test_launcher_outcomes.py', 'tests/integration/test_native_telemetry_identity.py', 'tests/integration/test_observer_terminal_cleanup.py', 'tests/integration/test_observer_terminal_viewers.py', 'tests/integration/test_supervisor_live_telemetry.py', 'tests/integration/test_terminal_lifecycle.py', 'tests/integration/test_viewer_fallback.py', 'tests/runtime/test_attach.py', 'tests/runtime/test_session_metrics.py', 'tests/runtime/test_supervisor_cli.py', 'tests/state/test_cli.py', 'tests/state/test_commands.py', 'tests/state/test_guarded_service.py', 'tests/tui/test_app.py', 'tests/tui/test_app_ended_selection.py', 'tests/tui/test_app_poll_responsiveness.py', 'tests/tui/test_model.py', 'tests/tui/test_model_elapsed_duration.py', 'tests/tui/test_model_live_evidence.py', 'tests/tui/test_theme_persistence.py']' timed out after 600.0 seconds)


## Verification evidence
The coordinator ran all following checks against the exact reviewed HEAD.
{
  "command": [
    "uv",
    "run",
    "pytest",
    "-q",
    "--tb=short"
  ],
  "exit": 0,
  "sha": "2eb175512b7fd0f79e7cb32b9a6581d2d86e802c"
}

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4579 passed, 2 warnings in 188.06s (0:03:08)
{
  "command": [
    "uv",
    "run",
    "ruff",
    "check",
    "."
  ],
  "exit": 0,
  "sha": "2eb175512b7fd0f79e7cb32b9a6581d2d86e802c"
}
All checks passed!
{
  "command": [
    "uv",
    "run",
    "ruff",
    "format",
    "--check",
    "."
  ],
  "exit": 0,
  "sha": "2eb175512b7fd0f79e7cb32b9a6581d2d86e802c"
}
205 files already formatted
{
  "command": [
    "uv",
    "run",
    "mypy",
    "src/ovcaq"
  ],
  "exit": 0,
  "sha": "2eb175512b7fd0f79e7cb32b9a6581d2d86e802c"
}
Success: no issues found in 60 source files
{
  "command": [
    "uv",
    "build"
  ],
  "exit": 0,
  "sha": "2eb175512b7fd0f79e7cb32b9a6581d2d86e802c"
}
Building wheel from source distribution...
Successfully built dist/ovcaq-0.1.0.dev0.tar.gz
Successfully built dist/ovcaq-0.1.0.dev0-py3-none-any.whl


## Repair handoff evidence
# PRD 00008 recovery build handoff

Settled product HEAD: `e90ce6bea414a775b008d5098b746a2e44dee3ef`. All 14 recovery tasks are complete.
Cycle-1 repairs are ready for fresh cycle-2 completion review; this build session ran no completion-review lens.
The original work_start_sha remains 1f500258065d431de41102dcc64f8d43d07ac44f and rework_cap remains 2.

## Verification

Final full suite: `4579 passed, 2 warnings in 160.54s (0:02:40)`.
Final Ruff lint and format checks both exit 0. The initial uv sync, mypy (60 source files), and wheel/sdist build passed at cce42f8. Mypy passed again after the observation error-boundary change. The final full suite exercises current wheel/sdist membership and installation.
The first full run found 44 failures and 76 errors (4,458 passed). One phase-final fix cycle reopened their owning tasks and dispatched isolated full-persona Ivan fixes. Existing test seams were migrated to the accepted shared-observer/lazy-viewer/guarded-transaction contracts; duration expectations now assert selected-run elapsed time, and XDG tests retain the trusted-anchor contract. Real regressions in standalone run_once and observation error reporting were fixed in production.
Full raw command output remains in docs/dev/tmp/rfinal-*.log and the task-specific logs named by each report. The durable build-verification-1.json records command exits and their actual product SHAs; no pre-fix result is attributed to the final HEAD. The cycle-1 verification queue is empty ([]).

## Task evidence and mechanical gates

The following values come from each repair's latest recorded style attempt, including final-regression supplements where stamped. No budget or earlier evidence was reset.

- 1: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-1.md)
- 2: style_gate: clean, split_hygiene: failed: checker reports three used packaging exports; required one deletion-only fix pass made no unsafe deletion — [repair evidence](00008-tui-python-launcher-v1-repair-task-2.md)
- 3: style_gate: fixed:019949ad8f49dd73f645662ee658fa5aec429dda, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-3.md)
- 4: style_gate: clean, split_hygiene: failed: checker reports used exports T2 and ERROR_CODES; required one deletion-only fix pass made no unsafe deletion — [repair evidence](00008-tui-python-launcher-v1-repair-task-4.md)
- 5: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-5.md)
- 6: style_gate: clean, split_hygiene: skipped:no-tests — [repair evidence](00008-tui-python-launcher-v1-repair-task-6.md)
- 7: style_gate: fixed:53c75fec64120a16facc59d419fff340e5cfd6ad, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-7.md)
  Reflow tripwire: `src/ovcaq/supervisor_cli.py:26`.
- 8: style_gate: clean, split_hygiene: skipped:no-tests — [repair evidence](00008-tui-python-launcher-v1-repair-task-8.md)
- 9: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-9.md)
- 10: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-10.md)
  Reflow tripwire: `tests/integration/test_viewer_fallback.py:32`.
- 11: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-11.md)
- 12: style_gate: clean, split_hygiene: skipped:no-tests — [repair evidence](00008-tui-python-launcher-v1-repair-task-12.md)
- 13: style_gate: clean, split_hygiene: skipped:no-tests — [repair evidence](00008-tui-python-launcher-v1-repair-task-13.md)
- 14: style_gate: clean, split_hygiene: clean — [repair evidence](00008-tui-python-launcher-v1-repair-task-14.md)

Final-regression evidence:

- [Task 11](00008-tui-python-launcher-v1-final-fix-1-task-11.md)
- [Task 7](00008-tui-python-launcher-v1-final-fix-1-task-7.md)
- [Task 1](00008-tui-python-launcher-v1-final-fix-1-task-1.md)
- [Task 4](00008-tui-python-launcher-v1-final-fix-1-task-4.md)
- [Task 6](00008-tui-python-launcher-v1-final-fix-1-task-6.md)
- [Task 2](00008-tui-python-launcher-v1-final-fix-1-task-2.md)
- [Task 3](00008-tui-python-launcher-v1-final-fix-1-task-3.md)
- [Task 9](00008-tui-python-launcher-v1-final-fix-1-task-9.md)
- [Task 10](00008-tui-python-launcher-v1-final-fix-1-task-10.md)

The final split-hygiene checker reports three existing packaging_support exports and two test_commands exports as UNUSED. Each owning task received its required one deletion-only Ivan pass, which verified live importing consumers and correctly made no deletion; repeated checks still report them. These are retained nonblocking checker limitations, not clean split-hygiene verdicts. Final style limits and other mechanical results are recorded in the final-gates artifact.
Task 11's final comment-only lint commit preceded its reflow probe; it changed one hunk, below the threshold. Task 8's original reflow evidence was reconstructed retrospectively as documented in its report. Task 6's first sandbox-failed narrow-run log paths were overwritten by its approved rerun; original failure evidence survives in the session transcript and report.

## Provenance and remaining review obligations

Native logical sonnet dispatches used OpenAI gpt-5.6-sol; logical opus used OpenAI gpt-6-astra. These are the user-authorized task-agent substitutions, not the source external Codex rung. Task reviews used the guarded external Claude Sonnet wrapper and preserved their raw verdicts. No native model-diversity claim is made.
Fresh cycle 2 must dispatch implementation-aware Alice with the complete R rubric, PRD-only blind Blake with the complete B rubric, and external Claude Opus Bob with D1-D5 plus de-slop appendix. Bob must use the autocodex reviewer helper and include its immutable receipt in consolidated top matter. Prior review-1 at 5544b1f cannot approve this repaired HEAD; remaining LOW notes and task-2 race-coverage limits remain review inputs.
The source single Devon/Tess budgets were preserved. Task 14 removed the real-adapter summary workaround and closed the summary-publication limitation recorded for task 1, with all eight mandatory strengthening mutations retained in its evidence.

## Cleanup and handoff

Only the main worktree and master branch exist; no stale worktree or orphan branch needs removal. The two top-level implementation plans remain sequencing authorities for later PRDs. Prior fast-track handoffs are durable audit records. Active-PRD scratch evidence is retained for the next reviewer; task-3 temporary verification logs were moved into docs/dev/tmp. No foreign product edits remain.
Canonical build/tasks_done followed by review/rework has advanced to cycle 2 and cleared rework_task_ids, without entering review in this process. Do not repeat those transitions. The contract card and brief precede the build leave row and final store recording. The store-only handoff commit may advance HEAD beyond the tested product SHA; last-verification is not falsified to conceal that.



## PRD 00008 assumption ledger


## Task 1 — Bounded JSONL tailing and shared metric/evidence readers

- The follower memory regression allows a 512 KiB peak while reading a 2 MiB row in 4 KiB chunks; the metrics aggregation regression allows a 48 MiB peak for a retained fixture larger than 64 MiB.
- Non-regular paths and open failures map to the public `missing` gap because the five-kind contract has no distinct unsafe/unavailable value.
- Read-budget exhaustion retains the public `backlog` flag and currently emits a `truncated` gap; Pat left the gap-kind overlap as a LOW review note.
- Whole-file metrics observation requests replay from byte zero with `replay_bytes=sys.maxsize`; actual reads remain bounded by the configured byte and record limits.
- The style split moved session observation helpers to `_session_io.py`; repository search found no monkeypatches of their former private module locations.
- Decoder faults retain the bounded `row rejected: <ExceptionName>` detail. The confirmed `RecursionError`/ordinary-exception fix passed the focused suite, but Pat's one allowed MEDIUM rerun still requested explicit regression tests, so the attempt is stamped `medium-retry:unfixed` for PRD-level review.

## Task 2 — Identity-bound fleet discovery

- Live runs sort by exact `(root, started_at, run_id)` values; no further tie-breaker is added.
- Malformed and stale registry paths retain the snapshot's original order rather than being re-sorted.
- Root selection compares exact `Path` values without resolving or normalizing them.
- Devon's single adversarial round proved and Tess closed eight projection/selection gaps: hardcoded fields, input-order dependence, dropped runs, timestamp rewriting, conditional diagnostic loss, singleton selector bypass, basename-only roots, and ambiguous duplicate run IDs.

## Task 3 — Provider-neutral project projections and core panels

- Each poll rebuilds transient gap reporting, so an event-backlog gap disappears after the follower drains; lanes, provider identity, normalized/raw evidence, and live usage persist until an explicit follower reset.
- Durable status precedence is state-write failure, identity inconsistency, operator stop, parking/stall recovery, pause request, attention, paused, halted, completed, running, then unknown. A latest completed metric whose decision is `halt` supplies the idle halted state.
- Lane labels and details accept strings only; malformed values produce a visible telemetry gap. Display text strips terminal and formatting control categories and truncates retained values to 512 characters.
- Usage aggregates completed metric rows with retained live session usage. A metric-covered session evicts its live sample; only the newest sample per remaining session is retained, capped at 256 sessions.
- Telemetry is partial when any gap exists, raw-only for raw evidence without normalized observations, unavailable when neither normalized observations nor metric rows exist, and complete otherwise.
- Identity mismatch reads no selected-run state, events, metrics, emergency marker, or evidence and projects an unknown status plus a gap.
- Devon's adversarial round closed eight refresh, aggregation, retention, and rendering weaknesses. Pat's one MEDIUM retry bounded retained usage and removed metric-covered sessions; the rerun reported no findings. Pat's original LOW notes remain PRD-level review evidence.

## Task 4 — Post-drain capability status and retry evidence

- Retry argv is presentation-only data and is rendered with `shlex.join`; no renderer executes it.
- The task added focused lifecycle, evidence-retention, required/optional, compact-view, unknown-value, determinism, and non-execution coverage. The single red failure was the prior plain-space join of retry argv.
- Pat reported LOW test-strength and duplication notes for the new capability assertions; they remain PRD-level review evidence. His scope note arose from the test-author scratch description, while the canonical task explicitly names `src/ovcaq/tui/panels.py` as its production location.

## Task 5 — Exact-run controls and Textual navigation

- The design required Pilot coverage and bounded plain selection without naming the app seams or bound. The test contract resolves these as public `FleetApp`/`ProjectApp` classes, public `RunControlService`/`StaleSelectionError`, and one 4096-character run-ID input line.
- A revision conflict retains the state store's `StateError`; exact-run identity replacement uses `StaleSelectionError`, whose `committed` flag distinguishes pre-write rejection from post-write replacement.
- `p` resumes a paused or pause-requested run and requests pause for other live statuses. Only completed status ends a project view automatically.
- Non-interactive attach enters plain mode without attempting Textual. Plain fleet selection accepts a run ID only; a line without its terminating newline or beyond the bound selects nothing.
- Project observers use `runtime_settings(run.root)`. All attach exit paths close the observer; viewer failure returns nonzero without signaling the supervisor.
- Devon proved and Tess closed eight identity-proof, post-commit, rendering, closure, and confirmation-retargeting gaps. Pat reported only LOW notes concerning revision-conflict wording, the unused fallback reason, duplicated fallback code, exception breadth, and metadata-read duplication; they remain PRD-level review evidence.

## Task 6 — OVCAQ theme persistence and user-facing branding

- The test contract resolves the unspecified theme boundary as public `theme_path`, `load_theme`, and `save_theme` functions with a frozen slotted `ThemeResult`; theme reads are capped at 256 bytes and names are allowlisted to the five built-in Textual themes exercised by tests.
- Missing theme state selects an allowlisted default without a gap. Invalid or unavailable theme state uses the sanitized visible marker `theme-unavailable:using-default` and never blocks attach or plain fallback.
- A relative `XDG_CONFIG_HOME` is joined to the current directory without resolving through symlinks. The config root and `ovcaq` directory are checked for symlinks; higher ancestors are not revalidated.
- Saving uses atomic 0600 replacement in a 0700 directory and rejects an existing symlink. Pat left LOW notes about the currently uncalled save API, duplicated theme application, remaining path-check TOCTOU, and missing fsync durability; they remain PRD-level review evidence.

## Task 7 — Raw-only and unknown-provider degradation

- Run-scoping required a narrow shared-record extension beyond the plan's single-file location: `EmergencyFailureObservation` now carries optional `created_at`, populated by the existing bounded reader rather than duplicating marker parsing in the TUI.
- Well-formed emergency evidence created before the selected run's start is stale. Equal/later timestamps are current; malformed evidence, missing timestamps, and unparseable timestamps fail loud as current because their age cannot be trusted.
- Timestamp comparison parses UTC instants rather than relying on lexical order. Pat left one LOW mixed-timezone-awareness crash note for PRD-level review.
- Unknown normalized events retain their generic observed provider and no lanes; raw evidence without normalization remains raw-only with unknown provider and no invented lanes.

## Task 8 — Python launch, attach, and resume lifecycle

- Interactive resume selects only an exact-root, uniquely live, active registry entry. No live entry plus an idle observation restarts once; any other ownership/observation combination fails closed.
- Resume passes `agent=None` to the launcher so the child resolves the configured/default agent through the normal foreground path. The viewer attaches only to the identity returned by the launch handshake.
- The child writes bounded launch evidence when the supervisor returns nonzero as well as when setup raises. After a successful handshake, the removed one-shot report is not recreated by a later child exit.
- Pat left LOW notes about retained report files after failed handshakes, weak configured-agent assertion precision, duplicate `FleetEntry` to `FleetRun` conversion, and the pause remaining cleared when an interactive restart fails.
- Pat's MEDIUM fix preserves established CLI codes for all currently normalized exception families while retaining `RUNTIME_FORMAT` conversion for otherwise-unknown pre-publication failures. The one allowed delta rerun still requested explicit state/resource regression tests, so the attempt is stamped `medium-retry:unfixed` for PRD-level review.
- The style fixer used the repository's 50-line function limit; the coordinator confirmed the final style and split-hygiene gates are clean.

## Task 9 — Textual-to-plain fallback

- Terminal state is captured/restored for both the project viewer and root-free fleet chooser because both can fail after Textual has altered the terminal.
- Restoration uses `TCSAFLUSH`; discarding pending input is accepted so stale keystrokes from the failed Textual session cannot drive the plain fallback.
- Pat left LOW notes about duplicated terminal-error plumbing, the deliberate input flush, and the PTY test simulating the post-mount failure boundary rather than driving a full real Textual mount.

## Task 10 — Terminal lifecycle and neutrality integration tests

- The macOS PTY suite gives only the Textual-fallback subprocess a controlling terminal; macOS revokes a controlling terminal when its session leader exits, while the other tests need Ctrl-C delivered as a Textual key binding rather than SIGINT.
- The fake agent emits Claude stream-JSON under the configured `claude` agent because the current production driver registry accepts that provider; provider identifiers remain confined to tests.
- Pause/resume scenarios treat `request_pause` as boundary-applied behavior and verify that assumption against the live supervisor.
- The no-Bash proof is behavioral: legacy-launcher shims on `PATH` fail and record any invocation, while the live supervisor argv is asserted as direct Python/module execution. No static `shell=False` source scan was added.

## Final verification regression cycle 1 — Task 8

- `launch` is used as the stable genuinely unsupported command in the package-baseline parser test; bare `run` is now valid by design.
- The state-protocol command inventory changed only in its generated block: `run` now has optional `--no-tui`, and `attach [--run-id ID]` is present.

## Final verification regression cycle 2 — Task 8

- The installed pause/resume test retains its historical `invalid_run` function name solely because the migration parity matrix references that exact proof node; its body no longer claims bare `run` is invalid.

## 11: [D1] Connect live telemetry and preserve truthful evidence (L)

- Coordinator pinned the additive capability fields as `session_id: str | None` and `evidence_path: Path | None`, defaulting to `None`; the path names the attempt's session directory under the configured runtime root.
- Preserved the shared evidence API's three regular-file presence flags, including empty artifacts. An additive defaulted `raw_only` content flag distinguishes nonempty raw output from empty or absent normalized evidence using the same no-follow observations.
- Tess and Ivan reported no remaining assumptions. Devon's eight exploits were rejected after one strengthening round. Pat resolved all eight task findings with no new findings.
- Subsequent coordinator inspection found a real-adapter identity mismatch that the generic test driver did not expose: provider run/session IDs differ from the supervisor-owned identities now required by the observer. The initial Pat verdict is retained as evidence, but task 11 needs a sequential repair before phase completion; see the cycle-1 rework report.

## 12: [D1] Preserve terminal run observations after cleanup (L)

- Coordinator pinned additive `ProjectView.ended: bool = False`, terminal `stopped` distinct from live `stopping`, and terminal attach results: completed→completed/0, paused or stopped→detached/0, halted/attention/state-write-failed/unknown→failed/1. Live pause/attention stays attached.
- Missing/symlink final-state diagnostics use semantic cause matching with state/final-evidence context rather than exact message prose. Capability raw evidence must retain the exact attempt-specific diagnostic line while allowing the existing appended execution record.
- The final-state fixture pins `next_phase` to the committed empty string; Pat flagged the prior None normalization change as LOW. Other LOW notes cover status-mapping placement, poll decomposition, and lazy import/re-exports after the mandated style split.
- Tess and Ivan reported no further assumptions. The 36-case suite passes, but Pat and coordinator source inspection confirm unresolved same-batch replacement attribution and observer-lock interference. Task12 aborted before its repair dispatch because the full prompt remained50,185 bytes after the one permitted trim. Full raw Pat verdicts and unfinished task descriptions are retained in the cycle-1 recovery snapshot.

## Recovery task 1 — Real adapter identity

- Ivan: supplying `session_id` to `RawFirstDecoder` means the caller owns both canonical run and session identity; omitting it preserves standalone provider-derived identities.
- Tess: the real decoder regression normalizes optional `tool_uses` to zero only in the final summary override. It proves live decoding, persistence and projection, not independent real-adapter summary publication. Fresh completion review must retain this limitation.
- The committed regression exposed normalized description projection as a separate prerequisite, completed under recovery task 13 without weakening the test. All six cases now pass.
- Pat resolved C11/F01/F19. His LOW suggestion to remove `_bind_identity` is rejected by inspection: the standalone decoder learns `_session_id` from observations, so testing that mutable field would start rebinding later records and change existing behavior. His LOW summary-coverage note remains open for fresh review.

## 2: Exact selected-run ownership

- A single latest-owner runtime receipt is sufficient; superseded viewers retain their own cached frame plus a gap, without recovering historical final states.
- Final-state evidence requires a safe current state read. The receipt is advisory observation evidence, never lifecycle authority. Missing/invalid receipts do not prove a new final frame.
- Remaining race coverage gaps are recorded in repair-task-2.md; prior test-author budgets were not reset.

## 7: Quick completion and launcher diagnostics

- Tess permits diagnostic newline separators while rejecting other Unicode Cc controls.
- The parent-created, explicitly inherited private report descriptor authorizes diagnostics before child configuration resolves. Environment-only path destinations still require resolved-runtime containment.
- Coordinator recorded `LaunchedSupervisor.run: FleetRun | None` for verified successful completion from the new child, and authorized `MissingRunError(ValueError)` solely to distinguish missing selection from other viewer errors. These are implementation contract decisions, not operator-selected choices.
- The first Pat F35 closure was rejected after source inspection exposed the still-starting-child branch. A deterministic added test failed, the narrow fix passed all30 cases, and the resumed reviewer closed both orderings.
- Completion is evaluated after the shared observation context exits because exit-time revalidation can invalidate its state. Pat's suggestion to evaluate earlier was rejected on that evidence.
- Final formatter checks remain mandatory; preserve the style limit after any formatter correction. Remaining LOW notes and precise test coverage limits are retained in repair-task-7.md.

## Recovery task 10 — Viewer fallback and EOF

- Tess treats 120.0001 seconds as below the displayed precision of 120.0; identical rendered text must not create another frame. Pipe-writer closure and PTY VEOF demonstrate actual EOF.
- A fallback notice is identified across stdout and stderr without pinning its stream. The runtime-failure harness uses a real Textual test session, a real observer read, and an actual terminal flag change.
- Delegated calls to the observer's idempotent close method may occur more than once; fallback must start after the active UI read finishes and before the first close. Earlier nonexistent `.closed` assertions and the fleet test double's missing return were corrected without changing product expectations.
- Ivan consumes non-EOF plain-viewer input and continues observation. Ordinary Exception failures enter UI fallback; KeyboardInterrupt and SystemExit retain process-control semantics.
- Pat closed F12/F13/F26. LOW import ordering is left to the mandatory final formatter/lint gate; plain monochrome output and visible-duration-driven updates remain accepted within this task. EOF detach applies to the viewer; foreground no-TUI execution is the supervisor path, not this viewer.
- Four total Tess dispatches were used: initial, two pre-commit quality retries, and a post-implementation correction of proven harness errors with stronger import coverage. No Devon ran at the sonnet tier. Final narrow verification passed all14 cases.

## Recovery task 12 — Operator documentation

- Ivan regenerated the tracked reference by capturing the existing renderer's exact output and applying that output to the artifact. Main equality tests confirm the generated document is current.
- The selected-run stop description follows the real confirmation dialog and selected identity. Coordinator clarified launch-versus-attach help, explicit run-ID selection, noninteractive/JSON behavior, and empty-XDG handling from the delivered code.
- This task changes documentation and help strings only. Existing parser/reference tests replace new prose-pinning tests; a per-task review is retained to close the rework findings.


## Recovery task 14 — Unknown final usage

- No test-author or implementor assumptions. The real-adapter summary workaround is removed and all131focused cases pass; this supersedes recovery task1's summary-publication limitation.
- Mandatory single Devon strengthening added regression assertions for eight proven mutations in a separate test commit. Pat's LOW scope notes are retained in repair-task-14.md; no production scope expansion.


## Final verification repair cycle 1 — Task 6

- Ivan: the explicit seam-repair contract authorizes the narrow behavioral updates to the three allowlisted test files despite the generic implementor preamble saying tests are the spec. This is the source final-regression procedure applied to the accepted lazy-viewer and explicit JSON opt-in changes; original ownership and foreground PID assertions remain.
