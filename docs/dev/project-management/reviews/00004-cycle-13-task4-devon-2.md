# Task 4 adversarial validation: round 2

Baseline SHA-256: 57c2b3b4dc90df7f3c54c4a48419702ad7aa479bcfdf2b82910953896f2928a4

Attempt 1 repeats the first-round hardcoded-name mutant.

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

Attempt 1 actual test evidence:

```text
exit=1; elapsed=1.05s
FFFF...                                                                  [100%]
=================================== FAILURES ===================================
_ test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt[parent-direct] _

installed_wheel = InstalledWheel(root=PosixPath('/private/tmp/ovcaq-devon-4-20260913/pytest-of-bob/pytest-2/ovcaq-installed-wheel0/venv'...DG_STATE_HOME': '/private/tmp/ovcaq-devon-4-20260913/pytest-of-bob/pytest-2/ovcaq-installed-wheel0/sandbox/xdg-state'})
tmp_path = PosixPath('/private/tmp/ovcaq-devon-4-20260913/pytest-of-bob/pytest-2/test_installed_defer_refuses_r0')
replay = False, position = 'parent'

    @pytest.mark.parametrize("replay", (False, True), ids=("direct", "exact-replay"))
    @pytest.mark.parametrize("position", ("parent", "nested-parent"))
    def test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt(
        installed_wheel: InstalledWheel, tmp_path: Path, replay: bool, position: str
    ) -> None:
        project = _prepare(installed_wheel, tmp_path)
        authoritative = _state_bytes(project)
        container = project if position == "parent" else project / "branch"
        ancestor = container / uuid4().hex
        ancestor.mkdir(parents=True)
        runtime = ancestor / "runtime"
        displaced_runtime = project / "displaced" / runtime.relative_to(ancestor)
        previous = _identity(ancestor)
        seeded = None
        if replay:
            assert (
                _invoke(
                    installed_wheel, project, "normal", runtime=runtime, ancestor=ancestor
                )["exit"]
                == 0
            )
            seeded = _assert_one_record(runtime)
            assert _state_bytes(project) == authoritative
    
        interrupted = _invoke(
            installed_wheel, project, "replace", runtime=runtime, ancestor=ancestor
        )
        _assert_replaced_after_confirmation(interrupted, project, ancestor, previous)
>       assert interrupted["exit"] == 2, interrupted
E       AssertionError: {'exit': 0, 'path': '/private/tmp/ovcaq-devon-4-20260913/pytest-of-bob/pytest-2/test_installed_defer_refuses_r0/projec...p', 'identity': [16777230, 107436446]}, {'kind': 'fsync', 'path': '/private', 'identity': [16777230, 107435247]}, ...]}
E       assert 0 == 2

tests/packaging/test_rework_13.py:169: AssertionError
_ test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt[parent-exact-replay] _

installed_wheel = InstalledWheel(root=PosixPath('/private/tmp/ovcaq-devon-4-20260913/pytest-of-bob/pytest-2/ovcaq-installed-wheel0/venv'...DG_STATE_HOME': '/private/tmp/ovcaq-devon-4-20260913/pytest-of-bob/pytest-2/ovcaq-installed-wheel0/sandbox/xdg-state'})
tmp_path = PosixPath('/private/tmp/ovcaq-devon-4-20260913/pytest-of-bob/pytest-2/test_installed_defer_refuses_r1')
replay = True, position = 'parent'

    @pytest.mark.parametrize("replay", (False, True), ids=("direct", "exact-replay"))
    @pytest.mark.parametrize("position", ("parent", "nested-parent"))
    def test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt(
        installed_wheel: InstalledWheel, tmp_path: Path, replay: bool, position: str
    ) -> None:
        project = _prepare(installed_wheel, tmp_path)
        authoritative = _state_bytes(project)
        container = project if position == "parent" else project / "branch"
        ancestor = container / uuid4().hex
        ancestor.mkdir(parents=True)
        runtime = ancestor / "runtime"
        displaced_runtime = project / "displaced" / runtime.relative_to(ancestor)
        previous = _identity(ancestor)
        seeded = None
        if replay:
            assert (
                _invoke(
                    installed_wheel, project, "normal", runtime=runtime, ancestor=ancestor
                )["exit"]
                == 0
            )
            seeded = _assert_one_record(runtime)
            assert _state_bytes(project) == authoritative
    
        interrupted = _invoke(
            installed_wheel, project, "replace", runtime=runtime, ancestor=ancestor
        )
        _assert_replaced_after_confirmation(interrupted, project, ancestor, previous)
>       assert interrupted["exit"] == 2, interrupted
E       AssertionError: {'exit': 0, 'path': '/private/tmp/ovcaq-devon-4-20260913/pytest-of-bob/pytest-2/test_installed_defer_refuses_r1/projec...p', 'identity': [16777230, 107436446]}, {'kind': 'fsync', 'path': '/private', 'identity': [16777230, 107435247]}, ...]}
E    
[repeated failure details omitted]
te'})
tmp_path = PosixPath('/private/tmp/ovcaq-devon-4-20260913/pytest-of-bob/pytest-2/test_installed_defer_refuses_r3')
replay = True, position = 'nested-parent'

    @pytest.mark.parametrize("replay", (False, True), ids=("direct", "exact-replay"))
    @pytest.mark.parametrize("position", ("parent", "nested-parent"))
    def test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt(
        installed_wheel: InstalledWheel, tmp_path: Path, replay: bool, position: str
    ) -> None:
        project = _prepare(installed_wheel, tmp_path)
        authoritative = _state_bytes(project)
        container = project if position == "parent" else project / "branch"
        ancestor = container / uuid4().hex
        ancestor.mkdir(parents=True)
        runtime = ancestor / "runtime"
        displaced_runtime = project / "displaced" / runtime.relative_to(ancestor)
        previous = _identity(ancestor)
        seeded = None
        if replay:
            assert (
                _invoke(
                    installed_wheel, project, "normal", runtime=runtime, ancestor=ancestor
                )["exit"]
                == 0
            )
            seeded = _assert_one_record(runtime)
            assert _state_bytes(project) == authoritative
    
        interrupted = _invoke(
            installed_wheel, project, "replace", runtime=runtime, ancestor=ancestor
        )
        _assert_replaced_after_confirmation(interrupted, project, ancestor, previous)
>       assert interrupted["exit"] == 2, interrupted
E       AssertionError: {'exit': 0, 'path': '/private/tmp/ovcaq-devon-4-20260913/pytest-of-bob/pytest-2/test_installed_defer_refuses_r3/projec...p', 'identity': [16777230, 107436446]}, {'kind': 'fsync', 'path': '/private', 'identity': [16777230, 107435247]}, ...]}
E       assert 0 == 2

tests/packaging/test_rework_13.py:169: AssertionError
=========================== short test summary info ============================
FAILED tests/packaging/test_rework_13.py::test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt[parent-direct]
FAILED tests/packaging/test_rework_13.py::test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt[parent-exact-replay]
FAILED tests/packaging/test_rework_13.py::test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt[nested-parent-direct]
FAILED tests/packaging/test_rework_13.py::test_installed_defer_refuses_replaced_ancestry_until_fresh_attempt[nested-parent-exact-replay]
4 failed, 3 passed in 0.94s

```

Attempt 1 was caught by all four replacement variants at `interrupted["exit"] == 2` (mutant returned 0).

Attempt 2 validates only the final two ancestors, trusting the rest of the chain. This is wrong for replacement farther above the destination. The revised positions change absolute depth but both still replace the same relative parent of runtime.

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
            # Deliberately wrong: trust all but the final two ancestors.
            if child in destination.parents[:2] and (
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

Attempt 2 actual test evidence:

```text
exit=0; elapsed=1.31s
.......                                                                  [100%]
7 passed in 1.20s

```
