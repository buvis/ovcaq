---
prd: docs/dev/project-management/prds/wip/00057-autopilot-controller-client-v1.md
review: 1
date: 2026-10-25
head_sha: e78015922abafe754b2118c9974f2339a325e620
codex_thread_id: 01a17481-0b54-7c21-9c66-fdab3c6ab821
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: 631769be
  carl: ce07f78b
---

# Review: 00057-autopilot-controller-client-v1

Diff range: `3f6b8b83876f225641968058d3cde0572e3dd434..e78015922abafe754b2118c9974f2339a325e620`

codex_rung_guard: not fired

## Review Summary

Reviewed: 2 completed tasks
PRDs checked: 00057-autopilot-controller-client-v1.md

### Agent Status

- Alice: ✅ Available (consensus lens, legacy engine)
- Blake: ✅ Available (blind lens, PRD-only)
- Bob: ✅ Available (codex, doubt lens D1-D5 + de-slop)
- Carl: ⚠️ Unavailable: copilot backend exit 1 "You have exceeded your monthly quota"; one retry forced `GEMINI_BACKEND=gemini`, which failed exit 1 with `mise ERROR No version is set for shim: gemini`. Retry budget spent, both backends unusable. Not latched to the batch (exit 1 is a transient/quota failure, not the permanent exit-4 class).

### Cycle notes

- `consensus_engine: legacy`, `doubt_reviewer: codex`. The codex doubt-roster guard did not fire: no task has a `codex` implementor (both tasks ran `claude`/opus), so Eve was not activated.
- Context pack unavailable this cycle: `engram pack` exited 1 (`not inside a registered repo; run gita add ...`). Prompts carried the `(no pack available this cycle)` sentinel. A review without the pack is degraded, not invalid.
- Bob's dispatch row `631769be` reports the *staged* prompt size, not the inlined prompt actually sent to codex (9536 bytes recorded against 185417 bytes sent). The row was not re-opened; the understatement is recorded here instead.
- No settled-decisions ledger existed for this PRD (cycle 1), so `consolidate_findings.py` ran without `--ledger`/`--ledger-dismiss` and nothing was auto-dismissed.
- No prior-cycle verification-check queue exists, so no failed checks were carried forward.

### Consolidation corrections (model-side, applied on top of the script output)

`consolidate_findings.py` produced 30 rows and warned that three rows merged only
after citation-suffix stripping. Two of those merges were wrong and were undone;
one under-merge set was corrected. Both directions are recorded so the table is
not silently wrong:

- **Row R1 over-merged three distinct defects** at `tools/autopilot-prerequisites`
  (lines 125, 22 and 38). R1 keeps Alice's config-validation defect. Blake's
  dependency-table defect was restored as **R31** and his exit-code defect as
  **R32**; without this, two of Blake's findings (one of them 🟠) would have
  vanished into another row's text.
- **Under-merges corrected in the Consensus and Found By cells** where two or
  three reviewers named the same defect at the same file in different words
  (the failure mode PRD 00095 describes): R1+R19, R5+R18, R9+R16,
  R10+R13+R17, R14+R22. Each row below carries the corrected consensus; the
  partner rows are retained as their own rows so every reviewer's wording
  survives, and each partner is dispositioned identically.
- Rows R2 (`workflow_client.py:253` ~ `:275`) and R4 (`config.py:268` ~ `:280`)
  were merged by the script on suffix stripping and the merges are correct: in
  each case both reviewers named the same defect.
- The one `[MECH]` tautological-shape line
  (`tests/workflow_client/test_contract_conformance.py:84`) matched existing row
  R24 by file and test, so `mech-check` was appended to that row's finders
  rather than added as a new row.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/3] | 🟠 | The `tools/autopilot-prerequisites` config contract is not met for PRDs without an artifact gate. A missing explicit `--config` file or unparseable TOML must exit 2. The config is read only inside `check_gate`, which runs for PRDs 61 and 65 only. For `--prd 58 --config /nonexistent`, the tool silently ignores the config and exits 0 or 1. Validate an explicit `--config` for every PRD. | tools/autopilot-prerequisites:125 | 1 | ALICE, BLAKE, BOB |
| R2 | [2/3] | 🟠 | Capability negotiation is incomplete. `ControllerClient.contract()` only checks `protocol_major`, `schema_digest` and `fixture_digest`. It never compares live `operations` or `capabilities` with the pinned bundle, so a controller missing `idempotent-request-id` or `expected-revision` is accepted. `test_transport.py:273` even asserts that an extra live-only capability is fine. The spec says to validate protocol-major and capabilities. | src/ovcaq/workflow_client.py:253 | Phase 1 task 1 | BLAKE, BOB |
| R3 | [2/3] | 🟠 | Actor-secret redaction is not implemented. The client only passes the actor-file path. Controller stderr goes verbatim into `ControllerError` (line 236), so any secret the controller echoes leaks. The canary test (`tests/workflow_client/test_transport.py:716`) uses canned stderr that never contains the canary, so it cannot fail. | src/ovcaq/workflow_client.py:235 | Phase 1 task 1 | BLAKE, BOB |
| R4 | [2/3] | 🟡 | `controller_settings` re-reads and re-merges the user and project TOML that `workflow_settings` just read. `workflow_settings` now calls it eagerly at `config.py:268`. Any workflow command then fails if `controller_argv` is set but `contract_bundle` is missing, even for commands that never use the controller. Pass the merged `workflow` table in, or call the controller reader lazily. | src/ovcaq/config.py:268 | 1 | ALICE, BOB |
| R5 | [2/3] | 🟠 | `ControllerClient._run` does not wrap spawn failures. A missing or non-executable controller argv[0] raises a bare `FileNotFoundError` or `PermissionError` from `Popen`, not a typed `ControllerError`. I reproduced this: a nonexistent argv gives `FileNotFoundError` from `snapshot()`. This is the most likely misconfiguration, and callers that catch `ControllerError` will miss it. Catch `OSError` around `Popen` and raise `ControllerError`. | src/ovcaq/workflow_client.py:218 | 1 | ALICE, BOB |
| R6 | [1/3] | 🟠 | Producer identity is not validated. Only the two digests are compared with the pinned bundle. `package_version` is accepted as any string, and no producer identity field is checked. | src/ovcaq/workflow_client.py:266 | Phase 0 task 1 | BLAKE |
| R7 | [1/3] | 🟠 | `snapshot()` and `apply()` bypass contract negotiation entirely, allowing mutation against an incompatible controller. Require cached negotiation before either operation. | src/ovcaq/workflow_client.py:285 | general | BOB |
| R8 | [1/3] | 🟠 | Bundle-content verification is disconnected: the computed digest is discarded, and negotiation compares only declared digest strings. Implement the specified producer-content digest verification and test tampering through `contract()`. | src/ovcaq/workflow_client.py:258 | general | BOB |
| R9 | [2/3] | 🟡 | `contract()` raises a raw `KeyError` when the pinned bundle and the live controller both omit `schema_digest` or `fixture_digest`. The loop at line 266 compares `None == None` and passes, then `live["schema_digest"]` at line 278 fails. I reproduced it with a bundle holding only `protocol_major`. It should raise `IncompatibleContractError` or `ControllerOutputError`. The digest values are also never checked to be strings. | src/ovcaq/workflow_client.py:266 | 1 | ALICE, BOB |
| R10 | [3/3] | 🟡 | The nonzero-exit path puts the entire decoded stderr into the exception message. The design requires a length-checked stderr tail, and `max_output_bytes` is applied only to stdout. A noisy or hostile controller can produce an unbounded exception message, and the same text may reach logs. Truncate to a bounded tail. | src/ovcaq/workflow_client.py:234 | 1 | ALICE, BLAKE, BOB |
| R11 | [1/3] | 🟡 | `RevisionConflictError` and `RejectedRequestError` are never raised anywhere in `src`. `apply()` always returns an `ApplyResult` for rejections, so both classes are dead and speculative. Either raise them from `apply()` when `ok` is false (`revision_conflict`, `invalid_request`, and so on), or delete them. Tests only exercise their constructors. | src/ovcaq/workflow_client.py:39 | 1 | ALICE |
| R12 | [1/3] | 🟡 | `test_apply_never_returns_result_when_ack_precedes_timeout` uses `pytest.raises((ControllerTimeoutError, ControllerOutputError))`. This is an either-or hedge. Both parametrized cases (a partial line and a complete line, each followed by a sleep) should raise `ControllerTimeoutError` specifically, so the assertion should pin that. | tests/workflow_client/test_transport.py:707 | 2 | ALICE |
| R13 | [3/3] | 🟡 | The output bound is enforced after the fact. `process.communicate()` buffers all stdout and stderr in memory, and the size is checked only afterwards. A hostile controller can exhaust memory before `output_bound` triggers. Stderr has no bound at all and is copied verbatim into the exception message. | src/ovcaq/workflow_client.py:227 | Phase 1 task 1 | BLAKE, ALICE, BOB |
| R14 | [2/3] | 🟡 | Retry and lost-ack handling is only implicit. `apply()` has no retry logic. Request identity survives only because the frozen `MutationEnvelope` is reused by the caller. After a timeout the apply outcome is unknown, and the client does not tell the caller that. A timeout in `apply` raises the generic `ControllerTimeoutError`. | src/ovcaq/workflow_client.py:290 | Phase 1 task 1 | BLAKE, BOB |
| R15 | [1/3] | 🟡 | The `mkstemp` request file is written to the shared system tmp dir. It is removed in `finally`, but a crash before cleanup leaves the envelope on disk. The actor file's permissions are never checked. | src/ovcaq/workflow_client.py:306 | Phase 1 task 1 | BLAKE |
| R16 | [2/3] | 🟡 | Missing digest fields can compare equal through `.get()` and then raise `KeyError`; matching null values produce an invalid typed contract. Validate required digest fields in both documents before comparison. | src/ovcaq/workflow_client.py:266 | general | BOB, ALICE |
| R17 | [3/3] | 🟡 | Stderr never receives a size check, and nonzero exits bypass the stdout check. Enforce the configured bound on both captured streams before processing exit status. | src/ovcaq/workflow_client.py:235 | general | BOB, ALICE, BLAKE |
| R18 | [2/3] | 🟡 | Missing executables, invalid working directories, and execution-permission failures escape as raw `OSError` subclasses. Wrap launch failures in `ControllerError` and cover these cases. | src/ovcaq/workflow_client.py:218 | general | BOB, ALICE |
| R19 | [3/3] | 🟡 | PRDs 58, 59, 60, and 64 ignore configuration entirely, so missing explicit files and malformed TOML can still produce ready=true. Parse configuration for every supported PRD before evaluating gates. | tools/autopilot-prerequisites:125 | 1 | BOB, ALICE, BLAKE |
| R20 | [1/3] | 🟡 | Artifact checking returns only one diagnostic, collapsing independently missing path and digest keys. Return a list containing one entry per unmet condition, preserving dependency-first ordering. | tools/autopilot-prerequisites:57 | 1 | BOB |
| R21 | [1/3] | 🟡 | The five-character limit rejects valid zero-prefixed IDs such as `000058`. Normalize leading zeros before graph lookup while preserving the original argument in JSON. | tools/autopilot-prerequisites:112 | 1 | BOB |
| R22 | [2/3] | 🟡 | `lost_ack_preserved` never retries, so it does not verify the required request-identity guarantee. Retry the same envelope after a lost acknowledgement and compare both recorded requests. | tests/workflow_client/test_transport.py:699 | general | BOB, BLAKE |
| R23 | [1/3] | 🟡 | The runtime import guard misses plugin caches such as `.codex/plugins/cache`. Check plugin-cache path components rather than only the two hardcoded path fragments. | tests/workflow_client/test_contract_conformance.py:102 | 2 | BOB |
| R24 | [1/3] | 🟡 | The supplied MECH gate flags the `or` whitelist assertion. Replace it with membership in one explicit allowed-root set to preserve behavior and satisfy the mandated shape check. | tests/workflow_client/test_contract_conformance.py:84 | 2 | BOB, mech-check |
| R25 | [1/3] | 🟡 | This test file has 818 lines, exceeding the 800-line limit. Move the bundle-digest tests into a separate focused module. | tests/workflow_client/test_contract.py:628 | general | BOB |
| R26 | [1/3] | ⚪ | The `[MECH]` flag at `tests/workflow_client/test_contract_conformance.py:84` looks like a false positive. `top in sys.stdlib_module_names or top == "ovcaq"` is an allow-list guard that fails for any other top-level module. The test is not tautological. | tests/workflow_client/test_contract_conformance.py:84 | 2 | ALICE |
| R27 | [1/3] | ⚪ | `contract()` reads the pinned bundle twice. `controller_bundle_digest` validates it, then `json.loads(read_text())` reads it again. This duplicates work and leaves a small window in which the file can change between the two reads. Have a helper return the parsed data. | src/ovcaq/workflow_client.py:258 | 1 | ALICE |
| R28 | [1/3] | ⚪ | `snapshot(*, workflow_id)` validates `workflow_id` but never sends it to the controller. If the design's signature is intentionally speculative, add a comment saying so. | src/ovcaq/workflow_client.py:285 | 1 | ALICE |
| R29 | [1/3] | ⚪ | The artifact symlink check, `os.path.realpath(artifact) != os.path.abspath(artifact)`, rejects any absolute artifact path under a symlinked ancestor, such as `/var` or `/tmp` on macOS. The spec only requires the file itself to be a non-symlink. This is stricter than the spec, and the docs do say "no symlinked path component". | tools/autopilot-prerequisites:81 | 1 | ALICE |
| R30 | [1/3] | ⚪ | `ControllerConfig` and `config.py` add `timeout_seconds` and `max_output_bytes` fields. They are reasonable, but the PRD does not list them. | src/ovcaq/workflow_client.py:72 | general | BLAKE |
| R31 | [1/3] | 🟠 | The prerequisites table drops a required condition. PRD 58 needs "controller core/jobs/reviews/records", and the code gates 58 on 57 and 62 only. The comment at tools/autopilot-prerequisites:22 admits this. The Phase 0 `[workflow].contract_bundle` precondition is also not probed. | tools/autopilot-prerequisites:22 | Phase 1 task 2 | BLAKE |
| R32 | [1/3] | 🟡 | The exit codes differ from the spec. The spec says exit 0 ready or 1 unavailable. Unknown PRD IDs (argparse) and a missing explicit config both exit 2. This is arguably "fail", but it is outside the 0/1 contract. | tools/autopilot-prerequisites:38 | Phase 1 task 2 | BLAKE |

## Alice

Consensus lens, implementation-aware. Alice ran `tests/workflow_client/test_prerequisites.py`, `test_contract_conformance.py` and `test_config.py` (152 passed) and did not rerun the full suite. She reproduced two of her findings directly (the unwrapped `FileNotFoundError` from `snapshot()` on a nonexistent argv, and the raw `KeyError` from `contract()` on a bundle holding only `protocol_major`).

Findings: R5, R9, R10, R11, R12, R26, R27, R28, R29 (raised), contributing to R1 and R4.

```
R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass
```

## Blake

Blind lens, PRD-only: no diff, no file list, no review history, no design doc. Blake located the implementation himself and ran `uv run pytest tests/workflow_client -q -x` (475 passed), without rerunning the full suite.

What he confirmed the code does right: the controller runs from an explicit argv list with no shell; it runs in a new session and the process group is killed on timeout; the contract bundle is read with duplicate-key and non-finite-number rejection; there is no plugin-cache import; the prerequisites tool is read-only, ignores backlog files, rejects symlinks, caps artifact reads at 16 MiB, and checks sha256 and the evidence tokens; `docs/operations.md` and `CHANGELOG.md` are updated.

Findings: R2, R3, R6, R13, R14, R15, R30, R31, R32 (raised), contributing to R1.

```
B1: fail
B2: pass
B3: fail
B4: pass
B5: fail
B6: pass
B7: pass
B8: pass
B9: fail
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: pass
B17: pass
B18: pass
B19: pass
```

## Bob

Doubt lens (codex, static-only sandbox) plus the de-slop lens. All 15 residual findings landed in FIX; VERIFY and KNOWN were both `- (none)`, so **no verification-check queue was written for this cycle** (nothing to queue).

Findings: R2, R3, R4, R7, R8, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25.

```
R1: fail
R2: fail
R3: pass
R4: pass
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
```

## Carl

Not run. Copilot backend refused with `You have exceeded your monthly quota` (exit 1); the single retry on the native Gemini backend failed with `mise ERROR No version is set for shim: gemini` (exit 1). Carl's one-retry budget is spent and both backends are unusable, so the UI/design lens is absent from this cycle. Graceful degradation: three lenses (consensus, blind, doubt) completed and the cycle is valid without him. The failure class is transient/quota (exit 1), not the permanent exit-4 class, so Carl was **not** latched to the batch and will be attempted again next cycle.

## Mechanical checks

- **Mechanical facts** (computed from `ast`): no finding contradicted the computed block, so nothing was discarded under the "contradicts computed facts" rule. The one countable claim raised independently — Bob's 818-line `tests/workflow_client/test_contract.py` (R25) — was verified against the file and is correct.
- **Tautological test shapes**: 102 test functions checked across 5 test files; one `[MECH]` line, folded into R24.
- **Fail-first replay**: 125 touched tests ran against the pre-change base at `3f6b8b83876f`; **125 failed against base, 0 passed**, and 4 test files could not be collected at base. No test in this change passes against the pre-change code, so nothing is unpinned by the replay check.

## Test gate

The full suite was run once this cycle at HEAD by `review-stage` (`./tools/check`, log at `docs/dev/tmp/gate-00057-c1-20261025.log`). `review-stage`'s parser did not recognize its summary line and reported `counts unavailable`, so the counts below were read back from that same run's log rather than re-running the identical command at the same HEAD.

**The full suite cannot pass in this sandbox.** 657 of the failures and errors are `PermissionError: [Errno 1] Operation not permitted: 'ps'`: the macOS seatbelt profile denies process enumeration, which the supervisor and driver tests require. `ruff` reported `All checks passed!`. The PRD's own modules are green: `tests/workflow_client` is **475 passed** (verified in this session). A clean full-suite verdict needs a host run of `./tools/check` outside the sandbox.

Verdict: 32 findings
Tests: 6935 passed, 561 failed, 198 errors (suite run this cycle; 657 of those are sandbox `ps` denials, see docs/dev/tmp/gate-00057-c1-20261025.log; tests/workflow_client 475 passed)
