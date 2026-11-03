# Bob — doubt and de-slop

The initial Bob context did not return after two completion requests. This is
the complete report from the plan-mandated fresh fallback using the same
isolated input packet and full `review-with-doubt` procedure.

## Verdict

changes_requested

## Must fix

- **Premature PRD completion — high.** `complete_prd()` accepts build/review
  state and records completion; reproduced from build, and
  `tests/workflow/test_workflow_cli.py:142-158` completes during review.
  Violates the state-decides invariant and fixed lifecycle.

- **Conflicting operation IDs lose records — high.**
  `src/ovcaq/workflow/records.py:295-296` treats any duplicate `op_id` as
  success without comparing payloads; reproduced a differing second payload
  being silently discarded. Violates idempotence and no-lost-work recovery.

- **Lifecycle symlink escape — high.**
  `src/ovcaq/workflow/records.py:348-362,468` trusts symlinked lifecycle
  parents; reproduced moving a WIP PRD into an external directory through a
  symlinked `hold`. Violates verified moves and creates data-loss/path-escape
  risk.

- **False saga replay — high.** `src/ovcaq/workflow/records.py:473-488` trusts
  destination existence alone before active-PRD validation, intent, record, or
  reset. Reproduced success for an already-held PRD while another PRD was
  active. Violates committed active-PRD binding and recoverable saga semantics.

- **Configured lifecycle root is not wired to commands — medium.**
  `src/ovcaq/cli.py:504,541` hardcodes `dev/local/prds`; `ovcaq.toml` is never
  read. Relative/absolute configuration tests exercise only the pure resolver.
  Violates the configured lifecycle-directory requirement.

- **Non-files are selected as PRDs — medium.**
  `src/ovcaq/workflow/selection.py:43-52` projects entry names without checking
  regular files; reproduced selecting `00001-directory.md/` ahead of a real
  backlog PRD. Violates PRD discovery/selection.

- **Launcher-specific resume instruction in core — medium.**
  `src/ovcaq/workflow/resume.py:39` emits `/work continues...`; the boundary
  guard omits launcher skill identifiers. Violates provider-neutral workflow
  and external-capabilities boundaries.

## Can defer

- POSIX-only `fcntl` prevents Windows import; cross-platform integration belongs
  to later PRDs.
- The diff's net 3,655 lines are roughly 61 times the acceptance-criteria word
  count. Most bulk is justified by the saga matrix, but
  `TransitionRow.next_phase`, `next_phase()`, and the weak related test are
  removable duplication of roughly 20 lines.
- `_workflow_context()` (`src/ovcaq/cli.py:502-505`) is a trivial single-caller
  abstraction.
- Several trivial docstrings paraphrase code, including
  `frontmatter.defaults()` and `transitions.next_phase()`.
- `"/" in value` in `_require_basename()` (`records.py:185`) is unreachable
  after `Path(value).name != value`; harmless redundant defense.
- `check-plan --ceiling` accepts negative values and reports zero tasks
  oversized; odd public input, but no positive-ceiling contract is stated.
- `test_next_phase_agrees_with_effect_table` checks membership in four strings,
  not agreement with effects; it is redundant because row effects are tested.

## Tests inspected or run

- Inspected all changed workflow/CLI/error files and workflow tests for
  applications, boundaries, frontmatter, policy, records, reports, resume,
  sagas, selection, transitions, CLI, plus packaging diffs.
- Read the passing verification evidence: 1,020 full tests, 138 focused tests,
  lint, format, mypy, build, and transition probe.
- Narrow temporary-directory probes confirmed duplicate-payload loss, false
  replay, symlink escape, premature completion, and directory selection.
- No exhaustive gates were rerun; no files were changed.

## Residual doubts

- 19 total doubts: 5 verified and dismissed, 7 confirmed must-fix, and 7 known
  limitations.
- Dismissed checks covered injected tier-map support, intentionally preserved
  review cap, bounded recursion at 512 tasks, deterministic committed-list
  rendering, and StateStore transaction serialization.
- All six Phase 1 questions and all five slop lenses were exercised.
