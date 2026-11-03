# Discovery: End-to-end verification

## Classification

Depth: standard | Date: 2026-10-19 | Status: open

## Problem

The suite has 7,252 tests and is mostly sound: in the 2026-10-18 audit no test
failed for a product reason, none flaked, none were skipped, and 20 of 24
sampled tests bound to a real rule. It still cannot prove the one journey a
user runs first: `ovcaq init`, then `run`, then a drained batch. Every drain
test seeds `batch.*` and `work.prd` straight through the store, and the
installed-wheel drain uses a fake that edits state directly instead of calling
the `ovcaq` CLI. `fake_claude.py` never drives the supervisor; the "claude"
drain variant runs the Codex fake with a swapped file name. Both providers are
proven only against hand-written schema-synthetic fixtures. No CI has ever run,
and the CI file targets Ubuntu while the runtime refuses anything but macOS.

## Requirements

### Must have

- One installed-wheel test per launcher: fresh `init`, `run --no-tui`, a fake
  agent that mutates state only through the `ovcaq` console script, two PRDs,
  ending with `batch.status == "completed"`, both PRDs in `done/`, and session
  evidence on disk. Depends on discovery 00003 for the entry verb.
- `fake_claude.py` drives that test for Claude with Claude-shaped output.
- One sanitized captured transcript per provider, from a real CLI run, asserted
  on the `SessionSummary` (success, failure class, usage), not on event shapes.
- A macOS CI job running `uv sync --locked` and the same steps as
  `mise.toml`'s `check` task, with uv pinned to the mise version. Ubuntu runs
  only the platform-neutral suites until PRD 00013.
- Negative assertions name the error code or message. Replace the 35 sites
  that accept any non-zero exit or any `OSError`.

### Nice to have

- A coverage report in CI (no gate), so the supervisor and TUI model numbers
  stop being guesses.
- Rename the `test_rework_1x.py` and `rework_1x_scripts.py` files after the
  behavior they test.

### Out of scope

- Live model calls in CI. Captured transcripts replace them.
- Linux CI for runtime suites. That is PRD 00013.

## Constraints

- Tests never read `~/.claude` or `~/.codex`; transcripts are sanitized and
  checked in under `tests/fixtures/` with provenance (AGENTS.md).
- Process and signal behavior keeps real-subprocess tests.

## Codebase Context

- **Relevant code**: `tests/packaging/test_installed_supervisor_cli.py:26-59`
  (`FAKE_DRIVER` edits state through `StateStore`), `:68` (seeded batch id);
  `tests/runtime/test_supervisor.py:215` (seeded batch);
  `tests/runtime/test_supervisor_adapters.py:44-51` (Claude variant runs the
  Codex fake), `:96` (seeded `work.prd`); `tests/fixtures/README.md:24-25`
  (schema-synthetic); `.github/workflows/ci.yml` (ubuntu, no `--locked`).
- **Similar implementations**: `tests/fixtures/codex/v1/fake_codex.py:100-136`
  already performs CLI handoffs (`state show`, `workflow select`,
  `phase-complete --expected-revision`, `complete-prd`).

## Success Criteria

- The two journey tests pass on a macOS runner and fail if any production
  step is removed (checked by deleting the entry verb once).
- CI is green on the first push and runs on every push.

## Risks

- **Captured transcripts leak private data**: run the capture in a scratch
  repo with a throwaway prompt, then pass the file through the existing
  normalizer redaction and a secret scan before commit.

## Open Questions

- Which real CLI versions to capture against, and how often to refresh them?

## Discovery Log

### Q1: Is the suite trustworthy today?

**Answer**: For state, workflow, events, decoders, and TUI panels, yes. For
the supervisor a user runs, no; see the 2026-10-18 test audit.
