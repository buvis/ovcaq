# PRD 00051 cycle-1 rework evidence

The installed Phase 4 existing-review/unfinished-rework rule selected tasks
6–9. This session resumed Phase 6; it did not repeat cycle 1 or run cycle 2.
The cap remains 2. Fresh full review is still required; no convergence is claimed.

Source review: `docs/dev/project-management/reviews/00051-triage-a-single-valid-codex-record-can-crash-th-v1-review-1.md`.

| Task | Source refs | Implementation and closure evidence |
| --- | --- | --- |
| 6 | R4, R5, R7, R8 | Tests-first commit `5d83125`; production/design/changelog commit `ec7f515`. Independent red check: 48 failed, 49 passed. Final narrow check: 97 passed; worker's two-file check: 431 passed. Pat resolved all four quoted findings, no findings. |
| 7 | R1, R9 | `05d0716`: design acceptance includes the approved frame split; shared completion additions preserve independent construct/decode paths. 1251 focused tests passed. Pat resolved both findings, no findings. |
| 8 | R3 | `6f737ae`: receiver details compare with independent expected values, including the cap case; token assertions inspect actual payloads. 180 tests passed. Pat resolved the quoted finding, no findings. |
| 9 | R11, R12 | `05748db`: protocol names the recognized controls and actual redaction order; runtime changelog wording moves into events. 180 tests passed. Pat resolved both quoted findings; one new LOW remains below. |

The first task-6 implementation revealed a second interaction: an original lone
ESC followed by a token became `ESC[REDACTED]`, which matched newly formed CSI.
Three regression cases failed. Masking only original lone ESC as a removable NUL
before the first sanitizer preserves original control recognition and redaction
markers. The correction and historical recipe are retained in the design.

Per-task artifacts (rendered prompts, output, verification, parser input and
attempt payloads) are archived in `reports/00051-cycle1-rework-artifacts/`.
Pat used the real personal `use-sonnet` wrapper with `--effort high`, no tools,
no permission bypass, and distinct session IDs. The older installed wrapper lacks
the effort flag; the authorized personal wrapper preserves guards and supplies it.
All four processes returned exit 0 and parser-valid closure output.

Task 6: style_gate clean; split_hygiene clean; self_deslop noop.
Task 7: style_gate clean; split_hygiene clean; self_deslop skipped:trivial.
Task 8: style_gate clean; split_hygiene clean; self_deslop skipped:trivial.
Task 9: style_gate clean; split_hygiene skipped:no-tests; self_deslop skipped:trivial.
Tasks 7–9 used the source micro lane: clean named files, at most two noncritical
findings/two files, measured net changes 5, -2 and 2, respectively. Pat was kept.
Tess and Ivan reported `ASSUMPTIONS: none`; no new assumptions were introduced.

## Remaining evidence

Final project gates at implementation HEAD `05748db`: sync, full pytest
(6981 passed, 0 failed, 0 skipped), Ruff check, Ruff format check (232 files),
mypy (61 source files), and sdist/wheel build all exited 0. The full suite ran
once with approved host access for real process/signal/lock/loopback coverage.
The only warnings were pytest cleanup failures for pre-existing temporary
garbage directories; no fixture, binary, global configuration or permission
policy was changed. Initial narrow verification could not open the default uv
cache in the sandbox; subsequent runs used a task cache in `/private/tmp`.
The verification record deliberately names the actual tested HEAD, before later
store-only commits; the fresh review must honor the source SHA-match rule.

verify_check: env UV_CACHE_DIR=/private/tmp/ovcaq-uv-cache mise exec -- uv run pytest -q --tb=line tests/events/test_unicode_safety.py tests/events/test_unicode_frames.py tests/events/test_tail.py tests/drivers/test_codex_detail_safety.py tests/drivers/test_codex_decode_terminals.py tests/runtime/test_unicode_continuity.py -> exit 0 (1480 passed).

State schema and task counts validated (9/9 complete); the existing cycle-1
full review passed the canonical coverage/guard shape gate. This validates the
prior review artifact only and is not a new cycle-2 verdict.

Pat task 9 LOW: the older drivers changelog bullet still says split credentials
"cannot survive normalization" and repeats a broader claim than the narrowed
protocol. Source step 5.7 carries LOW findings to full review, without a retry.
The complete finding and proposed fix remain in the archived Pat output.

R2, R6, R10, R13 and R14 remain settled deferrals. No cycle guards, TUI changes,
custom-driver rollback or arbitrary exception/path surrogate handling landed.
Original PRD 00009 cycle-2 source R7/R2 evidence remains intact; focused/full
verification and the next review establish repair readiness, not task status alone.
PRDs 00052–00054 and held 00010 remain unimplemented by this session.

## Actual implementation provenance

Task 6 Tess and Ivan used logical sonnet, observed OpenAI `gpt-6.1-sol`/medium.
Raw source metadata is preserved byte-for-byte in `autopilot/implementation-logs/`:

- Tess: `rollout-2026-10-10T11-42-47-01a12531-8f04-7a21-94cd-e7d92e06cb40.jsonl`.
- Ivan: `rollout-2026-10-10T11-45-40-01a12534-3394-7210-bd40-03965beb5f45.jsonl`.
- Coordinator/micro implementations: `rollout-2026-10-10T11-41-08-01a12530-0b4b-7bc1-bb9f-cbf937ca0337.jsonl`.

Each source has provider metadata at line 1 and observed model/effort in
`turn_context` at line 8. The native subagent source embeds the parent thread ID
and agent path. Correlate Tess/Ivan with task 6's rendered prompts, dispatch IDs
`c912129e` and `6ccc9e15`, and the two commits above. The coordinator's observed
OpenAI `gpt-6.1-sol`/low is implementation evidence only for its explicit micro
edits for tasks 7–9; its planning/coordination portions are excluded. These
micro attempts retain the source logical sonnet label and launcher identity
`orchestrator`; model and provider fields accurately describe the observed model.
The fresh self-deslop agent `/root/deslop6` returned no changes and is excluded
from contributing implementation models. Pat is read-only review and excluded.

Keep the cycle-1 implementation-models fingerprint/snapshot and receipts intact
through rework. Before cycle 2, regenerate the audit from all contributing prior
and new raw logs, correlate every attempt/test author/repair, and run driver
`review-route`. OpenAI implementation requires the complete Anthropic roster;
do not infer this from the launcher or reuse Pat as a full-review lens.
