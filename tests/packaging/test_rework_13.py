from __future__ import annotations

import errno
import json
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from packaging_support import (
    InstalledWheel,
    assert_installed,
    identity,
    initialize_installed_state,
)
from rework_11_scripts import INITIALIZE_STATE
from rework_12_scripts import ORIGIN_CHECK
from rework_13_scripts import ANCESTRY_BOUNDARY_ACTOR

PRD = "00004-a.md"


def _prepare(installed: InstalledWheel, tmp_path: Path) -> Path:
    script = (
        INITIALIZE_STATE
        + ORIGIN_CHECK
        + "\nfrom ovcaq.workflow.records import record_defer\n"
        + "print(json.dumps(installed_origins()))\n"
    )
    project, state = initialize_installed_state(
        installed, tmp_path.resolve(), script, PRD, "ovcaq.workflow.records"
    )
    state.with_suffix(".json.bak").write_bytes(state.read_bytes())
    (project / "ancestor").mkdir()
    return project


def _state_bytes(project: Path) -> tuple[bytes, bytes]:
    state = project / "independent/state.json"
    return state.read_bytes(), state.with_suffix(".json.bak").read_bytes()


def _invoke(
    installed: InstalledWheel,
    project: Path,
    mode: str,
    *,
    runtime: Path | None = None,
    ancestor: Path | None = None,
) -> dict[str, Any]:
    if runtime is None:
        runtime = project / "ancestor/runtime"
    if ancestor is None:
        ancestor = runtime.parent
    process = subprocess.run(
        [
            installed.python,
            "-I",
            "-c",
            ANCESTRY_BOUNDARY_ACTOR,
            str(project),
            mode,
            str(runtime),
            str(ancestor),
        ],
        cwd=project,
        env=installed.environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    value: dict[str, Any] = json.loads(process.stdout)
    assert process.returncode == value["exit"], (process.stdout, process.stderr)
    assert_installed(value["origins"], installed, "ovcaq.workflow.records")
    return value


def _ledger(runtime: Path) -> Path:
    return runtime / "deferred/batch-deferred.json"


def _assert_one_record(runtime: Path) -> bytes:
    content = _ledger(runtime).read_bytes()
    assert json.loads(content) == {
        "batch_id": "batch",
        "items": [{"op_id": "replacement-probe", "prd": PRD}],
    }
    return content


def _assert_replaced_after_confirmation(
    interrupted: dict[str, Any], project: Path, ancestor: Path, previous: list[int]
) -> None:
    events = interrupted["events"]
    replacements = [event for event in events if event["kind"] == "replaced"]
    assert len(replacements) == 1, interrupted
    replacement = replacements[0]
    assert replacement["previous"] == previous
    assert replacement["displaced"] == previous == identity(project / "displaced")
    assert replacement["replacement"] == identity(ancestor)
    assert replacement["replacement"] != previous
    assert replacement["boundary"] == "before-reopen"
    index = events.index(replacement)
    assert {
        "kind": "fsync",
        "path": str(ancestor.parent),
        "identity": identity(ancestor.parent),
    } in events[:index]
    assert {
        "kind": "observed",
        "path": str(ancestor),
        "identity": previous,
    } in events[:index]
    assert events[index + 1] == {
        "kind": "observed",
        "path": str(ancestor),
        "identity": replacement["replacement"],
    }
    assert not any(
        event["kind"] == "fsync" and event["path"] == str(ancestor)
        for event in events[:index]
    ), interrupted


def _assert_runtime_replaced_at_deferred_mkdir(
    interrupted: dict[str, Any], project: Path, runtime: Path, previous: list[int]
) -> None:
    events = interrupted["events"]
    replacements = [event for event in events if event["kind"] == "replaced"]
    assert len(replacements) == 1, interrupted
    replacement = replacements[0]
    assert replacement == {
        "kind": "replaced",
        "path": str(runtime),
        "previous": previous,
        "displaced": previous,
        "replacement": identity(runtime),
        "boundary": "deferred-mkdir",
    }
    assert identity(project / "displaced") == previous
    index = events.index(replacement)
    assert {
        "kind": "fsync",
        "path": str(runtime.parent),
        "identity": identity(runtime.parent),
    } in events[:index]
    assert {
        "kind": "observed",
        "path": str(runtime),
        "identity": previous,
    } in events[:index]
    assert events[index + 1]["kind"] == "mkdir"
    assert events[index + 1]["path"] == str(runtime / "deferred")


def _assert_runtime_replaced_during_publication(
    interrupted: dict[str, Any],
    project: Path,
    runtime: Path,
    previous: list[int],
    replay: bool,
) -> None:
    events = interrupted["events"]
    replacements = [event for event in events if event["kind"] == "replaced"]
    assert len(replacements) == 1, interrupted
    replacement = replacements[0]
    assert replacement == {
        "kind": "replaced",
        "path": str(runtime),
        "previous": previous,
        "displaced": previous,
        "replacement": identity(runtime),
        "boundary": "ledger-open",
    }
    assert identity(project / "displaced") == previous
    index = events.index(replacement)
    assert {
        "kind": "fsync",
        "path": str(runtime),
        "identity": previous,
    } in events[:index]
    assert any(
        event["kind"] == "observed" and event["path"] == str(runtime / "deferred")
        for event in events[:index]
    ), interrupted
    if not replay:
        assert any(
            event["kind"] == "mkdir" and event["path"] == str(runtime / "deferred")
            for event in events[:index]
        ), interrupted


@pytest.mark.parametrize("replay", (False, True), ids=("direct", "exact-replay"))
@pytest.mark.parametrize(
    "distance", (1, 3, 5), ids=("distance-1", "distance-3", "distance-5")
)
def test_installed_defer_refuses_replaced_distant_ancestry_until_fresh_attempt(
    installed_wheel: InstalledWheel, tmp_path: Path, replay: bool, distance: int
) -> None:
    project = _prepare(installed_wheel, tmp_path)
    authoritative = _state_bytes(project)
    runtime = project / uuid4().hex / "one/two/three/four/runtime"
    runtime.parent.mkdir(parents=True)
    ancestor = runtime.parents[distance - 1]
    displaced_runtime = project / "displaced" / runtime.relative_to(ancestor)
    previous = identity(ancestor)
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
    assert interrupted["exit"] == 2, interrupted
    assert interrupted["os_error"] is True, interrupted
    assert "identity changed; retry" in interrupted["error"]
    assert str(ancestor) in interrupted["error"].split("identity changed; retry", 1)[1]
    assert "path" not in interrupted
    assert not _ledger(runtime).exists()
    assert _state_bytes(project) == authoritative
    if replay:
        assert _ledger(displaced_runtime).read_bytes() == seeded
    else:
        assert not _ledger(displaced_runtime).exists()

    retry = _invoke(
        installed_wheel, project, "normal", runtime=runtime, ancestor=ancestor
    )
    assert retry["exit"] == 0, retry
    assert retry["path"] == str(_ledger(runtime))
    _assert_one_record(runtime)
    assert _state_bytes(project) == authoritative
    if replay:
        assert _ledger(displaced_runtime).read_bytes() == seeded


@pytest.mark.parametrize("replay", (False, True), ids=("direct", "exact-replay"))
@pytest.mark.parametrize(
    "mode",
    ("replace-at-deferred-mkdir", "replace-during-publication"),
    ids=("deferred-mkdir", "ledger-publication"),
)
def test_installed_defer_refuses_runtime_replacement_until_fresh_attempt(
    installed_wheel: InstalledWheel, tmp_path: Path, replay: bool, mode: str
) -> None:
    project = _prepare(installed_wheel, tmp_path)
    authoritative = _state_bytes(project)
    runtime = project / "ancestor/runtime"
    runtime.mkdir()
    seeded = None
    if replay:
        assert _invoke(installed_wheel, project, "normal")["exit"] == 0
        seeded = _assert_one_record(runtime)
        assert _state_bytes(project) == authoritative
    previous = identity(runtime)
    interrupted = _invoke(installed_wheel, project, mode, ancestor=runtime)
    if mode == "replace-at-deferred-mkdir":
        _assert_runtime_replaced_at_deferred_mkdir(
            interrupted, project, runtime, previous
        )
    else:
        _assert_runtime_replaced_during_publication(
            interrupted, project, runtime, previous, replay
        )
    assert interrupted["exit"] == 2, interrupted
    assert interrupted["os_error"] is True, interrupted
    assert "identity changed; retry" in interrupted["error"]
    assert str(runtime) in interrupted["error"].split("identity changed; retry", 1)[1]
    assert "path" not in interrupted
    assert not _ledger(runtime).exists()
    assert _state_bytes(project) == authoritative
    if replay:
        assert _ledger(project / "displaced").read_bytes() == seeded
    else:
        assert not _ledger(project / "displaced").exists()
    retry = _invoke(installed_wheel, project, "normal")
    assert retry["exit"] == 0, retry
    assert retry["path"] == str(_ledger(runtime))
    _assert_one_record(runtime)
    assert _state_bytes(project) == authoritative
    if replay:
        assert _ledger(project / "displaced").read_bytes() == seeded
    else:
        assert not _ledger(project / "displaced").exists()


def _assert_runtime_reparented_after_chain_confirmation(
    result: dict[str, Any],
    project: Path,
    runtime: Path,
    ancestor: Path,
    previous_ancestor: list[int],
    previous_runtime: list[int],
) -> int:
    events = result["events"]
    reparentings = [event for event in events if event["kind"] == "reparented"]
    assert len(reparentings) == 1, result
    reparenting = reparentings[0]
    assert reparenting == {
        "kind": "reparented",
        "path": str(ancestor),
        "previous": previous_ancestor,
        "displaced": identity(project / "displaced"),
        "replacement": identity(ancestor),
        "runtime_before": previous_runtime,
        "runtime_after": identity(runtime),
        "boundary": "ledger-open",
    }
    assert reparenting["displaced"] == previous_ancestor
    assert reparenting["replacement"] != previous_ancestor
    assert reparenting["runtime_after"] == previous_runtime
    index = events.index(reparenting)
    before = events[:index]
    observed = before.index(
        {"kind": "observed", "path": str(ancestor), "identity": previous_ancestor}
    )
    confirmed = before.index(
        {
            "kind": "fsync",
            "path": str(ancestor.parent),
            "identity": identity(ancestor.parent),
        }
    )
    runtime_confirmed = before.index(
        {"kind": "fsync", "path": str(runtime), "identity": previous_runtime}
    )
    assert observed < confirmed < runtime_confirmed < index, result
    assert any(
        event["kind"] == "observed" and event["path"] == str(runtime / "deferred")
        for event in before
    ), result
    return index


def _assert_reparented_result_is_safe(
    result: dict[str, Any],
    runtime: Path,
    ancestor: Path,
    confirmation_index: int,
    replay: bool,
    seeded: bytes | None,
) -> None:
    events = result["events"]
    if result["exit"] == 0:
        assert result["path"] == str(_ledger(runtime))
        returned = {"kind": "returned", "path": str(_ledger(runtime))}
        assert events.count(returned) == 1, result
        return_index = events.index(returned)
        assert confirmation_index < return_index, result
        for parent in (ancestor.parent, ancestor):
            assert {
                "kind": "fsync",
                "path": str(parent),
                "identity": identity(parent),
            } in events[confirmation_index + 1 : return_index], result
        _assert_one_record(runtime)
    else:
        assert result["exit"] == 2, result
        assert result["os_error"] is True, result
        assert "identity changed; retry" in result["error"], result
        assert str(ancestor) in result["error"].split("identity changed; retry", 1)[1]
        assert "path" not in result
        assert not any(event["kind"] == "returned" for event in events), result
        if replay:
            assert _ledger(runtime).read_bytes() == seeded
        else:
            assert not _ledger(runtime).exists()
    if replay:
        assert _ledger(runtime).read_bytes() == seeded


def _assert_reparented_retry_and_replay(
    installed: InstalledWheel,
    project: Path,
    runtime: Path,
    ancestor: Path,
    authoritative: tuple[bytes, bytes],
    previous_runtime: list[int],
    replay: bool,
    seeded: bytes | None,
) -> None:
    retry = _invoke(installed, project, "normal", runtime=runtime, ancestor=ancestor)
    assert retry["exit"] == 0, retry
    assert retry["path"] == str(_ledger(runtime))
    committed = _assert_one_record(runtime)
    assert identity(runtime) == previous_runtime
    assert _state_bytes(project) == authoritative
    for parent in (ancestor.parent, ancestor):
        assert {
            "kind": "fsync",
            "path": str(parent),
            "identity": identity(parent),
        } in retry["events"], retry
    exact_replay = _invoke(
        installed, project, "normal", runtime=runtime, ancestor=ancestor
    )
    assert exact_replay["exit"] == 0, exact_replay
    assert _assert_one_record(runtime) == committed
    if replay:
        assert committed == seeded
    assert _state_bytes(project) == authoritative


@pytest.mark.parametrize("replay", (False, True), ids=("direct", "exact-replay"))
@pytest.mark.parametrize(
    "distance", (1, 3, 5), ids=("distance-1", "distance-3", "distance-5")
)
def test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry(
    installed_wheel: InstalledWheel, tmp_path: Path, replay: bool, distance: int
) -> None:
    project = _prepare(installed_wheel, tmp_path)
    authoritative = _state_bytes(project)
    runtime = project / uuid4().hex / "one/two/three/four/runtime"
    runtime.mkdir(parents=True)
    ancestor = runtime.parents[distance - 1]
    previous_ancestor, previous_runtime = identity(ancestor), identity(runtime)
    seeded = None
    if replay:
        seed = _invoke(
            installed_wheel, project, "normal", runtime=runtime, ancestor=ancestor
        )
        assert seed["exit"] == 0, seed
        seeded = _assert_one_record(runtime)
        assert _state_bytes(project) == authoritative

    result = _invoke(
        installed_wheel,
        project,
        "reparent-during-publication",
        runtime=runtime,
        ancestor=ancestor,
    )
    index = _assert_runtime_reparented_after_chain_confirmation(
        result, project, runtime, ancestor, previous_ancestor, previous_runtime
    )
    _assert_reparented_result_is_safe(result, runtime, ancestor, index, replay, seeded)
    assert _state_bytes(project) == authoritative
    displaced_runtime = project / "displaced" / runtime.relative_to(ancestor)
    assert not displaced_runtime.exists()

    _assert_reparented_retry_and_replay(
        installed_wheel,
        project,
        runtime,
        ancestor,
        authoritative,
        previous_runtime,
        replay,
        seeded,
    )
    assert not displaced_runtime.exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="Darwin capability contract")
def test_installed_defer_confirms_parent_through_native_search_only_access(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    project = _prepare(installed_wheel, tmp_path)
    authoritative = _state_bytes(project)
    ancestor = project / "ancestor"
    runtime = ancestor / "runtime"
    runtime.mkdir()
    original_mode = stat.S_IMODE(ancestor.stat().st_mode)
    try:
        ancestor.chmod(0o111)
        assert stat.S_IMODE(ancestor.stat().st_mode) == 0o111
        result = _invoke(installed_wheel, project, "search")
    finally:
        ancestor.chmod(original_mode)
    assert stat.S_IMODE(ancestor.stat().st_mode) == original_mode
    assert _state_bytes(project) == authoritative
    if "skip" in result:
        pytest.skip(result["skip"])
    assert result["exit"] == 0, result
    ancestor_opens = [
        event["flags"]
        for event in result["events"]
        if event["kind"] == "open" and event["path"] == str(ancestor)
    ]
    assert any(
        flags & result["native_search_flag"] == result["native_search_flag"]
        and flags & result["directory_flag"] == result["directory_flag"]
        for flags in ancestor_opens
    ), result
    assert {
        "kind": "fsync",
        "path": str(ancestor),
        "identity": identity(ancestor),
    } in result["events"]
    assert result["path"] == str(_ledger(runtime))
    _assert_one_record(runtime)


@pytest.mark.skipif(sys.platform != "darwin", reason="Darwin capability contract")
def test_installed_defer_refuses_execute_only_ancestor_without_search_descriptor(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    project = _prepare(installed_wheel, tmp_path)
    authoritative = _state_bytes(project)
    ancestor = project / "ancestor"
    runtime = ancestor / "runtime"
    runtime.mkdir()
    seeded_result = _invoke(installed_wheel, project, "normal")
    assert seeded_result["exit"] == 0, seeded_result
    seeded = _assert_one_record(runtime)
    assert _state_bytes(project) == authoritative
    original_mode = stat.S_IMODE(ancestor.stat().st_mode)
    try:
        ancestor.chmod(0o111)
        assert stat.S_IMODE(ancestor.stat().st_mode) == 0o111
        result = _invoke(installed_wheel, project, "no-search")
    finally:
        ancestor.chmod(original_mode)
    assert stat.S_IMODE(ancestor.stat().st_mode) == original_mode
    assert _state_bytes(project) == authoritative
    if "skip" in result:
        pytest.skip(result["skip"])
    assert result["exit"] == 2, result
    assert result["descriptors_hidden"] is True, result
    assert result["permission_error"] is True, result
    assert result["os_error"] is True, result
    assert result["errno"] == errno.EACCES, result
    assert result["cause_type"] == "PermissionError", result
    assert result["cause_errno"] == errno.EACCES, result
    assert result["cause_is_original"] is True, result
    assert str(ancestor) in result["error"]
    assert "PosixPath(" not in result["error"]
    assert "path" not in result
    assert _ledger(runtime).read_bytes() == seeded


def test_installed_defer_confirms_first_descendant_without_root_self_confirmation(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    project = _prepare(installed_wheel, tmp_path)
    authoritative = _state_bytes(project)
    result = _invoke(installed_wheel, project, "normal")
    assert result["exit"] == 0, result
    root = Path(project.anchor)
    first_descendant = root / project.parts[1]
    events = result["events"]
    assert not any(
        event["kind"] == "mkdir" and event["path"] == str(root) for event in events
    ), result
    confirmations = [
        event
        for event in events
        if event["kind"] == "fsync" and event["path"] == str(root)
    ]
    assert confirmations == [
        {"kind": "fsync", "path": str(root), "identity": identity(root)}
    ], result
    assert {
        "kind": "observed",
        "path": str(first_descendant),
        "identity": identity(first_descendant),
    } in events[: events.index(confirmations[0])]
    _assert_one_record(project / "ancestor/runtime")
    assert _state_bytes(project) == authoritative


def test_installed_defer_avoids_creation_attempts_on_existing_external_ancestors(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    project = _prepare(installed_wheel, tmp_path)
    authoritative = _state_bytes(project)
    result = _invoke(installed_wheel, project, "forbid-ancestor-mkdir")
    assert result["exit"] == 0, result
    assert not [
        event
        for event in result["events"]
        if event["kind"] == "mkdir" and event["forbidden"]
    ], result
    runtime = project / "ancestor/runtime"
    for parent in runtime.parents:
        assert {
            "kind": "fsync",
            "path": str(parent),
            "identity": identity(parent),
        } in result["events"], (str(parent), result)
    assert result["path"] == str(_ledger(runtime))
    _assert_one_record(runtime)
    assert _state_bytes(project) == authoritative
