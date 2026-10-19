from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from ovcaq.config import ConfigurationError, RuntimeSettings, runtime_settings
from ovcaq.paths import (
    ProjectPathError,
    RuntimePaths,
    discover_project_root,
    ensure_runtime_layout,
    resolve_runtime_paths,
)


@pytest.fixture
def config_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    base = tmp_path.resolve()
    monkeypatch.setenv("HOME", str(base / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(base / "user-config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(base / "user-state"))
    root = base / "project"
    root.mkdir()
    return root


def test_default_paths_name_every_runtime_artifact_without_creating_it(
    config_root: Path,
) -> None:
    root = discover_project_root(config_root)
    paths = resolve_runtime_paths(root)
    runtime = root / "docs/dev/project-management/ovcaq"
    fleet = root.parent / "user-state/ovcaq/runs"

    assert isinstance(paths, RuntimePaths)
    assert root == config_root
    assert paths.project_root == root
    assert paths.runtime_root == runtime
    assert paths.state_file == runtime / "state.json"
    assert paths.run_lock == runtime / "run.lock"
    assert paths.run_metadata == runtime / "run.json"
    assert paths.events == runtime / "events.jsonl"
    assert paths.metrics == runtime / "metrics.jsonl"
    assert paths.sessions == runtime / "sessions"
    assert paths.reports == runtime / "reports"
    assert paths.retention_lock == runtime / "retention.lock"
    assert paths.fleet_root == fleet
    assert paths.fleet_lock == fleet / "fleet.lock"
    assert list(root.iterdir()) == []
    assert not fleet.exists()


@pytest.mark.parametrize("marker", ("ovcaq.toml", "docs/dev/project-management/ovcaq"))
def test_discovery_from_nested_start_selects_the_nearest_project_marker(
    config_root: Path, monkeypatch: pytest.MonkeyPatch, marker: str
) -> None:
    (config_root / ".git").mkdir()
    (config_root / "ovcaq.toml").write_text("version = 1\n")
    nested = config_root / "nested-project"
    start = nested / "src/package"
    start.mkdir(parents=True)
    project_marker = nested / marker
    if marker == "ovcaq.toml":
        project_marker.write_text("version = 1\n")
    else:
        project_marker.mkdir(parents=True)
    monkeypatch.chdir(config_root.parent)

    assert discover_project_root(start=start) == nested


def test_discovery_from_nested_start_uses_git_when_project_markers_are_absent(
    config_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (config_root / ".git").mkdir()
    start = config_root / "src/package"
    start.mkdir(parents=True)
    monkeypatch.chdir(config_root.parent)

    assert discover_project_root(start=start) == config_root


def test_xdg_state_injection_overrides_environment_and_home_is_the_fallback(
    config_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    injected = config_root.parent / "injected-state"
    assert (
        resolve_runtime_paths(config_root, xdg_state_home=injected).fleet_root
        == injected / "ovcaq/runs"
    )

    monkeypatch.delenv("XDG_STATE_HOME")
    assert resolve_runtime_paths(config_root).fleet_root == (
        config_root.parent / "home/.local/state/ovcaq/runs"
    )


@pytest.mark.parametrize("absolute", (False, True))
def test_internal_roots_accept_contained_paths_and_reject_escape(
    config_root: Path, absolute: bool
) -> None:
    internal = config_root / "private" if absolute else Path("private")
    escape = config_root.parent / "outside" if absolute else Path("../outside")

    assert (
        resolve_runtime_paths(config_root, runtime_root=internal).runtime_root
        == config_root / "private"
    )
    with pytest.raises(ProjectPathError):
        resolve_runtime_paths(config_root, runtime_root=escape)
    assert list(config_root.iterdir()) == []
    assert not (config_root.parent / "outside").exists()


def test_external_root_can_escape_but_cannot_coexist_with_internal_root(
    config_root: Path,
) -> None:
    external = config_root.parent / "outside"
    assert (
        resolve_runtime_paths(config_root, external_state_root=external).runtime_root
        == external
    )
    with pytest.raises(ProjectPathError):
        resolve_runtime_paths(
            config_root, runtime_root=Path("private"), external_state_root=external
        )
    assert not external.exists()


def test_layout_creates_private_directories_without_creating_record_files(
    config_root: Path,
) -> None:
    paths = resolve_runtime_paths(config_root)
    assert ensure_runtime_layout(paths) == paths
    assert ensure_runtime_layout(paths) == paths
    assert stat.S_IMODE(paths.runtime_root.stat().st_mode) == 0o700
    assert stat.S_IMODE(paths.sessions.stat().st_mode) == 0o700
    assert stat.S_IMODE(paths.reports.stat().st_mode) == 0o700
    assert stat.S_IMODE(paths.fleet_root.stat().st_mode) == 0o700
    assert set(paths.runtime_root.iterdir()) == {paths.sessions, paths.reports}
    assert list(paths.fleet_root.iterdir()) == []


@pytest.mark.parametrize("component", ("runtime", "sessions", "reports", "fleet"))
@pytest.mark.parametrize("kind", ("symlink", "file"))
def test_layout_refuses_symlink_and_file_components_without_touching_targets(
    config_root: Path, component: str, kind: str
) -> None:
    paths = resolve_runtime_paths(config_root)
    target = {
        "runtime": paths.runtime_root,
        "sessions": paths.sessions,
        "reports": paths.reports,
        "fleet": paths.fleet_root,
    }[component]
    target.parent.mkdir(parents=True, exist_ok=True)
    outside = config_root.parent / "outside"
    outside.mkdir()
    if kind == "symlink":
        target.symlink_to(outside, target_is_directory=True)
    else:
        target.write_text("preserve me")

    with pytest.raises(ProjectPathError):
        ensure_runtime_layout(paths)
    assert list(outside.iterdir()) == []
    if kind == "file":
        assert target.read_text() == "preserve me"
    else:
        assert target.is_symlink()


@pytest.mark.parametrize("component_name", ("amber", "quartz-17"))
def test_internal_resolution_refuses_existing_symlink_descendants(
    config_root: Path, component_name: str
) -> None:
    outside = config_root.parent / "outside"
    outside.mkdir()
    link = config_root / component_name
    link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ProjectPathError):
        resolve_runtime_paths(config_root, runtime_root=link / "nested")
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("location", ("project", "external", "fleet"))
def test_resolution_trusts_caller_selected_symlink_alias_anchors(
    config_root: Path, location: str
) -> None:
    resolved_parent = config_root.parent / "resolved"
    resolved_parent.mkdir()
    alias = config_root.parent / "alias"
    alias.symlink_to(resolved_parent, target_is_directory=True)

    if location == "project":
        project = resolved_parent / "project"
        project.mkdir()
        assert discover_project_root(alias / "project") == project
    elif location == "external":
        assert (
            resolve_runtime_paths(
                config_root, external_state_root=alias / "external"
            ).runtime_root
            == resolved_parent / "external"
        )
    else:
        assert (
            resolve_runtime_paths(
                config_root, xdg_state_home=alias / "state"
            ).fleet_root
            == resolved_parent / "state/ovcaq/runs"
        )

    assert list(resolved_parent.iterdir()) == (
        [] if location != "project" else [project]
    )


@pytest.mark.parametrize("component", ("project", "runtime", "fleet"))
def test_layout_rejects_directory_inode_replacement_after_resolution(
    config_root: Path, component: str
) -> None:
    runtime = config_root / "private"
    fleet = config_root.parent / "user-state/ovcaq/runs"
    runtime.mkdir()
    fleet.mkdir(parents=True)
    paths = resolve_runtime_paths(config_root, runtime_root=runtime)
    target = {"project": config_root, "runtime": runtime, "fleet": fleet}[component]
    saved = target.with_name(target.name + "-original")
    target.rename(saved)
    target.mkdir()

    with pytest.raises(ProjectPathError):
        ensure_runtime_layout(paths)
    assert list(target.iterdir()) == []


def test_layout_rejects_directory_inode_replacement_during_open_validation(
    config_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = config_root / "private"
    runtime.mkdir()
    paths = resolve_runtime_paths(config_root, runtime_root=runtime)
    saved = config_root / "original-private"
    original_identity = runtime.stat()
    real_open = os.open

    def replace_after_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        descriptor = real_open(path, flags, mode, dir_fd=dir_fd)
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) == (
            original_identity.st_dev,
            original_identity.st_ino,
        ) and not saved.exists():
            runtime.rename(saved)
            runtime.mkdir()
        return descriptor

    monkeypatch.setattr(os, "open", replace_after_open)
    with pytest.raises(ProjectPathError):
        ensure_runtime_layout(paths)
    assert saved.is_dir()
    assert list(runtime.iterdir()) == []
    assert list(saved.iterdir()) == []


def test_runtime_settings_defaults_ignore_non_xdg_environment_configuration(
    config_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OVCAQ_TERM_GRACE_SECONDS", "250")
    monkeypatch.setenv("OVCAQ_MAX_SESSION_BYTES", "1")
    monkeypatch.setenv("OVCAQ_MAX_RETAINED_BYTES", "2")
    monkeypatch.setenv("OVCAQ_MIN_FREE_BYTES", "3")
    monkeypatch.setenv("OVCAQ_RUNTIME_ROOT", "ignored")

    settings = runtime_settings(config_root)
    assert isinstance(settings, RuntimeSettings)
    assert settings.paths == resolve_runtime_paths(config_root)
    assert settings.term_grace_seconds == 10
    assert settings.max_session_bytes == 16 * 1024**3
    assert settings.max_retained_bytes == 128 * 1024**3
    assert settings.min_free_bytes == 1024**3
    assert list(config_root.iterdir()) == []


def test_settings_merge_each_key_with_explicit_project_user_default_precedence(
    config_root: Path,
) -> None:
    user = config_root.parent / "user-config/ovcaq/config.toml"
    user.parent.mkdir(parents=True)
    user.write_text(
        'version = 1\n[workflow]\nruntime_root = "user-runtime"\n'
        "[runtime]\nterm_grace_seconds = 20\nmax_session_bytes = 100\n"
        "max_retained_bytes = 200\n"
    )
    project = config_root / "ovcaq.toml"
    project.write_text(
        'version = 1\n[workflow]\nruntime_root = "project-runtime"\n'
        "[runtime]\nterm_grace_seconds = 30\nmax_session_bytes = 150\n"
    )

    merged = runtime_settings(config_root)
    assert merged.paths.runtime_root == config_root / "project-runtime"
    assert merged.term_grace_seconds == 30
    assert merged.max_session_bytes == 150
    assert merged.max_retained_bytes == 200
    assert merged.min_free_bytes == 1024**3

    explicit = runtime_settings(
        config_root,
        runtime_root=Path("explicit-runtime"),
        term_grace_seconds=0,
        max_session_bytes=0,
        max_retained_bytes=0,
        min_free_bytes=0,
    )
    assert explicit.paths.runtime_root == config_root / "explicit-runtime"
    assert explicit.term_grace_seconds == 0
    assert explicit.max_session_bytes == 0
    assert explicit.max_retained_bytes == 0
    assert explicit.min_free_bytes == 0
    assert list(config_root.iterdir()) == [project]


def test_xdg_config_injection_and_home_fallback_select_user_settings(
    config_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    injected = config_root.parent / "injected-config"
    user = injected / "ovcaq/config.toml"
    user.parent.mkdir(parents=True)
    user.write_text("[runtime]\nterm_grace_seconds = 42\n")
    state = config_root.parent / "injected-state"
    settings = runtime_settings(
        config_root, xdg_config_home=injected, xdg_state_home=state
    )
    assert settings.term_grace_seconds == 42
    assert settings.paths.fleet_root == state / "ovcaq/runs"

    fallback = config_root.parent / "home/.config/ovcaq/config.toml"
    fallback.parent.mkdir(parents=True)
    fallback.write_text("[runtime]\nterm_grace_seconds = 43\n")
    monkeypatch.delenv("XDG_CONFIG_HOME")
    assert runtime_settings(config_root).term_grace_seconds == 43


@pytest.mark.parametrize("config_present", (False, True))
def test_symlinked_xdg_config_home_is_a_trusted_selected_anchor(
    config_root: Path, config_present: bool
) -> None:
    resolved = config_root.parent / "resolved-config"
    resolved.mkdir()
    alias = config_root.parent / "config-alias"
    alias.symlink_to(resolved, target_is_directory=True)
    if config_present:
        config = resolved / "ovcaq/config.toml"
        config.parent.mkdir()
        config.write_text("[runtime]\nterm_grace_seconds = 42\n")

    settings = runtime_settings(config_root, xdg_config_home=alias)

    assert settings.term_grace_seconds == (42 if config_present else 10)


@pytest.mark.parametrize(
    "key, value",
    (
        ("term_grace_seconds", True),
        ("term_grace_seconds", float("nan")),
        ("term_grace_seconds", float("inf")),
        ("term_grace_seconds", float("-inf")),
        ("term_grace_seconds", -0.1),
        ("term_grace_seconds", 300.1),
        ("max_session_bytes", True),
        ("max_session_bytes", -1),
        ("max_session_bytes", 0.5),
        ("max_session_bytes", float("inf")),
        ("max_retained_bytes", False),
        ("max_retained_bytes", -1),
        ("max_retained_bytes", 0.5),
        ("max_retained_bytes", float("nan")),
        ("min_free_bytes", True),
        ("min_free_bytes", -1),
        ("min_free_bytes", 0.5),
        ("min_free_bytes", float("-inf")),
    ),
)
def test_explicit_invalid_limits_are_rejected_without_filesystem_effects(
    config_root: Path, key: str, value: float
) -> None:
    with pytest.raises(ConfigurationError):
        runtime_settings(config_root, **{key: value})
    assert list(config_root.iterdir()) == []


@pytest.mark.parametrize("grace", (0, 0.5, 300))
def test_grace_accepts_fractional_seconds_and_both_inclusive_boundaries(
    config_root: Path, grace: float
) -> None:
    assert (
        runtime_settings(config_root, term_grace_seconds=grace).term_grace_seconds
        == grace
    )


@pytest.mark.parametrize(
    "declaration",
    (
        "version = 0",
        "version = 2",
        "version = true",
        'version = "1"',
        "version = 1.0",
        "[runtime]\nterm_grace_seconds = true",
        "[runtime]\nterm_grace_seconds = nan",
        "[runtime]\nterm_grace_seconds = inf",
        "[runtime]\nterm_grace_seconds = -1",
        "[runtime]\nterm_grace_seconds = 301",
        "[runtime]\nmax_session_bytes = -1",
        "[runtime]\nmax_session_bytes = 0.5",
        "[runtime]\nmax_retained_bytes = false",
        "[runtime]\nmax_retained_bytes = 0.5",
        "[runtime]\nmin_free_bytes = -inf",
        "[runtime]\nmin_free_bytes = 0.5",
        '[workflow]\nruntime_root = ""',
    ),
)
def test_invalid_toml_runtime_settings_are_domain_errors_without_effects(
    config_root: Path, declaration: str
) -> None:
    config = config_root / "ovcaq.toml"
    config.write_text(declaration)
    with pytest.raises(ConfigurationError):
        runtime_settings(config_root)
    assert list(config_root.iterdir()) == [config]


def test_external_root_configuration_is_applied_and_conflicting_roots_rejected(
    config_root: Path,
) -> None:
    config = config_root / "ovcaq.toml"
    external = config_root.parent / "external"
    config.write_text(f'[runtime]\nexternal_state_root = "{external}"\n')
    assert runtime_settings(config_root).paths.runtime_root == external
    config.write_text(
        '[workflow]\nruntime_root = "private"\n'
        f'[runtime]\nexternal_state_root = "{external}"\n'
    )
    with pytest.raises((ConfigurationError, ProjectPathError)):
        runtime_settings(config_root)
    assert not external.exists()


@pytest.mark.parametrize("target_name", ("amber.toml", "quartz-17.data"))
@pytest.mark.parametrize("location", ("project-file", "user-file"))
def test_configuration_refuses_symlink_files_with_arbitrary_targets(
    config_root: Path, location: str, target_name: str
) -> None:
    outside = config_root.parent / "outside"
    outside.mkdir()
    source = outside / target_name
    source.write_text("[runtime]\nterm_grace_seconds = 50\n")
    if location == "project-file":
        (config_root / "ovcaq.toml").symlink_to(source)
    else:
        user = config_root.parent / "user-config/ovcaq"
        user.mkdir(parents=True)
        (user / "config.toml").symlink_to(source)

    with pytest.raises((ConfigurationError, ProjectPathError)):
        runtime_settings(config_root)
    assert list(outside.iterdir()) == [source]
    assert source.read_text() == "[runtime]\nterm_grace_seconds = 50\n"


def test_configuration_refuses_symlink_ancestors_below_xdg_anchor(
    config_root: Path,
) -> None:
    outside = config_root.parent / "outside"
    outside.mkdir()
    source = outside / "config.toml"
    source.write_text("[runtime]\nterm_grace_seconds = 50\n")
    user = config_root.parent / "user-config"
    user.mkdir()
    (user / "ovcaq").symlink_to(outside, target_is_directory=True)

    with pytest.raises((ConfigurationError, ProjectPathError)):
        runtime_settings(config_root)
    assert list(outside.iterdir()) == [source]
    assert source.read_text() == "[runtime]\nterm_grace_seconds = 50\n"
