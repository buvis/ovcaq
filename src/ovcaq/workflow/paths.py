"""Configured PRD lifecycle paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeGuard


class WorkflowIdentifierError(ValueError):
    """Raised when a workflow identifier is unsafe for a path or heading."""


def is_safe_identifier(value: object) -> TypeGuard[str]:
    """Return whether ``value`` is one printable, path-safe component."""
    return (
        isinstance(value, str)
        and bool(value)
        and value not in {".", ".."}
        and all(character.isprintable() for character in value)
        and "/" not in value
        and "\\" not in value
        and Path(value).name == value
    )


def require_safe_identifier(value: object, label: str) -> str:
    """Require a printable identifier usable as one path component."""
    if not is_safe_identifier(value):
        raise WorkflowIdentifierError(
            f"{label} must be a nonempty printable path-safe component: {value!r}"
        )
    return value


@dataclass(frozen=True)
class LifecyclePaths:
    """The fixed lifecycle directories under one configured PRD root."""

    root: Path
    backlog: Path
    wip: Path
    hold: Path
    done: Path


def resolve_lifecycle_paths(
    repo_root: Path,
    configured_root: Path,
) -> LifecyclePaths:
    """Resolve a configured PRD root without coupling it to runtime storage."""
    root = (
        configured_root
        if configured_root.is_absolute()
        else repo_root / configured_root
    )
    root = root.resolve()
    return LifecyclePaths(
        root=root,
        backlog=root / "backlog",
        wip=root / "wip",
        hold=root / "hold",
        done=root / "done",
    )
