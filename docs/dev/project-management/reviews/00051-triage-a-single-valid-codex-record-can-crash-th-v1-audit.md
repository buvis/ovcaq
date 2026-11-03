# Decision Audit Log: 00051-triage-a-single-valid-codex-record-can-crash-th-v1

PRD: `00051-triage-a-single-valid-codex-record-can-crash-th-v1.md`
Started: 2026-10-10T10:21:18Z
Completed: 2026-10-10T10:21:18Z
Autonomous: 27  |  Deferred: 8  |  Doubts: 0

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: PRD 00051 repair architecture

**Choice**: Shared scalar validation plus raw-first JSON preflight and strip/sanitize/bound detail ordering

**Rationale**: Reviewed design preserves pre-mutation rejection and strict writer errors; isolated GPT and Anthropic design reviews found no blockers. Recorded non-blockers/questions remain in design log.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: Provider rejection recovery

**Choice**: Operator requested proceeding; retry unchanged authorized repair workflow with existing provider safeguards

**Rationale**: User explicitly asked to proceed after the pause; no provider switch, permission relaxation, prompt obfuscation or cap increase

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The raw-first regressions (byte-exact raw output, gap digest/preview, unchanged adapter state, later healthy terminal) live in `tests/events/test_unicode_frames.py`. The PRD's Task 2 acceptance command (`pytest tests/events/test_unicode_safety.py tests/events/test_tail.py`) and its repository structure both name `test_unicode_safety.py`, so the PRD's own command does not run them. The full suite covers them, and the split keeps the file under 800 lines. Fix: record the file in the PRD or design acceptance text

**Choice**: queued for fresh rework

**Rationale**: Correct design acceptance to include the approved frame-test split; preserve coverage and size limits.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: `has_invalid_unicode_scalar` never stops on cyclic input. It keeps no record of containers it has already visited, so a payload like `d = {"self": d}` loops forever and its pending list grows without limit. I checked this: `Observation(payload=d)` was still running after 3 s. Before this change the recursive copier raised `RecursionError`, and `RawFirstDecoder` turned that into a `raw.unknown` gap. Now a driver bug that builds a cyclic payload freezes the supervisor's decode path, along with the timeout and cleanup steps that wait on it. Both design reviewers raised this as a non-blocker. Fix: track the `id()` of containers already visited, either skipping them or raising `ValueError`. That is about 3 lines and keeps the scan iterative

**Choice**: defer to batch end

**Rationale**: Settled limitation: the reviewed helper contract is explicitly acyclic JSON-like containers; native json.loads cannot create cycles. Preserve the witnessed hang; no cycle-guard scope expansion.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The receiver-lane test special-cases the exact cap input with `if detail != CAP_REPRODUCER`. It then calls `assert_safe_details(tmp_path, lanes, lane_detail)`, which compares the lane detail to itself, so the cap case never checks the exact redacted value or that `[REDACTED]` is present. I confirmed the actual lane detail equals the expected `"x"*4080 + " [REDACTED]"`. Simpler and stronger: drop the guard and call `assert_safe_details(tmp_path, lanes, expected)`. Related: `assert TOKEN not in expected` and `assert "sk-abcdefghijkl" not in expected` (lines 87-88) check fixed test data inside the loop. They should check `observation.payload["detail"]`

**Choice**: queued for fresh rework

**Rationale**: Strengthen independent exact-value and redaction assertions for the receiver lane cap case.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: Hot-path scan cost. `_payload` scans the whole payload at line 224, then `sanitize_json` scans it again at line 252, and `_usage_payload` scans again through `sanitize_json`. Each scan uses a per-character Python generator: about 22 ms per MiB, against about 2.5 ms for a precompiled `re.compile("[\ud800-\udfff]").search`. Every frame also gets re-validated by `replace()` in `_bind_observations` and by `observation_record` in the writer. Behavior-preserving fix: use the regex in the predicate, and call `_sanitize_json` inside `_payload` and `_usage_payload` once the up-front check has passed

**Choice**: queued for fresh rework

**Rationale**: Bounded scan optimization; preserve validation of all original strings before sensitive-key redaction, supported containers, and subclass semantics.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: Removing controls before redaction now leaks tokens that the old order caught. When a bare C0 control, DEL or lone ESC sits between a word character and a token, removal glues them together: `"x\x00sk-" + "a"*30` becomes `xsk-aaaa…` and `"auth\x00Bearer " + "a"*26` becomes `authBearer …`. `_LIKELY_SECRET` needs `\b` before `sk-`/`Bearer`, so neither `bounded_detail` nor the Observation's second sanitizer redacts them. The old order redacted both, because the control supplied the word boundary. Confirmed by tracing the regex by hand; not executed (read-only sandbox)

**Choice**: queued for fresh rework

**Rationale**: Confirmed on actual bounded_detail: C0 removal destroys regex word boundaries for bare and Bearer tokens; old order redacts both. Additional pre-cleanup redaction preserves required post-cleanup redaction and final cap, without interface changes. Amend the exact design contract from this review evidence.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The R2 class of bug still exists at display time, outside this PRD's scope. `bounded_detail` strips only C0 controls and 7-bit CSI. The TUI's `display_text` drops all Cc/Cf/Cs/Zl/Zp characters (src/ovcaq/tui/model.py:57). Confirmed: `"lane sk-abc\u200b<36 chars>"` (also with \x85, \x9b, \u00ad, \u2060 instead of \u200b) passes redaction unchanged and the TUI shows the joined `sk-abcabcdef…` token. Activity text and tool details (src/ovcaq/drivers/codex_events.py:32, src/ovcaq/drivers/codex_events.py:127) strip nothing, so a NUL-split token also renders whole on screen. This needs a durable home (a PRD or issue)

**Choice**: defer to batch end

**Rationale**: Display-time character stripping/activity UI is excluded by this PRD. Preserve durable follow-up evidence; no implicit expansion of 00054.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The preflight's `except (ValueError, RecursionError)` branch, which hands the frame to the driver, has no test. No RawFirstDecoder test feeds a deeply nested frame. Narrowing it to `except ValueError` would still pass the suite: deep frames would then get "driver failed to decode frame" instead of the driver's own native gap, against the contract's "ValueError or RecursionError → delegate unchanged"

**Choice**: queued for fresh rework

**Rationale**: Add independent deep-JSON RecursionError-delegation regression; preserve native fallback and adapter state.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The preflight parse and scan sit inside the tolerant driver catch, so the try blocks nest 4 levels deep (the limit). Hoist the `json.loads` try and the scalar check above it and wrap only `tuple(self._driver.decode(frame))` in `except Exception`. This also matches the contract's "consume decode under the existing tolerant catch"

**Choice**: queued for fresh rework

**Rationale**: Simplify only while preserving tolerant validation/decode failure behavior, ValueError/RecursionError delegation, raw-first ordering and fatal publication outside catches. Reject literal hoisting if it widens error escape; helper extraction within the existing boundary is acceptable.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: Duplicated test tables: the completion construct and record-decode tests repeat the same `additions` dict and body. Hoist it to one module constant or merge them into one test parametrized over construct vs decode

**Choice**: queued for fresh rework

**Rationale**: Share the completion additions fixture while preserving independent construct/decode paths and assertions.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The same strip-after-redact bug exists in the TUI. `display_text` drops Cc/Cf characters from already-sanitized activity and tool text without redacting again, so a stored `sk-abc\x00defghijklmnopqrstuvwxyz0123` shows on screen as the rebuilt token

**Choice**: defer to batch end

**Rationale**: Same out-of-scope display-time defect as R6; preserve its separate citation and deferral.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The same strip-after-redaction pattern survives outside `bounded_detail`. TUI `display_text` drops Cc/Cf characters after the sanitizer has already run. I checked that a NUL-split token in a Codex agent message (`codex_events.py:32`, where controls are never stripped) shows the full token on screen. So do ZWSP- and soft-hyphen-split tokens even in `bounded_detail` output, because format characters are not in its control regex. This is outside this PRD's scope ("no speculative control forms"), but the new doc sentence "prevents controls inside a credential from hiding it from redaction" claims more than the code delivers. Fix: narrow the wording to the recognized C0/DEL/CSI forms and file a follow-up PRD to re-sanitize at the display layer

**Choice**: queued for fresh rework

**Rationale**: Narrow protocol wording to recognized ANSI/control forms; broader TUI follow-up stays deferred.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The `**runtime**` changelog entry claims a runtime fix, but no runtime production code changed (Task 4 added tests only). It repeats the `**events**` gap entry. Fix: fold the continuation and propagation wording into the events entry

**Choice**: queued for fresh rework

**Rationale**: Fold duplicate runtime wording into the events changelog entry, retaining continuity and fatal-writer guarantees.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The supervisor's catch-all handler builds `SessionSummary(..., str(error), ...)`. If the error text carries surrogateescape bytes (a non-UTF-8 path), the new `SessionSummary` check raises `ValueError` inside the handler and `_conclude` is skipped, so the failure record is lost. Not a regression: the strict encode in src/ovcaq/runtime/_session_io.py:19 already failed on such text

**Choice**: defer to batch end

**Rationale**: Pre-existing arbitrary exception/path surrogate handling; retain for later scoped runtime failure work.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The pre-decode check assumes every driver parses frames with plain `json.loads`. A plugin driver that unwraps a prefix or applies its own escapes skips the pre-mutation check. The model still rejects the bad strings, so nothing crashes, but such a driver can change its state before the `Observation` constructor raises. Every frame (up to 1 MiB) is also parsed twice; the PRD sets no performance limit

**Choice**: defer to batch end

**Rationale**: Prefix-unwrapping/custom-escape plugin drivers are outside this native JSON frame contract. Preserve malformed/non-JSON delegation; no generic rollback framework.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: Cannot statically verify: focused and full suites pass at the review HEAD. The test gate was reused from 0961e40, and HEAD 4c84d4d adds chore commits on top

**Choice**: routed to verification

**Rationale**: Route the exact focused command to the next mandatory work verification pass; current-HEAD full verification is separately recorded.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: 66 touched test(s) pass against the pre-change code: test_bounded_detail_redacts_reconstructed_tokens_before_capping, test_bounded_detail_preserves_printable_text_and_caps_after_control_removal +60 more

**Choice**: discard verified preservation finding

**Rationale**: Verified preservation controls: valid Unicode/pairs, printable text, malformed delegation and genuine writer errors must pass before the change. The files also contain independent repair regressions; replay reports 1196 failures and 97 preservation passes with no uncollectable files.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: 5 touched test(s) pass against the pre-change code: test_valid_escaped_pair_remains_a_native_startup_record, test_malformed_and_non_json_frames_keep_native_delegation, test_real_writer_failures_propagate_from_unsafe_native_frames

**Choice**: discard verified preservation finding

**Rationale**: Verified preservation controls: valid Unicode/pairs, printable text, malformed delegation and genuine writer errors must pass before the change. The files also contain independent repair regressions; replay reports 1196 failures and 97 preservation passes with no uncollectable files.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: 26 touched test(s) pass against the pre-change code: test_usage_and_completion_preserve_valid_unicode_scalars +20 more

**Choice**: discard verified preservation finding

**Rationale**: Verified preservation controls: valid Unicode/pairs, printable text, malformed delegation and genuine writer errors must pass before the change. The files also contain independent repair regressions; replay reports 1196 failures and 97 preservation passes with no uncollectable files.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The review-1 two-pass `bounded_detail` leaks the tail of a split token. When the control sits after 20 or more body characters, pass 1 redacts the head. Control removal then glues the tail onto `[REDACTED]`, and pass 2 finds no `sk-` or `Bearer` prefix to match. I ran it to confirm: `bounded_detail('Diagnostic sk-abcdefghijklmnopqrstuvwxyz\x1b[0m0123456789ABCDEF')` returns `'Diagnostic [REDACTED]0123456789ABCDEF'`, the real `turn.failed` payload detail is the same, and `'Bearer '+'a'*23+'\x00bbbbbbbb'` returns `'Bearer [REDACTED]bbbbbbbb'`. Task 3's strip-first order redacted these fully, and pre-PRD code leaked the same way. This breaks two PRD rules ("ANSI/NUL splits of ordinary synthetic tokens are redacted", "synthetic credential fragments never enter normalized details") and makes docs/driver-protocol.md:224 claim too much. Every split test cuts at `token[:6]`, so no test catches it. Fix: before control removal, absorb token characters stuck to a marker across recognized controls with `re.sub(rf"\[REDACTED\](?:{controls})+[A-Za-z0-9_.-]+", "[REDACTED]", sanitize_text(protected))`. I probed this on both leaks plus `x\x00sk-…`, the OSC case and the cap reproducer, and all came out fully redacted (I did not run the suite with it). Also add SPLIT_DETAILS cases that split after 20 or more body characters, for both bare and Bearer tokens

**Choice**: cap-deferred

**Rationale**: Cap reached (cycle 2/2) with the late-split credential suffix HIGH unresolved. All three independent reviewers agree; coordinator reproduced bare/CSI and Bearer/NUL suffix leaks. No cap increase or repair authorized by this transition.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: Unreleased Fixed now has two `**drivers**` entries for one unreleased fix, and they give conflicting orders. Line 43 says redact both before and after control removal. Line 45 says remove controls before redacting, and its claim "so split credentials cannot survive normalization" is false given the finding above. Line 44 ("speed up surrogate detection") describes a tweak to unreleased code, so users see no change from the last release. Simpler: merge lines 43 and 45 into one drivers entry that states what actually shipped, and drop line 44

**Choice**: cap-deferred

**Rationale**: Cap reached with conflicting and overbroad unreleased changelog prose unresolved. Preserve the prior Pat LOW and all three current citations; no tail sweep on cap-out.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The raw-first R7 regressions (byte-exact raw, gap digest and preview, unchanged adapter state, later healthy terminal) live in a file the PRD doesn't list, tests/events/test_unicode_frames.py. The task-2 acceptance command `pytest tests/events/test_unicode_safety.py tests/events/test_tail.py` runs none of them, because test_unicode_safety.py only tests the shared models. That acceptance therefore passes without proving its claims.

**Choice**: cap-deferred

**Rationale**: Preserve literal PRD acceptance-command mismatch. Task 7 corrected the design command within its approved scope; source PRD was intentionally unchanged. Full and focused suites include frame tests, but the PRD command still omits them; requirements ambiguity retained rather than claiming literal closure.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: The fail-first replay count for test_codex_detail_safety.py does not match a static count. By my trace, at e4d765c the 48 new `boundary-*` cases pass on purpose (they guard behavior the old code already had). All `inside-*`, `exact-cap`, `ansi-split`, `nul-split`, `alternate-*-ansi/nul` and rate-limit cases should fail. That predicts about 96 passing at base, but the replay reports 143 (and its own line says "1 + 137 more" = 138)

**Choice**: discarded

**Rationale**: Contradicts computed facts: executed replay reports 143 passing detail cases, not the static estimate of 96. The summary prints six named tests plus 137 more, totaling 143; it never says one plus 137. This is not evidence of an invalid replay.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: 143 touched test(s) pass against the pre-change code: test_bounded_detail_redacts_control_boundaries_and_reconstructed_credentials +137 more

**Choice**: discarded

**Rationale**: Verified preservation checks for original-token boundaries, printable/short details, classifier/reset/OSC/alternate plain behavior. Replay has 1215 repair failures and 175 preservation passes overall, zero uncollectable files. The newly observed late-split regression is independently retained as R1; this computed passing count is not itself a defect.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: 6 touched test(s) pass against the pre-change code: test_valid_escaped_pair_remains_a_native_startup_record, test_malformed_and_non_json_frames_keep_native_delegation, test_deep_json_recursion_preserves_native_gap_and_durable_evidence, test_real_writer_failures_propagate_from_unsafe_native_frames

**Choice**: discarded

**Rationale**: Verified preservation checks: valid escaped pairs, malformed/non-JSON and deep-recursion native delegation, and genuine writer failures are required to retain pre-change behavior. Independent surrogate/raw-first repair cases fail at baseline.

### [autonomous] 2026-10-10T10:21:18Z

**Decision**: 26 touched test(s) pass against the pre-change code: test_usage_and_completion_preserve_valid_unicode_scalars +20 more

**Choice**: discarded

**Rationale**: Verified preservation checks for valid Unicode usage/completion; independent invalid-scalar construct/decode regressions fail against baseline.

### [deferred] 2026-10-10T10:21:18Z

**Decision**: `has_invalid_unicode_scalar` never stops on cyclic input. It keeps no record of containers it has already visited, so a payload like `d = {"self": d}` loops forever and its pending list grows without limit. I checked this: `Observation(payload=d)` was still running after 3 s. Before this change the recursive copier raised `RecursionError`, and `RawFirstDecoder` turned that into a `raw.unknown` gap. Now a driver bug that builds a cyclic payload freezes the supervisor's decode path, along with the timeout and cleanup steps that wait on it. Both design reviewers raised this as a non-blocker. Fix: track the `id()` of containers already visited, either skipping them or raising `ValueError`. That is about 3 lines and keeps the scan iterative

**Rationale**: Settled limitation: the reviewed helper contract is explicitly acyclic JSON-like containers; native json.loads cannot create cycles. Preserve the witnessed hang; no cycle-guard scope expansion.

### [deferred] 2026-10-10T10:21:18Z

**Decision**: The R2 class of bug still exists at display time, outside this PRD's scope. `bounded_detail` strips only C0 controls and 7-bit CSI. The TUI's `display_text` drops all Cc/Cf/Cs/Zl/Zp characters (src/ovcaq/tui/model.py:57). Confirmed: `"lane sk-abc\u200b<36 chars>"` (also with \x85, \x9b, \u00ad, \u2060 instead of \u200b) passes redaction unchanged and the TUI shows the joined `sk-abcabcdef…` token. Activity text and tool details (src/ovcaq/drivers/codex_events.py:32, src/ovcaq/drivers/codex_events.py:127) strip nothing, so a NUL-split token also renders whole on screen. This needs a durable home (a PRD or issue)

**Rationale**: Display-time character stripping/activity UI is excluded by this PRD. Preserve durable follow-up evidence; no implicit expansion of 00054.

### [deferred] 2026-10-10T10:21:18Z

**Decision**: The same strip-after-redact bug exists in the TUI. `display_text` drops Cc/Cf characters from already-sanitized activity and tool text without redacting again, so a stored `sk-abc\x00defghijklmnopqrstuvwxyz0123` shows on screen as the rebuilt token

**Rationale**: Same out-of-scope display-time defect as R6; preserve its separate citation and deferral.

### [deferred] 2026-10-10T10:21:18Z

**Decision**: The supervisor's catch-all handler builds `SessionSummary(..., str(error), ...)`. If the error text carries surrogateescape bytes (a non-UTF-8 path), the new `SessionSummary` check raises `ValueError` inside the handler and `_conclude` is skipped, so the failure record is lost. Not a regression: the strict encode in src/ovcaq/runtime/_session_io.py:19 already failed on such text

**Rationale**: Pre-existing arbitrary exception/path surrogate handling; retain for later scoped runtime failure work.

### [deferred] 2026-10-10T10:21:18Z

**Decision**: The pre-decode check assumes every driver parses frames with plain `json.loads`. A plugin driver that unwraps a prefix or applies its own escapes skips the pre-mutation check. The model still rejects the bad strings, so nothing crashes, but such a driver can change its state before the `Observation` constructor raises. Every frame (up to 1 MiB) is also parsed twice; the PRD sets no performance limit

**Rationale**: Prefix-unwrapping/custom-escape plugin drivers are outside this native JSON frame contract. Preserve malformed/non-JSON delegation; no generic rollback framework.

### [deferred] 2026-10-10T10:21:18Z

**Decision**: The review-1 two-pass `bounded_detail` leaks the tail of a split token. When the control sits after 20 or more body characters, pass 1 redacts the head. Control removal then glues the tail onto `[REDACTED]`, and pass 2 finds no `sk-` or `Bearer` prefix to match. I ran it to confirm: `bounded_detail('Diagnostic sk-abcdefghijklmnopqrstuvwxyz\x1b[0m0123456789ABCDEF')` returns `'Diagnostic [REDACTED]0123456789ABCDEF'`, the real `turn.failed` payload detail is the same, and `'Bearer '+'a'*23+'\x00bbbbbbbb'` returns `'Bearer [REDACTED]bbbbbbbb'`. Task 3's strip-first order redacted these fully, and pre-PRD code leaked the same way. This breaks two PRD rules ("ANSI/NUL splits of ordinary synthetic tokens are redacted", "synthetic credential fragments never enter normalized details") and makes docs/driver-protocol.md:224 claim too much. Every split test cuts at `token[:6]`, so no test catches it. Fix: before control removal, absorb token characters stuck to a marker across recognized controls with `re.sub(rf"\[REDACTED\](?:{controls})+[A-Za-z0-9_.-]+", "[REDACTED]", sanitize_text(protected))`. I probed this on both leaks plus `x\x00sk-…`, the OSC case and the cap reproducer, and all came out fully redacted (I did not run the suite with it). Also add SPLIT_DETAILS cases that split after 20 or more body characters, for both bare and Bearer tokens

**Rationale**: rework cap reached with this finding unresolved; Cap reached (cycle 2/2) with the late-split credential suffix HIGH unresolved. All three independent reviewers agree; coordinator reproduced bare/CSI and Bearer/NUL suffix leaks. No cap increase or repair authorized by this transition.

### [deferred] 2026-10-10T10:21:18Z

**Decision**: Unreleased Fixed now has two `**drivers**` entries for one unreleased fix, and they give conflicting orders. Line 43 says redact both before and after control removal. Line 45 says remove controls before redacting, and its claim "so split credentials cannot survive normalization" is false given the finding above. Line 44 ("speed up surrogate detection") describes a tweak to unreleased code, so users see no change from the last release. Simpler: merge lines 43 and 45 into one drivers entry that states what actually shipped, and drop line 44

**Rationale**: rework cap reached with this finding unresolved; Cap reached with conflicting and overbroad unreleased changelog prose unresolved. Preserve the prior Pat LOW and all three current citations; no tail sweep on cap-out.

### [deferred] 2026-10-10T10:21:18Z

**Decision**: The raw-first R7 regressions (byte-exact raw, gap digest and preview, unchanged adapter state, later healthy terminal) live in a file the PRD doesn't list, tests/events/test_unicode_frames.py. The task-2 acceptance command `pytest tests/events/test_unicode_safety.py tests/events/test_tail.py` runs none of them, because test_unicode_safety.py only tests the shared models. That acceptance therefore passes without proving its claims.

**Rationale**: rework cap reached with this finding unresolved; Preserve literal PRD acceptance-command mismatch. Task 7 corrected the design command within its approved scope; source PRD was intentionally unchanged. Full and focused suites include frame tests, but the PRD command still omits them; requirements ambiguity retained rather than claiming literal closure.
