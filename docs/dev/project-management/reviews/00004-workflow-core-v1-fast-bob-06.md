# Bob — doubt plus de-slop

## Verdict

changes_requested

## Must fix

1. **High — `stall` can silently finish an interrupted `park` for the same PRD.**
   - Evidence: `records.py:666-680` validates only the PRD when an operation already exists; it does not compare operation kind, site, or detail. Reproduction: interrupt `park` at `AFTER_INTENT_BEFORE_MOVE`, then invoke `stall` for the same PRD. Result: `{"requested": "stall", "result_kind": "park", "parks_consecutive": 1}`.
   - Existing tests cover exact committed replay and `park` intentionally reconciling a pending stall, but not the inverse in-flight kind conflict.
   - Violates: explicit recovery-kind semantics, deterministic lifecycle commands, DEC-076 conflict refusal.
   - Required action: make `stall` require a matching pending stall identity—kind, PRD, site, and detail—while preserving the explicitly intended reconcile-any behavior of `park`. Add an in-flight conflicting-kind regression test.

2. **High — deferred-record publication is not bound to the verified configured directory.**
   - Evidence: `records.py:297-350` validates the deferred path, but `_write_record_file` at `239-268` later operates by pathname. At `AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC`, replacing `root/deferred` with a new directory produced: `{"returned_exists": false, "relocated_exists": true, "configured_dir_empty": true}`.
   - The function returned success and fsynced the replacement directory, while the record existed only in the renamed directory. The saga may then advance to committed state and clear recovery.
   - WIP and hold identity are correctly reverified at both late boundaries; this equivalent protection is missing for the publication directory.
   - Violates: P02-T06/P02-T07 durability requirements and the exit criterion that interruption cannot lose work or records.
   - Required action: bind record creation/replacement/fsync to an opened, verified deferred-directory descriptor and reverify configured-path identity before advancing recovery and before final commit. Test replacement at the post-replace and post-append late boundaries.

3. **Medium — mandatory TEST-062 legacy/mixed completed-record behavior was not migrated.**
   - Evidence: `reports.py:303-319` directly indexes every completed-record field. A retained row missing `tasks_completed` raises uncaught `KeyError` rather than yielding unknown summary values.
   - Tests cover complete nonzero rows, empty legitimate zeros, and incomplete metrics rows, but not incomplete `completed_prds` rows.
   - Violates: migration row TEST-062, whose retained contract explicitly requires nonzero values, legitimate empty zeros, and unknown sums for legacy or mixed records. Phase-0 reconciliation marks it mandatory with no scope change.
   - Required action: add a tolerant completed-record projection that renders unknown totals for mixed/incomplete rows without weakening persisted-state validation, plus the migrated characterization test.

## Can defer

- **Low — redundant impossible guard:** `records.py:473` checks `source_stat is None` inside `if source_exists`, where `source_exists` was defined as `source_stat is not None`. Remove it during cleanup.
- **Low — unjustified single-caller abstraction:** `cli.py:561-564` defines `_workflow_context`, used only once at line 615, and introduces an `Any` return component. Inline it or give it a real reusable typed responsibility.

## Doubt audit

12 doubts examined: **5 FIX, 6 VERIFY-resolved/dismissed, 1 KNOWN**.

1. Pending recovery kind/payload conflicts may be accepted — **FIX**, confirmed; must-fix #1.
2. Deferred-directory identity may change after publication — **FIX**, reproduced; must-fix #2.
3. Retained incomplete completed rows may not render unknown totals — **FIX**, reproduced; must-fix #3.
4. WIP/hold identity may be lost after publication or at either late failpoint — **VERIFY-resolved**. `_verify_moved_artifact` runs before publication, after publication, and immediately after the late hook before commit; both WIP and hold replacement tests passed.
5. Metrics may mix batches, parse provider output, or mishandle zero/incomplete metric rows — **VERIFY-resolved**. Exact active-batch filtering is present, provider-neutral metric rows are consumed directly, empty totals remain zero, and missing metric components become unknown.
6. Control characters or missing report sections may escape as `StopIteration`/partial publication — **VERIFY-resolved**. Identifiers reject nonprintable characters, section lookup uses `next(..., None)`, failures become domain errors, and previous output remains intact.
7. Recovery mutations may bypass fencing or violate state durability order — **VERIFY-resolved**. Public state mutations enforce the recovery fence inside the store transaction; restore checks its precondition under the exclusive lock.
8. Documentation may drift from CLI behavior or shared workflow code may contain provider policy — **VERIFY-resolved**. Command docs are parser-generated and provider-boundary tests pass; no provider identifiers were found in production workflow modules.
9. Repeated exact `complete-prd` requests may duplicate summaries — **VERIFY-dismissed**. Exact repeats preserve revision and do not append another completion.
10. Available model-tier resolution is not wired through the current CLI — **KNOWN**. The pure frontmatter API accepts the tier map; configuration ownership and CLI integration belong to the subsequent configuration/runtime PRD.
11. The `source_stat is None` branch may be defensive dead code — **FIX**, confirmed; low-priority cleanup above.
12. `_workflow_context` may be unjustified indirection — **FIX**, confirmed; low-priority cleanup above.

## R1–R5 rubric

- **R1 PASS — production bloat/reducible complexity:** The roughly 2.5K production-line expansion is proportionate to ten workflow tasks, durable sagas, reporting, CLI integration, and confinement checks. No large removable subsystem or compatibility layer was found.
- **R2 FAIL — defensive-impossibility guards:** `records.py:473` contains a provably redundant `source_stat is None` branch.
- **R3 FAIL — unjustified single-caller abstractions:** `_workflow_context` is a one-use wrapper that adds indirection and weakens typing.
- **R4 PASS — comments/docstrings paraphrasing code:** Documentation is concise and primarily communicates contracts, durability intent, or public API purpose; no material narrative duplication was found.
- **R5 PASS — tests of framework/mocks instead of OVCAQ behavior:** Tests predominantly exercise real state stores, filesystem identities, subprocess/package behavior, and rendered output. The three gaps above are missing OVCAQ behavior cases, not mock-centric false confidence.

## Tests inspected or run

- Verified clean worktree and exact HEAD `c4b9ea38d2e11eac4a1de1a71bd7d4134142e661`.
- Inspected the complete PRD range and every changed production file, with full scrutiny of `records.py`, `reports.py`, CLI/state changes, workflow modules, generated documentation, migration rows, characterization items, fixtures, and relevant tests.
- Ran 26 focused tests covering recovery collision/reconciliation, both lifecycle identity replacements, report metrics, empty and incomplete metrics, control characters, parser-generated docs, and mutation fencing: **26 passed in 0.30s**.
- Ran three isolated temporary-directory reproductions for pending-kind confusion, deferred-directory replacement, and incomplete completed-record reporting.
- Coordinator evidence accepted: targeted **73 passed in 3.02s**; full pytest **1108 passed in 11.87s**; `uv sync`, Ruff check/format, mypy over 47 files, build, full-range diff-check, and exact plan digest all passed.

## Residual doubts

The available-tier map remains an intentional integration seam until the configuration/runtime PRD. After the must-fixes, rerun the two late publication identity scenarios against both direct record writing and the full saga, since that is where the current durability proof is weakest.
