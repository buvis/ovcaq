| Consensus | Severity | Issue | File | Task | Found By |
|-----------|----------|-------|------|------|----------|
| [2/3] | 🟡 | Report, audit, and final-state archive publication can succeed after their output directory is replaced, returning a path that does not exist; retain and recheck directory identity through publication and successful return | src/ovcaq/workflow/reports.py:499 | P02-T08 | ALICE, BOB |
| [1/3] | 🟠 | Frontmatter application discards catchup/design controls instead of committing their effective policy. `catchup: skip` leaves resume targeting catchup; `catchup: force` leaves completed catchup skipped. Only the review cap and tier floor persist, so subsequent applications also cannot report overwrites of the discarded controls. | src/ovcaq/workflow/frontmatter.py:191 | P02-T02 | BLAKE |
| [1/3] | 🟠 | B1: Missing PRD creates an unrecoverable null-artifact intent that fences every public state mutation | src/ovcaq/workflow/records.py:559 | P02-T07 | BOB |
| [1/3] | 🟡 | Deeply nested project or user TOML raises uncaught RecursionError, breaking the JSON CLI error contract; bound parsing and translate resource exhaustion into a contextual symbolic error | src/ovcaq/config.py:47 | P02-T09 | ALICE |
| [1/3] | 🟡 | B3: Section removal and extraction duplicate the same heading-span scanner | src/ovcaq/workflow/reports.py:570 | P02-T08 | BOB |
| [1/3] | 🟡 | B4: Installed-command helpers duplicate identical subprocess invocation logic | tests/packaging/packaging_support.py:162 | general | BOB |
| [1/3] | 🟡 | B6: Retained inherited collision test contains the mechanically identified OR assertion | tests/state/test_cli.py:372 | general | BOB |
| [1/3] | ⚪ | B5: Cannot statically verify test, lint, formatting, type-check and build execution; coordinator reports fresh passing gates | N/A | general | BOB |
| [1/3] | ⚪ | B7: Retained inherited StateService.add_task exceeds the function limit at 53 lines | src/ovcaq/state/commands.py:148 | general | BOB |
| [1/3] | ⚪ | B8: Lightly changed inherited schema module exceeds the file limit at 933 lines | src/ovcaq/state/schema.py:1 | general | BOB |
| [1/3] | ⚪ | B9: Comprehensive implementation-base fail-first binding remains unproven | N/A | general | BOB |
