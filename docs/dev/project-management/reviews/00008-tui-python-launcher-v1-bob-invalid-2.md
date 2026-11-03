# Invalid Bob attempt — cycle 2

This raw result is retained for forensics only. The shared context erroneously
included the design document. The helper then exited 1 because the nonunique
output path already existed; no new reviewer file or receipt was published.
The existing bob-output-2.txt is stale and is not this result.

Raw JSONL: `/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-2-ce429ee36ea64398af00e4609ffa2ce0.jsonl`
Stderr: same stem `.stderr` (empty).
Provider/model: external Claude `claude-opus-5-5`; this is not a Codex review.
No Eve dispatch or Codex thread is claimed. Every raw verdict follows unchanged.

[BOB] 🟡 Textual mode closes without leaving the final frame on screen. When the selected run ends, `_poll` schedules `self.exit(result)` after one refresh (`src/ovcaq/tui/app.py:388`), and `attach` then returns without printing anything (`src/ovcaq/tui/app.py:564-572`). The alternate screen closes, so the post-drain capability failure, its retry command and the halted or paused status disappear after one refresh. `attach` cannot reopen an ended run because cleanup removed its live registry entry. In the default interactive mode the PRD's "exact independent retry command" can therefore never be read; plain mode does print it. `test_textual_returns_terminal_result_after_real_supervisor_exit` takes its screenshot inside `run_test`, before the app closes, so it does not catch this. | File: src/ovcaq/tui/app.py:388 | Task: 2
[BOB] 🟡 A launched child that exits 0 without completing the batch is reported as a failure, and the diagnostic is the raw run-metadata JSON. `_run` writes `json.dumps(asdict(supervisor._metadata))` to the launch report for every exit-0 outcome (`src/ovcaq/supervisor_cli.py:177`). When `_completed_launch` rejects it, `_launch_failure` prints the report as-is: `exited with code 0: {"schema_version": 1, "run_id": ...}` (`src/ovcaq/supervisor_cli.py:303`). A realistic trigger is `pause_requested` still being set, either after `s` or `ovcaq stop` (`_record_stop` sets it) or after `ovcaq pause` while idle. An interactive `ovcaq run` then gets PAUSE from `boundary_decision` immediately and exits 0. If the 50 ms handshake catches the brief publication instead, attach looks for a run that is already gone and the user sees "No matching run selection; available: none". No test sets a pause before launch, and `test_child_completion_report_cannot_complete_a_replacement_batch` only checks that `detail` is truthy. | File: src/ovcaq/supervisor_cli.py:177 | Task: 7
[BOB] 🟡 One failed poll of selected state wipes the observer's session binding, and every run has such a window as it exits. Whenever `selected.state is None`, `_observe` calls `close()` and `_clear()` and sets `_session_id = None` (`src/ovcaq/tui/model.py:453-456`). After `cleanup_run_records` removes run.json, the supervisor process stays alive while it releases the lock, writes the launch report and shuts down. A poll in that gap takes the active branch, fails with "selected run identity is unavailable", and clears everything. The next poll takes the ended branch, which reuses `self._session_id` (`src/ovcaq/tui/model.py:487`). That is now None, so the cached terminal frame shows provider "unknown" and no lanes, and `_telemetry` returns "complete" (`src/ovcaq/tui/model.py:421`) even for a raw-only session. That breaks the PRD metric "raw-only providers remain visibly degraded rather than fabricated". This is a static trace; how often it happens depends on exit latency against the 250 ms poll. | File: src/ovcaq/tui/model.py:453 | Task: 2
[BOB] 🟡 The plain renderer still floods the output during any live run. It now skips identical frames (`src/ovcaq/tui/app.py:453`), but each frame includes `duration: {duration:.0f}s` (`src/ovcaq/tui/panels.py:70`), and duration now counts up from `started_at`. The text therefore changes every second, so a full five-panel frame still prints about once a second (around 3,600 frames an hour) instead of four times a second. `test_plain_prints_only_distinct_frames_and_always_prints_terminal_frame` uses `120.0001`, which rounds to the same text, so it misses this. F26 is reduced, not fixed. | File: src/ovcaq/tui/app.py:453 | Task: 10
[BOB] 🟡 The supervisor silently drops failures to attest its final state with `except _STATE_ERRORS: pass` (`src/ovcaq/runtime/supervisor.py:179`). Every other `_STATE_ERRORS` handler in the file records `_state_failure(site)`. If the read or the publish fails, `run-terminal.json` keeps the placeholder written at lock acquisition. Ended viewers then show "final state does not belong to the selected run" and the launcher rejects a real quick completion, with no record of the cause. | File: src/ovcaq/runtime/supervisor.py:179 | Task: 2
[BOB] 🟡 `ProjectObserver.__init__` still builds a `JsonlFollower` on `paths.events` (`events.jsonl`), the file F01 showed has no writer. It is never read: `_apply` closes and replaces it on the first session bind. It is now the only consumer of `RuntimePaths.events` and implies that file still matters. | File: src/ovcaq/tui/model.py:291 | Task: 1
[BOB] ⚪ `supervisor_cli._run` reads the private `Supervisor._metadata` after `run()` returns (`src/ovcaq/supervisor_cli.py:177`). This only works because `run()` resets `_run_id` but not `_metadata` (`src/ovcaq/runtime/supervisor.py:171`), and the launch report now depends on that asymmetry. | File: src/ovcaq/supervisor_cli.py:177 | Task: 7
[BOB] ⚪ `fleet_table` (`src/ovcaq/tui/panels.py:46`) still has no production caller. The new `_fleet_row` (`src/ovcaq/tui/app.py:38`) re-implements sanitized fleet rows next to it, so there are two fleet renderers and one is used only by tests. | File: src/ovcaq/tui/panels.py:46 | Task: 8
[BOB] ⚪ `_config_root` (`src/ovcaq/tui/app.py:145`) is a sixth copy of `_trusted_path(Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")))`; the other five are in `config.py`. It also imports the private `paths._trusted_path`. F22 asked to reuse config.py's anchor resolution, not to copy it. | File: src/ovcaq/tui/app.py:145 | Task: 9
[BOB] ⚪ Each poll now spawns six `ps` processes. `_selected_state` calls `process_identity` three times (`observe_run`, then `process_matches` at `src/ovcaq/runtime/_run_observation.py:105`, then `observe_run` again), and `observe_selected_run` calls `_selected_state` twice. That is about 24 spawns a second per attached viewer. The cost is my estimate, not measured. | File: src/ovcaq/runtime/_run_observation.py:105 | Task: 2
[BOB] ⚪ `next_phase` now passes `""` through (`src/ovcaq/tui/model.py:396`). The workflow panel prints `phase: build -> ` with nothing after the arrow, where it used to print "unknown". No task asked for this change. | File: src/ovcaq/tui/model.py:396 | Task: 2
[BOB] ⚪ `StateService.add_task` has unrelated formatting changes: two calls drop their magic trailing commas and collapse to one line (`src/ovcaq/state/commands.py:200`, `src/ovcaq/state/commands.py:219`). No task touched `add_task`. | File: src/ovcaq/state/commands.py:200 | Task: 4
[BOB] ⚪ `_run` assigns `descriptor = int(inherited)` before `_verify_inherited_report` succeeds, and the `finally` closes it either way (`src/ovcaq/supervisor_cli.py:158`, `src/ovcaq/supervisor_cli.py:192`). A stray `OVCAQ_LAUNCH_REPORT_FD=1` or `2` with no matching report path would close stdout or stderr before the error is printed. | File: src/ovcaq/supervisor_cli.py:158 | Task: 7
[BOB] ⚪ Cannot statically verify: fail-first replay for this cycle. It was skipped because the sandbox could not create the base worktree (`.git/worktrees/wt: Operation not permitted`). That is a different cause from cycle 1's settled 600 s timeout. | File: N/A | Task: general

R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass

FIX:
- Textual exit hides the terminal frame — src/ovcaq/tui/app.py:388 — When `ProjectApp.run()` returns a terminal result, print the cached ended frame to stdout before `attach` returns (`Console().print(_frame(observer.poll()))`; once ended, `poll()` returns the cached view without new reads). Add a test that runs `attach` to a failed-capability end and checks that stdout contains the retry command.
- Exit-0 pause reported with metadata JSON — src/ovcaq/supervisor_cli.py:177 — Write the decision kind and reason into the success report next to the metadata. In `launch_supervisor`, turn a verified exit 0 that did not complete into a LaunchError whose detail is that reason (for example "Workflow is paused; run `ovcaq resume`"), never the JSON. In `_launch_and_attach`, use the same attested decision for the MissingRunError branch. Add a launcher test that sets `request_pause` before an interactive `run`.
- Transient failure clears the session binding — src/ovcaq/tui/model.py:453 — When `state is None` and the run has not ended, keep `_session_id`, the follower, lanes and provider (`_apply` already resets them on a real session change). In the ended branch, if `_session_id` is None, use the newest metric row with `row.run_id == run.run_id`. Add a test: one poll with run.json removed while the process is alive, then the exit. The final frame must keep provider, lanes and raw-only telemetry.
- Plain renderer still prints every second — src/ovcaq/tui/app.py:453 — Decide whether to print by comparing a frame rendered from `replace(view, duration_seconds=None)`, so only real changes print. Keep always printing the terminal frame. Change the test to use durations that differ by whole seconds.
- Swallowed attestation failure — src/ovcaq/runtime/supervisor.py:179 — Replace `pass` with a recorded cause. Carry the error on `SupervisorOutcome` and have `_run` write it to the launch report or stderr. Keep `cleanup_run_records` in the `finally`.
- Dead initial follower on events.jsonl — src/ovcaq/tui/model.py:291 — Start with `self._follower: JsonlFollower[Observation] | None = None`, create it in `_apply`, and make `close()` skip None.
- Private `_metadata` read — src/ovcaq/supervisor_cli.py:177 — Expose the run identity on `SupervisorOutcome` (for example `metadata: SessionMetadata | None`) and read it from there.
- Two fleet renderers — src/ovcaq/tui/panels.py:46 — Keep one: delete `fleet_table` and its tests, or render the picker rows with it and drop `_fleet_row`.
- Sixth XDG resolution copy — src/ovcaq/tui/app.py:145 — Add one `config_home()` in `config.py` that returns the trusted anchor. Call it from `_config_root` and the five `config.py` sites, and drop the private `_trusted_path` import from the TUI.
- Six `ps` spawns per poll — src/ovcaq/runtime/_run_observation.py:105 — Skip the separate `process_matches` when the first `observe_run` is active and names the selected `(run_id, process)`, since that call already proved the process is alive. Keep the check in every other case.
- Blank next phase — src/ovcaq/tui/model.py:396 — Restore `(work["next_phase"] or None)`, or render an empty next phase as "none" in `workflow_panel`.
- Unrelated reformatting — src/ovcaq/state/commands.py:200 — Revert the two formatting-only hunks in `add_task` (lines 200 and 219).
- Unverified inherited fd closed — src/ovcaq/supervisor_cli.py:158 — Assign `descriptor` only after `_verify_inherited_report` succeeds, so the `finally` closes only a verified report fd.

VERIFY:
- Fail-first replay not run this cycle — `git -C /Users/bob/git/src/github.com/buvis/ovcaq worktree add --detach /tmp/ovcaq-c2-base 5544b1fc9c27 && rsync -a --delete /Users/bob/git/src/github.com/buvis/ovcaq/tests/ /tmp/ovcaq-c2-base/tests/ && (cd /tmp/ovcaq-c2-base && uv run pytest -q -p no:cacheprovider tests/integration/test_launcher_outcomes.py tests/integration/test_observer_terminal_cleanup.py tests/integration/test_observer_terminal_viewers.py tests/integration/test_native_telemetry_identity.py tests/integration/test_supervisor_live_telemetry.py tests/integration/test_control_commit_identity.py tests/integration/test_guarded_run_mutation.py tests/integration/test_viewer_fallback.py tests/state/test_guarded_service.py tests/tui/test_app_poll_responsiveness.py tests/tui/test_app_ended_selection.py tests/tui/test_model_elapsed_duration.py tests/tui/test_model_live_evidence.py tests/tui/test_theme_persistence.py); git -C /Users/bob/git/src/github.com/buvis/ovcaq worktree remove --force /tmp/ovcaq-c2-base`. Pass condition: no test passes at the base, and collection errors count as failing. Any test that does pass there does not pin its change.

KNOWN:
- (none)

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
