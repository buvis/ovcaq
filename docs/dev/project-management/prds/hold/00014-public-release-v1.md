# OVCAQ first public release

## Three-layer requirements — 2026-10-25

This PRD remains held. [Architecture authority](../../designs/autopilot-optional-supervision.md) supersedes older ownership/packaging wording below: workflow state/lifecycle/lanes/review/records belong to Autopilot's controller; session/process/collaboration and operations API to OVCAQ; TUI presentation to Tower. All historical state-command criteria below are satisfied through that controller; all TUI criteria through the separate API client. Every original source task/acceptance ID remains required under the reconciled coverage manifest.

Release closeout requires independently versioned Autopilot/controller, OVCAQ controller-client/operations protocols and optional Tower compatibility evidence. Verify OV00065 headless wheel and Tower00003 parity, exact producer digests and installed canaries. Existing security/artifact/publication approvals remain; no implicit publication of any new package.

Completeness correction (2026-10-25): consume AP 00012's frozen source inventory and behavior/regression map, with exact replacement artifact digests and passed evidence for every promised profile. Missing or unavailable evidence is not parity. Require AP 00017's real Codex + Gemini standalone and managed Claude-free certificates, including OV 00059/00060 attribution and full lifecycle/continuation/drain evidence; mixed Codex-build/Claude-review alone cannot satisfy that claim. Document tested Gemini compatibility and authentication prerequisites alongside existing Claude/Codex support. Source package removal is owned by claude-autopilot held PRD 00370 and its exact approved target ledger; this PRD must not independently delete that package.

## Overview

### Source Contract

Implements Phase 12 source tasks `P12-T01`–`P12-T08` and every phase exit
criterion from the [accepted implementation plan](../../plans/implementation-plan.md).
The [coverage manifest](../implementation-plan-coverage.md) and [resolved shared
discovery 00001](../../discovery/00001-ovcaq-v1.md) are mandatory inputs.
Grouped wording below never waives or renumbers a source obligation.

### Problem Statement

Passing personal and Linux workflows is insufficient for a maintainable public
release without stable protocol promises, complete operator documentation,
architecture records, security review, reproducible artifacts, and compatible
external plugin versions.

### Target User

Solo developers need a clean install that can provision/run Claude or Codex on
supported macOS/Linux; extension authors need a stable conformance contract.

### Success Metrics

- Clean supported environments install, provision, and run either first-party
  launcher through a complete smoke.
- A sample third-party driver installs and passes the published conformance test.
- Versioned state/CLI/driver/event docs exactly match executable tests.
- Full quality/security/package matrices pass before tag/publication.
- Published artifacts contain no personal data, paths, transcripts, or plugins.

## Preconditions and Boundaries

- Depends on completed and reviewed PRDs 00002–00013.
- Uses `dev/local/prds/implementation-plan-coverage.md` as the mandatory
  Phase 0–12 closeout checklist; every row needs durable evidence.
- Personal migration remains complete; release work does not restore old aliases,
  dual writers, or bundled launcher content.
- Compatibility guarantees begin with this release; no importer is retroactively
  required for the pre-stability fresh-state cutover.
- Publication is an explicit external action after all immutable artifact checks
  and separate approval of the exact commit, version, artifact checksums,
  marketplace pairings, package index, and tag destination.

## Functional Decomposition

### Capability: Stable Public Contracts

#### Feature: Protocol and compatibility policy

Finalize versioned state, CLI, driver, and event documents; define supported
change classes, future-version refusal, deprecation/migration rules, and the
first guarantees applying after the fresh-state personal cutover.

#### Feature: Architecture decision records

Record state authority, state-over-prose decisions, adapter seam, raw evidence,
external plugin boundary, shell-free argv, and supported-platform rationale.

### Capability: Operator and Extension Documentation

#### Feature: Complete operator path

Document install/init, configuration precedence, provisioning, run/attach,
pause/resume/stop, logs/purge, doctor, capabilities, failure recovery,
troubleshooting, retention/security, and platform boundaries from live commands.

#### Feature: Extension path

Document minimum loop versus rich telemetry capability, entry points, sample
driver, conformance command, compatibility/version negotiation, and unknown data.

### Capability: Release Assurance

#### Feature: Quality and security matrices

Run lint, format, type, unit, integration, macOS/Linux, launcher, provisioning,
extension, clean-install, and packaging gates. Review subprocess argv/env,
config/path containment, locks/signals, raw/normalized logs, permissions,
redaction, purge, plugin mutation, and secret exposure.

#### Feature: Reproducible artifact audit

Build sdist/wheel once, inspect contents/metadata/license/version/resources,
install those exact artifacts in clean environments, and retain checksums/results.

### Capability: Coordinated Publication

#### Feature: Core and marketplace release pairing

Declare minimum compatible Claude/Codex workflow and agoge plugin versions,
verify marketplace visibility, and document the pairing with the core release.

#### Feature: Tag and publish

After all gates pass, present an immutable release-authorization record. Only
after explicit approval create the release tag and publish those exact artifacts
to the named public Python package index. Post-publication, install by public
name and repeat help/doctor/provision smoke without checkout dependencies.

## Structural Decomposition

```text
docs/
  operations.md
  state-protocol.md
  driver-protocol.md
  provisioning.md
  troubleshooting.md
  platforms.md
  adr/*.md
pyproject.toml
.github/workflows/ci.yml
tests/{contracts,integration,packaging,security}/
external marketplace release metadata
```

Command documentation is generated/verified from the live parser; protocol docs
are executable contracts, not independent prose inventories.

## Dependency Graph

```text
PRDs 00002–00013 evidence -> stable contracts/docs/ADRs
stable contracts + full matrices + security review -> immutable artifacts
verified artifacts + compatible marketplace releases -> tag/publish/public smoke
```

## Implementation Phases

Task acceptance: each task pairs with its named `Pxx-Tyy` source task(s) in the
accepted plan; the source text plus the owning phase's exit criteria are that
task's acceptance criteria, and planning copies both verbatim.

### Phase A: Contracts and Documentation

- [ ] Complete operator, protocol, provisioning, troubleshooting, and platform docs.
- [ ] Declare state/CLI and extension compatibility/migration policies.
- [ ] Add required ADRs and parser/docs/protocol contract tests.

**Exit Criteria**: Documentation and executable behavior have one tested truth.

### Phase B: Release Candidate Assurance

- [ ] Run full quality/platform/launcher/extension/packaging matrices.
- [ ] Complete the security review and resolve all release-blocking findings.
- [ ] Build once, audit sdist/wheel, record checksums, and clean-install artifacts.
- [ ] Verify paired external plugin minimum versions and visibility.

**Exit Criteria**: One immutable release candidate passes every gate.

### Phase C: Publication and Independent Smoke

- [ ] Obtain explicit approval for the immutable release-authorization record.
- [ ] Tag the verified commit and publish the verified artifacts.
- [ ] Install by public package name on supported macOS/Linux environments.
- [ ] Re-run help/doctor/provision/first-party and sample-driver smoke paths.
- [ ] Publish release-to-plugin compatibility documentation.

**Exit Criteria**: Public installation reproduces tested supported behavior.

## Test Strategy

- Docs/parser/protocol examples and compatibility/version refusal/migration cases.
- Full lint/format/type/unit/integration matrices on macOS/Linux.
- Claude/Codex provisioning/run smokes and third-party driver conformance.
- Security review cases for shell injection, paths, symlinks, permissions,
  secrets/redaction, retention/purge, process identity, and launcher mutation.
- Sdist/wheel allowlist and clean install from exact release candidate.
- Public-index install with no checkout, home fixture, or plugin content leakage.

## Risks

- **Docs drift**: Generate commands and execute protocol examples.
- **Artifact mismatch**: Build once and publish the exact audited files.
- **Compatibility overpromise**: State explicit versioned guarantees and tests.
- **External release skew**: Gate publication on visible compatible plugin versions.
- **Sensitive release content**: Allowlist artifacts and scan for personal data.

## Acceptance Criteria

- [ ] All PRDs 00002–00013 and full-plan coverage evidence are complete.
- [ ] Stable state/CLI/driver/event policies and docs match tests.
- [ ] Quality, security, platform, launcher, extension, and packaging gates pass.
- [ ] Clean macOS/Linux installs provision/run both first-party launchers.
- [ ] Installed sample third-party driver passes published conformance.
- [ ] Published artifacts contain no personal/plugin/transcript/state content.
- [ ] Public package and marketplace compatibility documentation is live.
- [ ] The authorization record matches the published commit, version, tag,
  checksums, package-index destination, and marketplace pairings exactly.
- [ ] `uv tool install ovcaq` from the public index provides the verified command.
- [ ] Every Phase 0–12 obligation in the accepted implementation plan is closed.
- [ ] Evidence maps all 119 P00–P12 task IDs, 23 M01–M23 migration IDs and
  15 A01–A15 acceptance IDs, with no missing, duplicate or waived row.

## Unresolved Questions

None.
