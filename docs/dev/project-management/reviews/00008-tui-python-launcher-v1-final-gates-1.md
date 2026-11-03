# Final repair gates

Product HEAD: e90ce6bea414a775b008d5098b746a2e44dee3ef. Read-only checks after all formatting; no source edits followed.

style_gate: clean (exit 0), all 20 changed Python files from cce42f8..e90ce6b.
split_hygiene: failed: five existing exported bindings flagged by the file-local checker (exit 1). Both mandatory deletion-only full-persona Ivan passes verified importing consumers, made no changes, and returned no assumptions. These findings are retained, never silently reported clean.

Raw checker output:

```text
UNUSED | /Users/bob/git/src/github.com/buvis/ovcaq/tests/packaging/packaging_support.py:12 | PROJECT_ROOT | module-level binding never read in this file
UNUSED | /Users/bob/git/src/github.com/buvis/ovcaq/tests/packaging/packaging_support.py:98 | DECLARED_PACKAGE_MEMBERS | module-level binding never read in this file
UNUSED | /Users/bob/git/src/github.com/buvis/ovcaq/tests/packaging/packaging_support.py:99 | DECLARED_RESOURCE_MEMBERS | module-level binding never read in this file
UNUSED | /Users/bob/git/src/github.com/buvis/ovcaq/tests/state/test_commands.py:32 | T2 | module-level binding never read in this file
UNUSED | /Users/bob/git/src/github.com/buvis/ovcaq/tests/state/test_commands.py:458 | ERROR_CODES | module-level binding never read in this file
```

Consumers:

```text
tests/state/test_commands.py:32:T2 = "2026-08-26T10:02:00Z"
tests/state/test_commands.py:458:ERROR_CODES = (
tests/state/test_cli.py:15:    ERROR_CODES,
tests/state/test_cli.py:106:    assert tuple(error.value for error in ErrorCode) == ERROR_CODES
tests/state/test_schema_invariants.py:81:    T2,
tests/state/test_schema_invariants.py:710:                        finished_at=T2,
tests/state/test_schema_invariants.py:722:                    _capability_attempt("failed", finished_at=T2),
tests/state/test_schema_invariants.py:738:                    _capability_attempt("succeeded", started_at=T2, finished_at=T1)
tests/state/test_service_commands.py:11:    T2,
tests/state/test_service_commands.py:380:            _attempt(2, outcome="review_flagged", started_at=T1, finished_at=T2),
tests/state/test_service_commands.py:381:            _attempt(3, outcome="completed", started_at=T2, finished_at=T2),
tests/state/test_service_commands.py:395:            _attempt(2, outcome="rework_failed", started_at=T1, finished_at=T2),
tests/state/test_service_commands.py:396:            _attempt(3, outcome="completed", started_at=T2, finished_at=T2),
tests/state/test_schema.py:156:T2 = "2026-08-26T10:02:00Z"
tests/state/test_schema.py:198:                            "finished_at": T2,
tests/state/test_schema.py:294:            "decided_at": T2,
tests/state/test_schema.py:319:                    "created_at": T2,
tests/state/test_schema.py:347:        "created_at": T2,
```

Packaging consumers: test_distribution.py imports PROJECT_ROOT, DECLARED_PACKAGE_MEMBERS, and DECLARED_RESOURCE_MEMBERS at lines 22-24 and reads them at 178, 246, 385-386, 472-473. Details and raw agent reports remain in final-fix-1-task-2.md and final-fix-1-task-4.md.

All final-regression commit reflow checks returned 0 except task 11, whose one-comment/one-hunk lint commit was inspected retrospectively; original repair-task-7 and repair-task-10 report their 26/32-hunk tripwire findings. No unsafe deletion was made to satisfy checker limitations.

State attempt stamping initially used invalid dotted array indices and was rejected before mutation; verified bracket-index paths succeeded through the same state CLI. No state file was edited directly.
