# Bob — doubt plus de-slop

## Verdict

pass

## Must fix

None.

## Can defer

- Add a deterministic lstat-to-open substitution test replacing a regular state/backup with a FIFO. Current tests verify static rejection and `O_NONBLOCK`, but not the complete race.
- Add direct store tests for programmatic non-finite floats. Text-based inline, file, durable-state, and backup boundaries are already covered.

## Doubt audit

8 doubts: 0 FIX, 6 VERIFY resolved, 2 KNOWN.

1. **Least confidence — type-changing race (KNOWN):** Static FIFO/socket/directory rejection is covered, and regular reads assert `O_NONBLOCK`. A deterministic substitution-race test is absent. Code still survives: pre-open `lstat`, `O_NOFOLLOW | O_NONBLOCK`, then descriptor/path identity and regular-file verification before reading.

2. **Integer serialization closure (VERIFY, dismissed):** `_require_integer()` rejects `abs(value) >= 10**640` across typed integers and open JSON. Tests cover positive/negative 640-digit values, typed fields, blocker IDs, extensions, initialization, transactions, and round-trip encoding.

3. **Maximum revision rollover (VERIFY, dismissed):** Both `transaction()` and `restore()` calculate the next revision before publication and validate it. At the maximum readable revision, validation raises `ResourceLimitError`; tests assert the entire runtime directory remains byte-identical.

4. **Non-regular artifact handling (VERIFY, dismissed):** FIFO, Unix socket, and directory state/backup artifacts are rejected before open. Backup restore converts the failure to `BackupError`; state access remains `StateIOError`. Symlink, hard-link, and post-open identity checks complete the fail-closed path.

5. **NaN/Infinity classification (VERIFY, dismissed):** `parse_constant` rejects all three constants during decoding. CLI tests cover inline/file → `usage`, durable state → `state_io`, and backup → `invalid_backup`, with mutation-preservation assertions.

6. **Programmatic non-finite floats (KNOWN):** `_validate_json()` rejects them using `math.isfinite`, so publication is closed. Dedicated store-boundary regression tests were not present in the inspected additions.

7. **Alternative design (VERIFY, dismissed):** `allow_nan=False` during encoding could add redundancy, but it is unnecessary for correctness: decoded constants are rejected immediately, programmatic values undergo full validation before `_canonical_bytes()`, and committed state is a validated deep copy.

8. **Repair-size/slop concern (VERIFY, dismissed):** The 429-line repair is approximately 17 production lines, documentation corrections, and a four-boundary regression matrix. The volume is test-heavy but proportionate to distinct error classifications and preservation requirements.

Original-task completeness was checked against all three bounded repairs; no acceptance or invariant miss was found. Practical error paths checked included revision exhaustion, restore validation, static and racing artifact types, and every requested non-standard-number boundary.

## R1–R5 rubric

- **R1 PASS:** No reducible production bloat. Test volume reflects three constants across four separately classified boundaries plus artifact types.
- **R2 PASS:** The pre-open and post-open guards are not impossible defenses; they address distinct TOCTOU states.
- **R3 PASS:** `_reject_nonstandard_json_constant` is a single callback site, but the named function is required by `json.loads(parse_constant=...)`. The integer-limit constant avoids repeatedly constructing a 640-digit bound.
- **R4 PASS:** No new comment or docstring merely paraphrases adjacent code. Protocol changes define observable contracts.
- **R5 PASS:** Tests exercise OVCAQ classification, mutation preservation, and open flags. They do not merely verify pytest, `json`, or mocks.

## Tests inspected or run

Inspected the focused schema, store, CLI, protocol, and regression additions at `7b2e977`.

No tests rerun. Coordinator evidence at the exact clean HEAD reports:

- 883 tests passed.
- Focused repair selection: 33 passed, 118 deselected.
- Ruff check/format, mypy, build, and complete-range diff-check passed.
- Accepted-plan digest matched.

## Residual doubts

Only the two explicitly KNOWN test additions above remain. No unclassified doubts.
