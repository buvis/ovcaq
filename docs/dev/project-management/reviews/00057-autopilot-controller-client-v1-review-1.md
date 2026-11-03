---
prd: docs/dev/project-management/prds/wip/00057-autopilot-controller-client-v1.md
review: 1
date: 2026-10-28
head_sha: fee44aeeab54517e5609085c81c2bb5ccc60d248
codex_thread_id: 01a17fed-4d65-7b12-b96a-a1f3bf842fd6
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: 3bbc8549
  carl: 24276630
---

# Review: 00057-autopilot-controller-client-v1

Diff range: `d440d982566c26252d1879fcd38800e7904e7ce1..fee44aeeab54517e5609085c81c2bb5ccc60d248`

codex_rung_guard: not fired

## Cycle numbering

This is cycle 1 of a **second review loop** for this PRD. The first loop
(batch 202610251552) ran three cycles and stalled `cap_regression` at cycle 3
with seven unresolved HIGH findings. A human un-parked the PRD, its Phase 1
section was amended with the five residual tasks R2-R7, and batch 202610272211
built them (`d440d982..fee44ae`, five tasks, all completed). The prior loop's
`review-1/2/3.md` and `checks-2/3.json` were moved to
`docs/dev/project-management/reviews/00057-attempt-202610251552/` so this loop's
cycle 1-3 filenames are free; the settled-decisions ledger stayed in place and
was passed to this cycle's reviewers, which is why eleven prior calls were
auto-dismissed rather than re-argued.

## Review Summary

Reviewed: 5 completed tasks
PRDs checked: 00057-autopilot-controller-client-v1.md

### Agent Status

- Alice: ✅ Available (consensus lens, legacy engine)
- Blake: ✅ Available (blind lens, PRD-only)
- Bob: ✅ Available (codex; doubt lens, D1-D5 + de-slop)
- Carl: ⚠️ Unavailable: gemini-run backend=copilot model=gemini-3.8-flash exited 1 — "You have exceeded your monthly quota". Retried once per retry policy, same result. This is a one-off runtime failure (quota), **not** the permanent exit-4 class, so Carl is NOT latched for the batch and will be tried again next cycle.
- Eve: ⏸️ Disabled: the codex doubt-roster guard did not fire (no task was implemented by codex), so the optional fifth lens was not activated.

### Degradations this cycle

- **Context pack unavailable.** `engram pack` exited 1 ("not inside a registered repo; run `gita add /Users/bob/git/src/github.com/buvis/ovcaq`"). Every prompt carried the `(no pack available this cycle)` sentinel, so no findings-precedent section reached the reviewers. A review without the pack is degraded, not invalid.
- **Gate counts parsed by hand.** `review-stage`'s gate step ran `./tools/check` once at HEAD and reported `Tests: counts unavailable (suite run this cycle, exit 1, no PASS/FAIL/SKIP/EXIT summary line)` — a parser miss, not a missing measurement: the padded summary line is in the log it wrote. The `Tests:` line below was composed from that log rather than by re-running the suite or by a second `autopilot verify` call (the prior run of which recorded nothing, `recorded: false`, exit 1). Provenance is named in the line itself.

## Alice (consensus lens)

Alice verified the prior loop's residuals against the code and confirmed R1, R2,
R4, R5, R6, R7, R8 and R12 resolved, and the ledger's over-800-line
`test_contract.py` fixed (608 lines; the digest tests moved to
`test_contract_digest.py`). She found R3 only partly resolved and raised three
findings.

```
[ALICE] 🟠 R3 is only partly fixed: the tool and the client still disagree on what a valid pinned bundle is ... (a) the tool lowercases the pin before comparing, while controller_bundle_digest compares it exactly ... (b) the tool uses plain json.loads, so it accepts duplicate keys and NaN/Infinity, which _parse_bundle rejects. | File: tools/autopilot-prerequisites:156 | Task: 4
[ALICE] 🟡 The rework removed redaction from controller-supplied fields echoed in IncompatibleContractError ... _truncated(live) at :498 and _truncated(live[field]) at :531 truncate but no longer redact package_version, schema_digest and fixture_digest. Before the rework these went through _bounded. | File: src/ovcaq/workflow_client.py:498 | Task: 3
[ALICE] ⚪ test_apply_launch_failure_is_plain_controller_error asserts isinstance(caught.value, ControllerError) right after pytest.raises(ControllerError), which cannot fail. | File: tests/workflow_client/test_apply_outcome_unknown.py:1038 | Task: 2
```

Notes she recorded: `apply` is 42 lines and `_run` 34, both under the 50-line
limit; she did not re-raise the settled ledger items; she dismissed the replay
`[MECH]` rows herself on the ground that 41 of 104 touched tests do fail against
base.

Narrow check she ran: `uv run --locked python -m pytest tests/workflow_client -q` → 851 passed.

Verdicts: R1: fail, R2: pass, R3: pass, R4: fail, R6: pass, R7: pass, R8: pass, R9: fail, R10: pass, R11: pass, R12: pass, R13: pass

## Blake (blind lens, PRD-only)

Blake found the code himself from the PRD alone and reported no Critical or High
issues. He confirmed every acceptance test named in the PRD exists, that `_run`
no longer uses `with process:`, that readers close their own streams and are
never joined, that apply wraps every post-spawn `ControllerError` in
`ApplyOutcomeUnknownError` carrying the request id, that `_redact` never reads
the actor file, that one raw-bytes sha256 is shared by the client and the tool,
that the dependency graph matches the spec table, and that there are no
plugin-cache imports and no shell evaluation.

Three of his eight findings were auto-dismissed against the settled ledger (see
below). The surviving five:

```
[BLAKE] 🟡 The bundle validators disagree. The client parses strictly (rejects duplicate keys and NaN/Infinity, src/ovcaq/workflow_client.py:237), but tools/autopilot-prerequisites uses plain json.loads. | File: tools/autopilot-prerequisites:159 | Task: 4
[BLAKE] 🟡 Redaction masks only whitespace-delimited tokens of 8 or more characters. A secret shorter than MIN_SECRET_CHARS, or one split across whitespace, passes through stderr detail unmasked. | File: src/ovcaq/workflow_client.py:396 | Task: 3
[BLAKE] ⚪ Controller-supplied strings in IncompatibleContractError messages (live schema_digest, fixture_digest, package_version) are truncated but never redacted. | File: src/ovcaq/workflow_client.py:531 | Task: general
[BLAKE] ⚪ The spec says a launch failure "stays a plain ControllerError". The code raises the ControllerLaunchError subclass for any OSError from Popen, which is broader than FileNotFoundError and PermissionError. | File: src/ovcaq/workflow_client.py:468 | Task: 2
[BLAKE] ⚪ After a timeout the abandoned daemon reader threads live until the detached descendant releases the pipe (8 s in the test). The caller's bound holds, but threads and fds can linger. | File: src/ovcaq/workflow_client.py:328 | Task: 1
```

Narrow check he ran: `uv run pytest tests/workflow_client -q` → 851 passed. He did not run the full suite.

Verdicts: B1 through B19: all pass.

## Bob (codex; doubt lens + de-slop)

FIX:
```
[BOB] 🟠 Short credentials still leak. _redact("auth bad abc") preserves abc, even when it is the actor credential; the new short-credential test explicitly expects disclosure. Suppress controller diagnostics whenever credential safety cannot be established without reading the file, and test an echoed short credential. | File: src/ovcaq/workflow_client.py:396 | Task: 3
[BOB] 🟠 Negotiation diagnostics now bypass redaction: package-version and digest mismatches use _truncated(live) instead of _bounded(live). A controller can return credential bytes in these fields and expose them in exceptions. Restore the redaction pipeline and add mismatch tests containing synthetic secrets. | File: src/ovcaq/workflow_client.py:528 | Task: 3
[BOB] 🟠 Bundle validation still differs between consumers. The prerequisite tool retains its own hash and permissive json.loads, accepting matching-pinned bundles containing duplicate keys or NaN that the client rejects. Use the shared strict bundle-validation/digest entry point, retain the size/path guards, and test both consumers against these malformed bundles. | File: tools/autopilot-prerequisites:156 | Task: 4
```

VERIFY:
- (none)

KNOWN:
- (none)

Consensus rubric verdicts: R1: fail, R2: fail, R3: pass, R4: fail, R6: pass, R7: fail, R8: pass, R9: fail, R10: pass, R11: pass, R12: pass, R13: pass

Doubt rubric verdicts:
```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

No VERIFY item named a runnable command, so no verification-check queue was
written for this cycle.

## Carl (UI / frontend & design)

Carl: unavailable (gemini-run backend=copilot model=gemini-3.8-flash, exit 1,
"You have exceeded your monthly quota"; retried once, same result). No Carl
output was produced and none was consolidated. The diff is a Python transport
client, a stdlib CLI gate, docs and tests, with no frontend surface, so his
absence costs this cycle little.

## Mechanical checks (computed)

Tautological test shapes: 189 test functions checked across 11 test files, none
flagged.

Fail-first replay against `d440d982566c`: 104 touched tests ran, 41 failed
against base, 63 passed, and 3 test files could not be collected at base. The 41
failures are what pin this change. The 63 passers produced the eight `[MECH]`
rows absorbed into the table below (R9 to R16); they are pre-existing tests
living inside touched files, which is the same case the settled ledger already
discarded in the prior loop's cycles 2 and 3, and Alice refuted them
independently.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/3] | 🟠 High | One definition for a valid pinned bundle is still missing. The tool keeps its own `hashlib.sha256` and plain `json.loads`. (a) The tool lowercases the pin before comparing while `controller_bundle_digest` compares it exactly, confirmed by probe: an uppercase `contract_bundle_sha256` passes the PRD 58 gate and then fails `contract()` with `IncompatibleContractError`; the existing test at tests/workflow_client/test_prerequisites_controller.py:94 passes the tool an `.upper()` pin. (b) The tool's plain `json.loads` accepts duplicate keys and `NaN`/`Infinity` that `_parse_bundle` rejects. Normalise the pin once and give the tool the same strict parse (stdlib-only: copy the hooks, never import ovcaq), then test one configured value through both consumers with an uppercase pin and with a duplicate-key bundle. | tools/autopilot-prerequisites:156 | 4 | Alice, Blake, Bob |
| R2 | [3/3] | 🟠 High | Negotiation diagnostics bypass redaction — a regression this cycle's own rework introduced. `_truncated(live)` at src/ovcaq/workflow_client.py:498 and `_truncated(live[field])` at :531 truncate but no longer redact `package_version`, `schema_digest` and `fixture_digest`, which went through `_bounded` before the rework. A controller that echoes credential bytes into those fields reaches the exception text verbatim, and no test pins either behaviour. Restore the redaction pipeline (or record the deviation in the docstring) and add mismatch tests carrying synthetic secrets. | src/ovcaq/workflow_client.py:498 | 3 | Alice, Blake, Bob |
| R3 | [2/3] | 🟠 High | Short credentials still leak. `_redact("auth bad abc")` preserves `abc` even when it is the actor credential, and the new short-credential test explicitly expects disclosure; a secret split across whitespace also passes through. The PRD's task-3 acceptance criterion requires that "a secret shorter than `MIN_SECRET_CHARS` and an unreadable actor file both yield a redacted diagnostic, never the raw controller output", so the length-based construction only partly meets it. Suppress controller diagnostics whenever credential safety cannot be established without reading the actor file, and test an echoed short credential. | src/ovcaq/workflow_client.py:396 | 3 | Blake, Bob |
| R4 | [1/3] | ⚪ Low | `test_apply_launch_failure_is_plain_controller_error` asserts `isinstance(caught.value, ControllerError)` right after `pytest.raises(ControllerError)`, which cannot fail. The new public `ControllerLaunchError` is never asserted, so `launch_failure_stays_plain_controller_error` is satisfied by any `ControllerError` subclass. | tests/workflow_client/test_apply_outcome_unknown.py:1038 | 2 | Alice |
| R5 | [1/3] | ⚪ Low | The spec says a launch failure "stays a plain ControllerError". The code raises the `ControllerLaunchError` subclass for any `OSError` from `Popen`, broader than `FileNotFoundError` and `PermissionError`. It is still catchable as `ControllerError`, so the intent holds; the subclass is an extra symbol. | src/ovcaq/workflow_client.py:468 | 2 | Blake |
| R6 | [1/3] | ⚪ Low | After a timeout the abandoned daemon reader threads live until the detached descendant releases the pipe (8 s in the test). The caller's bound holds, but threads and fds can linger. | src/ovcaq/workflow_client.py:328 | 1 | Blake |
| R7 | [1/3] | 🟡 Medium | 2 touched tests pass against the pre-change code: test_the_published_redaction_constants_keep_their_values, test_detail_keeps_secret_free_and_multibyte_stderr_whole | tests/workflow_client/test_actor_secret_redaction.py | general | mech-check |
| R8 | [1/3] | 🟡 Medium | 17 touched tests pass against the pre-change code: test_apply_raises_outcome_unknown_on_output_bound_overrun, test_apply_raises_outcome_unknown_on_non_json_stdout_after_zero_exit, test_apply_raises_outcome_unknown_on_malformed_response +11 more | tests/workflow_client/test_apply_outcome_unknown.py | general | mech-check |
| R9 | [1/3] | 🟡 Medium | 3 touched tests pass against the pre-change code: test_envelope_rejects_missing_request_or_project_id_on_initial_open | tests/workflow_client/test_contract.py | general | mech-check |
| R10 | [1/3] | 🟡 Medium | 27 touched tests pass against the pre-change code: test_bundle_digest_is_stable_for_the_fixture, test_bundle_digest_matches_byte_copy_at_another_path, test_bundle_digest_detects_single_byte_value_change, test_bundle_digest_rejects_mismatched_artifact +21 more | tests/workflow_client/test_contract_digest.py | general | mech-check |
| R11 | [1/3] | 🟡 Medium | 3 touched tests pass against the pre-change code: test_nonzero_exit_message_keeps_only_a_marked_tail_of_long_prose_stderr | tests/workflow_client/test_controller_boundary.py | general | mech-check |
| R12 | [1/3] | 🟡 Medium | 5 touched tests pass against the pre-change code: test_kill_group_completes_within_bounded_time_when_signal_is_denied, test_kill_group_reports_a_signal_failure_that_is_not_a_denial, test_kill_group_ends_a_grandchild_sharing_the_controller_group, test_capture_completes_within_bounded_time_when_a_pipe_stays_open | tests/workflow_client/test_kill_group_bounded.py | general | mech-check |
| R13 | [1/3] | 🟡 Medium | 1 touched test passes against the pre-change code: test_contract_rejects_pinned_bundle_without_operations_or_capabilities | tests/workflow_client/test_negotiation.py | general | mech-check |
| R14 | [1/3] | 🟡 Medium | 5 touched tests pass against the pre-change code: test_call_raises_timeout_when_controller_outlives_timeout, test_apply_never_returns_result_when_ack_precedes_timeout | tests/workflow_client/test_transport.py | general | mech-check |

### Consolidation note

`consolidate_findings.py` emitted eight rows and merged two citation pairs after
suffix stripping (`tools/autopilot-prerequisites:156 ~ :159`,
`src/ovcaq/workflow_client.py:498 ~ :531`). Two further merges are this gate's
judgment on issue text plus file, recorded here so the regrouping is legible:
Bob's negotiation-redaction row (`:528`) names the same defect as Alice's and
Blake's (`:498`/`:531`) and is folded into **R2**, carrying Bob's HIGH severity;
Blake's short-credential row (`:396`) names the same defect as Bob's and is
folded into **R3**, likewise carrying HIGH. The eight `[MECH]` replay rows were
absorbed as R7 to R14 per step 6 rather than dropped.

### Auto-dismissed (ledger)

- [BLAKE] 🟡 contract_bundle_sha256 is optional in controller_settings/ControllerConfig. When unset the client skips the digest check and trusts whatever bundle file is on disk. This weakens "validate producer identity/digests" and is fail-open by default. tools/autopilot-prerequisites only enforces the digest for PRD 58, so a consumer that skips the tool is unpinned. | File: src/ovcaq/config.py:326 — single-voice
- [BLAKE] ⚪ RevisionConflictError and RejectedRequestError are defined but never raised or used in src. They are dead API surface and the first shadows the state-store class of the same name. | File: src/ovcaq/workflow_client.py:77 — single-voice
- [BLAKE] ⚪ Unknown PRD IDs and config errors exit 2 with a stderr message and no JSON. The spec output is "Exit 0 ready or 1 unavailable with JSON diagnostics". The exit code is documented in docs/operations.md and the generator, so this is a deviation but a safe one. | File: tools/autopilot-prerequisites:44 — single-voice; exit 2 for a usage error is the argparse convention and the PRD's own Behavior text says unknown IDs and missing config must "fail", which exit 2 satisfies. The R1/R19 fix keeps exit 2 for usage errors deliberately.

Verdict: 14 findings
Tests: 8136 passed, 61 failed, 14 errors (suite run this cycle; counts read from this cycle's own gate log docs/dev/tmp/gate-00057-c1-20261028.log:6109 after review-stage failed to parse the padded summary line. ruff check, ruff format --check and mypy are clean; uv build is never reached because the mise chain stops at pytest's exit. Every failure and error is in tests/integration/ (57 failed, 14 errors) or tests/tui/ (4 failed), the sandbox denies /bin/ps and the log carries 17 `PermissionError: [Errno 1] Operation not permitted: 'ps'`, and this cycle's diff touches no file under either tree; tests/workflow_client is green at 851 passed)
