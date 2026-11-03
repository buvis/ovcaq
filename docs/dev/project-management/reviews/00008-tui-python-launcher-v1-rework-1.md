# PRD 00008 cycle 1 rework evidence

Current work: task 11 reopened; task 12 aborted at its review-repair prompt budget; tasks 13–20 remain. Counts are 10/20 completed. The full phase suite and fresh cycle-2 review have not run. Canonical recovery and the full unfinished-task snapshot are in `00008-tui-python-launcher-v1-recovery-1.md`.

Follow-up required before phase completion: while task 12's tests were being authored, coordinator source inspection found that the real edge driver constructs an independent run ID (`drivers/edge.py`, `build_driver`) and its decoder retains the provider's native session ID (`drivers/claude.py`, `decode`/observation construction). `RawFirstDecoder` publishes those identities unchanged, whereas task 11 now filters against supervisor-owned run/session identities. The task-11 generic integration driver supplied canonical IDs and did not expose this mismatch. Finish the active task-12 pipeline, then repair task 11 sequentially with a regression covering real adapter output and canonical writer identity. Do not claim F01/F19 fully closed or advance the phase with this gap unresolved. Provider-native raw evidence must survive any normalization fix; do not weaken observer identity filtering.

## Task 11 — live telemetry and truthful evidence

Base: `f3b969131e393e43bf9a96023a87d3c3a6246d82`.
Test commits: `f310461882b92e466dd1e1739fc75e7ff20615dc`, `cbf86365a61bb104fb718d4d9e6719779fae555f`.
Implementation: `4ba3ef91cf35a517dec5e304b9921cc5a8a3243d`.

- Tess, Devon, Ivan and fresh self-deslop: isolated native Codex `gpt-6-astra`, logical `opus`; no claim of native model diversity.
- Dispatch IDs: Tess `489aad70`; Devon `6565392a`; Tess strengthening `a7852f65`; Ivan `aefa11d4`; preservation repair `8c2c6194`; self-deslop `d0f787ef`; Pat `7272fbc9`.
- Gemini helper declined its read-only availability probe with exit 3, `refusing nested dispatch (already inside a CLI agent)`. Its guard was preserved; the documented native fallback implemented the task. Raw probe receipt: `docs/dev/tmp/gemini-probe-11.log.json`.
- Pat: external Claude, observed model `claude-sonnet-5-5`, session `d6f65d5f-7924-445b-be93-f91d3c1d6391`. The installed Sonnet wrapper used `-t ''`, default permissions, approved network access, and no nesting-guard removal. Raw output: `docs/dev/tmp/review-task-11.md`; launcher receipt: `docs/dev/tmp/pat-11-run.log.json`.
- Devon demonstrated eight wrong implementations passing the initial tests. One Tess strengthening round rejected all eight. Reports: `docs/dev/tmp/devon-11-report.md`, `docs/dev/tmp/tess-11-strengthen-report.md`.
- Main red check: 18 expected failures, 2 passes. Main post-commit verification: `uv run pytest -q --tb=line tests/integration/test_supervisor_live_telemetry.py tests/tui/test_model_live_evidence.py` — exit 0, **20 passed, 2 warnings in 2.06s**. Bounded-runner receipt: `docs/dev/tmp/task-11-green.log.json`. Warnings concern pre-existing pytest temporary-directory cleanup.
- Existing evidence-presence preservation test plus the new tests: implementor exit 0, **21 passed, 2 warnings in 2.13s**. Receipt: `docs/dev/tmp/ivan-11-preserve-tests.log.json`.
- Main test-quality review and tautology checker passed. Reflow clean. Self-deslop `noop`.
- **11: style_gate: clean, split_hygiene: clean.**
- Foreign product dirt: none. The active workflow store and session logs remain for the store commit.

## Pat task 11 raw verdicts

CLOSURE | resolved | F01 ProjectObserver follows runtime `events.jsonl`, but supervisors write normalized observations only to each session's `normalized.jsonl` | `_apply` now builds the follower on `sessions/<id>/normalized.jsonl` and re-points it when the session id changes. The live-telemetry integration test runs the real supervisor writer against the observer across a rollover.
CLOSURE | resolved | F08 Latest-session cumulative usage is merged into batch totals without forcing `partial=True` | The `partial` argument is now `(metrics is None or metrics.complete) and not live_usage`. Live usage is dropped only once a row has `finished_at`.
CLOSURE | resolved | F09 Valid integer `cost_usd` values are ignored because the projection collects only floats | `_usage_view` now collects `isinstance(value, (int, float))`. The parametrized zero, integer, float and estimated cost test covers it.
CLOSURE | resolved | F10 Telemetry gaps are bounded only within one poll and are not retained | `self._gaps = _bounded_gaps(persistent)` carries gaps across polls and resets them only on a session change. The gap-survival test covers malformed, oversized, replaced and truncated damage.
CLOSURE | resolved | F16 Raw-only crash detection cannot work: mere normalized file existence is treated as successful normalization | `SessionEvidenceStatus.raw_only` is true when raw has bytes and normalized is empty. The model uses it, and the real-supervisor test with a precreated empty normalized file expects `raw-only`.
CLOSURE | resolved | F19 The raw-file degradation path never fires in production because `active_session_id` is the run_id | The supervisor now republishes run metadata with the real `session_id` after creating each session (`replace(self._metadata, session_id=session_id)`). The integration test checks the pending metric's session id against the session directory.
CLOSURE | resolved | F28 The capability view drops the last attempt's `session_id` | `CapabilityView` gains `session_id` and `evidence_path`, and `capability_panel` renders an `evidence:` line. The default-constructor test shows existing callers still work.
CLOSURE | resolved | F32 One backlog condition produces 2 or 3 gaps | The follower's budget-reached "truncated" gap is removed, and the model emits only "event backlog pending" while a backlog exists. "event history incomplete" is added only when there is no backlog. The single-diagnostic test and the follower test cover this.

NO FINDINGS

The retained F08 wording calls the expression the `partial` argument; it is actually the `_usage_view` completeness argument. The live merged-usage test verifies the resulting `partial=True` projection.

## Assumptions

The task-11 section of `docs/dev/project-management/meta/assumptions.md` records the two coordinator-pinned additive field shapes. Tess and Ivan reported none. Prior assumptions remain available for the final phase report and fresh review.

## Task 12 — terminal observations (aborted before review repair)

Base: `4ba3ef91cf35a517dec5e304b9921cc5a8a3243d`.
Test commits: `2c0f306`, `8194eec151c0f5cc77ab4a7eab95b5f11cf342a3`, `cd163af0ce9eb98000b16eb1d15928d37d17462c`.
Implementation: `fe63aabca455a92ae9494af57a290792d68b22ec`.
Style split: `f254d11cea570eeccf2751315b260d33f34b0e3e`.

- The eligible micro attempt exceeded the two-file ceiling and was reverted before tests were authored; `micro_lane: overrun`.
- Tess and Devon: isolated native Codex `gpt-6-astra`, logical `opus`. Tess initial `97f4f076`, quality repair `1d61d7a2`, Devon `72d20448`, adversarial strengthening `a2a5674b`.
- Devon demonstrated eight wrong implementations passing the initial 29 cases. Tess addressed each numbered weakness once; no second Devon dispatch. Reports: `docs/dev/tmp/devon-12-report.md`, `docs/dev/tmp/tess-12-strengthen-report.md`.
- Final test files: `tests/integration/test_observer_terminal_cleanup.py`, `tests/integration/test_observer_terminal_viewers.py`, `tests/tui/test_app_ended_selection.py`.
- Main four-check quality review, computed tautology check, test style and split hygiene passed. Tests retain real supervisor/agent subprocesses and a replacement during final observation.
- Main red check: `uv run pytest -q --tb=line` on those three files, exit 1, **36 failed, 2 warnings in 16.75s**. Expected missing terminal preservation/ended signal and continued polling. Receipt: `docs/dev/tmp/task-12-red.log.json`.
- Gemini availability probe exited 3, `refusing nested dispatch (already inside a CLI agent)`; guard preserved. Receipt: `docs/dev/tmp/gemini-probe-12.log.json`.
- Fresh native Ivan `gpt-6-astra`, logical `opus`, dispatch `c63a434a`; 48,042-byte complete rendered prompt. Full report: `docs/dev/tmp/ivan-12-report.md`.
- Tess's final quality correction (`46e4fb06`) preserved exact attempt-session/diagnostic binding while permitting the established appended execution record in raw evidence. No capability production change was made to satisfy an invented whole-file equality.
- Main post-commit test run: **36 passed, 2 warnings in 12.26s**, exit 0. Receipt: `docs/dev/tmp/task-12-postcommit-green.log.json`.
- Fresh self-deslop (`c2554284`, native `gpt-6-astra`, logical `opus`) returned `noop`.
- Style gate found `session.py` at 856 lines. The single style-only Ivan pass (`6681cf2a`) moved run observation into `_run_observation.py`, preserving public imports. Rebuilt style and split-hygiene checks passed. **style_gate: fixed:f254d11cea570eeccf2751315b260d33f34b0e3e; split_hygiene: clean.**
- Main post-split run: **36 passed, 2 warnings in 12.33s**, exit 0. Receipt: `docs/dev/tmp/task-12-style-green.log.json`.
- Reflow tripwire: `src/ovcaq/tui/model.py:23`; retained for review. The flagged hunks implement projection/identity changes rather than a file-wide formatter pass.
- Pat prompt `ca871ca4` was prepared prematurely before the style repair; it was never dispatched and its row explicitly records that fact. Actual external Claude Sonnet dispatch: `f27f7244`, observed model `claude-sonnet-5-5`, session `fa2262e1-7e0e-4cc4-8b5c-647cc52056fd`, no tools or edit permission, approved network access. Parser exit0; F02 closure resolved, two MEDIUM ownership findings and four LOW notes. Every raw verdict is retained in the recovery snapshot.
- Coordinator source inspection identifies coverage gaps around same-batch replacements, the observer's shared lock competing with launch, and evidence reads after an active-run identity check. These are not declared resolved by the green suite. Details: `docs/dev/tmp/task-12-coordinator-doubts.md`; inspect and resolve confirmed defects in the review/repair flow.
- Confirmed MEDIUM repair prompts measured 51,332 bytes (`620defc4`) and 50,185 after the one permitted context trim (`b0071cb4`). Neither was dispatched. The work skill mandates task abort after the trim still exceeds50,000. Attempt1 records `outcome: aborted`, `cause: subagent_prompt_overrun`, and the completed gates. No Pat delta review ran; no finding is falsely claimed fixed.
- State records the abort/stall and valid `next_phase: build`; canonical `resume-target` returns `replan: clear tasks, re-enter build at planning, write replan-context.md`. Current phase/cycle remain review/1. The obsolete `planning` next_phase spelling in the dispatch reference is rejected by the schema, so the current three-phase vocabulary is retained. No phase-done transition was appropriate for unfinished rework.
