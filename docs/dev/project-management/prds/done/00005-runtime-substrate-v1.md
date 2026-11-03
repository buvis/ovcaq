# OVCAQ shared runtime substrate

Status: backlog | Version: 1 | Umbrella phase: 3 | Created: 2026-08-23

## Overview

### Source Contract

Implements Phase 3 source tasks `P03-T01`–`P03-T11` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

Process ownership, paths, duplicate-run detection, registry discovery, watchdog
behavior, and session evidence are currently split between Python, Bash, and the
TUI. OVCAQ needs one provider-neutral substrate before moving the loop or UI.

### Target User

The supervisor and TUI need shared liveness/session models; operators need safe
process control, diagnostics, and durable raw evidence.

### Success Metrics

- A second supervisor for the same project is refused by `run.lock`.
- TERM/KILL tests stop owned grandchildren and never signal unrelated processes.
- Atomic registry data survives detach and stale/recycled PID entries are pruned.
- Raw bytes are retained before decoding with user-only permissions.
- Normal completion removes only ephemeral entries and never expires evidence.

## Preconditions and Boundaries

- Depends on completed PRDs 00002–00004.
- Provides process/session effects but no post-session workflow decision loop.
- Registry metadata aids discovery; the per-project lock is duplicate authority.
- No provider-native argv/event parsing and no TUI-specific liveness algorithm.
- Environment variables are limited to secrets, tests, and launcher needs; the
  broad legacy `_AUTOPILOT_*` configuration surface is not reproduced.
- Personal-cutover support is macOS; Linux remains a later release gate.

## Functional Decomposition

### Capability: Project and Run Discovery

#### Feature: Configured paths and capability probes

Resolve project root, PRD/runtime roots, XDG configuration/state paths, and
supported platform capabilities without checkout-relative imports. Configured
project/runtime paths remain under the resolved project unless the operator
explicitly supplies an external state root. Precedence is CLI flags, tracked
project `ovcaq.toml`, `${XDG_CONFIG_HOME:-~/.config}/ovcaq/config.toml`, then
package defaults.

#### Feature: Single-run lock and fleet registry

Hold a non-blocking project lock for the run lifetime. Atomically publish root,
PID, process-start identity, run ID, agent, and time; prune malformed, stale, and
recycled-PID entries through one shared registry module.

### Capability: Owned Process Trees

#### Feature: Shell-free process groups

Spawn argv with `shell=False`, stdin closed, and a dedicated process group or
session. Own TERM, grace, KILL, exit status, and cleanup.

#### Feature: Watchdog and signals

Use an injectable clock, configurable grace period, and centralized
Ctrl-C/TERM/HUP handling. Report emergency state-write failure without launching
another agent.

### Capability: Session Evidence and Retention

#### Feature: Session lifecycle and raw tee

Create run/session metadata directories and write raw bytes before any decoder.
Retained artifacts use restrictive permissions and remain after detach/crash.
The default tree is `<repo>/dev/local/ovcaq`: state/lock/backup, run lock and
metadata, normalized events/metrics, per-session raw/meta/summary files, and
reports. Fleet entries live under `${XDG_STATE_HOME:-~/.local/state}/ovcaq/runs`.

#### Feature: Diagnostics and explicit purge

Inventory evidence size; make `status`/`doctor` show location and exact purge
preview. Purge previews by default, requires `--apply`, refuses active sessions,
and has no scheduled or implicit expiry path. `ovcaq logs [--session ID]`
locates/tails retained raw or normalized evidence; cutoff purge deletes only
the explicitly selected eligible sessions.

## Structural Decomposition

```text
src/ovcaq/
  config.py
  paths.py
  runtime/
    __init__.py
    registry.py
    process.py
    watchdog.py
    session.py
  cli.py
tests/runtime/
  test_paths.py
  test_registry.py
  test_process.py
  test_watchdog.py
  test_session.py
  test_retention.py
```

- `paths.py`/`config.py`: precedence, root discovery, runtime/XDG locations.
- `registry.py`: atomic fleet metadata and centralized stale detection.
- `process.py`: process-group creation, signals, and owned cleanup.
- `watchdog.py`: timeout clock and TERM-to-KILL escalation.
- `session.py`: metadata, raw tee, evidence inventory, explicit purge.

## Dependency Graph

```text
PRD 00003 state + PRD 00004 workflow
  -> paths/config -> run lock + registry
                  -> process + watchdog
                  -> session/raw evidence/retention
shared services   -> status/doctor/logs CLI
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Paths, Metadata, and Registry

- [ ] Implement configuration precedence and project/runtime discovery.
- [ ] Enforce project path containment and explicit external-root semantics.
- [ ] Implement project `run.lock`, atomic XDG registry, and stale pruning.
- [ ] Define run/session metadata and platform capability probes.

**Exit Criteria**: Duplicate runs are refused and fleet discovery survives
detach without treating registry PID alone as authority.

### Phase B: Process Ownership

- [ ] Implement shell-free process-group spawn and exit collection.
- [ ] Port watchdog with injectable time and TERM/KILL grace.
- [ ] Centralize supervisor-signal cleanup and emergency error reporting.
- [ ] Exercise child/grandchild and unrelated-process integration cases.
- [ ] Run supported macOS lock/signal/process integration coverage.

**Exit Criteria**: Owned trees terminate predictably; unrelated processes do not.

### Phase C: Evidence and Operator Diagnostics

- [ ] Implement raw session tee and restrictive artifact creation.
- [ ] Implement retained-log inventory and preview/apply purge.
- [ ] Add `status`, `doctor`, and `logs` substrate commands/projections.
- [ ] Prove no startup/completion/timer path deletes retained evidence.

**Exit Criteria**: Live metadata survives detach; completion removes only
ephemeral artifacts and retains evidence indefinitely.

## Test Strategy

- Duplicate lock acquisition and safe release after signal/crash.
- Atomic registry updates; malformed, stale, missing, and recycled PIDs.
- Path traversal, symlink escape, and explicit external-state-root cases.
- Real subprocess groups with grandchildren, TERM grace, KILL, and no collateral.
- Ctrl-C/TERM/HUP exit codes and cleanup.
- Raw byte preservation, partial writes, restrictive permissions, and detach.
- Purge preview/apply cutoff, active-run refusal, and absence of automatic expiry.
- Installed status/doctor/logs behavior outside the checkout.

## Risks

- **Process leak/collateral signal**: Test real groups and process identity.
- **Registry split brain**: Centralize discovery and keep lock authoritative.
- **Sensitive accumulation**: Restrictive permissions plus visible manual purge.
- **Platform assumptions**: Probe capabilities and fail with actionable doctor
  output on unsupported behavior.

## Acceptance Criteria

- [ ] Duplicate supervisors cannot start.
- [ ] Owned agent trees stop without touching unrelated processes.
- [ ] Registry and session metadata support detach/reattach consumers.
- [ ] Raw evidence is written first and retained indefinitely by default.
- [ ] Purge is explicit, preview-first, cutoff-scoped, and active-run-safe.
- [ ] PRD 00006 can build adapters/events without duplicating runtime ownership.

## Unresolved Questions

None.
