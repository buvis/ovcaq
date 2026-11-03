# Alice — consensus/architecture

## Verdict

pass

## Must fix

None.

## Can defer

- **Living-design detail lags the repaired protocol.** Evidence: `dev/local/designs/00003-state-kernel-v1-design.md:67-79` omits `MAX_JSON_INTEGER_DIGITS`, and its store description at lines 361-399 does not mention regular-file preflight/nonblocking reads. The authoritative operator protocol records both at `docs/state-protocol.md:251-270`, with matching implementation and tests. Rationale: documentation-layer maintenance only; no runtime, PRD acceptance, or source-ID failure.

## Architecture and contract audit

- **Integer serialization closure and revision rollover — converges.** `src/ovcaq/state/schema.py:37-45,423-451,489-494,523-535` applies the same 640-digit domain to decoded, typed, and open-map integers. `src/ovcaq/state/store.py:138-149,152-173` assigns the store-owned next revision and validates it before publication, so maximum revision fails without changing state or backup. This satisfies P01-T01/P01-T02/P01-T05, the validate-before-publish ordering in `implementation-plan.md:573-593`, and the byte-preservation exit criterion at lines 1145-1150.

- **Prompt non-regular artifact rejection — converges.** `src/ovcaq/state/store.py:231-264` uses a nonblocking, non-following read open. Lines 456-483 reject non-regular or multi-linked artifacts before open and reverify type/inode/link count against the descriptor, covering both the normal case and a type-changing race. Backup reads use the same path and are wrapped as `BackupError` at lines 266-272. This remains inside the sole store boundary and satisfies P01-T03/P01-T06 plus the fail-closed state policy at `implementation-plan.md:975-980`.

- **Strict non-standard constants and classifications — converges.** `src/ovcaq/state/schema.py:433-451` rejects `NaN`, `Infinity`, and `-Infinity` during decoding. Inline/file decoding maps the resulting `ValueError` to `usage` at `src/ovcaq/cli.py:174-188`; durable state becomes `StateIOError` at `src/ovcaq/state/store.py:274-295`; restore wraps the same failure as `BackupError` at lines 152-164. Central normalization at `src/ovcaq/cli.py:364-389` yields the documented `usage`, `state_io`, and `invalid_backup` symbols. This satisfies P01-T01/P01-T02/P01-T03/P01-T06/P01-T10 and the PRD’s total-validation, validated-restore, and stable machine-error obligations.

No repair introduced a second writer, provider leakage, workflow policy, or alternate error boundary.

## Tests inspected or run

- Independently ran all three focused files: **151 passed in 2.49s**:
  - `tests/state/test_schema_limits.py`
  - `tests/state/test_store.py`
  - `tests/state/test_cli_limits.py`
- Also ran the narrower repair selection: **29 passed, 122 deselected**.
- Inspected boundary and regression coverage at:
  - `tests/state/test_schema_limits.py:45-116`
  - `tests/state/test_store.py:662-748,766-921`
  - `tests/state/test_cli_limits.py:52-177`
- Reviewed the supplied clean-HEAD evidence for the full 883-test suite, Ruff, formatting, mypy, build, `git diff --check`, accepted-plan hash, and 33-case coordinator repair matrix.

## Residual doubts

- **Verified issues:** none.
- **Speculation:** there is no single deterministic test that swaps a regular artifact to a FIFO precisely between metadata inspection and `open`; current coverage separately verifies pre-open rejection, `O_NONBLOCK`, and descriptor/path revalidation. The implementation composition closes that race, so this is not a required evidence gap.
