# Task 27 Pat

Bundled wrapper; tools disabled; high effort env override; Anthropic requested sonnet, observed claude-sonnet-5-5; session 108f27c8-a5dc-4ef9-9cf7-5ac9eaa14987. Raw source ~/.claude/projects/-Users-bob-git-src-github-com-buvis-ovcaq/108f27c8-a5dc-4ef9-9cf7-5ac9eaa14987.jsonl. Closure resolved; parser exit0.

CLOSURE | resolved | 🟡 src/ovcaq/drivers/codex_activity.py:6: `codex_activity.py` is a third module (43 lines) outside the design's module placement (codex.py + codex_events.py) and outside every task's writable Location, and it forced a packaging-inventory edit. Fold `item_activity` into codex_events.py (found by: ALICE, BOB) | The diff deletes `codex_activity.py`, adds `item_activity` to `codex_events.py` with an identical body, and `codex.py` now imports it from `codex_events`. The recorded run shows 34 tests passing and the parent red on the missing export.

LOW | tests/drivers/test_codex_rework_placement.py:1 | The file adds 140 lines of tests for a pure relocation. Several cases overlap: the plain-text and 4095/4096-length checks both assert pass-through, and the sanitize tests partly repeat each other across item types. | Keep the import-location test, the sanitize/bound test and the invalid-input table. Merge the length and plain-text cases. This is optional, because the task requires preserving all assertions.
