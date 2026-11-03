# Project Capsule: OVCAQ

Generated: 2026-10-28 21:20Z (full catchup, PRD 00063 build re-entry after an auth PAUSE)
Catchup HEAD: `0bd25ed` (`master`)

## Key Invariants

- `StateStore.transaction()` is the only durable `state.json` writer; commands and later workflow/runtime services share it.
- State plus a normalized session result decides lifecycle progress. Agent prose and observational logs never do.
- The clean v1 state is a one-way cutover: no legacy importer, dual writer, compatibility shim, or permanent `autoclaude`/`autopilot`/`tracon`/`statectl` aliases.
- Provider-specific argv, environment, event, model, and rate-limit logic remains at driver edges; provider-neutral state/runtime/TUI modules must not parse native events.
- Raw session evidence survives normalization, and configured commands are always argv arrays spawned without shell evaluation.
- PRD sequencing follows `docs/dev/project-management/plans/implementation-plan.md`: state first, then workflow, runtime, adapters, TUI, and provisioning.

## Architecture Decisions

- **Three-layer target adopted 2026-10-25** (AGENTS.md, `docs/dev/architecture/README.md`): workflow authority moves to external Autopilot's controller, terminal presentation moves to separate Lantern; OVCAQ keeps headless session/process orchestration, mixed-driver collaboration, execution records, and the public operations API. Workflow extraction precedes consumer activation; the operations API precedes external UI integration; installed parity precedes removing bundled Textual/Rich. Current bundled code remains authoritative until each extraction's consumer reaches parity — this PRD (00057) builds the controller-client characterization/contract layer, not the cutover itself.
- OVCAQ is one Python 3.12+ installable package with an `ovcaq` console command and a small runtime dependency set (Rich/Textual plus stdlib-first internals, Textual/Rich to be dropped from core once the TUI is extracted).
- State, workflow, runtime, events, both native adapters, supervisor, and TUI are implemented through PRD 00009; drivers/runtime/TUI continued through PRD 00054 and beyond (Codex adapter with native decoding/lane projection, shared-model TUI with attach/plain fallback, state-led supervisor decisions, handoff/recovery-intent rejection in workflow). Provisioning and real launcher/plugin smoke remain later-phase work.
- State v1 groups ownership under `batch`, `work`, `tasks`, `review`, `control`, and `recovery`, with a monotonic top-level `revision`.
- Every transaction holds one advisory lock across read, optional revision compare, deep-copy mutation, full validation, revision increment, raw-byte backup publication, state publication, and supported directory fsync.
- Generic JSON-path operations are recovery tools. Transition-owned paths require explicit `--unsafe`; normal skills use compound commands instead.
- External launcher skills/plugins remain in their marketplaces. Core owns only declarative requirements and lifecycle state needed to reconcile them.

## Component Boundaries

- `ovcaq.state.schema`: clean v1 types/defaults, full nested validation, cross-field invariants, and future-version refusal.
- `ovcaq.state.store`: locked load/init/transaction/restore, compare-and-set, backup, atomic replacement, and durability boundaries.
- `ovcaq.state.paths`: generic JSON-path parsing/mutation only; no workflow ownership policy.
- `ovcaq.state.commands`: compound task/attempt/contract-card operations and recovery commands; all writes call the store.
- `ovcaq.cli`: the live parser and stable machine-output/error boundary; help and state documentation derive from it.
- `ovcaq.workflow`: completed pure selection, frontmatter, resume, transition, policy, recoverable filesystem-record, and report services; it owns no process or launcher behavior.
- `ovcaq.paths` and `ovcaq.config`: shared project/runtime discovery, containment, configuration precedence, agent tier settings, and phase routing; launcher-specific interpretation remains at the driver edge.
- `ovcaq.runtime`: now owns runtime paths/configuration, the authoritative run lock, fleet registry, process groups, watchdog cleanup, raw session evidence, retention/purge, capabilities, and completion cleanup. `runtime_cli.py` projects those shared models into status/doctor/logs without becoming a second liveness authority.
- `ovcaq.events` owns immutable protocol-1 observations, reduction and raw-first framing; `ovcaq.drivers` owns native decoding for both launchers under driver API 2. `runtime.session` owns private raw evidence and the decoder publishes normalized observations only afterward. The raw-first boundary must reject invalid native strings before a stateful adapter mutates identity/usage; genuine evidence writer failures must still propagate.
- `ovcaq.tui` now projects the shared registry, state, metrics, normalized events,
  and capability models; it owns presentation and exact-run controls but no
  lifecycle policy or provider-native decoding. `ovcaq.provision` remains a
  later-phase boundary.

## Active Work

### Batch 202610272211
- [x] 00057-autopilot-controller-client-v1.md (3 cycles)
- [x] 00062-supervisor-process-identity-v1.md (2 cycles)
- [x] 00063-driver-failure-classes-tiers-v1.md (2 cycles)
- [ ] 00058-00061, 00064-00065 - remain in `backlog/`, all carrying `tools/autopilot-prerequisites` eligibility gates (skipped every pick so far this batch)

**00063 converged at cycle 2 with 3 cap-overflow deferrals, not a CRITICAL.** The
cycle-2 rework cap was reached with findings R2 (high), R1 (medium), R7 (medium)
unresolved; `src/ovcaq/runtime/decision.py` (R2's file) was untouched by cycle 2's
rework, so `cap_regression` did not fire and no custody capture was needed. All 3
are recorded in `docs/dev/project-management/autopilot/deferred/202610272211-deferred.json`
and R2 (high) minted hold stub `00066-triage-reclassifying-429-as-rate-limit-makes-a-v1.md`.
Also carried into the same deferred JSON: 3 pre-existing `residual-finding` entries
from this PRD's work phase (default_tiers shape validation gap, a distribution-scanner
false-positive on synthetic secret fixtures, and a pre-existing ruff format failure in
a PRD-00062 file outside this PRD's review range) - none blocking, all out of scope.

Observations: the three residual-finding deferred records for 00063 were written by
the work phase without an `issue` field (only `detail`); Phase 9 step 7a's missing-item
guard caught this (exit 12) and the records were backfilled with `issue` text mirroring
`detail` before the report render succeeded. Future `/autopilot:work` residual-finding
writes should set `issue` directly to avoid this backfill step.

00057 converged at cycle 3 with no CRITICAL/HIGH surviving. Cycle-2's `contract()` live-`protocol_major` leak was fixed at `0f18ef1` and confirmed by Alice and Bob. The short-credential residual at `workflow_client.py:407` (actor-file stat size cannot establish credential length) is a settled batch-end deferral in `docs/dev/project-management/autopilot/deferred/202610272211-deferred.json` (type `residual-finding`) - do not reopen it. `./tools/check` at the PRD's close commit is NOT green: 61 failed / 8215 passed / 14 errors, every one a sandbox `/bin/ps` PermissionError under `tests/integration`/`tests/tui` (pre-existing, untouched by this PRD); `tests/workflow_client` is fully green (930 passed).

**Reinstated by the user before this batch.** 00057 had stalled at the rework cap in batch 202610251552 (3 cycles, 6 unresolved HIGH). The user moved it `hold/` -> `wip/`, removed the 00066-00072 triage stubs from `hold/`, and rewrote the PRD's Phase 1 to carry the four cycle-3 residual tasks (R2-R7) explicitly. The first-pass code is on master; these tasks correct it. Do not re-derive the residuals - the PRD task list is the contract now.

The four residual tasks: (R2) bound `_run` cleanup so a detached descendant holding stdout/stderr open cannot outlive `timeout_seconds` - new test `test_kill_group_bounded.py::run_with_detached_descendant_times_out_within_bound`; (R4, R7) classify post-spawn abnormal exits as `ApplyOutcomeUnknownError` deriving from `ControllerError` not `ControllerTimeoutError`, launch failures staying plain `ControllerError`; (R5) `_redact` must never read the actor file, so a short secret or an unreadable file still yields a redacted diagnostic; (R3, R6) one digest definition - `contract_bundle_sha256` hashes the bundle's RAW file bytes, not canonical JSON, shared by `tools/autopilot-prerequisites` and `controller_settings`, with strict bundle validation and `docs/operations.md` + `CONTROLLER_CLIENT_NOTES` parity.

**What already exists on master** (verified at `d440d98`): `src/ovcaq/workflow_client.py` (577 lines), `src/ovcaq/config.py` (662), `tools/autopilot-prerequisites`, and fifteen files under `tests/workflow_client/` - including `test_kill_group_bounded.py`, `test_apply_outcome_unknown.py`, `test_actor_secret_redaction.py` and `test_prerequisites.py`, the very files the residual tasks name. So the residuals are partly scaffolded already; planning must recheck each acceptance scenario against the tree rather than assume a blank start, and the PRD's own exit criteria say to preserve already-satisfied behavior and report conflicting edits. Working tree is clean.

**Prior batch 202610251552** drained nothing. 00062 (supervisor process identity) and 00063 (driver failure classes/tiers) are back in `backlog/`; 00062's tasks 1-6 are committed on master (`fa26fb7..97c9766`). Backlog 00058-00061, 00064 and 00065 carry `eligibility:` gates via `tools/autopilot-prerequisites` and will be skipped until their predecessors reach `done/` - which is why this batch has exactly one eligible PRD.

**Two false `systemic_park` halts (2026-10-25, 2026-10-26)** were OAuth token revocations at the ~8h expiry window, not sick PRDs; see project memory `false-park-auth-revoked`. The loop now runs on a long-lived `claude setup-token`.

## Related context

Not queried (2026-10-28 21:20Z full catchup for PRD 00063, HEAD `0bd25ed`): `autopilot catchup-probe` returned `{"skip": ["engram"]}`, so no `engram harvest`, `index`, or `query` ran for the topic `master driver failure classes and neutral default tiers`. Same gap on the seven preceding catchups. This is a gap, not a "nothing related exists" claim.

## GitHub State

**Local master is 113 commits ahead of `origin/master`, 0 behind** (re-measured 2026-10-28 21:20Z at HEAD `0bd25ed`; origin last moved 2026-10-19). Everything PRDs 00057, 00062 and 00063 produced is local only, so no CI has seen the current tree. Loop-mode pushes are deferred by design; the user pushes by hand.

`buvis/ovcaq` on GitHub, branch `master`, 0 open issues. One open PR, #1 "chore: Configure Renovate" (onboarding PR, still unmerged since 2026-10-19 - Renovate stays inactive until it is merged). No releases. Remote branches: `master` and `renovate/configure`, both last moved 2026-10-19.

Re-confirmed 2026-10-28 21:18Z: still 0 issues, still only PR #1, still no releases, and CI has still not re-run since 2026-10-19 - so every statement below is unchanged, now describing a tree 113 commits stale.

CI is **red** on both branches and has not re-run since 2026-10-19. Latest `master` failure (run 39222061763, commit `cee9b943`): **259 failed / 6879 passed / 34 skipped** in 620s, all failures one cause - `OSError: [Errno 95] exclusive lifecycle rename is unavailable` raised where `tests/workflow/test_saga_identity.py`, `test_saga_publication.py` and `test_sagas.py` expected the message `'lifecycle directory identity changed'`, plus one assertion failure in `test_workflow_cli.py::test_stall_and_park_are_public_and_reconcile_without_marker_files` (`assert 2 == 0`). Errno 95 is ENOTSUP: the CI runner's filesystem lacks the rename-exclusivity capability the lifecycle saga relies on. This predates PRD 00057 and is environment-specific, not product breakage. Commit `cf8be72` landed after that run, so whether it is still red is unknown. Not this PRD's to fix unless its own tests touch the path - but a maintainer should push and re-run CI, because 71 unpushed commits mean the red signal describes a tree nine days stale.

Branch diff and branch consumer tracing are inapplicable on master (no feature branch).

## Project Health

- **2026-10-28 21:20Z, HEAD `0bd25ed`:** working tree clean. `tests/drivers` measured green here (1877 passed, 52s) - PRD 00063's Phase 0 gate. No `./tools/check` run happened during this catchup; the sandbox `ps` residue (`tests/integration/test_terminal_lifecycle.py`) still makes a full green run unreachable from the sandbox, so use `tests/drivers`, `tests/workflow/test_configuration.py` and `tests/runtime/test_adapter_launch_routing.py` as the per-task gate for the remaining tier tasks.
- **2026-10-28 (earlier), HEAD `0f18ef1`:** working tree clean. No `./tools/check` run happened during this catchup. The last measured gate (PRD 00057's close, recorded in Active Work) was 61 failed / 8215 passed / 14 errors, every failure a sandbox `/bin/ps` PermissionError under `tests/integration`/`tests/tui`; `tests/workflow_client` was fully green at 930 passed. Expect the same shape at this HEAD and use the targeted suites (`tests/runtime`, `tests/state`) as PRD 00062's per-task gate.
- **2026-10-27, HEAD `84e10e1`:** working tree clean. `d440d98` fixed the ruff BLE001 error that had been red in `tests/workflow_client/test_kill_group_bounded.py`; no `./tools/check` run happened during this catchup, so the gate is unverified at this HEAD. `tests/integration/test_terminal_lifecycle.py` still fails in-sandbox because the seatbelt denies `/bin/ps` - use the `tests/workflow_client` suite as the per-task gate and report that residue rather than claiming a clean full run.
- **2026-10-26, HEAD `97c9766`:** `./tools/check` was then RED on a ruff BLE001 error in `tests/workflow_client/test_kill_group_bounded.py:56` - PRD 00057's own cycle-3 regression R1, tracked as hold stub 00067, not a sandbox artifact. Verify it before trusting a green gate for PRD 00063; it is in `hold/`'s deferral set, not this PRD's scope.
- PRD 00062 landed libproc-based `process_identity`, so the macOS-seatbelt `ps` wall should be gone for `tests/runtime` under its new `forbid_ps` fixture - but 00062 stalled at its rework cap with two unresolved HIGH findings, so treat that as unconfirmed rather than settled. PRD 00063's own gate (`tests/drivers`, `tests/workflow/test_configuration.py`, `tests/runtime/test_adapter_launch_routing.py`) does not depend on it.
- Remote CI is red and stale (2026-10-19, errno 95 ENOTSUP on exclusive lifecycle rename, 259 failures, one cause). Unrelated to PRD 00063 and untested since `cf8be72`; 70 local commits have never been seen by CI.
- PRD 00054 full verification at product HEAD `ab3101b`: 7251 tests passed with two pytest temporary-directory cleanup warnings; sync/lint/format/types/build all passed. No remote/live CI evidence is available.
- Current source confirms task 1 repairs: text/detail precedence, exact message identity, distinct anonymous records, and detail-only tool projection. Task 2's 26 renderer tests pass; task 3 removes the stale matched-variant and lanes-only claims. Both task 1 and task 2 retained their initial GPT implementation attempt plus bounded Astra correction with raw metadata.
- Correct observer cursor/replay, activity eviction, session/reset clearing, plan summaries and literal sanitized Text rendering must remain. Regression coverage protects these; no forced rewrites.
- Task1 is committed and complete: strengthened 54-test targeted suite passes; style/split gates are clean and tool-less Sonnet Pat reports only 3 LOW suggestions. Devon proved eight passing wrong mutants and restored production bytes exactly. Both GPT implementation attempts and raw metadata are preserved. Sandbox ps setup errors require approved narrow-test commands, never weaker fixture ownership checks.
- Task 2 has an authorized native fallback; no routing decision remains pending. Held PRDs remain outside automatic selection. Full PRD verification passed after all tasks completed; catchup ran no behavioral tests. README and repo AGENTS still describe planning/bootstrap despite the implemented package; treat that as documentation debt, not permission to alter implementation sequencing.


## Project Memories

- `sandbox-and-remote-constraints`: the seatbelt denies `/bin/ps`, so `registry.process_identity` fails in-sandbox and `ovcaq run/attach/stop` exit 2 with a `state_io` error. PRD 00062's libproc rewrite is the fix and its commits are on local master, but the PRD stalled at its rework cap, so until a green in-sandbox `tests/runtime` run proves it, treat the full suite as unverifiable from the sandbox and never stage anything under `docs/dev/project-management/` (private, gitignored in this repo by explicit exception).
- `false-park-auth-revoked`: a `wrapper_died` park of a ~5 s, 0-token session is an OAuth 401, not a sick PRD. Check `loop-metrics.jsonl` for `instant_exit` rows before trusting a park.
- The extraction source is the characterized personal `run-autopilot` implementation. Port proven behavior rather than redesigning it, while applying the accepted v1 nesting, deep-validation, revision, and directory-fsync changes.
- Current legacy state has many flat operational fields, marker files, compound task verbs, a rotating raw-byte backup, and a recoverable stall saga. PRD 00003 owns their state-schema disposition; PRD 00004 owns workflow transitions and filesystem lifecycle sagas.
- Codex/Claude launcher capabilities and marketplace work are later PRDs. PRD 00003 must not introduce launcher-specific content or hardcoded personal paths.

## Catchup execution 2026-10-10

Mandated git-ferry 0.5.0 catchup completed for 00053. Logical skill tier `sonnet` maps to the native OpenAI `gpt-6.1-sol` model at medium effort. Architecture and active PRD loaded; no production edits, launch, state mutation, or stale workflow task restoration occurred.

Catchup 00054 refreshed at the HEAD recorded above: no remotes (direct gh repo view confirmed); master history, WIP PRD, build report, canonical state, config, memories and TUI boundaries loaded. GitHub CI and issues unavailable; engram harvest/index gap recorded. No implementation, state mutation, task restoration, cleanup of evidence, or behavioral test run. Reuse follower cursor/reset, observer cap/reinsertion, display_text and literal Rich Text.
