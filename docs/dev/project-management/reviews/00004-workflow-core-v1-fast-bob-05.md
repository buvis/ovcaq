# Bob doubt + de-slop review — FT-04R5 cycle 05

## Isolation and reviewed material

- Reviewer: Bob, isolated doubt plus de-slop lens.
- Reviewed HEAD: `c512a4ad7d67af75b413ee8c9612b088d21fb4f4` (verified before review; no checkout or commit switch).
- Complete reviewed range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c512a4ad7d67af75b413ee8c9612b088d21fb4f4`.
- Scope inspected: `AGENTS.md`, PRD 00004, the complete 40-file range diff, every changed workflow implementation and changed hunk in state/CLI/docs/tests, all current workflow tests and fixtures, and the necessary state schema/store/path/config layers.
- Isolation preserved: I did not read implementation plans, coverage/discovery documents, fast-track handoffs, commit messages/logs, any prior review, or any other reviewer output.
- Mutation discipline: no implementation, test, PRD, plan, state, capsule, or autopilot file was changed. This raw report is the only repository write.

## Verdict

**FAIL.** The implementation is impressively well tested at the behavior it currently defines, but four workflow-contract gaps remain reproducible: the review cap is dead data, installed frontmatter cannot resolve a valid tier map, non-cap frontmatter policy is not durable for state-only resume, and defer publication is not bound atomically to the state snapshot it attributes. A fifth input-safety bug allows a valid state/filename to corrupt report section structure. The explicit de-slop rubric also fails R1–R4.

## Ordered must-fix recommendations

1. **Enforce `review.cap` in the review transition and commit the cap-pause effect atomically.** `src/ovcaq/workflow/transitions.py:40-49` increments `review.cycle` for every `rework` without reading `review.cap`; the only cap behavior in the package is `resume.py:17-21`, which can describe a `review_cap` pause only after some other actor has already created it. Reproduction with `cycle=2, cap=2` produced `cycle=3`, `phase=review`, and `pause_reason=None`. The PRD's durable rework-cap policy therefore has no decision point. Add the boundary/rejection or pause row and row-by-row tests at below/at/above cap.

2. **Make installed frontmatter tier resolution reachable.** `frontmatter.parse` correctly accepts `available_tiers`, but `_dispatch_workflow` calls `apply_to_store` at `src/ovcaq/cli.py:611-616` without that argument. Therefore every installed `default_model` hint follows `frontmatter.py:126-134` to “unavailable,” even when the active agent has that abstract tier. Direct reproduction of the same call shape returned defaults plus `tier 'deep' is unavailable`. Wire the active agent's configured tier map into the command boundary and add installed/in-process CLI coverage for an available and unavailable tier.

3. **Bind defer intent/publication to one durable state decision.** `defer_record` reads/validates active PRD and batch at `src/ovcaq/workflow/records.py:201-209`, releases the state lock, then publishes at line 210 under only the deferred-file lock. An interleaving can change `work.prd`, `batch.id`, or start recovery between those actions. A controlled interleaving changed the current PRD to `00005-runtime.md` after `read()` and the function still published a record attributed to `00004-workflow-core-v1.md`/`batch-1`. The schema's `RecoveryKind` at `state/schema.py:59` also excludes defer, so there is no durable `recovery.operation` intent for this saga. Introduce a state-bound defer operation/revision protocol and tests that race defer against phase/reset/selection/recovery mutations.

4. **Persist or otherwise reconstruct non-cap frontmatter policy before state-only resume.** `apply_to_store` returns `catchup_mode`, `design_mode`, `design_gate`, and `pause_on_ambiguity`, but its transaction at `frontmatter.py:183-189` commits only `review.cap`, an ownership marker, and (when reachable) the tier floor; it actively removes the four policy extension keys. An in-memory application of all directives returned the requested effective fields while committed `batch.catchup`, `work.design_doc`, and `control.pause_reason` remained indistinguishable from defaults. `resume_target` reads only committed state, so a restart between frontmatter application and the next action loses these decisions. Either give these policies durable v1 owners or prove/retest a deterministic reparse on every resume before the state-only decision.

5. **Reject control characters in path-safe/report-heading identifiers.** `_require_component` at `reports.py:205-215` accepts newline characters. The v1 schema also accepts them, and selection accepts a POSIX filename such as `00004-safe\n## Injected.md`. Reproduction validated that state and component, then `render_report` emitted three level-two headings: the intended prefix, injected heading, and batch summary. This can break `_updated_report` section replacement and corrupt deterministic output. Apply a shared conservative component grammar to PRD names, batch IDs, and operation IDs and test newlines/control characters.

6. **Remove the impossible `source_stat is None` branch.** In `records.py:478-483`, `source_exists` is defined as `source_stat is not None`, then inside `if source_exists` the code tests `source_stat is None` again. The first disjunct cannot occur and obscures the real regular-file guard.

7. **Collapse `_workflow_context` and reuse the already-resolved paths.** `cli.py:602` resolves lifecycle paths, then the sole caller invokes `_workflow_context` at line 607, whose lines 561-564 resolve the same paths again. The three-line single-caller abstraction adds duplication without testability or architectural separation. Construct the store/runtime root inline and reuse `paths`.

8. **Trim duplicated installed-CLI setup while retaining boundary coverage.** The range adds 507 lines to `tests/packaging/test_installed_cli.py`, including six embedded Python state-initialization scripts (`127-141`, `194-216`, `268-283`, `349-398`, `468-477`, `527-540`) that repeat fixtures and semantics already exercised in workflow/state tests. Keep installed-wheel isolation plus one happy and one failure path per serialization/package boundary, and move reusable state setup behind a small installed test helper. A reduction of roughly 200–300 lines should preserve the unique packaging signal.

9. **Delete paraphrasing docstrings.** Examples that add no contract or rationale are `frontmatter.py:42`, `records.py:82`, `reports.py:377`, and `selection.py:57`. Keep docstrings that state non-obvious durability, purity, or security behavior; remove restatements of the symbol name and fields.

## Can-defer / KNOWN items

1. **Report publication can be stale relative to a concurrent state mutation.** Render commands take one validated snapshot, then publish outside the state lock. This is acceptable in this PRD because reports are explicitly projections rather than durable authority; a later render converges. If consumers ever require revision-coherent report artifacts, carry the revision into filenames/content or add snapshot publication coordination.
2. **Exact minimum-runtime execution was not exercised.** The available project venv runs Python 3.13.13. I did compile all 47 source files with mise Python 3.12 successfully, but did not create another environment to rerun all 1,095 tests. This is a validation limitation, not evidence of a current defect.

## Six-question doubt audit

### 1. What is least certain?

- The state/file atomicity of defer was least certain; inspection and a forced interleaving confirmed the attribution race (**VERIFY -> FIX**, item 3).
- The meaning and enforcement point of `review.cap` was uncertain; whole-package search plus a boundary reproduction confirmed it is written but never consumed (**VERIFY -> FIX**, item 1).
- Frontmatter/runtime integration was uncertain; command-path inspection confirmed that available tier maps never reach the installed command and that several effective fields disappear from committed state (**VERIFY -> FIX**, items 2 and 4).

### 2. Which assumptions might be wrong?

- Assumption “the state snapshot stays authoritative until defer publication” was wrong; the controlled interleaving published the old attribution after current state changed (**FIX**).
- Assumption “the installed command obtains active tier configuration” was wrong; no config/tier argument reaches `apply_to_store` (**FIX**).
- Assumption “path-safe component also means safe Markdown heading” was wrong; newline is accepted and creates an injected section (**FIX**).
- Assumption “the lifecycle path service is hardcoded” was checked and dismissed: `resolve_lifecycle_paths` accepts relative or absolute configured roots and workflow source contains no legacy runtime-root string. The installed CLI intentionally supplies the current default, though a future operator-configurable root should reuse this API (**VERIFY dismissed**).

### 3. Is the PRD fully complete?

No. Selection ordering/hold exclusion, plan shape, transition row closure, reset/completion summaries, park/stall durable replay, deterministic projections, parser-derived docs, and layer/string guards are present. The cap decision is absent, defer lacks the required state-bound recovery protocol, and installed tier resolution is unreachable. State-only recovery of the other frontmatter policies is also incomplete (**FIX**, items 1–4).

### 4. What can fail in practice?

- Rework can continue beyond the configured cap instead of pausing.
- A defer record can be written into the prior batch/PRD ledger during a concurrent transition or selection.
- Every installed `default_model` hint is discarded as unavailable.
- A crash/restart after applying frontmatter can change catchup/design/ambiguity behavior because the returned projection is gone.
- A legal POSIX PRD filename containing a newline can corrupt report structure and later section replacement.
- I checked park/stall interruptions, symlink swaps, atomic publication, active-recovery mutation fencing, exact replay, and kind collision through the focused/full suites; those doubts were dismissed by passing real-filesystem tests (**VERIFY dismissed**).

### 5. What should be approached differently?

Define the complete durable workflow decision model first: frontmatter application should map every restart-relevant value to an explicit state owner, and every state-attributed filesystem record should have an intent/revision handshake. Then transitions consume that model, and CLI only adapts inputs/config. Structurally, reuse the resolved command context and central publication primitives rather than adding local wrappers. The current park/stall descriptor-based design survived scrutiny and should remain.

### 6. Which validations are missing?

- At/beyond-cap rework transition and atomic `review_cap` pause tests.
- Installed CLI available-tier resolution test.
- Restart/resume test after frontmatter application for catchup/design/gate/ambiguity directives.
- Defer-vs-state-mutation interleaving test and crash tests for a durable defer intent.
- Newline/control-character tests for PRD, batch, and operation identifiers.
- The exact Python 3.12 full suite remains KNOWN; 3.12 syntax compilation passed.

## Doubt totals and actions

- Total concrete doubts: **13**.
- **FIX confirmed: 9** — ordered must-fix items 1–9 above. Per the explicit review-only constraint I changed no code; each is a recommendation backed by inspection or reproduction.
- **VERIFY dismissed: 2** — configurable lifecycle path resolution works without legacy coupling; park/stall durability and recovery fencing survived focused and full real-filesystem tests.
- **KNOWN: 2** — projection freshness under concurrency is non-authoritative/by design; exact 3.12 full-runtime execution was not run.
- Fixed in this review: **0** (review-only mandate).

## Explicit de-slop rubric

### R1 — Bloat ratio/diff proportionality: FAIL

The range is +6,094/-33, net +6,061 lines against 66 words in the PRD acceptance-criteria section (~91.8x). Breakdown: +2,224 net source, +3,806 net tests/fixtures, +31 net docs. The PRD is broad and durability justifies substantial tests, but the 507-line installed-CLI addition duplicates state construction and behavior already covered in `tests/workflow/test_sagas.py` and `test_workflow_cli.py`. The six embedded initializer scripts are concrete removable bulk; retain unique installed-wheel and subprocess serialization coverage while reducing approximately 200–300 lines.

### R2 — Defensive impossibility: FAIL

`records.py:478` computes `source_exists = source_stat is not None`; inside `if source_exists`, line 483 checks `source_stat is None` again. That state is impossible on the same local value. Remove the redundant disjunct and keep the regular-file test.

### R3 — Unjustified single-caller abstraction: FAIL

`cli.py:561-564` defines `_workflow_context`, used only at line 607. It merely constructs a store, resolves paths, and returns the runtime root; worse, its caller already resolved the same paths at line 602. Inline the two remaining constructors and reuse `paths`.

### R4 — Comment/docstring paraphrasing: FAIL

Concrete examples are `FrontmatterApplication` (“The committed state and effective frontmatter projection”), `SagaResult` (“The committed result of a stall or park operation”), `publish_audit` (“Publish the deterministic active-PRD audit”), and `select_from_paths` (“Read the two selectable lifecycle directories and apply select”). These restate names/fields without explaining why or a non-obvious constraint.

### R5 — Framework/mock/shape-only tests: PASS

No mock-confirming test was found. Monkeypatches observe required durability ordering or force real failure boundaries, and assertions also inspect state/filesystem outcomes. Parser/module/installed-wheel shape checks correspond to explicit command-registry, layering, and packaging contracts. Golden tests compare the product's render contract, not incidental framework output.

Concrete slop candidates found: four categories (R1 duplicated installed setup, R2 impossible guard, R3 duplicate single-caller context, R4 paraphrasing docstrings), satisfying the nontrivial-range requirement.

## Checks and reproductions

- Focused workflow/state command suite: **265 passed**.
- Full suite outside sandbox (required for Unix sockets and offline `uv` cache): **1,095 passed**.
- `ruff check --no-cache .`: **passed**.
- `ruff format --check --no-cache .`: **92 files already formatted**.
- `mypy --no-incremental src/ovcaq`: **passed, 47 source files**.
- `git diff --check` for the exact range: **passed**.
- Python 3.12 `compile()` over all source files: **47 compiled**.
- Frontmatter persistence reproduction: requested skip/gate/ambiguity fields were returned, but committed state retained only tier floor and review cap.
- Cap reproduction: `cycle=2, cap=2` plus `rework` produced cycle 3 without pause.
- Defer interleaving reproduction: current PRD changed before publication, but old PRD/batch attribution was still accepted.
- Heading reproduction: schema/component accepted `00004-safe\n## Injected.md`; renderer emitted the injected level-two heading.

## Residual doubts

- The PRD delegates detailed acceptance to prohibited source documents, so this isolated pass could not compare subtle legacy wording beyond the PRD and allowed characterized tests. The missing live uses of `review.cap` and tier mapping are nevertheless directly observable package-wide.
- `complete_prd_in_store` is logically duplicate-free but increments revision on exact replay. I did not classify this as a defect because the state store treats every successful transaction as a new revision and the current tests explicitly define that behavior; clarify byte-idempotence before changing it.
- Renderer output files use a strong descriptor-based publication path while deferred records use a weaker path check before opening their lock. I did not add a separate must-fix beyond item 3 because a state-bound defer protocol should define and test the complete publication boundary, including parent-directory identity.
