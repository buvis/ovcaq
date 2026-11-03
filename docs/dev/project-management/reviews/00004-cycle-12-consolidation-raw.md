| Consensus | Severity | Issue | File | Task | Found By |
|-----------|----------|-------|------|------|----------|
| [1/3] | 🟡 | F1: Report publication contention reuses the deferred ledger's message and the generic state_io code, so a supervisor can only tell "retry me" from a real disk failure by string-matching the word "retry" | src/ovcaq/workflow/_files.py:75 | P02-T08 | BOB |
| [1/3] | 🟡 | F2: _ensure_directory_chain dropped exist_ok, so a peer creating the same missing runtime ancestor makes defer fail with a bare FileExistsError; the sibling helper paths.ensure_runtime_directory:102 handles that case | src/ovcaq/workflow/_files.py:265 | P02-T06 | BOB |
| [1/3] | 🟡 | F3: Assertion cannot fail as written: delegated_calls counts every fsync and directories counts a labeled subset, so the inequality holds by construction | tests/packaging/test_rework_11.py:278 | P02-T06 | BOB |
| [1/3] | 🟡 | F4: reports.publish_report has no production caller; workflow_cli reaches into the module-private reports._publish_report instead | src/ovcaq/workflow/reports.py:676 | P02-T08 | BOB |
| [1/3] | 🟡 | R8-K1: inherited config-collision test retains the mechanically flagged either-or assertion | tests/state/test_cli.py:372 | general | BOB |
| [1/3] | ⚪ | F5: FSYNC_SCENARIO emits state_changed_while_interrupted; no assertion reads it | tests/packaging/rework_11_scripts.py:202 | P02-T06 | BOB |
| [1/3] | ⚪ | V1: Cannot statically verify: suite, ruff, format, mypy, and build gates at the reviewed head | N/A | general | BOB |
| [1/3] | ⚪ | K1: A ledger written past the reader's depth limit by a pre-fix build stays unreadable and unappendable; the repair is prospective only | src/ovcaq/workflow/_files.py:82 | P02-T06 | BOB |
| [1/3] | ⚪ | K2: render report requires runtime_root to already exist while defer now creates its chain | src/ovcaq/workflow/reports.py:507 | P02-T08 | BOB |
| [1/3] | ⚪ | R8-K2: inherited 53-line add_task and three unchanged packaging functions exceed R12 | src/ovcaq/state/commands.py:148 | general | BOB |
| [1/3] | ⚪ | R9-K3: inherited state schema remains 933 lines, over R13 | src/ovcaq/state/schema.py:1 | general | BOB |
| [1/3] | ⚪ | R9-K4: universal implementation-base fail-first binding remains unproven; this cycle's replay was skipped outright (worktree creation denied) | N/A | general | BOB |
