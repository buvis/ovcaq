# Implementation model audit

- Task 1: tess-1, session 01a13c02-db36-72f2-9e0b-bba8f8d1579e, models ['gpt-6.1-sol', 'gpt-6.1-sol', 'gpt-6.1-sol', 'gpt-6.1-sol']; observed turn_context rows, provider from session_meta.
- Task 1: ivan-1, session 01a13c14-48d2-79b1-8468-7dd055d07284, models ['gpt-6.1-sol']; observed turn_context rows, provider from session_meta.
- Task 1: ivan-1-repair, session 01a13c16-a6c9-7180-85b0-fc5ef5b43fe5, models ['gpt-6-astra']; observed turn_context rows, provider from session_meta.
- Task 1: task-1-harness-repair, session 01a13bfc-7cda-77e1-a993-9778c7536d9b, models ['gpt-6.1-sol']; observed turn_context rows, provider from session_meta.
- Task 2: tess2, session 01a13f81-81fa-7d32-8e43-61499609ab6f, models ['gpt-6.1-sol', 'gpt-6.1-sol']; observed turn_context rows, provider from session_meta.
- Task 2: ivan2, session 01a13f86-37d0-7ea2-a565-6a5eddca6956, models ['gpt-6.1-sol']; observed turn_context rows, provider from session_meta.
- Task 2: ivan2_status, session 01a13f87-4e7e-71c3-85ec-9a4e17d74f89, models ['gpt-6-astra']; observed turn_context rows, provider from session_meta.
- Task 3: ivan3, session 01a13f89-3974-7a41-bd03-dd03485f0e47, models ['gpt-6.1-sol']; observed turn_context rows, provider from session_meta.

Correlated using tasks attempts worker_session_id, test_author_session_id and worker_dispatch_id, dispatch ledger, and reports/00054-build-progress.md commit evidence. Task 1 tests: 6a651ef/427c168/0898d80; coordinator harness repair 9f6e04b; workers b85afb3/13e897d. Task 2 tests 1700e69/53849e8; workers 8be231d/4a9ebba. Task 3 ab3101b. All contributing turns retained. Root session counts only its task 1 test harness and changelog edits. Reverted Devon mutants, catchup, planning/coordinator-only actions and read-only Pat/design reviewers excluded. Launcher Codex is separately recorded, never used to infer model origin. Existing attempt actual_model/provider values agree with observed metadata; no history rewritten.
