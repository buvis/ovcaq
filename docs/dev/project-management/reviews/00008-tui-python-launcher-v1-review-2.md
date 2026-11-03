---
prd: docs/dev/project-management/prds/wip/00008-tui-python-launcher-v1.md
review: 2
date: 2026-10-04
head_sha: 2eb175512b7fd0f79e7cb32b9a6581d2d86e802c
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00008-c2-e454253ecd58445aae6fbf7d78969e75.txt.receipt.json
---

# Review: 00008-tui-python-launcher-v1

Diff range: `5544b1fc9c27838f8941c2266867a6c34ef10902..2eb175512b7fd0f79e7cb32b9a6581d2d86e802c`

codex_rung_guard: fired (12 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude

Host substitution: external Claude Opus Bob supplies the authorized independent non-Codex doubt voice. Native Eve/Fable is unavailable; no Eve dispatch or Codex reviewer thread is claimed. Alice and Blake ran as isolated native Codex gpt-6.1-sol/high with no parent history. These are different lenses on one native model; Claude Bob is the independent provider voice. Bob raw initialization records claude-opus-5-5; his receipt records requested alias opus. Every dispatched agent and process completed in this session.

Carl: unavailable (helper exit 3: refusing nested dispatch, already inside a CLI agent; no backend ran). Launcher guards were preserved. This is a cycle-local failure, not a permanent-availability latch.

Pack: unavailable after the permitted retry (engram: repository not registered in gita).

Scope: all 39 changed product/source/test/operator-documentation paths were reviewed. The full gathered scratch diff retains workflow/log records; the supplied complete product diff omits only docs/dev/project-management records. Alice received the full PRD, design and task context. Blake received the PRD and complete blind rubric, without diff, file list, plan, design, history or sibling findings. Bob received a separate PRD-only requirements context without design or implementation plan; current mechanical/verification evidence, scoped diff, prior findings and settled decisions were separate evidence. UUID-qualified Bob prompt/context/output paths were verified fresh before dispatch.

## Result and coverage

All 11 raw issue lines map exactly once to 11 consolidated findings: 0 critical, 1 high, 7 medium and 3 low. Consolidation used the required script without manual merges or dismissals. Current mechanical test checks contribute no issue lines; the prior verification queue is empty. Bob's six residual findings appear in FIX exactly once, with empty VERIFY/KNOWN; all five raw D verdicts pass. The checks-2 queue is empty. Raw R/B/D verdicts remain unchanged below.

The full suite at this reviewed HEAD passed 4579 tests, with no failures or skips. uv sync, Ruff, formatting, mypy and uv build passed. Fail-first replay reached its 600-second bound without a verdict; its temporary worktree was removed. This is retained verification evidence, not a pass. The prior settled replay limitation remains visible.

## Consolidated findings

| Consensus | Severity | Issue | File | Task | Found By |
|-----------|----------|-------|------|------|----------|
| [1/3] | 🟠 | If the selected supervisor completes during evidence reads, exit revalidation discards even valid selected-owner final state and sets ended=True; ProjectObserver permanently caches unknown, so both viewers return failed/1 for normal completion. Reobserve the attested final selection before caching a terminal result. | src/ovcaq/runtime/_run_observation.py:141 | 2 | ALICE |
| [1/3] | 🟡 | Active observation no longer checks the exact live registry entry; removing or replacing that entry while metadata, PID and run lock remain valid still exposes state and telemetry as running. Restore shared registry validation before and after evidence reads. | src/ovcaq/runtime/_run_observation.py:116 | 2 | ALICE |
| [1/3] | 🟡 | Three copies of the byte-at-a-time subprocess barrier reader appear in test_control_commit_identity, test_guarded_run_mutation and test_launcher_outcomes; extract one integration helper preserving their deadlines and EOF checks. | tests/integration/test_control_commit_identity.py:99 | general | ALICE |
| [1/3] | 🟡 | Raw fallback shows only a telemetry label: RAW_UNKNOWN previews are discarded, raw.jsonl is never tailed for presentation, and neither viewer displays raw output when normalization is unavailable. | src/ovcaq/tui/model.py:539 | P06-T07 | BLAKE |
| [1/3] | 🟡 | Capability failure and retry guidance are inaccessible through keyboard navigation at 80×24: the stacked Static frame overflows, but Tab, Down, PageDown and End leave scroll_y at zero; an in-memory Textual probe exposed the retry command only after programmatic scrolling. | src/ovcaq/tui/app.py:345 | P06-T04 | BLAKE |
| [1/3] | 🟡 | F20 is only partly fixed: a supervisor that exits 0 with a PAUSE decision is reported as a failed launch. This happens on an interactive `ovcaq run` while a pause request is pending, and every confirmed `s` stop leaves one (`_record_stop` sets `pause_requested`). `_completed_launch` accepts only batch status `completed`, so `_launch_failure` prints "supervisor pid N exited with code 0: {raw SessionMetadata JSON}" and the command exits nonzero. If the parent wins the handshake race instead, `cli.py:513` re-raises `MissingRunError`. Both outcomes contradict the pinned rule that paused maps to detached/0. | src/ovcaq/supervisor_cli.py:396 | 7 | BOB |
| [1/3] | 🟡 | `ProjectObserver.__init__` builds a `JsonlFollower` on the runtime `events.jsonl` that is never read. `_apply` always replaces it before the first read, because `_session_id` starts as None. It also points readers at the file F01 proved wrong. | src/ovcaq/tui/model.py:291 | 11 | BOB |
| [1/3] | 🟡 | The per-session usage machinery is now dead. The observer follows one session's file, drops records from other run/session pairs (line 536), and calls `_clear()` on every session change. So `self._usage` never holds more than one entry, and the pop/reinsert step plus the `MAX_USAGE_SESSIONS` eviction can never run. No test references the cap. | src/ovcaq/tui/model.py:548 | 11 | BOB |
| [1/3] | ⚪ | `_run` reads the private `supervisor._metadata` from another module to build the completion proof. | src/ovcaq/supervisor_cli.py:177 | 7 | BOB |
| [1/3] | ⚪ | `except _STATE_ERRORS: pass` silently drops a failed final-state read or attestation write. The viewer then reports "final state does not belong to the selected run", which blames an I/O fault on an ownership mismatch. Impact is limited because it fails closed, and the viewer reports its own read error when the state is unreadable. | src/ovcaq/runtime/supervisor.py:180 | 2 | BOB |
| [1/3] | ⚪ | Dropping `or None` from `next_phase` makes an empty committed `next_phase` render blank (`phase: build -> `) instead of a label. The change was made to satisfy a test fixture, not a requirement. | src/ovcaq/tui/model.py:396 | 12 | BOB |

## Decision evidence

Cycle 2 equals cap 2. The unresolved HIGH completion race prevents clean convergence. Under the unattended review gate's cap-out branch, all 11 unresolved findings are recorded as cap-overflow deferrals in state.deferred_decisions and the settled-decisions ledger. There are no CRITICAL findings requiring custody/stall. No repair task is created or started, no cycle increment or cap increase occurs, and all 14 completed tasks remain intact. The next fresh finalize session owns deferral migration and report reconciliation. This handoff is cap-deferred, not a clean review pass.

Durable evidence: `docs/dev/project-management/reviews/00008-tui-python-launcher-v1-cycle-2-evidence` contains raw outputs, full rendered prompts, Claude raw JSONL/stderr/receipt, current contexts/product diff, per-command verification logs, computed checks and dispatch provenance. The finding-to-source map is findings.json. Previous failed attempt artifacts are retained unchanged.

## Alice

[ALICE] 🟠 If the selected supervisor completes during evidence reads, exit revalidation discards even valid selected-owner final state and sets ended=True; ProjectObserver permanently caches unknown, so both viewers return failed/1 for normal completion. Reobserve the attested final selection before caching a terminal result. | File: src/ovcaq/runtime/_run_observation.py:141 | Task: 2
[ALICE] 🟡 Active observation no longer checks the exact live registry entry; removing or replacing that entry while metadata, PID and run lock remain valid still exposes state and telemetry as running. Restore shared registry validation before and after evidence reads. | File: src/ovcaq/runtime/_run_observation.py:116 | Task: 2
[ALICE] 🟡 Three copies of the byte-at-a-time subprocess barrier reader appear in test_control_commit_identity, test_guarded_run_mutation and test_launcher_outcomes; extract one integration helper preserving their deadlines and EOF checks. | File: tests/integration/test_control_commit_identity.py:99 | Task: general
R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: fail


## Blake

[BLAKE] 🟡 Raw fallback shows only a telemetry label: RAW_UNKNOWN previews are discarded, raw.jsonl is never tailed for presentation, and neither viewer displays raw output when normalization is unavailable. | File: src/ovcaq/tui/model.py:539 | Task: P06-T07
[BLAKE] 🟡 Capability failure and retry guidance are inaccessible through keyboard navigation at 80×24: the stacked Static frame overflows, but Tab, Down, PageDown and End leave scroll_y at zero; an in-memory Textual probe exposed the retry command only after programmatic scrolling. | File: src/ovcaq/tui/app.py:345 | Task: P06-T04
B1: fail
B2: pass
B3: pass
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
B15: fail
B16: fail
B17: pass
B18: pass
B19: pass


## Bob

**Incremental review, PRD 00008 cycle 2 (Bob, static only)**

**Prior findings**
- **Resolved in code:** F01, F02, F03, F04, F05, F06, F08, F09, F10, F11, F12, F13, F15, F16, F17, F18, F19, F21, F22, F23, F24, F25, F26, F27, F28, F32, F33, F34, F35, F36.
- **Only partly resolved:** F20. Quick completion is now recognized, but a quick pause exit is not. See finding 1.
- **Settled, not re-raised:** F07, F29, F30, F31 and F39 were discarded. F14, F37 and F38 stay deferred.
- **Hazards checked and ruled out:**
  - Textual's App uses a private `_watch_theme`, so the new `watch_theme` does not shadow it.
  - `FleetRegistry.snapshot()` takes no lock, so `guard_mutation` cannot deadlock on it.
  - Credential redaction cannot match the metadata JSON keys, so the completion proof is not corrupted.
  - The theme path now resolves the same way as `config.py`, including an empty `XDG_CONFIG_HOME`.

**New findings**

[BOB] 🟡 F20 is only partly fixed: a supervisor that exits 0 with a PAUSE decision is reported as a failed launch. This happens on an interactive `ovcaq run` while a pause request is pending, and every confirmed `s` stop leaves one (`_record_stop` sets `pause_requested`). `_completed_launch` accepts only batch status `completed`, so `_launch_failure` prints "supervisor pid N exited with code 0: {raw SessionMetadata JSON}" and the command exits nonzero. If the parent wins the handshake race instead, `cli.py:513` re-raises `MissingRunError`. Both outcomes contradict the pinned rule that paused maps to detached/0. | File: src/ovcaq/supervisor_cli.py:396 | Task: 7
[BOB] 🟡 `ProjectObserver.__init__` builds a `JsonlFollower` on the runtime `events.jsonl` that is never read. `_apply` always replaces it before the first read, because `_session_id` starts as None. It also points readers at the file F01 proved wrong. | File: src/ovcaq/tui/model.py:291 | Task: 11
[BOB] 🟡 The per-session usage machinery is now dead. The observer follows one session's file, drops records from other run/session pairs (line 536), and calls `_clear()` on every session change. So `self._usage` never holds more than one entry, and the pop/reinsert step plus the `MAX_USAGE_SESSIONS` eviction can never run. No test references the cap. | File: src/ovcaq/tui/model.py:548 | Task: 11
[BOB] ⚪ `_run` reads the private `supervisor._metadata` from another module to build the completion proof. | File: src/ovcaq/supervisor_cli.py:177 | Task: 7
[BOB] ⚪ `except _STATE_ERRORS: pass` silently drops a failed final-state read or attestation write. The viewer then reports "final state does not belong to the selected run", which blames an I/O fault on an ownership mismatch. Impact is limited because it fails closed, and the viewer reports its own read error when the state is unreadable. | File: src/ovcaq/runtime/supervisor.py:180 | Task: 2
[BOB] ⚪ Dropping `or None` from `next_phase` makes an empty committed `next_phase` render blank (`phase: build -> `) instead of a label. The change was made to satisfy a test fixture, not a requirement. | File: src/ovcaq/tui/model.py:396 | Task: 12

FIX:
- Quick PAUSE exit reported as a launch failure with raw JSON — src/ovcaq/supervisor_cli.py:396 — Accept any attested terminal state that the viewer maps to exit 0, not just `completed`. Concretely: check `pause_requested` or a paused phase alongside `completed` in `completed_run`. Return `LaunchedSupervisor(None)` with a "paused" notice, and add a regression test that calls `request_pause` before an interactive `run`.
- Dead `events.jsonl` follower — src/ovcaq/tui/model.py:291 — Start with `self._follower: JsonlFollower[Observation] | None = None` and make `close()` skip None.
- Dead multi-session usage cap — src/ovcaq/tui/model.py:548 — Replace `self._usage` with a single `Mapping | None` for the latest live usage, and delete `MAX_USAGE_SESSIONS` and the eviction branch.
- Private `_metadata` read across modules — src/ovcaq/supervisor_cli.py:177 — Expose a read-only `Supervisor.metadata` property, or carry the metadata in `SupervisorOutcome`.
- Swallowed terminal-attestation failure gives a misleading message — src/ovcaq/runtime/supervisor.py:180 — In `_verify_terminal_state`, report a record with a null `run_id` as "selected run published no final-state attestation", and add a comment at the `pass` that names the fail-closed intent.
- Blank `next_phase` render — src/ovcaq/tui/model.py:396 — In `workflow_panel`, render `""` as `none` so the panel distinguishes "no next phase" from "unknown".
VERIFY:
- (none)
KNOWN:
- (none)

R1: pass
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

**Not done:** I could not run the fail-first replay. It timed out again at 600 s, and the earlier cycle already deferred that (F14).

**Next:** Coordinator: send the three 🟡 FIX items to rework; the quick-pause launcher fix (Task 7) comes first.

Verdict: 11 findings
Tests: 4579 passed, 0 failed, 0 skipped (suite run this cycle at 2eb175512b7fd0f79e7cb32b9a6581d2d86e802c)
