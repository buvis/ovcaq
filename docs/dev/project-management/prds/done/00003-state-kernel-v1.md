# OVCAQ state kernel

Status: backlog | Version: 1 | Umbrella phase: 1 | Created: 2026-08-23

## Overview

### Source Contract

Implements Phase 1 source tasks `P01-T01`–`P01-T12` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

OVCAQ cannot move workflow or runtime callers until it owns one installed,
validated, crash-safe state writer. The current implementation is proven but
uses the legacy schema and personal-skill packaging.

### Target User

The repository owner and later OVCAQ services need a deterministic state API and
CLI that remains correct under concurrent processes, invalid input, and process
failure.

### Success Metrics

- Every durable `state.json` mutation goes through `StateStore.transaction()`.
- Full nested v1 validation rejects malformed and future-schema state before a
  mutator runs.
- Failed mutations leave state and backup byte-identical.
- Concurrent and kill/failpoint tests show no lost or partially published write.
- Installed `ovcaq state` works outside the checkout.

## Preconditions and Boundaries

- Depends on completed PRD 00002 package, inventory, fixture, and packaging gates.
- The PRD 00002 field inventory is the source set for the v1 schema crosswalk.
- No workflow transition, runtime supervision, provider, TUI, or provisioning
  policy belongs here.
- Fresh OVCAQ state is authoritative; no legacy-state importer or dual writer.

## Functional Decomposition

### Capability: Versioned State Schema

#### Feature: Clean v1 model and crosswalk

Define every `batch`, `work`, `tasks`, `review`, `control`, and `recovery` field,
including nested task, attempt, capability, decision, and doubt entries. Map each
legacy field to retained, renamed, derived, event-only, or retired.

#### Feature: Total validation

Validate the complete object and cross-field invariants. Refuse non-object,
corrupt, missing-version, and future-version input before mutation.

### Capability: Transactional Persistence

#### Feature: Sole locked transaction

Hold an exclusive advisory lock across read, optional revision comparison,
deep-copy mutation, validation, revision increment, backup publication, state
publication, and directory fsync.

#### Feature: Recovery primitives

Provide create-only initialization, validated restore from one rotating raw-byte
backup, and fail-closed reads. Unsupported directory fsync must be capability-
gated explicitly rather than silently weakening supported platforms.

### Capability: State Command Boundary

#### Feature: Compound domain mutations

Implement task add/start/attempt/complete/body/meta/status/clear and contract-card
operations with task-ID resolution and derived counts updated atomically.

#### Feature: Recovery mutations and output contract

Provide show, validate, get, set, append, delete, and restore. Generic mutations
of transition-owned paths require explicit `--unsafe`; normal skills never use
it. Project-level `ovcaq init` uses the same create-only store. Machine output
and symbolic JSON errors remain stable and stdout-safe. Initialization creates
the project configuration/runtime directories and fresh state without importing
or overwriting a legacy tree.

## Structural Decomposition

```text
src/ovcaq/
  cli.py
  state/
    __init__.py
    schema.py
    store.py
    paths.py
    commands.py
docs/state-protocol.md
tests/state/
  test_schema.py
  test_store.py
  test_durability.py
  test_commands.py
  test_installed_state.py
```

- `schema.py`: v1 types, defaults, deep validation, future-version refusal.
- `store.py`: locks, transactions, atomic publication, backup, init, restore.
- `paths.py`: generic JSON-path parsing only; no workflow ownership decisions.
- `commands.py`: state application service and compound state verbs.
- `cli.py`: parser registration and shared output/error handling.

## Dependency Graph

```text
PRD 00002 contracts -> schema -> store -> state commands -> installed CLI
                               -> durability tests
schema + PRD 00002 field inventory -> state protocol documentation
```

`state` imports no workflow, runtime, driver, event, TUI, or provision module.

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Schema Contract

- [ ] Define the field crosswalk and documented clean v1 schema.
- [ ] Implement complete nested and cross-field validation.
- [ ] Port schema fixtures/tests and add unknown-future-version coverage.

**Exit Criteria**: Every documented nested owner validates; all inventory fields
have one disposition.

### Phase B: Transaction Store

- [ ] Port load, exclusive init, transaction, backup, and restore behavior.
- [ ] Add monotonic revision and optional compare-and-set.
- [ ] Add same-directory atomic replacement plus file and directory fsync.
- [ ] Test concurrent writers and kill/failpoints at every durable boundary.

**Exit Criteria**: No tested failure publishes invalid/partial state or loses a
committed update.

### Phase C: Installed State CLI

- [ ] Port generic JSON-path recovery operations.
- [ ] Port compound task and contract-card operations.
- [ ] Register project `init` and the complete accepted `state` command family.
- [ ] Enforce transition-owned path protection and `--unsafe` escape hatch.
- [ ] Generate help/docs from the live parser and test installed execution.
- [ ] Port every current state/statectl characterization test without a shim,
  checkout-relative import, or `sys.path` bootstrap.

**Exit Criteria**: Every state write uses the store and installed commands pass
outside the checkout.

## Test Strategy

- Missing, corrupt, non-object, shallow-invalid, and future-schema state.
- Mutator/validator exceptions preserve current and backup bytes.
- Two-process contention, revision conflicts, and no lost updates.
- Kill/failpoints before and after every backup/state publication boundary.
- File/directory fsync calls through injected functions.
- Create-only init, validated restore, negative indices, and invalid JSON paths.
- Compound task counts, task-ID resolution, permissions, JSON errors, and help.

## Risks

- **Schema omission**: Enforce exact equality with PRD 00002's field inventory.
- **False durability**: Use real multi-process/kill tests in addition to mocks.
- **Ownership leakage**: Keep transition effects out of generic state commands.
- **Unsafe recovery use**: Require explicit `--unsafe` and exclude it from
  normal workflow documentation.

## Acceptance Criteria

- [ ] All state writes flow through one store.
- [ ] Full v1 schema and crosswalk are documented and machine-tested.
- [ ] Failed mutations preserve state and backup bytes.
- [ ] Concurrency and durability suites pass on supported macOS.
- [ ] Installed `ovcaq state` passes from an arbitrary cwd.
- [ ] PRD 00004 can consume state services without a compatibility shim.

## Unresolved Questions

None.
