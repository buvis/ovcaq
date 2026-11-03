# Cycle 12 evidence

Reviewed HEAD: `39ecaf4f95c79df6a88c30e4626386a352d1505b`.
Full scope: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..39ecaf4f95c79df6a88c30e4626386a352d1505b`.
Repair delta: `22d9193a0d00486b09ebea169e7a38a9f858799d..39ecaf4f95c79df6a88c30e4626386a352d1505b`.

## Source reconciliation

The fresh [ownership join](00004-cycle-12-owned-rows.json) verifies ten distinct
P02-T01–T10 source tasks and all 55 unique owned characterization rows. It keeps
the source tasks and phase exits verbatim. The accepted source hashes match
`tests/characterization/migration.toml`:

- Plan: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
- Inventory: `d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9`.

The attached task snapshot initially had exactly ten completed tasks and valid
schema/counts. Its imported source tasks have no attempt history. The literal
Codex-rung predicate counts zero; that absence does not prove historical work
never used Codex. The explicit host substitution supplies external Claude Bob
as the independent provider voice.

## Verification

[Recorded commands and results](00004-cycle-12-verification.json): 1,348 tests
passed in 22.14 seconds, zero failed/skipped. Sync, Ruff, formatting (119 files),
mypy (51 source files), wheel/sdist build and full-range whitespace pass.

The first sandbox run had six Unix-socket permission failures and four build
fixture errors caused by denied build-dependency DNS. The authorized rerun
resolved them without source changes. The full-base replay helper executed
with a disposable Git worktree but could not collect because
`packaging_support` is absent at the base. This preserves R9-K4's narrower
evidence limit. Its temporary worktree was removed. The mechanical test-shape
check again found only the inherited R8-K1 collision-test OR assertion.

Build hashes match the incoming repair handoff:

- Wheel: `e085e2fba91ab171abe1dcb22693495040a238c9846dd83e93d0bfd9621c47f4`.
- Sdist: `8edde79fb888731194bc078b53ccdd5ce47c8ce3b641eb9d5f1b4763117f4c94`.

## R12-01: interrupted runtime ancestor confirmation

[Probe source](00004_cycle_12_crash_probe.py) and
[structured observations](00004-cycle-12-crash-probe.json) use the wheel
installed by this cycle's packaging fixture. Every product import resolves
under that environment's `site-packages`; each retry starts a new interpreter.
All child processes finish and temporary project roots are context-managed.

The actor exits with `os._exit(73)` immediately before a native parent fsync,
after the preceding `mkdir` has succeeded. This models an abrupt process exit,
so exception cleanup cannot remove the unconfirmed child directory.

| Interrupted parent fsync | Surviving directories | Fresh successful retry fsyncs | Exact successful replay fsyncs |
|---|---|---|---|
| project | new | new, runtime, deferred | runtime, deferred |
| new | new, new/nested | runtime, deferred | runtime, deferred |

Both retry and replay return exit 0 with empty stderr, unchanged authoritative
state bytes, unchanged replay ledger bytes and exactly one `crash-one` record.
Neither confirms the interrupted parent entry. `_ensure_directory_chain`
mistakes existence for durable confirmation because its only repair path is
the caught-OSError `rmdir`. These are observed syscall omissions and a resulting
data-loss risk; no physical power-loss test or observed data loss is claimed.

R11-01's prospective ledger depth validation and R11-02's serialized report
composition pass their installed regressions. R11-03's ordinary and caught-error
paths pass, but its abrupt-exit/restart obligation remains incomplete. Therefore
P02-T06/T09 and the all-durable-boundaries exit cannot be signed off without the
bounded repair, despite a green existing suite.

The [prepared follow-up](00004-cycle-12-followup.json) preserves this finding
verbatim and requires a chronological installed crash regression, bounded fix,
preservation checks and the required full gates. No product repair or completion
phase ran in this review session.
