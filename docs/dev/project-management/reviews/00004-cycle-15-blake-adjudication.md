Source-only adjudication supplement; the original raw report remains unchanged.

- Frontmatter finding: **retracted**. The frozen v1 crosswalk explicitly classifies `catchup_mode`, `design_mode`, `design_gate`, and `pause_on_ambiguity` as derived values represented by `batch.catchup`, `work.design_doc`, and `control.pause_reason`; it forbids duplicating them as durable policy fields. `RecoveryKind` and the schema provide no alternate frontmatter owner. Returning parsed effective values while committing only owned fields matches that contract. Evidence: `docs/state-protocol.md:321-323,327`; `tests/characterization/current_system.toml:1140-1192`.

- Selection finding: **retracted**. No mandatory source says missing, invalid, or symlink lifecycle directories must raise. The frozen characterization requires WIP priority, backlog fallback, drain, and hold exclusion; the PRD test strategy merely names absent/invalid-directory cases without assigning error outcomes. The implementation’s explicit empty-input behavior is therefore compliant. A `PermissionError` from `iterdir()` is distinct: it is not caught and propagates rather than becoming an empty directory. Evidence: `tests/characterization/current_system.toml:742-756,2706-2711,4546-4551`; `src/ovcaq/workflow/selection.py:31-47`.

- Defer finding: **retracted**. The frozen command contract defines standalone defer as appending a PRD-attributed object to a per-batch ledger. The ledger is independently locked, and operation IDs provide replay deduplication. Durable `recovery.operation` is structurally limited to `park` and `stall`; requiring a defer recovery intent or state CAS would contradict the accepted schema. The batch and PRD captured by the validated read intentionally identify immutable output for that invocation, so later state progress does not retroactively misattribute it. Evidence: `tests/characterization/current_system.toml:724-728,1996-2010,2548-2560`; `src/ovcaq/state/schema.py:59,257-269`.

Corrected verdicts:

B1: pass
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: pass
B16: pass
B17: pass
B18: pass
B19: pass

Corrected source-task coverage: P02-T01–P02-T10 pass.

Corrected phase-exit coverage: Phases A, B, and C pass.
