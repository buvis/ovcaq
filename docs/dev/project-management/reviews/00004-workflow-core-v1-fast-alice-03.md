# FT-04R3 Consensus/Architecture Review

## Review scope

- Reviewed HEAD: `f2453760591875f1faf241ec9c0291303232efd9`
- Complete range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..f2453760591875f1faf241ec9c0291303232efd9`
- Verdict: `changes_requested`

## Findings

### F1 — High: Lifecycle paths can escape the repository through symlinks or `..`

- **Root cause:** `resolve_lifecycle_paths()` calls `Path.resolve()` without enforcing containment or rejecting symlinked ancestors. The saga’s `O_NOFOLLOW` protects only the final `wip`/`hold` component, after the potentially unsafe root has already been resolved.
- **Evidence:** `src/ovcaq/workflow/paths.py:20-36`; `src/ovcaq/workflow/records.py:398-424`; `src/ovcaq/workflow/records.py:634-695`.
- **Impact:** A default or configured PRD root that is a symlink, or a relative root containing `..`, can make `select`, `stall`, and `park` read or move files outside the repository. This contradicts the accepted path-confinement policy and defeats the otherwise careful non-symlink filesystem checks.
- **Required fix:** Resolve relative lifecycle roots beneath a verified repository directory without following symlink components; reject lexical escape and symlinked ancestors. If external absolute roots are supported, require an explicit external-root path. Open lifecycle descendants through verified directory descriptors. Add selection and stall/park tests for a symlinked PRD root, symlinked intermediate ancestor, and `..` escape, with external sentinels proving no mutation.

### F2 — High: Saga replay can advance state without re-establishing filesystem durability

- **Root cause:** Newly created `hold` and `deferred` directories are not followed by an `fsync` of their parent directory. Recovery also treats an already-moved PRD or an exact deferred-record replay as complete without fsyncing the relevant directories.
- **Evidence:** `src/ovcaq/workflow/records.py:242-269`; `src/ovcaq/workflow/records.py:315-348`; `src/ovcaq/workflow/records.py:398-406`; `src/ovcaq/workflow/records.py:440-469`; state advances immediately afterward at `src/ovcaq/workflow/records.py:687-714`.
- **Impact:** If execution stops between rename/replace and directory fsync, replay can observe the in-memory directory entry, skip the missing durability operation, and commit `moved`, `recorded`, or clear recovery. A later host failure can then lose the hold move or ledger, leaving reset state and a held/missing PRD without durable proof. A newly created directory can likewise disappear because its parent entry was never synced.
- **Required fix:** Fsync each parent after creating `hold` or `deferred`; after verifying the terminal move state, always fsync both lifecycle directories before advancing state, including replay; on exact deferred-record replay, fsync the record directory and ensure the directory’s parent entry is durable. Add syscall-level interruption tests around mkdir, rename/replace, and each directory fsync.

### F3 — Medium: Installed commands bypass configured lifecycle and tier inputs

- **Root cause:** Both workflow contexts hardcode `dev/local/prds`, and the installed `frontmatter` command never passes an active agent tier map into `apply_to_store()`.
- **Evidence:** `src/ovcaq/cli.py:554-557`; `src/ovcaq/cli.py:590-609`; unavailable tier behavior at `src/ovcaq/workflow/frontmatter.py:126-134`.
- **Impact:** A project-configured PRD root is ignored by installed `select`, `stall`, and `park` commands. Every `default_model` hint processed through the installed command is treated as unavailable, so a valid configured abstract tier floor is warned away. This leaves the PRD’s configured-path and frontmatter-tier requirements incomplete despite the pure APIs accepting those inputs.
- **Required fix:** Build one workflow command context from resolved configuration precedence, including `workflow.prd_root` and the active agent’s tier keys, and pass it to every installed workflow command. Add installed-wheel tests using a non-default PRD root and both present/absent abstract tier keys.

### F4 — Medium: A valid `stall --site wrapper_died` cannot replay idempotently

- **Root cause:** The public `--site` accepts arbitrary text, but durable records omit the operation kind and always use `"type": "stall"`. Replay infers park versus stall solely from `site == "wrapper_died"`, while park-counter reset also relies on that site instead of the operation kind.
- **Evidence:** `src/ovcaq/cli.py:184-190`; `src/ovcaq/workflow/records.py:489-511`; `src/ovcaq/workflow/records.py:570-598`; `src/ovcaq/workflow/records.py:700-709`.
- **Impact:** A stall with that accepted site commits as kind `stall`, but exact retry infers the record was a park and reports “no durable recovery proof.” It also fails to reset the consecutive-park breaker. This violates idempotent stall recovery for an accepted command input.
- **Required fix:** Persist and match the explicit recovery kind in deferred records and drive breaker behavior from `operation["kind"]`. Alternatively, reject the reserved site for `stall`. Add exact-replay and post-commit failpoint coverage for the collision.

## PRD acceptance-criteria coverage

| Acceptance criterion | Assessment | Evidence |
|---|---|---|
| Current lifecycle fixtures have equivalent OVCAQ outcomes | Covered for checked-in fixtures | `tests/workflow/test_characterized_fixtures.py:62-88`; report goldens at `tests/workflow/test_reports.py:292-312` |
| Every transition and rejection covered row-by-row | Covered | `tests/workflow/test_transitions.py:10-40`, `164-197` |
| Park/stall/defer recover at all durable boundaries | Not met | Named failpoint matrix is broad, but F2 leaves real syscall durability gaps and F4 breaks an accepted stall replay |
| No hardcoded legacy runtime root remains | Covered literally | Provider/legacy string guard at `tests/workflow/test_boundaries.py:46-53`; configured lifecycle behavior remains incomplete under F3 |
| Workflow imports only state and standard-library/lower-layer code | Covered | `tests/workflow/test_boundaries.py:30-43` |
| PRD 00005 can consume stable workflow and state services | Not met | Path confinement, durable replay, and configured installed-command context require correction |

## Architecture and invariant assessment

| Area | Assessment |
|---|---|
| One state writer | Met. Durable state mutations use `StateStore.transaction()` or store-backed application services. |
| State decides; prose does not | Met for this phase. Resume, transitions, completion, and recovery consume committed state and structured outcomes. |
| Provider code stays at the edge | Met. Workflow production modules contain no provider imports or identifiers. |
| Raw evidence survives normalization | Provider normalization is out of scope; filesystem recovery evidence does not yet meet the durability guarantee because of F2. |
| TUI observes shared models | Not exercised in this PRD; no violation introduced. |
| External capabilities remain external | Not exercised; no launcher content was added. |
| No shell evaluation | Met within this range; workflow code spawns no commands. |
| Dependency direction | Met: workflow depends only on state, workflow peers, and the standard library. |
| Product/filesystem boundary | Not met because F1 allows lifecycle operations outside the intended project boundary. |
| Installed-command contract | Partial: family, JSON behavior, CAS paths, packaging smoke, and generated docs are present; configured roots and tier resolution fail under F3. |

## Verification evidence

Fresh supplied gate evidence:

- `mise exec -- uv sync --all-groups`: exit 0; 25 resolved, 24 checked.
- `mise exec -- uv run pytest`: exit 0; 1068 passed in 13.84s.
- `mise exec -- uv run ruff check .`: exit 0.
- `mise exec -- uv run ruff format --check .`: exit 0; 92 files formatted.
- `mise exec -- uv run mypy src/ovcaq`: exit 0; 47 source files clean.
- `mise exec -- uv build`: exit 0; sdist and wheel built.
- Additional read-only check: complete-range `git diff --check` passed.

The passing gate demonstrates broad functional and packaging coverage but does not exercise ancestor-symlink confinement, parent-directory durability, syscall-gap replay, configured installed-command roots/tiers, or the reserved-site collision.

I reviewed the complete range `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..f2453760591875f1faf241ec9c0291303232efd9`, not only the final rework commit.
