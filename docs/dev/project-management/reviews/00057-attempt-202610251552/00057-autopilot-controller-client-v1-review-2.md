---
prd: docs/dev/project-management/prds/wip/00057-autopilot-controller-client-v1.md
review: 2
date: 2026-10-25
head_sha: b53efd3195d31987456bd071d830cb599a335d56
codex_thread_id: 01a17481-0b54-7c21-9c66-fdab3c6ab821
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: 2dcfa149
  carl: 7aa9e97e
---

# Review: 00057-autopilot-controller-client-v1

Diff range: `e78015922abafe754b2118c9974f2339a325e620..b53efd3195d31987456bd071d830cb599a335d56`

codex_rung_guard: not fired

## Review Summary

Reviewed: 6 completed tasks (2 original-plan, 4 `[D1]` rework)
PRDs checked: 00057-autopilot-controller-client-v1.md
Scope: incremental — the cycle-1 rework commits only. Cycle 1 reviewed the full work range.

### Agent Status

- Alice: ✅ Available (consensus lens, legacy engine)
- Blake: ✅ Available (blind lens, PRD-only)
- Bob: ✅ Available (codex, doubt lens D1-D5 + de-slop; codex thread `01a17481` resumed from cycle 1)
- Carl: ❌ **Permanently unavailable.** First dispatch: `copilot` backend, model `gemini-3.8-flash`, exit 1 — "You have exceeded your monthly quota". The one retry forced the native `gemini` backend (CLI-default model) and exited **4**: `IneligibleTierError: This client is no longer supported for Gemini Code Assist for individuals` (`reasonCode: UNSUPPORTED_CLIENT`, `tierId: free-tier`). Exit 4 is the permanent-unavailability class, so Carl is now **latched for batch 202610251552** (`state.batch.unavailable_reviewers = ["carl"]`, origin cycle 2 of this PRD). He publishes no output file; the empty `carl-output-00057-c2-20261025.txt` left by the quota run was NOT consolidated. No `ui` lens key this cycle.

### Cycle notes

- `consensus_engine: legacy`, `doubt_reviewer: codex`. The codex doubt-roster guard did not fire: no task has a `codex` implementor (all six ran `claude`/opus or the orchestrator), so Eve was not activated.
- Context pack unavailable this cycle: `engram pack` exited 1 (`not inside a registered repo; run gita add /Users/bob/git/src/github.com/buvis/ovcaq`). Prompts carried the `(no pack available this cycle)` sentinel. A review without the pack is degraded, not invalid.
- Bob's dispatch row `2dcfa149` reports the *staged* prompt size, not the inlined prompt actually sent to codex (26847 bytes recorded against 250093 bytes sent). The row was not re-opened; the understatement is recorded here instead, as in cycle 1.
- The settled-decisions ledger (15 cycle-1 entries) was passed to Alice's and Bob's prompts and to `consolidate_findings.py` as `--ledger` with `--ledger-dismiss BLAKE`. One Blake re-raise was auto-dismissed — see below.
- No cycle-1 verification-check queue file exists (`00057-...-checks-1.json` absent), so no failed checks were carried forward.
- **`autopilot verify` cannot write a record for this project.** `verification.SUMMARY_RE` requires a `PASS n FAIL n SKIP n EXIT n` line; `mise run check` (ruff, ruff format, mypy, pytest, uv build) emits none, which is why `review-stage`'s gate line reads `counts unavailable`. The `Tests:` line below is therefore composed model-side from this cycle's own gate run, whose combined log is `docs/dev/tmp/gate-00057-c2-20261025.log` (pytest summary at line 143657). Provenance is stated rather than hidden; the suite was genuinely run this cycle at this HEAD.

### Auto-dismissed (ledger)

- [BLAKE] 🟡 RevisionConflictError and RejectedRequestError are defined and exported but never raised by the client. A rejected or conflicting apply comes back as ApplyResult(ok=False, error_code=...). The "typed errors" are dead types, and the client never maps error_code to them. | File: src/ovcaq/workflow_client.py:61 — single-voice

(The match is correct: the cycle-1 ledger entry cites the same defect at `src/ovcaq/workflow_client.py:39`; only the line moved.)

### Consolidation corrections (model-side, applied on top of the script output)

`consolidate_findings.py` produced 18 rows and warned that two rows merged only
after citation-suffix stripping. Both merges are correct; two under-merges were
corrected. Both directions are recorded so the table is not silently wrong:

- **Correct merges.** R1 (`workflow_client.py:549` ~ `:546`) — Alice, Blake and
  Bob each name the same defect: only a timeout marks the apply outcome
  unknown. R3 (`docs/operations.md:121` ~ `:114`) — Alice and Blake each name
  the undocumented PRD 58 gate.
- **Under-merge corrected: R4 + R13.** Bob's 🟠 redaction row and Alice's ⚪
  redaction row share the short-secret gap (`MIN_SECRET_CHARS`). Both now carry
  two-of-three consensus and are dispositioned identically; each keeps its own
  wording and severity so neither voice is lost.
- **Under-merge corrected: R6 + R11.** Bob and Blake both say the new PRD 58
  `contract_bundle` prerequisite checks existence only and validates no
  content or provenance, at the same file and line. Both now carry two-of-three
  consensus and 🟠, dispositioned identically.
- **Mechanical rows absorbed as R19, R20 and R21** (below): one tautological
  shape and two fail-first replay rows. None matched an existing row's file and
  test, so each is its own row with `Found by: mech-check`.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/3] | 🟠 | `apply()` marks only a timeout as an unknown outcome. The design's Risks section says a timeout or truncated-output error on `apply` is not proof of non-commitment. Output-bound overruns (the group is SIGKILLed after a possible commit), exit 0 with non-JSON stdout, and a malformed response at line 565 all raise plain `ControllerOutputError`. A caller may treat these as "not applied" and mint a new `request_id`, which breaks idempotency. Raise `ApplyOutcomeUnknownError` (or a shared base class) for every post-spawn failure that leaves the commit state ambiguous, and add tests. | src/ovcaq/workflow_client.py:549 | 3 | ALICE, BLAKE, BOB |
| R2 | [2/3] | 🟠 | The producer-content digest check cannot be reached through configuration. `ControllerConfig.bundle_digest` is checked in `_pinned_contract`, but `controller_settings` never reads or passes it. There is no `[workflow]` key for it, and `test_config_leaves_bundle_digest_unpinned_by_default` pins that. So a client built through the config path never verifies the bundle content, and the prior R8 tamper defence is only reachable when a caller sets the field by hand. Add a `[workflow].contract_bundle_sha256` key, or record that wiring as deferred to PRD 00058. | src/ovcaq/config.py:317 | 5 | ALICE, BOB |
| R3 | [2/3] | 🟡 | `docs/operations.md` was not updated with the rework, although the tool's contract changed. The docs still say only PRDs 61 and 65 carry artifact gates. They omit the new PRD 58 gate: `[workflow] controller_artifact` and `controller_artifact_sha256`, an `evidence` list holding `core`, `jobs`, `reviews` and `records`, and a `contract_bundle` regular-file precondition. The paragraph at line 111 also lists only "protocol major and bundle digests", but the client now also checks capabilities, operations and package version. | docs/operations.md:121 | 4 | ALICE, BLAKE |
| R4 | [2/3] | 🟠 | Redaction now reads and caches credentials, violating the opaque actor-file contract, yet still exposes secrets shorter than eight characters or changed after caching. Keep credentials opaque and omit unsafe controller diagnostics; add no-read, short-secret, and rotation tests. | src/ovcaq/workflow_client.py:345 | 3 | BOB, ALICE |
| R5 | [1/3] | 🟠 | Cleanup can exceed the timeout indefinitely: denied signals are swallowed before unbounded `wait()`, while detached descendants retaining pipes can leave reader threads blocking pipe closure. Use deadline-bounded process and pipe cleanup; cover both cases. | src/ovcaq/workflow_client.py:298 | 3 | BOB |
| R6 | [2/3] | 🟠 | The new contract-bundle prerequisite checks only file existence. Empty or malformed files satisfy it, and tests explicitly require that acceptance. Validate bounded bundle contents and provenance before reporting readiness. | tools/autopilot-prerequisites:135 | 4 | BOB, BLAKE |
| R7 | [1/3] | 🟡 | The test hedges between two outcomes with `try/except ControllerError: pass`, and its comment calls the outcome a race. It is not one. The grandchild holds both pipes for `SLOW_SECONDS*3`, which is longer than the 1 s timeout, so neither reader reaches EOF and `contract()` deterministically raises `ControllerTimeoutError`. A successful parse or any other `ControllerError` would pass unnoticed. Pin it with `pytest.raises(ControllerTimeoutError)`. | tests/workflow_client/test_controller_boundary.py:335 | 3 | ALICE |
| R8 | [1/3] | 🟡 | `snapshot(*, workflow_id)` validates workflow_id and then ignores it. The controller call is "snapshot --project-root <root>" only, and test_negotiation.py:511-512 shows two different workflow_ids returning the same payload. A caller cannot select a workflow, and the parameter is misleading. | src/ovcaq/workflow_client.py:513 | 1.1 | BLAKE |
| R9 | [1/3] | 🟡 | The spec asks for "typed" snapshots, but snapshot() returns the raw dict[str, Any] unmodified. Only ApplyResult and ControllerContract are typed. | src/ovcaq/workflow_client.py:513 | 1.1 | BLAKE |
| R10 | [1/3] | 🟡 | The spec requires validating "producer identity/digests". The client checks protocol_major, package_version (the pinned version, or the pinned version plus a "+build" tag), schema_digest and fixture_digest, plus the advertised operations and capabilities. There is no producer or name field in the bundle or in the check. I could not find the canonical design doc in the repo (docs/dev/designs/autopilot-optional-supervision.md is absent), so I could not confirm that nothing else is required. | src/ovcaq/workflow_client.py:477 | 1.1 | BLAKE |
| R11 | [2/3] | 🟠 | For PRD 58, the prerequisites tool only checks that contract_bundle is a regular file. It does not read, parse or digest-check it, although the spec says "validate provenance". | tools/autopilot-prerequisites:135 | 1.2 | BLAKE, BOB |
| R12 | [1/3] | 🟡 | Overflow tests use finite responses and do not establish enforcement before process completion. Add oversized stdout/stderr followed by a long sleep; require prompt `ControllerOutputError` and process termination before the timeout. | tests/workflow_client/test_controller_boundary.py:95 | 3 | BOB |
| R13 | [2/3] | ⚪ | Redaction has two silent gaps. Secrets shorter than 8 characters (`MIN_SECRET_CHARS`) are never redacted. An `OSError` while reading the actor file at line 355 silently makes redaction a no-op, although the controller, which may have read access, can still echo the secret. Document the minimum length and the unreadable-file behaviour, or fail loudly. | src/ovcaq/workflow_client.py:355 | 3 | ALICE, BOB |
| R14 | [1/3] | ⚪ | The pinned bundle's `protocol_major` is never compared with the live value. Only the `PROTOCOL_MAJOR` constant is checked at line 489, so a bundle pinned at another major is accepted silently. This is harmless today but weakens "validate protocol-major". | src/ovcaq/workflow_client.py:488 | 3 | ALICE |
| R15 | [1/3] | ⚪ | The controller_contract_fixtures test serves the pinned bundle file back as the fake controller's contract response. It is a self-echo, not an independent producer fixture. The scenario is satisfied only formally, which the spec's "real-host support requires separate probe evidence" note acknowledges. | tests/workflow_client/test_contract_conformance.py:41 | 3.1 | BLAKE |
| R16 | [1/3] | ⚪ | The prerequisites tool checks for a symlink with realpath and then opens the path in a separate step, so there is a small check-then-act window. A path that changes in between could pass. | tools/autopilot-prerequisites:90 | 1.2 | BLAKE |
| R17 | [1/3] | ⚪ | The docs example uses a bare name, controller_argv = ["autopilot-controller"]. config.py:232-242 accepts any nonempty string array, and Popen resolves a bare name through PATH. This is arguably "explicit argv", but the "no executable auto-discovery" requirement is not enforced, for example by requiring an absolute path. | src/ovcaq/config.py:232 | 1.1 | BLAKE |
| R18 | [1/3] | ⚪ | Gate state is unverified. The supplied test gate shows the full suite exiting 1 with no summary line. I ran `uv run pytest tests/workflow_client` narrowly and got 757 passed. I did not run ./tools/check, and I cannot confirm the Phase 2 exit criterion that it passes. | N/A | 3.1 | BLAKE |
| R19 | [1/3] | 🟡 | test_no_plugin_import hedges with `or`: either outcome satisfies it | tests/workflow_client/test_contract_conformance.py:84 | general | mech-check |
| R20 | [1/3] | 🟡 | 40 touched test(s) pass against the pre-change code: test_contract_accepts_live_controller_advertising_more_than_pinned, test_contract_accepts_live_package_version_equal_or_build_tagged +34 more | tests/workflow_client/test_negotiation.py | general | mech-check |
| R21 | [1/3] | 🟡 | 38 touched test(s) pass against the pre-change code: test_contract_runs_contract_verb_in_project_root_and_maps_bundle, test_contract_rejects_digest_not_pinned_by_bundle +32 more | tests/workflow_client/test_transport.py | general | mech-check |

## Alice

Alice verified every one of the 32 cycle-1 findings as resolved or still
settled, and did not re-raise any ledger entry. Her resolution evidence:

- R1/R19/R31 — `tools/autopilot-prerequisites:157` loads the config before any
  PRD check; a missing explicit config, bad TOML or a wrong-typed key exits 2
  for every PRD. PRD 58 is gated on `[workflow].controller_artifact` (plus
  `_sha256` and the four evidence tokens) and a `contract_bundle` probe.
- R2/R6/R7/R8/R9/R16 — `contract()` compares pinned operations and capabilities
  with the live set, checks the package version, validates required strings in
  both documents before comparing, negotiates on the first `snapshot()`/`apply()`
  and caches, and checks an optional `bundle_digest` pin before any spawn.
- R3/R5/R10/R13/R17/R18 — both streams are read incrementally and capped at the
  bound plus one byte; the whole process group is killed on timeout or overrun;
  spawn `OSError` is wrapped as `ControllerError`; stderr is redacted then cut
  to a 512-character tail; the bound is applied before the exit status is read.
- R4 — `workflow_settings` validates only the shape of the controller keys via
  `_controller_inputs` (`config.py:245`) and no longer builds a
  `ControllerConfig`, so a missing `contract_bundle` no longer breaks unrelated
  commands. The config files are read once.
- R14 — a timed-out `apply` raises `ApplyOutcomeUnknownError` carrying the
  `request_id`, and a test retries the same envelope.
- R22 — the lost-ack test now retries and compares both recorded requests.

New findings: R1, R2, R3, R7, R13, R14 (see the table).

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

## Blake

Covered and OK:

- Transport uses an explicit argv array with no shell, a new session, and a process-group kill.
- Output is bounded per stream and a timeout is enforced.
- Actor secrets are redacted from stderr and error text.
- The apply request file is created by mkstemp (0600) and unlinked in a finally block, so the same envelope and request_id are preserved on retry.
- There are no plugin imports, and the AST and runtime tests prove it.
- The prerequisites dependency table matches the spec.
- Predecessors count only as regular files in the done bucket; backlog files are never accepted.
- Unknown IDs and bad config exit 2, and probes are read-only and capped at 16 MiB.

New findings: R1, R3, R6, R8, R9, R10, R11, R15, R16, R17, R18 (see the table).
One re-raise was auto-dismissed against the ledger (above).

B1: fail
B2: pass
B3: fail
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
B15: pass
B16: fail
B17: pass
B18: pass
B19: pass

## Bob

FIX:
- [BOB] 🟠 Redaction now reads and caches credentials, violating the opaque actor-file contract, yet still exposes secrets shorter than eight characters or changed after caching. Keep credentials opaque and omit unsafe controller diagnostics; add no-read, short-secret, and rotation tests. | File: src/ovcaq/workflow_client.py:345 | Task: 3
- [BOB] 🟠 Bundle verification remains disabled through the configuration entry point: `controller_settings()` never supplies `bundle_digest`, whose default is None. Wire a trusted pin through configuration and test that a config-created client rejects tampered content before spawning. | File: src/ovcaq/config.py:317 | Task: general
- [BOB] 🟠 Cleanup can exceed the timeout indefinitely: denied signals are swallowed before unbounded `wait()`, while detached descendants retaining pipes can leave reader threads blocking pipe closure. Use deadline-bounded process and pipe cleanup; cover both cases. | File: src/ovcaq/workflow_client.py:298 | Task: 3
- [BOB] 🟠 The new contract-bundle prerequisite checks only file existence. Empty or malformed files satisfy it, and tests explicitly require that acceptance. Validate bounded bundle contents and provenance before reporting readiness. | File: tools/autopilot-prerequisites:135 | Task: 4
- [BOB] 🟡 Unknown apply outcomes are identified only for timeouts. Truncated or oversized acknowledgements can also follow a committed mutation, but receive ordinary output errors without request identity or retry guidance. Expose that ambiguity consistently and test commit-then-truncate replay. | File: src/ovcaq/workflow_client.py:546 | Task: 3
- [BOB] 🟡 Overflow tests use finite responses and do not establish enforcement before process completion. Add oversized stdout/stderr followed by a long sleep; require prompt `ControllerOutputError` and process termination before the timeout. | File: tests/workflow_client/test_controller_boundary.py:95 | Task: 3

VERIFY:
- (none)

KNOWN:
- (none)

R1: fail
R2: pass
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

Carl: permanently unavailable. Backend `copilot` / model `gemini-3.8-flash` exited 1 on the monthly quota; the one retry on the native `gemini` backend exited 4 with `IneligibleTierError` (`UNSUPPORTED_CLIENT`, free tier). Latched for batch 202610251552. No output consolidated.

## Mechanical checks

- Tautological test shapes: 110 test functions checked in 8 test files; 1 `[MECH]` line, absorbed as R19.
- Fail-first replay (`uv run python -m pytest`, base `e78015922aba`): 154 touched tests ran, **76 failed against base**, 78 passed; 4 test files could not be collected at base. The two `[MECH]` lines naming the 78 passers are absorbed as R20 and R21. The rework's own new tests do pin the change (76 base failures); the passers are the pre-existing tests inside the same touched files.
- Mechanical facts block: computed per-function line counts were available to every implementation-aware lens; no finding contradicts it.

## Test gate

Full suite at `b53efd3` via `./tools/check` (`mise run check`: ruff, ruff format, mypy, pytest, uv build): **561 failed, 7217 passed, 198 errors in 569.35s**. Log: `docs/dev/tmp/gate-00057-c2-20261025.log` (summary at line 143657).

All 759 failures and errors are outside this PRD's scope — tests/runtime (440), tests/tui (144), tests/integration (139), tests/packaging (28), tests/drivers (8) — and are macOS-seatbelt `PermissionError` denials of `ps`, a sandbox limitation rather than a defect of this diff. **Zero failures or errors in `tests/workflow_client`**, this PRD's own scope (Blake's narrow run: 757 passed).

Verdict: 21 findings
Tests: 7217 passed, 561 failed, 198 errors (suite run this cycle; all 759 are sandbox `ps` denials outside tests/workflow_client, see docs/dev/tmp/gate-00057-c2-20261025.log)
