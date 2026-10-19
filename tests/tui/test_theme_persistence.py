from __future__ import annotations

import asyncio
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest

from ovcaq.runtime.registry import FleetRun, ProcessIdentity
from ovcaq.tui.app import (
    FleetApp,
    ProjectApp,
    ThemeResult,
    load_theme,
    save_theme,
    theme_path,
)
from ovcaq.tui.discovery import FleetView
from ovcaq.tui.model import ProjectView


class Observer:
    def __init__(self, run: FleetRun) -> None:
        self.current = ProjectView(
            run=run,
            status="running",
            phase=None,
            next_phase=None,
            prd="00008",
            revision=17,
            tasks_completed=1,
            tasks_total=3,
            review_cycle=0,
            provider="generic",
            duration_seconds=None,
            usage=None,
            lanes=(),
            capabilities=(),
            attention=None,
            telemetry="complete",
            gaps=(),
        )

    def poll(self) -> ProjectView:
        return self.current

    def close(self) -> None:
        pass


class Controls:
    def pause(
        self, run: FleetRun, expected_revision: int, reason: str | None = None
    ) -> None:
        raise AssertionError("Theme selection must not pause a run")

    def resume(self, run: FleetRun, expected_revision: int) -> None:
        raise AssertionError("Theme selection must not resume a run")

    def stop(self, run: FleetRun) -> ProcessIdentity:
        raise AssertionError("Theme selection must not stop a run")


def _app(kind: str, root: Path) -> FleetApp | ProjectApp:
    run = FleetRun("selected", root, "generic", "2026-10-03T12:00:00Z", 12345, "start")
    if kind == "fleet":
        return FleetApp(FleetView((run,), (), ()))
    return ProjectApp(Observer(run), Controls(), poll_interval=60)


def _screen_text(app: FleetApp | ProjectApp) -> str:
    screenshot = ET.fromstring(app.export_screenshot())
    return " ".join(
        "".join(element.itertext())
        for element in screenshot.iter("{http://www.w3.org/2000/svg}text")
    )


@pytest.fixture(autouse=True)
def isolated_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.chdir(tmp_path)


@pytest.mark.parametrize("kind", ["fleet", "project"])
def test_all_real_theme_changes_persist_and_load_in_a_later_app(
    kind: str, tmp_path: Path
) -> None:
    assert save_theme("gruvbox") == ThemeResult("gruvbox", None)
    path = theme_path()
    app = _app(kind, tmp_path)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.theme == "gruvbox"
            for name in (
                "nord",
                "textual-light",
                "gruvbox",
                "textual-dark",
                "catppuccin-mocha",
            ):
                app.theme = name
                await pilot.pause()
                assert load_theme() == ThemeResult(name, None)
                assert path.read_text().strip() == name
                assert path.stat().st_mode & 0o777 == 0o600
            await pilot.press("q")
        later = _app(kind, tmp_path)
        async with later.run_test() as pilot:
            await pilot.pause()
            assert later.theme == "catppuccin-mocha"
            await pilot.press("q")

    asyncio.run(exercise())
    assert set(path.parent.iterdir()) == {path}


@pytest.mark.parametrize("kind", ["fleet", "project"])
@pytest.mark.parametrize("condition", ["invalid", "unavailable"])
def test_mount_preserves_bad_file_and_displays_a_nonfatal_safe_gap(
    kind: str, condition: str, tmp_path: Path
) -> None:
    path = theme_path()
    path.parent.mkdir(parents=True)
    original = (
        b"private-invalid-theme\x1b[31m\n" if condition == "invalid" else b"nord\n"
    )
    path.write_bytes(original)
    if condition == "unavailable":
        path.chmod(0)
    inode = path.stat().st_ino
    expected = load_theme()
    assert expected.name is None and expected.gap
    app = _app(kind, tmp_path)

    async def exercise() -> None:
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert app.theme == "textual-dark"
            screen = _screen_text(app)
            assert expected.gap in screen
            assert "private-invalid-theme" not in screen
            assert path.stat().st_ino == inode
            await pilot.press("q")

    try:
        asyncio.run(exercise())
    finally:
        path.chmod(0o600)
    assert path.read_bytes() == original


@pytest.mark.parametrize("kind", ["fleet", "project"])
def test_mount_without_a_preference_uses_dark_without_writing(
    kind: str, tmp_path: Path
) -> None:
    path = theme_path()
    assert not path.exists()
    app = _app(kind, tmp_path)

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.theme == "textual-dark"
            assert not path.exists()
            await pilot.press("q")

    asyncio.run(exercise())
    assert not path.exists()


@pytest.mark.parametrize("kind", ["fleet", "project"])
def test_failed_user_theme_save_is_visible_and_app_can_still_detach(
    kind: str, tmp_path: Path
) -> None:
    assert save_theme("textual-dark") == ThemeResult("textual-dark", None)
    path = theme_path()
    outside = tmp_path / "outside"
    outside.write_bytes(b"private-outside-evidence")
    app = _app(kind, tmp_path)

    async def exercise() -> None:
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            path.unlink()
            path.symlink_to(outside)
            expected = save_theme("nord")
            assert expected.name is None and expected.gap
            app.theme = "nord"
            await pilot.pause()
            screen = _screen_text(app)
            assert expected.gap in screen
            assert "private-outside-evidence" not in screen
            assert path.is_symlink()
            assert outside.read_bytes() == b"private-outside-evidence"
            await pilot.press("q")

    asyncio.run(exercise())


def _select_anchor(
    selection: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    if selection == "unset":
        monkeypatch.delenv("XDG_CONFIG_HOME")
        anchor = Path.home() / ".config"
    elif selection == "empty":
        monkeypatch.setenv("XDG_CONFIG_HOME", "")
        anchor = tmp_path
    elif selection in ("relative", "relative-space", "absolute-space"):
        name = "relative-config" if selection == "relative" else "config with spaces"
        anchor = tmp_path / name
        configured = str(anchor) if selection == "absolute-space" else name
        monkeypatch.setenv("XDG_CONFIG_HOME", configured)
    else:
        name = "trusted target" if selection == "alias-space" else "trusted-target"
        anchor = tmp_path / name
        anchor.mkdir()
        alias = (
            Path.home() / ".config"
            if selection == "home-alias"
            else tmp_path
            / ("alias with spaces" if selection == "alias-space" else "alias")
        )
        alias.symlink_to(anchor, target_is_directory=True)
        if selection == "home-alias":
            monkeypatch.delenv("XDG_CONFIG_HOME")
        else:
            monkeypatch.setenv("XDG_CONFIG_HOME", str(alias))
    return anchor


@pytest.mark.parametrize(
    "selection",
    [
        "unset",
        "empty",
        "relative",
        "alias",
        "home-alias",
        "absolute-space",
        "relative-space",
        "alias-space",
    ],
)
def test_theme_storage_uses_shared_trusted_xdg_anchor_semantics(
    selection: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    anchor = _select_anchor(selection, tmp_path, monkeypatch)
    assert theme_path() == anchor / "ovcaq/theme"
    assert load_theme() == ThemeResult("textual-dark", None)
    assert not theme_path().exists()
    assert save_theme("nord") == ThemeResult("nord", None)
    assert load_theme() == ThemeResult("nord", None)
    assert (anchor / "ovcaq/theme").read_text().strip() == "nord"
    theme_path().unlink()
    assert load_theme() == ThemeResult("textual-dark", None)
    assert not theme_path().exists()


@pytest.mark.parametrize(
    "name", ["textual-dark", "textual-light", "nord", "gruvbox", "catppuccin-mocha"]
)
def test_allowlisted_save_is_private_atomic_and_leaves_no_temporary_files(
    name: str,
) -> None:
    path = theme_path()
    path.parent.mkdir(parents=True)
    siblings = {
        path.parent / "config.toml": b"# preserve config\n",
        path.parent / "notes.txt": b"unrelated sibling\n",
    }
    for sibling, content in siblings.items():
        sibling.write_bytes(content)
    inodes = {sibling: sibling.stat().st_ino for sibling in siblings}
    assert save_theme("gruvbox") == ThemeResult("gruvbox", None)
    for sibling, content in siblings.items():
        assert sibling.read_bytes() == content
        assert sibling.stat().st_ino == inodes[sibling]
    with path.open("rb") as old_file:
        old_content = old_file.read()
        old_inode = os.fstat(old_file.fileno()).st_ino
        assert save_theme(name) == ThemeResult(name, None)
        old_file.seek(0)
        assert old_file.read() == old_content
        assert path.stat().st_ino != old_inode
    assert load_theme() == ThemeResult(name, None)
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert set(path.parent.iterdir()) == {path, *siblings}
    for sibling, content in siblings.items():
        assert sibling.read_bytes() == content
        assert sibling.stat().st_ino == inodes[sibling]


@pytest.mark.parametrize("name", ["", "nord\n", "NORD", "dracula", "../nord"])
def test_disallowed_theme_names_preserve_the_existing_file(name: str) -> None:
    assert save_theme("gruvbox") == ThemeResult("gruvbox", None)
    path = theme_path()
    original = path.read_bytes()
    inode = path.stat().st_ino

    result = save_theme(name)

    assert result.name is None and result.gap
    assert path.read_bytes() == original
    assert path.stat().st_ino == inode
    assert set(path.parent.iterdir()) == {path}


@pytest.mark.parametrize(
    "content", [b"private-invalid-theme\x1b[31m", b"nord" + b" " * 253, b"\xff"]
)
def test_invalid_oversized_or_undecodable_file_is_ignored_without_content_leak(
    content: bytes,
) -> None:
    path = theme_path()
    path.parent.mkdir(parents=True)
    path.write_bytes(content)

    result = load_theme()

    assert result.name is None and result.gap
    assert "private-invalid-theme" not in result.gap
    assert "\x1b" not in result.gap
    assert path.read_bytes() == content


@pytest.mark.parametrize("location", ["directory", "file"])
def test_descendant_symlinks_are_rejected_without_changing_their_targets(
    location: str, tmp_path: Path
) -> None:
    path = theme_path()
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "theme"
    target.write_bytes(b"nord\n")
    if location == "directory":
        path.parent.parent.mkdir(parents=True)
        path.parent.symlink_to(outside, target_is_directory=True)
        link = path.parent
    else:
        path.parent.mkdir(parents=True)
        path.symlink_to(target)
        link = path

    for operation in (load_theme, lambda: save_theme("gruvbox")):
        result = operation()
        assert result.name is None and result.gap
        assert link.is_symlink()
        assert target.read_bytes() == b"nord\n"
        assert set(outside.iterdir()) == {target}


@pytest.mark.parametrize("kind", ["directory", "fifo"])
def test_nonregular_theme_files_are_ignored_without_blocking(kind: str) -> None:
    path = theme_path()
    path.parent.mkdir(parents=True)
    if kind == "directory":
        path.mkdir()
    else:
        os.mkfifo(path)

    result = load_theme()

    assert result.name is None and result.gap


@pytest.mark.parametrize("location", ["directory", "file"])
def test_read_never_follows_a_descendant_replaced_at_the_open_boundary(
    location: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert save_theme("nord") == ThemeResult("nord", None)
    path = theme_path()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "theme").write_bytes(b"gruvbox\n")
    displaced = tmp_path / "displaced"
    original_open = os.open
    changed = False

    def replace_at_open(file: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        nonlocal changed
        if not changed and Path(os.fsdecode(file)).name == "theme":
            changed = True
            victim = path.parent if location == "directory" else path
            victim.rename(displaced)
            victim.symlink_to(outside if location == "directory" else outside / "theme")
        return original_open(file, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", replace_at_open)
    result = load_theme()

    assert changed, "The replacement must occur at the filesystem read boundary"
    assert result.name in (None, "nord")
    if result.name is None:
        assert result.gap
    assert (outside / "theme").read_bytes() == b"gruvbox\n"
    assert (path.parent if location == "directory" else path).is_symlink()


@pytest.mark.parametrize("location", ["directory", "file"])
def test_save_preserves_concurrent_replacement_evidence_and_reports_a_gap(
    location: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert save_theme("nord") == ThemeResult("nord", None)
    path = theme_path()
    original_content = path.read_bytes()
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "theme"
    target.write_bytes(b"gruvbox\n")
    displaced = tmp_path / "displaced"
    original_open = os.open
    changed = False

    def replace_at_open(file: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        nonlocal changed
        if not changed and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT):
            changed = True
            victim = path.parent if location == "directory" else path
            victim.rename(displaced)
            victim.symlink_to(outside if location == "directory" else target)
        return original_open(file, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", replace_at_open)
    result = save_theme("catppuccin-mocha")

    assert changed, "The replacement must occur at the filesystem write boundary"
    assert result.name is None and result.gap
    assert (path.parent if location == "directory" else path).is_symlink()
    assert target.read_bytes() == b"gruvbox\n"
    assert set(outside.iterdir()) == {target}
    if location == "directory":
        assert set(displaced.iterdir()) == {displaced / "theme"}
        assert (displaced / "theme").read_bytes() == original_content
    else:
        assert displaced.read_bytes() == original_content


def test_concurrent_reader_atime_update_does_not_prevent_saving_a_new_theme(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert save_theme("nord") == ThemeResult("nord", None)
    path = theme_path()
    original_content = path.read_bytes()
    original_open = os.open
    changed = False

    def read_at_open(file: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        nonlocal changed
        if not changed and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT):
            changed = True
            before = path.stat()
            assert path.read_bytes() == original_content
            os.utime(path, ns=(before.st_atime_ns + 1_000_000_000, before.st_mtime_ns))
            after = path.stat()
            assert after.st_atime_ns != before.st_atime_ns
            assert after.st_mtime_ns == before.st_mtime_ns
            assert (after.st_dev, after.st_ino, after.st_size, after.st_mode) == (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mode,
            )
        return original_open(file, flags, *args, **kwargs)

    with path.open("rb") as prior_file:
        prior_identity = os.fstat(prior_file.fileno())
        monkeypatch.setattr(os, "open", read_at_open)
        result = save_theme("gruvbox")
        assert changed, "The reader must run at the filesystem write boundary"
        assert result == ThemeResult("gruvbox", None)
        assert prior_file.read() == original_content
        assert os.fstat(prior_file.fileno()).st_ino == prior_identity.st_ino
        assert path.stat().st_ino != prior_identity.st_ino
    assert load_theme() == ThemeResult("gruvbox", None)
    assert path.read_text().strip() == "gruvbox"
    assert set(path.parent.iterdir()) == {path}
