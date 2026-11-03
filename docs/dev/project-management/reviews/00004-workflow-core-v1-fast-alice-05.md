# Alice architecture/consensus review — FT-04R5 cycle 05

## Isolation and reviewed revision

- Role: isolated consensus/architecture reviewer (Alice).
- Verdict: **changes_requested**.
- Reviewed HEAD: `c512a4ad7d67af75b413ee8c9612b088d21fb4f4` (verified before review; no checkout or commit switch).
- Complete review range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c512a4ad7d67af75b413ee8c9612b088d21fb4f4`.
- Read the required AGENTS, accepted implementation plan, coverage manifest, discovery, PRD 00004, allowed range changes, workflow implementation/tests/docs/fixtures, and the state/config/path lower layers needed to assess integration.
- I did not read any file under `dev/local/reviews/`, any file under `dev/local/plans/fast-track-handoffs/`, `dev/local/plans/fast-track-implementation-plan.md`, git commit messages/logs, or other reviewer output.
- No implementation, test, plan, PRD, state, capsule, or handoff file was modified. This is the only review artifact written.

## Must-fix findings

### 1. High — Frontmatter controls are reported but discarded rather than committed

`src/ovcaq/workflow/frontmatter.py:160-195` parses `catchup`, `design`, `design_gate`, and `pause_on_ambiguity`, but the transaction commits only `review.cap` and, conditionally, `workflow/tier-floor`. Lines 184-186 explicitly remove all four corresponding extension keys and never write their effective values. The returned `FrontmatterApplication.fields` therefore claims that controls were applied although committed state cannot recover them. `src/ovcaq/workflow/resume.py:30-42` confirms the consequence: resume derives the build action solely from committed catch-up state, so a PRD declaring `catchup: skip` still resumes as `build: catchup then planning` until some unrelated caller records catch-up completion.

This violates P02-T02, the PRD boundary that workflow consumes committed state, and characterized route `CMD-014` (“transactionally applies the derived state fields”). It also breaks restart determinism: the command's transient JSON output, rather than state, becomes necessary to honor frontmatter. Existing coverage codifies the loss at `tests/workflow/test_applications.py:48-62` by asserting that all controls are returned while committed `work.extensions` contains only the tier.

Required correction: give every effective workflow control an authoritative v1 representation/application rule (including defaults and overwrite behavior), make resume/consumers derive from that committed representation, and add a restart/resume test for at least `catchup: skip`, `design: skip`, and the opt-in controls.

### 2. High — The installed frontmatter command cannot accept any valid tier hint

The PRD requires `default_model` to name an abstract tier resolved through the active agent's configured tier map, with a warning only when the tier is absent. The parser/API supports that contract at `src/ovcaq/workflow/frontmatter.py:126-134`, but the installed command calls `apply_to_store` without `available_tiers` at `src/ovcaq/cli.py:608-616`. Its value is therefore always `None`; every `default_model` declaration is classified unavailable and no tier floor can be committed through `ovcaq workflow frontmatter`, regardless of actual configuration.

The unit test at `tests/workflow/test_frontmatter.py:109-119` proves only the private API when a set is manually injected; no CLI/config integration covers the required accepted-tier path. This is an in-scope P02-T02/source-PRD feature, not later provider routing: the workflow value remains an abstract tier key.

Required correction: resolve and pass the active agent's configured tier keys at the command/application boundary (without leaking provider identifiers into workflow), and add installed/in-process CLI tests for accepted and absent configured tiers.

### 3. High — P02-T08 did not port the characterized metrics/report renderer contract

`src/ovcaq/workflow/reports.py:168-202` implements `render_metrics(state)` as review-cycle/decision/doubt totals only. It has no input for loop/session metric rows and cannot render the characterized `wall_secs`, `cost_usd`, or `tokens_out` evidence in `tests/fixtures/claude/legacy-metrics.jsonl`. The range contains no production consumer of that fixture. Likewise, `render_report` at `src/ovcaq/workflow/reports.py:103-165` accepts only state and deferred records, despite characterized `CMD-019` requiring report sections derived from state **and metrics**. The replacement goldens in `tests/workflow/test_reports.py:143-152,292-312` test a newly invented state-only projection, while `tests/workflow/test_characterized_fixtures.py:62-88` checks only resume targets and leaves the characterized metrics fixture unused.

P02-T08 explicitly owns porting deterministic audit/report/metrics rendering, and coverage routes `CMD-019`, `CMD-020`, `ART-039`–`ART-041`, `TEST-018`–`TEST-020`, and `TEST-062` to PRD 00004. Replacing the renderer's input domain and output semantics without an authorized retirement or equivalence proof is source-contract dilution. Operators invoking `ovcaq workflow render metrics` currently receive review bookkeeping, not the characterized workflow/session metrics surface.

Required correction: port the characterized metric-row reduction and its report bindings against the retained sanitized fixture/goldens, or record an explicit accepted retirement/reassignment in the authoritative plan/coverage before changing the contract. Add equivalence tests that actually consume `legacy-metrics.jsonl`, including nonzero and legitimately empty summary bindings.

## Nonblocking observations

- `src/ovcaq/cli.py:561-564,602` still supplies `Path("dev/local/prds")` directly. The pure resolver accepts a configured root, so P02-T01's lower-level seam exists, but configuration precedence is not connected yet. This is acceptable only if PRD 00005 supplies that integration before runtime consumers rely on it.
- `complete_prd_in_store` prevents duplicate records but still commits a new revision on an exact replay (`tests/workflow/test_applications.py:201-223`). That is data-idempotent, not byte/revision-idempotent; document the intended meaning before downstream callers treat revision changes as semantic progress.
- The saga implementation materially strengthens directory identity, fsync, symlink, hard-link, operation replay, and recovery fencing behavior. The focused saga matrix is unusually thorough and all current tests pass.

## Acceptance and source-ID audit

| Source ID | Assessment |
| --- | --- |
| P02-T01 | Implemented at the pure resolver/selection layer: WIP-first, backlog fallback, hold exclusion, sequence ordering, and absent/invalid directory handling are covered. CLI configuration wiring remains a later integration dependency noted above. |
| P02-T02 | **Fail**: parsing/default/warning behavior exists, but most effective controls are not durably applied; the CLI cannot resolve a valid configured tier. |
| P02-T03 | Pass: the six accepted rows and rejection matrix are closed; `phase-complete` uses one store CAS transaction and recovery intent fences it. |
| P02-T04 | Pass for the implemented resume precedence and plan ceiling/shape policy; recovery outranks phases and state drives the result. |
| P02-T05 | Pass with the idempotence nuance above: reset ownership and batch preservation are explicit, and completion summaries are deterministic/deduplicated. |
| P02-T06 | Pass: deferred records require operation IDs, deduplicate exact replay, reject conflicts, lock publication, fsync, and recover at publication boundaries. |
| P02-T07 | Pass: park/stall intent→move→record→reset→commit is recoverable across the named durable boundaries, with verified directory identity and state-mutation fencing. |
| P02-T08 | **Fail**: audit exists, but the characterized metrics and metrics-bound report contracts were replaced rather than ported/equivalence-tested. |
| P02-T09 | Pass for removal of the legacy runtime-root literal and use of `dev/local/ovcaq`; provider/legacy string guards pass. |
| P02-T10 | Pass: workflow command docs and state-protocol inventory are generated from and checked against the live parser. |

Phase exit criteria therefore do not pass: the package boundary and saga recovery criterion pass, but lifecycle/input equivalence and renderer equivalence do not. The stable workflow surface is not ready for PRD 00005 until the P02-T02 and P02-T08 failures are corrected.

Architecture invariants are otherwise preserved in the reviewed range: durable state writes pass through `StateStore`; transition/resume authority is committed state; workflow imports remain provider-neutral/lower-layer only; no provider event parsing or launcher content entered workflow; and no shell evaluation was introduced.

## Checks run

- `git rev-parse HEAD` — exact required SHA confirmed.
- Allowed full-range name/status and stat audit for `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c512a4ad7d67af75b413ee8c9612b088d21fb4f4`, excluding only the explicitly prohibited review/handoff files.
- `env PYTHONDONTWRITEBYTECODE=1 mise exec -- uv run pytest -p no:cacheprovider` — **1,095 passed** in 24.45s on Darwin/Python 3.13.13.
- `env PYTHONDONTWRITEBYTECODE=1 mise exec -- uv run ruff check .` — passed.
- `env PYTHONDONTWRITEBYTECODE=1 mise exec -- uv run ruff format --check .` — 92 files already formatted.
- `env PYTHONDONTWRITEBYTECODE=1 mise exec -- uv run mypy src/ovcaq` — passed, 47 source files.
- Static call/data-flow reproduction: traced parsed frontmatter fields through `apply_to_store`, CLI dispatch, committed owners, and resume; traced both renderer signatures/callers and verified that the retained legacy metrics fixture has no production/test consumption in this range.

## Verdict

**changes_requested** — fix the two frontmatter authority/integration defects and restore or formally reconcile the P02-T08 characterized rendering contract before approving FT-04R5.
