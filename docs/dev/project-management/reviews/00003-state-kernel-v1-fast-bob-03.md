## Verdict: changes_requested

## Must fix

1. **High — programmatic oversized integers can be committed successfully, making state unreadable and unrestorable.**
   - `decode_json()` enforces `MAX_JSON_INTEGER_DIGITS = 640` at `src/ovcaq/state/schema.py:422-429`, but in-memory validation does not: `_require_integer()` at `:483-486` checks only type, and `_validate_json()` at `:515-521` accepts every integer.
   - Reproduction: initialize a store, then call `StateService(store).add_task({"id": 10**640, "name": "oversized"})`. It returns success at revision 1. Both subsequent `store.read()` and `store.restore()` raise `StateResourceLimitError`.
   - Independent rollover reproduction: a readable state with a 640-digit all-nines revision is accepted; the no-op transaction at `src/ovcaq/state/store.py:138-144` increments it to 641 digits and publishes it. The returned commit has 641 digits; reread fails with `state: JSON integer literal exceeds 640 digits`.
   - Violates the PRD’s total-validation requirement, validated/crash-safe writer contract, recovery requirement, and Phase B exit criterion forbidding invalid publication.
   - Required fix: enforce the same integer bound for decoded and programmatic values, including generated revisions and generic JSON values, and add service-level oversized-ID/value plus revision-rollover regressions.

## Can defer

1. **KNOWN — dependency cycles are accepted.** A two-task state with `1 -> 2` and `2 -> 1` validated successfully (`accepted [2] [1]`). The schema only enforces existing, unique, non-self blockers. Defer because the PRD explicitly excludes workflow-transition policy.

2. **KNOWN — oversized test structure.** Of 12,697 additions, 9,549 are tests. `tests/state/test_schema_invariants.py` is 747 lines and contains roughly 250–300 reducible lines duplicating TypedDict annotations and constants. The exhaustive behavioral matrix is justified; the declaration mirror can be compressed later.

3. **KNOWN — redundant impossible guard.** `_task_by_id()` re-runs `_require_task_id()` at `src/ovcaq/state/commands.py:74-75`, although all six callers validate the immutable integer before opening their transaction (`:177`, `:196`, `:219`, `:243`, `:262`, `:294`). Cleanup only.

4. **KNOWN — paraphrasing docstrings.** Examples include `src/ovcaq/state/schema.py:1,328-337` and `src/ovcaq/state/store.py:1,31-60`; they restate module/class names without explaining design rationale. Documentation cleanup only.

5. **KNOWN — self-confirming inventory tests.** `tests/test_packaging.py:128-153` repeats `SOURCE_SUITE_INVENTORY` keys manually, while `:156-178` largely verifies destination-file existence. These cannot independently prove the claimed source-suite completeness. The supplied behavioral suite reduces risk, so this is deferrable.

## Doubt audit

**Total: 8 — FIX: 1; VERIFY-dismissed: 2; KNOWN: 5.**

1. **Least confidence:** parity between text decoding and programmatic validation. Confirmed false by both integer reproductions; classified **FIX**.
2. **Assumptions checked:** cyclic in-memory JSON might hang iterative validation. A self-referential list returned `ResourceLimitError: state: JSON nesting exceeds safe decode limit 40`; **VERIFY-dismissed**. Artifact alias defenses were inspected at `src/ovcaq/state/store.py:455-480` and rerun; four focused hard-link tests passed; **VERIFY-dismissed**.
3. **Task completeness:** schema, crosswalk, store, paths, service, CLI, installed-wheel, durability, and packaging families are present, and supplied gates pass. Work is nevertheless incomplete because an accepted programmatic mutation can publish unreadable state.
4. **Practical failures:** the confirmed integer defect bricks read and restore. Dependency cycles are accepted but classified **KNOWN** because workflow policy is excluded. Concurrency, compare-and-set, failpoint, SIGINT, hard-link, and installed-CLI evidence otherwise covers the named risks.
5. **Different approach in retrospect:** retain the current layering, but establish a serialization-closure invariant early: every value accepted by `validate_state()` and every successful transaction must round-trip through canonical bytes and `decode_json()`.
6. **Missing validation:** no test supplies oversized integers through the Python service API, tests generated revision overflow, or asserts the general accepted-state → canonical bytes → decode/validate round trip. Existing integer tests cover textual JSON only.

## R1-R5 rubric

- **R1 — FAIL.** Net diff is 12,682 lines against 67 acceptance-criteria words: about **189×**. Against the full 978-word PRD it is about **13×**. Much is justified by the 184-row crosswalk and durability matrix, but the annotation mirror in `test_schema_invariants.py` and hand-maintained packaging inventory are concretely reducible.
- **R2 — FAIL.** `_task_by_id()` contains the impossible duplicate task-ID type guard described above.
- **R3 — PASS.** Apparent single-caller production abstractions retain present value: `ensure_project_config()` isolates configuration collision semantics; `StateService.validate()` is the required distinct command boundary; `_dispatch_attempt_command()` shares attempt/complete dispatch; store backup helpers normalize public error types.
- **R4 — FAIL.** Several module and exception docstrings merely paraphrase their identifiers, with exact examples listed under Can defer.
- **R5 — FAIL.** The source-suite inventory completeness and destination-existence tests are self-confirming/non-behavioral. Annotation-shape tests are not counted against R5 because closed schema shape is explicitly contractual; restore spies also assert durable outcomes rather than only mock calls.

## Tests inspected or run

- Inspected the complete 28-file diff for `9cda04a6a0279a6306c24015ee2d3173fb916e68..296e757cb96007a8c2079b0c4015f836b4fe4c2b`, plus allowed AGENTS.md and PRD 00003.
- Ran `mise exec -- uv run pytest tests/state/test_store.py -k hard_linked -q`: **4 passed, 28 deselected**.
- Ran four minimal read-only `/tmp`/in-memory reproductions: oversized service task ID, revision rollover, cyclic JSON, and cyclic task dependencies.
- Coordinator evidence at exact HEAD: **850/850 pytest passed**, ruff, formatting, mypy, build, diff-check, installed CLI, durability, SIGINT, integer-text, task-ID, and hard-link regressions all passed.
- Final `git status --short`: clean.

## Residual doubts

No unclassified doubts. After fixing integer validation/round-trip closure, only the explicitly deferred workflow-policy and de-slop items remain.
