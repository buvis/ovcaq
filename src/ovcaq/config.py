from __future__ import annotations

import math
import os
import re
import stat
import tomllib
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, cast

from ovcaq.paths import (
    CONFIG_NAME,
    RuntimePaths,
    _checked_path,
    _trusted_path,
    resolve_runtime_paths,
    runtime_directory,
)
from ovcaq.workflow_client import ControllerConfig

if TYPE_CHECKING:
    from ovcaq.runtime.decision import SupervisorPolicy

Effort = Literal["low", "medium", "high", "xhigh"]
_PHASES = frozenset({"build", "review", "done"})

# Neutral tier keys every driver maps to its own models.
DEFAULT_PHASE_TIERS = {"build": "standard", "review": "deep", "done": "standard"}
NEUTRAL_TIERS = frozenset(DEFAULT_PHASE_TIERS.values())


class ConfigurationError(ValueError):
    """Raised when a workflow configuration input has an invalid shape."""


def ensure_project_config(root: Path) -> Path:
    path = root / CONFIG_NAME
    try:
        path.touch(exist_ok=False)
    except FileExistsError:
        if not path.is_file():
            raise
    return path


@dataclass(frozen=True)
class WorkflowSettings:
    prd_root: Path
    runtime_root: Path
    state_file: Path
    available_tiers: frozenset[str]
    controller_argv: tuple[str, ...] | None = None
    contract_bundle: Path | None = None
    actor_file: Path | None = None


_CREDENTIAL_KEY = re.compile(
    r"api[_-]?key|token|secret|password|authorization|cookie|credential",
    re.IGNORECASE,
)
_CREDENTIAL_VALUE = re.compile(
    r"\bbearer\s+\S+|\bsk-[A-Za-z0-9_-]{20,}\b"
    r"|\b(?:api[_-]?key|token|secret|password|authorization|cookie|credential)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


def _check_credentials(value: str, *, key: bool = False) -> None:
    pattern = _CREDENTIAL_KEY if key else _CREDENTIAL_VALUE
    if pattern.search(value):
        raise ConfigurationError("agent settings must not contain credentials")


def _freeze_options(value: object) -> object:
    if isinstance(value, Mapping):
        frozen: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ConfigurationError("agent option keys must be strings")
            _check_credentials(key, key=True)
            frozen[key] = _freeze_options(item)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_options(item) for item in value)
    if isinstance(value, str):
        _check_credentials(value)
        return value
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise ConfigurationError("agent options must contain finite JSON values")


@dataclass(frozen=True, slots=True)
class AgentSettings:
    name: str
    command: tuple[str, ...]
    tiers: Mapping[str, str]
    environment: Mapping[str, str]
    options: Mapping[str, object]
    prompts: Mapping[str, str] = dataclass_field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ConfigurationError("agent name must be nonempty text")
        if not self.command or any(
            not isinstance(part, str) or not part for part in self.command
        ):
            raise ConfigurationError("agent command must be nonempty strings")
        tiers = dict(self.tiers)
        environment = dict(self.environment)
        for field, values in (("tiers", tiers), ("environment", environment)):
            for key, value in values.items():
                if (
                    not isinstance(key, str)
                    or not key
                    or not isinstance(value, str)
                    or not value
                ):
                    raise ConfigurationError(
                        f"agent {field} must contain nonempty string keys and values"
                    )
                if field == "environment":
                    _check_credentials(key, key=True)
                    _check_credentials(value)
        object.__setattr__(self, "command", tuple(self.command))
        object.__setattr__(self, "tiers", MappingProxyType(tiers))
        object.__setattr__(self, "environment", MappingProxyType(environment))
        object.__setattr__(self, "options", _freeze_options(self.options))
        prompts = dict(self.prompts)
        for phase, prompt in prompts.items():
            if phase not in _PHASES:
                raise ConfigurationError(f"Unknown prompt phase: {phase}")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ConfigurationError("agent prompts must be nonblank strings")
            _check_credentials(prompt)
        object.__setattr__(self, "prompts", MappingProxyType(prompts))


def _read_config(path: Path) -> dict[str, object]:
    try:
        path = _checked_path(path)
        descriptor = os.open(
            path,
            os.O_RDONLY
            | os.O_NONBLOCK
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
        )
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ConfigurationError(f"configuration is not a regular file: {path}")
            config = tomllib.load(stream)
            version = config.get("version", 1)
            if type(version) is not int or version != 1:
                raise ConfigurationError("configuration version must be integer 1")
            return config
    except FileNotFoundError:
        return {}
    except RecursionError as error:
        raise ConfigurationError(
            f"configuration nesting exceeds safe decode limit: {path}"
        ) from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigurationError(f"invalid configuration {path}: {error}") from error
    except OSError as error:
        raise ConfigurationError(
            f"cannot read configuration {path}: {error}"
        ) from error


def _table(config: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = config.get(key, {})
    if not isinstance(value, dict):
        raise ConfigurationError(f"configuration {key} must be a table")
    return value


def _configured_path(root: Path, value: object, label: str) -> Path:
    if not isinstance(value, (str, Path)) or not str(value):
        raise ConfigurationError(f"configuration {label} must be a nonempty path")
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def agent_settings(root: Path, *, name: str | None = None) -> AgentSettings:
    """Load the selected agent's argv and merge its declarative settings."""
    root = _trusted_path(root)
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    config_home = _trusted_path(config_home)
    user = _read_config(config_home / "ovcaq/config.toml")
    project = _read_config(root / CONFIG_NAME)
    active = name if name is not None else project.get("agent", user.get("agent"))
    if not isinstance(active, str) or not active:
        raise ConfigurationError("configuration agent must be a nonempty name")
    user_agent = _table(_table(user, "agents"), active)
    project_agent = _table(_table(project, "agents"), active)
    command = project_agent.get("command", user_agent.get("command", [active]))
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(part, str) or not part for part in command)
    ):
        raise ConfigurationError("agent command must be a nonempty array of strings")
    merged = {
        field: {**_table(user_agent, field), **_table(project_agent, field)}
        for field in ("tiers", "environment", "options", "prompts")
    }
    return AgentSettings(
        name=active,
        command=tuple(command),
        tiers=cast("dict[str, str]", merged["tiers"]),
        environment=cast("dict[str, str]", merged["environment"]),
        options=merged["options"],
        prompts=cast("dict[str, str]", merged["prompts"]),
    )


def _workflow_tables(
    root: Path,
) -> tuple[Mapping[str, object], Mapping[str, object], dict[str, object]]:
    """Read the user and project TOML once and merge their [workflow] tables."""
    config_home = _trusted_path(
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    )
    user = _read_config(config_home / "ovcaq/config.toml")
    project = _read_config(root / CONFIG_NAME)
    return user, project, {**_table(user, "workflow"), **_table(project, "workflow")}


def _controller_argv(workflow: Mapping[str, object]) -> tuple[str, ...] | None:
    argv = workflow.get("controller_argv")
    if argv is None:
        return None
    if (
        not isinstance(argv, list)
        or not argv
        or any(not isinstance(part, str) or not part for part in argv)
    ):
        raise ConfigurationError("controller_argv must be a nonempty array of strings")
    return tuple(argv)


def _controller_inputs(
    root: Path, workflow: Mapping[str, object]
) -> tuple[tuple[str, ...] | None, Path | None, Path | None]:
    """Validate the controller keys' shapes without touching the filesystem."""
    argv = _controller_argv(workflow)
    if argv is None:
        return None, None, None
    bundle = workflow.get("contract_bundle")
    actor = workflow.get("actor_file")
    return (
        argv,
        None if bundle is None else _configured_path(root, bundle, "contract_bundle"),
        None if actor is None else _configured_path(root, actor, "actor_file"),
    )


def _active_tiers(
    root: Path, user: Mapping[str, object], project: Mapping[str, object]
) -> dict[str, str]:
    active = project.get("agent", user.get("agent"))
    if active is None:
        return {}
    if not isinstance(active, str) or not active:
        raise ConfigurationError("configuration agent must be a nonempty name")
    return dict(agent_settings(root, name=active).tiers)


def workflow_settings(
    root: Path,
    *,
    prd_root: Path | None = None,
    runtime_root: Path | None = None,
    state_file: Path | None = None,
    available_tiers: Collection[str] | None = None,
) -> WorkflowSettings:
    """Resolve only workflow inputs; model values and runtime policy stay opaque."""
    root = _trusted_path(root)
    user, project, workflow = _workflow_tables(root)
    prds = _configured_path(
        root,
        prd_root or workflow.get("prd_root", "docs/dev/project-management/prds"),
        "prd_root",
    )
    prds = runtime_directory(root, prds)
    runtime = _configured_path(
        root,
        runtime_root
        or workflow.get("runtime_root", "docs/dev/project-management/ovcaq"),
        "runtime_root",
    )
    runtime = runtime_directory(root, runtime)
    state = _configured_path(
        root,
        state_file
        if state_file is not None
        else workflow.get("state_file", runtime / "state.json"),
        "state_file",
    )
    state = runtime_directory(root, state)
    tiers = _active_tiers(root, user, project)
    argv, bundle, actor = _controller_inputs(root, workflow)
    return WorkflowSettings(
        prds,
        runtime,
        state,
        frozenset(
            NEUTRAL_TIERS.union(tiers) if available_tiers is None else available_tiers
        ),
        argv,
        bundle,
        actor,
    )


def controller_settings(root: Path) -> ControllerConfig | None:
    """Build the controller client config, or None when no argv is declared."""
    root = _trusted_path(root)
    _, _, workflow = _workflow_tables(root)
    argv = _controller_argv(workflow)
    if argv is None:
        return None
    bundle = _configured_path(root, workflow.get("contract_bundle"), "contract_bundle")
    actor = workflow.get("actor_file")
    digest = workflow.get("contract_bundle_sha256")
    if digest is not None and not isinstance(digest, str):
        raise ConfigurationError("contract_bundle_sha256 must be a string")
    try:
        return ControllerConfig(
            argv=argv,
            contract_bundle=bundle,
            actor_file=(
                None if actor is None else _configured_path(root, actor, "actor_file")
            ),
            project_root=root,
            bundle_digest=digest,
        )
    except (TypeError, ValueError) as error:
        raise ConfigurationError(
            f"invalid controller configuration: {error}"
        ) from error


@dataclass(frozen=True)
class RuntimeSettings:
    paths: RuntimePaths
    term_grace_seconds: float
    max_session_bytes: int
    max_retained_bytes: int
    min_free_bytes: int


def _runtime_path(
    root: Path, explicit: Path | None, config: Mapping[str, object], key: str
) -> Path | None:
    value = explicit if explicit is not None else config.get(key)
    return None if value is None else _configured_path(root, value, key)


def _runtime_limits(
    runtime: Mapping[str, object],
    term_grace_seconds: float | None,
    max_session_bytes: int | None,
    max_retained_bytes: int | None,
    min_free_bytes: int | None,
) -> tuple[float, int, int, int]:
    grace = (
        runtime.get("term_grace_seconds", 10)
        if term_grace_seconds is None
        else term_grace_seconds
    )
    if (
        isinstance(grace, bool)
        or not isinstance(grace, (int, float))
        or not 0 <= grace <= 300
    ):
        message = "term_grace_seconds must be finite and between 0 and 300"
        raise ConfigurationError(message)
    limits: list[int] = []
    for key, explicit, default in (
        ("max_session_bytes", max_session_bytes, 16 * 1024**3),
        ("max_retained_bytes", max_retained_bytes, 128 * 1024**3),
        ("min_free_bytes", min_free_bytes, 1024**3),
    ):
        value = explicit if explicit is not None else runtime.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ConfigurationError(f"{key} must be a nonnegative integer")
        limits.append(value)
    return grace, limits[0], limits[1], limits[2]


def runtime_settings(
    root: Path,
    *,
    runtime_root: Path | None = None,
    external_state_root: Path | None = None,
    term_grace_seconds: float | None = None,
    max_session_bytes: int | None = None,
    max_retained_bytes: int | None = None,
    min_free_bytes: int | None = None,
    xdg_config_home: Path | None = None,
    xdg_state_home: Path | None = None,
) -> RuntimeSettings:
    """Merge explicit, project, user, and default settings in precedence order."""
    root = _trusted_path(root)
    config_home = xdg_config_home
    if config_home is None:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    config_home = _trusted_path(config_home)
    user = _read_config(config_home / "ovcaq/config.toml")
    project = _read_config(root / CONFIG_NAME)
    workflow = {**_table(user, "workflow"), **_table(project, "workflow")}
    runtime = {**_table(user, "runtime"), **_table(project, "runtime")}
    limits = _runtime_limits(
        runtime,
        term_grace_seconds,
        max_session_bytes,
        max_retained_bytes,
        min_free_bytes,
    )
    paths = resolve_runtime_paths(
        root,
        runtime_root=_runtime_path(root, runtime_root, workflow, "runtime_root"),
        external_state_root=_runtime_path(
            root, external_state_root, runtime, "external_state_root"
        ),
        xdg_state_home=xdg_state_home,
    )
    return RuntimeSettings(paths, *limits)


@dataclass(frozen=True, slots=True)
class PhaseSettings:
    tier: str
    effort: Effort
    timeout_seconds: int

    def __post_init__(self) -> None:
        if not isinstance(self.tier, str) or not self.tier.strip():
            raise ConfigurationError("phase tier must be nonblank text")
        if self.effort not in ("low", "medium", "high", "xhigh"):
            raise ConfigurationError("unsupported phase effort")
        if (
            type(self.timeout_seconds) is not int
            or not 1 <= self.timeout_seconds <= 86400
        ):
            raise ConfigurationError("phase timeout must be an integer from 1 to 86400")


@dataclass(frozen=True, slots=True)
class ResolvedPhaseRoute:
    agent: str
    phase: str
    tier: str
    model: str
    effort: Effort
    timeout_seconds: int
    prompt: str | None


@dataclass(frozen=True, slots=True)
class SupervisorSettings:
    runtime: RuntimeSettings
    policy: SupervisorPolicy
    phases: Mapping[str, PhaseSettings]
    capability_timeouts: Mapping[str, int] = dataclass_field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "phases", MappingProxyType(dict(self.phases)))
        object.__setattr__(
            self,
            "capability_timeouts",
            MappingProxyType(dict(self.capability_timeouts)),
        )


def validate_capability_timeout(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 86400:
        raise ConfigurationError(
            "capability timeout must be an integer from 1 to 86400"
        )
    return value


def _capability_timeouts(
    user: Mapping[str, object], project: Mapping[str, object]
) -> Mapping[str, int]:
    result: dict[str, object] = {}
    for config in (user, project):
        capabilities = _table(config, "capabilities")
        for name in capabilities:
            values = _table(capabilities, name)
            if "timeout_seconds" in values:
                result[name] = values["timeout_seconds"]
    return {name: validate_capability_timeout(value) for name, value in result.items()}


def _phase_tables(
    config: Mapping[str, object], *, agent: bool = False
) -> dict[str, Mapping[str, object]]:
    phases = _table(config, "phases")
    if phases.keys() - _PHASES:
        raise ConfigurationError("unknown phase configuration")
    allowed = {"tier", "effort"} if agent else {"tier", "effort", "timeout_seconds"}
    result = {}
    for phase in phases:
        values = _table(phases, phase)
        if values.keys() - allowed:
            raise ConfigurationError(f"unknown fields for phase {phase}")
        result[phase] = values
    return result


def _supervisor_policy(
    user: Mapping[str, object],
    project: Mapping[str, object],
    explicit: Mapping[str, object],
) -> SupervisorPolicy:
    from ovcaq.runtime.decision import SupervisorPolicy

    if "policy" in explicit:
        policy = explicit["policy"]
        if not isinstance(policy, SupervisorPolicy):
            raise ConfigurationError("policy must be SupervisorPolicy")
    else:
        values: dict[str, object] = {
            "died_retries": 1,
            "connectivity_retries": 3,
            "rate_limit_retries": 3,
            "connectivity_wait_seconds": 1800,
            "rate_limit_wait_seconds": 21600,
            "phase_repeat_limit": 5,
        }
        for config in (user, project):
            configured = _table(config, "supervisor")
            if configured.keys() - values.keys():
                raise ConfigurationError("unknown supervisor policy fields")
            values.update(configured)
        for key, value in values.items():
            if key.endswith("wait_seconds"):
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or value <= 0
                ):
                    raise ConfigurationError(f"{key} must be finite and positive")
            elif type(value) is not int or value < (
                1 if key == "phase_repeat_limit" else 0
            ):
                raise ConfigurationError(f"{key} must be an integer in range")
        policy = SupervisorPolicy(
            died_retries=cast(int, values["died_retries"]),
            connectivity_retries=cast(int, values["connectivity_retries"]),
            rate_limit_retries=cast(int, values["rate_limit_retries"]),
            connectivity_wait_seconds=cast(float, values["connectivity_wait_seconds"]),
            rate_limit_wait_seconds=cast(float, values["rate_limit_wait_seconds"]),
            phase_repeat_limit=cast(int, values["phase_repeat_limit"]),
        )
    return policy


def _supervisor_phases(
    user: Mapping[str, object],
    project: Mapping[str, object],
    explicit: Mapping[str, object],
) -> Mapping[str, PhaseSettings]:
    if "phases" in explicit:
        phases = explicit["phases"]
        if (
            not isinstance(phases, Mapping)
            or phases.keys() != _PHASES
            or any(not isinstance(value, PhaseSettings) for value in phases.values())
        ):
            raise ConfigurationError(
                "phases must map every routable phase to PhaseSettings"
            )
    else:
        user_phases = _phase_tables(user)
        project_phases = _phase_tables(project)
        configured_phases: dict[str, PhaseSettings] = {}
        for phase in ("build", "review", "done"):
            phase_values = {
                "tier": DEFAULT_PHASE_TIERS[phase],
                "effort": "high",
                "timeout_seconds": 10800 if phase == "review" else 7200,
                **user_phases.get(phase, {}),
                **project_phases.get(phase, {}),
            }
            configured_phases[phase] = PhaseSettings(
                cast(str, phase_values["tier"]),
                cast(Effort, phase_values["effort"]),
                cast(int, phase_values["timeout_seconds"]),
            )
        phases = configured_phases
    return cast(Mapping[str, PhaseSettings], phases)


def supervisor_settings(root: Path, **explicit: object) -> SupervisorSettings:
    """Resolve runtime, retry policy, and provider-neutral phase defaults."""
    if explicit.keys() - {"runtime", "policy", "phases"}:
        raise ConfigurationError("unknown supervisor settings")
    root = _trusted_path(root)
    config_home = _trusted_path(
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    )
    user = _read_config(config_home / "ovcaq/config.toml")
    project = _read_config(root / CONFIG_NAME)
    runtime = explicit["runtime"] if "runtime" in explicit else runtime_settings(root)
    if not isinstance(runtime, RuntimeSettings):
        raise ConfigurationError("runtime must be RuntimeSettings")
    policy = _supervisor_policy(user, project, explicit)
    phases = _supervisor_phases(user, project, explicit)
    return SupervisorSettings(
        runtime, policy, phases, _capability_timeouts(user, project)
    )


def resolve_phase_route(
    root: Path,
    phase: str,
    *,
    agent: str | None = None,
    phase_settings: PhaseSettings | None = None,
    default_tiers: Mapping[str, str] | None = None,
) -> ResolvedPhaseRoute:
    """Resolve a phase tier and literal prompt for the selected agent."""
    if phase not in _PHASES:
        raise ConfigurationError(f"Unknown route phase: {phase}")
    selected = agent_settings(root, name=agent)
    root = _trusted_path(root)
    config_home = _trusted_path(
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    )
    overrides: dict[str, object] = {}
    for path in (config_home / "ovcaq/config.toml", root / CONFIG_NAME):
        config = _read_config(path)
        selected_config = _table(_table(config, "agents"), selected.name)
        overrides.update(_phase_tables(selected_config, agent=True).get(phase, {}))
    neutral = (
        supervisor_settings(root).phases[phase]
        if phase_settings is None
        else phase_settings
    )
    resolved = PhaseSettings(
        cast(str, overrides.get("tier", neutral.tier)),
        cast(Effort, overrides.get("effort", neutral.effort)),
        neutral.timeout_seconds,
    )
    tiers = (
        dict(selected.tiers)
        if default_tiers is None
        else {**default_tiers, **selected.tiers}
    )
    if resolved.tier not in tiers:
        raise ConfigurationError(f"Unknown agent tier: {resolved.tier}")
    return ResolvedPhaseRoute(
        selected.name,
        phase,
        resolved.tier,
        tiers[resolved.tier],
        resolved.effort,
        resolved.timeout_seconds,
        selected.prompts.get(phase),
    )
