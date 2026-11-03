## Verdict

changes_requested

## Must fix

1. **High — invalid state artifacts can hang reads indefinitely.** In `src/ovcaq/state/store.py:230`, `_read_bytes()` performs blocking `os.open(..., O_RDONLY)` before `_verify_open_artifact()`. `_reject_aliased_artifact()` at line 454 rejects symlinks and multi-linked regular files, but not FIFOs or other non-regular files. Reproduced at exact HEAD: replacing `state.json` with `os.mkfifo()` caused `StateStore.read()` to exceed a 0.5-second subprocess timeout rather than fail. A FIFO backup similarly affects restore. This violates the PRD’s deterministic behavior under invalid input and explicit fail-closed read requirement, and permits workspace-local denial of service.

2. **Medium — non-standard JSON constants receive the wrong stable symbolic error.** `decode_json()` in `src/ovcaq/state/schema.py:431` calls `json.loads()` without `parse_constant`, so Python accepts `NaN`, `Infinity`, and `-Infinity`. Reproduced with:
   `ovcaq --json state set 'work.extensions["tests/nonfinite"]' NaN`
   The command returned `invalid_state`; state remained unchanged. `NaN` is invalid JSON syntax, so the documented CLI contract requires `usage` for inline/file payloads. The same decoder path classifies such durable bytes as `invalid_state` instead of documented `state_io`. This violates the PRD’s stable symbolic JSON error contract.

## Can defer

None.

## Tests inspected or run

- Inspected the complete 28-file range diff and all added schema, crosswalk, path, service, CLI, packaging, transaction, concurrency, and durability tests.
- Reviewed the coordinator’s clean-HEAD evidence for all 850 tests and build/lint/type/package gates.
- Ran an isolated CLI non-finite JSON probe; reproduced `invalid_state`.
- Ran an isolated FIFO artifact probe; `StateStore.read()` timed out after 0.5 seconds.
- Did not rerun the full suite; the initial `uv` invocation was blocked by sandbox access to its user cache, so full-suite status relies on the supplied coordinator evidence.

## Residual doubts

Strict blind isolation prevented independently comparing the crosswalk against its external source inventory; completeness is supported by the inspected crosswalk test and supplied passing evidence. No other material doubts.
