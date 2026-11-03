# PRD 00009 repair triage — 2026-10-07

Read-only production/state audit of cycle-2 R1–R34 against current code. No full-suite rerun; isolated synthetic repros used `.venv/bin/python`. Existing review records 5591 passing tests at reviewed HEAD. Finding numbers below mean **cycle 2**; cycle-1 numbers refer to different issues and must not be reopened mechanically.

## Four bounded repair PRDs

Operator authorized this repair batch on 2026-10-07. The adapter and TUI work
below is split at the shared-model boundary: 00053 owns R1/R4/R12/R19/R20/R22/R23;
00054 owns R3/R10/R11/R27. This avoids one PRD spanning adapter policy and
presentation. All 00053 references to activity below route to 00054.
The UI policy selected for 00054 is the newest 20 activity entries first,
then up to 20 lanes with omission counts; retained model bounds are unchanged.

### 00051 — UTF-8-safe normalized evidence and credential detail

- **R7 confirmed:** `events/tail.py:NormalizedEventWriter.write` uses `ensure_ascii=False` then strict UTF-8 encoding; `RawFirstDecoder._complete` publishes outside its decoder exception boundary. `events/model.py:_identifier`, `sanitize_text`, and `sanitize_json` accept lone surrogates. Feeding an escaped lone surrogate in an `agent_message` through the real raw-first writer raises `UnicodeEncodeError`. Address identifiers, payload values and mapping keys at the shared observation boundary; preserve raw bytes, emit a normalization gap, continue with later frames. Changing serialization alone would retain problematic strings in runtime consumers.
- **R2 confirmed, narrower than original claim:** `drivers/codex_events.py:bounded_detail` sanitizes before stripping controls. Short reconstructed tokens are redacted again by `Observation.__post_init__ → _payload → sanitize_json`, so ordinary whole-token persistence did **not** reproduce. However `'x'*4080 + ' sk-abc\x1b[0mdefghijklmnopqrstuvwxyz0123456789ABCDEF'` passed through `turn.failed` persists the fragment `sk-abcdefghijkl`: bounding occurs before the second sanitizer and drops below its 20-character recognition threshold. Strip controls, sanitize, then bound. All credentials in probes were synthetic; no real exposure established.

Headless acceptance: real `RawFirstDecoder`/evidence writers receive lone high and low surrogates in thread/lane IDs, text/detail, nested values and keys, followed by a healthy terminal; no escaping exception, raw bytes exact, normalized JSONL reloadable, visible `raw.unknown` evidence, healthy record still reduced. Preserve valid non-BMP Unicode. ANSI/NUL-split synthetic tokens at ordinary and 4096-character cap boundaries must leave neither whole token nor identifiable fragment in failure/rate/lane normalized payloads. No live provider or plugin calls.

### 00052 — refresh reviewed CLI version evidence

- **R8 readiness issue, deliberate policy:** `drivers/codex.py:CodexDriver.probe` explicitly requires exact `0.160.0`; installed `0.160.1` rejection is consistent with the established drift guard. Repair by reviewing and refreshing the exact pinned version/help/schema/provenance contract for the approved installed release, not by silently accepting arbitrary patches.
- **R17 test gap:** `_run_probe_command` actually caps stdout/stderr buffers at 16 KiB, but `test_codex_rework_probe.py` asserts final diagnostic size only. Add a real subprocess that exceeds each stream cap and assert returned buffers, complete draining and bounded completion.

Headless acceptance: approved exact version/auth fake passes; unreviewed versions, aliases, prereleases and trailing noise fail before agent spawn. Fixture hashes/provenance match refreshed read-only evidence. Oversized stdout and stderr are both drained without buffer growth beyond 16 KiB. Preserve argv literalness, five-second timeout and authentication diagnostics. Real read-only CLI/help checks are sufficient; real model smoke remains downstream.

### 00053/00054 — adapter operational behavior and activity

- **R1 confirmed:** `CodexDriver._item_observations` passes all remembered lane IDs to `item_lanes`, including done lanes. Real decoder sequence running → completed → shutdown emits `lane.failed`. Only running identities should qualify for interrupted/shutdown/not_found failure projection. Test all three statuses after completion; existing running-then-interrupted failure behavior must remain.
- **R4 confirmed:** `codex_events.classify_failure` classifies capacity as `rate_limit`; `runtime/decision.py:_failure_decision` then halts without reset. Classify native server capacity as connectivity and test bounded WAIT/retry exhaustion through shared decisions. `test_codex_rework_decode.py:94` currently pins the defect.
- **R19 confirmed:** `config.resolve_phase_route` resolves a tier to its model; `Supervisor._attempt` passes `route.model`; `CodexDriver.build_launch` resolves keys again. With `{default='o3', o3='o3-pro'}`, resolved `o3` launches `o3-pro`. Define unambiguous resolved-model handoff while preserving documented direct tier launch behavior. Existing `test_codex_launch.py:test_tier_key_resolves_before_a_matching_configured_model_value` deliberately pins direct key precedence, so merely reversing precedence breaks that contract. Claude's edge bridge already handles supervisor-resolved models.
- **R20 confirmed:** `classify_failure('processed 401 files')` returns authentication. Match numeric codes in diagnostic/status context rather than any number; independent tests should retain genuine HTTP 401/403/429/502/503 classification and ordinary diagnostic words.
- **R23 confirmed:** `ClaudeDriver.probe` uses host PATH, whereas the spawn receives the configured overlay. An executable only in temporary overlay PATH exists and is executable but probes unhealthy. Probe the same effective PATH used at launch. Add **R22** missing-command Claude headless no-spawn health-gate coverage alongside the successful overlay case.
- **R3 confirmed by actual shapes:** `tui/model.py:_observe_activity` reads only `text` and keys every ID-less message as `('message','')`; Codex provisional errors and Claude `rate_limit_warning` use `detail`, while Codex turn markers replace them. Render actual detail, preserve distinct ID-less entries within the existing cap, and preserve updates for real IDs. Test decoder-produced payloads, repeated errors and following turn records.
- **R10 operational display defect:** `tui/panels.py:activity_panel` prints up to 256 chronological activities after up to 256 lanes, burying current work. Bound the rendered recent window and expose newest entries first; rendering acceptance must show newest activity even with crowded lanes, without changing lifecycle policy.
- **R12 test oracle gap:** `test_codex_decode_terminals.py:test_fixture_error_then_identical_failure_has_one_terminal_and_rate_start` derives expected classes with the classifier under test. Use literal fixture→class expectations for all four failure families.
- **R27 supporting cleanup:** remove invented `input` fallback/test payload only while repairing activity tests; assert real Claude tool shapes. **R11 supporting docs:** update fixture matrix for checked-in `lanes-matched.jsonl`, remove in-place variant claim, and document current tool/message/plan rendering in fixture README and driver protocol.

Headless acceptance: fake supervised launch records correct colliding tier/model argv; shared policy handles overload with bounded retries; literal status-code cases avoid numeric false positives; both native adapters exercise health failure before spawn and configured PATH success. Decoder→projection→Rich plain rendering verifies completed lane stays completed, provisional detail survives a later turn, repeated ID-less errors remain distinct, real ID updates consolidate, and recent activity is visible with bounded output. Independent failure fixture expectations, existing adapter/fake conformance and relevant runtime/TUI suites pass. No real provider run or policy-default migration.

## Complete R1–R34 disposition

| Ref | Disposition |
| --- | --- |
| R1 | Confirmed defect; 00053 lane-terminal regression. |
| R2 | Confirmed helper/order and cap-fragment defect; 00051; ordinary full-key normalized persistence disproved. |
| R3 | Confirmed actual payload/identity defect; 00054. |
| R4 | Confirmed overload retry defect; 00053. |
| R5 | Style-only helper return/name; leave alone. |
| R6 | Changelog duplication/blank line only; leave alone. |
| R7 | Confirmed supervisor crash; 00051. |
| R8 | Exact pin intentionally fails closed; reviewed contract refresh in 00052, no blanket patch tolerance. |
| R9 | Style-only prefix slicing; leave alone. |
| R10 | Current work hidden by panel history; 00054 bounded recent rendering. |
| R11 | Observable contract docs stale; update as support for 00054. |
| R12 | Independent oracle missing; targeted 00053 tests. |
| R13 | Review-oriented test naming/duplicate placement tests; no behavior defect, avoid rename/delete churn. |
| R14 | Style-only gap-join idiom; leave alone. |
| R15 | Style-only conditional merge; leave alone. |
| R16 | Test-local redundant calculation; leave alone. |
| R17 | Capture cap implemented, meaningful guard missing; 00052 test. |
| R18 | Extra validated options/explicit-model opt-in is established tested behavior; no necessary repair or API pruning. |
| R19 | Confirmed resolved model double mapping; 00053. |
| R20 | Numeric false classification reproduced; 00053. |
| R21 | Cleanup warning cause remains untraced; preserve as unconfirmed, no speculative process ownership change. |
| R22 | Shared health gate lacks Claude end-to-end regression; 00053 with R23. |
| R23 | Overlay PATH mismatch reproduced; 00053. |
| R24 | Already verified by 5591-pass reviewed-HEAD record; no defect. |
| R25 | Pipe-held-open timeout fails closed; descendant/process-group ownership explicitly settled as batch-end policy, exclude. |
| R26 | Unchanged preexisting test length; exclude. |
| R27 | Dead input fallback and invented Claude test; supporting real-shape activity cleanup in 00054. |
| R28 | Fake command-backed handoff test guards integration already present at base; base-pass is valid regression coverage, no defect. |
| R29 | Literal prompt override test guards preexisting behavior; base-pass alone warrants no repair. |
| R30 | Explicit reset punctuation/ceiling tests partly cover existing behavior; no failed contract shown, retain. |
| R31 | Exact version alias rejection tests cover drift guard; retain/update for refreshed approved version. |
| R32 | Repeated identical native thread success is intentionally the non-conflict control; retain. |
| R33 | Both-adapter fake command handoff drain guards existing shared integration; retain. |
| R34 | Fixture→fake supervisor→projection tests guard existing integration; retain; new actual-payload activity cases are covered by R3. |

Settled scope remains unchanged: ambiguous native reset prose, synthetic/live fixture capture policy, neutral phase-tier naming, and probe descendant ownership remain policy deferrals. No historical hold is promoted by this triage. Full gates belong to repair execution/review, not this read-only audit.
