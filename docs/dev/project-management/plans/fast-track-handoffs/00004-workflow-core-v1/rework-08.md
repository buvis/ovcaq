# FT-04F8 — PRD 00004 repair handoff

Date: 2026-09-05 13:19 CEST. Repairs committed; fresh FT-04R9 completion review
remains pending. This repair session did not run completion review.

## Exact state

- Repository: `/Users/bob/git/src/github.com/buvis/ovcaq`, branch `master`.
- Verified clean starting HEAD: `8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`.
- Repair HEAD: `78f916c366f74105b76e6f07d80a7a1aeb251e9f`.
- Commit: `fix(workflow): preserve recovery identity and durable records`.
- Full implementation base: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`.
- Repair diff: 36 files, +1454/-1021. Final Git status and stash list empty;
  only the original checkout is registered as a worktree.
- PRD remains `dev/local/prds/wip/00004-workflow-core-v1.md`.
- Authoritative findings: `dev/local/reviews/00004-workflow-core-v1-fast-review-08.md`
  and its `-evidence.md` companion. No older review histories were reopened.

## Repairs and retained regressions

| Root | Repair | Regression evidence |
|---|---|---|
| R8-01 | Deferred reads use the guarded state decoder before structural validation. Duplicate keys fail with contextual usage errors; excessive nesting keeps the resource-limit error. | `test_ledger_integrity.py`: root/item duplicates and deep nesting for append/load, byte preservation. `test_input_integrity.py`: installed defer/report reject duplicate/deep ledgers without state or ledger changes; exits 1/11, symbolic JSON errors. |
| R8-02 | Recovery intent stores the original source's device/inode before moving. Checks use that durable identity before/after rename and throughout moved/recorded publication and restart. | `test_saga_artifacts.py`: stall/park source substitution, post-rename substitution, and fresh-StateStore replay after intent/moved/recorded interruptions. Every conflict retains tasks/intent; restoring the original inode reconciles once and exact replay preserves bytes. |
| R8-03 | The sidecar lock context supplies an ownership check used before read/modify, immediately before ledger replacement, through durability/replay, and in saga publication guards. | `test_ledger_integrity.py`: all three defer boundaries with nested and real-process competing writers. Original call refuses, the successful competing append survives, and retry preserves both records. |
| R8-04 | Batch Summary reconstructs one deferred table for the complete batch with explicit PRD attribution. Current and historical lifecycle sections remain replaceable. | `test_report_recovery.py`: first rendering with earlier/current records, duplicates, input reordering, changed detail, next PRD, and byte-identical rerender. The golden report retains every prior field and adds PRD attribution. |
| R8-05 | Each opened publication component syncs its verified parent even on existing-directory retry; identical payload replay syncs the output directory. | `test_report_recovery.py`: report/audit/archive creation, failed directory creation and retry, post-replace directory-fsync failure and identical-content retry. Nonregular output/path checks remain in the complete report suites. |
| R8-06 | Completion counts and audit rows share substantive decision filtering over ID/kind/summary/rationale/cycle; status/timestamp alone do not count. | `test_blank_decisions.py`: blank/whitespace rows across all statuses; string zero, numeric zero, and populated individual cells survive. Schema-valid blank and partially populated examples are retained. |
| R8-07 | Payload and project/user config reads open nonblockingly without following the final symlink and verify regular-file type before reading. | `test_input_integrity.py`: installed frontmatter/defer/project config/user config FIFOs without writers exit within two seconds with usage JSON and unchanged state. |
| R8-08 | Split independent CLI/render/state command cases, reuse installed-root and argv setup, separate installed-interpreter fixture programs, and extract coherent fixture/assertion helpers. | Complete workflow and packaging directories rerun. `test_service_commands.py` is 774 lines (962 before repair; 851 at implementation base). Workflow `records.py` is 783. Every new/changed workflow/packaging function is at most 50 lines; retained overlength cases are structurally unchanged from base. |

Regression paths above are under `tests/workflow/`, except installed tests under
`tests/packaging/`. New state modules are `tests/state/test_recovery_mutations.py`
and `test_service_contracts.py`; all original assertions are retained there.

The assertion-expression comparison across all tests found only explicit
renamings/shared checks: build/review completion refusals now use the same helper
at both original revisions; frontmatter uses the shared CLI invocation; the
replacement flag is returned by a closure; the exact intent assertion adds
`artifact: null` for the original missing-source failure case. No assertion was
dropped. The installed origin/module checks remain unchanged.

## Source contract and observable changes

P02-T01–P02-T10 and all 55 PRD-owned characterization rows were read from
`tests/characterization/current_system.toml` and `migration.toml`; the coverage
manifest and resolved discovery were read. Retain cycle-08's row-by-row evidence.
The full suite still covers terminal drain, conflicting stall refusal, legacy and
mixed unknown totals, equal-key ordering, active-batch metrics, explicit recovery
kind, lifecycle/ledger identity and publication fences, control-character refusal,
provider neutrality and parser-generated command documentation.

`RecoveryOperation.artifact` is a required nullable schema field documented in
`docs/state-protocol.md`. Null preserves missing-source failure evidence; it does
not authorize adopting a later replacement. A replaced artifact requires restoring
the original before reconciliation. This is a pre-stability schema extension;
no importer, compatibility shim or second state writer was added.

Deferred details now appear once in the batch summary, including PRDs that were
never rendered while active. Named symlinks/nonregular payload and config inputs
refuse promptly. Blank metadata-only decisions no longer affect summaries/audits.

R8-K1 and R8-K2 remain inherited KNOWN observations; they are not repaired here.
Linux qualification and downstream runtime/provider configuration retain their
owners. Durability evidence is syscall/failpoint evidence, not a power-loss test.

## Observed verification

All commands below ran during this repair session on Darwin, Python 3.13.13,
pytest 9.1.1. Final verification ran at 13:17–13:19 CEST before the commit; the
committed source/test tree is the verified tree. Full-range whitespace also ran
after the commit.

| Command | Observed result |
|---|---|
| `mise exec -- uv sync --all-groups` | Exit 0; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/workflow/test_reports.py tests/workflow/test_transitions.py tests/packaging/test_installed_cli.py -q` | 111 passed in 2.41s |
| `mise exec -- uv run pytest tests/workflow/ tests/packaging/ -q` | 427 passed in 10.48s |
| `mise exec -- uv run pytest` | 1315 passed in 19.57s; zero failures/skips |
| `mise exec -- uv run ruff check .` | All checks passed |
| `mise exec -- uv run ruff format --check .` | 114 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | No issues in 51 source files |
| `mise exec -- uv build` | sdist and wheel built |
| `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..HEAD` | Exit 0, after commit |

The 56 new behavioral cases plus six cases from splitting existing parameterized
scenarios and one schema-owner annotation row account for the increase from
1252 to 1315 tests. A focused run of the new regressions plus split state contracts
passed 58 cases in 1.95s. The initial high-root regressions failed all 19 cases
before production repairs. Cycle-08's 17 probe observations also reproduced
unchanged before editing. Do not claim comprehensive installed fail-first replay:
the installed ledger tests first ran after its decoder repair, and their deep-JSON
exit expectation was corrected from 14 to the existing documented code 11.

The unmodified cycle-08 probe was re-used function-by-function after repair;
its lock probe now raises the expected refusal before returning an observation.
The supplemental runner caught only that expected OSError and recorded the limit.
Results: [rework-08-probes.json](rework-08-probes.json). All six identity cases
retain one task and recovery; malformed ledgers retain bytes; deep CLI exit 11
has no traceback; all FIFO probes terminate; the earlier PRD appears; the blank
decision counts zero; creation syncs its parent and retry performs directory syncs.
Competing-record preservation is separately asserted by nested/process tests.

AST evidence: [rework-08-sizes.json](rework-08-sizes.json). Three remaining packaging
overlength functions are unchanged from the implementation base. No new production
module was added. Plan/inventory hashes still match cycle-08's recorded SHA-256s.

## Fresh-review handoff

Run FT-04R9 only in a fresh session. Review the full implementation range above,
all ten source tasks, all 55 owned rows, and all accepted source obligations.
Run every mandatory lens in isolated contexts: Alice consensus, Blake PRD-only,
Bob doubt plus de-slop and every R1–R5 obligation. Do not infer correctness from
passing tests. Keep the coordinator-origin lock root despite its zero lens votes.
Do not bypass the nested-dispatch refusal in the external Bob/Carl wrappers or
claim model diversity from native host lenses. Do not attach unrelated autopilot
state, move/close the PRD, edit implementation plans, refresh the capsule, or begin
another PRD. No completion review or closeout occurred here.

No temporary worktree or branch was created; probe roots and subprocesses were
cleaned/reaped. No executed plan file was created. Existing review evidence and
other sessions' artifacts remain. The repair handoff and supplemental evidence
are deliberately retained under ignored `dev/local/`.

Unresolved questions: none.
