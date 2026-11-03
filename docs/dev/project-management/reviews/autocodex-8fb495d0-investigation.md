# Autocodex session investigation — 2026-09-13

## Failure Capture

- Session / task: `8fb495d042c640249ced99f611e3b06d`, PRD `00004-workflow-core-v1.md`, cycle 13 review at `be5e385bd9714952b4803ee30f7c72e661c278f2`.
- Goal in progress: finish the fresh mandatory review and commit its outcome.
- Error: committed `pause_reason.site = data_loss_risk`; R13-01 reports successful defer publication after an ancestor replacement without confirming the replacement entry in its parent.
- Last successful step: state/schema, task counts, review rubrics/receipt, contract card and clean-HEAD audit passed; session ended with `turn.completed`, process exit 0, `capped: false`.
- Last failed tool / command: `item_205` final audit compared a trailing newline against CLI-normalized contract text. `item_207` corrected the comparison with `.strip()` and passed. This was not the terminal cause.
- Repeated pattern seen: 60-second launcher heartbeats, not repeated launches. The ancestry-durability issue family recurred across cycles 11–13; this specific between-iteration replacement was first detected in cycle 13.
- Context pressure: no context-cap event or overflow recorded. Wrapper usage is 10,561,294 cumulative input tokens, including 10,337,152 cached tokens; 38,553 output tokens. These are cumulative API usage, not simultaneous context occupancy.
- Environment assumptions to verify: current HEAD matches reviewed source; installed-wheel evidence matches that source; Bob's receipt remains valid; workflow state remains paused at 13/16 tasks with cap 2.

## Recovery Action

- Diagnosis chosen: product durability defect caused the review policy to pause; the launcher and mandatory reviewer dispatch completed successfully.
- Smallest action: independently validate persisted review/state evidence and rerun the existing deterministic replacement probe against the current checkout.
- Why safe: the probe uses its own automatically cleaned temporary directory under `/private/tmp`. No production source or workflow-state edits, agent launches, cap changes or lifecycle transitions.
- Evidence needed: successful publication with `replacement_happened: true` and `parent_confirmed_after_replacement: false` confirms the defect remains. A future repair must reject the replacement or confirm its parent before returning success, while preserving prior crash/replay/concurrency guarantees.
- Verification result: independently reproduced on the unchanged reviewed HEAD. The operation returned an existing ledger containing one expected record; replacement occurred, and its parent was not fsynced afterward. State schema, 13/16 task counts, complete review rubrics and Bob's immutable receipt all passed. State bytes were unchanged (SHA-256 `3da847cd04ad43758167e336954245871b5c87bf81891524dedddf7c1a43e4be`). See the [independent check](autocodex-8fb495d0-investigation-check.json).

## Agent Self-Debug Report

- Session / task: cycle 13 review, session `8fb495d042c640249ced99f611e3b06d`.
- Failure: intentional whole-batch pause on R13-01, an unresolved High durability risk. No physical power-loss data loss was observed.
- Root cause: `_ensure_directory_chain` closes each confirmed directory and forgets its identity. The next iteration reopens that pathname as its parent and accepts a replacement inode. It fsyncs the replacement for its child but never reconfirms the replacement's own entry in the grandparent.
- Recovery action: diagnosis and bounded reproduction only; retain the existing pause and queued tasks 4/5/6.
- Result: success for diagnosis; product repair remains pending. Only this report and its check artifact were added under ignored `dev/local/reviews/`; the tracked worktree is clean. The probe cleaned its temporary directory, and there are no additional Git worktrees to remove.
- Token / time burn risk: this review took 1,662.114 seconds (27m 42s), 13:24:02–13:51:44 Europe/Prague. Bob's receipt spans 10m 28s. Repeating the full review before repairing the reproduced defect spends another review without resolving it. Earlier quota/DNS failures belong to different attempts.
- Follow-up needed: bounded ancestry-identity/access repair (task 4), exact contention assertions (task 5), redundant test-assertion cleanup (task 6), then a fresh complete review. Cycle 13 and cap 2 are preserved; this is not a cap pause.
- Preventive change to encode later: carry directory identity across traversal steps and add the replacement interleaving to regression coverage. The wrapper could surface the latest agent progress instead of repeating only the raw-log path.

## Evidence

- [Canonical review](00004-workflow-core-v1-review-13.md)
- [Independent reproduction and state/receipt validation](autocodex-8fb495d0-investigation-check.json)
- [Installed-wheel probe result](00004-cycle-13-approved-installed-probe.json)
- [Existing reproduction](ancestry_replacement_probe_13.py)
- [Bob receipt](bob-output-00004-13-20260913-approved.txt.receipt.json)
- [Session metrics](../autopilot/autocodex-metrics.jsonl)
- [Raw session](../autopilot/autocodex-sessions/8fb495d042c640249ced99f611e3b06d.jsonl)
- [Source loop](/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/workflow/_files.py:252)
- [Launcher heartbeat](/Users/bob/.config/autocodex/driver.py:184)

The installed [run-autopilot procedure](/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.1/skills/run-autopilot/SKILL.md:297) explicitly maps “Detected data-loss risk” to “PAUSE” in both modes. This explains the previous session's stop; the current request is investigation, not authorization to clear the pause. The [host recovery contract](/Users/bob/.config/autocodex/host.md:5) requires an operator decision before repairs and preserves the fresh work/review boundary.
