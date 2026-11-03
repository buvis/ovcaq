---
prd: docs/dev/project-management/prds/wip/00051-triage-a-single-valid-codex-record-can-crash-th-v1.md
review: 1
date: 2026-10-10
head_sha: 4c84d4dbfca6b66226c656b7ae9006085ddd9ddc
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
dispatch_rows:
  bob: 5ced95f7
---

# Review: 00051-triage-a-single-valid-codex-record-can-crash-th-v1

Diff range: `e4d765c42d1be7b42c27312e8a5f474d61178b52..4c84d4dbfca6b66226c656b7ae9006085ddd9ddc`

codex_rung_guard: not fired
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/alice-output-00051-c1-20261010.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/blake-output-00051-c1-20261010.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00051-c1-20261010.txt.receipt.json
provider_review_guard: satisfied

The actual implementation-company guard supersedes the legacy launcher guard. All contributing implementation models are OpenAI; all three complete lenses ran independently through approved external Claude processes. Eve did not run. Carl: operator-skipped for this repair batch. No reviewer resumed another thread. The immutable implementation audit snapshot is retained through rework; do not regenerate it until the next review cycle.

## Review Summary

Reviewed: 5 completed tasks, full PRD work range. All required reviewers succeeded, with complete Alice R, Blake B, and Bob R/D rubrics preserved below. One confirmed HIGH remains. The 9 selected bounded fixes are grouped by review-close; no repair ran in this review session.

Pack: failed (engram: repository not registered); source fallback sentinel was used. Review-stage initially reused verification from code SHA 0961e40; the coordinator then ran all quality gates at this exact reviewed HEAD. Restricted pytest produced 554 failures / 172 setup errors due host process-control denials; its full raw output is retained. Approved retry passed 6884 tests with two existing pytest cleanup warnings. Sync, lint, format, mypy (61 source files), and sdist/wheel build passed. Blake independently reported the same passing counts at this HEAD. Bob's static verification limitation is retained unchanged and routed to the exact focused command in checks-1.json for the next work pass.

Fail-first replay initially could not create a git worktree under the sandbox. Approved replay succeeded: 1293 cases, 1196 failing at the pre-change base, 97 passing preservation cases, zero uncollectable files. All three computed rows are retained in the findings table and dismissed with preservation evidence. No tautological shapes were detected. Replay worktree was removed by its helper; only the main checkout remains.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/3] | 🟡 | The raw-first regressions (byte-exact raw output, gap digest/preview, unchanged adapter state, later healthy terminal) live in `tests/events/test_unicode_frames.py`. The PRD's Task 2 acceptance command (`pytest tests/events/test_unicode_safety.py tests/events/test_tail.py`) and its repository structure both name `test_unicode_safety.py`, so the PRD's own command does not run them. The full suite covers them, and the split keeps the file under 800 lines. Fix: record the file in the PRD or design acceptance text | tests/events/test_unicode_frames.py:1 | 2 | ALICE, BLAKE, BOB |
| R2 | [2/3] | 🟡 | `has_invalid_unicode_scalar` never stops on cyclic input. It keeps no record of containers it has already visited, so a payload like `d = {"self": d}` loops forever and its pending list grows without limit. I checked this: `Observation(payload=d)` was still running after 3 s. Before this change the recursive copier raised `RecursionError`, and `RawFirstDecoder` turned that into a `raw.unknown` gap. Now a driver bug that builds a cyclic payload freezes the supervisor's decode path, along with the timeout and cleanup steps that wait on it. Both design reviewers raised this as a non-blocker. Fix: track the `id()` of containers already visited, either skipping them or raising `ValueError`. That is about 3 lines and keeps the scan iterative | src/ovcaq/events/model.py:77 | 1 | ALICE, BOB |
| R3 | [2/3] | 🟡 | The receiver-lane test special-cases the exact cap input with `if detail != CAP_REPRODUCER`. It then calls `assert_safe_details(tmp_path, lanes, lane_detail)`, which compares the lane detail to itself, so the cap case never checks the exact redacted value or that `[REDACTED]` is present. I confirmed the actual lane detail equals the expected `"x"*4080 + " [REDACTED]"`. Simpler and stronger: drop the guard and call `assert_safe_details(tmp_path, lanes, expected)`. Related: `assert TOKEN not in expected` and `assert "sk-abcdefghijkl" not in expected` (lines 87-88) check fixed test data inside the loop. They should check `observation.payload["detail"]` | tests/drivers/test_codex_detail_safety.py:281 | 3 | ALICE, BOB |
| R4 | [2/3] | ⚪ | Hot-path scan cost. `_payload` scans the whole payload at line 224, then `sanitize_json` scans it again at line 252, and `_usage_payload` scans again through `sanitize_json`. Each scan uses a per-character Python generator: about 22 ms per MiB, against about 2.5 ms for a precompiled `re.compile("[\ud800-\udfff]").search`. Every frame also gets re-validated by `replace()` in `_bind_observations` and by `observation_record` in the writer. Behavior-preserving fix: use the regex in the predicate, and call `_sanitize_json` inside `_payload` and `_usage_payload` once the up-front check has passed | src/ovcaq/events/model.py:224 | 1 | ALICE, BOB |
| R5 | [1/3] | 🟠 | Removing controls before redaction now leaks tokens that the old order caught. When a bare C0 control, DEL or lone ESC sits between a word character and a token, removal glues them together: `"x\x00sk-" + "a"*30` becomes `xsk-aaaa…` and `"auth\x00Bearer " + "a"*26` becomes `authBearer …`. `_LIKELY_SECRET` needs `\b` before `sk-`/`Bearer`, so neither `bounded_detail` nor the Observation's second sanitizer redacts them. The old order redacted both, because the control supplied the word boundary. Confirmed by tracing the regex by hand; not executed (read-only sandbox) | src/ovcaq/drivers/codex_events.py:64 | 3 | BOB |
| R6 | [1/3] | 🟡 | The R2 class of bug still exists at display time, outside this PRD's scope. `bounded_detail` strips only C0 controls and 7-bit CSI. The TUI's `display_text` drops all Cc/Cf/Cs/Zl/Zp characters (src/ovcaq/tui/model.py:57). Confirmed: `"lane sk-abc\u200b<36 chars>"` (also with \x85, \x9b, \u00ad, \u2060 instead of \u200b) passes redaction unchanged and the TUI shows the joined `sk-abcabcdef…` token. Activity text and tool details (src/ovcaq/drivers/codex_events.py:32, src/ovcaq/drivers/codex_events.py:127) strip nothing, so a NUL-split token also renders whole on screen. This needs a durable home (a PRD or issue) | src/ovcaq/drivers/codex_events.py:59 | 3 | BLAKE |
| R7 | [1/3] | 🟡 | The preflight's `except (ValueError, RecursionError)` branch, which hands the frame to the driver, has no test. No RawFirstDecoder test feeds a deeply nested frame. Narrowing it to `except ValueError` would still pass the suite: deep frames would then get "driver failed to decode frame" instead of the driver's own native gap, against the contract's "ValueError or RecursionError → delegate unchanged" | src/ovcaq/events/tail.py:119 | 2 | BOB |
| R8 | [1/3] | 🟡 | The preflight parse and scan sit inside the tolerant driver catch, so the try blocks nest 4 levels deep (the limit). Hoist the `json.loads` try and the scalar check above it and wrap only `tuple(self._driver.decode(frame))` in `except Exception`. This also matches the contract's "consume decode under the existing tolerant catch" | src/ovcaq/events/tail.py:116 | 2 | BOB |
| R9 | [1/3] | 🟡 | Duplicated test tables: the completion construct and record-decode tests repeat the same `additions` dict and body. Hoist it to one module constant or merge them into one test parametrized over construct vs decode | tests/events/test_unicode_safety.py:314 | 1 | BOB |
| R10 | [1/3] | 🟡 | The same strip-after-redact bug exists in the TUI. `display_text` drops Cc/Cf characters from already-sanitized activity and tool text without redacting again, so a stored `sk-abc\x00defghijklmnopqrstuvwxyz0123` shows on screen as the rebuilt token | src/ovcaq/tui/model.py:136 | general | BOB |
| R11 | [1/3] | ⚪ | The same strip-after-redaction pattern survives outside `bounded_detail`. TUI `display_text` drops Cc/Cf characters after the sanitizer has already run. I checked that a NUL-split token in a Codex agent message (`codex_events.py:32`, where controls are never stripped) shows the full token on screen. So do ZWSP- and soft-hyphen-split tokens even in `bounded_detail` output, because format characters are not in its control regex. This is outside this PRD's scope ("no speculative control forms"), but the new doc sentence "prevents controls inside a credential from hiding it from redaction" claims more than the code delivers. Fix: narrow the wording to the recognized C0/DEL/CSI forms and file a follow-up PRD to re-sanitize at the display layer | docs/driver-protocol.md:224 | 5 | ALICE |
| R12 | [1/3] | ⚪ | The `**runtime**` changelog entry claims a runtime fix, but no runtime production code changed (Task 4 added tests only). It repeats the `**events**` gap entry. Fix: fold the continuation and propagation wording into the events entry | CHANGELOG.md:43 | 4 | ALICE |
| R13 | [1/3] | ⚪ | The supervisor's catch-all handler builds `SessionSummary(..., str(error), ...)`. If the error text carries surrogateescape bytes (a non-UTF-8 path), the new `SessionSummary` check raises `ValueError` inside the handler and `_conclude` is skipped, so the failure record is lost. Not a regression: the strict encode in src/ovcaq/runtime/_session_io.py:19 already failed on such text | src/ovcaq/runtime/supervisor.py:370 | general | BLAKE |
| R14 | [1/3] | ⚪ | The pre-decode check assumes every driver parses frames with plain `json.loads`. A plugin driver that unwraps a prefix or applies its own escapes skips the pre-mutation check. The model still rejects the bad strings, so nothing crashes, but such a driver can change its state before the `Observation` constructor raises. Every frame (up to 1 MiB) is also parsed twice; the PRD sets no performance limit | src/ovcaq/events/tail.py:118 | 2 | BLAKE |
| R15 | [1/3] | ⚪ | Cannot statically verify: focused and full suites pass at the review HEAD. The test gate was reused from 0961e40, and HEAD 4c84d4d adds chore commits on top | N/A | general | BOB |
| R16 | [1/3] | 🟡 | 66 touched test(s) pass against the pre-change code: test_bounded_detail_redacts_reconstructed_tokens_before_capping, test_bounded_detail_preserves_printable_text_and_caps_after_control_removal +60 more | tests/drivers/test_codex_detail_safety.py | general | mech-check |
| R17 | [1/3] | 🟡 | 5 touched test(s) pass against the pre-change code: test_valid_escaped_pair_remains_a_native_startup_record, test_malformed_and_non_json_frames_keep_native_delegation, test_real_writer_failures_propagate_from_unsafe_native_frames | tests/events/test_unicode_frames.py | general | mech-check |
| R18 | [1/3] | 🟡 | 26 touched test(s) pass against the pre-change code: test_usage_and_completion_preserve_valid_unicode_scalars +20 more | tests/events/test_unicode_safety.py | general | mech-check |


## Decision Gate

Cycle 1 < rework cap 2. The verified HIGH is an in-scope redaction regression; no cap increase or deferral of that HIGH. It stems from the design's exact strip-first recipe omitting original word boundaries, rather than failure to implement the transmitted contract. A new bounded follow-up must amend that recipe to preserve original-token redaction while also redacting after cleanup and before the final cap. Public signatures, control forms, classification/reset handling and original R2 cap regression remain unchanged. Existing original task/attempt history is preserved.

| Ref | Classification | Reason |
|---|---|---|
| R1 | fix | Correct design acceptance to include the approved frame-test split; preserve coverage and size limits. |
| R2 | defer | Settled limitation: the reviewed helper contract is explicitly acyclic JSON-like containers; native json.loads cannot create cycles. Preserve the witnessed hang; no cycle-guard scope expansion. |
| R3 | fix | Strengthen independent exact-value and redaction assertions for the receiver lane cap case. |
| R4 | fix | Bounded scan optimization; preserve validation of all original strings before sensitive-key redaction, supported containers, and subclass semantics. |
| R5 | fix | Confirmed on actual bounded_detail: C0 removal destroys regex word boundaries for bare and Bearer tokens; old order redacts both. Additional pre-cleanup redaction preserves required post-cleanup redaction and final cap, without interface changes. Amend the exact design contract from this review evidence. |
| R6 | defer | Display-time character stripping/activity UI is excluded by this PRD. Preserve durable follow-up evidence; no implicit expansion of 00054. |
| R7 | fix | Add independent deep-JSON RecursionError-delegation regression; preserve native fallback and adapter state. |
| R8 | fix | Simplify only while preserving tolerant validation/decode failure behavior, ValueError/RecursionError delegation, raw-first ordering and fatal publication outside catches. Reject literal hoisting if it widens error escape; helper extraction within the existing boundary is acceptable. |
| R9 | fix | Share the completion additions fixture while preserving independent construct/decode paths and assertions. |
| R10 | defer | Same out-of-scope display-time defect as R6; preserve its separate citation and deferral. |
| R11 | fix | Narrow protocol wording to recognized ANSI/control forms; broader TUI follow-up stays deferred. |
| R12 | fix | Fold duplicate runtime wording into the events changelog entry, retaining continuity and fatal-writer guarantees. |
| R13 | defer | Pre-existing arbitrary exception/path surrogate handling; retain for later scoped runtime failure work. |
| R14 | defer | Prefix-unwrapping/custom-escape plugin drivers are outside this native JSON frame contract. Preserve malformed/non-JSON delegation; no generic rollback framework. |
| R15 | verify | Route the exact focused command to the next mandatory work verification pass; current-HEAD full verification is separately recorded. |
| R16 | discard | Verified preservation controls: valid Unicode/pairs, printable text, malformed delegation and genuine writer errors must pass before the change. The files also contain independent repair regressions; replay reports 1196 failures and 97 preservation passes with no uncollectable files. |
| R17 | discard | Verified preservation controls: valid Unicode/pairs, printable text, malformed delegation and genuine writer errors must pass before the change. The files also contain independent repair regressions; replay reports 1196 failures and 97 preservation passes with no uncollectable files. |
| R18 | discard | Verified preservation controls: valid Unicode/pairs, printable text, malformed delegation and genuine writer errors must pass before the change. The files also contain independent repair regressions; replay reports 1196 failures and 97 preservation passes with no uncollectable files. |


## Source repair closure evidence

Source PRD 00009 cycle 2 R7: all three lenses accept the scalar/native preflight guarantees; Alice ran 1383 named focused cases and Blake independently verified all 6884 tests. Native invalid frames retain byte-exact raw evidence, produce one gap without adapter mutation, allow later healthy real-child completion, and leave genuine publication failures fatal. Historical R7 evidence remains intact; additional RecursionError-delegation coverage is queued, so final repair closure awaits the next fresh review.

Source PRD 00009 cycle 2 R2: the original exact control-split cap reproducer and native failure/rate/lane cases pass. This cycle R5 nevertheless verifies a new word-boundary regression for `x + NUL + sk-token` and `auth + NUL + Bearer-token`; actual bounded_detail leaks both while the prior ordering redacted both. R2 is not declared fully repaired until rework and fresh review close this replacement defect. All strings are synthetic; no actual credential exposure is claimed.

Out-of-scope TUI display-time reconstruction, cyclic direct containers, arbitrary surrogate exception paths and non-JSON custom-driver transforms remain durable settled deferrals, without erasing any reviewer output or promoting held PRDs. PRDs 00052–00054 remain pending; 00010 stays held.

## Alice

Provider: Anthropic; actual model: claude-opus-5-5; effort: xhigh; session: 296495de-8078-47dd-971f-b75b8dac5e72.

[ALICE] 🟡 `has_invalid_unicode_scalar` never stops on cyclic input. It keeps no record of containers it has already visited, so a payload like `d = {"self": d}` loops forever and its pending list grows without limit. I checked this: `Observation(payload=d)` was still running after 3 s. Before this change the recursive copier raised `RecursionError`, and `RawFirstDecoder` turned that into a `raw.unknown` gap. Now a driver bug that builds a cyclic payload freezes the supervisor's decode path, along with the timeout and cleanup steps that wait on it. Both design reviewers raised this as a non-blocker. Fix: track the `id()` of containers already visited, either skipping them or raising `ValueError`. That is about 3 lines and keeps the scan iterative | File: src/ovcaq/events/model.py:77 | Task: 1
[ALICE] 🟡 The receiver-lane test special-cases the exact cap input with `if detail != CAP_REPRODUCER`. It then calls `assert_safe_details(tmp_path, lanes, lane_detail)`, which compares the lane detail to itself, so the cap case never checks the exact redacted value or that `[REDACTED]` is present. I confirmed the actual lane detail equals the expected `"x"*4080 + " [REDACTED]"`. Simpler and stronger: drop the guard and call `assert_safe_details(tmp_path, lanes, expected)`. Related: `assert TOKEN not in expected` and `assert "sk-abcdefghijkl" not in expected` (lines 87-88) check fixed test data inside the loop. They should check `observation.payload["detail"]` | File: tests/drivers/test_codex_detail_safety.py:281 | Task: 3
[ALICE] ⚪ Hot-path scan cost. `_payload` scans the whole payload at line 224, then `sanitize_json` scans it again at line 252, and `_usage_payload` scans again through `sanitize_json`. Each scan uses a per-character Python generator: about 22 ms per MiB, against about 2.5 ms for a precompiled `re.compile("[\ud800-\udfff]").search`. Every frame also gets re-validated by `replace()` in `_bind_observations` and by `observation_record` in the writer. Behavior-preserving fix: use the regex in the predicate, and call `_sanitize_json` inside `_payload` and `_usage_payload` once the up-front check has passed | File: src/ovcaq/events/model.py:224 | Task: 1
[ALICE] ⚪ The same strip-after-redaction pattern survives outside `bounded_detail`. TUI `display_text` drops Cc/Cf characters after the sanitizer has already run. I checked that a NUL-split token in a Codex agent message (`codex_events.py:32`, where controls are never stripped) shows the full token on screen. So do ZWSP- and soft-hyphen-split tokens even in `bounded_detail` output, because format characters are not in its control regex. This is outside this PRD's scope ("no speculative control forms"), but the new doc sentence "prevents controls inside a credential from hiding it from redaction" claims more than the code delivers. Fix: narrow the wording to the recognized C0/DEL/CSI forms and file a follow-up PRD to re-sanitize at the display layer | File: docs/driver-protocol.md:224 | Task: 5
[ALICE] ⚪ The raw-first regressions (byte-exact raw output, gap digest/preview, unchanged adapter state, later healthy terminal) live in `tests/events/test_unicode_frames.py`. The PRD's Task 2 acceptance command (`pytest tests/events/test_unicode_safety.py tests/events/test_tail.py`) and its repository structure both name `test_unicode_safety.py`, so the PRD's own command does not run them. The full suite covers them, and the split keeps the file under 800 lines. Fix: record the file in the PRD or design acceptance text | File: tests/events/test_unicode_frames.py:1 | Task: 2
[ALICE] ⚪ The `**runtime**` changelog entry claims a runtime fix, but no runtime production code changed (Task 4 added tests only). It repeats the `**events**` gap entry. Fix: fold the continuation and propagation wording into the events entry | File: CHANGELOG.md:43 | Task: 4

Focused tests I ran on HEAD (test_unicode_safety, test_unicode_frames, test_codex_detail_safety, test_unicode_continuity, test_tail, test_codex_decode_terminals): `1383 passed, 2 warnings`. Most of the tests flagged as passing on the old code are deliberate preservation tests. The key regressions (the exact cap input, native-frame state not changing, the normalized-stage writer failure) fail on the old code as they should.

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

Provider: Anthropic; actual model: claude-opus-5-5; effort: xhigh; session: 1a3c0b3f-796d-46ef-a146-a96b9508aedd.

Gates I ran on HEAD `4c84d4d`: `pytest` 6884 passed; `ruff check` passed; `ruff format --check` reported 232 files already formatted; `mypy` found no issues in 61 files; `uv build` built the sdist and wheel. I skipped `uv sync --all-groups` because the existing venv already works. A probe script (since deleted) confirmed the display-time leak in the second finding below.

[BLAKE] 🟡 The raw-first regressions are in a file the PRD doesn't list (tests/events/test_unicode_frames.py). The PRD's Phase 1 acceptance command (`pytest tests/events/test_unicode_safety.py tests/events/test_tail.py`) never runs them, so it shows nothing about byte-exact raw, gap digest/preview, unchanged adapter state or the later healthy terminal. The tests themselves are thorough and pass. Fix by moving them into test_unicode_safety.py, as the PRD's repo structure says, or by correcting the acceptance command | File: tests/events/test_unicode_frames.py:172 | Task: 2
[BLAKE] 🟡 The R2 class of bug still exists at display time, outside this PRD's scope. `bounded_detail` strips only C0 controls and 7-bit CSI. The TUI's `display_text` drops all Cc/Cf/Cs/Zl/Zp characters (src/ovcaq/tui/model.py:57). Confirmed: `"lane sk-abc\u200b<36 chars>"` (also with \x85, \x9b, \u00ad, \u2060 instead of \u200b) passes redaction unchanged and the TUI shows the joined `sk-abcabcdef…` token. Activity text and tool details (src/ovcaq/drivers/codex_events.py:32, src/ovcaq/drivers/codex_events.py:127) strip nothing, so a NUL-split token also renders whole on screen. This needs a durable home (a PRD or issue) | File: src/ovcaq/drivers/codex_events.py:59 | Task: 3
[BLAKE] ⚪ The supervisor's catch-all handler builds `SessionSummary(..., str(error), ...)`. If the error text carries surrogateescape bytes (a non-UTF-8 path), the new `SessionSummary` check raises `ValueError` inside the handler and `_conclude` is skipped, so the failure record is lost. Not a regression: the strict encode in src/ovcaq/runtime/_session_io.py:19 already failed on such text | File: src/ovcaq/runtime/supervisor.py:370 | Task: general
[BLAKE] ⚪ The pre-decode check assumes every driver parses frames with plain `json.loads`. A plugin driver that unwraps a prefix or applies its own escapes skips the pre-mutation check. The model still rejects the bad strings, so nothing crashes, but such a driver can change its state before the `Observation` constructor raises. Every frame (up to 1 MiB) is also parsed twice; the PRD sets no performance limit | File: src/ovcaq/events/tail.py:118 | Task: 2

Phase mapping: I matched B15–B17 to the PRD's phases by name. Phase 1 = Core, Phase 2 = Integration, and the PRD has no Phase 3, so B17 passes with nothing to check.

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
B15: fail
B16: pass
B17: pass
B18: pass
B19: pass

## Bob

Provider: Anthropic; actual model: claude-opus-5-5; effort: xhigh; session: 2fe37332-5ded-4d3a-8c92-5b2313b6812e.

[BOB] 🟠 Removing controls before redaction now leaks tokens that the old order caught. When a bare C0 control, DEL or lone ESC sits between a word character and a token, removal glues them together: `"x\x00sk-" + "a"*30` becomes `xsk-aaaa…` and `"auth\x00Bearer " + "a"*26` becomes `authBearer …`. `_LIKELY_SECRET` needs `\b` before `sk-`/`Bearer`, so neither `bounded_detail` nor the Observation's second sanitizer redacts them. The old order redacted both, because the control supplied the word boundary. Confirmed by tracing the regex by hand; not executed (read-only sandbox) | File: src/ovcaq/drivers/codex_events.py:64 | Task: 3
[BOB] 🟡 The preflight's `except (ValueError, RecursionError)` branch, which hands the frame to the driver, has no test. No RawFirstDecoder test feeds a deeply nested frame. Narrowing it to `except ValueError` would still pass the suite: deep frames would then get "driver failed to decode frame" instead of the driver's own native gap, against the contract's "ValueError or RecursionError → delegate unchanged" | File: src/ovcaq/events/tail.py:119 | Task: 2
[BOB] 🟡 The preflight parse and scan sit inside the tolerant driver catch, so the try blocks nest 4 levels deep (the limit). Hoist the `json.loads` try and the scalar check above it and wrap only `tuple(self._driver.decode(frame))` in `except Exception`. This also matches the contract's "consume decode under the existing tolerant catch" | File: src/ovcaq/events/tail.py:116 | Task: 2
[BOB] 🟡 Duplicated test tables: the completion construct and record-decode tests repeat the same `additions` dict and body. Hoist it to one module constant or merge them into one test parametrized over construct vs decode | File: tests/events/test_unicode_safety.py:314 | Task: 1
[BOB] ⚪ The receiver-lane test compares a value with itself. It passes `lane_detail` as `expected` to `assert_safe_details`, so `payload["detail"] == expected` is lane == lane, and the exact-cap case skips its positive check. The lane detail is plain `bounded_detail(message)`, so `lane_detail == expected` holds for every case | File: tests/drivers/test_codex_detail_safety.py:281 | Task: 3
[BOB] ⚪ The scalar scan runs a Python generator per character, and it runs up to 5 times per frame (preflight, `_payload`, `sanitize_json` inside `_payload`, and both again in `observation_record` on write) over frames up to 1 MiB. A precompiled `re.compile("[\ud800-\udfff]").search` runs in C, and `_payload` can call `_sanitize_json` after its own scan | File: src/ovcaq/events/model.py:83 | Task: 1
[BOB] 🟡 The same strip-after-redact bug exists in the TUI. `display_text` drops Cc/Cf characters from already-sanitized activity and tool text without redacting again, so a stored `sk-abc\x00defghijklmnopqrstuvwxyz0123` shows on screen as the rebuilt token | File: src/ovcaq/tui/model.py:136 | Task: general
[BOB] ⚪ `has_invalid_unicode_scalar` never ends on a cyclic container. The old recursive copy raised RecursionError, and a cycle under a sensitive key used to return `[REDACTED]` | File: src/ovcaq/events/model.py:77 | Task: 1
[BOB] ⚪ The raw-first tests live in `test_unicode_frames.py`. The PRD's task 2 acceptance command (`test_unicode_safety.py tests/events/test_tail.py`) never runs them | File: tests/events/test_unicode_frames.py:1 | Task: 2
[BOB] ⚪ Cannot statically verify: focused and full suites pass at the review HEAD. The test gate was reused from 0961e40, and HEAD 4c84d4d adds chore commits on top | File: N/A | Task: general

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: fail
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

FIX:
- Word-boundary redaction regression in strip-first order — src/ovcaq/drivers/codex_events.py:64 — redact before and after removing controls: `return sanitize_text(_CONTROLS.sub("", sanitize_text(detail)))[:4096]`. The cap reproducer and split cases still pass. Add SPLIT_DETAILS rows `"Before x\x00" + TOKEN + " After"` → `"Before x[REDACTED] After"` and `"auth\x00Bearer " + "a"*26` → `"authBearer [REDACTED]"`. This needs the design's verbatim `bounded_detail` contract amended.
- Preflight RecursionError delegation untested — tests/events/test_unicode_frames.py:267 — add a frame `'{"type":"thread.started","thread_id":"t","x":' + "["*100000 + '"\\ud800"' + "]"*100000 + "}"` (about 200 KB, under the frame cap). Assert its observations equal `native_unicode_driver().decode(frame)` (reason "Malformed or unsupported Codex record") and that `unicode_adapter_state` is unchanged.
- Nested try in `_complete` — src/ovcaq/events/tail.py:116 — move the `json.loads` try/except and the `has_invalid_unicode_scalar` branch out of the outer try, leaving only the `tuple(self._driver.decode(frame))` call under `except Exception`.
- Duplicated completion test tables — tests/events/test_unicode_safety.py:314 — define the `additions` table once at module level (lines 314 and 334), or merge both tests with `@pytest.mark.parametrize("path", ["construct", "decode"])`.
- Lane test self-comparison — tests/drivers/test_codex_detail_safety.py:281 — replace the `if detail != CAP_REPRODUCER` guard with `assert lane_detail == expected` and pass `expected` to `assert_safe_details`.
- Slow, repeated scalar scans — src/ovcaq/events/model.py:83 — use a module `_SURROGATE = re.compile("[\ud800-\udfff]")` with `_SURROGATE.search(current)`, and call `_sanitize_json(payload)` at src/ovcaq/events/model.py:252 since `_payload` already scanned.
VERIFY:
- Suites pass at review HEAD 4c84d4d — run `env UV_CACHE_DIR=/private/tmp/ovcaq-uv-cache mise exec -- uv run pytest -q --tb=line tests/events/test_unicode_safety.py tests/events/test_unicode_frames.py tests/events/test_tail.py tests/drivers/test_codex_detail_safety.py tests/drivers/test_codex_decode_terminals.py tests/runtime/test_unicode_continuity.py` and confirm exit 0 with 0 skipped.
KNOWN:
- TUI `display_text` strip-after-redact — the PRD's Risks section rules out activity-UI changes ("those have separate dispositions"). Needs a follow-up PRD to redact again after dropping controls.
- Cyclic-container hang in `has_invalid_unicode_scalar` — the contract scopes the scan to acyclic JSON-like values, and every production payload comes from parsed JSON. Adding a guard would protect against a state that cannot occur, and both design reviews recorded it as a non-blocker.
- Raw-first tests outside the PRD-named file — the coordinator approved the split to keep `test_unicode_safety.py` under 800 lines (it would be 821). The full pytest gate runs them, and the PRD may not be edited.

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass


Verdict: 18 findings
Tests: 6884 passed, 0 failed, 0 skipped (suite run this cycle at 4c84d4dbfca6b66226c656b7ae9006085ddd9ddc; approved retry)
