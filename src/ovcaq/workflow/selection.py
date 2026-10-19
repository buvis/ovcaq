"""Deterministic PRD selection."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from ovcaq.workflow.paths import LifecyclePaths, is_safe_identifier

type SelectionSource = Literal["wip", "backlog", "drained"]
type Selection = tuple[str | None, SelectionSource]

_SEQUENCE_RE = re.compile(r"^(\d{5})-")


def sequence(name: str) -> int | None:
    """Return a five-digit PRD sequence prefix, if present."""
    if not is_safe_identifier(name):
        return None
    match = _SEQUENCE_RE.match(name)
    return int(match.group(1)) if match is not None else None


def selectable(names: Iterable[str]) -> list[str]:
    """Filter and totally order selectable Markdown PRD names."""
    candidates = [
        name for name in names if name.endswith(".md") and sequence(name) is not None
    ]
    return sorted(candidates, key=lambda name: (sequence(name) or 0, name))


def select(wip: Iterable[str], backlog: Iterable[str]) -> Selection:
    """Select from WIP first, then backlog; hold is unreachable by design."""
    in_wip = selectable(wip)
    if in_wip:
        return in_wip[0], "wip"
    in_backlog = selectable(backlog)
    if in_backlog:
        return in_backlog[0], "backlog"
    return None, "drained"


def _directory_names(directory: Path) -> tuple[str, ...]:
    if directory.is_symlink() or not directory.is_dir():
        return ()
    try:
        return tuple(
            entry.name
            for entry in directory.iterdir()
            if not entry.is_symlink() and entry.is_file()
        )
    except (FileNotFoundError, NotADirectoryError):
        return ()


def select_from_paths(paths: LifecyclePaths) -> Selection:
    """Read the two selectable lifecycle directories and apply ``select``."""
    return select(_directory_names(paths.wip), _directory_names(paths.backlog))
