# Bob — doubt and de-slop
Verdict: changes_requested
## Must fix
- Deep under-limit JSON crashes instead of producing a stable symbolic error; high severity; `src/ovcaq/state/store.py:237-252`, `src/ovcaq/cli.py:169-181`, `src/ovcaq/cli.py:423-430`. Both decoders omit `RecursionError`; a 200,001-byte, 100,000-level array makes `StateStore.read()` and `main(... state set ...)` raise raw `RecursionError`, with no JSON diagnostic. Violates PRD lines 23-25, 56-57, 69-71, and 82-85.
- `ovcaq init` follows a pre-existing runtime-directory symlink, chmods its external target, and publishes state outside the project; high severity; `src/ovcaq/cli.py:215-219`, `src/ovcaq/paths.py:28-33`. Reproduced with `dev/local/ovcaq -> /tmp/victim`: init returned success, changed victim mode from `0755` to `0700`, and created external `state.json`. Violates PRD lines 84-87 and is a filesystem-escape/security risk.
- The lock sidecar follows symlinks and chmods the target; medium severity; `src/ovcaq/state/store.py:175-185`. Reproduced by replacing `state.json.lock` with a symlink to a `0644` victim file: a read succeeded and changed the victim to `0600`. Violates the safe locked-store boundary in PRD lines 61-65 and constitutes an arbitrary same-user filesystem mutation.
- Duplicate JSON object keys are silently collapsed before validation; medium severity; `src/ovcaq/state/store.py:237-252`, `src/ovcaq/cli.py:169-181`. A state file containing two `revision` fields was accepted, reporting the last value. Closed validation therefore cannot detect ambiguous/corrupt raw state. Violates PRD lines 30-31 and 54-57.
## Can defer
- Restore cannot recover a corrupt current state because it validates current bytes before reading the backup; evidence: `src/ovcaq/state/store.py:150-160`, pinned by `tests/state/test_store_concurrency.py:198-229` and documented at `docs/state-protocol.md:242-244`; rationale: this is an explicit current contract rather than a stated acceptance miss, though it limits disaster recovery.
- Valid empty keys in nested open JSON maps cannot be addressed through the string path grammar; evidence: metadata validation permits empty strings at `src/ovcaq/state/schema.py:456-467`, while `src/ovcaq/state/paths.py:33-34` and `tests/state/test_paths.py:149-180` reject `[""]`; rationale: no packet requirement promises empty-key addressability.
- Test-only bloat can be pruned separately; evidence: `tests/state/test_store.py:419-527` spends substantial machinery proving `subprocess.Popen`/pytest isolation already exercised by installed-wheel subprocess tests, while `tests/state/test_paths.py:22-146` repeats the same 18-case composition matrix across four operations; rationale: readability/cost issue, not a product acceptance failure.
- Port-inventory tests are partially self-confirming; evidence: `tests/test_packaging.py:128-179` compares a local constant to another literal and then checks destination-file existence; rationale: functional tests provide substantial independent coverage, but these manifest checks alone do not prove behavioral port completeness.
## Doubt audit
- FIX — Under-limit deeply nested stored and inline JSON can escape as raw `RecursionError`; reproduced as described above.
- FIX — Assumption that the runtime path remains beneath the project is false; reproduced external chmod/publication through a directory symlink.
- FIX — Assumption that the lock sidecar is a regular local file is false; reproduced external-target chmod through a symlink.
- FIX — Assumption that parsing preserves enough evidence for total validation is false for duplicate keys; reproduced acceptance of two `revision` fields.
- VERIFIED-DISMISSED — Concurrent writers, CAS, and crash boundaries might lose updates. Real-process tests at `tests/state/test_store_transactions.py:524-630` and `tests/state/test_durability.py:345-409` cover two writers and SIGKILL at every declared durability boundary; supplied full pytest passed.
- VERIFIED-DISMISSED — Publication exceptions might leave state/backup changed. Exact-byte repair tests at `tests/state/test_store_transactions.py:654-742` cover transaction and restore boundaries with and without an old backup.
- VERIFIED-DISMISSED — Installed execution or command coverage might depend on the checkout. `tests/state/test_installed_state.py:553-569` builds/installs a wheel and executes every state command from a hostile arbitrary cwd.
- VERIFIED-DISMISSED — Reflective validation might omit a current schema annotation. `tests/state/test_schema_invariants.py:141-504`, `tests/state/test_schema_constraints.py:249-670`, and `tests/state/test_crosswalk.py:253-296` independently pin owners, literals, runtime rejection, documentation, and error mappings.
- VERIFIED-DISMISSED — An explicit per-owner validator would necessarily be safer than the reflective validator. Current annotation forms are bounded and exhaustively pinned; no current unsupported annotation was found.
- VERIFIED-DISMISSED — Provider-specific behavior leaked into neutral production modules. The touched production state/CLI modules contain none of the forbidden provider strings; provider names occur only in the required legacy crosswalk and tests.
- KNOWN — Corrupt-current restore limitation; explicit documented behavior, not a stated acceptance miss.
- KNOWN — Empty-key path limitation; legitimate edge case but unspecified grammar.
- KNOWN — Test bloat and self-confirming manifest checks; structural slop without a product defect.
## R1–R5 de-slop rubric
R1: fail — 11,368 additions against 978 PRD words is 11.6×. Much of the ratio is justified by the mandatory 184-row crosswalk, durability matrix, and installed-wheel suite, but `tests/state/test_store.py:419-527` and the repeated matrix in `tests/state/test_paths.py:22-146` are concrete reducible bloat candidates.
R2: pass — investigated revision type guards, create-only double checks, cleanup/repair branches, and schema serialization fallbacks. Each handles a reachable race, malformed external object, or failure boundary; no confirmed impossible production guard was found.
R3: pass — inspected single-caller candidates `_dispatch_attempt_command` (`src/ovcaq/cli.py:277-292`), `_validate_latest_capability` (`src/ovcaq/state/schema.py:740-753`), and `ensure_project_config` (`src/ovcaq/config.py:8-15`). They isolate parser/application boundaries, validator complexity, or separately testable config behavior.
R4: pass — production comments/docstrings are short contract or rationale statements, notably the public path error-policy comment at `src/ovcaq/state/paths.py:1`; no adjacent-code paraphrasing or verbose trivial docstrings found.
R5: fail — `tests/test_packaging.py:128-179` includes self-mirroring/existence-only port-manifest checks, and the passing suite lacks regression cases for the reproduced recursion, runtime-symlink, lock-symlink, and duplicate-key failures. Mock-based routing and durability tests inspected also assert resulting durable behavior, so they are not merely mock-confirming.
## Tests inspected or run
- Relied on supplied head evidence: `mise exec -- uv sync --all-groups` passed; `mise exec -- uv run pytest` passed with 762 tests; `ruff check`, `ruff format --check`, `mypy src/ovcaq`, `uv build`, and range `git diff --check` all passed.
- Inspected `test_sigkill_at_each_locked_mutation_boundary_preserves_recoverable_state`; all six declared boundaries are parametrized.
- Inspected two-process CAS/counter tests, exact-byte transaction/restore repair tests, installed-wheel every-command test, schema owner/crosswalk tests, CLI resource-limit tests, and packaging-port tests.
- Focused probe: `StateStore.read()` on `b"[" * 100000 + b"0" + b"]" * 100000` raised raw `RecursionError`.
- Focused probe: `main(... state set ..., "[" * 100000 + "0" + "]" * 100000)` raised raw `RecursionError` with no structured stderr.
- Focused probe: init through a runtime symlink returned `0`, chmodded the external target to `0700`, and created external state.
- Focused probe: read through a lock-file symlink changed an external victim from `0644` to `0600`.
- Focused probe: raw state with duplicate `revision` keys was accepted and returned the last value.
## Residual doubts
- Exact completeness of the legacy state/statectl characterization port cannot be independently established from this packet because the legacy source tests and PRD 00002 inventory are excluded; the local manifest checks are not an independent oracle.
