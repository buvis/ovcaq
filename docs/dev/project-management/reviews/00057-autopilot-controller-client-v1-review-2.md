---
prd: docs/dev/project-management/prds/wip/00057-autopilot-controller-client-v1.md
review: 2
date: 2026-10-28
head_sha: 5c0bc5ea23de973fe9f984f5c6acade15ecc7073
codex_thread_id: 01a17fed-4d65-7b12-b96a-a1f3bf842fd6
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: ec9fecf0
  carl: ec76a308
---

# Review: 00057-autopilot-controller-client-v1

Diff range: `fee44aeeab54517e5609085c81c2bb5ccc60d248..5c0bc5ea23de973fe9f984f5c6acade15ecc7073`

codex_rung_guard: not fired

## Review Summary

Reviewed: 7 completed tasks (5 original + the two cycle-1 `[D1]` rework tasks)
PRDs checked: 00057-autopilot-controller-client-v1.md
Scope: **incremental** — the diff covers only the cycle-1 rework commits since
`fee44ae`; cycle 1 reviewed the full `d440d98..fee44ae` work range.

### Agent Status

- Alice: ✅ Available (consensus lens, legacy engine)
- Blake: ✅ Available (blind lens, PRD-only)
- Bob: ✅ Available (codex; doubt lens, D1-D5 + de-slop; resumed his cycle-1 thread `01a17fed-4d65-7b12-b96a-a1f3bf842fd6`)
- Carl: ⚠️ Unavailable: gemini-run backend=copilot model=gemini-3.8-flash exited 1 — "You have exceeded your monthly quota". Retried once per retry policy (dispatch row `b882be0f`), same result. A one-off runtime failure (quota), **not** the permanent exit-4 class, so Carl is NOT latched for the batch. This is the second consecutive cycle he has been lost to the same monthly quota.
- Eve: ⏸️ Disabled: the codex doubt-roster guard did not fire (no task was implemented by codex), so the optional fifth lens was not activated.

### Degradations this cycle

- **Context pack unavailable.** `engram pack` exited 1 ("not inside a registered repo; run `gita add /Users/bob/git/src/github.com/buvis/ovcaq`"). Every prompt carried the `(no pack available this cycle)` sentinel, so no findings-precedent section reached the reviewers. Degraded, not invalid. Same failure as cycle 1.
- **Gate counts parsed by hand, again.** `review-stage` ran `./tools/check` once at this HEAD and reported `Tests: counts unavailable (suite run this cycle, exit 1, no PASS/FAIL/SKIP/EXIT summary line)` — a parser miss, not a missing measurement: the padded summary line is at `docs/dev/tmp/gate-00057-c2-20261028.log:61`. The `Tests:` line below was composed from that log rather than by re-running the same red suite; `autopilot verify` refuses to certify a red gate, so no `last-verification.json` record exists for this cycle either. Provenance is named in the line itself.
- **Carl's lens is missing for the second cycle running.** No UI/design voice reviewed this PRD in either cycle. The PRD touches no frontend, so the loss is low-impact here, but it is a real two-of-three roster, not a full four.

## Alice (consensus lens)

Alice verified the cycle-1 rework against the code. She confirms R1 (the bundle
pin) fixed for the pin case, duplicate keys and NaN/Infinity: client and tool
both lowercase the pin, the tool parses with copies of the strict hooks and
imports nothing from ovcaq (pinned by `test_the_tool_imports_nothing_from_ovcaq`),
and new tests send one configured value through both consumers across five hex
spellings, near-miss pins, duplicate and nested-duplicate bundles, NaN and
Infinity, and a string containing "NaN" that must be accepted. She confirms R2
fixed at the three sites the rework touched, with secret, whitespace-free-secret
and bounding tests. She confirms R3's size-and-stat gate behaves as documented
and treats the residual as deferred.

She raises one 🟠: the rework missed a fourth negotiation site. She also raises
one 🟡 about a remaining client/tool divergence in parse-failure exception type,
and one ⚪ documentation gap.

Checks she ran: the MECH tautology block is empty this cycle and she found no
constant, self-comparing or either-or assertion in the added tests (R2); every
touched file is under 800 lines — 751, 709, 629, 520, 469, 221 — and the
pre-existing 818-line `test_contract.py` is untouched by this diff and already
settled (R13); the largest function is `apply` at 42 lines per the mechanical
facts (R12). She ran no tests, reading the supplied gate instead.

Verdicts: R1 pass, R2 pass, R3 pass, R4 pass, R6 pass, R7 pass, R8 pass,
R9 fail, R10 fail, R11 pass, R12 pass, R13 pass. (The consensus rubric has no
R5; R1-R4 and R6-R13 is the complete set.)

## Blake (blind lens, PRD-only)

Blake found the code himself from the PRD alone. He verified as satisfied: the
`_run` cleanup bound (no `with process:`, readers close their own streams and
are never joined, the detached-descendant test asserts a timeout under 3 s); the
unknown-outcome classification (`ApplyOutcomeUnknownError` derives from
`ControllerError`, its docstring names every trigger, and the post-spawn
non-zero-exit, launch-failure and timeout-base tests exist and pass); the
redaction path never reading the actor file; `_bundle_digest` hashing raw bytes
in both the client and the tool with the strict `null`/`{}`/missing-field checks
and matching docs and `CONTROLLER_CLIENT_NOTES`; and the dependency graph, the
done-bucket regular-file check, the 16 MiB bound, the symlink refusal and the
no-fetch/no-write behavior.

He raises one 🟠 on the short-secret criterion (the same residual the cycle-1
gate deferred, reached independently and from the spec rather than from the
review history), two ⚪ items, and one 🟡 about the unverified full-suite gate.
Five of his findings were auto-dismissed against the settled ledger; that
section is reproduced below.

Verdicts: B1 fail, B5 fail, B15 fail, all other B2-B19 pass.

## Bob (codex; doubt lens + de-slop)

Bob resumed his cycle-1 codex thread, so he judged the rework against his own
earlier critique rather than re-reviewing from zero.

FIX: (none)
VERIFY: (none)
KNOWN: one 🟠 — the R3 residual. Actor-file size cannot establish credential
length; a file containing `abc` plus padding passes `_can_mask_credential`, so
an echoed `abc` still reaches a diagnostic. He notes negotiation now uses the
redaction pipeline but inherits the limitation, and that the cycle-1 decision
gate explicitly deferred this residual, placing it outside the current rework
scope.

He raised nothing in FIX and nothing new that needs verification: the de-slop
pass found nothing.

Consensus verdicts: R1 pass, R2 pass, R3 pass, R4 pass, R6 pass, R7 fail,
R8 pass, R9 fail, R10 pass, R11 pass, R12 pass, R13 pass.

Doubt rubric: D1 pass, D2 pass, D3 pass, D4 pass, D5 pass.

## Carl (UI / frontend & design)

Not run. `gemini-run.sh` exited 1 on both the first dispatch and the retry with
"You have exceeded your monthly quota" (backend=copilot, model=gemini-3.8-flash).
Recorded as a one-off runtime failure, not latched for the batch.

## Mechanical checks (computed)

- **Tautological test shapes:** none. The block is empty this cycle.
- **Fail-first replay** (`uv run python -m pytest`, per changed test file): 38 of
  118 touched tests fail against the pre-change code, so most of the rework's
  tests do pin new behavior. The four rows below name the touched tests that
  pass against base; they are absorbed as findings R8-R11.
- **Mechanical facts** (`ast`): largest function `apply`, 42 lines. Touched file
  lengths 751, 709, 629, 520, 469, 221 — all under 800.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | 🟠 High | Short-secret redaction does not meet the task-3 criterion. `_can_mask_credential` judges safety from the actor file's stat size alone (size >= 8 means "safe"), so a short credential inside a larger file — a JSON `actor.json`, the PRD's own example name — is reported as maskable and then passes `_redact` unmasked, because only tokens of 8 or more characters are masked. The PRD requires that a secret shorter than `MIN_SECRET_CHARS` yield a redacted diagnostic, never raw controller output. The code, the CHANGELOG and the `_can_mask_credential` docstring all record this as a known residual, deferred at the cycle-1 decision gate. | src/ovcaq/workflow_client.py:407 | 6 | ALICE, BLAKE |
| R2 | [1/3] | 🟠 High | R2 was resolved at only three of the four negotiation sites that print a live controller value. `contract()` still formats the live `protocol_major` raw with `{major!r}` and never passes it through `_bounded`. A controller that answers `protocol_major: "<credential bytes>"` (any non-int JSON value, up to the 1 MiB output bound) puts those bytes verbatim into the `IncompatibleContractError` text. Same defect class as cycle-1's R2, on a site the rework missed. Fix with `self._bounded(repr(major))`, or report only the type for a non-int, and pin it with a mismatch test carrying a synthetic secret, as the three new tests do for package_version, schema_digest and fixture_digest. | src/ovcaq/workflow_client.py:560 | 6 | ALICE |
| R3 | [1/3] | 🟠 High | Prior R3 remains partially unresolved: actor-file size cannot establish credential length. A file containing `abc` plus padding passes `_can_mask_credential`, allowing an echoed `abc` into diagnostics. Negotiation now uses the redaction pipeline but inherits this limitation. The cycle-1 decision gate explicitly deferred this residual. | src/ovcaq/workflow_client.py:407 | 6 | BOB |
| R4 | [1/3] | 🟡 Medium | R1 is fixed for the pin case and for duplicate keys and NaN/Infinity, but the client and the tool still differ on other parse failures. `_parse_bundle` catches only `JSONDecodeError` and `UnicodeDecodeError`. A bundle nested deeply enough to raise `RecursionError`, or holding an integer past the int-digit limit (a plain `ValueError`), escapes `contract()` as a raw non-`ControllerError` exception. The tool catches `(ValueError, RecursionError)` and reports "not valid JSON". Both refuse, so this is not a gate bypass, but the "one definition of a valid bundle" claim does not hold for the exception type. Catch `ValueError` and `RecursionError` in `_parse_bundle` and wrap them in `IncompatibleContractError`. | src/ovcaq/workflow_client.py:244 | 7 | ALICE |
| R5 | [1/3] | ⚪ Low | docs/operations.md and the generator's `CONTROLLER_CLIENT_NOTES` (src/ovcaq/cli.py:296) still say only that the bundle "parses as a JSON object". They do not say that a duplicate key or a non-finite number is refused, or that hex letter case in `contract_bundle_sha256` is ignored. The CHANGELOG states both. Add one sentence to each, keeping `render_command_reference()` parity. | docs/operations.md:128 | 7 | ALICE |
| R6 | [1/3] | ⚪ Low | `RevisionConflictError` and `RejectedRequestError` are defined but never raised. Any non-zero apply exit becomes `ApplyOutcomeUnknownError`, so a structured controller rejection cannot surface as a typed error. These are dead typed errors against the "typed errors" requirement. | src/ovcaq/workflow_client.py:77 | 1 | BLAKE |
| R7 | [1/3] | ⚪ Low | `os.unlink(name)` in the `finally` block of `apply` can itself raise and mask the real error, for example if the temp file was removed externally. | src/ovcaq/workflow_client.py:613 | 1 | BLAKE |
| R8 | [1/3] | 🟡 Medium | 2 touched tests pass against the pre-change code: test_the_published_redaction_constants_keep_their_values, test_a_diagnostic_is_built_without_reading_the_actor_file | tests/workflow_client/test_actor_secret_redaction.py | general | mech-check |
| R9 | [1/3] | 🟡 Medium | 17 touched tests pass against the pre-change code: test_bundle_digest_rejects_a_pin_that_is_not_the_whole_digest +11 more | tests/workflow_client/test_contract_digest.py | general | mech-check |
| R10 | [1/3] | 🟡 Medium | 44 touched tests pass against the pre-change code: test_contract_rejects_live_controller_missing_a_pinned_operation, test_contract_rejects_live_controller_missing_a_pinned_capability +38 more | tests/workflow_client/test_negotiation.py | general | mech-check |
| R11 | [1/3] | 🟡 Medium | 17 touched tests pass against the pre-change code: test_one_pin_in_any_hex_case_is_accepted_by_the_tool_and_the_client, test_a_pin_that_is_not_the_whole_digest_is_refused_by_both +11 more | tests/workflow_client/test_prerequisites_controller.py | general | mech-check |

### Consolidation note

The consolidator merged Alice's carry-forward line about the R3 residual with
Blake's independent short-secret finding into R1 (same file and line), giving it
a two-of-three consensus. Bob's KNOWN row names the same defect at the same site
but kept its own row (R3) because the paraphrase did not match. R1 and R3 are therefore **one
defect** — the cycle-1-deferred short-credential residual — counted twice by the
table. The decision gate treats both as the same settled deferral.

No prior-cycle verification-check queue existed (cycle 1 queued no checks), so
nothing was carried forward.

### Auto-dismissed (ledger)

- [BLAKE] 🟡 The prerequisites tool exits 2, not 1, for an unknown PRD or a config error, and prints no JSON. The spec says outputs are "Exit 0 ready or 1 unavailable with JSON diagnostics" and that "Unknown IDs or missing config fail". argparse exits 2 for an unknown ID (line 198) and `refuse` exits 2 (line 44). Consumers who gate on exit 1 plus a JSON `missing` list get neither. The deviation is documented in docs/operations.md, but it contradicts the spec's two-state contract | File: tools/autopilot-prerequisites:44 — single-voice; exit 2 for a usage error is the argparse convention and the PRD's own Behavior text says unknown IDs and missing config must "fail", which exit 2 satisfies. The R1/R19 fix keeps exit 2 for usage errors deliberately.
- [BLAKE] 🟡 The client treats the bundle digest pin as optional. `controller_settings` passes `bundle_digest=None` when `contract_bundle_sha256` is unset, and `_validated_bundle` then skips the whole-file check. The spec says the client consumes a "pinned schema/fixture bundle" and that `controller_bundle_digest` rejects mismatched artifacts. With no pin configured, any well-formed JSON bundle is trusted, so an unpinned install silently loses the integrity gate. The tool does require the pin for PRD 58, but the client's runtime path is fail-open | File: src/ovcaq/config.py:326 — single-voice
- [BLAKE] 🟡 The evidence tokens are `AP00017` and `Lantern00003`, but the spec says "AP17 evidence" and "Lantern03 evidence". This is a plausible but unconfirmed reading. If a producer emits the literal spec names, the gate will refuse a valid artifact | File: tools/autopilot-prerequisites:32 — single-voice
- [BLAKE] ⚪ The launch-failure class is `ControllerLaunchError`, a subclass of `ControllerError`. The spec says "a plain `ControllerError`". The test asserts only that it is not an unknown outcome, so the behavior is consistent. The strict reading differs | File: src/ovcaq/workflow_client.py:55 — single-voice; and the reporter concedes the intent holds. The PRD asks that a launch failure stay catchable as a plain ControllerError, which a ControllerError subclass satisfies, and catching every OSError from Popen is the safer direction for a pre-spawn failure.
- [BLAKE] 🟡 The test gate reports the full suite as exit 1 with no summary line, so the "./tools/check passes" exit criterion is unverified. My narrow runs passed: `tests/workflow_client` (927 passed), the three CLI parity files (184 passed), `ruff check src tests tools` and `mypy` on `workflow_client.py`, `config.py` and `cli.py`. Something outside these scopes may be failing | File: N/A — single-voice; and answered by this cycle's own Test gate section: the full suite ran at this HEAD and every failure is a sandbox `ps` denial outside tests/workflow_client

Verdict: 11 findings
Tests: 8212 passed, 61 failed, 14 errors (suite run this cycle; counts read from this cycle's own gate log docs/dev/tmp/gate-00057-c2-20261028.log:61 after review-stage failed to parse the padded summary line. ruff check, ruff format --check and mypy are clean; uv build is never reached because the mise chain stops at pytest's exit. All 61 failures and all 14 errors are in tests/integration/ (57 failed, 14 errors) or tests/tui/ (4 failed), the sandbox denies /bin/ps and the log carries 17 `PermissionError: [Errno 1] Operation not permitted: 'ps'`, and this cycle's diff touches no file under either tree; tests/workflow_client has zero failures)
