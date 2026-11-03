# Decision Audit Log: 00005-runtime-substrate-v1

PRD: `00005-runtime-substrate-v1.md`
Started: 2026-09-25T22:13:36Z
Completed: 2026-09-25T22:13:36Z
Autonomous: 71  |  Deferred: 27  |  Doubts: 0

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Runtime substrate design choice

**Choice**: Use persistent authoritative locks, an owned process-group anchor, versioned runtime evidence, bounded raw writes, and lock-serialized explicit purge.

**Rationale**: Closes process and PID-reuse races while preserving provider-neutral boundaries; unresolved advisory items remain in the design Review log.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Task 1 runtime schema ambiguity

**Choice**: Use optional top-level version=1, [workflow].runtime_root, [runtime] external_state_root and limit keys, fixed runtime leaf names, and inode checks both before and during layout creation.

**Rationale**: This preserves the accepted plan configuration example and runtime tree while choosing the smallest compatible schema in unattended loop mode.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Task 8 emergency marker contract ambiguity

**Choice**: Use schema_version integer 1 at runtime_root/state-write-failed.json; bound site/detail by MAX_STRING_BYTES without automatic redaction; refuse malformed marker acknowledgement.

**Rationale**: The reviewed design pins versioned exact-key durable JSON, runtime-root placement, shared bounded JSON conventions, and future-version refusal; callers already own the no-environment-values rule.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Task 9 free-space floor ambiguity

**Choice**: Reject a chunk when available_bytes minus chunk length would fall below min_free_bytes; allow equality.

**Rationale**: A free-space floor is a post-write invariant and the task requires checking each complete chunk before accepting it.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Task 10 retention format ambiguity

**Choice**: Construct RuntimePaths with resolve_runtime_paths/ensure_runtime_layout; treat exact-key schema-version-1 session envelopes as schema_version, session_id, payload bounded by MAX_STATE_BYTES; validate run.json as the exact SessionMetadata record; preserve invalid aggregate rows and emit RuntimeWarning reports.

**Rationale**: The reviewed design specifies the exact owned schemas and bounded decoding but the PurgePlan/apply_purge return contract has no report field; warnings are the smallest observable reporting channel without widening the public API.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Task 10 purge argv ambiguity

**Choice**: Use --session and --before selectors; render before as before.astimezone(UTC).isoformat().replace(+00:00,Z), retaining fractional seconds when present.

**Rationale**: The reviewed CLI contract names those flags and requires UTC RFC3339; this is the smallest deterministic Python serialization matching the repository timestamp convention.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Task 11 runtime_format exit ambiguity

**Choice**: Add stable runtime_format error code with exit status 1.

**Rationale**: The reviewed design pins the symbolic code but not its number; exit 1 matches other invalid input/evidence formats while preserving machine-readable discrimination.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Task 11 doctor purge_preview shape ambiguity

**Choice**: Use the same exact object shape as a preview purge response: schema_version, applied=false, selected path strings, total_bytes, and command argv strings.

**Rationale**: The returned doctor preview must be executable and testable; reusing the public purge JSON contract avoids a second invented representation.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Task 11 adversarial test coverage remains incomplete

**Choice**: Proceed after the mandated single strengthening round; preserve the tests and require completion review to scrutinize authoritative state validation.

**Rationale**: The first exploit passed 44 tests with fake doctor data, lock-only activity, snapshot-only follow, and gutted generated docs; the strengthened suite blocked those but the second recheck passed 52 tests while treating schema-invalid JSON state as available. The Tess/Devon strengthening budget is exhausted.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: The collision test’s final `is_dir() or is_symlink()` assertion is mechanically tautological for its parameter setup; assert the exact expected obstacle per case

**Choice**: discarded after verification

**Rationale**: This assertion predates the PRD and is untouched: git diff for tests/state/test_cli.py changes only the parser command inventory. Preserve the mechanical finding, but do not expand this PRD into unrelated test cleanup.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: [MECH] `test_init_rejects_project_config_path_collisions_before_state_publication` hedges with `or` (`config.is_dir() or config.is_symlink()`) across `create_collision` params

**Choice**: discarded after verification

**Rationale**: This assertion predates the PRD and is untouched: git diff for tests/state/test_cli.py changes only the parser command inventory. Preserve the mechanical finding, but do not expand this PRD into unrelated test cleanup.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Cannot statically verify: suite/lint/type/build pass at HEAD (context reports 1812 passed, 0 skipped, Ruff/mypy/build exit 0)

**Choice**: discarded after verification

**Rationale**: Verification is already established at the exact reviewed HEAD: this cycle ran 1812 tests successfully, and the matching work record records successful sync/Ruff/format/mypy/build. Bob's static-only limitation is not a failing product check.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `_remove_aggregate_row` reports preserved-invalid rows via `warnings.warn(RuntimeWarning)`; in `--json` mode Python warning text lands on stderr beside the JSON contract

**Choice**: discarded after verification

**Rationale**: The design explicitly sends diagnostic/progress text to stderr while requested JSON data stays on stdout. RuntimeWarning on stderr does not violate that channel contract; no wire-schema extension is justified solely by this finding.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: PRD 00005 data-loss pause: operator-authorized recovery for existing tasks 12–21

**Choice**: Authorize fresh work/rework session, task 12 first; keep cycle/cap 1/2 and preserve all review obligations

**Rationale**: Operator replied "ok, proceed" on 2026-09-15 to the proposed explicit recovery and repair scope. This resolves authorization only; defects remain open until repairs and verification pass.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: apply_purge opens the original runtime directory but acquires run.lock and retention.lock through its replaceable pathname; swapping that directory lets purge delete active evidence while the original run.lock remains held.

**Recommendation**: The PRD requires explicit active-run-safe purge and raw-byte retention. Bind ownership and deletion to the same verified ancestry; retain malformed evidence and enforce bounded reads. F50 has saved synthetic proof at the current HEAD.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires explicit active-run-safe purge and raw-byte retention. Bind ownership and deletion to the same verified ancestry; retain malformed evidence and enforce bounded reads. F50 has saved synthetic proof at the current HEAD.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Aggregate purge reads each newline-delimited row into memory before enforcing `MAX_STATE_BYTES`, so a malformed newline-free aggregate can exhaust memory

**Recommendation**: The PRD requires explicit active-run-safe purge and raw-byte retention. Bind ownership and deletion to the same verified ancestry; retain malformed evidence and enforce bounded reads. F50 has saved synthetic proof at the current HEAD.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires explicit active-run-safe purge and raw-byte retention. Bind ownership and deletion to the same verified ancestry; retain malformed evidence and enforce bounded reads. F50 has saved synthetic proof at the current HEAD.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `RawSessionWriter.write` copies `chunk[offset:]` on every partial write

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires explicit active-run-safe purge and raw-byte retention. Bind ownership and deletion to the same verified ancestry; retain malformed evidence and enforce bounded reads. F50 has saved synthetic proof at the current HEAD.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Fleet registry reads follow symlinks, the mutation lock is unverified, and prune unlinks paths without a final identity check, violating the descriptor-relative race contract

**Recommendation**: The PRD and design require atomic private fleet records, no-follow opens, and identity-checked mutation; retain the project run lock as authority.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD and design require atomic private fleet records, no-follow opens, and identity-checked mutation; retain the project run lock as authority.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Fleet operations follow a replaced or symlinked registry root and open the mutation lock without `O_NOFOLLOW`, allowing prune to delete JSON files outside the resolved fleet root

**Recommendation**: The PRD and design require atomic private fleet records, no-follow opens, and identity-checked mutation; retain the project run lock as authority.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD and design require atomic private fleet records, no-follow opens, and identity-checked mutation; retain the project run lock as authority.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `FleetRegistry._mutation` creates the fleet root with umask-default `mkdir(parents=True)` and opens `fleet.lock`/entries without `O_NOFOLLOW`, unlike every other artifact (0o700/0o600, no-follow)

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD and design require atomic private fleet records, no-follow opens, and identity-checked mutation; retain the project run lock as authority.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `Watchdog.join(timeout)` returns an apparently final result while its worker may still be running and may signal the process later

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires owned-tree cleanup and signal exits. Current wait closes the anchor without cleaning descendants. Preserve ownership until bounded cleanup completes; test real processes and watchdog completion.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Normal exit collection closes the group anchor without terminating surviving descendants, after which ownership checks refuse further group signals and the processes leak

**Recommendation**: The PRD requires owned-tree cleanup and signal exits. Current wait closes the anchor without cleaning descendants. Preserve ownership until bounded cleanup completes; test real processes and watchdog completion.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires owned-tree cleanup and signal exits. Current wait closes the anchor without cleaning descendants. Preserve ownership until bounded cleanup completes; test real processes and watchdog completion.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `OwnedProcess.wait()`/`collect_exit()` reap the anchor and forfeit ownership: a grandchild surviving a normal agent exit is unreachable afterwards (`signal_group` raises), and a watchdog firing after `wait()` surfaces `ProcessOwnershipError` from `join()`; the cancel→signal→wait ordering contract is undocumented

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires owned-tree cleanup and signal exits. Current wait closes the anchor without cleaning descendants. Preserve ownership until bounded cleanup completes; test real processes and watchdog completion.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: PRD test strategy lists "Ctrl-C/TERM/HUP exit codes"; only `KeyboardInterrupt → 130` exists; `SupervisorSignal` carries `signal_number` with no exit-code mapping or test

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires owned-tree cleanup and signal exits. Current wait closes the anchor without cleaning descendants. Preserve ownership until bounded cleanup completes; test real processes and watchdog completion.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Workflow PRD and state paths bypass containment and symlink validation, so `--prd-root` and `--state` can escape the project without an explicit external state root

**Recommendation**: The PRD requires resolved roots and configured-path containment; the design also explicitly rejects existing symlink components and inode substitutions. Verify anchor behavior against both, preserving the safety policy rather than broadly resolving configured symlinks.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires resolved roots and configured-path containment; the design also explicitly rejects existing symlink components and inode substitutions. Verify anchor behavior against both, preserving the safety policy rather than broadly resolving configured symlinks.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Symlink rejection extends to trust anchors: `_checked_path` walks from `/`, so `--root /tmp/x` or `/var/...` fails on macOS (`/tmp`→`/private/tmp`) and a symlinked `~/.config` (stow/chezmoi) makes `_read_config` raise even when no config file exists; this now breaks every pre-existing workflow command too

**Recommendation**: The PRD requires resolved roots and configured-path containment; the design also explicitly rejects existing symlink components and inode substitutions. Verify anchor behavior against both, preserving the safety policy rather than broadly resolving configured symlinks.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires resolved roots and configured-path containment; the design also explicitly rejects existing symlink components and inode substitutions. Verify anchor behavior against both, preserving the safety policy rather than broadly resolving configured symlinks.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Session publication checks paths and then reopens them by pathname, so parent replacement can redirect durable metadata outside the validated runtime tree

**Recommendation**: The design explicitly specifies version-1 exact-key metadata, UTC timestamps, basename IDs, and ancestry-safe publication. Repair consistency within that existing schema.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The design explicitly specifies version-1 exact-key metadata, UTC timestamps, basename IDs, and ancestry-safe publication. Repair consistency within that existing schema.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Runtime metadata reads accept non-UTC timestamps and do not validate run/session IDs as basenames; use the shared `validate_timestamp` and identifier validation

**Recommendation**: The design explicitly specifies version-1 exact-key metadata, UTC timestamps, basename IDs, and ancestry-safe publication. Repair consistency within that existing schema.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The design explicitly specifies version-1 exact-key metadata, UTC timestamps, basename IDs, and ancestry-safe publication. Repair consistency within that existing schema.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Metadata publication accepts empty `agent` and `process_start` values that the CLI’s own reader later rejects

**Recommendation**: The design explicitly specifies version-1 exact-key metadata, UTC timestamps, basename IDs, and ancestry-safe publication. Repair consistency within that existing schema.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The design explicitly specifies version-1 exact-key metadata, UTC timestamps, basename IDs, and ancestry-safe publication. Repair consistency within that existing schema.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Session summaries can declare a different session ID from their containing session directory and metadata

**Recommendation**: The design explicitly specifies version-1 exact-key metadata, UTC timestamps, basename IDs, and ancestry-safe publication. Repair consistency within that existing schema.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The design explicitly specifies version-1 exact-key metadata, UTC timestamps, basename IDs, and ancestry-safe publication. Repair consistency within that existing schema.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Directory creation exists three times: `ensure_runtime_directory` (init), `ensure_runtime_layout` (new, no production caller), `_private_directory` (creates every missing ancestor at 0o700, including `dev/`)

**Recommendation**: The design explicitly specifies version-1 exact-key metadata, UTC timestamps, basename IDs, and ancestry-safe publication. Repair consistency within that existing schema.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The design explicitly specifies version-1 exact-key metadata, UTC timestamps, basename IDs, and ancestry-safe publication. Repair consistency within that existing schema.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `status` never consults `FleetRegistry`, so registry-only evidence is reported as `idle` instead of required `inconsistent`

**Recommendation**: The PRD/design require shared run-lock/process/metadata/fleet observations and doctor resource checks. Verify the lock-contention claim using real processes; do not adopt untested F_GETLK behavior or a second liveness policy.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD/design require shared run-lock/process/metadata/fleet observations and doctor resource checks. Verify the lock-contention claim using real processes; do not adopt untested F_GETLK behavior or a second liveness policy.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Active-session detection validates metadata shape but never calls `process_matches`, so stale or recycled process metadata can mark a session active

**Recommendation**: The PRD/design require shared run-lock/process/metadata/fleet observations and doctor resource checks. Verify the lock-contention claim using real processes; do not adopt untested F_GETLK behavior or a second liveness policy.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD/design require shared run-lock/process/metadata/fleet observations and doctor resource checks. Verify the lock-contention claim using real processes; do not adopt untested F_GETLK behavior or a second liveness policy.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `doctor` omits required permission, writability, retained-budget, and free-space checks, allowing `ok=true` when production should be blocked

**Recommendation**: The PRD/design require shared run-lock/process/metadata/fleet observations and doctor resource checks. Verify the lock-contention claim using real processes; do not adopt untested F_GETLK behavior or a second liveness policy.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD/design require shared run-lock/process/metadata/fleet observations and doctor resource checks. Verify the lock-contention claim using real processes; do not adopt untested F_GETLK behavior or a second liveness policy.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Read-only observations take the exclusive run lock (`_run_health` via `RunLock.acquire`, `_active_session_id` via `flock LOCK_EX|LOCK_NB`, plus `plan_purge` in doctor); a supervisor starting inside that window is refused as a duplicate; TUI polling widens it

**Recommendation**: The PRD/design require shared run-lock/process/metadata/fleet observations and doctor resource checks. Verify the lock-contention claim using real processes; do not adopt untested F_GETLK behavior or a second liveness policy.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD/design require shared run-lock/process/metadata/fleet observations and doctor resource checks. Verify the lock-contention claim using real processes; do not adopt untested F_GETLK behavior or a second liveness policy.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `status` discards `evidence_health`, silently presenting empty evidence when inventory fails

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD/design require shared run-lock/process/metadata/fleet observations and doctor resource checks. Verify the lock-contention claim using real processes; do not adopt untested F_GETLK behavior or a second liveness policy.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `_run_health` and `_active_session_id` discard the failure reason (`except …: pass`); `status` says `inconsistent` with no detail for the operator

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD/design require shared run-lock/process/metadata/fleet observations and doctor resource checks. Verify the lock-contention claim using real processes; do not adopt untested F_GETLK behavior or a second liveness policy.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Doctor walks the evidence tree twice and probes the run lock three times (`_evidence_summary` → `inventory_evidence`; `_doctor_payload` → `plan_purge` → `inventory_evidence`; `_run_health`)

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD/design require shared run-lock/process/metadata/fleet observations and doctor resource checks. Verify the lock-contention claim using real processes; do not adopt untested F_GETLK behavior or a second liveness policy.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `status` reports evidence location but omits the exact purge preview required alongside status/doctor diagnostics

**Recommendation**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `_purge_payload` prepends a second `--root`: `plan.command` already carries `--root <project>`, so preview/doctor/human output renders `ovcaq --root X --root X logs purge …`; argparse last-wins hides it from the round-trip tests

**Recommendation**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `RuntimePaths._identities` is a dataclass field: `asdict(paths)` in `_doctor_payload` emits a stringified device/inode tuple under `paths._identities`, and it participates in `==`

**Recommendation**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `logs` and `logs purge` share `dest="session"`; the subparser default overwrites a parent `--session`, and `--kind`/`--follow` before `purge` are silently ignored

**Recommendation**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `_state_attention` catches `EmergencyStateFailure` from `acknowledge_emergency_failure`, which never raises it, and reads the state store twice on acknowledgement

**Recommendation**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: PRD "make `status`/`doctor` show location and exact purge preview": `status` shows location only; `purge_preview` is doctor-only

**Recommendation**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD requires exact purge previews in status/doctor. Correct the existing representations and parser semantics, reusing the purge representation and stable top-level envelopes; unrelated public error-code changes remain deferred.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: No completion operation removes ephemeral `run.json` and fleet entries, leaving a normally completed run reported as inconsistent until external cleanup occurs

**Recommendation**: The PRD explicitly requires normal completion to remove only owner-specific ephemeral entries. Provide the substrate cleanup effect; do not implement the future supervisor or delete persistent locks/evidence.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD explicitly requires normal completion to remove only owner-specific ephemeral entries. Provide the substrate cleanup effect; do not implement the future supervisor or delete persistent locks/evidence.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: No completion counterpart for `publish_run_metadata`: nothing removes `run.json`, so after a normal run ends `status` reports `run: "inconsistent"` indefinitely (PRD: completion removes ephemeral entries)

**Recommendation**: The PRD explicitly requires normal completion to remove only owner-specific ephemeral entries. Provide the substrate cleanup effect; do not implement the future supervisor or delete persistent locks/evidence.

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The PRD explicitly requires normal completion to remove only owner-specific ephemeral entries. Provide the substrate cleanup effect; do not implement the future supervisor or delete persistent locks/evidence.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Emergency acknowledgement discards the returned archive path, although `doctor --acknowledge-emergency` must report it

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The design requires bounded emergency evidence and acknowledgement by durable archival. Preserve concurrent replacements and report the archive path; timing alone does not justify a lost marker.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `_read_emergency` uses bare `json.loads` + custom pairs hook instead of `decode_json`; a deeply nested marker raises `RecursionError`, which `require_no_emergency_failure` does not translate, so the launch gate crashes with a traceback instead of `EmergencyStateFailure`

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The design requires bounded emergency evidence and acknowledgement by durable archival. Preserve concurrent replacements and report the archive path; timing alone does not justify a lost marker.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `acknowledge_emergency_failure` keeps a TOCTOU between the final `samestat` and `marker.unlink()`; a marker rewritten in that window is deleted unarchived

**Choice**: operator-authorized repair; verify before closing

**Rationale**: The design requires bounded emergency evidence and acknowledgement by durable archival. Preserve concurrent replacements and report the archive path; timing alone does not justify a lost marker.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `runtime_settings` is 51 lines; extract numeric-limit selection and validation into a helper

**Choice**: operator-authorized repair; verify before closing

**Rationale**: Authorize bounded cleanup of verified violations in newly changed code and precise contract-based test rejection assertions; preserve public interfaces and safety semantics.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `resolve_runtime_paths` is 51 lines; extract existing-directory identity snapshot collection into a helper

**Choice**: operator-authorized repair; verify before closing

**Rationale**: Authorize bounded cleanup of verified violations in newly changed code and precise contract-based test rejection assertions; preserve public interfaces and safety semantics.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `session.py` is 810 lines, exceeding the 800-line limit; move retention internals into a focused private module while preserving the public API

**Choice**: operator-authorized repair; verify before closing

**Rationale**: Authorize bounded cleanup of verified violations in newly changed code and precise contract-based test rejection assertions; preserve public interfaces and safety semantics.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Size limits: `session.py` is 810 lines (>800); `runtime_settings` and `resolve_runtime_paths` are 51 lines; new test `test_failed_state_notice_publishes_private_synced_marker_and_persistent_gate` is 60 lines

**Choice**: operator-authorized repair; verify before closing

**Rationale**: Authorize bounded cleanup of verified violations in newly changed code and precise contract-based test rejection assertions; preserve public interfaces and safety semantics.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `_reject` helpers in 8 new test files accept any `Exception`, so a NameError/AttributeError in the code under test counts as a rejection; the intended error type is never pinned

**Choice**: operator-authorized repair; verify before closing

**Rationale**: Authorize bounded cleanup of verified violations in newly changed code and precise contract-based test rejection assertions; preserve public interfaces and safety semantics.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: Minor slop: `paths.runtime_root / "reports"` instead of `paths.reports`; `import fcntl` inside `_probe_advisory_lock` while registry imports it at module level; `runtime_settings` runs `_checked_path(root)` and `resolve_runtime_paths` repeats it

**Choice**: operator-authorized repair; verify before closing

**Rationale**: Authorize bounded cleanup of verified violations in newly changed code and precise contract-based test rejection assertions; preserve public interfaces and safety semantics.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: CHANGELOG `Fixed` entries describe fixes to code introduced in the same unreleased block; they read as fixes of released behavior

**Choice**: operator-authorized repair; verify before closing

**Rationale**: Authorize bounded cleanup of verified violations in newly changed code and precise contract-based test rejection assertions; preserve public interfaces and safety semantics.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: 7 touched test(s) pass against the pre-change code: test_internal_resolution_refuses_existing_symlink_descendants, test_configuration_refuses_symlink_files_with_arbitrary_targets +1 more

**Choice**: discarded after verification

**Rationale**: Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: 11 touched test(s) pass against the pre-change code: test_spawn_rejects_invalid_argv_before_starting_any_process +5 more

**Choice**: discarded after verification

**Rationale**: Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: 31 touched test(s) pass against the pre-change code: test_rejects_nonbytes_without_changing_evidence, test_rejects_invalid_limits +25 more

**Choice**: discarded after verification

**Rationale**: Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: 1 touched test(s) pass against the pre-change code: test_inode_substitution_during_acquisition_fails_and_releases_old_inode

**Choice**: discarded after verification

**Rationale**: Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: 25 touched test(s) pass against the pre-change code: test_invalid_selectors_fail_without_mutating_evidence +19 more

**Choice**: discarded after verification

**Rationale**: Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: 25 touched test(s) pass against the pre-change code: test_purge_rejects_parent_log_options_without_removing_evidence, test_runtime_readers_reject_unsafe_ids_non_utc_times_and_empty_required_strings +19 more

**Choice**: discarded after verification

**Rationale**: Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: 34 touched test(s) pass against the pre-change code: test_failed_state_notice_publishes_private_synced_marker_and_persistent_gate, test_invalid_failure_diagnostics_are_rejected_without_publishing_marker +28 more

**Choice**: discarded after verification

**Rationale**: Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: 16 touched test(s) pass against the pre-change code: test_rejects_invalid_durations_before_starting_a_worker +10 more

**Choice**: discarded after verification

**Rationale**: Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: 4 touched test(s) pass against the pre-change code: test_configured_runtime_preserves_containment_and_symlink_refusal, test_workflow_paths_accept_contained_explicit_and_configured_values

**Choice**: discarded after verification

**Rationale**: Computed pass-at-base fact retained, then assessed against the diff: these are pre-existing rejection/containment/byte-preservation cases with narrower expected exceptions, helper refactors, varied inputs, or regression backfill. Correct pre-change behavior should still pass. The replay separately records 113 failing touched cases and three uncollectable files; a passing existing parametrization is not itself a missing behavioral fix.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: The CLI adds unlisted `doctor --acknowledge-emergency` and `logs purge --session` options, expanding both the interface and destructive purge behavior beyond the specified command surface

**Choice**: discarded after verification

**Rationale**: The accepted PRD design explicitly specifies both flags as refinements of explicit session purge and emergency recovery; no automatic destructive action or out-of-scope product capability was added. The source command table is not an exhaustive flag inventory.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: The `command` field means opposite things in two outputs. In `status` and `doctor`, `purge_preview.command` removes `--apply` with `plan.command[:-1]`. In `logs purge` output, `command` keeps `--apply`. The slice also silently depends on `--apply` being the last argument.

**Choice**: discarded after verification

**Rationale**: Status/doctor intentionally expose a safe preview command, while explicit purge outputs the documented apply argv. PurgePlan's accepted contract pins --apply last, so slicing that suffix is not an unverified assumption.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `Watchdog.join` signals "worker still running" with the builtin `TimeoutError`, which is a subclass of `OSError`. Broad `except OSError` handlers, such as the one in `cli.main`, would report it as an I/O failure.

**Choice**: discarded after verification

**Rationale**: TimeoutError correctly represents a timed wait; no current production CLI path invokes Watchdog.join. A possible future broad OSError handler is hypothetical and does not justify a new exception API here.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `run_lock_held` raises on any platform other than darwin. On Linux, `status` and `doctor` will report `inconsistent` whenever run.lock exists.

**Choice**: discarded after verification

**Rationale**: The PRD explicitly limits this milestone to macOS and assigns Linux support to a later release gate; reporting unsupported observation is expected.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: `_read_config` refuses a symlinked user `~/.config/ovcaq` directory or `config.toml` file below the trusted anchor. That breaks stow-style dotfile setups.

**Choice**: discarded after verification

**Rationale**: The accepted trust-boundary repair deliberately resolves the chosen XDG anchor while refusing symlink descendants and config files. Relaxing that tested safety contract is not an automatic fix.

### [autonomous] 2026-09-25T22:13:36Z

**Decision**: In the fail-first replay, 154 touched tests pass against the pre-change code. Most are expected, because they cover code that was only moved or refactored. It is not confirmed that this cycle's new-behavior tests fail at the base.

**Choice**: routed to verification

**Rationale**: Routed to the exact named project verification command. No work pass runs on the cap-out path, so this check remains unrun. Bob's stated base-worktree and expected-failure interpretation is retained as context; ordinary current-HEAD exit zero alone would not establish that stronger claim.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `_dispatch_logs` maps `ActiveSessionError`, `OSError`, and "no matching retained session" all to `runtime_format`; an active-run refusal or a missing session is not a format error and callers cannot tell them apart

**Choice**: deferred for operator review

**Rationale**: Adding ACTIVE_RUN or new error-code distinctions changes the public error contract beyond an explicit PRD requirement. Preserve for the operator's API decision; do not silently broaden this repair.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `ovcaq logs` without `--session` reads every session's `meta.json`; one corrupt session fails default log lookup for all sessions

**Choice**: deferred for operator review

**Rationale**: Default log discovery fails closed on malformed evidence; explicit --session remains available. Skipping corrupt records would introduce a separate tolerance policy not specified in this milestone.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `record_state_failure` keeps only the first marker; a later, different failure's `site`/`detail` is not recorded while the gate is up

**Choice**: deferred for operator review

**Rationale**: The current emergency gate intentionally preserves the first failure and prevents another launch. Multi-failure accumulation is an extension rather than this milestone's required behavior.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `inventory_evidence` stats every retained file on each `status`; TUI polling on multi-GB evidence trees will be slow

**Choice**: deferred for operator review

**Rationale**: This PRD requires evidence inventory but specifies no TUI poll-rate or incremental-index performance target. The TUI and performance policy are later milestones.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `RuntimePaths._identities` remains a comparison field, so two objects with identical public contract fields compare unequal when their private filesystem snapshots differ; declare it with `compare=False`

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: F31 remains: `_private_directory` still duplicates the two path-layout creators and creates every missing ancestor with mode `0700`; consolidate the descriptor-walk primitive so intermediate project directories retain the established layout policy

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `_state_attention` still catches `EmergencyStateFailure`, which `acknowledge_emergency_failure` cannot raise, leaving the dead exception branch and import identified by F38

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: The rework expanded `test_runtime_cli.py` from 666 to 1234 lines, violating the 800-line limit; split status/doctor, log, purge, and emergency command tests into focused modules

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: Fleet entry reads are not identity-bound to deletion: `_scan` records a pre-open inode without comparing it to the opened descriptor, while `remove` validates contents and then unlinks the pathname without rechecking its inode; a replacement during either gap can make prune delete a live record or remove delete a new owner’s record

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved; replacement live-entry deletion reproduced with synthetic data in 00005_fleet_remove_race_proof_2.py. This loses discovery metadata; the authoritative run lock and retained session evidence remain intact.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: Signal handling only raises an exception; no production runtime path composes group termination, outcome recording, registry cleanup, and lock release, leaving P03-T10’s centralized cleanup contract unimplemented

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved; the source plan section 12.2 requires composed cleanup, while this PRD/design expose primitives and delegate composition to their caller. Preserve the scope ambiguity for operator triage; do not opportunistically implement the later supervisor.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: Three code paths now pick the state file differently. `workflow_settings` reads a new, undocumented `[workflow] state_file` key (config.py:117) and ignores `[runtime] external_state_root`. `status`, `doctor` and `--acknowledge-emergency` use `runtime_settings`, which honors the external root and ignores `state_file`. `init` and `state` use `state_path(root)` (cli.py:426). With either key set, doctor reports state "missing", and acknowledgement can accept a different file than the one workflow commands write (confirmed by reading). The PRD's explicit external-root behavior is still not met.

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved; 00005_runtime_resolution_proof_2.py confirms runtime diagnostics select external/state.json while workflow/state defaults remain project-local.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `status` still emits only `run.status`, so the concrete failure retained in `RunObservation.detail` is unavailable when status reports `inconsistent`; F28 remains observable even though doctor exposes the reason

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: Emergency decoding still reimplements the shared bounded duplicate-key-safe JSON decoder with `json.loads` and `_emergency_fields`; use `decode_json` directly and remove the duplicate parser

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: Runtime-root precedence merges internal and external choices independently, so a lower-priority user external root conflicts with a higher-priority project or explicit internal root instead of being overridden

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved; per-key merging and mutually exclusive root selectors conflict across layers. Preserve the exact precedence question for repair.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: Process identity uses `ps lstart` with one-second precision, so a PID recycled within the same second can be misclassified as the original process and escape stale-entry pruning

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: A `ps` timeout raises uncaught `subprocess.TimeoutExpired`, allowing registry discovery and `status`/`doctor` to traceback instead of producing degraded diagnostics

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `status` embeds `datetime.now()` in its purge preview, so unchanged runtime/state data produces different output despite the required deterministic status contract

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `doctor` reports `ok: false` on every newly initialized project. `_directory_health` stats `paths.sessions`, but `init` creates only `dev/local/ovcaq`, and only `create_session` creates `sessions`. The resulting FileNotFoundError fills both the `permissions` and `writability` checks with the error text. Every ok=True test runs `ensure_runtime_layout` first, so none catches this (confirmed by reading).

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved; isolated init-then-doctor reproduction confirms missing sessions directory makes permission/writability checks fail.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: The F14 fix landed on `_runtime_timestamp`, which after the refactor only parses `logs purge --before`. Cutoffs with an offset (valid RFC3339, the metavar) are now rejected as usage errors. No test covers this, and the validator label says `metadata.started_at` (metadata already goes through `parse_session_metadata`).

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved; cutoff input uses the strict UTC metadata parser despite RFC3339 labeling. Preserve both the behavior and misleading label for API-contract triage.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `cleanup_run_records` turns every OSError, ValueError and TypeError into `False`. A caller cannot tell "record belongs to another run" from "unlink or fsync failed", and the cause is lost.

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `_acquire_purge_locks` re-implements `RunLock.acquire`: O_NOFOLLOW open, S_ISREG check, LOCK_NB flock, samestat recheck, fchmod. Simpler: add `directory: int | None = None` to `RunLock.acquire` (as `run_lock_held` already has) and map DuplicateRunError to ActiveSessionError for run.lock.

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `cleanup_run_records` removes the fleet entry before `run.json`. If that unlink fails, or the entry is already gone, `remove()` returns False on every retry. `run.json` is then stranded and `status` stays inconsistent until the next run overwrites it.

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: A second concurrent `logs purge --apply` is refused with "cannot purge while a run is active", because run.lock is taken first. That message is wrong for this case. retention.lock can never be the contended lock, since its only taker already holds run.lock. If it ever were contended, its DuplicateRunError (a RuntimeError) would escape `_dispatch_logs` and `main` as a traceback.

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved; preserve the inaccurate contention diagnostic and uncaught retention-lock exception, but do not remove the retention lock required for future aggregate writers.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: `workflow_settings` validates the PRD root and the state file with `runtime_directory`. Rejections therefore say "derived runtime path escapes project root" even when the path is a PRD root or a state file.

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: The rewritten CHANGELOG Added bullets list implementation details ("identity-pinned fleet records behind inode-stable run locks without launch contention") rather than what the user sees.

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: rework cap reached with this finding unresolved

### [deferred] 2026-09-25T22:13:36Z

**Decision**: Emergency acknowledgement publishes and fsyncs a full archive copy (`_archive_emergency_evidence`), then deletes it on success at session.py:582. The rename plus link-back already keeps the evidence reachable.

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: The archive copy is deliberate recovery evidence used by failure-path tests. Removing it is a behavior/design change outside this repair; preserve Bob's KNOWN qualification.

### [deferred] 2026-09-25T22:13:36Z

**Decision**: On normal exit, surviving descendants get an immediate SIGKILL with no TERM grace, so they cannot flush. The PRD describes TERM, then grace, then KILL.

**Choice**: deferred to batch end; no repair dispatched

**Rationale**: The previous repair deliberately chose immediate owned-group cleanup after normal agent exit. Adding descendant TERM grace requires a policy/API decision; preserve this KNOWN limitation for later operator triage.
