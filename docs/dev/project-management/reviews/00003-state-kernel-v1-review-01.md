---
prd: dev/local/prds/wip/00003-state-kernel-v1.md
review: 1
date: 2026-08-27
head_sha: 9c99065aaf0abad9d6a3f026b572b92291091576
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
---

# Review: 00003-state-kernel-v1

Diff range: `9cda04a6a0279a6306c24015ee2d3173fb916e68..9c99065aaf0abad9d6a3f026b572b92291091576`

codex_rung_guard: not fired

pack: failed after one retry (repository is not registered in gita); review continued with the mandated degraded sentinel.

## Review Summary

Reviewed: 12 completed tasks
PRDs checked: 00003-state-kernel-v1

### Agent Status

- Alice: ✅ Available
- Blake: ✅ Available
- Bob: ✅ Available via native fallback after the canonical Codex helper refused nested CLI dispatch
- Carl: ⚠️ Unavailable after the canonical Gemini helper refused nested CLI dispatch and its one retry

## Consolidated Findings

| Consensus | Severity | Issue | File | Task | Found By |
|-----------|----------|-------|------|------|----------|
| [2/3] | 🟡 | `_validate_owned()` recomputes immutable type hints for every nested entry, producing tens of thousands of reflection calls at documented task/attempt limits; cache hints once per TypedDict owner | src/ovcaq/state/schema.py:634 | 2 | ALICE, BOB |
| [1/3] | 🟠 | `validate_state()` measures compact JSON while `StateStore` publishes larger indent-2 JSON, so state can pass validation/read yet fail initialization or every later transaction at the same byte limit; use one canonical serialization size check | src/ovcaq/state/schema.py:799 | 2 | ALICE |
| [1/3] | 🟠 | The preflight `json.dumps()` converts nested non-JSON values into a generic `state` error, violating the required first full dotted-path diagnostic; let the structural walk report the offending value before measuring serialized size | src/ovcaq/state/schema.py:799 | 2 | ALICE |
| [1/3] | 🟠 | Resource-limit classification parses user-controlled exception text, so an invalid value such as `"exceeds 9"` is incorrectly reported as `resource_limit`/11 instead of `invalid_state`/1; use a dedicated exception type | src/ovcaq/cli.py:335 | 10 | ALICE |
| [1/3] | 🟠 | Object-only task payloads are not shape-checked; arrays/scalars can commit invalid no-op mutations or escape as uncaught TypeError/AttributeError tracebacks | src/ovcaq/cli.py | P01-T10 | BLAKE |
| [1/3] | 🟠 | [FIX] `transaction()` validates a mutator-supplied revision before replacing it, so invalid revision values are rejected despite P01-T05 requiring every supplied value to be ignored; assign the store-owned revision before full validation and test invalid replacements | src/ovcaq/state/store.py:134 | 5 | BOB |
| [1/3] | 🟠 | [FIX] Task add/attempt/complete/set-meta cast arbitrary JSON without requiring an object; scalar or list payloads raise uncaught `TypeError`/`AttributeError`, violating the stable no-traceback error contract | src/ovcaq/cli.py:278 | 10 | BOB |
| [1/3] | 🟠 | [FIX] The state protocol documents only top-level owners and a validation summary; it omits the required complete nested schema and transaction, locking, CAS, backup, restore, fsync, and error contracts | docs/state-protocol.md:7 | 1 | BOB |
| [1/3] | 🟡 | Default argparse abbreviation accepts undeclared options such as `--js`, while the pre-parse JSON detector recognizes only `--json`, causing some requested JSON usage errors to emit plain text; disable abbreviations | src/ovcaq/cli.py:50 | 10 | ALICE |
| [1/3] | 🟡 | `COMMAND_PATHS` and `COMMAND_INVENTORY` manually duplicate parser and documentation truth, allowing option-level drift despite the single-registry requirement; derive assertions from the live parser and documentation-extracted commands | tests/state/test_commands.py:1024 | 11 | ALICE |
| [1/3] | 🟡 | The unresolved style gate is real: six production functions exceed 50 lines, `schema.py` exceeds 800 lines, and multiple test functions/files also exceed both limits; split the listed dispatch/validation concerns and test modules without changing behavior | N/A | general | ALICE |
| [1/3] | 🟡 | `--json` is only accepted before `state`, contradicting the accepted `ovcaq state show [--json]` interface | src/ovcaq/cli.py | P01-T10 | BLAKE |
| [1/3] | 🟡 | State command documentation is manually duplicated and only compared with another static test constant, rather than generated from the live parser | docs/state-protocol.md | P01-T10 | BLAKE |
| [1/3] | 🟡 | Initialization publishes authoritative state before creating the project config, so a config-write failure reports init failure but leaves state behind and makes retry fail with `state_exists` | src/ovcaq/cli.py | P01-T10 | BLAKE |
| [1/3] | 🟡 | [FIX] The accepted service surface requires `StateService.restore()` and an installed `ovcaq.state.StateService` export, but neither exists and CLI restore bypasses the service | N/A | general | BOB |
| [1/3] | 🟡 | [FIX] STATE-016/017 are labeled `derived` while targeting materialized count fields and claiming each value is derived from itself; mark them renamed or identify `tasks` as the derivation source and explain materialization | docs/state-protocol.md:76 | 1 | BOB |
| [1/3] | 🟡 | [FIX] `touch(exist_ok=True)` changes timestamps of an existing `ovcaq.toml`, contradicting “creates only when absent”; use create-only creation and test existing-file metadata preservation | src/ovcaq/config.py:10 | 10 | BOB |
| [1/3] | 🟡 | [FIX] The style gate remains failed: six production functions exceed 50 lines (`build_parser`, `_dispatch_task_or_contract`, `new_state`, `_validate_annotation`, `_validate_constraints`, `_validate_capability_invariants`); split them along parser and validator responsibilities | N/A | general | BOB |
| [1/3] | 🟡 | [FIX] Four changed files exceed the 800-line limit (`schema.py` 816; `test_commands.py` 1623; `test_schema.py` 2256; `test_store.py` 1594); split schema types/validation and tests by behavior | N/A | general | BOB |
| [1/3] | ⚪ | [FIX] If `os.fchmod()` fails after opening the lock, `_locked()` raises before entering its close-protected block and leaks the descriptor | src/ovcaq/state/store.py:172 | 3 | BOB |
| [1/3] | ⚪ | [VERIFY] Cannot statically verify: the full pytest, Ruff check/format, mypy, and build gates; exact check is the five verification commands listed in AGENTS.md | N/A | general | BOB |

## Follow-up Tasks Created

1. Task 13 — [Review C1] Fix schema validation sizing, diagnostics, and reflection cost (L)
2. Task 14 — [Review C1] Harden CLI payloads, JSON placement, and error typing (L)
3. Task 15 — [Review C1] Make parser and protocol documentation one live registry (M)
4. Task 16 — [Review C1] Honor store-owned revisions and close lock descriptors (M)
5. Task 17 — [Review C1] Complete the state service and protocol contract (L)
6. Task 18 — [Review C1] Make project initialization retry-safe and metadata-safe (M)
7. Task 19 — [Review C1] Clear all production and test style-limit violations (L)
8. Task 20 — [Review C1] Re-run the complete project verification matrix (S)

## Alice

[ALICE] 🟠 `validate_state()` measures compact JSON while `StateStore` publishes larger indent-2 JSON, so state can pass validation/read yet fail initialization or every later transaction at the same byte limit; use one canonical serialization size check | File: src/ovcaq/state/schema.py:799 | Task: 2
[ALICE] 🟠 The preflight `json.dumps()` converts nested non-JSON values into a generic `state` error, violating the required first full dotted-path diagnostic; let the structural walk report the offending value before measuring serialized size | File: src/ovcaq/state/schema.py:799 | Task: 2
[ALICE] 🟠 Resource-limit classification parses user-controlled exception text, so an invalid value such as `"exceeds 9"` is incorrectly reported as `resource_limit`/11 instead of `invalid_state`/1; use a dedicated exception type | File: src/ovcaq/cli.py:335 | Task: 10
[ALICE] 🟡 Default argparse abbreviation accepts undeclared options such as `--js`, while the pre-parse JSON detector recognizes only `--json`, causing some requested JSON usage errors to emit plain text; disable abbreviations | File: src/ovcaq/cli.py:50 | Task: 10
[ALICE] 🟡 `COMMAND_PATHS` and `COMMAND_INVENTORY` manually duplicate parser and documentation truth, allowing option-level drift despite the single-registry requirement; derive assertions from the live parser and documentation-extracted commands | File: tests/state/test_commands.py:1024 | Task: 11
[ALICE] 🟡 `_validate_owned()` recomputes immutable type hints for every nested entry, producing tens of thousands of reflection calls at documented task/attempt limits; cache hints once per TypedDict owner | File: src/ovcaq/state/schema.py:634 | Task: 2
[ALICE] 🟡 The unresolved style gate is real: six production functions exceed 50 lines, `schema.py` exceeds 800 lines, and multiple test functions/files also exceed both limits; split the listed dispatch/validation concerns and test modules without changing behavior | File: N/A | Task: general
R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: fail

## Blake

[BLAKE] 🟠 Object-only task payloads are not shape-checked; arrays/scalars can commit invalid no-op mutations or escape as uncaught TypeError/AttributeError tracebacks | File: src/ovcaq/cli.py | Task: P01-T10
[BLAKE] 🟡 `--json` is only accepted before `state`, contradicting the accepted `ovcaq state show [--json]` interface | File: src/ovcaq/cli.py | Task: P01-T10
[BLAKE] 🟡 State command documentation is manually duplicated and only compared with another static test constant, rather than generated from the live parser | File: docs/state-protocol.md | Task: P01-T10
[BLAKE] 🟡 Initialization publishes authoritative state before creating the project config, so a config-write failure reports init failure but leaves state behind and makes retry fail with `state_exists` | File: src/ovcaq/cli.py | Task: P01-T10
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
B14: fail
B15: fail
B16: pass
B17: pass
B18: pass
B19: pass

## Bob

[BOB] 🟠 [FIX] `transaction()` validates a mutator-supplied revision before replacing it, so invalid revision values are rejected despite P01-T05 requiring every supplied value to be ignored; assign the store-owned revision before full validation and test invalid replacements | File: src/ovcaq/state/store.py:134 | Task: 5
[BOB] 🟠 [FIX] Task add/attempt/complete/set-meta cast arbitrary JSON without requiring an object; scalar or list payloads raise uncaught `TypeError`/`AttributeError`, violating the stable no-traceback error contract | File: src/ovcaq/cli.py:278 | Task: 10
[BOB] 🟡 [FIX] The accepted service surface requires `StateService.restore()` and an installed `ovcaq.state.StateService` export, but neither exists and CLI restore bypasses the service | File: N/A | Task: general
[BOB] 🟠 [FIX] The state protocol documents only top-level owners and a validation summary; it omits the required complete nested schema and transaction, locking, CAS, backup, restore, fsync, and error contracts | File: docs/state-protocol.md:7 | Task: 1
[BOB] 🟡 [FIX] STATE-016/017 are labeled `derived` while targeting materialized count fields and claiming each value is derived from itself; mark them renamed or identify `tasks` as the derivation source and explain materialization | File: docs/state-protocol.md:76 | Task: 1
[BOB] 🟡 [FIX] `touch(exist_ok=True)` changes timestamps of an existing `ovcaq.toml`, contradicting “creates only when absent”; use create-only creation and test existing-file metadata preservation | File: src/ovcaq/config.py:10 | Task: 10
[BOB] 🟡 [FIX] Every nested owner validation recomputes `get_type_hints`; a maximum task/attempt state causes tens of thousands of repeated reflection calls under the state lock, so cache hints per owner and cover the combined maximum shape | File: src/ovcaq/state/schema.py:634 | Task: 2
[BOB] 🟡 [FIX] The style gate remains failed: six production functions exceed 50 lines (`build_parser`, `_dispatch_task_or_contract`, `new_state`, `_validate_annotation`, `_validate_constraints`, `_validate_capability_invariants`); split them along parser and validator responsibilities | File: N/A | Task: general
[BOB] 🟡 [FIX] Four changed files exceed the 800-line limit (`schema.py` 816; `test_commands.py` 1623; `test_schema.py` 2256; `test_store.py` 1594); split schema types/validation and tests by behavior | File: N/A | Task: general
[BOB] ⚪ [FIX] If `os.fchmod()` fails after opening the lock, `_locked()` raises before entering its close-protected block and leaks the descriptor | File: src/ovcaq/state/store.py:172 | Task: 3
[BOB] ⚪ [VERIFY] Cannot statically verify: the full pytest, Ruff check/format, mypy, and build gates; exact check is the five verification commands listed in AGENTS.md | File: N/A | Task: general
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
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 21 findings
Tests: 716 passed, 0 failed, 0 skipped

