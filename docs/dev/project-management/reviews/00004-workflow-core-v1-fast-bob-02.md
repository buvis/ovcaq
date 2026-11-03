# Bob — doubt and de-slop

## Verdict

`changes_requested`

## Must fix

- **D1 — High: completion never advances the PRD file lifecycle.** `src/ovcaq/workflow/records.py:134` only appends a summary; `src/ovcaq/cli.py:627` calls that state-only operation; `src/ovcaq/workflow/transitions.py:61` resets fields; and `LifecyclePaths.done` is never consumed anywhere. Reproduction in `/tmp`: after `complete-prd` and `phase-complete --outcome more_prds`, `00004-current.md` remained in `wip`, was absent from `done`, and `select_from_paths` returned `('00004-current.md', 'wip')` instead of backlog PRD 00005. This violates completion, done-to-next-PRD, deterministic selection, and lifecycle-path acceptance.

- **D2 — High: `review.cap` is not an upper bound.** `src/ovcaq/workflow/transitions.py:40` unconditionally increments the review cycle; no transition uses `review.cap`, while `src/ovcaq/workflow/resume.py:15` contains a cap-pause resume branch that current workflow control flow cannot reach. A validated state at cycle 2/cap 2 committed `rework` as cycle 3, phase `review`, with no pause reason. This violates the per-PRD rework-cap policy and the required full review transition/resume behavior.

- **D3 — High: configured lifecycle roots are discarded at the installed boundary.** `src/ovcaq/cli.py:502` and `src/ovcaq/cli.py:541` hardcode `Path("dev/local/prds")`. `src/ovcaq/config.py:8` only creates `ovcaq.toml`; no source code reads TOML or supplies a configured PRD root. The pure resolver accepts configuration, but no installed workflow command can use it. This directly misses “resolve configured lifecycle directories.”

- **D4 — Medium: installed frontmatter cannot resolve an active agent’s tier map.** `src/ovcaq/cli.py:550` calls `apply_to_store` without `available_tiers`; `src/ovcaq/workflow/frontmatter.py:124` therefore treats every `default_model` hint as unavailable. There is no configuration-loading alternative. This misses the required abstract-tier resolution behavior.

- **D5 — High: frontmatter can be applied from the wrong PRD.** `src/ovcaq/cli.py:547` reads any supplied path and commits it without comparing its basename to committed `work.prd`. `/tmp` reproduction with active `00004-active.md` and `--prd 00005-other.md` exited 0, advanced the revision, and applied `catchup=skip` to PRD 00004. This violates committed-state attribution and allows cross-PRD lifecycle corruption.

- **D6 — Medium: overwrite warnings miss the valid cap value 3.** `src/ovcaq/workflow/frontmatter.py:165` treats every current cap of 3 as an unowned schema default. Applying `rework_cap: 3`, then `rework_cap: 2`, produced no warning on either application. This misses the explicit overwrite-warning requirement.

- **D7 — High: the public report publisher permits path escape from schema-valid state.** `src/ovcaq/workflow/reports.py:239` interpolates unvalidated `batch.id` into a path. A state accepted by `validate_state` with `batch.id="../../escape"` caused `publish_report(runtime_root, ...)` to create `runtime/reports/../../escape-report.md`; its resolved path was outside `runtime_root`. The CLI happens to reject this via an earlier deferred-ledger loader, but the stable workflow service itself is unsafe for PRD 00005 consumers. This is a security/data-overwrite risk.

- **D8 — Medium: deferred-record rendering is order-dependent for conflicting operation IDs.** `src/ovcaq/workflow/reports.py:92` uses `setdefault`, silently selecting the first record. The same two-record multiset in reversed order produced different reports. The loader does not reject duplicate operation IDs. This violates deterministic rendering from records.

- **D9 — Medium: workflow command truth is duplicated manually.** `docs/state-protocol.md:47`–`56` adds a second hand-written workflow verb inventory, while only `docs/operations.md` is generated and contract-tested from the parser. This directly violates the repository rule that command documentation comes from the parser and has no second inventory.

- **D10 — Medium, required evidence gap: two tests do not prove their named workflow contracts.** `tests/workflow/test_selection.py:94` inspects a Python signature instead of populating `hold` and verifying path-level exclusion. `tests/workflow/test_transitions.py:212` only checks that table metadata belongs to an allowed string set; it does not compare `TransitionRow.next_phase` with the effect’s committed `work.next_phase`. The PRD explicitly requires hold-exclusion and row-by-row transition evidence. Regression tests are also missing for D1–D8.

## Can defer

- **D11 — KNOWN, R2:** `src/ovcaq/workflow/resume.py:46` handles an unknown phase even though validated `State` permits only build/review/done/paused and all four are already handled. This is unreachable defensive code, but only minor local slop.

- **D12 — KNOWN, R2:** `src/ovcaq/workflow/records.py:463` checks for an active recovery operation inside `_stamp_intent`, although its sole caller reaches it only after observing no operation and supplies that revision to CAS. Any concurrent state change fails revision checking before this guard. Removing it is cleanup, not a correctness fix.

- **D13 — KNOWN, R3:** `src/ovcaq/cli.py:502` defines `_workflow_context` for one caller at line 546, and that caller has already resolved the same paths at line 541. It adds indirection and duplicate resolution but is non-blocking.

## Doubt audit

1. **Least-confident parts:** completion/file lifecycle (D1, VERIFY→FIX via end-to-end `/tmp` probe); cap enforcement (D2, VERIFY→FIX via validated store transaction); configuration integration (D3/D4, VERIFY→FIX via complete source search); report trust boundaries (D7/D8, VERIFY→FIX via probes).

2. **Assumptions checked:** configured roots do not reach the CLI (D3 FIX); active tier maps are never injected (D4 FIX); `complete-prd` does not use `done` (D1 FIX); frontmatter is not bound to active state (D5 FIX); cap 3 has no ownership provenance (D6 FIX); schema-valid batch IDs are not path-safe (D7 FIX).

3. **Completeness against PRD and complete range:** selection, parsing, basic transition rows, reset, park/stall/defer recovery, renderers, and the named command family are present. Completion lifecycle, cap policy, configured paths, active-tier resolution, attribution checks, deterministic conflict handling, and parser-derived documentation remain incomplete: D1–D10 FIX.

4. **Practical failures:** the completed PRD is selected again (D1 FIX); review can exceed its cap indefinitely (D2 FIX); another PRD’s frontmatter mutates the active PRD (D5 FIX); a public publisher can escape its root (D7 FIX); conflicting record order changes output (D8 FIX).

5. **Different approach:** D1/D3–D5 would be simpler and safer behind one configured workflow-application context binding state store, lifecycle paths, active PRD, and tier map. Completion should be a recoverable application operation covering verified `wip→done` movement plus summary/state commit. This is the recommended resolution of those FIX items, not a separate doubt.

6. **Missing checks:** behavioral hold exclusion and table/effect agreement (D10 FIX), plus regression coverage for completion/reselection, configured-root CLI use, tier resolution, wrong-PRD frontmatter, cap boundary, cap-3 warnings, report path containment, and conflicting operation IDs (corresponding D1–D8 FIX).

**Totals:** 13 doubts: 10 FIX, 3 KNOWN, 0 unresolved VERIFY.

## R1–R5 de-slop rubric

- **R1 — pass.** Complete range is +4,239/−12 across 30 files against an 885-word, ten-task workflow PRD: 1,753 net source lines, 2,447 net test lines, and 27 net documentation lines. The production/PRD ratio is about 1.98× and total/PRD ratio about 4.79×. The large portion is the required durable saga and boundary matrix; no module is concretely removable while retaining the specified surfaces. D9 is duplication, but too small to make the overall ratio fail.

- **R2 — fail.** The unknown-phase fallback at `src/ovcaq/workflow/resume.py:46` is unreachable from validated state (D11). The active-operation guard at `src/ovcaq/workflow/records.py:463` is unreachable through its sole CAS-controlled call path (D12).

- **R3 — fail.** `_workflow_context` at `src/ovcaq/cli.py:502` has one caller, duplicates path resolution already performed at line 541, and provides no separate architecture or testability value (D13). Store-backed workflow wrappers and the public pure policy functions were inspected and do have present boundary/testability value.

- **R4 — pass.** There are no added inline implementation-narration comments. The short public docstrings generally state contract qualifiers such as committed, deterministic, idempotent, configured, or CAS semantics rather than paraphrasing the next statement.

- **R5 — fail.** `test_selection_cannot_receive_hold` at `tests/workflow/test_selection.py:94` verifies Python signature shape, not hold-directory exclusion. `test_next_phase_agrees_with_effect_table` at `tests/workflow/test_transitions.py:212` verifies membership in a literal set, not agreement with the applied OVCAQ effect. Both can pass while their named product contracts regress.

## Tests inspected or run

- Confirmed clean exact HEAD `56b664fc44c359b0b97282aa2e116dbf9ed44ff9`.
- Inspected the complete `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..56b664fc44c359b0b97282aa2e116dbf9ed44ff9` range and every resulting changed production, documentation, and test file: 30 files, +4,239/−12.
- `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..56b664fc44c359b0b97282aa2e116dbf9ed44ff9`: passed.
- `.venv/bin/python -B -m pytest -p no:cacheprovider tests/workflow tests/packaging/test_installed_cli.py -q`: 167 passed in 1.22s.
- `/tmp` completion probe: command exits 0, current PRD remains in `wip`, absent from `done`, and selection returns it again.
- `/tmp` cap probe through validated `StateStore`: cap 2/cycle 2 `rework` committed cycle 3 with no pause.
- `/tmp` frontmatter probes: wrong-PRD application exited 0 and mutated the active PRD; cap 3→2 produced no overwrite warning.
- `/tmp` report probes: reversed conflicting operation IDs produced unequal renders; a schema-valid traversal batch ID published outside the runtime root.
- Packet verification noted, not rerun: full pytest 1,049 passed; ruff check and format check passed; mypy passed; `uv build` passed; `uv sync --all-groups` passed.

## Residual doubts

No unclassified claims. D11–D13 are explicitly KNOWN and non-blocking; D1–D10 require correction or required evidence before acceptance.
