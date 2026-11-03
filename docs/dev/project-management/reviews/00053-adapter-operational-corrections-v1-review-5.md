---
prd: docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
review: 5
date: 2026-10-13
head_sha: 93fd36f5da3138d8a0d52be7560e9aebb15ec12c
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  bob: 41d9b970
---

# Review: 00053-adapter-operational-corrections-v1 — cycle 5

Diff range: `7819970d7f807d6fad07b115af4f0df1fbc4a248..93fd36f5da3138d8a0d52be7560e9aebb15ec12c` (full PRD review)

codex_rung_guard: not fired
The actual model-provider guard supersedes the legacy launcher guard. Eve did not run. Carl remains disabled by operator authorization.
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-cycle5-20261013/alice-output.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-cycle5-20261013/blake-output.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-cycle5-20261013/bob-output.txt.receipt.json
provider_review_guard: satisfied

All required reviewer processes exited 0. Actual served model: claude-opus-5-5, effort xhigh, three fresh isolated sessions. Blake received only the PRD and repository access. Source provenance and immutable receipts: reports/00053-cycle5-20261013/reviewer-provenance.json.

Optional context pack: failed (engram reports this repo is not registered). Full source rubrics, PRD/diff, task context, mechanical facts and replay were available. No lens omitted.

All six verification gates pass at reviewed HEAD: 7202 passed, zero failed/skipped. Prior failed process-inspection runs remain preserved; approved escalation resolved the host restriction. Current raw full-suite log/JUnit and gate logs are retained. Prior cycle verification-check queue is absent. Bob VERIFY is empty; no queue generated.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [1/3] | ⚪ | The task-28 and task-19 edits left the prose wrapping uneven. docs/driver-protocol.md:274 is 103 characters long, the only long line in the file that is not a link or a table row. Line 272 also runs past the file's ~80-column wrap. Lines 186-191 break after "tier-key precedence:", which makes the next sentence look like the start of a list, and line 191 stops at "`low`,". Fix: reflow both paragraphs to ~80 columns without changing any words | docs/driver-protocol.md | 28 | ALICE |
| R2 | [1/3] | ⚪ | Only the private subclasses built by `build_driver` map a resolved model back to its tier key. A Supervisor given a plain `CodexDriver`/`ClaudeDriver` or an entry-point driver still applies tier lookup to the resolved model, so `LaunchRequest.model` stays ambiguous between tier and model. This follows the PRD's chosen edge pattern; only the CLI path is protected | src/ovcaq/drivers/edge.py:16 | P1-T1 | BLAKE |
| R3 | [1/3] | ⚪ | `test_authentication_is_classified_beyond_the_display_detail_limit` repeats `test_failure_classifies_full_text_before_sanitizing_and_capping_detail` (tests/drivers/test_codex_rework_decode.py:136). Both decode a failure for the same two event kinds and check that the class comes from text past the 4096-character display limit. Only the trailing word differs ("Unauthorized" vs "Rate limit reached"). No PRD feature touches this path, and the test passes on the base, so it is padding of the same kind tasks 20, 21 and 23 removed. Delete it. `json` and the `driver` fixture are still used by the capacity test | tests/drivers/test_adapter_failure_classes.py:231 | 6 | BOB |
| R4 | [1/3] | ⚪ | The capacity bound test runs `connectivity_retries` 0, 1, 2 and 3. Cases 0, 1 and 2 all take the same `retries.connectivity < policy.connectivity_retries` branch (src/ovcaq/runtime/decision.py:215). Only 2 (the last WAIT) and 3 (HALT) pin the bound. Drop cases 0 and 1 | tests/drivers/test_adapter_failure_classes.py:258 | 6 | BOB |
| R5 | [1/3] | ⚪ | `test_numeric_diagnostics_require_an_explicit_status_or_error_context` checks only the positive cases. The "require" half is tested by `test_unrelated_numbers_are_not_failure_diagnostics` (tests/drivers/test_adapter_failure_classes.py:156). Rename it for the rule it enforces, e.g. `test_numeric_codes_classify_with_explicit_status_or_error_context` | tests/drivers/test_adapter_failure_classes.py:67 | 6 | BOB |
| R6 | [1/3] | ⚪ | docs/driver-protocol.md:36 says both native adapters fall back to the standard default search path when the host PATH is missing. Only Claude has a test for this (`test_claude_probe_uses_default_search_path_when_host_path_is_absent`). The design says to "reproduce and regress" the existing Codex probe behavior. Parametrize the test over ("claude", "codex") and drop "claude" from its name. As I read `os.get_exec_path`, the patched `os.defpath` also steers the Codex subprocess lookup (not run) | tests/runtime/test_adapter_health.py:229 | 3 | BOB |
| R7 | [1/3] | ⚪ | This cycle's incremental diff is 378,503 lines, and only about 1,300 of them are product code, tests and docs. The rest is committed autopilot evidence, including review diffs that git can regenerate: a 169,912-line review-diff.diff and a 16 MB review-diff-00053-postrepair-20261012.diff.gz. Each committed review diff contains the earlier cycles' diffs, so the repo grows faster every cycle | docs/dev/project-management/autopilot/reports/00053-cycle3-20261013-evidence/review-diff.diff | general | BOB |
| R8 | [1/3] | 🟡 | Labeled status forms classify correctly, but HTTP diagnostics without a label now return `unknown` where the old bare-number match classified them. Reproduced: `429 Too Many Requests`, `503 Service Unavailable`, `HTTPS 503`, `{"status":429}`, `"statusCode": 401` and `code: 429` all give `unknown`. So a real 429 or 503 reported in one of these forms no longer gets rate-limit or connectivity WAIT handling. The PRD's "explicit HTTP/status/error-code context" rule allows this, but it narrows "genuine HTTP diagnostics", and there is no negative or positive pin for these forms | src/ovcaq/drivers/codex_events.py:300 | P0-T1 | BLAKE |
| R9 | [1/3] | 🟡 | 111 touched test(s) pass against the pre-change code: test_numeric_diagnostics_require_an_explicit_status_or_error_context +105 more | tests/drivers/test_adapter_failure_classes.py | general | mech-check |
| R10 | [1/3] | 🟡 | 17 touched test(s) pass against the pre-change code: test_unfinished_lane_fails_after_close_status +11 more | tests/drivers/test_adapter_outcomes.py | general | mech-check |
| R11 | [1/3] | 🟡 | 10 touched test(s) pass against the pre-change code: test_native_failure_emits_classified_terminal_with_receipt_identity +4 more | tests/drivers/test_codex_decode_terminals.py | general | mech-check |
| R12 | [1/3] | 🟡 | 7 touched test(s) pass against the pre-change code: test_failure_classification_uses_documented_precedence +1 more | tests/drivers/test_codex_failures.py | general | mech-check |
| R13 | [1/3] | 🟡 | 61 touched test(s) pass against the pre-change code: test_launch_has_exact_order_and_omits_unconfigured_flags +55 more | tests/drivers/test_codex_launch.py | general | mech-check |
| R14 | [1/3] | 🟡 | 14 touched test(s) pass against the pre-change code: test_native_diagnostics_have_independent_failure_classification +8 more | tests/drivers/test_codex_rework_decode.py | general | mech-check |
| R15 | [1/3] | 🟡 | 18 touched test(s) pass against the pre-change code: test_probe_finds_executable_available_only_on_overlay_path, test_probe_rejects_absolute_command_that_is_not_an_executable_file, test_probe_rejects_file_without_execute_permission +12 more | tests/runtime/test_adapter_health.py | general | mech-check |
| R16 | [1/3] | 🟡 | 4 touched test(s) pass against the pre-change code: test_configured_supervisor_launches_each_selected_literal_model_and_effort | tests/runtime/test_adapter_launch_routing.py | general | mech-check |

### Auto-dismissed (ledger), raw script output


- [BLAKE] 🟡 Labeled status forms classify correctly, but HTTP diagnostics without a label now return `unknown` where the old bare-number match classified them. Reproduced: `429 Too Many Requests`, `503 Service Unavailable`, `HTTPS 503`, `{"status":429}`, `"statusCode": 401` and `code: 429` all give `unknown`. So a real 429 or 503 reported in one of these forms no longer gets rate-limit or connectivity WAIT handling. The PRD's "explicit HTTP/status/error-code context" rule allows this, but it narrows "genuine HTTP diagnostics", and there is no negative or positive pin for these forms | File: src/ovcaq/drivers/codex_events.py:300 — Requirements ambiguity: mixed diagnostic-prefix/ordinary-count messages need an explicit precedence contract. Existing scope requires diagnostic status contexts and ordinary count negatives; do not invent a broader prose grammar or silently change precedence. Keep the confirmed counterexamples for later specified work.
- [BLAKE] ⚪ The probe and the real launch can still find executables in different places when PATH has a relative or empty entry. The Codex probe spawns with no `cwd`, so it searches the supervisor's working directory. The launch spawns with `cwd=request.root`, and the CLI never changes into `--root`. The Claude probe reports an empty host PATH as unhealthy, yet the actual spawn would search root. This is an edge case of the "health checks and actual spawn agree" exit criterion. I reasoned it from Python's subprocess path lookup and did not reproduce it | File: src/ovcaq/drivers/codex.py:180 — Known pre-existing caller/request-root cwd disagreement. PRD explicitly excludes probe descendant/ownership redesign and preserves Codex probe behavior. Defer outside this repair; do not change the current scope.
- [BLAKE] ⚪ Every routine close of an already-completed lane (spawn, wait completed, close_agent shutdown) emits `raw.unknown` with reason "Malformed or unsupported Codex record". That label is wrong for a valid native record, and the test pins it as the contract. The TUI only shows raw evidence when nothing was normalized, so the visible impact is small | File: src/ovcaq/drivers/codex_events.py:233 — Previously settled and intentionally pinned raw-evidence behavior; no contract change authorized.

## Decision dispositions

Operator authorization update (2026-10-14): fix R1/R3/R4/R5/R6 and raise
the rework cap from 5 to 6 for one fresh full cycle-6 review. This supersedes
the earlier no-repair/no-cap-increase limits below for these five findings;
the original dispositions remain historical evidence. Canonical `review-close`
created tasks 29 (R3/R4/R5), 30 (R1), and 31 (R6). Normal finalization remains
conditional on passing all review gates. The global standing autonomy policy
now authorizes routine reversible finding dispositions, preserving every lens,
gate, explicit cap, scope limit, and fresh-session boundary.

- R1: operator-decision-required. New actionable low finding; cycle-4 authorization permits clean finalization only and requires operator disposition for new findings. No fix or task creation authorized.
- R2: discard. Compatibility boundary required by PRD: preserve direct build_launch tier-key precedence and use the existing edge adaptation pattern. Plain-driver and third-party-driver route semantics are outside this correction; Blake explicitly acknowledges the chosen edge pattern. No new behavior or interface authorized.
- R3: operator-decision-required. New actionable low finding; cycle-4 authorization permits clean finalization only and requires operator disposition for new findings. No fix or task creation authorized.
- R4: operator-decision-required. New actionable low finding; cycle-4 authorization permits clean finalization only and requires operator disposition for new findings. No fix or task creation authorized.
- R5: operator-decision-required. New actionable low finding; cycle-4 authorization permits clean finalization only and requires operator disposition for new findings. No fix or task creation authorized.
- R6: operator-decision-required. New actionable low finding; cycle-4 authorization permits clean finalization only and requires operator disposition for new findings. No fix or task creation authorized.
- R7: known. KNOWN tooling limitation: historical tracked review diffs recursively include prior evidence. This belongs to external autopilot tooling, outside the adapter PRD. No historical evidence deleted; this cycle keeps its reproducible diff in docs/dev/tmp only.
- R8: discard. The automatic mixed-count ledger match is unrelated and is reversed. Correct disposition: previously settled bare reason phrases, JSON/SDK labels, and additional diagnostic grammar require separately specified forms/fixtures. Cycle-4 ledger explicitly excludes bare phrases and JSON labels. HTTPS and a generic code label gain no new contract. Preserve every reported example as KNOWN; no broader grammar authorized.
- R9: discard. Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.
- R10: discard. Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.
- R11: discard. Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.
- R12: discard. Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.
- R13: discard. Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.
- R14: discard. Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.
- R15: discard. Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.
- R16: discard. Required PRD compatibility controls: fixtures, direct tier/argv precedence, existing Codex probe and normal paths must remain unchanged. Fresh replay: 296 touched tests ran; 54 fail at base, 242 pass. Same-file historical ledger reasons still hold. These eight computed rows are retained, not silently dropped.

The other two automatic Blake dismissals remain settled: pre-existing relative-PATH/cwd disagreement, and intentionally pinned raw evidence for completed lane close. Raw numeric dismissal is corrected through R8 above. No actionable finding is resolved merely by its low severity.

## Alice

Provider: Anthropic; observed model claude-opus-5-5; effort xhigh.

[ALICE] ⚪ The task-28 and task-19 edits left the prose wrapping uneven. docs/driver-protocol.md:274 is 103 characters long, the only long line in the file that is not a link or a table row. Line 272 also runs past the file's ~80-column wrap. Lines 186-191 break after "tier-key precedence:", which makes the next sentence look like the start of a list, and line 191 stops at "`low`,". Fix: reflow both paragraphs to ~80 columns without changing any words | File: docs/driver-protocol.md | Task: 28

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

**Done.** I found one low doc-formatting issue and no medium or higher issues.

**Changed:** nothing, review only. What I checked:
- **Task 27:** the regex simplification behaves the same as before. "HTTP status 429", "HTTP error 503", the reqwest forms and the HTTP/2 forms all still classify correctly.
- **Long input:** 200k-character whitespace runs after every prefix take about 5 ms. "status " repeated 100k times takes 51 ms.
- **Task 28:** the doc and the CHANGELOG now agree on the "HTTP, status or error" wording.
- **Other claims I checked:** only `build_driver` constructs drivers in `src/`. The settings parser rejects an empty configured PATH. The probe and the supervisor spawn both merge `os.environ` with the overlay.

```
467 passed, 2 warnings (PRD-scoped files; same pytest temp-dir cleanup warnings already settled)
ruff check: All checks passed! | ruff format --check: 229 files already formatted | mypy: no issues in 61 source files
```

**Next:** Task complete. Suggested next: route the doc reflow into the minutes as a low, then run the decision gate for cycle 5.

## Blake

Provider: Anthropic; observed model claude-opus-5-5; effort xhigh.

[BLAKE] 🟡 Labeled status forms classify correctly, but HTTP diagnostics without a label now return `unknown` where the old bare-number match classified them. Reproduced: `429 Too Many Requests`, `503 Service Unavailable`, `HTTPS 503`, `{"status":429}`, `"statusCode": 401` and `code: 429` all give `unknown`. So a real 429 or 503 reported in one of these forms no longer gets rate-limit or connectivity WAIT handling. The PRD's "explicit HTTP/status/error-code context" rule allows this, but it narrows "genuine HTTP diagnostics", and there is no negative or positive pin for these forms | File: src/ovcaq/drivers/codex_events.py:300 | Task: P0-T1
[BLAKE] ⚪ The probe and the real launch can still find executables in different places when PATH has a relative or empty entry. The Codex probe spawns with no `cwd`, so it searches the supervisor's working directory. The launch spawns with `cwd=request.root`, and the CLI never changes into `--root`. The Claude probe reports an empty host PATH as unhealthy, yet the actual spawn would search root. This is an edge case of the "health checks and actual spawn agree" exit criterion. I reasoned it from Python's subprocess path lookup and did not reproduce it | File: src/ovcaq/drivers/codex.py:180 | Task: P1-T2
[BLAKE] ⚪ Every routine close of an already-completed lane (spawn, wait completed, close_agent shutdown) emits `raw.unknown` with reason "Malformed or unsupported Codex record". That label is wrong for a valid native record, and the test pins it as the contract. The TUI only shows raw evidence when nothing was normalized, so the visible impact is small | File: src/ovcaq/drivers/codex_events.py:233 | Task: P0-T1
[BLAKE] ⚪ Only the private subclasses built by `build_driver` map a resolved model back to its tier key. A Supervisor given a plain `CodexDriver`/`ClaudeDriver` or an entry-point driver still applies tier lookup to the resolved model, so `LaunchRequest.model` stays ambiguous between tier and model. This follows the PRD's chosen edge pattern; only the CLI path is protected | File: src/ovcaq/drivers/edge.py:16 | Task: P1-T1
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

Provider: Anthropic; observed model claude-opus-5-5; effort xhigh.

[BOB] ⚪ `test_authentication_is_classified_beyond_the_display_detail_limit` repeats `test_failure_classifies_full_text_before_sanitizing_and_capping_detail` (tests/drivers/test_codex_rework_decode.py:136). Both decode a failure for the same two event kinds and check that the class comes from text past the 4096-character display limit. Only the trailing word differs ("Unauthorized" vs "Rate limit reached"). No PRD feature touches this path, and the test passes on the base, so it is padding of the same kind tasks 20, 21 and 23 removed. Delete it. `json` and the `driver` fixture are still used by the capacity test | File: tests/drivers/test_adapter_failure_classes.py:231 | Task: 6
[BOB] ⚪ The capacity bound test runs `connectivity_retries` 0, 1, 2 and 3. Cases 0, 1 and 2 all take the same `retries.connectivity < policy.connectivity_retries` branch (src/ovcaq/runtime/decision.py:215). Only 2 (the last WAIT) and 3 (HALT) pin the bound. Drop cases 0 and 1 | File: tests/drivers/test_adapter_failure_classes.py:258 | Task: 6
[BOB] ⚪ `test_numeric_diagnostics_require_an_explicit_status_or_error_context` checks only the positive cases. The "require" half is tested by `test_unrelated_numbers_are_not_failure_diagnostics` (tests/drivers/test_adapter_failure_classes.py:156). Rename it for the rule it enforces, e.g. `test_numeric_codes_classify_with_explicit_status_or_error_context` | File: tests/drivers/test_adapter_failure_classes.py:67 | Task: 6
[BOB] ⚪ docs/driver-protocol.md:36 says both native adapters fall back to the standard default search path when the host PATH is missing. Only Claude has a test for this (`test_claude_probe_uses_default_search_path_when_host_path_is_absent`). The design says to "reproduce and regress" the existing Codex probe behavior. Parametrize the test over ("claude", "codex") and drop "claude" from its name. As I read `os.get_exec_path`, the patched `os.defpath` also steers the Codex subprocess lookup (not run) | File: tests/runtime/test_adapter_health.py:229 | Task: 3
[BOB] ⚪ This cycle's incremental diff is 378,503 lines, and only about 1,300 of them are product code, tests and docs. The rest is committed autopilot evidence, including review diffs that git can regenerate: a 169,912-line review-diff.diff and a 16 MB review-diff-00053-postrepair-20261012.diff.gz. Each committed review diff contains the earlier cycles' diffs, so the repo grows faster every cycle | File: docs/dev/project-management/autopilot/reports/00053-cycle3-20261013-evidence/review-diff.diff | Task: general

FIX:
- Duplicate classify-before-bound test, padding in a new file — tests/drivers/test_adapter_failure_classes.py:231 — delete `test_authentication_is_classified_beyond_the_display_detail_limit`; tests/drivers/test_codex_rework_decode.py:136 already covers the path
- Capacity bound test runs 0 and 1 through the same WAIT branch as 2 — tests/drivers/test_adapter_failure_classes.py:258 — keep only the `(2, WAIT)` and `(3, HALT)` cases
- Test name says "require" but the test checks only positives — tests/drivers/test_adapter_failure_classes.py:67 — rename to `test_numeric_codes_classify_with_explicit_status_or_error_context`
- Codex fallback to the default search path when host PATH is missing is documented but has no test — tests/runtime/test_adapter_health.py:229 — parametrize over `("claude", "codex")` and rename to `test_probe_uses_default_search_path_when_host_path_is_absent`
VERIFY:
- (none)
KNOWN:
- Committed review diffs that git can regenerate grow with every cycle (docs/dev/project-management/autopilot/reports/) — this is a repo-wide autopilot evidence practice: 23 tracked `.diff`/`.diff.gz` files going back to PRD 00004. It belongs to the autopilot tooling, not to this adapter PRD

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

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

## Cycle outcome

Five new actionable low findings (R1, R3-R6) require operator disposition under the recorded cycle-4 authorization. All raw rubrics pass; no unresolved CRITICAL/HIGH. No new repairs, cap increase, task creation, tail sweep, or convergence transition performed. Cycle/cap remain 5/5; completed tasks and implementation provenance unchanged.

Verdict: 16 findings
Tests: 7202 passed, 0 failed, 0 skipped (reused from last-verification.json at 93fd36f5da3138d8a0d52be7560e9aebb15ec12c)
