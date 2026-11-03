# FT-04R5 Blake blind review — cycle 05

## Isolation

- Role: Blake, isolated blind PRD-only reviewer.
- Requirements source: `dev/local/prds/wip/00004-workflow-core-v1.md` only.
- Governance source: `AGENTS.md`.
- I did not read implementation plans, coverage manifests, discovery documents, prior reviews, fast-track handoffs, commit messages/logs, or other reviewer output.
- Review scope: the complete implementation range, all changed implementation/docs/tests, and necessary lower-layer state/configuration code.
- Repository changes: this report only; implementation, tests, PRD, plans, state, and capsule were not modified.

## Reviewed revision

- HEAD: `c512a4ad7d67af75b413ee8c9612b088d21fb4f4` (verified before review)
- Complete range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c512a4ad7d67af75b413ee8c9612b088d21fb4f4`
- Initial worktree: clean

## Verdict

**changes_requested**

The transition table, park/stall recovery, deterministic renderers, command inventory, provider-neutral boundary, and broad test coverage are strong. The public implementation nevertheless misses three explicit PRD contracts: defer has no durable state recovery intent, parsed lifecycle frontmatter is not committed as workflow authority, and configured lifecycle paths are not wired into the installed commands.

## Must-fix findings

### 1. High — `defer` is outside the durable recovery protocol and can publish against stale state

The PRD requires defer/park/stall to use operation IDs plus durable `recovery.operation` intent around record writes and requires restart recovery at every durable boundary. Public defer instead performs an unlocked state read, releases the state-store lock, and later writes the ledger:

- `src/ovcaq/workflow/records.py:201-210` reads and validates active batch/PRD/recovery state, then calls the filesystem writer after the read lock is gone.
- `src/ovcaq/workflow/records.py:307-365` locks only the deferred-record file; it never stamps or advances `state.recovery.operation`.
- `src/ovcaq/state/schema.py:59-60` permits recovery kinds only for `park` and `stall`, so defer cannot currently leave durable recovery intent.
- `src/ovcaq/cli.py:685-688` exposes this unfenced path as the installed `workflow defer` command.

This creates a concrete interleaving: defer validates PRD A and batch B; before its record lock/write, park or stall commits recovery, moves PRD A, writes its own record, and resets per-PRD state; defer then publishes its stale record and reports success. There is no committed intent from which restart or a competing workflow mutation can discover that defer owns a durable boundary. The existing defer failpoint tests (`tests/workflow/test_sagas.py:800-846`) demonstrate atomic file retry before/after replacement, but do not cover the required state-intent/concurrent-mutation boundary.

Fix by bringing defer under the durable state recovery protocol (including an operation kind/steps sufficient to reconcile its publication) or an equivalent state-store-owned protocol that durably fences competing workflow mutation before record publication and makes restart reconciliation authoritative.

### 2. High — frontmatter lifecycle choices are returned transiently but erased from committed authority

The PRD requires frontmatter policy to drive the deterministic workflow while the architecture requires state, not prose/output, to decide lifecycle behavior. `apply_to_store` parses `catchup`, `design`, `design_gate`, and `pause_on_ambiguity`, but does not commit any of them:

- `src/ovcaq/workflow/frontmatter.py:160-181` computes the effective fields and reads prior lifecycle extension values for overwrite warnings.
- `src/ovcaq/workflow/frontmatter.py:183-189` commits only `review.cap` and an optional tier floor; it removes every lifecycle extension key and never writes the newly parsed lifecycle values.
- `src/ovcaq/cli.py:619-627` returns those uncommitted values in command output, which is not durable authority.
- `src/ovcaq/workflow/resume.py:30-42` subsequently derives build resume only from tasks and `batch.catchup.completed_at`; a parsed `catchup: skip` therefore still resumes as `build: catchup then planning` unless some external actor performs another undocumented mutation.

The application test actually pins the loss: after parsing skip/skip/pause fields, it expects `work.extensions` to contain only the tier (`tests/workflow/test_applications.py:27-63`). This is not an equivalent lifecycle outcome and leaves PRD 00005 without a stable committed workflow input.

Commit the effective provider-neutral frontmatter policy through the state application service (using owned fields or documented workflow extensions) and make downstream resume/policy decisions consume that committed representation.

### 3. Medium — installed workflow commands ignore configured lifecycle directories and the active tier map

The PRD explicitly requires configured lifecycle paths and resolution of abstract model hints through the active agent's configured tier map. The pure functions accept both inputs, but the public command path replaces them with constants/absence:

- `src/ovcaq/cli.py:561-564` and `src/ovcaq/cli.py:597-607` hardcode `Path("dev/local/prds")` for workflow context and selection. No installed workflow command obtains a configured PRD root.
- `src/ovcaq/workflow/paths.py:20-37` can resolve a supplied root, but this capability is unreachable from the installed command family.
- `src/ovcaq/cli.py:608-616` calls `frontmatter.apply_to_store` without `available_tiers`, so every `default_model` declaration is treated as unavailable on the CLI.
- `src/ovcaq/config.py:8-15` only creates an empty configuration file; it supplies neither lifecycle-root nor tier-map values.

Consequently `workflow select`, `stall`, and `park` cannot operate on a configured lifecycle tree, and `workflow frontmatter` cannot apply a valid configured tier floor even though `frontmatter.parse` supports one. Wire configuration/runtime inputs into the public workflow boundary while keeping provider/model details at the adapter/runtime edge.

## Nonblocking observations / residual doubts

- `complete_prd_in_store` suppresses duplicate summaries but still increments the revision on an exact retry (`src/ovcaq/workflow/records.py:181-191`). This may be acceptable semantic idempotence, but byte-level retry idempotence would be more consistent with the saga/report behavior.
- Transition rows trust caller-supplied outcomes without cross-checking task/review facts (`src/ovcaq/workflow/transitions.py:72-116`), so `tasks_done`, `converged`, or `drained` can be committed against contradictory state. The PRD says decisions derive from committed state plus a normalized session result, but it does not define the normalized result contract in enough detail to call this a separate blocker here. PRD 00005 should either provide that validated result boundary or add explicit state preconditions.
- Report section updates use atomic replacement but no report-level lock (`src/ovcaq/workflow/reports.py:391-411`); concurrent projections can lose another process's section update. The PRD mandates deterministic/idempotent projections but does not explicitly require concurrent writers, so this is not blocking FT-04R5.

## PRD acceptance audit

| PRD obligation | Result | Evidence |
| --- | --- | --- |
| Current lifecycle fixtures have equivalent v1 outcomes | Partial | Three legacy resume fixtures and report goldens pass, but lifecycle frontmatter choices are not committed or consumed. |
| Every transition and rejection covered row-by-row | Pass | Six accepted rows plus phase/outcome rejection matrix in `tests/workflow/test_transitions.py`. |
| Park/stall/defer recover at all durable boundaries | Fail | Park/stall carry durable intent and failpoint coverage; defer has atomic file replay only and no `recovery.operation` protocol. |
| No hardcoded legacy runtime root remains | Pass narrowly | Workflow guard rejects `dev/local/autopilot`; however the separate configured-lifecycle-root requirement fails because the CLI hardcodes `dev/local/prds`. |
| Workflow imports only state and standard-library/lower-layer code | Pass | Static boundary guards and source inspection show no higher-layer/provider imports. |
| PRD 00005 can consume stable workflow/state services | Fail | Public commands omit configured path/tier inputs and frontmatter lifecycle policy is transient. |
| Full installed command family and parser-derived docs | Pass | Ten required workflow verbs are registered; `docs/operations.md` and state inventory are generated/tested from the live parser. |
| Deterministic audit/report/metrics projections | Pass for tested serial use | Golden, byte-idempotence, confinement, and installed CLI tests pass. |

## Checks run

- `git rev-parse HEAD` — exact required SHA confirmed.
- `git status --short` — clean before review.
- Complete range name/status, stat, and source/test/doc diff inspection.
- `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c512a4ad7d67af75b413ee8c9612b088d21fb4f4` — passed (no output).
- `PYTHONDONTWRITEBYTECODE=1 mise exec -- uv run --frozen pytest -p no:cacheprovider` — **1095 passed in 24.48s** on Python 3.13.13.
- Focused static tracing of frontmatter application/resume authority, configured workflow context, recovery fencing, defer publication ordering, transition guards, and report publication.

