# Task 4 adversarial validation

Baseline SHA-256: 57c2b3b4dc90df7f3c54c4a48419702ad7aa479bcfdf2b82910953896f2928a4

Attempt 1: check ancestry identity only for a directory named `ancestor`.

```python
def _ensure_directory_chain(path: Path) -> None:
    import errno
    import os
    import sys

    destination = path.absolute()
    flags = os.O_DIRECTORY | getattr(
        os, "O_SEARCH", 0x40000000 if sys.platform == "darwin" else os.O_RDONLY
    )
    parent = Path(destination.anchor)
    descriptor = os.open(parent, flags)
    try:
        for part in destination.parts[1:]:
            child = parent / part
            try:
                expected = os.stat(child)
            except FileNotFoundError:
                os.mkdir(child)
                expected = os.stat(child)
            os.fsync(descriptor)
            child_descriptor = os.open(child, flags)
            actual = os.fstat(child_descriptor)
            # Deliberately wrong: replacement is rejected only for this test name.
            if child.name == "ancestor" and (
                expected.st_dev, expected.st_ino
            ) != (actual.st_dev, actual.st_ino):
                os.close(child_descriptor)
                raise OSError(errno.EAGAIN, f"identity changed; retry: {child}")
            os.close(descriptor)
            descriptor = child_descriptor
            parent = child
    finally:
        os.close(descriptor)
```

Attempt 1 first execution: fixture setup error, 5 errors in 0.08s. uv selected an interpreter without hatchling. Tests did not run.

Attempt 1 rerun with UV_PYTHON selecting the supplied venv interpreter:

```text
exit=0; elapsed=0.95s
.....                                                                    [100%]
5 passed in 0.85s

```

Verdict: tests were broken by one obviously incorrect mutant. No second or third mutant was needed.

Weak test: `test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt` covers both direct and exact replay, but the replaced directory is always named `ancestor`. The mutant checks `(st_dev, st_ino)` only for that literal name and silently accepts replacements for every other directory component. It does not inspect test mode or monkeypatch tests.

Prevention: parameterize the replaced component using independently generated names and at several depths (including the runtime directory). For each, require OSError, `identity changed; retry`, the actual replaced path in the error, no returned path, no new ledger in either displaced or replacement ancestry, preserved state and preexisting ledger bytes, and successful recording only on a fresh invocation. At minimum, running the existing direct/exact-replay assertions against a second arbitrary component name kills this mutant.

Scope: only `_ensure_directory_chain` in the existing permitted product file was replaced. No test source, canonical repository, state, or other product source was edited. No agents were spawned. Source implementation was used only as bytes/AST function boundary to replace the authorized function; no implementation body was emitted as context. Support read: packaging_support.py and tests/packaging/conftest.py; tests/conftest.py was absent.

Created explicit paths: `devon-files.baseline` (will be overwritten with one placeholder line after byte-exact verification), `devon-result.md` (retained as required evidence). Test/fixture artifacts were created under `pytest-of-bob/` inside this disposable tree; pytest may also refresh its cache and Python bytecode there. No new product source files were created.

Both pytest subprocess calls used a 300-second timeout. The first did not execute tests because build setup lacked hatchling. The second used TMPDIR equal to this disposable tree and UV_PYTHON equal to the supplied canonical venv interpreter, leaving the mandated pytest command unchanged.

Restoration verified independently: byte-for-byte equal to backup, 15,432 bytes; SHA-256 `57c2b3b4dc90df7f3c54c4a48419702ad7aa479bcfdf2b82910953896f2928a4`. Backup then overwritten with one placeholder line.

abort_reason: none
