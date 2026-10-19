from __future__ import annotations

import fcntl
import os
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from types import FrameType

import pytest

from ovcaq import tui
from ovcaq.runtime.registry import FleetEntry, FleetRegistry, FleetRun, RegistrySnapshot
from ovcaq.tui.discovery import FleetView, discover_fleet, select_run


class _SnapshotRegistry(FleetRegistry):
    """Supply the shared registry's already-classified boundary result."""

    def __init__(self, result: RegistrySnapshot) -> None:
        self.result = result
        self.snapshot_calls = 0

    def snapshot(self) -> RegistrySnapshot:
        self.snapshot_calls += 1
        return self.result


def _entry(root: Path, run_id: str = "run-1") -> FleetEntry:
    return FleetEntry(
        schema_version=1,
        root=root,
        pid=876543,
        process_start="process-start-token",
        run_id=run_id,
        agent="test-agent",
        started_at="2026-10-03T10:00:00Z",
    )


def _run(entry: FleetEntry) -> FleetRun:
    return FleetRun(
        run_id=entry.run_id,
        root=entry.root,
        agent=entry.agent,
        started_at=entry.started_at,
        pid=entry.pid,
        process_start=entry.process_start,
    )


@pytest.mark.parametrize("order", [(4, 3, 2, 1, 0), (0, 1, 2, 3, 4), (2, 4, 1, 0, 3)])
def test_discovery_projects_one_snapshot_and_sorts_only_live_runs(
    tmp_path: Path, order: tuple[int, ...]
) -> None:
    early_a = replace(_entry(tmp_path / "a", "a"), agent="first-agent")
    early_z = replace(early_a, run_id="z", pid=876544, process_start="other-token")
    late = replace(
        early_a, run_id="0", agent="second-agent", started_at="2026-10-04T09:00:00Z"
    )
    other_root = replace(
        early_a, root=tmp_path / "b", run_id="0", started_at="2026-09-30T10:00:00Z"
    )
    last_root = replace(early_a, root=tmp_path / "c", run_id="last")
    ordered_entries = (early_a, early_z, late, other_root, last_root)
    live = tuple(ordered_entries[index] for index in order)
    snapshot = RegistrySnapshot(
        live=live,
        malformed=(tmp_path / "z-broken.json", tmp_path / "a-broken.json"),
        stale=(tmp_path / "z-stale.json", tmp_path / "a-stale.json"),
    )
    registry = _SnapshotRegistry(snapshot)

    view = discover_fleet(registry)

    assert registry.snapshot_calls == 1
    assert view == FleetView(
        runs=tuple(_run(entry) for entry in ordered_entries),
        malformed_entries=snapshot.malformed,
        stale_entries=snapshot.stale,
    )
    assert snapshot.live == live


@pytest.mark.parametrize(
    "has_malformed,has_stale",
    [(False, False), (True, True), (True, False), (False, True)],
)
def test_discovery_with_no_live_entries_preserves_registry_diagnostics(
    tmp_path: Path, has_malformed: bool, has_stale: bool
) -> None:
    malformed = (tmp_path / "broken.json",) if has_malformed else ()
    stale = (tmp_path / "stale.json",) if has_stale else ()
    registry = _SnapshotRegistry(
        RegistrySnapshot(live=(), malformed=malformed, stale=stale)
    )

    assert discover_fleet(registry) == FleetView(
        runs=(), malformed_entries=malformed, stale_entries=stale
    )
    assert registry.snapshot_calls == 1


def test_discovery_trusts_shared_liveness_without_process_or_lock_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    entry = _entry(tmp_path / "project-without-a-run-lock")
    registry = _SnapshotRegistry(
        RegistrySnapshot(live=(entry,), malformed=(), stale=())
    )
    forbidden = {"process_identity", "process_matches", "run_lock_held", "prune"}

    def forbid_classifier(frame: FrameType, event: str, arg: object) -> None:
        if event == "call" and frame.f_code.co_name in forbidden:
            raise AssertionError(f"discovery invoked {frame.f_code.co_name}")

    def forbid_external_check(*args: object, **kwargs: object) -> None:
        raise AssertionError("discovery attempted a process or lock check")

    monkeypatch.setattr(os, "kill", forbid_external_check)
    monkeypatch.setattr(subprocess, "Popen", forbid_external_check)
    monkeypatch.setattr(fcntl, "flock", forbid_external_check)
    previous_profile = sys.getprofile()
    try:
        sys.setprofile(forbid_classifier)
        view = discover_fleet(registry)
    finally:
        sys.setprofile(previous_profile)

    assert view == FleetView(
        runs=(_run(entry),), malformed_entries=(), stale_entries=()
    )
    assert registry.snapshot_calls == 1
    assert not entry.root.exists()


@pytest.fixture
def fleet_view(tmp_path: Path) -> FleetView:
    return FleetView(
        runs=(
            _run(_entry(tmp_path / "shared", "first")),
            _run(_entry(tmp_path / "shared", "second")),
            _run(_entry(tmp_path / "unique", "third")),
        ),
        malformed_entries=(),
        stale_entries=(),
    )


@pytest.mark.parametrize(
    "run_id,root_name,index",
    [("first", None, 0), ("second", "shared", 1), (None, "unique", 2)],
)
def test_selection_applies_each_selector_and_returns_original_identity(
    fleet_view: FleetView,
    tmp_path: Path,
    run_id: str | None,
    root_name: str | None,
    index: int,
) -> None:
    root = tmp_path / root_name if root_name is not None else None

    selected = select_run(fleet_view, run_id=run_id, root=root)

    assert selected is fleet_view.runs[index]
    assert selected.pid == 876543
    assert selected.process_start == "process-start-token"


@pytest.mark.parametrize(
    "run_id,root_name",
    [
        (None, None),
        (None, "shared"),
        ("missing", None),
        (None, "missing"),
        ("first", "unique"),
        ("third", "shared"),
        ("", None),
    ],
)
def test_ambiguous_or_unmatched_selection_lists_available_ids_and_roots(
    fleet_view: FleetView, tmp_path: Path, run_id: str | None, root_name: str | None
) -> None:
    root = tmp_path / root_name if root_name is not None else None

    with pytest.raises(ValueError) as error:
        select_run(fleet_view, run_id=run_id, root=root)

    message = str(error.value)
    for run in fleet_view.runs:
        assert run.run_id in message
        assert str(run.root) in message


def test_no_selectors_selects_the_only_run(tmp_path: Path) -> None:
    run = _run(_entry(tmp_path))
    view = FleetView(runs=(run,), malformed_entries=(), stale_entries=())

    assert select_run(view, run_id=None, root=None) is run


@pytest.mark.parametrize(
    "run_id,root_name",
    [("wrong", None), (None, "wrong"), ("run-1", "wrong"), ("wrong", "project")],
)
def test_singleton_rejects_mismatching_selectors(
    tmp_path: Path, run_id: str | None, root_name: str | None
) -> None:
    run = _run(_entry(tmp_path / "project"))
    view = FleetView(runs=(run,), malformed_entries=(), stale_entries=())
    root = tmp_path / root_name if root_name is not None else None

    with pytest.raises(ValueError) as error:
        select_run(view, run_id=run_id, root=root)

    assert run.run_id in str(error.value)
    assert str(run.root) in str(error.value)


@pytest.mark.parametrize("run_id", [None, "third"])
def test_root_selection_rejects_same_basename_under_another_parent(
    fleet_view: FleetView, tmp_path: Path, run_id: str | None
) -> None:
    other_root = tmp_path / "another-parent" / "unique"

    with pytest.raises(ValueError) as error:
        select_run(fleet_view, run_id=run_id, root=other_root)

    for run in fleet_view.runs:
        assert run.run_id in str(error.value)
        assert str(run.root) in str(error.value)


def test_duplicate_run_ids_require_root_disambiguation(tmp_path: Path) -> None:
    runs = (
        _run(_entry(tmp_path / "first", "duplicate")),
        _run(_entry(tmp_path / "second", "duplicate")),
    )
    view = FleetView(runs=runs, malformed_entries=(), stale_entries=())

    with pytest.raises(ValueError) as error:
        select_run(view, run_id="duplicate", root=None)

    for run in runs:
        assert run.run_id in str(error.value)
        assert str(run.root) in str(error.value)
        assert select_run(view, run_id=run.run_id, root=run.root) is run


@pytest.mark.parametrize("run_id", [None, "missing"])
def test_empty_fleet_rejects_selection(run_id: str | None) -> None:
    view = FleetView(runs=(), malformed_entries=(), stale_entries=())

    with pytest.raises(ValueError):
        select_run(view, run_id=run_id, root=None)


@pytest.mark.parametrize("changed_field", ["pid", "process_start"])
def test_rediscovery_keeps_replacement_identity_distinct_from_selected_run(
    tmp_path: Path, changed_field: str
) -> None:
    original = _entry(tmp_path)
    replacement = replace(
        original,
        **{
            changed_field: {
                "pid": original.pid + 1,
                "process_start": "replacement-token",
            }[changed_field]
        },
    )
    registry = _SnapshotRegistry(
        RegistrySnapshot(live=(original,), malformed=(), stale=())
    )
    first_view = discover_fleet(registry)
    selected = select_run(first_view, run_id=original.run_id, root=original.root)
    registry.result = RegistrySnapshot(live=(replacement,), malformed=(), stale=())

    second_view = discover_fleet(registry)
    current = select_run(second_view, run_id=original.run_id, root=original.root)

    assert registry.snapshot_calls == 2
    assert selected is first_view.runs[0]
    assert current is second_view.runs[0]
    assert selected == _run(original)
    assert current == _run(replacement)
    assert selected != current


@pytest.mark.parametrize("field", ["pid", "process_start"])
def test_selected_process_identity_is_immutable(tmp_path: Path, field: str) -> None:
    entry = _entry(tmp_path)
    run = _run(entry)

    assert not hasattr(run, "__dict__")
    assert run.run_id == entry.run_id
    assert run.root == entry.root
    assert run.agent == entry.agent
    assert run.started_at == entry.started_at
    assert run.pid == entry.pid
    assert run.process_start == entry.process_start

    with pytest.raises(FrozenInstanceError):
        setattr(run, field, None)


def test_fleet_view_is_immutable(tmp_path: Path) -> None:
    run = _run(_entry(tmp_path))
    view = FleetView(runs=(run,), malformed_entries=(), stale_entries=())

    assert not hasattr(view, "__dict__")
    assert view.runs == (run,)
    assert view.malformed_entries == ()
    assert view.stale_entries == ()

    with pytest.raises(FrozenInstanceError):
        view.runs = ()


def test_tui_reexports_the_shared_records_and_discovery_operations() -> None:
    assert tui.FleetRun is FleetRun
    assert tui.FleetView is FleetView
    assert tui.discover_fleet is discover_fleet
    assert tui.select_run is select_run
