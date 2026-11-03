---
prd: docs/dev/project-management/prds/wip/00051-triage-a-single-valid-codex-record-can-crash-th-v1.md
review: 2
date: 2026-10-10
head_sha: b289ae4e8d6e35e74e4e0df0ebc21060652eac65
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  bob: 8f12e22d
---

# Review: 00051-triage-a-single-valid-codex-record-can-crash-th-v1

Diff range: `e4d765c42d1be7b42c27312e8a5f474d61178b52..b289ae4e8d6e35e74e4e0df0ebc21060652eac65`

codex_rung_guard: not fired
provider_review_guard: satisfied
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/alice-output-00051-c2-20261010.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/blake-output-00051-c2-20261010.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00051-c2-20261010.txt.receipt.json

The actual model-provider guard supersedes the legacy launcher guard. Every contributing implementation model is OpenAI. The complete opposite-company Anthropic roster ran through the approved external helper with guards intact, fresh isolated sessions, and immutable successful receipts. Eve did not run. Carl was operator-skipped. All reviewers served `claude-opus-5-5`, requested `opus`, effort `xhigh`; distinct session IDs and raw hashes are in the receipts and reviewer-provenance.json. All raw R/B/D verdicts are retained verbatim below.

## Review Summary

Reviewed all 9 completed tasks and the full PRD work range. **One unanimous HIGH remains unresolved at cap 2/2. This is cap-deferred, not successful repair convergence.** No production change or sweep ran in this review session.

All current-HEAD gates passed: sync, 6981 tests (0 failed/0 skipped), Ruff lint/format (232 files), mypy (61 source files), sdist/wheel build. Two pre-existing pytest temporary-directory cleanup warnings remain. Review-stage initially reused the older store-only-ancestor verification; coordinator ran the full gates once at exact reviewed HEAD and archived all outputs. Blake independently ran the full/focused suites and quality gates. Engram pack failed because the repo is not registered; source fallback sentinel retained. State schema and task counts validate 9/9.

Baseline replay: 1390 cases, 1215 failing against e4d765c, 175 passing preservation cases, zero uncollectable files; no tautological shapes among 32 functions in 4 test files. All three MECH rows are retained below and disposed explicitly. Previous checks-1 entries all have integer exit 0, so none is carried forward.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/3] | 🟠 | The review-1 two-pass `bounded_detail` leaks the tail of a split token. When the control sits after 20 or more body characters, pass 1 redacts the head. Control removal then glues the tail onto `[REDACTED]`, and pass 2 finds no `sk-` or `Bearer` prefix to match. I ran it to confirm: `bounded_detail('Diagnostic sk-abcdefghijklmnopqrstuvwxyz\x1b[0m0123456789ABCDEF')` returns `'Diagnostic [REDACTED]0123456789ABCDEF'`, the real `turn.failed` payload detail is the same, and `'Bearer '+'a'*23+'\x00bbbbbbbb'` returns `'Bearer [REDACTED]bbbbbbbb'`. Task 3's strip-first order redacted these fully, and pre-PRD code leaked the same way. This breaks two PRD rules ("ANSI/NUL splits of ordinary synthetic tokens are redacted", "synthetic credential fragments never enter normalized details") and makes docs/driver-protocol.md:224 claim too much. Every split test cuts at `token[:6]`, so no test catches it. Fix: before control removal, absorb token characters stuck to a marker across recognized controls with `re.sub(rf"\[REDACTED\](?:{controls})+[A-Za-z0-9_.-]+", "[REDACTED]", sanitize_text(protected))`. I probed this on both leaks plus `x\x00sk-…`, the OSC case and the cap reproducer, and all came out fully redacted (I did not run the suite with it). Also add SPLIT_DETAILS cases that split after 20 or more body characters, for both bare and Bearer tokens | src/ovcaq/drivers/codex_events.py:66 | 6 | ALICE, BLAKE, BOB |
| R2 | [3/3] | 🟡 | Unreleased Fixed now has two `**drivers**` entries for one unreleased fix, and they give conflicting orders. Line 43 says redact both before and after control removal. Line 45 says remove controls before redacting, and its claim "so split credentials cannot survive normalization" is false given the finding above. Line 44 ("speed up surrogate detection") describes a tweak to unreleased code, so users see no change from the last release. Simpler: merge lines 43 and 45 into one drivers entry that states what actually shipped, and drop line 44 | CHANGELOG.md:43 | 6 | ALICE, BLAKE, BOB |
| R3 | [1/3] | 🟡 | The raw-first R7 regressions (byte-exact raw, gap digest and preview, unchanged adapter state, later healthy terminal) live in a file the PRD doesn't list, tests/events/test_unicode_frames.py. The task-2 acceptance command `pytest tests/events/test_unicode_safety.py tests/events/test_tail.py` runs none of them, because test_unicode_safety.py only tests the shared models. That acceptance therefore passes without proving its claims. | tests/events/test_unicode_frames.py:172 | 2 | BLAKE |
| R4 | [1/3] | ⚪ | The fail-first replay count for test_codex_detail_safety.py does not match a static count. By my trace, at e4d765c the 48 new `boundary-*` cases pass on purpose (they guard behavior the old code already had). All `inside-*`, `exact-cap`, `ansi-split`, `nul-split`, `alternate-*-ansi/nul` and rate-limit cases should fail. That predicts about 96 passing at base, but the replay reports 143 (and its own line says "1 + 137 more" = 138) | tests/drivers/test_codex_detail_safety.py | general | BOB |
| R5 | [1/3] | 🟡 | 143 touched test(s) pass against the pre-change code: test_bounded_detail_redacts_control_boundaries_and_reconstructed_credentials +137 more | tests/drivers/test_codex_detail_safety.py | general | mech-check |
| R6 | [1/3] | 🟡 | 6 touched test(s) pass against the pre-change code: test_valid_escaped_pair_remains_a_native_startup_record, test_malformed_and_non_json_frames_keep_native_delegation, test_deep_json_recursion_preserves_native_gap_and_durable_evidence, test_real_writer_failures_propagate_from_unsafe_native_frames | tests/events/test_unicode_frames.py | general | mech-check |
| R7 | [1/3] | 🟡 | 26 touched test(s) pass against the pre-change code: test_usage_and_completion_preserve_valid_unicode_scalars +20 more | tests/events/test_unicode_safety.py | general | mech-check |

### Auto-dismissed (ledger)

- [BLAKE] ⚪ `has_invalid_unicode_scalar` walks containers with an unbounded worklist and no cycle guard. A self-referential payload passed to `sanitize_json` or `Observation` now loops forever (confirmed: killed by a 3 s alarm, exit 142). The old recursive sanitizer raised RecursionError. Input from `json.loads` can't contain cycles, so only direct programmatic calls can hit this. | File: src/ovcaq/events/model.py:80 — Settled limitation: the reviewed helper contract is explicitly acyclic JSON-like containers; native json.loads cannot create cycles. Preserve the witnessed hang; no cycle-guard scope expansion.


## Decision Gate

The installed loop-mode cap branch runs before repair dispatch. R1–R3 are retained as cap-overflow deferrals; no cap increase, tail sweep, or cycle 3. R4 contradicts executed computed facts; R5–R7 are passing preservation controls, not independent new defects. Every dismissal/deferral is mirrored in the settled ledger.

| Ref | Disposition | Reason |
|---|---|---|
| R1 | cap-overflow | Cap reached (cycle 2/2) with the late-split credential suffix HIGH unresolved. All three independent reviewers agree; coordinator reproduced bare/CSI and Bearer/NUL suffix leaks. No cap increase or repair authorized by this transition. |
| R2 | cap-overflow | Cap reached with conflicting and overbroad unreleased changelog prose unresolved. Preserve the prior Pat LOW and all three current citations; no tail sweep on cap-out. |
| R3 | cap-overflow | Preserve literal PRD acceptance-command mismatch. Task 7 corrected the design command within its approved scope; source PRD was intentionally unchanged. Full and focused suites include frame tests, but the PRD command still omits them; requirements ambiguity retained rather than claiming literal closure. |
| R4 | discarded | Contradicts computed facts: executed replay reports 143 passing detail cases, not the static estimate of 96. The summary prints six named tests plus 137 more, totaling 143; it never says one plus 137. This is not evidence of an invalid replay. |
| R5 | discarded | Verified preservation checks for original-token boundaries, printable/short details, classifier/reset/OSC/alternate plain behavior. Replay has 1215 repair failures and 175 preservation passes overall, zero uncollectable files. The newly observed late-split regression is independently retained as R1; this computed passing count is not itself a defect. |
| R6 | discarded | Verified preservation checks: valid escaped pairs, malformed/non-JSON and deep-recursion native delegation, and genuine writer failures are required to retain pre-change behavior. Independent surrogate/raw-first repair cases fail at baseline. |
| R7 | discarded | Verified preservation checks for valid Unicode usage/completion; independent invalid-scalar construct/decode regressions fail against baseline. |

Bob VERIFY count discrepancy is not queued: its requested check requires creating a baseline worktree and overlaying HEAD tests before running pytest, not one directly runnable current-tree verification command. Its count premise is also contradicted by the actual replay evidence (R4). No current-cycle queue is created; the raw VERIFY text survives below.

## Historical Source Closure

PRD 00009 cycle-2 R7: scalar rejection, pre-mutation native frame gaps, exact raw evidence, later healthy completion, and fatal publication propagation are covered by the independent fixtures and real subprocess tests; all fresh lenses raised no Unicode continuity defect. Current full/focused suites pass. This establishes R7 closure for this scope.

PRD 00009 cycle-2 R2: exact original cap reproducer remains redacted, but intended split-token/fragment safety is **unresolved**: current R1 exposes a late-split suffix. Original source evidence and cycle-1 R5 are preserved; the two-pass rework fixed original word-boundary regression but introduced the threshold-dependent suffix interaction. Do not report R2 repair success. Cycle-1 R3/R4/R7/R8/R9 implementation/test issues have closure evidence in the rework report; source-PRD command wording and changelog claims persist as current R3/R2. Prior settled cyclic/TUI/custom-driver/exception limitations remain deferred unchanged. PRDs 00052–00054 and held 00010 are unaffected.

## Alice

Complete consensus output follows.

### Anthropic — claude-opus-5-5 / xhigh

Session: `916003ca-85fa-4f2e-9c98-3b6bf6e07d2e`. Immutable receipt: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/alice-output-00051-c2-20261010.txt.receipt.json`.

[ALICE] 🟠 The review-1 two-pass `bounded_detail` leaks the tail of a split token. When the control sits after 20 or more body characters, pass 1 redacts the head. Control removal then glues the tail onto `[REDACTED]`, and pass 2 finds no `sk-` or `Bearer` prefix to match. I ran it to confirm: `bounded_detail('Diagnostic sk-abcdefghijklmnopqrstuvwxyz\x1b[0m0123456789ABCDEF')` returns `'Diagnostic [REDACTED]0123456789ABCDEF'`, the real `turn.failed` payload detail is the same, and `'Bearer '+'a'*23+'\x00bbbbbbbb'` returns `'Bearer [REDACTED]bbbbbbbb'`. Task 3's strip-first order redacted these fully, and pre-PRD code leaked the same way. This breaks two PRD rules ("ANSI/NUL splits of ordinary synthetic tokens are redacted", "synthetic credential fragments never enter normalized details") and makes docs/driver-protocol.md:224 claim too much. Every split test cuts at `token[:6]`, so no test catches it. Fix: before control removal, absorb token characters stuck to a marker across recognized controls with `re.sub(rf"\[REDACTED\](?:{controls})+[A-Za-z0-9_.-]+", "[REDACTED]", sanitize_text(protected))`. I probed this on both leaks plus `x\x00sk-…`, the OSC case and the cap reproducer, and all came out fully redacted (I did not run the suite with it). Also add SPLIT_DETAILS cases that split after 20 or more body characters, for both bare and Bearer tokens | File: src/ovcaq/drivers/codex_events.py:66 | Task: 6
[ALICE] 🟡 Unreleased Fixed now has two `**drivers**` entries for one unreleased fix, and they give conflicting orders. Line 43 says redact both before and after control removal. Line 45 says remove controls before redacting, and its claim "so split credentials cannot survive normalization" is false given the finding above. Line 44 ("speed up surrogate detection") describes a tweak to unreleased code, so users see no change from the last release. Simpler: merge lines 43 and 45 into one drivers entry that states what actually shipped, and drop line 44 | File: CHANGELOG.md:43 | Task: 6

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

## Blake

Complete blind output follows.

### Anthropic — claude-opus-5-5 / xhigh

Session: `338f3828-0af7-4daa-89d8-2756075ffcf1`. Immutable receipt: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/blake-output-00051-c2-20261010.txt.receipt.json`.

[BLAKE] 🟠 `bounded_detail` redacts credentials both before and after it strips controls, but the PRD asks for strip, then redact, then bound. The extra first pass leaks the tail of a control-split token whose head already matches (`sk-` or `Bearer` plus 20 or more characters). Confirmed: `"sk-"+"a"*20+"\x1b[0mSECRETTAIL0123456789"` becomes `[REDACTED]SECRETTAIL0123456789`, and NUL, `\x1f` and Bearer splits do the same. In the PRD order the rebuilt token is redacted in full. The tests only split at offset 6, so they miss this. docs/driver-protocol.md:224 documents the deviation as intended. | File: src/ovcaq/drivers/codex_events.py:66 | Task: 3
[BLAKE] 🟡 The raw-first R7 regressions (byte-exact raw, gap digest and preview, unchanged adapter state, later healthy terminal) live in a file the PRD doesn't list, tests/events/test_unicode_frames.py. The task-2 acceptance command `pytest tests/events/test_unicode_safety.py tests/events/test_tail.py` runs none of them, because test_unicode_safety.py only tests the shared models. That acceptance therefore passes without proving its claims. | File: tests/events/test_unicode_frames.py:172 | Task: 2
[BLAKE] ⚪ CHANGELOG lists the same drivers fix twice with conflicting claims: :45 says controls are removed before redaction, :43 says redaction runs before and after. :44 ("speed up surrogate detection") is a non-user-visible note on an unreleased fix. | File: CHANGELOG.md:43 | Task: 4
[BLAKE] ⚪ `has_invalid_unicode_scalar` walks containers with an unbounded worklist and no cycle guard. A self-referential payload passed to `sanitize_json` or `Observation` now loops forever (confirmed: killed by a 3 s alarm, exit 142). The old recursive sanitizer raised RecursionError. Input from `json.loads` can't contain cycles, so only direct programmatic calls can hit this. | File: src/ovcaq/events/model.py:80 | Task: 1

Evidence (run this session): full suite `6981 passed`; focused PRD files `1480 passed`; `ruff check` "All checks passed!"; `ruff format --check` "232 files already formatted"; `mypy` "no issues found in 61 source files"; `uv build` built the sdist and wheel. Not run: `uv sync --all-groups`. The scope check found nothing extra: source diff since e4d765c touches only model.py, tail.py and codex_events.py, and the PRD's ledger frontmatter is unchanged. Phase mapping for B15–B17 is literal: the PRD's Phase 1 (Core) and Phase 2 (Integration). The PRD has no Phase 3. Its Phase 0 acceptance passes.

B1: fail
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: fail
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: pass
B17: pass
B18: pass
B19: pass

**Status:** Partly done. The audit is complete, but the build fails the PRD on 1 HIGH and 1 MEDIUM finding.
**Not done:** the redaction order in `bounded_detail` at src/ovcaq/drivers/codex_events.py:66 is still open. A fix has to keep the boundary cases tests/drivers/test_codex_detail_safety.py checks (a control between a word and the token) and also redact the tail of the split token.
**Next:** You: send the HIGH redaction finding to the fix cycle along with the Alice and Bob reports.

## Bob

Complete doubt and de-slop output follows.

### Anthropic — claude-opus-5-5 / xhigh

Session: `1663d285-f037-4242-8c79-c8355a3c5a6e`. Immutable receipt: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00051-c2-20261010.txt.receipt.json`.

[BOB] 🟠 `bounded_detail` still leaks part of a token when a control splits it late. If the part of the token before the control already meets the 20-character threshold, the first redaction pass replaces only that head. Removing the control then glues the tail to the marker: `"Before sk-"+"a"*23+"\x00"+"TAILxyz0123456789" + " After"` becomes `Before [REDACTED]TAILxyz0123456789 After`. The same happens with `Bearer`, a CSI sequence, DEL or a lone ESC. The second pass and the Observation sanitizer both miss `[REDACTED]TAIL…`, because they need `\bsk-` or `Bearer\s+`. The cycle-1 strip-first recipe redacted the whole rebuilt token, so the two-pass rework swapped one leak for another. This breaks the PRD exit criterion "synthetic secrets and fragments are absent", and docs/driver-protocol.md:228 and CHANGELOG.md:45 claim more than the code does. Every split test cuts at offset 6, below the threshold, and the `TOKEN`/`sk-abcdefghijkl` absence checks cannot see a tail. I confirmed this by tracing `_LIKELY_SECRET` (`{20,}\b`) by hand; I did not run it | File: src/ovcaq/drivers/codex_events.py:66 | Task: 6
[BOB] ⚪ The Unreleased Fixed section has rework entries stacked on top of each other. CHANGELOG.md:45 says controls are removed before redaction, while CHANGELOG.md:43 says redaction runs both before and after removal, so the two describe the same fix in conflicting ways. CHANGELOG.md:44 records a speed-up of a surrogate check that has not been released yet, which users never see | File: CHANGELOG.md | Task: 9
[BOB] ⚪ The fail-first replay count for test_codex_detail_safety.py does not match a static count. By my trace, at e4d765c the 48 new `boundary-*` cases pass on purpose (they guard behavior the old code already had). All `inside-*`, `exact-cap`, `ansi-split`, `nul-split`, `alternate-*-ansi/nul` and rate-limit cases should fail. That predicts about 96 passing at base, but the replay reports 143 (and its own line says "1 + 137 more" = 138) | File: tests/drivers/test_codex_detail_safety.py | Task: general

FIX:
- A late control split leaves the token's tail unredacted — src/ovcaq/drivers/codex_events.py:66 — before removing controls, extend each first-pass marker over any tail joined to it by controls: `redacted = re.sub(rf"\[REDACTED\](?:(?:{controls})+[A-Za-z0-9_.-]+)+", "[REDACTED]", sanitize_text(protected))`, then remove controls and run the final sanitize as now. Add a CONTROL_DETAILS placement `late` = `"Before " + prefix + token[:26] + control + token[26:] + " After"` expecting `"Before " + prefix + "[REDACTED] After"`. It covers bare and Bearer tokens, through both the helper and native JSONL, and fails on HEAD. Then reword docs/driver-protocol.md:228 to match.
- Stacked and conflicting changelog entries — CHANGELOG.md:43 — merge lines 43 and 45 into one accurate **drivers** entry (redact before and after removing recognized controls, then cap) and drop line 44.

VERIFY:
- Replay count discrepancy — run `env UV_CACHE_DIR=/private/tmp/ovcaq-uv-cache mise exec -- uv run pytest -q -rA tests/drivers/test_codex_detail_safety.py` in an e4d765c worktree with HEAD's test file overlaid. Confirm that every `inside-*`, `exact-cap`, `ansi-split`, `nul-split`, `alternate-*-ansi`, `alternate-*-nul` and rate-limit id FAILS there, and that only `boundary-*`, `bearer`, `osc-controls`, `alternate-*-plain`, printable, short and classification ids pass.

KNOWN:
- (none)

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

Verdict: 7 findings
Tests: 6981 passed, 0 failed, 0 skipped (suite run this cycle at b289ae4)
