---
prd: docs/dev/project-management/prds/wip/00057-autopilot-controller-client-v1.md
review: 3
date: 2026-10-28
head_sha: 0f18ef1b1f77420652ef1ff679d2f7303c72192c
codex_thread_id: 01a17fed-4d65-7b12-b96a-a1f3bf842fd6
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: 377d4c78
  carl: 04307a36
---

# Review: 00057-autopilot-controller-client-v1

Diff range: `5c0bc5ea23de973fe9f984f5c6acade15ecc7073..0f18ef1b1f77420652ef1ff679d2f7303c72192c`

codex_rung_guard: not fired

## Review Summary

Reviewed: 8 completed tasks (5 original, two cycle-1 `[D1]` tasks, one cycle-2 `[D2]` task)
PRDs checked: 00057-autopilot-controller-client-v1.md
Scope: **incremental** — the diff covers only the cycle-2 rework commit since
`5c0bc5e` (0f18ef1, the `protocol_major` bounding fix). Cycles 1 and 2 reviewed
the full work range and the cycle-1 rework respectively.

### Agent Status

- Alice: ✅ Available (consensus lens, legacy engine)
- Blake: ✅ Available (blind lens, PRD-only)
- Bob: ✅ Available (codex; doubt lens, D1-D5 + de-slop; resumed his thread `01a17fed-4d65-7b12-b96a-a1f3bf842fd6`)
- Carl: ⚠️ Unavailable: `gemini-run.sh` exited 1 on the first dispatch (row `04307a36`) and on the retry (row `db7a1576`), both with "You have exceeded your monthly quota" (backend=copilot, model=gemini-3.8-flash). A one-off runtime failure (quota), **not** the permanent exit-4 class, so Carl is NOT latched for the batch. Third consecutive cycle lost to the same monthly quota.
- Eve: ⏸️ Disabled: the codex doubt-roster guard did not fire (no task was implemented by codex), so the optional fifth lens was not activated.

### Degradations this cycle

- **Context pack unavailable.** `engram pack` exited 1 ("not inside a registered repo; run `gita add /Users/bob/git/src/github.com/buvis/ovcaq`"). Every prompt carried the `(no pack available this cycle)` sentinel. Same failure as cycles 1 and 2. Degraded, not invalid.
- **Gate counts parsed by hand, again.** `review-stage` ran `./tools/check` once at this HEAD and reported `Tests: counts unavailable (suite run this cycle, exit 1, no PASS/FAIL/SKIP/EXIT summary line)` — a parser miss, not a missing measurement: the summary line is at `docs/dev/tmp/gate-00057-c3-20261028.log:6112`. The `Tests:` line below was composed from that log rather than by re-running the same red suite; `autopilot verify` refuses to certify a red gate, so no `last-verification.json` record exists for this cycle either. Provenance is named in the line itself.
- **Carl's lens is missing for the third cycle running.** No UI/design voice reviewed this PRD in any cycle. The PRD touches no frontend, so the loss is low-impact here, but the roster was two of three every cycle, never four.

## Alice (consensus lens)

Alice found no issues. She verified the cycle-2 rework against the code: `contract()`
now passes `repr(major)` through `self._bounded(...)` (src/ovcaq/workflow_client.py:560),
so all four negotiation sites that print a live controller value go through redaction
and truncation. R1/R3 she treated as the settled deferral and did not re-raise; R4-R11
were discarded in earlier cycles and she did not re-raise them.

Regression check on the scoped diff: the change is one line plus a test and is
behaviour-preserving for the message shape (the diagnostic still names
`protocol_major`). The new test
`test_contract_drops_controller_text_for_a_mismatched_protocol_major`
(tests/workflow_client/test_actor_secret_redaction.py:425) runs three unmaskable-credential
states (tiny credential, ordinary name, missing actor file) and asserts that neither
the tiny secret, a freshly minted secret, nor the controller prose appears in the
message, that `REDACTED_MARKER` and `protocol_major` do appear, and that only the
`contract` verb was spawned. The replay block reports all 3 parametrized cases
failing against the pre-change code, so the test pins the fix. She ran
`uv run pytest tests/workflow_client/test_actor_secret_redaction.py -q`: 25 passed.

Verdicts: R1 pass, R2 pass, R3 pass, R4 pass, R6 pass, R7 pass, R8 pass, R9 pass,
R10 pass, R11 pass, R12 pass, R13 pass.

## Blake (blind lens, PRD-only)

Blake found the code himself from the PRD alone. He verified as satisfied: `_run`
no longer uses `with process:` (readers close their own streams and are never joined;
`test_run_with_detached_descendant_times_out_within_bound` passes);
`ApplyOutcomeUnknownError` derives from `ControllerError` with every trigger in its
docstring, and `apply` wraps every post-spawn `ControllerError` except
`ControllerLaunchError`; `_redact` never touches the actor file
(`test_redaction_never_reads_actor_file` passes); `_bundle_digest` hashes raw bytes
in both the client and the tool, with strict rejection of `null`, `{}` and bundles
missing `protocol_major`, `operations` or `capabilities`; the docs and
`CONTROLLER_CLIENT_NOTES` document the key and the raw-bytes digest. He ran
`uv run pytest tests/workflow_client`: 930 passed.

He raised nine findings. Five were auto-dismissed against the settled ledger
(reproduced below), including his independent re-discovery of the short-credential
residual. Four survive in the table, all single-voice Medium/Low.

Verdicts: B1 fail, B15 fail, all other B2-B19 pass.

## Bob (codex; doubt lens + de-slop)

Bob resumed his cycle-1/2 codex thread and judged the rework against his own earlier
critique. He reports no issues.

FIX: (none)
VERIFY: (none)
KNOWN: (none)

He dropped his cycle-2 KNOWN row (the R3 residual) on this pass, having already
recorded it as settled. The de-slop pass found nothing.

Consensus verdicts: R1 pass, R2 pass, R3 pass, R4 pass, R6 pass, R7 pass, R8 pass,
R9 pass, R10 pass, R11 pass, R12 pass, R13 pass.

Doubt rubric: D1 pass, D2 pass, D3 pass, D4 pass, D5 pass.

## Carl (UI / frontend & design)

Not run. `gemini-run.sh` exited 1 on both the first dispatch and the retry with
"You have exceeded your monthly quota" (backend=copilot, model=gemini-3.8-flash).
Recorded as a one-off runtime failure, not latched for the batch.

## Mechanical checks (computed)

- **Tautological test shapes:** none. 19 test functions in 1 test file checked, block empty.
- **Fail-first replay** (`uv run python -m pytest`, per changed test file): 3 touched
  tests ran, **3 failed against base**, 0 passed. The cycle-2 fix is fully pinned;
  there is no replay row to absorb this cycle.
- **Mechanical facts** (`ast`): computed and supplied to the reviewers; no finding
  contradicted it.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [1/3] | 🟡 Medium | Config source split. `controller_settings` merges the user and project `[workflow]` tables. `tools/autopilot-prerequisites` reads only the project `ovcaq.toml`, or the `--config` path. A bundle or digest set only in the user config makes the tool report unavailable while the client accepts it. The two readers therefore do not share one definition of the pin. | tools/autopilot-prerequisites:200 | R3 | BLAKE |
| R2 | [1/3] | ⚪ Low | Evidence tokens. The spec says "AP17 evidence" and "Lantern03 evidence". The tool requires the literal tokens `AP00017` and `Lantern00003`. This is probably a shorthand reading, but a producer that writes `AP17` is rejected. The docs state the long forms. | tools/autopilot-prerequisites:32 | Phase 1 task 2 | BLAKE |
| R3 | [1/3] | ⚪ Low | Unused argument. `snapshot(workflow_id=...)` validates `workflow_id` and then never passes it to the controller. I could not check this against Contract A, because the design document is not in the tree I inspected. | src/ovcaq/workflow_client.py:583 | general | BLAKE |
| R4 | [1/3] | ⚪ Low | Zombie risk. If `_kill_group` times out reaping after SIGKILL, the child may stay a zombie. The code comments this as an accepted bound. Daemon reader threads are abandoned by design. This is acceptable and noted only. | src/ovcaq/workflow_client.py:348 | R2 | BLAKE |

### Consolidation note

No CRITICAL and no HIGH survived this cycle. The cycle-2 🟠 R2 (`protocol_major`
unbounded) is fixed and confirmed by two lenses. The cycle-1/2 short-credential
residual (R1/R3 of cycle 2) was re-raised independently by Blake and was
auto-dismissed by the ledger as the settled deferral it is. Every surviving row
is single-voice from Blake.

No prior-cycle verification-check queue existed (cycle 2 queued no checks), so
nothing was carried forward. The mechanical blocks produced no findings.

### Auto-dismissed (ledger)

- [BLAKE] 🟠 Short-credential redaction miss. The client never reads the actor file, so `_can_mask_credential` judges it from file size alone (`actor_file.stat().st_size >= MIN_SECRET_CHARS`). A secret under 8 characters inside a larger file, such as the JSON `secrets/actor.json` that the shipped docs example uses, is not masked. A controller stderr or contract diagnostic that echoes it passes through `_redact` untouched, which breaks the R5 acceptance line that a secret shorter than `MIN_SECRET_CHARS` yields a redacted diagnostic. The docstring admits this as a known residual deferred since cycle 1. No test covers it, and the existing tests use only a tiny file or an unstatable one. | File: src/ovcaq/workflow_client.py:407 — settled deferral: the cycle-1 decision gate deferred this exact residual to batch end (batch 202610272211 deferred JSON, type residual-finding, owner "review gate"). Closing it needs the credential length or a redaction token declared in configuration; reading the actor file is forbidden by R5. Recorded in the _can_mask_credential docstring and the CHANGELOG.
- [BLAKE] 🟡 Fail-open bundle pin. `contract_bundle_sha256` is optional in `controller_settings`, so `bundle_digest=None` is accepted. `_validated_bundle` then skips the digest check, and the controller is negotiated against an unpinned bundle. The spec says to validate producer identity and digests. Only `tools/autopilot-prerequisites --prd 58` requires the digest, and a consumer can build a client without ever running that tool. | File: src/ovcaq/config.py:326 — single-voice
- [BLAKE] 🟡 Exit-code contract. The spec says "Exit 0 ready or 1 unavailable with JSON diagnostics". The tool exits 2 with stderr text and no JSON for an unknown PRD (`parser.error`) and for config errors (`refuse`). The doc generator documents exit 2. The behaviour is reasonable for "fail", but it goes beyond the 0/1 contract, and a consumer that gates on exit 1 only would read a config error as something else. | File: tools/autopilot-prerequisites:42 — single-voice; exit 2 for a usage error is the argparse convention and the PRD's own Behavior text says unknown IDs and missing config must "fail", which exit 2 satisfies. The R1/R19 fix keeps exit 2 for usage errors deliberately.
- [BLAKE] ⚪ Launch-failure class. The spec says a launch failure "stays a plain `ControllerError`". The code raises the new `ControllerLaunchError` subclass and re-raises it in `apply`. Behaviour is correct (it is not classed as unknown outcome). `ControllerLaunchError` is an unspecified extra public type, and `RevisionConflictError` and `RejectedRequestError` are also unspecified types. | File: src/ovcaq/workflow_client.py:55 — single-voice; and the reporter concedes the intent holds. The PRD asks that a launch failure stay catchable as a plain ControllerError, which a ControllerError subclass satisfies, and catching every OSError from Popen is the safer direction for a pre-spawn failure.
- [BLAKE] ⚪ Unguarded temp-file cleanup. `os.unlink(name)` in the `finally` of `apply` can raise `OSError`. That would replace an `ApplyOutcomeUnknownError` or a successful result and drop the request identity the caller needs for the retry. | File: src/ovcaq/workflow_client.py:614 — single-voice

Verdict: 4 findings
Tests: 8215 passed, 61 failed, 14 errors (suite run this cycle; counts read from this cycle's own gate log docs/dev/tmp/gate-00057-c3-20261028.log:6112 after review-stage failed to parse the padded summary line. All 61 failures and all 14 errors are in tests/integration/ (57 failed, 14 errors) or tests/tui/ (4 failed); the sandbox denies /bin/ps and the log carries 17 `PermissionError: [Errno 1] Operation not permitted: 'ps'`. This cycle's diff touches no file under either tree; tests/workflow_client is fully green)
