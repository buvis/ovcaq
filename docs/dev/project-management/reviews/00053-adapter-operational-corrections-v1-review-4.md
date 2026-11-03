---
prd: docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
review: 4
date: 2026-10-13
head_sha: badf378ae80592ec9cf1ec023350e55b9090d1ab
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  bob: 73ec27b0
---

# Review: 00053-adapter-operational-corrections-v1

Diff range: `7819970d7f807d6fad07b115af4f0df1fbc4a248..badf378ae80592ec9cf1ec023350e55b9090d1ab` (full PRD scope)

codex_rung_guard: not fired
The model-provider guard supersedes the legacy Eve rule; Eve did not run.
provider_review_guard: satisfied
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-cycle4-20261013-evidence/alice.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-cycle4-20261013-evidence/blake.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-cycle4-20261013-evidence/bob.txt.receipt.json

All three fresh external Anthropic Opus reviews succeeded. Complete raw output and immutable receipts retained. Observed served model: claude-opus-5-5 for all three lenses; effort xhigh under host routing. Session IDs and exact raw metadata are retained in raw logs, receipts, and reviewer-models.json. No thread reuse. Optional Carl disabled (no UI change). Context pack failed: repository is not registered with engram. No prior verification-check queue exists. Task count: 26/26 completed.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | ⚪ | The protocol doc still says numeric codes "require HTTP, status or error-code context". Since task 25, bare `Error 429:` and `status=429` also count. CHANGELOG.md:45 says "HTTP/status/error context", so the two documents disagree. Change the doc to "HTTP, status or error context" to match the code and the changelog | docs/driver-protocol.md:273 | 25 | ALICE, BOB |
| R2 | [2/3] | 🟡 | The ` error` branch inside the `http(...)` group of the `status` prefix can never change a result, so it is dead code. The new bare `error(?: code)?` branch already matches every string it catches, because a word boundary always sits between "http " and "error". I checked this by running both regexes on 4,288,305 generated token strings: 0 differences. Simpler version with the same behavior: `r"(?:http(?:/\d+(?:\.\d+)?| status(?: (?:client|server) error \()?)?"`, keeping line 302 as it is. "HTTP error 503" still returns connectivity through the bare `error` branch, so the `hTtP ErRoR {code}` tests keep passing | src/ovcaq/drivers/codex_events.py:301 | 25 | ALICE, BOB |
| R3 | [1/3] | ⚪ | A driver from build_driver now reads request.model as a model value, not a tier key: with {default: o3, o3: o3-pro}, build_driver(...).build_launch(model="o3") launches o3, while CodexDriver directly launches o3-pro. It is documented and the supervisor is its only caller, but the same request now means different things depending on how the driver was built | src/ovcaq/drivers/edge.py:19 | Phase 1 | BLAKE |
| R4 | [1/3] | ⚪ | The full suite still warns twice with "PytestWarning: (rm_rf) error removing …/garbage-… Directory not empty" (the same as R21 in review 00009-2). It predates this PRD and is still unexplained; some test process probably keeps writing into tmp after teardown | N/A | general | BLAKE |
| R5 | [1/3] | ⚪ | CHANGELOG.md:45 lists regex branch names ("equals-delimited status, bare error, HTTP error, native bare-status and HTTP-version forms"). It also restates unchanged behavior ("retain existing authentication word diagnostics and genuine rate/quota limits"). That describes the implementation, not what users see | CHANGELOG.md | 25 | BOB |
| R6 | [1/3] | ⚪ | Cannot statically verify: the full suite passes at HEAD. The last recorded run, at d9644c8 in last-verification.json, was interrupted: exit 130, with 88 failures and 27 errors in 3418 executed tests, blamed on a denied `ps`. The cycle-4 quality-gates.json says "counts discarded; fresh summary run pending". The settled 7165-passed result predates tasks 15-26, so the settled reason no longer covers HEAD | N/A | general | BOB |
| R7 | [1/3] | ⚪ | Suspected from reading, not run: JSON-style labels such as `"status": 503` and `"error_code": 429` now classify as `unknown`, because the prefix allows only whitespace, `:` or `=` between the label and the code. The pre-PRD bare-number match returned connectivity and rate_limit for these | src/ovcaq/drivers/codex_events.py | 6 | BOB |
| R8 | [1/3] | ⚪ | Status codes with no prefix are no longer classified: "503 Service Unavailable", "502 Bad Gateway", "403 Forbidden" and "429 Too Many Requests" now return unknown, so a bare 503 gets a died-retry and then PARK instead of a connectivity WAIT. Common SDK spellings "status_code=429", "statusCode: 429" and the PRD's own "error-code 401" also return unknown. This is spec-consistent but a real drop in coverage, and nothing pins the intent (confirmed by probe) | src/ovcaq/drivers/codex_events.py:300 | Phase 0 | BLAKE |
| R9 | [1/3] | 🟡 | 111 touched test(s) pass against the pre-change code: test_numeric_diagnostics_require_an_explicit_status_or_error_context +105 more | tests/drivers/test_adapter_failure_classes.py | general | mech-check |
| R10 | [1/3] | 🟡 | 17 touched test(s) pass against the pre-change code: test_unfinished_lane_fails_after_close_status +11 more | tests/drivers/test_adapter_outcomes.py | general | mech-check |
| R11 | [1/3] | 🟡 | 10 touched test(s) pass against the pre-change code: test_native_failure_emits_classified_terminal_with_receipt_identity +4 more | tests/drivers/test_codex_decode_terminals.py | general | mech-check |
| R12 | [1/3] | 🟡 | 7 touched test(s) pass against the pre-change code: test_failure_classification_uses_documented_precedence +1 more | tests/drivers/test_codex_failures.py | general | mech-check |
| R13 | [1/3] | 🟡 | 61 touched test(s) pass against the pre-change code: test_launch_has_exact_order_and_omits_unconfigured_flags +55 more | tests/drivers/test_codex_launch.py | general | mech-check |
| R14 | [1/3] | 🟡 | 14 touched test(s) pass against the pre-change code: test_native_diagnostics_have_independent_failure_classification +8 more | tests/drivers/test_codex_rework_decode.py | general | mech-check |
| R15 | [1/3] | 🟡 | 18 touched test(s) pass against the pre-change code: test_probe_finds_executable_available_only_on_overlay_path, test_probe_rejects_absolute_command_that_is_not_an_executable_file, test_probe_rejects_file_without_execute_permission +12 more | tests/runtime/test_adapter_health.py | general | mech-check |
| R16 | [1/3] | 🟡 | 4 touched test(s) pass against the pre-change code: test_configured_supervisor_launches_each_selected_literal_model_and_effort | tests/runtime/test_adapter_launch_routing.py | general | mech-check |

### Auto-dismissed (ledger)


- [BLAKE] 🟡 A plain "error" in front of a number now counts as a status code (added in task 25), so ordinary counts get classified: "Error: 429 tests failed" → rate_limit (which halts, since there is no reset time), "error 403 lines removed" → permission, "Error = 502 retries" → connectivity (confirmed by running classify_failure). This goes against "ordinary counts remain unknown". The negative tests only cover counts with no prefix. It widens a finding the ledger already deferred ("status: 401 tests passed") to a much more common word | File: src/ovcaq/drivers/codex_events.py:302 — Requirements ambiguity: mixed diagnostic-prefix/ordinary-count messages need an explicit precedence contract. Existing scope requires diagnostic status contexts and ordinary count negatives; do not invent a broader prose grammar or silently change precedence. Keep the confirmed counterexamples for later specified work.
- [BLAKE] ⚪ Status codes with no prefix are no longer classified: "503 Service Unavailable", "502 Bad Gateway", "403 Forbidden" and "429 Too Many Requests" now return unknown, so a bare 503 gets a died-retry and then PARK instead of a connectivity WAIT. Common SDK spellings "status_code=429", "statusCode: 429" and the PRD's own "error-code 401" also return unknown. This is spec-consistent but a real drop in coverage, and nothing pins the intent (confirmed by probe) | File: src/ovcaq/drivers/codex_events.py:300 — Requirements ambiguity: mixed diagnostic-prefix/ordinary-count messages need an explicit precedence contract. Existing scope requires diagnostic status contexts and ordinary count negatives; do not invent a broader prose grammar or silently change precedence. Keep the confirmed counterexamples for later specified work.
- [BLAKE] ⚪ Suspected, not reproduced: for a relative command containing a slash (e.g. "./bin/codex"), both health checks resolve it against the supervisor's working directory, but the launch resolves it against cwd=request.root, so health and launch can disagree when the two directories differ. This predates the PRD and is outside the cases it lists | File: src/ovcaq/drivers/claude.py:83 — Existing out-of-scope relative-path/cwd limitation; probe ownership redesign excluded by PRD. New Claude citation retained.

## Decision gate

- R1 protocol wording, R2 redundant numeric-prefix alternatives, and R5 changelog wording are new bounded actionable findings. Operator decision required: no repair or cap increase is authorized. R2 merges Alice and Bob's overlapping findings; their complete descriptions remain in raw sections below.
- R3 factory-versus-direct model precedence is the explicit PRD contract, documented and tested; discard as required behavior.
- R4 pytest cleanup warnings predate this PRD (review 00009-2 R21); known limitation, no test failures. Preserve for separately scoped process cleanup.
- R6 verification concern is resolved by fresh verification at reviewed HEAD: 7202 passed, zero failed/skipped, all six quality gates pass. See verification.json and full-suite.log. Blake independently confirms the same count. Earlier interrupted evidence remains intact. No additional suite is required merely to change verbosity to -q.
- R7 JSON label spellings are Bob's KNOWN item: no native fixture, no newly authorized JSON grammar. Preserve as a limitation; no production change authorized.
- R8 was restored from the script's erroneous second ledger dismissal: mixed-count precedence is not a reason to dismiss bare-code/SDK-spelling coverage. Independently discard bare reason phrases as explicitly excluded by operator authorization; SDK snake/camel/hyphen spellings require separately specified grammar and fixtures. No claim that they were fixed.
- The first Blake auto-dismissal falls under the preserved mixed diagnostic-prefix/count precedence deferral; its new error-prefix examples are retained verbatim. The relative-path dismissal is the established probe-cwd deferral.
- R9-R16 mechanical replay rows are retained compatibility controls required by the PRD: literal fixture oracles, unchanged direct precedence, PATH/reset/native behavior, and ordinary routes. Replay ran 296 touched tests: 54 failed at base, 242 passed. Existing same-file ledger reasons hold; no tautological-test rows were emitted.

Three actionable findings; no CRITICAL/HIGH. All settled deferrals remain preserved. The operator authorized finalization only on a clean review, so pause instead of a tail sweep or automatic repair. Cycle/cap remain 4/4.

### Subsequent operator disposition — 2026-10-13

The operator approved R1, R2 and R5 separately, then approved cap 4→5 for one fresh complete review and normal finalization only if that review passes every gate without new unresolved actionable findings. Authorization and preserved recovery evidence: `reports/00053-cycle4-recovery-20261013/`. Tasks 27/28 complete the approved repairs in `ca59071` and `dbd7e1f`. Classifier tests: 140 passed; Pat resolved R2 with no findings. Sync, lint, formatting, types and build pass. Full verification remains blocked in the recovery host by a denied `ps` launch (344 passed, one failure on each of the default and escalated fail-fast runs); cycle 5 must obtain a complete passing suite before finalization. Original findings, reviewer output, receipts and the historical pause above remain unchanged. No new repair or further cap increase is authorized.

## Alice

Provider: Anthropic (complete raw output follows).

[ALICE] 🟡 The ` error` branch inside the `http(...)` group of the `status` prefix can never change a result, so it is dead code. The new bare `error(?: code)?` branch already matches every string it catches, because a word boundary always sits between "http " and "error". I checked this by running both regexes on 4,288,305 generated token strings: 0 differences. Simpler version with the same behavior: `r"(?:http(?:/\d+(?:\.\d+)?| status(?: (?:client|server) error \()?)?"`, keeping line 302 as it is. "HTTP error 503" still returns connectivity through the bare `error` branch, so the `hTtP ErRoR {code}` tests keep passing | File: src/ovcaq/drivers/codex_events.py:301 | Task: 25
[ALICE] ⚪ The protocol doc still says numeric codes "require HTTP, status or error-code context". Since task 25, bare `Error 429:` and `status=429` also count. CHANGELOG.md:45 says "HTTP/status/error context", so the two documents disagree. Change the doc to "HTTP, status or error context" to match the code and the changelog | File: docs/driver-protocol.md:273 | Task: 25

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

## Blake: blind audit of PRD 00053 (adapter operational corrections)

Provider: Anthropic (complete raw output follows).

The PRD's behavior is in place, and all six exit-criteria checks pass on this tree (run 2026-10-13):

```
pytest (acceptance files): 322 passed, 1 warning
pytest (full):             7202 passed, 2 warnings in 240.23s, 0 skipped
ruff check:                All checks passed!
ruff format --check:       236 files already formatted
mypy src/ovcaq:            Success: no issues found in 61 source files
uv build:                  sdist + wheel built (scratch output deleted)
```

What I checked against the code:
- **Lanes** (`src/ovcaq/drivers/codex.py:370`): only lanes that started and haven't finished can be turned into a failure. Finished lanes ignore late updates.
- **Capacity**: "Selected model is at capacity" now lands in the connectivity bucket (`src/ovcaq/drivers/codex_events.py:328`). It waits and retries, and it halts once retries run out (`tests/drivers/test_adapter_failure_classes.py:258`).
- **Model chosen once**: the Codex driver from `build_driver` maps the chosen model back to its tier key, the same way the existing Claude edge does (`src/ovcaq/drivers/edge.py:16`). Calling `CodexDriver` directly still gives tier keys precedence (`tests/drivers/test_codex_launch.py:186`).
- **Health check PATH**: the Claude check now searches the configured PATH (`src/ovcaq/drivers/claude.py:82`). The Codex check already ran the command under the merged environment, which is how the real launch runs it.
- **Unchanged**: driver API 2, observation protocol 1, state schema 1. The rate-limit reset parser (`failure_reset`) and `DEFAULT_PHASE_TIERS` are untouched.

```
[BLAKE] 🟡 A plain "error" in front of a number now counts as a status code (added in task 25), so ordinary counts get classified: "Error: 429 tests failed" → rate_limit (which halts, since there is no reset time), "error 403 lines removed" → permission, "Error = 502 retries" → connectivity (confirmed by running classify_failure). This goes against "ordinary counts remain unknown". The negative tests only cover counts with no prefix. It widens a finding the ledger already deferred ("status: 401 tests passed") to a much more common word | File: src/ovcaq/drivers/codex_events.py:302 | Task: Phase 0
[BLAKE] ⚪ Status codes with no prefix are no longer classified: "503 Service Unavailable", "502 Bad Gateway", "403 Forbidden" and "429 Too Many Requests" now return unknown, so a bare 503 gets a died-retry and then PARK instead of a connectivity WAIT. Common SDK spellings "status_code=429", "statusCode: 429" and the PRD's own "error-code 401" also return unknown. This is spec-consistent but a real drop in coverage, and nothing pins the intent (confirmed by probe) | File: src/ovcaq/drivers/codex_events.py:300 | Task: Phase 0
[BLAKE] ⚪ A driver from build_driver now reads request.model as a model value, not a tier key: with {default: o3, o3: o3-pro}, build_driver(...).build_launch(model="o3") launches o3, while CodexDriver directly launches o3-pro. It is documented and the supervisor is its only caller, but the same request now means different things depending on how the driver was built | File: src/ovcaq/drivers/edge.py:19 | Task: Phase 1
[BLAKE] ⚪ Suspected, not reproduced: for a relative command containing a slash (e.g. "./bin/codex"), both health checks resolve it against the supervisor's working directory, but the launch resolves it against cwd=request.root, so health and launch can disagree when the two directories differ. This predates the PRD and is outside the cases it lists | File: src/ovcaq/drivers/claude.py:83 | Task: Phase 1
[BLAKE] ⚪ The full suite still warns twice with "PytestWarning: (rm_rf) error removing …/garbage-… Directory not empty" (the same as R21 in review 00009-2). It predates this PRD and is still unexplained; some test process probably keeps writing into tmp after teardown | File: N/A | Task: general
```

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

**Status**: Done.
**Changed**: nothing in the repo. I wrote two classifier probe scripts and a build output under /tmp, then deleted them.
**Next**: Task complete. Suggested next: decide whether a plain "error" prefix should count as a status code (finding 1) before this review is consolidated.

## Bob

Provider: Anthropic (complete raw output follows).

[BOB] 🟡 Two alternatives in the numeric prefix regex never change a result. Inside the `http(...)` group, ` error` (added by task 25) and plain ` status` (with no parenthetical) are redundant. `re.search` already matches the same text through the top-level `error(?: code)?` and `status(?: code)?` alternatives, and the preceding space always supplies the `\b`. Shrink the group to `http(?:/\d+(?:\.\d+)?| status (?:client|server) error \()?`. All current positives still match, including `hTtP ErRoR {code}`, `HTTP status: {code}` and the reqwest forms | File: src/ovcaq/drivers/codex_events.py | Task: 25
[BOB] ⚪ docs/driver-protocol.md:273 still says numeric codes need "HTTP, status or error-code context". Task 25 now also accepts a bare `error` label (`Error 429:`, `error=401`, `Error 429`), and CHANGELOG.md:45 already says "error context". The doc no longer matches the code | File: docs/driver-protocol.md | Task: 25
[BOB] ⚪ CHANGELOG.md:45 lists regex branch names ("equals-delimited status, bare error, HTTP error, native bare-status and HTTP-version forms"). It also restates unchanged behavior ("retain existing authentication word diagnostics and genuine rate/quota limits"). That describes the implementation, not what users see | File: CHANGELOG.md | Task: 25
[BOB] ⚪ Cannot statically verify: the full suite passes at HEAD. The last recorded run, at d9644c8 in last-verification.json, was interrupted: exit 130, with 88 failures and 27 errors in 3418 executed tests, blamed on a denied `ps`. The cycle-4 quality-gates.json says "counts discarded; fresh summary run pending". The settled 7165-passed result predates tasks 15-26, so the settled reason no longer covers HEAD | File: N/A | Task: general
[BOB] ⚪ Suspected from reading, not run: JSON-style labels such as `"status": 503` and `"error_code": 429` now classify as `unknown`, because the prefix allows only whitespace, `:` or `=` between the label and the code. The pre-PRD bare-number match returned connectivity and rate_limit for these | File: src/ovcaq/drivers/codex_events.py | Task: 6

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
- Redundant ` error` and plain ` status` alternatives inside the `http(...)` prefix group — src/ovcaq/drivers/codex_events.py:301 — replace line 301 with `r"(?:http(?:/\d+(?:\.\d+)?| status (?:client|server) error \()?"`. Behavior does not change: any `http error N` or `http status N` text also contains a top-level `error N` or `status N` match.
- Protocol doc says "error-code context" but bare `error` now counts — docs/driver-protocol.md:273 — change to "require HTTP, status or error context (for example `HTTP/2 503`, `status=429`, `Error 401:`)".
- Changelog numeric entry describes regex branches and unchanged behavior — CHANGELOG.md:45 — rewrite as: "**drivers**: count Codex failure codes 401/403/429/502/503 only after an HTTP, status or error label (for example `HTTP/2 503`, `status=429`, `Error 401:`), so ordinary counts such as 'processed 401 files' no longer trigger failure handling."
VERIFY:
- Full suite at HEAD has no recorded counts, and the last recorded run was interrupted with 88 failures and 27 errors — on a host that allows process inspection (`ps`), run `uv run pytest -q` at HEAD badf378. Record passed/failed/errors/skipped in docs/dev/project-management/autopilot/last-verification.json. Require 0 failed, 0 errors and 0 skipped.
KNOWN:
- JSON-style labels (`"status": 503`, `"error_code": 429`) classify as `unknown` (static reading; the pre-PRD code classified them) — out of scope for three reasons. The design says "additional diagnostic spellings can extend adapter fixtures independently". The operator ruled that bare numbers acquire no new contract. No checked-in fixture shows Codex emitting this form.

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

Verdict: 16 findings
Tests: 7202 passed, 0 failed, 0 skipped (suite run this cycle; raw full-suite.log, verification.json; first stage also exited 0 but discarded counts)
