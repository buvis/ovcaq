---
session: FT-04R7
review: 7
reviewer: alice
head_sha: 47a8764760e1fedb82eb1514a344584fb7ad2f3e
runner: native-isolated-codex-subagent
---

# Alice — cycle-07 lens report

The following is the reviewer's final text, preserved without coordinator revisions.

[ALICE] 🟠 Must fix: saga verification runs before StateStore publication. Replacing deferred, WIP, or hold at BACKUP_TEMP_FSYNCED while recovery is recorded still permits successful commit, clearing recovery and tasks despite missing configured evidence. Preserve verification through durable commit; add publication-boundary regressions. | File: src/ovcaq/workflow/records.py:696 | Task: P02-T07
[ALICE] 🟠 Must fix: batch identity validation occurs after filesystem effects. With batch.id="../escape", stall moves the PRD and commits recovery.step="moved" before rejecting the identifier; retries remain blocked and public state mutations are fenced. Missing batch identity also creates hold before refusal. Validate batch identity before opening or creating lifecycle directories, as DEC-076 requires. | File: src/ovcaq/workflow/records.py:766 | Task: P02-T07
[ALICE] 🟡 Must fix: load_metric_rows uses blocking Path.read_text. A FIFO at metrics.jsonl hangs both render metrics and render report indefinitely, bypassing the repaired nonregular-output refusal. Open metric input nonblocking and reject nonregular files, with bounded CLI regressions. | File: src/ovcaq/workflow/reports.py:133 | Task: P02-T08
[ALICE] 🟡 Must fix: the second consecutive park commits systemic_halt=True but the CLI returns ordinary success, exit 0. DEC-082 requires a halt code; human output currently exposes only the revision. Preserve a distinct halt outcome through dispatch and test the installed command. | File: src/ovcaq/cli.py:682 | Task: P02-T07
[ALICE] 🟡 Simplification: supplied mechanical counts show _execute_operation at 169 lines and _dispatch_workflow at 109, exceeding the 50-line rule. Extract intent preparation and saga step execution, and split CLI verbs into handlers while preserving parser authority and named failpoints. | File: src/ovcaq/workflow/records.py:728 | Task: general
[ALICE] 🟡 Simplification: records.py has 955 lines and test_sagas.py has 1,201, exceeding the 800-line rule. Separate deferred-ledger I/O from saga orchestration and split defer tests from park/stall tests along those existing boundaries. | File: src/ovcaq/workflow/records.py:1 | Task: general
R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: pass
R11: pass
R12: fail
R13: fail
