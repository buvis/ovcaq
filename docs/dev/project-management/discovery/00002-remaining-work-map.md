# Discovery: Remaining work map

## Classification

Depth: standard | Date: 2026-10-19 | Status: open

## Problem

OVCAQ has a working core (state, workflow, runtime, events, Claude and Codex
adapters, TUI) but cannot yet drain a batch end to end, and it is public before
personal cutover. Remaining work is spread across five held phase PRDs, 39 hold
stubs, a readiness review, and drift in the legacy runtime. This doc is the
single map: what remains, where it is specified, and in what order.

## Requirements

### Must have, in order

1. **Public preview surface** (discovery 00008): honest README, changelog,
   metadata, no empty modules. Small, and the repo is already public.
2. **Workflow entry and lifecycle ownership** (discovery 00003): enter verb,
   verified bucket moves, transition guards, stall recovery, one state-file
   resolver. Blocks every real drain.
3. **Supervisor robustness** (discovery 00004): `ps`-free process identity,
   validate before starting a batch, failure classes, neutral tiers.
4. **End-to-end verification** (discovery 00006): fresh-`init` drains for both
   launchers, captured transcripts, macOS CI. Proves 2 and 3.
5. **Hold backlog** (discovery 00009): close 30 fixed stubs; fix the five live
   redaction, identity, and pinning defects.
6. **Operator experience** (discovery 00005): doctor, human output,
   `--version`, error wording, config docs.
7. **Legacy drift reconciliation** (discovery 00007): inventory and
   dispositions for about 11,000 lines added to the legacy runtime since
   2026-08-25. Must finish before cutover.
8. **Plugin provisioning** (PRD 00010, held): capability runner, agoge,
   check/apply reconciliation.
9. **Personal cutover** (PRD 00011, held): canaries for both launchers, then
   remove the legacy runtime. Needs 2 to 8.
10. **Public release track** (PRDs 00012 generic driver, 00013 Linux, 00014
    stable release, held).

### Out of scope

- New product features beyond the original plan (discovery 00001).

## Constraints

- The held phase PRDs 00010 to 00014 predate these findings. Before promoting
  each one, refresh it against this map: they still cite `dev/local/` paths and
  assume the August characterization is current.
- Discovery 00001 placed public visibility last. The user moved it first on
  2026-10-18; PRD 00014 now covers only the stable release.

## Codebase Context

- **Relevant code**: see each discovery doc. Evidence base: the readiness
  review at `docs/dev/project-management/reviews/20261018-product-readiness.md`.
- **Integration points**: `prds/hold/00010` to `00014`, the external
  `claude-autopilot` run-autopilot skill.

## Success Criteria

- Every remaining item has exactly one home: a discovery doc here or a held
  phase PRD.
- Items 2 to 4 done means one fake-agent drain from a fresh `init` passes on a
  macOS runner, which is the first point where a real Claude drain is worth
  trying.

## Risks

- **Legacy keeps moving**: apply the freeze rule in discovery 00007 now, not
  at cutover.
- **Public visitors try it too early**: discovery 00008 puts a plain status
  line in the README.

## Open Questions

- Are waves (parallel PRD lanes) required for cutover? See discovery 00007.

## Discovery Log

### Q1: What does "done" look like for this map?

**Answer**: Personal cutover complete (PRD 00011), then the public release
track. Derived from discovery 00001 and the user's 2026-10-18 decision to
publish early.

## 2026-10-25 plugin/runtime correction

The [corrected boundary](../designs/autopilot-optional-supervision.md) preserves discovery 00001: OVCAQ replaces the runtime; the plugin remains external. OVCAQ 00057–00060 can progress independently of plugin 00012–00015 because OVCAQ owns the runtime contract. Plugin 00016 joins them; 00061 supplies wave parity. Plugin 00013 is session-local helpers, not another state/lifecycle backend. OVCAQ 00060 explicitly owns record-store commits. Held 00011 now requires the module/behavior drift dispositions and proof of no runtime implementation inside the plugin. Existing robustness, operator, agoge and release holds remain.
