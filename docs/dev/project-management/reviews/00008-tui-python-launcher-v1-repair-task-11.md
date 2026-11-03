# PRD 00008 recovery task 11

Rejected initialization now proves the original collision object's exact mode, device/inode identity, and symlink target remain unchanged, while preserving the no-state-publication assertion. JsonlFollower catches Exception directly rather than catching BaseException and re-raising every non-Exception; ordinary fault tolerance and process-control propagation are unchanged.

Base8843f8a1fa973868a2a3bad5e2b00b996b982349; commita30ae6b42b6b89653ef047354e58682467ef4a37. Mechanically eligible micro lane: twoMEDIUM findings/two clean files. Orchestrator apply_patch only,4net lines/twofiles. No Tess/Devon/testcommit/red-check per source micro lane. Behavior-preserving refactor commit plus test strengthening, no feature/fix release entry warranted. Main narrow test command covered all reader tests plus both collision parametrizations:19passed2pre-existing pytest cleanup warnings,exit0,0.26s. Style and split gates clean; reflow no threshold; self-deslop skipped:trivial by micro rule. ASSUMPTIONS:none.

Tool-free Patf25fa6eb12,464bytes, approved network guarded Claude runner, session42183b67-0312-4f5c-8996-ed5bad37c942, actualclaude-sonnet-5-5. F15/F25 resolved; optional comment rewrite and removing a test-local None sentinel are LOW, retained unchanged. The current target equality explicitly proves original symlink destination, stronger than the offered islink-only alternative. Parsed raw verdict retained below. No completion review invoked.

## Raw Pat review

CLOSURE | resolved | F15 `test_init_rejects_project_config_path_collisions_before_state_publication` hedges with `or`, so either asserted setup shape satisfies the final check | The `or` is replaced by `after.st_mode == original.st_mode` and `os.path.samestat(after, original)`, plus a `readlink()` equality check for symlinks. A dir cannot become a symlink or the reverse, and the no-state-publication assertion is kept.

CLOSURE | resolved | F25 `except BaseException` followed by `if not isinstance(error, Exception): raise` behaves exactly like `except Exception:` | The diff changes it to `except Exception as error:` and drops the isinstance/re-raise lines. `BaseException` subclasses such as `KeyboardInterrupt` still propagate, and the focused tests pass (19 passed).

LOW | src/ovcaq/events/tail.py:319 | The comment "JSON RecursionError and any decoder fault become gaps; signals do not." still fits, so there is no defect. It could say "ordinary exceptions become gaps" now that the shape is plain. | Optional rewording only.

LOW | tests/state/test_cli.py:354 | `target` is computed with an `if` expression before the call. The `if target is not None` check after it is a second branch on the same condition. | Compare `os.readlink` only when `stat.S_ISLNK(original.st_mode)`, or always compare `os.path.islink(config)` with the original. This drops the `None` sentinel.


## Final narrow verification

...................                                                      [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-57c4cc2b-9170-4df6-8ba1-17d4903cb7d8
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-57c4cc2b-9170-4df6-8ba1-17d4903cb7d8'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-491c65c7-d28e-47c4-928c-b019c1d53d95
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-491c65c7-d28e-47c4-928c-b019c1d53d95'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
19 passed, 2 warnings in 0.26s

{
  "command": [
    "uv",
    "run",
    "pytest",
    "-q",
    "--tb=line",
    "tests/events/test_tail_reader.py",
    "tests/state/test_cli.py::test_init_rejects_project_config_path_collisions_before_state_publication"
  ],
  "exit": 0,
  "timeout_seconds": 300
}