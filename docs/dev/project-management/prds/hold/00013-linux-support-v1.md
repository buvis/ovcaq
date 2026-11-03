# OVCAQ Linux support

## Three-layer requirements — 2026-10-25

This PRD remains held. [Architecture authority](../../designs/autopilot-optional-supervision.md) supersedes older ownership/packaging wording below: workflow state/lifecycle/lanes/review/records belong to Autopilot's controller; session/process/collaboration and operations API to OVCAQ; TUI presentation to Lantern (working name). All historical state-command criteria below are satisfied through that controller; all TUI criteria through the separate API client. Every original source task/acceptance ID remains required under the reconciled coverage manifest.

Linux gates cover controller file/lock behavior, OVCAQ process identity/supervision/headless wheel and separate Lantern terminal/detach behavior independently. TTY/non-TTY and UI-crash canaries use public operations API. OVCAQ must install/run with Textual/Rich/Lantern absent; no bundled UI convenience dependency.

## Overview

### Source Contract

Implements Phase 11 source tasks `P11-T01`–`P11-T05` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

Personal cutover proves macOS only. A public OVCAQ package must demonstrate that
state durability, process ownership, XDG paths, terminal behavior, and both
first-party launchers work on explicitly supported Linux environments.

### Target User

Linux operators need the same provider-neutral state/runtime guarantees and
actionable diagnostics when a platform capability is unavailable.

### Success Metrics

- macOS and Linux pass the same state/runtime contract suites.
- Linux clean-wheel install, no-TUI, detach/attach, and XDG tests pass in CI.
- Claude and Codex supported Linux smoke tests pass.
- Unsupported capabilities fail in doctor with concrete remediation.
- Documentation names supported distributions and required system capabilities.

## Preconditions and Boundaries

- Depends on completed PRDs 00002–00012.
- Linux support is a public-release gate, not retroactive personal-cutover work.
- Windows remains unsupported and out of scope.
- Platform-specific code must sit behind small capability adapters/probes; shared
  workflow and decision policy remains unchanged.

## Functional Decomposition

### Capability: Cross-Platform Durability

#### Feature: Lock and publication semantics

Run advisory lock, concurrent transaction, file fsync, directory fsync,
replacement, backup, permissions, and kill/failpoint suites on supported Linux.
Capability-gate only behavior the platform genuinely cannot provide.

### Capability: Cross-Platform Process Ownership

#### Feature: Process groups and signals

Validate spawn/session ownership, watchdog TERM/grace/KILL, supervisor crash,
Ctrl-C/TERM/HUP, orphan prevention, recycled PID registry handling, and no
collateral signaling with real Linux subprocess trees.

#### Feature: Terminal lifecycle

Validate TTY/non-TTY launch, plain fallback, detach/reattach, TUI crash safety,
and no-TUI operation under supported terminal environments.

### Capability: Linux Paths and Launcher Support

#### Feature: XDG and project paths

Validate configuration/state/cache precedence, permissions, path containment,
runtime discovery, and fleet registry behavior under Linux XDG conventions.

#### Feature: First-party launcher smokes

Run supported Claude and Codex Linux smokes through provider-neutral state,
runtime, events, provisioning checks, and normalized/raw evidence paths.

### Capability: CI and Diagnostics

#### Feature: Platform matrix

Add Linux clean-environment wheel installation and state/runtime/integration
jobs while retaining macOS gates. Record platform/tool versions in artifacts.

#### Feature: Actionable capability doctor

Report unsupported filesystem, signal, terminal, launcher, or XDG behavior with
symbolic codes and remediation rather than late runtime failure.

## Structural Decomposition

```text
src/ovcaq/{paths.py,config.py}
src/ovcaq/runtime/{process.py,watchdog.py,registry.py,session.py}
src/ovcaq/tui/app.py
src/ovcaq/cli.py
tests/integration/{test_linux_state.py,test_linux_process.py,test_terminal.py}
.github/workflows/ci.yml
docs/{operations.md,platforms.md}
```

Platform conditionals remain localized; provider-neutral contracts stay shared.

## Dependency Graph

```text
existing macOS contracts -> Linux state/process/path/terminal matrix
Linux capability probes -> doctor and documented support boundary
Linux package install + first-party smokes -> public-release readiness
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Linux State and Runtime Contracts

- [ ] Run/fix lock, fsync, replacement, registry, watchdog, and signal suites.
- [ ] Localize or capability-gate remaining macOS-only behavior.
- [ ] Add real child/grandchild and failure-path coverage.

**Exit Criteria**: macOS and Linux pass identical provider-neutral guarantees.

### Phase B: Paths, Terminal, and Packaging

- [ ] Validate XDG paths, containment, permissions, fleet discovery, and cleanup.
- [ ] Validate TTY/no-TUI/detach/attach/plain fallback on Linux.
- [ ] Add clean-wheel Linux CI jobs and artifact/version capture.

**Exit Criteria**: Clean Linux install and operator lifecycle paths pass in CI.

### Phase C: Launchers, Doctor, and Docs

- [ ] Run supported Claude and Codex Linux smokes.
- [ ] Add actionable doctor failures for unsupported capabilities.
- [ ] Document supported distributions, terminals, filesystems, and prerequisites.

**Exit Criteria**: Both first-party launchers pass and support boundaries are clear.

## Test Strategy

- Linux lock contention, revision CAS, fsync, backup, kill/failpoints.
- Process-group grandchildren, supervisor crash, timeout, signals, collateral.
- Stale/recycled registry identities and XDG path/permission cases.
- TTY/non-TTY, attach/detach, TUI crash, and plain fallback.
- Clean wheel outside checkout and provider-neutral import scans.
- Claude/Codex smoke, missing launcher/capability, and doctor remediation.

## Risks

- **Distribution variance**: Declare supported targets and capability-probe.
- **CI-only confidence**: Use real subprocess/filesystem integration tests.
- **Platform branches spread**: Localize adapters and keep contracts common.
- **Launcher availability**: Separate supported smoke environments from unit CI.

## Acceptance Criteria

- [ ] macOS/Linux pass the same state/runtime contract suites.
- [ ] Linux clean install, XDG, terminal, attach, and no-TUI gates pass.
- [ ] Claude and Codex supported Linux smokes pass.
- [ ] Unsupported capabilities fail early with actionable doctor output.
- [ ] Supported distributions/system capabilities are documented.
- [ ] PRD 00014 can publish with macOS and Linux support claims.

## Unresolved Questions

None.
