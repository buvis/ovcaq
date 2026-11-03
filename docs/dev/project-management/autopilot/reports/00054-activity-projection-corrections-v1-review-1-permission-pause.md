---
prd: docs/dev/project-management/prds/wip/00054-activity-projection-corrections-v1.md
review: 1
date: 2026-10-15
head_sha: 092be044697f52fe14e431e1c1cc2805575fd67b
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
dispatch_rows:
  bob: daec48f0
---

# Review evidence — permission pause

Diff range: 65926983d26de98d55692fd1232ad12a1de48caf..092be044697f52fe14e431e1c1cc2805575fd67b

codex_rung_guard: not fired
provider_review_guard: satisfied
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/alice-output-00054-c1-20261015.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/blake-output-00054-c1-20261015.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/bob-output-00054-c1-20261015.txt.receipt.json

The model-provider guard supersedes the legacy launcher guard; Eve did not run. All required reviewers served claude-opus-5-5 at helper-requested xhigh in fresh isolated sessions. Carl was not dispatched: automatic approval review rejected repository-context export to Gemini/Copilot as not specifically authorized. Operator decision pending: authorize Carl or explicitly skip the optional reviewer. This evidence draft is deliberately outside canonical reviews: no decision gate, adjudication, task creation, repair, cap change or convergence has occurred.

Pack unavailable (engram: repository unregistered). Mechanical shape check: no findings. Fail-first replay skipped because sandbox denied .git/worktrees creation. Build verification reused from last-verification.json at ab3101b; Blake independently ran the suite with 7249 passed/2 failed, then viewer fallback 14/14 passed alone, plus 80/80 PRD tests. Preserve both outcomes for adjudication; do not silently replace either.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/3] | 🟠 | Claude's decoder gives every text and thinking block in one message the same `message_id` (verified: decoding `tests/fixtures/claude/v1/healthy.jsonl` line 2 yields text and thinking, both `message-1`). The exact-ID key at model.py:576 therefore lets the thinking block replace the text, and "Working on the sanitized fixture." never reaches the panel. The test at tests/tui/test_activity_projection.py:83 (claude param) pins this kind-changing replacement as intended, and no test decodes a real Claude multi-block message. Fix: key on (kind, id), or add a block index at the decoder edge. If neither, record it as a deferred design gap. | src/ovcaq/tui/model.py:576 | 1 | ALICE, BLAKE, BOB |
| R2 | [3/3] | 🟡 | New doc text says "Plans display up to 256 steps", but `_observe_activity` passes the joined plan through `display_text` with its default 512-char cap (src/ovcaq/tui/model.py:604, src/ovcaq/tui/model.py:136). Only about 40 short steps can show before the "…" cut. This adds a new inaccurate display claim in a task whose job was to make the docs truthful. Fix: state the character bound instead. | docs/driver-protocol.md:339 | 3 | ALICE, BLAKE, BOB |
| R3 | [2/3] | 🟡 | Codex command detail is `command\noutput`, and `display_text` strips the `\n`, so the operator sees the command and its output run together ("printf exampleexample"). The new test asserts that string as the expected value (tests/tui/test_rework_activity.py:122), which treats an inaccurate render as intent. That conflicts with the PRD metric that tools "render accurate detail". Fix: turn line breaks into a visible separator before sanitizing, or record a deferral and stop asserting the fused text. | tests/tui/test_rework_activity.py:122 | 1 | ALICE, BLAKE |
| R4 | [1/3] | 🟠 | The Phase 0 acceptance says the tests must exercise "both adapters' decoded payloads". For Claude, only tools and the rate-limit warning are decoded. Every Claude message test builds its payload by hand with `_event`, so the multi-block collapse above was never seen. (I scored the rubric phases in order: B15 is Phase 0, B16 is Phase 1, B17 is Phase 2.) | tests/tui/test_activity_projection.py:82 | 1 | BLAKE |
| R5 | [1/3] | 🟡 | The window size `20` is repeated as a literal six times in `activity_panel`. Replace it with one module constant (e.g. `ACTIVITY_WINDOW = 20`). A constant is not configuration, and the design already expects constants here. | src/ovcaq/tui/panels.py:91 | 2 | ALICE |
| R6 | [1/3] | 🟡 | One critical scenario from the Test Strategy has no test in this layer: "synthetic credentials cannot appear unsanitized". No test under tests/tui puts a credential into a decoded or rendered activity payload; `rg` finds no `sk-`, `REDACTED` or `secret` in an activity test. The code is safe today because `Observation` construction runs `sanitize_json`. But the new `detail` fallback path has no test that would catch a regression. | tests/tui/test_activity_window.py:228 | 2 | BLAKE |
| R7 | [1/3] | ⚪ | Tool identity still uses `display_text(str(tool_id))`, which sanitizes and truncates the ID. Message IDs were just fixed for the same problem (same defect class, bug-fix discipline). Real tool IDs are short today, so the impact is low. | src/ovcaq/tui/model.py:595 | 1 | ALICE |
| R8 | [1/3] | ⚪ | The `marker` param in `test_decoded_idless_errors_survive_repeated_errors_and_turn_markers` decodes `turn.completed` / `session.failed`, and neither produces an `activity.message`. Both param cases exercise the same thing, and the name "turn markers" misleads. The real turn marker is `turns` (healthy[1]). Fix: drop the param. | tests/tui/test_activity_projection.py:126 | 1 | ALICE |
| R9 | [1/3] | ⚪ | `changed.activity is activity` and the repeated `changed == original` can never fail, because the frozen, slotted dataclass holds tuples. Keep a single equality check. | tests/tui/test_activity_window.py:211 | 2 | ALICE |
| R10 | [1/3] | ⚪ | The checks `elif started.payload.get("detail")` and `if terminal.payload.get("detail")` are always true for decoded Codex tools, because `item_tool` returns None when detail is missing (src/ovcaq/drivers/codex_events.py:277). Make these assertions unconditional. | tests/tui/test_rework_activity.py:109 | 1 | ALICE |
| R11 | [1/3] | ⚪ | Tool identity still uses `display_text(tool_id)`, which caps at 512 characters and strips controls. Two distinct tool IDs that share a 511-character prefix, or differ only in control or format characters, merge into one entry. This is the same bug the PRD fixed for message IDs (see `test_distinct_long_message_ids_are_not_merged_by_display_truncation`). | src/ovcaq/tui/model.py:595 | 1 | BLAKE |
| R12 | [1/3] | ⚪ | Some tests still pair provider `claude` with shapes the Claude decoder never emits: `kind: error` with `text` and `message_id`, and `kind: plan` with `items`. This is the invented-payload pattern R27 objected to, kept for messages. | tests/tui/test_rework_activity.py:180 | 1 | BLAKE |
| R13 | [1/3] | ⚪ | The "N activity entries omitted" line is printed after all 20 lanes instead of right after the activity block. In a panel limited by height, it is the first line cut off, and it reads as if it belongs to the lanes. A test locks in this placement. | src/ovcaq/tui/panels.py:101 | 2 | BLAKE |
| R14 | [1/3] | ⚪ | Exit-criteria run: the full `uv run pytest` gave 7249 passed and 2 failed, both in `test_ordinary_project_ui_failure_restores_pty_and_reuses_observer[construction|start]`. That file passed 14/14 when rerun alone. I ran ruff and mypy at the same time as the suite, so the failures look timing-sensitive under load, and this PRD does not touch the file. ruff check, ruff format --check, mypy and `uv build` all passed. The PRD's own test files passed 80/80. I did not run `uv sync --all-groups`. | tests/integration/test_viewer_fallback.py:338 | general | BLAKE |
| R15 | [1/3] | ⚪ | The `if`/`elif` guards on `payload.get("detail")` are always true for all 7 Codex fixture pairs, since every detail projection is non-empty. If the decoder ever produced an empty detail, the detail assertions would silently not run | tests/tui/test_rework_activity.py | 1 | BOB |
| R16 | [1/3] | ⚪ | `original = replace(changed)` followed by `assert changed == original` (written twice) and the `is` identity checks can never fail, because ProjectView is frozen and its fields are tuples. Line 215 repeats line 213 | tests/tui/test_activity_window.py | 2 | BOB |
| R17 | [1/3] | ⚪ | `display_text` drops newlines with no separator, so Codex command detail shows as "printf exampleexample". The tests now pin this joined-together form as the expected value | src/ovcaq/tui/model.py | 1 | BOB |
| R18 | [1/3] | ⚪ | Tool identity is still keyed by `display_text(tool_id)` (`src/ovcaq/tui/model.py:595`), which cleans and truncates the ID at 512 characters. Only message IDs got exact identity | src/ovcaq/tui/model.py | 1 | BOB |
| R19 | [1/3] | ⚪ | Both omission lines come after up to 40 rows, so a short live terminal may clip them | src/ovcaq/tui/panels.py | 2 | BOB |
| R20 | [1/3] | ⚪ | Cannot statically verify: fail-first replay of the changed tests against 65926983 (the replay was skipped because the worktree could not be created) | N/A | general | BOB |

## Alice

[ALICE] 🟡 Claude's decoder gives every text and thinking block in one message the same `message_id` (verified: decoding `tests/fixtures/claude/v1/healthy.jsonl` line 2 yields text and thinking, both `message-1`). The exact-ID key at model.py:576 therefore lets the thinking block replace the text, and "Working on the sanitized fixture." never reaches the panel. The test at tests/tui/test_activity_projection.py:83 (claude param) pins this kind-changing replacement as intended, and no test decodes a real Claude multi-block message. Fix: key on (kind, id), or add a block index at the decoder edge. If neither, record it as a deferred design gap. | File: src/ovcaq/tui/model.py:576 | Task: 1
[ALICE] 🟡 Codex command detail is `command\noutput`, and `display_text` strips the `\n`, so the operator sees the command and its output run together ("printf exampleexample"). The new test asserts that string as the expected value (tests/tui/test_rework_activity.py:122), which treats an inaccurate render as intent. That conflicts with the PRD metric that tools "render accurate detail". Fix: turn line breaks into a visible separator before sanitizing, or record a deferral and stop asserting the fused text. | File: tests/tui/test_rework_activity.py:122 | Task: 1
[ALICE] 🟡 New doc text says "Plans display up to 256 steps", but `_observe_activity` passes the joined plan through `display_text` with its default 512-char cap (src/ovcaq/tui/model.py:604, src/ovcaq/tui/model.py:136). Only about 40 short steps can show before the "…" cut. This adds a new inaccurate display claim in a task whose job was to make the docs truthful. Fix: state the character bound instead. | File: docs/driver-protocol.md:339 | Task: 3
[ALICE] 🟡 The window size `20` is repeated as a literal six times in `activity_panel`. Replace it with one module constant (e.g. `ACTIVITY_WINDOW = 20`). A constant is not configuration, and the design already expects constants here. | File: src/ovcaq/tui/panels.py:91 | Task: 2
[ALICE] ⚪ Tool identity still uses `display_text(str(tool_id))`, which sanitizes and truncates the ID. Message IDs were just fixed for the same problem (same defect class, bug-fix discipline). Real tool IDs are short today, so the impact is low. | File: src/ovcaq/tui/model.py:595 | Task: 1
[ALICE] ⚪ The `marker` param in `test_decoded_idless_errors_survive_repeated_errors_and_turn_markers` decodes `turn.completed` / `session.failed`, and neither produces an `activity.message`. Both param cases exercise the same thing, and the name "turn markers" misleads. The real turn marker is `turns` (healthy[1]). Fix: drop the param. | File: tests/tui/test_activity_projection.py:126 | Task: 1
[ALICE] ⚪ `changed.activity is activity` and the repeated `changed == original` can never fail, because the frozen, slotted dataclass holds tuples. Keep a single equality check. | File: tests/tui/test_activity_window.py:211 | Task: 2
[ALICE] ⚪ The checks `elif started.payload.get("detail")` and `if terminal.payload.get("detail")` are always true for decoded Codex tools, because `item_tool` returns None when detail is missing (src/ovcaq/drivers/codex_events.py:277). Make these assertions unconditional. | File: tests/tui/test_rework_activity.py:109 | Task: 1

Verification: 131 passed on the five related TUI test files (activity_projection, activity_window, rework_activity, panels, codex_projection), and `ruff check` is clean on src/ovcaq/tui and tests/tui. I did not re-run the fail-first replay: the harness skipped it because adding the worktree failed. I checked the new tests against the pre-change code by reading them instead.

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass
## Blake

[BLAKE] 🟠 Decoded Claude messages with more than one block lose content. The Claude decoder gives every text and thinking block of one assistant message the same `message.id`. `_observe_activity` keys on that ID, so each later block replaces the earlier one. I fed line 2 of the checked-in `claude/v1/healthy.jsonl` (a text block, then a thinking block, then a tool, all with id `message-1`) through the observer. It projected only `thinking: Check the public contract.` and `Read: started`; the assistant text "Working on the sanitized fixture." disappeared. This is not a faithful projection of the adapter's real payloads, and no test decodes Claude text or thinking frames. | File: src/ovcaq/tui/model.py:576 | Task: 1
[BLAKE] 🟠 The Phase 0 acceptance says the tests must exercise "both adapters' decoded payloads". For Claude, only tools and the rate-limit warning are decoded. Every Claude message test builds its payload by hand with `_event`, so the multi-block collapse above was never seen. (I scored the rubric phases in order: B15 is Phase 0, B16 is Phase 1, B17 is Phase 2.) | File: tests/tui/test_activity_projection.py:82 | Task: 1
[BLAKE] 🟡 Codex command tool detail is not shown accurately. `command_detail` builds `"{command}\n{output}"`, and `display_text` drops the newline, so the command and its output run together. A test locks this in as the expected result: `detail == "printf exampleexample"`. The success metric asks that tools "render accurate detail"; replacing the newline with a space or a separator would stay terminal-safe. | File: tests/tui/test_rework_activity.py:122 | Task: 1
[BLAKE] 🟡 One critical scenario from the Test Strategy has no test in this layer: "synthetic credentials cannot appear unsanitized". No test under tests/tui puts a credential into a decoded or rendered activity payload; `rg` finds no `sk-`, `REDACTED` or `secret` in an activity test. The code is safe today because `Observation` construction runs `sanitize_json`. But the new `detail` fallback path has no test that would catch a regression. | File: tests/tui/test_activity_window.py:228 | Task: 2
[BLAKE] ⚪ Tool identity still uses `display_text(tool_id)`, which caps at 512 characters and strips controls. Two distinct tool IDs that share a 511-character prefix, or differ only in control or format characters, merge into one entry. This is the same bug the PRD fixed for message IDs (see `test_distinct_long_message_ids_are_not_merged_by_display_truncation`). | File: src/ovcaq/tui/model.py:595 | Task: 1
[BLAKE] ⚪ Some tests still pair provider `claude` with shapes the Claude decoder never emits: `kind: error` with `text` and `message_id`, and `kind: plan` with `items`. This is the invented-payload pattern R27 objected to, kept for messages. | File: tests/tui/test_rework_activity.py:180 | Task: 1
[BLAKE] ⚪ The "N activity entries omitted" line is printed after all 20 lanes instead of right after the activity block. In a panel limited by height, it is the first line cut off, and it reads as if it belongs to the lanes. A test locks in this placement. | File: src/ovcaq/tui/panels.py:101 | Task: 2
[BLAKE] ⚪ The docs say "Plans display up to 256 steps". The plan detail is capped at 512 characters by `display_text`, so a rendered plan shows only about 40 short steps before the "…". The sentence is technically true but misleading. | File: docs/driver-protocol.md:339 | Task: 3
[BLAKE] ⚪ Exit-criteria run: the full `uv run pytest` gave 7249 passed and 2 failed, both in `test_ordinary_project_ui_failure_restores_pty_and_reuses_observer[construction|start]`. That file passed 14/14 when rerun alone. I ran ruff and mypy at the same time as the suite, so the failures look timing-sensitive under load, and this PRD does not touch the file. ruff check, ruff format --check, mypy and `uv build` all passed. The PRD's own test files passed 80/80. I did not run `uv sync --all-groups`. | File: tests/integration/test_viewer_fallback.py:338 | Task: general

B1: fail
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: pass
B17: pass
B18: pass
B19: pass
## Bob

[BOB] ⚪ `docs/driver-protocol.md:339` says "Plans display up to 256 steps", but the joined plan text is capped at 512 characters (`src/ovcaq/tui/model.py:604`, then again in the panel), so only about 40 short steps can actually show | File: docs/driver-protocol.md | Task: 3
[BOB] ⚪ The `if`/`elif` guards on `payload.get("detail")` are always true for all 7 Codex fixture pairs, since every detail projection is non-empty. If the decoder ever produced an empty detail, the detail assertions would silently not run | File: tests/tui/test_rework_activity.py | Task: 1
[BOB] ⚪ `original = replace(changed)` followed by `assert changed == original` (written twice) and the `is` identity checks can never fail, because ProjectView is frozen and its fields are tuples. Line 215 repeats line 213 | File: tests/tui/test_activity_window.py | Task: 2
[BOB] ⚪ Claude gives every content block in one message the same `message.id` (`src/ovcaq/drivers/claude.py:215`). Under the new message-ID update rule, the text block "Working on the sanitized fixture." in the checked-in `claude/v1/healthy.jsonl` line 2 gets replaced by the thinking block from the same message. This behavior existed before this change, and the contract requires it | File: src/ovcaq/tui/model.py | Task: 1
[BOB] ⚪ `display_text` drops newlines with no separator, so Codex command detail shows as "printf exampleexample". The tests now pin this joined-together form as the expected value | File: src/ovcaq/tui/model.py | Task: 1
[BOB] ⚪ Tool identity is still keyed by `display_text(tool_id)` (`src/ovcaq/tui/model.py:595`), which cleans and truncates the ID at 512 characters. Only message IDs got exact identity | File: src/ovcaq/tui/model.py | Task: 1
[BOB] ⚪ Both omission lines come after up to 40 rows, so a short live terminal may clip them | File: src/ovcaq/tui/panels.py | Task: 2
[BOB] ⚪ Cannot statically verify: fail-first replay of the changed tests against 65926983 (the replay was skipped because the worktree could not be created) | File: N/A | Task: general

FIX:
- Plan step count in the docs overstates what is shown — docs/driver-protocol.md:339 — change to "Plans summarize up to 256 steps with `done:`/`pending:` markers within the bounded detail".
- Detail assertions can be skipped silently — tests/tui/test_rework_activity.py:109 — remove the `elif`/`if` guards at lines 109 and 119 and assert detail equality unconditionally for every parametrized pair.
- Repeated self-comparison that cannot fail — tests/tui/test_activity_window.py:215 — delete the second `assert changed == original`. Keep one comparison to show the acceptance criterion is met.

VERIFY:
- New tests are not confirmed to fail on the old code — check out 65926983 in a scratch worktree, copy the HEAD versions of `tests/tui/test_activity_projection.py`, `tests/tui/test_activity_window.py` and `tests/tui/test_rework_activity.py` over it, and run `uv run pytest` on those three files. Expect failures in the ID-less distinctness, text/detail fallback, long-ID, follower-snapshot, reset and window tests. The real-ID eviction case and the Claude tool test should pass, since that behavior did not change.

KNOWN:
- Claude blocks that share a message ID collapse into one entry — the design contract requires that a message_id updates its existing item. Giving each block its own identity needs decoder or event-schema work, which the design rejected (alternative 3). Should go in a backlog PRD.
- Joined newline text in tool detail — the contract says to keep the existing `display_text` sanitization. Changing how it handles newlines affects every panel.
- Tool IDs are cleaned before use as keys — the exact-ID rule in the contract names `message_id` only. Native tool IDs are short, so no reported defect depends on this.
- Omission lines can be clipped in a short terminal — the contract fixes where they go ("append"). This was already recorded as a non-blocker in design review dispatch 2.

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass
Verdict: 20 findings
Tests: 7251 passed, 0 failed, 0 skipped (reused from last-verification.json at ab3101b; separate Blake failures retained above)
