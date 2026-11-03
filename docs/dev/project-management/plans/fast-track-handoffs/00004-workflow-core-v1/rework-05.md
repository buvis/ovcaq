# FT-04F5 rework handoff

PRD: `dev/local/prds/wip/00004-workflow-core-v1.md`  
Session: `FT-04F5`  
Next session: `FT-04R6` (fresh review)  
Starting HEAD: `c512a4ad7d67af75b413ee8c9612b088d21fb4f4`  
Repair commit/new HEAD: `c4b9ea38d2e11eac4a1de1a71bd7d4134142e661`  
Repair range: `c512a4ad7d67af75b413ee8c9612b088d21fb4f4..c4b9ea38d2e11eac4a1de1a71bd7d4134142e661`  
Complete PRD review range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c4b9ea38d2e11eac4a1de1a71bd7d4134142e661`

## Bounded repair

1. Lifecycle identity now remains pinned by open WIP/hold descriptors through
   deferred-record publication and the final recovery commit. Both configured
   names and the moved regular PRD are revalidated before record advancement
   and immediately before reset/commit.
2. Workflow reporting now loads provider-neutral normalized `metrics.jsonl`
   rows, reduces sessions/timing/cost/output tokens and convergence rows,
   scopes report and installed-command bindings to the active batch, and emits
   deterministic nonzero, empty-zero, and incomplete/unknown summaries.
3. One shared printable path-component grammar now rejects control characters
   for lifecycle selection/record basenames and report headings/filenames.
   Report structure failures raise `ReportError`; `StopIteration` cannot escape
   report publication.

No frontmatter persistence, tier/config wiring, review-cap enforcement,
defer/state serialization, successful-PRD movement, or nonblocking de-slop work
was added.

Context-isolation note: an initial exact-ID search was mistakenly scoped across
`dev/local` and surfaced brief matching snippets from excluded earlier review,
raw-lens, and handoff files. Those files were not opened in full and the repair
scope remained limited to the three consolidated findings above.

## Regression evidence

- `test_later_boundary_lifecycle_replacement_fails_then_reconciles`: four real
  filesystem cases (WIP and hold at `AFTER_MOVE_BEFORE_APPEND` and
  `AFTER_APPEND_BEFORE_COMMIT`) prove rename-away plus symlink replacement
  leaves recovery at `moved`/`recorded`, preserves live tasks, does not touch the
  replacement, and replays exactly once after identity restoration.
- Existing saga matrices still prove all characterized boundaries, directory
  fsync ordering, explicit recovery kind, replay deduplication, park-breaker
  behavior, and active-recovery mutation fencing.
- `test_metrics_render_reduces_retained_characterized_rows` consumes the
  retained sanitized three-row fixture and proves 2 sessions, 27 wall seconds,
  USD 0.27, 22 output tokens, one convergence, and two cycles.
- Report tests prove state-plus-active-batch-metrics binding, exclusion of an
  unrelated batch, deterministic reordered input, legitimate empty zeroes,
  and unknown totals for populated rows missing optional usage values.
- Selection, deferred-record, renderer, and publication tests reject control
  characters. The installed-wheel regression consumes `metrics.jsonl`, binds
  it into metrics/report output, returns the `usage` domain error for an
  injected heading, leaks no `StopIteration`, and preserves prior report bytes.

## Fresh verification

| Command | Result |
| --- | --- |
| `mise exec -- uv sync --all-groups` | passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/workflow/test_reports.py tests/packaging/test_installed_cli.py -q` | passed; 73 tests in 2.41s |
| `mise exec -- uv run pytest` | passed; 1,108 tests in 11.98s |
| `mise exec -- uv run ruff check .` | passed |
| `mise exec -- uv run ruff format --check .` | passed; 92 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | passed; 47 source files |
| `mise exec -- uv build` | passed; built `dist/ovcaq-0.1.0.dev0.tar.gz` and `dist/ovcaq-0.1.0.dev0-py3-none-any.whl` |
| `git diff --check c512a4ad7d67af75b413ee8c9612b088d21fb4f4..HEAD` | passed |
| `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..HEAD` | passed |

## Next session

Start `FT-04R6` as a fresh review session over the complete PRD range above.
Do not continue implementation or run review from FT-04F5.
