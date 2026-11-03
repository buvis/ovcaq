---
prd: dev/local/prds/wip/00003-state-kernel-v1.md
review: 2
date: 2026-08-27
head_sha: 9bd52bb9d140237c2d9962d878afb7ef4a9f0c01
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
---

# Review: 00003-state-kernel-v1

Diff range: `9c99065aaf0abad9d6a3f026b572b92291091576..9bd52bb9d140237c2d9962d878afb7ef4a9f0c01`

codex_rung_guard: not fired

pack: failed after one retry because the repository is not registered in gita; review continued with the mandated degraded sentinel.

## Review Summary

Reviewed: 20 completed tasks
PRDs checked: 00003-state-kernel-v1
Scope: incremental cycle-2 review of cycle-1 rework; 10,748 diff lines across 22 files.
Issue count: decreased from 21 in cycle 1 to 14 in cycle 2.

### Agent Status

- Alice: ✅ Available
- Blake: ✅ Available after one format/verdict-completeness retry
- Bob: ✅ Available via native fallback after the canonical Codex helper refused nested CLI dispatch
- Carl: ⚠️ Unavailable after the canonical Gemini helper refused nested CLI dispatch and its one retry

## Consolidated Findings

| Consensus | Severity | Issue | File | Task | Found By |
|-----------|----------|-------|------|------|----------|
| [2/3] | 🟡 | Pat warning is real: remove the unused `JSON_VALUE_MAP_ANNOTATION` constant | tests/state/test_schema.py:26 | 19 | ALICE, BOB |
| [2/3] | 🟡 | Pat warning is real: remove the unused `JSON_VALUE_MAP_ANNOTATION` constant | tests/state/test_schema_limits.py:32 | 19 | ALICE, BOB |
| [2/3] | 🟡 | Pat warning is real: remove the unused `JSON_VALUE_MAP_ANNOTATION` constant | tests/state/test_schema_constraints.py:16 | 19 | ALICE, BOB |
| [2/3] | 🟡 | Pat warning is real: remove the unused `T0` constant | tests/state/test_service_commands.py:25 | 19 | ALICE, BOB |
| [2/3] | 🟡 | Pat warning is real: the local `_ORIGINAL_POPEN` assignment is immediately shadowed by an import and `_ORIGINAL_POPEN_ATTRIBUTES` is never read; delete both assignments | tests/state/test_store_concurrency.py:14 | 19 | ALICE, BOB |
| [2/3] | 🟡 | Pat warning is real: the local `_ORIGINAL_POPEN` assignment is immediately shadowed by an import and `_ORIGINAL_POPEN_ATTRIBUTES` is never read; delete both assignments | tests/state/test_store_transactions.py:13 | 19 | ALICE, BOB |
| [2/3] | 🟡 | Pat warning is real: `_MINIMUM_DETAILS[minimum]` assumes every future minimum is tuple index 0 or 1; derive the message from the threshold or store it with each rule | src/ovcaq/state/schema.py:566 | 19 | ALICE, BOB |
| [1/3] | 🟠 | Escaped lone-surrogate JSON strings make `validate_state()` leak `UnicodeEncodeError` instead of the required path-aware `SchemaError`; catch UTF-8 encoding failures and test key/value paths | src/ovcaq/state/schema.py:381 | 13 | ALICE |
| [1/3] | 🟠 | Task creation rejects supplied IDs instead of assigning an ID only when absent | src/ovcaq/state/commands.py | P01-T08 | BLAKE |
| [1/3] | 🟠 | Schema validation accepts relative repository roots despite the documented absolute-path requirement | src/ovcaq/state/schema.py | P01-T02 | BLAKE |
| [1/3] | 🟡 | `ensure_project_config()` suppresses `FileExistsError` for directories and broken symlinks, allowing init to publish state and report success without an `ovcaq.toml` file | src/ovcaq/config.py:12 | 18 | ALICE |
| [1/3] | 🟡 | The crosswalk incorrectly classifies legacy batch.mode as a rename to semantically unrelated batch.status | docs/state-protocol.md | P01-T01 | BLAKE |
| [1/3] | 🟡 | [FIX] Typed schema resource-limit classification lacks positive CLI coverage: existing tests cover direct payload limits, raw state-byte limits, and spoof rejection, but never a below-16-MiB state that raises `ResourceLimitError`; add a nested string, collection, or open-map limit case asserting `resource_limit` and exit 11 | tests/state/test_cli_limits.py | 14 | BOB |
| [1/3] | ⚪ | [VERIFY] Cannot statically verify: the full pytest, Ruff check/format, mypy, and build gates; exact checks are `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src/ovcaq`, and `uv build` | N/A | general | BOB |

The final VERIFY item is resolved by current-HEAD evidence: pytest 754 passed in this cycle; the canonical style gate, Ruff check/format, mypy, and `uv build` passed at the same HEAD before review.

## Pat Warning Adjudication

Every requested Pat rerun warning is real; none was already resolved or a false positive.

| Warning | Evidence | Disposition |
|---------|----------|-------------|
| `JSON_VALUE_MAP_ANNOTATION` in `test_schema.py` | Declaration is the file's only occurrence | Real Medium; task 25 |
| `JSON_VALUE_MAP_ANNOTATION` in `test_schema_limits.py` | Declaration is the file's only occurrence | Real Medium; task 25 |
| `JSON_VALUE_MAP_ANNOTATION` in `test_schema_constraints.py` | Declaration is the file's only occurrence | Real Medium; task 25 |
| `T0` in `test_service_commands.py` | Declaration is the file's only occurrence | Real Medium; task 25 |
| local Popen captures in `test_store_concurrency.py` | `_ORIGINAL_POPEN` is shadowed by the `test_store` import; attributes snapshot is unused | Real Medium; task 25 |
| local Popen captures in `test_store_transactions.py` | `_ORIGINAL_POPEN` is shadowed by the `test_store` import; attributes snapshot is unused | Real Medium; task 25 |
| `_MINIMUM_DETAILS[minimum]` | Current thresholds are exactly 0/1; the threshold is used directly as a tuple index | Real Low; task 21 |

## Follow-up Tasks Created

1. Task 21 — [Review C2] Repair schema boundary validation (M)
2. Task 22 — [Review C2] Reconcile supplied task-ID behavior (M)
3. Task 23 — [Review C2] Reject invalid project-config path collisions (S)
4. Task 24 — [Review C2] Correct the batch.mode crosswalk disposition (S)
5. Task 25 — [Review C2] Remove split-test dead assignments (S)

These tasks remain pending. Cycle 2 equals `rework_cap=2`, and three unresolved High findings prohibit rework dispatch in this session.

## Alice

[ALICE] 🟠 Escaped lone-surrogate JSON strings make `validate_state()` leak `UnicodeEncodeError` instead of the required path-aware `SchemaError`; catch UTF-8 encoding failures and test key/value paths | File: src/ovcaq/state/schema.py:381 | Task: 13
[ALICE] 🟡 `ensure_project_config()` suppresses `FileExistsError` for directories and broken symlinks, allowing init to publish state and report success without an `ovcaq.toml` file | File: src/ovcaq/config.py:12 | Task: 18
[ALICE] 🟡 Pat warning is real: remove the unused `JSON_VALUE_MAP_ANNOTATION` constant | File: tests/state/test_schema.py:26 | Task: 19
[ALICE] 🟡 Pat warning is real: remove the unused `JSON_VALUE_MAP_ANNOTATION` constant | File: tests/state/test_schema_limits.py:32 | Task: 19
[ALICE] 🟡 Pat warning is real: remove the unused `JSON_VALUE_MAP_ANNOTATION` constant | File: tests/state/test_schema_constraints.py:16 | Task: 19
[ALICE] 🟡 Pat warning is real: remove the unused `T0` constant | File: tests/state/test_service_commands.py:25 | Task: 19
[ALICE] 🟡 Pat warning is real: the local `_ORIGINAL_POPEN` assignment is immediately shadowed by an import and `_ORIGINAL_POPEN_ATTRIBUTES` is never read; delete both assignments | File: tests/state/test_store_concurrency.py:14 | Task: 19
[ALICE] 🟡 Pat warning is real: the local `_ORIGINAL_POPEN` assignment is immediately shadowed by an import and `_ORIGINAL_POPEN_ATTRIBUTES` is never read; delete both assignments | File: tests/state/test_store_transactions.py:13 | Task: 19
[ALICE] 🟡 Pat warning is real: `_MINIMUM_DETAILS[minimum]` assumes every future minimum is tuple index 0 or 1; derive the message from the threshold or store it with each rule | File: src/ovcaq/state/schema.py:566 | Task: 19
R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass

## Blake

[BLAKE] 🟠 Task creation rejects supplied IDs instead of assigning an ID only when absent | File: src/ovcaq/state/commands.py | Task: P01-T08
[BLAKE] 🟠 Schema validation accepts relative repository roots despite the documented absolute-path requirement | File: src/ovcaq/state/schema.py | Task: P01-T02
[BLAKE] 🟡 The crosswalk incorrectly classifies legacy batch.mode as a rename to semantically unrelated batch.status | File: docs/state-protocol.md | Task: P01-T01
B1: fail
B2: fail
B3: fail
B4: pass
B5: fail
B6: pass
B7: pass
B8: pass
B9: pass
B10: fail
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: pass
B17: fail
B18: pass
B19: pass

## Bob

[BOB] 🟡 [FIX][Pat: real] `JSON_VALUE_MAP_ANNOTATION` is unused after the test split; delete the declaration | File: tests/state/test_schema.py:26 | Task: 19
[BOB] 🟡 [FIX][Pat: real] `JSON_VALUE_MAP_ANNOTATION` is unused after the test split; delete the declaration | File: tests/state/test_schema_limits.py:32 | Task: 19
[BOB] 🟡 [FIX][Pat: real] `JSON_VALUE_MAP_ANNOTATION` is unused after the test split; delete the declaration | File: tests/state/test_schema_constraints.py:16 | Task: 19
[BOB] 🟡 [FIX][Pat: real] `T0` is unused; delete the declaration | File: tests/state/test_service_commands.py:25 | Task: 19
[BOB] 🟡 [FIX][Pat: real] The local `_ORIGINAL_POPEN` capture is immediately shadowed by the import from `test_store`, while `_ORIGINAL_POPEN_ATTRIBUTES` is never read; remove both local assignments | File: tests/state/test_store_concurrency.py:14 | Task: 19
[BOB] 🟡 [FIX][Pat: real] The local `_ORIGINAL_POPEN` capture is immediately shadowed by the import from `test_store`, while `_ORIGINAL_POPEN_ATTRIBUTES` is never read; remove both local assignments | File: tests/state/test_store_transactions.py:13 | Task: 19
[BOB] ⚪ [FIX][Pat: real] `_MINIMUM_DETAILS[minimum]` couples diagnostic lookup to every minimum remaining a tuple index of 0 or 1; key details by minimum or store each detail with its rule | File: src/ovcaq/state/schema.py:566 | Task: 19
[BOB] 🟡 [FIX] Typed schema resource-limit classification lacks positive CLI coverage: existing tests cover direct payload limits, raw state-byte limits, and spoof rejection, but never a below-16-MiB state that raises `ResourceLimitError`; add a nested string, collection, or open-map limit case asserting `resource_limit` and exit 11 | File: tests/state/test_cli_limits.py | Task: 14
[BOB] ⚪ [VERIFY] Cannot statically verify: the full pytest, Ruff check/format, mypy, and build gates; exact checks are `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src/ovcaq`, and `uv build` | File: N/A | Task: general
R1: fail
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
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 14 findings
Tests: 754 passed, 0 failed, 0 skipped
