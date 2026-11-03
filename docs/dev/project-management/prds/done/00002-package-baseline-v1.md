# OVCAQ package and contract baseline

Status: backlog | Version: 1 | Umbrella phase: 0 | Created: 2026-08-22

## Overview

### Problem Statement

OVCAQ has an accepted architecture but no installable package, tracked contract
inventory, or reproducible baseline for the personal runtime being extracted.
Moving behavior before those exist would make omissions and accidental redesigns
hard to detect.

### Target User

The repository owner needs a clean Python package skeleton and a complete,
machine-checked map from the current personal implementation to later OVCAQ
phases.

### Source Contract

Implements Phase 0 source tasks `P00-T01`–`P00-T08` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.
`AGENTS.md` remains binding; the live personal runtime is characterization-only.

### Success Metrics

- Required sync, lint, format, type, test, build, and clean-wheel checks pass.
- Every current command, state field, loop decision, environment knob, shell
  behavior, tracon behavior, and test has one destination or retirement reason.
- No test or fixture reads live personal state or launcher directories.
- Built artifacts contain no plugin content, personal paths, or copied runtime.

## Scope

### In Scope

- Python 3.12+ package/lock/CI/MIT/release skeleton; empty boundaries and help.
- Sanitized fixtures, inventories/mappings, baselines, packaging/import gates,
  and a reviewed downstream-PRD reconciliation record.

### Out of Scope

Production behavior, compatibility shims/aliases, launcher content or mutation,
package publication, and personal cutover.

## Functional Decomposition

### Capability: Installable Package Baseline

#### Feature: Reproducible toolchain

`pyproject.toml`, `uv.lock`, a PEP 440 development version, Textual/Rich runtime
dependencies, and pytest/ruff/mypy groups make the documented verification
commands reproducible.

#### Feature: Installed command smoke surface

The wheel exposes `ovcaq` and `python -m ovcaq`; `--help` succeeds outside the
checkout. No product command performs work in this PRD.

#### Feature: Package boundary skeleton

The accepted `state`, `workflow`, `runtime`, `drivers`, `events`, `tui`, and
`provision` packages import but contain no copied production logic.

### Capability: Characterization Evidence

#### Feature: Frozen source inventory and migration manifest

Stable IDs enumerate current behavior and artifacts. Each ID has exactly one
later-phase destination or explicit retirement with rationale and a
characterization-test reference. Tests reject missing, duplicate, or unknown
mappings. After characterization, reconcile PRDs 00003–00014 and the coverage
manifest against the evidence; record every reviewed delta or an explicit
no-change result in `dev/local/audit-results/phase-0-reconciliation.md`
(audit-results is the curated home; the 2026-08-23 layout hook blocks files
directly in `prds/`).
The inventory must explicitly disposition the easy-to-miss rows: the
`_autopilot_fable_*` shell helpers, `fablectl.py` with the
`ledger/fable-requests.json` request budget, the drained-path `purge-devlocal`
script invocation in `loop.py`, `notify_out` notifications, the
`render_stream.py` presenter fallback chain, and the hook split
(state-validation, review-coverage, context-cap) destined for external plugin
content.

#### Feature: Fixtures and baseline capture

Minimal sanitized fixtures record provenance. Baseline evidence records exact
commands, tool versions, pass/fail/skip totals, and known failures so later PRDs
need no live-home access.

### Capability: Packaging Gates

#### Feature: Clean-wheel validation

Install the wheel into an isolated environment and test help/import behavior
from an arbitrary cwd containing a decoy `cli` package.

#### Feature: Distribution-content audit

Programmatically reject undeclared members, personal paths, live state, plugin
or skill content, transcripts, and caches in the sdist or wheel.

## Structural Decomposition

```text
pyproject.toml, uv.lock, LICENSE, .github/workflows/ci.yml
src/ovcaq/
  {__init__,__main__,cli,config,paths,errors}.py
  state/{__init__.py,schema.py,store.py,paths.py,commands.py}
  workflow/{__init__,transitions,selection,frontmatter,resume,policy,records,reports}.py
  runtime/{__init__,supervisor,decision,registry,process,watchdog,capability,session}.py
  drivers/{__init__.py,base.py,claude.py,codex.py,command.py}
  events/{__init__.py,model.py,reducer.py,tail.py}
  tui/{__init__.py,app.py,discovery.py,model.py,panels.py}
  provision/{__init__.py,manifest.py,reconcile.py,claude.py,codex.py}
  resources/extensions.toml
tests/
  characterization/{current_system.toml,migration.toml,test_migration_contract.py}
  fixtures/{README.md,claude/,codex/}
  {state,workflow,runtime,drivers,tui,provision}/
  packaging/{test_distribution.py,test_installed_cli.py}
docs/{baseline.md,state-protocol.md,driver-protocol.md,operations.md}
```

## Dependency Graph

```text
accepted plan + live sources -> inventory -> migration manifest -> contract tests
package metadata -> skeleton -> wheel -> packaging gates
fixtures + baseline evidence ------------------------^
```

This PRD has no implementation-PRD dependency. The state-kernel PRD depends on
its passing inventory, fixture, and packaging gates.

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Package Foundation

- [ ] Add package/build metadata, development version, dependencies, and entry
  points.
- [ ] Add the accepted package skeleton and help-only CLI.
- [ ] Add the MIT license and non-publishing CI/release skeleton.
- [ ] Add `CHANGELOG.md` with an `[Unreleased]` section so later feat/fix
  commits can update it in the same commit.
- [ ] Generate and commit `uv.lock`.

**Exit Criteria**: A wheel builds, installs, imports, and prints help outside the
checkout without loading current autopilot code.

### Phase B: Characterization Contracts

- [ ] Inventory every source surface named by the umbrella plan with stable IDs
  and provenance.
- [ ] Map every ID to one later phase or an explicit retirement.
- [ ] Copy only minimal sanitized fixtures and document provenance.
- [ ] Record existing suite commands, versions, results, skips, and failures.
- [ ] Enforce inventory/migration set equality and unique ownership in tests.
- [ ] Reconcile every downstream PRD/source-ID range against the characterized
  evidence and record reviewed deltas or no-change results.

**Exit Criteria**: Every current behavior is accounted for; retained evidence
requires no live personal directory; downstream contracts are reconciled.

### Phase C: Reproducibility and Distribution Gates

- [ ] Test arbitrary-cwd imports with a decoy `cli` package.
- [ ] Build and inspect sdist/wheel contents programmatically.
- [ ] Clean-install the wheel and smoke-test both entry points and boundaries.
- [ ] Run the documented verification set locally and in CI.

**Exit Criteria**: All checks pass; artifacts contain only declared skeleton,
metadata, and sanitized evidence.

## Test Strategy

- **Happy path**: Clean sync/build/install; arbitrary-cwd help/imports succeed.
- **Missing or duplicate mapping**: Contract test names the offending stable ID.
- **Import contamination**: A decoy `cli` does not change OVCAQ imports.
- **Artifact leak**: Content audit names the forbidden distribution member.
- **Live-home dependency**: Tests pass with personal paths unavailable.

### Required Verification

Run all six verification commands mandated by `AGENTS.md`: sync, pytest, ruff
check/format-check, mypy, and build.

## Risks

- **Inventory omission**: Derive inventory IDs separately from the mapping and
  enforce exact set equality.
- **Fixture leakage**: Minimize/sanitize fixtures and scan built artifacts.
- **Premature implementation**: Reject copied product behavior in this PRD.
- **False green baseline**: Preserve commands, versions, skips, and failures.

## Acceptance Criteria

- [ ] Umbrella Phase 0 exit criteria and all required checks pass.
- [ ] Inventory/migration coverage is total and unique.
- [ ] Baseline evidence is reproducible and names known failures.
- [ ] The Phase 0 reconciliation record covers PRDs 00003–00014 and the coverage
  manifest; no downstream implementation starts with an unexplained conflict.
- [ ] Distributions contain no copied runtime, plugin content, personal path,
  transcript, or live state.
- [ ] Phase 1 can proceed using committed fixtures and contracts only.

## Resolved Decisions

MIT is accepted for low-friction adoption; Apache-2.0's explicit patent grant is
not required for this project profile.

## Unresolved Questions

None.
