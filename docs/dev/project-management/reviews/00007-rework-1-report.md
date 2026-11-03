# PRD 00007 — Cycle 1 rework report

Implementation verified at `40ba50b0bd54bd8574eb7719162a72fe3195def0`. Tasks 9–15 are complete; the next gate is full cycle-2 review in a fresh session.
No cycle-2 review was invoked from this implementation session. Canonical advancement uses `phase-done --outcome rework`.

Batch lifecycle now starts and completes durably, capability failures record attention, and successful retries clear only their own notice. Shared decision policy bounds unchanged attempts across failure classes and honors committed controls before work. State failures preserve emergency evidence; operator stops persist until resume. Capability execution shares one lifecycle and uses its own validated timeout. Workflow reporting excludes capability attempts and retains malformed-usage phase sessions. Launches honor supplied phase settings. CLI error assertions and source size limits are repaired.

## Task evidence

- 9: style_gate: clean, split_hygiene: clean
  Verification: 11 failed / 15 passed red; 26 passed green. Self-deslop: noop.
- 10: style_gate: clean, split_hygiene: clean
  Verification: 69 failed / 218 passed original red; added terminal guards 8 failed / 7 passed; 302 passed green. Self-deslop: skipped:trivial (35 insertions - 32 deletions = 3 net lines).
- 11: style_gate: fixed:9cbd47a, split_hygiene: clean
  Verification: 20 failed / 42 passed red; Pat regression failed; 63 passed green. Self-deslop: noop.
- 12: style_gate: clean, split_hygiene: clean
  Verification: 72 failed /26 passed red; additional 2 failed /100 passed contract checks; 102 passed final green. Self-deslop: skipped:trivial (63 insertions -53 deletions =10 net).
- 13: style_gate: clean, split_hygiene: clean
  Verification: 2 failed /5 passed red; 7 passed green. Self-deslop: skipped:trivial (24 insertions -16 deletions =8 net).
- 14: style_gate: clean, split_hygiene: clean
  Verification: 1 failed /116 passed red; 117 passed green. Self-deslop: skipped:trivial (17 insertions -4 deletions =13 net).
- 15: style_gate: clean, split_hygiene: clean
  Verification: 2 failed on original PRD base; source style red54lines;16passedgreen. Self-deslop: skipped:trivial (20 insertions -10 deletions =10 net).

Every task ran the prescribed pipeline and Claude Pat closure review. Opus tasks 9–12 included adversarial Devon and one Tess strengthening pass. Tasks 13–15 used the sonnet lean pipeline. Micro trials 13 and 14 exceeded the two-file ceiling and were reverted before normal dispatch. Logical tiers and actual providers/models are recorded in `00007-rework-1-dispatch.json`; native implementors used Astra/Sol, and external Pat sessions observed `claude-sonnet-5-5`. The same-batch cached unhealthy implementor probe was reused, not represented as a new health check.

Task 11's valid MEDIUM review finding was repaired and re-reviewed with no remaining findings. Task 10's MEDIUM bootstrap claim was rejected after tracing the pre-existing failure decision branch; successful bootstrap PAUSE behavior remains unchanged. Task 12's initial startup-metric assumption was rejected before committing production changes. Raw reviewer output and dispositions remain in the dispatch artifact. Remaining Pat LOW notes are retained for full review, not silently discarded.

The installed lifecycle commands' real capability runner/readiness work remains assigned to PRD 00010 (F02/F23), and F06 bootstrap policy remains a settled deferral. Task 15 leaves the pre-existing F19 assertion untouched. Its revised CLI assertions fail at the original PRD base in an isolated replay; the copied tree was removed afterward. `_collect` is 45 lines, `_conclude` is 48, and the state CLI test file is 786.

## Final verification

Full suite: **3863 passed, 0 failed, 0 skipped**. Two pytest temporary-directory cleanup warnings were emitted. No final regression repair cycle was required.

| Command | Exit |
|---|---|
| `UV_CACHE_DIR=/private/tmp/ovcaq-final-cache mise exec -- uv sync --all-groups` | 0 |
| `UV_CACHE_DIR=/private/tmp/ovcaq-final-cache mise exec -- uv run pytest` | 0 |
| `UV_CACHE_DIR=/private/tmp/ovcaq-final-cache mise exec -- uv run ruff check .` | 1 |
| `UV_CACHE_DIR=/private/tmp/ovcaq-final-cache mise exec -- uv run ruff format --check .` | 1 |
| `UV_CACHE_DIR=/private/tmp/ovcaq-final-cache mise exec -- uv run ruff check src tests` | 0 |
| `UV_CACHE_DIR=/private/tmp/ovcaq-final-cache mise exec -- uv run ruff format --check src tests` | 0 |
| `UV_CACHE_DIR=/private/tmp/ovcaq-final-cache mise exec -- uv run mypy src/ovcaq` | 0 |
| `UV_CACHE_DIR=/private/tmp/ovcaq-final-cache mise exec -- uv build` | 0 |
| `UV_CACHE_DIR=/private/tmp/ovcaq-final-cache mise exec -- uv run pytest` | 0 |

Root Ruff checks remain nonzero: 41 lint errors and 46 files needing formatting, all in existing planning/design/review material outside this rework diff. Product and test lint/format checks pass. Those unrelated artifacts and the operator's dirty AGENTS.md were preserved.

verify_check: UV_CACHE_DIR=/private/tmp/ovcaq-final-cache uv run pytest -> exit 0

The queued command was validated as one exact project test invocation before execution and ran once after implementation settled. Raw logs are under `00007-rework-1-evidence/final-*`. `last-verification.json` records the actual tested SHA; the subsequent metadata/handoff commit does not retroactively change it.

Schema and derived task counts validated at 15/15. The existing cycle-1 review passed the coverage/provenance gate, and raw verdict coverage was checked against all source rules: Alice R1–R4/R6–R13 (the source has no R5), Blake B1–B19, and Bob D1–D5. No new full-review verdict is claimed.

All dispatched agents and processes were awaited. Temporary adversarial/replay copies were removed; only the current worktree/master exists. Active architecture plans and required review evidence remain. Current-PRD scratch prompts remain available for the fresh review session.

## Assumption ledger (verbatim)

# PRD 00007 assumptions

## Tasks 1–3

- No surviving implementor assumptions were recorded in the resumed session artifacts.

## Task 4 — Add compound supervisor and capability state mutations

- A failed or reconciled capability writes `control.attention` with site `capability:<name>` and leaves `batch.status` unchanged; the focused tests require actionable attention and prohibit completion, but do not require the batch-level `attention` status.
- Empty drain is defined by `work.next_phase == ""`, zero completed PRDs, and every capability still pending. It preserves existing control attention and creates no capability attempt.
- Capability attempts are serialized: only one capability may be running, and a failed capability cannot restart through the state-service start method; the later capability service owns explicit retry sequencing.
- Empty-drain `completed_at` uses the current UTC time at second precision.
- Devon's single strengthening round closed eight preservation gaps. A redundant resume-time recheck found additional fixture-specialization gaps, but the work contract permits no second Devon/Tess round; those observations are left to the mandatory PRD-level review.
- Pat left four LOW notes: injectable empty-drain time, attention overwrite semantics, explicit attempt-ID validation, and simplifying the success/failure branch.

## Task 5 — Implement durable provider-neutral capability execution

- `CapabilityService` is constructed with the project root, state store, runtime paths, run ID, injectable UTC clock, and a default 10,800-second timeout.
- Capability result evidence is one appended UTF-8 JSON line containing exactly `success`, `session_id`, and `detail`; existing runner bytes are preserved.
- Failed-to-running retry uses a dedicated atomic `StateService.retry_capability` mutation; `start_capability` remains pending-only.
- State transitions commit before their session evidence. Reconciliation treats missing ownership evidence as stale and repairs a wholly missing session, but the current implementation does not repair an existing partial session directory.
- Runner `Exception`s are durably recorded as failed and then re-raised; `KeyboardInterrupt` and `SystemExit` remain unhandled for normal process-level shutdown.
- Final metrics take `run_id` from retained session metadata. Rebuilt missing-session metadata uses the reconciling service's run ID and live process identity.
- Pat's one allowed MEDIUM retry fixed the live-owner wedge from runner exceptions, but remained unfixed for regression coverage and partial-session finalization; the attempt is stamped `medium-retry:unfixed` for PRD-level review.

## Task 6 — Implement the foreground supervisor loop and effects

- Workflow launches route `work.next_phase` first and fall back to `work.phase`; capability timeout selection currently uses the reverse order, which Pat left as a LOW consistency finding.
- Run and session metadata use the supervisor process's own PID/start identity. Signal interruption is finalized with decision `halt` and the shell-compatible signal exit code.
- Raw stdout is read directly from the owned process pipe with `os.read`; driver decode remains behind `RawFirstDecoder` so retained bytes precede parsing.
- Setup/evidence failures finalize the completion record and pending metric as `halt`, clean the owned process group, close evidence writers, then re-raise. A regression test covers launch and evidence-limit failures.
- When no child exit exists, the completion record currently uses `returncode=-1` with `signal=null`; Pat left this sentinel collision as LOW.
- Pat's one allowed MEDIUM retry closed the child-leak/unfinalized-metric path. Remaining LOW notes cover park return semantics, capability error chaining, route-order consistency, assert-based self identity, small wrapper/tuple simplifications, startup ordering, and the no-child sentinel.
- The one permitted style-fix pass initially cleaned the task, but the MEDIUM repair left `_collect` at 54 lines and `_conclude` at 51; the attempt records the final style gate as failed for PRD-level review.

## Task 7 — Expose supervisor lifecycle commands through the installed CLI

- Provider construction stays under `ovcaq.drivers`; the edge adapter maps the supervisor's resolved model back to the Claude driver's abstract tier without weakening the driver's explicit-model guard.
- Supervisor children inherit the prepared host environment with the driver's restricted/configured environment overlaid, matching the PRD 00006 adapter contract.
- The task-focused suite is green. Known full-suite inventory, distribution, documentation, and pre-existing provider-neutrality failures are assigned to task 8 and final verification rather than hidden in task 7.
- Pat's one allowed MEDIUM retry closed the stop-time process-exit race and preserved the JSON error envelope. Remaining LOW notes cover regression coverage for that race, private clock/settings access, lifecycle error-code granularity, readability, and test duplication.
- The stop-race repair reports `cannot signal the running supervisor` for any `OSError` raised while sending SIGTERM.

## Task 8 — Complete Phase 5 parity and end-to-end drain coverage

- The Phase 5 matrix contains all 69 PRD-00007 routes exactly once: 51 marked implemented and 18 legacy environment-variable spellings marked retired. The broad Phase 5 runtime/CLI subset passed 1,052 tests.
- Several implemented route destinations and proving node IDs were inferred from the task's legacy-semantics summary because the implementor was deliberately denied direct reads outside its write allowlist. The matrix verifies that each named destination and test function exists, but does not prove semantic correspondence; this is explicit review evidence, not a claim that those guesses are authoritative.
- Both legacy command rows are retired as public aliases even though current registry-driven OVCAQ lifecycle commands replace their behavior. All legacy environment-variable rows are retired in favor of TOML settings, RuntimePaths, and durable state.
- The new end-to-end fake drain assumes each phase is launched from committed `next_phase`, and the first build and review metric decisions are `continue`.
- The one allowed style-fix dispatch made no change after misreading the supplied violation as a test failure. The task records the remaining 52-line integration test as a failed style gate for PRD-level review; split hygiene is clean.

## Final verification regression cycle 1 — Task 2

- Default provider tier keys now live at the driver package edge and shared configuration imports only the provider-neutral phase-to-tier mapping. The targeted neutrality regression passes while public routing behavior remains unchanged.

## Final verification regression cycle 2 — Task 7

- Package declarations now include the three Phase 5 modules absent from the static wheel inventory. The sdist expectation excludes tracked `docs/dev` evidence because `pyproject.toml` deliberately excludes `/docs/dev` from source distributions.
- State protocol and parser inventory pins now include all five lifecycle commands. Calling `run` without `--no-tui` remains a usage error and the package-baseline test now asserts that required-argument contract.

## Task 12 — Capability execution rework

- Initial Ivan assumption: “Unfinished capability metrics stay pending until lifecycle reconciliation or completion supplies their terminal outcome, including when aggregate reconciliation runs independently.” Rejected before the source commit: startup normalization must still project retained pending rows as interrupted. The correction preserves that behavior and removes the redundant live-attempt aggregate rebuild instead. The final implementor report records no remaining assumptions.

## Task 13 — Workflow reporting rework

- Tess treats the supplied canonical phase/capability kinds and nullable capability fields as the metric contract. Retention means loading rows unchanged and in stream order; workflow totals exclude capability attempts.
- A string represents malformed non-mapping usage; existing coverage includes null and mapping values. Excluded unknown capability usage must not erase known workflow totals.
- Legacy session/convergence shapes follow characterized fixtures. Batch filtering retains canonical `batch_id` and legacy `batch` semantics. Ivan records no assumptions.

## Task 14 — Supplied phase settings rework

- Tess treats argv as owned by the already-selected driver, outside `LaunchRequest`; its new regression asserts the driver identity and launch requests. Existing adapter tests remain responsible for configured argv. Ivan records no assumptions.

