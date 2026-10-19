from __future__ import annotations

import os
import stat
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_NAME = "ovcaq.toml"
RUNTIME_PARTS = ("docs", "dev", "project-management", "ovcaq")


class ProjectPathError(OSError):
    """Raised when a derived project path can escape its resolved root."""


def _derived_runtime_path(root: Path) -> Path:
    return root.joinpath(*RUNTIME_PARTS)


def _reject_symlink_components(root: Path, derived: Path) -> None:
    current = root
    for component in derived.relative_to(root).parts:
        current /= component
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError as error:
            raise ProjectPathError(
                f"cannot inspect derived runtime path {current}: {error}"
            ) from error
        if stat.S_ISLNK(mode):
            raise ProjectPathError(
                f"derived runtime path contains a symlink: {current}"
            )


def _validated_runtime_path(
    root: Path,
    configured_root: Path | None = None,
    *,
    trusted_root: bool = False,
) -> Path:
    resolved_root = root if trusted_root else _checked_path(root)
    derived = (
        _derived_runtime_path(resolved_root)
        if configured_root is None
        else configured_root
    )
    if not derived.is_absolute():
        derived = resolved_root / derived
    try:
        derived.relative_to(resolved_root)
    except ValueError as error:
        raise ProjectPathError(
            f"derived runtime path escapes project root: {derived}"
        ) from error
    _reject_symlink_components(resolved_root, derived)
    try:
        derived.resolve().relative_to(resolved_root)
    except ValueError as error:
        raise ProjectPathError(
            f"derived runtime path escapes project root {resolved_root}: {derived}"
        ) from error
    return derived.resolve()


def _checked_path(path: Path) -> Path:
    """Normalize a path only after rejecting existing symlink components."""
    absolute = path.expanduser().absolute()
    _reject_symlink_components(Path(absolute.anchor), absolute)
    return absolute.resolve()


def _trusted_path(path: Path) -> Path:
    """Resolve an explicitly selected anchor, including any symlink aliases."""
    return path.expanduser().resolve()


def _is_runtime_marker(root: Path) -> bool:
    try:
        return runtime_directory(root).is_dir()
    except ProjectPathError:
        return False


def discover_project_root(
    explicit_root: Path | None = None,
    *,
    start: Path | None = None,
) -> Path:
    if explicit_root is not None:
        return _trusted_path(explicit_root)

    current = _trusted_path(Path.cwd() if start is None else start)
    candidates = (current, *current.parents)
    for candidate in candidates:
        if (candidate / CONFIG_NAME).is_file() or _is_runtime_marker(candidate):
            return candidate
    for candidate in candidates:
        if (candidate / ".git").exists():
            return candidate
    return current


def runtime_directory(root: Path, configured_root: Path | None = None) -> Path:
    return _validated_runtime_path(root, configured_root)


def ensure_runtime_directory(root: Path) -> Path:
    resolved_root = root.expanduser().resolve()
    resolved_root.mkdir(parents=True, exist_ok=True)
    current = resolved_root
    for index, component in enumerate(RUNTIME_PARTS):
        candidate = current / component
        _reject_symlink_components(resolved_root, candidate)
        try:
            mode = 0o700 if index == len(RUNTIME_PARTS) - 1 else 0o777
            candidate.mkdir(mode=mode)
        except FileExistsError:
            if not candidate.is_dir():
                raise ProjectPathError(
                    f"derived runtime path is not a directory: {candidate}"
                ) from None
        _reject_symlink_components(resolved_root, candidate)
        current = candidate

    runtime = _validated_runtime_path(resolved_root)
    descriptor = -1
    try:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(runtime, flags)
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise ProjectPathError(f"runtime path is not a directory: {runtime}")
        if runtime.is_symlink():
            raise ProjectPathError(f"runtime path is a symlink: {runtime}")
        os.fchmod(descriptor, 0o700)
    except OSError as error:
        if isinstance(error, ProjectPathError):
            raise
        raise ProjectPathError(
            f"cannot secure runtime directory {runtime}: {error}"
        ) from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    return runtime


def state_path(root: Path) -> Path:
    return runtime_directory(root) / "state.json"


@dataclass(frozen=True)
class RuntimePaths:
    project_root: Path
    runtime_root: Path
    state_file: Path
    run_lock: Path
    run_metadata: Path
    events: Path
    metrics: Path
    sessions: Path
    reports: Path
    fleet_root: Path
    fleet_lock: Path
    retention_lock: Path
    _identities: tuple[tuple[Path, int, int], ...] = field(
        default=(), init=False, repr=False
    )


def _directory_identity(path: Path) -> tuple[int, int]:
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode):
        raise ProjectPathError(f"path is not a directory: {path}")
    return info.st_dev, info.st_ino


def _identity_snapshot(*directories: Path) -> tuple[tuple[Path, int, int], ...]:
    identities: dict[Path, tuple[int, int]] = {}
    for directory in directories:
        for path in (*reversed(directory.parents), directory):
            if path in identities:
                continue
            try:
                identities[path] = _directory_identity(path)
            except FileNotFoundError:
                continue
            except OSError as error:
                raise ProjectPathError(
                    f"cannot inspect directory {path}: {error}"
                ) from error
    return tuple((path, *identity) for path, identity in identities.items())


def resolve_runtime_paths(
    root: Path,
    *,
    runtime_root: Path | None = None,
    external_state_root: Path | None = None,
    xdg_state_home: Path | None = None,
) -> RuntimePaths:
    """Resolve runtime artifacts without creating directories or records."""
    if runtime_root is not None and external_state_root is not None:
        raise ProjectPathError("internal and external runtime roots conflict")
    project = _trusted_path(root)
    if external_state_root is None:
        runtime = _validated_runtime_path(project, runtime_root, trusted_root=True)
    else:
        runtime = _trusted_path(project / external_state_root)
    if xdg_state_home is None:
        default = Path.home() / ".local/state"
        xdg_state_home = Path(os.environ.get("XDG_STATE_HOME", default))
    state_home = _trusted_path(xdg_state_home)
    fleet = _checked_path(state_home / "ovcaq/runs")
    snapshot = _identity_snapshot(
        project, runtime / "sessions", runtime / "reports", fleet
    )
    paths = RuntimePaths(
        project_root=project,
        runtime_root=runtime,
        state_file=runtime / "state.json",
        run_lock=runtime / "run.lock",
        run_metadata=runtime / "run.json",
        events=runtime / "events.jsonl",
        metrics=runtime / "metrics.jsonl",
        sessions=runtime / "sessions",
        reports=runtime / "reports",
        fleet_root=fleet,
        fleet_lock=fleet / "fleet.lock",
        retention_lock=runtime / "retention.lock",
    )
    object.__setattr__(paths, "_identities", snapshot)
    return paths


def ensure_runtime_layout(paths: RuntimePaths) -> RuntimePaths:
    """Create private directories using checked, no-follow directory handles."""
    expected = {path: (device, inode) for path, device, inode in paths._identities}
    private = {paths.runtime_root, paths.sessions, paths.reports, paths.fleet_root}
    descriptors: dict[Path, int] = {}
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        # Check the entire snapshot before creating any directories.
        for path, identity in expected.items():
            if _directory_identity(path) != identity:
                raise ProjectPathError(f"directory changed since resolution: {path}")
        for target in (
            paths.project_root,
            paths.runtime_root,
            paths.sessions,
            paths.reports,
            paths.fleet_root,
        ):
            for path in (*reversed(target.parents), target):
                if path in descriptors:
                    descriptor = descriptors[path]
                else:
                    parent_fd = descriptors.get(path.parent)
                    name = path.name if parent_fd is not None else str(path)
                    try:
                        descriptor = os.open(name, flags, dir_fd=parent_fd)
                    except FileNotFoundError:
                        os.mkdir(
                            name,
                            0o700 if path in private else 0o777,
                            dir_fd=parent_fd,
                        )
                        descriptor = os.open(name, flags, dir_fd=parent_fd)
                    descriptors[path] = descriptor
                opened = os.fstat(descriptor)
                identity = opened.st_dev, opened.st_ino
                if (
                    not stat.S_ISDIR(opened.st_mode)
                    or identity != _directory_identity(path)
                    or (path in expected and identity != expected[path])
                ):
                    raise ProjectPathError(f"directory changed while opening: {path}")
                if path in private:
                    os.fchmod(descriptor, 0o700)
    except OSError as error:
        raise ProjectPathError(f"cannot create runtime layout: {error}") from error
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
    return paths
