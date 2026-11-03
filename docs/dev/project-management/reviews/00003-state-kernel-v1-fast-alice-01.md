# Alice — consensus/architecture
Verdict: changes_requested
## Must fix
- Issue: Default runtime and lock paths can follow symlinks outside the resolved project. A symlinked `dev/local/ovcaq` makes `ovcaq init` chmod and write into its external target; a symlinked lock file is opened and `fchmod`ed. Severity: high. Evidence: `src/ovcaq/paths.py:28`, `src/ovcaq/cli.py:215`, `src/ovcaq/cli.py:347`, `src/ovcaq/state/store.py:179`. Violated requirement: `dev/local/plans/implementation-plan.md:975`–`977` requires project/runtime paths to remain under the resolved project unless an external state root is explicitly supplied.
## Can defer
- Issue: Several crosswalk “derived” rows do not define deterministic derivations, notably `cap_rotations -> recovery.operation` although recovery supports only park/stall, and token data mapped only to generic metadata or an estimate. Evidence: `docs/state-protocol.md:322`–`330`, `src/ovcaq/state/schema.py:56`, `src/ovcaq/state/schema.py:247`. Rationale: no immediate persistence defect, but clarify before Phase 2 relies on the crosswalk.
## Tests inspected or run
- Inspected all touched production modules, protocol documentation, and the complete touched state/schema/store/CLI/packaging test suites.
- `git diff --check 9cda04a6a0279a6306c24015ee2d3173fb916e68..9872123ac9be6433f95ad4fb5606ac48cb402fce`: passed.
- Focused durability, transaction, concurrency, and crosswalk run: 93 passed. Two installed-wheel tests could not set up because sandboxed `uv` could not access its cache.
- Separate installed-wheel retry with `UV_NO_CACHE=1`: blocked fetching `hatchling` by sandboxed DNS.
- Parser/schema/protection smoke: passed.
- Relied on supplied head evidence: `uv sync --all-groups` passed; full pytest 762 passed; Ruff check passed; Ruff format check passed for 75 files; mypy passed for 46 source files; sdist and wheel built; range `git diff --check` passed.
## Residual doubts
- Independent installed-wheel execution could not be reproduced inside this sandbox; the supplied successful full-suite and build evidence was relied upon.
