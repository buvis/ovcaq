# FT-04F11 repair handoff

Date: 2026-09-06, Europe/Prague. The bounded R11 repairs are complete and
committed. No completion review ran in this implementation session.

## Exact repository state

- Repository: `/Users/bob/git/src/github.com/buvis/ovcaq`
- Branch: `master`
- HEAD: `39ecaf4f95c79df6a88c30e4626386a352d1505b`
- Commit: `fix(workflow): close publication durability races`
- Commit timestamp: `2026-09-06T21:18:02+02:00`
- Incoming repair base: `22d9193a0d00486b09ebea169e7a38a9f858799d`
- Full implementation base: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`
- Status empty; stash list empty; only the original checkout and `master` exist.

At preflight and handoff, `dev/local/autopilot/state.json` was absent. This
differs from the incoming historical-state observation, so no state was
attached, created, imported, overwritten, or mutated. The standalone repair
transition is the commit above plus this handoff. Dispatch telemetry was written
only to `dev/local/autopilot/dispatch-metrics.jsonl` and its ledger mirror.

## Repairs

1. R11-01: deferred publication now canonicalizes, decodes, and applies the
   reader's bounded JSON-value validation to the complete prospective ledger
   before touching disk. Depth 30 remains accepted; depths 31–33 return
   contextual `resource_limit`/11 with prior ledger and state bytes intact.
2. R11-03: missing configured runtime ancestors are created top-down and each
   new directory entry is confirmed by fsyncing its parent. A failed parent
   sync removes only the just-created empty child, so retry rediscovers that
   boundary while retaining earlier confirmed partial ancestors. Runtime and
   deferred identity guards, directory-fd serialization, sidecars, and exact
   replay remain intact.
3. R11-02: report read/compose/publish now runs under the existing kernel
   directory-descriptor serialization boundary. A contender either publishes
   without losing prior successful sections or receives a contextual retry;
   retries preserve complete returned text and unchanged authoritative state.

The changelog and installed-wheel regressions were committed with the repair.
Raw fail-first output is retained in `rework-11-red.txt` beside this file.

## Provider and dispatch evidence

- Tess test author: native Codex subagent `tess_f11` / Poincare, logical
  `sonnet`, actual provider/model `OpenAI / gpt-5.6-sol`, isolated prompt.
- Ivan implementation attempt: external Claude CLI via the real use-sonnet
  wrapper, logical `sonnet`, actual provider/model `Anthropic Claude / sonnet`;
  dispatch id `e9409cc8`.
- Ivan implementation retry: external Claude CLI, same tier/model provenance;
  dispatch id `004bfa5e`.
- Ivan mandatory style repair: external Claude CLI, same tier/model provenance;
  dispatch id `24e0b086`.
- Dispatch `17b34a70` was closed as `error:prompt_superseded_before_dispatch`;
  it was never sent to a provider and is not model evidence.

Raw prompts and Claude results remain under `dev/local/tmp/dispatch-ivan-f11*`
and `dev/local/tmp/ivan-f11*`. No native model-diversity claim is made.

## Verification

- Fail-first installed regression: 5 failed, 4 passed on incoming production.
- Post-repair installed regression: 9 passed (also rerun post-commit).
- Existing focused records/deferred/report preservation: 78 passed.
- Workflow plus packaging: 460 passed.
- Full pytest: 1,348 passed in 22.42s; zero failures/skips.
- `uv sync --all-groups`: clean.
- Ruff check and format check: clean (119 files formatted).
- mypy: clean (51 source files).
- Build: wheel and sdist successful.
- Wheel SHA-256: `e085e2fba91ab171abe1dcb22693495040a238c9846dd83e93d0bfd9621c47f4`.
- Sdist SHA-256: `8edde79fb888731194bc078b53ccdd5ce47c8ce3b641eb9d5f1b4763117f4c94`.
- Full implementation-range `git diff --check`: clean.
- Task style-limit gate, split hygiene, reflow, and tautology detector: clean.
- Plan SHA-256 remains
  `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
- Inventory SHA-256 remains
  `d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9`.

## Preservation and exclusions

R10 complete-text equality and all R8/R9 repairs pass. The full suite preserves
strict decoding, safe identifiers and attribution, exact/conflicting op IDs,
temporary cleanup, sidecar ownership, directory-inode serialization, serialized
snapshot comparison, output traversal identity, all report/audit/archive
fsyncs, golden bytes, Unicode, duplicate collapse, summary replacement, saga
identities, recovery, terminal drain, provider-neutral guards, and parser-derived
docs.

No importer, alias, launcher marker, provider policy, abort/rollback API,
duplicate-frontmatter policy, Linux signoff, implementation-plan edit, capsule
refresh, PRD closeout, or next-PRD work was added. R8-K1/K2 and R9-K3/K4 remain
KNOWN. The settled initially-absent-source adjudication remains closed.

## Next session

Run FT-04R12 only in a fresh completion-review session over
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..39ecaf4f95c79df6a88c30e4626386a352d1505b`.
Reconcile P02-T01–T10, all 55 owned rows, and every phase exit. Dispatch isolated
Alice consensus (native Codex Sol, full R rubric), Blake PRD-only (native Codex
Sol, full B rubric, no implementation evidence), and Bob doubt plus de-slop
(fresh external Claude Opus, full D1–D5). Include the required Bob receipt in
consolidation. Do not claim native model diversity. Do not inherit this work
session as the review context.

Unresolved questions: none.
