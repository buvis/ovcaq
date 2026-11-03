# Autocodex metrics crash recovery — 2026-09-13

## Failure Capture
- Session / task: `b24cf97cdb084723964bcf00073261e5`; investigate and repair the launcher crash, assess restart readiness.
- Goal in progress: PRD `00004-workflow-core-v1.md`, fresh review cycle 14.
- Error: `TypeError: CodexLoop._append_metrics() takes 7 positional arguments but 8 were given`.
- Last successful step: review committed a valid `data_loss_risk` pause and complete review evidence; raw session ended with `turn.completed`.
- Last failed tool / command: `autocodex`, inherited `Loop._run_loop` calling the adapter's metrics hook before the action branch.
- Repeated pattern seen: 60-second progress heartbeats during the review; one deterministic post-session Python signature failure, not a repeated agent failure.
- Context pressure: no overflow reported; raw session contains 374 events and a successful terminal event.
- Environment assumptions to verify: installed autopilot 0.5.2 now passes `effort`; personal adapter is tracked in the home dotfiles repository and has pre-existing edits; paused state, review receipts, locks and restart behavior must remain intact.

## Recovery Action
- Diagnosis chosen: upstream metrics hook gained an `effort` parameter; the overriding adapter retained its old signature.
- Smallest action taken: accept and record `effort`; add four parameterized review-pause regressions and effort assertions to the existing full-lifecycle subprocess test; install only the three tested files after checking original hashes.
- Why this is safe: no agent launches, PRD repairs, state transitions or plugin-cache changes are needed to repair metrics compatibility. Preserve existing personal-tool changes.
- What evidence would prove the fix worked: regression fails before the patch and passes after; full adapter suite passes against the installed plugin; real state and review receipt validate; startup reports the saved pause without changing state.

## Restart assessment
The launcher crash is fixed, but unattended workflow continuation remains blocked by the recorded review pause. Tasks 7 and 8 address a confirmed ledger durability defect and its regression coverage. The launcher fix alone does not authorize clearing that pause or implementing those PRD tasks.

The installed [run-autopilot skill](/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.2/skills/run-autopilot/SKILL.md:300) explicitly requires “Detected data-loss risk” → “PAUSE.” The [host recovery contract](/Users/bob/.config/autocodex/host.md:11) requires an operator decision before clearing a pause or starting repairs. Next step: interactive recovery for the pending tasks, preserving cycle 14, cap 2, the existing batch and fresh work/review boundary, then restart `autocodex`.

## Verification
- Before fix: all four added review-pause cases fail with the exact reported `TypeError`, covering both inherited `run` and `run_once` callers and xhigh/medium effort.
- After fix: 64 tests pass in the sandbox; two existing process-group tests fail solely because `ps` is prohibited. Both pass on the approved retry outside the sandbox. Total: all 66 tests pass, zero skipped.
- Installed files: five targeted cases pass again, including the real subprocess build → review → finalize lifecycle with synthetic agents. No paid model inference was launched.
- Ruff lint and formatting checks pass; diff whitespace checks pass.
- Installed file hashes exactly match tested bytes; adapter and upstream metrics signatures match.
- Real cycle-14 state schema, complete saved review, immutable Bob receipt and plugin-version gate validate. The autocodex lock is available. Startup schema gate refuses the recorded pause with zero launches.
- Real `state.json` remains byte-for-byte unchanged: SHA-256 `8f26ee434592b6d0596458a7c0f6496a922f61e8bd7b2bbf6ea07bf33796d13a`.
- Raw review session has a successful terminal event and no parsed error. The failed metrics append did not discard review artifacts or committed state; no historical metrics row was fabricated.
- Changes live in `~/.config/autocodex/{adapter.py,test_adapter.py,test_integration.py}`. Pre-existing dotfiles edits were preserved; no commit was made over those unrelated edits. Exact task-only [patch](autocodex-metrics-fix-20260913.patch) is retained.
- Cleanup: removed this task's disposable repair/test directory. Repository has only its main worktree and master branch; no worktrees, branches or executable plans were created by this repair. Active architecture plans and referenced historical handoffs remain in place.

## Agent Self-Debug Report
- Session / task: autocodex cycle-14 metrics crash investigation and restart assessment.
- Failure: post-session metrics dispatch raised a Python argument-count error before pause reporting.
- Root cause: personal adapter override drifted from the installed autopilot metrics hook signature.
- Recovery action: installed the two-line compatibility fix and regression coverage after reproducing the original exception.
- Result: success for the requested launcher repair; workflow remains deliberately paused for the separate PRD defect.
- Token / time burn risk: no need to repeat the completed review to recover this crash. Repair tasks still need their normal fresh work/review sessions.
- Follow-up needed: authorize interactive recovery for tasks 7–8 before unattended continuation.
- Preventive change encoded: both inherited metrics call paths and per-phase effort are now exercised against the resolved installed plugin. Run the adapter suite when updating autopilot.

## Fresh handoff verification — 2026-09-13 19:43 CEST
- `mise exec -- uv run pytest -q --basetemp /private/tmp/ovcaq-handoff-20260913-1941`: 1359 passed in 43.65s, zero failures/skips.
- `.venv/bin/ruff check --no-cache .` and `ruff format --check --no-cache .`: pass, 123 files formatted.
- `mise exec -- uv run mypy src/ovcaq`: pass, 51 source files. `mise exec -- uv build`: source distribution and wheel built.
- Fresh-session prompt: `dev/local/tmp/00004-handoff-20260913-1941.md`; no state changes. Its pasted request supplies the bounded Resume authorization for the receiving session.
