---
prd: docs/dev/project-management/prds/wip/00057-autopilot-controller-client-v1.md
review: 3
date: 2026-10-26
head_sha: fa26fb71a8f6917a810eb598ed9601f7c90f3604
codex_thread_id: 01a17481-0b54-7c21-9c66-fdab3c6ab821
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: e3b2e0f0
---

# Review: 00057-autopilot-controller-client-v1

Diff range: `b53efd3195d31987456bd071d830cb599a335d56..fa26fb71a8f6917a810eb598ed9601f7c90f3604`

codex_rung_guard: not fired

carl: skipped (permanently unavailable since cycle 2 of 00057-autopilot-controller-client-v1.md)

## Review Summary

Reviewed: 10 completed tasks (4 cycle-2 rework tasks in this incremental range)
PRDs checked: 00057-autopilot-controller-client-v1.md
Scope: incremental — the cycle-2 rework commits only. Cycles 1 and 2 reviewed the earlier ranges.

### Agent Status

- Alice: ✅ Available (consensus lens, legacy engine)
- Blake: ✅ Available (blind lens, PRD-only)
- Bob: ✅ Available (codex, doubt lens D1-D5 + de-slop; codex thread `01a17481` resumed from cycle 2)
- Carl: ❌ Batch-skipped. Latched permanently unavailable for batch 202610251552 since cycle 2 of this PRD (exit 4, `IneligibleTierError`). No dispatch, no `ui` lens key, no output consolidated.

### Cycle notes

- `consensus_engine: legacy`, `doubt_reviewer: codex`. The codex doubt-roster guard did not fire: no task has a `codex` implementor, so Eve was not activated.
- Context pack unavailable this cycle: `engram pack` exited 1 (`not inside a registered repo; run gita add /Users/bob/git/src/github.com/buvis/ovcaq`). Prompts carried the `(no pack available this cycle)` sentinel. A review without the pack is degraded, not invalid.
- Bob's dispatch row `e3b2e0f0` reports the *staged* prompt size, not the inlined prompt actually sent to codex (26963 bytes recorded against 144795 bytes sent). The row was not re-opened; the understatement is recorded here instead, as in cycles 1 and 2.
- The settled-decisions ledger (27 entries) was passed to Alice's and Bob's prompts and to `consolidate_findings.py` as `--ledger` with `--ledger-dismiss BLAKE`. Two Blake re-raises were auto-dismissed — see below.
- The cycle-2 verification-check queue (`00057-...-checks-2.json`) is an empty array, so no failed checks were carried forward.
- **The project gate is RED at this HEAD, and the failure is inside this PRD's own diff.** `./tools/check` exited 1 at its first step: `uv run --locked ruff check .` found 1 error, BLE001 ("Do not catch blind exception: `BaseException`") at `tests/workflow_client/test_kill_group_bounded.py:56`, a test added by the cycle-2 rework. ruff format, mypy, the full pytest run and `uv build` were never reached. `autopilot verify --gate-command ./tools/check --cycle 3` reproduced exit 1 with no summary line (`docs/dev/tmp/gate-fa26fb7.log`). A narrow `uv run --locked python -m pytest tests/workflow_client -q` gives **782 passed in 41.36s**. All three reviewers raised the lint failure independently (R1).

### Auto-dismissed (ledger)

- [BLAKE] 🟡 `RevisionConflictError` and `RejectedRequestError` are defined but never raised anywhere in src. They are "typed errors" in name only. Rejections come back as `ApplyResult(ok=False, error_code=...)`, which is acceptable as a typed apply response, but the dead exception classes are unused surface. | File: src/ovcaq/workflow_client.py:61 — single-voice
- [BLAKE] 🟡 `tools/autopilot-prerequisites` exits 2, with a message on stderr and no JSON, for an unknown PRD or a config error. | File: tools/autopilot-prerequisites:40 — single-voice; exit 2 for a usage error is the argparse convention and the PRD's own Behavior text says unknown IDs and missing config must "fail", which exit 2 satisfies.

Both dismissals are correct: each matches a ledger entry at the same defect and file.

### Consolidation corrections (model-side, applied on top of the script output)

`consolidate_findings.py` produced 19 rows and warned that two rows merged only
after citation-suffix stripping. Both merges are correct; four under-merges were
corrected. Both directions are recorded so the table is not silently wrong.

- **Correct merges.** Script row 3 (`tools/autopilot-prerequisites:137 ~ :154`) — Alice and Bob each name the same digest-definition split. Script row 4 (`workflow_client.py:450 ~ :555`) — Blake and Bob each name the post-spawn abnormal-exit gap.
- **Under-merge corrected (now R1).** Blake's 🟠 gate row and the merged Alice/Bob 🟠 gate row are the same BLE001 failure at the same file and line. R1 now carries three-of-three consensus.
- **Under-merge corrected (now R4).** Alice's ⚪ "nonzero exit after spawn" residual is the same defect as the Blake/Bob 🟠 row. Folded in; R4 carries three-of-three consensus and keeps the higher severity.
- **Under-merge corrected (now R5).** Bob's 🟠 redaction row and Alice's 🟡 "prior R4 only partly resolved" row both say the client still reads the actor file on every `_redact` call. Two-of-three consensus, higher severity kept.
- **Under-merge corrected (now R7).** Alice's 🟡 `ApplyOutcomeUnknownError`-inheritance row and Bob's 🟡 misclassification row are one defect at different lines of the same file. Two-of-three consensus.
- **Mechanical rows absorbed as R16-R19**: four fail-first replay rows. None matched an existing row's file and test, so each is its own row with `Found by: mech-check`. The tautological-shape check found zero rows this cycle (64 test functions in 7 files).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/3] | 🟠 | The project gate fails. `uv run --locked ruff check .` reports BLE001 on `except BaseException as error` in the cycle-2 rework test, so `./tools/check` exits 1 before ruff format, mypy, pytest or the build. The PRD's Phase 2 exit criterion "`./tools/check` passes" is therefore not met. Fix by dropping the blind try/except and recording the worker's outcome another way (for example `threading.excepthook`, or a thread that stores `_kill_group`'s result). A suppression marker is not allowed. Run directly, ruff format (256 files) and mypy are clean, and `pytest tests/workflow_client` gives 782 passed. | tests/workflow_client/test_kill_group_bounded.py:56 | 7 | ALICE, BOB, BLAKE |
| R2 | [2/3] | 🟠 | Prior R5 is only half fixed. `_kill_group` now bounds its own `wait`, but `_run` still exits `with process:`. `Popen.__exit__` closes the pipes and then calls an unbounded `wait()`, and the close blocks while a reader thread sits in `read()`. Alice's probe: a fake controller that exits at once but leaves a `start_new_session=True` descendant holding stdout/stderr for 8 s, with `timeout_seconds=1`, made `_run("contract")` raise `ControllerTimeoutError` only after 8.04 s. The new tests call `_kill_group` and `_capture` directly with fake processes and never go through `_run`'s `with` exit. Bound the cleanup (close the pipes without joining the reader threads, reap with a timeout instead of `with process:`) and add an end-to-end test with a detached descendant that asserts elapsed time. | src/ovcaq/workflow_client.py:448 | 7 | ALICE, BOB |
| R3 | [2/3] | 🟠 | The key `[workflow].contract_bundle_sha256` has two incompatible digest definitions. `tools/autopilot-prerequisites` hashes the raw file bytes; the client passes the same key to `ControllerConfig.bundle_digest`, which `_bundle_digest` checks against sha256 of `json.dumps(data, sort_keys=True)`. On the real pinned fixture `tests/fixtures/workflow/controller-v1.json` the two differ (raw `c40ba84e…`, canonical `b98f0a68…`). An operator who sets the key to pass the PRD 58 gate gets `IncompatibleContractError` from `contract()`, and the reverse also fails. The tests miss it because every payload they use is compact sorted-key JSON, where the two digests coincide. Pick one definition for both sides and add a test with the real fixture (or a pretty-printed bundle) that passes the tool and `controller_settings` with one configured value. | tools/autopilot-prerequisites:137 | 8 | ALICE, BOB |
| R4 | [3/3] | 🟠 | Abnormal post-spawn exits still escape unknown-outcome handling. Timeouts, output overruns and malformed responses become `ApplyOutcomeUnknownError`, but a non-zero exit during apply raises a plain `ControllerError`. A controller killed or crashed after committing but before acking is therefore reported as a definite failure rather than unknown-outcome-retry-same-envelope, and the client has no retry of its own. Distinguish launch failures from post-spawn failures and test commit-then-signal termination with preserved request identity. | src/ovcaq/workflow_client.py:450 | 1.1 | BLAKE, BOB, ALICE |
| R5 | [2/3] | 🟠 | Redaction still reads credentials and still discloses in two cases: secrets shorter than `MIN_SECRET_CHARS` are never redacted, and an unreadable actor file makes redaction a silent no-op while the controller (which may have read access) can still echo the secret. Removing the cache fixed only rotation. The client also opens and reads the actor file on every `_redact` call, up to `max_output_bytes`, although the design says the client never reads the credential's bytes. Preserve the opaque actor-file boundary and suppress unsafe diagnostics, or record the deviation in the docstring and the design note; replace the test that explicitly expects disclosure. | src/ovcaq/workflow_client.py:350 | 7 | BOB, ALICE |
| R6 | [1/3] | 🟠 | Bundle validation accepts arbitrary JSON, including `null` and `{}`, although the client rejects these as contracts. Validate the required Contract A structure and strict JSON rules, and use actual contract fixtures instead of arbitrary objects in the readiness tests. | tools/autopilot-prerequisites:157 | 8 | BOB |
| R7 | [2/3] | 🟡 | `ApplyOutcomeUnknownError` still subclasses `ControllerTimeoutError` and its docstring still says "An apply timed out", yet it is now also raised for output overruns, non-JSON stdout and malformed responses. A caller catching `ControllerTimeoutError` therefore also catches completed-but-ambiguous calls. Give unknown outcomes a shared `ControllerError` base, keep timeout classification for actual timeouts, and fix the docstring. | src/ovcaq/workflow_client.py:50 | 7 | ALICE, BOB |
| R8 | [1/3] | 🟡 | `docs/operations.md` does not document the client-side `contract_bundle_sha256` key. The `[workflow]` TOML example lists only `controller_argv`, `contract_bundle` and `actor_file`; the key appears only inside the PRD 58 prerequisite sentence, with "sha256 matches" and no definition of which digest. The wiring added for prior R2 is therefore undiscoverable. State the key and its digest form in the client section. | docs/operations.md:104 | 10 | ALICE |
| R9 | [1/3] | 🟡 | `ControllerClient.snapshot(workflow_id=...)` validates `workflow_id` and then drops it. The argv is only `snapshot --project-root <root>`, and the payload is returned unmodified with no check that it belongs to the requested workflow; `tests/workflow_client/test_transport.py:207` even returns a `workflow-b` snapshot for a `workflow-a` request. A mismatched snapshot is silently accepted. | src/ovcaq/workflow_client.py:522 | 1.1 | BLAKE |
| R10 | [1/3] | 🟡 | Bundle digest pinning is optional. `contract_bundle_sha256` may be absent, and `bundle_digest=None` then skips the integrity check completely, so the client only compares the controller's answers to whatever file sits at the path. That is fail-open for "validate producer identity/digests" and "imported schema copies are not authoritative"; only the prerequisites tool makes the sha mandatory. | src/ovcaq/config.py:326 | general | BLAKE |
| R11 | [1/3] | 🟡 | No producer provenance is frozen or checked. `tests/fixtures/workflow/controller-v1.json` carries only `protocol_major`, `package_version`, two digests, operations and capabilities — no producer name, identity or provenance record — so `package_version` is the only identity check, although the Phase 0 task says "freeze imported producer bundle/provenance". | tests/fixtures/workflow/controller-v1.json | general | BLAKE |
| R12 | [1/3] | 🟡 | `docs/operations.md` changed without updating the generator's `CONTROLLER_CLIENT_NOTES`. Update the generator, regenerate the document, and check parity with `render_command_reference()`. | docs/operations.md:109 | 10 | BOB |
| R13 | [1/3] | ⚪ | In `test_capture_completes_within_bounded_time_when_a_pipe_stays_open`, `process` is referenced in `finally` but is unbound if `os.fdopen` or the process construction raises. | tests/workflow_client/test_kill_group_bounded.py:624 | 7 | ALICE |
| R14 | [1/3] | ⚪ | The done-bucket path (`DONE`) is resolved relative to the current directory, not the project root, so running the tool from a subdirectory reports every predecessor as missing. It fails closed, but it does not fit use as a consumer gate. | tools/autopilot-prerequisites:20 | 1.2 | BLAKE |
| R15 | [1/3] | ⚪ | Evidence for PRD 58/61/65 is a self-declared `evidence` list inside a JSON file pinned only by a sha from the same config, so provenance is only as strong as the config (though bounded to 16 MiB and symlink-checked). The tokens are `AP00017` and `Lantern00003`; the spec says AP17 and Lantern03. | tools/autopilot-prerequisites:30 | 1.2 | BLAKE |
| R16 | [1/3] | 🟡 | 1 touched test passes against the pre-change code: test_redact_with_unreadable_actor_file_does_not_raise | tests/workflow_client/test_actor_secret_redaction.py | general | mech-check |
| R17 | [1/3] | 🟡 | 4 touched tests pass against the pre-change code: test_apply_raises_outcome_unknown_on_timeout, test_snapshot_raises_plain_output_error_on_output_bound_overrun, test_snapshot_raises_plain_output_error_on_non_json_stdout, test_snapshot_raises_plain_output_error_on_non_dict_response | tests/workflow_client/test_apply_outcome_unknown.py | general | mech-check |
| R18 | [1/3] | 🟡 | 5 touched tests pass against the pre-change code: test_controller_settings_rejects_unusable_contract_bundle, test_controller_settings_omits_bundle_digest_without_the_key | tests/workflow_client/test_config.py | general | mech-check |
| R19 | [1/3] | 🟡 | 8 touched tests pass against the pre-change code: test_call_rejects_stdout_over_output_bound, test_call_rejects_unparseable_stdout_on_zero_exit +2 more | tests/workflow_client/test_transport.py | general | mech-check |

## Alice

Alice verified the cycle-2 findings at this HEAD:

- R1 (apply ambiguity): resolved for the listed cases, with positive and negative tests.
- R2 (digest wiring): code wired, config key validated and tested — but the two digest definitions do not agree (R3 above).
- R3 (docs): resolved for the PRD 58 gate and the negotiation wording.
- R4 (redaction): partial — see R5 above.
- R5 (bounded cleanup): partial — see R2 above.
- R6/R11 (bundle content and provenance in the tool): the tool now reads, hashes and parses the bundle, but see R3 and R6.
- R13: documented in the `_actor_secrets` docstring.
- The rest are settled or low and unchanged.

Gate facts she rechecked herself: `ruff check` has 1 error (R1), `ruff format --check .` is clean, `mypy` is clean. She did not re-run the full pytest suite beyond the 782-pass `tests/workflow_client` run. Scratch files were left outside the repo, in `/tmp/alice-scratch-c3`.

New findings: R1, R2, R3, R4, R5, R7, R8, R13 (see the table).

R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

## Blake

Covered and OK:

- Argv-only `Popen` with no shell, `start_new_session` and process-group kill.
- Both streams capped at the output bound, with a timeout.
- Actor secret passed by file path, never in argv, and redacted from error text.
- A private 0600 request file, always unlinked.
- Protocol major, schema and fixture digests, package version, operations and capabilities checked before any snapshot or apply.
- Strict bundle parsing that rejects duplicate keys and NaN.
- No plugin import: AST test and runtime probe.
- Predecessors accepted only from the `done/` bucket, with no symlinks or backlog files.
- Read-only, no fetch or write.
- `docs/operations.md` and `CHANGELOG.md` updated.

New findings: R1, R4, R9, R10, R11, R14, R15 (see the table).
Two re-raises were auto-dismissed against the ledger (above).

B1: fail
B2: pass
B3: pass
B4: pass
B5: fail
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: fail
B17: pass
B18: pass
B19: pass

## Bob

FIX:
- [BOB] 🟠 The shared `contract_bundle_sha256` key has incompatible meanings: the prerequisite tool hashes raw bytes, while the client hashes canonical JSON. Formatted bundles therefore cannot satisfy both consumers with one pin. Use one digest convention and add a config-to-gate-to-client integration test. | File: tools/autopilot-prerequisites:154 | Task: general
- [BOB] 🟠 Redaction still reads credentials and deliberately exposes short secrets or diagnostics when credential reads fail. Removing caching fixes only rotation. Preserve the opaque actor-file boundary, suppress unsafe diagnostics, and replace the test that explicitly expects disclosure. | File: src/ovcaq/workflow_client.py:350 | Task: 7
- [BOB] 🟠 Cleanup remains unbounded through `_run()`'s `Popen` context manager: pipe closure can block behind surviving readers, and context exit can wait indefinitely after denied termination. The new tests bypass that context by calling helpers directly. Fix and test the complete public-call cleanup path. | File: src/ovcaq/workflow_client.py:448 | Task: 7
- [BOB] 🟠 Bundle validation accepts arbitrary JSON, including `null` and `{}`, although the client rejects these as contracts. Validate the required Contract A structure and strict JSON rules; use actual contract fixtures instead of arbitrary objects in readiness tests. | File: tools/autopilot-prerequisites:157 | Task: 8
- [BOB] 🟠 Abnormal post-spawn exits still escape unknown-outcome handling as plain `ControllerError`. A controller killed after committing has the same acknowledgement ambiguity. Distinguish launch failures from post-spawn failures and test commit-then-signal termination with preserved request identity. | File: src/ovcaq/workflow_client.py:555 | Task: 7
- [BOB] 🟡 Malformed and oversized responses now raise an exception inheriting `ControllerTimeoutError`, misclassifying completed calls as timeouts. Give unknown outcomes a shared `ControllerError` base and retain timeout classification only for actual timeouts. | File: src/ovcaq/workflow_client.py:555 | Task: 7
- [BOB] 🟡 The supplied check fails on BLE001 at the new worker's `BaseException` handler. Make exception capture lint-compliant while preserving parent-thread failure reporting. | File: tests/workflow_client/test_kill_group_bounded.py:56 | Task: 7
- [BOB] 🟡 The operations document changed without updating the generator's `CONTROLLER_CLIENT_NOTES`. Update the generator, regenerate the document, and check parity with `render_command_reference()`. | File: docs/operations.md:109 | Task: 10

VERIFY:
- (none)

KNOWN:
- (none)

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: fail
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Carl: skipped (permanently unavailable since cycle 2 of 00057-autopilot-controller-client-v1.md). Latched for batch 202610251552 on exit 4 (`IneligibleTierError`, `UNSUPPORTED_CLIENT`, free tier). No dispatch this cycle, no output consolidated.

## Mechanical checks

- Tautological test shapes: 64 test functions checked in 7 test files; **0** `[MECH]` lines.
- Fail-first replay (`uv run python -m pytest`, base `b53efd3195d3`): 34 touched tests ran, **16 failed against base**, 18 passed; 2 test files could not be collected at base. The four `[MECH]` lines naming the 18 passers are absorbed as R16-R19. The rework's own new tests do pin the change; the passers are pre-existing tests inside the same touched files.
- Mechanical facts block: computed per-function line counts were available to every implementation-aware lens; no finding contradicts it.

## Test gate

`./tools/check` (`mise run check`: ruff, ruff format, mypy, pytest, uv build) at `fa26fb71` **exited 1 at the first step**: `uv run --locked ruff check .` found 1 error (BLE001, `tests/workflow_client/test_kill_group_bounded.py:56`). ruff format, mypy, pytest and `uv build` were never reached. Logs: `docs/dev/tmp/gate-00057-c3-20261026.log` and `docs/dev/tmp/gate-fa26fb7.log`.

This PRD's own scope was run narrowly instead: `uv run --locked python -m pytest tests/workflow_client -q` → **782 passed in 41.36s**. Run directly, `ruff format --check .` and `mypy` are clean (Alice reproduced both). The full pytest suite remains red in this sandbox for the pre-existing, out-of-scope macOS-seatbelt `PermissionError` denials of `ps` (tests/runtime, tests/tui, tests/integration, tests/packaging, tests/drivers).

Verdict: 19 findings
Tests: 782 passed (tests/workflow_client at fa26fb71; ./tools/check exited 1 at ruff check — BLE001, finding R1 — so ruff format, mypy, the full pytest run and uv build never ran this cycle; see docs/dev/tmp/gate-fa26fb7.log)
