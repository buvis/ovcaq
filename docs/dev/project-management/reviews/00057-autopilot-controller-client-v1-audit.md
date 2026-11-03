# Decision Audit Log: 00057-autopilot-controller-client-v1

PRD: `00057-autopilot-controller-client-v1.md`
Started: 2026-10-28T03:41:16Z
Completed: 2026-10-28T03:41:16Z
Autonomous: 19  |  Deferred: 2  |  Doubts: 0

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: Task 3 (R5) does not name the observable redaction contract tests must pin.

**Choice**: Length-based credential-agnostic redaction: tokens of >= MIN_SECRET_CHARS chars replaced with REDACTED_MARKER; no actor-file read; _actor_secrets/_json_strings removed; _bounded keeps redact-then-truncate.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: Prior attempt's review satellites (review-1/2/3.md, checks-2/3.json from batch 202610251552, cap_regression stall at cycle 3) occupied the cycle 1-3 filename namespace this fresh review loop needs

**Choice**: Moved them to docs/dev/project-management/reviews/00057-attempt-202610251552/; kept the settled-decisions ledger in place (it is designed to survive parked-PRD resumes and is read by the cap check and by Blake's auto-dismiss)

**Rationale**: Leaving them would have false-triggered Phase 4's 'this cycle's review file exists' skip and the Stop review-file gate against a stale head_sha (e780159), and overwriting review-1.md would have destroyed durable prior-attempt evidence

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: R1 (3/3 HIGH): the prerequisites tool and the client still disagree on what a valid pinned bundle is - the tool lowercases the pin and parses with plain json.loads, the client compares exactly and parses strictly. A recurrence of the prior loop's R3/R6 digest-divergence family, now for two different inputs.

**Choice**: Protocol B research run, verdict proceed: auto-fix as a [D1] rework task

**Rationale**: Recurring issue, so Protocol B applies. Research: Alice confirmed the uppercase-pin failure by probe and the existing test at tests/workflow_client/test_prerequisites_controller.py:94 already feeds the tool an .upper() pin, so the divergence is demonstrated, not speculative. The fix is mechanical and additive (normalise the pin once, copy the strict-parse hooks into the stdlib-only tool, add a both-consumers test); no signature, schema or dependency change, so nothing escalates.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: R2 (3/3 HIGH): negotiation diagnostics bypass redaction - _truncated() replaced _bounded() for package_version, schema_digest and fixture_digest in IncompatibleContractError, so controller-supplied bytes reach the exception text unredacted. A regression this cycle's own rework introduced while fixing R5.

**Choice**: Auto-fix as a [D1] rework task, grouped with R3

**Rationale**: A regression of a security property the PRD names in Behavior (redact actor secrets), raised by all three reviewers, and no test pins either the old or the new behaviour. The fix is additive (route the fields back through _bounded or document the deviation, plus mismatch tests carrying synthetic secrets). Bob's :528 row is the same defect as Alice's and Blake's :498/:531 rows; merged by this gate on issue text plus file and carries Bob's HIGH severity.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: R3 (2/3 HIGH): short credentials still leak - _redact leaves tokens under MIN_SECRET_CHARS intact and the new short-credential test expects that disclosure, against the PRD task-3 acceptance criterion that a secret shorter than MIN_SECRET_CHARS yields a redacted diagnostic, never the raw controller output.

**Choice**: Auto-fix as a [D1] rework task, grouped with R2

**Rationale**: The batch recorded an assumed-ambiguity for exactly this clause (length-based, credential-agnostic redaction) and built to it; two reviewers now read the PRD's own acceptance text as requiring more. The PRD text is explicit, so the PRD wins over the build-time assumption. Not treated as a settled deferral: the prior loop's cap-overflow HIGH covered redaction reading the actor file, which is fixed, and the PRD was amended afterwards to name the short-secret case. Blake's :396 row is merged into Bob's by this gate on issue text plus file, carrying HIGH, so the single-voice discard rule does not reach it.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: R4-R6 (three single-voice Low rows) and R7-R14 (eight single-voice Medium mech-check replay rows)

**Choice**: Discarded, no tasks; all eleven appended to docs/dev/project-management/reviews/00057-autopilot-controller-client-v1-ledger.json so a re-raise is auto-dismissed next cycle

**Rationale**: Single-voice Medium or Low is discarded by rule. R4's tautological-assert claim was verified before discarding and its verification is recorded in the ledger so it is not lost. R6 describes the construction the PRD's task-1 acceptance explicitly prescribes. The eight replay rows are refuted by the replay block itself: 41 of 104 touched tests fail against base d440d982566c, so the rework is pinned and the passers are pre-existing tests inside touched files - the same class the prior loop settled in cycles 2 and 3, and refuted independently by Alice.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: Carl (gemini) produced no review this cycle: gemini-run backend=copilot model=gemini-3.8-flash exited 1 with 'You have exceeded your monthly quota', and the one allowed retry hit the same wall.

**Choice**: Logged and continued with the three reviewers that succeeded (graceful degradation); Carl NOT latched into state.batch.unavailable_reviewers

**Rationale**: The latch is reserved for exit 4, permanent configuration unavailability. A monthly quota is a one-off runtime failure, so Carl is retried next cycle. The diff is a Python transport client, a stdlib CLI gate, docs and tests with no frontend surface, so the UI specialist's absence costs this cycle little, and all lenses that gate convergence (consensus, blind, doubt) ran.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: One definition for a valid pinned bundle is still missing. The tool keeps its own `hashlib.sha256` and plain `json.loads`. (a) The tool lowercases the pin before comparing while `controller_bundle_digest` compares it exactly, confirmed by probe: an uppercase `contract_bundle_sha256` passes the PRD 58 gate and then fails `contract()` with `IncompatibleContractError`; the existing test at tests/workflow_client/test_prerequisites_controller.py:94 passes the tool an `.upper()` pin. (b) The tool's plain `json.loads` accepts duplicate keys and `NaN`/`Infinity` that `_parse_bundle` rejects. Normalise the pin once and give the tool the same strict parse (stdlib-only: copy the hooks, never import ovcaq), then test one configured value through both consumers with an uppercase pin and with a duplicate-key bundle.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: Negotiation diagnostics bypass redaction — a regression this cycle's own rework introduced. `_truncated(live)` at src/ovcaq/workflow_client.py:498 and `_truncated(live[field])` at :531 truncate but no longer redact `package_version`, `schema_digest` and `fixture_digest`, which went through `_bounded` before the rework. A controller that echoes credential bytes into those fields reaches the exception text verbatim, and no test pins either behaviour. Restore the redaction pipeline (or record the deviation in the docstring) and add mismatch tests carrying synthetic secrets.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: Short credentials still leak. `_redact("auth bad abc")` preserves `abc` even when it is the actor credential, and the new short-credential test explicitly expects disclosure; a secret split across whitespace also passes through. The PRD's task-3 acceptance criterion requires that "a secret shorter than `MIN_SECRET_CHARS` and an unreadable actor file both yield a redacted diagnostic, never the raw controller output", so the length-based construction only partly meets it. Suppress controller diagnostics whenever credential safety cannot be established without reading the actor file, and test an echoed short credential.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: Tier for the two [D1] rework tasks (6: workflow_client redaction R2+R3; 7: prerequisites bundle validity R1). Neither carries a CRITICAL line, so the default_model floor does not apply and the documented default would be sonnet.

**Choice**: Passed --default-tier opus to review-close as the Tier classifier output, not as a floor

**Rationale**: Classifier inputs were available and both tasks land on the surface the PRD's own frontmatter rationale names: 'Cross-process contracts, extraction equivalence and concurrency require judgment' (default_model: opus). Task 6 is a security property whose previous opus pass introduced the R2 regression while fixing R5; task 7 is a two-consumer digest/parse equivalence whose live defect is a silent case-normalization mismatch. The measured cost of opus rework (71-118 min against 10-33 min at sonnet) is accepted: with rework_cap 3 and one cycle already spent, a cycle is the scarcer resource than minutes.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: R2: contract() formats the live protocol_major raw with {major!r}, bypassing _bounded, so a controller echoing credential bytes in that field leaks them verbatim into IncompatibleContractError (src/ovcaq/workflow_client.py:560)

**Choice**: auto-fix: created a [D2] rework task

**Rationale**: Cycle 2 decision gate. Same defect class as cycle-1 R2, on the fourth negotiation site the rework missed; verified in the code at line 558-561. The fix is additive (route the value through self._bounded and add a mismatch test with a synthetic secret) and modifies no signature, type or schema, so it classifies auto-fix rather than research-then-decide. Not escalated in tier: the cycle-1 task was correctly specified and simply did not enumerate every site, which is a spec-transmission gap, so the [D2] task carries the site verbatim at the same tier.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: R1 and R3: the short-credential residual — _can_mask_credential settles credential safety from the actor file's stat size, so a short credential wrapped in a larger actor document still reaches a diagnostic (src/ovcaq/workflow_client.py:407)

**Choice**: excluded from the convergence test as a settled deferral; appended to the settled-decisions ledger

**Rationale**: Cycle 2 decision gate. The cycle-1 gate already deferred this exact residual to batch end (batch 202610272211 deferred JSON, type residual-finding, owner "review gate"); Alice carries it forward and Blake and Bob reached it independently. Counting a settled deferral would block convergence for a decision already taken. Closing it needs the credential length or a redaction token declared in configuration, since reading the actor file is forbidden by R5.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: R4: _parse_bundle catches only JSONDecodeError and UnicodeDecodeError, so a RecursionError or a plain ValueError from a pathological bundle escapes contract() as a raw non-ControllerError, while the tool reports 'not valid JSON' (src/ovcaq/workflow_client.py:244)

**Choice**: discarded (single-voice)

**Rationale**: Cycle 2 decision gate. Consensus [1/3] on a Medium, which the gate discards rather than tasks. On the merits it is also narrow: both consumers refuse the bundle either way, so this is an exception-type difference on an already-refused input, not a gate bypass, as the reporter concedes. Appended to the settled-decisions ledger so a re-raise is auto-dismissed.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: R5, R6, R7: three single-voice Low rows — undocumented bundle strictness in docs/operations.md and CONTROLLER_CLIENT_NOTES; RevisionConflictError and RejectedRequestError defined but never raised; os.unlink in apply's finally block can mask the real error

**Choice**: discarded (single-voice)

**Rationale**: Cycle 2 decision gate. Each is Consensus [1/3] at Low severity, which the gate discards rather than tasks. R6 was already discarded in cycle 1 for the same unraised-error pair. All three appended to the settled-decisions ledger.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: R8-R11: four mech-check fail-first replay rows naming touched tests in test_actor_secret_redaction.py, test_contract_digest.py, test_negotiation.py and test_prerequisites_controller.py that pass against the pre-change code

**Choice**: discarded (single-voice)

**Rationale**: Cycle 2 decision gate. Each row is Consensus [1/3] at Medium, which the gate discards rather than tasks. On the merits the replay states a computed fact, not a defect: 38 of the 118 touched tests do fail against base, and the passers are pre-existing tests and deliberate regression guards living in files this cycle also touched. Same class as the cycle-1 and prior-loop rows, discarded for the same reason. Appended to the settled-decisions ledger.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: Carl (gemini) failed for the second consecutive cycle: gemini-run backend=copilot model=gemini-3.8-flash exited 1 with 'You have exceeded your monthly quota' on both the first dispatch and the retry; the engram context pack also failed again (repo not registered with gita)

**Choice**: logged and continued with graceful degradation (3 of 4 lenses)

**Rationale**: Cycle 2 Safety Checks. A quota exit 1 is a one-off runtime failure, not the permanent exit-4 class, so Carl is not latched for the batch. The PRD touches no frontend, so the lost UI/design lens is low-impact here. Consensus, blind and doubt all ran and produced parseable output, so the cycle completed; a single transient reviewer failure must not break an unattended run. Issue count moved 14 -> 11 across cycles, which is a decreasing count and needs no action.

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: R2 was resolved at only three of the four negotiation sites that print a live controller value. `contract()` still formats the live `protocol_major` raw with `{major!r}` and never passes it through `_bounded`. A controller that answers `protocol_major: "<credential bytes>"` (any non-int JSON value, up to the 1 MiB output bound) puts those bytes verbatim into the `IncompatibleContractError` text. Same defect class as cycle-1's R2, on a site the rework missed. Fix with `self._bounded(repr(major))`, or report only the type for a non-int, and pin it with a mismatch test carrying a synthetic secret, as the three new tests do for package_version, schema_digest and fixture_digest.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-10-28T03:41:16Z

**Decision**: Cycle 3 consolidated 4 findings, all single-voice Medium/Low from Blake (config source split, evidence token spelling, unused snapshot workflow_id, kill_group zombie bound)

**Choice**: discarded

**Rationale**: single-voice per the Classification rule; each appended to the settled-decisions ledger. No CRITICAL or HIGH survived; cycle 3 converged.

### [deferred] 2026-10-28T03:41:16Z

**Decision**: Short-secret redaction does not meet the task-3 criterion. `_can_mask_credential` judges safety from the actor file's stat size alone (size >= 8 means "safe"), so a short credential inside a larger file is reported as maskable and then passes `_redact` unmasked.

**Choice**: deferred

**Rationale**: deferred by review-close

### [deferred] 2026-10-28T03:41:16Z

**Decision**: Prior R3 remains partially unresolved: actor-file size cannot establish credential length. A file containing `abc` plus padding passes `_can_mask_credential`, allowing an echoed `abc` into diagnostics.

**Choice**: deferred

**Rationale**: deferred by review-close
