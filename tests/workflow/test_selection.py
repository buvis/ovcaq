from __future__ import annotations

from pathlib import Path

import pytest

from ovcaq.workflow.paths import LifecyclePaths, resolve_lifecycle_paths
from ovcaq.workflow.selection import select, select_from_paths, selectable, sequence


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        pytest.param("00089-extract-core-v1.md", 89, id="five-digits"),
        pytest.param("00010-leading-zero.md", 10, id="leading-zero"),
        pytest.param("FASTTRACK-PLAN-v5.md", None, id="unnumbered"),
        pytest.param("001189-six-digits.md", None, id="six-digits"),
        pytest.param("0089-four-digits.md", None, id="four-digits"),
    ],
)
def test_sequence_rows(name: str, expected: int | None) -> None:
    assert sequence(name) == expected


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        pytest.param(
            ["00100-b.md", "00089-a.md", "00095-c.md"],
            ["00089-a.md", "00095-c.md", "00100-b.md"],
            id="numeric-order",
        ),
        pytest.param(
            ["FASTTRACK-PLAN-v5.md", "00089-a.md"],
            ["00089-a.md"],
            id="unnumbered-excluded",
        ),
        pytest.param(
            ["00089-a.md.bak", "00090-b.txt", "00089-a.md"],
            ["00089-a.md"],
            id="markdown-only",
        ),
        pytest.param(
            ["00089-zebra.md", "00089-alpha.md"],
            ["00089-alpha.md", "00089-zebra.md"],
            id="deterministic-tie",
        ),
        pytest.param(
            ["00001-safe\n## Injected.md", "00002-safe.md"],
            ["00002-safe.md"],
            id="control-character-excluded",
        ),
        pytest.param([], [], id="empty"),
    ],
)
def test_selectable_rows(names: list[str], expected: list[str]) -> None:
    assert selectable(names) == expected


@pytest.mark.parametrize(
    ("wip", "backlog", "expected"),
    [
        pytest.param(
            ["00095-b.md", "00089-a.md"],
            [],
            ("00089-a.md", "wip"),
            id="lowest-wip",
        ),
        pytest.param(
            ["00099-in-progress.md"],
            ["00001-older.md"],
            ("00099-in-progress.md", "wip"),
            id="wip-priority",
        ),
        pytest.param(
            [],
            ["00095-b.md", "00089-a.md"],
            ("00089-a.md", "backlog"),
            id="backlog-fallback",
        ),
        pytest.param(
            ["notes.txt", "README.md"],
            ["00089-a.md"],
            ("00089-a.md", "backlog"),
            id="unselectable-wip",
        ),
        pytest.param([], [], (None, "drained"), id="drained"),
    ],
)
def test_selection_rows(
    wip: list[str],
    backlog: list[str],
    expected: tuple[str | None, str],
) -> None:
    assert select(wip, backlog) == expected


def test_selection_excludes_prds_present_only_in_hold(tmp_path: Path) -> None:
    paths = resolve_lifecycle_paths(tmp_path, Path("prds"))
    paths.hold.mkdir(parents=True)
    paths.hold.joinpath("00001-held.md").write_text("# Held\n", encoding="utf-8")

    assert select_from_paths(paths) == (None, "drained")


def test_lifecycle_paths_resolve_configured_relative_root(tmp_path: Path) -> None:
    paths = resolve_lifecycle_paths(tmp_path, Path("planning/prds"))

    assert paths == LifecyclePaths(
        root=(tmp_path / "planning/prds").resolve(),
        backlog=(tmp_path / "planning/prds/backlog").resolve(),
        wip=(tmp_path / "planning/prds/wip").resolve(),
        hold=(tmp_path / "planning/prds/hold").resolve(),
        done=(tmp_path / "planning/prds/done").resolve(),
    )


def test_lifecycle_paths_preserve_configured_absolute_root(tmp_path: Path) -> None:
    configured = tmp_path / "elsewhere" / "prds"
    assert resolve_lifecycle_paths(tmp_path / "repo", configured).root == configured


@pytest.mark.parametrize("missing", ["wip", "backlog"])
def test_select_from_paths_treats_missing_lifecycle_directory_as_empty(
    tmp_path: Path,
    missing: str,
) -> None:
    paths = resolve_lifecycle_paths(tmp_path, Path("prds"))
    present = paths.backlog if missing == "wip" else paths.wip
    present.mkdir(parents=True)
    (present / "00007-present.md").write_text("# PRD\n", encoding="utf-8")

    expected_source = "backlog" if missing == "wip" else "wip"
    assert select_from_paths(paths) == ("00007-present.md", expected_source)


def test_select_from_paths_treats_non_directory_as_empty(tmp_path: Path) -> None:
    paths = resolve_lifecycle_paths(tmp_path, Path("prds"))
    paths.root.mkdir()
    paths.wip.write_text("not a directory", encoding="utf-8")

    assert select_from_paths(paths) == (None, "drained")


def test_select_from_paths_ignores_directory_shaped_prds(tmp_path: Path) -> None:
    paths = resolve_lifecycle_paths(tmp_path, Path("prds"))
    paths.wip.mkdir(parents=True)
    paths.wip.joinpath("00001-directory.md").mkdir()
    paths.wip.joinpath("00002-regular.md").write_text("# PRD\n", encoding="utf-8")

    assert select_from_paths(paths) == ("00002-regular.md", "wip")


def test_select_from_paths_ignores_symlinked_prd_files(tmp_path: Path) -> None:
    paths = resolve_lifecycle_paths(tmp_path, Path("prds"))
    paths.wip.mkdir(parents=True)
    external = tmp_path / "external.md"
    external.write_text("# External\n", encoding="utf-8")
    paths.wip.joinpath("00001-symlink.md").symlink_to(external)
    paths.wip.joinpath("00002-regular.md").write_text("# PRD\n", encoding="utf-8")

    assert select_from_paths(paths) == ("00002-regular.md", "wip")


def test_select_from_paths_does_not_follow_symlinked_lifecycle_directory(
    tmp_path: Path,
) -> None:
    paths = resolve_lifecycle_paths(tmp_path, Path("prds"))
    paths.root.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    external.joinpath("00001-external.md").write_text("# External\n", encoding="utf-8")
    paths.wip.symlink_to(external, target_is_directory=True)

    assert select_from_paths(paths) == (None, "drained")
