# OVCAQ external plugin provisioning

## Three-layer requirements — 2026-10-25

This PRD remains held. [Architecture authority](../../designs/autopilot-optional-supervision.md) supersedes older ownership/packaging wording below: workflow state/lifecycle/lanes/review/records belong to Autopilot's controller; session/process/collaboration and operations API to OVCAQ; TUI presentation to Tower. All historical state-command criteria below are satisfied through that controller; all TUI criteria through the separate API client. Every original source task/acceptance ID remains required under the reconciled coverage manifest.

Before provisioning readiness require AP00017/00021 and OV00057–00060/00064 compatibility evidence. Reconcile one external portable Autopilot package and tested client catalogs, with canonical controller protocol/version/digest pins. OVCAQ never bundles controller, skills or Tower. Tower is separately installed only when explicitly requested; core remains usable without it. Preserve agoge source/range and required drain behavior.

## Overview

### Source Contract

Implements Phase 8 source tasks `P08-T01`–`P08-T11` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

OVCAQ depends on launcher-native workflow and post-drain capabilities but must
not vendor or hand-edit them. Fresh Claude and Codex setups need declarative,
dry-run-first reconciliation, compatible external releases, version pinning,
and real smoke evidence before personal cutover.

### Target User

The operator needs one check/apply workflow with concrete remediation; the
supervisor needs verified, pinned workflow and agoge capabilities.

### Success Metrics

- Fresh supported launcher setup reaches ready state from one explicit apply.
- A second apply is a no-op; check mode never mutates.
- Real Codex commits one OVCAQ state handoff after provisioning.
- Isolated agoge smoke succeeds for both launchers.
- The wheel contains requirement identifiers but no plugin/skill/agent content.

## Preconditions and Boundaries

- Depends on completed PRDs 00002–00009.
- Core owns manifest, reconciliation, pinning, drift, and generic capability
  lifecycle; external marketplaces own implementation content.
- OVCAQ never installs launcher binaries, authenticates users, bypasses policy,
  edits config/cache directly, or silently applies changes from `run`.
- External repository changes are required deliverables of this PRD and must be
  independently versioned/released before smoke completion.
- Before external work begins, link a bounded implementation record in each
  companion repository with target version, tests, release evidence, and owner.
- Real `--apply` and companion publication require explicit approval after their
  dry-run plan identifies exact launcher-global and repository targets.

## Functional Decomposition

### Capability: Declarative Requirements

#### Feature: Versioned manifest

Ship launcher, marketplace name/source, plugin, compatible version range,
capability identifier, required flag, and failure policy for Claude/Codex
capability identifiers workflow.autopilot and post_drain.agoge. Personal-cutover
overrides cannot make agoge optional. Workflow content comes from the tested
client catalogs for buvis/agent-plugins/plugins/autopilot; pin its exact tested
package version and controller schema/fixture digests. The historical workflow
range >=1,<2 is superseded, not evidence of controller compatibility. Preserve
agoge marketplace buvis-plugins, sources buvis/claude-plugins and
buvis/codex-plugins, and range >=0.1,<1 under the existing approved plan.

#### Feature: Batch resolution and pinning

Resolve installed versions at batch start, persist provider-neutral tuples, and
refuse new phases after unexpected drift unless the operator explicitly refreshes
the pin. Pin required/failure behavior with the version. Pin every resolved
required tuple: workflow, agoge, and any separately declared enforcement plugin.
The initial manifest's enforcement hooks travel inside the workflow plugin, so
this does not invent an undeclared fifth requirement.

### Capability: Safe Reconciliation

#### Feature: Generic plan and report

Represent current state, required state, ordered actions, drift, postconditions,
manual remediation, and machine-readable output. `--check` is read-only;
`--apply` is explicit and idempotent.

#### Feature: Launcher adapters

Use supported structured Claude marketplace list/add/update/install/check and
Codex marketplace list/add/upgrade/add/check commands. Re-list and verify every
postcondition, including plugin/skill visibility where supported; never
shell-evaluate configured sources or selectors.

### Capability: CLI and Runtime Integration

#### Feature: Provision and doctor

Implement `ovcaq provision --agent NAME --check|--apply`; integrate binary/auth,
marketplace, plugin, capability, path, lock, and version diagnostics into doctor.
Binary lookup follows PATH first and emits the project's documented `mise which`
guidance when resolution fails.

#### Feature: Run preflight and drift enforcement

`run` performs check only and refuses missing/incompatible content with the exact
apply/remediation command. Mid-batch drift produces actionable attention.

### Capability: External Content and Real Smokes

#### Feature: Companion plugins

Coordinate compatible `ovcaq-autopilot` and `agoge` releases in
`buvis/claude-plugins` and `buvis/codex-plugins`. Both expose the same OVCAQ CLI/
state protocol while retaining launcher-native instructions and manifests. Each
workflow plugin forbids direct state edits, reads through `ovcaq state`, uses
compound task/outcome commands, calls `workflow phase-complete` exactly once,
exits after handoff, and stops after two failed state-write attempts.

The OVCAQ PRD remains the integration closeout owner, but it cannot infer either
companion repository's completion: it links their reviewed commits, CI, versions,
published artifacts, and visibility evidence.

#### Feature: Provisioned execution proof

After explicit local apply, run one real Codex smoke phase that commits through
OVCAQ and one isolated agoge smoke per launcher, retaining raw evidence with
user-only permissions.

## Structural Decomposition

```text
src/ovcaq/
  provision/{__init__.py,manifest.py,reconcile.py,claude.py,codex.py}
  resources/extensions.toml
  runtime/capability.py
  cli.py
tests/provision/
tests/fixtures/provision/{claude,codex}/
docs/operations.md
external: buvis/claude-plugins, buvis/codex-plugins
```

## Dependency Graph

```text
requirement manifest -> generic reconciliation -> launcher adapters -> CLI/doctor
                    -> batch pinning/drift -> run preflight
external releases + explicit apply -> real Codex/agoge smokes -> cutover readiness
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Manifest, Plans, and Pinning

- [ ] Finalize requirement schema/version constraints and packaged resource.
- [ ] Implement plan/report types and batch pin/drift services.
- [ ] Cover absent/incompatible/overridden/required capability cases.

**Exit Criteria**: Provider-neutral requirements and drift produce deterministic
machine-readable results.

### Phase B: Launcher Reconciliation and CLI

- [ ] Implement Claude and Codex supported-command adapters.
- [ ] Implement check/apply, postcondition verification, doctor, and run preflight.
- [ ] Test fake CLIs, partial failure, exact commands, and second-apply no-op.

**Exit Criteria**: Check never mutates; apply is explicit/idempotent/actionable.

### Phase C: External Releases and Real Proof

- [ ] Create/link and complete bounded work records in both companion repositories.
- [ ] Release compatible workflow/agoge plugins in both external marketplaces.
- [ ] Apply provisioning explicitly and record resolved versions.
- [ ] Run real Codex state-handoff smoke and isolated agoge smoke per launcher.
- [ ] Inspect wheel to prove external content is absent.

**Exit Criteria**: Both launchers are provisioned, pinned, and smoke-proven.

## Test Strategy

- Marketplace absent/present/stale and plugin absent/disabled/wrong version.
- Check immutability; exact apply commands; second apply no-op.
- Partial failure and remaining-drift remediation.
- Unsupported launcher capability yields manual action, never direct config/cache
  edits.
- Required agoge absent/incompatible and override cannot disable requirement.
- Batch pin, explicit refresh, mid-batch drift, and attention outcomes.
- Fake launcher JSON plus user-only real Codex/agoge smoke evidence.
- Distribution inspection for identifiers-only packaging.

## Risks

- **User-global mutation**: Check by default and require explicit apply.
- **CLI drift**: Use structured outputs, fixture provenance, and postconditions.
- **Core/content coupling**: Share only versioned identifiers and CLI protocol.
- **Cross-repo skew**: Release compatible external versions before real smokes.

## Acceptance Criteria

- [ ] One explicit apply readies each fresh launcher; second apply is a no-op.
- [ ] Doctor/run report exact drift and remediation without silent mutation.
- [ ] Workflow and agoge versions are resolved, pinned, and drift-enforced.
- [ ] External Claude/Codex plugin releases implement the same OVCAQ contract.
- [ ] Both companion work records link reviewed commits, CI, versions, release
  artifacts, and marketplace visibility.
- [ ] Approval records identify the exact external publications and real
  launcher-global apply plans that were authorized.
- [ ] Real Codex handoff and both agoge smokes pass with retained evidence.
- [ ] Wheel contains metadata only, never external content.
- [ ] PRD 00011 can run both complete canaries.

## Unresolved Questions

None.
