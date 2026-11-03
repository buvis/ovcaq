---
prd: dev/local/prds/wip/00005-runtime-substrate-v1.md
review: 1
date: 2026-09-14
head_sha: e34547e734339e31bcba89e26b3fd3cd58e99690
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
---

# Review: 00005-runtime-substrate-v1

Diff range: `2742c08fe5f8194f65a36fa1e49a5980d69c16ef..e34547e734339e31bcba89e26b3fd3cd58e99690`

codex_rung_guard: fired (11 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude
autocodex_bob_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/dev/local/reviews/00005-bob-output-c1-20260914.txt.receipt.json
autocodex_host_substitution: Claude Bob directly supplies the non-Codex doubt voice; the gate-compatible fallback suffix records this authorized substitution. Eve/Fable was not dispatched, and no failed Eve dispatch is claimed.
providers: Alice and Blake = OpenAI gpt-5.6-sol (logical sonnet, high); Bob = Anthropic claude-opus-5 (helper model alias opus, xhigh), fresh external session.
carl: unavailable — helper exit 3, "refusing nested dispatch (already inside a CLI agent)"; no backend/model ran. Guard preserved; no unchanged retry or batch latch.
pack: unavailable — engram says this repository is not registered. No pack supplied to any reviewer.

## Outcome

PAUSED for detected data-loss risk. No production code was changed in this review session, and no rework was dispatched. The existing cycle and cap remain 1/2. Original build tasks remain 11/11 complete; ten review follow-ups are pending as tasks 12–21. Creating these tasks does not authorize clearing the pause or starting them.

The installed run-autopilot SKILL.md Error Handling row mandates **Detected data-loss risk → PAUSE**. It takes precedence over cap deferral and routine rework. The operator must authorize interactive recovery before repairs. The PRD stays in wip; no convergence marker or finalize handoff is appropriate.

## Confirmed data-loss proof

F50 is a coordinator reproduction using only synthetic files in a TemporaryDirectory. `apply_purge` opens the original runtime directory, then takes locks via the still-mutable absolute pathname. If the runtime directory is moved and replaced between those operations, it locks the replacement while deleting selected evidence through the original directory descriptor.

Command: `mise exec -- uv run python dev/local/reviews/00005-purge-root-swap-proof-1.py`

Result (exit 0):

```json
{"active_evidence_deleted": true, "apply_returned_success": true, "original_run_lock_still_held": true, "runtime_swapped_after_open": true}
```

The proof and result are retained as `00005-purge-root-swap-proof-1.py` and `00005-purge-root-swap-result-1.json`. No real session evidence was deleted. This concrete risk is the pause trigger regardless of disputed lower-severity findings.

## Scope and verification

| Original task | Description | Commits |
|---|---|---|
| 1 | Resolve runtime configuration and filesystem layout | 4d4efd4, 84a00c2, b61354d, 4ade4ba, 0d67457 |
| 2 | Implement the authoritative persistent project run lock | e51bced, 73f2bb8 |
| 3 | Publish and reconcile the atomic XDG fleet registry | 29a40c8, ef0c38e, 008c51e |
| 4 | Create secure versioned run and session metadata | 091fe2f, f03fcb8, 2031759 |
| 5 | Probe runtime platform capabilities on macOS | 0422f32, b04d344, 40d5c97, 51e9da4 |
| 6 | Spawn and own shell-free process groups with an anchor | 28363f0, 2655537, f436038, 50c8055 |
| 7 | Escalate owned groups through a bounded watchdog | 24d54c2, bb9d338 |
| 8 | Centralize supervisor signals and emergency state-write failure | 26aefda, e0d60cf, e80e495, 5242577 |
| 9 | Tee raw session bytes before decoding with resource guards | 2d7d7d5, 6bd3fe6 |
| 10 | Inventory retained evidence and apply explicit safe purge | bf0bb8e, f20dbf3, e014784 |
| 11 | Expose status doctor and retained-log commands | be77aa9, e3f2541, c10b167, 054e0d4, 5b0ad20 |

The final formatting commit `e34547e` applies across the reviewed task range. Every original task has its own coverage row; no folded task was dropped.

State/schema and counts were validated before review. The full suite ran once because the build verification record had null test counts: **1812 passed, 0 failed, 0 skipped** in 39.17 seconds, with two pytest temporary-directory cleanup warnings. Sync, Ruff lint/format, mypy, and wheel build all have exit-0 evidence in `last-verification.json` at the identical HEAD.

Mechanical facts and test-shape checks ran over all 32 changed files. The base replay first hit a sandbox Git-worktree denial; the approved retry succeeded and cleaned its temporary worktree: 3 touched tests failed against base, none passed, and 11 new test files could not be collected against pre-change code. The mechanical OR assertion predates this PRD and is preserved below with its verified discard.

`gather-context.sh` initially diffed master against itself; staged context/diff were corrected to the full authoritative PRD range before any reviewer dispatch. Bob received PRD/diff/mechanical evidence without the design document. Blake received only the PRD and blind rubric and located code independently. Complete dispatch/preflight evidence is in `00005-runtime-substrate-v1-preflight-1.md`.

## Consolidated findings

The installed consolidation script produced 49 rows from 50 reviewer issue lines. Its unmodified table is preserved in `00005-runtime-substrate-v1-consolidation-raw-1.md`. Coordinator deduplication merged only the clearly identical defects F02/F33, F07/F10/F30, F11/F26, F18/F48, and F23/F47; merged IDs remain shown. The mechanical test finding was absorbed into F18 without adding a duplicate. F50 adds the independently reproduced purge defect. This leaves **44 consolidated findings**, including seven recorded discard/deferral rows. No raw reviewer wording or rubric verdict was removed.

| ID | Consensus | Severity | Finding | File | Found by | Disposition |
|---|---|---|---|---|---|---|
| F01 | [2/3] | 🟡 | `Watchdog.join(timeout)` returns an apparently final result while its worker may still be running and may signal the process later | src/ovcaq/runtime/watchdog.py | BLAKE, BOB | Unstarted task 14 |
| F02 (also F33) | [2/3] | 🔴 | Normal exit collection closes the group anchor without terminating surviving descendants, after which ownership checks refuse further group signals and the processes leak | src/ovcaq/runtime/process.py | BLAKE, BOB | Unstarted task 14 |
| F03 | [1/3] | 🟠 | `status` never consults `FleetRegistry`, so registry-only evidence is reported as `idle` instead of required `inconsistent` | src/ovcaq/runtime_cli.py:146 | ALICE | Unstarted task 17 |
| F04 | [1/3] | 🟠 | Active-session detection validates metadata shape but never calls `process_matches`, so stale or recycled process metadata can mark a session active | src/ovcaq/runtime/session.py:471 | ALICE | Unstarted task 17 |
| F05 | [1/3] | 🟠 | `doctor` omits required permission, writability, retained-budget, and free-space checks, allowing `ok=true` when production should be blocked | src/ovcaq/runtime_cli.py:191 | ALICE | Unstarted task 17 |
| F06 | [1/3] | 🟠 | Aggregate purge reads each newline-delimited row into memory before enforcing `MAX_STATE_BYTES`, so a malformed newline-free aggregate can exhaust memory | src/ovcaq/runtime/session.py:720 | ALICE | Unstarted task 12 |
| F07 (also F10, F30) | [3/3] | 🟠 | Fleet registry reads follow symlinks, the mutation lock is unverified, and prune unlinks paths without a final identity check, violating the descriptor-relative race contract | src/ovcaq/runtime/registry.py:146 | ALICE, BLAKE, BOB | Unstarted task 13 |
| F08 | [1/3] | 🟠 | Session publication checks paths and then reopens them by pathname, so parent replacement can redirect durable metadata outside the validated runtime tree | src/ovcaq/runtime/session.py:178 | ALICE | Unstarted task 16 |
| F09 | [1/3] | 🟠 | Workflow PRD and state paths bypass containment and symlink validation, so `--prd-root` and `--state` can escape the project without an explicit external state root | src/ovcaq/config.py | BLAKE | Unstarted task 15 |
| F11 (also F26) | [2/3] | 🟠 | No completion operation removes ephemeral `run.json` and fleet entries, leaving a normally completed run reported as inconsistent until external cleanup occurs | N/A | BLAKE, BOB | Unstarted task 19 |
| F12 | [1/3] | 🟠 | Symlink rejection extends to trust anchors: `_checked_path` walks from `/`, so `--root /tmp/x` or `/var/...` fails on macOS (`/tmp`→`/private/tmp`) and a symlinked `~/.config` (stow/chezmoi) makes `_read_config` raise even when no config file exists; this now breaks every pre-existing workflow command too | src/ovcaq/paths.py:63, src/ovcaq/config.py:43 | BOB | Unstarted task 15 |
| F13 | [1/3] | 🟠 | Read-only observations take the exclusive run lock (`_run_health` via `RunLock.acquire`, `_active_session_id` via `flock LOCK_EX\|LOCK_NB`, plus `plan_purge` in doctor); a supervisor starting inside that window is refused as a duplicate; TUI polling widens it | src/ovcaq/runtime_cli.py:146, src/ovcaq/runtime/session.py:471 | BOB | Unstarted task 17 |
| F14 | [1/3] | 🟡 | Runtime metadata reads accept non-UTC timestamps and do not validate run/session IDs as basenames; use the shared `validate_timestamp` and identifier validation | src/ovcaq/cli_io.py:89 | ALICE | Unstarted task 16 |
| F15 | [1/3] | 🟡 | Metadata publication accepts empty `agent` and `process_start` values that the CLI’s own reader later rejects | src/ovcaq/runtime/session.py:165 | ALICE | Unstarted task 16 |
| F16 | [1/3] | 🟡 | Emergency acknowledgement discards the returned archive path, although `doctor --acknowledge-emergency` must report it | src/ovcaq/runtime_cli.py:128 | ALICE | Unstarted task 20 |
| F17 | [1/3] | 🟡 | `status` discards `evidence_health`, silently presenting empty evidence when inventory fails | src/ovcaq/runtime_cli.py:169 | ALICE | Unstarted task 17 |
| F18 (also F48) | [2/3] | 🟡 | The collision test’s final `is_dir() or is_symlink()` assertion is mechanically tautological for its parameter setup; assert the exact expected obstacle per case | tests/state/test_cli.py:379 | ALICE, BOB, mech-check | discarded |
| F19 | [1/3] | 🟡 | `runtime_settings` is 51 lines; extract numeric-limit selection and validation into a helper | src/ovcaq/config.py:142 | ALICE | Unstarted task 21 |
| F20 | [1/3] | 🟡 | `resolve_runtime_paths` is 51 lines; extract existing-directory identity snapshot collection into a helper | src/ovcaq/paths.py:171 | ALICE | Unstarted task 21 |
| F21 | [1/3] | 🟡 | `session.py` is 810 lines, exceeding the 800-line limit; move retention internals into a focused private module while preserving the public API | src/ovcaq/runtime/session.py:1 | ALICE | Unstarted task 21 |
| F22 | [1/3] | 🟡 | Session summaries can declare a different session ID from their containing session directory and metadata | src/ovcaq/runtime/session.py | BLAKE | Unstarted task 16 |
| F23 (also F47) | [2/3] | 🟡 | `status` reports evidence location but omits the exact purge preview required alongside status/doctor diagnostics | src/ovcaq/runtime_cli.py | BLAKE, BOB | Unstarted task 18 |
| F24 | [1/3] | 🟡 | `_purge_payload` prepends a second `--root`: `plan.command` already carries `--root <project>`, so preview/doctor/human output renders `ovcaq --root X --root X logs purge …`; argparse last-wins hides it from the round-trip tests | src/ovcaq/runtime_cli.py:46 | BOB | Unstarted task 18 |
| F25 | [1/3] | 🟡 | `RuntimePaths._identities` is a dataclass field: `asdict(paths)` in `_doctor_payload` emits a stringified device/inode tuple under `paths._identities`, and it participates in `==` | src/ovcaq/paths.py:159, src/ovcaq/runtime_cli.py:222 | BOB | Unstarted task 18 |
| F27 | [1/3] | 🟡 | `_dispatch_logs` maps `ActiveSessionError`, `OSError`, and "no matching retained session" all to `runtime_format`; an active-run refusal or a missing session is not a format error and callers cannot tell them apart | src/ovcaq/runtime_cli.py:116 | BOB | settled-deferral |
| F28 | [1/3] | 🟡 | `_run_health` and `_active_session_id` discard the failure reason (`except …: pass`); `status` says `inconsistent` with no detail for the operator | src/ovcaq/runtime_cli.py:164, src/ovcaq/runtime/session.py:507 | BOB | Unstarted task 17 |
| F29 | [1/3] | 🟡 | `_read_emergency` uses bare `json.loads` + custom pairs hook instead of `decode_json`; a deeply nested marker raises `RecursionError`, which `require_no_emergency_failure` does not translate, so the launch gate crashes with a traceback instead of `EmergencyStateFailure` | src/ovcaq/runtime/session.py:302 | BOB | Unstarted task 20 |
| F31 | [1/3] | 🟡 | Directory creation exists three times: `ensure_runtime_directory` (init), `ensure_runtime_layout` (new, no production caller), `_private_directory` (creates every missing ancestor at 0o700, including `dev/`) | src/ovcaq/runtime/session.py:178, src/ovcaq/paths.py:224 | BOB | Unstarted task 16 |
| F32 | [1/3] | 🟡 | Doctor walks the evidence tree twice and probes the run lock three times (`_evidence_summary` → `inventory_evidence`; `_doctor_payload` → `plan_purge` → `inventory_evidence`; `_run_health`) | src/ovcaq/runtime_cli.py:214 | BOB | Unstarted task 17 |
| F34 | [1/3] | 🟡 | PRD test strategy lists "Ctrl-C/TERM/HUP exit codes"; only `KeyboardInterrupt → 130` exists; `SupervisorSignal` carries `signal_number` with no exit-code mapping or test | src/ovcaq/runtime/process.py:33 | BOB | Unstarted task 14 |
| F35 | [1/3] | 🟡 | Size limits: `session.py` is 810 lines (>800); `runtime_settings` and `resolve_runtime_paths` are 51 lines; new test `test_failed_state_notice_publishes_private_synced_marker_and_persistent_gate` is 60 lines | src/ovcaq/runtime/session.py, src/ovcaq/config.py:142, src/ovcaq/paths.py:171 | BOB | Unstarted task 21 |
| F36 | [1/3] | 🟡 | `_reject` helpers in 8 new test files accept any `Exception`, so a NameError/AttributeError in the code under test counts as a rejection; the intended error type is never pinned | tests/runtime/test_raw_session.py:14 (and test_retention, test_session_metadata, test_session_emergency, test_process, test_watchdog, test_fleet_registry, test_registry) | BOB | Unstarted task 21 |
| F37 | [1/3] | ⚪ | `logs` and `logs purge` share `dest="session"`; the subparser default overwrites a parent `--session`, and `--kind`/`--follow` before `purge` are silently ignored | src/ovcaq/cli.py:209-216 | BOB | Unstarted task 18 |
| F38 | [1/3] | ⚪ | `_state_attention` catches `EmergencyStateFailure` from `acknowledge_emergency_failure`, which never raises it, and reads the state store twice on acknowledgement | src/ovcaq/runtime_cli.py:126-132 | BOB | Unstarted task 18 |
| F39 | [1/3] | ⚪ | Minor slop: `paths.runtime_root / "reports"` instead of `paths.reports`; `import fcntl` inside `_probe_advisory_lock` while registry imports it at module level; `runtime_settings` runs `_checked_path(root)` and `resolve_runtime_paths` repeats it | src/ovcaq/runtime/session.py:378, src/ovcaq/runtime/capability.py:68, src/ovcaq/config.py:155 | BOB | Unstarted task 21 |
| F40 | [1/3] | ⚪ | `_remove_aggregate_row` reports preserved-invalid rows via `warnings.warn(RuntimeWarning)`; in `--json` mode Python warning text lands on stderr beside the JSON contract | src/ovcaq/runtime/session.py:712 | BOB | discarded |
| F41 | [1/3] | ⚪ | `RawSessionWriter.write` copies `chunk[offset:]` on every partial write | src/ovcaq/runtime/session.py:109 | BOB | Unstarted task 12 |
| F42 | [1/3] | ⚪ | CHANGELOG `Fixed` entries describe fixes to code introduced in the same unreleased block; they read as fixes of released behavior | CHANGELOG.md:27-28 | BOB | Unstarted task 21 |
| F43 | [1/3] | ⚪ | `ovcaq logs` without `--session` reads every session's `meta.json`; one corrupt session fails default log lookup for all sessions | src/ovcaq/runtime_cli.py:56 | BOB | settled-deferral |
| F44 | [1/3] | ⚪ | `acknowledge_emergency_failure` keeps a TOCTOU between the final `samestat` and `marker.unlink()`; a marker rewritten in that window is deleted unarchived | src/ovcaq/runtime/session.py:396 | BOB | Unstarted task 20 |
| F45 | [1/3] | ⚪ | `record_state_failure` keeps only the first marker; a later, different failure's `site`/`detail` is not recorded while the gate is up | src/ovcaq/runtime/session.py:344 | BOB | settled-deferral |
| F46 | [1/3] | ⚪ | `inventory_evidence` stats every retained file on each `status`; TUI polling on multi-GB evidence trees will be slow | src/ovcaq/runtime/session.py:438 | BOB | settled-deferral |
| F49 | [1/3] | ⚪ | Cannot statically verify: suite/lint/type/build pass at HEAD (context reports 1812 passed, 0 skipped, Ruff/mypy/build exit 0) | N/A | BOB | discarded |
| F50 | [1/3] | 🔴 | apply_purge opens the original runtime directory but acquires run.lock and retention.lock through its replaceable pathname; swapping that directory lets purge delete active evidence while the original run.lock remains held. | src/ovcaq/runtime/session.py:787 | coordinator-proof | Unstarted task 12 |

## Unstarted follow-up tasks

| Task | Logical tier | Reason | Source finding IDs |
|---|---|---|---|
| 12 — Secure purge ownership and bound retained-evidence reads (L) | opus | algorithmic_risk | F50, F06, F41 |
| 13 — Secure fleet registry roots, locks, and mutation identities (L) | opus | algorithmic_risk | F07, F10, F30 |
| 14 — Retain process-group ownership through descendant cleanup (L) | opus | algorithmic_risk | F01, F02, F33, F34 |
| 15 — Reconcile trusted anchors with configured-path containment (M) | sonnet | default | F09, F12 |
| 16 — Make session publication safe and record validation consistent (L) | opus | algorithmic_risk | F08, F14, F15, F22, F31 |
| 17 — Reconcile runtime liveness and implement doctor resource checks (L) | opus | algorithmic_risk | F03, F04, F05, F13, F17, F28, F32 |
| 18 — Correct diagnostic payloads and logs argument handling (M) | opus | contract | F23, F24, F25, F37, F38, F47 |
| 19 — Provide ownership-safe ephemeral completion cleanup (M) | opus | algorithmic_risk | F11, F26 |
| 20 — Preserve and report emergency evidence through recovery (L) | opus | algorithmic_risk | F16, F29, F44 |
| 21 — Remove review-identified complexity and strengthen test rejection checks (M) | sonnet | default | F19, F20, F21, F35, F36, F39, F42 |

Each task description preserves its source findings verbatim, including script rows later merged for reporting. The installed `classify_tier.py` ran once per task from its file slice, details, and risk facts; no frontmatter model floor is present. Shared process/filesystem state selects logical opus; the diagnostic wire-object correction selects opus/contract; other tasks select sonnet/default. No actual implementor dispatch or Eve/Fable capability is claimed.

The ten tasks are review-work-completion follow-ups only. Do not dispatch them until interactive recovery resolves the pause and Phase 5 verifies/classifies their scope. In particular, preserve existing safety policy when assessing the trust-anchor suggestion; do not implement Bob's untested F_GETLK proposal, broaden the public API, or merely document a process leak.

## Recorded dispositions

- F18: **discarded** — This assertion predates the PRD and is untouched: git diff for tests/state/test_cli.py changes only the parser command inventory. Preserve the mechanical finding, but do not expand this PRD into unrelated test cleanup.
- F48: **discarded** — This assertion predates the PRD and is untouched: git diff for tests/state/test_cli.py changes only the parser command inventory. Preserve the mechanical finding, but do not expand this PRD into unrelated test cleanup.
- F49: **discarded** — Verification is already established at the exact reviewed HEAD: this cycle ran 1812 tests successfully, and the matching work record records successful sync/Ruff/format/mypy/build. Bob's static-only limitation is not a failing product check.
- F40: **discarded** — The design explicitly sends diagnostic/progress text to stderr while requested JSON data stays on stdout. RuntimeWarning on stderr does not violate that channel contract; no wire-schema extension is justified solely by this finding.
- F27: **settled-deferral** — Adding ACTIVE_RUN or new error-code distinctions changes the public error contract beyond an explicit PRD requirement. Preserve for the operator's API decision; do not silently broaden this repair.
- F43: **settled-deferral** — Default log discovery fails closed on malformed evidence; explicit --session remains available. Skipping corrupt records would introduce a separate tolerance policy not specified in this milestone.
- F45: **settled-deferral** — The current emergency gate intentionally preserves the first failure and prevents another launch. Multi-failure accumulation is an extension rather than this milestone's required behavior.
- F46: **settled-deferral** — This PRD requires evidence inventory but specifies no TUI poll-rate or incremental-index performance target. The TUI and performance policy are later milestones.

Every discard/deferral is also recorded with verbatim issue text in `00005-runtime-substrate-v1-ledger.json` and through the state CLI. Deferred lower-severity policy choices do not resolve any open Critical or High finding. F44's emergency-marker race remains in task 20 despite Bob's KNOWN classification: a same-account, short-window argument alone does not establish safe evidence retention.

## Verification-check queue

The queue `00005-runtime-substrate-v1-checks-1.json` is empty. Bob's two VERIFY entries are retained verbatim in his section:

- Exclusive-lock observation probe: **not queued: command shape**. It describes a two-process experiment, not one exact runnable project verification command; F13 remains an unresolved High finding in task 17.
- Suite/lint/type/build verification: **not queued: command shape**. The text contains multiple commands and shell chaining. F49 is discarded against the exact-HEAD suite and build evidence already available.

Bob's raw D3/D5 pass verdicts are retained exactly as required; the coordinator does not rewrite the reviewer's verdicts to conceal the non-queueable commands.

## Alice

Isolated native OpenAI gpt-5.6-sol; logical sonnet; no parent conversation.

[ALICE] 🟠 `status` never consults `FleetRegistry`, so registry-only evidence is reported as `idle` instead of required `inconsistent` | File: src/ovcaq/runtime_cli.py:146 | Task: 11
[ALICE] 🟠 Active-session detection validates metadata shape but never calls `process_matches`, so stale or recycled process metadata can mark a session active | File: src/ovcaq/runtime/session.py:471 | Task: 10
[ALICE] 🟠 `doctor` omits required permission, writability, retained-budget, and free-space checks, allowing `ok=true` when production should be blocked | File: src/ovcaq/runtime_cli.py:191 | Task: 11
[ALICE] 🟠 Aggregate purge reads each newline-delimited row into memory before enforcing `MAX_STATE_BYTES`, so a malformed newline-free aggregate can exhaust memory | File: src/ovcaq/runtime/session.py:720 | Task: 10
[ALICE] 🟠 Fleet registry reads follow symlinks, the mutation lock is unverified, and prune unlinks paths without a final identity check, violating the descriptor-relative race contract | File: src/ovcaq/runtime/registry.py:146 | Task: 3
[ALICE] 🟠 Session publication checks paths and then reopens them by pathname, so parent replacement can redirect durable metadata outside the validated runtime tree | File: src/ovcaq/runtime/session.py:178 | Task: 4
[ALICE] 🟡 Runtime metadata reads accept non-UTC timestamps and do not validate run/session IDs as basenames; use the shared `validate_timestamp` and identifier validation | File: src/ovcaq/cli_io.py:89 | Task: 11
[ALICE] 🟡 Metadata publication accepts empty `agent` and `process_start` values that the CLI’s own reader later rejects | File: src/ovcaq/runtime/session.py:165 | Task: 4
[ALICE] 🟡 Emergency acknowledgement discards the returned archive path, although `doctor --acknowledge-emergency` must report it | File: src/ovcaq/runtime_cli.py:128 | Task: 11
[ALICE] 🟡 `status` discards `evidence_health`, silently presenting empty evidence when inventory fails | File: src/ovcaq/runtime_cli.py:169 | Task: 11
[ALICE] 🟡 The collision test’s final `is_dir() or is_symlink()` assertion is mechanically tautological for its parameter setup; assert the exact expected obstacle per case | File: tests/state/test_cli.py:379 | Task: general
[ALICE] 🟡 `runtime_settings` is 51 lines; extract numeric-limit selection and validation into a helper | File: src/ovcaq/config.py:142 | Task: 1
[ALICE] 🟡 `resolve_runtime_paths` is 51 lines; extract existing-directory identity snapshot collection into a helper | File: src/ovcaq/paths.py:171 | Task: 1
[ALICE] 🟡 `session.py` is 810 lines, exceeding the 800-line limit; move retention internals into a focused private module while preserving the public API | File: src/ovcaq/runtime/session.py:1 | Task: general
R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: fail

## Blake

Isolated native OpenAI gpt-5.6-sol; logical sonnet; PRD-only blind lens; no parent conversation.

[BLAKE] 🔴 Normal exit collection closes the group anchor without terminating surviving descendants, after which ownership checks refuse further group signals and the processes leak | File: src/ovcaq/runtime/process.py | Task: Phase B
[BLAKE] 🟠 Workflow PRD and state paths bypass containment and symlink validation, so `--prd-root` and `--state` can escape the project without an explicit external state root | File: src/ovcaq/config.py | Task: Phase A
[BLAKE] 🟠 Fleet operations follow a replaced or symlinked registry root and open the mutation lock without `O_NOFOLLOW`, allowing prune to delete JSON files outside the resolved fleet root | File: src/ovcaq/runtime/registry.py | Task: Phase A
[BLAKE] 🟠 No completion operation removes ephemeral `run.json` and fleet entries, leaving a normally completed run reported as inconsistent until external cleanup occurs | File: N/A | Task: Phase C
[BLAKE] 🟡 `Watchdog.join(timeout)` returns an apparently final result while its worker may still be running and may signal the process later | File: src/ovcaq/runtime/watchdog.py | Task: Phase B
[BLAKE] 🟡 Session summaries can declare a different session ID from their containing session directory and metadata | File: src/ovcaq/runtime/session.py | Task: Phase C
[BLAKE] 🟡 `status` reports evidence location but omits the exact purge preview required alongside status/doctor diagnostics | File: src/ovcaq/runtime_cli.py | Task: Phase C
B1: fail
B2: fail
B3: pass
B4: pass
B5: fail
B6: pass
B7: pass
B8: pass
B9: pass
B10: fail
B11: pass
B12: fail
B13: pass
B14: fail
B15: fail
B16: fail
B17: fail
B18: pass
B19: pass

## Bob

Fresh external Anthropic claude-opus-5 through the authorized autocodex helper; logical opus. Immutable reviewer output, raw JSONL, stderr, and receipt are retained beside this file. No Codex thread-resume field is emitted.

I read the context, the full 7623-line diff, and the relevant source (`paths.py`, `cli.py`, `runtime_cli.py`, `session.py`, `state/schema.py`, `config.py`, `tests/state/test_cli.py:365-380`). Static analysis only; no code executed.

### Issues

```
[BOB] 🟠 Symlink rejection extends to trust anchors: `_checked_path` walks from `/`, so `--root /tmp/x` or `/var/...` fails on macOS (`/tmp`→`/private/tmp`) and a symlinked `~/.config` (stow/chezmoi) makes `_read_config` raise even when no config file exists; this now breaks every pre-existing workflow command too | File: src/ovcaq/paths.py:63, src/ovcaq/config.py:43 | Task: general
[BOB] 🟠 Read-only observations take the exclusive run lock (`_run_health` via `RunLock.acquire`, `_active_session_id` via `flock LOCK_EX|LOCK_NB`, plus `plan_purge` in doctor); a supervisor starting inside that window is refused as a duplicate; TUI polling widens it | File: src/ovcaq/runtime_cli.py:146, src/ovcaq/runtime/session.py:471 | Task: general
[BOB] 🟡 `_purge_payload` prepends a second `--root`: `plan.command` already carries `--root <project>`, so preview/doctor/human output renders `ovcaq --root X --root X logs purge …`; argparse last-wins hides it from the round-trip tests | File: src/ovcaq/runtime_cli.py:46 | Task: general
[BOB] 🟡 `RuntimePaths._identities` is a dataclass field: `asdict(paths)` in `_doctor_payload` emits a stringified device/inode tuple under `paths._identities`, and it participates in `==` | File: src/ovcaq/paths.py:159, src/ovcaq/runtime_cli.py:222 | Task: general
[BOB] 🟡 No completion counterpart for `publish_run_metadata`: nothing removes `run.json`, so after a normal run ends `status` reports `run: "inconsistent"` indefinitely (PRD: completion removes ephemeral entries) | File: src/ovcaq/runtime/session.py:244 | Task: general
[BOB] 🟡 `_dispatch_logs` maps `ActiveSessionError`, `OSError`, and "no matching retained session" all to `runtime_format`; an active-run refusal or a missing session is not a format error and callers cannot tell them apart | File: src/ovcaq/runtime_cli.py:116 | Task: general
[BOB] 🟡 `_run_health` and `_active_session_id` discard the failure reason (`except …: pass`); `status` says `inconsistent` with no detail for the operator | File: src/ovcaq/runtime_cli.py:164, src/ovcaq/runtime/session.py:507 | Task: general
[BOB] 🟡 `_read_emergency` uses bare `json.loads` + custom pairs hook instead of `decode_json`; a deeply nested marker raises `RecursionError`, which `require_no_emergency_failure` does not translate, so the launch gate crashes with a traceback instead of `EmergencyStateFailure` | File: src/ovcaq/runtime/session.py:302 | Task: general
[BOB] 🟡 `FleetRegistry._mutation` creates the fleet root with umask-default `mkdir(parents=True)` and opens `fleet.lock`/entries without `O_NOFOLLOW`, unlike every other artifact (0o700/0o600, no-follow) | File: src/ovcaq/runtime/registry.py:165 | Task: general
[BOB] 🟡 Directory creation exists three times: `ensure_runtime_directory` (init), `ensure_runtime_layout` (new, no production caller), `_private_directory` (creates every missing ancestor at 0o700, including `dev/`) | File: src/ovcaq/runtime/session.py:178, src/ovcaq/paths.py:224 | Task: general
[BOB] 🟡 Doctor walks the evidence tree twice and probes the run lock three times (`_evidence_summary` → `inventory_evidence`; `_doctor_payload` → `plan_purge` → `inventory_evidence`; `_run_health`) | File: src/ovcaq/runtime_cli.py:214 | Task: general
[BOB] 🟡 `OwnedProcess.wait()`/`collect_exit()` reap the anchor and forfeit ownership: a grandchild surviving a normal agent exit is unreachable afterwards (`signal_group` raises), and a watchdog firing after `wait()` surfaces `ProcessOwnershipError` from `join()`; the cancel→signal→wait ordering contract is undocumented | File: src/ovcaq/runtime/process.py:135 | Task: general
[BOB] 🟡 PRD test strategy lists "Ctrl-C/TERM/HUP exit codes"; only `KeyboardInterrupt → 130` exists; `SupervisorSignal` carries `signal_number` with no exit-code mapping or test | File: src/ovcaq/runtime/process.py:33 | Task: general
[BOB] 🟡 Size limits: `session.py` is 810 lines (>800); `runtime_settings` and `resolve_runtime_paths` are 51 lines; new test `test_failed_state_notice_publishes_private_synced_marker_and_persistent_gate` is 60 lines | File: src/ovcaq/runtime/session.py, src/ovcaq/config.py:142, src/ovcaq/paths.py:171 | Task: general
[BOB] 🟡 `_reject` helpers in 8 new test files accept any `Exception`, so a NameError/AttributeError in the code under test counts as a rejection; the intended error type is never pinned | File: tests/runtime/test_raw_session.py:14 (and test_retention, test_session_metadata, test_session_emergency, test_process, test_watchdog, test_fleet_registry, test_registry) | Task: general
[BOB] ⚪ `logs` and `logs purge` share `dest="session"`; the subparser default overwrites a parent `--session`, and `--kind`/`--follow` before `purge` are silently ignored | File: src/ovcaq/cli.py:209-216 | Task: general
[BOB] ⚪ `_state_attention` catches `EmergencyStateFailure` from `acknowledge_emergency_failure`, which never raises it, and reads the state store twice on acknowledgement | File: src/ovcaq/runtime_cli.py:126-132 | Task: general
[BOB] ⚪ Minor slop: `paths.runtime_root / "reports"` instead of `paths.reports`; `import fcntl` inside `_probe_advisory_lock` while registry imports it at module level; `runtime_settings` runs `_checked_path(root)` and `resolve_runtime_paths` repeats it | File: src/ovcaq/runtime/session.py:378, src/ovcaq/runtime/capability.py:68, src/ovcaq/config.py:155 | Task: general
[BOB] ⚪ `_remove_aggregate_row` reports preserved-invalid rows via `warnings.warn(RuntimeWarning)`; in `--json` mode Python warning text lands on stderr beside the JSON contract | File: src/ovcaq/runtime/session.py:712 | Task: general
[BOB] ⚪ `Watchdog.join(timeout)` returns the in-progress `_result` when the worker is still alive, indistinguishable from a final result | File: src/ovcaq/runtime/watchdog.py:72 | Task: general
[BOB] ⚪ `RawSessionWriter.write` copies `chunk[offset:]` on every partial write | File: src/ovcaq/runtime/session.py:109 | Task: general
[BOB] ⚪ CHANGELOG `Fixed` entries describe fixes to code introduced in the same unreleased block; they read as fixes of released behavior | File: CHANGELOG.md:27-28 | Task: general
[BOB] ⚪ `ovcaq logs` without `--session` reads every session's `meta.json`; one corrupt session fails default log lookup for all sessions | File: src/ovcaq/runtime_cli.py:56 | Task: general
[BOB] ⚪ `acknowledge_emergency_failure` keeps a TOCTOU between the final `samestat` and `marker.unlink()`; a marker rewritten in that window is deleted unarchived | File: src/ovcaq/runtime/session.py:396 | Task: general
[BOB] ⚪ `record_state_failure` keeps only the first marker; a later, different failure's `site`/`detail` is not recorded while the gate is up | File: src/ovcaq/runtime/session.py:344 | Task: general
[BOB] ⚪ `inventory_evidence` stats every retained file on each `status`; TUI polling on multi-GB evidence trees will be slow | File: src/ovcaq/runtime/session.py:438 | Task: general
[BOB] ⚪ PRD "make `status`/`doctor` show location and exact purge preview": `status` shows location only; `purge_preview` is doctor-only | File: N/A | Task: general
[BOB] ⚪ [MECH] `test_init_rejects_project_config_path_collisions_before_state_publication` hedges with `or` (`config.is_dir() or config.is_symlink()`) across `create_collision` params | File: tests/state/test_cli.py:379 | Task: general
[BOB] ⚪ Cannot statically verify: suite/lint/type/build pass at HEAD (context reports 1812 passed, 0 skipped, Ruff/mypy/build exit 0) | File: N/A | Task: general
```

### Rubric verdicts

```
R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: fail
```

R1: the purge `command` shape and doctor `paths` keys are new behavior with no exact assertion (both shipped bugs slipped). R9: `run.json` never cleared, preview command not "exact", doctor leaks internals. R10: `_run_health`/`_active_session_id` swallow reasons; `ActiveSessionError` mislabeled. R12: two 51-line functions. R13: `session.py` 810 lines.

### Categorization

```
FIX:
- Symlink rejection on trust anchors — src/ovcaq/paths.py:63, src/ovcaq/config.py:43 — resolve anchors (project root, XDG homes, `$HOME`) with `.resolve()`; apply `_reject_symlink_components` only to paths derived under the resolved anchor. Tests `test_resolution_refuses_existing_symlink_ancestors[project]` and `test_configuration_refuses_symlink_files_and_ancestors[user-directory]` pin the stricter behavior and must change; flagging, not silently altering.
- Duplicate `--root` in purge command — src/ovcaq/runtime_cli.py:46 — `"command": list(plan.command)`, drop the `root` parameter; assert exact `preview["command"]` in `test_purge_previews_without_mutation_and_applies_only_selected_sessions`.
- `_identities` leaks into doctor and equality — src/ovcaq/paths.py:159, src/ovcaq/runtime_cli.py:222 — `field(default=(), init=False, repr=False, compare=False)`; render `{f.name: str(getattr(paths, f.name)) for f in fields(paths) if not f.name.startswith("_")}`; assert `set(payload["paths"])` in `_assert_doctor_report`.
- No `run.json` removal on completion — src/ovcaq/runtime/session.py:244 — add `remove_run_metadata(paths)` (unlink + directory fsync, no-op when absent) with a test that `status` returns `idle` afterwards.
- `runtime_format` overloaded — src/ovcaq/runtime_cli.py:116 — add `ErrorCode.ACTIVE_RUN` (exit 1) for `ActiveSessionError`, map `OSError` to `STATE_IO`; add the row to `docs/state-protocol.md`; tighten `test_purge_apply_preserves_an_active_session_and_reports_failure` to assert the code.
- Swallowed run-health reasons — src/ovcaq/runtime_cli.py:164, src/ovcaq/runtime/session.py:507 — capture `str(error)` into a `run_detail` field on the status payload (None when healthy).
- Bare `json.loads` in `_read_emergency` — src/ovcaq/runtime/session.py:302 — use `decode_json(payload.decode("utf-8"), source=str(marker))`, delete `_emergency_fields`; add a `deep` case to `test_invalid_emergency_evidence_blocks_launch_and_cannot_be_acknowledged`.
- Fleet root permissions/no-follow — src/ovcaq/runtime/registry.py:165 — create with mode 0o700 + `fchmod`, open `fleet.lock` and entries with `O_NOFOLLOW`; assert 0o700 in `test_publish_replaces_private_same_directory_file_after_fsync_then_syncs_directory`.
- Three directory-creation paths — src/ovcaq/runtime/session.py:178, src/ovcaq/paths.py:224 — have `create_session` call `ensure_runtime_layout(paths)` and reduce `_private_directory` to the final component; leave `ensure_runtime_directory` retirement for a follow-up.
- Doctor double inventory — src/ovcaq/runtime_cli.py:214 — let `plan_purge` accept an optional precomputed `inventory` and pass the one from `_evidence_summary`.
- `wait()` forfeits ownership silently — src/ovcaq/runtime/process.py:135 — docstring on `wait`/`collect_exit` stating cancel watchdog → `signal_group` → `wait`; add a test showing a live grandchild is orphaned after `wait()`.
- No TERM/HUP exit-code mapping — src/ovcaq/runtime/process.py:33 — add `SupervisorSignal.exit_code` (128 + n) with a parametrized test.
- Size limits — src/ovcaq/runtime/session.py, src/ovcaq/config.py:142, src/ovcaq/paths.py:171, tests/runtime/test_session_emergency.py:81 — move the emergency block to `runtime/emergency.py` (add to `DECLARED_MODULES`); extract the identity-snapshot loop and limit-validation loop into helpers; split the 60-line test.
- Catch-all `_reject` helpers — tests/runtime/*.py — narrow to `pytest.raises((ValueError, TypeError, OSError))` or make `_reject` take the expected types.
- Shared `dest="session"` — src/ovcaq/cli.py:209-216 — `dest="purge_session"` on the purge selector; reject parent `--kind/--follow` when `logs_command == "purge"`.
- Dead `EmergencyStateFailure` catch / double read — src/ovcaq/runtime_cli.py:126-132 — drop it from the except tuple; read state once.
- Minor slop trio — src/ovcaq/runtime/session.py:378, src/ovcaq/runtime/capability.py:68, src/ovcaq/config.py:155 — use `paths.reports`, hoist the import, drop the duplicate `_checked_path`.
- `warnings.warn` for operator diagnostics — src/ovcaq/runtime/session.py:712 — count preserved rows and return `preserved_rows` in the purge payload.
- `Watchdog.join` timeout ambiguity — src/ovcaq/runtime/watchdog.py:72 — raise `TimeoutError` when `self._worker.is_alive()` after join.
- Tail copy per partial write — src/ovcaq/runtime/session.py:109 — `view = memoryview(chunk)`; write `view[offset:]`.
- CHANGELOG Fixed noise — CHANGELOG.md:27-28 — drop the two entries (or fold into the Added lines).
VERIFY:
- Observation probes hold the exclusive run lock — two-process macOS script: process A holds `RunLock.acquire`; process B calls `fcntl.fcntl(fd, fcntl.F_GETLK, struct.pack("hhqqi", fcntl.F_WRLCK, 0, 0, 0, 0))` on the same file and checks whether `l_type != F_UNLCK`. If it detects the flock, switch `_run_health` and `_active_session_id` to `F_GETLK`; if not, add a bounded retry (3×50 ms) at the supervisor's `RunLock.acquire` site in PRD 00006.
- Suite/lint/type/build at HEAD e34547e — run `mise exec -- uv run pytest -q` and `mise exec -- uv run ruff check . && mise exec -- uv run mypy` and confirm 1812 passed / 0 skipped / exit 0 (context reports this; I could not execute).
KNOWN:
- Default `logs` fails on any corrupt session `meta.json` — fail-closed on corrupted evidence matches the module's stance; `status` lists sessions so `--session` stays usable; skipping would hide evidence.
- TOCTOU between final `samestat` and `marker.unlink()` — POSIX has no unlink-if-inode; writer (supervisor) and acknowledger (operator) share an account and the window is microseconds; closing it needs a rename-based handoff redesign.
- Only the first emergency marker is retained — the gate blocks further launches until acknowledged, so a second failure requires a launch the gate prevents; multi-failure evidence is a design extension.
- `inventory_evidence` full walk per `status` — PRD asks for inventory size on status; incremental sizing is a later ceiling once the TUI's poll rate is known.
- `status` lacks `purge_preview` — PRD line is ambiguous; doctor carries the preview and status is the lightweight liveness view; adding it is one line if the stricter reading is wanted.
- [MECH] `or` hedge in `test_init_rejects_project_config_path_collisions_before_state_publication` — pre-existing test untouched by this diff; parametrizing the expected predicate belongs to a separate test cleanup.
```

Counts: 29 issue lines = 21 FIX + 2 VERIFY + 6 KNOWN.

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

**Status**: Done.
**Changed**: nothing (review only). 29 findings: 2 🟠, 13 🟡, 14 ⚪; R1/R9/R10/R12/R13 fail.
**Next**: Task complete. Suggested next: fix the two 🟠 items first (symlink-anchor scope in `paths.py:63`, lock-probe race in `runtime_cli.py:146`) since both hit existing callers.

## Review close

All dispatched reviewers/processes reached a terminal result. Alice and Blake reported complete R/B rubrics. Bob returned successful Claude evidence with all D1–D5 and all consensus R verdicts; the receipt pins the output and raw evidence hashes. Carl's guarded exit was recorded and its dispatch ledger row closed.

Verdict: 44 findings
Tests: 1812 passed, 0 failed, 0 skipped (suite run this cycle at e34547e734339e31bcba89e26b3fd3cd58e99690)
