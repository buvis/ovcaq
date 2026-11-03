# PRD 00008 cycle-1 recovery snapshot

Recorded after task 12's MEDIUM-repair prompt exceeded 50,000 bytes: 51,332 initially, 50,185 after the one permitted trim. Neither repair prompt was dispatched. Installed work/references/subagent-dispatch.md mandates an abort after that trim; the canonical resume-target now selects the replan handler.

Product HEAD: f254d11cea570eeccf2751315b260d33f34b0e3e. Task 12's 36 focused tests pass, but its two ownership findings remain unresolved. Full project gates and cycle-2 review have not run. Task 11 has been reopened because real adapter identities still break live observation, and its evidence-status construction has a known mypy error.

The schema accepts build/review/done/paused as next_phase, not the old planning spelling in the dispatch reference. The valid recovery destination is next_phase=build with stall_reason=subagent_prompt_overrun; phase stays review, cycle stays1, rework_task_ids and all tasks are preserved. The canonical resume-target confirms replan. No completed-phase transition or signal file was emitted.

Before any recovery handler clears tasks, preserve the pending descriptions below in replan-context. Replan only unfinished repairs. The commits and previous test/review evidence are reusable; do not rebuild the already implemented PRD or silently drop the quoted cycle-1 findings. The remaining task12 scope is smaller than its initial feature implementation. Its tests, no-tools external Pat session, and review state are identified in the cycle-1 rework report. The attempted MEDIUM repair was never dispatched; Pat's delta review was not run. Any continuation must preserve the full work/review session boundary and all required lenses at the next actual review. Never reuse cycle-1 review as proof of the post-repair HEAD.

Task11 follow-up must use real adapter output with native run/session IDs differing from the supervisor IDs, preserve raw bytes, and retain exact observer filtering. Fix SessionEvidenceStatus construction with explicit fields without changing presence/raw_only semantics. Task12 follow-up must bind final state to the exact ended owner even after same-batch replacement completes, and remove observational lock interference with launches. The active-run evidence window also requires verification after the evidence reads. Tess's four-dispatch budget for task12 is exhausted; record coverage limits honestly. Existing tests cover different-batch replacement only.

## Unfinished task snapshot

```json
[
  {
    "name": "[D1] Connect live telemetry and preserve truthful evidence (L)",
    "description": "Fix the cycle-1 findings for PRD 00008.\n\nSource review: docs/dev/project-management/reviews/00008-tui-python-launcher-v1-review-1.md\nReviewed HEAD: 5544b1fc9c27838f8941c2266867a6c34ef10902\n\nLocation: src/ovcaq/tui/model.py; src/ovcaq/tui/panels.py; src/ovcaq/events/tail.py; src/ovcaq/runtime/session.py; src/ovcaq/runtime/supervisor.py; tests/tui/test_model.py; tests/tui/test_panels.py; tests/runtime/test_session_metrics.py; tests/events/test_tail_reader.py; tests/integration/test_terminal_lifecycle.py\n\nDetails:\nConnect ProjectObserver to the actual supervisor-written normalized stream with exact run/session identity and bounded tailing. Correct the run-id versus active-session-id mismatch. Preserve raw-only status when raw bytes exist but the normalized file is empty; a missing unrelated aggregate file must not mask this as merely partial. Never add provider-native parsing or lose raw evidence. Keep live cumulative usage explicitly partial, accept all numeric costs already valid in shared metrics, retain bounded gaps across refreshes, and avoid duplicate backlog diagnostics. Extend the public CapabilityView read-model contract to expose the last attempt's retained session evidence and render a usable evidence pointer, without changing persisted state. Prove live lanes/provider/usage with the real writer-observer connection, including rollover and an empty precreated normalized file.\n\n### Findings (verbatim)\nF01 🟠 ProjectObserver follows runtime `events.jsonl`, but supervisors write normalized observations only to each session’s `normalized.jsonl`; real TUI polls therefore never receive provider, activity-lane, or live-usage events | File: src/ovcaq/tui/model.py:274 | Consensus: 3/3\nF08 🟡 Latest-session cumulative usage is merged into batch totals without forcing `partial=True`; a complete aggregate plus a live full usage snapshot is presented as a complete total even though the active snapshot can still grow | File: src/ovcaq/tui/model.py:323 | Consensus: 1/3\nF09 🟡 Valid integer `cost_usd` values accepted by the shared metric validator are ignored because the projection collects only floats, rendering a valid known cost as unknown | File: src/ovcaq/tui/model.py:221 | Consensus: 2/3\nF10 🟡 Telemetry gaps are bounded only within one poll and are not retained; one-shot malformed, oversized, rotation, and truncation evidence disappears on the next 250 ms refresh | File: src/ovcaq/tui/model.py:293 | Consensus: 1/3\nF16 🟠 Raw-only crash detection cannot work: the normalized file is created before streaming begins, while evidence status treats mere file existence as successful normalization, so a crash after raw persistence but before normalization renders partial/unavailable instead of raw-only | File: src/ovcaq/tui/model.py:393 | Consensus: 1/3\nF19 🟡 The raw-file degradation path never fires in production. `observe_run().active_session_id` comes from run.json, whose `session_id` the supervisor sets to the run_id (`supervisor.py:207`). Real sessions get fresh uuids (`supervisor.py:371`), so `observe_session_evidence(paths, run_id)` always looks in a directory that doesn't exist. `test_raw_only_telemetry_survives_missing_normalization` injects an arbitrary session id, so it passes anyway. | File: src/ovcaq/tui/model.py:376 | Consensus: 1/3\nF28 🟡 The capability view drops the last attempt's `session_id`, so \"retained evidence\" shows only the detail string, with no pointer to the durable session logs the PRD's post-drain feature names. | File: src/ovcaq/tui/model.py:236 | Consensus: 1/3\nF32 ⚪ One backlog condition produces 2 or 3 gaps: the follower's \"truncated: read budget reached\" plus \"backlog: ...\" (`session.py:277`), or plus \"event backlog pending\" and \"event history incomplete\" (`model.py:416`). `TailGap` kind \"truncated\" also covers two different things, a hit read budget and a truncated file. | File: src/ovcaq/events/tail.py:242 | Consensus: 1/3\n\n### Corroborating reviewer details (verbatim)\n[ALICE] 🟠 ProjectObserver follows runtime `events.jsonl`, but supervisors write normalized observations only to each session’s `normalized.jsonl`; real TUI polls therefore never receive provider, activity-lane, or live-usage events | File: src/ovcaq/tui/model.py:274 | Task: 3\n[BLAKE] 🟠 The project observer tails `runtime/events.jsonl`, but the supervisor writes normalized observations only to each session’s `normalized.jsonl`, so live provider identity, activity lanes, and usage events never reach the TUI | File: src/ovcaq/tui/model.py:273 | Task: P06-T01\n[BOB] 🟠 The TUI follows `paths.events` (`<runtime>/events.jsonl`), but no production code writes that file. The supervisor's `RawFirstDecoder` writes normalized observations only to `sessions/<id>/normalized.jsonl` (`supervisor.py:421`). In a real run, every poll therefore gets \"events missing\", lanes and live usage never fill in, provider stays \"unknown\", and telemetry is stuck at \"partial\". The integration suite never checks lanes or provider, so nothing caught this. | File: src/ovcaq/tui/model.py:274 | Task: P06-T01\n[ALICE] 🟡 Latest-session cumulative usage is merged into batch totals without forcing `partial=True`; a complete aggregate plus a live full usage snapshot is presented as a complete total even though the active snapshot can still grow | File: src/ovcaq/tui/model.py:323 | Task: 3\n[ALICE] 🟡 Valid integer `cost_usd` values accepted by the shared metric validator are ignored because the projection collects only floats, rendering a valid known cost as unknown | File: src/ovcaq/tui/model.py:221 | Task: 3\n[BOB] ⚪ The new metric validator accepts an int `cost_usd` (`session.py:118`), but `_usage_view` sums only floats. An int cost shows as \"unknown\" and isn't flagged partial. `events.model.Usage` requires float. | File: src/ovcaq/tui/model.py:221 | Task: P06-T01\n[ALICE] 🟡 Telemetry gaps are bounded only within one poll and are not retained; one-shot malformed, oversized, rotation, and truncation evidence disappears on the next 250 ms refresh | File: src/ovcaq/tui/model.py:293 | Task: 3\n[BLAKE] 🟠 Raw-only crash detection cannot work: the normalized file is created before streaming begins, while evidence status treats mere file existence as successful normalization, so a crash after raw persistence but before normalization renders partial/unavailable instead of raw-only | File: src/ovcaq/tui/model.py:393 | Task: P06-T07\n[BOB] 🟡 The raw-file degradation path never fires in production. `observe_run().active_session_id` comes from run.json, whose `session_id` the supervisor sets to the run_id (`supervisor.py:207`). Real sessions get fresh uuids (`supervisor.py:371`), so `observe_session_evidence(paths, run_id)` always looks in a directory that doesn't exist. `test_raw_only_telemetry_survives_missing_normalization` injects an arbitrary session id, so it passes anyway. | File: src/ovcaq/tui/model.py:376 | Task: P06-T07\n[BOB] 🟡 The capability view drops the last attempt's `session_id`, so \"retained evidence\" shows only the detail string, with no pointer to the durable session logs the PRD's post-drain feature names. | File: src/ovcaq/tui/model.py:236 | Task: P06-T04\n[BOB] ⚪ One backlog condition produces 2 or 3 gaps: the follower's \"truncated: read budget reached\" plus \"backlog: ...\" (`session.py:277`), or plus \"event backlog pending\" and \"event history incomplete\" (`model.py:416`). `TailGap` kind \"truncated\" also covers two different things, a hit read budget and a truncated file. | File: src/ovcaq/events/tail.py:242 | Task: P06-T01\n\nAcceptance criteria:\n- Every quoted finding no longer reproduces.\n- Cover repaired production paths with meaningful regression tests; do not validate only isolated fabricated projections.\n- Preserve sole state-writer ownership, provider-neutral TUI, exact-run targeting, supervisor survival, and raw evidence retention.\n- Run focused tests and the work skill's required verification/review pipeline. Record actual results and hand off to a fresh cycle-2 review after all rework completes.\n",
    "files": [
      "src/ovcaq/tui/model.py",
      "src/ovcaq/tui/panels.py",
      "src/ovcaq/events/tail.py",
      "src/ovcaq/runtime/session.py",
      "src/ovcaq/runtime/supervisor.py",
      "tests/tui/test_model.py",
      "tests/tui/test_panels.py",
      "tests/runtime/test_session_metrics.py",
      "tests/events/test_tail_reader.py",
      "tests/integration/test_terminal_lifecycle.py"
    ],
    "blocked_by": [],
    "estimated_tokens": 109993,
    "est_context_peak": 129993,
    "model": "opus",
    "tier_reason": "contract",
    "qwen_eligible": false,
    "qwen_excluded_reason": "ui",
    "id": "11",
    "status": "pending",
    "attempts": [
      {
        "attempt": 1,
        "model": "opus",
        "outcome": "completed",
        "review_cycle": 1,
        "cause": null,
        "implementor": "codex",
        "preflight_outcome": null,
        "pipeline": "full",
        "devon": "exploit_fixed",
        "devon_exploit": "Tess rejected all eight recorded exploits after strengthening real-child execution, cache totals, estimates, finalized completeness, capability required/status/name, and phase assertions",
        "devon_weak_points": 8,
        "devon_in_contract": [],
        "self_deslop": "noop",
        "style_gate": "clean",
        "split_hygiene": "clean"
      }
    ]
  },
  {
    "name": "[D1] Preserve terminal run observations after cleanup (L)",
    "description": "Fix the cycle-1 findings for PRD 00008.\n\nSource review: docs/dev/project-management/reviews/00008-tui-python-launcher-v1-review-1.md\nReviewed HEAD: 5544b1fc9c27838f8941c2266867a6c34ef10902\n\nLocation: src/ovcaq/tui/model.py; src/ovcaq/tui/app.py; src/ovcaq/runtime/session.py; src/ovcaq/runtime/registry.py; tests/tui/test_model.py; tests/tui/test_app.py; tests/integration/test_terminal_lifecycle.py\n\nDetails:\nCoordinate shared observation and registry identity across supervisor cleanup and replacement. Preserve the ended selected run's final committed state, capability failure/retry/evidence and exit meaning without reading a replacement's state as its own. Keep liveness classification in shared runtime services; the TUI must not add another process/registry algorithm. Make Textual and plain viewers stop polling a definitively ended run and retain a useful terminal frame/result for completed, paused, stopped, halted and attention outcomes. Test a real child that exits between polls, and a replacement starting during final observation.\n\n### Findings (verbatim)\nF02 🟠 Normal supervisor cleanup removes the selected registry entry before the next poll; the observer then returns `unknown`, while both viewers exit only on `completed`, so completion, pause, halt, or stop can leave the viewer polling forever | File: src/ovcaq/tui/app.py:275 | Consensus: 2/3\n\n### Corroborating reviewer details (verbatim)\n[ALICE] 🟠 Normal supervisor cleanup removes the selected registry entry before the next poll; the observer then returns `unknown`, while both viewers exit only on `completed`, so completion, pause, halt, or stop can leave the viewer polling forever | File: src/ovcaq/tui/app.py:275 | Task: 5\n[BOB] 🟠 When the selected supervisor exits (drain, halt, boundary pause, stop), `cleanup_run_records` removes its registry entry. `_identity_live` then returns False and `_observe` stops reading state, so the view drops to status \"unknown\" with no capabilities. The post-drain capability failure, its retry command, the halted/paused status and the completed status all disappear. `ProjectApp` exits on its own only if a poll happens to land in the sub-second window where the batch shows \"completed\". The unit tests keep the identity live with a stub, so this path is untested. | File: src/ovcaq/tui/model.py:396 | Task: P06-T04\n\nAcceptance criteria:\n- Every quoted finding no longer reproduces.\n- Cover repaired production paths with meaningful regression tests; do not validate only isolated fabricated projections.\n- Preserve sole state-writer ownership, provider-neutral TUI, exact-run targeting, supervisor survival, and raw evidence retention.\n- Run focused tests and the work skill's required verification/review pipeline. Record actual results and hand off to a fresh cycle-2 review after all rework completes.\n",
    "files": [
      "src/ovcaq/tui/model.py",
      "src/ovcaq/tui/app.py",
      "src/ovcaq/runtime/session.py",
      "src/ovcaq/runtime/registry.py",
      "tests/tui/test_model.py",
      "tests/tui/test_app.py",
      "tests/integration/test_terminal_lifecycle.py"
    ],
    "blocked_by": [
      11
    ],
    "estimated_tokens": 102447,
    "est_context_peak": 122447,
    "model": "opus",
    "tier_reason": "algorithmic_risk",
    "qwen_eligible": false,
    "qwen_excluded_reason": "ui",
    "id": "12",
    "status": "in_progress",
    "attempts": [
      {
        "attempt": 1,
        "model": "opus",
        "outcome": "aborted",
        "review_cycle": 1,
        "cause": "subagent_prompt_overrun",
        "implementor": "codex",
        "preflight_outcome": null,
        "pipeline": "full",
        "micro_lane": "overrun",
        "devon": "exploit_fixed",
        "devon_exploit": "Eight fixture-shaped wrong implementations passed initial tests; one strengthening round added exact frame, identity, telemetry and gap assertions.",
        "devon_weak_points": 8,
        "devon_in_contract": [],
        "self_deslop": "noop",
        "style_gate": "fixed:f254d11cea570eeccf2751315b260d33f34b0e3e",
        "split_hygiene": "clean",
        "reflow": "src/ovcaq/tui/model.py:23",
        "review": "failed:repair_prompt_overrun"
      }
    ]
  },
  {
    "name": "[D1] Keep controls responsive and duration live (M)",
    "description": "Fix the cycle-1 findings for PRD 00008.\n\nSource review: docs/dev/project-management/reviews/00008-tui-python-launcher-v1-review-1.md\nReviewed HEAD: 5544b1fc9c27838f8941c2266867a6c34ef10902\n\nLocation: src/ovcaq/tui/app.py; src/ovcaq/tui/model.py; tests/tui/test_app.py; tests/tui/test_model.py; tests/integration/test_terminal_lifecycle.py\n\nDetails:\nRun blocking filesystem/process polling outside the Textual UI event loop. Own at most one poll at a time, marshal completed immutable views back to the UI safely, and shut down observer work on detach/fallback without stopping the supervisor. This task coordinates shared observer state across the worker and UI thread. Compute active-run duration from FleetRun.started_at and the observation clock, with explicit unknown handling and a stable terminal duration. Verify navigation/detach while a poll is blocked and record a focused responsiveness measurement; keep duration separate from summed historical metric wall time.\n\n### Findings (verbatim)\nF03 🟠 The Textual timer executes registry snapshots, repeated `ps` probes, and filesystem reads synchronously on the UI thread, allowing every poll to freeze navigation and controls | File: src/ovcaq/tui/app.py:275 | Consensus: 1/3\nF04 🟠 Active duration is calculated by summing finalized session and capability wall times instead of elapsed time from `FleetRun.started_at`, contrary to the explicit duration contract | File: src/ovcaq/tui/model.py:299 | Consensus: 2/3\n\n### Corroborating reviewer details (verbatim)\n[ALICE] 🟠 The Textual timer executes registry snapshots, repeated `ps` probes, and filesystem reads synchronously on the UI thread, allowing every poll to freeze navigation and controls | File: src/ovcaq/tui/app.py:275 | Task: 3\n[ALICE] 🟠 Active duration is calculated by summing finalized session and capability wall times instead of elapsed time from `FleetRun.started_at`, contrary to the explicit duration contract | File: src/ovcaq/tui/model.py:299 | Task: 3\n[BLAKE] 🟡 Active duration is never calculated from registry `started_at`; the projection only sums finalized metric wall times, so a first or currently running session displays unknown or stale duration | File: src/ovcaq/tui/model.py:319 | Task: P06-T03\n\nAcceptance criteria:\n- Every quoted finding no longer reproduces.\n- Cover repaired production paths with meaningful regression tests; do not validate only isolated fabricated projections.\n- Preserve sole state-writer ownership, provider-neutral TUI, exact-run targeting, supervisor survival, and raw evidence retention.\n- Run focused tests and the work skill's required verification/review pipeline. Record actual results and hand off to a fresh cycle-2 review after all rework completes.\n",
    "files": [
      "src/ovcaq/tui/app.py",
      "src/ovcaq/tui/model.py",
      "tests/tui/test_app.py",
      "tests/tui/test_model.py",
      "tests/integration/test_terminal_lifecycle.py"
    ],
    "blocked_by": [
      12
    ],
    "estimated_tokens": 91627,
    "est_context_peak": 111627,
    "model": "opus",
    "tier_reason": "algorithmic_risk",
    "qwen_eligible": false,
    "qwen_excluded_reason": "ui",
    "id": "13",
    "status": "pending"
  },
  {
    "name": "[D1] Bind all controls to one run at mutation time (L)",
    "description": "Fix the cycle-1 findings for PRD 00008.\n\nSource review: docs/dev/project-management/reviews/00008-tui-python-launcher-v1-review-1.md\nReviewed HEAD: 5544b1fc9c27838f8941c2266867a6c34ef10902\n\nLocation: src/ovcaq/tui/app.py; src/ovcaq/tui/discovery.py; src/ovcaq/cli.py; src/ovcaq/supervisor_cli.py; src/ovcaq/runtime/registry.py; src/ovcaq/runtime/session.py; src/ovcaq/state/commands.py; src/ovcaq/state/store.py; tests/runtime/test_attach.py; tests/runtime/test_supervisor_cli.py; tests/tui/test_app.py; tests/integration/test_terminal_lifecycle.py\n\nDetails:\nClose the identity-check/state-commit replacement race using shared runtime/state synchronization, not a second TUI policy engine. The mutation must have an exact selected-run linearization boundary and stale selections must never mutate a replacement. Keep the single state writer and CAS protections; do not invent a new persisted schema. Reuse the same public control path for CLI interactive resume and the TUI, including injected registry semantics for stop. Avoid hand-copying FleetEntry conversions at three call sites when existing discovery selection can be reused. Add deterministic replacement-at-commit tests and real-process coverage; include lock-order and process-exit cases. If an in-scope exact-run fix cannot preserve the existing durable contract, report the concrete blocker rather than weakening the requirement.\n\n### Findings (verbatim)\nF17 🟠 Pause and resume verify run identity before and after the state commit, leaving a race where the selected run can exit and a replacement can start between verification and mutation; the replacement then receives the control action despite the exact-targeting requirement | File: src/ovcaq/tui/app.py:82 | Consensus: 1/3\nF24 🟡 `_resume_and_attach` repeats existing services. It builds a `FleetRun` from a `FleetEntry` by hand and runs verify, then CAS-resume, but skips the post-write re-verify that `RunControlService.resume` does. The same `FleetEntry`→`FleetRun` copy also appears at `supervisor_cli.py:260` and `tui/discovery.py:22`. | File: src/ovcaq/cli.py:492 | Consensus: 1/3\nF34 ⚪ `RunControlService.stop` calls `stop_supervisor(run)`, which builds its own `FleetRegistry` instead of using the injected `self._registry` that pause and resume use. | File: src/ovcaq/tui/app.py:77 | Consensus: 1/3\n\n### Corroborating reviewer details (verbatim)\n[BLAKE] 🟠 Pause and resume verify run identity before and after the state commit, leaving a race where the selected run can exit and a replacement can start between verification and mutation; the replacement then receives the control action despite the exact-targeting requirement | File: src/ovcaq/tui/app.py:82 | Task: P06-T05\n[BOB] 🟡 `_resume_and_attach` repeats existing services. It builds a `FleetRun` from a `FleetEntry` by hand and runs verify, then CAS-resume, but skips the post-write re-verify that `RunControlService.resume` does. The same `FleetEntry`→`FleetRun` copy also appears at `supervisor_cli.py:260` and `tui/discovery.py:22`. | File: src/ovcaq/cli.py:492 | Task: P06-T08\n[BOB] ⚪ `RunControlService.stop` calls `stop_supervisor(run)`, which builds its own `FleetRegistry` instead of using the injected `self._registry` that pause and resume use. | File: src/ovcaq/tui/app.py:77 | Task: P06-T05\n\nAcceptance criteria:\n- Every quoted finding no longer reproduces.\n- Cover repaired production paths with meaningful regression tests; do not validate only isolated fabricated projections.\n- Preserve sole state-writer ownership, provider-neutral TUI, exact-run targeting, supervisor survival, and raw evidence retention.\n- Run focused tests and the work skill's required verification/review pipeline. Record actual results and hand off to a fresh cycle-2 review after all rework completes.\n",
    "files": [
      "src/ovcaq/tui/app.py",
      "src/ovcaq/tui/discovery.py",
      "src/ovcaq/cli.py",
      "src/ovcaq/supervisor_cli.py",
      "src/ovcaq/runtime/registry.py",
      "src/ovcaq/runtime/session.py",
      "src/ovcaq/state/commands.py",
      "src/ovcaq/state/store.py",
      "tests/runtime/test_attach.py",
      "tests/runtime/test_supervisor_cli.py",
      "tests/tui/test_app.py",
      "tests/integration/test_terminal_lifecycle.py"
    ],
    "blocked_by": [
      13
    ],
    "estimated_tokens": 122032,
    "est_context_peak": 142032,
    "model": "opus",
    "tier_reason": "algorithmic_risk",
    "qwen_eligible": false,
    "qwen_excluded_reason": "tier",
    "id": "14",
    "status": "pending"
  },
  {
    "name": "[D1] Correct launch outcomes, diagnostics and CLI routing (L)",
    "description": "Fix the cycle-1 findings for PRD 00008.\n\nSource review: docs/dev/project-management/reviews/00008-tui-python-launcher-v1-review-1.md\nReviewed HEAD: 5544b1fc9c27838f8941c2266867a6c34ef10902\n\nLocation: src/ovcaq/cli.py; src/ovcaq/supervisor_cli.py; src/ovcaq/config.py; src/ovcaq/paths.py; tests/runtime/test_supervisor_cli.py; tests/packaging/test_installed_supervisor_cli.py; tests/integration/test_terminal_lifecycle.py\n\nDetails:\nEnforce the accepted JSON run --no-tui requirement while preserving non-TTY foreground behavior. Make immediate successful child completion and the publication/cleanup race return the committed success outcome instead of an unhandled-crash LaunchError; never spawn a second child as a retry. Capture bounded sanitized diagnostics for dispatch/config/layout failures before registry publication, including errors occurring before current report claim. Respect the configured runtime root without creating an unused default tree. Keep TUI imports lazy for ordinary state/headless commands; no guessed timing claim is needed to prove import isolation. Duplicate-owner guidance must recommend attaching to the healthy owner, not stopping it. Tests must cover quick-drain, config failure, configured runtime root, JSON flags, exactly-one child, and imported-module isolation.\n\n### Findings (verbatim)\nF05 🟠 JSON `run` without `--no-tui` is silently dispatched as a foreground run, although the CLI contract requires JSON mode to reject it unless `--no-tui` is explicit | File: src/ovcaq/cli.py:526 | Consensus: 1/3\nF11 🟡 `supervisor_settings()` runs before the child claims its launch report and before the guarded block, so configuration or layout failures bypass durable diagnostics and are misreported by the parent as an unhandled crash | File: src/ovcaq/supervisor_cli.py:117 | Consensus: 1/3\nF20 🟡 Interactive `run`/`resume` on a batch that finishes right away reports a crash. The child supervisor exits 0, but `_run` writes the launch report only when `exit_code != 0`, so the launcher prints \"exited with code 0: unhandled crash before publishing a failure report\". Alternatively, attach races cleanup and fails with \"No matching run selection\". | File: src/ovcaq/supervisor_cli.py:138 | Consensus: 1/3\nF23 🟡 `cli.py` imports `ovcaq.tui.app` at module top, and that module imports Textual and Rich at import time. Every `ovcaq` call, including the frequent agent `ovcaq state ...` calls, now pays the Textual import. The cost is my guess (about 100 ms or more, not measured). | File: src/ovcaq/cli.py:61 | Consensus: 1/3\nF35 ⚪ When a supervisor already owns the root, interactive `run` fails with \"ambiguous or unrelated ownership ... end it with `ovcaq stop`\". That `stop` would kill the healthy existing run, not the child that failed. | File: src/ovcaq/supervisor_cli.py:252 | Consensus: 1/3\nF36 ⚪ `launch_supervisor` creates the derived runtime tree (`ensure_runtime_directory`) but writes its report under the configured `runtime_root`. These may differ when the runtime root is configured. | File: src/ovcaq/supervisor_cli.py:279 | Consensus: 1/3\n\n### Corroborating reviewer details (verbatim)\n[ALICE] 🟠 JSON `run` without `--no-tui` is silently dispatched as a foreground run, although the CLI contract requires JSON mode to reject it unless `--no-tui` is explicit | File: src/ovcaq/cli.py:526 | Task: 8\n[ALICE] 🟡 `supervisor_settings()` runs before the child claims its launch report and before the guarded block, so configuration or layout failures bypass durable diagnostics and are misreported by the parent as an unhandled crash | File: src/ovcaq/supervisor_cli.py:117 | Task: 8\n[BOB] 🟡 Interactive `run`/`resume` on a batch that finishes right away reports a crash. The child supervisor exits 0, but `_run` writes the launch report only when `exit_code != 0`, so the launcher prints \"exited with code 0: unhandled crash before publishing a failure report\". Alternatively, attach races cleanup and fails with \"No matching run selection\". | File: src/ovcaq/supervisor_cli.py:138 | Task: P06-T08\n[BOB] 🟡 `cli.py` imports `ovcaq.tui.app` at module top, and that module imports Textual and Rich at import time. Every `ovcaq` call, including the frequent agent `ovcaq state ...` calls, now pays the Textual import. The cost is my guess (about 100 ms or more, not measured). | File: src/ovcaq/cli.py:61 | Task: P06-T08\n[BOB] ⚪ When a supervisor already owns the root, interactive `run` fails with \"ambiguous or unrelated ownership ... end it with `ovcaq stop`\". That `stop` would kill the healthy existing run, not the child that failed. | File: src/ovcaq/supervisor_cli.py:252 | Task: P06-T08\n[BOB] ⚪ `launch_supervisor` creates the derived runtime tree (`ensure_runtime_directory`) but writes its report under the configured `runtime_root`. These may differ when the runtime root is configured. | File: src/ovcaq/supervisor_cli.py:279 | Task: P06-T08\n\nAcceptance criteria:\n- Every quoted finding no longer reproduces.\n- Cover repaired production paths with meaningful regression tests; do not validate only isolated fabricated projections.\n- Preserve sole state-writer ownership, provider-neutral TUI, exact-run targeting, supervisor survival, and raw evidence retention.\n- Run focused tests and the work skill's required verification/review pipeline. Record actual results and hand off to a fresh cycle-2 review after all rework completes.\n",
    "files": [
      "src/ovcaq/cli.py",
      "src/ovcaq/supervisor_cli.py",
      "src/ovcaq/config.py",
      "src/ovcaq/paths.py",
      "tests/runtime/test_supervisor_cli.py",
      "tests/packaging/test_installed_supervisor_cli.py",
      "tests/integration/test_terminal_lifecycle.py"
    ],
    "blocked_by": [
      14
    ],
    "estimated_tokens": 102783,
    "est_context_peak": 122783,
    "model": "opus",
    "tier_reason": "algorithmic_risk",
    "qwen_eligible": false,
    "qwen_excluded_reason": "tier",
    "id": "15",
    "status": "pending"
  },
  {
    "name": "[D1] Sanitize real fleet pickers and show discovery gaps (M)",
    "description": "Fix the cycle-1 findings for PRD 00008.\n\nSource review: docs/dev/project-management/reviews/00008-tui-python-launcher-v1-review-1.md\nReviewed HEAD: 5544b1fc9c27838f8941c2266867a6c34ef10902\n\nLocation: src/ovcaq/tui/app.py; src/ovcaq/tui/panels.py; tests/tui/test_app.py; tests/tui/test_panels.py\n\nDetails:\nSanitize every rendered run ID, root and agent in both production fleet selection paths. Use the shared display_text boundary and a common row formatter or the existing fleet renderer where appropriate; test actual selectors rather than an unused table. Present stale/malformed counts and a useful empty-fleet result without silently selecting or launching a run. Preserve exact-run selection and literal Rich text semantics.\n\n### Findings (verbatim)\nF06 🟠 Fleet selection renders `run.root` and `run.agent` without `display_text`; configured agents or project paths containing terminal controls can inject output in both Textual and plain modes | File: src/ovcaq/tui/app.py:354 | Consensus: 3/3\nF18 🟡 Malformed and stale registry entries are preserved in `FleetView` but neither the Textual fleet selector nor the plain selector renders them, silently hiding incomplete fleet evidence instead of exposing a telemetry gap | File: src/ovcaq/tui/app.py:206 | Consensus: 2/3\n\n### Corroborating reviewer details (verbatim)\n[ALICE] 🟠 Fleet selection renders `run.root` and `run.agent` without `display_text`; configured agents or project paths containing terminal controls can inject output in both Textual and plain modes | File: src/ovcaq/tui/app.py:354 | Task: 3\n[BLAKE] 🟡 The actual Textual and plain fleet selectors sanitize only the run ID; attacker-controlled control characters in registry root or agent fields reach terminal output even though the separate fleet table sanitizes those values | File: src/ovcaq/tui/app.py:209 | Task: P06-T02\n[BOB] 🟡 The production fleet pickers print registry `root` and `agent` without `display_text`. `run_plain_fleet` writes them raw to the terminal, and the registry only checks that they are non-empty strings, so control sequences get through. Meanwhile the sanitized `fleet_table` (`panels.py:46`), which `test_fleet_table_sanitizes_agent_run_and_path_text` covers, has no production caller. | File: src/ovcaq/tui/app.py:354 | Task: P06-T02\n[BLAKE] 🟡 Malformed and stale registry entries are preserved in `FleetView` but neither the Textual fleet selector nor the plain selector renders them, silently hiding incomplete fleet evidence instead of exposing a telemetry gap | File: src/ovcaq/tui/app.py:206 | Task: P06-T02\n[BOB] ⚪ The fleet picker hides `malformed_entries`/`stale_entries`. With no live runs it opens an empty picker, and plain mode just waits at \"run id:\". | File: src/ovcaq/tui/app.py:209 | Task: P06-T02\n\nAcceptance criteria:\n- Every quoted finding no longer reproduces.\n- Cover repaired production paths with meaningful regression tests; do not validate only isolated fabricated projections.\n- Preserve sole state-writer ownership, provider-neutral TUI, exact-run targeting, supervisor survival, and raw evidence retention.\n- Run focused tests and the work skill's required verification/review pipeline. Record actual results and hand off to a fresh cycle-2 review after all rework completes.\n",
    "files": [
      "src/ovcaq/tui/app.py",
      "src/ovcaq/tui/panels.py",
      "tests/tui/test_app.py",
      "tests/tui/test_panels.py"
    ],
    "blocked_by": [
      15
    ],
    "estimated_tokens": 80342,
    "est_context_peak": 100342,
    "model": "sonnet",
    "tier_reason": "default",
    "qwen_eligible": false,
    "qwen_excluded_reason": "ui",
    "id": "16",
    "status": "pending"
  },
  {
    "name": "[D1] Wire theme persistence to the shared XDG boundary (M)",
    "description": "Fix the cycle-1 findings for PRD 00008.\n\nSource review: docs/dev/project-management/reviews/00008-tui-python-launcher-v1-review-1.md\nReviewed HEAD: 5544b1fc9c27838f8941c2266867a6c34ef10902\n\nLocation: src/ovcaq/tui/app.py; src/ovcaq/config.py; src/ovcaq/paths.py; tests/tui/test_app.py\n\nDetails:\nPersist real user theme changes through save_theme from both Textual apps; do not delete the requested persistence feature. Reuse existing XDG anchor semantics, including an explicitly selected symlink alias resolved as a trusted anchor and the documented empty/default/relative behavior. Enforce no-follow, size limits, allowlist, private permissions and atomic replacement for application-owned descendants beneath that anchor, with safe handling of concurrent path replacement. Keep failures visible and nonfatal. Alice's F07 all-ancestor rejection was discarded because it contradicts the shared trusted-anchor contract; do not implement it. Test actual theme change persistence and symlinked-anchor versus child/file-symlink cases.\n\n### Findings (verbatim)\nF21 🟡 `save_theme` has no production caller; only tests call it. No binding or theme watcher persists a theme change, so the saving half of the theme port is dead code. | File: src/ovcaq/tui/app.py:152 | Consensus: 1/3\nF22 🟡 `_linked_dirs` rejects a symlinked `XDG_CONFIG_HOME` (it checks `path.parent.parent`). `config.py` trusts the same anchor on purpose (`tests/runtime/test_paths.py:357`), so the two disagree. Users with a symlinked `~/.config` always get the theme gap. `_config_root` also re-implements XDG resolution and treats an empty value differently from `config.py`. | File: src/ovcaq/tui/app.py:123 | Consensus: 1/3\n\n### Corroborating reviewer details (verbatim)\n[BOB] 🟡 `save_theme` has no production caller; only tests call it. No binding or theme watcher persists a theme change, so the saving half of the theme port is dead code. | File: src/ovcaq/tui/app.py:152 | Task: P06-T06\n[BOB] 🟡 `_linked_dirs` rejects a symlinked `XDG_CONFIG_HOME` (it checks `path.parent.parent`). `config.py` trusts the same anchor on purpose (`tests/runtime/test_paths.py:357`), so the two disagree. Users with a symlinked `~/.config` always get the theme gap. `_config_root` also re-implements XDG resolution and treats an empty value differently from `config.py`. | File: src/ovcaq/tui/app.py:123 | Task: P06-T06\n\nAcceptance criteria:\n- Every quoted finding no longer reproduces.\n- Cover repaired production paths with meaningful regression tests; do not validate only isolated fabricated projections.\n- Preserve sole state-writer ownership, provider-neutral TUI, exact-run targeting, supervisor survival, and raw evidence retention.\n- Run focused tests and the work skill's required verification/review pipeline. Record actual results and hand off to a fresh cycle-2 review after all rework completes.\n",
    "files": [
      "src/ovcaq/tui/app.py",
      "src/ovcaq/config.py",
      "src/ovcaq/paths.py",
      "tests/tui/test_app.py"
    ],
    "blocked_by": [
      16
    ],
    "estimated_tokens": 83863,
    "est_context_peak": 103863,
    "model": "opus",
    "tier_reason": "algorithmic_risk",
    "qwen_eligible": false,
    "qwen_excluded_reason": "ui",
    "id": "17",
    "status": "pending"
  },
  {
    "name": "[D1] Make plain fallback survive errors and detach on EOF (M)",
    "description": "Fix the cycle-1 findings for PRD 00008.\n\nSource review: docs/dev/project-management/reviews/00008-tui-python-launcher-v1-review-1.md\nReviewed HEAD: 5544b1fc9c27838f8941c2266867a6c34ef10902\n\nLocation: src/ovcaq/tui/app.py; tests/tui/test_app.py; tests/integration/test_terminal_lifecycle.py\n\nDetails:\nCatch ordinary Textual import/start/runtime failures at the attach boundary, restore terminal state, and enter plain rendering on the same selected observer. Preserve KeyboardInterrupt/SystemExit semantics instead of swallowing BaseException. Make real stdin EOF/Ctrl-D detach plain project mode; injecting EOFError from a mock observer is not proof. Avoid repeatedly printing an unchanged full frame while maintaining useful bounded live updates. Retain the accepted AttachResult type and require tests to prove the supervisor/agent survive each failure and detach path.\n\n### Findings (verbatim)\nF12 🟡 The attach boundary catches only three exception families, so other Textual startup or runtime exceptions bypass the mandated plain-renderer fallback | File: src/ovcaq/tui/app.py:31 | Consensus: 2/3\nF13 🟡 Plain project mode never reads stdin, so terminal EOF/Ctrl-D cannot reach its `EOFError` handler and cannot detach the fallback viewer | File: src/ovcaq/tui/app.py:329 | Consensus: 2/3\nF26 🟡 `run_plain` prints the whole five-panel frame every 0.25 s even when nothing changed. Over a multi-hour session that floods the terminal or any piped log. | File: src/ovcaq/tui/app.py:338 | Consensus: 1/3\n\n### Corroborating reviewer details (verbatim)\n[ALICE] 🟡 The attach boundary catches only three exception families, so other Textual startup or runtime exceptions bypass the mandated plain-renderer fallback | File: src/ovcaq/tui/app.py:31 | Task: 9\n[BLAKE] 🟡 Textual fallback catches only ImportError, OSError, and RuntimeError, so other startup/runtime exceptions such as ValueError bypass the required plain-renderer fallback | File: src/ovcaq/tui/app.py:31 | Task: P06-T09\n[ALICE] 🟡 Plain project mode never reads stdin, so terminal EOF/Ctrl-D cannot reach its `EOFError` handler and cannot detach the fallback viewer | File: src/ovcaq/tui/app.py:329 | Task: 9\n[BOB] ⚪ The `EOFError` handlers in `run_plain` and `run_plain_fleet` can never fire: `readline` returns \"\" at EOF, and `poll` never reads stdin. `test_plain_project_interrupt_or_eof_is_detach` injects an EOFError that cannot happen. | File: src/ovcaq/tui/app.py:342 | Task: P06-T09\n[BOB] 🟡 `run_plain` prints the whole five-panel frame every 0.25 s even when nothing changed. Over a multi-hour session that floods the terminal or any piped log. | File: src/ovcaq/tui/app.py:338 | Task: P06-T09\n\nAcceptance criteria:\n- Every quoted finding no longer reproduces.\n- Cover repaired production paths with meaningful regression tests; do not validate only isolated fabricated projections.\n- Preserve sole state-writer ownership, provider-neutral TUI, exact-run targeting, supervisor survival, and raw evidence retention.\n- Run focused tests and the work skill's required verification/review pipeline. Record actual results and hand off to a fresh cycle-2 review after all rework completes.\n",
    "files": [
      "src/ovcaq/tui/app.py",
      "tests/tui/test_app.py",
      "tests/integration/test_terminal_lifecycle.py"
    ],
    "blocked_by": [
      17
    ],
    "estimated_tokens": 81325,
    "est_context_peak": 101325,
    "model": "sonnet",
    "tier_reason": "default",
    "qwen_eligible": false,
    "qwen_excluded_reason": "ui",
    "id": "18",
    "status": "pending"
  },
  {
    "name": "[D1] Tighten collision preservation and decoder exception handling (S)",
    "description": "Fix the cycle-1 findings for PRD 00008.\n\nSource review: docs/dev/project-management/reviews/00008-tui-python-launcher-v1-review-1.md\nReviewed HEAD: 5544b1fc9c27838f8941c2266867a6c34ef10902\n\nLocation: src/ovcaq/events/tail.py; tests/state/test_cli.py; tests/events/test_tail_reader.py\n\nDetails:\nPin each config collision's original object kind/identity after rejected initialization; retain no-state-publication assertions and avoid a disjunction that permits changing one collision shape into another. Simplify the new tail decoder's BaseException/isinstance/re-raise shape to the equivalent ordinary Exception catch, retaining propagation of process-control exceptions and tolerant decoding of ordinary failures. Verify only the affected tests before the mandatory final suite.\n\n### Findings (verbatim)\nF15 🟡 `test_init_rejects_project_config_path_collisions_before_state_publication` hedges with `or`, so either asserted setup shape satisfies the final check | File: tests/state/test_cli.py:361 | Consensus: 2/3\nF25 🟡 `except BaseException` followed by `if not isinstance(error, Exception): raise` behaves exactly like `except Exception:`. Ruff runs default rules with no BLE, so there is no lint reason for this shape. | File: src/ovcaq/events/tail.py:316 | Consensus: 1/3\n\n### Corroborating reviewer details (verbatim)\n[ALICE] 🟡 `test_init_rejects_project_config_path_collisions_before_state_publication` hedges with `or`, so either asserted setup shape satisfies the final check | File: tests/state/test_cli.py:361 | Task: general\n[BOB] ⚪ [MECH] `assert config.is_dir() or config.is_symlink()` hedges with `or`, so it doesn't pin the collision kind for each parameter. | File: tests/state/test_cli.py:361 | Task: general\n[BOB] 🟡 `except BaseException` followed by `if not isinstance(error, Exception): raise` behaves exactly like `except Exception:`. Ruff runs default rules with no BLE, so there is no lint reason for this shape. | File: src/ovcaq/events/tail.py:316 | Task: P06-T01\n\nAcceptance criteria:\n- Every quoted finding no longer reproduces.\n- Cover repaired production paths with meaningful regression tests; do not validate only isolated fabricated projections.\n- Preserve sole state-writer ownership, provider-neutral TUI, exact-run targeting, supervisor survival, and raw evidence retention.\n- Run focused tests and the work skill's required verification/review pipeline. Record actual results and hand off to a fresh cycle-2 review after all rework completes.\n",
    "files": [
      "src/ovcaq/events/tail.py",
      "tests/state/test_cli.py",
      "tests/events/test_tail_reader.py"
    ],
    "blocked_by": [
      18
    ],
    "estimated_tokens": 76581,
    "est_context_peak": 96581,
    "model": "sonnet",
    "tier_reason": "default",
    "qwen_eligible": false,
    "qwen_excluded_reason": "files",
    "id": "19",
    "status": "pending"
  },
  {
    "name": "[D1] Document the delivered launcher and TUI behavior (S)",
    "description": "Fix the cycle-1 findings for PRD 00008.\n\nSource review: docs/dev/project-management/reviews/00008-tui-python-launcher-v1-review-1.md\nReviewed HEAD: 5544b1fc9c27838f8941c2266867a6c34ef10902\n\nLocation: src/ovcaq/cli.py; docs/operations.md; CHANGELOG.md\n\nDetails:\nAdd the missing release notes for attach, TTY-default run, detach/plain fallback and interactive resume. Correct the live parser's resume help, regenerate command documentation from that parser, and add concise operator guidance for q/p/s/?, the OVCAQ theme path and plain fallback. Do not maintain a second handwritten verb inventory. Describe the behavior after the other cycle-1 fixes.\n\n### Findings (verbatim)\nF27 🟡 CHANGELOG has no Added entry for `ovcaq attach`, TTY-default `ovcaq run`, the TUI with plain fallback, or interactive `resume` that launches or attaches. In this range only a paths Fixed line was added, but `rules/changelog.md` requires an entry with each feat commit. | File: CHANGELOG.md:9 | Consensus: 1/3\nF33 ⚪ `resume` help still says \"clear a pause request\", but interactive resume now launches or attaches. The operator docs don't mention the q/p/s/? keys, the theme path, or the plain fallback. | File: src/ovcaq/cli.py:203 | Consensus: 1/3\n\n### Corroborating reviewer details (verbatim)\n[BOB] 🟡 CHANGELOG has no Added entry for `ovcaq attach`, TTY-default `ovcaq run`, the TUI with plain fallback, or interactive `resume` that launches or attaches. In this range only a paths Fixed line was added, but `rules/changelog.md` requires an entry with each feat commit. | File: CHANGELOG.md:9 | Task: general\n[BOB] ⚪ `resume` help still says \"clear a pause request\", but interactive resume now launches or attaches. The operator docs don't mention the q/p/s/? keys, the theme path, or the plain fallback. | File: src/ovcaq/cli.py:203 | Task: general\n\nAcceptance criteria:\n- Every quoted finding no longer reproduces.\n- Cover repaired production paths with meaningful regression tests; do not validate only isolated fabricated projections.\n- Preserve sole state-writer ownership, provider-neutral TUI, exact-run targeting, supervisor survival, and raw evidence retention.\n- Run focused tests and the work skill's required verification/review pipeline. Record actual results and hand off to a fresh cycle-2 review after all rework completes.\n",
    "files": [
      "src/ovcaq/cli.py",
      "docs/operations.md",
      "CHANGELOG.md"
    ],
    "blocked_by": [
      19
    ],
    "estimated_tokens": 75389,
    "est_context_peak": 95389,
    "model": "sonnet",
    "tier_reason": "default",
    "qwen_eligible": false,
    "qwen_excluded_reason": "files",
    "id": "20",
    "status": "pending"
  }
]
```

## External Pat task12 raw review

Actual provider/model: Claude claude-sonnet-5-5. Session fa2262e1-7e0e-4cc4-8b5c-647cc52056fd; dispatch f27f7244. Full prompt70,115 bytes through the external Sonnet helper, no tools/edit permissions, approved network access. Launcher receipt docs/dev/tmp/pat-12-run.log.json. parse_review.py accepted output (exit0). Both MEDIUM findings were confirmed from source by the coordinator; LOW notes remain review evidence.

CLOSURE | resolved | "Normal supervisor cleanup removes the selected registry entry before the next poll; the observer then returns `unknown`, while both viewers exit only on `completed`, so completion, pause, halt, or stop can leave the viewer polling forever" | `observe_selected_run` reads the final state under a pinned lock once the process identity ends, `_terminal_result` maps ended statuses to an `AttachResult`, and both `run_plain` and `ProjectApp._poll` stop on it. The real-subprocess tests cover completed, paused, stopped, halted and attention.

MEDIUM | src/ovcaq/runtime/_run_observation.py:52 | The ended branch accepts any final state whose `batch.id` matches the one cached from earlier polls. A replacement supervisor resuming the same batch (for example after a pause) that runs and cleans up between polls leaves metadata absent and the lock idle, so its progress is shown as the selected run's final state. The only replacement tests seed a different batch id, so this case is untested. | Bind the final state to the selected run's identity, for example by recording the run id or revision at the last live poll and rejecting a final state that does not belong to it. Add a same-batch replacement test.

MEDIUM | src/ovcaq/runtime/registry.py:26 | `observe_unowned_run` holds a shared `flock` on `run.lock` for the whole evidence read: state, metrics and session evidence. A concurrent supervisor start that takes the lock exclusively without waiting would hit `DuplicateRunError`. Another `observe_run` caller would also see the lock held with no metadata and report "inconsistent". The test fixture works around this (`# A reader may hold the run lock`, `ready.wait(0.5)`), which shows the interference is real. | Pin identity without holding the lock across the reads. For example, snapshot state and metadata, then re-check lock and metadata after the reads and discard the result on any change. Or keep the pin to a bounded window and add a test that a supervisor starting during final observation still acquires the lock.

LOW | src/ovcaq/tui/model.py:372 | `next_phase=(work["next_phase"] or None)` became `work["next_phase"]`. This unrelated projection change makes an empty string render as an empty value instead of `None`, and the full suite has not been run. | Restore `or None`. Loosen the test's `next_phase` equality only if it truly needs `""`.

LOW | src/ovcaq/tui/model.py:200 | Terminal status mapping is split across two places: `halted` in `_status` and `stopped` in `_project` (`"stopped" if self._ended and status == "stopping"`). | Move the `stopping` to `stopped` mapping into `_status` next to the `ended` handling.

LOW | src/ovcaq/tui/model.py:312 | `ProjectObserver.poll` is now about 50 lines and mixes state projection, caching and the closing decision. | Extract the `state is None and self._view is not None` fallback into a helper, such as `_degraded_view(gaps)`.

LOW | src/ovcaq/runtime/_run_observation.py:80 | `observe_run` imports `parse_session_metadata` from `session` inside the function, which hides a circular dependency, and `session.py` carries four re-export blocks to preserve the old names. | Move `parse_session_metadata` into `_run_observation` or `_session_io` so no lazy import is needed.


