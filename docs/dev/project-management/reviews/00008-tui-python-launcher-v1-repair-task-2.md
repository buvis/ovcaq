# PRD 00008 recovery task 2

Exact-owner final evidence now has a private runtime receipt. Observation no longer holds a shared launch lock. Active ownership/session is revalidated after evidence reads; ordinary same-owner state progress remains valid. No state schema change.

Base cfb4c34; implementation 64eb99b; MEDIUM correction 575e010. Native Ivan logical opus, actual OpenAI gpt-6-astra, dispatches b1e3daf8 and b2185534. Gemini wrapper refused nested dispatch (exit 3); guard preserved, native fallback used. Prior Tess four-dispatch cap and Devon pass were retained without additional test edits or dispatches.

Post-commit verification: uv run pytest -q --tb=line tests/integration/test_observer_terminal_cleanup.py tests/integration/test_observer_terminal_viewers.py tests/tui/test_app_ended_selection.py — exit 0, 36 passed, 2 warnings in 15.49s. Warnings concern temporary-directory cleanup. Style clean; split hygiene skipped:no-tests. Fresh full self-deslop c8a0c843: no slop found. Main narrow check required approved real-subprocess access.

Coverage gaps retained: no direct same-batch completed replacement, replacement during active evidence read, or ordinary active state write during a poll. Existing 36 tests do not prove those races. No test was weakened.

External Pat: Anthropic claude-sonnet-5-5, transcript-confirmed, session a364e5b5-86e1-4bf0-9726-29c8e121601e, dispatches d9806c90 and 940dc6a5. Tool-free installed wrapper, approved network, no permission bypass. First MEDIUM confirmed and corrected in the single permitted retry. First LOW about final-publish OSError is refuted by _STATE_ERRORS already containing OSError; initial receipt invalidation must fail closed. Optional-argument API suggestion retained as LOW, no change.

## Raw review cycle 1

CLOSURE | resolved | F02 "Normal supervisor cleanup removes the selected registry entry before the next poll; the observer then returns `unknown`, while both viewers exit only on `completed`" | `_terminal_result` in app.py ends the viewer on `view.ended` (paused/stopped -> detached, otherwise failed). The attested final state survives cleanup through `run-terminal.json`, so ended runs reach that branch.

CLOSURE | resolved | MEDIUM `_run_observation.py:52` "ended branch accepts any final state whose `batch.id` matches... same-batch replacement" | `_verify_terminal_state` requires `run_id`, `pid`, `process_start` and `state_digest` to equal the selected run. A new supervisor's `publish_terminal_evidence(self._paths)` on lock acquisition overwrites the record with nulls, so a replacement's state cannot pass. A same-batch replacement test is still absent from the diff.

CLOSURE | resolved | MEDIUM `registry.py:26` "`observe_unowned_run` holds a shared `flock`... for the whole evidence read" | The `fcntl.flock(LOCK_SH)` call is removed. The lock is now only probed with `run_lock_held` before and after the reads, so nothing holds it across them. I can't see `run_lock_held` in the prompt, so I can't rule out a brief probe collision.

CLOSURE | resolved | C22 "Active selected-run ownership is revalidated before caller evidence reads, leaving a replacement window" | `observe_selected_run` re-runs `_selected_state` after `yield`. It sets `result.state = None` on any change, and `ProjectObserver.poll` checks `selected.state is None` after the `with` block.

MEDIUM | src/ovcaq/runtime/_run_observation.py:133 | The post-read revalidation requires `after.state == result.state` for active runs too. A live supervisor writes state often, so any write during the metric, session or emergency reads discards the whole observation. `poll` then calls `close()` and `_clear()`, which drops accumulated lanes and the follower, so the view flaps to a gap and rebuilds from scratch. The 36 tests pass because none of them writes state during an active evidence read. | For active runs, compare only identity (`run_id`, process, `observation`). Keep the state-equality check for the ended branch, where state is final. Add a test that mutates state mid-read and still keeps the lanes.

LOW | src/ovcaq/runtime/supervisor.py:172 | The `finally` block catches only `_STATE_ERRORS` around `publish_terminal_evidence`. If the publish raises `OSError` (the new write at line 140 has the same exposure), the exception replaces the supervisor outcome, or fails a valid launch. Cleanup still runs because of the inner `finally`. | Wrap the publishes so a failed write degrades to "final state unavailable", the safe result, instead of propagating.

LOW | src/ovcaq/runtime/_run_observation.py:60 | `publish_terminal_evidence` takes three optional arguments, and "invalidate" and "attest" are the same call with different arguments. | Split it into `invalidate_terminal_evidence(paths)` and `attest_terminal_evidence(paths, entry, state)`. This keeps the same behavior and makes the call sites self-describing.

## Raw review cycle 2

CLOSURE | resolved | MEDIUM `_run_observation.py:133` "The post-read revalidation requires `after.state == result.state` for active runs too... any write during the metric, session or emergency reads discards the whole observation" | The delta changes the check to `after.state is None or (result.ended and after.state != result.state)`, so state equality now applies only to ended runs. Active runs are still pinned by `after.ended` and `after.observation`. The delta adds no test that mutates state mid-read, so the fix is unproven by the suite.

NO FINDINGS
