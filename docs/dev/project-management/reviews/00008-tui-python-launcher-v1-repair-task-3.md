# PRD 00008 recovery task 3

Textual polls now run outside the UI event loop with one in-flight observation. Detach remains responsive, and teardown drains the worker before observer close or plain fallback. Active duration uses the selected registry start. Terminal duration uses attested batch completion, otherwise the latest selected-run metric end; missing end evidence stays unknown.

Base: `575e010531106664a710506cd2e272f9d87424a1`. Test commits: `959ce95a8df3f62e2e62569a968883d05090a6d0`, then `e867f78` for the corrected terminal oracle. Implementation: `090604be106a5c171796b2afb661df08c3d1ac28`; terminal correction: `a724f3017f5396f5ba2e857595a1b8dd05426d08`; style correction: `019949ad8f49dd73f645662ee658fa5aec429dda`.

## Dispatch and coverage

All native task agents used logical opus / actual OpenAI `gpt-6-astra`. The Gemini wrapper's unmodified nesting guard refused the task probe (exit 3); the source-authorized native fallback was used. The initial micro trial exceeded its ceiling at 34 net lines and was reverted before the full pipeline.

Tess dispatches: `cac15e0c`, `c01acc19`, `a34c7304`, `55bd0761`. The four-dispatch budget is exhausted. Initial terminal fixtures were corrected to use a real terminated child. The third dispatch stopped before edits after comparing a 107,897-byte read audit with the context limit. The coordinator preserved that report, diagnosed the byte/token mismatch through `debug-stuck-agent`, and used the fourth dispatch in an isolated context without increasing any cap. Evidence: `docs/dev/tmp/r3-budget-recovery.md` and `r3-tess-terminal-report.md`. The final test-author pass corrected the late-poll oracle and added selected/foreign/missing metric cases. Its initial malformed metric fixtures were corrected before acceptance. Computed tautology and manual behavior-name/output/edge-case/non-tautology checks passed. No active/UI assertions were weakened.

Devon dispatch `5225455d` tried three mutations; none passed all supplied tests. Shutdown scaffold failures prevented isolating its integer-duration shortcut, so this is limited negative evidence, not proof of comprehensive coverage. The exact original implementation was restored and canonical tests stayed unchanged. Devon was not repeated after the terminal-contract clarification. Full evidence remains in `docs/dev/tmp/r3-devon-report.md`.

Ivan dispatches: `4d03d20b` (initial implementation), `f0d48e6f` (single MEDIUM repair), `48d9a96e` (single style fix). Each reported no assumptions. The style fix extracted duration calculation solely to resolve the computed 58-line `_project` violation. Canonical test files remained byte-identical to their latest test commit throughout implementation.

## Verification

- Original main-session red: 13 failed, 2 passed; original implementation green: 15 passed.
- Corrected terminal main-session red: 4 duration assertion failures, 14 passed; no fixture errors.
- Final committed HEAD `019949ad8f49dd73f645662ee658fa5aec429dda`: `uv run pytest -q --tb=line tests/tui/test_model_elapsed_duration.py tests/tui/test_app_poll_responsiveness.py` exited 0, **18 passed, 2 warnings in 4.86s**. Warnings concern existing temporary-directory cleanup. Exact approved subprocess/filesystem access was used.
- Original focused help/detach latency measurements while polling was blocked: q 0.070668 s, Ctrl-C 0.049242 s, Ctrl-D 0.049264 s. These measurements precede the duration-only correction.
- Self-deslop: `skipped:trivial` (latest behavior commit 13 net lines / 2 files; style commit 5 net lines / 1 file). Reflow checks clean. Style: fixed by `019949ad8f49dd73f645662ee658fa5aec429dda`; split hygiene clean.

Full project verification remains deferred until all build tasks complete. Coverage limitations: shutdown relies on a finite in-flight observation; a failure before normal unmount is not directly exercised. The state-unavailable terminal-duration clearing path was inspected but has no new direct case. The later fallback task and fresh completion-review session must retain those caveats.

## External task review

Pat uses tool-free Anthropic `claude-sonnet-5-5` (transcript-confirmed), session `e8e7ffeb-b485-4b33-8a3d-df87c1f0df8b`, through the installed guarded wrapper with approved network access. Initial dispatch `37c549b8`; delta dispatch `25fdffc2`. Both review outputs are preserved below after parser validation.

The first MEDIUM was confirmed: a live selection may finish before a late poll, inflating duration. Its direct-attach-to-dead-entry example is unreachable, but that does not invalidate the defect. The original fake-clock test did not observe the real end moment; it pinned the defect. The task contract was clarified through the state CLI before the test correction. The first executor LOW remains for later fallback work/review; the helper LOW was incidentally addressed by the mandated style extraction. Neither was promoted into an extra review cycle.

## Raw review cycle 1

CLOSURE | resolved | F03 "The Textual timer executes registry snapshots, repeated `ps` probes, and filesystem reads synchronously on the UI thread" | `_poll` now submits `self._observer.poll` to a one-worker `ThreadPoolExecutor`, only collects the result once `pending.done()`, and `on_unmount` drains the worker. The blocked-poll test presses help, `q`, `ctrl+c` and `ctrl+d` while a poll is held, and each gets a response.

CLOSURE | resolved | F04 "Active duration is calculated by summing finalized session and capability wall times instead of elapsed time from `FleetRun.started_at`" | The `walls` sum is removed. `_project` computes `datetime.now(UTC) - fromisoformat(self._run.started_at)`, and invalid, naive or future starts give `None`. The test confirms the result does not depend on the metric totals.

MEDIUM | src/ovcaq/tui/model.py:366 | The duration is always `now - started_at`, never an end time. If the first poll of an ended run comes late, for example `attach` on a run that finished an hour ago, the frozen terminal duration includes all the idle time. The contract asks for a "stable terminal duration", and the test only passes because it sets the clock to the exact end moment. | For an ended run, take the end timestamp from durable evidence (batch finished time in state, or the last metric `finished_at`) and fall back to `None` if it is absent. Add a test where the clock is well past the end.

LOW | src/ovcaq/tui/app.py:314 | The executor is only drained in `on_unmount`. If Textual fails before mount completes or without unmounting, the worker could still be polling when `attach` falls back to `run_plain` or closes the observer. The tests only cover the failure-inside-`run_test` path. | Also call `self._executor.shutdown(wait=True)` from `attach`'s fallback and close path (a `finally`), or track the future there.

LOW | src/ovcaq/tui/model.py:366 | The `try`/`except` clock block is inline in `_project`, which now has two jobs. | Extract an `_elapsed_seconds(started_at)` helper that returns `float | None`.


## Raw review cycle 2

CLOSURE | resolved | MEDIUM model.py:366 "The duration is always `now - started_at`, never an end time... a late first poll inflates the frozen terminal duration" | In the new `_duration`, an ended run takes its end from `state["batch"]["completed_at"]`, or else from the latest selected-run `finished_at`. If neither exists, `max()` of an empty sequence raises `ValueError`, which is caught and returns `None`. The late clock is never used as the end. Tests poll 2 hours after completion and after a paused end, and expect the real end or `None`.

LOW | src/ovcaq/tui/model.py:366 | One selected-run metric row with an unparseable `finished_at` raises inside the `max()` generator, so the whole duration becomes `None` even when other rows are valid. The contract says "latest valid" metric end. | Skip rows whose `finished_at` fails to parse, and return `None` only if none parse. This may be unreachable if `observe_metrics` already validates timestamps, so confirm that before changing anything.


## Final disposition

MEDIUM retry fixed. The delta LOW is refuted by the public read path: observe_metrics passes every row through metric_from_record, which calls _metric_payload and validate_timestamp before returning a SessionMetric. An unparseable finished_at cannot reach the max generator. No extra repair or third review was dispatched. The first review executor LOW remains documented above.
