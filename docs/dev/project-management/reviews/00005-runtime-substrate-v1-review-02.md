---
prd: dev/local/prds/wip/00005-runtime-substrate-v1.md
review: 2
date: 2026-09-26
head_sha: 666776af6ecb3baebb70e3eeb1c1b828fe64d135
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
---

# Review: 00005-runtime-substrate-v1

Diff range: `e34547e734339e31bcba89e26b3fd3cd58e99690..666776af6ecb3baebb70e3eeb1c1b828fe64d135`

codex_rung_guard: fired (18 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/reviews/00005-bob-output-c2-20260925.txt.receipt.json
autocodex_host_substitution: Fresh external Claude Bob directly supplies the non-Codex doubt voice. The gate-compatible suffix represents the explicitly authorized host substitution; no Eve/Fable dispatch or failed Eve attempt is claimed.
providers: Alice/Blake = OpenAI gpt-5.6-sol, logical sonnet, high; Bob = Anthropic claude-opus-5-5 from raw init (helper alias opus), fresh external session d0346aec-1dc5-4461-bbd3-5474bb161a31.
carl: unavailable — helper exit 3, "refusing nested dispatch (already inside a CLI agent)"; no backend/model ran. Nesting guard preserved; no unchanged retry or batch latch.
pack: unavailable — engram reported that this repository is not registered. No pack supplied.
outcome: cap_deferred

## Outcome and handoff

Cycle 2 reached the existing cap of 2. This is **completion of the review phase with deferrals**, not a clean review. There are no unresolved Critical findings. Three High findings remain: fleet-record replacement safety (C2F05), signal-cleanup composition/phase ownership (C2F06), and inconsistent state-path resolution (C2F07). The loop-mode cap rule defers unresolved findings at High or below and hands off to finalize.

- 38 consolidated findings: 21 cap-overflow deferrals (3 High, 14 Medium, 4 Low), 2 known limitations, 14 verified discards, and 1 routed verification item.
- Eight grouped follow-up records (tasks 22–29) remain unstarted. Tasks 1–21 and all their attempts remain completed and unchanged. Task counts are 21/29, reflecting these unexecuted review follow-ups.
- No production edits, commits, repair dispatch, cap increase, extra review cycle, PRD move, or finalize execution occurred in this session.
- `deferred_decisions` is the sole cap-out sink; no `autopilot defer` call was made. The next fresh finalize session owns migration to the batch deferred JSON and report.
- All reviewer processes and native agents completed and were awaited. The optional Carl failure is explicit, and all required lenses produced complete output.

The source run-autopilot Phase 5 cap branch controls this outcome. No finding was upgraded or suppressed to change that route. The reproduced fleet race loses ephemeral discovery metadata, while its authoritative lock and retained session evidence remain intact. The original active-run raw-evidence deletion proof (F50) now refuses before deletion.

## Scope and verification

Preflight: `00005-runtime-substrate-v1-preflight-2.md` records schema/count checks, source paths, provenance, and the task-to-commit mapping. The context contained 21 individual task rows with their full descriptions and attempt history; original task coverage remains in review-01.md and repairs 12–21 have individual rows in preflight-2.md.

The review covers all 28 files changed since cycle 1. Alice received implementation context and the design. Blake received only the PRD, rubric, and its mandatory requirements sources. Bob received PRD/diff/mechanical evidence without the design document, plus the full installed persona, doubt/de-slop appendix, D1–D5 rubric, previous findings, and settled ledger.

Verification reused `last-verification.json` at exactly `666776af6ecb3baebb70e3eeb1c1b828fe64d135`: 2015 tests passed, 0 failed, 0 skipped; sync, Ruff lint/format, mypy, and build all exited 0. No redundant full-suite run occurred.

Mechanical AST facts and shape checks ran before dispatch. The shape detector reported no findings. After an approved retry for sandbox-blocked Git metadata writes, the isolated base replay ran 267 touched cases: 113 failed, 154 passed, and three files could not collect at base. All nine MECH rows are included below and dispositioned against the changed tests. The temporary worktree was removed. The original proof was rerun with its expected ActiveSessionError explicitly handled.

Additional synthetic-only review proofs:
- `00005_fleet_remove_race_proof_2.py`: replacement live fleet entry was deleted and remove returned success; `00005-fleet-remove-race-result-2.json`.
- `00005_runtime_resolution_proof_2.py`: diagnostics selected external state while workflow/state defaults stayed project-local; doctor immediately after init reported unhealthy missing sessions directory; `00005-runtime-resolution-result-2.json`.

Bob receipt scope, output SHA-256 and immutable raw JSONL SHA-256 all verified. Raw model init identifies `claude-opus-5-5`; no stale `codex_thread_id` is emitted.

## Consolidation accounting

The installed script ran successfully; its unmodified output is preserved in `00005-runtime-substrate-v1-consolidation-raw-2.md`. Coordinator consolidation corrected its over-merge of Bob's state-resolution defect with the separate path-error-message issue, and merged four explicit duplicate pairs: private dataclass comparison, F31 directory creation duplication, dead exception catch, and oversized test file. All 33 raw issue lines map to 29 reviewer findings; nine mechanical rows bring the total to 38. No reviewer line or rubric verdict was dropped.

| ID | Consensus | Severity | Finding | File | Found by | Disposition |
|---|---|---|---|---|---|---|
| C2F01 | [2/3] | 🟡 medium | `RuntimePaths._identities` remains a comparison field, so two objects with identical public contract fields compare unequal when their private filesystem snapshots differ; declare it with `compare=False` | src/ovcaq/paths.py:169 | ALICE, BOB | cap-overflow |
| C2F02 | [2/3] | 🟡 medium | F31 remains: `_private_directory` still duplicates the two path-layout creators and creates every missing ancestor with mode `0700`; consolidate the descriptor-walk primitive so intermediate project directories retain the established layout policy | src/ovcaq/runtime/session.py:193 | ALICE, BOB | cap-overflow |
| C2F03 | [2/3] | 🟡 medium | `_state_attention` still catches `EmergencyStateFailure`, which `acknowledge_emergency_failure` cannot raise, leaving the dead exception branch and import identified by F38 | src/ovcaq/runtime_cli.py:142 | ALICE, BOB | cap-overflow |
| C2F04 | [2/3] | 🟡 medium | The rework expanded `test_runtime_cli.py` from 666 to 1234 lines, violating the 800-line limit; split status/doctor, log, purge, and emergency command tests into focused modules | tests/runtime/test_runtime_cli.py:1 | ALICE, BOB | cap-overflow |
| C2F05 | [1/3] | 🟠 high | Fleet entry reads are not identity-bound to deletion: `_scan` records a pre-open inode without comparing it to the opened descriptor, while `remove` validates contents and then unlinks the pathname without rechecking its inode; a replacement during either gap can make prune delete a live record or remove delete a new owner’s record | src/ovcaq/runtime/registry.py:317 | ALICE | cap-overflow |
| C2F06 | [1/3] | 🟠 high | Signal handling only raises an exception; no production runtime path composes group termination, outcome recording, registry cleanup, and lock release, leaving P03-T10’s centralized cleanup contract unimplemented | src/ovcaq/runtime/process.py:50 | BLAKE | cap-overflow |
| C2F07 | [1/3] | 🟠 high | Three code paths now pick the state file differently. `workflow_settings` reads a new, undocumented `[workflow] state_file` key (config.py:117) and ignores `[runtime] external_state_root`. `status`, `doctor` and `--acknowledge-emergency` use `runtime_settings`, which honors the external root and ignores `state_file`. `init` and `state` use `state_path(root)` (cli.py:426). With either key set, doctor reports state "missing", and acknowledgement can accept a different file than the one workflow commands write (confirmed by reading). The PRD's explicit external-root behavior is still not met. | src/ovcaq/config.py:117 | BOB | cap-overflow |
| C2F08 | [1/3] | 🟡 medium | `status` still emits only `run.status`, so the concrete failure retained in `RunObservation.detail` is unavailable when status reports `inconsistent`; F28 remains observable even though doctor exposes the reason | src/ovcaq/runtime_cli.py:312 | ALICE | cap-overflow |
| C2F09 | [1/3] | 🟡 medium | Emergency decoding still reimplements the shared bounded duplicate-key-safe JSON decoder with `json.loads` and `_emergency_fields`; use `decode_json` directly and remove the duplicate parser | src/ovcaq/runtime/session.py:431 | ALICE | cap-overflow |
| C2F10 | [1/3] | 🟡 medium | Runtime-root precedence merges internal and external choices independently, so a lower-priority user external root conflicts with a higher-priority project or explicit internal root instead of being overridden | src/ovcaq/config.py:214 | BLAKE | cap-overflow |
| C2F11 | [1/3] | 🟡 medium | Process identity uses `ps lstart` with one-second precision, so a PID recycled within the same second can be misclassified as the original process and escape stale-entry pruning | src/ovcaq/runtime/registry.py:109 | BLAKE | cap-overflow |
| C2F12 | [1/3] | 🟡 medium | A `ps` timeout raises uncaught `subprocess.TimeoutExpired`, allowing registry discovery and `status`/`doctor` to traceback instead of producing degraded diagnostics | src/ovcaq/runtime/registry.py:109 | BLAKE | cap-overflow |
| C2F13 | [1/3] | 🟡 medium | `status` embeds `datetime.now()` in its purge preview, so unchanged runtime/state data produces different output despite the required deterministic status contract | src/ovcaq/runtime_cli.py:303 | BLAKE | cap-overflow |
| C2F14 | [1/3] | 🟡 medium | `doctor` reports `ok: false` on every newly initialized project. `_directory_health` stats `paths.sessions`, but `init` creates only `dev/local/ovcaq`, and only `create_session` creates `sessions`. The resulting FileNotFoundError fills both the `permissions` and `writability` checks with the error text. Every ok=True test runs `ensure_runtime_layout` first, so none catches this (confirmed by reading). | src/ovcaq/runtime_cli.py:201 | BOB | cap-overflow |
| C2F15 | [1/3] | 🟡 medium | The F14 fix landed on `_runtime_timestamp`, which after the refactor only parses `logs purge --before`. Cutoffs with an offset (valid RFC3339, the metavar) are now rejected as usage errors. No test covers this, and the validator label says `metadata.started_at` (metadata already goes through `parse_session_metadata`). | src/ovcaq/cli_io.py:84 | BOB | cap-overflow |
| C2F16 | [1/3] | 🟡 medium | `cleanup_run_records` turns every OSError, ValueError and TypeError into `False`. A caller cannot tell "record belongs to another run" from "unlink or fsync failed", and the cause is lost. | src/ovcaq/runtime/session.py:370 | BOB | cap-overflow |
| C2F17 | [1/3] | 🟡 medium | `_acquire_purge_locks` re-implements `RunLock.acquire`: O_NOFOLLOW open, S_ISREG check, LOCK_NB flock, samestat recheck, fchmod. Simpler: add `directory: int \| None = None` to `RunLock.acquire` (as `run_lock_held` already has) and map DuplicateRunError to ActiveSessionError for run.lock. | src/ovcaq/runtime/_retention.py:343 | BOB | cap-overflow |
| C2F18 | [1/3] | 🟡 medium | 7 touched test(s) pass against the pre-change code: test_internal_resolution_refuses_existing_symlink_descendants, test_configuration_refuses_symlink_files_with_arbitrary_targets +1 more | tests/runtime/test_paths.py | mech-check | discarded |
| C2F19 | [1/3] | 🟡 medium | 11 touched test(s) pass against the pre-change code: test_spawn_rejects_invalid_argv_before_starting_any_process +5 more | tests/runtime/test_process.py | mech-check | discarded |
| C2F20 | [1/3] | 🟡 medium | 31 touched test(s) pass against the pre-change code: test_rejects_nonbytes_without_changing_evidence, test_rejects_invalid_limits +25 more | tests/runtime/test_raw_session.py | mech-check | discarded |
| C2F21 | [1/3] | 🟡 medium | 1 touched test(s) pass against the pre-change code: test_inode_substitution_during_acquisition_fails_and_releases_old_inode | tests/runtime/test_registry.py | mech-check | discarded |
| C2F22 | [1/3] | 🟡 medium | 25 touched test(s) pass against the pre-change code: test_invalid_selectors_fail_without_mutating_evidence +19 more | tests/runtime/test_retention.py | mech-check | discarded |
| C2F23 | [1/3] | 🟡 medium | 25 touched test(s) pass against the pre-change code: test_purge_rejects_parent_log_options_without_removing_evidence, test_runtime_readers_reject_unsafe_ids_non_utc_times_and_empty_required_strings +19 more | tests/runtime/test_runtime_cli.py | mech-check | discarded |
| C2F24 | [1/3] | 🟡 medium | 34 touched test(s) pass against the pre-change code: test_failed_state_notice_publishes_private_synced_marker_and_persistent_gate, test_invalid_failure_diagnostics_are_rejected_without_publishing_marker +28 more | tests/runtime/test_session_emergency.py | mech-check | discarded |
| C2F25 | [1/3] | 🟡 medium | 16 touched test(s) pass against the pre-change code: test_rejects_invalid_durations_before_starting_a_worker +10 more | tests/runtime/test_watchdog.py | mech-check | discarded |
| C2F26 | [1/3] | 🟡 medium | 4 touched test(s) pass against the pre-change code: test_configured_runtime_preserves_containment_and_symlink_refusal, test_workflow_paths_accept_contained_explicit_and_configured_values | tests/workflow/test_configuration.py | mech-check | discarded |
| C2F27 | [1/3] | ⚪ low | The CLI adds unlisted `doctor --acknowledge-emergency` and `logs purge --session` options, expanding both the interface and destructive purge behavior beyond the specified command surface | src/ovcaq/cli.py:167 | BLAKE | discarded |
| C2F28 | [1/3] | ⚪ low | `cleanup_run_records` removes the fleet entry before `run.json`. If that unlink fails, or the entry is already gone, `remove()` returns False on every retry. `run.json` is then stranded and `status` stays inconsistent until the next run overwrites it. | src/ovcaq/runtime/session.py:361 | BOB | cap-overflow |
| C2F29 | [1/3] | ⚪ low | A second concurrent `logs purge --apply` is refused with "cannot purge while a run is active", because run.lock is taken first. That message is wrong for this case. retention.lock can never be the contended lock, since its only taker already holds run.lock. If it ever were contended, its DuplicateRunError (a RuntimeError) would escape `_dispatch_logs` and `main` as a traceback. | src/ovcaq/runtime/_retention.py:363 | BOB | cap-overflow |
| C2F30 | [1/3] | ⚪ low | The `command` field means opposite things in two outputs. In `status` and `doctor`, `purge_preview.command` removes `--apply` with `plan.command[:-1]`. In `logs purge` output, `command` keeps `--apply`. The slice also silently depends on `--apply` being the last argument. | src/ovcaq/runtime_cli.py:305 | BOB | discarded |
| C2F31 | [1/3] | ⚪ low | `Watchdog.join` signals "worker still running" with the builtin `TimeoutError`, which is a subclass of `OSError`. Broad `except OSError` handlers, such as the one in `cli.main`, would report it as an I/O failure. | src/ovcaq/runtime/watchdog.py:75 | BOB | discarded |
| C2F32 | [1/3] | ⚪ low | `workflow_settings` validates the PRD root and the state file with `runtime_directory`. Rejections therefore say "derived runtime path escapes project root" even when the path is a PRD root or a state file. | src/ovcaq/config.py:106 | BOB | cap-overflow |
| C2F33 | [1/3] | ⚪ low | The rewritten CHANGELOG Added bullets list implementation details ("identity-pinned fleet records behind inode-stable run locks without launch contention") rather than what the user sees. | CHANGELOG.md:20 | BOB | cap-overflow |
| C2F34 | [1/3] | ⚪ low | In the fail-first replay, 154 touched tests pass against the pre-change code. Most are expected, because they cover code that was only moved or refactored. It is not confirmed that this cycle's new-behavior tests fail at the base. | N/A | BOB | routed-verification |
| C2F35 | [1/3] | ⚪ low | Emergency acknowledgement publishes and fsyncs a full archive copy (`_archive_emergency_evidence`), then deletes it on success at session.py:582. The rename plus link-back already keeps the evidence reachable. | src/ovcaq/runtime/session.py:582 | BOB | settled-deferral |
| C2F36 | [1/3] | ⚪ low | On normal exit, surviving descendants get an immediate SIGKILL with no TERM grace, so they cannot flush. The PRD describes TERM, then grace, then KILL. | src/ovcaq/runtime/process.py:154 | BOB | settled-deferral |
| C2F37 | [1/3] | ⚪ low | `run_lock_held` raises on any platform other than darwin. On Linux, `status` and `doctor` will report `inconsistent` whenever run.lock exists. | src/ovcaq/runtime/registry.py:40 | BOB | discarded |
| C2F38 | [1/3] | ⚪ low | `_read_config` refuses a symlinked user `~/.config/ovcaq` directory or `config.toml` file below the trusted anchor. That breaks stow-style dotfile setups. | src/ovcaq/config.py:44 | BOB | discarded |

## Decisions and unresolved items

Every decision is persisted through the state CLI and in `00005-cycle-02-decisions.json`. Every discard or deferral is also recorded in the settled ledger using the finding's own text.

- **C2F01 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F02 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F03 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F04 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F05 — cap-overflow:** rework cap reached with this finding unresolved; replacement live-entry deletion reproduced with synthetic data in 00005_fleet_remove_race_proof_2.py. This loses discovery metadata; the authoritative run lock and retained session evidence remain intact.
- **C2F06 — cap-overflow:** rework cap reached with this finding unresolved; the source plan section 12.2 requires composed cleanup, while this PRD/design expose primitives and delegate composition to their caller. Preserve the scope ambiguity for operator triage; do not opportunistically implement the later supervisor.
- **C2F07 — cap-overflow:** rework cap reached with this finding unresolved; 00005_runtime_resolution_proof_2.py confirms runtime diagnostics select external/state.json while workflow/state defaults remain project-local.
- **C2F08 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F09 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F10 — cap-overflow:** rework cap reached with this finding unresolved; per-key merging and mutually exclusive root selectors conflict across layers. Preserve the exact precedence question for repair.
- **C2F11 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F12 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F13 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F14 — cap-overflow:** rework cap reached with this finding unresolved; isolated init-then-doctor reproduction confirms missing sessions directory makes permission/writability checks fail.
- **C2F15 — cap-overflow:** rework cap reached with this finding unresolved; cutoff input uses the strict UTC metadata parser despite RFC3339 labeling. Preserve both the behavior and misleading label for API-contract triage.
- **C2F16 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F17 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F18 — discarded:** Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.
- **C2F19 — discarded:** Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.
- **C2F20 — discarded:** Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.
- **C2F21 — discarded:** Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.
- **C2F22 — discarded:** Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.
- **C2F23 — discarded:** Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.
- **C2F24 — discarded:** Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.
- **C2F25 — discarded:** Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.
- **C2F26 — discarded:** Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.
- **C2F27 — discarded:** The accepted PRD design explicitly specifies both flags as refinements of explicit session purge and emergency recovery; no automatic destructive action or out-of-scope product capability was added. The source command table is not an exhaustive flag inventory.
- **C2F28 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F29 — cap-overflow:** rework cap reached with this finding unresolved; preserve the inaccurate contention diagnostic and uncaught retention-lock exception, but do not remove the retention lock required for future aggregate writers.
- **C2F30 — discarded:** Status/doctor intentionally expose a safe preview command, while explicit purge outputs the documented apply argv. PurgePlan's accepted contract pins --apply last, so slicing that suffix is not an unverified assumption.
- **C2F31 — discarded:** TimeoutError correctly represents a timed wait; no current production CLI path invokes Watchdog.join. A possible future broad OSError handler is hypothetical and does not justify a new exception API here.
- **C2F32 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F33 — cap-overflow:** rework cap reached with this finding unresolved
- **C2F34 — routed-verification:** Routed to the exact named project verification command. No work pass runs on the cap-out path, so this check remains unrun. Bob's stated base-worktree and expected-failure interpretation is retained as context; ordinary current-HEAD exit zero alone would not establish that stronger claim.
- **C2F35 — settled-deferral:** The archive copy is deliberate recovery evidence used by failure-path tests. Removing it is a behavior/design change outside this repair; preserve Bob's KNOWN qualification.
- **C2F36 — settled-deferral:** The previous repair deliberately chose immediate owned-group cleanup after normal agent exit. Adding descendant TERM grace requires a policy/API decision; preserve this KNOWN limitation for later operator triage.
- **C2F37 — discarded:** The PRD explicitly limits this milestone to macOS and assigns Linux support to a later release gate; reporting unsupported observation is expected.
- **C2F38 — discarded:** The accepted trust-boundary repair deliberately resolves the chosen XDG anchor while refusing symlink descendants and config files. Relaxing that tested safety contract is not an automatic fix.

## Follow-up records (unstarted)

| Task | Subject | Finding IDs |
|---|---|---|
| 22 | [C2] Preserve fleet ownership and bounded identity diagnostics (L) | C2F05, C2F11, C2F12 |
| 23 | [C2] Resolve signal cleanup ownership at the substrate boundary (M) | C2F06 |
| 24 | [C2] Unify configured state paths and root precedence (L) | C2F07, C2F10, C2F32 |
| 25 | [C2] Correct initial and deterministic runtime diagnostics (M) | C2F08, C2F13, C2F14 |
| 26 | [C2] Finish bounded runtime and test cleanup (M) | C2F01, C2F02, C2F03, C2F04, C2F09, C2F17, C2F33 |
| 27 | [C2] Reconcile purge cutoff parsing and its public contract (S) | C2F15 |
| 28 | [C2] Make owner cleanup observable and retryable (M) | C2F16, C2F28 |
| 29 | [C2] Report purge lock contention safely (S) | C2F29 |

These are review records, not a queued rework batch; `rework_task_ids` remains empty. No task tier escalation or implementor dispatch is claimed. A briefly staged duplicate verification task was withdrawn before handoff to obey the mandatory VERIFY routing rule; its withdrawal record is retained.

## Verification-check queue

`00005-runtime-substrate-v1-checks-2.json` holds Bob's exact five-case pytest command for C2F34. This cap-out has no work pass, so the queue remains **unrun**, as the skill explicitly permits. The original request requires a base worktree with HEAD tests overlaid and expects failures; that precondition and interpretation are retained alongside the command. A later current-HEAD pass alone must not be presented as the stronger fail-first evidence. The previous queue was empty, so no failed check was carried forward.

## Alice

Isolated native OpenAI gpt-5.6-sol; logical sonnet; high; agent /root/alice_cycle2. Full raw response retained in `00005-alice-output-c2-20260925.txt`.

[ALICE] 🟠 Fleet entry reads are not identity-bound to deletion: `_scan` records a pre-open inode without comparing it to the opened descriptor, while `remove` validates contents and then unlinks the pathname without rechecking its inode; a replacement during either gap can make prune delete a live record or remove delete a new owner’s record | File: src/ovcaq/runtime/registry.py:317 | Task: 13
[ALICE] 🟡 `RuntimePaths._identities` remains a comparison field, so two objects with identical public contract fields compare unequal when their private filesystem snapshots differ; declare it with `compare=False` | File: src/ovcaq/paths.py:169 | Task: 18
[ALICE] 🟡 F31 remains: `_private_directory` still duplicates the two path-layout creators and creates every missing ancestor with mode `0700`; consolidate the descriptor-walk primitive so intermediate project directories retain the established layout policy | File: src/ovcaq/runtime/session.py:193 | Task: 16
[ALICE] 🟡 `status` still emits only `run.status`, so the concrete failure retained in `RunObservation.detail` is unavailable when status reports `inconsistent`; F28 remains observable even though doctor exposes the reason | File: src/ovcaq/runtime_cli.py:312 | Task: 17
[ALICE] 🟡 Emergency decoding still reimplements the shared bounded duplicate-key-safe JSON decoder with `json.loads` and `_emergency_fields`; use `decode_json` directly and remove the duplicate parser | File: src/ovcaq/runtime/session.py:431 | Task: 20
[ALICE] 🟡 `_state_attention` still catches `EmergencyStateFailure`, which `acknowledge_emergency_failure` cannot raise, leaving the dead exception branch and import identified by F38 | File: src/ovcaq/runtime_cli.py:142 | Task: 18
[ALICE] 🟡 The rework expanded `test_runtime_cli.py` from 666 to 1234 lines, violating the 800-line limit; split status/doctor, log, purge, and emergency command tests into focused modules | File: tests/runtime/test_runtime_cli.py:1 | Task: 21
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
R13: fail

Prior findings resolved with concrete implementation or regression coverage: F01, F02/F33, F03, F04, F05, F06, F08, F09, F11/F26, F12, F13, F14, F15, F16, F17, F19, F20, F21, F22, F23/F47, F24, F32, F34, F35, F36, F37, F39, F41, F42, F44, and F50.

Prior findings unresolved or only partially resolved: F07/F10/F30, F25, F28, F29, F31, and F38, as detailed above.

Settled decisions remain unchanged: F18/F48, F40, and F49 are discarded; F27, F43, F45, and F46 remain deferred. Exact-HEAD evidence reports 2015 passing tests, zero skipped tests, and successful Ruff, formatting, mypy, and build checks.

## Blake

Isolated native OpenAI gpt-5.6-sol; logical sonnet; high; agent /root/blake_cycle2. Full raw response retained in `00005-blake-output-c2-20260925.txt`.

[BLAKE] 🟠 Signal handling only raises an exception; no production runtime path composes group termination, outcome recording, registry cleanup, and lock release, leaving P03-T10’s centralized cleanup contract unimplemented | File: src/ovcaq/runtime/process.py:50 | Task: general
[BLAKE] 🟡 Runtime-root precedence merges internal and external choices independently, so a lower-priority user external root conflicts with a higher-priority project or explicit internal root instead of being overridden | File: src/ovcaq/config.py:214 | Task: general
[BLAKE] 🟡 Process identity uses `ps lstart` with one-second precision, so a PID recycled within the same second can be misclassified as the original process and escape stale-entry pruning | File: src/ovcaq/runtime/registry.py:109 | Task: general
[BLAKE] 🟡 A `ps` timeout raises uncaught `subprocess.TimeoutExpired`, allowing registry discovery and `status`/`doctor` to traceback instead of producing degraded diagnostics | File: src/ovcaq/runtime/registry.py:109 | Task: general
[BLAKE] 🟡 `status` embeds `datetime.now()` in its purge preview, so unchanged runtime/state data produces different output despite the required deterministic status contract | File: src/ovcaq/runtime_cli.py:303 | Task: general
[BLAKE] ⚪ The CLI adds unlisted `doctor --acknowledge-emergency` and `logs purge --session` options, expanding both the interface and destructive purge behavior beyond the specified command surface | File: src/ovcaq/cli.py:167 | Task: general
B1: fail
B2: pass
B3: fail
B4: pass
B5: fail
B6: fail
B7: fail
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: fail
B17: fail
B18: pass
B19: pass

## Bob

Fresh external Anthropic claude-opus-5-5, logical opus, exact host helper. Full raw text and receipt retained under `00005-bob-output-c2-20260925.txt*`; raw JSONL/stderr remain immutable. All raw R and D verdicts below are preserved. Bob's proposed next rework is advisory; committed cap policy controls orchestration.

### Bob: incremental review of 00005 cycle 2 (e34547e..666776a)

#### Prior findings

- **Resolved:** F01, F02, F03, F04, F06, F07, F08, F12, F13, F14, F15, F16, F17, F19, F20, F21 (`session.py` is now 702 lines), F22, F23, F24, F28, F29, F32, F34, F36, F37, F39, F41, F42, F44, F50.
- **Resolved, but the fix caused a new problem:** F05 (see #2), F09 (containment is in, but external-root semantics are not; see #1), F35 (all functions are 50 lines or fewer, but a test file now breaks the size limit; see #6).
- **Present but not wired in:** F11. `cleanup_run_records` exists but nothing calls it yet. That is expected for a substrate PRD.
- **Partly resolved:** F25 (#11), F38 (#10).
- **Still open:** F31 (#7).
- **Settled rows, not re-raised:** F18/F48, F27, F40, F43, F45, F46, F49.

#### Issues

```
[BOB] 🟠 Three code paths now pick the state file differently. `workflow_settings` reads a new, undocumented `[workflow] state_file` key (config.py:117) and ignores `[runtime] external_state_root`. `status`, `doctor` and `--acknowledge-emergency` use `runtime_settings`, which honors the external root and ignores `state_file`. `init` and `state` use `state_path(root)` (cli.py:426). With either key set, doctor reports state "missing", and acknowledgement can accept a different file than the one workflow commands write (confirmed by reading). The PRD's explicit external-root behavior is still not met. | File: src/ovcaq/config.py:117 | Task: 15
[BOB] 🟡 `doctor` reports `ok: false` on every newly initialized project. `_directory_health` stats `paths.sessions`, but `init` creates only `dev/local/ovcaq`, and only `create_session` creates `sessions`. The resulting FileNotFoundError fills both the `permissions` and `writability` checks with the error text. Every ok=True test runs `ensure_runtime_layout` first, so none catches this (confirmed by reading). | File: src/ovcaq/runtime_cli.py:201 | Task: 17
[BOB] 🟡 The F14 fix landed on `_runtime_timestamp`, which after the refactor only parses `logs purge --before`. Cutoffs with an offset (valid RFC3339, the metavar) are now rejected as usage errors. No test covers this, and the validator label says `metadata.started_at` (metadata already goes through `parse_session_metadata`). | File: src/ovcaq/cli_io.py:84 | Task: 16
[BOB] 🟡 `cleanup_run_records` turns every OSError, ValueError and TypeError into `False`. A caller cannot tell "record belongs to another run" from "unlink or fsync failed", and the cause is lost. | File: src/ovcaq/runtime/session.py:370 | Task: 19
[BOB] 🟡 `_acquire_purge_locks` re-implements `RunLock.acquire`: O_NOFOLLOW open, S_ISREG check, LOCK_NB flock, samestat recheck, fchmod. Simpler: add `directory: int | None = None` to `RunLock.acquire` (as `run_lock_held` already has) and map DuplicateRunError to ActiveSessionError for run.lock. | File: src/ovcaq/runtime/_retention.py:343 | Task: 12
[BOB] 🟡 `tests/runtime/test_runtime_cli.py` grew by 594 lines this cycle to 1234, over the 800-line file limit. | File: tests/runtime/test_runtime_cli.py | Task: 21
[BOB] 🟡 F31 is still open. `ensure_runtime_layout` has no production caller (only the test `_session` helper uses it), and it duplicates `_private_directory` and `ensure_runtime_directory`. Calling it from `init` would also fix the doctor-after-init bug above. | File: src/ovcaq/paths.py:239 | Task: 16
[BOB] ⚪ `cleanup_run_records` removes the fleet entry before `run.json`. If that unlink fails, or the entry is already gone, `remove()` returns False on every retry. `run.json` is then stranded and `status` stays inconsistent until the next run overwrites it. | File: src/ovcaq/runtime/session.py:361 | Task: 19
[BOB] ⚪ A second concurrent `logs purge --apply` is refused with "cannot purge while a run is active", because run.lock is taken first. That message is wrong for this case. retention.lock can never be the contended lock, since its only taker already holds run.lock. If it ever were contended, its DuplicateRunError (a RuntimeError) would escape `_dispatch_logs` and `main` as a traceback. | File: src/ovcaq/runtime/_retention.py:363 | Task: 12
[BOB] ⚪ F38 is only partly fixed. `_state_attention` still catches `EmergencyStateFailure`, which `acknowledge_emergency_failure` never raises. | File: src/ovcaq/runtime_cli.py:142 | Task: 18
[BOB] ⚪ F25 is only partly fixed. `RuntimePaths._identities` is hidden from output but still takes part in `==` and hashing, because the field has no `compare=False`. | File: src/ovcaq/paths.py:169 | Task: 18
[BOB] ⚪ The `command` field means opposite things in two outputs. In `status` and `doctor`, `purge_preview.command` removes `--apply` with `plan.command[:-1]`. In `logs purge` output, `command` keeps `--apply`. The slice also silently depends on `--apply` being the last argument. | File: src/ovcaq/runtime_cli.py:305 | Task: 18
[BOB] ⚪ `Watchdog.join` signals "worker still running" with the builtin `TimeoutError`, which is a subclass of `OSError`. Broad `except OSError` handlers, such as the one in `cli.main`, would report it as an I/O failure. | File: src/ovcaq/runtime/watchdog.py:75 | Task: 14
[BOB] ⚪ `workflow_settings` validates the PRD root and the state file with `runtime_directory`. Rejections therefore say "derived runtime path escapes project root" even when the path is a PRD root or a state file. | File: src/ovcaq/config.py:106 | Task: 15
[BOB] ⚪ The rewritten CHANGELOG Added bullets list implementation details ("identity-pinned fleet records behind inode-stable run locks without launch contention") rather than what the user sees. | File: CHANGELOG.md:20 | Task: 21
[BOB] ⚪ In the fail-first replay, 154 touched tests pass against the pre-change code. Most are expected, because they cover code that was only moved or refactored. It is not confirmed that this cycle's new-behavior tests fail at the base. | File: N/A | Task: general
[BOB] ⚪ Emergency acknowledgement publishes and fsyncs a full archive copy (`_archive_emergency_evidence`), then deletes it on success at session.py:582. The rename plus link-back already keeps the evidence reachable. | File: src/ovcaq/runtime/session.py:582 | Task: 20
[BOB] ⚪ On normal exit, surviving descendants get an immediate SIGKILL with no TERM grace, so they cannot flush. The PRD describes TERM, then grace, then KILL. | File: src/ovcaq/runtime/process.py:154 | Task: 14
[BOB] ⚪ `run_lock_held` raises on any platform other than darwin. On Linux, `status` and `doctor` will report `inconsistent` whenever run.lock exists. | File: src/ovcaq/runtime/registry.py:40 | Task: general
[BOB] ⚪ `_read_config` refuses a symlinked user `~/.config/ovcaq` directory or `config.toml` file below the trusted anchor. That breaks stow-style dotfile setups. | File: src/ovcaq/config.py:44 | Task: 15
```

#### Buckets

FIX:
- State-file resolution split: src/ovcaq/config.py:117. Drop the `[workflow] state_file` key (F09 asked for containment, not a new key). Resolve the workflow state file from the same `RuntimePaths` (including `external_state_root`) that `runtime_settings` builds, and use it in `init`/`state` too.
- Doctor fails after init: src/ovcaq/runtime_cli.py:201. Call `ensure_runtime_layout` from `init`, or treat a missing `sessions` directory as healthy. Add a test that runs doctor right after init.
- `--before` rejects offsets: src/ovcaq/cli_io.py:84. Accept any timezone-aware RFC3339 cutoff again (the metadata path is already strict), or document UTC-only with a test. Fix the label either way.
- `cleanup_run_records` hides errors: src/ovcaq/runtime/session.py:370. Return False only for an ownership mismatch and let I/O errors raise.
- Duplicate lock code: src/ovcaq/runtime/_retention.py:343. Add a `directory` parameter to `RunLock.acquire` and reuse it.
- Test file over 800 lines: tests/runtime/test_runtime_cli.py. Split the doctor/emergency tests and the logs/purge tests into their own modules.
- F31: src/ovcaq/paths.py:239. Give `ensure_runtime_layout` a production caller (`init`) or move it into test support.
- Cleanup cannot be retried: src/ovcaq/runtime/session.py:361. Treat an already-absent matching fleet entry as removed.
- Concurrent purge: src/ovcaq/runtime/_retention.py:363. Catch DuplicateRunError in `_dispatch_logs` and say "run or purge in progress", or drop the redundant retention lock.
- F38 leftover: src/ovcaq/runtime_cli.py:142. Remove `EmergencyStateFailure` from the except tuple.
- F25 leftover: src/ovcaq/paths.py:169. Add `compare=False` to the `_identities` field.
- Preview command: src/ovcaq/runtime_cli.py:305. Build the preview command explicitly (`_purge_payload(plan, applied=..., preview=True)`) instead of slicing.
- Watchdog timeout: src/ovcaq/runtime/watchdog.py:75. Raise a dedicated exception that is not an OSError (a RuntimeError subclass).
- Error messages: src/ovcaq/config.py:106. Pass a label so PRD-root and state-file rejections name the right thing.
- Changelog: CHANGELOG.md:20. Rewrite the bullets as short statements of what the user sees.

VERIFY:
- Fail-first replay. In a worktree at e34547e with HEAD's tests overlaid, run `mise exec -- uv run pytest tests/runtime/test_session_emergency.py::test_failed_acknowledgement_preserves_or_restores_canonical_blocking_evidence tests/runtime/test_session_emergency.py::test_marker_replacement_during_acknowledgement_preserves_new_failure_and_gate tests/runtime/test_retention.py::test_purge_retains_oversized_newline_free_evidence_using_bounded_reads tests/runtime/test_retention.py::test_runtime_root_swap_cannot_bypass_the_original_live_run_lock tests/runtime/test_watchdog.py::test_join_times_out_during_pending_signal_and_returns_only_after_last_delivery`. Each one must fail.

KNOWN:
- Redundant archive copy: the failure-path tests deliberately expect both archives to remain. Removing the copy changes which files exist, so it is a design change, not a repair.
- SIGKILL without grace on normal exit: this was the chosen F02 direction. `term_grace_seconds` is not passed into `OwnedProcess`, and grace for orphans is a policy decision outside this rework.
- `run_lock_held` is macOS-only: the PRD makes macOS the personal-cutover target and Linux a later release gate.
- User-config symlink refusal: this is a deliberate, tested posture (`test_configuration_refuses_symlink_*`). Relaxing it is a security-policy decision, not a defect fix.

#### Rubric verdicts

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
R13: fail

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

---
**Status:** Done. This review found 20 issues: 1 🟠, 6 🟡, 13 ⚪. They split into 15 FIX, 1 VERIFY and 4 KNOWN. Every point was checked by reading the code only; nothing was executed.
**Next:** the coordinator merges these into the cycle-2 table and sends the 🟠 state-file split and the 🟡 doctor-after-init bug to rework first.

## Archived review inputs

All 12 cycle-local staging files were moved byte-for-byte from `dev/local/tmp/` into `00005-cycle-02-inputs/`. Its `manifest.json` maps every original absolute path (including the paths embedded in immutable prompts) to its durable archive path and SHA-256. Bob output, raw JSONL, stderr, and receipt remain at their original durable paths. No other session's staging files or evidence were removed. The accepted umbrella implementation plan remains active and was retained.

## Final record

Verdict: 38 findings
Tests: 2015 passed, 0 failed, 0 skipped (reused from last-verification.json at 666776af6ecb3baebb70e3eeb1c1b828fe64d135)

