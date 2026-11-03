---
prd: docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
review: 6
date: 2026-10-14
head_sha: ca878006eba9e0fff0f1eb175a30557d82f8278b
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
dispatch_rows:
  bob: e045a68c
---

# Review: 00053-adapter-operational-corrections-v1

Diff range: `7819970d7f807d6fad07b115af4f0df1fbc4a248..ca878006eba9e0fff0f1eb175a30557d82f8278b`

Full work range retained; prior findings are additional closure context. All three reviewer invocations are fresh and isolated.

autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/alice-output-00053-c6-20261014.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/blake-output-00053-c6-20261014.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00053-c6-20261014.txt.receipt.json
provider_review_guard: satisfied
codex_rung_guard: not fired

The model-provider guard supersedes the legacy launcher guard. All contributing implementation models are OpenAI; all three independent review lenses are Anthropic claude-opus-5-5 (observed raw init), helper-requested xhigh, permission auto, guards intact. Eve/Fable did not run; Carl remains operator-disabled. Raw session IDs are preserved separately in each receipt.

31/31 completed tasks; schema/count validation passes. No implementation edits or attempt provenance changes this session. Engram pack unavailable: repo is not registered with gita. Initial stage/replay gate attempts were blocked by uv-cache access; approved retries passed. No previous-cycle check queue exists. The initial failed staging evidence remains distinguishable from the green final suite.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [1/3] | ⚪ | A plain `error` label counts as a numeric code context because the ` code` part is optional (`error(?: code)?`). So `Error: 401 tests passed` comes back `authentication`. That is an ordinary count after a generic error label, not the "error-code" context the PRD describes | src/ovcaq/drivers/codex_events.py:302 | Phase 0 | BLAKE |
| R2 | [1/3] | ⚪ | The Claude probe checks only `command[0]` against the overlay `PATH`. With a wrapper argv (for example `env claude`), it never checks that the wrapped executable exists, while the Codex probe runs the full wrapper argv. This predates the PRD, but the PRD lists wrapper argv as a probe input | src/ovcaq/drivers/claude.py:81 | Phase 1 | BLAKE |
| R3 | [1/3] | ⚪ | Cannot statically verify: the Phase-2 exit gate (full `uv run pytest`) at HEAD. The settled 7202-passed run was at 93fd36f. The only run at cf48315 (`last-verification.json`) stopped with exit 130 (partial: 85 failed, 27 errors, blamed on the macOS `ps` denial), and this cycle's test gate exited 2 with no summary line. The rework since 93fd36f touches only tests and docs, and both narrow runs pass (136 passed; 2 passed), so the settled reason does not cover HEAD | N/A | general | BOB |
| R4 | [1/3] | 🟡 | 109 touched test(s) pass against the pre-change code: test_numeric_codes_classify_with_explicit_status_or_error_context +103 more | tests/drivers/test_adapter_failure_classes.py | general | mech-check |
| R5 | [1/3] | 🟡 | 17 touched test(s) pass against the pre-change code: test_unfinished_lane_fails_after_close_status +11 more | tests/drivers/test_adapter_outcomes.py | general | mech-check |
| R6 | [1/3] | 🟡 | 10 touched test(s) pass against the pre-change code: test_native_failure_emits_classified_terminal_with_receipt_identity +4 more | tests/drivers/test_codex_decode_terminals.py | general | mech-check |
| R7 | [1/3] | 🟡 | 7 touched test(s) pass against the pre-change code: test_failure_classification_uses_documented_precedence +1 more | tests/drivers/test_codex_failures.py | general | mech-check |
| R8 | [1/3] | 🟡 | 61 touched test(s) pass against the pre-change code: test_launch_has_exact_order_and_omits_unconfigured_flags +55 more | tests/drivers/test_codex_launch.py | general | mech-check |
| R9 | [1/3] | 🟡 | 14 touched test(s) pass against the pre-change code: test_native_diagnostics_have_independent_failure_classification +8 more | tests/drivers/test_codex_rework_decode.py | general | mech-check |
| R10 | [1/3] | 🟡 | 19 touched test(s) pass against the pre-change code: test_probe_finds_executable_available_only_on_overlay_path, test_probe_rejects_absolute_command_that_is_not_an_executable_file, test_probe_rejects_file_without_execute_permission +13 more | tests/runtime/test_adapter_health.py | general | mech-check |
| R11 | [1/3] | 🟡 | 4 touched test(s) pass against the pre-change code: test_configured_supervisor_launches_each_selected_literal_model_and_effort | tests/runtime/test_adapter_launch_routing.py | general | mech-check |

### Auto-dismissed (ledger)


- [BLAKE] 🟡 Numeric codes in explicit status or error-code fields are not recognized: `status_code=429`, `error_code: 429`, `statusCode: 429` and JSON `"status": 429` all come back `unknown`. The prefix regex only accepts `status`/`error`, optionally followed by a space and `code`, so underscore, camelCase and quoted-key forms miss. Before this PRD the bare `\b429\b` matched these as rate_limit. A real 429 in these shapes now loses the bounded WAIT/retry path, and no positive test pins these shapes | File: src/ovcaq/drivers/codex_events.py:300 — No native JSON-label fixture or newly authorized JSON grammar; retained as KNOWN limitation.
- [BLAKE] ⚪ A routine `close_agent`/`wait` with status shutdown, interrupted or not_found on an already completed lane emits a `raw.unknown` observation every time. The TUI then flags the session as having raw evidence (`tui/model.py:548`) for normal protocol traffic. This is documented, but it adds noise | File: src/ovcaq/drivers/codex.py:378 — Requirements ambiguity: resume/restart generation semantics are not specified by this PRD. The existing contract deliberately freezes completed/failed identities and pins late updates. A binary tool name does not prove a native status sequence; changing this would undo reviewed stability without a fixture. Preserve for separately specified adapter lifecycle work.
- [BLAKE] ⚪ The health probe and the real launch resolve paths from different directories when the command is relative or the host `PATH` is empty. The Codex probe spawns without `cwd` and Claude's `shutil.which` checks against the process cwd, but launch uses `cwd=request.root`. The docs admit part of this (Codex searches the current directory, Claude reports unhealthy). It is still a corner where the probe and the spawn can disagree | File: src/ovcaq/drivers/codex.py:47 — Known pre-existing caller/request-root cwd disagreement. PRD explicitly excludes probe descendant/ownership redesign and preserves Codex probe behavior. Defer outside this repair; do not change the current scope.


Adjudication check: the completed-close raw-noise row matches the exact cycle-2 post-sweep ledger entry (the consolidator printed a less specific lifecycle reason); raw unknown evidence is intentionally documented and tested. SDK/JSON diagnostic forms and cwd lookup limitations remain the previously settled scope decisions. No silent dismissal.

## Classification

| Ref | Disposition | Evidence/reason |
|-----|-------------|-----------------|
| R1 | discard | Previously settled mixed diagnostic-prefix/count precedence limitation (cycle 2): status: 401 tests passed and error code: 503 records. Error: 401 tests passed is the same ambiguity, not a new contract. PRD preserves genuine Error 401: diagnostics; broader prose grammar requires separate specification. |
| R2 | defer | Existing wrapper-inner-executable limitation: base 7819970 Claude probe already checks only command[0]. The reviewed design explicitly requires shutil.which(command, path=effective_path), not execution or parsing of arbitrary wrapper argv. Effective PATH lookup is implemented and tested. Further wrapper health semantics need a separately specified contract. |
| R3 | verify | Resolved by approved full suite at reviewed HEAD ca878006eba9e0fff0f1eb175a30557d82f8278b: uv run pytest -q --tb=line exited 0, 7199 passed, 0 failed/skipped. Sync, Ruff lint/format, mypy and build also pass. Alice independently obtained the same full-suite result. |
| R4 | discard | Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics. |
| R5 | discard | Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics. |
| R6 | discard | Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics. |
| R7 | discard | Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics. |
| R8 | discard | Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics. |
| R9 | discard | Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics. |
| R10 | discard | Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics. |
| R11 | discard | Required PRD compatibility/preservation controls, not tautologies: direct tier/argv precedence, native fixtures, normal lane/probe behavior remain compatible. Fresh full-range replay ran 293 touched cases; 52 fail against base and 241 preserve behavior. Same-file historical ledger dispositions remain valid; the new Codex default-PATH case intentionally preserves pre-existing subprocess semantics. |

## Alice

Provider: Anthropic; observed model claude-opus-5-5; helper-requested effort xhigh.

[ALICE] ✅ No issues found

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

All five findings from the last review are fixed, and the rework broke nothing.

The only code changes since `93fd36f` are in three files: `docs/driver-protocol.md`, `tests/drivers/test_adapter_failure_classes.py` and `tests/runtime/test_adapter_health.py`. The rest of the diff is autopilot evidence, which a settled deferral already covers.

**Prior findings:**
- **R1 (task 30):** the two paragraphs are reflowed with the same words. The 103-character line is gone. The longest prose line in the edited paragraphs is now 84 characters, at `docs/driver-protocol.md:272`, which is in line with the file's other 81-83 character lines.
- **R3 (task 29):** the duplicate display-limit test is deleted. `json` and the `driver` fixture are still used by the capacity test, and ruff is clean.
- **R4 (task 29):** only the `(2, WAIT)` and `(3, HALT)` cases remain at `tests/drivers/test_adapter_failure_classes.py:233`, so the test still pins the exact bound.
- **R5 (task 29):** the test is renamed to `test_numeric_codes_classify_with_explicit_status_or_error_context` (`tests/drivers/test_adapter_failure_classes.py:67`). Nothing still uses the old name; a search for the new name confirmed the search works.
- **R6 (task 31):** `tests/runtime/test_adapter_health.py:229` is now parametrized over claude and codex. The check at line 239 confirms the stdlib's own fallback finds nothing there. So the Codex case passing shows its subprocess lookup really used the patched default search path.

**Gates at HEAD `ca87800`, run in this session:**
```
PRD-scoped tests: 464 passed, 2 warnings (467 - 2 deleted auth cases - 2 capacity cases + 1 codex case)
Full suite: 7199 passed, 0 failed, 0 skipped, 2 warnings (the known temp-directory cleanup warnings)
ruff check: All checks passed | ruff format --check: 236 files already formatted | mypy: no issues in 61 source files
```

The review context's test gate reported exit 2 with no summary line. My run above passed, so that report looks like a tooling glitch, not a failing suite. I did not run `uv sync --all-groups` or `uv build`. Since cycle 5 only tests and docs changed, so the build inputs are the same.

## Blake

Provider: Anthropic; observed model claude-opus-5-5; helper-requested effort xhigh.

[BLAKE] 🟡 Numeric codes in explicit status or error-code fields are not recognized: `status_code=429`, `error_code: 429`, `statusCode: 429` and JSON `"status": 429` all come back `unknown`. The prefix regex only accepts `status`/`error`, optionally followed by a space and `code`, so underscore, camelCase and quoted-key forms miss. Before this PRD the bare `\b429\b` matched these as rate_limit. A real 429 in these shapes now loses the bounded WAIT/retry path, and no positive test pins these shapes | File: src/ovcaq/drivers/codex_events.py:300 | Task: Phase 0
[BLAKE] ⚪ A plain `error` label counts as a numeric code context because the ` code` part is optional (`error(?: code)?`). So `Error: 401 tests passed` comes back `authentication`. That is an ordinary count after a generic error label, not the "error-code" context the PRD describes | File: src/ovcaq/drivers/codex_events.py:302 | Task: Phase 0
[BLAKE] ⚪ A routine `close_agent`/`wait` with status shutdown, interrupted or not_found on an already completed lane emits a `raw.unknown` observation every time. The TUI then flags the session as having raw evidence (`tui/model.py:548`) for normal protocol traffic. This is documented, but it adds noise | File: src/ovcaq/drivers/codex.py:378 | Task: Phase 0
[BLAKE] ⚪ The health probe and the real launch resolve paths from different directories when the command is relative or the host `PATH` is empty. The Codex probe spawns without `cwd` and Claude's `shutil.which` checks against the process cwd, but launch uses `cwd=request.root`. The docs admit part of this (Codex searches the current directory, Claude reports unhealthy). It is still a corner where the probe and the spawn can disagree | File: src/ovcaq/drivers/codex.py:47 | Task: Phase 1
[BLAKE] ⚪ The Claude probe checks only `command[0]` against the overlay `PATH`. With a wrapper argv (for example `env claude`), it never checks that the wrapped executable exists, while the Codex probe runs the full wrapper argv. This predates the PRD, but the PRD lists wrapper argv as a probe input | File: src/ovcaq/drivers/claude.py:81 | Task: Phase 1
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

## Bob

Provider: Anthropic; observed model claude-opus-5-5; helper-requested effort xhigh.

[BOB] ⚪ Cannot statically verify: the Phase-2 exit gate (full `uv run pytest`) at HEAD. The settled 7202-passed run was at 93fd36f. The only run at cf48315 (`last-verification.json`) stopped with exit 130 (partial: 85 failed, 27 errors, blamed on the macOS `ps` denial), and this cycle's test gate exited 2 with no summary line. The rework since 93fd36f touches only tests and docs, and both narrow runs pass (136 passed; 2 passed), so the settled reason does not cover HEAD | File: N/A | Task: general

The five prior findings are resolved. I checked each at HEAD:
- **R1** (task 30): `docs/driver-protocol.md` was reflowed and no words changed. The longest touched prose line is now 84 characters (line 272), close enough to the file's ~80-column wrap, where 81-character lines already exist.
- **R3** (task 29): the duplicate display-limit test is gone. `tests/drivers/test_codex_rework_decode.py:136` still covers that path. `json` and the `driver` fixture are still used, at `tests/drivers/test_adapter_failure_classes.py:240`.
- **R4** (task 29): only `(2, WAIT)` and `(3, HALT)` remain. They pin the `<` bound at `src/ovcaq/runtime/decision.py:215`.
- **R5** (task 29): the test is renamed, and no stale references remain in `src`, `tests`, the docs, the CHANGELOG or the PRDs.
- **R6** (task 31): the test now runs for both `claude` and `codex`. The Codex case does pin the behavior. `Popen` with no `PATH` in its environment falls back to `os.get_exec_path`, then to the patched `os.defpath`. The line `assert shutil.which(executable.name) is None` (`tests/runtime/test_adapter_health.py:239`) shows that a `CS_PATH`-based lookup would fail. The fake executable uses an absolute shebang, so removing `PATH` cannot break the child process.

No production code changed since 93fd36f (`src/` diff is empty), so the rework cannot have broken anything in production.

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

FIX:
- (none)

VERIFY:
- The full suite is unverified at HEAD (the last run at cf48315 exited 130; this cycle's gate exited 2) — run `mise exec -- uv run pytest` at ca87800 on a host where `ps` and process inspection are allowed. Expect exit 0 with 7199 passed and 0 failed, errors or skipped: 7202, minus 2 for the deleted auth test, minus 2 for the dropped capacity cases, plus 1 for the new codex case.

KNOWN:
- (none)

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

## Cycle outcome

No unresolved CRITICAL/HIGH, no actionable Medium/Low tail. R1 is a settled ambiguity, R2 is durably deferred outside the specified probe correction, R3 is verified by the completed full suite, and all eight mechanical rows are preservation controls adjudicated against the PRD and historical ledger. No repair, cap increase or new implementation task is needed. All raw R/B/D verdicts are retained above. Mandatory shape, provider receipt, complete-rubric, state/count and constraint gates passed before the canonical convergence transition.

Verdict: 11 findings
Tests: 7199 passed, 0 failed, 0 skipped (suite run this cycle at ca878006eba9e0fff0f1eb175a30557d82f8278b; two temporary-directory cleanup warnings)
